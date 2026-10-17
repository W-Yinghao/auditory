"""ALN3.4 nested data subsets and independent inner-person source training.

Process-local hooks only; legacy trainer bytes and historical rows are untouched.
See DATA_AND_INNER_DESIGN_20261017.md. No outer-test evaluation for inner sources.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
from datetime import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import traceback

import numpy as np
import torch

from .. import core
from . import learning_budget as B

BASE = Path(core.OUT) / "aln34/data_inner_v1"
PLAN = BASE / "plan.json"
STORE = Path("<private checkpoint storage>/auditory_alignment_v3/aln34_data_inner_v1")
NOTE = Path(core.OUT) / "aln34/DATA_AND_INNER_DESIGN_20261017.md"
FAMILIES = {"ALN34_SPLIT_FM": "aligned32", "ALN34_SPLIT_LOCAL": "local_support"}
SELF = ("auditory_alignment_v3/aln34", "data_inner.py")


def register():
    for family, source in FAMILIES.items():
        files = core.FAMILY_CODE[source] + [SELF, B.SELF]
        group = family.lower()
        if group in core.FAMILY_CODE and core.FAMILY_CODE[group] != files:
            raise ValueError("family registration collision")
        core.FAMILY_CODE[group] = files
        core.FAMILY_GROUP[family] = group


def prefix(items, fraction, salt):
    """Stable nested group subsets independent of training seed and model."""
    items = sorted(set(items))
    if not items or fraction <= 0 or fraction > 1:
        raise ValueError("nonempty groups and fraction in (0,1] required")
    ranked = sorted(items, key=lambda x: hashlib.sha256(f"{salt}|{x}".encode()).hexdigest())
    return sorted(ranked[:max(1, math.ceil(fraction * len(ranked)))])


def metadata(coh):
    return {"participants": [{k: p[k] for k in ("id", "group", "fold")} for p in coh.participants],
            "segments": [{k: s[k] for k in ("p", "role", "kind", "uid", "part", "e0", "s0")} for s in coh.segments]}


def selection(meta, sf, cf, axis, fraction):
    people = meta["participants"]
    train = [p for p in people if p["fold"] != sf]
    inner = (sf + 1) % 5 if axis == "inner_person" else None
    if inner is not None:
        train = [p for p in train if p["fold"] != inner]
    if axis == "people":
        chosen = set()
        for group in sorted({p["group"] for p in train}):
            chosen.update(prefix([p["id"] for p in train if p["group"] == group], fraction,
                                 f"ALN34-20261017|people|sf{sf}|{group}"))
        train = [p for p in train if p["id"] in chosen]
    ids = sorted(p["id"] for p in train)
    indices = {i for i, p in enumerate(people) if p["id"] in ids}
    fit = [i for i, s in enumerate(meta["segments"]) if s["p"] in indices and s["role"] == "fit" and s["kind"] == "ss"]
    es = [i for i, s in enumerate(meta["segments"]) if s["p"] in indices and s["role"] == "es" and s["kind"] == "ss"]
    groups = sorted({meta["segments"][i]["part"] for i in fit})
    if axis == "content":
        groups = prefix(groups, fraction, f"ALN34-20261017|content|cf{cf}")
        fit = [i for i in fit if meta["segments"][i]["part"] in groups]
    if not fit or not es or len({meta['segments'][i]['uid'] for i in fit}) < 2:
        raise ValueError("subset has insufficient fit/es coverage")
    assert not any(p["fold"] in ({sf, inner} if inner is not None else {sf}) for p in train)
    return {"axis": axis, "fraction": fraction, "train_ids": ids, "fit_indices": fit, "es_indices": es,
            "content_groups": groups, "inner_fold": inner,
            "inner_ids": sorted(p["id"] for p in people if p["fold"] == inner) if inner is not None else [],
            "outer_ids": sorted(p["id"] for p in people if p["fold"] == sf)}


def make_row(source, split_key, split, digest):
    row = copy.deepcopy(source)
    local = source["family_id"] == "ALN32_LOCAL_SUPPORT"
    row["family_id"] = "ALN34_SPLIT_LOCAL" if local else "ALN34_SPLIT_FM"
    row["spec"].update(card="E34_INNER_PERSON_SOURCE" if split["axis"] == "inner_person" else "E34_LEARNING_CURVES",
                       split_key=split_key, axis=split["axis"], fraction=split["fraction"],
                       baseline_id=source["experiment_id"], baseline_family=source["family_id"],
                       epochs=B.EPOCHS[source["spec"]["architecture"]], design_sha256=digest)
    row.pop("experiment_id")
    row.pop("registered", None)
    row["experiment_id"] = "ALN34S_" + hashlib.sha256(B.dumps(row).encode()).hexdigest()[:16]
    row["registered"] = f"ALN3.4 data/inner source v1; {NOTE.relative_to(core.REPO)} SHA256 {digest}"
    return row


def make_plan():
    from auditory_alignment_v2.run import load_cohort
    register()
    original = core.load_rows() + [json.loads(x) for x in (Path(core.OUT) / "plan_ext.jsonl").read_text().splitlines()]
    sources = B.select_baselines(original)
    meta = {}
    for cf in range(2):
        coh = load_cohort(next(r for r in sources if r["content_fold"] == cf))
        meta[str(cf)] = metadata(coh)
        del coh
    splits, rows, baseline = {}, [], {}
    design = B.sha(NOTE)
    for source in sources:
        sf, cf, arch = source["subject_fold"], source["content_fold"], source["spec"]["architecture"]
        choices = [("inner_person", 1.0)]
        if arch != "reve" or source["seed"] == 3401:
            choices += [(axis, f) for axis in ("people", "content") for f in (0.25, 0.5)]
        recpath = Path(core.OUT) / "units" / f"{source['experiment_id']}.json"
        rec = json.loads(recpath.read_text())
        assert rec["status"] == "complete" and rec["row"] == source
        assert rec["code_hash"] == core.code_hash(source["family_id"])
        ckpt = Path(core.OUT) / "ckpt" / f"{source['experiment_id']}_best.pt"
        assert ckpt.is_file(), f"outer refit checkpoint absent: {ckpt}"
        baseline[source["experiment_id"]] = {"record_sha256": B.sha(recpath), "checkpoint_sha256": B.sha(ckpt),
                                             "code_hash": rec["code_hash"], "row": source}
        for axis, fraction in choices:
            key = f"sf{sf}_cf{cf}_{axis}_{fraction}"
            splits.setdefault(key, selection(meta[str(cf)], sf, cf, axis, fraction))
            rows.append(make_row(source, key, splits[key], design))
    assert len(rows) == len({r["experiment_id"] for r in rows}) == 590
    body = {"version": "ALN34_DATA_INNER_v1", "created": datetime.now().astimezone().isoformat(),
            "design_sha256": design, "source_sha256": B.sha(__file__), "rows": rows, "splits": splits,
            "code_hashes": {f: core.code_hash(f) for f in FAMILIES}, "baselines": baseline,
            "metadata_sha256": {cf: hashlib.sha256(B.dumps(m).encode()).hexdigest() for cf, m in meta.items()},
            "counts": {"reduced_data": 440, "inner_sources": 150, "reused_full_data_curve_references": 110},
            "selection_level": "curves: training-person ES content; inner sources: excludes outer+inner identities",
            "checkpoint_store": str(STORE)}
    if PLAN.exists():
        previous = json.loads(PLAN.read_text())
        assert all(previous[k] == body[k] for k in body if k != "created"), "immutable plan drift"
    else:
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
        BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
        link = BASE / "ckpt"
        if not link.exists():
            link.symlink_to(STORE, target_is_directory=True)
        assert link.is_symlink() and link.resolve() == STORE
        B.write(PLAN, body)
        PLAN.chmod(0o444)
    print(f"Registered 590 rows; plan SHA256 {B.sha(PLAN)}", flush=True)


def evaluation_view(coh, split):
    """Inner development gets only source-ES sound, never outer-test sound."""
    view = copy.copy(coh)
    view.segments = [dict(s) for s in coh.segments]
    held = set(split["inner_ids"])
    for s in view.segments:
        if s["role"] == "test":
            s["role"] = "excluded_outer_test_content"
        elif coh.participants[s["p"]]["id"] in held and s["role"] == "es":
            s["role"] = "test"
    return view


@contextlib.contextmanager
def instrumentation(row, plan, total):
    from auditory_alignment_v2 import train as T
    from .. import fm_aligned, fm_aligned32, local_train
    local = row["family_id"] == "ALN34_SPLIT_LOCAL"
    split = plan["splits"][row["spec"]["split_key"]]
    old_init, old_record = T.Batcher.__init__, core.write_record
    old_stats = local_train.target_stats if local else fm_aligned32.target_stats
    old_eval = core.evaluate_grid if local else fm_aligned.evaluate_aligned
    old_bind = core.bind

    def bind(r):
        b = old_bind(r)
        if r["experiment_id"] == row["experiment_id"]:
            b["spec"]["epochs"] = total
        return b

    def init(bt, coh, spec, r, dev):
        digest = hashlib.sha256(B.dumps(metadata(coh)).encode()).hexdigest()
        assert digest == plan["metadata_sha256"][str(row["content_fold"])], "cohort metadata drift"
        old_init(bt, coh, spec, r, dev)
        outer_fit = list(bt.fit)
        bt.fit, bt.es = list(split["fit_indices"]), list(split["es_indices"])
        bt.train_p = {i for i, p in enumerate(coh.participants) if p["id"] in split["train_ids"]}
        assert all(coh.segments[i]["p"] in bt.train_p for i in bt.fit + bt.es)
        bt._aln34_target_fit = list(bt.fit) if split["axis"] == "inner_person" else outer_fit
        retained = set(bt.fit)
        for i, s in enumerate(coh.segments):
            if s["kind"] == "ss" and s["role"] == "fit" and s["p"] in bt.train_p and i not in retained:
                s["role"] = "excluded_fit_content"

    def stats(bt, rng, *args, **kw):
        fit = bt.fit
        try:
            bt.fit = bt._aln34_target_fit
            return old_stats(bt, rng, *args, **kw)
        finally:
            bt.fit = fit

    def evaluate(b, enc, head, bt, coh, cal, grid):
        if split["axis"] != "inner_person":
            return old_eval(b, enc, head, bt, coh, cal, grid)
        view = evaluation_view(coh, split)
        previous = bt.coh_segments
        bt.coh_segments = view.segments
        try:
            out = old_eval({**b, "subject_fold": split["inner_fold"]}, enc, head, bt, view, cal, grid)
        finally:
            bt.coh_segments = previous
        out["evaluation_population"] = "independent inner identities, original source-ES content only"
        out["outer_test_evaluated"] = False
        return out

    def record(path, rec, start):
        rec.update(split=split, card=row["spec"]["card"], baseline_id=row["spec"]["baseline_id"],
                   actual_requested_epochs=total, truncated=total != row["spec"]["epochs"],
                   execution={"job": os.environ.get("SLURM_JOB_ID"), "plan_sha256": B.sha(PLAN)},
                   target_statistics_access="inner training audio only" if split["axis"] == "inner_person" else "full outer-training audio; common with reused baseline",
                   budget_interpretation="fixed epoch horizon; actual optimizer steps vary with available fit segments")
        old_record(path, rec, start)

    T.Batcher.__init__, core.write_record, core.bind = init, record, bind
    if local:
        local_train.target_stats, core.evaluate_grid = stats, evaluate
    else:
        fm_aligned32.target_stats, fm_aligned.evaluate_aligned = stats, evaluate
    try:
        yield
    finally:
        T.Batcher.__init__, core.write_record, core.bind = old_init, old_record, old_bind
        if local:
            local_train.target_stats, core.evaluate_grid = old_stats, old_eval
        else:
            fm_aligned32.target_stats, fm_aligned.evaluate_aligned = old_stats, old_eval


def verify(plan):
    register()
    assert plan["source_sha256"] == B.sha(__file__) and plan["design_sha256"] == B.sha(NOTE), "source/design drift"
    assert all(core.code_hash(f) == h for f, h in plan["code_hashes"].items()), "training code drift"


def run_one(row, plan, probe=False):
    out = BASE / "probes" / os.environ["SLURM_JOB_ID"] if probe else BASE
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not probe:
        assert (BASE / "ckpt").resolve() == STORE and (BASE / "ckpt").is_symlink()
    total = 2 if probe else row["spec"]["epochs"]
    with instrumentation(row, plan, total):
        if row["family_id"] == "ALN34_SPLIT_LOCAL":
            from ..local_support import run
        else:
            from ..run_aligned32 import run
        run(row, str(out), epochs=total)
    path = out / "units" / f"{row['experiment_id']}.json"
    rec = json.loads(path.read_text())
    if rec["status"] != "complete":
        raise RuntimeError(f"Unit failed: {rec.get('error')}")
    return rec


def worker(plan, lane, smoke_receipt):
    smoke = json.loads(Path(smoke_receipt).read_text())
    assert smoke["status"] == "pass" and smoke["plan_sha256"] == B.sha(PLAN), "matching engineering smoke required"
    claims = BASE / "claims"
    claims.mkdir(parents=True, exist_ok=True)
    for row in plan["rows"]:
        inner = row["spec"]["axis"] == "inner_person"
        if lane == "inner" and not inner or lane == "curves" and inner:
            continue
        eid = row["experiment_id"]
        if (BASE / "units" / f"{eid}.json").exists() or (BASE / "units" / f"{eid}.FAILED.json").exists():
            continue
        with (claims / f"{eid}.lock").open("a+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if (BASE / "units" / f"{eid}.json").exists():
                continue
            print(f"START {eid} {row['spec']['architecture']} {row['spec']['axis']}", flush=True)
            subprocess.run([sys.executable, "-B", "-m", "auditory_alignment_v3.aln34.data_inner", "--unit", eid], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--make-plan", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--unit")
    ap.add_argument("--lane", choices=("all", "inner", "curves"), default="all")
    ap.add_argument("--smoke-receipt", type=Path)
    args = ap.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Slurm is required")
    os.umask(0o077)
    if args.make_plan:
        make_plan()
        return
    plan = json.loads(PLAN.read_text())
    verify(plan)
    assert torch.cuda.is_available(), "requires a runfill GPU allocation"
    if args.smoke:
        receipt = {"status": "running", "plan_sha256": B.sha(PLAN), "units": []}
        # Cover all three architectures and both identity/content exclusions;
        # inner-person evaluation is checked with every architecture.
        targets = [(a, "inner_person") for a in B.EPOCHS] + [("lag_local_tokens", "people"), ("cbramod", "content")]
        try:
            for arch, axis in targets:
                row = next(r for r in plan["rows"] if r["spec"]["architecture"] == arch and r["spec"]["axis"] == axis)
                torch.cuda.reset_peak_memory_stats()
                rec = run_one(row, plan, probe=True)
                assert rec["truncated"] and rec["epochs_completed"] == 2
                receipt["units"].append({"id": row["experiment_id"], "axis": axis, "architecture": arch,
                                          "peak_mb": rec["gpu_peak_allocated_mb"], "seconds": rec["total_seconds"]})
            receipt["status"] = "pass"
        except BaseException:
            receipt["status"], receipt["traceback"] = "failed", traceback.format_exc()
            raise
        finally:
            B.write(BASE / "probes" / os.environ["SLURM_JOB_ID"] / "receipt.json", receipt)
    elif args.unit:
        run_one(next(r for r in plan["rows"] if r["experiment_id"] == args.unit), plan)
    else:
        if not args.smoke_receipt:
            raise ValueError("production requires --smoke-receipt")
        worker(plan, args.lane, args.smoke_receipt)


if __name__ == "__main__":
    main()
