# ALN3.6 R2 replication and ALN4.2 NET diagnostic (2026-10-21)

## ALN3.6 R2 (seed 3407)

- **Readouts and analysis:** the R1 code under `aln36.r2`, run on 2026-10-21 at 21:20–21:22.
  - Results: `results/auditory_alignment_v3/aln36/r2/r2_final/` (`summary.json`, `per_person.csv`, `FAMILY_TABLES.md`).
  - All 9 families are complete, with full coverage.
- **Replication:** `results/auditory_alignment_v3/aln36/r2/R1_R2_REPLICATION.md` (generator `aln36/r2_tables.py`).
  - 51 members are resolved in at least one seed. 46 have the same mark in both seeds; none flips sign.
  - The 5 that differ include 0 in R1 and are resolved in R2, in the direction of the R1 point estimate: FAU TH CBpre GT,
    children AP DT, and children twin_E0 / twin_ET for AP and twin_E0 for APwrong.
- **Fixed shared readout on the excluded HA group:**
  - CBpre G0: R1 +0.00233 [+0.00139, +0.00327]; R2 +0.00232 [+0.00122, +0.00342].
  - local G0: R1 +0.00173; R2 +0.00220 [+0.00126, +0.00315].
- **CI and TH G0 include 0 in both seeds.** DTU G0 is positive in both seeds (CBpre R2 +0.00324).
- **Personal time reweighting (DT) is harmful in every public cell in both seeds.** Examples: FAU HA CBpre −0.00796, DTU
  CBpre −0.00753 (R2).
- **Children:** AP−APwrong includes 0 in both seeds.
  - In R2 the strict-twin difference is positive for AP (+0.00082 [+0.00027, +0.00137]).
  - It is also positive for APwrong (+0.00165 [+0.00026, +0.00305]).
  - So the twin signal is not specific to the correct pairing.
- **The children mechanism family keeps the history outlier.** Its GH term is seed-independent: +0.06398, with a bootstrap-t
  critical value of about 159.7.

## NET diagnostic (post-R1, labelled as such)

- **Inputs:** `aln42/net_adapter.py` feeds the package tool `tools/paired_risk_summary.py`, which uses the fixed-SE max-|z|
  person bootstrap.
  - Output: `results/auditory_alignment_v3/aln42/net/paired_net_diagnostic_s3401_s3407.json` (700 rows; seeds averaged within
    person).
  - The seed-3401 version sits beside it. The original ALN3.6 families are unchanged.
- **Definitions:** NET_C = R(E0) − R(EC) and NET_T = R(E0) − R(ET). Positive means the personal update helps.

| Cohort | NET_C CBpre | NET_T CBpre | NET_C local | NET_T local |
|---|---|---|---|---|
| DTU (44) | −0.0078 [−0.0096, −0.0059] | −0.0146 [−0.0170, −0.0121] | −0.0077 | −0.0142 |
| FAU HA (29) | −0.0059 [−0.0067, −0.0051] | −0.0134 [−0.0155, −0.0113] | −0.0061 | −0.0144 |
| FAU CI (24) | −0.0054 [−0.0069, −0.0038] | −0.0149 [−0.0187, −0.0111] | −0.0064 | −0.0145 |
| FAU TH (14) | −0.0058 [−0.0068, −0.0047] | −0.0158 [−0.0196, −0.0119] | −0.0056 | −0.0163 |

- **Public cohorts:** relative to the shared readout E0, the personal scale recalibration (EC) is a net loss for every
  cohort and tool. Adding the time reweighting (ET) doubles the loss.
  - GC > 0 does not imply a net benefit. It is offset by the GH history recalibration, which is about −0.006 to −0.008.
  - Single-seed and two-seed values agree to within 0.0008.
- **Private:** about +0.064 ± 0.064 for both tools. This is the history-term outlier described above, so the result is
  uninformative. No child was removed.
