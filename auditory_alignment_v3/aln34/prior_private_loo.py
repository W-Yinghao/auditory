"""Frozen-weight self-reference intervention on public-prior private CS targets."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import numpy as np
import torch

from .. import core
from . import private_calibration_loo as L
from ..prior33 import contract as C, model as M, views as V, target_train as TT, run_target as RT
from ..sci_r1 import stats as S

ROOT=Path(core.REPO);SOURCE=Path(core.OUT)
BASE=SOURCE/'aln34/prior_private_loo_v1';PLAN=BASE/'plan.json'
STORE=Path('<private checkpoint storage>/auditory_alignment_v3/aln34_prior_private_loo_v1')
NOTE=SOURCE/'aln34/PRIOR_PRIVATE_LOO_DESIGN_20261017.md'


def read(p):return json.loads(Path(p).read_text())
def now():return datetime.now().astimezone().isoformat()
def sha(p):return L.sha(p)
def write(p,v):L.D.write(p,v)


def sources():
    files={Path(__file__),NOTE,Path(L.__file__),Path(C.__file__),Path(M.__file__),Path(V.__file__),Path(TT.__file__),Path(RT.__file__),Path(S.__file__)}
    files.update(ROOT/d/f for d,f in core.FAMILY_CODE[core.FAMILY_GROUP['ALN32_PUBLIC_AUDIO_PRIOR_TARGET']]+core.V2_DEPS)
    files.update(ROOT/p for p in L.source_hashes())
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}


def all_rows():return core.load_rows()+[json.loads(x) for x in (SOURCE/'plan_ext.jsonl').read_text().splitlines() if x.strip()]


def eligible(row):
    return row['family_id']=='ALN32_PUBLIC_AUDIO_PRIOR_TARGET' and row['dataset']=='private_bdf' and row['spec']['objective']=='CS_SINGLE'


def config(row):
    s=row['spec']
    return '|'.join(str(s.get(k,'')) for k in ('block','member','init','variant','objective','epochs'))


def register():
    rows=sorted((r for r in all_rows() if eligible(r)),key=lambda r:(r['seed'],r['subject_fold'],r['experiment_id']))
    assert rows and len({r['experiment_id'] for r in rows})==len(rows)
    plan={'version':'ALN34_PRIOR_PRIVATE_LOO_v1','created':now(),'rows':rows,'sources':sources(),
          'reproduction_tolerance':L.REPRO_TOL,'checkpoint':'primary_best_only','note_sha256':sha(NOTE)}
    if PLAN.exists():assert all(read(PLAN)[k]==v for k,v in plan.items() if k!='created')
    else:write(PLAN,plan);PLAN.chmod(0o444)
    STORE.mkdir(parents=True,exist_ok=True,mode=0o700)
    print('Registered',len(rows),'private prior CS frozen evaluations',sha(PLAN),flush=True)


def verify(plan):assert plan['sources']==sources(),'prior private readout source drift'


def ready(row):
    p=SOURCE/'units'/f'{row["experiment_id"]}.json';c=SOURCE/'ckpt'/f'{row["experiment_id"]}_best.pt'
    if not p.exists() or not c.is_file():return False
    r=read(p)
    return r.get('status')=='complete' and not r.get('truncated') and r.get('row')==row


def bind_source(row,source,probe):
    eid=row['experiment_id'];path=source/'units'/f'{eid}.json';ckpt=source/'ckpt'/f'{eid}_best.pt';rec=read(path)
    assert rec['status']=='complete' and rec['row']==row
    assert probe or not rec.get('truncated')
    assert rec['code_hash']==core.code_hash(row['family_id'])
    return {'row':row,'record_sha256':sha(path),'checkpoint_sha256':sha(ckpt),'recorded_device':rec['device'],
            'original_code_hash':rec['code_hash'],'original_source':str(source),'probe':probe}


def rebuild(row,kids,dev):
    eid=row['experiment_id'];rec=read(Path(core.OUT)/'units'/f'{eid}.json');b=TT.bind(row)
    manifest=RT.open_manifest(row)
    TT._private_cell(kids,V.manifest_cell(manifest,'private_bdf',row['subject_fold'],0),row['subject_fold'])
    bt=V.PrivateBatcher64(kids,b['spec'],b,dev)
    enc=M.build_shared(C.PRIVATE_LAYOUT,C.PRIVATE_LAYOUT,row['seed']).to(dev)
    sd=torch.load(Path(core.OUT)/'ckpt'/f'{eid}_best.pt',map_location=dev,weights_only=False)
    enc.load_state_dict(sd['enc'],strict=True);enc.requires_grad_(False).eval()
    return enc,sd.get('protos'),rec,bt


@contextmanager
def bindings(source,dest,score):
    from auditory_alignment import data
    previous=(core.OUT,L.BASE,L.PLAN,L.rebuild,data.load_private)
    score.mkdir(parents=True,exist_ok=True,mode=0o700);dest.mkdir(parents=True,exist_ok=True,mode=0o700)
    link=dest/'scores'
    if not link.exists():link.symlink_to(score,target_is_directory=True)
    assert link.resolve()==score.resolve()
    old_loader=data.load_private
    core.OUT=str(source);L.BASE=dest;L.PLAN=PLAN;L.rebuild=rebuild
    data.load_private=lambda:V.load_private64(old_loader())
    try:yield
    finally:core.OUT,L.BASE,L.PLAN,L.rebuild,data.load_private=previous


def evaluate(row,plan,probe_source=None):
    probe=probe_source is not None;eid=row['experiment_id'];source=Path(probe_source) if probe else SOURCE
    dest=BASE/'probes'/os.environ['SLURM_JOB_ID']/'evaluation' if probe else BASE
    score=STORE/'probes'/os.environ['SLURM_JOB_ID'] if probe else STORE/'scores'
    unit=bind_source(row,source,probe);binding=dest/'bindings'/f'{eid}.json'
    if binding.exists():assert read(binding)==unit
    else:write(binding,unit);binding.chmod(0o444)
    # Byte-identical records and symlinks isolate the inherited evaluator's paths.
    view=dest/'source_view';rp=view/'units'/f'{eid}.json';cp=view/'ckpt'/f'{eid}_best.pt'
    rp.parent.mkdir(parents=True,exist_ok=True);cp.parent.mkdir(parents=True,exist_ok=True)
    if not rp.exists():shutil.copy2(source/'units'/f'{eid}.json',rp)
    if not cp.exists():cp.symlink_to((source/'ckpt'/f'{eid}_best.pt').resolve())
    assert sha(rp)==unit['record_sha256'] and sha(cp)==unit['checkpoint_sha256']
    with bindings(view,dest,score):L.evaluate(unit,plan)
    out=dest/'units'/f'{eid}.json';result=read(out)
    result.update(probe=probe,evaluation_id='ALN34PLOO_'+hashlib.sha256((sha(PLAN)+'|'+eid).encode()).hexdigest()[:16],
                  binding_sha256=sha(binding),source_checkpoint_selection='primary_best_only')
    write(out,result)


def clean(x):
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,np.generic):return clean(x.item())
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items() if k!='T'}
    if isinstance(x,(tuple,list)):return [clean(v) for v in x]
    return x


def aggregate(plan):
    configs={};complete=0;provenance={}
    for row in plan['rows']:
        key=config(row);cfg=configs.setdefault(key,{'planned':[],'values':{}});cfg['planned'].append(row)
        p=BASE/'units'/f'{row["experiment_id"]}.json'
        if not p.exists():continue
        r=read(p)
        if r.get('status')!='complete':continue
        assert not r.get('probe') and r['reproduction']['pass'] and r['plan_sha256']==sha(PLAN)
        complete+=1;provenance[row['experiment_id']]={'file':str(p),'sha256':sha(p),'binding_sha256':r['binding_sha256']}
        for child,value in r['per_participant'].items():
            token=(row['seed'],row['subject_fold']);cfg['values'].setdefault(child,{})
            assert token not in cfg['values'][child];cfg['values'][child][token]=value
    families={}
    for key,cfg in configs.items():
        rows=cfg['planned'];seeds=sorted({r['seed'] for r in rows});folds={seed:{r['subject_fold'] for r in rows if r['seed']==seed} for seed in seeds}
        assert all(v==set(range(5)) for v in folds.values())
        ids=sorted(c for c,v in cfg['values'].items() if {s for s,f in v}==set(seeds) and len(v)==len(seeds) and len({f for s,f in v})==1)
        item={'planned_seeds':seeds,'paired_n':len(ids),'expected_n':64,'comparisons':['original_refit','class_kernel'],'metrics':{}}
        if len(ids)>=3:
            for metric in ('nll_bits','brier','auc_score'):
                y=np.array([[np.mean([v['leave_self_out'][metric]-v[other][metric] for v in cfg['values'][c].values()]) for other in item['comparisons']] for c in ids])
                item['metrics'][metric]=clean(S.summary(y,B=4000,seed=S.group_seed('prior_loo',key,metric)))
        families[key]=item
    result={'time':now(),'status':'complete' if complete==len(plan['rows']) else 'interim','units_complete':complete,
            'units_planned':len(plan['rows']),'families':families,'provenance':provenance,'plan_sha256':sha(PLAN),'job':os.environ['SLURM_JOB_ID']}
    write(ROOT/'results/auditory_alignment_v3/aln34/prior_private_loo/efficacy.json',result)
    lines=['# Public-prior private CS calibration sensitivity','',f"Snapshot{result['time']}: **{result['status']}**, {complete}/{len(plan['rows'])}frozen primary checkpoints.",'',
           'This exploratory readout intervention preserves training, primary checkpoint selection and test reference banks. Original-score reproduction must pass the inherited numerical tolerances; only exact calibration-trial self-reference is removed. Same-child reference dependence remains. Positive-affine AUC is unchanged. It does not replace the frozen prior analysis.','',
           '| Configuration | Planned seeds | Complete paired children | LOO minus original NLL | Simultaneous95% interval |','|---|---|---:|---:|---|']
    for key,item in families.items():
        v=item['metrics'].get('nll_bits');point=f"{v['est'][0]:+.6f}" if v else 'pending';interval=f"[{v['band_low'][0]:+.6f}, {v['band_high'][0]:+.6f}]" if v else 'pending'
        lines.append(f"| {key.replace('|',' / ')} | {item['planned_seeds']} | {item['paired_n']}/64 | {point} | {interval} |")
    lines+=['','Both reference contrasts and all endpoints are in the aggregate JSON;4000identity bootstrap-t, simultaneous within each configuration×endpoint two-contrast family. Only full planned-seed pairing enters a mean. The gain-selected checkpoint sensitivity is outside this first follow-up.']
    (ROOT/'docs/auditory_alignment_v3/PRIOR_PRIVATE_CALIBRATION_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print('Prior private calibration',complete,'/',len(plan['rows']),flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--register',action='store_true');ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--unit');ap.add_argument('--smoke-job');ap.add_argument('--max-units',type=int,default=8);ap.add_argument('--aggregate',action='store_true')
    a=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if a.register:register();return
    plan=read(PLAN);verify(plan)
    if a.aggregate:aggregate(plan);return
    if a.unit:evaluate(next(r for r in plan['rows'] if r['experiment_id']==a.unit),plan);return
    if a.smoke:
        receipt={'status':'running','plan_sha256':sha(PLAN)}
        try:
            row=next(r for r in plan['rows'] if r['spec'].get('init')=='random' and r['seed']==3401 and r['subject_fold']==0)
            source=BASE/'probes'/os.environ['SLURM_JOB_ID']/'source'
            RT.run(row,str(source),epochs=2,device='cuda',rows=all_rows())
            evaluate(row,plan,source);receipt.update(status='pass',source_unit=row['experiment_id'])
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    receipt=read(BASE/'probes'/str(a.smoke_job)/'receipt.json');assert receipt['status']=='pass' and receipt['plan_sha256']==sha(PLAN)
    assert not list((BASE/'units').glob('*.FAILED.json')),'unresolved reproduction/technical failure'
    done=0
    for row in plan['rows']:
        eid=row['experiment_id'];p=BASE/'units'/f'{eid}.json'
        if p.exists() or not ready(row):continue
        lock=BASE/'claims'/f'{eid}.lock';lock.parent.mkdir(parents=True,exist_ok=True)
        with lock.open('a+') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if p.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m','auditory_alignment_v3.aln34.prior_private_loo','--unit',eid]).returncode
            if rc or not p.exists() or read(p).get('status')!='complete':
                write(BASE/'units'/f'{eid}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc});raise RuntimeError('prior private reproduction failed')
            done+=1
        if done>=a.max_units:break


if __name__=='__main__':main()
