"""W7 GPU-arm results: frozen-readout endpoints of TCS_RES / TCS_PRES / TCS_RES_PRES / TCS_CCS against TCS, and the frozen
W7_FACT families (results/auditory_alignment_v3/paper/w7/W7_FAMILIES_v1.json; design W7_CS_DEPENDENCE_PREREG_FROZEN.md §4).

Per-person endpoints come from manuscript_tables' verified collectors (aln41 readout units: content folds averaged, then all
three seeds required and averaged), with the W7 arms' readout directories (paper/w7_arms_v2: w7_v1/arms_v2/<ARM>/seed<S>/
readout_v1) added; age from each arm x seed age_v1/age_results.json (same parsing as manuscript_tables.collect_age).
Families: aln41.analysis.family with its default B = 4000, as frozen for W7. Sign as frozen: positive = arm better (loss-type
endpoints are TCS - arm).

python -m auditory_alignment_v3.paper.w7_results   (CPU, Slurm) -> results/auditory_alignment_v3/paper/w7/{W7_FACT_FAMILIES.json, W7_ARMS.md}
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from .. import core
from ..aln41 import analysis as AN
from . import manuscript_tables as MT
from . import w7_arms_v2 as WA

OUT = Path(core.REPO) / 'results/auditory_alignment_v3/paper/w7'
FAMILIES = OUT / 'W7_FAMILIES_v1.json'
ARMS = ('TCS_RES', 'TCS_PRES', 'TCS_RES_PRES', 'TCS_CCS')
LOSS = {'time_fixed_loss', 'attention20_nll_bits', 'age_abs_err'}
_ORIG_DIRS = MT.readout_dirs                         # captured before main() re-points MT.readout_dirs


def w7_dirs():
    base = _ORIG_DIRS()
    for arm in ARMS:
        base[arm] = [(s, WA.OUT / arm / f'seed{s}' / 'readout_v1' / 'units') for s in WA.SEEDS]
    return base


def w7_age(priv):
    for arm in ARMS:
        per = {}
        for s in WA.SEEDS:
            f = WA.OUT / arm / f'seed{s}' / 'age_v1' / 'age_results.json'
            if not f.exists():
                continue
            for c in MT.read(f)['arms'].get(arm, {}).get('children', []):
                per.setdefault(c['id'], {})[s] = c['model_absolute_error_months']
        for cid, by in per.items():
            if all(s in by for s in WA.SEEDS):
                priv.setdefault(arm, {}).setdefault(cid, {})['age_abs_err'] = float(np.mean([by[s] for s in WA.SEEDS]))


def cell(vals):
    t, j = MT.cell(vals, digits=4)
    return t


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    orig = MT.readout_dirs
    MT.readout_dirs = w7_dirs
    try:
        pub, priv, groups = MT.collect_readouts()
    finally:
        MT.readout_dirs = orig
    MT.collect_age(priv); w7_age(priv)
    fams = MT.read(FAMILIES)['families']
    done, md = [], ['# W7 GPU arms — frozen-readout endpoints and W7_FACT families', '',
                    'Person means [95% percentile bootstrap] over people with all three seeds; families: aln41.analysis.family (B = 4000), '
                    'simultaneous 95%, positive = arm better. Pre-registered in W7_CS_DEPENDENCE_PREREG_FROZEN.md (frozen 2026-10-22 19:48; '
                    'hypotheses proposed after Tables 2-6 were seen); PRES uses APPENDUM_04 (L2), beta = 1.0; CCS uses APPENDUM_02/03.', '']
    rows = []
    for f in fams:
        if not f['id'].startswith('W7_FACT:'):
            continue
        _, e, c = f['id'].split(':')
        src = priv if c == 'private' else {s: v for (cc, s), v in pub.items() if cc == c}
        T = src.get('TCS', {})
        if not T or not all(a in src for a in ARMS):
            done.append({'family_id': f['id'], 'status': 'missing_member', 'members': [], 'present': sorted(a for a in ARMS if a in src)})
            continue
        sign = -1 if e in LOSS else 1
        members = [(m, AN.diff(src[m.split('-')[0]], T, e, sign)) for m in f['members']]
        done.append(AN.family(f['id'], f.get('unit', e), members, sorted(T)))
        rows.append([f'{e} ({c})'] + [cell([v.get(e) for v in src.get(s, {}).values()]) for s in ('TCS',) + ARMS])
    md += ['## Endpoint means', '', MT.table(['endpoint (cohort)', 'TCS', *ARMS], rows), '', '## W7_FACT families', '']
    for f in done:
        if f.get('status') == 'missing_member':
            md += [f"**{f['family_id']}** — missing member (present: {f['present']})", '']
            continue
        md += [f"**{f['family_id']}** — {f['status']}, n {f.get('complete_n')}/{f.get('expected_n')}", '',
               MT.table(['member', 'estimate', 'simultaneous 95%'],
                        [[m['name'], f"{m['estimate']:+.5f}" if m.get('estimate') is not None else '—',
                          (f"[{m['simultaneous_95'][0]:+.5f}, {m['simultaneous_95'][1]:+.5f}]" if m.get('simultaneous_95') else '—')]
                         for m in f['members']]), '']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'W7_FACT_FAMILIES.json').write_text(json.dumps({'families': done, 'families_file_sha256': MT.SRC.sha(FAMILIES)}, indent=1) + '\n')
    (OUT / 'W7_ARMS.md').write_text('\n'.join(md) + '\n')
    print('written', OUT / 'W7_ARMS.md')


if __name__ == '__main__':
    main()
