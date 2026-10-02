"""Run bookkeeping for auditory_story: auditory_pf's requeue-safe runtime, story source hashes and a job ledger.

Jobs run under --qos=runfill (preemptible, PreemptMode=REQUEUE). Units are written atomically with done markers, so
a requeued job skips finished units; representation training resumes from its last 100-step checkpoint.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

from auditory_pf import runtime as pfr
from auditory_pf.runtime import (ROOT, ProvenanceError, cfg, digest, job_tag, mark_done, private_dir, read_json,  # noqa: F401
                                 require_slurm, results_dir, save_npz_atomic, stable_int, task_units, unit_done,
                                 write_csv_atomic, write_json_atomic)

PACKAGE = Path(__file__).resolve().parent
CONFIG_DEFAULT = "configs/auditory_story_v1.yaml"
DEPENDENCIES = ("auditory_pf/cohort.py", "auditory_pf/runtime.py", "auditory_nextmap/adapters.py",
                "auditory_nextmap/runtime.py", "auditory_st/runtime.py", "auditory5/events.py", "auditory_st/events.py")
PACKAGE_DOCS = ("story_file", "execution_file", "method_file")


def load_config(relative: str = CONFIG_DEFAULT) -> dict:
    config = pfr.load_config(relative)            # adds _path, _sha256 and _protocol_sha256 (project.protocol)
    config["_package_sha256"] = {key: (digest(ROOT / config["project"][key]) if (ROOT / config["project"][key]).exists()
                                       else None) for key in PACKAGE_DOCS}
    return config


def source_hashes() -> dict:
    out = {f"auditory_story/{p.name}": digest(p) for p in sorted(PACKAGE.glob("*.py"))}
    for dep in DEPENDENCIES:
        p = ROOT / dep
        if p.exists():
            out[dep] = digest(p)
    return out


def code_hash() -> str:
    import hashlib
    h = hashlib.sha256()
    for k, v in sorted(source_hashes().items()):
        h.update(f"{k}:{v}\n".encode())
    return h.hexdigest()


def ledger_event(config: dict, payload: dict) -> None:
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
    write_json_atomic(ctx["private"] / "receipts" / f"{command}_{job_tag()}_story_sources.json",
                      {"sources": source_hashes(), "code_hash": code_hash(), "package": config.get("_package_sha256"),
                       "protocol_sha256": config.get("_protocol_sha256")}, private=True)
    ledger_event(config, {"event": "start", "command": command, "run": run})
    return ctx


def close_run(config: dict, command: str, run: str, status: str, **extra) -> None:
    ledger_event(config, {"event": "end", "command": command, "run": run, "status": status, **extra})


def require_protocol(config: dict) -> None:
    """Comparison runs start only after the protocol file is frozen (read-only; its hash enters every receipt)."""
    path = ROOT / config["project"]["protocol"]
    if not path.exists():
        raise ProvenanceError("PROTOCOL_NOT_FROZEN: write docs/auditory_story/PROTOCOL.md first")
    if os.access(path, os.W_OK):
        raise ProvenanceError("PROTOCOL_WRITABLE: chmod a-w docs/auditory_story/PROTOCOL.md before comparison runs")


def _tmp_beside(path: Path) -> Path:
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


def append_jsonl(path: Path, row: dict) -> None:
    """One private JSON line (O_APPEND); used for the fit ledger."""
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, (json.dumps(row, sort_keys=True, ensure_ascii=False, default=_jsonable) + "\n").encode("utf-8"))
    finally:
        os.close(fd)


def torch_save_atomic(obj, path: Path) -> Path:
    import torch
    tmp = _tmp_beside(path)
    torch.save(obj, tmp)
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


def hash_ids(ids) -> str:
    """Order-free hash of a set of child indices (scope hashes in the fit ledger; values never printed)."""
    import hashlib
    return hashlib.sha256(",".join(str(int(i)) for i in sorted(set(int(x) for x in ids))).encode()).hexdigest()[:16]
