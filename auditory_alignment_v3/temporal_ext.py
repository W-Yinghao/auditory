"""ALN3 A_LOCAL_FACTORS encoders (package docs/04): controls for lag_local_tokens. Delegates other names to ALN2.
  lag_local_capacity_control  lag_local_tokens with the local conv widened (16m -> 32m channels, m from a fixed grid) to
                              the multiplier whose parameter count is closest to density_tokens for the same windows / d;
                              locality and cross-lag weight sharing kept.
  local_unshared_control      one small encoder per lag offset (no sharing): per lag Linear(C*w -> r) -> GELU -> Linear(r ->
                              TOKEN_DIM), r chosen so the total parameter count is closest to lag_local_tokens.
Both record the actual parameter counts of themselves and of the reference architectures (describe_ext)."""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from auditory_alignment_v2 import temporal as T2

M_GRID = (1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0)


class LagLocalWide(T2.LagLocalBranch):
    def __init__(self, n_ch, L, step, w, m):
        super().__init__(n_ch, L, step, w)
        c1, c2 = int(round(16 * m)), int(round(32 * m)); w = self.w
        self.local = nn.Sequential(nn.Conv1d(n_ch, c1, 1), nn.Conv1d(c1, c2, min(3, w), padding=min(3, w) // 2), T2.ChannelLN(c2), nn.GELU())
        self.c2 = c2; self.tok = nn.Linear(c2, T2.TOKEN_DIM)

    def forward(self, x):
        B, C, L = x.shape
        idx = self.offs[:, None] + torch.arange(self.w, device=x.device)[None]
        p = x[:, :, idx].permute(0, 2, 1, 3).reshape(B * len(self.offs), C, self.w)
        h = self.local(p).mean(-1).reshape(B, len(self.offs), self.c2)
        return self.tok(h) + self.pos


class LagUnshared(T2.LagLocalBranch):
    def __init__(self, n_ch, L, step, w, r):
        super().__init__(n_ch, L, step, w)
        K, D = len(self.offs), n_ch * self.w
        del self.local, self.tok
        self.A = nn.Parameter(torch.randn(K, D, r) / D ** 0.5); self.a = nn.Parameter(torch.zeros(K, r))
        self.Bm = nn.Parameter(torch.randn(K, r, T2.TOKEN_DIM) / r ** 0.5); self.b = nn.Parameter(torch.zeros(K, T2.TOKEN_DIM))

    def forward(self, x):
        B, C, L = x.shape
        idx = self.offs[:, None] + torch.arange(self.w, device=x.device)[None]
        p = x[:, :, idx].permute(0, 2, 1, 3).reshape(B, len(self.offs), C * self.w)  # [B, K, C*w]
        h = F.gelu(torch.einsum("bkd,kdr->bkr", p, self.A) + self.a)
        return torch.einsum("bkr,kro->bko", h, self.Bm) + self.b + self.pos


class TokenEncoderExt(T2.TokenEncoder):
    def __init__(self, n_ch, d, windows, fs, make):
        nn.Module.__init__(self)
        step = T2.token_step(fs); w = max(2, int(round(T2.LOCAL_PATCH_MS * fs / 1000)))
        self.windows, self.kind = windows, "ext"
        self.branches = nn.ModuleList([make(b - a, step, w) for a, b in windows])
        self.n_tokens = sum(br.K for br in self.branches)
        self.proj = nn.Sequential(nn.LayerNorm(self.n_tokens * T2.TOKEN_DIM), nn.Linear(self.n_tokens * T2.TOKEN_DIM, d))


npar = lambda m: int(sum(p.numel() for p in m.parameters()))
LAST = {}


def build_encoder(architecture, n_ch, d, windows, fs):
    if architecture not in ("lag_local_capacity_control", "local_unshared_control"):
        return T2.build_encoder(architecture, n_ch, d, windows, fs)
    ref_density = npar(T2.TokenEncoder("density_tokens", n_ch, d, windows, fs))
    ref_lag = npar(T2.TokenEncoder("lag_local_tokens", n_ch, d, windows, fs))
    if architecture == "lag_local_capacity_control":
        cands = [(abs(npar(TokenEncoderExt(n_ch, d, windows, fs, lambda L, s, w, m=m: LagLocalWide(n_ch, L, s, w, m))) - ref_density), m) for m in M_GRID]
        m = min(cands)[1]; enc = TokenEncoderExt(n_ch, d, windows, fs, lambda L, s, w: LagLocalWide(n_ch, L, s, w, m)); knob = {"width_multiplier": m}
    else:
        cands = [(abs(npar(TokenEncoderExt(n_ch, d, windows, fs, lambda L, s, w, r=r: LagUnshared(n_ch, L, s, w, r))) - ref_lag), r) for r in range(1, 33)]
        r = min(cands)[1]; enc = TokenEncoderExt(n_ch, d, windows, fs, lambda L, s, w: LagUnshared(n_ch, L, s, w, r)); knob = {"per_lag_rank": r}
    LAST.clear(); LAST.update({"architecture": architecture, "n_params": npar(enc), "ref_density_tokens_params": ref_density, "ref_lag_local_tokens_params": ref_lag, **knob})
    return enc
