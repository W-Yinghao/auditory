"""Routing only (not part of any unit's code hash): one pool command for every foundation / dependency-bearing line.
  queue line '<experiment_id>|<plan index>' -> run_fm / run_stage / run_adapt by family
  queue line 'donor__<arch>__<depth>__<src+src>__s<seed>|-1' -> run_stage.build_donor; writes units/<donor id>.json marker
  queue line 'LRX__<arch>__<adaptation>__<dataset>__<obj>|-2' -> fm_ext.lr_select (item 3); index >= 100000 -> fm_ext plan row
Usage: python -m auditory_alignment_v2.dispatch --manifest PLAN --job-index <i> --eid <experiment_id> [--out DIR]"""
import argparse
import json
import os

from .run import OUT, PLAN, load_row

STAGE = {"B_AUDITORY_CONTINUE", "D_FM_PUBLIC", "D_LOCAL_DISTILL"}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--manifest", default=PLAN); a.add_argument("--job-index", type=int); a.add_argument("--eid"); a.add_argument("--out", default=OUT)
    args = a.parse_args()
    if args.eid and args.eid.startswith("donor__"):
        from .run_stage import build_donor
        _, arch, depth, src, seed = args.eid.split("__")
        build_donor(f"{arch}|{depth}|{src}|{seed.lstrip('s')}", args.out)
        p = os.path.join(args.out, "donors", args.eid + ".pt")
        if os.path.exists(p):
            os.makedirs(os.path.join(args.out, "units"), exist_ok=True)
            json.dump({"experiment_id": args.eid, "status": "complete", "kind": "donor_marker"}, open(os.path.join(args.out, "units", args.eid + ".json"), "w"))
        return
    if args.eid and args.eid.startswith("LRX__"):  # item-3 learning-rate selection (X_FT_REG recipe)
        from .fm_ext import lr_select
        lr_select(args.eid[5:].replace("__", "|"), args.out)
        return
    if args.job_index is not None and args.job_index >= 100000:  # item-3 plan rows (fm_ext.X_OFFSET)
        from .fm_ext import PLAN_X, run_unit as run_x
        rows = [json.loads(l) for l in open(PLAN_X)]
        run_x(rows[args.job_index - 100000], args.out)
        return
    row = load_row(args.manifest, args.job_index)
    fam = row["family_id"]
    if fam in STAGE:
        from .run_stage import run_unit
    elif fam == "C_ADAPT":
        from .run_adapt import run_unit
    else:
        from .run_fm import run_unit
    run_unit(row, args.out)


if __name__ == "__main__":
    main()
