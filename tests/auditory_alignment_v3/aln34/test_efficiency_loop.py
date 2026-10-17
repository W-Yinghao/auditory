import copy
import json
import pytest

from private.auditory_alignment_v3.aln34 import efficiency_loop as E


def job(jid='1', state='PENDING', reason='Resources', name='c3_aln34budget', partition='A100,L40S'):
    return dict(id=jid, name=name, qos='runfill', state=state, reason=reason,
                partition=partition, gres='gres/gpu:1')


def test_gpu_count_uses_requested_cards_and_preserves_other_projects():
    jobs = [job(str(i), 'RUNNING') for i in range(10)]
    jobs += [dict(job('99', 'RUNNING', name='v9f_external'), gres='gres/gpu:8')]
    assert E.gpu_count(jobs) == 10
    jobs[0]['gres'] = 'gres/gpu:a100:2'
    assert E.gpu_count(jobs) == 11
    jobs[0]['gres'] = 'N/A'
    with pytest.raises(ValueError):
        E.gpu_count(jobs)


def test_routing_falls_back_on_stale_or_busy_capacity_and_short_tasks():
    status = {'epoch': 1000, 'hardware': {'idle_partitions': ['A100']}}
    assert E.route('budget', status, now=1000)['partitions'] == ['A100', 'L40S']
    assert E.route('science', status, now=1000)['partitions'] == list(E.BROAD)
    assert E.route('budget', status, now=2000)['partitions'] == list(E.BROAD)
    status['broad_until'] = {'budget': 3000}
    assert E.route('budget', status, now=1000)['partitions'] == list(E.BROAD)
    assert 'V100' not in E.route('prior', {}, now=1000, oom_only=True)['partitions']
    assert 'V100' in E.route('prior', {}, now=1000)['partitions']


def test_qos_wait_does_not_trigger_queue_churn():
    j = job()
    meta = dict(id='1', name=j['name'], lane='budget', eligible_since=10, fallback=False)
    assert E.pending_fallback(j, meta, [j], 1300)
    assert not E.pending_fallback(dict(j, reason='QOSMaxGRESPerUser'), meta, [j], 1300)
    running = [job(str(i+2), 'RUNNING') for i in range(10)]
    assert not E.pending_fallback(j, meta, running+[j], 1300)
    assert not E.pending_fallback(dict(j, state='RUNNING'), meta, [j], 1300)
    assert not E.pending_fallback(j, dict(meta, eligible_since=None), [j], 1300)


def test_pending_to_running_race_never_duplicates_or_cancels_active_work():
    j = job()
    meta = dict(id='1', name=j['name'], lane='budget', eligible_since=10, fallback=False,
                base_command=['--job-name=c3_aln34budget', 'slurm/aln34_priority_rotation.sbatch', '--lane', 'budget'])
    commands = []
    def no_submit(command):
        raise AssertionError('must not submit when old job still exists')
    assert E.replace_pending(j, meta, [j], 1300, lambda: [dict(j, state='RUNNING')], commands.append, no_submit) is None
    assert commands == [['scancel', '--state=PENDING', '1']]
    result = E.replace_pending(j, meta, [j], 1300, lambda: [], commands.append, lambda command: '2')
    assert result['id'] == '2' and result['fallback'] and result['replaces'] == '1'
    assert result['base_command'] == meta['base_command']
    assert result['decision']['partitions'] == list(E.BROAD)


def test_timing_evidence_cannot_mix_budgets_or_resumes():
    r = dict(status='complete', device='NVIDIA A100', total_seconds=100, optimizer_steps=100, epochs_completed=20)
    row = dict(dataset='dtu', subject_fold=0, content_fold=0,
               spec={'architecture': 'reve', 'objective': 'NCE'})
    assert E.timing_sample(dict(r, resumed_from_epoch=10), row, 'budget') is None
    assert E.timing_sample(dict(r, reused_from={'id': 'old'}), row, 'budget') is None
    assert E.timing_sample(dict(r, truncated=True), row, 'budget') is None
    values = [E.timing_sample(r, row, 'budget') for _ in range(2)]
    values += [E.timing_sample(dict(r, device='NVIDIA A40', total_seconds=300), row, 'budget') for _ in range(2)]
    assert E.timing_summary(values)['matched_speedups'][0]['slow_over_fast'] == 3
    values[2] = E.timing_sample(dict(r, device='NVIDIA A40', optimizer_steps=50), row, 'budget')
    assert not E.timing_summary(values)['matched_speedups']


def test_normal_qos_count_expands_arrays():
    assert E.normal_slots([dict(id='4_[0-3%2]', qos='normal'), dict(id='5', qos='normal')]) == 5
    assert E.normal_slots([dict(id='4_[0,2,3]', qos='normal')]) == 30


def test_prior_trial_drains_one_owned_worker_only_after_new_keeper_is_live(tmp_path, monkeypatch):
    base = tmp_path/'aln34'; base.mkdir()
    pool = tmp_path/'pool/queue_v3_prior'; pool.mkdir(parents=True)
    monkeypatch.setattr(E, 'OUT', tmp_path); monkeypatch.setattr(E, 'BASE', base)
    monkeypatch.setattr(E, 'STATE', base/'efficiency_state.json')
    monitor = E.Monitor()
    monitor.state = {'epoch': E.time.time(), 'hardware': {'idle_partitions': ['A100']}}
    jobs = [job('10', 'RUNNING', name='c3_aln3pr', partition='V100'),
            job('11', 'RUNNING', name='c3_aln3pr', partition='V100'),
            job('99', 'RUNNING', name='other_project', partition='V100')]
    monitor.drain_prior_canary(jobs)
    assert not list(pool.glob('.infra_*'))
    (base/'efficiency_prior_keeper.json').write_text(json.dumps({'job':'22','adopted_workers':['10','11']}))
    jobs.append(dict(job('22','RUNNING',name='c3_p33keeper'),qos='normal'))
    monitor.drain_prior_canary(jobs)
    assert [p.name for p in pool.glob('.infra_*')] == ['.infra_10']
    monitor.drain_prior_canary(jobs)
    assert len(list(pool.glob('.infra_*'))) == 1


def test_v15_fills_to_twelve_pending_with_ten_active_without_touching_them(tmp_path, monkeypatch):
    from private.auditory_alignment_v3.aln34 import maintain_fleet_v15 as F
    out = tmp_path / 'out'; base = out / 'aln34'; base.mkdir(parents=True)
    (out/'STOP_queue_v3_fm').write_text('legacy keeper stopped')
    (out/'queue_v3_fm.txt').write_text('')
    (base/'fleet_smoke_jobs.json').write_text('{}')
    (base/'fleet_runtime.json').write_text('{}')
    monkeypatch.setenv('SLURM_JOB_ID', 'test')
    monkeypatch.setattr(F, 'ROOT', tmp_path); monkeypatch.setattr(F, 'OUT', out); monkeypatch.setattr(F, 'BASE', base)
    monkeypatch.setattr(F, 'JOURNAL', base/'efficiency_jobs.json')
    monkeypatch.setattr(E, 'STATE', base/'efficiency_state.json')
    keys = list(F.Priority.LANE_PRIORITY)
    monkeypatch.setattr(F, 'CONFIG', {k: None for k in keys})
    initial = [job(str(i), 'RUNNING', name='c3_existing_'+str(i)) for i in range(10)] + [job('repair', name='c3_repair')]
    monkeypatch.setattr(E, 'query_jobs', lambda: copy.deepcopy(initial))
    monkeypatch.setattr(F, 'renew_services', lambda *args: None)
    monkeypatch.setattr(E.Monitor, 'refresh', lambda *args: {})
    monkeypatch.setattr(E.Monitor, 'drain_prior_canary', lambda *args: None)
    monkeypatch.setattr(E.Monitor, 'fallback_prior', lambda *args: False)
    monkeypatch.setattr(E.Monitor, 'event', lambda *args, **kwargs: None)
    monkeypatch.setattr(F.Previous, 'lane', lambda key, overrides: dict(name='c3_'+key, lane=key, state='ready', ready=1,
        slots=1, initial=[], submit=['--job-name=c3_'+key, 'slurm/aln34_priority_rotation.sbatch']))
    submitted = []
    def submit(command):
        submitted.append(command); return str(100+len(submitted))
    monkeypatch.setattr(F, 'submit', submit)
    monkeypatch.setattr(F, 'cancel', lambda *args: pytest.fail('active jobs must be preserved'))
    monkeypatch.setattr(F.time, 'sleep', lambda seconds: (base/'STOP_fleet_maintenance_v15').write_text('test end'))
    monkeypatch.chdir(tmp_path)
    F.main()
    assert len(submitted) == 11
    assert len({next(x for x in cmd if x.startswith('--job-name=')) for cmd in submitted}) == 11
    assert all('--time=24:00:00' in cmd for cmd in submitted)
    assert sum(j['state']=='RUNNING' for j in initial) == 10
