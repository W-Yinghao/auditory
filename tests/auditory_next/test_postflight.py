import hashlib
import json
from pathlib import Path

import pytest

from auditory_next import postflight


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _fixture(tmp_path, monkeypatch):
    root = tmp_path / "root"
    old = root / "old"
    old.mkdir(parents=True)
    (old / "a.bin").write_bytes(b"abc")
    private = root / "private/auditory_next_v2/S0_001"
    private.mkdir(parents=True, mode=0o700)
    inventory = [{"path": str(old / "a.bin"), "sha256": _sha(old / "a.bin"), "bytes": 3}]
    (private / "legacy_input_hashes.json").write_text(json.dumps(inventory))
    monkeypatch.setattr(postflight, "ROOT", root)
    monkeypatch.setattr(postflight, "require_slurm", lambda: None)
    captured = {}
    monkeypatch.setattr(postflight, "finish", lambda dest, public, summary: captured.setdefault("summary", summary))
    return root, private, captured


def test_run_verifies_inventory_and_publishes_only_aggregates(tmp_path, monkeypatch):
    root, private, captured = _fixture(tmp_path, monkeypatch)
    dest, public = root / "dest", root / "public"
    dest.mkdir(); public.mkdir()
    postflight.run({}, {}, {}, dest, public, root / "report", source_run="S0_001")
    summary = captured["summary"]
    assert summary["legacy_changed"] == 0
    assert summary["legacy_missing"] == 0
    assert summary["legacy_files"] == 1 and summary["legacy_bytes"] == 3
    assert summary["model_fits"] == 0
    text = json.dumps(summary)
    assert str(root / "old") not in text
    audit = json.loads((dest / "legacy_hash_audit.json").read_text())
    assert audit["files"][0]["status"] == "ok"
    assert str(root / "old/a.bin") in (dest / "legacy_hash_audit.json").read_text()


def test_changed_and_missing_are_counted(tmp_path, monkeypatch):
    root, private, captured = _fixture(tmp_path, monkeypatch)
    old = root / "old/a.bin"
    old.write_bytes(b"changed")
    inventory = json.loads((private / "legacy_input_hashes.json").read_text())
    inventory.append({"path": str(root / "old/missing"), "sha256": "0" * 64})
    (private / "legacy_input_hashes.json").write_text(json.dumps(inventory))
    dest, public = root / "dest", root / "public"; dest.mkdir(); public.mkdir()
    postflight.run({}, {}, {}, dest, public, root / "report")
    assert captured["summary"]["legacy_changed"] == 1
    assert captured["summary"]["legacy_missing"] == 1
    assert captured["summary"]["status"] == "INPUT_INTEGRITY_FAILURE"


def test_permission_and_symlink_anomalies_are_reported_without_chmod(tmp_path, monkeypatch):
    root, private, captured = _fixture(tmp_path, monkeypatch)
    bad = private / "bad.txt"
    bad.write_text("x")
    bad.chmod(0o644)
    link = private / "link"
    link.symlink_to(bad)
    dest, public = root / "dest", root / "public"; dest.mkdir(); public.mkdir()
    postflight.run({}, {}, {}, dest, public, root / "report")
    kinds = [x["kind"] for x in json.loads((dest / "permission_audit.json").read_text())["anomalies"]]
    assert "file" in kinds and "symlink" in kinds
    assert (bad.stat().st_mode & 0o777) == 0o644
    assert captured["summary"]["permission_anomalies"] >= 2
    assert captured["summary"]["status"] == "PERMISSION_ANOMALIES"


def test_slurm_gate_is_required(tmp_path, monkeypatch):
    root, _, _ = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(postflight, "require_slurm", lambda: (_ for _ in ()).throw(RuntimeError("slurm")))
    with pytest.raises(RuntimeError, match="slurm"):
        postflight.run({}, {}, {}, root / "d", root / "p", root / "r")
