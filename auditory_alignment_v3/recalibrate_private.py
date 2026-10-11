"""ALN3 R_PRIVATE_CALIBRATION: re-evaluation of every completed ALN2 private unit with the calibration variants of calib.py
(temperature / positive-slope affine / class kernel / GX affine), from the saved best checkpoints. No training; the ALN2
records are not modified. Output: private/auditory_alignment_v3/units_recal/<ALN2 id>.json.
Usage: python -m auditory_alignment_v3.recalibrate_private <shard> <n_shards>
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time
import traceback

import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2 = os.path.join(REPO, "private", "auditory_alignment_v2")
OUTD = os.path.join(REPO, "private", "auditory_alignment_v3", "units_recal")
FAMS = ("D_TASK_LOCAL", "D_GX", "D_FM_GENERIC", "D_FM_PUBLIC", "D_LOCAL_DISTILL")


def units():
    out = []
    for p in sorted(glob.glob(os.path.join(V2, "units", "ALN2_D_*private_bdf*.json"))):
        if p.endswith(".FAILED.json"):
            continue
        r = json.load(open(p))
        if r.get("status") == "complete" and not r.get("reuse_of") and r["row"]["family_id"] in FAMS and "eval" in r:
            out.append(r)
    return out


def rebuild(r, kids, dev):
    from auditory_alignment_v2.train import PrivateBatcher
    row = r["row"]; fam = row["family_id"]; eid = r["experiment_id"]
    ck = os.path.join(V2, "ckpt", f"{eid}_best.pt")
    if r.get("chosen_candidate") is not None and r.get("candidates"):
        ch = r["chosen_candidate"]  # run.py records {"candidate": {...}}; distillation records {"distill_weight": w, ...}
        ci = [i for i, c in enumerate(r["candidates"]) if c.get("candidate", {k: c.get(k) for k in ch}) == ch][0]
        ck = os.path.join(V2, "ckpt", f"{eid}_c{ci}_best.pt")
    sd = torch.load(ck, map_location=dev)
    if fam == "D_GX":
        from auditory_alignment_v2.gx import GXNet, GXWrap
        spec = dict(row["spec"]); spec["architecture"] = "density_tokens"
        bt = PrivateBatcher(kids, spec, row, dev); T = sum(b - a for a, b in bt.W)
        net = GXNet(20, T).to(dev); net.load_state_dict(sd["net"]); net.eval()
        return "gx", GXWrap(net), bt, None, ck
    if fam in ("D_TASK_LOCAL", "D_LOCAL_DISTILL"):
        from auditory_alignment_v2.temporal import build_encoder
        arch = row["spec"]["architecture"] if fam == "D_TASK_LOCAL" else "lag_local_tokens"
        bt = PrivateBatcher(kids, row["spec"], row, dev)
        enc = build_encoder(arch, 20, 16, bt.W, 250).to(dev)
    else:
        from auditory_alignment_v2.foundation_adapter import Backbone
        from auditory_alignment_v2.train_fm import EpochEncoder, PrivateFMBatcher
        bt = PrivateFMBatcher(kids, row["spec"], row, dev)
        enc = EpochEncoder(Backbone(row["spec"]["architecture"], "private_bdf", row["spec"]["adaptation"], 250)).to(dev)
    enc.load_state_dict(sd["enc"], strict=True); enc.eval()
    return "native", enc, bt, sd.get("protos"), ck


def main():
    from auditory_alignment import data
    from . import calib
    shard, n = int(sys.argv[1]), int(sys.argv[2])
    os.makedirs(OUTD, exist_ok=True)
    dev = torch.device("cuda"); kids = data.load_private()
    todo = [r for k, r in enumerate(units()) if k % n == shard]
    print(f"shard {shard}/{n}: {len(todo)} units", flush=True)
    for r in todo:
        eid = r["experiment_id"]; p = os.path.join(OUTD, f"{eid}.json")
        if os.path.exists(p) and json.load(open(p)).get("status") == "complete":
            continue
        t0 = time.time(); rec = {"source_unit": eid, "source_code_hash": r.get("code_hash"), "row": r["row"], "status": "running"}
        try:
            kind, enc, bt, protos, ck = rebuild(r, kids, dev)
            rec["source_checkpoint"] = os.path.relpath(ck, REPO)
            rec["native_calibration"] = calib.gx_variants(r["row"], enc, bt) if kind == "gx" else \
                calib.private_variants(r["row"], enc, bt, protos.to(dev) if protos is not None else None, r["objective_calibration"])
            rec["status"] = "complete"
        except Exception as ex:  # noqa: BLE001
            rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-3000:]
        rec["seconds"] = round(time.time() - t0, 1)
        json.dump(rec, open(p + ".tmp", "w"), default=float); os.replace(p + ".tmp", p)
        print(eid, rec["status"], rec["seconds"], rec.get("error", ""), flush=True)
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
