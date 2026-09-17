"""S4: aggregate explicit immutable runs, without fitting or recomputing bootstrap.

Only public aggregate summaries/tables are copied to public outputs. Private plan
receipts are checked for S3 completeness and hashed; trial EEG, individual OOF
predictions and clinical rows are never read here. A missing estimate is absent.
R_SIM remains primary; R_SUP is parallel. Fixed-OOF intervals do not include
pipeline refitting. Numerical failures precede scientific negative verdicts.

Slurm API: run(run_name, sources_path, *, root=ROOT). The source YAML is an exact
registry, not a directory search. Re-running requires a new immutable run name.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from auditory5.provenance import ROOT, digest, object_hash, require_slurm, write_json

METRIC_COLUMNS = ("route", "mode", "statistic", "estimate", "ci_lower", "ci_upper",
                  "n_candidates", "units", "run")
AGGREGATE_COLUMNS = ("route", "stage", "experiment_id", "preprocessing_id", "dataset_scope",
    "representation_mode", "reader_family", "split_protocol", "seed", "outer_fold", "comparison_id",
    "primary_endpoint", "value", "unit", "ci_lower", "ci_upper", "ci_scope", "n_candidate_groups",
    "n_records", "n_trials", "coverage_fraction", "control_status", "verdict", "limitation_code")
ROUTES = tuple("ABCDE")
MODES = {"L0", "R_SUP", "R_SIM", "R_RAND", "E0_native"}
FAIL_STATES = {"FAIL", "IMPLEMENTATION_FAIL", "NUMERICAL_FAILURE", "E0_PARTIAL_NUMERICAL_FAILURE"}
C_FILES = ("single_joint_gains.csv", "capacity_controls.csv", "fixed_head_interventions.csv",
           "coverage.csv", "input_isolation_tests.json", "synthetic_controls.json")
D_FILES = ("control_status.json", "fp32_invariance.json", "null_stimulus_probe.json",
           "clinical_sensitivities.csv")


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_]+", value):
        raise ValueError("UNSAFE_RUN_IDENTIFIER")
    return value


def _number(value):
    if isinstance(value, bool):
        raise ValueError("BOOLEAN_ESTIMATE")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("NONFINITE_ESTIMATE")
    return number


def _integer(value):
    number = _number(value)
    if number < 0 or not number.is_integer():
        raise ValueError("INVALID_COUNT")
    return int(number)


def _read_json(path):
    def reject(_):
        raise ValueError("NONFINITE_JSON")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject)


def _ci(row, n=None):
    """Normalize actual finite intervals; None is unavailable, not an effect."""
    estimate = _number(row["estimate"])
    low, high = row["ci95"] if "ci95" in row else (row["ci_lower"], row["ci_upper"])
    low, high = _number(low), _number(high)
    if low > high:
        raise ValueError("REVERSED_INTERVAL")
    count = _integer(row.get("n_candidates", n))
    for key in ("n_bootstrap", "n_boot"):
        if key in row and _integer(row[key]) != 2000:
            raise ValueError("UNFROZEN_BOOTSTRAP_COUNT")
    if count == 0:
        raise ValueError("EMPTY_EFFECT_COHORT")
    return dict(estimate=estimate, ci_lower=low, ci_upper=high, n_candidates=count)


@dataclass
class Source:
    route: str
    kind: str
    run: str
    modes: tuple
    state: str = "MISSING"
    summary: dict = field(default_factory=dict)
    files: dict = field(default_factory=dict)
    pending: list = field(default_factory=list)
    errors: list = field(default_factory=list)


def _artifact(path, label, audit):
    """Record both source hashes; refuse a file changed during aggregation."""
    if not path.exists():
        audit.append(dict(label=label, status="MISSING", path=str(path)))
        return None
    before = digest(path)
    try:
        if path.suffix == ".csv":
            with path.open(newline="", encoding="utf-8") as stream:
                result = list(csv.DictReader(stream))
        elif path.suffix == ".json":
            result = _read_json(path)
        else:
            result = path.read_text(encoding="utf-8")
    finally:
        after = digest(path)
        audit.append(dict(label=label, status="READ" if before == after else "MUTATED",
                          sha256=before, sha256_after=after, path=str(path)))
    if before != after:
        raise ValueError("SOURCE_MUTATED_DURING_READ")
    return result


def read_source(spec, public_root, audit):
    source = Source(spec["route"], spec["kind"], _identifier(spec["run"]), tuple(spec["modes"]))
    try:
        base = public_root / source.run
        summary = _artifact(base / "summary.json", source.run + "/summary.json", audit)
        failure = _artifact(base / "failure.json", source.run + "/failure.json", audit)
        if failure is not None and not isinstance(failure, dict):
            raise ValueError("FAILURE_SCHEMA")
        if failure is not None and failure.get("status") in FAIL_STATES:
            source.state = "FAIL"
            source.summary = summary or failure
            source.errors.append("declared_failure")
            return source
        if summary is None:
            source.pending.append("summary.json")
            return source
        if not isinstance(summary, dict) or not isinstance(summary.get("status"), str):
            raise ValueError("SUMMARY_SCHEMA")
        source.summary = summary
        source.state = "FAIL" if summary["status"] in FAIL_STATES else "READY"
        filenames = C_FILES if source.route == "C" else D_FILES if source.route == "D" and source.kind == "controls" else ()
        if source.state != "FAIL":
            for name in filenames:
                value = _artifact(base / name, source.run + "/" + name, audit)
                if value is None:
                    source.pending.append(name)
                else:
                    source.files[name] = value
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        source.state = "FAIL"
        source.errors.append(type(exc).__name__)
        # Detailed errors remain in the private audit; public status is sanitized.
        audit.append(dict(label=source.run, status="ERROR", detail=repr(exc)))
    return source


def representation_status(plan, plan_hash, plan_path, audit, expected=90):
    tasks = plan.get("tasks", [])
    names = [task.get("name") for task in tasks]
    if len(tasks) != expected or len(set(names)) != expected:
        return dict(status="IMPLEMENTATION_FAIL", completed=0, expected=expected, reason="fixed_task_matrix")
    completed, failed, pending = 0, 0, 0
    for task in tasks:
        name = _identifier(task["name"])
        base = plan_path.parent / "outputs" / name
        try:
            receipt = _artifact(base / "completion.json", "representation/" + name + "/completion.json", audit)
            submitted = _artifact(base / "task.json", "representation/" + name + "/task.json", audit)
            if receipt is None:
                pending += 1
                continue
            same_task = submitted is not None and all(submitted.get(k) == v for k, v in task.items())
            valid = (same_task and receipt.get("status") == "PASS" and receipt.get("task") == name and
                     receipt.get("plan_hash") == plan_hash and submitted.get("plan_hash") == plan_hash and
                     bool(receipt.get("encoder_fit_scope_hash")) and
                     all(receipt.get(k) == task.get(k) for k in ("mode", "branch", "stage", "outer_fold", "inner_fold")))
            completed += int(valid)
            failed += int(not valid)
        except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
            failed += 1
            audit.append(dict(label="representation/" + name, status="ERROR", detail=repr(exc)))
    status = "IMPLEMENTATION_FAIL" if failed else "S3_COMPLETE" if completed == expected else "IN_PROGRESS"
    return dict(status=status, completed=completed, expected=expected, failed=failed, pending=pending)


def _metric(source, mode, statistic, row, n=None, units="bits/trial"):
    return dict(route=source.route, mode=mode, statistic=statistic, **_ci(row, n), units=units, run=source.run)


def extract_metrics(source):
    """Read reported aggregate estimates, including valid E linear partial results."""
    s, output = source.summary, []
    if not s or source.kind == "controls" or (source.state == "FAIL" and source.route != "E"):
        return output
    if source.route == "A":
        for row in s.get("results", []):
            if row.get("analysis") == "alternate20" and row.get("statistics", {}).get("post"):
                output.append(_metric(source, row["mode"], "post_T", row["statistics"]["post"], row["n_candidates"], "cosine_difference"))
    elif source.route == "B":
        representations = s.get("representations", {"L0": s})
        for mode, content in representations.items():
            for row in content.get("comparisons", []):
                if (row.get("analysis_set"), row.get("probability_mode"), row.get("comparison")) == ("all", "calibrated", "main_gain"):
                    output.append(_metric(source, mode, "calibrated_main_gain", row))
    elif source.route == "C":
        for row in source.files.get("single_joint_gains.csv", []):
            if row.get("statistic") == "T_C":
                output.append(_metric(source, row["representation"], "T_C_" + row["family"] + "_" + row["probability_mode"], row))
    elif source.route == "D":
        for row in s.get("modes", []):
            if row.get("main_D2_minus_D3"):
                output.append(_metric(source, row["mode"], "D2_minus_D3", row["main_D2_minus_D3"], row["n_candidates"], "MUSS_source_points"))
    elif source.route == "E":
        family_states = s.get("family_status", {})
        for row in s.get("results", []):
            if family_states.get(row["family"]) != "COMPLETE":
                raise ValueError("INCOMPLETE_E_FAMILY_AGGREGATED")
            if row.get("family") == "linear" and row.get("calibration") == "calibrated":
                output.append(_metric(source, "E0_native", "linear_calibrated_J_" + row["task"], row["J_bits_interval"]))
    if any(row["mode"] not in source.modes for row in output):
        raise ValueError("UNDECLARED_REPRESENTATION")
    keys = [(row["mode"], row["statistic"]) for row in output]
    if len(keys) != len(set(keys)):
        raise ValueError("DUPLICATE_ESTIMATE")
    return output


def resolve_display_metrics(metrics, sources):
    """Prefer successful full C linear output only after equality validation.

    A fallback and a full run are the same frozen analysis, not replication.
    Conflicting estimates are withheld and flagged; never choose the better one.
    """
    kinds = {s.run: s.kind for s in sources}
    groups = {}
    for row in metrics:
        groups.setdefault((row["route"], row["mode"], row["statistic"]), []).append(row)
    result, conflicts = [], []
    for key, rows in groups.items():
        if len(rows) == 1:
            result.extend(rows)
            continue
        equal = (key[0] == "C" and all(row["n_candidates"] == rows[0]["n_candidates"] and
                 all(abs(row[name] - rows[0][name]) <= 1e-10 for name in ("estimate", "ci_lower", "ci_upper")) for row in rows))
        cores = [row for row in rows if kinds.get(row["run"]) == "core"]
        if not equal or len(cores) != 1:
            conflicts.extend(row["run"] for row in rows)
        else:
            result.extend(cores)
    return result, sorted(set(conflicts))


def _a_primary(source):
    return next((row for row in source.summary.get("results", []) if row.get("mode") == "R_SIM" and row.get("analysis") == "alternate20"), None)


def _b_mode(source, mode):
    return source.summary.get("representations", {}).get(mode, source.summary if mode == "L0" else {})


def _comparison(rows, name, analysis="all", probability="calibrated"):
    found = [row for row in rows if (row.get("comparison"), row.get("analysis_set"), row.get("probability_mode")) == (name, analysis, probability)]
    if len(found) > 1:
        raise ValueError("DUPLICATE_COMPARISON")
    return found[0] if found else None


def _c_rows(source, mode, family="mlp32", probability="calibrated"):
    rows = [row for row in source.files.get("single_joint_gains.csv", []) if
            (row.get("representation"), row.get("family"), row.get("probability_mode")) == (mode, family, probability)]
    if len({row["statistic"] for row in rows}) != len(rows):
        raise ValueError("DUPLICATE_C_STATISTIC")
    return {row["statistic"]: row for row in rows}


def required_controls(source, folds=5):
    """Detailed evidence takes precedence over broad INTERIM/NEED labels."""
    missing, failures = list(source.pending), []
    s = source.summary
    if source.kind == "core" and source.route in "ABD":
        for mode in source.modes:
            if source.route == "A":
                for analysis in ("alternate20", "early_late20", "alternate20_common40", "alternate40"):
                    matches = [r for r in s.get("results", []) if r.get("mode") == mode and r.get("analysis") == analysis]
                    if len(matches) != 1:
                        missing.append(mode + ":" + analysis)
                        continue
                    row = matches[0]
                    fold_rows = row.get("folds", [])
                    if (row.get("status") != "INTERIM_A_CORE_COMPLETE" or len(fold_rows) != folds or
                            len({r.get("fold") for r in fold_rows}) != folds or any(r.get("status") != "PASS" for r in fold_rows)):
                        missing.append(mode + ":" + analysis + ":support")
                    for key in ("post", "pre", "background", "background_adjusted", "random_projection"):
                        stat = row.get("statistics", {}).get(key)
                        if not stat:
                            missing.append(mode + ":" + analysis + ":" + key)
                        else:
                            _ci(stat, row["n_candidates"])
            elif source.route == "B":
                row = _b_mode(source, mode)
                count = row.get("completed_analysis_folds", row.get("completed_model_folds", 0))
                if count != 2 * folds:
                    missing.append(mode + ":complete_history_folds")
                for probability in ("raw", "calibrated"):
                    for name, subset in (("main_gain", "all"), ("post_increment_over_pre", "all"),
                                         ("main_gain", "previous_response_available"),
                                         ("post_increment_over_pre", "previous_response_available"),
                                         ("post_increment_over_previous", "previous_response_available")):
                        stat = _comparison(row.get("comparisons", []), name, subset, probability)
                        if stat is None or _ci(stat)["n_candidates"] < 20:
                            missing.append(mode + ":" + probability + ":" + name + ":" + subset)
                        elif name == "main_gain" and not 0 <= _number(stat["positive_candidate_fraction"]) <= 1:
                            raise ValueError("B_POSITIVE_CANDIDATE_FRACTION")
            else:
                matches = [r for r in s.get("modes", []) if r.get("mode") == mode]
                if len(matches) != 1:
                    missing.append(mode + ":clinical_mode")
                    continue
                row = matches[0]
                expected = {"D0_mean", "D1_C", "D2_CV", "D3_CVN", "D4_CN", "D5_CFULL", "D7_CPRE"}
                expected |= {"D6_CRANDOM_" + str(i) for i in range(20)}
                if row.get("status") != "INTERIM_D_NESTED_CORE_COMPLETE" or not expected <= set(row.get("MAE", {})):
                    missing.append(mode + ":clinical_core_matrix")
                else:
                    for value in row["MAE"].values():
                        _number(value)
                if not row.get("clinical_D1_minus_D3") or len(row.get("leave_one_out_main_gain_range", [])) != 2:
                    missing.append(mode + ":clinical_baseline_or_LOO")
                else:
                    _ci(row["clinical_D1_minus_D3"], row["n_candidates"])
    if source.kind == "controls" and source.route == "A":
        if s.get("version") != "auditory5_A_controls_v1":
            missing.append("A_control_schema_version")
        for mode in source.modes:
            for name in ("continuous_unbalanced", "continuous_balanced", "reset_unbalanced", "reset_balanced",
                         "continuous_unbalanced_on_balanced", "reset_unbalanced_on_balanced", "continuous_on_reset_unbalanced"):
                row = s.get("aggregates", {}).get(mode + ":" + name, {})
                if row.get("status") != "PASS" or row.get("complete_folds") != folds:
                    missing.append(mode + ":" + name)
                elif _integer(row.get("total_candidates", 0)) < 25:
                    missing.append(mode + ":" + name + ":candidate_support")
                else:
                    _ci(row, row["total_candidates"])
            for name in ("continuous_balance_minus_unbalanced", "reset_balance_minus_unbalanced", "reset_minus_continuous_same_reset_trials"):
                row = s.get("aggregates", {}).get(mode + ":" + name, {})
                if row.get("status") != "PASS" or _integer(row.get("total_candidates", 0)) < 25:
                    missing.append(mode + ":" + name)
                else:
                    _ci(dict(estimate=row["paired_estimate"], ci95=row["paired_ci95"]), row["total_candidates"])
        if s.get("fold_mode_status", {}).get("FAIL", 0):
            failures.append("A_control_fold_failure")
    elif source.kind == "controls" and source.route == "B":
        for mode in source.modes:
            row = s.get("modes", {}).get(mode, {})
            counts = row.get("completed_fold_diagnostics", {})
            for name in ("early", "late", "quality", "circular_shift"):
                if counts.get(name) != folds:
                    missing.append(mode + ":" + name)
            for name in ("early", "late", "quality"):
                comparison = _comparison(row.get("comparisons", []), "main_gain", name)
                if comparison is None or _ci(comparison)["n_candidates"] < 20:
                    missing.append(mode + ":" + name + ":comparison_support")
            if not row.get("circular_shift") or len(row.get("context_balance", [])) != 2:
                missing.append(mode + ":context_or_shift")
    elif source.kind == "controls" and source.route == "D":
        states = source.files.get("control_status.json", [])
        for row in states:
            if row.get("status") == "FAIL":
                failures.append("D_control_failure:" + str(row.get("control")))
        if not any(row.get("control") == "count_QC_source" and row.get("status") == "PASS" for row in states):
            missing.append("D_count_QC_source")
        for mode in source.modes:
            for name, count in (("all_trials", folds), ("budget40_count_qc", folds), ("all_trials_count_qc", folds),
                                ("FP32_invariance", folds * 4), ("null_linear_stimulus_probe", folds)):
                rows = [row for row in states if row.get("mode") == mode and row.get("control") == name]
                coordinates = {(row.get("outer_fold"), row.get("inner_fold")) for row in rows}
                if len(rows) != count or len(coordinates) != count or any(row.get("status") != "PASS" for row in rows):
                    missing.append(mode + ":" + name)
            for variant in ("all_trials", "budget40_count_qc", "all_trials_count_qc"):
                rows = [row for row in source.files.get("clinical_sensitivities.csv", []) if
                        row.get("mode") == mode and row.get("variant") == variant and row.get("comparison") == "D2_minus_D3"]
                if len(rows) != 1 or _ci(rows[0])["n_candidates"] < 30:
                    missing.append(mode + ":" + variant + ":complete_cohort")
            numerics = [row for row in source.files.get("fp32_invariance.json", []) if row.get("mode") == mode]
            if len(numerics) != folds * 4:
                missing.append(mode + ":FP32_numeric_evidence")
            for row in numerics:
                if (row.get("dtype") != "float32" or row.get("status") != "PASS" or
                        _number(row["threshold"]) != 1e-6 or
                        max(_number(row["real_max_abs_probability_difference"]), _number(row["synthetic_max_abs_probability_difference"])) > 1e-6 or
                        max(_number(row["projector_difference_float64"]), _number(row["null_projector_difference_float64"])) > 1e-10):
                    failures.append(mode + ":FP32_invariance_numeric_failure")
            null = [row for row in source.files.get("null_stimulus_probe.json", []) if row.get("mode") == mode]
            if len(null) != 2 or {row.get("probability_mode") for row in null} != {"raw", "calibrated"}:
                missing.append(mode + ":null_linear_probe_aggregate")
            else:
                for row in null:
                    _ci(row["J_bits"])
    elif source.route == "C" and source.kind == "core":
        for filename in ("input_isolation_tests.json", "synthetic_controls.json"):
            status = source.files.get(filename, {}).get("status")
            if status == "FAIL":
                failures.append(filename)
            elif status != "PASS":
                missing.append(filename)
        for mode in source.modes:
            coverage = [row for row in source.files.get("coverage.csv", []) if row.get("representation") == mode]
            if len(coverage) != folds or len({row.get("outer_fold") for row in coverage}) != folds or any(row.get("status") != "COMPLETE_FOLD" for row in coverage):
                missing.append(mode + ":complete_fold_coverage")
            for family in ("linear", "mlp32"):
                for probability in ("raw", "calibrated"):
                    matrix = _c_rows(source, mode, family, probability)
                    required = {"T_C", "J_joint", "duplicate_margin"}
                    if family == "mlp32":
                        required |= {"capacity_margin", "expanded_margin"}
                    if not required <= set(matrix):
                        missing.append(mode + ":" + family + ":" + probability + ":capacity_matrix")
                    else:
                        for name in required:
                            _ci(matrix[name])
                    interventions = [row for row in source.files.get("fixed_head_interventions.csv", []) if
                                     (row.get("representation"), row.get("family"), row.get("probability_mode")) == (mode, family, probability)]
                    expected = {(model, intervention) for model in ("C_LR", "C_LL", "C_RR") for intervention in
                                ("zero_first", "zero_second", "same_class_first", "same_class_second", "opposite_class_first", "opposite_class_second")}
                    observed = {(row.get("model"), row.get("intervention")) for row in interventions if
                                row.get("status") != "NEED_CONTROLS" and row.get("ce_increase_bits") not in (None, "")}
                    if observed != expected or len(interventions) != len(expected):
                        missing.append(mode + ":" + family + ":" + probability + ":interventions")
                    else:
                        for row in interventions:
                            _ci(dict(row, estimate=row["ce_increase_bits"]))
    return missing, failures


def scientific_screen(route, core, controls, effect):
    """Apply frozen primary thresholds only after completion/support checks."""
    threshold = {"A": (.05, 25), "B": (.01, 20), "C": (.01, 25), "D": (.5, 30)}[route]
    if effect["n_candidates"] < threshold[1]:
        return "SUPPORT_INSUFFICIENT"
    main = effect["estimate"] >= threshold[0] and effect["ci_lower"] > 0
    if not main:
        return "NEGATIVE_SCREEN"
    if route == "A":
        statistics = _a_primary(core)["statistics"]
        background = statistics.get("background_adjusted", {})
        loo = statistics.get("post_leave_one_candidate_out_range", [])
        if not background or len(loo) != 2:
            return "NEED_CONTROLS"
        reset = next((s.summary.get("aggregates", {}).get("R_SIM:reset_balanced") for s in controls if "R_SIM" in s.modes), None)
        return "POSITIVE_SCREEN" if (_number(background["estimate"]) > 0 and _number(loo[0]) > 0 and
                                     _number(statistics["post"]["paired_estimate"]) > 0 and
                                     reset and _number(reset["estimate"]) > 0) else "MIXED_SCREEN:general_identity_or_sequence"
    if route == "B":
        rows = _b_mode(core, "R_SIM").get("comparisons", [])
        main_row = _comparison(rows, "main_gain")
        if _number(main_row.get("positive_candidate_fraction", 0)) < .60:
            return "NEGATIVE_SCREEN"
        extra = [_comparison(rows, "post_increment_over_pre"),
                 _comparison(rows, "post_increment_over_previous", "previous_response_available")]
        if any(row is None for row in extra):
            return "NEED_CONTROLS"
        return "POSITIVE_SCREEN" if all(_number(row["estimate"]) > 0 for row in extra) else "MIXED_SCREEN:history_present_not_current_specific"
    if route == "C":
        matrix = _c_rows(core, "R_SIM")
        raw = _c_rows(core, "R_SIM", probability="raw")
        okay = all(_number(matrix[name]["ci_lower"]) > 0 for name in ("J_joint", "capacity_margin"))
        okay &= (_number(raw["T_C"]["estimate"]) >= .01 and _number(raw["T_C"]["ci_lower"]) > 0 and
                 all(_number(raw[name]["ci_lower"]) > 0 for name in ("J_joint", "capacity_margin")))
        return "POSITIVE_SCREEN" if okay else "MIXED_SCREEN:capacity_or_calibration"
    row = next(row for row in core.summary["modes"] if row["mode"] == "R_SIM")
    return "POSITIVE_SCREEN" if (_number(row["clinical_D1_minus_D3"]["estimate"]) > 0 and
                                 _number(row["leave_one_out_main_gain_range"][0]) > 0) else "MIXED_SCREEN:recovers_bad_visible_baseline"


def evaluate_route(route, sources, metrics, folds=5):
    relevant = [s for s in sources if s.route == route]
    required = [s for s in relevant if s.kind != "descriptive"]
    failed = [s.run for s in relevant if s.state == "FAIL"]
    pending = [s.run + ":missing" for s in relevant if s.state == "MISSING"]
    pending.extend(s.run + ":" + name for s in relevant if s.kind == "descriptive" for name in s.pending)
    for source in required:
        if source.state == "READY":
            missing, failures = required_controls(source, folds)
            pending.extend(source.run + ":" + name for name in missing)
            failed.extend(source.run + ":" + name for name in failures)
    cores = [s for s in required if s.kind == "core" and "R_SIM" in s.modes]
    if len(cores) > 1:
        raise ValueError("MULTIPLE_PRIMARY_CORE_SOURCES")
    core = cores[0] if cores else None
    statistic = {"A": "post_T", "B": "calibrated_main_gain", "C": "T_C_mlp32_calibrated", "D": "D2_minus_D3"}.get(route)
    candidates = [m for m in metrics if m["route"] == route and m["mode"] == "R_SIM" and m["statistic"] == statistic and core and m["run"] == core.run]
    effect = candidates[0] if len(candidates) == 1 else None
    if route != "E" and effect is None and not (core and core.state == "FAIL"):
        pending.append("R_SIM:primary_estimate")
    if route == "A" and core and _a_primary(core):
        row = _a_primary(core)
        stats = row.get("statistics", {})
        if any(name not in stats for name in ("pre", "background", "background_adjusted", "random_projection", "post_leave_one_candidate_out_range")):
            pending.append("A:core_controls")
        if stats.get("post", {}).get("paired_estimate") is None or stats.get("post", {}).get("paired_ci95") is None:
            pending.append("A:paired_post_minus_pre")
    if route == "B" and core:
        rows = _b_mode(core, "R_SIM").get("comparisons", [])
        for name, subset in (("post_increment_over_pre", "all"), ("main_gain", "previous_response_available"),
                             ("post_increment_over_previous", "previous_response_available")):
            row = _comparison(rows, name, subset)
            if row is None or _ci(row)["n_candidates"] < 20:
                pending.append("B:" + name + ":" + subset)
    if not required:
        pending.append("route_source_registry")
    status = "IMPLEMENTATION_FAIL" if failed else "NEED_CONTROLS" if pending else "SUPPORT_INSUFFICIENT_FOR_E1" if route == "E" else scientific_screen(route, core, [s for s in required if s.kind == "controls"], effect)
    complete = (not failed and not pending and route != "E" and
                (status in {"POSITIVE_SCREEN", "NEGATIVE_SCREEN"} or status.startswith("MIXED_SCREEN")))
    class_dependence = None
    if route == "C" and core and all(_c_rows(core, "R_SIM", family) for family in ("linear", "mlp32")):
        family_support = []
        for family, capacity in (("linear", "duplicate_margin"), ("mlp32", "capacity_margin")):
            matrix = _c_rows(core, "R_SIM", family)
            if all(name in matrix for name in ("T_C", "J_joint", capacity)):
                family_support.append(_number(matrix["T_C"]["estimate"]) >= .01 and
                    all(_number(matrix[key]["ci_lower"]) > 0 for key in ("T_C", "J_joint", capacity)))
        if len(family_support) == 2:
            class_dependence = family_support[0] != family_support[1]
    return dict(route=route, primary_mode="E1:puretone_to_bapa" if route == "E" else "R_SIM",
                primary_endpoint="E1_transfer_gap_not_estimated" if route == "E" else statistic,
                estimate=effect["estimate"] if effect else None, ci_lower=effect["ci_lower"] if effect else None,
                ci_upper=effect["ci_upper"] if effect else None, n_candidates=effect["n_candidates"] if effect else None,
                units=effect["units"] if effect else None, verdict=status, scientific_complete=complete,
                input_status="IN_PROGRESS" if any(s.state == "MISSING" or any(p.endswith((".json", ".csv")) for p in s.pending) for s in relevant) else "RECORDED",
                control_status="FAIL" if failed else "PENDING" if pending else "COMPLETE",
                support_status="SUPPORT_INSUFFICIENT_FOR_E1" if route == "E" else "SEE_EFFECT_AND_CONTROLS",
                pending=sorted(set(pending)), failures=sorted(set(failed)), primary_run=core.run if core else None,
                model_class_dependent=class_dependence)


def _csv(path, rows, columns):
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                             for key, value in row.items() if key in columns})


def protocol_metric_rows(metrics, verdicts):
    """Section16.2 schema; absent source counts remain explicitly unavailable.

    These are main-endpoint readouts for each representation. Only the frozen
    R_SIM endpoint is primary. E0 decoding and C linear fallback never become
    the unmeasured E1 transfer gap or the required C MLP endpoint.
    """
    states = {row['route']: row for row in verdicts}
    expected = {'A': 'post_T', 'B': 'calibrated_main_gain',
                'C': 'T_C_mlp32_calibrated', 'D': 'D2_minus_D3'}
    output = []
    for row in metrics:
        route, statistic = row['route'], row['statistic']
        state = states[route]
        primary = (row['mode'] == 'R_SIM' and statistic == expected.get(route)
                   and row['run'] == state.get('primary_run'))
        reader = ('mlp32' if 'mlp32' in statistic else 'linear') if route in 'CE' else {
            'A': 'contrast_match', 'B': 'conditional_logistic', 'D': 'nested_group_ridge'}.get(route)
        output.append(dict(route=route, stage='S4', experiment_id=row['run'],
            preprocessing_id='P2_SPATIAL_SPLIT' if route == 'C' else 'E0_BLOCK_RESET_60S' if route == 'E' else 'P1_CAUSAL20',
            dataset_scope='MFF_same_layout_paired_tasks' if route == 'E' else 'HA_frozen_earliest_index',
            representation_mode=row['mode'], reader_family=reader,
            split_protocol='within_record_independent_filter_blocks' if route == 'E' else 'frozen_identity_group_outer5',
            seed='see_source_fit_scope', outer_fold='pooled_OOF', comparison_id=statistic,
            primary_endpoint=primary, value=row['estimate'], unit=row['units'],
            ci_lower=row['ci_lower'], ci_upper=row['ci_upper'], ci_scope='fixed_OOF_candidate_cluster_bootstrap_2000',
            n_candidate_groups=row['n_candidates'], n_records=None, n_trials=None, coverage_fraction=None,
            control_status=state['control_status'], verdict=state['verdict'],
            limitation_code='exploratory_seen_cohort;record_trial_counts_not_in_source_metric;not_pipeline_refit'))
    return output


def validate_registry(registry):
    if registry.get("version") != "auditory5_screening_sources_v1":
        raise ValueError("SOURCE_REGISTRY_VERSION")
    if registry.get("primary_mode") != "R_SIM" or registry.get("parallel_mode") != "R_SUP":
        raise ValueError("FROZEN_REPRESENTATION_PRIORITY")
    if registry.get("expected_representation_tasks") != 90 or registry.get("expected_outer_folds") != 5:
        raise ValueError("FROZEN_TASK_MATRIX")
    sources = registry["sources"]
    names = [item["run"] for item in sources]
    if len(names) != len(set(names)):
        raise ValueError("DUPLICATE_SOURCE_RUN")
    for source in sources:
        _identifier(source["run"])
        if (source["route"] not in ROUTES or source["kind"] not in {"core", "controls", "descriptive"} or
                not source["modes"] or not set(source["modes"]) <= MODES):
            raise ValueError("SOURCE_REGISTRY_SCHEMA")
    for route in "ABCD":
        for mode in ("L0", "R_SIM", "R_SUP"):
            if sum(s["route"] == route and s["kind"] == "core" and mode in s["modes"] for s in sources) != 1:
                raise ValueError("CORE_REGISTRY_COVERAGE")
        if route in "ABD":
            for mode in ("L0", "R_SIM", "R_SUP"):
                if sum(s["route"] == route and s["kind"] == "controls" and mode in s["modes"] for s in sources) != 1:
                    raise ValueError("CONTROL_REGISTRY_COVERAGE")
    if sum(s["route"] == "E" and s["kind"] == "core" for s in sources) != 1:
        raise ValueError("E_REGISTRY_COVERAGE")
    limits = registry.get("limitations", {})
    if limits.get("E1_bapa_safe_candidates") != 16 or limits.get("E1_min_candidates_each_task") != 20:
        raise ValueError("E1_SUPPORT_DEFINITION")


def control_evidence(sources):
    """Whitelisted aggregate control rows; no automatic recursive summary dump."""
    output = []
    for source in sources:
        if source.kind == "core" and source.route == "A":
            for row in source.summary.get("results", []):
                stats = row.get("statistics", {})
                for name in ("pre", "background", "background_adjusted", "random_projection"):
                    if stats.get(name):
                        output.append(dict(route="A", run=source.run, mode=row["mode"], control=row["analysis"] + ":" + name,
                                           **_ci(stats[name], row["n_candidates"]), units="cosine_difference"))
                post = stats.get("post", {})
                if post.get("paired_estimate") is not None and post.get("paired_ci95") is not None:
                    output.append(dict(route="A", run=source.run, mode=row["mode"], control=row["analysis"] + ":paired_post_minus_pre",
                        **_ci(dict(estimate=post["paired_estimate"], ci95=post["paired_ci95"]), row["n_candidates"]), units="cosine_difference"))
        elif source.kind == "core" and source.route == "B":
            for mode, content in source.summary.get("representations", {"L0": source.summary}).items():
                for row in content.get("comparisons", []):
                    output.append(dict(route="B", run=source.run, mode=mode,
                        control=row["analysis_set"] + ":" + row["probability_mode"] + ":" + row["comparison"], **_ci(row), units="bits/trial"))
        elif source.kind == "controls" and source.route == "A":
            for name, row in source.summary.get("aggregates", {}).items():
                if row.get("status") == "PASS":
                    effect = (dict(estimate=row["paired_estimate"], ci95=row["paired_ci95"])
                              if row.get("paired_direction") else row)
                    output.append(dict(route="A", run=source.run, mode=name.split(":")[0], control=name.split(":")[-1],
                                       **_ci(effect, row.get("total_candidates")), units="cosine_difference"))
        elif source.kind == "controls" and source.route == "B":
            for mode, content in source.summary.get("modes", {}).items():
                for row in content.get("comparisons", []):
                    output.append(dict(route="B", run=source.run, mode=mode,
                        control=row["analysis_set"] + ":" + row["probability_mode"] + ":" + row["comparison"], **_ci(row), units="bits/trial"))
                for row in content.get("circular_shift", []):
                    output.append(dict(route="B", run=source.run, mode=mode, control="circular_shift:" + row["probability_mode"],
                                       **_ci(row), units="bits/trial"))
        elif source.kind == "controls" and source.route == "D":
            for row in source.files.get("clinical_sensitivities.csv", []):
                output.append(dict(route="D", run=source.run, mode=row["mode"],
                    control=row["variant"] + ":" + row["comparison"] + ":" + row.get("model", ""),
                    **_ci(row), units="MUSS_source_points"))
            for row in source.files.get("null_stimulus_probe.json", []):
                output.append(dict(route="D", run=source.run, mode=row["mode"],
                    control="new_null_linear_probe_J:" + row["probability_mode"], **_ci(row["J_bits"]), units="bits/trial"))
        elif source.route == "C":
            for row in source.files.get("capacity_controls.csv", []):
                output.append(dict(route="C", run=source.run, mode=row["representation"],
                    control=row["family"] + ":" + row["probability_mode"] + ":" + row["statistic"],
                    **_ci(row), units="bits/trial"))
    return output


QUESTIONS = {
    "A": ("刺激差值表征的同候选跨时间块匹配是否超过异候选匹配。", "背景、刺激前、随机投影、配对时序与训练内白化可解释重复性。",
          "共享滤波历史、序列位置及一般个体状态仍需重置/平衡敏感性约束。", "终点是固定表征的候选级重复性，不复用旧波形相关作为临床证据。"),
    "B": ("在当前及前一个字面码均为 1 时，历史 run-length 对当前反应是否仍有条件预测增量。",
          "强 gap/position 上下文、刺激前和前次反应均使用同试次对照。", "残余历史、适应、质量和序列混杂不能解释为因果信息传递。",
          "估计固定 OOF 条件 CE 增益，不以已有负结果重新选择历史或窗口。"),
    "C": ("独立预处理及编码的左右分支联合读出是否优于任一单分支。", "LL/RR、扩展单分支容量及温度校准约束模型容量解释。",
          "固定头置零与替换是分布外诊断；预测互补性不等于 PID synergy。", "左右原始输入隔离，不能从全头表示事后切片宣称独立视角。"),
    "D": ("刺激固定线性头的 null 空间是否在临床协变量及 visible 之外降低 MUSS 源分 MAE。",
          "临床单独、完整特征、刺激前、随机投影与试次数/QC 敏感性保持原终点。", "固定头不变性只说明该头几何；新 null 读出可能恢复刺激信息。",
          "outer 和 inner encoder 均独立拟合；不以旧临床阴性结果后的新终点替换主 MAE。"),
    "E": ("E0 描述记录内独立时间块的任务可读性；E1 才检验纯音到 bapa 迁移。", "E0 的 linear 与 MLP32 分族核对完整记录，失败族不在成功子集聚合。",
          "任务、布局及来源设备差异仍可能解释迁移；E0 不估计迁移信息瓶颈。", "MFF 包含混合及未知来源，不能整体称 CI；现有 E1 bapa 16 候选不足 20。"),
}


def _fmt(value):
    return "未完成/不可用" if value is None else f"{value:.6g}" if isinstance(value, (float, int)) else str(value)


def _table(metrics):
    lines = ["| mode | statistic | estimate [95% CI] | n candidates | units | run |",
             "|---|---|---|---:|---|---|"]
    for row in metrics:
        lines.append(f"| {row['mode']} | {row['statistic']} | {_fmt(row['estimate'])} [{_fmt(row['ci_lower'])}, {_fmt(row['ci_upper'])}] | {row['n_candidates']} | {row['units']} | {row['run']} |")
    if not metrics:
        lines.append("| 未完成 | 无可用估计 | 不以 0 代替 | — | — | — |")
    return "\n".join(lines)


def write_reports(directory, summary, verdicts, metrics, baselines, sources, registry):
    lines = ["# 五条思路第一轮筛查报告", "", f"执行状态：**{summary['status']}**；表征状态：**{summary['S3']['status']}**（{summary['S3']['completed']}/90）。",
             "", "本文件是 S4 聚合记录。报告已生成、作业提交、合成契约通过和科学实验完成是不同状态。任何路线失败或未完成均保留；没有宣称五路线全部科学完成。",
             "", "主表征固定为 R_SIM，R_SUP 为平行分析，L0 与随机表示为基线。不同路线的效应单位不同，不构造跨路线总分。",
             "", "| 路线 | 主终点 | verdict | 控制 | 样本支持 | 科学完成 |", "|---|---|---|---|---|---|"]
    for row in verdicts:
        lines.append(f"| {row['route']} | {row['primary_endpoint']} | {row['verdict']} | {row['control_status']} | {row['support_status']} | {row['scientific_complete']} |")
    lines += ["", "所有区间直接继承各来源的候选等权、固定 OOF 2000 次 cluster bootstrap；不是 pipeline-refit 区间。负 J / 负增益原样保留。", ""]
    for row in verdicts:
        route = row["route"]
        text = [f"# 路线 {route}", "", f"判定：**{row['verdict']}**。主表征：{row['primary_mode']}。", "",
                _table([m for m in metrics if m["route"] == route]), ""]
        if row.get("model_class_dependent") is not None:
            text += [f"按完整 calibrated 对照矩阵比较 linear 与 MLP32，模型类依赖：{row['model_class_dependent']}。", ""]
        for title, answer in zip(("现象与 estimand", "基线解释", "剩余替代解释", "与旧工作区别"), QUESTIONS[route]):
            text += [f"{title}：{answer}", ""]
        text += ["下一有限步骤：完成列出的预设控制与失败复核；只有完整支持的首轮筛查才考虑预设种子复现。独立儿童验证仍未完成。", "",
                 "待完成：" + ("；".join(row["pending"]) or "无列出的输入缺项"), "",
                 "失败保留：" + ("；".join(row["failures"]) or "无记录到的实现失败"), "",
                 "来源：" + "、".join(s.run for s in sources if s.route == route), ""]
        if route == "E":
            for source in sources:
                if source.route == "E" and source.summary:
                    text += [f"E0 请求记录 {source.summary.get('records_requested', '未知')}；具有块支持 {source.summary.get('records_with_block_support', '未知')}；两族均成功记录 {source.summary.get('records_decoded', '未知')}。",
                             "族状态：" + json.dumps(source.summary.get("family_status", {}), ensure_ascii=False) + "；数值失败 record-head 数：" + str(source.summary.get("numerical_failure_record_heads", "未知")) + "。", ""]
        if route == "A" and summary.get("A_balance_support"):
            support = summary["A_balance_support"]
            text += [f"固定六格历史×位置平衡支持：{support['candidate_groups']} 候选中，满足所有 24 个 half/class/cell 固定配额的候选为 {support['candidates_with_all_24_cells_at_fixed_quota']}。",
                     "该序列支持限制不是代码失败，不调小配额补成阳性。字面码 2 的 H0 单元几乎结构为空；各半份/位置单元的零计数见 history_position_support.csv。有效的独立 reset 项仍单独保留。", ""]
        (directory / f"{route}_screening_report.md").write_text("\n".join(text), encoding="utf-8")
        lines += [f"## 路线 {route}", "", "\n".join(text[2:]), ""]
    lines += ["## 共享刺激读出", "", "以下数字来自显式 execution run 的已汇总 OOF 表；这里没有重新拟合或重新 bootstrap。略高的 bAcc 不保证正的 J=1−CE_bits；过度自信的错误可以使 J 为负。", "",
              "| mode | bAcc | AUROC | calibrated CE bits | J bits [95% CI] | n candidates |", "|---|---:|---:|---:|---|---:|"]
    for row in baselines:
        if (row["branch"], row["window"], row["probability"]) == ("all", "post", "calibrated"):
            lines.append(f"| {row['mode']} | {_fmt(row['bacc'])} | {_fmt(row['auroc'])} | {_fmt(row['ce_bits'])} | {_fmt(row['J_bits'])} [{_fmt(row['J_ci_lower'])}, {_fmt(row['J_ci_upper'])}] | {row['n_candidates']} |")
    if not baselines:
        lines.append("| 未完成 | — | — | — | 不替换为 0 | — |")
    lines += ["", "## 已看数据和范围限制", "",
        "Phase 0–3 与已完成 A/B/D 阴性或弱结果均保留。原有 53 候选及当前开发队列不是未经查看的独立验证集。HA 数字码不自动命名标准/偏差音；设备开关、精确声学起点、临床量表与 EEG 同期性仍有未知。元数据 addendum 的少量设备史线索不等同于精确 EEG 状态。",
        "", "MFF 是混合及未知来源，不能把全部记录称为 CI。E1 bapa 安全候选 16 < 20；E0 记录内时间块分析不替代儿童外推迁移。任何数值失败的族不以仅成功记录的聚合替代。",
        "", "所有失败与取消尝试保留，未覆盖原结果。源版本由 source YAML 明确指定，未搜索最好或最高版本。逐候选误差、预测和临床记录继续留在原 private 产物；本聚合器不发布或复算个人明细。",
        "", "历史尝试：" + "；".join(f"{item['run']} ({item['state']})" for item in registry.get("retained_attempts", [])),
        "", "精确输入与代码 SHA256 见 source_hashes.csv；路径与异常详情仅写 private 审计。补充控制估计见 control_metrics.csv；所有任务/分支/窗口刺激读出见 stimulus_decoding.csv。metrics_aggregate.csv 按方案 §16.2 列出主终点标记；来源指标未提供的记录数、试次数、覆盖比例留空，不能由人数推造。", ""]
    (directory / "FIVE_IDEAS_SCREENING_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def run(run_name, sources_path, *, root=ROOT):
    require_slurm()
    root, name = Path(root).resolve(), _identifier(run_name)
    sources_path = Path(sources_path)
    sources_path = sources_path if sources_path.is_absolute() else root / sources_path
    registry = yaml.safe_load(sources_path.read_text(encoding="utf-8"))
    validate_registry(registry)
    config_path = root / registry["project_config"]
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if config["project"]["overwrite"] or config["project"]["publish_individual_data"]:
        raise ValueError("RESTRICTED_IMMUTABLE_OUTPUT_REQUIRED")
    private_root = (root / config["paths"]["private_relative"]).resolve()
    if not private_root.is_relative_to(root / "private"):
        raise ValueError("PRIVATE_OUTPUT_REQUIRED")
    public_root = (root / config["paths"]["aggregates_relative"]).resolve()
    reports_root = (root / config["paths"]["reports_relative"]).resolve()
    if not public_root.is_relative_to(root / "results") or not reports_root.is_relative_to(root / "reports"):
        raise ValueError("OUTPUT_ROOT_CONTRACT")
    destination, public, reports = private_root / "screening" / name, public_root / name, reports_root / name
    for path in (destination, public, reports):
        if path.exists():
            raise FileExistsError("SCREENING_RUN_ALREADY_EXISTS")
    destination.mkdir(parents=True, mode=0o700)
    public.mkdir(parents=True)
    reports.mkdir(parents=True)
    audit, global_pending, global_failures = [], [], []
    for path, label in ((sources_path, "screening_sources.yaml"), (config_path, "project_config.yaml"),
                        (root / registry["protocol"], "protocol.md"), (Path(__file__), "screening.py")):
        if _artifact(path, label, audit) is None:
            global_pending.append(label)
    for attempt in registry.get("retained_attempts", []):
        retained = _identifier(attempt["run"])
        for filename in ("summary.json", "failure.json"):
            try:
                _artifact(public_root / retained / filename, "retained/" + retained + "/" + filename, audit)
            except (ValueError, TypeError, KeyError, OSError) as exc:
                audit.append(dict(label="retained/" + retained, status="ERROR", detail=repr(exc)))
    (destination / "sources.yaml").write_text(sources_path.read_text(encoding="utf-8"), encoding="utf-8")
    plan_path, plan = root / registry["plan"], None
    try:
        plan = _artifact(plan_path, "representation_plan.json", audit)
        split = _artifact(root / registry["split"], "split_folds.json", audit)
        if plan is None or split is None:
            s3 = dict(status="IN_PROGRESS", completed=0, expected=90)
            global_pending.append("representation_plan_or_split")
        else:
            plan_hash = digest(plan_path)
            if plan.get("config_hash") != object_hash(config) or plan.get("split_hash") != digest(root / registry["split"]):
                raise ValueError("PLAN_CONFIG_SPLIT_HASH_MISMATCH")
            s3 = representation_status(plan, plan_hash, plan_path, audit)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        s3 = dict(status="IMPLEMENTATION_FAIL", completed=0, expected=90)
        global_failures.append("representation_contract")
        audit.append(dict(label="representation_contract", status="ERROR", detail=repr(exc)))
    sources = [read_source(spec, public_root, audit) for spec in registry["sources"]]
    metrics, controls = [], []
    for source in sources:
        try:
            if source.summary.get("plan_hash") is not None and (plan is None or source.summary["plan_hash"] != digest(plan_path)):
                raise ValueError("ROUTE_PLAN_HASH_MISMATCH")
            current = extract_metrics(source)
            # Every declared core mode must have an estimate. Partial linear C
            # sources remain descriptive and never supply the MLP primary.
            if source.kind == "core" and source.state == "READY":
                for mode in source.modes:
                    if not any(row["mode"] == mode for row in current):
                        source.pending.append(mode + ":core_estimate")
            metrics.extend(current)
            controls.extend(control_evidence([source]))
        except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
            source.state = "FAIL"
            source.errors.append("aggregate_contract")
            audit.append(dict(label=source.run, status="ERROR", detail=repr(exc)))
    write_json(destination / "all_source_metrics.json", metrics)
    metrics, conflicts = resolve_display_metrics(metrics, sources)
    for source in sources:
        if source.run in conflicts:
            source.state = "FAIL"
            source.errors.append("duplicate_source_estimate_conflict")
    if conflicts:
        global_failures.append("duplicate_source_estimate_conflict")
    balance_support, balance_cells = None, []
    balance_columns = ("half", "stimulus_local_id", "history", "position_third", "quota", "candidates",
                       "median_trials", "minimum_trials", "zero_cell_candidates", "below_quota_candidates", "literal_code")
    try:
        support_run = _identifier(registry["A_balance_support_run"])
        support_summary = _artifact(public_root / support_run / "summary.json", support_run + "/summary.json", audit)
        support_table = _artifact(public_root / support_run / "history_position_support.csv", support_run + "/history_position_support.csv", audit)
        if support_summary is None or support_table is None:
            global_pending.append("A_history_position_support_audit")
        else:
            if support_summary.get("status") != "COMPLETE" or support_summary.get("selection_rules_changed") is not False:
                raise ValueError("A_SUPPORT_AUDIT_CONTRACT")
            balance_support = {key: _integer(support_summary[key]) for key in
                               ("candidate_groups", "candidates_with_all_24_cells_at_fixed_quota")}
            balance_support["run"] = support_run
            for row in support_table:
                balance_cells.append({key: _number(row[key]) for key in balance_columns})
            observed = {(row["half"], row["stimulus_local_id"], row["history"], row["position_third"]) for row in balance_cells}
            expected = {(half, stimulus, history, position) for half in range(2) for stimulus in range(2)
                        for history in range(2) for position in range(3)}
            if len(balance_cells) != 24 or observed != expected:
                raise ValueError("A_SUPPORT_CELL_MATRIX")
    except (ValueError, TypeError, KeyError, OSError) as exc:
        global_failures.append("A_history_position_support_audit")
        audit.append(dict(label="A_support", status="ERROR", detail=repr(exc)))
    verdicts = []
    for route in ROUTES:
        try:
            verdicts.append(evaluate_route(route, sources, metrics))
        except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
            audit.append(dict(label="route_" + route, status="ERROR", detail=repr(exc)))
            verdicts.append(dict(route=route, primary_mode="R_SIM" if route != "E" else "E1:puretone_to_bapa",
                primary_endpoint="UNAVAILABLE", verdict="IMPLEMENTATION_FAIL", scientific_complete=False,
                control_status="FAIL", input_status="RECORDED", pending=[], failures=["aggregate_schema"], support_status="UNKNOWN"))
    if balance_support and balance_support["candidates_with_all_24_cells_at_fixed_quota"] < 25:
        row = next(row for row in verdicts if row["route"] == "A")
        row["support_status"] = "SUPPORT_INSUFFICIENT_FOR_HISTORY_POSITION_CONTROL"
        row["scientific_complete"] = False
        row["pending"].append("A:frozen_history_position_balance_support")
        if row["verdict"] != "IMPLEMENTATION_FAIL":
            row["verdict"], row["control_status"] = "NEED_CONTROLS", "PENDING"
    if "A_history_position_support_audit" in global_failures:
        row = next(row for row in verdicts if row["route"] == "A")
        row.update(verdict="IMPLEMENTATION_FAIL", scientific_complete=False, control_status="FAIL")
        row["failures"].append("A_support_audit_schema")
    baseline_columns = ("mode", "branch", "window", "probability", "n_candidates", "trial_count", "ce_bits", "J_bits",
                        "bacc", "auroc", "brier", "auroc_definition", "J_ci_lower", "J_ci_upper")
    baselines = []
    try:
        execution_run = _identifier(registry["execution_run"])
        execution = _artifact(public_root / execution_run / "summary.json", execution_run + "/summary.json", audit)
        table = _artifact(public_root / execution_run / "stimulus_decoding.csv", execution_run + "/stimulus_decoding.csv", audit)
        if execution is None or table is None:
            global_pending.append("execution_summary_or_stimulus_decoding")
        else:
            if plan is None or execution.get("plan_hash") != digest(plan_path):
                raise ValueError("EXECUTION_PLAN_HASH_MISMATCH")
            for row in table:
                normalized = {key: row[key] for key in baseline_columns}
                for key in ("ce_bits", "J_bits", "bacc", "auroc", "brier", "J_ci_lower", "J_ci_upper"):
                    normalized[key] = _number(row[key])
                for key in ("n_candidates", "trial_count"):
                    normalized[key] = _integer(row[key])
                if abs(normalized["J_bits"] - (1 - normalized["ce_bits"])) > 1e-8:
                    raise ValueError("NEGATIVE_INFORMATION_NOT_PRESERVED")
                baselines.append(normalized)
            coordinates = {(row["mode"], row["branch"], row["window"], row["probability"]) for row in baselines}
            expected = {(mode, branch, window, probability) for mode in ("L0", "R_SUP", "R_SIM", "R_RAND")
                        for branch in ("all", "left", "right") for window in ("post", "pre") for probability in ("raw", "calibrated")}
            if len(coordinates) != len(baselines) or not coordinates <= expected:
                raise ValueError("STIMULUS_AGGREGATE_MATRIX")
            if execution.get("completed_representation_tasks") != 90 or len(baselines) != 48:
                global_pending.append("execution_aggregate_not_complete")
    except (ValueError, TypeError, KeyError, OSError) as exc:
        global_failures.append("stimulus_aggregate_contract")
        baselines = []
        audit.append(dict(label="stimulus_aggregate", status="ERROR", detail=repr(exc)))
    # A source that changed after its read cannot support a completion claim.
    for entry in audit[:]:
        if entry.get("sha256"):
            try:
                changed = digest(Path(entry["path"])) != entry["sha256"]
            except OSError:
                changed = True
            if changed:
                global_failures.append("source_changed_after_read")
    if s3["status"] == "IMPLEMENTATION_FAIL" or "source_changed_after_read" in global_failures:
        for row in verdicts:
            row.update(verdict="IMPLEMENTATION_FAIL", scientific_complete=False, control_status="FAIL")
            row["failures"].append("shared_source_or_representation_contract")
    unfinished = (any(s.state == "MISSING" or any(name.endswith((".json", ".csv")) for name in s.pending) for s in sources)
                  or bool(global_pending) or s3["status"] == "IN_PROGRESS")
    failures = any(row["verdict"] == "IMPLEMENTATION_FAIL" for row in verdicts) or bool(global_failures) or s3["status"] == "IMPLEMENTATION_FAIL"
    summary = dict(stage="S4_SCREENING_AGGREGATION", status="IN_PROGRESS" if unfinished else "S4_RECORDED_WITH_FAILURES" if failures else "S4_RECORDED",
                   report_generated=True, S3=s3, all_five_scientific_routes_complete=all(row["scientific_complete"] for row in verdicts),
                   primary_mode="R_SIM", parallel_mode="R_SUP", global_pending=global_pending, global_failures=global_failures,
                   source_registry_sha256=digest(sources_path), fixed_oof_not_pipeline_refit=True,
                   A_balance_support=balance_support, duplicate_source_conflicts=conflicts,
                   verdicts=verdicts, source_states=[dict(route=s.route, run=s.run, kind=s.kind, state=s.state) for s in sources])
    _csv(public / "screen_metrics.csv", metrics, METRIC_COLUMNS)
    _csv(public / "metrics_aggregate.csv", protocol_metric_rows(metrics, verdicts), AGGREGATE_COLUMNS)
    _csv(public / "verdict.csv", verdicts, ("route", "primary_mode", "primary_endpoint", "estimate", "ci_lower", "ci_upper", "n_candidates", "units",
        "primary_run", "verdict", "control_status", "input_status", "support_status", "scientific_complete", "model_class_dependent", "pending", "failures"))
    _csv(public / "control_metrics.csv", controls, ("route", "run", "mode", "control", "estimate", "ci_lower", "ci_upper", "n_candidates", "units"))
    _csv(public / "stimulus_decoding.csv", baselines, baseline_columns)
    _csv(public / "history_position_support.csv", balance_cells, balance_columns)
    _csv(public / "source_hashes.csv", audit, ("label", "status", "sha256", "sha256_after"))
    write_json(destination / "source_audit.json", audit)
    write_json(public / "summary.json", summary)
    write_reports(reports, summary, verdicts, metrics, baselines, sources, registry)
    write_json(destination / "completion.json", dict(status="REPORT_GENERATED", scientific_status=summary["status"],
        output_hashes={p.name: digest(p) for p in public.iterdir() if p.is_file()},
        report_hashes={p.name: digest(p) for p in reports.iterdir() if p.is_file()}))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--sources", default="configs/auditory5_screening_sources_v1.yaml")
    args = parser.parse_args()
    summary = run(args.run, args.sources)
    print(json.dumps({"status": summary["status"], "S3": summary["S3"]["status"], "run": args.run}, ensure_ascii=False))


if __name__ == "__main__":
    main()
