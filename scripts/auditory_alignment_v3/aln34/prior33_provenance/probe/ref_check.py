"""Read-only: reference scheme check on public caches. ratio = std(sum over channels) / (sqrt(C) * median channel std):
~0 for an average reference (rows sum to zero), ~1 for independent channels, >1 for a shared common-mode (e.g. CMS)."""
import glob, json
import numpy as np, h5py
PUB = "/projects/EEG-foundation-model/auditory_public"
def ratio(X):
    X = X[np.isfinite(X).all(1)]
    s = X.sum(0); return float(np.std(s) / (np.sqrt(X.shape[0]) * np.median(X.std(1)) + 1e-30))
out = {}
p = sorted(glob.glob(f"{PUB}/derived/c3_preproc_v1/fau_tud_stageB/th/*.h5"))[0]
with h5py.File(p, "r") as f:
    t = sorted(f.keys())[0]; out["fau_stageB_ica_1_20"] = ratio(f[t]["eeg_1_20_ica"][()].astype(np.float64)[:, 400:8000])
p = sorted(glob.glob(f"{PUB}/derived/c3_preproc_v1/dtu_snhl/sub-0*.h5"))[0]
with h5py.File(p, "r") as f:
    t = sorted(f.keys())[0]; out["dtu_stageA_1_20_first64"] = ratio(f[t]["eeg_1_20"][()].astype(np.float64)[:64, 200:6000])
p = sorted(glob.glob(f"{PUB}/derived/c3_preproc_v1/federici_ci_children/HC/*.h5"))[0]
with h5py.File(p, "r") as f:
    out["federici_author_cache"] = ratio(f["eeg"][0].astype(np.float64))
S = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_eeg"
q = sorted(glob.glob(f"{S}/sub-002/*/*.npy"))[0]
x = np.load(q, mmap_mode="r", allow_pickle=False); out["sparrkulee_preprocessed"] = ratio(np.asarray(x[:, 640:640 + 64 * 120], np.float64))
out["sparrkulee_dtype_shape"] = [str(x.dtype), list(x.shape)]
print(json.dumps(out, indent=1))
