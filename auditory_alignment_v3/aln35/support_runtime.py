"""Frozen-source interfaces shared by the two bounded ALN3.5 support lanes."""
from __future__ import annotations

import copy
import gc
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import torch
from scipy.special import expit, logit, softmax
from torch.nn import functional as F

from .. import core
from ..aln34 import adaptation_policy as D, data_inner as I, learning_budget as B
from ..aln34 import episode_training as E, private_episode_v2 as PE, private_current_time as C
from ..aln34.calibration_retry import AffineLogitCalibrator
from ..sci_r1 import private_task as P
from . import support_contract as K

ROOT = Path(core.OUT)/'aln35'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln35')


def read(path): return json.loads(Path(path).read_text())


def selected_sources():
    ip, pp = read(I.PLAN), read(PE.PLAN)
    I.verify(ip); PE.verify(pp); I.register()
    out = []
    for inner in ip['rows']:
        s = inner['spec']
        if (s['axis'] != 'inner_person' or inner['seed'] != 3401 or s['objective'] != 'NCE'
                or s['architecture'] not in ('lag_local_tokens', 'cbramod')
                or s['architecture'] == 'cbramod' and s['adaptation'] != 'pretrained_full'): continue
        outer = ip['baselines'][s['baseline_id']]
        out.append({'dataset': 'dtu', 'architecture': s['architecture'], 'outer': outer,
                    'inner': inner, 'inner_plan_sha256': B.sha(I.PLAN),
                    'inner_split': ip['splits'][s['split_key']],
                    'source_execution_id': outer['row']['experiment_id']})
    assert len(out) == 20
    for u in pp['rows']:
        row, s = u['source'], u['source']['spec']
        if row['seed'] != 3401 or s['objective'] != 'NCE': continue
        if s['architecture'] not in ('lag_local_tokens', 'cbramod'): continue
        if s['architecture'] == 'cbramod' and s['adaptation'] != 'pretrained_full': continue
        out.append({'dataset': 'private_bdf', 'architecture': s['architecture'], 'private_parent': u,
                    'outer': {'row': row, 'record_sha256': u['record_sha256'], 'checkpoint_sha256': u['checkpoint_sha256']},
                    'inner_plan_sha256': B.sha(PE.PLAN), 'source_execution_id': row['experiment_id']})
    assert len(out) == 30 and len({r['source_execution_id'] for r in out}) == 30
    return sorted(out, key=lambda x: (x['dataset'], x['architecture'], x['source_execution_id']))


def source_files(own, note):
    files = {Path(__file__), Path(K.__file__), Path(own), Path(note),
             Path(core.REPO)/'auditory_alignment_v3/aln34/calibration_retry.py',
             Path(core.REPO)/'auditory_alignment_v3/aln3_reference/calibration.py',
             Path(core.REPO)/'auditory_alignment/evaluate.py',
             Path(core.REPO)/'auditory_c3/private_mi2.py',
             Path(core.REPO)/'auditory_alignment/data.py'}
    sources = {**D.sources(), **PE.sources()}
    for f in files: sources[str(f.relative_to(core.REPO))] = B.sha(f)
    return dict(sorted(sources.items()))


def load_kids():
    from auditory_alignment import data
    from auditory_c3.private_mi2 import hist_codes
    kids = data.load_private()
    for k in kids:
        path = Path(core.REPO)/'private/auditory_gx/GX_stage_001/epochs'/f'{k["rid"]}.npz'
        with np.load(path, allow_pickle=False) as z:
            accepted = z['accepted'].astype(bool)
            h = hist_codes(z['previous_code'][accepted], z['previous_run_length'][accepted])['since_last_deviant']
            valid = h >= 0
            assert np.array_equal(z['y'][accepted][valid], k['y'])
            assert np.array_equal(z['block_id'][accepted][valid], k['block'])
            assert np.array_equal(h[valid], k['bin'])
            k['_s35_onset_seconds'] = z['onset_seconds'][accepted][valid].copy()
            assert float(z['rate_hz']) == 250 and int(z['pre_samples']) == 50 and int(z['post_samples']) == 150
            # Bind only required event geometry, not a raw-data copy or identity map.
            k['_s35_geometry_sha256'] = K.digest({'onset': k['_s35_onset_seconds'].tolist(),
                   'blocks': k['block'].tolist(), 'y': k['y'].tolist(), 'history': k['bin'].tolist()})
    return kids


def split_public(bundle, person, role):
    items = bundle.items(person, role)
    split = K.dtu_split(items, bundle.bt.fs, bundle.bt.seg_len, bundle.grid, bundle.bt.post,
                        fit_only=role == 'fit')
    return items, split


def serial_split(split, identity):
    out = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in split.items()}
    out.update(query_hash=K.digest([K.stable_key(identity, j) for j in split['query']]),
               pool_hash=K.digest([K.stable_key(identity, j) for j in split['pool']]),
               n_query=len(split['query']), n_pool=len(split['pool']))
    return out


def bindings(sources):
    """CPU intake: freeze sample geometry before any new outer result exists."""
    from auditory_alignment_v2.run import load_cohort
    kids = load_kids(); private = {}
    for k in kids:
        s = K.private_split(k)
        private[k['id']] = {**serial_split(s, k['id']), 'geometry_sha256': k['_s35_geometry_sha256'],
                            'group': k['group'], 'fold': k['fold']}
    public = {}
    for cf in (0, 1):
        source = next(s for s in sources if s['dataset'] == 'dtu' and s['outer']['row']['content_fold'] == cf)
        coh = load_cohort(core.bind(source['outer']['row']))
        grid = core.grid_samples(coh.fs)
        for person, p in enumerate(coh.participants):
            for role in ('fit', 'es', 'test'):
                items = sorted([s for s in coh.segments if s['p'] == person and s['kind'] == 'ss' and s['role'] == role], key=lambda s: s['e0'])
                sp = K.dtu_split(items, coh.fs, coh.meta['seg_len'], grid, round(.6*coh.fs), role == 'fit')
                key = f'{cf}/{role}/{p["id"]}'
                public[key] = {**serial_split(sp, p['id']), 'geometry_sha256': K.digest([
                    {k:s[k] for k in ('e0', 's0', 'uid', 'part', 'code', 'role')} for s in items]),
                    'group': p['group'], 'fold': p['fold']}
        del coh
    return {'private': private, 'dtu': public,
            'restricted': 'sample indexes and event geometry are server-only support binding metadata, not publication payload'}


def check_binding(binding, split, identity, dataset, cf=None, role=None):
    key = identity if dataset == 'private_bdf' else f'{cf}/{role}/{identity}'
    ref = binding['private' if dataset == 'private_bdf' else 'dtu'][key]
    actual = serial_split(split, identity)
    assert all(actual[k] == ref[k] for k in actual), f'support/query geometry changed: {key}'
    return ref


def ready(source, inner=False):
    outer = source['outer']; row = outer['row']
    if not (Path(core.OUT)/'ckpt'/f'{row["experiment_id"]}_best.pt').is_file(): return False
    if not inner: return True
    if source['dataset'] == 'dtu': return D.ready({'inner_source': source['inner']})
    directory = PE.STORE/'production'/source['private_parent']['id']/'inner_source'
    return (directory/'record.json').is_file() and (directory/'model_best.pt').is_file()


def public_bundle(source, stage):
    I.register()
    ip = read(I.PLAN); I.verify(ip)
    row = source['inner'] if stage == 'inner' else source['outer']['row']
    bundle, provenance = D.rebuild(row, I.BASE if stage == 'inner' else core.OUT, ip if stage == 'inner' else None)
    if stage == 'outer':
        assert all(provenance[k] == source['outer'][k] for k in ('record_sha256', 'checkpoint_sha256'))
    ids = source['inner_split']['inner_ids'] if stage == 'inner' else source['inner_split']['outer_ids']
    people = [i for i, p in enumerate(bundle.coh.participants) if p['id'] in ids]
    train_ids = [bundle.coh.participants[i]['id'] for i in sorted(bundle.bt.train_p)]
    assert not set(ids) & set(train_ids)
    provenance.update(fit_ids=train_ids, calibration_ids=train_ids, evaluation_ids=ids,
        selection_level='whole encoder/source readout excludes inner identities; inner queries use original source-ES content',
        target_statistics_access='inner training audio only' if stage == 'inner' else 'outer training audio only')
    return bundle, people, 'es' if stage == 'inner' else 'test', provenance


def private_bundle(source, stage, kids=None):
    kids = load_kids() if kids is None else kids
    parent = source['private_parent']
    if stage == 'inner':
        directory = PE.STORE/'production'/parent['id']
        assert ready(source, True), 'private v2 independent inner checkpoint missing'
        enc, protos, rec, bt, fd = PE.inner_source(parent, kids, directory, False)
        path = directory/'inner_source/model_best.pt'
        provenance = {'checkpoint_sha256': B.sha(path), 'record_sha256': B.sha(directory/'inner_source/record.json'),
                      'parent_unit': parent['id'], 'parent_plan_sha256': B.sha(PE.PLAN)}
    else:
        enc, protos, rec, bt, fd = PE.original_source(parent, kids)
        provenance = {k: source['outer'][k] for k in ('record_sha256', 'checkpoint_sha256')}
    assert not set(fd.tr) & set(fd.te)
    provenance.update(fit_ids=[kids[i]['id'] for i in fd.tr], calibration_ids=[kids[i]['id'] for i in fd.tr],
                      evaluation_ids=[kids[i]['id'] for i in fd.te],
                      selection_level='whole encoder source excludes inner identities' if stage == 'inner' else 'outer held-out children',
                      preprocessing_access='inherited within-record normalisation across fit/ES/support/query; no cross-person statistics')
    return PrivateBundle(source['outer']['row'], enc, protos, rec, bt, fd), provenance


class PrivateProbe:
    """Same source-ES logistic interface, with the already validated numeric retry."""
    def __init__(self, x, y):
        from sklearn.linear_model import LogisticRegression
        self.mu, self.sd = x.mean(0), x.std(0)+1e-8
        self.lr = LogisticRegression(C=1., max_iter=2000).fit((x-self.mu)/self.sd, y)
        self.cal = AffineLogitCalibrator.fit(self.score(x), y)

    def score(self, x): return self.lr.decision_function((x-self.mu)/self.sd)


class PrivateBundle:
    def __init__(self, row, enc, protos, rec, bt, fd):
        self.row, self.model, self.protos, self.record, self.bt, self.fd = row, enc, protos, rec, bt, fd
        self.model.requires_grad_(False).eval()
        self.objective = PE.objective(rec)
        self.refresh_readouts()

    def representations(self, child, idx=None, model=None):
        return PE.representations(self.model if model is None else model, self.bt, child, idx)

    def refresh_readouts(self):
        u = {i: self.representations(i) for i in self.fd.tr}
        x = self.fd.es_rows(u)
        self.probe = PrivateProbe(x, self.fd.y_es)
        self.native = P.Native(self.record, self.protos, self.fd, u)
        native_scores = np.concatenate([self.native(u[i][self.fd.es[i]]) for i in self.fd.tr])
        self.native_cal = AffineLogitCalibrator.fit(native_scores, self.fd.y_es)
        self.readout_receipt = {'linear': self.probe.cal.to_dict(), 'native': self.native_cal.to_dict(),
                 'fit': 'source ES only', 'n_rows': len(x), 'source_ids': [self.fd.kids[i]['id'] for i in self.fd.tr]}
        self.source_u = u

    def logits(self, u, mode):
        scores = self.probe.score(u) if mode == 'linear' else self.native(u)
        calibration = self.probe.cal if mode == 'linear' else self.native_cal
        return logit(np.clip(calibration.predict(scores), 1e-12, 1-1e-12))


def adapter_parameters(adapter):
    return [p for name, p in adapter.named_parameters() if not name.startswith('base.')]


def fit_public(bundle, support, steps, seed):
    """Sparse anchor optimisation after the stricter full-query geometry guard."""
    from auditory_alignment.train import Objective
    torch.manual_seed(seed)
    model = D.Adapter(bundle.model, 'lowrank_spatial', bundle.coh.n_ch).to(bundle.bt.dev).eval()
    pars = adapter_parameters(model); anchors = E.anchors(bundle, support)
    ledger = {'requested_adapter_steps': steps, 'effective_adapter_steps': 0,
              'identity_fallback_reason': 'zero_step_candidate' if steps == 0 else 'insufficient_distinct_anchors' if len(anchors) < 2 else None,
              'anchor_count': len(anchors), 'gradient_norms': [], 'sample_exposures': 0,
              'parameterisation': 'input lowrank_spatial rank4 A~N(0,.01), B=0; Adam1e-3'}
    if ledger['identity_fallback_reason']: return model, ledger
    obj = Objective({'objective':'NCE', 'config':{'temperature':.1}},
                    torch.zeros(4,32,device=bundle.bt.dev), torch.zeros(4,32,device=bundle.bt.dev))
    optimizer = torch.optim.Adam(pars, lr=1e-3); rng = np.random.default_rng(seed)
    for _ in range(steps):
        selected = [anchors[i] for i in rng.choice(len(anchors), size=min(256,len(anchors)), replace=False)]
        x, v, keys = E.tensor_batch(bundle, selected)
        loss, _ = obj(model(x), v, keys=keys)
        if not torch.isfinite(loss): raise FloatingPointError('nonfinite support objective')
        optimizer.zero_grad(); loss.backward(); norm = torch.nn.utils.clip_grad_norm_(pars, 5.)
        if not torch.isfinite(norm): raise FloatingPointError('nonfinite support gradient')
        optimizer.step(); ledger['gradient_norms'].append(float(norm)); ledger['effective_adapter_steps'] += 1
        ledger['sample_exposures'] += len(selected)
    ledger['BA_norm'] = float((model.B@model.A).detach().norm())
    return model.eval(), ledger


def fit_private_spatial(bundle, child, support, steps, seed):
    torch.manual_seed(seed)
    model = D.Adapter(bundle.model, 'lowrank_spatial', 20).to(bundle.bt.dev).eval()
    pars = adapter_parameters(model); kid = bundle.fd.kids[child]
    ledger = K.support_signal(bundle.objective.name, kid['y'][support], steps)
    ledger.update(gradient_norms=[], sample_exposures=0, actual_updates=0,
                  parameterisation='input lowrank_spatial rank4 A~N(0,.01), B=0; Adam1e-3')
    optimizer = torch.optim.Adam(pars, lr=1e-3); rng = np.random.default_rng(seed)
    for _ in range(ledger['effective_adapter_steps']):
        chosen = rng.choice(support, size=min(128,len(support)), replace=False)
        x = bundle.bt.patches(child, torch.tensor(chosen, device=bundle.bt.dev))
        y = torch.tensor(kid['y'][chosen], device=bundle.bt.dev)
        loss, _ = bundle.objective(model(x), labels=y, prototypes=bundle.protos)
        if not torch.isfinite(loss): raise FloatingPointError('nonfinite private adapter loss')
        optimizer.zero_grad(); loss.backward(); norm = torch.nn.utils.clip_grad_norm_(pars, 5.)
        if not torch.isfinite(norm): raise FloatingPointError('nonfinite private adapter gradient')
        before = [p.detach().clone() for p in pars]; optimizer.step()
        ledger['actual_updates'] += int(any(not torch.equal(p, old) for p, old in zip(pars, before)))
        ledger['gradient_norms'].append(float(norm)); ledger['sample_exposures'] += len(chosen)
    ledger['BA_norm'] = float((model.B@model.A).detach().norm())
    return model.eval(), ledger


def fit_private_output(bundle, u, labels, support, steps, seed):
    torch.manual_seed(seed)
    adapter = C.OutputResidual(u.shape[1]).to(bundle.bt.dev)
    ledger = K.support_signal('NCE', labels[support], steps)
    ledger.update(gradient_norms=[], sample_exposures=0, actual_updates=0,
                  parameterisation='native-science output rank4; fixed source linear-probe BCE; Adam1e-3')
    optimizer = torch.optim.Adam(adapter.parameters(), lr=1e-3)
    x = torch.tensor(u[support], dtype=torch.float32, device=bundle.bt.dev)
    y = torch.tensor(labels[support], dtype=torch.float32, device=bundle.bt.dev)
    probe = bundle.probe
    w = torch.tensor(probe.lr.coef_[0]/probe.sd, device=bundle.bt.dev, dtype=torch.float32)
    bias = float(probe.lr.intercept_[0]-probe.mu@(probe.lr.coef_[0]/probe.sd))
    rng = np.random.default_rng(seed)
    for _ in range(ledger['effective_adapter_steps']):
        ix = rng.choice(len(x), size=min(256,len(x)), replace=False)
        loss = F.binary_cross_entropy_with_logits(adapter(x[ix])@w+bias, y[ix])
        if not torch.isfinite(loss): raise FloatingPointError('nonfinite output-rank4 loss')
        optimizer.zero_grad(); loss.backward()
        norm = torch.sqrt(sum(p.grad.square().sum() for p in adapter.parameters()))
        if not torch.isfinite(norm): raise FloatingPointError('nonfinite output-rank4 gradient')
        optimizer.step(); ledger['gradient_norms'].append(float(norm)); ledger['sample_exposures'] += len(ix)
        ledger['actual_updates'] += 1
    ledger['BA_norm'] = float((adapter.B@adapter.A).detach().norm())
    return adapter.eval(), ledger


def private_metrics(bundle, u, kid, query, mode, base_u=None, temperature=1.):
    logits = bundle.logits(u, mode); p = expit(logits/temperature)
    oldp = expit(bundle.logits(u if base_u is None else base_u, mode))
    result = C.clean_metrics(logits/temperature, p, kid['y'][query], bundle.fd.base)
    if len(query) > 1:
        wrong = C.clean_metrics(np.roll(logits,1)/temperature, np.roll(p,1), kid['y'][query], bundle.fd.base)
        result.update(wrong_nll_bits=wrong['nll_bits'], mismatch_gain_bits=wrong['nll_bits']-result['nll_bits'])
    else: result.update(wrong_nll_bits=None, mismatch_gain_bits=None)
    result.update(K.probability_change(p,oldp), n_query=len(query), temperature=float(temperature))
    result['representation_relative_change'] = float(np.linalg.norm(u-base_u)/(np.linalg.norm(base_u)+1e-12)) if base_u is not None else 0.
    return result


def public_metrics(bundle, u, query, pool, mode, base_u=None, temperature=1.):
    from auditory_alignment import evaluate as ev
    uid, v, a = pool; own = np.asarray([uid[s['uid']] for s in query])
    scores = bundle.readout.scores(u,v,a,mode); tau = bundle.readout.tau[mode]*temperature
    val = ev._metrics(scores,own,tau)
    old = scores if base_u is None else bundle.readout.scores(base_u,v,a,mode)
    result = {'true_nll_bits': val['logloss_bits'], 'nll_bits':val['logloss_bits'],
              'rank_pct':val['rank_pct'],'top1':val['top1'],'n_query':len(query),
              'n_candidates':len(uid), 'candidate_hash':K.digest(list(uid)), 'temperature':temperature,
              **K.probability_change(softmax(scores/tau,axis=1),softmax(old/bundle.readout.tau[mode],axis=1))}
    if len(query) > 1:
        wrong = ev._metrics(np.roll(scores,1,axis=0), own, tau)
        result.update(wrong_nll_bits=wrong['logloss_bits'], mismatch_gain_bits=wrong['logloss_bits']-val['logloss_bits'])
    else: result.update(wrong_nll_bits=None,mismatch_gain_bits=None)
    result['representation_relative_change'] = float(np.linalg.norm(u-base_u)/(np.linalg.norm(base_u)+1e-12)) if base_u is not None else 0.
    return result


def public_temperature(bundle, support, mode):
    if len(support) < 2: return 1., {'reason':'no_legal_support_risk','risks':{},'n_candidates':len(support)}
    unique = {s['uid']:s for s in support}; rows = list(unique.values()); index = {s['uid']:i for i,s in enumerate(rows)}
    if len(rows) < 2: return 1., {'reason':'no_legal_support_risk','risks':{},'n_candidates':len(rows)}
    v,a = bundle.reps.va([s['s0'] for s in rows]); u = bundle.reps.u([s['e0'] for s in support])
    scores = bundle.readout.scores(u,v,a,mode)
    t,receipt = K.temperature_retrieval(scores,np.asarray([index[s['uid']] for s in support]),bundle.readout.tau[mode])
    receipt.update(candidate_role='selected personal support only', candidate_hash=K.digest(list(unique)), n_candidates=len(rows))
    return t,receipt


def cleanup():
    gc.collect(); torch.cuda.empty_cache()
