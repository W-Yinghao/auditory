"""The FIXC PCA exclusion is a whole-presentation rule, including non-overlap windows."""
import numpy as np

from auditory_alignment_v3.prior33 import contract as C
from auditory_alignment_v3.prior33.refit_rich import available_windows, core_fit_windows, preserve_previous


def fixture_manifest():
    return {"donor_sets": {"fau": {"core": {"excluded_presentations": {"sparrkulee": []}}},
                           "federici": {"core": {"excluded_presentations": {"sparrkulee": [1]}}}},
            "presentations": [{"stream": 0}, {"stream": 1}],
            "segments": {"sparrkulee": {"presentation": [0, 0, 1, 1], "s": [100, 100, 100, 20000]}},
            "pools": {"core": {"sparrkulee": [0, 1, 2, 3]}}}


def test_refit_removes_whole_shared_presentation_and_deduplicates():
    windows, stats = core_fit_windows(fixture_manifest())
    assert set(windows) == {0}
    np.testing.assert_array_equal(windows[0], np.unique(100 + C.TICK_OFFS))
    assert stats["n_segments"] == 1 and stats["excluded_presentations"] == [1]


def test_refit_only_uses_available_target_windows():
    recs = [{"reason": None, "n_64": 500, "length": 500, "name": "ok"},
            {"reason": None, "n_64": 30000, "length": 30000, "name": "excluded"}]
    kept, stats = available_windows(fixture_manifest(), recs)
    assert set(kept) == {0} and stats["fit_streams"] == ["ok"]
    recs[0]["reason"] = "no_source"
    assert available_windows(fixture_manifest(), recs)[0] == {}


def test_preserved_outputs_survive_atomic_replacement(tmp_path):
    from auditory_alignment_v3.prior33 import build_rich as BR
    path = tmp_path / BR.META
    path.write_bytes(b"original")
    backup = preserve_previous(tmp_path)
    replacement = tmp_path / "new"
    replacement.write_bytes(b"new")
    replacement.replace(path)
    from pathlib import Path
    assert (Path(backup) / BR.META).read_bytes() == b"original"
    preserve_previous(tmp_path)
    assert (Path(backup) / BR.META).read_bytes() == b"original"
