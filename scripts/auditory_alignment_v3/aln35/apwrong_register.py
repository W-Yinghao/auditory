"""Freeze the bounded comparison after CPU contract tests and source audit."""
import copy
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from auditory_alignment_v3 import core, registry
from auditory_alignment_v3.prior33 import views as V, donor_train as D
from auditory_alignment_v3.aln35.ap_wrong import ROOT, OUT, PLAN, FORMAT, sha, digest, write
from auditory_alignment_v3.aln35.ap_wrong_sampler import PairSampler, RULE, REVISION, WRONG_RNG_TAG


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Slurm only")
    if PLAN.exists():
        raise FileExistsError("plan already frozen; no in-place rewrite")
    subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                    "tests/auditory_alignment_v3/aln35/test_ap_wrong.py"], check=True, cwd=ROOT)
    audit_path = OUT / "source_audit.json"
    audit = json.loads(audit_path.read_text())
    assert len(audit["lineages"]) == 3
    names = set()
    for group in ("prior33_donor", "prior33_target"):
        names.update(str(Path(d) / f) for d, f in registry.FAMILY_CODE[group] + core.V2_DEPS)
    names.update(["auditory_alignment_v3/aln35/ap_wrong.py", "auditory_alignment_v3/aln35/ap_wrong_sampler.py",
                  "private/auditory_alignment_v3/aln35/apwrong_register.py",
                  "private/auditory_alignment_v3/aln35/apwrong_audit.py",
                  "tests/auditory_alignment_v3/aln35/test_ap_wrong.py", "slurm/aln35_apwrong_gpu.sbatch",
                  "docs/auditory_alignment_v3/aln35/AP_WRONG_DESIGN.md"])
    code_hashes = {name: sha(ROOT / name) for name in sorted(names)}
    code_digest = digest(code_hashes)
    rows = [json.loads(line) for line in (ROOT / "private/auditory_alignment_v3/plan_ext.jsonl").read_text().splitlines()]
    original_targets = [row for row in rows if row["family_id"] == "ALN32_PUBLIC_AUDIO_PRIOR_TARGET"
                        and row["seed"] == 3401 and row["spec"]["objective"] == "NCE"
                        and row["spec"]["block"] == "core" and row["dataset"] in ("dtu", "fau", "private_bdf")]
    inputs, units, metachecks = {str(audit_path): sha(audit_path)}, [], []
    for lineage in audit["lineages"]:
        assert lineage["first_invalid"] is not None and not lineage["strict_stream_reuse_possible"]
        row = lineage["source_row"]
        target = row["dataset"]
        man = V.open_for_row(row)
        inputs[man.path] = sha(man.path)
        inputs[lineage["source_record"]] = lineage["source_record_sha256"]
        sam = PairSampler(man, target, 3401, "cpu", revised=True, metadata_only=True)
        steps = D.steps_at(30, man["budget"]["anchors_per_ep_eq"])
        # Full actual h30 metadata stream: prove legal derangement at every
        # step before any GPU model or outer result exists in this namespace.
        for _ in range(steps):
            sam.next_draw()
        meta = {"target": target, "steps": steps, "stream_sha256": sam.stream_hash(),
                "hash_log": sam.hash_log, "rejections": dict(sam.rejections), "all_steps_strictly_feasible": True}
        metachecks.append(meta)
        print(json.dumps({"metadata_stream_checked": target, "steps": steps, "rejections": dict(sam.rejections)}), flush=True)
        spec = {"format": FORMAT, "dataset": target, "seed": 3401, "code_digest": code_digest,
                "original_donor": row["experiment_id"], "original_record_sha256": lineage["source_record_sha256"],
                "manifest_sha256": man.sha256, "rule": RULE, "revision": REVISION,
                "horizon": 30, "updates": steps, "revised_stream_sha256": sam.stream_hash()}
        uid = "ALN35APW_" + digest(spec)[:16]
        units.append({"unit_id": uid, "stage": "donor_pair", "dataset": target, "spec": spec,
                      "source_row": row, "source_audit": {"path": str(audit_path), "sha256": inputs[str(audit_path)],
                          "historical_H": lineage["original_horizon"], "first_invalid": lineage["first_invalid"],
                          "old_AP_retained": True, "old_AP_not_used_as_equal_budget_comparator": True},
                      "updates_per_member": steps})
        targets = [row for row in original_targets if row["dataset"] == target and row["spec"]["variant"] == "AP"]
        assert len(targets) == (5 if target == "private_bdf" else 10)
        for template in targets:
            scratch = [row for row in original_targets if row["dataset"] == target and row["spec"]["variant"] == "S"
                       and row["subject_fold"] == template["subject_fold"] and row["content_fold"] == template["content_fold"]]
            assert len(scratch) == 1
            refs = {}
            for label, ref in (("scratch", scratch[0]), ("original_ap", template)):
                path = ROOT / "private/auditory_alignment_v3/units" / f'{ref["experiment_id"]}.json'
                record = json.loads(path.read_text())
                assert record["status"] == "complete"
                inputs[str(path)] = sha(path)
                refs[label] = {"experiment_id": ref["experiment_id"], "path": str(path), "sha256": inputs[str(path)],
                               "code_hash": record.get("code_hash"), "split_hash": ref["spec"]["split_hash"]}
            for arm in ("AP", "APwrong"):
                binding = {"donor_unit": uid, "arm": arm, "template": template["experiment_id"],
                           "template_sha256": digest(template), "code_digest": code_digest}
                tid = "ALN35APT_" + digest(binding)[:16]
                adapter = copy.deepcopy(template)
                adapter["experiment_id"] = tid
                adapter["spec"]["donor_group"] = uid
                adapter["logical_dependencies"] = [uid]
                adapter["registered"] = "ALN3.5 matched APwrong fixed h30 common-sampler control"
                units.append({"unit_id": tid, "stage": "target", "dataset": target, "arm": arm,
                              "donor_unit": uid, "binding": binding, "source_template": template,
                              "adapter_row": adapter, "scratch_reference": refs["scratch"],
                              "original_ap_reference": refs["original_ap"]})
    assert Counter(unit["stage"] for unit in units) == {"donor_pair": 3, "target": 50}
    metapath = OUT / "revised_stream_audit.json"
    write(metapath, {"job": os.environ["SLURM_JOB_ID"], "lineages": metachecks})
    inputs[str(metapath)] = sha(metapath)
    package = ROOT / "AUDITORY_ALN3_SERVER_PACKAGE_v3_5_20261018/docs/03_PRIOR_AND_CHECKPOINT_SELECTION.md"
    inputs[str(package)] = sha(package)
    plan = {"format": FORMAT, "created_utc": datetime.now(timezone.utc).isoformat(),
            "registration_job": os.environ["SLURM_JOB_ID"], "baseline": "5ef4a60bf77eeaeab5582c2cb076077c0b15bd11",
            "workpackage": "S35_AP_WRONG", "exploratory": True, "outer_wrong_results_seen": False,
            "code_hashes": code_hashes, "input_hashes": inputs, "units": units,
            "contract": {"architecture": "prior33/core", "objective": "NCE", "seed": 3401,
                         "donor_control": "AP/APwrong common revised source metadata sampler and fixed h30 only",
                         "source_dev": "unchanged true-paired calibrated NLL; 30 candidates; first minimum",
                         "wrong_rng": {"seed_sequence": [3401, WRONG_RNG_TAG], "independent_of_eeg_stream": True},
                         "public_target": "original mode T / unified risk", "private_target": "original native class endpoint",
                         "target_epochs": 200, "target_recipe": "unmodified prior33 target_train/fit_target",
                         "contrasts": ["AP-S", "APwrong-S", "AP-APwrong"],
                         "risk_direction": "R_reference-R_candidate", "auc_direction": "candidate-reference",
                         "inference": "within-person paired; independent metric families; actual paired identities; no seed x subject n",
                         "original_results": "keep all original S/AP/XP/J*/XM outputs and longer historical AP trajectory"}}
    write(PLAN, plan)
    PLAN.with_suffix(".sha256").write_text(sha(PLAN) + "\n")
    PLAN.chmod(0o444); PLAN.with_suffix(".sha256").chmod(0o444)
    write(OUT / "cpu_receipt.json", {"status": "PASS", "job": os.environ["SLURM_JOB_ID"],
                                   "plan_sha256": sha(PLAN), "units": 53, "donor_pairs": 3,
                                   "target_cells": 50, "metadata_steps": sum(x["steps"] for x in metachecks),
                                   "no_GPU_or_outer_wrong_results_used": True})
    print(json.dumps({"status": "PASS", "plan_sha256": sha(PLAN), "units": len(units)}), flush=True)


if __name__ == "__main__":
    main()
