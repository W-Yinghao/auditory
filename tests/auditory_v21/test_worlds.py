import numpy as np
from auditory_v21.worlds import generate


def test_known_zero_information_oracles_preserve_h_baseline():
    for world in ('strong_history_null','history_copy','near_deterministic'):
        data=generate('N3',world,21101,64,.2,[12])
        np.testing.assert_allclose(data['oracle']['H'],data['oracle']['joint'],atol=1e-14)
        assert len(set(data['groups']))==60


def test_independent_background_has_no_conditional_background_information():
    data=generate('N1','independent_background',21102,64,.2,[12])
    np.testing.assert_array_equal(data['oracle']['HP'],data['oracle']['joint'])


def test_fixed_world_seed_reproduces_features_and_roles():
    a=generate('N1','group_key',21103,64,.2,[12]);b=generate('N1','group_key',21103,64,.2,[12])
    for key in ('p','b','h','y'):np.testing.assert_array_equal(a[key],b[key])
    for role in a['roles']:np.testing.assert_array_equal(a['roles'][role],b['roles'][role])
