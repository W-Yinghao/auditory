"""C2-S exact geometry/injection contracts; no real EEG, fits or power study."""
import numpy as np
import pytest

from auditory_next.c2_spatial import (CHANNELS, COMPONENT_ORDER, bin_20ms, coordinates19,
    decompose20, from_coordinates19, helmert_basis, inject_spatial_world, linear_maps,
    local_center, l0_views, reconstruct20)


def test_five_component_reconstruction_and_19_effective_dimensions():
    x = np.random.default_rng(4).normal(size=(7, 20, 100))
    parts = decompose20(x, CHANNELS)
    assert parts.effective_dimensions == (7, 7, 3, 1, 1)
    expected = x - x.mean(axis=1, keepdims=True)
    np.testing.assert_allclose(reconstruct20(parts), expected, atol=2e-15, rtol=1e-13)
    z = coordinates19(parts)
    assert z.shape == (7, 19, 100)
    np.testing.assert_allclose(reconstruct20(from_coordinates19(z, CHANNELS)), expected, atol=3e-15, rtol=1e-13)
    forward, inverse = linear_maps(CHANNELS)
    assert np.linalg.matrix_rank(forward) == 19
    np.testing.assert_allclose(inverse @ forward, np.eye(20) - np.ones((20, 20)) / 20, atol=1e-15)
    np.testing.assert_allclose(forward @ inverse, np.eye(19), atol=1e-15)


def test_actual_channel_order_is_respected_and_no_missing_channel_imputation():
    rng = np.random.default_rng(6)
    order = rng.permutation(20)
    names = tuple(CHANNELS[i] for i in order)
    x = rng.normal(size=(3, 20, 10))
    parts = decompose20(x[:, order], names)
    np.testing.assert_allclose(reconstruct20(parts), (x - x.mean(axis=1, keepdims=True))[:, order], atol=1e-14)
    for bad_names in (CHANNELS[:-1], CHANNELS[:-1] + ('VREF',), CHANNELS[:-1] + (CHANNELS[0],)):
        with pytest.raises(ValueError, match='COMPLETE_20_CHANNEL_LAYOUT'):
            decompose20(x, bad_names)


def test_right_numeric_intervention_exactly_preserves_left_but_changes_joint():
    world = inject_spatial_world('right_perturbation')
    a = decompose20(world['data'], world['channel_names'])
    b = decompose20(world['changed'], world['channel_names'])
    np.testing.assert_array_equal(a.u_L, b.u_L)
    np.testing.assert_array_equal(a.u_M, b.u_M)
    assert not np.array_equal(a.m_LR, b.m_LR)
    assert not np.array_equal(a.m_M, b.m_M)
    np.testing.assert_array_equal(a.u_L, local_center(world['data'][:, :8]))


def test_common_reference_drift_changes_no_spatial_component():
    world = inject_spatial_world('reference_drift')
    a, b = [decompose20(world[name], CHANNELS) for name in ('data', 'changed')]
    for key in COMPONENT_ORDER:
        np.testing.assert_allclose(getattr(a, key), getattr(b, key), atol=1e-14, rtol=1e-13)


def test_cross_group_mean_signal_is_destroyed_locally_and_recovered_explicitly():
    world = inject_spatial_world('crossmean')
    parts = decompose20(world['data'], CHANNELS)
    assert not np.any(parts.u_L) and not np.any(parts.u_R)
    assert not np.any(parts.u_M) and not np.any(parts.m_M)
    labels = (parts.m_LR[:, 0].mean(axis=-1) > 0).astype(int)
    np.testing.assert_array_equal(labels, world['labels'])
    views = l0_views(parts)
    assert not np.any(views['S0'])
    assert not np.any(views['S0_DUP_S1']) and not np.any(views['S0_DUP_S2'])
    assert np.any(views['S1']) and np.any(views['S2'])


def test_only_midline_mean_and_only_local_contrast_are_distinct_worlds():
    world = inject_spatial_world('midline')
    parts = decompose20(world['data'], CHANNELS)
    views = l0_views(parts)
    assert not np.any(views['S0']) and not np.any(views['S1'])
    assert np.any(views['S2'])
    np.testing.assert_array_equal((parts.m_M[:, 0].mean(axis=-1) > 0).astype(int), world['labels'])
    world = inject_spatial_world('local_left')
    parts = decompose20(world['data'], CHANNELS)
    assert np.any(parts.u_L) and not np.any(parts.u_R)
    assert not np.any(parts.m_LR) and not np.any(parts.m_M)
    np.testing.assert_array_equal((parts.u_L[:, 0].mean(axis=-1) > 0).astype(int), world['labels'])


def test_l0_fixed_sample_units_and_duplicate_widths():
    x = np.broadcast_to(np.arange(10.), (4, 20, 10)).copy()
    np.testing.assert_array_equal(bin_20ms(x), np.broadcast_to([2., 7.], (4, 20, 2)))
    parts = decompose20(np.random.default_rng(3).normal(size=(4, 20, 100)), CHANNELS)
    views = l0_views(parts)
    assert {key: value.shape[1] for key, value in views.items()} == {
        'S0': 320, 'S1': 340, 'S2': 440, 'FULL20': 400, 'S0_DUP_S1': 340, 'S0_DUP_S2': 440}
    np.testing.assert_array_equal(views['S0_DUP_S1'][:, :320], views['S0'])
    np.testing.assert_array_equal(views['S0_DUP_S1'][:, 320:], views['S0'][:, :20])
    with pytest.raises(ValueError, match='250HZ'):
        bin_20ms(x, sfreq=1000.)
    with pytest.raises(ValueError, match='COMPLETE_20MS'):
        bin_20ms(x[..., :9])


def test_linear_head_can_be_composed_exactly_across_reversible_coordinates():
    rng = np.random.default_rng(9)
    forward, inverse = linear_maps(CHANNELS)
    raw = rng.normal(size=(11, 20))
    global_reference = raw - raw.mean(axis=1, keepdims=True)
    z = raw @ forward.T
    head20 = rng.normal(size=(3, 20))
    bias = rng.normal(size=3)
    head19 = head20 @ inverse
    np.testing.assert_allclose(global_reference @ head20.T + bias, z @ head19.T + bias, atol=1e-13)
    for n in (4, 8):
        basis = helmert_basis(n)
        np.testing.assert_allclose(basis.T @ basis, np.eye(n - 1), atol=1e-15)
        np.testing.assert_allclose(basis.sum(axis=0), 0., atol=1e-15)
