"""Analysis of S35_EPISODE_REPLICATION_S3407 with the unchanged S35_SUPPORT_SUMMARY_v1.1 machinery (Slurm only).

Reuses support_experiment_summary's frozen roster/geometry checks, process_episode extraction and the
package reference bootstrap (REF.analyze). Only the seed label (3407) and family ids differ. Prints the
seed-3401 values of the same panels from the complete 1050758 summary side by side. No refit.
"""
import json
import os
from pathlib import Path

from auditory_alignment_v3.aln35 import support_experiment_summary as SES, episode_pressure_s3407 as ER

REPO = SES.REPO
OUT = REPO / 'results/auditory_alignment_v3/aln35/episode_rep_s3407_v1'
DOC = REPO / 'docs/auditory_alignment_v3/aln35/EPISODE_REPLICATION_S3407_RESULTS.md'
REFERENCE = REPO / 'results/auditory_alignment_v3/aln35/support_summary_v1/snapshots/job_1050758_20261020T015908062290Z/summary.json'


def relabel(row):
    # SES hard-codes the seed-3401 label in both `seed` and provenance `source_seed_ids`; every unit here is seed 3407.
    prov = dict(row['provenance'])
    if 'source_seed_ids' in prov:
        SES.require(prov['source_seed_ids'] == [3401], 'unexpected source seed label')
        prov['source_seed_ids'] = [3407]
    return dict(row, seed=3407, provenance=prov)


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'run under Slurm'
    plan, plan_sha = SES.read(ER.PLAN)
    ER.verify(plan)
    SES.require(all(u['seed'] == 3407 and u['source']['inner']['seed'] == 3407 for u in plan['rows']), 'non-3407 unit in plan')
    geometry_path = SES.ROOT / 'support_coverage_v1/restricted_support_bindings.json'
    geometry, geometry_sha = SES.read(geometry_path)
    support_plan, _ = SES.read(SES.ROOT / 'support_coverage_v1/plan.json')
    SES.require(geometry_sha == support_plan['query_binding_sha256'], 'frozen support geometry changed')
    export = SES.Export(SES.identity_roster(geometry), geometry)
    for unit in plan['rows']:
        for kind in ('episode_fixed20', 'episode_selected'):
            SES.panel_membership(export, kind, unit, unit['id'])
    inventory = []
    for unit in plan['rows']:
        path = ER.BASE / 'units' / f'{unit["id"]}.json'
        entry = {'id': unit['id'], 'state': 'missing'}
        inventory.append(entry)
        if not path.is_file():
            continue
        record, sha = SES.read(path)
        SES.valid_record(record, unit, plan_sha)
        ok = SES.transaction(export, SES.process_episode, record, path, sha)
        entry.update(state='complete' if ok else 'invalid_record', sha256=sha)
        if ok:
            for panel in export.panels.values():
                if unit['id'] in panel['expected_units']:
                    panel['available_units'].append(unit['id'])
    reference = {f['family_id']: f for f in json.loads(REFERENCE.read_text())['families']}
    families = []
    for panel in sorted(export.panels.values(), key=lambda p: p['panel_id']):
        spec = SES.build_spec(panel, 'nll_bits', export.rosters)
        original_id = spec['family_id']
        spec['family_id'] += '__seed3407'
        spec['required_seeds'] = [3407]
        rows = [relabel(r) for r in panel['rows'] if r['metric'] == 'nll_bits']
        result = SES.REF.analyze(rows, spec) if rows else SES.empty_result(spec)
        result.update(panel_id=panel['panel_id'], expected_unit_count=len(set(panel['expected_units'])),
                      complete_unit_count=len(set(panel['available_units'])), seed3401_family=original_id)
        result.pop('identity_values', None)
        families.append(result)
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {'job': os.environ['SLURM_JOB_ID'], 'plan_sha256': plan_sha, 'inventory': inventory,
               'errors': export.errors, 'families': families,
               'note': 'seed 3407 sources; frozen v1 sampling streams; DTU 44; intervals per family as in S35 v1.1'}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2, default=float) + '\n')
    lines = ['# Episode pressure-100 replication with seed-3407 sources (DTU, local)', '',
             f"Analysis job {summary['job']}; plan `{plan_sha[:16]}…`; complete units "
             f"{sum(e['state'] == 'complete' for e in inventory)}/10; errors {len(export.errors)}.", '',
             'True-query NLL bits/query; positive = first-named arm better; simultaneous 95% intervals within family '
             '(identity bootstrap, fixed original SE, max-|z*|; same machinery as 1050758). Seed-3401 column is the '
             'complete 1050758 value of the same panel/contrast.', '',
             '| Panel | Contrast | seed 3407 | seed 3401 (1050758) |', '|---|---|---|---|']
    for f in families:
        ref = {c['id']: c for c in reference.get(f['seed3401_family'], {}).get('contrasts', [])}
        for c in f.get('contrasts', []):
            def fmt(x):
                if not x or x.get('estimate') is None:
                    return 'NA'
                lo, hi = x['simultaneous_ci'] or (None, None)
                return f"{x['estimate']:+.4f} [{lo:+.4f}, {hi:+.4f}]" if lo is not None else f"{x['estimate']:+.4f}"
            lines.append(f"| {f['panel_id']} | {c['id']} | {fmt(c)} | {fmt(ref.get(c['id']))} |")
    DOC.write_text('\n'.join(lines) + '\n')
    print(json.dumps({'complete': sum(e['state'] == 'complete' for e in inventory), 'errors': export.errors}, indent=2))


if __name__ == '__main__':
    main()
