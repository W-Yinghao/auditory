import copy

import numpy as np
import pandas as pd
import pytest
import torch

import auditory_v3.r3_execution as module
from auditory5.models.small_cnn import SmallEEGCNN_v1


def _loader_inputs():
    rows = [dict(split_group_id=f"g{g:02}", A_half=half, previous_code="1",
                 previous_run_bin="run_1", stimulus_local_id=label)
            for g in range(30) for half in (0, 1) for label in (0, 1)]
    members = pd.DataFrame(rows)
    groups = sorted(members.split_group_id.unique())
    folds, states = [], {}
    rng = np.random.default_rng(67001)
    post = rng.normal(size=(len(members), 20, 100)).astype("float32")
    pre = rng.normal(size=(len(members), 20, 50)).astype("float32")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(11)
        initial = SmallEEGCNN_v1(20, 2)
    initial_hash = module._state_hash(initial)
    for fold in range(5):
        test = [g for i, g in enumerate(groups) if i % 5 == fold]
        train = sorted(set(groups) - set(test))
        fit, validation = train[5:], train[:5]
        folds.append(dict(outer_fold=fold, train_groups=train, test_groups=test,
                          R3_fit_groups=fit, R3_validation_groups=validation))
        fit_indices = np.flatnonzero(members.split_group_id.isin(fit))
        mean, scale = module.channel_scaler(post, members, fit_indices)
        for objective in module.OBJECTIVES:
            states[(objective, fold)] = {"model": initial.state_dict(), "scaler_mean": mean,
                "scaler_std": scale, "fit_groups": fit, "initial_encoder_sha256": initial_hash}
    return members, post, pre, {"folds": folds}, states


def test_selection_loader_infers_requested_rows_only_and_accepts_pre_length(monkeypatch):
    members, post, pre, splits, states = _loader_inputs()
    seen = []

    def infer(state, raw, **kwargs):
        seen.append(raw.copy())
        return np.ones((len(raw), 64))

    monkeypatch.setattr(module, "infer_features", infer)
    loader = module.checkpoint_feature_loader(members, post, pre, splits, states, "selection")
    fit = np.flatnonzero(members.split_group_id.isin(splits["folds"][0]["R3_fit_groups"]))[:3]
    validation = np.flatnonzero(members.split_group_id.isin(splits["folds"][0]["R3_validation_groups"]))[:2]
    test = np.flatnonzero(members.split_group_id.isin(splits["folds"][0]["test_groups"]))[:2]
    assert loader("SUP", 0, "selection", "post", fit).shape == (3, 64)
    assert loader("MATCH", 0, "selection", "pre", validation).shape == (2, 64)
    np.testing.assert_array_equal(seen[0], post[fit])
    np.testing.assert_array_equal(seen[1], pre[validation])
    with pytest.raises(ValueError, match="outer-test"):
        loader("SUP", 0, "selection", "post", test)
    assert len(seen) == 2
    expected = post[fit].astype(float).reshape(3, 20, 20, 5).mean(-1).reshape(3, 400)
    np.testing.assert_array_equal(loader("L0", 0, "selection", "post", fit), expected)
    assert loader("RAND", 0, "selection", "post", fit).shape == (3, 64)


def test_saved_input_scaler_must_match_exact_encoder_fit_scope():
    members, post, pre, splits, states = _loader_inputs()
    states = copy.deepcopy(states)
    states[("MATCH", 0)]["scaler_mean"][0, 0] += 1
    with pytest.raises(ValueError, match="fit-only"):
        module.checkpoint_feature_loader(members, post, pre, splits, states, "selection")


def test_source_and_private_path_bindings_reject_changed_or_escaping_artifacts(tmp_path):
    source = {f"auditory_v3/{name}.py": "fixed" for name in module.PACKET_SOURCES["R3"]}
    source["auditory5/models/small_cnn.py"] = "fixed"
    reference = {"config_sha256": "config", "source_hashes": source}
    changed = copy.deepcopy(reference)
    changed["source_hashes"]["auditory_v3/train.py"] = "changed"
    with pytest.raises(ValueError, match="source mismatch"):
        module._check_sources(reference, changed)
    with pytest.raises(ValueError, match="escapes"):
        module._restricted_path(tmp_path / "outside.pt", tmp_path / "training")
