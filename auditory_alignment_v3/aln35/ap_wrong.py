"""ALN3.5 bounded matched AP/APwrong h30 execution, isolated from prior33.

The plan freezes three target-excluded lineages.  Donor control pairs share one
stream, initialisation, head, optimiser and fixed h30 schedule.  Only the audio
array is permuted.  Targets call the unchanged prior33 adaptation/evaluation
implementation through an explicitly recorded AP-shaped loading adapter.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import gc
import hashlib
import json
import math
import os
import time
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from ..prior33 import contract as C, donor_train as D, losses as L, model as M
from ..prior33 import target_train as T, views as V
from .ap_wrong_sampler import PairSampler, RULE, REVISION, mask_sha

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "private/auditory_alignment_v3/aln35/apwrong_v1"
STORAGE = Path("<private checkpoint storage>/auditory_alignment_v3/aln35_apwrong_v1")
PLAN = OUT / "plan.json"
FORMAT = "aln35_apwrong_h30_v1"
ARMS = ("AP", "APwrong")


def sha(path):
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".{os.getpid()}.tmp")
    replaced = []
    def safe(obj, at=()):
        if isinstance(obj, float) and not math.isfinite(obj):
            replaced.append(".".join(map(str, at)))
            return None
        if isinstance(obj, dict):
            return {key: safe(item, at + (key,)) for key, item in obj.items()}
        if isinstance(obj, list):
            return [safe(item, at + (i,)) for i, item in enumerate(obj)]
        return obj
    payload = safe(D._py(value))
    if replaced and isinstance(payload, dict):
        payload["nonfinite_to_null"] = {"count": len(replaced), "paths": replaced}
    temp.write_text(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n")
    os.replace(temp, path)


def state_sha(state):
    h = hashlib.sha256()
    for name, value in sorted(state.items()):
        h.update(name.encode() + b"\0")
        h.update(str(value.dtype).encode())
        h.update(np.asarray(value.shape, dtype="<i8").tobytes())
        h.update(value.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def open_plan(path=PLAN):
    path = Path(path)
    expected = path.with_suffix(".sha256").read_text().strip()
    if sha(path) != expected:
        raise ValueError("APwrong plan hash mismatch")
    plan = json.loads(path.read_text())
    for name, value in plan["code_hashes"].items():
        if sha(ROOT / name) != value:
            raise ValueError(f"frozen APwrong code changed: {name}")
    for name, value in plan["input_hashes"].items():
        if sha(name) != value:
            raise ValueError(f"frozen APwrong source changed: {name}")
    return plan, expected


def load_npz_equal(path, values):
    if not path.exists():
        return False
    with np.load(path, allow_pickle=False) as previous:
        if set(previous.files) != set(values) or any(not np.array_equal(previous[k], v) for k, v in values.items()):
            raise ValueError(f"deterministic ledger replay disagrees: {path}")
    return True


class BatchLedger:
    """Exact correspondence evidence under /projects; no EEG/audio values."""
    def __init__(self, directory, unknown_clock, state=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.unknown = unknown_clock
        self.pending = []
        self.files = list((state or {}).get("files", []))
        self.strata = Counter((state or {}).get("strata", {}))
        self.presentations = Counter((state or {}).get("presentations", {}))
        self.families = Counter((state or {}).get("families", {}))
        self.chain = (state or {}).get("chain", hashlib.sha256(RULE.encode()).hexdigest())
        for item in self.files:
            if sha(self.directory / item["name"]) != item["sha256"]:
                raise ValueError("committed ledger chunk changed")

    def add(self, batch, perm):
        keys = batch.keys.cpu().numpy().astype(np.int64)
        fam, pres, sample = C.unpack_key(keys)
        actual = keys[perm]
        mhash = mask_sha(keys, self.unknown)
        h = hashlib.sha256(bytes.fromhex(self.chain))
        h.update(keys.astype("<i8").tobytes()); h.update(np.asarray(perm, dtype="<i2").tobytes())
        h.update(bytes.fromhex(mhash)); self.chain = h.hexdigest()
        self.pending.append((batch.step, keys, actual, np.asarray(perm, dtype=np.uint16),
                             sample.astype(np.int64), sample[perm].astype(np.int64), mhash))
        self.strata[batch.stratum] += 1
        self.presentations.update(map(str, pres.tolist()))
        self.families.update(map(str, fam.tolist()))
        if len(self.pending) >= 512:
            self.flush()

    def flush(self):
        if not self.pending:
            return
        rows = self.pending
        values = {"step": np.asarray([r[0] for r in rows], np.int64),
                  "nominal_keys": np.stack([r[1] for r in rows]),
                  "actual_audio_keys": np.stack([r[2] for r in rows]),
                  "audio_row_permutation": np.stack([r[3] for r in rows]),
                  "nominal_interval_start": np.stack([r[4] for r in rows]),
                  "actual_interval_start": np.stack([r[5] for r in rows]),
                  "interval_length_samples": np.asarray(C.N_TGT, np.int64),
                  "nominal_positive_exclusion_mask_sha256": np.asarray([r[6] for r in rows], dtype="U64")}
        name = f"steps_{rows[0][0]:08d}_{rows[-1][0]:08d}.npz"
        path = self.directory / name
        if not load_npz_equal(path, values):
            temp = path.with_suffix(".tmp.npz")
            np.savez_compressed(temp, **values)
            os.replace(temp, path)
        self.files.append({"name": name, "sha256": sha(path), "n_steps": len(rows)})
        self.pending.clear()

    def state(self):
        self.flush()
        return {"files": self.files, "chain": self.chain, "strata": dict(self.strata),
                "presentations": dict(self.presentations), "families": dict(self.families)}


def build_pair(manifest, target, device):
    names = [n for n in C.VOCAB if n in set(manifest["seen"][target])]
    encoders = {arm: M.build_shared(names, names, 3401).to(device) for arm in ARMS}
    initial = {arm: state_sha(enc.state_dict()) for arm, enc in encoders.items()}
    if len(set(initial.values())) != 1:
        raise AssertionError("AP and APwrong initialisation differs")
    return encoders, initial


def train_donor(unit, plan, plan_sha, *, probe_steps=None, probe_tag=None):
    device = torch.device("cuda")
    determinism = D.determinism(device)
    man = V.open_for_row(unit["source_row"])
    target, uid = unit["dataset"], unit["unit_id"]
    storage = STORAGE / ("production" if probe_steps is None else f"probes/{probe_tag}") / uid
    storage.mkdir(parents=True, exist_ok=True)
    sampler = PairSampler(man, target, 3401, device, revised=True)
    heads = {key: head.to(device).eval() for key, head in M.fixed_heads(man, man.root).items()}
    encoders, initial = build_pair(man, target, device)
    sigma = D.calibrate_bandwidths(encoders["AP"], sampler, heads)
    unknown = L.unknown_clock_families(man)
    members = {arm: D._Member("AP", encoders[arm], "NCE", sigma, unknown, heads) for arm in ARMS}
    validator = D.DevValidator(man, device, heads["env"])
    schedule = D.GroupWSD(man["budget"]["anchors_per_ep_eq"], adopted=30, limit=30)
    end = schedule.steps_at(30)
    if end != unit["updates_per_member"]:
        raise ValueError("h30 update budget disagrees with frozen plan")
    stop = min(end, int(probe_steps)) if probe_steps is not None else end
    validations = {schedule.steps_at(e): e for e in range(1, 31)}
    if probe_steps is not None:
        validations[stop] = schedule.ep_eq_of(stop)
    state_path = storage / "resume.pt"
    curves, best, time_by_arm = {arm: [] for arm in ARMS}, {arm: None for arm in ARMS}, {arm: 0.0 for arm in ARMS}
    start, resumes, ledger_state = 0, [], None
    if state_path.exists():
        state = D._load(str(state_path))
        if state["plan_sha256"] != plan_sha or state["unit_id"] != uid or state["code_hashes"] != plan["code_hashes"]:
            raise ValueError("resume belongs to other source/plan/code")
        if state["probe_steps"] != probe_steps:
            raise ValueError("probe and production resume budgets differ")
        sigma = state["sigma"]
        for arm in ARMS:
            members[arm].restore(state["members"][arm])
            members[arm].counts = state["counts"][arm]
            members[arm].sigma = sigma
            members[arm].acc.__dict__.update(copy.deepcopy(state["accumulators"][arm]))
        sampler.load_state(state["sampler"])
        torch.set_rng_state(state["torch_rng"].cpu())
        torch.cuda.set_rng_state_all(state["cuda_rng"])
        start, curves, best = state["step"], state["curves"], state["best"]
        for arm, selected_state in state["selected_checkpoints"].items():
            if selected_state is not None:
                D._save(str(storage / f"{arm}_best.pt"), selected_state)
        ledger_state, time_by_arm = state["ledger"], state["time_by_arm"]
        resumes = state["resumes"] + [{"at_step": start, "device": torch.cuda.get_device_name(), "job": os.environ.get("SLURM_JOB_ID")}]
    ledger = BatchLedger(storage / "ledger", unknown, ledger_state)
    started = time.time()
    for step in range(start, stop):
        batch = sampler.next_batch()
        permutation = sampler.last_perm
        with torch.no_grad():
            audio = heads["env"](batch.y)
            wrong_audio = audio[torch.as_tensor(permutation, device=device)]
        ledger.add(batch, permutation)
        learning_rate = D.LR * schedule.lr_scale(step)
        for arm, values in (("AP", audio), ("APwrong", wrong_audio)):
            before = D._clock(device)
            members[arm].step(batch, values, None, None, learning_rate, "main")
            time_by_arm[arm] += D._clock(device) - before
            if members[arm].counts["main"]["nonfinite"]:
                raise FloatingPointError(f"{arm} non-finite update {step}; no unmatched update skipping")
        current = step + 1
        if current in validations:
            scores = validator.validate(encoders, sigma)
            for arm in ARMS:
                dev = scores[arm]["dev"]
                if not math.isfinite(float(dev["ce_bits"])):
                    raise FloatingPointError(f"{arm} non-finite true-paired donor-dev NLL")
                candidate = {"step": current, "ep_eq": validations[current], "branch": "h30_common",
                             "phase": "stable" if current <= schedule.steps_at(27) else "decay",
                             "dev": dev, "diag": scores[arm]["diag"], "train": members[arm].acc.summary()}
                curves[arm].append(candidate)
                members[arm].acc = D._Acc()
                if best[arm] is None or dev["ce_bits"] < best[arm]["dev"]["ce_bits"]:
                    best[arm] = copy.deepcopy(candidate)
                    D._save(str(storage / f"{arm}_best.pt"), {
                        "format": FORMAT, "unit_id": uid, "arm": arm, "kind": "h30_source_dev_best",
                        "enc": D._state(encoders[arm]), "head": D._state(heads["env"]), "sigma": sigma,
                        "validation": candidate, "manifest_sha256": man.sha256, "contract": C.CONTRACT,
                        "plan_sha256": plan_sha, "code_hashes": plan["code_hashes"], "initial_state_sha256": initial[arm]})
            print(json.dumps({"unit": uid, "step": current, "ep_eq": validations[current],
                              "dev_ce": {arm: scores[arm]["dev"]["ce_bits"] for arm in ARMS}}), flush=True)
        if current in validations or current % 1000 == 0 or current == stop:
            D._save(str(state_path), {"format": FORMAT, "unit_id": uid, "plan_sha256": plan_sha,
                "code_hashes": plan["code_hashes"], "probe_steps": probe_steps, "step": current, "sigma": sigma,
                "members": {arm: members[arm].snapshot() for arm in ARMS},
                "accumulators": {arm: copy.deepcopy(members[arm].acc.__dict__) for arm in ARMS},
                "counts": {arm: members[arm].counts for arm in ARMS}, "sampler": sampler.state(),
                "torch_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state_all(),
                "curves": curves, "best": best, "ledger": ledger.state(), "time_by_arm": time_by_arm,
                "selected_checkpoints": {arm: (None if best[arm] is None else
                    D._load(str(storage / f"{arm}_best.pt"))) for arm in ARMS},
                "resumes": resumes})
    checkpoints = {}
    for arm in ARMS:
        ck = storage / f"{arm}_best.pt"
        if not ck.exists():
            raise AssertionError("no source-dev selected checkpoint")
        checkpoints[arm] = {"path": str(ck), "sha256": sha(ck), "selected": best[arm]}
    if probe_steps is None and any(members[arm].counts["main"]["updates"] != end for arm in ARMS):
        raise AssertionError("donor pair did not receive the fixed h30 update budget")
    if probe_steps is None and sampler.stream_hash() != unit["spec"]["revised_stream_sha256"]:
        raise AssertionError("actual GPU sampler stream differs from the fully audited frozen source stream")
    result = {"format": FORMAT, "unit_id": uid, "stage": "donor_pair", "dataset": target,
              "status": "complete" if probe_steps is None else "probe_complete", "plan_sha256": plan_sha,
              "source_row": unit["source_row"], "source_audit": unit["source_audit"],
              "source_exclusions": man["donor_sets"][target]["core"], "manifest_sha256": man.sha256,
              "target_contract": man["target_contract"], "initial_state_sha256": initial,
              "fixed_audio_head_state_sha256": state_sha(heads["env"].state_dict()),
              "optimizer": D.OPTIMIZER, "steps_per_member": stop, "requested_updates_per_member": end,
              "horizon_ep_eq": 30, "schedule": schedule.describe(), "no_result_dependent_extensions": True,
              "selection": "same true-paired donor-dev calibrated CE; strict lower; earlier tie; epochs 1..30; no epoch0",
              "selection_level": D.SELECTION_LEVEL, "score_sets": validator.sizes(),
              "curves": curves, "checkpoints": checkpoints,
              "nominal_mask_unchanged": True, "wrong_rule": RULE, "common_sampler_revision": REVISION,
              "sampler_rejections": dict(sampler.rejections), "stream_sha256": sampler.stream_hash(),
              "correspondence_ledger": {"directory": str(ledger.directory), **ledger.state(),
                  "canonical_group_rule": "known clock: (family, sample); unknown clock: (family, presentation, sample)",
                  "interval": "[start,start+8) at 64 Hz; whole-family exclusion also excludes overlapping neighbours",
                  "audio_exposure": "AP and APwrong use the identical per-step multiset; recorded histograms apply to both",
                  "eeg_views": "both unchanged; nominal positives 2B x B, original keys and masks"},
              "determinism": determinism, "device": torch.cuda.get_device_name(), "resumed": resumes,
              "gpu_seconds_by_arm": time_by_arm, "seconds_this_invocation": time.time() - started,
              "job": os.environ.get("SLURM_JOB_ID"), "code_hashes": plan["code_hashes"]}
    return result


def train_target(unit, plan, plan_sha, donor_record, *, epochs=None, probe_tag=None):
    device = torch.device("cuda")
    D.determinism(device)
    arm, uid = unit["arm"], unit["unit_id"]
    checkpoint = donor_record["checkpoints"][arm]
    if sha(checkpoint["path"]) != checkpoint["sha256"] or donor_record["plan_sha256"] != plan_sha:
        raise ValueError("donor checkpoint or source plan changed")
    if epochs is None and donor_record["status"] != "complete":
        raise ValueError("production target cannot use a probe donor")
    donor = T.load_donor_state(checkpoint["path"])
    if donor["arm"] != arm or donor["unit_id"] != unit["donor_unit"]:
        raise ValueError("wrong arm or target-excluded donor lineage")
    row = copy.deepcopy(unit["adapter_row"])
    man = V.open_for_row(row)
    if man.sha256 != donor["manifest_sha256"] or donor_record["dataset"] != unit["dataset"]:
        raise ValueError("target/manifest binding changed")
    generated = T.check_generated()
    if not generated["ok"]:
        raise ValueError(generated["problems"])
    path = STORAGE / ("production" if epochs is None else f"probes/{probe_tag}") / "targets"
    path.mkdir(parents=True, exist_ok=True)
    ck = str(path / uid)
    log = {}
    if unit["dataset"] == "private_bdf":
        result = T.adapt_private(row, man, device, ck, log, donor, epochs=epochs)
    else:
        result = T.adapt_public(row, man, device, ck, log, donor, epochs=epochs)
    return {"format": FORMAT, "unit_id": uid, "stage": "target", "dataset": unit["dataset"],
            "arm": arm, "status": "complete" if epochs is None else "probe_complete",
            "subject_fold": row["subject_fold"], "content_fold": row["content_fold"], "seed": 3401,
            "plan_sha256": plan_sha, "manifest_sha256": man.sha256, "target_contract": row["spec"]["target_contract"],
            "source_template": unit["source_template"], "adapter_row": row,
            "adapter_note": "AP-shaped loader contract only; actual trained donor arm is recorded separately and hash-checked",
            "donor_unit": unit["donor_unit"], "donor_checkpoint": checkpoint, "scratch_reference": unit["scratch_reference"],
            "original_ap_reference": unit["original_ap_reference"], "generated_check": generated,
            "code_hashes": plan["code_hashes"], "device": torch.cuda.get_device_name(),
            "job": os.environ.get("SLURM_JOB_ID"), "training": log, **result}


def probe(plan, plan_sha, dataset, steps, tag):
    donor = next(unit for unit in plan["units"] if unit["stage"] == "donor_pair" and unit["dataset"] == dataset)
    base = OUT / "probes" / tag
    base.mkdir(parents=True, exist_ok=True)
    donor_result = train_donor(donor, plan, plan_sha, probe_steps=steps, probe_tag=tag)
    write(base / f'{donor["unit_id"]}.json', donor_result)
    target = next(unit for unit in plan["units"] if unit["stage"] == "target" and unit["dataset"] == dataset
                  and unit["arm"] == "APwrong")
    target_result = train_target(target, plan, plan_sha, donor_result, epochs=1, probe_tag=tag)
    write(base / f'{target["unit_id"]}.json', target_result)
    receipt = {"status": "PASS", "dataset": dataset, "plan_sha256": plan_sha,
               "donor_steps_per_arm": steps, "donor_pair": donor["unit_id"], "target": target["unit_id"],
               "target_epochs": 1, "no_performance_gate": True, "job": os.environ.get("SLURM_JOB_ID"),
               "code_hashes": plan["code_hashes"], "device": torch.cuda.get_device_name()}
    write(base / "receipt.json", receipt)
    write(OUT / "engineering" / f"{dataset}.json", receipt)
    return receipt


def worker(plan, plan_sha, stage, max_units, dataset=None):
    completed = 0
    for unit in plan["units"]:
        if stage != "all" and unit["stage"] != stage:
            continue
        if dataset and unit["dataset"] != dataset:
            continue
        uid = unit["unit_id"]
        dest = OUT / "units" / f"{uid}.json"
        failed = OUT / "units" / f"{uid}.FAILED.json"
        ready = OUT / "engineering" / f'{unit["dataset"]}.json'
        if not ready.exists() or json.loads(ready.read_text()).get("plan_sha256") != plan_sha:
            continue
        if dest.exists() or failed.exists():
            continue
        dep = OUT / "units" / f'{unit.get("donor_unit")}.json'
        if unit["stage"] == "target" and not dep.exists():
            continue
        lock_path = OUT / "claims" / f"{uid}.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if dest.exists() or failed.exists():
                continue
            try:
                result = (train_donor(unit, plan, plan_sha) if unit["stage"] == "donor_pair" else
                          train_target(unit, plan, plan_sha, json.loads(dep.read_text())))
                write(dest, result)
            except Exception as error:
                write(failed, {"status": "technical_failed", "unit_id": uid, "plan_sha256": plan_sha,
                               "error": str(error), "traceback": traceback.format_exc(), "job": os.environ.get("SLURM_JOB_ID")})
                raise
            completed += 1
            gc.collect(); torch.cuda.empty_cache()
            if completed >= max_units:
                break
    return {"completed_this_worker": completed, "plan_sha256": plan_sha}


def fleet_status():
    """Read-only status plugin; the project fleet owns every GPU submission."""
    result = {"name": "c3_s35apwrong", "lane": "s35_apwrong", "state": "not_registered",
              "ready": 0, "remaining": 53, "slots": 1, "initial": [],
              "submit": ["slurm/aln35_apwrong_gpu.sbatch", "worker", "--max-units", "1"]}
    if not PLAN.exists() or not PLAN.with_suffix(".sha256").exists():
        return result
    expected = PLAN.with_suffix(".sha256").read_text().strip()
    if sha(PLAN) != expected:
        return {**result, "state": "plan_hash_mismatch"}
    plan = json.loads(PLAN.read_text())
    for name, value in plan["code_hashes"].items():
        if sha(ROOT / name) != value:
            return {**result, "state": "code_hash_mismatch", "detail": name}
    remaining = ready_count = failures = 0
    for unit in plan["units"]:
        dest = OUT / "units" / f'{unit["unit_id"]}.json'
        if dest.exists():
            record = json.loads(dest.read_text())
            if record.get("status") != "complete" or record.get("plan_sha256") != expected:
                return {**result, "state": "invalid_completed_record", "detail": unit["unit_id"]}
            continue
        remaining += 1
        if (OUT / "units" / f'{unit["unit_id"]}.FAILED.json').exists():
            failures += 1
            continue
        engineering = OUT / "engineering" / f'{unit["dataset"]}.json'
        if not engineering.exists():
            continue
        receipt = json.loads(engineering.read_text())
        if receipt.get("status") != "PASS" or receipt.get("plan_sha256") != expected or receipt.get("code_hashes") != plan["code_hashes"]:
            continue
        if unit["stage"] == "target":
            dependency = OUT / "units" / f'{unit["donor_unit"]}.json'
            if not dependency.exists():
                continue
            donor = json.loads(dependency.read_text())
            if donor.get("status") != "complete" or donor.get("plan_sha256") != expected:
                continue
            checkpoint = donor["checkpoints"][unit["arm"]]
            if not Path(checkpoint["path"]).exists() or sha(checkpoint["path"]) != checkpoint["sha256"]:
                return {**result, "state": "donor_checkpoint_missing_or_changed"}
        ready_count += 1
    return {**result, "remaining": remaining, "ready": ready_count, "failed": failures,
            "state": "complete" if not remaining else ("ready" if ready_count else
                     ("technical_failure" if failures else "engineering_or_donor_dependency")),
            "plan_sha256": expected}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("probe", "worker"))
    parser.add_argument("--dataset", choices=("dtu", "fau", "private_bdf"))
    parser.add_argument("--stage", choices=("all", "donor_pair", "target"), default="all")
    parser.add_argument("--max-units", type=int, default=1)
    parser.add_argument("--probe-steps", type=int, default=8)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("APwrong computation must run through Slurm")
    plan, plan_sha = open_plan()
    if args.command == "probe":
        if not args.dataset:
            parser.error("probe needs --dataset")
        result = probe(plan, plan_sha, args.dataset, args.probe_steps,
                       f'{args.dataset}_{os.environ["SLURM_JOB_ID"]}')
    else:
        result = worker(plan, plan_sha, args.stage, args.max_units, args.dataset)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
