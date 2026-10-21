"""ALN4.1 time bank: three native crops -> crop-only resampling to 200 Hz -> right pad to 200 -> one shared Stage1 backbone.

Windows W0=[-200,200), W1=[0,400), W2=[200,600) ms around the anchor (time_access.native_bounds: half-open, ceil
endpoints of native sample times). `resample` reproduces scipy.signal.resample (real FFT method, Nyquist halving when
up-sampling an even crop and doubling when down-sampling to an even length) on torch tensors; check_resampler() compares
it with scipy on the actual crop lengths. The wrapper owns resampling; the backbone is built with fs_native=200 so its own
resampler is the identity, and the backbone applies the asset amplitude scaling (CBraMod 0.15*z) exactly once.
Each crop is an independent single-patch forward (no cross-window context). Projections: one 32-d channel-aware
linear readout (LayerNorm per channel token, Linear(C*200 -> 32), L2) per audio view, shared by the three windows.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ..fm_aligned import AlignedPatchLinear
from . import time_access as TA

WINDOWS_MS = TA.WINDOWS_MS
TARGET_HZ, PAD_TO = 200, 200
VIEWS = ('env', 'ss', 'sc')


def layout(fs_native):
    """[(native_start, native_stop_exclusive, resampled_valid_n)] relative to the anchor sample."""
    out = []
    for w in WINDOWS_MS:
        d = TA.describe(w, fs_native, target_hz=TARGET_HZ, pad_to=PAD_TO)
        out.append((d['native_start'], d['native_stop_exclusive'], d['resampled_valid_n']))
    return out


def resample(x, num):
    """scipy.signal.resample(x, num, axis=-1) for real x, in torch (float64 internally)."""
    nx = x.shape[-1]
    X = torch.fft.rfft(x.to(torch.float64), dim=-1)
    Y = torch.zeros(*x.shape[:-1], num // 2 + 1, dtype=X.dtype, device=x.device)
    n = min(num, nx)
    nyq = n // 2 + 1
    Y[..., :nyq] = X[..., :nyq]
    if n % 2 == 0:
        if num < nx:
            Y[..., n // 2] *= 2.0
        elif nx < num:
            Y[..., n // 2] *= 0.5
    y = torch.fft.irfft(Y, n=num, dim=-1) * (float(num) / float(nx))
    return y.to(x.dtype if x.is_floating_point() else torch.float32)


def crop_inputs(crops, fs_native):
    """crops: list of 3 tensors [B, C, n_native_k] -> [3B, C, 200] (window-major), zero right padding after resampling."""
    lay = layout(fs_native)
    out = []
    for x, (a, b, n_out) in zip(crops, lay):
        assert x.shape[-1] == b - a, (x.shape, a, b)
        z = resample(x.float(), n_out)
        out.append(F.pad(z, (0, PAD_TO - n_out)))
    return torch.cat(out, 0)


class TimeBankModel(nn.Module):
    """Stage1 backbone + per-view shared projections; tokens() returns raw backbone tokens [B, 3, C, 200]."""

    def __init__(self, dataset_key, n_ch, fs_native, views=VIEWS, d=32, init_state=None):
        super().__init__()
        from auditory_alignment_v2.foundation_adapter import Backbone
        self.bb = Backbone('cbramod', dataset_key, 'pretrained_full', TARGET_HZ, init_state=init_state)
        assert len(self.bb.channel_names) == n_ch
        self.fs_native, self.n_ch = fs_native, n_ch
        self.heads = nn.ModuleDict({v: AlignedPatchLinear(n_ch, self.bb.E, d) for v in views})

    def tokens(self, crops):
        B = crops[0].shape[0]
        z = crop_inputs(crops, self.fs_native)
        h = self.bb(z)
        assert h.shape[2] == 1, h.shape
        return h[:, :, 0].reshape(3, B, self.n_ch, -1).transpose(0, 1)

    def project(self, tok, view):
        B = tok.shape[0]
        return self.heads[view](tok.flatten(0, 1)).reshape(B, 3, -1)

    def forward(self, crops, views=None):
        tok = self.tokens(crops)
        return {v: self.project(tok, v) for v in (views or self.heads.keys())}, tok


def check_resampler(fs_list=(64, 128, 250), trials=5, seed=0):
    """Max |torch - scipy| on random crops of the actual window lengths (float64)."""
    from scipy.signal import resample as sresample
    rng = np.random.default_rng(seed); report = []
    for fs in fs_list:
        for a, b, n_out in layout(fs):
            err = 0.0
            for _ in range(trials):
                x = rng.normal(size=(3, 7, b - a))
                ref = sresample(x, n_out, axis=-1)
                got = resample(torch.as_tensor(x), n_out).numpy()
                err = max(err, float(np.max(np.abs(ref - got))))
            report.append({'fs': fs, 'native_n': b - a, 'resampled_n': n_out, 'max_abs_error': err})
    return report
