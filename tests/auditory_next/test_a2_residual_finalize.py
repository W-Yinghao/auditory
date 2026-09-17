"""Saved-matrix recovery tests; never fit a predictor, PCA or encoder."""
from copy import deepcopy

import numpy as np
import pytest

from auditory5.routes.a_matching import bootstrap_match
from auditory_next.a2_residual_execution import decomposition_table
from auditory_next.a2_residual_finalize import (
    MODES, reconstruct_aggregates, validate_saved_details, validate_output_failure)


def _details(fold=0):
    rng = np.random.default_rng(31 + fold)
    delta = rng.normal(size=(4, 3, 2, 5))
    prediction = rng.normal(size=(4, 3, 2, 5)) * .2
    return decomposition_table(delta, prediction, tuple(f"synthetic_{fold}_{i}" for i in range(3)))


def _records():
    # Deliberately preserve a non-sorted source fold order for the RNG audit.
    return [dict(mode=mode, outer_fold=fold, details=_details(fold),
        quality_status="FEATURE_TASK_HAS_NO_FIXED_QUALITY_ARRAY",
        background_components=["post_common_response", "pre_common_response", "pre_delta"])
        for mode in MODES for fold in (3, 0, 4, 1, 2)]


def test_saved_details_revalidate_pair_identity_and_vector_statistics():
    details = _details()
    check = validate_saved_details(details, details["groups"])
    assert check["max_pair_error"] <= check["tolerance"]
    changed = deepcopy(details)
    changed["pair_matrices"]["P_cosine"][0, 1] += .2
    with pytest.raises(ValueError, match="VECTOR_STATISTIC_MISMATCH"):
        validate_saved_details(changed, details["groups"])
    changed = deepcopy(details)
    changed["decomposition"]["tolerance"] = 1e6
    with pytest.raises(ValueError, match="IDENTITY_TOLERANCE_CHANGED"):
        validate_saved_details(changed, details["groups"])


def test_algebra_failure_is_not_repaired_into_a_negative_value():
    details = _details()
    details["decomposition"]["max_pair_error"] = .1
    with pytest.raises(ValueError, match="FOUR_TERM_IDENTITY"):
        validate_saved_details(details, details["groups"])
    details = _details()
    details["pair_matrices"]["R_inner_product"][0, 0] = np.nan
    with pytest.raises(ValueError, match="PAIR_SHAPE_FINITE"):
        validate_saved_details(details, details["groups"])


def test_reconstruction_uses_saved_outer_matrices_and_original_fold_order(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("recovery must never refit")
    import auditory_next.a2_residual_execution as original
    monkeypatch.setattr(original, "fit_background", forbidden)
    monkeypatch.setattr(original, "fit_summary_axis", forbidden)
    records = _records()
    aggregate, terms = reconstruct_aggregates(records, n_boot=32)
    assert len(aggregate) == 144 and len(terms) == 100
    all_rows = aggregate[aggregate.outer_fold.eq("ALL")]
    assert len(all_rows) == 24
    own = [r["details"] for r in records if r["mode"] == "R_SIM"]
    reference = bootstrap_match([d["pair_matrices"]["R_inner_product"] for d in own],
                                [d["groups"] for d in own], n_boot=32, seed=20260917)
    value = all_rows[all_rows["mode"].eq("R_SIM") & all_rows.quantity.eq("R") & all_rows.metric.eq("inner_product")].iloc[0]
    assert value.estimate == pytest.approx(reference["estimate"])
    assert value.ci_lower == pytest.approx(reference["ci95"][0])
    assert value.ci_upper == pytest.approx(reference["ci95"][1])
    assert value.invalid_replicates == reference["invalid_replicates"]
    assert value.n_candidates == 15
    assert not {"groups", "candidate", "fit_scope", "test_scope"} & set(aggregate.columns)


def test_incomplete_fit_matrix_and_different_mode_cohort_fail():
    with pytest.raises(ValueError, match="COMPLETE_TWENTY_FOLD_MATRIX"):
        reconstruct_aggregates(_records()[:-1], n_boot=1)
    records = _records()
    details = records[-1]["details"]
    details["groups"] = tuple("changed_" + g for g in details["groups"])
    with pytest.raises(ValueError, match="DIFFERENT_MODE_COHORT"):
        reconstruct_aggregates(records, n_boot=1)


def _failure(source, *, final=True):
    text = '\n'.join([
        'write_json(dest / "input_hashes.json", hashes)',
        'raise ValueError("A2R_IMMUTABLE_DEPENDENCY_CHANGED")',
        'write_json(dest / "input_hashes.json", hashes)',
        'write_json(dest / "fit_receipts.json", receipts)',
    ])
    line = 3 if final else 1
    trace = (f'  File "{source}/source/auditory_next/a2_residual_execution.py", line {line}, in run\n'
             f'FileExistsError: [Errno 17] File exists: \'{source}/input_hashes.json\'')
    return dict(status="FAILED", command="run-packet", traceback=trace), text


def test_only_the_final_duplicate_hash_write_is_recoverable(tmp_path):
    failure, text = _failure(tmp_path)
    validate_output_failure(failure, tmp_path, text)
    early, text = _failure(tmp_path, final=False)
    with pytest.raises(ValueError, match="NOT_FINAL_OUTPUT_WRITE"):
        validate_output_failure(early, tmp_path, text)
    wrong = deepcopy(failure)
    wrong["traceback"] = wrong["traceback"].replace("FileExistsError:", "ValueError:")
    with pytest.raises(ValueError, match="NOT_THE_OUTPUT_ONLY_FAILURE"):
        validate_output_failure(wrong, tmp_path, text)
    wrong = deepcopy(failure)
    wrong["command"] = "smoke-packet"
    with pytest.raises(ValueError, match="NOT_THE_OUTPUT_ONLY_FAILURE"):
        validate_output_failure(wrong, tmp_path, text)
