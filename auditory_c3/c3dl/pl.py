"""C3-DL P-L (docs/auditory_c3/C3DL_PILOT_SPEC.md §2): conditional recovery of the frozen deep target L (Lz, 5 dims)
beyond the acoustic background m0(Ac), from 31-channel 1-20 Hz EEG. Data are organised as per-code stimulus streams
(shared by all participants) plus per-participant EEG streams, so the synthetic worlds in checks.py use the same path.

Arms: B0 (m0), B1 (m0 + ridge on EEG lags), D0 (EEG only), D1 (EEG + [m0, Ac] concatenated), D2 (m0 + correction),
D3 (D2 + InfoNCE, random negatives), D4 (D2 + InfoNCE, matched negatives).
"""
from __future__ import annotations

import json
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .core import Encoder, Head, LN2, Timer, candidate_scores, device, gaussian_evidence_bits, grad_param_norms, maha, nonfinite, set_seed

FEAT = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/fau_tud"
PRE = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/fau_tud_stageB"
FS, T, GUARD, D = 128, 640, 314, 5
M0_OFFSETS = np.arange(-128, 129, 2)
B1_LAGS = np.arange(0, 77, 4)
ALPHAS_M0 = np.logspace(-2, 6, 9)
ALPHAS_B1 = np.logspace(0, 6, 7)
AUX_NAMES = ("aux", "audio", "sound", "stim", "erg", "trig")


# ------------------------------------------------------------------------------------------------ real data loading
def _bp(x):
    import mne
    return mne.filter.filter_data(np.atleast_2d(x).astype(np.float64), FS, 1.0, 8.0, method="fir", phase="zero",
                                  fir_design="firwin", pad="reflect_limited", verbose=False)


TARGETS = {"z27": ("pca_k8_128hz_whisper_z27.h5", "layer_27"), "l27": ("pca_k8_128hz_whisper.h5", "layer_27")}
BACKGROUNDS = {"ac": ("pca_k8_128hz_whisper_shallow.h5", "shallow_01_02"), "mel": ("pca_k8_128hz_mel.h5", "logmel")}


def load_streams(target="z27", bg="ac"):
    """Single-speaker attended streams (codes 1xx): band-passed background (key "Ac": Whisper shallow PCA-5 or log-mel
    PCA-5) and target L (Lz = z-scored L27 PCA-5, or the frozen L27 PCA-5)."""
    import h5py
    (fb, kb), (ft, kt) = BACKGROUNDS[bg], TARGETS[target]
    out = {}
    with h5py.File(os.path.join(FEAT, fb), "r") as fa, h5py.File(os.path.join(FEAT, ft), "r") as fl:
        for c in sorted(k for k in fl.keys() if not k.startswith("_") and k.startswith("1")):
            Ac = _bp(fa[f"{c}/attended/{kb}"][()][:D]); L = _bp(fl[f"{c}/attended/{kt}"][()][:D])
            n = min(Ac.shape[1], L.shape[1])
            out[c] = {"Ac": Ac[:, :n].astype(np.float32), "L": L[:, :n].astype(np.float32), "story": c[1], "part": c[2], "n": n}
    return out


def load_eeg(grp, subj, stage_dir=None, dataset="eeg_1_20_ica", robust=False):
    """Single-speaker trials of stage B (default; ICA-cleaned 1-20 Hz), stage C (B + EOG removal) or stage M
    (minimal: dataset "eeg_min", robust=True). Scaling per channel over the recording: z-score, or (robust) median /
    1.4826 MAD then clamp to +-20 (C3DL_PROTOCOL_v1_FROZEN.md §7)."""
    import h5py
    with h5py.File(os.path.join(stage_dir or PRE, grp, f"{subj}.h5"), "r") as f:
        ch = [str(c) for c in f.attrs["channels"]]
        assert len(ch) == 31 and not any(a in c.lower() for c in ch for a in AUX_NAMES), ch
        X = {str(f[t].attrs["stimulus"]): f[t][dataset][()].astype(np.float64) for t in sorted(f.keys())
             if str(f[t].attrs["stimulus"]).startswith("1")}
    V = np.concatenate([x[:, GUARD:-GUARD] for x in X.values()], axis=1)
    if robust:
        mu = np.median(V, 1, keepdims=True); sd = 1.4826 * np.median(np.abs(V - mu), 1, keepdims=True); sd[sd == 0] = 1
        return {c: np.clip((x - mu) / sd, -20, 20).astype(np.float32) for c, x in X.items()}, ch
    mu, sd = V.mean(1, keepdims=True), V.std(1, keepdims=True); sd[sd == 0] = 1
    return {c: ((x - mu) / sd).astype(np.float32) for c, x in X.items()}, ch


# ------------------------------------------------------------------------------------------------ background m0
def _lagged(A, offsets, lo, hi):
    """Rows t in [lo, hi): features A[:, t + o] for o in offsets -> [hi - lo, A.shape[0] * len(offsets)]."""
    return np.concatenate([A[:, lo + o:hi + o].T for o in offsets], axis=1)


def fit_m0(streams, train_codes):
    """Ridge m0: L_t from Ac at t + offsets (+-1 s), fitted on train_codes only; alpha by leave-one-code-out.
    Returns m0 streams for every code, W = Sigma^{-1/2} of the training residual, and normalisation stats."""
    XtX, XtY, data = {}, {}, {}
    for c in train_codes:
        s = streams[c]
        Xc = _lagged(s["Ac"], M0_OFFSETS, GUARD, s["n"] - GUARD).astype(np.float64)
        Yc = s["L"][:, GUARD:s["n"] - GUARD].T.astype(np.float64)
        XtX[c], XtY[c], data[c] = Xc.T @ Xc, Xc.T @ Yc, (Xc, Yc)
    mx = np.concatenate([d[0] for d in data.values()]).mean(0)
    best = None
    for a in ALPHAS_M0:
        sse = 0.0
        for c in train_codes:
            A = sum(XtX[k] for k in train_codes if k != c); b = sum(XtY[k] for k in train_codes if k != c)
            Bc = np.linalg.solve(A + a * np.eye(len(A)), b)
            sse += float(((data[c][1] - data[c][0] @ Bc) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, a)
    alpha = best[1]
    Bm = np.linalg.solve(sum(XtX.values()) + alpha * np.eye(len(mx)), sum(XtY.values()))
    m0 = {}
    for c, s in streams.items():
        full = np.zeros_like(s["L"])
        lo, hi = 128, s["n"] - 128
        full[:, lo:hi] = (_lagged(s["Ac"], M0_OFFSETS, lo, hi) @ Bm).T
        m0[c] = full.astype(np.float32)
    R = np.concatenate([(streams[c]["L"] - m0[c])[:, GUARD:streams[c]["n"] - GUARD] for c in train_codes], axis=1)
    Sig = np.cov(R)
    w, V = np.linalg.eigh(Sig)
    W = (V @ np.diag(w ** -0.5) @ V.T).astype(np.float32)
    acs = np.concatenate([streams[c]["Ac"][:, GUARD:-GUARD] for c in train_codes], axis=1)
    m0s = np.concatenate([m0[c][:, GUARD:-GUARD] for c in train_codes], axis=1)
    norm = {"Ac": (acs.mean(1), acs.std(1)), "m0": (m0s.mean(1), m0s.std(1))}
    return m0, W, {"alpha": float(alpha), "sigma_eig": w.tolist()}, norm


# ------------------------------------------------------------------------------------------------ segments
def build_stim(streams, m0, codes, rf):
    """Stimulus segment table (shared across participants) for the given codes."""
    rows = []
    for c in codes:
        s = streams[c]
        for st in range(GUARD, s["n"] - GUARD - T + 1, T):
            A = s["Ac"][:, st:st + T]
            rows.append({"code": c, "story": s["story"], "part": s["part"], "start": st,
                         "L": s["L"][:, st:st + T], "Ac": A, "m0": m0[c][:, st:st + T], "feat": np.r_[A.mean(1), A.std(1)]})
    stim = {k: np.stack([r[k] for r in rows]) for k in ("L", "Ac", "m0", "feat", "start")}
    for k in ("code", "story", "part"):
        stim[k] = np.array([r[k] for r in rows])
    return stim


def subject_segments(stim, eeg, rf):
    """EEG windows [n, C, T + rf - 1] for the stimulus segments this participant has (window starts at the segment)."""
    idx, X = [], []
    for i, (c, st) in enumerate(zip(stim["code"], stim["start"])):
        x = eeg.get(c)
        if x is not None and st + T + rf - 1 <= x.shape[1]:
            idx.append(i); X.append(x[:, st:st + T + rf - 1])
    return np.array(idx), np.stack(X)


def matched_candidates(stim, pool, K, min_sep=None):
    """For each segment in pool: K nearest segments (z-scored Ac summary distance) of the same story and a different
    part; with min_sep (samples), also segments of the same code at least min_sep apart (no shared speech-model
    context window or EEG input)."""
    F_ = stim["feat"][pool]; F_ = (F_ - F_.mean(0)) / (F_.std(0) + 1e-12)
    out = {}
    for a, i in enumerate(pool):
        el = [b for b, j in enumerate(pool) if stim["story"][j] == stim["story"][i] and
              (stim["part"][j] != stim["part"][i] or
               (min_sep is not None and stim["code"][j] == stim["code"][i] and abs(int(stim["start"][j]) - int(stim["start"][i])) >= min_sep))]
        d = np.sqrt(((F_[el] - F_[a]) ** 2).sum(1))
        out[int(i)] = [int(pool[el[k]]) for k in np.argsort(d)[:K]]
    return out


def pools(stim, fit_parts=("1",), es_parts=("2",), test_parts=("3", "4")):
    """fit / es (early stopping, training participants) / seen = fit + es parts / unseen = test parts."""
    return {"fit": np.flatnonzero(np.isin(stim["part"], fit_parts)), "es": np.flatnonzero(np.isin(stim["part"], es_parts)),
            "seen": np.flatnonzero(np.isin(stim["part"], list(fit_parts) + list(es_parts))),
            "unseen": np.flatnonzero(np.isin(stim["part"], test_parts))}


def default_cfg(stim, P, norm, epochs=40):
    cfg = {"seed": 1, "lr": 1e-3, "wd": 1e-4, "bs": 32, "epochs": epochs, "K": 8, "tau": 1.0, "eta": 0.5, "norm": norm,
           "matched_fit": matched_candidates(stim, P["fit"], 8, min_sep=40 * FS),
           "matched_es": matched_candidates(stim, P["es"], 8, min_sep=40 * FS)}
    # D4 negatives need K candidates; the early-stopping pool only supplies the twin's top-1 swap partner
    for k, need in (("matched_fit", cfg["K"]), ("matched_es", 1)):
        short = [i for i, c in cfg[k].items() if len(c) < need]
        if short:
            raise ValueError(f"{k}: {len(short)} anchors have fewer than {need} candidates")
    cfg["n_es_anchors_lt_K"] = int(sum(len(c) < cfg["K"] for c in cfg["matched_es"].values()))
    return cfg


def random_candidates(stim, pool, i, K, rng):
    el = [j for j in pool if stim["code"][j] != stim["code"][i]]
    return [int(j) for j in rng.choice(el, K, replace=False)]


# ------------------------------------------------------------------------------------------------ models
class PLModel(nn.Module):
    """head="additive": g = MLP([Z, m0, Ac]); head="bilinear": g = MLP([Z, m0, Ac]) + W((U Z) * (V [m0, Ac]))."""

    def __init__(self, arm, n_ch, norm, head="additive"):
        super().__init__()
        self.arm, self.head_kind = arm, head
        self.enc = Encoder(n_ch)
        self.head = Head(self.enc.d_z + 2 * D, D)
        if head == "bilinear":
            self.bu = nn.Conv1d(self.enc.d_z, 16, 1); self.bv = nn.Conv1d(2 * D, 16, 1, bias=False)
            self.bw = nn.Conv1d(16, D, 1, bias=False); nn.init.zeros_(self.bw.weight)
        for k in ("Ac", "m0"):
            self.register_buffer(f"{k}_mu", torch.tensor(norm[k][0], dtype=torch.float32)[None, :, None])
            self.register_buffer(f"{k}_sd", torch.tensor(norm[k][1], dtype=torch.float32)[None, :, None])

    def forward(self, X, m0, Ac):
        if self.arm == "BG":  # background-only: same head as D2, EEG representation fixed at zero (encoder unused)
            Z = torch.zeros(m0.shape[0], self.enc.d_z, m0.shape[2], device=m0.device)
        else:
            Z = self.enc(X)
        mz = (m0 - self.m0_mu) / self.m0_sd; az = (Ac - self.Ac_mu) / self.Ac_sd
        if self.arm == "D0":
            mz, az = torch.zeros_like(mz), torch.zeros_like(az)
        out = self.head(torch.cat([Z, mz, az], 1))
        if self.head_kind == "bilinear":
            out = out + self.bw(self.bu(Z) * self.bv(torch.cat([mz, az], 1)))
        if self.arm in ("D2s", "D3s", "D4s"):  # two-stage: frozen strong background + EEG correction
            with torch.no_grad():
                base = self.bg(X, m0, Ac)
            return base + out
        return out if self.arm in ("D0", "D1") else m0 + out


class Bundle:
    """Everything a train/evaluate call needs, on device."""

    def __init__(self, stim, subj, W, dev):
        self.dev = dev
        self.L = torch.tensor(stim["L"], device=dev); self.Ac = torch.tensor(stim["Ac"], device=dev)
        self.m0 = torch.tensor(stim["m0"], device=dev); self.W = torch.tensor(W, device=dev)
        self.stim = stim
        self.subj = {s: (idx, torch.tensor(X, device=dev)) for s, (idx, X) in subj.items()}


def _pairs(B, subjects, pool):
    """All (subject, local row, stim index) triples whose stim index is in pool."""
    pool = set(int(p) for p in pool)
    return [(s, r, int(i)) for s in subjects for r, i in enumerate(B.subj[s][0]) if int(i) in pool]


def predict(model, B, triples, bs=64, swap=None):
    """Lhat for the given triples; swap maps stim index -> stim index whose EEG (same subject) replaces the anchor's."""
    out = []
    with torch.no_grad():
        for k in range(0, len(triples), bs):
            tr = triples[k:k + bs]
            X = []
            for s, r, i in tr:
                if swap is not None:
                    j = swap[i]; rr = int(np.flatnonzero(B.subj[s][0] == j)[0]); X.append(B.subj[s][1][rr])
                else:
                    X.append(B.subj[s][1][r])
            ii = torch.tensor([t[2] for t in tr], device=B.dev)
            out.append(model(torch.stack(X), B.m0[ii], B.Ac[ii]))
    return torch.cat(out)


def train_arm(arm, B, train_subj, fit_pool, es_pool, cfg, log, twin=False):
    """Fit on train_subj x fit_pool; early stopping on the natural loss over train_subj x es_pool (held-out content,
    never test participants); the best epoch's weights are restored. twin=True: null twin, the EEG of every training
    and early-stopping segment is replaced by that of the participant's top-1 Ac-matched segment."""
    set_seed(cfg["seed"])
    rng = np.random.default_rng(cfg["seed"])
    n_ch = next(iter(B.subj.values()))[1].shape[1]
    model = PLModel(arm, n_ch, cfg["norm"], head=cfg.get("head", "additive")).to(B.dev)
    if arm in ("D2s", "D3s", "D4s"):
        # frozen strong background: set without nn.Module registration, so it is excluded from parameters(),
        # the optimiser and state_dict
        object.__setattr__(model, "bg", cfg["bg_model"])
        assert not any(p is q for p in model.parameters() for q in cfg["bg_model"].parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    tr = _pairs(B, train_subj, fit_pool); es = _pairs(B, train_subj, es_pool)
    matched = cfg["matched_fit"]
    es_swap = {i: c[0] for i, c in cfg["matched_es"].items()} if twin else None
    if twin:
        loc = {s: {int(i): r for r, i in enumerate(B.subj[s][0])} for s in train_subj}
        tr = [(s, loc[s][matched[i][0]], i) for s, r, i in tr]
    ies = torch.tensor([t[2] for t in es], device=B.dev)
    best = (np.inf, -1, None)
    for ep in range(cfg["epochs"]):
        model.train()
        perm = rng.permutation(len(tr)); stats = {"nat": [], "con": [], "gn": []}
        for k in range(0, len(perm), cfg["bs"]):
            bt = [tr[j] for j in perm[k:k + cfg["bs"]]]
            X = torch.stack([B.subj[s][1][r] for s, r, _ in bt]); ii_ = [i for _, _, i in bt]; ii = torch.tensor(ii_, device=B.dev)
            Lhat = model(X, B.m0[ii], B.Ac[ii])
            nat = maha(B.L[ii] - Lhat, B.W).mean() / 2
            loss = nat
            if arm in ("D3", "D3s", "D4", "D4s"):
                if arm == "D4":  # conditional negatives relative to m0: m0_i + residual of an Ac-matched segment
                    Lc = conditional_candidates(B, ii_, [matched[i] for i in ii_])
                elif arm == "D4s":  # conditional negatives relative to the strong background: BG_i + (L_j - BG_j)
                    Lc = conditional_candidates(B, ii_, [matched[i] for i in ii_], base="bg")
                else:  # D3 / D3s: ordinary random pairing (whole other segments)
                    cand = torch.tensor([[i] + random_candidates(B.stim, fit_pool, i, cfg["K"], rng) for i in ii_], device=B.dev)
                    Lc = B.L[cand]
                sc = candidate_scores(Lc, Lhat, B.W) / cfg["tau"]
                con = F.cross_entropy(sc, torch.zeros(len(bt), dtype=torch.long, device=B.dev))
                loss = nat + cfg["eta"] * con; stats["con"].append(float(con))
            opt.zero_grad(); loss.backward()
            gn, _ = grad_param_norms(model)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
            stats["nat"].append(float(nat)); stats["gn"].append(gn)
        model.eval()
        with torch.no_grad():
            Lv = predict(model, B, es, swap=es_swap)
            vnat = float(maha(B.L[ies] - Lv, B.W).mean() / 2)
        if vnat < best[0]:
            best = (vnat, ep, {k: v.detach().clone() for k, v in model.state_dict().items()})
        model.train()
        assert model.training
        _, pn = grad_param_norms(model)
        log.append({"arm": arm + ("_twin" if twin else ""), "epoch": ep, "train_nat": float(np.mean(stats["nat"])),
                    "train_con": float(np.mean(stats["con"])) if stats["con"] else None, "es_nat": vnat,
                    "grad_norm_mean": float(np.mean(stats["gn"])), "param_norm": pn, "nonfinite": nonfinite(model),
                    "mode_after_val": "train" if model.training else "eval"})
    model.load_state_dict(best[2]); model.eval()
    model.best_epoch = best[1]
    return model


def train_bg(B, fit_pool, es_pool, cfg, max_epochs=3000, patience=200):
    """Strong background (no EEG) on the unique stimulus segments of fit_pool; early stopping on es_pool; stores the
    frozen model's predictions for every stimulus segment in B.bgL."""
    set_seed(cfg["seed"]); rng = np.random.default_rng(cfg["seed"])
    model = PLModel("BG", 1, cfg["norm"], head=cfg.get("head", "additive")).to(B.dev)
    opt = torch.optim.AdamW([p for n, p in model.named_parameters() if not n.startswith("enc.")], lr=cfg["lr"], weight_decay=cfg["wd"])
    fit = np.array(sorted(fit_pool)); es = torch.tensor(sorted(es_pool), device=B.dev)
    best, bad, hist = (np.inf, -1, None), 0, []
    for ep in range(max_epochs):
        model.train()
        perm = rng.permutation(fit)
        for k in range(0, len(perm), cfg["bs"]):
            ii = torch.tensor(perm[k:k + cfg["bs"]], device=B.dev)
            Lhat = model(None, B.m0[ii], B.Ac[ii])
            loss = maha(B.L[ii] - Lhat, B.W).mean() / 2
            opt.zero_grad(); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            v = float(maha(B.L[es] - model(None, B.m0[es], B.Ac[es]), B.W).mean() / 2)
        hist.append(v)
        if v < best[0] - 1e-7:
            best, bad = (v, ep, {k: t.detach().clone() for k, t in model.state_dict().items()}), 0
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(best[2]); model.eval(); model.best_epoch = best[1]; model.es_history = hist
    with torch.no_grad():
        B.bgL = torch.cat([model(None, B.m0[k:k + 256], B.Ac[k:k + 256]) for k in range(0, B.L.shape[0], 256)])
    return model


def conditional_candidates(B, anchors, negs, base="m0"):
    """[B, K+1, D, T]: positive L_i, then base_i + (L_j - base_j) for each matched j (background identical to the
    anchor's); base = m0 (linear) or bg (the frozen strong background's predictions, B.bgL)."""
    a = torch.tensor(anchors, device=B.dev); n = torch.tensor(negs, device=B.dev)
    bs = B.m0 if base == "m0" else B.bgL
    neg = bs[a][:, None] + (B.L[n] - bs[n])
    return torch.cat([B.L[a][:, None], neg], 1)


class FixedPred:
    """B0 / B1 as a callable with the model interface."""

    def __init__(self, B, kind, b1=None):
        self.B, self.kind, self.b1 = B, kind, b1

    def __call__(self, X, m0, Ac):
        if self.kind == "B0":
            return m0
        Bw, Winv = self.b1
        F_ = torch.cat([X[:, :, l:l + T] for l in B1_LAGS], 1)  # [B, C*nl, T]
        return m0 + torch.einsum("ed,bdt->bet", Winv, torch.einsum("df,bft->bdt", Bw, F_))

    def eval(self):
        return self


def fit_b1(B, train_subj, train_pool):
    """Ridge from EEG lags (0-600 ms, every 4th sample) to the whitened residual W (L - m0); alpha by leave-one-subject-out."""
    acc = {}
    for s in train_subj:
        tr = _pairs(B, [s], train_pool)
        XtX = XtY = YtY = 0
        for k in range(0, len(tr), 16):
            bt = tr[k:k + 16]
            X = torch.stack([B.subj[s][1][r] for _, r, _ in bt]).double(); ii = torch.tensor([i for _, _, i in bt], device=B.dev)
            F_ = torch.cat([X[:, :, l:l + T] for l in B1_LAGS], 1).permute(0, 2, 1).reshape(-1, X.shape[1] * len(B1_LAGS))
            Y = torch.einsum("ed,bdt->bte", B.W.double(), (B.L[ii] - B.m0[ii]).double()).reshape(-1, D)
            XtX = XtX + F_.T @ F_; XtY = XtY + F_.T @ Y; YtY = YtY + (Y * Y).sum()
        acc[s] = (XtX, XtY, YtY)
    tot = [sum(a[k] for a in acc.values()) for k in range(3)]
    I = torch.eye(tot[0].shape[0], device=B.dev, dtype=torch.float64)
    best = None
    for a in ALPHAS_B1:
        sse = 0.0
        for s, (xx, xy, yy) in acc.items():
            Bs = torch.linalg.solve(tot[0] - xx + a * I, tot[1] - xy)
            sse += float(yy - 2 * (Bs * xy).sum() + (Bs * (xx @ Bs)).sum())
        if best is None or sse < best[0]:
            best = (sse, a)
    Bw = torch.linalg.solve(tot[0] + best[1] * I, tot[1]).float().T  # [D, C*nl]
    Winv = torch.linalg.inv(B.W)
    return (Bw, Winv), float(best[1])


def evaluate(model, B, subjects, pool, K, twin=False, min_sep=None):
    """Natural-distribution evidence, nMSE, matched retrieval and conditional-mismatch EEG on (subjects x pool).
    twin=True: the model is a null twin and is scored on mismatched EEG throughout (as it was trained)."""
    model.eval()
    matched = matched_candidates(B.stim, np.array(sorted(pool)), K, min_sep=min_sep)
    swap = {i: c[0] for i, c in matched.items()}  # every anchor needs >= 1 candidate (asserted below)
    assert all(len(c) >= 1 for c in matched.values())
    per = {}
    for s in subjects:
        tri = _pairs(B, [s], pool)
        ii = torch.tensor([t[2] for t in tri], device=B.dev)
        Lh = predict(model, B, tri, swap=swap if twin else None); Lm = predict(model, B, tri, swap=swap)
        e = gaussian_evidence_bits(B.L[ii], B.m0[ii], Lh, B.W).mean(1)
        e_mm = gaussian_evidence_bits(B.L[ii], B.m0[ii], Lm, B.W).mean(1)
        nmse = float(((B.L[ii] - Lh) ** 2).sum() / ((B.L[ii] - B.m0[ii]) ** 2).sum())
        full = [n for n, t in enumerate(tri) if len(matched[t[2]]) == K]  # retrieval only on anchors with K candidates
        trf = [tri[n] for n in full]; Lr = Lh[full]
        zero = torch.zeros(len(trf), dtype=torch.long, device=B.dev)
        cand = torch.tensor([[t[2]] + matched[t[2]] for t in trf], device=B.dev)
        sc = candidate_scores(B.L[cand], Lr, B.W)
        scc = candidate_scores(conditional_candidates(B, [t[2] for t in trf], [matched[t[2]] for t in trf]), Lr, B.W)
        ll = F.cross_entropy(sc, zero, reduction="none") / LN2
        llc = F.cross_entropy(scc, zero, reduction="none") / LN2
        if getattr(B, "bgL", None) is not None:
            scb = candidate_scores(conditional_candidates(B, [t[2] for t in trf], [matched[t[2]] for t in trf], base="bg"), Lr, B.W)
            llb = F.cross_entropy(scb, zero, reduction="none") / LN2
            bgx = {"retrieval_condbg_logloss_bits": float(llb.mean()), "retrieval_condbg_top1": float((scb.argmax(1) == 0).float().mean())}
        else:
            bgx = {}
        per[s] = {"e_bits_per_sample": float(e.mean()), "e_mismatch": float(e_mm.mean()), "nmse_vs_m0": nmse,
                  "retrieval_segments_logloss_bits": float(ll.mean()), "retrieval_segments_top1": float((sc.argmax(1) == 0).float().mean()),
                  "retrieval_conditional_logloss_bits": float(llc.mean()), "retrieval_conditional_top1": float((scc.argmax(1) == 0).float().mean()),
                  **bgx, "n_seg": len(tri), "n_retrieval_anchors": len(trf)}
    agg = {k: float(np.mean([v[k] for v in per.values()])) for k in next(iter(per.values())) if k not in ("n_seg", "n_retrieval_anchors")}
    return {"mean_over_subjects": agg, "per_subject": per}


# ------------------------------------------------------------------------------------------------ CLIP-style (§7)
class CLIPModel(nn.Module):
    """Unconditional EEG <-> target contrast: flattened 5 s embeddings, symmetric in-batch InfoNCE."""

    def __init__(self, n_ch, mu, sd, d=16):
        super().__init__()
        self.enc = Encoder(n_ch); self.pe = nn.Conv1d(self.enc.d_z, d, 1)
        self.tg = nn.Sequential(nn.Conv1d(D, 32, 9, padding=4), nn.GELU(), nn.Conv1d(32, d, 1))
        self.register_buffer("mu", torch.tensor(mu, dtype=torch.float32)[None, :, None])
        self.register_buffer("sd", torch.tensor(sd, dtype=torch.float32)[None, :, None])

    def emb_eeg(self, X):
        return F.normalize(self.pe(self.enc(X)).flatten(1), dim=1)

    def emb_tgt(self, Y):
        return F.normalize(self.tg((Y - self.mu) / self.sd).flatten(1), dim=1)


def _unique_batches(items, bs, rng):
    """Batches without repeated stimulus segments (no false negatives from other participants)."""
    pending = [items[i] for i in rng.permutation(len(items))]
    while pending:
        batch, used, rest = [], set(), []
        for it in pending:
            if len(batch) < bs and it[2] not in used:
                batch.append(it); used.add(it[2])
            else:
                rest.append(it)
        yield batch
        pending = rest


def _clip_loss(model, B, batch, Y, tau):
    X = torch.stack([B.subj[s][1][r] for s, r, _ in batch]); ii = torch.tensor([i for _, _, i in batch], device=B.dev)
    sim = model.emb_eeg(X) @ model.emb_tgt(Y[ii]).t() / tau
    lab = torch.arange(len(batch), device=B.dev)
    return (F.cross_entropy(sim, lab) + F.cross_entropy(sim.t(), lab)) / 2


def train_clip(B, train_subj, fit_pool, es_pool, cfg, target, log, tau=0.1, max_epochs=40):
    set_seed(cfg["seed"]); rng = np.random.default_rng(cfg["seed"])
    Y = B.L if target == "L" else B.Ac
    fp = torch.tensor(sorted(fit_pool), device=B.dev)
    mu = Y[fp].mean((0, 2)).cpu().numpy(); sd = Y[fp].std((0, 2)).cpu().numpy()
    n_ch = next(iter(B.subj.values()))[1].shape[1]
    model = CLIPModel(n_ch, mu, sd).to(B.dev)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    tr = _pairs(B, train_subj, fit_pool); es = _pairs(B, train_subj, es_pool)
    es_batches = list(_unique_batches(es, cfg["bs"], np.random.default_rng(0)))
    best = (np.inf, -1, None)
    for ep in range(max_epochs):
        model.train(); ls, gns = [], []
        for batch in _unique_batches(tr, cfg["bs"], rng):
            if len(batch) < 2:
                continue
            loss = _clip_loss(model, B, batch, Y, tau)
            opt.zero_grad(); loss.backward(); gn, _ = grad_param_norms(model)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step(); ls.append(float(loss)); gns.append(gn)
        model.eval()
        with torch.no_grad():
            v = float(np.mean([float(_clip_loss(model, B, b, Y, tau)) for b in es_batches if len(b) >= 2]))
        if v < best[0]:
            best = (v, ep, {k: t.detach().clone() for k, t in model.state_dict().items()})
        model.train(); assert model.training
        log.append({"arm": f"CLIP_{target}", "epoch": ep, "train_nat": float(np.mean(ls)), "train_con": None, "es_nat": v,
                    "grad_norm_mean": float(np.mean(gns)), "param_norm": grad_param_norms(model)[1], "nonfinite": nonfinite(model),
                    "mode_after_val": "train" if model.training else "eval"})
    model.load_state_dict(best[2]); model.eval(); model.best_epoch = best[1]
    return model


def evaluate_clip(model, B, subjects, pool, target, K=8):
    """Identification among all segments of the test pool (top-1, top-5, mean rank percentile); for target L also
    top-1 among K conditional candidates BG_i + (L_j - BG_j) of Ac-matched segments (chance 1/(K+1))."""
    model.eval()
    Y = B.L if target == "L" else B.Ac
    pool = np.array(sorted(pool)); col = {int(i): c for c, i in enumerate(pool)}
    matched = matched_candidates(B.stim, pool, K) if target == "L" else None
    per = {}
    with torch.no_grad():
        T_ = torch.cat([model.emb_tgt(Y[torch.tensor(pool[k:k + 128], device=B.dev)]) for k in range(0, len(pool), 128)])
        for s in subjects:
            tri = _pairs(B, [s], pool)
            E = torch.cat([model.emb_eeg(torch.stack([B.subj[s][1][r] for _, r, _ in tri[k:k + 64]])) for k in range(0, len(tri), 64)])
            sim = E @ T_.t()
            own = torch.tensor([col[t[2]] for t in tri], device=B.dev)
            rank = (sim > sim[torch.arange(len(tri)), own][:, None]).sum(1).float()
            r = {"top1": float((rank == 0).float().mean()), "top5": float((rank < 5).float().mean()),
                 "rank_pct": float((rank / (len(pool) - 1)).mean()), "n_candidates": int(len(pool)), "n_seg": len(tri)}
            if target == "L" and getattr(B, "bgL", None) is not None:
                full = [t for t in tri if len(matched[t[2]]) == K]
                if full:
                    Lc = conditional_candidates(B, [t[2] for t in full], [matched[t[2]] for t in full], base="bg")
                    Ec = torch.cat([model.emb_eeg(torch.stack([B.subj[s][1][r] for _, r, _ in full[k:k + 64]])) for k in range(0, len(full), 64)])
                    Tc = model.emb_tgt(Lc.flatten(0, 1)).view(len(full), K + 1, -1)
                    sc = torch.einsum("bd,bkd->bk", Ec, Tc)
                    r["cond_top1"] = float((sc.argmax(1) == 0).float().mean())
            per[s] = r
    keys = [k for k in next(iter(per.values())) if k not in ("n_candidates", "n_seg")]
    return {"mean_over_subjects": {k: float(np.mean([v[k] for v in per.values() if k in v])) for k in keys}, "per_subject": per}
