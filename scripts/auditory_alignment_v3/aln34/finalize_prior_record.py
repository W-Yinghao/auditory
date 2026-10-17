"""Finalize M13 only from a complete, matching M12 receipt. Slurm CPU job.

Does not modify live registry, append plan rows, submit GPU workers or claim that
production training has happened. The record checker runs before atomic freeze.
"""
from datetime import datetime
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from auditory_alignment_v3 import core


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Final provenance verification requires Slurm")
    os.umask(0o077)
    root, base = Path(core.REPO), Path(core.OUT) / "aln34"
    audit_path = base / "prior33_freeze_audit.json"
    audit = json.loads(audit_path.read_text())
    probe = json.loads(args.receipt.read_text())
    assert probe["status"] == "pass", "all M12 phases must actually pass"
    assert set(probe["phases"]) == {"integrity", "tiny", "short"}
    assert all(v["status"] == "pass" for v in probe["phases"].values())
    assert probe["code_hashes"] == audit["group_hashes"]
    assert probe["script_sha256"] == sha(root / "private/auditory_alignment_v3/probe_prior33.py")
    for f, digest in audit["code"].items():
        assert sha(root / f) == digest, f"source changed since freeze audit: {f}"
    for f, digest in audit["manifests"].items():
        assert sha(f) == digest, f"manifest changed since freeze audit: {f}"
    full = str(base / "prior33/manifest.json")
    rich = str(base / "prior33/manifest_rich.json")
    assert probe["manifest_sha256"] == audit["manifests"][full]
    assert probe["manifest_rich_sha256"] == audit["manifests"][rich]
    for test in audit["tests"].values():
        assert sha(root / test["file"]) == test["sha256"]
    path = Path(core.OUT) / "make_plan_ext_prior33.py"
    spec = importlib.util.spec_from_file_location("prior_m13_plan", path)
    P = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(P)
    man, _, _ = P.open_manifest(full, probe["manifest_sha256"])
    rows = P.build_primary(P.manifest_context(man, man.sha256), "M13 verification; not registered")
    assert len(rows) == audit["production_rows"] == 1154
    lines = ["# E34_PUBLIC_PRIOR execution record — M13", "",
             f"Frozen {datetime.now().astimezone().isoformat()} by Slurm CPU job {os.environ['SLURM_JOB_ID']}. "
             f"Real M12 GPU job {probe['job']} passed all three phases on {probe['device']}. "
             "This record precedes production registration. Its 1,154 planned rows are not described as completed training.", "",
             "Authority: ALN3.4 and the researcher's instructions to execute the package, complete the handoff and design/submit "
             "the next experiments. The standalone ALN3.3 zip never arrived; the byte-preserved ALN3.4 inherited contract "
             "and PUBLIC_PRIOR_DESIGN.md define aln33_env64_125ms_v1. No model-performance or wording gate applies.", "",
             "## Completed prerequisites and scope", "",
             "FIXC fixes the full/private manifest fallback, binds the rich supplement, verifies consumed bytes lazily, "
             "guards C2 reference eligibility, corrects the sub-051 reason, separates truncated probes from production and "
             "records resume code lineage. The generated target trainer retains the inherited computation; changed wrappers "
             "and seed descriptions are hashed below. Existing running ALN3 training files remain byte-identical.", "",
             "CPU cache job 1043917 completed core → rich PCA refit → rich supplement → CPU probe selection → plan dry-run "
             "and compute-node sbatch --test-only. Core has N_SK=84,132; 673,056 anchors per epoch-equivalent; "
             "2,629.125 steps per epoch-equivalent (ceil 2,630); initial 30-ep-eq S0=78,874. "
             "The eligible rich refit uses 1,899,000 unique windows. Pass-1 recomputed zero streams; original rich files are "
             "retained in rich_before_fixc_20261017. PCA SHA: 39ae5ee387c56ba624871db49d535c7af78edd1a5a8d158b788e9aa7d6bbfa07.", "",
             "The 1,154 rows comprise core 540, zero-shot access 210, seed panel 120, rich 126 and CSX 158. "
             "Rich is a separate comparison, not a full cross-product of the core matrix. Compatible results are reused. "
             "Private data are loaded in memory inside target units; no private EEG cache is added.", "",
             "## Decisions, limitations and deviations recorded before production results", "",
             "1. Donor extension uses the first minimum without tolerance, excludes XM from its trigger and applies the "
             "same rule to all eligible contract members. Continuations retain previous results, source checkpoints and code hashes.",
             "2. PCA and sigma use the same core-manifest unique donor-fit windows, excluding whole presentations barred "
             "by any target's donor set. Historical C7 outputs are preserved and are not the production basis.",
             "3. SparrKULee sub-051 audiobook_12_2 remains a declared exclusion despite C2 classing it unverifiable. "
             "This departs from the general retention rule. The scout off-peak set contains the -8.84 s peak, so equality "
             "to its maximum was not prominence evidence. C2 diagnostics and the original decision provenance remain in the manifest.",
             "4. Of 616 C2-audited runs, 148 are aligned, one misaligned and 467 unverifiable; another 50 entries were not audited. "
             "Unverifiable runs are generally retained under the declared rule. This is partial clock verification, not proof "
             "that every donor stream is correctly aligned. Restricted participants never enter reference or training reads.",
             "5. Private test stimuli were not scanned against donors: non-overlap remains unverified. Historical individual "
             "overlap in generic foundation-model pretraining is also uncertified. These limitations do not become claims of independence.",
             "6. The FAU:123 MAP_UNPLAYED_BY_CODE exclusion removes 2,025 of 16,848 FAU core-pool rows in each affected "
             "DTU/Federici donor set; the possibly inaudible stereo-channel caveat is retained.",
             "7. FAU raw-uV mode C clips beyond +/-65,000 uV: two samples, participant 221. The aborted pre-clip output is "
             "preserved; A/B z-score caches are unchanged. Federici mode C is partial and cannot restore absent frequencies.",
             "8. B_uni_cal uses bridge_cal as a labelled sensitivity. Primary bridges use donor fit. Rich and CSX bridges "
             "reuse the core fit/calibration rows, without silently adding fau_cs. Zero-shot mode C uses donor statistics.",
             "9. Every consumed cache file is verified by SHA256 and byte size, memoized only while its stat and expected "
             "digest are unchanged. Donor opening does not load target caches. M12's integrity and bank-load timing include "
             "different work and are not pure hashing-overhead benchmarks.",
             "10. Production wrappers refuse truncated donor chains and epoch overrides. Probe records remain parseable "
             "but excluded from production analysis. Resume records retain original/current code hashes and mismatches.",
             "11. Analysis resamples identities, with group_seed(family, endpoint), separate NLL/AUC max-t families and "
             "actual paired coverage. Intervals condition on available fitted models; seeds and folds do not increase n.",
             "12. Seed labels follow executed code: the manifest replaces the inherited target-statistics +5 fit; public "
             "early-stopping segment draws use 12345 and anchor draws use batch index, private early stopping uses batch "
             "index, +99 initializes objective calibration in both target paths, +98/+1000 are public-only, and +77 is the "
             "private CS kernel-reference path. Complete record fields describe applicable paths; unused labels are not executed randomness.",
             "13. Original build_rich.py remains byte-identical for reusable pass-1 markers. Its three-versus-four no-source "
             "reason count and old Slurm docstring are documentation defects; actual availability is in the rich manifest. "
             "select.py's duplicate names_limit helper remains; operational dependency checks are separate.",
             "14. M12 includes one-ep-eq DTU and private NCE donor groups for correct leave-target-out provenance. Its rich "
             "short run uses the initial H=30 schedule with the actual short core AP checkpoint solely as an engineering "
             "override; it does not establish a production horizon. Rich clock checks read the frozen C7 evidence for "
             "three streams per available cohort; C2 and the first SparrKULee participant are actually recomputed.", "",
             "## Engineering evidence and actual resources", "",
             "The broad FIXC suite 1043898 passed 418 cases and failed one obsolete private input-mode assertion. "
             "After correcting it and applicable seed descriptions, affected job 1043916 passed all 42 checks. "
             "Earlier 1043888 (181 passed, five failures) and 1043896 (three refit tests passed, one infrastructure "
             "admission-order whitespace assertion failed) are retained below with their corrections; they are not represented as clean runs. "
             "Registry staging check 1043934 preserved all 21 legacy groups across 7,398 records and 25 families. "
             "No unrecorded-family bypass was used.", "",
             "| M12 phase | Wall seconds | GPU peak GiB | Status |", "|---|---:|---:|---|"]
    for name, phase in probe["phases"].items():
        lines.append(f"| {name} | {phase['seconds']:.2f} | {phase['gpu_peak_bytes']/2**30:.3f} | {phase['status']} |")
    lines += ["", "Detailed timings, selection checks, paired target budgets, sample windows, exact-resume checks, "
              "member curves and all short-run checkpoint provenance are in the complete receipt linked below. "
              "The probe is truncated engineering evidence. Production resource projections inherit the measured device/recipe "
              "limitations and are not a promised completion date. Pool weights are conservative admission estimates; "
              "the existing memory-aware pool and 10-GPU cap remain authoritative.", "",
              f"M12 receipt: `{args.receipt.relative_to(root)}` SHA256 `{sha(args.receipt)}`. "
              f"Freeze audit: `{audit_path.relative_to(root)}` SHA256 `{sha(audit_path)}`. "
              f"Finalizer source SHA256: `{sha(__file__)}`.", "",
              "## Results known before registration", "",
              "Already viewed: D multi-seed, the paired-order attention correction, D_ADAPT true risk, private E multi-seed, "
              "record-level complement findings, and TF refresh 1043925 (232/400 panel units; DTU 44 people fully paired "
              "across three seeds). The result-informed 150-unit DTU doubled-budget plan was registered independently. "
              "Private calibration stage-1 diagnosis 1043948 was also viewed: positive-affine NLL worsens REVE's three CS "
              "panel configurations; its 120-checkpoint leave-self-out evaluation is separately registered. Complement GPU "
              "evaluation is running. No production public-prior result has yet been generated under this record.", "",
              "## Deployment and execution identity", "",
              "Next, deploy checked registry, dispatch and offload; stop the old offload daemon gracefully and wait for "
              "exit before resubmitting. Append the locked plan only after these checks; then install queue/watcher changes "
              "and start the prior keeper (at most four prior workers, within ten running project GPUs). Existing obsolete "
              "execution holds stay intact. Use squeue/scancel/sbatch only; scontrol is prohibited. Every actual operation "
              "and job belongs in logs/operations.log and the mutable completion ledger, not retroactively in this frozen record.", "",
              "## Frozen manifests", "", "| File | SHA256 |", "|---|---|"]
    lines += [f"| {p} | `{h}` |" for p, h in audit["manifests"].items()]
    lines += ["", "## Frozen training code groups", "", "| Family | Code hash |", "|---|---|"]
    lines += [f"| {p} | `{h}` |" for p, h in audit["group_hashes"].items()]
    lines += ["", "## Frozen file hashes", "", "| File | SHA256 |", "|---|---|"]
    lines += [f"| {p} | `{h}` |" for p, h in audit["code"].items()]
    lines += ["", "## Retained test receipts", "", "| Job | Summary | Log SHA256 |", "|---|---|---|"]
    lines += [f"| {j} | {'; '.join(t['summary'])} | `{t['sha256']}` |" for j, t in audit["tests"].items()]
    dest = base / "E34_PUBLIC_PRIOR_EXECUTION_RECORD.md"
    if dest.exists():
        raise FileExistsError("M13 already frozen; do not rewrite its execution identity")
    tmp = dest.with_suffix(".candidate.md")
    tmp.write_text("\n".join(lines) + "\n")
    digest, problems = P.record_status(str(tmp), rows)
    if problems:
        raise RuntimeError(f"M13 validation failed: {problems}")
    tmp.chmod(0o444)
    os.replace(tmp, dest)
    print(f"M13 frozen: {dest}; SHA256 {digest}; all {len(rows)} rows pass record checks", flush=True)


if __name__ == "__main__":
    main()
