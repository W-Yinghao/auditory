"""ALN4.1 R1 frozen age readout (CPU): core arms B0/TCS/TNCE, a raw-EEG log-variance ridge and the train mean.

Children: the 64 private children, one primary record each; age in months from data.load_private (children with a
missing age are listed and excluded before any model is run). Features: per child the trial mean and std (ddof 0) of
each slot's raw frozen token vector (frozen_v1 private units), slot/statistic/channel order fixed; one shared source
encoder per arm. Raw baseline: per child the trial mean of log(variance over the 200 real samples + 1e-12) per channel,
read from the GX staged epochs before the per-child z-score of hc.load_children (accepted, history-valid trials;
amplitudes in the stored GX epoch unit). Model: age_probe.run_probe (package reference, byte-identical): 5 outer folds
(seed-20261005 child folds), 4 inner folds (seed 3431), alpha in {.01,.1,1,10,100} x trace/n by inner MAE.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from .. import core
from . import age_probe as AP
from . import frozen as FZ
from . import source as SRC

BASE = SRC.OUT / 'age_v1'
read, write, sha = SRC.read, SRC.write, SRC.sha
ARMS = ('B0', 'TCS', 'TNCE')


def raw_logvar(kids):
    from auditory_c3.private_mi2 import hist_codes
    out = []
    for k in kids:
        path = Path(core.REPO) / 'private/auditory_gx/GX_stage_001/epochs' / f'{k["rid"]}.npz'
        with np.load(path, allow_pickle=False) as z:
            acc = z['accepted'].astype(bool)
            h = hist_codes(z['previous_code'][acc], z['previous_run_length'][acc])['since_last_deviant']
            valid = h >= 0
            assert np.array_equal(z['y'][acc][valid], k['y']) and np.array_equal(z['block_id'][acc][valid], k['block'])
            x = z['x'][acc][valid].astype(np.float64)
        assert x.shape[1:] == (20, 200)
        out.append(np.log(x.var(axis=2) + 1e-12).mean(0))
    return np.stack(out)


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    from auditory_alignment import data
    kids = data.load_private()
    ids = np.array([k['id'] for k in kids]); folds = np.array([str(k['fold']) for k in kids])
    age = np.array([np.nan if k.get('age_months') is None else float(k['age_months']) for k in kids])
    roster = {'n_children': len(kids), 'age_available': int(np.isfinite(age).sum()),
              'missing_age_ids': ids[~np.isfinite(age)].tolist(), 'fold_sizes': {f: int((folds == f).sum()) for f in sorted(set(folds))}}
    results = {'roster': roster, 'arms': {}}
    plan = read(FZ.BASE / 'plan.json')
    for arm in ARMS:
        row = next(r for r in plan['rows'] if r['arm'] == arm and r['dataset'] == 'private_bdf')
        unit = FZ.BASE / 'units' / f'{row["id"]}.json'
        if not unit.exists():
            results['arms'][arm] = {'status': 'NOT_RUN'}; continue
        u = read(unit); dest = Path(u['dest']); assert sha(dest / 'arrays.npz') == u['array_sha256']
        meta = read(dest / 'meta.json'); assert meta['children'] == {str(i): k['id'] for i, k in enumerate(kids)}
        with np.load(dest / 'arrays.npz', allow_pickle=False) as z:
            X = z['age_features'].reshape(len(kids), -1)
        results['arms'][arm] = {'status': 'COMPLETE_VALID', 'frozen_unit': row['id'], **AP.run_probe(X, age, ids, folds)}
    results['raw_eeg_logvar'] = {'status': 'COMPLETE_VALID', **AP.run_probe(raw_logvar(kids), age, ids, folds),
                                 'feature': 'trial-mean log(var over 200 real samples + 1e-12) per channel, GX staged epochs before per-child z-score'}
    out = BASE / 'age_results.json'
    write(out, {**results, 'source_sha256': sha(__file__), 'age_probe_sha256': sha(AP.__file__), 'job': os.environ['SLURM_JOB_ID']})
    print({a: (v.get('model_metrics') if isinstance(v, dict) else v) for a, v in results['arms'].items()},
          results['raw_eeg_logvar']['model_metrics'], flush=True)


if __name__ == '__main__':
    main()
