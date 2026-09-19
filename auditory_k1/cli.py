"""K1 runner: narrow checks, then the corrected matrix. Slurm only."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

from auditory_fn1.models import TabularTransform, clip_to_bounds
from auditory_fn1.statistics import error_metrics, leave_one_identity_range, paired_identity_bootstrap, shared_draws
from auditory_fn1a import runtime
from auditory_fn1a.runtime import ROOT, ProvenanceError, load_config, require_config_value, write_json
from auditory_fn1a.signal_export import AMPLITUDE_COLUMN, TECHNICAL_COLUMNS

from . import narrow
from .profiled import ClinicalBlock, SetNetwork, predict, train_profiled

FN1A_PRIVATE = "private/auditory_fn1a"
FN1A_RESULTS = "results/auditory_fn1a"
K1_PATHS = {"private_relative": "private/auditory_k1", "results_relative": "results/auditory_k1",
            "reports_relative": "reports/auditory_k1", "docs_relative": "docs/auditory_k1"}


def _write_table(path: Path, rows: list[dict], columns: list[str], *, private: bool) -> None:
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    path.chmod(0o600 if private else 0o644)


def _load(config: dict, support_run: str, target_name: str):
    private_root, results_root = ROOT / FN1A_PRIVATE, ROOT / FN1A_RESULTS
    support = json.loads((private_root / support_run / "support.json").read_text())
    lock = json.loads((private_root / support["freeze_run"] / "archive_analysis_lock.json").read_text())
    with (private_root / lock["bound_runs"]["prepare"] / "archive_rows.csv").open(newline="", encoding="utf-8") as h:
        rows = {r["index_record_id"]: r for r in csv.DictReader(h)}
    with (results_root / support["segments_run"] / "segment_support_summary.csv").open(newline="", encoding="utf-8") as h:
        technical = {r["index_record_id"]: r for r in csv.DictReader(h)}
    packages = private_root / support["segments_run"] / "packages"

    usable = support["usable"]
    if target_name == "V_archive_given_A":
        usable = [u for u in usable if str(u["target_V_given_A_available"]) == "True"]
    index_of = {u["split_group_id"]: i for i, u in enumerate(usable)}
    folds = []
    for fold in support["splits"]["folds"]:
        inner = [{"inner_fold": i["inner_fold"],
                  "train_idx": np.array([index_of[g] for g in i["train"] if g in index_of], dtype=int),
                  "validation_idx": np.array([index_of[g] for g in i["validation"] if g in index_of], dtype=int)}
                 for i in fold["inner"]]
        folds.append({"outer_fold": fold["outer_fold"],
                      "train_idx": np.array([index_of[g] for g in fold["train"] if g in index_of], dtype=int),
                      "test_idx": np.array([index_of[g] for g in fold["test"] if g in index_of], dtype=int),
                      "inner": inner})
    clinical, technical_rows, amplitude, segments, target, identities = [], [], [], [], [], []
    for entry in usable:
        row, tech = rows[entry["index_record_id"]], technical[entry["index_record_id"]]
        values = [row["age_recorded_months"], row["HA_duration_months"],
                  row["better_unaided_pta_corrected"], row["better_aided_pta_corrected"]]
        y = row["A_raw_value"]
        if target_name == "V_archive_given_A":
            values.append(row["A_raw_value"])
            y = row["MUSS_raw_value"]
        clinical.append([float(v) if str(v) not in ("", "None") else np.nan for v in values])
        technical_rows.append([float(tech[f"Q_{c}"]) for c in TECHNICAL_COLUMNS])
        amplitude.append(float(tech[f"Q_{AMPLITUDE_COLUMN}"]))
        with np.load(packages / f"{entry['index_record_id']}.npz", allow_pickle=False) as package:
            segments.append(package["features"])
        target.append(float(y))
        identities.append(entry["split_group_id"])
    return {"folds": folds, "identities": np.asarray(identities),
            "clinical": np.asarray(clinical, float), "technical": np.asarray(technical_rows, float),
            "amplitude": np.asarray(amplitude, float), "segments": np.asarray(segments, float),
            "target": np.asarray(target, float)}


def _fit_one(data: dict, matrix: np.ndarray, order: str, train, evaluate, spec: dict,
             neural_penalty: float, seed: int, bounds, config: dict, ledger, context_note: dict):
    lo, hi = bounds
    span = hi - lo
    transform = TabularTransform(spec["family"]).fit(matrix[train])
    design_train, design_eval = transform.transform(matrix[train]), transform.transform(matrix[evaluate])
    block_features = data["segments"][train].reshape(-1, data["segments"].shape[2])
    centre, spread = block_features.mean(axis=0), block_features.std(axis=0)
    spread = np.where(spread <= 0, 1.0, spread)
    segments_train = (data["segments"][train] - centre) / spread
    segments_eval = (data["segments"][evaluate] - centre) / spread
    y_train = (data["target"][train] - lo) / span
    block = ClinicalBlock.fit(design_train, float(spec["penalty"]))
    network = SetNetwork(order="mean_then_map" if order == "M3" else "map_then_mean",
                         clinical_dim=0, seed=int(seed))
    ledger.reserve("neural", context_note)
    diagnostics = train_profiled(network, block, segments_train, design_train, y_train,
                                 steps=int(require_config_value(config, "models.optimization_steps")),
                                 learning_rate=float(require_config_value(config, "models.learning_rate")),
                                 neural_penalty=float(neural_penalty))
    prediction = predict(network, block, diagnostics["gamma"], diagnostics["intercept"],
                         segments_eval, design_eval) * span + lo
    return prediction, diagnostics


def _select_and_fit(data: dict, matrix: np.ndarray, order: str, fold: dict, spec: dict,
                    bounds, config: dict, ledger) -> dict:
    seeds = [int(s) for s in require_config_value(config, "models.seeds")]
    penalties = [float(p) for p in sorted(require_config_value(config, "models.neural_penalties"), reverse=True)]
    best, trace = None, []
    for penalty in penalties:
        errors = []
        for inner in fold["inner"]:
            per_seed = [_fit_one(data, matrix, order, inner["train_idx"], inner["validation_idx"], spec,
                                 penalty, seed, bounds, config, ledger,
                                 {"stage": order, "penalty": penalty, "seed": seed,
                                  "outer_fold": fold["outer_fold"], "inner_fold": inner["inner_fold"]})[0]
                        for seed in seeds]
            averaged = np.mean(per_seed, axis=0)
            errors.append(np.abs(clip_to_bounds(averaged, bounds) - data["target"][inner["validation_idx"]]))
        mae = float(np.concatenate(errors).mean())
        trace.append({"penalty": penalty, "inner_MAE": mae})
        if best is None or mae < best["inner_MAE"] - 1e-12:
            best = {"penalty": penalty, "inner_MAE": mae}
    finals, diagnostics = [], []
    for seed in seeds:
        prediction, diag = _fit_one(data, matrix, order, fold["train_idx"], fold["test_idx"], spec,
                                    best["penalty"], seed, bounds, config, ledger,
                                    {"stage": order + "_final", "penalty": best["penalty"], "seed": seed,
                                     "outer_fold": fold["outer_fold"]})
        finals.append(prediction)
        diagnostics.append({k: v for k, v in diag.items() if k not in ("gamma", "intercept")})
    return {"prediction": np.mean(finals, axis=0), "selected": best, "trace": trace,
            "diagnostics": diagnostics}


def command_narrow(context: dict, config: dict, args) -> dict:
    ledger = runtime.FitLedger(context["private"], config)
    model_config = require_config_value(config, "models")
    planned = 3 * 4 * 2
    for index in range(planned):
        ledger.reserve("neural", {"stage": "narrow_world", "index": index})
    result = narrow.run_all(model_config)
    write_json(context["public"] / "narrow_checks.json",
               {k: v for k, v in result.items() if k != "worlds"} |
               {"worlds_summary": result["worlds"]["summary"],
                "worlds_criterion": result["worlds"]["criterion"],
                "worlds_interpretation": result["worlds"]["interpretation"]}, private=False)
    write_json(context["private"] / "narrow_world_rows.json", {"rows": result["worlds"]["rows"]}, private=True)
    return runtime.finish(context, {"status": result["status"], "world_fits": result["world_fits"],
                                    "fit_ledger": ledger.counts(), "real_eeg_read": False})


def command_fit(context: dict, config: dict, args) -> dict:
    narrow_summary = json.loads((ROOT / K1_PATHS["results_relative"] / args.narrow / "summary.json").read_text())
    if narrow_summary.get("status") != "NARROW_CHECKS_PASSED":
        return runtime.finish(context, {"status": "IMPLEMENTATION_UNRESOLVED", "target": args.target,
                                        "reason": f"narrow checks reported {narrow_summary.get('status')}",
                                        "neural_fits": 0})
    data = _load(config, args.support, args.target)
    bounds = tuple(float(x) for x in require_config_value(config, "archive.target_bounds_source_units"))
    selections = json.loads((ROOT / FN1A_RESULTS / args.fit_run / "outer_selections.json").read_text())["selections"]
    specs = {s["outer_fold"]: s["shared_clinical_spec"] for s in selections}
    original = np.load(ROOT / FN1A_PRIVATE / args.fit_run / "predictions.npz", allow_pickle=False)

    ledger = runtime.FitLedger(context["private"], config)
    matrix = np.hstack([data["clinical"], data["technical"]])
    augmented = np.hstack([data["clinical"], data["technical"], data["amplitude"].reshape(-1, 1)])
    n = data["target"].size
    predictions = {"M3s": np.full(n, np.nan), "M4s": np.full(n, np.nan),
                   "M4s_amplitude": np.full(n, np.nan), "M4s_mismatch": np.full(n, np.nan)}
    fold_rows, diagnostics_rows = [], []
    seeds = [int(s) for s in require_config_value(config, "models.seeds")]
    mismatch_seed = int(require_config_value(config, "controls.mismatch_seed"))

    for fold in data["folds"]:
        spec = specs[fold["outer_fold"]]
        for order, key in (("M3", "M3s"), ("M4", "M4s")):
            outcome = _select_and_fit(data, matrix, order, fold, spec, bounds, config, ledger)
            predictions[key][fold["test_idx"]] = clip_to_bounds(outcome["prediction"], bounds)
            fold_rows.append({"outer_fold": fold["outer_fold"], "model": key,
                              "selected_penalty": outcome["selected"]["penalty"],
                              "inner_MAE": outcome["selected"]["inner_MAE"],
                              "n_train": int(fold["train_idx"].size), "n_test": int(fold["test_idx"].size)})
            for seed, diag in zip(seeds, outcome["diagnostics"]):
                diagnostics_rows.append({"outer_fold": fold["outer_fold"], "model": key, "seed": seed, **diag})
        # Controls reuse the frozen selection; no new grid is opened.
        chosen = next(r for r in fold_rows if r["outer_fold"] == fold["outer_fold"] and r["model"] == "M4s")
        amplitude_final = [_fit_one(data, augmented, "M4", fold["train_idx"], fold["test_idx"], spec,
                                    chosen["selected_penalty"], seed, bounds, config, ledger,
                                    {"stage": "M4s_amplitude", "seed": seed, "outer_fold": fold["outer_fold"]})[0]
                           for seed in seeds]
        predictions["M4s_amplitude"][fold["test_idx"]] = clip_to_bounds(np.mean(amplitude_final, axis=0), bounds)
        rng = np.random.default_rng(mismatch_seed + int(fold["outer_fold"]))
        size = fold["train_idx"].size
        while True:
            order_permutation = rng.permutation(size)
            if not np.any(order_permutation == np.arange(size)):
                break
        scrambled = dict(data)
        shuffled = data["segments"].copy()
        shuffled[fold["train_idx"]] = data["segments"][fold["train_idx"]][order_permutation]
        scrambled["segments"] = shuffled
        mismatch_final = [_fit_one(scrambled, matrix, "M4", fold["train_idx"], fold["test_idx"], spec,
                                   chosen["selected_penalty"], seed, bounds, config, ledger,
                                   {"stage": "M4s_mismatch", "seed": seed, "outer_fold": fold["outer_fold"]})[0]
                          for seed in seeds]
        predictions["M4s_mismatch"][fold["test_idx"]] = clip_to_bounds(np.mean(mismatch_final, axis=0), bounds)

    pool = {name: original[name] for name in ("M0_C", "M1_CQ", "M2_MEAN_RIDGE",
                                              "M3_MEAN_THEN_MLP", "M4_MLP_THEN_MEAN",
                                              "M1_CQ_amplitude", "M4_amplitude", "M4_mismatch")}
    pool.update(predictions)
    metrics = [{"model": m, **error_metrics(data["target"], v)} for m, v in pool.items()]
    _write_table(context["public"] / "model_metrics.csv", metrics, ["model", "MAE", "RMSE", "n"], private=False)

    repetitions = int(require_config_value(config, "validation.bootstrap_repetitions"))
    seed = int(require_config_value(config, "validation.bootstrap_seed"))
    draws = shared_draws(n, repetitions=repetitions, seed=seed)
    errors = {m: np.abs(v - data["target"]) for m, v in pool.items()}
    comparisons = [("M0_C", "M4s", "corrected method vs original clinical numbers"),
                   ("M1_CQ", "M4s", "corrected EEG increment beyond the acquisition summary"),
                   ("M3s", "M4s", "corrected learning-order comparison"),
                   ("M4_MLP_THEN_MEAN", "M4s", "corrected objective vs the original M4"),
                   ("M3_MEAN_THEN_MLP", "M3s", "corrected objective vs the original M3"),
                   ("M1_CQ_amplitude", "M4s_amplitude", "amplitude-adjusted corrected increment"),
                   ("M0_C", "M4s_amplitude", "amplitude-adjusted corrected method vs original clinical"),
                   ("M4s_mismatch", "M4s", "real correspondence vs mismatched training, corrected")]
    paired = []
    for reference, candidate, meaning in comparisons:
        record = paired_identity_bootstrap(errors[reference], errors[candidate],
                                           repetitions=repetitions, seed=seed, draws=draws)
        record.update({"reference": reference, "candidate": candidate, "meaning": meaning,
                       **{f"loo_{k}": v for k, v in
                          leave_one_identity_range(errors[reference], errors[candidate]).items()}})
        paired.append(record)
    _write_table(context["public"] / "paired_effects.csv", paired,
                 sorted({k for r in paired for k in r}), private=False)
    _write_table(context["public"] / "fold_and_seed_summary.csv", fold_rows,
                 ["outer_fold", "model", "selected_penalty", "inner_MAE", "n_train", "n_test"], private=False)
    _write_table(context["public"] / "training_diagnostics.csv", diagnostics_rows,
                 sorted({k for r in diagnostics_rows for k in r}), private=False)
    write_json(context["public"] / "fit_ledger_summary.json",
               {"counts": ledger.counts(),
                "caps": {"neural": int(require_config_value(config, "resources.neural_fit_cap"))},
                "clinical_solves_are_inside_each_neural_fit": True,
                "note": ("The profiled clinical solve runs once per theta update inside each neural fit. "
                         "The normal-equation matrix is theta-independent, so it is Cholesky-factorised "
                         "once per fit and re-used; that is the same solution, not an approximation. "
                         "These inner solves are reported per fit in training_diagnostics.csv and are not "
                         "counted against the standalone linear-solver cap, which was written for model "
                         "selection fits.")}, private=False)
    saved = context["private"] / "predictions.npz"
    np.savez_compressed(saved, target=data["target"], groups=data["identities"], **pool)
    saved.chmod(0o600)
    return runtime.finish(context, {"status": "FIT_COMPLETE", "target": args.target,
                                    "identities": int(n), "fit_ledger": ledger.counts(),
                                    "reused_from": args.fit_run, "real_eeg_read": False})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m auditory_k1.cli")
    parser.add_argument("command", choices=["narrow", "fit"])
    parser.add_argument("--run", required=True)
    parser.add_argument("--config", default=runtime.CONFIG_DEFAULT)
    parser.add_argument("--support", default=None)
    parser.add_argument("--narrow", default=None)
    parser.add_argument("--fit-run", default=None)
    parser.add_argument("--target", choices=["A_archive", "V_archive_given_A"], default=None)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    config["paths"] = dict(config["paths"])
    config["paths"].update(K1_PATHS)
    context = runtime.create_run(args.command, args.run, config, args=vars(args))
    receipt = (command_narrow if args.command == "narrow" else command_fit)(context, config, args)
    print(json.dumps({"k1": args.command, "run": args.run, "status": receipt.get("status")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
