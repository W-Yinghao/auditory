"""ALN3 D_ADAPT policy arms dense_fm_policy / complement_policy (ADDENDUM_04 §2; package docs/07 §3).

Base: the unit chosen by the training-only model policy (policy.py), rebuilt from its best checkpoint (policy_models.py) and
frozen; it stays in eval mode while adapters are updated. Adapters as for the lag_local_tokens arm (run_adapt3): none |
input_spatial (C x C channel map, identity init, on the EEG input; for the complement model also on its local patches) |
output_low_rank (rank-4 residual on the d = 32 output, zero init). Protocol unchanged from run_adapt3: per test participant in
recording order support = first 10 % or 30 %, query = last 70 %; updates use the unit's own objective on the support pairs (known
sounds); the number of steps is chosen from {20, 50, 100} on training participants' early-stopping content split the same way;
query evaluation on the dense grid against the full test candidate pool with readouts fitted on training participants with the
base model (unified and native).
"""
from __future__ import annotations

import os
import time
import traceback

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import core, policy
from .run_adapt3 import FRACTIONS, STEP_CANDIDATES, _gain, split_support_query


class AdaptedFM(nn.Module):
    def __init__(self, base, kind, C, d):
        super().__init__()
        self.base, self.kind = base, kind
        for p in self.base.parameters():
            p.requires_grad_(False)
        self.M = nn.Parameter(torch.eye(C)) if kind == "input_spatial" else None
        if kind == "output_low_rank":
            self.A = nn.Parameter(torch.randn(4, d) * 0.1); self.B = nn.Parameter(torch.zeros(d, 4))

    def train(self, mode=True):  # the frozen base never leaves eval mode
        super().train(mode); self.base.eval(); return self

    def forward(self, e0, t):
        u = self.base(e0, t, self.M)
        return F.normalize(u + u @ self.A.T @ self.B.T, dim=-1) if self.kind == "output_low_rank" else u


def bundle(row, pol, dev):
    from auditory_alignment import evaluate as ev1
    from auditory_alignment.train import Objective
    from .policy_models import FMReps, build_chosen
    m0 = build_chosen(pol, dev)
    fb, head, bt, coh, b, g, d = m0["base"], m0["head"], m0["bt"], m0["coh"], m0["bound"], m0["grid"], m0["d"]
    reps_of = lambda f: FMReps(f, head, bt, g)
    reps = reps_of(fb); C = coh.n_ch
    obj = Objective({"objective": row["spec"]["objective"], "config": {"temperature": 0.1}}, torch.zeros(4, d, device=dev), torch.zeros(4, d, device=dev))
    cal = m0["record"]["objective_calibration"]; obj.sigma_u, obj.sigma_v, obj.ridge_u, obj.ridge_v = cal["sigma_u"], cal["sigma_v"], cal["ridge_u"], cal["ridge_v"]

    def rows_of(segs_, rg):
        step = max(g, (bt.seg_len // 8) // g * g)
        t = g * rg.integers(0, max(1, step // g), len(segs_))[:, None] + np.arange(8)[None] * step
        tt = torch.tensor(t, device=dev)
        e0 = torch.tensor(np.array([s["e0"] for s in segs_]), device=dev)
        s0 = (torch.tensor(np.array([s["s0"] for s in segs_]), device=dev)[:, None] + tt).reshape(-1)
        keys = (torch.tensor(np.array([hash(s["uid"]) % (2 ** 31) for s in segs_]), device=dev)[:, None] * 1000 + tt).reshape(-1)
        return e0, tt, head(bt.audio(s0)), keys

    def loss_fn(model, support, rg):
        e0, tt, v, keys = rows_of(support, rg)
        return obj(model(e0, tt).reshape(-1, d), v, keys=keys)[0]

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
        torch.manual_seed(int(seed) % (2 ** 31))
        m = AdaptedFM(fb, kind, C, d).to(dev)
        params = [p for n, p in m.named_parameters() if p.requires_grad and not n.startswith("base.")]
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
    return {"per_participant": per, "steps": steps_choice, "grid_samples": g, "base_model": m0["kind"],
            "query_rule": "last 70% of each participant's test segments (recording order)"}


def run(row, out, epochs=None):
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    pol = policy.resolve(row, core.load_rows(), core.OUT)  # candidates are the fleet's B/C units (also when out is a probe dir)
    if pol is None:
        print("technical_pending (training-only model policy not resolvable)", row["experiment_id"]); return
    t0 = time.time(); b = core.bind(row); rec = core.new_record(row, b, out)
    rec["policy"] = {k: v for k, v in pol.items() if k != "chosen_row"}; rec["policy"]["chosen_spec"] = pol["chosen_row"]["spec"]
    rec["dependency"] = {"policy_chosen": pol["chosen"], "chosen_checkpoint": pol["chosen_checkpoint"]}
    try:
        rec["eval"] = bundle(row, pol, torch.device("cuda")); rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
