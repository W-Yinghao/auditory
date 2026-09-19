"""Run creation, source snapshot, environment capture and the fit ledger for FN1-A.

Same discipline as the FN1 runtime: config values are read not duplicated, provenance
mismatches raise with no downgrade path, status fields are derived, private artefacts
are created 0700/0600 explicitly, and interpreter/library versions go into the receipt.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from auditory_fn1.runtime import (  # pure helpers, no gate
    BudgetError,
    FitLedger,
    ProvenanceError,
    digest,
    digest_bytes,
    environment_record,
    require_slurm,
    write_json,
    write_text,
)

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = Path(__file__).resolve().parent
FN1_PACKAGE = ROOT / "auditory_fn1"
CONFIG_DEFAULT = "configs/auditory_fn1a.yaml"

__all__ = ["ROOT", "PACKAGE", "CONFIG_DEFAULT", "ProvenanceError", "BudgetError", "FitLedger",
           "digest", "digest_bytes", "environment_record", "require_slurm", "write_json",
           "write_text", "load_config", "require_config_value", "create_run", "finish",
           "resolve_source", "SupportStop"]


class SupportStop(RuntimeError):
    """A real support/conflict stop. Never raised for plain metadata unknowns."""


def load_config(relative: str = CONFIG_DEFAULT) -> dict:
    import yaml

    path = ROOT / relative
    if not path.is_file():
        raise ProvenanceError(f"CONFIG_MISSING:{relative}")
    config = yaml.safe_load(path.read_text())
    config["_path"] = str(relative)
    config["_sha256"] = digest(path)
    return config


def require_config_value(config: dict, dotted: str):
    node = config
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node:
            raise ProvenanceError(f"CONFIG_KEY_MISSING:{dotted}")
        node = node[key]
    return node


def resolve_source(config: dict, name: str) -> Path:
    """Resolve a declared source path and refuse an undeclared or forbidden one."""
    relative = require_config_value(config, f"sources.{name}")
    path = ROOT / relative
    if not path.exists():
        raise ProvenanceError(f"SOURCE_MISSING:{name}:{relative}")
    return path


def _snapshot(destination: Path, config_relative: str) -> dict[str, str]:
    snapshot = destination / "source"
    snapshot.mkdir(mode=0o700, parents=True, exist_ok=False)
    hashes: dict[str, str] = {}
    for package_dir, label in ((PACKAGE, "auditory_fn1a"), (FN1_PACKAGE, "auditory_fn1")):
        target_dir = snapshot / label
        target_dir.mkdir(mode=0o700, exist_ok=False)
        for module in sorted(package_dir.glob("*.py")):
            target = target_dir / module.name
            shutil.copyfile(module, target)
            target.chmod(0o600)
            hashes[f"{label}/{module.name}"] = digest(module)
    for extra in (config_relative, "AUDITORY_FN1_ARCHIVAL_PLAN_v1_1_493a076.md"):
        source = ROOT / extra
        target = snapshot / Path(extra).name
        shutil.copyfile(source, target)
        target.chmod(0o600)
        hashes[extra] = digest(source)
    return hashes


def create_run(command: str, run: str, config: dict, *, args: dict | None = None) -> dict:
    job = require_slurm()
    private = ROOT / require_config_value(config, "paths.private_relative") / run
    public = ROOT / require_config_value(config, "paths.results_relative") / run
    report = ROOT / require_config_value(config, "paths.reports_relative") / run
    for path in (private, public, report):
        if path.exists():
            raise ProvenanceError(f"RUN_OCCUPIED:{path.relative_to(ROOT)}")
    private.mkdir(mode=0o700, parents=True, exist_ok=False)
    public.mkdir(mode=0o755, parents=True, exist_ok=False)
    report.mkdir(mode=0o755, parents=True, exist_ok=False)
    hashes = _snapshot(private, str(config["_path"]))
    start = {
        "command": command,
        "run": run,
        "job_id": job,
        "config_path": str(config["_path"]),
        "config_sha256": config["_sha256"],
        "plan_sha256": digest(ROOT / require_config_value(config, "project.plan_file")),
        "source_hashes": hashes,
        "environment": environment_record(),
        "args": args or {},
        "stage": require_config_value(config, "project.initial_stage"),
        "real_training_authorized": require_config_value(config, "project.real_training_authorized"),
        "external_contact_required": require_config_value(config, "project.external_contact_required"),
    }
    write_json(private / "start.json", start, private=True)
    return {"private": private, "public": public, "report": report, "start": start, "config": config}


def finish(context: dict, summary: dict) -> dict:
    if "status" not in summary:
        raise ProvenanceError("COMPLETION_STATUS_REQUIRED")
    private: Path = context["private"]
    public: Path = context["public"]
    receipt = dict(summary)
    receipt.update({k: context["start"][k] for k in ("job_id", "run", "command", "config_sha256")})
    receipt["output_hashes"] = {p.name: digest(p) for p in sorted(private.iterdir()) if p.is_file()}
    receipt["public_output_hashes"] = {p.name: digest(p) for p in sorted(public.iterdir()) if p.is_file()}
    write_json(private / "completion.json", receipt, private=True)
    write_json(public / "summary.json", {k: v for k, v in receipt.items()
                                         if k not in ("output_hashes",)}, private=False)
    return receipt
