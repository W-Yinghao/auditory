"""ALN3.4 bounded doubled-budget intervention; independent, versioned production plan.

The registered ALN32 trainers remain byte-identical. Process-local hooks preserve
fixed-time states, evaluate them without test-driven selection, and record provenance.
This lane has its own plan/output/claims; it never edits plan_ext or old code hashes.
All CLI computation requires Slurm. See RESEARCH_BUDGET_FIX_20261017.md.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import time
import traceback

import torch

from .. import core

BASE = Path(core.OUT) / "aln34" / "learning_budget_v2"
PLAN = BASE / "plan.json"
STORE = Path("<private checkpoint storage>/auditory_alignment_v3/aln34_learning_budget_v2")
NOTE = Path(core.OUT) / "aln34" / "RESEARCH_BUDGET_FIX_20261017.md"
FAMILIES = {"ALN34_BUDGET2_FM": "aligned32", "ALN34_BUDGET2_LOCAL": "local_support"}
SELF = ("auditory_alignment_v3/aln34", "learning_budget_v2.py")
SEEDS = (3401, 3407, 3413)
LR = {"cbramod": 3e-4, "reve": 1e-5}
EPOCHS = {"cbramod": 100, "reve": 50, "lag_local_tokens": 200}
FRACTIONS = (0.25, 0.5, 1.0, 2.0)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dumps(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    os.replace(tmp, path)


def register():
    """Install only this process's family hash entries, leaving all existing groups intact."""
    for family, source in FAMILIES.items():
        group = family.lower()
        files = core.FAMILY_CODE[source] + [SELF, ("auditory_alignment_v3/aln34", "budget_local_v2.py")]
        if group in core.FAMILY_CODE and core.FAMILY_CODE[group] != files:
            raise ValueError(f"registration collision: {group}")
        core.FAMILY_CODE[group] = files
        core.FAMILY_GROUP[family] = group


def select_baselines(rows):
    selected = []
    for row in rows:
        s = row["spec"]
        if row["dataset"] != "dtu" or row["seed"] not in SEEDS or s.get("objective") != "NCE":
            continue
        local = row["family_id"] == "ALN32_LOCAL_SUPPORT" and s.get("variant") == "local_aligned1000"
        fm = (row["family_id"] == "ALN32_TRUE_FULL" and s.get("recipe") == "full_onestep_v1"
              and s.get("architecture") in LR and s.get("adaptation") in ("pretrained_full", "random_full")
              and float(s.get("lr_backbone", -1)) == LR[s["architecture"]])
        if local or fm:
            selected.append(row)
    keys = [(r["seed"], r["subject_fold"], r["content_fold"], r["spec"]["architecture"], r["spec"].get("adaptation", "local"))
            for r in selected]
    wanted = {(seed, sf, cf, arch, ad) for seed in SEEDS for sf in range(5) for cf in range(2)
              for arch, ads in (("cbramod", ("pretrained_full", "random_full")), ("reve", ("pretrained_full", "random_full")),
                                ("lag_local_tokens", ("local",))) for ad in ads}
    if len(keys) != len(set(keys)) or set(keys) != wanted:
        raise ValueError(f"baseline coverage mismatch: selected={len(keys)}, missing={sorted(wanted-set(keys))[:8]}, "
                         f"unexpected={sorted(set(keys)-wanted)[:8]}")
    return sorted(selected, key=lambda r: (r["seed"], r["subject_fold"], r["content_fold"], r["spec"]["architecture"],
                                           r["spec"].get("adaptation", "local")))


def new_row(source, record, note_sha):
    row = copy.deepcopy(source)
    old = row["experiment_id"]
    local = source["family_id"] == "ALN32_LOCAL_SUPPORT"
    row["family_id"] = "ALN34_BUDGET2_LOCAL" if local else "ALN34_BUDGET2_FM"
    s = row["spec"]
    s.update(card="E34_LEARNING_CURVES", intervention="doubled_budget_v2", baseline_id=old,
             baseline_family=source["family_id"], baseline_code_hash=record["code_hash"],
             baseline_epochs=EPOCHS[s["architecture"]], epochs=2 * EPOCHS[s["architecture"]],
             trajectory_fractions=list(FRACTIONS), research_note_sha256=note_sha)
    row.pop("experiment_id")
    row.pop("registered", None)
    row["experiment_id"] = "ALN34B2_" + hashlib.sha256(dumps(row).encode()).hexdigest()[:16]
    row["registered"] = f"ALN3.4 result-informed budget comparison; {NOTE.relative_to(core.REPO)} sha256 {note_sha}"
    return row


def make_plan(path=PLAN):
    register()
    rows = core.load_rows() + [json.loads(line) for line in (Path(core.OUT) / "plan_ext.jsonl").read_text().splitlines()]
    selected = select_baselines(rows)
    note_sha = sha(NOTE)
    new, baseline_files = [], {}
    for source in selected:
        record_path = Path(core.OUT) / "units" / (source["experiment_id"] + ".json")
        record = json.loads(record_path.read_text())
        if record.get("status") != "complete" or record.get("row") != source:
            raise ValueError(f"baseline missing, unfinished or row drift: {record_path}")
        if record["code_hash"] != core.code_hash(source["family_id"]):
            raise ValueError(f"baseline code changed: {source['experiment_id']}")
        new.append(new_row(source, record, note_sha))
        baseline_files[source["experiment_id"]] = {"record_sha256": sha(record_path), "code_hash": record["code_hash"],
                                                   "epochs": record["epochs_completed"], "optimizer_steps": record["optimizer_steps"]}
    assert len(new) == len({r["experiment_id"] for r in new}) == 150
    body = {"schema": "aln34_learning_budget_v2", "registered_at": datetime.now().astimezone().isoformat(),
            "note": str(NOTE), "note_sha256": note_sha, "rows": new, "baselines": baseline_files,
            "code_hashes": {f: core.code_hash(f) for f in FAMILIES}, "source_sha256": sha(__file__),
            "scope": "DTU full population/content, doubled cosine horizon; initialization pairs matched within architecture",
            "selection": "unchanged training-identity early-stopping content; no outer-test timepoint selection",
            "out": str(BASE), "checkpoint_storage": str(STORE)}
    if Path(path).exists():
        previous = json.loads(Path(path).read_text())
        if any(previous.get(k) != body[k] for k in ("rows", "baselines", "code_hashes", "source_sha256", "note_sha256")):
            raise ValueError("frozen plan already exists with different provenance; create a new execution version")
        print(f"Existing plan verified: {path}; 150 rows", flush=True)
        return previous
    write(path, body)
    Path(path).chmod(0o444)
    print(f"Registered {len(new)} independent-plan rows: {path}; sha256 {sha(path)}", flush=True)
    return body


def snapshot_epochs(base_epochs, total):
    return sorted({min(total, max(1, int(base_epochs * fraction + 0.5))) for fraction in FRACTIONS})


def cpu_state(module):
    return {k: v.detach().cpu().clone() for k, v in module.state_dict().items()}


@contextlib.contextmanager
def instrumentation(row, out, total, captures):
    """Hook only this fresh unit process. Existing trainers perform every optimizer update."""
    local = row["family_id"] == "ALN34_BUDGET2_LOCAL"
    if local:
        from .. import local_train as legacy_local
        from .. import local_support
        from . import budget_local_v2 as trainer
        old_fit = legacy_local.fit_continuous
        old_grid, old_snapshot = trainer.GridBatcher, trainer.SNAPSHOT
        legacy_local.fit_continuous = trainer.fit_continuous
        trainer.GridBatcher = local_support.batcher_for("aligned1000")
    else:
        from .. import fm_aligned, fm_aligned32
        trainer = fm_aligned32
    original_save, original_write, original_bind = trainer._save_resume, core.write_record, core.bind
    original_eval = core.evaluate_grid if local else fm_aligned.evaluate_aligned
    selected_epochs = snapshot_epochs(row["spec"]["baseline_epochs"], total)
    prefix = Path(out) / "ckpt" / row["experiment_id"]
    code = core.code_hash(row["family_id"])

    def bind(r):
        b = original_bind(r)
        if r["experiment_id"] == row["experiment_id"]:
            b["spec"]["epochs"] = total
        return b

    def save(path, **payload):
        original_save(path, **payload)
        epoch = int(payload["epoch"])
        if not local and epoch in selected_epochs:
            target = Path(str(prefix) + f"_trajectory_e{epoch:04d}.pt")
            record = {k: payload[k] for k in (("enc", "head") if local else ("model",))}
            record.update(epoch=epoch, optimizer_steps=int(payload["step"]), code_hash=code,
                          experiment_id=row["experiment_id"], baseline_fraction=epoch / row["spec"]["baseline_epochs"])
            torch.save(record, str(target) + ".tmp")
            os.replace(str(target) + ".tmp", target)

    def local_snapshot(epoch, step, enc, head):
        if epoch not in selected_epochs:
            return
        target = Path(str(prefix) + f"_trajectory_e{epoch:04d}.pt")
        value = {"enc": cpu_state(enc), "head": cpu_state(head), "epoch": epoch,
                 "optimizer_steps": step, "code_hash": code, "experiment_id": row["experiment_id"],
                 "baseline_fraction": epoch / row["spec"]["baseline_epochs"]}
        torch.save(value, str(target) + ".tmp")
        os.replace(str(target) + ".tmp", target)

    def evaluate(*args, **kw):
        main = original_eval(*args, **kw)
        model, head = args[1], args[2]
        state = cpu_state(model)
        head_state = cpu_state(head) if local else None
        try:
            for epoch in selected_epochs:
                target = Path(str(prefix) + f"_trajectory_e{epoch:04d}.pt")
                snap = torch.load(target, map_location="cpu", weights_only=True)
                if snap["code_hash"] != code or snap["experiment_id"] != row["experiment_id"]:
                    raise ValueError("trajectory checkpoint provenance mismatch")
                model.load_state_dict(snap["enc"] if local else snap["model"])
                if local:
                    head.load_state_dict(snap["head"])
                model.eval(); head.eval()
                started = time.time()
                value = original_eval(*args, **kw)
                captures.append({"epoch": epoch, "optimizer_steps": snap["optimizer_steps"],
                                 "baseline_fraction": snap["baseline_fraction"], "state_kind": "fixed_epoch_state",
                                 "eval": value, "eval_seconds": round(time.time() - started, 3),
                                 "checkpoint": str(target), "checkpoint_sha256": sha(target)})
        finally:
            model.load_state_dict(state)
            if local:
                head.load_state_dict(head_state)
            model.eval(); head.eval()
        return main

    def record(path, rec, start):
        rec.update(card="E34_LEARNING_CURVES", intervention="doubled_budget_v2", trajectory=captures,
                   baseline_id=row["spec"]["baseline_id"], baseline_code_hash=row["spec"]["baseline_code_hash"],
                   planned_epochs=row["spec"]["epochs"], actual_requested_epochs=total,
                   truncated=total != row["spec"]["epochs"],
                   selection_level="training identities, held-out early-stopping content; fixed trajectory states never selected on test",
                   execution={"slurm_job": os.environ.get("SLURM_JOB_ID"), "host": socket.gethostname(),
                              "plan_sha256": sha(PLAN) if PLAN.exists() else None,
                              "note_sha256": row["spec"]["research_note_sha256"]})
        original_write(path, rec, start)

    trainer._save_resume, core.write_record, core.bind = save, record, bind
    if local:
        core.evaluate_grid = evaluate
        trainer.SNAPSHOT = local_snapshot
    else:
        fm_aligned.evaluate_aligned = evaluate
    try:
        yield
    finally:
        trainer._save_resume, core.write_record, core.bind = original_save, original_write, original_bind
        if local:
            core.evaluate_grid = original_eval
            legacy_local.fit_continuous = old_fit
            trainer.GridBatcher, trainer.SNAPSHOT = old_grid, old_snapshot
        else:
            fm_aligned.evaluate_aligned = original_eval


def run_one(row, out=BASE, probe=False):
    register()
    out = Path(out)
    if probe and out.resolve() == BASE.resolve():
        raise ValueError("truncated probes cannot write production outputs")
    if not probe and out.resolve() != BASE.resolve():
        raise ValueError("production output root differs from the registered plan")
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not probe:
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
        ck = out / "ckpt"
        if not ck.exists():
            ck.symlink_to(STORE, target_is_directory=True)
        if not ck.is_symlink() or ck.resolve() != STORE.resolve():
            raise ValueError("production checkpoints must use the registered /projects storage")
    total = 2 if probe else row["spec"]["epochs"]
    with instrumentation(row, out, total, []):
        if row["family_id"] == "ALN34_BUDGET2_FM":
            from ..run_aligned32 import run
        else:
            from ..local_support import run
        run(row, str(out), epochs=total)


def verify_plan(plan):
    register()
    if plan["source_sha256"] != sha(__file__) or plan["note_sha256"] != sha(NOTE):
        raise ValueError("frozen plan source/note drift")
    for family, expected in plan["code_hashes"].items():
        if core.code_hash(family) != expected:
            raise ValueError(f"frozen training code drift: {family}")


def worker(plan, max_units=None):
    """Whole-card sequential worker; flock claims survive pre-emption without stale ownership."""
    verify_plan(plan)
    claims = BASE / "claims"
    claims.mkdir(parents=True, exist_ok=True, mode=0o700)
    done = 0
    for row in plan["rows"]:
        eid = row["experiment_id"]
        record = BASE / "units" / (eid + ".json")
        failed = BASE / "units" / (eid + ".FAILED.json")
        if record.exists() or failed.exists():
            continue
        with (claims / (eid + ".lock")).open("a+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if record.exists() or failed.exists():
                continue
            lock.seek(0); lock.truncate()
            lock.write(dumps({"job": os.environ.get("SLURM_JOB_ID"), "host": socket.gethostname(),
                              "code_hash": core.code_hash(row["family_id"])})); lock.flush()
            print(f"START {eid} {row['spec']['architecture']} {row['spec'].get('adaptation', 'local')}", flush=True)
            # Use a fresh process per unit; module globals and GPU allocations do not carry across units.
            import subprocess
            result = subprocess.run([os.sys.executable, "-B", "-m", "auditory_alignment_v3.aln34.learning_budget_v2",
                                     "--unit", eid, "--plan", str(PLAN)], check=False)
            if result.returncode:
                print(f"FAILED {eid} exit={result.returncode}; preserved record/checkpoints for diagnosis", flush=True)
                if not failed.exists():
                    raise RuntimeError(f"unit exited without a result: {eid}")
            done += 1
            if max_units is not None and done >= max_units:
                break
    print(f"worker end: {done} units attempted", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--make-plan", action="store_true")
    ap.add_argument("--plan", type=Path, default=PLAN)
    ap.add_argument("--unit")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--max-units", type=int)
    args = ap.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("run all analyses/tests/training through Slurm")
    os.umask(0o077)
    if args.make_plan:
        make_plan(args.plan)
        return
    plan = json.loads(args.plan.read_text())
    verify_plan(plan)
    if not torch.cuda.is_available():
        raise RuntimeError("GPU execution needs a runfill GPU allocation")
    if args.smoke:
        seen = set()
        receipt = {"job": os.environ["SLURM_JOB_ID"], "status": "running", "units": []}
        out = BASE / "probes" / os.environ["SLURM_JOB_ID"]
        try:
            for row in plan["rows"]:
                key = row["spec"]["architecture"]
                if key in seen:
                    continue
                seen.add(key)
                torch.cuda.reset_peak_memory_stats()
                run_one(row, out, probe=True)
                rec = json.loads((out / "units" / (row["experiment_id"] + ".json")).read_text())
                assert rec["status"] == "complete" and rec["truncated"] and rec["epochs_completed"] == 2
                assert [x["epoch"] for x in rec["trajectory"]] == [2]
                receipt["units"].append({"id": row["experiment_id"], "architecture": key,
                                          "code_hash": rec["code_hash"], "gpu_peak_mb": rec["gpu_peak_allocated_mb"]})
            receipt["status"] = "pass"
        except BaseException:
            receipt["status"] = "failed"; receipt["traceback"] = traceback.format_exc()
            raise
        finally:
            write(out / "receipt.json", receipt)
    elif args.unit:
        selected = [r for r in plan["rows"] if r["experiment_id"] == args.unit]
        if len(selected) != 1:
            raise ValueError("unit must identify exactly one registered row")
        run_one(selected[0])
    else:
        worker(plan, args.max_units)


if __name__ == "__main__":
    main()
