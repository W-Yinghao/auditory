import numpy as np
import pytest
from auditory_alignment_v3.aln35 import support_contract as K


def test_private_boundary_and_trial_not_block_budget():
    kid={'y':np.arange(40)%2,'block':np.repeat(np.arange(10),4),
         'es_mask':np.zeros(40,bool),'_s35_onset_seconds':np.arange(40)*.5}
    out=K.private_split(kid)
    assert out['n10']==4 and out['n30']==11
    assert out['query'].tolist()==list(range(13,40))
    assert out['query_identical_private_episode_v2'] and not out['query_identical_native_science']
    assert max(kid['_s35_onset_seconds'][out['pool']])+.6 <= min(kid['_s35_onset_seconds'][out['query']])-.2


def test_guard_uses_full_epoch_for_both_models_and_keeps_query():
    kid={'y':np.arange(40)%2,'block':np.repeat(np.arange(10),4),
         'es_mask':np.zeros(40,bool),'_s35_onset_seconds':np.arange(40)*.1}
    out=K.private_split(kid)
    assert out['query'].tolist()==list(range(13,40))
    assert out['guard_excluded'].tolist()==[6,7,8,9,10]
    assert out['pool'].tolist()==[0,1,2,3,4,5]


def test_public_guard_all_grid_anchors_not_only_adaptation_anchors():
    items=[{'e0':i*640,'code':'x'} for i in range(10)]
    split=K.dtu_split(items,128,640,16,77)
    assert split['pool'].tolist()==[0,1]
    assert split['query'].tolist()==list(range(3,10))
    assert split['guard_excluded'].tolist()==[2]
    assert split['n10']==1


def test_u10_nested_reproducible_all_five_seeds():
    pool=np.arange(30);group=np.repeat(['g0','g1','g2'],10)
    a=K.select_support(pool,7,'person',groups=group)
    b=K.select_support(pool,7,'person',groups=group)
    for seed in K.SAMPLING_SEEDS:
        assert np.array_equal(a[f'U10_{seed}'],b[f'U10_{seed}'])
        assert len(a[f'U10_{seed}'])==7 and set(a[f'U10_{seed}'])<=set(a['U30'])
    assert len(set(tuple(a[f'U10_{s}']) for s in K.SAMPLING_SEEDS))==5
    assert len(set(group[a['C10']]))==3


def test_c10_rare_class_transfer_and_hash_stability():
    pool=np.arange(12);labels=np.array([0]*11+[1])
    result=K.select_support(pool,8,'child',labels=labels)
    assert labels[result['C10']].sum()==1 and len(result['C10'])==8
    assert set(result['C10'])<=set(pool)


def test_h10_covers_history_without_query_metadata():
    pool=np.arange(18);history=np.tile(np.arange(6),3);times=np.arange(18)
    result=K.select_support(pool,6,'child',labels=pool%2,history=history,times=times)
    assert len(set(history[result['H10']]))==6
    assert len(set((times[result['H10']]//6).tolist()))==3
    assert len(result['H10'])==len(result['C10'])==6


def test_empty_and_equal_support_are_retained():
    result=K.select_support(np.array([],int),0,'child',labels=np.array([],int),history=np.array([],int),times=np.array([],float))
    assert set(result)=={*(f'U10_{x}' for x in K.SAMPLING_SEEDS),'U30','C10','H10'}
    assert all(len(v)==0 for v in result.values())
    same=K.select_support(np.array([2]),1,'child',labels=np.array([1]))
    assert all(v.tolist()==[2] for v in same.values())


def test_temperature_true_risk_ties_and_no_support():
    t,rec=K.temperature_binary(np.zeros(4),[0,1,0,1]);assert t==1.
    t,rec=K.temperature_binary([],[]);assert t==1. and rec['reason']
    t,rec=K.temperature_binary([10.,10.],[0,0]);assert t==2.
    t,rec=K.temperature_retrieval(np.zeros((3,2)),[0,1,0],.3);assert t==1.
    t,rec=K.temperature_retrieval(np.ones((1,1)),[0],.3);assert t==1. and rec['reason']


def test_access_is_not_fit_label_budget():
    split={'pool':np.arange(30)}
    receipt=K.access_budget('H10',split,np.arange(10),20,True)
    assert receipt['metadata_rows_accessed']==receipt['label_rows_accessed']==30
    assert receipt['fit_rows']==10 and receipt['fit_updates']==20
    assert not receipt['deployment_label_budget_equivalence_claimed']


def test_cs_single_class_signal_identity_not_child_exclusion():
    record=K.support_signal('CS_SINGLE',np.ones(20),100)
    assert record['effective_adapter_steps']==0 and record['identity_fallback_reason']=='zero_signal_single_class_CS'
    assert K.support_signal('NCE',np.ones(20),100)['effective_adapter_steps']==100
    assert K.support_signal('CS_SINGLE',[0,1],20)['effective_adapter_steps']==20


def test_zero_cosine_is_undefined_and_probability_change_is_functional():
    assert K.cosine_or_none([0,0],[1,2]) is None
    assert K.cosine_or_none([1,0],[0,1])==0.
    assert K.probability_change([.2,.8],[.2,.8])['probability_tv']==0.
    assert K.probability_change([.4,.6],[.2,.8])['probability_tv']==pytest.approx(.2)
