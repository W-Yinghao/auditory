"""Slurm CPU aggregation of frozen public/private science units, with complete identities."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import os
from pathlib import Path
import shutil

import numpy as np

from .. import core, bc_interim
from ..sci_r1 import stats as S
from . import learning_budget as B
from . import new_lane_aggregate as A

BASE = Path(core.OUT) / 'aln34'
NOTE = BASE / 'SCIENCE_AGGREGATION_NOTE_20261017.md'
RES = Path(core.REPO) / 'results/auditory_alignment_v3/aln34/science'
DOC = Path(core.REPO) / 'docs/auditory_alignment_v3/NEW_SCIENCE_RESULTS.md'
CENTERS = (-200, 0, 200, 400, 600)
WINDOWS = ('full', 'pre', '0_200', '200_400', '400_600')
PRIVATE_METRICS = ('auc', 'nll_bits', 'brier', 'gain_vs_base_bits', 'history_gain_bits',
                   'history_gain_common_support_bits', 'history_twin_gain_bits', 'history_minus_twin_bits')


def difference(a, b):
    return None if a is None or b is None else a - b


def configs(row):
    return A.arm(row) + '/' + row['spec']['objective'] + '/' + row['family_id']


def public_rows(panel, plan, audit):
    lane = 'content_time_v1'; sha = B.sha(BASE / lane / 'plan.json')
    for unit in plan['rows']:
        row = unit['source']; old = A.source(row['experiment_id'], unit['record_sha256'])
        rec = A.production(lane, unit, sha, audit)
        targets = ['env/direct', 'env/history_conditional']
        if row['dataset'] != 'federici':
            targets += [f'{t}/{v}' for t in ('onset', 'spec', 'flux', 'Ac', 'Lz') for v in ('direct', 'conditional')]
        for rep in (('model', 'raw') if row['spec']['architecture'] == 'lag_local_tokens' else ('model',)):
            for target in targets:
                scope = 'public/' + configs(row) + '/' + rep + '/' + target
                for tau in CENTERS:
                    for other in CENTERS:
                        cell = f'{tau}/{other}'
                        per = rec['decoding'][rep + '/' + target][cell]['per_participant'] if rec else {}
                        for metric in ('r', 'mse', 'matched_minus_mismatch_r', 'mismatch_minus_matched_mse'):
                            obs = None
                            if rec:
                                obs = {p: v.get(metric) if metric in ('r', 'mse') else
                                       difference(v['r'], v['mismatch_r']) if metric == 'matched_minus_mismatch_r' else
                                       difference(v['mismatch_mse'], v['mse']) for p, v in per.items()}
                            panel.add(scope, cell, metric, row, old['eval']['per_participant'], obs)


def private_rows(panel, plan, audit):
    lane = 'private_current_time_v1'; sha = B.sha(BASE / lane / 'plan.json'); covariates = {}; missing = defaultdict(int)
    for unit in plan['rows']:
        row = unit['source']; old = A.source(row['experiment_id'], unit['record_sha256'])
        rec = A.production(lane, unit, sha, audit); pop = old['eval']['per_participant']
        if row['family_id'] == 'E_LOCAL' and row['spec']['objective'] == 'NCE' and row['seed'] == 3401:
            covariates.update({p: {'group': v['group'], 'age': v.get('age_months'), 'duration': v.get('duration_months')} for p, v in pop.items()})
        config = '|'.join(map(str, unit['config']))
        for metric in PRIVATE_METRICS:
            for window in WINDOWS:
                obs = {p: v['windows'][window].get(metric) for p, v in rec['per_participant'].items()} if rec else None
                panel.add('private/windows/' + config, window, metric, row, pop, obs)
        for cal in ('original_calibration', 'source_only_destination_calibration'):
            for metric in ('auc', 'nll_bits', 'brier'):
                for src in WINDOWS[1:]:
                    for dst in WINDOWS[1:]:
                        key = src + '/' + dst
                        obs = {p: v['temporal_generalization'][key][cal].get(metric) for p, v in rec['per_participant'].items()} if rec else None
                        panel.add('private/tg/' + config + '/' + cal, key, metric, row, pop, obs)
        for frac in ('0.1', '0.3'):
            for metric in ('auc', 'nll_bits', 'brier', 'history_gain_bits', 'benefit_bits'):
                for step in ('0', '5', '20'):
                    obs = None
                    if rec:
                        obs = {}
                        for p, v in rec['per_participant'].items():
                            d = v['adaptation'][frac]
                            if d['status'] != 'complete':
                                if metric == 'nll_bits' and step == '0': missing[config + '/' + frac + '/' + d['status']] += 1
                                continue
                            c = d['candidates']; obs[p] = difference(c['0']['nll_bits'], c[step]['nll_bits']) if metric == 'benefit_bits' else c[step].get(metric)
                    panel.add('private/adapt/' + config + '/' + frac, step, metric, row, pop, obs)
    return covariates, dict(missing)


def joint_ols(Y, cov, ids, ha_only, seed, Bn):
    names = ('age_per_year', 'duration_per_year') if ha_only else ('age_per_year', 'HA_indicator')
    good = [p for p in ids if p in cov and cov[p]['age'] is not None and np.isfinite(cov[p]['age']) and
            (not ha_only or cov[p]['group'] == 'HA' and cov[p]['duration'] is not None and np.isfinite(cov[p]['duration']))]
    if len(good) < 8:
        return {'n': len(good), 'missing_or_outside_population': len(ids) - len(good), 'note': 'fewer than eight complete identities'}
    X = np.array([[cov[p]['age'] / 12., cov[p]['duration'] / 12. if ha_only else float(cov[p]['group'] == 'HA')] for p in good])
    rank = int(np.linalg.matrix_rank(np.c_[np.ones(len(X)), X]))
    if rank != 3:
        return {'n': len(good), 'design_rank': rank, 'note': 'rank-deficient covariates'}
    items = {}; endpoints = {}
    for label, vals in Y.items():
        model = S.ols(X, np.array([vals[p] for p in good]), names, B=Bn, seed=seed)
        endpoints[label] = A.as_json(model)
        if 'coef' in model:
            for name in names:
                c = model['coef'][name]; items[label + '/' + name] = (c['est'], c['se'], model['T'][name])
    return {'n': len(good), 'missing_or_outside_population': len(ids) - len(good), 'design_rank': rank,
            'endpoints': endpoints, 'simultaneous_coefficient_family': A.as_json(S.family_maxt(items))}


def summaries(panel, cov, Bn):
    families = sorted({h[:3] for h in panel.expected}); output = []; developmental = defaultdict(dict)
    for ds, scope, metric in families:
        labels = sorted(h[3] for h in panel.expected if h[:3] == (ds, scope, metric))
        seeds = sorted({t[0] for lab in labels for ts in panel.expected[(ds, scope, metric, lab)].values() for t in ts})
        seed_scopes = [(str(s), {s}) for s in seeds] + ([('complete_seed_mean', set(seeds))] if len(seeds) > 1 else [])
        for name, required in seed_scopes:
            vals = {lab: panel.complete((ds, scope, metric, lab), required) for lab in labels}
            ids = sorted(set.intersection(*[set(v) for v in vals.values()]))
            expected = set.union(*[set(panel.expected[(ds, scope, metric, lab)]) for lab in labels])
            entry = {'dataset': ds, 'scope': scope, 'metric': metric, 'seed_scope': name, 'seeds': sorted(required),
                     'labels': labels, 'common_n': len(ids), 'expected_n': len(expected),
                     'complete_n_each_cell': {k: len(v) for k, v in vals.items()}, 'groups': {}}
            groups = {'all': ids}
            groups.update({str(g): [p for p in ids if panel.groups[(ds, p)] == g] for g in sorted({panel.groups[(ds, p)] for p in ids}, key=str)})
            for group, people in groups.items():
                Y = np.array([[vals[l][p] for l in labels] for p in people], float)
                entry['groups'][group] = A.as_json(S.summary(Y, B=Bn, seed=S.group_seed(ds, scope, metric, name, group)))
            if scope.startswith('private/') and ids:
                ha = groups.get('HA', []); nh = groups.get('NH', [])
                entry['HA_minus_NH'] = A.as_json(S.contrast(np.array([[vals[l][p] for l in labels] for p in ha]),
                                                         np.array([[vals[l][p] for l in labels] for p in nh]), B=Bn,
                                                         seed=S.group_seed(scope, metric, name, 'HA-NH')))
                if scope.startswith('private/windows/') and metric in ('auc', 'nll_bits', 'history_gain_bits', 'history_minus_twin_bits'):
                    config = scope.removeprefix('private/windows/')
                    developmental[(config, name)]['full/' + metric] = vals['full']
                if scope.startswith('private/adapt/') and metric == 'benefit_bits':
                    config, frac = scope.removeprefix('private/adapt/').rsplit('/', 1)
                    for step in ('5', '20'):
                        developmental[(config, name)]['adapt/' + frac + '/' + step] = vals[step]
            output.append(entry)
    dev = {}
    for (cfg, name), values in sorted(developmental.items()):
        # All eight endpoints must exist before drawing a combined coefficient family.
        if len(values) != 8:
            dev[cfg + '/' + name] = {'available_endpoints': len(values), 'required_endpoints': 8, 'status': 'waiting'}; continue
        ids = sorted(set.intersection(*[set(v) for v in values.values()]))
        item = {key: joint_ols(values, cov, ids, ha_only, S.group_seed(cfg, name, key), Bn)
                for key, ha_only in (('all_age_group', False), ('HA_age_duration', True))}
        item['paired_n_all_endpoints'] = len(ids)
        item['stages'] = {}
        for stage, check in (('<=2mo', lambda x:x <= 2), ('>2to<13mo', lambda x:2 < x < 13), ('>=13mo', lambda x:x >= 13)):
            people = [p for p in ids if cov.get(p, {}).get('group') == 'HA' and cov[p]['duration'] is not None and check(cov[p]['duration'])]
            item['stages'][stage] = {'n': len(people), 'means': {k: float(np.mean([v[p] for p in people])) for k, v in values.items()} if people else {}}
        dev[cfg + '/' + name] = item
    return output, dev


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--bootstrap', type=int, default=4000); a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    from . import content_time as C, private_current_time as P
    panel = A.Panel(bc_interim.load_manifest()); audits = {}; plans = {}
    for lane, module in (('content_time_v1', C), ('private_current_time_v1', P)):
        plan = A.read(BASE / lane / 'plan.json'); module.verify(plan); plans[lane] = plan; audits[lane] = []
    public_rows(panel, plans['content_time_v1'], audits['content_time_v1'])
    cov, missing = private_rows(panel, plans['private_current_time_v1'], audits['private_current_time_v1'])
    result, dev = summaries(panel, cov, a.bootstrap)
    status = {k: {'planned': len(v), 'complete': sum(x['status'] == 'complete' for x in v),
                  'failed_markers': sum(x.get('failure_marker', False) for x in v)} for k, v in audits.items()}
    value = {'time': datetime.now().astimezone().isoformat(), 'job': os.environ['SLURM_JOB_ID'], 'source_sha256': B.sha(__file__),
             'note_sha256': B.sha(NOTE), 'plans': {k: B.sha(BASE / k / 'plan.json') for k in plans}, 'units': status,
             'families': result, 'developmental': dev, 'missing_private': missing, 'provenance': audits,
             'nonhuman_entities_excluded': sorted(panel.excluded_entities), 'status': 'complete' if all(v['planned'] == v['complete'] for v in status.values()) else 'interim'}
    p = RES / 'science.json'
    if p.exists():
        b = RES / 'history' / (B.sha(p) + '.json'); b.parent.mkdir(parents=True, exist_ok=True)
        if not b.exists(): shutil.copy2(p, b)
    B.write(p, value)
    lines = ['# New fixed-model content/time and private science', '', f"Snapshot {value['time']}, CPU job {value['job']}; **{value['status']}**.", '',
             'Complete session/content/seed pairing; one independent person per row. Full matrices and group/developmental summaries are retained in `results/auditory_alignment_v3/aln34/science/science.json`. Broad windows and input masking are not neural latency estimates.', '',
             '| Lane | Complete / registered | Failed markers |', '|---|---:|---:|']
    lines += [f"| {k} | {v['complete']} / {v['planned']} | {v['failed_markers']} |" for k, v in status.items()]
    available = sum(v['common_n'] >= 3 for v in result)
    lines += ['', f'{available} declared matrix/curve families currently have at least three complete identities. No outer-test peak or model is selected.', '',
              'For each family, max-t intervals cover its cells; they do not claim correction across all models, targets or reported populations. Age/duration associations are conditional, not treatment effects. Missing coverage remains visible.']
    DOC.write_text('\n'.join(lines) + '\n')
    print(A.as_json({'units': status, 'reported_families': available, 'developmental_families': len(dev)}))


if __name__ == '__main__':
    main()
