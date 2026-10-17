"""Identity-complete interim/final efficacy aggregation for five frozen ALN3.4 lanes.

No fitting, selection, queue mutation or rewriting of unit records. See the separate
NEW_LANES_AGGREGATION_NOTE_20261017.md. CLI computation requires a Slurm CPU job.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil

import numpy as np

from .. import core
from ..sci_r1 import stats
from . import learning_budget as B

BASE = Path(core.OUT) / 'aln34'
NOTE = BASE / 'NEW_LANES_AGGREGATION_NOTE_20261017.md'
ADDENDUM = BASE / 'NEW_LANES_ANALYSIS_ADDENDUM_20261017.md'
RES = Path(core.REPO) / 'results/auditory_alignment_v3/aln34/new_lanes'
DOC = Path(core.REPO) / 'docs/auditory_alignment_v3/NEW_LANES_EFFICACY.md'
LANES = ('learning_budget_v2', 'data_inner_v1', 'adaptation_policy_v1', 'strong_fusion_v1', 'episode_training_v1')


def read(p):
    return json.loads(Path(p).read_text())


def arm(row):
    s = row['spec']
    if s['architecture'] == 'lag_local_tokens':
        return 'local'
    return s['architecture'] + '/' + s['adaptation']


def as_json(x):
    if isinstance(x, dict):
        return {str(k): as_json(v) for k, v in x.items() if k != 'T'}
    if isinstance(x, (tuple, list)):
        return [as_json(v) for v in x]
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    return x


class Panel:
    """Expected observations are registered even when production is still absent.

    A token is (seed, subject fold, content fold, recording id); mapping recordings
    to identity happens before eligibility, and each session must be present.
    """
    def __init__(self, manifest=None):
        self.manifest = manifest or {}
        self.expected = defaultdict(lambda: defaultdict(set))
        self.values = defaultdict(lambda: defaultdict(dict))
        self.groups = {}
        self.contrasts = defaultdict(set)
        self.excluded_entities = set()

    def population(self, row, pp):
        out = {}
        for pid, value in pp.items():
            ds = row['dataset']
            ident, group, kind = (pid, value.get('group'), 'human')
            if ds == 'federici':
                ident, group, kind = self.manifest[pid]
            if kind != 'human':
                self.excluded_entities.add((ds, ident)); continue
            key = (ds, ident)
            if key in self.groups and self.groups[key] != group:
                raise ValueError('identity group changed')
            self.groups[key] = group
            out[pid] = ident
        return out

    def add(self, scope, variant, mode, row, population, observed=None):
        header = (row['dataset'], scope, mode, variant)
        for pid, ident in self.population(row, population).items():
            token = (int(row['seed']), int(row['subject_fold']), int(row['content_fold'] or 0), pid)
            self.expected[header][ident].add(token)
            if observed is None or pid not in observed or observed[pid] is None:
                continue
            v = float(observed[pid])
            if not np.isfinite(v):
                raise ValueError(f'nonfinite result: {header}, {pid}')
            old = self.values[header][ident].get(token)
            if old is not None and old != v:
                raise ValueError('conflicting duplicate observation')
            self.values[header][ident][token] = v

    def compare(self, dataset, scope, mode, reference, candidate):
        self.contrasts[(dataset, scope, mode)].add((reference, candidate))

    def complete(self, header, seeds):
        result = {}
        for person, tokens in self.expected[header].items():
            wanted = {t for t in tokens if t[0] in seeds}
            if {t[0] for t in wanted} != set(seeds):
                continue
            observed = self.values[header].get(person, {})
            if not wanted.issubset(observed):
                continue
            by_seed = defaultdict(lambda: defaultdict(list))
            for token in sorted(wanted):
                by_seed[token[0]][token[2]].append(observed[token])
            result[person] = float(np.mean([np.mean([np.mean(v) for v in d.values()]) for d in by_seed.values()]))
        return result

    def summarise(self, Bn=4000):
        output = []
        for family, pairs in sorted(self.contrasts.items()):
            ds, scope, mode = family
            variants = sorted({v for pair in pairs for v in pair})
            required = {v: {t[0] for ts in self.expected[(ds, scope, mode, v)].values() for t in ts} for v in variants}
            allseeds = sorted(set.union(*required.values()))
            scopes = [(str(s), {s}) for s in allseeds]
            if len(allseeds) > 1:
                scopes.append(('complete_seed_mean', set(allseeds)))
            for seed_scope, seeds in scopes:
                # A representative single-seed arm must not enter a three-seed contrast.
                allowed = [(a, b) for a, b in sorted(pairs) if seeds <= required[a] and seeds <= required[b]]
                if not allowed:
                    continue
                values = {v: self.complete((ds, scope, mode, v), seeds) for v in variants}
                labels = [b + ' versus ' + a for a, b in allowed]
                per_pair = [set(values[a]) & set(values[b]) for a, b in allowed]
                common = sorted(set.intersection(*per_pair))
                entry = {'dataset': ds, 'scope': scope, 'readout': mode, 'seed_scope': seed_scope,
                         'evidence_origin': 'reused historical baseline; not a new training result' if scope == 'budget_models/historical_selected' else 'new production intervention',
                         'seeds': sorted(seeds), 'direction': 'positive = reference minus candidate true NLL, bits/query',
                         'labels': labels, 'paired_n_each_contrast': dict(zip(labels, map(len, per_pair))),
                         'common_identity_n': len(common), 'expected_identity_n': len(set.union(*[set(self.expected[(ds, scope, mode, v)]) for v in variants])),
                         'complete_n_per_variant': {v: len(values[v]) for v in variants}, 'groups': {}}
                groups = {'all': common}
                groups.update({str(g): [p for p in common if self.groups[(ds, p)] == g] for g in sorted({self.groups[(ds, p)] for p in common}, key=str)})
                for group, people in groups.items():
                    Y = np.array([[values[a][p] - values[b][p] for a, b in allowed] for p in people], float)
                    seed = stats.group_seed('ALN34NEW', ds, scope, mode, seed_scope, group)
                    entry['groups'][group] = as_json(stats.summary(Y, B=Bn, seed=seed))
                if scope.startswith(('policy/', 'episode/', 'private_episode/')):
                    entry['group_by_intervention'] = group_interactions(values, allowed, groups, labels, Bn,
                        stats.group_seed('ALN34GROUP', ds, scope, mode, seed_scope))
                output.append(entry)
        return output


def group_interactions(values, allowed, groups, labels, Bn, seed):
    """Direct difference of paired individual changes, with joint group resampling."""
    names = sorted(k for k in groups if k != 'all'); contrasts = {}; family = {}
    matrices = {g:np.array([[values[a][p]-values[b][p] for a,b in allowed] for p in groups[g]],float) for g in names}
    indices = {g:stats.draws(len(groups[g]),Bn,seed+i) for i,g in enumerate(names) if len(groups[g])>=3}
    for i,a in enumerate(names):
        for b in names[i+1:]:
            key = a+' minus '+b
            v = stats.contrast(matrices[a],matrices[b],B=Bn,seed=seed,
                               idx_a=indices.get(a),idx_b=indices.get(b))
            if 'T' in v:
                for j,label in enumerate(labels):family[key+' / '+label]=(v['est'][j],v['se'][j],v['T'][:,j])
            contrasts[key] = as_json(v)
    return {'direction':'group A minus group B of paired individual benefits', 'comparisons':contrasts,
            'joint_simultaneous_family':as_json(stats.family_maxt(family))}


def source(eid, digest=None):
    p = Path(core.OUT) / 'units' / f'{eid}.json'
    if digest is not None and B.sha(p) != digest:
        raise ValueError('frozen baseline record drift: ' + eid)
    r = read(p)
    if r['status'] != 'complete' or r.get('truncated'):
        raise ValueError('source incomplete')
    return r


def production(lane, unit, plan_sha, audit):
    eid = unit.get('experiment_id', unit.get('id'))
    p = BASE / lane / 'units' / f'{eid}.json'
    item = {'id': eid, 'status': 'missing'}
    audit.append(item)
    if not p.exists():
        item['failure_marker'] = p.with_name(eid + '.FAILED.json').exists()
        return None
    r = read(p); item.update(status=r.get('status'), sha256=B.sha(p))
    if r.get('status') != 'complete':
        return None
    if r.get('probe') or r.get('truncated'):
        raise ValueError('probe/truncation in production: ' + eid)
    if r.get('row', r.get('unit')) != unit:
        raise ValueError('unit row differs from frozen plan: ' + eid)
    if 'family_id' in unit and r.get('code_hash') != core.code_hash(unit['family_id']):
        raise ValueError('production training code hash mismatch: ' + eid)
    actual = r.get('plan_sha256', r.get('execution', {}).get('plan_sha256'))
    if actual != plan_sha:
        raise ValueError('production plan hash mismatch: ' + eid)
    return r


def standard(ev, mode):
    return {p: v[mode + '/regular']['logloss_bits'] for p, v in ev['per_participant'].items()}


def add_risks(panel, scope, variants, row, population, comparisons):
    for mode in ('native', 'unified'):
        for name, value in variants.items():
            panel.add(scope, name, mode, row, population, None if value is None else value[mode])
        for ref, cand in comparisons:
            panel.compare(row['dataset'], scope, mode, ref, cand)


def eval_risks(ev):
    return {m: standard(ev, m) for m in ('native', 'unified')}


def named_risks(pp):
    return {m: {p: v[m]['true_nll_bits'] for p, v in pp.items()} for m in ('native', 'unified')}


def budget(panel, plan, audit, lane='learning_budget_v2'):
    sha = B.sha(BASE / lane / 'plan.json')
    for row in plan['rows']:
        old = source(row['spec']['baseline_id'], plan['baselines'][row['spec']['baseline_id']]['record_sha256'])
        r = production(lane, row, sha, audit)
        variants = {'historical_selected': eval_risks(old['eval']), 'new_selected': eval_risks(r['eval']) if r else None}
        for frac in (.25, .5, 1., 2.):
            ev = next((v['eval'] for v in r['trajectory'] if v['baseline_fraction'] == frac), None) if r else None
            variants['fixed_' + str(frac)] = eval_risks(ev) if ev else None
        comp = [('historical_selected', x) for x in variants if x != 'historical_selected'] + [('fixed_1.0', 'fixed_2.0')]
        add_risks(panel, 'budget/' + arm(row), variants, row, old['eval']['per_participant'], comp)
        for condition, vals in variants.items():
            add_model_risks(panel, 'budget_models/' + condition, arm(row), vals, row, old['eval']['per_participant'])


def add_model_risks(panel, scope, name, vals, row, pop):
    for m in ('native', 'unified'):
        panel.add(scope, name, m, row, pop, None if vals is None else vals[m])


def data(panel, plan, audit, lane='data_inner_v1'):
    sha = B.sha(BASE / lane / 'plan.json')
    for row in plan['rows']:
        r = production(lane, row, sha, audit)
        if row['spec']['axis'] == 'inner_person':
            if r and r['eval'].get('outer_test_evaluated') is not False:
                raise ValueError('inner source unexpectedly evaluated outer test')
            continue
        s = row['spec']; old = source(s['baseline_id'], plan['baselines'][s['baseline_id']]['record_sha256'])
        fraction = str(s['fraction']); vals = eval_risks(r['eval']) if r else None
        scope = 'data/' + s['axis'] + '/' + arm(row)
        add_risks(panel, scope, {'full': eval_risks(old['eval']), fraction: vals}, row, old['eval']['per_participant'], [('full', fraction)])
        add_model_risks(panel, 'data_models/' + s['axis'] + '/' + fraction, arm(row), vals, row, old['eval']['per_participant'])


def adapt(panel, plan, audit, lane='adaptation_policy_v1'):
    sha = B.sha(BASE / lane / 'plan.json')
    for unit in plan['rows']:
        row = unit['outer_source']['row']; old = source(row['experiment_id'], unit['outer_source']['record_sha256'])
        r = production(lane, unit, sha, audit)
        variants = {'base': named_risks({p: v['base'] for p, v in r['per_participant'].items()}) if r else None}
        for kind in unit['adapters']:
            for f in unit['support']:
                key = f'{kind}|{f}'
                variants[key] = named_risks({p: v['policies'][key] for p, v in r['per_participant'].items()}) if r else None
        add_risks(panel, 'policy/' + arm(row), variants, row, old['eval']['per_participant'], [('base', k) for k in variants if k != 'base'])


def fusion(panel, plan, audit, lane='strong_fusion_v1'):
    sha = B.sha(BASE / lane / 'plan.json')
    for unit in plan['rows']:
        src = unit['models']['local']['outer']; row = src['row']; old = source(row['experiment_id'], src['record_sha256'])
        r = production(lane, unit, sha, audit)
        for which in ('cb_pre', 'cb_random', 'reve_pre'):
            for mode in ('native', 'unified'):
                variants = {k: None for k in ('local_direct', 'fm_direct', 'strong_single', 'probability', 'sc_local', 'common_linear', 'residual')}
                if r:
                    outer = r['stages']['outer']['comparisons']; decision = r['decisions'][mode]
                    pick = decision['strong_single']
                    records = {k: outer[which][k] for k in ('local_direct', 'fm_direct')}
                    records['strong_single'] = outer[which]['local_direct'] if pick == 'local' else outer[pick]['fm_direct']
                    records.update({k: outer[which][v] for k, v in decision['pairs'][which].items()})
                    variants = {k: {p: x['true_nll_bits'] for p, x in v['per_person'][mode].items()} for k, v in records.items()}
                scope = 'fusion/' + which
                for k, vals in variants.items():
                    panel.add(scope, k, mode, row, old['eval']['per_participant'], vals)
                for candidate in ('probability', 'sc_local', 'common_linear', 'residual'):
                    for reference in ('local_direct', 'fm_direct', 'strong_single'):
                        panel.compare(row['dataset'], scope, mode, reference, candidate)


def episode(panel, plan, audit, lane='episode_training_v1'):
    sha = B.sha(BASE / lane / 'plan.json')
    for unit in plan['rows']:
        src = unit['outer']; row = src['row']; old = source(row['experiment_id'], src['record_sha256'])
        r = production(lane, unit, sha, audit)
        for frac in ('0.1', '0.3'):
            variants = {'source_no_adaptation': None, 'ordinary_selected': None, 'episode_selected': None}
            if r:
                variants['source_no_adaptation'] = named_risks(r['stages']['outer']['candidates']['source'][frac]['0']['per_participant'])
                for regime in ('ordinary', 'episode'):
                    variants[regime + '_selected'] = named_risks(r['choices'][regime][frac]['outer']['per_participant'])
            for regime in ('source', 'ordinary', 'episode'):
                for steps in (0, 5, 20):
                    key = f'fixed_{regime}/{steps}'
                    variants[key] = named_risks(r['stages']['outer']['candidates'][regime][frac][str(steps)]['per_participant']) if r else None
            pairs = [('source_no_adaptation', k) for k in variants if k != 'source_no_adaptation']
            pairs += [('ordinary_selected', 'episode_selected')]
            pairs += [(f'fixed_ordinary/{step}', f'fixed_episode/{step}') for step in (0,5,20)]
            add_risks(panel, 'episode/' + arm(row) + '/support_' + frac, variants, row, old['eval']['per_participant'], pairs)


def model_contrasts(panel):
    families = {(ds, scope, mode) for ds, scope, mode, v in panel.expected if scope.startswith(('budget_models/', 'data_models/'))}
    for ds, scope, mode in families:
        names = {v for d, s, m, v in panel.expected if (d, s, m) == (ds, scope, mode)}
        for name in sorted(names - {'local'}):
            if 'local' in names:
                panel.compare(ds, scope, mode, 'local', name)
        for arch in ('cbramod', 'reve'):
            a, b = arch + '/random_full', arch + '/pretrained_full'
            if {a, b} <= names:
                panel.compare(ds, scope, mode, a, b)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--bootstrap', type=int, default=4000); args = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'Slurm required'
    os.umask(0o077)
    from .. import bc_interim
    from . import learning_budget_v2 as LB, data_inner as DI, adaptation_policy as DA, strong_fusion as SF, episode_training as EP
    modules = (LB, DI, DA, SF, EP)
    panel = Panel(bc_interim.load_manifest()); provenance = {}; statuses = {}
    for lane, module, parser in zip(LANES, modules, (budget, data, adapt, fusion, episode)):
        p = BASE / lane / 'plan.json'; plan = read(p)
        (module.verify_plan if lane == 'learning_budget_v2' else module.verify)(plan)
        audit = []; parser(panel, plan, audit)
        provenance[lane] = {'plan_sha256': B.sha(p), 'units': audit}
        statuses[lane] = {'planned': len(audit), 'complete': sum(v['status'] == 'complete' for v in audit),
                          'failed_markers': sum(v.get('failure_marker', False) for v in audit)}
    model_contrasts(panel)
    families = panel.summarise(args.bootstrap)
    result = {'time': datetime.now().astimezone().isoformat(), 'job': os.environ['SLURM_JOB_ID'],
              'source_sha256': B.sha(__file__), 'note_sha256': B.sha(NOTE), 'addendum_sha256':B.sha(ADDENDUM), 'bootstrap': args.bootstrap,
              'status': 'complete' if all(x['complete'] == x['planned'] for x in statuses.values()) else 'interim',
              'units': statuses, 'families': families, 'provenance': provenance,
              'excluded_nonhuman_entities': sorted(panel.excluded_entities)}
    previous = RES / 'efficacy.json'
    if previous.exists():
        backup = RES / 'history' / (B.sha(previous) + '.json')
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(previous, backup)
    B.write(previous, result)
    lines = ['# ALN3.4 new-lane efficacy snapshot', '', f"Generated {result['time']} by CPU job {result['job']}. Status: **{result['status']}**.", '',
             'Complete identity pairing is required; seeds and folds do not increase n. Intervals condition on fitted models. Interim snapshots are not sequential significance tests. `historical_selected` tables reuse existing baseline records; they are not new budget results and do not replace the frozen ADDENDUM_11 analysis.', '',
             '| Lane | Complete / registered | Failed markers |', '|---|---:|---:|']
    lines += [f"| {k} | {v['complete']} / {v['planned']} | {v['failed_markers']} |" for k, v in statuses.items()]
    lines += ['', 'Positive values mean lower true query NLL than the named reference. Native and unified are distinct families. All group summaries and coverage are in `results/auditory_alignment_v3/aln34/new_lanes/efficacy.json`.', '']
    shown = 0
    for f in families:
        v = f['groups']['all']
        if f['common_identity_n'] < 3 or 'est' not in v:
            continue
        shown += 1
        lines += [f"## {f['scope']} · {f['readout']} · {f['seed_scope']}", '', f"Common paired identities: {f['common_identity_n']} / {f['expected_identity_n']}.", '',
                  '| Contrast | ΔR bits/query | Simultaneous 95% interval |', '|---|---:|---:|']
        for j, label in enumerate(f['labels']):
            lines.append(f"| {label} | {v['est'][j]:+.4f} | [{v['band_low'][j]:+.4f}, {v['band_high'][j]:+.4f}] |")
        lines.append('')
    if not shown:
        lines.append('No declared family has three identities with every required paired cell yet. No efficacy estimate is promoted from incomplete cells.')
    DOC.write_text('\n'.join(lines) + '\n')
    print(json.dumps({'status': result['status'], 'units': statuses, 'reported_families': shown}))


if __name__ == '__main__':
    main()
