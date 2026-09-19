"""D1 export runner. Slurm only. Real EEG derivatives stay under private/."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / "private/auditory_d1"
RESULTS = ROOT / "results/auditory_d1"


def build_plan(args) -> dict:
    index = pd.read_csv(ROOT / "manifests/mff_export_index.csv", low_memory=False)
    level = index["data_level"].astype(str).str.contains("continuous", case=False, na=False)
    ok = index["read_status"].astype(str) == "ok"
    rate_ok = index["sampling_rate_hz"].isin([250.0, 500.0, 1000.0])
    long_enough = pd.to_numeric(index["stored_time_s"], errors="coerce") >= 60.0
    selected = index[level & ok & rate_ok & long_enough].copy()
    selected = selected.sort_values("container_id")
    rows = [{"container_id": str(r.container_id),
             "candidate_acquisition_id": str(r.candidate_acquisition_id),
             "sampling_rate_hz": float(r.sampling_rate_hz),
             "n_signal_channels": int(r.n_signal_channels),
             "stored_time_s": float(r.stored_time_s)} for r in selected.itertuples()]
    PRIVATE.mkdir(parents=True, exist_ok=True)
    plan_path = PRIVATE / f"{args.run}_plan.json"
    plan_path.write_text(json.dumps(rows, indent=2) + "\n")
    plan_path.chmod(0o600)
    excluded = {
        "not_continuous": int((~level).sum()),
        "read_status_not_ok": int((level & ~ok).sum()),
        "unsupported_rate": int((level & ok & ~rate_ok).sum()),
        "shorter_than_60s": int((level & ok & rate_ok & ~long_enough).sum()),
    }
    summary = {"run": args.run, "selected": len(rows), "excluded": excluded,
               "total_hours": round(float(selected["stored_time_s"].sum()) / 3600.0, 2),
               "rates": {str(k): int(v) for k, v in selected["sampling_rate_hz"].value_counts().items()},
               "channels": {str(k): int(v) for k, v in selected["n_signal_channels"].value_counts().items()},
               "distinct_acquisitions": int(selected["candidate_acquisition_id"].nunique())}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{args.run}_plan_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n")
    (RESULTS / f"{args.run}_plan_summary.json").chmod(0o644)
    return summary


def build_bdf_plan(args) -> dict:
    from auditory_d1 import export_bdf

    rows = export_bdf.signal_records(ROOT)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    plan_path = PRIVATE / f"{args.run}_plan.json"
    plan_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    plan_path.chmod(0o600)
    summary = {"run": args.run, "branch": "bdf", "selected": len(rows),
               "total_hours": round(sum(r["duration_s"] for r in rows) / 3600.0, 2),
               "distinct_acquisitions": len({r["candidate_acquisition_id"] for r in rows})}
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{args.run}_plan_summary.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    out.chmod(0o644)
    return summary


def export_bdf_slice(args) -> dict:
    from auditory_d1 import export_bdf

    plan = json.loads((PRIVATE / f"{args.run}_plan.json").read_text())
    task = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))
    count = int(os.environ.get("SLURM_ARRAY_TASK_COUNT", 1))
    mine = plan[task::count]
    destination = PRIVATE / args.run / "arrays"
    receipts = PRIVATE / args.run / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    done, failed, skipped = 0, 0, 0
    for entry in mine:
        receipt = receipts / f"{entry['container_id']}.json"
        if receipt.exists():
            skipped += 1
            continue
        started = time.time()
        try:
            payload = export_bdf.export_record(ROOT, entry, destination)
            payload["elapsed_s"] = round(time.time() - started, 1)
            done += 1
        except Exception as exc:
            payload = {"container_id": entry["container_id"], "status": "D1_EXPORT_FAILED",
                       "error_class": type(exc).__name__, "error": str(exc)[:400],
                       "traceback_tail": traceback.format_exc()[-800:]}
            failed += 1
        receipt.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        receipt.chmod(0o600)
    return {"task": task, "of": count, "assigned": len(mine),
            "exported": done, "failed": failed, "already_done": skipped}


def export_slice(args) -> dict:
    from auditory_d1 import export

    plan = json.loads((PRIVATE / f"{args.run}_plan.json").read_text())
    task = int(os.environ["SLURM_ARRAY_TASK_ID"])
    count = int(os.environ["SLURM_ARRAY_TASK_COUNT"])
    mine = plan[task::count]
    destination = PRIVATE / args.run / "arrays"
    receipts = PRIVATE / args.run / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    done, failed, skipped = 0, 0, 0
    for row in mine:
        container = row["container_id"]
        receipt = receipts / f"{container}.json"
        if receipt.exists():
            skipped += 1
            continue
        started = time.time()
        try:
            payload = export.export_container(ROOT, container, destination)
            payload["elapsed_s"] = round(time.time() - started, 1)
            done += 1
        except Exception as exc:  # recorded, never silently dropped
            payload = {"container_id": container, "status": "D1_EXPORT_FAILED",
                       "error_class": type(exc).__name__, "error": str(exc)[:400],
                       "traceback_tail": traceback.format_exc()[-800:],
                       "elapsed_s": round(time.time() - started, 1)}
            failed += 1
        receipt.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        receipt.chmod(0o600)
    return {"task": task, "of": count, "assigned": len(mine),
            "exported": done, "failed": failed, "already_done": skipped}


def collect(args) -> dict:
    receipts = sorted((PRIVATE / args.run / "receipts").glob("*.json"))
    rows = [json.loads(p.read_text()) for p in receipts]
    ok = [r for r in rows if r.get("status") == "D1_EXPORTED"]
    summary = {
        "run": args.run, "receipts": len(rows), "exported": len(ok),
        "failed": sum(1 for r in rows if r.get("status") == "D1_EXPORT_FAILED"),
        "no_usable_interval": sum(1 for r in rows if r.get("status") == "D1_NO_USABLE_INTERVAL"),
        "error_classes": {},
        "total_hours": round(sum(r["seconds"] for r in ok) / 3600.0, 2) if ok else 0.0,
        "channels": {}, "rates": {},
        "nonfinite_total": sum(r.get("nonfinite_samples", 0) for r in ok),
    }
    for r in rows:
        if r.get("status") == "D1_EXPORT_FAILED":
            key = r.get("error_class", "unknown")
            summary["error_classes"][key] = summary["error_classes"].get(key, 0) + 1
    for r in ok:
        summary["channels"][str(r["n_channels"])] = summary["channels"].get(str(r["n_channels"]), 0) + 1
        summary["rates"][str(r["rate_hz"])] = summary["rates"].get(str(r["rate_hz"]), 0) + 1
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{args.run}_export_summary.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    out.chmod(0o644)
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="auditory_d1")
    parser.add_argument("command", choices=["plan", "export", "collect",
                                            "plan-bdf", "export-bdf"])
    parser.add_argument("--run", required=True)
    args = parser.parse_args(argv)
    assert os.environ.get("SLURM_JOB_ID"), "Slurm only"
    os.umask(0o077)
    result = {"plan": build_plan, "export": export_slice, "collect": collect,
              "plan-bdf": build_bdf_plan, "export-bdf": export_bdf_slice}[args.command](args)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
