# S34 science_v2 readout (content/time 180 + private current/time v2 130)

Source `results/auditory_alignment_v3/aln34/science_v2/science.json` (job 1045980, 2026-10-18T16:45:48.730601+02:00), sha256 `008ec2cd8a1843e5…`. Readout only: no refit, no new bootstrap. Full cell tables: `results/auditory_alignment_v3/aln35/science_readout_v1/science_v2_cells.csv`.

Marks: `+`/`−` = the family's simultaneous band (max-t over its cells) excludes 0 (AUC: excludes 0.5). No mark = band includes the reference. Bands condition on fitted models; n = people. DTU = 3-seed mean (seeds averaged within person); FAU/Federici seed 3401; REVE 3401.

Public windows: EEG access [c−400, c+600) ms around each sound anchor; centers are overlapping 1-s access windows, not neural latencies. Matched−mismatch r subtracts an EEG-only within-person segment-roll baseline.

## Public dtu: matched − mismatch r on the diagonal (train = test center)

| Model | Target | -200 ms | 0 ms | 200 ms | 400 ms | 600 ms |
|---|---|---|---|---|---|---|
| local | env direct | +0.108+ | +0.145+ | +0.125+ | +0.100+ | +0.072+ |
| local | onset direct | +0.069+ | +0.110+ | +0.074+ | +0.058+ | +0.037+ |
| local | spec direct | +0.037+ | +0.048+ | +0.042+ | +0.040+ | +0.032+ |
| local | flux direct | +0.089+ | +0.111+ | +0.108+ | +0.098+ | +0.067+ |
| local | Ac direct | +0.071+ | +0.099+ | +0.070+ | +0.060+ | +0.046+ |
| local | Lz direct | +0.053+ | +0.072+ | +0.068+ | +0.059+ | +0.053+ |
| local | onset conditional | +0.067+ | +0.109+ | +0.072+ | +0.057+ | +0.035+ |
| local | spec conditional | +0.037+ | +0.048+ | +0.041+ | +0.040+ | +0.032+ |
| local | flux conditional | +0.068+ | +0.088+ | +0.077+ | +0.067+ | +0.040+ |
| local | Ac conditional | +0.027+ | +0.055+ | +0.026+ | +0.021+ | +0.015+ |
| local | Lz conditional | +0.022+ | +0.029+ | +0.033+ | +0.020+ | +0.024+ |
| local | env history_conditional | +0.075+ | +0.104+ | +0.060+ | +0.039+ | +0.030+ |
| raw20 | env direct | +0.009 | +0.013+ | +0.057+ | +0.006 | +0.008 |
| raw20 | onset direct | -0.002 | +0.002 | +0.037+ | +0.001 | -0.005 |
| raw20 | spec direct | +0.002 | +0.006 | +0.016+ | +0.003 | +0.006 |
| raw20 | flux direct | +0.000 | +0.009 | +0.030+ | +0.003 | +0.007 |
| raw20 | Ac direct | +0.002 | +0.010+ | +0.022+ | +0.007+ | +0.010+ |
| raw20 | Lz direct | +0.003 | +0.008+ | +0.014+ | +0.003 | +0.012+ |
| raw20 | onset conditional | -0.003 | +0.001 | +0.036+ | +0.000 | -0.004 |
| raw20 | spec conditional | +0.002 | +0.006 | +0.016+ | +0.003 | +0.006 |
| raw20 | flux conditional | -0.004 | -0.001 | +0.015 | -0.002 | +0.003 |
| raw20 | Ac conditional | +0.001 | +0.005 | -0.003 | -0.003 | +0.005 |
| raw20 | Lz conditional | +0.004 | +0.005 | +0.004 | +0.001 | +0.007+ |
| raw20 | env history_conditional | +0.002 | +0.005 | +0.041+ | +0.001 | -0.003 |
| CBpre | env direct | +0.100+ | +0.159+ | +0.111+ | +0.073+ | +0.075+ |
| CBpre | onset direct | +0.051+ | +0.115+ | +0.068+ | +0.042+ | +0.027+ |
| CBpre | spec direct | +0.034+ | +0.055+ | +0.043+ | +0.033+ | +0.037+ |
| CBpre | flux direct | +0.075+ | +0.120+ | +0.103+ | +0.067+ | +0.053+ |
| CBpre | Ac direct | +0.057+ | +0.105+ | +0.059+ | +0.043+ | +0.045+ |
| CBpre | Lz direct | +0.046+ | +0.074+ | +0.054+ | +0.045+ | +0.048+ |
| CBpre | onset conditional | +0.049+ | +0.114+ | +0.066+ | +0.041+ | +0.026+ |
| CBpre | spec conditional | +0.033+ | +0.054+ | +0.042+ | +0.033+ | +0.037+ |
| CBpre | flux conditional | +0.057+ | +0.090+ | +0.076+ | +0.045+ | +0.033+ |
| CBpre | Ac conditional | +0.019+ | +0.050+ | +0.012+ | +0.012+ | +0.010+ |
| CBpre | Lz conditional | +0.016+ | +0.025+ | +0.023+ | +0.015+ | +0.014+ |
| CBpre | env history_conditional | +0.055+ | +0.112+ | +0.048+ | +0.023+ | +0.021+ |
| CBrand | env direct | +0.084+ | +0.142+ | +0.100+ | +0.071+ | +0.073+ |
| CBrand | onset direct | +0.035+ | +0.101+ | +0.060+ | +0.038+ | +0.028+ |
| CBrand | spec direct | +0.030+ | +0.051+ | +0.034+ | +0.027+ | +0.034+ |
| CBrand | flux direct | +0.062+ | +0.110+ | +0.095+ | +0.063+ | +0.056+ |
| CBrand | Ac direct | +0.047+ | +0.092+ | +0.051+ | +0.039+ | +0.042+ |
| CBrand | Lz direct | +0.040+ | +0.067+ | +0.051+ | +0.043+ | +0.047+ |
| CBrand | onset conditional | +0.033+ | +0.100+ | +0.058+ | +0.038+ | +0.027+ |
| CBrand | spec conditional | +0.029+ | +0.050+ | +0.033+ | +0.027+ | +0.034+ |
| CBrand | flux conditional | +0.046+ | +0.085+ | +0.069+ | +0.040+ | +0.032+ |
| CBrand | Ac conditional | +0.017+ | +0.043+ | +0.011+ | +0.007 | +0.012+ |
| CBrand | Lz conditional | +0.016+ | +0.024+ | +0.020+ | +0.013+ | +0.012+ |
| CBrand | env history_conditional | +0.042+ | +0.100+ | +0.040+ | +0.021+ | +0.024+ |
| REVEpre | env direct | +0.110+ | +0.153+ | +0.111+ | +0.076+ | +0.072+ |
| REVEpre | onset direct | +0.062+ | +0.110+ | +0.071+ | +0.060+ | +0.034+ |
| REVEpre | spec direct | +0.036+ | +0.055+ | +0.042+ | +0.036+ | +0.036+ |
| REVEpre | flux direct | +0.087+ | +0.118+ | +0.109+ | +0.083+ | +0.061+ |
| REVEpre | Ac direct | +0.064+ | +0.103+ | +0.066+ | +0.052+ | +0.048+ |
| REVEpre | Lz direct | +0.053+ | +0.076+ | +0.061+ | +0.053+ | +0.053+ |
| REVEpre | onset conditional | +0.059+ | +0.109+ | +0.070+ | +0.059+ | +0.033+ |
| REVEpre | spec conditional | +0.036+ | +0.054+ | +0.040+ | +0.035+ | +0.036+ |
| REVEpre | flux conditional | +0.065+ | +0.098+ | +0.082+ | +0.052+ | +0.037+ |
| REVEpre | Ac conditional | +0.025+ | +0.051+ | +0.018+ | +0.017+ | +0.013+ |
| REVEpre | Lz conditional | +0.019+ | +0.028+ | +0.023+ | +0.017+ | +0.020+ |
| REVEpre | env history_conditional | +0.065+ | +0.106+ | +0.052+ | +0.030+ | +0.026+ |

### dtu: temporal generalization, train at 200 ms (env and onset direct)

| Model | Target | test -200 | test 0 | test 200 | test 400 | test 600 |
|---|---|---|---|---|---|---|
| local | env | -0.032− | +0.089+ | +0.125+ | +0.029+ | -0.062− |
| local | onset | -0.017 | +0.031+ | +0.074+ | +0.035+ | -0.011 |
| raw20 | env | -0.009 | +0.018 | +0.057+ | +0.001 | -0.032− |
| raw20 | onset | -0.004 | +0.010 | +0.037+ | +0.011 | -0.009 |
| CBpre | env | -0.006 | +0.094+ | +0.111+ | +0.018 | -0.065− |
| CBpre | onset | -0.011 | +0.049+ | +0.068+ | +0.033+ | -0.016 |
| CBrand | env | -0.003 | +0.090+ | +0.100+ | +0.013 | -0.061− |
| CBrand | onset | -0.000 | +0.045+ | +0.060+ | +0.027+ | -0.017− |
| REVEpre | env | -0.002 | +0.098+ | +0.111+ | +0.018 | -0.060− |
| REVEpre | onset | -0.005 | +0.052+ | +0.071+ | +0.033+ | -0.018 |

### dtu: hearing groups, env direct matched − mismatch r (diagonal 0 / 200 ms)

| Model | hi 0 / 200 | nh 0 / 200 |
|---|---|---|
| local | +0.162+ / +0.141+ (n=22) | +0.128+ / +0.110+ (n=22) |
| raw20 | +0.016 / +0.063+ (n=22) | +0.011 / +0.052+ (n=22) |
| CBpre | +0.179+ / +0.115+ (n=22) | +0.139+ / +0.107+ (n=22) |
| CBrand | +0.159+ / +0.099+ (n=22) | +0.126+ / +0.101+ (n=22) |
| REVEpre | +0.167+ / +0.121+ (n=22) | +0.138+ / +0.100+ (n=22) |

## Public fau: matched − mismatch r on the diagonal (train = test center)

| Model | Target | -200 ms | 0 ms | 200 ms | 400 ms | 600 ms |
|---|---|---|---|---|---|---|
| local | env direct | +0.047+ | +0.075+ | +0.055+ | +0.031+ | +0.028+ |
| local | onset direct | +0.034+ | +0.053+ | +0.021+ | +0.013+ | +0.002 |
| local | spec direct | +0.019+ | +0.028+ | +0.016+ | +0.009+ | +0.008+ |
| local | flux direct | +0.046+ | +0.055+ | +0.040+ | +0.022+ | +0.018+ |
| local | Ac direct | +0.040+ | +0.054+ | +0.032+ | +0.015+ | +0.014+ |
| local | Lz direct | +0.029+ | +0.045+ | +0.032+ | +0.021+ | +0.014+ |
| local | onset conditional | +0.034+ | +0.053+ | +0.021+ | +0.013 | +0.002 |
| local | spec conditional | +0.019+ | +0.028+ | +0.016+ | +0.009+ | +0.008+ |
| local | flux conditional | +0.039+ | +0.043+ | +0.036+ | +0.018+ | +0.014+ |
| local | Ac conditional | +0.043+ | +0.042+ | +0.023+ | +0.017+ | +0.008 |
| local | Lz conditional | +0.011+ | +0.015+ | +0.013+ | +0.009+ | +0.006 |
| local | env history_conditional | +0.032+ | +0.055+ | +0.019+ | +0.019+ | +0.003 |
| raw20 | env direct | -0.000 | +0.013 | +0.023+ | +0.009 | +0.003 |
| raw20 | onset direct | -0.005 | +0.003 | +0.017+ | +0.000 | +0.006 |
| raw20 | spec direct | -0.002 | +0.006 | +0.010+ | +0.002 | -0.000 |
| raw20 | flux direct | -0.001 | -0.009 | +0.008 | -0.002 | +0.010 |
| raw20 | Ac direct | -0.002 | +0.006 | +0.014+ | +0.001 | +0.001 |
| raw20 | Lz direct | +0.002 | +0.005 | +0.007+ | +0.004 | -0.000 |
| raw20 | onset conditional | -0.005 | +0.003 | +0.017+ | +0.000 | +0.006 |
| raw20 | spec conditional | -0.002 | +0.006 | +0.010+ | +0.002 | -0.000 |
| raw20 | flux conditional | +0.001 | -0.007 | +0.004 | +0.000 | +0.007 |
| raw20 | Ac conditional | +0.003 | +0.006 | +0.005 | +0.005 | +0.001 |
| raw20 | Lz conditional | +0.002 | +0.001 | +0.004 | +0.001 | +0.004 |
| raw20 | env history_conditional | -0.003 | -0.000 | +0.018+ | -0.000 | -0.005 |
| CBpre | env direct | +0.029+ | +0.080+ | +0.043+ | +0.018+ | +0.009 |
| CBpre | onset direct | +0.025+ | +0.064+ | +0.021+ | +0.003 | -0.006 |
| CBpre | spec direct | +0.017+ | +0.029+ | +0.019+ | +0.006 | +0.005 |
| CBpre | flux direct | +0.041+ | +0.070+ | +0.047+ | -0.000 | +0.004 |
| CBpre | Ac direct | +0.035+ | +0.058+ | +0.025+ | +0.006 | +0.009+ |
| CBpre | Lz direct | +0.021+ | +0.048+ | +0.024+ | +0.006+ | +0.008+ |
| CBpre | onset conditional | +0.025+ | +0.064+ | +0.021+ | +0.003 | -0.006 |
| CBpre | spec conditional | +0.016+ | +0.029+ | +0.019+ | +0.006 | +0.005 |
| CBpre | flux conditional | +0.033+ | +0.052+ | +0.035+ | +0.003 | -0.001 |
| CBpre | Ac conditional | +0.033+ | +0.044+ | +0.014+ | +0.006 | +0.010+ |
| CBpre | Lz conditional | +0.007+ | +0.014+ | +0.007 | +0.002 | +0.005 |
| CBpre | env history_conditional | +0.017+ | +0.064+ | +0.016+ | +0.008 | -0.004 |
| CBrand | env direct | +0.020+ | +0.066+ | +0.033+ | +0.020+ | +0.008 |
| CBrand | onset direct | +0.018+ | +0.051+ | +0.023+ | +0.002 | -0.004 |
| CBrand | spec direct | +0.014+ | +0.027+ | +0.014+ | +0.008+ | +0.004 |
| CBrand | flux direct | +0.035+ | +0.064+ | +0.051+ | -0.002 | +0.006 |
| CBrand | Ac direct | +0.034+ | +0.053+ | +0.019+ | +0.007 | +0.012+ |
| CBrand | Lz direct | +0.019+ | +0.046+ | +0.022+ | +0.007+ | +0.010+ |
| CBrand | onset conditional | +0.018+ | +0.051+ | +0.023+ | +0.002 | -0.004 |
| CBrand | spec conditional | +0.014+ | +0.027+ | +0.014+ | +0.008+ | +0.004 |
| CBrand | flux conditional | +0.031+ | +0.049+ | +0.039+ | +0.001 | +0.003 |
| CBrand | Ac conditional | +0.031+ | +0.040+ | +0.015+ | +0.008 | +0.012+ |
| CBrand | Lz conditional | +0.006 | +0.011+ | +0.004 | -0.002 | +0.000 |
| CBrand | env history_conditional | +0.023+ | +0.049+ | +0.014+ | +0.011 | +0.001 |
| REVEpre | env direct | +0.037+ | +0.073+ | +0.053+ | +0.029+ | +0.014+ |
| REVEpre | onset direct | +0.034+ | +0.061+ | +0.035+ | +0.013 | +0.002 |
| REVEpre | spec direct | +0.018+ | +0.029+ | +0.020+ | +0.013+ | +0.008+ |
| REVEpre | flux direct | +0.063+ | +0.078+ | +0.061+ | +0.021+ | +0.005 |
| REVEpre | Ac direct | +0.041+ | +0.056+ | +0.032+ | +0.015+ | +0.009+ |
| REVEpre | Lz direct | +0.025+ | +0.047+ | +0.035+ | +0.014+ | +0.012+ |
| REVEpre | onset conditional | +0.034+ | +0.061+ | +0.035+ | +0.013 | +0.002 |
| REVEpre | spec conditional | +0.018+ | +0.028+ | +0.020+ | +0.013+ | +0.008+ |
| REVEpre | flux conditional | +0.055+ | +0.060+ | +0.049+ | +0.006 | +0.005 |
| REVEpre | Ac conditional | +0.037+ | +0.045+ | +0.022+ | +0.009 | +0.014+ |
| REVEpre | Lz conditional | +0.004 | +0.014+ | +0.011+ | +0.003 | +0.002 |
| REVEpre | env history_conditional | +0.032+ | +0.062+ | +0.023+ | +0.014+ | -0.001 |

### fau: temporal generalization, train at 200 ms (env and onset direct)

| Model | Target | test -200 | test 0 | test 200 | test 400 | test 600 |
|---|---|---|---|---|---|---|
| local | env | -0.020− | +0.025+ | +0.055+ | +0.002 | -0.014− |
| local | onset | -0.002 | +0.000 | +0.021+ | +0.007 | -0.004 |
| raw20 | env | -0.001 | +0.015+ | +0.023+ | -0.002 | -0.006 |
| raw20 | onset | -0.007 | -0.006 | +0.017+ | -0.001 | -0.005 |
| CBpre | env | +0.000 | +0.030+ | +0.043+ | +0.000 | -0.012 |
| CBpre | onset | -0.004 | +0.024+ | +0.021+ | +0.007 | +0.002 |
| CBrand | env | +0.003 | +0.025+ | +0.033+ | +0.003 | -0.008 |
| CBrand | onset | -0.011 | +0.021+ | +0.023+ | +0.014 | +0.001 |
| REVEpre | env | -0.012 | +0.028+ | +0.053+ | +0.000 | -0.009 |
| REVEpre | onset | +0.004 | +0.026+ | +0.035+ | +0.016+ | +0.004 |

### fau: hearing groups, env direct matched − mismatch r (diagonal 0 / 200 ms)

| Model | ci 0 / 200 | ha 0 / 200 | th 0 / 200 |
|---|---|---|---|
| local | +0.046+ / +0.040+ (n=24) | +0.097+ / +0.063+ (n=29) | +0.078+ / +0.062+ (n=14) |
| raw20 | +0.005 / +0.023 (n=24) | +0.019 / +0.021 (n=29) | +0.017 / +0.025 (n=14) |
| CBpre | +0.049+ / +0.031+ (n=24) | +0.095+ / +0.048+ (n=29) | +0.102+ / +0.055+ (n=14) |
| CBrand | +0.040+ / +0.023 (n=24) | +0.078+ / +0.031+ (n=29) | +0.085+ / +0.054+ (n=14) |
| REVEpre | +0.044+ / +0.037+ (n=24) | +0.088+ / +0.059+ (n=29) | +0.091+ / +0.067+ (n=14) |

## Public federici: matched − mismatch r on the diagonal (train = test center)

| Model | Target | -200 ms | 0 ms | 200 ms | 400 ms | 600 ms |
|---|---|---|---|---|---|---|
| local | env direct | +0.068+ | +0.092+ | +0.042+ | +0.029 | +0.013 |
| local | env history_conditional | +0.036+ | +0.028 | +0.005 | +0.000 | +0.002 |
| raw20 | env direct | -0.038 | +0.026 | +0.019 | -0.010 | +0.008 |
| raw20 | env history_conditional | -0.007 | +0.012 | +0.011 | +0.002 | -0.005 |
| CBpre | env direct | +0.081+ | +0.137+ | +0.078+ | +0.032 | +0.049+ |
| CBpre | env history_conditional | -0.007 | +0.041+ | +0.026 | +0.012 | +0.012 |
| CBrand | env direct | +0.081+ | +0.122+ | +0.073+ | +0.021 | +0.045+ |
| CBrand | env history_conditional | -0.013 | +0.034 | +0.044+ | -0.006 | +0.023 |
| REVEpre | env direct | +0.074+ | +0.117+ | +0.080+ | +0.021 | +0.049+ |
| REVEpre | env history_conditional | +0.014 | +0.020 | +0.043+ | -0.013 | +0.009 |

### federici: temporal generalization, train at 200 ms (env and onset direct)

| Model | Target | test -200 | test 0 | test 200 | test 400 | test 600 |
|---|---|---|---|---|---|---|
| local | env | -0.008 | +0.048+ | +0.042+ | +0.004 | -0.019 |
| raw20 | env | +0.002 | -0.013 | +0.019 | -0.012 | +0.019 |
| CBpre | env | +0.016 | +0.117+ | +0.078+ | +0.008 | -0.050− |
| CBrand | env | +0.022 | +0.097+ | +0.073+ | +0.005 | -0.034 |
| REVEpre | env | +0.018 | +0.108+ | +0.080+ | +0.027 | -0.028 |

### federici: hearing groups, env direct matched − mismatch r (diagonal 0 / 200 ms)

| Model | CI 0 / 200 | HC 0 / 200 | HC-v 0 / 200 |
|---|---|---|---|
| local | +0.073+ / +0.049 (n=33) | +0.105+ / +0.034 (n=37) | +0.103 / +0.050 (n=16) |
| raw20 | +0.036 / -0.001 (n=33) | +0.022 / +0.018 (n=37) | +0.011 / +0.063 (n=16) |
| CBpre | +0.119+ / +0.067+ (n=33) | +0.149+ / +0.086+ (n=37) | +0.148+ / +0.081 (n=16) |
| CBrand | +0.104+ / +0.057 (n=33) | +0.126+ / +0.075+ (n=37) | +0.151+ / +0.099 (n=16) |
| REVEpre | +0.093+ / +0.072 (n=33) | +0.135+ / +0.071+ (n=37) | +0.125+ / +0.119 (n=16) |

## Private current sound (64 children: HA 55, NH 9)

Common source-ES logistic readout, positive-affine calibration. Seeds averaged within child (REVE 3401). `pre` for E_LOCAL and E_PUBLIC_TRANSFER had an all-zero input (CORRECTION_PRIVATE_PRE_ACCESS) and is shown as `invalid`.

### AUC by input window

| Configuration | Group | full | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|---|---|
| E_LOCAL|NCE|lag_local_tokens|full | all (n=64) | 0.518+ | invalid | 0.509 | 0.511+ | 0.504 |
| E_LOCAL|NCE|lag_local_tokens|full | HA (n=55) | 0.515+ | invalid | 0.506 | 0.511+ | 0.503 |
| E_LOCAL|NCE|lag_local_tokens|full | NH (n=9) | 0.532 | invalid | 0.529 | 0.509 | 0.508 |
| E_LOCAL|CS_SINGLE|lag_local_tokens|full | all (n=64) | 0.532+ | invalid | 0.516+ | 0.515+ | 0.504 |
| E_LOCAL|CS_SINGLE|lag_local_tokens|full | HA (n=55) | 0.529+ | invalid | 0.513+ | 0.513+ | 0.503 |
| E_LOCAL|CS_SINGLE|lag_local_tokens|full | NH (n=9) | 0.556+ | invalid | 0.532+ | 0.527 | 0.512+ |
| E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial | all (n=64) | 0.524+ | invalid | 0.516+ | 0.512+ | 0.505 |
| E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial | HA (n=55) | 0.521+ | invalid | 0.513+ | 0.511+ | 0.504 |
| E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial | NH (n=9) | 0.544 | invalid | 0.537 | 0.518 | 0.514 |
| E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial | all (n=64) | 0.531+ | invalid | 0.516+ | 0.519+ | 0.502 |
| E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial | HA (n=55) | 0.526+ | invalid | 0.514+ | 0.518+ | 0.502 |
| E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial | NH (n=9) | 0.560+ | invalid | 0.532 | 0.527 | 0.505 |
| E_GENERIC|NCE|cbramod|pretrained_full | all (n=64) | 0.512+ | 0.500 | 0.507 | 0.513+ | 0.500 |
| E_GENERIC|NCE|cbramod|pretrained_full | HA (n=55) | 0.510+ | 0.499 | 0.506 | 0.513+ | 0.500 |
| E_GENERIC|NCE|cbramod|pretrained_full | NH (n=9) | 0.525 | 0.504 | 0.514 | 0.513 | 0.502 |
| E_GENERIC|CS_SINGLE|cbramod|pretrained_full | all (n=64) | 0.537+ | 0.497 | 0.516+ | 0.521+ | 0.508+ |
| E_GENERIC|CS_SINGLE|cbramod|pretrained_full | HA (n=55) | 0.533+ | 0.498 | 0.515+ | 0.519+ | 0.507 |
| E_GENERIC|CS_SINGLE|cbramod|pretrained_full | NH (n=9) | 0.559 | 0.495 | 0.525 | 0.533 | 0.516 |
| E_GENERIC|NCE|cbramod|random_full | all (n=64) | 0.510+ | 0.501 | 0.504 | 0.501 | 0.503 |
| E_GENERIC|NCE|cbramod|random_full | HA (n=55) | 0.510+ | 0.500 | 0.502 | 0.500 | 0.503 |
| E_GENERIC|NCE|cbramod|random_full | NH (n=9) | 0.512 | 0.508 | 0.512 | 0.508 | 0.504 |
| E_GENERIC|CS_SINGLE|cbramod|random_full | all (n=64) | 0.522+ | 0.501 | 0.509+ | 0.512+ | 0.502 |
| E_GENERIC|CS_SINGLE|cbramod|random_full | HA (n=55) | 0.519+ | 0.502 | 0.507 | 0.511+ | 0.502 |
| E_GENERIC|CS_SINGLE|cbramod|random_full | NH (n=9) | 0.540+ | 0.495 | 0.522 | 0.519 | 0.504 |
| E_GENERIC|NCE|reve|pretrained_full | all (n=64) | 0.518+ | 0.499 | 0.501 | 0.509 | 0.507 |
| E_GENERIC|NCE|reve|pretrained_full | HA (n=55) | 0.516+ | 0.500 | 0.498 | 0.508 | 0.508 |
| E_GENERIC|NCE|reve|pretrained_full | NH (n=9) | 0.528 | 0.494 | 0.518 | 0.511 | 0.504 |
| E_GENERIC|CS_SINGLE|reve|pretrained_full | all (n=64) | 0.518+ | 0.494 | 0.505 | 0.514+ | 0.503 |
| E_GENERIC|CS_SINGLE|reve|pretrained_full | HA (n=55) | 0.516+ | 0.494 | 0.502 | 0.514+ | 0.504 |
| E_GENERIC|CS_SINGLE|reve|pretrained_full | NH (n=9) | 0.535 | 0.493 | 0.528 | 0.510 | 0.497 |

### history increment (bits/trial) by window

| Configuration | Group | full | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|---|---|
| E_LOCAL|NCE|lag_local_tokens|full | all (n=64) | -0.0031 | invalid | -0.0033 | -0.0031 | -0.0027 |
| E_LOCAL|NCE|lag_local_tokens|full | HA (n=55) | -0.0030 | invalid | -0.0035 | -0.0029 | -0.0025 |
| E_LOCAL|NCE|lag_local_tokens|full | NH (n=9) | -0.0037 | invalid | -0.0023 | -0.0044− | -0.0037− |
| E_LOCAL|CS_SINGLE|lag_local_tokens|full | all (n=64) | -0.0016 | invalid | -0.0031 | -0.0023 | -0.0031 |
| E_LOCAL|CS_SINGLE|lag_local_tokens|full | HA (n=55) | -0.0018 | invalid | -0.0032 | -0.0022 | -0.0032 |
| E_LOCAL|CS_SINGLE|lag_local_tokens|full | NH (n=9) | -0.0003 | invalid | -0.0025 | -0.0028 | -0.0028− |
| E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial | all (n=64) | -0.0028 | invalid | -0.0031 | -0.0030 | -0.0027 |
| E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial | HA (n=55) | -0.0028 | invalid | -0.0034 | -0.0029 | -0.0026 |
| E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial | NH (n=9) | -0.0030 | invalid | -0.0018 | -0.0033 | -0.0033 |
| E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial | all (n=64) | -0.0021 | invalid | -0.0032 | -0.0016 | -0.0035 |
| E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial | HA (n=55) | -0.0025 | invalid | -0.0032 | -0.0016 | -0.0033 |
| E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial | NH (n=9) | +0.0003 | invalid | -0.0032 | -0.0013 | -0.0043 |
| E_GENERIC|NCE|cbramod|pretrained_full | all (n=64) | -0.0032 | -0.0031 | -0.0035 | -0.0031 | -0.0034 |
| E_GENERIC|NCE|cbramod|pretrained_full | HA (n=55) | -0.0032 | -0.0031 | -0.0034 | -0.0030 | -0.0032 |
| E_GENERIC|NCE|cbramod|pretrained_full | NH (n=9) | -0.0033 | -0.0033− | -0.0041− | -0.0033 | -0.0041− |
| E_GENERIC|CS_SINGLE|cbramod|pretrained_full | all (n=64) | -0.0009 | -0.0034 | -0.0023− | -0.0015 | -0.0025 |
| E_GENERIC|CS_SINGLE|cbramod|pretrained_full | HA (n=55) | -0.0011 | -0.0033 | -0.0023 | -0.0013 | -0.0024 |
| E_GENERIC|CS_SINGLE|cbramod|pretrained_full | NH (n=9) | +0.0006 | -0.0036 | -0.0028 | -0.0025 | -0.0031− |
| E_GENERIC|NCE|cbramod|random_full | all (n=64) | -0.0033 | -0.0029 | -0.0039− | -0.0033 | -0.0036 |
| E_GENERIC|NCE|cbramod|random_full | HA (n=55) | -0.0033 | -0.0029 | -0.0038 | -0.0032 | -0.0033 |
| E_GENERIC|NCE|cbramod|random_full | NH (n=9) | -0.0034− | -0.0033− | -0.0043− | -0.0036 | -0.0058− |
| E_GENERIC|CS_SINGLE|cbramod|random_full | all (n=64) | -0.0026 | -0.0041 | -0.0037− | -0.0032 | -0.0040 |
| E_GENERIC|CS_SINGLE|cbramod|random_full | HA (n=55) | -0.0029 | -0.0039 | -0.0039− | -0.0031 | -0.0040 |
| E_GENERIC|CS_SINGLE|cbramod|random_full | NH (n=9) | -0.0011 | -0.0053− | -0.0026 | -0.0039− | -0.0037− |
| E_GENERIC|NCE|reve|pretrained_full | all (n=64) | -0.0029 | -0.0031 | -0.0032 | -0.0024 | -0.0029− |
| E_GENERIC|NCE|reve|pretrained_full | HA (n=55) | -0.0029 | -0.0030 | -0.0031 | -0.0022 | -0.0029− |
| E_GENERIC|NCE|reve|pretrained_full | NH (n=9) | -0.0029 | -0.0035 | -0.0037 | -0.0033 | -0.0029 |
| E_GENERIC|CS_SINGLE|reve|pretrained_full | all (n=64) | -0.0039− | -0.0047− | -0.0041− | -0.0032 | -0.0035 |
| E_GENERIC|CS_SINGLE|reve|pretrained_full | HA (n=55) | -0.0041− | -0.0044− | -0.0043− | -0.0028 | -0.0033 |
| E_GENERIC|CS_SINGLE|reve|pretrained_full | NH (n=9) | -0.0027 | -0.0065− | -0.0024 | -0.0059− | -0.0044− |

### Input-mask transfer (AUC, source-only destination calibration; rows train mask, cols test mask)

E_LOCAL|NCE|lag_local_tokens|full:

| train \ test | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|
| pre | invalid | invalid | invalid | invalid |
| 0_200 | invalid | 0.509 | 0.503 | 0.502 |
| 200_400 | invalid | 0.508+ | 0.511+ | 0.498 |
| 400_600 | invalid | 0.501 | 0.499 | 0.504 |

E_LOCAL|CS_SINGLE|lag_local_tokens|full:

| train \ test | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|
| pre | invalid | invalid | invalid | invalid |
| 0_200 | invalid | 0.516+ | 0.503 | 0.500 |
| 200_400 | invalid | 0.509 | 0.515+ | 0.502 |
| 400_600 | invalid | 0.508 | 0.505 | 0.504 |

E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial:

| train \ test | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|
| pre | invalid | invalid | invalid | invalid |
| 0_200 | invalid | 0.516+ | 0.503 | 0.498 |
| 200_400 | invalid | 0.507 | 0.512+ | 0.502 |
| 400_600 | invalid | 0.500 | 0.504 | 0.505 |

E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial:

| train \ test | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|
| pre | invalid | invalid | invalid | invalid |
| 0_200 | invalid | 0.516+ | 0.511+ | 0.502 |
| 200_400 | invalid | 0.514+ | 0.519+ | 0.505 |
| 400_600 | invalid | 0.515+ | 0.503 | 0.502 |

E_GENERIC|NCE|cbramod|pretrained_full:

| train \ test | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|
| pre | 0.500 | 0.499 | 0.497 | 0.496 |
| 0_200 | 0.503 | 0.507 | 0.504 | 0.501 |
| 200_400 | 0.499 | 0.504 | 0.513+ | 0.503 |
| 400_600 | 0.500 | 0.497 | 0.504 | 0.500 |

E_GENERIC|CS_SINGLE|cbramod|pretrained_full:

| train \ test | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|
| pre | 0.497 | 0.491 | 0.488− | 0.498 |
| 0_200 | 0.498 | 0.516+ | 0.507 | 0.501 |
| 200_400 | 0.501 | 0.513+ | 0.521+ | 0.508 |
| 400_600 | 0.501 | 0.510 | 0.509+ | 0.508 |

E_GENERIC|NCE|cbramod|random_full:

| train \ test | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|
| pre | 0.501 | 0.496 | 0.501 | 0.500 |
| 0_200 | 0.500 | 0.504 | 0.498 | 0.499 |
| 200_400 | 0.498 | 0.503 | 0.501 | 0.501 |
| 400_600 | 0.502 | 0.499 | 0.500 | 0.503 |

E_GENERIC|CS_SINGLE|cbramod|random_full:

| train \ test | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|
| pre | 0.501 | 0.498 | 0.498 | 0.499 |
| 0_200 | 0.498 | 0.509 | 0.509 | 0.505 |
| 200_400 | 0.501 | 0.511+ | 0.512+ | 0.504 |
| 400_600 | 0.498 | 0.506 | 0.504 | 0.502 |

E_GENERIC|NCE|reve|pretrained_full:

| train \ test | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|
| pre | 0.499 | 0.501 | 0.506 | 0.504 |
| 0_200 | 0.494 | 0.501 | 0.499 | 0.498 |
| 200_400 | 0.500 | 0.507 | 0.509 | 0.494 |
| 400_600 | 0.503 | 0.504 | 0.500 | 0.507 |

E_GENERIC|CS_SINGLE|reve|pretrained_full:

| train \ test | pre | 0_200 | 200_400 | 400_600 |
|---|---|---|---|---|
| pre | 0.494 | 0.498 | 0.499 | 0.498 |
| 0_200 | 0.500 | 0.505 | 0.505 | 0.501 |
| 200_400 | 0.502 | 0.503 | 0.514+ | 0.499 |
| 400_600 | 0.497 | 0.500 | 0.500 | 0.503 |

### Personal output adaptation (rank-4 residual; steps 0/5/20; support = first 10% / 30% blocks)

| Configuration | Support | AUC 0 / 5 / 20 | NLL bits 0 / 5 / 20 |
|---|---|---|---|
| E_LOCAL|NCE|lag_local_tokens|full | 0.1 | 0.517+ / 0.517+ / 0.516+ | 0.7171 / 0.7171 / 0.7235 |
| E_LOCAL|NCE|lag_local_tokens|full | 0.3 | 0.517+ / 0.518+ / 0.518+ | 0.7171 / 0.7170 / 0.7171 |
| E_LOCAL|CS_SINGLE|lag_local_tokens|full | 0.1 | 0.530+ / 0.530+ / 0.526+ | 0.7160 / 0.7159 / 0.7170 |
| E_LOCAL|CS_SINGLE|lag_local_tokens|full | 0.3 | 0.530+ / 0.530+ / 0.530+ | 0.7160 / 0.7158 / 0.7151 |
| E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial | 0.1 | 0.522+ / 0.522+ / 0.523+ | 0.7164 / 0.7164 / 0.7276 |
| E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial | 0.3 | 0.522+ / 0.522+ / 0.526+ | 0.7164 / 0.7162 / 0.7165 |
| E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial | 0.1 | 0.528+ / 0.528+ / 0.521+ | 0.7166 / 0.7164 / 0.7187 |
| E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial | 0.3 | 0.528+ / 0.528+ / 0.530+ | 0.7166 / 0.7163 / 0.7160 |
| E_GENERIC|NCE|cbramod|pretrained_full | 0.1 | 0.510+ / 0.510+ / 0.510+ | 0.7177 / 0.7177 / 0.7187 |
| E_GENERIC|NCE|cbramod|pretrained_full | 0.3 | 0.510+ / 0.510+ / 0.511+ | 0.7177 / 0.7177 / 0.7176 |
| E_GENERIC|CS_SINGLE|cbramod|pretrained_full | 0.1 | 0.532+ / 0.533+ / 0.525+ | 0.7154 / 0.7152 / 0.7189 |
| E_GENERIC|CS_SINGLE|cbramod|pretrained_full | 0.3 | 0.532+ / 0.533+ / 0.537+ | 0.7154 / 0.7151 / 0.7149 |
| E_GENERIC|NCE|cbramod|random_full | 0.1 | 0.509+ / 0.509+ / 0.509+ | 0.7173 / 0.7173 / 0.7180 |
| E_GENERIC|NCE|cbramod|random_full | 0.3 | 0.509+ / 0.510+ / 0.510+ | 0.7173 / 0.7173 / 0.7172 |
| E_GENERIC|CS_SINGLE|cbramod|random_full | 0.1 | 0.520+ / 0.520+ / 0.512+ | 0.7164 / 0.7164 / 0.7179 |
| E_GENERIC|CS_SINGLE|cbramod|random_full | 0.3 | 0.520+ / 0.520+ / 0.522+ | 0.7164 / 0.7163 / 0.7160 |
| E_GENERIC|NCE|reve|pretrained_full | 0.1 | 0.517+ / 0.517+ / 0.517+ | 0.7167 / 0.7167 / 0.7165 |
| E_GENERIC|NCE|reve|pretrained_full | 0.3 | 0.517+ / 0.517+ / 0.517+ | 0.7167 / 0.7167 / 0.7166 |
| E_GENERIC|CS_SINGLE|reve|pretrained_full | 0.1 | 0.518+ / 0.518+ / 0.519+ | 0.7171 / 0.7171 / 0.7171 |
| E_GENERIC|CS_SINGLE|reve|pretrained_full | 0.3 | 0.518+ / 0.518+ / 0.519+ | 0.7171 / 0.7171 / 0.7169 |

## Development (science_v2): simultaneous intervals over all endpoints × coefficients per model

Models: (a) all children, age in years + HA indicator; (b) HA only, age + device-use duration in years. Associations conditional on fitted models; not maturation or treatment effects. Only coefficient cells whose simultaneous interval excludes 0 are listed; every cell is in the CSV.

| Configuration / seed scope | Model | Endpoint | Coefficient | Estimate [simultaneous 95%] |
|---|---|---|---|---|

0 of 1088 coefficient cells exclude 0 under their simultaneous family.

### Prespecified stage means (descriptive; seed-mean configurations)

| Configuration | Stage | n | full AUC | history gain | history − twin | adapt 0.3/20 ΔNLL |
|---|---|---|---|---|---|---|
| E_GENERIC|CS_SINGLE|cbramod|pretrained_full/complete_seed_mean | <=2mo | 14 | 0.525 | -0.0029 | 0.0015 | -0.0022 |
| E_GENERIC|CS_SINGLE|cbramod|pretrained_full/complete_seed_mean | >2to<13mo | 5 | 0.553 | 0.0002 | 0.0042 | -0.0051 |
| E_GENERIC|CS_SINGLE|cbramod|pretrained_full/complete_seed_mean | >=13mo | 36 | 0.534 | -0.0006 | 0.0020 | 0.0019 |
| E_GENERIC|CS_SINGLE|cbramod|random_full/complete_seed_mean | <=2mo | 14 | 0.518 | -0.0041 | 0.0009 | 0.0004 |
| E_GENERIC|CS_SINGLE|cbramod|random_full/complete_seed_mean | >2to<13mo | 5 | 0.527 | -0.0030 | 0.0025 | -0.0004 |
| E_GENERIC|CS_SINGLE|cbramod|random_full/complete_seed_mean | >=13mo | 36 | 0.518 | -0.0024 | 0.0023 | 0.0003 |
| E_GENERIC|CS_SINGLE|reve|pretrained_full/3401 | <=2mo | 14 | 0.520 | -0.0037 | 0.0024 | 0.0001 |
| E_GENERIC|CS_SINGLE|reve|pretrained_full/3401 | >2to<13mo | 5 | 0.527 | -0.0048 | -0.0000 | 0.0001 |
| E_GENERIC|CS_SINGLE|reve|pretrained_full/3401 | >=13mo | 36 | 0.513 | -0.0042 | -0.0016 | 0.0003 |
| E_GENERIC|NCE|cbramod|pretrained_full/complete_seed_mean | <=2mo | 14 | 0.506 | -0.0044 | 0.0005 | -0.0001 |
| E_GENERIC|NCE|cbramod|pretrained_full/complete_seed_mean | >2to<13mo | 5 | 0.508 | -0.0046 | 0.0010 | 0.0001 |
| E_GENERIC|NCE|cbramod|pretrained_full/complete_seed_mean | >=13mo | 36 | 0.511 | -0.0026 | 0.0008 | 0.0002 |
| E_GENERIC|NCE|cbramod|random_full/complete_seed_mean | <=2mo | 14 | 0.511 | -0.0038 | 0.0021 | 0.0001 |
| E_GENERIC|NCE|cbramod|random_full/complete_seed_mean | >2to<13mo | 5 | 0.504 | -0.0050 | -0.0018 | -0.0001 |
| E_GENERIC|NCE|cbramod|random_full/complete_seed_mean | >=13mo | 36 | 0.510 | -0.0029 | 0.0006 | 0.0002 |
| E_GENERIC|NCE|reve|pretrained_full/3401 | <=2mo | 14 | 0.529 | -0.0024 | 0.0035 | 0.0000 |
| E_GENERIC|NCE|reve|pretrained_full/3401 | >2to<13mo | 5 | 0.514 | -0.0036 | 0.0010 | 0.0000 |
| E_GENERIC|NCE|reve|pretrained_full/3401 | >=13mo | 36 | 0.511 | -0.0030 | 0.0024 | 0.0002 |
| E_LOCAL|CS_SINGLE|lag_local_tokens|full/complete_seed_mean | <=2mo | 14 | 0.524 | -0.0037 | 0.0010 | -0.0008 |
| E_LOCAL|CS_SINGLE|lag_local_tokens|full/complete_seed_mean | >2to<13mo | 5 | 0.546 | -0.0024 | 0.0038 | 0.0005 |
| E_LOCAL|CS_SINGLE|lag_local_tokens|full/complete_seed_mean | >=13mo | 36 | 0.528 | -0.0010 | 0.0014 | 0.0013 |
| E_LOCAL|NCE|lag_local_tokens|full/complete_seed_mean | <=2mo | 14 | 0.511 | -0.0044 | 0.0000 | -0.0006 |
| E_LOCAL|NCE|lag_local_tokens|full/complete_seed_mean | >2to<13mo | 5 | 0.525 | -0.0037 | 0.0020 | 0.0005 |
| E_LOCAL|NCE|lag_local_tokens|full/complete_seed_mean | >=13mo | 36 | 0.516 | -0.0023 | 0.0015 | 0.0003 |
| E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial/complete_seed_mean | <=2mo | 14 | 0.517 | -0.0051 | -0.0002 | -0.0010 |
| E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial/complete_seed_mean | >2to<13mo | 5 | 0.540 | -0.0022 | 0.0047 | 0.0002 |
| E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial/complete_seed_mean | >=13mo | 36 | 0.528 | -0.0016 | 0.0015 | 0.0011 |
| E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial/complete_seed_mean | <=2mo | 14 | 0.510 | -0.0053 | -0.0003 | -0.0003 |
| E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial/complete_seed_mean | >2to<13mo | 5 | 0.532 | -0.0017 | 0.0036 | 0.0005 |
| E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial/complete_seed_mean | >=13mo | 36 | 0.523 | -0.0020 | 0.0017 | 0.0001 |

