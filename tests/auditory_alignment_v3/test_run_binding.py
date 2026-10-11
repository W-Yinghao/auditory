"""ALN3 binding checks (engineering only)."""
import json
from collections import Counter
import numpy as np
import pytest
from auditory_alignment_v3 import run as R3
from auditory_alignment_v3.aln3_reference.calibration import AffineLogitCalibrator

ROWS = R3.load_rows()


def test_plan_size_and_ids():
    assert len(ROWS) == 5996 and len({r["experiment_id"] for r in ROWS}) == 5996


@pytest.mark.parametrize("fam", sorted(R3.LOCAL_FAMILIES | R3.PRIVATE_FAMILIES))
def test_bind(fam):
    rs = [r for r in ROWS if r["family_id"] == fam]
    assert rs
    for r in rs:
        b = R3.bind(r)
        assert b["experiment_id"] == r["experiment_id"] and b["seed"] == r["seed"] and b["subject_fold"] == r["subject_fold"]
        assert b["spec"]["objective"] == r["spec"]["objective"] and b["spec"]["architecture"] == r["spec"].get("architecture")
        assert b["spec"]["target"] == (r["spec"].get("target") or R3.DEFAULT_TARGET[r["dataset"]])
        if r["dataset"] != "private_bdf":
            assert b["spec"]["window"] == r["spec"]["window"] and b["content_fold"] in (0, 1)


def test_grid():
    assert R3.grid_samples(128) == 3 and R3.grid_samples(100) == 2 and R3.grid_samples(250) == 5


def test_counts_bound():
    c = Counter(r["family_id"] for r in ROWS if r["family_id"] in R3.LOCAL_FAMILIES | R3.PRIVATE_FAMILIES)
    # A_LOCAL_FACTORS joined the local group when it was bound (ADDENDUM_02, 2026-10-10 20:46); expectation updated 2026-10-11
    assert c == {"A_LOCAL": 1000, "A_LOCAL_FACTORS": 100, "A_TARGETS": 320, "A_DIMENSION": 100, "E_GX": 30, "E_LOCAL": 140, "E_GENERIC": 180}


def test_positive_affine_keeps_order():
    r = np.random.default_rng(0); s = r.normal(size=500); y = (r.random(500) < 0.2 + 0.1 * (s > 0)).astype(int)
    cal = AffineLogitCalibrator.fit(s, y)
    assert cal.slope > 0 and np.all(np.diff(cal.predict(np.sort(s))) >= 0)
