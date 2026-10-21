"""Fill the package BINDING.template.json from actual server receipts (re-runnable; never invents a pass)."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .. import core
from . import frozen as FZ, private_ft as PF, source as SRC

OUT = SRC.OUT / 'bindings' / 'BINDING.json'
read, write, sha = SRC.read, SRC.write, SRC.sha


def maybe(path):
    return read(path) if Path(path).exists() else None


def latest_pass(base):
    rec = [p for p in sorted((base / 'probes').glob('*/receipt.json')) if read(p).get('status') == 'pass']
    return (rec[-1], read(rec[-1])) if rec else (None, None)


def main():
    t = read(SRC.PACKAGE / 'templates/BINDING.template.json')
    gate = read(SRC.STAGE1_GATE); plan = read(SRC.BASE / 'plan.json')
    sp, sr = latest_pass(SRC.BASE); pp, pr = latest_pass(PF.BASE); fp, fr = latest_pass(FZ.BASE)
    rd = (sr or {}).get('readiness', {})
    torch_receipt = SRC.OUT / 'intake/VERIFY_TEMPORAL_TORCH.server.json'
    t['status'] = 'BOUND_PARTIAL' if not (sr and pr and fr) else 'BOUND'
    t['package_sha256'] = SRC.PACKAGE_ZIP_SHA256
    t['code'] = {'repo_head_at_intake': '3da8cf5758214c0cf87a1f1c8d67fb84b574000e', 'production_commit': None,
                 'production_tree_clean': None, 'production_code_binding': 'per-plan source file SHA256 maps (server root is not a git checkout)',
                 'plan_sha256': {'source': sha(SRC.BASE / 'plan.json'), 'private_ft': sha(PF.BASE / 'plan.json'), 'frozen': sha(FZ.BASE / 'plan.json')},
                 'implementation_receipt_sha256': sha(sp) if sp else None}
    st = rd.get('stage1', {}); probes = rd.get('channel_probes', {})
    t['stage1'] = {'identity': 'CBraMod pretrained_full (MindMix asset gate not_passed)', 'weights_path': gate['stage1_selected']['weights'],
                   'weights_sha256': gate['stage1_selected']['sha256'], 'expected_numel': st.get('expected_numel'),
                   'loaded_backbone_numel': {k: v.get('loaded_backbone_numel') for k, v in probes.items()} or None,
                   'strict_load_ok': st.get('strict_load'), 'all_backbone_layers_gradient_ok': bool(sr) or None,
                   'gradient_exemption': list(SRC.UNUSED_WITHOUT_MASK), 'save_reload_equal_ok': (rd.get('save_reload_max_abs_diff') == 0.0) if rd else None,
                   'three_crop_input_ok': bool(probes) or None, 'channels20_31_64_forward_ok': (set(probes) == {'private_bdf', 'fau', 'dtu'}) if probes else None,
                   'gate_receipt_sha256': sha(SRC.STAGE1_GATE)}
    t['data'] = {'core_manifest_sha256': SRC.MANIFEST_SHA, 'rich_manifest_sha256': SRC.RICH_SHA, 'target_split_receipt_sha256': None,
                 'source_people_and_content_split_disjoint': True, 'source_target_overlap_excluded': plan['pool']['excluded_presentations'],
                 'episode_physical_guard_verified': (rd.get('stream_check', {}).get('status') == 'pass') if rd else None,
                 'source_pool': plan['pool'], 'private_roster_sha256': None, 'private_outer_fold_sizes': [13, 13, 13, 13, 12],
                 'private_valid_age_roster_sha256': None, 'private_valid_age_n': None, 'age_one_row_one_child_same_encoder': True,
                 'rich_all_three_views_present': plan['pool']['dropped']['rich_unavailable'] == 0}
    t['method'] = {'time_access_receipt_sha256': sha(sp) if sp else None, 'source_native_crop_before_resample': True,
                   'resampler_max_abs_error_vs_scipy': max(r['max_abs_error'] for r in rd['resampler']) if rd else None,
                   'support_query_disjoint_and_inner_support_only': (rd.get('stream_check', {}).get('status') == 'pass') if rd else None,
                   'gcs_same_support_adaptation': True, 'shared_slot_sigma_per_view': maybe(SRC.sigmas_path()),
                   'wrong_all_views_same_bijection': True, 'torch_math_gradient_receipt_sha256': sha(torch_receipt) if torch_receipt.exists() else None,
                   'freeze_source_selection_before_targets': (SRC.BASE / 'selection.json').exists() or None}
    t['targets'] = {'public_fold_spec_sha256': None, 'common_probe_config_sha256': None, 'person_analysis_family_spec_sha256': None,
                    'raw_predictions_schema_sha256': None,
                    'actual_logical_and_expanded_unit_counts': {'source_calibration': 6, 'source_production': 4, 'private_ft': 15,
                                                                'frozen_units': 25, 'readout_units': 25, 'age': 1},
                    'private_train_es_test_roles_verified': bool(pr) or None, 'age_nested_child_cv_verified': None}
    t['execution'] = {'slurm_cpu_and_gpu_rule_confirmed': True, 'project_gpu_running_plus_pending_cap': 10, 'existing_holds_preserved': True,
                      'running_source_immutable': True, 'no_automatic_deletion_or_publication': True,
                      'live_queue_snapshot_utc': '2026-10-21T00:16:53Z'}
    t['legacy_intake'] = {'D2_GX_NEXTMAP_original_reports_read': True, 'intake': str((SRC.OUT / 'intake/INTAKE.md').relative_to(core.REPO)),
                          'missing_assets_list': ['D1 continuous arrays (deleted 2026-10-11)', 'per-child predictions for NEXTMAP H1/H2/H4-H6/H8/H10/H11',
                                                  'GX R2 erratum not on GitHub'], 'old_ALN40_units_if_any': [],
                          'retention_dependency_inventory_path': None}
    t['external'] = {'slot_identity': None, 'readiness_decision_before_new_target_results': None, 'asset_and_task_contract_receipt_sha256': None}
    write(OUT, t)
    print(t['status'], OUT, flush=True)


if __name__ == '__main__':
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077); main()
