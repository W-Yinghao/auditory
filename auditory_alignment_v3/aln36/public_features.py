"""ALN3.6 R1 public frozen feature banks (one per source model; GPU forward only, no fitting).

Sources: the 12 ALN36 FAU whole-group units and the 40 existing pooled seed-3401 parents (DTU and FAU, local L1 and
CBpre true-full; the same rows content_time_v1 used). Rows per bank, all kind=ss:
  source  - every legal source person's role=fit and role=es segments (readout cross-fit, OOF, ES selection);
  target  - every target person's role=fit segments (natural-U30 support candidates) and role=test segments (query).
Target people: the whole held-out group (ALN36) or the parent's outer person fold (pooled). Role=es of a target person is
never extracted. Each segment contributes the fixed 8 anchors (0.8:0.4:3.6 s) x 5 window centres [-200..600] ms, window
[c-400, c+600) ms (content_time_v1 geometry), plus the current envelope (Local row 5) and its 20/100/200/500 ms past
values. Inputs keep each source's own preprocessing: ALN36 units use their frozen population source-fit scaler; pooled
parents keep the inherited per-person z-score of their training loader (disclosed, not relabelled).
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import gc
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from ..aln34 import content_time as CT
from . import common as C
from . import fau_group as G

BASE = C.OUT / 'public_features_v1'
PLAN = BASE / 'plan.json'
STORE = C.STORE / 'public_features_v1'
CENTERS = CT.CENTERS
LAGS_MS = (20, 100, 200, 500)
NAME, LANE, SBATCH = 'c3_s35a36feat', 's35_aln36_features', 'slurm/aln35_aln36_features.sbatch'


def sources():
    files = [Path(__file__), Path(C.__file__), Path(G.__file__), Path(CT.__file__),
             C.REPO / 'auditory_alignment_v3/local_support.py', C.REPO / 'auditory_alignment_v3/fm_aligned.py',
             C.REPO / 'auditory_alignment_v3/fm_dense.py', C.REPO / 'auditory_alignment_v3/core.py']
    files += [C.REPO / d / f for d, f in core.V2_DEPS]
    return {str(p.relative_to(C.REPO)): C.sha(p) for p in sorted(set(files))}


def tool_of(row):
    return 'local_L1' if row['spec']['architecture'] == 'lag_local_tokens' else 'CBpre_true_full'


def make_plan():
    rows = []
    ct = C.read(CT.PLAN)
    for u in ct['rows']:
        r = u['source']
        if r['seed'] != C.SEED or r['dataset'] not in ('dtu', 'fau') or CT.label(r) not in ('local', 'cbramod_pretrained_full'):
            continue
        rec = Path(core.OUT) / 'units' / f'{r["experiment_id"]}.json'; ck = Path(core.OUT) / 'ckpt' / f'{r["experiment_id"]}_best.pt'
        assert C.sha(rec) == u['record_sha256'] and C.sha(ck) == u['checkpoint_sha256']
        body = {'kind': 'pooled_parent', 'dataset': r['dataset'], 'tool': tool_of(r), 'seed': r['seed'],
                'person_fold': r['subject_fold'], 'content_fold': r['content_fold'], 'source_id': r['experiment_id'],
                'source_record_sha256': u['record_sha256'], 'source_checkpoint_sha256': u['checkpoint_sha256'],
                'preprocessing': 'inherited per-person z-score over all loaded ss+cs trials (auditory_alignment.data._stdz)'}
        rows.append({**body, 'id': 'ALN36F_' + C.digest(body)})
    gp = C.read(G.PLAN)
    for r in gp['rows']:
        body = {'kind': 'whole_group', 'dataset': 'fau', 'tool': r['tool'], 'seed': r['seed'], 'excluded_group': r['excluded_group'],
                'content_fold': r['content_fold'], 'source_id': r['experiment_id'], 'group_plan_sha256': C.sha(G.PLAN),
                'binding': r['binding'], 'binding_sha256': r['binding_sha256'],
                'preprocessing': 'stageB without per-person z-score; frozen population source-fit channel scaler'}
        rows.append({**body, 'id': 'ALN36F_' + C.digest(body)})
    assert len(rows) == 52 and len({r['id'] for r in rows}) == 52
    body = {'version': 'ALN36_PUBLIC_FEATURES_v1', 'rows': rows, 'sources': sources(), 'store': str(STORE),
            'centers_ms': list(CENTERS), 'window_relative_to_center_ms': [-400, 600], 'joint_access_ms': [-600, 1200],
            'anchor_seconds': [0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.6], 'history_lags_ms': list(LAGS_MS)}
    if PLAN.exists():
        old = C.read(PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
        C.write(PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); PLAN.chmod(0o444)
    print('ALN36 public feature plan', len(rows), C.sha(PLAN), flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'frozen source drift'


def ready(row):
    if row['kind'] == 'pooled_parent':
        return True
    return (G.BASE / 'units' / f'{row["source_id"]}.json').exists()


def rebuild(row, dev):
    """Cohort, stimulus bank, batcher, frozen model, source and target participant indices."""
    import torch
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v2.temporal import build_encoder
    from auditory_alignment_v2.train import train_participants
    from auditory_alignment_v2.foundation_adapter import Backbone
    from .. import local_support, fm_aligned
    local = row['tool'] == 'local_L1'
    if row['kind'] == 'pooled_parent':
        rec_path = Path(core.OUT) / 'units' / f'{row["source_id"]}.json'; ck = Path(core.OUT) / 'ckpt' / f'{row["source_id"]}_best.pt'
        assert C.sha(rec_path) == row['source_record_sha256'] and C.sha(ck) == row['source_checkpoint_sha256']
        src_row = C.read(rec_path)['row']; b = core.bind(src_row)
        torch.manual_seed(src_row['seed']); coh = load_cohort(b)
        source = sorted(train_participants(coh, b['spec'], b['subject_fold']))
        target = sorted(i for i, p in enumerate(coh.participants)
                        if p['fold'] == b['subject_fold'] and not p.get('dev') and not p.get('test_only'))
        sets = None
    else:
        grec = C.read(G.BASE / 'units' / f'{row["source_id"]}.json'); assert grec['status'] == 'complete' and not grec['probe']
        ck = Path(grec['final_checkpoint']); assert C.sha(ck) == grec['final_checkpoint_sha256']
        grow = grec['row']; binding = C.read(G.BINDINGS / grow['binding']); assert C.sha(G.BINDINGS / grow['binding']) == row['binding_sha256']
        coh, sets, _ = G.load_bound(grow, binding)
        b = grec['bound_row']
        ids = {p['id']: i for i, p in enumerate(coh.participants)}
        source = sorted(ids[i] for i in binding['source_ids']); target = sorted(ids[i] for i in binding['target_ids'])
    assert source and target and not set(source) & set(target)
    stim = coh.stim; grid = core.grid_samples(coh.fs)
    if local:
        base = local_support.batcher_for('aligned1000')
    else:
        base = fm_aligned.AlignedBatcher
    bt = (G.group_batcher(base, sets) if sets else base)(coh, b['spec'], b, dev, grid)
    if local:
        model = build_encoder('lag_local_tokens', coh.n_ch, 32, bt.W, coh.fs).to(dev)
    else:
        model = fm_aligned.AlignedFM(Backbone('cbramod', coh.meta['dataset'], 'pretrained_full', coh.fs), 32).to(dev)
    sd = torch.load(ck, map_location=dev, weights_only=False)
    model.load_state_dict(sd['enc'] if local else sd['model'], strict=True)
    model.requires_grad_(False).eval()
    return coh, stim, bt, model, local, source, target


def extract(row, probe=False):
    import torch
    dev = torch.device('cuda'); t0 = time.time()
    coh, stim, bt, model, local, source, target = rebuild(row, dev)
    segs = coh.segments; parts = coh.participants
    src, tgt = set(source), set(target)
    items = [i for i, s in enumerate(segs) if s['kind'] == 'ss' and ((s['p'] in src and s['role'] in ('fit', 'es'))
                                                                   or (s['p'] in tgt and s['role'] in ('fit', 'test')))]
    if probe:
        keep = []
        for p in sorted(src)[:2] + sorted(tgt)[:2]:
            keep += [i for i in items if segs[i]['p'] == p][:6]
        items = sorted(keep)
    order = {}
    for i in sorted(items, key=lambda i: segs[i]['e0']):
        order.setdefault(segs[i]['p'], []).append(i)
    physical = {i: k for p, lst in order.items() for k, i in enumerate(lst)}
    offsets = CT.valid_offsets(coh.fs, bt.seg_len); nt = len(offsets)
    e = np.array([segs[i]['e0'] for i in items]); a = np.array([segs[i]['s0'] for i in items])
    idx = (a[:, None] + offsets).reshape(-1)
    env = np.asarray(stim['Local'])[5]
    lags = [int(round(ms * coh.fs / 1000)) for ms in LAGS_MS]
    arrays = {'segment_index': np.array(items), 'person': np.array([parts[segs[i]['p']]['id'] for i in items]),
              'group': np.array([parts[segs[i]['p']]['group'] for i in items]),
              'side': np.array(['source' if segs[i]['p'] in src else 'target' for i in items]),
              'role': np.array([segs[i]['role'] for i in items]), 'uid': np.array([segs[i]['uid'] for i in items]),
              'code': np.array([segs[i]['code'] for i in items]), 'part': np.array([str(segs[i]['part']) for i in items]),
              'e0': e, 's0': a, 'physical_rank': np.array([physical[i] for i in items]), 'anchor_offsets': offsets,
              'env': env[idx].reshape(len(items), nt).astype(np.float64),
              'env_history': np.stack([env[idx - L] for L in lags], axis=-1).reshape(len(items), nt, len(lags)).astype(np.float64)}
    flat_e = np.repeat(e, nt); flat_t = np.tile(offsets, len(e))
    with torch.no_grad():
        for center in CENTERS:
            shift = round(center * coh.fs / 1000); out = []
            for k in range(0, len(flat_e), 1024):
                ee = torch.as_tensor(flat_e[k:k + 1024], device=dev); tt = torch.as_tensor(flat_t[k:k + 1024] + shift, device=dev)
                x = bt.patches(ee + tt) if local else bt.windows(ee, tt[:, None])
                out.append(model(x).float().cpu().numpy())
            arrays[f'model_{center}'] = np.concatenate(out).reshape(len(items), nt, -1).astype(np.float32)
    dest = (STORE / 'probes' / os.environ['SLURM_JOB_ID'] if probe else STORE / 'banks') / row['id']
    dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(dest / 'arrays.npz', **arrays)
    meta = {'row': row, 'plan_sha256': C.sha(PLAN), 'source_sha256': C.sha(__file__), 'probe': probe, 'fs': coh.fs,
            'seg_len': bt.seg_len, 'n_segments': len(items), 'n_anchors_per_segment': nt, 'lag_samples': lags,
            'n_source_people': len(src), 'n_target_people': len(tgt),
            'source_people': sorted(parts[i]['id'] for i in src), 'target_people': sorted(parts[i]['id'] for i in tgt),
            'target_person_fold': {parts[i]['id']: parts[i]['fold'] for i in tgt},
            'groups': {parts[i]['id']: parts[i]['group'] for i in src | tgt},
            'model_access_ms': {str(c): [c - 400, c + 600] for c in CENTERS}, 'array_sha256': C.sha(dest / 'arrays.npz'),
            'seconds': round(time.time() - t0, 1), 'gpu_peak_mb': round(torch.cuda.max_memory_allocated() / 2 ** 20),
            'job': os.environ['SLURM_JOB_ID'], 'device': torch.cuda.get_device_name(0)}
    C.write(dest / 'meta.json', meta)
    if not probe:
        C.write(BASE / 'units' / f'{row["id"]}.json', {'status': 'complete', 'bank': str(dest), 'meta_sha256': C.sha(dest / 'meta.json'),
                                                      'array_sha256': meta['array_sha256'], 'row': row, 'seconds': meta['seconds']})
    print(row['id'], row['kind'], row['dataset'], row['tool'], len(items), 'segments', meta['seconds'], 's', flush=True)
    del bt, model, coh, stim; gc.collect(); torch.cuda.empty_cache()
    return meta


def receipts():
    out = {'pass': [], 'other': []}
    if not PLAN.exists():
        return out
    for path in sorted((BASE / 'probes').glob('*/receipt.json')):
        rec = C.read(path)
        if rec.get('plan_sha256') == C.sha(PLAN):
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    status = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 52, 'slots': 1, 'initial': [], 'submit': []}
    if not PLAN.exists():
        return status
    plan = C.read(PLAN); units = BASE / 'units'
    remaining = [r for r in plan['rows'] if not (units / f'{r["id"]}.json').exists()]
    status['remaining'] = len(remaining)
    if not remaining:
        status['state'] = 'complete'; return status
    rec = receipts()
    if not rec['pass']:
        if rec['other']:
            status['state'] = 'engineering_probe_failed'; return status
        status.update(state='ready', ready=1, submit=[SBATCH, '--smoke']); return status
    available = [r for r in remaining if ready(r) and not (units / f'{r["id"]}.FAILED.json').exists()]
    status.update(state='ready' if available else 'waiting_for_sources', ready=len(available), slots=2,
                  submit=[SBATCH, '--smoke-job', rec['pass'][-1].parent.name, '--max-units', '8'])
    return status


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--make-plan', action='store_true'); ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--probe-unit'); ap.add_argument('--smoke-job'); ap.add_argument('--max-units', type=int, default=8)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = C.read(PLAN); verify(plan)
    if a.unit or a.probe_unit:
        extract(next(r for r in plan['rows'] if r['id'] in (a.unit, a.probe_unit)), probe=bool(a.probe_unit)); return
    if a.smoke:
        job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': C.sha(PLAN), 'units': []}
        try:
            picks = [next(r for r in plan['rows'] if r['kind'] == 'pooled_parent' and r['dataset'] == ds and r['tool'] == tool)
                     for ds in ('dtu', 'fau') for tool in C.TOOLS]
            for r in picks:
                rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--probe-unit', r['id']]).returncode
                assert rc == 0, r['id']
                meta = C.read(STORE / 'probes' / job / r['id'] / 'meta.json')
                with np.load(STORE / 'probes' / job / r['id'] / 'arrays.npz') as z:
                    assert all(np.isfinite(z[f'model_{c}']).all() for c in CENTERS) and np.isfinite(z['env_history']).all()
                    assert set(z['side'].tolist()) == {'source', 'target'}
                receipt['units'].append({'id': r['id'], 'seconds': meta['seconds'], 'peak_mb': meta['gpu_peak_mb'], 'segments': meta['n_segments']})
            receipt['status'] = 'pass'
        except BaseException:
            receipt.update(status='failed', traceback=traceback.format_exc()); raise
        finally:
            C.write(BASE / 'probes' / job / 'receipt.json', receipt)
        return
    rec = C.read(BASE / 'probes' / str(a.smoke_job) / 'receipt.json'); assert rec['status'] == 'pass' and rec['plan_sha256'] == C.sha(PLAN)
    count = 0
    for row in plan['rows']:
        path = BASE / 'units' / f'{row["id"]}.json'
        if path.exists() or (BASE / 'units' / f'{row["id"]}.FAILED.json').exists() or not ready(row):
            continue
        lock = BASE / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', row['id']]).returncode
            if rc or not path.exists():
                C.write(BASE / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('aln36 feature bank failed')
            count += 1
        if count >= a.max_units:
            break


if __name__ == '__main__':
    main()
