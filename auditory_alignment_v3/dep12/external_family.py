"""DEP12 F_EXTERNAL (package 05 §3): CS-pair against the external systems on the SAME 20 s queries.

Query identity: Agent M's DEP12 attention queries are exactly the aln42 / ext_common `integrate` 20 s windows (DECISIONS M8):
4 consecutive 5 s competing-talker segments, same partition and test people as every Table 2 system. Person accuracies are therefore
paired by person on the same query set; the systems differ in how they read those windows (access table in EXTERNAL_COMPARISON.md).

Members (positive = CS-pair higher accuracy), per cohort:
  cs_pair − mTRF, − VLAAI, − Transformer-CLIP, − MindMix complete (blind order-symmetrised score), − MindMix EEG branch (DEP12 rule b)
CS-pair = per-person mean over seeds 3401/3407/3413 of the DEP12 primary score; rule (b) (training-side linear envelope readout) is the
main family, rule (a) (dependence decision) a second family; the post-hoc debiased variants are reported descriptively.
Statistics: aln41.analysis.family (bootstrap-t, family max-|T*|) with B = 10,000 as the package fixes (module constant re-pointed at
run time; the file is not edited). Only people with every member enter (coverage reported).

python -m auditory_alignment_v3.dep12.external_family   (CPU, Slurm) -> results/auditory_alignment_v3/dep12/F_EXTERNAL.{json,md}
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from .. import core
from ..aln41 import analysis as AN

ROOT = Path(core.REPO)
RES = ROOT / 'results/auditory_alignment_v3'
PRED = RES / 'dep12/predictions/attention_public'
OUT = RES / 'dep12'
SEEDS = (3401, 3407, 3413)
EXT = {'mTRF': 'paper/external_decoders/mtrf/TABLE2_MTRF.json', 'VLAAI': 'paper/external_decoders/vlaai_v2/TABLE2_VLAAI_V2.json',
       'TCLIP': 'paper/external_decoders/clip/TABLE2_CLIP.json'}
MMFAU = 'paper/external_decoders/mmfau/TABLE2_MMFAU.json'
MMDTU = 'aln42/external/EXTERNAL_COMPARISON.json'


def read(p):
    return json.loads(Path(p).read_text())


def dep12(ds, enc, key, debiased=False):
    p = PRED / ds / (f'{enc}.debiased.people.json' if debiased else f'{enc}.people.json')
    if not p.exists():
        return {}
    return {pid: v.get(key) for pid, v in read(p)['people'].items() if v.get(key) is not None}


def cs_pair(ds, key, debiased=False):
    per = [dep12(ds, f'cs_pair@{s}', key, debiased) for s in SEEDS]
    people = set.intersection(*[set(d) for d in per]) if all(per) else set()
    return {p: float(np.mean([d[p] for d in per])) for p in people}


def external(ds):
    out = {}
    for name, rel in EXT.items():
        d = read(RES / rel)['datasets'].get(ds)
        if d:
            out[name] = {p: v['accuracy'] for p, v in d['per_person_by_window_s']['20'].items()}
    if ds == 'dtu':
        out['MindMix_complete'] = {p: v['accuracy'] for p, v in read(RES / MMDTU)['per_person']['external'].items()}
    else:
        d = read(RES / MMFAU)['datasets'].get(ds)
        out['MindMix_complete'] = {p: v['accuracy'] for p, v in d['per_person_by_window_s']['20'].items()}
    return out


def family(fid, A, others, unit):
    people = sorted(set(A).intersection(*[set(v) for v in others.values()]))
    members = [(f'cs_pair-{k}', {p: A[p] - v[p] for p in people}) for k, v in others.items()]
    f = AN.family(fid, unit, members, people)
    f['coverage'] = {'people': len(people), 'cs_pair': len(A), **{k: len(v) for k, v in others.items()}}
    return f


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    AN.B_REP = 10000
    fams, desc = [], {}
    for ds in ('dtu', 'fau'):
        ext = external(ds)
        for rule, key in (('readout_b', 'attention20_acc_readout'), ('dependence_a', 'attention20_acc_dependence')):
            A = cs_pair(ds, key)
            others = {**ext, 'MindMix_branch': dep12(ds, 'MINDMIX_branch', key)}
            fams.append(family(f'F_EXTERNAL:{ds}:{rule}', A, others, '20 s attention accuracy difference (CS-pair minus system)'))
            desc[f'{ds}:{rule}'] = {k: (float(np.mean(list(v.values()))), len(v)) for k, v in {'cs_pair': A, **others}.items()}
            Ad = cs_pair(ds, key, debiased=True)
            if Ad:
                desc[f'{ds}:{rule}:debiased_cs_pair'] = (float(np.mean(list(Ad.values()))), len(Ad))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'F_EXTERNAL.json').write_text(json.dumps({'families': fams, 'descriptive_means': desc, 'B': AN.B_REP,
                                                      'query_identity': 'aln42/ext_common 20 s integrate windows (DECISIONS M8)'}, indent=1) + '\n')
    md = ['# DEP12 F_EXTERNAL — CS-pair vs external systems on the same 20 s queries', '',
          'Positive = CS-pair higher 20 s accuracy. CS-pair = person mean over seeds 3401/3407/3413. B = 10,000, simultaneous 95%.', '']
    for f in fams:
        md += [f"## {f['family_id']} — {f['status']}, n {f.get('complete_n')}/{f.get('expected_n')}", '',
               '| member | estimate | simultaneous 95% |', '|---|---|---|']
        md += [f"| {m['name']} | {m['estimate']:+.4f} | [{m['simultaneous_95'][0]:+.4f}, {m['simultaneous_95'][1]:+.4f}] |"
               if m.get('estimate') is not None and m.get('simultaneous_95') else f"| {m['name']} | — | — |" for m in f['members']]
        md += ['']
    md += ['## Descriptive means (person mean accuracy, n)', '']
    for k, v in desc.items():
        md += [f'- {k}: ' + (', '.join(f'{a} {m:.3f} (n{n})' for a, (m, n) in v.items()) if isinstance(v, dict) else f'{v[0]:.3f} (n{v[1]})')]
    (OUT / 'F_EXTERNAL.md').write_text('\n'.join(md) + '\n')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
