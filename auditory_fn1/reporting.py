"""W0/W1 reporting. Reads saved predictions and receipts; never fits anything.

Plan section 14.2: `report` must not implicitly retrain, and when no real model exists
it must emit `W1_NOT_STARTED` rather than an empty "zero gain" primary table.

This module imports no estimator and no route. That is deliberate and is asserted in
tests, because a report or ledger repair that re-enters training is the specific
failure this project has already paid for once.
"""
from __future__ import annotations

import json
from pathlib import Path

from .runtime import ROOT, digest


def stage_status(*, lock_state: dict, implementation: dict | None, request_summary: dict | None,
                 signal_feasibility: dict | None) -> dict:
    """Derive the single machine-readable stage status. Every field is computed."""
    reasons: list[str] = []
    if not lock_state.get("w1_allowed"):
        reasons.append(lock_state.get("reason", "clinical lock absent"))
    implementation_status = (implementation or {}).get("status")
    if implementation is not None and implementation_status != "IMPLEMENTATION_CAPABILITY_ESTABLISHED":
        reasons.append(f"implementation check: {implementation_status}")
    if lock_state.get("w1_allowed") and implementation_status == "IMPLEMENTATION_CAPABILITY_ESTABLISHED":
        stage = "W1_READY"
    elif implementation is not None and implementation_status not in (None, "IMPLEMENTATION_CAPABILITY_ESTABLISHED"):
        stage = "IMPLEMENTATION_UNRESOLVED"
    else:
        stage = "W0_READY / W1_BLOCKED_CLINICAL_LOCK"
    return {
        "stage": stage,
        "w0_status": "NEEDS_CLINICAL_RESPONSE" if not lock_state.get("w1_allowed") else "TARGET_RESOLVED",
        "w1_allowed": bool(lock_state.get("w1_allowed")),
        "blocking_reasons": reasons,
        "implementation_status": implementation_status,
        "request_summary": request_summary,
        "signal_feasibility": signal_feasibility,
        "note": ("W0 status describes the state of the clinical material, not an EEG "
                 "positive or negative result."),
    }


def load_if_present(relative: str) -> tuple[dict | None, dict]:
    path = ROOT / relative
    if not path.is_file():
        return None, {"path": relative, "present": False}
    return json.loads(path.read_text()), {"path": relative, "present": True, "sha256": digest(path)}


def build_report(run_directory: Path, *, sources: list[dict], status: dict,
                 implementation: dict | None) -> str:
    """Render the W0 implementation/status report as markdown from computed values."""
    lines: list[str] = []
    lines.append("# FN1 W0 execution report")
    lines.append("")
    lines.append(f"- stage: `{status['stage']}`")
    lines.append(f"- W0 status: `{status['w0_status']}`")
    lines.append(f"- W1 allowed: `{status['w1_allowed']}`")
    if status["blocking_reasons"]:
        lines.append("- blocking reasons:")
        for reason in status["blocking_reasons"]:
            lines.append(f"  - {reason}")
    lines.append("")
    if implementation is not None:
        lines.append("## Limited implementation check")
        lines.append("")
        lines.append(f"- status: `{implementation['status']}`")
        lines.append(f"- neural fits executed: {implementation['total_neural_fits']} "
                     f"(plan budget: three mechanisms x four seeds x two orders = 24)")
        lines.append(f"- all predictions finite: {implementation['all_predictions_finite']}")
        lines.append(f"- non-finite optimiser runs: {implementation['nonfinite_optimizer_runs']}")
        lines.append(f"- parameter counts observed: {implementation['parameter_counts_observed']}")
        lines.append("")
        lines.append("| mechanism | model | required | seeds meeting threshold | passed |")
        lines.append("|---|---|---|---|---|")
        for check in implementation["checks"]:
            lines.append(f"| {check['mechanism']} | {check['model']} | {check['required']} | "
                         f"{check['seeds_meeting_threshold']}/{check['seeds_total']} | {check['passed']} |")
        lines.append("")
        lines.append(f"> {implementation['interpretation']}")
        lines.append("")
    lines.append("## Sources consulted")
    lines.append("")
    lines.append("| role | path | present | sha256 |")
    lines.append("|---|---|---|---|")
    for source in sources:
        lines.append(f"| {source.get('role','')} | `{source['path']}` | {source.get('present')} | "
                     f"`{str(source.get('sha256',''))[:16]}` |")
    lines.append("")
    lines.append("No model was fitted on real EEG, no clinical material was sent anywhere, and no "
                 "EEG-to-target association was computed in this stage.")
    return "\n".join(lines) + "\n"
