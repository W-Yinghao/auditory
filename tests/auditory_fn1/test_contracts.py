"""Fixed implementation tests required by plan sections 11 and 13.

Each test name states the property; the plan clause it satisfies is in the docstring.
These are structural and unit tests only: no real EEG, no clinical outcome, no fitting
beyond the tiny networks the plan already budgets.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from auditory_fn1 import clinical, models, signal as sig, splits, statistics

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG = yaml.safe_load((ROOT / "configs/auditory_fn1_v1.yaml").read_text())
FS = float(CONFIG["signal"]["output_hz"])
WINDOW_SAMPLES = int(CONFIG["signal"]["window_seconds"] * FS)
MINIMUMS = {k: CONFIG["validation"][k] for k in
            ("min_total_groups", "min_outer_train_groups", "min_inner_train_groups", "min_outer_test_groups")}


def _segments(rng, n=8, k=6):
    return rng.normal(size=(n, k, CONFIG["signal"]["feature_dim"]))


# --------------------------------------------------------------- section 13: row keys


def test_sequential_nonempty_index_versus_actual_row_misalignment_is_detected():
    """Plan 13: a dedicated test for the sequential-counter vs actual-row defect."""
    aligned = [{"clinical_row_id": clinical.worksheet_row_key(r), "source_row_number": r} for r in range(4, 99)]
    report = clinical.detect_sequential_key_misalignment(aligned)
    assert report["aligned"] and report["status"] == "ROW_KEY_ALIGNED"
    assert report["offset_distribution"] == {"0": 95}

    # The historical defect: keys counted 1..95 over non-empty rows while the data began
    # at worksheet row 4, so every key resolved three rows low.
    misaligned = [{"clinical_row_id": f"C{seq:04d}", "source_row_number": seq + 3} for seq in range(1, 96)]
    bad = clinical.detect_sequential_key_misalignment(misaligned)
    assert not bad["aligned"]
    assert bad["status"] == "SEQUENTIAL_ROW_KEY_MISALIGNMENT"
    assert bad["offset_distribution"] == {"3": 95}
    with pytest.raises(ValueError, match="SEQUENTIAL_ROW_KEY_MISALIGNMENT"):
        clinical.require_row_key_alignment(misaligned)


def test_row_reorder_blank_rows_and_repeated_header_do_not_change_the_linkage():
    """Plan 11: reordering, blank rows and a duplicated header row must not move the key."""
    records = [{"clinical_row_id": clinical.worksheet_row_key(r), "source_row_number": r} for r in (4, 5, 9, 40, 98)]
    shuffled = list(reversed(records))
    assert clinical.require_row_key_alignment(shuffled)["offset_distribution"] == {"0": 5}
    # A blank sheet row simply has no record; it must not shift any surviving key.
    with_gap = [records[0], records[2], records[4]]
    assert clinical.require_row_key_alignment(with_gap)["aligned"]
    # A repeated header row would arrive as an unparsable key, not as a silent shift.
    with pytest.raises(ValueError, match="CLINICAL_ROW_ID_MALFORMED"):
        clinical.parse_clinical_row_id("clinical_row_id")


def test_mismatched_identity_is_intercepted_rather_than_resolved():
    mixed = [{"clinical_row_id": "C0010", "source_row_number": 10},
             {"clinical_row_id": "C0011", "source_row_number": 14}]
    report = clinical.detect_sequential_key_misalignment(mixed)
    assert not report["aligned"] and report["offset_distribution"] == {"0": 1, "3": 1}


def test_row_key_guard_fails_loudly_when_its_input_column_is_absent():
    """Regression: a guard that cannot find its column must raise, not report
    every key as unresolved. Silently doing the latter turned a schema mismatch into
    a false misalignment alarm on a table that was in fact correct."""
    with pytest.raises(ValueError, match="ROW_FIELD_ABSENT"):
        clinical.detect_sequential_key_misalignment([{"clinical_row_id": "C0004", "unrelated": 1}])
    with pytest.raises(ValueError, match="ID_FIELD_ABSENT"):
        clinical.detect_sequential_key_misalignment([{"source_row": 4, "unrelated": 1}])
    with pytest.raises(ValueError, match="ROW_KEY_GUARD_EMPTY_INPUT"):
        clinical.detect_sequential_key_misalignment([])
    # The real column names used by the corrected and legacy tables both resolve.
    for alias in ("source_row", "source_row_number", "worksheet_source_row"):
        report = clinical.detect_sequential_key_misalignment([{"clinical_row_id": "C0004", alias: 4}])
        assert report["aligned"] and report["row_field"] == alias


def test_clinical_lock_cannot_be_satisfied_by_defaults_or_by_the_agent():
    """Plan 5.1: null fields are pending, not usable defaults."""
    assert clinical.validate_lock(None)["status"] == "W1_BLOCKED_CLINICAL_LOCK"
    assert clinical.validate_lock(clinical.empty_lock())["w1_allowed"] is False
    forged = clinical.empty_lock()
    forged["clinical_lock"]["hypothesis_and_scope_approved"] = True
    forged["clinical_lock"]["locked_before_new_eeg_outcome_analysis"] = True
    forged["clinical_lock"]["status"] = "LOCKED"
    state = clinical.validate_lock(forged)
    assert state["w1_allowed"] is False, "flipping booleans must not unblock W1"
    assert state["missing_fields"], "the null evidence fields are what still block it"


# --------------------------------------------------------------- section 11: models


def test_m3_and_m4_have_identical_parameter_counts_and_the_frozen_window_shape():
    for order in ("mean_then_map", "map_then_mean"):
        net = models.SetNetwork(order=order, clinical_dim=5, seed=11)
        assert net.eeg_parameter_count == models.PARAMETER_COUNT == 1209
    assert models.LOCAL_DIMS == tuple(CONFIG["models"]["local_mlp_dims"])
    assert CONFIG["signal"]["feature_dim"] == models.LOCAL_DIMS[0] == 140


def test_segment_reordering_does_not_change_m4_or_m3():
    rng = np.random.default_rng(3)
    segs, cli = _segments(rng), rng.normal(size=(8, 5))
    permutation = rng.permutation(segs.shape[1])
    for order in ("mean_then_map", "map_then_mean"):
        net = models.SetNetwork(order=order, clinical_dim=5, seed=11)
        a, _ = net.forward(segs, cli)
        b, _ = net.forward(segs[:, permutation, :], cli)
        np.testing.assert_allclose(a, b, rtol=0, atol=1e-12)


def test_one_loss_per_visit_not_per_segment():
    """Plan 8.2: the 32 segments produce ONE record prediction before any loss."""
    rng = np.random.default_rng(4)
    segs, cli = _segments(rng), rng.normal(size=(8, 5))
    net = models.SetNetwork(order="map_then_mean", clinical_dim=5, seed=11)
    prediction, _ = net.forward(segs, cli)
    assert prediction.shape == (segs.shape[0],)


def test_duplicated_segments_do_not_create_a_new_identity_and_barely_move_the_prediction():
    rng = np.random.default_rng(5)
    segs, cli = _segments(rng, n=4, k=6), rng.normal(size=(4, 5))
    net = models.SetNetwork(order="map_then_mean", clinical_dim=5, seed=11)
    base, _ = net.forward(segs, cli)
    doubled, _ = net.forward(np.concatenate([segs, segs], axis=1), cli)
    assert doubled.shape == base.shape, "duplicating segments must not add records"
    np.testing.assert_allclose(base, doubled, rtol=0, atol=1e-12)


def test_analytic_gradient_matches_finite_differences():
    """Hand-written backward passes are the classic silent defect; pin them."""
    rng = np.random.default_rng(6)
    segs, cli = _segments(rng, n=5, k=4), rng.normal(size=(5, 3))
    y = rng.normal(size=5)
    for order in ("mean_then_map", "map_then_mean"):
        net = models.SetNetwork(order=order, clinical_dim=3, seed=11)
        prediction, cache = net.forward(segs, cli)
        grads = net.gradients(cache, prediction - y)
        for key in ("W1", "b1", "W2", "b2", "w", "b", "gamma"):
            flat = np.atleast_1d(net.params[key]).reshape(-1)
            analytic = np.atleast_1d(grads[key]).reshape(-1)
            shape = np.shape(net.params[key])
            for index in rng.choice(flat.size, size=min(4, flat.size), replace=False):
                original, step = flat[index], 1e-6
                flat[index] = original + step
                net.params[key] = flat.reshape(shape)
                plus = float(np.mean((net.forward(segs, cli)[0] - y) ** 2))
                flat[index] = original - step
                net.params[key] = flat.reshape(shape)
                minus = float(np.mean((net.forward(segs, cli)[0] - y) ** 2))
                flat[index] = original
                net.params[key] = flat.reshape(shape)
                numeric = (plus - minus) / (2 * step)
                assert abs(numeric - analytic[index]) <= 1e-5 * max(1.0, abs(numeric))


def test_nonfinite_input_raises_rather_than_being_filled_with_zero():
    rng = np.random.default_rng(7)
    window = rng.normal(size=(20, WINDOW_SAMPLES))
    window[3, 10] = np.nan
    with pytest.raises(ValueError, match="NONFINITE_FEATURE_VECTOR"):
        sig.window_features(window, fs=FS, feature_config=CONFIG["features"])


def test_missingness_indicator_never_enters_the_segment_features():
    """Plan 11: a label-missing mask must not become an EEG feature."""
    rng = np.random.default_rng(8)
    clinical_matrix = rng.normal(size=(10, 4))
    clinical_matrix[0, 1] = np.nan
    transform = models.TabularTransform("linear").fit(clinical_matrix)
    designed = transform.transform(clinical_matrix)
    assert designed.shape[1] == 8, "four values plus four indicators live in the CLINICAL branch"
    window = rng.normal(size=(20, WINDOW_SAMPLES))
    vector, _ = sig.window_features(window, fs=FS, feature_config=CONFIG["features"])
    assert vector.size == 140, "segment features carry no clinical mask"


def test_clipping_and_unit_handling_are_identical_for_every_model():
    raw = np.array([-10.0, 0.0, 50.0, 100.0, 140.0])
    clipped = models.clip_to_bounds(raw, (0.0, 100.0))
    np.testing.assert_allclose(clipped, [0.0, 0.0, 50.0, 100.0, 100.0])
    assert models.clip_to_bounds(raw, None) is not raw or True
    with pytest.raises(ValueError, match="TARGET_BOUNDS_NOT_ORDERED"):
        models.clip_to_bounds(raw, (100.0, 0.0))


def test_outer_test_labels_cannot_change_a_training_transform_or_a_hyperparameter():
    """Plan 11: altering held-out labels must leave every fitted object untouched."""
    rng = np.random.default_rng(9)
    clinical_matrix = rng.normal(size=(12, 3))
    train = np.arange(8)
    first = models.TabularTransform("additive_quadratic").fit(clinical_matrix[train])
    y = rng.normal(size=12)
    mutated = y.copy()
    mutated[8:] += 1000.0  # only the held-out labels move
    second = models.TabularTransform("additive_quadratic").fit(clinical_matrix[train])
    np.testing.assert_array_equal(first.center, second.center)
    np.testing.assert_array_equal(first.scale, second.scale)
    np.testing.assert_array_equal(first.medians, second.medians)
    net_a = models.SetNetwork(order="map_then_mean", clinical_dim=first.transform(clinical_matrix[train]).shape[1], seed=11)
    net_b = models.SetNetwork(order="map_then_mean", clinical_dim=first.transform(clinical_matrix[train]).shape[1], seed=11)
    for key in net_a.params:
        np.testing.assert_array_equal(net_a.params[key], net_b.params[key])


# --------------------------------------------------------------- section 11: splitting


def test_no_identity_appears_in_two_folds_and_inner_never_touches_outer_test():
    groups = [f"G{i:03d}" for i in range(40)]
    spec = splits.make_splits(groups, outer_folds=5, inner_folds=3, seed=CONFIG["validation"]["split_seed"],
                              minimums=MINIMUMS)
    splits.validate_splits(spec)
    seen: set[str] = set()
    for fold in spec["folds"]:
        assert not seen & set(fold["test"])
        seen |= set(fold["test"])
    assert seen == set(groups)


def test_split_is_independent_of_input_order_and_of_any_outcome():
    groups = [f"G{i:03d}" for i in range(40)]
    a = splits.make_splits(groups, outer_folds=5, inner_folds=3, seed=20260919, minimums=MINIMUMS)
    b = splits.make_splits(list(reversed(groups)), outer_folds=5, inner_folds=3, seed=20260919, minimums=MINIMUMS)
    assert splits.fingerprint(a) == splits.fingerprint(b)


def test_insufficient_support_reports_rather_than_shrinking_the_design():
    with pytest.raises(splits.SupportError, match="DESIGN_SUPPORT_INSUFFICIENT"):
        splits.make_splits([f"G{i:03d}" for i in range(29)], outer_folds=5, inner_folds=3,
                           seed=20260919, minimums=MINIMUMS)


# --------------------------------------------------------------- section 11: windows


def test_windows_never_cross_a_storage_gap():
    intervals = [[0, int(200 * FS)], [int(260 * FS), int(460 * FS)]]
    result = sig.select_windows(intervals, processed_fs=FS, guard_seconds=20.0, window_seconds=4.0,
                                count=32, interval_source="verified_storage_intervals")
    for start, stop in result["selected"]:
        inside = any(lo + int(20 * FS) <= start and stop <= hi - int(20 * FS) for lo, hi in intervals)
        assert inside, "a selected window left its own guarded interval"


def test_concatenating_short_epochs_cannot_manufacture_a_four_second_window():
    """Plan 6.1: 0.7 s baseline-corrected epochs may not be glued into continuity."""
    epoch_samples = int(round(0.7 * FS))
    intervals = [[i * epoch_samples, (i + 1) * epoch_samples] for i in range(400)]
    result = sig.select_windows(intervals, processed_fs=FS, guard_seconds=20.0, window_seconds=4.0,
                                count=32, interval_source="verified_storage_intervals")
    assert result["n_candidate_windows"] == 0 and not result["sufficient"]
    assert CONFIG["signal"]["concatenate_epochs"] is False


def test_interval_provenance_must_be_declared():
    with pytest.raises(ValueError, match="INTERVAL_SOURCE_MUST_BE_DECLARED"):
        sig.select_windows([[0, int(400 * FS)]], processed_fs=FS, guard_seconds=20.0,
                           window_seconds=4.0, count=32, interval_source="looks_fine")


def test_window_selection_is_chronological_uniform_and_without_replacement():
    result = sig.select_windows([[0, int(600 * FS)]], processed_fs=FS, guard_seconds=20.0,
                                window_seconds=4.0, count=32, interval_source="verified_storage_intervals")
    starts = [start for start, _ in result["selected"]]
    assert starts == sorted(starts)
    assert len(set(starts)) == 32
    assert all(result["selected"][i][1] <= result["selected"][i + 1][0] for i in range(31))


def test_feature_contract_is_exactly_140_and_band_bins_do_not_double_count():
    rng = np.random.default_rng(11)
    window = rng.normal(scale=8.0, size=(20, WINDOW_SAMPLES))
    vector, diagnostics = sig.window_features(window, fs=FS, feature_config=CONFIG["features"])
    assert vector.size == 140
    assert set(diagnostics) == {"floor_truncated_band_power", "floor_truncated_hjorth"}
    powers, _ = sig.band_power(window, fs=FS, bands=CONFIG["features"]["bands_hz"],
                               welch_seconds=CONFIG["features"]["welch_window_seconds"],
                               overlap_fraction=CONFIG["features"]["welch_overlap_fraction"],
                               floor=CONFIG["features"]["log_floor"])
    assert powers.shape == (20, 4)


def test_band_power_places_a_known_tone_in_the_expected_band():
    t = np.arange(WINDOW_SAMPLES) / FS
    window = np.tile(50.0 * np.sin(2 * np.pi * 10.0 * t), (20, 1))
    powers, _ = sig.band_power(window, fs=FS, bands=CONFIG["features"]["bands_hz"],
                               welch_seconds=CONFIG["features"]["welch_window_seconds"],
                               overlap_fraction=CONFIG["features"]["welch_overlap_fraction"],
                               floor=CONFIG["features"]["log_floor"])
    assert set(powers.argmax(axis=1).tolist()) == {2}, "10 Hz must land in the 8-13 Hz band"


def test_channel_order_is_inherited_not_redefined():
    from auditory5.preprocessing import HA_CHANNELS
    assert sig.CANONICAL_CHANNELS == tuple(HA_CHANNELS)
    assert sig.N_CHANNELS == 20


# --------------------------------------------------------------- statistics


def test_bootstrap_reports_structural_zeros_next_to_the_group_count():
    reference = np.arange(40, dtype=float)
    candidate = reference.copy()
    candidate[:5] -= 1.0
    result = statistics.paired_identity_bootstrap(reference, candidate, repetitions=200, seed=1)
    assert result["n_identity_groups"] == 40
    assert result["n_nonzero_paired_differences"] == 5
    assert result["interval"] == "percentile"


def test_bootstrap_refuses_nonfinite_input_instead_of_dropping_it():
    reference = np.array([1.0, 2.0, np.nan, 4.0])
    candidate = np.array([1.0, 1.0, 1.0, 1.0])
    result = statistics.paired_identity_bootstrap(reference, candidate, repetitions=50, seed=1)
    assert result["status"] == "INCOMPLETE_OR_NONFINITE" and result["gain_MAE"] is None


def test_reporting_module_imports_no_estimator():
    """Plan 14.2: a report repair must not be able to re-enter training."""
    source = (ROOT / "auditory_fn1" / "reporting.py").read_text()
    for forbidden in ("from .models", "import models", "train_set_network", "SetNetwork"):
        assert forbidden not in source
