"""Pre-launch regression cases from the ALN3.4 FIXC review; synthetic files only."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from auditory_alignment_v3.prior33 import bridge, contract, manifest, run_donor, run_target, views


def write_json(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(doc, sort_keys=True).encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def copies(tmp_path):
    cache, private = tmp_path / "cache", tmp_path / "private"
    doc = {"schema": views.SCHEMA, "contract": contract.CONTRACT, "constants": views.contract_constants(),
           "cohorts": {"fau": {}}, "files": {}, "cache_root": str(cache), "copy": "private_full"}
    sha = write_json(private / "manifest.json", doc)
    pub = write_json(cache / "manifest.json", {**doc, "copy": "public_redacted"})
    rich = {"schema": views.RICH_SCHEMA, "contract": contract.CONTRACT, "core_manifest_sha256": sha,
            "core_manifest_public_sha256": pub, "rich": {"loss_weights": [1., .5, .5]},
            "cohorts": {"fau": {"rich": "rich_f32.npy", "rich_streams": "rich_streams.json"}},
            "files": {"rich_f32.npy": {"sha256": "a" * 64, "bytes": 128}}}
    rsha = write_json(private / "manifest_rich.json", rich)
    return cache, private, sha, rsha


def test_consumers_fall_through_public_copy_and_merge_rich(copies, monkeypatch):
    cache, private, sha, rsha = copies
    row = {"experiment_id": "synthetic", "family_id": views.RICH_DONOR_FAMILY,
           "spec": {"manifest_sha256": sha, "manifest_rich_sha256": rsha}}
    monkeypatch.setattr(views, "CACHE_ROOT", str(cache))
    for module, public_name in ((run_donor, "MANIFEST"), (run_target, "MANIFEST"), (bridge, "MANIFEST_PATH")):
        monkeypatch.setattr(module, public_name, str(cache / "manifest.json"))
        monkeypatch.setattr(module, "PRIVATE_MANIFEST", str(private / "manifest.json"))
    for opened in (run_donor._open_manifest(row, None), run_target.open_manifest(row), bridge.open_row_manifest(row),
                   views.open_for_row(row, paths=[cache / "manifest.json", private / "manifest.json"],
                                      rich_paths=[private / "manifest_rich.json"])):
        assert opened.sha256 == sha and opened.rich_sha256 == rsha
        assert opened["rich"]["loss_weights"] == [1., .5, .5]
        assert "rich_f32.npy" in opened["files"]
    row["spec"]["manifest_rich_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="no rich supplement"):
        run_donor._open_manifest(row, None)


def test_runtime_integrity_detects_same_size_replacement(tmp_path):
    path = tmp_path / "cache.npy"
    path.write_bytes(b"abcd")
    man = views.Manifest({"files": {"cache.npy": {"sha256": hashlib.sha256(b"abcd").hexdigest(), "bytes": 4}}}, root=str(tmp_path))
    views.verify_file(man, path)
    other = tmp_path / "replacement"
    other.write_bytes(b"abce")
    other.replace(path)
    with pytest.raises(ValueError, match="sha256 differs"):
        views.verify_file(man, path)
    with pytest.raises(ValueError, match="no sha256/bytes"):
        views.verify_file(man, tmp_path / "unknown.npy")


def test_registration_refuses_redacted_manifest(copies):
    cache, _, _, _ = copies
    path = Path(__file__).resolve().parents[3] / "private/auditory_alignment_v3/make_plan_ext_prior33.py"
    spec = importlib.util.spec_from_file_location("prior33_fixc_plan", path)
    plan = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plan)
    with pytest.raises(plan.PlanError, match="private_full"):
        plan.open_manifest(str(cache / "manifest.json"), None)
    assert plan._common({"sha": "a", "rich_sha": "b", "target_contract": "c"}, "rich", 3401, "NCE", "envelope", 3401, None)["manifest_rich_sha256"] == "b"
    assert "manifest_rich_sha256" not in plan._common({"sha": "a", "rich_sha": "b", "target_contract": "c"}, "core", 3401, "NCE", "envelope", 3401, None)


def test_manifest_consumer_helpers_share_hashed_implementation():
    assert views.RICH_DONOR_FAMILY == manifest.RICH_DONOR_FAMILY
    assert views.PRIVATE_OUT == manifest.PRIVATE_OUT
