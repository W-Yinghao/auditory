"""Run creation, source snapshot, fit ledger and environment capture.

Design rules this module enforces, each adopted because the historical audit of this
repository found the opposite pattern somewhere:

* Every governing constant is READ from the frozen config. `require_config_value`
  refuses to supply a default, so a constant silently duplicated in code cannot
  diverge from the YAML that the receipt certifies.
* A provenance mismatch RAISES. There is no flag, keyword or environment variable
  that downgrades it to a warning.
* Status fields are derived from computed comparisons. This module offers no helper
  that writes a literal PASS.
* Private run directories are created mode 0700 and every file written into them is
  chmod 0600 explicitly, rather than relying on the caller's umask.
* The receipt records interpreter and library versions, not only data and code hashes.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = Path(__file__).resolve().parent
CONFIG_DEFAULT = "configs/auditory_fn1_v1.yaml"


class ProvenanceError(RuntimeError):
    """Raised when a declared source, hash or contract does not match reality."""


class BudgetError(RuntimeError):
    """Raised when a reservation would exceed a frozen resource cap."""


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def require_slurm() -> str:
    """All numerical work runs under Slurm (AGENTS.md; plan section 17)."""
    job = os.environ.get("SLURM_JOB_ID")
    if not job:
        raise ProvenanceError("SLURM_REQUIRED: numerical work must run as a Slurm job")
    return job


def load_config(relative: str = CONFIG_DEFAULT) -> dict:
    path = ROOT / relative
    if not path.is_file():
        raise ProvenanceError(f"CONFIG_MISSING:{relative}")
    config = yaml.safe_load(path.read_text())
    config["_path"] = str(relative)
    config["_sha256"] = digest(path)
    return config


def require_config_value(config: dict, dotted: str) -> Any:
    """Read a frozen config value. Deliberately has no default parameter.

    A caller that wants a constant must declare it in the YAML, so the config hash in
    the receipt actually governs behaviour instead of merely accompanying it.
    """
    node: Any = config
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node:
            raise ProvenanceError(f"CONFIG_KEY_MISSING:{dotted}")
        node = node[key]
    return node


def environment_record() -> dict:
    """Interpreter, libraries and BLAS threading, recorded with every run."""
    versions: dict[str, str] = {"python": platform.python_version(), "executable": sys.executable}
    for name in ("numpy", "scipy", "sklearn", "pandas", "yaml", "mne", "torch"):
        try:
            module = __import__(name)
            versions[name] = str(getattr(module, "__version__", "unknown"))
        except Exception:
            versions[name] = "absent"
    threads = {key: os.environ.get(key) for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
    return {"versions": versions, "thread_environment": threads, "platform": platform.platform()}


def write_json(path: Path, payload: Any, *, private: bool) -> Path:
    path = Path(path)
    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text)
    path.chmod(0o600 if private else 0o644)
    return path


def write_text(path: Path, text: str, *, private: bool) -> Path:
    path = Path(path)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text if text.endswith("\n") else text + "\n")
    path.chmod(0o600 if private else 0o644)
    return path


def _snapshot_sources(destination: Path, config_relative: str) -> dict[str, str]:
    """Copy the executing package, the config and the frozen plan into the run."""
    snapshot = destination / "source"
    snapshot.mkdir(mode=0o700, parents=True, exist_ok=False)
    (snapshot / "auditory_fn1").mkdir(mode=0o700, exist_ok=False)
    hashes: dict[str, str] = {}
    for module in sorted(PACKAGE.glob("*.py")):
        target = snapshot / "auditory_fn1" / module.name
        shutil.copyfile(module, target)
        target.chmod(0o600)
        hashes[f"auditory_fn1/{module.name}"] = digest(module)
    for extra in (config_relative, require_plan_relative()):
        source = ROOT / extra
        target = snapshot / Path(extra).name
        shutil.copyfile(source, target)
        target.chmod(0o600)
        hashes[extra] = digest(source)
    return hashes


def require_plan_relative() -> str:
    return "AUDITORY_FN1_NEXT_ROUND_PLAN_493a076.md"


def create_run(command: str, run: str, config: dict, *, args: dict | None = None) -> dict:
    """Create the private/results/reports triplet for a run and snapshot its sources.

    Refuses an occupied run name in any of the three trees, so a rerun can never
    silently overwrite a historical result.
    """
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
    hashes = _snapshot_sources(private, str(config["_path"]))
    start = {
        "command": command,
        "run": run,
        "job_id": job,
        "config_path": str(config["_path"]),
        "config_sha256": config["_sha256"],
        "plan_sha256": digest(ROOT / require_plan_relative()),
        "source_hashes": hashes,
        "environment": environment_record(),
        "args": args or {},
        "stage": require_config_value(config, "project.initial_stage"),
        "real_training_enabled": require_config_value(config, "project.real_training_enabled"),
    }
    write_json(private / "start.json", start, private=True)
    return {"private": private, "public": public, "report": report, "start": start}


def finish(context: dict, summary: dict) -> dict:
    """Write the completion receipt. `status` must already be a derived value."""
    if "status" not in summary:
        raise ProvenanceError("COMPLETION_STATUS_REQUIRED")
    private: Path = context["private"]
    public: Path = context["public"]
    outputs = {p.name: digest(p) for p in sorted(private.iterdir()) if p.is_file()}
    outputs.update({f"../../results/{public.parent.name}/{public.name}/{p.name}": digest(p) for p in sorted(public.iterdir()) if p.is_file()})
    receipt = dict(summary)
    receipt["job_id"] = context["start"]["job_id"]
    receipt["run"] = context["start"]["run"]
    receipt["command"] = context["start"]["command"]
    receipt["config_sha256"] = context["start"]["config_sha256"]
    receipt["output_hashes"] = outputs
    write_json(private / "completion.json", receipt, private=True)
    write_json(public / "summary.json", {k: v for k, v in receipt.items() if k != "output_hashes"}, private=False)
    return receipt


class FitLedger:
    """Reserve every optimiser call before it happens, under an exclusive lock.

    Failures stay charged. The caps come from the config, not from literals.
    """

    def __init__(self, private: Path, config: dict) -> None:
        self.path = Path(private) / "fit_events.jsonl"
        self.path.touch(mode=0o600, exist_ok=True)
        self.caps = {
            "neural": int(require_config_value(config, "resources.neural_fit_cap")),
            "linear": int(require_config_value(config, "resources.linear_solver_call_cap")),
        }

    def counts(self) -> dict[str, int]:
        totals = {kind: 0 for kind in self.caps}
        if self.path.stat().st_size:
            for line in self.path.read_text().splitlines():
                if not line.strip():
                    continue
                kind = json.loads(line).get("kind")
                if kind in totals:
                    totals[kind] += 1
        return totals

    def reserve(self, kind: str, context: dict) -> int:
        if kind not in self.caps:
            raise BudgetError(f"UNKNOWN_FIT_KIND:{kind}")
        with self.path.open("r+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                used = sum(1 for line in handle.read().splitlines() if line.strip() and json.loads(line).get("kind") == kind)
                if used >= self.caps[kind]:
                    raise BudgetError(f"FIT_CAP_EXCEEDED:{kind}:{used}/{self.caps[kind]}")
                handle.write(json.dumps({"kind": kind, "index": used, **context}, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                return used
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
