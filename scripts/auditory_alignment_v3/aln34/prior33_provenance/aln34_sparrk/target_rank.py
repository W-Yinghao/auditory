"""Read-only: 2-8 Hz band-limited SparrKULee envelopes at 64 Hz -> 8-sample targets [i_k, i_k+8) on the 20 ms tick grid, one copy per
presentation (deduplicated over listeners). Eigen-spectrum of the 8x8 covariance; filter transient length; Butterworth vs FIR."""
import glob, os, json
import numpy as np
from scipy.signal import butter, sosfiltfilt, firwin, filtfilt, sosfilt
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_stimuli"
names = sorted(os.path.basename(p)[:-13] for p in glob.glob(f"{D}/*_envelope.npy") if "artefact" not in p)
sos = butter(4, [2, 8], btype="band", fs=64, output="sos")
fir = firwin(129, [2, 8], pass_zero=False, fs=64)  # 2 s linear-phase FIR, zero-phase via filtfilt
def targets(x, filt):
    y = sosfiltfilt(sos, x) if filt == "butter4_sosfiltfilt" else filtfilt(fir, [1.0], x)
    K = (50 * (len(y) - 8) + 24) // 64 + 3; i = (64 * np.arange(K) + 25) // 50; i = i[i + 8 <= len(y)]
    return y, np.stack([y[j:j + 8] for j in i])
out = {}
for filt in ("butter4_sosfiltfilt", "fir129_filtfilt"):
    Ys = []
    for k in names:
        x = np.load(f"{D}/{k}_envelope.npy", allow_pickle=False)[:, 0].astype(np.float64)
        _, Y = targets(x, filt); Ys.append(Y)
    Y = np.concatenate(Ys); mu = Y.mean(0); sd = Y.std(0); Z = (Y - mu) / sd
    ev = np.linalg.eigvalsh(np.cov(Z.T))[::-1]; frac = ev / ev.sum()
    out[filt] = {"n_ticks": int(len(Y)), "eig_frac": np.round(frac, 4).tolist(), "cum": np.round(np.cumsum(frac), 4).tolist(),
                 "participation_ratio": float(ev.sum() ** 2 / (ev ** 2).sum()), "per_dim_sd_raw": np.round(sd, 4).tolist(),
                 "lag1_autocorr": float(np.corrcoef(Z[:, 0], Z[:, 1])[0, 1])}
    print(filt, json.dumps(out[filt]))
# transient: impulse response of the zero-phase Butterworth (forward-backward) -> 99% energy half-width
imp = np.zeros(64 * 20); imp[len(imp) // 2] = 1; h = sosfiltfilt(sos, imp, padlen=0) if False else sosfilt(sos, sosfilt(sos, imp)[::-1])[::-1]
e = np.cumsum(h[len(h) // 2:] ** 2 + h[len(h) // 2::-1][:len(h) - len(h) // 2] ** 2); e /= e[-1]
print("butter4 2-8 Hz zero-phase impulse response: 99%% energy within +-%.3f s, 99.9%% within +-%.3f s" % (np.searchsorted(e, 0.99) / 64, np.searchsorted(e, 0.999) / 64))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "target_rank.json"), "w"), indent=1)
