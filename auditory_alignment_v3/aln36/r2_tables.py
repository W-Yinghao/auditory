"""ALN3.6 R2 family tables (CPU, read-only on summary.json): the R1 FAMILY_TABLES.md layout for r2_final, and an R1-vs-R2
replication table (same members, both seeds' estimates and simultaneous bootstrap-t intervals; '+' / '-' = the simultaneous
interval excludes 0 on that side, '0' = it includes 0). Seeds are not pooled here; each table conditions on its own fitted models.
Usage: `python -m auditory_alignment_v3.aln36.r2_tables`.
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import core

ROOT = Path(core.REPO) / 'results/auditory_alignment_v3/aln36'
R1, R2 = ROOT / 'r1/r1_final', ROOT / 'r2/r2_final'


def mark(ci):
    return '+' if ci[0] > 0 else '-' if ci[1] < 0 else '0'


def fmt(ci):
    return f'[{ci[0]:+.5f}, {ci[1]:+.5f}]'


def coverage(f):
    return '; '.join(f'{g} {c["complete_n"]}/{c["expected_n"]}' for g, c in f['coverage'].items())


def family_tables(summary):
    out = []
    for f in summary['families']:
        ref = f['secondary_reference_fixed_se_max_z']
        out += [f'### {f["family_id"]} ({f["unit"]})', '', f'Coverage: {coverage(f)}',
                f'Status {f["status"]}; bootstrap-t critical {f["critical"]:.3f}; fixed-SE max-|z| reference critical {ref["critical"]:.3f}', '',
                '| member | n | estimate | simultaneous 95% (bootstrap-t) | fixed-SE reference 95% |', '|---|---:|---:|---|---|']
        out += [f'| {m["name"]} | {m["n"]} | {m["estimate"]:+.5f} | {fmt(m["simultaneous_95"])} | {fmt(ref["intervals"][m["name"]])} |'
                for m in f['members']]
        out.append('')
    return '\n'.join(out) + '\n'


def replication(s1, s2):
    by1 = {f['family_id']: f for f in s1['families']}
    out = ['# ALN3.6 R1 (seed 3401) vs R2 (seed 3407), member by member', '',
           'Mark: simultaneous bootstrap-t 95% interval above 0 (+), below 0 (-), or including 0 (0). Same contrasts, same people,',
           'bindings and statistics; only the training seed differs. Not pooled.', '']
    agree = disagree = 0
    for f2 in s2['families']:
        f1 = by1[f2['family_id']]; m1 = {m['name']: m for m in f1['members']}
        out += [f'## {f2["family_id"]} ({f2["unit"]})', '', '| member | R1 estimate | R1 sim 95% | R2 estimate | R2 sim 95% | marks R1/R2 |',
                '|---|---:|---|---:|---|---|']
        for m in f2['members']:
            a = m1[m['name']]; k1, k2 = mark(a['simultaneous_95']), mark(m['simultaneous_95'])
            if k1 != '0' or k2 != '0':
                agree += k1 == k2; disagree += k1 != k2
            out.append(f'| {m["name"]} | {a["estimate"]:+.5f} | {fmt(a["simultaneous_95"])} | {m["estimate"]:+.5f} | {fmt(m["simultaneous_95"])} | {k1}/{k2} |')
        out.append('')
    out.insert(4, f'Members resolved in at least one seed: {agree + disagree}; same mark in both seeds: {agree}; different: {disagree}.\n')
    return '\n'.join(out) + '\n'


def main():
    s1, s2 = (json.loads((p / 'summary.json').read_text()) for p in (R1, R2))
    (R2 / 'FAMILY_TABLES.md').write_text(family_tables(s2))
    (ROOT / 'r2' / 'R1_R2_REPLICATION.md').write_text(replication(s1, s2))
    print('written', R2 / 'FAMILY_TABLES.md', ROOT / 'r2' / 'R1_R2_REPLICATION.md')


if __name__ == '__main__':
    main()
