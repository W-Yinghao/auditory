#!/usr/bin/env python3
"""Read local repository evidence; write a new snapshot. No network or scheduler calls."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def git_read(repo, *args):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return {"returncode": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--package", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--remote-head", default=None, help="Optional remotely observed HEAD supplied by operator; this script does not fetch it")
    a = ap.parse_args()
    repo, package = a.repo.resolve(), a.package.resolve()
    if not repo.is_dir():
        ap.error("--repo must be an existing repository directory")
    if a.out.exists():
        ap.error("--out already exists; select a new versioned output")
    source = json.loads((package / "SOURCE_INDEX.json").read_text(encoding="utf-8"))
    head = git_read(repo, "rev-parse", "HEAD")
    if head["returncode"]:
        ap.error("cannot read repository HEAD")
    records = []
    for item in source.get("repository_sources", []):
        rel = Path(item["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("unsafe source path")
        p = repo / rel
        r = {"path": str(rel), "baseline_sha256": item["sha256"], "exists": p.is_file()}
        if p.is_file():
            b = p.read_bytes()
            r.update(size_bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
            r["matches_package_baseline"] = r["sha256"] == r["baseline_sha256"]
        records.append(r)
    result = {
        "schema_version": "aln35_local_intake_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "package_baseline_commit": source["baseline_commit"],
        "local_head": head["stdout"],
        "remote_head_operator_supplied": a.remote_head,
        "worktree_status": git_read(repo, "status", "--short"),
        "sources": records,
        "code_handoff_present": (repo / "CODEX_HANDOFF.md").is_file(),
        "scope": "local metadata and selected source bytes only; no live scheduler/checkpoint inventory",
        "required_server_followup": ["actual remote HEAD/time", "owned live jobs and exact held executions", "registered plan/record coverage", "checkpoint/cache availability and lineage", "bind workpackages to exact units and source-side selection roles"],
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")
    print(json.dumps({"written": str(a.out.resolve()), "local_head": head["stdout"], "sources": len(records), "changed_or_missing": sum(not r.get("matches_package_baseline", False) for r in records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
