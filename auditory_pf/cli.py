"""auditory_pf command line (all numerical commands require Slurm)."""
from __future__ import annotations

import argparse
import json
import sys

from .runtime import load_config


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="auditory_pf")
    ap.add_argument("--config", default="configs/auditory_pf_v1.yaml")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, **defaults):
        p = sub.add_parser(name)
        p.add_argument("--run", required=True)
        p.add_argument("--prepare-run", default="prepare_001")
        for k, v in defaults.items():
            p.add_argument(f"--{k.replace('_', '-')}", default=v, type=type(v) if v is not None else str)
        return p

    add("prepare")
    add("features")
    add("stim", only="")
    p = add("e2e", mode="observed", perms="1-200")
    add("b2")
    add("b3gpu", part="h18")
    add("perm-b", stim_run="stim_001", embed_source="xfit")
    add("shuffle-h12", stim_run="stim_001", embed_source="xfit")
    p = add("analyze", stim_run="stim_001", e2e_run="e2e_001", features_run="features_001", perm_b_run="perm_b_001",
            shuffle_run="shuffle_h12_001", b2_run="b2_001", b3_run="b3_001", embed_source="xfit")
    p.add_argument("--blind", action="store_true")
    add("h14-sim", stim_run="stim_001", n_sim="200", embed_source="xfit")
    add("reembed")
    add("perm-bdev", stim_run="stim_001", embed_source="mo")
    add("stim2")
    add("analyze2", stim_run="stim_002", perm_run="perm_bdev_002")
    args = ap.parse_args(argv)
    config = load_config(args.config)
    if args.cmd == "prepare":
        from .cohort import cmd_prepare as fn
    elif args.cmd == "features":
        from .features import cmd_features as fn
    elif args.cmd == "stim":
        from .stim import cmd_stim as fn
    elif args.cmd == "e2e":
        from .e2e import cmd_e2e as fn
    elif args.cmd == "b2":
        from .b2 import cmd_b2 as fn
    elif args.cmd == "b3gpu":
        from .b3gpu import cmd_b3gpu as fn
    elif args.cmd == "perm-b":
        from .analyze import cmd_perm_b as fn
    elif args.cmd == "shuffle-h12":
        from .analyze import cmd_shuffle_h12 as fn
    elif args.cmd == "stim2":
        from .stim import cmd_stim2 as fn
    elif args.cmd == "analyze2":
        from .analyze2 import cmd_analyze2 as fn
    elif args.cmd == "perm-bdev":
        from .analyze import cmd_perm_bdev as fn
    elif args.cmd == "reembed":
        from .stim import cmd_reembed as fn
    elif args.cmd == "h14-sim":
        from .analyze import cmd_h14_sim as fn
    elif args.cmd == "analyze":
        from .analyze import cmd_analyze as fn
    else:
        raise ValueError(args.cmd)
    out = fn(args, config)
    print(json.dumps(out, indent=2, default=str, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
