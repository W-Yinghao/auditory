import hashlib
import json
from types import SimpleNamespace

import pytest

from private.auditory_alignment_v3.aln35 import maintain_fleet_v2 as F
from private.auditory_alignment_v3.aln34 import efficiency_loop_v3 as E


def test_compatibility_receipt_and_source_drift(tmp_path, monkeypatch):
    paths = {}
    for key in ('receipt', 'module_source', 'plan'):
        path = tmp_path / key
        path.write_text(json.dumps({'status': 'pass'}))
        paths[key] = path
    entry = {'phase': 'episode'}
    for key, expected in (('receipt', 'receipt_sha256'), ('module_source', 'module_sha256'), ('plan', 'plan_sha256')):
        entry[key] = str(paths[key])
        entry[expected] = hashlib.sha256(paths[key].read_bytes()).hexdigest()
    policy = tmp_path / 'policy.json'
    policy.write_text(json.dumps({'device': 'Tesla V100-PCIE-32GB', 'phases': [{'phase': 'episode', 'status': 'pass'}],
                                 'allowed_lanes': {'s35_episode': entry}}))
    monkeypatch.setattr(E, 'V100_POLICY', policy)
    assert E.v100_allowed('s35_episode')
    assert not E.v100_allowed('s35_matched')
    paths['module_source'].write_text('changed')
    assert not E.v100_allowed('s35_episode')


def test_fast_preference_and_verified_broad_fallback(monkeypatch):
    monkeypatch.setattr(E, 'v100_allowed', lambda lane: lane == 's35_episode')
    assert E.route('s35_episode', {}, now=1000)['partitions'] == ['A100', 'L40S', 'A40', 'A30', 'V100']
    assert 'V100' not in E.route('unverified', {}, now=1000)['partitions']
    assert 'V100' not in E.route('s35_episode', {}, now=1000, oom_only=True)['partitions']
    fresh = {'epoch': 1000, 'hardware': {'idle_partitions': ['A100', 'V100']}}
    assert E.route('s35_episode', fresh, now=1001)['partitions'] == ['A100', 'L40S']
    assert 'V100' in E.route('s35_episode', fresh, now=1001, force_broad=True)['partitions']
    assert 'P100' not in E.BROAD


def setup_migration(monkeypatch):
    monitor = SimpleNamespace(state={}, event=lambda *a, **k: None)
    journal = {'123': {'id': '123', 'name': 'c3_s35episode', 'lane': 's35_episode'}}
    lane = {'name': 'c3_s35episode', 'lane': 's35_episode', 'state': 'ready', 'ready': 5}
    job = {'id': '123', 'name': lane['name'], 'qos': 'runfill', 'state': 'PENDING',
           'reason': 'Priority', 'partition': 'A100,L40S,A40,A30', 'gres': 'gres/gpu:1'}
    cancelled, launched = [], []
    monkeypatch.setattr(F.E, 'v100_allowed', lambda lane: True)
    monkeypatch.setattr(F.E, 'query_jobs', lambda: [])
    monkeypatch.setattr(F.E, 'write', lambda *a: None)
    monkeypatch.setattr(F, 'cancel', lambda command: cancelled.append(command))
    monkeypatch.setattr(F, 'launch', lambda *a, **k: launched.append(k) or '456')
    return monitor, journal, lane, job, cancelled, launched


def test_pending_replacement_is_scoped_and_opens_v100(monkeypatch):
    monitor, journal, lane, job, cancelled, launched = setup_migration(monkeypatch)
    assert F.migrate_pending([job], [lane], monitor, journal)
    assert cancelled == [['scancel', '--state=PENDING', '123']]
    assert launched == [{'force_broad': True, 'replaces': '123'}]
    assert monitor.state['v100_adopted_pending'] == {'123': '456'}


@pytest.mark.parametrize('change', [{'state': 'RUNNING'}, {'name': 'other_project'},
                                   {'qos': 'normal'}, {'partition': 'A100,L40S'},
                                   {'partition': 'A100,V100'}])
def test_never_replaces_running_foreign_or_fast_trial(monkeypatch, change):
    monitor, journal, lane, job, cancelled, launched = setup_migration(monkeypatch)
    job.update(change)
    assert not F.migrate_pending([job], [lane], monitor, journal)
    assert cancelled == launched == []


def test_pending_to_running_race_never_launches_duplicate(monkeypatch):
    monitor, journal, lane, job, cancelled, launched = setup_migration(monkeypatch)
    monkeypatch.setattr(F.E, 'query_jobs', lambda: [{**job, 'state': 'RUNNING'}])
    assert not F.migrate_pending([job], [lane], monitor, journal)
    assert cancelled == [['scancel', '--state=PENDING', '123']]
    assert not launched


def test_no_requeue_while_project_uses_ten_gpus(monkeypatch):
    monitor, journal, lane, job, cancelled, launched = setup_migration(monkeypatch)
    running = [{**job, 'id': str(i), 'state': 'RUNNING'} for i in range(10)]
    assert not F.migrate_pending([*running, job], [lane], monitor, journal)
    assert cancelled == launched == []


def test_service_renewal_keeps_new_coordinator(monkeypatch, tmp_path):
    monitor = SimpleNamespace(state={}, event=lambda *a, **k: None)
    calls = []
    monkeypatch.setenv('SLURM_JOB_ID', '900')
    monkeypatch.setattr(F.E, 'STATE', tmp_path / 'state.json')
    monkeypatch.setattr(F.Previous, 'renew_offload', lambda *a: None)
    monkeypatch.setattr(F, 'submit', lambda command: calls.append(command) or '901')
    F.renew_services([{'id': '900', 'qos': 'normal', 'left': '00:30:00'}], monitor)
    assert calls == [['--dependency=afterany:900', 'slurm/aln35_maintain_fleet_v2.sbatch']]
