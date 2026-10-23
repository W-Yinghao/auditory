"""DEP12 optional 400 ms input-perturbation panel v4 (Agent M; = v3 on measure_v5 / public_features_v5 + plan_ext3 (DTU / FAU); package v1.2 02 §5.2 last paragraph, 03 §4.5).

Not a neural latency: an input-support perturbation of the frozen encoders. For every main measurement panel anchor q (128 Hz),
three native crops equal in physical time to the 64 Hz windows [-12:13] / [0:26] / [13:39] of 03 §4.5:
  W0 eeg[q-24 : q+26]  (50 samples, [-187.5, +203.125) ms)  -> 78 points
  W1 eeg[q    : q+52]  (52 samples, [0, +406.25) ms)        -> 81 points
  W2 eeg[q+26 : q+78]  (52 samples, [+203.125, +609.375) ms) -> 81 points
Each crop alone is resampled (aln41.timebank.resample; lengths by aln41.time_access.output_length rounding) and placed at index 40
of the same all-zero 1 s 200-point container; pad_mask marks the zeros (validated by encoders.py). Every encoder, the same
panels, descriptors, calibration rule (each window support calibrated on its own training-people panels) and null bank as the
main measurement. W2 reads q+78 (two samples beyond the main window); every panel anchor keeps it inside the guard (checked: 0
violations). Outputs are labelled support 'pert_W0/W1/W2' and are never mixed with the main 1 s results.
Feature cache: STORE/<encoder>__<enc_key>/<ds>/pert400_v1/<defs16>/panels_W{0,1,2}.npz (+ meta.json); records under
results/auditory_alignment_v3/dep12/measurement/public_perturb/<ds>/<encoder>/.
CLI (Slurm only): python -m auditory_alignment_v3.dep12.perturb {plan, smoke, worker [--max-units N], unit --id ID, measure-all, status}
"""
from __future__ import annotations

import argparse
from datetime import datetime
import gc
import gzip
import json
import os
from pathlib import Path
import shutil
import time
import traceback

import numpy as np

from .. import core
from . import dependence_measure as DM
from . import measure_v5 as M
from . import panels as PN
from . import public_features_v5 as PF

BASE = PN.OUT / 'perturb_v1'
SUPPORT_ID = 'pert400_v1'
WINDOWS = {'W0': (-24, 26), 'W1': (0, 52), 'W2': (26, 78)}
OFFSET = 40
MEAS = M.RESULTS / 'measurement' / 'public_perturb'
NAME, LANE, SBATCH = 'c3_s35dMpert', 's35_dep12_pub_perturb', 'slurm/aln35_dep12_pub_perturb_v4.sbatch'
sha, write, read, digest = PN.sha, PN.write, PN.read, PN.digest


def sources():
    here = Path(__file__).parent
    return {**PF.sources(), str((here / 'perturb_v4.py').relative_to(core.REPO)): sha(here / 'perturb_v4.py'),
            str((here / 'measure_v5.py').relative_to(core.REPO)): sha(here / 'measure_v5.py')}


def layout():
    from ..aln41 import time_access as TA
    return {w: (a, b, TA.output_length(b - a, PN.FS, 200)) for w, (a, b) in WINDOWS.items()}


def make_plan():
    path = BASE / 'plan.json'
    main = read(PF.FEAT / 'plan.json')
    rows = [{**{k: r[k] for k in ('dataset', 'group', 'encoders')}, 'id': 'DEP12PP_' + digest({'dataset': r['dataset'], 'group': r['group'],
                                                                                              'encoders': r['encoders'], 'support': SUPPORT_ID}, 16)}
            for r in main['rows'] if not r['group'].startswith('aln34')]
    lay = layout()
    assert [v[2] for v in lay.values()] == [78, 81, 81], lay
    body = {'version': 'DEP12_PUB_PERTURB_v1', 'rows': rows, 'support_id': SUPPORT_ID, 'windows': WINDOWS, 'layout': lay,
            'container_offset': OFFSET, 'defs_sha256': {ds: PF.defs_hash(ds) for ds in PN.DATASETS}}
    if path.exists():
        old = read(path); assert all(old[k] == v for k, v in body.items() if k != 'layout'), 'immutable perturbation plan drift'
        return old
    BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    write(path, {**body, 'created': datetime.now().astimezone().isoformat()}); path.chmod(0o444)
    print('perturbation plan', len(rows), sha(path), flush=True)
    return body


EXT_PLAN = BASE / 'plan_ext1.json'


def make_plan_ext():
    """Supplementary frozen plan for the mechanism-control seeds (DECISIONS M17); rows wait until the encoders are available."""
    rows = []
    for ds in PN.DATASETS:
        for a in PF.EXT_ARMS:
            rows.append({'dataset': ds, 'group': a, 'encoders': [a],
                         'id': 'DEP12PP_' + digest({'dataset': ds, 'group': a, 'encoders': [a], 'support': SUPPORT_ID}, 16)})
    body = {'version': 'DEP12_PUB_PERTURB_EXT1', 'base_plan_sha256': sha(BASE / 'plan.json'), 'rows': rows, 'support_id': SUPPORT_ID}
    if EXT_PLAN.exists():
        old = read(EXT_PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable perturbation extension drift'
        return old
    write(EXT_PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); EXT_PLAN.chmod(0o444)
    print('perturbation extension plan', len(rows), sha(EXT_PLAN), flush=True)
    return body


EXT2_PLAN = BASE / 'plan_ext2.json'


def make_plan_ext2():
    """Second supplementary frozen perturbation plan: ext2 cs_pair_noise (M19)."""
    rows = []
    for ds in PN.DATASETS:
        for a in PF.EXT2_ARMS:
            rows.append({'dataset': ds, 'group': a, 'encoders': [a],
                         'id': 'DEP12PP_' + digest({'dataset': ds, 'group': a, 'encoders': [a], 'support': SUPPORT_ID}, 16)})
    body = {'version': 'DEP12_PUB_PERTURB_EXT2', 'base_plan_sha256': sha(BASE / 'plan.json'), 'rows': rows, 'support_id': SUPPORT_ID}
    if EXT2_PLAN.exists():
        old = read(EXT2_PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable perturbation ext2 drift'
        return old
    write(EXT2_PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); EXT2_PLAN.chmod(0o444)
    print('perturbation ext2 plan', len(rows), sha(EXT2_PLAN), flush=True)
    return body


EXT3_PLAN = BASE / 'plan_ext3.json'


def make_plan_ext3():
    """Third supplementary frozen perturbation plan: ext3 ssl_continue on DTU / FAU (M21)."""
    rows = []
    for ds in PN.DATASETS:
        for a in PF.EXT3_ARMS:
            rows.append({'dataset': ds, 'group': a, 'encoders': [a],
                         'id': 'DEP12PP_' + digest({'dataset': ds, 'group': a, 'encoders': [a], 'support': SUPPORT_ID}, 16)})
    body = {'version': 'DEP12_PUB_PERTURB_EXT3', 'base_plan_sha256': sha(BASE / 'plan.json'), 'rows': rows, 'support_id': SUPPORT_ID}
    if EXT3_PLAN.exists():
        old = read(EXT3_PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable perturbation ext3 drift'
        return old
    write(EXT3_PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); EXT3_PLAN.chmod(0o444)
    print('perturbation ext3 plan', len(rows), sha(EXT3_PLAN), flush=True)
    return body


def plan_rows():
    rows = list(read(BASE / 'plan.json')['rows'])
    for p in (EXT_PLAN, EXT2_PLAN, EXT3_PLAN):
        if p.exists():
            rows += read(p)['rows']
    return rows


def containers(x, q, dev):
    """x [C, n] numpy, q anchors -> {W: (z [len(q), C, 200] torch, pad_mask [200] bool)}."""
    import torch
    from ..aln41 import timebank as TB
    out = {}
    for w, (a, b, n_out) in layout().items():
        idx = np.asarray(q)[:, None] + np.arange(a, b)[None]
        assert idx.min() >= 0 and idx.max() < x.shape[1]
        crop = torch.as_tensor(np.ascontiguousarray(x[:, idx].transpose(1, 0, 2)), device=dev, dtype=torch.float32)
        r = TB.resample(crop, n_out)
        z = torch.zeros(len(q), x.shape[0], 200, device=dev, dtype=torch.float32); z[..., OFFSET:OFFSET + n_out] = r
        mask = np.ones(200, bool); mask[OFFSET:OFFSET + n_out] = False
        out[w] = (z, mask)
    return out


def run_unit(row, probe=False, people_limit=None):
    import torch
    t0 = time.time(); dev = PF._device(); ds = row['dataset']
    ENC = PF.enc_module(); R = ENC.refresh(); defs = PN.defs(ds); dsha = PF.defs_hash(ds); coh = PF.Cohort(ds)
    sc = read(PN.DEFS / ds / 'scan.json'); trials = {(p, r['trial']): r for p, rows in sc['trials'].items() for r in rows}
    encs = {}
    for name in row['encoders']:
        e = ENC.load(name, dev)
        tp, cp, _ = PF.needs(defs, coh, PF.scope_of(R[name], ds))
        ids = tp + cp
        if people_limit:
            ids = [p for p in ids if defs['panels'][p]['person'] in people_limit]
        encs[name] = {'enc': e, 'key': PF.enc_key(e.meta), 'ids': ids, 'U': {w: {} for w in WINDOWS}}
    byperson = {}
    for name, E in encs.items():
        for pid in E['ids']:
            byperson.setdefault(defs['panels'][pid]['person'], set()).add(pid)
    timing = {'load_s': 0.0, 'forward_s': 0.0, 'windows': 0}
    for person in sorted(byperson):
        a = time.time(); xs = coh.load(person); timing['load_s'] += time.time() - a
        for pid in sorted(byperson[person]):
            pn = defs['panels'][pid]
            for blk in pn['blocks']:
                r = trials[(person, blk['trial'])]; q = PN.anchors_of(blk)
                assert (q + WINDOWS['W2'][1] <= r['g1']).all() and (q + WINDOWS['W0'][0] >= r['g0']).all(), 'perturbation crop outside guard'
            a = time.time()
            Z = [containers(xs[blk['trial']], PN.anchors_of(blk), dev) for blk in pn['blocks']]
            for name, E in encs.items():
                if pid not in E['ids']:
                    continue
                for w in WINDOWS:
                    z = torch.cat([zz[w][0] for zz in Z]); mask = Z[0][w][1]
                    U = PF.represent_masked(E['enc'], z, coh.channels, mask)
                    E['U'][w][pid] = PF.sqd(U); timing['windows'] += len(z)
            timing['forward_s'] += time.time() - a
        del xs; gc.collect()
    coh.close(); res = {}
    for name, E in encs.items():
        dest = (PF.STORE / 'probes' / os.environ['SLURM_JOB_ID'] if probe else PF.STORE) / f'{name}__{E["key"]}' / ds / SUPPORT_ID / dsha[:16]
        tmp = dest.with_name(dest.name + '.tmp'); shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True, mode=0o700)
        for w in WINDOWS:
            np.savez(tmp / f'panels_{w}.npz', ids=np.array(E['ids']), d2=np.stack([E['U'][w][p] for p in E['ids']]))
        info = {'encoder': name, 'enc_key': E['key'], 'dataset': ds, 'support_id': SUPPORT_ID, 'layout': layout(), 'offset': OFFSET,
                'defs_sha256': dsha, 'n_panels': len(E['ids']), 'registry': {k: R[name].get(k) for k in ('kind', 'input_support_flag', 'data_access', 'seed')},
                'files_sha256': {f'panels_{w}.npz': sha(tmp / f'panels_{w}.npz') for w in WINDOWS}, 'sources': sources(),
                'job': os.environ.get('SLURM_JOB_ID'), 'device': PF._device_name(dev), 'probe': probe}
        write(tmp / 'meta.json', info)
        if dest.exists():
            shutil.rmtree(dest)
        os.replace(tmp, dest)
        res[name] = {'dest': str(dest), 'files_sha256': info['files_sha256']}
    timing['total_s'] = time.time() - t0
    timing['gpu_peak_mb'] = torch.cuda.max_memory_allocated() / 2 ** 20 if dev.type == 'cuda' else None
    return res, timing


# ------------------------------------------------------------------------------------------------ measurement (CPU)
def measure(name, ds):
    t0 = time.time(); M.check_reference()
    row = next(r for r in plan_rows() if r['dataset'] == ds and name in r['encoders'])
    rec = read(BASE / 'units' / f'{row["id"]}.json')['encoders'][name]; dest = Path(rec['dest'])
    for f, h in rec['files_sha256'].items():
        assert sha(dest / f) == h, f
    info = read(dest / 'meta.json'); defs = PN.defs(ds); desc = PF.load_descriptors(ds)
    didx = {p: i for i, p in enumerate(desc['panel_ids'].tolist())}
    groups = {q['id']: q.get('group') for q in read(PN.DEFS / ds / 'scan.json')['people']}
    from ..paper import ext_common as X
    c = X.Cache(ds); out_dir = MEAS / ds / name; out_dir.mkdir(parents=True, exist_ok=True)
    cells, nulls, calib = [], [], {}
    R = PF.enc_module().refresh(); scope = PF.scope_of(R[name], ds)
    for w in WINDOWS:
        with np.load(dest / f'panels_{w}.npz', allow_pickle=False) as z:
            ids = z['ids'].tolist(); D2 = z['d2']
        pidx = {p: i for i, p in enumerate(ids)}
        for cf, sf in sorted(scope):
            train, test = c.unit_people(sf)
            people = sorted(p for p in train if f'{ds}:{p}:cf{cf}:calib' in pidx)
            if not people:
                continue
            dcal = M.descriptor_calibration(ds, defs, desc, cf, sf, people)
            ecal = M.eeg_calibration({p: D2[pidx[f'{ds}:{p}:cf{cf}:calib']] for p in people}, people, ds, cf, sf, f'{name}:{w}')
            calib[f'{w}:cf{cf}_sf{sf}'] = ecal
            for p in sorted(test):
                panel = f'{ds}:{p}:cf{cf}:test'
                if panel not in pidx:
                    continue
                for dn in M.DESCRIPTORS:
                    base = {'cohort': ds, 'encoder': name, 'support': f'pert_{w}', 'content_fold': cf, 'person_fold': sf,
                            'participant_id': p, 'group': groups.get(p), 'panel_id': panel, 'descriptor': dn, 'condition': 'main',
                            'n_anchors': 128, 'sigma_multiplier': 1.0}
                    if ecal['status'] == 'calibration_degenerate':
                        cells.append({**base, 'status': 'calibration_degenerate'}); continue
                    Y = (desc[dn][didx[panel]].astype(np.float64) - dcal[dn]['mu']) / dcal[dn]['sd']
                    sy = dcal[dn]['cal']['overlap_sigma']; L = DM.gaussian_gram(Y, sy)
                    K = np.ones((128, 128)) if ecal['status'] == 'constant_representation' else M.gram_from_d2(D2[pidx[panel]], ecal['overlap_sigma'])
                    r = DM.measure_from_grams(K, L, M.bank(defs, 'n128', range(4)), null_design=defs['null_design']['n128'])
                    cells.append({**base, 'status': 'completed', 'sigma_u': ecal.get('overlap_sigma'), 'sigma_y': sy,
                                  'null_index': len(nulls), **M.cell_record(r, nulls)})
    with gzip.open(out_dir / 'cells.jsonl.gz', 'wt') as f:
        for cell in cells:
            f.write(json.dumps(cell, allow_nan=False, default=float) + '\n')
    lens = np.array([len(x) for x in nulls], np.int64)
    np.savez(out_dir / 'nulls.npz', flat=np.concatenate(nulls) if nulls else np.zeros(0), offsets=np.r_[0, np.cumsum(lens)].astype(np.int64))
    write(out_dir / 'calibration.json', {'version': 'DEP12_PUB_PERTURB_MEASURE_v1', 'encoder': name, 'dataset': ds, 'feature': info,
                                         'calibration': calib, 'n_cells': len(cells), 'cells_sha256': sha(out_dir / 'cells.jsonl.gz'),
                                         'sources': sources(), 'seconds': time.time() - t0, 'job': os.environ.get('SLURM_JOB_ID')})
    print(name, ds, 'perturbation cells', len(cells), round(time.time() - t0, 1), flush=True)


def measure_all():
    for row in plan_rows():
        if not (BASE / 'units' / f'{row["id"]}.json').exists():
            continue
        for name in row['encoders']:
            p = MEAS / row['dataset'] / name / 'calibration.json'
            if not p.exists():
                measure(name, row['dataset'])


# ------------------------------------------------------------------------------------------------ fleet
def receipts():
    out = {'pass': [], 'other': []}
    if not (BASE / 'plan.json').exists():
        return out
    for path in sorted((BASE / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('plan_sha256') == sha(BASE / 'plan.json') and rec.get('sources') == sources():
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 1, 'slots': 1, 'initial': [], 'submit': []}
    if not (BASE / 'plan.json').exists():
        return st
    remaining = [r for r in plan_rows() if not (BASE / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(remaining)
    if not remaining:
        return {**st, 'state': 'complete'}
    if not any(PF.unit_ready(r) if 'PF' in globals() else unit_ready(r) for r in remaining):
        return {**st, 'state': 'waiting_for_sources'}           # v2: no smoke while every remaining row waits for its encoders
    rec = receipts()
    if not rec['pass']:
        if rec['other']:
            return {**st, 'state': 'engineering_probe_failed'}
        return {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, 'smoke']}
    if any((BASE / 'units' / f'{r["id"]}.FAILED.json').exists() for r in remaining):
        return {**st, 'state': 'failed_unit_review'}
    ready = [r for r in remaining if PF.unit_ready(r)]
    return {**st, 'state': 'ready' if ready else 'waiting_for_sources', 'ready': len(ready), 'slots': 1,
            'submit': [SBATCH, 'worker', '--max-units', '3']}


def worker(max_units):
    import fcntl
    import subprocess
    import sys
    assert receipts()['pass'], 'no passing perturbation smoke'
    count = 0
    for row in plan_rows():
        path = BASE / 'units' / f'{row["id"]}.json'
        if path.exists() or (BASE / 'units' / f'{row["id"]}.FAILED.json').exists() or not PF.unit_ready(row):
            continue
        lock = BASE / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, 'unit', '--id', row['id']]).returncode
            if rc < 0:
                raise SystemExit(rc)
            if rc or not path.exists():
                write(BASE / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError(f'dep12 perturbation unit failed: {row["id"]}')
            count += 1
        if count >= max_units:
            return


def unit_main(uid):
    import torch
    row = next(r for r in plan_rows() if r['id'] == uid)
    res, timing = run_unit(row)
    write(BASE / 'units' / f'{uid}.json', {'status': 'complete', 'row': row, 'plan_sha256': sha(BASE / 'plan.json'), 'encoders': res,
                                           'timing': timing, 'job': os.environ['SLURM_JOB_ID'], 'device': torch.cuda.get_device_name(0),
                                           'sources': sources(), 'time': datetime.now().astimezone().isoformat()})
    print(uid, row['group'], row['dataset'], 'complete', json.dumps(timing), flush=True)


def smoke():
    job = os.environ['SLURM_JOB_ID']
    receipt = {'status': 'running', 'job': job, 'plan_sha256': sha(BASE / 'plan.json'), 'sources': sources(), 'timing': {}}
    try:
        plan = read(BASE / 'plan.json')
        for ds in PN.DATASETS:
            coh = PF.Cohort(ds); people = sorted(coh.test[0])[:1] + sorted(coh.train[0])[:2]; coh.close()
            row = next(r for r in plan['rows'] if r['dataset'] == ds and r['group'] == 'B0')
            res, timing = run_unit(row, probe=True, people_limit=set(people))
            with np.load(Path(res['B0']['dest']) / 'panels_W2.npz') as z:
                assert np.isfinite(z['d2']).all() and z['d2'].shape[1:] == (128, 128)
            receipt['timing'][ds] = timing
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(BASE / 'probes' / job / 'receipt.json', receipt)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=('plan', 'plan-ext', 'plan-ext2', 'plan-ext3', 'smoke', 'worker', 'unit', 'measure-all', 'status'))
    ap.add_argument('--id'); ap.add_argument('--max-units', type=int, default=3)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.step == 'plan':
        make_plan()
    elif a.step == 'plan-ext':
        make_plan_ext()
    elif a.step == 'plan-ext2':
        make_plan_ext2()
    elif a.step == 'plan-ext3':
        make_plan_ext3()
    elif a.step == 'smoke':
        smoke()
    elif a.step == 'worker':
        worker(a.max_units)
    elif a.step == 'unit':
        unit_main(a.id)
    elif a.step == 'measure-all':
        os.umask(0o022); measure_all()
    else:
        print(json.dumps(fleet_status()))


if __name__ == '__main__':
    main()
