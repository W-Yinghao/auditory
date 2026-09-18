import numpy as np
import pandas as pd
from pathlib import Path

from auditory_repair.legacy_d import MODE_DIR, clinical_features, load_corrected_table, model_list


def test_missing_pta_uses_training_median_and_indicator():
    frame = pd.DataFrame(
        {"target": [1, 2, 3], "age": [10, 11, 12], "log_duration": [0, 1, 2], "pta": [20.0, np.nan, 40.0]},
        index=["a", "b", "c"],
    )
    train, test, meta = clinical_features(frame, ["a", "b"], ["c"])
    assert meta["pta_train_median"] == 20.0
    assert train.shape == (2, 4)
    assert train[1, 2] == 20.0 and train[1, 3] == 1.0
    assert test[0, 2] == 40.0 and test[0, 3] == 0.0


def test_model_matrix_is_frozen():
    models = model_list()
    assert models[:7] == ["D0_mean", "D1_C", "D2_CV", "D3_CVN", "D4_CN", "D5_CFULL", "D7_CPRE"]
    assert models[7:] == [f"D6_CRANDOM_{k}" for k in range(20)]
    assert len(models) == 27


def test_route_directory_names_and_exact_subset(tmp_path):
    assert MODE_DIR == {"L0": "D_L0_core_001", "R_SUP": "D_SUP_core_001", "R_SIM": "D_SIM_core_001"}
    old = pd.DataFrame(
        {"candidate_id": ["c1", "c2", "c3"], "MUSS_source_percentage": [10, 20, 30], "age_months": [1, 2, 3], "log1p_device_duration_months": [0, 1, 2]},
        index=pd.Index(["g1", "g2", "g3"], name="split_group_id"),
    )
    corrected = pd.DataFrame(
        {"candidate_id": ["c1", "c2", "unmapped"], "MUSS_source_percentage": [10, 20, 99], "age_months": [1, 2, 9], "log1p_device_duration_months": [0, 1, 9], "better_ear_4freq_source_units": [5, 6, 9]}
    )
    path = tmp_path / "legacy_d_unknown_mapping.csv"
    corrected.to_csv(path, index=False)
    out, meta = load_corrected_table(Path(path), old, {"g1", "g2"})
    assert set(out.index) == {"g1", "g2"}
    assert meta["covered_old_groups"] == 2
