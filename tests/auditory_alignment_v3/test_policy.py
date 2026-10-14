"""ADDENDUM_04 §1: the training-only model policy picks the lowest recorded best_selection_score, reads no evaluation field,
breaks ties on the id, maps SELECTION_CE to NCE and refuses to resolve an incomplete cell."""
import json
import os

from auditory_alignment_v3 import policy


def _row(eid, fam, obj="NCE", fold=0, cfold=0, seed=3401, ds="fau", target="local", arch=None):
    return {"experiment_id": eid, "family_id": fam, "dataset": ds, "subject_fold": fold, "content_fold": cfold, "seed": seed,
            "spec": {"objective": obj, "target": target, **({"architecture": arch} if arch else {})}}


def _cell(tmp, fam, n, scores, obj="NCE", eval_field=None):
    os.makedirs(tmp / "units", exist_ok=True); os.makedirs(tmp / "ckpt", exist_ok=True)
    rows = []
    for i in range(n):
        e = f"ALN3_{fam}_{i:02d}"; rows.append(_row(e, fam, obj))
        rec = {"status": "complete", "best_selection_score": scores[i]}
        if eval_field is not None:
            rec["eval"] = eval_field[i]
        json.dump(rec, open(tmp / "units" / f"{e}.json", "w")); open(tmp / "ckpt" / f"{e}_best.pt", "w").close()
    return rows


def test_lowest_score_and_tie_break(tmp_path):
    scores = [0.5 - 0.01 * i for i in range(20)]; scores[3] = scores[19]  # tie between ids 03 and 19 -> 03
    rows = _cell(tmp_path, "B_DENSE", 20, scores)
    d = _row("ALN3_D", "D_ADAPT", arch="dense_fm_policy")
    p = policy.resolve(d, rows + [d], str(tmp_path))
    assert p["chosen"] == "ALN3_B_DENSE_03" and p["n_candidates"] == 20 and p["candidate_family"] == "B_DENSE"


def test_no_evaluation_field_is_used(tmp_path):
    scores = [1.0] * 12; scores[5] = 0.1
    rows = _cell(tmp_path, "C_COMPLEMENT", 12, scores, eval_field=[{"gain": 100.0 if i == 7 else 0.0} for i in range(12)])
    d = _row("ALN3_D", "D_ATTENTION", obj="SELECTION_CE", arch="complement_policy")  # SELECTION_CE -> NCE candidates
    assert policy.resolve(d, rows, str(tmp_path))["chosen"] == "ALN3_C_COMPLEMENT_05"


def test_incomplete_cell_does_not_resolve(tmp_path):
    rows = _cell(tmp_path, "B_DENSE", 20, [0.1] * 20)
    d = _row("ALN3_D", "D_ADAPT", arch="dense_fm_policy")
    os.remove(tmp_path / "ckpt" / "ALN3_B_DENSE_07_best.pt")
    assert policy.resolve(d, rows, str(tmp_path)) is None
    assert policy.resolve(d, rows[:19], str(tmp_path)) is None  # wrong candidate count
    other = _row("ALN3_D2", "D_ADAPT", fold=1, arch="dense_fm_policy")  # other fold: no candidates
    assert policy.resolve(other, rows, str(tmp_path)) is None
