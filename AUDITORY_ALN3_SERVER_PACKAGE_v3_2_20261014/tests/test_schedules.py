import pytest
from aln32_reference.schedules import legacy_coverage,legacy_open_groups,full_update_flags,update_coverage_from_steps

def test_reve_legacy_not_full():
    x=legacy_coverage(22,50)
    assert x['final_open_blocks']==9 and not x['non_block_open']
    assert sum(r['open_epochs']>0 for r in x['groups'])==9

def test_cbramod_late_embedding():
    x=legacy_coverage(12,100)
    assert x['final_open_blocks']==12
    assert x['groups'][-1]['first_open_epoch']==66
    assert x['groups'][-1]['open_epochs']==35

@pytest.mark.parametrize('ep,expected',[(0,0),(4,0),(5,1),(9,1),(10,2),(49,9)])
def test_legacy_boundary(ep,expected):assert legacy_open_groups(ep,22)==expected

@pytest.mark.parametrize('recipe', ['full_onestep_v1','warmup_then_all_v1'])
def test_full_keeps_masks(recipe):
    assert full_update_flags(10,[True,False,True],recipe)==[True,False,True]

def test_true_full_from_first():assert all(full_update_flags(0,[True]*23,'full_onestep_v1'))
def test_warmup_then_all():
    assert not any(full_update_flags(4,[True]*23,'warmup_then_all_v1'))
    assert all(full_update_flags(5,[True]*23,'warmup_then_all_v1'))

def test_step_coverage():assert update_coverage_from_steps(['head','input'],[100,0])['never_updated']==['input']
def test_invalid_schedule():
    with pytest.raises(ValueError):legacy_coverage(0,50)
