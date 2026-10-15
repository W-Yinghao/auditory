from pathlib import Path
import yaml
from aln32_reference.queue_policy import advise
R=Path(__file__).resolve().parents[1]

def test_running_no_mutation():assert advise({'status':'running'})['recommendation']=='allow_registered_completion'
def test_completed_keep():assert advise({'status':'complete'})['recommendation']=='retain'
def test_aligned_continues():assert advise({'family_id':'B_ALIGNED','status':'pending'})['recommendation']=='continue_existing'
def test_local_d_not_wholefamily_hold():
    r={'family_id':'D_ATTENTION','spec':{'architecture':'lag_local_tokens'},'depends_on_old_dense_interface':False}
    assert advise(r)['recommendation']=='continue_if_bound'
def test_old_dependency_hold():
    r={'family_id':'D_ATTENTION','depends_on_old_dense_interface':True}
    assert advise(r)['recommendation']=='hold_version'
def test_unknown_not_guess():assert advise({'family_id':'D_ATTENTION'})['recommendation']=='needs_binding'
def test_no_metrics_gate():
    a={'family_id':'B_ALIGNED','score':0};b=dict(a,score=1)
    assert advise(a)==advise(b)
def test_configs_unique():
    c=yaml.safe_load((R/'configs/experiments.yaml').read_text());ids=[x['id'] for x in c['families']]
    assert len(ids)==len(set(ids)) and c['inherited'][0]['expected_registered_rows']==250
