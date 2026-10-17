"""Traditional kernel-CS continuation of matched public local NCE sources.

Frozen NCE runners are reused through restored, process-local bindings. Nothing
is patched on disk; each CS result has a new identity, plan and checkpoint store.
"""
from __future__ import annotations
import argparse
import contextlib
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

import numpy as np
import torch
from auditory_alignment import train as T
from . import episode_training as E, breadth_episode as BE
from . import learning_budget as B
from .. import core

BASE = Path(core.OUT)/'aln34/cs_episode_v1'
PLAN = BASE/'plan.json'
NOTE = Path(core.OUT)/'aln34/CS_EPISODE_DESIGN_20261017.md'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln34_cs_episode_v1')
ENGINES = {'dtu': E, 'fau': BE}
PROBE_ROOTS = {'dtu': E.I.BASE/'probes/1044071', 'fau': BE.I.BASE/'probes/1044203'}
LegacyObjective = T.Objective
OriginalBundle = E.D.Bundle
original_tensor_batch = E.tensor_batch


def sources():
    files = {Path(__file__), NOTE, Path(T.__file__)}
    from auditory_alignment import losses, evaluate
    files.update((Path(losses.__file__), Path(evaluate.__file__)))
    for engine in ENGINES.values():
        files.update(Path(core.REPO)/p for p in engine.sources())
    return {str(p.relative_to(core.REPO)): B.sha(p) for p in sorted(files)}


def make_plan():
    rows = []
    for ds, engine in ENGINES.items():
        parent = json.loads(engine.PLAN.read_text()); engine.verify(parent)
        for old in parent['rows']:
            if old['inner']['spec']['architecture'] != 'lag_local_tokens':
                continue
            unit = {**old, 'parent_episode_id': old['id'], 'dataset': ds,
                    'initial_training_objective': 'NCE', 'continuation_objective': 'CS_SINGLE',
                    'design_sha256': B.sha(NOTE)}
            del unit['id']
            unit['id'] = 'ALN34CE_'+hashlib.sha256(B.dumps(unit).encode()).hexdigest()[:16]
            rows.append(unit)
    assert len(rows) == 40
    body = {'version': 'ALN34_CS_EPISODE_v1', 'created': datetime.now().astimezone().isoformat(),
            'rows': rows, 'sources': sources(), 'store': str(STORE),
            'parents': {ds: B.sha(e.PLAN) for ds, e in ENGINES.items()}}
    if PLAN.exists():
        old = json.loads(PLAN.read_text())
        assert all(old[k] == v for k, v in body.items() if k != 'created')
    else:
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
        B.write(PLAN, body); PLAN.chmod(0o444)
    print('Registered40 CS bundles /160 source continuations', B.sha(PLAN), flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'frozen CS continuation source drift'
    assert plan['parents'] == {ds: B.sha(e.PLAN) for ds, e in ENGINES.items()}
    for e in ENGINES.values():
        e.verify(json.loads(e.PLAN.read_text()))


def calibration_anchors(bundle):
    """A deterministic, fit-only set; no target-person or ES/test EEG."""
    rng = np.random.default_rng(bundle.row['seed']+51000)
    fit = [s for s in bundle.segs if s['p'] in bundle.bt.train_p
           and s['kind'] == 'ss' and s['role'] == 'fit']
    if not fit:
        raise ValueError('no source-fit CS calibration segments')
    segments = [fit[i] for i in rng.choice(len(fit), min(32, len(fit)), replace=False)]
    anchors = E.anchors(bundle, segments)
    return [anchors[i] for i in rng.choice(len(anchors), min(256, len(anchors)), replace=False)]


def draw_digest(items):
    return hashlib.sha256(B.dumps([(s['p'], s['uid'], s['e0'], s['s0'], int(t))
                                  for s, t in items]).encode()).hexdigest()


@contextlib.contextmanager
def objective_binding(objective):
    previous = T.Objective
    def factory(job, u0, v0, labels0=None):
        assert job['objective'] == 'NCE' and labels0 is None, 'unexpected inherited objective call'
        return objective
    T.Objective = factory
    try:
        yield
    finally:
        T.Objective = previous


class CSBundle(OriginalBundle):
    def __init__(self, row, record, coh, bt, model, head, grid, local):
        from auditory_alignment import evaluate as V
        assert local and row['spec']['architecture'] == 'lag_local_tokens'
        self.row, self.record, self.coh, self.bt = row, record, coh, bt
        self.model, self.head, self.grid, self.local = model, head, grid, local
        self.reps_of = lambda m: V.Reps(m, head, bt, stride=grid)
        self.reps = self.reps_of(model); self.segs = coh.segments
        self.rng = np.random.default_rng(row['seed']+1000)
        training = [s for s in self.segs if s['p'] in bt.train_p
                    and s['kind'] == 'ss' and s['role'] in ('fit', 'es')]
        self.readout = V.Readouts('CS_SINGLE', self.reps, training, self.rng)
        uid, pool = self.pool('es')
        queries = [s for s in self.segs if s['p'] in bt.train_p and s['kind'] == 'ss' and s['role'] == 'es']
        queries = [queries[i] for i in self.rng.choice(len(queries), min(300, len(queries)), replace=False)]
        vc, ac = self.reps.va([s['s0'] for s in pool]); uq = self.reps.u([s['e0'] for s in queries])
        self.readout.calibrate({m: self.readout.scores(uq, vc, ac, m) for m in ('native', 'unified')},
                               np.array([uid[s['uid']] for s in queries]))
        selected = calibration_anchors(self)
        x, v, _ = original_tensor_batch(self, selected)
        with torch.no_grad():
            u = model(x)
        self.cs_objective = LegacyObjective({'objective': 'CS_SINGLE', 'config': {}}, u, v)
        self.cs_calibration = {**self.cs_objective.record(), 'n_anchors': len(selected),
                               'anchor_sha256': draw_digest(selected),
                               'people': sorted({coh.participants[s['p']]['id'] for s, _ in selected}),
                               'role': 'source-training fit only'}

    def fit_adapter(self, *args, **kwargs):
        with objective_binding(self.cs_objective):
            return super().fit_adapter(*args, **kwargs)


@contextlib.contextmanager
def engine_binding(engine):
    old = {k: getattr(engine, k) for k in ('BASE', 'PLAN', 'STORE', 'continue_source')}
    bundle_class = engine.D.Bundle
    original_continue = engine.continue_source
    write = B.write
    def provisional_write(path, value):
        if isinstance(value, dict) and value.get('status') == 'complete' and 'stages' in value:
            value = {**value, 'status': 'awaiting_pair_audit'}
        write(path, value)
    B.write = provisional_write
    engine.BASE, engine.PLAN, engine.STORE = BASE, PLAN, STORE
    engine.D.Bundle = CSBundle

    def continuation(bundle, regime, dest, initial, updates, probe=False):
        contract = {'objective': 'CS_SINGLE', 'source_sha256': B.sha(__file__),
                    'plan_sha256': B.sha(PLAN), 'calibration': bundle.cs_calibration}
        stream = []
        for path in (dest/f'{regime}.pt', dest/f'{regime}_resume.pt'):
            if path.exists():
                state = torch.load(path, map_location='cpu', weights_only=False)
                assert state['cs_contract'] == contract, 'CS checkpoint contract drift'
                stream = list(state['ledger']['query_draw_sha256'])
                break
        atomic, tensor = engine.atomic_torch, engine.tensor_batch
        def save(path, value):
            value['cs_contract'] = contract
            value['ledger'].update(objective='CS_SINGLE', cs_calibration=bundle.cs_calibration,
                                   query_draw_sha256=list(stream))
            assert len(stream) == value['ledger']['encoder_updates']
            atomic(path, value)
        def batch(b, items):
            stream.append(draw_digest(items)); return tensor(b, items)
        engine.atomic_torch, engine.tensor_batch = save, batch
        try:
            with objective_binding(bundle.cs_objective):
                return original_continue(bundle, regime, dest, initial, updates, probe)
        finally:
            engine.atomic_torch, engine.tensor_batch = atomic, tensor
    engine.continue_source = continuation
    try:
        yield
    finally:
        engine.D.Bundle = bundle_class
        B.write = write
        for key, value in old.items():
            setattr(engine, key, value)


def ready(unit, probe_root=None):
    return ENGINES[unit['dataset']].ready(unit, probe_root)


def run_unit(unit, probe_root=None):
    engine = ENGINES[unit['dataset']]
    with engine_binding(engine):
        engine.run_unit(unit, probe_root)
    target = BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe_root else BASE/'units'
    path = target/f'{unit["id"]}.json'; record = json.loads(path.read_text())
    for stage in record['stages'].values():
        ordinary, episode = (stage['training'][r] for r in E.REGIMES)
        for key in ('query_draw_sha256', 'support_steps', 'query_anchors', 'support_eligible_anchors',
                    'source_ids', 'encoder_updates', 'cs_calibration'):
            assert ordinary[key] == episode[key], 'unmatched CS regimes: '+key
    record.update(status='complete', continuation_objective='CS_SINGLE', initial_training_objective='NCE',
                  native_readout='source-training ridge to fixed audio features; squared distance; source ES temperature',
                  source_sha256=B.sha(__file__), selection_level='whole pipeline: one held-out inner-person split',
                  limitations=['100-update CS continuation of NCE sources, not from-scratch CS training',
                               'NCE parent native readout differs; use unified readout for cross-objective comparison',
                               'historical noncausal input filtering retained'])
    B.write(path, record)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--register', action='store_true'); ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--smoke-job'); ap.add_argument('--unit'); ap.add_argument('--probe-root', type=Path)
    ap.add_argument('--max-units', type=int, default=2)
    args = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if args.register:
        make_plan(); return
    plan = json.loads(PLAN.read_text()); verify(plan)
    if args.unit:
        run_unit(next(u for u in plan['rows'] if u['id'] == args.unit), args.probe_root); return
    if args.smoke:
        receipt = {'status': 'running', 'plan_sha256': B.sha(PLAN), 'units': []}
        try:
            for ds in ENGINES:
                root = PROBE_ROOTS[ds]
                r = json.loads((root/'receipt.json').read_text()); assert r['status'] == 'pass'
                unit = next(u for u in plan['rows'] if u['dataset'] == ds and ready(u, root))
                run_unit(unit, root); receipt['units'].append(unit['id'])
            receipt['status'] = 'pass'
        except BaseException:
            receipt.update(status='failed', traceback=traceback.format_exc()); raise
        finally:
            B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json', receipt)
        return
    receipt = json.loads((BASE/'probes'/str(args.smoke_job)/'receipt.json').read_text())
    assert receipt['status'] == 'pass' and receipt['plan_sha256'] == B.sha(PLAN)
    completed = 0
    for unit in plan['rows']:
        if completed >= args.max_units:
            break
        if not ready(unit) or (BASE/'units'/f'{unit["id"]}.json').exists():
            continue
        lock = BASE/'claims'/f'{unit["id"]}.lock'; lock.parent.mkdir(exist_ok=True)
        with lock.open('a+') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if (BASE/'units'/f'{unit["id"]}.json').exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-m', 'auditory_alignment_v3.aln34.cs_episode',
                                 '--unit', unit['id']]).returncode
            if rc:
                B.write(BASE/'units'/f'{unit["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('CS episode unit failed')
            completed += 1


if __name__ == '__main__':
    main()
