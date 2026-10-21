"""ALN4.2 NET adapter (package docs/05): ALN3.6 per-person risks -> the package helper tools/paired_risk_summary.py.

post_R1_diagnostic_net_contrasts: NET_C = E0 - EC and NET_T = E0 - ET, labelled as designed after R1. The original ALN3.6
families and intervals are kept unchanged beside this output.
Cohorts: FAU_HA / FAU_CI / FAU_TH (whole-group exclusion panel), DTU (pooled parents), PRIVATE (matched AP / APwrong).
Tools: local_L1, CBpre_true_full; private AP, APwrong. Seeds: 3401 (R1) and 3407 (R2).
Public values are averaged over the two content folds within person, tool and seed (both required). The query fingerprint is
sha256 of the two per-fold query_set_id values in content-fold order. Those ids are the readouts' own digests of the query
segment ids, and they are identical for the five states, both tools and both seeds of one person. Private values come from
the child's outer fold; the fingerprint is the readout's query_set_id. Units: public 'mse' (source-target-scaled MSE),
private 'bits_per_trial'. Rosters: the frozen R1 bindings (FAU targets, DTU 44) and the 64 private children.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from .. import core
from ..aln36 import common as C, r2 as R36, public_readout as R, private_readout as PR, public_features as F, private_features as PFE

OUT = Path(core.OUT) / 'aln42' / 'net_v1'
RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/aln42/net'
TOOL = Path(core.REPO) / 'AUDITORY_ALN4_SERVER_PACKAGE_v4_2_20261021/tools/paired_risk_summary.py'
STATES = ('H0', 'E0', 'HP', 'EC', 'ET')


def h(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def rows_for_seed(seed):
    pub, priv = {}, []
    ctx = R36.seeded() if seed == 3407 else _null()
    with ctx:
        fplan = C.read(F.PLAN)
        for row in fplan['rows']:
            p = R.BASE / 'units' / f'{row["id"]}.json'
            if not p.exists():
                continue
            if row['kind'] == 'whole_group':
                cohort = 'FAU_' + row['excluded_group'].upper()
            elif row['dataset'] == 'dtu':
                cohort = 'DTU'
            else:
                continue                                   # FAU pooled parents are descriptive only in ALN3.6
            for pid, r in C.read(p)['people'].items():
                pub.setdefault((cohort, pid, row['tool']), {})[row['content_fold']] = (r['evaluation']['risk'], r['query_set_id'], r['evaluation']['unit'])
        if PFE.PLAN.exists():
            for row in C.read(PFE.PLAN)['rows']:
                p = PR.BASE / 'units' / f'{row["id"]}.json'
                if row['kind'] != 'matched_target' or not p.exists():
                    continue
                for cid, r in C.read(p)['people'].items():
                    fp = r['query_set_id']
                    priv.append({'cohort': 'PRIVATE', 'person_id': cid, 'tool': row['arm'], 'seed': seed, 'unit': 'bits_per_trial',
                                 **{f'risk_{s}': r['evaluation']['risk'][s] for s in STATES}, **{f'risk_{s}_query_fingerprint': fp for s in STATES}})
    out = []
    for (cohort, pid, tool), by_cf in sorted(pub.items()):
        if sorted(by_cf) != [0, 1]:
            continue
        assert {by_cf[c][2] for c in (0, 1)} == {'source_target_scaled_MSE'}
        fp = h([by_cf[0][1], by_cf[1][1]])
        out.append({'cohort': cohort, 'person_id': pid, 'tool': tool, 'seed': seed, 'unit': 'mse',
                    **{f'risk_{s}': (by_cf[0][0][s] + by_cf[1][0][s]) / 2 for s in STATES},
                    **{f'risk_{s}_query_fingerprint': fp for s in STATES}})
    return out + priv


class _null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def expected_panel():
    """Frozen rosters: R1 FAU group bindings (target ids), DTU 44 pooled people, 64 private children."""
    from ..aln36 import fau_group as G
    panel = {}
    for g in C.GROUPS:
        b = C.read(G.BINDINGS / f'{g}_cf0.json')
        panel['FAU_' + g.upper()] = {'person_ids': sorted(b['target_ids']), 'tools': list(C.TOOLS), 'unit': 'mse'}
    dtu = set()
    for row in C.read(F.PLAN)['rows']:
        p = R.BASE / 'units' / f'{row["id"]}.json'
        if row['kind'] == 'pooled_parent' and row['dataset'] == 'dtu' and p.exists():
            dtu |= set(C.read(p)['people'])
    panel['DTU'] = {'person_ids': sorted(dtu), 'tools': list(C.TOOLS), 'unit': 'mse'}
    kids = PFE.load_children()
    panel['PRIVATE'] = {'person_ids': sorted(k['id'] for k in kids), 'tools': ['AP', 'APwrong'], 'unit': 'bits_per_trial'}
    return panel


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--seeds', type=int, nargs='+', required=True)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700); RESULTS.mkdir(parents=True, exist_ok=True)
    tag = 's' + '_s'.join(map(str, a.seeds))
    rows = [r for s in a.seeds for r in rows_for_seed(s)]
    panel = expected_panel()
    assert len(panel['DTU']['person_ids']) == 44 and len(panel['PRIVATE']['person_ids']) == 64
    csv_path, panel_path = OUT / f'normalized_person_risks_{tag}.csv', OUT / f'expected_panel_{tag}.json'
    cols = ['cohort', 'person_id', 'tool', 'seed', 'unit'] + [f'risk_{s}' for s in STATES] + [f'risk_{s}_query_fingerprint' for s in STATES]
    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator='\n'); w.writeheader()
        for r in rows:
            w.writerow(r)
    panel_path.write_text(json.dumps(panel, indent=1) + '\n')
    out = RESULTS / f'paired_net_diagnostic_{tag}.json'
    assert not out.exists(), 'output exists; the helper refuses to overwrite'
    cmd = [sys.executable, '-B', str(TOOL), '--input', str(csv_path), '--output', str(out), '--expected-seeds', *map(str, a.seeds),
           '--expected-panel', str(panel_path), '--family-id', f'POST_R1_NET_DIAGNOSTIC_{tag}']
    rc = subprocess.run(cmd).returncode
    receipt = {'version': 'ALN42_NET_ADAPTER_v1', 'seeds': a.seeds, 'csv_sha256': C.sha(csv_path), 'panel_sha256': C.sha(panel_path),
               'tool_sha256': C.sha(TOOL), 'adapter_sha256': C.sha(Path(__file__)), 'rows': len(rows), 'returncode': rc,
               'output': str(out.relative_to(core.REPO)) if out.exists() else None,
               'aggregation': 'public: mean over content folds 0/1 within person/tool/seed (both required); private: outer-fold value',
               'query_fingerprint': 'per-risk fingerprints = sha256 of the readout query_set_id(s); equal across states, tools, seeds by construction',
               'scope': 'post_R1_diagnostic_net_contrasts; original ALN3.6 families retained'}
    (RESULTS / f'net_adapter_receipt_{tag}.json').write_text(json.dumps(receipt, indent=1) + '\n')
    print(json.dumps(receipt, indent=1))


if __name__ == '__main__':
    main()
