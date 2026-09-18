import numpy as np
import pandas as pd

import auditory_v3.n2r_execution as module
from auditory_v3.bags_packet import H_COLUMNS, bag_history_array


def _packet(n_groups=31):
    rng = np.random.default_rng(66001)
    rows, history = [], []
    for group in range(n_groups):
        name = f"g{group:02}"
        for half in (0, 1):
            for repeat in range(1 + group % 2):
                for label in (0, 1):
                    bag = f"{name}_h{half}_r{repeat}_c{label}"
                    h = dict(zip(H_COLUMNS, rng.normal(size=16)))
                    history.append(dict(bag_id=bag, **h))
                    for member in range(8):
                        rows.append(dict(bag_id=bag, matched_pair_id=f"{name}_{half}_{repeat}",
                            trial_id=f"t{len(rows)}", candidate_id=name, split_group_id=name,
                            record_id=f"record_{group}", segment_id="segment", stimulus_local_id=label,
                            A_half=half, A_block_id=f"block{member // 4}", physical_block_id=f"block{member // 4}",
                            previous_code="1", previous_run_bin="run_1", k=8, outer_fold=group % 5))
    frame = pd.DataFrame(rows)
    post, pre = rng.normal(size=(len(frame), 400)), rng.normal(size=(len(frame), 200))
    folds = []
    population = sorted(frame.split_group_id.unique())
    for number in range(5):
        test = sorted(frame.loc[frame.outer_fold == number, "split_group_id"].unique())
        train = sorted(set(population) - set(test))
        blocks = np.array_split(train, 3)
        inner = [{"inner_fold": i, "validation_groups": block.tolist(),
                  "fit_groups": sorted(set(train) - set(block))} for i, block in enumerate(blocks)]
        folds.append(dict(outer_fold=number, train_groups=train, test_groups=test, inner_folds=inner))
    return frame, post, pre, pd.DataFrame(history), {"folds": folds}


class _FastPCA:
    """Runner-control test double; real PCA geometry is tested separately."""
    def fit(self, X, weights):
        self.mean_ = np.average(X, axis=0, weights=weights)
        self.rank_ = 8
        self.components_ = np.eye(X.shape[1])[:8]
        return self

    def transform(self, X, n_components=None):
        return (X - self.mean_)[:, :8]


class _ConstantFit:
    def __init__(self, risk, success=True):
        self.success = success
        self.probability = (1 - np.sqrt(max(0, 1 - 4 * 2. ** (-2 * risk)))) / 2
        self.diagnostics = dict(success=success, status="PASS" if success else "NUMERICAL_FAIL",
                                attempt_count=1, final_objective=.5)

    def predict_proba(self, X):
        return np.full(len(X), self.probability if self.success else np.nan)


def _risk_fit(X, y, weights, lambda_l2, *, ledger=None, context=None):
    inner = context.get("inner_fold", 0)
    if lambda_l2 == .001:
        risk = 2. if inner == 0 else 1.
    elif lambda_l2 == .01:
        risk = 1.34
    else:
        risk = 2.
    return _ConstantFit(risk)


def test_inner_selection_uses_all_identity_oof_weights_and_four_cached_contexts(monkeypatch):
    monkeypatch.setattr(module, "WeightedPCA", _FastPCA)
    monkeypatch.setattr(module, "fit_logistic", _risk_fit)
    data = _packet()
    result = module.run_packet(*data, view_names=("HQ", "HQV"), outer_folds=[1])
    # Fold1 has25 outer-train groups with9/8/8 inner validation groups. Lambda
    # .001 has mean-fold CE1.333..., but identity-weighted CE1.36; .01 wins1.34.
    assert result["selections"].selected_lambda.eq(.01).all()
    for risks in result["selections"].inner_oof_ce_bits:
        np.testing.assert_allclose(risks["0.001"], 1.36, atol=1e-13)
        np.testing.assert_allclose(risks["0.01"], 1.34, atol=1e-13)
    assert result["summary"]["planned_heads"] == result["summary"]["actual_heads"] == 20
    assert result["summary"]["transform_contexts"] == len(result["transforms"]) == 4
    assert set(result["predictions"].outer_fold) == {1}
    assert result["summary"]["n_groups"] == 6
    assert all(not (set(t.fit_groups) & set(t.evaluation_groups)) for t in result["transforms"].values())


def test_block_scaling_duplicate_geometry_and_ddof_log_order():
    frame, post, pre, history, _ = _packet(4)
    bags, bag_members = module._bag_index(frame)
    h = bag_history_array(frame, history)
    transform = module.fit_transform_context(frame, bags, bag_members, post, pre, h,
                                              ["g00", "g01"], ["g02"], module.ALL_VIEWS)
    views = transform.views
    expected = {"H": 16, "HM": 24, "HMV": 32, "HQ": 60, "HQV": 68,
                "HQQ": 104, "HPRE": 68, "HPREQ": 112, "HPREQV": 120,
                "FULL_MU": 400, "FULL_MU_VAR": 800}
    assert {key: value.shape[1] for key, value in views.items()} == expected
    np.testing.assert_allclose(views["HQQ"][:, 16:60], views["HQ"][:, 16:] / np.sqrt(2), atol=0, rtol=0)
    np.testing.assert_allclose(views["HQQ"][:, 60:], views["HQ"][:, 16:] / np.sqrt(2), atol=0, rtol=0)
    np.testing.assert_array_equal(views["HQQ"][:, :16], views["HQ"][:, :16])
    # Recover raw V with the saved block scaler and compare explicit unbiased
    # variance in the training-derived, unwhitened PCA coordinates.
    scaler, pca = transform.trial_scalers["post"], transform.pcas["post"]
    global_first_bag = transform.bag_indices[0]
    z = pca.transform(scaler.transform(post[bag_members[global_first_bag]]), n_components=8)
    expected_v = np.log1p(np.var(z, axis=0, ddof=1))
    v_scaler = transform.block_scalers["V"]
    actual_v = transform.blocks["V"][0] * v_scaler.scale_ + v_scaler.mean_
    np.testing.assert_allclose(actual_v, expected_v, atol=1e-12)


def test_inner_validation_and_outer_test_changes_cannot_change_fit_transforms():
    frame, post, pre, history, _ = _packet(4)
    bags, bag_members = module._bag_index(frame)
    h = bag_history_array(frame, history)
    first = module.fit_transform_context(frame, bags, bag_members, post, pre, h,
                                         ["g00", "g01"], ["g02"], module.ALL_VIEWS)
    changed = frame.copy()
    heldout = frame.split_group_id.isin(["g02", "g03"]).to_numpy()
    changed.loc[heldout, "stimulus_local_id"] = 1 - changed.loc[heldout, "stimulus_local_id"]
    changed_post, changed_pre = post.copy(), pre.copy()
    changed_post[heldout] += 1e6
    changed_pre[heldout] -= 1e6
    changed_bags, changed_index = module._bag_index(changed)
    second = module.fit_transform_context(changed, changed_bags, changed_index, changed_post, changed_pre, h,
                                          ["g00", "g01"], ["g02"], module.ALL_VIEWS)
    for kind in ("post", "pre"):
        np.testing.assert_array_equal(first.trial_scalers[kind].mean_, second.trial_scalers[kind].mean_)
        np.testing.assert_array_equal(first.pcas[kind].components_, second.pcas[kind].components_)
    for block in first.block_scalers:
        np.testing.assert_array_equal(first.block_scalers[block].mean_, second.block_scalers[block].mean_)
        np.testing.assert_array_equal(first.block_scalers[block].scale_, second.block_scalers[block].scale_)
    fit_local = first.fit_bag_indices
    for view in module.ALL_VIEWS:
        np.testing.assert_array_equal(first.views[view][fit_local], second.views[view][fit_local])


def test_failed_inner_fold_cannot_select_successful_fold_subset(monkeypatch):
    monkeypatch.setattr(module, "WeightedPCA", _FastPCA)

    def failed(X, y, weights, lambda_l2, *, ledger=None, context=None):
        model = _risk_fit(X, y, weights, lambda_l2, context=context)
        if context["stage"] == "inner" and context["view"] == "HQV" and context["inner_fold"] == 1 and lambda_l2 == .01:
            model.success = False
            model.diagnostics.update(success=False, status="NUMERICAL_FAIL")
        return model

    monkeypatch.setattr(module, "fit_logistic", failed)
    result = module.run_packet(*_packet(), view_names=("HQ", "HQV"), outer_folds=[1])
    assert len(result["fit_diagnostics"]) == 20
    assert result["summary"]["actual_heads"] == 19
    assert result["selections"].set_index("view").loc["HQV", "status"] == "INCOMPLETE_INNER_GRID"
    assert result["predictions"].HQV.isna().all()
    assert result["summary"]["contrasts"]["HQ_minus_HQV"]["gain_bits"] is None
    assert result["summary"]["primary_status"] == "NUMERICAL_FAIL"


def test_failed_independent_full_sensitivity_retains_primary(monkeypatch):
    monkeypatch.setattr(module, "WeightedPCA", _FastPCA)

    def failed(X, y, weights, lambda_l2, *, ledger=None, context=None):
        model = _risk_fit(X, y, weights, lambda_l2, context=context)
        if context["stage"] == "inner" and context["view"] == "FULL_MU" and context["inner_fold"] == 1 and lambda_l2 == .01:
            model.success = False
            model.diagnostics.update(success=False, status="NUMERICAL_FAIL")
        return model

    monkeypatch.setattr(module, "fit_logistic", failed)
    result = module.run_packet(*_packet(), view_names=("HQ", "HQV", "FULL_MU"), outer_folds=[1])
    assert result["summary"]["primary_status"] == "PASS"
    assert result["summary"]["actual_heads"] == 29
    assert result["summary"]["metrics"]["FULL_MU"]["ce_bits"] is None
    assert result["summary"]["contrasts"]["HQ_minus_HQV"]["gain_bits"] == 0
