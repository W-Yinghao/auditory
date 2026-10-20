# publish_034 — results of the two bounded ALN3.5 lanes, lane records since publish_033

Researcher instruction 2026-10-20: "你来push一版到github". Established publication scope (everything except the private
dataset itself, names and identity mappings; no weights, run logs or storage-cleanup tooling). This is a snapshot of
continuing experiments, not a declaration that the registered work is complete.

## What is new since publish_033 (2026-10-20 10:28 CEST)

- **[S35_CBAUD_PEOPLE results](aln35/CBAUD_PEOPLE_RESULTS.md)** (DTU, 44 people, seed 3401; design frozen before
  results in [CBAUD_PEOPLE_DESIGN](aln35/CBAUD_PEOPLE_DESIGN.md)). Native readout: the auditory-continued CBraMod start
  has lower true-query NLL than the direct start at 50% source people, +0.156 bits/query [+0.057, +0.256]
  (simultaneous 95%); at 25% +0.093 [−0.014, +0.199] and at 100% +0.017 [−0.019, +0.054] are uncertain; the 50%
  advantage exceeds the 100% advantage by +0.139 [+0.050, +0.228]. Unified readout: every column includes 0.
  The auditory start does not replace source people: native risk at 50% people with the auditory start (6.356)
  remains above 100% people with the direct start (5.988). Both arms inherit the ALN3.4 gain-based early-stopping
  rule, not source-side true-risk selection.
- **[Episode replication with seed-3407 sources](aln35/EPISODE_REPLICATION_S3407_RESULTS.md)** (design:
  [EPISODE_REPLICATION_S3407_DESIGN](aln35/EPISODE_REPLICATION_S3407_DESIGN.md); 10/10 units). Local native,
  fixed 20 inner steps, pressure 100: episode vs ordinary +0.041 [+0.023, +0.059] at U10 and +0.034 [+0.016, +0.052]
  at U30, close to the seed-3401 values (+0.034, +0.037); ordinary vs source stays near 0. Unified: +0.017 and +0.013
  with lower bounds near 0. Selected-checkpoint native: +0.036 [+0.012, +0.060] at U10, +0.026 [−0.000, +0.052] at U30.
  One seed panel replicates the local native benefit; it does not add independent people.
- **Analysis code**: `scripts/auditory_alignment_v3/aln35/cbaud_people_analysis_v1.py` and
  `episode_rep_s3407_analysis_v1.py`, summaries in `results/auditory_alignment_v3/aln35/{cbaud_people_v1,episode_rep_s3407_v1}/`.
  The reused episode summary helper writes a fixed seed-3401 provenance label; the replication analysis asserts that
  label and that every unit is seed 3407, then relabels the rows to 3407 (documented in the script).
- **Operations**: on 2026-10-20 17:17–17:19 four requeued tail workers died within 40 s of starting with
  "CUDA error: uncorrectable ECC error"; each lane stopped on its failure marker. After checking that no result or
  checkpoint had been written by the failed attempts, the markers were preserved (not deleted) and the lanes resumed
  at the 10-GPU cap (`scripts/auditory_alignment_v3/aln35/fleet_v3_20261020/RECEIPT.md`, `resolve_ecc_20261020.py`).

## Lane records

`results/auditory_alignment_v3/unit_records/lanes_034_*.tar.gz` with `LANES_MANIFEST_034.tsv`: ALN3.4 and ALN3.5 lane
records not already published byte-identically in publish_030–033 (member name and SHA256), including the 20
S35_CBAUD_PEOPLE and 10 seed-3407 episode records and the tail-lane completions since publish_033. Main-runner archives
are unchanged. Records, releases and seeds do not increase independent participant n.

## Still running at this snapshot (19:55 CEST)

ALN3.4 tails: DTU learning budget (39 of 150 units remaining), DTU data curves (10 of 440), breadth budget (9 of 75),
breadth curves (74 of 300). Their interim result files carry their own generation times.

## Not published

Private raw data, file/event/clinical source tables, identity mappings, names/contact details, server-only support
geometry bindings, model weights, run logs, storage-cleanup tools/lists, agent handoff notes and their audit scripts.
Source and publication hashes: `results/auditory_alignment_v3/publication_034/MANIFEST.tsv`.
