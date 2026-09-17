import json
from pathlib import Path
import numpy as np
import pytest
from auditory_v21.evaluation import judge_world,summarize_cells
from auditory_v21.worlds import generate


THRESHOLDS={
    'minimum_positive_gain_bits':.01,'minimum_control_margin_bits':.005,
    'positive_ci_lower_strictly_above':0.,'minimum_positive_recoveries_per_20':16,
    'meaningful_false_positive_gain_bits':.005,'maximum_meaningful_false_positives_per_20':2,
    'minimum_null_risk_preservations_per_20':18,'null_maximum_loss_increase_bits':.005,
    'null_maximum_mean_loss_increase_bits':.002,'minimum_baseline_gain_over_class_prior_bits':.02,
    'near_deterministic_maximum_baseline_risk_bits':.05}


def rows_n1():
    return [dict(first=a,second=b,estimate=value,ci_lower=value-.001,ci_upper=value+.001)
        for a,b,value in [('HP','HPB',0.),('HB','HPB',.1),('HPBnoise','HPB',0.),('HPP','HPB',0.)]]


def test_independent_background_zero_gate_is_conditional_on_hp_only():
    judged=judge_world('N1','independent_background',.2,rows_n1(),{'HP':.4,'HB':.5},THRESHOLDS)
    assert judged['kind']=='NULL' and not judged['meaningful_false_positive']
    assert judged['risk_preserved']


def test_missing_control_is_unevaluable_not_a_pass():
    with pytest.raises(ValueError,match='CONTROL_MISSING'):
        judge_world('N1','trial_key',.2,rows_n1()[:-1],{'HP':.4,'HB':.5},THRESHOLDS)


def test_success_subset_cannot_pass_complete_cell():
    judged=dict(recovered=True,meaningful_false_positive=False,unthresholded_false_positive=False,
                risk_preserved=True,worst_primary_gain=.1)
    records=[dict(world='trial_key',rate=.2,status='COMPLETE',judgment=judged) for _ in range(19)]
    records.append(dict(world='trial_key',rate=.2,status='FAILED'))
    cell=summarize_cells(records,['trial_key'],[.2],THRESHOLDS,20)[0]
    assert cell['status']=='FAIL' and cell['unevaluable']==1 and cell['planned']==20


def test_real_width_and_unequal_role_sample_profile_preserves_known_oracle():
    profile={'A':[10]*33,'B':[11]*3,'C':[12]*5,'D':[13]*6,'E':[14]*12}
    data=generate('N1','independent_background',999031,400,.15,
                  history_dimension=25,background_dimension=200,role_sample_sizes=profile)
    assert data['h'].shape[1]==25 and data['p'].shape[1]==400 and data['b'].shape[1]==200
    assert data['noise'].shape[1]==200
    for role,sizes in profile.items():
        assert len(data['roles'][role])==sum(sizes)
        assert len(set(data['groups'][data['roles'][role]]))==len(sizes)
    np.testing.assert_array_equal(data['oracle']['HP'],data['oracle']['joint'])
