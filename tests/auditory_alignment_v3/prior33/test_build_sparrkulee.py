"""M2a tests: the SparrKULee builders C1 / C2 / C4 (auditory_alignment_v3/prior33/build_sparrkulee.py; PUBLIC_PRIOR_DESIGN.md §2.1-§2.3,
§2.5, §3.2, §6.2, §7.1 items 8 and 3b) on a synthetic mini-BIDS tree in tmp: the run table and its roles, the restricted-participant
guard (an open-file audit hook: C2 and C4 never open a restricted participant's file, C1 reads only its .npy header; byte counts
from /proc/thread-self/io and from os.read show that only the header bytes reach the process; a participant restricted only by the
dataset_description.json Notes), the 64 Hz consistency rule, the clock-validity audit on planted offsets (aligned, a consistent
misalignment, inconsistent halves, no tracking, too few co-listeners) and its uniform record schema, the time-major float16 cache
against an independent recomputation, role slabs and exclusions, the stream / run table schema against the shared fixture
(fixtures.py, the interface of views.py) and the cohort unit (UNIT_RULE of build_public.py), resumability, the output-location
guard and the CLI guards. CPU only, about 200 MB in tmp."""
import collections
import inspect
import json
import os
import shutil
import sys

import numpy as np
import pytest
from scipy import signal

from auditory_alignment_v3.prior33 import build_public as BP
from auditory_alignment_v3.prior33 import build_sparrkulee as B
from auditory_alignment_v3.prior33 import contract as C

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixtures as FX  # noqa: E402

# ---------------------------------------------------------------------------------------------------------- open-file audit hook
_OPENS = {"on": False, "log": []}
_Open = collections.namedtuple("_Open", "path hdr mode flags")    # mode None: os.open (open() and io.open_code give a mode string)


def _hook(event, args):
    if not _OPENS["on"] or event != "open" or not args or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    names, f = set(), sys._getframe(1)
    while f is not None:
        names.add(f.f_code.co_name)
        f = f.f_back
    _OPENS["log"].append(_Open(os.fsdecode(args[0]), "_read_npy_header" in names, args[1] if len(args) > 1 else None,
                               args[2] if len(args) > 2 else None))


sys.addaudithook(_hook)        # process-wide and permanent, inert unless _OPENS["on"]


class _Record:
    def __enter__(self):
        _OPENS["log"] = []
        _OPENS["on"] = True
        return _OPENS["log"]

    def __exit__(self, *exc):
        _OPENS["on"] = False


def _names_restricted(path):
    return bool(B.subs_in_path(path) & set(B.RESTRICTED))


# ---------------------------------------------------------------------------------------------------------- synthetic mini-BIDS tree
T_ENV, EXTRA, LAG = 7680, 160, 6        # 120 s envelopes; EEG runs 2.5 s longer (as in the real data); neural lag 6 samples
SESS = {"001": "shortstories01", "002": "shortstories01", "003": "shortstories01", "004": "shortstories01", "005": "shortstories01",
        "019": "shortstories01", "031": "varyingStories01", "032": "varyingStories01", "051": "varyingStories05",
        "052": "varyingStories05", "053": "varyingStories05", "061": "varyingStories07", "062": "varyingStories07", "063": "varyingStories07"}
PLAN = [  # (sub, stimulus, plan): delta = clock offset (EEG sample t pairs with envelope sample t + delta), delta2 = second half
    ("001", "audiobook_1", {}), ("002", "audiobook_1", {}), ("003", "audiobook_1", {}), ("004", "audiobook_1", {}),
    ("019", "audiobook_1", {}), ("051", "audiobook_1", {}), ("061", "audiobook_1", {}),
    ("003", "audiobook_1_1", {}), ("002", "audiobook_1_artefact", {}),
    ("001", "audiobook_2_1", {}), ("002", "audiobook_2_1", {}), ("003", "audiobook_2_1", {}), ("004", "audiobook_2_1", {"delta": -300}),
    ("001", "audiobook_3", {}), ("002", "audiobook_3", {}), ("003", "audiobook_3", {"extra_T": 64}), ("004", "audiobook_3", {}),
    ("005", "audiobook_3", {"delta2": 200}), ("019", "audiobook_3", {}),
    ("001", "podcast_1", {"plant": ("Iz", 0.01)}), ("002", "podcast_1", {"delta": 3}), ("004", "podcast_1", {"plant": ("T8", 30.0)}),
    ("005", "podcast_1", {"extra_T": 64, "noise_only": True}),
    ("031", "audiobook_7_5", {}), ("032", "audiobook_7_5", {}),
    ("051", "audiobook_11_1", {}), ("052", "audiobook_11_1", {}), ("053", "audiobook_11_1", {}),
    ("061", "audiobook_13_1", {}), ("062", "audiobook_13_1", {}), ("063", "audiobook_13_1", {}),
]
STIMS = sorted({s for _, s, _ in PLAN})
DEC = "derivatives/preprocessed_eeg"
README = """# synthetic SparrKULee-like tree

Due to mistakes during recording, following recordings do not have an adequate number of triggers and can therefore not be accurately aligned with the stimulus:

1. sub-006/ses-shortstories01/eeg/sub-006_ses-shortstories01_task-listeningActive_run-06_eeg.bdf.gz
2. sub-017/ses-shortstories01/eeg/sub-017_ses-shortstories01_task-listeningActive_run-03_eeg.bdf.gz
3. sub-048/ses-varyingStories05/eeg/sub-048_ses-varyingStories05_task-listeningActive_run-04_eeg.bdf.gz
"""


def _env(rng, n):
    k = np.hanning(9)
    return np.convolve(np.abs(rng.standard_normal(n)), k / k.sum(), mode="same") + 0.05


def _response(env, T, delta, delta2, h):
    t = np.arange(T)
    i = t + np.where(t < h, delta, delta2) - LAG
    ok = (i >= 0) & (i < len(env))
    s = np.zeros(T)
    s[ok] = env[i[ok]]
    return s


def make_tree(root, seed=20261017):
    """The synthetic dataset; returns the planted truth."""
    rng = np.random.default_rng(seed)
    os.makedirs(os.path.join(root, DEC), exist_ok=True)
    stim_dir = os.path.join(root, "derivatives", "preprocessed_stimuli")
    os.makedirs(stim_dir, exist_ok=True)
    envs = {s: _env(rng, T_ENV + (37 if s == "podcast_1" else 0)) for s in STIMS}
    for s, e in envs.items():
        np.save(os.path.join(stim_dir, f"{s}_envelope.npy"), e[:, None])
    np.save(os.path.join(stim_dir, "audiobook_3_envelope-1.npy"), envs["audiobook_3"][:, None])     # duplicate: listed, never read
    for s in STIMS:
        with open(os.path.join(stim_dir, f"{s}.data_dict"), "wb") as f:                          # pickle decoy: never opened
            f.write(b"\x80\x04 not a pickle to be opened")
    with open(os.path.join(root, "README.md"), "w") as f:
        f.write(README)
    with open(os.path.join(root, "dataset_description.json"), "w") as f:
        json.dump({"Name": "synthetic", "Notes": "sub-019 is EXCLUDED: access-restricted."}, f)
    with open(os.path.join(root, "participants.tsv"), "w") as f:
        f.write("participant_id\tage\tsex\texclusion_note\n")
        for s in sorted(SESS):
            f.write(f"sub-{s}\tn/a\tF\t{'access-restricted (synthetic)' if s == '019' else 'n/a'}\n")
    gain, meta, truth, nrun = rng.standard_normal(64), {}, {"runs": {}}, collections.Counter()
    for sub, stim, plan in PLAN:
        ses = SESS[sub]
        nrun[sub] += 1
        run = f"{nrun[sub]:02d}"
        stem = f"sub-{sub}_ses-{ses}_task-listeningActive_run-{run}"
        e = envs[stim]
        T = len(e) + EXTRA + plan.get("extra_T", 0)
        h = min(len(e), T - 24) // 2
        d0 = plan.get("delta", 0)
        s = _response(e, T, d0, plan.get("delta2", d0), h)
        s = (s - s.mean()) * (0.0 if plan.get("noise_only") else 1.0)
        x = np.outer(gain * rng.uniform(0.7, 1.3), s) + 3.0 * e.std() * rng.standard_normal((64, T))
        x *= rng.uniform(5, 20, 64)[:, None]
        x -= x.mean(0, keepdims=True)                                                             # the authors' CAR-64
        if "plant" in plan:
            ch, fct = plan["plant"]
            x[C.BIOSEMI64.index(ch)] *= fct
        d = os.path.join(root, DEC, f"sub-{sub}", f"ses-{ses}")
        os.makedirs(d, exist_ok=True)
        out = f"{stem}_desc-preproc-audio-{stim}_eeg.npy"
        np.save(os.path.join(d, out), x)
        meta[f"{stem}_eeg.bdf.gz"] = [f"sub-{sub}/ses-{ses}/{out}"]
        ed = os.path.join(root, f"sub-{sub}", f"ses-{ses}", "eeg")
        os.makedirs(ed, exist_ok=True)
        cond, snr, noise = ("no_noise", "100", "eeg/n/a") if stim == "audiobook_1_1" else \
            ("in_noise", "-4", "eeg/audiobook_6_1_swn.npz.gz") if stim == "audiobook_7_5" else ("in_noise", "100.00", f"eeg/noise_{stim}.npz.gz")
        with open(os.path.join(ed, f"{stem}_events.tsv"), "w") as f:      # written for 019 too: a decoy C1 must not open
            f.write("onset\tduration\tstim_file\ttrigger_file\tnoise_file\tvideo_file\tcondition\tsnr\n")
            f.write(f"12.5\t{len(e) / 64:.2f}\teeg/{stim}.npz.gz\teeg/t_{stim}.npz.gz\t{noise}\tn/a\t{cond}\t{snr}\n")
        truth["runs"][f"sub-{sub}_ses-{ses}_run-{run}"] = dict(plan, sub=sub, stim=stim, T=T)
    first = sorted(meta)[0]
    meta[first.replace(".bdf.gz", ".bdf")] = meta[first]                                          # one output listed twice
    with open(os.path.join(root, DEC, ".save_metadata.json"), "w") as f:
        json.dump(meta, f)
    truth["rid"] = {(v["sub"], v["stim"]): k for k, v in truth["runs"].items()}
    return truth


EXPECT = {"n_runs": len(PLAN), "n_participants": len(SESS), "n_restricted_runs": 2, "n_envelopes": len(STIMS),
          "readme_flagged": B.README_FLAGGED, "ignored_stimulus_files": ("audiobook_3_envelope-1.npy",),
          "save_metadata_entries": len(PLAN) + 1, "outputs_listed_twice": 1, "artefact_runs": (("002", "shortstories01", "02"),)}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    base = tmp_path_factory.mktemp("m2a")
    src, out = str(base / "sparrkulee_src"), str(base / "cache")
    truth = make_tree(src)
    logs = {}
    with _Record() as lg:
        table = B.stage_c1(src, out, expect=EXPECT, hash_eeg=True, log=lambda m: None)
    logs["C1"] = list(lg)
    with _Record() as lg:
        B.stage_c2(None, out, log=lambda m: None)
    logs["C2"] = list(lg)
    with _Record() as lg:
        res = B.stage_c4(None, out, log=lambda m: None)
    logs["C4"] = list(lg)
    d = os.path.join(out, B.COHORT)
    audit = B.read_audit(out, table)
    return {"src": src, "out": out, "dir": d, "truth": truth, "table": table, "audit": audit, "res": res, "logs": logs,
            "base": base}


def _rid(b, sub, stim):
    return b["truth"]["rid"][(sub, stim)]


# ---------------------------------------------------------------------------------------------------------- C1
def test_c1_run_table_roles_and_sources(built):
    t, truth = built["table"], built["truth"]
    runs = {r["run_id"]: r for r in t["runs"]}
    assert t["schema"] == B.SCHEMA_TABLE and t["contract"] == C.CONTRACT and set(runs) == set(truth["runs"])
    role = lambda sub, stim: runs[_rid(built, sub, stim)]["role"]   # noqa: E731
    assert role("001", "audiobook_1") == "fit" and role("051", "audiobook_1") == role("061", "audiobook_1") == "holdout_seen_content"
    assert role("002", "audiobook_1_artefact") == "control_artefact" and role("003", "audiobook_1_1") == "fit"
    assert role("051", "audiobook_11_1") == "dev" and role("061", "audiobook_13_1") == "bridge_cal" and role("031", "audiobook_7_5") == "fit"
    assert role("019", "audiobook_1") == role("019", "audiobook_3") == "restricted"
    assert t["counts"]["runs_by_role"] == {"bridge_cal": 3, "control_artefact": 1, "dev": 3, "fit": 20, "holdout_seen_content": 2,
                                           "restricted": 2}
    for rid, r in runs.items():                                       # headers, envelope lengths, declared families, sources
        assert r["T_eeg"] == truth["runs"][rid]["T"] and r["T_env"] == T_ENV + (37 if r["stimulus"] == "podcast_1" else 0)
        assert r["family_name"] == "sparrkulee:" + ("audiobook_1" if r["stimulus"].startswith("audiobook_1") and r["stimulus"] in
                                                    B.DECLARED_FAMILY else r["stimulus"])
        if r["restricted"]:                                           # file name and .npy header only
            assert r["events"] is None and r["sha256"] == {"eeg": None, "events": None} and r["presentation_key"] is None
            assert r["flags"] == ["restricted_participant"] and r["raw_bdf_present"] is None
        else:
            assert len(r["sha256"]["eeg"]) == len(r["sha256"]["events"]) == 64 and r["events"]["stim_file"].endswith(f"{r['stimulus']}.npz.gz")
    assert runs[_rid(built, "003", "audiobook_1")]["family_offset_declared"] == 0
    assert runs[_rid(built, "003", "audiobook_1_1")]["family_offset_declared"] == 1711
    assert runs[_rid(built, "002", "audiobook_1_artefact")]["family_offset_declared"] is None
    nn = runs[_rid(built, "003", "audiobook_1_1")]                    # 'eeg/n/a' means no noise file
    assert nn["noise_condition"] == "no_noise" and nn["noise_file"] is None and nn["snr"] == 100.0
    assert nn["presentation_key"] == "sparrkulee:audiobook_1_1|no_noise|snr=100|noise=none"
    nz = runs[_rid(built, "031", "audiobook_7_5")]
    assert nz["snr"] == -4.0 and nz["presentation_key"] == "sparrkulee:audiobook_7_5|in_noise|snr=-4|noise=audiobook_6_1_swn.npz.gz"
    anom = {rid for rid, r in runs.items() if r["structural"]["anomalous"]}  # structural-anomaly rule: |T - mode of co-listeners| > 8
    assert anom == {_rid(built, "003", "audiobook_3"), _rid(built, "005", "podcast_1")}
    s = runs[_rid(built, "003", "audiobook_3")]["structural"]
    assert s["delta"] == 64 and s["T_eeg_mode"] == T_ENV + EXTRA and s["n_colisteners"] == 4          # restricted 019 not counted
    assert runs[_rid(built, "003", "audiobook_1_1")]["structural"] == {"n_colisteners": 0, "T_eeg_mode": None, "delta": None, "anomalous": False}
    assert t["restricted"] == sorted(B.RESTRICTED) and t["restricted_sources"]["participants_tsv"] == ["019"]
    assert t["restricted_sources"]["dataset_description"] == ["019"] and t["ignored_stimulus_files"] == ["audiobook_3_envelope-1.npy"]
    assert len(t["save_metadata"]["outputs_listed_twice"]) == 1 and t["save_metadata"]["duplicate_json_keys"] == []
    assert [tuple(f) for f in t["readme_flagged"]] == sorted(B.README_FLAGGED) and t["readme_flagged_absent"]
    assert {e["stimulus"] for e in t["envelopes"]} == set(STIMS) and all(len(e["sha256"]) == 64 for e in t["envelopes"])
    cov = t["counts"]["coverage_before_audit"]
    assert cov["dev"]["participants"] == 3 and cov["dev"]["presentations_ge2"] == 1 and cov["fit"]["presentations_ge2"] == 5


def test_c1_readme_flagged_and_role_disjointness(built, tmp_path, monkeypatch):
    src = built["src"]
    readme = os.path.join(src, "README.md")
    with open(readme) as f:
        orig = f.read()
    try:                                                              # a README-flagged run that is present must stop C1
        with open(readme, "w") as f:
            f.write(orig + "4. sub-001/ses-shortstories01/eeg/sub-001_ses-shortstories01_task-listeningActive_run-01_eeg.bdf.gz\n")
        with pytest.raises(AssertionError, match="README-flagged runs present"):
            B.stage_c1(src, str(tmp_path / "o1"), expect=None, hash_eeg=False, log=lambda m: None)
    finally:
        with open(readme, "w") as f:
            f.write(orig)
    with _Record() as lg:                                             # the real-data expectations do not hold for this tree: the
        with pytest.raises(AssertionError, match="restricted participants from participants_tsv"):   # restricted sources fail
            B.stage_c1(src, str(tmp_path / "o2"), expect=B.EXPECT_REAL, hash_eeg=False, log=lambda m: None)   # first, before any
    assert not [o for o in lg if o.path.endswith(("_events.tsv", ".npy"))]                                # per-run file is read
    with pytest.raises(AssertionError, match="n_runs"):
        B.stage_c1(src, str(tmp_path / "o2"), expect={k: v for k, v in B.EXPECT_REAL.items() if k != "restricted"}, hash_eeg=False,
                   log=lambda m: None)
    orig_family = B.family_of                                         # a family heard in two donor roles must stop C1: make
    monkeypatch.setattr(B, "family_of", lambda s: ("podcast_1", 0, "own") if s == "audiobook_7_5" else orig_family(s))
    monkeypatch.setitem(B.SESSION_ROLE, "varyingStories01", "dev")    # audiobook_7_5 (vS01) the podcast_1 family, vS01 dev
    with pytest.raises(AssertionError, match="content families shared across donor roles"):
        B.stage_c1(src, str(tmp_path / "o3"), expect=None, hash_eeg=False, log=lambda m: None)
    assert not os.path.exists(str(tmp_path / "o3" / "sparrkulee" / B.RUNS_TABLE))


def test_c1_64hz_consistency_rule(built, tmp_path, monkeypatch):
    t = built["table"]                                                # the synthetic runs: 160 or 224 samples longer
    assert t["counts"]["T_tail_range"] == [EXTRA, EXTRA + 64] and all(r["T_tail"] == r["T_eeg"] - r["T_env"] for r in t["runs"])
    assert t["rules"]["rate_check"] == {"rule": "0 <= T_eeg - T_env <= min(2100, 0.05 T_env)", "tail_max": 2100, "tail_frac": 0.05}
    orig = B._envelopes

    def env_len(stim, f):
        def patched(src):
            envs, ignored = orig(src)
            envs[stim] = dict(envs[stim], T_env=f(envs[stim]["T_env"]))
            return envs, ignored
        return patched
    for f, what in ((lambda n: 2 * n, "an envelope at 128 Hz"), (lambda n: n // 2, "EEG at 128 Hz"),
                    (lambda n: n - 300, "a tail beyond 0.05 T_env"), (lambda n: n + EXTRA + 1, "EEG shorter than its envelope")):
        monkeypatch.setattr(B, "_envelopes", env_len("audiobook_2_1", f))
        with pytest.raises(ValueError, match="not EEG and envelope at the same 64 Hz"):
            B.stage_c1(built["src"], str(tmp_path / "o"), expect=None, hash_eeg=False, log=lambda m: None)
        assert not os.path.exists(tmp_path / "o"), what                 # nothing written, not even the directory
    monkeypatch.setattr(B, "_envelopes", env_len("audiobook_2_1", lambda n: n - 100))   # 260 <= 0.05 x 7580: accepted
    t2 = B.stage_c1(built["src"], str(tmp_path / "o"), expect=None, hash_eeg=False, log=lambda m: None)
    assert {r["T_tail"] for r in t2["runs"] if r["stimulus"] == "audiobook_2_1"} == {EXTRA + 100}


# ---------------------------------------------------------------------------------------------------------- restricted guard
def test_restricted_participants_never_opened(built, tmp_path):
    logs, src = built["logs"], built["src"]
    c1_restricted = [o for o in logs["C1"] if _names_restricted(o.path)]
    assert c1_restricted and all(o.hdr for o in c1_restricted)        # C1: only the header reader touches them, read-only and
    assert all(o.mode is None and o.flags & os.O_ACCMODE == os.O_RDONLY for o in c1_restricted)  # through os.open (unbuffered)
    assert {os.path.basename(o.path) for o in c1_restricted} == {os.path.basename(r["file"]) for r in built["table"]["runs"]
                                                                 if r["restricted"]}
    for stage in ("C2", "C4"):                                        # C2 and C4: never opened, not even the header
        assert not [o for o in logs[stage] if _names_restricted(o.path)], stage
        assert any(o.path.endswith("_eeg.npy") for o in logs[stage])  # (the hook did see the other EEG files)
    for stage, lg in logs.items():                                    # never: pickles, the duplicate envelope, raw stimuli
        assert not [o for o in lg if o.path.endswith((".data_dict", ".pkl", ".npz.gz", "_envelope-1.npy"))], stage
        assert not [o for o in lg if "/stimuli/" in o.path], stage
    dec = next(r for r in built["table"]["runs"] if r["restricted"])
    path = os.path.join(src, dec["file"])
    with _Record() as lg:                                             # the guard raises before any open
        with pytest.raises(B.RestrictedAccess):
            B._load_array(path, B.restricted_set(built["table"]))
        with pytest.raises(B.RestrictedAccess):
            B.guard(os.path.join(src, DEC, "sub-019"), B.RESTRICTED)
        with pytest.raises(B.RestrictedAccess):
            B.stage_c2(None, built["out"], runs=[dec["run_id"]], log=lambda m: None)
    assert not [o for o in lg if _names_restricted(o.path)] and not [o for o in lg if o.path.endswith(".npy")]
    assert B.subs_in_path("/x/sub-019/ses-a/sub-019_ses-a_eeg.npy") == {"019"} and not B.subs_in_path("/x/sub-0190x/y")
    assert {"020", "026"} <= B.restricted_set({"restricted": []}) and "777" in B.restricted_set({"restricted": ["777"]})
    res = built["res"]                                                # hard exclusion in the outputs
    assert {p["sub"] for p in res["participants"]}.isdisjoint(B.RESTRICTED)
    rr = [r for r in res["runs"] if r["sub"] in B.RESTRICTED]
    assert len(rr) == 2 and all(r["role"] == "restricted" and r["row_offset"] is None and r["slab"] is None and r["segment_starts"] == []
                                and r["source_sha256"] is None and r["audit"]["clock"] == "not_audited" and r["masked"] == []
                                and r["raw_file"] == r["file"] and r["presentation"] is None for r in rr)
    assert {built["audit"][r["run_id"]]["class"] for r in rr} == {"not_audited"} and all(not built["audit"][r["run_id"]]["refs"] for r in rr)
    assert not any(set(q["refs"]) & {r["run_id"] for r in rr} for q in built["audit"].values())


def _rchar():
    with open("/proc/thread-self/io", "rb") as f:
        b = f.read()
    return int(next(x for x in b.split(b"\n") if x.startswith(b"rchar:")).split()[1]), len(b)


def _received(fn):
    """(bytes this thread received from read syscalls while fn ran, fn's result): /proc/thread-self/io rchar, the probe's own
    read removed. Independent of how the reader is written, so it sees a user-space read-ahead buffer."""
    r0, n0 = _rchar()
    res = fn()
    r1, _ = _rchar()
    return r1 - r0 - n0, res


def _raises(fn, exc):
    try:
        fn()
    except exc as e:
        return e
    raise AssertionError(f"no {exc.__name__}")


def _buffered_header(path):                                           # what C1 used to do: a buffered open()
    with open(path, "rb") as f:
        np.lib.format.read_magic(f)
        np.lib.format.read_array_header_1_0(f)


def test_npy_header_reader_receives_only_the_header_bytes(tmp_path, monkeypatch):
    if not os.path.exists("/proc/thread-self/io"):
        pytest.skip("no per-thread I/O accounting on this system")
    assert _received(lambda: None)[0] == 0                            # the probe itself is exact
    p = str(tmp_path / "x.npy")
    np.save(p, np.zeros((64, 20000)))                                 # 10 MB of array bytes behind a 128-byte header
    n_buf, _ = _received(lambda: _buffered_header(p))                 # positive control: a buffered open pulls a whole block
    n, h = _received(lambda: B._read_npy_header(p))
    assert h["header_bytes"] == h["bytes_read"] == n == 128 < n_buf, (n, n_buf)
    assert h["shape"] == [64, 20000] and h["dtype"] == "<f8" and h["consistent"] and h["version"] == [1, 0] and not h["object"]
    asked, real_read = [], os.read                                    # each os.read asks for exactly the missing bytes
    monkeypatch.setattr(os, "read", lambda fd, k: asked.append(k) or real_read(fd, k))
    B._read_npy_header(p)
    monkeypatch.undo()
    assert asked == [8, 2, 118]
    p2 = str(tmp_path / "v2.npy")                                     # a version 2.0 header (4-byte length field)
    with open(p2, "wb") as f:
        np.lib.format.write_array(f, np.zeros((3, 5), np.float32), version=(2, 0))
    n, h = _received(lambda: B._read_npy_header(p2))
    assert h["version"] == [2, 0] and n == h["header_bytes"] and h["header_bytes"] % 64 == 0 and h["shape"] == [3, 5]
    assert h["dtype"] == "<f4" and h["consistent"]
    p3 = str(tmp_path / "obj.npy")                                    # an object array: flagged from the header alone; the
    hdr = b"{'descr': '|O', 'fortran_order': False, 'shape': (4,), }"  # pickle bytes behind it never reach the process
    hdr += b" " * (63 - (10 + len(hdr)) % 64) + b"\n"
    with open(p3, "wb") as f:
        f.write(B.NPY_MAGIC + b"\x01\x00" + len(hdr).to_bytes(2, "little") + hdr + b"\x80\x04 pickle bytes, never read " * 400)
    n, h = _received(lambda: B._read_npy_header(p3))
    assert h["object"] and not h["consistent"] and n == h["header_bytes"] == 10 + len(hdr)
    bad = {"not_npy": (b"PK\x03\x04" + b"\x00" * 4000, 8, "not a .npy"),        # malformed files: refused, reading no more
           "truncated": (B.NPY_MAGIC + b"\x01\x00" + (200).to_bytes(2, "little") + b"{'descr'", 18, "end of file"),
           "huge_header": (B.NPY_MAGIC + b"\x02\x00" + (10 ** 9).to_bytes(4, "little") + b"x" * 4000, 12, "refused unread"),
           "version_9": (B.NPY_MAGIC + b"\x09\x00" + b"\x00" * 4000, 8, "unsupported")}
    for k, (data, n_exp, msg) in bad.items():
        q = str(tmp_path / f"{k}.npy")
        with open(q, "wb") as f:
            f.write(data)
        n, e = _received(lambda: _raises(lambda: B._read_npy_header(q), ValueError))
        assert n == n_exp and msg in str(e), (k, n, e)


def test_c1_receives_only_the_header_bytes_of_restricted_files(built, tmp_path, monkeypatch):
    fd_path, got = {}, collections.Counter()
    real_open, real_read = os.open, os.read

    def op(path, flags, mode=0o777, *, dir_fd=None):
        fd = real_open(path, flags, mode, dir_fd=dir_fd)
        fd_path[fd] = os.fspath(path)
        return fd

    def rd(fd, n):
        b = real_read(fd, n)
        got[fd_path.get(fd, f"fd {fd}")] += len(b)
        return b
    monkeypatch.setattr(os, "open", op)
    monkeypatch.setattr(os, "read", rd)
    with _Record() as lg:
        t = B.stage_c1(built["src"], str(tmp_path / "o"), expect=EXPECT, hash_eeg=True, log=lambda m: None)
    monkeypatch.undo()
    rr = [r for r in t["runs"] if r["restricted"]]
    paths = {os.path.join(built["src"], r["file"]): r for r in rr}
    assert rr and all(got[p] == r["npy_header"]["header_bytes"] == r["npy_header"]["bytes_read"] == 128 for p, r in paths.items())
    assert all(p.endswith(".npy") for p in got)                       # only the header reader uses os.read
    opened = [o for o in lg if _names_restricted(o.path)]             # and it opened each restricted file once, read-only
    assert sorted(o.path for o in opened) == sorted(paths) and all(o.hdr and o.mode is None for o in opened)


def test_participant_restricted_only_by_the_notes_is_never_opened(built, tmp_path):
    src = built["src"]
    desc = os.path.join(src, "dataset_description.json")
    with open(desc) as f:
        orig = f.read()
    out = str(tmp_path / "o")
    try:                                                              # sub-005 is named only in the Notes (as the host does)
        with open(desc, "w") as f:
            json.dump({"Name": "synthetic", "Notes": "sub-019 and sub-005 are EXCLUDED: access-restricted."}, f)
        with _Record() as lg0:                                        # a restricted-set expectation fails before the run loop
            _raises(lambda: B.stage_c1(src, str(tmp_path / "o0"), expect={"restricted": ("019",)}, hash_eeg=True,
                                       log=lambda m: None), AssertionError)
        assert not [o for o in lg0 if o.path.endswith(("_events.tsv", "_eeg.npy"))]
        with _Record() as lg1:
            t = B.stage_c1(src, out, expect=None, hash_eeg=True, log=lambda m: None)
    finally:
        with open(desc, "w") as f:
            f.write(orig)
    assert t["restricted"] == ["005", "019", "020", "021", "022", "026"] and t["restricted_sources"]["dataset_description"] == ["005", "019"]
    r5 = [r for r in t["runs"] if r["sub"] == "005"]
    assert len(r5) == 2 and all(r["restricted"] and r["role"] == "restricted" and r["events"] is None and r["presentation_key"] is None
                                and r["sha256"] == {"eeg": None, "events": None} for r in r5)
    assert next(p for p in t["participants"] if p["sub"] == "005")["restricted"]
    is5 = lambda path: "005" in B.subs_in_path(path)                   # noqa: E731
    seen = [o for o in lg1 if is5(o.path)]
    assert len(seen) == 2 and all(o.hdr and o.mode is None and o.path.endswith("_eeg.npy") for o in seen)   # headers only
    with _Record() as lg2:
        B.stage_c2(None, out, log=lambda m: None)
        res = B.stage_c4(None, out, log=lambda m: None)
    assert not [o for o in lg2 if is5(o.path)]
    a = B.read_audit(out, t)
    assert all(a[r["run_id"]]["class"] == "not_audited" for r in r5)
    assert not any(set(q["refs"]) & {r["run_id"] for r in r5} for q in a.values())
    assert "005" not in {p["sub"] for p in res["participants"]}
    assert all(r["row_offset"] is None and r["role"] == "restricted" for r in res["runs"] if r["sub"] == "005")


# ---------------------------------------------------------------------------------------------------------- C2
def test_lagged_pearson_matches_direct_correlation():
    rng = np.random.default_rng(3)
    a, b = rng.standard_normal(3000), rng.standard_normal(3200)
    b[100:2900] += 0.5 * a[50:2850]                                   # a[t] pairs with b[t + 50]
    for lo, hi in ((0, 1500), (1500, 3000), (200, 2600)):
        taus, r, N = B.lagged_pearson(a, b, lo, hi, search=700)
        for tau in (-700, -333, -1, 0, 1, 50, 699, 700):
            t0, t1 = max(lo, -tau), min(hi, len(b) - tau)
            ref = np.corrcoef(a[t0:t1], b[t0 + tau:t1 + tau])[0, 1]
            assert abs(r[tau + 700] - ref) < 1e-9 and N[tau + 700] == t1 - t0, (lo, hi, tau)
        assert taus[np.nanargmax(r)] == 50
    t_, p_, z = B.peak_and_z(taus, r)
    assert t_ == 50 and z > 10


def test_classify_rule_boundaries():
    assert B.classify([0, 0], [9.0, 9.0]) == ("aligned", None) and B.classify([-4, 4], [5.0, 5.0])[0] == "aligned"
    assert B.classify([-566, -566], [9.0, 8.5])[0] == "misaligned" and B.classify([5, 9], [6.0, 6.0])[0] == "misaligned"
    assert B.classify([2, 6], [6.0, 6.0])[0] == "unverifiable"        # |mean| = 4 is not > 4, and |6| > 4 is not aligned
    assert B.classify([0, 200], [9.0, 9.0]) == ("unverifiable", "lags differ between halves")
    assert B.classify([-300, -300], [4.99, 9.0])[0] == "unverifiable"  # one half not measurable: never excluded
    assert B.classify([0, 0], [None, 9.0])[0] == "unverifiable"


def test_c2_alignment_audit_on_planted_offsets(built):
    a, t = built["audit"], {r["run_id"]: r for r in built["table"]["runs"]}
    assert set(a) == set(t) and all(set(q) >= {"run", "refs", "tau", "z", "class"} for q in a.values())
    assert all(len(q["tau"]) == len(q["z"]) == 2 for q in a.values())
    for rid, q in a.items():                                          # references: same stimulus, other participant, not restricted,
        r = t[rid]                                                    # not structurally anomalous, at most 8, sorted
        assert q["refs"] == [x["run_id"] for x in B._refs_for(r, B._audit_pool(built["table"], r["stimulus"]))] or r["restricted"]
        for ref in q["refs"]:
            assert t[ref]["stimulus"] == r["stimulus"] and t[ref]["sub"] != r["sub"] and not t[ref]["restricted"]
            assert not t[ref]["structural"]["anomalous"]
        assert len(q["refs"]) <= B.MAX_REFS
    cls = lambda sub, stim: a[_rid(built, sub, stim)]                 # noqa: E731
    for sub, stim in (("001", "audiobook_1"), ("061", "audiobook_1"), ("001", "audiobook_2_1"), ("003", "audiobook_3"),
                      ("051", "audiobook_11_1"), ("063", "audiobook_13_1"), ("004", "podcast_1")):
        q = cls(sub, stim)
        assert q["class"] == "aligned" and all(abs(v) <= 1 for v in q["tau"]) and min(q["z"]) >= B.Z_MEAS, (sub, stim, q)
    q = cls("002", "podcast_1")                                       # a +3-sample clock offset is within tolerance
    assert q["class"] == "aligned" and all(abs(v - 3) <= 1 for v in q["tau"])
    q = cls("004", "audiobook_2_1")                                   # planted -300 in both halves
    assert q["class"] == "misaligned" and all(abs(v + 300) <= 1 for v in q["tau"]) and min(q["z"]) >= B.Z_MEAS
    dg = q["diagnostic"]                                              # the scout's +-10 s statistics, descriptive only
    assert dg["search_samples"] == 640 and abs(dg["full"]["tau"] + 300) <= 1 and all(abs(hh["tau"] + 300) <= 1 for hh in dg["halves"])
    assert dg["full"]["offpeak_absmax"] == dg["full"]["r"] and dg["full"]["r_at_0"] < 0.2 < dg["full"]["r"]
    dg = cls("001", "audiobook_1")["diagnostic"]
    assert abs(dg["full"]["tau"]) <= 1 and dg["full"]["r"] > dg["full"]["offpeak_absmax"] and len(dg["halves"]) == 2
    q = cls("005", "audiobook_3")                                     # halves at 0 and +200: kept, unverifiable
    assert q["class"] == "unverifiable" and abs(q["tau"][0]) <= 1 and abs(q["tau"][1] - 200) <= 1 and q["reason"] == "lags differ between halves"
    q = cls("005", "podcast_1")                                       # no stimulus tracking: unmeasurable, never "misaligned"
    assert q["class"] == "unverifiable" and max(q["z"]) < B.Z_MEAS and q["reason"].startswith("half not measurable")
    for sub, stim in (("003", "audiobook_1_1"), ("002", "audiobook_1_artefact"), ("031", "audiobook_7_5")):
        q = cls(sub, stim)
        assert q["class"] == "unverifiable" and q["reason"] == "fewer than 2 eligible co-listeners" and q["tau"] == [None, None]
    assert len(cls("031", "audiobook_7_5")["refs"]) == 1
    assert cls("001", "audiobook_1")["refs"] == [_rid(built, s, "audiobook_1") for s in ("002", "003", "004", "051", "061")]
    assert _rid(built, "003", "audiobook_3") not in cls("001", "audiobook_3")["refs"]     # structural anomaly: never a reference
    assert set(cls("004", "audiobook_3")["sha256"]) == {_rid(built, "004", "audiobook_3")} | set(cls("004", "audiobook_3")["refs"])
    meta = B._read_json(os.path.join(built["dir"], B.AUDIT_META))
    assert meta["classes"] == dict(sorted(collections.Counter(q["class"] for q in a.values()).items()))
    assert [m["run"] for m in meta["misaligned"]] == [_rid(built, "004", "audiobook_2_1")] and meta["rule"]["search_samples"] == 2560
    with open(os.path.join(built["dir"], B.AUDIT)) as f:              # one sorted record per run of the table
        assert [json.loads(line)["run"] for line in f] == sorted(t)


def test_c2_rerun_reads_nothing_and_stale_markers_are_recomputed(built, tmp_path):
    with _Record() as lg:
        B.stage_c2(None, built["out"], log=lambda m: None)
    assert not [o for o in lg if o.path.endswith(".npy")]
    with open(os.path.join(built["dir"], B.AUDIT)) as f:
        assert {json.loads(line)["run"]: json.loads(line) for line in f} == built["audit"]
    d4 = tmp_path / "cache4" / B.COHORT                               # markers of another run table are never reused
    shutil.copytree(os.path.join(built["dir"], B.C2_DONE), d4 / B.C2_DONE)
    t = B._read_json(os.path.join(built["dir"], B.RUNS_TABLE))
    t["note"] = "edited"
    B._write_json(str(d4 / B.RUNS_TABLE), t)
    with _Record() as lg:
        B.stage_c2(None, str(tmp_path / "cache4"), runs=[_rid(built, "051", "audiobook_11_1")], log=lambda m: None)
    assert any(o.path.endswith("_eeg.npy") for o in lg)
    new = B._read_json(str(d4 / B.C2_DONE / f"{_rid(built, '051', 'audiobook_11_1')}.json"))
    old = built["audit"][_rid(built, "051", "audiobook_11_1")]
    assert new["runs_table_sha256"] != old["runs_table_sha256"]
    assert {k: v for k, v in new.items() if k != "runs_table_sha256"} == {k: v for k, v in old.items() if k != "runs_table_sha256"}
    assert not os.path.exists(d4 / B.AUDIT)                           # the other markers are stale: the audit is incomplete


def test_c2_audit_records_share_one_schema_and_reproduce_their_class(built):
    a, t = built["audit"], {r["run_id"]: r for r in built["table"]["runs"]}
    assert {c: sum(q["class"] == c for q in a.values()) > 0 for c in B.CLASSES} == {c: True for c in B.CLASSES}
    tsha = B._sha256_file(os.path.join(built["dir"], B.RUNS_TABLE))
    for rid, q in a.items():                                          # one key set for every class (not_audited, < 2 references,
        assert tuple(sorted(q)) == tuple(sorted(B.AUDIT_KEYS)), rid    # decoded) and the provenance fields everywhere
        assert q["runs_table_sha256"] == tsha and q["builder_sha256"] == B._code_sha()
        assert q["structural_anomaly"] == (None if t[rid]["restricted"] else t[rid]["structural"]["anomalous"])
        assert (q["diagnostic"] is None) == (q["class"] == "not_audited" or q["n_refs"] < B.MIN_REFS), rid
        if None not in q["tau"]:                                      # the stored values reproduce the class exactly
            assert B.classify(q["tau"], q["z"])[0] == q["class"], rid
    assert any(v != round(v, 6) for q in a.values() for v in q["z"] if v is not None)   # z stored as computed, not rounded
    assert B.classify([0, 0], [4.9999996, 9.0])[0] == "unverifiable"  # (a rounded 5.0 would have said aligned)
    with pytest.raises(KeyError, match="outside AUDIT_KEYS"):
        B._audit_record(t[next(iter(t))], tsha, "x", extra=1, **{"class": "aligned"})


# ---------------------------------------------------------------------------------------------------------- C4
def _expected_rows(built, sub):
    """Independent recomputation of one participant's cache rows (scipy directly, the §2.1 / §6.2 chain)."""
    sos = signal.butter(4, [1, 20], btype="band", fs=64, output="sos")
    assert np.array_equal(sos, C.eeg_sos()[0])
    rr = [r for r in built["res"]["runs"] if r["sub"] == sub]
    Y, M = {}, {}
    for r in rr:
        x = np.load(os.path.join(built["src"], r["file"]), allow_pickle=False)
        y = signal.sosfiltfilt(sos, x, axis=1, padtype="odd", padlen=min(256, x.shape[1] - 1))
        sd = y.std(1)
        M[r["run_id"]] = (sd > 10 * np.median(sd)) | (sd < 0.1 * np.median(sd))
        Y[r["run_id"]] = y
    mu, sdv = np.zeros(64), np.zeros(64)
    for c in range(64):
        v = np.concatenate([Y[k][c, 128:Y[k].shape[1] - 128] for k in Y if not M[k][c]])
        mu[c], sdv[c] = v.mean(), v.std()
    out = {}
    for r in rr:
        z = (Y[r["run_id"]] - mu[:, None]) / sdv[:, None]
        z[M[r["run_id"]]] = 0
        out[r["run_id"]] = (z.T.astype(np.float16), [C.BIOSEMI64[c] for c in np.flatnonzero(M[r["run_id"]])])
    return out, mu, sdv


def test_c4_time_major_float16_cache(built):
    d, res = built["dir"], built["res"]
    X = np.load(os.path.join(d, B.CACHE), mmap_mode="r")
    cached = sorted((r for r in res["runs"] if r["row_offset"] is not None), key=lambda r: r["row_offset"])
    N = sum(r["T_eeg"] for r in cached)
    assert X.dtype == np.float16 and X.shape == (N, 64) and X.flags.c_contiguous and res["cohort_info"]["n_rows"] == N
    assert np.isfinite(np.asarray(X)).all() and not os.path.exists(os.path.join(d, B.PARTIAL))
    assert cached[0]["row_offset"] == 0 and all(a["row_offset"] + a["T_eeg"] == b["row_offset"] for a, b in zip(cached, cached[1:]))
    slabs = res["cohort_info"]["role_slabs"]
    order = [s for s in B.SLABS if s in slabs]
    assert order == ["fit", "dev", "bridge_cal", "holdout_seen_content", "control_artefact", "excluded_rule"]
    assert [slabs[s][0] for s in order] == [0] + [slabs[s][1] for s in order[:-1]] and slabs[order[-1]][1] == N
    for r in cached:                                                  # each run inside its own slab; a 38 x 64 window is contiguous
        lo, hi = slabs[r["slab"]]
        assert lo <= r["row_offset"] and r["row_offset"] + r["T_eeg"] <= hi and r["slab"] == r["role"]
    w = X[cached[0]["row_offset"] + 200:cached[0]["row_offset"] + 238]
    assert w.shape == (38, 64) and w.flags.c_contiguous and w.nbytes == 4864
    for sub in ("001", "004", "005"):                                 # planted QC channels, an excluded run, a structural run
        exp, mu, sdv = _expected_rows(built, sub)
        part = next(p for p in res["participants"] if p["sub"] == sub)
        assert np.allclose(part["mu"]["A"], mu, rtol=1e-9, atol=1e-9) and np.allclose(part["sd_prez"]["A"], sdv, rtol=1e-9)
        for rid, (z16, masked) in exp.items():
            r = next(q for q in res["runs"] if q["run_id"] == rid)
            got = np.asarray(X[r["row_offset"]:r["row_offset"] + r["T_eeg"]])
            assert r["masked"] == masked and got.shape == (r["T_eeg"], 64)
            assert np.abs(got.astype(np.float64) - z16.astype(np.float64)).max() <= 2e-3 * max(1.0, np.abs(z16).max()), rid
            for ch in masked:
                assert not got[:, C.BIOSEMI64.index(ch)].any()
    runs = {r["run_id"]: r for r in res["runs"]}
    assert runs[_rid(built, "001", "podcast_1")]["masked"] == ["Iz"] and runs[_rid(built, "004", "podcast_1")]["masked"] == ["T8"]
    assert res["cohort_info"]["masked_cells"] == 2
    g0, g1 = C.GUARDS["sparrkulee"]
    for p in res["participants"]:                                     # z per participant x channel over guarded unmasked cells
        mine = [r for r in cached if r["sub"] == p["sub"]]
        for c in range(0, 64, 9):
            v = np.concatenate([np.asarray(X[r["row_offset"] + g0:r["row_offset"] + r["T_eeg"] - g1, c], dtype=np.float64)
                                for r in mine if C.BIOSEMI64[c] not in r["masked"]])
            assert abs(v.mean()) < 5e-3 and abs(v.std() - 1) < 5e-3, (p["sub"], c)
    assert res["sanity"]["car_not_ok"] == sorted([_rid(built, "001", "podcast_1"), _rid(built, "004", "podcast_1")])
    assert all(runs[k]["car_ratio"] < 1e-9 for k in runs if runs[k]["row_offset"] is not None and k not in res["sanity"]["car_not_ok"])


def test_c4_roles_exclusions_and_segments(built):
    res, runs = built["res"], {r["run_id"]: r for r in built["res"]["runs"]}
    rid = lambda s, st: _rid(built, s, st)                            # noqa: E731
    mis, anom = runs[rid("004", "audiobook_2_1")], runs[rid("005", "podcast_1")]
    assert mis["role"] == mis["slab"] == "excluded_rule" and mis["flags"] == ["clock_misaligned"] and mis["row_offset"] is not None
    assert mis["role_c1"] == "fit" and runs[rid("051", "audiobook_1")]["role_c1"] == runs[rid("051", "audiobook_1")]["role"]
    assert anom["role"] == "excluded_rule" and anom["flags"] == ["structural_anomaly_unverified_clock"]
    kept = runs[rid("003", "audiobook_3")]                            # structural anomaly with an aligned clock: kept
    assert kept["role"] == "fit" and kept["flags"] == [] and kept["structural"]["anomalous"] and kept["audit"]["clock"] == "aligned"
    inc = runs[rid("005", "audiobook_3")]                             # inconsistent halves, no structural anomaly: kept
    assert inc["role"] == "fit" and inc["flags"] == [] and inc["audit"]["clock"] == "unverifiable"
    assert {k for k, r in runs.items() if r["flags"]} == {mis["run_id"], anom["run_id"]}
    assert collections.Counter(r["role"] for r in runs.values()) == {"fit": 18, "dev": 3, "bridge_cal": 3, "holdout_seen_content": 2,
                                                                     "control_artefact": 1, "excluded_rule": 2, "restricted": 2}
    for r in runs.values():
        if r["row_offset"] is not None:
            assert r["segment_starts"] == C.segment_starts(r["T_env"], r["T_eeg"], "sparrkulee").tolist() and r["segment_starts"]
            assert all(s % 32 == 0 and s >= 128 and s + C.SPAN_EEG <= r["T_eeg"] - 128 and s + C.SPAN_ENV <= r["T_env"] - 41
                       for s in r["segment_starts"])
    parts = {p["sub"]: p for p in res["participants"]}
    assert parts["051"]["role"] == "dev" and parts["061"]["role"] == "bridge_cal" and parts["001"]["donor"]
    assert set(parts) == set(SESS) - {"019"}
    pres = res["presentations"]
    assert [p["id"] for p in pres] == list(range(len(pres))) and len(pres) == len(STIMS)
    for r in runs.values():
        if r["presentation"] is not None:
            p = pres[r["presentation"]]
            assert p["key"] == r["presentation_key"] and p["stream"] == r["stream"] and p["family"] == r["family"] and p["condition"] == "listeningActive"
    fam = {f["name"]: f for f in res["families"]}
    ab1 = [p for p in pres if p["family_name"] == "sparrkulee:audiobook_1"]
    assert {p["stimulus"] for p in ab1} == {"audiobook_1", "audiobook_1_1", "audiobook_1_artefact"}
    assert sorted(fam["sparrkulee:audiobook_1"]["members"]) == sorted(p["id"] for p in ab1) and fam["sparrkulee:audiobook_1"]["basis"] == "declared"
    assert all(f["basis"] == "own" for n, f in fam.items() if n != "sparrkulee:audiobook_1") and all(n.startswith("sparrkulee:") for n in fam)
    art = next(p for p in pres if p["stimulus"] == "audiobook_1_artefact")
    assert art["family_offset"] is None and not art["offset_known"] and next(p for p in pres if p["stimulus"] == "audiobook_1_1")["family_offset"] == 1711


def test_c4_stream_and_run_tables_match_fixture_schema(built, tmp_path):
    fx = FX.make_synthetic_manifest(tmp_path / "fixture")
    info = fx["manifest"]["cohorts"]["sparrkulee"]
    f_runs = B._read_json(os.path.join(fx["root"], info["dir"], info["table"]))
    f_streams = B._read_json(os.path.join(fx["root"], info["dir"], info["streams"]))["streams"]
    d = built["dir"]
    mine = B._read_json(os.path.join(d, B.RUNS))
    streams = B._read_json(os.path.join(d, B.STREAMS))["streams"]
    assert set(f_runs) <= set(mine) and info["items"] == mine["cohort_info"]["items"] == "runs" and tuple(FX.SK_SLABS) == B.SLABS
    for k in ("table", "env", "streams", "guards", "s_first", "n_ch", "layout", "fs_native"):
        assert mine["cohort_info"][k] == info[k], k
    assert mine["cohort_info"]["caches"] == info["caches"] == {"A": "eeg_f16_tmajor.npy"}

    def kinds(v):
        return {type(None): "none", bool: "bool", int: "int", float: "float", str: "str", list: "list", dict: "dict"}[type(v)]

    def compatible(fx_rows, my_rows, allow_none=()):
        keys = set().union(*(set(r) for r in fx_rows))
        assert keys <= set().union(*(set(r) for r in my_rows)), keys - set().union(*(set(r) for r in my_rows))
        for k in keys:
            fk = {kinds(r[k]) for r in fx_rows if k in r} - {"none"}
            mk = {kinds(r[k]) for r in my_rows if k in r} - {"none"}
            if fk and mk:
                assert mk <= fk | ({"int", "float"} if fk & {"int", "float"} else set()), (k, fk, mk)
    compatible(f_streams, streams)
    compatible([r for r in f_runs["runs"] if r["role"] != "restricted"], [r for r in mine["runs"] if r["role"] != "restricted"])
    compatible([r for r in f_runs["runs"] if r["role"] == "restricted"], [r for r in mine["runs"] if r["role"] == "restricted"])
    compatible(f_runs["participants"], mine["participants"])
    env = np.load(os.path.join(d, B.ENV))                             # 2-8 Hz, RMS 1 per stream, concatenated in stream order
    assert env.dtype == np.float32 and env.ndim == 1 and sum(s["length"] for s in streams) == len(env)
    assert [s["stream"] for s in streams] == list(range(len(streams))) and all(s["offset"] == sum(q["length"] for q in streams[:i])
                                                                             for i, s in enumerate(streams))
    for s in streams:
        e = env[s["offset"]:s["offset"] + s["length"]].astype(np.float64)
        raw = np.load(os.path.join(built["src"], s["file"]), allow_pickle=False)[:, 0]
        bl = signal.sosfiltfilt(signal.butter(4, [2, 8], btype="band", fs=64, output="sos"), raw, padtype="odd", padlen=min(128, len(raw) - 1))
        assert abs(np.sqrt((e ** 2).mean()) - 1) < 1e-4 and np.allclose(e, bl / np.sqrt((bl ** 2).mean()), atol=1e-5)
        assert abs(s["rms"] - np.sqrt((bl ** 2).mean())) < 1e-9 * s["rms"] and s["kind"] == "attended"
        assert s["fs_source"] == 64 and s["filter_sha256"] == {"env_sos": C.filter_shas()["env_sos"]} and s["nan_count"] == 0  # §2.3
        assert s["source_sha256"] == B._sha256_file(os.path.join(built["src"], s["file"])) and s["T_source"] == s["length"]
        assert s["origin"].startswith(FX.ENV_SOURCE["sparrkulee"][0]) and s["original_band"] == FX.ENV_SOURCE["sparrkulee"][1]
    for r in mine["runs"]:
        assert streams[r["stream"]]["name"] == r["stimulus"] and streams[r["stream"]]["length"] == r["T_env"]
    assert mine["id_space"] == "cohort_local_provisional" and mine["inputs"]["runs_table_sha256"] == B._sha256_file(os.path.join(d, B.RUNS_TABLE))
    assert mine["sanity"]["stimuli_with_several_presentations"] == {}
    # the cache unit: UNIT_RULE of build_public.py (M2b) decides it here, so C6 can pool SparrKULee into the mode-C scales
    u, ci = mine["unit"], mine["cohort_info"]["unit"]
    assert ci["name"] == info["unit"]["name"] == "uV" and ci["factor_to_uV"] == 1.0 and ci["source_unit"] == "uV"
    assert u["supported"] and u["rule"] == BP.UNIT_RULE and u["documented"]["unit"] is None and u["magnitude"]["unit"] == "uV"
    assert u["participant_medians"]["other_unit"] == [] and u["participant_medians"]["n"] == len(mine["participants"])
    assert u["rule_source"]["sha256"] == B._sha256_file(BP.__file__)
    assert mine["unit_evidence"]["median_prez_sd"] == u["magnitude"]["median"] and 0.1 <= u["magnitude"]["median"] <= 1e3
    for p in mine["participants"]:
        assert p["sd_prez_uV"]["A"] == p["sd_prez"]["A"] and p["median_prez_sd"]["A"] == np.median([v for v in p["sd_prez"]["A"]
                                                                                                    if v is not None])
    lay = mine["cohort_info"]["layout"]
    sc = BP.mode_c_scales("dtu", {"sparrkulee": {"layout": lay, "participants": mine["participants"]},
                                  "dtu": {"layout": list(C.MONTAGES["dtu"])}}, {"sparrkulee": ci["factor_to_uV"]}, donors=("sparrkulee",))
    fit = [p for p in mine["participants"] if p["role"] == "fit"]
    assert sc["supported"] and fit and len(fit) < len(mine["participants"])           # donor-fit participants only
    for n in ("Cz", "Iz", "T8"):
        i = lay.index(n)
        assert sc["scale"][n] == float(np.median([p["sd_prez"]["A"][i] for p in fit if p["sd_prez"]["A"][i] is not None]))


def test_c4_checks_the_shared_unit_rule_before_building(built, tmp_path, monkeypatch):
    d5 = os.path.join(str(tmp_path / "cache5"), B.COHORT)
    os.makedirs(d5)
    for f in (B.RUNS_TABLE, B.AUDIT, B.AUDIT_META):
        shutil.copy(os.path.join(built["dir"], f), d5)
    monkeypatch.delattr(BP, "decide_unit")                            # M2b's rule moved: C4 stops before any cache byte
    with pytest.raises(ImportError, match="decide_unit"):
        B.stage_c4(None, str(tmp_path / "cache5"), log=lambda m: None)
    assert sorted(os.listdir(d5)) == sorted((B.RUNS_TABLE, B.AUDIT, B.AUDIT_META))


def test_cohort_unit_rule():
    u = B.cohort_unit({"001": [3.0, 4.0, None], "002": [2.5, 5.0, 6.0]})            # microvolt magnitudes
    assert u["supported"] and u["name"] == "uV" and u["source_unit"] == "uV" and u["factor_to_uV"] == 1.0
    assert u["documented"] == {"unit": None, "basis": B.UNIT_DOCUMENTED[1]} and u["participant_medians"]["other_unit"] == []
    v = B.cohort_unit({"001": [3e-6, 4e-6], "002": [2e-6, 5e-6]})                     # volts -> x 1e6
    assert v["supported"] and v["source_unit"] == "V" and v["factor_to_uV"] == 1e6 and v["name"] == "uV"
    w = B.cohort_unit({"001": [1.0, 1.01, 0.99], "002": [1.0, 1.02, None]})          # source-normalised: no unit
    assert not w["supported"] and w["name"] is None and w["factor_to_uV"] is None and "source-normalised" in w["magnitude"]["reason"]
    x = B.cohort_unit({"001": [3.0, 4.0], "002": [2.0, 5.0], "003": [3e-6, 4e-6]})  # one participant in another band
    assert not x["supported"] and x["name"] is None and x["participant_medians"]["other_unit"] == ["003"] and "003" in x["reason"]
    assert x["magnitude"]["unit"] == "uV" and "basis" not in x


def test_c4_resume_gives_identical_outputs(built, tmp_path):
    out2 = str(tmp_path / "cache2")
    d2 = os.path.join(out2, B.COHORT)
    os.makedirs(d2)
    for f in (B.RUNS_TABLE, B.AUDIT, B.AUDIT_META):
        shutil.copy(os.path.join(built["dir"], f), d2)
    with pytest.raises(B._Interrupted):
        B.stage_c4(None, out2, log=lambda m: None, _stop_after=2)
    assert os.path.exists(os.path.join(d2, B.PARTIAL)) and not os.path.exists(os.path.join(d2, B.CACHE))
    assert len([f for f in os.listdir(os.path.join(d2, B.C4_DONE)) if f.startswith("sub-")]) == 2
    B.stage_c4(None, out2, log=lambda m: None)
    for f in (B.CACHE, B.RUNS, B.ENV, B.STREAMS):
        with open(os.path.join(built["dir"], f), "rb") as a, open(os.path.join(d2, f), "rb") as b:
            assert a.read() == b.read(), f
    B.stage_c4(None, out2, log=lambda m: None)                         # a complete build only rewrites the (identical) tables
    with open(os.path.join(built["dir"], B.RUNS), "rb") as a, open(os.path.join(d2, B.RUNS), "rb") as b:
        assert a.read() == b.read()
    with open(os.path.join(d2, B.C4_DONE, "layout.json")) as f:       # a different layout refuses to mix with the partial build
        lay = json.load(f)
    lay["N"] += 1
    with open(os.path.join(d2, B.C4_DONE, "layout.json"), "w") as f:
        json.dump(lay, f)
    with pytest.raises(RuntimeError, match="another layout"):
        B.stage_c4(None, out2, log=lambda m: None)


def test_c4_requires_complete_audit_and_final_role_precedence(built, tmp_path):
    out3 = str(tmp_path / "cache3")
    d3 = os.path.join(out3, B.COHORT)
    os.makedirs(d3)
    shutil.copy(os.path.join(built["dir"], B.RUNS_TABLE), d3)
    with pytest.raises(FileNotFoundError):
        B.stage_c4(None, out3, log=lambda m: None)
    with open(os.path.join(built["dir"], B.AUDIT)) as f, open(os.path.join(d3, B.AUDIT), "w") as g:
        g.writelines(f.readlines()[:-1])
    with pytest.raises(ValueError, match="lacks 1 runs"):
        B.stage_c4(None, out3, log=lambda m: None)
    shutil.copy(os.path.join(built["dir"], B.AUDIT), d3)               # complete audit, no meta: refused
    with pytest.raises(FileNotFoundError, match=B.AUDIT_META):
        B.stage_c4(None, out3, log=lambda m: None)
    meta = B._read_json(os.path.join(built["dir"], B.AUDIT_META))
    meta["runs_table_sha256"] = "0" * 64                               # an audit of another run table: refused
    B._write_json(os.path.join(d3, B.AUDIT_META), meta)
    with pytest.raises(ValueError, match="were not built from this"):
        B.stage_c4(None, out3, log=lambda m: None)
    assert not os.path.exists(os.path.join(d3, B.CACHE)) and not os.path.exists(os.path.join(d3, B.PARTIAL))
    r = {"restricted": False, "role": "fit", "structural": {"anomalous": True}}
    assert B.final_role(r, {"class": "aligned"}) == ("fit", [])
    assert B.final_role(r, {"class": "unverifiable"}) == ("excluded_rule", ["structural_anomaly_unverified_clock"])
    assert B.final_role(r, {"class": "misaligned"}) == ("excluded_rule", ["clock_misaligned", "structural_anomaly_unverified_clock"])
    assert B.final_role(dict(r, structural={"anomalous": False}), {"class": "unverifiable"}) == ("fit", [])
    assert B.final_role(dict(r, restricted=True), {"class": "not_audited"}) == ("restricted", [])


def test_cli_guards(built, tmp_path, monkeypatch):
    with pytest.raises(SystemExit):                                   # --out is required (no default output)
        B.main(["--stage", "C1", "--src", built["src"], "--expect", "none"])
    with pytest.raises(SystemExit):                                   # only the §6.2 cache root without --allow-other-out
        B.main(["--stage", "C1", "--src", built["src"], "--out", str(tmp_path / "x"), "--expect", "none"])
    assert not os.path.exists(tmp_path / "x")
    for name in ("stage_c1", "stage_c2", "stage_c4"):                 # production-root refusals (no stage may be reached)
        monkeypatch.setattr(B, name, lambda *a, **k: pytest.fail("a stage was reached under the production cache root"))
    for argv in (["--stage", "C2", "--runs", "sub-001_ses-x_run-01"], ["--stage", "C1", "--no-hash-eeg"], ["--stage", "C1", "--expect", "none"]):
        with pytest.raises(SystemExit):
            B.main(argv + ["--out", B.CACHE_ROOT])
    monkeypatch.undo()
    with pytest.raises(FileNotFoundError, match="run C1 first"):
        B.main(["--stage", "C2", "--out", str(tmp_path / "y"), "--allow-other-out"])
    with pytest.raises(ValueError, match="differs from the C1 table"):
        B.main(["--stage", "C2", "--out", built["out"], "--allow-other-out", "--src", str(tmp_path)])
    assert B.main(["--stage", "C1", "--src", built["src"], "--out", str(tmp_path / "z"), "--allow-other-out", "--expect", "none",
                   "--no-hash-eeg"]) == 0
    t = B._read_json(str(tmp_path / "z" / "sparrkulee" / B.RUNS_TABLE))
    assert not t["hash_eeg"] and all(r["sha256"]["eeg"] is None for r in t["runs"]) and len(t["runs"]) == len(PLAN)
    assert B.CACHE_ROOT == "/projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1"      # design §6.2


def test_output_location_guard(built, tmp_path, monkeypatch):
    src = built["src"]
    for name in ("stage_c1", "stage_c2", "stage_c4"):                 # the stages have no default output
        assert inspect.signature(getattr(B, name)).parameters["out"].default is inspect.Parameter.empty
    inner = os.path.join(src, "inner")                                # an output inside the C1 table's dataset tree (C2 / C4 learn
    os.makedirs(os.path.join(inner, B.COHORT))                        # the tree from the table): refused before any write
    shutil.copy(os.path.join(built["dir"], B.RUNS_TABLE), os.path.join(inner, B.COHORT))
    try:
        for stage in (B.stage_c2, B.stage_c4):
            with pytest.raises(B.OutputLocationError, match="overlaps the dataset tree"):
                stage(None, inner, log=lambda m: None)
        assert sorted(os.listdir(os.path.join(inner, B.COHORT))) == [B.RUNS_TABLE]
    finally:
        shutil.rmtree(inner)
    for name in ("_cohort_dir", "_write_json", "_save_npy", "_read_json", "_participants_tsv"):   # past the guard nothing may run
        monkeypatch.setattr(B, name, lambda *a, **k: pytest.fail("a refused output location got past check_out"))
    link = tmp_path / "link_to_cache_root"                            # the cache root, also through a symlink: CLI only
    os.symlink(B.CACHE_ROOT, link)
    for out in (B.CACHE_ROOT, B.CACHE_ROOT + "/", str(link)):
        with pytest.raises(B.OutputLocationError, match="only by the CLI job"):
            B.stage_c1(src, out, expect=B.EXPECT_REAL, hash_eeg=True, log=lambda m: None)
        for stage in (B.stage_c2, B.stage_c4):
            with pytest.raises(B.OutputLocationError, match="only by the CLI job"):
                stage(None, out, log=lambda m: None)
    with pytest.raises(B.OutputLocationError, match="always hashes"):  # with the CLI token, the production settings still hold
        B.stage_c1(src, B.CACHE_ROOT, expect=None, hash_eeg=True, log=lambda m: None, _auth=B._CLI)
    with pytest.raises(B.OutputLocationError, match="always hashes"):
        B.stage_c1(src, B.CACHE_ROOT, expect=B.EXPECT_REAL, hash_eeg=False, log=lambda m: None, _auth=B._CLI)
    with pytest.raises(B.OutputLocationError, match="partial audit"):
        B.stage_c2(None, B.CACHE_ROOT, runs=["sub-001_ses-x_run-01"], log=lambda m: None, _auth=B._CLI)
    refused = {src: "overlaps", os.path.join(src, "derivatives"): "overlaps", B.SRC_DEFAULT: "nothing is written under",
               B.DATA_VOLUME: "nothing is written under", B.DATA_VOLUME + "/auditory/x": "nothing is written under",
               B.DATA_VOLUME + "/auditory_public/derived/other": "nothing is written under",
               B.DATA_VOLUME + "/auditory_private/x": "nothing is written under", B.CACHE_ROOT + "/sub": "nothing is written under",
               os.path.join(src, "..", os.path.basename(src)): "overlaps"}
    for out, msg in refused.items():                                  # the stages themselves
        with pytest.raises(B.OutputLocationError, match=msg):
            B.stage_c1(src, out, expect=None, hash_eeg=False, log=lambda m: None)
        for stage in (B.stage_c2, B.stage_c4):
            with pytest.raises(B.OutputLocationError, match=msg):
                stage(src, out, log=lambda m: None)
        with pytest.raises(B.OutputLocationError, match=msg):
            B.check_out(out, src, B._CLI)
    for name in ("stage_c1", "stage_c2", "stage_c4"):
        monkeypatch.setattr(B, name, lambda *a, **k: pytest.fail("a stage was reached for a refused --out"))
    for out in refused:                                               # the CLI, even with --allow-other-out
        for st in ("C1", "C2", "C4"):
            with pytest.raises(SystemExit):
                B.main(["--stage", st, "--src", src, "--out", out, "--allow-other-out", "--expect", "none", "--no-hash-eeg"])
    with pytest.raises(B.OutputLocationError, match="overlaps"):      # <out>/sparrkulee containing the dataset tree
        B.check_out(tmp_path / "o", tmp_path / "o" / B.COHORT / "data")
    with pytest.raises(B.OutputLocationError, match="overlaps"):      # the cache root too, against a --src that contains it
        B.check_out(B.CACHE_ROOT, os.path.dirname(os.path.dirname(B.CACHE_ROOT)), B._CLI)
    with pytest.raises(B.OutputLocationError, match="required"):
        B.check_out(None)
    assert B.check_out(tmp_path / "ok", src) == (os.path.realpath(tmp_path / "ok"), False)
    assert B.check_out(B.CACHE_ROOT, None, B._CLI) == (os.path.realpath(B.CACHE_ROOT), True)
    assert not os.path.exists(os.path.join(src, B.COHORT)) and not os.path.exists(tmp_path / "ok")
