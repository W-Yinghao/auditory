"""ALN3 D policy arms: the training-only model policy (docs/auditory_alignment_v3/ADDENDUM_04_D_POLICY_BINDING.md §1).

For a D row with architecture dense_fm_policy / complement_policy the candidates are the B_DENSE / C_COMPLEMENT units of the
same dataset, subject fold, content fold, seed and objective (SELECTION_CE -> NCE) with target local (20 / 12 units). The
chosen unit has the lowest recorded best_selection_score (training participants' early-stopping own loss minus its
within-batch mismatched value at the unit's selected checkpoint); ties break on the experiment id. Only that field, the
candidate ids, rows, checkpoint existence and the dependency path are read - never an evaluation field. If a candidate is
missing, incomplete or has no checkpoint, the policy is not resolvable (None): no substitution.
"""
from __future__ import annotations

import json
import os

from . import core

FAMILY = {"dense_fm_policy": "B_DENSE", "complement_policy": "C_COMPLEMENT"}
N_EXPECTED = {"dense_fm_policy": 20, "complement_policy": 12}
RULE = ("min recorded best_selection_score (training participants' early-stopping own loss - within-batch mismatched loss) "
        "over the B_DENSE (dense_fm_policy) / C_COMPLEMENT (complement_policy) units of the same dataset, subject fold, content fold, "
        "seed and objective (SELECTION_CE -> NCE), target local; ties -> experiment id")


def is_policy_row(row):
    return row["family_id"].startswith("D_") and row["spec"].get("architecture") in FAMILY


def candidates(row, rows):
    arch = row["spec"]["architecture"]
    o = row["spec"]["objective"]
    o = "NCE" if o == "SELECTION_CE" else o
    return [r for r in rows if r["family_id"] == FAMILY[arch] and r["dataset"] == row["dataset"] and r["subject_fold"] == row["subject_fold"]
            and r["content_fold"] == row["content_fold"] and r["seed"] == row["seed"] and r["spec"]["objective"] == o
            and r["spec"].get("target") == "local"]


def resolve(row, rows, out):
    """-> policy record (dict) or None when the cell is not (yet) resolvable."""
    arch = row["spec"]["architecture"]
    cands = candidates(row, rows)
    if len(cands) != N_EXPECTED[arch]:
        return None
    scores, ckpts = {}, {}
    for r in cands:
        e = r["experiment_id"]
        p = os.path.join(out, "units", f"{e}.json"); ck = os.path.join(out, "ckpt", f"{e}_best.pt")
        if not (os.path.exists(p) and os.path.exists(ck)):
            return None
        rec = json.load(open(p))
        if rec.get("status") != "complete" or rec.get("best_selection_score") is None:
            return None
        scores[e] = float(rec["best_selection_score"]); ckpts[e] = ck
    chosen = min(scores, key=lambda e: (scores[e], e))
    crow = next(r for r in cands if r["experiment_id"] == chosen)
    return {"rule": RULE, "candidate_family": FAMILY[arch], "n_candidates": len(cands), "candidates_best_selection_score": scores,
            "chosen": chosen, "chosen_row": crow, "chosen_checkpoint": os.path.relpath(ckpts[chosen], core.REPO)}
