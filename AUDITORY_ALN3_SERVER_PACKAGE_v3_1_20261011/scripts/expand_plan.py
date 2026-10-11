#!/usr/bin/env python3
"""Expand planned comparisons only. This program never submits training jobs."""
from pathlib import Path
import argparse, hashlib, itertools, json
from collections import Counter
import yaml


def matches(spec, rule):
    return all(spec.get(k) in v for k, v in rule.items())


def expand(config):
    rows = []
    for family in config['families']:
        grid = family['grid']; keys = list(grid)
        combos = itertools.product(*(grid[k] for k in keys)) if grid else [()]
        combinations = [dict(zip(keys, values)) for values in combos]
        for dataset in family['datasets']:
            ds = config['datasets'][dataset]
            folds = itertools.product(ds['subject_folds'], ds['content_folds']) if family['folded'] else [(None, None)]
            folds = list(folds)
            for chosen in combinations:
                spec = dict(config['common']); spec.pop('status', None)
                spec.update({'target': ds['default_target']})
                spec.update(family['constants']); spec.update(chosen)
                if any(matches(spec, rule) for rule in family.get('exclude', [])):
                    continue
                if spec.get('training_task') == 'selection_only':
                    spec['objective'] = 'SELECTION_CE'
                panel = any(matches(spec, rule) for rule in family.get('panel_rules', []))
                seeds = config['seed_breadth'] + (config['seed_panel_extra'] if panel else [])
                for sf, cf in folds:
                    for seed in seeds:
                        deps = list(family['logical_dependencies'])
                        if dataset == 'federici' and 'verified_identity_manifest' not in deps:
                            deps.append('verified_identity_manifest')
                        row = {'family_id': family['id'], 'dataset': dataset, 'job_kind': family['job_kind'],
                               'base_commit': config['base_commit'], 'seed': seed, 'subject_fold': sf, 'content_fold': cf,
                               'spec': spec, 'logical_dependencies': deps, 'status': 'planned_needs_binding',
                               'seed_scope': 'breadth' if seed in config['seed_breadth'] else 'panel'}
                        signature = json.dumps(row, sort_keys=True, separators=(',', ':'))
                        row['experiment_id'] = 'ALN3_' + hashlib.sha256(signature.encode()).hexdigest()[:16]
                        rows.append(row)
    ids = [row['experiment_id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate plan signatures')
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args=p.parse_args()
    config=yaml.safe_load(args.config.read_text(encoding='utf-8'))
    rows=expand(config); args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'units.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
    summary={'version':config['version'],'n_plan_records':len(rows),'by_family':dict(Counter(r['family_id'] for r in rows)),
             'by_job_kind':dict(Counter(r['job_kind'] for r in rows)),
             'by_seed_scope':dict(Counter(r['seed_scope'] for r in rows)),
             'config_sha256':hashlib.sha256(args.config.read_bytes()).hexdigest(),
             'note':'Logical comparisons, not equal-cost fits or independent samples; no jobs submitted.'}
    (args.out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
