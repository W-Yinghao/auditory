"""ALN4.2 source-diagnosis aggregation (CPU): unit records -> public summary tables, gradient audit, helper cross-check.

Outputs in results/auditory_alignment_v3/aln42/source_diag/:
- SOURCE_DIAG_SUMMARY.json: per arm x snapshot x panel means (and between-person sd) of every exported quantity;
- source_probe_person.jsonl.gz: the per-person rows (opaque person hashes only);
- source_gradient_audit.json: the d/da data-vs-KL audit, projection/backbone gradient norms, code checks, reproduction;
- helper_crosscheck.json: the package tools/source_probe_metrics.py on the exported fit-episode-0 bundles vs this module's
  own NCE / uniform values for the same episode.
Directions: NCE losses lower = better; CS objective = -score, lower = better; 'gain' = prior objective - support objective
(positive = the per-episode support delta improved the query objective).
"""
from __future__ import annotations

import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np

from .. import core
from . import source_diag as SD

RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/aln42/source_diag'
TOOL = Path(core.REPO) / 'AUDITORY_ALN4_SERVER_PACKAGE_v4_2_20261021/tools/source_probe_metrics.py'


def ms(xs):
    xs = np.asarray([x for x in xs if x is not None], float)
    return {'mean': float(xs.mean()) if len(xs) else None, 'sd': float(xs.std(ddof=1)) if len(xs) > 1 else None, 'n': int(len(xs))}


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    plan = SD.read(SD.OUT / 'plan.json'); RESULTS.mkdir(parents=True, exist_ok=True)
    summary, grads, rows_out, cross = {}, {}, [], {}
    for row in plan['rows']:
        u = SD.read(SD.OUT / 'units' / f'{row["id"]}.json'); arm = row['arm']
        assert SD.sha(u['rows_path']) == u['rows_sha256']
        rows = [json.loads(l) for l in gzip.open(u['rows_path'], 'rt')]
        rows_out += rows
        grads[arm] = {'gradient_audit': u['gradient_audit'], 'code_checks': u['code_checks'], 'reproduction': u['reproduction'],
                      'zero_update_checks': u['zero_update_checks'], 'optimizer_constructed': u['optimizer_constructed'],
                      'seconds': u['seconds'], 'gpu_peak_mb': u['gpu_peak_mb'], 'device': u['device']}
        for snap in map(str, SD.SNAPSHOTS):
            for panel in ('fit', 'dev'):
                rs = [r for r in rows if str(r['snapshot']) == snap and r['panel'] == panel]
                key = f'{arm}/{snap}/{panel}'; s = {}
                for split in ('S', 'Q'):
                    for metric in ('margin', 'top1_retrieval', 'nce_minus_uniform', 'nce_nats', 'uniform_nce_nats', 'pos_mean', 'legal_neg_mean'):
                        s[f'pairing/{split}/{metric}'] = ms([r['slot_pairing'][f'{split}/{v}/{k}'][metric] for r in rs for v in ('env', 'ss', 'sc') for k in range(3)])
                        for v in ('env', 'ss', 'sc'):
                            s[f'pairing/{split}/{v}/{metric}'] = ms([r['slot_pairing'][f'{split}/{v}/{k}'][metric] for r in rs for k in range(3)])
                    s[f'tcs_probe/{split}/slot_score'] = ms([np.mean(r['slot_pairing'][f'{split}/{v}/tcs_potentials']['slot_scores_nats']) for r in rs for v in ('env', 'ss', 'sc')])
                    for part in ('tokens', 'env', 'ss', 'sc'):
                        s[f'repr/{split}/{part}/effective_rank'] = ms([r['repr'][f'{split}/{part}/{k}']['effective_rank'] for r in rs for k in range(3)])
                        s[f'repr/{split}/{part}/mean_offdiag_cosine'] = ms([r['repr'][f'{split}/{part}/{k}']['mean_offdiag_cosine'] for r in rs for k in range(3)])
                        s[f'repr/{split}/{part}/centred_variance'] = ms([r['repr'][f'{split}/{part}/{k}']['centred_variance'] for r in rs for k in range(3)])
                        s[f'repr/{split}/{part}/rel_change_from_update0'] = ms([r['repr'].get(f'{split}/{part}/rel_change_from_update0') for r in rs])
                for label in ('native', 'correct_pair_probe'):
                    obs = [r['objective'][label] for r in rs if label in r['objective']]
                    if not obs:
                        continue
                    q = {g: [o['query'][g]['query_objective_nats'] for o in obs] for g in ('uniform', 'prior', 'support')}
                    s[f'{label}/query_objective/uniform'] = ms(q['uniform']); s[f'{label}/query_objective/prior'] = ms(q['prior'])
                    s[f'{label}/query_objective/support'] = ms(q['support'])
                    s[f'{label}/support_gain_on_query'] = ms([p - t for p, t in zip(q['prior'], q['support'])])
                    s[f'{label}/support_gain_positive_fraction'] = float(np.mean([p - t > 0 for p, t in zip(q['prior'], q['support'])]))
                    s[f'{label}/prior_minus_uniform_on_query'] = ms([un - p for un, p in zip(q['uniform'], q['prior'])])
                    s[f'{label}/support_objective_change_5_steps'] = ms([o['support_steps'][-1]['without_penalty'] - o['support_steps'][0]['without_penalty'] for o in obs])
                    s[f'{label}/delta_l2'] = ms([float(np.linalg.norm(o['delta'])) for o in obs])
                    s[f'{label}/q_prior'] = obs[0]['q_prior']
                    qs = np.array([o['q_support'] for o in obs]); s[f'{label}/q_support_mean'] = qs.mean(0).tolist(); s[f'{label}/q_support_sd'] = qs.std(0).tolist()
                summary[key] = s
        for snap in map(str, SD.SNAPSHOTS):
            summary[f'{arm}/{snap}/ridge'] = u['ridge'][snap]
        # helper cross-check on the exported fit-episode-0 bundles
        for snap in map(str, SD.SNAPSHOTS):
            b = Path(u['rows_path']).parent / f'helper_bundle_s{snap}.npz'
            outp = RESULTS / 'helper' / f'{arm}_s{snap}.json'
            outp.parent.mkdir(parents=True, exist_ok=True)
            if outp.exists():
                outp.unlink()
            rc = subprocess.run([sys.executable, '-B', str(TOOL), '--input', str(b), '--output', str(outp)], capture_output=True, text=True)
            mine = next(r for r in rows if str(r['snapshot']) == snap and r['panel'] == 'fit' and r['episode'] == 0)
            own = {f'{v}/{k}': (mine['slot_pairing'][f'Q/{v}/{k}']['nce_nats'], mine['slot_pairing'][f'Q/{v}/{k}']['uniform_nce_nats'])
                   for v in ('env', 'ss', 'sc') for k in range(3)}
            cross[f'{arm}/{snap}'] = {'returncode': rc.returncode, 'helper': json.loads(outp.read_text()) if outp.exists() else rc.stderr[-500:],
                                      'own_nce_and_uniform_by_view_slot': own}
    with gzip.open(RESULTS / 'source_probe_person.jsonl.gz', 'wt') as f:
        for r in rows_out:
            f.write(json.dumps(r) + '\n')
    for name, value in (('SOURCE_DIAG_SUMMARY.json', {'plan_sha256': SD.sha(SD.OUT / 'plan.json'), 'summary': summary,
                                                       'directions': __doc__.split('Directions:')[1].strip()}),
                        ('source_gradient_audit.json', grads), ('helper_crosscheck.json', cross)):
        (RESULTS / name).write_text(json.dumps(value, indent=1) + '\n')
    print('rows', len(rows_out), 'summary keys', len(summary))


if __name__ == '__main__':
    main()
