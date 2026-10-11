"""Lag grids and protocol windows (SCI_R1_PREREG §3, §6).

Token k of a lag_local_tokens branch over window [a, b) reads input samples [a + offs[k], a + offs[k] + w) relative to the
anchor (continuous) or to epoch sample 0 (private; stimulus onset at sample 50). Protocol windows map to the tokens whose
sample support lies entirely inside the window; they are fixed here and re-derived from the encoder in the engineering check.
"""
from __future__ import annotations

FS = {"fau": 128, "dtu": 128, "federici": 100, "private_bdf": 250}
N_CH = {"fau": 31, "dtu": 64, "federici": 32, "private_bdf": 20}
PRE = {"private_bdf": 50}  # epoch samples before stimulus onset
# protocol windows in ms (auditory_alignment.model.WINDOWS_MS; private relative to stimulus onset)
PROTOCOL_MS = {"fau": {"early": (0, 80), "late": (90, 300)}, "dtu": {"early": (0, 80), "late": (90, 300)},
               "federici": {"early": (0, 150), "late": (150, 600)}, "private_bdf": {"early": (120, 200), "late": (240, 320)}}
WINDOW_TOKENS = {"fau": {"early": [0, 1], "late": list(range(4, 12))}, "dtu": {"early": [0, 1], "late": list(range(4, 12))},
                 "federici": {"early": list(range(0, 6)), "late": list(range(8, 29))},
                 "private_bdf": {"early": [6, 7, 8], "late": [12, 13, 14]}}
# negative-lag raw controls: start offsets (samples) relative to the anchor / stimulus onset, same width and step as the tokens
NEG_OFFS = {"fau": list(range(-26, -4, 3)), "dtu": list(range(-26, -4, 3)), "federici": list(range(-20, -3, 2)),
            "private_bdf": list(range(-50, -9, 5))}


def window_samples(ds, win):
    """Half-open protocol window in samples relative to the anchor / stimulus onset (ALN2 rule: round(ms * fs / 1000))."""
    a, b = PROTOCOL_MS[ds][win]
    return int(round(a * FS[ds] / 1000)), int(round(b * FS[ds] / 1000))


WINDOW_TOKENS_INTERSECT = {"fau": {"early": [0, 1, 2, 3], "late": list(range(3, 13))}, "dtu": {"early": [0, 1, 2, 3], "late": list(range(3, 13))},
                           "federici": {"early": list(range(0, 8)), "late": list(range(6, 29))},
                           "private_bdf": {"early": list(range(5, 10)), "late": list(range(11, 16))}}


def tokens_touching_window(starts, w, ds, win):
    """Indices of tokens whose support intersects the protocol window (straddlers included)."""
    lo, hi = window_samples(ds, win)
    return [k for k, s in enumerate(starts) if s < hi and s + w > lo]


def tokens_in_window(starts, w, ds, win):
    """Indices of tokens (sample starts relative to the anchor / onset, width w) fully inside the protocol window."""
    lo, hi = window_samples(ds, win)
    return [k for k, s in enumerate(starts) if s >= lo and s + w <= hi]


def lag_table(starts, w, fs, target_frames=8):
    """Per-lag time labels: sample-access support [start, start + w) in samples and ms, and the stimulus-to-EEG lag span
    [start - (target_frames - 1), start + w - 1] samples implied by the 8-frame target window from the same anchor."""
    out = []
    for k, s in enumerate(starts):
        out.append({"k": k, "start": int(s), "stop": int(s + w), "start_ms": 1000.0 * s / fs, "stop_ms": 1000.0 * (s + w) / fs,
                    "centre_ms": 1000.0 * (s + (w - 1) / 2) / fs, "stim_lag_lo": int(s - (target_frames - 1)), "stim_lag_hi": int(s + w - 1)})
    return out


def branch_starts(enc, windows, rebase=0):
    """Token sample starts per branch: window start a + offs[k] (- rebase), and the patch width w."""
    out = []
    for br, (a, _) in zip(enc.branches, windows):
        out.append(([int(a + o - rebase) for o in br.offs.tolist()], int(br.w)))
    return out
