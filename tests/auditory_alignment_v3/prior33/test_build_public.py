"""M2b tests (PUBLIC_PRIOR_DESIGN.md §2.1, §2.2, §2.3, §2.5, §2.13, §3.1, §3.3, §3.5, §6.2 C5; §7.1 items 2-3, 8, 9): the public
target-cohort builders of auditory_alignment_v3.prior33.build_public on synthetic sources written in the real on-disk layouts (FAU
stage-B HDF5, stimulus_env_128.h5, the published waveforms and stereo WAVs, the C3 receipt and chanmap log; DTU stage-A HDF5,
inventory.json, content groups, dtu_cf*.h5 and audio_local.h5; Federici blocks and content_groups.json). The existing loaders'
module constants (auditory_alignment.data, prep_targets, federici_content) are redirected with monkeypatch, so the real reading
code runs.
Checked: the contract filters (h_aa resampling, the 2-8 Hz envelope chain, RMS 1) and, independently of the contract functions,
the anti-aliasing stopband, the pass band and zero-phase timing against analytic tones and a pulse; the per participant x channel
z-score with guards and masks, the 2-8 Hz statistic; modes A / B / C and the unit rule (human evidence, the phantom outside the
band, a human outside the band, a source-normalised cohort, no leftover partial file); CAR; segment starts with the competing-
talker onset rule and the target-stage starts; the DTU masker placed by an exact fractional delay; the cache layout and the schema
of fixtures.py; cohort-local presentations, own repeats, item-level Federici conditions, HC / HC-v identities and the phantom; the
FAU stereo files matched by content and the aux patterns; DTU trial exclusions, unread files and the inventory reconciliation;
resume and byte determinism, separate mode jobs, the lock, the restricted-SparrKULee guard, the CLI and the mode-C scale of §2.13
(same-band rule, uV cross-check, with_band_sd). CPU only, synthetic data only, about 30 s."""
import builtins
import hashlib
import json
import os
import sys

import h5py
import numpy as np
import pytest
from scipy import signal
from scipy.io import wavfile

from auditory_alignment import data as ALD
from auditory_alignment import federici_content as FC
from auditory_alignment import prep_targets as PT
from auditory_alignment_v3.prior33 import build_public as BP
from auditory_alignment_v3.prior33 import contract as C

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixtures import make_synthetic_manifest  # noqa: E402

QUIET = lambda *a: None  # noqa: E731
STR = h5py.string_dtype()


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _json(path):
    with open(path) as f:
        return json.load(f)


def _env(rng, n, fs):
    k = np.hanning(max(3, fs // 8))
    return np.convolve(np.abs(rng.standard_normal(n)), k / k.sum(), mode="same") + 0.05


def _strs(names):
    """A string-array attribute as the real caches store it (an empty list is an empty float64 array, as in stage B)."""
    names = list(names)
    return np.array(names, dtype=STR) if names else np.array([], dtype=np.float64)


# ---------------------------------------------------------------------------------------------------------- synthetic FAU
FAU_IDS = {"th": ("301", "302", "303"), "ha": ("201",), "ci": ("101",)}
FAU_SEL = ("301", "302")                     # always-train TH (selection half)
FAU_BADS = {"101": ("CP6", "CP5")}           # interpolated in a CI user (stored unordered on purpose)
FAU_CODES = ("111", "112", "121", "215", "227")
FAU_SIDE = {"111": 1, "112": 0, "121": 1, "215": 0, "227": 1}   # stereo channel of the attended stream (0 left, 1 right)
FAU_ONSET = {"215": 2.0, "227": 2.53125}     # distractor onsets (s)
FAU_SWAP = {"215": "227", "227": "215"}      # stereo files stored under each other's name (as the real S220.wav / S229.wav)
FAU_FLIPPED = "303"                          # both aux recording channels exchanged for the session (pattern 'swapped')
FAU_SINGLE = "201"                           # aux1 silent, both streams on aux0 (pattern 'single_channel')
L128, WAV_FS = 2048, 8000


def make_fau(root, monkeypatch, nan_in_env=True):
    rng = np.random.default_rng(1)
    repo, pub, stageb = root / "repo", root / "pub", root / "stageB"
    env_path = pub / "derived" / "c3_preproc_v1" / "fau_tud" / "stimulus_env_128.h5"
    for d in (repo / "private" / "auditory_c3" / "public" / "fau_tud", repo / "private" / "auditory_c3" / "receipts",
              pub / "fau_tud" / "zx", pub / "fau_tud" / "stimuli" / "stimuli", env_path.parent,
              pub / "derived" / "c3_preproc_v1" / "_logs", *(stageb / g for g in FAU_IDS)):
        os.makedirs(d, exist_ok=True)
    with open(repo / "private" / "auditory_c3" / "public" / "fau_tud" / "th_split.json", "w") as f:
        json.dump({"selection_half": list(FAU_SEL), "heldout_half": [s for s in FAU_IDS["th"] if s not in FAU_SEL]}, f)
    with open(pub / "derived" / "c3_preproc_v1" / "_logs" / "fau_tud_chanmap.json", "w") as f:
        json.dump({"ha": {"scale_ratio_median": 0.91}, "ci": {"scale_ratio_median": 0.75}, "th": {"scale_ratio_median": 0.92}}, f)
    envs, n_wav0 = {}, int(L128 / 128 * WAV_FS)
    with h5py.File(env_path, "w") as fe, h5py.File(pub / "fau_tud" / "zx" / "hi.hdf5", "w") as fp:
        fe.attrs["source"] = "fau_tud/zx/hi.hdf5"
        for i, code in enumerate(FAU_CODES):
            cs = code[0] == "2"
            n_wav = n_wav0 + 8 * i                                              # each code's own waveform length
            a = _env(rng, L128, 128)
            if nan_in_env and code == "112":
                a[100:103] = np.nan                                             # NaN samples: nan_to_num, counted
            dd = np.full(L128, np.nan)
            wa = (rng.standard_normal(n_wav) * 1e6).astype(np.int32)
            wd = np.zeros(n_wav, np.int32)
            if cs:
                on = FAU_ONSET[code]
                dd = _env(rng, L128, 128)
                dd[:int(on * 128)] = 0.0
                wd[int(round(on * WAV_FS)):] = (rng.standard_normal(n_wav - int(round(on * WAV_FS))) * 1e6).astype(np.int32)
            envs[code] = (a, dd)
            fe.create_dataset(f"{code}/attended_env/raw", data=a.astype(np.float32))
            fe.create_dataset(f"{code}/distractor_env/raw", data=dd.astype(np.float32))
            fp.create_dataset(f"stimulus_files/{code}/attended_wav", data=wa)
            fp.create_dataset(f"stimulus_files/{code}/distractor_wav", data=wd)
            st = np.zeros((n_wav, 2), np.int32)
            st[:, FAU_SIDE[code]], st[:, 1 - FAU_SIDE[code]] = wa, wd
            wavfile.write(str(pub / "fau_tud" / "stimuli" / "stimuli" / f"S{FAU_SWAP.get(code, code)}.wav"), WAV_FS, st)
    lay, rows, eeg = C.MONTAGES["fau"], {g: [] for g in ("ha", "ci", "th")}, {}
    gain = rng.standard_normal(len(lay))
    for grp, ids in FAU_IDS.items():
        for s in ids:
            with h5py.File(stageb / grp / f"{s}.h5", "w") as f:
                f.attrs.update(channels=_strs(lay), bads_interpolated=_strs(FAU_BADS.get(s, ())), guard_samples=314, fs=128,
                               subject=s, group=grp)
                for t, code in enumerate(FAU_CODES):
                    T = L128 - 3 * t                                            # EEG and envelope lengths differ slightly
                    a = np.nan_to_num(envs[code][0])[:T]
                    resp = np.zeros(T)
                    resp[6:] = a[:T - 6]
                    ica = (np.outer(gain, resp) + 2.0 * rng.standard_normal((len(lay), T))) * rng.uniform(2, 8, len(lay))[:, None] * 1e-6
                    noica = ica + (np.outer(np.r_[np.zeros(8), 5e-6, np.zeros(len(lay) - 9)], a) if grp == "ci" else 0.0)
                    g = f.create_group(f"trial_{t + 1:02d}")
                    g.attrs.update(stimulus=code, valid_start=314 + (2 if t == 1 else 0), valid_stop=T - 314, realigned_copy=t == 1,
                                   aux_lag_ms=3)
                    g.create_dataset("eeg_1_20_ica", data=ica.astype(np.float32))
                    g.create_dataset("eeg_1_20_noica", data=noica.astype(np.float32))
                    eeg[(s, f"trial_{t + 1:02d}")] = (ica.astype(np.float32), noica.astype(np.float32))
                    k = FAU_SIDE[code] if s != FAU_FLIPPED else 1 - FAU_SIDE[code]
                    r_att, r_dis = [0.05, 0.05], [float("nan")] * 2
                    if s == FAU_SINGLE:
                        r_att = [0.8, 0.03]
                        if code[0] == "2":
                            r_dis = [0.6, 0.03]
                    else:
                        r_att[k] = 0.8
                        if code[0] == "2":
                            r_dis = [0.05, 0.05]
                            r_dis[1 - k] = 0.7
                    rows[grp].append({"subject": s, "trial": t + 1, "stimulus": code,
                                      **{f"aux{i}_attended_env": {"lag_ms": 1, "r": r_att[i]} for i in (0, 1)},
                                      **{f"aux{i}_distractor_env": {"lag_ms": 1, "r": r_dis[i]} for i in (0, 1)}})
    with open(repo / "private" / "auditory_c3" / "receipts" / "fau_tud_schema_private_001.json", "w") as f:
        f.write(json.dumps({g: {"_alignment_rows": r} for g, r in rows.items()}))
    monkeypatch.setattr(ALD, "REPO", str(repo))
    monkeypatch.setattr(ALD, "STAGEB", str(stageb))
    monkeypatch.setattr(ALD, "PUB", str(pub))
    monkeypatch.setattr(PT, "FAU_ENV", str(env_path))
    monkeypatch.setattr(BP, "FAU_WAV_FS", WAV_FS)
    return {"envs": envs, "eeg": eeg, "stageb": stageb, "pub": pub}


# ---------------------------------------------------------------------------------------------------------- synthetic DTU
DTU_SUBS = {"sub-001": "hi", "sub-002": "hi", "sub-021": "nh", "sub-022": "nh", "sub-023": "nh"}
DTU_TRIALS = {  # trial -> (target, masker or None, masker offset s, side)
    "sub-021": {"trial_001": ("tA", None, None, "attendleft"), "trial_002": ("tB", None, None, "attendright"),
                "trial_003": ("tC", "mA", 3.0, "attendright")},
    "sub-022": {"trial_001": ("tA", None, None, "attendleft"), "trial_002": ("tB", None, None, "attendright"),
                "trial_003": ("tC", "mA", 3.0, "attendright"), "trial_004": ("tA", None, None, "attendleft")},   # own repeat
    "sub-023": {"trial_001": ("tA", None, None, "attendleft"), "trial_002": ("tE", None, None, "attendleft"),
                "trial_003": ("tC", "mA", 4.0078125, "attendright"), "trial_004": ("tX", None, None, "attendleft")},
    "sub-001": {"trial_001": ("hA", None, None, "attendleft"), "trial_002": ("hC", "mB", 3.5, "attendleft")},
    "sub-002": {"trial_001": ("hA", None, None, "attendleft"), "trial_002": ("hC", "mB", 3.5, "attendleft")}}
DTU_INV_ONLY = {"sub-024_run-2": {"trial_001": ("tE", None, None), "trial_002": ("tC", "mA", 3.25)}}   # a file load_dtu never reads
DTU_CG = {"tA": (0, 0, False), "tB": (1, 1, True), "tC": (2, 0, False), "tE": (3, 1, False), "hA": (0, 0, False), "hC": (2, 0, False)}
L_DTU = 2560
PREPROC = "def dtu():\n    X = raw.get_data(picks=eeg_names + eog_names) * 1e6  # uV, recorded CMS reference\n"


def make_dtu(root, monkeypatch):
    rng = np.random.default_rng(2)
    repo, pub = root / "repo", root / "pub"
    pre, kcs = pub / "derived" / "c3_preproc_v1" / "dtu_snhl", pub / "derived" / "c3_features_v1" / "dtu" / "kcs_targets_v1"
    tsv = pub / "dtu_snhl" / "ds-eeg-snhl" / "ds-eeg-snhl"
    for d in (repo / "private" / "auditory_c3" / "public" / "dtu_v2", repo / "auditory_c3", pre, kcs, tsv):
        os.makedirs(d, exist_ok=True)
    with open(repo / "auditory_c3" / "preproc.py", "w") as f:
        f.write(PREPROC)
    code_sha = _sha(repo / "auditory_c3" / "preproc.py")
    with open(tsv / "participants.tsv", "w") as f:
        f.write("participant_id\thearing_status\tage\n" + "".join(f"{s}\t{g}\t{40 + i}\n" for i, (s, g) in enumerate(DTU_SUBS.items())))
    for s in DTU_SUBS:
        with open(repo / "private" / "auditory_c3" / "public" / "dtu_v2" / f"{s}.json", "w") as f:
            f.write("{}")
    shas = {n: hashlib.sha256(n.encode()).hexdigest() for n in ("tA", "tB", "tC", "tE", "tX", "hA", "hC", "mA", "mB")}
    inv = []
    for s, trials in list(DTU_TRIALS.items()) + list(DTU_INV_ONLY.items()):
        hi = DTU_SUBS.get(s) == "hi"
        for k, v in trials.items():
            t, m, off = v[:3]
            inv.append({"file": s, "trial": k, "kind": "target", "sha": shas[t], "offset_s": 0.0, "hi": hi, "path": t})
            if m:
                inv.append({"file": s, "trial": k, "kind": "masker", "sha": shas[m], "offset_s": off, "hi": hi, "path": m})
    os.makedirs(pub / "derived" / "c3_features_v1" / "dtu", exist_ok=True)
    with open(pub / "derived" / "c3_features_v1" / "dtu" / "inventory.json", "w") as f:
        json.dump(inv, f)
    with open(kcs / "content_groups.json", "w") as f:
        json.dump({"content": {shas[n]: {"group": g, "half": h, "early_stop": e} for n, (g, h, e) in DTU_CG.items()}}, f)
    envs = {}
    with h5py.File(kcs / "audio_local.h5", "w") as fa, h5py.File(kcs / "dtu_cf0.h5", "w") as f0, h5py.File(kcs / "dtu_cf1.h5", "w") as f1:
        for n, h in shas.items():
            envs[n] = _env(rng, L_DTU + 40, 128)
            fa.create_dataset(f"{h}/env", data=envs[n].astype(np.float32))
            if n != "tX":
                for ff in (f0, f1):
                    ff.create_group(h)
    lay = list(C.BIOSEMI64) + ["EXG1", "EXG2"]
    eeg, gain = {}, rng.standard_normal(64)
    for s, trials in DTU_TRIALS.items():
        with h5py.File(pre / f"{s}.h5", "w") as f:
            f.attrs.update(channels=_strs(lay), code_sha256=code_sha, fs=128, subject=s)
            for k, (t, m, off, side) in trials.items():
                resp = np.zeros(L_DTU)
                resp[6:] = envs[t][:L_DTU - 6]
                x = (np.outer(gain, resp) + 2.0 * rng.standard_normal((64, L_DTU))) * rng.uniform(5, 15, 64)[:, None]
                x = x + 80.0 * rng.standard_normal(L_DTU)[None]                       # CMS common mode, removed by CAR
                x = np.vstack([x, 1e3 * rng.standard_normal((2, L_DTU))])             # EXG rows (dropped by [:64])
                g = f.create_group(k)
                g.attrs.update(talkers="twotalker" if m else "singletalker", masker_onset_rel_s=float(off) if m else np.nan,
                               attend_left_right=side, attend_male_female="attendfemale", stim_file=f"{s}/target/{t}.wav")
                g.create_dataset("eeg_1_20", data=x.astype(np.float32))
                eeg[(s, k)] = x.astype(np.float32)
    with open(pre / "sub-024_run-2.h5", "wb") as f:                                  # never to be opened (not an HDF5 file)
        f.write(b"decoy: auditory_alignment.data.load_dtu never reads this file")
    monkeypatch.setattr(ALD, "REPO", str(repo))
    monkeypatch.setattr(ALD, "PUB", str(pub))
    monkeypatch.setattr(ALD, "DTU_PRE", str(pre))
    monkeypatch.setattr(ALD, "DTU_KCS", str(kcs))
    return {"envs": envs, "eeg": eeg, "shas": shas, "pre": pre}


# ---------------------------------------------------------------------------------------------------------- synthetic Federici
FED_HEAR = {"HC/1001": ("N1", "N2"), "HC/1002": ("N1", "N3"), "HC-v/1001": ("V1", "V2"), "HC-v/1002": ("N1", "V1"),
            "CI/0001": ("N2", "N3"), "CI/00010": ("N1", "N2"), "Artifact/0306_bi": ("N1", "N3")}
FED_GROUP = {"N1": 0, "V1": 0, "N2": 1, "V2": 1, "N3": 2}
FED_ORDER = ["HC:1001", "HC:1002", "CI:0001", "CI:00010", "HC-v:1001", "HC-v:1002", "Artifact:0306_bi"]   # load_federici order
N100 = 3000


def make_fed(root, monkeypatch, zscored=False, scale=None, eeg_fn=None, items_fn=None):
    """scale {who: factor} multiplies a session's EEG; eeg_fn(who, block, x) and items_fn(items) replace content (end-to-end
    filter checks)."""
    rng = np.random.default_rng(3)
    pre, out = root / "fed_pre", root / "fed_kcs"
    os.makedirs(out, exist_ok=True)
    base = {n: _env(rng, N100, 100) for n in ("N1", "N2", "N3")}
    items = {**base, "V1": 0.8 * np.roll(base["N1"], 50) + 0.05 * _env(rng, N100, 100),
             "V2": 0.8 * np.roll(base["N2"], 30) + 0.05 * _env(rng, N100, 100)}
    if items_fn is not None:
        items = items_fn(items)
    items = {n: np.asarray(e).astype(np.float32) for n, e in items.items()}
    keys = {}
    for n, e in items.items():
        e = e.astype(np.float64)
        keys[n] = FC.env_key(((e - e.mean()) / (e.std() + 1e-12)).astype(np.float32))
    n_l = {n: sum(n in v for v in FED_HEAR.values()) for n in items}
    with open(out / "content_groups.json", "w") as f:
        json.dump({"items": [{"key": keys[n], "group": FED_GROUP[n], "role": ("fit", "es", "test")[FED_GROUP[n]], "n_listeners": n_l[n],
                              "first": n} for n in sorted(items)]}, f)
    lay, eeg = C.MONTAGES["federici"], {}
    kern = np.hanning(9) / np.hanning(9).sum() * 3.0
    for who, hear in FED_HEAR.items():
        grp, fid = who.split("/")
        os.makedirs(pre / grp, exist_ok=True)
        E = []
        for b, n in enumerate(hear):
            noise = np.stack([np.convolve(rng.standard_normal(N100), kern, mode="same") for _ in lay])     # below about 15 Hz
            x = (np.outer(rng.standard_normal(len(lay)), items[n]) + noise) * rng.uniform(2, 6, len(lay))[:, None]
            if zscored:
                x = (x - x.mean(1, keepdims=True)) / x.std(1, keepdims=True)
            if eeg_fn is not None:
                x = eeg_fn(who, b, x)
            E.append(x * (scale or {}).get(who, 1.0))
        E = np.stack(E).astype(np.float32)
        eeg[f"{grp}:{fid}"] = E
        with h5py.File(pre / grp / f"{fid}.h5", "w") as f:
            f.attrs.update(channels=_strs(lay), fs=100, participant=fid)
            f.create_dataset("eeg", data=E)
            f.create_dataset("env", data=np.stack([items[n] for n in hear]))
    monkeypatch.setattr(ALD, "FED_PRE", str(pre))
    monkeypatch.setattr(FC, "OUT", str(out))
    return {"items": items, "keys": keys, "eeg": eeg}


# ---------------------------------------------------------------------------------------------------------- helpers
def _load(out, cohort):
    d = os.path.join(out, cohort)
    t = _json(os.path.join(d, BP.TABLE))
    return d, t, _json(os.path.join(d, BP.STREAMS))["streams"], np.load(os.path.join(d, BP.ENV), allow_pickle=False)


def _cache(d, cm):
    return np.load(os.path.join(d, C.CACHE_FILE[cm]), mmap_mode="r", allow_pickle=False)


def _expected(arrs, masked_idx, guard, mode, factor=None, fs=128):
    """Independent mode-A / B / C rows of one participant: resample64, data._stdz over guarded spans without masked cells."""
    x64 = [C.resample64(np.asarray(a, np.float64), fs) for a in arrs]
    if mode == "C":
        out = []
        for x in x64:
            y = x * factor
            y[masked_idx] = 0
            out.append(y)
        return out
    g0, g1 = guard
    V = np.concatenate([x[:, g0:x.shape[1] - g1] for x in x64], axis=1)
    mu, sd = V.mean(1), V.std(1)
    out = []
    for x in x64:
        z = (x - mu[:, None]) / np.where(sd > 0, sd, 1)[:, None]
        z[masked_idx] = 0
        out.append(z)
    return out


def _sd_2_8(arrs, masked_idx, guard, fs=128):
    """Independent 2-8 Hz pre-z SD: scipy butter(4, [2, 8]) sosfiltfilt (odd padding, padlen min(128, T - 1)) of each 64 Hz piece."""
    sos = signal.butter(4, [2, 8], btype="band", fs=64, output="sos")
    g0, g1 = guard
    ys = [signal.sosfiltfilt(sos, C.resample64(np.asarray(a, np.float64), fs), axis=-1, padtype="odd",
                             padlen=min(128, a.shape[1] * 64 // fs - 1)) for a in arrs]
    V = np.concatenate([y[:, g0:y.shape[1] - g1] for y in ys], axis=1)
    return [None if i in masked_idx else float(V[i].std()) for i in range(V.shape[0])]


@pytest.fixture(scope="module")
def fixture_tables(tmp_path_factory):
    fx = make_synthetic_manifest(tmp_path_factory.mktemp("prior33_fixture_for_build_public"))
    man, tabs = fx["manifest"], {}
    for c, info in man["cohorts"].items():
        tabs[c] = _json(os.path.join(fx["root"], info["dir"], info["table"]))
        tabs[c]["_streams"] = _json(os.path.join(fx["root"], info["dir"], info["streams"]))["streams"]
        tabs[c]["_layout"] = info["layout"]
    return {"manifest": man, "tables": tabs}


def _schema_check(t, streams, fixture_tables, cohort):
    ft = fixture_tables["tables"][cohort]
    missing_piece = set(ft["pieces"][0]) - set(t["pieces"][0])
    assert not missing_piece, missing_piece
    for q in t["pieces"]:
        assert set(ft["pieces"][0]) <= set(q)
    fp = set().union(*(set(p) for p in ft["participants"]))
    assert fp <= set(t["participants"][0]) | {"cs_side"}, fp - set(t["participants"][0])
    assert set(ft["_streams"][0]) <= set(streams[0]), set(ft["_streams"][0]) - set(streams[0])
    info = fixture_tables["manifest"]["cohorts"][cohort]
    ours = t["cohort_info"]
    assert set(info) - {"rich", "rich_streams"} <= set(ours), set(info) - set(ours)        # rich_*: the C7 builder's files
    assert ours["layout"] == info["layout"] == list(C.MONTAGES[cohort])
    assert set(ours["caches"]) == set(info["caches"]) and all(ours["caches"][m] == info["caches"][m] for m in info["caches"])
    assert t["id_space"] == BP.ID_SPACE and t["id_note"] == BP.ID_NOTE
    assert ours["stats_band"] == {k: list(v) for k, v in BP.STATS_BAND[cohort].items()}


def _layout_check(t, cohort):
    """Rows: slab order, contiguous, covering N; the contract segment rule; presentations consistent with the pieces; own repeats."""
    pieces, N = t["pieces"], t["cohort_info"]["n_rows"]
    order = sorted(pieces, key=lambda q: q["row_offset"])
    pos = 0
    for q in order:
        assert q["row_offset"] == pos
        pos += q["T_eeg"]
    assert pos == N
    slabs = t["cohort_info"]["role_slabs"]
    for q in pieces:
        a, b = slabs[q["slab"]]
        assert a <= q["row_offset"] and q["row_offset"] + q["T_eeg"] <= b and q["slab"] == q["role"]
        assert q["segment_starts"] == C.segment_starts(q["T_env"], q["T_eeg"], cohort, onset=q["onset_s"]).tolist()
        assert all(s % 32 == 0 for s in q["segment_starts"])
        guard_only = cohort == "fau" and q["kind"] == "cs"                         # §2.2: FAU's onset rule is CSX only
        assert q["segment_starts_target_stage"] == (q["segment_starts_guard_only"] if guard_only else q["segment_starts"])
        pr = t["presentations"][q["presentation"]]
        assert pr["key"] == q["presentation_key"] and pr["id"] == q["presentation"]
        assert t["families"][q["family"]]["name"] == q["family_name"] and q["presentation"] in t["families"][q["family"]]["members"]
        mine = [x["piece_id"] for x in pieces if x["participant"] == q["participant"] and x["presentation_key"] == q["presentation_key"]]
        assert sorted(q["own_repeat_pieces"]) == sorted(set(mine) - {q["piece_id"]})
        assert q["ignored_lead"] == 0
    for pr in t["presentations"]:
        assert pr["n_pieces"] == sum(q["presentation"] == pr["id"] for q in pieces)
    assert t["checks"]["own_repeats"] == [{"participant": a, "presentation_key": k, "pieces": v} for (a, k), v in sorted(
        {(q["participant"], q["presentation_key"]): [x["piece_id"] for x in pieces if (x["participant"], x["presentation_key"]) ==
                                                     (q["participant"], q["presentation_key"])] for q in pieces}.items()) if len(v) > 1]
    if "target_only" in slabs and "fit" in slabs:
        assert slabs["fit"][1] <= slabs["target_only"][0]


def _amp(x, f, fs=64):
    """Amplitude of the tone at f (an exact FFT bin) under a Hann window."""
    w = np.hanning(len(x))
    return 2 * abs(np.fft.rfft(np.asarray(x, np.float64) * w)[int(round(f * len(x) / fs))]) / w.sum()


# ---------------------------------------------------------------------------------------------------------- FAU
def test_fau_modes_values_schema(tmp_path, monkeypatch, fixture_tables):
    src = make_fau(tmp_path, monkeypatch)
    out = tmp_path / "cache"
    s = BP.build("fau", "A,B,C", str(out), log=QUIET)
    assert s["caches"] == {"A": "done", "B": "done", "C": "done"} and s["mode_c"]["supported"] and s["mode_c"]["built"]
    d, t, streams, env = _load(out, "fau")
    _schema_check(t, streams, fixture_tables, "fau")
    _layout_check(t, "fau")
    parts = {p["participant"]: p for p in t["participants"]}
    assert [p["participant"] for p in t["participants"]] == ["301", "302", "101", "201", "303"]   # load_fau order
    assert parts["301"]["dev"] and parts["301"]["fold"] == -1 and not parts["303"]["dev"] and parts["303"]["fold"] >= 0
    assert parts["101"]["masked"] == ["CP5", "CP6"] and parts["201"]["masked"] == []
    assert all(p["donor"] and not p["test_only"] for p in parts.values())
    assert set(t["cohort_info"]["role_slabs"]) == {"fit"} and t["cohort_info"]["masked_cells"] == 2 * len(FAU_CODES)
    # competing talker: onset from the published distractor waveform, side from the stereo file, keys (code, side)
    for q in t["pieces"]:
        code = q["stimulus"]
        side = ("left", "right")[FAU_SIDE[code]]
        assert q["attended_side"] == side and q["family_name"] == f"fau:{code}" and q["family_offset"] == 0
        if q["kind"] == "cs":
            assert q["onset_s"] == pytest.approx(FAU_ONSET[code], abs=1 / WAV_FS)
            assert q["presentation_key"] == f"fau:{code}|side={side}" and q["ignored_lead"] == 0
            assert q["segment_starts"][0] == 32 * int(np.ceil((FAU_ONSET[code] + C.CS_LEAD_S) * 64 / 32 - 1e-9))
            assert q["segment_starts_guard_only"][0] == C.S_FIRST["fau"] == q["segment_starts_target_stage"][0]
            assert streams[q["ignored_stream"]]["name"] == f"{code}/distractor" and streams[q["ignored_stream"]]["family"] is None
            assert parts[q["participant"]]["cs_side"][code] == side
        else:
            assert q["presentation_key"] == f"fau:{code}" and q["onset_s"] is None and q["ignored_stream"] is None
    pres = {p["key"]: p for p in t["presentations"]}
    assert all(p["n_listeners"] == p["n_pieces"] == 5 for p in pres.values()) and len(pres) == len(FAU_CODES)
    # the stereo files of 215 / 227 sit under each other's name: matched by content (SIDE_RULE), as the real 220 / 229
    assert t["checks"]["stereo_file_name_mismatches"] == {"215": "S227.wav", "227": "S215.wav"} and t["checks"]["codes_without_side"] == {}
    ev = t["checks"]["codes"]["215"]["side_evidence"]
    assert ev["expected_file"] == "S215.wav" and ev["file_name_mismatch"] and [c["file"] for c in ev["content_search"]["candidates"]] == ["S227.wav"]
    # aux: diagnostic patterns only; no key depends on them
    aux = t["checks"]["aux"]
    assert aux["listeners_by_pattern"] == {"consistent": ["101", "301", "302"], "single_channel": [FAU_SINGLE], "swapped": [FAU_FLIPPED]}
    assert aux["listeners_unexplained"] == [] and aux["majority_mapping"] == {"aux0": "left", "aux1": "right"}
    assert aux["votes"] == {"aux0->left": 6, "aux0->right": 3, "aux1->left": 2, "aux1->right": 9}   # 201 does not vote
    assert {p: parts[p]["aux_pattern"] for p in parts} == {"101": "consistent", "301": "consistent", "302": "consistent",
                                                           "201": "single_channel", "303": "swapped"}
    for q in t["pieces"]:
        st = {"201": "single_channel", "303": "inconsistent"}.get(q["participant"], "consistent")
        assert q["aux_status"] == st and (q["aux_distractor_on"] is None) == (q["kind"] == "ss")
    assert t["pieces"][1]["stageb"]["extra_guard_128"] == 2 and t["pieces"][1]["stageb"]["realigned_copy"]
    # unit: documented volts (chanmap log), confirmed by the magnitude rule
    u = t["unit"]
    assert u["supported"] and u["source_unit"] == "V" and u["factor_to_uV"] == 1e6 and u["documented"]["unit"] == "V"
    assert t["cohort_info"]["unit"]["name"] == "uV" and u["participant_medians"]["other_unit"] == []
    assert t["unit_evidence"]["test_only"] == {} and u["evidence"] == "human (non-test_only) participants"
    # values, mode by mode, against an independent computation (CI participant: masked channels)
    lay = C.MONTAGES["fau"]
    for pid in ("101", "303"):
        midx = [lay.index(n) for n in FAU_BADS.get(pid, ())]
        mine = [q for q in t["pieces"] if q["participant"] == pid]
        for cm, sig in (("A", 0), ("B", 1), ("C", 1)):
            exp = _expected([src["eeg"][(pid, q["trial"])][sig] for q in mine], midx, C.GUARDS["fau"], "C" if cm == "C" else "z", 1e6)
            mm = _cache(d, cm)
            assert mm.shape == (t["cohort_info"]["n_rows"], 31) and mm.dtype == np.float16
            for q, e in zip(mine, exp):
                got = np.asarray(mm[q["row_offset"]:q["row_offset"] + q["T_eeg"]], np.float64).T
                assert got.shape == e.shape
                np.testing.assert_allclose(got, e, rtol=2e-3, atol=2e-3 * (1 if cm != "C" else np.abs(e).max()))
                assert not got[midx].any()
            if cm != "C":   # unit variance over the guarded spans of the unmasked channels
                g0, g1 = C.GUARDS["fau"]
                V = np.concatenate([np.asarray(mm[q["row_offset"] + g0:q["row_offset"] + q["T_eeg"] - g1], np.float64) for q in mine])
                keep = [i for i in range(31) if i not in midx]
                np.testing.assert_allclose(V[:, keep].mean(0), 0, atol=2e-3)
                np.testing.assert_allclose(V[:, keep].std(0), 1, atol=2e-3)
        p = parts[pid]
        assert set(p["sd_prez"]) == {"A", "B", "A_2_8"} and p["sd_prez_unit"] == "V"
        assert p["source_sha256"] == _sha(src["stageb"] / ("ci" if pid == "101" else "th") / f"{pid}.h5")
        for k in ("A", "B", "A_2_8"):
            assert all((v is None) == (i in midx) for i, v in enumerate(p["sd_prez"][k]))
            assert all(a is None or b == pytest.approx(a * 1e6) for a, b in zip(p["sd_prez"][k], p["sd_prez_uV"][k]))
            assert 1e-7 < p["median_prez_sd"][k] < 1e-3                       # source unit: volts
        exp_b = _sd_2_8([src["eeg"][(pid, q["trial"])][0] for q in mine], midx, C.GUARDS["fau"])   # the ica signal, 2-8 Hz
        assert all((a is None and b is None) or a == pytest.approx(b, rel=1e-7) for a, b in zip(p["sd_prez"]["A_2_8"], exp_b))
        assert all(b is None or b < a for a, b in zip(p["sd_prez"]["A"], p["sd_prez"]["A_2_8"]))
    for cm in ("A", "B", "C"):
        dj = _json(os.path.join(d, C.CACHE_FILE[cm]) + ".done.json")
        assert dj["sha256"] == _sha(os.path.join(d, C.CACHE_FILE[cm])) and dj["layout_sha256"] == t["layout_sha256"]
        assert t["caches"][cm] == dj and not os.path.exists(os.path.join(d, BP._partial(C.CACHE_FILE[cm])))


def test_envelope_contract_chain(tmp_path, monkeypatch):
    src = make_fau(tmp_path, monkeypatch)
    out = tmp_path / "cache"
    BP.build("fau", "A", str(out), log=QUIET)
    d, t, streams, env = _load(out, "fau")
    assert env.dtype == np.float32 and len(env) == sum(s["length"] for s in streams)
    names = [s["name"] for s in streams]
    assert names == sorted(names) and set(names) == {f"{c}/attended" for c in FAU_CODES} | {f"{c}/distractor" for c in FAU_CODES
                                                                                         if c[0] == "2"}
    sos = C.env_sos()[0]
    for s in streams:
        code, stream = s["name"].split("/")
        raw = src["envs"][code][0 if stream == "attended" else 1]
        exp = C.rms_norm(C.band(C.resample64(np.nan_to_num(raw), 128), sos))
        got = env[s["offset"]:s["offset"] + s["length"]]
        assert s["length"] == len(exp) == -(-len(raw) // 2)
        np.testing.assert_allclose(got, exp, rtol=1e-5, atol=1e-5)
        assert float(np.sqrt(np.mean(got.astype(np.float64) ** 2))) == pytest.approx(1.0, abs=1e-5)
        assert s["nan_count"] == (3 if s["name"] == "112/attended" else 0)
        assert s["filter_sha256"] == {"aa_fir_128": C.filter_shas()["aa_fir_128"], "env_sos": C.env_sos()[1]}
        assert s["source_sha256"] == hashlib.sha256(np.asarray(raw.astype(np.float32), np.float64).tobytes()).hexdigest()
        assert s["fs_source"] == 128 and s["original_band"] and s["origin"] and "placement" not in s
        assert (s["family_name"] is None) == (stream == "distractor") and s["rms"] > 0
    for q in t["pieces"]:      # target windows never touch the 41-sample stream edges
        for s0 in q["segment_starts"]:
            assert s0 + C.TICK_OFFS[0] >= C.ENV_EDGE and s0 + C.TICK_OFFS[-1] + C.N_TGT <= q["T_env"] - C.ENV_EDGE


# ---------------------------------------------------------------------------------------------------------- DTU
def test_dtu_car_roles_presentations_exclusions(tmp_path, monkeypatch, fixture_tables):
    src = make_dtu(tmp_path, monkeypatch)
    opened, real = [], h5py.File

    def rec_file(path, *a, **k):
        opened.append(os.fspath(path))
        return real(path, *a, **k)
    monkeypatch.setattr(h5py, "File", rec_file)
    out = tmp_path / "cache"
    s = BP.build("dtu", "all", str(out), log=QUIET)
    assert s["caches"] == {"A": "done", "C": "done"}
    assert not any("sub-024_run-2" in p for p in opened)
    d, t, streams, env = _load(out, "dtu")
    _schema_check(t, streams, fixture_tables, "dtu")
    _layout_check(t, "dtu")
    sh = {v: k for k, v in src["shas"].items()}
    assert [e["trial"] for e in t["excluded_trials"]] == ["trial_004"] and "content_groups" in t["excluded_trials"][0]["reason"]
    # the unread file is listed with its inventory trials (never opened)
    assert [os.path.basename(u["file"]) for u in t["unread_files"]] == ["sub-024_run-2.h5"]
    assert t["unread_files"][0]["inventory_trials"] == [
        {"trial": "trial_001", "kind": "ss", "hearing": "nh", "target_sha": src["shas"]["tE"], "masker_sha": None, "masker_offset_s": None},
        {"trial": "trial_002", "kind": "cs", "hearing": "nh", "target_sha": src["shas"]["tC"], "masker_sha": src["shas"]["mA"],
         "masker_offset_s": 3.25}]
    rec = t["checks"]["inventory_reconciliation"]
    assert rec["trials"] == {"hi/cs/loaded": 2, "hi/ss/loaded": 2, "nh/cs/loaded": 3, "nh/cs/unread_file": 1, "nh/ss/excluded": 1,
                             "nh/ss/loaded": 7, "nh/ss/unread_file": 1}
    assert rec["nh_single_talker"] == {"inventory_trials": 9, "inventory_shas": 4, "inventory_shas_ge2_listeners": 3,
                                       "inventory_trials_on_shas_ge2": 8, "cache_trials": 7, "cache_shas": 3,
                                       "cache_shas_ge2_listeners": 2, "cache_trials_on_shas_ge2": 6}
    assert rec["shas_below_2_listeners_in_cache"] == [src["shas"]["tE"]]              # its second listener is in the unread file
    assert sorted((r["file"], r["trial"], r["status"]) for r in rec["not_loaded"]) == [
        ("sub-023", "trial_004", "excluded"), ("sub-024_run-2", "trial_001", "unread_file"), ("sub-024_run-2", "trial_002", "unread_file")]
    by = {(q["participant"], q["trial"]): q for q in t["pieces"]}
    for (p, k), q in by.items():
        nh, cs = p in ("sub-021", "sub-022", "sub-023"), q["kind"] == "cs"
        assert q["role"] == ("fit" if nh and not cs else "target_only")
        assert q["content_group"] == DTU_CG[sh[q["stimulus"]]][0] and q["content_half"] == DTU_CG[sh[q["stimulus"]]][1]
        if cs:          # the masker placed on the trial grid at its exact offset; target stage uses the onset rule (§2.2)
            off = DTU_TRIALS[p][k][2]
            ign = streams[q["ignored_stream"]]
            assert q["ignored_lead"] == 0 and q["onset_s"] == off and q["masker_offset_s"] == off and q["ignored_placement"]
            assert ign["kind"] == "masker" and ign["family"] is None and ign["key"] == f"{q['ignored_stimulus']}@{off!r}"
            assert ign["placement"]["delay_64"] == off * 64 and ign["placement"]["masker_sha"] == q["ignored_stimulus"]
            assert q["segment_starts_target_stage"] == q["segment_starts"] and q["segment_starts"][0] >= (off + C.CS_LEAD_S) * 64
    # placed maskers: the masker's own contract envelope (computed here) delayed by frac_delay (checked against analytic tones below)
    placed = [x for x in streams if x["kind"] == "masker"]
    assert sorted((sh[x["placement"]["masker_sha"]], x["placement"]["offset_s"]) for x in placed) == [("mA", 3.0), ("mA", 4.0078125),
                                                                                                     ("mB", 3.5)]
    sos = C.env_sos()[0]
    for x in placed:
        raw = src["envs"][sh[x["placement"]["masker_sha"]]].astype(np.float32).astype(np.float64)
        base = C.rms_norm(C.band(C.resample64(raw, 128), sos))
        dly = x["placement"]["delay_64"]
        exp = BP.frac_delay(base, dly, int(np.ceil(dly)) + len(base))
        got = env[x["offset"]:x["offset"] + x["length"]].astype(np.float64)
        assert x["length"] == len(exp) and x["source_sha256"] == hashlib.sha256(raw.tobytes()).hexdigest()
        np.testing.assert_allclose(got, exp, atol=1e-5)
        D = int(np.floor(dly))
        assert not got[:D - BP.FRAC_HALF].any()                                       # silent before the masker starts
        if dly == int(dly):                                                           # integer delay: an exact shift
            np.testing.assert_allclose(got[D:], base, atol=1e-6)
    assert len(streams) == 6 + 3 and {x["kind"] for x in streams} == {"attended", "masker"}
    pres = {p["key"]: p for p in t["presentations"]}
    tA = f"dtu:{src['shas']['tA']}|side=left"
    assert pres[tA]["n_listeners"] == 3 and pres[tA]["n_pieces"] == 4 and pres[f"dtu:{src['shas']['tE']}|side=left"]["n_listeners"] == 1
    # the own repeat of sub-022 (trial_001 / trial_004) is listed and never its own partner
    assert t["checks"]["own_repeats"] == [{"participant": "sub-022", "presentation_key": tA,
                                           "pieces": ["dtu:sub-022:trial_001", "dtu:sub-022:trial_004"]}]
    assert by[("sub-022", "trial_004")]["own_repeat_pieces"] == ["dtu:sub-022:trial_001"] and by[("sub-021", "trial_001")]["own_repeat_pieces"] == []
    shared_cs = f"dtu:{src['shas']['tC']}+{src['shas']['mA']}@3.0|side=right"
    assert pres[shared_cs]["n_listeners"] == 2
    hi = [p for p in t["presentations"] if "|eq=" in p["key"]]
    assert len(hi) == 4 and all(p["n_listeners"] == 1 for p in hi)                    # equalised: unique per listener
    assert by[("sub-001", "trial_001")]["stream"] == by[("sub-002", "trial_001")]["stream"]   # same woa waveform, own presentations
    assert by[("sub-001", "trial_001")]["presentation"] != by[("sub-002", "trial_001")]["presentation"]
    parts = {p["participant"]: p for p in t["participants"]}
    assert [parts[x]["donor"] for x in ("sub-001", "sub-021")] == [False, True] and parts["sub-021"]["age"] == 42.0
    assert t["checks"]["nh_single_talker_shas_with_mixed_sides"] == [] and t["checks"]["dtu_cf0_cf1_same_keys"]
    assert t["unit"]["supported"] and t["unit"]["source_unit"] == "uV" and t["unit"]["documented"]["unit"] == "uV"
    assert parts["sub-021"]["sd_prez_unit"] == "uV" and set(parts["sub-021"]["sd_prez"]) == {"A", "A_2_8"}
    # CAR (ours) in both caches; values against an independent computation
    for pid in ("sub-021", "sub-001"):
        mine = [q for q in t["pieces"] if q["participant"] == pid]
        car = [src["eeg"][(pid, q["trial"])][:64].astype(np.float64) for q in mine]
        car = [x - x.mean(0, keepdims=True) for x in car]
        for cm in ("A", "C"):
            exp = _expected(car, [], C.GUARDS["dtu"], "C" if cm == "C" else "z", 1.0)
            mm = _cache(d, cm)
            for q, e in zip(mine, exp):
                got = np.asarray(mm[q["row_offset"]:q["row_offset"] + q["T_eeg"]], np.float64).T
                np.testing.assert_allclose(got, e, rtol=2e-3, atol=2e-3 * (1 if cm == "A" else np.abs(e).max()))
        rows = np.asarray(_cache(d, "C")[mine[0]["row_offset"]:mine[0]["row_offset"] + mine[0]["T_eeg"]], np.float64)
        assert np.abs(rows.sum(1)).max() < 1e-2 * np.abs(rows).max() * 8              # zero channel sum up to float16 rounding
        exp_b = _sd_2_8(car, [], C.GUARDS["dtu"])
        assert parts[pid]["sd_prez"]["A_2_8"] == pytest.approx(exp_b, rel=1e-7)
    with pytest.raises(ValueError):
        BP.parse_modes("dtu", "B")


def test_frac_delay_against_analytic_tones():
    n = np.arange(3000)
    for f in (2.0, 5.0, 8.0):
        w = 2 * np.pi * f / 64
        x = np.sin(w * n + 0.2)
        for d in (256.5, 241.875, 192.0 + 1 / 3, 0.25):
            y = BP.frac_delay(x, d, int(np.ceil(d)) + len(x))
            D = int(np.floor(d))
            m = np.arange(D + BP.FRAC_HALF + 8, D + len(x) - BP.FRAC_HALF - 8)
            np.testing.assert_allclose(y[m], np.sin(w * (m - d) + 0.2), atol=1e-4)     # x(n - d), not a rounded shift
            assert not y[:max(0, D - BP.FRAC_HALF - 1)].any() and len(y) == int(np.ceil(d)) + len(x)
    x = np.random.default_rng(0).standard_normal(400)
    for d in (0, 7, 64):
        y = BP.frac_delay(x, float(d), d + 400)
        assert np.array_equal(y[d:], x) and not y[:d].any()
    with pytest.raises(ValueError):
        BP.frac_delay(x, -1.0, 10)
    # rounding the 4.0078125 s DTU offset to 64 Hz samples would shift a 5 Hz component by 7.8 ms: about 0.25 rad
    assert abs(BP.frac_delay(np.sin(2 * np.pi * 5 / 64 * n), 256.5, 3257)[1000] - np.sin(2 * np.pi * 5 / 64 * (1000 - 257))) > 0.2


# ---------------------------------------------------------------------------------------------------------- Federici
def test_federici_identities_phantom_and_items(tmp_path, monkeypatch, fixture_tables):
    src = make_fed(tmp_path, monkeypatch)
    out = tmp_path / "cache"
    s = BP.build("federici", "A,C", str(out), log=QUIET)
    assert s["caches"] == {"A": "done", "C_partial": "done"} and s["mode_c"]["mode"] == "C_partial"
    d, t, streams, env = _load(out, "federici")
    _schema_check(t, streams, fixture_tables, "federici")
    _layout_check(t, "federici")
    parts = {p["participant"]: p for p in t["participants"]}
    assert list(parts) == FED_ORDER
    hc, hv, ph = parts["HC:1001"], parts["HC-v:1001"], parts["Artifact:0306_bi"]
    assert hc["uid"] == "federici:HC:1001" != hv["uid"] == "federici:HC-v:1001"          # separate identities
    assert hc["identity"] == hv["identity"] == "1001" and hc["fold"] == hv["fold"] >= 0  # one fold key (ALN3 Option A)
    assert parts["HC:1002"]["fold"] == parts["HC-v:1002"]["fold"]
    assert parts["CI:0001"]["identity"] == "CI:0001" and ph["identity"] == "Artifact:0306_bi"
    assert t["partner_exclusions"] == [["federici", "HC:1001", "HC-v:1001"], ["federici", "HC:1002", "HC-v:1002"]]
    assert ph["test_only"] and not ph["donor"] and ph["phantom"] and ph["fold"] == -1
    assert all(p["donor"] and not p["test_only"] for k, p in parts.items() if k != "Artifact:0306_bi")
    fit_end = t["cohort_info"]["role_slabs"]["fit"][1]
    inv = {v: k for k, v in src["keys"].items()}
    for q in t["pieces"]:
        phantom, n = q["participant"] == "Artifact:0306_bi", inv[q["stimulus"]]
        assert q["role"] == ("target_only" if phantom else "fit") and (q["row_offset"] >= fit_end) == phantom
        # condition is an item property (scan_audio.py, the fixture); the session's own label is session_condition
        assert q["condition"] == ("phantom" if phantom else "vocoded" if n[0] == "V" else "natural")
        assert q["session_condition"] == ("phantom" if phantom else "vocoded" if q["group"] == "HC-v" else "natural")
        assert q["presentation_key"] == f"federici:{q['stimulus']}" + ("|phantom" if phantom else "")
        assert q["content_group"] == FED_GROUP[n] and q["content_role"] == ("fit", "es", "test")[FED_GROUP[n]]
        multi = FED_GROUP[n] in (0, 1)
        assert (q["family_offset"] is None) == multi and t["families"][q["family"]]["clock"] == ("pending_C3" if multi else "known")
    pres = {p["key"]: p for p in t["presentations"]}
    n1 = pres[f"federici:{src['keys']['N1']}"]
    assert n1["n_listeners"] == 4 and n1["condition"] == "natural"                       # HC 1001, HC 1002, CI 00010 and HC-v 1002
    assert pres[f"federici:{src['keys']['N1']}|phantom"]["n_listeners"] == 1               # the phantom never shares a presentation
    assert pres[f"federici:{src['keys']['V1']}"]["n_listeners"] == 2 and pres[f"federici:{src['keys']['V1']}"]["condition"] == "vocoded"
    assert t["checks"]["items_heard_in_natural_and_vocoded_sessions"] == [src["keys"]["N1"]]
    assert t["checks"]["n_items_by_condition"] == {"natural": 3, "vocoded": 2}
    s1 = {q["stream"] for q in t["pieces"] if q["stimulus"] == src["keys"]["N1"]}
    assert len(s1) == 1 and len(streams) == len(src["items"])                              # one stream per item (scale removed)
    assert t["unit"]["supported"] and t["unit"]["documented"]["unit"] is None and t["unit"]["source_unit"] == "uV"
    assert set(t["unit_evidence"]["test_only"]) == {"Artifact:0306_bi"} and t["unit"]["participant_medians"]["n"] == 6
    assert set(hc["sd_prez"]) == {"A"}                                                     # Federici: the authors' 2-8 Hz only
    for pid in ("HC-v:1001", "Artifact:0306_bi"):
        mine = [q for q in t["pieces"] if q["participant"] == pid]
        for cm in ("A", "C_partial"):
            exp = _expected(list(src["eeg"][pid]), [], C.GUARDS["federici"], "C" if cm != "A" else "z", 1.0, fs=100)
            mm = _cache(d, cm)
            for q, e in zip(mine, exp):
                got = np.asarray(mm[q["row_offset"]:q["row_offset"] + q["T_eeg"]], np.float64).T
                assert got.shape == (32, 1920)
                np.testing.assert_allclose(got, e, rtol=2e-3, atol=2e-3 * (1 if cm == "A" else np.abs(e).max()))


def test_anti_aliasing_band_and_timing_end_to_end(tmp_path, monkeypatch):
    """Independent of contract.resample64 / band: EEG tones at 10 and 20 Hz (pass band), a 40 Hz tone (stopband: aliases to 24 Hz
    at 64 Hz) and a Gaussian pulse at 7.5 s; an envelope with 5 Hz (pass) and 1 Hz (stop) modulation. Amplitudes and timing are
    checked against their analytic values in the mode-C cache (uV) and env_f32.npy."""
    t100 = np.arange(N100) / 100.0

    def eeg_fn(who, b, x):
        if who == "HC/1001" and b == 0:
            x = x.copy()
            x[0] = 50 * np.sin(2 * np.pi * 10 * t100) + 30 * np.sin(2 * np.pi * 20 * t100) + 50 * np.sin(2 * np.pi * 40 * t100)
            x[1] = 100 * np.exp(-0.5 * ((t100 - 7.5) / 0.03) ** 2)
        return x

    def items_fn(items):
        items["N3"] = 1.0 + 0.4 * np.sin(2 * np.pi * 5 * t100 + 0.3) + 0.4 * np.sin(2 * np.pi * 1 * t100)
        return items
    src = make_fed(tmp_path, monkeypatch, eeg_fn=eeg_fn, items_fn=items_fn)
    out = tmp_path / "cache"
    BP.build("federici", "A,C", str(out), log=QUIET)
    d, t, streams, env = _load(out, "federici")
    q = next(q for q in t["pieces"] if q["participant"] == "HC:1001" and q["trial"] == "block_0")
    x = np.asarray(_cache(d, "C_partial")[q["row_offset"]:q["row_offset"] + q["T_eeg"]], np.float64).T
    assert x.shape == (32, 1920)
    assert _amp(x[0], 10) == pytest.approx(50, rel=3e-3) and _amp(x[0], 20) == pytest.approx(30, rel=3e-3)   # h_aa pass band
    assert _amp(x[0], 24) < 50 * 10 ** (-55 / 20)                                 # 40 Hz: stopband >= 59.7 dB, no alias at 24 Hz
    k = int(np.argmax(x[1]))
    delta = 0.5 * (x[1, k - 1] - x[1, k + 1]) / (x[1, k - 1] - 2 * x[1, k] + x[1, k + 1])
    assert k == 480 and abs(delta) < 0.02                                          # 7.500 s in, 7.500 s out (sample 0 kept)
    s3 = next(s for s in streams if s["key"] == src["keys"]["N3"])
    y = env[s3["offset"]:s3["offset"] + s3["length"]].astype(np.float64)
    n = np.arange(len(y))
    m = slice(64, len(y) - 64)
    ph = 2 * np.pi * 5 * n / 64 + 0.3
    a, b = np.linalg.lstsq(np.stack([np.sin(ph[m]), np.cos(ph[m])], 1), y[m], rcond=None)[0]
    assert abs(b / a) < 2e-3                                                       # zero phase: no delay in h_aa or 2-8 Hz
    assert _amp(y, 1) / _amp(y, 5) < 10 ** (-55 / 20)                              # 1 Hz: about -63 dB (zero-phase 2-8 Hz)


def test_phantom_outside_the_human_band_keeps_mode_c(tmp_path, monkeypatch):
    src = make_fed(tmp_path, monkeypatch, scale={"Artifact/0306_bi": 1e-3})          # median channel SD about 0.004 uV
    out = tmp_path / "cache"
    s = BP.build("federici", "A,C", str(out), log=QUIET)
    assert s["caches"] == {"A": "done", "C_partial": "done"}
    d, t, _, _ = _load(out, "federici")
    assert t["unit"]["supported"] and t["mode_c"]["supported"] and t["unit"]["participant_medians"]["other_unit"] == []
    ev = t["unit_evidence"]["test_only"]["Artifact:0306_bi"]
    assert ev["median_prez_sd"] < 0.1 and ev["magnitude_unit"] is None and not ev["in_cohort_band"]
    u = _json(os.path.join(d, BP.DONE_DIR, "C_partial", "_unit.json"))
    assert u["first_participant"] == "HC:1001" and not u["first_participant_test_only"]
    mk = _json(BP._marker(d, "C_partial", "Artifact:0306_bi"))
    assert mk["test_only"] and not mk["own_magnitude"]["in_cohort_band"]
    mine = [q for q in t["pieces"] if q["participant"] == "Artifact:0306_bi"]          # its rows stay in the cohort unit (uV)
    for q, e in zip(mine, _expected(list(src["eeg"]["Artifact:0306_bi"]), [], C.GUARDS["federici"], "C", 1.0, fs=100)):
        got = np.asarray(_cache(d, "C_partial")[q["row_offset"]:q["row_offset"] + q["T_eeg"]], np.float64).T
        np.testing.assert_allclose(got, e, rtol=2e-3, atol=2e-3 * np.abs(e).max())


def test_a_human_outside_the_band_disables_mode_c_and_leaves_no_partial(tmp_path, monkeypatch):
    make_fed(tmp_path, monkeypatch, scale={"HC-v/1002": 1e-4})                       # the sixth participant built
    out = tmp_path / "cache"
    s = BP.build("federici", "A,C", str(out), log=QUIET)
    d, t, _, _ = _load(out, "federici")
    assert s["caches"] == {"A": "done", "C_partial": "unsupported"}
    assert not os.path.exists(os.path.join(d, BP._partial(C.CACHE_FILE["C_partial"]))) and not os.path.exists(
        os.path.join(d, C.CACHE_FILE["C_partial"]))
    assert "HC-v:1002" in _json(os.path.join(d, BP.DONE_DIR, "C_partial", "_unsupported.json"))["reason"]
    assert os.path.exists(BP._marker(d, "C_partial", "HC:1001")) and not os.path.exists(BP._marker(d, "C_partial", "HC-v:1002"))
    assert not t["unit"]["supported"] and t["unit"]["participant_medians"]["other_unit"] == ["HC-v:1002"]
    assert not t["mode_c"]["supported"] and not t["mode_c"]["built"] and t["caches"]["A"]["nonfinite"] == 0
    assert all(p["sd_prez_uV"]["A"] is None and p["sd_prez_unit"] is None for p in t["participants"])


def test_mode_c_unsupported_for_a_source_normalised_cohort(tmp_path, monkeypatch):
    make_fed(tmp_path, monkeypatch, zscored=True)
    out = tmp_path / "cache"
    s = BP.build("federici", "A,C", str(out), log=QUIET)
    d, t, _, _ = _load(out, "federici")
    assert s["caches"] == {"A": "done", "C_partial": "unsupported"}
    assert not os.path.exists(os.path.join(d, C.CACHE_FILE["C_partial"]))
    assert not os.path.exists(os.path.join(d, BP._partial(C.CACHE_FILE["C_partial"])))   # never created: no unit, no file
    assert not os.path.exists(os.path.join(d, BP.DONE_DIR, "C_partial", "_unit.json"))
    assert not t["mode_c"]["supported"] and not t["mode_c"]["built"] and "normalised" in t["mode_c"]["reason"]
    assert not t["unit"]["supported"] and t["cohort_info"]["unit"]["name"] is None
    assert all(p["sd_prez_uV"]["A"] is None and len(p["sd_prez"]["A"]) == 32 for p in t["participants"])   # no uV without a unit
    s2 = BP.build("federici", "C", str(out), log=QUIET)                                   # recorded: no silent retry
    assert s2["caches"] == {"C_partial": "unsupported"}


def test_unit_rules():
    assert BP.unit_from_magnitude([5e-6, 1e-5, 2e-5])[0] == "V"
    assert BP.unit_from_magnitude([3.0, 9.0, 12.0])[0] == "uV"
    name, det = BP.unit_from_magnitude([1.0, 1.001, 0.999, 1.0])
    assert name is None and "normalised" in det["reason"]
    assert BP.unit_from_magnitude([5e4, 6e4])[0] is None and BP.unit_from_magnitude([None, float("nan")])[0] is None
    ok = BP.decide_unit(("V", "doc"), ("V", {"median": 1e-5}))
    assert ok["supported"] and ok["factor_to_uV"] == 1e6 and ok["name"] == "uV"
    assert not BP.decide_unit(("uV", "doc"), ("V", {}))["supported"]                   # documented and magnitude disagree
    assert not BP.decide_unit(("uV", "doc"), (None, {"reason": "x"}))["supported"]
    assert BP.decide_unit((None, "none"), ("uV", {}))["factor_to_uV"] == 1.0
    assert not BP.decide_unit((None, "none"), (None, {}))["supported"]


# ---------------------------------------------------------------------------------------------------------- resume, modes, lock
def _tree(d):
    out = {}
    for root, _, files in os.walk(d):
        for f in files:
            if f == BP.LOCK:
                continue
            p = os.path.join(root, f)
            out[os.path.relpath(p, d)] = _sha(p)
    return out


def test_resume_after_interruption_is_byte_identical(tmp_path, monkeypatch):
    make_fau(tmp_path, monkeypatch)
    clean = tmp_path / "clean"
    BP.build("fau", "A,B,C", str(clean), log=QUIET)
    calls = []

    class Flaky(BP.FauSource):
        def read(self, p, sigs):
            calls.append(p["participant"])
            if len(calls) == 3 and fail[0]:
                raise RuntimeError("preempted")
            return super().read(p, sigs)
    fail = [True]
    monkeypatch.setitem(BP.SOURCES, "fau", Flaky)
    resumed = tmp_path / "resumed"
    with pytest.raises(RuntimeError, match="preempted"):
        BP.build("fau", "A,B,C", str(resumed), log=QUIET)
    assert not os.path.exists(resumed / "fau" / C.CACHE_FILE["A"])
    fail[0], calls[:] = False, []
    BP.build("fau", "A,B,C", str(resumed), log=QUIET)
    assert calls == ["101", "201", "303"]                                                 # only the participants not yet done
    a, b = _tree(clean / "fau"), _tree(resumed / "fau")
    assert a == b
    calls[:] = []
    BP.build("fau", "A,B,C", str(resumed), log=QUIET)                                    # complete: nothing is read again
    assert calls == [] and _tree(resumed / "fau") == a


def test_resume_after_the_last_participant_finalises_the_written_partial(tmp_path, monkeypatch):
    make_dtu(tmp_path, monkeypatch)
    clean, hit = tmp_path / "clean", tmp_path / "hit"
    BP.build("dtu", "A,C", str(clean), log=QUIET)
    real = BP._finalise_cache
    monkeypatch.setattr(BP, "_finalise_cache", lambda *a, **k: (_ for _ in ()).throw(KeyboardInterrupt("killed before finalising")))
    with pytest.raises(KeyboardInterrupt):
        BP.build("dtu", "A,C", str(hit), log=QUIET)
    assert os.path.exists(hit / "dtu" / BP._partial(C.CACHE_FILE["C"]))
    monkeypatch.setattr(BP, "_finalise_cache", real)
    s = BP.build("dtu", "A,C", str(hit), log=QUIET)                                     # no participant left: the partial is reopened
    assert s["caches"] == {"A": "done", "C": "done"} and _tree(clean / "dtu") == _tree(hit / "dtu")


def test_kill_between_rename_and_record_recovers(tmp_path, monkeypatch):
    make_dtu(tmp_path, monkeypatch)
    clean, hit = tmp_path / "clean", tmp_path / "hit"
    BP.build("dtu", "A,C", str(clean), log=QUIET)
    real, n = BP._write_json, [0]

    def flaky(path, obj):
        if path.endswith(".done.json") and not n[0]:
            n[0] += 1
            raise KeyboardInterrupt("killed after os.replace")
        return real(path, obj)
    monkeypatch.setattr(BP, "_write_json", flaky)
    with pytest.raises(KeyboardInterrupt):
        BP.build("dtu", "A,C", str(hit), log=QUIET)
    d = hit / "dtu"
    assert os.path.exists(d / C.CACHE_FILE["A"]) and not os.path.exists(d / (C.CACHE_FILE["A"] + ".done.json"))
    s = BP.build("dtu", "A,C", str(hit), log=QUIET)
    assert s["caches"] == {"A": "done", "C": "done"} and _tree(clean / "dtu") == _tree(d)


def test_separate_mode_jobs_merge_and_lock(tmp_path, monkeypatch):
    make_dtu(tmp_path, monkeypatch)
    one, two = tmp_path / "one", tmp_path / "two"
    BP.build("dtu", "A,C", str(one), log=QUIET)
    BP.build("dtu", "A", str(two), log=QUIET)
    t = _json(two / "dtu" / BP.TABLE)
    assert set(t["caches"]) == {"A"} and not t["mode_c"]["built"] and t["mode_c"]["supported"]
    BP.build("dtu", "C", str(two), log=QUIET)
    assert _tree(one / "dtu") == _tree(two / "dtu")                                    # same bytes as the combined job
    import fcntl
    with open(two / "dtu" / BP.LOCK, "a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="another build"):
            BP.build("dtu", "A", str(two), log=QUIET)
    BP.build("dtu", "A", str(two), log=QUIET)                                            # released


def test_layout_change_is_refused(tmp_path, monkeypatch):
    src = make_fau(tmp_path, monkeypatch)
    out = tmp_path / "cache"
    opened, real = [], h5py.File

    def rec_file(path, *a, **k):
        opened.append(os.fspath(path))
        return real(path, *a, **k)
    monkeypatch.setattr(h5py, "File", rec_file)
    BP.build("fau", "A", str(out), participants=["101"], log=QUIET)
    assert {p for p in opened if p.startswith(str(src["stageb"]))} == {str(src["stageb"] / "ci" / "101.h5")}   # a dry run opens one
    t = _json(out / "fau" / BP.TABLE)
    assert t["partial"] and [p["participant"] for p in t["participants"]] == ["101"]
    assert {p["fold"] for p in t["participants"]} == {BP.FauSource().data.fau_panel()[1]["101"][1]}
    with pytest.raises(RuntimeError, match="another layout"):
        BP.build("fau", "A", str(out), log=QUIET)
    with pytest.raises(ValueError, match="unknown participants"):
        BP.build("fau", "A", str(tmp_path / "x"), participants=["999"], log=QUIET)


# ---------------------------------------------------------------------------------------------------------- data-use guards
def test_restricted_paths_are_never_opened(tmp_path, monkeypatch):
    sk = "/projects/x/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_eeg"
    for p in (f"{sk}/sub-019/ses-shortstories01/eeg/x_eeg.npy", f"{sk}/sub-026_ses-varyingStories02_run-01_eeg.npy",
              "/tmp/SparrKULee/sub-020/a.npy", f"{sk}/sub-021", f"{sk}/sub-022/"):
        with pytest.raises(BP.RestrictedAccess):
            BP.check_path(p)
    for p in (f"{sk}/sub-018/a.npy", f"{sk}/sub-0190/a.npy", "/projects/x/dtu_snhl/sub-021.h5", "/x/fed/HC/sub-019.h5"):
        assert BP.check_path(p) == p
    restricted = tmp_path / "sparrkulee_copy" / "sub-021"
    os.makedirs(restricted)
    link = tmp_path / "innocent.h5"
    os.symlink(restricted / "x.h5", link)
    with pytest.raises(BP.RestrictedAccess):
        BP.check_path(link)                                                              # resolved through the symlink
    with pytest.raises(BP.RestrictedAccess):                                             # the cache helper for C6 too
        BP.with_band_sd({"cohort_info": {"layout": [], "guards": [128, 128]}, "pieces": [], "participants": []},
                        str(tmp_path / "sparrkulee" / "sub-019"))
    # a source tree pointed into a SparrKULee restricted directory is refused before any file is opened
    make_fed(tmp_path, monkeypatch)
    bad = tmp_path / "sparrkulee_mirror" / "sub-019"
    os.makedirs(bad / "HC")
    os.replace(tmp_path / "fed_pre" / "HC" / "1001.h5", bad / "HC" / "1001.h5")
    monkeypatch.setattr(ALD, "FED_PRE", str(bad))
    opened, real = [], h5py.File

    def rec_file(path, *a, **k):
        opened.append(os.fspath(path))
        return real(path, *a, **k)
    monkeypatch.setattr(h5py, "File", rec_file)
    with pytest.raises(BP.RestrictedAccess):
        BP.build("federici", "A", str(tmp_path / "cache"), log=QUIET)
    assert not any("sub-019" in p for p in opened)


def test_full_builds_open_nothing_restricted_and_unpickle_nothing(tmp_path, monkeypatch):
    make_fau(tmp_path / "f", monkeypatch)
    opened, real_h5, real_open = [], h5py.File, builtins.open

    def rec_h5(path, *a, **k):
        opened.append(os.fspath(path))
        return real_h5(path, *a, **k)

    def rec_open(path, *a, **k):
        if isinstance(path, (str, bytes, os.PathLike)):
            opened.append(os.fspath(path))
        return real_open(path, *a, **k)
    monkeypatch.setattr(h5py, "File", rec_h5)
    monkeypatch.setattr(builtins, "open", rec_open)
    import pickle
    monkeypatch.setattr(pickle, "load", lambda *a, **k: (_ for _ in ()).throw(AssertionError("unpickled")))
    monkeypatch.setattr(pickle, "loads", lambda *a, **k: (_ for _ in ()).throw(AssertionError("unpickled")))
    BP.build("fau", "A,C", str(tmp_path / "cache"), log=QUIET)
    make_dtu(tmp_path / "d", monkeypatch)
    BP.build("dtu", "A", str(tmp_path / "cache"), log=QUIET)
    make_fed(tmp_path / "e", monkeypatch)
    BP.build("federici", "A", str(tmp_path / "cache"), log=QUIET)
    assert opened and not any("sparrkulee" in p.casefold() for p in opened)
    assert not any(p.endswith((".pkl", ".data_dict", ".npz.gz")) for p in opened)
    with real_open(BP.__file__) as fh:
        src = fh.read()
    assert "import pickle" not in src and "allow_pickle=True" not in src
    assert all("allow_pickle=False" in line for line in src.splitlines() if "np.load(" in line and "def " not in line)


# ---------------------------------------------------------------------------------------------------------- CLI
def test_cli(tmp_path, monkeypatch, capsys):
    make_fau(tmp_path, monkeypatch)
    out = tmp_path / "dry"
    assert BP.main(["--cohort", "fau", "--mode", "A,B,C", "--out", str(out), "--allow-other-out", "--participants", "101"]) == 0
    t = _json(out / "fau" / BP.TABLE)
    assert t["partial"] and set(t["caches"]) == {"A", "B", "C"} and t["pieces"][0]["participant"] == "101"
    with pytest.raises(SystemExit):
        BP.main(["--cohort", "fau", "--mode", "A", "--out", str(tmp_path / "other")])        # not the cache root
    monkeypatch.setattr(BP, "CACHE_ROOT", str(tmp_path / "root"))
    with pytest.raises(SystemExit):
        BP.main(["--cohort", "fau", "--mode", "A", "--out", str(tmp_path / "root"), "--participants", "101"])
    assert not os.path.exists(tmp_path / "root")
    with pytest.raises(SystemExit):
        BP.main(["--cohort", "dtu", "--mode", "B", "--out", str(out), "--allow-other-out"])
    with pytest.raises(SystemExit):
        BP.main(["--cohort", "sparrkulee", "--mode", "A", "--out", str(out), "--allow-other-out"])
    with pytest.raises(SystemExit):
        BP.main(["--cohort", "all", "--mode", "A", "--out", str(out), "--allow-other-out"])


def test_cli_all_cohorts_in_one_job(tmp_path, monkeypatch):
    make_fau(tmp_path, monkeypatch)
    make_dtu(tmp_path, monkeypatch)                                                       # shares repo / pub with FAU: no collision
    make_fed(tmp_path, monkeypatch)
    out = tmp_path / "all"
    assert BP.main(["--cohort", "all", "--mode", "all", "--out", str(out), "--allow-other-out"]) == 0
    for c, cms in (("fau", {"A", "B", "C"}), ("dtu", {"A", "C"}), ("federici", {"A", "C_partial"})):
        t = _json(out / c / BP.TABLE)
        assert set(t["caches"]) == cms and not t["partial"] and t["mode_c"]["built"]


# ---------------------------------------------------------------------------------------------------------- mode-C scale (§2.13)
def test_mode_c_scales_match_the_fixture(fixture_tables):
    man, tabs = fixture_tables["manifest"], fixture_tables["tables"]
    tables = {c: {"layout": tabs[c]["_layout"], "participants": tabs[c]["participants"]} for c in tabs}
    units = {c: 1.0 for c in tabs}                                                        # the fixture's caches are in uV
    for target in ("fau", "dtu", "federici"):
        got = BP.mode_c_scales(target, tables, units, band="own")                         # the fixture pools every donor's 'A'
        exp = man["mode_c"][target]["scale"]
        assert got["supported"] and set(got["scale"]) == set(exp)
        for n in exp:
            assert got["scale"][n] == pytest.approx(exp[n], rel=1e-12)
    assert not BP.mode_c_scales("fau", tables, {**units, "sparrkulee": None})["supported"]
    half = {c: (0.5 if c == "dtu" else 1.0) for c in tabs}                                # a donor's factor_to_uV enters the scale
    assert BP.mode_c_scales("fau", tables, half, band="own")["scale"] != BP.mode_c_scales("fau", tables, units, band="own")["scale"]


def _ptab(cohort, sd, sd_b=None, factor=1.0, n=1):
    """A cohort table as C4 / C5 write it: sd_prez in the source unit, sd_prez_uV = sd_prez x factor."""
    lay, parts = list(C.MONTAGES[cohort]), []
    for i in range(n):
        p = {"participant": f"{cohort}{i}", "donor": True, "sd_prez": {"A": [sd * (1 + 0.01 * i)] * len(lay)}}
        if sd_b is not None:
            p["sd_prez"]["A_2_8"] = [sd_b * (1 + 0.01 * i)] * len(lay)
        p["sd_prez_uV"] = {k: [v * factor for v in vals] for k, vals in p["sd_prez"].items()}
        parts.append(p)
    return {"layout": lay, "participants": parts}


def test_mode_c_scales_same_band_rule_and_units():
    tables = {"sparrkulee": _ptab("sparrkulee", 3.0, n=2), "fau": _ptab("fau", 1.1e-5, 6e-6, factor=1e6),
              "dtu": _ptab("dtu", 12.7, 5.5), "federici": _ptab("federici", 4.8)}
    units = {"sparrkulee": 1.0, "fau": 1e6, "dtu": 1.0, "federici": 1.0}
    # FAU target (1-20 Hz): SparrKULee and DTU 'A'; Federici's 2-8 Hz SDs have no same-band signal and never enter
    s = BP.mode_c_scales("fau", tables, units)
    assert s["supported"] and s["stat_keys"] == {"sparrkulee": "A", "dtu": "A"} and s["donors_without_band"] == ["federici"]
    assert s["scale"]["Cz"] == pytest.approx(3.03) and s["scale"]["TP9"] == pytest.approx(3.03) and "TP9" in s["fallback"]
    own = BP.mode_c_scales("fau", tables, units, band="own")
    assert own["scale"]["TP9"] == pytest.approx(4.8) and "TP9" not in own["fallback"]  # the band mix the same-band rule avoids
    # Federici target (2-8 Hz): FAU / DTU 'A_2_8'; SparrKULee's signal contains the band but its table lacks the statistic
    f = BP.mode_c_scales("federici", tables, units)
    assert not f["supported"] and f["donors_missing_band"] == ["sparrkulee"] and "with_band_sd" in f["reason"]
    f = BP.mode_c_scales("federici", tables, units, missing_band="skip")
    assert f["supported"] and f["stat_keys"] == {"fau": "A_2_8", "dtu": "A_2_8"} and f["scale"]["Cz"] == pytest.approx(5.75)
    assert f["scale"]["FT9"] == pytest.approx(5.5) and "FT9" in f["fallback"]
    # sd_prez stays in the source unit (FAU volts): sd_prez_uV is used and must agree with sd_prez x units
    with pytest.raises(ValueError, match="factor_to_uV"):
        BP.mode_c_scales("dtu", tables, {**units, "fau": 1.0})
    assert BP.mode_c_scales("dtu", tables, units)["scale"]["Cz"] == pytest.approx(3.03)  # median of 3.0, 3.03 and 11.0 uV
    assert BP.mode_c_scales("dtu", tables, units, donors=("fau",))["scale"]["Cz"] == pytest.approx(11.0)   # 1.1e-5 V -> 11 uV
    no_uv = {**tables, "fau": {**tables["fau"], "participants": [{k: v for k, v in p.items() if k != "sd_prez_uV"}
                                                                 for p in tables["fau"]["participants"]]}}
    assert BP.mode_c_scales("dtu", no_uv, units)["scale"] == BP.mode_c_scales("dtu", tables, units)["scale"]   # fixture-style table


def test_with_band_sd_derives_the_2_8_statistic_from_a_z_cache(tmp_path, monkeypatch):
    make_fau(tmp_path, monkeypatch)
    out = tmp_path / "cache"
    BP.build("fau", "A", str(out), log=QUIET)
    d, t, _, _ = _load(out, "fau")
    strip = json.loads(json.dumps(t))
    for p in strip["participants"]:
        for k in ("sd_prez", "sd_prez_uV"):
            p[k].pop("A_2_8")
    strip["cohort_info"].pop("stats_band")
    got = BP.with_band_sd(strip, d)
    assert got["cohort_info"]["stats_band"] == {"A": [1.0, 20.0], "B": [1.0, 20.0], "A_2_8": [2.0, 8.0]}
    for p, q in zip(got["participants"], t["participants"]):
        for a, b in zip(p["sd_prez"]["A_2_8"], q["sd_prez"]["A_2_8"]):           # from float16 z rows: rounding only
            assert (a is None and b is None) or a == pytest.approx(b, rel=3e-3)
        assert p["sd_prez_uV"]["A_2_8"] == pytest.approx([None if v is None else v * 1e6 for v in p["sd_prez"]["A_2_8"]])
    assert "A_2_8" not in strip["participants"][0]["sd_prez"]                            # the input table is not modified
    with pytest.raises(ValueError):
        BP.with_band_sd(strip, d, band=(1.0, 20.0))
