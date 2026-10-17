"""Read-only throughput probe: load 12 SparrKULee preprocessed EEG .npy files (allow_pickle=False), convert to float16, time it."""
import glob, time, numpy as np
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_eeg"
runs = sorted(glob.glob(f"{D}/sub-0[6-7]*/ses-*/*_eeg.npy"))[:12]
t0 = time.time(); nb = 0; ns = 0
for p in runs:
    a = np.load(p, allow_pickle=False); nb += a.nbytes; ns += a.shape[1]
    b = a.astype(np.float16); del a, b
dt = time.time() - t0
print(f"{len(runs)} files, {nb / 2**20:.0f} MiB float64 in {dt:.1f} s -> {nb / 2**20 / dt:.0f} MiB/s; samples {ns}; full 18.8 GB at this rate ~{18.8e9 / (nb / dt) / 60:.1f} min")
