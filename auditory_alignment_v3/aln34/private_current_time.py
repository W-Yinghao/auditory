"""S34_PRIVATE frozen-source current/history/time and fixed support adaptation."""
from __future__ import annotations
import argparse
from datetime import datetime
import fcntl
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import numpy as np
import torch
from scipy.special import expit
from torch import nn
from torch.nn import functional as F

from .. import core,private_stage
from . import learning_budget as B,private_calibration_loo as L,e_multiseed as E
from ..sci_r1 import private_task as P
from ..aln3_reference.calibration import AffineLogitCalibrator

BASE=Path(core.OUT)/'aln34/private_current_time_v1';PLAN=BASE/'plan.json'
NOTE=Path(core.OUT)/'aln34/PRIVATE_CURRENT_HISTORY_TIME_DESIGN_20261017.md'
STORE=Path('<private checkpoint storage>/auditory_alignment_v3/aln34_private_current_time_v1')
WINDOWS={'full':None,'pre':(-200,0),'0_200':(0,200),'200_400':(200,400),'400_600':(400,600)}
STEPS=(0,5,20)


def sources():
    files={Path(__file__),NOTE,Path(B.__file__),Path(L.__file__),Path(E.__file__),Path(P.__file__)}
    for family in ('E_LOCAL','E_GENERIC','E_PUBLIC_TRANSFER'):
        files.update(Path(core.REPO)/d/f for d,f in core.FAMILY_CODE[core.FAMILY_GROUP[family]]+core.V2_DEPS)
    for f in ('auditory_c3/c3dl/hc.py','auditory_c3/c3dl_stage0.py','auditory_alignment/data.py','auditory_alignment_v3/private_stage.py'):
        files.add(Path(core.REPO)/f)
    return {str(p.relative_to(core.REPO)):B.sha(p) for p in sorted(files)}


def make_plan():
    original=core.load_rows()+[json.loads(x) for x in (Path(core.OUT)/'plan_ext.jsonl').read_text().splitlines()];rows=[]
    for r in original:
        if not E.row_in_panel(r):continue
        cfg=E.config_of(r)
        if cfg[0] in ('E_LOCAL','E_PUBLIC_TRANSFER'):take=True
        elif cfg[0]=='E_GENERIC':
            take=(cfg[2]=='cbramod' and cfg[3] in ('pretrained_full','random_full') or cfg[2]=='reve' and cfg[3]=='pretrained_full' and r['seed']==3401)
        else:take=False
        if not take:continue
        p=Path(core.OUT)/'units'/f'{r["experiment_id"]}.json';cp=Path(core.OUT)/'ckpt'/f'{r["experiment_id"]}_best.pt';rec=json.loads(p.read_text())
        assert rec['status']=='complete' and rec['row']==r and E.EQUIVALENT_HASHES.get(rec['code_hash'],rec['code_hash'])==core.code_hash(r['family_id'])
        u={'source':r,'config':list(cfg),'record_sha256':B.sha(p),'checkpoint_sha256':B.sha(cp),'design_sha256':B.sha(NOTE)}
        u['id']='ALN34P_'+hashlib.sha256(B.dumps(u).encode()).hexdigest()[:16];rows.append(u)
    rows.sort(key=lambda u:(u['source']['seed'],u['source']['subject_fold'],u['config']))
    assert len(rows)==len({u['id'] for u in rows})==130,len(rows)
    body={'version':'ALN34_PRIVATE_CURRENT_TIME_v1','created':datetime.now().astimezone().isoformat(),'rows':rows,'sources':sources()}
    if PLAN.exists():
        old=json.loads(PLAN.read_text());assert all(old[k]==v for k,v in body.items() if k!='created')
    else:STORE.mkdir(parents=True,exist_ok=True,mode=0o700);B.write(PLAN,body);PLAN.chmod(0o444)
    print('Registered130 private current/history/time units',B.sha(PLAN),flush=True)


def verify(plan):assert plan['sources']==sources(),'private science source drift'


def mask_patches(patches,bt,window):
    if window is None:return patches
    lo=round((window[0]+200)*.25);hi=round((window[1]+200)*.25)
    values=[]
    for x,(a,b) in zip(patches,bt.W):
        idx=torch.arange(a+bt.lo,b+bt.lo,device=x.device)
        values.append(x*((idx>=lo)&(idx<hi)).to(x.dtype)[None,None,:])
    return values


@torch.no_grad()
def extract(unit,kids,probe=False):
    dest=STORE/('probes/'+os.environ['SLURM_JOB_ID'] if probe else 'cache')/unit['id'];meta=dest/'meta.json'
    if meta.exists():
        record=json.loads(meta.read_text());assert record['unit']==unit and record['source_sha256']==B.sha(__file__) and record['array_sha256']==B.sha(dest/'arrays.npz')
        with np.load(dest/'arrays.npz',allow_pickle=False) as z:return {k:z[k] for k in z.files},record
    r=unit['source'];p=Path(core.OUT)/'units'/f'{r["experiment_id"]}.json';cp=Path(core.OUT)/'ckpt'/f'{r["experiment_id"]}_best.pt'
    assert B.sha(p)==unit['record_sha256'] and B.sha(cp)==unit['checkpoint_sha256']
    torch.manual_seed(r['seed']);enc,_,rec,bt=L.rebuild(r,kids,torch.device('cuda'));enc.requires_grad_(False).eval();arrays={}
    for window,bounds in WINDOWS.items():
        for i,k in enumerate(kids):
            out=[]
            for start in range(0,len(k['y']),128):
                idx=torch.arange(start,min(start+128,len(k['y'])),device=bt.dev)
                out.append(enc(mask_patches(bt.patches(i,idx),bt,bounds)).cpu().numpy())
            arrays[f'{window}_{i}']=np.concatenate(out)
    metadata={'unit':unit,'probe':probe,'source_sha256':B.sha(__file__),'device':torch.cuda.get_device_name(0),
              'children':{str(i):k['id'] for i,k in enumerate(kids)},'windows_ms':WINDOWS,
              'original_native_per_participant':rec['eval'].get('native_calibration',{}).get('per_participant',{}),
              'recipe':rec.get('resolved_config')}
    dest.mkdir(parents=True,exist_ok=True,mode=0o700);np.savez_compressed(dest/'arrays.npz',**arrays)
    metadata['array_sha256']=B.sha(dest/'arrays.npz');B.write(meta,metadata)
    del enc,bt;gc.collect();torch.cuda.empty_cache();return arrays,metadata


def blocks(k,fraction):
    unique=np.unique(k['block']);n=len(unique);q0=max(1,int(np.ceil(.3*n)))
    ns=min(q0,max(1,int(np.floor(fraction*n))))
    support=np.flatnonzero(np.isin(k['block'],unique[:ns]));query=np.flatnonzero(np.isin(k['block'],unique[q0:]))
    assert not set(k['block'][support])&set(k['block'][query])
    return support,query


class OutputResidual(nn.Module):
    def __init__(self,dim=32):
        super().__init__();self.A=nn.Parameter(torch.randn(4,dim)*.01);self.B=nn.Parameter(torch.zeros(dim,4))
    def forward(self,u):return F.normalize(u+u@self.A.T@self.B.T,dim=-1)


def adapt_output(u,y,support,query,probe,steps,seed):
    if steps==0:return u[query].copy()
    torch.manual_seed(seed);m=OutputResidual(u.shape[1]).to('cuda');opt=torch.optim.Adam(m.parameters(),lr=1e-3)
    x=torch.tensor(u[support],device='cuda');labels=torch.tensor(y[support],device='cuda',dtype=torch.float32)
    w=torch.tensor(probe.lr.coef_[0]/probe.sd,device='cuda',dtype=torch.float32)
    bias=float(probe.lr.intercept_[0]-probe.mu@(probe.lr.coef_[0]/probe.sd))
    rng=np.random.default_rng(seed)
    for _ in range(steps):
        ix=rng.choice(len(x),size=min(256,len(x)),replace=False)
        loss=F.binary_cross_entropy_with_logits(m(x[ix])@w+bias,labels[ix])
        if not torch.isfinite(loss):raise FloatingPointError('nonfinite private output adaptation')
        opt.zero_grad();loss.backward();opt.step()
    with torch.no_grad():return m(torch.tensor(u[query],device='cuda')).cpu().numpy()


def clean_metrics(s,p,y,base):
    values=P.child_metrics(s,p,y,base)
    return {k:float(v) if np.isfinite(v) else None for k,v in zip(('auc','nll_bits','brier','gain_vs_base_bits'),values)}


def fit_interface(fd,features):
    from auditory_c3.c3dl_stage0 import _fit_offset_logistic
    x=fd.es_rows(features);probe=P.Probe(x,fd.y_es)
    hist=_fit_offset_logistic((x-probe.mu)/probe.sd,fd.y_es,fd.off_es)
    twin={i:features[i][fd.kids[i]['swap']] for i in features}
    hist_twin=_fit_offset_logistic((fd.es_rows(twin)-probe.mu)/probe.sd,fd.y_es,fd.off_es)
    return probe,hist,hist_twin


def history_metrics(fd,k,features,probe,hist,idx):
    q0=fd.q0[k['bin'][idx]];logit=fd.logit(q0)
    pred=expit(logit+np.c_[np.ones(len(idx)),(features-probe.mu)/probe.sd]@hist)
    gain=P.LL(pred,k['y'][idx])-P.LL(q0,k['y'][idx]);common=(q0>.01)&(q0<.99)
    return {'history_gain_bits':float(gain.mean()),'history_gain_common_support_bits':float(gain[common].mean()) if common.any() else None,
            'n_common_support':int(common.sum())}


def run_unit(unit,probe=False):
    from auditory_alignment import data
    start=time.time();kids=data.load_private()
    if probe:
        # Preserve source fit/ES rows and ensure every selected child's swap is legal in the truncated bank.
        for k in kids:
            es=np.flatnonzero(k['es_mask']);fit=np.flatnonzero(~k['es_mask']);ix=np.sort(np.r_[fit[:32],es[:32]])
            oldn=len(k['y'])
            for key,val in list(k.items()):
                if isinstance(val,np.ndarray) and val.ndim and len(val)==oldn:k[key]=val[ix]
            k['swap']=np.roll(np.arange(len(ix)),1)
    fd=P.Fold(kids,unit['source']['subject_fold']);arrays,meta=extract(unit,kids,probe)
    interfaces={};per={};fits={}
    for window in WINDOWS:
        u={i:arrays[f'{window}_{i}'] for i in range(len(kids))}
        pr,h,ht=fit_interface(fd,u);interfaces[window]=(pr,h,ht)
        fits[window]={'calibration':pr.cal.to_dict(),'fit_population':'source-training ES only','n_fit':len(fd.y_es)}
        for i in fd.te:
            k=kids[i];idx=np.arange(len(k['y']));s=pr.score(u[i]);metric=clean_metrics(s,pr.cal.predict(s),k['y'],fd.base)
            metric.update(history_metrics(fd,k,u[i],pr,h,idx))
            twin=history_metrics(fd,k,u[i][k['swap']],pr,ht,idx)
            metric['history_twin_gain_bits']=twin['history_gain_bits'];metric['history_minus_twin_bits']=metric['history_gain_bits']-twin['history_gain_bits']
            per.setdefault(k['id'],{'group':k['group'],'windows':{},'temporal_generalization':{},'adaptation':{}})['windows'][window]=metric
    masked=[w for w in WINDOWS if w!='full']
    for source in masked:
        pr,_,_=interfaces[source]
        for target in masked:
            u={i:arrays[f'{target}_{i}'] for i in range(len(kids))}
            cal=AffineLogitCalibrator.fit(pr.score(fd.es_rows(u)),fd.y_es)
            for i in fd.te:
                k=kids[i];s=pr.score(u[i])
                per[k['id']]['temporal_generalization'][source+'/'+target]={
                    'original_calibration':clean_metrics(s,pr.cal.predict(s),k['y'],fd.base),
                    'source_only_destination_calibration':clean_metrics(s,cal.predict(s),k['y'],fd.base)}
    pr,h,_=interfaces['full']
    for i in fd.te:
        k=kids[i];u=arrays[f'full_{i}']
        for fraction in (.1,.3):
            support,query=blocks(k,fraction)
            if not len(query):
                per[k['id']]['adaptation'][str(fraction)]={'status':'insufficient_blocks','blocks':len(np.unique(k['block']))};continue
            values={}
            for steps in ((0,1) if probe else STEPS):
                changed=adapt_output(u,k['y'],support,query,pr,steps,unit['source']['seed']+i)
                s=pr.score(changed);v=clean_metrics(s,pr.cal.predict(s),k['y'][query],fd.base)
                v.update(history_metrics(fd,k,changed,pr,h,query));values[str(steps)]=v
            per[k['id']]['adaptation'][str(fraction)]={'status':'complete','candidates':values,'n_support':len(support),'n_query':len(query),
                'n_support_positive':int(k['y'][support].sum()),'support_blocks':np.unique(k['block'][support]).tolist(),
                'query_blocks':np.unique(k['block'][query]).tolist()}
    out={'status':'complete','unit':unit,'probe':probe,'plan_sha256':B.sha(PLAN),'cache_metadata':meta,'fits':fits,
         'per_participant':per,'seconds':time.time()-start,'job':os.environ['SLURM_JOB_ID'],'gpu_peak_mb':torch.cuda.max_memory_allocated()/2**20,
         'limitations':['fixed private adaptation candidates; no inner-selected policy','masked input sensitivity, not neural latency','private pretrained/random are recipe contrasts']}
    dest=BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe else BASE/'units';B.write(dest/f'{unit["id"]}.json',out)
    print(unit['id'],'complete',round(time.time()-start,1),'probe',probe,flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');ap.add_argument('--unit');ap.add_argument('--smoke',action='store_true');ap.add_argument('--smoke-receipt',type=Path)
    args=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if args.make_plan:make_plan();return
    plan=json.loads(PLAN.read_text());verify(plan)
    if args.unit:run_unit(next(u for u in plan['rows'] if u['id']==args.unit));return
    if args.smoke:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            for fam,arch in (('E_LOCAL','lag_local_tokens'),('E_PUBLIC_TRANSFER','lag_local_tokens'),('E_GENERIC','cbramod'),('E_GENERIC','reve')):
                u=next(u for u in plan['rows'] if u['config'][0]==fam and u['config'][2]==arch)
                run_unit(u,True);receipt['units'].append(u['id'])
            receipt['status']='pass'
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    r=json.loads(args.smoke_receipt.read_text());assert r['status']=='pass' and r['plan_sha256']==B.sha(PLAN)
    done=0
    for unit in plan['rows']:
        if (BASE/'units'/f'{unit["id"]}.json').exists():continue
        lock=BASE/'claims'/f'{unit["id"]}.lock';lock.parent.mkdir(exist_ok=True)
        with lock.open('a+') as f:
            try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            rc=subprocess.run([sys.executable,'-B','-m','auditory_alignment_v3.aln34.private_current_time','--unit',unit['id']]).returncode
            if rc:
                B.write(BASE/'units'/f'{unit["id"]}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc});raise RuntimeError('private science failed')
            done+=1
            if done>=2:break


if __name__=='__main__':main()
