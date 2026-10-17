"""Fixed-source feature decoding and explicitly broad-window temporal generalization."""
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

from .. import core,sci_r2 as S
from . import learning_budget as B

BASE=Path(core.OUT)/'aln34/content_time_v1'
PLAN=BASE/'plan.json'
NOTE=Path(core.OUT)/'aln34/CONTENT_TIME_DESIGN_20261017.md'
STORE=Path('<private checkpoint storage>/auditory_alignment_v3/aln34_content_time_v1')
CENTERS=(-200,0,200,400,600)
ALPHAS=np.logspace(-3,4,8)


def label(row):
    s=row['spec']
    if s['architecture']=='lag_local_tokens':return 'local'
    return s['architecture']+'_'+s['adaptation']


def sources():
    files={Path(__file__),NOTE,Path(B.__file__),Path(S.__file__)}
    for g in ('local_support','aligned32'):
        files.update(Path(core.REPO)/d/f for d,f in core.FAMILY_CODE[g]+core.V2_DEPS)
    return {str(f.relative_to(core.REPO)):B.sha(f) for f in sorted(files)}


def make_plan():
    rows=[]
    original=core.load_rows()+[json.loads(x) for x in (Path(core.OUT)/'plan_ext.jsonl').read_text().splitlines()]
    for r in original:
        s=r['spec']
        if r['dataset'] not in ('dtu','fau','federici') or r['seed'] not in ((3401,3407,3413) if r['dataset']=='dtu' else (3401,)):continue
        if s.get('objective')!='NCE':continue
        local=r['family_id']=='ALN32_LOCAL_SUPPORT' and s.get('variant')=='local_aligned1000'
        fm=r['family_id']=='ALN32_TRUE_FULL' and s.get('recipe')=='full_onestep_v1' and (
            s.get('architecture')=='cbramod' and s.get('adaptation') in ('pretrained_full','random_full') and float(s.get('lr_backbone',-1))==3e-4 or
            s.get('architecture')=='reve' and s.get('adaptation')=='pretrained_full' and float(s.get('lr_backbone',-1))==1e-5)
        if not(local or fm):continue
        path=Path(core.OUT)/'units'/f'{r["experiment_id"]}.json';cp=Path(core.OUT)/'ckpt'/f'{r["experiment_id"]}_best.pt'
        rec=json.loads(path.read_text());assert rec['status']=='complete' and rec['row']==r and rec['code_hash']==core.code_hash(r['family_id'])
        unit={'source':r,'record_sha256':B.sha(path),'checkpoint_sha256':B.sha(cp),'design_sha256':B.sha(NOTE)}
        unit['id']='ALN34T_'+hashlib.sha256(B.dumps(unit).encode()).hexdigest()[:16];rows.append(unit)
    rows.sort(key=lambda u:(u['source']['seed'],u['source']['dataset'],u['source']['subject_fold'],u['source']['content_fold'],label(u['source'])))
    assert len(rows)==len({r['id'] for r in rows})==180,len(rows)
    body={'version':'ALN34_CONTENT_TIME_v1','created':datetime.now().astimezone().isoformat(),'rows':rows,'sources':sources(),'store':str(STORE)}
    if PLAN.exists():
        old=json.loads(PLAN.read_text());assert all(old[k]==v for k,v in body.items() if k!='created')
    else:
        STORE.mkdir(parents=True,exist_ok=True,mode=0o700);B.write(PLAN,body);PLAN.chmod(0o444)
    print('Registered180 frozen-model content/time units',B.sha(PLAN),flush=True)


def verify(plan):assert plan['sources']==sources(),'frozen science source drift'


def features(stim,ds,idx):
    """SCI_R2 features at selected anchors, without full-bank float64 copies."""
    if ds=='federici':return {'env':np.asarray(stim['envelope'])[:1,idx].T.astype(np.float64)}
    local=np.asarray(stim['Local']);current=local[:,idx];previous=local[:,idx-1]
    return {'env':current[5:6].T.astype(np.float64),'onset':np.maximum(current[5:6]-previous[5:6],0).T.astype(np.float64),
            'spec':current[:5].T.astype(np.float64),'flux':np.linalg.norm(current[:5]-previous[:5],axis=0)[:,None].astype(np.float64),
            'Ac':np.asarray(stim['Ac'])[:,idx].T.astype(np.float64),'Lz':np.asarray(stim['Lz'])[:,idx].T.astype(np.float64)}


def valid_offsets(fs,seg_len,probe=False):
    offsets=np.rint(np.linspace(.8,3.6,3 if probe else 8)*fs).astype(int)
    for center in CENTERS:
        shift=int(round(center*fs/1000))
        assert np.all(offsets+shift-round(.4*fs)>=0) and np.all(offsets+shift+round(.6*fs)<=seg_len)
    return offsets


def rebuild(unit):
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v2.temporal import build_encoder
    from auditory_alignment_v2.foundation_adapter import Backbone
    from .. import local_support,fm_aligned
    row=unit['source'];p=Path(core.OUT)/'units'/f'{row["experiment_id"]}.json';cp=Path(core.OUT)/'ckpt'/f'{row["experiment_id"]}_best.pt'
    assert B.sha(p)==unit['record_sha256'] and B.sha(cp)==unit['checkpoint_sha256']
    rec=json.loads(p.read_text());assert rec['code_hash']==core.code_hash(row['family_id'])
    torch.manual_seed(row['seed']);coh=load_cohort(core.bind(row));stim=coh.stim
    dev=torch.device('cuda');grid=core.grid_samples(coh.fs);local=row['spec']['architecture']=='lag_local_tokens'
    if local:
        bt=local_support.batcher_for('aligned1000')(coh,core.bind(row)['spec'],row,dev,grid)
        model=build_encoder('lag_local_tokens',coh.n_ch,32,bt.W,coh.fs).to(dev)
    else:
        bt=fm_aligned.AlignedBatcher(coh,core.bind(row)['spec'],row,dev,grid)
        model=fm_aligned.AlignedFM(Backbone(row['spec']['architecture'],row['dataset'],row['spec']['adaptation'],coh.fs),32).to(dev)
    sd=torch.load(cp,map_location=dev,weights_only=False);model.load_state_dict(sd['enc'] if local else sd['model'],strict=True)
    model.requires_grad_(False).eval();return row,coh,stim,bt,model,local


@torch.no_grad()
def extract(unit,probe=False):
    dest=STORE/('probes/'+os.environ['SLURM_JOB_ID'] if probe else 'cache')/unit['id'];meta=dest/'meta.json'
    if meta.is_file():
        data=json.loads(meta.read_text());assert data['unit']==unit and data['source_sha256']==B.sha(__file__)
        assert data['array_sha256']==B.sha(dest/'arrays.npz')
        with np.load(dest/'arrays.npz',allow_pickle=False) as z:return {k:z[k] for k in z.files},data
    row,coh,stim,bt,model,local=rebuild(unit)
    train=[s for s in coh.segments if s['p'] in bt.train_p and s['role'] in ('fit','es') and s['kind']=='ss']
    rng=np.random.default_rng(row['seed']+44000)
    selected=[train[i] for i in rng.choice(len(train),size=min(400,len(train)),replace=False)]
    if probe:
        selected=[s for s in selected if s['role']=='fit'][:10]+[s for s in selected if s['role']=='es'][:10]
    test=[]
    people=[i for i,p in enumerate(coh.participants) if p['fold']==row['subject_fold']]
    if probe:people=people[:1]
    for p in people:
        items=sorted([s for s in coh.segments if s['p']==p and s['role']=='test' and s['kind']=='ss'],key=lambda s:s['e0'])
        test.extend(items[:2] if probe else items)
    assert test and not set(people)&set(bt.train_p)
    items=selected+test;offsets=valid_offsets(coh.fs,bt.seg_len,probe);nt=len(offsets)
    e=np.array([s['e0'] for s in items]);a=np.array([s['s0'] for s in items]);idx=(a[:,None]+offsets).reshape(-1)
    arrays={'role':np.repeat(np.array([s['role'] for s in items]),nt),'person':np.repeat(np.array([coh.participants[s['p']]['id'] for s in items]),nt),
            'segment':np.repeat(np.arange(len(items)),nt),'source_segment_e0':e,'anchor_offsets':offsets}
    for fam,value in features(stim,row['dataset'],idx).items():arrays['target_'+fam]=value
    env=np.asarray(stim['envelope'])[:1] if row['dataset']=='federici' else np.asarray(stim['Local'])[5:6]
    arrays['env_history']=np.concatenate([env[:,idx-round(ms*coh.fs/1000)].T for ms in (20,100,200,500)],axis=1).astype(np.float64)
    flat_starts=np.repeat(e,nt);flat_offsets=np.tile(offsets,len(e))
    for center in CENTERS:
        shift=round(center*coh.fs/1000);out=[];raw=[]
        for start in range(0,len(flat_starts),64):
            ee=torch.as_tensor(flat_starts[start:start+64],device=bt.dev)
            tt=torch.as_tensor(flat_offsets[start:start+64]+shift,device=bt.dev)
            x=bt.patches(ee+tt) if local else bt.windows(ee,tt[:,None])
            out.append(model(x).cpu().numpy())
            if local:
                half=max(1,round(.01*coh.fs));indices=ee[:,None]+tt[:,None]+torch.arange(-half,half,device=bt.dev)[None]
                raw.append(bt.E[:,indices].float().mean(-1).T.cpu().numpy())
        arrays[f'model_{center}']=np.concatenate(out)
        if local:arrays[f'raw_{center}']=np.concatenate(raw)
    metadata={'unit':unit,'source_sha256':B.sha(__file__),'probe':probe,'fs':coh.fs,'n_training_segments':len(selected),
              'n_test_segments':len(test),'n_anchors_per_segment':nt,'groups':{p['id']:p['group'] for p in coh.participants},
              'model_access_ms':{str(c):[c-400,c+600] for c in CENTERS},'raw_window_samples':2*max(1,round(.01*coh.fs))}
    dest.mkdir(parents=True,exist_ok=True,mode=0o700);np.savez_compressed(dest/'arrays.npz',**arrays)
    metadata['array_sha256']=B.sha(dest/'arrays.npz');B.write(meta,metadata)
    del bt,model,coh,stim;gc.collect();torch.cuda.empty_cache();return arrays,metadata


def ridge(x,y,alpha):
    mx=x.mean(0);my=y.mean(0);sd=x.std(0)+1e-8;z=(x-mx)/sd
    gram=z.T@z/len(z);coef=np.linalg.solve(gram+alpha*np.eye(z.shape[1]),z.T@(y-my)/len(z))
    return (coef/sd[:,None],my-mx@(coef/sd[:,None]))


def correlation(y,p):
    a=y-y.mean(0);b=p-p.mean(0)
    return float(np.mean((a*b).sum(0)/np.sqrt(np.maximum((a*a).sum(0)*(b*b).sum(0),1e-24))))


def fitted(x,y,role):
    fit=role=='fit';es=role=='es';train=fit|es
    assert fit.any() and es.any()
    curve=[]
    for alpha in ALPHAS:
        w,b=ridge(x[fit],y[fit],alpha);curve.append(correlation(y[es],x[es]@w+b))
    index=int(np.argmax(curve));w,b=ridge(x[train],y[train],ALPHAS[index])
    return w,b,{'alpha_relative':float(ALPHAS[index]),'es_correlation':curve}


def target_views(arrays):
    role=arrays['role'];train=role!='test';previous=[];out={};nuisance={}
    for fam in S.FAMS:
        if 'target_'+fam not in arrays:continue
        y=arrays['target_'+fam]
        out[fam+'/direct']=y
        if previous:
            x=np.concatenate(previous,axis=1);w,b,meta=fitted(x,y,role)
            out[fam+'/conditional']=y-(x@w+b);nuisance[fam]=meta
        previous.append(y)
    w,b,meta=fitted(arrays['env_history'],arrays['target_env'],role)
    out['env/history_conditional']=arrays['target_env']-(arrays['env_history']@w+b);nuisance['env_history']=meta
    # Train-only scaling prevents high-dimensional targets dominating their summaries.
    scaled={}
    for key,y in out.items():scaled[key]=(y-y[train].mean(0))/(y[train].std(0)+1e-8)
    return scaled,nuisance


def mismatch_indices(arrays,person):
    indices=np.flatnonzero((arrays['person']==person)&(arrays['role']=='test'))
    segments=np.unique(arrays['segment'][indices]);blocks=[indices[arrays['segment'][indices]==s] for s in segments]
    assert len({len(x) for x in blocks})==1
    return indices,np.concatenate(blocks[-1:]+blocks[:-1])


def analyse(arrays):
    targets,nuisance=target_views(arrays);role=arrays['role'];test=role=='test'
    people=sorted(set(arrays['person'][test].tolist()));results={}
    for rep in ('model','raw'):
        if f'{rep}_0' not in arrays:continue
        for target,y in targets.items():
            cells={}
            for tau in CENTERS:
                x=arrays[f'{rep}_{tau}'].astype(np.float64);w,b,selection=fitted(x,y,role)
                for other in CENTERS:
                    xp=arrays[f'{rep}_{other}'].astype(np.float64);pred=xp@w+b;per={}
                    for p in people:
                        ix,wrong=mismatch_indices(arrays,p);true=y[ix]
                        has_mismatch=len(np.unique(arrays['segment'][ix]))>1
                        per[p]={'r':correlation(true,pred[ix]),'mse':float(np.mean((true-pred[ix])**2)),
                                'mismatch_r':correlation(true,pred[wrong]) if has_mismatch else None,
                                'mismatch_mse':float(np.mean((true-pred[wrong])**2)) if has_mismatch else None,
                                'n_anchors':len(ix),'n_segments':len(np.unique(arrays['segment'][ix]))}
                    cells[f'{tau}/{other}']={'selection':selection,'per_participant':per}
            results[rep+'/'+target]=cells
    return {'decoding':results,'nuisance_fits':nuisance,'attributes':[x for x in S.FAMS if 'target_'+x in arrays]}


def run_unit(unit,probe=False):
    start=time.time();arrays,metadata=extract(unit,probe);results=analyse(arrays)
    dest=BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe else BASE/'units'
    out={'status':'complete','unit':unit,'probe':probe,'plan_sha256':B.sha(PLAN),'metadata':metadata,
         **results,'seconds':time.time()-start,'job':os.environ['SLURM_JOB_ID'],'gpu_peak_mb':torch.cuda.max_memory_allocated()/2**20}
    B.write(dest/f'{unit["id"]}.json',out);print(unit['id'],'complete',round(time.time()-start,1),'probe',probe,flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');ap.add_argument('--unit');ap.add_argument('--smoke',action='store_true');ap.add_argument('--smoke-receipt',type=Path);ap.add_argument('--max-units',type=int,default=4)
    args=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if args.make_plan:make_plan();return
    plan=json.loads(PLAN.read_text());verify(plan)
    if args.unit:run_unit(next(u for u in plan['rows'] if u['id']==args.unit));return
    if args.smoke:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            selected=[next(u for u in plan['rows'] if u['source']['dataset']=='dtu' and label(u['source'])==k) for k in ('local','cbramod_pretrained_full','cbramod_random_full','reve_pretrained_full')]
            selected.append(next(u for u in plan['rows'] if u['source']['dataset']=='federici' and label(u['source'])=='local'))
            for u in selected:run_unit(u,True);receipt['units'].append(u['id'])
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
            rc=subprocess.run([sys.executable,'-B','-m','auditory_alignment_v3.aln34.content_time','--unit',unit['id']]).returncode
            if rc:
                B.write(BASE/'units'/f'{unit["id"]}.FAILED.json',{'returncode':rc,'job':os.environ['SLURM_JOB_ID']});raise RuntimeError('science unit failed')
            done+=1
            if done>=args.max_units:break


if __name__=='__main__':main()
