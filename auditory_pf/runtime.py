"""Run bookkeeping for auditory_pf: requeue-safe receipts, atomic outputs, done markers.

Jobs run under --qos=runfill (preemptible, PreemptMode=REQUEUE). A requeued job keeps its
SLURM_JOB_ID, so receipts carry SLURM_RESTART_COUNT, every unit is written atomically
(tmp file + rename) and units that already have a done marker are skipped.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import yaml

from auditory_st.runtime import ROOT  # noqa: F401  (project root)

PACKAGE = Path(__file__).resolve().parent
CONFIG_DEFAULT = "configs/auditory_pf_v1.yaml"


class ProvenanceError(RuntimeError):
    pass


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_config(relative: str = CONFIG_DEFAULT) -> dict:
    path = ROOT / relative
    config = yaml.safe_load(path.read_text())
    config["_path"] = relative
    config["_sha256"] = digest(path)
    protocol = ROOT / config["project"]["protocol"]
    config["_protocol_sha256"] = digest(protocol) if protocol.exists() else None
    return config


def cfg(config: dict, dotted: str):
    node = config
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node:
            raise ProvenanceError(f"CONFIG_KEY_MISSING:{dotted}")
        node = node[key]
    return node


def private_dir(config: dict, run: str) -> Path:
    return ROOT / cfg(config, "paths.private_relative") / run


def results_dir(config: dict, run: str) -> Path:
    return ROOT / cfg(config, "paths.results_relative") / run


def require_slurm() -> str:
    job = os.environ.get("SLURM_JOB_ID")
    if not job:
        raise ProvenanceError("SLURM_REQUIRED: numerical work runs as a Slurm job (AGENTS.md)")
    return job


def job_tag() -> str:
    job = os.environ.get("SLURM_ARRAY_JOB_ID") or os.environ.get("SLURM_JOB_ID", "nojob")
    task = os.environ.get("SLURM_ARRAY_TASK_ID")
    restart = os.environ.get("SLURM_RESTART_COUNT", "0")
    sub = os.environ.get("PF_SUB")
    return f"{job}" + (f"_{task}" if task is not None else "") + f"_r{restart}" + (f"_w{sub}" if sub is not None else "")


def environment_record() -> dict:
    import platform
    out = {"python": platform.python_version(), "node": os.environ.get("SLURMD_NODENAME"),
           "gpu": os.environ.get("CUDA_VISIBLE_DEVICES"), "partition": os.environ.get("SLURM_JOB_PARTITION"),
           "qos": os.environ.get("SLURM_JOB_QOS")}
    try:
        import torch
        out["torch"] = torch.__version__
        if torch.cuda.is_available():
            out["gpu_name"] = torch.cuda.get_device_name(0)
    except Exception:  # noqa: BLE001  (receipt only)
        pass
    return out


def source_hashes() -> dict:
    out = {f"auditory_pf/{p.name}": digest(p) for p in sorted(PACKAGE.glob("*.py"))}
    for dep in ("auditory_gx/data.py", "auditory_gx/train.py", "auditory_gx/models.py", "auditory_d2/spectral.py",
                "auditory_d2/data.py"):
        p = ROOT / dep
        if p.exists():
            out[dep] = digest(p)
    return out


def open_run(command: str, run: str, config: dict, *, args: dict | None = None) -> dict:
    """Create or attach to a run directory; write one receipt per (job, task, restart)."""
    require_slurm()
    private, public = private_dir(config, run), results_dir(config, run)
    private.mkdir(mode=0o700, parents=True, exist_ok=True)
    public.mkdir(mode=0o755, parents=True, exist_ok=True)
    for p in (public, public.parent):
        try:
            p.chmod(0o755)
        except OSError:
            pass
    receipts = private / "receipts"
    receipts.mkdir(mode=0o700, exist_ok=True)
    payload = {"command": command, "run": run, "job": job_tag(), "args": args or {},
               "config": config["_path"], "config_sha256": config["_sha256"],
               "protocol_sha256": config.get("_protocol_sha256"), "source_hashes": source_hashes(),
               "environment": environment_record()}
    write_json_atomic(receipts / f"{command}_{job_tag()}.json", payload, private=True)
    return {"private": private, "public": public}


def _atomic_target(path: Path) -> tuple[int, str]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))


def write_json_atomic(path: Path, payload, *, private: bool) -> Path:
    path = Path(path)
    fd, tmp = _atomic_target(path)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True, default=_default) + "\n")
    os.chmod(tmp, 0o600 if private else 0o644)
    os.replace(tmp, path)
    return path


def save_npz_atomic(path: Path, **arrays) -> Path:
    path = Path(path)
    fd, tmp = _atomic_target(path)
    os.close(fd)
    with open(tmp, "wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return path


def write_csv_atomic(frame, path: Path, *, private: bool) -> Path:
    path = Path(path)
    fd, tmp = _atomic_target(path)
    os.close(fd)
    frame.to_csv(tmp, index=False)
    os.chmod(tmp, 0o600 if private else 0o644)
    os.replace(tmp, path)
    return path


def read_json(path: Path):
    return json.loads(Path(path).read_text())


def _default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(type(obj))


def unit_done(marker: Path) -> bool:
    return Path(marker).exists()


def mark_done(marker: Path, payload: dict | None = None) -> None:
    write_json_atomic(marker, {"job": job_tag(), **(payload or {})}, private=True)


def task_units(units: list, *, env_task: str = "SLURM_ARRAY_TASK_ID", env_count: str = "SLURM_ARRAY_TASK_COUNT") -> list:
    """Units for this array task (and optional worker PF_SUB of PF_NSUB on the same GPU): strided, deterministic."""
    task = os.environ.get(env_task)
    sub, nsub = int(os.environ.get("PF_SUB", "0")), int(os.environ.get("PF_NSUB", "1"))
    if task is None:
        if nsub == 1:
            return list(units)
        return [u for i, u in enumerate(units) if i % nsub == sub]
    count = int(os.environ.get(env_count) or (int(os.environ.get("SLURM_ARRAY_TASK_MAX", task)) + 1))
    slot, n_slots = int(task) * nsub + sub, count * nsub
    return [u for i, u in enumerate(units) if i % n_slots == slot]


def stable_int(*parts) -> int:
    text = "|".join(str(p) for p in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)
