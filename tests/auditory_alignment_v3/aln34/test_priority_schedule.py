import copy
from private.auditory_alignment_v3.aln34 import priority_schedule as P


def test_reordering_preserves_all_paired_rows_and_ignores_outcomes():
    rows=[{'id':str((arch,seed,fold,init)),'spec':{'architecture':arch,'adaptation':init},
           'seed':seed,'subject_fold':fold,'content_fold':0,'test_score':(-1)**fold}
          for arch in ('reve','cbramod','lag_local_tokens') for seed in (3401,3407,3413)
          for fold in range(5) for init in ('random_full','pretrained_full')]
    frozen=copy.deepcopy(rows)
    ordered=sorted(rows,key=lambda r:P.row_priority('budget',r))
    assert rows==frozen and {r['id'] for r in rows}=={r['id'] for r in ordered}
    tiers=[P.row_priority('budget',r)[0] for r in ordered]
    assert tiers==sorted(tiers) and len([v for v in tiers if v==0])==60
    changed=copy.deepcopy(rows)
    for r in changed:r['test_score']*=1e9
    assert [r['id'] for r in sorted(changed,key=lambda r:P.row_priority('budget',r))]==[r['id'] for r in ordered]


def test_dependency_sources_and_private_science_precede_grid_extensions():
    assert P.rank('inner',99)<P.rank('curves',0)
    assert P.rank('private',99)<P.rank('breadth_budget',0)
    assert P.rank('private_factorial',99)<P.rank('budget',0)
    assert P.rank('breadth_inner',99)<P.rank('breadth_curves',0)
    assert P.max_units('science')==8 and P.max_units('budget')==2
    assert set(P.LANE_PRIORITY)=={'private','science','prior_loo','prior_science','attention','private_factorial',
        'inner','breadth_inner','adapt','private_episode','cb_auditory','breadth_adapt','budget','fusion',
        'breadth_fusion','episode','cs_episode','breadth_episode','curves','breadth_budget','breadth_curves'}


def test_priority_refill_respects_pending_cap_without_cancelling_running_jobs(tmp_path,monkeypatch):
    from private.auditory_alignment_v3.aln34 import maintain_fleet_v14 as F
    out=tmp_path/'out';base=out/'aln34';base.mkdir(parents=True)
    (out/'STOP_queue_v3_fm').write_text('already stopped legacy keeper')
    (out/'queue_v3_fm.txt').write_text('')
    monkeypatch.setenv('SLURM_JOB_ID','priority_test')
    monkeypatch.setattr(F,'ROOT',tmp_path);monkeypatch.setattr(F,'OUT',out);monkeypatch.setattr(F,'BASE',base)
    keys=list(P.LANE_PRIORITY)
    monkeypatch.setattr(F,'CONFIG',{k:None for k in keys})
    initial=[{'id':str(i),'name':'c3_active_'+str(i),'qos':'runfill','state':'RUNNING'} for i in range(10)]
    initial.append({'id':'repair','name':'c3_repair','qos':'runfill','state':'PENDING'})
    monkeypatch.setattr(F,'jobs',lambda:copy.deepcopy(initial))
    monkeypatch.setattr(F,'renew_offload',lambda jobs:False)
    monkeypatch.setattr(F,'lane',lambda key,overrides:{'name':'c3_'+key,'lane':key,'state':'ready','ready':1,'slots':1,
        'initial':[],'submit':['--job-name=c3_'+key,'dummy.sbatch']})
    submitted=[]
    def submit(command):submitted.append(command);return str(100+len(submitted))
    monkeypatch.setattr(F,'submit',submit)
    monkeypatch.setattr(F.time,'sleep',lambda seconds:(base/'STOP_fleet_maintenance_v14').write_text('test done'))
    # F.main intentionally chdirs; restore through pytest's monkeypatch cleanup.
    monkeypatch.chdir(tmp_path)
    F.main()
    assert len(submitted)==11  # one existing pending + eleven new = twelve
    assert [int(x[0].split('=')[1]) for x in submitted]==sorted(int(x[0].split('=')[1]) for x in submitted)
    assert len({x[1] for x in submitted})==11
    assert sum(j['state']=='RUNNING' for j in initial)==10
