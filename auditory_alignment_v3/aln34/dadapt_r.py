"""ALN3.4 R34_DADAPT_R: true-query risk R of the completed lag-local D_ADAPT units - GPU-ready evaluator and aggregation.

Analysis note, written before any R was computed: private/auditory_alignment_v3/aln34/DADAPT_R_NOTE.md (package docs/04 section A:
"keep the original D_ADAPT gain main table; add the true query risk as an explicit new analysis").

The D_ADAPT records (auditory_alignment_v3.run_adapt3, code hash f029aabd1ea656c1) store, per test participant x support fraction x
readout, only gain_bits, rank_pct, top1 and n_query; the adapters were not saved. Per unit this module
  * resolves the frozen same-fold base exactly as run_adapt3.run does (run_complement.base_ready over plan + plan_ext rows);
  * seeds torch's CPU generator with a declared per-unit seed. The original process never seeded it, so the random A initialisation
    of output_low_rank cannot be re-created; none and input_spatial draw nothing from it;
  * calls the imported, unchanged run_adapt3.bundle (readouts fitted with the base, step choice on training participants, refit per
    test participant on the first 10 % / 30 %, query = last 70 %) with run_adapt3._gain replaced, in this process and for this call
    only, by gain_with_risk(). It returns the same four fields computed the same way, plus the true-query logloss R, the
    mismatched-EEG logloss, top5, MRR, the number of candidates K and the temperature;
  * checks the reproduced gain_bits / rank_pct / top1 / n_query / n_support / step choice against the record (tier "exact" for none
    and input_spatial, "seeded_refit" for output_low_rank; rules in the analysis note);
  * writes private/auditory_alignment_v3/aln34/dadapt_r/units/<eid>.json (0600) under execution R34_DADAPT_R_v1 (per-participant
    values, hence private: note, addendum 2, correction C3).
Original records, checkpoints and code are only read; every write refuses the source trees (correction C4).
Aggregation (note, addendum 2, correction C1): none -> adapter and 10 % -> 30 % are paired per identity over the same content folds,
those admitted on both sides; partial and missing pairs are counted in the public JSON and listed in the private per-identity file.

Usage (repo root, eeg2025 interpreter, PYTHONHASHSEED=0, PYTHONPATH=<repo>):
  python -B -m auditory_alignment_v3.aln34.dadapt_r --unit EID [--device cuda] [--out DIR] [--loader original|ss_only]
  python -B -m auditory_alignment_v3.aln34.dadapt_r --units-file F [--shard K/N] [--worker-tag T] [--device cuda]
  python -B -m auditory_alignment_v3.aln34.dadapt_r --aggregate [--update-doc]
  python -B -m auditory_alignment_v3.aln34.dadapt_r --write-units
--units-file runs every unit in a fresh subprocess (as the ALN3 pool ran them) with atomic claims (<out>/claims/<eid>.claim): its own
shard first, then the rest of the list; finished units are skipped; a unit is tried at most 3 times; a requeued Slurm job releases
its own claims. --loader ss_only is for CPU engineering tests within a small RAM budget: the cohort without the competing-speech
trials (each participant still standardised over all of its trials, as the original), EEG stored as float16 by torch's conversion
(the batcher stores it as float16 anyway). The D_ADAPT path reads single-speaker segments only.
"""
from __future__ import annotations

import argparse
import contextlib
import glob
import hashlib
import inspect
import json
import os
import re
import resource
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
from collections import Counter, defaultdict

import numpy as np

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import core
from auditory_alignment_v3 import d_lag_interim as DL
from auditory_alignment_v3.sci_r1 import stats as S

VERSION = "R34_DADAPT_R_v1"
EXEC_PREFIX = "R34DR1_"
SCHEMA = "R34_DADAPT_R_unit_v1"
REPO = core.REPO
RES = os.environ.get("DR_RES", os.path.join(REPO, "results", "auditory_alignment_v3", "aln34", "dadapt_r"))
PRIV = os.environ.get("DR_PRIV", os.path.join(core.OUT, "aln34", "dadapt_r"))
UNITS_DIR = os.path.join(PRIV, "units")  # per-participant values -> private (note, addendum 2, C3); also claims/ and <eid>.FAILED.json
DOCS = os.environ.get("DR_DOCS", os.path.join(REPO, "docs", "auditory_alignment_v3"))
DOC_NAME = "D_ADAPT_TRUE_RISK_RESULTS.md"
NOTE = os.path.join(core.OUT, "aln34", "DADAPT_R_NOTE.md")
UNITS_FILE = os.path.join(core.OUT, "aln34", "dadapt_r_units.txt")
SBATCH = os.path.join(core.OUT, "aln34", "dadapt_r_gpu.sbatch")
LOGS = os.path.join(PRIV, "logs")
RECORDS = os.path.join(core.OUT, "units")
TESTS = os.path.join(REPO, "tests", "auditory_alignment_v3", "aln34", "test_dadapt_r.py")
PY = "/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python"

RECORD_CODE_HASH = "f029aabd1ea656c1"   # every one of the 200 source records (core.code_hash("D_ADAPT"))
ORIGINAL_DEVICE = "NVIDIA A40"          # device of every one of the 200 source records
SEEDS = (3401, 3407, 3413)
PANEL_SEEDS = (3407, 3413)
DATASETS = ("fau", "dtu")
OBJECTIVES = ("NCE", "CS_SINGLE")
ADAPTERS = ("none", "input_spatial", "output_low_rank")
SUPPORTS = ("0.1", "0.3")
READOUTS = ("unified", "native")
TIER = {"none": "exact", "input_spatial": "exact", "output_low_rank": "seeded_refit"}
TOL_GAIN, TOL_RANK, TOL_NONE = 1e-3, 1e-3, 1e-12   # engineering tolerances of the re-fit against the record (note: QC), not gates
MAX_TRIES = 3
EXTRA_FIELDS = ("logloss_bits", "mismatched_logloss_bits", "top5", "mrr", "n_candidates", "tau")
ORIGINAL_FIELDS = ("gain_bits", "rank_pct", "top1", "n_query")
FROZEN = ("auditory_alignment_v3/run_adapt3.py", "auditory_alignment_v3/run_complement.py", "auditory_alignment_v3/core.py",
          "auditory_alignment_v3/local_train.py", "auditory_alignment_v3/run.py", "auditory_alignment_v3/registry.py",
          "auditory_alignment/evaluate.py", "auditory_alignment/data.py", "auditory_alignment/train.py", "auditory_alignment/losses.py",
          "auditory_alignment_v2/run.py", "auditory_alignment_v2/train.py", "auditory_alignment_v2/temporal.py",
          "auditory_alignment_v2/audio_targets.py")
AGG_CODE = ("auditory_alignment_v3/d_lag_interim.py", "auditory_alignment_v3/bc_interim.py", "auditory_alignment_v3/sci_r1/stats.py")
# aggregation metrics: key, readout, field of the per-unit output (None = recorded gain from the source record), direction
# (bc_interim convention: lower -> reference - candidate; higher / raw -> candidate - reference; positive = candidate better for
# lower / higher)
METRICS = (("R_bits", "unified", "logloss_bits", "lower"),
           ("R_bits_native", "native", "logloss_bits", "lower"),
           ("R_mm_bits", "unified", "mismatched_logloss_bits", "raw"),
           ("R_mm_bits_native", "native", "mismatched_logloss_bits", "raw"),
           ("gain_refit", "unified", "gain_bits", "higher"),
           ("gain_refit_native", "native", "gain_bits", "higher"),
           ("gain_record", "unified", None, "higher"),
           ("gain_record_native", "native", None, "higher"))
METRIC_KEYS = tuple(m[0] for m in METRICS)
PRIMARY = "R_bits"
LABELS = {"R_bits": "ΔR unified", "R_bits_native": "ΔR native", "R_mm_bits": "ΔR_mm unified (cand − ref)", "R_mm_bits_native": "ΔR_mm native (cand − ref)",
          "gain_refit": "Δgain unified, refit", "gain_refit_native": "Δgain native, refit", "gain_record": "Δgain unified, record",
          "gain_record_native": "Δgain native, record"}
HAND = ("2.", "3.", "4.", "6.")  # hand-written sections of the results document (carried over verbatim on regeneration)
# source trees this module never writes into (note, addendum 2, C4); also the top level of private/auditory_alignment_v3 itself
PROTECTED = (RECORDS, os.path.join(core.OUT, "ckpt"), os.path.join(core.OUT, "governance"), os.path.dirname(core.PLAN),
             "/projects/EEG-foundation-model/auditory", "<private checkpoint storage>/auditory_alignment_v3")
PAIRING = ("content-fold matched (note, addendum 2, C1): per seed, family member and identity, the reference and the candidate are "
           "averaged over the same content folds, those admitted on both sides; complete = all content folds in which both records hold "
           "the identity; partial = some dropped (kept, counted, listed privately); missing = none kept (listed privately, never filled)")

with open(__file__, "rb") as _fh:
    _SOURCE = _fh.read()  # the source this process loaded
MODULE_SHA256 = hashlib.sha256(_SOURCE).hexdigest()


# ================================================================================================ small helpers
def _utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def protected(path):
    """True when `path` lies in a source tree of PROTECTED or directly in private/auditory_alignment_v3 (symlinks resolved)."""
    rp = os.path.realpath(path)
    if os.path.dirname(rp) == os.path.realpath(core.OUT):
        return True
    for d in PROTECTED:
        rd = os.path.realpath(d)
        if rp == rd or rp.startswith(rd + os.sep):
            return True
    return False


def guard(path):
    if protected(path):
        raise PermissionError(f"refusing to write {path}: protected source tree (analysis note, addendum 2, C4)")
    return path


def check_out_dir(out_dir):
    """--out must not be (or lie inside) a protected tree: outputs are named <eid>.json like the source records."""
    guard(out_dir); guard(os.path.join(out_dir, "x.json")); guard(os.path.join(out_dir, "claims", "x.claim"))
    return out_dir


def write_json(path, obj):
    """atomic write, mode 0600, directories 0700; never into a protected tree."""
    guard(path)
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(BI.jl(obj), f, indent=1, default=float)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return path


def write_text(path, text):
    guard(path)
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return path


def execution_id(eid):
    return EXEC_PREFIX + hashlib.sha256(f"{eid}|{VERSION}".encode()).hexdigest()[:16]


def torch_seed(eid):
    """declared per-unit seed of torch's default generators (analysis note: execution)."""
    return int(hashlib.sha256(f"{eid}|{VERSION}|torch".encode()).hexdigest()[:8], 16)


def evaluator_sha256():
    """sha256 of the source of the value-producing functions (independent of edits to the aggregation code)."""
    fns = (gain_with_risk, risk_capture, loader_scope, _f16, load_fau_ss_only, load_dtu_ss_only, load_cohort_ss_only, in_scope,
           resolve_base, evaluate_unit, reproduction_qc, _dev_summary, environment)
    return hashlib.sha256("\n".join(inspect.getsource(f) for f in fns).encode()).hexdigest()


VALUE_CONSTANTS = ("VERSION", "EXEC_PREFIX", "SCHEMA", "RECORD_CODE_HASH", "ORIGINAL_DEVICE", "SEEDS", "DATASETS", "OBJECTIVES", "ADAPTERS",
                   "SUPPORTS", "READOUTS", "TIER", "TOL_GAIN", "TOL_RANK", "TOL_NONE", "EXTRA_FIELDS", "ORIGINAL_FIELDS")


def value_path_sha256():
    """note, addendum 2, C5: the evaluator functions of evaluator_sha256() (whose definition is kept, so that it stays comparable with
    the CPU outputs) plus torch_seed() (output_low_rank initialisation), execution_id() and the module constants of VALUE_CONSTANTS."""
    fns = (gain_with_risk, risk_capture, loader_scope, _f16, load_fau_ss_only, load_dtu_ss_only, load_cohort_ss_only, in_scope,
           resolve_base, evaluate_unit, reproduction_qc, _dev_summary, environment, torch_seed, execution_id)
    consts = json.dumps({k: globals()[k] for k in VALUE_CONSTANTS}, sort_keys=True, default=repr)
    return hashlib.sha256(("\n".join(inspect.getsource(f) for f in fns) + "\n" + consts).encode()).hexdigest()


def code_versions():
    out = {"aln34/dadapt_r.py": MODULE_SHA256, "evaluator_functions": EVALUATOR_SHA256, "value_path": VALUE_PATH_SHA256}
    for rel in FROZEN:
        out[rel] = sha256_file(os.path.join(REPO, rel))
    return out


# ================================================================================================ scope
def in_scope(r):
    """the 200 completed lag-local D_ADAPT units of the note: seeds 3401 / 3407 / 3413, FAU / DTU, NCE / CS_SINGLE, three adapters."""
    s = r["spec"]
    return (r["family_id"] == "D_ADAPT" and s.get("architecture") == "lag_local_tokens" and r["seed"] in SEEDS and r["dataset"] in DATASETS
            and s.get("objective") in OBJECTIVES and s.get("adapter") in ADAPTERS)


def all_rows():
    """plan rows followed by plan_ext rows (as auditory_alignment_v3.run.all_rows; the runner resolves panel bases through both)."""
    from auditory_alignment_v3 import run as R3
    return R3.all_rows()


def record_path(eid):
    return os.path.join(RECORDS, f"{eid}.json")


def load_record(eid):
    p = record_path(eid)
    return json.load(open(p)) if os.path.exists(p) else None


def out_path(out_dir, eid):
    return os.path.join(out_dir, f"{eid}.json")


def fail_path(out_dir, eid):
    return os.path.join(out_dir, f"{eid}.FAILED.json")


def load_output(out_dir, eid):
    p = out_path(out_dir, eid)
    return json.load(open(p)) if os.path.exists(p) else None


def scope_units(rows, load=load_record):
    """in-scope rows (plan order) with their record status."""
    return [(r, (load(r["experiment_id"]) or {}).get("status", "missing")) for r in rows if in_scope(r)]


# ================================================================================================ the R capture
def gain_with_risk(S_true, S_mm, own, tau):
    """run_adapt3._gain, the same four fields computed the same way, plus the true-pair logloss (R), the mismatched-EEG logloss,
    top5, MRR, K and tau of the same two _metrics calls."""
    from auditory_alignment import evaluate as ev1
    a, b = ev1._metrics(S_true, own, tau), ev1._metrics(S_mm, own, tau)
    out = {"gain_bits": b["logloss_bits"] - a["logloss_bits"], "rank_pct": a["rank_pct"], "top1": a["top1"], "n_query": int(len(own))}
    out.update({"logloss_bits": a["logloss_bits"], "mismatched_logloss_bits": b["logloss_bits"], "top5": a["top5"], "mrr": a["mrr"],
                "n_candidates": int(a["n_candidates"]), "tau": float(tau)})
    return out


@contextlib.contextmanager
def risk_capture():
    """replace run_adapt3._gain by gain_with_risk for the duration of the block (this process only); always restored."""
    from auditory_alignment_v3 import run_adapt3 as RA
    orig = RA._gain
    RA._gain = gain_with_risk
    try:
        yield
    finally:
        RA._gain = orig


@contextlib.contextmanager
def loader_scope(kind):
    """'original': auditory_alignment_v2.run.load_cohort unchanged; 'ss_only': load_cohort_ss_only for the block (CPU tests)."""
    if kind == "original":
        yield
        return
    if kind != "ss_only":
        raise ValueError(f"loader {kind}")
    from auditory_alignment_v2 import run as V2R
    orig = V2R.load_cohort
    V2R.load_cohort = load_cohort_ss_only
    try:
        yield
    finally:
        V2R.load_cohort = orig


# ================================================================================================ ss_only loaders (CPU engineering tests)
def _f16(x):
    """float32 -> float16 by torch (the conversion the batcher applies to the whole bank)."""
    import torch
    return torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).to(torch.float16).numpy()


def load_fau_ss_only(content_fold, stage_dir=None):
    """auditory_alignment.data.load_fau(content_fold, kinds=("ss", "cs")) restricted, after the per-participant standardisation over
    all trials, to the single-speaker trials. Lines marked R34 differ from the original; every other line is the original's."""
    import h5py
    from auditory_alignment import data as D
    stage_dir = D.STAGEB if stage_dir is None else stage_dir
    kinds = ("ss", "cs")  # R34: the trial set of load_cohort's call (standardisation set)
    fs, guard = 128, 314
    seg_len = int(D.SEG_S * fs); margin = int(D.MAX_WIN_S * fs) + 1 + D.AUDIO_FRAMES
    dev, panel = D.fau_panel()
    plist = [{"id": s, "group": "th", "fold": -1, "dev": True} for s in dev] + \
            [{"id": s, "group": g, "fold": f, "dev": False} for s, (g, f) in sorted(panel.items())]
    tf = h5py.File(os.path.join(D.FAU_KCS, f"fau_cf{content_fold}.h5"), "r")
    targets = ("Ac", "Lz", "Local")
    sbank = {t: D._Bank() for t in targets}
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
    eparts, n_e, segments = [], 0, []  # R34: float16 EEG bank of the single-speaker trials (replaces ebank)
    for pi, p in enumerate(plist):
        with h5py.File(os.path.join(stage_dir, p["group"], f"{p['id']}.h5"), "r") as f:
            ch = [str(c) for c in f.attrs["channels"]]
            assert len(ch) == 31 and "IO2" not in ch
            trials = [(str(f[t].attrs["stimulus"]), f[t]["eeg_1_20_ica"][()].astype(np.float64)) for t in sorted(f.keys())]
        trials = [(c, x) for c, x in trials if ("ss" in kinds and c[0] == "1") or ("cs" in kinds and c[0] == "2")]
        xs = D._stdz([x for _, x in trials], guard)
        for (code, _), x in zip(trials, xs):
            kind = "ss" if code[0] == "1" else "cs"
            if kind != "ss":
                continue  # R34: competing-speech trial: standardised with the others above, not kept
            roles = D.FAU_CF[content_fold][kind]
            role = next(r for r, parts in roles.items() if code[2] in parts)
            sa, na = stim_off(code, "attended")
            n = min(x.shape[1], na)  # R34: the original's min(x.shape[1], na, si[1] or na) with si = (None, None) for ss
            e0 = n_e; eparts.append(_f16(x)); n_e += x.shape[1]  # R34: e0 = ebank.add(x)
            for st in D._segments_of(guard, n - guard, seg_len, margin):
                segments.append({"p": pi, "e0": e0 + st, "s0": sa + st, "s0_ign": None,
                                 "role": role, "kind": kind, "uid": f"{code}@{st}", "hard_key": code[1], "part": code[2],
                                 "code": code})
        del trials, xs
    stim = {t: b.array() for t, b in sbank.items()}
    for s in segments:  # stimulus summary for hard candidates (Ac mean / SD over the segment)
        a = stim["Ac"][:, s["s0"]:s["s0"] + seg_len]
        s["feat"] = np.r_[a.mean(1), a.std(1)]
    eeg = np.concatenate(eparts, axis=1) if eparts else np.zeros((31, 0), np.float16)  # R34
    eparts.clear()
    return D.Cohort(fs, 31, plist, eeg, stim, segments, {"dataset": "fau", "content_fold": content_fold, "seg_len": seg_len})


def load_dtu_ss_only(content_fold):
    """auditory_alignment.data.load_dtu(content_fold, kinds=("ss", "cs")) restricted, after the per-participant standardisation over
    all trials, to the single-talker trials. Lines marked R34 differ from the original; every other line is the original's."""
    import h5py
    import pandas as pd
    from auditory_alignment import data as D
    kinds = ("ss", "cs")  # R34: the trial set of load_cohort's call (standardisation set)
    fs = 128; seg_len = int(D.SEG_S * fs); margin = int(D.MAX_WIN_S * fs) + 1 + D.AUDIO_FRAMES; start_guard = 64
    part = pd.read_csv(f"{D.PUB}/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv", sep="\t")
    hs = dict(zip(part.participant_id, part.hearing_status)); age = dict(zip(part.participant_id, part.age))
    subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(D.REPO, "private", "auditory_c3", "public", "dtu_v2", "*.json")))
    folds = D._folds({g: [s for s in subs if hs[s] == g] for g in ("nh", "hi")})
    plist = [{"id": s, "group": hs[s], "fold": folds[s], "dev": False, "age": float(age[s])} for s in subs]
    inv = json.load(open(f"{D.PUB}/derived/c3_features_v1/dtu/inventory.json"))
    sha = {(r["file"], r["trial"], r["kind"]): (r.get("sha"), r["offset_s"]) for r in inv}
    cg = json.load(open(os.path.join(D.DTU_KCS, "content_groups.json")))["content"]
    tf = h5py.File(os.path.join(D.DTU_KCS, f"dtu_cf{content_fold}.h5"), "r")
    targets = ("Ac", "Lz", "Local")
    sbank = {t: D._Bank() for t in targets}; soff = {}

    def stim_off(h, lead, n):
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
    eparts, n_e, segments = [], 0, []  # R34: float16 EEG bank of the single-talker trials (replaces ebank)
    for pi, p in enumerate(plist):
        with h5py.File(os.path.join(D.DTU_PRE, f"{p['id']}.h5"), "r") as f:
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
        xs = D._stdz([r[5] for r in rows], start_guard)
        for (k, two, th, mh, moff, _, mon), x in zip(rows, xs):
            if two:
                continue  # R34: two-talker trial: standardised with the others above, not kept
            n = x.shape[1]
            c = cg[th]
            role = "test" if c["half"] == content_fold else ("es" if c["early_stop"] else "fit")
            sa = stim_off(th, 0, n)
            a0 = start_guard  # R34: the original's 'start_guard if not two else ...'
            e0 = n_e; eparts.append(_f16(x)); n_e += n  # R34: e0 = ebank.add(x)
            for st in D._segments_of(a0, n, seg_len, margin):
                segments.append({"p": pi, "e0": e0 + st, "s0": sa + st, "s0_ign": None, "role": role,
                                 "kind": "ss", "uid": f"g{c['group']}@{st}", "hard_key": "dtu", "part": str(c["group"]),
                                 "code": th[:10]})
        del rows, xs
    stim = {t: b.array() for t, b in sbank.items()}
    for s in segments:
        a = stim["Ac"][:, s["s0"]:s["s0"] + seg_len]
        s["feat"] = np.r_[a.mean(1), a.std(1)]
    eeg = np.concatenate(eparts, axis=1) if eparts else np.zeros((64, 0), np.float16)  # R34
    eparts.clear()
    return D.Cohort(fs, 64, plist, eeg, stim, segments, {"dataset": "dtu", "content_fold": content_fold, "seg_len": seg_len})


def load_cohort_ss_only(row):
    """drop-in for auditory_alignment_v2.run.load_cohort (FAU / DTU) used by loader_scope('ss_only')."""
    ds, cf = row["dataset"], row["content_fold"]
    if ds == "fau":
        return load_fau_ss_only(cf)
    if ds == "dtu":
        return load_dtu_ss_only(cf)
    raise ValueError(ds)


# ================================================================================================ evaluation of one unit
def resolve_base(row, rows, rec):
    """the base exactly as run_adapt3.run resolves it, and its agreement with the record's dependency."""
    from auditory_alignment_v3 import run_complement as RC
    probe = dict(row); probe["spec"] = {**row["spec"], "local_architecture": "lag_local_tokens", "window": "full"}
    br = RC.base_ready(probe, rows, core.OUT)
    if br is None:
        raise RuntimeError("same-fold local base not complete or checkpoint missing")
    b_row, b_path, b_ck = br
    dep = rec.get("dependency") or {}
    info = {"experiment_id": b_row["experiment_id"], "checkpoint": os.path.relpath(b_ck, REPO), "checkpoint_realpath": os.path.realpath(b_ck),
            "checkpoint_sha256": sha256_file(b_ck), "record": os.path.relpath(b_path, REPO), "record_sha256": sha256_file(b_path),
            "record_dependency": dep}
    info["matches_record"] = dep.get("base_same_fold") == b_row["experiment_id"] and dep.get("base_checkpoint") == info["checkpoint"]
    return b_row, b_path, b_ck, info


def environment(dev):
    import torch
    cuda = dev.type == "cuda"
    e = {"torch": torch.__version__, "numpy": np.__version__, "python": sys.version.split()[0], "host": socket.gethostname(), "device": str(dev),
         "device_name": torch.cuda.get_device_name(dev) if cuda else "cpu", "cuda": torch.version.cuda,
         "cudnn": torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None,
         "cudnn_allow_tf32": bool(torch.backends.cudnn.allow_tf32), "matmul_allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
         "float32_matmul_precision": torch.get_float32_matmul_precision(), "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
         "cudnn_deterministic": bool(torch.backends.cudnn.deterministic), "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
         "torch_threads": torch.get_num_threads(),
         "env": {k: os.environ.get(k) for k in ("PYTHONHASHSEED", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "CUDA_VISIBLE_DEVICES",
                                                 "SLURM_JOB_ID", "SLURM_ARRAY_JOB_ID", "SLURM_ARRAY_TASK_ID", "SLURM_RESTART_COUNT")}}
    e["torch_defaults_as_original"] = (e["cudnn_allow_tf32"] and not e["matmul_allow_tf32"] and e["float32_matmul_precision"] == "highest"
                                       and not e["cudnn_benchmark"] and not e["cudnn_deterministic"] and not e["deterministic_algorithms"])
    e["same_device_type_as_records"] = e["device_name"] == ORIGINAL_DEVICE
    return e


def _dev_summary(x):
    x = np.asarray(x, float)
    if not len(x):
        return {"n": 0}
    a = np.abs(x)
    return {"n": int(len(x)), "max_abs": float(a.max()), "mean_abs": float(a.mean()), "median_abs": float(np.median(a)), "mean_signed": float(x.mean()),
            "n_positive": int((x > 0).sum()), "n_negative": int((x < 0).sum())}


def reproduction_qc(rec, new_eval, adapter, base_ok=True, code_ok=True):
    """the note's reproduction QC: structural checks (every tier, exact), numeric agreement (tier exact), deviations reported."""
    tier = TIER[adapter]
    R, N = rec["eval"]["per_participant"], new_eval["per_participant"]
    problems, cells = [], []
    if set(R) != set(N):
        problems.append(f"participants differ: record-only {sorted(set(R) - set(N))[:5]}, refit-only {sorted(set(N) - set(R))[:5]}")
    for pid in sorted(set(R) & set(N)):
        r, n = R[pid], N[pid]
        for k in ("group", "n_segments"):
            if r.get(k) != n.get(k):
                problems.append(f"{pid}: {k} {r.get(k)} != {n.get(k)}")
        for sf in SUPPORTS:
            key = f"support_{sf}"
            if (key in r) != (key in n):
                problems.append(f"{pid}: {key} present in only one"); continue
            if key not in r:
                continue
            if r[key].get("n_support") != n[key].get("n_support"):
                problems.append(f"{pid}/{sf}: n_support {r[key].get('n_support')} != {n[key].get('n_support')}")
            for rd in READOUTS:
                a, b = r[key][rd], n[key][rd]
                if a.get("n_query") != b.get("n_query"):
                    problems.append(f"{pid}/{sf}/{rd}: n_query {a.get('n_query')} != {b.get('n_query')}")
                dt = float(b["top1"]) - float(a["top1"])
                cells.append({"participant": pid, "support": sf, "readout": rd, "d_gain_bits": float(b["gain_bits"]) - float(a["gain_bits"]),
                              "d_rank_pct": float(b["rank_pct"]) - float(a["rank_pct"]), "d_top1": dt, "top1_query_flips": int(round(abs(dt) * int(a["n_query"])))})
    none_ok = None
    if adapter == "none":
        none_ok = True
        for pid, n in N.items():
            if "support_0.1" not in n or "support_0.3" not in n:
                continue
            for rd in READOUTS:
                for fld in ORIGINAL_FIELDS + EXTRA_FIELDS:
                    x, y = n["support_0.1"][rd].get(fld), n["support_0.3"][rd].get(fld)
                    if x is None or y is None or abs(float(x) - float(y)) > TOL_NONE:
                        none_ok = False
        if not none_ok:
            problems.append("adapter none: refit values differ between support fractions")
    rs, ns = rec["eval"].get("steps") or {}, new_eval.get("steps") or {}
    rsc, nsc = {str(k): v for k, v in (rs.get("scores") or {}).items()}, {str(k): v for k, v in (ns.get("scores") or {}).items()}
    common = [k for k in rsc if k in nsc and rsc[k] is not None and nsc[k] is not None]
    steps = {"recorded": rs.get("chosen"), "refit": ns.get("chosen"), "equal": rs.get("chosen") == ns.get("chosen"),
             "scores_max_abs_diff": max((abs(float(nsc[k]) - float(rsc[k])) for k in common), default=0.0), "score_keys_equal": set(rsc) == set(nsc)}
    if not base_ok:
        problems.append("base differs from the record's dependency")
    if not code_ok:
        problems.append("code hash differs from the record's")
    dev = {f"{m}|{rd}": _dev_summary([c[f"d_{m}"] for c in cells if c["readout"] == rd]) for m in ("gain_bits", "rank_pct", "top1") for rd in READOUTS}
    flips = {rd: int(sum(c["top1_query_flips"] for c in cells if c["readout"] == rd)) for rd in READOUTS}
    structural = not problems
    max_g = max((abs(c["d_gain_bits"]) for c in cells), default=0.0)
    max_r = max((abs(c["d_rank_pct"]) for c in cells), default=0.0)
    numeric = steps["equal"] and max_g <= TOL_GAIN and max_r <= TOL_RANK
    passed = structural and (numeric if tier == "exact" else True)
    return {"tier": tier, "pass": bool(passed), "structural_pass": bool(structural), "numeric_pass": bool(numeric), "problems": problems[:50],
            "n_problems": len(problems), "steps": steps, "max_abs_d_gain_bits": float(max_g), "max_abs_d_rank_pct": float(max_r),
            "deviation": dev, "top1_query_flips": flips, "none_identical_across_support": none_ok, "cells": cells,
            "tolerance": {"gain_bits": TOL_GAIN, "rank_pct": TOL_RANK, "none_across_support": TOL_NONE},
            "rule": "exact: structural and steps equal and max|d gain_bits| <= tol and max|d rank_pct| <= tol; seeded_refit: structural only"}


def evaluate_unit(eid, device="cuda", out_dir=UNITS_DIR, loader="original", rows=None):
    """re-fit one unit with the imported runner and write <out_dir>/<eid>.json; returns the path."""
    import torch
    from auditory_alignment_v3 import run_adapt3 as RA
    t0 = time.time(); started = _utc()
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("PYTHONHASHSEED=0 is required: the NCE support rows key stimuli by hash(uid), and the pool ran with PYTHONHASHSEED=0")
    rows = all_rows() if rows is None else rows
    byid = {r["experiment_id"]: r for r in rows}
    if eid not in byid:
        raise KeyError(f"{eid}: not a plan or plan_ext row")
    row = byid[eid]
    if not in_scope(row):
        raise ValueError(f"{eid}: not in the R34_DADAPT_R scope")
    rec = load_record(eid)
    if rec is None or rec.get("status") != "complete":
        raise RuntimeError(f"{eid}: source record missing or not complete")
    b_row, b_path, b_ck, base = resolve_base(row, rows, rec)
    code_now = core.code_hash(row["family_id"])
    base_unit = json.load(open(b_path)); base["base_code_hash"] = base_unit.get("code_hash")
    seed_t = torch_seed(eid)
    dev = torch.device(device)
    if dev.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
    torch.manual_seed(seed_t)  # declared per-unit seed (note); nothing between here and bundle draws from torch's generators
    with risk_capture(), loader_scope(loader):
        ev = RA.bundle(row, base_unit, b_ck, dev)
    seconds = round(time.time() - t0, 1)
    adapter = row["spec"]["adapter"]
    qc = reproduction_qc(rec, ev, adapter, base["matches_record"], code_now == rec.get("code_hash"))
    s = row["spec"]
    out = {"schema": SCHEMA, "execution_version": VERSION, "execution_id": execution_id(eid), "source_experiment_id": eid, "status": "complete",
           "family_id": row["family_id"], "dataset": row["dataset"], "seed": row["seed"], "subject_fold": row["subject_fold"],
           "content_fold": row["content_fold"], "objective": s["objective"], "adapter": adapter, "tier": TIER[adapter], "loader": loader,
           "torch_manual_seed": seed_t,
           "source_record": {"path": os.path.relpath(record_path(eid), REPO), "sha256": sha256_file(record_path(eid)), "code_hash": rec.get("code_hash"),
                             "device": rec.get("device"), "total_seconds": rec.get("total_seconds"), "steps": (rec.get("eval") or {}).get("steps")},
           "code_hash_now": code_now, "code_hash_equal": code_now == rec.get("code_hash"), "base": base, "code": code_versions(),
           "environment": environment(dev), "eval": ev, "qc": qc,
           "runtime": {"started_utc": started, "finished_utc": _utc(), "seconds": seconds,
                       "gpu_peak_allocated_mb": round(torch.cuda.max_memory_allocated() / 2 ** 20) if dev.type == "cuda" else None,
                       "max_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)},
           "note": {"path": os.path.relpath(NOTE, REPO), "sha256": sha256_file(NOTE) if os.path.exists(NOTE) else None}}
    return write_json(out_path(out_dir, eid), out)


# ================================================================================================ claims and worker loop
def owner(tag):
    """claim owner: SLURM_JOB_ID (unique per array element) and, in an array, also <SLURM_ARRAY_JOB_ID>_<SLURM_ARRAY_TASK_ID> (the
    form squeue -o %i prints for array elements; note, addendum 2, C2)."""
    job = os.environ.get("SLURM_JOB_ID") or f"local-{socket.gethostname()}-{os.getpid()}"
    o = {"job": job, "worker": str(tag), "host": socket.gethostname(), "pid": os.getpid(), "utc": _utc()}
    aj, at = os.environ.get("SLURM_ARRAY_JOB_ID"), os.environ.get("SLURM_ARRAY_TASK_ID")
    if aj and at:
        o["array_task"] = f"{aj}_{at}"
    return o


def live_jobs():
    """this user's running Slurm jobs in both id forms - %A (job id, unique for each array element) and %i (<base>_<index> for array
    elements) - or None when squeue fails or lists nothing (then no foreign claim is released). Note, addendum 2, C2."""
    try:
        p = subprocess.run(["squeue", "-u", os.environ.get("USER", ""), "-h", "-t", "RUNNING,CONFIGURING,COMPLETING", "-o", "%A %i"],
                           capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    ids = set(p.stdout.split())
    return ids if p.returncode == 0 and ids else None


def claim_live(own, live):
    """the claim's Slurm job is running, in either id form."""
    return live is not None and (str(own.get("job")) in live or (own.get("array_task") is not None and str(own["array_task"]) in live))


def is_own(own, me):
    """the claim was made by this very worker process (job, worker tag, host and pid)."""
    return own is not None and all(str(own.get(k)) == str(me.get(k)) for k in ("job", "worker", "host", "pid"))


def _pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def sweep_claims(claims_dir, me, live):
    """release: own claims (same job and worker tag: a requeued job restarts its loop), claims of jobs no longer running (in neither
    squeue id form), claims of dead local processes on this host, owner-less claims older than 10 min; never another worker's claim
    younger than 2 min."""
    released = []
    if not os.path.isdir(claims_dir):
        return released
    for d in sorted(os.listdir(claims_dir)):
        p = os.path.join(claims_dir, d)
        if not d.endswith(".claim") or not os.path.isdir(p):
            continue
        try:
            own = json.load(open(os.path.join(p, "owner.json")))
        except (OSError, ValueError):
            own = None
        age_min = (time.time() - os.path.getmtime(p)) / 60
        job = (own or {}).get("job")
        if own is not None and job == me["job"] and own.get("worker") == me["worker"]:
            drop = True
        elif own is None:
            drop = age_min > 10
        elif age_min < 2:
            drop = False
        elif str(job).startswith("local-"):
            drop = own.get("host") == socket.gethostname() and not _pid_alive(own.get("pid"))
        else:
            drop = live is not None and not claim_live(own, live)
        if drop:
            shutil.rmtree(p, ignore_errors=True); released.append(d[:-len(".claim")])
    return released


def try_claim(claims_dir, eid, me):
    guard(claims_dir)
    os.makedirs(claims_dir, mode=0o700, exist_ok=True)
    p = os.path.join(claims_dir, f"{eid}.claim")
    try:
        os.mkdir(p, 0o700)  # atomic: exactly one worker succeeds
    except FileExistsError:
        return False
    write_json(os.path.join(p, "owner.json"), me)
    return True


def release_claim(claims_dir, eid, me):
    """remove the claim only when its owner record is `me`; never another worker's claim (note, addendum 2, C2)."""
    p = os.path.join(claims_dir, f"{eid}.claim")
    try:
        own = json.load(open(os.path.join(p, "owner.json")))
    except (OSError, ValueError):
        return False
    if not is_own(own, me):
        print(f"claim {eid} is held by {own.get('job')}/{own.get('worker')} (pid {own.get('pid')}), not by this worker: left in place", flush=True)
        return False
    shutil.rmtree(p, ignore_errors=True)
    return True


def failed_tries(out_dir, eid):
    p = fail_path(out_dir, eid)
    if not os.path.exists(p):
        return 0
    try:
        return int(json.load(open(p)).get("tries", 1))
    except (OSError, ValueError):
        return 1


def record_failure(out_dir, eid, error, tb, tries, me):
    write_json(fail_path(out_dir, eid), {"eid": eid, "execution_version": VERSION, "error": error, "traceback": tb[-4000:], "tries": tries,
                                         "owner": me, "utc": _utc(), "module_sha256": MODULE_SHA256})


def parse_shard(s):
    if not s:
        return None
    k, n = (int(x) for x in s.split("/"))
    if not 0 <= k < n:
        raise ValueError(f"shard {s}: need 0 <= K < N")
    return k, n


def read_units_file(path):
    return [l.split()[0] for l in open(path) if l.strip() and not l.lstrip().startswith("#")]


def unit_order(eids, shard, steal=True):
    """own shard (i mod N == K) first, then, with steal, the rest of the list in file order (claims prevent duplicates)."""
    mine = [e for i, e in enumerate(eids) if shard is None or i % shard[1] == shard[0]]
    if not steal:
        return mine
    seen = set(mine)
    return mine + [e for e in eids if e not in seen]


def run_child(eid, device, out_dir, loader, threads=None):
    """one unit in a fresh interpreter (fresh generator / CUDA / allocator state, as the pool ran units); log appended to LOGS/<eid>.log."""
    os.makedirs(LOGS, mode=0o700, exist_ok=True)
    logp = os.path.join(LOGS, f"{eid}.log")
    cmd = [sys.executable, "-B", "-m", "auditory_alignment_v3.aln34.dadapt_r", "--unit", eid, "--claimed", "--device", device, "--out", out_dir, "--loader", loader]
    if threads:
        cmd += ["--threads", str(threads)]
    env = {**os.environ, "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1",
           "PYTHONPATH": REPO + (os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")}
    fd = os.open(logp, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a") as fh:
        fh.write(f"=== {_utc()} host={socket.gethostname()} job={os.environ.get('SLURM_JOB_ID', 'local')} {' '.join(cmd)}\n"); fh.flush()
        p = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=REPO, env=env)
    return p.returncode, logp


def run_units_file(path, device, out_dir=UNITS_DIR, shard=None, tag="w0", loader="original", max_tries=MAX_TRIES, steal=True, threads=None,
                   child=run_child, live=None):
    """worker loop; each unit in a fresh subprocess. A unit is skipped when its output exists, when it failed max_tries times, or
    when another worker holds its claim. Failures are recorded (<eid>.FAILED.json with the try count), never hidden."""
    check_out_dir(out_dir)
    eids = unit_order(read_units_file(path), shard, steal)
    claims = os.path.join(out_dir, "claims"); me = owner(tag)
    released = sweep_claims(claims, me, live_jobs() if live is None else live)
    tally = Counter({"released_stale_claims": len(released)})
    for eid in eids:
        if os.path.exists(out_path(out_dir, eid)):
            tally["skip_done"] += 1; continue
        tries = failed_tries(out_dir, eid)
        if tries >= max_tries:
            tally["skip_failed"] += 1; continue
        if not try_claim(claims, eid, me):
            tally["skip_claimed"] += 1; continue
        try:
            if os.path.exists(out_path(out_dir, eid)):
                tally["skip_done"] += 1; continue
            t = time.time()
            rc, logp = child(eid, device, out_dir, loader, threads)
            if rc == 0 and os.path.exists(out_path(out_dir, eid)):
                tally["done"] += 1
                print(f"{time.strftime('%H:%M:%S')} done {eid} {round(time.time() - t)}s", flush=True)
            else:
                if failed_tries(out_dir, eid) == tries:  # the child died before recording its failure
                    tail = ""
                    if logp and os.path.exists(logp):
                        with open(logp, errors="replace") as fh:
                            tail = "".join(fh.readlines()[-40:])
                    record_failure(out_dir, eid, f"child exit code {rc}", tail, tries + 1, me)
                tally["failed"] += 1
                print(f"{time.strftime('%H:%M:%S')} FAILED {eid} rc={rc}", flush=True)
        finally:
            release_claim(claims, eid, me)
    print("worker", dict(tally), flush=True)
    return dict(tally)


def unit_main(eid, device, out_dir, loader, claimed=False, force=False):
    """--unit: idempotent; claims the unit itself unless the parent worker holds the claim (--claimed)."""
    check_out_dir(out_dir)
    if os.path.exists(out_path(out_dir, eid)) and not force:
        print("skip (output exists)", eid, flush=True)
        return 0
    claims = os.path.join(out_dir, "claims"); me = owner("unit")
    if not claimed and not try_claim(claims, eid, me):
        print("skip (claimed by another worker)", eid, flush=True)
        return 0
    tries = failed_tries(out_dir, eid)
    try:
        p = evaluate_unit(eid, device, out_dir, loader)
        q = json.load(open(p))["qc"]
        print("done", eid, p, "| tier", q["tier"], "| qc pass", q["pass"], "| steps", q["steps"]["recorded"], "->", q["steps"]["refit"],
              "| max|d gain|", f"{q['max_abs_d_gain_bits']:.2e}", "| max|d rank|", f"{q['max_abs_d_rank_pct']:.2e}", "| problems", q["n_problems"], flush=True)
        return 0
    except Exception as ex:  # noqa: BLE001 - recorded, never hidden
        record_failure(out_dir, eid, f"{type(ex).__name__}: {ex}", traceback.format_exc(), tries + 1, me)
        print("FAILED", eid, f"{type(ex).__name__}: {ex}", flush=True)
        traceback.print_exc()
        return 1
    finally:
        if not claimed:
            release_claim(claims, eid, me)


def start_rss_watchdog(limit_mib, period=0.5):
    """CPU tests: end the process (exit 3) as soon as its resident memory exceeds limit_mib."""
    page = os.sysconf("SC_PAGE_SIZE")

    def watch():
        while True:
            try:
                with open("/proc/self/statm") as f:
                    rss = int(f.read().split()[1]) * page / 2 ** 20
            except OSError:
                return
            if rss > limit_mib:
                sys.stderr.write(f"RSS watchdog: {rss:.0f} MiB > {limit_mib} MiB, exiting\n"); sys.stderr.flush()
                os._exit(3)
            time.sleep(period)
    threading.Thread(target=watch, daemon=True).start()


# ================================================================================================ unit list and Slurm template
def unit_table(rows, load=load_record, out_dir=UNITS_DIR):
    out = []
    for r, st in scope_units(rows, load):
        if st != "complete":
            continue
        rec = load(r["experiment_id"])
        s = r["spec"]
        out.append({"eid": r["experiment_id"], "dataset": r["dataset"], "seed": r["seed"], "objective": s["objective"], "adapter": s["adapter"],
                    "subject_fold": r["subject_fold"], "content_fold": r["content_fold"], "tier": TIER[s["adapter"]],
                    "record_seconds": float(rec.get("total_seconds") or 0.0), "done": os.path.exists(out_path(out_dir, r["experiment_id"]))})
    key = lambda u: (SEEDS.index(u["seed"]), DATASETS.index(u["dataset"]), OBJECTIVES.index(u["objective"]), ADAPTERS.index(u["adapter"]),
                     u["subject_fold"], u["content_fold"])
    return sorted(out, key=key)


def estimate(units, overhead=(10.0, 15.0, 30.0), factor=(0.8, 1.0, 1.5)):
    """assumption-based GPU estimate: per unit factor x the record's wall time (shared A40, up to 8 units per card) + process/CUDA start."""
    pend = [u for u in units if not u["done"]]
    secs = [sum(f * u["record_seconds"] + o for u in pend) for f, o in zip(factor, overhead)]
    return {"pending": len(pend), "listed": len(units), "unit_minutes": [round(x / 60, 1) for x in secs],
            "record_seconds_sum_pending": round(sum(u["record_seconds"] for u in pend), 1),
            "assumption": "per unit (0.8 / 1.0 / 1.5) x the record's total_seconds + (10 / 15 / 30) s; GPU-minutes = unit-minutes / PAR when PAR units share a card"}


def write_units(rows=None, load=load_record):
    rows = all_rows() if rows is None else rows
    units = unit_table(rows, load)
    est = estimate(units)
    tiers = Counter(u["tier"] for u in units)
    by = Counter((u["seed"], u["dataset"], u["objective"], u["adapter"]) for u in units)
    lo, mid, hi = est["unit_minutes"]
    head = [f"# R34_DADAPT_R unit list, execution {VERSION}; written {time.strftime('%Y-%m-%d %H:%M %Z')} by auditory_alignment_v3.aln34.dadapt_r --write-units.",
            "# Scope: every completed lag-local D_ADAPT unit (run_adapt3, code hash f029aabd1ea656c1): seed 3401 FAU/DTU x NCE/CS_SINGLE x",
            "# none/input_spatial/output_low_rank x 10 fold cells (120) and the 3407/3413 panel FAU/DTU x NCE x none/input_spatial x 10 (80).",
            "# Not listed: the D_ADAPT policy arms (dense_fm_policy / complement_policy; other runner, held old-policy executions).",
            f"# Units: {len(units)} (tier exact {tiers.get('exact', 0)}, seeded_refit {tiers.get('seeded_refit', 0)}); pending (no output in "
            f"{os.path.relpath(UNITS_DIR, REPO)}): {est['pending']}.",
            f"# Records' own wall times (total_seconds, shared A40s, up to 8 units per card): {sum(u['record_seconds'] for u in units):,.1f} s summed over "
            f"the {len(units)} listed units, {est['record_seconds_sum_pending']:,.1f} s over the pending ones.",
            f"# Estimate for the pending units: {mid} unit-minutes (range {lo}-{hi}). GPU-minutes: about {round(mid / 2)} with PAR = 2 units per card "
            f"(range {round(lo / 2)}-{round(hi / 2)}), {round(mid)} with PAR = 1 (range {round(lo)}-{round(hi)}). Assumption, not measured: {est['assumption']}.",
            "# Columns: experiment_id dataset seed objective adapter subject_fold content_fold tier record_seconds (the worker reads the first column)."]
    for k, v in sorted(by.items(), key=lambda kv: (SEEDS.index(kv[0][0]), kv[0][1:])):
        head.append(f"#   {k[0]} {k[1]} {k[2]} {k[3]}: {v}")
    lines = [f"{u['eid']} {u['dataset']} {u['seed']} {u['objective']} {u['adapter']} {u['subject_fold']} {u['content_fold']} {u['tier']} {u['record_seconds']:.1f}"
             for u in units]
    write_text(UNITS_FILE, "\n".join(head + lines) + "\n")
    rel = os.path.relpath(UNITS_FILE, REPO)
    sb = [
        "#!/bin/bash",
        f"# TEMPLATE written by auditory_alignment_v3.aln34.dadapt_r --write-units ({time.strftime('%Y-%m-%d %H:%M %Z')}); execution {VERSION}.",
        "# NOT submitted by this lane. Submitting it is an operational step inside the project's 10-GPU cap (shared with the c3_aln3fm pool",
        "# and the other lanes). Each array task is one GPU running PAR concurrent worker loops (default 2) over the unit list: own shard first,",
        "# then the rest; every unit runs in a fresh subprocess; atomic claims (<out>/claims/<eid>.claim) prevent duplicate work; finished units",
        "# (<out>/<eid>.json) are skipped; a unit is tried at most 3 times; a requeued task releases its own claims and redoes its unfinished",
        "# units from scratch (a unit takes about 0.5-8 min). Claims record SLURM_JOB_ID and <array job>_<task>; the sweep checks both squeue",
        "# id forms (%A and %i), and a worker removes only its own claims (note, addendum 2, C2). Per-unit outputs (per-participant values)",
        f"# go to {os.path.relpath(UNITS_DIR, REPO)}/ (note, addendum 2, C3).",
        "# Partition A40: the device of all 200 source records (TF32 cuDNN convolutions by default), so the numerics stay closest to the records.",
        "# Other cards should also pass the QC tolerance (the CPU FP32 checks matched the A40 records within 2e-4 bits): A30 / L40S / V100 can be",
        "# added if A40 is congested; A100 / H100 would need --time under the slot policy.",
        f"# Estimate (assumption-based, from the records' wall times): {mid} unit-minutes for {est['pending']} pending units (range {lo}-{hi}); about",
        f"# {round(mid / 2)} GPU-minutes at PAR 2, i.e. ~{round(mid / 2 / 4)} min wall with the 4 array tasks below once they all run.",
        "# Submit from the repo root: sbatch private/auditory_alignment_v3/aln34/dadapt_r_gpu.sbatch [PAR]",
        "#SBATCH --job-name=c3_aln34dr",
        "#SBATCH --nice=50",
        "#SBATCH --qos=runfill",
        "#SBATCH --partition=A40",
        "#SBATCH --gres=gpu:1",
        "#SBATCH --exclude=node52",
        "#SBATCH --cpus-per-task=4",
        "#SBATCH --mem=32G",
        "#SBATCH --array=0-3",
        "#SBATCH --requeue",
        "#SBATCH --open-mode=append",
        "#SBATCH --output=private/auditory_alignment_v3/logs/%x-%A_%a.log",
        "set -uo pipefail",
        "umask 077",
        'cd "$SLURM_SUBMIT_DIR"',
        "export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false",
        "export _MNE_FAKE_HOME_DIR=$(mktemp -d)",
        f"PY={PY}",
        f"UNITS={rel}",
        "K=${SLURM_ARRAY_TASK_ID:-0}; N=${SLURM_ARRAY_TASK_COUNT:-1}; PAR=${1:-2}",
        'echo "start $(date -Is) node=${SLURMD_NODENAME:-?} gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1) restart=${SLURM_RESTART_COUNT:-0} job=${SLURM_JOB_ID:-?} task=$K/$N par=$PAR"',
        "if ! $PY -c \"import torch; torch.zeros(1).cuda(); torch.cuda.synchronize()\" >/dev/null 2>&1; then",
        '  echo "GPU unusable on ${SLURMD_NODENAME:-?}; exiting without claiming"; exit 0',
        "fi",
        "for j in $(seq 0 $((PAR-1))); do",
        "  $PY -B -m auditory_alignment_v3.aln34.dadapt_r --units-file $UNITS --shard $((K*PAR+j))/$((N*PAR)) --worker-tag w$j --device cuda &",
        "  sleep 30  # stagger the cohort loads (host memory)",
        "done",
        "wait",
        'echo "end $(date -Is)"',
    ]
    write_text(SBATCH, "\n".join(sb) + "\n")
    print("unit list:", rel, "| units", len(units), "| pending", est["pending"], "| tiers", dict(tiers))
    print("estimate:", est)
    print("sbatch template (not submitted):", os.path.relpath(SBATCH, REPO))
    return units, est


# ================================================================================================ aggregation
def setup():
    """directions of the new endpoints (positive = candidate better for lower / higher), this process only."""
    BI.PDIR.update({k: d for k, _, _, d in METRICS})


def direction(metric):
    return BI.DIRECTION.get(metric) or BI.PDIR[metric]


def problem_kind(p):
    """a QC problem string of reproduction_qc without its participant id (public outputs; note, addendum 2, C3)."""
    if p.startswith("participants differ"):
        return "participants differ"
    if ": " not in p or p.startswith(("adapter none", "base differs", "code hash differs")):
        return p
    rest = p.split(": ", 1)[1]
    field = rest.split()[0] if rest.split() else "?"
    return f"{field} present in only one" if "present in only one" in rest else f"{field} differs"


def _unit_mean(per_cf):
    """identity mean over its admitted units (content folds), metric by metric (levels and the per-identity file; descriptive)."""
    acc = defaultdict(list)
    for d in per_cf.values():
        for m, x in d.items():
            acc[m].append(x)
    return {m: float(np.mean(x)) for m, x in acc.items()}


def collect(rows, out_load, rec_load=load_record):
    """per seed s and configuration c = ('AD', ds, objective, adapter, support):
      cells[s][c][identity][content_fold] = {metric: value} of the one admitted unit (the input of the content-fold-matched pairs);
      vals[s][c][identity] = {metric: mean over the identity's admitted units} (levels and the per-identity file; descriptive);
      expected[s][c][identity] = content folds in which the complete source record holds the identity.
    Also groups, the per-unit table (public: QC problem kinds only), the full QC problem strings (private), K per (dataset, seed),
    units per identity and every participant id seen (for the identity scan). A unit is admitted when its output is complete, of
    this execution version and its QC passes (exact: structural + numeric; seeded_refit: structural); other units are listed,
    never filled."""
    cells = {s: defaultdict(lambda: defaultdict(dict)) for s in SEEDS}
    expected = {s: defaultdict(lambda: defaultdict(set)) for s in SEEDS}
    grp, units, K, problems, ids = {}, [], defaultdict(set), {}, set()
    for r in rows:
        if not in_scope(r):
            continue
        eid, s, seed, ds, cf = r["experiment_id"], r["spec"], r["seed"], r["dataset"], r["content_fold"]
        rec = rec_load(eid)
        rp = ((rec.get("eval") or {}).get("per_participant") or {}) if (rec or {}).get("status") == "complete" else {}
        for pid, v in rp.items():
            ids.add(str(pid))
            for sf in SUPPORTS:
                if v.get(f"support_{sf}"):
                    expected[seed][("AD", ds, s["objective"], s["adapter"], sf)][pid].add(cf)
        out = out_load(eid)
        u = {"eid": eid, "execution_id": execution_id(eid), "seed": seed, "dataset": ds, "objective": s["objective"], "adapter": s["adapter"],
             "subject_fold": r["subject_fold"], "content_fold": cf, "tier": TIER[s["adapter"]], "record_status": (rec or {}).get("status", "missing"),
             "output": "missing" if out is None else out.get("status"), "admitted": False}
        if out is not None:
            q = out["qc"]
            u.update({"qc_pass": q["pass"], "structural_pass": q["structural_pass"], "numeric_pass": q["numeric_pass"], "steps_recorded": q["steps"]["recorded"],
                      "steps_refit": q["steps"]["refit"], "steps_equal": q["steps"]["equal"], "max_abs_d_gain_bits": q["max_abs_d_gain_bits"],
                      "max_abs_d_rank_pct": q["max_abs_d_rank_pct"], "n_problems": q["n_problems"],
                      "problem_kinds": dict(Counter(problem_kind(p) for p in q["problems"])),
                      "device_name": out["environment"]["device_name"], "loader": out.get("loader"), "seconds": out["runtime"]["seconds"],
                      "module_sha256": out["code"]["aln34/dadapt_r.py"], "evaluator_sha256": out["code"]["evaluator_functions"],
                      "value_path_sha256": out["code"].get("value_path")})
            if q["problems"]:
                problems[eid] = list(q["problems"])
            ids.update(str(p) for p in (out.get("eval") or {}).get("per_participant", {}))
            if out.get("status") == "complete" and q["pass"] and out.get("execution_version") == VERSION:
                u["admitted"] = True
                for pid, v in out["eval"]["per_participant"].items():
                    grp[(ds, pid)] = v.get("group")
                    for sf in SUPPORTS:
                        x, xr = v.get(f"support_{sf}"), (rp.get(pid) or {}).get(f"support_{sf}")
                        if not x:
                            continue
                        c = ("AD", ds, s["objective"], s["adapter"], sf)
                        if cf in cells[seed][c][pid]:
                            raise ValueError(f"{eid}: a second admitted unit for one identity and content fold of {BI.ckey(c)}")
                        d = {}
                        for key, rd, fld, _ in METRICS:
                            val = (xr or {}).get(rd, {}).get("gain_bits") if fld is None else x[rd].get(fld)
                            if val is not None:
                                d[key] = float(val)
                        cells[seed][c][pid][cf] = d
                        K[(ds, seed)].add(int(x["unified"]["n_candidates"]))
        units.append(u)
    vals = {s: {c: {i: _unit_mean(per_cf) for i, per_cf in per.items()} for c, per in cells[s].items()} for s in SEEDS}
    per_identity_units = {f"{s}|{BI.ckey(c)}": {str(k): v for k, v in sorted(Counter(len(per_cf) for per_cf in per.values()).items())}
                          for s in SEEDS for c, per in cells[s].items()}
    return {"cells": cells, "vals": vals, "expected": expected, "groups": grp, "units": units, "K": {f"{k[0]}|{k[1]}": sorted(v) for k, v in K.items()},
            "units_per_identity": per_identity_units, "problems": problems, "ids": ids}


# ------------------------------------------------------------------------------------------------ content-fold-matched pairs (C1)
def pair_keys(label, name):
    return ("PAIR_REF", label, name), ("PAIR_CAND", label, name)


def pair_fams(fams):
    """the families with each member's reference / candidate replaced by its content-fold-matched pair keys."""
    return [(fam, sc, label, [(name, *pair_keys(label, name), tag) for name, ref, cand, tag in members]) for fam, sc, label, members in fams]


def restricted_mean(per_cf, kept):
    """mean over the kept content folds; a metric enters only when every kept content fold has it (one query set per pair)."""
    out = {}
    for m in METRIC_KEYS:
        xs = [per_cf[cf].get(m) for cf in sorted(kept)]
        if all(x is not None for x in xs):
            out[m] = float(np.mean(xs))
    return out


def pair_inputs(fams, cells, expected):
    """note, addendum 2, C1: per seed, family member (reference, candidate) and identity, both sides averaged over the same content
    folds - those admitted on both sides. Returns {seed: {pair key: {identity: {metric: value}}}} (pseudo-configurations, so that
    d_lag_interim.run_fams / bc_interim.run_family apply unchanged) and one coverage row per seed x member x identity
    (kind complete / partial / missing; identity-level, private)."""
    pv = {s: {} for s in cells}
    cov = []
    for fam, sc, label, members in fams:
        for name, ref, cand, tag in members:
            Rk, Ck = pair_keys(label, name)
            for s in cells:
                a, b = cells[s].get(ref, {}), cells[s].get(cand, {})
                ea, eb = expected[s].get(ref, {}), expected[s].get(cand, {})
                pr, pc = {}, {}
                for i in sorted(set(a) | set(b) | set(ea) | set(eb), key=str):
                    exp = set(ea.get(i, ())) & set(eb.get(i, ()))
                    ka, kb = set(a.get(i, {})), set(b.get(i, {}))
                    kept = ka & kb
                    if not exp and not kept:
                        continue  # the identity is not in both records of this pair
                    if kept:
                        pr[i], pc[i] = restricted_mean(a[i], kept), restricted_mean(b[i], kept)
                    kind = "missing" if not kept else ("complete" if exp <= kept else "partial")
                    cov.append({"seed": s, "family": label, "member": name, "identity": i, "kind": kind, "expected_content_folds": sorted(exp),
                                "kept_content_folds": sorted(kept), "dropped_content_folds": sorted(exp - kept),
                                "reference_admitted": sorted(ka), "candidate_admitted": sorted(kb)})
                pv[s][Rk], pv[s][Ck] = pr, pc
    return pv, cov


def restore_keys(res, fams):
    """write the members' original configurations back into the family results (the pair keys are internal)."""
    orig = {(f[2], m[0]): m for f in fams for m in f[3]}
    for label in res["families"]:
        for blk in [res["families"][label]] + list(res["secondary"][label].values()):
            for name, r in blk.get("members", {}).items():
                o = orig[(label, name)]
                r["ref"], r["cand"] = BI.ckey(o[1]), BI.ckey(o[2])
    return res


def full_families():
    """the ADDENDUM_12 D_ADAPT families (seed 3401): AD-GAIN | ds | obj | support and AD-SUPPORT | ds | obj, members input_spatial and
    output_low_rank."""
    return DL.ad_families()


def panel_families():
    """the D_MULTI_SEED panel restriction (NCE, member input_spatial; same labels)."""
    out = []
    for fam, sc, label, members in DL.ad_families():
        keep = [m for m in members if m[1][2] == "NCE" and m[2][2] == "NCE" and m[0] == "input_spatial"]
        if keep:
            out.append((fam, sc, label, keep))
    return out


def seed_mean_deltas(vals_by_seed, ref, cand, metric):
    """{identity: (mean over the seeds with the pair of the within-seed paired difference, number of such seeds)} (as d_multiseed)."""
    per = {s: BI.member_values(v, ref, cand, metric) for s, v in vals_by_seed.items()}
    ids = set().union(*[set(p) for p in per.values()]) if per else set()
    return {i: (float(np.mean([per[s][i] for s in per if i in per[s]])), int(sum(i in per[s] for s in per))) for i in ids}


def run_seed_mean(fams, vals_by_seed, grp, notes, complete_case=False, orig_fams=None):
    """identity mean over seeds through the same family machinery: reference 0, candidate = signed mean difference (so that
    bc_interim.diff returns the mean difference for every direction). With the content-fold-matched pairs, `fams` are pair_fams(...)
    and `vals_by_seed` the pair inputs; `orig_fams` are the families with the original configurations (written back)."""
    pv, sfams, nseeds = {}, [], {}
    for fam, sc, label, members in fams:
        mm = []
        for name, ref, cand, tag in members:
            Rk, Ck = ("SM_REF", label, name), ("SM_CAND", label, name)
            pr, pc = defaultdict(dict), defaultdict(dict)
            for m in METRIC_KEYS:
                sgn = -1.0 if direction(m) == "lower" else 1.0
                d = seed_mean_deltas(vals_by_seed, ref, cand, m)
                if m == PRIMARY:
                    nseeds[(label, name)] = {i: k for i, (_, k) in d.items()}
                for i, (x, k) in d.items():
                    if complete_case and k < len(vals_by_seed):
                        continue
                    pr[i][m] = 0.0; pc[i][m] = sgn * x
            pv[Rk], pv[Ck] = dict(pr), dict(pc)
            mm.append((name, Rk, Ck, tag))
        sfams.append((fam, sc, label, mm))
    res = restore_keys(DL.run_fams(sfams, pv, grp, METRIC_KEYS, PRIMARY, notes), fams if orig_fams is None else orig_fams)
    for label in res["families"]:
        for name, r in res["families"][label].get("members", {}).items():
            ns = nseeds.get((label, name), {})
            r["identities_by_n_seeds"] = {str(k): v for k, v in sorted(Counter(ns.values()).items())}
    return res


def member_block(res, label, metric):
    return res["families"].get(label, {}) if metric == PRIMARY else res["secondary"].get(label, {}).get(metric, {})


def between_seed(per_seed, fams):
    out = {}
    for fam, sc, label, members in fams:
        for name, *_ in members:
            for m in METRIC_KEYS:
                ests = {s: member_block(per_seed[s], label, m).get("members", {}).get(name, {}).get("est") for s in per_seed}
                xs = [v for v in ests.values() if v is not None]
                out[f"{label}|{name}|{m}"] = {"per_seed": ests, "min": min(xs) if xs else None, "max": max(xs) if xs else None,
                                              "spread": (max(xs) - min(xs)) if xs else None, "n_seeds": len(xs)}
    return out


def decomposition(res, fams):
    """identity-level Δgain(refit) − [ΔR + ΔR_mm] per member and readout (exact by construction) and Δgain(refit) − Δgain(record)."""
    out = {}
    for fam, sc, label, members in fams:
        for name, *_ in members:
            e = lambda m: member_block(res, label, m).get("members", {}).get(name, {}).get("est")
            for rd, sfx in (("unified", ""), ("native", "_native")):
                g, r, mmv, gr = e(f"gain_refit{sfx}"), e(f"R_bits{sfx}"), e(f"R_mm_bits{sfx}"), e(f"gain_record{sfx}")
                out[f"{label}|{name}|{rd}"] = {"d_gain_refit": g, "d_R": r, "d_R_mm": mmv, "d_gain_record": gr,
                                               "identity_residual": None if None in (g, r, mmv) else g - (r + mmv),
                                               "refit_minus_record": None if None in (g, gr) else g - gr}
    return out


def levels(vals_by_seed, K):
    """R per configuration and seed: identity mean with a pointwise bootstrap-t interval (descriptive), K and log2 K of the units."""
    out = {}
    for s, vals in vals_by_seed.items():
        for c in sorted(vals, key=BI.ckey):
            v = vals[c]
            r = {"seed": s, "n": len(v), "K": K.get(f"{c[1]}|{s}")}
            for m in ("R_bits", "R_bits_native", "R_mm_bits", "R_mm_bits_native"):
                ids = sorted(i for i in v if m in v[i] and np.isfinite(v[i][m]))
                y = np.array([v[i][m] for i in ids])
                if len(y) >= 3:
                    sm = S.summary(y, seed=S.group_seed("R34-DR-LEVEL", s, BI.ckey(c), m))
                    r[m] = {"n": len(y), **{k: float(sm[k]) for k in ("est", "ci_low", "ci_high")}}
                elif len(y):
                    r[m] = {"n": len(y), "est": float(y.mean())}
            out[f"{s}|{BI.ckey(c)}"] = r
    return out


def coverage(units, vals_by_seed, pair_cov, per_identity_units=None):
    """public coverage: counts only (the identity-level pair rows go to the private per-identity file; note, addendum 2, C3)."""
    cfg = defaultdict(Counter)
    for u in units:
        k = f"{u['seed']}|{u['dataset']}|{u['objective']}|{u['adapter']}"
        cfg[k]["listed"] += 1
        cfg[k]["output"] += u["output"] != "missing"
        cfg[k]["admitted"] += u["admitted"]
    idents = {}
    for s, vals in vals_by_seed.items():
        for c, v in vals.items():
            idents[f"{s}|{BI.ckey(c)}"] = len(v)
    pairs = defaultdict(Counter)
    for p in pair_cov:
        c = pairs[f"{p['seed']}|{p['family']}|{p['member']}"]
        c["expected"] += bool(p["expected_content_folds"]); c[p["kind"]] += 1
        c["asymmetric"] += p["reference_admitted"] != p["candidate_admitted"]
    kinds = Counter(p["kind"] for p in pair_cov)
    return {"by_configuration": {k: dict(v) for k, v in sorted(cfg.items())}, "identities": idents,
            "units_per_identity": per_identity_units or {}, "pairing": PAIRING,
            "pairs": {k: {x: v.get(x, 0) for x in ("expected", "complete", "partial", "missing", "asymmetric")} for k, v in sorted(pairs.items())},
            "n_complete_pairs": kinds.get("complete", 0), "n_partial_pairs": kinds.get("partial", 0), "n_missing_pairs": kinds.get("missing", 0),
            "n_asymmetric_pairs": sum(p["reference_admitted"] != p["candidate_admitted"] for p in pair_cov),
            "units_listed": len(units), "units_with_output": sum(u["output"] != "missing" for u in units),
            "units_admitted": sum(u["admitted"] for u in units)}


def qc_summary(units, out_load):
    by = defaultdict(Counter)
    cells = defaultdict(list)
    for u in units:
        t = u["tier"]
        by[t]["listed"] += 1
        if u["output"] == "missing":
            continue
        by[t]["output"] += 1; by[t]["pass"] += bool(u.get("qc_pass")); by[t]["structural_pass"] += bool(u.get("structural_pass"))
        by[t]["steps_equal"] += bool(u.get("steps_equal"))
        out = out_load(u["eid"])
        for c in out["qc"]["cells"]:
            cells[(t, c["readout"])].append(c["d_gain_bits"])
    fails = [u for u in units if u["output"] != "missing" and not u.get("qc_pass")]
    return {"by_tier": {k: dict(v) for k, v in by.items()}, "d_gain_bits": {f"{t}|{rd}": _dev_summary(x) for (t, rd), x in sorted(cells.items())},
            "failing_units": [{k: u.get(k) for k in ("eid", "seed", "dataset", "objective", "adapter", "subject_fold", "content_fold", "tier",
                                                       "steps_recorded", "steps_refit", "max_abs_d_gain_bits", "n_problems", "problem_kinds")} for u in fails],
            "devices": dict(Counter(u.get("device_name") for u in units if u["output"] != "missing")),
            "loaders": dict(Counter(u.get("loader") for u in units if u["output"] != "missing")),
            "evaluator_versions": dict(Counter(u.get("evaluator_sha256") for u in units if u["output"] != "missing")),
            "value_path_versions": dict(Counter(str(u.get("value_path_sha256")) for u in units if u["output"] != "missing"))}


def analyse(rows, out_load, rec_load=load_record):
    """returns (public aggregate, private per-identity file). The family runs use the content-fold-matched pairs (note, addendum 2, C1)."""
    setup()
    notes = []
    C = collect(rows, out_load, rec_load)
    vals, grp, K = C["vals"], C["groups"], C["K"]
    ff, pf = full_families(), panel_families()
    pv, pair_cov = pair_inputs(ff, C["cells"], C["expected"])  # the panel members are members of the full families (same labels)
    pff, ppf = pair_fams(ff), pair_fams(pf)
    full = restore_keys(DL.run_fams(pff, pv[3401], grp, METRIC_KEYS, PRIMARY, notes), ff)
    per_seed = {s: restore_keys(DL.run_fams(ppf, pv[s], grp, METRIC_KEYS, PRIMARY, notes), pf) for s in SEEDS}
    mean = run_seed_mean(ppf, pv, grp, notes, orig_fams=pf)
    complete = run_seed_mean(ppf, pv, grp, notes, complete_case=True, orig_fams=pf)
    out = {"pairing": PAIRING, "full_3401": full, "panel_per_seed": {str(s): per_seed[s] for s in SEEDS}, "panel_identity_mean": mean,
           "panel_identity_mean_complete_case": complete, "between_seed": between_seed(per_seed, pf),
           "decomposition_full_3401": decomposition(full, ff), "decomposition_panel_mean": decomposition(mean, pf),
           "levels": levels(vals, K), "K": K, "coverage": coverage(C["units"], vals, pair_cov, C["units_per_identity"]),
           "qc": qc_summary(C["units"], out_load), "units": C["units"], "notes": notes}
    per_identity = {str(s): {BI.ckey(c): v for c, v in vals[s].items()} for s in SEEDS}
    per_identity["groups"] = {f"{k[0]}|{k[1]}": g for k, g in grp.items()}
    per_identity["pair_values"] = {str(s): {f"{k[1]}|{k[2]}|{'ref' if k[0] == 'PAIR_REF' else 'cand'}": v for k, v in pv[s].items() if v} for s in SEEDS}
    per_identity["pair_coverage"] = pair_cov
    per_identity["qc_problems"] = C["problems"]
    per_identity["_ids"] = sorted(C["ids"])
    return out, per_identity


# ------------------------------------------------------------------------------------------------ report
def f3(x):
    return "–" if x is None else f"{x:+.3f}"


def iv(m, lo="ci_low", hi="ci_high"):
    return "–" if not m or lo not in m else f"[{m[lo]:+.3f}, {m[hi]:+.3f}]"


def lab(label):
    return label.replace("|", " · ")


def _member(res, label, name, metric):
    return member_block(res, label, metric).get("members", {}).get(name, {})


def family_table(res, fams):
    L = ["| family · member | n | ΔR unified [95% CI] | [sim.] · class | ΔR native [95% CI] | ΔR_mm unified (cand − ref) | Δgain unified refit | Δgain unified record | Δgain native refit | Δgain native record |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for fam, sc, label, members in fams:
        crit = res["families"].get(label, {}).get("crit")
        for name, *_ in members:
            p = _member(res, label, name, PRIMARY)
            if not p:
                L.append(f"| {lab(label)} · {name} | 0 | – | – | – | – | – | – | – | – |"); continue
            sim = "–" if "sim_low" not in p else f"[{p['sim_low']:+.3f}, {p['sim_high']:+.3f}] {p['class']}"
            g = lambda m: f3(_member(res, label, name, m).get("est"))
            L.append(f"| {lab(label)} · {name} | {p['n']} | {f3(p.get('est'))} {iv(p)} | {sim} | {g('R_bits_native')} {iv(_member(res, label, name, 'R_bits_native'))} | "
                     f"{g('R_mm_bits')} | {g('gain_refit')} | {g('gain_record')} | {g('gain_refit_native')} | {g('gain_record_native')} |")
        if crit is not None:
            L.append(f"| ↳ critical value {lab(label)} | | {crit:.2f} | | | | | | | |")
    return L


def panel_table(out, fams):
    L = ["| family · member | n | seed 3401 ΔR [sim.] | seed 3407 ΔR [sim.] | seed 3413 ΔR [sim.] | between-seed range (spread) | identity mean ΔR [95% CI] | identity mean [sim.] · class |",
         "|---|---|---|---|---|---|---|---|"]
    for fam, sc, label, members in fams:
        for name, *_ in members:
            cells = []
            for s in SEEDS:
                p = _member(out["panel_per_seed"][str(s)], label, name, PRIMARY)
                cells.append("–" if not p else f"{f3(p.get('est'))} {iv(p, 'sim_low', 'sim_high')} {p.get('class', '')}")
            b = out["between_seed"].get(f"{label}|{name}|{PRIMARY}", {})
            rng = "–" if b.get("min") is None else f"[{b['min']:+.3f}, {b['max']:+.3f}] ({b['spread']:.3f})"
            m = _member(out["panel_identity_mean"], label, name, PRIMARY)
            L.append(f"| {lab(label)} · {name} | {m.get('n', 0)} | " + " | ".join(cells) + f" | {rng} | {f3(m.get('est'))} {iv(m)} | "
                     f"{iv(m, 'sim_low', 'sim_high')} {m.get('class', '–')} |")
    return L


def render(out, meta):
    cov, qc = out["coverage"], out["qc"]
    ff, pf = full_families(), panel_families()
    L = [f"# D_ADAPT true-query risk R — seeds 3401 / 3407 / 3413 (R34_DADAPT_R, execution {VERSION})", "",
         "<!-- Generated by `python -m auditory_alignment_v3.aln34.dadapt_r --aggregate --update-doc`: the preamble and sections 1 and 5. "
         "Sections 2-4 and 6 are written by hand after the generated tables were viewed; the generator carries them over verbatim. -->", "",
         f"**日期／代码与数据版本 (date, code and data versions).** Generated {meta['generated']} on `{meta['host']}` (Slurm {meta['slurm_job']}). "
         f"Aggregation code sha256: " + ", ".join(f"`{k}` {v[:12]}" for k, v in meta["code_sha256"].items()) + f". Analysis note "
         f"`{meta['note']}` sha256 {meta['note_sha256'][:12]} (last modified {meta['note_mtime']}). Per-unit outputs: `{meta['units_dir']}`.", "",
         f"**本轮完成／运行／待依赖 (live state).** Listed units {cov['units_listed']}; with an output {cov['units_with_output']}; admitted "
         f"(QC pass) {cov['units_admitted']}; identity pairs (seed × member) complete {cov['n_complete_pairs']}, partial {cov['n_partial_pairs']}, "
         f"missing {cov['n_missing_pairs']}. Devices: {qc['devices']}. Loaders: {qc['loaders']}.", "",
         "**已见信息与本轮新增信息 (seen before / new).** Seen before: all D_ADAPT gain results (seed 3401 and panel). New: every R, R_mm and "
         "refit-gain value in this document.", "",
         "## 1. 当前观察 (observation)", "",
         "### Scope, units and statistics", "",
         "- R = unified logloss_bits of the true pairing against the full test candidate pool on the fixed last-70 % query (bits per query; lower = "
         "better). ΔR = R(reference) − R(candidate): positive = lower risk with the candidate. ΔR_mm = candidate − reference (mismatched-EEG "
         "logloss). Δgain = candidate − reference; per identity Δgain = ΔR + ΔR_mm exactly (§1.4).",
         "- n counts unique test identities. Within a pair (reference → candidate) both sides of an identity are averaged over the same content "
         "folds, those admitted on both sides (normally its two content folds; analysis note, addendum 2, C1); partial and missing pairs are "
         "counted in §1.6. Seeds, folds and content folds never add n. Bootstrap-t over identities, B = 4,000; [sim.] = simultaneous 95 % by "
         "max-t within the family. No p-values.",
         "- Tier exact (none, input_spatial): the refit reproduces the recorded fit (QC §1.8). Tier seeded_refit (output_low_rank): a new seeded "
         "fit; its gain differs from the record by the initialisation draw (columns 'refit' vs 'record').", "",
         "### 1.1 Seed 3401, ADDENDUM_12 families (AD-GAIN: none → adapter; AD-SUPPORT: 0.1 → 0.3)", ""]
    L += family_table(out["full_3401"], ff)
    L += ["", "### 1.2 Panel (NCE, input_spatial): per seed and identity mean over seeds", ""]
    L += panel_table(out, pf)
    L += ["", "Complete-case identity mean (identities with all three seeds):", ""]
    L += family_table(out["panel_identity_mean_complete_case"], pf)
    L += ["", "Panel identity mean, all readouts:", ""]
    L += family_table(out["panel_identity_mean"], pf)
    L += ["", "### 1.3 Per group (seed 3401 families; descriptive, pointwise; n < 5 → n only)", "", "| family · member | per group ΔR |", "|---|---|"]
    for fam, sc, label, members in ff:
        for name, *_ in members:
            p = _member(out["full_3401"], label, name, PRIMARY)
            gs = "; ".join(f"{g}: " + (f"{x['est']:+.3f} [{x['ci_low']:+.3f}, {x['ci_high']:+.3f}] (n={x['n']})" if "est" in x else f"n={x['n']}")
                           for g, x in sorted((p.get("groups") or {}).items()))
            L.append(f"| {lab(label)} · {name} | {gs or '–'} |")
    L += ["", "### 1.4 Decomposition and refit versus record (identity-level estimates)", "",
          "| family · member · readout | Δgain refit | ΔR | ΔR_mm | Δgain refit − (ΔR + ΔR_mm) | Δgain record | refit − record |", "|---|---|---|---|---|---|---|"]
    for key, d in list(out["decomposition_full_3401"].items()) + [(f"identity mean · {k}", v) for k, v in out["decomposition_panel_mean"].items()]:
        res = "–" if d["identity_residual"] is None else f"{d['identity_residual']:+.1e}"
        rr = "–" if d["refit_minus_record"] is None else f"{d['refit_minus_record']:+.4f}"
        L.append(f"| {lab(key)} | {f3(d['d_gain_refit'])} | {f3(d['d_R'])} | {f3(d['d_R_mm'])} | {res} | {f3(d['d_gain_record'])} | {rr} |")
    L += ["", "### 1.5 Levels (descriptive; R per configuration, identity mean [pointwise 95% CI]; K = candidates, log2 K = uniform-score logloss)", "",
          "| seed · configuration | n | K | R unified | R native | R_mm unified |", "|---|---|---|---|---|---|"]
    for k, r in out["levels"].items():
        cell = lambda m: "–" if m not in r else (f"{r[m]['est']:.3f} [{r[m]['ci_low']:.3f}, {r[m]['ci_high']:.3f}]" if "ci_low" in r[m] else f"{r[m]['est']:.3f}")
        Ks = r.get("K") or []
        L.append(f"| {k.replace('|', ' · ')} | {r['n']} | {', '.join(f'{x} (log2 {np.log2(x):.2f})' for x in Ks) or '–'} | {cell('R_bits')} | {cell('R_bits_native')} | {cell('R_mm_bits')} |")
    L += ["", "### 1.6 Coverage", "", "| seed · dataset · objective · adapter | listed | with output | admitted | identities · units per identity (0.1 / 0.3) |",
          "|---|---|---|---|---|"]
    for k, v in cov["by_configuration"].items():
        s_, ds_, o_, a_ = k.split("|")
        upi = "; ".join(f"{sf}: {cov['identities'].get(f'{s_}|AD|{ds_}|{o_}|{a_}|{sf}', 0)} · {cov['units_per_identity'].get(f'{s_}|AD|{ds_}|{o_}|{a_}|{sf}', {})}"
                        for sf in SUPPORTS)
        L.append(f"| {k.replace('|', ' · ')} | {v.get('listed', 0)} | {v.get('output', 0)} | {v.get('admitted', 0)} | {upi} |")
    L += ["", f"Identity pairs per seed × family member (content-fold matched; complete / partial / missing, never filled; identity lists in the "
              f"private per-identity file): complete {cov['n_complete_pairs']}, partial {cov['n_partial_pairs']}, missing {cov['n_missing_pairs']}, "
              f"with unequal admitted content folds on the two sides {cov['n_asymmetric_pairs']}.", ""]
    inc = {k: v for k, v in cov["pairs"].items() if v.get("partial") or v.get("missing")}
    if inc:
        L += ["| seed · family · member | expected | complete | partial | missing | unequal sides |", "|---|---|---|---|---|---|"]
        L += [f"| {lab(k)} | {v['expected']} | {v['complete']} | {v['partial']} | {v['missing']} | {v['asymmetric']} |" for k, v in inc.items()]
    else:
        L += ["Every expected pair is complete."]
    L += ["", "### 1.7 Reproduction QC (rules in the analysis note)", "", f"- By tier: {qc['by_tier']}.",
          f"- Δgain_bits (refit − record) over participant × support cells: {qc['d_gain_bits']}.",
          f"- Failing units: {len(qc['failing_units'])}" + ("." if not qc["failing_units"] else ": " + "; ".join(
              f"{u['eid']} ({u['tier']}, steps {u['steps_recorded']}→{u['steps_refit']}, max|Δgain| {u['max_abs_d_gain_bits']:.2e}, "
              f"{u['n_problems']} problems: {', '.join(f'{k} ×{n}' for k, n in sorted((u.get('problem_kinds') or {}).items())) or '–'})" for u in qc["failing_units"])),
          f"- Evaluator versions among the outputs: {qc['evaluator_versions']}; value-path versions: {qc['value_path_versions']}.", ""]
    for h in ("## 2. 当前工作判断 (working interpretation)", "## 3. 仍竞争的解释 (competing explanations)", "## 4. 下一轮干预 (next intervention)"):
        L += [h, "", "_Not written yet: written by hand after the generated tables have been viewed._", ""]
    L += ["## 5. 复用与运行 (reuse and execution)", "",
          f"- Per-unit re-fits: {cov['units_with_output']} outputs of {cov['units_listed']} listed units; aggregation in {meta['runtime_seconds']} s, "
          f"peak resident memory {meta['peak_rss_mib']:.0f} MiB.",
          f"- Outputs (0600): `{meta['json']}`; this document; private per-identity values, identity-level pair coverage and the full QC "
          f"problem strings `{meta['per_identity']}`. The public outputs carry no participant id (identity scan before writing).", "",
          "## 6. 暂不决定 (not decided here)", "", "_Not written yet: written by hand after the generated tables have been viewed._", ""]
    return "\n".join(L)


def sections(text):
    out, head, buf = [], None, []
    for line in text.split("\n"):
        if line.startswith("## "):
            out.append((head, buf)); head, buf = line, []
        else:
            buf.append(line)
    out.append((head, buf))
    return [(h, "\n".join(b)) for h, b in out]


def _hand_key(h):
    return None if h is None or len(h.split()) < 2 or h.split()[1] not in HAND else h.split()[1]


def splice(generated, existing):
    """generated sections from `generated`; hand-written sections (HAND) verbatim from `existing` when present there."""
    old = {_hand_key(h): (h, b) for h, b in sections(existing) if _hand_key(h)}
    used, parts = set(), []
    for h, b in sections(generated):
        k = _hand_key(h)
        if k in old:
            h, b = old[k]; used.add(k)
        parts.append(b if h is None else f"{h}\n{b}")
    if set(old) - used:
        raise ValueError(f"hand-written sections missing from the template: {sorted(set(old) - used)}")
    return "\n".join(parts)


def identity_hits(obj, text, ids):
    """participant ids in the public outputs (note, addendum 2, C3): JSON keys or string values equal to an id, or starting with
    '<id>:' / '<id>/' (the QC problem form); DTU-style ids anywhere; ids quoted in the document."""
    ids = {str(i) for i in ids}
    hits, dtu = set(), re.compile(r"\bsub-\d{2,}\b")

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(str(k)); walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            head = re.split(r"[:/ ]", x, maxsplit=1)[0]
            if x in ids or (head in ids and x != head):
                hits.add(x[:60])
            hits.update(dtu.findall(x))
    walk(obj)
    hits.update(dtu.findall(text))
    hits.update(i for i in ids if re.search(r"""['"`]""" + re.escape(i) + r"""['"`]""", text))
    return sorted(hits)


def aggregate_main(update_doc=False, units_dir=UNITS_DIR):
    t0 = time.time()
    rows = all_rows()
    out, per_identity = analyse(rows, lambda e: load_output(units_dir, e))
    ids = per_identity.pop("_ids", [])
    here = os.path.dirname(os.path.abspath(__file__))
    jp, pp = os.path.join(RES, "dadapt_r.json"), os.path.join(PRIV, "per_identity.json")
    meta = {"track": "R34_DADAPT_R", "execution_version": VERSION, "generated": time.strftime("%Y-%m-%d %H:%M %Z"), "host": socket.gethostname(),
            "slurm_job": os.environ.get("SLURM_JOB_ID", "none"), "n_boot": S.NB,
            "code_sha256": {"aln34/dadapt_r.py": MODULE_SHA256, **{rel: sha256_file(os.path.join(REPO, rel)) for rel in AGG_CODE}},
            "note": os.path.relpath(NOTE, REPO), "note_sha256": sha256_file(NOTE),
            "note_mtime": time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(os.path.getmtime(NOTE))),
            "units_dir": os.path.relpath(units_dir, REPO), "json": os.path.relpath(jp, REPO), "per_identity": os.path.relpath(pp, REPO),
            "tests": os.path.relpath(TESTS, REPO), "module_dir": os.path.relpath(here, REPO)}
    meta["runtime_seconds"] = round(time.time() - t0, 1)
    meta["peak_rss_mib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    pub = BI.jl({"meta": meta, **out})
    gen = render(out, meta)
    doc = os.path.join(DOCS, DOC_NAME)
    if update_doc:
        text = splice(gen, open(doc).read()) if os.path.exists(doc) else gen
    else:
        doc, text = os.path.join(RES, DOC_NAME.replace(".md", ".generated.md")), gen
    write_json(pp, per_identity)
    hits = identity_hits(pub, text, ids)
    print("identity scan of the public outputs:", "PASS" if not hits else f"FAIL {hits[:20]}")
    if hits:  # nothing public is written
        raise SystemExit(3)
    write_json(jp, pub)
    write_text(doc, text)
    bad = BI.privacy_scan([jp, doc], set())
    print("doc:", doc, "| units with output", out["coverage"]["units_with_output"], "/", out["coverage"]["units_listed"], "| admitted",
          out["coverage"]["units_admitted"], "| missing pairs", out["coverage"]["n_missing_pairs"], "| qc", out["qc"]["by_tier"])
    print("privacy scan:", "PASS" if not bad else bad)
    if bad:
        raise SystemExit(2)
    return out


# ================================================================================================ CLI
def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument("--unit"); g.add_argument("--units-file"); g.add_argument("--aggregate", action="store_true"); g.add_argument("--write-units", action="store_true")
    a.add_argument("--device", default="cuda"); a.add_argument("--out", default=UNITS_DIR); a.add_argument("--loader", default="original", choices=("original", "ss_only"))
    a.add_argument("--shard"); a.add_argument("--worker-tag", default="w0"); a.add_argument("--max-tries", type=int, default=MAX_TRIES)
    a.add_argument("--no-steal", action="store_true"); a.add_argument("--claimed", action="store_true", help=argparse.SUPPRESS)
    a.add_argument("--force", action="store_true", help="--unit: re-run even when an output exists (engineering tests only)")
    a.add_argument("--threads", type=int); a.add_argument("--rss-limit-mib", type=float); a.add_argument("--update-doc", action="store_true")
    a.add_argument("--units-dir", default=UNITS_DIR, help="--aggregate: directory of the per-unit outputs")
    args = a.parse_args(argv)
    os.umask(0o077)
    if args.rss_limit_mib:
        start_rss_watchdog(args.rss_limit_mib)
    if args.threads:
        import torch
        torch.set_num_threads(args.threads)
    if args.unit:
        return unit_main(args.unit, args.device, args.out, args.loader, args.claimed, args.force)
    if args.units_file:
        run_units_file(args.units_file, args.device, args.out, parse_shard(args.shard), args.worker_tag, args.loader, args.max_tries,
                       not args.no_steal, args.threads)
        return 0
    if args.write_units:
        write_units()
        return 0
    aggregate_main(args.update_doc, args.units_dir)
    return 0


EVALUATOR_SHA256 = evaluator_sha256()  # at import, while the file on disk is the source just loaded
VALUE_PATH_SHA256 = value_path_sha256()

if __name__ == "__main__":
    sys.exit(main())
