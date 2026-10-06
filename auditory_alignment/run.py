"""Run one planned fit unit end to end (spec §15.3).

Usage: python -m auditory_alignment.run --manifest <planned_jobs.jsonl> --job-index <i> [--epochs N] [--out DIR]
Writes <out>/units/<experiment_id>.json (per-participant results, curves, calibration; private) and checkpoints under
<out>/ckpt/. A unit whose result file exists is skipped (preemption-safe).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import time
import traceback

import numpy as np
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "private", "auditory_alignment_kernel_cs")


UNIT_CODE = ("data.py", "evaluate.py", "losses.py", "losses_reference.py", "model.py", "run.py", "train.py")


def code_hash():
    """Hash of the files that determine a unit's result (aggregation / manifest scripts excluded)."""
    h = hashlib.sha256()
    for f in UNIT_CODE:
        h.update(open(os.path.join(REPO, "auditory_alignment", f), "rb").read())
    return h.hexdigest()[:16]


def load_job(manifest, index=None, experiment_id=None):
    with open(manifest) as f:
        for i, line in enumerate(f):
            j = json.loads(line)
            if (index is not None and i == index) or (experiment_id is not None and j["experiment_id"] == experiment_id):
                return j
    raise SystemExit("job not found")


def run_job(job, out=OUT, epochs=None):
    from . import data, evaluate, train
    os.makedirs(os.path.join(out, "units"), exist_ok=True); os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    res_path = os.path.join(out, "units", f"{job['experiment_id']}.json")
    if os.path.exists(res_path):
        print("skip", job["experiment_id"]); return
    if epochs is not None:
        job = json.loads(json.dumps(job)); job["config"]["epochs_initial"] = epochs
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    t0 = time.time()
    rec = {"job": job, "code_hash": code_hash(), "config_hash": hashlib.sha256(json.dumps(job["config"], sort_keys=True).encode()).hexdigest()[:16],
           "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu", "status": "running"}
    ckpt = os.path.join(out, "ckpt", job["experiment_id"])
    ds = job["dataset"]
    try:
        if ds == "private_bdf":
            kids = data.load_private()
            rec["load_seconds"] = round(time.time() - t0, 1)
            enc, bt = train.fit_private(job, kids, dev, ckpt, rec)
            rec["eval"] = evaluate.evaluate_private(enc, bt, job, rec["objective_calibration"])
        else:
            if ds == "fau":
                coh = data.load_fau(job["content_fold"], kinds=("ss", "cs"))
            elif ds == "dtu":
                coh = data.load_dtu(job["content_fold"], kinds=("ss", "cs"))
            else:
                coh = data.load_federici()
            rec["load_seconds"] = round(time.time() - t0, 1)
            rec["cohort"] = {"n_participants": len(coh.participants), "n_segments": len(coh.segments), "fs": coh.fs, "n_ch": coh.n_ch}
            enc, aud, bt = train.fit_continuous(job, coh, dev, ckpt, rec)
            rec["eval"] = evaluate.evaluate_continuous(job["objective"], enc, aud, bt, coh, job, np.random.default_rng(job["seed"] + 1000),
                                                       rec["objective_calibration"])
        rec["status"] = "complete"
    except Exception as ex:  # a failed unit is recorded as failed, never as a scientific null
        rec["status"] = "failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    rec["total_seconds"] = round(time.time() - t0, 1)
    if torch.cuda.is_available():
        rec["gpu_peak_allocated_mb"] = round(torch.cuda.max_memory_allocated() / 2 ** 20)
        rec["gpu_peak_reserved_mb"] = round(torch.cuda.max_memory_reserved() / 2 ** 20)
    path = res_path if rec["status"] == "complete" else res_path.replace(".json", ".FAILED.json")
    json.dump(rec, open(path + ".tmp", "w"), default=float); os.replace(path + ".tmp", path)
    print(job["experiment_id"], rec["status"], rec["total_seconds"], rec.get("error", ""), flush=True)
    if rec["status"] != "complete":
        raise SystemExit(1)


def reeval_job(job, src, out):
    """Evaluation-only rerun of a fitted unit (same best checkpoint and calibration, current evaluation code)."""
    from . import data, evaluate, train
    os.makedirs(os.path.join(out, "units"), exist_ok=True)
    srec = json.load(open(os.path.join(src, "units", f"{job['experiment_id']}.json")))
    job = srec["job"]
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    t0 = time.time()
    rec = {k: v for k, v in srec.items() if k != "eval"}
    rec.update({"reeval_of": src, "reeval_code_hash": code_hash()})
    ck = os.path.join(src, "ckpt", f"{job['experiment_id']}_best.pt")
    if job["dataset"] == "private_bdf":
        enc, bt = train.load_private_unit(job, data.load_private(), dev, ck)
        rec["eval"] = evaluate.evaluate_private(enc, bt, job, rec["objective_calibration"])
    else:
        coh = {"fau": lambda: data.load_fau(job["content_fold"], kinds=("ss", "cs")), "dtu": lambda: data.load_dtu(job["content_fold"], kinds=("ss", "cs")),
               "federici": data.load_federici}[job["dataset"]]()
        enc, aud, bt = train.load_continuous(job, coh, dev, ck)
        rec["eval"] = evaluate.evaluate_continuous(job["objective"], enc, aud, bt, coh, job, np.random.default_rng(job["seed"] + 1000),
                                                   rec["objective_calibration"])
    rec["reeval_seconds"] = round(time.time() - t0, 1)
    path = os.path.join(out, "units", f"{job['experiment_id']}.json")
    json.dump(rec, open(path + ".tmp", "w"), default=float); os.replace(path + ".tmp", path)
    print("reeval", job["experiment_id"], rec["reeval_seconds"], flush=True)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--manifest", required=True); a.add_argument("--job-index", type=int); a.add_argument("--experiment-id")
    a.add_argument("--epochs", type=int); a.add_argument("--out", default=OUT)
    a.add_argument("--reeval-from", help="evaluation-only rerun of the unit fitted under this output directory")
    args = a.parse_args()
    job = load_job(args.manifest, args.job_index, args.experiment_id)
    if args.reeval_from:
        reeval_job(job, args.reeval_from, args.out)
    else:
        run_job(job, args.out, args.epochs)


if __name__ == "__main__":
    main()
