"""Train-only SUP/SIM/random engines. Real jobs and tests must run in Slurm."""
from dataclasses import dataclass
from pathlib import Path
import math,random,json
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from auditory5.contracts import CandidateScaler,FitScope
from auditory5.models import SmallEEGCNN_v1,ProjectionHead,make_noise_views,nt_xent_loss
from auditory5.probes import candidate_class_weights
from auditory5.provenance import object_hash


def _seed(seed):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True


def _check(X,groups,scope,y=None,record_ids=None,onset_seconds=None):
    x=np.asarray(X,dtype=np.float32);g=np.asarray(groups,dtype=str)
    if x.ndim!=3 or min(x.shape)<1 or g.shape!=(len(x),) or not np.isfinite(x).all():raise ValueError('invalid training EEG')
    scope.assert_fit_groups(g)
    if y is not None:
        a=np.asarray(y)
        if a.shape!=(len(x),) or not np.isin(a,[0,1]).all():raise ValueError('SUP labels must be 0/1')
        for candidate in np.unique(g):
            if set(a[g==candidate])!={0,1}:raise ValueError('SUP every candidate must have both classes')
    if (record_ids is None)!=(onset_seconds is None):raise ValueError('record and onset must be supplied together')
    if record_ids is not None:
        if np.shape(record_ids)!=(len(x),) or np.shape(onset_seconds)!=(len(x),) or not np.isfinite(onset_seconds).all():raise ValueError('invalid original sample provenance')
    return x,g


def _batch_indices(groups,y=None,record_ids=None,onset_seconds=None,*,batch_size,seed,
                   candidate_balanced=True,class_balanced=False,near_overlap_seconds=.7,views=False):
    """Candidate-uniform draws, class-uniform SUP; no duplicate or near-overlap.

    Retry the SAME candidate and class before choosing another draw. If exhausted,
    retain a smaller batch instead of admitting overlapping originals. Each epoch
    draws ceil(N/batch) batches; individual trials may recur in different batches.
    """
    if not candidate_balanced or batch_size<2 or near_overlap_seconds<.7:raise ValueError('invalid frozen sampler specification')
    g=np.asarray(groups);n=len(g);rng=np.random.default_rng(seed);candidates=np.unique(g)
    if not n:raise ValueError('empty sampler')
    pools={c:np.flatnonzero(g==c) for c in candidates}
    if class_balanced:
        if y is None:raise ValueError('SUP sampler needs stimulus labels')
        yy=np.asarray(y)
        classes=np.unique(yy)
        pools={(c,k):np.flatnonzero((g==c)&(yy==k)) for c in candidates for k in classes}
        if any(not len(p) for p in pools.values()):raise ValueError('candidate missing class')
    rid=None if record_ids is None else np.asarray(record_ids)
    ons=None if onset_seconds is None else np.asarray(onset_seconds)
    batches=[]
    for _ in range(math.ceil(n/batch_size)):
        selected=[];seen=set();record_times={}
        for attempt in range(min(batch_size,n)*20):
            if len(selected)>=min(batch_size,n):break
            c=candidates[int(rng.integers(len(candidates)))];key=(c,classes[int(rng.integers(len(classes)))]) if class_balanced else c
            pool=pools[key];i=None
            for _ in range(16):
                proposed=int(pool[int(rng.integers(len(pool)))])
                if proposed in seen:continue
                if rid is not None and any(abs(ons[proposed]-t)<near_overlap_seconds for t in record_times.get(rid[proposed],[])):continue
                i=proposed;break
            if i is None:continue
            selected.append(i);seen.add(i)
            if rid is not None:record_times.setdefault(rid[i],[]).append(ons[i])
        if len(selected)<2:raise ValueError('SUPPORT_INSUFFICIENT: fewer than two separated original trials per batch')
        batches.append(np.asarray(selected,dtype=int))
    return batches,0  # Actual admitted violations, distinct from rejected attempts.


def _scaler(X,groups,scope):
    ids=np.unique(groups)
    return CandidateScaler().fit([X[groups==g] for g in ids],ids,scope)


def _device(device):return torch.device(device or ('cuda' if torch.cuda.is_available() else 'cpu'))


def _schedule(opt,horizon):
    def factor(ep):
        if ep<5:return (ep+1)/5
        return .5*(1+math.cos(math.pi*min(ep-5,horizon-5)/max(1,horizon-5)))
    return torch.optim.lr_scheduler.LambdaLR(opt,factor)


def _forward(model,z,device,logits=False):
    model.eval();out=[]
    with torch.no_grad():
        for start in range(0,len(z),256):
            x=torch.from_numpy(z[start:start+256]).to(device)
            value=model(x,return_logits=True)[1] if logits else model(x)
            out.append(value.detach().cpu().numpy())
    if not out:raise ValueError('empty inference view')
    return np.concatenate(out)


def _diagnostics(model,projector,z,groups,device):
    ix=np.concatenate([np.flatnonzero(groups==g)[:8] for g in np.unique(groups)])[:512]
    latent=_forward(model,z[ix],device);centered=latent-latent.mean(axis=0)
    singular=np.linalg.svd(centered,compute_uv=False);power=singular**2
    p=power/max(power.sum(),1e-30);positive=p[p>0]
    norms=np.linalg.norm(latent,axis=1);unit=latent/np.maximum(norms[:,None],1e-30)
    out={'encoder_variance_mean':float(np.var(latent,axis=0).mean()),
         'encoder_effective_rank':float(np.exp(-np.sum(positive*np.log(positive)))) if len(positive) else 0.,
         'encoder_off_diagonal_cosine':float(((unit@unit.T).sum()-np.sum(unit*unit))/(len(unit)*(len(unit)-1))) if len(unit)>1 else None}
    if projector is not None:
        projector.eval()
        with torch.no_grad():v=projector(torch.from_numpy(latent).to(device)).cpu().numpy()
        out['projector_variance_mean']=float(np.var(v,axis=0).mean())
    return out


@dataclass
class FittedEncoder:
    encoder:nn.Module
    scaler:CandidateScaler
    scope:FitScope
    mode:str
    seed:int
    batch_violation_count:int=0
    projection:nn.Module|None=None
    metadata:dict|None=None
    device:str='cpu'

    def transform(self,X):return _forward(self.encoder,self.scaler.transform(X),self.device)

    def checkpoint(self):
        return {'version':'auditory5_training_v2','mode':self.mode,'seed':self.seed,'scope':self.scope.__dict__,
            'scope_hash':self.scope.hash,'scaler':{'center':self.scaler.center,'scale':self.scaler.scale,
              'scope_hash':self.scaler.scope_hash,'fit_groups':self.scaler.fit_groups},
            'encoder_state':self.encoder.state_dict(),'projection_state':None if self.projection is None else self.projection.state_dict(),
            'metadata':self.metadata,'batch_violation_count':self.batch_violation_count,
            'rng':{'python':random.getstate(),'numpy':np.random.get_state(),'torch':torch.get_rng_state(),
                   'cuda':torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None},
            'resume_status':'inference restore implemented; optimizer/scheduler states retained; mid-epoch resume not authorized'}

    def save(self,path):
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:torch.save(self.checkpoint(),f)

    @classmethod
    def load(cls,path,device='cpu',restore_rng=False):
        state=torch.load(path,map_location='cpu',weights_only=False)
        if state['version']!='auditory5_training_v2':raise ValueError('checkpoint version mismatch')
        scope=FitScope(**{k:tuple(v) for k,v in state['scope'].items()})
        assert state['scope_hash']==scope.hash
        scaler=CandidateScaler()
        for k,v in state['scaler'].items():setattr(scaler,k,v)
        metadata=state['metadata'];encoder=SmallEEGCNN_v1(metadata['input_channels'],n_classes=2 if state['mode']=='R_SUP' else None)
        encoder.load_state_dict(state['encoder_state']);encoder.to(device)
        projector=None
        if state['projection_state'] is not None:
            projector=ProjectionHead();projector.load_state_dict(state['projection_state']);projector.to(device)
        if restore_rng:
            random.setstate(state['rng']['python']);np.random.set_state(state['rng']['numpy']);torch.set_rng_state(state['rng']['torch'])
            if state['rng']['cuda'] is not None and torch.cuda.is_available():torch.cuda.set_rng_state_all(state['rng']['cuda'])
        return cls(encoder,scaler,scope,state['mode'],state['seed'],state['batch_violation_count'],projector,metadata,str(device))


def _metadata(X,groups,scope,config,model):
    return {'config_hash':object_hash(config) if config is not None else None,'input_channels':X.shape[1],
            'input_time_samples':X.shape[2],'parameter_count':sum(p.numel() for p in model.parameters()),
            'train_groups':sorted(set(groups)),'scope_hash':scope.hash,'training_version':'v2',
            'sampling':'candidate equal; SUP class equal within candidate; SIM no label use',
            'epoch_sampling':'fresh seed+epoch; ceil(N/batch) batches; no same batch duplicate/overlap; retries can affect realized balance'}


def fit_random(X,groups,scope,*,seed=11,config=None,device=None):
    X,groups=_check(X,groups,scope);_seed(seed);dev=_device(device)
    model=SmallEEGCNN_v1(X.shape[1]).to(dev);scale=_scaler(X,groups,scope)
    metadata=_metadata(X,groups,scope,config,model);metadata.update(_diagnostics(model,None,scale.transform(X),groups,dev))
    return FittedEncoder(model,scale,scope,'R_RAND',seed,metadata=metadata,device=str(dev))


def _train(z,y,groups,mode,epochs,horizon,seed,device,batch_size,record_ids,onset_seconds,validation=None,patience=12):
    _seed(seed);model=SmallEEGCNN_v1(z.shape[1],n_classes=2 if mode=='R_SUP' else None).to(device)
    projector=ProjectionHead().to(device) if mode=='R_SIM' else None
    params=list(model.parameters())+([] if projector is None else list(projector.parameters()))
    opt=torch.optim.AdamW(params,lr=1e-3 if mode=='R_SUP' else 3e-4,weight_decay=1e-4);scheduler=_schedule(opt,horizon)
    history=[];best=float('inf');chosen=epochs;stale=0;draw_counts={g:0 for g in np.unique(groups)}
    gen=torch.Generator(device=device).manual_seed(seed+700001)
    for ep in range(epochs):
        batches,violations=_batch_indices(groups,y,record_ids,onset_seconds,batch_size=batch_size,seed=seed+ep,
                                          class_balanced=mode=='R_SUP',near_overlap_seconds=.7)
        model.train()
        if projector is not None:projector.train()
        losses=[];grads=[];lr=float(opt.param_groups[0]['lr'])
        for idx in batches:
            x=torch.from_numpy(z[idx]).to(device)
            for g,n in zip(*np.unique(groups[idx],return_counts=True)):draw_counts[g]+=int(n)
            if mode=='R_SUP':
                _,logits=model(x,return_logits=True);loss=F.cross_entropy(logits,torch.from_numpy(y[idx]).to(device))
            else:
                a,b=make_noise_views(x,1.,noise_fraction=.02,generator=gen)
                loss=nt_xent_loss(projector(model(a)),projector(model(b)),temperature=.2)
            if not torch.isfinite(loss):raise ValueError('nonfinite training loss')
            opt.zero_grad(set_to_none=True);loss.backward();grad=nn.utils.clip_grad_norm_(params,5.)
            if not torch.isfinite(grad):raise ValueError('nonfinite gradient')
            opt.step();losses.append(float(loss.detach()));grads.append(float(grad))
        row={'epoch':ep+1,'learning_rate':lr,'loss_nats':float(np.mean(losses)),'gradient_norm_before_clip_mean':float(np.mean(grads)),
             'actual_overlap_violations':violations,'sampled_trials':sum(len(x) for x in batches),'short_batches':sum(len(x)<batch_size for x in batches)}
        scheduler.step()
        if validation is not None:
            vx,vy,vg=validation;logits=_forward(model,vx,device,logits=True)
            logprob=F.log_softmax(torch.from_numpy(logits).double(),dim=1).numpy()
            weights=candidate_class_weights(vy,vg);score=float(np.average(-logprob[np.arange(len(vy)),vy],weights=weights))
            row['monitor_candidate_balanced_ce_nats']=score
            if score<best-1e-8:best=score;chosen=ep+1;stale=0
            else:stale+=1
        history.append(row)
        if (ep+1)%10==0:print(json.dumps({'mode':mode,'epoch':ep+1,'loss':row['loss_nats'],'monitor':validation is not None}),flush=True)
        if validation is not None and stale>=patience:break
    metadata={'optimizer_state':opt.state_dict(),'scheduler_state':scheduler.state_dict(),'augmentation_generator_state':gen.get_state(),
              'history':history,'selected_epochs':chosen,'schedule_horizon':horizon,'sampled_group_counts':draw_counts}
    metadata.update(_diagnostics(model,projector,z,groups,device))
    return model,projector,metadata


def fit_supervised(X,y,groups,scope,*,record_ids=None,onset_seconds=None,seed=11,max_epochs=80,patience=12,batch_size=64,near_overlap_seconds=.7,config=None,device=None):
    X,groups=_check(X,groups,scope,y,record_ids,onset_seconds);y=np.asarray(y,dtype=np.int64)
    if max_epochs<1 or patience<1 or near_overlap_seconds!=.7:raise ValueError('invalid SUP config')
    gs=np.unique(groups);np.random.default_rng(seed).shuffle(gs)
    if len(gs)<3:raise ValueError('SUP early stopping needs >=3 training candidates')
    monitor=gs[:max(1,int(round(.2*len(gs))))];fit=~np.isin(groups,monitor)
    inner_scope=FitScope(tuple(sorted(set(groups[fit]))),tuple(sorted(monitor)),tuple(scope.validation_groups)+tuple(scope.test_groups))
    monitor_scale=_scaler(X[fit],groups[fit],inner_scope);z=monitor_scale.transform(X);dev=_device(device)
    rid=None if record_ids is None else np.asarray(record_ids);ons=None if onset_seconds is None else np.asarray(onset_seconds)
    _,_,selection=_train(z[fit],y[fit],groups[fit],'R_SUP',max_epochs,max_epochs,seed,dev,batch_size,
        None if rid is None else rid[fit],None if ons is None else ons[fit],validation=(z[~fit],y[~fit],groups[~fit]),patience=patience)
    selected=selection['selected_epochs']
    # Crucially refit BOTH scaler and freshly initialized network on all train groups.
    scaler=_scaler(X,groups,scope);final_z=scaler.transform(X)
    model,_,metadata=_train(final_z,y,groups,'R_SUP',selected,max_epochs,seed,dev,batch_size,rid,ons)
    metadata.update(_metadata(X,groups,scope,config,model));metadata.update(selected_epochs=selected,
        monitor_train_groups=list(inner_scope.train_groups),monitor_validation_groups=list(inner_scope.validation_groups),
        monitor_scaler_center=monitor_scale.center,monitor_scaler_scale=monitor_scale.scale,
        monitor_scaler_fit_groups=monitor_scale.fit_groups,monitor_scope_hash=inner_scope.hash,
        monitor_history=selection['history'],final_scaler_fit_groups=scaler.fit_groups)
    return FittedEncoder(model,scaler,scope,'R_SUP',seed,metadata=metadata,device=str(dev))


def fit_simclr(X,groups,scope,*,record_ids=None,onset_seconds=None,seed=11,epochs=100,batch_size=128,config=None,device=None):
    X,groups=_check(X,groups,scope,record_ids=record_ids,onset_seconds=onset_seconds)
    if epochs<1:raise ValueError('positive SIM epochs required')
    scaler=_scaler(X,groups,scope);dev=_device(device)
    model,projector,metadata=_train(scaler.transform(X),None,groups,'R_SIM',epochs,epochs,seed,dev,batch_size,record_ids,onset_seconds)
    metadata.update(_metadata(X,groups,scope,config,model))
    return FittedEncoder(model,scaler,scope,'R_SIM',seed,projection=projector,metadata=metadata,device=str(dev))
