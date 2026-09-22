"""Run bookkeeping for auditory_gx (shares helpers with auditory_st / auditory_fn1)."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

from auditory_fn1.runtime import ProvenanceError, digest, environment_record, require_slurm, write_json  # noqa: F401
from auditory_st.runtime import ROOT, array_slice, read_json  # noqa: F401

PACKAGE = Path(__file__).resolve().parent
CONFIG_DEFAULT = "configs/auditory_gx_v1.yaml"


def load_config(relative: str = CONFIG_DEFAULT) -> dict:
    path = ROOT / relative
    config = yaml.safe_load(path.read_text())
    config["_path"] = relative
    config["_sha256"] = digest(path)
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


def open_run(command: str, run: str, config: dict, *, args: dict | None = None) -> dict:
    """Create (or attach to) a run; array tasks and re-submissions attach. Receipts per job."""
    job = require_slurm()
    private, public = private_dir(config, run), results_dir(config, run)
    created = False
    try:
        private.mkdir(mode=0o700, parents=True, exist_ok=False)
        created = True
    except FileExistsError:
        pass
    public.mkdir(mode=0o755, parents=True, exist_ok=True)
    for p in (public, public.parent):
        try:
            p.chmod(0o755)          # mkdir's mode is masked by the 077 umask; results must stay readable
        except OSError:
            pass
    receipts = private / "receipts"
    receipts.mkdir(mode=0o700, exist_ok=True)
    task = os.environ.get("SLURM_ARRAY_TASK_ID")
    suffix = f"_task{task}" if task is not None else ""
    hashes = {f"auditory_gx/{m.name}": digest(m) for m in sorted(PACKAGE.glob("*.py"))}
    write_json(receipts / f"{command}{suffix}_{job}.json",
               {"command": command, "run": run, "job_id": job, "array_task": task, "args": args or {},
                "config_sha256": config["_sha256"], "source_hashes": hashes, "created": created,
                "environment": environment_record(),
                "gpu": os.environ.get("CUDA_VISIBLE_DEVICES"), "node": os.environ.get("SLURMD_NODENAME")},
               private=True)
    return {"private": private, "public": public, "job": job}


def write_json_overwrite(path: Path, payload, *, private: bool) -> Path:
    """Run outputs that a legitimate re-run may replace (receipts stay exclusive-create)."""
    import json as _json
    path = Path(path)
    path.write_text(_json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True, default=str) + "\n", encoding="utf-8")
    path.chmod(0o600 if private else 0o644)
    return path


def done(private: Path, command: str, payload: dict) -> None:
    job = os.environ.get("SLURM_JOB_ID", "nojob")
    task = os.environ.get("SLURM_ARRAY_TASK_ID")
    suffix = f"_task{task}" if task is not None else ""
    write_json(private / "receipts" / f"{command}{suffix}_{job}_done.json", payload, private=True)


def chmod_private(path: Path) -> None:
    for p in path.rglob("*"):
        try:
            p.chmod(0o700 if p.is_dir() else 0o600)
        except OSError:
            pass
