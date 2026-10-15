# ALN3 private task (E families) — interim summary

> Publication copy (publish_027, 2026-10-16): released by the researcher; group-level aggregates only, no child-level value. The private original carried the heading "PRIVATE, not for publication". §2 labels `pretrained_full − random_full` "matched-update initialization"; that label is superseded by [CORRECTION_01](CORRECTION_01_FULL_UPDATE_LABEL.md) (a recipe contrast: 30× backbone lr, progressive-prefix schedule). Values unchanged; nothing else is changed.

**Interim, seed 3401 only.** Generated 2026-10-14 11:07 CEST (Slurm job 1039549) by `python -m auditory_alignment_v3.bc_interim` under the frozen `ADDENDUM_05_BC_INTERIM_AGGREGATION.md`. Intervals are identity-level bootstrap-t (4000 replicates) conditional on the seed-3401 training; they are not training-seed uncertainty. Simultaneous intervals: max-t within the family named in each table. Sign: positive = the candidate is better (ΔR = R(reference) − R(candidate), bits per 5 s query, unified readout). Classes follow ADDENDUM_05 §7; no other interpretation is made here.

Code sha256: `bc_interim.py` 2840df81b608, `bc_interim_report.py` d0cfe6de6bcd, `sci_r1/stats.py` 8bb141cf6070.

Private children, seed 3401. NLL = positive-affine calibrated natural-distribution NLL (bits, lower is better); AUC = positive-affine AUC (= native ranking). Contrasts: ΔNLL = NLL(reference) − NLL(candidate), ΔAUC = AUC(candidate) − AUC(reference); positive = candidate better. NLL changes with unchanged AUC are probability / calibration changes (docs/08 §5). No age, duration, stage or function analysis here.

## 0. Coverage

Unit status: {'E_GX|complete': 20, 'E_LOCAL|complete': 120, 'E_GENERIC|complete': 100, 'E_PUBLIC_TRANSFER|complete': 60, 'E_COMPLEMENT|complete': 60, 'E_DISTILL|complete': 120}. Children per configuration: {64: 132}. Groups: {'HA': 55, 'NH': 9}.

## 1. Levels

| configuration | n | NLL [95% CI] | AUC [95% CI] | hist gain | twin sens. | NLL HA / NH | AUC HA / NH |
|---|---|---|---|---|---|---|---|
| E_COMPLEMENT / CS_SINGLE / cbramod / residual_pretrained_frozen / combined | 64 | 0.716 [+0.710, +0.721] | 0.537 [+0.526, +0.548] | – | – | 0.716 / 0.716 | 0.533 / 0.561 |
| E_COMPLEMENT / CS_SINGLE / cbramod / residual_pretrained_frozen / local_only | 64 | 0.716 [+0.711, +0.721] | 0.544 [+0.532, +0.557] | – | – | 0.716 / 0.715 | 0.539 / 0.578 |
| E_COMPLEMENT / CS_SINGLE / cbramod / residual_pretrained_peft / combined | 64 | 0.716 [+0.710, +0.721] | 0.539 [+0.528, +0.551] | – | – | 0.716 / 0.715 | 0.535 / 0.567 |
| E_COMPLEMENT / CS_SINGLE / cbramod / residual_pretrained_peft / local_only | 64 | 0.716 [+0.710, +0.721] | 0.544 [+0.532, +0.557] | – | – | 0.716 / 0.715 | 0.539 / 0.578 |
| E_COMPLEMENT / CS_SINGLE / cbramod / residual_random_trainable / combined | 64 | 0.716 [+0.710, +0.721] | 0.539 [+0.528, +0.550] | – | – | 0.716 / 0.716 | 0.535 / 0.561 |
| E_COMPLEMENT / CS_SINGLE / cbramod / residual_random_trainable / local_only | 64 | 0.716 [+0.710, +0.721] | 0.544 [+0.532, +0.557] | – | – | 0.716 / 0.715 | 0.539 / 0.578 |
| E_COMPLEMENT / CS_SINGLE / reve / residual_pretrained_frozen / combined | 64 | 0.716 [+0.710, +0.721] | 0.539 [+0.528, +0.551] | – | – | 0.716 / 0.715 | 0.534 / 0.574 |
| E_COMPLEMENT / CS_SINGLE / reve / residual_pretrained_frozen / local_only | 64 | 0.716 [+0.710, +0.721] | 0.544 [+0.532, +0.557] | – | – | 0.716 / 0.715 | 0.539 / 0.578 |
| E_COMPLEMENT / CS_SINGLE / reve / residual_pretrained_peft / combined | 64 | 0.716 [+0.710, +0.721] | 0.538 [+0.525, +0.550] | – | – | 0.716 / 0.715 | 0.532 / 0.571 |
| E_COMPLEMENT / CS_SINGLE / reve / residual_pretrained_peft / local_only | 64 | 0.716 [+0.711, +0.721] | 0.544 [+0.532, +0.557] | – | – | 0.716 / 0.715 | 0.539 / 0.578 |
| E_COMPLEMENT / CS_SINGLE / reve / residual_random_trainable / combined | 64 | 0.716 [+0.710, +0.721] | 0.540 [+0.529, +0.551] | – | – | 0.716 / 0.715 | 0.535 / 0.575 |
| E_COMPLEMENT / CS_SINGLE / reve / residual_random_trainable / local_only | 64 | 0.716 [+0.710, +0.721] | 0.544 [+0.532, +0.557] | – | – | 0.716 / 0.715 | 0.539 / 0.578 |
| E_COMPLEMENT / NCE / cbramod / residual_pretrained_frozen / combined | 64 | 0.717 [+0.711, +0.723] | 0.520 [+0.512, +0.527] | – | – | 0.717 / 0.719 | 0.517 / 0.538 |
| E_COMPLEMENT / NCE / cbramod / residual_pretrained_frozen / local_only | 64 | 0.717 [+0.711, +0.723] | 0.522 [+0.515, +0.530] | – | – | 0.717 / 0.719 | 0.520 / 0.539 |
| E_COMPLEMENT / NCE / cbramod / residual_pretrained_peft / combined | 64 | 0.717 [+0.711, +0.723] | 0.522 [+0.514, +0.529] | – | – | 0.717 / 0.719 | 0.518 / 0.540 |
| E_COMPLEMENT / NCE / cbramod / residual_pretrained_peft / local_only | 64 | 0.717 [+0.711, +0.723] | 0.522 [+0.514, +0.530] | – | – | 0.717 / 0.719 | 0.520 / 0.539 |
| E_COMPLEMENT / NCE / cbramod / residual_random_trainable / combined | 64 | 0.717 [+0.711, +0.723] | 0.520 [+0.513, +0.527] | – | – | 0.717 / 0.719 | 0.517 / 0.538 |
| E_COMPLEMENT / NCE / cbramod / residual_random_trainable / local_only | 64 | 0.717 [+0.711, +0.723] | 0.522 [+0.514, +0.531] | – | – | 0.717 / 0.719 | 0.520 / 0.539 |
| E_COMPLEMENT / NCE / reve / residual_pretrained_frozen / combined | 64 | 0.717 [+0.711, +0.723] | 0.523 [+0.515, +0.531] | – | – | 0.717 / 0.719 | 0.519 / 0.544 |
| E_COMPLEMENT / NCE / reve / residual_pretrained_frozen / local_only | 64 | 0.717 [+0.711, +0.723] | 0.522 [+0.514, +0.530] | – | – | 0.717 / 0.719 | 0.520 / 0.539 |
| E_COMPLEMENT / NCE / reve / residual_pretrained_peft / combined | 64 | 0.717 [+0.711, +0.723] | 0.521 [+0.514, +0.528] | – | – | 0.717 / 0.719 | 0.518 / 0.540 |
| E_COMPLEMENT / NCE / reve / residual_pretrained_peft / local_only | 64 | 0.717 [+0.711, +0.723] | 0.522 [+0.515, +0.530] | – | – | 0.717 / 0.719 | 0.520 / 0.539 |
| E_COMPLEMENT / NCE / reve / residual_random_trainable / combined | 64 | 0.717 [+0.712, +0.723] | 0.521 [+0.514, +0.529] | – | – | 0.717 / 0.719 | 0.518 / 0.541 |
| E_COMPLEMENT / NCE / reve / residual_random_trainable / local_only | 64 | 0.717 [+0.711, +0.723] | 0.522 [+0.514, +0.530] | – | – | 0.717 / 0.719 | 0.520 / 0.539 |
| E_DISTILL / CS_SINGLE / auditory_adapted_teacher / early / chosen | 64 | 0.717 [+0.711, +0.724] | 0.518 [+0.510, +0.527] | -0.001 | 0.000 | 0.717 / 0.719 | 0.514 / 0.548 |
| E_DISTILL / CS_SINGLE / auditory_adapted_teacher / early / lambda0 | 64 | 0.718 [+0.711, +0.724] | 0.516 [+0.507, +0.524] | -0.001 | -0.000 | 0.717 / 0.720 | 0.513 / 0.531 |
| E_DISTILL / CS_SINGLE / auditory_adapted_teacher / full / chosen | 64 | 0.716 [+0.710, +0.722] | 0.539 [+0.529, +0.550] | -0.001 | 0.001 | 0.716 / 0.717 | 0.535 / 0.568 |
| E_DISTILL / CS_SINGLE / auditory_adapted_teacher / full / lambda0 | 64 | 0.716 [+0.711, +0.721] | 0.545 [+0.532, +0.557] | 0.000 | 0.002 | 0.716 / 0.715 | 0.539 / 0.579 |
| E_DISTILL / CS_SINGLE / auditory_adapted_teacher / late / chosen | 64 | 0.718 [+0.711, +0.724] | 0.519 [+0.511, +0.526] | -0.000 | 0.001 | 0.717 / 0.721 | 0.519 / 0.520 |
| E_DISTILL / CS_SINGLE / auditory_adapted_teacher / late / lambda0 | 64 | 0.718 [+0.711, +0.725] | 0.519 [+0.510, +0.527] | -0.000 | 0.001 | 0.717 / 0.720 | 0.518 / 0.525 |
| E_DISTILL / CS_SINGLE / generic_pretrained_teacher / early / chosen | 64 | 0.718 [+0.711, +0.724] | 0.519 [+0.510, +0.528] | -0.001 | -0.000 | 0.717 / 0.719 | 0.515 / 0.543 |
| E_DISTILL / CS_SINGLE / generic_pretrained_teacher / early / lambda0 | 64 | 0.717 [+0.711, +0.724] | 0.518 [+0.508, +0.528] | -0.001 | 0.000 | 0.717 / 0.719 | 0.515 / 0.534 |
| E_DISTILL / CS_SINGLE / generic_pretrained_teacher / full / chosen | 64 | 0.717 [+0.712, +0.722] | 0.535 [+0.523, +0.546] | -0.001 | 0.001 | 0.717 / 0.716 | 0.528 / 0.574 |
| E_DISTILL / CS_SINGLE / generic_pretrained_teacher / full / lambda0 | 64 | 0.716 [+0.711, +0.721] | 0.539 [+0.527, +0.551] | -0.001 | 0.001 | 0.716 / 0.716 | 0.535 / 0.563 |
| E_DISTILL / CS_SINGLE / generic_pretrained_teacher / late / chosen | 64 | 0.718 [+0.711, +0.725] | 0.517 [+0.510, +0.524] | -0.001 | 0.000 | 0.718 / 0.720 | 0.515 / 0.526 |
| E_DISTILL / CS_SINGLE / generic_pretrained_teacher / late / lambda0 | 64 | 0.718 [+0.711, +0.725] | 0.516 [+0.508, +0.524] | -0.000 | 0.001 | 0.717 / 0.721 | 0.515 / 0.519 |
| E_DISTILL / CS_SINGLE / legacy_full_teacher_control / early / chosen | 64 | 0.717 [+0.710, +0.724] | 0.523 [+0.514, +0.531] | -0.001 | 0.001 | 0.717 / 0.719 | 0.521 / 0.530 |
| E_DISTILL / CS_SINGLE / legacy_full_teacher_control / early / lambda0 | 64 | 0.717 [+0.711, +0.724] | 0.514 [+0.504, +0.523] | -0.002 | -0.001 | 0.717 / 0.720 | 0.514 / 0.515 |
| E_DISTILL / CS_SINGLE / legacy_full_teacher_control / full / chosen | 64 | 0.717 [+0.712, +0.722] | 0.536 [+0.525, +0.546] | -0.000 | 0.001 | 0.717 / 0.718 | 0.532 / 0.556 |
| E_DISTILL / CS_SINGLE / legacy_full_teacher_control / full / lambda0 | 64 | 0.716 [+0.710, +0.721] | 0.544 [+0.532, +0.557] | -0.000 | 0.001 | 0.716 / 0.714 | 0.539 / 0.574 |
| E_DISTILL / CS_SINGLE / legacy_full_teacher_control / late / chosen | 64 | 0.718 [+0.711, +0.724] | 0.521 [+0.513, +0.529] | -0.000 | 0.001 | 0.717 / 0.721 | 0.521 / 0.522 |
| E_DISTILL / CS_SINGLE / legacy_full_teacher_control / late / lambda0 | 64 | 0.718 [+0.711, +0.725] | 0.517 [+0.509, +0.525] | -0.001 | 0.001 | 0.718 / 0.721 | 0.517 / 0.520 |
| E_DISTILL / CS_SINGLE / local_teacher / early / chosen | 64 | 0.718 [+0.711, +0.724] | 0.514 [+0.505, +0.523] | -0.001 | -0.000 | 0.717 / 0.720 | 0.511 / 0.532 |
| E_DISTILL / CS_SINGLE / local_teacher / early / lambda0 | 64 | 0.718 [+0.712, +0.724] | 0.511 [+0.502, +0.519] | -0.002 | -0.001 | 0.718 / 0.720 | 0.510 / 0.516 |
| E_DISTILL / CS_SINGLE / local_teacher / full / chosen | 64 | 0.716 [+0.711, +0.722] | 0.539 [+0.527, +0.550] | -0.001 | 0.001 | 0.717 / 0.716 | 0.534 / 0.572 |
| E_DISTILL / CS_SINGLE / local_teacher / full / lambda0 | 64 | 0.716 [+0.711, +0.721] | 0.541 [+0.529, +0.553] | -0.000 | 0.001 | 0.716 / 0.716 | 0.537 / 0.568 |
| E_DISTILL / CS_SINGLE / local_teacher / late / chosen | 64 | 0.718 [+0.712, +0.724] | 0.521 [+0.512, +0.530] | -0.000 | 0.001 | 0.717 / 0.720 | 0.519 / 0.528 |
| E_DISTILL / CS_SINGLE / local_teacher / late / lambda0 | 64 | 0.718 [+0.711, +0.725] | 0.517 [+0.508, +0.525] | -0.000 | 0.001 | 0.718 / 0.721 | 0.516 / 0.521 |
| E_DISTILL / NCE / auditory_adapted_teacher / early / chosen | 64 | 0.718 [+0.711, +0.725] | 0.508 [+0.501, +0.514] | -0.000 | 0.000 | 0.717 / 0.721 | 0.505 / 0.524 |
| E_DISTILL / NCE / auditory_adapted_teacher / early / lambda0 | 64 | 0.718 [+0.711, +0.725] | 0.508 [+0.502, +0.515] | -0.000 | 0.000 | 0.717 / 0.721 | 0.506 / 0.521 |
| E_DISTILL / NCE / auditory_adapted_teacher / full / chosen | 64 | 0.718 [+0.713, +0.723] | 0.521 [+0.512, +0.531] | -0.001 | 0.001 | 0.717 / 0.720 | 0.519 / 0.538 |
| E_DISTILL / NCE / auditory_adapted_teacher / full / lambda0 | 64 | 0.717 [+0.712, +0.723] | 0.522 [+0.515, +0.530] | -0.001 | 0.001 | 0.717 / 0.719 | 0.520 / 0.539 |
| E_DISTILL / NCE / auditory_adapted_teacher / late / chosen | 64 | 0.718 [+0.712, +0.724] | 0.514 [+0.508, +0.521] | -0.001 | 0.000 | 0.717 / 0.720 | 0.514 / 0.519 |
| E_DISTILL / NCE / auditory_adapted_teacher / late / lambda0 | 64 | 0.718 [+0.711, +0.724] | 0.512 [+0.506, +0.518] | -0.000 | 0.000 | 0.717 / 0.720 | 0.511 / 0.517 |
| E_DISTILL / NCE / generic_pretrained_teacher / early / chosen | 64 | 0.718 [+0.711, +0.725] | 0.509 [+0.503, +0.516] | -0.000 | -0.000 | 0.717 / 0.721 | 0.507 / 0.527 |
| E_DISTILL / NCE / generic_pretrained_teacher / early / lambda0 | 64 | 0.718 [+0.711, +0.725] | 0.508 [+0.502, +0.515] | -0.000 | 0.000 | 0.717 / 0.720 | 0.506 / 0.525 |
| E_DISTILL / NCE / generic_pretrained_teacher / full / chosen | 64 | 0.718 [+0.713, +0.723] | 0.518 [+0.509, +0.528] | -0.001 | 0.001 | 0.718 / 0.720 | 0.515 / 0.539 |
| E_DISTILL / NCE / generic_pretrained_teacher / full / lambda0 | 64 | 0.717 [+0.711, +0.723] | 0.522 [+0.515, +0.530] | -0.001 | 0.001 | 0.717 / 0.719 | 0.520 / 0.539 |
| E_DISTILL / NCE / generic_pretrained_teacher / late / chosen | 64 | 0.718 [+0.712, +0.724] | 0.508 [+0.503, +0.513] | -0.000 | 0.000 | 0.718 / 0.721 | 0.508 / 0.510 |
| E_DISTILL / NCE / generic_pretrained_teacher / late / lambda0 | 64 | 0.718 [+0.712, +0.724] | 0.512 [+0.506, +0.518] | -0.000 | 0.000 | 0.717 / 0.720 | 0.511 / 0.518 |
| E_DISTILL / NCE / legacy_full_teacher_control / early / chosen | 64 | 0.718 [+0.711, +0.725] | 0.504 [+0.497, +0.511] | -0.001 | -0.000 | 0.718 / 0.721 | 0.503 / 0.513 |
| E_DISTILL / NCE / legacy_full_teacher_control / early / lambda0 | 64 | 0.718 [+0.711, +0.725] | 0.509 [+0.502, +0.515] | -0.000 | 0.000 | 0.717 / 0.720 | 0.506 / 0.523 |
| E_DISTILL / NCE / legacy_full_teacher_control / full / chosen | 64 | 0.718 [+0.712, +0.723] | 0.520 [+0.511, +0.529] | -0.001 | 0.001 | 0.717 / 0.720 | 0.518 / 0.532 |
| E_DISTILL / NCE / legacy_full_teacher_control / full / lambda0 | 64 | 0.717 [+0.711, +0.723] | 0.522 [+0.515, +0.530] | -0.001 | 0.001 | 0.717 / 0.719 | 0.520 / 0.539 |
| E_DISTILL / NCE / legacy_full_teacher_control / late / chosen | 64 | 0.718 [+0.712, +0.724] | 0.508 [+0.503, +0.514] | -0.000 | 0.000 | 0.718 / 0.721 | 0.508 / 0.510 |
| E_DISTILL / NCE / legacy_full_teacher_control / late / lambda0 | 64 | 0.718 [+0.712, +0.724] | 0.512 [+0.506, +0.518] | -0.000 | 0.000 | 0.717 / 0.720 | 0.511 / 0.517 |
| E_DISTILL / NCE / local_teacher / early / chosen | 64 | 0.718 [+0.711, +0.725] | 0.510 [+0.503, +0.517] | -0.001 | -0.000 | 0.717 / 0.721 | 0.508 / 0.522 |
| E_DISTILL / NCE / local_teacher / early / lambda0 | 64 | 0.718 [+0.711, +0.725] | 0.508 [+0.502, +0.515] | -0.000 | 0.000 | 0.717 / 0.721 | 0.506 / 0.521 |
| E_DISTILL / NCE / local_teacher / full / chosen | 64 | 0.718 [+0.712, +0.723] | 0.523 [+0.513, +0.532] | -0.001 | 0.000 | 0.717 / 0.719 | 0.520 / 0.541 |
| E_DISTILL / NCE / local_teacher / full / lambda0 | 64 | 0.717 [+0.711, +0.723] | 0.522 [+0.514, +0.530] | -0.001 | 0.001 | 0.717 / 0.719 | 0.520 / 0.539 |
| E_DISTILL / NCE / local_teacher / late / chosen | 64 | 0.718 [+0.712, +0.724] | 0.513 [+0.507, +0.520] | -0.000 | 0.000 | 0.717 / 0.720 | 0.512 / 0.520 |
| E_DISTILL / NCE / local_teacher / late / lambda0 | 64 | 0.718 [+0.712, +0.724] | 0.512 [+0.506, +0.518] | -0.000 | 0.000 | 0.717 / 0.720 | 0.511 / 0.517 |
| E_GENERIC / CS_SINGLE / cbramod / pretrained_frozen | 64 | 0.718 [+0.711, +0.725] | 0.518 [+0.509, +0.527] | -0.001 | 0.001 | 0.718 / 0.720 | 0.516 / 0.531 |
| E_GENERIC / CS_SINGLE / cbramod / pretrained_full | 64 | 0.715 [+0.710, +0.720] | 0.549 [+0.533, +0.564] | 0.001 | 0.003 | 0.715 / 0.716 | 0.543 / 0.583 |
| E_GENERIC / CS_SINGLE / cbramod / pretrained_partial | 64 | 0.718 [+0.711, +0.724] | 0.526 [+0.516, +0.536] | -0.000 | 0.001 | 0.717 / 0.719 | 0.523 / 0.543 |
| E_GENERIC / CS_SINGLE / cbramod / pretrained_peft | 64 | 0.715 [+0.710, +0.720] | 0.549 [+0.534, +0.564] | 0.000 | 0.003 | 0.715 / 0.715 | 0.544 / 0.579 |
| E_GENERIC / CS_SINGLE / cbramod / random_full | 64 | 0.717 [+0.711, +0.723] | 0.526 [+0.515, +0.537] | -0.001 | 0.001 | 0.717 / 0.719 | 0.524 / 0.542 |
| E_GENERIC / CS_SINGLE / reve / pretrained_frozen | 64 | 0.721 [+0.717, +0.725] | 0.524 [+0.515, +0.534] | -0.003 | -0.000 | 0.721 / 0.722 | 0.520 / 0.547 |
| E_GENERIC / CS_SINGLE / reve / pretrained_full | 64 | 0.719 [+0.714, +0.724] | 0.525 [+0.516, +0.533] | -0.003 | 0.000 | 0.719 / 0.719 | 0.522 / 0.542 |
| E_GENERIC / CS_SINGLE / reve / pretrained_partial | 64 | 0.728 [+0.722, +0.733] | 0.509 [+0.503, +0.516] | -0.004 | 0.001 | 0.728 / 0.728 | 0.508 / 0.519 |
| E_GENERIC / CS_SINGLE / reve / pretrained_peft | 64 | 0.722 [+0.717, +0.727] | 0.518 [+0.507, +0.529] | -0.003 | 0.000 | 0.722 / 0.725 | 0.517 / 0.526 |
| E_GENERIC / CS_SINGLE / reve / random_full | 64 | 0.811 [+0.803, +0.818] | 0.499 [+0.493, +0.505] | -0.003 | -0.000 | 0.810 / 0.816 | 0.499 / 0.497 |
| E_GENERIC / NCE / cbramod / pretrained_frozen | 64 | 0.717 [+0.710, +0.724] | 0.525 [+0.517, +0.533] | -0.000 | 0.000 | 0.717 / 0.720 | 0.524 / 0.533 |
| E_GENERIC / NCE / cbramod / pretrained_full | 64 | 0.718 [+0.712, +0.724] | 0.517 [+0.508, +0.527] | -0.001 | 0.000 | 0.718 / 0.717 | 0.513 / 0.546 |
| E_GENERIC / NCE / cbramod / pretrained_partial | 64 | 0.715 [+0.710, +0.720] | 0.547 [+0.534, +0.561] | 0.001 | 0.001 | 0.715 / 0.715 | 0.543 / 0.572 |
| E_GENERIC / NCE / cbramod / pretrained_peft | 64 | 0.717 [+0.712, +0.723] | 0.527 [+0.516, +0.537] | 0.000 | 0.000 | 0.717 / 0.721 | 0.523 / 0.549 |
| E_GENERIC / NCE / cbramod / random_full | 64 | 0.718 [+0.711, +0.724] | 0.511 [+0.505, +0.518] | -0.002 | 0.001 | 0.717 / 0.720 | 0.510 / 0.522 |
| E_GENERIC / NCE / reve / pretrained_frozen | 64 | 0.717 [+0.711, +0.723] | 0.526 [+0.517, +0.535] | 0.000 | 0.001 | 0.717 / 0.718 | 0.523 / 0.545 |
| E_GENERIC / NCE / reve / pretrained_full | 64 | 0.718 [+0.711, +0.724] | 0.518 [+0.512, +0.525] | -0.002 | 0.002 | 0.717 / 0.720 | 0.517 / 0.526 |
| E_GENERIC / NCE / reve / pretrained_partial | 64 | 0.718 [+0.712, +0.724] | 0.506 [+0.500, +0.513] | -0.003 | 0.000 | 0.717 / 0.721 | 0.505 / 0.514 |
| E_GENERIC / NCE / reve / pretrained_peft | 64 | 0.718 [+0.712, +0.723] | 0.520 [+0.511, +0.529] | -0.002 | -0.000 | 0.717 / 0.718 | 0.517 / 0.536 |
| E_GENERIC / NCE / reve / random_full | 64 | 0.718 [+0.712, +0.724] | 0.509 [+0.502, +0.516] | -0.002 | 0.001 | 0.717 / 0.721 | 0.509 / 0.512 |
| E_GX / GX_NATIVE / GX / early | 64 | 0.717 [+0.711, +0.724] | 0.517 [+0.507, +0.527] | -0.002 | 0.001 | 0.717 / 0.719 | 0.512 / 0.544 |
| E_GX / GX_NATIVE / GX / full | 64 | 0.714 [+0.710, +0.719] | 0.553 [+0.538, +0.568] | -0.007 | 0.004 | 0.714 / 0.714 | 0.548 / 0.584 |
| E_GX / GX_NATIVE / GX / joint | 64 | 0.716 [+0.711, +0.722] | 0.537 [+0.524, +0.551] | -0.001 | 0.001 | 0.716 / 0.717 | 0.533 / 0.565 |
| E_GX / GX_NATIVE / GX / late | 64 | 0.717 [+0.711, +0.724] | 0.526 [+0.517, +0.536] | -0.002 | 0.002 | 0.717 / 0.721 | 0.526 / 0.524 |
| E_LOCAL / CS_SINGLE / density_tokens / early | 64 | 0.719 [+0.713, +0.725] | 0.507 [+0.499, +0.515] | -0.003 | 0.000 | 0.718 / 0.723 | 0.508 / 0.504 |
| E_LOCAL / CS_SINGLE / density_tokens / full | 64 | 0.716 [+0.711, +0.722] | 0.537 [+0.527, +0.548] | 0.000 | 0.001 | 0.716 / 0.718 | 0.535 / 0.555 |
| E_LOCAL / CS_SINGLE / density_tokens / joint | 64 | 0.719 [+0.713, +0.724] | 0.515 [+0.506, +0.524] | -0.003 | 0.001 | 0.718 / 0.721 | 0.515 / 0.517 |
| E_LOCAL / CS_SINGLE / density_tokens / late | 64 | 0.718 [+0.712, +0.725] | 0.508 [+0.501, +0.515] | -0.001 | 0.001 | 0.718 / 0.720 | 0.506 / 0.523 |
| E_LOCAL / CS_SINGLE / lag_local_tokens / early | 64 | 0.718 [+0.711, +0.724] | 0.515 [+0.507, +0.523] | -0.001 | 0.000 | 0.717 / 0.719 | 0.512 / 0.530 |
| E_LOCAL / CS_SINGLE / lag_local_tokens / full | 64 | 0.716 [+0.710, +0.721] | 0.544 [+0.532, +0.557] | 0.000 | 0.002 | 0.716 / 0.715 | 0.539 / 0.578 |
| E_LOCAL / CS_SINGLE / lag_local_tokens / joint | 64 | 0.717 [+0.712, +0.723] | 0.526 [+0.516, +0.536] | -0.001 | -0.000 | 0.717 / 0.719 | 0.522 / 0.551 |
| E_LOCAL / CS_SINGLE / lag_local_tokens / late | 64 | 0.718 [+0.711, +0.725] | 0.516 [+0.508, +0.524] | -0.000 | 0.001 | 0.718 / 0.721 | 0.516 / 0.519 |
| E_LOCAL / CS_SINGLE / legacy_pool4 / early | 64 | 0.718 [+0.711, +0.725] | 0.507 [+0.500, +0.513] | -0.003 | 0.000 | 0.718 / 0.720 | 0.505 / 0.516 |
| E_LOCAL / CS_SINGLE / legacy_pool4 / full | 64 | 0.716 [+0.711, +0.722] | 0.538 [+0.527, +0.549] | -0.002 | 0.001 | 0.716 / 0.716 | 0.535 / 0.559 |
| E_LOCAL / CS_SINGLE / legacy_pool4 / joint | 64 | 0.719 [+0.714, +0.724] | 0.512 [+0.504, +0.521] | -0.003 | -0.001 | 0.719 / 0.719 | 0.508 / 0.539 |
| E_LOCAL / CS_SINGLE / legacy_pool4 / late | 64 | 0.719 [+0.712, +0.726] | 0.506 [+0.499, +0.512] | -0.001 | 0.002 | 0.718 / 0.723 | 0.506 / 0.501 |
| E_LOCAL / NCE / density_tokens / early | 64 | 0.718 [+0.711, +0.724] | 0.501 [+0.495, +0.508] | -0.001 | 0.000 | 0.717 / 0.721 | 0.503 / 0.489 |
| E_LOCAL / NCE / density_tokens / full | 64 | 0.717 [+0.711, +0.724] | 0.519 [+0.511, +0.528] | -0.001 | 0.001 | 0.717 / 0.720 | 0.521 / 0.513 |
| E_LOCAL / NCE / density_tokens / joint | 64 | 0.718 [+0.711, +0.724] | 0.507 [+0.501, +0.513] | -0.001 | 0.002 | 0.717 / 0.720 | 0.505 / 0.515 |
| E_LOCAL / NCE / density_tokens / late | 64 | 0.718 [+0.711, +0.726] | 0.496 [+0.489, +0.502] | -0.001 | 0.001 | 0.718 / 0.721 | 0.496 / 0.495 |
| E_LOCAL / NCE / lag_local_tokens / early | 64 | 0.718 [+0.711, +0.725] | 0.508 [+0.501, +0.515] | -0.000 | 0.000 | 0.717 / 0.720 | 0.506 / 0.522 |
| E_LOCAL / NCE / lag_local_tokens / full | 64 | 0.717 [+0.711, +0.723] | 0.522 [+0.515, +0.530] | -0.001 | 0.001 | 0.717 / 0.719 | 0.520 / 0.539 |
| E_LOCAL / NCE / lag_local_tokens / joint | 64 | 0.718 [+0.711, +0.724] | 0.514 [+0.506, +0.521] | -0.000 | 0.001 | 0.717 / 0.720 | 0.513 / 0.516 |
| E_LOCAL / NCE / lag_local_tokens / late | 64 | 0.718 [+0.712, +0.724] | 0.512 [+0.506, +0.518] | -0.000 | 0.000 | 0.717 / 0.720 | 0.511 / 0.517 |
| E_LOCAL / NCE / legacy_pool4 / early | 64 | 0.718 [+0.711, +0.725] | 0.504 [+0.497, +0.510] | -0.002 | -0.001 | 0.717 / 0.721 | 0.505 / 0.498 |
| E_LOCAL / NCE / legacy_pool4 / full | 64 | 0.718 [+0.711, +0.725] | 0.505 [+0.499, +0.512] | -0.002 | 0.000 | 0.718 / 0.721 | 0.504 / 0.515 |
| E_LOCAL / NCE / legacy_pool4 / joint | 64 | 0.718 [+0.711, +0.725] | 0.497 [+0.490, +0.504] | -0.002 | -0.000 | 0.718 / 0.720 | 0.495 / 0.509 |
| E_LOCAL / NCE / legacy_pool4 / late | 64 | 0.718 [+0.711, +0.725] | 0.499 [+0.493, +0.504] | -0.002 | -0.000 | 0.717 / 0.721 | 0.498 / 0.505 |
| E_PUBLIC_TRANSFER / CS_SINGLE / cbramod / task_full | 64 | 0.715 [+0.710, +0.720] | 0.549 [+0.535, +0.563] | 0.001 | 0.002 | 0.716 / 0.714 | 0.543 / 0.583 |
| E_PUBLIC_TRANSFER / CS_SINGLE / cbramod / task_partial | 64 | 0.715 [+0.710, +0.720] | 0.549 [+0.535, +0.564] | 0.000 | 0.002 | 0.715 / 0.714 | 0.544 / 0.583 |
| E_PUBLIC_TRANSFER / CS_SINGLE / lag_local_tokens / task_full | 64 | 0.716 [+0.711, +0.721] | 0.542 [+0.529, +0.555] | 0.000 | 0.002 | 0.716 / 0.715 | 0.537 / 0.576 |
| E_PUBLIC_TRANSFER / CS_SINGLE / lag_local_tokens / task_partial | 64 | 0.716 [+0.711, +0.721] | 0.545 [+0.531, +0.558] | -0.000 | 0.001 | 0.716 / 0.716 | 0.541 / 0.568 |
| E_PUBLIC_TRANSFER / CS_SINGLE / reve / task_full | 64 | 0.718 [+0.711, +0.724] | 0.516 [+0.508, +0.523] | -0.001 | 0.000 | 0.717 / 0.721 | 0.516 / 0.514 |
| E_PUBLIC_TRANSFER / CS_SINGLE / reve / task_partial | 64 | 0.718 [+0.711, +0.725] | 0.506 [+0.500, +0.512] | -0.001 | 0.001 | 0.717 / 0.721 | 0.506 / 0.507 |
| E_PUBLIC_TRANSFER / NCE / cbramod / task_full | 64 | 0.718 [+0.711, +0.724] | 0.514 [+0.506, +0.522] | -0.002 | 0.001 | 0.717 / 0.720 | 0.512 / 0.523 |
| E_PUBLIC_TRANSFER / NCE / cbramod / task_partial | 64 | 0.716 [+0.711, +0.722] | 0.532 [+0.522, +0.542] | 0.001 | 0.001 | 0.716 / 0.717 | 0.528 / 0.557 |
| E_PUBLIC_TRANSFER / NCE / lag_local_tokens / task_full | 64 | 0.717 [+0.712, +0.723] | 0.523 [+0.514, +0.532] | -0.001 | 0.001 | 0.717 / 0.719 | 0.521 / 0.533 |
| E_PUBLIC_TRANSFER / NCE / lag_local_tokens / task_partial | 64 | 0.717 [+0.712, +0.722] | 0.528 [+0.516, +0.540] | -0.000 | 0.000 | 0.717 / 0.718 | 0.523 / 0.555 |
| E_PUBLIC_TRANSFER / NCE / reve / task_full | 64 | 0.718 [+0.711, +0.724] | 0.515 [+0.509, +0.521] | -0.003 | 0.001 | 0.717 / 0.721 | 0.515 / 0.513 |
| E_PUBLIC_TRANSFER / NCE / reve / task_partial | 64 | 0.718 [+0.711, +0.724] | 0.506 [+0.499, +0.514] | -0.002 | 0.002 | 0.717 / 0.721 | 0.507 / 0.502 |

## 2. Generic FM: `random_full` → `pretrained_*` (full = matched-update initialization contrast; others recipe)

> Label superseded by [CORRECTION_01](CORRECTION_01_FULL_UPDATE_LABEL.md): the `full` row is a recipe contrast, not a matched-update initialization contrast; values unchanged.

**NCE · cbramod · NLL** (critical value 2.55)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | recipe | 64 | +0.001 | [-0.000, +0.001] | [-0.000, +0.001] | contains 0 | +0.002 | -0.000 |
| pretrained_peft | recipe | 64 | +0.000 | [-0.001, +0.001] | [-0.001, +0.002] | contains 0 | +0.002 | -0.000 |
| pretrained_partial | recipe | 64 | +0.003 | [+0.001, +0.005] | [+0.001, +0.006] | I>0 | +0.003 | +0.001 |
| pretrained_full | initialization (matched full update) | 64 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.001 | -0.000 |

**NCE · cbramod · AUC** (critical value 2.54)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | recipe | 64 | +0.014 | [+0.005, +0.022] | [+0.003, +0.024] | I>0 | +0.002 | -0.000 |
| pretrained_peft | recipe | 64 | +0.015 | [+0.005, +0.025] | [+0.003, +0.028] | I>0 | +0.002 | -0.000 |
| pretrained_partial | recipe | 64 | +0.036 | [+0.023, +0.049] | [+0.020, +0.052] | I>0 | +0.003 | +0.001 |
| pretrained_full | initialization (matched full update) | 64 | +0.006 | [-0.003, +0.016] | [-0.006, +0.018] | contains 0 | +0.001 | -0.000 |

**NCE · reve · NLL** (critical value 2.58)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | recipe | 64 | +0.001 | [-0.000, +0.001] | [-0.001, +0.002] | contains 0 | +0.002 | +0.000 |
| pretrained_peft | recipe | 64 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.001 | -0.001 |
| pretrained_partial | recipe | 64 | -0.000 | [-0.001, +0.000] | [-0.001, +0.000] | contains 0 | -0.001 | -0.000 |
| pretrained_full | initialization (matched full update) | 64 | +0.000 | [-0.000, +0.001] | [-0.000, +0.001] | contains 0 | -0.001 | +0.001 |

**NCE · reve · AUC** (critical value 2.54)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | recipe | 64 | +0.017 | [+0.010, +0.025] | [+0.007, +0.027] | I>0 | +0.002 | +0.000 |
| pretrained_peft | recipe | 64 | +0.011 | [+0.002, +0.020] | [-0.001, +0.022] | contains 0 | -0.001 | -0.001 |
| pretrained_partial | recipe | 64 | -0.003 | [-0.012, +0.006] | [-0.014, +0.009] | contains 0 | -0.001 | -0.000 |
| pretrained_full | initialization (matched full update) | 64 | +0.009 | [+0.001, +0.018] | [-0.001, +0.020] | contains 0 | -0.001 | +0.001 |

**CS_SINGLE · cbramod · NLL** (critical value 2.43)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | recipe | 64 | -0.001 | [-0.002, -0.000] | [-0.002, -0.000] | I<0 | +0.001 | -0.001 |
| pretrained_peft | recipe | 64 | +0.002 | [+0.000, +0.003] | [+0.000, +0.003] | I>0 | +0.002 | +0.001 |
| pretrained_partial | recipe | 64 | -0.001 | [-0.002, +0.000] | [-0.002, +0.001] | contains 0 | +0.001 | -0.000 |
| pretrained_full | initialization (matched full update) | 64 | +0.002 | [+0.000, +0.003] | [-0.000, +0.004] | contains 0 | +0.002 | +0.001 |

**CS_SINGLE · cbramod · AUC** (critical value 2.42)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | recipe | 64 | -0.008 | [-0.017, +0.001] | [-0.019, +0.003] | contains 0 | +0.001 | -0.001 |
| pretrained_peft | recipe | 64 | +0.022 | [+0.012, +0.033] | [+0.010, +0.035] | I>0 | +0.002 | +0.001 |
| pretrained_partial | recipe | 64 | -0.000 | [-0.009, +0.009] | [-0.011, +0.010] | contains 0 | +0.001 | -0.000 |
| pretrained_full | initialization (matched full update) | 64 | +0.022 | [+0.012, +0.033] | [+0.010, +0.035] | I>0 | +0.002 | +0.001 |

**CS_SINGLE · reve · NLL** (critical value 2.25)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | recipe | 64 | +0.090 | [+0.084, +0.095] | [+0.083, +0.096] | I>0 | +0.000 | +0.000 |
| pretrained_peft | recipe | 64 | +0.089 | [+0.082, +0.095] | [+0.082, +0.096] | I>0 | +0.001 | +0.000 |
| pretrained_partial | recipe | 64 | +0.083 | [+0.078, +0.088] | [+0.077, +0.089] | I>0 | -0.000 | +0.001 |
| pretrained_full | initialization (matched full update) | 64 | +0.092 | [+0.086, +0.097] | [+0.086, +0.098] | I>0 | +0.000 | +0.000 |

**CS_SINGLE · reve · AUC** (critical value 2.49)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | recipe | 64 | +0.026 | [+0.015, +0.036] | [+0.012, +0.039] | I>0 | +0.000 | +0.000 |
| pretrained_peft | recipe | 64 | +0.019 | [+0.007, +0.031] | [+0.005, +0.034] | I>0 | +0.001 | +0.000 |
| pretrained_partial | recipe | 64 | +0.011 | [+0.002, +0.019] | [-0.000, +0.021] | contains 0 | -0.000 | +0.001 |
| pretrained_full | initialization (matched full update) | 64 | +0.026 | [+0.016, +0.036] | [+0.013, +0.039] | I>0 | +0.000 | +0.000 |

## 3. vs the local model: E_LOCAL `lag_local_tokens` full → E_GENERIC / E_PUBLIC_TRANSFER configuration

**NCE · NLL** (critical value 3.01)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| generic/cbramod/random_full | vs local | 64 | -0.001 | [-0.001, +0.000] | [-0.002, +0.000] | contains 0 | -0.001 | -0.001 |
| generic/cbramod/pretrained_frozen | vs local | 64 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.001 | -0.001 |
| generic/cbramod/pretrained_peft | vs local | 64 | -0.000 | [-0.001, +0.001] | [-0.002, +0.001] | contains 0 | +0.001 | -0.001 |
| generic/cbramod/pretrained_partial | vs local | 64 | +0.002 | [+0.001, +0.004] | [-0.000, +0.005] | contains 0 | +0.002 | +0.000 |
| generic/cbramod/pretrained_full | vs local | 64 | -0.000 | [-0.001, +0.000] | [-0.002, +0.001] | contains 0 | -0.000 | -0.001 |
| generic/reve/random_full | vs local | 64 | -0.001 | [-0.001, +0.000] | [-0.002, +0.000] | contains 0 | -0.001 | -0.000 |
| generic/reve/pretrained_frozen | vs local | 64 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.001 | -0.000 |
| generic/reve/pretrained_peft | vs local | 64 | -0.000 | [-0.001, +0.001] | [-0.002, +0.001] | contains 0 | -0.001 | -0.002 |
| generic/reve/pretrained_partial | vs local | 64 | -0.001 | [-0.002, -0.000] | [-0.002, +0.000] | contains 0 | -0.002 | -0.001 |
| generic/reve/pretrained_full | vs local | 64 | -0.000 | [-0.001, +0.000] | [-0.001, +0.001] | contains 0 | -0.002 | +0.001 |
| transfer/lag_local_tokens/task_partial | vs local | 64 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | -0.001 |
| transfer/lag_local_tokens/task_full | vs local | 64 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | -0.001 |
| transfer/cbramod/task_partial | vs local | 64 | +0.001 | [-0.000, +0.002] | [-0.000, +0.002] | contains 0 | +0.002 | -0.000 |
| transfer/cbramod/task_full | vs local | 64 | -0.000 | [-0.001, +0.000] | [-0.002, +0.001] | contains 0 | -0.001 | +0.000 |
| transfer/reve/task_partial | vs local | 64 | -0.001 | [-0.001, +0.000] | [-0.002, +0.001] | contains 0 | -0.001 | +0.001 |
| transfer/reve/task_full | vs local | 64 | -0.000 | [-0.001, +0.000] | [-0.001, +0.001] | contains 0 | -0.002 | +0.000 |

**NCE · AUC** (critical value 3.00)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| generic/cbramod/random_full | vs local | 64 | -0.011 | [-0.020, -0.002] | [-0.024, +0.002] | contains 0 | -0.001 | -0.001 |
| generic/cbramod/pretrained_frozen | vs local | 64 | +0.003 | [-0.007, +0.012] | [-0.012, +0.017] | contains 0 | +0.001 | -0.001 |
| generic/cbramod/pretrained_peft | vs local | 64 | +0.004 | [-0.006, +0.014] | [-0.010, +0.019] | contains 0 | +0.001 | -0.001 |
| generic/cbramod/pretrained_partial | vs local | 64 | +0.025 | [+0.014, +0.035] | [+0.009, +0.040] | I>0 | +0.002 | +0.000 |
| generic/cbramod/pretrained_full | vs local | 64 | -0.005 | [-0.015, +0.005] | [-0.020, +0.010] | contains 0 | -0.000 | -0.001 |
| generic/reve/random_full | vs local | 64 | -0.013 | [-0.022, -0.004] | [-0.026, -0.000] | I<0 | -0.001 | -0.000 |
| generic/reve/pretrained_frozen | vs local | 64 | +0.004 | [-0.004, +0.012] | [-0.008, +0.016] | contains 0 | +0.001 | -0.000 |
| generic/reve/pretrained_peft | vs local | 64 | -0.003 | [-0.012, +0.007] | [-0.017, +0.012] | contains 0 | -0.001 | -0.002 |
| generic/reve/pretrained_partial | vs local | 64 | -0.016 | [-0.026, -0.006] | [-0.031, -0.001] | I<0 | -0.002 | -0.001 |
| generic/reve/pretrained_full | vs local | 64 | -0.004 | [-0.012, +0.004] | [-0.016, +0.008] | contains 0 | -0.002 | +0.001 |
| transfer/lag_local_tokens/task_partial | vs local | 64 | +0.005 | [-0.003, +0.013] | [-0.007, +0.017] | contains 0 | +0.000 | -0.001 |
| transfer/lag_local_tokens/task_full | vs local | 64 | +0.000 | [-0.006, +0.007] | [-0.010, +0.011] | contains 0 | +0.000 | -0.001 |
| transfer/cbramod/task_partial | vs local | 64 | +0.010 | [+0.001, +0.018] | [-0.003, +0.022] | contains 0 | +0.002 | -0.000 |
| transfer/cbramod/task_full | vs local | 64 | -0.009 | [-0.018, +0.001] | [-0.023, +0.006] | contains 0 | -0.001 | +0.000 |
| transfer/reve/task_partial | vs local | 64 | -0.016 | [-0.026, -0.006] | [-0.031, -0.001] | I<0 | -0.001 | +0.001 |
| transfer/reve/task_full | vs local | 64 | -0.007 | [-0.015, +0.000] | [-0.019, +0.004] | contains 0 | -0.002 | +0.000 |

**CS_SINGLE · NLL** (critical value 3.12)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| generic/cbramod/random_full | vs local | 64 | -0.001 | [-0.002, +0.000] | [-0.003, +0.001] | contains 0 | -0.002 | -0.000 |
| generic/cbramod/pretrained_frozen | vs local | 64 | -0.002 | [-0.003, -0.001] | [-0.004, -0.000] | I<0 | -0.001 | -0.001 |
| generic/cbramod/pretrained_peft | vs local | 64 | +0.001 | [-0.000, +0.002] | [-0.001, +0.002] | contains 0 | -0.000 | +0.001 |
| generic/cbramod/pretrained_partial | vs local | 64 | -0.002 | [-0.003, -0.001] | [-0.003, -0.000] | I<0 | -0.001 | -0.000 |
| generic/cbramod/pretrained_full | vs local | 64 | +0.001 | [-0.000, +0.002] | [-0.001, +0.002] | contains 0 | +0.000 | +0.001 |
| generic/reve/random_full | vs local | 64 | -0.095 | [-0.100, -0.089] | [-0.103, -0.086] | I<0 | -0.004 | -0.002 |
| generic/reve/pretrained_frozen | vs local | 64 | -0.005 | [-0.007, -0.003] | [-0.008, -0.003] | I<0 | -0.004 | -0.002 |
| generic/reve/pretrained_peft | vs local | 64 | -0.006 | [-0.009, -0.004] | [-0.010, -0.002] | I<0 | -0.003 | -0.001 |
| generic/reve/pretrained_partial | vs local | 64 | -0.012 | [-0.014, -0.010] | [-0.015, -0.008] | I<0 | -0.004 | -0.001 |
| generic/reve/pretrained_full | vs local | 64 | -0.003 | [-0.004, -0.002] | [-0.005, -0.001] | I<0 | -0.004 | -0.002 |
| transfer/lag_local_tokens/task_partial | vs local | 64 | -0.000 | [-0.001, +0.001] | [-0.002, +0.001] | contains 0 | -0.000 | -0.000 |
| transfer/lag_local_tokens/task_full | vs local | 64 | -0.000 | [-0.001, +0.001] | [-0.002, +0.001] | contains 0 | -0.000 | +0.001 |
| transfer/cbramod/task_partial | vs local | 64 | +0.001 | [-0.000, +0.002] | [-0.001, +0.002] | contains 0 | -0.000 | +0.000 |
| transfer/cbramod/task_full | vs local | 64 | +0.000 | [-0.001, +0.002] | [-0.001, +0.002] | contains 0 | +0.000 | +0.000 |
| transfer/reve/task_partial | vs local | 64 | -0.002 | [-0.003, -0.001] | [-0.004, +0.000] | contains 0 | -0.002 | -0.000 |
| transfer/reve/task_full | vs local | 64 | -0.002 | [-0.003, -0.001] | [-0.004, +0.000] | contains 0 | -0.001 | -0.001 |

**CS_SINGLE · AUC** (critical value 3.02)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| generic/cbramod/random_full | vs local | 64 | -0.018 | [-0.027, -0.009] | [-0.031, -0.005] | I<0 | -0.002 | -0.000 |
| generic/cbramod/pretrained_frozen | vs local | 64 | -0.026 | [-0.036, -0.017] | [-0.041, -0.011] | I<0 | -0.001 | -0.001 |
| generic/cbramod/pretrained_peft | vs local | 64 | +0.004 | [-0.003, +0.012] | [-0.007, +0.016] | contains 0 | -0.000 | +0.001 |
| generic/cbramod/pretrained_partial | vs local | 64 | -0.018 | [-0.026, -0.010] | [-0.031, -0.006] | I<0 | -0.001 | -0.000 |
| generic/cbramod/pretrained_full | vs local | 64 | +0.004 | [-0.003, +0.012] | [-0.007, +0.015] | contains 0 | +0.000 | +0.001 |
| generic/reve/random_full | vs local | 64 | -0.046 | [-0.059, -0.032] | [-0.066, -0.025] | I<0 | -0.004 | -0.002 |
| generic/reve/pretrained_frozen | vs local | 64 | -0.020 | [-0.027, -0.013] | [-0.031, -0.009] | I<0 | -0.004 | -0.002 |
| generic/reve/pretrained_peft | vs local | 64 | -0.026 | [-0.037, -0.015] | [-0.043, -0.010] | I<0 | -0.003 | -0.001 |
| generic/reve/pretrained_partial | vs local | 64 | -0.035 | [-0.047, -0.023] | [-0.053, -0.017] | I<0 | -0.004 | -0.001 |
| generic/reve/pretrained_full | vs local | 64 | -0.020 | [-0.029, -0.011] | [-0.034, -0.006] | I<0 | -0.004 | -0.002 |
| transfer/lag_local_tokens/task_partial | vs local | 64 | +0.000 | [-0.006, +0.007] | [-0.010, +0.010] | contains 0 | -0.000 | -0.000 |
| transfer/lag_local_tokens/task_full | vs local | 64 | -0.002 | [-0.008, +0.004] | [-0.011, +0.007] | contains 0 | -0.000 | +0.001 |
| transfer/cbramod/task_partial | vs local | 64 | +0.005 | [-0.002, +0.012] | [-0.006, +0.015] | contains 0 | -0.000 | +0.000 |
| transfer/cbramod/task_full | vs local | 64 | +0.004 | [-0.002, +0.011] | [-0.005, +0.014] | contains 0 | +0.000 | +0.000 |
| transfer/reve/task_partial | vs local | 64 | -0.038 | [-0.049, -0.027] | [-0.055, -0.021] | I<0 | -0.002 | -0.000 |
| transfer/reve/task_full | vs local | 64 | -0.029 | [-0.042, -0.016] | [-0.048, -0.009] | I<0 | -0.001 | -0.001 |

## 4. Public auditory transfer vs the non-transferred twin

**NCE · NLL** (critical value 2.67)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| transfer/lag_local_tokens/task_partial | transfer vs non-transferred twin | 64 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | -0.001 |
| transfer/lag_local_tokens/task_full | transfer vs non-transferred twin | 64 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | -0.001 |
| transfer/cbramod/task_partial | transfer vs non-transferred twin | 64 | -0.002 | [-0.003, -0.000] | [-0.003, +0.000] | contains 0 | -0.000 | -0.000 |
| transfer/cbramod/task_full | transfer vs non-transferred twin | 64 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | +0.001 |
| transfer/reve/task_partial | transfer vs non-transferred twin | 64 | +0.000 | [-0.000, +0.001] | [-0.000, +0.001] | contains 0 | +0.000 | +0.002 |
| transfer/reve/task_full | transfer vs non-transferred twin | 64 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.001 | -0.001 |

**NCE · AUC** (critical value 2.72)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| transfer/lag_local_tokens/task_partial | transfer vs non-transferred twin | 64 | +0.005 | [-0.003, +0.014] | [-0.006, +0.016] | contains 0 | +0.000 | -0.001 |
| transfer/lag_local_tokens/task_full | transfer vs non-transferred twin | 64 | +0.000 | [-0.007, +0.007] | [-0.009, +0.010] | contains 0 | +0.000 | -0.001 |
| transfer/cbramod/task_partial | transfer vs non-transferred twin | 64 | -0.015 | [-0.023, -0.006] | [-0.027, -0.003] | I<0 | -0.000 | -0.000 |
| transfer/cbramod/task_full | transfer vs non-transferred twin | 64 | -0.004 | [-0.015, +0.007] | [-0.018, +0.011] | contains 0 | -0.000 | +0.001 |
| transfer/reve/task_partial | transfer vs non-transferred twin | 64 | -0.000 | [-0.010, +0.009] | [-0.013, +0.012] | contains 0 | +0.000 | +0.002 |
| transfer/reve/task_full | transfer vs non-transferred twin | 64 | -0.003 | [-0.010, +0.004] | [-0.013, +0.006] | contains 0 | -0.001 | -0.001 |

**CS_SINGLE · NLL** (critical value 2.72)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| transfer/lag_local_tokens/task_partial | transfer vs non-transferred twin | 64 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | -0.000 |
| transfer/lag_local_tokens/task_full | transfer vs non-transferred twin | 64 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | +0.001 |
| transfer/cbramod/task_partial | transfer vs non-transferred twin | 64 | +0.002 | [+0.001, +0.004] | [+0.001, +0.004] | I>0 | +0.001 | +0.000 |
| transfer/cbramod/task_full | transfer vs non-transferred twin | 64 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | -0.001 |
| transfer/reve/task_partial | transfer vs non-transferred twin | 64 | +0.010 | [+0.008, +0.012] | [+0.007, +0.013] | I>0 | +0.003 | +0.000 |
| transfer/reve/task_full | transfer vs non-transferred twin | 64 | +0.001 | [-0.000, +0.003] | [-0.001, +0.003] | contains 0 | +0.002 | +0.000 |

**CS_SINGLE · AUC** (critical value 2.67)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| transfer/lag_local_tokens/task_partial | transfer vs non-transferred twin | 64 | +0.000 | [-0.006, +0.007] | [-0.008, +0.009] | contains 0 | -0.000 | -0.000 |
| transfer/lag_local_tokens/task_full | transfer vs non-transferred twin | 64 | -0.002 | [-0.008, +0.004] | [-0.010, +0.006] | contains 0 | -0.000 | +0.001 |
| transfer/cbramod/task_partial | transfer vs non-transferred twin | 64 | +0.023 | [+0.014, +0.032] | [+0.011, +0.035] | I>0 | +0.001 | +0.000 |
| transfer/cbramod/task_full | transfer vs non-transferred twin | 64 | -0.000 | [-0.005, +0.005] | [-0.007, +0.007] | contains 0 | -0.000 | -0.001 |
| transfer/reve/task_partial | transfer vs non-transferred twin | 64 | -0.003 | [-0.011, +0.004] | [-0.014, +0.007] | contains 0 | +0.003 | +0.000 |
| transfer/reve/task_full | transfer vs non-transferred twin | 64 | -0.009 | [-0.019, +0.001] | [-0.022, +0.004] | contains 0 | +0.002 | +0.000 |

## 5. Local + pretrained residual logit (within record) and recipe contrasts

**NCE · cbramod · NLL** (critical value 2.52)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| residual_pretrained_frozen | combined vs local_only (within record) | 64 | -0.000 | [-0.000, +0.000] | [-0.001, +0.000] | contains 0 | – | – |
| residual_pretrained_peft | combined vs local_only (within record) | 64 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_random_trainable | combined vs local_only (within record) | 64 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_pretrained_frozen_vs_random_trainable | recipe | 64 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_pretrained_peft_vs_random_trainable | recipe | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |

**NCE · cbramod · AUC** (critical value 2.58)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| residual_pretrained_frozen | combined vs local_only (within record) | 64 | -0.003 | [-0.006, +0.000] | [-0.007, +0.001] | contains 0 | – | – |
| residual_pretrained_peft | combined vs local_only (within record) | 64 | -0.001 | [-0.004, +0.002] | [-0.005, +0.003] | contains 0 | – | – |
| residual_random_trainable | combined vs local_only (within record) | 64 | -0.002 | [-0.005, +0.000] | [-0.006, +0.001] | contains 0 | – | – |
| residual_pretrained_frozen_vs_random_trainable | recipe | 64 | -0.000 | [-0.002, +0.002] | [-0.002, +0.002] | contains 0 | – | – |
| residual_pretrained_peft_vs_random_trainable | recipe | 64 | +0.002 | [-0.000, +0.003] | [-0.000, +0.004] | contains 0 | – | – |

**NCE · reve · NLL** (critical value 2.53)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| residual_pretrained_frozen | combined vs local_only (within record) | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_pretrained_peft | combined vs local_only (within record) | 64 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_random_trainable | combined vs local_only (within record) | 64 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_pretrained_frozen_vs_random_trainable | recipe | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_pretrained_peft_vs_random_trainable | recipe | 64 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |

**NCE · reve · AUC** (critical value 2.49)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| residual_pretrained_frozen | combined vs local_only (within record) | 64 | +0.000 | [-0.003, +0.003] | [-0.003, +0.004] | contains 0 | – | – |
| residual_pretrained_peft | combined vs local_only (within record) | 64 | -0.002 | [-0.004, +0.001] | [-0.005, +0.002] | contains 0 | – | – |
| residual_random_trainable | combined vs local_only (within record) | 64 | -0.001 | [-0.004, +0.002] | [-0.005, +0.002] | contains 0 | – | – |
| residual_pretrained_frozen_vs_random_trainable | recipe | 64 | +0.002 | [+0.000, +0.003] | [-0.000, +0.003] | contains 0 | – | – |
| residual_pretrained_peft_vs_random_trainable | recipe | 64 | -0.000 | [-0.001, -0.000] | [-0.001, +0.000] | contains 0 | – | – |

**CS_SINGLE · cbramod · NLL** (critical value 2.59)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| residual_pretrained_frozen | combined vs local_only (within record) | 64 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_pretrained_peft | combined vs local_only (within record) | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_random_trainable | combined vs local_only (within record) | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_pretrained_frozen_vs_random_trainable | recipe | 64 | -0.000 | [-0.000, +0.000] | [-0.001, +0.000] | contains 0 | – | – |
| residual_pretrained_peft_vs_random_trainable | recipe | 64 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |

**CS_SINGLE · cbramod · AUC** (critical value 2.54)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| residual_pretrained_frozen | combined vs local_only (within record) | 64 | -0.007 | [-0.011, -0.003] | [-0.012, -0.002] | I<0 | – | – |
| residual_pretrained_peft | combined vs local_only (within record) | 64 | -0.005 | [-0.008, -0.001] | [-0.009, -0.000] | I<0 | – | – |
| residual_random_trainable | combined vs local_only (within record) | 64 | -0.006 | [-0.010, -0.002] | [-0.011, -0.000] | I<0 | – | – |
| residual_pretrained_frozen_vs_random_trainable | recipe | 64 | -0.002 | [-0.006, +0.003] | [-0.007, +0.004] | contains 0 | – | – |
| residual_pretrained_peft_vs_random_trainable | recipe | 64 | +0.001 | [-0.003, +0.005] | [-0.005, +0.006] | contains 0 | – | – |

**CS_SINGLE · reve · NLL** (critical value 2.63)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| residual_pretrained_frozen | combined vs local_only (within record) | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_pretrained_peft | combined vs local_only (within record) | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_random_trainable | combined vs local_only (within record) | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_pretrained_frozen_vs_random_trainable | recipe | 64 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |
| residual_pretrained_peft_vs_random_trainable | recipe | 64 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | – | – |

**CS_SINGLE · reve · AUC** (critical value 2.60)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| residual_pretrained_frozen | combined vs local_only (within record) | 64 | -0.005 | [-0.009, -0.001] | [-0.010, -0.000] | I<0 | – | – |
| residual_pretrained_peft | combined vs local_only (within record) | 64 | -0.007 | [-0.010, -0.003] | [-0.011, -0.002] | I<0 | – | – |
| residual_random_trainable | combined vs local_only (within record) | 64 | -0.004 | [-0.008, +0.000] | [-0.009, +0.001] | contains 0 | – | – |
| residual_pretrained_frozen_vs_random_trainable | recipe | 64 | -0.001 | [-0.005, +0.003] | [-0.006, +0.004] | contains 0 | – | – |
| residual_pretrained_peft_vs_random_trainable | recipe | 64 | -0.003 | [-0.007, +0.001] | [-0.008, +0.003] | contains 0 | – | – |

## 6. Distillation: λ = 0 baseline → chosen λ (within record)

**NCE · NLL** (critical value 2.96)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| local_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | -0.000 | -0.001 |
| local_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | -0.000 | +0.000 |
| local_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.001, +0.000] | [-0.001, +0.001] | contains 0 | +0.000 | -0.001 |
| generic_pretrained_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | -0.000 | -0.000 |
| generic_pretrained_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.001, +0.000] | [-0.001, +0.000] | contains 0 | +0.000 | +0.000 |
| generic_pretrained_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | -0.001 | [-0.001, +0.000] | [-0.002, +0.000] | contains 0 | +0.000 | -0.001 |
| auditory_adapted_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | -0.000 | -0.000 |
| auditory_adapted_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | -0.000 | -0.000 |
| auditory_adapted_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.001, +0.000] | [-0.002, +0.001] | contains 0 | +0.000 | -0.001 |
| legacy_full_teacher_control/early | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.001, +0.000] | [-0.001, +0.000] | contains 0 | -0.001 | -0.001 |
| legacy_full_teacher_control/late | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.001, +0.000] | [-0.001, +0.000] | contains 0 | +0.000 | +0.000 |
| legacy_full_teacher_control/full | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.001, +0.000] | [-0.002, +0.001] | contains 0 | +0.000 | -0.000 |

**NCE · AUC** (critical value 2.87)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| local_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | +0.002 | [-0.003, +0.007] | [-0.005, +0.009] | contains 0 | -0.000 | -0.001 |
| local_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | +0.001 | [-0.002, +0.005] | [-0.004, +0.006] | contains 0 | -0.000 | +0.000 |
| local_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | +0.000 | [-0.006, +0.006] | [-0.008, +0.008] | contains 0 | +0.000 | -0.001 |
| generic_pretrained_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | +0.001 | [-0.003, +0.005] | [-0.005, +0.007] | contains 0 | -0.000 | -0.000 |
| generic_pretrained_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | -0.004 | [-0.009, +0.000] | [-0.011, +0.002] | contains 0 | +0.000 | +0.000 |
| generic_pretrained_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | -0.004 | [-0.010, +0.002] | [-0.013, +0.005] | contains 0 | +0.000 | -0.001 |
| auditory_adapted_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.005, +0.004] | [-0.007, +0.006] | contains 0 | -0.000 | -0.000 |
| auditory_adapted_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | +0.002 | [-0.001, +0.006] | [-0.003, +0.008] | contains 0 | -0.000 | -0.000 |
| auditory_adapted_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | -0.001 | [-0.007, +0.005] | [-0.009, +0.007] | contains 0 | +0.000 | -0.001 |
| legacy_full_teacher_control/early | chosen lambda vs lambda 0 (within record) | 64 | -0.005 | [-0.010, +0.000] | [-0.013, +0.003] | contains 0 | -0.001 | -0.001 |
| legacy_full_teacher_control/late | chosen lambda vs lambda 0 (within record) | 64 | -0.003 | [-0.008, +0.001] | [-0.010, +0.003] | contains 0 | +0.000 | +0.000 |
| legacy_full_teacher_control/full | chosen lambda vs lambda 0 (within record) | 64 | -0.003 | [-0.009, +0.004] | [-0.012, +0.006] | contains 0 | +0.000 | -0.000 |

**CS_SINGLE · NLL** (critical value 3.00)

| member | label | n | ΔNLL | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| local_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | +0.001 | +0.000 |
| local_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | -0.000 |
| local_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | -0.001 | [-0.001, +0.000] | [-0.002, +0.001] | contains 0 | -0.001 | -0.000 |
| generic_pretrained_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.000, +0.000] | [-0.001, +0.001] | contains 0 | +0.000 | -0.000 |
| generic_pretrained_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.001, +0.000] | [-0.001, +0.001] | contains 0 | -0.000 | -0.001 |
| generic_pretrained_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.001, +0.000] | [-0.002, +0.001] | contains 0 | +0.000 | +0.001 |
| auditory_adapted_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | +0.000 | [-0.000, +0.001] | [-0.000, +0.001] | contains 0 | +0.000 | +0.000 |
| auditory_adapted_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | +0.000 |
| auditory_adapted_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | -0.001 | [-0.002, +0.000] | [-0.002, +0.001] | contains 0 | -0.001 | -0.002 |
| legacy_full_teacher_control/early | chosen lambda vs lambda 0 (within record) | 64 | +0.000 | [-0.000, +0.001] | [-0.000, +0.001] | contains 0 | +0.001 | +0.002 |
| legacy_full_teacher_control/late | chosen lambda vs lambda 0 (within record) | 64 | +0.001 | [+0.000, +0.001] | [-0.000, +0.002] | contains 0 | +0.000 | -0.000 |
| legacy_full_teacher_control/full | chosen lambda vs lambda 0 (within record) | 64 | -0.001 | [-0.002, -0.000] | [-0.003, +0.000] | contains 0 | +0.000 | +0.000 |

**CS_SINGLE · AUC** (critical value 2.95)

| member | label | n | ΔAUC | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |
|---|---|---|---|---|---|---|---|---|
| local_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | +0.003 | [-0.006, +0.013] | [-0.011, +0.017] | contains 0 | +0.001 | +0.000 |
| local_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | +0.004 | [-0.002, +0.010] | [-0.004, +0.012] | contains 0 | -0.000 | -0.000 |
| local_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | -0.002 | [-0.008, +0.004] | [-0.011, +0.006] | contains 0 | -0.001 | -0.000 |
| generic_pretrained_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | +0.001 | [-0.005, +0.007] | [-0.007, +0.010] | contains 0 | +0.000 | -0.000 |
| generic_pretrained_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | +0.001 | [-0.004, +0.005] | [-0.006, +0.008] | contains 0 | -0.000 | -0.001 |
| generic_pretrained_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | -0.004 | [-0.010, +0.001] | [-0.013, +0.004] | contains 0 | +0.000 | +0.001 |
| auditory_adapted_teacher/early | chosen lambda vs lambda 0 (within record) | 64 | +0.003 | [-0.002, +0.008] | [-0.005, +0.010] | contains 0 | +0.000 | +0.000 |
| auditory_adapted_teacher/late | chosen lambda vs lambda 0 (within record) | 64 | -0.000 | [-0.007, +0.006] | [-0.010, +0.010] | contains 0 | +0.000 | +0.000 |
| auditory_adapted_teacher/full | chosen lambda vs lambda 0 (within record) | 64 | -0.005 | [-0.011, +0.000] | [-0.014, +0.003] | contains 0 | -0.001 | -0.002 |
| legacy_full_teacher_control/early | chosen lambda vs lambda 0 (within record) | 64 | +0.009 | [+0.000, +0.017] | [-0.004, +0.021] | contains 0 | +0.001 | +0.002 |
| legacy_full_teacher_control/late | chosen lambda vs lambda 0 (within record) | 64 | +0.004 | [-0.001, +0.009] | [-0.004, +0.012] | contains 0 | +0.000 | -0.000 |
| legacy_full_teacher_control/full | chosen lambda vs lambda 0 (within record) | 64 | -0.009 | [-0.014, -0.003] | [-0.017, -0.000] | I<0 | +0.000 | +0.000 |

## Appendix: notes

- PE-COMPLEMENT|NCE|cbramod|sec/residual_pretrained_frozen/hist_gain: no paired identities
- PE-COMPLEMENT|NCE|cbramod|sec/residual_pretrained_peft/hist_gain: no paired identities
- PE-COMPLEMENT|NCE|cbramod|sec/residual_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|NCE|cbramod|sec/residual_pretrained_frozen_vs_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|NCE|cbramod|sec/residual_pretrained_peft_vs_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|NCE|cbramod|sec/residual_pretrained_frozen/twin_sens: no paired identities
- PE-COMPLEMENT|NCE|cbramod|sec/residual_pretrained_peft/twin_sens: no paired identities
- PE-COMPLEMENT|NCE|cbramod|sec/residual_random_trainable/twin_sens: no paired identities
- PE-COMPLEMENT|NCE|cbramod|sec/residual_pretrained_frozen_vs_random_trainable/twin_sens: no paired identities
- PE-COMPLEMENT|NCE|cbramod|sec/residual_pretrained_peft_vs_random_trainable/twin_sens: no paired identities
- PE-COMPLEMENT|NCE|reve|sec/residual_pretrained_frozen/hist_gain: no paired identities
- PE-COMPLEMENT|NCE|reve|sec/residual_pretrained_peft/hist_gain: no paired identities
- PE-COMPLEMENT|NCE|reve|sec/residual_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|NCE|reve|sec/residual_pretrained_frozen_vs_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|NCE|reve|sec/residual_pretrained_peft_vs_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|NCE|reve|sec/residual_pretrained_frozen/twin_sens: no paired identities
- PE-COMPLEMENT|NCE|reve|sec/residual_pretrained_peft/twin_sens: no paired identities
- PE-COMPLEMENT|NCE|reve|sec/residual_random_trainable/twin_sens: no paired identities
- PE-COMPLEMENT|NCE|reve|sec/residual_pretrained_frozen_vs_random_trainable/twin_sens: no paired identities
- PE-COMPLEMENT|NCE|reve|sec/residual_pretrained_peft_vs_random_trainable/twin_sens: no paired identities
- PE-COMPLEMENT|CS_SINGLE|cbramod|sec/residual_pretrained_frozen/hist_gain: no paired identities
- PE-COMPLEMENT|CS_SINGLE|cbramod|sec/residual_pretrained_peft/hist_gain: no paired identities
- PE-COMPLEMENT|CS_SINGLE|cbramod|sec/residual_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|CS_SINGLE|cbramod|sec/residual_pretrained_frozen_vs_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|CS_SINGLE|cbramod|sec/residual_pretrained_peft_vs_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|CS_SINGLE|cbramod|sec/residual_pretrained_frozen/twin_sens: no paired identities
- PE-COMPLEMENT|CS_SINGLE|cbramod|sec/residual_pretrained_peft/twin_sens: no paired identities
- PE-COMPLEMENT|CS_SINGLE|cbramod|sec/residual_random_trainable/twin_sens: no paired identities
- PE-COMPLEMENT|CS_SINGLE|cbramod|sec/residual_pretrained_frozen_vs_random_trainable/twin_sens: no paired identities
- PE-COMPLEMENT|CS_SINGLE|cbramod|sec/residual_pretrained_peft_vs_random_trainable/twin_sens: no paired identities
- PE-COMPLEMENT|CS_SINGLE|reve|sec/residual_pretrained_frozen/hist_gain: no paired identities
- PE-COMPLEMENT|CS_SINGLE|reve|sec/residual_pretrained_peft/hist_gain: no paired identities
- PE-COMPLEMENT|CS_SINGLE|reve|sec/residual_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|CS_SINGLE|reve|sec/residual_pretrained_frozen_vs_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|CS_SINGLE|reve|sec/residual_pretrained_peft_vs_random_trainable/hist_gain: no paired identities
- PE-COMPLEMENT|CS_SINGLE|reve|sec/residual_pretrained_frozen/twin_sens: no paired identities
- PE-COMPLEMENT|CS_SINGLE|reve|sec/residual_pretrained_peft/twin_sens: no paired identities
- PE-COMPLEMENT|CS_SINGLE|reve|sec/residual_random_trainable/twin_sens: no paired identities
- PE-COMPLEMENT|CS_SINGLE|reve|sec/residual_pretrained_frozen_vs_random_trainable/twin_sens: no paired identities
- PE-COMPLEMENT|CS_SINGLE|reve|sec/residual_pretrained_peft_vs_random_trainable/twin_sens: no paired identities
