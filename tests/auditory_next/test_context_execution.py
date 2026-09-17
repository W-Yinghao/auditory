import numpy as np
import pandas as pd
from auditory_next.context_execution import candidate_losses,paired_effect,_calibrated_logit
from auditory_next.n3_summary import choose_family
from auditory_next.n1_controls import fixed_head_inputs


def test_stable_saturated_scores_are_not_clipped_and_gain_can_be_negative():
    rows=pd.DataFrame(dict(split_group_id=['a','a','b','b'],stimulus_local_id=[0,1,0,1],logit=[100,-100,100,-100]))
    x=candidate_losses(rows,'P_bal')
    assert (x.ce_bits>100).all()
    loss=pd.concat([x.assign(view='bad'),x.assign(view='good',ce_bits=1.)])
    assert paired_effect(loss,'good','bad')['estimate']<0


def test_family_selection_reads_only_inner_loss_and_tie_prefers_logistic():
    base=dict(mode='R_SIM',population='P_nat',outer_fold=0,view='H',inner_ce_bits_raw=.5)
    rows=[dict(base,family='mlp32',test_loss=0.),dict(base,family='logistic',test_loss=100.)]
    assert choose_family(rows,'R_SIM','P_nat',0,'H')=='logistic'


def test_donor_intervention_changes_only_background_and_eta_uses_training_prior():
    record=dict(common=np.array([True,True]),same=np.array([1,0]),cross=np.array([0,1]),hp=np.ones((2,1)),
        pp=np.array([[2.],[3.]]),bp_query=np.array([[4.],[5.]]),bp_fit=np.array([[6.],[7.]]))
    x=fixed_head_inputs(record)
    np.testing.assert_array_equal(x['actual_B'][:,:2],x['same_child_B'][:,:2])
    np.testing.assert_array_equal(x['same_child_B'][:,-1],[5.,4.])
    cal=dict(temperature=2.,eta=1.,training_prior=.2)
    np.testing.assert_allclose(_calibrated_logit(np.array([100.,-100.]),cal,'mixture_diagnostic'),np.log(.2/.8))
