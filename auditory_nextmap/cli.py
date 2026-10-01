"""auditory_nextmap command line (all numerical commands require Slurm; `report` never fits)."""
from __future__ import annotations

import argparse
import importlib
import json
import sys

from .runtime import CONFIG_DEFAULT, load_config

COMMANDS = {
    "source-check": ("manifest", "cmd_source_check", {}),
    "plan": ("manifest", "cmd_plan", {"p0_run": "p0_001"}),
    "synthetic": ("synthetic", "cmd_synthetic", {}),
    "age-core": ("age_core", "cmd_age_core", {}),
    "age-summary": ("age_core", "cmd_age_summary", {}),
    "headroom": ("headroom", "cmd_headroom", {}),
    "headroom-diag": ("headroom", "cmd_headroom_diag", {}),
    "headroom-rescore": ("headroom", "cmd_headroom_rescore", {}),
    "controls-prep": ("controls", "cmd_controls_prep", {}),
    "controls-infer": ("controls", "cmd_controls_infer", {"prep_run": "a1_prep_001"}),
    "age-controls": ("controls", "cmd_age_controls", {"prep_run": "a1_prep_001", "infer_run": "a1_infer_001",
                                                      "a0_run": "a0_001"}),
    "recover": ("recovery", "cmd_recover", {"unit": "", "reuse_scan": ""}),
    "unlock-plan": ("unlock", "cmd_unlock_plan", {}),
    "report": ("reporting", "cmd_report", {}),
    "g1-train": ("gpu_age", "cmd_g1_train", {}),
    "g1-readout": ("gpu_age", "cmd_g1_readout", {"train_run": "g1_train_001"}),
    "g2-train": ("gpu_share", "cmd_g2_train", {}),
    "g2-summary": ("gpu_share", "cmd_g2_summary", {"train_run": "g2_train_001"}),
    "h1-prep": ("h_prep", "cmd_h1_prep", {}),
    "h4-features": ("h_prep", "cmd_h4_features", {}),
    "h-infer": ("h_gpu", "cmd_h_infer", {"prep_run": "h1_prep_001"}),
    "h3-train": ("h_gpu", "cmd_h3_train", {}),
    "h1-readout": ("h_readout", "cmd_h1_readout", {"prep_run": "h1_prep_001", "infer_run": "h_infer_001"}),
    "h2-readout": ("h_readout", "cmd_h2_readout", {"infer_run": "h_infer_001"}),
    "h3-readout": ("h_readout", "cmd_h3_readout", {"train_run": "h3_train_001"}),
    "h4-readout": ("h_readout", "cmd_h4_readout", {"features_run": "h4_features_001"}),
    "h5-assoc": ("h_readout", "cmd_h5_assoc", {}),
    "h6-readout": ("h_readout", "cmd_h6_readout", {"infer_run": "h_infer_001"}),
    "h7-range": ("h_readout", "cmd_h7_range", {"infer_run": "h_infer_001", "features_run": "h4_features_001"}),
    "h8-d2plus": ("h_extra", "cmd_h8_d2plus", {"reuse_features": "", "only_views": ""}),
    "h8b-bdf": ("h_extra", "cmd_h8b_bdf", {}),
    "h11-duration": ("h_extra", "cmd_h11_duration", {}),
    "h10-budget": ("h_extra", "cmd_h10_budget", {"features_run": "h8_d2plus_001"}),
    "h8c-grid": ("h_extra", "cmd_h8c_grid", {"infer_run": "h_infer_001", "features_run": "h4_features_001"}),
    "h9-reliability": ("h_extra", "cmd_h9_reliability", {"a1_prep_run": "a1_prep_001", "h1_prep_run": "h1_prep_001"}),
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="auditory_nextmap")
    ap.add_argument("--config", default=CONFIG_DEFAULT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, (_mod, _fn, extra) in COMMANDS.items():
        p = sub.add_parser(name)
        p.add_argument("--run", required=True)
        for k, v in extra.items():
            p.add_argument(f"--{k.replace('_', '-')}", default=v)
    args = ap.parse_args(argv)
    config = load_config(args.config)
    mod, fn, _ = COMMANDS[args.cmd]
    out = getattr(importlib.import_module(f"auditory_nextmap.{mod}"), fn)(args, config)
    print(json.dumps(out, indent=2, default=str, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
