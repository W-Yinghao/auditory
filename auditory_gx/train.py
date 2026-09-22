"""Training loops and metrics for the GX decoders (GPU, mixed precision, early stopping on inner validation)."""
from __future__ import annotations

import math

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score

from .data import Lane
from .models import EEGNet
from .runtime import cfg

LOG2 = math.log(2.0)
TRIAL_WEIGHTS = None     # optional [N] tensor set by the CLI for robust (QC-free) training


def seed_all(seed: int) -> torch.Generator:
    torch.manual_seed(seed)
    np.random.seed(seed % (2 ** 31))
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    return gen


def build_model(config: dict, lane: Lane, *, n_children: int = 0, cond_dim: int = 0) -> EEGNet:
    m = cfg(config, "model")
    return EEGNet(lane.x.shape[1], lane.x.shape[2], lane.n_classes, F1=int(m["F1"]), D=int(m["D"]), F2=int(m["F2"]),
                  k1=int(m["k1"]), k2=int(m["k2"]), dropout=float(m["dropout"]),
                  n_children=n_children, cond_dim=cond_dim)


def augment(xb: torch.Tensor, config: dict, gen: torch.Generator) -> torch.Tensor:
    t = cfg(config, "train")
    B, C, T = xb.shape
    dev = xb.device
    x = xb.float()
    scale = 1.0 + (torch.rand(B, 1, 1, generator=gen, device=dev) * 2 - 1) * float(t["amplitude_jitter"])
    x = x * scale
    if float(t["noise_sd"]) > 0:
        x = x + torch.randn(B, C, T, generator=gen, device=dev) * float(t["noise_sd"]) * x.std()
    if float(t["channel_dropout"]) > 0:
        keep = (torch.rand(B, C, 1, generator=gen, device=dev) > float(t["channel_dropout"])).float()
        x = x * keep
    shift = int(t["time_shift_samples"])
    if shift > 0:
        s = int(torch.randint(-shift, shift + 1, (1,), generator=gen, device=dev).item())
        x = torch.roll(x, shifts=s, dims=-1)
    return x


def class_weights(y: torch.Tensor, n_classes: int) -> torch.Tensor:
    counts = torch.bincount(y, minlength=n_classes).float().clamp(min=1)
    w = counts.sum() / (n_classes * counts)
    return w


@torch.no_grad()
def predict(model: nn.Module, lane: Lane, idx: np.ndarray, *, child: torch.Tensor | None = None,
            cond: torch.Tensor | None = None, batch: int = 1024) -> np.ndarray:
    model.eval()
    out = []
    idx_t = torch.as_tensor(idx, dtype=torch.long, device=lane.x.device)
    for b in range(0, len(idx_t), batch):
        sel = idx_t[b:b + batch]
        xb = lane.x[sel].float()
        cb = child[sel] if child is not None else None
        kb = cond[sel] if cond is not None else None
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=xb.is_cuda):
            logits = model(xb, cb, kb)
        out.append(logits.float().cpu().numpy())
    model.train()
    return np.concatenate(out) if out else np.zeros((0, lane.n_classes), dtype=np.float32)


def balanced_ce_bits(logits: np.ndarray, y: np.ndarray, n_classes: int) -> float:
    """Class-balanced cross-entropy in bits (auditory5 CE_bal convention); chance = log2 K."""
    z = logits - logits.max(1, keepdims=True)
    logp = z - np.log(np.exp(z).sum(1, keepdims=True))
    per_class = []
    for k in range(n_classes):
        m = y == k
        if m.any():
            per_class.append(-logp[m, k].mean() / LOG2)
    return float(np.mean(per_class)) if per_class else float("nan")


def fit(model: nn.Module, lane: Lane, train_idx: np.ndarray, val_idx: np.ndarray, config: dict, *, seed: int,
        child: torch.Tensor | None = None, cond: torch.Tensor | None = None, max_epochs: int | None = None,
        learning_rate: float | None = None, log: list | None = None) -> dict:
    """Weighted-CE training with AdamW + cosine schedule; restores the best inner-validation state."""
    t = cfg(config, "train")
    gen = seed_all(seed)
    dev = lane.x.device
    gen_dev = torch.Generator(device=dev)
    gen_dev.manual_seed(seed)
    model.to(dev).train()
    max_epochs = int(max_epochs or t["max_epochs"])
    lr = float(learning_rate or t["learning_rate"])
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=float(t["weight_decay"]))
    bs = int(t["batch_size"])
    steps_per_epoch = max(1, math.ceil(len(train_idx) / bs))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=max_epochs * steps_per_epoch,
                                                pct_start=0.15, anneal_strategy="cos")
    w = class_weights(lane.y[torch.as_tensor(train_idx, device=dev)], lane.n_classes)
    tr = torch.as_tensor(train_idx, dtype=torch.long, device=dev)
    best, best_state, bad = float("inf"), None, 0
    yv = lane.y[torch.as_tensor(val_idx, device=dev)].cpu().numpy()
    for epoch in range(max_epochs):
        perm = tr[torch.randperm(len(tr), generator=gen_dev, device=dev)]
        total = 0.0
        for b in range(0, len(perm), bs):
            sel = perm[b:b + bs]
            xb = augment(lane.x[sel], config, gen_dev)
            cb = child[sel] if child is not None else None
            kb = cond[sel] if cond is not None else None
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=xb.is_cuda):
                logits = model(xb, cb, kb)
                if TRIAL_WEIGHTS is None:
                    loss = F.cross_entropy(logits.float(), lane.y[sel], weight=w)
                else:
                    per = F.cross_entropy(logits.float(), lane.y[sel], weight=w, reduction="none")
                    tw = TRIAL_WEIGHTS[sel]
                    loss = (per * tw).sum() / tw.sum().clamp(min=1e-6)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
            total += float(loss.item()) * len(sel)
        val_logits = predict(model, lane, val_idx, child=child, cond=cond)
        val = balanced_ce_bits(val_logits, yv, lane.n_classes)
        if log is not None:
            log.append({"epoch": epoch, "train_loss": total / max(1, len(tr)), "val_ce_bal_bits": val})
        if val < best - 1e-5:
            best, bad = val, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= int(t["patience"]):
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return {"best_val_ce_bal_bits": best, "epochs_run": epoch + 1}


def child_metrics(logits: np.ndarray, y: np.ndarray, n_classes: int) -> dict:
    """Threshold-free and balanced metrics for one child's trials."""
    out = {"n": int(len(y)), "n_class1": int(np.sum(y == 1))}
    if len(np.unique(y)) < 2:
        out.update(auc=float("nan"), bacc=float("nan"), ce_bal_bits=float("nan"), j_bits=float("nan"))
        return out
    if n_classes == 2:
        score = logits[:, 1] - logits[:, 0]
        out["auc"] = float(roc_auc_score(y, score))
        pred = (score > 0).astype(int)          # class-weighted training -> balanced decision at 0
    else:
        aucs = []
        for k in range(n_classes):
            if 0 < np.sum(y == k) < len(y):
                aucs.append(roc_auc_score((y == k).astype(int), logits[:, k] - np.log(np.exp(logits).sum(1))))
        out["auc"] = float(np.mean(aucs)) if aucs else float("nan")
        pred = logits.argmax(1)
        m = np.isin(y, [1, 2])
        if np.sum(y[m] == 1) > 0 and np.sum(y[m] == 2) > 0:
            out["auc_pitch_direction"] = float(roc_auc_score((y[m] == 2).astype(int), logits[m, 2] - logits[m, 1]))
    accs = [float(np.mean(pred[y == k] == k)) for k in range(n_classes) if np.any(y == k)]
    out["bacc"] = float(np.mean(accs))
    out["ce_bal_bits"] = balanced_ce_bits(logits, y, n_classes)
    out["j_bits"] = math.log2(n_classes) - out["ce_bal_bits"]
    return out
