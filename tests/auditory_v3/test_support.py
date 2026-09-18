import numpy as np
import pandas as pd
import pytest
from auditory_v3.splits import make_splits,validate_bags
from auditory_v3.data import htrial


def test_identity_split_does_not_depend_on_outcomes_or_member_multiplicity():
    groups=[f'synthetic_{i}' for i in range(50)]
    legacy={'folds':[dict(outer_fold=f,test_groups=groups[f*10:(f+1)*10],train_groups=[g for g in groups if g not in groups[f*10:(f+1)*10]]) for f in range(5)]}
    frame=pd.DataFrame(dict(split_group_id=np.repeat(groups,4),stimulus_local_id=np.tile([0,1,0,1],50)))
    first=make_splits(frame,legacy)
    frame['stimulus_local_id']=1-frame.stimulus_local_id
    second=make_splits(pd.concat([frame,frame.iloc[:30]],ignore_index=True),legacy)
    assert first==second
    for f in first['folds']:
        assert not set(f['R3_fit_groups'])&set(f['R3_validation_groups'])
        assert not set(f['R3_fit_groups'])&set(f['test_groups'])
        assert all(not set(i['fit_groups'])&set(i['validation_groups']) for i in f['inner_folds'])


def test_history_features_reject_identifier_and_current_target_routes():
    frame=pd.DataFrame(dict(previous_code=['1','2',None],previous_run_bin=['run_1','run_2',None],previous_gap_s=[1.,np.nan,2.],position_fraction=[.1,.5,.9],A_half=[0,1,1]))
    initial=htrial(frame)
    frame['trial_id']=['secret_c0','secret_c1','secret_c0'];frame['current_run_length']=[999,222,111]
    frame['stimulus_local_id']=[1,0,1]
    np.testing.assert_array_equal(initial,htrial(frame))
    assert initial.shape==(3,13)
    assert np.isfinite(initial).all()
