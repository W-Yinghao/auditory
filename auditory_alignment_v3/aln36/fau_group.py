"""ALN3.6 R1 panel A: FAU sources trained with a whole hearing group withheld (12 unique fits per seed).

For each held-out group g in {ci, ha, th}, content fold and tool (local L1, CBpre true-full), one source is trained on
every human FAU identity whose group != g (TH dev people are sources unless g == th) using only their role=fit,
kind=ss segments for gradients and their role=es, kind=ss segments for checkpoint selection. The five original
person folds of the target group share this source (60 evaluation cells, not 60 trainings).

EEG input scaling: the stageB eeg_1_20_ica signal (inherited offline 1-20 Hz filter and ICA) without the per-person
`data._stdz`; one channel mean/sd fitted on the legal source-fit segment samples and frozen for source ES, target
support and target query. Checkpoints: train_true_nll (source-ES true-query native NLL).
Package: AUDITORY_ALN3_SERVER_PACKAGE_v3_6_20261020 docs/02 §A, docs/04 §4.2-4.4.
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import fcntl
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from . import common as C

BASE = C.OUT / 'fau_group_v1'
PLAN = BASE / 'plan.json'
BINDINGS = BASE / 'bindings'
STORE = C.STORE / 'fau_group_v1'
FAMILY = 'ALN36_FAU_GROUP'
PARENTS = {('local_L1', 0): 'ALN3X_84b5c4fd866b3b7a', ('local_L1', 1): 'ALN3X_f296f7a7e2f2176c',
           ('CBpre_true_full', 0): 'ALN3X_124a413438c432c7', ('CBpre_true_full', 1): 'ALN3X_fa1f6f11e410c0b3'}
EPOCHS = {'local_L1': 200, 'CBpre_true_full': 100}
EXPECTED_TARGETS = {'ci': 24, 'ha': 29, 'th': 14}
RISK_ANCHORS = 16
CAL_QUERIES = 600
SMOKE_EPOCHS = 2
NAME = {'local_L1': 'c3_s35a36loc', 'CBpre_true_full': 'c3_s35a36cb'}
SBATCH = {'local_L1': 'slurm/aln35_aln36_group_local.sbatch', 'CBpre_true_full': 'slurm/aln35_aln36_group_cb.sbatch'}


def sources():
    files = [Path(__file__), Path(C.__file__), C.REPO / 'auditory_alignment_v3/aln36/train_true_nll.py',
             C.REPO / 'auditory_alignment_v3/local_support.py', C.REPO / 'auditory_alignment_v3/local_train.py',
             C.REPO / 'auditory_alignment_v3/fm_aligned.py', C.REPO / 'auditory_alignment_v3/fm_aligned32.py',
             C.REPO / 'auditory_alignment_v3/fm_dense.py', C.REPO / 'auditory_alignment_v3/core.py']
    files += [C.REPO / d / f for d, f in core.V2_DEPS]
    return {str(p.relative_to(C.REPO)): C.sha(p) for p in sorted(set(files))}


@contextlib.contextmanager
def raw_scale():
    """Process-local: the loader keeps stageB amplitudes (float32) instead of per-person z-scoring; restored on exit."""
    from auditory_alignment import data
    original = data._stdz
    data._stdz = lambda arrs, guard: [np.asarray(a, dtype=np.float32) for a in arrs]
    try:
        yield
    finally:
        data._stdz = original


def load_raw(cf):
    from auditory_alignment import data
    with raw_scale():
        coh = data.load_fau(cf, kinds=('ss',))
    assert all(s['kind'] == 'ss' for s in coh.segments)
    return coh


def segment_keys(coh):
    """Stable physical keys (person id, uid, occurrence) in loader order (trial_NN order, then segment start)."""
    seen, keys = {}, []
    for s in coh.segments:
        pid = coh.participants[s['p']]['id']
        k = (pid, s['uid'])
        n = seen.get(k, 0); seen[k] = n + 1
        keys.append(f'{pid}|{s["uid"]}|{n}')
    return keys


def group_sets(coh, g):
    parts = coh.participants
    source = sorted(i for i, p in enumerate(parts) if p['group'] != g and not p.get('test_only'))
    target = sorted(i for i, p in enumerate(parts) if p['group'] == g and not p['dev'])
    excluded = sorted(i for i, p in enumerate(parts) if p['group'] == g)
    assert not set(source) & set(excluded) and set(target) <= set(excluded)
    assert all(parts[i]['group'] != g for i in source)
    th_dev = [i for i, p in enumerate(parts) if p['dev']]
    assert (set(th_dev) <= set(source)) == (g != 'th') and (not set(th_dev) & set(source)) == (g == 'th')
    assert len(target) == EXPECTED_TARGETS[g], (g, len(target))
    src = set(source)
    fit = [i for i, s in enumerate(coh.segments) if s['p'] in src and s['role'] == 'fit' and s['kind'] == 'ss']
    es = [i for i, s in enumerate(coh.segments) if s['p'] in src and s['role'] == 'es' and s['kind'] == 'ss']
    return {'source': source, 'target': target, 'excluded': excluded, 'fit': fit, 'es': es}


def scaler_from(coh, fit):
    L = coh.meta['seg_len']
    s1 = np.zeros(coh.eeg.shape[0]); s2 = np.zeros(coh.eeg.shape[0]); n = 0
    for i in fit:
        x = coh.eeg[:, coh.segments[i]['e0']:coh.segments[i]['e0'] + L].astype(np.float64)
        s1 += x.sum(1); s2 += (x * x).sum(1); n += x.shape[1]
    mu = s1 / n; sd = np.sqrt(np.maximum(s2 / n - mu * mu, 0)); sd[sd == 0] = 1
    return mu, sd, n


def apply_scaler(coh, mu, sd):
    coh.eeg -= mu.astype(np.float32)[:, None]
    coh.eeg /= sd.astype(np.float32)[:, None]


def risk_keys(coh, keys, sets, seed):
    """Frozen query/candidate identities for the source-side checkpoint risk (no EEG values involved)."""
    segs = coh.segments

    def pool(units):
        rep = {}
        for i in units:
            rep.setdefault(segs[i]['uid'], i)
        return [keys[rep[u]] for u in sorted(rep)]
    cal = sorted(np.random.default_rng(seed + 36006).choice(sets['fit'], size=min(CAL_QUERIES, len(sets['fit'])), replace=False).tolist())
    grid = core.grid_samples(coh.fs)
    anchors = (grid * np.round(np.linspace(0, (coh.meta['seg_len'] - 1) // grid, RISK_ANCHORS))).astype(int).tolist()
    return {'anchors': anchors, 'cal_queries': [keys[i] for i in cal], 'cal_candidates': pool(sets['fit']),
            'es_queries': [keys[i] for i in sets['es']], 'es_candidates': pool(sets['es']),
            'cal_rule': f'{CAL_QUERIES} source-fit segments drawn with default_rng(seed+36006), candidates = all source-fit uids',
            'es_rule': 'all source-ES segments, candidates = deduplicated source-ES uids (sorted)'}


def binding_path(g, cf):
    return BINDINGS / f'{g}_cf{cf}.json'


def bind():
    """Write the six immutable (group, content fold) source bindings; CPU, run once before the plan."""
    from auditory_alignment import data
    from auditory_alignment_v2.foundation_adapter import CBRAMOD_W, CHANNELS
    import h5py
    BINDINGS.mkdir(parents=True, exist_ok=True, mode=0o700)
    pkg = C.package_binding()
    channels = set()
    for g in ('th', 'ha', 'ci'):
        for p in sorted(Path(data.STAGEB, g).glob('*.h5')):
            with h5py.File(p, 'r') as f:
                channels.add(tuple(str(c) for c in f.attrs['channels']))
    assert len(channels) == 1
    channels = list(next(iter(channels)))
    init = {'path': CBRAMOD_W, 'sha256': C.sha(CBRAMOD_W),
            'stageB_channel_order_equals_backbone_contract': channels == CHANNELS['fau']}
    for cf in C.CONTENT_FOLDS:
        coh = load_raw(cf); keys = segment_keys(coh)
        assert len(set(keys)) == len(keys)
        s0_of = {}
        for s in coh.segments:
            assert s0_of.setdefault(s['uid'], s['s0']) == s['s0'], 'one uid must map to one audio position'
        fit_uids = {}
        for g in C.GROUPS:
            sets = group_sets(coh, g)
            fit_uids[g] = sorted({coh.segments[i]['uid'] for i in sets['fit']})
            mu, sd, n = scaler_from(coh, sets['fit'])
            parts = coh.participants
            body = {'version': 'ALN36_FAU_GROUP_BINDING_v1', 'excluded_group': g, 'content_fold': cf, 'seed': C.SEED,
                    'stage_dir': data.STAGEB, 'loader': 'auditory_alignment.data.load_fau(kinds=("ss",)) with _stdz replaced by identity (aln36.fau_group.raw_scale)',
                    'channels': channels, 'fs': coh.fs, 'seg_len': coh.meta['seg_len'],
                    'source_ids': [parts[i]['id'] for i in sets['source']],
                    'source_groups': sorted({parts[i]['group'] for i in sets['source']}),
                    'source_th_dev_ids': [parts[i]['id'] for i in sets['source'] if parts[i]['dev']],
                    'target_ids': [parts[i]['id'] for i in sets['target']],
                    'target_person_fold': {parts[i]['id']: parts[i]['fold'] for i in sets['target']},
                    'excluded_ids': [parts[i]['id'] for i in sets['excluded']],
                    'excluded_dev_ids': [parts[i]['id'] for i in sets['excluded'] if parts[i]['dev']],
                    'source_fit_keys': [keys[i] for i in sets['fit']], 'source_es_keys': [keys[i] for i in sets['es']],
                    'scaler': {'mean': mu.tolist(), 'sd': sd.tolist(), 'n_samples_per_channel': int(n),
                               'rule': 'per-channel mean/sd over every sample of the source role=fit kind=ss 5 s segments'},
                    'risk': risk_keys(coh, keys, sets, C.SEED), 'cbramod_init': init, 'package': {'zip_sha256': pkg['zip_sha256']}}
            body['source_fit_sha256'] = C.digest(body['source_fit_keys'], 64)
            body['source_es_sha256'] = C.digest(body['source_es_keys'], 64)
            body['scaler_sha256'] = C.digest(body['scaler'], 64)
            path = binding_path(g, cf)
            if path.exists():
                old = C.read(path); assert all(old[k] == v for k, v in body.items()), f'immutable binding drift {path.name}'
            else:
                C.write(path, {**body, 'created': datetime.now().astimezone().isoformat(), 'job': os.environ.get('SLURM_JOB_ID')})
                path.chmod(0o444)
            print('binding', path.name, len(body['source_ids']), 'source people', len(body['target_ids']), 'targets',
                  len(body['source_fit_keys']), 'fit', len(body['source_es_keys']), 'es', flush=True)
        assert fit_uids['ci'] == fit_uids['ha'] == fit_uids['th'], 'source-fit audio content differs across held-out groups'
        del coh


def parent(tool, cf):
    eid = PARENTS[(tool, cf)]
    path = Path(core.OUT) / 'units' / f'{eid}.json'
    rec = C.read(path)
    assert rec['status'] == 'complete' and rec['row']['content_fold'] == cf and rec['row']['seed'] == C.SEED
    return rec, path


def recipe(tool, rec):
    s = rec['row']['spec']
    if tool == 'local_L1':
        assert s['variant'] == 'local_aligned1000' and s['architecture'] == 'lag_local_tokens' and rec['resolved_config']['epochs'] == 200
        return {'variant': 'local_aligned1000', 'epochs': 200, 'optimizer': 'AdamW', 'lr': 1e-3, 'weight_decay': 1e-4,
                'schedule': 'cosine T_max=epochs*steps_per_epoch', 'validation': 'every 5th epoch and the last', 'd': 32}
    assert s['recipe'] == 'full_onestep_v1' and s['adaptation'] == 'pretrained_full' and float(s['lr_backbone']) == 3e-4
    assert rec['resolved_config']['epochs'] == 100 and float(s['lr_head']) == 1e-3
    return {'recipe': 'full_onestep_v1', 'epochs': 100, 'lr_backbone': 3e-4, 'lr_head': 1e-3, 'llrd': 1.0, 'optimizer': 'AdamW',
            'weight_decay': 1e-4, 'schedule': 'cosine T_max=epochs*steps_per_epoch', 'validation': 'every epoch', 'd': 32,
            'readout': 'aligned_patch_linear', 'init': 'generic CBraMod pretrained_weights.pth (no project donor)'}


def make_plan():
    from . import train_true_nll as TT
    rows = []
    for tool in C.TOOLS:
        for g in C.GROUPS:
            for cf in C.CONTENT_FOLDS:
                b = C.read(binding_path(g, cf)); prec, ppath = parent(tool, cf)
                spec = core.bind(prec['row'])['spec']
                signature = {'seed': C.SEED, 'tool': tool, 'recipe': recipe(tool, prec), 'bound_spec': spec,
                             'excluded_group': g, 'content_fold': cf, 'source_ids': b['source_ids'],
                             'source_fit_sha256': b['source_fit_sha256'], 'source_es_sha256': b['source_es_sha256'],
                             'scaler_sha256': b['scaler_sha256'], 'loader': b['loader'],
                             'init': b['cbramod_init'] if tool == 'CBpre_true_full' else {'kind': 'fresh', 'torch_manual_seed': C.SEED},
                             'target_coordinate': 'dense20ms_v1 Local 8-frame target, fixed_features head, stats from source fit',
                             'checkpoint_rule': TT.SELECTION_RULE, 'risk_sha256': C.digest(b['risk'], 64), 'sources': sources()}
                eid = 'ALN36G_' + C.digest(signature)
                cells = [{'person_fold': pf, 'target_ids': sorted(i for i, f in b['target_person_fold'].items() if f == pf)}
                         for pf in C.PERSON_FOLDS]
                assert sorted(sum((c['target_ids'] for c in cells), [])) == sorted(b['target_ids'])
                rows.append({'experiment_id': eid, 'family_id': FAMILY, 'tool': tool, 'excluded_group': g, 'content_fold': cf,
                             'seed': C.SEED, 'parent_id': prec['experiment_id'], 'parent_record_sha256': C.sha(ppath),
                             'binding': binding_path(g, cf).name, 'binding_sha256': C.sha(binding_path(g, cf)),
                             'training_signature': signature, 'evaluation_cells': cells})
    assert len(rows) == 12 and len({r['experiment_id'] for r in rows}) == 12
    body = {'version': 'ALN36_FAU_GROUP_v1', 'origin': C.ORIGIN, 'rows': rows, 'sources': sources(), 'store': str(STORE),
            'package': C.package_binding()['zip_sha256'], 'evaluation_cells': sum(len(r['evaluation_cells']) for r in rows)}
    assert body['evaluation_cells'] == 60
    if PLAN.exists():
        old = C.read(PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
        C.write(PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); PLAN.chmod(0o444)
    print('ALN36 FAU group plan', len(rows), 'unique source fits,', body['evaluation_cells'], 'evaluation cells', C.sha(PLAN), flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'frozen source drift'
    for r in plan['rows']:
        assert C.sha(BINDINGS / r['binding']) == r['binding_sha256']
        assert C.sha(Path(core.OUT) / 'units' / f'{r["parent_id"]}.json') == r['parent_record_sha256']


def group_batcher(base, sets):
    class GroupSourceBatcher(base):
        """Parent batcher with the frozen legal source sets installed before any statistic or batch is drawn."""

        def __init__(self, coh, spec, row, dev, grid):
            super().__init__(coh, spec, row, dev, grid)
            self.fit, self.es, self.train_p = list(sets['fit']), list(sets['es']), set(sets['train_p'])
    return GroupSourceBatcher


def load_bound(row, binding):
    """Cohort with the frozen source scaler, and the binding's keys mapped to this process's segment indices."""
    coh = load_raw(row['content_fold']); keys = segment_keys(coh); index = {k: i for i, k in enumerate(keys)}
    parts = {p['id']: i for i, p in enumerate(coh.participants)}
    fit = [index[k] for k in binding['source_fit_keys']]; es = [index[k] for k in binding['source_es_keys']]
    mu, sd, _ = scaler_from(coh, fit)
    assert np.allclose(mu, binding['scaler']['mean'], rtol=1e-9, atol=1e-9) and np.allclose(sd, binding['scaler']['sd'], rtol=1e-9, atol=1e-9)
    apply_scaler(coh, np.asarray(binding['scaler']['mean']), np.asarray(binding['scaler']['sd']))
    train_p = {parts[i] for i in binding['source_ids']}
    g = row['excluded_group']
    assert all(coh.participants[p]['group'] != g for p in train_p)
    assert all(coh.segments[i]['p'] in train_p and coh.segments[i]['role'] == 'fit' for i in fit)
    assert all(coh.segments[i]['p'] in train_p and coh.segments[i]['role'] == 'es' for i in es)
    rk = binding['risk']
    risk = {'anchors': rk['anchors'], **{k: [index[x] for x in rk[k]] for k in ('cal_queries', 'cal_candidates', 'es_queries', 'es_candidates')}}
    return coh, {'fit': fit, 'es': es, 'train_p': train_p}, risk


def run_unit(row, plan, probe=False):
    import torch
    from .. import fm_aligned, local_support
    from . import train_true_nll as TT
    t0 = time.time()
    binding = C.read(BINDINGS / row['binding']); assert C.sha(BINDINGS / row['binding']) == row['binding_sha256']
    if row['tool'] == 'CBpre_true_full':
        assert C.sha(binding['cbramod_init']['path']) == binding['cbramod_init']['sha256']
    job = os.environ['SLURM_JOB_ID']
    out = BASE / 'probes' / job if probe else BASE
    store = STORE / 'probes' / job if probe else STORE
    (out / 'units').mkdir(parents=True, exist_ok=True, mode=0o700); (store / 'ckpt').mkdir(parents=True, exist_ok=True, mode=0o700)
    eid = row['experiment_id']; prefix = str(store / 'ckpt' / eid)
    total = SMOKE_EPOCHS if probe else EPOCHS[row['tool']]
    coh, sets, risk = load_bound(row, binding)
    spec = dict(row['training_signature']['bound_spec'], epochs=total)
    b = {'experiment_id': eid, 'family_id': FAMILY, 'dataset': 'fau', 'subject_fold': None, 'content_fold': row['content_fold'],
         'seed': row['seed'], 'spec': spec}
    dev = torch.device('cuda'); grid = core.grid_samples(coh.fs); log = {}
    targets = {i for i, p in enumerate(coh.participants) if p['id'] in binding['target_ids']}
    rec = {'experiment_id': eid, 'row': row, 'bound_row': b, 'status': 'running', 'device': torch.cuda.get_device_name(0),
           'probe': probe, 'truncated': total != EPOCHS[row['tool']], 'plan_sha256': C.sha(PLAN), 'job': job}
    if row['tool'] == 'local_L1':
        model, head, bt = TT.fit_local(b, coh, dev, prefix, log, group_batcher(local_support.batcher_for('aligned1000'), sets), risk, d=32, grid=grid)
    else:
        model, head, bt = TT.fit_cb(b, coh, dev, prefix, log, group_batcher(fm_aligned.AlignedBatcher, sets), risk, epochs=total,
                                    lr=(3e-4, 1e-3), d=32, grid=grid)
    assert not bt.train_p & targets and set(bt.fit) == set(sets['fit']) and set(bt.es) == set(sets['es'])
    assert log['epochs_completed'] == total and log['optimizer_steps'] > 0 and log['last_state_relative_weight_change'] > 0
    assert math.isfinite(log['best_selection_score'])
    if row['tool'] == 'CBpre_true_full':
        led = log['update_ledger']['groups']
        assert all(L['grad_steps'] == log['optimizer_steps'] and L['first_open_epoch'] == 1 for L in led), 'not a full one-step update'
    rec.update(log)
    rec['source_exclusion'] = {'excluded_group': row['excluded_group'], 'n_source_people': len(bt.train_p),
                               'source_groups': sorted({coh.participants[p]['group'] for p in bt.train_p}),
                               'th_dev_in_source': any(coh.participants[p]['dev'] for p in bt.train_p),
                               'target_people_in_source': 0, 'n_fit_segments': len(bt.fit), 'n_es_segments': len(bt.es),
                               'audio_target_stats': 'target_stats(bt) over bt.fit (source fit only)',
                               'input_scaler_sha256': binding['scaler_sha256']}
    rec['resolved_config'] = {'d': 32, 'grid_samples': grid, 'fs': coh.fs, 'epochs': total, 'tool': row['tool'],
                              'input_scaling': 'population source-fit channel scaler (no per-person z-score)'}
    rec['final_checkpoint'] = prefix + '_best.pt'; rec['final_checkpoint_sha256'] = C.sha(prefix + '_best.pt')
    rec['status'] = 'complete'; rec['total_seconds'] = round(time.time() - t0, 1)
    rec['gpu_peak_allocated_mb'] = round(torch.cuda.max_memory_allocated() / 2 ** 20)
    C.write(out / 'units' / f'{eid}.json', rec)
    print(eid, 'complete', row['tool'], row['excluded_group'], row['content_fold'], 'best', log['best_epoch'],
          round(log['best_selection_score'], 4), 'probe', probe, round(rec['total_seconds'], 1), flush=True)
    return rec


def receipts():
    out = {'pass': [], 'other': []}
    if not PLAN.exists():
        return out
    digest = C.sha(PLAN)
    for path in sorted((BASE / 'probes').glob('*/receipt.json')):
        rec = C.read(path)
        if rec.get('plan_sha256') != digest:
            continue
        out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    """Two read-only readiness items (local, CB); the smoke probe runs once in the local lane."""
    items = []
    for tool in C.TOOLS:
        item = {'name': NAME[tool], 'lane': 's35_aln36_group_' + ('local' if tool == 'local_L1' else 'cb'), 'state': 'plan_missing',
                'ready': 0, 'remaining': 6, 'slots': 1, 'initial': [], 'submit': []}
        items.append(item)
        if not PLAN.exists():
            continue
        plan = C.read(PLAN); units = BASE / 'units'
        remaining = [r for r in plan['rows'] if r['tool'] == tool and not (units / f'{r["experiment_id"]}.json').exists()]
        item['remaining'] = len(remaining)
        if not remaining:
            item['state'] = 'complete'; continue
        rec = receipts()
        if not rec['pass']:
            if rec['other']:
                item['state'] = 'engineering_probe_failed'; continue
            if tool == 'local_L1':
                item.update(state='ready', ready=1, submit=[SBATCH[tool], '--smoke'])
            else:
                item['state'] = 'awaiting_smoke'
            continue
        available = [r for r in remaining if not (units / f'{r["experiment_id"]}.FAILED.json').exists()]
        item.update(state='ready' if available else 'failed_unit_review', ready=len(available), slots=2,
                    submit=[SBATCH[tool], '--smoke-job', rec['pass'][-1].parent.name, '--tool', tool, '--max-units', '1'])
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bind', action='store_true'); ap.add_argument('--make-plan', action='store_true')
    ap.add_argument('--smoke', action='store_true'); ap.add_argument('--unit'); ap.add_argument('--probe-unit'); ap.add_argument('--smoke-job')
    ap.add_argument('--tool', choices=C.TOOLS); ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.bind:
        bind(); return
    if a.make_plan:
        make_plan(); return
    plan = C.read(PLAN); verify(plan)
    if a.unit or a.probe_unit:
        run_unit(next(r for r in plan['rows'] if r['experiment_id'] in (a.unit, a.probe_unit)), plan, probe=bool(a.probe_unit)); return
    if a.smoke:
        job = os.environ['SLURM_JOB_ID']
        receipt = {'status': 'running', 'plan_sha256': C.sha(PLAN), 'units': []}
        try:
            for tool in C.TOOLS:
                row = next(r for r in plan['rows'] if r['tool'] == tool and r['excluded_group'] == 'th' and r['content_fold'] == 0)
                rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--probe-unit', row['experiment_id']]).returncode
                assert rc == 0, f'smoke unit failed: {tool}'
                rec = C.read(BASE / 'probes' / job / 'units' / f'{row["experiment_id"]}.json')
                assert rec['truncated'] and rec['probe'] and not rec['source_exclusion']['th_dev_in_source']
                assert rec['source_exclusion']['source_groups'] == ['ci', 'ha']
                receipt['units'].append({'id': row['experiment_id'], 'tool': tool, 'peak_mb': rec['gpu_peak_allocated_mb'],
                                         'seconds': rec['total_seconds'], 'optimizer_steps': rec['optimizer_steps'],
                                         'best_epoch': rec['best_epoch'], 'risk_curve': [c.get('risk_nll_bits') for c in rec['curve']],
                                         'last_state_relative_weight_change': rec['last_state_relative_weight_change'],
                                         'n_source_people': rec['source_exclusion']['n_source_people']})
            receipt['status'] = 'pass'
        except BaseException:
            receipt.update(status='failed', traceback=traceback.format_exc()); raise
        finally:
            C.write(BASE / 'probes' / job / 'receipt.json', receipt)
        return
    rec = C.read(BASE / 'probes' / str(a.smoke_job) / 'receipt.json')
    assert rec['status'] == 'pass' and rec['plan_sha256'] == C.sha(PLAN)
    count = 0
    for row in plan['rows']:
        if a.tool and row['tool'] != a.tool:
            continue
        eid = row['experiment_id']; path = BASE / 'units' / f'{eid}.json'
        if path.exists() or (BASE / 'units' / f'{eid}.FAILED.json').exists():
            continue
        lock = BASE / 'claims' / f'{eid}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', eid]).returncode
            if rc or not path.exists():
                C.write(BASE / 'units' / f'{eid}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('aln36 FAU group unit failed')
            count += 1
        if count >= a.max_units:
            break


if __name__ == '__main__':
    main()
