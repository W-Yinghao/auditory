"""ITEM3_TO_B_MAPPING (ALN3.1 UPDATE_NOW / ALN3_1_DECISIONS §3): old item-3 training arms (3b X_PHASE; 3c X_FT_VAL, X_FT_REG; frozen
registration docs/auditory_alignment_v2/ITEM3_PREREG_FROZEN.md, folded into B by addendum 01) -> the ALN3 B rows that carry
the same question. Exact old unit ids -> exact new comparison ids, preserved question, what changed (time target / recipe),
source checkpoint, live status read from the unit records. Writes governance/item3_to_b_mapping.json and prints the summary
for docs/auditory_alignment_v3/ITEM3_TO_B_MAPPING.md. No submission, no cancellation."""
import json, os, sys, time
from collections import Counter

sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import core

V2 = core.V2_OUT; O = core.OUT
plan = core.load_rows(); ext = [json.loads(l) for l in open(f"{O}/plan_ext.jsonl")]
X = [json.loads(l) for l in open(f"{V2}/plan_item3.jsonl")]
status = lambda eid: "complete" if os.path.exists(f"{O}/units/{eid}.json") else ("running_or_queued" if os.path.isdir(f"{O}/pool/queue_v3_fm/{eid}.claim") else "pending")
QUESTION = {"X_PHASE": "3b: does a finer temporal phase / relative-time alignment help the foundation-model readout (1 s patch rows were the ALN2 interface)?",
            "X_FT_VAL": "3c-1: is the checkpoint-selection granularity (validation every epoch instead of every E/20) one reason fine-tuning underperformed freezing?",
            "X_FT_REG": "3c-2: do lower backbone learning rates with layer-wise decay (0.75) reduce the over-fitting loss of fine-tuning?"}
CHANGE = {"X_PHASE": ["time target: dense20ms_v1 grid (20 ms rows, relative-time dense_query) and channel_phase_linear readout instead of 1 s patch rows with random phase offsets",
                      "training recipe: ALN3 B recipe (head warm-up 5 epochs, top-down unfreezing where applicable, per-epoch development validation, layer-wise lr decay 0.75); frozen arms train the readout only"],
          "X_FT_VAL": ["training recipe: per-epoch development validation on fixed training-side blocks is the ALN3 B default (addendum 01 §3)", "time target: dense20ms_v1 instead of 1 s patch rows"],
          "X_FT_REG": ["training recipe: layer-wise lr decay 0.75, fixed lower backbone lr (partial/full 1e-5, PEFT 1e-4) chosen before results; B_LR_PANEL (x0.3, x3) replaces the development-side lr re-selection of X_FT_REG; B_CTRL_ONESTEP keeps the ALN2 one-step recipe as the control", "time target: dense20ms_v1 instead of 1 s patch rows"]}
maps = []
for x in X:
    if x["family_id"] == "X_READOUT_DIAG":
        continue
    s = x["spec"]
    same = lambda r: r["dataset"] == x["dataset"] and r["subject_fold"] == x["subject_fold"] and r["content_fold"] == x["content_fold"] and r["seed"] == 3401 \
        and r["spec"].get("architecture") == s["architecture"] and r["spec"].get("adaptation") == s["adaptation"] and r["spec"]["objective"] == s["objective"]
    b = [r for r in plan if r["family_id"] == "B_DENSE" and same(r)]
    primary = [r["experiment_id"] for r in b if r["spec"]["readout"] == "dense_query"]
    phase = [r["experiment_id"] for r in b if r["spec"]["readout"] == "channel_phase_linear"]
    ctrl = [r["experiment_id"] for r in ext if r["family_id"] == "B_CTRL_ONESTEP" and same(r)]
    lrp = [r["experiment_id"] for r in ext if r["family_id"] == "B_LR_PANEL" and same(r)]
    new = primary + (phase if x["family_id"] == "X_PHASE" else []) + (ctrl + lrp if x["family_id"] == "X_FT_REG" else ctrl if x["family_id"] == "X_FT_VAL" else [])
    maps.append({"old_family": x["family_id"], "old_experiment_id": x["experiment_id"], "old_base_unit": x["base_unit"], "dataset": x["dataset"], "subject_fold": x["subject_fold"], "content_fold": x["content_fold"],
                 "architecture": s["architecture"], "adaptation": s["adaptation"], "objective": s["objective"], "preserved_question": QUESTION[x["family_id"]],
                 "new_owner": "B_DENSE" + (" + B_CTRL_ONESTEP + B_LR_PANEL" if x["family_id"] == "X_FT_REG" else " + B_CTRL_ONESTEP" if x["family_id"] == "X_FT_VAL" else ""),
                 "new_comparison_ids": {"B_DENSE_dense_query": primary, "B_DENSE_channel_phase_linear": phase, "B_CTRL_ONESTEP": ctrl, "B_LR_PANEL": lrp},
                 "changes": CHANGE[x["family_id"]],
                 "source_checkpoint": "public pretrained backbone (same initial weights as the ALN2 B_FM unit); the ALN2 unit " + x["base_unit"] + " stays the legacy comparator, no ALN2 checkpoint is fine-tuned further",
                 "status": {k: dict(Counter(status(e) for e in v)) for k, v in (("B_DENSE_dense_query", primary), ("B_DENSE_channel_phase_linear", phase), ("B_CTRL_ONESTEP", ctrl), ("B_LR_PANEL", lrp)) if v},
                 "old_unit_status": "never trained (folded into B before any 3b/3c unit started; addendum 01, 2026-10-10)"})
unmapped = [m["old_experiment_id"] for m in maps if not m["new_comparison_ids"]["B_DENSE_dense_query"]]
out = {"version": "ALN3.1", "generated": time.strftime("%Y-%m-%d %H:%M"), "status": "bound_on_server", "not_a_submission": True,
       "old_registration": "docs/auditory_alignment_v2/ITEM3_PREREG_FROZEN.md (sha256 c7590820..., read-only) + ITEM3_ADDENDUM_01.md",
       "item3a": {"old_family": "X_READOUT_DIAG", "action": "run_evaluation_only", "n_units": sum(x["family_id"] == "X_READOUT_DIAG" for x in X),
                  "n_complete": sum(os.path.exists(f"{V2}/units/{x['experiment_id']}.json") for x in X if x["family_id"] == "X_READOUT_DIAG"),
                  "results": "docs/auditory_alignment_v2/ITEM3A_RESULTS.md", "role": "readout diagnosis and B reference; not a launch gate for A or E"},
       "n_old_training_units": len(maps), "n_unmapped": len(unmapped), "unmapped": unmapped,
       "by_old_family": {f: {"n": sum(m["old_family"] == f for m in maps), "new_ids_dense_query": sum(len(m["new_comparison_ids"]["B_DENSE_dense_query"]) for m in maps if m["old_family"] == f),
                             "new_ids_phase_linear": sum(len(m["new_comparison_ids"]["B_DENSE_channel_phase_linear"]) for m in maps if m["old_family"] == f),
                             "ctrl_onestep": sum(len(m["new_comparison_ids"]["B_CTRL_ONESTEP"]) for m in maps if m["old_family"] == f), "lr_panel": sum(len(m["new_comparison_ids"]["B_LR_PANEL"]) for m in maps if m["old_family"] == f)}
                         for f in ("X_PHASE", "X_FT_VAL", "X_FT_REG")},
       "b_status_overall": dict(Counter(st for m in maps for v in m["new_comparison_ids"].values() for st in map(status, v))),
       "mappings": maps}
os.makedirs(f"{O}/governance", exist_ok=True)
p = f"{O}/governance/item3_to_b_mapping.json"; open(p + ".tmp", "w").write(json.dumps(out, indent=1) + "\n"); os.replace(p + ".tmp", p)
print(json.dumps({k: v for k, v in out.items() if k != "mappings"}, indent=1))
