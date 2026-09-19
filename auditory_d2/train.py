"""Training and the information readout.

The primary information quantity is operational and needs no density estimator:

    bits_recovered = CE_marginal(test) - CE_model(test)          [log base 2]

with CE_marginal the cross-entropy of the TRAIN-fold marginal class distribution scored
on the test fold. Because the marginal predictor is a fixed function of training data
only, this difference is a lower bound on I(Z; Y) up to the generalisation gap, and it
is reported with a label-shuffled control that must land at zero.
"""
from __future__ import annotations

import numpy as np
import torch
from torch import nn

LOG2 = float(np.log(2.0))


def quantile_bins(values: np.ndarray, n_bins: int) -> np.ndarray:
    """Interior bin edges from the training fold only."""
    quantiles = np.linspace(0.0, 1.0, n_bins + 1)[1:-1]
    edges = np.quantile(np.asarray(values, dtype=float), quantiles)
    return np.unique(edges)


def assign_bins(values: np.ndarray, edges: np.ndarray) -> np.ndarray:
    return np.digitize(np.asarray(values, dtype=float), edges, right=False).astype(np.int64)


def marginal_log_probabilities(labels: np.ndarray, n_classes: int) -> np.ndarray:
    counts = np.bincount(labels, minlength=n_classes).astype(float) + 0.5
    return np.log(counts / counts.sum())


def cross_entropy_bits(log_probabilities: np.ndarray, labels: np.ndarray) -> float:
    return float(-log_probabilities[np.arange(labels.size), labels].mean() / LOG2)


@torch.no_grad()
def _validation_bits(model, bank, channels, labels, rows, batch_size: int) -> float:
    model.eval()
    total, count = 0.0, 0
    for begin in range(0, rows.numel(), batch_size):
        picks = rows[begin:begin + batch_size]
        logits = model(bank.batch(picks, channels))
        target = labels[bank.record[picks]]
        total += float(nn.functional.cross_entropy(logits, target, reduction="sum").item())
        count += int(picks.numel())
    model.train()
    return total / max(count, 1) / LOG2


def train_one(model: nn.Module, bank, channels, labels, rows, *, device: str, steps: int,
              batch_size: int, learning_rate: float, weight_decay: float, seed: int,
              validation_rows=None, check_every: int = 100) -> dict:
    """Train on device-resident windows. `labels` is a long tensor indexed by record.

    When `validation_rows` is given the best-validation state is restored before
    returning, so the reported model is never an arbitrary last iterate.
    """
    torch.manual_seed(seed)
    generator = torch.Generator(device=device).manual_seed(seed)
    model.to(device).train()
    optimiser = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    schedule = torch.optim.lr_scheduler.OneCycleLR(optimiser, max_lr=learning_rate,
                                                   total_steps=steps, pct_start=0.15)
    criterion = nn.CrossEntropyLoss()
    last = float("nan")
    best = {"bits": float("inf"), "step": -1, "state": None}
    for step in range(steps):
        picks = rows[torch.randint(rows.numel(), (min(batch_size, rows.numel()),),
                                   device=device, generator=generator)]
        batch = bank.batch(picks, channels)
        target = labels[bank.record[picks]]
        optimiser.zero_grad(set_to_none=True)
        loss = criterion(model(batch), target)
        if not torch.isfinite(loss):
            return {"status": "D2_NONFINITE_LOSS", "step": step}
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimiser.step()
        schedule.step()
        last = float(loss.item())
        if validation_rows is not None and validation_rows.numel() and (
                step % check_every == check_every - 1 or step == steps - 1):
            bits = _validation_bits(model, bank, channels, labels, validation_rows, batch_size)
            if bits < best["bits"]:
                best = {"bits": bits, "step": step,
                        "state": {k: v.detach().clone() for k, v in model.state_dict().items()}}
    restored = False
    if best["state"] is not None:
        model.load_state_dict(best["state"])
        restored = True
    return {"status": "D2_TRAINED", "final_loss_bits": last / LOG2,
            "best_validation_bits": best["bits"] if best["step"] >= 0 else None,
            "best_step": best["step"], "restored_best": restored}


@torch.no_grad()
def evaluate(model: nn.Module, bank, channels, records, *, device: str,
             batch_size: int, stride: int = 1) -> dict:
    """Window-level log-probabilities plus a per-recording aggregate."""
    model.to(device).eval()
    log_probabilities, window_record = [], []
    for record in records:
        rows = bank.rows_for([int(record)])[::stride]
        if rows.numel() == 0:
            continue
        for begin in range(0, rows.numel(), batch_size):
            picks = rows[begin:begin + batch_size]
            logits = model(bank.batch(picks, channels))
            log_probabilities.append(torch.log_softmax(logits.float(), dim=-1).cpu().numpy())
            window_record.append(np.full(int(picks.numel()), int(record), dtype=np.int64))
    if not log_probabilities:
        return {"status": "D2_NO_EVALUATION_WINDOWS"}
    log_probabilities = np.concatenate(log_probabilities, axis=0)
    window_record = np.concatenate(window_record)
    present = np.unique(window_record)
    # Arithmetic mean of the per-window posteriors. Averaging LOG probabilities instead
    # would treat two hundred overlapping windows of one recording as independent
    # evidence, which they are not, and produce a confidently wrong recording posterior.
    probabilities = np.exp(log_probabilities)
    pooled = np.stack([probabilities[window_record == r].mean(axis=0) for r in present])
    pooled = np.log(np.maximum(pooled / pooled.sum(axis=1, keepdims=True), 1e-12))
    return {"status": "D2_EVALUATED", "window_log_probabilities": log_probabilities,
            "window_record": window_record, "records": present,
            "record_log_probabilities": pooled, "n_windows": int(window_record.size)}


def readout(evaluation: dict, labels_per_record: np.ndarray, marginal: np.ndarray,
            bin_centres: np.ndarray) -> dict:
    """Bits recovered and the clinical error, at window level and recording level."""
    records = evaluation["records"]
    record_labels = labels_per_record[records]
    window_labels = labels_per_record[evaluation["window_record"]]
    n_classes = marginal.size
    marginal_windows = np.repeat(marginal[None, :], window_labels.size, axis=0)
    marginal_records = np.repeat(marginal[None, :], record_labels.size, axis=0)

    window_ce = cross_entropy_bits(evaluation["window_log_probabilities"], window_labels)
    window_base = cross_entropy_bits(marginal_windows, window_labels)
    record_ce = cross_entropy_bits(evaluation["record_log_probabilities"], record_labels)
    record_base = cross_entropy_bits(marginal_records, record_labels)

    probabilities = np.exp(evaluation["record_log_probabilities"])
    expected = probabilities @ bin_centres
    truth = bin_centres[record_labels]
    return {
        "n_records": int(records.size), "n_windows": int(evaluation["n_windows"]),
        "n_classes": int(n_classes),
        "window_cross_entropy_bits": window_ce, "window_marginal_bits": window_base,
        "window_bits_recovered": window_base - window_ce,
        "record_cross_entropy_bits": record_ce, "record_marginal_bits": record_base,
        "record_bits_recovered": record_base - record_ce,
        "record_top1_accuracy": float((probabilities.argmax(axis=1) == record_labels).mean()),
        "record_expected_value_MAE": float(np.abs(expected - truth).mean()),
    }
