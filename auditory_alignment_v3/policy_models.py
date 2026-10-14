"""ALN3 D policy arms: rebuild the chosen B_DENSE / C_COMPLEMENT model from its best checkpoint (ADDENDUM_04 §2).

The construction repeats fm_dense.fit_dense / fm_complement.fit_complement up to the point where training starts, then loads
the chosen unit's best state strictly:
  B_DENSE      Backbone(architecture, adaptation) + DenseFM(readout); fixed audio head rebuilt as in fit_dense (target_stats of
               the unit's own batcher, seed + 5).
  C_COMPLEMENT lag_local_tokens base + FMContext(Backbone) + Complement(variant); fixed audio head loaded from the A_LOCAL base
               checkpoint recorded in the C unit's dependency, as in fit_complement.
FMBase gives both a common call (segment starts e0 [n], query offsets t [n, Q] in samples, optional C x C channel map M on the
EEG input; for the complement model M also maps the local patches) -> [n, Q, d] L2-normalised. FMReps is the ev1.Reps interface
(u: one forward per segment on the evaluation grid; va as fm_dense.DenseReps).
"""
from __future__ import annotations

import json
import os

import numpy as np
import torch
import torch.nn as nn

from . import core, fm_complement, fm_dense


class FMBase(nn.Module):
    def __init__(self, model, bt, kind):
        super().__init__()
        self.model, self.kind = model, kind
        self.bt = bt

    def forward(self, e0, t, M=None):
        bt = self.bt
        x = bt.context(e0)
        if M is not None:
            x = torch.einsum("dc,bcl->bdl", M, x)
        q = t.float() / bt.fs
        if self.kind == "dense":
            return self.model(x, q)
        n, Q = t.shape
        patches = bt.patches((e0[:, None] + t).reshape(-1))
        if M is not None:
            patches = [torch.einsum("dc,bcl->bdl", M, p) for p in patches]
        return self.model(patches, x, q).reshape(n, Q, -1)


class FMReps:
    """ev1.Reps interface for any callable f(e0 [n], t [n, Q]) -> [n, Q, d]."""

    def __init__(self, f, aud, bt, stride, chunk=8):
        self.f, self.aud, self.bt, self.chunk = f, aud, bt, chunk
        self.offs = np.arange(0, bt.seg_len, stride)

    @torch.no_grad()
    def u(self, e0s):
        e0s = np.asarray(e0s); out = []; dev = self.bt.dev
        t = torch.tensor(self.offs, device=dev)
        for k in range(0, len(e0s), self.chunk):
            e = torch.tensor(e0s[k:k + self.chunk], device=dev)
            out.append(self.f(e, t[None].expand(len(e), -1)).float().cpu().numpy())
        return np.concatenate(out)

    va = fm_dense.DenseReps.va


def build_chosen(pol, dev):
    """-> dict(base=FMBase (eval, frozen), head, bt, coh, bound=bound chosen row, record=chosen unit record, kind, d, grid)."""
    from auditory_alignment_v2.audio_targets import build_head, target_stats
    from auditory_alignment_v2.foundation_adapter import Backbone
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v2.temporal import build_encoder
    crow = pol["chosen_row"]; s = crow["spec"]
    rec = json.load(open(os.path.join(core.OUT, "units", f"{crow['experiment_id']}.json")))
    b = core.bind(crow); coh = load_cohort(b); g = core.grid_samples(coh.fs); d = int(s.get("projection_dim", 32))
    ck = os.path.join(core.REPO, pol["chosen_checkpoint"])
    if pol["candidate_family"] == "B_DENSE":
        kind = "dense"
        bb = Backbone(s["architecture"], coh.meta["dataset"], s["adaptation"], coh.fs)
        bt = fm_dense.DenseBatcher(coh, b["spec"], b, dev, g)
        model = fm_dense.DenseFM(bb, s["readout"], d, coh.fs, bt.seg_len, bt.ctx_len).to(dev)
        head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], target_stats(bt, np.random.default_rng(b["seed"] + 5))).to(dev)
    else:
        kind = "complement"
        bspec = dict(b["spec"]); bspec["architecture"] = "lag_local_tokens"; bspec["window"] = "full"
        bt = fm_dense.DenseBatcher(coh, bspec, b, dev, g)
        base = build_encoder("lag_local_tokens", coh.n_ch, d, bt.W, coh.fs).to(dev)
        head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], target_stats(bt, np.random.default_rng(b["seed"] + 5))).to(dev)
        sd_base = torch.load(os.path.join(core.REPO, rec["dependency"]["base_checkpoint"]), map_location=dev)
        head.load_state_dict(sd_base["head"], strict=True)
        ad, _ = fm_complement.VARIANT_FM[s["variant"]]
        bb = Backbone(s["architecture"], coh.meta["dataset"], "random_full" if ad == "random_frozen" else ad, coh.fs)
        ctx = fm_complement.FMContext(bb, coh.fs, bt.seg_len, bt.ctx_len).to(dev)
        model = fm_complement.Complement(base, ctx, s["variant"], d, base.n_tokens * 32).to(dev)
    model.load_state_dict(torch.load(ck, map_location=dev)["model"], strict=True)
    for p in list(model.parameters()) + list(head.parameters()):
        p.requires_grad_(False)
    model.eval(); head.eval()
    fb = FMBase(model, bt, kind).to(dev).eval()
    return {"base": fb, "head": head, "bt": bt, "coh": coh, "bound": b, "record": rec, "kind": kind, "d": d, "grid": g}
