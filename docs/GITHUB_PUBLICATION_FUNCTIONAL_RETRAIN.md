# Functional analyses, PTA repair and corrected-cohort retraining publication

The researcher explicitly requested this push after the retraining round. The
curated checkout is `/home/infres/yinwang/auditory_github`, separate from this
research workspace. Publication completed on 2026-09-19.

- Repository: https://github.com/W-Yinghao/auditory
- Branch: `main`
- Commit: `493a076a3848d3546a5889e2c583d0fee2ba1612`
- Verified index/commit tree: `603b3912f656203d2727642e75d73833352c3c58`
- Remote `refs/heads/main` was read back and equals this commit; checkout clean.

The commit changes 257 files and adds 247 selected source/scientific artifacts:
F-series qualification, archival analyses, PTA repair and HA/CI-MFF expansion,
and corrected-cohort full retraining. The release contains 1,308 tracked files,
1,306 payload hashes and 16,506,322 payload bytes. Of the new source files, 217
are exact copies; 30 Markdown copies add a publication/historical-status notice
and annotate any unavailable server links. Numerical results, code, tests,
configurations and figures are unchanged. The 1,051 historical payloads outside
the five navigation/editorial files remain unchanged, including earlier code
redactions. New README guidance explains the PTA lineage correction and retains
small/uncertain, negative and control-sensitive results.

Publication-only CPU Slurm jobs:

| Job | Purpose | Result |
|---|---|---|
| 999621 | Candidate/schema/known-token inspection | PASS; literal schema labels reviewed |
| 999623 | Explicit curated export and source-drift review | PASS |
| 999624 | Manifest and full publication verification | PASS |
| 999625 | First exact-index check | Rejected stale staged verification receipt; nothing pushed |
| 999626 | Final verification after editorial clarification | PASS |
| 999627 | Exact staged-blob and tree verification after restaging | PASS |

Jobs requested two CPUs each; time limits were 5, 5, 10, 5, 10 and 5 minutes,
respectively. Their total requested upper bound is 80 CPU core-minutes, separate
from scientific ledgers. No GPU work, model fitting, scientific test reruns or
scientific resampling was performed for publication. Original Markdown hard
breaks and CSV CRLF are preserved rather than normalizing frozen payloads.

Final publication verification parsed 327 Python files, checked 81 Slurm scripts,
399 local links, text in 28 PDFs and structure/metadata of 33 PNGs. It scanned
218 known-name entries, the configured parquet identifier dictionary (1,238)
and an expanded separate identifier dictionary (4,356), plus opaque-ID patterns
across the current tree. These dictionaries overlap; their counts must not be
summed as unique people. Checks are bounded and are not anonymity certification
or clearance of all Git history. The earlier disclosed legacy-script Git-history
limitation remains.

The verifier checked 144 new aggregate schemas, bound the historical 43-test
retraining preparation receipt, checked 112 retraining source bindings, all
45 representation completion receipts, 121 control states, 60 FP32 states,
180 model-metric rows and 16 repair-final output bindings. Existing V3 test and
completion bindings were retained. This verifies saved evidence and publication
integrity; it does not turn internal exploratory results into independent
clinical validation. The final exact-index receipt binds verification SHA256
`ee07f8d749845c8a008998671f5ba5b8c22efb618460a3f47dea965768c15859`.

Original/processed EEG, participant names/identifiers/dates/source paths,
clinical rows, exact folds, individual predictions and weights remain private.
Private publication scripts, allowlists, source dictionaries, logs and index
receipts are retained in `private/github_publish_006/` with restricted access.
The public change record, manifest and verification live under `release/`.
