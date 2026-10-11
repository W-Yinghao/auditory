#!/usr/bin/env python3
"""Aggregate an explicitly exported normalized private table; never infer identity."""
from pathlib import Path
import argparse, hashlib, json, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
from aln3_reference.aggregation import summarize_conditions, paired_conditions


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--n-boot", type=int, default=4000)
    p.add_argument("--seed", type=int, default=3401)
    args = p.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit("Output directory is not empty; use a new versioned directory.")
    df = pd.read_csv(args.input)
    if set(df.dataset) != {"federici"}:
        raise SystemExit("This entry point only accepts a Federici table.")
    by_cond = summarize_conditions(df, args.n_boot, args.seed)
    pairs = paired_conditions(df, n_boot=args.n_boot, seed=args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {"input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(), "n_input_rows": len(df),
               "human_identities": int(df[df.entity_type == "human"].subject_uid.nunique()),
               "nonhuman_or_unknown_identities": int(df[df.entity_type != "human"].subject_uid.nunique()),
               "identity_source": "supplied_verified_manifest_not_inferred_by_this_script",
               "note": "Per-condition and paired outputs; no pooled human/phantom result."}
    for name, value in [("summary_by_condition.json", by_cond), ("paired_HC_minus_HCv.json", pairs), ("receipt.json", receipt)]:
        (args.output_dir / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))

if __name__ == "__main__":
    main()
