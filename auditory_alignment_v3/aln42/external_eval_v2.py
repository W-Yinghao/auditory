"""ALN4.2 R3 external comparison evaluation, v2 = external_eval.py with one dependency-scoped correction (2026-10-22).

Bug in v1 core_people(): inside R2.seeded(seed) the patched SRC.SEED equals `seed`, so `base = RO.BASE if seed == SRC.SEED`
picked the R1 readout directory for the R2 seeds; no R2 TCS/TNCE unit was found there, so TCS/TNCE were silently dropped and
both families came out "incomplete_no_intervals" (v1 output kept as EXTERNAL_COMPARISON_v1_incomplete.json). v2 decides the
readout directory from the loop seed (3401 -> R1 readout_v1, else r2/seed<S>/readout_v1). Everything else (integration,
families, outputs) is v1 unchanged and imported from it. v2 also adds per-person hearing groups for the manuscript tables.
"""
from __future__ import annotations

import json
import os

import numpy as np

from ..aln41 import analysis as AN, frozen as FZ, r2 as R2, readout as RO, source as SRC
from . import external_eval as V1, external_mindmix as XM

SEEDS, RESULTS = V1.SEEDS, V1.RESULTS
R1_SEED = 3401


def core_people():
    by, groups = {}, {}
    for seed in SEEDS:
        ctx = R2.seeded(seed) if seed != R1_SEED else V1._null()
        with ctx:
            base = (RO.BASE if seed == R1_SEED else R2.ROOT / f'seed{seed}' / 'readout_v1')
            for row in FZ.read(FZ.BASE / 'plan.json')['rows']:
                p = base / 'units' / f'{row["id"]}.json'
                if row['dataset'] != 'dtu' or row['arm'] not in ('B0', 'TCS', 'TNCE') or not p.exists():
                    continue
                for pid, r in FZ.read(p)['people'].items():
                    groups[pid] = r.get('group')
                    v = r.get('attention', {}).get('q0', {}).get('20')
                    if v:
                        by.setdefault(row['arm'], {}).setdefault(pid, {}).setdefault(seed, {})[row['content_fold']] = (v['accuracy'], v['nll_bits'])
    out = {}
    for arm, people in by.items():
        need = (R1_SEED,) if arm == 'B0' else SEEDS
        for pid, s in people.items():
            if all(x in s and sorted(s[x]) == [0, 1] for x in need):
                out.setdefault(arm, {})[pid] = {k: float(np.mean([np.mean([s[x][c][j] for c in (0, 1)]) for x in need]))
                                                for j, k in enumerate(('accuracy', 'nll_bits'))}
    return out, groups


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    old = RESULTS / 'EXTERNAL_COMPARISON.json'
    if old.exists() and not (RESULTS / 'EXTERNAL_COMPARISON_v1_incomplete.json').exists():
        v = json.loads(old.read_text())
        if any(f['status'] != 'complete' for f in v['families']):
            old.rename(RESULTS / 'EXTERNAL_COMPARISON_v1_incomplete.json')
    ext, (core3, groups) = V1.external_people(), core_people()
    assert set(core3) == {'B0', 'TCS', 'TNCE'}, sorted(core3)
    people = sorted(set(ext) | set().union(*[set(v) for v in core3.values()]))
    fams = []
    for metric, direction in (('accuracy', 'higher is better'), ('nll_bits', 'lower is better; negative = external better')):
        members = [(f'external-{arm}', {p: (ext[p][metric] - core3[arm][p][metric]) if p in ext and p in core3.get(arm, {}) else None for p in people})
                   for arm in ('B0', 'TCS', 'TNCE')]
        f = AN.family(f'F_EXTERNAL:{metric}', f'20 s attention {metric} ({direction})', members, people)
        f['method'] = 'sci_r1 identity bootstrap-t B=4000, family max-|T*|; core TCS/TNCE seed-averaged within person; external single released checkpoint, seed 3401'
        fams.append(f)
    RESULTS.mkdir(parents=True, exist_ok=True)
    desc = {name: {m: float(np.mean([v[m] for v in d.values()])) for m in ('accuracy', 'nll_bits')} for name, d in [('external', ext)] + list(core3.items())}
    (RESULTS / 'EXTERNAL_COMPARISON.json').write_text(json.dumps({'version': 'v2 (core_people seed-directory correction)', 'families': fams,
        'descriptive_means': desc, 'per_person': {'external': ext, **core3}, 'groups': {p: groups.get(p) for p in people},
        'binding_sha256': XM.sha(XM.BINDING), 'plan_sha256': XM.sha(XM.OUT / 'plan.json'),
        'display_name': 'MindMix released full architecture, common-protocol task adaptation'}, indent=1, default=float) + '\n')
    print(json.dumps({f['family_id']: f['status'] for f in fams}, indent=1), desc)


if __name__ == '__main__':
    main()
