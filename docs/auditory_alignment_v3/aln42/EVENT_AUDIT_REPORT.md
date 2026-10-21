# ALN4.2 §4.2: private children's event and history audit

Public-safe narrative. The report gives anonymous counts and kinds only. Children appear only under the authorised pseudonyms `childNN`. No record ids, identity keys, file paths or absolute times appear here. The row-wise traces, the identity crosswalk and the raw-event details stay in this private directory.

Audit id `ALN42_EVENT_AUDIT_v1` (2026-10-21). CPU only, run through Slurm step overlap on the evidence-service allocation. No existing file, code, plan or result was modified.

## 1. Question and scope

Background: ALN3.6 R1 found that one HA child (child60) had a stimulus sequence that looked opposite to the group's. This audit asks one question: does that pattern come from an implementation fault (codes, labels, alignment or history), or does the child's real stimulus sequence differ?

The audit covered all **64 children** of the private BDF lane (55 HA, 9 NH), one primary record each. That cohort is the set registered by the loader. child60 was the starting point because of the registered R1 validity item. Model scores played no part in choosing it. Every check below is computed from raw records and code, never from model outputs.

The chain was checked end to end for every child:

> raw event annotations → raw EEG signal → ST1 event table → D1 export (regenerated in memory from the raw signal with the frozen exporter) → GX staged epochs → loader (`load_private` / `load_kids`) → support/query split (`private_split`).

## 2. Rules as found in code (not chosen by the audit)

| Item | Rule in force |
|---|---|
| Label map | literal `1` → 0 (standard), literal `2` → 1 (deviant); any other literal is an unknown sound |
| History | Before-event only, built on the complete pre-QC stream, so QC-rejected stimuli are included. The chain restarts at the record start and after any non-target literal. The first run after a restart has unknown length. |
| Block reset | None. The 60-s `block_id` is bookkeeping only. |
| Since-last-deviant bins | {0}, {1}, {2}, {3}, {4,5}, {6+}. Rows whose value is unknown are dropped by the loader (`since_last_deviant >= 0`). |
| Epoch | 250 Hz, [-0.2, +0.6) s (50/150 samples), 2-s interval-edge guard. Slots W0/W1/W2 are native rows [0:100], [50:150], [100:200]. |
| Support/query guard | Uses the first ceil(0.3 × blocks) blocks. The support[:-1] / query[1:] boundary rule applies, and the full [-0.2, +0.6) epoch guard requires support end ≤ first query start. |

The history values were recomputed with an independent walk-back implementation, without calling the original history builder. The results were then compared row by row with the stored fields.

## 3. Whole-cohort result: no implementation fault

**Counts.**
- 63,601 raw annotation rows: 63,415 target stimuli and 186 non-target literal rows (185 × `0`, 1 × `4`).
- Every target had full epoch support, giving 63,415 staged epochs.
- 6,365 epochs were QC-rejected, leaving 57,050 accepted.
- 56,426 rows reached the loader. The other 624 accepted rows were dropped because their history was unknown under the registered chain-restart rule.

**Mismatches by kind, all 64 children:**

| Kind | Mismatches |
|---|---|
| Raw stream: non-monotonic order / duplicate samples / events outside the signal / non-zero event-clock offset | 0 / 0 / 0 / 0 |
| ST1 table vs raw: row count, trial id, literal, sample, kind, local id, onset, block, D1 index | 0 |
| ST1 history vs recompute: previous code, previous run length, previous gap, status, previous-event id (and previous id not in the past) | 0 |
| GX epochs vs raw: row set, geometry (rate/pre/post/fs/shape), y, onset, block | 0 |
| GX history vs recompute: previous code, run length, gap, status, since-last-deviant bin (all epochs and accepted only) | 0 |
| Loader vs raw recompute: row count, y, bin, block, onset, x row order/normalisation | 0 |
| Signal: best lag ≠ 0, relative RMSE > 1 %, QC accept flips, record-scale difference, D1 length, PF counts | 0 |
| Support/query guard violations; differences from the registered query/pool/geometry bindings | 0; 0/0/0 |

**Totals.** Label 0, history 0, alignment/geometry 0, block 0, roster/QC 0, guard 0.

### The checks can detect faults

- **Leaky history.** All 63,415 stored history bins equal the before-event recompute. A history that wrongly included the current label would match only 5,690 of them.
- **Accepted-only history.** A history built only from accepted epochs would differ on 5,932 accepted rows. 2,404 accepted rows follow a QC-dropped stimulus and still match the full-stream value.
- **Signal.** The raw D1 was regenerated with the frozen exporter and each staged epoch was cross-correlated against it over lags of −8 to +8 samples. The best lag was 0 for **all 63,415 epochs**. The relative RMSE was at most 2.8e-4, which is float16 quantisation.
- **Byte identity.** The regenerated D1 array is byte-identical to the deleted original for 15 of 64 records. The other 49 differ at byte level but agree with every staged epoch at the same float16 level. Byte identity is not required by the contract, and the cause of those differences was not investigated.

Two properties are documented but are not faults:
- The 250-Hz zero sample sits 0–3 ms before the 1-kHz trigger because of integer decimation. This is the same for all classes.
- All 185 `0` literals sit exactly at a stimulus slot, so they are probably stimuli with an unrecorded code. Under the registered rule they break the history chain.

All 15 cohort checks pass except `SEQUENCE_PROTOCOL_MATCH`, which is a property of the raw logs, not of the code. Section 4 covers it.

## 4. Sequence protocol per record and block

**Documented protocol:** pure-tone oddball, 80/20 standard/deviant. The mapping from code to physical tone frequency has never been confirmed, and no audio exists. The audit therefore claims nothing about acoustics.

**Cohort (62 records not flagged):**

| Statistic | Median | Range |
|---|---|---|
| Targets | 998 | 989–1000 |
| Deviant rate | 0.200 | 0.197–0.201 |
| Target SOA median | 0.781 s | 0.773–0.785 |
| Target SOA sd | 0.030 s | 0.029–0.031 |

- **Deviant spacing.** Always 2 to 6 standards between deviants. There are 0 back-to-back deviants.
- **Blocks.** 14 per record, with per-block deviant rates 0.15–0.33.
- **Implied transition table.** A deviant never follows a deviant, and after 6+ standards one almost always follows. This matches the group pattern quoted in R1.

**Flag rule (declared before the protocol outputs were read):** robust z > 5 on any of seven sequence statistics. No model scores were used. Two records were flagged:

- **child2: timing-only flag.** SOA dispersion is slightly high (sd 0.032 s) because a few triggers are irregular (minimum 0.53 s, maximum 1.12 s). Counts, deviant rate, spacing and the transition table all match the cohort. History bins are ordinal, so nothing changes; this is not registered as a mismatch.
- **child60: sequence-structure departure** on all seven statistics. Details are in section 5.

## 5. child60 deep dive: contract case (a)

**The raw chain is consistent end to end.**
- 601 raw annotations: 598 targets, one `4` start marker and two `0` literals.
- These became 598 staged epochs (all accepted, with 0 QC flips on recompute) and 588 loader rows.
- Label, history and alignment mismatches: **0**.
- Regenerated D1 is byte-identical to the deleted original, and the best lag is 0 for all 598 epochs.
- The support/query split equals the registered bindings: pool 143 rows, query 443 rows, 0 overlap, support ends before the first query starts.
- The EEG header signature (channel labels, equipment field, rates, units, ranges, prefilter) is identical across all 64 records. Record scale and acceptance fall inside the cohort range. The departure is therefore in the stimulus presentation, not in the EEG system.

**The real sequence differs** (child60 vs cohort):

| Statistic | child60 | Cohort |
|---|---|---|
| Targets | 598 | ≈1000 |
| Deviant rate | 0.151 | 0.200 (documented 0.20) |
| Target SOA median / sd | 0.849 / 0.088 s (jittered) | 0.781 / 0.030 s |
| Back-to-back deviants | 16 | 0 |
| Spacing between deviants (standards) | 0–27 | 2–6 |
| Blocks | 10 | 14 |
| P(deviant \| previous was deviant) | 0.178 | ≈ 0 |
| P(deviant \| 6+ standards) | 0.142 | ≈ 1 |

In the loader rows, 225 of 588 fall in the 6+ bin, and 193 of those are standards.

**The R1 history size follows from the raw sequence alone.** I applied the leave-one-out cohort table of P(deviant | since bin), with the same smoothing as `q0_table`, to child60's raw sequence. The result is a sequence-only cross-entropy of **4.83 bits/trial**; the cohort range is 0.44–0.49. This reproduces the R1 H0 of 4.77 bits/trial without any model output.

**Lane context.** This comes from the derived ST1 table, not the raw files. One other record in the same lane, outside the 64-child cohort, has the same sequence form: about 600 stimuli, about 15 % deviants, SOA about 0.85 s, back-to-back deviants allowed, and the same start marker. This points to an alternative presentation script rather than a corrupted log.

**Classification: case (a).** Codes, y, alignment and history are all consistent, and the child heard a different sequence. This is a true distribution mismatch, not a label or history bug.

## 6. Consequences

- **No recompute is required.** Status `NO_RECOMPUTE_REQUIRED` (see `PRIVATE_RECOMPUTE_SCOPE.json`). No bug was confirmed, so no BUG_SCOPE_RECEIPT was written.
- **Every result is kept.**
  - All children, rosters, families and primary counts stay as registered.
  - The ALN4.1 private units (private FT, frozen, readout, cross-stimulus, support, age) and the ALN3.6 private units (private features and readout) are reused unchanged.
- **child60 is registered as a real sequence-protocol mismatch.** Any history-conditioned statement for this child is conditional on the sequence it actually heard. This explains the degenerate R1 child-mechanism interval without excluding the child or switching method. Any follow-up is limited to CPU summaries of existing predictions.

## Deliverables (private directory)

| File | Contents | Visibility |
|---|---|---|
| `PRIVATE_EVENT_TRACE.json` | Schema `aln4.private_event_trace.v1`; validated with jsonschema Draft 2020-12, 0 errors. Holds the full 601-event trace of child60, 15 cohort checks and 145 dependency entries (REUSE_UNCHANGED). Row-wise traces for all 64 records are bound by hash. | private |
| `PRIVATE_EVENT_VALIDATION_SUMMARY.json` | Anonymous summary | public-safe |
| `PRIVATE_RECOMPUTE_SCOPE.json` | Recompute decision | public-safe |
| `EVENT_AUDIT_REPORT.md` | This report | public-safe |
| `PRIVATE_IDENTITY_CROSSWALK.json` | Identity crosswalk | private only |
| `cohort_rowwise_private.parquet` | Row-wise traces, all 64 records | private only |
| `audit_records_private.json` | Per-record audit records | private only |
| `child60_events_private.json` | child60 raw-event trace | private only |
| `protocol_table_private.csv` | Per-record protocol statistics | private only |
| `audit_events.py` | Audit script | script |
| `build_outputs.py` | Builds the deliverables | script |
| `explore_00_cohort.py`, `explore_01_lane_context.py` | Exploration scripts | script |
