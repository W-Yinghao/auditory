#!/usr/bin/env python3
"""Synthetic mathematical and leakage checks for age_probe.py; NumPy only."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

from age_probe import average_ranks, fit_ridge, metrics, run_probe


def verify():
    rng = np.random.default_rng(713)
    x = rng.normal(size=(30, 7))
    x[:, -1] = 7.0
    age = 80.0 + 7.0 * x[:, 0] - 3.0 * x[:, 2] + rng.normal(size=30)
    ids = np.array([f"child_{i:03d}" for i in range(30)])
    folds = np.arange(30) % 5
    checks = []

    # Independent primal normal equations versus the implementation's dual solve.
    tx, ty, qx = x[:17], age[:17], x[17:]
    fit = fit_ridge(tx, ty, 0.1)
    sd = tx.std(axis=0, ddof=0)
    z = (tx - tx.mean(axis=0)) / np.where(sd == 0.0, 1.0, sd)
    zq = (qx - tx.mean(axis=0)) / np.where(sd == 0.0, 1.0, sd)
    penalty = 0.1 * np.sum(z * z) / len(z)
    beta = np.linalg.solve(z.T @ z + penalty * np.eye(z.shape[1]), z.T @ (ty - ty.mean()))
    difference = float(np.max(np.abs(fit.predict(qx) - (ty.mean() + zq @ beta))))
    assert difference < 1e-10, difference
    checks.append({"name": "independent_primal_dual_prediction", "max_abs_difference": difference})

    base = run_probe(x, age, ids, folds)
    test = folds == 0

    def fold0(result):
        return next(f for f in result["fold_results"] if f["fold"] == "0")

    def prediction_map(result, fold=None):
        return {p["id"]: p["prediction_months"] for p in result["children"] if fold is None or p["fold"] == fold}

    perturbed_age = age.copy()
    perturbed_age[test] = 1000.0 + rng.normal(size=int(test.sum())) * 50.0
    changed = run_probe(x, perturbed_age, ids, folds)
    assert prediction_map(base, "0") == prediction_map(changed, "0")
    assert fold0(base) == fold0(changed)
    assert base["model_metrics"] != changed["model_metrics"]
    checks.append({"name": "heldout_age_cannot_change_its_fold_fit_or_alpha", "affected_fold": "0"})

    perturbed_x = x.copy()
    perturbed_x[test, :3] = 500.0 + 100.0 * perturbed_x[test, :3]
    changed_x = run_probe(perturbed_x, age, ids, folds)
    assert fold0(base) == fold0(changed_x)
    assert prediction_map(base, "0") != prediction_map(changed_x, "0")
    checks.append({"name": "heldout_features_cannot_change_its_fold_scaler_or_alpha"})

    duplicate_ids = ids.copy()
    duplicate_ids[1] = duplicate_ids[0]
    try:
        run_probe(x, age, duplicate_ids, folds)
        raise AssertionError("duplicate child IDs accepted")
    except ValueError as exc:
        assert "duplicate child" in str(exc)
    checks.append({"name": "duplicate_child_rows_rejected"})

    missing_age, missing_x = age.copy(), x.copy()
    missing_age[[2, 8]] = [np.nan, np.inf]
    missing_x[2] = np.nan  # Features of age-excluded rows must never enter a fit.
    filtered = run_probe(missing_x, missing_age, ids, folds)
    assert filtered["retained_children"] == 28
    assert {v["id"] for v in filtered["excluded_rows"]} == {ids[2], ids[8]}
    assert not {ids[2], ids[8]} & set(filtered["retained_ids"])
    checks.append({"name": "nonfinite_age_filter_and_explicit_roster"})

    constant = run_probe(np.full((12, 3), 7.0), np.arange(12.0) + 50,
                         np.array([f"constant_{i}" for i in range(12)]), np.arange(12) % 3)
    assert all(p["prediction_months"] == p["train_mean_prediction_months"] for p in constant["children"])
    assert all(f["zero_scale_fallback"] and f["selected_alpha"] == 0.01 for f in constant["fold_results"])
    checks.append({"name": "zero_feature_scale_exact_mean_fallback_and_alpha_tie"})

    order = rng.permutation(len(age))
    reordered = run_probe(x[order], age[order], ids[order], folds[order])
    assert prediction_map(base) == prediction_map(reordered)
    assert base["fold_results"] == reordered["fold_results"]
    checks.append({"name": "input_row_order_invariance"})

    for f in base["fold_results"]:
        train_ids, test_ids = set(f["train_ids"]), set(f["test_ids"])
        validations = [v for group in f["inner_validation_ids"] for v in group]
        assert len(validations) == len(set(validations)) == len(train_ids)
        assert set(validations) == train_ids and not train_ids & test_ids
        assert f["n_inner_folds"] == 4
    checks.append({"name": "inner_children_partition_outer_train_only"})

    assert average_ranks(np.array([5.0, 1.0, 5.0, 9.0])).tolist() == [2.5, 1.0, 2.5, 4.0]
    assert np.isclose(metrics(np.arange(5.0), -np.arange(5.0))["spearman"], -1.0, rtol=0.0, atol=1e-14)
    assert metrics(np.ones(5), np.arange(5.0))["r2"] is None
    assert metrics(np.ones(5), np.arange(5.0))["spearman"] is None
    checks.append({"name": "rank_ties_and_undefined_constant_metrics"})

    small = run_probe(x[:6], age[:6], ids[:6], np.arange(6) % 2)
    assert all(f["n_inner_folds"] == 3 for f in small["fold_results"])
    checks.append({"name": "small_synthetic_outer_folds"})

    with tempfile.TemporaryDirectory(prefix="aln4_age_verify_") as directory:
        path = Path(directory)
        np.savez(path / "input.npz", X=x, age=age, ids=ids, folds=folds,
                 feature_names=np.array([f"f{i}" for i in range(x.shape[1])]))
        completed = subprocess.run([sys.executable, str(Path(__file__).with_name("age_probe.py")),
                                    "--input", str(path / "input.npz"), "--out", str(path / "out.json")],
                                   check=True, capture_output=True, text=True)
        cli = json.loads((path / "out.json").read_text())
        assert prediction_map(cli) == prediction_map(base)
        assert cli["feature_names"] == [f"f{i}" for i in range(x.shape[1])]
        assert len(cli["input_npz_sha256"]) == 64 and completed.returncode == 0
    checks.append({"name": "npz_cli_json_roundtrip"})
    return {"status": "PASS", "numpy_version": np.__version__, "checks_passed": len(checks),
            "checks": checks, "synthetic_only": True,
            "limits": "No private data, source encoder provenance, clinical validity, or predictive benefit is validated here."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Optional JSON verification report")
    args = parser.parse_args()
    result = verify()
    encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
