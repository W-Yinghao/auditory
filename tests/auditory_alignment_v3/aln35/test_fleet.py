import copy
import json
from types import SimpleNamespace

import pytest

from private.auditory_alignment_v3.aln35 import maintain_fleet as F


def test_unverified_plugin_cannot_submit(tmp_path, monkeypatch):
    p=tmp_path/'plugins.json'
    p.write_text(json.dumps({'version':1,'plugins':[{'module':'auditory_alignment_v3.aln35.fake',
        'name':'c3_s35fake','lane':'s35_fake','sha256':'wrong'}]}))
    called=[]
    module=SimpleNamespace(__file__=str(p),fleet_status=lambda:called.append(True))
    monkeypatch.setattr(F.importlib,'import_module',lambda name:module)
    lanes=F.plugin_lanes(p)
    assert not called and lanes[0]['ready']==0 and lanes[0]['state']=='technical_error'


def test_one_pass_preserves_active_work_and_caps_waiting_jobs(tmp_path,monkeypatch):
    out=tmp_path/'out';base=out/'aln34';new=out/'aln35'
    base.mkdir(parents=True);new.mkdir()
    (out/'STOP_queue_v3_fm').write_text('old keeper stopped')
    (out/'queue_v3_fm.txt').write_text('')
    (base/'fleet_smoke_jobs.json').write_text('{}')
    (base/'fleet_runtime.json').write_text('{}')
    monkeypatch.setenv('SLURM_JOB_ID','test')
    for key,value in dict(ROOT=tmp_path,OUT=out,BASE=base,NEWBASE=new,JOURNAL=base/'journal.json').items():
        monkeypatch.setattr(F,key,value)
    monkeypatch.setattr(F.E,'STATE',base/'efficiency_state.json')
    monkeypatch.setattr(F,'CONFIG',{f'old{i}':None for i in range(15)})
    initial=[dict(id=str(i),name='c3_existing'+str(i),qos='runfill',state='RUNNING',gres='gres/gpu:1') for i in range(10)]
    initial+=[dict(id='pending',name='c3_pending',qos='runfill',state='PENDING')]
    monkeypatch.setattr(F.E,'query_jobs',lambda:copy.deepcopy(initial))
    monkeypatch.setattr(F,'renew_services',lambda *args:None)
    for name in ('refresh','drain_prior_canary','event'):
        monkeypatch.setattr(F.E.Monitor,name,lambda *args,**kwargs:None)
    monkeypatch.setattr(F.E.Monitor,'fallback_prior',lambda *args:False)
    monkeypatch.setattr(F,'lane',lambda key,overrides:dict(name='c3_'+key,lane=key,state='ready',
        ready=1,slots=1,initial=[],submit=['--job-name=c3_'+key,'slurm/aln34_priority_rotation.sbatch']))
    monkeypatch.setattr(F,'plugin_lanes',lambda:[])
    calls=[]
    monkeypatch.setattr(F,'submit',lambda command:(calls.append(command) or str(100+len(calls))))
    monkeypatch.setattr(F,'cancel',lambda *args:pytest.fail('active work must remain'))
    monkeypatch.setattr(F.time,'sleep',lambda seconds:(new/'STOP_fleet_maintenance').write_text('end'))
    monkeypatch.chdir(tmp_path)
    F.main()
    assert len(calls)==11
    assert all('--time=24:00:00' in command for command in calls)
    assert all('P100' not in ' '.join(command) for command in calls)
    assert (new/'fleet_status.json').exists()


def test_dependencies_and_bounded_new_work_precede_redundant_curves():
    assert F.Priority.rank('inner',0)<F.Priority.rank('curves',0)
    assert F.Priority.rank('cb_auditory',0)<F.Priority.rank('breadth_budget',0)
    assert F.Priority.rank('s35_support',0)<F.Priority.rank('breadth_curves',0)
    assert F.CONFIG['inner'][3]==2 and F.CONFIG['cb_auditory'][3]==2
