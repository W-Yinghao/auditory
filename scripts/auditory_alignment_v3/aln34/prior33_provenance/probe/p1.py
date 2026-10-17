import sys, math
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch
torch.set_num_threads(1)
from auditory_alignment_v2.audio_targets import semi_orthogonal
from auditory_alignment_v2.temporal import build_encoder, describe, token_step, LOCAL_PATCH_MS
from auditory_alignment.losses_reference import cs_qmi
# 1. fixed projection
P = semi_orthogonal(32, 8, 20261016)
print("P shape", tuple(P.shape), "PtP-I max", float((P.T @ P - torch.eye(8)).abs().max()), "rank", int(torch.linalg.matrix_rank(P)))
print("P[:2,:4]", P[:2, :4].tolist())
# 2. lag_local_tokens at 64 Hz [0,38) vs 128 Hz [0,77)
for fs, L in ((64, 38), (128, 77), (100, 60), (250, 150)):
    enc = build_encoder("lag_local_tokens", 64, 32, [(0, L)], fs)
    br = enc.branches[0]
    print(f"fs={fs} L={L} token_step={token_step(fs)} w={br.w} n_tokens={enc.n_tokens} offs[:6]={br.offs[:6].tolist()} last={br.offs[-1].item()}", describe(enc))
print([n for n, _ in build_encoder("lag_local_tokens", 64, 32, [(0, 38)], 64).named_parameters()])
# 3. 20 ms query ticks at 64 Hz, cumulative rounding from origin (5 s segment = 320 samples)
k = np.arange(0, 250); ticks = np.round(k * 0.020 * 64).astype(int)
print("query ticks first 12", ticks[:12].tolist(), "steps", sorted(set(np.diff(ticks).tolist())), "n", len(ticks), "unique", len(set(ticks.tolist())), "max err ms", float(np.abs(ticks / 64 - k * 0.02).max() * 1000))
naive = np.cumsum(np.r_[0, np.full(249, int(round(0.020 * 64)))])
print("accumulated round(0.02*fs) drift after 5 s (ms)", float((naive[-1] / 64 - 249 * 0.02) * 1000))
# 4. CS full formula check vs direct A, B, C
g = torch.Generator().manual_seed(0)
u = torch.randn(64, 32, generator=g, dtype=torch.float64); v = u[:, :8] + 0.5 * torch.randn(64, 8, generator=g, dtype=torch.float64)
su, sv = 1.3, 0.9
val, st = cs_qmi(u, v, sigma_u=su, sigma_v=sv)
K = torch.exp(-torch.cdist(u, u) ** 2 / (2 * su ** 2)); Lm = torch.exp(-torch.cdist(v, v) ** 2 / (2 * sv ** 2)); n = 64
A = (K * Lm).sum() / n ** 2; B = (K.sum() / n ** 2) * (Lm.sum() / n ** 2); C = (K.sum(1) * Lm.sum(1)).sum() / n ** 3
print("cs_ref", float(val), "direct logA+logB-2logC", float(torch.log(A) + torch.log(B) - 2 * torch.log(C)))
