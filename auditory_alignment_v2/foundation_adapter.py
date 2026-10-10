"""ALN2 module B: EEG foundation-model backbones (CBraMod, REVE) and their adaptation recipes (package docs/04).

Pinned assets (auditory_public/foundation_models/FETCH_RECEIPT.json):
  CBraMod : official code github wjq-learning/CBraMod @ b9e96100, weights HF weighting666/CBraMod @ 500543c (sha256 0792cb80…)
  REVE    : HF brain-bzh/reve-base @ dc2a075 (model.safetensors sha256 8ecc6506…), positions brain-bzh/reve-positions @ befa5b5
Input contracts (resolved here; not tuned on results):
  both    : 200 Hz (per-segment FFT resampling of the cached EEG), no EEG outside the supplied segment / epoch.
  CBraMod : official finetuning datasets divide microvolts by 100; the cached EEG is z-scored per recording channel, so
            x = 0.15 * z (typical 15 uV standard deviation in 100-uV units). Non-overlapping 1 s patches of 200 samples.
  REVE    : pretraining z-scores per recording and clips at 15 SD; x = clip(z, -15, 15). Patches 200 with overlap 20
            (step 0.9 s); positions from the official bank by channel name (legacy 10-20 aliases T3/T4/T5/T6 mapped to
            T7/T8/P7/P8).
Adaptation recipes: random_full (same architecture, random init, all trainable); pretrained_frozen (backbone frozen);
pretrained_peft (LoRA rank 8 on the attention projection weights, via weight parametrisation, backbone otherwise frozen);
pretrained_partial (last 25% of transformer blocks trainable: CBraMod 3/12, REVE 6/22); pretrained_full.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.utils.parametrize as P

FM_ROOT = "/projects/EEG-foundation-model/auditory_public/foundation_models"
CBRAMOD_CODE = os.path.join(FM_ROOT, "github__wjq-learning__CBraMod")
CBRAMOD_W = os.path.join(FM_ROOT, "weighting666__CBraMod@500543c", "pretrained_weights.pth")
REVE_DIR = os.path.join(FM_ROOT, "brain-bzh__reve-base@dc2a075")
REVE_POS = os.path.join(FM_ROOT, "brain-bzh__reve-positions@befa5b5")
FS_FM = 200
CHANNELS = {
    "fau": ["Fp1", "Fz", "F3", "F7", "F9", "FC5", "FC1", "C3", "T7", "TP9", "CP5", "CP1", "Pz", "P3", "P7", "O1", "Oz", "O2", "P4", "P8",
            "TP10", "CP6", "CP2", "C4", "T8", "F10", "FC6", "F4", "F8", "Fp2", "Cz"],
    "dtu": ["Fp1", "AF7", "AF3", "F1", "F3", "F5", "F7", "FT7", "FC5", "FC3", "FC1", "C1", "C3", "C5", "T7", "TP7", "CP5", "CP3", "CP1", "P1",
            "P3", "P5", "P7", "P9", "PO7", "PO3", "O1", "Iz", "Oz", "POz", "Pz", "CPz", "Fpz", "Fp2", "AF8", "AF4", "AFz", "Fz", "F2", "F4",
            "F6", "F8", "FT8", "FC6", "FC4", "FC2", "FCz", "Cz", "C2", "C4", "C6", "T8", "TP8", "CP6", "CP4", "CP2", "P2", "P4", "P6", "P8",
            "P10", "PO8", "PO4", "O2"],
    "federici": ["Fp1", "F3", "F7", "FT9", "FC5", "FC1", "C3", "T7", "TP9", "CP5", "CP1", "Pz", "P3", "P7", "O1", "Oz", "O2", "P4", "P8",
                 "TP10", "CP6", "CP2", "C4", "T8", "FT10", "FC6", "FC2", "F4", "F8", "Fp2", "Fz", "Cz"],
    "private_bdf": ["Fp1", "Fp2", "Fz", "F3", "F4", "F7", "F8", "Cz", "C3", "C4", "T3", "T4", "Pz", "P3", "P4", "T5", "T6", "Oz", "O1", "O2"],
}
ALIASES = {"T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8"}
LORA_RANK = 8


def resample_fft(x, n_out):
    """FFT resampling along the last axis (as the CBraMod preprocessing scripts' signal.resample)."""
    n = x.shape[-1]
    if n == n_out:
        return x
    X = torch.fft.rfft(x.float(), dim=-1)
    m = min(X.shape[-1], n_out // 2 + 1)
    Y = torch.zeros(*X.shape[:-1], n_out // 2 + 1, dtype=X.dtype, device=X.device); Y[..., :m] = X[..., :m]
    return torch.fft.irfft(Y, n=n_out, dim=-1) * (n_out / n)


def _load_cbramod():
    """Official CBraMod code imports 'models.criss_cross_transformer' absolutely: append its repository root to sys.path
    (appended, so installed packages such as 'datasets' are never shadowed) and import models.cbramod."""
    if CBRAMOD_CODE not in sys.path:
        sys.path.append(CBRAMOD_CODE)
    mod = importlib.import_module("models.cbramod")
    assert os.path.dirname(os.path.abspath(mod.__file__)) == os.path.join(CBRAMOD_CODE, "models"), mod.__file__
    return mod.CBraMod


class LoRA(nn.Module):
    """W + (alpha / r) B A, A random, B zero (identity at start)."""

    def __init__(self, shape, r=LORA_RANK, alpha=16):
        super().__init__()
        self.A = nn.Parameter(torch.randn(r, shape[1]) / math.sqrt(shape[1]))
        self.B = nn.Parameter(torch.zeros(shape[0], r))
        self.scale = alpha / r

    def forward(self, W):
        return W + self.scale * (self.B @ self.A)


class Backbone(nn.Module):
    """x [B, C, T_native] -> tokens [B, C, P, E]; also returns patch start times (seconds) and the resolved contract."""

    def __init__(self, arch, dataset, adaptation, fs_native, init_state=None):
        super().__init__()
        self.arch, self.dataset, self.adaptation, self.fs_native = arch, dataset, adaptation, fs_native
        names = [ALIASES.get(c, c) for c in CHANNELS[dataset]]
        self.channel_names = names
        pretrained = adaptation.startswith("pretrained") or adaptation.startswith("auditory")
        if arch == "cbramod":
            CB = _load_cbramod()
            self.net = CB(in_dim=200, out_dim=200, d_model=200, dim_feedforward=800, seq_len=30, n_layer=12, nhead=8)
            if pretrained:
                sd = torch.load(CBRAMOD_W, map_location="cpu")
                missing, unexpected = self.net.load_state_dict(sd, strict=True), None
            self.net.proj_out = nn.Identity()
            self.E, self.blocks = 200, list(self.net.encoder.layers)
            self.attn_weights = [(l.self_attn_s, "in_proj_weight") for l in self.blocks] + [(l.self_attn_t, "in_proj_weight") for l in self.blocks]
        elif arch == "reve":
            from transformers import AutoConfig, AutoModel
            if pretrained:
                self.net = AutoModel.from_pretrained(REVE_DIR, trust_remote_code=True)
            else:
                self.net = AutoModel.from_config(AutoConfig.from_pretrained(REVE_DIR, trust_remote_code=True), trust_remote_code=True)
            bank = AutoModel.from_pretrained(REVE_POS, trust_remote_code=True)
            with torch.no_grad():
                pos = bank(names)
            self.register_buffer("pos", torch.as_tensor(pos, dtype=torch.float32))
            self.E, self.blocks = 512, list(self.net.transformer.layers)
            self.attn_weights = [(blk[0].to_qkv, "weight") for blk in self.blocks] + [(blk[0].to_out, "weight") for blk in self.blocks]
        else:
            raise ValueError(arch)
        self.init_loaded = None
        if init_state is not None:  # donor weights, loaded strictly BEFORE any LoRA parametrisation renames parameters
            res = self.net.load_state_dict(init_state, strict=True)
            self.init_loaded = {"missing": list(res.missing_keys), "unexpected": list(res.unexpected_keys), "n_tensors": len(init_state)}
        self._apply_adaptation()

    def _apply_adaptation(self):
        a = self.adaptation
        for p in self.net.parameters():
            p.requires_grad_(a in ("random_full", "pretrained_full", "auditory_continued_full", "auditory_pretrained_full"))
        self.trainable_layers = "all" if a in ("random_full", "pretrained_full", "auditory_continued_full", "auditory_pretrained_full") else []
        if a in ("pretrained_partial", "auditory_continued_partial"):
            k = 3 if self.arch == "cbramod" else 6
            for blk in self.blocks[-k:]:
                for p in blk.parameters():
                    p.requires_grad_(True)
            n = len(self.blocks); self.trainable_layers = [f"block_{i}" for i in range(n - k, n)]
        if a in ("pretrained_peft", "auditory_pretrained_peft"):
            for mod, wname in self.attn_weights:
                P.register_parametrization(mod, wname, LoRA(getattr(mod, wname).shape))
            for mod, wname in self.attn_weights:
                for p in getattr(mod.parametrizations, wname).parameters():
                    p.requires_grad_(True)
                getattr(mod.parametrizations, wname).original.requires_grad_(False)
            self.trainable_layers = [f"lora_r{LORA_RANK}:{type(m).__name__}.{w}" for m, w in self.attn_weights[:2]] + ["…all attention projections"]

    def contract(self):
        return {"arch": self.arch, "fs_hz": FS_FM, "channels": self.channel_names, "aliases": ALIASES,
                "amplitude": "0.15*z (100-uV units)" if self.arch == "cbramod" else "clip(z, -15, 15)",
                "patch": "200 non-overlapping" if self.arch == "cbramod" else "200 with overlap 20 (step 180)",
                "adaptation": self.adaptation, "trainable_layers": self.trainable_layers,
                "n_params": int(sum(p.numel() for p in self.parameters())), "init_state_loaded": self.init_loaded,
                "n_trainable_backbone": int(sum(p.numel() for p in self.parameters() if p.requires_grad))}

    def patch_starts(self, n200):
        if self.arch == "cbramod":
            return [p * 1.0 for p in range(n200 // 200)]
        return [p * 0.9 for p in range((n200 - 200) // 180 + 1)]

    def forward(self, x):
        B, C, _ = x.shape
        z = resample_fft(x, int(round(x.shape[-1] * FS_FM / self.fs_native)))
        if z.shape[-1] < 200:  # short private epochs: zero-pad inside the epoch support (no extra EEG)
            z = F.pad(z, (0, 200 - z.shape[-1]))
        if self.arch == "cbramod":
            n = (z.shape[-1] // 200) * 200
            tok = self.net((0.15 * z[..., :n]).reshape(B, C, n // 200, 200))
        else:
            tok = self.net(z.clamp(-15, 15), self.pos.expand(B, -1, -1))
        return tok  # [B, C, P, E]


class PatchHead(nn.Module):
    """LEGACY (legacy_chmean_v1; an ablation, not the default interface - amendment A1): tokens [B, C, P, E] -> unweighted
    channel mean -> LN -> Linear -> L2 per patch: [B, P, d]. Kept only to document and reproduce the legacy variant."""

    def __init__(self, E, d):
        super().__init__(); self.ln = nn.LayerNorm(E); self.lin = nn.Linear(E, d)

    def forward(self, tok):
        return F.normalize(self.lin(self.ln(tok.mean(1))), dim=-1)
