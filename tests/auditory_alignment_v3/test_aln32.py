"""ADDENDUM_07 synthetic checks: masked support windows (slice, zero before the anchor's segment start, segment lookup), post-only
windows, raw-ridge encoder normalisation, update-ledger semantics and persistence, generated trainer text, plan_ext block 4 rows."""
import json

import torch

from auditory_alignment_v3 import core, fm_aligned, fm_aligned32, local_support, run


def test_masked_windows_segment_start():
    C, N = 2, 400
    E = torch.arange(C * N, dtype=torch.float32).reshape(C, N) + 1
    starts = torch.tensor([10, 100, 200])  # contiguous segments of a trial
    e = torch.tensor([10, 15, 100, 130, 250]); a, b = -8, 6
    X = local_support.masked_windows(E, e, a, b, starts)
    for i, ei in enumerate(e.tolist()):
        s = max(x for x in starts.tolist() if x <= ei)
        for j, off in enumerate(range(a, b)):
            k = ei + off
            assert torch.equal(X[i, :, j], E[:, k] if k >= s else torch.zeros(C))
    assert (X[0, :, :8] == 0).all() and (X[1, :, :3] == 0).all() and (X[3] != 0).all()


def test_postonly_windows_zero_left():
    bt = object.__new__(fm_aligned32.PostOnlyAlignedBatcher)
    bt.E = torch.arange(3 * 500, dtype=torch.float32).reshape(3, 500) + 1; bt.pre, bt.post = 5, 7
    e0 = torch.tensor([100]); t = torch.tensor([[0, 20]])
    W = bt.windows(e0, t); ref = fm_aligned.aligned_windows(bt.E, e0, t, 5, 7)
    assert (W[..., :5] == 0).all() and torch.equal(W[..., 5:], ref[..., 5:])


def test_raw_ridge_normalised():
    m = local_support.RawRidge(12, 4)
    u = m([torch.randn(6, 3, 4)])
    assert u.shape == (6, 4) and torch.allclose(u.norm(dim=-1), torch.ones(6), atol=1e-5)


def test_ledger(tmp_path):
    p1, p2 = torch.nn.Parameter(torch.ones(3)), torch.nn.Parameter(torch.ones(2))
    pg = [{"params": [p1], "lr": 0.1, "name": "block0"}, {"params": [p2], "lr": 0.2, "name": "other"}]
    led = fm_aligned32._ledger_init(pg, str(tmp_path / "u"))
    p2.requires_grad_(False)
    fm_aligned32._ledger_epoch(led, pg, 0)
    p1.grad = torch.ones(3); fm_aligned32._ledger_step(led, pg)
    p2.requires_grad_(True); fm_aligned32._ledger_epoch(led, pg, 1); fm_aligned32._ledger_epoch(led, pg, 1)  # duplicate epoch ignored (resume)
    p2.grad = torch.ones(2); fm_aligned32._ledger_step(led, pg)
    fm_aligned32._ledger_save(led)
    L = fm_aligned32._ledger_init(pg, str(tmp_path / "u"))["groups"]  # persisted across a restart
    assert L[0]["first_open_epoch"] == 1 and L[0]["epochs_open"] == 2 and L[0]["grad_steps"] == 2 and abs(L[0]["lr_sum"] - 0.2) < 1e-12
    assert L[1]["first_open_epoch"] == 2 and L[1]["epochs_open"] == 1 and L[1]["grad_steps"] == 1


def test_generated_trainer_text():
    src = open(fm_aligned32.__file__).read().split('"""', 2)[2]
    assert src.count("def fit_aligned32(") == 1 and "def fit_aligned(" not in src
    assert 'if recipe == "warmup_then_all_v1":\n            n_open = 0 if ep < WARMUP else len(groups_bb)' in src
    assert 've = 1 if recipe in ("aln3", "full_onestep_v1", "warmup_then_all_v1")' in src and "_ledger_step(led, pg); opt.step()" in src


def test_registry_and_block4_rows():
    assert core.FAMILY_GROUP["ALN32_TRUE_FULL"] == "aligned32" and run.RUNNER["local_support"] == "local_support"
    assert core.code_hash("B_ALIGNED").startswith("1add5d0f70527fa8") and core.code_hash("B_DENSE").startswith("040d71894b35349f")
    ext = run.ext_rows(); by = {r["experiment_id"]: r for r in ext + core.load_rows()}
    fam = lambda f: [r for r in ext if r["family_id"] == f]
    assert (len(fam("ALN32_LOCAL_SUPPORT")), len(fam("ALN32_POSTONLY_FM")), len(fam("ALN32_TRUE_FULL"))) == (75, 100, 400)
    for r in fam("ALN32_TRUE_FULL"):
        b = by[r["base_plan_row"]]; s = r["spec"]
        assert b["family_id"] == "B_ALIGNED" and b["spec"]["adaptation"] == s["adaptation"] in ("random_full", "pretrained_full")
        assert s["recipe"] in ("full_onestep_v1", "warmup_then_all_v1") and s["lr_backbone"] in (1e-5, 3e-4) and s["llrd"] == 1.0
    pairs = {}
    for r in fam("ALN32_TRUE_FULL"):  # every random row has its pretrained twin with the same recipe / lr / cell
        s = r["spec"]; k = (r["dataset"], r["subject_fold"], r["content_fold"], s["architecture"], s["recipe"], s["lr_backbone"])
        pairs.setdefault(k, set()).add(s["adaptation"])
    assert all(v == {"random_full", "pretrained_full"} for v in pairs.values()) and len(pairs) == 200
    for r in fam("ALN32_LOCAL_SUPPORT"):
        b = by[r["base_plan_row"]]
        assert b["family_id"] == "A_LOCAL" and b["spec"]["architecture"] == "lag_local_tokens" and r["spec"]["variant"] in local_support.SUPPORT
