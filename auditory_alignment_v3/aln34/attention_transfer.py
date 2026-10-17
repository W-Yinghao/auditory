"""Frozen retrieval-source attention transfer with held-out-person policy development."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import fcntl
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

from .. import core, run_attention
from . import adaptation_policy as D, breadth_policy as BD, attention_order as AO
from . import learning_budget as B

BASE=Path(core.OUT)/'aln34/attention_transfer_v1'
PLAN=BASE/'plan.json'
NOTE=Path(core.OUT)/'aln34/ATTENTION_TRANSFER_DESIGN_20261017.md'
SECONDS=(5,10,20)
INTEGRATORS=('mean','antisymmetric')


def read(path):return json.loads(Path(path).read_text())
def module(unit):return D if unit['source']['row']['dataset']=='dtu' else BD
def sources():
    files={Path(__file__),NOTE,Path(AO.__file__),Path(run_attention.__file__)}
    for m in (D,BD):
        files.update(Path(core.REPO)/p for p in m.sources())
    return {str(p.relative_to(core.REPO)):B.sha(p) for p in sorted(files)}


def make_plan():
    rows=[];parents={}
    for m in (D,BD):
        plan=read(m.PLAN);m.verify(plan);parents[str(m.PLAN.relative_to(core.REPO))]=B.sha(m.PLAN)
        for old in plan['rows']:
            body={'card':'E34_NEW_D_POLICY_ATTENTION_TRANSFER','source':old['outer_source'],
                  'inner':old['inner_source'],'inner_plan_sha256':old['inner_plan_sha256'],
                  'source_policy_id':old['id'],'design_sha256':B.sha(NOTE)}
            body['id']='ALN34AT_'+hashlib.sha256(B.dumps(body).encode()).hexdigest()[:16];rows.append(body)
    assert len(rows)==len({x['id'] for x in rows})==160
    value={'version':'ALN34_ATTENTION_TRANSFER_v1','created':datetime.now().astimezone().isoformat(),
           'rows':rows,'sources':sources(),'parents':parents}
    if PLAN.exists():
        old=read(PLAN);assert all(old[k]==v for k,v in value.items() if k!='created')
    else:B.write(PLAN,value);PLAN.chmod(0o444)
    print('Registered160 attention-transfer units',B.sha(PLAN),flush=True)


def verify(plan):
    assert plan['sources']==sources(),'frozen source drift'
    assert all(B.sha(Path(core.REPO)/p)==s for p,s in plan['parents'].items())


def ready(unit,probe_root=None):
    root=Path(probe_root) if probe_root else module(unit).I.BASE
    eid=unit['inner']['experiment_id'];p=root/'units'/f'{eid}.json'
    if not p.exists() or not (root/'ckpt'/f'{eid}_best.pt').is_file():return False
    r=read(p);return r.get('status')=='complete' and bool(r.get('truncated'))==bool(probe_root)


def segments(bundle,people,roles,limit=None):
    rows=[s for s in bundle.coh.segments if s['p'] in people and s['role'] in roles
          and s['kind']=='cs' and s.get('s0_ign') is not None]
    rows.sort(key=lambda s:(s['p'],s['e0']))
    if limit is not None:
        counts=defaultdict(int);out=[]
        for s in rows:
            counts[s['p']]+=1
            if counts[s['p']]<=limit:out.append(s)
        rows=out
    return rows


def windows(rows,seg_len,seconds):
    # Keep role in the grouping even if a future cache has adjacent role blocks.
    by=defaultdict(list)
    for s in rows:by[s['role']].append(s)
    return [w for role in sorted(by) for w in run_attention._windows(run_attention._runs(by[role],seg_len),seconds//5)]


def scores(bundle,rows):
    out={}
    for j in range(0,len(rows),32):
        q=rows[j:j+32];u=bundle.reps.u([s['e0'] for s in q])
        va,aa=bundle.reps.va([s['s0'] for s in q]);vi,ai=bundle.reps.va([s['s0_ign'] for s in q])
        for k,s in enumerate(q):
            key=(s['p'],s['e0'])
            if key in out:raise ValueError('duplicate participant/segment coordinate')
            out[key]={mode:float(bundle.readout.scores(u[k:k+1],va[k:k+1],aa[k:k+1],mode)[0,0]-
                                bundle.readout.scores(u[k:k+1],vi[k:k+1],ai[k:k+1],mode)[0,0])
                      for mode in ('native','unified')}
    return out


def matrix(windows_,values,mode,seconds):
    return np.array([[values[(s['p'],s['e0'])][mode] for s in w] for w in windows_],float).reshape(-1,seconds//5)


def mean_fit(x):
    if not len(x):return {'status':'no_fit'}
    rms=AO.train_scale(x)
    if rms==0:return {'status':'ok','tau':1.,'zero_training_scale':True,'n_windows':len(x)}
    if not np.isfinite(rms):raise ValueError('nonfinite training scores')
    grid=np.logspace(-3,2,41)*rms
    loss=np.array([AO.order_logloss_bits(x.mean(1)/t,-x.mean(1)/t).mean() for t in grid])
    i=int(np.argmin(loss))
    return {'status':'ok','tau':float(grid[i]),'at_grid_edge':i in (0,len(grid)-1),'n_windows':len(x)}


def logits(fits,name,x):
    if fits[name]['status']!='ok':return None
    return x.mean(1)/fits['mean']['tau'] if name=='mean' else AO.antisym_scorer(fits[name])(x)


def evaluate_windows(bundle,w,values,mode,seconds,fits):
    by=defaultdict(list)
    for i,z in enumerate(w):by[z[0]['p']].append(i)
    x=matrix(w,values,mode,seconds);out={name:{} for name in INTEGRATORS}
    for name in INTEGRATORS:
        z=logits(fits,name,x)
        if z is None:continue
        acc=AO.order_credit(z,-z);ll=AO.order_logloss_bits(z,-z)
        for p,ix in by.items():
            pid=bundle.coh.participants[p]['id']
            out[name][pid]={'group':bundle.coh.participants[p]['group'],'accuracy':float(acc[ix].mean()),
                           'nll_bits':float(ll[ix].mean()),'n_windows':len(ix)}
    return out


def select_integrator(candidates):
    means={name:float(np.mean([v['nll_bits'] for v in candidates[name].values()]))
           for name in INTEGRATORS if candidates[name]}
    if not means:raise ValueError('no attention-development windows')
    return min(means,key=lambda name:(means[name],INTEGRATORS.index(name))),means


def stage(bundle,people,role,probe):
    tr=segments(bundle,set(bundle.bt.train_p),{'fit','es'},64 if probe else None)
    te=segments(bundle,set(people),{role},32 if probe else None)
    assert not ({s['p'] for s in tr}&{s['p'] for s in te}),'source/development people overlap'
    vals=scores(bundle,tr+te);output={}
    for sec in SECONDS:
        wt=windows(tr,bundle.bt.seg_len,sec);we=windows(te,bundle.bt.seg_len,sec)
        for mode in ('native','unified'):
            x=matrix(wt,vals,mode,sec)
            fits={'mean':mean_fit(x),'antisymmetric':AO.fit_antisymmetric(x)}
            per=evaluate_windows(bundle,we,vals,mode,sec,fits)
            output[f'{sec}|{mode}']={'fits':fits,'candidates':per,'training_windows':len(wt),'evaluation_windows':len(we)}
    return {'metrics':output,'training_people':sorted(bundle.coh.participants[p]['id'] for p in bundle.bt.train_p),
            'evaluation_people':sorted(bundle.coh.participants[p]['id'] for p in people),
            'training_segments':len(tr),'evaluation_segments':len(te),
            'evaluation_coordinates':[[bundle.coh.participants[s['p']]['id'],s.get('code'),s['e0'],s['role']] for s in te],
            'segment_margins':[{'person':bundle.coh.participants[s['p']]['id'],'e0':s['e0'],'role':s['role'],
                                'scores':vals[(s['p'],s['e0'])]} for s in tr+te]}


def run_unit(unit,probe_root=None):
    t0=time.time();m=module(unit);ip=read(m.I.PLAN);m.I.verify(ip)
    assert ready(unit,probe_root)
    bundle,inner_prov=m.rebuild(unit['inner'],probe_root or m.I.BASE,ip,bool(probe_root))
    split=ip['splits'][unit['inner']['spec']['split_key']]
    people=[i for i,p in enumerate(bundle.coh.participants) if p['id'] in split['inner_ids']]
    if probe_root:people=people[:1]
    inner=stage(bundle,people,'es',bool(probe_root));choices={};risk={}
    for key,item in inner['metrics'].items():choices[key],risk[key]=select_integrator(item['candidates'])
    del bundle;torch.cuda.empty_cache()
    source=unit['source'];sp=Path(core.OUT)/'units'/f'{source["row"]["experiment_id"]}.json'
    assert B.sha(sp)==source['record_sha256']
    bundle,outer_prov=m.rebuild(source['row'],core.OUT)
    assert outer_prov['checkpoint_sha256']==source['checkpoint_sha256']
    people=[i for i,p in enumerate(bundle.coh.participants) if p['fold']==source['row']['subject_fold'] and not p.get('dev') and not p.get('test_only')]
    if probe_root:people=people[:1]
    outer=stage(bundle,people,'test',bool(probe_root))
    for key,item in outer['metrics'].items():
        choice=choices[key]
        if not item['candidates'][choice]:raise ValueError('selected integrator unavailable in outer source')
        item['selected']=item['candidates'][choice]
    value={'status':'complete','id':unit['id'],'unit':unit,'probe':bool(probe_root),'plan_sha256':B.sha(PLAN),
           'job':os.environ['SLURM_JOB_ID'],'seconds':time.time()-t0,'gpu_peak_mb':torch.cuda.max_memory_allocated()/2**20,
           'inner_provenance':inner_prov,'outer_provenance':outer_prov,'chosen_integrators':choices,
           'inner_risks':risk,'inner':inner,'outer':outer,'training_task':'single-speaker retrieval; frozen-encoder transfer to attention',
           'selection_level':'source encoders and readouts exclude inner people; inner attention selects integrator; outer test unused'}
    dest=BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe_root else BASE/'units'
    B.write(dest/f'{unit["id"]}.json',value)
    print('COMPLETE',unit['id'],'probe',bool(probe_root),'seconds',round(time.time()-t0,1),flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');ap.add_argument('--unit')
    ap.add_argument('--probe-root',type=Path);ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--dtu-probe',default='1044071');ap.add_argument('--fau-probe',default='1044203')
    ap.add_argument('--smoke-job');ap.add_argument('--max-units',type=int,default=2);a=ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if a.make_plan:make_plan();return
    plan=read(PLAN);verify(plan)
    if a.unit:
        run_unit(next(x for x in plan['rows'] if x['id']==a.unit),a.probe_root);return
    if a.smoke:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            for ds,arch in (('dtu','lag_local_tokens'),('dtu','cbramod'),('dtu','reve'),('fau','lag_local_tokens')):
                root=(D.I.BASE/'probes'/a.dtu_probe) if ds=='dtu' else (BD.I.BASE/'probes'/a.fau_probe)
                unit=next(x for x in plan['rows'] if x['source']['row']['dataset']==ds and x['inner']['spec']['architecture']==arch and ready(x,root))
                run_unit(unit,root);receipt['units'].append({'id':unit['id'],'dataset':ds,'architecture':arch})
            receipt['status']='pass'
        except BaseException:
            receipt['status']='failed';receipt['traceback']=traceback.format_exc();raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    receipt=read(BASE/'probes'/str(a.smoke_job)/'receipt.json')
    assert receipt['status']=='pass' and receipt['plan_sha256']==B.sha(PLAN)
    if list((BASE/'units').glob('*.FAILED.json')):raise RuntimeError('unresolved technical failure')
    done=0
    for unit in plan['rows']:
        dest=BASE/'units'/f'{unit["id"]}.json'
        if dest.exists() or not ready(unit):continue
        lock=BASE/'claims'/f'{unit["id"]}.lock';lock.parent.mkdir(exist_ok=True)
        with lock.open('a+') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if dest.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m','auditory_alignment_v3.aln34.attention_transfer','--unit',unit['id']]).returncode
            rec=read(dest) if dest.exists() else {}
            if rc or rec.get('status')!='complete' or rec.get('probe'):
                B.write(BASE/'units'/f'{unit["id"]}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'rc':rc});raise RuntimeError('attention unit failed')
            done+=1
        if done>=a.max_units:break
    print('ROTATION COMPLETE attention',done,flush=True)


if __name__=='__main__':main()
