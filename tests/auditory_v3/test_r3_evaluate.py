import copy

import numpy as np
import pandas as pd
import pytest

import auditory_v3.evaluate as module
from auditory_v3.linear import LogisticFit


def _fixture():
    rows = []
    for group in range(30):
        for half in (0, 1):
            for label in (0, 1):
                rows.append({"trial_id": f"t{len(rows)}", "split_group_id": f"g{group:02}",
                    "A_half": half, "previous_code": "1", "previous_run_bin": "run_1",
                    "stimulus_local_id": label, "outer_fold": group % 5,
                    "previous_gap_s": 1.0 + group * .01, "position_fraction": half * .5})
    frame = pd.DataFrame(rows)
    folds = []
    groups = sorted(frame.split_group_id.unique())
    for fold in range(5):
        test = sorted(frame.loc[frame.outer_fold == fold, "split_group_id"].unique())
        train = sorted(set(groups) - set(test))
        folds.append({"outer_fold": fold, "train_groups": train, "test_groups": test,
                      "R3_fit_groups": train[5:], "R3_validation_groups": train[:5]})
    return frame, {"folds": folds}


def _fake_fit(X, y, weights, lambda_l2, **kwargs):
    X, y = np.asarray(X), np.asarray(y)
    w = np.asarray(weights) / np.sum(weights)
    coef = (X.T @ (w * (y - .5))) / (1 + lambda_l2)
    diagnostics = {"success": True, "status": "PASS", "attempt_count": 1,
                   "lambda_l2": lambda_l2, "final_objective": .5,
                   "initial_objective": .693, "gradient_inf": 0., "finite": True}
    return LogisticFit(coef, 0., diagnostics)


def _features(frame, *, constant=False):
    rng = np.random.default_rng(65001)
    values = {}
    for objective in (*module.OBJECTIVES, "L0", "RAND"):
        for fold in range(5):
            for stage in ("selection", "final"):
                for window in ("post", "pre"):
                    dimension = 400 if objective == "L0" else 64
                    array = np.ones((len(frame), dimension)) if constant else rng.normal(size=(len(frame), dimension))
                    values[(objective, fold, stage, window)] = array
    return values


def test_selection_excludes_test_features_labels_and_uses_complete_catalog(monkeypatch):
    monkeypatch.setattr(module, "fit_logistic", _fake_fit)
    frame, splits = _fixture()
    features = _features(frame)
    calls = []

    def loader(objective, fold, stage, window, indices):
        assert stage == "selection"
        assert not (frame.iloc[indices].outer_fold == fold).any()
        calls.append((objective, fold, stage, window, indices.copy()))
        return features[(objective, fold, stage, window)][indices]

    first = module.select_probes(frame, loader, splits)
    assert first["selection_receipt"]["status"] == "PASS"
    assert len(first["fit_diagnostics"]) == 180
    assert len(first["selection_receipt"]["selections"]) == 60
    assert first["selection_receipt"]["outer_test_scored"] is False
    expected_dimensions = {"Htrial": 13, "L0_post": 400, "RAND_post": 64}
    for item in first["selection_receipt"]["selections"]:
        expected = expected_dimensions.get(item["probe"], 64 if item["probe"].endswith("__Zpost") else 77)
        assert item["feature_dimension"] == expected
    changed = frame.copy()
    test = np.flatnonzero(frame.outer_fold.to_numpy() == 0)
    changed.loc[test, "stimulus_local_id"] = 1 - changed.loc[test, "stimulus_local_id"]
    for (objective, fold, stage, window), array in features.items():
        if fold == 0:
            array[test] = 1e8
    second = module.select_probes(changed, loader, splits)
    left = [s for s in first["selection_receipt"]["selections"] if s["outer_fold"] == 0]
    right = [s for s in second["selection_receipt"]["selections"] if s["outer_fold"] == 0]
    assert left == right
    for key in first["models"]:
        if key.startswith("fold0__"):
            np.testing.assert_array_equal(first["models"][key]["model"].coef_, second["models"][key]["model"].coef_)
            np.testing.assert_array_equal(first["models"][key]["scaler"].mean_, second["models"][key]["scaler"].mean_)


def test_ties_choose_stronger_lambda_and_incomplete_grid_is_not_selected():
    assert module._choose_lambda({.001: .5, .01: .5, .1: .5}) == .1
    assert module._choose_lambda({.001: .5, .01: None, .1: .5}) is None
    assert module._choose_lambda({.001: .5, .1: .5}) is None


def test_complete_selection_receipt_required_before_final_feature_loading(monkeypatch):
    monkeypatch.setattr(module, "fit_logistic", _fake_fit)
    frame, splits = _fixture()
    features = _features(frame)
    loader = lambda objective, fold, stage, window, indices: features[(objective, fold, stage, window)][indices]
    selection = module.select_probes(frame, loader, splits)["selection_receipt"]
    selection = copy.deepcopy(selection)
    selection["selections"].pop()
    calls = []
    with pytest.raises(RuntimeError, match="complete R3 selection"):
        module.evaluate_representations(frame, lambda *args: calls.append(args), splits, selection)
    assert calls == []


def test_failed_final_fold_withholds_whole_model_metric_not_success_only_average(monkeypatch):
    monkeypatch.setattr(module, "fit_logistic", _fake_fit)
    frame, splits = _fixture()
    features = _features(frame)
    stages = []

    def loader(objective, fold, stage, window, indices):
        stages.append(stage)
        return features[(objective, fold, stage, window)][indices]

    selection = module.select_probes(frame, loader, splits)["selection_receipt"]

    def failing_fit(X, y, weights, lambda_l2, **kwargs):
        model = _fake_fit(X, y, weights, lambda_l2, **kwargs)
        context = kwargs["context"]
        if context["outer_fold"] == 0 and context["probe"] == "MATCH__Htrial_Zpost":
            model.diagnostics.update(success=False, status="NUMERICAL_FAIL")
        return model

    monkeypatch.setattr(module, "fit_logistic", failing_fit)
    stages.clear()
    result = module.evaluate_representations(frame, loader, splits, selection)
    assert set(stages) == {"final"}
    assert len(result["fit_diagnostics"]) == len(result["models"]) == 60
    assert result["summary"]["total_planned_probe_heads"] == 240
    assert result["summary"]["metrics"]["MATCH__Htrial_Zpost"]["ce_bits"] is None
    assert result["summary"]["contrasts"]["SUP_minus_MATCH__Htrial_Zpost"]["gain_bits"] is None
    assert result["summary"]["research"] == "NUMERICAL_FAIL"
    assert result["predictions"].loc[frame.outer_fold == 0, "MATCH__Htrial_Zpost"].isna().all()
    assert result["predictions"].loc[frame.outer_fold != 0, "MATCH__Htrial_Zpost"].notna().all()


def test_constant_encoder_is_retained_as_a_scientific_result(monkeypatch):
    monkeypatch.setattr(module, "fit_logistic", _fake_fit)
    frame, splits = _fixture()
    features = _features(frame, constant=True)
    loader = lambda objective, fold, stage, window, indices: features[(objective, fold, stage, window)][indices]
    selection = module.select_probes(frame, loader, splits)["selection_receipt"]
    result = module.evaluate_representations(frame, loader, splits, selection)
    assert result["summary"]["execution"] == "COMPLETE"
    assert result["summary"]["research"] == "NO_ADDED_VALUE_OVER_SUPERVISION"
    assert all(r["numerical_rank"] == 0 for r in result["summary"]["rank_diagnostics"])
    assert result["summary"]["metrics"]["SUP__Zpost"]["ce_bits"] == pytest.approx(1.,abs=1e-14)
    assert len(result["models"]) == 60


def test_secondary_grid_failure_preserves_complete_primary_matrix(monkeypatch):
    frame, splits = _fixture()
    features = _features(frame, constant=True)
    loader = lambda objective, fold, stage, window, indices: features[(objective, fold, stage, window)][indices]

    def fail_secondary(X, y, weights, lambda_l2, **kwargs):
        model = _fake_fit(X, y, weights, lambda_l2, **kwargs)
        context = kwargs["context"]
        if (context["stage"] == "selection" and context["outer_fold"] == 0
                and context["probe"] == "SIM__Zpost" and lambda_l2 == .01):
            model.diagnostics.update(success=False, status="NUMERICAL_FAIL")
        return model

    monkeypatch.setattr(module, "fit_logistic", fail_secondary)
    selection = module.select_probes(frame, loader, splits)["selection_receipt"]
    assert selection["status"] == "COMPLETED_WITH_NUMERICAL_FAILURES"
    assert selection["selection_complete"] is True
    result = module.evaluate_representations(frame, loader, splits, selection)
    assert result["summary"]["primary_status"] == "PASS"
    assert result["summary"]["research"] == "NO_ADDED_VALUE_OVER_SUPERVISION"
    assert result["summary"]["final_heads"] == 59
    assert result["summary"]["incomplete_models"] == ["SIM__Zpost"]
    assert result["summary"]["metrics"]["SIM__Zpost"]["ce_bits"] is None
