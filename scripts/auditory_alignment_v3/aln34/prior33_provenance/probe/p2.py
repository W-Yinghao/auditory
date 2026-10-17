"""Synthetic prototype checks (no data): name-indexed signed spatial map in front of the shared lag-local network;
multi-positive log-sum-exp NCE with +/-2 s same-content neighbour mask; cross-person CS rows."""
import sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
torch.set_num_threads(1); torch.manual_seed(0)
from auditory_alignment_v2.temporal import build_encoder
from auditory_alignment_v2.foundation_adapter import CHANNELS, ALIASES
from auditory_alignment.losses import deduplicated_infonce
from auditory_alignment.losses_reference import symmetric_infonce, cs_qmi

SPK = ["Fp1","AF7","AF3","F1","F3","F5","F7","FT7","FC5","FC3","FC1","C1","C3","C5","T7","TP7","CP5","CP3","CP1","P1","P3","P5","P7","P9","PO7","PO3","O1","Iz","Oz","POz","Pz","CPz","Fpz","Fp2","AF8","AF4","AFz","Fz","F2","F4","F6","F8","FT8","FC6","FC4","FC2","FCz","Cz","C2","C4","C6","T8","TP8","CP6","CP4","CP2","P2","P4","P6","P8","P10","PO8","PO4","O2"]
LAY = {"sparrkulee": SPK, **{k: [ALIASES.get(c, c) for c in v] for k, v in CHANNELS.items()}}
VOCAB = sorted(set().union(*map(set, LAY.values())))
print("vocab size", len(VOCAB), "outside SparrKULee", sorted(set(VOCAB) - set(SPK)))
DONORS = {"fau": ["sparrkulee", "dtu", "federici"], "dtu": ["sparrkulee", "fau", "federici"], "federici": ["sparrkulee", "fau", "dtu"],
          "private_bdf": ["sparrkulee", "fau", "dtu", "federici"]}
for t, ds in DONORS.items():
    seen = set().union(*(set(LAY[d]) for d in ds)); miss = [c for c in LAY[t] if c not in seen]
    print(f"target {t}: {len(LAY[t]) - len(miss)}/{len(LAY[t])} channels donor-seen; unseen {miss}")

class NameIndexedSpatial(nn.Module):
    def __init__(self, vocab, k=16):
        super().__init__(); self.vocab = list(vocab); self.W = nn.Parameter(torch.randn(len(vocab), k) / 8); self.b = nn.Parameter(torch.zeros(k))
        self.register_buffer("seen", torch.ones(len(vocab), dtype=torch.bool))
    def forward(self, x, idx, mask):  # x [B, C, L] in the cohort's order; idx [C] vocab rows; mask [C] float
        w = self.W[idx] * (mask * self.seen[idx].to(x.dtype))[:, None]
        return torch.einsum("bcl,ck->bkl", x, w) + self.b[None, :, None]

class SharedLocal(nn.Module):
    def __init__(self, vocab, d=32, fs=64, L=38):
        super().__init__(); self.sp = NameIndexedSpatial(vocab); self.enc = build_encoder("lag_local_tokens", 16, d, [(0, L)], fs)
        self.enc.branches[0].local[0] = nn.Identity()  # spatial map moved in front (pointwise in time -> identical algebra)
    def forward(self, patches, idx, mask):
        return self.enc([self.sp(patches[0], idx, mask)])

# (a) equivalence with the per-cohort Conv1d(n_ch,16,1) when the vocabulary rows equal the conv weights
ref = build_encoder("lag_local_tokens", 31, 32, [(0, 38)], 64); m = SharedLocal(VOCAB)
idx = torch.tensor([VOCAB.index(c) for c in LAY["fau"]])
with torch.no_grad():
    m.sp.W[idx] = ref.branches[0].local[0].weight[:, :, 0].T; m.sp.b.copy_(ref.branches[0].local[0].bias)
    sd = {k: v for k, v in ref.state_dict().items() if not k.startswith("branches.0.local.0.")}
    print("load shared (strict=False):", m.enc.load_state_dict(sd, strict=False))
x = torch.randn(5, 31, 38)
print("max |ref - name-indexed| =", float((ref([x]) - m([x], idx, torch.ones(31))).abs().max()))
# (b) donor-unseen rows: zero contribution and zero gradient
m.sp.seen[torch.tensor([VOCAB.index("F9"), VOCAB.index("F10")])] = False
x2 = x.clone(); x2[:, LAY["fau"].index("F9")] += 100.0
print("output change when an unseen channel changes:", float((m([x], idx, torch.ones(31)) - m([x2], idx, torch.ones(31))).abs().max()))
m.zero_grad(); m([x], idx, torch.ones(31)).sum().backward()
print("grad norm of unseen rows:", float(m.sp.W.grad[[VOCAB.index("F9"), VOCAB.index("F10")]].norm()), "| seen rows:", float(m.sp.W.grad[idx].norm()))

# (c) multi-positive log-sum-exp NCE with neighbour mask
def lse_nce(q, c, pos, excl, tau=0.1):
    """q [n,d], c [m,d]; pos/excl [n,m] bool. Loss_i = -(LSE_{p in pos} s_ip - LSE_{j not excl} s_ij); pos must not be excluded."""
    s = F.normalize(q.double(), dim=1) @ F.normalize(c.double(), dim=1).T / tau
    ninf = torch.tensor(float("-inf"), dtype=s.dtype)
    num = torch.logsumexp(torch.where(pos, s, ninf), 1); den = torch.logsumexp(torch.where(excl & ~pos, ninf, s), 1)
    return (den - num).mean()
n = 16; u = torch.randn(n, 32, dtype=torch.float64); v = u + 0.8 * torch.randn(n, 32, dtype=torch.float64)
eye = torch.eye(n, dtype=torch.bool); no = torch.zeros(n, n, dtype=torch.bool)
print("single positive: LSE-NCE", float((lse_nce(u, v, eye, no) + lse_nce(v, u, eye, no)) / 2), "== reference symmetric InfoNCE", float(symmetric_infonce(u, v, 0.1)))
keys = torch.tensor([0, 0, 1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])  # duplicated audio anchors
pos = keys[:, None] == keys[None]
print("duplicate keys: LSE-over-positives", float((lse_nce(u, v, pos, no) + lse_nce(v, u, pos.T, no)) / 2), "vs repo deduplicated_infonce (mean log-prob over positives)", float(deduplicated_infonce(u, v, keys, 0.1)))
content = torch.tensor([0] * 8 + [1] * 8); tick = torch.tensor(list(range(0, 320, 40)) * 2)  # 8 anchors 0.625 s apart per content (64 Hz)
nb = (content[:, None] == content[None]) & ((tick[:, None] - tick[None]).abs() <= 128) & ~eye
print("neighbour mask: masked per row", nb.sum(1).tolist(), "| loss masked", float(lse_nce(u, v, eye, nb)), "unmasked", float(lse_nce(u, v, eye, no)))

# (d) cross-person CS rows: (u_a, u_b) per anchor; both orderings stacked = symmetric empirical joint
ua = torch.randn(64, 32, dtype=torch.float64); ub = ua + 0.7 * torch.randn(64, 32, dtype=torch.float64)
med = lambda z: float(torch.cdist(z, z)[~torch.eye(len(z), dtype=torch.bool)].median())
val1, st1 = cs_qmi(ua, ub, sigma_u=med(ua), sigma_v=med(ub))
uu, vv = torch.cat([ua, ub]), torch.cat([ub, ua]); val2, st2 = cs_qmi(uu, vv, sigma_u=med(uu), sigma_v=med(vv))
val0, _ = cs_qmi(ua, ub[torch.randperm(64)], sigma_u=med(ua), sigma_v=med(ub))
print("cross-person CS: one ordering", round(float(val1), 5), "| both orderings", round(float(val2), 5), "| shuffled partner", round(float(val0), 5))
