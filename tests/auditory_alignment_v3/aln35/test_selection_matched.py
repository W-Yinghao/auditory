import copy
import numpy as np
import pytest
from auditory_alignment_v3.aln35 import selection_assets as A,selection_policy as P,selection_training as T


def trajectory(risks,gains,steps=(0,25,50,100)):
    result={'budget':{'candidate_steps':list(steps),'candidate_fractions':[0,.25,.5,1]},'candidates':{}}
    for step,risk,gain in zip(steps,risks,gains):
        result['candidates'][str(step)]={'gain':{'inherited_gain_selection_score':gain},'evaluation':{'per_participant':{
            person:{'status':'complete','group':'nh','metrics':{mode:{'nll_bits':risk+delta} for mode in ('native','unified')},
                    'query_hash':'fixed-query','candidate_hash':'fixed-candidates'} for person,delta in (('a',0),('b',.2))}}}
    return result


def test_true_risk_and_gain_separate_same_candidates_including_zero():
    choice=P.choose(trajectory([1,.9,1.1,.8],[0,-3,-4,-1]))
    assert choice['native']['true_risk_selected_step']==100
    assert choice['native']['gain_selected_step']==50
    assert choice['native']['complete_inner_ids']==['a','b']


def test_ties_keep_epoch0_and_outer_only_applies_fixed_position():
    choice=P.choose(trajectory([1,1,1,1],[0,0,0,0]))
    outer=trajectory([4,1,.01,2],[0,0,0,0],steps=(0,50,100,200))
    out=P.apply_choice(choice,outer)
    assert out['native']['true_risk_outer_step']==0
    assert out['native']['gain_outer_step']==0
    assert out['native']['per_participant']['a']['true_risk_policy']['nll_bits']==4


def test_relative_candidate_position_transfers_not_raw_inner_step():
    choice=P.choose(trajectory([2,1,3,4],[0,1,2,3]))
    out=P.apply_choice(choice,trajectory([3,2,1,0],[0,1,2,3],steps=(0,50,100,200)))
    assert out['native']['true_risk_outer_step']==50


def test_paired_query_candidate_mismatch_rejected():
    choice=P.choose(trajectory([2,1,3,4],[0,1,2,3]))
    outer=trajectory([3,2,1,0],[0,1,2,3])
    outer['candidates']['25']['evaluation']['per_participant']['a']['query_hash']='different'
    with pytest.raises(AssertionError):P.apply_choice(choice,outer)


def test_nested_eeg_people_exclude_inner_and_share_full_legal_audio():
    people=[{'id':f'p{i}','group':'nh' if i%2 else 'hi','fold':i%5} for i in range(30)]
    segs=[{'p':i,'role':role,'kind':'ss','uid':f's{i}-{role}','part':str(i)} for i in range(30) for role in ('fit','es')]
    meta={'participants':people,'segments':segs};source={'outer':{'row':{'subject_fold':0}}}
    full=A.stage_split(meta,source,'inner',1.);half=A.stage_split(meta,source,'inner',.5)
    assert set(half['train_ids'])<set(full['train_ids'])
    assert full['audio_statistics_fit_indices']==half['audio_statistics_fit_indices']
    assert not set(half['train_ids'])&set(full['evaluation_ids'])
    assert all(people[segs[i]['p']]['fold'] not in (0,1) for i in half['fit_indices']+half['es_indices'])
    assert half['readout_fit_cal_ids']==half['train_ids']


def test_sampler_actual_U_and_horizon_not_conflated():
    meta={'segments':[{'p':i%3,'uid':f'u{i}'} for i in range(65)]}
    split={'fit_indices':list(range(65))}
    result=A.update_grid(meta,split,4,3401)
    assert result['candidate_steps'][0]==0 and result['candidate_steps'][-1]==result['U']
    assert result['scheduler_horizon_updates']==16
    assert result['U']>8  # partial/unique batches add actual updates beyond floor count


def test_policy_never_receives_outer_arg():
    import inspect
    assert list(inspect.signature(P.choose).parameters)==['inner']
