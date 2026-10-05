"""P0 signal preprocessing, stage A (c3_preproc_v1): deterministic, decision-free transforms only.

Applied identically to every group (no group-specific step):
  * drop aux rows (FAU/TUD); removed CI electrodes become NaN rows (never interpolated here);
  * zero-phase FIR band-pass within each physically continuous interval (FAU/TUD: a trial; DTU: the whole run),
    two bands: 1-8 Hz (main) and 1-20 Hz (sensitivity) (03 §3.7);
  * polyphase resampling to 128 Hz;
  * the recorded reference is kept (FAU/TUD: online Cz; DTU: Biosemi CMS); re-referencing, ICA and interpolation are
    linear/analysis decisions taken after G1.
FAU/TUD trials whose aux channels show a confident offset (r >= 0.3, |lag| > 5 ms; P0 audit) also get a realigned copy;
which copy is primary is frozen at G1. Stimulus envelopes get the same filter/resampling. No EEG quantity is computed,
except the pooled (all groups together) Federici spectrum used for the D2 bandwidth check.

Usage: python -m auditory_c3.preproc fau_tud <ha|ci|th> | dtu | federici | chanmap
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import sys

import numpy as np

ROOT = "/projects/EEG-foundation-model/auditory_public"
OUT = os.path.join(ROOT, "derived", "c3_preproc_v1")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECEIPTS = os.path.join(REPO, "private", "auditory_c3", "receipts")
FS_OUT = 128
BANDS = {"1_8": (1.0, 8.0), "1_20": (1.0, 20.0)}
LAG_SPAN_S = 0.8  # [-200, 600] ms
H5 = {"ha": "fau_tud/zenodo_17927767_ha/hi_dataset_1kHz.hdf5", "ci": "fau_tud/zenodo_17952844_ci/ci_dataset_1kHz.hdf5",
      "th": "fau_tud/zenodo_17952231_th/nh_dataset_1kHz.hdf5"}
FAU_CH = ["Fp1", "Fz", "F3", "F7", "F9", "FC5", "FC1", "C3", "T7", "TP9", "CP5", "CP1", "Pz", "P3", "P7", "O1", "Oz", "O2",
          "P4", "P8", "TP10", "CP6", "CP2", "C4", "T8", "F10", "FC6", "IO2", "F4", "F8", "Fp2"]  # vhdr Ch1-31; Aux1/2 = rows 32-33


def _code_sha():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


def _bp(x, fs, band):
    import mne
    return mne.filter.filter_data(x, sfreq=fs, l_freq=band[0], h_freq=band[1], method="fir", phase="zero",
                                  fir_design="firwin", pad="reflect_limited", verbose=False)


def _filter_len_s(fs, band):
    import mne
    h = mne.filter.create_filter(None, fs, band[0], band[1], method="fir", phase="zero", fir_design="firwin", verbose=False)
    return len(h) / fs


def _rs(x, fs_in):
    from fractions import Fraction
    from scipy.signal import resample_poly
    fr = Fraction(FS_OUT, int(fs_in)).limit_denominator(1000)
    return resample_poly(x, fr.numerator, fr.denominator, axis=-1)


def _guard(fs_in):
    return int(np.ceil((max(_filter_len_s(fs_in, b) for b in BANDS.values()) / 2 + LAG_SPAN_S) * FS_OUT))


def _open_out(path):
    import h5py
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    return h5py.File(tmp, "w"), tmp


def _close_out(f, tmp, path):
    f.close()
    os.replace(tmp, path)


# ----------------------------------------------------------------------------------------------------- FAU/TUD
def _alignment_table(grp):
    p = json.load(open(os.path.join(RECEIPTS, "fau_tud_schema_private_001.json")))[grp]["_alignment_rows"]
    out = {}
    for r in p:
        c = [v for k, v in r.items() if k.startswith("aux") and "attended" in k]
        b = max(c, key=lambda v: v["r"])
        out[(r["subject"], r["trial"])] = (int(b["lag_ms"]), float(b["r"]))
    return out


def fau_tud(grp):
    import h5py
    align = _alignment_table(grp)
    src = os.path.join(ROOT, H5[grp])
    guard = _guard(1000)
    flen = {b: _filter_len_s(1000, v) for b, v in BANDS.items()}
    log = {"group": grp, "subjects": {}, "code_sha256": _code_sha()}
    with h5py.File(src, "r") as f:
        for s in sorted(f["eeg"].keys()):
            path = os.path.join(OUT, "fau_tud", grp, f"{s}.h5")
            if os.path.exists(path):
                log["subjects"][s] = "present"; continue
            sg = f["eeg"][s]
            removed = [int(i) for i in np.atleast_1d(sg["taken_out_indices"][()])] if "taken_out_indices" in sg else []
            o, tmp = _open_out(path)
            o.attrs.update(source=H5[grp], subject=s, group=grp, fs=FS_OUT, channels=FAU_CH, reference="Cz (online, not in data)",
                           eog_channels=["IO2"], removed_rows=removed, guard_samples=guard, lag_span_s=LAG_SPAN_S,
                           filter="mne FIR firwin zero-phase, reflect_limited pad, per trial at 1 kHz; then resample_poly to 128 Hz",
                           filter_len_s=json.dumps(flen), code_sha256=_code_sha(), stage="c3_preproc_v1 stage A")
            rec = {"removed": removed, "removed_row_std": {}, "trials": {}}
            for t in sorted([k for k in sg.keys() if k.isdigit()], key=int):
                ds = sg[t]
                x = ds[:31, :].astype(np.float64)
                for r in removed:
                    rec["removed_row_std"][r] = float(np.std(x[r]))
                valid = [i for i in range(31) if i not in removed]
                lag, rr = align[(s, int(t))]
                realign = rr >= 0.3 and abs(lag) > 5
                g = o.create_group(f"trial_{int(t):02d}")
                code = ds.attrs["stimulus"]; code = code.decode() if isinstance(code, bytes) else str(code)
                g.attrs.update(stimulus=code, n_1k=x.shape[1], aux_lag_ms=lag, aux_r=rr, realigned_copy=realign)
                for bname, band in BANDS.items():
                    y = np.full_like(x, np.nan)
                    y[valid] = _bp(x[valid], 1000, band)
                    g.create_dataset(f"eeg_{bname}", data=_rs(y, 1000).astype(np.float32), compression="lzf")
                    if realign:
                        # aux(t) ~ env(t - lag): shift EEG so that sample k is aligned with stimulus sample k
                        z = np.zeros_like(y)
                        if lag > 0:
                            z[:, :-lag] = y[:, lag:]
                        else:
                            z[:, -lag:] = y[:, :lag]
                        z[removed] = np.nan
                        d = g.create_dataset(f"eeg_{bname}_realigned", data=_rs(z, 1000).astype(np.float32), compression="lzf")
                        d.attrs["extra_guard_samples"] = int(np.ceil(abs(lag) / 1000 * FS_OUT))
                rec["trials"][t] = {"n_1k": x.shape[1], "lag": lag, "r": rr, "realigned": realign}
            _close_out(o, tmp, path)
            log["subjects"][s] = rec
            print(grp, s, "trials", len(rec["trials"]), "removed", removed, "realigned", sum(v["realigned"] for v in rec["trials"].values()), flush=True)
    # stimulus envelopes (identical across groups; written once, from this group's file if absent)
    stim_path = os.path.join(OUT, "fau_tud", "stimulus_env_128.h5")
    if grp == "ha" and not os.path.exists(stim_path):  # one writer; the three group jobs run concurrently
        with h5py.File(src, "r") as f:
            o, tmp = _open_out(stim_path)
            o.attrs.update(fs=FS_OUT, source=H5[grp], code_sha256=_code_sha(), note="published 1 kHz envelopes; raw-resampled and band-passed copies")
            for code in sorted(f["stimulus_files"].keys()):
                for k in ("attended_env", "distractor_env", "attended_onset_env", "distractor_onset_env"):
                    e = np.asarray(f[f"stimulus_files/{code}/{k}"][()], float).ravel()
                    o.create_dataset(f"{code}/{k}/raw", data=_rs(e, 1000).astype(np.float32))
                    for bname, band in BANDS.items():
                        o.create_dataset(f"{code}/{k}/bp_{bname}", data=_rs(_bp(e[None], 1000, band)[0], 1000).astype(np.float32))
                    o[f"{code}/{k}"].attrs["n_1k"] = len(e)
            _close_out(o, tmp, stim_path)
    _write_log(f"fau_tud_{grp}", log)


def chanmap():
    """Confirm HDF5 row order == vhdr channel order using the example raw recordings (one per group)."""
    import h5py
    import mne
    out = {}
    for grp, sub, folder in (("ha", "201", "zenodo_17927767_ha/raw_hi/raw_hi"), ("ci", "102", "zenodo_17952844_ci/raw_ci/raw_ci"),
                             ("th", "301", "zenodo_17952231_th/raw_nh/raw_nh")):
        vhdr = os.path.join(ROOT, "fau_tud", folder, sub, f"{sub}.vhdr")
        if not os.path.exists(vhdr):
            out[grp] = {"error": "vhdr missing"}; continue
        raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose=False)
        R = raw.get_data()  # V
        with h5py.File(os.path.join(ROOT, H5[grp]), "r") as f:
            if sub not in f["eeg"]:
                out[grp] = {"error": f"subject {sub} not in HDF5"}; continue
            X = f[f"eeg/{sub}/1"][:31, :20000].astype(float)
        a = np.diff(X[1])  # Fz; first differences remove the DC offsets of DC-coupled recordings
        r = np.diff(R[1])
        n = 1 << (len(r) + len(a)).bit_length()
        c = np.fft.irfft(np.fft.rfft(r, n) * np.conj(np.fft.rfft(a, n)), n)[: len(r) - len(a)]
        off = int(np.argmax(np.abs(c)))
        seg = R[:31, off:off + X.shape[1]]
        C = np.corrcoef(np.vstack([np.diff(X, axis=1), np.diff(seg, axis=1)]))[:31, 31:]
        best = np.nanargmax(np.abs(C), axis=1)
        out[grp] = {"subject": sub, "raw_channels": raw.ch_names, "offset_samples": off,
                    "diag_abs_r_min": float(np.nanmin(np.abs(np.diag(C)))), "rows_matching_same_index": int(np.sum(best == np.arange(31))),
                    "scale_ratio_median": float(np.nanmedian(np.std(X, 1) / (np.std(seg, 1) + 1e-30)))}
        print(grp, json.dumps({k: v for k, v in out[grp].items() if k != "raw_channels"}), flush=True)
    _write_log("fau_tud_chanmap", out)


# ----------------------------------------------------------------------------------------------------- DTU
def dtu():
    import mne
    import pandas as pd
    import scipy.io as sio
    S = os.path.join(ROOT, "dtu_snhl", "ds-eeg-snhl", "ds-eeg-snhl")
    guard = _guard(512)
    log = {"subjects": {}, "code_sha256": _code_sha()}
    for bdf in sorted(glob.glob(os.path.join(S, "sub-*", "eeg", "*task-selectiveattention*_eeg.bdf"))):
        sub = re.search(r"(sub-\d+)", bdf).group(1)
        run = re.search(r"(run-\d+)", bdf)
        tag = sub + (f"_{run.group(1)}" if run else "")
        path = os.path.join(OUT, "dtu_snhl", f"{tag}.h5")
        if os.path.exists(path):
            log["subjects"][tag] = "present"; continue
        raw = mne.io.read_raw_bdf(bdf, preload=True, verbose=False)
        ch = pd.read_csv(bdf.replace("_eeg.bdf", "_channels.tsv"), sep="\t")
        eeg_names = [n for n, t in zip(ch["name"], ch["type"]) if str(t).upper() == "EEG"]
        eog_names = [n for n, t in zip(ch["name"], ch["type"]) if str(t).upper() == "EOG"]
        fs = raw.info["sfreq"]
        X = raw.get_data(picks=eeg_names + eog_names) * 1e6  # uV, recorded CMS reference
        ev = pd.read_csv(bdf.replace("_eeg.bdf", "_events.tsv"), sep="\t")
        on = ev[ev["trigger_type"] == "targetonset"].reset_index(drop=True)
        ends = ev[ev["trigger_type"].isin(["trialend", "error_terminated"])].reset_index(drop=True)
        mask = ev[ev["trigger_type"] == "maskeronset"]
        o, tmp = _open_out(path)
        o.attrs.update(subject=sub, source=os.path.relpath(bdf, ROOT), fs=FS_OUT, channels=eeg_names, eog_channels=eog_names,
                       reference="Biosemi CMS (recorded; not re-referenced)", guard_samples=guard, lag_span_s=LAG_SPAN_S,
                       filter="mne FIR firwin zero-phase over the continuous run; trials cut with 2 s margins then resample_poly",
                       code_sha256=_code_sha(), stage="c3_preproc_v1 stage A")
        Y = {b: _bp(X, fs, band) for b, band in BANDS.items()}
        margin = int(2 * fs)
        rec = []
        for i, row in on.iterrows():
            t0 = float(row["onset"])
            later = ends[ends["onset"] > t0]
            if later.empty:
                rec.append({"trial": i, "status": "no_end_event"}); continue
            t1 = float(later.iloc[0]["onset"])
            a, b = int(round(t0 * fs)), int(round(t1 * fs))
            lo, hi = max(0, a - margin), min(X.shape[1], b + margin)
            g = o.create_group(f"trial_{i + 1:03d}")
            for bname in BANDS:
                seg = _rs(Y[bname][:, lo:hi], fs)
                k0 = int(round((a - lo) / fs * FS_OUT)); k1 = k0 + int(round((b - a) / fs * FS_OUT))
                g.create_dataset(f"eeg_{bname}", data=seg[:, k0:k1].astype(np.float32), compression="lzf")
            m = mask[(mask["onset"] > t0) & (mask["onset"] < t1)]
            g.attrs.update(onset_s=t0, end_s=t1, end_type=str(later.iloc[0]["trigger_type"]), stim_file=str(row["stim_file"]),
                           attend_left_right=str(row["attend_left_right"]), talkers=str(row["single_talker_two_talker"]),
                           attend_male_female=str(row["attend_male_female"]), masker_onset_rel_s=float(m.iloc[0]["onset"] - t0) if len(m) else np.nan)
            # envelopes from derivatives (target / masker; CamEQ and 'woa' where present), on the trial's 128 Hz grid
            n128 = g[f"eeg_1_8"].shape[1]
            stim_rel = str(row["stim_file"]).replace(".wav", "")
            for kind, rel in (("target", stim_rel), ("masker", stim_rel.replace("/target/t", "/masker/m"))):
                for suffix in ("", "woa"):
                    mp = os.path.join(S, "derivatives", "stimuli", rel + suffix + ".mat")
                    if not os.path.exists(mp):
                        continue
                    d = sio.loadmat(mp, squeeze_me=True, struct_as_record=False)
                    st = [v for k, v in d.items() if not k.startswith("__")][0]
                    feat, efs, tt = np.asarray(st.feat, float).ravel(), float(st.fs), np.asarray(st.t, float).ravel()
                    grid = np.arange(n128) / FS_OUT
                    e = np.interp(grid, tt, feat, left=np.nan, right=np.nan)
                    dset = g.create_dataset(f"env_{kind}{'_' + suffix if suffix else ''}", data=e.astype(np.float32))
                    dset.attrs.update(source_fs=efs, source=os.path.relpath(mp, ROOT), t_first=float(tt[0]), t_last=float(tt[-1]))
            rec.append({"trial": i, "dur_s": t1 - t0, "talkers": str(row["single_talker_two_talker"])})
        _close_out(o, tmp, path)
        log["subjects"][tag] = {"n_trials": len(rec), "fs_in": fs, "n_eeg": len(eeg_names), "n_eog": len(eog_names)}
        print(tag, log["subjects"][tag], flush=True)
    _write_log("dtu_snhl", log)


# ----------------------------------------------------------------------------------------------------- Federici
def federici():
    import scipy.io as sio
    from scipy.signal import welch
    base = glob.glob(os.path.join(ROOT, "federici_ci_children", "mendeley_nzg5g2gzrd_v2", "files", "*", "Code"))[0]
    labels = None
    for c in sorted(glob.glob(os.path.join(base, "..", "**", "ChanlocsFinal.mat"), recursive=True)):
        d = sio.loadmat(c, squeeze_me=True, struct_as_record=False)
        v = [x for k, x in d.items() if not k.startswith("__")][0]
        labels = [str(getattr(e, "labels", "")) for e in np.atleast_1d(v)]
        label_src = os.path.relpath(c, base); break
    log = {"code_sha256": _code_sha(), "channel_labels": labels, "label_source": labels and label_src, "groups": {}}
    psd_h, psd_p, fpsd = [], [], None
    for g in ("02_HC_Encoding_model", "03_CI_Encoding_model", "04_HC-v_Encoding_model", "06_Artifact_Encoding_model"):
        n = 0
        for m in sorted(glob.glob(os.path.join(base, g, "Data", "EEG", "*", "*_preprocEEG_cut_ica.mat"))):
            pid = os.path.basename(m).replace("_preprocEEG_cut_ica.mat", "")
            envp = os.path.join(base, g, "Data", "StimulusEnvelope", f"{pid}AudioEnvSp.mat")
            path = os.path.join(OUT, "federici_ci_children", g.split("_")[1], f"{pid}.h5")
            eeg = sio.loadmat(m, squeeze_me=True)["CutEEG"]
            E = np.stack([np.asarray(s, float).T for s in np.atleast_1d(eeg)])  # (seg, ch, time)
            env = sio.loadmat(envp, squeeze_me=True)["AudioEnvSp"] if os.path.exists(envp) else None
            for seg in E:
                f_, p_ = welch(seg, fs=100, nperseg=512)
                fpsd = f_
                (psd_p if g.startswith("06") else psd_h).append(np.median(p_, axis=0))
            if not os.path.exists(path):
                o, tmp = _open_out(path)
                o.create_dataset("eeg", data=E.astype(np.float32), compression="lzf")
                if env is not None:
                    o.create_dataset("env", data=np.stack([np.asarray(s, float).ravel() for s in np.atleast_1d(env)]).astype(np.float32))
                o.attrs.update(participant=pid, folder=g, fs=100, source=os.path.relpath(m, ROOT), channels=labels or [],
                               note="authors' preprocessed data (2-8 Hz per paper, ICA); reformatted only, no further filtering",
                               code_sha256=_code_sha(), stage="c3_preproc_v1 stage A (reformat)")
                _close_out(o, tmp, path)
            n += 1
        log["groups"][g] = n
        print(g, n, flush=True)

    def edges(P):
        P = np.median(np.array(P), axis=0); ref = np.median(P[(fpsd >= 3) & (fpsd <= 7)])
        db = 10 * np.log10(P / ref)
        def first(cond, rng):
            idx = [i for i in rng if cond(db[i])]
            return float(fpsd[idx[0]]) if idx else None
        inband = [i for i in range(len(fpsd)) if 3 <= fpsd[i] <= 7]
        lo_rng = list(range(inband[0], -1, -1)); hi_rng = list(range(inband[-1], len(fpsd)))
        return {"minus3dB_low_hz": first(lambda v: v < -3, lo_rng), "minus3dB_high_hz": first(lambda v: v < -3, hi_rng),
                "minus20dB_low_hz": first(lambda v: v < -20, lo_rng), "minus20dB_high_hz": first(lambda v: v < -20, hi_rng),
                "db_at": {str(h): float(db[np.argmin(np.abs(fpsd - h))]) for h in (0.5, 1, 1.5, 2, 8, 9, 10, 12, 15, 20, 30, 40)}}
    log["d2_bandwidth_pooled_humans"] = edges(psd_h)  # HC + CI + HC-v pooled; no group split
    log["d2_bandwidth_phantom"] = edges(psd_p)
    print("D2 humans pooled:", json.dumps(log["d2_bandwidth_pooled_humans"]), flush=True)
    _write_log("federici", log)


def _write_log(name, obj):
    os.makedirs(os.path.join(OUT, "_logs"), exist_ok=True)
    p = os.path.join(OUT, "_logs", f"{name}.json")
    json.dump(obj, open(p, "w"), indent=1, default=str)
    print("log", p)


def main(argv=None):
    a = argv or sys.argv[1:]
    {"fau_tud": lambda: fau_tud(a[1]), "dtu": dtu, "federici": federici, "chanmap": chanmap}[a[0]]()


if __name__ == "__main__":
    main()
