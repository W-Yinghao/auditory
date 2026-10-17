"""Read-only: spectral shape of the existing envelope sources (FAU author env, DTU Hilbert env, DTU dataset-derivative env,
SparrKULee preprocessed env). Welch PSD relative to the 3-7 Hz median; no EEG is read."""
import glob, json, os
import numpy as np, h5py
from scipy.signal import welch
PUB = "/projects/EEG-foundation-model/auditory_public"
def shape(xs, fs):
    P = []
    for x in xs:
        x = np.asarray(x, np.float64); x = x[np.isfinite(x)]
        if len(x) < 4 * fs: continue
        f, p = welch(x - x.mean(), fs=fs, nperseg=int(16 * fs)); P.append(p)
    P = np.median(np.array(P), 0); ref = np.median(P[(f >= 3) & (f <= 7)]); db = 10 * np.log10(P / ref + 1e-30)
    return {"n": len(xs), "fs": fs, "db_re_3_7Hz": {str(h): round(float(db[np.argmin(np.abs(f - h))]), 1) for h in (0.2, 0.5, 1, 2, 8, 10, 12, 16, 20, 30) if h < fs / 2}}
res = {}
with h5py.File(f"{PUB}/derived/c3_preproc_v1/fau_tud/stimulus_env_128.h5", "r") as h:
    codes = sorted(h.keys()); res["fau_stimulus_env_128_attrs"] = {k: str(v)[:200] for k, v in h.attrs.items()}
    res["fau_codes"] = codes
    xs = [h[f"{c}/attended_env/raw"][()] for c in codes]
    res["fau_author_env_raw_128"] = shape(xs, 128)
    res["fau_env_keys_example"] = sorted(h[codes[0]].keys())
with h5py.File(f"{PUB}/derived/c3_features_v1/dtu/kcs_targets_v1/audio_local.h5", "r") as h:
    ks = sorted(h.keys())[:40]
    res["dtu_hilbert_env_128"] = shape([h[f"{k}/env"][()] for k in ks], 128)
    res["dtu_audio_local_n_waveforms"] = len(h.keys())
fs_ = sorted(glob.glob(f"{PUB}/derived/c3_preproc_v1/dtu_snhl/*.h5"))[:2]
xs, xw = [], []
for p in fs_:
    with h5py.File(p, "r") as h:
        for k in sorted(h.keys())[:20]:
            g = h[k]
            if "env_target" in g: xs.append(g["env_target"][()])
            if "env_target_woa" in g: xw.append(g["env_target_woa"][()])
            res.setdefault("dtu_trial_env_attrs", {kk: str(vv)[:120] for kk, vv in g["env_target"].attrs.items()} if "env_target" in g else None)
            res.setdefault("dtu_trial_keys", sorted(g.keys()))
            res.setdefault("dtu_h5_attrs", {kk: str(vv)[:600] for kk, vv in h.attrs.items() if kk in ("channels", "eog_channels", "fs", "reference", "filter")})
res["dtu_dataset_derivative_env_on_128grid"] = shape(xs, 128)
if xw: res["dtu_dataset_derivative_env_woa_on_128grid"] = shape(xw, 128)
S = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_stimuli"
ps = sorted(glob.glob(f"{S}/*_envelope.npy"))[:20]
res["sparrkulee_env_64"] = shape([np.load(p, allow_pickle=False)[:, 0] for p in ps], 64)
print(json.dumps(res, indent=1))
