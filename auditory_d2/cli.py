"""D2 runner. Slurm only. GPU for training; aggregates public, everything else private."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / "private/auditory_d2"
RESULTS = ROOT / "results/auditory_d2"


def _write(path: Path, payload, *, private: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    path.chmod(0o600 if private else 0o644)


def geometry(args) -> dict:
    """One electrode layout per distinct layout hash, read from a single source each."""
    if args.run.startswith("D1_bdf"):
        from auditory5.adapters.mff import standard_1020_head_positions
        from auditory5.preprocessing import HA_CHANNELS

        positions = standard_1020_head_positions(HA_CHANNELS)
        out = {"bdf_ha20": {"n_channels": len(HA_CHANNELS),
                            "n_with_geometry": len(HA_CHANNELS),
                            "channels": list(HA_CHANNELS),
                            "xyz_m": [list(map(float, row)) for row in positions],
                            "sensor_net": "clinical_10_20_22ch_scalp_subset"}}
        _write(PRIVATE / f"{args.run}_geometry.json", out, private=True)
        return {"run": args.run, "layouts": {"bdf_ha20": {
            "n_channels": len(HA_CHANNELS), "n_with_geometry": len(HA_CHANNELS),
            "sensor_net": "clinical_10_20_22ch_scalp_subset", "records": None}}}
    from auditory5.adapters import mff
    from auditory_d1 import export as d1_export
    from auditory_d2 import cohort as d2_cohort

    receipts = d2_cohort.d1_receipts(ROOT, args.run)
    paths = d1_export.registry(ROOT)
    layouts: dict[str, str] = {}
    for container, receipt in receipts.items():
        key = str(receipt.get("layout_hash"))
        layouts.setdefault(key, container)
    out = {}
    for key, container in layouts.items():
        metadata = mff.inspect_source(paths[container])
        names = d1_export.retained_channels(metadata)
        position = {row["channel_name"]: row.get("xyz_m") for row in metadata["geometry"]}
        usable = [n for n in names if position.get(n) is not None
                  and np.isfinite(np.asarray(position[n], dtype=float)).all()]
        out[key] = {"n_channels": len(names), "n_with_geometry": len(usable),
                    "channels": names,
                    "xyz_m": [list(map(float, position[n])) if n in usable else None for n in names],
                    "sensor_net": metadata.get("sensor_net")}
    _write(PRIVATE / f"{args.run}_geometry.json", out, private=True)
    return {"run": args.run, "layouts": {k: {"n_channels": v["n_channels"],
                                             "n_with_geometry": v["n_with_geometry"],
                                             "sensor_net": v["sensor_net"],
                                             "records": sum(1 for r in receipts.values()
                                                            if str(r.get("layout_hash")) == k)}
                                         for k, v in out.items()}}


def build_cohort(args) -> dict:
    from auditory_d2 import cohort as d2_cohort

    builder = d2_cohort.bdf_labelled if args.run.startswith("D1_bdf") else d2_cohort.mff_labelled
    built = builder(ROOT, args.run)
    _write(PRIVATE / f"{args.run}_cohort.json", built, private=True)
    summary = d2_cohort.summarise(built)
    _write(RESULTS / f"{args.run}_cohort_summary.json", summary, private=False)
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="auditory_d2")
    parser.add_argument("command", choices=["geometry", "cohort", "budget", "spectral-budget", "ridge-budget", "paired", "selfsup", "clinical", "compare", "select", "transfer", "ablate"])
    parser.add_argument("--run", default="D1_mff_001")
    parser.add_argument("--out", default=None)
    parser.add_argument("--budgets", default="1,2,4,8,16,32,64,128")
    parser.add_argument("--variants", type=int, default=3)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--bins", type=int, default=8)
    parser.add_argument("--steps", type=int, default=1500)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=2e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-2)
    parser.add_argument("--seed", type=int, default=20260919)
    parser.add_argument("--shuffle-control", action="store_true")
    parser.add_argument("--eval-stride", type=int, default=1)
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--blocks", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--max-bad-fraction", type=float, default=0.10)
    parser.add_argument("--min-windows", type=int, default=8)
    parser.add_argument("--max-windows", type=int, default=400)
    parser.add_argument("--readout", choices=["linear", "rbf"], default="linear")
    parser.add_argument("--compare", default=None)
    parser.add_argument("--select-budget", type=int, default=16)
    parser.add_argument("--minutes", type=float, default=None)
    parser.add_argument("--pool-limit", type=int, default=260)
    parser.add_argument("--ssl-steps", type=int, default=4000)
    parser.add_argument("--near-seconds", type=float, default=60.0)
    parser.add_argument("--far-seconds", type=float, default=300.0)
    args = parser.parse_args(argv)
    assert os.environ.get("SLURM_JOB_ID"), "Slurm only"
    os.umask(0o077)
    if args.command == "budget":
        from auditory_d2.budget import run_budget
        result = run_budget(args, ROOT, PRIVATE, RESULTS)
    elif args.command == "selfsup":
        from auditory_d2.selfsup_probe import run_selfsup_probe
        result = run_selfsup_probe(args, ROOT, PRIVATE, RESULTS)
    elif args.command == "clinical":
        from auditory_d2.clinical import run_clinical
        result = run_clinical(args, ROOT, PRIVATE, RESULTS)
    elif args.command == "select":
        from auditory_d2.select import run_select
        result = run_select(args, ROOT, PRIVATE, RESULTS)
    elif args.command == "ablate":
        from auditory_d2.ablate import run_ablate
        result = run_ablate(args, ROOT, PRIVATE, RESULTS)
    elif args.command == "transfer":
        from auditory_d2.transfer import run_transfer
        result = run_transfer(args, ROOT, PRIVATE, RESULTS)
    elif args.command == "compare":
        from auditory_d2.paired import run_compare
        result = run_compare(args, ROOT, PRIVATE, RESULTS)
    elif args.command == "paired":
        from auditory_d2.paired import run_paired
        result = run_paired(args, ROOT, PRIVATE, RESULTS)
    elif args.command == "ridge-budget":
        from auditory_d2.ridge_budget import run_ridge_budget
        result = run_ridge_budget(args, ROOT, PRIVATE, RESULTS)
    elif args.command == "spectral-budget":
        from auditory_d2.spectral_budget import run_spectral_budget
        result = run_spectral_budget(args, ROOT, PRIVATE, RESULTS)
    else:
        result = {"geometry": geometry, "cohort": build_cohort}[args.command](args)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
