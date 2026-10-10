"""ALN2 runner for dependency-bearing families (technical dependencies only, never result gates):
  B_AUDITORY_CONTINUE : donor(arch, depth, other public cohorts, seed) -> target-cohort fine-tuning at the same depth.
  D_FM_PUBLIC         : donor(arch, full, all public cohorts, seed) -> private PEFT / full fine-tuning.
  D_LOCAL_DISTILL     : teacher = matching D_FM_PUBLIC auditory_pretrained_full unit -> restricted-window student.
Usage:
  python -m auditory_alignment_v2.run_stage --job-index <i>
  python -m auditory_alignment_v2.run_stage --donor "<arch>|<full|partial>|<src+src>|<seed>"
Learning rates come from the B_FM / D_FM_GENERIC recipes chosen on the development cell (target stage: the target cohort's
recipe for the same depth and objective; donor stage: the first source cohort's NCE recipe). Units whose dependency is not
yet available exit as technical_pending without a record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import traceback

import numpy as np
import torch

from .run import OUT, PLAN, REPO, canonical, load_cohort, load_row
from .run_fm import epochs_for, recipe_dir

STAGE_CODE = [("auditory_alignment_v2", f) for f in ("donor.py", "distill.py", "run_stage.py", "foundation_adapter.py", "fm_readout.py", "train_fm.py", "eval_fm.py",
                                                     "train.py", "evaluate.py", "audio_targets.py", "temporal.py")] + \
             [("auditory_alignment", f) for f in ("data.py", "evaluate.py", "losses.py", "losses_reference.py", "train.py")]
from .fm_readout import HEAD_VERSION, channel_probe_private, channel_probe_segments  # noqa: E402
from .run_fm import _probe  # noqa: E402
STAGE_FAMILIES = {"B_AUDITORY_CONTINUE", "D_FM_PUBLIC", "D_LOCAL_DISTILL"}


def code_hash():
    h = hashlib.sha256()
    for d, f in STAGE_CODE:
        h.update(open(os.path.join(REPO, d, f), "rb").read())
    return h.hexdigest()[:16]


def depth_of(adaptation):
    return "full" if adaptation.endswith("full") else ("partial" if adaptation.endswith("partial") else "peft")


def recipe(arch, depth, dataset, objective, out=OUT):
    f = os.path.join(recipe_dir(out), f"{arch}__pretrained_{depth}__{dataset}__{objective}.json")
    return json.load(open(f))["chosen"] if os.path.exists(f) else None


def donor_spec(row):
    from .donor import sources_for
    s = row["spec"]; fam = row["family_id"]
    arch = s["architecture"] if fam != "D_LOCAL_DISTILL" else s["teacher"].split("_")[0]
    depth = "full" if fam == "D_FM_PUBLIC" else depth_of(s["adaptation"])
    return arch, depth, sources_for(fam, row["dataset"]), row["seed"]


def build_donor(key, out=OUT):
    from .donor import donor_id, train_donor
    arch, depth, src, seed = key.split("|"); sources = src.split("+"); seed = int(seed)
    lr = recipe(arch, depth, sources[0], "NCE", out)
    if lr is None:
        print("technical_pending (donor recipe unresolved)", key); return
    p = train_donor(arch, depth, sources, seed, out, lr["lr_backbone"], lr["lr_head"])
    print("donor", donor_id(arch, depth, sources, seed), p)


def teacher_of(row, plan_rows):
    s = row["spec"]; arch = s["teacher"].split("_")[0]
    for r in plan_rows:
        if (r["family_id"] == "D_FM_PUBLIC" and r["spec"]["architecture"] == arch and r["spec"]["adaptation"] == "auditory_pretrained_full"
                and r["spec"]["objective"] == s["objective"] and r["subject_fold"] == row["subject_fold"] and r["seed"] == row["seed"]):
            return arch, r["experiment_id"]
    return arch, None


def run_unit(row, out=OUT):
    from auditory_alignment import data
    from . import evaluate
    from .donor import donor_id
    from .eval_fm import evaluate_segments
    from .train_fm import fit_private_fm, fit_segments
    eid = row["experiment_id"]; path = os.path.join(out, "units", f"{eid}.json"); fam = row["family_id"]
    if os.path.exists(path):
        print("skip", eid); return
    if fam not in STAGE_FAMILIES:
        print("technical_pending", eid, fam); return
    s = row["spec"]; dev = torch.device("cuda")
    rec = {"experiment_id": eid, "row": row, "canonical": canonical(row), "code_hash": code_hash(), "runner": "run_stage", "status": "running",
           "device": torch.cuda.get_device_name(0)}
    if fam == "D_LOCAL_DISTILL":
        arch, t_eid = teacher_of(row, [json.loads(l) for l in open(PLAN)])
        t_ck = os.path.join(out, "ckpt", f"{t_eid}_best.pt") if t_eid else None
        if not t_eid or not os.path.exists(os.path.join(out, "units", f"{t_eid}.json")) or not os.path.exists(t_ck):
            print("technical_pending (teacher not available)", eid); return
        rec["teacher_unit"] = t_eid
    else:
        arch, depth, sources, seed = donor_spec(row)
        d_path = os.path.join(out, "donors", donor_id(arch, depth, sources, seed) + ".pt")
        tgt_depth = depth_of(s["adaptation"])
        lr = recipe(arch, tgt_depth, row["dataset"], s["objective"], out); E = epochs_for(arch, out)
        if not os.path.exists(d_path) or lr is None or not E:
            print("technical_pending (donor or recipe unavailable)", eid); return
        rec["donor"] = json.load(open(d_path.replace(".pt", ".json")))
        rec["donor"].pop("curve", None)
        rec["resolved_config"] = {"epochs": E, **lr, "target_depth": tgt_depth}
    os.makedirs(os.path.join(out, "units"), exist_ok=True); os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    t0 = time.time()
    try:
        if fam == "D_LOCAL_DISTILL":
            from .distill import fit_private_distill
            kids = data.load_private(); fits = []
            for ci, lam in enumerate((0.1, 1.0)):
                log = {}
                enc, bt, protos = fit_private_distill(row, kids, dev, os.path.join(out, "ckpt", f"{eid}_c{ci}"), log, arch, t_ck, lam)
                fits.append((lam, log, (enc, bt, protos)))
            k = int(np.argmin([f[1]["best_selection_score"] for f in fits]))
            rec["candidates"] = [{"distill_weight": f[0], "curve": f[1]["curve"], "best_selection_score": f[1]["best_selection_score"]} for f in fits]
            rec["chosen_candidate"] = {"distill_weight": fits[k][0]}
            log = fits[k][1]; enc, bt, protos = fits[k][2]; rec.update(log)
            rec["eval"] = evaluate.evaluate_private(row, enc, bt, log["objective_calibration"], protos)
        else:
            init = torch.load(d_path, map_location="cpu")["net"]; log = {}
            if row["dataset"] == "private_bdf":
                enc, bt, protos = fit_private_fm(row, data.load_private(), dev, os.path.join(out, "ckpt", eid), log, lr["lr_backbone"], lr["lr_head"], E,
                                                 s["adaptation"], init_state=init)
                rec.update(log); rec["eval"] = evaluate.evaluate_private(row, enc, bt, log["objective_calibration"], protos)
                rec["readout_head"] = HEAD_VERSION; _probe(rec, lambda: channel_probe_private(row, enc, bt))
            else:
                coh = load_cohort(row)
                enc, head, bt, _ = fit_segments(row, coh, dev, os.path.join(out, "ckpt", eid), log, lr["lr_backbone"], lr["lr_head"], E,
                                                s["adaptation"], init_state=init)
                rec.update(log); rec["eval"] = evaluate_segments(row, enc, head, bt, coh, log["objective_calibration"])
                rec["readout_head"] = HEAD_VERSION; _probe(rec, lambda: channel_probe_segments(row, enc, head, bt, coh, log["objective_calibration"]))
        rec["status"] = "complete"
    except Exception as ex:
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    rec["total_seconds"] = round(time.time() - t0, 1); rec["gpu_peak_allocated_mb"] = round(torch.cuda.max_memory_allocated() / 2 ** 20)
    p = path if rec["status"] == "complete" else path.replace(".json", ".FAILED.json")
    json.dump(rec, open(p + ".tmp", "w"), default=float); os.replace(p + ".tmp", p)
    print(eid, rec["status"], rec["total_seconds"], rec.get("error", ""), flush=True)
    if rec["status"] != "complete":
        raise SystemExit(1)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--manifest", default=PLAN); a.add_argument("--job-index", type=int); a.add_argument("--experiment-id")
    a.add_argument("--donor"); a.add_argument("--out", default=OUT)
    args = a.parse_args()
    if args.donor:
        build_donor(args.donor, args.out)
    else:
        run_unit(load_row(args.manifest, args.job_index, args.experiment_id), args.out)


if __name__ == "__main__":
    main()
