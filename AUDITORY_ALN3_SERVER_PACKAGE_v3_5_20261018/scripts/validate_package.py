#!/usr/bin/env python3
"""Validate package bytes and local structure without executing project training code."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import re
from pathlib import Path


def reject_constant(s):
    raise ValueError("non-finite JSON constant: " + s)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package", required=True, type=Path)
    ap.add_argument("--allow-no-manifest", action="store_true", help="Only for package construction, not final delivery")
    a = ap.parse_args()
    root = a.package.resolve()
    errors, counts = [], {"json": 0, "jsonl_rows": 0, "python": 0, "markdown": 0, "manifest_files": 0}
    required = ["README.md", "SERVER_START_PROMPT.md", "SERVER_FULL_DOCUMENT.md", "START_NOW.md", "AGENTS_APPEND.md", "PACKAGE_METADATA.json", "SOURCE_INDEX.json", "plans/workpackages.json", "plans/science_contrasts.json", "plans/main_endpoint_group_contrasts.json", "docs/00_RESEARCH_DECISIONS.md", "docs/01_BASELINE_AND_INTAKE.md", "docs/02_SCIENCE_PRIVATE_AND_CORRECTIONS.md", "docs/03_PRIOR_AND_CHECKPOINT_SELECTION.md", "docs/04_SUPPORT_AND_EPISODE.md", "docs/05_FUSION_READOUT_ATTENTION.md", "docs/06_EXECUTION_AND_REPORTING.md", "docs/08_REFERENCE_TOOLS.md", "reports/LOCAL_VALIDATION.md"]
    for rel in required:
        if not (root / rel).is_file():
            errors.append("missing required file: " + rel)
    for p in sorted(root.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            errors.append("symlink not allowed in distributable: " + rel)
            continue
        try:
            if p.suffix == ".json":
                json.loads(p.read_text(encoding="utf-8"), parse_constant=reject_constant)
                counts["json"] += 1
            elif p.suffix == ".jsonl":
                for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                    if line.strip():
                        json.loads(line, parse_constant=reject_constant)
                        counts["jsonl_rows"] += 1
            elif p.suffix == ".py":
                ast.parse(p.read_text(encoding="utf-8"), filename=rel)
                counts["python"] += 1
            elif p.suffix == ".md":
                text = p.read_text(encoding="utf-8")
                counts["markdown"] += 1
                for target in re.findall(r"(?<!!)\[[^\]\n]+\]\(([^\s)]+)\)", text):
                    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("#"):
                        continue
                    target = target.split("#", 1)[0]
                    if target and not (p.parent / target).exists():
                        errors.append("broken local Markdown link: " + rel + " -> " + target)
        except (ValueError, SyntaxError, UnicodeError) as e:
            errors.append(rel + ": " + str(e))
    manifest_path = root / "MANIFEST.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        listed = set()
        for item in manifest["files"]:
            rel = item["path"]
            pp = Path(rel)
            if pp.is_absolute() or ".." in pp.parts or rel in listed:
                errors.append("unsafe/duplicate manifest path: " + rel)
                continue
            listed.add(rel)
            p = root / pp
            if not p.is_file() or p.is_symlink():
                errors.append("manifest file missing/unsafe: " + rel)
                continue
            b = p.read_bytes()
            if len(b) != item["size_bytes"] or hashlib.sha256(b).hexdigest() != item["sha256"]:
                errors.append("manifest byte mismatch: " + rel)
        actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name not in {"MANIFEST.json", "SHA256SUMS"}}
        if actual != listed:
            errors.append("manifest membership differs: " + repr(sorted(actual ^ listed)))
        counts["manifest_files"] = len(listed)
        sums = root / "SHA256SUMS"
        if not sums.is_file():
            errors.append("missing SHA256SUMS")
        else:
            expected = {r["path"]: r["sha256"] for r in manifest["files"]}
            expected["MANIFEST.json"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            lines = {}
            for line in sums.read_text(encoding="utf-8").splitlines():
                digest, sep, rel = line.partition("  ")
                if not sep or rel in lines:
                    errors.append("invalid/duplicate SHA256SUMS line")
                lines[rel] = digest
            if lines != expected:
                errors.append("SHA256SUMS does not match complete manifest plus MANIFEST.json")
    elif not a.allow_no_manifest:
        errors.append("missing final MANIFEST.json")
    print(json.dumps({"ok": not errors, "counts": counts, "errors": errors, "scope": "static package and byte validation only"}, indent=2, ensure_ascii=False))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
