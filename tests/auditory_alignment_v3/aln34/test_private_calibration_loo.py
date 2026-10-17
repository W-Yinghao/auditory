import numpy as np
import pytest

from auditory_alignment_v3.aln34 import private_calibration_loo as L


def test_remove_self_equals_rebuilding_each_reference_bank():
    x = np.array([[0.0], [1.0], [2.0], [4.0]])
    y = np.array([0., 1., 1., 0.])
    sel = np.array([3, 1, 0])
    K = np.exp(-(x-x[sel].T)**2 / 2)
    base = 0.4
    num, den = K @ y[sel] + base, K.sum(1) + 1
    n, d = L.remove_self(num, den, sel, y[sel])
    for i in range(len(x)):
        keep = sel != i
        assert n[i]/d[i] == pytest.approx((K[i, keep] @ y[sel[keep]] + base)/(K[i, keep].sum() + 1))
    assert n[2] == num[2] and d[2] == den[2]
    assert np.array_equal(num, K @ y[sel] + base)


def test_single_reference_retains_base_pseudocount():
    n, d = L.remove_self([1.3, 0.5], [2., 1.4], [0], [1.])
    assert n[0]/d[0] == pytest.approx(0.3)
    with pytest.raises(ValueError, match="distinct"):
        L.remove_self([1.3], [2.], [0, 0], [1., 1.])
    n, d = L.remove_self([1.2999], [1.9999], [0], [1.], [0.9999])
    assert n[0]/d[0] == pytest.approx(0.3)


def test_all_120_design_cells_and_smoke_selection():
    rr = []
    for seed in (3401, 3407, 3413):
        for fold in range(5):
            for fam, arch, ad in (("E_GENERIC", a, b) for a in ("cbramod", "reve")
                                  for b in ("random_full", "pretrained_peft", "pretrained_full")):
                rr.append({"row": {"experiment_id": str(len(rr)), "family_id": fam, "seed": seed,
                                   "subject_fold": fold, "spec": {"architecture": arch, "adaptation": ad}}})
            for fam in ("E_LOCAL", "E_PUBLIC_TRANSFER"):
                rr.append({"row": {"experiment_id": str(len(rr)), "family_id": fam, "seed": seed,
                                   "subject_fold": fold, "spec": {"source_architecture": "lag_local_tokens"}}})
    assert len(rr) == 120
    selected = L.smoke_units({"units": rr})
    assert len(selected) == 4
    assert {u["row"]["family_id"] for u in selected} == {"E_GENERIC", "E_LOCAL", "E_PUBLIC_TRANSFER"}
