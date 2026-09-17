import numpy as np
import pandas as pd
from auditory_next.context_inputs import independent_noise,context_views,donor_indices


def test_noise_is_per_trial_order_invariant_and_view_duplication_is_exact():
    ids=['x','y'];a=independent_noise(ids,3);b=independent_noise(ids[::-1],3)
    np.testing.assert_array_equal(a,b[::-1])
    h=np.ones((2,1));v=context_views(h,a,b,a,'N1')
    np.testing.assert_array_equal(v['HPP'][:,1:4],v['HPP'][:,4:])


def test_fast_donor_has_same_label_blindness_and_physical_scope():
    base=dict(candidate_id='c',split_group_id='g',record_id='r',segment_id='s',previous_code='1',previous_run_bin='run_3_5',layout_id='HA20',previous_gap_s=.6)
    rows=pd.DataFrame([dict(base,trial_id='q',raw_dependency_start=30.,raw_dependency_end=42.,stimulus_local_id=0,time_block_id=1),
                       dict(base,trial_id='d',raw_dependency_start=0.,raw_dependency_end=12.,stimulus_local_id=1,time_block_id=0)])
    one=donor_indices(rows,rows,role='same_child')[0]
    rows['stimulus_local_id']=1-rows.stimulus_local_id
    np.testing.assert_array_equal(one,donor_indices(rows,rows,role='same_child')[0])
    np.testing.assert_array_equal(one,[1,0])
