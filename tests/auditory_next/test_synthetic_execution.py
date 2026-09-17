"""Pure synthetic contracts; no classifier, calibration or encoder fitting."""
from copy import deepcopy
import json

import numpy as np
import pandas as pd
import pytest

from auditory_next import synthetic_execution as execution
from auditory_next.a2_residual_audit import identity_contrast
from auditory_next.provenance import digest


def _spec(packet, mechanism=None, repeat=0):
    return next(row for row in execution.planned_worlds() if row["packet"] == packet and
                (mechanism is None or row["mechanism"] == mechanism) and row["world_index"] == repeat)


def test_complete_independent_world_and_fit_allowances():
    specifications = execution.planned_worlds()
    assert len(specifications) == 660
    assert sum(s["route_world"] for s in specifications) == 600
    assert len({s["id"] for s in specifications}) == 660
    assert sum(len(s["specs"]) for s in specifications) == 1920
    assert sum(family == "mlp32" for s in specifications for family, _ in s["specs"]) == 630
    assert execution.planned_worlds() == specifications


@pytest.mark.parametrize("packet,mechanism", [
    ("N1", "PRIOR_ONLY"), ("N1", "BACKGROUND_KEY"), ("N1", "ADDITIVE_NOISE"),
    ("N1", "INDEPENDENT_BACKGROUND"), ("N3", "HISTORY_ONLY"),
    ("N3", "EEG_INCREMENT"), ("N3", "NEAR_DETERMINISTIC_HISTORY")])
def test_actual_size_is_60_candidates_600_trials_not_4500_children(packet, mechanism):
    world = execution.make_world(_spec(packet, mechanism))
    y, g, train, test = execution._validate_world(world)
    assert len(y) == 36000
    assert set(np.unique(g, return_counts=True)[1]) == {600}
    assert len(set(g[train])) == 36 and len(set(g[test])) == 24
    assert not set(g[train]) & set(g[test])


def test_time_drift_has_frozen_class_support_and_observed_global_time():
    spec = _spec("N2", "TIME_DRIFT")
    world = execution.make_world(spec)
    y, g, train, test = execution._validate_world(world)
    assert world["bags"].shape == (4800, 8, 2)
    assert set(np.unique(g, return_counts=True)[1]) == {80}
    time = world["H_BAG"][:, 1]
    assert np.array_equal(time, np.linspace(0, 1, 4800))
    counts = []
    for group in np.unique(world["group_id"]):
        own = world["group_id"] == group
        expected = np.clip(np.rint((.2 + .6 * time[own].mean()) * 80), 1, 79)
        assert y[own].sum() == expected
        counts.append(expected)
    assert counts[0] < counts[-1]
    again = execution.make_world(spec)
    assert np.array_equal(world["bags"], again["bags"])
    assert np.array_equal(y, again["y"])


@pytest.mark.parametrize("packet,mechanism", [("N1", "BACKGROUND_KEY"), ("N3", "EEG_INCREMENT")])
def test_heldout_eeg_and_labels_cannot_change_training_noise_or_views(packet, mechanism):
    spec = _spec(packet, mechanism)
    world = execution.make_world(spec, trials_per_candidate=8)
    first, first_artifacts = execution.build_views(world, packet, spec["seed"])
    changed = deepcopy(world)
    test = changed["test_mask"]
    for field in ("H", "P", "B"):
        changed[field][test] += 1e8
    changed["y"][test] = 1 - changed["y"][test]
    second, second_artifacts = execution.build_views(changed, packet, spec["seed"])
    for view in first:
        assert np.array_equal(first[view][world["train_mask"]], second[view][world["train_mask"]])
    noise_view = "HPBnoise" if packet == "N1" else "Hnoise"
    assert np.array_equal(first[noise_view][:, -1], second[noise_view][:, -1])
    for attribute in ("mean_", "scale_"):
        assert np.array_equal(getattr(first_artifacts["noise_training_scale"], attribute),
                              getattr(second_artifacts["noise_training_scale"], attribute))


def test_n2_heldout_bags_do_not_change_training_pca_rff_or_training_views():
    spec = _spec("N2", "COVARIANCE_SIGNAL")
    world = execution.make_world(spec, bags_per_candidate=8)
    original, _ = execution.build_views(world, "N2", spec["seed"])
    changed = deepcopy(world)
    changed["bags"][changed["test_mask"]] += 1e6
    changed["y"][changed["test_mask"]] = 1 - changed["y"][changed["test_mask"]]
    new, _ = execution.build_views(changed, "N2", spec["seed"])
    assert set(original) == {"H", "HMU", "HMUVAR", "HMUMU", "HVAR", "HRFF"}
    for view in original:
        assert np.array_equal(original[view][world["train_mask"]], new[view][world["train_mask"]])


def test_identity_bootstrap_excludes_repeated_identity_from_mismatches():
    matrix = np.array([[2., .1, -.4], [.7, 3., -.2], [.3, -.1, 4.]])
    ids = np.array(["synthetic_a", "synthetic_b", "synthetic_c"])
    indices = np.random.default_rng(22).integers(0, 3, (2000, 3))
    values, invalid = [], 0
    for index in indices:
        if len(set(index)) < 2:
            invalid += 1
        else:
            values.append(identity_contrast(matrix[np.ix_(index, index)], ids[index])["gain"])
    actual = execution.identity_bootstrap(matrix, ids, seed=22)
    assert actual["invalid_replicates"] == invalid > 0
    assert actual["estimate"] == pytest.approx(identity_contrast(matrix, ids)["gain"])
    assert actual["ci_lower"] == pytest.approx(np.quantile(values, .025), abs=1e-12)
    assert actual["ci_upper"] == pytest.approx(np.quantile(values, .975), abs=1e-12)


def test_paired_contrasts_preserve_same_candidates_and_reject_nan():
    losses = pd.DataFrame(dict(base=[1., 2., 3.], post=[.8, 1.8, 2.8], noise=[1.1, 2.1, 3.1]), index=["a", "b", "c"])
    result = execution.paired_loss_contrasts(losses, {"main": ("base", "post"), "noise": ("noise", "post")}, seed=1, threshold=.005)
    assert result["main"]["estimate"] == pytest.approx(.2)
    assert result["main"]["ci_lower"] == pytest.approx(.2)
    assert result["noise"]["ci_upper"] == pytest.approx(.3)
    assert result["main"]["screen"] is True
    losses.loc["a", "post"] = np.nan
    with pytest.raises(ValueError, match="COMPLETE_CANDIDATE_LOSSES"):
        execution.paired_loss_contrasts(losses, {"main": ("base", "post")}, seed=1, threshold=.005)


def test_unknown_worlds_are_never_negative_in_rate_denominator():
    rows = [dict(world_id=str(i), status="EVALUATED" if i < 10 else "NUMERICAL_FAILURE", screen=i < 5 if i < 10 else None) for i in range(30)]
    result = execution.rate_summary(rows, 30)
    assert (result["n_planned"], result["n_evaluable"], result["n_positive"], result["n_unknown"]) == (30, 10, 5, 20)
    assert result["positive_rate_among_evaluable"] == .5
    assert result["identified_rate_lower"] == 5 / 30
    assert result["identified_rate_upper"] == 25 / 30
    assert result["monte_carlo_ci_lower"] < 5 / 30 and result["monte_carlo_ci_upper"] > 25 / 30
    unknown = execution.rate_summary([dict(world_id=str(i), status="NOT_EVALUATED", screen=None) for i in range(30)], 30)
    assert unknown["monte_carlo_ci_lower"] == 0 and unknown["monte_carlo_ci_upper"] == 1
    assert unknown["positive_rate_among_evaluable"] is None
    with pytest.raises(ValueError, match="PLANNED_WORLD_DENOMINATOR"):
        execution.rate_summary(rows[:-1], 30)


def test_one_required_failure_withholds_whole_world_and_keeps_g0_null_identity(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Incomplete world must never predict its successful heads")
    monkeypatch.setattr(execution, "predict_logits", forbidden)
    g0 = dict(_spec("G0"), injected=False, fit_ids=["failed"], folder=str(tmp_path))
    n3 = dict(_spec("N3"), injected=None, fit_ids=["success", "failed"], folder=str(tmp_path))
    rows = execution.score_worlds([g0, n3], {"success": object()}, [dict(fit_id="success", numerical_status="OPTIMIZATION_STABLE")], tmp_path)
    assert len(rows) == 3 and all(row["status"] == "NUMERICAL_FAILURE" and row["screen"] is None for row in rows)
    assert rows[0]["mechanism"] == "null" and rows[0]["expected_positive"] is False
    assert {row["family"] for row in rows[1:]} == {"logistic", "mlp32"}


def test_catalog_excludes_gate_fit_allowances_and_binds_every_real_allowance(tmp_path, monkeypatch):
    monkeypatch.setattr(execution, "ROOT", tmp_path)
    rows = []
    for spec in execution.planned_worlds():
        for family, view in spec["specs"]:
            population = "equal_candidate" if spec["packet"] == "A2" else "P_bal" if spec["packet"] in ("N2", "G0") else "P_nat"
            rows.append(dict(packet=spec["packet"], mode="synthetic", population=population, family=family, view=view,
                mechanism=spec["mechanism"], world_index=spec["world_index"], fit_stage="synthetic", neural=family == "mlp32"))
    rows.extend(dict(packet="GATES", mode="synthetic", family="logistic", fit_stage="test", neural=False) for _ in range(300))
    catalog = pd.DataFrame(rows)
    catalog["fit_index"] = np.arange(len(catalog))
    directory = tmp_path / "private/auditory_next_v2/plan"
    directory.mkdir(parents=True)
    source = directory / "TASK_PLAN.csv"
    catalog.to_csv(source, index=False)
    plan = dict(task_csv=str(source), task_csv_hash=digest(source), contract_run="gate")
    (directory / "plan.json").write_text(json.dumps(plan))
    (directory / "completion.json").write_text(json.dumps(dict(status="PASS")))
    gate = directory.parent / "gate"
    gate.mkdir()
    (gate / "completion.json").write_text(json.dumps(dict(status="PASS")))
    own = execution._source_plan(plan, {})
    assert len(own) == 1920
    bindings = execution._bind_tasks(execution.planned_worlds(), own)
    assert len(bindings) == 1920 and len(set(bindings.values())) == 1920


def test_smoke_generates_inputs_only_without_fit_or_transforms(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("smoke cannot fit")
    monkeypatch.setattr(execution, "fit_cases", forbidden)
    monkeypatch.setattr(execution, "audit_residual_world", forbidden)
    monkeypatch.setattr(execution, "build_views", forbidden)
    metadata = execution._smoke(execution.planned_worlds())
    assert len(metadata) == 17  # A2 3 + N1 4 + N2 3 + N3 3 + G0 4.
    assert all(row["train_candidates"] + row["test_candidates"] == 60 for row in metadata)


def test_a2_support_counts_and_noise_are_frozen_from_quota_not_effects():
    groups = [f"synthetic_{i}" for i in range(49)]
    folds = dict(folds=[dict(outer_fold=i, test_groups=groups[i::5],
        train_groups=[g for g in groups if g not in groups[i::5]]) for i in range(5)])
    overlap = dict(omega=["run3_5_pos0", "run3_5_pos1"], groups=groups, trials_per_cell=6, repetitions=20,
        status="SUFFICIENT_FOR_SCREEN", cell_weights=[.5, .5], definition_hash="frozen_metadata",
        candidates=[dict(omega=["run3_5_pos0", "run3_5_pos1"], groups=groups, sufficient=True,
            fold_counts=[(i, 49-len(groups[i::5]), len(groups[i::5])) for i in range(5)])])
    draw = dict(omega=overlap["omega"], groups=groups, cell_weights=[.5, .5], definition_hash="frozen_metadata", seed=20260917)
    designs = execution.a2_support_design(overlap, draw, folds)
    assert len(designs) == 5
    assert [d["test"] for d in designs] == [10, 10, 10, 10, 9]
    assert all(d["half_contrast_noise_sd"] == pytest.approx(np.sqrt(1 / 6)) for d in designs)
    assert all(d["repeat_noise_reduction"] is False for d in designs)
    for i in range(5):
        spec = dict(_spec("A2", "null", repeat=i), a2_design=designs[i])
        world = execution.make_world(spec)
        assert len(world["train"]["candidate_ids"]) == designs[i]["train"]
        assert len(world["test"]["candidate_ids"]) == designs[i]["test"]
    altered = deepcopy(draw)
    altered["cell_weights"] = [.25, .75]
    with pytest.raises(ValueError, match="FROZEN_TWO_CELL_QUOTA"):
        execution.a2_support_design(overlap, altered, folds)
    leaked = deepcopy(folds)
    leaked["folds"][0]["train_groups"].append(leaked["folds"][0]["test_groups"][0])
    with pytest.raises(ValueError, match="FOLD_SUPPORT"):
        execution.a2_support_design(overlap, draw, leaked)


def test_shared_world_conditions_are_reported_separately_not_extra_draws():
    rows = []
    for condition in ("zero__delta", "fixed__delta", "fitted__delta"):
        rows.extend(dict(world_id=f"same_{i}", packet="A2", mechanism="null", family=condition,
            status="EVALUATED", screen=False, expected_positive=False) for i in range(100))
    rates = execution.aggregate_rates(rows)
    assert len(rates) == 3
    assert all(r["n_planned"] == 100 and r["n_positive"] == 0 and r["shared_draw_conditions"] for r in rates)
