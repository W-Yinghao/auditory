"""Self-supervised pretraining on the unlabelled recordings.

The pretext task is relative positioning WITHIN one recording: given two windows from
the same recording, decide whether they are close in time or far apart. The choice is
deliberate. A contrastive objective whose negatives come from other recordings rewards
whatever makes a recording identifiable - impedance, electrode placement, amplifier
noise - which is exactly the shortcut that made the supervised from-scratch decoder in
round 1 memorise its training recordings. Keeping both members of every pair inside one
recording removes that gradient entirely.
"""
from __future__ import annotations

import numpy as np
import torch
from torch import nn

LOG2 = float(np.log(2.0))


class RelativePositioning(nn.Module):
    """Encoder plus a binary head on the absolute embedding difference."""

    def __init__(self, encoder: nn.Module, embedding_dim: int):
        super().__init__()
        self.encoder = encoder
        self.head = nn.Sequential(nn.Linear(embedding_dim, embedding_dim // 2), nn.GELU(),
                                  nn.Linear(embedding_dim // 2, 1))

    def forward(self, first, second):
        difference = torch.abs(self.encoder.embed(first) - self.encoder.embed(second))
        return self.head(difference).squeeze(-1)


class PairSampler:
    """Uniform within-recording pairs, labelled near or far, grey zone discarded."""

    def __init__(self, bank, rows, *, near_seconds: float, far_seconds: float, seed: int):
        self.bank = bank
        self.rate = bank.rate
        self.near = near_seconds * bank.rate
        self.far = far_seconds * bank.rate
        self.generator = torch.Generator(device=bank.device).manual_seed(seed)
        self.rows = rows
        record = bank.record[rows]
        order = torch.argsort(record)
        self.sorted_rows = rows[order]
        sorted_record = record[order]
        unique, counts = torch.unique_consecutive(sorted_record, return_counts=True)
        self.starts_index = torch.cumsum(counts, 0) - counts
        self.counts = counts
        self.unique = unique
        self.usable = int((counts >= 2).sum().item())

    def draw(self, size: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Return (anchor_rows, partner_rows, labels) with labels 1 = near."""
        eligible = torch.nonzero(self.counts >= 2, as_tuple=False).squeeze(1)
        anchors, partners, labels = [], [], []
        wanted = size
        for _ in range(12):  # bounded retries; the grey zone rejects some draws
            pick = eligible[torch.randint(eligible.numel(), (wanted,), device=self.bank.device,
                                          generator=self.generator)]
            base = self.starts_index[pick]
            count = self.counts[pick]
            offset_a = (torch.rand(wanted, device=self.bank.device,
                                   generator=self.generator) * count).long()
            offset_b = (torch.rand(wanted, device=self.bank.device,
                                   generator=self.generator) * count).long()
            row_a = self.sorted_rows[base + offset_a]
            row_b = self.sorted_rows[base + offset_b]
            delta = torch.abs(self.bank.start[row_a] - self.bank.start[row_b]).float()
            near = delta <= self.near
            far = delta >= self.far
            keep = near | far
            anchors.append(row_a[keep])
            partners.append(row_b[keep])
            labels.append(near[keep].float())
            got = int(sum(a.numel() for a in anchors))
            if got >= size:
                break
        anchor = torch.cat(anchors)[:size]
        partner = torch.cat(partners)[:size]
        label = torch.cat(labels)[:size]
        return anchor, partner, label


def pretrain(model: RelativePositioning, bank, channels, sampler: PairSampler, *,
             device: str, steps: int, batch_size: int, learning_rate: float,
             weight_decay: float, seed: int, validation: PairSampler | None = None,
             check_every: int = 250, validation_batches: int = 8) -> dict:
    torch.manual_seed(seed)
    model.to(device).train()
    optimiser = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    schedule = torch.optim.lr_scheduler.OneCycleLR(optimiser, max_lr=learning_rate,
                                                   total_steps=steps, pct_start=0.1)
    criterion = nn.BCEWithLogitsLoss()
    history, best = [], {"bits": float("inf"), "step": -1, "state": None}
    for step in range(steps):
        anchor, partner, label = sampler.draw(batch_size)
        logits = model(bank.batch(anchor, channels), bank.batch(partner, channels))
        loss = criterion(logits, label)
        if not torch.isfinite(loss):
            return {"status": "D2_SSL_NONFINITE", "step": step, "history": history}
        optimiser.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimiser.step()
        schedule.step()
        if validation is not None and (step % check_every == check_every - 1 or step == steps - 1):
            bits, accuracy = _validate(model, bank, channels, validation, batch_size,
                                       validation_batches)
            history.append({"step": step, "train_bits": float(loss.item()) / LOG2,
                            "validation_bits": bits, "validation_accuracy": accuracy})
            if bits < best["bits"]:
                best = {"bits": bits, "step": step,
                        "state": {k: v.detach().clone() for k, v in model.state_dict().items()}}
    if best["state"] is not None:
        model.load_state_dict(best["state"])
    return {"status": "D2_SSL_TRAINED", "history": history,
            "best_validation_bits": best["bits"] if best["step"] >= 0 else None,
            "best_step": best["step"]}


@torch.no_grad()
def _validate(model, bank, channels, sampler, batch_size, batches):
    model.eval()
    total, correct, count = 0.0, 0, 0
    for _ in range(batches):
        anchor, partner, label = sampler.draw(batch_size)
        logits = model(bank.batch(anchor, channels), bank.batch(partner, channels))
        total += float(nn.functional.binary_cross_entropy_with_logits(
            logits, label, reduction="sum").item())
        correct += int(((logits > 0).float() == label).sum().item())
        count += int(label.numel())
    model.train()
    return total / max(count, 1) / LOG2, correct / max(count, 1)


@torch.no_grad()
def embed_records(encoder: nn.Module, bank, channels, records, *, device: str,
                  batch_size: int, stride: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Mean and standard deviation of the frozen embedding over each recording's windows."""
    encoder.to(device).eval()
    features, present = [], []
    for record in records:
        rows = bank.rows_for([int(record)])[::stride]
        if rows.numel() == 0:
            continue
        pieces = []
        for begin in range(0, rows.numel(), batch_size):
            picks = rows[begin:begin + batch_size]
            pieces.append(encoder.embed(bank.batch(picks, channels)).float().cpu().numpy())
        stacked = np.concatenate(pieces, axis=0)
        features.append(np.concatenate([stacked.mean(axis=0), stacked.std(axis=0)]))
        present.append(int(record))
    return np.stack(features), np.array(present, dtype=int)
