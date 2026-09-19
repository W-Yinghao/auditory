"""FN1 command line. Plan section 14.

Every command that could touch real EEG or real clinical outcomes first consults
`clinical.validate_lock`. There is no flag, environment variable or argument that
unblocks W1; only a real, complete, pre-registered lock file does.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from . import clinical, reporting, request as request_module, runtime, signal as signal_module
from .runtime import ROOT, ProvenanceError, load_config, require_config_value, write_json, write_text

COMMANDS = ("prepare_request", "test", "resolve_evidence", "freeze", "export_segments", "fit", "report")


def _load_lock(path: str | None) -> dict:
    if not path:
        return clinical.validate_lock(None)
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    if not candidate.is_file():
        return {"w1_allowed": False, "status": "W1_BLOCKED_CLINICAL_LOCK",
                "reason": f"clinical lock file not found: {path}", "missing_fields": list(clinical.REQUIRED_FOR_W1)}
    document = yaml.safe_load(candidate.read_text())
    state = clinical.validate_lock(document)
    state["lock_file"] = str(candidate.relative_to(ROOT)) if str(candidate).startswith(str(ROOT)) else "<external>"
    state["lock_sha256"] = runtime.digest(candidate)
    return state


def _blocked_receipt(context: dict, command: str, lock_state: dict, extra: dict | None = None) -> dict:
    """A zero-fit stop receipt. Required by plan 14.2 whenever a gate is missing."""
    summary = {
        "status": "W1_BLOCKED_CLINICAL_LOCK",
        "command": command,
        "clinical_lock": lock_state,
        "neural_fits": 0,
        "linear_solver_calls": 0,
        "real_eeg_read": False,
        "note": "Gate not satisfied; nothing was fitted and no real signal was opened.",
    }
    if extra:
        summary.update(extra)
    return runtime.finish(context, summary)


def command_prepare_request(context: dict, config: dict, args: argparse.Namespace) -> dict:
    lock_state = _load_lock(args.clinical_lock)
    evidence = request_module.collect_evidence()
    questions = request_module.question_register(evidence)
    package = request_module.write_package(context["public"], context["private"], evidence, questions, lock_state)
    status = reporting.stage_status(lock_state=lock_state, implementation=None,
                                    request_summary=package, signal_feasibility=None)
    write_json(context["public"] / "STAGE_STATUS.json", status, private=False)
    write_text(context["report"] / "W0_REQUEST_REPORT.md",
               reporting.build_report(context["report"], sources=evidence["sources"], status=status,
                                      implementation=None), private=False)
    return runtime.finish(context, {"status": status["w0_status"], "stage": status["stage"],
                                    "clinical_lock": lock_state, "package": package,
                                    "neural_fits": 0, "real_eeg_read": False,
                                    "eeg_outcome_associations_computed": False})


def command_test(context: dict, config: dict, args: argparse.Namespace) -> dict:
    from . import synthetic

    ledger = runtime.FitLedger(context["private"], config)
    synthetic_config = require_config_value(config, "synthetic")
    model_config = require_config_value(config, "models")
    feature_dim = int(require_config_value(config, "signal.feature_dim"))
    planned = len(synthetic_config["mechanisms"]) * len(synthetic_config["seeds"]) * 2
    for index in range(planned):
        ledger.reserve("neural", {"stage": "synthetic", "index": index})
        ledger.reserve("linear", {"stage": "synthetic_clinical_baseline", "index": index})
    result = synthetic.run_suite(synthetic_config, model_config, feature_dim)
    if result["total_neural_fits"] != planned:
        raise ProvenanceError(f"SYNTHETIC_FIT_COUNT_MISMATCH:{result['total_neural_fits']}!={planned}")
    write_json(context["public"] / "implementation_check.json",
               {k: v for k, v in result.items() if k != "rows"}, private=False)
    write_json(context["private"] / "implementation_rows.json", {"rows": result["rows"]}, private=True)
    support = signal_module.inherited_support(1000.0, float(require_config_value(config, "signal.guard_seconds_min")))
    write_json(context["public"] / "inherited_signal_contract.json", {
        "inherited": signal_module.INHERITED_SOURCES,
        "new_in_this_module": list(signal_module.NEW_IMPLEMENTATIONS),
        "measured_support_at_1000hz": support,
        "known_gap": ("No acquisition-gap detection exists for HA BDF anywhere in this repository. "
                      "select_windows requires the caller to declare interval provenance and labels a "
                      "whole-record interval as assumed_single_interval_unverified."),
    }, private=False)
    lock_state = _load_lock(args.clinical_lock)
    status = reporting.stage_status(lock_state=lock_state, implementation=result,
                                    request_summary=None, signal_feasibility=None)
    write_json(context["public"] / "STAGE_STATUS.json", status, private=False)
    write_text(context["report"] / "IMPLEMENTATION_TEST_REPORT.md",
               reporting.build_report(context["report"], sources=[], status=status, implementation=result),
               private=False)
    return runtime.finish(context, {"status": result["status"], "stage": status["stage"],
                                    "neural_fits": result["total_neural_fits"],
                                    "fit_ledger": ledger.counts(), "real_eeg_read": False,
                                    "eeg_outcome_associations_computed": False})


def command_resolve_evidence(context: dict, config: dict, args: argparse.Namespace) -> dict:
    """Consume a REAL evidence file. Refuses to invent one."""
    if not args.evidence:
        return runtime.finish(context, {"status": "NO_EVIDENCE_SUPPLIED", "neural_fits": 0,
                                        "note": "resolve_evidence requires --evidence pointing at a real reply."})
    path = Path(args.evidence)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        return runtime.finish(context, {"status": "EVIDENCE_FILE_NOT_FOUND", "neural_fits": 0,
                                        "evidence_path": str(args.evidence)})
    raise ProvenanceError("RESOLVE_EVIDENCE_NOT_IMPLEMENTED_UNTIL_A_REAL_REPLY_EXISTS: "
                          "the import rule must be written against the actual reply format, "
                          "not guessed in advance.")


def command_freeze(context: dict, config: dict, args: argparse.Namespace) -> dict:
    lock_state = _load_lock(args.clinical_lock)
    if not lock_state["w1_allowed"]:
        return _blocked_receipt(context, "freeze", lock_state)
    raise ProvenanceError("FREEZE_REQUIRES_RESOLVED_EVIDENCE: a valid lock exists but the cohort "
                          "freeze must be written against the confirmed material.")


def command_export_segments(context: dict, config: dict, args: argparse.Namespace) -> dict:
    lock_state = _load_lock(args.clinical_lock)
    if not lock_state["w1_allowed"]:
        return _blocked_receipt(context, "export_segments", lock_state,
                                {"continuous_source_opened": False})
    raise ProvenanceError("EXPORT_SEGMENTS_REQUIRES_FROZEN_COHORT")


def command_fit(context: dict, config: dict, args: argparse.Namespace) -> dict:
    lock_state = _load_lock(args.clinical_lock)
    if not lock_state["w1_allowed"]:
        # F2 insufficiency alone would block only F2; a missing lock blocks both.
        return _blocked_receipt(context, "fit", lock_state, {"target": args.target})
    raise ProvenanceError("FIT_REQUIRES_EXPORTED_SEGMENTS")


def command_report(context: dict, config: dict, args: argparse.Namespace) -> dict:
    lock_state = _load_lock(args.clinical_lock)
    status = reporting.stage_status(lock_state=lock_state, implementation=None,
                                    request_summary=None, signal_feasibility=None)
    if not lock_state["w1_allowed"]:
        write_json(context["public"] / "STAGE_STATUS.json", status, private=False)
        return runtime.finish(context, {"status": "W1_NOT_STARTED", "stage": status["stage"],
                                        "clinical_lock": lock_state, "neural_fits": 0,
                                        "note": ("No real model exists. No primary table is emitted; an "
                                                 "empty zero-gain table would misrepresent a data gap as a result.")})
    raise ProvenanceError("REPORT_REQUIRES_COMPLETED_FIT_RUNS")


HANDLERS = {
    "prepare_request": command_prepare_request,
    "test": command_test,
    "resolve_evidence": command_resolve_evidence,
    "freeze": command_freeze,
    "export_segments": command_export_segments,
    "fit": command_fit,
    "report": command_report,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m auditory_fn1.cli")
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--run", required=True)
    parser.add_argument("--config", default=runtime.CONFIG_DEFAULT)
    parser.add_argument("--clinical-lock", default=None)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--freeze", dest="freeze_run", default=None)
    parser.add_argument("--target", choices=["A", "MUSS_given_A"], default=None)
    parser.add_argument("--sources", default=None)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    context = runtime.create_run(args.command, args.run, config, args=vars(args))
    receipt = HANDLERS[args.command](context, config, args)
    print(json.dumps({"fn1_command": args.command, "run": args.run, "status": receipt.get("status")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
