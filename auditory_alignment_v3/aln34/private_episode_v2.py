"""Versioned private episode repair: keep CS singleton-support queries with identity adaptation."""
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

from .. import core, local_train
from ..sci_r1 import private_task as P
from ..aln3_reference.calibration import AffineLogitCalibrator
from . import learning_budget as B, private_current_time as C, private_calibration_loo as L
from . import adaptation_policy as D, episode_training as E

BASE = Path(core.OUT)/'aln34/private_episode_v2'
PLAN = BASE/'plan.json'
NOTE = Path(core.OUT)/'aln34/PRIVATE_EPISODE_SINGLETON_CORRECTION_20261017.md'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln34_private_episode_v2')
REGIMES = ('ordinary', 'episode')
FRACTIONS = (.1, .3)
STEPS = (0, 5, 20)
UPDATES = 100


def read(path): return json.loads(Path(path).read_text())


def sources():
    files = {Path(__file__), NOTE, Path(__file__).with_name('private_episode.py'), Path(B.__file__), Path(C.__file__), Path(L.__file__),
             Path(D.__file__), Path(E.__file__), Path(P.__file__)}
    for family in ('E_LOCAL', 'E_GENERIC'):
        files.update(Path(core.REPO)/d/f for d, f in core.FAMILY_CODE[core.FAMILY_GROUP[family]]+core.V2_DEPS)
    return {str(p.relative_to(core.REPO)): B.sha(p) for p in sorted(files)}


def take(row):
    s = row['spec']; obj = s['objective']
    if row['family_id'] == 'E_LOCAL':
        return s.get('architecture') == 'lag_local_tokens' and s.get('window') == 'full' and obj in ('NCE', 'CS_SINGLE')
    return (row['family_id'] == 'E_GENERIC' and s.get('adaptation') == 'pretrained_full' and obj == 'NCE'
            and (s['architecture'] == 'cbramod' or s['architecture'] == 'reve' and row['seed'] == 3401))


def partitions(kids, sf, inner=True):
    held = (sf+1) % 5
    tr = [i for i, k in enumerate(kids) if k['fold'] != sf and (not inner or k['fold'] != held)]
    dev = [i for i, k in enumerate(kids) if k['fold'] == held]
    te = [i for i, k in enumerate(kids) if k['fold'] == sf]
    assert tr and dev and te and not set(tr)&set(te)
    if inner: assert not set(tr)&set(dev)
    return tr, dev, te


def split_blocks(kid, fraction, fit_only=False):
    eligible = ~kid['es_mask'] if fit_only else np.ones(len(kid['y']), bool)
    blocks = np.unique(kid['block'][eligible]); n = len(blocks)
    if n < 2: return np.array([], int), np.array([], int)
    q0 = min(n-1, max(1, int(np.ceil(.3*n))))
    ns = min(q0, max(1, int(np.floor(fraction*n))))
    support = np.flatnonzero(eligible & np.isin(kid['block'], blocks[:ns]))
    query = np.flatnonzero(eligible & np.isin(kid['block'], blocks[q0:]))
    # The fixed query set is identical for both support fractions.
    support, query = support[:-1], query[1:]
    assert not set(kid['block'][support]) & set(kid['block'][query])
    return support, query


def make_plan():
    from auditory_alignment import data
    cp = read(C.PLAN); C.verify(cp); kids = data.load_private(); rows = []
    for source in cp['rows']:
        row = source['source']
        if not take(row): continue
        old = read(Path(core.OUT)/'units'/f'{row["experiment_id"]}.json')
        tr, dev, te = partitions(kids, row['subject_fold'])
        unit = {'source': row, 'record_sha256': source['record_sha256'], 'checkpoint_sha256': source['checkpoint_sha256'],
                'resolved_config': old['resolved_config'], 'inner_fold': (row['subject_fold']+1)%5,
                'inner_train_ids': sorted(kids[i]['id'] for i in tr), 'inner_dev_ids': sorted(kids[i]['id'] for i in dev),
                'outer_test_ids': sorted(kids[i]['id'] for i in te), 'design_sha256': B.sha(NOTE)}
        unit['id'] = 'ALN34PE2_'+hashlib.sha256(B.dumps(unit).encode()).hexdigest()[:16]
        rows.append(unit)
    rows.sort(key=lambda u: (u['source']['seed'], u['source']['subject_fold'], u['source']['spec']['architecture'], u['source']['spec']['objective']))
    assert len(rows) == len({u['id'] for u in rows}) == 50, len(rows)
    body = {'version': 'ALN34_PRIVATE_EPISODE_v2', 'created': datetime.now().astimezone().isoformat(),
            'rows': rows, 'sources': sources(), 'private_science_plan_sha256': B.sha(C.PLAN)}
    if PLAN.exists(): assert all(read(PLAN)[k] == v for k, v in body.items() if k != 'created')
    else:
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700); B.write(PLAN, body); PLAN.chmod(0o444)
    print('Registered50 private episode bundles,50 inner sources,200 continuations', B.sha(PLAN), flush=True)


def verify(plan):
    assert plan['sources'] == sources() and plan['private_science_plan_sha256'] == B.sha(C.PLAN), 'private episode source drift'


class Fold(P.Fold):
    def __init__(self, kids, tr, te):
        from auditory_c3.c3dl.hc import q0_table, _logit
        self.kids, self.tr, self.te = kids, tr, te
        self.q0 = q0_table([kids[i] for i in tr]); self.logit = _logit
        self.base = float(np.concatenate([kids[i]['y'] for i in tr]).mean())
        self.es = {i: kids[i]['es_mask'] for i in tr}
        self.y_es = np.concatenate([kids[i]['y'][self.es[i]] for i in tr])
        self.off_es = _logit(self.q0[np.concatenate([kids[i]['bin'][self.es[i]] for i in tr])])


def batcher(row, kids, dev, tr):
    from auditory_alignment_v2.train import PrivateBatcher
    from auditory_alignment_v2.train_fm import PrivateFMBatcher
    b = core.bind(row)
    cls = PrivateBatcher if row['family_id'] == 'E_LOCAL' else PrivateFMBatcher
    bt = cls(kids, b['spec'], b, dev)
    bt.train = list(tr)
    bt.fit_idx = {i: bt.fit_idx[i] for i in tr}; bt.es_idx = {i: bt.es_idx[i] for i in tr}
    return bt


def new_encoder(row, bt, device):
    from auditory_alignment_v2.temporal import build_encoder
    from auditory_alignment_v2.foundation_adapter import Backbone
    if row['family_id'] == 'E_LOCAL':
        return build_encoder('lag_local_tokens', 20, 32, bt.W, 250).to(device)
    return local_train.EpochEncoder(Backbone(row['spec']['architecture'], 'private_bdf', row['spec']['adaptation'], 250), 32).to(device)


def inner_source(unit, kids, dest, probe):
    row = unit['source']; tr, dv, te = partitions(kids, row['subject_fold'])
    assert sorted(kids[i]['id'] for i in tr) == unit['inner_train_ids']
    path = dest/'inner_source'; path.mkdir(parents=True, exist_ok=True, mode=0o700)
    meta = path/'record.json'; prefix = str(path/'model'); dev = torch.device('cuda')
    if not meta.exists():
        intent = {'unit': unit['id'], 'plan_sha256': B.sha(PLAN), 'probe': probe, 'train_ids': unit['inner_train_ids']}
        if (path/'intent.json').exists(): assert read(path/'intent.json') == intent
        else: B.write(path/'intent.json', intent)
        b = core.bind(row); b['experiment_id'] = unit['id']+'_inner'
        b['spec']['epochs'] = 1 if probe else unit['resolved_config']['epochs']
        log = {}; training = [kids[i] for i in tr]; cfg = unit['resolved_config']
        if row['family_id'] == 'E_LOCAL':
            enc, bt, protos = local_train.fit_private(b, training, dev, prefix, log, d=32)
        else:
            enc, bt, protos = local_train.fit_private_fm(b, training, dev, prefix, log, cfg['lr_backbone'], cfg['lr_head'],
                                                     b['spec']['epochs'], row['spec']['adaptation'], d=32)
        B.write(meta, {**intent, 'status': 'complete', 'row': row, **log, 'checkpoint_sha256': B.sha(prefix+'_best.pt')})
        del enc, bt, protos; gc.collect(); torch.cuda.empty_cache()
    rec = read(meta)
    assert rec['status'] == 'complete' and rec['plan_sha256'] == B.sha(PLAN) and rec['probe'] == probe
    assert B.sha(prefix+'_best.pt') == rec['checkpoint_sha256']
    torch.manual_seed(row['seed']); bt = batcher(row, kids, dev, tr); enc = new_encoder(row, bt, dev)
    state = torch.load(prefix+'_best.pt', map_location=dev, weights_only=False)
    enc.load_state_dict(state['enc']); enc.requires_grad_(False).eval()
    return enc, state['protos'].detach(), rec, bt, Fold(kids, tr, dv)


def original_source(unit, kids):
    row = unit['source']; root = Path(core.OUT); eid = row['experiment_id']
    assert B.sha(root/'units'/f'{eid}.json') == unit['record_sha256'] and B.sha(root/'ckpt'/f'{eid}_best.pt') == unit['checkpoint_sha256']
    torch.manual_seed(row['seed']); enc, proto, rec, bt = L.rebuild(row, kids, torch.device('cuda'))
    tr, _, te = partitions(kids, row['subject_fold'], inner=False)
    assert bt.train == tr
    enc.requires_grad_(False).eval()
    return enc, proto.detach(), rec, bt, Fold(kids, tr, te)


def objective(rec):
    from auditory_alignment.train import Objective
    obj = Objective.__new__(Objective); obj.name = rec['row']['spec']['objective']
    for k, v in rec['objective_calibration'].items(): setattr(obj, k, v)
    return obj


def support_policy(objective_name, n_support, steps):
    minimum = 2 if objective_name == 'CS_SINGLE' else 1
    reason = 'zero_step_candidate' if not steps else 'insufficient_support' if n_support < minimum else None
    return {'minimum_support_trials':minimum, 'requested_adapter_steps':steps,
            'effective_adapter_steps':0 if reason else steps, 'identity_fallback_reason':reason,
            'insufficient_support_identity_fallback':bool(steps and n_support < minimum)}


def fit_adapter(enc, bt, child, idx, obj, protos, steps, seed):
    torch.manual_seed(seed); adapted = D.Adapter(enc, 'lowrank_spatial', 20).to(bt.dev).eval()
    params = [p for name, p in adapted.named_parameters() if not name.startswith('base.')]
    if not support_policy(obj.name, len(idx), steps)['effective_adapter_steps']: return adapted
    opt = torch.optim.Adam(params, lr=1e-3); rng = np.random.default_rng(seed)
    for _ in range(steps):
        chosen = rng.choice(idx, size=min(128, len(idx)), replace=False)
        ix = torch.tensor(chosen, device=bt.dev)
        labels = torch.tensor(bt.kids[child]['y'][chosen], device=bt.dev)
        loss, _ = obj(adapted(bt.patches(child, ix)), labels=labels, prototypes=protos)
        if not torch.isfinite(loss): raise FloatingPointError('nonfinite private support objective')
        opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(params, 5.); opt.step()
    return adapted.eval()


@torch.no_grad()
def representations(enc, bt, child, idx=None):
    if idx is None: idx = np.arange(len(bt.kids[child]['y']))
    values = []
    for pos in range(0, len(idx), 128):
        ix = torch.tensor(idx[pos:pos+128], device=bt.dev)
        values.append(enc(bt.patches(child, ix)).cpu().numpy())
    return np.concatenate(values) if values else np.empty((0, 32))


def continue_source(enc, bt, protos, rec, initial, regime, dest, probe):
    steps = 2 if probe else UPDATES; path = dest/f'{regime}.pt'; resume = dest/f'{regime}_resume.pt'
    if path.exists():
        state = torch.load(path, map_location='cpu', weights_only=False)
        assert state['source_sha256'] == B.sha(__file__) and state['updates'] == steps
        return state['ledger']
    enc.load_state_dict(initial); enc.requires_grad_(True).eval(); params = list(enc.parameters())
    arch = rec['row']['spec']['architecture']; lr = {'lag_local_tokens':1e-4, 'cbramod':3e-5, 'reve':1e-6}[arch]
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps); obj = objective(rec)
    rng = np.random.default_rng(rec['row']['seed']+41000); eligible = {}; unavailable = []
    for i in bt.train:
        support, query = split_blocks(bt.kids[i], .3, True)
        if len(support) >= 2 and len(query) >= 2: eligible[i] = (support, query)
        else: unavailable.append(bt.kids[i]['id'])
    if not eligible: raise ValueError('no source child with disjoint fit blocks')
    people = sorted(eligible); started = time.time()
    ledger = {'regime':regime, 'encoder_updates':0, 'query_trials':0, 'support_steps':0, 'support_trials':0,
              'source_ids':[bt.kids[i]['id'] for i in people], 'unavailable_episode_ids':unavailable, 'losses':[],
              'lr':lr, 'mode':'eval with gradients', 'sham_support':regime == 'ordinary'}
    if resume.exists():
        state = torch.load(resume, map_location=bt.dev, weights_only=False)
        assert state['source_sha256'] == B.sha(__file__)
        enc.load_state_dict(state['model']); opt.load_state_dict(state['optimizer']); sched.load_state_dict(state['scheduler'])
        rng.bit_generator.state = state['rng']; ledger = state['ledger']
    for step in range(ledger['encoder_updates'], steps):
        i = people[int(rng.integers(len(people)))]; support, query = eligible[i]
        adapted = fit_adapter(enc, bt, i, support, obj, protos, 1 if probe else 3, rec['row']['seed']+42000+step)
        for name, p in adapted.named_parameters():
            if not name.startswith('base.'): p.requires_grad_(False)
        enc.requires_grad_(True).eval()
        chosen = rng.choice(query, size=min(64, len(query)), replace=False); ix = torch.tensor(chosen, device=bt.dev)
        labels = torch.tensor(bt.kids[i]['y'][chosen], device=bt.dev)
        loss, _ = obj((adapted if regime == 'episode' else enc)(bt.patches(i, ix)), labels=labels, prototypes=protos)
        if not torch.isfinite(loss): raise FloatingPointError('nonfinite private episode query objective')
        opt.zero_grad(); loss.backward(); gn = torch.nn.utils.clip_grad_norm_(params, 5.)
        if not torch.isfinite(gn): raise FloatingPointError('nonfinite private episode gradient')
        opt.step(); sched.step(); ledger['encoder_updates'] = step+1
        ledger['query_trials'] += len(chosen); ledger['support_steps'] += 1 if probe else 3
        ledger['support_trials'] += min(128, len(support))*(1 if probe else 3); ledger['losses'].append(float(loss.detach()))
        del adapted, loss
        if (step+1)%20 == 0 or step+1 == steps:
            E.atomic_torch(resume, {'model':enc.state_dict(), 'optimizer':opt.state_dict(), 'scheduler':sched.state_dict(),
                                   'rng':rng.bit_generator.state, 'ledger':ledger, 'source_sha256':B.sha(__file__)})
    num = sum(float((p.detach()-initial[k].to(p.device)).square().sum()) for k,p in enc.named_parameters())
    den = sum(float(initial[k].square().sum()) for k,_ in enc.named_parameters())
    ledger.update(seconds=time.time()-started, relative_parameter_change=float(np.sqrt(num)/(np.sqrt(den)+1e-12)),
                  trainable_parameters=sum(p.numel() for p in params))
    E.atomic_torch(path, {'model':enc.state_dict(), 'ledger':ledger, 'updates':steps, 'source_sha256':B.sha(__file__)})
    enc.requires_grad_(False).eval(); return ledger


class Readouts:
    def __init__(self, rec, protos, fd, U):
        from auditory_c3.c3dl_stage0 import _fit_offset_logistic
        self.native = P.Native(rec, protos, fd, U); X = fd.es_rows(U)
        self.probe = P.Probe(X, fd.y_es)
        self.history = _fit_offset_logistic((X-self.probe.mu)/self.probe.sd, fd.y_es, fd.off_es)
        raw = np.concatenate([self.native(U[i][fd.es[i]]) for i in fd.tr])
        self.calibration_kind = 'positive_affine_source_ES'
        if self.native.obj == 'CS_SINGLE':
            sel = np.random.default_rng(rec['row']['seed']+77).choice(len(X), size=min(6000, len(X)), replace=False)
            offset = 0; adjusted = []
            for i in fd.tr:
                x = U[i][fd.es[i]]; positions = np.flatnonzero((sel >= offset)&(sel < offset+len(x)))
                local = sel[positions]-offset
                n, d, w = L.kernel_mass(x, self.native.Xs, self.native.ys, rec['objective_calibration']['sigma_u'], fd.base, (local,positions))
                n, d = L.remove_self(n, d, local, fd.y_es[sel[positions]], w)
                adjusted.append(L.logit_mass(n,d)); offset += len(x)
            raw = np.concatenate(adjusted); self.calibration_kind = 'positive_affine_source_ES_leave_self_out'
        self.native_cal = AffineLogitCalibrator.fit(raw, fd.y_es)

    def evaluate(self, U, kid, idx, fd):
        ns = self.native(U); ls = self.probe.score(U); y = kid['y'][idx]
        out = {'native':C.clean_metrics(ns, self.native_cal.predict(ns), y, fd.base),
               'linear':C.clean_metrics(ls, self.probe.cal.predict(ls), y, fd.base)}
        out['history'] = C.history_metrics(fd, kid, U, self.probe, self.history, idx)
        return out


def evaluate(enc, bt, protos, rec, fd, probe):
    enc.requires_grad_(False).eval(); U = {i:representations(enc, bt, i) for i in fd.tr}
    ro = Readouts(rec, protos, fd, U); obj = objective(rec); candidates = {}
    for fraction in FRACTIONS:
        candidates[str(fraction)] = {}
        for steps in ((0,1) if probe else STEPS):
            per = {}
            for i in (fd.te[:1] if probe else fd.te):
                kid = fd.kids[i]; support, query = split_blocks(kid, fraction)
                if not len(query):
                    per[kid['id']] = {'status':'no_query', 'group':kid['group']}; continue
                m = fit_adapter(enc, bt, i, support, obj, protos, steps, rec['row']['seed']+i+43000)
                values = ro.evaluate(representations(m, bt, i, query), kid, query, fd)
                per[kid['id']] = {'status':'complete', 'group':kid['group'], **values,
                                 'n_support_trials':len(support), 'n_support_blocks':len(np.unique(kid['block'][support])),
                                 'n_support_classes':len(np.unique(kid['y'][support])), 'n_query_trials':len(query),
                                 'n_query_blocks':len(np.unique(kid['block'][query])),
                                 'no_support_identity_fallback':not len(support),
                                 **support_policy(obj.name, len(support), steps)}
                del m
            valid = [v['native']['nll_bits'] for v in per.values() if v['status']=='complete']
            if not valid: raise ValueError('no valid private evaluation query')
            candidates[str(fraction)][str(steps)] = {'per_participant':per, 'mean_native_true_nll':float(np.mean(valid))}
    return {'candidates':candidates, 'readouts':{'native_calibration_kind':ro.calibration_kind,
            'native_calibration':ro.native_cal.to_dict(), 'linear_calibration':ro.probe.cal.to_dict(),
            'source_ES_trials':len(fd.y_es), 'source_ids':[fd.kids[i]['id'] for i in fd.tr]}}


def choose(inner, outer):
    result = {}
    for regime in REGIMES:
        result[regime] = {}
        for frac in map(str, FRACTIONS):
            risks = {f'{name}/{step}':v['mean_native_true_nll'] for name in ('source',regime)
                     for step,v in inner[name]['candidates'][frac].items()}
            selected = min((v,i,k) for i,(k,v) in enumerate(risks.items()))[2]
            name, step = selected.split('/')
            result[regime][frac] = {'chosen':selected, 'inner_risks':risks,
                                    'outer':outer[name]['candidates'][frac][step]}
    return result


def smoke_kids(kids):
    for k in kids:
        n = len(k['y']); ix = np.unique(np.linspace(0, n-1, min(64,n)).round().astype(int))
        for key,value in list(k.items()):
            if isinstance(value,np.ndarray) and value.ndim and len(value)==n: k[key]=value[ix]
        # Only a source-interface bookkeeping field: no twin endpoint is evaluated here.
        k['swap'] = np.roll(np.arange(len(ix)),1)
    return kids


def run_unit(unit, probe=False):
    from auditory_alignment import data
    started = time.time(); kids = data.load_private()
    if probe: kids = smoke_kids(kids)
    dest = STORE/('probes/'+os.environ['SLURM_JOB_ID'] if probe else 'production')/unit['id']
    output = {'status':'running', 'unit':unit, 'id':unit['id'], 'probe':probe, 'plan_sha256':B.sha(PLAN), 'stages':{}}
    for stage in ('inner','outer'):
        enc, protos, rec, bt, fd = inner_source(unit,kids,dest,probe) if stage=='inner' else original_source(unit,kids)
        initial = E.cpu_state(enc); values = {'source':evaluate(enc,bt,protos,rec,fd,probe)}; ledgers = {}
        for regime in REGIMES:
            ledgers[regime] = continue_source(enc,bt,protos,rec,initial,regime,dest/stage,probe)
            state = torch.load(dest/stage/f'{regime}.pt',map_location=bt.dev,weights_only=False)
            enc.load_state_dict(state['model']); values[regime] = evaluate(enc,bt,protos,rec,fd,probe)
            del state
        output['stages'][stage] = {'values':values, 'training':ledgers,
                                  'checkpoints':{r:B.sha(dest/stage/f'{r}.pt') for r in REGIMES},
                                  'source_train_ids':[kids[i]['id'] for i in fd.tr], 'evaluation_ids':[kids[i]['id'] for i in fd.te]}
        del enc,protos,bt,fd,initial;gc.collect();torch.cuda.empty_cache()
    output.update(status='complete', choices=choose(output['stages']['inner']['values'],output['stages']['outer']['values']),
                  job=os.environ['SLURM_JOB_ID'], device=torch.cuda.get_device_name(0), seconds=time.time()-started,
                  gpu_peak_mb=torch.cuda.max_memory_allocated()/2**20, source_sha256=B.sha(__file__))
    target = BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe else BASE/'units'
    B.write(target/f'{unit["id"]}.json',output);print(unit['id'],'complete',round(time.time()-started,1),'probe',probe,flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--repair-check',action='store_true')
    ap.add_argument('--unit');ap.add_argument('--smoke-job');ap.add_argument('--max-units',type=int,default=2)
    a=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if a.make_plan:make_plan();return
    plan=read(PLAN);verify(plan)
    if a.repair_check:
        parent=read(Path(core.OUT)/'aln34/private_episode_v1/plan.json')
        failed=next(u for u in parent['rows'] if u['id']=='ALN34PE_6588a1cb55507bc6')
        unit=next(u for u in plan['rows'] if u['source']==failed['source'])
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'unit':unit['id'],'kind':'full_previous_failure_replay'}
        try:
            run_unit(unit)
            rec=read(BASE/'units'/f"{unit['id']}.json")
            assert rec['status']=='complete' and not rec['probe']
            hits=[]
            for stage,body in rec['stages'].items():
                for regime,values in body['values'].items():
                    for fraction,candidates in values['candidates'].items():
                        for steps,candidate in candidates.items():
                            for child,v in candidate['per_participant'].items():
                                if v.get('status')=='complete' and v['n_support_trials']==1 and int(steps)>0:
                                    assert v['effective_adapter_steps']==0 and v['insufficient_support_identity_fallback']
                                    assert v['n_query_trials']>0
                                    hits.append({'stage':stage,'regime':regime,'fraction':fraction,'steps':steps,'child':child})
            assert hits,'the production failure case was not exercised'
            receipt.update(status='pass',singleton_cases=hits,record_sha256=B.sha(BASE/'units'/f"{unit['id']}.json"))
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    if a.unit:run_unit(next(u for u in plan['rows'] if u['id']==a.unit));return
    if a.smoke:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            for arch,obj in (('lag_local_tokens','NCE'),('lag_local_tokens','CS_SINGLE'),('cbramod','NCE'),('reve','NCE')):
                unit=next(u for u in plan['rows'] if u['source']['spec']['architecture']==arch and u['source']['spec']['objective']==obj)
                run_unit(unit,True);receipt['units'].append(unit['id'])
            receipt['status']='pass'
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    receipt=read(BASE/'probes'/str(a.smoke_job)/'receipt.json')
    assert receipt['status']=='pass' and receipt['plan_sha256']==B.sha(PLAN)
    if list((BASE/'units').glob('*.FAILED.json')):raise RuntimeError('unresolved private episode failure')
    done=0
    for u in plan['rows']:
        output=BASE/'units'/f'{u["id"]}.json'
        if output.exists():assert read(output)['status']=='complete';continue
        lock=BASE/'claims'/f'{u["id"]}.lock';lock.parent.mkdir(parents=True,exist_ok=True)
        with lock.open('a+') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if output.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m','auditory_alignment_v3.aln34.private_episode_v2','--unit',u['id']]).returncode
            if rc or not output.exists() or read(output).get('probe'):
                B.write(BASE/'units'/f'{u["id"]}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc})
                raise RuntimeError('private episode unit failed')
            done+=1
        if done>=a.max_units:break


if __name__=='__main__':main()
