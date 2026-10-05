"""P0 schema audit for the public C3 sources (02_DATASET_REGISTER "P0 必须核对").

Reads structure, attributes, sampling metadata and the stimulus/aux-channel alignment only. It computes no EEG
quantity. Per-participant listings go to private/auditory_c3/receipts/ (0700); stdout carries counts only.

Usage: python -m auditory_c3.p0_audit <fau_tud|federici|dtu_snhl> [--align]
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys

import numpy as np

ROOT = "/projects/EEG-foundation-model/auditory_public"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "private", "auditory_c3", "receipts")


def _jsonable(v):
    if isinstance(v, bytes):
        return v.decode(errors="replace")
    if isinstance(v, np.ndarray):
        return v.tolist() if v.size <= 64 else {"array_shape": list(v.shape), "dtype": str(v.dtype)}
    if isinstance(v, np.generic):
        return v.item()
    return v


def _dump(name, obj):
    os.makedirs(OUT, mode=0o700, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)
    os.chmod(path, 0o600)
    return path


# --------------------------------------------------------------------------------------------------- FAU/TUD
def _env(x, fs, cutoff=8.0):
    from scipy.signal import butter, sosfiltfilt
    sos = butter(4, cutoff, fs=fs, output="sos")
    return sosfiltfilt(sos, np.abs(x))


def _xcorr_peak(a, b, max_lag):
    """Lag (samples) maximising Pearson r of a(t) vs b(t - lag); positive = b leads a."""
    a = (a - a.mean()) / (a.std() + 1e-12)
    b = (b - b.mean()) / (b.std() + 1e-12)
    n = len(a)
    nfft = 1 << (2 * n - 1).bit_length()
    c = np.fft.irfft(np.fft.rfft(a, nfft) * np.conj(np.fft.rfft(b, nfft)), nfft) / n
    lags = np.arange(-max_lag, max_lag + 1)
    vals = c[lags % nfft]
    i = int(np.argmax(vals))
    return int(lags[i]), float(vals[i])


def audit_fau_tud(align: bool):
    import h5py
    files = {"ha": "zenodo_17927767_ha/hi_dataset_1kHz.hdf5", "ci": "zenodo_17952844_ci/ci_dataset_1kHz.hdf5",
             "th": "zenodo_17952231_th/nh_dataset_1kHz.hdf5"}
    summary, private = {}, {}
    for grp, rel in files.items():
        path = os.path.join(ROOT, "fau_tud", rel)
        g_sum = {"file": rel, "bytes": os.path.getsize(path)}
        g_priv = {}
        with h5py.File(path, "r") as f:
            g_sum["root_keys"] = sorted(f.keys())
            g_sum["root_attrs"] = {k: _jsonable(v) for k, v in f.attrs.items()}
            # stimulus_files
            sf = f["stimulus_files"]
            stim = {}
            for code in sorted(sf.keys()):
                stim[code] = {k: {"shape": list(sf[code][k].shape), "dtype": str(sf[code][k].dtype),
                                  "attrs": {a: _jsonable(b) for a, b in sf[code][k].attrs.items()}}
                              for k in sf[code].keys()}
                stim[code]["_attrs"] = {a: _jsonable(b) for a, b in sf[code].attrs.items()}
            g_sum["stimulus_codes"] = sorted(stim.keys())
            g_sum["stimulus_example"] = stim[sorted(stim)[0]]
            # every attribute name seen anywhere under eeg branches (behaviour fields would show up here)
            attr_names = collections.Counter()
            for br in [k for k in f.keys() if k.startswith("eeg")]:
                subs = sorted(f[br].keys())
                b_sum = {"n_subjects": len(subs), "subject_group_digits": dict(collections.Counter(s[0] for s in subs))}
                n_trials, n_rows, durs, removed = [], collections.Counter(), [], collections.Counter()
                for s in subs:
                    sg = f[br][s]
                    for a in sg.attrs:
                        attr_names[f"{br}/<subject>.attrs:{a}"] += 1
                    keys = list(sg.keys())
                    trials = [k for k in keys if k.isdigit()]
                    others = [k for k in keys if not k.isdigit()]
                    for o in others:
                        attr_names[f"{br}/<subject>/{o}"] += 1
                    tio = sg["taken_out_indices"][()] if "taken_out_indices" in sg else None
                    removed[0 if tio is None else int(np.size(tio))] += 1
                    n_trials.append(len(trials))
                    rec = {"trials": {}, "taken_out_indices": _jsonable(tio) if tio is not None else None,
                           "attrs": {a: _jsonable(v) for a, v in sg.attrs.items()}}
                    for t in trials:
                        ds = sg[t]
                        n_rows[ds.shape[0]] += 1
                        durs.append(ds.shape[1] / 1000.0)
                        for a in ds.attrs:
                            attr_names[f"{br}/<subject>/<trial>.attrs:{a}"] += 1
                        rec["trials"][t] = {"shape": list(ds.shape), "attrs": {a: _jsonable(v) for a, v in ds.attrs.items()}}
                    g_priv[f"{br}/{s}"] = rec
                b_sum.update({"trials_per_subject": dict(collections.Counter(n_trials)), "rows_per_trial": dict(n_rows),
                              "trial_seconds": {"min": float(np.min(durs)), "median": float(np.median(durs)),
                                                "max": float(np.max(durs)), "total_hours": float(np.sum(durs) / 3600)},
                              "n_removed_electrodes": dict(removed)})
                g_sum[br] = b_sum
            g_sum["attribute_and_member_names"] = dict(attr_names)
            if align:
                g_sum["alignment"] = _align_group(f, grp, g_priv)
        summary[grp] = g_sum
        private[grp] = g_priv
    # wav files
    import soundfile as sf_
    wavs = {}
    for w in sorted(glob.glob(os.path.join(ROOT, "fau_tud", "stimuli", "stimuli", "*.wav"))):
        info = sf_.info(w)
        wavs[os.path.basename(w)] = {"sr": info.samplerate, "channels": info.channels, "seconds": info.duration}
    summary["wav_files"] = {"n": len(wavs), "total_seconds": sum(v["seconds"] for v in wavs.values()),
                            "channels": dict(collections.Counter(v["channels"] for v in wavs.values())),
                            "sr": dict(collections.Counter(v["sr"] for v in wavs.values())), "per_file": wavs}
    return summary, private


def _align_group(f, grp, g_priv):
    """Per trial: lag of each aux row's envelope against attended/distractor envelope from the HDF5 (1 kHz).
    Aux rows are the last two rows (audio splitter recordings), not EEG."""
    out = []
    for s in sorted(f["eeg"].keys()):
        sg = f["eeg"][s]
        for t in sorted([k for k in sg.keys() if k.isdigit()], key=int):
            ds = sg[t]
            code = ds.attrs["stimulus"]
            code = code.decode() if isinstance(code, bytes) else str(code)
            aux = ds[ds.shape[0] - 2:, :].astype(float)
            row = {"subject": s, "trial": int(t), "stimulus": code}
            for name in ("attended_env", "distractor_env"):
                key = f"stimulus_files/{code}/{name}"
                if key not in f:
                    continue
                env = np.asarray(f[key][()], float).ravel()
                n = min(len(env), aux.shape[1])
                if n < 20000 or env[:n].std() == 0:
                    continue
                for r in range(2):
                    lag, rr = _xcorr_peak(_env(aux[r, :n], 1000.0), env[:n], 1000)
                    row[f"aux{r}_{name}"] = {"lag_ms": lag, "r": round(rr, 4)}
            out.append(row)
    g_priv["_alignment_rows"] = out
    best = []
    for row in out:
        cands = [v for k, v in row.items() if k.startswith("aux") and "attended" in k]
        if cands:
            best.append(max(cands, key=lambda v: v["r"]))
    lags = np.array([b["lag_ms"] for b in best]); rs = np.array([b["r"] for b in best])
    return {"n_trials": len(out), "n_with_attended_env": int(len(best)),
            "best_aux_attended_lag_ms": {"min": int(lags.min()), "p05": float(np.percentile(lags, 5)), "median": float(np.median(lags)),
                                         "p95": float(np.percentile(lags, 95)), "max": int(lags.max()),
                                         "n_abs_le_5ms": int(np.sum(np.abs(lags) <= 5))} if len(best) else None,
            "best_aux_attended_r": {"min": float(rs.min()), "median": float(np.median(rs))} if len(best) else None}


# --------------------------------------------------------------------------------------------------- Federici
def audit_federici():
    import scipy.io as sio
    base = glob.glob(os.path.join(ROOT, "federici_ci_children", "mendeley_nzg5g2gzrd_v2", "files", "*", "Code"))[0]
    summary, private = {}, {}
    for g in ("02_HC_Encoding_model", "03_CI_Encoding_model", "04_HC-v_Encoding_model", "06_Artifact_Encoding_model"):
        eeg_files = sorted(glob.glob(os.path.join(base, g, "Data", "EEG", "*")))
        env_files = sorted(glob.glob(os.path.join(base, g, "Data", "StimulusEnvelope", "*")))
        g_sum = {"n_eeg_entries": len(eeg_files), "n_env_entries": len(env_files)}
        # entries may be folders (mat_data_cut_<id>) holding the .mat files
        mats = sorted(glob.glob(os.path.join(base, g, "Data", "EEG", "**", "*.mat"), recursive=True))
        envs = sorted(glob.glob(os.path.join(base, g, "Data", "StimulusEnvelope", "**", "*.mat"), recursive=True))
        g_sum["n_eeg_mat"] = len(mats); g_sum["n_env_mat"] = len(envs)
        g_sum["eeg_mat_name_patterns"] = dict(collections.Counter(re.sub(r"\d{3,}", "<ID>", os.path.basename(m)) for m in mats))
        ex = {}
        for m in (mats[:2] + envs[:2]):
            try:
                d = sio.loadmat(m, squeeze_me=True, struct_as_record=False)
                ex[os.path.relpath(m, base)] = _describe_mat(d)
            except NotImplementedError:
                import h5py
                with h5py.File(m, "r") as h:
                    ex[os.path.relpath(m, base)] = {"v7.3_keys": list(h.keys())}
        g_sum["examples"] = ex
        ids = sorted({re.match(r"(\d+)", os.path.basename(m)).group(1) for m in mats if re.match(r"\d+", os.path.basename(m))})
        g_sum["n_distinct_ids"] = len(ids)
        private[g] = {"ids": ids, "eeg_mats": [os.path.relpath(m, base) for m in mats]}
        summary[g] = g_sum
    hc, hcv = set(private["02_HC_Encoding_model"]["ids"]), set(private["04_HC-v_Encoding_model"]["ids"])
    summary["hc_v_ids_in_hc"] = len(hcv & hc)
    # behavioural / descriptive tables: headers and row counts only on stdout; full sheets stay private
    import pandas as pd
    tabs = {}
    for x in sorted(glob.glob(os.path.join(base, "**", "*.xlsx"), recursive=True)):
        try:
            sheets = pd.read_excel(x, sheet_name=None)
            tabs[os.path.relpath(x, base)] = {s: {"n_rows": int(len(df)), "columns": [str(c) for c in df.columns]} for s, df in sheets.items()}
        except Exception as e:  # noqa: BLE001
            tabs[os.path.relpath(x, base)] = {"error": type(e).__name__}
    summary["xlsx_tables"] = tabs
    mats_beh = {}
    for m in sorted(glob.glob(os.path.join(base, "07_TRF_CI_biomarker", "*.mat"))):
        try:
            mats_beh[os.path.basename(m)] = _describe_mat(sio.loadmat(m, squeeze_me=True, struct_as_record=False))
        except Exception as e:  # noqa: BLE001
            mats_beh[os.path.basename(m)] = {"error": type(e).__name__}
    summary["biomarker_mats"] = mats_beh
    # sampling / filter evidence in the authors' code (D2)
    hits = []
    for mf in sorted(glob.glob(os.path.join(base, "0*", "*.m"))):
        for i, line in enumerate(open(mf, errors="replace")):
            if re.search(r"\b(fs|Fs|srate|fsample|resample|filt|lpf|hpf|bandpass|tmin|tmax|lags?)\b", line):
                hits.append(f"{os.path.relpath(mf, base)}:{i + 1}: {line.strip()[:160]}")
    summary["code_sampling_filter_lines"] = hits[:120]
    return summary, private


def _describe_mat(d):
    out = {}
    for k, v in d.items():
        if k.startswith("__"):
            continue
        if hasattr(v, "_fieldnames"):
            sub = {}
            for fn in v._fieldnames:
                fv = getattr(v, fn)
                if isinstance(fv, np.ndarray):
                    sub[fn] = {"shape": list(fv.shape), "dtype": str(fv.dtype)}
                elif isinstance(fv, (int, float, str, np.generic)):
                    sub[fn] = _jsonable(fv)
                else:
                    sub[fn] = type(fv).__name__
            out[k] = {"struct_fields": sub}
        elif isinstance(v, np.ndarray):
            out[k] = {"shape": list(v.shape), "dtype": str(v.dtype)}
            if v.dtype == object and v.size:
                first = v.flat[0]
                out[k]["first_elem"] = {"type": type(first).__name__,
                                        "shape": list(first.shape) if isinstance(first, np.ndarray) else None}
        else:
            out[k] = _jsonable(v) if isinstance(v, (int, float, str, np.generic)) else type(v).__name__
    return out


# --------------------------------------------------------------------------------------------------- DTU
def audit_dtu():
    import pandas as pd
    S = os.path.join(ROOT, "dtu_snhl", "ds-eeg-snhl", "ds-eeg-snhl")
    p = pd.read_csv(os.path.join(S, "participants.tsv"), sep="\t")
    summary = {"n_participants": int(len(p)), "hearing_status": dict(p["hearing_status"].value_counts()),
               "participant_columns": list(p.columns),
               "srt_non_missing": int(p["speech_reception_thresholds"].notna().sum()),
               "dataset_description": json.load(open(os.path.join(S, "dataset_description.json")))}
    tasks = collections.Counter(); fs = collections.Counter(); chans = collections.Counter()
    for js in sorted(glob.glob(os.path.join(S, "sub-*", "eeg", "*_eeg.json"))):
        d = json.load(open(js)); t = re.search(r"task-([a-z]+)", js).group(1)
        tasks[t] += 1; fs[f"{t}:{d.get('SamplingFrequency')}"] += 1; chans[f"{t}:{d.get('EEGChannelCount')}+{d.get('EOGChannelCount')}eog+{d.get('MiscChannelCount')}misc"] += 1
    summary.update({"task_counts": dict(tasks), "sampling": dict(fs), "channels": dict(chans)})
    ev = sorted(glob.glob(os.path.join(S, "sub-*", "eeg", "*task-selectiveattention_events.tsv")))
    cols, trig, talkers = None, collections.Counter(), collections.Counter()
    for e in ev:
        df = pd.read_csv(e, sep="\t"); cols = list(df.columns)
        trig.update(df["trigger_type"].dropna().astype(str))
        on = df[df["trigger_type"] == "targetonset"]
        talkers.update(on["single_talker_two_talker"].astype(str))
    summary.update({"events_columns": cols, "trigger_types": dict(trig), "target_onsets_by_talker_condition": dict(talkers)})
    der = os.path.join(S, "derivatives", "stimuli")
    files = glob.glob(os.path.join(der, "**", "*"), recursive=True)
    summary["derivative_stimuli"] = {"n_subject_dirs": len(glob.glob(os.path.join(der, "sub*"))),
                                     "file_patterns": dict(collections.Counter(re.sub(r"\d+", "<n>", os.path.relpath(f, der)) for f in files if os.path.isfile(f)).most_common(15))}
    summary["derivative_readme_head"] = open(os.path.join(S, "derivatives", "README")).read()[:3000] if os.path.exists(os.path.join(S, "derivatives", "README")) else None
    summary["readme_head"] = open(os.path.join(S, "README")).read()[:4000]
    summary["raw_wav_present"] = len(glob.glob(os.path.join(S, "**", "*.wav"), recursive=True))
    return summary, {"participants_tsv": p.to_dict(orient="list")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("source", choices=["fau_tud", "federici", "dtu_snhl"])
    ap.add_argument("--align", action="store_true")
    a = ap.parse_args(argv)
    if a.source == "fau_tud":
        s, p = audit_fau_tud(a.align)
    elif a.source == "federici":
        s, p = audit_federici()
    else:
        s, p = audit_dtu()
    print("summary:", _dump(f"{a.source}_schema_summary_001.json", s))
    print("private:", _dump(f"{a.source}_schema_private_001.json", p))
    print(json.dumps(s, indent=1, default=str)[:20000])


if __name__ == "__main__":
    sys.exit(main())
