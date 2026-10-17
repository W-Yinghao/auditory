"""ALN3 queues (rebuilt every 10 min by refresh.sh as families are bound / dependencies resolve):
  queue_v3_small.txt  local / private / small staged families (shared GPUs; weight 2 GB)
  queue_v3_fm.txt     foundation-model families                   (one per GPU; weight 1000; E_DISTILL 12, since 2026-10-11)
  queue_v3_prior.txt  E34_PUBLIC_PRIOR families (ALN3.4)          (prior33.deps.write_queue: eid|idx|up1,up2,... and counters)
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
QUEUES = {"small": ["E_GX", "E_LOCAL", "A_LOCAL", "A_TARGETS", "A_DIMENSION", "A_LOCAL_FACTORS", "D_COVERAGE", "D_ADAPT", "D_ATTENTION", "E_PUBLIC_TRANSFER", "ALN32_LOCAL_SUPPORT"], "fm": ["E_GENERIC", "B_DENSE", "B_CTRL_ONESTEP", "B_LR_PANEL", "C_COMPLEMENT", "C_CAPACITY_CONTROL", "E_COMPLEMENT", "E_DISTILL", "B_LAYER_PROBE", "E_PUBLIC_TRANSFER", "D_ADAPT", "D_COVERAGE", "D_ATTENTION", "B_ALIGNED", "ALN32_LOCAL_SUPPORT", "ALN32_POSTONLY_FM", "ALN32_TRUE_FULL", "ALN32_RESIDUAL", "ALN32_SIMPLE_COMPLEMENT"]}  # B_ALIGNED: ADDENDUM_06; ALN32_*: ADDENDUM_07 (2026-10-14)
# E34_PUBLIC_PRIOR (ALN3.4, PUBLIC_PRIOR_DESIGN.md §6.5): queue_v3_prior.txt is written by prior33.deps.write_queue (prior_queue
# below; lines eid|idx|up1,up2,..., weights, counters .remaining / .waiting / .blocked), never by the generic path, and served
# only by keeper_prior.sh and slurm/aln33_prior_pool.sbatch. Last in QUEUES, so the fm and small queues are written first.
QUEUES["prior"] = ["ALN32_PUBLIC_AUDIO_PRIOR_DONOR", "ALN32_PUBLIC_AUDIO_PRIOR_CSX_DONOR", "ALN32_PUBLIC_AUDIO_PRIOR_RICH_DONOR",
                   "ALN32_PUBLIC_AUDIO_PRIOR_BRIDGE", "ALN32_PUBLIC_AUDIO_PRIOR_TARGET", "ALN32_PUBLIC_AUDIO_PRIOR_ZEROSHOT"]
EXT = [json.loads(l) for l in open(f"{O}/plan_ext.jsonl")] if os.path.exists(f"{O}/plan_ext.jsonl") else []
ALL = rows + EXT  # dependency lookups (bases / twins / donors / teachers) over plan rows and registered extension rows
DEF_FILE = f"{O}/governance/deferred_redundant_v30_panel.json"
DEFERRED = set(json.load(open(DEF_FILE))["ids"]) if os.path.exists(DEF_FILE) and not os.path.exists(f"{O}/PANEL_V30_RESUME") else set()
HELD_FILE = f"{O}/governance/held_executions.json"
HELD = set(json.load(open(HELD_FILE))["ids"]) if os.path.exists(HELD_FILE) else set()
from auditory_alignment_v3 import run_complement
from auditory_alignment_v3 import policy as POL
from auditory_alignment_v3.registry import POLICY_GROUP
_POL = {}


def policy_ok(r):  # memoised per policy cell (candidates are read from the fleet records, core.OUT)
    k = (r["family_id"], r["dataset"], r["subject_fold"], r["content_fold"], r["seed"], r["spec"]["objective"], r["spec"]["architecture"])
    if k not in _POL:
        _POL[k] = POL.resolve(r, ALL, core.OUT) is not None
    return _POL[k]


def policy_base_ok(r):  # ADDENDUM_04: the complement arms of D_COVERAGE / D_ATTENTION (mean_score) need their lag-local base complete
    from auditory_alignment_v3 import run_attention_policy, run_coverage_policy
    if r["family_id"] == "D_COVERAGE":
        return run_coverage_policy.lag_base_ready(r, ALL) is not None
    if r["family_id"] == "D_ATTENTION" and r["spec"]["architecture"] == "complement_policy" and r["spec"]["integrator"] == "mean_score":
        return run_attention_policy.lag_twin_ready(r, ALL) is not None
    return True


def prior_queue(fams):
    """E34_PUBLIC_PRIOR (PUBLIC_PRIOR_DESIGN.md §6.5): the prior queue files from prior33.deps.write_queue, with held = HELD |
    families_on_hold.json and bound = the families of QUEUES["prior"] bound in core.FAMILY_GROUP. When nothing is left in scope
    (.remaining 0) while a prior row without a unit record or .failed marker is held or unbound, .remaining is rewritten as 'held':
    the lane is paused, not complete (keeper_prior.sh ends only on 0). Any exception (the prior33 import included) is printed,
    and queue_v3_prior.txt, its weights and .blocked are written empty and .remaining / .waiting 'unknown' (never 0:
    keeper_prior.sh keeps running on a non-integer; watch_anyhost.sh raises an EVENT after 20 min of a non-integer other than
    'held'); the fm and small queues are unaffected."""
    try:
        from auditory_alignment_v3.prior33 import deps as P33
        hold = set(json.load(open(f"{O}/families_on_hold.json"))) if os.path.exists(f"{O}/families_on_hold.json") else set()
        held, bound = HELD | hold, set(core.FAMILY_GROUP) & set(fams)
        s = P33.write_queue(O, ALL, held=held, bound=bound, ext=EXT)
        paused = [r["experiment_id"] for r in ALL if r["family_id"] in fams and (r["experiment_id"] in held or r["family_id"] in held
                  or r["family_id"] not in bound) and not os.path.exists(f"{O}/units/{r['experiment_id']}.json")
                  and not os.path.exists(f"{O}/pool/queue_v3_prior/{r['experiment_id']}.failed")]
        if s["remaining"] == 0 and paused:  # deps.write_queue wrote 0; the keeper reads 0 twice, a minute apart, before it ends
            with open(f"{O}/queue_v3_prior.remaining.tmp", "w") as f:
                f.write("held\n")
            os.replace(f"{O}/queue_v3_prior.remaining.tmp", f"{O}/queue_v3_prior.remaining")
        print("prior", s["queued"], {k: s[k] for k in ("ready", "waiting", "blocked", "done", "failed")}, f"held_out={s['held']}",
              f"paused={len(paused)}", f"unresolved={len(s['unresolved'])}")
    except Exception as ex:  # noqa: BLE001
        print(f"prior queue error {ex!r}: queue_v3_prior written empty, .remaining unknown")
        for suf, txt in ((".txt", ""), ("_weights.txt", ""), (".blocked", ""), (".remaining", "unknown\n"), (".waiting", "unknown\n")):
            p = f"{O}/queue_v3_prior{suf}"
            try:
                with open(p + ".tmp", "w") as f:
                    f.write(txt)
                os.replace(p + ".tmp", p)
            except OSError as ex2:
                print(f"prior queue: cannot write {p}: {ex2!r}")


for q, fams in QUEUES.items():
    if q == "prior":  # E34_PUBLIC_PRIOR: written by prior33.deps (prior_queue); the generic path below never runs for it
        prior_queue(fams)
        continue
    ready = set(core.FAMILY_GROUP) - set(json.load(open(f"{O}/families_on_hold.json"))) if os.path.exists(f"{O}/families_on_hold.json") else set(core.FAMILY_GROUP)
    sel = [(i, r) for i, r in enumerate(rows) if r["family_id"] in fams and r["family_id"] in ready]
    sel += [(100000 + j, r) for j, r in enumerate(EXT) if r["family_id"] in fams and r["family_id"] in ready]
    sel = [(i, r) for i, r in sel if r["experiment_id"] not in DEFERRED]  # ALN3.1 deferred_redundant (reversible: PANEL_V30_RESUME)
    sel = [(i, r) for i, r in sel if r["experiment_id"] not in HELD]  # ALN3.2 execution-specific hold (governance/held_executions.json)
    sel = [(i, r) for i, r in sel if not r["family_id"].startswith("C_") or run_complement.base_ready(r, ALL, O) is not None]  # same-fold base complete
    # ADDENDUM_04 (2026-10-13): lag_local_tokens D arms on the small queue; a policy arm (dense_fm_policy / complement_policy) on the FM
    # queue (whole card) once its family is bound (registry.POLICY_GROUP) and its training-only model policy resolves
    sel = [(i, r) for i, r in sel if not r["family_id"].startswith("D_") or ((q == "small") if r["spec"].get("architecture") == "lag_local_tokens"
                                                                          else (q == "fm" and r["family_id"] in POLICY_GROUP and policy_ok(r) and policy_base_ok(r)))]
    from auditory_alignment_v3 import run_attention, run_distill, run_e_complement, run_transfer
    # E_PUBLIC_TRANSFER: foundation sources on the FM queue (whole card), the lag_local source on the small queue; donor must exist
    sel = [(i, r) for i, r in sel if r["family_id"] != "E_PUBLIC_TRANSFER" or ((r["spec"]["source_architecture"] == "lag_local_tokens") == (q == "small")
                                                                               and run_transfer.donor_ready(r, ALL, O) is not None)]
    sel = [(i, r) for i, r in sel if r["family_id"] != "E_COMPLEMENT" or run_e_complement.base_ready(r, ALL, O) is not None]
    from auditory_alignment_v3 import complement32 as _C32, residual32 as _R32  # ADDENDUM_09/10: same-fold / same-seed base complete
    sel = [(i, r) for i, r in sel if r["family_id"] != "ALN32_RESIDUAL" or _R32.base_ready(r, ALL, O) is not None]
    sel = [(i, r) for i, r in sel if r["family_id"] != "ALN32_SIMPLE_COMPLEMENT" or _C32.base_ready(r, ALL, O) is not None]
    # ADDENDUM_07: the local_aligned1000 encoder on the small queue (shared card); the raw ridges (up to ~3 GB of normal equations) on the FM queue
    # 2026-10-14: all ALN32_LOCAL_SUPPORT rows on the FM queue (small-queue workers would starve behind the FM keeper's 10 slots, as E_DISTILL did on 2026-10-11)
    sel = [(i, r) for i, r in sel if r["family_id"] != "ALN32_LOCAL_SUPPORT" or q == "fm"]
    sel = [(i, r) for i, r in sel if r["family_id"] != "E_DISTILL" or run_distill.teachers_ready(r, ALL) is not None]  # all candidates complete
    sel = [(i, r) for i, r in sel if r["family_id"] != "D_ATTENTION" or r["spec"]["integrator"] == "mean_score" or run_attention.twin_ready(r, ALL, O) is not None]
    sel = [(i, r) for i, r in sel if r["family_id"] != "D_ADAPT" or r["spec"]["architecture"] != "lag_local_tokens" or run_complement.base_ready({**r, "spec": {**r["spec"], "local_architecture": "lag_local_tokens", "window": "full"}}, ALL, O) is not None]
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
        # 2026-10-15: not-done rows first within each family (stable), so the round-robin interleaves remaining work; with done rows
        # interleaved too, a family that started early (B_ALIGNED) waited ~10 h for the newer families to reach its row position
        _done = {f[:-5] for f in os.listdir(os.path.join(O, "units")) if f.endswith(".json") and not f.endswith("FAILED.json")}
        per = {k: [t for t in v if t[1]["experiment_id"] not in _done] + [t for t in v if t[1]["experiment_id"] in _done] for k, v in per.items()}
        out_sel += [t for grp in zip_longest(*per.values()) for t in grp if t is not None]
    sel = out_sel
    w = 1000 if q == "fm" else 2
    W_FAM = {"E_DISTILL": 12}
    W_ROW = lambda r: 2 if (r["family_id"] == "ALN32_LOCAL_SUPPORT" and r["spec"]["variant"] == "local_aligned1000") else None  # small local encoder (1.9 GB in probe 1040154)  # E_DISTILL: brief foundation-teacher forward pass; B_LAYER_PROBE stays whole-card (user 2026-10-07: one FM job per GPU)
    open(f"{O}/queue_v3_{q}.txt.tmp", "w").write("".join(f"{r['experiment_id']}|{i}\n" for i, r in sel)); os.replace(f"{O}/queue_v3_{q}.txt.tmp", f"{O}/queue_v3_{q}.txt")
    open(f"{O}/queue_v3_{q}_weights.txt.tmp", "w").write("".join(f"{r['experiment_id']} {W_ROW(r) or W_FAM.get(r['family_id'], w)}\n" for _, r in sel)); os.replace(f"{O}/queue_v3_{q}_weights.txt.tmp", f"{O}/queue_v3_{q}_weights.txt")
    from collections import Counter
    print(q, len(sel), dict(Counter(r["family_id"] for _, r in sel)), f"deferred_out={sum(r['experiment_id'] in DEFERRED for r in ALL if r['family_id'] in fams)}")
