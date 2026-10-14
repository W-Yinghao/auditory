"""ALN3 dispatcher (not part of any code hash): plan row -> family runner module.
Usage: python -m auditory_alignment_v3.run --index <i> --eid <experiment_id> [--out DIR] [--epochs N]"""
from __future__ import annotations

import argparse
import importlib
import os

from .core import FAMILY_GROUP, OUT, bind, code_hash, grid_samples, load_rows  # noqa: F401 (re-exported for probes/tests)

RUNNER = {"local": "run_local", "private": "run_private", "dense": "run_dense", "local_factors": "run_local_factors", "complement": "run_complement", "dense_ext": "run_dense_ext", "adapt": "run_adapt3", "coverage": "run_coverage", "attention": "run_attention", "e_complement": "run_e_complement", "distill": "run_distill", "layer_probe": "run_layer_probe", "transfer": "run_transfer",
          "adapt_policy": "run_adapt_policy", "coverage_policy": "run_coverage_policy",
          "attention_policy": "run_attention_policy", "aligned": "run_aligned"}
EXT_OFFSET = 100000  # queue index >= EXT_OFFSET -> row (index - EXT_OFFSET) of private/auditory_alignment_v3/plan_ext.jsonl
LOCAL_FAMILIES = {f for f, g in FAMILY_GROUP.items() if g in ("local", "local_factors")}
PRIVATE_FAMILIES = {f for f, g in FAMILY_GROUP.items() if g == "private"}
FM_FAMILIES = {f for f, g in FAMILY_GROUP.items() if g == "dense"}


def run_unit(row, out=OUT, epochs=None):
    if os.path.exists(os.path.join(out, "units", f"{row['experiment_id']}.json")):
        print("skip", row["experiment_id"]); return
    g = FAMILY_GROUP.get(row["family_id"])
    if g is None:
        print("technical_pending (family not bound yet)", row["experiment_id"], row["family_id"]); return
    if row["family_id"].startswith("D_") and row["spec"].get("architecture") in ("dense_fm_policy", "complement_policy"):
        # ADDENDUM_04: a bound policy arm runs its own code group; this process records that group's code_group / code_hash
        from . import core
        from .registry import POLICY_GROUP
        g = POLICY_GROUP.get(row["family_id"])
        if g is None:
            print("technical_pending (policy arm not bound yet)", row["experiment_id"], row["family_id"]); return
        core.FAMILY_GROUP = {**core.FAMILY_GROUP, row["family_id"]: g}
    importlib.import_module(f"auditory_alignment_v3.{RUNNER[g]}").run(row, out, epochs)


def ext_rows():
    import json
    p = os.path.join(OUT, "plan_ext.jsonl")
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []


def all_rows():
    """Plan rows followed by the registered extension rows (plan_ext.jsonl). The family runners resolve their same-fold /
    same-seed dependencies (A_LOCAL bases, mean_score twins, lag_local donors, teacher candidates) through core.load_rows();
    since ALN3.1 (2026-10-11) seed-panel rows live in plan_ext.jsonl, so the dispatcher points core.load_rows at this list
    (indices < len(plan) are unchanged). run.py is not part of any code hash."""
    return load_rows() + ext_rows()


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--index", type=int, required=True); a.add_argument("--eid"); a.add_argument("--out", default=OUT); a.add_argument("--epochs", type=int)
    args = a.parse_args()
    if args.index >= EXT_OFFSET:
        row = ext_rows()[args.index - EXT_OFFSET]
    else:
        row = load_rows()[args.index]
    if args.eid:
        assert row["experiment_id"] == args.eid, (row["experiment_id"], args.eid)  # real-id addressing
    from . import core
    rows = all_rows(); core.load_rows = lambda: rows  # dependency lookups of the runners see plan + extension rows
    run_unit(row, args.out, args.epochs)


if __name__ == "__main__":
    main()
