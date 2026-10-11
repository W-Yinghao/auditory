"""ALN3 private dependent families (package docs/08): E_COMPLEMENT and E_DISTILL.

Shared: models of completed units are rebuilt from their best checkpoints (E_LOCAL: local encoder d = 32 + prototypes;
E_GENERIC: repaired channel-aware EpochEncoder d = 32; ALN2 D_FM_PUBLIC: repaired EpochEncoder d = 16 on the public-auditory
donor). Native score per trial: NCE cos(u,p1) - cos(u,p0); CS log-odds of the class-kernel posterior against the training
children's early-stopping trials (ALN2 rule). Probabilities = positive-slope affine calibration of the native score on the
training children's early-stopping blocks (calib.py / package reference calibrator). Test children are never used.

E_COMPLEMENT (logit space): base = same-fold E_LOCAL lag_local_tokens full unit, frozen; base logit = calibrated native score.
  Context branch: Backbone (CBraMod / REVE; residual_pretrained_frozen | _peft | residual_random_trainable) on the full private
  epoch (-200..600 ms, zero-padded; ALN2 contract) -> ChannelSpatialProjection (package reference) -> 64 features.
  logit = base_logit + ZeroResidualPrediction([u_base; ctx]) (zero-initialised: identical to the base at initialisation);
  trained with binary cross-entropy on the training children's fit trials (true labels), checkpoint by early-stopping-block
  loss each epoch, then one positive affine recalibration of the combined logit on the early-stopping blocks.
E_DISTILL: student = lag_local_tokens on the declared window (early / late / full), the unit's task objective (NCE / CS) plus
  lambda * KL(p_teacher || p_student) on the training children's trials; p_student from a student logit head (NCE: affine of the
  prototype score, CS: linear head on u). Teacher policy -> candidate units of the same outer fold / seed / objective, chosen by
  their recorded training-side early-stopping selection score (lower is better): local_teacher = E_LOCAL units;
  generic_pretrained_teacher = E_GENERIC units; auditory_adapted_teacher = ALN2 D_FM_PUBLIC units (public donor, no private
  child); legacy_full_teacher_control = ALN2 D_FM_PUBLIC auditory_pretrained_full units. lambda in {0.1, 1.0} chosen on the
  training side; lambda = 0 (no distillation) is trained and reported in every unit as the complete baseline. At inference
  the student reads only its declared window; the teacher is not used.
"""
from __future__ import annotations

import json
import math
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import core

LL = lambda q, y: np.where(y == 1, np.log2(np.clip(q, 1e-12, 1)), np.log2(np.clip(1 - q, 1e-12, 1)))


def metrics(p, y, base):
    from auditory_alignment.evaluate import _auc
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {"auc": _auc(p, y), "nll_bits": float(-LL(p, y).mean()), "brier": float(((p - y) ** 2).mean()),
            "gain_vs_base_bits": float((LL(p, y) - LL(np.full(len(y), base), y)).mean()), "n": int(len(y))}


def unit_paths(eid):
    for out in (core.OUT, core.V2_OUT):
        p = os.path.join(out, "units", f"{eid}.json")
        if os.path.exists(p):
            return out, p
    return None, None


def rebuild(eid, kids, dev):
    """(kind, encoder, protos, record, input) for a completed private unit; input 'local' (PrivateBatcher windows) or 'epoch'."""
    from auditory_alignment_v2.foundation_adapter import Backbone
    from auditory_alignment_v2.temporal import build_encoder
    out, p = unit_paths(eid); r = json.load(open(p)); row = r["row"]; fam = row["family_id"]
    sd = torch.load(os.path.join(out, "ckpt", f"{eid}_best.pt"), map_location=dev)
    if fam in ("E_LOCAL", "D_TASK_LOCAL"):
        from auditory_alignment_v2.train import PrivateBatcher
        d = 32 if fam == "E_LOCAL" else 16; b = core.bind(row) if fam == "E_LOCAL" else row
        bt = PrivateBatcher(kids, b["spec"], b, dev); enc = build_encoder(b["spec"]["architecture"], 20, d, bt.W, 250).to(dev)
        enc.load_state_dict(sd["enc"], strict=True); enc.eval(); return enc, sd.get("protos"), r, bt
    from auditory_alignment_v2.train_fm import PrivateFMBatcher
    if fam == "E_GENERIC":
        from .local_train import EpochEncoder
        b = core.bind(row); enc = EpochEncoder(Backbone(row["spec"]["architecture"], "private_bdf", row["spec"]["adaptation"], 250), 32).to(dev)
    else:  # ALN2 D_FM_PUBLIC (repaired, d = 16)
        from auditory_alignment_v2.train_fm import EpochEncoder as E2
        b = row; enc = E2(Backbone(row["spec"]["architecture"], "private_bdf", row["spec"]["adaptation"], 250)).to(dev)
    bt = PrivateFMBatcher(kids, b["spec"], b, dev)
    enc.load_state_dict(sd["enc"], strict=True); enc.eval(); return enc, sd.get("protos"), r, bt


@torch.no_grad()
def native_scores(enc, protos, rec, bt, kids, idx_children):
    """native score for every trial of the given children (dict child -> [n])."""
    from auditory_alignment.evaluate import _private_reps
    U = {i: _private_reps(enc, bt, i) for i in idx_children}
    obj = rec["row"]["spec"]["objective"]
    if obj == "NCE":
        P = F.normalize(protos.float().cpu(), dim=1).numpy()
        return {i: ((U[i] / np.linalg.norm(U[i], axis=1, keepdims=True)) @ P.T) @ np.array([-1.0, 1.0]) for i in U}
    tr = [i for i in idx_children if kids[i]["fold"] != rec["row"]["subject_fold"]]
    yr = np.concatenate([kids[i]["y"][kids[i]["es_mask"]] for i in tr]); Xr = np.concatenate([U[i][kids[i]["es_mask"]] for i in tr])
    base = float(np.concatenate([kids[i]["y"] for i in tr]).mean())
    sel = np.random.default_rng(rec["row"]["seed"] + 77).choice(len(Xr), size=min(6000, len(Xr)), replace=False)
    Xs, ys = torch.tensor(Xr[sel], dtype=torch.float64), torch.tensor(yr[sel], dtype=torch.float64); s2 = 2 * rec["objective_calibration"]["sigma_u"] ** 2
    out = {}
    for i in U:
        K = torch.exp(-torch.cdist(torch.tensor(U[i], dtype=torch.float64), Xs).pow(2) / s2)
        q = np.clip(((K @ ys + base) / (K.sum(1) + 1.0)).numpy(), 1e-6, 1 - 1e-6); out[i] = np.log(q) - np.log1p(-q)
    return out


def calibrator(S, kids, tr):
    from .aln3_reference.calibration import AffineLogitCalibrator
    sr = np.concatenate([S[i][kids[i]["es_mask"]] for i in tr]); yr = np.concatenate([kids[i]["y"][kids[i]["es_mask"]] for i in tr])
    return AffineLogitCalibrator.fit(sr, yr)
