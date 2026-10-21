"""ALN4.2 intake: INTAKE_AND_BINDING.json and R2_REUSE_INDEX.json from the live server state (read-only, CPU).

Every registered R2 unit (ALN4.1 seeds 3407 / 3413: source, private CE, frozen; ALN3.6 seed 3407: FAU group, feature banks,
AP/APwrong) and the R2-attached CPU plans (support, cross-stimulus) are listed with the full plan hash, the code hashes the
plan froze, the result file hash when complete, and the action: reuse a complete unit, or await the unit in its registered
fleet lane. Nothing is resubmitted; the live queue is observed with squeue only.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

from .. import core
from ..aln41 import r2 as R41, source as SRC, private_ft as PF, frozen as FZ, support as SU, cross_stim as XS
from ..aln36 import r2 as R36, r2_apwrong as RW, fau_group as G, public_features as F

OUT = Path(core.OUT) / 'aln42' / 'intake'
PKG = Path(core.REPO) / 'AUDITORY_ALN4_SERVER_PACKAGE_v4_2_20261021'
read, write, sha = SRC.read, SRC.write, SRC.sha


def unit_rows(base, rows, key, meta):
    out = []
    for r in rows:
        uid = r[key]; p = base / 'units' / f'{uid}.json'; failed = base / 'units' / f'{uid}.FAILED.json'
        status = 'complete' if p.exists() else ('failed_marker' if failed.exists() else 'not_complete')
        out.append({'original_unit_id': uid, 'original_result_keys': str(p.relative_to(core.REPO)) if status == 'complete' else None,
                    **meta(r), 'plan_sha256': sha(base / 'plan.json'), 'output_sha256': sha(p) if status == 'complete' else None,
                    'status': status, 'action': {'complete': 'reuse', 'not_complete': 'await_registered_lane',
                                                  'failed_marker': 'technical_review_existing_receipts'}[status]})
    return out


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    now = datetime.now(timezone.utc).isoformat()
    index, plans = [], {}
    for seed in R41.SEEDS:
        with R41.seeded(seed):
            _, rows = SRC.all_rows(); sp = read(SRC.BASE / 'plan.json')
            index += unit_rows(SRC.BASE, rows, 'id', lambda r: {'package': 'ALN4.1', 'stage': 'source', 'arm': r['arm'], 'seed': r['seed'], 'fold': None,
                                                                 'input_hashes': {'stream': sp['stream_sha256'], 'panels': sp['panels_sha256']},
                                                                 'code_hashes': {**sp['sources'], **sp['r2_sources']}})
            pp = read(PF.BASE / 'plan.json')
            index += unit_rows(PF.BASE, pp['rows'], 'id', lambda r: {'package': 'ALN4.1', 'stage': 'private_ce', 'arm': r['arm'], 'seed': r['seed'],
                                                                     'fold': r['outer_fold'], 'input_hashes': {'source_plan': pp['source_plan_sha256']},
                                                                     'code_hashes': pp['sources']})
            fp = read(FZ.BASE / 'plan.json')
            index += unit_rows(FZ.BASE, fp['rows'], 'id', lambda r: {'package': 'ALN4.1', 'stage': 'frozen', 'arm': r['arm'], 'seed': r['seed'],
                                                                     'fold': r['content_fold'], 'dataset': r['dataset'],
                                                                     'input_hashes': {'source_plan': fp['source_plan_sha256']}, 'code_hashes': fp['sources']})
            plans[f'aln41_r2_seed{seed}'] = {k: sha(b / 'plan.json') for k, b in (('source', SRC.BASE), ('private_ft', PF.BASE), ('frozen', FZ.BASE))}
    xp = read(XS.OUT / 'plan.json')
    index += unit_rows(XS.OUT, xp['rows'], 'id', lambda r: {'package': 'ALN4.1', 'stage': 'cross_stim_frozen', 'arm': r['arm'], 'seed': r['seed'],
                                                            'fold': None, 'input_hashes': {'records': xp['records_sha256'], 'decision': xp['decision_sha256']},
                                                            'code_hashes': xp['sources']})
    with R36.seeded():
        gp = read(G.PLAN)
        index += unit_rows(G.BASE, gp['rows'], 'experiment_id', lambda r: {'package': 'ALN3.6', 'stage': 'fau_group', 'arm': r['tool'], 'seed': r['seed'],
                                                                           'fold': r['content_fold'], 'excluded_group': r['excluded_group'],
                                                                           'input_hashes': {'binding': r['binding_sha256']}, 'code_hashes': gp['sources']})
        fp = read(F.PLAN)
        index += unit_rows(F.BASE, fp['rows'], 'id', lambda r: {'package': 'ALN3.6', 'stage': 'public_features', 'arm': r['tool'], 'seed': r['seed'],
                                                               'fold': r.get('content_fold'), 'kind': r['kind'],
                                                               'input_hashes': {'source': r.get('source_record_sha256') or r.get('binding_sha256')},
                                                               'code_hashes': fp['sources']})
        plans['aln36_r2_s3407'] = {'fau_group': sha(G.PLAN), 'public_features': sha(F.PLAN), 'apwrong': sha(RW.PLAN),
                                   'private_features': sha(R36.PFE.PLAN) if R36.PFE.PLAN.exists() else 'NOT_YET_CREATED (after the 10 targets)'}
    ap = read(RW.PLAN)
    index += unit_rows(RW.OUT, ap['units'], 'unit_id', lambda r: {'package': 'ALN3.6', 'stage': 'apwrong_' + r['stage'], 'arm': r.get('arm'), 'seed': RW.SEED,
                                                                  'fold': (r.get('adapter_row') or {}).get('subject_fold'),
                                                                  'input_hashes': {'plan_inputs': len(ap['input_hashes'])}, 'code_hashes': ap['code_hashes']})
    write(OUT / 'R2_REUSE_INDEX.json', {'version': 'ALN42_R2_REUSE_INDEX_v1', 'observed_utc': now, 'units': index,
                                        'counts': {s: sum(1 for u in index if u['status'] == s) for s in ('complete', 'not_complete', 'failed_marker')},
                                        'rule': 'complete -> reuse; not complete -> await the registered fleet lane; nothing resubmitted'})
    q = subprocess.run(['squeue', '-u', os.environ['USER'], '-h', '-o', '%i|%j|%T|%q'], capture_output=True, text=True).stdout.splitlines()
    mine = [l for l in q if '|c3_' in l]
    insp = read(OUT / 'inspect_existing_state.json') if (OUT / 'inspect_existing_state.json').exists() else {}
    ext = Path(core.OUT) / 'aln41/intake/EXTERNAL_SLOT_DECISION.json'
    body = {'template_only': False, 'package_version': '4.2', 'package_zip_sha256': sha(Path(core.REPO) / 'AUDITORY_ALN4_SERVER_PACKAGE_v4_2_20261021.zip'),
            'design_baseline': '5d2960eee61a75c048f6b6ee3cef8427d945c3cd', 'observed_utc': now, 'actual_repo_path': str(core.REPO),
            'actual_repo_head': 'server working tree is not a git checkout; publication checkout private/github_publish_035/checkout HEAD '
                                + str(insp.get('repository', {}).get('head_commit')),
            'baseline_relationship': insp.get('status'), 'critical_code_comparison': 'tools/inspect_existing_state.py: '
            + str(insp.get('status')) + '; server files byte-identical to the published baseline (publish_035 verify)',
            'live_queue_observed_utc': now, 'live_queue_summary': {'project_jobs': len(mine), 'running': sum('|RUNNING|' in l for l in mine),
                                                                   'pending': sum('|PENDING|' in l for l in mine)},
            'existing_aln41_source_plan_sha256': sha(SRC.BASE / 'plan.json'), 'existing_aln41_r2_plan_sha256': plans,
            'existing_aln36_r2_plan_sha256': plans['aln36_r2_s3407'], 'existing_support_plan_sha256': sha(SU.OUT / 'plan.json'),
            'existing_cross_stim_plan_sha256': sha(XS.OUT / 'plan.json'),
            'external_slot_original_decision_path_private': str(ext.relative_to(core.REPO)), 'external_slot_original_decision_sha256': sha(ext),
            'external_route': 'pending readiness gates (MindMix per the original decision; fixed fallback Transformer-CLIP)',
            'r2_reuse_index_path': str((OUT / 'R2_REUSE_INDEX.json').relative_to(core.REPO)),
            'source_probe_panel_hash': None, 'private_audit_root': 'private/auditory_alignment_v3/aln42/event_audit',
            'public_report_root': 'docs/auditory_alignment_v3/aln42 and results/auditory_alignment_v3/aln42',
            'registered_complete_units': sum(1 for u in index if u['status'] == 'complete'),
            'registered_missing_units': sum(1 for u in index if u['status'] != 'complete'),
            'new_diagnostic_units': ['aln42/source_diag (4 arm units, 0 optimizer updates)', 'aln42/event_audit (CPU)', 'NET adapter (CPU)'],
            'confirmed_bug_scopes': [], 'authorization_note': 'deidentified person model results already authorized; no fresh confirmation for same scope',
            'notes': ['ALN4.1 R2 and ALN3.6 R2 continue unchanged in their registered lanes (no resubmission).',
                      'node51 excluded in active sbatch files after repeated uncorrectable ECC errors (receipts in aln35/fleet_v3_20261020).']}
    diag_plan = Path(core.OUT) / 'aln42/source_diag_v1/plan.json'
    if diag_plan.exists():
        body['source_probe_panel_hash'] = read(diag_plan)['panels_sha256']
    write(OUT / 'INTAKE_AND_BINDING.json', body)
    print(json.dumps({'units': len(index), **{s: sum(1 for u in index if u['status'] == s) for s in ('complete', 'not_complete', 'failed_marker')}}))


if __name__ == '__main__':
    main()
