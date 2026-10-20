"""Read-only Slurm inventory of ALN3.5 scientific source schemas."""
import json
import os
from pathlib import Path
import numpy as np
from auditory_alignment_v3 import core


def shape(x, depth=0):
    if isinstance(x, dict):
        if depth > 1:
            return list(x)[:12]
        return {k: shape(v, depth + 1) for k, v in x.items() if k not in ('curve', 'curves')}
    if isinstance(x, list):
        return {'length': len(x), 'first': shape(x[0], depth + 1) if x else None}
    return x


def main():
    assert os.environ.get('SLURM_JOB_ID')
    base = Path(core.OUT)
    for lane in ('content_time_v1', 'prior_science_v1', 'private_current_time_v2'):
        plan = json.loads((base / 'aln34' / lane / 'plan.json').read_text())
        for ds in (('fau', 'private_bdf') if lane == 'prior_science_v1' else ('federici',) if lane == 'content_time_v1' else ('private_bdf',)):
            u = next(u for u in plan['rows'] if u['source']['dataset'] == ds)
            rec = json.loads((base / 'aln34' / lane / 'units' / (u['id'] + '.json')).read_text())
            display = {k: v for k, v in rec.items() if k not in ('decoding', 'per_participant')}
            for k in ('decoding', 'per_participant'):
                if k in rec: display[k] = {next(iter(rec[k])): next(iter(rec[k].values()))}
            print(lane, ds, json.dumps(shape(display)), flush=True)
            source = json.loads((base / 'units' / (u['source']['experiment_id'] + '.json')).read_text())
            print('SOURCE', json.dumps(shape(source)), flush=True)
            store = Path(plan.get('store', '<private checkpoint storage>/auditory_alignment_v3/aln34_private_current_time_v1'))
            cache = store / 'cache' / u.get('previous_id', u['id']) / 'arrays.npz'
            if cache.exists():
                with np.load(cache, allow_pickle=False) as z:
                    print('ARRAYS', str(cache), {k: (z[k].shape, str(z[k].dtype)) for k in z.files}, flush=True)


if __name__ == '__main__': main()
