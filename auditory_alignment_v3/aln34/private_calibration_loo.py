"""S34_PRIVATE frozen-checkpoint leave-self-out calibration intervention v1.

No encoder training; full original and intervened scores are retained. See the
pre-analysis note. A separate immutable plan binds all 120 source checkpoints.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np
import torch
from scipy.special import expit

from auditory_alignment_v3 import calib, core, private_stage
from auditory_alignment_v3.aln3_reference.calibration import AffineLogitCalibrator
from auditory_alignment_v3.aln34 import private_calibration_diagnosis as D

BASE = Path(core.OUT) / "aln34" / "private_calibration_loo_v1"
PLAN = BASE / "plan.json"
STORE = Path("<private checkpoint storage>/auditory_alignment_v3/aln34_private_calibration_loo_v1")
REPRO_TOL = {"nll_bits": 1e-4, "brier": 1e-5, "auc_score": 1e-4}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def source_hashes():
    files = {Path(__file__), Path(D.__file__), Path(calib.__file__), Path(private_stage.__file__), D.NOTE}
    for family in ("E_GENERIC", "E_LOCAL", "E_PUBLIC_TRANSFER"):
        files.update(Path(core.REPO) / d / f for d, f in core.FAMILY_CODE[core.FAMILY_GROUP[family]] + core.V2_DEPS)
    return {str(p.relative_to(core.REPO)): sha(p) for p in sorted(files)}


def make_plan():
    selected = D.rows()
    assert len(selected) == 120
    units = []
    for row in sorted(selected, key=lambda r: (r["seed"], r["subject_fold"], r["experiment_id"])):
        eid = row["experiment_id"]
        record = Path(core.OUT) / "units" / f"{eid}.json"
        checkpoint = Path(core.OUT) / "ckpt" / f"{eid}_best.pt"
        rec = json.loads(record.read_text())
        assert rec["status"] == "complete" and rec["row"] == row
        units.append({"row": row, "record_sha256": sha(record), "checkpoint_sha256": sha(checkpoint),
                      "recorded_device": rec["device"], "original_code_hash": rec["code_hash"]})
    body = {"version": "S34_PRIVATE_CALIBRATION_LOO_v1", "units": units, "source_sha256": source_hashes(),
            "recorded_at": datetime.now().astimezone().isoformat(), "reproduction_tolerance": REPRO_TOL,
            "result_exposure": "E v3 and stage-1 CPU diagnosis 1043948 seen; stage-2 intervention unchanged from pre-stage-1 note",
            "n_units": 120, "score_storage": str(STORE), "encoder_training": False}
    if PLAN.exists():
        previous = json.loads(PLAN.read_text())
        assert previous["source_sha256"] == body["source_sha256"] and previous["units"] == units, "frozen plan drift"
        return
    STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
    BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    score_link = BASE / "scores"
    if not score_link.exists():
        score_link.symlink_to(STORE, target_is_directory=True)
    assert score_link.resolve() == STORE
    D.write(PLAN, body)
    PLAN.chmod(0o444)
    print(f"Registered 120 frozen-checkpoint evaluations; plan SHA {sha(PLAN)}", flush=True)


def remove_self(numerator, denominator, reference_indices, reference_labels, self_weights=None):
    """Inputs contain the original kernel sum plus pseudocount; copies returned.

    Only calibration rows actually selected into the reference bank lose weight
    one and their own label. Others retain exactly their original posterior.
    """
    num, den = np.array(numerator, copy=True), np.array(denominator, copy=True)
    ix = np.asarray(reference_indices, dtype=int)
    if len(np.unique(ix)) != len(ix) or np.any(ix < 0) or np.any(ix >= len(num)):
        raise ValueError("reference selection must index distinct calibration trials")
    if len(ix) != len(reference_labels):
        raise ValueError("reference labels misaligned")
    weights = np.ones(len(ix)) if self_weights is None else np.asarray(self_weights)
    if weights.shape != ix.shape or not np.isfinite(weights).all() or np.any(weights < 0) or np.any(weights > 1+1e-12):
        raise ValueError("invalid self-kernel weights")
    num[ix] -= np.asarray(reference_labels) * weights
    den[ix] -= weights
    if np.any(den < 1 - 1e-8) or np.any(num < -1e-8) or np.any(num > den + 1e-8):
        raise ValueError("invalid leave-self-out kernel mass")
    return num, den


def kernel_mass(X, reference, labels, sigma, base, self_pairs=None):
    """FP64 CPU cdist as in calib.py; GPU is used only by the frozen encoder."""
    K = torch.exp(-torch.cdist(torch.tensor(X, dtype=torch.float64), reference).pow(2) / (2 * sigma ** 2))
    own = K[self_pairs].numpy() if self_pairs is not None else np.array([])
    return (K @ labels).numpy() + base, K.sum(1).numpy() + 1.0, own


def logit_mass(num, den):
    q = np.clip(num / den, 1e-6, 1 - 1e-6)
    return np.log(q) - np.log1p(-q)


def rebuild(row, kids, dev):
    if row["family_id"] != "E_PUBLIC_TRANSFER":
        return private_stage.rebuild(row["experiment_id"], kids, dev)
    from auditory_alignment_v2.train import PrivateBatcher
    from auditory_alignment_v2.temporal import build_encoder
    assert row["spec"]["source_architecture"] == "lag_local_tokens"
    b = core.bind(row)
    b["spec"].update(architecture="lag_local_tokens", window="full")
    bt = PrivateBatcher(kids, b["spec"], b, dev)
    enc = build_encoder("lag_local_tokens", 20, int(row["spec"].get("projection_dim", 32)), bt.W, 250).to(dev)
    eid = row["experiment_id"]
    sd = torch.load(Path(core.OUT) / "ckpt" / f"{eid}_best.pt", map_location=dev, weights_only=False)
    enc.load_state_dict(sd["enc"], strict=True)
    enc.eval()
    rec = json.loads((Path(core.OUT) / "units" / f"{eid}.json").read_text())
    return enc, sd.get("protos"), rec, bt


@torch.no_grad()
def evaluate(unit, plan):
    from auditory_alignment import data
    from auditory_alignment.evaluate import _private_reps
    started = time.time()
    row = unit["row"]
    eid = row["experiment_id"]
    record_path = Path(core.OUT) / "units" / f"{eid}.json"
    ckpt_path = Path(core.OUT) / "ckpt" / f"{eid}_best.pt"
    assert sha(record_path) == unit["record_sha256"] and sha(ckpt_path) == unit["checkpoint_sha256"]
    torch.manual_seed(row["seed"])
    kids = data.load_private()
    enc, _, rec, bt = rebuild(row, kids, torch.device("cuda"))
    tr = bt.train
    te = [i for i, k in enumerate(kids) if k["fold"] == row["subject_fold"]]
    U = {i: _private_reps(enc, bt, i) for i in tr + te}
    es = {i: kids[i]["es_mask"] for i in tr}
    Xr = np.concatenate([U[i][es[i]] for i in tr])
    yr = np.concatenate([kids[i]["y"][es[i]] for i in tr])
    base = float(np.concatenate([kids[i]["y"] for i in tr]).mean())
    sel = np.random.default_rng(row["seed"] + 77).choice(len(Xr), size=min(6000, len(Xr)), replace=False)
    xs = torch.tensor(Xr[sel], dtype=torch.float64)
    ys = torch.tensor(yr[sel], dtype=torch.float64)
    sigma = rec["objective_calibration"]["sigma_u"]
    # Score by child, preserving the original cdist call geometry. Concatenating
    # all calibration rows first could change the numerical reproduction.
    masses, self_weights, offset = {}, np.empty(len(sel)), 0
    for i in tr:
        trials = np.flatnonzero(es[i])
        positions = np.flatnonzero((sel >= offset) & (sel < offset + len(trials)))
        pairs = (trials[sel[positions] - offset], positions)
        masses[i] = kernel_mass(U[i], xs, ys, sigma, base, pairs)
        self_weights[positions] = masses[i][2]
        offset += len(trials)
    for i in te:
        masses[i] = kernel_mass(U[i], xs, ys, sigma, base)
    scores = {i: logit_mass(*masses[i][:2]) for i in tr + te}
    sr = np.concatenate([scores[i][es[i]] for i in tr])
    nr = np.concatenate([masses[i][0][es[i]] for i in tr])
    dr = np.concatenate([masses[i][1][es[i]] for i in tr])
    nl, dl = remove_self(nr, dr, sel, yr[sel], self_weights)
    sl = logit_mass(nl, dl)
    old_fit = AffineLogitCalibrator.fit(sr, yr)
    loo_fit = AffineLogitCalibrator.fit(sl, yr)
    stored_fit = AffineLogitCalibrator(**rec["eval"]["native_calibration"]["methods"]["positive_affine"])
    per, maximum = {}, {k: 0.0 for k in REPRO_TOL}
    arrays = {"calibration_y": yr, "calibration_original_score": sr, "calibration_loo_score": sl,
              "reference_calibration_indices": sel}
    for i in te:
        cid, y, s = kids[i]["id"], kids[i]["y"], scores[i]
        methods = {"class_kernel": calib._summ(expit(s), s, y, base),
                   "original_refit": calib._summ(old_fit.predict(s), s, y, base),
                   "stored_calibrator_replay": calib._summ(stored_fit.predict(s), s, y, base),
                   "leave_self_out": calib._summ(loo_fit.predict(s), s, y, base)}
        reference = rec["eval"]["native_calibration"]["per_participant"][cid]
        for method, original in (("class_kernel", "class_kernel"), ("original_refit", "positive_affine"),
                                 ("stored_calibrator_replay", "positive_affine")):
            for field in REPRO_TOL:
                maximum[field] = max(maximum[field], abs(methods[method][field] - reference[original][field]))
        assert len({m["auc_score"] for m in methods.values()}) == 1
        per[cid] = methods
        arrays[f"test_{i}_score"] = s
        arrays[f"test_{i}_y"] = y
    scores_path = BASE / "scores" / f"{eid}.npz"
    with open(str(scores_path) + ".tmp", "wb") as f:
        np.savez_compressed(f, **arrays)
    os.replace(str(scores_path) + ".tmp", scores_path)
    reproduction_pass = all(maximum[k] <= REPRO_TOL[k] for k in maximum)
    output = {"version": plan["version"], "source_unit": eid, "status": "complete" if reproduction_pass else "reproduction_failed",
              "job": os.environ.get("SLURM_JOB_ID"), "plan_sha256": sha(PLAN), "source": unit,
              "device": torch.cuda.get_device_name(0), "same_recorded_device": unit["recorded_device"] == torch.cuda.get_device_name(0),
              "torch_version": torch.__version__, "cuda_version": torch.version.cuda,
              "tf32": {"matmul": torch.backends.cuda.matmul.allow_tf32, "cudnn": torch.backends.cudnn.allow_tf32},
              "reproduction": {"max_abs_difference": maximum, "tolerance": REPRO_TOL, "pass": reproduction_pass},
              "calibrators": {"original_refit": old_fit.to_dict(), "stored": stored_fit.to_dict(), "leave_self_out": loo_fit.to_dict()},
              "calibration": {"n": len(yr), "n_self_removed": len(sel), "base_rate": base, "sigma_u": sigma,
                              "max_self_kernel_deviation_from_one": float(np.max(np.abs(self_weights-1))),
                              "original_fit_nll": float(-calib.LL(old_fit.predict(sr), yr).mean()),
                              "loo_fit_nll": float(-calib.LL(loo_fit.predict(sl), yr).mean()),
                              "original_fit_on_loo_nll": float(-calib.LL(old_fit.predict(sl), yr).mean()),
                              "score_change_mean_abs": float(np.abs(sl-sr).mean())},
              "per_participant": per, "score_file": str(scores_path), "score_sha256": sha(scores_path),
              "test_array_to_child": {str(i): kids[i]["id"] for i in te},
              "seconds": time.time() - started, "gpu_peak_mb": torch.cuda.max_memory_allocated() / 2**20}
    D.write(BASE / "units" / f"{eid}.json", output)
    print(json.dumps({"unit": eid, "status": output["status"], "seconds": output["seconds"], "reproduction": maximum}), flush=True)
    if not reproduction_pass:
        raise RuntimeError(f"Original frozen-score reproduction exceeds registered tolerance: {eid}")


def load_plan():
    plan = json.loads(PLAN.read_text())
    assert plan["source_sha256"] == source_hashes(), "source drift against frozen plan"
    return plan


def smoke_units(plan):
    rr = plan["units"]
    selected = []
    for family, arch in (("E_GENERIC", "cbramod"), ("E_GENERIC", "reve"), ("E_LOCAL", "lag_local_tokens"),
                         ("E_PUBLIC_TRANSFER", "lag_local_tokens")):
        selected.append(next(u for u in rr if u["row"]["family_id"] == family and u["row"]["seed"] == 3401
                             and u["row"]["subject_fold"] == 0
                             and u["row"]["spec"].get("architecture", u["row"]["spec"].get("source_architecture")) == arch
                             and (family != "E_GENERIC" or u["row"]["spec"]["adaptation"] == "pretrained_peft")))
    return selected


def worker(smoke=False):
    plan = load_plan()
    work = smoke_units(plan) if smoke else plan["units"]
    for unit in work:
        eid = unit["row"]["experiment_id"]
        p = BASE / "units" / f"{eid}.json"
        if p.exists():
            old = json.loads(p.read_text())
            if old["status"] != "complete":
                raise RuntimeError(f"Unresolved evaluation failure: {eid}")
            assert old["plan_sha256"] == sha(PLAN)
            continue
        lock = BASE / "claims" / f"{eid}.lock"
        lock.parent.mkdir(exist_ok=True)
        with open(lock, "a+") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if p.exists():
                continue
            subprocess.run([sys.executable, "-B", "-u", "-m", "auditory_alignment_v3.aln34.private_calibration_loo", "--unit", eid], check=True)
    if smoke:
        assert all(json.loads((BASE / "units" / f"{u['row']['experiment_id']}.json").read_text())["status"] == "complete" for u in work)
        D.write(BASE / "smoke_receipt.json", {"status": "pass", "job": os.environ.get("SLURM_JOB_ID"),
                                           "units": [u["row"]["experiment_id"] for u in work], "plan_sha256": sha(PLAN)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--make-plan", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--unit")
    args = ap.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("This computation requires Slurm")
    if args.make_plan:
        make_plan()
    elif args.unit:
        plan = load_plan()
        unit = next(u for u in plan["units"] if u["row"]["experiment_id"] == args.unit)
        try:
            evaluate(unit, plan)
        except Exception:
            D.write(BASE / "failures" / f"{args.unit}.json", {"job": os.environ.get("SLURM_JOB_ID"), "traceback": traceback.format_exc()})
            raise
    else:
        if not args.smoke:
            receipt = json.loads((BASE / "smoke_receipt.json").read_text())
            assert receipt["status"] == "pass" and receipt["plan_sha256"] == sha(PLAN)
        worker(args.smoke)


if __name__ == "__main__":
    main()
