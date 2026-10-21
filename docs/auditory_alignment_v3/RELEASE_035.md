# publish_035 — ALN3.6 and ALN4.1 round 1, both round-2 plans and the cross-stimulus decision

Researcher instruction 2026-10-21: "先push到github上". The publication scope is the established one: everything except the
private dataset itself, names and identity mappings; no weights, run logs or storage-cleanup tooling. This is a snapshot of
continuing experiments. Both R2 rounds are running.

## What is new since publish_034 (2026-10-20 evening)

### Packages

The two researcher packages are included as zips plus their byte-identical extracted copies:

- `AUDITORY_ALN3_SERVER_PACKAGE_v3_6_20261020`: three-round closure of ALN3, with FAU whole-group exclusion and nested
  readouts.
- `AUDITORY_ALN4_SERVER_PACKAGE_v4_1_20261021`: Stage2 temporal CS. It takes priority over ALN3.6 where the two compete.

### ALN3.6 R1 (seed 3401)

Conclusion: [aln36/R1_SCIENTIFIC_DECISION.md](aln36/R1_SCIENTIFIC_DECISION.md). Binding: [aln36/R1_BINDING.md](aln36/R1_BINDING.md).
Family tables: `results/auditory_alignment_v3/aln36/r1/r1_final/`.

- **Whole-group exclusion.** No HA EEG was used in training, standardisation, selection or readout. The fixed shared readout
  still improves current-envelope prediction over history for HA listeners: local +0.00173 [+0.00058, +0.00288] and CBpre
  +0.00233 [+0.00139, +0.00327] (MSE, simultaneous 95%).
  - TH: same direction, not resolved.
  - CI: no increment. The pooled models, whose training included CI listeners, are also near 0 for CI.
- **Personal time reweighting** (DT) is negative for every FAU group, both tools and DTU. In this setting it is refuted, not
  merely unresolved.
- **Personal history recalibration** is harmful under cross-content support.
- **Overall EEG scale calibration** helps for HA and DTU.
- **Children:**
  - G0 is unresolved.
  - The strict twin is unresolved.
  - AP − APwrong is about 0.
- **One child's event sequence** is almost the reverse of the group's. It makes the bootstrap-t interval of one private
  family uninformative. The child is kept, and the package's fixed-SE reference is reported. Whether the sequence reflects a
  different protocol will be checked in R3.
- **CPU closures:** episode interaction and history-description intervals, in
  `results/auditory_alignment_v3/aln36/{episode_interaction_v1,history_interval_v1}/`.

### ALN4.1 R1 (seed 3401)

Report: [aln41/ROUND1_REPORT.md](aln41/ROUND1_REPORT.md). Tables: `results/auditory_alignment_v3/aln41/r1/`.

- **Stage1 is CBraMod.** The MindMix EEG-only asset did not pass its gate.
- **Frozen content readout, ranking TNCE > TCS > B0:**
  - TCS − TNCE: DTU −0.034, FAU −0.012 (both resolved).
  - TCS − B0: FAU +0.018; DTU not resolved.
  - TCS − GCS: FAU +0.034.
  - TCS vs TCS_WRONG: TCS is higher, but most of that gap is damage done by the wrong pairing.
- **Did not work as designed:**
  - The learned group time gate stayed uniform in every arm.
  - The TNCE query loss stayed at chance throughout training.
- **Children:**
  - History-conditional and current-sound contrasts are unresolved.
  - Full fine-tuning AUC is 0.535–0.538 in every arm.
  - Frozen age MAE is about 25 months, against 32 for the raw-EEG ridge and the training mean. Stage2 adds no gain here.
  - F_ASSOC has no resolved coefficient.

### R2 (running; plans frozen before any R2 result)

- **ALN4.1 R2** ([aln41/R2_PLAN.md](aln41/R2_PLAN.md)):
  - Seeds 3407/3413: 8 source fits, 30 private CE fits and 40 frozen units. The R1 modules are byte-identical and re-pointed
    per seed (`auditory_alignment_v3/aln41/r2.py`). The learning rate is not re-selected.
  - F_SUPPORT: U0/U10/U30, personal δ against affine calibration. The plan and its 20-member family are frozen; runs on CPU.
  - Analysis code: `aln41/analysis_r2.py`.
- **Cross-stimulus question** ([aln41/R2_CROSS_STIM_DECISION.md](aln41/R2_CROSS_STIM_DECISION.md)):
  - The route was chosen from asset semantics alone. MFF pure-tone and bapa share the deviant/standard relation, not sound
    identity.
  - Design: transfer pure-tone → bapa, then refit on bapa. 24 gated bapa children; fixed 13-member family.
  - 7 frozen extractions are running. The readout has not been run.
  - The plan binds the decision record's sha256. It is not published because it lists MFF record ids and identity keys.
- **ALN3.6 R2** ([aln36/R2_BINDING.md](aln36/R2_BINDING.md)), seed 3407:
  - 12 FAU whole-group fits, now complete.
  - 52 feature banks. The 40 pooled banks reuse existing seed-3407 weights, matched one-to-one by spec.
  - Child AP/APwrong: 1 donor pair and 10 target fits (`aln36/r2_apwrong.py`, R1 runner unchanged).

### Operations

- **Faulty GPU on node51.** On 2026-10-21 one L40S GPU on node51 returned "uncorrectable ECC error" on every job it received.
  - Eleven failures were released with receipts, in `scripts/auditory_alignment_v3/aln35/fleet_v3_20261020/`
    (`resolve_ecc_20261021*.json`, `resolve_ecc_items_*.json`). Each release checked that no result or newer state had been
    written.
  - node51 was added to `--exclude` in the active sbatch files.
  - The R2 AP/APwrong plan had to be re-registered before any unit result, because its sbatch is hash-bound. The first plan is
    kept on the server.
- **New fleet readiness shims:** `auditory_alignment_v3/aln35/{aln36_fleet,aln41_fleet*,aln41_r2_fleet,aln41_xs_fleet,aln36_r2_fleet}.py`.

## Lane records

`results/auditory_alignment_v3/unit_records/lanes_035_*.tar.gz`, with `LANES_MANIFEST_035.tsv`, holds every ALN3.4/3.5 lane
record not already published byte-identically in publish_030–034, plus the ALN3.6 and ALN4.1 lane records (prefixes `aln36/`
and `aln41/`). That covers R1 complete and R2 completed so far.

Not included:

- the cross-stimulus lane (its readout would key children by identity group);
- the age results file (true ages).

Records, releases and seeds do not increase independent participant n.

## Still running at this snapshot

- **ALN3.4 tails:** DTU budget 1 unit remaining; breadth curves 18 remaining. DTU curves (440/440) and breadth budget (75/75)
  are complete.
- **ALN4.1 R2 and ALN3.6 R2:** both in progress, as above.

## Not published

- private raw data;
- file, event and clinical source tables;
- identity mappings and names/contact details;
- MFF record and identity lists, including the cross-stimulus plan and asset audit tables;
- server-only support geometry bindings;
- model weights and run logs;
- storage-cleanup tools/lists;
- agent handoff notes and their audit scripts.

Source and publication hashes: `results/auditory_alignment_v3/publication_035/MANIFEST.tsv`.
