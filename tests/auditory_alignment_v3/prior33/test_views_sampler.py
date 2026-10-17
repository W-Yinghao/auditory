"""M3 views and sampler tests (PUBLIC_PRIOR_DESIGN.md §7.1 items 1 (TickReps), 2 (private input), 4a, 4c, 4d, 4h, 4i, 8, 9 (pools,
train_p), 10a, and the M3 task list): batch geometry against the caches, one shared batch stream per group (identical batches
and stream hashes, core = rich), exact resume after state / load_state, cross-person positives (different participants, equal
keys), the XM derangement without fixed points, leave-target-out and data use over 10^4 draws per donor set and block, no access to
the target cohort's outer test, zero-shot pools that include every participant but no target training participant (pools equal
to the adapted rows', checked end to end through ev1.evaluate_continuous), the target-stage batcher on the ticks, the access
modes, the restricted-participant guard (an open-file audit hook) and the private input at 64 Hz. Synthetic data only
(tests/.../prior33/fixtures.py; scale 4 where a design batch is needed); CPU; about 1-2 minutes.

M3 review cases (section at the end): the XM rule on strata with the real family structure (no feasible batch left with a
violation; the exact minimum on infeasible ones), the twin-aware XM partner rule, the acoustic XM condition key, the fixed shared
sets against every target's excluded presentations, the table stream / ignored stream / lead / T_env against the manifest (and
an unmappable SparrKULee table), the bank modes "pieces" / "segments" with the chunked gather and iter_ticks, the sampler's own
piece-restricted banks, the CSX core-pool check, zero-shot through ev1 with the EEG and audio rows actually read, and the rows
actually read by the A_LOCAL target-stage access pattern.

M3 review round 2 (last section): the attended side and the acoustic condition in the table-vs-manifest piece check (FAU
left / right remap, DTU HI / NH original, SparrKULee noise condition, SNR and noise file), the query side of TickBatcher bound
to the manifest cell, bridge_rows re-checking leave-target-out and the sampler's row rules, the restricted-path names
(sub-019.npy, sub-019-eeg.npy, ...) and the full manifest constants block. Scale-1 fixture only.

M3 review round 3 (after the last section): unique presentation keys, targets() refusing a presentation without a stream (and ids
that would wrap), segment rows in their role's slab with their presentation's family and kind, TickBatcher.query_coverage,
bridge_rows' cache root, and check_donor_rows' bounds and restricted-first order. Scale-1 fixture only."""
import contextlib
import copy
import json
import os
import shutil
import sys
import types

import numpy as np
import pytest
import torch
from scipy.optimize import linear_sum_assignment

from auditory_alignment_v3.prior33 import contract as C
from auditory_alignment_v3.prior33 import sampler as SM
from auditory_alignment_v3.prior33 import views as V

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixtures import make_synthetic_manifest, synthetic_kids  # noqa: E402

COMBOS = [(t, b) for t in ("fau", "dtu", "federici", "private_bdf") for b in ("core", "rich", "csx") if not (t == "fau" and b == "csx")]
SPEC = {"architecture": "lag_local_tokens", "window": "full", "objective": "NCE", "training_task": "paired_alignment"}

# ---------------------------------------------------------------------------------------------------------- open-file audit hook
_OPENED = None


def _audit(event, args):
    if _OPENED is not None and event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        _OPENED.append(os.path.abspath(os.fsdecode(args[0])))


sys.addaudithook(_audit)


@contextlib.contextmanager
def opened_files():
    global _OPENED
    _OPENED = []
    try:
        yield _OPENED
    finally:
        _OPENED = None


# ---------------------------------------------------------------------------------------------------------- fixtures
@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    return make_synthetic_manifest(tmp_path_factory.mktemp("m3_fx1"))


@pytest.fixture(scope="module")
def fx4(tmp_path_factory):
    return make_synthetic_manifest(tmp_path_factory.mktemp("m3_fx4"), scale=4)


@pytest.fixture(scope="module")
def man(fx):
    return V.open_manifest(fx["manifest_path"], fx["manifest_sha256"])


@pytest.fixture(scope="module")
def man4(fx4):
    return V.open_manifest(fx4["manifest_path"], fx4["manifest_sha256"])


@pytest.fixture(scope="module")
def banks4(man4):
    """One bank per donor cohort (rich loaded; SparrKULee with its dev and bridge_cal slabs), shared by the samplers."""
    return {c: V.DonorBank(man4, c, ("fit", "dev", "bridge_cal") if c == "sparrkulee" else ("fit",), "cpu", rich=True)
            for c in V.DONOR_COHORTS}


def _sampler(man4, banks4, target, block, seed=3401):
    return SM.DonorSampler(man4, target, block, seed, "cpu", banks=banks4)


def _table(fx, c):
    info = fx["manifest"]["cohorts"][c]
    with open(os.path.join(fx["root"], info["dir"], info["table"])) as f:
        t = json.load(f)
    return t, t[info["items"]]


def _npy(fx, c, name):
    info = fx["manifest"]["cohorts"][c]
    return np.load(os.path.join(fx["root"], info["dir"], name), mmap_mode="r", allow_pickle=False)


def _streams(fx, c, name="streams"):
    info = fx["manifest"]["cohorts"][c]
    with open(os.path.join(fx["root"], info["dir"], info[name])) as f:
        return json.load(f)["streams"]


def _same_batch(a, b):
    for f in ("x1", "x2", "y", "keys", "part1", "part2", "fam_s", "chan_mask"):
        if not torch.equal(getattr(a, f), getattr(b, f)):
            return False
    if (a.rich is None) != (b.rich is None) or (a.rich is not None and not (torch.equal(a.rich_mask, b.rich_mask) and all(
            torch.allclose(a.rich[k], b.rich[k], rtol=0, atol=0, equal_nan=True) for k in a.rich))):   # absent rich rows are NaN
        return False
    return (a.stratum == b.stratum and np.array_equal(a.seg_ids, b.seg_ids) and np.array_equal(a.partner_ids, b.partner_ids)
            and np.array_equal(a.ticks, b.ticks) and a.montage == b.montage)


def _twin_groups(man, smp):
    """{participant id: smallest id of its HC N / HC-v N pair} from the manifest partner_exclusions (the XM twin rule)."""
    out = {}
    for c, a, b in man["partner_exclusions"]:
        if c in smp.banks:
            pa, pb = smp.banks[c].pid[a], smp.banks[c].pid[b]
            out[pa] = out[pb] = min(pa, pb)
    return out


def _min_violations(fam, lis, par):
    """Exact minimum of the XM hard-constraint violations over all derangements (independent of the sampler's cost)."""
    fam, lis, par = (np.asarray(a) for a in (fam, lis, par))
    H = (fam[None, :] == fam[:, None]).astype(float) + (par[None, :] == lis[:, None])
    np.fill_diagonal(H, np.inf)
    r, c = linear_sum_assignment(H)
    return int(H[r, c].sum())


def _fake_batch(fams, lis, par, pres):
    """A duck-typed Batch for derangement(): seg_ids, keys (family, presentation, s), part1, part2 per segment x 8 anchors."""
    r8 = lambda a: torch.as_tensor(np.repeat(np.asarray(a, dtype=np.int64), 8))   # noqa: E731
    k = C.pack_key(np.repeat(np.asarray(fams, np.int64), 8), np.repeat(np.asarray(pres, np.int64), 8),
                   np.tile(np.arange(8), len(fams)) + 1000)
    return types.SimpleNamespace(seg_ids=np.arange(len(fams)), keys=torch.as_tensor(k), part1=r8(lis), part2=r8(par))


def _rows_to_pieces(items, rows, guards):
    """Cache row of each window start -> table position of its piece; asserts every window [r, r + 38) lies in the piece's guards."""
    cached = sorted((int(it["row_offset"]), i) for i, it in enumerate(items) if it["row_offset"] is not None)
    starts = np.array([a for a, _ in cached])
    j = np.searchsorted(starts, rows, side="right") - 1
    piece = np.array([cached[k][1] for k in j])
    off = np.array([items[p]["row_offset"] for p in piece]); T = np.array([items[p]["T_eeg"] for p in piece])
    assert (rows >= off + guards[0]).all() and (rows + C.L_IN <= off + T - guards[1]).all()
    return piece


def _audio_to_streams(streams, s0):
    """Envelope index of each target window start -> stream id; asserts every window [s, s + 8) avoids the 41-sample edges."""
    so = np.array([s["offset"] for s in streams]); sl = np.array([s["length"] for s in streams])
    k = np.searchsorted(so, s0, side="right") - 1
    assert ((s0 >= so[k] + C.ENV_EDGE) & (s0 + C.N_TGT <= so[k] + sl[k] - C.ENV_EDGE)).all()
    return k


# ---------------------------------------------------------------------------------------------------------- manifest
def test_open_manifest_verifies_sha(fx, tmp_path):
    m = V.open_manifest(fx["manifest_path"], fx["manifest_sha256"])
    assert isinstance(m, dict) and m.sha256 == fx["manifest_sha256"] and m.root == os.path.abspath(fx["root"])
    assert V.open_manifest(fx["manifest_path"], fx["manifest_sha256"][:16]).sha256 == fx["manifest_sha256"]
    for bad in (None, "", fx["manifest_sha256"][:15], "z" * 64):
        with pytest.raises(ValueError):
            V.open_manifest(fx["manifest_path"], bad)
    with pytest.raises(ValueError, match="sha256"):
        V.open_manifest(fx["manifest_path"], "0" * 64)
    raw = open(fx["manifest_path"], "rb").read()
    p = tmp_path / "manifest.json"
    p.write_bytes(raw.replace(b'"seg_step": 320', b'"seg_step": 321'))
    import hashlib
    with pytest.raises(ValueError, match="constants"):           # a self-consistent sha does not excuse a contract mismatch
        V.open_manifest(str(p), hashlib.sha256(p.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match="sha256"):              # the original sha does not match the edited bytes
        V.open_manifest(str(p), fx["manifest_sha256"])
    p.write_bytes(raw.replace(b'"schema": "prior33_manifest_v2"', b'"schema": "prior33_manifest_v1"'))
    with pytest.raises(ValueError, match="schema"):
        V.open_manifest(str(p), hashlib.sha256(p.read_bytes()).hexdigest())
    m2 = V.open_manifest(fx["manifest_path"], fx["manifest_sha256"], root=str(tmp_path))      # a private copy needs the cache root
    with pytest.raises(FileNotFoundError):
        V.cohort_dir(m2, "fau")
    with pytest.raises(ValueError, match="root"):
        V.cohort_dir(dict(fx["manifest"]), "fau")


# ---------------------------------------------------------------------------------------------------------- batch geometry
def test_batch_geometry_against_the_caches(fx4, man4, banks4):
    """Every stratum of every donor set and block: x1 / x2 [256, C, 38] float16 equal the cache windows at the anchor ticks (zero
    outside the read channels), y [256, 8] the envelope, keys / fam_s / participant ids / masks / segment ids consistent (§2.2,
    §2.6); rich targets only in the rich block."""
    m, P = man4, man4["presentations"]
    caches = {c: _npy(fx4, c, m["cohorts"][c]["caches"]["A"]) for c in m["cohorts"]}
    envs = {c: _npy(fx4, c, m["cohorts"][c]["env"]) for c in m["cohorts"]}
    richs = {c: _npy(fx4, c, m["cohorts"][c]["rich"]) for c in m["cohorts"]}
    tabs = {c: _table(fx4, c)[1] for c in m["cohorts"]}
    streams = {c: _streams(fx4, c) for c in m["cohorts"]}
    avail = {c: [r["available"] for r in _streams(fx4, c, "rich_streams")] for c in m["cohorts"]}
    twins = {(a, b) for _, a, b in m["partner_exclusions"]} | {(b, a) for _, a, b in m["partner_exclusions"]}
    seen = set()
    for target, block in COMBOS:
        smp = _sampler(m, banks4, target, block)
        for stratum, b in smp.calibration_batches().items():
            c = SM.coh_of(stratum); S = m["segments"][c]; n_ch = m["cohorts"][c]["n_ch"]
            assert b.stratum == stratum and b.cohort == c and b.layout == tuple(m["cohorts"][c]["layout"])
            assert b.x1.shape == b.x2.shape == (256, n_ch, 38) and b.x1.dtype == b.x2.dtype == torch.float16
            assert b.y.shape == (256, 8) and b.y.dtype == torch.float32 and b.chan_mask.shape == (2, 256, n_ch)
            assert b.keys.dtype == b.part1.dtype == b.part2.dtype == b.fam_s.dtype == torch.int64
            assert b.seg_ids.shape == b.partner_ids.shape == (32,) and b.ticks.shape == (32, 8)
            assert len({(S["presentation"][r], S["s"][r]) for r in b.seg_ids}) == 32            # distinct (presentation, s)
            assert ((b.ticks - b.ticks[:, :1]) == 31 * np.arange(8)).all() and b.ticks[:, 0].max() <= 30 and b.ticks.min() >= 0
            assert len(torch.unique(b.keys)) == 256                                              # one key per anchor
            f, p, s_ = C.unpack_key(b.keys)
            assert torch.equal(s_, b.fam_s)
            offs = C.TICK_OFFS[b.ticks].reshape(-1)
            for view, rows, x in ((0, b.seg_ids, b.x1), (1, b.partner_ids, b.x2)):
                rr = np.repeat(rows, 8)
                ref = np.stack([np.asarray(caches[c][tabs[c][S["piece"][r]]["row_offset"] + S["s"][r] + o + np.arange(38)]).T
                                for r, o in zip(rr, offs)])
                mask = b.chan_mask[view].numpy()
                assert np.array_equal(x.numpy(), np.where(mask[:, :, None], ref, 0).astype(np.float16)), (target, block, stratum)
                for i, r in enumerate(rr):
                    it = tabs[c][S["piece"][r]]
                    assert all(not mask[i, b.layout.index(C.canonical(n))] for n in it["masked"])
                    assert S["role"][r] == "fit" and S["kind"][r] == ("cs" if stratum == "fau_cs" else "ss")
            rr = np.repeat(b.seg_ids, 8)
            pres = np.array([S["presentation"][r] for r in rr]); s = np.array([S["s"][r] for r in rr])
            assert np.array_equal(f.numpy(), [P[q]["family"] for q in pres]) and np.array_equal(p.numpy(), pres)
            assert np.array_equal(s_.numpy(), [P[q]["family_offset"] for q in pres] + s + offs)
            t0 = np.array([streams[c][P[q]["stream"]]["offset"] for q in pres]) + s + offs
            assert np.array_equal(b.y.numpy(), np.stack([envs[c][a:a + 8] for a in t0]))
            pids = {pp: smp.banks[c].pid[pp] for pp in set(S["participant"])}
            assert np.array_equal(b.part1.numpy(), [pids[S["participant"][r]] for r in rr])
            assert np.array_equal(b.part2.numpy(), [pids[S["participant"][r]] for r in np.repeat(b.partner_ids, 8)])
            for r, q in zip(b.seg_ids, b.partner_ids):
                a_, q_ = S["participant"][r], S["participant"][q]
                assert q_ != a_ and (a_, q_) not in twins and (S["presentation"][q], S["s"][q]) == (S["presentation"][r], S["s"][r])
            if b.montage is not None:
                drop = torch.as_tensor(~SM.montage_masks(b.layout)[b.montage])
                assert c in ("sparrkulee", "dtu") and not b.chan_mask[:, :, drop].any()
                assert not b.x1[:, drop].any() and not b.x2[:, drop].any()
            if block == "rich":
                R = np.stack([richs[c][a:a + 8] for a in t0])
                ok = np.array([avail[c][P[q]["stream"]] for q in pres]) & np.isfinite(R).all((1, 2))
                assert torch.equal(b.rich_mask, torch.as_tensor(ok)) and b.rich["ss"].shape == (256, 32) and b.rich["sc"].shape == (256, 8)
                assert np.array_equal(b.rich["ss"].numpy()[ok], R[ok][:, :, :4].reshape(-1, 32))
                assert np.array_equal(b.rich["sc"].numpy()[ok], R[ok][:, :, 4]) and (c != "federici" or not ok.any())
            else:
                assert b.rich is None and b.rich_mask is None
            seen.add((target, block, stratum))
    assert {s for _, _, s in seen} == {"sparrkulee", "fau", "dtu", "federici", "fau_cs"}
    assert len(seen) == sum(len(m["donor_sets"][t][SM.BLOCKS[b]]["strata"]) for t, b in COMBOS)


def test_next_batch_stratum_weights_and_montage(man4, banks4):
    """Strata follow the manifest weights; the montage subset is drawn with p = 0.5 for 64-channel strata only (§2.6)."""
    smp = _sampler(man4, banks4, "private_bdf", "csx", seed=11)
    n, counts, aug, n64 = 10_000, {s: 0 for s in smp.strata}, {k: 0 for k in SM.AUG_NAMES}, 0
    for _ in range(n):
        stratum, rows, partners, ticks, montage = smp.next_draw()
        counts[stratum] += 1
        if SM.coh_of(stratum) in ("sparrkulee", "dtu"):
            n64 += 1
            aug[montage] = aug.get(montage, 0) + 1
        else:
            assert montage is None
    for s, w in zip(smp.strata, smp.weights):
        assert abs(counts[s] - n * w) < 5 * np.sqrt(n * w * (1 - w)) + 1, (s, counts[s], n * w)
    on = sum(aug[k] for k in SM.AUG_NAMES)
    assert abs(on - n64 / 2) < 5 * np.sqrt(n64 / 4) and all(abs(aug[k] - on / 3) < 5 * np.sqrt(on * 2 / 9) for k in SM.AUG_NAMES)
    assert [len(v) for v in C.AUG_SUBSETS.values()] == [27, 28, 20] and SM.montage_masks(C.MONTAGES["fau"]) == {}
    b = smp.next_batch()
    assert b.step == n and smp.step == n + 1


# ---------------------------------------------------------------------------------------------------------- one stream per group
def test_group_members_share_one_stream(man4, banks4):
    """§2.6 / §7.1 10a: two samplers with the same (donor set, block, seed) give identical batches and stream hashes; the rich block
    draws the core stream (equal hashes); the XM derangement generator leaves the main stream unchanged; another seed differs."""
    a, b = _sampler(man4, banks4, "dtu", "core"), _sampler(man4, banks4, "dtu", "core")
    r, o = _sampler(man4, banks4, "dtu", "rich"), _sampler(man4, banks4, "dtu", "core", seed=3407)
    rr = _sampler(man4, banks4, "dtu", "rich")
    assert a.stream_hash() == b.stream_hash() == r.stream_hash() == o.stream_hash()      # h_0 is the same tag for every group
    diff = 0
    for _ in range(40):
        ba, bb, br, bo = a.next_batch(), b.next_batch(), r.next_batch(), o.next_batch()
        a.derangement(ba)                                                                  # only a draws XM permutations
        assert _same_batch(ba, bb)
        assert br.stratum == ba.stratum and np.array_equal(br.seg_ids, ba.seg_ids) and torch.equal(br.x1, ba.x1)
        assert torch.equal(br.y, ba.y) and br.rich is not None and ba.rich is None
        assert _same_batch(br, rr.next_batch())                                            # rich batches (NaN rows) compare too
        diff += not np.array_equal(bo.seg_ids, ba.seg_ids)
    assert a.stream_hash() == b.stream_hash() == r.stream_hash() != o.stream_hash() and diff >= 35
    for _ in range(1000 - 40):
        a.next_draw(); r.next_draw()
    assert a.hash_log == r.hash_log and [s for s, _ in a.hash_log] == [1000] and a.hash_log[0][1] == a.stream_hash()
    csx = _sampler(man4, banks4, "dtu", "csx")
    assert csx.strata == a.strata + ["fau_cs"] and csx.next_batch().stratum in csx.strata


def test_exact_resume_after_state_and_load_state(man4, banks4, tmp_path):
    """state() / load_state(): the next batches, XM permutations, stream hash and hash log continue exactly, after a JSON and a
    torch.save round trip; a state of another configuration is refused."""
    sk = [i for i, p in enumerate(man4["presentations"]) if p["cohort"] == "sparrkulee"][:1]
    hard = _fake_batch(np.r_[np.zeros(31, np.int64), 1], np.arange(32), np.arange(32) + 100, sk * 32)   # forces the assignment
    ref = _sampler(man4, banks4, "federici", "csx", seed=3413)
    for _ in range(7):
        ref.derangement(ref.next_batch())
    assert ref.derangement(hard)[1]["method"] == "assignment"          # the fallback's tie-break draws are part of the state
    st = ref.state()
    (tmp_path / "st.json").write_text(json.dumps(st))
    torch.save(st, tmp_path / "st.pt")
    nxt = []
    for k in range(6):
        bt = ref.next_batch()
        nxt.append((bt, ref.derangement(bt), ref.derangement(hard) if k % 2 else None))
    for loaded in (json.loads((tmp_path / "st.json").read_text()), torch.load(tmp_path / "st.pt", weights_only=False)):
        new = _sampler(man4, banks4, "federici", "csx", seed=3413)
        new.load_state(loaded)
        assert new.step == 7 and new.stream_hash() == st["chain"]
        for bt, (perm, stats), h in nxt:
            b2 = new.next_batch()
            p2, s2 = new.derangement(b2)
            assert _same_batch(bt, b2) and np.array_equal(perm, p2) and stats == s2 and b2.step == bt.step
            if h is not None:
                ph, sh = new.derangement(hard)
                assert np.array_equal(ph, h[0]) and sh == h[1] and sh["method"] == "assignment"
        assert new.stream_hash() == ref.stream_hash() and new.state()["rng"] == ref.state()["rng"]
        assert new.state()["xm_rng"] == ref.state()["xm_rng"]
    old = copy.deepcopy(st); old["schema"] = "prior33_donor_sampler_state_v1"     # a state from before the assignment fallback
    with pytest.raises(ValueError, match="schema"):
        _sampler(man4, banks4, "federici", "csx", seed=3413).load_state(old)
    other = _sampler(man4, banks4, "federici", "csx", seed=3401)
    with pytest.raises(ValueError, match="configuration"):
        other.load_state(st)
    with pytest.raises(ValueError, match="configuration"):
        _sampler(man4, banks4, "federici", "rich", seed=3413).load_state(st)


# ---------------------------------------------------------------------------------------------------------- positives and XM
def test_cross_person_positives_different_participants_same_key(fx4, man4, banks4):
    """§2.5 / §7.1 4a, 4d: each anchor's two views come from different participants (never an HC / HC-v twin) with the same key,
    i.e. the same presentation and tick; under the contract masks every query's only positive is its own anchor in the other view."""
    from auditory_alignment_v3.prior33.losses import nce_masks, unknown_clock_families
    uc = unknown_clock_families(man4)
    tabs = {c: _table(fx4, c)[1] for c in man4["cohorts"]}
    for target, block in (("fau", "core"), ("private_bdf", "csx"), ("dtu", "rich")):
        smp = _sampler(man4, banks4, target, block, seed=5)
        for b in [smp.next_batch() for _ in range(12)] + list(smp.calibration_batches().values()):
            S = man4["segments"][b.cohort]
            assert (b.part1 != b.part2).all()
            for r, q in zip(b.seg_ids, b.partner_ids):
                ir, iq = tabs[b.cohort][S["piece"][r]], tabs[b.cohort][S["piece"][q]]
                assert ir["participant"] != iq["participant"] and ir["presentation"] == iq["presentation"] == S["presentation"][r]
                assert S["s"][r] == S["s"][q] and S["s"][r] in ir["segment_starts"] and S["s"][q] in iq["segment_starts"]
            pos, excl = nce_masks(b.keys, b.keys, b.part1, b.part2, unknown_clock=uc)
            assert torch.equal(pos, torch.eye(256, dtype=torch.bool)) and not (pos & excl).any()
            fam, pres, s = C.unpack_key(b.keys)
            near = (fam[:, None] == fam[None]) & ((s[:, None] - s[None]).abs() <= C.NEIGHBOR) & ~torch.eye(256, dtype=torch.bool)
            assert not (near & ~excl).any()                   # the +-2 s family-clock neighbours are masked
    hi = {p["participant"] for p in _table(fx4, "dtu")[0]["participants"] if p["group"] == "hi"}
    smp = _sampler(man4, banks4, "fau", "core", seed=9)
    for _ in range(3000):
        stratum, rows, partners, _, _ = smp.next_draw()
        if stratum == "dtu":                                  # §7.1 4c: DTU HI rows are never cross-person eligible
            S = man4["segments"]["dtu"]
            assert not ({S["participant"][r] for r in rows} | {S["participant"][q] for q in partners}) & hi


def test_derangement_has_no_fixed_points_and_keeps_x1_keys(man4, banks4):
    """§2.6 / §7.1 4i: pi has no fixed point on every batch; violations are counted exactly; the XM view takes X2[pi] with X1's keys;
    a feasible batch gets a draw with no violation and an infeasible one counts its violations; the main stream is unchanged."""
    for target, block in (("private_bdf", "csx"), ("fau", "core")):
        smp, other = _sampler(man4, banks4, target, block, seed=21), _sampler(man4, banks4, target, block, seed=21)
        twin = _twin_groups(man4, smp)
        for _ in range(30):
            b = smp.next_batch()
            assert _same_batch(b, other.next_batch())
            perm, st = smp.derangement(b)
            assert sorted(perm) == list(range(32)) and not (perm == np.arange(32)).any() and st["fixed_points"] == 0
            fam = C.unpack_key(b.keys)[0].numpy().reshape(32, 8)[:, 0]
            lis, par = (np.array([twin.get(int(x), int(x)) for x in v.numpy().reshape(32, 8)[:, 0]]) for v in (b.part1, b.part2))
            assert st["violations_family"] == int((fam[perm] == fam).sum()) and st["violations_partner"] == int((par[perm] == lis).sum())
            assert st["violations"] == st["violations_family"] + st["violations_partner"] and 1 <= st["draws"] <= SM.XM_DRAWS
            assert 0 <= st["same_condition_fraction"] <= 1 and st["constraints_met"] == (st["violations"] == 0)
            vmin = _min_violations(fam, lis, par)
            assert st["violations"] == vmin and st["feasible"] == st["constraints_met"] == (vmin == 0)
            assert st["method"] in ("random_draw", "assignment") and (st["method"] == "random_draw" or st["draws"] == SM.XM_DRAWS)
            xm = smp.xm_view(b, perm)
            rows = (perm[:, None] * 8 + np.arange(8)).reshape(-1)
            assert torch.equal(xm.keys, b.keys) and torch.equal(xm.x2, b.x2[rows]) and torch.equal(xm.part2, b.part2[rows])
            assert torch.equal(xm.chan_mask2, b.chan_mask[1][rows])
    smp = _sampler(man4, banks4, "fau", "core", seed=1)

    def fake(fams, lis, par, pres):
        r8 = lambda a: torch.as_tensor(np.repeat(np.asarray(a, dtype=np.int64), 8))   # noqa: E731
        k = C.pack_key(np.repeat(fams, 8), np.repeat(pres, 8), np.tile(np.arange(8), len(fams)) + 1000)
        return types.SimpleNamespace(seg_ids=np.arange(len(fams)), keys=torch.as_tensor(k), part1=r8(lis), part2=r8(par))
    sk = [i for i, p in enumerate(man4["presentations"]) if p["cohort"] == "sparrkulee"][:4]
    ok = fake(np.arange(32) % 16, np.arange(32), np.arange(32) + 100, [sk[i % 4] for i in range(32)])   # 16 families: feasible
    perm, st = smp.derangement(ok)
    assert st["violations"] == 0 and st["feasible"] and st["method"] == "random_draw" and not (perm == np.arange(32)).any()
    one = fake(np.zeros(32, np.int64), np.arange(32), np.arange(32) + 100, [sk[0]] * 32)                  # a single family: infeasible
    perm, st = smp.derangement(one)
    assert st["violations_family"] == 32 and not st["feasible"] and not st["constraints_met"] and st["draws"] == SM.XM_DRAWS
    assert st["method"] == "assignment" and not (perm == np.arange(32)).any() and sorted(perm) == list(range(32))
    # 31 segments of one family and 1 of another: infeasible; the assignment reaches the exact minimum of violations
    fams = np.r_[np.zeros(31, np.int64), 1]
    perm, st = smp.derangement(fake(fams, np.arange(32), np.arange(32) + 100, [sk[0]] * 32))
    assert not st["feasible"] and st["violations"] == _min_violations(fams, np.arange(32), np.arange(32) + 100) == 30


# ---------------------------------------------------------------------------------------------------------- data use
def test_leave_target_out_and_data_use_over_10k_draws(fx4, man4, banks4):
    """§7.1 8: 10^4 draws per donor set and block hold no target-cohort piece; never private_bdf, the phantom, a DTU HI listener or
    a restricted participant; SparrKULee rows are donor-fit only (no dev / bridge_cal / holdout / control / rule-excluded run);
    fau_cs only in CSX; no excluded (overlapping) presentation; no shared-audio span; HC / HC-v twins are never paired."""
    m = man4
    shared = {}
    for d in m["shared_audio"]:
        shared.setdefault(d["presentation"], []).append(d["span"])
    parts = {c: {p["participant"]: p for p in _table(fx4, c)[0]["participants"]} for c in m["cohorts"]}
    twins = {(a, b) for _, a, b in m["partner_exclusions"]} | {(b, a) for _, a, b in m["partner_exclusions"]}
    excluded_runs = set(fx4["truth"]["excluded_runs"])
    sk_items = _table(fx4, "sparrkulee")[1]
    for target, block in COMBOS:
        smp = _sampler(m, banks4, target, block, seed=77)
        ds = m["donor_sets"][target][SM.BLOCKS[block]]
        assert set(smp.banks) == {SM.coh_of(s) for s in ds["strata"]} and target not in smp.banks and "private_bdf" not in smp.banks
        rows_by, used = {s: [] for s in ds["strata"]}, set()
        for _ in range(10_000):
            stratum, rows, partners, _, _ = smp.next_draw()
            rows_by[stratum].append(np.r_[rows, partners])
        for stratum, lst in rows_by.items():
            if not lst:
                continue
            used.add(stratum)
            c = SM.coh_of(stratum); S = m["segments"][c]
            R = np.unique(np.concatenate(lst))
            assert c != target and stratum in ds["strata"] and (stratum != "fau_cs" or block == "csx")
            pool = set(m["pools"]["csx"]["fau_cs"] if stratum == "fau_cs" else m["pools"]["core"][c])
            excl = set(ds["excluded_presentations"][stratum])
            for r in R:
                p = parts[c][S["participant"][r]]
                assert r in pool and S["role"][r] == "fit" and S["presentation"][r] not in excl and S["n_partners"][r] >= 1
                assert p["donor"] and not p.get("test_only") and p["group"] not in ("Artifact", "hi") and S["participant"][r] not in V.RESTRICTED
                for a, b in shared.get(S["presentation"][r], ()):
                    assert not (a < S["s"][r] + C.SPAN_EEG and S["s"][r] < b)
                if c == "sparrkulee":
                    it = sk_items[S["piece"][r]]
                    assert it["role"] == "fit" and it["run_id"] not in excluded_runs and not it["flags"]
            for prs in lst:
                for r, q in zip(prs[:32], prs[32:]):
                    assert (S["participant"][r], S["participant"][q]) not in twins
        assert used == set(ds["strata"]), (target, block, used)
    S, grp = m["segments"]["federici"], {}            # the would-be HC / HC-v pair exists in the table but is never drawn
    for r in range(len(S["s"])):
        grp.setdefault((S["presentation"][r], S["s"][r]), set()).add(S["participant"][r])
    assert any(a in g and b in g for g in grp.values() for _, a, b in m["partner_exclusions"])


def test_sampler_refuses_broken_donor_sets(fx, man):
    """Leave-target-out, fau_cs outside CSX, the CSX block of target fau, weights that are not the shares, an unknown target."""
    for target, block in (("fau", "csx"), ("sparrkulee", "core"), ("nobody", "core")):
        with pytest.raises(ValueError):
            SM.DonorSampler(man, target, block, 1, "cpu")
    with pytest.raises(ValueError, match="cannot fill"):        # scale 1: the Federici stratum holds < 32 distinct contents
        SM.DonorSampler(man, "dtu", "core", 1, "cpu")
    with pytest.raises(ValueError):
        SM.DonorSampler(man, "fau", "warmup", 1, "cpu")

    def broken(edit):
        m2 = V.Manifest(copy.deepcopy(dict(man)), man.path, None, man.root)
        edit(m2["donor_sets"])
        return m2
    for target, edit, msg in (("fau", lambda d: d["fau"]["core"]["strata"].__setitem__(1, "fau"), "leave-target-out"),
                              ("dtu", lambda d: d["dtu"]["core"].update(strata=d["dtu"]["core"]["strata"][:2] + ["fau_cs"]), "CSX"),
                              ("dtu", lambda d: d["dtu"]["core"].update(weights=[0.5, 0.25, 0.25]), "shares"),
                              ("dtu", lambda d: d["dtu"]["core"].update(n_segments=[1, *d["dtu"]["core"]["n_segments"][1:]],   # shares kept
                                                                        weights=[w / sum([1, *d["dtu"]["core"]["n_segments"][1:]])
                                                                                 for w in [1, *d["dtu"]["core"]["n_segments"][1:]]]),
                               "n_segments")):
        with pytest.raises(ValueError, match=msg):
            SM.DonorSampler(broken(edit), target, "core", 1, "cpu")
    rich = broken(lambda d: d["dtu"]["rich"].update(weights=list(reversed(d["dtu"]["rich"]["weights"]))))
    with pytest.raises(ValueError, match="rich donor set"):
        SM.DonorSampler(rich, "dtu", "rich", 1, "cpu")
    csx = broken(lambda d: d["dtu"]["csx"]["strata"].reverse())
    with pytest.raises(ValueError, match="core strata plus fau_cs"):
        SM.DonorSampler(csx, "dtu", "csx", 1, "cpu")
    assert SM.resolve_donor_set(man, man["donor_sets"]["dtu"]["core"], "core")[0] == "dtu"
    assert SM.resolve_donor_set(man, ["sparrkulee", "fau", "federici"], "panel")[:2] == ("dtu", "core")


def test_restricted_participants_never_opened(fx, man, fx4, man4, tmp_path):
    """No restricted participant's array is opened by the banks, the sampler, the fixed sets or the views (open-file audit hook);
    check_path refuses the decoy (also through a symlink); a table that gives a restricted run cache rows, or a segment row of a
    restricted participant, raises RestrictedAccess before any array is read."""
    decoy = os.path.join(fx4["root"], fx4["truth"]["restricted_files"][0])
    assert os.path.exists(decoy)
    with opened_files() as seen:
        smp = SM.DonorSampler(man4, "private_bdf", "rich", 3401, "cpu", bank_roles={"sparrkulee": ("fit", "dev", "bridge_cal", "control_artefact")})
        for _ in range(20):
            smp.derangement(smp.next_batch())
        SM.selection_sets(man4); SM.bridge_rows(man4, "private_bdf")
        for c in V.TARGET_COHORTS:
            V.target_view(c, 0, man4, "A")
    mine = [p for p in seen if p.startswith(os.path.abspath(fx4["root"]))]
    assert mine and not [p for p in mine if "raw" in p.split(os.sep) or "sub-" in os.path.basename(p)]
    assert any(p.endswith(os.path.join("sparrkulee", "eeg_f16_tmajor.npy")) for p in mine)
    with pytest.raises(V.RestrictedAccess):
        V.check_path(decoy)
    link = tmp_path / "innocent.npy"
    os.symlink(decoy, link)
    with pytest.raises(V.RestrictedAccess):
        V.check_path(str(link))
    for ok in ("/x/dtu/sub-021.h5", "/x/sparrkulee/runs.json", "/x/sparrkulee/sub-023_run.npy"):
        assert V.check_path(ok) == ok
    for bad in ("/x/sparrkulee_nm/sub-019/eeg/a.npy", "/x/sparrkulee/sub-026_ses-1_eeg.npy"):
        with pytest.raises(V.RestrictedAccess):
            V.check_path(bad)
    # a tampered copy: the restricted run claims cache rows -> refused before the cache is opened
    root = tmp_path / "tampered"
    shutil.copytree(fx["root"], root, symlinks=True, ignore=shutil.ignore_patterns("raw"))
    p = root / "sparrkulee" / "runs.json"
    t = json.loads(p.read_text())
    r = next(x for x in t["runs"] if x["sub"] in V.RESTRICTED)
    r.update(row_offset=0, slab="fit", segment_starts=[128])
    os.chmod(p, 0o644); p.write_text(json.dumps(t))
    with opened_files() as seen:
        with pytest.raises(V.RestrictedAccess):
            V.DonorBank(V.Manifest(dict(man), None, None, str(root)), "sparrkulee", ("fit",), "cpu")
    assert not [q for q in seen if q.endswith(".npy")]
    m2 = copy.deepcopy(dict(man))
    m2["segments"]["sparrkulee"]["participant"][0] = "019"
    with pytest.raises(V.RestrictedAccess):
        V.DonorBank(V.Manifest(m2, None, None, man.root), "sparrkulee", ("fit",), "cpu")


def test_bank_roles_and_window_guards(fx, man):
    """DonorBank loads donor role slabs only and refuses windows outside the guards or target windows on the stream edges."""
    for c, roles in (("dtu", ("target_only",)), ("federici", ("target_only",)), ("sparrkulee", ("excluded_rule",)),
                     ("sparrkulee", ("holdout_seen_content",)), ("fau", ("dev",)), ("private_bdf", ("fit",))):
        with pytest.raises(ValueError):
            V.DonorBank(man, c, roles, "cpu")
    b = V.DonorBank(man, "dtu", ("fit",), "cpu")
    S, items = man["segments"]["dtu"], b.items
    hi = next(i for i, it in enumerate(items) if it["slab"] == "target_only")
    with pytest.raises(ValueError, match="loaded"):
        b.gather([hi], [64], [0])
    r = man["pools"]["core"]["dtu"][0]
    piece, s, pres = S["piece"][r], S["s"][r], S["presentation"][r]
    assert b.gather([piece], [s], [319]).shape == (1, 64, 38)
    with pytest.raises(ValueError, match="guards"):
        b.gather([piece], [items[piece]["T_eeg"] - 41 - 37], [0])
    with pytest.raises(ValueError, match="edges"):
        b.targets([pres], [0], [0])
    x, y = b.all_ticks([piece], [s], [pres])
    assert x.shape == (250, 64, 38) and y.shape == (250, 8)
    assert torch.equal(x, b.gather(np.repeat(piece, 250), np.repeat(s, 250), C.TICK_OFFS))


# ---------------------------------------------------------------------------------------------------------- target views
def test_no_access_to_target_outer_test(fx, man, fx4, man4):
    """Donor side: a sampler for target T opens no file of T. Target stage: every cell's training and early-stopping segments come
    from the cell's training participants and fit / es content only; a test participant cannot be forced in; zero-shot reads none."""
    for target in V.TARGET_COHORTS:
        with opened_files() as seen:
            smp = SM.DonorSampler(man4, target, "core", 3401, "cpu")
            smp.next_batch()
        tdir = os.path.join(os.path.abspath(fx4["root"]), man4["cohorts"][target]["dir"]) + os.sep
        assert seen and not [p for p in seen if p.startswith(tdir)] and target not in smp.banks
    for cell in man["cells"]:
        if cell["dataset"] == "private_bdf":
            continue
        ds, sf, cf = cell["dataset"], cell["subject_fold"], cell["content_fold"]
        coh = V.target_view(ds, cf, man, "A")
        bt = V.TickBatcher(coh, SPEC, {"dataset": ds, "subject_fold": sf, "content_fold": cf, "seed": 3401}, "cpu", man)
        ids = [q["id"] for q in coh.participants]
        assert {ids[i] for i in bt.train_p} == set(cell["train"]) and not {ids[i] for i in bt.train_p} & (set(cell["test"]) | set(cell["test_only"]))
        content = cell["content"]
        for i in bt.fit + bt.es:
            sg = coh.segments[i]
            lists = content[sg["kind"]] if ds == "fau" else content
            assert ids[sg["p"]] in cell["train"] and sg["code"] in lists[sg["role"]] and sg["role"] in ("fit", "es") and sg["kind"] == "ss"
        assert bt.fit and (bt.es or ds == "federici" and not content["es"])
        test_i = {ids.index(t) for t in cell["test"]}
        with pytest.raises(ValueError, match="subset"):
            V.TickBatcher(V.target_view(ds, cf, man, "A"), SPEC, {"dataset": ds, "subject_fold": sf, "content_fold": cf}, "cpu", man,
                          train_p=set(bt.train_p) | test_i)
    with pytest.raises(TypeError, match="indices"):            # participant ids are not indices
        V.TickBatcher(V.target_view("fau", 0, man, "A"), SPEC, {"dataset": "fau", "subject_fold": 0, "content_fold": 0}, "cpu", man,
                      train_p={"301"})
    coh = V.target_view("fau", 0, man, "A")
    zs = V.TickBatcher(coh, SPEC, {"dataset": "fau", "subject_fold": 0, "content_fold": 0}, "cpu", man, train_p=set())
    acc = zs.training_access(coh)
    assert zs.zero_shot and zs.fit == zs.es == [] and acc["train_segs"] == acc["es_queries"] == 0 and acc["train_participants"] == []


def test_zero_shot_pools_include_every_participant_and_match_adapted_rows(fx, man):
    """§2.13 / §7.1 9: the views load every participant (the phantom and DTU HI included) in every mode; the stimulus-defined test
    pool (and pool_sha256) of a cell is identical for the adapted view and every zero-shot mode; the zero-shot batcher holds no
    target training participant, and the queries are the fold's test participants (+ test_only sessions) only."""
    for c, modes in (("fau", ("A", "B", "C")), ("dtu", ("A", "C")), ("federici", ("A", "C_partial"))):
        t, items = _table(fx, c)
        all_ids = [p["participant"] for p in t["participants"]]
        cfs = sorted({cell["content_fold"] for cell in man["cells"] if cell["dataset"] == c})
        for cf in cfs:
            views = {m: V.target_view(c, cf, man, m) for m in modes}
            ref = views["A"]
            assert [q["id"] for q in ref.participants] == all_ids
            assert {ref.participants[s["p"]]["id"] for s in ref.segments} == {it["participant"] for it in items if it["row_offset"] is not None}
            for kind in ("ss", "cs"):
                pa = V.pool_of(ref, "test", kind)
                for m, v in views.items():
                    pz = V.pool_of(v, "test", kind)
                    assert pz[0] == pa[0] and [r["s0"] for r in pz[1]] == [r["s0"] for r in pa[1]], (c, cf, m, kind)
            assert len({v.meta["pool_sha256"] for v in views.values()}) == 1 and len({v.meta["view_sha256"] for v in views.values()}) == len(views)
            for cell in (x for x in man["cells"] if x["dataset"] == c and x["content_fold"] == cf):
                sf = cell["subject_fold"]
                row = {"dataset": c, "subject_fold": sf, "content_fold": cf}
                ad = V.TickBatcher(V.target_view(c, cf, man, "A"), SPEC, row, "cpu", man)
                for m in modes:
                    v = V.target_view(c, cf, man, m)
                    zs = V.TickBatcher(v, SPEC, row, "cpu", man, train_p=set())
                    assert zs.train_p == set() and zs.training_access(v)["train_segs"] == 0 and len(v.participants) == len(all_ids)
                    q = {v.participants[i]["id"] for i in V.test_queries(v, sf)}
                    assert q and q <= set(cell["test"]) | set(cell["test_only"]) and not q & set(cell["train"])
                    assert V.pool_of(v, "test", "ss")[0] == V.pool_of(ref, "test", "ss")[0]
                assert ad.train_p and {ref.participants[i]["id"] for i in ad.train_p} == set(cell["train"])


def test_ev1_pools_and_queries_end_to_end(fx, man):
    """ev1.evaluate_continuous with TickReps on an adapted FAU and DTU cell: n_test_candidates equals pool_of's size (the number a
    zero-shot row of the cell must reproduce), the evaluated participants are test_queries, and the attention 2AFC reads s0_ign."""
    from auditory_alignment import evaluate as ev1
    from auditory_alignment_v3.prior33.model import build_shared, fixed_heads
    head = fixed_heads(man, man.root)["env"]
    for c, sf, cf in (("fau", 1, 0), ("dtu", 0, 1)):
        coh = V.target_view(c, cf, man, "A")
        n_pool = len(V.pool_of(coh, "test", "ss")[1])
        q = sorted(coh.participants[i]["id"] for i in V.test_queries(coh, sf))
        qa = {coh.participants[i]["id"] for i in V.test_queries(coh, sf, "cs")}
        bt = V.TickBatcher(coh, SPEC, {"dataset": c, "subject_fold": sf, "content_fold": cf}, "cpu", man)
        enc = build_shared(coh.layout, coh.layout, 3401).eval()
        orig = ev1.Reps
        ev1.Reps = V.TickReps
        try:
            out = ev1.evaluate_continuous("NCE", enc, head, bt, coh, {"subject_fold": sf}, np.random.default_rng(0),
                                          {"sigma_u": 1.0, "sigma_v": 1.0})
        finally:
            ev1.Reps = orig
        assert out["readout"]["n_test_candidates"] == n_pool and sorted(out["per_participant"]) == q
        rec = next(iter(out["per_participant"].values()))
        assert rec["unified/regular"]["n_candidates"] == n_pool and np.isfinite(rec["unified/regular"]["logloss_bits"])
        assert qa and "attention_2afc" in out and set(out["attention_2afc"]) == qa


def test_tick_batcher_rows_keys_and_tick_reps(fx, man):
    """§2.2 / §2.5 / §2.12: rows at ticks j = phi + 31 a with packed keys; the rolled rows carry the rolled audio's keys at the same
    ticks; patches / audio read the cache and the envelope; TickReps evaluates on TICK_OFFS."""
    coh = V.target_view("fau", 1, man, "A")
    cache = _npy(fx, "fau", "eeg_f16_tmajor.npy"); env = _npy(fx, "fau", "env_f32.npy")
    bt = V.TickBatcher(coh, SPEC, {"dataset": "fau", "subject_fold": 2, "content_fold": 1}, "cpu", man)
    assert bt.W == [(0, 38)] and bt.seg_len == 320 and bt.audio_dim == 8 and coh.eeg is None and coh.stim is None
    batch = next(bt.epoch_batches(np.random.default_rng(3), 32))
    assert len({coh.segments[i]["uid"] for i in batch}) == len(batch) >= 2
    e0, s0, keys = bt.rows(batch, np.random.default_rng(4))
    e0r, s0r, keysr = bt.rows(batch, np.random.default_rng(4), roll=True)
    phase = np.random.default_rng(4).integers(0, 31, size=len(batch))
    t = C.TICK_OFFS[phase[:, None] + 31 * np.arange(8)].reshape(-1)
    seg = [coh.segments[i] for i in batch]
    src = np.roll(np.arange(len(batch)), 1)
    assert torch.equal(e0, e0r) and np.array_equal(e0.numpy(), np.repeat([s["e0"] for s in seg], 8) + t)
    assert np.array_equal(s0.numpy(), np.repeat([s["s0"] for s in seg], 8) + t)
    for k_, order in ((keys, np.arange(len(batch))), (keysr, src)):
        ref = C.pack_key(np.repeat([seg[i]["family"] for i in order], 8), np.repeat([seg[i]["presentation"] for i in order], 8),
                         np.repeat([seg[i]["fs0"] for i in order], 8) + t)
        assert np.array_equal(k_.numpy(), ref)
    assert np.array_equal(s0r.numpy(), np.repeat([seg[i]["s0"] for i in src], 8) + t) and len(torch.unique(keys)) == len(keys)
    x = bt.patches(e0[:16])[0]
    assert x.shape == (16, 31, 38) and np.array_equal(x.numpy(), np.stack([np.asarray(cache[a:a + 38], np.float32).T for a in e0[:16].numpy()]))
    assert np.array_equal(bt.audio(s0[:16]).numpy(), np.stack([env[a:a + 8] for a in s0[:16].numpy()]))
    reps = V.TickReps(None, None, bt)
    assert np.array_equal(reps.offs, C.TICK_OFFS) and len(reps.offs) == 250 and reps.offs.max() == 319
    with pytest.raises(ValueError):
        V.TickReps(None, None, bt, stride=4)
    with pytest.raises(ValueError):
        bt.rows(batch, np.random.default_rng(0), anchors=4)
    for bad in ({"pairing": "declared_wrong_pair"}, {"training_task": "attended_alignment"}, {"architecture": "density_tokens"}):
        with pytest.raises(ValueError):
            V.TickBatcher(V.target_view("fau", 1, man, "A"), {**SPEC, **bad}, {"dataset": "fau", "subject_fold": 2, "content_fold": 1}, "cpu", man)
    with pytest.raises(ValueError, match="already"):
        V.TickBatcher(coh, SPEC, {"dataset": "fau", "subject_fold": 2, "content_fold": 1}, "cpu", man)


def test_target_view_segments_modes_and_scale(fx, man, tmp_path):
    """Segment fields and roles, the FAU competing-talker guard-only starts and the DTU onset rule (§2.2), one candidate per audio
    stream and start (DTU HI shares the original's), mode C = raw / donor scale, and §7.1 9: a target participant's variance moves
    the mode-A input but not the mode-C scale."""
    v = V.target_view("fau", 0, man, "A")
    t, items = _table(fx, "fau")
    for s in v.segments:
        it = items[s["piece"]]
        assert s["e0"] == it["row_offset"] + s["s"] and s["s"] % 32 == 0 and s["role"] in ("fit", "es", "test")
        assert s["code"] in v_content(man, "fau", 0)[s["kind"]][s["role"]] and s["hard_key"] == s["code"][1] and s["part"] == s["code"][2]
        assert len(s["feat"]) == 3 and np.isfinite(s["feat"]).all() and (s["s0_ign"] is None) == (s["kind"] == "ss")
    cs = [s for s in v.segments if s["kind"] == "cs"]
    assert cs and min(s["s"] for s in cs) == C.S_FIRST["fau"] < (fx["truth"]["fau_cs_onset_s"] + 1.7) * 64
    d = V.target_view("dtu", 0, man, "A")
    tcs = [s for s in d.segments if s["kind"] == "cs"]
    onsets = fx["truth"]["dtu_masker_onsets"]
    assert tcs and all(s["s"] >= (onsets[d.participants[s["p"]]["id"]] + 1.7) * 64 for s in tcs)
    hi = {i for i, q in enumerate(d.participants) if q["group"] == "hi"}
    hs = [s for s in d.segments if s["p"] in hi and s["kind"] == "ss"]
    nh_uids = {s["uid"] for s in d.segments if s["p"] not in hi}
    assert hs and all(s["uid"] in nh_uids or s["code"] == "t08" for s in hs)
    assert len({s["presentation"] for s in hs}) == len({(s["p"], s["code"]) for s in hs})        # HI presentations stay unique
    raw = _npy(fx, "dtu", "eeg_raw_f16_tmajor.npy")
    dc = V.target_view("dtu", 0, man, "C")
    sc = np.array([man["mode_c"]["dtu"]["scale"][n] for n in man["cohorts"]["dtu"]["layout"]], dtype=np.float32)
    assert np.allclose(dc.eeg[:, :5000].astype(np.float32), (np.asarray(raw[:5000], np.float32) / sc).T, rtol=2e-3, atol=1e-4)
    with pytest.raises(ValueError):
        V.target_view("sparrkulee", 0, man, "A")
    with pytest.raises(ValueError):
        V.target_view("fau", 2, man, "A")
    m2 = copy.deepcopy(dict(man)); m2["mode_c"]["dtu"]["supported"] = False
    with pytest.raises(ValueError, match="supported"):
        V.target_view("dtu", 0, V.Manifest(m2, None, None, man.root), "C")
    fxp = make_synthetic_manifest(tmp_path / "perturbed", perturb={("fau", "101"): 3.0})
    mp = V.open_manifest(fxp["manifest_path"], fxp["manifest_sha256"])
    assert mp["mode_c"]["fau"]["scale"] == man["mode_c"]["fau"]["scale"]
    a0, a1 = V.target_view("fau", 0, man, "A"), V.target_view("fau", 0, mp, "A")
    k = next(i for i, q in enumerate(a0.participants) if q["id"] == "101")
    cols = np.concatenate([np.arange(s["e0"], s["e0"] + 38) for s in a0.segments if s["p"] == k])
    assert not np.array_equal(a0.eeg[:, cols], a1.eeg[:, cols])
    other = np.concatenate([np.arange(s["e0"], s["e0"] + 38) for s in a0.segments if s["p"] != k][:2000])
    assert np.array_equal(a0.eeg[:, other], a1.eeg[:, other])
    assert a0.meta["pool_sha256"] == a1.meta["pool_sha256"]


def v_content(man, c, cf):
    return V.content_split(man, c, cf)


# ---------------------------------------------------------------------------------------------------------- fixed sets
def test_selection_sets_and_bridge_rows(fx4, man4, banks4):
    """§2.10 / §2.11: the fixed fit / dev / bridge_cal sets lie in their SparrKULee pools and roles (disjoint by participant and
    family); dev candidates are the unique (presentation, s) of the queries with own and other-content indices of the same listener;
    the bridge rows are the manifest's, with a deterministic montage only on 64-channel strata; all ticks gather from the bank."""
    m = man4
    ss = SM.selection_sets(m)
    S = m["segments"]["sparrkulee"]
    assert list(ss["fit"].rows) == m["selection"]["fit_segments"] and list(ss["dev"]["queries"].rows) == m["selection"]["dev_queries"]
    dq, dc, own, other = ss["dev"]["queries"], ss["dev"]["candidates"], ss["dev"]["own"], ss["dev"]["other"]
    ckeys = list(zip(dc.presentation, dc.s))
    assert len(set(ckeys)) == len(ckeys) and all(ckeys[o] == (p, s) for o, p, s in zip(own, dq.presentation, dq.s))
    for i, o in enumerate(other):
        assert o >= 0 and o != own[i]
        j = [k for k in range(len(dq)) if own[k] == o and dq.participant[k] == dq.participant[i]]
        assert j                                            # the other content is another dev segment of the same listener
    cal = ss["bridge_cal"]
    assert list(cal["queries"].rows) == m["bridge"]["cal_queries"] and set(cal["fold"]) == {0, 1}
    assert {(int(p), int(s)) for p, s in zip(cal["candidates"].presentation, cal["candidates"].s)} == \
        {(S["presentation"][r], S["s"][r]) for r in m["pools"]["bridge_cal"]["sparrkulee"]}
    k = ss["fit"].keys()
    assert k.shape == (len(ss["fit"]), 250) and (np.diff(C.unpack_key(k)[2], axis=1) > 0).all()
    for target in ("fau", "dtu", "federici", "private_bdf"):
        br, br2 = SM.bridge_rows(m, target), SM.bridge_rows(m, target)
        assert br["order"] == br2["order"] and [(s, r) for s, r, _ in br["order"]] == [tuple(x) for x in m["bridge"]["fit_rows"][target]]
        for stratum, segs in br["fit"].items():
            assert stratum in m["donor_sets"][target]["core"]["strata"] and stratum != "fau_cs"
            assert all(x is None for x in segs.montage) or SM.coh_of(stratum) in ("sparrkulee", "dtu")
            assert set(segs.montage) - {None} <= set(SM.AUG_NAMES)
    b = banks4["sparrkulee"]
    q = dq.take([0, 1])
    x, y = b.all_ticks(q.piece, q.s, q.presentation)
    assert x.shape == (500, 64, 38) and y.shape == (500, 8) and torch.isfinite(x.float()).all()


# ---------------------------------------------------------------------------------------------------------- private input
def test_private_input_at_64hz(monkeypatch):
    """§2.1 / §2.12 private path: load_private64 adds x64 [n, 20, 90] (LP20, per-child z over [32, 70)); PrivateBatcher64 serves
    window [32, 70) of x64 at 64 Hz (never the 250 Hz epochs), with the base batcher's folds, early-stopping blocks and labels."""
    from auditory_alignment import data
    kids = synthetic_kids()
    calls = []
    monkeypatch.setattr(data, "load_private", lambda: calls.append(1) or kids)
    out = V.load_private64()
    assert calls == [1] and out is kids
    for k in kids:
        x64 = k["x64"]
        assert x64.shape == (len(k["y"]), 20, 90) and x64.dtype == np.float32 and np.isfinite(x64).all()
        w = x64[:, :, 32:70].astype(np.float64)
        assert np.allclose(w.mean(axis=(0, 2)), 0, atol=1e-5) and np.allclose(w.std(axis=(0, 2)), 1, atol=1e-4)
        assert np.allclose(x64, C.z64_per_child(C.private_to64(k["x"])))
    row = {"subject_fold": 2, "seed": 3401}
    bt = V.PrivateBatcher64(kids, {"architecture": "lag_local_tokens", "window": "full", "objective": "NCE"}, row, "cpu")
    assert bt.W == [(0, 38)] and (bt.lo, bt.hi) == (32, 70) and bt.Xall.shape == (sum(len(k["y"]) for k in kids), 20, 38)
    assert bt.train == [i for i, k in enumerate(kids) if k["fold"] != 2] and bt.input == V.PRIVATE_INPUT
    xb, yb = bt.batch(np.random.default_rng(0), per=4)
    assert len(xb) == 1 and xb[0].shape == (4 * len(bt.train), 20, 38) and xb[0].dtype == torch.float32 and yb.shape == (4 * len(bt.train),)
    i = bt.train[0]
    idx = torch.arange(len(kids[i]["y"]))
    p = bt.patches(i, idx)[0]
    assert np.array_equal(p.numpy(), kids[i]["x64"][:, :, 32:70].astype(np.float16).astype(np.float32))
    for j in bt.train:
        assert np.array_equal(bt.fit_idx[j], bt.off[j] + np.flatnonzero(~kids[j]["es_mask"]))
    before = bt.patches(i, idx)[0].clone()
    for k in kids:
        k["x"] = k["x"] * 0 + 7.0                                  # the 250 Hz epochs are not read after load_private64
    assert torch.equal(bt.patches(i, idx)[0], before)
    with pytest.raises(ValueError, match="x64"):
        V.PrivateBatcher64([{**kids[0], "x64": None}], {}, row, "cpu")
    with pytest.raises(ValueError):
        V.load_private64([{"id": "c", "x": np.zeros((3, 20, 250), np.float32), "y": np.zeros(3)}])


# ---------------------------------------------------------------------------------------------------------- interfaces
def test_batches_feed_the_m4_model_and_losses(man4, banks4):
    """Interface check with M4 (model.py, losses.py, rich.py): rich-block batches of every stratum drive the AP / XP / XM NCE terms,
    both CS terms and the normalised rich loss through the shared encoder (per-call layout and channel mask) and the fixed heads,
    with finite values and gradients; XP has a positive for every query."""
    from auditory_alignment_v3.prior33 import losses as L
    from auditory_alignment_v3.prior33 import rich as R
    from auditory_alignment_v3.prior33.model import build_shared, fixed_heads
    heads, uc = fixed_heads(man4, man4.root), L.unknown_clock_families(man4)
    smp = _sampler(man4, banks4, "fau", "rich", seed=8)
    enc = build_shared(C.MONTAGES["sparrkulee"], man4["seen"]["fau"], 3401, rich=True)
    for stratum, b in smp.calibration_batches().items():
        enc.zero_grad()
        u1, u2 = enc(b.x1, layout=b.layout, mask=b.chan_mask[0]), enc(b.x2, layout=b.layout, mask=b.chan_mask[1])
        v = heads["env"](b.y)
        l_ap, s_ap = L.nce_audio_pair(u1, u2, v, b.keys, unknown_clock=uc)
        l_xp, s_xp = L.nce_cross_person(u1, u2, b.keys, b.part1, b.part2, unknown_clock=uc)
        perm, _ = smp.derangement(b)
        xm = smp.xm_view(b, perm)
        l_xm, _ = L.nce_cross_person(u1, enc(xm.x2, layout=b.layout, mask=xm.chan_mask2), xm.keys, b.part1, xm.part2, unknown_clock=uc)
        l_cs, _ = L.cs_audio_pair(u1, u2, v, 1.0, 1.0)
        l_csx, _ = L.cs_cross_person(u1, u2, 1.0)
        uh = R.eeg_heads(enc, b.x1, b.x2, b.layout)
        vh = {"env": v, "ss": heads["ss"](b.rich["ss"]), "sc": heads["sc"](b.rich["sc"])}
        l_r, s_r = R.rich_loss(uh, vh, {"env": True, "ss": b.rich_mask, "sc": b.rich_mask}, "NCE", keys=b.keys, unknown_clock=uc)
        total = l_ap + l_xp + l_xm + l_cs + l_csx + l_r
        total.backward()
        assert torch.isfinite(total) and s_xp["nopos_12"] == s_xp["nopos_21"] == 0 and s_ap["nopos_e2a"] == 0
        assert all(p.grad is None or torch.isfinite(p.grad).all() for p in enc.parameters())
        assert s_r["rows_ss"] == int(b.rich_mask.sum()) and (stratum != "federici" or s_r["rows_ss"] == 0)


def test_cohort_local_table_ids(fx, man, tmp_path):
    """Builder tables in the cohort-local id space (id_space cohort_local_provisional, C1 / C4 / C5): the views map pieces by
    presentation_key to the manifest's keyed presentations (pools unchanged), refuse when no mapping exists (IdSpaceError), and
    refuse a mapping that disagrees with the manifest segment table; DonorBank records whether it could cross-check."""
    root = tmp_path / "local"
    for c in ("fau", "dtu"):
        src, dst = os.path.join(fx["root"], man["cohorts"][c]["dir"]), root / man["cohorts"][c]["dir"]
        dst.mkdir(parents=True)
        for f in os.listdir(src):
            (os.symlink if f.endswith(".npy") else shutil.copy)(os.path.join(src, f), dst / f)
    for c in ("fau", "dtu"):
        p = root / man["cohorts"][c]["dir"] / man["cohorts"][c]["table"]
        t = json.loads(p.read_text())
        t["id_space"] = "cohort_local_provisional"
        for it in t["pieces"]:
            it["presentation_key"] = f"key:{it['presentation']}"
            it["presentation"] = 900 + it["presentation"]             # a provisional id that the views must not use
        os.chmod(p, 0o644); p.write_text(json.dumps(t))
    with pytest.raises(V.IdSpaceError):
        V.target_view("fau", 0, V.Manifest(dict(man), None, None, str(root)), "A")
    keyed = copy.deepcopy(dict(man))
    for q in keyed["presentations"]:
        q["key"] = f"key:{q['id']}"
    ref = V.target_view("fau", 0, man, "A")
    got = V.target_view("fau", 0, V.Manifest(keyed, None, None, str(root)), "A")
    assert got.meta["pool_sha256"] == ref.meta["pool_sha256"] and V.pool_of(got, "test", "ss")[0] == V.pool_of(ref, "test", "ss")[0]
    swapped = copy.deepcopy(keyed)
    fau = [q for q in swapped["presentations"] if q["cohort"] == "fau"]
    fau[0]["key"], fau[1]["key"] = fau[1]["key"], fau[0]["key"]
    with pytest.raises(ValueError, match="manifest segment table"):
        V.target_view("fau", 0, V.Manifest(swapped, None, None, str(root)), "A")
    with pytest.raises(ValueError, match="manifest segment table"):
        V.DonorBank(V.Manifest(swapped, None, None, str(root)), "fau", ("fit",), "cpu")
    with pytest.raises(V.IdSpaceError):                 # a donor bank that cannot map its table refuses too (no "not checked")
        V.DonorBank(V.Manifest(dict(man), None, None, str(root)), "dtu", ("fit",), "cpu")
    b = V.DonorBank(V.Manifest(keyed, None, None, str(root)), "dtu", ("fit",), "cpu")
    assert b.presentation_check == "checked" == V.DonorBank(man, "dtu", ("fit",), "cpu").presentation_check
    assert b.n_pieces_checked == sum(it["row_offset"] is not None for it in _table(fx, "dtu")[1])


# ---------------------------------------------------------------------------------------------------------- M3 review cases
def _xm_structure_batches(rng, n_part, hear, n_seg_of, nb):
    """Batches drawn by the sampler's rule (uniform participant, uniform segment, distinct (content, segment), uniform partner
    among the content's other listeners) on a synthetic table of the real sizes -> int64 [32, 3] (family, listener, partner)."""
    listeners = {}
    for p, cs in enumerate(hear):
        for c in cs:
            listeners.setdefault(c, []).append(p)
    out = []
    for _ in range(nb):
        used, rows = set(), []
        while len(rows) < 32:
            p = int(rng.integers(n_part))
            c = hear[p][int(rng.integers(len(hear[p])))]
            s = int(rng.integers(n_seg_of[c]))
            if (c, s) in used or len(listeners[c]) < 2:
                continue
            used.add((c, s))
            q = p
            while q == p:
                q = listeners[c][int(rng.integers(len(listeners[c])))]
            rows.append((c, p, q))
        out.append(np.array(rows, dtype=np.int64))
    return out


def test_xm_meets_the_hard_constraints_whenever_possible_on_realistic_strata(man4, banks4):
    """M3 review (MED): with the real family structure (FAU 8 single-talker families x 81 listeners, fau_cs 12 x 81, a
    SparrKULee-like fit role of 64 listeners on 49 presentations) the literal 100 random derangements missed an existing
    permutation in about 37 / 3 / 2 % of batches. With the assignment fallback the kept pi meets both hard constraints on every
    feasible batch (against the exact minimum), never has a fixed point, reaches the minimum on infeasible ones, and
    stats['feasible'] is exact."""
    smp = _sampler(man4, banks4, "fau", "core", seed=4)
    pres0 = [i for i, p in enumerate(man4["presentations"]) if p["cohort"] == "sparrkulee"][0]
    rng = np.random.default_rng(20261017)
    sk_hear = [[0] for _ in range(64)]
    for c in range(1, 49):
        for p in rng.choice(64, size=8, replace=False):
            sk_hear[p].append(c)
    structures = {"fau": (81, [list(range(8))] * 81, [26] * 8, 300), "fau_cs": (81, [list(range(12))] * 81, [26] * 12, 100),
                  "sparrkulee": (64, sk_hear, [180] + [160] * 48, 100), "two_families": (81, [[0, 1]] * 81, [3, 40], 40)}
    for name, (n_part, hear, n_seg_of, nb) in structures.items():
        used = {"random_draw": 0, "assignment": 0}
        n_infeasible = 0
        for rows in _xm_structure_batches(rng, n_part, hear, n_seg_of, nb):
            fam, lis, par = rows[:, 0], rows[:, 1] + 1000, rows[:, 2] + 1000
            perm, st = smp.derangement(_fake_batch(fam, lis, par, [pres0] * 32))
            vmin = _min_violations(fam, lis, par)
            assert sorted(perm) == list(range(32)) and not (perm == np.arange(32)).any() and st["fixed_points"] == 0
            assert st["violations"] == int((fam[perm] == fam).sum() + (par[perm] == lis).sum()) == vmin, (name, st, vmin)
            assert st["feasible"] == st["constraints_met"] == (vmin == 0)
            used[st["method"]] += 1
            n_infeasible += vmin > 0
        assert name != "fau" or used["assignment"] > 0.1 * nb, (name, used)          # the fallback path is exercised
        assert name != "two_families" or n_infeasible == nb                          # 3 + 40 segments: always infeasible


def test_xm_partner_constraint_is_twin_aware(man4, banks4):
    """HC N and HC-v N (manifest partner_exclusions) count as one listener for the XM partner constraint, as §2.5 does for partner
    sampling, so XM's view 2 never pairs them either; other Federici listeners are unaffected."""
    smp = _sampler(man4, banks4, "fau", "core", seed=4)
    pid = smp.banks["federici"].pid
    (_, a, b), = [t for t in man4["partner_exclusions"] if t[1] == "HC:1001"]
    pres = [i for i, p in enumerate(man4["presentations"]) if p["cohort"] == "federici"][:2]
    twin = _fake_batch([0, 1], [pid[a], pid["CI:0002"]], [pid["CI:0001"], pid[b]], pres)   # pi = (1, 0): view 2 of seg 0 is HC-v 1001
    perm, st = smp.derangement(twin)
    assert list(perm) == [1, 0] and st["violations_partner"] == 1 and not st["feasible"] and st["method"] == "assignment"
    plain = _fake_batch([0, 1], [pid["HC:1003"], pid["CI:0002"]], [pid["CI:0001"], pid["HC:1004"]], pres)
    assert smp.derangement(plain)[1]["violations"] == 0


def test_xm_condition_key_uses_the_acoustic_condition(man4, banks4):
    """M3 review (LOW): SparrKULee presentations share the task state 'listeningActive'; the XM same-condition preference still
    tells the noise condition and SNR apart when the manifest carries them (views.condition_key; numbers compare as floats; the
    stimulus-specific noise file is not a condition)."""
    idx = V.manifest_index(man4)
    assert len(set(idx.cond.tolist())) == len({p["condition"] for p in man4["presentations"]})    # fixture: the strings only
    m2 = copy.deepcopy(dict(man4))
    sk = [p for p in m2["presentations"] if p["cohort"] == "sparrkulee"]
    for k, p in enumerate(sk):
        p.update(noise_condition="in_noise" if k % 2 else "no_noise", snr=100 if k % 2 else None, noise_file="n.wav" if k % 2 else None)
    sk[1]["snr"] = 100.0
    i2 = V.manifest_index(V.Manifest(m2, None, None, man4.root))
    ids = [p["id"] for p in sk]
    assert len({int(i2.cond[i]) for i in ids}) == 2 and i2.cond[ids[1]] == i2.cond[ids[3]] != i2.cond[ids[0]]
    assert V.condition_key({"condition": "c", "snr": 100}) == V.condition_key({"condition": "c", "snr": 100.0})
    assert V.condition_key({"condition": "c", "noise_file": "noise_a.npz.gz"}) == V.condition_key({"condition": "c", "noise_file": "b"})
    assert V.condition_key({"condition": "c", "snr": -4}) != V.condition_key({"condition": "c", "snr": 100})
    smp = _sampler(man4, banks4, "fau", "core", seed=6)
    pres = [ids[k % 2] for k in range(32)]
    fake = _fake_batch(np.arange(32), np.arange(32), np.arange(32) + 100, pres)
    assert smp.derangement(fake)[1]["same_condition"] == 32                  # one condition class in the fixture
    smp.idx = i2                                                             # the manifest with acoustic conditions
    perm, st = smp.derangement(fake)
    c = i2.cond[np.asarray(pres)]
    assert st["same_condition"] == int((c[perm] == c).sum()) and st["same_condition_fraction"] == st["same_condition"] / 32


def test_fixed_sets_refuse_presentations_excluded_for_any_target(man4):
    """M3 review (LOW-MED): one fit / dev / bridge_cal definition serves every donor set (§3.2), and target-overlapping content
    leaves donor development and calibration too (§3.4.1, inherited contract §2), so no shared SparrKULee set may hold a
    presentation that any donor set excludes. The fixture has none; tampered copies plant one per set and selection_sets and
    bridge_rows raise (fail closed)."""
    ss = SM.selection_sets(man4)
    assert ss["excluded_presentations_checked"] == len(SM.excluded_anywhere(man4)) == 0
    S = man4["segments"]["sparrkulee"]
    cal = man4["pools"]["bridge_cal"]["sparrkulee"]
    cal_pres = sorted({S["presentation"][r] for r in cal})
    assert len(cal_pres) >= 2
    cases = (("fau", "core", S["presentation"][man4["selection"]["fit_segments"][0]], None, "selection.fit_segments", "dtu"),
             ("dtu", "rich", S["presentation"][man4["selection"]["dev_queries"][0]], None, "selection.dev_queries", "fau"),
             ("federici", "csx", S["presentation"][man4["bridge"]["cal_queries"][0]], None, "bridge.cal_queries", "fau"),
             ("private_bdf", "core", cal_pres[1], [r for r in cal if S["presentation"][r] == cal_pres[0]], "pools.bridge_cal", "dtu"))
    for target, block, pres, queries, where, other in cases:
        m2 = copy.deepcopy(dict(man4))
        m2["donor_sets"][target][block]["excluded_presentations"]["sparrkulee"] = [int(pres)]
        if queries is not None:                       # the queries avoid the presentation; the candidate pool still holds it
            m2["bridge"]["cal_queries"] = queries
        m2 = V.Manifest(m2, None, None, man4.root)
        with pytest.raises(ValueError, match="excluded") as e:
            SM.selection_sets(m2)
        assert where in str(e.value) and f"{target}/{block}" in str(e.value), str(e.value)
        with pytest.raises(ValueError, match="excluded"):
            SM.bridge_rows(m2, other)


def test_table_streams_must_match_the_manifest(fx, man, tmp_path):
    """M3 review (LOW-MED): the manifest presentation decides every envelope window and the table's piece the EEG rows; a stream,
    ignored stream or lead that differs between them is refused by DonorBank and target_view (before, two swapped FAU streams
    were accepted and silently paired EEG with another code's envelope), and a SparrKULee table that cannot be mapped to the
    manifest ids is refused by the bank."""
    P = man["presentations"]
    a, b = [p["id"] for p in P if p["cohort"] == "fau" and p["kind"] == "ss"][:2]
    m2 = copy.deepcopy(dict(man))
    m2["presentations"][a]["stream"], m2["presentations"][b]["stream"] = P[b]["stream"], P[a]["stream"]
    m2 = V.Manifest(m2, None, None, man.root)
    with pytest.raises(ValueError, match="stream"):
        V.DonorBank(m2, "fau", ("fit",), "cpu")
    with pytest.raises(ValueError, match="stream"):
        V.target_view("fau", 0, m2, "A")
    cs = next(p["id"] for p in P if p["cohort"] == "fau" and p["kind"] == "cs")
    for field, value in (("ignored_stream", None), ("ignored_lead", 64)):
        m3 = copy.deepcopy(dict(man))
        m3["presentations"][cs][field] = value
        with pytest.raises(ValueError, match="ignored"):
            V.target_view("fau", 0, V.Manifest(m3, None, None, man.root), "A")
    t, items = _table(fx, "fau")
    idx, streams = V.manifest_index(man), _streams(fx, "fau")
    pres_of = V.piece_presentations(man, "fau", t, items)
    assert V.check_piece_streams("fau", items, pres_of, idx, streams) == sum(it["row_offset"] is not None for it in items)
    i = next(k for k, it in enumerate(items) if it["row_offset"] is not None)
    for field, value, msg in (("T_env", items[i]["T_env"] + 1, "T_env"), ("stream", None, "stream"), ("kind", "cs", "kind")):
        bad = copy.deepcopy(items)
        bad[i][field] = value
        with pytest.raises(ValueError, match=msg):
            V.check_piece_streams("fau", bad, pres_of, idx, streams)
    with pytest.raises(V.IdSpaceError):
        V.check_piece_streams("fau", items, pres_of[:i] + [None] + pres_of[i + 1:], idx, streams)
    root = tmp_path / "sk"                                 # SparrKULee table in the builders' provisional id space
    src, dst = os.path.join(fx["root"], man["cohorts"]["sparrkulee"]["dir"]), root / man["cohorts"]["sparrkulee"]["dir"]
    dst.mkdir(parents=True)
    for f in os.listdir(src):
        (os.symlink if f.endswith(".npy") else shutil.copy)(os.path.join(src, f), dst / f)
    p = dst / man["cohorts"]["sparrkulee"]["table"]
    tab = json.loads(p.read_text())
    tab["id_space"] = "cohort_local_provisional"
    for it in tab["runs"]:
        it["presentation_key"] = None if it["presentation"] is None else f"key:{it['presentation']}"
        it["presentation"] = None if it["presentation"] is None else 900 + it["presentation"]
    os.chmod(p, 0o644); p.write_text(json.dumps(tab))
    with pytest.raises(V.IdSpaceError):
        V.DonorBank(V.Manifest(dict(man), None, None, str(root)), "sparrkulee", ("fit",), "cpu")
    keyed = copy.deepcopy(dict(man))
    for q in keyed["presentations"]:
        q["key"] = f"key:{q['id']}"
    assert V.DonorBank(V.Manifest(keyed, None, None, str(root)), "sparrkulee", ("fit",), "cpu").presentation_check == "checked"


def test_bank_modes_memory_and_chunked_gather(fx4, man4, banks4, monkeypatch):
    """M3 review (LOW, resource): mode 'pieces' (no FAU competing-talker trial in a core bank) and mode 'segments' (the fixed
    validation / bridge sets: 357 rows per segment) hold fewer rows but gather exactly the slab bank's windows; the chunked gather
    equals the one-shot gather across chunk edges; iter_ticks concatenates to all_ticks; the cache is copied through writable
    arrays (no torch non-writable-array warning)."""
    real = torch.from_numpy

    def strict(a):
        assert a.flags.writeable, "torch.from_numpy on a read-only array"
        return real(a)
    monkeypatch.setattr(torch, "from_numpy", strict)
    S, items = V.manifest_index(man4).seg["fau"], _table(fx4, "fau")[1]
    full = banks4["fau"]
    ss = sorted({int(S["piece"][r]) for r in man4["pools"]["core"]["fau"]})
    cs = [i for i, it in enumerate(items) if it["kind"] == "cs"]
    pb = V.DonorBank(man4, "fau", ("fit",), "cpu", pieces={"fit": ss})
    assert pb.mode == "pieces" and not pb.loaded(cs).any() and pb.loaded(ss).all() and pb.nbytes < full.nbytes
    assert pb.describe()["n_pieces"] == len(ss) and pb.describe()["mode"] == "pieces"
    rows = np.asarray(man4["pools"]["core"]["fau"])[:40]
    a = full.all_ticks(S["piece"][rows], S["s"][rows], S["presentation"][rows])
    b = pb.all_ticks(S["piece"][rows], S["s"][rows], S["presentation"][rows])
    assert torch.equal(a[0], b[0]) and torch.equal(a[1], b[1])
    with pytest.raises(ValueError, match="loaded"):
        pb.gather([cs[0]], [items[cs[0]]["segment_starts"][0]], [0])
    with pytest.raises(ValueError, match="not cached pieces"):
        V.DonorBank(man4, "fau", ("fit",), "cpu", pieces=[10 ** 6])
    sel = SM.selection_sets(man4)
    Sk = V.manifest_index(man4).seg["sparrkulee"]
    seg_rows = np.r_[sel["fit"].rows, sel["dev"]["queries"].rows]
    sb = V.DonorBank(man4, "sparrkulee", ("fit", "dev"), "cpu", segments=seg_rows)
    n_u = len({(Sk["piece"][r], Sk["s"][r]) for r in seg_rows})
    assert sb.mode == "segments" and sb.n_rows == n_u * C.SPAN_EEG and tuple(sb.E.shape) == (n_u * C.SPAN_EEG, 64)
    assert sb.describe()["n_segments"] == n_u and sb.nbytes < banks4["sparrkulee"].nbytes
    sk_full = banks4["sparrkulee"]
    q = np.r_[sel["fit"].rows[:3], sel["dev"]["queries"].rows[:3]]
    x1, y1 = sk_full.all_ticks(Sk["piece"][q], Sk["s"][q], Sk["presentation"][q])
    x2, y2 = sb.all_ticks(Sk["piece"][q], Sk["s"][q], Sk["presentation"][q])
    assert torch.equal(x1, x2) and torch.equal(y1, y2)
    loaded = {(Sk["piece"][r], Sk["s"][r]) for r in seg_rows}
    other = next(r for r in man4["pools"]["core"]["sparrkulee"] if (Sk["piece"][r], Sk["s"][r]) not in loaded)
    with pytest.raises(ValueError, match="not loaded"):
        sb.gather([Sk["piece"][other]], [Sk["s"][other]], [0])
    q0 = next(r for r in seg_rows if Sk["s"][r] > C.S_FIRST["sparrkulee"])
    with pytest.raises(ValueError, match="span"):
        sb.gather([Sk["piece"][q0]], [Sk["s"][q0]], [-1])
    with pytest.raises(ValueError, match="outside the slabs"):
        V.DonorBank(man4, "sparrkulee", ("fit",), "cpu", segments=sel["dev"]["queries"].rows)
    with pytest.raises(ValueError, match="not both"):
        V.DonorBank(man4, "sparrkulee", ("fit",), "cpu", pieces=[0], segments=[0])
    monkeypatch.setattr(V, "GATHER_CHUNK", 7)                 # chunk edges inside the 1,500 windows
    x3, _ = sk_full.all_ticks(Sk["piece"][q], Sk["s"][q], Sk["presentation"][q])
    assert torch.equal(x1, x3)
    parts = list(sk_full.iter_ticks(Sk["piece"][q], Sk["s"][q], Sk["presentation"][q], chunk=4))
    assert [(i0, i1) for i0, i1, _, _ in parts] == [(0, 4), (4, 6)]
    assert torch.equal(torch.cat([x for _, _, x, _ in parts]), x1) and torch.equal(torch.cat([y for _, _, _, y in parts]), y1)


def test_sampler_own_banks_hold_only_drawable_pieces(man4, banks4):
    """The sampler's own banks hold the fit pieces of its eligible rows only (a core group: no FAU competing-talker trial; CSX:
    with them); its batches and stream equal those drawn from whole-slab banks; a 'segments' bank is refused for training."""
    own = SM.DonorSampler(man4, "dtu", "core", 3401, "cpu")
    ref = _sampler(man4, banks4, "dtu", "core")
    fb = own.banks["fau"]
    cs = [i for i, it in enumerate(fb.items) if it["kind"] == "cs"]
    assert fb.mode == "pieces" and not fb.loaded(cs).any() and fb.nbytes < banks4["fau"].nbytes
    for _ in range(25):
        assert _same_batch(own.next_batch(), ref.next_batch())
    assert own.stream_hash() == ref.stream_hash()
    csx = SM.DonorSampler(man4, "dtu", "csx", 3401, "cpu")
    assert csx.banks["fau"].loaded(sorted({int(p) for p in np.asarray(man4["segments"]["fau"]["piece"])[man4["pools"]["csx"]["fau_cs"]]})).all()
    seg_bank = V.DonorBank(man4, "fau", ("fit",), "cpu", segments=man4["pools"]["core"]["fau"][:40])
    with pytest.raises(ValueError, match="segments"):
        SM.DonorSampler(man4, "dtu", "core", 3401, "cpu", banks={**banks4, "fau": seg_bank})
    d = own.describe()
    assert d["banks"]["fau"]["mode"] == "pieces" and d["xm"]["rule"] == SM.XM_RULE and d["xm"]["twin_aware_partner"]


def test_csx_donor_set_keeps_the_core_pools(man):
    """M3 review (LOW): the CSX donor set's core strata must keep the core's n_segments and excluded presentations (§2.16)."""
    for edit in (lambda d: d["dtu"]["csx"]["excluded_presentations"].__setitem__("sparrkulee", [0]),
                 lambda d: d["dtu"]["csx"]["n_segments"].__setitem__(0, d["dtu"]["csx"]["n_segments"][0] - 1)):
        m2 = V.Manifest(copy.deepcopy(dict(man)), man.path, None, man.root)
        edit(m2["donor_sets"])
        with pytest.raises(ValueError, match="CSX"):
            SM.DonorSampler(m2, "dtu", "csx", 1, "cpu")


def test_zero_shot_through_ev1_reads_only_the_outer_test(fx, man):
    """M3 review (test gap): ev1.evaluate_continuous with a zero-shot batcher (train_p = set()), a frozen stand-in readout (no fit;
    calibrate raises), ev1._ridge raising and TickReps reproduces the adapted row's candidate pool, query participants, per-
    participant query counts and attention set, with finite metrics; every EEG row it reads is test content of a test participant
    (or test_only session), and every audio row belongs to a test segment's attended or ignored stream window."""
    from auditory_alignment import evaluate as ev1
    from auditory_alignment_v3.prior33.model import build_shared, fixed_heads
    head = fixed_heads(man, man.root)["env"]

    class Frozen(ev1.Readouts):
        def __init__(self, objective, reps, train_segs, rng, **kw):
            if train_segs:
                raise AssertionError(f"a zero-shot readout received {len(train_segs)} target training segments")
            g = np.random.default_rng(1)
            self.objective, self.alpha_uni, self.alpha_nat = objective, 1.0, 1.0
            self.B_uni, self.B_nat = g.standard_normal((33, C.N_TGT)), g.standard_normal((33, 32))
            self.a_mu, self.a_sd, self.tau = np.zeros(C.N_TGT), np.ones(C.N_TGT), {"unified": 0.05, "native": 0.05}

        def calibrate(self, S, own):
            raise AssertionError("calibrate in a zero-shot evaluation")

    def ridge(*a, **k):
        raise AssertionError("ev1._ridge in a zero-shot evaluation")

    for c, sf, cf, modes in (("fau", 1, 0, ("A", "C")), ("dtu", 0, 1, ("C",)), ("federici", 2, 0, ("C_partial",))):
        cell = V.manifest_cell(man, c, sf, cf)
        row = {"dataset": c, "subject_fold": sf, "content_fold": cf}
        enc = build_shared(C.MONTAGES[c], C.MONTAGES[c], 3401).eval()
        coh = V.target_view(c, cf, man, "A")
        bt = V.TickBatcher(coh, SPEC, row, "cpu", man)
        orig = (ev1.Reps, ev1.Readouts, ev1._ridge)
        ev1.Reps = V.TickReps
        try:
            ad = ev1.evaluate_continuous("NCE", enc, head, bt, coh, {"subject_fold": sf}, np.random.default_rng(7), {"sigma_u": 1.0, "sigma_v": 1.0})
        finally:
            ev1.Reps = orig[0]
        items = _table(fx, c)[1]
        test_ids, content = set(cell["test"]) | set(cell["test_only"]), cell["content"]
        for m in modes:
            v = V.target_view(c, cf, man, m)
            zb = V.TickBatcher(v, SPEC, row, "cpu", man, train_p=set())
            allowed_a = {int(s[k]) + int(o) for s in v.segments if s["role"] == "test" for k in ("s0", "s0_ign")
                         if s.get(k) is not None for o in C.TICK_OFFS}
            seen_e, seen_a = [], []
            pe, pa = zb.patches, zb.audio
            zb.patches = lambda e, f=pe: (seen_e.append(e.cpu().numpy().copy()), f(e))[1]
            zb.audio = lambda s, f=pa: (seen_a.append(s.cpu().numpy().copy()), f(s))[1]
            ev1.Reps, ev1.Readouts, ev1._ridge = V.TickReps, Frozen, ridge
            try:
                zo = ev1.evaluate_continuous("NCE", enc, head, zb, v, {"subject_fold": sf}, np.random.default_rng(7), {"sigma_u": 1.0, "sigma_v": 1.0})
            finally:
                ev1.Reps, ev1.Readouts, ev1._ridge = orig
            assert zo["readout"]["n_test_candidates"] == ad["readout"]["n_test_candidates"] == len(V.pool_of(v, "test", "ss")[1])
            assert sorted(zo["per_participant"]) == sorted(ad["per_participant"]) and set(zo["per_participant"]) <= test_ids
            for p, r in zo["per_participant"].items():
                assert r["unified/regular"]["n_queries"] == ad["per_participant"][p]["unified/regular"]["n_queries"]
                assert np.isfinite(r["unified/regular"]["logloss_bits"]) and np.isfinite(r["native/regular"]["logloss_bits"])
            assert set(zo.get("attention_2afc", {})) == set(ad.get("attention_2afc", {})) and (c == "federici" or zo["attention_2afc"])
            for i in np.unique(_rows_to_pieces(items, np.concatenate(seen_e), C.GUARDS[c])):
                it = items[i]
                lists = content[it["kind"]] if c == "fau" else content
                assert it["participant"] in test_ids and it["stimulus"] in lists["test"], (c, m, it["piece_id"])
            assert set(np.concatenate(seen_a).tolist()) <= allowed_a, (c, m)


def test_target_training_reads_only_training_rows(fx, man):
    """M3 review (test gap): the A_LOCAL access pattern of fit_continuous (the calibration batch, 40 early-stopping batches true and
    rolled, epochs over the fit set) reads EEG only from the cell's training participants' fit / es single-talker pieces inside the
    guards, and audio only from fit / es single-talker streams inside the edges: the rows actually read, not only bt.fit / bt.es."""
    for cell in man["cells"]:
        ds, sf, cf = cell["dataset"], cell["subject_fold"], cell["content_fold"]
        if ds == "private_bdf":
            continue
        items, streams = _table(fx, ds)[1], _streams(fx, ds)
        coh = V.target_view(ds, cf, man, "A")
        bt = V.TickBatcher(coh, SPEC, {"dataset": ds, "subject_fold": sf, "content_fold": cf, "seed": 3401}, "cpu", man)
        rows_e, rows_s = [], []

        def take(r):
            rows_e.append(r[0].numpy()); rows_s.append(r[1].numpy())
        take(bt.rows(next(bt.epoch_batches(np.random.default_rng(3401 + 99), 32)), np.random.default_rng(3401 + 98)))
        es_rng, es_sel = np.random.default_rng(12345), []
        while len(es_sel) < 40:
            got = [b for b, _ in zip(bt.epoch_batches(es_rng, 32, bt.es), range(40 - len(es_sel)))]
            if not got:
                break
            es_sel += got
        for k, b in enumerate(es_sel):
            take(bt.rows(b, np.random.default_rng(k))); take(bt.rows(b, np.random.default_rng(k), roll=True))
        rng = np.random.default_rng(3401)
        for _ in range(2):
            for b in bt.epoch_batches(rng, 32):
                take(bt.rows(b, rng))
        lists = cell["content"]["ss"] if ds == "fau" else cell["content"]
        train = set(cell["train"])
        for i in np.unique(_rows_to_pieces(items, np.concatenate(rows_e), C.GUARDS[ds])):
            it = items[i]
            assert it["participant"] in train and it["kind"] == "ss" and it["stimulus"] in set(lists["fit"]) | set(lists["es"]), \
                (ds, sf, cf, it["piece_id"])
        for st in np.unique(_audio_to_streams(streams, np.concatenate(rows_s))):
            stims = {p["stimulus"].split("@")[0] for p in man["presentations"] if p["cohort"] == ds and p["stream"] == st and p["kind"] == "ss"}
            assert stims and stims <= set(lists["fit"]) | set(lists["es"]), (ds, sf, cf, st, stims)


# ---------------------------------------------------------------------------------------------------------- M3 review, round 2
def _cohort_copy(fx, man, root, cohort):
    """A copy of one cohort directory under `root`: the JSON tables / stream lists copied (editable), the .npy caches symlinked."""
    src, dst = os.path.join(fx["root"], man["cohorts"][cohort]["dir"]), root / man["cohorts"][cohort]["dir"]
    dst.mkdir(parents=True)
    for f in os.listdir(src):
        (os.symlink if f.endswith(".npy") else shutil.copy)(os.path.join(src, f), dst / f)
    p = dst / man["cohorts"][cohort]["table"]
    os.chmod(p, 0o644)
    return p


def test_piece_side_and_condition_must_match_the_manifest(fx, man, tmp_path):
    """M3 review round 2 (chk_side.py): presentations that share a stream are not told apart by stream, ignored stream, lead or
    T_env: FAU competing talker (code, left) / (code, right), and a DTU HI listener's individually equalised presentation / the NH
    original. A C6 remapping that moves every piece of one side presentation to the other (table and segment table rewritten
    consistently) was accepted by DonorBank, and the CSX sampler then paired left- and right-attending listeners as cross-person
    positives. check_piece_streams now also compares the attended side and the acoustic condition fields the table carries."""
    P = man["presentations"]
    by = {}
    for p in P:
        if p["cohort"] == "fau" and p["kind"] == "cs":
            by.setdefault(p["stimulus"], []).append(p)
    code, (pa, pb) = next((k, v) for k, v in sorted(by.items()) if len(v) == 2)
    assert pa["stream"] == pb["stream"] and pa["ignored_stream"] == pb["ignored_stream"] and pa["attended_side"] != pb["attended_side"]
    tp = _cohort_copy(fx, man, tmp_path / "side", "fau")
    t = json.loads(tp.read_text())
    moved = [i for i, it in enumerate(t["pieces"]) if it["presentation"] == pb["id"]]
    assert moved and all(t["pieces"][i]["attended_side"] == pb["attended_side"] for i in moved)
    for i in moved:
        t["pieces"][i]["presentation"] = pa["id"]
    tp.write_text(json.dumps(t))
    m2 = copy.deepcopy(dict(man))
    S = m2["segments"]["fau"]
    S["presentation"] = [pa["id"] if x == pb["id"] else x for x in S["presentation"]]
    M2 = V.Manifest(m2, None, None, str(tmp_path / "side"))
    with pytest.raises(ValueError, match="attended side"):
        V.DonorBank(M2, "fau", ("fit",), "cpu")
    with pytest.raises(ValueError, match="attended side"):
        V.target_view("fau", 0, M2, "A")
    # DTU: an HI listener's equalised piece remapped to the NH original (same stream, kind and side): only the condition differs
    t, items = _table(fx, "dtu")
    idx, streams = V.manifest_index(man), _streams(fx, "dtu")
    pres_of = V.piece_presentations(man, "dtu", t, items)
    n_cached = sum(it["row_offset"] is not None for it in items)
    hi = next(i for i, p in enumerate(pres_of) if p is not None and "equalised" in str(P[p]["condition"]))
    orig = next(q["id"] for q in P if q["cohort"] == "dtu" and q["kind"] == "ss" and q["stream"] == P[pres_of[hi]]["stream"]
                and "equalised" not in str(q["condition"]))
    remap = list(pres_of)
    remap[hi] = orig
    assert V.check_piece_streams("dtu", items, remap, idx, streams) == n_cached     # the fixture's pieces carry no condition
    with_cond = copy.deepcopy(items)
    for it, p in zip(with_cond, pres_of):
        if p is not None:
            it["condition"] = P[p]["condition"]                                     # as the C5 builder writes it
    assert V.check_piece_streams("dtu", with_cond, pres_of, idx, streams) == n_cached
    with pytest.raises(ValueError, match="condition field condition"):
        V.check_piece_streams("dtu", with_cond, remap, idx, streams)
    # SparrKULee: the task state is 'listeningActive' everywhere; noise condition, SNR and noise file are the acoustic condition
    # (C4 / C6; the noise file is a presentation property although not an XM condition class)
    m3 = copy.deepcopy(dict(man))
    for k, q in enumerate(q for q in m3["presentations"] if q["cohort"] == "sparrkulee"):
        q.update(noise_condition="in_noise" if k % 2 else "no_noise", snr=100.0 if k % 2 else None,
                 noise_file=f"noise_{q['stimulus']}.npz.gz" if k % 2 else None)
    idx3 = V.manifest_index(V.Manifest(m3, None, None, man.root))
    t, items = _table(fx, "sparrkulee")
    streams = _streams(fx, "sparrkulee")
    pres_of = V.piece_presentations(man, "sparrkulee", t, items)
    its = copy.deepcopy(items)
    for it, p in zip(its, pres_of):
        if p is not None:
            q = m3["presentations"][p]
            it.update(noise_condition=q["noise_condition"], snr=None if q["snr"] is None else int(q["snr"]),   # an int in the table
                      noise_file=q["noise_file"])
    n_cached = sum(it["row_offset"] is not None for it in its)
    assert V.check_piece_streams("sparrkulee", its, pres_of, idx3, streams) == n_cached
    i = next(k for k, it in enumerate(its) if it["row_offset"] is not None and it["snr"] is not None)
    for field, value in (("snr", -4), ("noise_condition", "no_noise"), ("condition", "listeningPassive"), ("snr", None),
                         ("noise_file", "noise_other.npz.gz")):
        bad = copy.deepcopy(its)
        bad[i][field] = value
        with pytest.raises(ValueError, match=f"condition field {field}"):
            V.check_piece_streams("sparrkulee", bad, pres_of, idx3, streams)
    with pytest.raises(ValueError, match="condition field noise_condition"):        # the presentation lacks the field: None there
        V.check_piece_streams("sparrkulee", its, pres_of, V.manifest_index(man), streams)


def _ev1_test_p(coh, sf):
    """ev1.evaluate_continuous's query participants, verbatim from its source (test segments, fold == subject fold or test_only)."""
    segs = coh.segments
    return sorted({s["p"] for s in segs if s["role"] == "test" and (coh.participants[s["p"]]["fold"] == sf or coh.participants[s["p"]].get("test_only"))})


def test_tick_batcher_binds_the_query_side_to_the_cell(fx, man):
    """M3 review round 2: TickBatcher checked only the training side against the manifest cell; the query side is now bound
    too. ev1 queries the participants with test segments whose fold is the row's subject fold (or test_only): they must be exactly
    the cell's test and test_only participants that have test segments, and none of them a training participant. Cases that
    pass the training check but not the query check: a cell that lists fewer test participants than the view's fold (b), a
    Federici cell without its phantom test_only sessions (d), and an always-train FAU participant whose fold is the test fold
    (trained on and queried, e)."""
    for cell in man["cells"]:
        ds, sf, cf = cell["dataset"], cell["subject_fold"], cell["content_fold"]
        if ds == "private_bdf":
            continue
        row = {"dataset": ds, "subject_fold": sf, "content_fold": cf}
        for train_p in (None, set()):
            coh = V.target_view(ds, cf, man, "A")
            bt = V.TickBatcher(coh, SPEC, row, "cpu", man, train_p=train_p)
            ids = [q["id"] for q in coh.participants]
            with_test = {ids[s["p"]] for s in coh.segments if s["role"] == "test"}
            assert bt.query_p == _ev1_test_p(coh, sf)
            assert {ids[i] for i in bt.query_p} == (set(cell["test"]) | set(cell["test_only"])) & with_test and bt.query_p
            assert not {ids[i] for i in bt.query_p} & set(cell["train"])

    def tampered(edit):
        m2 = copy.deepcopy(dict(man))
        edit(m2["cells"])
        return V.Manifest(m2, None, None, man.root)
    c_fau = next(c for c in man["cells"] if c["dataset"] == "fau" and c["subject_fold"] == 1 and c["content_fold"] == 0)
    dropped = sorted(c_fau["test"])[0]

    def drop_test(cells):
        c = next(c for c in cells if c["dataset"] == "fau" and c["subject_fold"] == 1 and c["content_fold"] == 0)
        c["test"] = [p for p in c["test"] if p != dropped]

    def drop_phantom(cells):
        next(c for c in cells if c["dataset"] == "federici" and c["subject_fold"] == 2)["test_only"] = []
    for edit, ds, sf, cf in ((drop_test, "fau", 1, 0), (drop_phantom, "federici", 2, 0)):
        for train_p in (None, set()):
            with pytest.raises(ValueError, match="query participants"):
                V.TickBatcher(V.target_view(ds, cf, man, "A"), SPEC, {"dataset": ds, "subject_fold": sf, "content_fold": cf}, "cpu",
                              tampered(edit), train_p=train_p)
    for train_p in (None, set()):                       # (e) an always-train participant labelled with the test fold in the view
        coh = V.target_view("fau", 0, man, "A")
        k = next(i for i, q in enumerate(coh.participants) if q["dev"])
        coh.participants[k]["fold"] = 1
        assert k in _ev1_test_p(coh, 1)                  # ev1 would query a participant that the fold also trains on
        with pytest.raises(ValueError, match=rf"training participants among the queries: \['{coh.participants[k]['id']}'\]"):
            V.TickBatcher(coh, SPEC, {"dataset": "fau", "subject_fold": 1, "content_fold": 0}, "cpu", man, train_p=train_p)


def test_bridge_rows_recheck_leave_target_out_and_the_row_rules(fx, man, tmp_path):
    """M3 review round 2 (chk_bridge_lto.py): bridge_rows accepted a donor set that lists the target's own stratum with a target
    row among the bridge rows, and a non-fit row planted in the core pool and the bridge rows, both of which DonorSampler refuses.
    It now re-checks leave-target-out and the DonorSampler row rules (role, kind, partner, participant, presentation) as defense
    in depth."""
    ok = SM.bridge_rows(man, "fau")
    assert ok["target"] == "fau" and "fau" not in {SM.coh_of(s) for s in ok["fit"]} and ok["n_fit_rows"] == len(man["bridge"]["fit_rows"]["fau"])
    assert SM.bridge_rows(man, "fau", root=man.root)["order"] == ok["order"]

    def tampered(edit, root=None):
        m2 = copy.deepcopy(dict(man))
        edit(m2)
        return V.Manifest(m2, None, None, root or man.root)

    def own_stratum(m):                                  # the reviewer's case 1
        ds = m["donor_sets"]["fau"]["core"]
        ds["strata"].append("fau"); ds["n_segments"].append(len(m["pools"]["core"]["fau"]))
        ds["weights"] = [x / sum(ds["n_segments"]) for x in ds["n_segments"]]
        m["bridge"]["fit_rows"]["fau"].append(["fau", int(m["pools"]["core"]["fau"][0])])
    m1 = tampered(own_stratum)
    with pytest.raises(ValueError, match="leave-target-out"):
        SM.bridge_rows(m1, "fau")
    with pytest.raises(ValueError, match="leave-target-out"):
        SM.DonorSampler(m1, "fau", "core", 1, "cpu")
    S = man["segments"]["dtu"]
    non_fit = next(i for i in range(len(S["s"])) if S["role"][i] != "fit")

    def plant(m, stratum, r):                            # the reviewer's case 2: a row planted in the core pool and the bridge rows
        m["pools"]["core"][SM.coh_of(stratum)].append(int(r))
        m["bridge"]["fit_rows"]["fau"].append([stratum, int(r)])
    with pytest.raises(ValueError, match="not fit"):
        SM.bridge_rows(tampered(lambda m: plant(m, "dtu", non_fit)), "fau")
    Sf = man["segments"]["fau"]
    cs_row = next(i for i in range(len(Sf["s"])) if Sf["kind"][i] == "cs" and Sf["role"][i] == "fit")
    with pytest.raises(ValueError, match="not fit / ss"):                 # a competing-talker row in the core rows of target dtu
        SM.bridge_rows(tampered(lambda m: m["bridge"]["fit_rows"]["dtu"].append(["fau", int(cs_row)]) or
                                m["pools"]["core"]["fau"].append(int(cs_row))), "dtu")
    with pytest.raises(ValueError, match="CSX"):                          # fau_cs is not a core stratum
        SM.bridge_rows(tampered(lambda m: m["donor_sets"]["dtu"]["core"]["strata"].append("fau_cs")), "dtu")
    # a bridge row of a participant that is not a donor in the cohort table (an HI-style listener): the table is read
    fit_rows = [r for s, r in man["bridge"]["fit_rows"]["fau"] if s == "dtu"]
    who = S["participant"][fit_rows[0]]
    (tmp_path / "nd").mkdir()
    for c in ("sparrkulee", "fau", "federici"):                           # bridge_rows reads every donor cohort's table
        os.symlink(os.path.join(fx["root"], man["cohorts"][c]["dir"]), tmp_path / "nd" / man["cohorts"][c]["dir"])
    tp = _cohort_copy(fx, man, tmp_path / "nd", "dtu")
    t = json.loads(tp.read_text())
    next(p for p in t["participants"] if p["participant"] == who)["group"] = "hi"
    tp.write_text(json.dumps(t))
    with pytest.raises(ValueError, match="is not a donor"):
        SM.bridge_rows(tampered(lambda m: None), "fau", root=str(tmp_path / "nd"))
    with pytest.raises(ValueError, match="is not a donor"):
        SM.bridge_rows(V.Manifest(dict(man), None, None, str(tmp_path / "nd")), "fau")      # the manifest's root= is used too


def test_restricted_path_names_and_manifest_constants(fx, tmp_path):
    """M3 review round 2: the restricted-path pattern missed 'sub-019.npy' and 'sub-019-eeg.npy' (it required the end of the
    component or '_' after the id); open_manifest compared only the constants the manifest carried, so a manifest without a
    constants block (the reviewer's real-data dry run) opened, and tau / onset64 were never compared."""
    bad = ("/x/sparrkulee/sub-019.npy", "/x/sparrkulee/sub-019-eeg.npy", "/x/sparrkulee/sub-020", "/x/sparrkulee/sub-021_ses-1.npy",
           "/x/SparrKULee/derivatives/SUB-022/eeg.npy", "/x/sparrkulee/split_data/train_-_sub-026_-_audiobook_1_-_eeg.npy",
           "/x/sparrkulee/sub-019.npy.gz", "/x/sparrkulee_nm/sub-026.d/run.npy")
    good = ("/x/sparrkulee/sub-0190.npy", "/x/sparrkulee/sub-023.npy", "/x/sparrkulee/sub-001-eeg.npy", "/x/dtu/sub-019.npy",
            "/x/sparrkulee/runs.json", "/x/sparrkulee/eeg_f16_tmajor.npy", "/x/sparrkulee/sub-02.npy")
    for p in bad:
        with pytest.raises(V.RestrictedAccess):
            V.check_path(p)
    assert [V.check_path(p) for p in good] == list(good)
    d = tmp_path / "sparrkulee"
    d.mkdir()
    (d / "sub-019-eeg.npy").write_bytes(b"")
    os.symlink(d / "sub-019-eeg.npy", tmp_path / "innocent.npy")
    with pytest.raises(V.RestrictedAccess):
        V.check_path(str(tmp_path / "innocent.npy"))                        # resolved through the symlink
    # constants: every key of contract_constants() present and equal (the fixture writes exactly that block)
    man0 = json.loads(open(fx["manifest_path"], "rb").read())
    assert man0["constants"] == V.contract_constants()

    def opened(edit):
        m = copy.deepcopy(man0)
        edit(m)
        p = tmp_path / "manifest_edit.json"
        p.write_text(json.dumps(m))
        import hashlib
        return V.open_manifest(str(p), hashlib.sha256(p.read_bytes()).hexdigest(), root=fx["root"])
    for edit, msg in ((lambda m: m.pop("constants"), "no constants block"), (lambda m: m.update(constants=[]), "no constants block"),
                      (lambda m: m["constants"].pop("tau"), r"missing \['tau'\]"),
                      (lambda m: m["constants"].pop("tick_offs_sha256"), "missing"),
                      (lambda m: m["constants"].update(span_eeg=357), r"unknown \['span_eeg'\]"),
                      (lambda m: m["constants"].update(tau=0.07), "different"), (lambda m: m["constants"].update(onset64=50), "different"),
                      (lambda m: m["constants"].update(key_bits=[23, 16]), "different"), (lambda m: m["constants"].update(fs=True), "different"),
                      (lambda m: m["constants"].update(neighbor="128"), "different"),
                      (lambda m: m["constants"].update(tick_offs_sha256="0" * 64), "different")):
        with pytest.raises(ValueError, match=msg):
            opened(edit)
    assert opened(lambda m: m["constants"].update(fs=64.0, tau=0.1)).sha256      # JSON numbers compare by value


# ---------------------------------------------------------------------------------------------------------- M3 review, round 3
def test_presentation_keys_are_unique(fx, man):
    """M3 review round 3 (c): two manifest presentations with one key were accepted and the key mapped silently to the last one,
    so a cohort-local table piece could be keyed to the wrong presentation. The index refuses a repeated key (key or
    presentation_key); distinct keys map one to one."""
    keyed = copy.deepcopy(dict(man))
    for q in keyed["presentations"]:
        q["key"] = f"{q['cohort']}:k{q['id']}"
    assert V.manifest_index(V.Manifest(keyed, None, None, man.root)).key == {q["key"]: q["id"] for q in keyed["presentations"]}
    dup = copy.deepcopy(keyed)
    fau = [q for q in dup["presentations"] if q["cohort"] == "fau"]
    fau[1]["key"] = fau[0]["key"]
    for build in (lambda m: V.manifest_index(m), lambda m: V.DonorBank(m, "fau", ("fit",), "cpu"),
                  lambda m: V.target_view("fau", 0, m, "A")):
        with pytest.raises(ValueError, match=rf"manifest presentations {fau[0]['id']} and {fau[1]['id']} share the key"):
            build(V.Manifest(copy.deepcopy(dup), None, None, man.root))
    pk = copy.deepcopy(dict(man))
    pk["presentations"][0]["presentation_key"] = pk["presentations"][1]["presentation_key"] = "x"
    with pytest.raises(ValueError, match="share the key 'x'"):
        V.manifest_index(V.Manifest(pk, None, None, man.root))


def test_targets_refuse_a_presentation_without_a_stream(fx, man):
    """M3 review round 3 (d): DonorBank._target_index indexed the stream tables with -1 for a presentation whose stream is None,
    so targets() returned a window of the last stream; a negative presentation id wrapped to the last presentation the same way.
    Both raise now, as does an id beyond the manifest."""
    m2 = copy.deepcopy(dict(man))
    P = m2["presentations"]
    p0 = next(q for q in P if q["cohort"] == "fau" and q["kind"] == "ss")
    P.append({**copy.deepcopy(p0), "id": len(P), "stream": None, "stimulus": "no_stream"})     # a presentation of no cached piece
    bank = V.DonorBank(V.Manifest(m2, None, None, man.root), "fau", ("fit",), "cpu")
    s = C.ENV_EDGE + 1
    assert tuple(bank.targets([p0["id"]], [s], [0]).shape) == (1, C.N_TGT)
    for bad, msg in (([len(P) - 1], "no attended stream"), ([p0["id"], len(P) - 1], "no attended stream"),
                     ([-1], "outside the manifest"), ([len(P)], "outside the manifest")):
        with pytest.raises(ValueError, match=msg):
            bank.targets(bad, [s] * len(bad), [0] * len(bad))


def test_segment_rows_match_their_slab_family_and_kind(fx, man):
    """M3 review round 3 (e): DonorBank accepted a manifest segment row whose role was changed from fit to dev, and one whose
    family differs from its presentation's. A row in a role that banks and fixed sets read by role (BANK_ROLES) must lie in that
    role's slab, and its family and kind must be its presentation's. A row in another role is accepted (C6 marks a declared
    exclusion's dev-slab segments excluded_declared; no pool or fixed set reads them)."""
    def edited(cohort, col, r, value):
        m2 = copy.deepcopy(dict(man))
        m2["segments"][cohort][col][r] = value
        return V.Manifest(m2, None, None, man.root)
    S = man["segments"]
    first = lambda c, role: next(i for i, x in enumerate(S[c]["role"]) if x == role)   # noqa: E731
    for c in ("fau", "sparrkulee"):                                           # the reviewer's case: a fit row relabelled dev
        with pytest.raises(ValueError, match="of slab 'fit'"):
            V.DonorBank(edited(c, "role", first(c, "fit"), "dev"), c, ("fit",), "cpu")
    for role in ("fit", "bridge_cal", "control_artefact"):                    # a dev-slab row in another bank role
        with pytest.raises(ValueError, match="of slab 'dev'"):
            V.DonorBank(edited("sparrkulee", "role", first("sparrkulee", "dev"), role), "sparrkulee", ("fit",), "cpu")
    b = V.DonorBank(edited("sparrkulee", "role", first("sparrkulee", "dev"), "excluded_declared"), "sparrkulee", ("fit", "dev"), "cpu")
    assert b.mode == "slabs" and b.roles == ("fit", "dev")
    r = first("sparrkulee", "fit")
    with pytest.raises(ValueError, match="family"):
        V.DonorBank(edited("sparrkulee", "family", r, (S["sparrkulee"]["family"][r] + 1) % len(man["families"])), "sparrkulee",
                    ("fit",), "cpu")
    with pytest.raises(ValueError, match="kind"):
        V.DonorBank(edited("dtu", "kind", 0, "cs" if S["dtu"]["kind"][0] == "ss" else "ss"), "dtu", ("fit",), "cpu")
    with pytest.raises(ValueError, match="presentation ids outside"):
        V.DonorBank(edited("fau", "presentation", 0, -1), "fau", ("fit",), "cpu")
    for c in V.DONOR_COHORTS:                                                 # the unedited manifest passes for every cohort
        V._check_segment_table(c, _table(fx, c)[1], V.manifest_index(man).seg[c], V.manifest_index(man))


def test_tick_batcher_reports_query_coverage(fx, man):
    """M3 review round 3 (INFO): the query check binds ev1's queries to the cell's test participants that have test segments in
    the view, so a cell test participant without any passes unnoticed; TickBatcher now reports the coverage (query_coverage) for
    the unit record."""
    row = {"dataset": "fau", "subject_fold": 1, "content_fold": 0}
    cell = V.manifest_cell(man, "fau", 1, 0)
    want = set(map(str, cell["test"])) | set(map(str, cell.get("test_only", ())))
    coh = V.target_view("fau", 0, man, "A")
    ids = [q["id"] for q in coh.participants]
    bt = V.TickBatcher(coh, SPEC, row, "cpu", man)
    queried = {ids[i] for i in bt.query_p}
    assert bt.query_coverage == {"cell_test_participants": len(want), "queried": len(queried),
                                 "cell_test_not_queried": sorted(want - queried)} and queried
    gone = ids[bt.query_p[0]]
    coh = V.target_view("fau", 0, man, "A")
    coh.segments = [s for s in coh.segments if not (ids[s["p"]] == gone and s["role"] == "test")]    # no test segment left
    bt = V.TickBatcher(coh, SPEC, row, "cpu", man)
    assert gone in bt.query_coverage["cell_test_not_queried"] and bt.query_coverage["queried"] == len(queried) - 1


def test_bridge_rows_needs_the_cache_root(fx, man):
    """M3 review round 3 (LOW, latent): bridge_rows reads the donor cohorts' tables for the participant rules, so it needs a cache
    root: root=, else the Manifest's. A plain-dict manifest without one fails closed with a message naming root=; with root= the
    rows equal the Manifest's. bridge.bridge_banks and bridge.fit_bridge must pass their root (reported for M6)."""
    ok = SM.bridge_rows(man, "fau")
    plain = dict(man)
    assert "cache_root" not in plain and not hasattr(plain, "root")
    with pytest.raises(ValueError, match="pass root="):
        SM.bridge_rows(plain, "fau")
    assert SM.bridge_rows(plain, "fau", root=man.root)["order"] == ok["order"]
    assert SM.bridge_rows({**plain, "cache_root": man.root}, "fau")["order"] == ok["order"]     # C6 records cache_root


def test_check_donor_rows_bounds_and_restricted_first(fx, man):
    """M3 review round 3 (INFO): check_donor_rows (shared by DonorSampler and bridge_rows) raises ValueError for rows outside
    the segment table (a negative row used to wrap as a numpy index), and the restricted-participant rule runs before the table
    lookup: a restricted SparrKULee participant raises RestrictedAccess even when the table does not list it."""
    idx = V.manifest_index(man)
    parts = {str(p["participant"]): p for p in _table(fx, "dtu")[0]["participants"]}
    good = [int(r) for r in man["pools"]["core"]["dtu"][:3]]
    SM.check_donor_rows(idx, "dtu", "dtu", good, parts, set())
    for bad in ([-1], [len(idx.seg["dtu"]["s"])], good + [-2]):
        with pytest.raises(ValueError, match="outside the dtu segment table"):
            SM.check_donor_rows(idx, "dtu", "dtu", bad, parts, set())
    m2 = copy.deepcopy(dict(man))
    r = int(man["pools"]["core"]["sparrkulee"][0])
    m2["segments"]["sparrkulee"]["participant"][r] = "019"
    idx2 = V.manifest_index(V.Manifest(m2, None, None, man.root))
    psk = {str(p["participant"]): p for p in _table(fx, "sparrkulee")[0]["participants"] if str(p["participant"]) != "019"}
    with pytest.raises(V.RestrictedAccess):
        SM.check_donor_rows(idx2, "sparrkulee", "sparrkulee", [r], psk, set())
