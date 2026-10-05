"""C3-DL H-Cur (docs/auditory_c3/C3DL_PILOT_SPEC.md §3): current-sound (standard/deviant) evidence beyond the fixed
history background b(h), from single-trial 20-channel EEG (GX_stage_001 accepted epochs, -200..600 ms, 250 Hz).

Arms: B0 (b(h)), B1 (b(h) + logistic on the frozen GX evidence), D0 (EEG only), D1 (EEG + history one-hot),
D2 (b(h) + correction r([z, h])), D3 (D2 + supervised contrast, any history), D4 (D2 + supervised contrast within
the same record, same history bin, different physical block).
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

from .core import LN2, Encoder, Proj, device, grad_param_norms, nonfinite, set_seed, supcon

N_BINS = 6


def load_children():
    from ..private_mi import P, lane_bank, seed_avg_evidence
    from ..private_mi2 import hist_codes
    rec, bank = lane_bank("bdf_puretone", accepted_only=True)
    pf = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "records.csv"))
    ch = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "children.csv"))
    assert list(rec.record_id) == list(pf.record_id)
    ev, _ = seed_avg_evidence("GX1_bdf_puretone_shared", len(bank["y"]))
    H = hist_codes(bank["pc"], bank["prl"])
    kids = []
    for _, c in ch.iterrows():
        grp = "HA" if (c.group == "labelled" and bool(c.eligible)) else ("NH" if (c.group == "nh" and bool(c.nh_eligible)) else None)
        if grp is None:
            continue
        rid = pf.record_id[int(c.primary_rec)]
        m = bank["rec"] == int(c.primary_rec)
        with np.load(os.path.join(P, "auditory_gx", "GX_stage_001", "epochs", f"{rid}.npz")) as s:
            acc = s["accepted"].astype(bool)
            x = s["x"][acc].astype(np.float32); blk = s["block_id"][acc]; yy = s["y"][acc]
        assert len(x) == int(m.sum()) and np.array_equal(yy, bank["y"][m])
        ok = H["since_last_deviant"][m] >= 0
        x = x[ok]
        mu = x.mean(axis=(0, 2), keepdims=True); sd = x.std(axis=(0, 2), keepdims=True); sd[sd == 0] = 1
        kids.append({"id": f"child{int(c.child)}", "group": grp, "rid": rid, "x": (x - mu) / sd, "y": bank["y"][m][ok].astype(np.int64),
                     "bin": H["since_last_deviant"][m][ok].astype(np.int64), "block": blk[ok].astype(np.int64), "ev": ev[m][ok].astype(np.float32)})
    return kids


def folds(kids, seed=20261005, n=5):
    rng = np.random.default_rng(seed); f = {}
    for g in sorted({k["group"] for k in kids}):
        ids = [k["id"] for k in kids if k["group"] == g]
        for p, i in enumerate(rng.permutation(len(ids))):
            f[ids[i]] = p % n
    return f


def inner_split(kids, seed, frac=0.2):
    rng = np.random.default_rng(seed); val = set()
    for g in sorted({k["group"] for k in kids}):
        ids = sorted(k["id"] for k in kids if k["group"] == g)
        nv = max(1, int(np.ceil(frac * len(ids))))
        val |= set(np.array(ids)[rng.permutation(len(ids))[:nv]].tolist())
    return [k for k in kids if k["id"] not in val], [k for k in kids if k["id"] in val]


def q0_table(train):
    y = np.concatenate([k["y"] for k in train]); b = np.concatenate([k["bin"] for k in train])
    return np.array([(y[b == h].sum() + 0.5) / ((b == h).sum() + 1.0) for h in range(N_BINS)])


def _logit(p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return np.log(p / (1 - p))


class HCModel(nn.Module):
    def __init__(self, arm, n_ch):
        super().__init__()
        self.arm = arm
        self.enc = Encoder(n_ch)
        self.l1 = nn.Linear(self.enc.d_z + N_BINS, 64); self.l2 = nn.Linear(64, 1)
        nn.init.zeros_(self.l2.weight); nn.init.zeros_(self.l2.bias)
        self.proj = Proj(self.enc.d_z)

    def forward(self, x, h, off):
        z = self.enc(x).mean(-1)
        oh = F.one_hot(h, N_BINS).float()
        if self.arm == "D0":
            oh = torch.zeros_like(oh)
        r = self.l2(F.gelu(self.l1(torch.cat([z, oh], 1))))[:, 0]
        return (r if self.arm in ("D0", "D1") else off + r), z


def _batches(train, rng, n_rec=4, per=32):
    """Every batch: n_rec records x per trials (sampled without replacement within an epoch where possible)."""
    pools = {i: list(rng.permutation(len(k["y"]))) for i, k in enumerate(train)}
    total = sum(len(k["y"]) for k in train)
    for _ in range(total // (n_rec * per)):
        recs = rng.choice(len(train), n_rec, replace=False)
        out = []
        for r in recs:
            if len(pools[r]) < per:
                pools[r] = list(rng.permutation(len(train[r]["y"])))
            out += [(int(r), int(pools[r].pop())) for _ in range(per)]
        yield out


def add_swaps(kids, seed=20261007):
    """Fixed once: for each trial, a trial of the same record, same history bin, different physical block (fallback:
    same bin); used by the null twin (training and scoring) and by the conditional-mismatch evaluation."""
    rng = np.random.default_rng(seed)
    for k in kids:
        k["swap"], k["swap_strict_fraction"] = _mismatch_index(k, rng)


def _tensors(kids, items, q0, dev, twin=False):
    x = torch.tensor(np.stack([kids[r]["x"][kids[r]["swap"][i] if twin else i] for r, i in items]), device=dev)
    h = torch.tensor([kids[r]["bin"][i] for r, i in items], device=dev)
    y = torch.tensor([kids[r]["y"][i] for r, i in items], device=dev).float()
    off = torch.tensor(_logit(q0[[kids[r]["bin"][i] for r, i in items]]), device=dev).float()
    rec = torch.tensor([r for r, _ in items], device=dev); blk = torch.tensor([kids[r]["block"][i] for r, i in items], device=dev)
    return x, h, y, off, rec, blk


def _es_loss(model, kids, q0, dev, twin):
    tot, n = 0.0, 0
    for k in kids:
        lg = logits_for(model, k, q0, dev, x=k["x"][k["swap"]] if twin else None)
        y = k["y"]
        tot += float(np.sum(np.logaddexp(0, lg) - y * lg)); n += len(y)
    return tot / n


def train_arm(arm, fit, es, q0, cfg, log, dev, twin=False):
    """Fit on `fit` children; early stopping on the natural cross-entropy of `es` children (never the scored
    children); best epoch restored. twin=True: every trial's EEG replaced by its fixed swap partner."""
    set_seed(cfg["seed"]); rng = np.random.default_rng(cfg["seed"])
    model = HCModel(arm, fit[0]["x"].shape[1]).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    best = (np.inf, -1, None)
    for ep in range(cfg["epochs"]):
        model.train(); st = {"nat": [], "con": [], "gn": [], "anchors": []}
        for items in _batches(fit, rng):
            x, h, y, off, rec, blk = _tensors(fit, items, q0, dev, twin=twin)
            logit, z = model(x, h, off)
            nat = F.binary_cross_entropy_with_logits(logit, y)
            loss = nat
            if arm in ("D3", "D4"):
                eye = torch.eye(len(y), dtype=torch.bool, device=dev)
                valid = ~eye if arm == "D3" else (~eye & (rec[:, None] == rec[None]) & (h[:, None] == h[None]) & (blk[:, None] != blk[None]))
                con, na = supcon(model.proj(z), y.long(), valid, cfg["tau"])
                loss = nat + cfg["eta"] * con; st["con"].append(float(con)); st["anchors"].append(na)
            opt.zero_grad(); loss.backward()
            gn, _ = grad_param_norms(model)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
            st["nat"].append(float(nat)); st["gn"].append(gn)
        model.eval()
        es_ce = _es_loss(model, es, q0, dev, twin)
        if es_ce < best[0]:
            best = (es_ce, ep, {k: v.detach().clone() for k, v in model.state_dict().items()})
        model.train(); assert model.training
        _, pn = grad_param_norms(model)
        log.append({"arm": arm + ("_twin" if twin else ""), "epoch": ep, "train_nat": float(np.mean(st["nat"])),
                    "train_con": float(np.mean(st["con"])) if st["con"] else None,
                    "contrast_anchors_per_batch": float(np.mean(st["anchors"])) if st["anchors"] else None,
                    "es_ce": es_ce, "grad_norm_mean": float(np.mean(st["gn"])), "param_norm": pn, "nonfinite": nonfinite(model),
                    "mode_after_val": "train" if model.training else "eval"})
    model.load_state_dict(best[2]); model.eval()
    model.best_epoch = best[1]
    return model


def _mismatch_index(k, rng):
    """For each trial: another trial of the same record, same history bin, different physical block (else any other
    trial of the same bin); returns indices and the fraction that met the strict rule."""
    idx, strict = np.empty(len(k["y"]), int), 0
    for i in range(len(k["y"])):
        c = np.flatnonzero((k["bin"] == k["bin"][i]) & (k["block"] != k["block"][i]))
        if len(c):
            strict += 1
        else:
            c = np.flatnonzero((k["bin"] == k["bin"][i]) & (np.arange(len(k["y"])) != i))
        idx[i] = rng.choice(c) if len(c) else i
    return idx, strict / len(k["y"])


def _auc(s, y):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else float("nan")


def logits_for(model, k, q0, dev, x=None, bs=512):
    x = k["x"] if x is None else x
    out = []
    with torch.no_grad():
        for a in range(0, len(x), bs):
            xb = torch.tensor(x[a:a + bs], device=dev); hb = torch.tensor(k["bin"][a:a + bs], device=dev)
            ob = torch.tensor(_logit(q0[k["bin"][a:a + bs]]), device=dev).float()
            out.append(model(xb, hb, ob)[0].cpu().numpy())
    return np.concatenate(out)


def _ll2(p, y):
    return np.where(y == 1, np.log2(np.clip(p, 1e-12, 1)), np.log2(np.clip(1 - p, 1e-12, 1)))


def evaluate(model, kids, q0, dev, b1=None, twin=False):
    """Per child: G_Cur|Hist (bits/trial), AUC, Brier; for trained models also the conditional-mismatch G (fixed swap
    partner EEG). twin=True: the model is a null twin and is scored on swapped EEG. Means over children, overall and
    by group."""
    per = {}
    for k in kids:
        p0 = q0[k["bin"]]; y = k["y"]
        if model is None:  # B0 / B1
            lg = _logit(p0) if b1 is None else _logit(p0) + np.where(np.isfinite(k["ev"]), b1[0] + b1[1] * np.nan_to_num(k["ev"]), 0.0)
        else:
            lg = logits_for(model, k, q0, dev, x=k["x"][k["swap"]] if twin else None)
        p1 = 1 / (1 + np.exp(-lg))
        cs = (p0 > 0.01) & (p0 < 0.99)  # common support: histories with real current-class uncertainty (plan §6.4)
        g = _ll2(p1, y) - _ll2(p0, y)
        r = {"G_bits_per_trial": float(g.mean()), "G_common_support": float(g[cs].mean()) if cs.any() else float("nan"),
             "auc": _auc(p1, y), "auc_common_support": _auc(p1[cs], y[cs]) if cs.any() else float("nan"),
             "brier": float(((p1 - y) ** 2).mean()), "frac_common_support": float(cs.mean()),
             "n_q0_violations": int(((p0 <= 0.01) & (y == 1)).sum() + ((p0 >= 0.99) & (y == 0)).sum())}
        if model is not None and not twin:
            pm = 1 / (1 + np.exp(-logits_for(model, k, q0, dev, x=k["x"][k["swap"]])))
            gm = _ll2(pm, y) - _ll2(p0, y)
            r["G_mismatch"] = float(gm.mean()); r["G_mismatch_common_support"] = float(gm[cs].mean()) if cs.any() else float("nan")
        r.update({"n": int(len(y)), "group": k["group"], "swap_strict_fraction": k.get("swap_strict_fraction")})
        per[k["id"]] = r
    keys = [kk for kk in next(iter(per.values())) if kk not in ("n", "group", "swap_strict_fraction")]
    mean = lambda vs: {kk: float(np.nanmean([v[kk] for v in vs])) for kk in keys}
    return {"mean_over_children": mean(per.values()),
            "by_group": {g: mean([v for v in per.values() if v["group"] == g]) for g in ("HA", "NH") if any(v["group"] == g for v in per.values())},
            "per_child": per}


def fit_b1(train, q0):
    from ..c3dl_stage0 import _fit_offset_logistic
    ev = np.concatenate([k["ev"] for k in train])[:, None]; y = np.concatenate([k["y"] for k in train])
    off = _logit(q0[np.concatenate([k["bin"] for k in train])])
    ok = np.isfinite(ev[:, 0])
    w = _fit_offset_logistic(ev[ok], y[ok], off[ok])
    return float(w[0]), float(w[1])
