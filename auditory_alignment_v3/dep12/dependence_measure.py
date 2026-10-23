"""NumPy reference for traditional, self-pair-inclusive Parzen CS dependence.

This module is a measurement reference, not a production training implementation.
It uses natural logarithms and does not claim to estimate Shannon mutual
information. Permutations MUST be supplied by the caller: this module validates
their indices, not their temporal exchangeability or scientific validity.
"""
from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

_ALLOWED_CALIBRATION_SCOPES = {
    "source_train", "source_dev", "target_train_unlabelled",
    "declared_target_support",
}


def _rows(values: Any, name: str) -> np.ndarray:
    raw = np.asarray(values)
    if np.iscomplexobj(raw):
        raise ValueError(f"{name} must be real")
    try:
        x = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain numeric real values") from exc
    if x.ndim != 2 or x.shape[0] < 2 or x.shape[1] < 1:
        raise ValueError(f"{name} must have shape (n>=2, d>=1)")
    if not np.isfinite(x).all():
        raise ValueError(f"{name} contains NaN or Inf")
    return x


def _sigma(value: Any, name: str) -> float:
    sigma = float(value)
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError(f"{name} must be a finite, strictly positive scalar")
    return sigma


def _pairwise_squared_distances(x: np.ndarray) -> np.ndarray:
    """Direct differences avoid cancellation; temporary memory is O(n*d)."""
    n = len(x)
    d2 = np.zeros((n, n), dtype=np.float64)
    try:
        with np.errstate(over="raise", invalid="raise"):
            for i in range(n - 1):
                difference = x[i + 1:] - x[i]
                row = np.einsum("ij,ij->i", difference, difference)
                d2[i, i + 1:] = row
                d2[i + 1:, i] = row
    except FloatingPointError as exc:
        raise ValueError("Pairwise distance overflow: inspect feature scale") from exc
    return d2


def gaussian_gram(rows: Any, sigma: float) -> np.ndarray:
    """Gaussian OVERLAP kernel; KDE component SD is sigma/sqrt(2).

    K_ij = exp(-||x_i-x_j||^2 / (2*sigma^2)).
    The diagonal remains one. sigma must already have been calibrated on a
    permitted panel; it is never recalibrated by a measurement or permutation.
    """
    x = _rows(rows, "rows")
    s = _sigma(sigma, "sigma")
    d2 = _pairwise_squared_distances(x)
    with np.errstate(over="ignore", under="ignore", invalid="raise"):
        scaled = (d2 / s) / s
        k = np.exp(-0.5 * scaled)
    if not np.isfinite(k).all():
        raise ValueError("Nonfinite Gaussian kernel")
    return k


def delta_gram(labels: Any) -> np.ndarray:
    """Counting-measure category kernel; labels must be a 1-D typed array."""
    y = np.asarray(labels)
    if y.ndim != 1 or len(y) < 2:
        raise ValueError("labels must have shape (n>=2,)")
    if y.dtype.kind not in "biuUS":
        raise ValueError(
            "labels must have bool, integer, unicode or byte-string dtype; "
            "encode categories explicitly rather than passing floats/objects"
        )
    return (y[:, None] == y[None, :]).astype(np.float64)


def _validate_calibration_provenance(calibration_scope: str, panel_id: str) -> None:
    if (
        not isinstance(calibration_scope, str)
        or calibration_scope not in _ALLOWED_CALIBRATION_SCOPES
    ):
        raise ValueError(
            "calibration_scope must be source_train, source_dev, "
            "target_train_unlabelled or declared_target_support; "
            "query/test calibration is prohibited"
        )
    if not isinstance(panel_id, str) or not panel_id.strip():
        raise ValueError("panel_id must be a nonempty provenance identifier")


def _lower_median_bandwidth(distances: np.ndarray, multiplier: float) -> dict[str, Any]:
    mult = _sigma(multiplier, "multiplier")
    middle = (len(distances) - 1) // 2
    median = float(np.partition(distances, middle)[middle])
    sigma = median * mult
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError(
            "Nonpositive/nonfinite calibration median: inspect duplicated or "
            "collapsed rows; no automatic bandwidth fallback is applied"
        )
    return {
        "overlap_sigma": sigma,
        "kde_component_sd": sigma / np.sqrt(2.0),
        "multiplier": mult,
        "distance_median": median,
        "n_pairs": int(len(distances)),
        "fixed_after_calibration": True,
    }


def calibrate_overlap_sigma(
    training_rows: Any,
    *,
    calibration_scope: str,
    panel_id: str,
    multiplier: float = 1.0,
) -> dict[str, Any]:
    """Calibrate a single panel once; never use query/test rows.

    For multiple listeners, use calibrate_grouped_overlap_sigma; concatenating
    their rows here would include between-person distances. Scope validation
    does not prove provenance. Persist actual panel membership, checkpoint and
    split digest. source_dev requires declared development access;
    target_train_unlabelled means target-cohort TRAINING people, not evaluation
    people or query material. declared_target_support must be separately allowed.
    Repeated-row zero distances are included; no bandwidth fallback is hidden.
    """
    _validate_calibration_provenance(calibration_scope, panel_id)
    x = _rows(training_rows, "training_rows")
    d2 = _pairwise_squared_distances(x)
    distances = np.sqrt(d2[np.triu_indices(len(x), 1)])
    return {
        **_lower_median_bandwidth(distances, multiplier),
        "rule": "unordered_offdiagonal_lower_median_including_zeros",
        "n_rows": int(len(x)),
        "feature_dim": int(x.shape[1]),
        "calibration_scope": calibration_scope,
        "panel_id": panel_id,
    }


def calibrate_grouped_overlap_sigma(
    person_rows: Mapping[Any, Any],
    *,
    calibration_scope: str,
    panel_id: str,
    multiplier: float = 1.0,
) -> dict[str, Any]:
    """Pool ONLY within-person upper-triangle distances from equal-size panels.

    Each mapping value must have the same (n>=2, d>=1) shape. Equal anchor counts
    give every person the same number of pair distances, regardless of the size
    of their available recording. The caller selects those anchors under the
    declared source/train/support protocol before invoking this function.
    Keys must be nonempty strings or integers and are returned as provenance.

    No between-person distance is computed. The pooled lower median includes
    zeros. Scopes have the same access meaning as calibrate_overlap_sigma;
    target_train_unlabelled never permits fitting on query/evaluation people.
    """
    _validate_calibration_provenance(calibration_scope, panel_id)
    if not isinstance(person_rows, Mapping) or not person_rows:
        raise ValueError("person_rows must be a nonempty mapping of person IDs to rows")
    person_ids: list[str | int] = []
    distances_per_person = []
    expected_shape = None
    for person_id, values in person_rows.items():
        if isinstance(person_id, str) and person_id.strip():
            normalized_id = person_id
        elif isinstance(person_id, (int, np.integer)) and not isinstance(
            person_id, (bool, np.bool_)
        ):
            normalized_id = int(person_id)
        else:
            raise ValueError("Person IDs must be nonempty strings or integers")
        x = _rows(values, f"person_rows[{person_id!r}]")
        if expected_shape is None:
            expected_shape = x.shape
        elif x.shape != expected_shape:
            raise ValueError(
                "Every person must have the same fixed anchor count and feature dimension"
            )
        person_ids.append(normalized_id)
        d2 = _pairwise_squared_distances(x)
        distances_per_person.append(np.sqrt(d2[np.triu_indices(len(x), 1)]))
    # Computing distances after concatenating rows would mix identity offsets
    # into the calibration and is deliberately not used here.
    distances = np.concatenate(distances_per_person)
    n_rows, feature_dim = expected_shape
    n_people = len(person_ids)
    return {
        **_lower_median_bandwidth(distances, multiplier),
        "rule": "pooled_within_person_offdiagonal_lower_median_including_zeros",
        "n_people": n_people,
        "person_ids": person_ids,
        "n_rows_per_person": int(n_rows),
        "n_rows_total": int(n_people * n_rows),
        "n_pairs_per_person": int(n_rows * (n_rows - 1) // 2),
        "feature_dim": int(feature_dim),
        "cross_person_pairs_included": False,
        "equal_person_pair_weight": True,
        "calibration_scope": calibration_scope,
        "panel_id": panel_id,
    }


def _gram(values: Any, name: str) -> np.ndarray:
    raw = np.asarray(values)
    if np.iscomplexobj(raw):
        raise ValueError(f"{name} must be real")
    g = np.asarray(values, dtype=np.float64)
    if g.ndim != 2 or g.shape[0] != g.shape[1] or g.shape[0] < 2:
        raise ValueError(f"{name} must have shape (n>=2, n)")
    if not np.isfinite(g).all():
        raise ValueError(f"{name} contains NaN or Inf")
    if np.any(g < 0) or np.any(g > 1):
        raise ValueError(f"{name} must be a normalized Gaussian/delta Gram in [0,1]")
    if not np.allclose(g, g.T, rtol=1e-10, atol=1e-12):
        raise ValueError(f"{name} must be symmetric")
    if not np.allclose(np.diag(g), 1.0, rtol=0, atol=1e-12):
        raise ValueError(f"{name} must retain unit self-pairs")
    # These checks do not prove that arbitrary caller-supplied matrices are
    # actual density overlaps. Prefer gaussian_gram or delta_gram above.
    return g


def _raw_cs(k: np.ndarray, l: np.ndarray) -> dict[str, Any]:
    a = float(np.mean(k * l))
    b = float(np.mean(k) * np.mean(l))
    c = float(np.mean(np.mean(k, axis=1) * np.mean(l, axis=1)))
    if min(a, b, c) <= 0 or not np.isfinite([a, b, c]).all():
        raise ValueError("Invalid Parzen potentials")
    la, lb, lc = float(np.log(a)), float(np.log(b)), float(np.log(c))
    return {
        "raw_cs_nats": la + lb - 2.0 * lc,
        "joint_square": a,
        "marginal_product_square": b,
        "cross_overlap": c,
        "log_joint_square": la,
        "log_marginal_product_square": lb,
        "log_cross_overlap": lc,
        "n_rows": int(len(k)),
        "includes_self_pairs": True,
        "estimator": "uniform_weight_Parzen_V_statistic",
    }


def parzen_cs(k: Any, l: Any) -> dict[str, Any]:
    """Complete CS statistic with A, B and C; no nonnegative clipping."""
    kg, lg = _gram(k, "k"), _gram(l, "l")
    if kg.shape != lg.shape:
        raise ValueError("k and l must have matching shapes")
    return _raw_cs(kg, lg)


def kernel_diagnostics(gram: Any, *, saturation_tol: float = 1e-12) -> dict[str, Any]:
    """Descriptive numerical saturation flags, never performance stop rules."""
    g = _gram(gram, "gram")
    tol = float(saturation_tol)
    if not np.isfinite(tol) or not 0 <= tol < 0.5:
        raise ValueError("saturation_tol must be finite and in [0,0.5)")
    off = g[np.triu_indices(len(g), 1)]
    q05, median, q95 = np.quantile(off, [0.05, 0.5, 0.95])
    return {
        "offdiag_mean": float(off.mean()),
        "offdiag_q05": float(q05),
        "offdiag_median": float(median),
        "offdiag_q95": float(q95),
        "near_zero_offdiag_fraction": float(np.mean(off <= tol)),
        "near_one_offdiag_fraction": float(np.mean(off >= 1.0 - tol)),
        "identity_like": bool(np.all(off <= tol)),
        "constant_like": bool(np.all(off >= 1.0 - tol)),
        "saturation_tol": tol,
    }


def validate_permutations(permutations: Any, n: int) -> np.ndarray:
    """Validate index syntax only; exchangeability remains the caller's task."""
    p = np.asarray(permutations)
    if p.ndim != 2 or p.shape[0] < 1 or p.shape[1] != n:
        raise ValueError("permutations must have shape (B>=1, n)")
    if p.dtype.kind not in "iu":
        raise ValueError("permutations must have integer dtype")
    reference = np.arange(n, dtype=np.int64)
    if not np.all(np.sort(p, axis=1) == reference[None, :]):
        raise ValueError("Each permutation must contain every index 0..n-1 exactly once")
    return p.astype(np.int64, copy=False)


def measure_from_grams(
    k: Any,
    l: Any,
    permutations: Any,
    *,
    null_design: str,
    null_sd_atol: float = 1e-12,
    null_sd_rtol: float = 1e-8,
) -> dict[str, Any]:
    """Observed, explicit-null and excess CS under one frozen kernel protocol.

    No permutation is generated, removed, deduplicated or altered here.
    Duplicate/identity null draws are recorded; their scientific legality
    depends on the supplied randomization design. This reference reports no
    p-value because it cannot establish the design's exchangeability.
    """
    if not isinstance(null_design, str) or not null_design.strip():
        raise ValueError("null_design must explicitly identify the caller's design")
    for value, name in ((null_sd_atol, "null_sd_atol"), (null_sd_rtol, "null_sd_rtol")):
        if not np.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and nonnegative")
    kg, lg = _gram(k, "k"), _gram(l, "l")
    if kg.shape != lg.shape:
        raise ValueError("k and l must have matching shapes")
    p = validate_permutations(permutations, len(kg))
    observed = _raw_cs(kg, lg)
    values = np.array([
        _raw_cs(kg, lg[np.ix_(row, row)])["raw_cs_nats"] for row in p
    ], dtype=np.float64)
    mean = float(values.mean())
    excess = float(observed["raw_cs_nats"] - mean)
    if len(values) < 2:
        sd, z, status, threshold = None, None, "insufficient_null_replicates", None
    else:
        sd = float(values.std(ddof=1))
        threshold = float(
            null_sd_atol + null_sd_rtol * max(abs(mean), abs(observed["raw_cs_nats"]))
        )
        if sd <= threshold:
            z, status = None, "near_zero_null_sd"
        else:
            z, status = excess / sd, "ok"
    identity = np.arange(len(kg))
    return {
        **observed,
        "null_mean_nats": mean,
        "null_sd_nats": sd,
        "excess_cs_nats": excess,
        "z": z,
        "z_status": status,
        "null_sd_atol": float(null_sd_atol),
        "null_sd_rtol": float(null_sd_rtol),
        "null_sd_threshold": threshold,
        "null_scores_nats": values.tolist(),
        "n_null_draws": int(len(p)),
        "n_unique_permutations": int(len(np.unique(p, axis=0))),
        "n_identity_permutations": int(np.sum(np.all(p == identity[None, :], axis=1))),
        "null_design": null_design,
        "permutation_index_syntax_validated": True,
        "exchangeability_validated_by_this_module": False,
        "k_diagnostics": kernel_diagnostics(kg),
        "l_diagnostics": kernel_diagnostics(lg),
        "units_note": "CS nats, not Shannon MI; n_rows is not the number of people",
    }


def measure_dependence(
    u: Any,
    v: Any | None = None,
    *,
    labels: Any | None = None,
    sigma_u: float,
    sigma_v: float | None = None,
    permutations: Any,
    null_design: str,
    null_sd_atol: float = 1e-12,
    null_sd_rtol: float = 1e-8,
) -> dict[str, Any]:
    """High-level Gaussian/Gaussian or Gaussian/category measurement."""
    if (v is None) == (labels is None):
        raise ValueError("Supply exactly one of v and labels")
    ur = _rows(u, "u")
    k = gaussian_gram(ur, sigma_u)
    if v is not None:
        vr = _rows(v, "v")
        if len(vr) != len(ur) or sigma_v is None:
            raise ValueError("v must match u rows, and sigma_v is required")
        l = gaussian_gram(vr, sigma_v)
        target = {"kernel_kind": "continuous_continuous", "target_dim": int(vr.shape[1])}
    else:
        if sigma_v is not None:
            raise ValueError("sigma_v does not apply to a category delta kernel")
        l = delta_gram(labels)
        if len(l) != len(ur):
            raise ValueError("labels must match u rows")
        target = {"kernel_kind": "continuous_categorical", "target_dim": None}
    result = measure_from_grams(
        k, l, permutations, null_design=null_design,
        null_sd_atol=null_sd_atol, null_sd_rtol=null_sd_rtol,
    )
    result.update(target)
    result.update(
        feature_dim=int(ur.shape[1]),
        sigma_u=float(sigma_u),
        sigma_v=None if sigma_v is None else float(sigma_v),
        bandwidths_recalibrated_during_measurement=False,
    )
    return result


def leave_one_out_raw_cs(k: Any, l: Any) -> dict[str, Any]:
    """Full-statistic deletion sensitivity, with frozen original Gram kernels.

    The retained pairs have size n-1. This is RAW CS sensitivity, not an
    excess-dependence contribution, a significance test or a neural attribution.
    Source feature scaling and bandwidth MUST NOT be refitted after deletion.
    Reference implementation uses explicit reduced matrices for auditability.
    """
    kg, lg = _gram(k, "k"), _gram(l, "l")
    if kg.shape != lg.shape or len(kg) < 3:
        raise ValueError("Matching Gram matrices with n>=3 are required")
    n = len(kg)
    total = float(_raw_cs(kg, lg)["raw_cs_nats"])
    reduced = []
    for i in range(n):
        keep = np.concatenate((np.arange(i), np.arange(i + 1, n)))
        reduced.append(float(_raw_cs(
            kg[np.ix_(keep, keep)], lg[np.ix_(keep, keep)]
        )["raw_cs_nats"]))
    delta = total - np.asarray(reduced)
    return {
        "raw_cs_before_nats": total,
        "n_before": n,
        "n_after": n - 1,
        "raw_cs_leave_one_out_nats": reduced,
        "raw_deletion_change_nats": delta.tolist(),
        "mean_centered_raw_deletion_change_nats": (delta - delta.mean()).tolist(),
        "includes_sample_count_effect": True,
        "null_recomputed": False,
        "bandwidths_refitted": False,
        "interpretation": "descriptive_raw_full_statistic_deletion_sensitivity_only",
        "not_excess_contribution": True,
        "not_significance": True,
    }


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="NPZ: u, v OR labels, permutations")
    parser.add_argument("--output", required=True, help="JSON output path")
    parser.add_argument("--sigma-u", type=float, required=True)
    parser.add_argument("--sigma-v", type=float)
    parser.add_argument("--null-design", required=True, help="Registered null design ID")
    parser.add_argument("--raw-loo", action="store_true")
    args = parser.parse_args()
    with np.load(args.input, allow_pickle=False) as data:
        if "u" not in data or "permutations" not in data:
            raise ValueError("NPZ must contain u and explicit permutations")
        has_v, has_labels = "v" in data, "labels" in data
        if has_v == has_labels:
            raise ValueError("NPZ must contain exactly one of v and labels")
        u = np.array(data["u"])
        v = np.array(data["v"]) if has_v else None
        labels = np.array(data["labels"]) if has_labels else None
        perms = np.array(data["permutations"])
    result = measure_dependence(
        u, v, labels=labels, sigma_u=args.sigma_u, sigma_v=args.sigma_v,
        permutations=perms, null_design=args.null_design,
    )
    if args.raw_loo:
        k = gaussian_gram(u, args.sigma_u)
        l = gaussian_gram(v, args.sigma_v) if v is not None else delta_gram(labels)
        result["raw_leave_one_out"] = leave_one_out_raw_cs(k, l)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(destination), "z_status": result["z_status"]}))


if __name__ == "__main__":
    _main()

