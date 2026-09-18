"""Fixed R3 CNN objectives, fit-only transforms and resumable checkpoints."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import time
import numpy as np
import pandas as pd
import torch
from torch import nn
from auditory5.models.small_cnn import SmallEEGCNN_v1
from .runtime import require_slurm,write_json
from .objectives import supervised_ce,nt_xent_loss,match_objective
from .representation_data import sample_quartets
from .statistics import hierarchical_weights,weighted_metrics
from .linear import WeightedScaler,fit_logistic
from .deterministic_pool import configure_pool

ALLOWED_GPU=('A100','L40S','H100','V100','RTX PRO 6000','PRO6000')
class TrainingContractError(ValueError):pass
class ProjectionHead(nn.Module):
    def __init__(self):
        super().__init__();self.net=nn.Sequential(nn.Linear(64,128),nn.GELU(),nn.Linear(128,64))
    def forward(self,z):return self.net(z)

def _check_device(device,synthetic=False):
    if device=='cpu' and synthetic:return torch.device(device)
    if not device.startswith('cuda') or not torch.cuda.is_available():raise TrainingContractError('CUDA_REQUIRED')
    name=torch.cuda.get_device_name(torch.device(device))
    if 'P100' in name.upper() or not any(x.lower() in name.lower() for x in ALLOWED_GPU):raise TrainingContractError('GPU_NOT_ALLOWED')
    return torch.device(device)

def _validate_batch_plan(post,labels,members,fit_groups,batch_indices,epochs=60):
    frame=pd.DataFrame(members);post=np.asarray(post);labels=np.asarray(labels);plan=np.asarray(batch_indices)
    if post.ndim!=3 or post.shape[1:]!=(20,100) or len(frame)!=len(post) or labels.shape!=(len(post),):raise TrainingContractError('INPUT_SHAPE')
    if not np.isfinite(post).all() or not np.isin(labels,[0,1]).all():raise TrainingContractError('INPUT_FINITE_BINARY')
    group=frame.split_group_id.astype(str).to_numpy();allowed=set(map(str,fit_groups));fit=np.isin(group,list(allowed))
    if set(group[fit])!=allowed or len(allowed)<16:raise TrainingContractError('TRAIN_GROUP_SUPPORT')
    expected=(epochs,math.ceil(int(fit.sum())/64),64)
    if plan.shape!=expected or not np.issubdtype(plan.dtype,np.integer) or plan.min()<0 or plan.max()>=len(frame):raise TrainingContractError('EXPOSURE_SHAPE')
    flat=plan.reshape(-1,64)
    if (np.diff(np.sort(flat,axis=1),axis=1)==0).any() or not fit[flat].all():raise TrainingContractError('DUPLICATE_OR_NONFIT_EXPOSURE')
    quads=flat.reshape(-1,16,4)
    for col in ('split_group_id','A_half','record_id','segment_id','previous_code','previous_run_bin'):
        values=frame[col].astype(str).to_numpy()[quads]
        if not (values==values[...,:1]).all():raise TrainingContractError('QUARTET_SCOPE')
    qgroups=group[quads[:,:,0]]
    if (np.sort(qgroups,axis=1)[:,1:]==np.sort(qgroups,axis=1)[:,:-1]).any():raise TrainingContractError('BATCH_GROUP_REPEATED')
    qlabels=labels[quads]
    if not np.all(qlabels==np.array([0,0,1,1])):raise TrainingContractError('QUARTET_CLASS_ORDER')
    if 'stimulus_local_id' in frame and not np.array_equal(labels,frame.stimulus_local_id):raise TrainingContractError('LABEL_METADATA_ALIGNMENT')
    blocks=frame.physical_block_id.astype(str).to_numpy()[quads]
    times=frame.onset_seconds_relative.to_numpy(float)[quads]
    minimum=max(10.823,float(frame.filter_support_seconds.max())) if 'filter_support_seconds' in frame else 10.823
    for a,b in ((0,1),(2,3)):
        if (blocks[...,a]==blocks[...,b]).any() or (np.abs(times[...,a]-times[...,b])<minimum).any():raise TrainingContractError('POSITIVE_FILTER_SUPPORT')
    starts=frame.epoch_start_s.to_numpy(float)[quads] if 'epoch_start_s' in frame else times-.2
    ends=frame.epoch_end_s.to_numpy(float)[quads] if 'epoch_end_s' in frame else times+.5
    for a in range(4):
        for b in range(a+1,4):
            if (np.maximum(starts[...,a],starts[...,b])<np.minimum(ends[...,a],ends[...,b])).any():raise TrainingContractError('DIRECT_EPOCH_OVERLAP')


def channel_scaler(post,members,fit_idx):
    frame=pd.DataFrame(members).iloc[fit_idx].copy()
    weights=hierarchical_weights(frame)
    raw=np.asarray(post[fit_idx],dtype=np.float64)
    mean=np.sum(raw.mean(axis=2)*weights[:,None],axis=0)[:,None]
    var=np.sum(((raw-mean)**2).mean(axis=2)*weights[:,None],axis=0)[:,None]
    scale=np.sqrt(np.maximum(var,0));scale[scale<1e-12]=1
    return mean.astype('float32'),scale.astype('float32')

def _state_hash(model):
    h=hashlib.sha256()
    for name,value in model.state_dict().items():h.update(name.encode());h.update(value.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def fit_encoder(post,labels,members,fit_groups,batch_indices,config,private,objective,*,device='cuda',ledger=None,synthetic=False,resume=None,zero_update_recovery=None):
    require_slurm()
    if objective not in ('SUP','SIM','MATCH'):raise TrainingContractError('UNKNOWN_OBJECTIVE')
    dev=_check_device(device,synthetic);frame=pd.DataFrame(members);post=np.asarray(post);labels=np.asarray(labels,dtype=np.int64);plan=np.asarray(batch_indices)
    epochs=int(config.get('epochs',60));seed=11
    if epochs!=60 or config.get('formal_seeds',[11])!=[11]:raise TrainingContractError('FIXED_TRAINING_CONFIG')
    _validate_batch_plan(post,labels,frame,fit_groups,plan,epochs)
    torch.manual_seed(seed);torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark=False
    model=configure_pool(SmallEEGCNN_v1(20,2)).to(dev);projector=ProjectionHead().to(dev)
    initial_hash=_state_hash(model)
    params=list(model.parameters())+list(projector.parameters())
    optimizer=torch.optim.AdamW(params,lr=3e-4,weight_decay=1e-4)
    scheduler=torch.optim.lr_scheduler.LambdaLR(optimizer,lambda e:(e+1)/5 if e<5 else .5*(1+np.cos(np.pi*(e-5)/55)))
    fit_idx=np.flatnonzero(frame.split_group_id.astype(str).isin(set(map(str,fit_groups))))
    mean,scale=channel_scaler(post,frame,fit_idx)
    remap=np.full(len(frame),-1,dtype=int);remap[fit_idx]=np.arange(len(fit_idx));local_plan=remap[plan]
    x=torch.as_tensor((post[fit_idx]-mean)/scale,dtype=torch.float32,device=dev)
    y=torch.as_tensor(labels[fit_idx],dtype=torch.long,device=dev)
    noise=torch.Generator(device=dev).manual_seed(seed)
    private=Path(private);private.mkdir(parents=True,exist_ok=True,mode=0o700)
    exposure_hash=hashlib.sha256(plan.tobytes()).hexdigest();history=[];start_epoch=0;checkpoint=Path(resume) if resume else None
    if resume:
        saved=torch.load(resume,map_location=dev,weights_only=False)
        if saved['objective']!=objective or saved['exposure_hash']!=exposure_hash or saved['config']!=config:raise TrainingContractError('RESUME_STATE_MISMATCH')
        if saved['fit_groups']!=sorted(map(str,fit_groups)) or not np.array_equal(saved['scaler_mean'],mean) or not np.array_equal(saved['scaler_std'],scale):raise TrainingContractError('RESUME_FIT_SCOPE_OR_SCALER_CHANGED')
        model.load_state_dict(saved['model']);projector.load_state_dict(saved['projector']);optimizer.load_state_dict(saved['optimizer']);scheduler.load_state_dict(saved['scheduler']);noise.set_state(saved['noise_state'].cpu())
        torch.set_rng_state(saved['rng_state'].cpu())
        if dev.type=='cuda':torch.cuda.set_rng_state_all([x.cpu() for x in saved['cuda_rng_states']])
        start_epoch=saved['epoch'];history=saved['history']
    if zero_update_recovery:
        if not synthetic or resume or zero_update_recovery['objective']!=objective or zero_update_recovery['exposure_hash']!=exposure_hash or zero_update_recovery['initial_encoder_sha256']!=initial_hash or zero_update_recovery['fit_groups']!=sorted(map(str,fit_groups)):raise TrainingContractError('ZERO_UPDATE_RECOVERY_STATE_MISMATCH')
        write_json(private/'zero_update_recovery.json',zero_update_recovery)
    if ledger:ledger(dict(event='resume' if resume or zero_update_recovery else 'fit_start',objective=objective,fit_groups=sorted(map(str,fit_groups)),exposure_hash=exposure_hash,initial_encoder_sha256=initial_hash,recovery_of=zero_update_recovery.get('run') if zero_update_recovery else None))
    started=time.monotonic()
    for epoch in range(start_epoch,epochs):
        model.train();projector.train();loss_sum=0.;correct=0;total=0;rep_scale=0.;grad_max=0.
        for batch in local_plan[epoch]:
            idx=torch.as_tensor(batch,dtype=torch.long,device=dev);base=x[idx]
            views=torch.stack([base+.02*torch.randn(base.shape,generator=noise,device=dev) for _ in range(2)],dim=1)
            z,logits=model(views.reshape(-1,20,100),return_logits=True);z=z.reshape(64,2,64);logits=logits.reshape(64,2,2)
            if objective=='SUP':loss=supervised_ce(logits,y[idx])
            elif objective=='SIM':loss=nt_xent_loss(projector(z),.2)
            else:loss=match_objective(logits,y[idx],projector(z),torch.arange(16,device=dev).repeat_interleave(4),.2)
            if not torch.isfinite(loss):raise TrainingContractError('NONFINITE_LOSS')
            optimizer.zero_grad(set_to_none=True);loss.backward()
            grad=float(torch.nn.utils.clip_grad_norm_(params,5.,error_if_nonfinite=True));optimizer.step()
            loss_sum+=float(loss.detach());correct+=int((logits.detach().argmax(-1)==y[idx,None]).sum());total+=128
            rep_scale+=float(z.detach().std());grad_max=max(grad_max,grad)
        scheduler.step()
        history.append(dict(epoch=epoch+1,loss=loss_sum/len(local_plan[epoch]),gradient_norm_max=grad_max,original_head_accuracy_diagnostic=correct/total,representation_std=rep_scale/len(local_plan[epoch]),original_trial_exposures=(epoch+1)*plan.shape[1]*64,elapsed_seconds=time.monotonic()-started))
        if (epoch+1)%10==0:
            state=dict(model=model.state_dict(),projector=projector.state_dict(),optimizer=optimizer.state_dict(),scheduler=scheduler.state_dict(),epoch=epoch+1,objective=objective,config=config,exposure_hash=exposure_hash,initial_encoder_sha256=initial_hash,scaler_mean=mean,scaler_std=scale,rng_state=torch.get_rng_state(),cuda_rng_states=torch.cuda.get_rng_state_all() if dev.type=='cuda' else [],noise_state=noise.get_state(),history=history,fit_groups=sorted(map(str,fit_groups)))
            checkpoint=private/f'checkpoint_epoch_{epoch+1:03d}.pt';torch.save(state,checkpoint);checkpoint.chmod(0o600)
            write_json(private/'training_progress.json',dict(epoch=epoch+1,history=history))
    result=dict(status='ENCODER_COMPLETE',objective=objective,seed=seed,epochs=epochs,checkpoint=str(checkpoint),fit_groups=sorted(map(str,fit_groups)),exposure_hash=exposure_hash,initial_encoder_sha256=initial_hash,history=history,parameter_count_encoder=sum(p.numel() for p in model.parameters()),parameter_count_projector=sum(p.numel() for p in projector.parameters()),device=torch.cuda.get_device_name(dev) if dev.type=='cuda' else 'cpu',elapsed_seconds=time.monotonic()-started)
    write_json(private/'training_receipt.json',result)
    return result


def infer_features(checkpoint,post,*,device='cpu',batch_size=256,return_logits=False):
    require_slurm();dev=torch.device('cpu') if device=='cpu' else _check_device(device)
    state=torch.load(checkpoint,map_location=dev,weights_only=False) if isinstance(checkpoint,(str,Path)) else checkpoint
    model=configure_pool(SmallEEGCNN_v1(20,2)).to(dev);model.load_state_dict(state['model']);model.eval()
    features=[];logits=[]
    with torch.no_grad():
        for start in range(0,len(post),batch_size):
            x=torch.as_tensor((np.asarray(post[start:start+batch_size])-state['scaler_mean'])/state['scaler_std'],dtype=torch.float32,device=dev)
            z,l=model(x,return_logits=True);features.append(z.cpu().numpy());logits.append(l.cpu().numpy())
    return (np.concatenate(features),np.concatenate(logits)) if return_logits else np.concatenate(features)


def generate_smoke_data(seed=64001,train_groups=24,test_groups=8):
    rng=np.random.default_rng(seed);rows=[];xs=[]
    for group in range(train_groups+test_groups):
        background=rng.normal(0,.15,(20,1))
        for half in (0,1):
            for label in (0,1):
                for repeat in range(2):
                    x=rng.normal(0,.3,(20,100))+background
                    x[0:4,30:70]+=(2*label-1)*1.5
                    onset=half*400+label*100+repeat*30
                    rows.append(dict(split_group_id=f'synthetic_{group}',candidate_id=f'synthetic_{group}',trial_id=f'synthetic_{group}_{half}_{label}_{repeat}',record_id=f'synthetic_record_{group}',segment_id=0,A_half=half,previous_code='1',previous_run_bin='run_1',stimulus_local_id=label,physical_block_id=f'{half}_{label}_{repeat}',onset_seconds_relative=onset))
                    xs.append(x)
    frame=pd.DataFrame(rows)
    return np.asarray(xs,dtype=np.float32),frame.stimulus_local_id.to_numpy(),frame


def smoke(objective,private,config=None,ledger_head=None,ledger_encoder=None,*,device='cuda',zero_update_recovery=None):
    require_slurm();private=Path(private);x,y,frame=generate_smoke_data()
    train_groups=[f'synthetic_{i}' for i in range(24)]
    sampled=sample_quartets(frame,fit_groups=train_groups,epochs=60,seed=11)
    receipt=fit_encoder(x,y,frame,train_groups,sampled['batch_indices'],config or {'epochs':60,'formal_seeds':[11]},private,objective,device=device,ledger=ledger_encoder,synthetic=True,zero_update_recovery=zero_update_recovery)
    features=infer_features(receipt['checkpoint'],x,device=device)
    # Restore the full completed optimizer/RNG state without another model fit.
    fit_encoder(x,y,frame,train_groups,sampled['batch_indices'],config or {'epochs':60,'formal_seeds':[11]},private,objective,device=device,ledger=ledger_encoder,synthetic=True,resume=receipt['checkpoint'])
    # New interpreter verifies checkpoint predictions across process restart.
    import subprocess,sys
    np.save(private/'smoke_inputs.npy',x)
    subprocess.run([sys.executable,'-c','import sys,numpy as np; from auditory_v3.train import infer_features; np.save(sys.argv[3],infer_features(sys.argv[1],np.load(sys.argv[2]),device=sys.argv[4]))',receipt['checkpoint'],str(private/'smoke_inputs.npy'),str(private/'restarted_features.npy'),device],check=True)
    repeated=np.load(private/'restarted_features.npy')
    parity=float(np.max(np.abs(features-repeated)));fit=frame.split_group_id.isin(train_groups).to_numpy();weights=hierarchical_weights(frame.loc[fit])
    scaler=WeightedScaler().fit(features[fit],weights)
    model=fit_logistic(scaler.transform(features[fit]),y[fit],weights,.01,ledger=ledger_head,context=dict(packet='R3',kind='smoke_probe',objective=objective))
    metrics=weighted_metrics(y[~fit],model.predict_proba(scaler.transform(features[~fit])),hierarchical_weights(frame.loc[~fit]))
    passed=bool(model.success and parity<=1e-6 and np.isfinite(features).all() and (objective=='SIM' or metrics['bacc']>=.8))
    return dict(status='PASS' if passed else 'CAPABILITY_FAIL',packet='R3',objective=objective,strong_test_bacc=metrics['bacc'],metrics=metrics,checkpoint_reload_max_abs=parity,epochs=60,train_groups=24,test_groups=8,initial_encoder_sha256=receipt['initial_encoder_sha256'],exposure_hash=receipt['exposure_hash'],device=receipt['device'],finite_training=True,new_synthetic_encoder_fits=0 if zero_update_recovery else 1,same_initial_state_recovery=zero_update_recovery is not None,recovery_of=zero_update_recovery.get('run') if zero_update_recovery else None,new_head_fits=1)
