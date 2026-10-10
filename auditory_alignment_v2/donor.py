"""ALN2 public auditory donors: continued training of a foundation backbone on public paired sound-EEG alignment
(package docs/04 §4.5 'public paired objective'; docs/05 §5.7 donor definition).

A donor is defined by (architecture, trainable depth, source cohorts, seed):
  - B_AUDITORY_CONTINUE donors for target cohort T use only the OTHER public cohorts (FAU target: DTU + Federici; DTU
    target: FAU + Federici), so they never contain a participant or stimulus of T and are safe for every outer fold of T.
  - D_FM_PUBLIC donors use all three public cohorts (no private child).
Training: all participants and all speech segments of the sources (single-speaker; each source cohort with its own target:
FAU / DTU Local from content fold 0, Federici envelope), one shared EEG backbone + one spatial readout per cohort layout (amendment A1), per-cohort fixed
audio heads, per-cohort REVE electrode positions; round-robin cohort batches; reference NCE (temperature 0.1);
AdamW with the target-free B_FM recipe (arch, pretrained_<depth>, first source, NCE); DONOR_EPOCHS passes; the final
state is the donor (no target information is available to select on). Records sources, counts, steps and curves.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time

import numpy as np
import torch

from auditory_alignment.train import Objective
from .foundation_adapter import Backbone
from .train_fm import FMEncoder, SegmentAudioHead, SegmentBatcher, param_groups, seg_target_stats

DONOR_EPOCHS = 20
TARGET_OF = {"fau": "local", "dtu": "local", "federici": "envelope"}


def donor_id(arch, depth, sources, seed):
    return f"donor__{arch}__{depth}__{'+'.join(sorted(sources))}__s{seed}"


def sources_for(family, target):
    if family == "D_FM_PUBLIC":
        return ["dtu", "fau", "federici"]
    return [c for c in ("dtu", "fau", "federici") if c != target]


def train_donor(arch, depth, sources, seed, out, lr_backbone, lr_head, epochs=DONOR_EPOCHS):
    from .run import load_cohort
    did = donor_id(arch, depth, sources, seed)
    d_dir = os.path.join(out, "donors"); os.makedirs(d_dir, exist_ok=True)
    path = os.path.join(d_dir, did + ".pt")
    if os.path.exists(path):
        return path
    dev = torch.device("cuda"); torch.manual_seed(seed); rng = np.random.default_rng(seed)
    adaptation = "pretrained_full" if depth == "full" else "pretrained_partial"
    bbs, bts, heads, objs, info = {}, {}, {}, {}, {}
    shared = None
    for ds in sources:
        row = {"dataset": ds, "subject_fold": None, "content_fold": 0, "seed": seed,
               "spec": {"architecture": arch, "objective": "NCE", "target": TARGET_OF[ds], "training_task": "paired_alignment"}}
        coh = load_cohort(row)
        bb = Backbone(arch, ds, adaptation, coh.fs)
        if shared is None:
            shared = bb
        else:
            bb.net = shared.net  # one backbone; cohort-specific input contract (positions) kept by the wrapper
        bbs[ds] = bb
        bt = SegmentBatcher(coh, row["spec"], row, dev, bb.patch_starts(int(round(coh.meta["seg_len"] * 200 / coh.fs))))
        bt.fit = [i for i, s in enumerate(coh.segments) if s["kind"] == "ss" and s["p"] in bt.train_p]  # all content of the source
        bts[ds] = bt
        heads[ds] = SegmentAudioHead(bt.nbin * bt.S.shape[0], 16, *seg_target_stats(bt, np.random.default_rng(seed + 5)), ds).to(dev)
        info[ds] = {"participants": len(bt.train_p), "segments": len(bt.fit), "fs": coh.fs, "content_fold_targets": 0}
    from .fm_readout import HEAD_VERSION, make_head
    eheads = {ds: make_head(bbs[ds]).to(dev) for ds in bts}  # one spatial readout per cohort channel layout (amendment A1)
    for bb in bbs.values():
        bb.to(dev)
    bbp = [p for p in shared.net.parameters() if p.requires_grad]; hdp = [p for h in eheads.values() for p in h.parameters()]
    groups, params = [{"params": bbp, "lr": lr_backbone}, {"params": hdp, "lr": lr_head}], bbp + hdp
    opt = torch.optim.AdamW(groups, weight_decay=1e-4)
    n_seg = 32
    steps_per_epoch = sum(max(1, len(bt.fit) // n_seg) for bt in bts.values())
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    for ds, bt in bts.items():
        with torch.no_grad():
            b = next(bt.epoch_batches(np.random.default_rng(seed + 99), n_seg)); r0 = bt.seg_rows(b)
            u0 = eheads[ds](bbs[ds](bt.segments(r0[0]))).reshape(-1, 16); v0 = heads[ds](bt.audio_patches(r0[1])).reshape(-1, 16)
        objs[ds] = Objective({"objective": "NCE", "config": {"temperature": 0.1}}, u0, v0)
    curve, t0, step = [], time.time(), 0
    for ep in range(epochs):
        shared.train(); [h.train() for h in eheads.values()]; its = {ds: bt.epoch_batches(rng, n_seg) for ds, bt in bts.items()}; live = list(its); tl = {ds: [] for ds in its}
        while live:
            for ds in list(live):
                b = next(its[ds], None)
                if b is None:
                    live.remove(ds); continue
                rws = bts[ds].seg_rows(b)
                u = eheads[ds](bbs[ds](bts[ds].segments(rws[0]))).reshape(-1, 16); v = heads[ds](bts[ds].audio_patches(rws[1])).reshape(-1, 16)
                loss, _ = objs[ds](u, v, keys=rws[2])
                opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(params, 5.0)
                if torch.isfinite(loss):
                    opt.step(); sched.step(); step += 1; tl[ds].append(float(loss))
        curve.append({"epoch": ep + 1, **{f"loss_{ds}": float(np.mean(v)) if v else None for ds, v in tl.items()}, "seconds": round(time.time() - t0, 1)})
    torch.save({"net": shared.net.state_dict()}, path + ".tmp"); os.replace(path + ".tmp", path)
    rec = {"donor_id": did, "arch": arch, "depth": depth, "sources": sources, "seed": seed, "epochs": epochs, "optimizer_steps": step,
           "lr_backbone": lr_backbone, "lr_head": lr_head, "source_info": info, "curve": curve, "objective": "NCE (temperature 0.1), per-cohort fixed audio heads",
           "selection": "final state (no target information used)", "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()[:16],
           "backbone_contract": shared.contract(), "readout_head": HEAD_VERSION + " (one per source cohort; not part of the donor)"}
    json.dump(rec, open(os.path.join(d_dir, did + ".json"), "w"), indent=1, default=float)
    return path
