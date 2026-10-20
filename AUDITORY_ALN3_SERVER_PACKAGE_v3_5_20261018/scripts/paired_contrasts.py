#!/usr/bin/env python3
"""Read normalized inputs and emit a reference report; never launch server work."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aln35_reference.contrasts import ReferenceError, analyze, load_rows, parse_json
from aln35_reference.sampling import allocate_support_ids, audit_mask_coverage


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("contrast", "paired identity contrasts and fixed-original-SE simultaneous intervals"),
                            ("mask", "retained and zeroed physical input positions under a keep-mask"),
                            ("support", "pure-ID nested count allocation in a fixed first-30% region")):
        sub = subparsers.add_parser(name, help=help_text)
        source = sub.add_mutually_exclusive_group(required=True)
        source.add_argument("--spec", type=Path, help="read a JSON specification")
        source.add_argument("--spec-json", help="inline JSON specification")
        sub.add_argument("--output", type=Path, help="create a NEW report file; existing paths are never overwritten")
        if name == "contrast":
            sub.add_argument("--rows", type=Path, required=True, help="normalized JSONL rows; read-only")
    args = parser.parse_args(argv)
    try:
        spec = parse_json(args.spec.read_text(encoding="utf-8") if args.spec else args.spec_json)
        if args.command == "contrast":
            result = analyze(load_rows(args.rows), spec)
        elif args.command == "mask":
            result = audit_mask_coverage(spec)
        else:
            result = allocate_support_ids(spec)
        payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(payload)
        else:
            sys.stdout.write(payload)
        if args.command == "mask" and not result["all_declared_counts_match"]:
            return 3
        return 0
    except (ReferenceError, OSError, OverflowError) as exc:
        parser.exit(2, f"reference input error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
