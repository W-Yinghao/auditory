import json
from pathlib import Path
from auditory_alignment_v3.aln35 import bridge_factor_fleet as L


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(L, 'BASE', tmp_path)
    monkeypatch.setattr(L, 'PLAN', tmp_path / 'fleet_plan.json')
    plan = {'rows': [{'key': k, 'cache': str(tmp_path / 'cache' / k)} for k in L.F.KEYS],
            'bootstrap_key': 'dtu_AP', 'source_plan_sha256': 'planhash',
            'sources': {'auditory_alignment_v3/aln35/bridge_factor_extract.py': 'extracthash'}}
    write(L.PLAN, plan)
    return plan


def finish(plan, key, tmp_path):
    unit = next(u for u in plan['rows'] if u['key'] == key)
    rec = {'status': 'complete', 'key': key, 'plan_sha256': 'planhash', 'extract_code_sha256': 'extracthash'}
    write(tmp_path / 'extract_receipts' / (key + '.json'), rec)
    write(Path(unit['cache']) / 'complete.json', rec)


def test_bootstrap_gates_remaining_three_and_no_jobs_submitted(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch)
    assert L.fleet_status()['ready'] == 0
    assert L.fleet_status()['state'] == 'bootstrap_dtu_AP_receipt_required'
    finish(plan, 'dtu_AP', tmp_path)
    status = L.fleet_status()
    assert status['state'] == 'ready' and status['ready'] == 3 and status['slots'] == 1
    assert status['submit'] == ['slurm/aln35_bridge_fleet.sbatch', '--max-units', '1']


def test_partial_or_failed_cache_is_never_overwritten_or_retried(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch); finish(plan, 'dtu_AP', tmp_path)
    Path(plan['rows'][1]['cache']).mkdir(parents=True)
    assert L.fleet_status()['state'] == 'partial_cache_or_active_worker'
    assert L.fleet_status()['ready'] == 0
    write(tmp_path / 'fleet_failures' / 'dtu_XM.json', {'status': 'technical_failed'})
    assert L.fleet_status()['state'] == 'failed_unit_requires_review'


def test_all_four_receipts_mark_gpu_complete_and_cpu_ready(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch)
    for key in L.F.KEYS: finish(plan, key, tmp_path)
    status = L.fleet_status()
    assert status['state'] == 'complete' and status['remaining'] == 0
    assert status['CPU_analysis_ready']
