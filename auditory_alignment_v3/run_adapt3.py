"""ALN3 D_ADAPT (lag_local_tokens arm; package docs/07 §3). dense_fm_policy / complement_policy arms wait for the
training-side model policy of B / C and are not bound here.

Base: the completed same-fold A_LOCAL lag_local_tokens full unit (same dataset, subject fold, content fold, seed, objective),
frozen. Adapters: none | input_spatial (C x C channel map, identity init) | output_low_rank (rank-4 residual on the d = 32
output, zero init). Per test participant, recording order: support = first 10% or 30%, query = the last 70% (the same query
for every support fraction and adapter). Updates use the unit's own objective on the support pairs (known sounds; not
zero-shot); the number of steps is chosen from {20, 50, 100} on TRAINING participants' early-stopping content split the same
way. Query evaluation on the dense grid: true vs within-query mismatched EEG over the full test candidate pool, readouts
fitted on training participants with the base model (unified and native) - the ALN2 C_ADAPT rule with the ALN3 contract.
"""
from __future__ import annotations

import json
import os
import time
import traceback

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import core

STEP_CANDIDATES = (20, 50, 100)
FRACTIONS = (0.1, 0.3)
QUERY_FROM = 0.3


class Adapted3(nn.Module):
    def __init__(self, base, kind, C, d):
        super().__init__()
        self.base, self.kind = base, kind
        for p in self.base.parameters():
            p.requires_grad_(False)
        self.M = nn.Parameter(torch.eye(C)) if kind == "input_spatial" else None
        if kind == "output_low_rank":
            self.A = nn.Parameter(torch.randn(4, d) * 0.1); self.B = nn.Parameter(torch.zeros(d, 4))

    def forward(self, x):
        if self.M is not None:
            x = [torch.einsum("dc,bcl->bdl", self.M, p) for p in x]
        u = self.base(x)
        return F.normalize(u + u @ self.A.T @ self.B.T, dim=-1) if self.kind == "output_low_rank" else u


def split_support_query(items, frac):
    n = len(items); q0 = int(round(QUERY_FROM * n)); s1 = max(1, int(round(frac * n)))
    return items[:s1], items[q0:]


def _gain(S_true, S_mm, own, tau):
    from auditory_alignment import evaluate as ev1
    a, b = ev1._metrics(S_true, own, tau), ev1._metrics(S_mm, own, tau)
    return {"gain_bits": b["logloss_bits"] - a["logloss_bits"], "rank_pct": a["rank_pct"], "top1": a["top1"], "n_query": int(len(own))}


def bundle(row, base_unit, base_ck, dev):
    from auditory_alignment import evaluate as ev1
    from auditory_alignment.train import Objective
    from auditory_alignment_v2.audio_targets import build_head, target_stats
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v2.temporal import build_encoder
    from .local_train import GridBatcher
    b = core.bind(base_unit["row"]); b["spec"]["architecture"] = "lag_local_tokens"; b["spec"]["window"] = "full"
    coh = load_cohort(b); g = core.grid_samples(coh.fs); d = int(row["spec"].get("projection_dim", 32))
    bt = GridBatcher(coh, b["spec"], b, dev, g)
    enc = build_encoder("lag_local_tokens", coh.n_ch, d, bt.W, coh.fs).to(dev)
    head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], target_stats(bt, np.random.default_rng(b["seed"] + 5))).to(dev)
    sd = torch.load(base_ck, map_location=dev); enc.load_state_dict(sd["enc"], strict=True); head.load_state_dict(sd["head"], strict=True); enc.eval()
    reps_of = lambda model: ev1.Reps(model, head, bt, stride=g)
    reps = reps_of(enc); C = coh.n_ch
    obj = Objective({"objective": row["spec"]["objective"], "config": {"temperature": 0.1}}, torch.zeros(4, d, device=dev), torch.zeros(4, d, device=dev))
    cal = base_unit["objective_calibration"]; obj.sigma_u, obj.sigma_v, obj.ridge_u, obj.ridge_v = cal["sigma_u"], cal["sigma_v"], cal["ridge_u"], cal["ridge_v"]

    def rows_of(segs_, rg):
        step = max(g, (bt.seg_len // 8) // g * g)
        t = (g * rg.integers(0, max(1, step // g), len(segs_))[:, None] + np.arange(8)[None] * step).reshape(-1); bb = np.repeat(np.arange(len(segs_)), 8)
        e0 = torch.tensor(np.array([s["e0"] for s in segs_])[bb] + t, device=dev); s0 = torch.tensor(np.array([s["s0"] for s in segs_])[bb] + t, device=dev)
        keys = torch.tensor(np.array([hash(s["uid"]) % (2 ** 31) for s in segs_])[bb] * 1000 + t, device=dev)
        return bt.patches(e0), head(bt.audio(s0)), keys

    def loss_fn(model, support, rg):
        x, v, keys = rows_of(support, rg)
        return obj(model(x).reshape(-1, d), v, keys=keys)[0]

    segs = coh.segments; rng = np.random.default_rng(b["seed"] + 1000)
    train_segs = [s for s in segs if s["p"] in bt.train_p and s["role"] in ("fit", "es") and s["kind"] == "ss"]
    ro = ev1.Readouts(row["spec"]["objective"], reps, train_segs, rng)

    def pool(role):
        uids, rows = {}, []
        for s in segs:
            if s["role"] == role and s["kind"] == "ss" and s["uid"] not in uids:
                uids[s["uid"]] = len(rows); rows.append(s)
        return uids, rows
    es_uid, es_rows = pool("es"); te_uid, te_rows = pool("test")
    q_es = [s for s in segs if s["p"] in bt.train_p and s["role"] == "es" and s["kind"] == "ss"]
    q_es = [q_es[i] for i in rng.choice(len(q_es), size=min(300, len(q_es)), replace=False)]
    Ve, Ae = reps.va([r["s0"] for r in es_rows]); Uq = reps.u([s["e0"] for s in q_es])
    ro.calibrate({"unified": ro.scores(Uq, Ve, Ae, "unified"), "native": ro.scores(Uq, Ve, Ae, "native")}, np.array([es_uid[s["uid"]] for s in q_es]))
    kind = row["spec"]["adapter"]

    def evaluate_query(model, query, uid, Vc, Ac):
        Uq = reps_of(model).u([s["e0"] for s in query]); own = np.array([uid[s["uid"]] for s in query]); Umm = np.roll(Uq, 1, axis=0)
        return {kr: _gain(ro.scores(Uq, Vc, Ac, kr), ro.scores(Umm, Vc, Ac, kr), own, ro.tau[kr]) for kr in ("unified", "native")}

    def adapt_for(support, steps, seed):
        m = Adapted3(enc, kind, C, d).to(dev)
        params = [p for p in m.parameters() if p.requires_grad]
        if kind != "none" and params and steps:
            m.train(); opt = torch.optim.Adam(params, lr=1e-3); rg = np.random.default_rng(seed)
            for _ in range(steps):
                loss = loss_fn(m, support, rg); opt.zero_grad(); loss.backward(); opt.step()
            m.eval()
        return m
    steps_choice = {"chosen": 0, "scores": {}}
    if kind != "none":
        tp = sorted({s["p"] for s in q_es})[:8]
        for S in STEP_CANDIDATES:
            gg = []
            for p in tp:
                ps = sorted([s for s in segs if s["p"] == p and s["role"] == "es" and s["kind"] == "ss"], key=lambda s: s["e0"])
                if len(ps) < 6:
                    continue
                sup, qry = split_support_query(ps, 0.3)
                with torch.enable_grad():
                    m = adapt_for(sup, S, p)
                gg.append(evaluate_query(m, qry, es_uid, Ve, Ae)["native"]["gain_bits"])
            steps_choice["scores"][S] = float(np.mean(gg)) if gg else None
        steps_choice["chosen"] = max((s for s in steps_choice["scores"] if steps_choice["scores"][s] is not None), key=lambda s: steps_choice["scores"][s])
    Vc, Ac = reps.va([r["s0"] for r in te_rows])
    per = {}
    test_p = sorted({s["p"] for s in segs if s["role"] == "test" and coh.participants[s["p"]]["fold"] == row["subject_fold"]})
    for p in test_p:
        q = sorted([s for s in segs if s["p"] == p and s["role"] == "test" and s["kind"] == "ss"], key=lambda s: s["e0"])
        if len(q) < 6:
            continue
        rr = {"group": coh.participants[p]["group"], "n_segments": len(q)}
        for f in FRACTIONS:
            sup, qry = split_support_query(q, f)
            with torch.enable_grad():
                m = adapt_for(sup, steps_choice["chosen"], p)
            rr[f"support_{f}"] = {**evaluate_query(m, qry, te_uid, Vc, Ac), "n_support": len(sup)}
        per[coh.participants[p]["id"]] = rr
    return {"per_participant": per, "steps": steps_choice, "grid_samples": g, "query_rule": "last 70% of each participant's test segments (recording order)"}


def run(row, out, epochs=None):
    from .run_complement import base_ready
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    if row["spec"]["architecture"] != "lag_local_tokens":
        print("technical_pending (model policy arm waits for B/C training-side policy)", row["experiment_id"]); return
    probe = dict(row); probe["spec"] = {**row["spec"], "local_architecture": "lag_local_tokens", "window": "full"}
    br = base_ready(probe, core.load_rows(), out)
    if br is None:
        print("technical_pending (same-fold local base not complete)", row["experiment_id"]); return
    b_row, b_path, b_ck = br
    t0 = time.time(); b = core.bind(row); rec = core.new_record(row, b, out)
    rec["dependency"] = {"base_same_fold": b_row["experiment_id"], "base_checkpoint": os.path.relpath(b_ck, core.REPO)}
    try:
        rec["eval"] = bundle(row, json.load(open(b_path)), b_ck, torch.device("cuda")); rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
