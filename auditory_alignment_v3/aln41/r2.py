"""ALN4.1 R2 seed replication runner: seeds 3407 / 3413 of the four source productions (8 fits), the core-3 x 5 private CE
fits (30) and the non-B0 frozen endpoints, on the unchanged R1 modules.

Package closure.json R2: LR is not re-selected (production LR = the R1 selection.json choice), no arm is dropped. For one
seed the R1 modules source / private_ft / frozen are re-pointed before use (`seeded`): SEED, the derived episode stream
seed (seed + 41000, R1 3401 + 41000) and the output / store roots. Everything else is the R1 definition: pool, eligible
people, source panels (seed 3420, byte-copied and hash-checked), inner settings, sigma rule, optimiser, snapshots, private
recipe, PCA. Sigmas are re-fixed at each seed's initial state with the R1 rule (the projection heads are seeded). B0
frozen units do not depend on the seed (generic CBraMod, PCA seed 3437), so R2 reuses the R1 B0 frozen units.
Every unit runs in its own process: `python -m auditory_alignment_v3.aln41.r2 <source|private|frozen> --seed S ...`.
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

import numpy as np

from . import source as SRC, private_ft as PF, frozen as FZ

SEEDS = (3407, 3413)
R1_SOURCE = SRC.OUT / 'source_v1'
R1_STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln41')
ROOT = SRC.OUT / 'r2'
STORE_ROOT = R1_STORE / 'r2'
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest


@contextlib.contextmanager
def seeded(seed):
    """Re-point the R1 modules to one R2 seed; restores the previous values on exit (the fleet process is shared)."""
    assert seed in SEEDS
    saved = [(m, k, getattr(m, k)) for m, keys in ((SRC, ('SEED', 'STREAM_SEED', 'BASE', 'STORE')), (PF, ('BASE', 'STORE')),
                                                     (FZ, ('BASE', 'STORE', 'ARMS'))) for k in keys]
    try:
        SRC.SEED, SRC.STREAM_SEED = seed, seed + 41000
        SRC.BASE, SRC.STORE = ROOT / f'seed{seed}' / 'source_v1', STORE_ROOT / f'seed{seed}' / 'source_v1'
        PF.BASE, PF.STORE = ROOT / f'seed{seed}' / 'private_ft_v1', STORE_ROOT / f'seed{seed}' / 'private_ft_v1'
        FZ.BASE, FZ.STORE = ROOT / f'seed{seed}' / 'frozen_v1', STORE_ROOT / f'seed{seed}' / 'frozen_v1'
        FZ.ARMS = tuple(a for a in FZ.ARMS if a != 'B0')
        yield
    finally:
        for m, k, v in saved:
            setattr(m, k, v)


def r2_sources():
    return {'auditory_alignment_v3/aln41/r2.py': sha(Path(__file__))}


# ----------------------------------------------------------------------------------------------- plans (CPU, once per seed)
def make_plans(seed):
    r1 = read(R1_SOURCE / 'plan.json'); sel1 = read(R1_SOURCE / 'selection.json')
    with seeded(seed):
        man = SRC.open_manifest(); split_pool, pool_info = SRC.pool(man); people, excluded = SRC.eligible_people(split_pool['fit'])
        assert pool_info == r1['pool'] and len(people) == r1['eligible_people'] and excluded == r1['excluded_people']
        SRC.STORE.mkdir(parents=True, exist_ok=True, mode=0o700); SRC.BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not (SRC.STORE / 'stream.npz').exists():
            stream = SRC.make_stream(split_pool['fit'], people, SRC.PROD_STEPS, seed=SRC.STREAM_SEED)   # default arg is bound to R1
            SRC.check_stream(man, stream)
            np.savez_compressed(SRC.STORE / 'stream.npz', **stream)
        if not (SRC.STORE / 'panels.npz').exists():
            shutil.copyfile(Path(r1['store']) / 'panels.npz', SRC.STORE / 'panels.npz')
        assert sha(SRC.STORE / 'panels.npz') == r1['panels_sha256']
        rows = []
        for arm in SRC.ARMS:
            body = {'stage': 'production', 'arm': arm, 'lr': sel1['choice'][arm]['lr'], 'updates': SRC.PROD_STEPS, 'seed': seed}
            rows.append({**body, 'id': 'ALN41P_' + digest(body, 16)})
        keep = ('package_zip_sha256', 'manifest_sha256', 'rich_sha256', 'stage1', 'stage1_gate_sha256', 'pool', 'eligible_people',
                'excluded_people', 'panel_seed', 'inner', 'optimizer', 'production_updates', 'production_snapshots', 'arms', 'views')
        body = {'version': 'ALN41_SOURCE_R2_v1', 'seed': seed, 'rows': [], 'production_rows': rows, 'sources': SRC.sources(),
                'r2_sources': r2_sources(), 'store': str(SRC.STORE), **{k: r1[k] for k in keep},
                'stream_seed': SRC.STREAM_SEED, 'stream_sha256': sha(SRC.STORE / 'stream.npz'), 'panels_sha256': r1['panels_sha256'],
                'r1_plan_sha256': sha(R1_SOURCE / 'plan.json'), 'r1_selection_sha256': sha(R1_SOURCE / 'selection.json'),
                'lr_rule': 'R1 selection.json choice, not re-selected (package closure.json R2: retune_on_R1_test false)'}
        plan = SRC.BASE / 'plan.json'
        if plan.exists():
            old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
        else:
            write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
        sel = {'version': 'ALN41_SOURCE_SELECTION_R2_v1', 'plan_sha256': sha(plan),
               'choice': {arm: {'lr': sel1['choice'][arm]['lr'], 'status': 'inherited_R1_selection'} for arm in SRC.ARMS},
               'production_rows': rows, 'r1_selection_sha256': sha(R1_SOURCE / 'selection.json')}
        path = SRC.BASE / 'selection.json'
        if path.exists():
            old = read(path); assert old['choice'] == sel['choice'] and old['production_rows'] == rows
        else:
            write(path, {**sel, 'created': datetime.now().astimezone().isoformat()}); path.chmod(0o444)
        PF.make_plan(); FZ.make_plan()
        assert len(read(PF.BASE / 'plan.json')['rows']) == 15 and len(read(FZ.BASE / 'plan.json')['rows']) == 20
        print('ALN41 R2 seed', seed, 'source', sha(plan), 'stream', body['stream_sha256'][:12], flush=True)


def verify_source(plan):
    SRC.verify(plan); assert plan['r2_sources'] == r2_sources(), 'r2 runner drift'


# ----------------------------------------------------------------------------------------------- workers (GPU)
def unit_cmd(stage, seed, *args):
    return [sys.executable, '-B', '-u', '-m', __spec__.name, stage, '--seed', str(seed), *args]


def claim_and_run(stage, seed, base, row):
    """flock claim + one unit subprocess; FAILED marker on error. Returns True when the unit ran."""
    path = base / 'units' / f'{row["id"]}.json'
    lock = base / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if path.exists():
            return False
        rc = subprocess.run(unit_cmd(stage, seed, '--unit', row['id'])).returncode
        if rc or not path.exists():
            write(base / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc, 'seed': seed})
            raise RuntimeError(f'aln41 R2 {stage} unit failed')
    return True


def source_smoke(seed):
    import torch
    plan = read(SRC.BASE / 'plan.json'); verify_source(plan); _, rows = SRC.all_rows()
    job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': sha(SRC.BASE / 'plan.json'), 'seed': seed, 'units': []}
    try:
        receipt['sigmas'] = SRC.fix_sigmas(plan, torch.device('cuda'))['sigmas']
        receipt['readiness'] = SRC.readiness(plan)
        for arm in ('TCS', 'TNCE', 'GCS'):
            row = next(r for r in rows if r['arm'] == arm)
            assert subprocess.run(unit_cmd('source', seed, '--probe-unit', row['id'])).returncode == 0, arm
            rec = read(SRC.BASE / 'probes' / job / 'units' / f'{row["id"]}.json')
            receipt['units'].append({'id': row['id'], 'arm': arm, 'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb'],
                                     'losses': [x['loss'] for x in rec['log']], 'probe': rec['selection_probe']})
        wrong = next(r for r in rows if r['arm'] == 'TCS_WRONG')
        assert subprocess.run(unit_cmd('source', seed, '--probe-unit', wrong['id'])).returncode == 0, 'TCS_WRONG'
        rec = read(SRC.BASE / 'probes' / job / 'units' / f'{wrong["id"]}.json')
        receipt['units'].append({'id': wrong['id'], 'arm': 'TCS_WRONG', 'losses': [x['loss'] for x in rec['log']]})
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(SRC.BASE / 'probes' / job / 'receipt.json', receipt)


def private_smoke(seed):
    plan = read(PF.BASE / 'plan.json'); PF.verify(plan)
    job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': sha(PF.BASE / 'plan.json'), 'seed': seed, 'units': []}
    try:
        row = next(r for r in plan['rows'] if r['arm'] == 'B0' and r['outer_fold'] == 0)
        assert subprocess.run(unit_cmd('private', seed, '--probe-unit', row['id'])).returncode == 0
        rec = read(PF.BASE / 'probes' / job / 'units' / f'{row["id"]}.json')
        assert rec['label_access']['test_children'] in (12, 13) and len(rec['curve']) == 2
        receipt['units'].append({'id': row['id'], 'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb'], 'curve': rec['curve']})
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(PF.BASE / 'probes' / job / 'receipt.json', receipt)


def frozen_smoke(seed):
    plan = read(FZ.BASE / 'plan.json'); FZ.verify(plan)
    job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': sha(FZ.BASE / 'plan.json'), 'seed': seed, 'units': []}
    try:
        for ds, cf in (('fau', 0), ('private_bdf', None)):
            row = next(r for r in plan['rows'] if r['arm'] == 'TCS' and r['dataset'] == ds and r['content_fold'] == cf)
            rec = FZ.run_unit(row, plan, probe=True)
            with np.load(Path(rec['dest']) / 'arrays.npz') as z:
                key = 'pca_sf0' if ds == 'fau' else 'pca_f0'
                assert np.isfinite(z[key]).all() and z[key].shape[1:] == (3, z[key].shape[2])
            receipt['units'].append({'dataset': ds, 'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb']})
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(FZ.BASE / 'probes' / job / 'receipt.json', receipt)


def stage_rows(stage, arm=None):
    """(module, base, rows, ready(row)) of the currently seeded stage."""
    if stage == 'source':
        _, rows = SRC.all_rows(); return SRC, SRC.BASE, rows, lambda r: True
    if stage == 'private':
        rows = [r for r in read(PF.BASE / 'plan.json')['rows'] if arm is None or r['arm'] == arm]; return PF, PF.BASE, rows, PF.ready
    return FZ, FZ.BASE, read(FZ.BASE / 'plan.json')['rows'], FZ.ready


def worker(stage, seeds, arm, max_units):
    """Claim up to max_units ready units over the seeds (in order) whose own smoke receipt passed."""
    count = 0
    for seed in seeds:
        with seeded(seed):
            M, base, rows, ready = stage_rows(stage, arm)
            plan = read(base / 'plan.json')
            if stage == 'source':
                verify_source(plan)
            else:
                M.verify(plan)
            if not M.receipts()['pass']:
                continue
            for row in rows:
                if (base / 'units' / f'{row["id"]}.json').exists() or (base / 'units' / f'{row["id"]}.FAILED.json').exists() or not ready(row):
                    continue
                count += claim_and_run(stage, seed, base, row)
                if count >= max_units:
                    return


def run_one(stage, seed, unit, probe):
    with seeded(seed):
        if stage == 'source':
            plan = read(SRC.BASE / 'plan.json'); verify_source(plan); _, rows = SRC.all_rows()
            SRC.run_unit(next(r for r in rows if r['id'] == unit), plan, probe=probe)
        elif stage == 'private':
            plan = read(PF.BASE / 'plan.json'); PF.verify(plan)
            PF.run_unit(next(r for r in plan['rows'] if r['id'] == unit), plan, probe=probe)
        else:
            plan = read(FZ.BASE / 'plan.json'); FZ.verify(plan)
            FZ.run_unit(next(r for r in plan['rows'] if r['id'] == unit), plan)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('stage', choices=('plans', 'source', 'private', 'frozen'))
    ap.add_argument('--seed', type=int); ap.add_argument('--smoke', action='store_true'); ap.add_argument('--worker', action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--probe-unit'); ap.add_argument('--arm', choices=PF.ARMS)
    ap.add_argument('--max-units', type=int)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.stage == 'plans':
        for seed in ([a.seed] if a.seed else SEEDS):
            make_plans(seed)
        return
    if a.unit or a.probe_unit:
        run_one(a.stage, a.seed, a.unit or a.probe_unit, bool(a.probe_unit)); return
    if a.smoke:
        with seeded(a.seed):
            {'source': source_smoke, 'private': private_smoke, 'frozen': frozen_smoke}[a.stage](a.seed)
        return
    assert a.worker
    worker(a.stage, SEEDS, a.arm, a.max_units or {'source': 1, 'private': 1, 'frozen': 3}[a.stage])


if __name__ == '__main__':
    main()
