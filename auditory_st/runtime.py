"""Run creation, provenance and guarded output for auditory_st. Slurm only.

Reuses the FN1 runtime helpers (digest, write_json, environment_record, require_slurm,
ProvenanceError) so that receipts follow the same shape as earlier rounds.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import yaml

from auditory_fn1.runtime import (  # noqa: F401  (re-exported)
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
CONFIG_DEFAULT = "configs/auditory_st_v1.yaml"


def load_config(relative: str = CONFIG_DEFAULT) -> dict:
    path = ROOT / relative
    if not path.is_file():
        raise ProvenanceError(f"CONFIG_MISSING:{relative}")
    config = yaml.safe_load(path.read_text())
    config["_path"] = str(relative)
    config["_sha256"] = digest(path)
    return config


def cfg(config: dict, dotted: str):
    """Read a frozen config value; deliberately no default."""
    node = config
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node:
            raise ProvenanceError(f"CONFIG_KEY_MISSING:{dotted}")
        node = node[key]
    return node


def source_path(config: dict, name: str) -> Path:
    relative = cfg(config, f"sources.{name}")
    path = ROOT / relative
    if not path.exists():
        raise ProvenanceError(f"SOURCE_MISSING:{name}:{relative}")
    return path


def private_dir(config: dict, run: str) -> Path:
    return ROOT / cfg(config, "paths.private_relative") / run


def results_dir(config: dict, run: str) -> Path:
    return ROOT / cfg(config, "paths.results_relative") / run


def _snapshot(destination: Path, config_relative: str) -> dict[str, str]:
    snapshot = destination / "source"
    snapshot.mkdir(mode=0o700, parents=True, exist_ok=False)
    hashes: dict[str, str] = {}
    target_dir = snapshot / "auditory_st"
    target_dir.mkdir(mode=0o700, exist_ok=False)
    for module in sorted(PACKAGE.glob("*.py")):
        target = target_dir / module.name
        shutil.copyfile(module, target)
        target.chmod(0o600)
        hashes[f"auditory_st/{module.name}"] = digest(module)
    for extra in (config_relative,):
        source = ROOT / extra
        target = snapshot / Path(extra).name
        shutil.copyfile(source, target)
        target.chmod(0o600)
        hashes[extra] = digest(source)
    return hashes


def create_run(command: str, run: str, config: dict, *, args: dict | None = None,
               allow_existing: bool = False) -> dict:
    """Create private/results run directories, snapshot sources, write start receipt.

    Array jobs share one run: the first task creates it, later tasks attach
    (allow_existing=True) and write their own start receipt under receipts/.
    """
    job = require_slurm()
    private = private_dir(config, run)
    public = results_dir(config, run)
    task = os.environ.get("SLURM_ARRAY_TASK_ID")
    created = False
    if private.exists() or public.exists():
        if not allow_existing:
            raise ProvenanceError(f"RUN_OCCUPIED:{private.relative_to(ROOT)}")
    else:
        try:
            private.mkdir(mode=0o700, parents=True, exist_ok=False)
            created = True
        except FileExistsError:
            # Array tasks start together: another task created the run a moment ago.
            if not allow_existing:
                raise ProvenanceError(f"RUN_OCCUPIED:{private.relative_to(ROOT)}")
    if created:
        public.mkdir(mode=0o755, parents=True, exist_ok=True)
        hashes = _snapshot(private, str(config["_path"]))
        plan = ROOT / cfg(config, "project.plan_file")
        start = {
            "command": command, "run": run, "job_id": job,
            "config_path": str(config["_path"]), "config_sha256": config["_sha256"],
            "plan_sha256": digest(plan) if plan.is_file() else None,
            "source_hashes": hashes, "environment": environment_record(), "args": args or {},
        }
        write_json(private / "start.json", start, private=True)
    receipts = private / "receipts"
    receipts.mkdir(mode=0o700, exist_ok=True)
    suffix = f"_task{task}" if task is not None else ""
    # Every attach records the hashes of the code actually executing, so a run whose source
    # changed between commands stays traceable (the start.json snapshot is the first command's).
    current = {f"auditory_st/{m.name}": digest(m) for m in sorted(PACKAGE.glob("*.py"))}
    write_json(receipts / f"{command}{suffix}_{job}.json",
               {"command": command, "job_id": job, "array_task": task, "args": args or {},
                "config_sha256": config["_sha256"], "source_hashes_at_attach": current,
                "environment": environment_record()},
               private=True)
    return {"private": private, "public": public, "job": job}


def array_slice(items: list, *, env_task: str = "SLURM_ARRAY_TASK_ID",
                env_count: str = "SLURM_ARRAY_TASK_COUNT") -> list:
    task = int(os.environ.get(env_task, 0))
    count = int(os.environ.get(env_count, 1))
    return items[task::count]


def read_json(path: Path):
    return json.loads(Path(path).read_text())


def finish(private: Path, command: str, payload: dict) -> None:
    job = os.environ.get("SLURM_JOB_ID", "nojob")
    task = os.environ.get("SLURM_ARRAY_TASK_ID")
    suffix = f"_task{task}" if task is not None else ""
    write_json(private / "receipts" / f"{command}{suffix}_{job}_done.json", payload, private=True)
