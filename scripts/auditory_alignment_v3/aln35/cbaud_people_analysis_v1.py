"""Analysis of S35_CBAUD_PEOPLE as declared in CBAUD_PEOPLE_DESIGN.md (Slurm only; no refit).

Per person (DTU outer test), true-query NLL bits/query from eval.per_participant[<readout>/regular].logloss_bits,
content folds averaged within person. Family per readout: auditory-start advantage (direct − auditory risk) at
0.25 / 0.5 / 1.0 and its change versus 1.0; sci_r1 identity bootstrap-t, B = 4000, simultaneous across columns.
"""
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np

from auditory_alignment_v3 import core
from auditory_alignment_v3.sci_r1 import stats
from auditory_alignment_v3.aln34 import data_inner as I, cb_auditory as CA, learning_budget as B
from auditory_alignment_v3.aln35 import cbaud_people as CP

OUT = Path(core.REPO) / 'results/auditory_alignment_v3/aln35/cbaud_people_v1'
DOC = Path(core.REPO) / 'docs/auditory_alignment_v3/aln35/CBAUD_PEOPLE_RESULTS.md'
COLUMNS = ['advantage_0.25', 'advantage_0.5', 'advantage_1.0', 'change_0.25_vs_1.0', 'change_0.5_vs_1.0']


def risks(path, mode):
    rec = json.loads(Path(path).read_text())
    assert rec['status'] == 'complete' and not rec.get('truncated') and not rec.get('probe')
    pp = rec['eval']['per_participant']
    return rec, {p: (v[mode + '/regular']['logloss_bits'], v.get('group')) for p, v in pp.items()}


def collect(plan, mode):
    """cells[(fraction, arm)][person] -> list over content folds; groups[person]."""
    cells = defaultdict(lambda: defaultdict(list)); groups = {}; units = []
    def add(frac, arm, path, sf, cf):
        rec, vals = risks(path, mode)
        units.append({'fraction': frac, 'arm': arm, 'id': rec['experiment_id'], 'subject_fold': sf, 'content_fold': cf,
                      'best_epoch': rec.get('best_epoch'), 'optimizer_steps': rec.get('optimizer_steps'),
                      'record_sha256': B.sha(path)})
        for p, (v, g) in vals.items():
            assert np.isfinite(v)
            cells[(frac, arm)][p].append((cf, v))
            assert groups.setdefault(p, g) == g
    for row in plan['rows']:
        f = str(row['spec']['fraction']); sf, cf = row['subject_fold'], row['content_fold']
        add(f, 'auditory', CP.BASE / 'units' / f'{row["experiment_id"]}.json', sf, cf)
        add(f, 'direct', I.BASE / 'units' / f'{row["spec"]["direct_reference_id"]}.json', sf, cf)
    for ref in plan['references']['full']:
        add('1.0', 'auditory', CA.BASE / 'units' / f'{ref["auditory"]}.json', ref['subject_fold'], ref['content_fold'])
        add('1.0', 'direct', Path(core.OUT) / 'units' / f'{ref["direct"]}.json', ref['subject_fold'], ref['content_fold'])
    return cells, groups, units


def person_means(cells):
    out = {}
    for key, per in cells.items():
        out[key] = {}
        for p, vals in per.items():
            folds = sorted(cf for cf, _ in vals)
            assert folds == [0, 1], ('content folds', key, folds)
            out[key][p] = float(np.mean([v for _, v in vals]))
    return out


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'run under Slurm'
    plan = json.loads(CP.PLAN.read_text()); CP.verify(plan)
    result = {'job': os.environ['SLURM_JOB_ID'], 'plan_sha256': B.sha(CP.PLAN), 'families': {}, 'absolute': {}}
    lines = ['# S35_CBAUD_PEOPLE results — auditory-continued vs direct CBraMod start by source-people fraction', '',
             f"Analysis job {result['job']}; plan `{result['plan_sha256'][:16]}…`. DTU, seed 3401. Positive advantage = "
             'auditory-continued start has lower true-query NLL (bits/query). Change columns = advantage at the reduced '
             'fraction minus advantage at 1.0 (positive = the auditory start helps more when people are fewer). '
             'Intervals: identity bootstrap-t, B = 4000, simultaneous within each family.', '']
    for mode in ('native', 'unified'):
        cells, groups, units = collect(plan, mode)
        m = person_means(cells)
        people = sorted(set.intersection(*(set(v) for v in m.values())))
        def adv(f, p): return m[(f, 'direct')][p] - m[(f, 'auditory')][p]
        Y = np.array([[adv('0.25', p), adv('0.5', p), adv('1.0', p), adv('0.25', p) - adv('1.0', p),
                       adv('0.5', p) - adv('1.0', p)] for p in people])
        fam = {'all': stats.summary(Y, B=4000, seed=stats.group_seed('S35CBAUD', mode, 'all'))}
        for g in sorted({groups[p] for p in people}):
            idx = [i for i, p in enumerate(people) if groups[p] == g]
            fam[str(g)] = stats.summary(Y[idx], B=4000, seed=stats.group_seed('S35CBAUD', mode, g))
        result['families'][mode] = {'columns': COLUMNS, 'n': len(people), 'groups': {k: {kk: (vv.tolist() if hasattr(vv, 'tolist') else vv)
                                     for kk, vv in v.items()} for k, v in fam.items()}, 'units': units}
        result['absolute'][mode] = {f'{f}/{a}': float(np.mean([m[(f, a)][p] for p in people]))
                                    for f in ('0.25', '0.5', '1.0') for a in ('direct', 'auditory')}
        a = fam['all']
        lines += [f'## {mode} readout (n = {len(people)} people)', '', '| Column | Estimate | Simultaneous 95% |', '|---|---:|---|']
        for j, c in enumerate(COLUMNS):
            lines.append(f"| {c} | {a['est'][j]:+.4f} | [{a['band_low'][j]:+.4f}, {a['band_high'][j]:+.4f}] |")
        lines += ['', '| Fraction | direct risk | auditory risk |', '|---|---:|---:|']
        for f in ('0.25', '0.5', '1.0'):
            lines.append(f"| {f} | {result['absolute'][mode][f + '/direct']:.4f} | {result['absolute'][mode][f + '/auditory']:.4f} |")
        lines.append('')
        for g, v in fam.items():
            if g == 'all' or 'est' not in v:
                continue
            lines.append(f"- {g} (n={v['n']}): " + '; '.join(f"{c} {v['est'][j]:+.4f} [{v['band_low'][j]:+.4f}, {v['band_high'][j]:+.4f}]"
                                                            for j, c in enumerate(COLUMNS)))
        lines.append('')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'summary.json').write_text(json.dumps(result, indent=2, default=float) + '\n')
    DOC.write_text('\n'.join(lines) + '\n')
    print(json.dumps({m: {'n': result['families'][m]['n']} for m in result['families']}))


if __name__ == '__main__':
    main()
