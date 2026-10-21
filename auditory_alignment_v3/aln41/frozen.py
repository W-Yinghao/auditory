"""ALN4.1 R1 frozen representations of the five arms for DTU, FAU and the private children (GPU forward; no training).

Arms: B0 = Stage1 CBraMod; TCS / TNCE / GCS / TCS_WRONG = the production source backbones at update 10000 (fixed final
transfer step) with their learned gate logits a (q0 = softmax(a); B0 uniform). Three crops per anchor/trial through
timebank (crop-only resampling, pad 200, one patch per crop), raw backbone tokens [3, C, 200].
Public (DTU 64 ch / FAU 31 ch, 128 Hz, inherited per-person z-score of the pooled loaders): every person's ss segments of
roles fit/es/test, the fixed 8 anchors (0.8:0.4:3.6 s); targets = current envelope (Local row 5) and 20/100/200/500 ms
lags. For each original pooled fold (5 person folds x the loaded content fold) one PCA64 shared by the three slots is
fitted on <= 8190 token rows (2730 per slot) of that fold's training people's role=fit anchors (fixed id order +
seed 3437); every row of the cohort is projected with it. Private: 64 children, all trials; per outer fold a PCA64 on
the training children's fit trials; per child the trial mean and std (ddof 0) of each slot's raw token vector for the
frozen age readout (no labels, no q).
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
from . import source as SRC

BASE = SRC.OUT / 'frozen_v1'
STORE = SRC.STORE.parent / 'frozen_v1'
ARMS = ('B0', 'TCS', 'TNCE', 'GCS', 'TCS_WRONG')
COHORTS = (('dtu', 0), ('dtu', 1), ('fau', 0), ('fau', 1), ('private_bdf', None))
PCA_DIM, PCA_ROWS_PER_SLOT, PCA_SEED = 64, 2730, 3437
LAGS_MS = (20, 100, 200, 500)
CS_ANCHORS = 16
NAME, LANE, SBATCH = 'c3_s35a41frz', 's35_aln41_frozen', 'slurm/aln35_aln41_frozen.sbatch'
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest


def sources():
    here = Path(__file__).parent
    files = [here / 'frozen.py', here / 'timebank.py', here / 'time_access.py', Path(CT.__file__),
             Path(core.REPO) / 'auditory_alignment/data.py', Path(core.REPO) / 'auditory_alignment_v2/run.py',
             Path(core.REPO) / 'auditory_alignment_v2/train.py', Path(core.REPO) / 'auditory_alignment_v2/foundation_adapter.py']
    return {str(p.relative_to(core.REPO)): sha(p) for p in sorted(set(files))}


def make_plan():
    rows = []
    for arm in ARMS:
        for ds, cf in COHORTS:
            body = {'arm': arm, 'dataset': ds, 'content_fold': cf, 'seed': SRC.SEED}
            rows.append({**body, 'id': 'ALN41Z_' + digest(body, 16)})
    body = {'version': 'ALN41_FROZEN_v1', 'rows': rows, 'sources': sources(), 'store': str(STORE),
            'source_plan_sha256': sha(SRC.BASE / 'plan.json'), 'pca': {'dim': PCA_DIM, 'rows_per_slot': PCA_ROWS_PER_SLOT, 'seed': PCA_SEED},
            'anchors_s': [0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.6]}
    plan = BASE / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700); write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    print('ALN41 frozen plan', len(rows), sha(plan), flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'frozen source drift'


def arm_state(arm):
    """(backbone net state or None, q0, provenance)."""
    import torch
    if arm == 'B0':
        return None, np.full(3, 1 / 3), {'kind': 'generic_cbramod'}
    sel = read(SRC.BASE / 'selection.json'); row = next(r for r in sel['production_rows'] if r['arm'] == arm)
    rec = read(SRC.BASE / 'units' / f'{row["id"]}.json'); assert rec['status'] == 'complete'
    ck = rec['checkpoints'][str(SRC.PROD_STEPS)]; assert sha(ck['path']) == ck['sha256']
    st = torch.load(ck['path'], map_location='cpu', weights_only=False)
    net = {k[len('net.'):]: v for k, v in st['backbone'].items() if k.startswith('net.')}
    q0 = torch.softmax(st['a'].double(), 0).numpy()
    return net, q0, {'kind': 'aln41_source', 'unit': row['id'], 'checkpoint': ck, 'a': st['a'].tolist()}


def ready(row):
    if row['arm'] == 'B0':
        return True
    if not (SRC.BASE / 'selection.json').exists():
        return False
    sel = read(SRC.BASE / 'selection.json'); r = next(x for x in sel['production_rows'] if x['arm'] == row['arm'])
    return (SRC.BASE / 'units' / f'{r["id"]}.json').exists()


def backbone(dataset_key, net, dev):
    from auditory_alignment_v2.foundation_adapter import Backbone
    bb = Backbone('cbramod', dataset_key, 'pretrained_full', 200, init_state=net).to(dev).eval()
    bb.requires_grad_(False)
    return bb


def tokens(bb, crops_fn, n, fs, chunk=256):
    """float16 CPU tokens [n, 3, C*200]."""
    import torch
    from . import timebank as TB
    out = []
    with torch.no_grad():
        for s in range(0, n, chunk):
            crops = crops_fn(s, min(n, s + chunk))
            B = crops[0].shape[0]
            h = bb(TB.crop_inputs(crops, fs))[:, :, 0]
            out.append(h.reshape(3, B, -1).transpose(0, 1).half().cpu())
    return torch.cat(out)


def pca_fit(T, rows, seed):
    """Shared PCA over slots: <= 2730 rows per slot from `rows` (fixed id order + seed), mean/scale from those rows."""
    import torch
    rows = np.sort(np.asarray(rows)); rng = np.random.default_rng(seed)
    pick = rows if len(rows) <= PCA_ROWS_PER_SLOT else np.sort(rng.choice(rows, PCA_ROWS_PER_SLOT, replace=False))
    X = torch.cat([T[pick, k].float() for k in range(3)]).cuda()
    mu = X.mean(0); sd = X.std(0) + 1e-6; Z = (X - mu) / sd
    dim = min(PCA_DIM, Z.shape[1], len(Z) - 1)
    _, S, Vh = torch.linalg.svd(Z, full_matrices=False)
    comp = Vh[:dim]
    explained = float((S[:dim] ** 2).sum() / (S ** 2).sum())
    return {'mu': mu.cpu(), 'sd': sd.cpu(), 'components': comp.cpu(), 'n_rows': int(len(Z)), 'dim': int(dim),
            'explained_variance': explained, 'row_ids': pick.tolist()}


def pca_apply(T, p, chunk=20000):
    import torch
    mu, sd, comp = p['mu'].cuda(), p['sd'].cuda(), p['components'].cuda().T
    out = []
    for s in range(0, len(T), chunk):
        X = T[s:s + chunk].float().cuda()
        out.append((((X - mu) / sd) @ comp).cpu())
    return torch.cat(out).numpy().astype(np.float32)


def public_unit(row, probe):
    import torch
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v2.train import train_participants
    from . import timebank as TB
    dev = torch.device('cuda'); ds, cf = row['dataset'], row['content_fold']
    b = {'experiment_id': row['id'], 'family_id': 'ALN41', 'dataset': ds, 'subject_fold': 0, 'content_fold': cf, 'seed': SRC.SEED,
         'spec': {'architecture': 'cbramod', 'window': 'full', 'objective': 'NCE', 'target': 'local', 'audio_head': 'fixed_features',
                  'training_task': 'paired_alignment', 'epochs': 1, 'adaptation': 'pretrained_full'}}
    coh = load_cohort(b); segs = coh.segments; parts = coh.participants
    items = [i for i, s in enumerate(segs) if s['kind'] == 'ss' and s['role'] in ('fit', 'es', 'test') and not parts[s['p']].get('test_only')]
    if probe:
        items = items[:64]
    offs = CT.valid_offsets(coh.fs, coh.meta['seg_len']); nt = len(offs)
    E = torch.as_tensor(coh.eeg, dtype=torch.float32)
    lay = TB.layout(coh.fs)
    e0 = np.array([segs[i]['e0'] for i in items]); anchor = (e0[:, None] + offs[None]).reshape(-1)

    def crops_fn(s, t):
        a = torch.as_tensor(anchor[s:t])
        return [E[:, a[:, None] + torch.arange(lo, hi)[None]].permute(1, 0, 2).to(dev) for lo, hi, _ in lay]
    net, q0, prov = arm_state(row['arm'])
    bb = backbone(ds, net, dev)
    T = tokens(bb, crops_fn, len(anchor), coh.fs)
    env = np.asarray(coh.stim['Local'])[5]
    s0 = np.array([segs[i]['s0'] for i in items]); aidx = (s0[:, None] + offs[None]).reshape(-1)
    lags = [int(round(ms * coh.fs / 1000)) for ms in LAGS_MS]
    person = np.repeat([parts[segs[i]['p']]['id'] for i in items], nt); role = np.repeat([segs[i]['role'] for i in items], nt)
    seg_index = np.repeat(np.arange(len(items)), nt)
    meta = {'row': row, 'arm_provenance': prov, 'q0': q0.tolist(), 'fs': coh.fs, 'n_anchor_rows': int(len(anchor)), 'n_segments': len(items),
            'crop_layout': lay, 'anchor_offsets': offs.tolist(), 'groups': {p['id']: p['group'] for p in parts},
            'folds': {p['id']: p['fold'] for p in parts}, 'dev_people': [p['id'] for p in parts if p.get('dev')], 'pca': {}}
    dest = (STORE / 'probes' / os.environ['SLURM_JOB_ID'] if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    arrays = {'person': person, 'role': role, 'segment': seg_index, 'e0': np.repeat(e0, nt), 's0': np.repeat(s0, nt),
              'uid': np.repeat([segs[i]['uid'] for i in items], nt), 'env': env[aidx].astype(np.float64),
              'env_history': np.stack([env[aidx - L] for L in lags], 1).astype(np.float64)}
    # Competing-talker segments for the public attention endpoint: 16 anchors per 5 s, attended and ignored envelopes.
    cs = [i for i, s in enumerate(segs) if s['kind'] == 'cs' and s.get('s0_ign') is not None and s['role'] in ('fit', 'es', 'test')
          and not parts[s['p']].get('test_only')]
    if probe:
        cs = cs[:16]
    cs_offs = np.rint(np.linspace(0.4, 4.15, CS_ANCHORS) * coh.fs).astype(int)
    assert cs_offs.min() + lay[0][0] >= 0 and cs_offs.max() + lay[2][1] <= coh.meta['seg_len']
    ce0 = np.array([segs[i]['e0'] for i in cs]); canchor = (ce0[:, None] + cs_offs[None]).reshape(-1)

    def cs_crops(s, t):
        a = torch.as_tensor(canchor[s:t])
        return [E[:, a[:, None] + torch.arange(lo, hi)[None]].permute(1, 0, 2).to(dev) for lo, hi, _ in lay]
    Tc = tokens(bb, cs_crops, len(canchor), coh.fs) if len(cs) else None
    for key, field in (('cs_env_att', 's0'), ('cs_env_ign', 's0_ign')):
        st = np.array([segs[i][field] for i in cs]); arrays[key] = env[(st[:, None] + cs_offs[None])].astype(np.float64)
    arrays.update(cs_person=np.array([parts[segs[i]['p']]['id'] for i in cs]), cs_role=np.array([segs[i]['role'] for i in cs]),
                  cs_code=np.array([str(segs[i]['code']) for i in cs]), cs_e0=ce0, cs_offsets=cs_offs)
    meta['cs'] = {'n_segments': len(cs), 'anchors_per_segment': CS_ANCHORS, 'seg_len': coh.meta['seg_len']}
    for sf in range(5):
        tp = train_participants(coh, b['spec'], sf); train_ids = {parts[i]['id'] for i in tp}
        fit_rows = np.flatnonzero(np.isin(person, list(train_ids)) & (role == 'fit'))
        p = pca_fit(T, fit_rows, PCA_SEED + sf)
        arrays[f'pca_sf{sf}'] = pca_apply(T.reshape(len(T) * 3, -1), p).reshape(len(T), 3, -1)
        if Tc is not None:
            arrays[f'cs_pca_sf{sf}'] = pca_apply(Tc.reshape(len(Tc) * 3, -1), p).reshape(len(cs), CS_ANCHORS, 3, -1)
        meta['pca'][str(sf)] = {k: v for k, v in p.items() if k in ('n_rows', 'dim', 'explained_variance')}
        meta['pca'][str(sf)]['row_ids_sha256'] = digest(p['row_ids']); meta['pca'][str(sf)]['train_people'] = sorted(train_ids)
        torch.save({k: p[k] for k in ('mu', 'sd', 'components')}, dest / f'pca_sf{sf}.pt')
    np.savez_compressed(dest / 'arrays.npz', **arrays)
    meta['array_sha256'] = sha(dest / 'arrays.npz')
    write(dest / 'meta.json', meta)
    del T, Tc, E, coh; gc.collect()
    return dest, meta


def private_unit(row, probe):
    import torch
    from auditory_alignment import data
    from . import timebank as TB
    dev = torch.device('cuda')
    kids = data.load_private()
    if probe:
        kids = kids[:6]
    X = np.concatenate([k['x'] for k in kids]).astype(np.float32); owner = np.concatenate([[i] * len(k['y']) for i, k in enumerate(kids)])
    Xt = torch.as_tensor(X); lay = TB.layout(250)

    def crops_fn(s, t):
        return [Xt[s:t, :, 50 + lo:50 + hi].to(dev) for lo, hi, _ in lay]
    net, q0, prov = arm_state(row['arm'])
    bb = backbone('private_bdf', net, dev)
    T = tokens(bb, crops_fn, len(X), 250)
    dest = (STORE / 'probes' / os.environ['SLURM_JOB_ID'] if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    arrays = {'child_index': owner, 'trial': np.concatenate([np.arange(len(k['y'])) for k in kids])}
    age = np.zeros((len(kids), 3, 2, T.shape[-1]), np.float32)
    for i in range(len(kids)):
        t = T[owner == i].float()
        age[i, :, 0] = t.mean(0).numpy(); age[i, :, 1] = t.std(0, unbiased=False).numpy()
    arrays['age_features'] = age
    meta = {'row': row, 'arm_provenance': prov, 'q0': q0.tolist(), 'children': {str(i): k['id'] for i, k in enumerate(kids)},
            'crop_layout': lay, 'n_trials': int(len(X)), 'pca': {},
            'age_feature': 'per child: trial mean and std (ddof 0) of each slot raw token vector [C*200], slot-major, no labels, no q'}
    folds = np.array([k['fold'] for k in kids])
    for f in range(5):
        train = np.flatnonzero(folds != f)
        fit_rows = np.flatnonzero(np.isin(owner, train) & ~np.concatenate([k['es_mask'] for k in kids]))
        p = pca_fit(T, fit_rows, PCA_SEED + 100 + f)
        arrays[f'pca_f{f}'] = pca_apply(T.reshape(len(T) * 3, -1), p).reshape(len(T), 3, -1)
        meta['pca'][str(f)] = {k: v for k, v in p.items() if k in ('n_rows', 'dim', 'explained_variance')}
        meta['pca'][str(f)]['row_ids_sha256'] = digest(p['row_ids'])
        torch.save({k: p[k] for k in ('mu', 'sd', 'components')}, dest / f'pca_f{f}.pt')
    np.savez_compressed(dest / 'arrays.npz', **arrays)
    meta['array_sha256'] = sha(dest / 'arrays.npz'); write(dest / 'meta.json', meta)
    del T, Xt; gc.collect()
    return dest, meta


def run_unit(row, plan, probe=False):
    import torch
    started = time.time()
    dest, meta = (private_unit if row['dataset'] == 'private_bdf' else public_unit)(row, probe)
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(BASE / 'plan.json'), 'dest': str(dest),
           'meta_sha256': sha(dest / 'meta.json'), 'array_sha256': meta['array_sha256'], 'seconds': time.time() - started,
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': os.environ['SLURM_JOB_ID']}
    out = BASE / 'probes' / os.environ['SLURM_JOB_ID'] if probe else BASE
    write(out / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], row['arm'], row['dataset'], row['content_fold'], 'complete', round(rec['seconds'], 1), flush=True)
    return rec


def receipts():
    out = {'pass': [], 'other': []}
    if not (BASE / 'plan.json').exists():
        return out
    for path in sorted((BASE / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('plan_sha256') == sha(BASE / 'plan.json'):
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 25, 'slots': 1, 'initial': [], 'submit': []}
    if not (BASE / 'plan.json').exists():
        return st
    plan = read(BASE / 'plan.json')
    remaining = [r for r in plan['rows'] if not (BASE / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(remaining)
    if not remaining:
        st['state'] = 'complete'; return st
    rec = receipts()
    if not rec['pass']:
        if rec['other']:
            st['state'] = 'engineering_probe_failed'; return st
        st.update(state='ready', ready=1, submit=[SBATCH, '--smoke']); return st
    available = [r for r in remaining if ready(r) and not (BASE / 'units' / f'{r["id"]}.FAILED.json').exists()]
    st.update(state='ready' if available else 'waiting_for_sources', ready=len(available), slots=2,
              submit=[SBATCH, '--smoke-job', rec['pass'][-1].parent.name, '--max-units', '3'])
    return st


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--make-plan', action='store_true'); ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--smoke-job'); ap.add_argument('--max-units', type=int, default=3)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = read(BASE / 'plan.json'); verify(plan)
    if a.unit:
        run_unit(next(r for r in plan['rows'] if r['id'] == a.unit), plan); return
    if a.smoke:
        job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': sha(BASE / 'plan.json'), 'units': []}
        try:
            for ds, cf in (('fau', 0), ('private_bdf', None)):
                row = next(r for r in plan['rows'] if r['arm'] == 'B0' and r['dataset'] == ds and r['content_fold'] == cf)
                rec = run_unit(row, plan, probe=True)
                with np.load(Path(rec['dest']) / 'arrays.npz') as z:
                    key = 'pca_sf0' if ds == 'fau' else 'pca_f0'
                    assert np.isfinite(z[key]).all() and z[key].shape[1:] == (3, z[key].shape[2])
                receipt['units'].append({'dataset': ds, 'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb']})
            receipt['status'] = 'pass'
        except BaseException:
            receipt.update(status='failed', traceback=traceback.format_exc()); raise
        finally:
            write(BASE / 'probes' / job / 'receipt.json', receipt)
        return
    rec = read(BASE / 'probes' / str(a.smoke_job) / 'receipt.json'); assert rec['status'] == 'pass' and rec['plan_sha256'] == sha(BASE / 'plan.json')
    count = 0
    for row in plan['rows']:
        path = BASE / 'units' / f'{row["id"]}.json'
        if path.exists() or (BASE / 'units' / f'{row["id"]}.FAILED.json').exists() or not ready(row):
            continue
        lock = BASE / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', row['id']]).returncode
            if rc or not path.exists():
                write(BASE / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('aln41 frozen unit failed')
            count += 1
        if count >= a.max_units:
            break


if __name__ == '__main__':
    main()
