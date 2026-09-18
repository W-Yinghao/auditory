import numpy as np
import pandas as pd
from auditory_v3.n2r_capability import capability_catalog,synthetic_packet,summarize_capability,WORLD_NAMES
from auditory_v3.bags_packet import H_COLUMNS


def template():
    rows=[]
    for g in range(3):
        for half in (0,1):
            for label in (0,1):
                bag=f'{g}_{half}_{label}'
                for k in range(8):
                    rows.append(dict(bag_id=bag,matched_pair_id=f'{g}_{half}',trial_id=f'{bag}_{k}',candidate_id=str(g),split_group_id=str(g),record_id=str(g),segment_id=0,stimulus_local_id=label,A_half=half,A_block_id=half,physical_block_id=k//4,previous_code='1',previous_run_bin='run_1',k=8,onset_seconds_relative=half*100+label*20+k))
    m=pd.DataFrame(rows);h=pd.DataFrame({'bag_id':m.bag_id.unique()})
    for col in H_COLUMNS:h[col]=0.
    return m,h

def test_worlds_preserve_every_metadata_row_and_use_new_numeric_features():
    m,h=template()
    for name in WORLD_NAMES:
        world=synthetic_packet(name,53001,m,h)
        pd.testing.assert_frame_equal(world.members,m)
        assert world.post.shape==(len(m),400) and world.pre.shape==(len(m),200)
        assert np.isfinite(world.post).all()
        # Strong variance world does not mechanically demean each bag.
        assert np.abs(world.post[:8].mean(axis=0)).max()>.01
        repeated=synthetic_packet(name,53001,m,h)
        np.testing.assert_array_equal(world.post,repeated.post)
    pd.testing.assert_frame_equal(h,template()[1])

def test_complete_denominators_and_seed_bank():
    catalog=capability_catalog()
    assert len(catalog)==60 and catalog.seed.is_unique
    assert set(catalog.seed)==set(range(53001,53061))
    rows=[]
    for row in catalog.to_dict('records'):
        gain=.02 if row['world']=='VAR_EXTRA' else -.01
        rows.append(dict(row,execution='COMPLETE',gain_bits=gain,ci_low=gain-.001,ci_high=gain+.001))
    assert summarize_capability(rows)['status']=='PASS'
    rows[0]['execution']='FAILED'
    assert summarize_capability(rows)['status']=='CAPABILITY_FAIL'
    assert summarize_capability(rows[1:])['status']=='CAPABILITY_FAIL'
