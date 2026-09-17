"""Synthetic C2-S runner contracts; Slurm execution only."""
import pickle
import numpy as np
import pandas as pd
import pytest

from auditory5.contracts import FitScope
from auditory_next import spatial_execution as spatial


def _pool():
    rows = pd.DataFrame(dict(trial_id=[f"t{k}" for k in range(40)], record_id=np.repeat([f"r{k}" for k in range(20)], 2),
        split_group_id=np.repeat([f"g{k}" for k in range(20)], 2), stimulus_local_id=np.tile([0, 1], 20)))
    groups = set(rows.split_group_id)
    folds = []
    for fold in range(5):
        test = {f"g{k}" for k in range(fold * 4, fold * 4 + 4)}
        folds.append(dict(outer_fold=fold, train_groups=sorted(groups - test), test_groups=sorted(test)))
    return rows, folds


def test_post_start_is_per_row_and_exact_20ms_means_follow_geometry():
    x = np.random.default_rng(6).normal(size=(3, 20, 175))
    starts = np.array([0., 21., 75.])  # Nullable event tables can store exact integers as floats.
    views, audit = spatial.extract_views(x, starts, spatial.CHANNELS)
    expected = np.stack([trial[:, int(j):int(j)+100] for trial, j in zip(x, starts)])
    expected -= expected.mean(axis=1, keepdims=True)
    expected = expected.reshape(3, 20, 20, 5).mean(axis=-1).reshape(3, 400)
    np.testing.assert_allclose(views["FULL20"], expected, atol=1e-13)
    assert {name: value.shape for name, value in views.items()} == {k: (3, v) for k, v in spatial.WIDTHS.items()}
    assert audit["effective_spatial_dimensions"] == 19
    assert audit["numeric_isolation"] and not audit["selection_isolation"]
    assert max(audit[k] for k in ("max_reconstruction_error", "max_full_epoch_reconstruction_error", "max_19dim_reconstruction_error")) < 1e-12


@pytest.mark.parametrize("starts", [[.1, 0], [-1, 0], [0, 76], [np.nan, 0]])
def test_sample_indices_cannot_be_truncated_padded_or_shifted(starts):
    with pytest.raises(ValueError, match="C2S_"):
        spatial.extract_views(np.zeros((2, 20, 175)), starts, spatial.CHANNELS)
    with pytest.raises(ValueError, match="C2S_EXACT_POST"):
        spatial.extract_views(np.zeros((2, 20, 175)), [0, 0], spatial.CHANNELS, processed_fs=1000)


def test_common_pool_does_not_gain_a_new_twenty_trials_per_class_exclusion():
    rows, folds = _pool()
    result = spatial.support_audit(rows, folds)
    assert result["status"] == "SUFFICIENT_FOR_SCREEN"
    assert result["minimum_trials_class0"] == result["minimum_trials_class1"] == 1
    assert result["extra_trial_count_exclusions"] == 0
    changed = rows.copy()
    changed.loc[changed.split_group_id.eq("g0"), "stimulus_local_id"] = 0
    bad = spatial.support_audit(changed, folds)
    assert bad["status"] == "SUPPORT_INSUFFICIENT" and bad["candidates"] == 20
    assert not bad["all_candidates_have_both_classes"]
    folds[1]["test_groups"] = folds[0]["test_groups"]
    with pytest.raises(ValueError, match="C2S_OUTER|C2S_TEST_IDENTITIES"):
        spatial.support_audit(rows, folds)


def test_six_view_bootstrap_is_paired_and_cannot_hide_missing_cells():
    base = np.linspace(.7, 1.2, 20)
    table = pd.DataFrame({view: base.copy() for view in spatial.VIEWS}, index=[f"g{k}" for k in range(20)])
    table["S1"] -= .02
    table["S2"] -= .03
    rows = spatial.paired_spatial_summary(table)
    by_name = {r["statistic"]: r for r in rows}
    for name, value in (("G_crossmean", .02), ("G_midline", .01), ("complete_spatial_matched_width_margin", .03)):
        assert by_name[name]["estimate"] == pytest.approx(value)
        assert by_name[name]["ci_lower"] == pytest.approx(value)
        assert by_name[name]["ci_upper"] == pytest.approx(value)
        assert by_name[name]["n_candidates"] == 20
    assert spatial.paired_spatial_summary(table.iloc[::-1]) == rows
    with pytest.raises(ValueError, match="SIX_VIEW"):
        spatial.paired_spatial_summary(table.drop(columns="FULL20"))
    table.loc["g0", "S2"] = np.nan
    with pytest.raises(ValueError, match="FAILED_MODEL"):
        spatial.paired_spatial_summary(table)


def test_thirteen_head_fits_use_only_training_groups_and_prediction_cannot_refit():
    rng = np.random.default_rng(8)
    y, groups = np.tile([0, 1], 24), np.repeat([f"train{k}" for k in range(6)], 8)
    x = rng.normal(size=(48, 6))
    x[:, 0] += .4 * y
    scope = FitScope(tuple(np.unique(groups)), test_groups=("test_a", "test_b"))
    fits = []
    model = spatial.fit_spatial_probe(x, y, groups, scope, on_fit=fits.append)
    assert sum(item["status"] == "STARTED" for item in fits) == 13
    assert sum(item["status"] == "PASS" for item in fits) == 13
    for item in fits:
        s = item["scope"]
        assert not set(s["train_groups"]) & set(s["validation_groups"] + s["test_groups"])
        assert set(s["train_groups"]) <= set(groups)
    assert model.evidence["PCA"] == "NONE"
    assert model.evidence["calibration"]["bounds"] == [.25, 16.]
    saved = pickle.dumps(model)
    model.predict(rng.normal(size=(5, 6)) * 1000)
    assert pickle.dumps(model) == saved
    changed = groups.copy()
    changed[:8] = "test_a"
    with pytest.raises(ValueError, match="LEAKAGE"):
        spatial.fit_spatial_probe(x, y, changed, scope)
    assert len(fits) == 26


def test_smoke_only_uses_metadata_selected_geometry_and_fits_no_head(tmp_path, monkeypatch):
    rows, folds = _pool()
    monkeypatch.setattr(spatial, "ROOT", tmp_path)
    monkeypatch.setattr(spatial, "_sources", lambda *args: ({}, {"folds": folds}, {}, rows, None))
    monkeypatch.setattr(spatial, "finish", lambda private, public, summary: summary)
    observed = []

    def geometry(dest, legacy, selected, inventory, hashes, *, smoke):
        observed.append(smoke)
        return {}, dict(status="PASS", records=1, numeric_isolation=True, selection_isolation=False)

    def forbidden(*args, **kwargs):
        pytest.fail("a geometry-only smoke must not fit a readout")

    monkeypatch.setattr(spatial, "_feature_bank", geometry)
    monkeypatch.setattr(spatial, "fit_spatial_probe", forbidden)
    paths = [tmp_path / base / "auditory_next_v2" / "smoke" for base in ("private", "results", "reports")]
    for path in paths:
        path.mkdir(parents=True)
    config = dict(calibration={"new_T_bounds": [.25, 16]}, readouts={"legacy_C_or_alpha_grid": list(spatial.C_GRID), "seed": 11},
                  preprocessing={"sample_rate": 250, "post_seconds": [.05, .45], "default_source": "P1_CAUSAL20"})
    result = spatial.run(config, {}, {}, *paths, {"support_run": "synthetic"}, smoke=True)
    assert result["status"] == "PASS" and result["head_fits_attempted"] == 0
    assert not result["main_matrix_complete"] and observed == [True]
