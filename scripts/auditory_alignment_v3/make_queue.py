"""ALN3 queues (rebuilt every 10 min by refresh.sh as families are bound / dependencies resolve):
  queue_v3_small.txt  local / private / small staged families (shared GPUs; weight 2 GB)
  queue_v3_fm.txt     foundation-model families                   (one per GPU; weight 1000; E_DISTILL 12, since 2026-10-11)
Line: <experiment_id>|<plan index> (index >= 100000: row index-100000 of plan_ext.jsonl). Order (docs/12 §6, a resource order,
not a performance gate): breadth seed 3401 before the seed panel; within a block dependency feeders (same-fold bases, teacher
candidates) first, then round-robin across families so every bound family progresses.
ALN3.1 (2026-10-11): the seed panel = the v3.0 panel rows that a v3.1 role requires + the registered v3.1 panel rows in
plan_ext.jsonl (make_plan_ext.py); v3.0 panel rows outside every role are deferred_redundant (governance/
deferred_redundant_v30_panel.json) and left out unless the switch file PANEL_V30_RESUME exists. Dependency lookups see plan
rows and extension rows alike (a seed-3407 C row needs the seed-3407 A_LOCAL base, a learned_temporal attention row its
mean_score twin of the same seed)."""
import json, os, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import core
O = core.OUT
rows = core.load_rows()
# 2026-10-11 10:00: E_DISTILL moved small -> fm. The small queue had drained (09:30), the FM keeper took all 10 runfill slots and
# FM workers only exit when a full pass claims nothing, so dependency-released E_DISTILL rows starved behind them (small workers
# pending on QOSMaxGRESPerUser). On FM workers an E_DISTILL row keeps weight 12 (never co-admitted with a whole-card unit).
QUEUES = {"small": ["E_GX", "E_LOCAL", "A_LOCAL", "A_TARGETS", "A_DIMENSION", "A_LOCAL_FACTORS", "D_COVERAGE", "D_ADAPT", "D_ATTENTION", "E_PUBLIC_TRANSFER"], "fm": ["E_GENERIC", "B_DENSE", "B_CTRL_ONESTEP", "B_LR_PANEL", "C_COMPLEMENT", "C_CAPACITY_CONTROL", "E_COMPLEMENT", "E_DISTILL", "B_LAYER_PROBE", "E_PUBLIC_TRANSFER"]}
EXT = [json.loads(l) for l in open(f"{O}/plan_ext.jsonl")] if os.path.exists(f"{O}/plan_ext.jsonl") else []
ALL = rows + EXT  # dependency lookups (bases / twins / donors / teachers) over plan rows and registered extension rows
DEF_FILE = f"{O}/governance/deferred_redundant_v30_panel.json"
DEFERRED = set(json.load(open(DEF_FILE))["ids"]) if os.path.exists(DEF_FILE) and not os.path.exists(f"{O}/PANEL_V30_RESUME") else set()
from auditory_alignment_v3 import run_complement
for q, fams in QUEUES.items():
    ready = set(core.FAMILY_GROUP) - set(json.load(open(f"{O}/families_on_hold.json"))) if os.path.exists(f"{O}/families_on_hold.json") else set(core.FAMILY_GROUP)
    sel = [(i, r) for i, r in enumerate(rows) if r["family_id"] in fams and r["family_id"] in ready]
    sel += [(100000 + j, r) for j, r in enumerate(EXT) if r["family_id"] in fams and r["family_id"] in ready]
    sel = [(i, r) for i, r in sel if r["experiment_id"] not in DEFERRED]  # ALN3.1 deferred_redundant (reversible: PANEL_V30_RESUME)
    sel = [(i, r) for i, r in sel if not r["family_id"].startswith("C_") or run_complement.base_ready(r, ALL, O) is not None]  # same-fold base complete
    sel = [(i, r) for i, r in sel if not r["family_id"].startswith("D_") or r["spec"].get("architecture") == "lag_local_tokens"]  # policy arms wait for B/C
    from auditory_alignment_v3 import run_attention, run_distill, run_e_complement, run_transfer
    # E_PUBLIC_TRANSFER: foundation sources on the FM queue (whole card), the lag_local source on the small queue; donor must exist
    sel = [(i, r) for i, r in sel if r["family_id"] != "E_PUBLIC_TRANSFER" or ((r["spec"]["source_architecture"] == "lag_local_tokens") == (q == "small")
                                                                               and run_transfer.donor_ready(r, ALL, O) is not None)]
    sel = [(i, r) for i, r in sel if r["family_id"] != "E_COMPLEMENT" or run_e_complement.base_ready(r, ALL, O) is not None]
    sel = [(i, r) for i, r in sel if r["family_id"] != "E_DISTILL" or run_distill.teachers_ready(r, ALL) is not None]  # all candidates complete
    sel = [(i, r) for i, r in sel if r["family_id"] != "D_ATTENTION" or r["spec"]["integrator"] == "mean_score" or run_attention.twin_ready(r, ALL, O) is not None]
    sel = [(i, r) for i, r in sel if r["family_id"] != "D_ADAPT" or run_complement.base_ready({**r, "spec": {**r["spec"], "local_architecture": "lag_local_tokens", "window": "full"}}, ALL, O) is not None]
    # dependency-driven priority: the same-fold bases of C_COMPLEMENT (A_LOCAL lag_local_tokens full) and E_COMPLEMENT /
    # E_DISTILL (E_LOCAL lag_local_tokens full) first, so dependent families can start as early as possible
    base = lambda r: r["family_id"] in ("A_LOCAL", "E_LOCAL") and r["spec"].get("architecture") == "lag_local_tokens" and r["spec"].get("window") == "full"
    # E_GENERIC seed-3401 pretrained units are the generic_pretrained_teacher candidates of E_DISTILL
    feeder = lambda r: base(r) or (r["family_id"] == "E_GENERIC" and r["seed"] == 3401 and r["spec"]["adaptation"].startswith("pretrained"))
    sel.sort(key=lambda t: (t[1]["seed_scope"] != "breadth", not feeder(t[1]), fams.index(t[1]["family_id"]), t[1]["dataset"], t[1]["subject_fold"] or 0, t[1]["content_fold"] or 0))
    # within each seed-scope block: round-robin across families, so every bound family progresses (C starts alongside B)
    from itertools import groupby, zip_longest
    out_sel = []
    for _, blk in groupby(sel, key=lambda t: t[1]["seed_scope"] != "breadth"):  # feeders stay first within their family
        per = {}
        for t in blk:
            per.setdefault(t[1]["family_id"], []).append(t)
        out_sel += [t for grp in zip_longest(*per.values()) for t in grp if t is not None]
    sel = out_sel
    w = 1000 if q == "fm" else 2
    W_FAM = {"E_DISTILL": 12}  # E_DISTILL: brief foundation-teacher forward pass; B_LAYER_PROBE stays whole-card (user 2026-10-07: one FM job per GPU)
    open(f"{O}/queue_v3_{q}.txt.tmp", "w").write("".join(f"{r['experiment_id']}|{i}\n" for i, r in sel)); os.replace(f"{O}/queue_v3_{q}.txt.tmp", f"{O}/queue_v3_{q}.txt")
    open(f"{O}/queue_v3_{q}_weights.txt.tmp", "w").write("".join(f"{r['experiment_id']} {W_FAM.get(r['family_id'], w)}\n" for _, r in sel)); os.replace(f"{O}/queue_v3_{q}_weights.txt.tmp", f"{O}/queue_v3_{q}_weights.txt")
    from collections import Counter
    print(q, len(sel), dict(Counter(r["family_id"] for _, r in sel)), f"deferred_out={sum(r['experiment_id'] in DEFERRED for r in ALL if r['family_id'] in fams)}")
