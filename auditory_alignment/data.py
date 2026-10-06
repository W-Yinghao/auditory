"""Cohort loaders for the kernel-CS round (IMPLEMENTATION_NOTES §1). Every continuous-speech cohort is returned as

    Cohort(fs, n_ch, participants, eeg [C, N] float32, stim {target: [D, M] float32}, segments)

where a segment is one 5 s piece of one participant's EEG paired with its stimulus stream(s): fields p (participant
index), e0 (EEG bank index of the segment start), s0 / s0_ign (stimulus bank index of the attended / ignored stream at
the same time), role (fit / es / test), kind (ss / cs), uid (stimulus identity of the segment, shared by every
participant who heard it), hard_key (stimulus-defined grouping for hard candidates) and feat (stimulus summary used to
rank hard candidates). The private category task returns trial arrays instead (load_private).
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np

SEG_S = 5.0
AUDIO_FRAMES = 8          # A[t] = target frames t .. t+7
MAX_WIN_S = 0.6           # longest EEG window (0-600 ms)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = "/projects/EEG-foundation-model/auditory_public"
FAU_KCS = f"{PUB}/derived/c3_features_v1/fau_tud/kcs_targets_v1"
DTU_KCS = f"{PUB}/derived/c3_features_v1/dtu/kcs_targets_v1"
STAGEB = f"{PUB}/derived/c3_preproc_v1/fau_tud_stageB"
DTU_PRE = f"{PUB}/derived/c3_preproc_v1/dtu_snhl"
FED_PRE = f"{PUB}/derived/c3_preproc_v1/federici_ci_children"
FED_META = (f"{PUB}/federici_ci_children/mendeley_nzg5g2gzrd_v2/files/Resilience and vulnerability of neural speech "
            "tracking in children with cochlear implants/Code/07_TRF_CI_biomarker/Descrittive&BehavHCCDDDHCv.xlsx")


class Cohort:
    def __init__(self, fs, n_ch, participants, eeg, stim, segments, meta):
        self.fs, self.n_ch, self.participants, self.eeg, self.stim, self.segments, self.meta = fs, n_ch, participants, eeg, stim, segments, meta


def _stdz(arrs, guard):
    V = np.concatenate([a[:, guard:a.shape[1] - guard] for a in arrs], axis=1)
    mu, sd = V.mean(1, keepdims=True), V.std(1, keepdims=True); sd[sd == 0] = 1
    return [((a - mu) / sd).astype(np.float32) for a in arrs]


def _folds(ids_by_group, seed=20261005, n=5):
    rng = np.random.default_rng(seed); out = {}
    for g in sorted(ids_by_group):
        ids = sorted(ids_by_group[g])
        for p_, i in enumerate(rng.permutation(len(ids))):
            out[ids[i]] = p_ % n
    return out


class _Bank:
    def __init__(self):
        self.parts, self.n = [], 0

    def add(self, a):
        off = self.n; self.parts.append(a); self.n += a.shape[1]
        return off

    def array(self):
        return np.concatenate(self.parts, axis=1) if self.parts else np.zeros((0, 0), np.float32)


def _segments_of(n_valid_start, n_valid_end, seg_len, margin_end):
    return list(range(n_valid_start, n_valid_end - seg_len - margin_end + 1, seg_len))


# ------------------------------------------------------------------------------------------------ FAU/TUD
FAU_CF = {0: {"ss": {"fit": "1", "es": "2", "test": "34"}, "cs": {"fit": "05", "es": "6", "test": "789"}},
          1: {"ss": {"fit": "3", "es": "4", "test": "12"}, "cs": {"fit": "78", "es": "9", "test": "056"}}}


def fau_panel():
    split = json.load(open(os.path.join(REPO, "private", "auditory_c3", "public", "fau_tud", "th_split.json")))
    ids = {"th": sorted(split["heldout_half"]),
           "ha": sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(STAGEB, "ha", "*.h5"))),
           "ci": sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(STAGEB, "ci", "*.h5")))}
    folds = _folds(ids)  # identical to auditory_c3.c3dl.full.panel()
    return sorted(split["selection_half"]), {s: (g, folds[s]) for g, ss in ids.items() for s in ss}


def load_fau(content_fold, kinds=("ss",), stage_dir=STAGEB):
    import h5py
    fs, guard = 128, 314
    seg_len = int(SEG_S * fs); margin = int(MAX_WIN_S * fs) + 1 + AUDIO_FRAMES
    dev, panel = fau_panel()
    plist = [{"id": s, "group": "th", "fold": -1, "dev": True} for s in dev] + \
            [{"id": s, "group": g, "fold": f, "dev": False} for s, (g, f) in sorted(panel.items())]
    tf = h5py.File(os.path.join(FAU_KCS, f"fau_cf{content_fold}.h5"), "r")
    targets = ("Ac", "Lz", "Local")
    sbank = {t: _Bank() for t in targets}
    soff = {}

    def stim_off(code, stream):
        key = (code, stream)
        if key not in soff:
            arrs = {t: tf[f"{code}/{stream}/{t}"][()] for t in targets}
            n = min(a.shape[1] for a in arrs.values())
            soff[key] = (sbank["Ac"].add(arrs["Ac"][:, :n]), n)
            for t in ("Lz", "Local"):
                assert sbank[t].add(arrs[t][:, :n]) == soff[key][0]
        return soff[key]
    ebank = _Bank(); segments = []
    for pi, p in enumerate(plist):
        with h5py.File(os.path.join(stage_dir, p["group"], f"{p['id']}.h5"), "r") as f:
            ch = [str(c) for c in f.attrs["channels"]]
            assert len(ch) == 31 and "IO2" not in ch
            trials = [(str(f[t].attrs["stimulus"]), f[t]["eeg_1_20_ica"][()].astype(np.float64)) for t in sorted(f.keys())]
        trials = [(c, x) for c, x in trials if ("ss" in kinds and c[0] == "1") or ("cs" in kinds and c[0] == "2")]
        xs = _stdz([x for _, x in trials], guard)
        for (code, _), x in zip(trials, xs):
            kind = "ss" if code[0] == "1" else "cs"
            roles = FAU_CF[content_fold][kind]
            role = next(r for r, parts in roles.items() if code[2] in parts)
            sa, na = stim_off(code, "attended")
            si = stim_off(code, "distractor") if kind == "cs" else (None, None)
            n = min(x.shape[1], na, si[1] or na)
            e0 = ebank.add(x)
            for st in _segments_of(guard, n - guard, seg_len, margin):
                segments.append({"p": pi, "e0": e0 + st, "s0": sa + st, "s0_ign": (si[0] + st) if kind == "cs" else None,
                                 "role": role, "kind": kind, "uid": f"{code}@{st}", "hard_key": code[1], "part": code[2],
                                 "code": code})
    stim = {t: b.array() for t, b in sbank.items()}
    for s in segments:  # stimulus summary for hard candidates (Ac mean / SD over the segment)
        a = stim["Ac"][:, s["s0"]:s["s0"] + seg_len]
        s["feat"] = np.r_[a.mean(1), a.std(1)]
    return Cohort(fs, 31, plist, ebank.array(), stim, segments, {"dataset": "fau", "content_fold": content_fold, "seg_len": seg_len})


# ------------------------------------------------------------------------------------------------ DTU
def load_dtu(content_fold, kinds=("ss",)):
    import h5py
    import pandas as pd
    fs = 128; seg_len = int(SEG_S * fs); margin = int(MAX_WIN_S * fs) + 1 + AUDIO_FRAMES; start_guard = 64
    part = pd.read_csv(f"{PUB}/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv", sep="\t")
    hs = dict(zip(part.participant_id, part.hearing_status)); age = dict(zip(part.participant_id, part.age))
    subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(REPO, "private", "auditory_c3", "public", "dtu_v2", "*.json")))
    folds = _folds({g: [s for s in subs if hs[s] == g] for g in ("nh", "hi")})
    plist = [{"id": s, "group": hs[s], "fold": folds[s], "dev": False, "age": float(age[s])} for s in subs]
    inv = json.load(open(f"{PUB}/derived/c3_features_v1/dtu/inventory.json"))
    sha = {(r["file"], r["trial"], r["kind"]): (r.get("sha"), r["offset_s"]) for r in inv}
    cg = json.load(open(os.path.join(DTU_KCS, "content_groups.json")))["content"]
    tf = h5py.File(os.path.join(DTU_KCS, f"dtu_cf{content_fold}.h5"), "r")
    targets = ("Ac", "Lz", "Local")
    sbank = {t: _Bank() for t in targets}; soff = {}

    def stim_off(h, lead, n):
        """Stimulus stream for one trial on the EEG time grid: the waveform placed at `lead` samples (zeros before)."""
        key = (h, lead, n)
        if key not in soff:
            arrs = {}
            for t in targets:
                z = tf[f"{h}/{t}"][()]; a = np.zeros((z.shape[0], n), np.float32); m = min(z.shape[1], n - lead)
                a[:, lead:lead + m] = z[:, :m]; arrs[t] = a
            soff[key] = sbank["Ac"].add(arrs["Ac"])
            for t in ("Lz", "Local"):
                assert sbank[t].add(arrs[t]) == soff[key]
        return soff[key]
    ebank = _Bank(); segments = []
    for pi, p in enumerate(plist):
        with h5py.File(os.path.join(DTU_PRE, f"{p['id']}.h5"), "r") as f:
            keys = sorted(f.keys())
            rows = []
            for k in keys:
                g = f[k]; two = str(g.attrs["talkers"]) == "twotalker"
                if (two and "cs" not in kinds) or (not two and "ss" not in kinds):
                    continue
                th, _ = sha.get((p["id"], k, "target"), (None, 0)); mh, moff = sha.get((p["id"], k, "masker"), (None, 0))
                if th is None or th not in cg or th not in tf or (two and (mh is None or mh not in tf)):
                    continue
                rows.append((k, two, th, mh, moff, g["eeg_1_20"][()][:64].astype(np.float64), float(g.attrs["masker_onset_rel_s"]) if two else None))
        xs = _stdz([r[5] for r in rows], start_guard)
        for (k, two, th, mh, moff, _, mon), x in zip(rows, xs):
            n = x.shape[1]
            c = cg[th]
            role = "test" if c["half"] == content_fold else ("es" if c["early_stop"] else "fit")
            sa = stim_off(th, 0, n)
            si = stim_off(mh, int(round(moff * fs)), n) if two else None
            a0 = start_guard if not two else max(start_guard, int(np.ceil((mon + 1.7) * fs)))
            e0 = ebank.add(x)
            for st in _segments_of(a0, n, seg_len, margin):
                segments.append({"p": pi, "e0": e0 + st, "s0": sa + st, "s0_ign": (si + st) if two else None, "role": role,
                                 "kind": "cs" if two else "ss", "uid": f"g{c['group']}@{st}", "hard_key": "dtu", "part": str(c["group"]),
                                 "code": th[:10]})
    stim = {t: b.array() for t, b in sbank.items()}
    for s in segments:
        a = stim["Ac"][:, s["s0"]:s["s0"] + seg_len]
        s["feat"] = np.r_[a.mean(1), a.std(1)]
    return Cohort(fs, 64, plist, ebank.array(), stim, segments, {"dataset": "dtu", "content_fold": content_fold, "seg_len": seg_len})


# ------------------------------------------------------------------------------------------------ Federici
def _fed_ages():
    import pandas as pd
    d = pd.read_excel(FED_META)
    out = {}
    for _, r in d.iterrows():
        code = str(r["codice exp"]).strip()
        out[code] = {"age_years": float(r["età al test in anni"]) if r["età al test in anni"] == r["età al test in anni"] else None,
                     "group_code": int(r["Group"]) if r["Group"] == r["Group"] else None,
                     "behav_acc": float(r["Behav acc"]) if r["Behav acc"] == r["Behav acc"] else None}
    return out


def _fed_id(fname):
    s = fname.lstrip("0")
    return s if s else fname


def load_federici():
    import h5py
    fs = 100; seg_len = int(SEG_S * fs); margin = int(MAX_WIN_S * fs) + 1 + AUDIO_FRAMES
    ages = _fed_ages()
    people = []
    for grp in ("HC", "CI", "HC-v", "Artifact"):
        for p in sorted(glob.glob(os.path.join(FED_PRE, grp, "*.h5"))):
            fid = os.path.basename(p)[:-3]
            ident = fid if grp in ("HC", "HC-v") else f"{grp}:{fid}"  # HC and HC-v of one child share an identity
            people.append({"file": p, "group": grp, "file_id": fid, "identity": ident})
    idents = {g: sorted({q["identity"] for q in people if q["group"] in gs}) for g, gs in (("hc", ("HC", "HC-v")), ("ci", ("CI",)))}
    folds = _folds(idents)
    from .federici_content import OUT as FED_KCS, env_key
    content = {it["key"]: it for it in json.load(open(os.path.join(FED_KCS, "content_groups.json")))["items"]}
    plist = []
    ebank, sbank, segments = _Bank(), _Bank(), []
    env_seen = {}
    for q in people:
        with h5py.File(q["file"], "r") as f:
            E = f["eeg"][()].astype(np.float64); env = f["env"][()].astype(np.float64)
        key = q["file_id"] if q["group"] in ("HC", "HC-v") else ("S" + q["file_id"].lstrip("0").rjust(3, "0") if q["group"] == "CI" else None)
        a = ages.get(_fed_id(q["file_id"]), ages.get(key, {})) if key else {}
        fold = folds.get(q["identity"], -1)
        plist.append({"id": f"{q['group']}:{q['file_id']}", "group": q["group"], "fold": fold, "identity": q["identity"],
                      "dev": False, "age_years": a.get("age_years"), "behav_acc": a.get("behav_acc"), "test_only": q["group"] == "Artifact"})
        pi = len(plist) - 1
        xs = _stdz([seg for seg in E], 20)
        for b, (x, e) in enumerate(zip(xs, env)):
            ez = ((e - e.mean()) / (e.std() + 1e-12)).astype(np.float32)[None]
            h = env_key(ez)
            role, grp_c = content[h]["role"], content[h]["group"]  # strict unseen-content split by envelope content group
            if h not in env_seen:
                env_seen[h] = sbank.add(ez)
            so = env_seen[h]
            e0 = ebank.add(x)
            for st in _segments_of(20, x.shape[1], seg_len, margin):
                segments.append({"p": pi, "e0": e0 + st, "s0": so + st, "s0_ign": None, "role": role, "kind": "ss",
                                 "uid": f"env{so}@{st}", "hard_key": "fed", "part": f"g{grp_c}", "block": b, "code": q["group"]})
    stim = {"envelope": sbank.array()}
    for s in segments:
        a = stim["envelope"][:, s["s0"]:s["s0"] + seg_len]
        s["feat"] = np.r_[a.mean(1), a.std(1), np.abs(np.diff(a, axis=1)).mean(1)]
    return Cohort(fs, 32, plist, ebank.array(), stim, segments, {"dataset": "federici", "content_fold": 0, "seg_len": seg_len})


# ------------------------------------------------------------------------------------------------ private BDF
def load_private():
    """Trial-level private HA/NH data (GX_stage_001 accepted epochs): same children, folds and swaps as C3-DL H-Cur;
    adds calendar age, device-use duration and the early-stop physical blocks (last ~20% blocks of each child)."""
    import pandas as pd
    from auditory_c3.c3dl import hc
    from auditory_c3.private_mi import P
    kids = hc.load_children(); hc.add_swaps(kids)
    folds = hc.folds(kids)
    ch = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "children.csv"))
    info = {f"child{int(r.child)}": r for _, r in ch.iterrows()}
    for k in kids:
        r = info[k["id"]]
        k["fold"] = folds[k["id"]]
        k["age_months"] = float(r.age_months) if r.age_months == r.age_months else None
        k["duration_months"] = float(r.duration_months) if (k["group"] == "HA" and r.duration_months == r.duration_months) else None
        blocks = np.unique(k["block"])
        es_blocks = set(blocks[int(np.floor(0.8 * len(blocks))):].tolist()) if len(blocks) >= 3 else set()
        k["es_mask"] = np.isin(k["block"], list(es_blocks))
    return kids
