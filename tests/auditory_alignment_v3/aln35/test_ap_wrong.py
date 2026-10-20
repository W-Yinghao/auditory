import copy
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from auditory_alignment_v3.prior33 import contract as C, losses as L, donor_train as D, model as M
from auditory_alignment_v3.aln35.ap_wrong_sampler import (
    strict_permutation, canonical_groups, assert_permutation, feasibility, NoLegalPermutation,
    PairSampler, metadata_banks, mask_sha,
)
from auditory_alignment_v3.aln35.ap_wrong import BatchLedger, state_sha


def keys(families, times=None, presentations=None):
    f = np.asarray(families, dtype=np.int64)
    p = f if presentations is None else np.asarray(presentations, dtype=np.int64)
    t = np.arange(len(f), dtype=np.int64) * 400 if times is None else np.asarray(times, dtype=np.int64)
    return C.pack_key(f, p, t)


@pytest.mark.parametrize("n", [2, 3, 32, 256])
def test_exact_exposures_family_exclusion_rng_repeat(n):
    k = keys(np.arange(n) % (n if n < 4 else max(2, n // 4)))
    p = strict_permutation(k, (), np.random.default_rng(16))
    q = strict_permutation(k, (), np.random.default_rng(16))
    assert np.array_equal(p, q)
    assert_permutation(k, p)
    assert np.array_equal(np.sort(k[p]), np.sort(k))


def test_canonical_alias_duplicate_groups_move_whole():
    k = keys([0, 0, 1, 1, 2, 2, 3, 3], [0, 0, 400, 400, 800, 800, 1200, 1200],
             [0, 1, 2, 3, 4, 5, 6, 7])
    assert len(canonical_groups(k)) == 4
    assert len(canonical_groups(k, (0,))) == 5
    p = strict_permutation(k, (), np.random.default_rng(17))
    assert_permutation(k, p)
    for rows in np.arange(8).reshape(4, 2):
        assert len(set(p[rows] // 2)) == 1


def test_multiplicity_bucket_failure_not_relaxed():
    k = keys([0, 0, 1, 2], [0, 0, 400, 800], [0, 1, 2, 3])
    assert not feasibility(k)[0]
    with pytest.raises(NoLegalPermutation):
        strict_permutation(k, (), np.random.default_rng(8))


def test_same_family_distant_audio_is_not_accepted():
    k = keys([0] * 10)
    assert not feasibility(k)[0]
    with pytest.raises(NoLegalPermutation):
        strict_permutation(k, (), np.random.default_rng(7))


def test_nominal_loss_mask_and_double_views_stay_fixed():
    torch.manual_seed(20)
    k = keys([0, 0, 1, 1, 2, 2], [0, 32, 400, 432, 800, 832])
    p = strict_permutation(k, (), np.random.default_rng(9))
    u1, u2, v = [torch.randn(6, 8, requires_grad=True) for _ in range(3)]
    loss, stats = L.nce_audio_pair(u1, u2, v[p], torch.as_tensor(k), unknown_clock=())
    nominal_pos, nominal_excl = L.nce_masks(torch.as_tensor(np.r_[k, k]), torch.as_tensor(k), unknown_clock=())
    score = L._cos(torch.cat([u1, u2]), v[p], C.TAU)
    expected = (L.masked_lse_nce(score, nominal_pos, nominal_excl).mean()
                + L.masked_lse_nce(score.T, nominal_pos.T, nominal_excl.T).mean()) / 2
    torch.testing.assert_close(loss, expected, rtol=0, atol=0)
    assert stats["n_q_e2a"] == 12 and stats["n_q_a2e"] == 6
    assert stats["pos_per_q_e2a"] == 1 and stats["pos_per_q_a2e"] == 2
    loss.backward()
    assert torch.isfinite(u1.grad).all() and torch.isfinite(u2.grad).all()


def test_h30_schedule_is_old_h30_not_group_best():
    fixed = D.GroupWSD(256, adopted=30, limit=30)
    original = D.GroupWSD(256)
    original.decide(27, {"AP": list(range(27, 0, -1))})
    for step in range(27):
        assert fixed.lr_scale(step) == 1
    for step in range(27, 30):
        assert fixed.lr_scale(step) == original.lr_scale(step, "side")
    assert fixed.steps_at(30) == 30


def test_two_identical_members_unmodified_step_and_resume(tmp_path):
    torch.manual_seed(21)
    layout = C.MONTAGES["private_bdf"]
    enc = M.build_shared(layout, layout, 3401)
    e2 = M.build_shared(layout, layout, 3401)
    assert state_sha(enc.state_dict()) == state_sha(e2.state_dict())
    members = [D._Member("AP", e, "NCE", {"sigma_u": 1., "sigma_v": 1.}, (), {}) for e in (enc, e2)]
    k = keys(np.arange(8))
    batch = SimpleNamespace(x1=torch.randn(8, len(layout), C.L_IN), x2=torch.randn(8, len(layout), C.L_IN),
                            keys=torch.as_tensor(k), layout=layout)
    v = torch.randn(8, 32)
    for member in members:
        member.step(batch, v, None, None, .001, "main")
    assert state_sha(enc.state_dict()) == state_sha(e2.state_dict())
    snapshot = members[0].snapshot()
    members[0].step(batch, v, None, None, .0005, "main")
    members[1].restore(snapshot)
    members[1].step(batch, v, None, None, .0005, "main")
    assert state_sha(enc.state_dict()) == state_sha(e2.state_dict())


def test_ledger_exact_arrays_and_resume_verification(tmp_path):
    k = keys([0, 0, 1, 1])
    p = strict_permutation(k, (), np.random.default_rng(40))
    batch = SimpleNamespace(step=0, keys=torch.as_tensor(k), stratum="test")
    ledger = BatchLedger(tmp_path, ())
    ledger.add(batch, p)
    st = ledger.state()
    restored = BatchLedger(tmp_path, (), st)
    assert restored.chain == ledger.chain
    with np.load(tmp_path / st["files"][0]["name"]) as arr:
        assert np.array_equal(arr["nominal_keys"][0], k)
        assert np.array_equal(arr["actual_audio_keys"][0], k[p])
        assert arr["nominal_positive_exclusion_mask_sha256"][0] == mask_sha(k, ())
