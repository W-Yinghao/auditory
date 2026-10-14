# ALN3 B_DENSE dense readout — interim results

**Interim, seed 3401 only.** Generated 2026-10-14 11:07 CEST (Slurm job 1039549) by `python -m auditory_alignment_v3.bc_interim` under the frozen `ADDENDUM_05_BC_INTERIM_AGGREGATION.md`. Intervals are identity-level bootstrap-t (4000 replicates) conditional on the seed-3401 training; they are not training-seed uncertainty. Simultaneous intervals: max-t within the family named in each table. Sign: positive = the candidate is better (ΔR = R(reference) − R(candidate), bits per 5 s query, unified readout). Classes follow ADDENDUM_05 §7; no other interpretation is made here.

Code sha256: `bc_interim.py` 2840df81b608, `bc_interim_report.py` d0cfe6de6bcd, `sci_r1/stats.py` 8bb141cf6070.

## 0. Coverage and checks

| set | complete | other |
|---|---|---|
| B | 1000 | 0 |
| L | 50 | 0 |

Identities (local reference, NCE): FAU ci 24, ha 29, th 14; DTU hi 22, nh 22; Federici CI 33, HC 37, HC-v 16. Federici phantom entities excluded: 1.
Pairing check (identical participant sets and candidate / query counts per fold): {'matched': 570}; excluded pairs: 0.

## 1. Overview: interval classes (simultaneous 95%)

| family | dataset | objective | I>0 | I<0 | contains 0 |
|---|---|---|---|---|---|
| B-READOUT | FAU | NCE | 0 | 7 | 3 |
| B-READOUT | FAU | CS_SINGLE | 2 | 5 | 3 |
| B-READOUT | DTU | NCE | 0 | 7 | 3 |
| B-READOUT | DTU | CS_SINGLE | 0 | 6 | 4 |
| B-READOUT | Federici | NCE | 0 | 4 | 6 |
| B-READOUT | Federici | CS_SINGLE | 0 | 0 | 10 |
| B-INIT | FAU | NCE | 11 | 2 | 3 |
| B-INIT | FAU | CS_SINGLE | 0 | 3 | 13 |
| B-INIT | DTU | NCE | 10 | 0 | 6 |
| B-INIT | DTU | CS_SINGLE | 2 | 0 | 14 |
| B-INIT | Federici | NCE | 4 | 0 | 12 |
| B-INIT | Federici | CS_SINGLE | 0 | 0 | 16 |
| B-ADAPT | FAU | NCE | 3 | 2 | 7 |
| B-ADAPT | FAU | CS_SINGLE | 0 | 1 | 11 |
| B-ADAPT | DTU | NCE | 2 | 1 | 9 |
| B-ADAPT | DTU | CS_SINGLE | 1 | 0 | 11 |
| B-ADAPT | Federici | NCE | 2 | 0 | 10 |
| B-ADAPT | Federici | CS_SINGLE | 0 | 0 | 12 |
| B-LOCAL | FAU | NCE | 0 | 20 | 0 |
| B-LOCAL | FAU | CS_SINGLE | 0 | 20 | 0 |
| B-LOCAL | DTU | NCE | 0 | 20 | 0 |
| B-LOCAL | DTU | CS_SINGLE | 0 | 20 | 0 |
| B-LOCAL | Federici | NCE | 0 | 20 | 0 |
| B-LOCAL | Federici | CS_SINGLE | 0 | 20 | 0 |

## 2. Levels (unified readout)

R = true-query candidate cross-entropy (bits, lower is better); other columns are identity means.

**FAU · NCE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| B cbramod / pretrained_frozen / channel_phase_linear | 67 | 6.691 [+6.689, +6.692] | 0.011 | 0.488 | 0.006 | 6.691 | 0.502 |
| B cbramod / pretrained_frozen / dense_query | 67 | 6.691 [+6.691, +6.691] | 0.010 | 0.500 | 0.000 | 6.691 | 0.486 |
| B cbramod / pretrained_full / channel_phase_linear | 67 | 6.688 [+6.685, +6.691] | 0.011 | 0.483 | 0.011 | 6.690 | 0.505 |
| B cbramod / pretrained_full / dense_query | 67 | 6.691 [+6.691, +6.691] | 0.010 | 0.500 | 0.000 | 6.691 | 0.495 |
| B cbramod / pretrained_partial / channel_phase_linear | 67 | 6.690 [+6.688, +6.692] | 0.010 | 0.488 | 0.006 | 6.691 | 0.503 |
| B cbramod / pretrained_partial / dense_query | 67 | 6.691 [+6.691, +6.691] | 0.010 | 0.500 | 0.000 | 6.691 | 0.490 |
| B cbramod / pretrained_peft / channel_phase_linear | 67 | 6.683 [+6.680, +6.686] | 0.013 | 0.475 | 0.016 | 6.690 | 0.510 |
| B cbramod / pretrained_peft / dense_query | 67 | 6.691 [+6.691, +6.691] | 0.010 | 0.500 | 0.000 | 6.691 | 0.482 |
| B cbramod / random_full / channel_phase_linear | 67 | 6.684 [+6.681, +6.688] | 0.012 | 0.473 | 0.016 | 6.686 | 0.520 |
| B cbramod / random_full / dense_query | 67 | 6.692 [+6.692, +6.692] | 0.010 | 0.499 | 0.000 | 6.691 | 0.493 |
| B reve / pretrained_frozen / channel_phase_linear | 67 | 6.657 [+6.648, +6.666] | 0.016 | 0.438 | 0.065 | 6.658 | 0.513 |
| B reve / pretrained_frozen / dense_query | 67 | 6.691 [+6.691, +6.691] | 0.010 | 0.499 | 0.000 | 6.691 | 0.485 |
| B reve / pretrained_full / channel_phase_linear | 67 | 6.654 [+6.645, +6.664] | 0.016 | 0.437 | 0.068 | 6.652 | 0.515 |
| B reve / pretrained_full / dense_query | 67 | 6.691 [+6.691, +6.691] | 0.010 | 0.499 | 0.000 | 6.691 | 0.485 |
| B reve / pretrained_partial / channel_phase_linear | 67 | 6.655 [+6.645, +6.664] | 0.016 | 0.437 | 0.068 | 6.652 | 0.514 |
| B reve / pretrained_partial / dense_query | 67 | 6.691 [+6.691, +6.691] | 0.010 | 0.499 | 0.000 | 6.691 | 0.485 |
| B reve / pretrained_peft / channel_phase_linear | 67 | 6.659 [+6.649, +6.668] | 0.016 | 0.438 | 0.063 | 6.647 | 0.511 |
| B reve / pretrained_peft / dense_query | 67 | 6.692 [+6.691, +6.692] | 0.010 | 0.499 | 0.000 | 6.691 | 0.483 |
| B reve / random_full / channel_phase_linear | 67 | 6.673 [+6.667, +6.678] | 0.014 | 0.453 | 0.034 | 6.678 | 0.517 |
| B reve / random_full / dense_query | 67 | 6.692 [+6.691, +6.692] | 0.010 | 0.500 | 0.000 | 6.691 | 0.495 |
| local `lag_local_tokens` full | 67 | 6.309 [+6.189, +6.428] | 0.066 | 0.302 | 1.044 | 6.004 | 0.547 |

**FAU · CS_SINGLE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| B cbramod / pretrained_frozen / channel_phase_linear | 67 | 6.691 [+6.691, +6.692] | 0.010 | 0.497 | 0.000 | 6.693 | 0.483 |
| B cbramod / pretrained_frozen / dense_query | 67 | 6.693 [+6.692, +6.693] | 0.011 | 0.501 | -0.001 | 6.693 | 0.523 |
| B cbramod / pretrained_full / channel_phase_linear | 67 | 6.690 [+6.690, +6.691] | 0.009 | 0.492 | 0.002 | 6.693 | 0.490 |
| B cbramod / pretrained_full / dense_query | 67 | 6.693 [+6.692, +6.694] | 0.010 | 0.500 | 0.000 | 6.694 | 0.508 |
| B cbramod / pretrained_partial / channel_phase_linear | 67 | 6.691 [+6.690, +6.691] | 0.009 | 0.494 | 0.001 | 6.693 | 0.491 |
| B cbramod / pretrained_partial / dense_query | 67 | 6.694 [+6.693, +6.695] | 0.011 | 0.500 | -0.000 | 6.694 | 0.515 |
| B cbramod / pretrained_peft / channel_phase_linear | 67 | 6.692 [+6.691, +6.692] | 0.011 | 0.495 | 0.002 | 6.693 | 0.492 |
| B cbramod / pretrained_peft / dense_query | 67 | 6.695 [+6.693, +6.696] | 0.009 | 0.501 | 0.000 | 6.694 | 0.513 |
| B cbramod / random_full / channel_phase_linear | 67 | 6.691 [+6.690, +6.692] | 0.010 | 0.493 | 0.001 | 6.692 | 0.505 |
| B cbramod / random_full / dense_query | 67 | 6.693 [+6.691, +6.694] | 0.009 | 0.501 | 0.000 | 6.693 | 0.521 |
| B reve / pretrained_frozen / channel_phase_linear | 67 | 6.693 [+6.692, +6.693] | 0.010 | 0.498 | 0.000 | 6.693 | 0.519 |
| B reve / pretrained_frozen / dense_query | 67 | 6.692 [+6.691, +6.692] | 0.009 | 0.500 | 0.000 | 6.693 | 0.529 |
| B reve / pretrained_full / channel_phase_linear | 67 | 6.693 [+6.692, +6.693] | 0.010 | 0.498 | 0.001 | 6.693 | 0.522 |
| B reve / pretrained_full / dense_query | 67 | 6.691 [+6.691, +6.692] | 0.009 | 0.499 | 0.000 | 6.692 | 0.530 |
| B reve / pretrained_partial / channel_phase_linear | 67 | 6.693 [+6.692, +6.693] | 0.010 | 0.498 | 0.001 | 6.693 | 0.522 |
| B reve / pretrained_partial / dense_query | 67 | 6.693 [+6.692, +6.695] | 0.010 | 0.500 | -0.000 | 6.693 | 0.527 |
| B reve / pretrained_peft / channel_phase_linear | 67 | 6.691 [+6.688, +6.693] | 0.010 | 0.491 | 0.005 | 6.690 | 0.518 |
| B reve / pretrained_peft / dense_query | 67 | 6.691 [+6.691, +6.692] | 0.010 | 0.500 | 0.000 | 6.693 | 0.524 |
| B reve / random_full / channel_phase_linear | 67 | 6.691 [+6.691, +6.691] | 0.010 | 0.500 | 0.000 | 6.693 | 0.523 |
| B reve / random_full / dense_query | 67 | 6.693 [+6.692, +6.694] | 0.009 | 0.499 | 0.001 | 6.693 | 0.522 |
| local `lag_local_tokens` full | 67 | 6.358 [+6.278, +6.438] | 0.054 | 0.317 | 0.724 | 6.340 | 0.543 |

**DTU · NCE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| B cbramod / pretrained_frozen / channel_phase_linear | 44 | 7.736 [+7.727, +7.745] | 0.006 | 0.478 | 0.024 | 7.727 | 0.525 |
| B cbramod / pretrained_frozen / dense_query | 44 | 7.738 [+7.734, +7.741] | 0.006 | 0.509 | -0.000 | 7.726 | 0.484 |
| B cbramod / pretrained_full / channel_phase_linear | 44 | 7.730 [+7.720, +7.739] | 0.004 | 0.475 | 0.028 | 7.725 | 0.521 |
| B cbramod / pretrained_full / dense_query | 44 | 7.740 [+7.736, +7.743] | 0.005 | 0.510 | -0.000 | 7.726 | 0.483 |
| B cbramod / pretrained_partial / channel_phase_linear | 44 | 7.737 [+7.727, +7.747] | 0.006 | 0.476 | 0.029 | 7.723 | 0.523 |
| B cbramod / pretrained_partial / dense_query | 44 | 7.740 [+7.735, +7.745] | 0.006 | 0.508 | 0.000 | 7.726 | 0.487 |
| B cbramod / pretrained_peft / channel_phase_linear | 44 | 7.731 [+7.725, +7.737] | 0.005 | 0.486 | 0.014 | 7.730 | 0.510 |
| B cbramod / pretrained_peft / dense_query | 44 | 7.742 [+7.736, +7.749] | 0.006 | 0.508 | 0.000 | 7.727 | 0.488 |
| B cbramod / random_full / channel_phase_linear | 44 | 7.726 [+7.720, +7.733] | 0.004 | 0.476 | 0.024 | 7.720 | 0.505 |
| B cbramod / random_full / dense_query | 44 | 7.747 [+7.741, +7.753] | 0.004 | 0.509 | 0.001 | 7.725 | 0.488 |
| B reve / pretrained_frozen / channel_phase_linear | 44 | 7.663 [+7.645, +7.681] | 0.009 | 0.415 | 0.144 | 7.685 | 0.533 |
| B reve / pretrained_frozen / dense_query | 44 | 7.736 [+7.731, +7.741] | 0.004 | 0.505 | 0.001 | 7.727 | 0.488 |
| B reve / pretrained_full / channel_phase_linear | 44 | 7.654 [+7.635, +7.673] | 0.011 | 0.409 | 0.166 | 7.669 | 0.539 |
| B reve / pretrained_full / dense_query | 44 | 7.735 [+7.730, +7.741] | 0.004 | 0.507 | 0.000 | 7.727 | 0.482 |
| B reve / pretrained_partial / channel_phase_linear | 44 | 7.654 [+7.634, +7.674] | 0.011 | 0.409 | 0.166 | 7.669 | 0.539 |
| B reve / pretrained_partial / dense_query | 44 | 7.735 [+7.730, +7.740] | 0.004 | 0.507 | 0.000 | 7.727 | 0.482 |
| B reve / pretrained_peft / channel_phase_linear | 44 | 7.647 [+7.624, +7.669] | 0.012 | 0.405 | 0.182 | 7.645 | 0.545 |
| B reve / pretrained_peft / dense_query | 44 | 7.742 [+7.736, +7.748] | 0.005 | 0.507 | 0.000 | 7.727 | 0.487 |
| B reve / random_full / channel_phase_linear | 44 | 7.703 [+7.689, +7.718] | 0.008 | 0.440 | 0.088 | 7.710 | 0.519 |
| B reve / random_full / dense_query | 44 | 7.753 [+7.745, +7.761] | 0.005 | 0.506 | 0.000 | 7.726 | 0.483 |
| local `lag_local_tokens` full | 44 | 6.869 [+6.712, +7.026] | 0.066 | 0.224 | 2.009 | 6.214 | 0.668 |

**DTU · CS_SINGLE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| B cbramod / pretrained_frozen / channel_phase_linear | 44 | 7.733 [+7.729, +7.737] | 0.005 | 0.497 | 0.003 | 7.726 | 0.499 |
| B cbramod / pretrained_frozen / dense_query | 44 | 7.752 [+7.744, +7.761] | 0.005 | 0.498 | -0.001 | 7.727 | 0.484 |
| B cbramod / pretrained_full / channel_phase_linear | 44 | 7.732 [+7.727, +7.738] | 0.005 | 0.487 | 0.009 | 7.726 | 0.503 |
| B cbramod / pretrained_full / dense_query | 44 | 7.741 [+7.735, +7.747] | 0.003 | 0.500 | -0.004 | 7.728 | 0.490 |
| B cbramod / pretrained_partial / channel_phase_linear | 44 | 7.737 [+7.733, +7.742] | 0.003 | 0.493 | 0.006 | 7.726 | 0.506 |
| B cbramod / pretrained_partial / dense_query | 44 | 7.749 [+7.743, +7.755] | 0.004 | 0.505 | -0.003 | 7.729 | 0.486 |
| B cbramod / pretrained_peft / channel_phase_linear | 44 | 7.736 [+7.731, +7.740] | 0.006 | 0.498 | 0.004 | 7.726 | 0.503 |
| B cbramod / pretrained_peft / dense_query | 44 | 7.739 [+7.735, +7.744] | 0.004 | 0.497 | 0.002 | 7.726 | 0.495 |
| B cbramod / random_full / channel_phase_linear | 44 | 7.731 [+7.726, +7.735] | 0.004 | 0.487 | 0.008 | 7.726 | 0.498 |
| B cbramod / random_full / dense_query | 44 | 7.748 [+7.742, +7.753] | 0.005 | 0.503 | 0.000 | 7.727 | 0.489 |
| B reve / pretrained_frozen / channel_phase_linear | 44 | 7.742 [+7.736, +7.748] | 0.006 | 0.490 | 0.006 | 7.725 | 0.488 |
| B reve / pretrained_frozen / dense_query | 44 | 7.761 [+7.754, +7.768] | 0.006 | 0.499 | -0.001 | 7.733 | 0.483 |
| B reve / pretrained_full / channel_phase_linear | 44 | 7.740 [+7.734, +7.746] | 0.007 | 0.491 | 0.006 | 7.725 | 0.490 |
| B reve / pretrained_full / dense_query | 44 | 7.756 [+7.749, +7.762] | 0.006 | 0.500 | -0.000 | 7.733 | 0.481 |
| B reve / pretrained_partial / channel_phase_linear | 44 | 7.740 [+7.735, +7.746] | 0.007 | 0.491 | 0.006 | 7.725 | 0.490 |
| B reve / pretrained_partial / dense_query | 44 | 7.756 [+7.749, +7.762] | 0.006 | 0.500 | -0.000 | 7.733 | 0.481 |
| B reve / pretrained_peft / channel_phase_linear | 44 | 7.746 [+7.738, +7.755] | 0.007 | 0.488 | 0.007 | 7.728 | 0.483 |
| B reve / pretrained_peft / dense_query | 44 | 7.755 [+7.746, +7.764] | 0.005 | 0.503 | -0.000 | 7.732 | 0.484 |
| B reve / random_full / channel_phase_linear | 44 | 7.750 [+7.740, +7.760] | 0.007 | 0.492 | 0.004 | 7.731 | 0.484 |
| B reve / random_full / dense_query | 44 | 7.756 [+7.749, +7.763] | 0.005 | 0.500 | -0.003 | 7.727 | 0.487 |
| local `lag_local_tokens` full | 44 | 7.108 [+6.986, +7.230] | 0.047 | 0.255 | 1.381 | 7.205 | 0.651 |

**Federici · NCE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| B cbramod / pretrained_frozen / channel_phase_linear | 86 | 8.174 [+8.169, +8.178] | 0.004 | 0.492 | 0.000 | 8.169 | – |
| B cbramod / pretrained_frozen / dense_query | 86 | 8.171 [+8.170, +8.172] | 0.005 | 0.505 | -0.000 | 8.169 | – |
| B cbramod / pretrained_full / channel_phase_linear | 86 | 8.169 [+8.167, +8.171] | 0.006 | 0.485 | 0.001 | 8.169 | – |
| B cbramod / pretrained_full / dense_query | 86 | 8.171 [+8.170, +8.173] | 0.004 | 0.510 | -0.000 | 8.171 | – |
| B cbramod / pretrained_partial / channel_phase_linear | 86 | 8.170 [+8.167, +8.173] | 0.006 | 0.488 | 0.001 | 8.169 | – |
| B cbramod / pretrained_partial / dense_query | 86 | 8.171 [+8.170, +8.172] | 0.002 | 0.503 | -0.000 | 8.169 | – |
| B cbramod / pretrained_peft / channel_phase_linear | 86 | 8.171 [+8.168, +8.173] | 0.004 | 0.492 | -0.001 | 8.168 | – |
| B cbramod / pretrained_peft / dense_query | 86 | 8.170 [+8.170, +8.171] | 0.003 | 0.506 | -0.000 | 8.169 | – |
| B cbramod / random_full / channel_phase_linear | 86 | 8.172 [+8.167, +8.178] | 0.003 | 0.493 | 0.002 | 8.170 | – |
| B cbramod / random_full / dense_query | 86 | 8.172 [+8.169, +8.175] | 0.005 | 0.498 | 0.000 | 8.170 | – |
| B reve / pretrained_frozen / channel_phase_linear | 86 | 8.158 [+8.151, +8.166] | 0.007 | 0.475 | 0.025 | 8.159 | – |
| B reve / pretrained_frozen / dense_query | 86 | 8.171 [+8.169, +8.174] | 0.002 | 0.498 | 0.000 | 8.176 | – |
| B reve / pretrained_full / channel_phase_linear | 86 | 8.158 [+8.149, +8.166] | 0.007 | 0.473 | 0.029 | 8.152 | – |
| B reve / pretrained_full / dense_query | 86 | 8.170 [+8.169, +8.172] | 0.004 | 0.502 | -0.001 | 8.173 | – |
| B reve / pretrained_partial / channel_phase_linear | 86 | 8.158 [+8.149, +8.166] | 0.007 | 0.473 | 0.029 | 8.152 | – |
| B reve / pretrained_partial / dense_query | 86 | 8.170 [+8.169, +8.172] | 0.004 | 0.502 | -0.001 | 8.173 | – |
| B reve / pretrained_peft / channel_phase_linear | 86 | 8.098 [+8.071, +8.124] | 0.010 | 0.410 | 0.147 | 8.097 | – |
| B reve / pretrained_peft / dense_query | 86 | 8.178 [+8.172, +8.183] | 0.004 | 0.508 | -0.006 | 8.177 | – |
| B reve / random_full / channel_phase_linear | 86 | 8.172 [+8.168, +8.176] | 0.005 | 0.493 | 0.002 | 8.171 | – |
| B reve / random_full / dense_query | 86 | 8.173 [+8.171, +8.175] | 0.004 | 0.504 | 0.000 | 8.170 | – |
| local `lag_local_tokens` full | 86 | 8.056 [+8.022, +8.090] | 0.012 | 0.390 | 0.264 | 7.999 | – |

**Federici · CS_SINGLE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| B cbramod / pretrained_frozen / channel_phase_linear | 86 | 8.173 [+8.167, +8.178] | 0.004 | 0.494 | -0.002 | 8.171 | – |
| B cbramod / pretrained_frozen / dense_query | 86 | 8.169 [+8.167, +8.172] | 0.006 | 0.495 | 0.003 | 8.171 | – |
| B cbramod / pretrained_full / channel_phase_linear | 86 | 8.172 [+8.167, +8.178] | 0.003 | 0.492 | 0.000 | 8.171 | – |
| B cbramod / pretrained_full / dense_query | 86 | 8.173 [+8.169, +8.176] | 0.003 | 0.500 | -0.001 | 8.171 | – |
| B cbramod / pretrained_partial / channel_phase_linear | 86 | 8.173 [+8.168, +8.178] | 0.004 | 0.498 | -0.000 | 8.171 | – |
| B cbramod / pretrained_partial / dense_query | 86 | 8.169 [+8.167, +8.172] | 0.003 | 0.487 | -0.000 | 8.171 | – |
| B cbramod / pretrained_peft / channel_phase_linear | 86 | 8.172 [+8.167, +8.177] | 0.003 | 0.499 | 0.000 | 8.171 | – |
| B cbramod / pretrained_peft / dense_query | 86 | 8.171 [+8.169, +8.173] | 0.000 | 0.497 | -0.001 | 8.171 | – |
| B cbramod / random_full / channel_phase_linear | 86 | 8.171 [+8.168, +8.175] | 0.003 | 0.498 | 0.000 | 8.171 | – |
| B cbramod / random_full / dense_query | 86 | 8.171 [+8.168, +8.174] | 0.004 | 0.500 | -0.001 | 8.171 | – |
| B reve / pretrained_frozen / channel_phase_linear | 86 | 8.172 [+8.170, +8.175] | 0.004 | 0.503 | 0.000 | 8.171 | – |
| B reve / pretrained_frozen / dense_query | 86 | 8.172 [+8.167, +8.176] | 0.003 | 0.502 | 0.000 | 8.171 | – |
| B reve / pretrained_full / channel_phase_linear | 86 | 8.172 [+8.170, +8.175] | 0.004 | 0.503 | 0.000 | 8.171 | – |
| B reve / pretrained_full / dense_query | 86 | 8.171 [+8.169, +8.172] | 0.002 | 0.500 | 0.002 | 8.171 | – |
| B reve / pretrained_partial / channel_phase_linear | 86 | 8.172 [+8.170, +8.175] | 0.004 | 0.503 | 0.000 | 8.171 | – |
| B reve / pretrained_partial / dense_query | 86 | 8.170 [+8.169, +8.171] | 0.001 | 0.502 | 0.000 | 8.171 | – |
| B reve / pretrained_peft / channel_phase_linear | 86 | 8.172 [+8.170, +8.173] | 0.003 | 0.510 | 0.000 | 8.171 | – |
| B reve / pretrained_peft / dense_query | 86 | 8.171 [+8.169, +8.172] | 0.002 | 0.501 | 0.000 | 8.171 | – |
| B reve / random_full / channel_phase_linear | 86 | 8.174 [+8.171, +8.177] | 0.003 | 0.502 | 0.001 | 8.171 | – |
| B reve / random_full / dense_query | 86 | 8.173 [+8.170, +8.177] | 0.004 | 0.504 | 0.001 | 8.171 | – |
| local `lag_local_tokens` full | 86 | 8.077 [+8.045, +8.109] | 0.012 | 0.396 | 0.221 | 8.170 | – |

## 3. Readout at fixed backbone and adaptation: `channel_phase_linear` → `dense_query`

**FAU · NCE · cbramod** (family `B-READOUT|fau|NCE|cbramod`, critical value 2.51)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 67 | -0.008 | [-0.011, -0.004] | [-0.012, -0.003] | I<0 | -0.002 | -0.027 | -0.015 | -0.005 | -0.027 |
| pretrained_frozen | readout | 67 | -0.000 | [-0.002, +0.001] | [-0.002, +0.001] | contains 0 | -0.001 | -0.012 | -0.006 | +0.001 | -0.016 |
| pretrained_peft | readout | 67 | -0.008 | [-0.011, -0.005] | [-0.012, -0.005] | I<0 | -0.003 | -0.025 | -0.016 | -0.001 | -0.028 |
| pretrained_partial | readout | 67 | -0.001 | [-0.003, +0.000] | [-0.004, +0.001] | contains 0 | -0.001 | -0.012 | -0.006 | +0.000 | -0.013 |
| pretrained_full | readout | 67 | -0.003 | [-0.006, -0.000] | [-0.007, +0.000] | contains 0 | -0.001 | -0.017 | -0.011 | -0.001 | -0.010 |

**FAU · NCE · reve** (family `B-READOUT|fau|NCE|reve`, critical value 2.31)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 67 | -0.019 | [-0.024, -0.014] | [-0.025, -0.013] | I<0 | -0.004 | -0.047 | -0.034 | -0.013 | -0.022 |
| pretrained_frozen | readout | 67 | -0.034 | [-0.043, -0.025] | [-0.045, -0.024] | I<0 | -0.006 | -0.061 | -0.065 | -0.032 | -0.028 |
| pretrained_peft | readout | 67 | -0.033 | [-0.042, -0.023] | [-0.044, -0.022] | I<0 | -0.006 | -0.061 | -0.063 | -0.044 | -0.028 |
| pretrained_partial | readout | 67 | -0.036 | [-0.046, -0.027] | [-0.047, -0.026] | I<0 | -0.006 | -0.062 | -0.068 | -0.038 | -0.029 |
| pretrained_full | readout | 67 | -0.037 | [-0.046, -0.027] | [-0.047, -0.026] | I<0 | -0.006 | -0.063 | -0.068 | -0.039 | -0.029 |

**FAU · CS_SINGLE · cbramod** (family `B-READOUT|fau|CS_SINGLE|cbramod`, critical value 2.74)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 67 | -0.002 | [-0.003, -0.000] | [-0.004, +0.000] | contains 0 | -0.001 | -0.008 | -0.001 | -0.001 | +0.017 |
| pretrained_frozen | readout | 67 | -0.001 | [-0.002, -0.001] | [-0.003, -0.000] | I<0 | +0.001 | -0.004 | -0.001 | -0.000 | +0.040 |
| pretrained_peft | readout | 67 | -0.003 | [-0.005, -0.001] | [-0.005, -0.001] | I<0 | -0.002 | -0.006 | -0.002 | -0.001 | +0.021 |
| pretrained_partial | readout | 67 | -0.003 | [-0.005, -0.002] | [-0.005, -0.001] | I<0 | +0.001 | -0.005 | -0.002 | -0.001 | +0.024 |
| pretrained_full | readout | 67 | -0.003 | [-0.004, -0.001] | [-0.005, -0.001] | I<0 | +0.001 | -0.008 | -0.002 | -0.000 | +0.019 |

**FAU · CS_SINGLE · reve** (family `B-READOUT|fau|CS_SINGLE|reve`, critical value 2.70)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 67 | -0.002 | [-0.003, -0.000] | [-0.003, -0.000] | I<0 | -0.001 | +0.001 | +0.001 | +0.000 | -0.001 |
| pretrained_frozen | readout | 67 | +0.001 | [+0.000, +0.001] | [+0.000, +0.002] | I>0 | -0.000 | -0.002 | -0.000 | +0.000 | +0.009 |
| pretrained_peft | readout | 67 | -0.001 | [-0.003, +0.002] | [-0.003, +0.002] | contains 0 | -0.001 | -0.008 | -0.005 | -0.003 | +0.006 |
| pretrained_partial | readout | 67 | -0.001 | [-0.002, +0.000] | [-0.002, +0.001] | contains 0 | -0.000 | -0.002 | -0.001 | +0.000 | +0.005 |
| pretrained_full | readout | 67 | +0.001 | [+0.001, +0.002] | [+0.000, +0.002] | I>0 | -0.001 | -0.002 | -0.000 | +0.001 | +0.008 |

**DTU · NCE · cbramod** (family `B-READOUT|dtu|NCE|cbramod`, critical value 2.56)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 44 | -0.020 | [-0.028, -0.012] | [-0.030, -0.010] | I<0 | +0.000 | -0.032 | -0.023 | -0.005 | -0.017 |
| pretrained_frozen | readout | 44 | -0.002 | [-0.009, +0.006] | [-0.012, +0.008] | contains 0 | -0.000 | -0.031 | -0.024 | +0.001 | -0.041 |
| pretrained_peft | readout | 44 | -0.011 | [-0.016, -0.005] | [-0.018, -0.004] | I<0 | +0.001 | -0.022 | -0.014 | +0.003 | -0.023 |
| pretrained_partial | readout | 44 | -0.003 | [-0.011, +0.004] | [-0.013, +0.006] | contains 0 | +0.000 | -0.032 | -0.029 | -0.003 | -0.037 |
| pretrained_full | readout | 44 | -0.010 | [-0.019, -0.001] | [-0.022, +0.002] | contains 0 | +0.001 | -0.035 | -0.029 | -0.000 | -0.037 |

**DTU · NCE · reve** (family `B-READOUT|dtu|NCE|reve`, critical value 2.46)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 44 | -0.050 | [-0.062, -0.037] | [-0.065, -0.034] | I<0 | -0.003 | -0.066 | -0.087 | -0.016 | -0.036 |
| pretrained_frozen | readout | 44 | -0.073 | [-0.090, -0.055] | [-0.094, -0.051] | I<0 | -0.005 | -0.089 | -0.143 | -0.042 | -0.045 |
| pretrained_peft | readout | 44 | -0.096 | [-0.117, -0.074] | [-0.122, -0.069] | I<0 | -0.007 | -0.102 | -0.182 | -0.081 | -0.058 |
| pretrained_partial | readout | 44 | -0.081 | [-0.100, -0.062] | [-0.105, -0.058] | I<0 | -0.007 | -0.099 | -0.166 | -0.058 | -0.057 |
| pretrained_full | readout | 44 | -0.081 | [-0.101, -0.062] | [-0.105, -0.058] | I<0 | -0.007 | -0.099 | -0.166 | -0.058 | -0.057 |

**DTU · CS_SINGLE · cbramod** (family `B-READOUT|dtu|CS_SINGLE|cbramod`, critical value 2.79)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 44 | -0.017 | [-0.023, -0.011] | [-0.026, -0.008] | I<0 | +0.001 | -0.016 | -0.008 | -0.001 | -0.009 |
| pretrained_frozen | readout | 44 | -0.019 | [-0.027, -0.012] | [-0.029, -0.009] | I<0 | -0.001 | -0.001 | -0.004 | -0.002 | -0.015 |
| pretrained_peft | readout | 44 | -0.003 | [-0.009, +0.002] | [-0.011, +0.004] | contains 0 | -0.002 | +0.001 | -0.002 | -0.000 | -0.008 |
| pretrained_partial | readout | 44 | -0.011 | [-0.017, -0.006] | [-0.019, -0.004] | I<0 | +0.000 | -0.012 | -0.008 | -0.003 | -0.020 |
| pretrained_full | readout | 44 | -0.008 | [-0.015, -0.001] | [-0.018, +0.001] | contains 0 | -0.001 | -0.013 | -0.014 | -0.002 | -0.013 |

**DTU · CS_SINGLE · reve** (family `B-READOUT|dtu|CS_SINGLE|reve`, critical value 2.50)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 44 | -0.005 | [-0.019, +0.008] | [-0.023, +0.012] | contains 0 | -0.002 | -0.008 | -0.007 | +0.003 | +0.003 |
| pretrained_frozen | readout | 44 | -0.019 | [-0.028, -0.011] | [-0.030, -0.009] | I<0 | -0.000 | -0.009 | -0.007 | -0.007 | -0.006 |
| pretrained_peft | readout | 44 | -0.009 | [-0.017, -0.001] | [-0.019, +0.001] | contains 0 | -0.002 | -0.015 | -0.008 | -0.005 | +0.001 |
| pretrained_partial | readout | 44 | -0.016 | [-0.023, -0.009] | [-0.024, -0.007] | I<0 | -0.001 | -0.009 | -0.006 | -0.008 | -0.009 |
| pretrained_full | readout | 44 | -0.016 | [-0.023, -0.009] | [-0.024, -0.007] | I<0 | -0.001 | -0.009 | -0.006 | -0.008 | -0.009 |

**Federici · NCE · cbramod** (family `B-READOUT|federici|NCE|cbramod`, critical value 2.55)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 86 | +0.001 | [-0.006, +0.007] | [-0.008, +0.009] | contains 0 | +0.002 | -0.005 | -0.002 | +0.000 | – |
| pretrained_frozen | readout | 86 | +0.003 | [-0.002, +0.008] | [-0.003, +0.009] | contains 0 | +0.001 | -0.013 | -0.000 | -0.000 | – |
| pretrained_peft | readout | 86 | +0.000 | [-0.003, +0.003] | [-0.003, +0.004] | contains 0 | -0.001 | -0.014 | +0.001 | -0.001 | – |
| pretrained_partial | readout | 86 | -0.001 | [-0.004, +0.002] | [-0.005, +0.003] | contains 0 | -0.003 | -0.015 | -0.001 | -0.000 | – |
| pretrained_full | readout | 86 | -0.003 | [-0.005, +0.000] | [-0.006, +0.001] | contains 0 | -0.002 | -0.025 | -0.001 | -0.002 | – |

**Federici · NCE · reve** (family `B-READOUT|federici|NCE|reve`, critical value 2.42)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 86 | -0.001 | [-0.006, +0.004] | [-0.007, +0.005] | contains 0 | -0.001 | -0.012 | -0.002 | +0.001 | – |
| pretrained_frozen | readout | 86 | -0.013 | [-0.020, -0.005] | [-0.022, -0.004] | I<0 | -0.006 | -0.023 | -0.024 | -0.016 | – |
| pretrained_peft | readout | 86 | -0.080 | [-0.107, -0.053] | [-0.113, -0.047] | I<0 | -0.006 | -0.097 | -0.153 | -0.080 | – |
| pretrained_partial | readout | 86 | -0.013 | [-0.021, -0.004] | [-0.023, -0.002] | I<0 | -0.003 | -0.029 | -0.030 | -0.020 | – |
| pretrained_full | readout | 86 | -0.013 | [-0.021, -0.004] | [-0.023, -0.002] | I<0 | -0.003 | -0.030 | -0.030 | -0.020 | – |

**Federici · CS_SINGLE · cbramod** (family `B-READOUT|federici|CS_SINGLE|cbramod`, critical value 2.49)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 86 | +0.000 | [-0.004, +0.005] | [-0.005, +0.006] | contains 0 | +0.001 | -0.001 | -0.001 | -0.000 | – |
| pretrained_frozen | readout | 86 | +0.003 | [-0.003, +0.009] | [-0.004, +0.010] | contains 0 | +0.002 | -0.001 | +0.005 | -0.000 | – |
| pretrained_peft | readout | 86 | +0.001 | [-0.004, +0.007] | [-0.006, +0.008] | contains 0 | -0.003 | +0.002 | -0.001 | -0.000 | – |
| pretrained_partial | readout | 86 | +0.003 | [-0.002, +0.009] | [-0.003, +0.010] | contains 0 | -0.001 | +0.011 | -0.000 | +0.000 | – |
| pretrained_full | readout | 86 | -0.000 | [-0.006, +0.006] | [-0.008, +0.007] | contains 0 | -0.000 | -0.008 | -0.001 | +0.000 | – |

**Federici · CS_SINGLE · reve** (family `B-READOUT|federici|CS_SINGLE|reve`, critical value 2.63)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random_full | readout | 86 | +0.000 | [-0.004, +0.005] | [-0.005, +0.006] | contains 0 | +0.001 | -0.001 | -0.000 | +0.000 | – |
| pretrained_frozen | readout | 86 | +0.001 | [-0.004, +0.005] | [-0.006, +0.007] | contains 0 | -0.001 | +0.001 | -0.000 | +0.000 | – |
| pretrained_peft | readout | 86 | +0.001 | [-0.000, +0.003] | [-0.001, +0.004] | contains 0 | -0.001 | +0.009 | -0.000 | +0.000 | – |
| pretrained_partial | readout | 86 | +0.002 | [-0.000, +0.005] | [-0.001, +0.005] | contains 0 | -0.002 | +0.001 | +0.000 | +0.000 | – |
| pretrained_full | readout | 86 | +0.002 | [-0.001, +0.005] | [-0.002, +0.006] | contains 0 | -0.002 | +0.003 | +0.001 | +0.000 | – |

## 4. Initialization at fixed readout: `random_full` → `pretrained_*` (only `pretrained_full` is the matched-update initialization contrast; others are recipe contrasts)

**FAU · NCE · cbramod** (family `B-INIT|fau|NCE|cbramod`, critical value 2.52)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 67 | -0.006 | [-0.010, -0.003] | [-0.011, -0.002] | I<0 | -0.001 | -0.015 | -0.010 | -0.006 | -0.019 |
| channel_phase_linear/pretrained_peft | recipe | 67 | +0.001 | [-0.002, +0.004] | [-0.003, +0.005] | contains 0 | +0.000 | -0.002 | +0.000 | -0.004 | -0.011 |
| channel_phase_linear/pretrained_partial | recipe | 67 | -0.005 | [-0.009, -0.002] | [-0.009, -0.001] | I<0 | -0.002 | -0.015 | -0.010 | -0.005 | -0.017 |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 67 | -0.004 | [-0.007, -0.000] | [-0.008, +0.000] | contains 0 | -0.001 | -0.010 | -0.005 | -0.004 | -0.016 |
| dense_query/pretrained_frozen | recipe | 67 | +0.001 | [+0.001, +0.001] | [+0.000, +0.001] | I>0 | +0.000 | -0.000 | -0.000 | +0.000 | -0.007 |
| dense_query/pretrained_peft | recipe | 67 | +0.001 | [+0.000, +0.001] | [+0.000, +0.001] | I>0 | -0.000 | -0.001 | -0.000 | -0.000 | -0.011 |
| dense_query/pretrained_partial | recipe | 67 | +0.001 | [+0.000, +0.001] | [+0.000, +0.001] | I>0 | -0.000 | -0.001 | -0.000 | +0.000 | -0.003 |
| dense_query/pretrained_full | initialization (matched full update) | 67 | +0.001 | [+0.000, +0.001] | [+0.000, +0.001] | I>0 | -0.000 | -0.001 | -0.000 | -0.000 | +0.002 |

**FAU · NCE · reve** (family `B-INIT|fau|NCE|reve`, critical value 2.58)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 67 | +0.016 | [+0.010, +0.021] | [+0.009, +0.023] | I>0 | +0.002 | +0.015 | +0.031 | +0.020 | -0.003 |
| channel_phase_linear/pretrained_peft | recipe | 67 | +0.014 | [+0.007, +0.020] | [+0.005, +0.023] | I>0 | +0.003 | +0.014 | +0.029 | +0.032 | -0.006 |
| channel_phase_linear/pretrained_partial | recipe | 67 | +0.018 | [+0.012, +0.024] | [+0.010, +0.026] | I>0 | +0.002 | +0.016 | +0.034 | +0.026 | -0.003 |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 67 | +0.018 | [+0.012, +0.024] | [+0.010, +0.026] | I>0 | +0.002 | +0.016 | +0.034 | +0.027 | -0.002 |
| dense_query/pretrained_frozen | recipe | 67 | +0.001 | [+0.000, +0.001] | [+0.000, +0.001] | I>0 | +0.000 | +0.000 | +0.000 | +0.000 | -0.010 |
| dense_query/pretrained_peft | recipe | 67 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.001 | +0.000 | +0.000 | -0.011 |
| dense_query/pretrained_partial | recipe | 67 | +0.000 | [+0.000, +0.001] | [+0.000, +0.001] | I>0 | -0.000 | +0.001 | +0.000 | +0.000 | -0.009 |
| dense_query/pretrained_full | initialization (matched full update) | 67 | +0.000 | [+0.000, +0.001] | [+0.000, +0.001] | I>0 | -0.000 | +0.001 | +0.000 | +0.000 | -0.009 |

**FAU · CS_SINGLE · cbramod** (family `B-INIT|fau|CS_SINGLE|cbramod`, critical value 2.87)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 67 | -0.000 | [-0.001, +0.001] | [-0.002, +0.001] | contains 0 | +0.000 | -0.004 | -0.001 | -0.001 | -0.022 |
| channel_phase_linear/pretrained_peft | recipe | 67 | -0.001 | [-0.002, +0.001] | [-0.002, +0.001] | contains 0 | +0.001 | -0.002 | +0.001 | -0.001 | -0.012 |
| channel_phase_linear/pretrained_partial | recipe | 67 | +0.000 | [-0.001, +0.002] | [-0.001, +0.002] | contains 0 | -0.001 | -0.001 | +0.000 | -0.001 | -0.013 |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 67 | +0.001 | [-0.000, +0.002] | [-0.001, +0.003] | contains 0 | -0.001 | +0.001 | +0.001 | -0.001 | -0.015 |
| dense_query/pretrained_frozen | recipe | 67 | +0.000 | [-0.002, +0.002] | [-0.002, +0.002] | contains 0 | +0.002 | -0.000 | -0.001 | -0.000 | +0.002 |
| dense_query/pretrained_peft | recipe | 67 | -0.002 | [-0.004, +0.000] | [-0.005, +0.001] | contains 0 | +0.000 | +0.001 | -0.000 | -0.001 | -0.008 |
| dense_query/pretrained_partial | recipe | 67 | -0.001 | [-0.003, +0.000] | [-0.004, +0.001] | contains 0 | +0.002 | +0.001 | -0.000 | -0.001 | -0.006 |
| dense_query/pretrained_full | initialization (matched full update) | 67 | -0.000 | [-0.002, +0.001] | [-0.003, +0.002] | contains 0 | +0.001 | +0.002 | +0.000 | -0.001 | -0.013 |

**FAU · CS_SINGLE · reve** (family `B-INIT|fau|CS_SINGLE|reve`, critical value 2.68)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 67 | -0.001 | [-0.002, -0.001] | [-0.002, -0.001] | I<0 | +0.000 | +0.002 | +0.000 | -0.000 | -0.004 |
| channel_phase_linear/pretrained_peft | recipe | 67 | +0.000 | [-0.002, +0.003] | [-0.002, +0.003] | contains 0 | +0.001 | +0.008 | +0.005 | +0.003 | -0.005 |
| channel_phase_linear/pretrained_partial | recipe | 67 | -0.001 | [-0.002, -0.001] | [-0.002, -0.001] | I<0 | +0.000 | +0.002 | +0.000 | -0.000 | -0.001 |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 67 | -0.001 | [-0.002, -0.001] | [-0.002, -0.001] | I<0 | +0.000 | +0.002 | +0.000 | -0.000 | -0.001 |
| dense_query/pretrained_frozen | recipe | 67 | +0.001 | [-0.000, +0.002] | [-0.001, +0.003] | contains 0 | +0.001 | -0.001 | -0.001 | -0.000 | +0.007 |
| dense_query/pretrained_peft | recipe | 67 | +0.001 | [+0.000, +0.003] | [-0.000, +0.003] | contains 0 | +0.001 | -0.001 | -0.000 | -0.000 | +0.002 |
| dense_query/pretrained_partial | recipe | 67 | -0.001 | [-0.002, +0.001] | [-0.003, +0.001] | contains 0 | +0.001 | -0.001 | -0.001 | -0.001 | +0.005 |
| dense_query/pretrained_full | initialization (matched full update) | 67 | +0.001 | [+0.000, +0.002] | [-0.000, +0.003] | contains 0 | +0.001 | -0.000 | -0.000 | +0.000 | +0.008 |

**DTU · NCE · cbramod** (family `B-INIT|dtu|NCE|cbramod`, critical value 2.78)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 44 | -0.009 | [-0.017, -0.002] | [-0.019, +0.000] | contains 0 | +0.002 | -0.001 | +0.000 | -0.007 | +0.020 |
| channel_phase_linear/pretrained_peft | recipe | 44 | -0.005 | [-0.011, +0.001] | [-0.013, +0.003] | contains 0 | +0.001 | -0.010 | -0.010 | -0.010 | +0.006 |
| channel_phase_linear/pretrained_partial | recipe | 44 | -0.011 | [-0.018, -0.003] | [-0.021, +0.000] | contains 0 | +0.002 | -0.000 | +0.005 | -0.003 | +0.018 |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 44 | -0.003 | [-0.011, +0.004] | [-0.013, +0.007] | contains 0 | +0.001 | +0.001 | +0.004 | -0.005 | +0.016 |
| dense_query/pretrained_frozen | recipe | 44 | +0.009 | [+0.005, +0.014] | [+0.003, +0.015] | I>0 | +0.002 | -0.000 | -0.001 | -0.001 | -0.004 |
| dense_query/pretrained_peft | recipe | 44 | +0.005 | [-0.003, +0.012] | [-0.006, +0.015] | contains 0 | +0.002 | +0.000 | -0.001 | -0.002 | -0.000 |
| dense_query/pretrained_partial | recipe | 44 | +0.007 | [-0.001, +0.014] | [-0.003, +0.016] | contains 0 | +0.002 | +0.000 | -0.001 | -0.001 | -0.001 |
| dense_query/pretrained_full | initialization (matched full update) | 44 | +0.007 | [+0.003, +0.012] | [+0.001, +0.014] | I>0 | +0.001 | -0.001 | -0.002 | -0.000 | -0.005 |

**DTU · NCE · reve** (family `B-INIT|dtu|NCE|reve`, critical value 2.70)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 44 | +0.040 | [+0.030, +0.050] | [+0.026, +0.054] | I>0 | +0.001 | +0.025 | +0.057 | +0.025 | +0.015 |
| channel_phase_linear/pretrained_peft | recipe | 44 | +0.057 | [+0.040, +0.073] | [+0.035, +0.078] | I>0 | +0.004 | +0.035 | +0.095 | +0.065 | +0.026 |
| channel_phase_linear/pretrained_partial | recipe | 44 | +0.049 | [+0.038, +0.060] | [+0.034, +0.064] | I>0 | +0.003 | +0.031 | +0.078 | +0.041 | +0.020 |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 44 | +0.049 | [+0.038, +0.060] | [+0.034, +0.064] | I>0 | +0.003 | +0.031 | +0.078 | +0.041 | +0.021 |
| dense_query/pretrained_frozen | recipe | 44 | +0.017 | [+0.011, +0.023] | [+0.009, +0.025] | I>0 | -0.001 | +0.001 | +0.001 | -0.001 | +0.005 |
| dense_query/pretrained_peft | recipe | 44 | +0.011 | [+0.006, +0.015] | [+0.005, +0.017] | I>0 | +0.000 | -0.001 | +0.000 | -0.001 | +0.004 |
| dense_query/pretrained_partial | recipe | 44 | +0.018 | [+0.010, +0.025] | [+0.008, +0.027] | I>0 | -0.001 | -0.001 | -0.000 | -0.001 | -0.001 |
| dense_query/pretrained_full | initialization (matched full update) | 44 | +0.018 | [+0.010, +0.025] | [+0.008, +0.027] | I>0 | -0.001 | -0.001 | -0.000 | -0.001 | -0.001 |

**DTU · CS_SINGLE · cbramod** (family `B-INIT|dtu|CS_SINGLE|cbramod`, critical value 2.81)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 44 | -0.002 | [-0.007, +0.002] | [-0.009, +0.004] | contains 0 | +0.001 | -0.010 | -0.005 | -0.000 | +0.001 |
| channel_phase_linear/pretrained_peft | recipe | 44 | -0.005 | [-0.011, +0.000] | [-0.013, +0.002] | contains 0 | +0.001 | -0.011 | -0.004 | -0.000 | +0.004 |
| channel_phase_linear/pretrained_partial | recipe | 44 | -0.007 | [-0.012, -0.001] | [-0.014, +0.001] | contains 0 | -0.001 | -0.006 | -0.002 | -0.001 | +0.008 |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 44 | -0.002 | [-0.007, +0.003] | [-0.009, +0.006] | contains 0 | +0.000 | -0.000 | +0.001 | -0.001 | +0.005 |
| dense_query/pretrained_frozen | recipe | 44 | -0.004 | [-0.014, +0.005] | [-0.018, +0.009] | contains 0 | -0.001 | +0.005 | -0.002 | -0.000 | -0.005 |
| dense_query/pretrained_peft | recipe | 44 | +0.009 | [+0.002, +0.015] | [-0.000, +0.017] | contains 0 | -0.002 | +0.006 | +0.002 | +0.001 | +0.006 |
| dense_query/pretrained_partial | recipe | 44 | -0.001 | [-0.009, +0.007] | [-0.013, +0.011] | contains 0 | -0.002 | -0.002 | -0.003 | -0.002 | -0.004 |
| dense_query/pretrained_full | initialization (matched full update) | 44 | +0.007 | [-0.001, +0.015] | [-0.004, +0.018] | contains 0 | -0.002 | +0.003 | -0.004 | -0.001 | +0.001 |

**DTU · CS_SINGLE · reve** (family `B-INIT|dtu|CS_SINGLE|reve`, critical value 2.60)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 44 | +0.009 | [+0.001, +0.016] | [-0.001, +0.019] | contains 0 | -0.000 | +0.002 | +0.002 | +0.006 | +0.004 |
| channel_phase_linear/pretrained_peft | recipe | 44 | +0.004 | [-0.005, +0.013] | [-0.008, +0.016] | contains 0 | +0.000 | +0.004 | +0.003 | +0.003 | -0.001 |
| channel_phase_linear/pretrained_partial | recipe | 44 | +0.010 | [+0.003, +0.018] | [+0.000, +0.020] | I>0 | -0.000 | +0.001 | +0.001 | +0.006 | +0.006 |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 44 | +0.010 | [+0.003, +0.018] | [+0.000, +0.020] | I>0 | -0.000 | +0.001 | +0.001 | +0.006 | +0.006 |
| dense_query/pretrained_frozen | recipe | 44 | -0.005 | [-0.012, +0.002] | [-0.014, +0.003] | contains 0 | +0.002 | +0.001 | +0.002 | -0.005 | -0.004 |
| dense_query/pretrained_peft | recipe | 44 | +0.000 | [-0.008, +0.009] | [-0.010, +0.011] | contains 0 | +0.000 | -0.003 | +0.002 | -0.005 | -0.002 |
| dense_query/pretrained_partial | recipe | 44 | -0.000 | [-0.006, +0.006] | [-0.008, +0.008] | contains 0 | +0.001 | -0.000 | +0.002 | -0.005 | -0.005 |
| dense_query/pretrained_full | initialization (matched full update) | 44 | -0.000 | [-0.006, +0.006] | [-0.008, +0.008] | contains 0 | +0.001 | -0.000 | +0.002 | -0.005 | -0.005 |

**Federici · NCE · cbramod** (family `B-INIT|federici|NCE|cbramod`, critical value 2.58)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 86 | -0.001 | [-0.006, +0.004] | [-0.007, +0.005] | contains 0 | +0.001 | +0.001 | -0.002 | +0.000 | – |
| channel_phase_linear/pretrained_peft | recipe | 86 | +0.002 | [-0.004, +0.007] | [-0.005, +0.009] | contains 0 | +0.001 | +0.001 | -0.003 | +0.001 | – |
| channel_phase_linear/pretrained_partial | recipe | 86 | +0.003 | [-0.002, +0.007] | [-0.003, +0.009] | contains 0 | +0.003 | +0.005 | -0.002 | +0.001 | – |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 86 | +0.004 | [-0.002, +0.009] | [-0.003, +0.010] | contains 0 | +0.004 | +0.008 | -0.002 | +0.001 | – |
| dense_query/pretrained_frozen | recipe | 86 | +0.001 | [-0.002, +0.004] | [-0.003, +0.005] | contains 0 | -0.000 | -0.007 | -0.000 | +0.000 | – |
| dense_query/pretrained_peft | recipe | 86 | +0.002 | [-0.002, +0.005] | [-0.003, +0.006] | contains 0 | -0.002 | -0.008 | -0.000 | +0.000 | – |
| dense_query/pretrained_partial | recipe | 86 | +0.001 | [-0.002, +0.004] | [-0.003, +0.005] | contains 0 | -0.002 | -0.005 | -0.000 | +0.000 | – |
| dense_query/pretrained_full | initialization (matched full update) | 86 | +0.000 | [-0.003, +0.004] | [-0.003, +0.004] | contains 0 | -0.001 | -0.012 | -0.000 | -0.001 | – |

**Federici · NCE · reve** (family `B-INIT|federici|NCE|reve`, critical value 2.81)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 86 | +0.014 | [+0.007, +0.020] | [+0.004, +0.023] | I>0 | +0.002 | +0.018 | +0.023 | +0.011 | – |
| channel_phase_linear/pretrained_peft | recipe | 86 | +0.074 | [+0.049, +0.100] | [+0.037, +0.111] | I>0 | +0.005 | +0.083 | +0.145 | +0.074 | – |
| channel_phase_linear/pretrained_partial | recipe | 86 | +0.014 | [+0.006, +0.022] | [+0.003, +0.026] | I>0 | +0.002 | +0.020 | +0.028 | +0.019 | – |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 86 | +0.014 | [+0.006, +0.022] | [+0.003, +0.026] | I>0 | +0.002 | +0.020 | +0.028 | +0.019 | – |
| dense_query/pretrained_frozen | recipe | 86 | +0.002 | [-0.003, +0.006] | [-0.004, +0.007] | contains 0 | -0.002 | +0.007 | +0.000 | -0.005 | – |
| dense_query/pretrained_peft | recipe | 86 | -0.005 | [-0.010, +0.000] | [-0.012, +0.002] | contains 0 | -0.000 | -0.003 | -0.006 | -0.007 | – |
| dense_query/pretrained_partial | recipe | 86 | +0.003 | [-0.000, +0.005] | [-0.001, +0.006] | contains 0 | +0.000 | +0.002 | -0.001 | -0.003 | – |
| dense_query/pretrained_full | initialization (matched full update) | 86 | +0.003 | [-0.000, +0.005] | [-0.001, +0.006] | contains 0 | +0.000 | +0.002 | -0.001 | -0.003 | – |

**Federici · CS_SINGLE · cbramod** (family `B-INIT|federici|CS_SINGLE|cbramod`, critical value 2.77)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 86 | -0.001 | [-0.005, +0.002] | [-0.006, +0.003] | contains 0 | +0.001 | +0.004 | -0.002 | +0.000 | – |
| channel_phase_linear/pretrained_peft | recipe | 86 | -0.001 | [-0.003, +0.001] | [-0.004, +0.002] | contains 0 | +0.000 | -0.001 | -0.000 | -0.000 | – |
| channel_phase_linear/pretrained_partial | recipe | 86 | -0.001 | [-0.004, +0.001] | [-0.004, +0.002] | contains 0 | +0.001 | +0.000 | -0.000 | -0.000 | – |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 86 | -0.001 | [-0.003, +0.001] | [-0.004, +0.002] | contains 0 | +0.000 | +0.006 | +0.000 | +0.000 | – |
| dense_query/pretrained_frozen | recipe | 86 | +0.002 | [-0.002, +0.005] | [-0.003, +0.006] | contains 0 | +0.002 | +0.004 | +0.004 | +0.000 | – |
| dense_query/pretrained_peft | recipe | 86 | -0.000 | [-0.003, +0.003] | [-0.005, +0.005] | contains 0 | -0.004 | +0.002 | -0.001 | +0.000 | – |
| dense_query/pretrained_partial | recipe | 86 | +0.002 | [-0.002, +0.005] | [-0.003, +0.006] | contains 0 | -0.001 | +0.012 | +0.000 | +0.000 | – |
| dense_query/pretrained_full | initialization (matched full update) | 86 | -0.001 | [-0.006, +0.003] | [-0.008, +0.005] | contains 0 | -0.001 | -0.001 | -0.000 | +0.000 | – |

**Federici · CS_SINGLE · reve** (family `B-INIT|federici|CS_SINGLE|reve`, critical value 2.87)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_frozen | recipe | 86 | +0.001 | [-0.000, +0.003] | [-0.001, +0.004] | contains 0 | +0.000 | -0.000 | -0.001 | -0.000 | – |
| channel_phase_linear/pretrained_peft | recipe | 86 | +0.002 | [-0.000, +0.004] | [-0.001, +0.005] | contains 0 | -0.000 | -0.007 | -0.001 | -0.000 | – |
| channel_phase_linear/pretrained_partial | recipe | 86 | +0.001 | [-0.000, +0.003] | [-0.001, +0.004] | contains 0 | +0.000 | -0.000 | -0.001 | -0.000 | – |
| channel_phase_linear/pretrained_full | initialization (matched full update) | 86 | +0.001 | [-0.000, +0.003] | [-0.001, +0.004] | contains 0 | +0.000 | -0.000 | -0.001 | -0.000 | – |
| dense_query/pretrained_frozen | recipe | 86 | +0.002 | [-0.004, +0.007] | [-0.007, +0.010] | contains 0 | -0.002 | +0.002 | -0.001 | -0.000 | – |
| dense_query/pretrained_peft | recipe | 86 | +0.003 | [-0.001, +0.006] | [-0.002, +0.008] | contains 0 | -0.002 | +0.003 | -0.001 | +0.000 | – |
| dense_query/pretrained_partial | recipe | 86 | +0.003 | [-0.000, +0.006] | [-0.002, +0.008] | contains 0 | -0.003 | +0.002 | -0.000 | +0.000 | – |
| dense_query/pretrained_full | initialization (matched full update) | 86 | +0.003 | [-0.001, +0.007] | [-0.002, +0.008] | contains 0 | -0.002 | +0.004 | +0.001 | +0.000 | – |

## 5. Adaptation at fixed initialization: `pretrained_frozen` → `pretrained_{peft, partial, full}`

**FAU · NCE · cbramod** (family `B-ADAPT|fau|NCE|cbramod`, critical value 2.59)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 67 | +0.008 | [+0.005, +0.010] | [+0.004, +0.011] | I>0 | +0.001 | +0.013 | +0.010 | +0.002 | +0.008 |
| channel_phase_linear/pretrained_partial | adaptation | 67 | +0.001 | [-0.001, +0.003] | [-0.001, +0.003] | contains 0 | -0.001 | +0.000 | -0.000 | +0.000 | +0.001 |
| channel_phase_linear/pretrained_full | adaptation | 67 | +0.003 | [+0.000, +0.005] | [-0.001, +0.006] | contains 0 | -0.000 | +0.006 | +0.006 | +0.001 | +0.003 |
| dense_query/pretrained_peft | adaptation | 67 | -0.000 | [-0.000, -0.000] | [-0.000, -0.000] | I<0 | -0.000 | -0.000 | -0.000 | -0.000 | -0.004 |
| dense_query/pretrained_partial | adaptation | 67 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | -0.000 | -0.000 | -0.000 | -0.000 | +0.004 |
| dense_query/pretrained_full | adaptation | 67 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | -0.000 | -0.000 | -0.000 | -0.000 | +0.009 |

**FAU · NCE · reve** (family `B-ADAPT|fau|NCE|reve`, critical value 2.64)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 67 | -0.002 | [-0.006, +0.002] | [-0.008, +0.004] | contains 0 | +0.000 | -0.000 | -0.002 | +0.012 | -0.003 |
| channel_phase_linear/pretrained_partial | adaptation | 67 | +0.002 | [+0.001, +0.003] | [+0.000, +0.003] | I>0 | -0.000 | +0.001 | +0.003 | +0.006 | +0.000 |
| channel_phase_linear/pretrained_full | adaptation | 67 | +0.002 | [+0.001, +0.003] | [+0.001, +0.004] | I>0 | -0.000 | +0.001 | +0.003 | +0.007 | +0.001 |
| dense_query/pretrained_peft | adaptation | 67 | -0.001 | [-0.001, -0.000] | [-0.001, -0.000] | I<0 | +0.000 | +0.000 | +0.000 | +0.000 | -0.002 |
| dense_query/pretrained_partial | adaptation | 67 | -0.000 | [-0.000, -0.000] | [-0.000, +0.000] | contains 0 | -0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| dense_query/pretrained_full | adaptation | 67 | -0.000 | [-0.000, -0.000] | [-0.000, +0.000] | contains 0 | -0.000 | +0.000 | +0.000 | +0.000 | +0.000 |

**FAU · CS_SINGLE · cbramod** (family `B-ADAPT|fau|CS_SINGLE|cbramod`, critical value 2.80)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 67 | -0.000 | [-0.001, +0.001] | [-0.002, +0.001] | contains 0 | +0.001 | +0.002 | +0.002 | -0.000 | +0.009 |
| channel_phase_linear/pretrained_partial | adaptation | 67 | +0.001 | [-0.000, +0.001] | [-0.001, +0.002] | contains 0 | -0.001 | +0.002 | +0.001 | -0.000 | +0.008 |
| channel_phase_linear/pretrained_full | adaptation | 67 | +0.001 | [+0.000, +0.002] | [-0.000, +0.002] | contains 0 | -0.001 | +0.005 | +0.002 | -0.000 | +0.007 |
| dense_query/pretrained_peft | adaptation | 67 | -0.002 | [-0.003, -0.000] | [-0.004, +0.000] | contains 0 | -0.001 | +0.001 | +0.001 | -0.001 | -0.010 |
| dense_query/pretrained_partial | adaptation | 67 | -0.001 | [-0.003, +0.000] | [-0.003, +0.001] | contains 0 | -0.000 | +0.001 | +0.001 | -0.001 | -0.008 |
| dense_query/pretrained_full | adaptation | 67 | -0.000 | [-0.002, +0.001] | [-0.002, +0.001] | contains 0 | -0.001 | +0.002 | +0.001 | -0.000 | -0.015 |

**FAU · CS_SINGLE · reve** (family `B-ADAPT|fau|CS_SINGLE|reve`, critical value 2.59)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 67 | +0.002 | [-0.000, +0.004] | [-0.001, +0.005] | contains 0 | +0.001 | +0.007 | +0.005 | +0.004 | -0.001 |
| channel_phase_linear/pretrained_partial | adaptation | 67 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.000 | +0.000 | -0.000 | +0.003 |
| channel_phase_linear/pretrained_full | adaptation | 67 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.000 | +0.000 | -0.000 | +0.003 |
| dense_query/pretrained_peft | adaptation | 67 | +0.000 | [-0.000, +0.001] | [-0.000, +0.001] | contains 0 | +0.000 | +0.000 | +0.000 | +0.000 | -0.005 |
| dense_query/pretrained_partial | adaptation | 67 | -0.002 | [-0.003, -0.000] | [-0.003, -0.000] | I<0 | +0.000 | +0.000 | -0.000 | -0.000 | -0.002 |
| dense_query/pretrained_full | adaptation | 67 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | +0.001 | +0.000 | +0.001 | +0.001 |

**DTU · NCE · cbramod** (family `B-ADAPT|dtu|NCE|cbramod`, critical value 2.85)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 44 | +0.005 | [-0.001, +0.011] | [-0.004, +0.013] | contains 0 | -0.001 | -0.009 | -0.010 | -0.003 | -0.014 |
| channel_phase_linear/pretrained_partial | adaptation | 44 | -0.001 | [-0.006, +0.004] | [-0.008, +0.006] | contains 0 | -0.001 | +0.001 | +0.005 | +0.004 | -0.001 |
| channel_phase_linear/pretrained_full | adaptation | 44 | +0.006 | [+0.001, +0.011] | [-0.001, +0.014] | contains 0 | -0.002 | +0.003 | +0.004 | +0.002 | -0.004 |
| dense_query/pretrained_peft | adaptation | 44 | -0.004 | [-0.010, +0.001] | [-0.012, +0.003] | contains 0 | -0.000 | +0.001 | +0.000 | -0.001 | +0.004 |
| dense_query/pretrained_partial | adaptation | 44 | -0.002 | [-0.006, +0.001] | [-0.007, +0.002] | contains 0 | -0.000 | +0.001 | +0.000 | -0.000 | +0.003 |
| dense_query/pretrained_full | adaptation | 44 | -0.002 | [-0.003, -0.000] | [-0.004, +0.000] | contains 0 | -0.001 | -0.001 | -0.000 | +0.000 | -0.000 |

**DTU · NCE · reve** (family `B-ADAPT|dtu|NCE|reve`, critical value 2.63)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 44 | +0.017 | [+0.004, +0.029] | [-0.000, +0.034] | contains 0 | +0.003 | +0.010 | +0.038 | +0.040 | +0.012 |
| channel_phase_linear/pretrained_partial | adaptation | 44 | +0.009 | [+0.005, +0.013] | [+0.004, +0.014] | I>0 | +0.001 | +0.007 | +0.022 | +0.016 | +0.006 |
| channel_phase_linear/pretrained_full | adaptation | 44 | +0.009 | [+0.005, +0.013] | [+0.004, +0.014] | I>0 | +0.001 | +0.007 | +0.022 | +0.016 | +0.006 |
| dense_query/pretrained_peft | adaptation | 44 | -0.006 | [-0.009, -0.003] | [-0.010, -0.002] | I<0 | +0.001 | -0.003 | -0.001 | +0.001 | -0.001 |
| dense_query/pretrained_partial | adaptation | 44 | +0.001 | [-0.002, +0.003] | [-0.002, +0.004] | contains 0 | -0.000 | -0.003 | -0.001 | +0.000 | -0.006 |
| dense_query/pretrained_full | adaptation | 44 | +0.001 | [-0.002, +0.003] | [-0.002, +0.004] | contains 0 | -0.000 | -0.003 | -0.001 | +0.000 | -0.006 |

**DTU · CS_SINGLE · cbramod** (family `B-ADAPT|dtu|CS_SINGLE|cbramod`, critical value 2.71)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 44 | -0.003 | [-0.007, +0.001] | [-0.009, +0.003] | contains 0 | +0.000 | -0.001 | +0.002 | +0.000 | +0.004 |
| channel_phase_linear/pretrained_partial | adaptation | 44 | -0.004 | [-0.008, -0.001] | [-0.009, +0.000] | contains 0 | -0.002 | +0.004 | +0.003 | -0.000 | +0.007 |
| channel_phase_linear/pretrained_full | adaptation | 44 | +0.001 | [-0.005, +0.006] | [-0.007, +0.008] | contains 0 | -0.001 | +0.009 | +0.007 | -0.001 | +0.004 |
| dense_query/pretrained_peft | adaptation | 44 | +0.013 | [+0.004, +0.022] | [+0.001, +0.025] | I>0 | -0.001 | +0.001 | +0.003 | +0.001 | +0.011 |
| dense_query/pretrained_partial | adaptation | 44 | +0.004 | [-0.005, +0.012] | [-0.008, +0.015] | contains 0 | -0.001 | -0.007 | -0.001 | -0.001 | +0.001 |
| dense_query/pretrained_full | adaptation | 44 | +0.011 | [+0.002, +0.021] | [-0.002, +0.024] | contains 0 | -0.001 | -0.002 | -0.003 | -0.001 | +0.006 |

**DTU · CS_SINGLE · reve** (family `B-ADAPT|dtu|CS_SINGLE|reve`, critical value 2.90)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 44 | -0.005 | [-0.010, +0.001] | [-0.012, +0.003] | contains 0 | +0.000 | +0.002 | +0.001 | -0.002 | -0.005 |
| channel_phase_linear/pretrained_partial | adaptation | 44 | +0.001 | [-0.000, +0.003] | [-0.001, +0.004] | contains 0 | +0.000 | -0.000 | -0.000 | -0.000 | +0.002 |
| channel_phase_linear/pretrained_full | adaptation | 44 | +0.001 | [-0.000, +0.003] | [-0.001, +0.004] | contains 0 | +0.000 | -0.000 | -0.000 | -0.000 | +0.002 |
| dense_query/pretrained_peft | adaptation | 44 | +0.006 | [-0.005, +0.016] | [-0.010, +0.021] | contains 0 | -0.001 | -0.004 | +0.000 | +0.000 | +0.001 |
| dense_query/pretrained_partial | adaptation | 44 | +0.005 | [+0.001, +0.009] | [-0.001, +0.011] | contains 0 | -0.001 | -0.001 | +0.000 | -0.000 | -0.002 |
| dense_query/pretrained_full | adaptation | 44 | +0.005 | [+0.001, +0.009] | [-0.001, +0.011] | contains 0 | -0.001 | -0.001 | +0.000 | -0.000 | -0.001 |

**Federici · NCE · cbramod** (family `B-ADAPT|federici|NCE|cbramod`, critical value 2.66)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 86 | +0.003 | [-0.001, +0.007] | [-0.002, +0.008] | contains 0 | +0.000 | +0.000 | -0.001 | +0.001 | – |
| channel_phase_linear/pretrained_partial | adaptation | 86 | +0.004 | [+0.001, +0.007] | [-0.000, +0.008] | contains 0 | +0.002 | +0.004 | +0.000 | +0.000 | – |
| channel_phase_linear/pretrained_full | adaptation | 86 | +0.005 | [+0.001, +0.009] | [+0.000, +0.009] | I>0 | +0.003 | +0.007 | +0.000 | +0.000 | – |
| dense_query/pretrained_peft | adaptation | 86 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | -0.002 | -0.001 | -0.000 | +0.000 | – |
| dense_query/pretrained_partial | adaptation | 86 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.002 | +0.002 | -0.000 | +0.000 | – |
| dense_query/pretrained_full | adaptation | 86 | -0.001 | [-0.002, +0.000] | [-0.002, +0.001] | contains 0 | -0.001 | -0.005 | -0.000 | -0.001 | – |

**Federici · NCE · reve** (family `B-ADAPT|federici|NCE|reve`, critical value 2.57)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 86 | +0.061 | [+0.038, +0.084] | [+0.030, +0.091] | I>0 | +0.003 | +0.064 | +0.122 | +0.063 | – |
| channel_phase_linear/pretrained_partial | adaptation | 86 | +0.001 | [-0.001, +0.003] | [-0.002, +0.003] | contains 0 | +0.000 | +0.002 | +0.005 | +0.007 | – |
| channel_phase_linear/pretrained_full | adaptation | 86 | +0.001 | [-0.001, +0.003] | [-0.002, +0.003] | contains 0 | +0.000 | +0.002 | +0.005 | +0.007 | – |
| dense_query/pretrained_peft | adaptation | 86 | -0.006 | [-0.012, -0.001] | [-0.013, +0.001] | contains 0 | +0.002 | -0.010 | -0.006 | -0.001 | – |
| dense_query/pretrained_partial | adaptation | 86 | +0.001 | [-0.002, +0.004] | [-0.003, +0.005] | contains 0 | +0.003 | -0.005 | -0.001 | +0.003 | – |
| dense_query/pretrained_full | adaptation | 86 | +0.001 | [-0.002, +0.004] | [-0.003, +0.005] | contains 0 | +0.003 | -0.005 | -0.001 | +0.003 | – |

**Federici · CS_SINGLE · cbramod** (family `B-ADAPT|federici|CS_SINGLE|cbramod`, critical value 2.60)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 86 | +0.000 | [-0.002, +0.003] | [-0.003, +0.003] | contains 0 | -0.001 | -0.005 | +0.002 | -0.000 | – |
| channel_phase_linear/pretrained_partial | adaptation | 86 | -0.000 | [-0.002, +0.002] | [-0.003, +0.003] | contains 0 | -0.000 | -0.004 | +0.001 | -0.000 | – |
| channel_phase_linear/pretrained_full | adaptation | 86 | +0.000 | [-0.002, +0.003] | [-0.003, +0.003] | contains 0 | -0.000 | +0.002 | +0.002 | -0.000 | – |
| dense_query/pretrained_peft | adaptation | 86 | -0.002 | [-0.005, +0.001] | [-0.006, +0.002] | contains 0 | -0.005 | -0.002 | -0.004 | -0.000 | – |
| dense_query/pretrained_partial | adaptation | 86 | +0.000 | [-0.003, +0.003] | [-0.004, +0.004] | contains 0 | -0.003 | +0.008 | -0.003 | +0.000 | – |
| dense_query/pretrained_full | adaptation | 86 | -0.003 | [-0.007, +0.001] | [-0.008, +0.002] | contains 0 | -0.003 | -0.005 | -0.004 | +0.000 | – |

**Federici · CS_SINGLE · reve** (family `B-ADAPT|federici|CS_SINGLE|reve`, critical value 2.67)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/pretrained_peft | adaptation | 86 | +0.001 | [-0.001, +0.002] | [-0.001, +0.002] | contains 0 | -0.000 | -0.007 | +0.000 | -0.000 | – |
| channel_phase_linear/pretrained_partial | adaptation | 86 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.000 | +0.000 | -0.000 | – |
| channel_phase_linear/pretrained_full | adaptation | 86 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.000 | +0.000 | -0.000 | – |
| dense_query/pretrained_peft | adaptation | 86 | +0.001 | [-0.003, +0.006] | [-0.005, +0.007] | contains 0 | -0.001 | +0.000 | +0.000 | +0.000 | – |
| dense_query/pretrained_partial | adaptation | 86 | +0.002 | [-0.003, +0.006] | [-0.004, +0.007] | contains 0 | -0.001 | -0.000 | +0.000 | +0.000 | – |
| dense_query/pretrained_full | adaptation | 86 | +0.001 | [-0.003, +0.006] | [-0.004, +0.007] | contains 0 | -0.001 | +0.001 | +0.002 | +0.000 | – |

## 6. Foundation dense readout vs the local model (same dense task): local → B configuration

**FAU · NCE · cbramod** (family `B-LOCAL|fau|NCE|cbramod`, critical value 2.09)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 67 | -0.376 | [-0.500, -0.252] | [-0.501, -0.251] | I<0 | -0.054 | -0.171 | -1.029 | -0.682 | -0.027 |
| channel_phase_linear/pretrained_frozen | vs local | 67 | -0.382 | [-0.507, -0.257] | [-0.508, -0.256] | I<0 | -0.054 | -0.187 | -1.039 | -0.687 | -0.045 |
| channel_phase_linear/pretrained_peft | vs local | 67 | -0.375 | [-0.499, -0.250] | [-0.500, -0.249] | I<0 | -0.053 | -0.173 | -1.028 | -0.686 | -0.037 |
| channel_phase_linear/pretrained_partial | vs local | 67 | -0.381 | [-0.506, -0.256] | [-0.507, -0.255] | I<0 | -0.055 | -0.186 | -1.039 | -0.687 | -0.044 |
| channel_phase_linear/pretrained_full | vs local | 67 | -0.380 | [-0.504, -0.255] | [-0.505, -0.254] | I<0 | -0.055 | -0.181 | -1.033 | -0.686 | -0.042 |
| dense_query/random_full | vs local | 67 | -0.383 | [-0.509, -0.258] | [-0.510, -0.257] | I<0 | -0.056 | -0.198 | -1.044 | -0.687 | -0.054 |
| dense_query/pretrained_frozen | vs local | 67 | -0.383 | [-0.508, -0.257] | [-0.509, -0.256] | I<0 | -0.056 | -0.198 | -1.044 | -0.687 | -0.061 |
| dense_query/pretrained_peft | vs local | 67 | -0.383 | [-0.508, -0.257] | [-0.509, -0.256] | I<0 | -0.056 | -0.198 | -1.044 | -0.687 | -0.065 |
| dense_query/pretrained_partial | vs local | 67 | -0.383 | [-0.508, -0.257] | [-0.509, -0.256] | I<0 | -0.056 | -0.198 | -1.044 | -0.687 | -0.057 |
| dense_query/pretrained_full | vs local | 67 | -0.383 | [-0.508, -0.257] | [-0.509, -0.256] | I<0 | -0.056 | -0.198 | -1.044 | -0.687 | -0.052 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | ci | ha | th |
|---|---|---|---|
| channel_phase_linear/random_full | +0.004 [-0.195, +0.203] (n=24) | -0.629 [-0.751, -0.507] (n=29) | -0.503 [-0.739, -0.268] (n=14) |
| channel_phase_linear/pretrained_frozen | +0.000 [-0.202, +0.202] (n=24) | -0.634 [-0.764, -0.505] (n=29) | -0.516 [-0.754, -0.278] (n=14) |
| channel_phase_linear/pretrained_peft | +0.005 [-0.195, +0.205] (n=24) | -0.625 [-0.751, -0.499] (n=29) | -0.506 [-0.746, -0.267] (n=14) |
| channel_phase_linear/pretrained_partial | +0.001 [-0.201, +0.203] (n=24) | -0.633 [-0.762, -0.503] (n=29) | -0.516 [-0.753, -0.278] (n=14) |
| channel_phase_linear/pretrained_full | +0.001 [-0.203, +0.205] (n=24) | -0.630 [-0.757, -0.503] (n=29) | -0.512 [-0.744, -0.281] (n=14) |
| dense_query/random_full | +0.000 [-0.211, +0.212] (n=24) | -0.636 [-0.762, -0.509] (n=29) | -0.518 [-0.753, -0.283] (n=14) |
| dense_query/pretrained_frozen | +0.001 [-0.199, +0.201] (n=24) | -0.635 [-0.765, -0.505] (n=29) | -0.517 [-0.744, -0.290] (n=14) |
| dense_query/pretrained_peft | +0.001 [-0.203, +0.205] (n=24) | -0.635 [-0.766, -0.504] (n=29) | -0.517 [-0.753, -0.282] (n=14) |
| dense_query/pretrained_partial | +0.001 [-0.206, +0.208] (n=24) | -0.635 [-0.766, -0.505] (n=29) | -0.517 [-0.753, -0.282] (n=14) |
| dense_query/pretrained_full | +0.001 [-0.206, +0.208] (n=24) | -0.635 [-0.766, -0.504] (n=29) | -0.517 [-0.748, -0.286] (n=14) |

**FAU · NCE · reve** (family `B-LOCAL|fau|NCE|reve`, critical value 2.01)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 67 | -0.364 | [-0.480, -0.248] | [-0.482, -0.246] | I<0 | -0.052 | -0.151 | -1.010 | -0.674 | -0.030 |
| channel_phase_linear/pretrained_frozen | vs local | 67 | -0.348 | [-0.461, -0.235] | [-0.463, -0.233] | I<0 | -0.050 | -0.136 | -0.979 | -0.654 | -0.033 |
| channel_phase_linear/pretrained_peft | vs local | 67 | -0.350 | [-0.463, -0.237] | [-0.466, -0.235] | I<0 | -0.049 | -0.137 | -0.981 | -0.642 | -0.036 |
| channel_phase_linear/pretrained_partial | vs local | 67 | -0.346 | [-0.459, -0.233] | [-0.461, -0.231] | I<0 | -0.050 | -0.135 | -0.976 | -0.648 | -0.033 |
| channel_phase_linear/pretrained_full | vs local | 67 | -0.346 | [-0.459, -0.233] | [-0.461, -0.231] | I<0 | -0.050 | -0.135 | -0.976 | -0.647 | -0.032 |
| dense_query/random_full | vs local | 67 | -0.383 | [-0.503, -0.263] | [-0.504, -0.261] | I<0 | -0.056 | -0.198 | -1.044 | -0.687 | -0.052 |
| dense_query/pretrained_frozen | vs local | 67 | -0.382 | [-0.502, -0.263] | [-0.504, -0.261] | I<0 | -0.056 | -0.198 | -1.044 | -0.687 | -0.062 |
| dense_query/pretrained_peft | vs local | 67 | -0.383 | [-0.503, -0.263] | [-0.504, -0.261] | I<0 | -0.056 | -0.198 | -1.044 | -0.687 | -0.064 |
| dense_query/pretrained_partial | vs local | 67 | -0.382 | [-0.502, -0.263] | [-0.504, -0.261] | I<0 | -0.056 | -0.198 | -1.044 | -0.687 | -0.062 |
| dense_query/pretrained_full | vs local | 67 | -0.382 | [-0.502, -0.263] | [-0.504, -0.261] | I<0 | -0.056 | -0.198 | -1.044 | -0.687 | -0.062 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | ci | ha | th |
|---|---|---|---|
| channel_phase_linear/random_full | +0.014 [-0.177, +0.205] (n=24) | -0.617 [-0.744, -0.490] (n=29) | -0.488 [-0.714, -0.262] (n=14) |
| channel_phase_linear/pretrained_frozen | +0.020 [-0.174, +0.214] (n=24) | -0.595 [-0.715, -0.475] (n=29) | -0.468 [-0.683, -0.252] (n=14) |
| channel_phase_linear/pretrained_peft | +0.018 [-0.179, +0.215] (n=24) | -0.601 [-0.719, -0.482] (n=29) | -0.462 [-0.684, -0.241] (n=14) |
| channel_phase_linear/pretrained_partial | +0.021 [-0.176, +0.218] (n=24) | -0.593 [-0.714, -0.471] (n=29) | -0.464 [-0.680, -0.248] (n=14) |
| channel_phase_linear/pretrained_full | +0.021 [-0.172, +0.214] (n=24) | -0.593 [-0.713, -0.472] (n=29) | -0.463 [-0.690, -0.237] (n=14) |
| dense_query/random_full | +0.001 [-0.199, +0.200] (n=24) | -0.635 [-0.767, -0.503] (n=29) | -0.518 [-0.752, -0.283] (n=14) |
| dense_query/pretrained_frozen | +0.001 [-0.201, +0.203] (n=24) | -0.635 [-0.765, -0.504] (n=29) | -0.517 [-0.753, -0.281] (n=14) |
| dense_query/pretrained_peft | +0.001 [-0.207, +0.209] (n=24) | -0.635 [-0.762, -0.509] (n=29) | -0.518 [-0.750, -0.285] (n=14) |
| dense_query/pretrained_partial | +0.001 [-0.203, +0.205] (n=24) | -0.635 [-0.762, -0.508] (n=29) | -0.517 [-0.751, -0.284] (n=14) |
| dense_query/pretrained_full | +0.001 [-0.202, +0.205] (n=24) | -0.635 [-0.765, -0.505] (n=29) | -0.517 [-0.760, -0.275] (n=14) |

**FAU · CS_SINGLE · cbramod** (family `B-LOCAL|fau|CS_SINGLE|cbramod`, critical value 1.99)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 67 | -0.333 | [-0.412, -0.254] | [-0.413, -0.254] | I<0 | -0.044 | -0.176 | -0.723 | -0.352 | -0.038 |
| channel_phase_linear/pretrained_frozen | vs local | 67 | -0.333 | [-0.412, -0.254] | [-0.413, -0.253] | I<0 | -0.044 | -0.180 | -0.724 | -0.353 | -0.060 |
| channel_phase_linear/pretrained_peft | vs local | 67 | -0.334 | [-0.413, -0.254] | [-0.413, -0.254] | I<0 | -0.043 | -0.178 | -0.722 | -0.353 | -0.050 |
| channel_phase_linear/pretrained_partial | vs local | 67 | -0.333 | [-0.412, -0.253] | [-0.413, -0.253] | I<0 | -0.045 | -0.178 | -0.723 | -0.353 | -0.052 |
| channel_phase_linear/pretrained_full | vs local | 67 | -0.332 | [-0.412, -0.253] | [-0.412, -0.253] | I<0 | -0.044 | -0.175 | -0.722 | -0.353 | -0.053 |
| dense_query/random_full | vs local | 67 | -0.335 | [-0.414, -0.256] | [-0.415, -0.255] | I<0 | -0.045 | -0.184 | -0.724 | -0.353 | -0.022 |
| dense_query/pretrained_frozen | vs local | 67 | -0.335 | [-0.414, -0.255] | [-0.415, -0.255] | I<0 | -0.043 | -0.185 | -0.725 | -0.353 | -0.020 |
| dense_query/pretrained_peft | vs local | 67 | -0.337 | [-0.416, -0.257] | [-0.416, -0.257] | I<0 | -0.044 | -0.184 | -0.724 | -0.354 | -0.030 |
| dense_query/pretrained_partial | vs local | 67 | -0.336 | [-0.415, -0.257] | [-0.416, -0.256] | I<0 | -0.043 | -0.183 | -0.725 | -0.354 | -0.027 |
| dense_query/pretrained_full | vs local | 67 | -0.335 | [-0.414, -0.256] | [-0.415, -0.256] | I<0 | -0.044 | -0.183 | -0.724 | -0.353 | -0.034 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | ci | ha | th |
|---|---|---|---|
| channel_phase_linear/random_full | -0.097 [-0.240, +0.046] (n=24) | -0.482 [-0.574, -0.390] (n=29) | -0.430 [-0.577, -0.282] (n=14) |
| channel_phase_linear/pretrained_frozen | -0.096 [-0.238, +0.046] (n=24) | -0.483 [-0.576, -0.390] (n=29) | -0.430 [-0.587, -0.274] (n=14) |
| channel_phase_linear/pretrained_peft | -0.097 [-0.235, +0.041] (n=24) | -0.482 [-0.573, -0.391] (n=29) | -0.432 [-0.585, -0.278] (n=14) |
| channel_phase_linear/pretrained_partial | -0.096 [-0.233, +0.042] (n=24) | -0.482 [-0.575, -0.390] (n=29) | -0.429 [-0.579, -0.279] (n=14) |
| channel_phase_linear/pretrained_full | -0.096 [-0.234, +0.043] (n=24) | -0.482 [-0.574, -0.390] (n=29) | -0.428 [-0.573, -0.283] (n=14) |
| dense_query/random_full | -0.098 [-0.234, +0.038] (n=24) | -0.484 [-0.580, -0.388] (n=29) | -0.431 [-0.585, -0.277] (n=14) |
| dense_query/pretrained_frozen | -0.097 [-0.237, +0.043] (n=24) | -0.485 [-0.577, -0.393] (n=29) | -0.431 [-0.585, -0.277] (n=14) |
| dense_query/pretrained_peft | -0.099 [-0.242, +0.043] (n=24) | -0.486 [-0.578, -0.393] (n=29) | -0.434 [-0.588, -0.280] (n=14) |
| dense_query/pretrained_partial | -0.098 [-0.247, +0.050] (n=24) | -0.486 [-0.577, -0.395] (n=29) | -0.434 [-0.586, -0.281] (n=14) |
| dense_query/pretrained_full | -0.098 [-0.238, +0.042] (n=24) | -0.484 [-0.577, -0.392] (n=29) | -0.432 [-0.584, -0.279] (n=14) |

**FAU · CS_SINGLE · reve** (family `B-LOCAL|fau|CS_SINGLE|reve`, critical value 1.98)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 67 | -0.333 | [-0.411, -0.255] | [-0.412, -0.254] | I<0 | -0.044 | -0.183 | -0.724 | -0.353 | -0.020 |
| channel_phase_linear/pretrained_frozen | vs local | 67 | -0.335 | [-0.413, -0.256] | [-0.414, -0.255] | I<0 | -0.044 | -0.181 | -0.724 | -0.353 | -0.023 |
| channel_phase_linear/pretrained_peft | vs local | 67 | -0.333 | [-0.410, -0.255] | [-0.411, -0.254] | I<0 | -0.043 | -0.175 | -0.719 | -0.349 | -0.025 |
| channel_phase_linear/pretrained_partial | vs local | 67 | -0.335 | [-0.413, -0.256] | [-0.414, -0.255] | I<0 | -0.044 | -0.181 | -0.724 | -0.353 | -0.021 |
| channel_phase_linear/pretrained_full | vs local | 67 | -0.335 | [-0.413, -0.256] | [-0.414, -0.255] | I<0 | -0.044 | -0.181 | -0.724 | -0.353 | -0.021 |
| dense_query/random_full | vs local | 67 | -0.335 | [-0.413, -0.257] | [-0.414, -0.256] | I<0 | -0.045 | -0.182 | -0.723 | -0.352 | -0.021 |
| dense_query/pretrained_frozen | vs local | 67 | -0.334 | [-0.412, -0.256] | [-0.413, -0.255] | I<0 | -0.044 | -0.183 | -0.724 | -0.353 | -0.014 |
| dense_query/pretrained_peft | vs local | 67 | -0.333 | [-0.412, -0.255] | [-0.413, -0.254] | I<0 | -0.044 | -0.183 | -0.724 | -0.353 | -0.018 |
| dense_query/pretrained_partial | vs local | 67 | -0.336 | [-0.414, -0.257] | [-0.415, -0.256] | I<0 | -0.044 | -0.183 | -0.725 | -0.353 | -0.016 |
| dense_query/pretrained_full | vs local | 67 | -0.333 | [-0.412, -0.255] | [-0.413, -0.254] | I<0 | -0.044 | -0.182 | -0.724 | -0.352 | -0.013 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | ci | ha | th |
|---|---|---|---|
| channel_phase_linear/random_full | -0.096 [-0.237, +0.045] (n=24) | -0.483 [-0.572, -0.393] (n=29) | -0.430 [-0.585, -0.276] (n=14) |
| channel_phase_linear/pretrained_frozen | -0.097 [-0.238, +0.043] (n=24) | -0.484 [-0.576, -0.392] (n=29) | -0.432 [-0.581, -0.283] (n=14) |
| channel_phase_linear/pretrained_peft | -0.097 [-0.235, +0.041] (n=24) | -0.481 [-0.572, -0.391] (n=29) | -0.429 [-0.583, -0.274] (n=14) |
| channel_phase_linear/pretrained_partial | -0.098 [-0.240, +0.044] (n=24) | -0.484 [-0.576, -0.392] (n=29) | -0.431 [-0.584, -0.279] (n=14) |
| channel_phase_linear/pretrained_full | -0.098 [-0.241, +0.046] (n=24) | -0.484 [-0.577, -0.391] (n=29) | -0.431 [-0.587, -0.276] (n=14) |
| dense_query/random_full | -0.098 [-0.235, +0.039] (n=24) | -0.484 [-0.579, -0.390] (n=29) | -0.430 [-0.579, -0.281] (n=14) |
| dense_query/pretrained_frozen | -0.097 [-0.238, +0.044] (n=24) | -0.483 [-0.577, -0.389] (n=29) | -0.431 [-0.581, -0.281] (n=14) |
| dense_query/pretrained_peft | -0.096 [-0.233, +0.042] (n=24) | -0.483 [-0.574, -0.392] (n=29) | -0.431 [-0.582, -0.280] (n=14) |
| dense_query/pretrained_partial | -0.098 [-0.237, +0.041] (n=24) | -0.485 [-0.579, -0.391] (n=29) | -0.432 [-0.588, -0.276] (n=14) |
| dense_query/pretrained_full | -0.096 [-0.234, +0.042] (n=24) | -0.483 [-0.575, -0.391] (n=29) | -0.431 [-0.584, -0.278] (n=14) |

**DTU · NCE · cbramod** (family `B-LOCAL|dtu|NCE|cbramod`, critical value 2.05)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 44 | -0.857 | [-1.013, -0.701] | [-1.017, -0.697] | I<0 | -0.062 | -0.252 | -1.985 | -1.506 | -0.163 |
| channel_phase_linear/pretrained_frozen | vs local | 44 | -0.867 | [-1.023, -0.710] | [-1.026, -0.707] | I<0 | -0.060 | -0.254 | -1.985 | -1.513 | -0.143 |
| channel_phase_linear/pretrained_peft | vs local | 44 | -0.862 | [-1.020, -0.704] | [-1.023, -0.701] | I<0 | -0.061 | -0.263 | -1.995 | -1.516 | -0.157 |
| channel_phase_linear/pretrained_partial | vs local | 44 | -0.868 | [-1.023, -0.713] | [-1.026, -0.709] | I<0 | -0.061 | -0.253 | -1.980 | -1.509 | -0.144 |
| channel_phase_linear/pretrained_full | vs local | 44 | -0.860 | [-1.016, -0.705] | [-1.019, -0.702] | I<0 | -0.062 | -0.251 | -1.980 | -1.511 | -0.147 |
| dense_query/random_full | vs local | 44 | -0.877 | [-1.037, -0.718] | [-1.041, -0.714] | I<0 | -0.062 | -0.285 | -2.007 | -1.511 | -0.180 |
| dense_query/pretrained_frozen | vs local | 44 | -0.868 | [-1.028, -0.709] | [-1.031, -0.706] | I<0 | -0.060 | -0.285 | -2.009 | -1.512 | -0.184 |
| dense_query/pretrained_peft | vs local | 44 | -0.873 | [-1.032, -0.713] | [-1.035, -0.710] | I<0 | -0.060 | -0.284 | -2.009 | -1.513 | -0.180 |
| dense_query/pretrained_partial | vs local | 44 | -0.871 | [-1.029, -0.713] | [-1.033, -0.709] | I<0 | -0.060 | -0.284 | -2.009 | -1.512 | -0.181 |
| dense_query/pretrained_full | vs local | 44 | -0.870 | [-1.030, -0.711] | [-1.033, -0.707] | I<0 | -0.061 | -0.286 | -2.009 | -1.512 | -0.184 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | hi | nh |
|---|---|---|
| channel_phase_linear/random_full | -1.085 [-1.323, -0.848] (n=22) | -0.629 [-0.809, -0.449] (n=22) |
| channel_phase_linear/pretrained_frozen | -1.090 [-1.323, -0.857] (n=22) | -0.643 [-0.825, -0.461] (n=22) |
| channel_phase_linear/pretrained_peft | -1.087 [-1.325, -0.849] (n=22) | -0.637 [-0.820, -0.454] (n=22) |
| channel_phase_linear/pretrained_partial | -1.093 [-1.322, -0.864] (n=22) | -0.642 [-0.823, -0.461] (n=22) |
| channel_phase_linear/pretrained_full | -1.086 [-1.318, -0.855] (n=22) | -0.635 [-0.814, -0.455] (n=22) |
| dense_query/random_full | -1.108 [-1.349, -0.867] (n=22) | -0.647 [-0.834, -0.460] (n=22) |
| dense_query/pretrained_frozen | -1.099 [-1.340, -0.859] (n=22) | -0.637 [-0.822, -0.453] (n=22) |
| dense_query/pretrained_peft | -1.103 [-1.339, -0.868] (n=22) | -0.642 [-0.830, -0.454] (n=22) |
| dense_query/pretrained_partial | -1.102 [-1.338, -0.866] (n=22) | -0.639 [-0.825, -0.454] (n=22) |
| dense_query/pretrained_full | -1.101 [-1.340, -0.861] (n=22) | -0.640 [-0.827, -0.452] (n=22) |

**DTU · NCE · reve** (family `B-LOCAL|dtu|NCE|reve`, critical value 2.09)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 44 | -0.834 | [-0.985, -0.682] | [-0.991, -0.677] | I<0 | -0.058 | -0.216 | -1.921 | -1.496 | -0.149 |
| channel_phase_linear/pretrained_frozen | vs local | 44 | -0.794 | [-0.945, -0.643] | [-0.948, -0.639] | I<0 | -0.057 | -0.192 | -1.865 | -1.471 | -0.134 |
| channel_phase_linear/pretrained_peft | vs local | 44 | -0.777 | [-0.923, -0.632] | [-0.928, -0.627] | I<0 | -0.054 | -0.182 | -1.827 | -1.431 | -0.122 |
| channel_phase_linear/pretrained_partial | vs local | 44 | -0.785 | [-0.935, -0.635] | [-0.938, -0.631] | I<0 | -0.055 | -0.185 | -1.843 | -1.455 | -0.128 |
| channel_phase_linear/pretrained_full | vs local | 44 | -0.785 | [-0.935, -0.635] | [-0.938, -0.631] | I<0 | -0.055 | -0.185 | -1.843 | -1.455 | -0.128 |
| dense_query/random_full | vs local | 44 | -0.883 | [-1.041, -0.726] | [-1.047, -0.719] | I<0 | -0.061 | -0.282 | -2.009 | -1.512 | -0.185 |
| dense_query/pretrained_frozen | vs local | 44 | -0.867 | [-1.025, -0.708] | [-1.032, -0.701] | I<0 | -0.062 | -0.281 | -2.008 | -1.513 | -0.180 |
| dense_query/pretrained_peft | vs local | 44 | -0.873 | [-1.032, -0.714] | [-1.038, -0.708] | I<0 | -0.061 | -0.284 | -2.009 | -1.513 | -0.180 |
| dense_query/pretrained_partial | vs local | 44 | -0.866 | [-1.024, -0.708] | [-1.032, -0.700] | I<0 | -0.062 | -0.284 | -2.009 | -1.513 | -0.185 |
| dense_query/pretrained_full | vs local | 44 | -0.866 | [-1.024, -0.708] | [-1.032, -0.700] | I<0 | -0.062 | -0.284 | -2.009 | -1.513 | -0.185 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | hi | nh |
|---|---|---|
| channel_phase_linear/random_full | -1.057 [-1.288, -0.826] (n=22) | -0.611 [-0.782, -0.439] (n=22) |
| channel_phase_linear/pretrained_frozen | -1.021 [-1.243, -0.799] (n=22) | -0.566 [-0.736, -0.397] (n=22) |
| channel_phase_linear/pretrained_peft | -0.999 [-1.215, -0.783] (n=22) | -0.555 [-0.718, -0.393] (n=22) |
| channel_phase_linear/pretrained_partial | -1.010 [-1.224, -0.796] (n=22) | -0.559 [-0.723, -0.395] (n=22) |
| channel_phase_linear/pretrained_full | -1.010 [-1.225, -0.795] (n=22) | -0.559 [-0.727, -0.391] (n=22) |
| dense_query/random_full | -1.114 [-1.346, -0.882] (n=22) | -0.653 [-0.837, -0.469] (n=22) |
| dense_query/pretrained_frozen | -1.096 [-1.336, -0.857] (n=22) | -0.637 [-0.819, -0.454] (n=22) |
| dense_query/pretrained_peft | -1.103 [-1.342, -0.864] (n=22) | -0.642 [-0.833, -0.452] (n=22) |
| dense_query/pretrained_partial | -1.096 [-1.334, -0.859] (n=22) | -0.635 [-0.819, -0.452] (n=22) |
| dense_query/pretrained_full | -1.096 [-1.336, -0.857] (n=22) | -0.635 [-0.818, -0.453] (n=22) |

**DTU · CS_SINGLE · cbramod** (family `B-LOCAL|dtu|CS_SINGLE|cbramod`, critical value 2.04)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 44 | -0.623 | [-0.740, -0.506] | [-0.743, -0.503] | I<0 | -0.043 | -0.232 | -1.373 | -0.520 | -0.153 |
| channel_phase_linear/pretrained_frozen | vs local | 44 | -0.625 | [-0.742, -0.508] | [-0.745, -0.506] | I<0 | -0.042 | -0.242 | -1.378 | -0.520 | -0.152 |
| channel_phase_linear/pretrained_peft | vs local | 44 | -0.628 | [-0.745, -0.512] | [-0.748, -0.508] | I<0 | -0.041 | -0.243 | -1.376 | -0.520 | -0.148 |
| channel_phase_linear/pretrained_partial | vs local | 44 | -0.630 | [-0.746, -0.513] | [-0.749, -0.510] | I<0 | -0.044 | -0.238 | -1.375 | -0.521 | -0.145 |
| channel_phase_linear/pretrained_full | vs local | 44 | -0.625 | [-0.743, -0.507] | [-0.745, -0.504] | I<0 | -0.043 | -0.232 | -1.371 | -0.521 | -0.148 |
| dense_query/random_full | vs local | 44 | -0.640 | [-0.757, -0.523] | [-0.760, -0.519] | I<0 | -0.042 | -0.248 | -1.380 | -0.522 | -0.162 |
| dense_query/pretrained_frozen | vs local | 44 | -0.644 | [-0.760, -0.529] | [-0.763, -0.526] | I<0 | -0.042 | -0.243 | -1.382 | -0.522 | -0.167 |
| dense_query/pretrained_peft | vs local | 44 | -0.631 | [-0.749, -0.514] | [-0.752, -0.510] | I<0 | -0.044 | -0.242 | -1.379 | -0.521 | -0.156 |
| dense_query/pretrained_partial | vs local | 44 | -0.641 | [-0.757, -0.525] | [-0.761, -0.521] | I<0 | -0.044 | -0.250 | -1.383 | -0.524 | -0.165 |
| dense_query/pretrained_full | vs local | 44 | -0.633 | [-0.750, -0.516] | [-0.754, -0.512] | I<0 | -0.044 | -0.245 | -1.385 | -0.523 | -0.161 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | hi | nh |
|---|---|---|
| channel_phase_linear/random_full | -0.780 [-0.957, -0.604] (n=22) | -0.465 [-0.609, -0.322] (n=22) |
| channel_phase_linear/pretrained_frozen | -0.780 [-0.954, -0.606] (n=22) | -0.471 [-0.617, -0.325] (n=22) |
| channel_phase_linear/pretrained_peft | -0.780 [-0.959, -0.602] (n=22) | -0.476 [-0.625, -0.327] (n=22) |
| channel_phase_linear/pretrained_partial | -0.784 [-0.961, -0.608] (n=22) | -0.475 [-0.617, -0.333] (n=22) |
| channel_phase_linear/pretrained_full | -0.779 [-0.959, -0.600] (n=22) | -0.470 [-0.621, -0.320] (n=22) |
| dense_query/random_full | -0.799 [-0.977, -0.620] (n=22) | -0.481 [-0.625, -0.337] (n=22) |
| dense_query/pretrained_frozen | -0.795 [-0.974, -0.616] (n=22) | -0.494 [-0.641, -0.346] (n=22) |
| dense_query/pretrained_peft | -0.787 [-0.964, -0.611] (n=22) | -0.475 [-0.626, -0.325] (n=22) |
| dense_query/pretrained_partial | -0.794 [-0.971, -0.617] (n=22) | -0.488 [-0.636, -0.340] (n=22) |
| dense_query/pretrained_full | -0.788 [-0.962, -0.613] (n=22) | -0.478 [-0.630, -0.327] (n=22) |

**DTU · CS_SINGLE · reve** (family `B-LOCAL|dtu|CS_SINGLE|reve`, critical value 2.15)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 44 | -0.643 | [-0.767, -0.518] | [-0.773, -0.512] | I<0 | -0.040 | -0.237 | -1.376 | -0.525 | -0.167 |
| channel_phase_linear/pretrained_frozen | vs local | 44 | -0.634 | [-0.756, -0.512] | [-0.761, -0.506] | I<0 | -0.041 | -0.235 | -1.374 | -0.520 | -0.163 |
| channel_phase_linear/pretrained_peft | vs local | 44 | -0.639 | [-0.759, -0.518] | [-0.765, -0.512] | I<0 | -0.040 | -0.233 | -1.373 | -0.522 | -0.168 |
| channel_phase_linear/pretrained_partial | vs local | 44 | -0.632 | [-0.754, -0.510] | [-0.760, -0.505] | I<0 | -0.041 | -0.236 | -1.375 | -0.520 | -0.161 |
| channel_phase_linear/pretrained_full | vs local | 44 | -0.632 | [-0.754, -0.510] | [-0.760, -0.505] | I<0 | -0.041 | -0.236 | -1.375 | -0.520 | -0.161 |
| dense_query/random_full | vs local | 44 | -0.648 | [-0.769, -0.527] | [-0.774, -0.522] | I<0 | -0.042 | -0.245 | -1.383 | -0.522 | -0.164 |
| dense_query/pretrained_frozen | vs local | 44 | -0.653 | [-0.777, -0.530] | [-0.782, -0.525] | I<0 | -0.041 | -0.244 | -1.381 | -0.527 | -0.168 |
| dense_query/pretrained_peft | vs local | 44 | -0.648 | [-0.768, -0.527] | [-0.774, -0.521] | I<0 | -0.042 | -0.248 | -1.381 | -0.527 | -0.167 |
| dense_query/pretrained_partial | vs local | 44 | -0.648 | [-0.770, -0.526] | [-0.775, -0.521] | I<0 | -0.042 | -0.245 | -1.381 | -0.527 | -0.170 |
| dense_query/pretrained_full | vs local | 44 | -0.648 | [-0.770, -0.526] | [-0.775, -0.521] | I<0 | -0.042 | -0.245 | -1.381 | -0.527 | -0.170 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | hi | nh |
|---|---|---|
| channel_phase_linear/random_full | -0.801 [-0.976, -0.626] (n=22) | -0.484 [-0.634, -0.334] (n=22) |
| channel_phase_linear/pretrained_frozen | -0.790 [-0.971, -0.609] (n=22) | -0.478 [-0.629, -0.327] (n=22) |
| channel_phase_linear/pretrained_peft | -0.791 [-0.970, -0.611] (n=22) | -0.487 [-0.629, -0.344] (n=22) |
| channel_phase_linear/pretrained_partial | -0.788 [-0.965, -0.611] (n=22) | -0.477 [-0.623, -0.332] (n=22) |
| channel_phase_linear/pretrained_full | -0.788 [-0.968, -0.607] (n=22) | -0.477 [-0.623, -0.331] (n=22) |
| dense_query/random_full | -0.802 [-0.981, -0.624] (n=22) | -0.494 [-0.642, -0.346] (n=22) |
| dense_query/pretrained_frozen | -0.806 [-0.983, -0.629] (n=22) | -0.500 [-0.652, -0.348] (n=22) |
| dense_query/pretrained_peft | -0.803 [-0.976, -0.630] (n=22) | -0.492 [-0.637, -0.347] (n=22) |
| dense_query/pretrained_partial | -0.801 [-0.976, -0.625] (n=22) | -0.495 [-0.645, -0.346] (n=22) |
| dense_query/pretrained_full | -0.801 [-0.974, -0.628] (n=22) | -0.495 [-0.644, -0.347] (n=22) |

**Federici · NCE · cbramod** (family `B-LOCAL|federici|NCE|cbramod`, critical value 2.11)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 86 | -0.117 | [-0.150, -0.083] | [-0.152, -0.081] | I<0 | -0.009 | -0.102 | -0.262 | -0.171 | – |
| channel_phase_linear/pretrained_frozen | vs local | 86 | -0.118 | [-0.151, -0.084] | [-0.153, -0.082] | I<0 | -0.008 | -0.102 | -0.264 | -0.171 | – |
| channel_phase_linear/pretrained_peft | vs local | 86 | -0.115 | [-0.148, -0.081] | [-0.150, -0.079] | I<0 | -0.008 | -0.102 | -0.265 | -0.169 | – |
| channel_phase_linear/pretrained_partial | vs local | 86 | -0.114 | [-0.148, -0.080] | [-0.150, -0.078] | I<0 | -0.006 | -0.098 | -0.263 | -0.170 | – |
| channel_phase_linear/pretrained_full | vs local | 86 | -0.113 | [-0.147, -0.079] | [-0.149, -0.077] | I<0 | -0.005 | -0.095 | -0.263 | -0.170 | – |
| dense_query/random_full | vs local | 86 | -0.116 | [-0.150, -0.082] | [-0.152, -0.080] | I<0 | -0.007 | -0.108 | -0.264 | -0.171 | – |
| dense_query/pretrained_frozen | vs local | 86 | -0.115 | [-0.149, -0.081] | [-0.150, -0.079] | I<0 | -0.007 | -0.115 | -0.264 | -0.171 | – |
| dense_query/pretrained_peft | vs local | 86 | -0.114 | [-0.148, -0.081] | [-0.150, -0.079] | I<0 | -0.009 | -0.116 | -0.264 | -0.171 | – |
| dense_query/pretrained_partial | vs local | 86 | -0.115 | [-0.149, -0.081] | [-0.150, -0.079] | I<0 | -0.009 | -0.113 | -0.264 | -0.170 | – |
| dense_query/pretrained_full | vs local | 86 | -0.116 | [-0.149, -0.082] | [-0.151, -0.080] | I<0 | -0.008 | -0.120 | -0.264 | -0.172 | – |

Per group (descriptive, pointwise; n < 5 → n only):

| member | CI | HC | HC-v |
|---|---|---|---|
| channel_phase_linear/random_full | -0.138 [-0.202, -0.075] (n=33) | -0.104 [-0.156, -0.053] (n=37) | -0.100 [-0.169, -0.031] (n=16) |
| channel_phase_linear/pretrained_frozen | -0.142 [-0.203, -0.080] (n=33) | -0.106 [-0.157, -0.055] (n=37) | -0.096 [-0.166, -0.027] (n=16) |
| channel_phase_linear/pretrained_peft | -0.141 [-0.202, -0.080] (n=33) | -0.104 [-0.152, -0.055] (n=37) | -0.086 [-0.161, -0.012] (n=16) |
| channel_phase_linear/pretrained_partial | -0.138 [-0.201, -0.075] (n=33) | -0.102 [-0.152, -0.052] (n=37) | -0.091 [-0.162, -0.020] (n=16) |
| channel_phase_linear/pretrained_full | -0.137 [-0.202, -0.073] (n=33) | -0.102 [-0.151, -0.053] (n=37) | -0.088 [-0.163, -0.012] (n=16) |
| dense_query/random_full | -0.142 [-0.203, -0.081] (n=33) | -0.104 [-0.155, -0.054] (n=37) | -0.090 [-0.162, -0.017] (n=16) |
| dense_query/pretrained_frozen | -0.139 [-0.201, -0.077] (n=33) | -0.105 [-0.153, -0.057] (n=37) | -0.087 [-0.161, -0.014] (n=16) |
| dense_query/pretrained_peft | -0.138 [-0.202, -0.075] (n=33) | -0.105 [-0.155, -0.055] (n=37) | -0.087 [-0.159, -0.015] (n=16) |
| dense_query/pretrained_partial | -0.138 [-0.199, -0.077] (n=33) | -0.106 [-0.155, -0.056] (n=37) | -0.088 [-0.162, -0.014] (n=16) |
| dense_query/pretrained_full | -0.139 [-0.203, -0.075] (n=33) | -0.106 [-0.156, -0.056] (n=37) | -0.088 [-0.161, -0.015] (n=16) |

**Federici · NCE · reve** (family `B-LOCAL|federici|NCE|reve`, critical value 2.33)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 86 | -0.116 | [-0.150, -0.082] | [-0.156, -0.076] | I<0 | -0.007 | -0.103 | -0.262 | -0.172 | – |
| channel_phase_linear/pretrained_frozen | vs local | 86 | -0.102 | [-0.135, -0.070] | [-0.140, -0.065] | I<0 | -0.004 | -0.084 | -0.239 | -0.161 | – |
| channel_phase_linear/pretrained_peft | vs local | 86 | -0.042 | [-0.073, -0.010] | [-0.078, -0.005] | I<0 | -0.002 | -0.020 | -0.117 | -0.098 | – |
| channel_phase_linear/pretrained_partial | vs local | 86 | -0.102 | [-0.134, -0.069] | [-0.139, -0.064] | I<0 | -0.004 | -0.083 | -0.235 | -0.154 | – |
| channel_phase_linear/pretrained_full | vs local | 86 | -0.102 | [-0.134, -0.069] | [-0.139, -0.064] | I<0 | -0.004 | -0.083 | -0.235 | -0.153 | – |
| dense_query/random_full | vs local | 86 | -0.117 | [-0.151, -0.083] | [-0.156, -0.077] | I<0 | -0.008 | -0.114 | -0.264 | -0.171 | – |
| dense_query/pretrained_frozen | vs local | 86 | -0.115 | [-0.149, -0.081] | [-0.155, -0.076] | I<0 | -0.010 | -0.107 | -0.264 | -0.177 | – |
| dense_query/pretrained_peft | vs local | 86 | -0.122 | [-0.156, -0.087] | [-0.161, -0.082] | I<0 | -0.008 | -0.117 | -0.270 | -0.178 | – |
| dense_query/pretrained_partial | vs local | 86 | -0.114 | [-0.149, -0.080] | [-0.154, -0.075] | I<0 | -0.008 | -0.112 | -0.265 | -0.174 | – |
| dense_query/pretrained_full | vs local | 86 | -0.114 | [-0.149, -0.080] | [-0.154, -0.075] | I<0 | -0.008 | -0.112 | -0.265 | -0.174 | – |

Per group (descriptive, pointwise; n < 5 → n only):

| member | CI | HC | HC-v |
|---|---|---|---|
| channel_phase_linear/random_full | -0.138 [-0.198, -0.077] (n=33) | -0.106 [-0.159, -0.052] (n=37) | -0.095 [-0.166, -0.024] (n=16) |
| channel_phase_linear/pretrained_frozen | -0.123 [-0.181, -0.065] (n=33) | -0.090 [-0.140, -0.040] (n=37) | -0.089 [-0.162, -0.016] (n=16) |
| channel_phase_linear/pretrained_peft | -0.081 [-0.137, -0.025] (n=33) | -0.012 [-0.058, +0.035] (n=37) | -0.030 [-0.094, +0.034] (n=16) |
| channel_phase_linear/pretrained_partial | -0.121 [-0.180, -0.063] (n=33) | -0.090 [-0.139, -0.041] (n=37) | -0.089 [-0.162, -0.017] (n=16) |
| channel_phase_linear/pretrained_full | -0.121 [-0.179, -0.064] (n=33) | -0.090 [-0.139, -0.040] (n=37) | -0.089 [-0.162, -0.017] (n=16) |
| dense_query/random_full | -0.141 [-0.205, -0.078] (n=33) | -0.107 [-0.157, -0.058] (n=37) | -0.089 [-0.167, -0.012] (n=16) |
| dense_query/pretrained_frozen | -0.137 [-0.202, -0.073] (n=33) | -0.107 [-0.156, -0.058] (n=37) | -0.089 [-0.163, -0.015] (n=16) |
| dense_query/pretrained_peft | -0.145 [-0.208, -0.082] (n=33) | -0.111 [-0.162, -0.061] (n=37) | -0.098 [-0.168, -0.027] (n=16) |
| dense_query/pretrained_partial | -0.138 [-0.199, -0.077] (n=33) | -0.104 [-0.156, -0.052] (n=37) | -0.088 [-0.163, -0.013] (n=16) |
| dense_query/pretrained_full | -0.138 [-0.201, -0.076] (n=33) | -0.104 [-0.156, -0.053] (n=37) | -0.088 [-0.164, -0.012] (n=16) |

**Federici · CS_SINGLE · cbramod** (family `B-LOCAL|federici|CS_SINGLE|cbramod`, critical value 2.14)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 86 | -0.095 | [-0.127, -0.062] | [-0.129, -0.060] | I<0 | -0.009 | -0.102 | -0.221 | -0.001 | – |
| channel_phase_linear/pretrained_frozen | vs local | 86 | -0.096 | [-0.129, -0.063] | [-0.131, -0.061] | I<0 | -0.008 | -0.098 | -0.222 | -0.001 | – |
| channel_phase_linear/pretrained_peft | vs local | 86 | -0.096 | [-0.128, -0.063] | [-0.130, -0.061] | I<0 | -0.009 | -0.103 | -0.221 | -0.002 | – |
| channel_phase_linear/pretrained_partial | vs local | 86 | -0.096 | [-0.129, -0.064] | [-0.131, -0.061] | I<0 | -0.008 | -0.102 | -0.221 | -0.001 | – |
| channel_phase_linear/pretrained_full | vs local | 86 | -0.096 | [-0.128, -0.063] | [-0.130, -0.061] | I<0 | -0.008 | -0.096 | -0.220 | -0.001 | – |
| dense_query/random_full | vs local | 86 | -0.095 | [-0.128, -0.062] | [-0.130, -0.059] | I<0 | -0.008 | -0.104 | -0.221 | -0.002 | – |
| dense_query/pretrained_frozen | vs local | 86 | -0.093 | [-0.126, -0.060] | [-0.128, -0.058] | I<0 | -0.006 | -0.099 | -0.218 | -0.001 | – |
| dense_query/pretrained_peft | vs local | 86 | -0.095 | [-0.128, -0.061] | [-0.130, -0.059] | I<0 | -0.011 | -0.102 | -0.222 | -0.002 | – |
| dense_query/pretrained_partial | vs local | 86 | -0.093 | [-0.126, -0.060] | [-0.128, -0.058] | I<0 | -0.009 | -0.091 | -0.221 | -0.001 | – |
| dense_query/pretrained_full | vs local | 86 | -0.096 | [-0.129, -0.063] | [-0.132, -0.060] | I<0 | -0.009 | -0.104 | -0.222 | -0.001 | – |

Per group (descriptive, pointwise; n < 5 → n only):

| member | CI | HC | HC-v |
|---|---|---|---|
| channel_phase_linear/random_full | -0.096 [-0.161, -0.031] (n=33) | -0.100 [-0.147, -0.054] (n=37) | -0.080 [-0.148, -0.012] (n=16) |
| channel_phase_linear/pretrained_frozen | -0.098 [-0.164, -0.033] (n=33) | -0.099 [-0.144, -0.053] (n=37) | -0.086 [-0.152, -0.019] (n=16) |
| channel_phase_linear/pretrained_peft | -0.096 [-0.160, -0.033] (n=33) | -0.100 [-0.145, -0.055] (n=37) | -0.086 [-0.151, -0.020] (n=16) |
| channel_phase_linear/pretrained_partial | -0.099 [-0.164, -0.034] (n=33) | -0.099 [-0.144, -0.055] (n=37) | -0.083 [-0.149, -0.016] (n=16) |
| channel_phase_linear/pretrained_full | -0.097 [-0.160, -0.033] (n=33) | -0.100 [-0.146, -0.054] (n=37) | -0.084 [-0.152, -0.016] (n=16) |
| dense_query/random_full | -0.097 [-0.161, -0.033] (n=33) | -0.104 [-0.152, -0.056] (n=37) | -0.067 [-0.138, +0.004] (n=16) |
| dense_query/pretrained_frozen | -0.097 [-0.162, -0.033] (n=33) | -0.099 [-0.144, -0.054] (n=37) | -0.069 [-0.140, +0.001] (n=16) |
| dense_query/pretrained_peft | -0.098 [-0.161, -0.035] (n=33) | -0.104 [-0.151, -0.057] (n=37) | -0.066 [-0.141, +0.009] (n=16) |
| dense_query/pretrained_partial | -0.096 [-0.161, -0.032] (n=33) | -0.100 [-0.146, -0.054] (n=37) | -0.069 [-0.139, +0.001] (n=16) |
| dense_query/pretrained_full | -0.098 [-0.164, -0.033] (n=33) | -0.104 [-0.153, -0.055] (n=37) | -0.073 [-0.144, -0.003] (n=16) |

**Federici · CS_SINGLE · reve** (family `B-LOCAL|federici|CS_SINGLE|reve`, critical value 2.07)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel_phase_linear/random_full | vs local | 86 | -0.097 | [-0.129, -0.065] | [-0.131, -0.063] | I<0 | -0.008 | -0.107 | -0.220 | -0.001 | – |
| channel_phase_linear/pretrained_frozen | vs local | 86 | -0.096 | [-0.128, -0.063] | [-0.130, -0.062] | I<0 | -0.008 | -0.107 | -0.221 | -0.002 | – |
| channel_phase_linear/pretrained_peft | vs local | 86 | -0.095 | [-0.128, -0.063] | [-0.130, -0.061] | I<0 | -0.008 | -0.114 | -0.221 | -0.002 | – |
| channel_phase_linear/pretrained_partial | vs local | 86 | -0.096 | [-0.128, -0.063] | [-0.130, -0.062] | I<0 | -0.008 | -0.107 | -0.221 | -0.002 | – |
| channel_phase_linear/pretrained_full | vs local | 86 | -0.096 | [-0.128, -0.063] | [-0.130, -0.062] | I<0 | -0.008 | -0.107 | -0.221 | -0.002 | – |
| dense_query/random_full | vs local | 86 | -0.097 | [-0.129, -0.064] | [-0.131, -0.062] | I<0 | -0.008 | -0.108 | -0.220 | -0.001 | – |
| dense_query/pretrained_frozen | vs local | 86 | -0.095 | [-0.128, -0.062] | [-0.130, -0.061] | I<0 | -0.009 | -0.106 | -0.221 | -0.001 | – |
| dense_query/pretrained_peft | vs local | 86 | -0.094 | [-0.126, -0.062] | [-0.128, -0.060] | I<0 | -0.010 | -0.105 | -0.221 | -0.001 | – |
| dense_query/pretrained_partial | vs local | 86 | -0.094 | [-0.126, -0.061] | [-0.128, -0.060] | I<0 | -0.010 | -0.106 | -0.221 | -0.001 | – |
| dense_query/pretrained_full | vs local | 86 | -0.094 | [-0.126, -0.062] | [-0.128, -0.060] | I<0 | -0.010 | -0.104 | -0.219 | -0.001 | – |

Per group (descriptive, pointwise; n < 5 → n only):

| member | CI | HC | HC-v |
|---|---|---|---|
| channel_phase_linear/random_full | -0.100 [-0.162, -0.038] (n=33) | -0.107 [-0.156, -0.058] (n=37) | -0.068 [-0.138, +0.002] (n=16) |
| channel_phase_linear/pretrained_frozen | -0.099 [-0.163, -0.035] (n=33) | -0.105 [-0.152, -0.057] (n=37) | -0.069 [-0.140, +0.002] (n=16) |
| channel_phase_linear/pretrained_peft | -0.099 [-0.160, -0.037] (n=33) | -0.104 [-0.152, -0.055] (n=37) | -0.069 [-0.140, +0.002] (n=16) |
| channel_phase_linear/pretrained_partial | -0.099 [-0.162, -0.037] (n=33) | -0.105 [-0.152, -0.057] (n=37) | -0.069 [-0.140, +0.002] (n=16) |
| channel_phase_linear/pretrained_full | -0.099 [-0.163, -0.036] (n=33) | -0.105 [-0.152, -0.057] (n=37) | -0.069 [-0.139, +0.002] (n=16) |
| dense_query/random_full | -0.103 [-0.164, -0.042] (n=33) | -0.103 [-0.149, -0.056] (n=37) | -0.070 [-0.145, +0.004] (n=16) |
| dense_query/pretrained_frozen | -0.099 [-0.163, -0.034] (n=33) | -0.100 [-0.149, -0.051] (n=37) | -0.077 [-0.154, -0.001] (n=16) |
| dense_query/pretrained_peft | -0.096 [-0.159, -0.034] (n=33) | -0.102 [-0.150, -0.053] (n=37) | -0.072 [-0.144, +0.001] (n=16) |
| dense_query/pretrained_partial | -0.097 [-0.159, -0.034] (n=33) | -0.101 [-0.148, -0.055] (n=37) | -0.069 [-0.143, +0.005] (n=16) |
| dense_query/pretrained_full | -0.098 [-0.162, -0.034] (n=33) | -0.100 [-0.147, -0.054] (n=37) | -0.071 [-0.146, +0.004] (n=16) |

## 7. Not in this interim

- Seed panel (3407 / 3413): to be added with the same code when the registered cells complete (ADDENDUM_05 §6).
- B_LAYER_PROBE layer panel, B_LR_PANEL, B_CTRL_ONESTEP, training curves.
- The ALN2 coarse `SpatialPatchHead` interface (1.2 s target) is not differenced against ALN3 (docs/05 l.24).

## Appendix: notes

190 notes (first 40 listed; all in the JSON):

- B-READOUT|federici|NCE|cbramod|sec/random_full/attention/unified/accuracy: no paired identities
- B-READOUT|federici|NCE|cbramod|sec/pretrained_frozen/attention/unified/accuracy: no paired identities
- B-READOUT|federici|NCE|cbramod|sec/pretrained_peft/attention/unified/accuracy: no paired identities
- B-READOUT|federici|NCE|cbramod|sec/pretrained_partial/attention/unified/accuracy: no paired identities
- B-READOUT|federici|NCE|cbramod|sec/pretrained_full/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_frozen/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_peft/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_partial/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_full/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/dense_query/pretrained_frozen/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/dense_query/pretrained_peft/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/dense_query/pretrained_partial/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/dense_query/pretrained_full/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_peft/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_partial/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_full/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/dense_query/pretrained_peft/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/dense_query/pretrained_partial/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/dense_query/pretrained_full/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/channel_phase_linear/random_full/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_frozen/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_peft/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_partial/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_full/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/dense_query/random_full/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/dense_query/pretrained_frozen/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/dense_query/pretrained_peft/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/dense_query/pretrained_partial/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/dense_query/pretrained_full/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/init_full/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/init_frozen/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/capacity_frozen/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/capacity_peft/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/capacity_full/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/residual_vs_concat/attention/unified/accuracy: no paired identities
- C-FMONLY|federici|NCE|cbramod|sec/concat_pretrained/attention/unified/accuracy: no paired identities
- C-FMONLY|federici|NCE|cbramod|sec/residual_pretrained_frozen/attention/unified/accuracy: no paired identities
- C-FMONLY|federici|NCE|cbramod|sec/residual_pretrained_peft/attention/unified/accuracy: no paired identities
- C-FMONLY|federici|NCE|cbramod|sec/residual_pretrained_full/attention/unified/accuracy: no paired identities
- C-FMONLY|federici|NCE|cbramod|sec/residual_random_frozen/attention/unified/accuracy: no paired identities
