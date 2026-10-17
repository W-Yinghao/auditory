"""Synthetic check (no data): scipy.signal.resample_poly default anti-aliasing filter for each source rate -> 64 Hz,
plus the onset-phase of the 64 Hz grid for 250 Hz epochs with a 50-sample pre-stimulus segment."""
import json
import numpy as np
from scipy.signal import firwin, freqz, resample_poly
from fractions import Fraction
out = {}
for fs in (1000, 512, 250, 128, 100):
    fr = Fraction(64, fs); up, down = fr.numerator, fr.denominator
    mr = max(up, down); half = 10 * mr
    h = firwin(2 * half + 1, 1.0 / mr, window=("kaiser", 5.0))
    w, H = freqz(h, worN=1 << 16, fs=fs * up)
    db = 20 * np.log10(np.abs(H) + 1e-15)
    pick = {f: round(float(db[np.argmin(np.abs(w - f))]), 1) for f in (8, 20, 25, 28, 30, 32, 34, 36, 40, 45) if f < fs / 2}
    out[str(fs)] = {"up": up, "down": down, "taps": len(h), "half_support_ms": round(1000 * half / (fs * up), 1), "dB": pick}
# onset phase for the private epochs (-200..600 ms at 250 Hz; onset = sample 50)
x = np.zeros(200); x[50] = 1.0
y = resample_poly(x, 32, 125)
out["private_naive"] = {"n_out": len(y), "onset_output_position": 50 * 32 / 125, "nearest_output_sample_ms_after_onset": round(1000 * (13 * 125 / 32 - 50) / 250, 3)}
# onset-anchored: left-pad 75 samples so that onset sits at input 125 -> output 32
xp = np.r_[np.zeros(75), x]; yp = resample_poly(xp, 32, 125)
out["private_padded75"] = {"n_out": len(yp), "onset_output_index": int(np.argmax(yp)), "argmax_expected": 32,
                           "window_0_600ms_output_indices": [32, 32 + 38], "last_index_time_ms_after_onset": round(1000 * 37 / 64, 3)}
print(json.dumps(out, indent=1))
