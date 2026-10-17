#!/usr/bin/env python3
"""Example:
python scripts/audit_seed_pairs.py --index normalized_metadata.jsonl \
  --spec configs/pairing_example.yaml --output reports/pair_audit.json

Input role assignment comes from the server registry. This tool never submits,
resumes or cancels jobs, reads EEG, or selects records by performance.
"""
from pathlib import Path
import argparse, json, sys
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aln34_reference.pairing import audit_pairs

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--index",type=Path,required=True)
    p.add_argument("--spec",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.output.resolve() in {args.index.resolve(), args.spec.resolve()}:
        p.error("output must not overwrite either input")
    try:
        spec=yaml.safe_load(args.spec.read_text())
        records=[json.loads(line) for line in args.index.read_text().splitlines() if line.strip()]
        result=audit_pairs(records,spec["reference_role"],spec["candidate_role"],tuple(spec["match_fields"]))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        p.error(str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"n_pairs":result["n_pairs"],"n_missing":result["n_missing"]}))
if __name__=="__main__":main()
