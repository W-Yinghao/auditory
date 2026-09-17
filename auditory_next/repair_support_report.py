"""JSON-only E0 repair flow: no fitting, predictions or success-subset scores.

Record-level optimization support is distinct from full-family scoring permission.
Legacy ``records_decoded`` describes the old MLP and is deliberately unused.
"""
from collections import Counter
from copy import deepcopy
from math import isfinite
from pathlib import Path

LEGACY, REPAIR = "E0_native_003", "E0R_core_001"
STABLE, UNRESOLVED = "OPTIMIZATION_STABLE", "OPTIMIZATION_UNRESOLVED"
MEMBER_KEYS = set("key case family view width part alpha".split())


def _require(condition, code):
    if not condition:
        raise ValueError("REPAIR_SUPPORT_" + code)


def _index(rows, count, required):
    _require(isinstance(rows, list) and len(rows) == count, "ROW_COUNT")
    _require(all(isinstance(r, dict) and required <= r.keys() and
                 isinstance(r["key"], str) and r["key"] for r in rows), "KEYS")
    result = {r["key"]: r for r in rows}
    _require(len(result) == count, "DUPLICATE_KEY")
    return result


def summarize_repair_support(legacy, members, diagnostics, cases, completion):
    """Validate frozen receipts and return aggregate-only, detached JSON data."""
    _require(legacy["records_requested"] == 18 and legacy["records_with_block_support"] == 16
             and legacy["family_status"]["linear"] == "COMPLETE", "LEGACY_SUPPORT")
    rows = legacy["results"]
    row_keys = set("family calibration task complete_pairs mean_CE_bits J_bits_interval".split())
    interval_keys = set("estimate ci_lower ci_upper n_candidates n_bootstrap seed effect gain_definition valid".split())
    _require(len(rows) == 4 and all(set(r) == row_keys for r in rows), "LEGACY_ROWS")
    _require({(r["calibration"], r["task"]) for r in rows} ==
             {(c, t) for c in ("raw", "calibrated") for t in ("puretone", "bapa")}, "LEGACY_GRID")
    for row in rows:
        interval = row["J_bits_interval"]
        _require(row["family"] == "linear" and row["complete_pairs"] == 7 and set(interval) == interval_keys
                 and interval["n_candidates"] == 7 and interval["valid"] is True, "LEGACY_INTERVAL")
        _require(interval["n_bootstrap"] == 2000 and interval["seed"] == 20260917 and
                 interval["effect"] == "baseline_minus_augmented" and interval["gain_definition"] == "baseline - augmented", "LEGACY_SCOPE")
        _require(all(isfinite(v) for v in (row["mean_CE_bits"], interval["estimate"],
                 interval["ci_lower"], interval["ci_upper"])) and
                 interval["ci_lower"] <= interval["ci_upper"], "LEGACY_NUMBERS")
    case_map = _index(cases, 64, set("key record_id fold kind specs".split()))
    record_cases = Counter(c["record_id"] for c in cases)
    _require(len(record_cases) == 16 and set(record_cases.values()) == {4}, "RECORD_COUNT")
    for record in record_cases:
        own = [c for c in cases if c["record_id"] == record]
        _require({c["fold"] for c in own} == {0, 1, 2, 3} and all(c["kind"] == "E0_R"
                 and c["specs"] == [["MLP32", "native", 32]] for c in own), "CASE_GRID")
    manifest = _index(members, 1024, MEMBER_KEYS)
    _require(all(set(m) == MEMBER_KEYS and m["case"] in case_map and
             (m["family"], m["view"], m["width"]) == ("MLP32", "native", 32) for m in members), "MEMBERS")
    grid = {(p, a) for p in ("inner0", "inner1", "inner2", "final") for a in (.01, .1, 1., 10.)}
    for key in case_map:
        own = [m for m in members if m["case"] == key]
        _require(len(own) == 16 and {(m["part"], m["alpha"]) for m in own} == grid, "HEAD_GRID")
    budget = diagnostics["budget"]
    _require(budget in (1000, 2000), "BUDGET")
    for phase, steps in (("initial", 1000), ("final", budget)):
        indexed = _index(diagnostics[phase], 1024, MEMBER_KEYS | {"status", "steps", "attempted_budget"})
        _require(indexed.keys() == manifest.keys(), "DIAGNOSTIC_KEYS")
        for key, d in indexed.items():
            _require(all(d[k] == manifest[key][k] for k in MEMBER_KEYS) and d["status"] in (STABLE, UNRESOLVED)
                     and d["attempted_budget"] == steps and 0 <= d["steps"] <= steps and
                     (d["status"] != STABLE or d["steps"] == steps), "DIAGNOSTIC_MEMBER")
    _require(budget == (1000 if all(d["status"] == STABLE for d in diagnostics["initial"]) else 2000), "BARRIER")
    stable = Counter(case_map[d["case"]]["record_id"] for d in diagnostics["final"] if d["status"] == STABLE)
    n_stable, passed = sum(stable.values()), sum(stable.values()) == 1024
    status = STABLE if passed else "INCOMPLETE_PRIMARY_MATRIX"
    extended = 1024 if budget == 2000 else 0
    _require(diagnostics["status"] == status and diagnostics["neural_fits"] == 1024 and
             diagnostics["continuation_fits"] == 0 and diagnostics["extended_members"] == extended, "FAMILY")
    expected = dict(stage="E0_R", implementation_status="PASS", final_alpha_fits_including_unselected=True,
                    optimization_status=status, required_members=1024, stable_members=n_stable,
                    new_neural_head_fits=1024, new_linear_head_fits=0, new_encoder_fits=0,
                    selected_budget=budget, extended_members=extended,
                    status="COMPLETE_REPAIRED_CORE" if passed else status,
                    core_status="COMPLETE_REPAIRED_MATRIX" if passed else status)
    _require(all(completion[k] == v for k, v in expected.items()), "COMPLETION")
    if not passed:
        _require(completion["test_predictions_generated"] is False and
                 completion["incomplete_family_aggregates_withheld"] is True and completion["results"] == [], "WITHHELD")
    return dict(source_run=REPAIR, optimization_status=status, records_requested=18, records_with_block_support=16,
                required_cases=64, required_heads_per_record=64, required_heads=1024, selected_budget=budget,
                stable_heads=n_stable, unresolved_heads=1024 - n_stable, mlp_family_passed=passed,
                mlp_records_all_required_heads_stable=sum(stable[r] == 64 for r in record_cases),
                mlp_records_available_for_primary_aggregation=16 if passed else 0,
                legacy_linear_records_complete=16, legacy_linear_complete_pairs=7,
                legacy_linear_source_run=LEGACY, legacy_linear_family_status="COMPLETE", new_fits=0,
                legacy_linear_results=[dict(deepcopy(r), source_run=LEGACY) for r in rows])


def read_repair_support(root, reader):
    """Read only fixed JSON sources via reader.read(path, logical_alias)."""
    root = Path(root)
    repair = root / "private/auditory_next_v2" / REPAIR
    legacy = reader.read(root / "results/auditory5_v1" / LEGACY / "summary.json", "e0_support/legacy_summary")
    files = sorted((repair / "cases").glob("*/case.json"))
    _require(len(files) == 64, "CASE_FILES")
    cases = [reader.read(p, f"e0_support/case_{i:03d}") for i, p in enumerate(files)]
    _require(all(c["key"] == p.parent.name for c, p in zip(cases, files)), "CASE_FILE_KEY")
    data = [reader.read(repair / name, "e0_support/" + name) for name in
            ("member_manifest.json", "family_training_diagnostics.json", "completion.json")]
    return summarize_repair_support(legacy, data[0], data[1], cases, data[2])
