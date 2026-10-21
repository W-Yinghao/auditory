#!/usr/bin/env python3
"""Read-only package integrity and count check; never submits or deletes jobs."""
import hashlib
import json
from pathlib import Path
from materialize_plan import expand

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text())
    failures = []
    for rec in manifest["files"]:
        path = ROOT / rec["path"]
        if not path.is_file():
            failures.append({"path": rec["path"], "reason": "missing"})
            continue
        raw = path.read_bytes()
        if len(raw) != rec["bytes"] or hashlib.sha256(raw).hexdigest() != rec["sha256"]:
            failures.append({"path": rec["path"], "reason": "bytes_or_hash_changed"})
    plan = expand(json.loads((ROOT / "plans/round1.json").read_text()))
    counts = {"unique_training": plan["unique_train_count"], "evaluation_bundles": plan["evaluation_bundle_count"]}
    print(json.dumps({"status": "pass" if not failures else "failed", "manifest_files": len(manifest["files"]),
                      "counts": counts, "failures": failures, "production_results_verified": False}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
