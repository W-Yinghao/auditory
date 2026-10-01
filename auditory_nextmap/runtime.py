"""Run bookkeeping for auditory_nextmap: auditory_pf's requeue-safe runtime, nextmap source hashes and a job ledger.

Jobs run under --qos=runfill (preemptible, PreemptMode=REQUEUE). Every unit is written atomically and carries a done
marker, so a requeued job skips finished units; receipts are written per (job, task, restart).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from auditory_pf import runtime as pfr
from auditory_pf.runtime import (ROOT, ProvenanceError, cfg, digest, job_tag, mark_done, private_dir, read_json,  # noqa: F401
                                 require_slurm, results_dir, save_npz_atomic, stable_int, task_units, unit_done,
                                 write_csv_atomic, write_json_atomic)

PACKAGE = Path(__file__).resolve().parent
CONFIG_DEFAULT = "configs/auditory_nextmap_v1.yaml"
DEPENDENCIES = ("auditory_pf/cohort.py", "auditory_pf/stats.py", "auditory_pf/gpu.py", "auditory_pf/stim.py",
                "auditory_pf/analysis_b1.py", "auditory_pf/runtime.py", "auditory_gx/data.py", "auditory_gx/train.py",
                "auditory_gx/models.py", "auditory_gx/stage.py", "auditory_st/features.py", "auditory_st/events.py",
                "auditory_d2/data.py", "auditory_d2/spectral.py", "auditory_dv/audit.py")


def load_config(relative: str = CONFIG_DEFAULT) -> dict:
    config = pfr.load_config(relative)            # adds _path, _sha256 and _protocol_sha256 (project.protocol)
    config["_document_sha256"] = {key: (digest(ROOT / config["project"][key]) if (ROOT / config["project"][key]).exists()
                                        else None)
                                  for key in ("research_document", "execution_document", "server_plan")}
    return config


def source_hashes() -> dict:
    out = {f"auditory_nextmap/{p.name}": digest(p) for p in sorted(PACKAGE.glob("*.py"))}
    for dep in DEPENDENCIES:
        p = ROOT / dep
        if p.exists():
            out[dep] = digest(p)
    return out


def ledger_event(config: dict, payload: dict) -> None:
    """Append one line to the private job ledger (small O_APPEND writes; one line per event)."""
    path = ROOT / cfg(config, "paths.private_relative") / "job_ledger.jsonl"
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    line = json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "job": job_tag(),
                       "partition": os.environ.get("SLURM_JOB_PARTITION"), "qos": os.environ.get("SLURM_JOB_QOS"),
                       **payload}, ensure_ascii=False, sort_keys=True, default=str)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, (line + "\n").encode("utf-8"))
    finally:
        os.close(fd)


def open_run(command: str, run: str, config: dict, *, args: dict | None = None) -> dict:
    ctx = pfr.open_run(command, run, config, args=args)
    write_json_atomic(ctx["private"] / "receipts" / f"{command}_{job_tag()}_nextmap_sources.json",
                      {"sources": source_hashes(), "documents": config.get("_document_sha256"),
                       "protocol_sha256": config.get("_protocol_sha256")}, private=True)
    ledger_event(config, {"event": "start", "command": command, "run": run})
    return ctx


def close_run(config: dict, command: str, run: str, status: str, **extra) -> None:
    ledger_event(config, {"event": "end", "command": command, "run": run, "status": status, **extra})


def require_protocol(config: dict) -> None:
    """Analyses that compare models run only after the protocol file is frozen (read-only, hash in receipts)."""
    path = ROOT / config["project"]["protocol"]
    if not path.exists():
        raise ProvenanceError("PROTOCOL_NOT_FROZEN: write docs/auditory_nextmap/NEXTMAP_PROTOCOL_FROZEN.md first")
    if os.access(path, os.W_OK):
        raise ProvenanceError("PROTOCOL_WRITABLE: freeze the protocol (chmod a-w) before comparison runs")


def refuse_existing(path: Path) -> None:
    if Path(path).exists():
        raise ProvenanceError(f"REFUSE_OVERWRITE:{path}")


def _tmp_beside(path: Path) -> Path:
    import tempfile
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    os.close(fd)
    return Path(tmp)


def write_parquet_atomic(frame, path: Path) -> Path:
    tmp = _tmp_beside(path)
    frame.to_parquet(tmp, index=False)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return Path(path)


def write_jsonl_atomic(rows, path: Path) -> Path:
    tmp = _tmp_beside(path)
    with open(tmp, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, default=_jsonable) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return Path(path)


def _jsonable(obj):
    import numpy as np
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)
