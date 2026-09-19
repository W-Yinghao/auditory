"""FN1-A command line. Plan section 13.

`fit` checks the archive manifest, target values, identity isolation, real signal,
window/training support, tests, budget and snapshot. It does NOT check whether a
clinician replied, whether all questionnaire dates exist, or whether every scale
version is confirmed.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from . import archive, runtime
from .runtime import ROOT, ProvenanceError, load_config, require_config_value, write_json, write_text

COMMANDS = ("prepare_archive", "test", "freeze_archive", "export_segments", "freeze_support", "fit", "report")


def _write_table(path: Path, rows: list[dict], columns: list[str], *, private: bool) -> None:
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    path.chmod(0o600 if private else 0o644)


def command_prepare_archive(context: dict, config: dict, args) -> dict:
    cohort = archive.build_cohort(config)
    private, public = context["private"], context["public"]

    # Full per-row analysis table stays private: it carries the worksheet row, the link
    # key, the acquisition time and the per-child scores.
    _write_table(private / "archive_rows.csv", cohort["rows"], list(archive.ANALYSIS_TABLE_COLUMNS), private=True)

    # Public cohort flow: counts and reasons only.
    flow_rows = [{"stage": k, "count": v} for k, v in cohort["flow"].items()]
    _write_table(public / "cohort_flow.csv", flow_rows, ["stage", "count"], private=False)
    reasons: dict[str, int] = {}
    for row in cohort["rows"]:
        for reason in filter(None, row["exclusion_reason"].split(";")):
            reasons[reason] = reasons.get(reason, 0) + 1
    write_json(public / "exclusion_reasons.json", {"blocking_reasons_applied": reasons,
                                                   "blocking_reason_vocabulary": sorted(archive.BLOCKING_REASONS),
                                                   "note": "plain metadata unknowns are not in this vocabulary and never block"},
               private=False)
    write_json(public / "archive_limitations.json", {"limitations": cohort["limitations"]}, private=False)
    write_json(public / "pta_row_key_guard.json", cohort["pta_row_key_guard"], private=False)
    write_json(public / "source_hashes.json", cohort["source_hashes"], private=False)

    missing_locator = [r["index_record_id"] for r in cohort["eligible"] if not str(r.get("signal_file_id", "")).strip()]
    if missing_locator:
        raise ProvenanceError(f"ELIGIBLE_RECORD_WITHOUT_SIGNAL_LOCATOR:{len(missing_locator)}")
    status = "ARCHIVE_PREPARED" if cohort["flow"]["eligible_for_A"] else "TARGET_DATA_INSUFFICIENT"
    return runtime.finish(context, {
        "status": status,
        "flow": cohort["flow"],
        "blocking_reasons_applied": reasons,
        "external_contact_required": False,
        "real_eeg_read": False,
        "neural_fits": 0,
    })


def command_test(context: dict, config: dict, args) -> dict:
    from . import synthetic

    ledger = runtime.FitLedger(context["private"], config)
    synthetic_config = require_config_value(config, "synthetic")
    model_config = require_config_value(config, "models")
    planned = len(synthetic_config["mechanisms"]) * len(synthetic_config["seeds"]) * 2
    for index in range(planned):
        ledger.reserve("neural", {"stage": "synthetic", "index": index})
        ledger.reserve("linear", {"stage": "synthetic_reference", "index": index})
    result = synthetic.run_suite(synthetic_config, model_config,
                                 int(require_config_value(config, "signal.feature_dim")))
    if result["total_neural_fits"] != planned:
        raise ProvenanceError(f"SYNTHETIC_FIT_COUNT_MISMATCH:{result['total_neural_fits']}!={planned}")
    write_json(context["public"] / "implementation_tests.json",
               {k: v for k, v in result.items() if k != "rows"}, private=False)
    write_json(context["private"] / "implementation_rows.json", {"rows": result["rows"]}, private=True)
    return runtime.finish(context, {"status": result["status"], "neural_fits": result["total_neural_fits"],
                                    "fit_ledger": ledger.counts(), "real_eeg_read": False})


def command_freeze_archive(context: dict, config: dict, args) -> dict:
    if not args.prepare or not args.tests:
        raise ProvenanceError("FREEZE_ARCHIVE_REQUIRES_PREPARE_AND_TESTS_RUNS")
    results = ROOT / require_config_value(config, "paths.results_relative")
    prepare_summary = json.loads((results / args.prepare / "summary.json").read_text())
    tests_summary = json.loads((results / args.tests / "summary.json").read_text())
    if prepare_summary.get("status") != "ARCHIVE_PREPARED":
        raise ProvenanceError(f"PREPARE_NOT_USABLE:{prepare_summary.get('status')}")
    cohort = archive.build_cohort(config)
    manifest = f"{require_config_value(config, 'paths.private_relative')}/{args.prepare}/archive_rows.csv"
    lock = archive.analysis_lock(config, cohort, cohort_manifest=manifest,
                                 identity_registry=require_config_value(config, "sources.frozen_index_cohort"))
    lock["bound_runs"] = {"prepare": args.prepare, "tests": args.tests,
                          "tests_status": tests_summary.get("status")}
    write_json(context["private"] / "archive_analysis_lock.json", lock, private=True)
    write_json(context["public"] / "archive_analysis_lock_summary.json", {
        "analysis_lock": {k: v for k, v in lock["analysis_lock"].items() if k != "cohort_manifest"},
        "cohort_manifest": "private (per-row archive table)",
        "bound_runs": lock["bound_runs"],
        "note": lock["note"],
    }, private=False)
    return runtime.finish(context, {"status": "ARCHIVE_ANALYSIS_LOCKED",
                                    "identity_groups_eligible": cohort["flow"]["identity_groups_eligible"],
                                    "tests_status": tests_summary.get("status"),
                                    "external_contact_required": False, "neural_fits": 0})


def command_export_segments(context: dict, config: dict, args) -> dict:
    """Read real continuous HA BDF and emit the frozen 32x140 package per record.

    This is the first command in the round that opens real EEG. It fits nothing.
    """
    import numpy as np

    from . import signal_export

    results = ROOT / require_config_value(config, "paths.results_relative")
    private_root = ROOT / require_config_value(config, "paths.private_relative")
    if not args.freeze:
        raise ProvenanceError("EXPORT_REQUIRES_FREEZE_RUN")
    lock = json.loads((private_root / args.freeze / "archive_analysis_lock.json").read_text())
    if lock["analysis_lock"]["status"] != "LOCKED_FROM_EXISTING_ARCHIVE":
        raise ProvenanceError(f"ARCHIVE_LOCK_NOT_USABLE:{lock['analysis_lock']['status']}")
    prepare_run = lock["bound_runs"]["prepare"]
    with (private_root / prepare_run / "archive_rows.csv").open(newline="", encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if not r["exclusion_reason"]]
    if args.probe:
        rows = rows[: int(args.probe)]

    path_map = signal_export._path_map(config)
    guard = float(require_config_value(config, "signal.guard_seconds_min"))
    package_dir = context["private"] / "packages"
    package_dir.mkdir(mode=0o700, exist_ok=False)

    summaries: list[dict] = []
    for row in rows:
        file_id = row.get("signal_file_id") or ""
        if not file_id or file_id not in path_map:
            summaries.append({"split_group_id": row["split_group_id"], "index_record_id": row["index_record_id"],
                              "status": "no_signal_source", "n_candidate_windows": 0,
                              "n_qualified_windows": 0, "n_selected": 0})
            continue
        signal_path = Path(path_map[file_id])
        stream = signal_export.stream_record(signal_path, expected_fs=None, guard_seconds=guard)
        selection = signal_export.qualify_and_select(stream, config)
        entry = {
            "split_group_id": row["split_group_id"], "index_record_id": row["index_record_id"],
            "original_fs": stream["original_fs"], "processed_fs": stream["processed_fs"],
            "decimation_factor": stream["decimation_factor"],
            "filter_support_seconds": stream["support_seconds"], "guard_seconds": stream["guard_seconds"],
            "source_duration_s": stream["n_samples_original"] / stream["original_fs"],
            "n_candidate_windows": selection["n_candidate_windows"],
            "n_qualified_windows": selection["n_qualified_windows"],
            "n_selected": selection["n_selected"],
            "reject_reason_counts": json.dumps(selection["reject_reason_counts"], sort_keys=True),
            "interval_source": selection["interval_source"],
            "status": "exported" if selection["sufficient"] else "signal_support_insufficient",
        }
        if selection["sufficient"]:
            features, truncated = signal_export.features_for(stream, selection, config)
            technical = signal_export.technical_summary(stream, selection)
            entry.update({f"Q_{k}": v for k, v in technical.items()})
            entry.update(truncated)
            np.savez_compressed(
                package_dir / f"{row['index_record_id']}.npz",
                features=features.astype(np.float64),
                window_start_processed=np.asarray([a for a, _ in selection["selected"]], dtype=np.int64),
                window_start_original=np.asarray([int(stream["source_samples"][a]) for a, _ in selection["selected"]], dtype=np.int64),
                channels=np.asarray(stream["channels"]),
                processed_fs=np.asarray(stream["processed_fs"]),
            )
            (package_dir / f"{row['index_record_id']}.npz").chmod(0o600)
        summaries.append(entry)
        del stream

    columns = sorted({k for s in summaries for k in s})
    _write_table(context["public"] / "segment_support_summary.csv", summaries, columns, private=False)
    exported = sum(1 for s in summaries if s.get("status") == "exported")
    status = "SEGMENTS_EXPORTED" if exported else "CONTINUOUS_SIGNAL_SUPPORT_LIMITED"
    return runtime.finish(context, {
        "status": status, "records_considered": len(rows), "records_exported": exported,
        "records_signal_support_insufficient": sum(1 for s in summaries if s.get("status") == "signal_support_insufficient"),
        "probe_limit": args.probe, "freeze_run": args.freeze, "real_eeg_read": True, "neural_fits": 0,
    })



def _load_archive_rows(config: dict, freeze_run: str) -> tuple[list[dict], dict]:
    private_root = ROOT / require_config_value(config, "paths.private_relative")
    lock = json.loads((private_root / freeze_run / "archive_analysis_lock.json").read_text())
    prepare_run = lock["bound_runs"]["prepare"]
    with (private_root / prepare_run / "archive_rows.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return rows, lock


def command_freeze_support(context: dict, config: dict, args) -> dict:
    """Fix the analysable identities and the outer/inner folds before any outcome model."""
    from auditory_fn1.splits import SupportError, fingerprint, make_splits

    if not (args.freeze and args.segments):
        raise ProvenanceError("FREEZE_SUPPORT_REQUIRES_FREEZE_AND_SEGMENTS_RUNS")
    results = ROOT / require_config_value(config, "paths.results_relative")
    rows, lock = _load_archive_rows(config, args.freeze)
    with (results / args.segments / "segment_support_summary.csv").open(newline="", encoding="utf-8") as handle:
        exported = {r["index_record_id"]: r for r in csv.DictReader(handle)}

    by_record = {r["index_record_id"]: r for r in rows}
    usable, dropped = [], []
    for record_id, entry in exported.items():
        row = by_record.get(record_id)
        if row is None:
            dropped.append({"index_record_id": record_id, "reason": "not_in_archive_manifest"})
            continue
        if entry.get("status") != "exported":
            dropped.append({"index_record_id": record_id, "reason": entry.get("status", "unknown")})
            continue
        if row["exclusion_reason"]:
            dropped.append({"index_record_id": record_id, "reason": row["exclusion_reason"]})
            continue
        usable.append({"split_group_id": row["split_group_id"], "index_record_id": record_id,
                       "target_A_available": row["target_A_available"],
                       "target_V_given_A_available": row["target_V_given_A_available"]})

    identities = [u["split_group_id"] for u in usable]
    minimums = {k: int(require_config_value(config, f"validation.{k}")) for k in
                ("min_total_groups", "min_outer_train_groups", "min_inner_train_groups", "min_outer_test_groups")}
    try:
        spec = make_splits(identities, outer_folds=int(require_config_value(config, "validation.outer_folds")),
                           inner_folds=int(require_config_value(config, "validation.inner_folds")),
                           seed=int(require_config_value(config, "validation.split_seed")), minimums=minimums)
    except SupportError as error:
        write_json(context["public"] / "support_stop.json",
                   {"status": "DESIGN_SUPPORT_INSUFFICIENT", "reason": str(error),
                    "analysable_identities": len(identities)}, private=False)
        return runtime.finish(context, {"status": "DESIGN_SUPPORT_INSUFFICIENT", "reason": str(error),
                                        "analysable_identities": len(identities), "neural_fits": 0})

    secondary = [u["split_group_id"] for u in usable if str(u["target_V_given_A_available"]) == "True"]
    write_json(context["private"] / "support.json",
               {"usable": usable, "splits": spec, "segments_run": args.segments,
                "freeze_run": args.freeze, "secondary_identities": secondary}, private=True)
    write_json(context["public"] / "support_summary.json", {
        "analysable_identities": len(identities),
        "secondary_identities": len(secondary),
        "dropped": dropped,
        "outer_fold_sizes": [len(f["test"]) for f in spec["folds"]],
        "inner_train_sizes": [[len(i["train"]) for i in f["inner"]] for f in spec["folds"]],
        "split_fingerprint": fingerprint(spec),
        "minimums": minimums,
        "note": "Support is design executability, not a clinical power statement.",
    }, private=False)
    return runtime.finish(context, {"status": "SUPPORT_FROZEN", "analysable_identities": len(identities),
                                    "secondary_identities": len(secondary), "neural_fits": 0})


def command_fit(context: dict, config: dict, args) -> dict:
    """Run the full prescribed M0-M4 matrix plus both mandated controls for one target."""
    import numpy as np

    from . import fitting

    if not (args.support and args.target):
        raise ProvenanceError("FIT_REQUIRES_SUPPORT_RUN_AND_TARGET")
    private_root = ROOT / require_config_value(config, "paths.private_relative")
    support = json.loads((private_root / args.support / "support.json").read_text())
    rows, lock = _load_archive_rows(config, support["freeze_run"])
    by_record = {r["index_record_id"]: r for r in rows}
    packages = private_root / support["segments_run"] / "packages"

    usable = support["usable"]
    if args.target == "V_archive_given_A":
        usable = [u for u in usable if str(u["target_V_given_A_available"]) == "True"]
    identities = [u["split_group_id"] for u in usable]
    spec = support["splits"]
    index_of = {u["split_group_id"]: i for i, u in enumerate(usable)}
    folds = []
    for fold in spec["folds"]:
        train = np.array([index_of[g] for g in fold["train"] if g in index_of], dtype=int)
        test = np.array([index_of[g] for g in fold["test"] if g in index_of], dtype=int)
        inner = [{"inner_fold": i["inner_fold"],
                  "train_idx": np.array([index_of[g] for g in i["train"] if g in index_of], dtype=int),
                  "validation_idx": np.array([index_of[g] for g in i["validation"] if g in index_of], dtype=int)}
                 for i in fold["inner"]]
        if test.size == 0 or train.size == 0 or any(x["train_idx"].size == 0 or x["validation_idx"].size == 0 for x in inner):
            return runtime.finish(context, {"status": "DESIGN_SUPPORT_INSUFFICIENT", "target": args.target,
                                            "reason": f"empty scope in outer fold {fold['outer_fold']}",
                                            "neural_fits": 0})
        folds.append({"outer_fold": fold["outer_fold"], "train_idx": train, "test_idx": test, "inner": inner})

    technical_columns = list(__import__("auditory_fn1a.signal_export", fromlist=["x"]).TECHNICAL_COLUMNS)
    amplitude_column = __import__("auditory_fn1a.signal_export", fromlist=["x"]).AMPLITUDE_COLUMN
    results_root = ROOT / require_config_value(config, "paths.results_relative")
    with (results_root / support["segments_run"] / "segment_support_summary.csv").open(newline="", encoding="utf-8") as handle:
        technical_rows = {r["index_record_id"]: r for r in csv.DictReader(handle)}

    clinical, technical, amplitude, segments, target = [], [], [], [], []
    for entry in usable:
        row = by_record[entry["index_record_id"]]
        tech = technical_rows[entry["index_record_id"]]
        clinical_values = [row["age_recorded_months"], row["HA_duration_months"],
                           row["better_unaided_pta_corrected"], row["better_aided_pta_corrected"]]
        if args.target == "V_archive_given_A":
            clinical_values.append(row["A_raw_value"])
            y = row["MUSS_raw_value"]
        else:
            y = row["A_raw_value"]
        clinical.append([float(v) if str(v) not in ("", "None") else np.nan for v in clinical_values])
        technical.append([float(tech[f"Q_{c}"]) for c in technical_columns])
        amplitude.append(float(tech[f"Q_{amplitude_column}"]))
        with np.load(packages / f"{entry['index_record_id']}.npz", allow_pickle=False) as package:
            segments.append(package["features"])
        target.append(float(y))

    bounds = tuple(float(x) for x in require_config_value(config, "archive.target_bounds_source_units"))
    data = fitting.Dataset(groups=np.asarray(identities), clinical=np.asarray(clinical, dtype=float),
                           technical=np.asarray(technical, dtype=float),
                           amplitude=np.asarray(amplitude, dtype=float),
                           segments=np.asarray(segments, dtype=float),
                           target=np.asarray(target, dtype=float), bounds=bounds)
    if np.unique(data.target).size < 2:
        return runtime.finish(context, {"status": "TARGET_DATA_INSUFFICIENT", "target": args.target,
                                        "reason": "target is constant over the analysable cohort",
                                        "neural_fits": 0})

    ledger = runtime.FitLedger(context["private"], config)
    main = fitting.run_outer(data, folds, config, ledger)
    amplitude_predictions = fitting.amplitude_control(data, folds, main["selections"], config, ledger)
    mismatch_predictions = fitting.mismatch_control(data, folds, main["selections"], config, ledger)
    pool = {**main["predictions"], **amplitude_predictions, **mismatch_predictions}

    _write_table(context["public"] / "model_metrics.csv", fitting.metrics_table(data, pool),
                 ["model", "MAE", "RMSE", "n", "n_at_source_ceiling"], private=False)
    paired = fitting.paired_table(data, main["predictions"], config)
    paired_columns = sorted({k for r in paired for k in r})
    _write_table(context["public"] / "paired_effects.csv", paired, paired_columns, private=False)
    controls = fitting.control_table(data, main["predictions"], amplitude_predictions, mismatch_predictions, config)
    _write_table(context["public"] / "technical_amplitude_controls.csv", controls,
                 sorted({k for r in controls for k in r}), private=False)
    fold_rows = []
    for fold, selection in zip(folds, main["selections"]):
        for model, values in main["predictions"].items():
            residual = np.abs(values[fold["test_idx"]] - data.target[fold["test_idx"]])
            fold_rows.append({"outer_fold": fold["outer_fold"], "model": model,
                              "n_test": int(fold["test_idx"].size), "fold_MAE": float(residual.mean()),
                              "selection": json.dumps(selection.get(model.split("_")[0], {}), sort_keys=True)})
    _write_table(context["public"] / "fold_and_seed_summary.csv", fold_rows,
                 ["outer_fold", "model", "n_test", "fold_MAE", "selection"], private=False)
    write_json(context["public"] / "fit_ledger_summary.json",
               {"counts": ledger.counts(),
                "caps": {"neural": int(require_config_value(config, "resources.neural_fit_cap")),
                         "linear": int(require_config_value(config, "resources.linear_solver_call_cap"))},
                "seeds": list(require_config_value(config, "models.seeds")),
                "note": "Counts are optimiser calls, not independent experiments."}, private=False)
    write_json(context["public"] / "outer_selections.json", {"selections": main["selections"]}, private=False)
    np_private = context["private"] / "predictions.npz"
    np.savez_compressed(np_private, target=data.target, groups=data.groups,
                        **{k: v for k, v in pool.items()},
                        **{f"unclipped_{k}": v for k, v in main["unclipped"].items()})
    np_private.chmod(0o600)
    return runtime.finish(context, {"status": "FIT_COMPLETE", "target": args.target,
                                    "identities": int(data.target.size),
                                    "fit_ledger": ledger.counts(), "real_eeg_read": False,
                                    "models": list(pool)})


def _unimplemented(name: str):
    def handler(context: dict, config: dict, args) -> dict:
        raise ProvenanceError(f"{name.upper()}_NOT_YET_IMPLEMENTED")
    return handler


HANDLERS = {
    "prepare_archive": command_prepare_archive,
    "test": command_test,
    "freeze_archive": command_freeze_archive,
    "export_segments": command_export_segments,
    "freeze_support": command_freeze_support,
    "fit": command_fit,
    "report": _unimplemented("report"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m auditory_fn1a.cli")
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--run", required=True)
    parser.add_argument("--config", default=runtime.CONFIG_DEFAULT)
    parser.add_argument("--prepare", default=None)
    parser.add_argument("--tests", default=None)
    parser.add_argument("--freeze", default=None)
    parser.add_argument("--segments", default=None)
    parser.add_argument("--support", default=None)
    parser.add_argument("--target", choices=["A_archive", "V_archive_given_A"], default=None)
    parser.add_argument("--sources", default=None)
    parser.add_argument("--probe", type=int, default=None,
                        help="Export only the first N eligible records. Recorded in the receipt; "
                             "a probe run never substitutes for the full export.")
    args = parser.parse_args(argv)
    config = load_config(args.config)
    context = runtime.create_run(args.command, args.run, config, args=vars(args))
    receipt = HANDLERS[args.command](context, config, args)
    print(json.dumps({"fn1a_command": args.command, "run": args.run, "status": receipt.get("status")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
