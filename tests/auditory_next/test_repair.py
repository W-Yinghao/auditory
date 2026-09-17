"""Synthetic scope and packet-barrier tests; execute only in Slurm gates."""
import pickle
import numpy as np
import pandas as pd
import pytest

from auditory5.contracts import FitScope
from auditory_next import repair


def test_complete_budget_counts_all_unselected_final_alpha_models():
    assert repair.fit_counts("C2_R") == {"neural": 560, "linear": 325}
    assert repair.fit_counts("E0_R") == {"neural": 1024, "linear": 0}
    cases = [{"key": "outer0", "specs": repair.old_c.MODEL_SPECS}]
    members = repair.neural_members(cases)
    assert len(members) == 7 * 16
    assert sum(m["part"] == "final" for m in members) == 7 * 4
    for family, view, width in repair.old_c.MODEL_SPECS:
        if width:
            own = [m for m in members if m["family"] == family and m["view"] == view]
            assert len(own) == 16
            for part in ("inner0", "inner1", "inner2", "final"):
                assert {m["alpha"] for m in own if m["part"] == part} == set(repair.C_GRID)


@pytest.mark.parametrize("unstable", [False, True])
def test_global_barrier_finishes_every_initial_member_before_extending_any(tmp_path, monkeypatch, unstable):
    calls = []
    members = [{"key": "A"}, {"key": "B"}, {"key": "C"}]

    def fake(case_root, states, member, steps, *, device):
        calls.append((member["key"], steps))
        bad = unstable and member["key"] == "C" and steps == 1000
        return dict(member, steps=steps, status="OPTIMIZATION_UNRESOLVED" if bad else "OPTIMIZATION_STABLE")

    monkeypatch.setattr(repair, "_member_pass", fake)
    outcome = repair.fit_neural_family(tmp_path / "cases", tmp_path / "states", members)
    assert calls[:3] == [("A", 1000), ("B", 1000), ("C", 1000)]
    assert calls[3:] == ([("A", 2000), ("B", 2000), ("C", 2000)] if unstable else [])
    assert outcome["status"] == "OPTIMIZATION_STABLE"
    assert outcome["budget"] == (2000 if unstable else 1000)
    assert outcome["neural_fits"] == 3 and outcome["continuation_fits"] == 0


def test_unstable_final_alpha_blocks_selection_without_accessing_validation_or_test(tmp_path, monkeypatch):
    members = [{"key": "unused_final_alpha"}, {"key": "other"}]

    def fake(case_root, states, member, steps, *, device):
        return dict(member, steps=steps, status="OPTIMIZATION_UNRESOLVED" if member["key"].startswith("unused") else "OPTIMIZATION_STABLE")

    def forbidden(*args, **kwargs):
        pytest.fail("no predictions or input reads before the complete-family gate")

    monkeypatch.setattr(repair, "_member_pass", fake)
    monkeypatch.setattr(repair, "_scores", forbidden)
    monkeypatch.setattr(repair, "_partition", forbidden)
    outcome = repair.fit_neural_family(tmp_path / "cases", tmp_path / "states", members)
    assert outcome["status"] == "INCOMPLETE_PRIMARY_MATRIX" and outcome["budget"] == 2000
    with pytest.raises(ValueError, match="INCOMPLETE_PRIMARY_MATRIX"):
        repair.select_neural_models(tmp_path / "cases", tmp_path / "states", [], members, outcome)


def test_alpha_grid_cannot_drop_a_failure_and_ties_use_strongest_regularization():
    y = np.tile([0, 1], 6)
    groups = np.repeat(["a", "b", "c"], 4)
    oof = {a: np.zeros((12, 2)) for a in repair.C_GRID}
    chosen, losses = repair.select_alpha(oof, y, groups)
    assert chosen == 10 and all(v == pytest.approx(1) for v in losses.values())
    del oof[.01]
    with pytest.raises(ValueError, match="ALPHA_GRID_INCOMPLETE"):
        repair.select_alpha(oof, y, groups)
    oof[.01] = np.full((12, 2), np.nan)
    with pytest.raises(ValueError):
        repair.select_alpha(oof, y, groups)


def test_nonfinite_attempt_is_not_reported_as_completed_steps():
    failed = dict(status="OPTIMIZATION_UNRESOLVED", steps=0, attempted_budget=1000)
    assert repair.family_budget([failed]) == 2000
    with pytest.raises(ValueError, match="INCOMPLETE_PRIMARY_MATRIX"):
        repair.require_complete_family([dict(failed, attempted_budget=2000)], 1, 2000)


def _data():
    rng = np.random.default_rng(4)
    groups = np.repeat([f"group{k}" for k in range(8)], 8)
    y = np.tile([0, 1], 32)
    rows = pd.DataFrame(dict(trial_id=[f"t{k}" for k in range(64)],
                            split_group_id=groups, filter_block_id=groups, stimulus_local_id=y))
    train, test = np.arange(48), np.arange(48, 64)
    scope = FitScope(tuple(np.unique(groups[train])), test_groups=tuple(np.unique(groups[test])))
    return rng.normal(size=(64, 48)), rng.normal(size=(64, 48)), rows, train, test, scope


@pytest.mark.parametrize("kind", ["C2_R", "E0_R"])
def test_outer_features_labels_cannot_change_any_training_transform(tmp_path, kind):
    left, right, rows, train, test, scope = _data()
    other = left.copy()
    other[test] *= 1000
    changed = rows.copy()
    changed.loc[test, "stimulus_local_id"] = 1 - changed.loc[test, "stimulus_local_id"]
    repair.prepare_case(tmp_path / "first", left, right if kind == "C2_R" else None,
                        rows, train, test, scope, kind=kind, metadata={})
    repair.prepare_case(tmp_path / "second", other, right if kind == "C2_R" else None,
                        changed, train, test, scope, kind=kind, metadata={})
    for part in ("inner0", "inner1", "inner2", "final"):
        with (tmp_path / "first" / part / "transform.pkl").open("rb") as stream:
            a = pickle.load(stream)
        with (tmp_path / "second" / part / "transform.pkl").open("rb") as stream:
            b = pickle.load(stream)
        assert a["scope"].hash == b["scope"].hash
        for x, z in zip(a["scalers"], b["scalers"]):
            np.testing.assert_array_equal(x.mean_, z.mean_)
            np.testing.assert_array_equal(x.scale_, z.scale_)
            assert set(x.fit_groups_) <= set(scope.train_groups)
        if kind == "E0_R":
            np.testing.assert_array_equal(a["pca"].components_, b["pca"].components_)
            assert a["pca"].n_components_ <= 32
        else:
            assert a["pca"] is None


def test_prepared_train_mutation_is_rejected_before_fitting(tmp_path):
    left, right, rows, train, test, scope = _data()
    case = repair.prepare_case(tmp_path / "case", left, right, rows, train, test, scope,
                               kind="C2_R", metadata={})
    member = repair.neural_members([case])[0]
    x, y, weights, receipt = repair._partition(tmp_path, member)
    assert x.shape[0] == len(y) and weights.sum() == pytest.approx(len(np.unique(receipt["scope"]["train_groups"])))
    with (tmp_path / "case" / member["part"] / "train.npz").open("ab") as stream:
        stream.write(b"mutation")
    with pytest.raises(ValueError, match="PREPARED_INPUT_MUTATION"):
        repair._partition(tmp_path, member)


def test_frozen_inner_assignments_override_runtime_groupkfold(tmp_path,monkeypatch):
    left,right,rows,train,test,scope=_data()
    definitions=[]
    for i in range(3):
        va=tuple(scope.train_groups[i*2:(i+1)*2]);tr=tuple(g for g in scope.train_groups if g not in va)
        inner=FitScope(tr,va,scope.test_groups)
        definitions.append(dict(fit_groups=tr,validation_groups=va,scope_hash=inner.hash))
    def forbidden(*args,**kwargs):raise AssertionError('must not recreate legacy folds')
    monkeypatch.setattr(repair,'GroupKFold',forbidden)
    repair.prepare_case(tmp_path/'frozen',left,right,rows,train,test,scope,kind='C2_R',metadata={},inner_definitions=definitions)
    for i,definition in enumerate(definitions):
        with (tmp_path/'frozen'/f'inner{i}'/'transform.pkl').open('rb') as f:transform=pickle.load(f)
        assert transform['scope'].hash==definition['scope_hash']
