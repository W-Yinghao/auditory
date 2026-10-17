"""R34_DADAPT_R synthetic checks of auditory_alignment_v3.aln34.dadapt_r: the R capture (same four fields as run_adapt3._gain plus the
true / mismatched logloss of the same _metrics calls; reaches the runner's nested evaluate_query; always restored), the ss_only loaders
against the original FAU / DTU loaders on synthetic HDF5 files (identical single-speaker segments, float16 EEG and stimulus windows),
execution ids and seeds, the scope, the reproduction QC rules of the analysis note, the claim-based worker loop (idempotence, claims,
failure records, shards), the aggregation (signs, decomposition, identity mean over seeds, missing pairs, QC admission, panel families
equal to d_multiseed's) and the document splice. No unit record or real EEG is read; one test reads the plan rows only.
Addendum 2 of the note: content-fold-matched pairs incl. the verifier's partial-pair case on either side (C1); array-element claims in
both squeue id forms and owner-checked release (C2); identity-free public outputs and QC problem kinds (C3); protected write targets
(C4); the value-path hash and the pinned evaluator hash (C5)."""
import inspect
import json
import os

import numpy as np
import pytest

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import d_lag_interim as DL
from auditory_alignment_v3.aln34 import dadapt_r as DR


# ------------------------------------------------------------------------------------------------ R capture
def _scores(rng, nq=17, nc=23):
    s_true = rng.standard_normal((nq, nc)); s_mm = rng.standard_normal((nq, nc))
    own = rng.integers(0, nc, nq)
    return s_true, s_mm, own


def test_gain_with_risk_matches_runner_gain():
    from auditory_alignment import evaluate as ev1
    from auditory_alignment_v3 import run_adapt3 as RA
    rng = np.random.default_rng(0)
    for tau in (0.05, 0.3, 2.0):
        s_true, s_mm, own = _scores(rng)
        ref = RA._gain(s_true, s_mm, own, tau)
        new = DR.gain_with_risk(s_true, s_mm, own, tau)
        assert set(ref) == set(DR.ORIGINAL_FIELDS)
        for k in ref:
            assert new[k] == ref[k]  # same computation, bit for bit
        a, b = ev1._metrics(s_true, own, tau), ev1._metrics(s_mm, own, tau)
        assert new["logloss_bits"] == a["logloss_bits"] and new["mismatched_logloss_bits"] == b["logloss_bits"]
        assert new["gain_bits"] == new["mismatched_logloss_bits"] - new["logloss_bits"]
        assert new["n_candidates"] == s_true.shape[1] and new["tau"] == tau
        assert new["top5"] == a["top5"] and new["mrr"] == a["mrr"]
        assert set(new) == set(DR.ORIGINAL_FIELDS) | set(DR.EXTRA_FIELDS)


def test_risk_capture_restores_even_on_error():
    from auditory_alignment_v3 import run_adapt3 as RA
    orig = RA._gain
    with DR.risk_capture():
        assert RA._gain is DR.gain_with_risk
    assert RA._gain is orig
    with pytest.raises(RuntimeError):
        with DR.risk_capture():
            raise RuntimeError("x")
    assert RA._gain is orig


def test_runner_looks_up_gain_globally():
    """bundle's nested evaluate_query resolves _gain from the module globals at call time, so risk_capture reaches it."""
    from auditory_alignment_v3 import run_adapt3 as RA
    assert "_gain" not in RA.bundle.__code__.co_varnames
    nested = [c for c in RA.bundle.__code__.co_consts if inspect.iscode(c) and c.co_name == "evaluate_query"]
    assert len(nested) == 1 and "_gain" in nested[0].co_names
    assert "_gain(ro.scores(Uq, Vc, Ac, kr), ro.scores(Umm, Vc, Ac, kr), own, ro.tau[kr])" in inspect.getsource(RA.bundle)


def test_loader_scope():
    from auditory_alignment_v2 import run as V2R
    orig = V2R.load_cohort
    with DR.loader_scope("original"):
        assert V2R.load_cohort is orig
    with DR.loader_scope("ss_only"):
        assert V2R.load_cohort is DR.load_cohort_ss_only
    assert V2R.load_cohort is orig
    with pytest.raises(ValueError):
        with DR.loader_scope("other"):
            pass
    from auditory_alignment_v3 import run_adapt3 as RA
    assert "from auditory_alignment_v2.run import load_cohort" in inspect.getsource(RA.bundle)  # imported at call time


# ------------------------------------------------------------------------------------------------ ss_only loaders vs the originals
def _h5():
    return pytest.importorskip("h5py")


def _fau_fixture(tmp, rng):
    h5py = _h5()
    stage = tmp / "stageB"; kcs = tmp / "kcs"; kcs.mkdir()
    people = {"th": ["d1", "d2"], "ha": ["h1"], "ci": ["c1"]}
    codes_ss = ["1a1", "1a2", "1b3", "1b4"]; codes_cs = ["2a0", "2a6", "2b7", "2b9"]
    stim_len = {}
    with h5py.File(kcs / "fau_cf0.h5", "w") as f:
        for c in codes_ss + codes_cs:
            n = int(rng.integers(3000, 3600)); stim_len[c] = n
            for stream in ("attended", "distractor"):
                for t, d in (("Ac", 2), ("Lz", 3), ("Local", 6)):
                    f[f"{c}/{stream}/{t}"] = rng.standard_normal((d, n + int(rng.integers(0, 5)))).astype(np.float32)
    for g, ids in people.items():
        (stage / g).mkdir(parents=True)
        for pid in ids:
            with h5py.File(stage / g / f"{pid}.h5", "w") as f:
                f.attrs["channels"] = np.array([f"E{j}" for j in range(31)], dtype="S")
                order = [str(c) for c in rng.permutation(codes_ss + codes_cs)]
                for j, c in enumerate(order):
                    n = stim_len[c] - int(rng.integers(0, 200))
                    grp = f.create_group(f"t{j:02d}"); grp.attrs["stimulus"] = c
                    grp["eeg_1_20_ica"] = (rng.standard_normal((31, n)) * rng.uniform(0.5, 3.0) + rng.uniform(-1, 1)).astype(np.float32)
    panel = {"h1": ("ha", 0), "c1": ("ci", 1)}
    return stage, kcs, (["d1", "d2"], panel)


def _dtu_fixture(tmp, rng):
    h5py = _h5()
    pub = tmp / "pub"; repo = tmp / "repo"; kcs = tmp / "kcs_dtu"; pre = tmp / "pre"
    (pub / "dtu_snhl" / "ds-eeg-snhl" / "ds-eeg-snhl").mkdir(parents=True); (pub / "derived" / "c3_features_v1" / "dtu").mkdir(parents=True)
    (repo / "private" / "auditory_c3" / "public" / "dtu_v2").mkdir(parents=True); kcs.mkdir(); pre.mkdir()
    subs = {"sub-001": "nh", "sub-002": "hi", "sub-003": "nh", "sub-004": "hi"}
    with open(pub / "dtu_snhl" / "ds-eeg-snhl" / "ds-eeg-snhl" / "participants.tsv", "w") as f:
        f.write("participant_id\thearing_status\tage\n" + "".join(f"{s}\t{g}\t{40 + j}\n" for j, (s, g) in enumerate(subs.items())))
    for s in subs:
        (repo / "private" / "auditory_c3" / "public" / "dtu_v2" / f"{s}.json").write_text("{}")
    hashes = [f"h{j:02d}aaaaaaaaaa" for j in range(8)]
    content = {h: {"half": j % 2, "early_stop": j % 3 == 0, "group": j // 2} for j, h in enumerate(hashes)}
    with open(kcs / "content_groups.json", "w") as f:
        json.dump({"content": content}, f)
    with h5py.File(kcs / "dtu_cf0.h5", "w") as f:
        for h in hashes:
            n = int(rng.integers(2600, 3200))
            for t, d in (("Ac", 2), ("Lz", 3), ("Local", 6)):
                f[f"{h}/{t}"] = rng.standard_normal((d, n)).astype(np.float32)
    inv = []
    for s in subs:
        with h5py.File(pre / f"{s}.h5", "w") as f:
            for j in range(6):
                k = f"trial{j:02d}"; two = j % 2 == 1
                n = int(rng.integers(2200, 3000))
                g = f.create_group(k); g.attrs["talkers"] = "twotalker" if two else "singletalker"
                if two:
                    g.attrs["masker_onset_rel_s"] = float(rng.uniform(0.5, 2.0))
                g["eeg_1_20"] = (rng.standard_normal((66, n)) * rng.uniform(0.5, 2.0)).astype(np.float32)
                th = hashes[int(rng.integers(0, len(hashes)))]
                inv.append({"file": s, "trial": k, "kind": "target", "sha": th, "offset_s": 0.0})
                if two:
                    inv.append({"file": s, "trial": k, "kind": "masker", "sha": hashes[int(rng.integers(0, len(hashes)))], "offset_s": float(rng.uniform(0, 1))})
            if s == "sub-003":  # a trial without inventory entry is skipped by both loaders
                g = f.create_group("trial99"); g.attrs["talkers"] = "singletalker"; g["eeg_1_20"] = np.zeros((66, 900), np.float32)
    with open(pub / "derived" / "c3_features_v1" / "dtu" / "inventory.json", "w") as f:
        json.dump(inv, f)
    return pub, repo, kcs, pre


def _compare_cohorts(orig, new, window=77, frames=8):
    import torch
    assert (orig.fs, orig.n_ch, orig.meta) == (new.fs, new.n_ch, new.meta)
    assert orig.participants == new.participants
    o_ss = [s for s in orig.segments if s["kind"] == "ss"]
    assert len(o_ss) == len(new.segments) > 0 and all(s["kind"] == "ss" for s in new.segments)
    assert any(s["kind"] == "cs" for s in orig.segments)  # the fixture has competing-speech trials that the original keeps
    seg_len = orig.meta["seg_len"]
    e16 = torch.from_numpy(orig.eeg).to(torch.float16).numpy()  # the batcher's conversion of the original bank
    assert new.eeg.dtype == np.float16
    for a, b in zip(o_ss, new.segments):
        for k in ("p", "role", "kind", "uid", "hard_key", "part", "code", "s0_ign"):
            assert a[k] == b[k], k
        np.testing.assert_array_equal(a["feat"], b["feat"])
        np.testing.assert_array_equal(e16[:, a["e0"]:a["e0"] + seg_len + window], new.eeg[:, b["e0"]:b["e0"] + seg_len + window])
        for t in orig.stim:
            np.testing.assert_array_equal(orig.stim[t][:, a["s0"]:a["s0"] + seg_len + frames], new.stim[t][:, b["s0"]:b["s0"] + seg_len + frames])
    # recording order of each participant's single-speaker segments is preserved (the runner sorts by e0)
    for p in {s["p"] for s in new.segments}:
        ua = [s["uid"] for s in sorted((s for s in o_ss if s["p"] == p), key=lambda s: s["e0"])]
        ub = [s["uid"] for s in sorted((s for s in new.segments if s["p"] == p), key=lambda s: s["e0"])]
        assert ua == ub


def test_fau_ss_only_equals_original(tmp_path, monkeypatch):
    from auditory_alignment import data as D
    rng = np.random.default_rng(1)
    stage, kcs, panel = _fau_fixture(tmp_path, rng)
    monkeypatch.setattr(D, "FAU_KCS", str(kcs)); monkeypatch.setattr(D, "STAGEB", str(stage)); monkeypatch.setattr(D, "fau_panel", lambda: panel)
    for cf in (0,):
        orig = D.load_fau(cf, kinds=("ss", "cs"), stage_dir=str(stage))
        new = DR.load_fau_ss_only(cf)
        _compare_cohorts(orig, new)
        roles = {s["role"] for s in new.segments}
        assert roles == {"fit", "es", "test"}


def test_dtu_ss_only_equals_original(tmp_path, monkeypatch):
    from auditory_alignment import data as D
    rng = np.random.default_rng(2)
    pub, repo, kcs, pre = _dtu_fixture(tmp_path, rng)
    for k, v in (("PUB", str(pub)), ("REPO", str(repo)), ("DTU_KCS", str(kcs)), ("DTU_PRE", str(pre))):
        monkeypatch.setattr(D, k, v)
    orig = D.load_dtu(0, kinds=("ss", "cs"))
    new = DR.load_dtu_ss_only(0)
    _compare_cohorts(orig, new)


def test_ss_only_standardises_over_all_trials(tmp_path, monkeypatch):
    """the kept single-speaker EEG equals the original (both-kind) standardisation and differs from an ss-only standardisation."""
    from auditory_alignment import data as D
    rng = np.random.default_rng(3)
    stage, kcs, panel = _fau_fixture(tmp_path, rng)
    monkeypatch.setattr(D, "FAU_KCS", str(kcs)); monkeypatch.setattr(D, "STAGEB", str(stage)); monkeypatch.setattr(D, "fau_panel", lambda: panel)
    wrong = D.load_fau(0, kinds=("ss",), stage_dir=str(stage))  # standardised over single-speaker trials only
    new = DR.load_fau_ss_only(0)
    a, b = wrong.segments[0], new.segments[0]
    assert a["uid"] == b["uid"]
    assert not np.array_equal(wrong.eeg[:, a["e0"]:a["e0"] + 640].astype(np.float16), new.eeg[:, b["e0"]:b["e0"] + 640])


# ------------------------------------------------------------------------------------------------ ids, scope
def test_execution_id_and_seed():
    a, b = DR.execution_id("ALN3_x"), DR.execution_id("ALN3_y")
    assert a == DR.execution_id("ALN3_x") and a != b and a.startswith("R34DR1_") and len(a) == len("R34DR1_") + 16
    s = DR.torch_seed("ALN3_x")
    assert s == DR.torch_seed("ALN3_x") and 0 <= s < 2 ** 32 and s != DR.torch_seed("ALN3_y")


def _row(eid, ds="fau", seed=3401, obj="NCE", ad="none", sf=0, cf=0, arch="lag_local_tokens", fam="D_ADAPT"):
    return {"experiment_id": eid, "family_id": fam, "dataset": ds, "seed": seed, "subject_fold": sf, "content_fold": cf,
            "spec": {"architecture": arch, "objective": obj, "adapter": ad}}


def test_in_scope():
    assert DR.in_scope(_row("a"))
    assert not DR.in_scope(_row("a", arch="dense_fm_policy")) and not DR.in_scope(_row("a", arch="complement_policy"))
    assert not DR.in_scope(_row("a", ds="federici")) and not DR.in_scope(_row("a", seed=3402)) and not DR.in_scope(_row("a", fam="D_ATTENTION"))
    assert not DR.in_scope(_row("a", obj="FMCA"))


def test_scope_on_live_plan_rows():
    """reads the plan and plan_ext rows only (no record): 200 lag-local D_ADAPT rows with the note's breakdown."""
    rows = DR.all_rows()
    sc = [r for r in rows if DR.in_scope(r)]
    assert len(sc) == 200
    from collections import Counter
    c = Counter((r["seed"], r["spec"]["objective"], r["spec"]["adapter"]) for r in sc)
    for a in DR.ADAPTERS:
        for o in DR.OBJECTIVES:
            assert c[(3401, o, a)] == 20
    for s in DR.PANEL_SEEDS:
        assert c[(s, "NCE", "none")] == 20 and c[(s, "NCE", "input_spatial")] == 20 and c[(s, "NCE", "output_low_rank")] == 0
        assert c[(s, "CS_SINGLE", "none")] == 0


# ------------------------------------------------------------------------------------------------ QC
def _eval(pids=("P1", "P2"), gain=0.5, shift=0.0, nq=20, chosen=50, none=False):
    pp = {}
    for j, p in enumerate(pids):
        rr = {"group": "ha", "n_segments": 30}
        for sf in DR.SUPPORTS:
            x = {}
            for rd in DR.READOUTS:
                g = gain + 0.1 * j + (0.0 if none else (0.05 if sf == "0.3" else 0.0)) + shift
                x[rd] = {"gain_bits": g, "rank_pct": 0.3, "top1": 0.1, "n_query": nq, "logloss_bits": 6.0 - g / 2, "mismatched_logloss_bits": 6.0 + g / 2,
                         "top5": 0.3, "mrr": 0.2, "n_candidates": 100, "tau": 0.1}
            x["n_support"] = 3 if sf == "0.1" else 9
            rr[f"support_{sf}"] = x
        pp[p] = rr
    return {"per_participant": pp, "steps": {"chosen": chosen, "scores": {20: 0.1, 50: 0.2, 100: 0.15}}}


def _rec(ev):
    r = json.loads(json.dumps(ev))
    for p in r["per_participant"].values():
        for sf in DR.SUPPORTS:
            for rd in DR.READOUTS:
                for k in DR.EXTRA_FIELDS:
                    p[f"support_{sf}"][rd].pop(k)
    return {"status": "complete", "eval": r}


def test_qc_exact_pass_and_fail():
    ev = _eval()
    q = DR.reproduction_qc(_rec(ev), ev, "input_spatial")
    assert q["pass"] and q["structural_pass"] and q["tier"] == "exact" and q["max_abs_d_gain_bits"] == 0.0 and q["steps"]["equal"]
    q = DR.reproduction_qc(_rec(ev), _eval(shift=5e-4), "input_spatial")
    assert q["pass"] and abs(q["max_abs_d_gain_bits"] - 5e-4) < 1e-12
    q = DR.reproduction_qc(_rec(ev), _eval(shift=2e-3), "input_spatial")
    assert not q["pass"] and q["structural_pass"] and not q["numeric_pass"]
    q = DR.reproduction_qc(_rec(ev), _eval(chosen=100), "input_spatial")
    assert not q["pass"] and not q["steps"]["equal"]
    q = DR.reproduction_qc(_rec(ev), _eval(nq=21), "input_spatial")
    assert not q["structural_pass"] and any("n_query" in p for p in q["problems"])
    q = DR.reproduction_qc(_rec(ev), _eval(pids=("P1",)), "input_spatial")
    assert not q["structural_pass"]
    q = DR.reproduction_qc(_rec(ev), ev, "input_spatial", base_ok=False)
    assert not q["pass"]


def test_qc_seeded_refit_reports_but_does_not_bound():
    ev = _eval()
    q = DR.reproduction_qc(_rec(ev), _eval(shift=0.02, chosen=20), "output_low_rank")
    assert q["tier"] == "seeded_refit" and q["pass"] and not q["numeric_pass"] and not q["steps"]["equal"]
    assert abs(q["deviation"]["gain_bits|unified"]["mean_signed"] - 0.02) < 1e-12
    q = DR.reproduction_qc(_rec(ev), _eval(shift=0.02, nq=3), "output_low_rank")
    assert not q["pass"]


def test_qc_none_identical_across_support():
    ev = _eval(none=True, chosen=0)
    q = DR.reproduction_qc(_rec(ev), ev, "none")
    assert q["pass"] and q["none_identical_across_support"]
    bad = _eval(none=True, chosen=0)
    bad["per_participant"]["P1"]["support_0.3"]["unified"]["logloss_bits"] += 1e-9
    q = DR.reproduction_qc(_rec(ev), bad, "none")
    assert not q["pass"] and q["none_identical_across_support"] is False


def test_qc_top1_flips():
    ev = _eval()
    new = json.loads(json.dumps(ev))
    new["per_participant"]["P1"]["support_0.1"]["unified"]["top1"] += 1 / 20
    q = DR.reproduction_qc(_rec(ev), new, "input_spatial")
    assert q["top1_query_flips"]["unified"] == 1 and q["pass"]  # reported, not bounded


# ------------------------------------------------------------------------------------------------ worker loop
def _units_file(tmp, eids):
    p = tmp / "units.txt"
    p.write_text("# header\n" + "".join(f"{e} x y\n" for e in eids))
    return str(p)


def test_unit_order_and_shards():
    e = [f"u{j}" for j in range(7)]
    assert DR.unit_order(e, (1, 3), steal=False) == ["u1", "u4"]
    assert DR.unit_order(e, (1, 3)) == ["u1", "u4", "u0", "u2", "u3", "u5", "u6"]
    assert DR.unit_order(e, None) == e
    assert DR.parse_shard("2/4") == (2, 4) and DR.parse_shard(None) is None
    with pytest.raises(ValueError):
        DR.parse_shard("4/4")


def test_worker_idempotent_claims_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(DR, "LOGS", str(tmp_path / "logs"))
    out = tmp_path / "out"; out.mkdir()
    calls = []

    def ok_child(eid, device, out_dir, loader, threads=None):
        calls.append(eid)
        if eid == "bad":
            return 1, None  # dies without recording: the parent records the failure
        DR.write_json(DR.out_path(out_dir, eid), {"status": "complete"})
        return 0, None
    uf = _units_file(tmp_path, ["a", "b", "bad", "c"])
    # a fresh foreign claim on "c" (another live worker) is respected
    os.makedirs(out / "claims" / "c.claim")
    DR.write_json(str(out / "claims" / "c.claim" / "owner.json"), {"job": "999", "worker": "w0", "host": "h", "pid": 1})
    t = DR.run_units_file(uf, "cpu", str(out), None, "w0", "original", 3, True, None, child=ok_child, live={"999"})
    assert t["done"] == 2 and t["failed"] == 1 and t["skip_claimed"] == 1 and calls == ["a", "b", "bad"]
    assert DR.failed_tries(str(out), "bad") == 1 and not os.path.exists(out / "claims" / "a.claim")
    calls.clear()
    t = DR.run_units_file(uf, "cpu", str(out), None, "w0", "original", 3, True, None, child=ok_child, live={"999"})
    assert t["skip_done"] == 2 and calls == ["bad"] and DR.failed_tries(str(out), "bad") == 2
    DR.run_units_file(uf, "cpu", str(out), None, "w0", "original", 3, True, None, child=ok_child, live={"999"})
    calls.clear()
    t = DR.run_units_file(uf, "cpu", str(out), None, "w0", "original", 3, True, None, child=ok_child, live={"999"})
    assert t["skip_failed"] == 1 and calls == []  # tried 3 times: skipped
    # the foreign claim's job is gone and the claim is older than 2 min: released by the sweep
    old = time_back(out / "claims" / "c.claim", 300)
    t = DR.run_units_file(uf, "cpu", str(out), None, "w0", "original", 3, True, None, child=ok_child, live={"1"})
    assert old and t["released_stale_claims"] == 1 and t["done"] == 1


def time_back(path, seconds):
    import time
    st = os.stat(path)
    os.utime(path, (st.st_atime - seconds, st.st_mtime - seconds))
    return True


def test_sweep_releases_own_claims_only(tmp_path):
    claims = tmp_path / "claims"
    me = {"job": "123", "worker": "w1"}
    for name, own in (("mine", {"job": "123", "worker": "w1"}), ("sibling", {"job": "123", "worker": "w0"}), ("other", {"job": "456", "worker": "w1"})):
        os.makedirs(claims / f"{name}.claim")
        DR.write_json(str(claims / f"{name}.claim" / "owner.json"), own)
    rel = DR.sweep_claims(str(claims), me, {"123", "456"})
    assert rel == ["mine"] and os.path.isdir(claims / "sibling.claim") and os.path.isdir(claims / "other.claim")


def _claim(claims, name, own, age_s=300):
    os.makedirs(claims / f"{name}.claim")
    DR.write_json(str(claims / f"{name}.claim" / "owner.json"), own)
    time_back(claims / f"{name}.claim", age_s)


def test_sweep_array_elements_in_both_squeue_forms(tmp_path):
    """note, addendum 2, C2: an array element's claim (SLURM_JOB_ID 1041001 = element 1041000_1) is live when squeue lists the element in
    either form (%i: 1041000_1; %A: 1041001); it is released only when the element runs in neither form."""
    claims = tmp_path / "claims"
    me = {"job": "1041003", "worker": "w0", "array_task": "1041000_3"}
    el = {"job": "1041001", "worker": "w0", "array_task": "1041000_1", "host": "h", "pid": 7}
    _claim(claims, "ALN3_x", el)
    assert DR.sweep_claims(str(claims), me, {"1041000_0", "1041000_1", "1041000_3"}) == []  # %i form (the verifier's case)
    assert DR.sweep_claims(str(claims), me, {"1041000", "1041001", "1041003"}) == []  # %A form
    assert DR.sweep_claims(str(claims), me, {"1041000_0", "1041000_1", "1041002", "1041003"}) == []  # mixed (squeue -o "%A %i")
    assert DR.sweep_claims(str(claims), me, {"1041000_0", "1041000", "1041003"}) == ["ALN3_x"]  # element no longer running
    _claim(claims, "ALN3_y", {"job": "1041001", "worker": "w0", "host": "h", "pid": 7})  # owner record without array_task (plain job)
    assert DR.sweep_claims(str(claims), me, {"1041000_1"}) == ["ALN3_y"]  # only the %i form listed and no array_task: not live
    _claim(claims, "ALN3_z", {"job": "1041001", "worker": "w0", "host": "h", "pid": 7})
    assert DR.sweep_claims(str(claims), me, {"1041001"}) == []


def test_owner_and_live_jobs_forms(monkeypatch):
    monkeypatch.setenv("SLURM_JOB_ID", "1041001"); monkeypatch.setenv("SLURM_ARRAY_JOB_ID", "1041000"); monkeypatch.setenv("SLURM_ARRAY_TASK_ID", "1")
    o = DR.owner("w1")
    assert o["job"] == "1041001" and o["array_task"] == "1041000_1" and o["worker"] == "w1"
    monkeypatch.delenv("SLURM_ARRAY_JOB_ID"); monkeypatch.delenv("SLURM_ARRAY_TASK_ID")
    assert "array_task" not in DR.owner("w1")
    seen = {}

    class P:
        returncode, stdout = 0, "1041001 1041000_1\n1041002 1041000_2\n1039458 1039458\n"

    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        return P()
    monkeypatch.setattr(DR.subprocess, "run", fake_run)
    live = DR.live_jobs()
    assert seen["cmd"][-2:] == ["-o", "%A %i"] and live == {"1041001", "1041000_1", "1041002", "1041000_2", "1039458"}
    P.stdout = ""
    assert DR.live_jobs() is None  # nothing listed: no foreign claim is released


def test_release_claim_only_own(tmp_path):
    """the first worker's release never deletes a claim that another worker holds (note, addendum 2, C2)."""
    claims = tmp_path / "claims"
    me = {"job": "1041001", "worker": "w0", "host": "h", "pid": 11}
    other = {"job": "1041002", "worker": "w0", "host": "h2", "pid": 12}
    assert DR.try_claim(str(claims), "u1", other)
    assert DR.release_claim(str(claims), "u1", me) is False and os.path.isdir(claims / "u1.claim")
    assert DR.release_claim(str(claims), "u1", {**other, "utc": "later"}) is True and not os.path.exists(claims / "u1.claim")
    assert DR.try_claim(str(claims), "u2", me) and not DR.try_claim(str(claims), "u2", other)
    assert DR.release_claim(str(claims), "u2", {**me, "pid": 99}) is False  # same job and tag, other process: not its claim
    assert DR.release_claim(str(claims), "missing", me) is False


def test_protected_writes(tmp_path, monkeypatch):
    """note, addendum 2, C4: no write into the records / checkpoint / source trees; --out is checked before anything is written."""
    assert DR.protected(os.path.join(DR.RECORDS, "ALN3_x.json")) and DR.protected(DR.RECORDS)
    assert DR.protected(os.path.join(DR.core.OUT, "ckpt", "x_best.pt")) and DR.protected(os.path.join(DR.core.OUT, "plan_ext.jsonl"))
    assert DR.protected("/projects/EEG-foundation-model/auditory/x") and not DR.protected("/projects/EEG-foundation-model/auditory_public/x")
    assert not DR.protected(os.path.join(DR.UNITS_DIR, "ALN3_x.json")) and not DR.protected(DR.UNITS_FILE) and not DR.protected(DR.NOTE)
    assert os.path.relpath(DR.UNITS_DIR, DR.REPO).startswith(os.path.join("private", "auditory_alignment_v3", "aln34")) or os.environ.get("DR_PRIV")
    fake = tmp_path / "records"; fake.mkdir()
    monkeypatch.setattr(DR, "PROTECTED", (str(fake),))
    with pytest.raises(PermissionError):
        DR.write_json(str(fake / "ALN3_x.json"), {"a": 1})
    with pytest.raises(PermissionError):
        DR.write_text(str(fake / "sub" / "x.md"), "x")
    with pytest.raises(PermissionError):
        DR.unit_main("ALN3_x", "cpu", str(fake), "original", force=True)
    with pytest.raises(PermissionError):
        DR.run_units_file(_units_file(tmp_path, ["ALN3_x"]), "cpu", str(fake), child=lambda *a, **k: (0, None), live=set())
    with pytest.raises(PermissionError):
        DR.try_claim(str(fake / "claims"), "ALN3_x", {"job": "1"})
    assert os.listdir(fake) == []
    link = tmp_path / "link"; os.symlink(fake, link)  # through a symlink as well
    with pytest.raises(PermissionError):
        DR.write_json(str(link / "x.json"), {})


def test_value_path_hash(monkeypatch):
    """note, addendum 2, C5: the evaluator hash keeps its definition (= the three CPU outputs of addendum 1); the value-path hash also
    covers torch_seed, execution_id and the constants."""
    assert DR.EVALUATOR_SHA256 == "65d2d06219630ef1a8460e3538af120f5a4f37d87f038304f31a24ddbeb5c383", \
        "the evaluator functions changed: the CPU checks of addendum 1 no longer cover this code (note it before any GPU run)"
    assert DR.evaluator_sha256() == DR.EVALUATOR_SHA256 and DR.value_path_sha256() == DR.VALUE_PATH_SHA256
    monkeypatch.setattr(DR, "TIER", {**DR.TIER, "output_low_rank": "exact"})
    assert DR.value_path_sha256() != DR.VALUE_PATH_SHA256 and DR.evaluator_sha256() == DR.EVALUATOR_SHA256
    monkeypatch.setattr(DR, "TOL_GAIN", 1e-2)
    assert DR.value_path_sha256() != DR.VALUE_PATH_SHA256
    assert DR.code_versions()["value_path"] == DR.VALUE_PATH_SHA256 and DR.code_versions()["evaluator_functions"] == DR.EVALUATOR_SHA256


def test_write_json_mode(tmp_path):
    p = DR.write_json(str(tmp_path / "d" / "x.json"), {"a": np.float32(1.5), "b": {3: np.int64(2)}})
    assert oct(os.stat(p).st_mode & 0o777) == "0o600" and json.load(open(p)) == {"a": 1.5, "b": {"3": 2}}


# ------------------------------------------------------------------------------------------------ aggregation
PIDS = {"fau": [f"F{j:02d}" for j in range(8)], "dtu": [f"D{j:02d}" for j in range(6)]}
EFF = {3401: 0.10, 3407: 0.12, 3413: 0.08}  # R(none) - R(input_spatial) at support 0.3, unified


def _true_R(seed, ds, obj, ad, sf, j, cf):
    r = 6.5 + 0.02 * j + 0.01 * cf
    if ad == "input_spatial":
        r -= EFF[seed] if sf == "0.3" else -0.05
    if ad == "output_low_rank":
        r -= 0.02
    return r


def _synthetic(fail=None):
    rows, outs, recs = [], {}, {}
    k = 0
    for seed in DR.SEEDS:
        for ds in DR.DATASETS:
            for obj in (DR.OBJECTIVES if seed == 3401 else ("NCE",)):
                for ad in (DR.ADAPTERS if seed == 3401 else ("none", "input_spatial")):
                    for sf in (0, 1):
                        for cf in (0, 1):
                            eid = f"U{k:04d}"; k += 1
                            rows.append(_row(eid, ds, seed, obj, ad, sf, cf))
                            test = [p for j, p in enumerate(PIDS[ds]) if j % 2 == sf]
                            pp, rp = {}, {}
                            for p in test:
                                j = PIDS[ds].index(p)
                                rr, rv = {"group": "a" if j % 2 else "b", "n_segments": 20}, {"group": "a" if j % 2 else "b", "n_segments": 20}
                                for s_ in DR.SUPPORTS:
                                    x, xr = {}, {}
                                    for rd in DR.READOUTS:
                                        R = _true_R(seed, ds, obj, ad, s_, j, cf) + (0.3 if rd == "native" else 0.0)
                                        Rmm = 7.0 + 0.01 * j + (0.01 if ad == "input_spatial" else 0.0)
                                        g = Rmm - R
                                        x[rd] = {"gain_bits": g, "rank_pct": 0.3, "top1": 0.1, "n_query": 14, "logloss_bits": R, "mismatched_logloss_bits": Rmm,
                                                 "top5": 0.3, "mrr": 0.2, "n_candidates": 128, "tau": 0.1}
                                        xr[rd] = {"gain_bits": g + (0.004 if ad == "output_low_rank" else 0.0), "rank_pct": 0.3, "top1": 0.1, "n_query": 14}
                                    x["n_support"] = xr["n_support"] = 2 if s_ == "0.1" else 6
                                    rr[f"support_{s_}"] = x; rv[f"support_{s_}"] = xr
                                pp[p] = rr; rp[p] = rv
                            passed = not (fail and fail(eid, seed, ds, obj, ad, sf, cf))
                            outs[eid] = {"status": "complete", "execution_version": DR.VERSION, "loader": "original",
                                         "eval": {"per_participant": pp, "steps": {"chosen": 50}},
                                         "qc": {"pass": passed, "structural_pass": passed, "numeric_pass": passed, "steps": {"recorded": 50, "refit": 50, "equal": True},
                                                "max_abs_d_gain_bits": 0.0, "max_abs_d_rank_pct": 0.0, "n_problems": 0, "problems": [],
                                                "cells": [{"readout": "unified", "d_gain_bits": 0.0}]},
                                         "environment": {"device_name": "NVIDIA A40"}, "runtime": {"seconds": 1.0},
                                         "code": {"aln34/dadapt_r.py": "m", "evaluator_functions": "e"}}
                            recs[eid] = {"status": "complete", "eval": {"per_participant": rp}}
    return rows, outs, recs


def _member(res, label, name, metric=DR.PRIMARY):
    return DR.member_block(res, label, metric)["members"][name]


def test_aggregate_signs_decomposition_seed_mean():
    rows, outs, recs = _synthetic()
    out, per = DR.analyse(rows, outs.get, recs.get)
    m = _member(out["full_3401"], "AD-GAIN|fau|NCE|0.3", "input_spatial")
    assert m["n"] == len(PIDS["fau"]) and abs(m["est"] - EFF[3401]) < 1e-9 and m["class"] == "I>0"  # positive = lower risk
    m01 = _member(out["full_3401"], "AD-GAIN|fau|NCE|0.1", "input_spatial")
    assert abs(m01["est"] + 0.05) < 1e-9
    # decomposition: Δgain = ΔR + ΔR_mm per identity, hence for the means
    for d in out["decomposition_full_3401"].values():
        assert d["identity_residual"] is not None and abs(d["identity_residual"]) < 1e-9
    d = out["decomposition_full_3401"]["AD-GAIN|fau|NCE|0.3|input_spatial|unified"]
    assert abs(d["refit_minus_record"]) < 1e-12  # exact tier: refit gain equals the recorded gain in the fixture
    # identity mean over seeds = mean of the per-seed paired differences
    sm = _member(out["panel_identity_mean"], "AD-GAIN|dtu|NCE|0.3", "input_spatial")
    assert abs(sm["est"] - np.mean(list(EFF.values()))) < 1e-9 and sm["identities_by_n_seeds"] == {"3": len(PIDS["dtu"])}
    for s in DR.SEEDS:
        ps = _member(out["panel_per_seed"][str(s)], "AD-GAIN|dtu|NCE|0.3", "input_spatial")
        assert abs(ps["est"] - EFF[s]) < 1e-9
    b = out["between_seed"]["AD-GAIN|dtu|NCE|0.3|input_spatial|R_bits"]
    assert abs(b["spread"] - (max(EFF.values()) - min(EFF.values()))) < 1e-9
    # mismatched: raw direction (candidate - reference): input_spatial has +0.01
    mm = _member(out["full_3401"], "AD-GAIN|fau|NCE|0.3", "input_spatial", "R_mm_bits")
    assert abs(mm["est"] - 0.01) < 1e-9
    cov = out["coverage"]
    assert cov["n_missing_pairs"] == 0 and cov["n_partial_pairs"] == 0 and cov["n_asymmetric_pairs"] == 0 and cov["units_admitted"] == len(rows)
    # 3401: 24 members (12 families x 2); panel seeds: 6 members each; every identity of the dataset once per member
    n_id = {"fau": len(PIDS["fau"]), "dtu": len(PIDS["dtu"])}
    assert cov["n_complete_pairs"] == sum(n_id[k.split("|")[2]] for k in cov["pairs"]) and len(cov["pairs"]) == 24 + 2 * 6
    assert cov["units_per_identity"]["3401|AD|fau|NCE|none|0.1"] == {"2": len(PIDS["fau"])}  # two content folds each
    lv = out["levels"]["3401|AD|fau|NCE|none|0.1"]
    assert lv["n"] == len(PIDS["fau"]) and lv["K"] == [128]
    assert set(per) == {"3401", "3407", "3413", "groups", "pair_values", "pair_coverage", "qc_problems", "_ids"}
    assert all(p["kind"] == "complete" and p["kept_content_folds"] == [0, 1] for p in per["pair_coverage"])
    # members keep their original configurations in the results (the pair keys are internal)
    assert m["ref"] == "AD|fau|NCE|none|0.3" and m["cand"] == "AD|fau|NCE|input_spatial|0.3"
    assert _member(out["panel_identity_mean"], "AD-GAIN|dtu|NCE|0.3", "input_spatial")["cand"] == "AD|dtu|NCE|input_spatial|0.3"


def test_aggregate_output_low_rank_record_difference():
    rows, outs, recs = _synthetic()
    out, _ = DR.analyse(rows, outs.get, recs.get)
    d = out["decomposition_full_3401"]["AD-GAIN|dtu|CS_SINGLE|0.1|output_low_rank|native"]
    assert abs(d["d_gain_record"] - d["d_gain_refit"] - 0.004) < 1e-9 and abs(d["refit_minus_record"] + 0.004) < 1e-9


def test_aggregate_excludes_failed_units_and_lists_missing_pairs():
    # both content folds of FAU subject fold 0, seed 3407, input_spatial fail -> those identities miss the 3407 pair
    fail = lambda eid, seed, ds, obj, ad, sf, cf: seed == 3407 and ds == "fau" and ad == "input_spatial" and sf == 0
    rows, outs, recs = _synthetic(fail)
    out, per = DR.analyse(rows, outs.get, recs.get)
    lost = [p for j, p in enumerate(PIDS["fau"]) if j % 2 == 0]
    mp = [m for m in per["pair_coverage"] if m["seed"] == 3407 and m["kind"] == "missing"]
    assert {m["identity"] for m in mp} == set(lost) and out["coverage"]["units_admitted"] == len(rows) - 2
    # 3 members at 3407 (AD-GAIN 0.1, AD-GAIN 0.3, AD-SUPPORT) x 4 identities; nothing partial
    assert len(mp) == 3 * len(lost) and out["coverage"]["n_missing_pairs"] == 3 * len(lost) and out["coverage"]["n_partial_pairs"] == 0
    assert out["coverage"]["pairs"]["3407|AD-GAIN|fau|NCE|0.3|input_spatial"] == {"expected": len(PIDS["fau"]), "complete": len(PIDS["fau"]) - len(lost),
                                                                                    "partial": 0, "missing": len(lost), "asymmetric": len(lost)}
    ps = _member(out["panel_per_seed"]["3407"], "AD-GAIN|fau|NCE|0.3", "input_spatial")
    assert ps["n"] == len(PIDS["fau"]) - len(lost)
    sm = _member(out["panel_identity_mean"], "AD-GAIN|fau|NCE|0.3", "input_spatial")
    assert sm["n"] == len(PIDS["fau"]) and sm["identities_by_n_seeds"] == {"2": len(lost), "3": len(PIDS["fau"]) - len(lost)}
    cc = _member(out["panel_identity_mean_complete_case"], "AD-GAIN|fau|NCE|0.3", "input_spatial")
    assert cc["n"] == len(PIDS["fau"]) - len(lost)
    assert len(out["qc"]["failing_units"]) == 2
    assert out["coverage"]["units_per_identity"]["3407|AD|fau|NCE|input_spatial|0.3"] == {"2": len(PIDS["fau"]) - len(lost)}


@pytest.mark.parametrize("side", ["input_spatial", "none"])
def test_aggregate_partial_pair_is_content_fold_matched(side):
    """the verifier's case (note, addendum 2, C1): only content fold 0 of FAU 3407 subject fold 0 fails, on the candidate side
    (input_spatial) or on the reference side (none). The pair keeps content fold 1 on both sides: every identity's ΔR is the per-unit
    0.12 (the fixture's R has +0.01 per content fold, so mixing query sets gave 0.115 and a member estimate of 0.1175), and the 4
    partial pairs are counted and listed."""
    fail = lambda eid, seed, ds, obj, ad, sf, cf: seed == 3407 and ds == "fau" and ad == side and sf == 0 and cf == 0
    rows, outs, recs = _synthetic(fail)
    out, per = DR.analyse(rows, outs.get, recs.get)
    hit = [p for j, p in enumerate(PIDS["fau"]) if j % 2 == 0]
    for sf in DR.SUPPORTS:
        ps = _member(out["panel_per_seed"]["3407"], f"AD-GAIN|fau|NCE|{sf}", "input_spatial")
        want = EFF[3407] if sf == "0.3" else -0.05
        assert ps["n"] == len(PIDS["fau"]) and abs(ps["est"] - want) < 1e-12
    pv = per["pair_values"]["3407"]
    for i in PIDS["fau"]:
        d = pv["AD-GAIN|fau|NCE|0.3|input_spatial|ref"][i]["R_bits"] - pv["AD-GAIN|fau|NCE|0.3|input_spatial|cand"][i]["R_bits"]
        assert abs(d - EFF[3407]) < 1e-12, i
        dg = pv["AD-GAIN|fau|NCE|0.3|input_spatial|cand"][i]["gain_refit"] - pv["AD-GAIN|fau|NCE|0.3|input_spatial|ref"][i]["gain_refit"]
        dm = pv["AD-GAIN|fau|NCE|0.3|input_spatial|cand"][i]["R_mm_bits"] - pv["AD-GAIN|fau|NCE|0.3|input_spatial|ref"][i]["R_mm_bits"]
        assert abs(dg - (d + dm)) < 1e-12  # decomposition on one query set
    sm = _member(out["panel_identity_mean"], "AD-GAIN|fau|NCE|0.3", "input_spatial")
    assert abs(sm["est"] - np.mean(list(EFF.values()))) < 1e-12 and sm["identities_by_n_seeds"] == {"3": len(PIDS["fau"])}
    part = [p for p in per["pair_coverage"] if p["kind"] == "partial"]
    gain = [p for p in part if p["family"].startswith("AD-GAIN")]
    assert {p["identity"] for p in part} == set(hit) and all(p["seed"] == 3407 for p in part)
    assert len(gain) == 2 * len(hit) and all(p["kept_content_folds"] == [1] and p["dropped_content_folds"] == [0] for p in part)
    lacking = "candidate_admitted" if side == "input_spatial" else "reference_admitted"
    assert all(p[lacking] == [1] and p[({"candidate_admitted", "reference_admitted"} - {lacking}).pop()] == [0, 1] for p in gain)
    cov = out["coverage"]
    n_sup = len(hit) if side == "input_spatial" else 0  # AD-SUPPORT (input_spatial 0.1 -> 0.3) is within one unit
    assert cov["n_partial_pairs"] == len(gain) + n_sup and cov["n_missing_pairs"] == 0 and cov["n_asymmetric_pairs"] == len(gain)
    assert cov["pairs"]["3407|AD-GAIN|fau|NCE|0.3|input_spatial"] == {"expected": len(PIDS["fau"]), "complete": len(PIDS["fau"]) - len(hit),
                                                                       "partial": len(hit), "missing": 0, "asymmetric": len(hit)}
    # levels stay the configuration's own identity mean over its admitted units (descriptive)
    assert out["coverage"]["units_per_identity"][f"3407|AD|fau|NCE|{side}|0.3"] == {"1": len(hit), "2": len(PIDS["fau"]) - len(hit)}


def test_public_outputs_identity_free():
    """note, addendum 2, C3: the public aggregate and document carry no participant id; the private file has the identity lists."""
    fail = lambda eid, seed, ds, obj, ad, sf, cf: seed == 3407 and ds == "dtu" and ad == "input_spatial" and sf == 1 and cf == 0
    rows, outs, recs = _synthetic(fail)
    bad_eid = next(e for e, o in outs.items() if not o["qc"]["pass"])
    outs[bad_eid]["qc"]["problems"] = ["D01: n_segments 20 != 21", "D03/0.3/unified: n_query 14 != 13", "D01: support_0.1 present in only one",
                                      "participants differ: record-only ['D05'], refit-only []", "base differs from the record's dependency"]
    outs[bad_eid]["qc"]["n_problems"] = 5
    out, per = DR.analyse(rows, outs.get, recs.get)
    ids = per.pop("_ids")
    assert set(ids) == set(PIDS["fau"]) | set(PIDS["dtu"])
    meta = {"generated": "now", "host": "h", "slurm_job": "none", "code_sha256": {"x": "0" * 64}, "note": "n", "note_sha256": "1" * 64, "note_mtime": "t",
            "units_dir": "u", "runtime_seconds": 1.0, "peak_rss_mib": 10.0, "json": "j", "per_identity": "p"}
    doc = DR.render(out, meta)
    pub = BI.jl(out)
    assert DR.identity_hits(pub, doc, ids) == []
    txt = json.dumps(pub) + doc
    assert not any(i in txt for i in ids)  # the fixture's ids are distinctive strings
    fu = out["qc"]["failing_units"][0]
    assert fu["problem_kinds"] == {"n_segments differs": 1, "n_query differs": 1, "support_0.1 present in only one": 1, "participants differ": 1,
                                   "base differs from the record's dependency": 1}
    assert per["qc_problems"][bad_eid][0] == "D01: n_segments 20 != 21" and any(p["kind"] == "partial" for p in per["pair_coverage"])
    # the scan finds ids in every form it guards against
    assert DR.identity_hits({"x": ["D01: n_query 3 != 4"]}, "", ids) and DR.identity_hits({"D01": 1}, "", ids)
    assert DR.identity_hits({"x": "F02"}, "", ids) and DR.identity_hits({}, "| 'F02' |", ids) and DR.identity_hits({}, "sub-012 text", set())
    assert DR.identity_hits({"n": "102 units"}, "", {"103"}) == []


def test_problem_kind_has_no_participant_id():
    ev = _eval(pids=("P1", "P2"))
    bad = json.loads(json.dumps(ev))
    bad["per_participant"]["P2"]["n_segments"] = 31; bad["per_participant"]["P2"]["group"] = "ci"
    bad["per_participant"]["P1"]["support_0.3"]["n_support"] = 8; bad["per_participant"]["P1"]["support_0.1"]["unified"]["n_query"] = 3
    del bad["per_participant"]["P2"]["support_0.1"]
    bad["per_participant"]["P9"] = bad["per_participant"].pop("P1")
    q = DR.reproduction_qc(_rec(ev), bad, "none", base_ok=False, code_ok=False)
    assert q["n_problems"] >= 5
    kinds = [DR.problem_kind(p) for p in q["problems"]]
    assert not any(("P1" in k or "P2" in k or "P9" in k) for k in kinds) and "participants differ" in kinds and "n_segments differs" in kinds


def test_panel_families_equal_d_multiseed():
    from auditory_alignment_v3.aln34 import d_multiseed as DM
    ref = [(f["family"], f["scope"], f["label"], f["members"]) for f in DM.panel_families() if f["kind"] == "ad"]
    assert DR.panel_families() == ref and len(ref) == 6
    assert DR.full_families() == DL.ad_families() and len(DR.full_families()) == 12


def test_seed_mean_deltas_equal_d_multiseed():
    from auditory_alignment_v3.aln34 import d_multiseed as DM
    DR.setup()
    rows, outs, recs = _synthetic()
    C = DR.collect(rows, outs.get, recs.get)
    vals = C["vals"]
    ref, cand = ("AD", "fau", "NCE", "none", "0.3"), ("AD", "fau", "NCE", "input_spatial", "0.3")
    pv, _ = DR.pair_inputs(DR.full_families(), C["cells"], C["expected"])
    pr, pc = DR.pair_keys("AD-GAIN|fau|NCE|0.3", "input_spatial")
    for m in DR.METRIC_KEYS:
        assert DR.seed_mean_deltas(vals, ref, cand, m) == DM.seed_mean_deltas(vals, ref, cand, m)
        # with every unit admitted, the content-fold-matched pairs give the configuration means' differences
        a, b = DR.seed_mean_deltas(pv, pr, pc, m), DM.seed_mean_deltas(vals, ref, cand, m)
        assert set(a) == set(b) and all(abs(a[i][0] - b[i][0]) < 1e-12 and a[i][1] == b[i][1] for i in a)


def test_directions_registered():
    DR.setup()
    assert BI.PDIR["R_bits"] == "lower" and BI.PDIR["R_mm_bits"] == "raw" and BI.PDIR["gain_refit"] == "higher"
    assert BI.diff(7.0, 6.5, DR.direction("R_bits")) == 0.5


def test_render_and_splice():
    rows, outs, recs = _synthetic()
    out, _ = DR.analyse(rows, outs.get, recs.get)
    meta = {"generated": "now", "host": "h", "slurm_job": "none", "code_sha256": {"x": "0" * 64}, "note": "n", "note_sha256": "1" * 64, "note_mtime": "t",
            "units_dir": "u", "runtime_seconds": 1.0, "peak_rss_mib": 10.0, "json": "j", "per_identity": "p"}
    doc = DR.render(out, meta)
    assert "## 1. 当前观察" in doc and "AD-GAIN · fau · NCE · 0.3 · input_spatial" in doc and "## 6. 暂不决定" in doc
    hand = doc.replace("## 2. 当前工作判断 (working interpretation)\n\n_Not written yet: written by hand after the generated tables have been viewed._",
                       "## 2. 当前工作判断 (working interpretation)\n\nhand text")
    assert "hand text" in DR.splice(doc, hand)
    with pytest.raises(ValueError):
        DR.splice(doc.replace("## 2. 当前工作判断", "## 9. other"), hand)
