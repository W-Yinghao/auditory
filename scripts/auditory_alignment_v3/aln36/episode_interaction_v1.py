"""ALN3.6 R1 supplement: direct interval for the episode adaptation interaction (CPU only, no new episode training).

Per DTU person and source seed, local L1 native readout, pressure 100, support U30, the same query set:
  zero-step advantage  A0  = NLL(ordinary, 0 steps)  - NLL(episode, 0 steps)
  fixed-20 advantage   A20 = NLL(ordinary, 20 steps) - NLL(episode, 20 steps)
  interaction          I   = A20 - A0 (positive: the episode model gains more from the 20 support steps)
from stages.outer.values.{ordinary,episode}.per_participant.*.supports.U30.candidates.{0,20}.metrics.native.nll_bits.
Seed 3401 uses episode_pressure_v1 with the two documented lineage_v2 replacements; seed 3407 uses
episode_pressure_s3407_v1. Content folds are averaged within person. Intervals: sci_r1 identity bootstrap-t, B = 4000,
simultaneous over the six members (A0, A20, I x two seeds); the two seeds share people and replicate indices.
"""
import json
import os
from pathlib import Path

import numpy as np

from auditory_alignment_v3.sci_r1 import stats as S
from auditory_alignment_v3.aln36 import common as C

ROOT = Path(C.OUT).parent / 'aln35'
OUT = C.REPO / 'results/auditory_alignment_v3/aln36/episode_interaction_v1'
LANES = {3401: ('episode_pressure_v1', 'episode_lineage_v2'), 3407: ('episode_pressure_s3407_v1', None)}


def records(seed):
    lane, lineage = LANES[seed]
    plan = C.read(ROOT / lane / 'plan.json')
    replaced = {}
    if lineage:
        for r in C.read(ROOT / lineage / 'plan.json')['rows']:
            replaced[r['parent_aln35_id']] = ROOT / lineage / 'units' / f'{r["id"]}.json'
    out = []
    for row in plan['rows']:
        s = row['source']
        if s['dataset'] != 'dtu' or s['architecture'] != 'lag_local_tokens' or row['support_steps'] != 100 or row['seed'] != seed:
            continue
        path = replaced.get(row['id'], ROOT / lane / 'units' / f'{row["id"]}.json')
        rec = C.read(path); assert rec['status'] == 'complete' and not rec.get('probe')
        out.append((row, path, rec))
    assert len(out) == 10, (seed, len(out))
    return out


def per_person(seed):
    vals = {}
    for row, path, rec in records(seed):
        v = rec['stages']['outer']['values']
        for pid in v['episode']['per_participant']:
            def nll(regime, steps):
                c = v[regime]['per_participant'][pid]['supports']['U30']['candidates'][str(steps)]['metrics']['native']
                return c['nll_bits'], c.get('candidate_hash'), c['n_query']
            (oz, hz, nz), (ez, hz2, nz2) = nll('ordinary', 0), nll('episode', 0)
            (o20, h20, n20), (e20, h202, n202) = nll('ordinary', 20), nll('episode', 20)
            assert nz == nz2 == n20 == n202 and hz == hz2 == h20 == h202, 'paired query/candidate set differs'
            vals.setdefault(pid, []).append({'A0': oz - ez, 'A20': o20 - e20, 'cf': row['content_fold'], 'unit': row['id'],
                                             'record_sha256': C.sha(path)})
    out = {}
    for pid, items in vals.items():
        assert sorted(i['cf'] for i in items) == [0, 1], (pid, items)
        a0 = float(np.mean([i['A0'] for i in items])); a20 = float(np.mean([i['A20'] for i in items]))
        out[pid] = {'A0': a0, 'A20': a20, 'I': a20 - a0}
    return out


def main():
    assert os.environ.get('SLURM_JOB_ID')
    data = {seed: per_person(seed) for seed in LANES}
    people = sorted(data[3401]); assert people == sorted(data[3407]) and len(people) == 44
    idx = S.draws(len(people), S.NB, 361020)
    items, members = {}, []
    for seed in LANES:
        for k in ('A0', 'A20', 'I'):
            y = np.array([data[seed][p][k] for p in people]); s = S.summary(y, idx=idx)
            name = f'seed{seed}/{k}'; items[name] = (s['est'], s['se'], s['T'])
            members.append({'name': name, 'n': len(y), 'estimate': float(s['est']), 'se': float(s['se']),
                            'pointwise_95': [float(s['ci_low']), float(s['ci_high'])]})
    fam = S.family_maxt(items)
    for m in members:
        iv = fam['intervals'][m['name']]; m['simultaneous_95'] = [iv['sim_low'], iv['sim_high']]
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {'version': 'ALN36_EPISODE_INTERACTION_v1', 'analysis_origin': C.ORIGIN, 'unit': 'bits/query (native NLL)',
               'definition': 'per person: A = ordinary - episode NLL (positive favours episode); I = A20 - A0; U30, pressure 100, local L1, DTU',
               'method': 'sci_r1 identity bootstrap-t, B=4000, family max-|T*| over 6 members', 'critical': fam['crit'],
               'members': members, 'people': len(people), 'job': os.environ['SLURM_JOB_ID']}
    C.write(OUT / 'summary.json', summary)
    with open(OUT / 'per_person.csv', 'w') as f:
        f.write('person,' + ','.join(f'seed{s}_{k}' for s in LANES for k in ('A0', 'A20', 'I')) + '\n')
        for p in people:
            f.write(p + ',' + ','.join(f'{data[s][p][k]:.9f}' for s in LANES for k in ('A0', 'A20', 'I')) + '\n')
    print(json.dumps({m['name']: [round(m['estimate'], 6), [round(x, 6) for x in m['simultaneous_95']]] for m in members}))


if __name__ == '__main__':
    main()
