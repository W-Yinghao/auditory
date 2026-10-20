"""Four saved CB auditory states: donor-dev-only selection sensitivity.

This never trains a donor or chooses a target state with outer outcomes.  The
frozen source curve currently selects update10000, so targets are exact aliases
of the already registered fixed10000 DTU3401 panel, not new fitting requests.
"""
from __future__ import annotations
import argparse
import fcntl
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from .. import core, fm_aligned
from ..prior33 import views as V, model as M, losses as L, donor_train as D
from ..aln34 import cb_auditory as CB, learning_budget as B

BASE = Path(core.OUT) / "aln35/cb_audio_state_v1"
PLAN = BASE / "plan.json"
RESULT = Path(core.REPO) / "results/auditory_alignment_v3/aln35/cb_audio_state/diagnostics.json"
NOTE = Path(core.REPO) / "docs/auditory_alignment_v3/aln35/CB_AUDIO_STATE_DESIGN.md"
STATES = (0, 2500, 5000, 10000)
SELECT_SCOPE = "donor-dev NCE sensitivity only; not whole-pipeline or target-inner selection"


def choose_state(curves):
    by_step = {int(row["step"]): row for row in curves}
    if len(by_step) != len(curves) or set(by_step) != set(STATES):
        raise ValueError("need all four distinct original candidate states; no post hoc subset")
    for row in curves:
        if not math.isfinite(float(row["paired_dev_nce_nats"])):
            raise ValueError("nonfinite source development risk")
    streams = {row["stream_sha256"] for row in curves}
    if len(streams) != 1 or any(row["batches"] != 32 for row in curves):
        raise ValueError("candidate source-dev query streams differ")
    return min(STATES, key=lambda step: (float(by_step[step]["paired_dev_nce_nats"]), step))


def effective_rank_gram(features):
    """Singular-value entropy rank from the smaller centered Gram matrix."""
    x = features.double() - features.double().mean(0)
    gram = x @ x.T
    eigenvalues = torch.linalg.eigvalsh(gram).clamp_min(0)
    tolerance = torch.finfo(torch.float64).eps * max(x.shape) * max(float(eigenvalues.max()), 1.0)
    singular = torch.sqrt(eigenvalues[eigenvalues > tolerance])
    if singular.numel() == 0:
        return 0.0
    p = singular / singular.sum()
    return float(torch.exp(-(p * p.log()).sum()))


def source_hashes():
    paths = {Path(__file__), NOTE, Path(D.__file__)}
    paths.update(Path(core.REPO) / name for name in CB.sources())
    paths.update((Path(core.REPO) / "tests/auditory_alignment_v3/aln35/test_cb_audio_state.py",
                  Path(core.REPO) / "slurm/aln35_cb_state_gpu.sbatch",
                  Path(core.REPO) / "slurm/aln35_cb_state_cpu.sbatch"))
    return {str(path.relative_to(core.REPO)): B.sha(path) for path in sorted(paths)}


def make_plan():
    if PLAN.exists():
        raise FileExistsError("state selection plan already frozen")
    old = CB.read(CB.PLAN)
    CB.verify(old)
    donor = [u for u in old["rows"] if CB.is_donor(u) and u["seed"] == 3401 and u["arm"] == "generic_paired"]
    assert len(donor) == 1
    donor = donor[0]
    path = CB.BASE / "units" / f'{donor["id"]}.json'
    record = CB.read(path)
    assert record["status"] == "complete" and not record["probe"] and record["plan_sha256"] == B.sha(CB.PLAN)
    selected = choose_state(record["curves"])
    snapshots = []
    for step in STATES:
        checkpoint = Path(record["final_checkpoint"]).parent / f"update{step}.pt"
        if not checkpoint.exists():
            raise FileNotFoundError(f"required candidate is missing: {step}")
        snapshots.append({"step": step, "path": str(checkpoint), "sha256": B.sha(checkpoint),
                          "size_bytes": checkpoint.stat().st_size})
    # This data-derived finite rule currently aliases the existing fixed10000
    # target policy.  Refuse to silently implement a different target workflow.
    if selected != 10000:
        raise RuntimeError("selected source state is not the fixed10000 alias; register its bounded target completion separately")
    targets = [row for row in old["rows"] if not CB.is_donor(row) and row["dataset"] == "dtu"
               and row["seed"] == 3401 and row["spec"]["intermediate_arm"] == "generic_paired"]
    assert len(targets) == 10
    aliases = []
    for row in targets:
        wrong = [r for r in old["rows"] if not CB.is_donor(r) and r["dataset"] == "dtu" and r["seed"] == 3401
                 and r["subject_fold"] == row["subject_fold"] and r["content_fold"] == row["content_fold"]
                 and r["spec"]["intermediate_arm"] == "generic_wrong"]
        assert len(wrong) == 1
        aliases.append({"selected_equals_fixed10000": row, "direct_id": row["spec"]["baseline_id"],
                        "wrong_id": wrong[0]["experiment_id"], "requires_new_training": False})
    plan = {"version": "ALN35_CB_AUDIO_STATE_v1", "created_utc": datetime.now(timezone.utc).isoformat(),
            "job": os.environ["SLURM_JOB_ID"], "baseline": "5ef4a60bf77eeaeab5582c2cb076077c0b15bd11",
            "source_plan": {"path": str(CB.PLAN), "sha256": B.sha(CB.PLAN)},
            "source_record": {"path": str(path), "sha256": B.sha(path)}, "donor": donor,
            "manifest_sha256": CB.MANIFEST_SHA, "pool": old["pool"], "code_hashes": source_hashes(),
            "candidates": snapshots, "original_curves": record["curves"], "selected_step": selected,
            "selection": {"scope": SELECT_SCOPE, "rule": "minimum original paired donor-dev NCE nats; earlier exact tie",
                          "uses_outer_outcomes": False, "uses_target_inner_outcomes": False,
                          "primary_fixed10000_unchanged": True,
                          "exploratory_after_historical_results": True},
            "diagnostics": {"same_32_source_dev_batches_as_original": True, "rank_batches": 4,
                            "rank_anchors": 256, "rank": "centered singular-value entropy, flattened backbone tokens and readout",
                            "head_transfers_to_target": False, "new_donor_training": False},
            "target_aliases": aliases, "new_target_executions": 0}
    B.write(PLAN, plan)
    PLAN.with_suffix(".sha256").write_text(B.sha(PLAN) + "\n")
    PLAN.chmod(0o444); PLAN.with_suffix(".sha256").chmod(0o444)
    B.write(BASE / "cpu_receipt.json", {"status": "PASS", "plan_sha256": B.sha(PLAN), "selected_step": selected,
                                      "job": os.environ["SLURM_JOB_ID"], "new_target_executions": 0,
                                      "new_donor_executions": 0, "target_aliases": 10})
    print(json.dumps({"status": "PASS", "selected_step": selected, "new_target_executions": 0,
                      "plan_sha256": B.sha(PLAN)}), flush=True)


def verify(plan):
    if B.sha(PLAN) != PLAN.with_suffix(".sha256").read_text().strip() or plan["code_hashes"] != source_hashes():
        raise ValueError("CB state plan/code drift")
    for item in (plan["source_plan"], plan["source_record"], *plan["candidates"]):
        if B.sha(item["path"]) != item["sha256"]:
            raise ValueError(f"CB state immutable source changed: {item['path']}")
    if choose_state(plan["original_curves"]) != plan["selected_step"]:
        raise ValueError("source selection rule drift")


@torch.no_grad()
def diagnose(plan, probe=False):
    from auditory_alignment_v2.foundation_adapter import Backbone
    device = torch.device("cuda")
    D.determinism(device)
    torch.manual_seed(3401)
    manifest = V.open_manifest(CB.MANIFEST, CB.MANIFEST_SHA)
    model = fm_aligned.AlignedFM(Backbone("cbramod", "dtu", "pretrained_full", 64), 32).to(device)
    model.requires_grad_(False).eval()
    head = M.fixed_heads(manifest, manifest.root)["env"].to(device).requires_grad_(False)
    initial = torch.load(plan["candidates"][0]["path"], map_location="cpu", weights_only=False)
    parameter_names = [name for name, _ in model.bb.net.named_parameters()]
    outputs = []
    for candidate in plan["candidates"][:1] if probe else plan["candidates"]:
        state = torch.load(candidate["path"], map_location="cpu", weights_only=False)
        if state["step"] != candidate["step"] or state["unit"] != plan["donor"] or state["probe"]:
            raise ValueError("snapshot identity/probe mismatch")
        if state["plan_sha256"] != plan["source_plan"]["sha256"]:
            raise ValueError("snapshot belongs to another source plan")
        model.bb.net.load_state_dict(state["backbone"], strict=True)
        model.readout.load_state_dict(state["head"], strict=True)
        stream = CB.Stream(manifest, plan["pool"]["dev"], 3401 + 59000, "dev", device)
        loss_values, tokens, readouts = [], [], []
        for index in range(2 if probe else 32):
            x, y, keys, _, _ = stream.draw()
            h = model.bb(x)
            if h.shape[2] != 1:
                raise ValueError("expected a single query-aligned backbone patch")
            z = model.readout(h[:, :, 0])
            loss, _ = L.nce_single_view(z, head(y), keys, unknown_clock=L.unknown_clock_families(manifest))
            if not torch.isfinite(loss) or not torch.isfinite(z).all() or not torch.isfinite(h).all():
                raise FloatingPointError("nonfinite source-state diagnostic")
            loss_values.append(float(loss))
            if index < 4:
                tokens.append(h.flatten(1)); readouts.append(z)
        old = next(row for row in plan["original_curves"] if row["step"] == candidate["step"])
        if not probe and stream.chain != old["stream_sha256"]:
            raise ValueError("source-dev input stream changed")
        numerator = denominator = 0.0
        for name in parameter_names:
            now, before = state["backbone"][name].double(), initial["backbone"][name].double()
            numerator += float((now - before).square().sum())
            denominator += float(before.square().sum())
        outputs.append({"step": candidate["step"], "checkpoint_sha256": candidate["sha256"],
                        "original_fit_interval_nce_nats": old["fit_loss_mean"],
                        "original_source_dev_nce_nats": old["paired_dev_nce_nats"],
                        "replayed_source_dev_nce_nats": float(np.mean(loss_values)),
                        "replay_minus_original_nats": float(np.mean(loss_values)) - old["paired_dev_nce_nats"],
                        "source_dev_stream_sha256": stream.chain, "source_dev_batches": len(loss_values),
                        "relative_backbone_change_from_0": math.sqrt(numerator / denominator),
                        "rank_anchors": sum(len(t) for t in tokens),
                        "backbone_flattened_effective_rank": effective_rank_gram(torch.cat(tokens)),
                        "readout_effective_rank": effective_rank_gram(torch.cat(readouts))})
        del stream, tokens, readouts, state
    receipt = {"status": "PASS", "probe": probe, "plan_sha256": B.sha(PLAN), "code_hashes": plan["code_hashes"],
               "job": os.environ["SLURM_JOB_ID"], "device": torch.cuda.get_device_name(),
               "selection_scope": SELECT_SCOPE, "selected_step": plan["selected_step"], "states": outputs,
               "new_training": False, "target_policy_equals_existing_fixed10000": True,
               "replay_risks_are_diagnostics_not_reselection": True}
    if probe:
        B.write(BASE / "probes" / os.environ["SLURM_JOB_ID"] / "receipt.json", receipt)
        B.write(BASE / "engineering.json", receipt)
    else:
        B.write(RESULT, receipt); B.write(BASE / "complete.json", receipt)
        report(plan, receipt)
    print(json.dumps({"status": "PASS", "probe": probe, "selected_step": plan["selected_step"], "states": len(outputs)}), flush=True)


def report(plan=None, diagnostics=None):
    plan = plan or CB.read(PLAN)
    diagnostics = diagnostics or (CB.read(RESULT) if RESULT.exists() else None)
    done, missing = [], []
    for alias in plan["target_aliases"]:
        uid = alias["selected_equals_fixed10000"]["experiment_id"]
        path = CB.BASE / "units" / f"{uid}.json"
        if not path.exists():
            missing.append(uid); continue
        result = CB.read(path)
        if result.get("status") != "complete" or result.get("probe"):
            raise ValueError("invalid fixed10000 target alias")
        source = result["auditory_intermediate"]
        selected = next(item for item in plan["candidates"] if item["step"] == plan["selected_step"])
        if (result["plan_sha256"] != plan["source_plan"]["sha256"]
                or result["row"] != alias["selected_equals_fixed10000"]
                or source["donor_id"] != plan["donor"]["id"]
                or source["checkpoint_sha256"] != selected["sha256"]
                or source["updates"] != 10000 or source["head_transfer"]):
            raise ValueError("fixed10000 target alias provenance mismatch")
        done.append({"id": uid, "path": str(path), "sha256": B.sha(path),
                     "same_as_selected_policy": True, "new_fitting": False})
    B.write(BASE / "target_reuse.json", {"plan_sha256": B.sha(PLAN), "complete": done, "pending_original_lane": missing})
    lines = ["# ALN3.5 CB auditory state sensitivity", "", f"Selection scope: **{SELECT_SCOPE}**.", "",
             "The minimum of the four original source-dev NCE values selects update10000. This sensitivity therefore equals the original fixed10000 policy exactly; it is not an additional independent result or a new target fit.", "",
             f"Existing DTU seed3401 generic_paired target coverage: {len(done)}/10 cells; unfinished cells remain in the original registered lane.", "",
             "| Update | Original fit NCE | Original dev NCE | Flattened backbone rank | Readout rank | Relative backbone change |",
             "|---:|---:|---:|---:|---:|---:|"]
    for old in plan["original_curves"]:
        diag = next((row for row in (diagnostics or {}).get("states", []) if row["step"] == old["step"]), {})
        values = [old["step"], old["fit_loss_mean"], old["paired_dev_nce_nats"],
                  diag.get("backbone_flattened_effective_rank"), diag.get("readout_effective_rank"),
                  diag.get("relative_backbone_change_from_0")]
        cells = [("not applicable" if i == 1 else "pending") if value is None else f"{value:.6g}"
                 for i, value in enumerate(values)]
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "Rank uses the same first four fixed source-dev batches (256 anchors), centered singular-value entropy, without target data. Original training-interval losses and donor-head dev losses do not establish target transferability. A large parameter change alone does not establish catastrophic forgetting.", "",
              "The historical fixed10000, direct CB and generic_wrong target comparisons remain in CB_AUDITORY_CONTINUATION_RESULTS.md with their own paired coverage. A whole target adaptation/readout inner-person selector is not implemented or claimed by this finite source-dev sensitivity."]
    path = Path(core.REPO) / "docs/auditory_alignment_v3/aln35/CB_AUDIO_STATE_RESULTS.md"
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text("\n".join(lines) + "\n")


def fleet_status():
    out = {"name": "c3_s35cbstate", "lane": "s35_cb_state", "state": "not_registered", "ready": 0,
           "remaining": 1, "slots": 1, "initial": [], "submit": ["slurm/aln35_cb_state_gpu.sbatch", "diagnose"]}
    if not PLAN.exists():
        return out
    plan = CB.read(PLAN)
    if B.sha(PLAN) != PLAN.with_suffix(".sha256").read_text().strip() or plan["code_hashes"] != source_hashes():
        return {**out, "state": "source_or_plan_drift"}
    if any(B.sha(item["path"]) != item["sha256"] for item in (plan["source_plan"], plan["source_record"])):
        return {**out, "state": "original_source_drift"}
    if (BASE / "complete.json").exists():
        result = CB.read(BASE / "complete.json")
        if result["status"] == "PASS" and result["plan_sha256"] == B.sha(PLAN):
            return {**out, "remaining": 0, "state": "complete"}
    if not (BASE / "engineering.json").exists():
        return {**out, "state": "engineering_pending"}
    receipt = CB.read(BASE / "engineering.json")
    if (receipt["status"] != "PASS" or receipt["plan_sha256"] != B.sha(PLAN)
            or receipt["code_hashes"] != plan["code_hashes"]):
        return {**out, "state": "engineering_invalid"}
    if any(not Path(item["path"]).exists() or Path(item["path"]).stat().st_size != item["size_bytes"]
           for item in plan["candidates"]):
        return {**out, "state": "snapshot_missing"}
    if (BASE / "failed.json").exists():
        return {**out, "state": "failed_needs_review"}
    return {**out, "state": "ready", "ready": 1}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("register", "probe", "diagnose", "report"))
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Slurm only")
    if args.command == "register":
        make_plan(); report(); return
    plan = CB.read(PLAN); verify(plan)
    if args.command == "report":
        report(plan)
    else:
        with open(BASE / "execution.lock", "a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print("Another CB state probe/diagnostic owns the lock", flush=True)
                return
            if args.command == "diagnose":
                if (BASE / "complete.json").exists():
                    result = CB.read(BASE / "complete.json")
                    assert result["status"] == "PASS" and result["plan_sha256"] == B.sha(PLAN)
                    print("Saved-state diagnostics already complete", flush=True)
                    return
                receipt = CB.read(BASE / "engineering.json")
                assert receipt["status"] == "PASS" and receipt["plan_sha256"] == B.sha(PLAN)
            try:
                diagnose(plan, probe=args.command == "probe")
            except Exception as exc:
                failed = (BASE / "failed.json" if args.command == "diagnose"
                          else BASE / "probes" / os.environ["SLURM_JOB_ID"] / "failed.json")
                B.write(failed, {"status": "failed", "job": os.environ["SLURM_JOB_ID"],
                                 "plan_sha256": B.sha(PLAN), "error": repr(exc)})
                raise


if __name__ == "__main__":
    main()
