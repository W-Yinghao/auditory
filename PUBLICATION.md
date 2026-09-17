# GitHub snapshot: scope and reproducibility

## v2.1 update

The researcher explicitly requested this curated update after completion of the conditional v2.1 plan. Start with [the scientific results](docs/auditory_v21/SCIENTIFIC_RESULTS_v2_1.md), [route decisions](docs/auditory_v21/ROUTE_DECISIONS_v2_1.md), and [final acceptance report](reports/auditory_v21/final_001/FINAL_REPORT_CN.md). N1/N3 passed their frozen capability gates across 880 independent synthetic worlds and completed 130 real EEG heads without establishing a controlled increment. N2 has matched-bag common support, but the frozen role split fails support in four of five folds; its dependent capability/real branch was conditionally stopped. This is not a negative distribution-information finding.

The amendment, code, tests, executed configurations, selected numerical outputs, reports and final figures are exact copies. Newly copied documentation adds publication notices and annotations for unavailable server links. README and this guidance are editorial navigation. Earlier test/preflight failures and superseded closure audits are retained; use tests_009, input_preflight_003, closure_003 and final_001 for final status. The v2.1 final_001 is distinct from the superseded v2 final_001. Historical statements that a plan was unexecuted or publication was not automatic describe their original time.

N2 denominator note: the design audit starts with 57 original candidates. The later input receipt counts only the 54 candidates represented by at least one matched half: 49 have both halves, five have only one, and three of the original 57 have none. Thus 49/57 is the full-cohort common-support fraction; `candidate_denominator: 54` in n2_inputs is conditional on any matched-bag support, not a replacement cohort denominator. The release verifier reconciles these counts against the saved bag metadata; original files are preserved.

The broader release scan also found two hardcoded pseudonymous record IDs in the previously published `slurm/13_phase1_smoke.sbatch`. Its current publication copy now requires record IDs as runtime arguments. The server's executed script remains unchanged; the manifest retains its source and previous-release hashes. This correction changes the current tree, not existing Git history, where the old script remains accessible. Earlier privacy receipts describe their narrower scans and are not retroactively upgraded.

[The v2.1 change record](release/auditory_v21_publication_changes.json), [manifest](release/manifest.json) and [current verification](release/verification.json) record the selected scope, hashes and checks. [Previous v2 verification](release/verification_auditory_next_v2.json) remains historical. Publication packaging, privacy scans and static verification run through Slurm, separately from the frozen scientific allocation upper bound of 32 CPU core-hours and 0 GPU-hours. No models are refit for this publication; the verifier checks the 59-test scientific receipt and matching source hashes rather than claiming a new test run.

Private source snapshots, exact identity/event/bag manifests and splits, individual predictions, clinical rows, model artifacts and detailed logs remain on the server. Hash references to these objects do not make them downloadable. Current source is not necessarily identical to every earlier run snapshot. Site-level server paths in code and configurations require local adaptation; they are not participant source locators. Full reproduction requires the restricted inputs and [the reproduction guide](docs/auditory_v21/REPRODUCTION.md). Source selection and QC isolation limitations remain explicit. This publication does not authorize future participant-data releases.

## auditory_next v2 update

After completion of the v2 execution and audits, the researcher explicitly requested this GitHub push. This later instruction authorizes the curated code and aggregate snapshot despite historical "not pushed" or "no automatic publication" statements in the frozen plan, configuration and reports. It does not authorize publication of participant-level inputs, outputs, models or logs.

Start with [the v2 final status](docs/AUDITORY_NEXT_FINAL_STATUS_v2.md), [research decisions](docs/AUDITORY_NEXT_RESEARCH_DECISIONS_v2.md) and [final_002 report](reports/auditory_next_v2/final_002/NEXT_ROUND_REPORT.md). All eight packets have terminal receipts or explicit incomplete-control states. N1/N2/N3 did not meet progression criteria; the C2-R primary repair completed without clear joint benefit; E0-R remained numerically incomplete. Some synthetic worlds remain unevaluable. Execution completion is distinct from scientific validity. The original final_001 completion flag is superseded by the corrected integrity/permission/budget gate in final_002; both the original permission failure and its correction are retained.

The governing protocol, code, configurations, selected numerical outputs and all45 audited final_002 artifacts are exact copies. Only newly copied documentation receives publication notices and annotations for unavailable local links. README and publication guidance are editorial updates. [The v2 change record](release/auditory_next_v2_publication_changes.json) and [release manifest](release/manifest.json) identify exact source/published hashes. The previous Auditory5 verification is preserved as [historical evidence](release/verification_auditory5_v1.json); the current [verification](release/verification.json) covers this release. Packaging and data-independent checks run via CPU Slurm jobs, separately from the frozen scientific resource ledger; they do not refit participant models.

Private per-run source snapshots, event/bag/donor manifests, exact identity splits, participant-level support tables, native fit receipts, predictions and model artifacts remain on the server. Published source hashes do not make these private inputs downloadable. Current source is not claimed identical to every historical executed snapshot, and the published repository cannot reproduce the whole experiment without restricted inputs. Per-fit receipt field coverage and historical scheduler accounting remain partial; missing actual use is not zero. Synthetic unit-test fit calls during publication are counted separately and do not change the scientific fit ledger.

The GPU policy is now A100 by default, with A100/L40S/H100 preferred and V100/PRO6000 as alternatives; no future P100 use. Hardware in historical execution receipts is preserved. Observed site paths in scripts/configurations are environment settings, not participant file locators; adapt them for another cluster. One-off finalization/probe scripts have occupied run names and must not be blindly resubmitted.

## Auditory5 update

The researcher subsequently authorized pushing the Auditory5 implementation and existing results. This update includes the five-ideas protocol, source modules and tests, frozen configurations, Slurm entry points, implementation notes, interim reports, and the final `S4_final_001` aggregate report/figures. All90 representation tasks completed. B/D have negative primary screens; A has unsupported history balancing; C has numerical readout failures; E has partial numerical failures and insufficient E1 support. Numerical failures are not zero or negative scientific effects.

The original scientific outputs remain unchanged. New numerical result files, configurations, source code and the governing plan are byte-for-byte copies; publication copies of new Markdown reports add a scope notice and mark unavailable server downloads. The historical draft spec review is explicitly subordinate to the executed decisions. The updated README is an editorial summary of the final aggregates. Exact additions and changes are recorded in [the Auditory5 publication record](release/auditory5_publication_changes.json).

The private90-task plan contains individual training/test group lists and remains on the server. Its public aggregate descriptor, plan hash and task-status matrix are included. Raw/processed signals, manifests and identity splits with individual IDs, clinical rows, embeddings, per-person predictions, weights/checkpoints and detailed logs remain excluded. This explicit publication request covers the curated code and aggregate snapshot; it does not release the participant dataset.

Use [the Auditory5 reproduction guide](docs/AUDITORY5_REPRODUCTION_v1.md) and the final report for current status. Older “queued”, “not trained” and “server only” statements are historical. Site paths and scheduler partitions in scripts/configurations describe the observed server and need adaptation elsewhere. Module tests can run without private participant inputs; full scientific reproduction requires those restricted inputs. The release verification runs the published173-test Auditory5 suite through Slurm in addition to the legacy checks.

## Original Phase 0–3 snapshot

This snapshot was prepared on 2026-09-17 for the researcher-authorized publication of existing project results at `W-Yinghao/auditory`. It contains analysis source, frozen configurations, protocols, research reports, selected aggregate tables and figures. It does not release the underlying human-participant dataset.

## Included and retained on the server

Included results are selected explicitly by file, rather than by copying the entire results tree. Both favorable measurement-reliability results and negative/weak clinical and decoding results are retained. Final metadata corrections accompany the original outcome definitions; no scientific result was recomputed or selected for significance during packaging.

The following remain on the research server: raw and processed EEG, epoch arrays and event ledgers, identifying names and dates, source paths and identity maps, clinical row values, participant/record-level feature and prediction tables, individual waveform collections, logs, dependencies and source archives. Pseudonymous IDs do not establish anonymity. Aggregate reports can describe small groups; this repository is not a certified anonymous participant-data release.

Historical reports and configurations were written before GitHub publication was requested. Statements that results were “server only” or publication was not authorized describe that earlier state. This document authorizes no further data release: its scope is the curated files in [the release manifest](release/manifest.json). References to omitted server artifacts are displayed as text rather than working download links. Source scientific documents remain unchanged in the research workspace; publication copies carry a scope notice and adjusted links.

Frozen configurations, selected numeric result files and analysis code are copied byte for byte, with one code exception: `phase3_metadata_addendum.py` loads its adjudicated clinical row rules from an omitted private JSON input instead of embedding row positions and note excerpts. The analysis algorithm is retained; the original script and exact rule map remain on the server. The manifest records source and published SHA256 values and documents publication-only changes. The supplied `server_restart_en_v1/` package is historical planning evidence; its existing checksum manifest remains applicable. No source EEG was edited or uploaded.

## Environment and execution

The analysis environment uses Python 3.13.7. [requirements-observed.txt](requirements-observed.txt) records the observed versions of relevant packages, rather than claiming a complete dependency lock or a clean-install validation. Some older audit scripts were written for this server layout and contain explicit workspace/environment paths. Existing Slurm scripts target the `CPU` partition and retain the executed resource requests. Adapt scheduler and executable paths for another installation; preserve original configurations and use new output directories for new runs.

All CPU/GPU analyses, dependency installation, environment probes and tests must run through Slurm. Original data are read-only. Several scripts intentionally refuse to overwrite an existing run. The private inventory map and candidate linkage artifacts are required to reproduce the original opaque IDs; a fresh inventory is not an interchangeable replacement. Current and superseded versions and the necessary order of stages are documented in the four artifact guides.

To run the data-independent reader/measurement unit checks on an appropriately provisioned Slurm cluster, replace the paths and partition in this example:

```bash
mkdir -p private
chmod 700 private
sbatch --partition=CPU --cpus-per-task=1 --mem=3G --time=00:05:00 \
  --chdir=/path/to/auditory --output=private/tests-%j.log \
  --wrap='umask 077; export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1; PYTHONPATH=scripts /path/to/python -m unittest discover -s tests -v'
```

These checks do not rerun the data analyses. Historical delivery checks depend on intentionally omitted server artifacts; their archived summaries describe those original checks. The separate release verification records checks performed on the GitHub snapshot.

## Interpretation

Read the final Phase 3 report before interpreting the figures. The analyses are exploratory, candidate identities and source labels have evidence limits, device power remains unconfirmed, and the CI MUSS scale header conflicts with its observed range. Within-record reliability is distinct from test–retest reliability or clinical validity. Trial-budget resampling is retrospective and does not validate shorter acquisitions. The current HA models did not improve MUSS prediction. No foundation-model training or external clinical validation has been completed.
