"""Matched CBraMod auditory intermediate training and frozen-recipe target runs."""
from __future__ import annotations
import argparse
import contextlib
import copy
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

from .. import core, fm_aligned, fm_aligned32
from ..prior33 import views as V, contract as C, model as M, losses as L
from . import learning_budget as B, content_time as CT, episode_training as E

BASE=Path(core.OUT)/'aln34/cb_auditory_v1';PLAN=BASE/'plan.json'
NOTE=Path(core.OUT)/'aln34/CB_AUDITORY_CONTINUATION_DESIGN_20261017.md'
MANIFEST=Path(core.OUT)/'aln34/prior33/manifest.json'
MANIFEST_SHA='b751976b9238590026f26a6fbe6c84177b69802ef9e55e687425af210b627426'
STORE=Path('<private checkpoint storage>/auditory_alignment_v3/aln34_cb_auditory_v1')
ARMS=('generic_paired','random_paired','generic_wrong')
SNAPSHOTS=(0,2500,5000,10000)
FAMILY='ALN34_CB_AUDITORY_TARGET'


def read(p):return json.loads(Path(p).read_text())


def register():
    group='aln34_cb_auditory';files=core.FAMILY_CODE['aligned32']+[('auditory_alignment_v3/aln34','cb_auditory.py')]
    if group in core.FAMILY_CODE:assert core.FAMILY_CODE[group]==files
    core.FAMILY_CODE[group]=files;core.FAMILY_GROUP[FAMILY]=group


def sources():
    files={Path(__file__),NOTE,Path(B.__file__),Path(CT.__file__),Path(E.__file__),Path(V.__file__),Path(C.__file__),Path(M.__file__),Path(L.__file__)}
    files.update(Path(core.REPO)/d/f for d,f in core.FAMILY_CODE['aligned32']+core.V2_DEPS)
    return {str(p.relative_to(core.REPO)):B.sha(p) for p in sorted(files)}


def eligible(man):
    idx=V.manifest_index(man);s=idx.seg['sparrkulee']
    excluded=set()
    for ds in ('dtu','fau','federici'):excluded.update(man['donor_sets'][ds]['core']['excluded_presentations']['sparrkulee'])
    def keep(rows,role):
        out=[int(i) for i in rows if int(s['presentation'][int(i)]) not in excluded]
        assert out and all(s['role'][i]==role for i in out)
        return out
    return {'fit':keep(man['pools']['core']['sparrkulee'],'fit'),
            'dev':keep(man['selection']['dev_queries'],'dev'),'excluded_presentations':sorted(excluded)}


def make_plan():
    from auditory_alignment_v2.foundation_adapter import CHANNELS
    register();man=V.open_manifest(MANIFEST,MANIFEST_SHA);pool=eligible(man)
    assert tuple(man['montages']['sparrkulee'])==tuple(CHANNELS['dtu'])==C.BIOSEMI64
    oldplan=read(CT.PLAN);CT.verify(oldplan);baselines={u['source']['experiment_id']:u for u in oldplan['rows'] if u['source']['spec']['architecture']=='cbramod'}
    donors=[];targets=[]
    for seed in (3401,3407,3413):
        for arm in ARMS:
            u={'kind':'donor','seed':seed,'arm':arm,'updates':10000,'manifest_sha256':MANIFEST_SHA,
               'pool_sha256':hashlib.sha256(B.dumps(pool).encode()).hexdigest(),'design_sha256':B.sha(NOTE)}
            u['id']='ALN34CBP_'+hashlib.sha256(B.dumps(u).encode()).hexdigest()[:16];donors.append(u)
    for baseline in baselines.values():
        original=baseline['source'];s=original['spec']
        for arm in ARMS:
            if (s['adaptation']=='random_full')!=(arm=='random_paired'):continue
            donor=next(u for u in donors if u['seed']==original['seed'] and u['arm']==arm)
            row=copy.deepcopy(original);row.pop('experiment_id');row.pop('registered',None);row['family_id']=FAMILY
            row['spec'].update(card='E34_CB_AUDITORY',kind='target',intermediate_arm=arm,donor_id=donor['id'],
                               baseline_id=original['experiment_id'],design_sha256=B.sha(NOTE),epochs=100)
            row['experiment_id']='ALN34CBT_'+hashlib.sha256(B.dumps(row).encode()).hexdigest()[:16];targets.append(row)
    assert len(donors)==9 and len(targets)==135,(len(donors),len(targets))
    targets.sort(key=lambda r:(r['seed'],r['dataset'],r['subject_fold'],r['content_fold'],r['spec']['intermediate_arm']))
    body={'version':'ALN34_CB_AUDITORY_v1','created':datetime.now().astimezone().isoformat(),'rows':donors+targets,
          'sources':sources(),'manifest_sha256':MANIFEST_SHA,'pool':pool,'baselines':baselines,'target_code_hash':core.code_hash(FAMILY)}
    if PLAN.exists():assert all(read(PLAN)[k]==v for k,v in body.items() if k!='created')
    else:
        STORE.mkdir(parents=True,exist_ok=True,mode=0o700);B.write(PLAN,body);PLAN.chmod(0o444)
        link=BASE/'ckpt'
        if not link.exists():link.symlink_to(STORE/'target_ckpt',target_is_directory=True)
        (STORE/'target_ckpt').mkdir(exist_ok=True,mode=0o700)
        assert link.resolve()==STORE/'target_ckpt'
    print('Registered9 matched CB donors and135 target units',B.sha(PLAN),flush=True)


def verify(plan):
    register();assert plan['sources']==sources() and plan['target_code_hash']==core.code_hash(FAMILY),'CB intermediate frozen source drift'
    assert B.sha(MANIFEST)==plan['manifest_sha256']==MANIFEST_SHA


def is_donor(unit):return unit.get('kind')=='donor'
def eid(unit):return unit.get('id',unit.get('experiment_id'))


def ready(unit,root=None):
    if is_donor(unit):return True
    root=Path(root) if root else BASE
    p=root/'units'/f'{unit["spec"]["donor_id"]}.json'
    if not p.is_file():return False
    r=read(p)
    return r.get('status')=='complete' and (bool(r.get('probe'))==bool(root!=BASE)) and Path(r['final_checkpoint']).is_file()


class Stream:
    def __init__(self,man,rows,seed,role,device,probe=False):
        self.idx=V.manifest_index(man);self.seg=self.idx.seg['sparrkulee'];self.rows=np.array(rows,int)
        assert all(self.seg['role'][self.rows]==role)
        self.by={int(f):self.rows[self.seg['family'][self.rows]==f] for f in np.unique(self.seg['family'][self.rows])}
        assert len(self.by)>=2,'contrastive source needs at least two content families'
        self.families=sorted(self.by);self.rng=np.random.default_rng(seed)
        self.offsets=C.TICK_OFFS[C.TICK_OFFS>=26]
        self.bank=V.DonorBank(man,'sparrkulee',(role,),device=device,
                              pieces=np.unique(self.seg['piece'][self.rows]))
        assert self.bank.layout==C.BIOSEMI64
        self.chain='0'*64;self.step=0;self.probe=probe

    def draw(self):
        families=self.rng.choice(self.families,size=min(8,len(self.families)),replace=False)
        rows=np.array([self.by[int(f)][int(self.rng.integers(len(self.by[int(f)])))] for f in families])
        offsets=np.stack([self.rng.choice(self.offsets,size=8,replace=False) for _ in rows])
        assert len(set(self.seg['family'][rows].tolist()))==len(rows)
        body={'rows':rows.tolist(),'offsets':offsets.tolist()}
        self.chain=hashlib.sha256(bytes.fromhex(self.chain)+B.dumps(body).encode()).hexdigest();self.step+=1
        piece=np.repeat(self.seg['piece'][rows],8);start=np.repeat(self.seg['s'][rows],8)
        pres=np.repeat(self.seg['presentation'][rows],8);off=offsets.reshape(-1)
        before=self.bank.gather(piece,start,off-26);after=self.bank.gather(piece,start,off)
        x=torch.cat([before[...,:26],after],dim=-1).float()
        assert x.shape[-1]==64 and bool(torch.isfinite(x).all())
        y=self.bank.targets(pres,start,off)
        keys=torch.tensor(self.idx.keys(pres,start+off),device=x.device)
        # All chosen segment families differ, so a one-segment cycle is always legal.
        wrong=np.roll(np.arange(len(rows)),1)
        assert np.all(self.seg['family'][rows]!=self.seg['family'][rows[wrong]])
        return x,y,keys,torch.tensor((wrong[:,None]*8+np.arange(8)).reshape(-1),device=x.device),body

    def state(self):return {'rng':self.rng.bit_generator.state,'chain':self.chain,'step':self.step}
    def load(self,value):self.rng.bit_generator.state=value['rng'];self.chain=value['chain'];self.step=value['step']


@torch.no_grad()
def validate(model,head,man,pool,seed,device,probe):
    stream=Stream(man,pool['dev'],seed+59000,'dev',device,probe);losses=[]
    model.eval();unknown=L.unknown_clock_families(man)
    for _ in range(2 if probe else 32):
        x,y,keys,_,_=stream.draw();loss,_=L.nce_single_view(model(x),head(y),keys,unknown_clock=unknown)
        losses.append(float(loss))
    return {'paired_dev_nce_nats':float(np.mean(losses)),'batches':len(losses),'stream_sha256':stream.chain}


def run_donor(unit,plan,probe=False):
    from auditory_alignment_v2.foundation_adapter import Backbone
    started=time.time();dev=torch.device('cuda');man=V.open_manifest(MANIFEST,MANIFEST_SHA)
    torch.manual_seed(unit['seed']);ad='random_full' if unit['arm']=='random_paired' else 'pretrained_full'
    model=fm_aligned.AlignedFM(Backbone('cbramod','dtu',ad,64),32).to(dev)
    head=M.fixed_heads(man,man.root)['env'].to(dev).requires_grad_(False)
    assert all(p.requires_grad for p in model.parameters())
    initial={k:v.detach().cpu().clone() for k,v in model.bb.net.state_dict().items()}
    steps=2 if probe else unit['updates'];snapshots=(0,2) if probe else SNAPSHOTS
    out=BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe else BASE
    dest=STORE/('probes/'+os.environ['SLURM_JOB_ID'] if probe else 'donors')/unit['id'];dest.mkdir(parents=True,exist_ok=True)
    opt=torch.optim.AdamW(model.parameters(),lr=3e-4,weight_decay=1e-4);schedule=torch.optim.lr_scheduler.CosineAnnealingLR(opt,steps)
    stream=Stream(man,plan['pool']['fit'],unit['seed']+58000,'fit',dev,probe)
    unknown=L.unknown_clock_families(man);resume=dest/'resume.pt';begin=0;curves=[];interval=[];query_rows=0
    def checkpoint(step):
        metrics=validate(model,head,man,plan['pool'],unit['seed'],dev,probe)
        item={'step':step,**metrics,'fit_loss_mean':float(np.mean(interval)) if interval else None,'seconds':time.time()-started}
        curves.append(item);interval.clear()
        E.atomic_torch(dest/f'update{step}.pt',{'backbone':model.bb.net.state_dict(),'head':model.readout.state_dict(),
                        'step':step,'unit':unit,'plan_sha256':B.sha(PLAN),'stream':stream.state(),'probe':probe})
    if resume.exists():
        state=torch.load(resume,map_location=dev,weights_only=False)
        assert state['plan_sha256']==B.sha(PLAN) and state['probe']==probe
        model.load_state_dict(state['model']);opt.load_state_dict(state['optimizer']);schedule.load_state_dict(state['scheduler'])
        stream.load(state['stream']);begin=state['step'];curves=state['curves'];interval=state['interval'];query_rows=state['query_rows']
        torch.set_rng_state(state['torch_rng'].cpu());torch.cuda.set_rng_state(state['cuda_rng'].cpu())
    else:checkpoint(0)
    for step in range(begin,steps):
        model.train();x,y,keys,wrong,_=stream.draw();v=head(y)
        if unit['arm']=='generic_wrong':v=v[wrong]
        loss,_=L.nce_single_view(model(x),v,keys,unknown_clock=unknown)
        if not torch.isfinite(loss):raise FloatingPointError('nonfinite CB auditory objective')
        opt.zero_grad();loss.backward();gn=torch.nn.utils.clip_grad_norm_(model.parameters(),5.)
        if not torch.isfinite(gn):raise FloatingPointError('nonfinite CB auditory gradient')
        opt.step();schedule.step();query_rows+=len(x);interval.append(float(loss.detach()))
        if step+1 in snapshots:checkpoint(step+1)
        if (step+1)%100==0 or step+1==steps:
            E.atomic_torch(resume,{'model':model.state_dict(),'optimizer':opt.state_dict(),'scheduler':schedule.state_dict(),
                'stream':stream.state(),'step':step+1,'curves':curves,'interval':interval,'query_rows':query_rows,
                'torch_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state(),'plan_sha256':B.sha(PLAN),'probe':probe})
        if (step+1)%1000==0:print(unit['id'],'update',step+1,'stream',stream.chain[:16],flush=True)
    final=dest/f'update{steps}.pt';numerator=denominator=0.
    for name,param in model.bb.net.named_parameters():
        old=initial[name].to(dev);numerator+=float((param.detach()-old).square().sum());denominator+=float(old.square().sum())
    result={'status':'complete','unit':unit,'id':unit['id'],'probe':probe,'plan_sha256':B.sha(PLAN),
            'updates':steps,'query_rows':query_rows,'curves':curves,'stream_sha256':stream.chain,
            'final_checkpoint':str(final),'final_checkpoint_sha256':B.sha(final),'source_sha256':B.sha(__file__),
            'relative_backbone_change':float(np.sqrt(numerator)/(np.sqrt(denominator)+1e-12)),
            'device':torch.cuda.get_device_name(0),'job':os.environ['SLURM_JOB_ID'],'seconds':time.time()-started,
            'gpu_peak_mb':torch.cuda.max_memory_allocated()/2**20,'sampling':'up to8 distinct content families, one segment/family,8 anchors/segment',
            'donor_contract':'64Hz,26before+38after,only SparrKULee; transfer backbone only'}
    B.write(out/'units'/f'{unit["id"]}.json',result);print(unit['id'],'complete',round(time.time()-started,1),flush=True)
    del model,head,stream;gc.collect();torch.cuda.empty_cache()


@contextlib.contextmanager
def target_instrumentation(row,donor,probe):
    old_backbone,old_write=fm_aligned32.Backbone,core.write_record
    state=torch.load(donor['final_checkpoint'],map_location='cpu',weights_only=False)
    assert state['probe']==probe and donor['final_checkpoint_sha256']==B.sha(donor['final_checkpoint'])
    class AuditoryBackbone(old_backbone):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.net.load_state_dict(state['backbone'],strict=True)
    def write(path,rec,start):
        rec.update(plan_sha256=B.sha(PLAN),probe=probe,truncated=probe,baseline_id=row['spec']['baseline_id'],
                   auditory_intermediate={'donor_id':row['spec']['donor_id'],'checkpoint_sha256':donor['final_checkpoint_sha256'],
                   'updates':donor['updates'],'head_transfer':False,'stream_sha256':donor['stream_sha256']})
        old_write(path,rec,start)
    fm_aligned32.Backbone,core.write_record=AuditoryBackbone,write
    try:yield
    finally:fm_aligned32.Backbone,core.write_record=old_backbone,old_write


def run_target(row,plan,probe=False,root=None):
    from .. import run_aligned32
    out=Path(root) if root else BASE;did=row['spec']['donor_id'];donor=read(out/'units'/f'{did}.json')
    assert ready(row,out if probe else None)
    source=plan['baselines'][row['spec']['baseline_id']]
    assert B.sha(Path(core.OUT)/'units'/f'{row["spec"]["baseline_id"]}.json')==source['record_sha256']
    (out/'ckpt').mkdir(parents=True,exist_ok=True)
    with target_instrumentation(row,donor,probe):run_aligned32.run(row,str(out),epochs=2 if probe else 100)
    rec=read(out/'units'/f'{row["experiment_id"]}.json')
    assert rec['status']=='complete' and rec['epochs_completed']==(2 if probe else 100)
    print(row['experiment_id'],'complete','probe',probe,flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--unit');ap.add_argument('--smoke-job');ap.add_argument('--max-units',type=int,default=1)
    a=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if a.make_plan:make_plan();return
    plan=read(PLAN);verify(plan)
    if a.unit:
        u=next(u for u in plan['rows'] if eid(u)==a.unit)
        (run_donor if is_donor(u) else run_target)(u,plan);return
    if a.smoke:
        root=BASE/'probes'/os.environ['SLURM_JOB_ID'];receipt={'status':'running','plan_sha256':B.sha(PLAN),'donors':[],'targets':[]}
        try:
            for arm in ARMS:
                donor=next(u for u in plan['rows'] if is_donor(u) and u['seed']==3401 and u['arm']==arm)
                run_donor(donor,plan,True);receipt['donors'].append(eid(donor))
            hashes={read(root/'units'/f'{d}.json')['stream_sha256'] for d in receipt['donors']};assert len(hashes)==1
            for arm in ARMS:
                row=next(u for u in plan['rows'] if not is_donor(u) and u['dataset']=='dtu' and u['seed']==3401 and u['spec']['intermediate_arm']==arm)
                run_target(row,plan,True,root);receipt['targets'].append(eid(row));gc.collect();torch.cuda.empty_cache()
            receipt['status']='pass';receipt['paired_stream_sha256']=next(iter(hashes))
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(root/'receipt.json',receipt)
        return
    receipt=read(BASE/'probes'/str(a.smoke_job)/'receipt.json')
    assert receipt['status']=='pass' and receipt['plan_sha256']==B.sha(PLAN)
    if list((BASE/'units').glob('*.FAILED.json')):raise RuntimeError('unresolved CB intermediate failure')
    done=0
    for u in plan['rows']:
        ident=eid(u);p=BASE/'units'/f'{ident}.json'
        if p.exists():assert read(p)['status']=='complete';continue
        if not ready(u):continue
        lock=BASE/'claims'/f'{ident}.lock';lock.parent.mkdir(parents=True,exist_ok=True)
        with lock.open('a+') as f:
            try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if p.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m','auditory_alignment_v3.aln34.cb_auditory','--unit',ident]).returncode
            if rc or not p.exists() or read(p).get('probe'):
                B.write(BASE/'units'/f'{ident}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc});raise RuntimeError('CB auditory unit failed')
            done+=1
        if done>=a.max_units:break


if __name__=='__main__':main()
