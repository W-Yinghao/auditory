import json
from private.auditory_alignment_v3.aln35 import evidence_refresh as E


def test_array_admission_counts_tasks_not_lines():
    assert E.normal_count([['1_[1-30%2]', 'x', 'PENDING']]) == 30
    assert E.normal_count([['1_[1,3,5]', 'x', 'PENDING']]) == 30
    assert E.normal_count([['1_3', 'x', 'RUNNING'], ['2','y','RUNNING']]) == 2


def test_signature_changes_only_with_new_valid_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(E, 'ROOT', tmp_path)
    task = {'sources':['*.json'], 'minimum_files':1}
    a, ready, n = E.signature(task)
    assert not ready and n == 0
    (tmp_path/'one.FAILED.json').write_text('{}')
    assert E.signature(task) == (a, ready, n)
    (tmp_path/'one.json').write_text('{"status":"complete"}')
    b, ready, n = E.signature(task)
    assert a != b and ready and n == 1


def test_tick_never_resubmits_success_or_live_task(tmp_path, monkeypatch):
    monkeypatch.setenv('SLURM_JOB_ID','test')
    monkeypatch.setattr(E,'BASE',tmp_path)
    monkeypatch.setattr(E,'CONFIG',tmp_path/'config.json')
    monkeypatch.setattr(E,'STATE',tmp_path/'state.json')
    E.CONFIG.write_text(json.dumps({'version':1,'tasks':{'done':{},'live':{}}}))
    E.STATE.write_text(json.dumps({'tasks':{'done':{'last_signature':'same'},
        'live':{'pending':{'job':'55','submitted':0}}}}))
    monkeypatch.setattr(E,'normal_jobs',lambda:[['55','x','RUNNING']])
    monkeypatch.setattr(E,'validate_task',lambda t:None)
    monkeypatch.setattr(E,'signature',lambda t:('same',True,1))
    def check(args, **kwargs):
        assert args[0] == 'squeue', 'duplicate submission'
        return '3-23:00:00'
    monkeypatch.setattr(E.subprocess,'check_output',check)
    E.tick()
    assert E.read(E.STATE)['tasks']['live']['pending']['job']=='55'
