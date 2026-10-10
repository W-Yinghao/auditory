"""Applies the A1 readout repair to the foundation-model code (all-or-nothing: every edit must match exactly once)."""
import os
R = "/home/infres/yinwang/EEG_auditory/auditory_alignment_v2/"
edits = {
    "train_fm.py": [
        ("from .foundation_adapter import Backbone, PatchHead\n",
         "from .fm_readout import make_head\nfrom .foundation_adapter import Backbone\n", 1),
        ("super().__init__(); self.bb = backbone; self.head = PatchHead(backbone.E, d)",
         "super().__init__(); self.bb = backbone; self.head = make_head(backbone, d)  # amendment A1: channel-aware spatial readout", 2),
        ('    torch.save({"enc": enc.state_dict()}, ckpt_prefix + "_last.pt")\n', "", 1),
        ('    torch.save({"enc": enc.state_dict(), "protos": protos.detach()}, ckpt_prefix + "_last.pt")\n', "", 1),
        ("Parameter groups: backbone (lr_backbone) and head (lr_head), AdamW, cosine schedule over actual updates.\n",
         "Parameter groups: backbone (lr_backbone) and head (lr_head), AdamW, cosine schedule over actual updates.\n"
         "Readout (amendment A1, 2026-10-07): fm_readout.SpatialPatchHead (channel-aware, signed spatial filters, patch axis kept);\n"
         "the earlier channel-mean head is the legacy_chmean_v1 variant. Final-epoch states are not saved (never read).\n", 1),
    ],
    "donor.py": [
        ("    enc_head = FMEncoder(shared).to(dev)  # shared patch head\n",
         "    from .fm_readout import HEAD_VERSION, make_head\n"
         "    eheads = {ds: make_head(bbs[ds]).to(dev) for ds in bts}  # one spatial readout per cohort channel layout (amendment A1)\n", 1),
        ("    groups, params = param_groups(enc_head, lr_backbone, lr_head)\n",
         "    bbp = [p for p in shared.net.parameters() if p.requires_grad]; hdp = [p for h in eheads.values() for p in h.parameters()]\n"
         "    groups, params = [{\"params\": bbp, \"lr\": lr_backbone}, {\"params\": hdp, \"lr\": lr_head}], bbp + hdp\n", 1),
        ("u0 = enc_head.head(bbs[ds](bt.segments(r0[0])))", "u0 = eheads[ds](bbs[ds](bt.segments(r0[0])))", 1),
        ("        enc_head.train(); its =", "        shared.train(); [h.train() for h in eheads.values()]; its =", 1),
        ("u = enc_head.head(bbs[ds](bts[ds].segments(rws[0])))", "u = eheads[ds](bbs[ds](bts[ds].segments(rws[0])))", 1),
        ('"backbone_contract": shared.contract()}', '"backbone_contract": shared.contract(), "readout_head": HEAD_VERSION + " (one per source cohort; not part of the donor)"}', 1),
        ("one shared EEG backbone + shared patch head,", "one shared EEG backbone + one spatial readout per cohort layout (amendment A1),", 1),
    ],
    "eval_fm.py": [
        ("def evaluate_segments(row, enc, head, bt, coh, calib, K=8):\n",
         "def evaluate_segments(row, enc, head, bt, coh, calib, K=8, reps=None, readouts=(\"unified\", \"native\"), dependence=True):\n", 1),
        ("    reps = SegmentReps(enc, head, bt)\n", "    reps = reps if reps is not None else SegmentReps(enc, head, bt)\n", 1),
        ('        ro.calibrate({"unified": ro.scores(Uq, Vc, Ac, "unified"), "native": ro.scores(Uq, Vc, Ac, "native")}, own)\n',
         "        ro.calibrate({kr: ro.scores(Uq, Vc, Ac, kr) for kr in readouts}, own)\n", 1),
        ('for kr in ("unified", "native"):', "for kr in readouts:", 2),
        ("        dep = ev1.test_cs_dependence(Uq, Vc[own], calib, np.random.default_rng(p), anchors=Uq.shape[1])\n",
         "        dep = ev1.test_cs_dependence(Uq, Vc[own], calib, np.random.default_rng(p), anchors=Uq.shape[1]) if dependence else None\n", 1),
    ],
    "run_fm.py": [
        ('("foundation_adapter.py", "train_fm.py", "eval_fm.py", "run_fm.py",', '("foundation_adapter.py", "fm_readout.py", "train_fm.py", "eval_fm.py", "run_fm.py",', 1),
        ('            rec["eval"] = evaluate.evaluate_private(row, enc, bt, log["objective_calibration"], protos)\n',
         '            rec["eval"] = evaluate.evaluate_private(row, enc, bt, log["objective_calibration"], protos)\n'
         '            _probe(rec, lambda: channel_probe_private(row, enc, bt))\n', 1),
        ('            rec["eval"] = evaluate_segments(row, enc, head, bt, coh, log["objective_calibration"])\n',
         '            rec["eval"] = evaluate_segments(row, enc, head, bt, coh, log["objective_calibration"])\n'
         '            _probe(rec, lambda: channel_probe_segments(row, enc, head, bt, coh, log["objective_calibration"]))\n', 1),
        ('    rec = {"experiment_id": eid, "row": row, "canonical": canonical(row), "code_hash": code_hash(), "runner": "run_fm", "status": "running",\n',
         '    rec = {"experiment_id": eid, "row": row, "canonical": canonical(row), "code_hash": code_hash(), "runner": "run_fm", "status": "running",\n'
         '           "readout_head": HEAD_VERSION,\n', 1),
        ('        ck = os.path.join(out, "ckpt_lrsel", f"{key.replace(\'|\', \'__\')}__{lr_b:g}__{lr_h:g}")\n',
         '        ck = os.path.join(out, "ckpt", "lrsel", f"{key.replace(\'|\', \'__\')}__{lr_b:g}__{lr_h:g}")  # scratch; removed after scoring\n', 1),
        ("        torch.cuda.empty_cache()\n",
         "        for suf in (\"_best.pt\", \"_resume.pt\", \"_last.pt\"):  # candidate states are never reused (user 2026-10-07: delete files no longer useful)\n"
         "            if os.path.exists(ck + suf):\n"
         "                os.remove(ck + suf)\n"
         "        torch.cuda.empty_cache()\n", 1),
        ('    res = {"key": key, "dev_cell": DEV_CELL, "epochs": E, "code_hash": code_hash(), "candidates": []}\n',
         '    res = {"key": key, "dev_cell": DEV_CELL, "epochs": E, "code_hash": code_hash(), "readout_head": HEAD_VERSION, "candidates": []}\n', 1),
        ("from .run import OUT, PLAN, REPO, canonical, load_cohort, load_row\n",
         "from .fm_readout import HEAD_VERSION, channel_probe_private, channel_probe_segments\n"
         "from .run import OUT, PLAN, REPO, canonical, load_cohort, load_row\n\n\n"
         "def _probe(rec, fn):\n"
         "    \"\"\"Channels-preserved linear-probe reference (amendment A1); a failure is recorded in the unit, never hidden.\"\"\"\n"
         "    try:\n"
         "        rec[\"eval\"][\"channel_probe\"] = fn()\n"
         "    except Exception as ex:  # noqa: BLE001\n"
         "        rec[\"eval\"][\"channel_probe_error\"] = f\"{type(ex).__name__}: {ex}\"\n", 1),
    ],
    "run_stage.py": [
        ('STAGE_CODE = [("auditory_alignment_v2", f) for f in ("donor.py", "distill.py", "run_stage.py", "foundation_adapter.py", "train_fm.py", "eval_fm.py",',
         'STAGE_CODE = [("auditory_alignment_v2", f) for f in ("donor.py", "distill.py", "run_stage.py", "foundation_adapter.py", "fm_readout.py", "train_fm.py", "eval_fm.py",', 1),
        ('                rec.update(log); rec["eval"] = evaluate.evaluate_private(row, enc, bt, log["objective_calibration"], protos)\n',
         '                rec.update(log); rec["eval"] = evaluate.evaluate_private(row, enc, bt, log["objective_calibration"], protos)\n'
         '                rec["readout_head"] = HEAD_VERSION; _probe(rec, lambda: channel_probe_private(row, enc, bt))\n', 1),
        ('                rec.update(log); rec["eval"] = evaluate_segments(row, enc, head, bt, coh, log["objective_calibration"])\n',
         '                rec.update(log); rec["eval"] = evaluate_segments(row, enc, head, bt, coh, log["objective_calibration"])\n'
         '                rec["readout_head"] = HEAD_VERSION; _probe(rec, lambda: channel_probe_segments(row, enc, head, bt, coh, log["objective_calibration"]))\n', 1),
        ("STAGE_FAMILIES = {", "from .fm_readout import HEAD_VERSION, channel_probe_private, channel_probe_segments  # noqa: E402\n"
                             "from .run_fm import _probe  # noqa: E402\nSTAGE_FAMILIES = {", 1),
    ],
    "run_adapt.py": [
        ('ADAPT_CODE = [("auditory_alignment_v2", f) for f in ("adapt.py", "run_adapt.py", "train.py", "train_fm.py", "foundation_adapter.py", "eval_fm.py",',
         'ADAPT_CODE = [("auditory_alignment_v2", f) for f in ("adapt.py", "run_adapt.py", "train.py", "train_fm.py", "foundation_adapter.py", "fm_readout.py", "eval_fm.py",', 1),
    ],
    "foundation_adapter.py": [
        ('    """tokens [B, C, P, E] -> channel mean -> LN -> Linear -> L2 per patch: [B, P, d]."""\n',
         '    """LEGACY (legacy_chmean_v1; an ablation, not the default interface - amendment A1): tokens [B, C, P, E] -> unweighted\n'
         '    channel mean -> LN -> Linear -> L2 per patch: [B, P, d]. Kept only to document and reproduce the legacy variant."""\n', 1),
    ],
}
new = {}
for f, es in edits.items():
    s = open(R + f).read()
    for old, rep, n in es:
        c = s.count(old)
        assert c == n, f"{f}: expected {n} match(es), found {c}: {old[:70]!r}"
        s = s.replace(old, rep)
    new[f] = s
for f, s in new.items():
    open(R + f + ".tmp", "w").write(s); os.replace(R + f + ".tmp", R + f)
print("patched:", ", ".join(new))
