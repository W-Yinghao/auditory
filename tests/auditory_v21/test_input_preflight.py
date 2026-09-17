import json
from pathlib import Path

import pytest

from auditory_v21.input_preflight import (RAW_H_COLUMNS, _l0_source_receipt,
                                          _npz_headers, _selected_history_columns,
                                          _sha256, split_role_groups)


def test_raw_history_schema_is_fixed_and_past_only():
    assert len(RAW_H_COLUMNS) == 25
    assert all("clinical" not in name and "muss" not in name and "age" not in name for name in RAW_H_COLUMNS)
    assert "current_run_length" not in RAW_H_COLUMNS


def test_history_selector_drops_layout_id_from_25_numeric_columns():
    pd = pytest.importorskip("pandas")
    frame = pd.DataFrame({column: [1.0, 2.0] for column in RAW_H_COLUMNS})
    frame["layout_id"] = ["HA20", "HA20"]

    class Selector:
        @staticmethod
        def history_feature_columns(_frame):
            return list(RAW_H_COLUMNS) + ["layout_id"]

    assert _selected_history_columns(Selector, frame) == RAW_H_COLUMNS


def test_split_roles_is_deterministic_and_exhaustive():
    train = [f"G{i:02d}" for i in range(48)]
    validation = train[34:]
    test = [f"G{i:02d}" for i in range(48, 60)]
    first = split_role_groups(train, validation, test)
    second = split_role_groups(train, validation, test)
    assert first == second
    assert set().union(*map(set, first.values())) == set(train + test)
    assert sum(len(v) for v in first.values()) == 60
    assert {k: len(v) for k, v in first.items()} == {"A": 34, "B": 3, "C": 5, "D": 6, "E": 12}


def test_split_roles_rejects_underpowered_pool():
    with pytest.raises(ValueError, match="ROLE_SUPPORT_LIMITED"):
        split_role_groups(["A"] * 0 + [f"G{i}" for i in range(16)], [f"G{i}" for i in range(2)], [f"T{i}" for i in range(3)])


def test_npz_headers_do_not_require_loading_arrays(tmp_path: Path):
    np = pytest.importorskip("numpy")
    path = tmp_path / "features.npz"
    np.savez(path, post=np.zeros((3, 64)), pre=np.zeros((3, 64)), y=np.zeros(3))
    assert _npz_headers(path)["post"] == [3, 64]
    assert _npz_headers(path)["pre"] == [3, 64]


def test_l0_scope_is_stateless_and_keeps_probe_fit_groups(tmp_path: Path):
    snapshot = tmp_path / "snapshot"
    source = {
        "auditory5/execution.py": (
            "encoder=None\n"
            "z=bin_20ms(view.X) if encoder is None else encoder.transform(view.X)\n"
            "if encoder is not None:encoder.save\n"
        ),
        "auditory5/probes.py": (
            "def bin_20ms\nprocessed_fs != 250.0\n"
            "reshape(x.shape[0], x.shape[1], x.shape[2] // 5, 5)\n.mean(axis=-1)\n"
        ),
        "auditory5/datasets.py": "def load_dataset\nnp.load(dest/(branch+'.npy'\n",
    }
    plan_hashes = {}
    s0_hashes = {}
    for relative, text in source.items():
        path = snapshot / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        plan_hashes[relative] = _sha256(path)
        original = tmp_path / relative
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_text(text)
        s0_hashes[str(original)] = _sha256(original)
    artifacts = {
        "encoder.pt": {"exists": False},
        "features.npz": {"exists": True, "hash_match": True, "sha256": "feature"},
        "feature_rows.parquet": {"exists": True, "hash_match": True, "sha256": "rows"},
    }
    scope = {"completion_status": "PASS", "plan_hash_match": True,
             "task_fit_groups": ["probe-A"], "task_validation_groups": [],
             "task_test_groups": [], "completion_scope_hash": "probe-scope"}
    receipt = _l0_source_receipt(
        tmp_path, {"source_snapshot": str(snapshot), "code_hashes": plan_hashes},
        "plan", artifacts, s0_hashes, scope)
    assert receipt["status"] == "PASS"
    assert receipt["feature_generation_kind"] == "STATELESS_FIXED_BINNING"
    assert receipt["stateless_source_verified"] is True
    assert receipt["actual_encoder_fit_groups"] == []
    assert receipt["actual_scaler_fit_groups"] == []
    assert receipt["old_probe_fit_groups"] == ["probe-A"]
    assert receipt["completion_proof_no_encoder"] is True
