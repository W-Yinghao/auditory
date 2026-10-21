#!/usr/bin/env python3
"""Post-R1 paired net-risk diagnostics; CPU reference, not production bootstrap-t.

NumPy >= 1.22 is the only non-standard-library dependency. No model fitting,
submission, network, repository mutation, or implicit overwrite is performed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np


STATES = ("H0", "E0", "HP", "EC", "ET")
EFFECTS = ("G0", "GH", "GC", "DT", "NET_C", "NET_T")
NET_EFFECTS = ("NET_C", "NET_T")
DEFINITIONS = {
    "G0": "risk_H0 - risk_E0",
    "GH": "risk_H0 - risk_HP",
    "GC": "risk_HP - risk_EC",
    "DT": "risk_EC - risk_ET",
    "NET_C": "risk_E0 - risk_EC = GH + GC - G0",
    "NET_T": "risk_E0 - risk_ET = GH + GC + DT - G0",
}
REQUIRED = ("cohort", "person_id", "tool", "seed", "unit") + tuple(
    f"risk_{s}" for s in STATES
)
RISK_FINGERPRINTS = tuple(f"risk_{s}_query_fingerprint" for s in STATES)
KNOWN_COLUMNS = set(REQUIRED) | set(RISK_FINGERPRINTS) | {"query_fingerprint"}


class ValidationError(ValueError):
    """The input cannot support the declared paired analysis."""


def effects(risk: dict[str, float]) -> dict[str, float]:
    h0, e0, hp, ec, et = (risk[s] for s in STATES)
    result = dict(zip(EFFECTS, (h0 - e0, h0 - hp, hp - ec, ec - et, e0 - ec, e0 - et)))
    if not all(math.isfinite(x) for x in result.values()):
        raise ValidationError("Nonfinite derived risk contrast")
    return result


def _fingerprint(value: str, location: str) -> str:
    value = value.strip().lower()
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValidationError(f"{location}: query fingerprint must be a SHA-256 hex digest")
    return value


def load_panel(path: Path, expected_seeds: list[int], shared_query_declaration: bool,
               expected_panel_path: Path | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not expected_seeds or len(set(expected_seeds)) != len(expected_seeds):
        raise ValidationError("expected-seeds must be a nonempty list without duplicates")
    if any(type(s) is not int or s < 0 for s in expected_seeds):
        raise ValidationError("expected-seeds must be nonnegative integers")
    expected = set(expected_seeds)
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, int]] = set()
    query_by_person: dict[tuple[str, str], str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        names = reader.fieldnames or []
        if len(set(names)) != len(names):
            raise ValidationError("Duplicate CSV column names")
        absent = set(REQUIRED) - set(names)
        if absent:
            raise ValidationError(f"Missing required CSV columns: {sorted(absent)}")
        per_risk = set(RISK_FINGERPRINTS) & set(names)
        if per_risk and len(per_risk) != len(STATES):
            raise ValidationError("Supply all five risk query fingerprints, not a partial set")
        if not per_risk and ("query_fingerprint" not in names or not shared_query_declaration):
            raise ValidationError("A single query_fingerprint requires --shared-query-declaration; "
                                  "otherwise supply all five risk_*_query_fingerprint columns")
        for line, raw in enumerate(reader, start=2):
            if None in raw or any(v is None for v in raw.values()):
                raise ValidationError(f"CSV line {line}: field count does not match header")
            for name in REQUIRED:
                if not raw[name].strip():
                    raise ValidationError(f"CSV line {line}: empty {name}")
            if re.fullmatch(r"0|[1-9][0-9]*", raw["seed"].strip()) is None:
                raise ValidationError(f"CSV line {line}: seed must be an integer string")
            seed = int(raw["seed"])
            if seed not in expected:
                raise ValidationError(f"CSV line {line}: unexpected seed {seed}")
            risk = {}
            for state in STATES:
                try:
                    value = float(raw[f"risk_{state}"])
                except ValueError as exc:
                    raise ValidationError(f"CSV line {line}: invalid risk_{state}") from exc
                if not math.isfinite(value) or value < 0:
                    raise ValidationError(f"CSV line {line}: risk_{state} must be finite and >= 0; "
                                          "negative rounding errors are not silently clipped")
                risk[state] = value
            fingerprints = [_fingerprint(raw[k], f"CSV line {line}/{k}")
                            for k in RISK_FINGERPRINTS] if per_risk else []
            if "query_fingerprint" in names:
                fingerprints.append(_fingerprint(raw["query_fingerprint"], f"CSV line {line}"))
            if len(set(fingerprints)) != 1:
                raise ValidationError(f"CSV line {line}: the five risks do not bind to the same Q")
            cohort, person, tool, unit = (raw[k].strip() for k in ("cohort", "person_id", "tool", "unit"))
            key = (cohort, person, tool, seed)
            if key in seen:
                raise ValidationError(f"Duplicate (cohort, person_id, tool, seed): {key}")
            seen.add(key)
            person_key = (cohort, person)
            previous = query_by_person.setdefault(person_key, fingerprints[0])
            if previous != fingerprints[0]:
                raise ValidationError(f"Different Q fingerprints across tools/seeds for {person_key}")
            rows.append(dict(cohort=cohort, person_id=person, tool=tool, seed=seed,
                             unit=unit, risks=risk, query_fingerprint=fingerprints[0]))
    if not rows:
        raise ValidationError("No observations in CSV")

    observed: dict[str, dict[str, Any]] = {}
    for cohort in sorted({r["cohort"] for r in rows}):
        group = [r for r in rows if r["cohort"] == cohort]
        people = sorted({r["person_id"] for r in group})
        tools = sorted({r["tool"] for r in group})
        units = {r["unit"] for r in group}
        if len(units) != 1:
            raise ValidationError(f"Mixed units within cohort {cohort}: {sorted(units)}")
        for person in people:
            for tool in tools:
                actual = {r["seed"] for r in group if r["person_id"] == person and r["tool"] == tool}
                if actual != expected:
                    raise ValidationError(f"Incomplete panel for {(cohort, person, tool)}: "
                                          f"expected seeds {sorted(expected)}, got {sorted(actual)}")
        observed[cohort] = dict(person_ids=people, tools=tools, unit=next(iter(units)))

    if expected_panel_path is not None:
        panel = json.loads(expected_panel_path.read_text(encoding="utf-8"))
        if not isinstance(panel, dict) or set(panel) != set(observed):
            raise ValidationError("Expected-panel cohort set differs from CSV")
        for cohort, declared in panel.items():
            if not isinstance(declared, dict) or set(declared) != {"person_ids", "tools", "unit"}:
                raise ValidationError("Each expected-panel cohort needs exactly person_ids, tools, unit")
            for key in ("person_ids", "tools"):
                items = declared[key]
                if (not isinstance(items, list) or not items
                        or any(not isinstance(x, str) or not x or x != x.strip() for x in items)
                        or len(set(items)) != len(items)):
                    raise ValidationError(f"Invalid or duplicate expected-panel {cohort}/{key}")
                if sorted(items) != observed[cohort][key]:
                    raise ValidationError(f"Expected-panel mismatch for {cohort}/{key}")
            if declared["unit"] != observed[cohort]["unit"]:
                raise ValidationError(f"Expected-panel unit mismatch for {cohort}")
    metadata = dict(
        path=str(path.resolve()), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        rows=len(rows), query_binding="five_risk_fingerprints" if per_risk else "adapter_declared_shared_Q",
        cross_tool_and_cross_seed_Q_match=True,
        expected_panel_status="verified" if expected_panel_path else "not_supplied",
        expected_panel_sha256=(hashlib.sha256(expected_panel_path.read_bytes()).hexdigest()
                               if expected_panel_path else None),
        ignored_columns=sorted(set(names) - KNOWN_COLUMNS),
        observed_panel=observed,
    )
    return rows, metadata


def _net_family(values: np.ndarray, labels: list[dict[str, str]], family_id: str,
                bootstrap: int, bootstrap_seed: int) -> dict[str, Any]:
    """Fixed ORIGINAL SE max-|z*|; no bootstrap-specific denominator is used."""
    n, dimensions = values.shape
    means = np.mean(values, axis=0)
    if not np.isfinite(means).all():
        raise ValidationError("Nonfinite family means")
    result: dict[str, Any] = dict(
        family_id=family_id, family_members=labels, n_participants=n,
        method="reference_fixed_original_se_max_abs_z_person_bootstrap",
        production_bootstrap_t_equivalence="not_claimed_or_verified",
        nominal_simultaneous_confidence=0.95, multiplicity_scope="this_cohort_all_supplied_tools_NET_C_and_NET_T",
        bootstrap_requested=bootstrap, bootstrap_used=0,
        bootstrap_zero_resample_se_total=None, bootstrap_zero_resample_se_by_member=None,
        critical_value=None, status="not_run", estimands=[],
    )
    for label, mean in zip(labels, means):
        result["estimands"].append(dict(**label, mean=float(mean), standard_error=None,
                                         simultaneous_ci95=None))
    if n < 3:
        result["status"] = "nonregular_fewer_than_three_people_null_CI"
        return result
    se = np.std(values, axis=0, ddof=1) / math.sqrt(n)
    if not np.isfinite(se).all():
        raise ValidationError("Nonfinite original family standard errors")
    # A constant non-binary float can acquire a tiny spurious std from mean rounding.
    # Detect equal observations directly; do not manufacture certainty from that artifact.
    se[np.ptp(values, axis=0) == 0] = 0.0
    for estimate, error in zip(result["estimands"], se):
        estimate["standard_error"] = float(error)
    zero = np.flatnonzero(se == 0)
    if len(zero):
        result["status"] = "nonregular_zero_original_SE_family_null_CI"
        result["nonregular_members"] = [labels[int(i)] for i in zero]
        return result

    # A cohort-specific deterministic stream makes addition/reordering of other cohorts irrelevant.
    seed_material = f"{bootstrap_seed}:{family_id}".encode("utf-8")
    rng_seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    result["bootstrap_rng_seed"] = rng_seed
    rng = np.random.default_rng(rng_seed)
    maxima = np.empty(bootstrap, dtype=float)
    zero_counts = np.zeros(dimensions, dtype=np.int64)
    any_zero = 0
    for start in range(0, bootstrap, 256):
        count = min(256, bootstrap - start)
        draw = values[rng.integers(0, n, size=(count, n))]
        draw_means = np.mean(draw, axis=1)
        draw_se = np.std(draw, axis=1, ddof=1) / math.sqrt(n)
        zero_draw = (draw_se == 0) | (np.ptp(draw, axis=1) == 0)
        zero_counts += np.sum(zero_draw, axis=0)
        any_zero += int(np.sum(np.any(zero_draw, axis=1)))
        # Zero resample SE is recorded, never used as a divisor and never dropped.
        maxima[start:start + count] = np.max(np.abs((draw_means - means) / se), axis=1)
    if not np.isfinite(maxima).all():
        raise ValidationError("Nonfinite bootstrap statistic; no draws have been dropped")
    critical = float(np.quantile(maxima, 0.95, method="higher"))
    result.update(bootstrap_used=bootstrap, bootstrap_zero_resample_se_total=any_zero,
                  bootstrap_zero_resample_se_by_member=[
                      dict(**label, count=int(count)) for label, count in zip(labels, zero_counts)],
                  critical_value=critical)
    if critical <= 0:
        result["status"] = "nonregular_zero_bootstrap_critical_value_null_CI"
        return result
    result["status"] = "ok_reference_intervals"
    for estimate, mean, error in zip(result["estimands"], means, se):
        bounds = [float(mean - critical * error), float(mean + critical * error)]
        if not all(math.isfinite(x) for x in bounds):
            raise ValidationError("Nonfinite confidence limits")
        estimate["simultaneous_ci95"] = bounds
    return result


def build_report(input_path: Path, expected_seeds: list[int], *, bootstrap: int = 4000,
                 bootstrap_seed: int = 20261021, family_id: str = "POST_R1_NET_DIAGNOSTIC",
                 shared_query_declaration: bool = False,
                 expected_panel_path: Path | None = None) -> dict[str, Any]:
    if bootstrap < 1000:
        raise ValidationError("Use at least 1000 bootstrap draws; default is 4000")
    if bootstrap_seed < 0 or not family_id.strip():
        raise ValidationError("bootstrap-seed must be nonnegative; family-id must be nonempty")
    rows, metadata = load_panel(input_path, expected_seeds, shared_query_declaration, expected_panel_path)
    seeds = sorted(expected_seeds)
    report: dict[str, Any] = dict(
        schema_version="aln4.paired_risk_summary.v1", input=metadata,
        analysis_scope={
            "label": "post_R1_diagnostic_net_contrasts",
            "registration": "defined_after_observed_R1; prospective_R2_binding_is_external",
            "reference_helper_only": True,
            "original_R1_R2_families": "retained_unchanged_not_replaced_by_this_report",
            "conditional_on": "supplied_fitted_models_and_fixed_seed_list",
            "resampling_unit": "person_after_equal_weight_mean_over_fixed_seeds",
            "not_estimated": ["J", "cross_cohort_effect", "training_seed_population_uncertainty"],
        },
        expected_seeds=seeds, definitions=DEFINITIONS,
        inference_parameters=dict(bootstrap=bootstrap, bootstrap_seed=bootstrap_seed,
                                  numpy_version=np.__version__), cohorts=[],
        warnings=["Reference intervals are not verified replicas of production bootstrap-t.",
                  "No joint multiplicity guarantee across separate cohort families.",
                  "A matching digest checks the declaration, not the adapter's underlying query membership."],
    )
    if expected_panel_path is None:
        report["warnings"].append("No expected roster/tool panel supplied: entirely absent people/tools cannot be detected.")
    index = {(r["cohort"], r["person_id"], r["tool"], r["seed"]): r for r in rows}
    for cohort, panel in metadata["observed_panel"].items():
        tools, people = panel["tools"], panel["person_ids"]
        labels = [dict(tool=tool, effect=effect) for tool in tools for effect in NET_EFFECTS]
        values = np.empty((len(people), len(labels)))
        per_person = []
        for i, person in enumerate(people):
            for j, tool in enumerate(tools):
                source = [index[cohort, person, tool, seed] for seed in seeds]
                mean = np.mean([[r["risks"][s] for s in STATES] for r in source], axis=0)
                if not np.isfinite(mean).all():
                    raise ValidationError("Nonfinite within-person mean")
                risks = dict(zip(STATES, map(float, mean)))
                gains = effects(risks)
                values[i, 2 * j:2 * j + 2] = [gains[e] for e in NET_EFFECTS]
                per_person.append(dict(
                    person_id=person, tool=tool, seed_count=len(seeds), risks=risks, effects=gains,
                    query_fingerprint=source[0]["query_fingerprint"],
                    by_seed=[dict(seed=r["seed"], risks=r["risks"], effects=effects(r["risks"])) for r in source]))
        descriptive = []
        for tool in tools:
            persons = [p for p in per_person if p["tool"] == tool]
            descriptive.append(dict(
                tool=tool,
                mean_risks={s: float(np.mean([p["risks"][s] for p in persons])) for s in STATES},
                mean_effects={e: float(np.mean([p["effects"][e] for p in persons])) for e in EFFECTS}))
        residuals = [abs(p["effects"]["NET_C"] - (p["effects"]["GH"] + p["effects"]["GC"] - p["effects"]["G0"]))
                     for p in per_person]
        residuals += [abs(p["effects"]["NET_T"] - (p["effects"]["GH"] + p["effects"]["GC"]
                                                   + p["effects"]["DT"] - p["effects"]["G0"]))
                      for p in per_person]
        report["cohorts"].append(dict(
            cohort=cohort, unit=panel["unit"], n_participants=len(people), tools=tools,
            person_ids=people, descriptive_by_tool=descriptive, per_person=per_person,
            max_algebra_reconstruction_error=max(residuals),
            net_family=_net_family(values, labels, f"{family_id}::{cohort}", bootstrap, bootstrap_seed)))
    # Enforce standard JSON before returning; NaN/Infinity must never become an artifact.
    json.dumps(report, allow_nan=False)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-seeds", type=int, nargs="+", required=True)
    parser.add_argument("--expected-panel", type=Path,
                        help="Optional JSON: cohort -> {person_ids, tools, unit}; rejects wholly missing members")
    parser.add_argument("--shared-query-declaration", action="store_true",
                        help="Explicit adapter declaration that one query_fingerprint binds all five state risks")
    parser.add_argument("--family-id", default="POST_R1_NET_DIAGNOSTIC")
    parser.add_argument("--bootstrap", type=int, default=4000)
    parser.add_argument("--bootstrap-seed", type=int, default=20261021)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValidationError(f"Output already exists; choose a new path: {args.output}")
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            report = build_report(args.input, args.expected_seeds, bootstrap=args.bootstrap,
                                  bootstrap_seed=args.bootstrap_seed, family_id=args.family_id,
                                  shared_query_declaration=args.shared_query_declaration,
                                  expected_panel_path=args.expected_panel)
        payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(payload)
        print(f"Wrote {args.output}: {len(report['cohorts'])} separate cohort families; reference diagnostics only")
        return 0
    except (OSError, ValueError, FloatingPointError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
