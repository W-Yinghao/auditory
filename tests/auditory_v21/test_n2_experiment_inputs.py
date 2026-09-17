import pandas as pd

from auditory_v21.n2_experiment_inputs import (
    H_BAG_COLUMNS,
    ROLE_MIN_GROUPS,
    build_fold_support_manifest,
    eligible_two_half_candidates,
    validate_h_bag_metadata,
)


def _roles():
    return {
        "A": [f"A{i}" for i in range(12)],
        "B": [f"B{i}" for i in range(3)],
        "C": [f"C{i}" for i in range(4)],
        "D": [f"D{i}" for i in range(4)],
        "E": [f"E{i}" for i in range(3)],
    }


def _bags():
    rows = []
    trial = 0
    for group in sum(_roles().values(), []):
        for half in (0, 1):
            pair_id = f"pair_{trial}"
            for label in (0, 1):
                bag_id = f"bag_{trial}_{label}"
                for member in range(8):
                    rows.append({
                        "bag_id": bag_id, "matched_pair_id": pair_id,
                        "trial_id": f"trial_{trial}_{member}", "candidate_id": "candidate0",
                        "record_id": "record0", "segment_id": "segment0",
                        "split_group_id": group, "stimulus_local_id": label,
                        "A_half": half, "A_block_id": member // 4,
                        "physical_block_id": f"block{member // 4}", "k": 8,
                    })
                trial += 1
    for label in (0, 1):
        for member in range(8):
            rows.append({
                "bag_id": f"unsupported_{label}", "matched_pair_id": "unsupported",
                "trial_id": f"unsupported_trial_{label}_{member}", "candidate_id": "candidate1",
                "record_id": "record0", "segment_id": "segment0",
                "split_group_id": "A0", "stimulus_local_id": label, "A_half": 0,
                "A_block_id": member // 4, "physical_block_id": f"block{member // 4}", "k": 8,
            })
    return pd.DataFrame(rows)


def _cases():
    roles = _roles()
    hashes = {
        "features.npz": {"exists": True, "hash_match": True, "sha256": "a"},
        "feature_rows.parquet": {"exists": True, "hash_match": True, "sha256": "b"},
    }
    return [{
        "case": f"N1_R_SIM_outer{fold}", "packet": "N1", "mode": "R_SIM",
        "outer_fold": fold, "status": "PASS", "roles": roles,
        "encoder_receipt": {
            "encoder_fit_groups": roles["A"],
            "scaler_train_groups": roles["A"],
        }, "feature_file_hashes": hashes,
        "dimensions": {"P_header": 64, "B_header": 64},
    } for fold in range(5)]


def test_two_half_filter_keeps_unsupported_candidates_out_of_scope():
    eligible, detail = eligible_two_half_candidates(_bags())
    assert eligible == {"candidate0"}
    assert detail["candidate_both_half_numerator"] == 1
    assert detail["candidate_unsupported"] == ["candidate1"]


def test_h_bag_contract_is_exactly_sixteen_numeric_columns():
    frame = pd.DataFrame({column: [float(index)] for index, column in enumerate(H_BAG_COLUMNS)})
    result = validate_h_bag_metadata(frame)
    assert result["column_count"] == 16
    assert result["columns"] == list(H_BAG_COLUMNS)


def test_all_five_fold_role_support_is_required_and_records_members():
    roles = _roles()
    all_groups = sum(roles.values(), [])
    folds = [{"outer_fold": fold, "train_groups": all_groups[:], "test_groups": []}
             for fold in range(5)]
    result = build_fold_support_manifest(_bags(), _cases(), folds)
    assert result["status"] == "PASS"
    assert len(result["folds"]) == 5
    assert all(row["status"] == "PASS" for row in result["folds"])
    assert result["passing_fold_subset_selection"] is False
    assert len(result["members"]) == 5 * len(all_groups) * 2 * 2 * 8
    assert {row["role"] for row in result["role_counts"]} == set(ROLE_MIN_GROUPS)
