"""ALN3.6 R2 (package ALN3.7): fixed seed-3407 replication of the R1 core on the unchanged R1 modules.

docs/05 R2, fixed before R1 results: FAU three groups x two tools x two content folds with seed 3407 (12 unique source fits,
60 evaluation cells; every group repeated whatever its R1 sign); DTU / FAU pooled readouts reuse the existing seed-3407 pooled
weights (only the same readout is redone); the children's matched AP / APwrong pair with seed 3407 (aln36/r2_apwrong.py). All
R1 definitions stay unchanged: bindings (source people, population scaler, risk anchor sets), support rules, history, time
bank, lambda and statistics families. The R1 bindings are reused byte-identically; their risk calibration draw used seed 3401,
so only the training seed differs from R1.
`seeded()` re-points the R1 modules for one process: common.SEED, the FAU group parents and the output / store roots. The
group parents are the seed-3407 pooled person-fold-0 units with the R1 parents' exact spec, so the recipe is identical. Pooled
public parents: DTU comes from content_time_v1 (seed 3407 rows). FAU seed-3407 rows are not in that plan, so each R1 FAU pooled
row is matched to the unique completed seed-3407 unit with the identical spec, person fold and content fold.
Usage: `python -m auditory_alignment_v3.aln36.r2 <plans|group|features|private|public_readout|private_readout|analysis> ...`.
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

import numpy as np

from .. import core
from ..aln34 import content_time as CT
from . import common as C, fau_group as G, public_features as F, private_features as PFE
from . import public_readout as R, private_readout as PR, analysis as A
from . import r2_apwrong as RW

SEED = 3407
ROOT = C.OUT / 'r2_s3407'
STORE = C.STORE / 'r2_s3407'
RESULTS = C.REPO / 'results/auditory_alignment_v3/aln36/r2'
PARENTS = {('local_L1', 0): 'ALN3X_da6696d66809ebb3', ('local_L1', 1): 'ALN3X_b4998069d1d024dd',
           ('CBpre_true_full', 0): 'ALN3X_fa8605dc2a60565a', ('CBpre_true_full', 1): 'ALN3X_792874d043389f51'}


_R1_PACKAGE_BINDING = C.package_binding


def package_binding():
    """The package's round1.json carries seed 3401: byte-check the package under that seed, then return to R2."""
    current, C.SEED = C.SEED, 3401
    try:
        return _R1_PACKAGE_BINDING()
    finally:
        C.SEED = current


@contextlib.contextmanager
def seeded():
    patch = [(C, 'SEED', SEED), (C, 'package_binding', package_binding), (G, 'PARENTS', PARENTS),
             (G, 'BASE', ROOT / 'fau_group_v1'), (G, 'PLAN', ROOT / 'fau_group_v1' / 'plan.json'), (G, 'STORE', STORE / 'fau_group_v1'),
             (F, 'BASE', ROOT / 'public_features_v1'), (F, 'PLAN', ROOT / 'public_features_v1' / 'plan.json'),
             (F, 'STORE', STORE / 'public_features_v1'),
             (PFE, 'BASE', ROOT / 'private_features_v1'), (PFE, 'PLAN', ROOT / 'private_features_v1' / 'plan.json'),
             (PFE, 'STORE', STORE / 'private_features_v1'), (PFE, 'APW', RW.OUT), (PFE, 'APW_STORE', RW.STORAGE / 'production' / 'targets'),
             (R, 'BASE', ROOT / 'public_readout_v1'), (PR, 'BASE', ROOT / 'private_readout_v1'),
             (A, 'BASE', ROOT / 'analysis'), (A, 'RESULTS', RESULTS)]
    saved = [(m, k, getattr(m, k)) for m, k, _ in patch]
    try:
        for m, k, v in patch:
            setattr(m, k, v)
        yield
    finally:
        for m, k, v in saved:
            setattr(m, k, v)


def r2_sources():
    return {'auditory_alignment_v3/aln36/r2.py': C.sha(Path(__file__))}


# ----------------------------------------------------------------------------------------------- plans (CPU)
def unit_rows():
    out = {}
    for p in (Path(core.OUT) / 'units').glob('ALN3X_*.json'):
        if p.name.endswith('.FAILED.json'):
            continue
        rec = C.read(p); row = rec.get('row', {})
        if row.get('dataset') == 'fau' and row.get('seed') == SEED and rec.get('status') == 'complete':
            out[row['experiment_id']] = row
    return out


def same_spec(a, b):
    strip = lambda r: {k: v for k, v in r['spec'].items() if k not in ('seed', 'target_seed', 'sampler_seed', 'donor_seed')}
    return strip(a) == strip(b) and a.get('family_id') == b.get('family_id') and a.get('content_fold') == b.get('content_fold')


def check_parents(units):
    for (tool, cf), eid in PARENTS.items():
        r1 = C.read(Path(core.OUT) / 'units' / f'{G.PARENTS[(tool, cf)]}.json')['row']
        assert same_spec(units[eid], r1) and units[eid]['subject_fold'] == r1['subject_fold'], (tool, cf)


def feature_plan():
    """R1 public_features.make_plan with the seed-3407 pooled parents (40) and the R2 group units (12)."""
    units = unit_rows(); rows = []
    ct = C.read(CT.PLAN)
    for u in ct['rows']:
        r = u['source']
        if r['dataset'] not in ('dtu', 'fau') or CT.label(r) not in ('local', 'cbramod_pretrained_full'):
            continue
        if r['dataset'] == 'dtu' and r['seed'] == SEED:
            eid, rec_sha, ck_sha = r['experiment_id'], u['record_sha256'], u['checkpoint_sha256']
            src = r
        elif r['dataset'] == 'fau' and r['seed'] == 3401:
            match = [k for k, x in units.items() if same_spec(x, r) and x['subject_fold'] == r['subject_fold']]
            assert len(match) == 1, r['experiment_id']
            eid = match[0]; src = units[eid]
            rec_sha = C.sha(Path(core.OUT) / 'units' / f'{eid}.json'); ck_sha = C.sha(Path(core.OUT) / 'ckpt' / f'{eid}_best.pt')
        else:
            continue
        assert C.sha(Path(core.OUT) / 'units' / f'{eid}.json') == rec_sha and C.sha(Path(core.OUT) / 'ckpt' / f'{eid}_best.pt') == ck_sha
        body = {'kind': 'pooled_parent', 'dataset': src['dataset'], 'tool': F.tool_of(src), 'seed': src['seed'],
                'person_fold': src['subject_fold'], 'content_fold': src['content_fold'], 'source_id': eid,
                'source_record_sha256': rec_sha, 'source_checkpoint_sha256': ck_sha,
                'preprocessing': 'inherited per-person z-score over all loaded ss+cs trials (auditory_alignment.data._stdz)'}
        rows.append({**body, 'id': 'ALN36F_' + C.digest(body)})
    assert len(rows) == 40 and all(r['seed'] == SEED for r in rows)
    gp = C.read(G.PLAN)
    for r in gp['rows']:
        body = {'kind': 'whole_group', 'dataset': 'fau', 'tool': r['tool'], 'seed': r['seed'], 'excluded_group': r['excluded_group'],
                'content_fold': r['content_fold'], 'source_id': r['experiment_id'], 'group_plan_sha256': C.sha(G.PLAN),
                'binding': r['binding'], 'binding_sha256': r['binding_sha256'],
                'preprocessing': 'stageB without per-person z-score; frozen population source-fit channel scaler'}
        rows.append({**body, 'id': 'ALN36F_' + C.digest(body)})
    assert len(rows) == 52 and len({r['id'] for r in rows}) == 52
    r1 = C.read(C.OUT / 'public_features_v1' / 'plan.json')
    body = {'version': 'ALN36_PUBLIC_FEATURES_R2_v1', 'seed': SEED, 'rows': rows, 'sources': F.sources(), 'r2_sources': r2_sources(),
            'store': str(F.STORE), **{k: r1[k] for k in ('centers_ms', 'window_relative_to_center_ms', 'joint_access_ms', 'anchor_seconds',
                                                         'history_lags_ms')}, 'r1_plan_sha256': C.sha(C.OUT / 'public_features_v1' / 'plan.json')}
    if F.PLAN.exists():
        old = C.read(F.PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        F.STORE.mkdir(parents=True, exist_ok=True, mode=0o700); F.PLAN.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        C.write(F.PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); F.PLAN.chmod(0o444)
    print('ALN36 R2 public feature plan', len(rows), C.sha(F.PLAN), flush=True)


def private_plan():
    """R1 private_features.make_plan on the R2 matched pair (10 targets); optional S only from compatible seed-3407 caches."""
    from ..aln34 import prior_science as PS
    apw = C.read(PFE.APW / 'plan.json'); rows = []
    for u in apw['units']:
        if u['stage'] != 'target':
            continue
        rec_path = PFE.APW / 'units' / f'{u["unit_id"]}.json'; rec = C.read(rec_path)
        assert rec['status'] == 'complete' and rec['seed'] == SEED and rec['arm'] in ('AP', 'APwrong')
        ck = PFE.APW_STORE / rec['checkpoints']['best']['file']; assert C.sha(ck) == rec['checkpoints']['best']['sha256']
        body = {'kind': 'matched_target', 'arm': rec['arm'], 'person_fold': rec['subject_fold'], 'seed': rec['seed'],
                'source_id': u['unit_id'], 'source_record_sha256': C.sha(rec_path), 'checkpoint': str(ck),
                'checkpoint_sha256': rec['checkpoints']['best']['sha256'], 'checkpoint_rule': rec['selection']['primary']['rule'],
                'donor_unit': rec['donor_unit'], 'view_sha256': rec['view']['view_sha256'], 'pool_sha256': rec['view']['pool_sha256']}
        rows.append({**body, 'id': 'ALN36P_' + C.digest(body)})
    assert len(rows) == 10 and {(r['arm'], r['person_fold']) for r in rows} == {(a, f) for a in ('AP', 'APwrong') for f in C.PERSON_FOLDS}
    optional = []
    for u in C.read(PS.PLAN)['rows']:
        r = u['source']; meta = PS.STORE / 'cache' / u['id'] / 'meta.json'
        if r['dataset'] != 'private_bdf' or u['config'] != ['S', 'NCE'] or r['seed'] != SEED or not meta.exists():
            continue
        m = C.read(meta)
        body = {'kind': 'existing_S_cache', 'arm': 'S', 'person_fold': r['subject_fold'], 'seed': r['seed'], 'source_id': r['experiment_id'],
                'prior_science_unit': u['id'], 'cache_meta_sha256': C.sha(meta), 'array_sha256': m['array_sha256']}
        optional.append({**body, 'id': 'ALN36P_' + C.digest(body)})
    rows.sort(key=lambda r: (r['person_fold'], r['arm'])); optional.sort(key=lambda r: r['person_fold'])
    body = {'version': 'ALN36_PRIVATE_FEATURES_R2_v1', 'seed': SEED, 'rows': rows, 'optional_S': optional, 'sources': PFE.sources(),
            'r2_sources': r2_sources(), 'store': str(PFE.STORE), 'windows_ms': {k: v for k, v in PFE.WINDOWS.items()},
            'apwrong_plan_sha256': C.sha(PFE.APW / 'plan.json')}
    if PFE.PLAN.exists():
        old = C.read(PFE.PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        PFE.STORE.mkdir(parents=True, exist_ok=True, mode=0o700); PFE.PLAN.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        C.write(PFE.PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); PFE.PLAN.chmod(0o444)
    print('ALN36 R2 private feature plan', len(rows), 'core,', len(optional), 'optional S', C.sha(PFE.PLAN), flush=True)


def make_plans(which):
    with seeded():
        if 'group' in which:
            check_parents(unit_rows())
            G.PLAN.parent.mkdir(parents=True, exist_ok=True, mode=0o700); G.make_plan()
            plan = C.read(G.PLAN); assert all(r['seed'] == SEED for r in plan['rows']) and len(plan['rows']) == 12
        if 'features' in which:
            feature_plan()
        if 'private' in which:
            private_plan()


# ----------------------------------------------------------------------------------------------- GPU workers
def cmd(stage, *args):
    return [sys.executable, '-B', '-u', '-m', __spec__.name, stage, *args]


def verify_plan(stage):
    if stage == 'group':
        G.verify(C.read(G.PLAN))
    else:
        plan = C.read(F.PLAN); F.verify(plan); assert plan['r2_sources'] == r2_sources(), 'r2 runner drift'


def receipts(stage):
    return G.receipts() if stage == 'group' else F.receipts()


def smoke(stage):
    base, plan_path = (G.BASE, G.PLAN) if stage == 'group' else (F.BASE, F.PLAN)
    verify_plan(stage); plan = C.read(plan_path)
    job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': C.sha(plan_path), 'seed': SEED, 'units': []}
    try:
        if stage == 'group':
            for tool in C.TOOLS:
                row = next(r for r in plan['rows'] if r['tool'] == tool and r['excluded_group'] == 'th' and r['content_fold'] == 0)
                assert subprocess.run(cmd('group', '--probe-unit', row['experiment_id'])).returncode == 0, tool
                rec = C.read(base / 'probes' / job / 'units' / f'{row["experiment_id"]}.json')
                assert rec['truncated'] and rec['probe'] and not rec['source_exclusion']['th_dev_in_source']
                assert rec['source_exclusion']['source_groups'] == ['ci', 'ha'] and rec['bound_row']['seed'] == SEED
                receipt['units'].append({'id': row['experiment_id'], 'tool': tool, 'peak_mb': rec['gpu_peak_allocated_mb'],
                                         'seconds': rec['total_seconds'], 'optimizer_steps': rec['optimizer_steps']})
        else:
            picks = [next(r for r in plan['rows'] if r['kind'] == 'pooled_parent' and r['dataset'] == ds and r['tool'] == tool)
                     for ds in ('dtu', 'fau') for tool in C.TOOLS]
            for r in picks:
                assert subprocess.run(cmd('features', '--probe-unit', r['id'])).returncode == 0, r['id']
                meta = C.read(F.STORE / 'probes' / job / r['id'] / 'meta.json')
                with np.load(F.STORE / 'probes' / job / r['id'] / 'arrays.npz') as z:
                    assert all(np.isfinite(z[f'model_{c}']).all() for c in F.CENTERS) and np.isfinite(z['env_history']).all()
                    assert set(z['side'].tolist()) == {'source', 'target'}
                receipt['units'].append({'id': r['id'], 'seconds': meta['seconds'], 'peak_mb': meta['gpu_peak_mb']})
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        C.write(base / 'probes' / job / 'receipt.json', receipt)


def worker(stage, tool, max_units):
    base, plan_path = (G.BASE, G.PLAN) if stage == 'group' else (F.BASE, F.PLAN)
    verify_plan(stage); plan = C.read(plan_path)
    assert receipts(stage)['pass'], 'no passing smoke receipt for this plan'
    key = 'experiment_id' if stage == 'group' else 'id'
    count = 0
    for row in plan['rows']:
        if tool and row['tool'] != tool:
            continue
        uid = row[key]; path = base / 'units' / f'{uid}.json'
        if path.exists() or (base / 'units' / f'{uid}.FAILED.json').exists() or (stage == 'features' and not F.ready(row)):
            continue
        lock = base / 'claims' / f'{uid}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run(cmd(stage, '--unit', uid)).returncode
            if rc or not path.exists():
                C.write(base / 'units' / f'{uid}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError(f'aln36 R2 {stage} unit failed')
            count += 1
        if count >= max_units:
            break


def run_one(stage, uid, probe):
    verify_plan(stage)
    if stage == 'group':
        plan = C.read(G.PLAN); G.run_unit(next(r for r in plan['rows'] if r['experiment_id'] == uid), plan, probe=probe)
    else:
        plan = C.read(F.PLAN); F.extract(next(r for r in plan['rows'] if r['id'] == uid), probe=probe)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=('plans', 'group', 'features', 'private', 'public_readout', 'private_readout', 'analysis'))
    ap.add_argument('--which', default='group,features'); ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--worker', action='store_true'); ap.add_argument('--unit'); ap.add_argument('--probe-unit')
    ap.add_argument('--tool', choices=C.TOOLS); ap.add_argument('--max-units', type=int)
    a, rest = ap.parse_known_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.stage == 'plans':
        make_plans(a.which.split(',')); return
    with seeded():
        if a.stage in ('private', 'public_readout', 'private_readout', 'analysis'):
            # R1 mains whose loops run in-process (no self-subprocess): they read the re-pointed globals directly.
            if a.stage == 'private':
                plan = C.read(PFE.PLAN); assert plan['r2_sources'] == r2_sources(), 'r2 runner drift'
            module = {'private': PFE, 'public_readout': R, 'private_readout': PR, 'analysis': A}[a.stage]
            sys.argv = [module.__name__, *rest]
            module.main(); return
        if a.unit or a.probe_unit:
            run_one(a.stage, a.unit or a.probe_unit, bool(a.probe_unit)); return
        if a.smoke:
            smoke(a.stage); return
        assert a.worker
        worker(a.stage, a.tool, a.max_units or {'group': 1, 'features': 8}[a.stage])


if __name__ == '__main__':
    main()
