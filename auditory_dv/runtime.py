"""Run bookkeeping for auditory_dv: auditory_pf's requeue-safe runtime plus auditory_dv source hashes."""
from __future__ import annotations

from pathlib import Path

from auditory_pf import runtime as pfr
from auditory_pf.runtime import (ROOT, cfg, digest, job_tag, load_config, mark_done, private_dir, read_json,  # noqa: F401
                                 results_dir, save_npz_atomic, stable_int, task_units, unit_done, write_csv_atomic,
                                 write_json_atomic)

PACKAGE = Path(__file__).resolve().parent
CONFIG_DEFAULT = "configs/auditory_dv_v1.yaml"


def open_run(command: str, run: str, config: dict, *, args: dict | None = None) -> dict:
    ctx = pfr.open_run(command, run, config, args=args)
    write_json_atomic(ctx["private"] / "receipts" / f"{command}_{job_tag()}_dv_sources.json",
                      {f"auditory_dv/{p.name}": digest(p) for p in sorted(PACKAGE.glob("*.py"))}, private=True)
    return ctx
