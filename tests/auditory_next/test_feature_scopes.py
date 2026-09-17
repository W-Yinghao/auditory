import numpy as np
import pytest

from auditory_next.features import (LegacyFeatureRegistry, audit_inner_scope,
                                    final_head_scope, validate_feature_alignment)


def _fixture():
    plan = {"tasks": [{"name": "outer0_all_R_SIM", "stage": "outer", "mode": "R_SIM",
                       "branch": "all", "outer_fold": 0, "inner_fold": None,
                       "fit_groups": ["a", "b"], "test_groups": ["c"]}]}
    scopes = [{"task": "outer0_all_R_SIM", "feature_scope_id": "scope-x",
               "fit_groups": ["a", "b"], "validation_groups": [], "test_groups": ["c"]}]
    return plan, scopes


def test_explicit_task_resolution_and_wrong_fold_rejection():
    reg = LegacyFeatureRegistry.from_dicts(*_fixture())
    assert reg.resolve_task(stage="outer", mode="R_SIM", branch="all", outer_fold=0)["name"] == "outer0_all_R_SIM"
    with pytest.raises(KeyError): reg.resolve_task(stage="outer", mode="R_SIM", branch="all", outer_fold=1)


def test_inner_scope_rejects_training_overlap_and_unrecorded_validation():
    scope = {"validation_groups": ["v"]}
    with pytest.raises(ValueError): audit_inner_scope(scope, ["x"], ["a"], ["a", "v", "x"])
    with pytest.raises(ValueError): audit_inner_scope(scope, ["v"], ["v", "a"], ["a", "v"])


def test_alignment_rejects_test_group_or_clinical_columns():
    rows = [{"trial_id": "t1", "split_group_id": "test", "stimulus_local_id": 0}]
    arr = {"trial_ids": ["t1"], "groups": ["test"], "labels": [0]}
    assert validate_feature_alignment(arr, rows)["n_rows"] == 1
    with pytest.raises(ValueError): validate_feature_alignment({"trial_ids": ["t1"], "groups": ["x"], "labels": [0]}, rows)
    with pytest.raises(ValueError): validate_feature_alignment({**arr, "clinical": np.array([1])}, [{**rows[0], "MUSS": 4}])


def test_final_head_scope_cannot_expand_to_unknown_groups():
    assert final_head_scope(["a", "b"], ["a"])["fit_groups"] == ["a"]
    with pytest.raises(ValueError): final_head_scope(["a", "b"], ["z"])
