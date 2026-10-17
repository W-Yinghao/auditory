"""Exploratory S34_PRIVATE CS calibration diagnosis, recorded before computation.

Reads completed records only. Positive delta = positive_affine - class_kernel
for losses. Children are averaged across seeds before the bootstrap.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np

from auditory_alignment_v3 import core
from auditory_alignment_v3.aln34 import e_multiseed as E
from auditory_alignment_v3.sci_r1 import stats as S

BASE = Path(core.OUT) / "aln34" / "private_calibration"
NOTE = Path(core.OUT) / "aln34" / "PRIVATE_CALIBRATION_NOTE_20261017.md"
RESULT = Path(core.REPO) / "results/auditory_alignment_v3/aln34/private_calibration"
DOC = Path(core.REPO) / "docs/auditory_alignment_v3/PRIVATE_CALIBRATION_DIAGNOSIS.md"
CONFIGS = tuple(c for c in E.PANEL_CONFIGS if c[1] == "CS_SINGLE")
METRICS = ("nll_bits", "brier", "auc_score")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows():
    ext = Path(core.OUT) / "plan_ext.jsonl"
    rr = core.load_rows() + [json.loads(line) for line in ext.read_text().splitlines() if line.strip()]
    return [r for r in rr if E.row_in_panel(r) and E.config_of(r) in CONFIGS]


def validate_pair(pair):
    a, b = pair["class_kernel"], pair["positive_affine"]
    if a["n"] != b["n"]:
        raise ValueError("trial counts differ")
    for field in (*METRICS, "gain_vs_base_bits"):
        if not np.isfinite([a[field], b[field]]).all():
            raise ValueError(f"nonfinite {field}")
    if abs(a["auc_score"] - b["auc_score"]) > 1e-12:
        raise ValueError("same-score AUC changed")
    if abs((a["nll_bits"] + a["gain_vs_base_bits"]) - (b["nll_bits"] + b["gain_vs_base_bits"])) > 1e-10:
        raise ValueError("base entropy differs")
    return {field: float(b[field] - a[field]) for field in METRICS}


def identity_matrix(values, configs=CONFIGS, seeds=E.SEEDS):
    """All config/seed cells must contain identical identities; no seed-as-n."""
    key = lambda c: "|".join(c)
    sets = [set(values[key(c)][str(s)]) for c in configs for s in seeds]
    if not sets or any(x != sets[0] for x in sets):
        raise ValueError("incomplete paired identity coverage")
    ids = sorted(sets[0])
    return ids, {m: np.array([[np.mean([values[key(c)][str(s)][i]["delta"][m] for s in seeds])
                              for c in configs] for i in ids]) for m in METRICS}


def _jsonable(x):
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items() if k != "T"}
    if isinstance(x, (tuple, list)):
        return [_jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    return x


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(_jsonable(value), indent=2, sort_keys=True, allow_nan=False) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def analyze():
    started = time.time()
    rr = rows()
    assert len(rr) == 120 and len({r["experiment_id"] for r in rr}) == 120
    values = {"|".join(c): {str(s): {} for s in E.SEEDS} for c in CONFIGS}
    provenance, units = {}, []
    for row in rr:
        eid = row["experiment_id"]
        path = Path(core.OUT) / "units" / f"{eid}.json"
        rec = json.loads(path.read_text())
        assert rec["status"] == "complete" and rec["row"] == row, f"record identity: {eid}"
        expected_hash = core.code_hash(row["family_id"])
        assert E.EQUIVALENT_HASHES.get(rec["code_hash"], rec["code_hash"]) == expected_hash, f"code hash: {eid}"
        cal = rec["eval"]["native_calibration"]
        conf, seed = "|".join(E.config_of(row)), str(row["seed"])
        diffs = []
        for child, pair in cal["per_participant"].items():
            assert child not in values[conf][seed], "child duplicated across folds"
            delta = validate_pair(pair)
            diffs.append(delta["nll_bits"])
            values[conf][seed][child] = {"delta": delta, "class_kernel": pair["class_kernel"],
                                       "positive_affine": pair["positive_affine"], "unit": eid}
        params = cal["methods"]["positive_affine"]
        units.append({"id": eid, "config": conf, "seed": int(seed), "fold": row["subject_fold"],
                      "n_children": len(diffs), "mean_nll_delta": float(np.mean(diffs)),
                      "calibrator": params, "reference": cal["methods"]["class_kernel"],
                      "calibration_trials": cal["n_calibration_trials"]})
        provenance[eid] = sha(path)
    ids, matrices = identity_matrix(values)
    assert len(ids) == 64
    for child in ids:
        ns = {values["|".join(c)][str(s)][child]["class_kernel"]["n"] for c in CONFIGS for s in E.SEEDS}
        assert len(ns) == 1, "paired trial counts differ across seeds/configurations"
    stats = {m: S.summary(mat, B=4000, seed=S.group_seed("S34_PRIVATE_CALIBRATION", m)) for m, mat in matrices.items()}
    levels = {}
    for c in CONFIGS:
        k = "|".join(c)
        levels[k] = {}
        for s in E.SEEDS:
            vv = list(values[k][str(s)].values())
            levels[k][str(s)] = {method: {m: float(np.mean([v[method][m] for v in vv])) for m in METRICS}
                                  for method in ("class_kernel", "positive_affine")}
    meta = {"job": os.environ.get("SLURM_JOB_ID"), "seconds": time.time() - started,
            "n_children": len(ids), "n_units": len(rr), "seeds": E.SEEDS,
            "note_sha256": sha(NOTE), "source_record_sha256": provenance,
            "code_sha256": {str(p.relative_to(Path(core.REPO))): sha(p) for p in
                            (Path(__file__), Path(E.__file__), Path(S.__file__))}}
    result = {"meta": meta, "config_order": CONFIGS, "delta_positive_means": "calibration increased loss (NLL/Brier)",
              "identity_mean_contrasts": stats, "levels_by_seed": levels, "units": units}
    write(BASE / "per_identity.json", values)
    write(RESULT / "record_diagnosis.json", result)
    lines = ["# Private CS calibration diagnosis — exploratory, 2026-10-17", "",
             "Stage 1 reads all 120 CS_SINGLE panel records (8 configurations × 3 seeds × 5 folds). "
             "All 64 children are paired, with identical trial counts. No model was retrained. "
             "Positive ΔNLL means positive-affine calibration increased test loss relative to the stored class-kernel posterior.", "",
             "Child means across seeds are bootstrapped (4,000 draws); simultaneous intervals cover the eight configurations. "
             "They condition on the fitted models. Seeds do not increase n.", "",
             "| Configuration | ΔNLL 3401 / 3407 / 3413 | Child-mean ΔNLL [simultaneous 95%] |",
             "|---|---|---|"]
    for j, c in enumerate(CONFIGS):
        k = "|".join(c)
        ds = [levels[k][str(s)]["positive_affine"]["nll_bits"] - levels[k][str(s)]["class_kernel"]["nll_bits"] for s in E.SEEDS]
        st = stats["nll_bits"]
        lines.append(f"| {k.replace('|', ' / ')} | " + " / ".join(f"{x:+.5f}" for x in ds) +
                     f" | {st['est'][j]:+.5f} [{st['band_low'][j]:+.5f}, {st['band_high'][j]:+.5f}] |")
    lines += ["", "The stored native-score AUC is identical between methods for every child. "
              "A loss difference diagnoses the probability mapping, but does not by itself establish the cause. "
              "Stage 2's leave-one-out self-reference intervention remains separately registered and must reproduce the original scorer. "
              "No corrected GPU result is claimed by this report.", "",
              f"Slurm CPU job: {meta['job']}; analysis code SHA256: {sha(Path(__file__))}. "
              "Full code and record hashes, per-seed NLL/Brier/AUC levels and all unit calibration parameters are in "
              "results/auditory_alignment_v3/aln34/private_calibration/record_diagnosis.json. "
              "The original E_MULTI_SEED_RESULTS.md is retained."]
    body = "\n".join(lines) + "\n"
    assert not any(child in body for child in ids), "identity in aggregate report"
    DOC.write_text(body)
    os.chmod(DOC, 0o600)
    print(json.dumps({"units": len(rr), "children": len(ids), "job": meta["job"], "seconds": meta["seconds"]}), flush=True)


if __name__ == "__main__":
    analyze()
