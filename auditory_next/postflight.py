"""Postflight integrity and private-permission audit (review draft).

This module only hashes the frozen legacy inventory and audits filesystem
metadata.  It never fits a model and never publishes an input path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .provenance import ROOT, digest, finish, require_slurm, write_json


LEGACY_INVENTORY = Path("private/auditory_next_v2/S0_001/legacy_input_hashes.json")


def _current_path(value: Any) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def _verify_inventory(inventory: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Return private per-file results and the byte total of present files."""
    results: list[dict[str, Any]] = []
    present_bytes = 0
    for entry in inventory:
        if not isinstance(entry, dict) or "path" not in entry or "sha256" not in entry:
            raise ValueError("INVALID_LEGACY_HASH_ENTRY")
        path = _current_path(entry["path"])
        row = {"path": str(path), "expected_sha256": str(entry["sha256"])}
        if not path.is_file() or path.is_symlink():
            row.update(status="missing", actual_sha256=None, bytes=None)
        else:
            actual = digest(path)
            size = path.stat().st_size
            present_bytes += size
            row.update(status="ok" if actual == row["expected_sha256"] else "changed",
                       actual_sha256=actual, bytes=size)
        results.append(row)
    return results, present_bytes


def _permission_audit(private_root: Path) -> list[dict[str, Any]]:
    """Audit every entry below the private tree without changing its mode."""
    anomalies: list[dict[str, Any]] = []
    if not private_root.exists():
        return [{"path": str(private_root), "kind": "missing", "mode": None,
                 "expected_mode": "0700"}]
    for current, dirnames, filenames in os.walk(private_root, followlinks=False):
        current_path = Path(current)
        for name in list(dirnames) + list(filenames):
            path = current_path / name
            stat = path.lstat()
            mode = stat.st_mode & 0o777
            if path.is_symlink():
                anomalies.append({"path": str(path), "kind": "symlink", "mode": oct(mode),
                                  "expected_mode": None})
                if name in dirnames:
                    dirnames.remove(name)
                continue
            expected = 0o700 if path.is_dir() else 0o600
            if mode != expected:
                anomalies.append({"path": str(path), "kind": "directory" if path.is_dir() else "file",
                                  "mode": oct(mode), "expected_mode": oct(expected)})
    root_mode = private_root.stat().st_mode & 0o777
    if root_mode != 0o700:
        anomalies.insert(0, {"path": str(private_root), "kind": "directory",
                             "mode": oct(root_mode), "expected_mode": "0o700"})
    return anomalies


def run(config, registry, site, dest, public, report, source_run=None):
    """Verify the frozen S0 legacy files and audit private output permissions."""
    require_slurm()
    del config, registry, site, report
    inventory_path = ROOT / LEGACY_INVENTORY
    if not inventory_path.is_file():
        raise FileNotFoundError(inventory_path)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if not isinstance(inventory, list):
        raise ValueError("INVALID_LEGACY_HASH_INVENTORY")
    rows, present_bytes = _verify_inventory(inventory)
    private_root = ROOT / "private/auditory_next_v2"
    permission_rows = _permission_audit(private_root)
    changed = sum(row["status"] == "changed" for row in rows)
    missing = sum(row["status"] == "missing" for row in rows)
    write_json(Path(dest) / "legacy_hash_audit.json", {
        "inventory": str(inventory_path), "source_run": source_run,
        "expected_files": len(rows), "present_bytes": present_bytes, "files": rows,
    })
    write_json(Path(dest) / "permission_audit.json", {
        "root": str(private_root), "expected_directory_mode": "0700",
        "expected_file_mode": "0600", "anomalies": permission_rows,
    })
    # Keep this summary path-free: detailed paths remain private above.
    summary = {
        "status": "INPUT_INTEGRITY_FAILURE" if changed or missing else "PERMISSION_ANOMALIES" if permission_rows else "PASS",
        "scope": "frozen S0 legacy hash and private permission audit",
        "legacy_files": len(rows), "legacy_bytes": present_bytes,
        "legacy_changed": changed, "legacy_missing": missing,
        "permission_anomalies": len(permission_rows), "source_run": source_run,
        "model_fits": 0,
    }
    return finish(Path(dest), Path(public), summary)
