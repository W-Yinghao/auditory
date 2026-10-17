"""ALN3.4 independent-person task-side adaptation policy (DTU v1)."""
from __future__ import annotations

import argparse
import contextlib
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

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from .. import core
from . import breadth_inner as I
from . import learning_budget as B

BASE = Path(core.OUT)/'aln34/breadth_policy_v1'
PLAN = BASE/'plan.json'
NOTE = Path(core.OUT)/'aln34/PUBLIC_BREADTH_DESIGN_20261017.md'
ADAPTERS = ('none', 'diagonal_spatial', 'lowrank_spatial', 'full_spatial', 'output_low_rank', 'declared_window_temporal')
FRACTIONS = (.1, .3)
STEPS = (0, 20, 50, 100)


class Adapter(nn.Module):
    def __init__(self, base, kind, channels, dim=32, rank=4):
        super().__init__()
        if kind not in ADAPTERS:
            raise ValueError(kind)
        self.base, self.kind = base, kind
        self.base.requires_grad_(False)
        self.base.eval()
        if kind == 'diagonal_spatial':
            self.scale = nn.Parameter(torch.zeros(channels))
        elif kind == 'lowrank_spatial':
            self.A = nn.Parameter(torch.randn(rank, channels)*.01)
            self.B = nn.Parameter(torch.zeros(channels, rank))
        elif kind == 'full_spatial':
            self.matrix = nn.Parameter(torch.eye(channels))
        elif kind == 'output_low_rank':
            self.A = nn.Parameter(torch.randn(rank, dim)*.01)
            self.B = nn.Parameter(torch.zeros(dim, rank))
        elif kind == 'declared_window_temporal':
            self.taps = nn.Parameter(torch.zeros(3))

    def train(self, mode=True):
        super().train(mode)
        self.base.eval()
        return self

    def transform(self, x):
        if self.kind == 'diagonal_spatial':
            return x*self.scale.exp()[:, None]
        if self.kind == 'lowrank_spatial':
            return x + torch.einsum('cr,rd,...dt->...ct', self.B, self.A, x)
        if self.kind == 'full_spatial':
            return torch.einsum('cd,...dt->...ct', self.matrix, x)
        if self.kind == 'declared_window_temporal':
            shifted = (F.pad(x[..., :-1], (1,0)), x, F.pad(x[..., 1:], (0,1)))
            return x + sum(a*z for a,z in zip(self.taps, shifted))
        return x

    def forward(self, x):
        value = [self.transform(y) for y in x] if isinstance(x, list) else self.transform(x)
        u = self.base(value)
        return F.normalize(u + u@self.A.T@self.B.T, dim=-1) if self.kind == 'output_low_rank' else u


def split_items(items, fraction):
    if fraction not in FRACTIONS or len(items) < 6:
        raise ValueError('registered support fraction and at least six segments required')
    q0 = int(round(.3*len(items)))
    ns = max(1, int(round(fraction*len(items))))
    assert ns <= q0
    return items[:ns], items[q0:]


def select_step(scores):
    good = [(float(loss), int(step)) for step, loss in scores.items() if np.isfinite(loss)]
    if not good:
        raise ValueError('no finite inner-development candidate')
    return min(good)[1]


def sources():
    files = {Path(__file__), NOTE, Path(I.__file__), Path(B.__file__)}
    for g in ('local_support', 'aligned32'):
        files.update(Path(core.REPO)/d/f for d,f in core.FAMILY_CODE[g]+core.V2_DEPS)
    return {str(f.relative_to(core.REPO)): B.sha(f) for f in sorted(files)}


def make_plan():
    inner_plan = json.loads(I.PLAN.read_text())
    I.verify(inner_plan)
    rows = []
    for inner in inner_plan['rows']:
        s = inner['spec']
        if inner['dataset'] != 'fau' or s['axis'] != 'inner_person' or s['architecture'] == 'reve' and s['adaptation'] != 'pretrained_full':
            continue
        source = inner_plan['baselines'][s['baseline_id']]
        body = {'card':'E34_NEW_D_POLICY', 'outer_source':source, 'inner_source':inner,
                'inner_plan_sha256':B.sha(I.PLAN), 'adapters':ADAPTERS, 'support':FRACTIONS, 'steps':STEPS,
                'design_sha256':B.sha(NOTE)}
        body['id'] = 'ALN34BD_'+hashlib.sha256(B.dumps(body).encode()).hexdigest()[:16]
        rows.append(body)
    assert len(rows) == len({r['id'] for r in rows}) == 40
    body = {'version':'ALN34_NEW_D_POLICY_v1', 'created':datetime.now().astimezone().isoformat(),
            'rows':rows, 'sources':sources(), 'inner_plan_sha256':B.sha(I.PLAN)}
    if PLAN.exists():
        old = json.loads(PLAN.read_text())
        assert all(old[k] == v for k,v in body.items() if k != 'created')
    else:
        B.write(PLAN, body)
        PLAN.chmod(0o444)
    print(f'Registered 40 FAU adaptation-policy units; {B.sha(PLAN)}', flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'frozen source drift'
    assert plan['inner_plan_sha256'] == B.sha(I.PLAN)


def ready(unit, probe_root=None):
    inner = unit['inner_source']['experiment_id']
    root = Path(probe_root) if probe_root else I.BASE
    record, ckpt = root/'units'/f'{inner}.json', root/'ckpt'/f'{inner}_best.pt'
    if not record.is_file() or not ckpt.is_file():
        return False
    rec = json.loads(record.read_text())
    return rec.get('status') == 'complete' and bool(rec.get('truncated')) == bool(probe_root)


def rebuild(row, root, inner_plan=None, allow_probe=False):
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v2.audio_targets import build_head, target_stats
    from auditory_alignment_v2.temporal import build_encoder
    from auditory_alignment_v2.foundation_adapter import Backbone
    from .. import fm_aligned, local_support
    root = Path(root)
    path, cp = root/'units'/f'{row["experiment_id"]}.json', root/'ckpt'/f'{row["experiment_id"]}_best.pt'
    record = json.loads(path.read_text())
    assert record['status'] == 'complete' and record['row'] == row
    assert record['code_hash'] == core.code_hash(row['family_id']), 'source code mismatch'
    assert bool(record.get('truncated')) == bool(allow_probe)
    dev = torch.device('cuda')
    torch.manual_seed(row['seed'])
    b = core.bind(row)
    coh = load_cohort(b)
    grid = core.grid_samples(coh.fs)
    local = row['spec']['architecture'] == 'lag_local_tokens'
    ctx = I.instrumentation(row, inner_plan, row['spec']['epochs']) if inner_plan is not None else contextlib.nullcontext()
    with ctx:
        if local:
            bt = local_support.batcher_for('aligned1000')(coh,b['spec'],b,dev,grid)
            model = build_encoder('lag_local_tokens',coh.n_ch,32,bt.W,coh.fs).to(dev)
        else:
            bt = fm_aligned.AlignedBatcher(coh,b['spec'],b,dev,grid)
            model = fm_aligned.AlignedFM(Backbone(row['spec']['architecture'],row['dataset'],row['spec']['adaptation'],coh.fs),32).to(dev)
    # The inner batcher has the correct fit set; no full-outer audio statistics are used.
    head = build_head('fixed_features',bt.audio_dim,32,coh.meta['dataset'],target_stats(bt,np.random.default_rng(row['seed']+5))).to(dev)
    sd = torch.load(cp,map_location=dev,weights_only=False)
    model.load_state_dict(sd['enc'] if local else sd['model'],strict=True)
    if local:
        head.load_state_dict(sd['head'],strict=True)
    model.requires_grad_(False).eval(); head.requires_grad_(False).eval()
    return Bundle(row,record,coh,bt,model,head,grid,local), {'record_sha256':B.sha(path),'checkpoint_sha256':B.sha(cp),'path':str(cp)}


class Bundle:
    def __init__(self,row,record,coh,bt,model,head,grid,local):
        from auditory_alignment import evaluate as E
        from auditory_alignment_v3.fm_aligned import AlignedReps
        self.row,self.record,self.coh,self.bt,self.model,self.head,self.grid,self.local = row,record,coh,bt,model,head,grid,local
        self.reps_of = lambda m: E.Reps(m,head,bt,stride=grid) if local else AlignedReps(m,head,bt,grid)
        self.reps = self.reps_of(model)
        self.segs = coh.segments
        self.rng = np.random.default_rng(row['seed']+1000)
        training = [s for s in self.segs if s['p'] in bt.train_p and s['kind']=='ss' and s['role'] in ('fit','es')]
        self.readout = E.Readouts('NCE',self.reps,training,self.rng)
        uid, pool = self.pool('es')
        queries = [s for s in self.segs if s['p'] in bt.train_p and s['kind']=='ss' and s['role']=='es']
        queries = [queries[i] for i in self.rng.choice(len(queries),size=min(300,len(queries)),replace=False)]
        V,A = self.reps.va([s['s0'] for s in pool])
        U = self.reps.u([s['e0'] for s in queries])
        self.readout.calibrate({k:self.readout.scores(U,V,A,k) for k in ('native','unified')},np.array([uid[s['uid']] for s in queries]))

    def pool(self,role):
        uid,rows = {},[]
        for s in self.segs:
            if s['role']==role and s['kind']=='ss' and s['uid'] not in uid:
                uid[s['uid']]=len(rows);rows.append(s)
        return uid,rows

    def items(self,p,role):
        return sorted([s for s in self.segs if s['p']==p and s['role']==role and s['kind']=='ss'],key=lambda s:s['e0'])

    def fit_adapter(self,kind,support,query,steps,seed):
        from auditory_alignment.train import Objective
        torch.manual_seed(seed)
        m = Adapter(self.model,kind,self.coh.n_ch).to(self.bt.dev)
        ps = [p for p in m.parameters() if p.requires_grad]
        step = max(self.grid,(self.bt.seg_len//8)//self.grid*self.grid)
        # A fixed eligible anchor set, independently of iteration and adapter.
        anchors = [(s,t) for s in support for t in np.arange(0,self.bt.seg_len,step)[:8]
                   if s['e0']+int(t)+int(round(.6*self.bt.fs)) <= query[0]['e0']]
        if len(anchors) < 2:
            raise ValueError('support has fewer than two directly disjoint anchors')
        if kind=='none' or steps==0:
            return m.eval(), len(anchors)
        objective = Objective({'objective':'NCE','config':{'temperature':.1}},torch.zeros(4,32,device=self.bt.dev),torch.zeros(4,32,device=self.bt.dev))
        opt = torch.optim.Adam(ps,lr=1e-3)
        rng = np.random.default_rng(seed)
        for _ in range(steps):
            ix = rng.choice(len(anchors),size=min(256,len(anchors)),replace=False)
            picked = [anchors[i] for i in ix]
            e = torch.tensor([s['e0']+int(t) for s,t in picked],device=self.bt.dev)
            a = torch.tensor([s['s0']+int(t) for s,t in picked],device=self.bt.dev)
            keys = torch.tensor([hash(s['uid'])%(2**31)*1000+int(t) for s,t in picked],device=self.bt.dev)
            if self.local:
                x = self.bt.patches(e)
            else:
                starts = torch.tensor([s['e0'] for s,t in picked],device=self.bt.dev)
                offsets = torch.tensor([[int(t)] for s,t in picked],device=self.bt.dev)
                x = self.bt.windows(starts,offsets)
            m.train()
            loss,_ = objective(m(x),self.head(self.bt.audio(a)),keys=keys)
            if not torch.isfinite(loss):
                raise FloatingPointError('nonfinite adaptation loss')
            opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(ps,5.0);opt.step()
        return m.eval(), len(anchors)

    def evaluate(self,m,query,pool):
        from auditory_alignment import evaluate as E
        uid,V,A = pool
        U = self.reps_of(m).u([s['e0'] for s in query])
        own = np.array([uid[s['uid']] for s in query])
        out = {}
        for mode in ('native','unified'):
            true = E._metrics(self.readout.scores(U,V,A,mode),own,self.readout.tau[mode])
            wrong = E._metrics(self.readout.scores(np.roll(U,1,axis=0),V,A,mode),own,self.readout.tau[mode])
            out[mode] = {'true_nll_bits':true['logloss_bits'],'mismatch_gain_bits':wrong['logloss_bits']-true['logloss_bits'],
                         'rank_pct':true['rank_pct'],'top1':true['top1'],'n_query':len(query)}
        return out

    def eval_pool(self,role):
        uid,rows = self.pool(role)
        V,A = self.reps.va([s['s0'] for s in rows])
        return uid,V,A


def run_unit(unit,probe_root=None):
    start = time.time()
    inner_plan = json.loads(I.PLAN.read_text())
    I.verify(inner_plan)
    assert ready(unit,probe_root)
    split = inner_plan['splits'][unit['inner_source']['spec']['split_key']]
    bundle,inner_prov = rebuild(unit['inner_source'],probe_root or I.BASE,inner_plan, bool(probe_root))
    people = [i for i,p in enumerate(bundle.coh.participants) if p['id'] in split['inner_ids']]
    if probe_root:
        people=people[:1]
    pool = bundle.eval_pool('es')
    candidates,chosen = {},{}
    step_set = (0,2) if probe_root else STEPS
    for kind in ADAPTERS:
        for frac in FRACTIONS:
            key=f'{kind}|{frac}'
            candidate={}
            for steps in ((0,) if kind=='none' else step_set):
                per={}
                for p in people:
                    items=bundle.items(p,'es')
                    if len(items)<6:
                        continue
                    support,query=split_items(items,frac)
                    if probe_root:
                        query=query[:6]
                    model,n=bundle.fit_adapter(kind,support,query,steps,unit['inner_source']['seed']+p)
                    per[bundle.coh.participants[p]['id']]={**bundle.evaluate(model,query,pool),'eligible_support_anchors':n}
                if not per:
                    raise ValueError('no valid inner-development identities')
                candidate[str(steps)]={'mean_native_true_nll':float(np.mean([x['native']['true_nll_bits'] for x in per.values()])), 'per_participant':per}
            chosen[key]=select_step({k:v['mean_native_true_nll'] for k,v in candidate.items()})
            candidates[key]=candidate
    del bundle,model,pool
    torch.cuda.empty_cache()
    source=unit['outer_source']
    sourcepath=Path(core.OUT)/'units'/f'{source["row"]["experiment_id"]}.json'
    assert B.sha(sourcepath)==source['record_sha256']
    bundle,outer_prov=rebuild(source['row'],core.OUT)
    assert outer_prov['checkpoint_sha256']==source['checkpoint_sha256']
    people=[i for i,p in enumerate(bundle.coh.participants) if p['fold']==source['row']['subject_fold']]
    if probe_root:
        people=people[:1]
    pool=bundle.eval_pool('test')
    per={}
    for p in people:
        items=bundle.items(p,'test')
        if len(items)<6:
            continue
        _,query=split_items(items,.3)
        if probe_root:
            query=query[:6]
        base=bundle.evaluate(bundle.model,query,pool)
        values={}
        for kind in ADAPTERS:
            for frac in FRACTIONS:
                support,_=split_items(items,frac)
                key=f'{kind}|{frac}'
                model,n=bundle.fit_adapter(kind,support,query,chosen[key],source['row']['seed']+p)
                value=bundle.evaluate(model,query,pool)
                for mode in ('native','unified'):
                    value[mode]['benefit_bits']=base[mode]['true_nll_bits']-value[mode]['true_nll_bits']
                ps=[x for x in model.parameters() if x.requires_grad]
                values[key]={**value,'steps':chosen[key],'n_support_segments':len(support),'eligible_support_anchors':n,
                             'adapter_parameters':sum(x.numel() for x in ps)}
        per[bundle.coh.participants[p]['id']]={'group':bundle.coh.participants[p]['group'],'base':base,'policies':values,
                                             'query_e0':[s['e0'] for s in query]}
    output={'status':'complete','id':unit['id'],'unit':unit,'probe':bool(probe_root),'inner_provenance':inner_prov,
            'outer_provenance':outer_prov,'chosen_steps':chosen,'development':candidates,'per_participant':per,
            'plan_sha256':B.sha(PLAN),'job':os.environ['SLURM_JOB_ID'],'seconds':time.time()-start,
            'gpu_peak_mb':torch.cuda.max_memory_allocated()/2**20,'selection_level':'one inner-person split; entire encoder excludes inner/outer people',
            'limitations':['historical noncausal input filter retained','fixed source readout after adaptation','known labelled support sounds']}
    dest=BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe_root else BASE/'units'
    B.write(dest/f'{unit["id"]}.json',output)
    print(f'{unit["id"]} complete probe={bool(probe_root)} {time.time()-start:.1f}s',flush=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--make-plan',action='store_true')
    ap.add_argument('--unit')
    ap.add_argument('--probe-root',type=Path)
    ap.add_argument('--smoke-receipt',type=Path)
    args=ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'),'Slurm required'
    os.umask(0o077)
    if args.make_plan:
        make_plan();return
    plan=json.loads(PLAN.read_text());verify(plan)
    if args.unit:
        unit=next(x for x in plan['rows'] if x['id']==args.unit)
        run_unit(unit,args.probe_root);return
    if args.probe_root:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            for arch in ('lag_local_tokens','cbramod','reve'):
                unit=next(x for x in plan['rows'] if x['inner_source']['spec']['architecture']==arch and ready(x,args.probe_root))
                run_unit(unit,args.probe_root);receipt['units'].append(unit['id'])
            receipt['status']='pass'
        except BaseException:
            receipt['status']='failed';receipt['traceback']=traceback.format_exc()
            raise
        finally:
            B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    smoke=json.loads(args.smoke_receipt.read_text())
    assert smoke['status']=='pass' and smoke['plan_sha256']==B.sha(PLAN)
    for unit in plan['rows']:
        if not ready(unit) or (BASE/'units'/f'{unit["id"]}.json').exists():
            continue
        lock=BASE/'claims'/f'{unit["id"]}.lock';lock.parent.mkdir(exist_ok=True)
        with lock.open('a+') as f:
            try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError: continue
            subprocess.run([sys.executable,'-B','-m','auditory_alignment_v3.aln34.breadth_policy','--unit',unit['id']],check=True)


if __name__=='__main__':
    main()
