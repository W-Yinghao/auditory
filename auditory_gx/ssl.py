"""GX2/GX3: masked-reconstruction self-supervision on the continuous D1 corpus, probes and age fine-tuning."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

from auditory_d2.data import RecordStore

from .models import ConvEncoder, MaskedReconstructor, patch_mask
from .runtime import ROOT, cfg, read_json


def corpus_records(config: dict, branch: str) -> list[dict]:
    """All D1-exported records of one branch with the majority layout; identity/age when known."""
    run = cfg(config, "sources.d1_mff_run" if branch == "MFF" else "sources.d1_bdf_run")
    arrays = ROOT / "private/auditory_d1" / run / "arrays"
    scope = ROOT / "private/auditory_st" / cfg(config, "sources.st_scope_run") / "records.parquet"
    import pandas as pd
    rec = pd.read_parquet(scope)
    if branch == "MFF":
        known = {r["record_id"]: r for r in rec[rec.branch == "MFF"].to_dict("records")}
    else:   # itertuples renames underscore-prefixed columns; use dict rows
        known = {str(r["_d1_container_id"]): r for r in rec[rec.branch == "HA_BDF"].to_dict("records")}
    rows = []
    for meta_path in sorted(arrays.glob("*.json")):
        meta = read_json(meta_path)
        if meta.get("status") != "D1_EXPORTED":
            continue
        cid = meta["container_id"]
        k = known.get(cid)
        rows.append({"container_id": cid, "n_channels": int(meta["n_channels"]), "seconds": float(meta["seconds"]),
                     "layout_hash": str(meta.get("layout_hash") or ""), "run": run,
                     "identity_group": (str(k["identity_group"]) if k is not None else ""),
                     "age_months": (float(k["age_months"]) if k is not None and np.isfinite(float(k["age_months"])) else float("nan")),
                     "protocol_task": (str(k["protocol_task"]) if k is not None else ""),
                     "source_cohort_evidence": (str(k["source_cohort_evidence"]) if k is not None else ""),
                     "record_id": (str(k["record_id"]) if k is not None else "")})
    counts: dict = {}
    for r in rows:
        counts[r["n_channels"]] = counts.get(r["n_channels"], 0) + 1
    majority = max(counts, key=counts.get)
    return [r for r in rows if r["n_channels"] == majority]


def build_window_bank(config: dict, records: list[dict], device, *, windows_per_record: int, seed: int,
                      log=print) -> tuple[torch.Tensor, np.ndarray, list[dict]]:
    """Fixed random usable windows per record, scaled per record, resident on the device as float16."""
    window_s = float(cfg(config, "ssl.window_seconds"))
    rng = np.random.default_rng(seed)
    pieces, owner, kept = [], [], []
    for i, r in enumerate(records):
        store = RecordStore(ROOT, r["run"], r["container_id"], window_seconds=window_s)
        if store.starts.size == 0:
            continue
        picks = rng.choice(store.starts, size=min(windows_per_record, store.starts.size), replace=False)
        block = np.stack([store.read(int(s)) for s in np.sort(picks)])            # [w, C, L]
        scale = float(np.median(np.abs(block)))
        if not np.isfinite(scale) or scale <= 1e-6:
            scale = 1.0
        pieces.append(torch.from_numpy(np.clip(block / scale, -60, 60).astype(np.float16)))
        owner.append(np.full(len(picks), len(kept)))
        kept.append({**r, "n_windows": int(len(picks)), "scale": scale, "usable_fraction": float(store.usable_fraction)})
        if (i + 1) % 25 == 0:
            log(f"loaded {i + 1}/{len(records)} records")
    bank = torch.cat(pieces).to(device)
    return bank, np.concatenate(owner), kept


def train_masked(config: dict, bank: torch.Tensor, device, *, seed: int, steps: int | None = None, log=print) -> tuple[MaskedReconstructor, list]:
    s = cfg(config, "ssl")
    torch.manual_seed(seed)
    gen = torch.Generator(device=device)
    gen.manual_seed(seed)
    model = MaskedReconstructor(bank.shape[1], int(s["width"])).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=float(s["learning_rate"]), weight_decay=0.05)
    steps = int(steps or s["steps"])
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=float(s["learning_rate"]), total_steps=steps, pct_start=0.05)
    bs = int(s["batch_size"])
    patch = int(round(float(s["mask_patch_seconds"]) * float(cfg(config, "epoch.rate_hz"))))
    frac = float(s["mask_fraction"])
    L = bank.shape[2]
    history = []
    model.train()
    for step in range(steps):
        idx = torch.randint(0, bank.shape[0], (bs,), generator=gen, device=device)
        x = bank[idx].float()
        mask = patch_mask(bs, L, patch, frac, gen, device)                  # [B, L]
        xm = x * (~mask).unsqueeze(1).float()
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            recon = model(xm)
        recon = recon.float()[..., :L]
        err = ((recon - x) ** 2).mean(1)                                    # [B, L]
        loss = (err * mask).sum() / mask.sum().clamp(min=1)
        with torch.no_grad():
            base = (x ** 2).mean(1)
            baseline = (base * mask).sum() / mask.sum().clamp(min=1)       # predicting zero
        opt.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        opt.step()
        sched.step()
        if step % 200 == 0 or step == steps - 1:
            history.append({"step": step, "masked_mse": float(loss.item()), "zero_baseline_mse": float(baseline.item()),
                            "r2_masked": float(1.0 - loss.item() / max(baseline.item(), 1e-9))})
            log(f"step {step} masked_mse {loss.item():.4f} baseline {baseline.item():.4f}")
    model.eval()
    return model, history


@torch.no_grad()
def embed_bank(encoder: ConvEncoder, bank: torch.Tensor, batch: int = 512) -> np.ndarray:
    encoder.eval()
    out = []
    for b in range(0, bank.shape[0], batch):
        x = bank[b:b + batch].float()
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            z = encoder.embed(x)
        out.append(z.float().cpu().numpy())
    return np.concatenate(out)


def record_embeddings(z: np.ndarray, owner: np.ndarray, n_records: int) -> np.ndarray:
    d = z.shape[1]
    out = np.zeros((n_records, 2 * d), dtype=np.float64)
    for r in range(n_records):
        m = owner == r
        if m.any():
            out[r, :d] = z[m].mean(0)
            out[r, d:] = z[m].std(0)
    return out


def ridge_probe(X: np.ndarray, y: np.ndarray, groups: np.ndarray, *, n_folds: int, seeds: list[int],
                alphas=(0.1, 1, 10, 100, 1000)) -> dict:
    """Child-held-out ridge with inner alpha selection; returns MAE vs train-mean baseline per seed."""
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import GroupKFold
    from sklearn.preprocessing import StandardScaler
    results = []
    uniq = np.unique(groups)
    for seed in seeds:
        rng = np.random.default_rng(seed)
        perm = {g: i for i, g in enumerate(rng.permutation(uniq))}
        gnum = np.array([perm[g] for g in groups])
        pred = np.full(len(y), np.nan)
        base = np.full(len(y), np.nan)
        for tr, te in GroupKFold(n_splits=n_folds).split(X, y, gnum):
            sc = StandardScaler().fit(X[tr])
            Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])
            best, best_a = None, None
            for a in alphas:
                inner_err = []
                for itr, ival in GroupKFold(n_splits=4).split(Xtr, y[tr], gnum[tr]):
                    m = Ridge(alpha=a).fit(Xtr[itr], y[tr][itr])
                    inner_err.append(np.mean(np.abs(m.predict(Xtr[ival]) - y[tr][ival])))
                if best is None or np.mean(inner_err) < best:
                    best, best_a = np.mean(inner_err), a
            m = Ridge(alpha=best_a).fit(Xtr, y[tr])
            pred[te] = m.predict(Xte)
            base[te] = y[tr].mean()
        results.append({"seed": seed, "mae": float(np.mean(np.abs(pred - y))), "baseline_mae": float(np.mean(np.abs(base - y))),
                        "r": float(np.corrcoef(pred, y)[0, 1]) if np.std(pred) > 0 else float("nan"), "n": int(len(y))})
    return {"per_seed": results, "mae_mean": float(np.mean([r["mae"] for r in results])),
            "baseline_mae_mean": float(np.mean([r["baseline_mae"] for r in results]))}


def logistic_probe(X: np.ndarray, y: np.ndarray, groups: np.ndarray, *, n_folds: int, seeds: list[int]) -> dict:
    """Child-held-out logistic probe; per-child AUC averaged (binary) — used for event-locked embeddings."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import GroupKFold
    from sklearn.preprocessing import StandardScaler
    out = []
    uniq = np.unique(groups)
    for seed in seeds:
        rng = np.random.default_rng(seed)
        perm = {g: i for i, g in enumerate(rng.permutation(uniq))}
        gnum = np.array([perm[g] for g in groups])
        score = np.full(len(y), np.nan)
        for tr, te in GroupKFold(n_splits=n_folds).split(X, y, gnum):
            sc = StandardScaler().fit(X[tr])
            m = LogisticRegression(C=1.0, max_iter=3000, class_weight="balanced").fit(sc.transform(X[tr]), y[tr])
            score[te] = m.decision_function(sc.transform(X[te]))
        aucs = []
        for g in uniq:
            mg = groups == g
            if len(np.unique(y[mg])) == 2:
                aucs.append(roc_auc_score(y[mg], score[mg]))
        out.append({"seed": seed, "auc_child_mean": float(np.mean(aucs)), "children": len(aucs)})
    return {"per_seed": out, "auc_child_mean": float(np.mean([r["auc_child_mean"] for r in out]))}


class AgeHead(nn.Module):
    def __init__(self, encoder: ConvEncoder):
        super().__init__()
        self.encoder = encoder
        self.head = nn.Sequential(nn.Linear(encoder.embedding_dim, 64), nn.GELU(), nn.Linear(64, 1))

    def forward(self, x):
        return self.head(self.encoder.embed(x)).squeeze(-1)


def finetune_age(config: dict, bank: torch.Tensor, owner: np.ndarray, records: list[dict], device, *, seed: int,
                 init_state: dict | None, n_folds: int, epochs: int = 12, log=print) -> dict:
    """Child-held-out age regression on windows; record-level prediction = mean over its windows."""
    ages = np.array([r["age_months"] for r in records])
    groups = np.array([r["identity_group"] for r in records])
    usable = np.flatnonzero(np.isfinite(ages) & (groups != ""))
    uniq = np.unique(groups[usable])
    rng = np.random.default_rng(seed)
    order = rng.permutation(uniq)
    folds = [order[k::n_folds] for k in range(n_folds)]
    pred_rec = np.full(len(records), np.nan)
    base_rec = np.full(len(records), np.nan)
    width = int(cfg(config, "ssl.width"))
    for k, test_groups in enumerate(folds):
        test_rec = usable[np.isin(groups[usable], test_groups)]
        train_rec = usable[~np.isin(groups[usable], test_groups)]
        mu = float(ages[train_rec].mean())
        sd = float(ages[train_rec].std() + 1e-6)
        enc = ConvEncoder(bank.shape[1], width)
        if init_state is not None:
            enc.load_state_dict({k2.replace("encoder.", "", 1): v for k2, v in init_state.items() if k2.startswith("encoder.")})
        model = AgeHead(enc).to(device)
        opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.05)
        tr_windows = np.flatnonzero(np.isin(owner, train_rec))
        target = torch.as_tensor((ages[owner] - mu) / sd, dtype=torch.float32, device=device)
        gen = torch.Generator(device=device)
        gen.manual_seed(seed * 10 + k)
        model.train()
        bs = 64
        for epoch in range(epochs):
            perm = torch.as_tensor(tr_windows, device=device)[torch.randperm(len(tr_windows), generator=gen, device=device)]
            for b in range(0, len(perm), bs):
                sel = perm[b:b + bs]
                x = bank[sel].float()
                x = x * (1 + 0.2 * (torch.rand(len(sel), 1, 1, generator=gen, device=device) - 0.5))
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    out = model(x)
                loss = F.smooth_l1_loss(out.float(), target[sel])
                opt.zero_grad(set_to_none=True)
                loss.backward()
                opt.step()
        model.eval()
        with torch.no_grad():
            for r in test_rec:
                sel = torch.as_tensor(np.flatnonzero(owner == r), device=device)
                outs = []
                for b in range(0, len(sel), 256):
                    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                        outs.append(model(bank[sel[b:b + 256]].float()).float())
                pred_rec[r] = float(torch.cat(outs).mean().item()) * sd + mu
                base_rec[r] = mu
        log(f"age fold {k}: test records {len(test_rec)}")
    m = np.isfinite(pred_rec)
    err = np.abs(pred_rec[m] - ages[m])
    return {"seed": seed, "n_records": int(m.sum()), "n_children": int(len(uniq)),
            "mae": float(err.mean()), "baseline_mae": float(np.abs(base_rec[m] - ages[m]).mean()),
            "r": float(np.corrcoef(pred_rec[m], ages[m])[0, 1]) if m.sum() > 2 else float("nan"),
            "predictions": {records[i]["container_id"]: float(pred_rec[i]) for i in np.flatnonzero(m)}}
