"""M12 selects valid matched rows before a GPU is allocated; no real data or training here."""
import importlib.util
from pathlib import Path
import sys

from auditory_alignment_v3 import core
from auditory_alignment_v3.prior33 import select as SEL

sys.path.insert(0, str(Path(__file__).parent))
from fixtures import make_synthetic_manifest


def test_probe_row_selection_covers_requested_arms(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "FAMILY_CODE", dict(core.FAMILY_CODE))
    monkeypatch.setattr(core, "FAMILY_GROUP", dict(core.FAMILY_GROUP))
    path = Path(core.OUT) / "probe_prior33.py"
    spec = importlib.util.spec_from_file_location("m12_synthetic_preflight", path)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    fixture = make_synthetic_manifest(tmp_path / "fixture")
    rows, man = probe.plan_and_manifests(fixture["manifest_path"])
    chosen = probe.check_selections(rows)
    assert len(chosen) == len({r["experiment_id"] for r in chosen}) == 15
    for row in chosen:
        if row["family_id"] == SEL.DONOR:
            assert row["dataset"] not in row["spec"]["donor_set"]
        assert row["spec"]["manifest_sha256"] == man.sha256
    targets = [r for r in chosen if r["family_id"] == SEL.TARGET]
    assert {(r["dataset"], r["spec"]["init"]) for r in targets} == {
        (d, i) for d in ("fau", "private_bdf") for i in ("random", "donor")}
