"""Pure receipt enrichment fixtures; execution belongs to the Slurm gate."""

import json

from auditory_next.fit_accounting import MANDATORY_RECEIPT_FIELDS
from auditory_next.receipt_enrichment import enrich_unit


def test_all_required_fields_are_explicitly_unknown_without_receipts():
    row = enrich_unit({})
    assert set(MANDATORY_RECEIPT_FIELDS) <= set(row)
    assert all(row["field_origin"][field] == "unknown" for field in MANDATORY_RECEIPT_FIELDS)


def test_scope_observations_and_model_digest_use_declared_aliases(tmp_path):
    receipt = tmp_path / "start.json"
    receipt.write_text(json.dumps({"fit_id": "f1", "scope_hash": "s", "feature_hash": "x",
                                   "scope": {"fit_groups": ["G1", "G1", "G2"]},
                                   "n_training_observations": 12, "objective": "new_fixed_lambda_or_C",
                                   "iterations": 4}))
    row = enrich_unit({"fit_id": "f1", "receipt_files": [str(receipt)],
                       "model_file_digests": [{"sha256": "abc"}]})
    assert row["training_scope_hash"] == "s"
    assert row["n_train_candidates"] == 2
    assert row["n_train_trials_or_bags"] == 12
    assert row["model_hash"] == "abc"
    assert row["objective_kind"] == "penalized_objective"
    assert row["field_origin"]["model_hash"] == "derived:model_file_digest"


def test_terminal_optimization_and_last_gradient_are_used(tmp_path):
    folder = tmp_path / "fit"
    folder.mkdir()
    start = folder / "start.json"
    start.write_text(json.dumps({"fit_id": "f2", "optimization": {"steps": 1000}}))
    (folder / "training_curve.json").write_text(json.dumps([{"loss": 2}, {"loss": 1, "gradient_norm_unclipped": 0.25}]))
    completion = folder / "completion.json"
    completion.write_text(json.dumps({"optimizer_status": "OPTIMIZATION_STABLE"}))
    row = enrich_unit({"receipt_files": [str(start), str(completion)]})
    assert row["step_count"] == 1000
    assert row["final_train_loss"] is None
    assert row["last_observed_objective"] == 1
    assert row["gradient_diagnostic"]["timing"] == "before_update"


def test_config_code_are_inherited_and_unresolved_fields_stay_unknown(tmp_path):
    receipt = tmp_path / "completion.json"
    receipt.write_text(json.dumps({"fit_id": "f3", "label_hash": "array-not-map"}))
    row = enrich_unit({"receipt_files": [str(receipt)]}, {"config_hash": "c", "code_hash": "h"})
    assert row["config_hash"] == "c" and row["code_hash"] == "h"
    assert row["field_origin"]["config_hash"] == "inherited:run_config"
    assert row["feature_scope_hash"] is None and row["label_map_hash"] is None
