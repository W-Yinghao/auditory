"""M2c tests for the C3 audio scan (PUBLIC_PRIOR_DESIGN.md §2.5, §3.4, §6.2 C3, §7.1 4b / 4f / 8): synthetic envelopes with planted
duplicates, excerpts, shifted copies, jingles, natural/vocoded lags and cross-cohort overlaps; offsets must be recovered to the
sample, flags / merges / masks / exclusions must be the planted ones. The positive controls must pass on the planted family and fail
when the window scan is broken (no hits) or insensitive (r x 0.85); unrefined detections stay flagged; exclusions propagate through
families; the FAU attention-swapped scene pairs are reported. A synthetic source tree in the real layouts drives the CLI (resume,
--force, the scan_audio.latest.json pointer, exit 4 for a stale output, the out-root guard), with an open-audit hook proving that no
restricted SparrKULee participant file, no preprocessed EEG and no pickle is opened. The M1 fixture is scanned too: C3 reproduces
its family offsets, its cross-cohort overlap (with the manifest's lag sign) and, through the C6 rule, every fixture exclusion list.
Second review of M2c: on the real-source path a cohort that yields no stream fails the run before any scan, with an error naming it
(complete is asserted); source_sha256 follows the M1 / M2b float64 rule (fixtures.array_sha256); provisional_names stay complete
when a non-declared stream merges into the declared family. Third review: completeness counts keyed streams (a cohort of DTU
maskers or FAU distractors only fails like an empty one; a --sources run scans it but says complete false), a cohort missing from
the config gets the same FAILED file, a source a loader cannot read fails with exit 3 and a FAILED file instead of a traceback (a
RestrictedAccess refusal still propagates and writes nothing), and PROVISIONAL_CHECK is the last check of scan(), after the checks
that M2c already had. CPU only, tmp dirs only, about a minute and a half."""
import glob
import json
import os
import sys

import numpy as np
import pytest

from auditory_alignment_v3.prior33 import contract as C
from auditory_alignment_v3.prior33 import scan_audio as SA

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ------------------------------------------------------------------------------------------------ synthetic signals
def raw_env(rng, n, fs=64):
    """A positive speech-like envelope at `fs` (smoothed |noise|): its 2-8 Hz band carries the syllable-rate content."""
    k = np.hanning(max(3, fs // 8))
    k /= k.sum()
    return np.convolve(np.abs(rng.standard_normal(n)), k, mode="same") + 0.05


def stream(cohort, sid, raw, fs=64, kind="attended", keyed=True, **meta):
    x, _ = SA.prepare(raw, fs)
    return SA.Stream(cohort, sid, kind, keyed, x, meta)


def by_sid(rows):
    return {r["stream"]: r for r in rows}


def family_of(res, cohort, sid):
    for f in res["families"][cohort]:
        for m in f["members"]:
            if m["stream"] == sid:
                return f, m
    raise KeyError(sid)


def pair(res, cohort, a, b):
    out = [p for p in res["within"][cohort]["pairs"] if {p["a"], p["b"]} == {a, b}]
    assert out, (a, b)
    return out


def sk_streams(rng, o2=30986, shifted_lag=0):
    """The declared audiobook_1 structure (root, halves at +1711 / +o2, shifted copies, artefact excerpt) and three podcasts: a
    15 s jingle at podcast_1 [0, 960) and podcast_2 [320, 1280); podcast_3 independent."""
    master = raw_env(rng, 34000)
    jingle = raw_env(rng, 960)
    p1, p2 = raw_env(rng, 4000), raw_env(rng, 4200)
    p1[:960] = jingle
    p2[320:1280] = jingle
    h1 = master[1711:1711 + 3000].copy()
    s1 = master[1711 + shifted_lag:1711 + shifted_lag + 3000] + 0.15 * raw_env(rng, 3000)
    raws = {"audiobook_1": master, "audiobook_1_1": h1, "audiobook_1_2": master[o2:o2 + 2800].copy(),
            "audiobook_1_1_shifted": s1, "audiobook_1_2_shifted": master[o2:o2 + 2800] + 0.15 * raw_env(rng, 2800),
            "audiobook_1_artefact": master[:2500].copy(), "podcast_1": p1, "podcast_2": p2, "podcast_3": raw_env(rng, 4000)}
    return raws


def sk_cohort(raws):
    return sorted((stream("sparrkulee", k, v) for k, v in raws.items()), key=lambda s: s.sid)


# ------------------------------------------------------------------------------------------------ guards (§3.2, §6.2; hard rules)
def test_guard_refuses_restricted_participants_and_pickles(tmp_path):
    sk = tmp_path / "sk"
    SA.register_sk_root(sk)
    for rel in ("sub-019", "sub-020/ses-x/eeg/a.bdf.gz", "derivatives/preprocessed_eeg/sub-021/ses-a/x_eeg.npy",
                "derivatives/preprocessed_eeg/sub-022_ses-a_task-listeningActive_run-01_eeg.npy", "sub-026"):
        with pytest.raises(SA.RestrictedAccess):
            SA.guard_path(sk / rel)
    for ok in ("derivatives/preprocessed_stimuli/podcast_1_envelope.npy", "sub-018/ses-a/x.npy", "sub-0190", "sub-023/eeg"):
        assert SA.guard_path(sk / ok) == os.path.realpath(sk / ok)
    # DTU participants sub-021 / sub-022 are other people: outside a SparrKULee root nothing is refused
    assert SA.guard_path(tmp_path / "dtu" / "sub-021" / "trial.wav")
    for bad in ("x.data_dict", "y.pkl", "z.PICKLE"):
        with pytest.raises(SA.RestrictedAccess):
            SA.guard_path(tmp_path / bad)
    # the restriction holds for the real root whatever the config says
    with pytest.raises(SA.RestrictedAccess):
        SA.guard_path(os.path.join(SA.SK_ROOT_REAL, "derivatives", "preprocessed_eeg", "sub-019", "ses-x", "a.npy"))
    # a loader pointed at a restricted directory refuses before listing it
    with pytest.raises(SA.RestrictedAccess):
        SA.load_sparrkulee({"root": str(sk), "envelopes": "sub-019/stimuli"})


def test_npy_reads_never_unpickle(tmp_path):
    p = tmp_path / "obj_envelope.npy"
    np.save(p, np.array([{"a": 1}, None], dtype=object), allow_pickle=True)
    with pytest.raises(ValueError):
        SA.read_npy(p)
    d = tmp_path / "sk" / "derivatives" / "preprocessed_stimuli"
    d.mkdir(parents=True)
    np.save(d / "podcast_1_envelope.npy", np.array([[1.0]] * 10, dtype=object), allow_pickle=True)
    with pytest.raises(ValueError):
        SA.load_sparrkulee({"root": str(tmp_path / "sk")})


# ------------------------------------------------------------------------------------------------ primitives
def test_contract_chain_and_scale_invariance():
    rng = np.random.default_rng(3)
    for fs in (64, 100, 128):
        raw = raw_env(rng, 40 * fs, fs)
        x, rms = SA.prepare(raw, fs)
        ref, rref = C.rms_norm(C.band(C.resample64(raw, fs), C.env_sos()[0]), return_rms=True)
        np.testing.assert_allclose(x, ref, rtol=0, atol=1e-12)
        assert abs(rms - rref) < 1e-12 and abs(np.sqrt(np.mean(x ** 2)) - 1) < 1e-12
        x10, _ = SA.prepare(10 * raw, fs)
        np.testing.assert_allclose(x10, x, atol=1e-10)
    raw = raw_env(rng, 640)
    raw[100:110] = np.nan
    assert SA.prepare(raw, 64)[0] is not None and np.isfinite(SA.prepare(raw, 64)[0]).all()
    assert SA.prepare(np.full(500, np.nan), 128) == (None, 0.0)


def test_xcorr_pearson_matches_direct():
    rng = np.random.default_rng(5)
    a, b = rng.standard_normal(900), rng.standard_normal(700)
    ks, r = SA.xcorr_pearson(a, b, 200)
    for k in (-500, -123, 0, 17, 300, 700):
        t0, t1 = max(0, k), min(len(a), len(b) + k)
        want = np.corrcoef(a[t0:t1], b[t0 - k:t1 - k])[0, 1]
        assert abs(r[list(ks).index(k)] - want) < 1e-9
    assert ((np.minimum(len(a), len(b) + ks) - np.maximum(0, ks)) >= 200).all()
    # a planted copy b[u] = a[u + 250] is found exactly
    m = SA.measure_offset(a, a[250:650].copy(), max_lag=128)
    assert m["global"]["b_in_a"] == 250 and m["global"]["r"] > 0.999999
    assert m["window"] is None or abs(m["window"]["b_in_a"]) <= 128


def _brute(x, bank_streams, hop, self_j):
    """Per-window best Pearson r over every valid window of every other bank stream (direct)."""
    W = SA.WIN
    best = []
    for t in range(0, len(x) - W + 1, hop):
        q = x[t:t + W]
        if q.var() <= SA.VAR_FLOOR:
            continue
        top = (-np.inf, None, None)
        for j, s in enumerate(bank_streams):
            if j == self_j:
                continue
            V = np.lib.stride_tricks.sliding_window_view(s.x, W)
            v = V.var(1)
            r = ((V - V.mean(1, keepdims=True)) * ((q - q.mean()) / q.std())).mean(1) / np.sqrt(v)
            r[v <= SA.VAR_FLOOR] = -np.inf
            u = int(np.argmax(r))
            if r[u] > top[0]:
                top = (r[u], j, u)
        best.append((t,) + top)
    return best


@pytest.mark.parametrize("nfft,nq", [(2048, 1), (4096, 3), (16384, 8)])
def test_overlap_save_detection_matches_bruteforce(nfft, nq):
    rng = np.random.default_rng(11)
    a, b, c = raw_env(rng, 2600), raw_env(rng, 3100), raw_env(rng, 1900)
    b[1200:2100] = a[300:1200]                    # a 14 s copy: b[u] = a[u - 900] on the overlap
    S = [stream("dtu", n, v) for n, v in (("a", a), ("b", b), ("c", c))]
    bank = SA.Bank(S, nfft=nfft)
    assert bank.nfft <= nfft and bank.n_valid > 0
    h, nw, ns = SA.detect_stream(S[0].x, bank, 64, 0.9, 0, 1, nq)
    ref = _brute(S[0].x, S, 64, 0)
    assert nw == len(range(0, len(a) - SA.WIN + 1, 64)) and len(h["wt"]) == len(ref)
    for (t, r, j, u), wt, wr, wb, wu in zip(ref, h["wt"], h["wr"], h["wb"], h["wu"]):
        assert t == wt and abs(r - wr) < 2e-4
        if r > 0.5:
            assert (j, u) == (wb, wu)
    hits = {(int(t), int(b_), int(u)) for t, b_, u in zip(h["t"], h["b"], h["u"])}
    want = {(t, j, u) for t, r, j, u in ref if r >= 0.9}
    assert want and want <= hits
    assert all(u - t == 900 and b_ == 1 for t, b_, u in hits)          # b's u holds a's t + 900 - 900: lag b_in_a = -900


# ------------------------------------------------------------------------------------------------ SparrKULee declared family and jingles
def test_sparrkulee_offsets_merges_and_jingles():
    rng = np.random.default_rng(1)
    res = SA.scan({"sparrkulee": sk_cohort(sk_streams(rng))})
    rep = res["sparrkulee_audiobook_1"]
    assert rep["ok"] and all(c["ok"] for c in rep["checks"])
    want = {"audiobook_1": 0, "audiobook_1_1": 1711, "audiobook_1_2": 30986, "audiobook_1_1_shifted": 1711,
            "audiobook_1_2_shifted": 30986, "audiobook_1_artefact": 0}
    for m, k in want.items():
        if m != "audiobook_1":
            assert rep["measured"][m]["b_in_root"] == k and rep["measured"][m]["r"] > 0.95
        f, mem = family_of(res, "sparrkulee", m)
        assert f["name"] == "sparrkulee:audiobook_1" and f["clock"] == "known" and mem["offset"] == k and mem["offset_known"]
    assert f["basis"] == "declared" and not f["conflicts"] and len(f["members"]) == 6
    # the generic duplicate rule reproduces the declared structure: every member pair that overlaps >= 50 % is merged at the lag;
    # inside the declared group these merges are check-only edges, and all of them agree with the declared clock (residual 0)
    for a, b, k in (("audiobook_1", "audiobook_1_1", 1711), ("audiobook_1", "audiobook_1_2_shifted", 30986),
                    ("audiobook_1_1", "audiobook_1_1_shifted", 0), ("audiobook_1", "audiobook_1_artefact", 0)):
        p = pair(res, "sparrkulee", a, b)[0]
        assert p["action"] == "merge" and p["b_in_a"] == k and p["coverage"] >= 0.99 and p["edge_role"] == "check_only"
    scan_edges = [e for e in f["edges"] if e["source"] == "duplicate_scan"]
    assert len(scan_edges) == 7 and all(e["check_only"] and e["residual"] == 0 for e in scan_edges)
    assert sum(e["tree"] for e in f["edges"]) == 5 and all(e["source"] == "declared" for e in f["edges"] if e["tree"])
    # the artefact overlaps the first half only on 31.6 % of its length: no merge, and no mask (same family, same clock)
    p = pair(res, "sparrkulee", "audiobook_1_1", "audiobook_1_artefact")[0]
    assert p["b_in_a"] == -1711 and p["action"] == "family_mask_covers" and 0.3 < p["coverage"] < 0.32
    # jingle: podcast_1 [0, 960) = podcast_2 [320, 1280): masked on both, extended at most ~1 s past the planted span + 0.5 s margin
    p = pair(res, "sparrkulee", "podcast_1", "podcast_2")[0]
    assert p["action"] == "mask" and p["b_in_a"] == -320 and p["coverage"] < 0.5
    sh = {r["stream"]: r for r in res["shared_audio"]["sparrkulee"]}
    assert set(sh) == {"podcast_1", "podcast_2"}
    for sid, (j0, j1), L in (("podcast_1", (0, 960), 4000), ("podcast_2", (320, 1280), 4200)):
        a, b = sh[sid]["span"]
        assert a <= max(0, j0 - SA.MARGIN) and b >= j1 + SA.MARGIN, (sid, a, b)
        assert a >= j0 - SA.MARGIN - 2 * C.FS and b <= j1 + SA.MARGIN + 2 * C.FS, (sid, a, b)
        assert sh[sid]["partners"][0]["stream"] == ({"podcast_1", "podcast_2"} - {sid}).pop()
    assert not [p for p in res["within"]["sparrkulee"]["pairs"] if "podcast_3" in (p["a"], p["b"])]
    sec = res["shared_audio_seconds"]["sparrkulee"]
    assert sec["n_streams"] == 2 and abs(sec["masked_s"] - sum(r["span"][1] - r["span"][0] for r in sh.values()) / 64) < 1e-9
    rows = by_sid(res["streams"]["sparrkulee"])
    assert rows["audiobook_1_2"]["family"] == "sparrkulee:audiobook_1" and rows["audiobook_1_2"]["family_offset"] == 30986
    assert rows["podcast_3"]["family"] == "sparrkulee:podcast_3" and rows["podcast_3"]["family_offset"] == 0
    assert f["provisional_names"] == ["sparrkulee:audiobook_1"] and rows["podcast_1"]["kind"] == "attended"
    # positive controls: every declared relation is a merge of the window scan at its lag, and the cross path finds every member
    pc = res["positive_controls"]
    assert pc["ran"] and pc["ok"] and len(pc["relations"]) == 7 and len(pc["cross"]["rows"]) == 5
    assert {(r["x"], r["y"], r["expected_b_in_a"]) for r in pc["relations"]} == \
        {("audiobook_1", m, k) for m, k in want.items() if m != "audiobook_1"} | \
        {("audiobook_1_1", "audiobook_1_1_shifted", 0), ("audiobook_1_2", "audiobook_1_2_shifted", 0)}
    for r in pc["within"]:
        assert r["ok"] and any(f["action"] == "merge" and f["b_in_a"] == r["expected_b_in_a"] for f in r["found"]), r
    for r in pc["cross"]["rows"]:
        assert r["ok"] and r["flagged"] and any(f["b_in_a"] == r["expected_b_in_a"] and f["coverage"] > 0.99 for f in r["found"]), r
    assert all(c["ok"] for c in res["checks"] if c["level"] == "assert")
    assert [c["ok"] for c in res["checks"] if c["check"].startswith("SparrKULee shared audio found")] == [True]


def _no_hits(orig):
    def f(x, bank, hop, thr, self_j=None, workers=1, nq_max=8):
        h, nw, ns = orig(x, bank, hop, thr, self_j, workers, nq_max)
        return {k: (v[:0] if k in ("t", "b", "u", "r") else v) for k, v in h.items()}, nw, ns
    return f


def _degraded(orig, factor=0.85):
    """A silent sensitivity loss: window r effectively scaled by `factor` (hits only where r >= thr / factor)."""
    def f(x, bank, hop, thr, self_j=None, workers=1, nq_max=8):
        h, nw, ns = orig(x, bank, hop, min(0.999, thr / factor), self_j, workers, nq_max)
        h["wr"] = h["wr"] * factor
        return h, nw, ns
    return f


def test_positive_controls_catch_a_broken_window_scan(monkeypatch, tmp_path):
    """Review M2c problem 1: with the window scan broken (no hits) or insensitive (r x 0.85), the run must fail, not report 0 merges,
    0 masks and 0 overlaps as a clean result. The declared-offset check (global cross-correlation) cannot see this."""
    orig = SA.detect_stream
    rng = np.random.default_rng(1)
    S = sk_cohort(sk_streams(rng))
    monkeypatch.setattr(SA, "detect_stream", _no_hits(orig))
    res = SA.scan({"sparrkulee": S})
    assert res["sparrkulee_audiobook_1"]["ok"]                       # the global path is unaffected ...
    failed = [c["check"] for c in res["checks"] if c["level"] == "assert" and not c["ok"]]
    assert not res["positive_controls"]["ok"] and len(failed) == 12   # ... the 7 window relations and the 5 cross probes fail
    assert sum(f.startswith("positive control (window scan)") for f in failed) == 7
    assert sum(f.startswith("positive control (cross rule)") for f in failed) == 5
    assert [c["ok"] for c in res["checks"] if c["check"].startswith("SparrKULee shared audio found")] == [False]
    # insensitive: the exact excerpts still merge, the noisy shifted copies (r ~ 0.99 < 0.9 / 0.85) do not
    monkeypatch.setattr(SA, "detect_stream", _degraded(orig))
    res = SA.scan({"sparrkulee": S})
    bad = {(r["x"], r["y"]) for r in res["positive_controls"]["within"] if not r["ok"]}
    assert not res["positive_controls"]["ok"] and bad == {("audiobook_1", "audiobook_1_1_shifted"), ("audiobook_1", "audiobook_1_2_shifted"),
                                                          ("audiobook_1_1", "audiobook_1_1_shifted"), ("audiobook_1_2", "audiobook_1_2_shifted")}
    # the CLI on the synthetic source tree: exit 3, a FAILED file, the pointer says failed
    monkeypatch.setattr(SA, "detect_stream", _no_hits(orig))
    cfg, _, _ = make_tree(tmp_path / "src")
    out = tmp_path / "cache"
    assert SA.main(["--sources", cfg, "--out", str(out)]) == SA.EXIT_FAILED
    assert not (out / SA.OUT_NAME).exists() and json.load(open(out / SA.LATEST_NAME))["status"] == "failed"
    doc = json.load(open(out / SA.FAILED_NAME))
    assert doc["summary"]["n_cross_overlaps"] == 0 and not doc["positive_controls"]["ok"]


def test_sparrkulee_declared_offset_assertion():
    rng = np.random.default_rng(2)
    _, rep = SA.sk_declared(sk_cohort(sk_streams(rng, o2=30990)))
    bad = [c for c in rep["checks"] if not c["ok"]]
    # the half and its shifted copy (cut at the same place) both miss the declared +30986; the copy stays on its half's clock
    assert not rep["ok"] and all(c["level"] == "assert" for c in bad)
    assert [c["detail"] for c in bad] == [{"expected": 30986, "measured": 30990},
                                          {"expected": 30986, "measured": 30990, "declared_as": "audiobook_1_2"}]
    # a shifted copy 3 samples off its half: an assertion (§2.5 'asserts them to +-1'), both against the declared offset and the half
    rng = np.random.default_rng(2)
    _, rep = SA.sk_declared(sk_cohort(sk_streams(rng, shifted_lag=3)))
    bad = [c for c in rep["checks"] if not c["ok"]]
    assert not rep["ok"] and rep["measured"]["audiobook_1_1_shifted"]["b_in_root"] == 1714
    assert [c["detail"] for c in bad] == [{"expected": 1711, "measured": 1714, "declared_as": "audiobook_1_1"}, {"difference": 3}]
    assert all(c["level"] == "assert" for c in bad)
    # one sample off (the real audiobook_1_1_shifted sits at +1712): within the tolerance; the family takes the measured offset
    rng = np.random.default_rng(2)
    res = SA.scan({"sparrkulee": sk_cohort(sk_streams(rng, shifted_lag=1))})
    rep = res["sparrkulee_audiobook_1"]
    assert rep["ok"] and all(c["ok"] for c in rep["checks"]) and rep["measured"]["audiobook_1_1_shifted"]["b_in_root"] == 1712
    assert family_of(res, "sparrkulee", "audiobook_1_1_shifted")[1]["offset"] == 1712 and res["positive_controls"]["ok"]
    w = {(r["x"], r["y"]): r for r in res["positive_controls"]["within"]}
    assert w[("audiobook_1_1", "audiobook_1_1_shifted")]["expected_b_in_a"] == 1
    assert [f["b_in_a"] for f in w[("audiobook_1_1", "audiobook_1_1_shifted")]["found"] if f["action"] == "merge"] == [1]
    # a missing declared member fails
    rng = np.random.default_rng(2)
    raws = sk_streams(rng)
    del raws["audiobook_1_artefact"]
    _, rep = SA.sk_declared(sk_cohort(raws))
    assert not rep["ok"]


# ------------------------------------------------------------------------------------------------ duplicate rule within a cohort
def test_merge_rule_threshold_and_offsets():
    """A 1-s hop / r >= 0.9 duplicate covering >= 50 % of the shorter stream merges at the detected lag; a shorter one is masked."""
    rng = np.random.default_rng(4)
    a = raw_env(rng, 3200)
    b = a[1000:].copy()                                        # 100 % of b: merged, offset +1000
    c = raw_env(rng, 2000); c[500:1300] = a[200:1000]          # 40 % of c: masked
    d = raw_env(rng, 2000); d[100:1300] = a[1800:3000]         # 60 % of d: merged, b_in_a(a, d) = 1700
    e = raw_env(rng, 2000)
    S = sorted((stream("dtu", n, v) for n, v in (("a", a), ("b", b), ("c", c), ("d", d), ("e", e))), key=lambda s: s.sid)
    res = SA.scan({"dtu": S})
    f, _ = family_of(res, "dtu", "a")
    offs = {m["stream"]: m["offset"] for m in f["members"]}
    assert offs == {"a": 0, "b": 1000, "d": 1700} and f["clock"] == "known" and f["basis"] == "duplicate_scan" and not f["conflicts"]
    assert f["name"] == "dtu:a" and f["provisional_names"] == ["dtu:a", "dtu:b", "dtu:d"]
    pc = pair(res, "dtu", "a", "c")[0]
    assert pc["action"] == "mask" and pc["b_in_a"] == -300 and 0.35 < pc["coverage"] < 0.45
    sh = {r["stream"]: r["span"] for r in res["shared_audio"]["dtu"]}
    assert set(sh) == {"a", "c"}
    assert sh["c"][0] <= 500 - SA.MARGIN and sh["c"][1] >= 1300 + SA.MARGIN and sh["c"][1] - sh["c"][0] <= 800 + 2 * SA.MARGIN + 4 * C.FS
    assert sh["a"][0] <= 200 - SA.MARGIN and sh["a"][1] >= 1000 + SA.MARGIN
    assert family_of(res, "dtu", "e")[0]["members"] == [{"stream": "e", "offset": 0, "offset_s": 0.0, "offset_known": True, "length": 2000}]
    # b and d overlap each other only through a: the b-d pair is consistent with the family offsets (no mask)
    for p in res["within"]["dtu"]["pairs"]:
        if {p["a"], p["b"]} == {"b", "d"}:
            assert p["action"] in ("merge", "family_mask_covers")


def test_unrefined_detections_are_kept_and_flagged(monkeypatch):
    """Review M2c problem 5: a detection whose lag refinement finds no candidate keeps the best hit's lag (refined false): it is
    still merged / masked within a cohort and flagged across cohorts, and a warning lists it."""
    monkeypatch.setattr(SA, "refine_lag", lambda a, b, ks, xpos, rs: (None, SA._union([(int(p), int(p) + SA.WIN) for p in xpos])))
    rng = np.random.default_rng(4)
    a = raw_env(rng, 3200)
    b = a[1000:].copy()
    c = raw_env(rng, 2000); c[500:1300] = a[200:1000]
    f = raw_env(rng, 3000)
    g = raw_env(rng, 3000); g[1000:1896] = f[1500:2396]                 # 14 s shared across cohorts: b_in_a(f, g) = 500
    res = SA.scan({"fau": [stream("fau", "122/attended", f)], "dtu": sorted([stream("dtu", n, v) for n, v in (("a", a), ("b", b), ("c", c),
                                                                                                        ("g", g))], key=lambda s: s.sid)})
    fam, _ = family_of(res, "dtu", "a")
    assert {m["stream"]: m["offset"] for m in fam["members"]} == {"a": 0, "b": 1000}
    pc = pair(res, "dtu", "a", "c")[0]
    assert pc["action"] == "mask" and pc["b_in_a"] == -300 and pc["refined"] is False
    assert {r["stream"] for r in res["shared_audio"]["dtu"]} == {"a", "c"}
    o = res["cross_cohort"]["overlaps"]
    assert len(o) == 1 and o[0]["refined"] is False and o[0]["b_in_a"] == 500 and o[0]["lag"] == -500
    assert res["cross_cohort"]["donor_exclusions"]["fau"]["dtu"] == ["g"] and res["cross_cohort"]["donor_exclusions"]["dtu"]["fau"] == ["122/attended"]
    warn = {c_["check"]: c_ for c_ in res["checks"] if c_["level"] == "warn"}
    assert not warn["every within-cohort detection refined"]["ok"]
    assert not warn["every cross-cohort detection refined (unrefined ones are flagged at the best hit's lag)"]["ok"]
    assert res["summary"]["n_cross_unrefined"] == 1


def test_family_propagated_donor_exclusions():
    """A donor stream flagged against a target excludes every member of its family (donor_exclusions); donor_exclusions_direct
    keeps the direct flags. Overlap records carry lag = b.span[0] - a.span[0] = -b_in_a and the stimulus of each side."""
    rng = np.random.default_rng(12)
    f = raw_env(rng, 3000)
    dA = raw_env(rng, 3000); dA[200:1096] = f[1500:2396]                  # dA[u] = f[u + 1300] on 14 s
    dR = dA[1400:].copy()                                                 # re-cut copy of dA without the shared excerpt
    S = {"fau": [stream("fau", "122/attended", f)],
         "dtu": sorted([stream("dtu", n, v) for n, v in (("dA", dA), ("dR", dR), ("dZ", raw_env(rng, 3000)))], key=lambda s: s.sid)}
    res = SA.scan(S)
    cc = res["cross_cohort"]
    assert {m["stream"]: m["offset"] for m in family_of(res, "dtu", "dA")[0]["members"]} == {"dA": 0, "dR": 1400}
    assert len(cc["overlaps"]) == 1
    o = cc["overlaps"][0]
    assert (o["a"]["stream"], o["b"]["stream"], o["b_in_a"], o["lag"]) == ("122/attended", "dA", 1300, -1300)
    assert o["lag"] == o["b"]["span"][0] - o["a"]["span"][0] and (o["a"]["stimulus"], o["b"]["stimulus"]) == ("122", "dA")
    assert cc["donor_exclusions_direct"]["fau"] == {"dtu": ["dA"]} and cc["donor_exclusions"]["fau"] == {"dtu": ["dA", "dR"]}
    assert cc["added_via_family"]["fau"] == {"dtu": ["dR"]} and cc["donor_exclusions"]["dtu"] == {"fau": ["122/attended"]}
    assert cc["donor_exclusions"]["federici"] == {"fau": [], "dtu": []} and cc["flagged_streams"] == {"fau": ["122/attended"], "dtu": ["dA"]}
    assert set(cc["not_scanned"]) == {"private_bdf"} and cc["donor_exclusions"]["private_bdf"] == {"fau": [], "dtu": []}
    assert [a_["status"] for a_ in res["assumptions"] if a_["item"].startswith("private_bdf")] == ["unverified"]


def test_detection_guaranteed_lengths():
    """The fixed rule always finds exact shared audio of >= 11 s within a cohort (a 1 s-grid 10 s window fits inside) and of >= 12 s
    across cohorts (2 s grid), wherever it sits; shorter audio is the documented detection limit (review: 9.5 s 6/6, 9 s 4/6)."""
    rng = np.random.default_rng(31)

    def bandlim(n):
        y = C.band(rng.standard_normal(n + 400), C.env_sos()[0])[200:200 + n]
        return y / np.sqrt(np.mean(y ** 2))

    for o in (5, 23, 41, 63):
        a, b = bandlim(3000), bandlim(3000)
        b[1000 + o:1000 + o + 704] = a[1700 + o:1700 + o + 704]            # 11 s: b[u] = a[u + 700]
        res = SA.scan({"dtu": [SA.Stream("dtu", "a", "attended", True, a, {}), SA.Stream("dtu", "b", "attended", True, b, {})]})
        assert [(p["action"], p["b_in_a"]) for p in res["within"]["dtu"]["pairs"]] == [("mask", 700)], o
        a, b = bandlim(3000), bandlim(3000)
        b[1000 + 2 * o:1000 + 2 * o + 768] = a[1700 + 2 * o:1700 + 2 * o + 768]      # 12 s across cohorts
        res = SA.scan({"fau": [SA.Stream("fau", "111/attended", "attended", True, a, {})], "dtu": [SA.Stream("dtu", "b", "attended", True, b, {})]})
        assert [(o_["b_in_a"], o_["detected_from"]) for o_ in res["cross_cohort"]["overlaps"]] == [(700, ["dtu", "fau"])], o


def test_family_conflict_gives_unknown_clock():
    rng = np.random.default_rng(6)
    S = [stream("dtu", n, raw_env(rng, 2000 + 100 * i)) for i, n in enumerate("abc")]
    ok = [{"a": "a", "b": "b", "k": 100, "source": "duplicate_scan", "weight": 0.9},
          {"a": "b", "b": "c", "k": 50, "source": "duplicate_scan", "weight": 0.8},
          {"a": "a", "b": "c", "k": 151, "source": "duplicate_scan", "weight": 0.7}]
    fams, member = SA.build_families("dtu", S, ok)
    assert len(fams) == 1 and fams[0]["clock"] == "known" and fams[0]["root"] == "c"
    assert {m["stream"]: m["offset"] for m in fams[0]["members"]} == {"c": 150, "a": 0, "b": 100}
    bad = ok[:2] + [{"a": "a", "b": "c", "k": 200, "source": "duplicate_scan", "weight": 0.7}]
    fams, member = SA.build_families("dtu", S, bad)
    f = fams[0]
    assert f["clock"] == "unknown" and len(f["conflicts"]) == 1 and abs(f["conflicts"][0]["residual"]) == 50
    assert [m["stream"] for m in f["members"] if m["offset_known"]] == [f["root"]] and member[f["root"]][1] == 0
    # offsets beyond the 2**24 key budget are refused
    with pytest.raises(SA.ScanError):
        SA.build_families("dtu", S, [{"a": "a", "b": "b", "k": 1 << 24, "source": "duplicate_scan", "weight": 1.0}])


def test_provisional_names_complete_when_a_stream_merges_into_the_declared_family():
    """Review 2 of M2c, item 3: provisional_names lists every member's C4 / C5 provisional name. podcast_9, a re-cut of the root
    (100 % of it), merges into the declared audiobook_1 family at +10000 and keeps its own provisional name 'sparrkulee:podcast_9'
    (M2c listed 'sparrkulee:audiobook_1' only, so C6 could not re-map C4's family of podcast_9); the names are
    build_sparrkulee.family_name's. PROVISIONAL_CHECK fails when a declared member lands outside the declared family."""
    from auditory_alignment_v3.prior33 import build_sparrkulee as BS
    rng = np.random.default_rng(1)
    raws = sk_streams(rng)
    raws["podcast_9"] = raws["audiobook_1"][10000:13000].copy()
    res = SA.scan({"sparrkulee": sk_cohort(raws)})
    f, m = family_of(res, "sparrkulee", "podcast_9")
    assert f["name"] == "sparrkulee:audiobook_1" and m["offset"] == 10000 and m["offset_known"] and len(f["members"]) == 7
    assert f["provisional_names"] == ["sparrkulee:audiobook_1", "sparrkulee:podcast_9"]
    assert f["basis"] == "declared+duplicate_scan" and f["clock"] == "known" and not f["conflicts"]
    p = [p for p in pair(res, "sparrkulee", "audiobook_1", "podcast_9") if p["action"] == "merge"]
    assert len(p) == 1 and p[0]["b_in_a"] == 10000 and p[0]["coverage"] > 0.99 and p[0]["edge_role"] == "tree"
    rows = by_sid(res["streams"]["sparrkulee"])
    assert rows["podcast_9"]["family"] == "sparrkulee:audiobook_1" and rows["podcast_9"]["family_offset"] == 10000
    # every family lists exactly its members' C4 names (build_sparrkulee.family_name), and each name lies in one family
    assert set(SA.sk_declared_members()) == set(BS.DECLARED_FAMILY)
    for f_ in res["families"]["sparrkulee"]:
        assert f_["provisional_names"] == sorted({BS.family_name(m_["stream"]) for m_ in f_["members"]}), f_["name"]
    assert [c_["ok"] for c_ in res["checks"] if c_["check"] == SA.PROVISIONAL_CHECK] == [True]
    # PROVISIONAL_CHECK (assert level, new in this review) is appended last: the checks M2c had keep their positions
    assert res["checks"][-1]["check"] == SA.PROVISIONAL_CHECK and res["checks"][-1]["level"] == "assert"
    assert res["positive_controls"]["ok"] and all(c_["ok"] for c_ in res["checks"] if c_["level"] == "assert")
    # a declared member that does not match the root (r < 0.9) stays outside the declared family: its C4 name
    # 'sparrkulee:audiobook_1' then lies in two families, which C6 could not re-map (an assertion, besides the declared-member one)
    raws = sk_streams(np.random.default_rng(1))
    raws["audiobook_1_artefact"] = raw_env(np.random.default_rng(99), 2500)
    res = SA.scan({"sparrkulee": sk_cohort(raws)})
    (pc,) = [c_ for c_ in res["checks"] if c_["check"] == SA.PROVISIONAL_CHECK]
    assert pc["level"] == "assert" and not pc["ok"] and not res["sparrkulee_audiobook_1"]["ok"]
    assert pc["detail"] == {"sparrkulee": {"sparrkulee:audiobook_1": ["sparrkulee:audiobook_1", "sparrkulee:audiobook_1_artefact"]}}
    # build_families directly: without declared_members the declared edges' endpoints are the declared members
    S = [stream("sparrkulee", n, raw_env(np.random.default_rng(i), 2000)) for i, n in enumerate(("audiobook_1", "audiobook_1_1", "podcast_9"))]
    fams, _ = SA.build_families("sparrkulee", S, [{"a": "audiobook_1", "b": "audiobook_1_1", "k": 5, "source": "declared", "weight": 1.0},
                                                  {"a": "audiobook_1", "b": "podcast_9", "k": 70, "source": "duplicate_scan", "weight": 0.9}],
                                family_name="audiobook_1")
    assert len(fams) == 1 and fams[0]["name"] == "sparrkulee:audiobook_1"
    assert fams[0]["provisional_names"] == ["sparrkulee:audiobook_1", "sparrkulee:podcast_9"]
    # a Federici item merged into another content group's family keeps its own group name
    F = [stream("federici", n, raw_env(np.random.default_rng(i), 2000, 100), 100, "item", content_group=g)
         for i, (n, g) in enumerate((("N1", 0), ("V1", 0), ("X", 5)))]
    fams, _ = SA.build_families("federici", F, [{"a": "N1", "b": "V1", "k": 0, "source": "natural_vocoded", "weight": 0.9},
                                                {"a": "V1", "b": "X", "k": 30, "source": "duplicate_scan", "weight": 0.8}])
    assert len(fams) == 1 and fams[0]["name"] == "federici:g0" and fams[0]["provisional_names"] == ["federici:g0", "federici:g5"]
    assert fams[0]["crosses_content_groups"]


# ------------------------------------------------------------------------------------------------ Federici natural / vocoded
def fed_items(rng, n100=3000):
    """At 100 Hz: N1 / V1 with V1[u] = N1[u + 75] (+48 at 64 Hz), N2 / V2 unrelated, N3 / V3 shifted 300 (192 at 64 Hz, outside
    +-2 s), N4 alone. Returns raw arrays and content groups."""
    m1, m3 = raw_env(rng, n100 + 75, 100), raw_env(rng, n100 + 300, 100)
    raws = {"N1": m1[:n100], "V1": 0.8 * m1[75:75 + n100] + 0.05 * raw_env(rng, n100, 100), "N2": raw_env(rng, n100, 100),
            "V2": raw_env(rng, n100, 100), "N3": m3[:n100], "V3": 0.8 * m3[300:300 + n100] + 0.05 * raw_env(rng, n100, 100),
            "N4": raw_env(rng, n100, 100)}
    group = {"N1": 0, "V1": 0, "N2": 1, "V2": 1, "N3": 2, "V3": 2, "N4": 3}
    return raws, group


def test_federici_natural_vocoded_lags():
    rng = np.random.default_rng(8)
    raws, group = fed_items(rng)
    S = sorted((stream("federici", k, v, fs=100, kind="item", content_group=group[k], n_listeners=5 if k[0] == "N" else 2,
                       condition="natural" if k[0] == "N" else "vocoded") for k, v in raws.items()), key=lambda s: s.sid)
    res = SA.scan({"federici": S})
    recs = {r["partner"]: r for r in res["federici_natural_vocoded"]}
    assert set(recs) == {"V1", "V2", "V3"} and {r["reference"] for r in recs.values()} == {"N1", "N2", "N3"}
    assert recs["V1"]["clock"] == "known" and recs["V1"]["offset"] == 48 and recs["V1"]["window"]["r"] > 0.9
    assert recs["V2"]["clock"] == "unknown" and recs["V2"]["offset"] is None and "< 0.5" in recs["V2"]["reason"]
    assert recs["V3"]["clock"] == "unknown" and recs["V3"]["global"]["b_in_a"] == 192 and "outside" in recs["V3"]["reason"]
    f, m = family_of(res, "federici", "V1")
    assert f["name"] == "federici:g0" and f["clock"] == "known" and m["offset"] == 48 and family_of(res, "federici", "N1")[1]["offset"] == 0
    for v in ("V2", "V3"):
        f, m = family_of(res, "federici", v)
        assert f["clock"] == "unknown" and not m["offset_known"] and m["offset"] is None and f["basis"] == "natural_vocoded"
    # V3 duplicates N3 at +192 (> 2 s): the generic merge is check-only, the +-2 s rule keeps the clock unknown, and no mask is added
    p = pair(res, "federici", "N3", "V3")[0]
    assert p["action"] == "merge" and p["b_in_a"] == 192 and p["edge_role"] == "check_only"
    assert not res["shared_audio"]["federici"]
    assert family_of(res, "federici", "N4")[0]["basis"] == "own"


# ------------------------------------------------------------------------------------------------ cross-cohort overlap (§3.4.2)
def test_cross_cohort_flags_and_donor_exclusions():
    rng = np.random.default_rng(9)
    fau112 = raw_env(rng, 2 * 3000, 128)
    dtuA = raw_env(rng, 2 * 2600, 128)
    dtuA[1000:1000 + 1792] = fau112[2000:2000 + 1792]            # 14 s: DTU 64 Hz 500 = FAU 64 Hz 1000 -> b_in_a 500
    e128 = raw_env(rng, 1920, 128)
    sk3 = raw_env(rng, 4000)
    sk3[1000:1960] = C.resample64(e128, 128)                    # 15 s heard by FAU listeners as a distractor
    dis = raw_env(rng, 2 * 3200, 128)
    dis[4000:5920] = e128
    S = {"sparrkulee": [stream("sparrkulee", "podcast_3", sk3), stream("sparrkulee", "podcast_4", raw_env(rng, 4000))],
         "fau": sorted([stream("fau", "112/attended", fau112, 128, "attended"), stream("fau", "215/attended", raw_env(rng, 6400, 128), 128, "attended"),
                        stream("fau", "215/distractor", dis, 128, "distractor", keyed=False)], key=lambda s: s.sid),
         "dtu": sorted([stream("dtu", "dtuA", dtuA, 128), stream("dtu", "dtuB", raw_env(rng, 5200, 128), 128)], key=lambda s: s.sid),
         "federici": [stream("federici", "N9", raw_env(rng, 3000, 100), 100, "item")]}
    res = SA.scan(S)
    ov = res["cross_cohort"]["overlaps"]
    got = {(o["a"]["cohort"], o["a"]["stream"], o["b"]["cohort"], o["b"]["stream"]): o for o in ov}
    assert set(got) == {("fau", "112/attended", "dtu", "dtuA"), ("sparrkulee", "podcast_3", "fau", "215/distractor")}
    o = got[("fau", "112/attended", "dtu", "dtuA")]
    assert o["b_in_a"] == 500 and o["r_window_max"] > 0.95 and o["r_detect_max"] > 0.95 and set(o["detected_from"]) == {"fau", "dtu"}
    a0, a1 = o["a"]["span"]
    assert a0 <= 1000 + 64 and a1 >= 1896 - 64 and o["b"]["span"] == [a0 - 500, a1 - 500]
    o = got[("sparrkulee", "podcast_3", "fau", "215/distractor")]
    assert o["b_in_a"] == -1000 and o["b"]["keyed"] is False
    ex = res["cross_cohort"]["donor_exclusions"]
    assert ex["fau"] == {"sparrkulee": ["podcast_3"], "dtu": ["dtuA"], "federici": []}
    assert ex["dtu"] == {"sparrkulee": [], "fau": ["112/attended"], "federici": []}
    assert ex["federici"] == {"sparrkulee": [], "fau": [], "dtu": []} and set(ex["private_bdf"]) == set(SA.COHORTS)
    assert all(v == [] for v in ex["private_bdf"].values()) and "sparrkulee" not in ex
    st = {(s["query"], s["bank"]): s for s in res["cross_cohort"]["stats"]}
    assert len(st) == 12 and st[("fau", "dtu")]["n_ge_thr"] >= 1 and st[("dtu", "federici")]["n_ge_thr"] == 0
    assert res["cross_cohort"]["flagged_streams"]["federici"] == []


def test_scene_pairs_classification():
    """FAU scene pairs (review M2c problem 6, report only): both swapped relations at one lag = the same scene; at two lags = same
    content, different scene; one relation only = a shared stream, not attention-swapped; < 50 % coverage is not a relation."""
    S = [SA.Stream("fau", f"{c}/{w}", w, w == "attended", np.zeros(1), {}) for c in ("210", "215", "220", "225", "229") for w in ("attended", "distractor")]
    rec = lambda a, b, k, cov=1.0: {"a": a, "b": b, "b_in_a": k, "coverage": cov, "action": "report_only"}      # noqa: E731
    pairs = [rec("210/attended", "220/distractor", 0), rec("210/distractor", "220/attended", 1),         # same scene (lags 0, 1)
             rec("215/attended", "225/distractor", 0), rec("225/attended", "215/distractor", 300),      # b_in_a(215d, 225a) = -300
             rec("210/attended", "229/distractor", 64), rec("215/attended", "229/attended", 0, 0.3)]     # one-sided; partial
    got = {tuple(p["codes"]): p for p in SA.scene_pairs(S, pairs)}
    assert set(got) == {("210", "220"), ("215", "225"), ("210", "229")}
    assert got[("210", "220")]["attention_swapped"] and got[("210", "220")]["same_scene"]
    assert got[("215", "225")]["attention_swapped"] and not got[("215", "225")]["same_scene"]
    assert got[("215", "225")]["distractor_X~attended_Y"] == [-300] and got[("215", "225")]["attended_X~distractor_Y"] == [0]
    assert not got[("210", "229")]["attention_swapped"] and got[("210", "229")]["attended_X~distractor_Y"] == [64]
    assert all(p["action"] == "report_only" for p in got.values())


# ------------------------------------------------------------------------------------------------ CLI on a synthetic source tree
def _h5(path, data):
    import h5py
    with h5py.File(path, "w") as f:
        for k, v in data.items():
            f.create_dataset(k, data=v)


def make_tree(root, o2=30986, shifted_lag=1):
    """Synthetic sources in the real layouts (SparrKULee npy dir with restricted decoys and a pickle, FAU stimulus h5, DTU
    audio_local.h5 + inventory + content groups, Federici per-participant h5 + content groups) -> sources JSON path. As on the real
    data, audiobook_1_1_shifted sits one sample after its half (+1712)."""
    from auditory_alignment.federici_content import env_key
    rng = np.random.default_rng(21)
    root = str(root)
    sk = os.path.join(root, "sparrkulee")
    d = os.path.join(sk, "derivatives", "preprocessed_stimuli")
    os.makedirs(d)
    raws = sk_streams(rng, o2=o2, shifted_lag=shifted_lag)
    e128 = raw_env(rng, 1920, 128)
    raws["podcast_3"][1000:1960] = C.resample64(e128, 128)
    for k, v in raws.items():
        np.save(os.path.join(d, f"{k}_envelope.npy"), v[:, None])
    np.save(os.path.join(d, "audiobook_9_2_envelope-1.npy"), raws["podcast_3"][:, None])      # ignored duplicate file
    with open(os.path.join(d, "podcast_1.data_dict"), "wb") as f:
        f.write(b"\x80\x04K\x01.")                                                          # a pickle: never opened
    decoys = [os.path.join(sk, "derivatives", "preprocessed_eeg", "sub-019", "ses-a",
                           "sub-019_ses-a_task-listeningActive_run-01_desc-preproc-audio-podcast_1_eeg.npy"),
              os.path.join(sk, "derivatives", "preprocessed_eeg", "sub-005", "ses-a",
                           "sub-005_ses-a_task-listeningActive_run-01_desc-preproc-audio-podcast_1_eeg.npy"),
              os.path.join(sk, "sub-020", "ses-a", "eeg", "sub-020_ses-a_task-listeningActive_run-01_eeg.npy")]
    for p in decoys:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        np.save(p, rng.standard_normal((64, 700)))
    # FAU: 111 / 112 single talker (silent distractors), 123 single talker with a non-silent distractor, 215 / 225 competing with
    # attention swapped (215/distractor = 225/attended, 225/distractor = 215/attended); 112/attended shares 14 s with DTU tX;
    # 215/distractor carries SparrKULee podcast_3's excerpt
    fau = {}
    for code, n in (("111", 6000), ("112", 6000), ("123", 5000), ("215", 6400), ("225", 6400)):
        fau[f"{code}/attended_env/raw"] = raw_env(rng, n, 128).astype(np.float32)
        fau[f"{code}/distractor_env/raw"] = np.full(n, np.nan, np.float32)
    fau["123/distractor_env/raw"] = raw_env(rng, 5000, 128).astype(np.float32)
    dis = raw_env(rng, 6400, 128)
    dis[4000:5920] = e128
    fau["215/distractor_env/raw"] = dis.astype(np.float32)
    fau["225/attended_env/raw"] = fau["215/distractor_env/raw"].copy()
    fau["225/distractor_env/raw"] = fau["215/attended_env/raw"].copy()
    fau_h5 = os.path.join(root, "fau", "stimulus_env_128.h5")
    os.makedirs(os.path.dirname(fau_h5))
    _h5(fau_h5, fau)
    # DTU at 128 Hz: tA..tC NH targets, wA = HI woa twin of tA, tR = tA re-cut 800 samples (128 Hz) later, tX shares FAU 112's excerpt
    tA = raw_env(rng, 2 * 3300, 128)
    dtu = {"tA": tA[:6000], "wA": 0.9 * tA[:6000] + 0.03 * raw_env(rng, 6000, 128), "tR": tA[800:6600].copy(), "tB": raw_env(rng, 6000, 128),
           "tC": raw_env(rng, 6000, 128), "m1": raw_env(rng, 6000, 128)}
    tX = raw_env(rng, 5200, 128)
    tX[1000:1000 + 1792] = fau["112/attended_env/raw"][2000:2000 + 1792]
    dtu["tX"] = tX
    os.makedirs(os.path.join(root, "dtu"))
    _h5(os.path.join(root, "dtu", "audio_local.h5"), {f"{k}/env": v.astype(np.float32) for k, v in dtu.items()})
    inv = []
    for i, (sub, sha, kind, hi) in enumerate([("sub-021", "tA", "target", False), ("sub-022", "tA", "target", False), ("sub-021", "tB", "target", False),
                                              ("sub-022", "tC", "target", False), ("sub-021", "tR", "target", False), ("sub-001", "wA", "target", True),
                                              ("sub-022", "tX", "target", False), ("sub-021", "m1", "masker", False)]):
        inv.append({"file": sub, "trial": f"trial_{i + 1:03d}", "kind": kind, "path": f"/nonexistent/{sub}/{sha}.wav", "offset_s": 0.0, "hi": hi, "sha": sha})
    with open(os.path.join(root, "dtu", "inventory.json"), "w") as f:
        json.dump(inv, f)
    cgd = {"tA": 0, "wA": 0, "tR": 0, "tB": 1, "tC": 2, "tX": 3}
    with open(os.path.join(root, "dtu", "content_groups.json"), "w") as f:
        json.dump({"content": {k: {"group": g, "half": g % 2, "early_stop": False} for k, g in cgd.items()}}, f)
    # Federici at 100 Hz
    items, group = fed_items(rng)
    hear = {("HC", "1001"): ("N1", "N2", "N3", "N4"), ("HC", "1002"): ("N1", "N2", "N3", "N4"), ("CI", "0001"): ("N1", "N4", "N2", "N3"),
            ("HC-v", "1001"): ("V1", "V2", "V3", "V1"), ("Artifact", "0306_bi"): ("N2", "N3", "N1", "N4")}
    pre = os.path.join(root, "federici", "pre")
    for (grp, fid), its in hear.items():
        os.makedirs(os.path.join(pre, grp), exist_ok=True)
        _h5(os.path.join(pre, grp, f"{fid}.h5"), {"env": np.stack([items[i] for i in its]), "eeg": np.zeros((len(its), 2, 10))})
    key = {k: env_key(((v - v.mean()) / (v.std() + 1e-12)).astype(np.float32)) for k, v in items.items()}
    with open(os.path.join(root, "federici", "content_groups.json"), "w") as f:
        json.dump({"items": [{"key": key[k], "group": group[k], "role": "fit", "first": k, "n_listeners": 1} for k in items]}, f)
    cfg = {"sparrkulee": {"root": sk, "envelopes": os.path.join("derivatives", "preprocessed_stimuli"), "fs": 64, "expected_n": len(raws)},
           "fau": {"file": fau_h5, "fs": 128},
           "dtu": {"audio": os.path.join(root, "dtu", "audio_local.h5"), "inventory": os.path.join(root, "dtu", "inventory.json"),
                   "content_groups": os.path.join(root, "dtu", "content_groups.json"), "fs": 128},
           "federici": {"pre": pre, "groups": ["HC", "CI", "HC-v", "Artifact"], "content_groups": os.path.join(root, "federici", "content_groups.json"),
                        "fs": 100}}
    path = os.path.join(root, "sources.json")
    with open(path, "w") as f:
        json.dump(cfg, f)
    return path, key, decoys


_OPENED = []
_AUDIT = {"on": False}


def _audit(event, args):
    if _AUDIT["on"] and event in ("open", "os.listdir", "os.scandir", "glob.glob"):
        _OPENED.append((event, str(args[0]) if args else ""))


sys.addaudithook(_audit)


def _strip(doc):
    return {k: v for k, v in doc.items() if k not in ("created_utc", "elapsed_s")}


def test_cli_end_to_end_resume_and_data_use(tmp_path, capsys):
    cfg, key, decoys = make_tree(tmp_path / "src")
    out = tmp_path / "cache"
    SA.READ_LOG.clear()
    _OPENED.clear()
    _AUDIT["on"] = True
    try:
        rc = SA.main(["--sources", cfg, "--out", str(out), "--workers", "1", "--batch-mb", "64"])
    finally:
        _AUDIT["on"] = False
    assert rc == 0
    doc = json.load(open(out / SA.OUT_NAME))
    assert oct(os.stat(out / SA.OUT_NAME).st_mode & 0o777) == "0o444"
    assert doc["schema"] == SA.SCHEMA and doc["contract"] == C.CONTRACT and doc["ok"] and doc["complete"]
    assert doc["builder"]["sha256"] == SA._file_sha(SA.__file__) and doc["filters"] == C.filter_shas()
    ptr = json.load(open(out / SA.LATEST_NAME))
    assert ptr["status"] == "ok" and ptr["file"] == SA.OUT_NAME and ptr["sha256"] == SA._file_sha(out / SA.OUT_NAME)
    assert ptr["superseded"] is None and ptr["signature"] == doc["signature"] and ptr["builder_sha256"] == doc["builder"]["sha256"]
    assert doc["positive_controls"]["ran"] and doc["positive_controls"]["ok"] and doc["summary"]["positive_controls_ok"]
    # data use: no restricted participant, no preprocessed EEG, no pickle was listed or opened
    touched = [p for _, p in _OPENED] + list(SA.READ_LOG)
    assert touched and not [p for p in touched if "preprocessed_eeg" in p or "sub-019" in p or "sub-020" in p or p.endswith(".data_dict")]
    assert not [p for p in touched if any(os.path.basename(d_) in p for d_ in decoys)]
    assert "audiobook_9_2_envelope-1.npy" in doc["sources"]["sparrkulee"]["ignored"]
    # SparrKULee
    fams = {f["name"]: f for f in doc["families"]["sparrkulee"]}
    offs = {m["stream"]: m["offset"] for m in fams["sparrkulee:audiobook_1"]["members"]}
    assert offs == {"audiobook_1": 0, "audiobook_1_artefact": 0, "audiobook_1_1": 1711, "audiobook_1_1_shifted": 1712,
                    "audiobook_1_2": 30986, "audiobook_1_2_shifted": 30986}          # measured offsets (the copy is declared at 1711)
    assert doc["sparrkulee_audiobook_1"]["ok"] and {r["stream"] for r in doc["shared_audio"]["sparrkulee"]} == {"podcast_1", "podcast_2"}
    # FAU: silent single-talker distractors skipped; 123's distractor observed; 215 / 225 (attention swapped) reported only
    fau = by_sid(doc["streams"]["fau"])
    assert "111/distractor" not in fau and fau["123/distractor"]["keyed"] is False and fau["225/attended"]["keyed"]
    assert {s["stream"] for s in doc["sources"]["fau"]["skipped"]} == {"111/distractor", "112/distractor"}
    assert any("123/distractor" in o for o in doc["observations"])
    for pr in ({"215/distractor", "225/attended"}, {"215/attended", "225/distractor"}):
        rp = [p for p in doc["within"]["fau"]["pairs"] if {p["a"], p["b"]} == pr]
        assert len(rp) == 1 and rp[0]["action"] == "report_only" and rp[0]["b_in_a"] == 0 and rp[0]["coverage"] > 0.99, pr
    assert doc["scene_pairs"] == {"fau": [{"codes": ["215", "225"], "attended_X~distractor_Y": [0], "distractor_X~attended_Y": [0],
                                           "attention_swapped": True, "same_scene": True, "action": "report_only"}]}
    assert doc["summary"]["n_scene_pairs"] == {"fau": 1} and any("attention swapped" in o for o in doc["observations"])
    assert not [s for s in doc["shared_audio"]["fau"]]                    # not masked (CSX: the lead's decision)
    assert all(f["members"][0]["stream"] != "215/distractor" for f in doc["families"]["fau"])
    # DTU: the woa twin and the re-cut copy join tA's family (+0, +400); masker m1 has no family
    f = next(f for f in doc["families"]["dtu"] if "tA" in [m["stream"] for m in f["members"]])
    assert {m["stream"]: m["offset"] for m in f["members"]} == {"tA": 0, "wA": 0, "tR": 400} and f["clock"] == "known"
    assert f["name"] == "dtu:tA" and f["provisional_names"] == ["dtu:tA", "dtu:tR", "dtu:wA"]
    assert {f_["name"] for f_ in doc["families"]["fau"]} == {"fau:111", "fau:112", "fau:123", "fau:215", "fau:225"}
    assert f["content_groups"] == ["0"] and not f["crosses_content_groups"]
    dtu = by_sid(doc["streams"]["dtu"])
    assert dtu["m1"]["family"] is None and dtu["m1"]["kind"] == "masker" and dtu["tR"]["family_offset"] == 400 and dtu["tA"]["kind"] == "attended"
    assert dtu["wA"]["trials_by_hearing"] == {"hi": 1} and dtu["tA"]["n_listeners"] == 2
    assert "sub-02" not in json.dumps(doc["streams"]) and "sub-001" not in json.dumps(doc["streams"])     # counts only, no participant ids
    # Federici: items keyed by env_key, conditions from the listener groups, lags from the +-2 s rule
    fed = by_sid(doc["streams"]["federici"])
    assert set(fed) == set(key.values())
    assert fed[key["V1"]]["condition"] == "vocoded" and fed[key["N1"]]["condition"] == "natural"
    assert fed[key["N1"]]["listener_groups"] == {"Artifact": 1, "CI": 1, "HC": 2} and fed[key["V1"]]["n_listeners"] == 2
    assert fed[key["V1"]]["family_offset"] == 48 and fed[key["V1"]]["offset_known"]
    assert fed[key["V2"]]["offset_known"] is False and fed[key["V3"]]["offset_known"] is False
    assert fed[key["V1"]]["family"] == "federici:g0" and fed[key["N4"]]["family"] == "federici:g3"
    # cross-cohort
    pairs = {(o["a"]["stream"], o["b"]["stream"]): o["b_in_a"] for o in doc["cross_cohort"]["overlaps"]}
    assert pairs == {("112/attended", "tX"): 500, ("podcast_3", "215/distractor"): -1000, ("podcast_3", "225/attended"): -1000}
    assert all(o["lag"] == -o["b_in_a"] and o["refined"] for o in doc["cross_cohort"]["overlaps"])
    ex = doc["cross_cohort"]["donor_exclusions"]
    assert ex["fau"]["dtu"] == ["tX"] and ex["dtu"]["fau"] == ["112/attended"] and ex["fau"]["sparrkulee"] == ["podcast_3"]
    assert ex == doc["cross_cohort"]["donor_exclusions_direct"]          # tX, podcast_3 and the FAU streams are one-member families
    assert all(c["ok"] for c in doc["checks"] if c["level"] == "assert")
    assert doc["checks"][-1]["check"] == SA.PROVISIONAL_CHECK and not [c for c in doc["checks"] if c["check"] == SA.COMPLETE_CHECK]
    warns = {c["check"] for c in doc["checks"] if c["level"] == "warn" and not c["ok"]}
    assert warns == {"no SparrKULee stream flagged against another cohort (a flagged dev / bridge_cal stream makes the shared dev / "
                     "bridge_cal definition target-specific: C6 checks the roles)"}               # podcast_3 is planted
    # resume: an existing output is left alone; --force reuses every unit and reproduces the document
    capsys.readouterr()
    assert SA.main(["--sources", cfg, "--out", str(out)]) == 0
    assert "exists and is current; nothing to do" in capsys.readouterr().out
    assert SA.main(["--sources", cfg, "--out", str(out), "--force", "--batch-mb", "64"]) == 0
    log = capsys.readouterr().out
    assert " unit " not in log
    doc2 = json.load(open(out / SA.OUT_NAME))
    assert _strip(doc2) == _strip(doc)
    # a corrupted unit is recomputed, with the same result
    work = out / SA.WORK_NAME / doc["signature"][:16]
    units = sorted(work.glob("within__sparrkulee__sparrkulee__*.npz"))
    assert units
    units[0].write_bytes(b"truncated")
    assert SA.main(["--sources", cfg, "--out", str(out), "--force"]) == 0
    assert "within sparrkulee->sparrkulee unit 1/1" in capsys.readouterr().out
    assert _strip(json.load(open(out / SA.OUT_NAME))) == _strip(doc)


def test_cli_failed_assertion_writes_failed_file(tmp_path):
    cfg, _, _ = make_tree(tmp_path / "src", o2=30990)
    out = tmp_path / "cache"
    assert SA.main(["--sources", cfg, "--out", str(out)]) == 3
    assert not (out / SA.OUT_NAME).exists()
    bad = json.load(open(out / SA.FAILED_NAME))
    assert bad["ok"] is False and not bad["sparrkulee_audiobook_1"]["ok"]
    assert [c["detail"] for c in bad["checks"] if c["level"] == "assert" and not c["ok"]] == \
        [{"expected": 30986, "measured": 30990}, {"expected": 30986, "measured": 30990, "declared_as": "audiobook_1_2"}]
    # the window scan itself is healthy (its positive controls use the measured offsets); the pointer names the FAILED file
    assert bad["positive_controls"]["ok"]
    ptr = json.load(open(out / SA.LATEST_NAME))
    assert ptr["status"] == "failed" and ptr["file"] == SA.FAILED_NAME and ptr["stale"] is None
    assert ptr["sha256"] == SA._file_sha(out / SA.FAILED_NAME) and oct(os.stat(out / SA.LATEST_NAME).st_mode & 0o777) == "0o444"


def test_cli_latest_pointer_supersedes_and_marks_stale(tmp_path, monkeypatch, capsys):
    """Review M2c problem 7: scan_audio.latest.json always names the latest run's result. A success after a failure supersedes the
    FAILED file; a failed --force rerun marks the older scan_audio.json stale; a stale or foreign-builder scan_audio.json is never
    reused without --force (exit 4). Nothing is moved or deleted."""
    bad_cfg, _, _ = make_tree(tmp_path / "bad", o2=30990)
    good_cfg, _, _ = make_tree(tmp_path / "good")
    out = tmp_path / "cache"
    ptr = lambda: json.load(open(out / SA.LATEST_NAME))                                  # noqa: E731
    assert SA.main(["--sources", bad_cfg, "--out", str(out)]) == SA.EXIT_FAILED
    failed_sha = SA._file_sha(out / SA.FAILED_NAME)
    assert SA.main(["--sources", good_cfg, "--out", str(out)]) == SA.EXIT_OK
    p = ptr()
    assert p["status"] == "ok" and p["sha256"] == SA._file_sha(out / SA.OUT_NAME)
    assert p["superseded"]["file"] == SA.FAILED_NAME and p["superseded"]["sha256"] == failed_sha and p["superseded"]["ok"] is False
    assert (out / SA.FAILED_NAME).exists() and SA.not_current(str(out)) == []
    ok_sha = SA._file_sha(out / SA.OUT_NAME)
    capsys.readouterr()
    assert SA.main(["--sources", good_cfg, "--out", str(out)]) == SA.EXIT_OK and "nothing to do" in capsys.readouterr().out
    # a failed --force rerun: the older scan_audio.json stays in place, the pointer marks it stale, nothing reuses it any more
    assert SA.main(["--sources", bad_cfg, "--out", str(out), "--force"]) == SA.EXIT_FAILED
    p = ptr()
    assert p["status"] == "failed" and p["file"] == SA.FAILED_NAME and p["stale"]["sha256"] == ok_sha
    assert SA._file_sha(out / SA.OUT_NAME) == ok_sha and "STALE" in capsys.readouterr().out
    assert SA.main(["--sources", good_cfg, "--out", str(out)]) == SA.EXIT_NOT_CURRENT
    assert "not current" in capsys.readouterr().out and SA._file_sha(out / SA.OUT_NAME) == ok_sha
    assert SA.main(["--sources", good_cfg, "--out", str(out), "--force"]) == SA.EXIT_OK and ptr()["status"] == "ok"
    # a scan_audio.json written by another builder version is not reused without --force either
    monkeypatch.setattr(SA, "builder_sha", lambda: "0" * 64)
    why = SA.not_current(str(out))
    assert len(why) == 1 and "builder" in why[0]
    assert SA.main(["--sources", good_cfg, "--out", str(out)]) == SA.EXIT_NOT_CURRENT


def test_cli_out_root_guard(tmp_path):
    _OPENED.clear()
    SA.READ_LOG.clear()
    _AUDIT["on"] = True
    try:
        with pytest.raises(SystemExit):                     # real sources: only the design cache root
            SA.main(["--out", str(tmp_path / "elsewhere")])
    finally:
        _AUDIT["on"] = False
    assert not SA.READ_LOG and not [p for _, p in _OPENED if p.startswith(SA.PUB)]
    cfg, _, _ = make_tree(tmp_path / "src")
    for bad in (SA.CACHE_ROOT, os.path.join(SA.PUB, "derived", "x"), os.path.join(SA.REPO, "results", "x"), os.path.join(SA.REPO, "private", "x")):
        with pytest.raises(SystemExit):
            SA.main(["--sources", cfg, "--out", bad])
    assert SA._check_out(SA.CACHE_ROOT, True) == os.path.realpath(SA.CACHE_ROOT)


# ------------------------------------------------------------------------------------------------ second review of M2c
def test_source_sha256_follows_the_m1_rule(tmp_path):
    """Review 2 of M2c, item 2: source_sha256 follows the M1 / M2b rule (fixtures.py 'Source hashes'; build_public.py hashes
    np.asarray(raw, float64) the same way). An array inside a container (FAU / DTU h5 dataset, Federici block row) hashes the C-order
    float64 bytes of the flattened array as read, before nan_to_num, whatever its stored dtype, byte order or shape; a SparrKULee
    envelope file hashes its bytes. M2c hashed the stored float32 bytes of the FAU and DTU datasets."""
    import hashlib
    import h5py
    from auditory_alignment.federici_content import env_key
    from fixtures import array_sha256
    x = np.random.default_rng(41).standard_normal(301)
    x[[3, 77]] = np.nan
    x32 = x.astype(np.float32)
    for a in (x, x32, x32.astype(">f4"), x.astype(">f8"), x32[:, None], x[::2], np.asfortranarray(np.stack([x, -x], 1)),
              x32.astype(np.float16), np.arange(7, dtype=np.int16)):
        assert SA._sha_arr(a) == array_sha256(a), (a.dtype, a.shape)
    assert SA._sha_arr(x32) == SA._sha_arr(x32.astype(">f4")) == SA._sha_arr(x32[:, None]) == array_sha256(x32.astype(np.float64))
    assert SA._sha_arr(x32) != hashlib.sha256(x32.tobytes()).hexdigest()              # the stored-dtype hash of M2c
    # every stream the loaders read from the synthetic tree (float32 FAU / DTU datasets, float64 Federici rows, SparrKULee .npy)
    cfg_path, _, _ = make_tree(tmp_path / "src")
    cfg = json.load(open(cfg_path))
    streams, _ = SA.load_sources(cfg)
    assert all(streams[c] for c in SA.COHORTS)
    with h5py.File(cfg["fau"]["file"], "r") as f:
        for s in streams["fau"]:
            raw = f[f"{s.sid}_env/raw"][()]
            assert raw.dtype == np.float32 and s.meta["source_sha256"] == array_sha256(raw), s.sid
    with h5py.File(cfg["dtu"]["audio"], "r") as f:
        for s in streams["dtu"]:
            raw = f[f"{s.sid}/env"][()]
            assert raw.dtype == np.float32 and s.meta["source_sha256"] == array_sha256(raw), s.sid
    first = {}
    for grp in cfg["federici"]["groups"]:
        for p in sorted(glob.glob(os.path.join(cfg["federici"]["pre"], grp, "*.h5"))):
            with h5py.File(p, "r") as f:
                for e in np.asarray(f["env"][()], dtype=np.float64):
                    first.setdefault(env_key(((e - e.mean()) / (e.std() + 1e-12)).astype(np.float32)), e)
    assert {s.sid for s in streams["federici"]} == set(first)
    for s in streams["federici"]:
        assert s.meta["source_sha256"] == array_sha256(first[s.sid]), s.sid
    d = os.path.join(cfg["sparrkulee"]["root"], cfg["sparrkulee"]["envelopes"])
    for s in streams["sparrkulee"]:
        assert s.meta["source_sha256"] == SA._file_sha(os.path.join(d, f"{s.sid}_envelope.npy")), s.sid
    # item 4 (documented): one masker stream under its bare sha, hashed from its <sha>/env array, which is also the array every C5
    # placement '<sha>@<offset_s>' of it hashes (build_public.py: the masker's raw <sha>/env)
    m1 = {s.sid: s for s in streams["dtu"]}["m1"]
    assert m1.kind == "masker" and not m1.keyed and m1.meta["source"]["dataset"] == "m1/env"
    assert "'<sha>@<offset_s>'" in SA.__doc__ and "placement.masker_sha" in SA.__doc__


def _empty_cohort(cfg, cohort, d):
    """Make `cohort` of a make_tree source config yield no stream, the way each loader can come up empty: SparrKULee an envelope
    directory without *_envelope.npy, FAU a stimulus h5 whose streams are all silent, DTU an inventory without shas, Federici no
    listener file in the configured groups."""
    os.makedirs(d, exist_ok=True)
    if cohort == "sparrkulee":
        os.makedirs(os.path.join(cfg["sparrkulee"]["root"], "derivatives", "no_stimuli"), exist_ok=True)
        cfg["sparrkulee"]["envelopes"] = os.path.join("derivatives", "no_stimuli")
    elif cohort == "fau":
        cfg["fau"]["file"] = os.path.join(d, "stimulus_env_128_silent.h5")
        _h5(cfg["fau"]["file"], {f"111/{w}_env/raw": np.full(640, np.nan, np.float32) for w in ("attended", "distractor")})
    elif cohort == "dtu":
        cfg["dtu"]["inventory"] = os.path.join(d, "inventory_empty.json")
        with open(cfg["dtu"]["inventory"], "w") as f:
            json.dump([], f)
    else:
        cfg["federici"]["groups"] = ["no_such_group"]
    return cfg


@pytest.mark.parametrize("cohort", SA.COHORTS)
def test_real_sources_fail_when_a_cohort_yields_no_stream(tmp_path, monkeypatch, cohort):
    """Review 2 of M2c, item 1: on the real-source path (run(require_all=True), i.e. main without --sources) every cohort must yield
    streams. A cohort that yields none fails the run before any scan, with an error naming it: exit 3, scan_audio.FAILED.json with
    complete false, empty_cohorts and the failed COMPLETE_CHECK, the pointer says failed, no scan_audio.json and no work unit. M2c
    scanned the other cohorts, left the empty one out of donor_exclusions and exited 0."""
    cfg_path, _, _ = make_tree(tmp_path / "src")
    cfg = _empty_cohort(json.load(open(cfg_path)), cohort, tmp_path / "empty")
    monkeypatch.setattr(SA, "scan", lambda *a, **k: pytest.fail("no scan may run on incomplete real sources"))
    out, logs = tmp_path / "cache", []
    assert SA.run(cfg, str(out), require_all=True, log=logs.append) == SA.EXIT_FAILED
    assert not (out / SA.OUT_NAME).exists() and not (out / SA.WORK_NAME).exists()
    doc = json.load(open(out / SA.FAILED_NAME))
    assert doc["ok"] is False and doc["complete"] is False and doc["empty_cohorts"] == [cohort]
    assert f"incomplete sources: required cohort(s) {cohort} yielded no keyed streams" in doc["error"]
    assert any(m.startswith("[scan_audio] FAILED: incomplete sources") and cohort in m for m in logs)
    assert doc["n_streams"][cohort] == 0 and all(doc["n_streams"][c] > 0 for c in SA.COHORTS if c != cohort)
    assert doc["n_keyed"][cohort] == 0 and all(doc["n_keyed"][c] > 0 for c in SA.COHORTS if c != cohort)
    (chk,) = doc["checks"]
    assert (chk["check"], chk["level"], chk["ok"], list(chk["detail"]["empty"])) == (SA.COMPLETE_CHECK, "assert", False, [cohort])
    why = chk["detail"]["empty"][cohort]
    want = {"sparrkulee": {"n_files": 0, "failed_source_checks": ["sparrkulee envelope files"]},
            "fau": {"n_skipped": 2, "skip_reasons": {"silent (all NaN or zero)": 2}},
            "dtu": {"n_inventory_rows": 0, "n_shas": 0}, "federici": {"n_files": 0, "n_items": 0}}[cohort]
    assert why["configured"] and {k: why[k] for k in want} == want, why
    assert (why["n_streams"], why["n_keyed"], why["stream_kinds"]) == (0, 0, {})
    ptr = json.load(open(out / SA.LATEST_NAME))
    assert ptr["status"] == "failed" and ptr["file"] == SA.FAILED_NAME and ptr["sha256"] == SA._file_sha(out / SA.FAILED_NAME)


def test_real_sources_assert_complete(tmp_path):
    """Review 2 of M2c, item 1: a complete run on the real-source path records the asserted COMPLETE_CHECK (complete true, every
    donor cohort in donor_exclusions); two empty cohorts are both named, in COHORTS order; a --sources subset (synthetic trees,
    tests) is not asserted and says complete false."""
    cfg_path, _, _ = make_tree(tmp_path / "src")
    cfg = json.load(open(cfg_path))
    out = tmp_path / "real"
    assert SA.run(cfg, str(out), require_all=True, log=lambda m: None) == SA.EXIT_OK
    doc = json.load(open(out / SA.OUT_NAME))
    chk = [c for c in doc["checks"] if c["check"] == SA.COMPLETE_CHECK]
    assert doc["ok"] and doc["complete"] is True and len(chk) == 1 and chk[0]["ok"] and chk[0]["level"] == "assert"
    assert chk[0]["detail"]["cohorts_scanned"] == doc["cohorts_scanned"] == list(SA.COHORTS)
    assert min(chk[0]["detail"]["n_streams"].values()) > 0 and min(chk[0]["detail"]["n_keyed"].values()) > 0
    assert all(set(v) == set(SA.DONOR_SETS[t]) for t, v in doc["cross_cohort"]["donor_exclusions"].items())
    # the checks new in the second review come after every check M2c had: scan()'s PROVISIONAL_CHECK, then the run-level ones
    assert [c["check"] for c in doc["checks"][-3:]] == [SA.PROVISIONAL_CHECK, "positive controls ran (real sources)", SA.COMPLETE_CHECK]
    for c in ("federici", "dtu"):
        _empty_cohort(cfg, c, tmp_path / "empty")
    out = tmp_path / "two"
    assert SA.run(cfg, str(out), require_all=True, log=lambda m: None) == SA.EXIT_FAILED
    doc = json.load(open(out / SA.FAILED_NAME))
    assert doc["empty_cohorts"] == ["dtu", "federici"] and "required cohort(s) dtu, federici yielded no keyed streams" in doc["error"]
    # the same sources as a --sources subset: allowed, not asserted, but never reported complete
    out = tmp_path / "subset"
    assert SA.run(cfg, str(out), log=lambda m: None) == SA.EXIT_OK
    doc = json.load(open(out / SA.OUT_NAME))
    assert doc["ok"] and doc["complete"] is False and doc["cohorts_scanned"] == ["sparrkulee", "fau"]
    assert not [c for c in doc["checks"] if c["check"] == SA.COMPLETE_CHECK]
    assert set(doc["cross_cohort"]["donor_exclusions"]["fau"]) == {"sparrkulee"}


def _non_keyed_cohort(cfg, cohort, d):
    """Make `cohort` of a make_tree source config yield streams none of which is keyed: FAU a stimulus h5 whose attended streams
    are all silent while 123's distractor is audible, DTU an inventory in which every row is a masker."""
    os.makedirs(d, exist_ok=True)
    if cohort == "fau":
        cfg["fau"]["file"] = os.path.join(d, "stimulus_env_128_distractor_only.h5")
        _h5(cfg["fau"]["file"], {"111/attended_env/raw": np.full(640, np.nan, np.float32), "111/distractor_env/raw": np.full(640, np.nan, np.float32),
                                 "123/attended_env/raw": np.full(5000, np.nan, np.float32),
                                 "123/distractor_env/raw": raw_env(np.random.default_rng(5), 5000, 128).astype(np.float32)})
    else:
        rows = json.load(open(cfg["dtu"]["inventory"]))
        cfg["dtu"]["inventory"] = os.path.join(d, "inventory_maskers_only.json")
        with open(cfg["dtu"]["inventory"], "w") as f:
            json.dump([{**r, "kind": "masker"} for r in rows], f)
    return cfg


@pytest.mark.parametrize("cohort", ("fau", "dtu"))
def test_real_sources_fail_when_a_cohort_yields_only_non_keyed_streams(tmp_path, monkeypatch, cohort):
    """Review 3 of M2c, P2: completeness counts keyed streams. A cohort whose streams are all non-keyed (FAU distractors, DTU
    maskers) has no family and no donor content: on the real-source path it fails before any scan like an empty cohort (review 2
    counted any stream: 0 families, exit 0, complete true). A --sources run still scans it (any heard audio counts for the
    cross-cohort flags) but never reports complete."""
    cfg_path, _, _ = make_tree(tmp_path / "src")
    cfg = _non_keyed_cohort(json.load(open(cfg_path)), cohort, tmp_path / "non_keyed")
    out = tmp_path / "subset"
    assert SA.run(cfg, str(out), log=lambda m: None) == SA.EXIT_OK
    doc = json.load(open(out / SA.OUT_NAME))
    assert doc["ok"] and doc["complete"] is False and doc["cohorts_scanned"] == list(SA.COHORTS)
    assert doc["streams"][cohort] and not any(s["keyed"] for s in doc["streams"][cohort]) and doc["families"][cohort] == []
    monkeypatch.setattr(SA, "scan", lambda *a, **k: pytest.fail("no scan may run on incomplete real sources"))
    out = tmp_path / "real"
    assert SA.run(cfg, str(out), require_all=True, log=lambda m: None) == SA.EXIT_FAILED
    assert not (out / SA.OUT_NAME).exists() and not (out / SA.WORK_NAME).exists()
    doc = json.load(open(out / SA.FAILED_NAME))
    kinds = {"fau": {"distractor": 1}, "dtu": {"masker": 7}}[cohort]
    assert doc["ok"] is False and doc["complete"] is False and doc["empty_cohorts"] == [cohort]
    assert f"incomplete sources: required cohort(s) {cohort} yielded no keyed streams" in doc["error"]
    assert doc["n_streams"][cohort] == sum(kinds.values()) and doc["n_keyed"][cohort] == 0
    assert all(doc["n_keyed"][c] > 0 for c in SA.COHORTS if c != cohort)
    (chk,) = doc["checks"]
    why = chk["detail"]["empty"][cohort]
    assert (chk["check"], chk["level"], chk["ok"]) == (SA.COMPLETE_CHECK, "assert", False) and why["configured"]
    assert (why["n_streams"], why["n_keyed"], why["stream_kinds"]) == (sum(kinds.values()), 0, kinds), why
    assert json.load(open(out / SA.LATEST_NAME))["status"] == "failed"


def test_real_sources_refuse_a_cohort_missing_from_the_config(tmp_path, monkeypatch):
    """Review 3 of M2c, P3: on the real-source path a cohort missing from the config is refused before anything is read, with the
    FAILED file of an empty cohort: complete false, empty_cohorts, the failed COMPLETE_CHECK and an error naming the cohort (review
    2's file had neither complete nor empty_cohorts). Unknown keys stay a plain config error on both paths."""
    cfg_path, _, _ = make_tree(tmp_path / "src")
    cfg, src = json.load(open(cfg_path)), str(tmp_path / "src")
    monkeypatch.setattr(SA, "scan", lambda *a, **k: pytest.fail("no scan may run on incomplete real sources"))
    for drop in (["dtu"], ["fau", "federici"]):
        out = tmp_path / ("real_" + "_".join(drop))
        SA.READ_LOG.clear()
        _OPENED.clear()
        _AUDIT["on"] = True
        try:
            rc = SA.run({k: v for k, v in cfg.items() if k not in drop}, str(out), require_all=True, log=lambda m: None)
        finally:
            _AUDIT["on"] = False
        assert rc == SA.EXIT_FAILED
        assert not SA.READ_LOG and not [p for _, p in _OPENED if p.startswith(src)]           # refused before anything is read
        doc = json.load(open(out / SA.FAILED_NAME))
        assert doc["ok"] is False and doc["complete"] is False and doc["empty_cohorts"] == drop
        assert f"incomplete sources: required cohort(s) {', '.join(drop)} not configured" in doc["error"]
        (chk,) = doc["checks"]
        assert (chk["check"], chk["level"], chk["ok"]) == (SA.COMPLETE_CHECK, "assert", False)
        assert chk["detail"]["empty"] == {c: {"configured": False} for c in drop}
        assert json.load(open(out / SA.LATEST_NAME))["status"] == "failed" and not (out / SA.OUT_NAME).exists()
    for require_all in (True, False):
        out = tmp_path / f"unknown_{require_all}"
        assert SA.run({**cfg, "private_bdf": {}}, str(out), require_all=require_all, log=lambda m: None) == SA.EXIT_FAILED
        doc = json.load(open(out / SA.FAILED_NAME))
        assert "unknown keys ['private_bdf']" in doc["error"] and "complete" not in doc and "empty_cohorts" not in doc


def _break_source(cfg, cohort, what, d):
    """Make one configured source of a make_tree config unreadable -> (cfg, exception type, a substring of its message)."""
    os.makedirs(d, exist_ok=True)
    if what == "env dataset":                                   # a Federici listener file without its `env` block
        os.makedirs(os.path.join(cfg["federici"]["pre"], "Broken"))
        _h5(os.path.join(cfg["federici"]["pre"], "Broken", "9999.h5"), {"eeg": np.zeros((1, 2, 10))})
        cfg["federici"]["groups"] = [*cfg["federici"]["groups"], "Broken"]
        return cfg, "KeyError", "env"
    key = {"envelope dir": "envelopes", "h5": "file", "inventory": "inventory", "audio h5": "audio", "content groups": "content_groups"}[what]
    name = "no_such_" + os.path.basename(cfg[cohort][key])
    cfg[cohort][key] = os.path.join("derivatives", name) if key == "envelopes" else os.path.join(d, name)
    return cfg, "FileNotFoundError", name


@pytest.mark.parametrize("cohort,what", [("sparrkulee", "envelope dir"), ("fau", "h5"), ("dtu", "inventory"), ("dtu", "audio h5"),
                                         ("federici", "content groups"), ("federici", "env dataset")])
def test_unreadable_source_fails_with_exit_3(tmp_path, monkeypatch, cohort, what):
    """Review 3 of M2c, P4: a configured source that a loader cannot read (a missing file or directory, a missing dataset) fails the
    run with exit 3 on both paths: scan_audio.FAILED.json with complete false and source_error naming the cohort, the pointer says
    failed, nothing is scanned. Before, FileNotFoundError / KeyError escaped run() (traceback, exit 1, no FAILED file, the pointer
    not updated)."""
    cfg_path, _, _ = make_tree(tmp_path / "src")
    cfg, exc_type, needle = _break_source(json.load(open(cfg_path)), cohort, what, tmp_path / "broken")
    monkeypatch.setattr(SA, "scan", lambda *a, **k: pytest.fail("no scan may run on an unreadable source"))
    for require_all in (True, False):
        out, logs = tmp_path / f"out_{require_all}", []
        assert SA.run(cfg, str(out), require_all=require_all, log=logs.append) == SA.EXIT_FAILED
        assert not (out / SA.OUT_NAME).exists() and not (out / SA.WORK_NAME).exists()
        doc = json.load(open(out / SA.FAILED_NAME))
        err = doc["source_error"]
        assert doc["ok"] is False and doc["complete"] is False and (err["cohort"], err["type"], err["config"]) == (cohort, exc_type, cfg[cohort])
        assert doc["error"].startswith(f"source {cohort}: cannot read the configured source ({exc_type}: ") and needle in err["error"], doc["error"]
        assert any(m.startswith(f"[scan_audio] FAILED: source {cohort}: cannot read") for m in logs)
        ptr = json.load(open(out / SA.LATEST_NAME))
        assert ptr["status"] == "failed" and ptr["file"] == SA.FAILED_NAME and ptr["sha256"] == SA._file_sha(out / SA.FAILED_NAME)


def test_restricted_source_config_propagates_and_writes_nothing(tmp_path):
    """A data-use refusal is not an unreadable source: a config that points into a restricted SparrKULee participant raises
    RestrictedAccess out of run() before that directory is listed, and no result file or pointer is written."""
    cfg_path, _, _ = make_tree(tmp_path / "src")
    cfg = json.load(open(cfg_path))
    cfg["sparrkulee"]["envelopes"] = os.path.join("derivatives", "preprocessed_eeg", "sub-019")
    out = tmp_path / "cache"
    _OPENED.clear()
    _AUDIT["on"] = True
    try:
        with pytest.raises(SA.RestrictedAccess):
            SA.run(cfg, str(out), require_all=True, log=lambda m: None)
    finally:
        _AUDIT["on"] = False
    assert not [p for _, p in _OPENED if "sub-019" in p] and os.listdir(out) == []


# ------------------------------------------------------------------------------------------------ the M1 fixture (consistency)
def test_scan_reproduces_m1_fixture_structure(tmp_path):
    """C3 on the M1 fixture's envelopes: the DTU re-cut duplicate (+400), the Federici known lag (+48) and unknown clock, the FAU 122 /
    DTU t05 excerpt and the audiobook_1 relations are recovered. The fixture's 3 s jingle is shorter than the 10 s detection window
    of §3.4, so C3 cannot reproduce the fixture's shared_audio spans (M2e must not expect them from C3)."""
    from fixtures import make_synthetic_manifest
    fx = make_synthetic_manifest(tmp_path / "fx")
    man = fx["manifest"]
    fam_name = {f["id"]: f["name"] for f in man["families"]}
    streams, name_of = {}, {}
    for c in SA.COHORTS:
        info = man["cohorts"][c]
        env = np.load(os.path.join(fx["root"], info["dir"], info["env"]), allow_pickle=False)
        rows = json.load(open(os.path.join(fx["root"], info["dir"], info["streams"])))["streams"]
        name_of[c] = {r["stream"]: r["name"] for r in rows}
        S = []
        for r in rows:
            x = env[r["offset"]:r["offset"] + r["length"]].astype(np.float64)
            keyed = r["kind"] in ("attended", "item")
            meta = {}
            if c == "federici":
                g = fam_name[r["family"]]
                meta = {"content_group": g if g.startswith("g") else None, "condition": "vocoded" if r["name"].startswith("V") else "natural",
                        "n_listeners": 3}
            S.append(SA.Stream(c, r["name"], r["kind"], keyed, x, meta))
        streams[c] = sorted(S, key=lambda s: s.sid)
    res = SA.scan(streams, sk_declared_spec=None)
    t = fx["truth"]
    f, m = family_of(res, "dtu", "t07")
    assert {mm["stream"]: mm["offset"] for mm in f["members"]} == {"t01": 0, "t07": t["family_offset"]["dtu:t07"]}
    assert family_of(res, "federici", "V1")[1]["offset"] == t["family_offset"]["federici:V1"] == 48
    assert family_of(res, "federici", "V2")[0]["clock"] == "unknown"
    o = [o for o in res["cross_cohort"]["overlaps"] if (o["a"]["stream"], o["b"]["stream"]) == ("122/attended", "t05")]
    assert len(o) == 1 and o[0]["b_in_a"] == (256 - 640) // 2          # FAU 122 64 Hz sample 128 = DTU t05 sample 320
    # the record's lag has the sign of manifest.overlap (b span start - a span start = +192), opposite to b_in_a
    mo = man["overlap"][0]
    assert (mo["a"]["cohort"], mo["a"]["stimulus"], mo["b"]["cohort"], mo["b"]["stimulus"]) == ("fau", "122", "dtu", "t05")
    assert o[0]["lag"] == mo["lag"] == 192 and (o[0]["a"]["stimulus"], o[0]["b"]["stimulus"]) == ("122", "t05")
    assert res["cross_cohort"]["donor_exclusions"]["fau"]["dtu"] == ["t05"] and res["cross_cohort"]["donor_exclusions"]["dtu"]["fau"] == ["122/attended"]
    # the C6 rule (remove a donor presentation whose attended OR ignored stream is listed) reproduces every fixture exclusion list
    # (the fixture maps through the attended stream only; the two agree here because no planted overlap involves an ignored stream)
    ex, n_lists, n_ids = res["cross_cohort"]["donor_exclusions"], 0, 0
    for target, blocks in man["donor_sets"].items():
        for blk, v in blocks.items():
            for stratum, want in v["excluded_presentations"].items():
                c = "fau" if stratum == "fau_cs" else stratum
                listed = set(ex[target].get(c, []))
                got = sorted(p["id"] for p in man["presentations"] if p["cohort"] == c and
                             (name_of[c].get(p["stream"]) in listed or name_of[c].get(p["ignored_stream"]) in listed))
                assert got == sorted(want), (target, blk, stratum, got, want)
                n_lists, n_ids = n_lists + 1, n_ids + len(want)
    assert n_lists >= 4 and n_ids >= 2
    sk_off = {s: t["family_offset"][f"sparrkulee:{s}"] for s in ("audiobook_1_1", "audiobook_1_shifted", "audiobook_1_artefact")}
    f, _ = family_of(res, "sparrkulee", "audiobook_1_1")
    rel = {mm["stream"]: mm["offset"] for mm in f["members"]}
    assert set(rel) == set(sk_off) and all(rel[s] - rel["audiobook_1_1"] == sk_off[s] - sk_off["audiobook_1_1"] for s in sk_off)
    assert res["shared_audio"]["sparrkulee"] == []          # fixture jingle 3 s < 10 s window: not detectable by the §3.4 rule


def test_default_sources_are_the_loaders_paths():
    """The real sources are where auditory_alignment/data.py, prep_targets.py and federici_content.py read them (§2.3); nothing is read."""
    from auditory_alignment import data as D, prep_targets as PT
    from auditory_alignment.federici_content import OUT
    SA.READ_LOG.clear()
    cfg = SA.default_sources()
    assert not SA.READ_LOG and set(cfg) == set(SA.COHORTS)
    assert cfg["sparrkulee"]["root"] == SA.SK_ROOT_REAL and cfg["sparrkulee"]["expected_n"] == 72 and cfg["sparrkulee"]["fs"] == 64
    assert cfg["fau"] == {"file": PT.FAU_ENV, "fs": 128}
    assert cfg["dtu"]["audio"] == os.path.join(D.DTU_KCS, "audio_local.h5") and cfg["dtu"]["inventory"] == os.path.join(PT.DTU_FEAT, "inventory.json")
    assert cfg["federici"]["pre"] == D.FED_PRE and cfg["federici"]["content_groups"] == os.path.join(OUT, "content_groups.json")
    assert SA.CACHE_ROOT == os.path.join(SA.PUB, "derived", "aln33_env64_125ms_v1")
    with pytest.raises(SA.ScanError):                       # refused before anything is read
        SA.load_sources({k: v for k, v in cfg.items() if k != "dtu"}, require_all=True)
    with pytest.raises(SA.ScanError):
        SA.load_sources({**cfg, "private_bdf": {}})
    assert not SA.READ_LOG
