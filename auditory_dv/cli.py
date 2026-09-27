"""auditory_dv command line (all numerical commands require Slurm)."""
from __future__ import annotations

import argparse
import json
import sys

from .runtime import load_config


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="auditory_dv")
    ap.add_argument("--config", default="configs/auditory_dv_v1.yaml")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, extra in (("prepare-mff", {}), ("stim-mff", {"prepare_run": "prepare_mff_001"}),
                        ("features-mff", {"prepare_run": "prepare_mff_001"}), ("montages", {}),
                        ("montage-lane", {"montage_run": "montages_001"}), ("audit-c", {}), ("audit-d", {}),
                        ("analyze", {}), ("pooled", {}), ("a1-sensitivity", {})):
        p = sub.add_parser(name)
        p.add_argument("--run", required=True)
        for k, v in extra.items():
            p.add_argument(f"--{k.replace('_', '-')}", default=v)
    args = ap.parse_args(argv)
    config = load_config(args.config)
    mod, fn = {"prepare-mff": ("mff", "cmd_prepare_mff"), "stim-mff": ("stim_mff", "cmd_stim_mff"),
               "features-mff": ("features_mff", "cmd_features_mff"), "montages": ("montage", "cmd_montages"),
               "montage-lane": ("montage", "cmd_montage_lane"), "audit-c": ("audit", "cmd_audit_c"),
               "audit-d": ("audit", "cmd_audit_d"), "analyze": ("analyze", "cmd_analyze"),
               "pooled": ("pooled", "cmd_pooled"), "a1-sensitivity": ("analyze", "cmd_a1_sensitivity")}[args.cmd]
    import importlib
    out = getattr(importlib.import_module(f"auditory_dv.{mod}"), fn)(args, config)
    print(json.dumps(out, indent=2, default=str, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
