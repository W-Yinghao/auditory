"""K0 runner. Zero EEG, zero model search, zero new data; Slurm only."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

from auditory_fn1a import runtime
from auditory_fn1a.runtime import ROOT, ProvenanceError, load_config, require_config_value, write_json
from auditory_fn1a.signal_export import AMPLITUDE_COLUMN, TECHNICAL_COLUMNS

from . import check


def _load_scope(source_paths: dict, config: dict, support_run: str, target_name: str):
    """Read the FROZEN fn1a artefacts. `source_paths` are the fn1a roots, deliberately
    separate from this run's own k0 output roots."""
    private_root = ROOT / source_paths["private_relative"]
    results_root = ROOT / source_paths["results_relative"]
    support = json.loads((private_root / support_run / "support.json").read_text())
    lock = json.loads((private_root / support["freeze_run"] / "archive_analysis_lock.json").read_text())
    with (private_root / lock["bound_runs"]["prepare"] / "archive_rows.csv").open(newline="", encoding="utf-8") as handle:
        rows = {r["index_record_id"]: r for r in csv.DictReader(handle)}
    with (results_root / support["segments_run"] / "segment_support_summary.csv").open(newline="", encoding="utf-8") as handle:
        technical = {r["index_record_id"]: r for r in csv.DictReader(handle)}

    usable = support["usable"]
    if target_name == "V_archive_given_A":
        usable = [u for u in usable if str(u["target_V_given_A_available"]) == "True"]
    index_of = {u["split_group_id"]: i for i, u in enumerate(usable)}
    folds = []
    for fold in support["splits"]["folds"]:
        folds.append({"outer_fold": fold["outer_fold"],
                      "train_idx": np.array([index_of[g] for g in fold["train"] if g in index_of], dtype=int),
                      "test_idx": np.array([index_of[g] for g in fold["test"] if g in index_of], dtype=int),
                      "inner_train_sizes": [len([g for g in i["train"] if g in index_of]) for i in fold["inner"]]})
    design, target = [], []
    for entry in usable:
        row = rows[entry["index_record_id"]]
        tech = technical[entry["index_record_id"]]
        values = [row["age_recorded_months"], row["HA_duration_months"],
                  row["better_unaided_pta_corrected"], row["better_aided_pta_corrected"]]
        if target_name == "V_archive_given_A":
            values.append(row["A_raw_value"])
            y = row["MUSS_raw_value"]
        else:
            y = row["A_raw_value"]
        clinical = [float(v) if str(v) not in ("", "None") else np.nan for v in values]
        design.append(clinical + [float(tech[f"Q_{c}"]) for c in TECHNICAL_COLUMNS])
        target.append(float(y))
    return np.asarray(design, dtype=float), np.asarray(target, dtype=float), folds


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m auditory_k0.cli")
    parser.add_argument("command", choices=["parity"])
    parser.add_argument("--run", required=True)
    parser.add_argument("--config", default=runtime.CONFIG_DEFAULT)
    parser.add_argument("--support", required=True)
    parser.add_argument("--fit-runs", nargs="+", required=True,
                        help="fn1a fit runs whose outer_selections.json supply the frozen M1 specification")
    args = parser.parse_args(argv)
    config = load_config(args.config)
    # The fn1a roots are the read side; k0 writes to its own namespace.
    source_paths = {"private_relative": config["paths"]["private_relative"],
                    "results_relative": config["paths"]["results_relative"]}
    config["paths"] = dict(config["paths"])
    for key, value in (("private_relative", "private/auditory_k0"), ("results_relative", "results/auditory_k0"),
                       ("reports_relative", "reports/auditory_k0"), ("docs_relative", "docs/auditory_k0")):
        config["paths"][key] = value
    context = runtime.create_run(args.command, args.run, config, args=vars(args))

    results_root = ROOT / "results/auditory_fn1a"
    scopes: list[dict] = []
    shrinkage: dict[str, dict] = {}
    fit_sizes: set[int] = set()
    for fit_run in args.fit_runs:
        summary = json.loads((results_root / fit_run / "summary.json").read_text())
        target_name = summary["target"]
        selections = json.loads((results_root / fit_run / "outer_selections.json").read_text())["selections"]
        specs = {s["outer_fold"]: s["M1"] for s in selections}
        design, target, folds = _load_scope(source_paths, config, args.support, target_name)
        for fold in folds:
            fit_sizes.add(int(fold["train_idx"].size))
            fit_sizes.update(int(s) for s in fold["inner_train_sizes"])
            scopes.append({"target": target_name, "outer_fold": fold["outer_fold"],
                           "scope": "outer_train", "n": int(fold["train_idx"].size),
                           "alpha": float(specs[fold["outer_fold"]]["penalty"]),
                           "alpha_over_n": float(specs[fold["outer_fold"]]["penalty"]) / int(fold["train_idx"].size),
                           "basis": specs[fold["outer_fold"]]["family"],
                           "target_unit": "HA source column 0-100; network trains on 0-1"})
            for inner_index, inner_n in enumerate(fold["inner_train_sizes"]):
                scopes.append({"target": target_name, "outer_fold": fold["outer_fold"],
                               "scope": f"inner_train[{inner_index}]", "n": int(inner_n),
                               "alpha": float(specs[fold["outer_fold"]]["penalty"]),
                               "alpha_over_n": float(specs[fold["outer_fold"]]["penalty"]) / int(inner_n),
                               "basis": specs[fold["outer_fold"]]["family"],
                               "target_unit": "HA source column 0-100; network trains on 0-1"})
        bounds = tuple(float(x) for x in require_config_value(config, "archive.target_bounds_source_units"))
        shrinkage[target_name] = check.clinical_shrinkage(design, target, folds, specs, bounds)

    parity = check.parity_suite(sorted(fit_sizes))
    status = ("OBJECTIVE_SCALE_DEFECT_CONFIRMED"
              if (parity["implementation_is_sse_form"] and parity["sse_equals_mse_over_n"]
                  and parity["mse_plain_equals_sse_with_n_alpha"] and parity["sse_differs_from_mse_plain"])
              else "OBJECTIVE_PARITY_INCONCLUSIVE")
    write_json(context["public"] / "objective_parity.json",
               {k: v for k, v in parity.items() if k != "rows"} | {"status": status}, private=False)
    write_json(context["private"] / "objective_parity_rows.json", {"rows": parity["rows"]}, private=True)
    write_json(context["public"] / "clinical_shrinkage.json", shrinkage, private=False)
    with (context["public"] / "fit_scope_penalties.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["target", "outer_fold", "scope", "n", "alpha",
                                                    "alpha_over_n", "basis", "target_unit"])
        writer.writeheader()
        for row in scopes:
            writer.writerow(row)
    (context["public"] / "fit_scope_penalties.csv").chmod(0o644)
    receipt = runtime.finish(context, {
        "status": status, "parity_cases": parity["cases"],
        "fit_sizes_covered": sorted(fit_sizes), "penalties_covered": list(check.PENALTIES),
        "targets": sorted(shrinkage), "real_eeg_read": False, "neural_fits": 0,
        "note": ("K0 confirms or refutes a scale identity. It does not establish that a corrected "
                 "objective would produce a usable EEG increment."),
    })
    print(json.dumps({"k0": args.command, "run": args.run, "status": receipt["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
