"""GPU helpers: checked lane loading, batched inference with occlusion, model builders."""
from __future__ import annotations

import dataclasses

import numpy as np
import torch
from torch import nn

from auditory_gx import data as gxd
from auditory_gx import train as gxt
from auditory_gx.round3 import HA_CHANNELS
from auditory_gx.runtime import load_config as gx_load_config

from .runtime import ROOT, cfg


def device():
    if not torch.cuda.is_available():
        raise RuntimeError("PF GPU commands need a GPU (slurm/auditory_pf_gpu.sbatch)")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("PF GPU commands need bf16 support (A100/A40/L40S/H100/A30)")
    return torch.device("cuda")


def load_lane_checked(config: dict, cohort, dev):
    gx_config = gx_load_config(cfg(config, "sources.gx_config"))
    stage_private = ROOT / "private/auditory_gx" / cfg(config, "sources.stage_run")
    lane = gxd.load_lane(gx_config, stage_private, cfg(config, "sources.lane"), dev)
    if list(lane.record_ids) != list(cohort.rec.record_id):
        raise RuntimeError("LANE_RECORD_ORDER_MISMATCH")
    if not np.array_equal(lane.child, cohort.rec.child.to_numpy()[cohort.t_record]):
        raise RuntimeError("LANE_CHILD_MISMATCH")
    if not np.array_equal(lane.y.cpu().numpy(), cohort.t_y):
        raise RuntimeError("LANE_LABEL_MISMATCH")
    if not np.allclose(lane.onset_s, cohort.t_onset):
        raise RuntimeError("LANE_ONSET_MISMATCH")
    return lane, gx_config


def masked_lane(lane, keep_from: int, keep_to: int):
    """Copy of the lane whose epochs are zero outside [keep_from, keep_to) samples."""
    x = torch.zeros_like(lane.x)
    x[:, :, keep_from:keep_to] = lane.x[:, :, keep_from:keep_to]
    return dataclasses.replace(lane, x=x)


def channel_index(names: list[str]) -> list[int]:
    return [HA_CHANNELS.index(n) for n in names]


def occlusions(config: dict, T: int, rate: float = 250.0, pre_s: float = 0.2) -> list[dict]:
    """19 time windows (80 ms, 40 ms step) then the fixed channel groups (protocol H3)."""
    win = int(round(float(cfg(config, "windows.width_s")) * rate))
    step = int(round(float(cfg(config, "windows.step_s")) * rate))
    out = []
    for s in range(0, T - win + 1, step):
        out.append({"kind": "time", "name": f"t{(s + win / 2) / rate - pre_s:+.2f}", "start": s, "stop": s + win,
                    "centre_s": round((s + win / 2) / rate - pre_s, 4)})
    for gname, chans in cfg(config, "channel_groups").items():
        out.append({"kind": "chan", "name": gname, "chans": channel_index(list(chans))})
    return out


class LinearDecoder(nn.Module):
    """Full-window linear baseline: flattened [C, T] epoch -> class logits."""

    def __init__(self, n_channels: int, n_times: int, n_classes: int):
        super().__init__()
        self.lin = nn.Linear(n_channels * n_times, n_classes)

    def forward(self, x, child=None, cond=None):
        return self.lin(x.flatten(1))


@torch.no_grad()
def infer(model: nn.Module, lane, idx: np.ndarray, *, occl: dict | None = None, embed: bool = False,
          child: torch.Tensor | None = None, cond: torch.Tensor | None = None, batch: int = 4096):
    """Logit difference (class1 - class0) and optionally the pre-head embedding, eval mode."""
    model.eval()
    diffs, embs = [], []
    idx_t = torch.as_tensor(np.asarray(idx), dtype=torch.long, device=lane.x.device)
    for b in range(0, len(idx_t), batch):
        sel = idx_t[b:b + batch]
        xb = lane.x[sel].float()
        if occl is not None:
            if occl["kind"] == "time":
                xb[:, :, occl["start"]:occl["stop"]] = 0
            else:
                xb[:, occl["chans"], :] = 0
        cb = child[sel] if child is not None else None
        kb = cond[sel] if cond is not None else None
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            if embed:
                e = model.embed(xb, cb, kb)
                logits = model.head(e)
                embs.append(e.float().cpu().numpy())
            else:
                logits = model(xb, cb, kb)
        logits = logits.float()
        diffs.append((logits[:, 1] - logits[:, 0]).cpu().numpy() if logits.shape[1] > 1 else logits[:, 0].cpu().numpy())
    d = np.concatenate(diffs) if diffs else np.zeros(0, np.float32)
    if embed:
        return d, (np.concatenate(embs) if embs else np.zeros((0, 0), np.float32))
    return d


def train_stim(lane, gx_config, train_idx: np.ndarray, val_idx: np.ndarray, seed: int, *, linear: bool = False,
               cond_dim: int = 0, child=None, cond=None, model=None):
    gxt.seed_all(seed)
    if model is None:
        model = (LinearDecoder(lane.x.shape[1], lane.x.shape[2], lane.n_classes) if linear
                 else gxt.build_model(gx_config, lane, cond_dim=cond_dim))
    info = gxt.fit(model, lane, train_idx, val_idx, gx_config, seed=seed, child=child, cond=cond)
    model.eval()
    return model, info
