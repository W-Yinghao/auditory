import numpy as np
import pandas as pd
import pytest
import json
from auditory_next.metrics_supplement import candidate_metrics, summarize_metrics, influence_description, calibration_records, history_stratum_support


def test_macro_risk_keeps_unequal_candidate_sizes_and_probability_definitions():
    frame=pd.DataFrame(dict(trial_id=list('abcdef'),split_group_id=['a','a','b','b','b','b'],
        stimulus_local_id=[0,1,0,0,1,1],logit=[-2,2,0,0,0,0],population='P_bal',view='H'))
    candidates,dimensions=candidate_metrics(frame)
    metrics={r['metric']:r for r in summarize_metrics(candidates,dimensions)}
    assert metrics['bacc']['estimate']==.75
    assert metrics['auroc']['estimate']==.75
    assert metrics['ce_bits']['estimate']==pytest.approx((1+np.logaddexp(0,-2)/np.log(2))/2)
    assert metrics['ce_bits']['n_candidates']==2
    with pytest.raises(ValueError,match='DUPLICATE'):
        candidate_metrics(pd.concat([frame,frame.iloc[:1]],ignore_index=True))


def test_influence_reports_sign_instability_without_excluding_any_candidate():
    result=influence_description([1.,-.1,-.1])
    assert result['estimate']==pytest.approx(.8/3)
    assert result['leave_one_out_min']==pytest.approx(-.1)
    assert result['leave_one_out_max']==pytest.approx(.45)
    assert not result['all_leave_one_out_positive']
    assert result['n_candidates']==3


def test_g0_calibration_collects_actual_saved_parameters_without_refitting(tmp_path):
    data=[dict(mode='R_SIM',outer_fold=0,calibration=dict(temperature=16.,eta=0.)),
          dict(mode='R_SIM',outer_fold=0,calibration=dict(temperature=16.,eta=0.)),
          dict(mode='R_SIM',outer_fold=0)]
    (tmp_path/'within_child_fit_receipts.json').write_text(json.dumps(data))
    hashes={}
    result=calibration_records('G0_within',tmp_path,hashes)
    assert len(result)==2 and all(r['temperature']==16 for r in result)
    assert len(hashes)==1
    (tmp_path/'bridge_causal_outer3_calibration.json').write_text(json.dumps(dict(temperature=.25)))
    assert calibration_records('G0_bridge',tmp_path,hashes)==[dict(mode='L0',bank='causal',outer_fold=3,temperature=.25)]


def test_strata_preserve_class_zeros_and_require_identical_prediction_pools():
    source=pd.DataFrame(dict(trial_id=list('abcde'),split_group_id=['a','a','b','b','b'],
        stimulus_local_id=[0,1,0,1,0], previous_run_bin=['run2']*4+['run3_5'],
        mode='R_SIM',population='P_nat'))
    frame=pd.concat([source.assign(view=v,calibration=c) for v in ('H','HP','HB','HBP','Hnoise')
        for c in ('raw','temperature')],ignore_index=True)
    result={r['previous_run_bin']:r for r in history_stratum_support(frame)}
    assert result['run2']['n_trials']==4 and result['run2']['n_candidates_both_classes']==2
    assert result['run2']['class0_trials']==result['run2']['class1_trials']==2
    assert result['run3_5']['class1_trials']==0 and result['run3_5']['n_candidates_both_classes']==0
    with pytest.raises(ValueError,match='ALL_VIEWS_SAME_POOL'):
        history_stratum_support(frame.iloc[:-1])
