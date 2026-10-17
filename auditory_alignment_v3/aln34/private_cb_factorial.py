"""Complete the missing cells of private CB initialization x original rate pairs."""
from __future__ import annotations
import argparse
import copy
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
import torch

from .. import core,local_train,calib
from . import learning_budget as B,private_current_time as C,e_multiseed as E

BASE=Path(core.OUT)/'aln34/private_cb_factorial_v1';PLAN=BASE/'plan.json'
NOTE=Path(core.OUT)/'aln34/PRIVATE_CB_FACTORIAL_DESIGN_20261017.md'
STORE=Path('<private checkpoint storage>/auditory_alignment_v3/aln34_private_cb_factorial_v1')
FAMILY='ALN34_PRIVATE_CB_FACTORIAL';SELF=('auditory_alignment_v3/aln34','private_cb_factorial.py')
RATES={'NCE':{'pre_recipe':(1e-4,1e-4),'random_recipe':(3e-4,3e-4)},
       'CS_SINGLE':{'pre_recipe':(1e-5,1e-3),'random_recipe':(1e-4,1e-4)}}


def read(p):return json.loads(Path(p).read_text())
def register():
    files=core.FAMILY_CODE[core.FAMILY_GROUP['E_GENERIC']]+[SELF]
    group='aln34_private_cb_factorial'
    assert group not in core.FAMILY_CODE or core.FAMILY_CODE[group]==files
    core.FAMILY_CODE[group]=files;core.FAMILY_GROUP[FAMILY]=group


def sources():
    files={Path(__file__),NOTE,Path(B.__file__),Path(E.__file__)}
    files.update(Path(core.REPO)/d/f for d,f in core.FAMILY_CODE[core.FAMILY_GROUP['E_GENERIC']]+core.V2_DEPS)
    return {str(p.relative_to(core.REPO)):B.sha(p) for p in sorted(files)}


def crossed(row):
    old='pre_recipe' if row['spec']['adaptation']=='pretrained_full' else 'random_recipe'
    other='random_recipe' if old=='pre_recipe' else 'pre_recipe'
    return old,other


def make_plan():
    register();cp=read(C.PLAN);C.verify(cp);rows=[];baselines={}
    for unit in cp['rows']:
        row=unit['source'];s=row['spec']
        if row['family_id']!='E_GENERIC' or s['architecture']!='cbramod':continue
        assert s['adaptation'] in ('pretrained_full','random_full') and s['objective'] in RATES
        eid=row['experiment_id'];path=Path(core.OUT)/'units'/f'{eid}.json';old=read(path)
        assert old['status']=='complete' and old['row']==row
        assert E.EQUIVALENT_HASHES.get(old['code_hash'],old['code_hash'])==core.code_hash('E_GENERIC')
        assert B.sha(path)==unit['record_sha256'] and B.sha(Path(core.OUT)/'ckpt'/f'{eid}_best.pt')==unit['checkpoint_sha256']
        own,other=crossed(row);lr=old['resolved_config']
        assert tuple(lr[k] for k in ('lr_backbone','lr_head'))==RATES[s['objective']][own] and lr['epochs']==100
        baselines[eid]={'row':row,'rate_cell':own,'record_sha256':unit['record_sha256'],
                        'checkpoint_sha256':unit['checkpoint_sha256'],'recipe':lr}
        new=copy.deepcopy(row);new['family_id']=FAMILY;new.pop('experiment_id')
        new['spec'].update(rate_cell=other,lr_backbone=RATES[s['objective']][other][0],lr_head=RATES[s['objective']][other][1],epochs=100,
                           baseline_id=eid,card='PRIVATE_CB_INIT_RATE_FACTORIAL',design_sha256=B.sha(NOTE))
        new['experiment_id']='ALN34PI_'+hashlib.sha256(B.dumps(new).encode()).hexdigest()[:16];rows.append(new)
    rows.sort(key=lambda r:(r['seed'],r['subject_fold'],r['spec']['objective'],r['spec']['adaptation']))
    assert len(rows)==len(baselines)==len({r['experiment_id'] for r in rows})==60
    value={'version':'ALN34_PRIVATE_CB_FACTORIAL_v1','created':datetime.now().astimezone().isoformat(),'rows':rows,
           'baselines':baselines,'sources':sources(),'private_science_plan_sha256':B.sha(C.PLAN)}
    if PLAN.exists():assert all(read(PLAN)[k]==v for k,v in value.items() if k!='created')
    else:STORE.mkdir(parents=True,exist_ok=True,mode=0o700);B.write(PLAN,value);PLAN.chmod(0o444)
    print('Registered60 crossed private CB cells;60 historical cells reused',B.sha(PLAN),flush=True)


def verify(plan):
    register();assert plan['sources']==sources() and plan['private_science_plan_sha256']==B.sha(C.PLAN)


def state_hash(state):
    h=hashlib.sha256()
    for key,t in sorted(state.items()):
        h.update(key.encode());h.update(t.detach().contiguous().cpu().numpy().tobytes())
    return h.hexdigest()


def init_audit():
    from auditory_alignment_v2.foundation_adapter import Backbone
    out={}
    for adaptation in ('pretrained_full','random_full'):
        torch.manual_seed(3401)
        bb=Backbone('cbramod','private_bdf',adaptation,250)
        enc=local_train.EpochEncoder(bb,32).to('cuda');protos=torch.randn(2,32,device='cuda')
        assert all(p.requires_grad for p in enc.parameters())
        out[adaptation]={'head_sha256':state_hash({k:v for k,v in enc.state_dict().items() if not k.startswith('bb.')}),
                         'backbone_sha256':state_hash(bb.state_dict()),'prototype_sha256':state_hash({'protos':protos}),
                         'cpu_rng_sha256':state_hash({'rng':torch.get_rng_state()}),
                         'gpu_rng_sha256':state_hash({'rng':torch.cuda.get_rng_state()}),
                         'trainable_parameters':sum(p.numel() for p in enc.parameters())}
        del enc,bb,protos;torch.cuda.empty_cache()
    a,b=out.values()
    for k in ('head_sha256','prototype_sha256','cpu_rng_sha256','gpu_rng_sha256','trainable_parameters'):assert a[k]==b[k],k
    assert a['backbone_sha256']!=b['backbone_sha256']
    return out


def run_unit(row,probe=False):
    from auditory_alignment import data
    from auditory_alignment_v2 import evaluate as ev2
    t0=time.time();plan=read(PLAN);verify(plan);root=BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe else BASE
    dest=STORE/('probes/'+os.environ['SLURM_JOB_ID'] if probe else 'production');dest.mkdir(parents=True,exist_ok=True,mode=0o700)
    s=row['spec'];b=core.bind(row);epochs=2 if probe else 100;log={}
    rec=core.new_record(row,b,str(root));prefix=str(dest/row['experiment_id'])
    rec.update(probe=probe,truncated=probe,plan_sha256=B.sha(PLAN),job=os.environ['SLURM_JOB_ID'],
               resolved_config={'d':32,'epochs':epochs,'lr_backbone':s['lr_backbone'],'lr_head':s['lr_head'],
                                'rate_cell':s['rate_cell'],'readout':'spatial_signed_k8_e32_v1'})
    kids=data.load_private()
    enc,bt,protos=local_train.fit_private_fm(b,kids,torch.device('cuda'),prefix,log,s['lr_backbone'],s['lr_head'],epochs,s['adaptation'],d=32)
    assert log['backbone_contract']['trainable_layers']=='all'
    rec.update(log);rec['eval']=ev2.evaluate_private(b,enc,bt,log['objective_calibration'],protos)
    rec['eval']['native_calibration']=calib.private_variants(b,enc,bt,protos,log['objective_calibration'])
    rec.update(status='complete',selection_level='training children and their source ES blocks; original E recipe',
               checkpoint=prefix+'_best.pt',checkpoint_sha256=B.sha(prefix+'_best.pt'),
               inherited_baseline=plan['baselines'][s['baseline_id']],
               requested_optimizer_steps=epochs*log['steps_per_epoch'],
               nonfinite_steps=epochs*log['steps_per_epoch']-log['optimizer_steps'],
               nonfinite_steps_observed_validation_epochs=sum(x['nonfinite_steps'] for x in log['curve']))
    link=root/'ckpt'/f'{row["experiment_id"]}_best.pt'
    if not link.exists():link.symlink_to(prefix+'_best.pt')
    core.write_record(str(root/'units'/f'{row["experiment_id"]}.json'),rec,t0)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');ap.add_argument('--unit')
    ap.add_argument('--probe',action='store_true');ap.add_argument('--smoke',action='store_true');ap.add_argument('--smoke-job')
    ap.add_argument('--max-units',type=int,default=2);a=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if a.make_plan:make_plan();return
    plan=read(PLAN);verify(plan)
    if a.unit:run_unit(next(r for r in plan['rows'] if r['experiment_id']==a.unit),a.probe);return
    if a.smoke:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            receipt['initialization_audit']=init_audit()
            for obj in RATES:
                for ad in ('pretrained_full','random_full'):
                    row=next(r for r in plan['rows'] if r['spec']['objective']==obj and r['spec']['adaptation']==ad)
                    run_unit(row,True);receipt['units'].append(row['experiment_id'])
            receipt['status']='pass'
        except BaseException:
            receipt['status']='failed';receipt['traceback']=traceback.format_exc();raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    receipt=read(BASE/'probes'/str(a.smoke_job)/'receipt.json')
    assert receipt['status']=='pass' and receipt['plan_sha256']==B.sha(PLAN)
    if list((BASE/'units').glob('*.FAILED.json')):raise RuntimeError('unresolved technical failure')
    done=0
    for row in plan['rows']:
        eid=row['experiment_id'];p=BASE/'units'/f'{eid}.json'
        if p.exists():continue
        lock=BASE/'claims'/f'{eid}.lock';lock.parent.mkdir(exist_ok=True)
        with lock.open('a+') as h:
            try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if p.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m','auditory_alignment_v3.aln34.private_cb_factorial','--unit',eid]).returncode
            rec=read(p) if p.exists() else {}
            if rc or rec.get('status')!='complete' or rec.get('probe'):
                B.write(BASE/'units'/f'{eid}.FAILED.json',{'rc':rc,'job':os.environ['SLURM_JOB_ID']});raise RuntimeError('private crossed cell failed')
            done+=1
        if done>=a.max_units:break
    print('ROTATION COMPLETE private CB factorial',done,flush=True)


if __name__=='__main__':main()
