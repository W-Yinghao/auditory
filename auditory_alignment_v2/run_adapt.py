"""ALN2 C_ADAPT runner (adaptation bundles; see adapt.py for the design). Usage:
  python -m auditory_alignment_v2.run_adapt --job-index <i>
A bundle = one outer model x one adapter kind: per test participant, support fractions 0.1 and 0.3 on a fixed query (last
70%). Exits technical_pending when the base unit is not complete yet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import traceback

import numpy as np
import torch
import torch.nn.functional as F

from .run import OUT, PLAN, REPO, canonical, load_cohort, load_row

ADAPT_CODE = [("auditory_alignment_v2", f) for f in ("adapt.py", "run_adapt.py", "train.py", "train_fm.py", "foundation_adapter.py", "fm_readout.py", "eval_fm.py",
                                                     "audio_targets.py", "temporal.py", "evaluate.py")] + \
             [("auditory_alignment", f) for f in ("data.py", "evaluate.py", "losses.py", "losses_reference.py", "train.py")]


def code_hash():
    h = hashlib.sha256()
    for d, f in ADAPT_CODE:
        h.update(open(os.path.join(REPO, d, f), "rb").read())
    return h.hexdigest()[:16]


def base_row(row, plan):
    s = row["spec"]; ds = row["dataset"]; arch = s["architecture"]; obj = s["objective"]
    same = lambda r: r["dataset"] == ds and r["subject_fold"] == row["subject_fold"] and r["content_fold"] == row["content_fold"] and r["seed"] == row["seed"] and r["spec"]["objective"] == obj
    for r in plan:
        if not same(r):
            continue
        rs = r["spec"]
        if arch == "density_tokens" and ds != "private_bdf" and r["family_id"] == "A_TIME" and rs["architecture"] == "density_tokens" and rs["window"] == "full":
            return r
        if arch == "density_tokens" and ds == "private_bdf" and r["family_id"] == "D_TASK_LOCAL" and rs["architecture"] == "density_tokens" and rs["window"] == "full":
            return r
        if arch == "cbramod" and r["family_id"] in ("B_FM", "D_FM_GENERIC") and rs["architecture"] == "cbramod" and rs["adaptation"] == "pretrained_peft":
            return r
    return None


def resolve_unit(eid, out):
    p = os.path.join(out, "units", f"{eid}.json")
    if not os.path.exists(p):
        return None, None
    r = json.load(open(p))
    if r.get("status") != "complete":
        return None, None
    if "reuse_of" in r:
        return resolve_unit(r["reuse_of"], out)
    k = r.get("chosen_candidate"); ck = os.path.join(out, "ckpt", f"{eid}_best.pt")
    if k is not None and "candidates" in r:
        ci = [c["candidate"] for c in r["candidates"]].index(k); ck = os.path.join(out, "ckpt", f"{eid}_c{ci}_best.pt")
    return r, ck


def _gain(S_true, S_mm, own, tau):
    from auditory_alignment import evaluate as ev1
    a = ev1._metrics(S_true, own, tau); b = ev1._metrics(S_mm, own, tau)
    return {"gain_bits": b["logloss_bits"] - a["logloss_bits"], "rank_pct": a["rank_pct"], "top1": a["top1"], "n_query": int(len(own))}


def continuous_bundle(row, brow, brec, ck, dev, out):
    from auditory_alignment import evaluate as ev1
    from auditory_alignment.train import Objective
    from .adapt import FRACTIONS, STEP_CANDIDATES, Adapted, adapt_steps, split_support_query
    from .audio_targets import build_head, target_stats
    from .temporal import build_encoder
    from .train import Batcher
    coh = load_cohort(brow); spec = brow["spec"]; arch = spec["architecture"]
    sd = torch.load(ck, map_location=dev)
    if arch == "density_tokens":
        bt = Batcher(coh, spec, brow, dev)
        enc = build_encoder(arch, coh.n_ch, 16, bt.W, coh.fs).to(dev)
        head = build_head("fixed_features", bt.audio_dim, 16, coh.meta["dataset"], target_stats(bt, np.random.default_rng(brow["seed"] + 5))).to(dev)
        enc.load_state_dict(sd["enc"]); head.load_state_dict(sd["head"]); reps = ev1.Reps(enc, head, bt); C = coh.n_ch
        def rows_of(segs_, g):  # anchors of support segments
            step = bt.seg_len // 8; t = (g.integers(0, step, len(segs_))[:, None] + np.arange(8)[None] * step).reshape(-1); b = np.repeat(np.arange(len(segs_)), 8)
            e0 = torch.tensor(np.array([s["e0"] for s in segs_])[b] + t, device=dev); s0 = torch.tensor(np.array([s["s0"] for s in segs_])[b] + t, device=dev)
            keys = torch.tensor(np.array([hash(s["uid"]) % (2 ** 31) for s in segs_])[b] * 1000 + t, device=dev)
            return bt.patches(e0), head(bt.audio(s0)), keys
        def make_reps(model):
            return ev1.Reps(model, head, bt)
    else:
        from .eval_fm import SegmentReps
        from .foundation_adapter import Backbone
        from .train_fm import FMEncoder, SegmentAudioHead, SegmentBatcher, seg_target_stats
        bb = Backbone("cbramod", coh.meta["dataset"], "pretrained_peft", coh.fs); enc = FMEncoder(bb).to(dev)
        bt = SegmentBatcher(coh, spec, brow, dev, bb.patch_starts(int(round(coh.meta["seg_len"] * 200 / coh.fs))))
        head = SegmentAudioHead(bt.nbin * bt.S.shape[0], 16, *seg_target_stats(bt, np.random.default_rng(brow["seed"] + 5)), coh.meta["dataset"]).to(dev)
        enc.load_state_dict(sd["enc"]); reps = SegmentReps(enc, head, bt); C = coh.n_ch
        def rows_of(segs_, g):
            e0 = torch.tensor([s["e0"] for s in segs_], device=dev); s0 = torch.tensor([s["s0"] for s in segs_], device=dev)
            keys = (torch.tensor([hash(s["uid"]) % (2 ** 31) for s in segs_], device=dev)[:, None] * 100 + torch.arange(len(bt.starts), device=dev)[None]).reshape(-1)
            return bt.segments(e0), head(bt.audio_patches(s0)).reshape(-1, 16), keys
        def make_reps(model):
            return SegmentReps(model, head, bt)
    enc.eval()
    obj = Objective({"objective": spec["objective"], "config": {"temperature": 0.1}}, torch.zeros(4, 16, device=dev), torch.zeros(4, 16, device=dev))
    cal = brec["objective_calibration"]; obj.sigma_u, obj.sigma_v, obj.ridge_u, obj.ridge_v = cal["sigma_u"], cal["sigma_v"], cal["ridge_u"], cal["ridge_v"]
    def loss_fn(model, support, g):
        x, v, keys = rows_of(support, g)
        u = model(x).reshape(-1, 16)
        return obj(u, v, keys=keys)[0]
    segs = coh.segments
    rng = np.random.default_rng(brow["seed"] + 1000)
    train_segs = [s for s in segs if s["p"] in bt.train_p and s["role"] in ("fit", "es") and s["kind"] == "ss"]
    ro = ev1.Readouts(spec["objective"] if spec["objective"] != "SELECTION_CE" else "NCE", reps, train_segs, rng)
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
    kind = row["spec"]["adapter_kind"]

    def evaluate_query(model, query, uid, Vc, Ac):
        Uq = make_reps(model).u([s["e0"] for s in query]); own = np.array([uid[s["uid"]] for s in query]); Umm = np.roll(Uq, 1, axis=0)
        return {kr: _gain(ro.scores(Uq, Vc, Ac, kr), ro.scores(Umm, Vc, Ac, kr), own, ro.tau[kr]) for kr in ("unified", "native")}

    def adapt_for(support, steps, seed):
        m = Adapted(enc, kind, C, "segment" if arch == "cbramod" else "patches").to(dev)
        if kind != "none":
            m.train(); adapt_steps(m, loss_fn, support, steps, seed=seed); m.eval()
        return m
    # steps: training participants' early-stopping content, support 0.3 / query 0.7, mean native gain
    steps_choice = {"chosen": 0, "scores": {}}
    if kind != "none":
        tp = sorted({s["p"] for s in q_es})[:8]
        for S in STEP_CANDIDATES:
            g = []
            for p in tp:
                ps = sorted([s for s in segs if s["p"] == p and s["role"] == "es" and s["kind"] == "ss"], key=lambda s: s["e0"])
                if len(ps) < 6:
                    continue
                sup, qry = split_support_query(ps, 0.3)
                with torch.enable_grad():
                    m = adapt_for(sup, S, p)
                g.append(evaluate_query(m, qry, es_uid, Ve, Ae)["native"]["gain_bits"])
            steps_choice["scores"][S] = float(np.mean(g)) if g else None
        steps_choice["chosen"] = max((s for s in steps_choice["scores"] if steps_choice["scores"][s] is not None), key=lambda s: steps_choice["scores"][s])
    Vc, Ac = reps.va([r["s0"] for r in te_rows])
    per = {}
    test_p = sorted({s["p"] for s in segs if s["role"] == "test" and coh.participants[s["p"]]["fold"] == row["subject_fold"]})
    for p in test_p:
        q = sorted([s for s in segs if s["p"] == p and s["role"] == "test" and s["kind"] == "ss"], key=lambda s: s["e0"])
        if len(q) < 6:
            continue
        rec = {"group": coh.participants[p]["group"], "n_segments": len(q)}
        for f in FRACTIONS:
            sup, qry = split_support_query(q, f)
            with torch.enable_grad():
                m = adapt_for(sup, steps_choice["chosen"], p)
            rec[f"support_{f}"] = {**evaluate_query(m, qry, te_uid, Vc, Ac), "n_support": len(sup)}
        per[coh.participants[p]["id"]] = rec
    return {"per_participant": per, "steps": steps_choice, "query_rule": "last 70% of each participant's test segments (recording order)"}


def private_bundle(row, brow, brec, ck, dev, out):
    from auditory_alignment import data
    from auditory_alignment import evaluate as ev1
    from auditory_alignment.train import Objective
    from sklearn.linear_model import LogisticRegression
    from .adapt import FRACTIONS, STEP_CANDIDATES, Adapted, adapt_steps, split_support_query
    spec = brow["spec"]; arch = spec["architecture"]; kids = data.load_private(); sd = torch.load(ck, map_location=dev)
    if arch == "density_tokens":
        from .temporal import build_encoder
        from .train import PrivateBatcher
        bt = PrivateBatcher(kids, spec, brow, dev); enc = build_encoder(arch, 20, 16, bt.W, 250).to(dev)
    else:
        from .foundation_adapter import Backbone
        from .train_fm import EpochEncoder, PrivateFMBatcher
        bt = PrivateFMBatcher(kids, spec, brow, dev); enc = EpochEncoder(Backbone("cbramod", "private_bdf", "pretrained_peft", 250)).to(dev)
    enc.load_state_dict(sd["enc"]); enc.eval(); protos = sd["protos"].to(dev)
    obj = Objective({"objective": spec["objective"], "config": {"temperature": 0.1}}, torch.zeros(4, 16, device=dev), None, labels0=torch.zeros(4, device=dev))
    cal = brec["objective_calibration"]; obj.sigma_u, obj.ridge_u, obj.ridge_v = cal["sigma_u"], cal["ridge_u"], cal["ridge_v"]
    kind = row["spec"]["adapter_kind"]

    def emb(model, i, idx):
        out_ = []
        for a in range(0, len(idx), 1024):
            out_.append(model(bt.patches(i, torch.tensor(idx[a:a + 1024], device=dev))))
        return torch.cat(out_)

    def loss_fn(model, support, g):
        i, idx = support; take = g.choice(idx, size=min(256, len(idx)), replace=False)
        u = model(bt.patches(i, torch.tensor(take, device=dev)))
        return obj(u, labels=torch.tensor(kids[i]["y"][take], device=dev), prototypes=protos)[0]

    def score(model, i, sup, qry):
        """Readout identical for every adapter kind: native score (prototype logit / kernel score over the support) with a
        2-parameter Platt calibration fitted on the support trials; AUC and log loss on the query."""
        with torch.no_grad():
            Us, Uq = emb(model, i, sup), emb(model, i, qry)
            if spec["objective"] == "NCE":
                P = F.normalize(protos, dim=1); zs = (Us @ P.T); zq = (Uq @ P.T); zs, zq = (zs[:, 1] - zs[:, 0]).cpu().numpy(), (zq[:, 1] - zq[:, 0]).cpu().numpy()
            else:
                ys = torch.tensor(kids[i]["y"][sup], dtype=torch.float64, device=dev); s2 = 2 * cal["sigma_u"] ** 2
                def ks(U):
                    K = torch.exp(-torch.cdist(U.double(), Us.double()).pow(2) / s2)
                    return ((K @ ys + 1.0) / (K.sum(1) + 2.0)).cpu().numpy()
                zs, zq = ks(Us), ks(Uq)
        y_s, y_q = kids[i]["y"][sup], kids[i]["y"][qry]
        if 0 < y_s.sum() < len(y_s):
            pl = LogisticRegression(C=1.0).fit(zs[:, None], y_s); p = np.clip(pl.predict_proba(zq[:, None])[:, 1], 1e-6, 1 - 1e-6)
        else:
            p = np.full(len(y_q), np.clip(y_s.mean(), 1e-3, 1 - 1e-3))
        ll = np.where(y_q == 1, -np.log2(p), -np.log2(1 - p))
        return {"auc": ev1._auc(zq, y_q), "logloss_bits": float(ll.mean()), "n_query": int(len(y_q))}

    def adapt_for(i, sup, steps, seed):
        m = Adapted(enc, kind, 20, "patches").to(dev)
        if kind != "none":
            m.train(); adapt_steps(m, loss_fn, (i, sup), steps, seed=seed); m.eval()
        return m
    steps_choice = {"chosen": 0, "scores": {}}
    if kind != "none":
        for S in STEP_CANDIDATES:
            v = []
            for i in bt.train[:8]:
                idx = np.flatnonzero(kids[i]["es_mask"])
                if len(idx) < 50:
                    continue
                sup, qry = split_support_query(idx, 0.3)
                with torch.enable_grad():
                    m = adapt_for(i, sup, S, i)
                v.append(-score(m, i, sup, qry)["logloss_bits"])
            steps_choice["scores"][S] = float(np.mean(v)) if v else None
        steps_choice["chosen"] = max((s for s in steps_choice["scores"] if steps_choice["scores"][s] is not None), key=lambda s: steps_choice["scores"][s])
    per = {}
    for i, k in enumerate(kids):
        if k["fold"] != row["subject_fold"]:
            continue
        idx = np.arange(len(k["y"])); rec = {"group": k["group"], "n_trials": int(len(idx))}
        for f in FRACTIONS:
            sup, qry = split_support_query(idx, f)
            with torch.enable_grad():
                m = adapt_for(i, sup, steps_choice["chosen"], i)
            rec[f"support_{f}"] = {**score(m, i, sup, qry), "n_support": int(len(sup))}
        per[k["id"]] = rec
    return {"per_participant": per, "steps": steps_choice, "query_rule": "last 70% of each child's trials (recording order)"}


def run_unit(row, out=OUT):
    eid = row["experiment_id"]; path = os.path.join(out, "units", f"{eid}.json")
    if os.path.exists(path):
        print("skip", eid); return
    if row["family_id"] != "C_ADAPT":
        print("technical_pending", eid); return
    plan = [json.loads(l) for l in open(PLAN)]
    brow = base_row(row, plan)
    brec, ck = resolve_unit(brow["experiment_id"], out) if brow else (None, None)
    if brec is None or not os.path.exists(ck):
        print("technical_pending (base unit not complete)", eid); return
    dev = torch.device("cuda"); t0 = time.time()
    rec = {"experiment_id": eid, "row": row, "canonical": canonical(row), "code_hash": code_hash(), "runner": "run_adapt", "status": "running",
           "base_unit": brow["experiment_id"], "base_checkpoint": os.path.basename(ck), "device": torch.cuda.get_device_name(0)}
    try:
        rec["eval"] = (private_bundle if row["dataset"] == "private_bdf" else continuous_bundle)(row, brow, brec, ck, dev, out)
        rec["status"] = "complete"
    except Exception as ex:
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    rec["total_seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.join(out, "units"), exist_ok=True)
    p = path if rec["status"] == "complete" else path.replace(".json", ".FAILED.json")
    json.dump(rec, open(p + ".tmp", "w"), default=float); os.replace(p + ".tmp", p)
    print(eid, rec["status"], rec["total_seconds"], rec.get("error", ""), flush=True)
    if rec["status"] != "complete":
        raise SystemExit(1)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--manifest", default=PLAN); a.add_argument("--job-index", type=int); a.add_argument("--experiment-id"); a.add_argument("--out", default=OUT)
    args = a.parse_args()
    run_unit(load_row(args.manifest, args.job_index, args.experiment_id), args.out)


if __name__ == "__main__":
    main()
