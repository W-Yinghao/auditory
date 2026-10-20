# Public auditory prior science readout (300/300 targets, seed 3401)

Source `results/auditory_alignment_v3/aln34/prior_science/science.json` (job 1045980, 2026-10-18T18:09:41.893653+02:00), sha256 `319725f1e7727ee6…`. Readout only. Every arm-level and contrast cell: `results/auditory_alignment_v3/aln35/science_readout_v1/prior_science_cells.csv`.

Contrasts are arm minus scratch S (positive = arm better: higher r/AUC/gain, lower loss). Marks use each family's simultaneous band. AP/XP/J*/XM differ in target and supervision, not only in sound pairing (see AP_WRONG_RESULTS_V2 for the pairing test).

## dtu: arm − S, matched − mismatch r on the diagonal

| Objective | Model/raw | Target | Arm | -200 | 0 | 200 | 400 | 600 |
|---|---|---|---|---|---|---|---|---|
| CS_SINGLE | model | env direct | AP | +0.003 | -0.002 | -0.023 | +0.009 | +0.003 |
| CS_SINGLE | model | env direct | XP | -0.006 | -0.020 | -0.011 | -0.003 | +0.001 |
| CS_SINGLE | model | env direct | J* | -0.000 | -0.010 | -0.002 | +0.001 | +0.002 |
| CS_SINGLE | model | env direct | XM | -0.013 | -0.017 | -0.014 | +0.006 | +0.010 |
| CS_SINGLE | model | env history_conditional | AP | -0.028 | +0.007 | -0.011 | +0.007 | -0.002 |
| CS_SINGLE | model | env history_conditional | XP | -0.017 | -0.005 | -0.006 | +0.009 | -0.002 |
| CS_SINGLE | model | env history_conditional | J* | -0.028− | -0.005 | -0.014 | -0.000 | -0.008 |
| CS_SINGLE | model | env history_conditional | XM | -0.041− | +0.002 | -0.027 | -0.004 | -0.016 |
| CS_SINGLE | model | onset conditional | AP | -0.022 | -0.004 | -0.028 | -0.017 | -0.005 |
| CS_SINGLE | model | onset conditional | XP | -0.021 | -0.010 | -0.004 | -0.004 | -0.010 |
| CS_SINGLE | model | onset conditional | J* | -0.015 | -0.020 | -0.012 | -0.008 | -0.011 |
| CS_SINGLE | model | onset conditional | XM | -0.031− | -0.006 | -0.017 | -0.013 | -0.013 |
| CS_SINGLE | model | onset direct | AP | -0.022 | -0.004 | -0.028 | -0.017 | -0.005 |
| CS_SINGLE | model | onset direct | XP | -0.021 | -0.010 | -0.004 | -0.004 | -0.010 |
| CS_SINGLE | model | onset direct | J* | -0.015 | -0.020 | -0.012 | -0.008 | -0.011 |
| CS_SINGLE | model | onset direct | XM | -0.031− | -0.006 | -0.017 | -0.013 | -0.013 |
| CS_SINGLE | raw | env direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | model | env direct | AP | -0.002 | +0.008 | +0.005 | -0.008 | -0.004 |
| NCE | model | env direct | XP | +0.004 | -0.004 | +0.005 | +0.006 | +0.002 |
| NCE | model | env direct | J* | +0.002 | +0.004 | +0.007 | +0.006 | -0.001 |
| NCE | model | env direct | XM | +0.001 | +0.006 | +0.003 | +0.005 | +0.001 |
| NCE | model | env history_conditional | AP | +0.002 | +0.007 | +0.006 | +0.016 | +0.016 |
| NCE | model | env history_conditional | XP | +0.018 | -0.007 | +0.004 | +0.005 | +0.012 |
| NCE | model | env history_conditional | J* | +0.007 | +0.004 | +0.007 | +0.012 | +0.012 |
| NCE | model | env history_conditional | XM | +0.014 | -0.004 | +0.006 | -0.001 | +0.013 |
| NCE | model | onset conditional | AP | +0.006 | +0.001 | -0.011 | +0.016 | +0.002 |
| NCE | model | onset conditional | XP | +0.002 | -0.009 | -0.008 | -0.005 | -0.004 |
| NCE | model | onset conditional | J* | +0.008 | +0.011 | -0.012 | +0.014 | +0.004 |
| NCE | model | onset conditional | XM | +0.008 | -0.006 | +0.005 | -0.002 | -0.006 |
| NCE | model | onset direct | AP | +0.006 | +0.001 | -0.011 | +0.016 | +0.002 |
| NCE | model | onset direct | XP | +0.002 | -0.009 | -0.008 | -0.005 | -0.004 |
| NCE | model | onset direct | J* | +0.008 | +0.011 | -0.012 | +0.014 | +0.004 |
| NCE | model | onset direct | XM | +0.008 | -0.006 | +0.005 | -0.002 | -0.006 |
| NCE | raw | env direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |

## fau: arm − S, matched − mismatch r on the diagonal

| Objective | Model/raw | Target | Arm | -200 | 0 | 200 | 400 | 600 |
|---|---|---|---|---|---|---|---|---|
| CS_SINGLE | model | env direct | AP | -0.002 | -0.002 | -0.001 | -0.006 | -0.010 |
| CS_SINGLE | model | env direct | XP | -0.009 | -0.003 | -0.001 | +0.001 | -0.005 |
| CS_SINGLE | model | env direct | J* | -0.005 | -0.010 | -0.003 | -0.002 | -0.004 |
| CS_SINGLE | model | env direct | XM | -0.003 | -0.004 | -0.006 | +0.001 | -0.000 |
| CS_SINGLE | model | env history_conditional | AP | -0.008 | -0.007 | -0.016 | -0.001 | +0.001 |
| CS_SINGLE | model | env history_conditional | XP | -0.014 | -0.009 | -0.010 | +0.012 | -0.006 |
| CS_SINGLE | model | env history_conditional | J* | -0.014 | -0.014− | -0.011 | +0.002 | -0.000 |
| CS_SINGLE | model | env history_conditional | XM | -0.005 | -0.007 | -0.008 | +0.008 | -0.005 |
| CS_SINGLE | model | onset conditional | AP | -0.008 | -0.013 | -0.009 | -0.000 | +0.011 |
| CS_SINGLE | model | onset conditional | XP | -0.011 | -0.013 | -0.011 | +0.002 | -0.001 |
| CS_SINGLE | model | onset conditional | J* | -0.012 | -0.014− | -0.010 | -0.005 | +0.005 |
| CS_SINGLE | model | onset conditional | XM | -0.004 | -0.009 | -0.009 | +0.003 | -0.000 |
| CS_SINGLE | model | onset direct | AP | -0.008 | -0.013 | -0.009 | -0.000 | +0.011 |
| CS_SINGLE | model | onset direct | XP | -0.011 | -0.013 | -0.011 | +0.002 | -0.001 |
| CS_SINGLE | model | onset direct | J* | -0.012 | -0.014− | -0.010 | -0.005 | +0.005 |
| CS_SINGLE | model | onset direct | XM | -0.004 | -0.009 | -0.009 | +0.003 | -0.000 |
| CS_SINGLE | raw | env direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | model | env direct | AP | +0.009 | +0.006 | -0.005 | -0.002 | +0.000 |
| NCE | model | env direct | XP | +0.003 | -0.004 | -0.004 | +0.001 | +0.003 |
| NCE | model | env direct | J* | +0.011 | -0.002 | -0.001 | -0.002 | +0.000 |
| NCE | model | env direct | XM | +0.004 | +0.004 | -0.006 | -0.002 | +0.007 |
| NCE | model | env history_conditional | AP | +0.007 | +0.007 | +0.012 | +0.004 | -0.001 |
| NCE | model | env history_conditional | XP | +0.007 | -0.005 | +0.005 | +0.001 | -0.002 |
| NCE | model | env history_conditional | J* | +0.010 | +0.004 | +0.009 | +0.004 | -0.002 |
| NCE | model | env history_conditional | XM | +0.007 | -0.000 | +0.004 | -0.002 | -0.004 |
| NCE | model | onset conditional | AP | -0.002 | -0.004 | +0.008 | -0.002 | +0.002 |
| NCE | model | onset conditional | XP | +0.002 | -0.005 | +0.010 | -0.007 | +0.001 |
| NCE | model | onset conditional | J* | +0.002 | -0.006 | +0.011 | -0.005 | -0.004 |
| NCE | model | onset conditional | XM | +0.003 | -0.002 | +0.011 | -0.005 | +0.001 |
| NCE | model | onset direct | AP | -0.002 | -0.004 | +0.008 | -0.002 | +0.002 |
| NCE | model | onset direct | XP | +0.002 | -0.005 | +0.010 | -0.007 | +0.001 |
| NCE | model | onset direct | J* | +0.002 | -0.006 | +0.011 | -0.005 | -0.004 |
| NCE | model | onset direct | XM | +0.003 | -0.002 | +0.011 | -0.005 | +0.001 |
| NCE | raw | env direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |

## federici: arm − S, matched − mismatch r on the diagonal

| Objective | Model/raw | Target | Arm | -200 | 0 | 200 | 400 | 600 |
|---|---|---|---|---|---|---|---|---|
| CS_SINGLE | model | env direct | AP | +0.000 | -0.001 | +0.017 | -0.011 | +0.011 |
| CS_SINGLE | model | env direct | XP | -0.004 | -0.013 | +0.008 | -0.015 | -0.009 |
| CS_SINGLE | model | env direct | J* | -0.003 | -0.009 | +0.014 | +0.013 | -0.005 |
| CS_SINGLE | model | env direct | XM | -0.017 | -0.013 | +0.001 | -0.005 | -0.006 |
| CS_SINGLE | model | env history_conditional | AP | -0.030 | +0.008 | +0.012 | -0.013 | -0.003 |
| CS_SINGLE | model | env history_conditional | XP | -0.021 | +0.009 | +0.013 | -0.009 | -0.016 |
| CS_SINGLE | model | env history_conditional | J* | -0.016 | +0.008 | +0.003 | +0.009 | -0.020 |
| CS_SINGLE | model | env history_conditional | XM | -0.017 | -0.002 | -0.015 | -0.028 | -0.015 |
| CS_SINGLE | model | onset conditional | AP | -0.021 | +0.007 | +0.006 | +0.012 | +0.009 |
| CS_SINGLE | model | onset conditional | XP | -0.006 | +0.012 | +0.012 | -0.006 | +0.001 |
| CS_SINGLE | model | onset conditional | J* | -0.029 | +0.003 | +0.005 | +0.010 | +0.003 |
| CS_SINGLE | model | onset conditional | XM | -0.022 | +0.007 | -0.017 | +0.004 | -0.000 |
| CS_SINGLE | model | onset direct | AP | -0.021 | +0.007 | +0.006 | +0.012 | +0.010 |
| CS_SINGLE | model | onset direct | XP | -0.006 | +0.012 | +0.012 | -0.006 | +0.001 |
| CS_SINGLE | model | onset direct | J* | -0.028 | +0.003 | +0.005 | +0.010 | +0.003 |
| CS_SINGLE | model | onset direct | XM | -0.022 | +0.007 | -0.017 | +0.004 | -0.000 |
| CS_SINGLE | raw | env direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | env history_conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| CS_SINGLE | raw | onset direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | model | env direct | AP | -0.016 | -0.006 | +0.006 | +0.010 | +0.002 |
| NCE | model | env direct | XP | -0.013 | +0.004 | +0.008 | +0.009 | -0.001 |
| NCE | model | env direct | J* | -0.002 | +0.005 | +0.009 | +0.002 | -0.000 |
| NCE | model | env direct | XM | +0.009 | +0.003 | +0.018 | +0.016 | +0.004 |
| NCE | model | env history_conditional | AP | -0.003 | -0.014 | +0.008 | +0.007 | +0.014 |
| NCE | model | env history_conditional | XP | -0.008 | -0.003 | +0.009 | -0.010 | -0.024 |
| NCE | model | env history_conditional | J* | +0.006 | +0.004 | +0.016 | +0.013 | -0.011 |
| NCE | model | env history_conditional | XM | +0.014 | +0.017 | +0.003 | +0.003 | +0.006 |
| NCE | model | onset conditional | AP | +0.023 | +0.009 | +0.013 | -0.005 | +0.009 |
| NCE | model | onset conditional | XP | +0.017 | -0.003 | -0.003 | -0.009 | -0.012 |
| NCE | model | onset conditional | J* | +0.004 | -0.022 | +0.013 | -0.001 | -0.006 |
| NCE | model | onset conditional | XM | +0.017 | -0.003 | -0.007 | -0.012 | -0.014 |
| NCE | model | onset direct | AP | +0.023 | +0.009 | +0.013 | -0.005 | +0.009 |
| NCE | model | onset direct | XP | +0.017 | -0.003 | -0.003 | -0.009 | -0.012 |
| NCE | model | onset direct | J* | +0.004 | -0.022 | +0.013 | -0.001 | -0.006 |
| NCE | model | onset direct | XM | +0.017 | -0.003 | -0.007 | -0.012 | -0.014 |
| NCE | raw | env direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | env history_conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset conditional | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | AP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | XP | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | J* | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| NCE | raw | onset direct | XM | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |

## Hearing-group differences in arm − S effects (cells whose simultaneous band excludes 0)

11 of 45728 group-difference cells exclude 0.

| Dataset | Scope | Metric | Comparison | Cell | Estimate [band] |
|---|---|---|---|---|---|
| dtu | public/CS_SINGLE/model/env/direct | mismatch_minus_matched_mse | hi minus nh | J*/400/400 versus S/400/400 | -0.0071 [-0.0142, -0.0000] |
| dtu | public/NCE/model/env/direct | matched_minus_mismatch_r | hi minus nh | J*/0/0 versus S/0/0 | +0.0295 [+0.0018, +0.0572] |
| fau | public/CS_SINGLE/model/env/history_conditional | mismatch_minus_matched_mse | ci minus ha | J*/0/-200 versus S/0/-200 | -0.0078 [-0.0152, -0.0004] |
| fau | public/CS_SINGLE/model/onset/conditional | r | ci minus ha | AP/200/-200 versus S/200/-200 | +0.0392 [+0.0036, +0.0748] |
| fau | public/CS_SINGLE/model/onset/direct | r | ci minus ha | AP/200/-200 versus S/200/-200 | +0.0392 [+0.0041, +0.0742] |
| fau | public/NCE/model/env/direct | mismatch_minus_matched_mse | ci minus ha | J*/200/0 versus S/200/0 | +0.0085 [+0.0011, +0.0159] |
| fau | public/NCE/model/env/direct | r | ci minus ha | XP/400/-200 versus S/400/-200 | +0.0361 [+0.0002, +0.0719] |
| fau | public/NCE/model/env/direct | r | ci minus ha | J*/400/-200 versus S/400/-200 | +0.0342 [+0.0015, +0.0668] |
| fau | public/NCE/model/env/direct | r | ci minus th | J*/-200/-200 versus S/-200/-200 | -0.0370 [-0.0740, -0.0000] |
| fau | public/NCE/model/env/history_conditional | matched_minus_mismatch_r | ci minus ha | J*/0/600 versus S/0/600 | -0.0208 [-0.0394, -0.0022] |
| federici | public/CS_SINGLE/model/env/history_conditional | matched_minus_mismatch_r | HC minus HC-v | XM/-200/0 versus S/-200/0 | +0.1402 [+0.0008, +0.2796] |

## Private (64 children): arm − S

| Scope | Metric | Contrast | all | HA | NH |
|---|---|---|---|---|---|
| private/adapt/CS_SINGLE/0.1 | auc | AP/0 versus S/0 | -0.0071 | -0.0053 | -0.0180 |
| private/adapt/CS_SINGLE/0.1 | auc | AP/20 versus S/20 | -0.0084 | -0.0074 | -0.0145 |
| private/adapt/CS_SINGLE/0.1 | auc | AP/5 versus S/5 | -0.0071 | -0.0053 | -0.0179 |
| private/adapt/CS_SINGLE/0.1 | auc | XP/0 versus S/0 | -0.0015 | +0.0003 | -0.0126 |
| private/adapt/CS_SINGLE/0.1 | auc | XP/20 versus S/20 | -0.0000 | +0.0010 | -0.0065 |
| private/adapt/CS_SINGLE/0.1 | auc | XP/5 versus S/5 | -0.0016 | +0.0002 | -0.0123 |
| private/adapt/CS_SINGLE/0.1 | auc | J*/0 versus S/0 | -0.0101 | -0.0108 | -0.0053 |
| private/adapt/CS_SINGLE/0.1 | auc | J*/20 versus S/20 | -0.0125 | -0.0131 | -0.0083 |
| private/adapt/CS_SINGLE/0.1 | auc | J*/5 versus S/5 | -0.0101 | -0.0109 | -0.0053 |
| private/adapt/CS_SINGLE/0.1 | auc | XM/0 versus S/0 | -0.0046 | -0.0023 | -0.0190 |
| private/adapt/CS_SINGLE/0.1 | auc | XM/20 versus S/20 | -0.0037 | -0.0006 | -0.0225 |
| private/adapt/CS_SINGLE/0.1 | auc | XM/5 versus S/5 | -0.0045 | -0.0022 | -0.0185 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | AP/0 versus S/0 | -0.0001 | +0.0002 | -0.0021 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | AP/20 versus S/20 | -0.0008 | -0.0005 | -0.0024 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | AP/5 versus S/5 | -0.0002 | +0.0002 | -0.0021 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | XP/0 versus S/0 | -0.0001 | -0.0002 | +0.0006 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | XP/20 versus S/20 | -0.0004 | -0.0006 | +0.0012 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | XP/5 versus S/5 | -0.0001 | -0.0003 | +0.0006 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | J*/0 versus S/0 | -0.0012 | -0.0015 | +0.0004 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | J*/20 versus S/20 | -0.0023 | -0.0029 | +0.0010 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | J*/5 versus S/5 | -0.0013 | -0.0015 | +0.0005 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | XM/0 versus S/0 | -0.0016 | -0.0014 | -0.0029 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | XM/20 versus S/20 | -0.0024 | -0.0024 | -0.0027 |
| private/adapt/CS_SINGLE/0.1 | history_gain_bits | XM/5 versus S/5 | -0.0017 | -0.0015 | -0.0029 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | AP/0 versus S/0 | -0.0011 | -0.0008 | -0.0033 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | AP/20 versus S/20 | -0.0014 | -0.0010 | -0.0040 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | AP/5 versus S/5 | -0.0011 | -0.0008 | -0.0032 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | XP/0 versus S/0 | -0.0002 | -0.0000 | -0.0016 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | XP/20 versus S/20 | -0.0001 | +0.0001 | -0.0014 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | XP/5 versus S/5 | -0.0003 | -0.0001 | -0.0016 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | J*/0 versus S/0 | -0.0021 | -0.0023 | -0.0010 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | J*/20 versus S/20 | -0.0029− | -0.0032− | -0.0005 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | J*/5 versus S/5 | -0.0022 | -0.0024 | -0.0009 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | XM/0 versus S/0 | -0.0014 | -0.0010 | -0.0039 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | XM/20 versus S/20 | -0.0015 | -0.0011 | -0.0039 |
| private/adapt/CS_SINGLE/0.1 | nll_bits | XM/5 versus S/5 | -0.0014 | -0.0010 | -0.0038 |
| private/adapt/CS_SINGLE/0.3 | auc | AP/0 versus S/0 | -0.0071 | -0.0053 | -0.0180 |
| private/adapt/CS_SINGLE/0.3 | auc | AP/20 versus S/20 | -0.0061 | -0.0050 | -0.0130 |
| private/adapt/CS_SINGLE/0.3 | auc | AP/5 versus S/5 | -0.0069 | -0.0051 | -0.0178 |
| private/adapt/CS_SINGLE/0.3 | auc | XP/0 versus S/0 | -0.0015 | +0.0003 | -0.0126 |
| private/adapt/CS_SINGLE/0.3 | auc | XP/20 versus S/20 | +0.0003 | +0.0013 | -0.0058 |
| private/adapt/CS_SINGLE/0.3 | auc | XP/5 versus S/5 | -0.0014 | +0.0004 | -0.0122 |
| private/adapt/CS_SINGLE/0.3 | auc | J*/0 versus S/0 | -0.0101 | -0.0108 | -0.0053 |
| private/adapt/CS_SINGLE/0.3 | auc | J*/20 versus S/20 | -0.0093 | -0.0107 | -0.0005 |
| private/adapt/CS_SINGLE/0.3 | auc | J*/5 versus S/5 | -0.0100 | -0.0108 | -0.0051 |
| private/adapt/CS_SINGLE/0.3 | auc | XM/0 versus S/0 | -0.0046 | -0.0023 | -0.0190 |
| private/adapt/CS_SINGLE/0.3 | auc | XM/20 versus S/20 | -0.0052 | -0.0038 | -0.0141 |
| private/adapt/CS_SINGLE/0.3 | auc | XM/5 versus S/5 | -0.0044 | -0.0021 | -0.0183 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | AP/0 versus S/0 | -0.0001 | +0.0002 | -0.0021 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | AP/20 versus S/20 | -0.0003 | -0.0000 | -0.0023 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | AP/5 versus S/5 | -0.0001 | +0.0002 | -0.0021 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | XP/0 versus S/0 | -0.0001 | -0.0002 | +0.0006 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | XP/20 versus S/20 | -0.0002 | -0.0004 | +0.0012 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | XP/5 versus S/5 | -0.0001 | -0.0002 | +0.0006 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | J*/0 versus S/0 | -0.0012 | -0.0015 | +0.0004 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | J*/20 versus S/20 | -0.0012 | -0.0015 | +0.0006 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | J*/5 versus S/5 | -0.0012 | -0.0015 | +0.0005 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | XM/0 versus S/0 | -0.0016 | -0.0014 | -0.0029 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | XM/20 versus S/20 | -0.0019 | -0.0020 | -0.0014 |
| private/adapt/CS_SINGLE/0.3 | history_gain_bits | XM/5 versus S/5 | -0.0016 | -0.0014 | -0.0028 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | AP/0 versus S/0 | -0.0011 | -0.0008 | -0.0033 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | AP/20 versus S/20 | -0.0014 | -0.0010 | -0.0039 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | AP/5 versus S/5 | -0.0011 | -0.0008 | -0.0033 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | XP/0 versus S/0 | -0.0002 | -0.0000 | -0.0016 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | XP/20 versus S/20 | -0.0004 | -0.0002 | -0.0017 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | XP/5 versus S/5 | -0.0003 | -0.0001 | -0.0016 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | J*/0 versus S/0 | -0.0021 | -0.0023 | -0.0010 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | J*/20 versus S/20 | -0.0024 | -0.0026 | -0.0013 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | J*/5 versus S/5 | -0.0022 | -0.0023 | -0.0010 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | XM/0 versus S/0 | -0.0014 | -0.0010 | -0.0039 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | XM/20 versus S/20 | -0.0019 | -0.0017 | -0.0032 |
| private/adapt/CS_SINGLE/0.3 | nll_bits | XM/5 versus S/5 | -0.0014 | -0.0010 | -0.0038 |
| private/adapt/NCE/0.1 | auc | AP/0 versus S/0 | +0.0173+ | +0.0149+ | +0.0323 |
| private/adapt/NCE/0.1 | auc | AP/20 versus S/20 | +0.0184+ | +0.0161+ | +0.0326+ |
| private/adapt/NCE/0.1 | auc | AP/5 versus S/5 | +0.0174+ | +0.0151+ | +0.0316 |
| private/adapt/NCE/0.1 | auc | XP/0 versus S/0 | +0.0047 | +0.0047 | +0.0043 |
| private/adapt/NCE/0.1 | auc | XP/20 versus S/20 | +0.0048 | +0.0054 | +0.0011 |
| private/adapt/NCE/0.1 | auc | XP/5 versus S/5 | +0.0047 | +0.0048 | +0.0039 |
| private/adapt/NCE/0.1 | auc | J*/0 versus S/0 | +0.0148+ | +0.0141+ | +0.0192 |
| private/adapt/NCE/0.1 | auc | J*/20 versus S/20 | +0.0150+ | +0.0146+ | +0.0174 |
| private/adapt/NCE/0.1 | auc | J*/5 versus S/5 | +0.0149+ | +0.0143+ | +0.0190 |
| private/adapt/NCE/0.1 | auc | XM/0 versus S/0 | +0.0118+ | +0.0110+ | +0.0164 |
| private/adapt/NCE/0.1 | auc | XM/20 versus S/20 | +0.0124+ | +0.0116+ | +0.0172 |
| private/adapt/NCE/0.1 | auc | XM/5 versus S/5 | +0.0119+ | +0.0111+ | +0.0166 |
| private/adapt/NCE/0.1 | history_gain_bits | AP/0 versus S/0 | +0.0033 | +0.0030 | +0.0047 |
| private/adapt/NCE/0.1 | history_gain_bits | AP/20 versus S/20 | +0.0099 | +0.0100 | +0.0098+ |
| private/adapt/NCE/0.1 | history_gain_bits | AP/5 versus S/5 | +0.0026 | +0.0023 | +0.0045 |
| private/adapt/NCE/0.1 | history_gain_bits | XP/0 versus S/0 | +0.0002 | +0.0001 | +0.0007 |
| private/adapt/NCE/0.1 | history_gain_bits | XP/20 versus S/20 | +0.0130 | +0.0143 | +0.0050 |
| private/adapt/NCE/0.1 | history_gain_bits | XP/5 versus S/5 | +0.0007 | +0.0007 | +0.0003 |
| private/adapt/NCE/0.1 | history_gain_bits | J*/0 versus S/0 | +0.0021 | +0.0021 | +0.0018 |
| private/adapt/NCE/0.1 | history_gain_bits | J*/20 versus S/20 | +0.0026 | +0.0021 | +0.0056 |
| private/adapt/NCE/0.1 | history_gain_bits | J*/5 versus S/5 | -0.0017 | -0.0020 | +0.0004 |
| private/adapt/NCE/0.1 | history_gain_bits | XM/0 versus S/0 | +0.0020 | +0.0021 | +0.0019 |
| private/adapt/NCE/0.1 | history_gain_bits | XM/20 versus S/20 | +0.0073 | +0.0078 | +0.0045 |
| private/adapt/NCE/0.1 | history_gain_bits | XM/5 versus S/5 | -0.0139 | -0.0152 | -0.0055 |
| private/adapt/NCE/0.1 | nll_bits | AP/0 versus S/0 | +0.0035 | +0.0032 | +0.0055 |
| private/adapt/NCE/0.1 | nll_bits | AP/20 versus S/20 | -0.0063 | -0.0090 | +0.0101 |
| private/adapt/NCE/0.1 | nll_bits | AP/5 versus S/5 | -0.0027 | -0.0032 | +0.0004 |
| private/adapt/NCE/0.1 | nll_bits | XP/0 versus S/0 | +0.0006 | +0.0006 | +0.0002 |
| private/adapt/NCE/0.1 | nll_bits | XP/20 versus S/20 | +0.0014 | +0.0009 | +0.0043 |
| private/adapt/NCE/0.1 | nll_bits | XP/5 versus S/5 | +0.0003 | +0.0004 | -0.0006 |
| private/adapt/NCE/0.1 | nll_bits | J*/0 versus S/0 | +0.0021 | +0.0020 | +0.0027 |
| private/adapt/NCE/0.1 | nll_bits | J*/20 versus S/20 | -0.0015 | -0.0027 | +0.0058 |
| private/adapt/NCE/0.1 | nll_bits | J*/5 versus S/5 | -0.0078 | -0.0082 | -0.0057 |
| private/adapt/NCE/0.1 | nll_bits | XM/0 versus S/0 | +0.0016 | +0.0015 | +0.0021 |
| private/adapt/NCE/0.1 | nll_bits | XM/20 versus S/20 | +0.0007 | +0.0004 | +0.0028 |
| private/adapt/NCE/0.1 | nll_bits | XM/5 versus S/5 | -0.0247 | -0.0253 | -0.0215− |
| private/adapt/NCE/0.3 | auc | AP/0 versus S/0 | +0.0173+ | +0.0149+ | +0.0323 |
| private/adapt/NCE/0.3 | auc | AP/20 versus S/20 | +0.0210+ | +0.0201+ | +0.0263 |
| private/adapt/NCE/0.3 | auc | AP/5 versus S/5 | +0.0180+ | +0.0158+ | +0.0316 |
| private/adapt/NCE/0.3 | auc | XP/0 versus S/0 | +0.0047 | +0.0047 | +0.0043 |
| private/adapt/NCE/0.3 | auc | XP/20 versus S/20 | +0.0058 | +0.0060 | +0.0043 |
| private/adapt/NCE/0.3 | auc | XP/5 versus S/5 | +0.0048 | +0.0049 | +0.0041 |
| private/adapt/NCE/0.3 | auc | J*/0 versus S/0 | +0.0148+ | +0.0141+ | +0.0192 |
| private/adapt/NCE/0.3 | auc | J*/20 versus S/20 | +0.0203+ | +0.0210+ | +0.0158 |
| private/adapt/NCE/0.3 | auc | J*/5 versus S/5 | +0.0153+ | +0.0147+ | +0.0190 |
| private/adapt/NCE/0.3 | auc | XM/0 versus S/0 | +0.0118+ | +0.0110+ | +0.0164 |
| private/adapt/NCE/0.3 | auc | XM/20 versus S/20 | +0.0149+ | +0.0145+ | +0.0175 |
| private/adapt/NCE/0.3 | auc | XM/5 versus S/5 | +0.0120+ | +0.0112+ | +0.0165 |
| private/adapt/NCE/0.3 | history_gain_bits | AP/0 versus S/0 | +0.0033+ | +0.0030 | +0.0047 |
| private/adapt/NCE/0.3 | history_gain_bits | AP/20 versus S/20 | +0.0024 | +0.0020 | +0.0049 |
| private/adapt/NCE/0.3 | history_gain_bits | AP/5 versus S/5 | +0.0037 | +0.0035 | +0.0047 |
| private/adapt/NCE/0.3 | history_gain_bits | XP/0 versus S/0 | +0.0002 | +0.0001 | +0.0007 |
| private/adapt/NCE/0.3 | history_gain_bits | XP/20 versus S/20 | -0.0012 | -0.0015 | +0.0008 |
| private/adapt/NCE/0.3 | history_gain_bits | XP/5 versus S/5 | -0.0002 | -0.0003 | +0.0004 |
| private/adapt/NCE/0.3 | history_gain_bits | J*/0 versus S/0 | +0.0021 | +0.0021 | +0.0018 |
| private/adapt/NCE/0.3 | history_gain_bits | J*/20 versus S/20 | +0.0025 | +0.0025 | +0.0021 |
| private/adapt/NCE/0.3 | history_gain_bits | J*/5 versus S/5 | +0.0039 | +0.0042 | +0.0017 |
| private/adapt/NCE/0.3 | history_gain_bits | XM/0 versus S/0 | +0.0020 | +0.0021 | +0.0019 |
| private/adapt/NCE/0.3 | history_gain_bits | XM/20 versus S/20 | +0.0012 | +0.0011 | +0.0023 |
| private/adapt/NCE/0.3 | history_gain_bits | XM/5 versus S/5 | +0.0027 | +0.0030 | +0.0009 |
| private/adapt/NCE/0.3 | nll_bits | AP/0 versus S/0 | +0.0035+ | +0.0032+ | +0.0055 |
| private/adapt/NCE/0.3 | nll_bits | AP/20 versus S/20 | +0.0042+ | +0.0040+ | +0.0053 |
| private/adapt/NCE/0.3 | nll_bits | AP/5 versus S/5 | +0.0033+ | +0.0032+ | +0.0040 |
| private/adapt/NCE/0.3 | nll_bits | XP/0 versus S/0 | +0.0006 | +0.0006 | +0.0002 |
| private/adapt/NCE/0.3 | nll_bits | XP/20 versus S/20 | +0.0009 | +0.0010 | +0.0008 |
| private/adapt/NCE/0.3 | nll_bits | XP/5 versus S/5 | +0.0007 | +0.0008 | -0.0001 |
| private/adapt/NCE/0.3 | nll_bits | J*/0 versus S/0 | +0.0021 | +0.0020 | +0.0027 |
| private/adapt/NCE/0.3 | nll_bits | J*/20 versus S/20 | +0.0031+ | +0.0031+ | +0.0027 |
| private/adapt/NCE/0.3 | nll_bits | J*/5 versus S/5 | +0.0016 | +0.0018 | +0.0003 |
| private/adapt/NCE/0.3 | nll_bits | XM/0 versus S/0 | +0.0016 | +0.0015 | +0.0021 |
| private/adapt/NCE/0.3 | nll_bits | XM/20 versus S/20 | +0.0020 | +0.0019 | +0.0026 |
| private/adapt/NCE/0.3 | nll_bits | XM/5 versus S/5 | +0.0012 | +0.0015 | -0.0004 |
| private/tg/CS_SINGLE/original_calibration | auc | AP/0_200/0_200 versus S/0_200/0_200 | +0.0015 | +0.0002 | +0.0097 |
| private/tg/CS_SINGLE/original_calibration | auc | AP/0_200/200_400 versus S/0_200/200_400 | -0.0005 | -0.0035 | +0.0177 |
| private/tg/CS_SINGLE/original_calibration | auc | AP/0_200/400_600 versus S/0_200/400_600 | +0.0074 | +0.0065 | +0.0131 |
| private/tg/CS_SINGLE/original_calibration | auc | AP/200_400/0_200 versus S/200_400/0_200 | -0.0073 | -0.0074 | -0.0065 |
| private/tg/CS_SINGLE/original_calibration | auc | AP/200_400/200_400 versus S/200_400/200_400 | -0.0032 | -0.0014 | -0.0137 |
| private/tg/CS_SINGLE/original_calibration | auc | AP/200_400/400_600 versus S/200_400/400_600 | +0.0057 | +0.0089 | -0.0139 |
| private/tg/CS_SINGLE/original_calibration | auc | AP/400_600/0_200 versus S/400_600/0_200 | +0.0061 | +0.0010 | +0.0372 |
| private/tg/CS_SINGLE/original_calibration | auc | AP/400_600/200_400 versus S/400_600/200_400 | +0.0299+ | +0.0279+ | +0.0421 |
| private/tg/CS_SINGLE/original_calibration | auc | AP/400_600/400_600 versus S/400_600/400_600 | -0.0013 | -0.0013 | -0.0011 |
| private/tg/CS_SINGLE/original_calibration | auc | XP/0_200/0_200 versus S/0_200/0_200 | +0.0094 | +0.0077 | +0.0200 |
| private/tg/CS_SINGLE/original_calibration | auc | XP/0_200/200_400 versus S/0_200/200_400 | -0.0015 | -0.0012 | -0.0036 |
| private/tg/CS_SINGLE/original_calibration | auc | XP/0_200/400_600 versus S/0_200/400_600 | +0.0081 | +0.0063 | +0.0193 |
| private/tg/CS_SINGLE/original_calibration | auc | XP/200_400/0_200 versus S/200_400/0_200 | -0.0023 | +0.0003 | -0.0181 |
| private/tg/CS_SINGLE/original_calibration | auc | XP/200_400/200_400 versus S/200_400/200_400 | -0.0051 | -0.0032 | -0.0162 |
| private/tg/CS_SINGLE/original_calibration | auc | XP/200_400/400_600 versus S/200_400/400_600 | +0.0008 | +0.0028 | -0.0116 |
| private/tg/CS_SINGLE/original_calibration | auc | XP/400_600/0_200 versus S/400_600/0_200 | +0.0045 | -0.0016 | +0.0420 |
| private/tg/CS_SINGLE/original_calibration | auc | XP/400_600/200_400 versus S/400_600/200_400 | +0.0129 | +0.0099 | +0.0310 |
| private/tg/CS_SINGLE/original_calibration | auc | XP/400_600/400_600 versus S/400_600/400_600 | -0.0019 | -0.0011 | -0.0070 |
| private/tg/CS_SINGLE/original_calibration | auc | J*/0_200/0_200 versus S/0_200/0_200 | +0.0059 | +0.0050 | +0.0114 |
| private/tg/CS_SINGLE/original_calibration | auc | J*/0_200/200_400 versus S/0_200/200_400 | -0.0066 | -0.0068 | -0.0050 |
| private/tg/CS_SINGLE/original_calibration | auc | J*/0_200/400_600 versus S/0_200/400_600 | +0.0114 | +0.0133 | +0.0002 |
| private/tg/CS_SINGLE/original_calibration | auc | J*/200_400/0_200 versus S/200_400/0_200 | -0.0027 | -0.0008 | -0.0144 |
| private/tg/CS_SINGLE/original_calibration | auc | J*/200_400/200_400 versus S/200_400/200_400 | -0.0115− | -0.0092 | -0.0256 |
| private/tg/CS_SINGLE/original_calibration | auc | J*/200_400/400_600 versus S/200_400/400_600 | +0.0038 | +0.0053 | -0.0057 |
| private/tg/CS_SINGLE/original_calibration | auc | J*/400_600/0_200 versus S/400_600/0_200 | -0.0035 | -0.0066 | +0.0154 |
| private/tg/CS_SINGLE/original_calibration | auc | J*/400_600/200_400 versus S/400_600/200_400 | +0.0024 | -0.0003 | +0.0189 |
| private/tg/CS_SINGLE/original_calibration | auc | J*/400_600/400_600 versus S/400_600/400_600 | -0.0082 | -0.0069 | -0.0160 |
| private/tg/CS_SINGLE/original_calibration | auc | XM/0_200/0_200 versus S/0_200/0_200 | +0.0072 | +0.0045 | +0.0241 |
| private/tg/CS_SINGLE/original_calibration | auc | XM/0_200/200_400 versus S/0_200/200_400 | -0.0045 | -0.0082 | +0.0175 |
| private/tg/CS_SINGLE/original_calibration | auc | XM/0_200/400_600 versus S/0_200/400_600 | +0.0149 | +0.0139 | +0.0210 |
| private/tg/CS_SINGLE/original_calibration | auc | XM/200_400/0_200 versus S/200_400/0_200 | +0.0078 | +0.0082 | +0.0048 |
| private/tg/CS_SINGLE/original_calibration | auc | XM/200_400/200_400 versus S/200_400/200_400 | -0.0021 | +0.0007 | -0.0189 |
| private/tg/CS_SINGLE/original_calibration | auc | XM/200_400/400_600 versus S/200_400/400_600 | +0.0028 | +0.0051 | -0.0116 |
| private/tg/CS_SINGLE/original_calibration | auc | XM/400_600/0_200 versus S/400_600/0_200 | +0.0074 | +0.0043 | +0.0262 |
| private/tg/CS_SINGLE/original_calibration | auc | XM/400_600/200_400 versus S/400_600/200_400 | +0.0201+ | +0.0187+ | +0.0285 |
| private/tg/CS_SINGLE/original_calibration | auc | XM/400_600/400_600 versus S/400_600/400_600 | -0.0026 | -0.0023 | -0.0042 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | AP/0_200/0_200 versus S/0_200/0_200 | -0.0005 | -0.0004 | -0.0011 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | AP/0_200/200_400 versus S/0_200/200_400 | -0.0344− | -0.0355− | -0.0277 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | AP/0_200/400_600 versus S/0_200/400_600 | -0.0240− | -0.0247− | -0.0200 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | AP/200_400/0_200 versus S/200_400/0_200 | -0.0108− | -0.0114 | -0.0070 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | AP/200_400/200_400 versus S/200_400/200_400 | -0.0017 | -0.0012 | -0.0047 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | AP/200_400/400_600 versus S/200_400/400_600 | -0.0142− | -0.0137− | -0.0173 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | AP/400_600/0_200 versus S/400_600/0_200 | +0.0689 | +0.0623 | +0.1089 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | AP/400_600/200_400 versus S/400_600/200_400 | +0.1635+ | +0.1544+ | +0.2192 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | AP/400_600/400_600 versus S/400_600/400_600 | -0.0001 | -0.0001 | +0.0000 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XP/0_200/0_200 versus S/0_200/0_200 | +0.0008 | +0.0007 | +0.0018 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XP/0_200/200_400 versus S/0_200/200_400 | -0.0168− | -0.0145− | -0.0311 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XP/0_200/400_600 versus S/0_200/400_600 | -0.0307− | -0.0309− | -0.0291 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XP/200_400/0_200 versus S/200_400/0_200 | +0.0037 | +0.0045 | -0.0017 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XP/200_400/200_400 versus S/200_400/200_400 | -0.0014 | -0.0011 | -0.0036 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XP/200_400/400_600 versus S/200_400/400_600 | -0.0034 | -0.0029 | -0.0069 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XP/400_600/0_200 versus S/400_600/0_200 | +0.1088+ | +0.1045+ | +0.1349 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XP/400_600/200_400 versus S/400_600/200_400 | +0.1975+ | +0.1898+ | +0.2446 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XP/400_600/400_600 versus S/400_600/400_600 | +0.0002 | +0.0004 | -0.0011 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | J*/0_200/0_200 versus S/0_200/0_200 | +0.0003 | +0.0001 | +0.0012 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | J*/0_200/200_400 versus S/0_200/200_400 | -0.0123− | -0.0116 | -0.0166 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | J*/0_200/400_600 versus S/0_200/400_600 | -0.0096 | -0.0093 | -0.0110 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | J*/200_400/0_200 versus S/200_400/0_200 | -0.0942− | -0.0936− | -0.0980 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | J*/200_400/200_400 versus S/200_400/200_400 | -0.0012 | -0.0007 | -0.0045 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | J*/200_400/400_600 versus S/200_400/400_600 | -0.0444− | -0.0442− | -0.0453 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | J*/400_600/0_200 versus S/400_600/0_200 | +0.0909+ | +0.0867+ | +0.1166 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | J*/400_600/200_400 versus S/400_600/200_400 | +0.1760+ | +0.1682+ | +0.2239 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | J*/400_600/400_600 versus S/400_600/400_600 | -0.0012 | -0.0011 | -0.0018 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XM/0_200/0_200 versus S/0_200/0_200 | +0.0007 | +0.0005 | +0.0016 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XM/0_200/200_400 versus S/0_200/200_400 | -0.0061 | -0.0068 | -0.0017 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XM/0_200/400_600 versus S/0_200/400_600 | -0.0064 | -0.0072 | -0.0016 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XM/200_400/0_200 versus S/200_400/0_200 | +0.0073+ | +0.0084+ | +0.0010 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XM/200_400/200_400 versus S/200_400/200_400 | -0.0013 | -0.0008 | -0.0040 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XM/200_400/400_600 versus S/200_400/400_600 | +0.0034 | +0.0041 | -0.0007 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XM/400_600/0_200 versus S/400_600/0_200 | +0.1060+ | +0.1032+ | +0.1231 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XM/400_600/200_400 versus S/400_600/200_400 | +0.1944+ | +0.1862+ | +0.2441 |
| private/tg/CS_SINGLE/original_calibration | nll_bits | XM/400_600/400_600 versus S/400_600/400_600 | -0.0002 | -0.0000 | -0.0015 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | AP/0_200/0_200 versus S/0_200/0_200 | +0.0015 | +0.0002 | +0.0097 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | AP/0_200/200_400 versus S/0_200/200_400 | -0.0005 | -0.0035 | +0.0177 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | AP/0_200/400_600 versus S/0_200/400_600 | +0.0074 | +0.0065 | +0.0131 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | AP/200_400/0_200 versus S/200_400/0_200 | -0.0073 | -0.0074 | -0.0065 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | AP/200_400/200_400 versus S/200_400/200_400 | -0.0032 | -0.0014 | -0.0137 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | AP/200_400/400_600 versus S/200_400/400_600 | +0.0057 | +0.0089 | -0.0139 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | AP/400_600/0_200 versus S/400_600/0_200 | +0.0061 | +0.0010 | +0.0372 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | AP/400_600/200_400 versus S/400_600/200_400 | +0.0299+ | +0.0279+ | +0.0421 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | AP/400_600/400_600 versus S/400_600/400_600 | -0.0013 | -0.0013 | -0.0011 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XP/0_200/0_200 versus S/0_200/0_200 | +0.0094 | +0.0077 | +0.0200 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XP/0_200/200_400 versus S/0_200/200_400 | -0.0015 | -0.0012 | -0.0036 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XP/0_200/400_600 versus S/0_200/400_600 | +0.0081 | +0.0063 | +0.0193 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XP/200_400/0_200 versus S/200_400/0_200 | -0.0023 | +0.0003 | -0.0181 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XP/200_400/200_400 versus S/200_400/200_400 | -0.0051 | -0.0032 | -0.0162 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XP/200_400/400_600 versus S/200_400/400_600 | +0.0008 | +0.0028 | -0.0116 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XP/400_600/0_200 versus S/400_600/0_200 | +0.0045 | -0.0016 | +0.0420 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XP/400_600/200_400 versus S/400_600/200_400 | +0.0129 | +0.0099 | +0.0310 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XP/400_600/400_600 versus S/400_600/400_600 | -0.0019 | -0.0011 | -0.0070 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | J*/0_200/0_200 versus S/0_200/0_200 | +0.0059 | +0.0050 | +0.0114 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | J*/0_200/200_400 versus S/0_200/200_400 | -0.0066 | -0.0068 | -0.0050 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | J*/0_200/400_600 versus S/0_200/400_600 | +0.0114 | +0.0133 | +0.0002 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | J*/200_400/0_200 versus S/200_400/0_200 | -0.0027 | -0.0008 | -0.0144 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | J*/200_400/200_400 versus S/200_400/200_400 | -0.0115− | -0.0092 | -0.0256 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | J*/200_400/400_600 versus S/200_400/400_600 | +0.0038 | +0.0053 | -0.0057 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | J*/400_600/0_200 versus S/400_600/0_200 | -0.0035 | -0.0066 | +0.0154 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | J*/400_600/200_400 versus S/400_600/200_400 | +0.0024 | -0.0003 | +0.0189 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | J*/400_600/400_600 versus S/400_600/400_600 | -0.0082 | -0.0069 | -0.0160 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XM/0_200/0_200 versus S/0_200/0_200 | +0.0072 | +0.0045 | +0.0241 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XM/0_200/200_400 versus S/0_200/200_400 | -0.0045 | -0.0082 | +0.0175 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XM/0_200/400_600 versus S/0_200/400_600 | +0.0149 | +0.0139 | +0.0210 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XM/200_400/0_200 versus S/200_400/0_200 | +0.0078 | +0.0082 | +0.0048 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XM/200_400/200_400 versus S/200_400/200_400 | -0.0021 | +0.0007 | -0.0189 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XM/200_400/400_600 versus S/200_400/400_600 | +0.0028 | +0.0051 | -0.0116 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XM/400_600/0_200 versus S/400_600/0_200 | +0.0074 | +0.0043 | +0.0262 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XM/400_600/200_400 versus S/400_600/200_400 | +0.0201+ | +0.0187+ | +0.0285 |
| private/tg/CS_SINGLE/source_only_destination_calibration | auc | XM/400_600/400_600 versus S/400_600/400_600 | -0.0026 | -0.0023 | -0.0042 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | AP/0_200/0_200 versus S/0_200/0_200 | -0.0005 | -0.0004 | -0.0011 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | AP/0_200/200_400 versus S/0_200/200_400 | +0.0000 | -0.0000 | +0.0004 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | AP/0_200/400_600 versus S/0_200/400_600 | -0.0000 | +0.0000 | -0.0001 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | AP/200_400/0_200 versus S/200_400/0_200 | +0.0002 | +0.0002 | -0.0001 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | AP/200_400/200_400 versus S/200_400/200_400 | -0.0017 | -0.0012 | -0.0047 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | AP/200_400/400_600 versus S/200_400/400_600 | +0.0001 | +0.0001 | -0.0000 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | AP/400_600/0_200 versus S/400_600/0_200 | -0.0000 | -0.0000 | -0.0001 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | AP/400_600/200_400 versus S/400_600/200_400 | +0.0002 | +0.0002 | +0.0002 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | AP/400_600/400_600 versus S/400_600/400_600 | -0.0001 | -0.0001 | +0.0000 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XP/0_200/0_200 versus S/0_200/0_200 | +0.0008 | +0.0007 | +0.0018 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XP/0_200/200_400 versus S/0_200/200_400 | +0.0000 | +0.0000 | +0.0002 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XP/0_200/400_600 versus S/0_200/400_600 | -0.0003 | -0.0003 | -0.0000 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XP/200_400/0_200 versus S/200_400/0_200 | +0.0002 | +0.0003 | -0.0003 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XP/200_400/200_400 versus S/200_400/200_400 | -0.0014 | -0.0011 | -0.0036 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XP/200_400/400_600 versus S/200_400/400_600 | +0.0000 | +0.0000 | +0.0001 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XP/400_600/0_200 versus S/400_600/0_200 | -0.0000 | -0.0001 | +0.0006 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XP/400_600/200_400 versus S/400_600/200_400 | -0.0001 | -0.0001 | -0.0003 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XP/400_600/400_600 versus S/400_600/400_600 | +0.0002 | +0.0004 | -0.0011 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | J*/0_200/0_200 versus S/0_200/0_200 | +0.0003 | +0.0001 | +0.0012 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | J*/0_200/200_400 versus S/0_200/200_400 | -0.0000 | -0.0000 | +0.0000 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | J*/0_200/400_600 versus S/0_200/400_600 | +0.0000 | +0.0000 | -0.0001 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | J*/200_400/0_200 versus S/200_400/0_200 | +0.0001 | +0.0002 | -0.0003 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | J*/200_400/200_400 versus S/200_400/200_400 | -0.0012 | -0.0007 | -0.0045 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | J*/200_400/400_600 versus S/200_400/400_600 | -0.0000 | -0.0000 | +0.0001 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | J*/400_600/0_200 versus S/400_600/0_200 | -0.0000 | -0.0000 | -0.0001 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | J*/400_600/200_400 versus S/400_600/200_400 | +0.0000 | +0.0001 | -0.0000 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | J*/400_600/400_600 versus S/400_600/400_600 | -0.0012 | -0.0011 | -0.0018 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XM/0_200/0_200 versus S/0_200/0_200 | +0.0007 | +0.0005 | +0.0016 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XM/0_200/200_400 versus S/0_200/200_400 | -0.0004 | -0.0006 | +0.0004 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XM/0_200/400_600 versus S/0_200/400_600 | +0.0001 | +0.0001 | +0.0000 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XM/200_400/0_200 versus S/200_400/0_200 | +0.0003 | +0.0004 | -0.0002 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XM/200_400/200_400 versus S/200_400/200_400 | -0.0013 | -0.0008 | -0.0040 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XM/200_400/400_600 versus S/200_400/400_600 | -0.0000 | +0.0000 | -0.0002 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XM/400_600/0_200 versus S/400_600/0_200 | -0.0000 | +0.0000 | -0.0001 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XM/400_600/200_400 versus S/400_600/200_400 | -0.0000 | -0.0000 | -0.0002 |
| private/tg/CS_SINGLE/source_only_destination_calibration | nll_bits | XM/400_600/400_600 versus S/400_600/400_600 | -0.0002 | -0.0000 | -0.0015 |
| private/tg/NCE/original_calibration | auc | AP/0_200/0_200 versus S/0_200/0_200 | +0.0116 | +0.0088 | +0.0292 |
| private/tg/NCE/original_calibration | auc | AP/0_200/200_400 versus S/0_200/200_400 | -0.0034 | +0.0013 | -0.0318 |
| private/tg/NCE/original_calibration | auc | AP/0_200/400_600 versus S/0_200/400_600 | +0.0125 | +0.0134 | +0.0067 |
| private/tg/NCE/original_calibration | auc | AP/200_400/0_200 versus S/200_400/0_200 | -0.0003 | +0.0018 | -0.0131 |
| private/tg/NCE/original_calibration | auc | AP/200_400/200_400 versus S/200_400/200_400 | +0.0113 | +0.0111 | +0.0128 |
| private/tg/NCE/original_calibration | auc | AP/200_400/400_600 versus S/200_400/400_600 | +0.0123 | +0.0100 | +0.0262 |
| private/tg/NCE/original_calibration | auc | AP/400_600/0_200 versus S/400_600/0_200 | +0.0224+ | +0.0153 | +0.0657 |
| private/tg/NCE/original_calibration | auc | AP/400_600/200_400 versus S/400_600/200_400 | +0.0074 | +0.0069 | +0.0104 |
| private/tg/NCE/original_calibration | auc | AP/400_600/400_600 versus S/400_600/400_600 | +0.0048 | +0.0033 | +0.0143 |
| private/tg/NCE/original_calibration | auc | XP/0_200/0_200 versus S/0_200/0_200 | +0.0006 | +0.0007 | -0.0006 |
| private/tg/NCE/original_calibration | auc | XP/0_200/200_400 versus S/0_200/200_400 | +0.0093 | +0.0094 | +0.0088 |
| private/tg/NCE/original_calibration | auc | XP/0_200/400_600 versus S/0_200/400_600 | +0.0195 | +0.0200 | +0.0168 |
| private/tg/NCE/original_calibration | auc | XP/200_400/0_200 versus S/200_400/0_200 | -0.0175 | -0.0141 | -0.0384 |
| private/tg/NCE/original_calibration | auc | XP/200_400/200_400 versus S/200_400/200_400 | +0.0049 | +0.0039 | +0.0108 |
| private/tg/NCE/original_calibration | auc | XP/200_400/400_600 versus S/200_400/400_600 | -0.0073 | -0.0116 | +0.0185 |
| private/tg/NCE/original_calibration | auc | XP/400_600/0_200 versus S/400_600/0_200 | +0.0093 | +0.0040 | +0.0418 |
| private/tg/NCE/original_calibration | auc | XP/400_600/200_400 versus S/400_600/200_400 | +0.0047 | +0.0061 | -0.0039 |
| private/tg/NCE/original_calibration | auc | XP/400_600/400_600 versus S/400_600/400_600 | +0.0025 | +0.0021 | +0.0052 |
| private/tg/NCE/original_calibration | auc | J*/0_200/0_200 versus S/0_200/0_200 | +0.0072 | +0.0074 | +0.0064 |
| private/tg/NCE/original_calibration | auc | J*/0_200/200_400 versus S/0_200/200_400 | +0.0026 | +0.0064 | -0.0204 |
| private/tg/NCE/original_calibration | auc | J*/0_200/400_600 versus S/0_200/400_600 | +0.0179 | +0.0172 | +0.0221 |
| private/tg/NCE/original_calibration | auc | J*/200_400/0_200 versus S/200_400/0_200 | -0.0179 | -0.0182 | -0.0163 |
| private/tg/NCE/original_calibration | auc | J*/200_400/200_400 versus S/200_400/200_400 | +0.0130+ | +0.0143+ | +0.0051 |
| private/tg/NCE/original_calibration | auc | J*/200_400/400_600 versus S/200_400/400_600 | -0.0042 | -0.0060 | +0.0067 |
| private/tg/NCE/original_calibration | auc | J*/400_600/0_200 versus S/400_600/0_200 | +0.0059 | +0.0040 | +0.0172 |
| private/tg/NCE/original_calibration | auc | J*/400_600/200_400 versus S/400_600/200_400 | +0.0075 | +0.0100 | -0.0079 |
| private/tg/NCE/original_calibration | auc | J*/400_600/400_600 versus S/400_600/400_600 | +0.0000 | -0.0013 | +0.0081 |
| private/tg/NCE/original_calibration | auc | XM/0_200/0_200 versus S/0_200/0_200 | +0.0079 | +0.0070 | +0.0137 |
| private/tg/NCE/original_calibration | auc | XM/0_200/200_400 versus S/0_200/200_400 | +0.0092 | +0.0114 | -0.0043 |
| private/tg/NCE/original_calibration | auc | XM/0_200/400_600 versus S/0_200/400_600 | +0.0121 | +0.0133 | +0.0045 |
| private/tg/NCE/original_calibration | auc | XM/200_400/0_200 versus S/200_400/0_200 | -0.0317− | -0.0287 | -0.0501 |
| private/tg/NCE/original_calibration | auc | XM/200_400/200_400 versus S/200_400/200_400 | +0.0054 | +0.0052 | +0.0066 |
| private/tg/NCE/original_calibration | auc | XM/200_400/400_600 versus S/200_400/400_600 | +0.0051 | +0.0024 | +0.0217 |
| private/tg/NCE/original_calibration | auc | XM/400_600/0_200 versus S/400_600/0_200 | -0.0060 | -0.0083 | +0.0082 |
| private/tg/NCE/original_calibration | auc | XM/400_600/200_400 versus S/400_600/200_400 | -0.0072 | -0.0026 | -0.0347 |
| private/tg/NCE/original_calibration | auc | XM/400_600/400_600 versus S/400_600/400_600 | +0.0065 | +0.0060 | +0.0094 |
| private/tg/NCE/original_calibration | nll_bits | AP/0_200/0_200 versus S/0_200/0_200 | +0.0022+ | +0.0018 | +0.0048 |
| private/tg/NCE/original_calibration | nll_bits | AP/0_200/200_400 versus S/0_200/200_400 | +0.0163+ | +0.0173+ | +0.0098 |
| private/tg/NCE/original_calibration | nll_bits | AP/0_200/400_600 versus S/0_200/400_600 | +0.0219+ | +0.0214+ | +0.0249 |
| private/tg/NCE/original_calibration | nll_bits | AP/200_400/0_200 versus S/200_400/0_200 | +0.0099+ | +0.0100 | +0.0092 |
| private/tg/NCE/original_calibration | nll_bits | AP/200_400/200_400 versus S/200_400/200_400 | +0.0023+ | +0.0024+ | +0.0013 |
| private/tg/NCE/original_calibration | nll_bits | AP/200_400/400_600 versus S/200_400/400_600 | +0.0164+ | +0.0164+ | +0.0163 |
| private/tg/NCE/original_calibration | nll_bits | AP/400_600/0_200 versus S/400_600/0_200 | -0.0586− | -0.0647− | -0.0209 |
| private/tg/NCE/original_calibration | nll_bits | AP/400_600/200_400 versus S/400_600/200_400 | -0.0698− | -0.0690− | -0.0747 |
| private/tg/NCE/original_calibration | nll_bits | AP/400_600/400_600 versus S/400_600/400_600 | +0.0019+ | +0.0017 | +0.0029 |
| private/tg/NCE/original_calibration | nll_bits | XP/0_200/0_200 versus S/0_200/0_200 | +0.0002 | +0.0002 | +0.0005 |
| private/tg/NCE/original_calibration | nll_bits | XP/0_200/200_400 versus S/0_200/200_400 | -0.0856− | -0.0863− | -0.0815 |
| private/tg/NCE/original_calibration | nll_bits | XP/0_200/400_600 versus S/0_200/400_600 | -0.0327− | -0.0324− | -0.0346 |
| private/tg/NCE/original_calibration | nll_bits | XP/200_400/0_200 versus S/200_400/0_200 | -0.0413− | -0.0394− | -0.0534 |
| private/tg/NCE/original_calibration | nll_bits | XP/200_400/200_400 versus S/200_400/200_400 | +0.0003 | +0.0001 | +0.0015 |
| private/tg/NCE/original_calibration | nll_bits | XP/200_400/400_600 versus S/200_400/400_600 | -0.0569− | -0.0566− | -0.0586 |
| private/tg/NCE/original_calibration | nll_bits | XP/400_600/0_200 versus S/400_600/0_200 | -0.0135 | -0.0179 | +0.0134 |
| private/tg/NCE/original_calibration | nll_bits | XP/400_600/200_400 versus S/400_600/200_400 | -0.0468− | -0.0475− | -0.0420 |
| private/tg/NCE/original_calibration | nll_bits | XP/400_600/400_600 versus S/400_600/400_600 | +0.0009 | +0.0008 | +0.0015 |
| private/tg/NCE/original_calibration | nll_bits | J*/0_200/0_200 versus S/0_200/0_200 | +0.0014 | +0.0014 | +0.0015 |
| private/tg/NCE/original_calibration | nll_bits | J*/0_200/200_400 versus S/0_200/200_400 | +0.0095 | +0.0103 | +0.0045 |
| private/tg/NCE/original_calibration | nll_bits | J*/0_200/400_600 versus S/0_200/400_600 | +0.0097 | +0.0092 | +0.0124 |
| private/tg/NCE/original_calibration | nll_bits | J*/200_400/0_200 versus S/200_400/0_200 | -0.0301− | -0.0303− | -0.0290 |
| private/tg/NCE/original_calibration | nll_bits | J*/200_400/200_400 versus S/200_400/200_400 | +0.0017 | +0.0019 | +0.0005 |
| private/tg/NCE/original_calibration | nll_bits | J*/200_400/400_600 versus S/200_400/400_600 | -0.0150− | -0.0137− | -0.0225 |
| private/tg/NCE/original_calibration | nll_bits | J*/400_600/0_200 versus S/400_600/0_200 | -0.3756− | -0.3680− | -0.4224 |
| private/tg/NCE/original_calibration | nll_bits | J*/400_600/200_400 versus S/400_600/200_400 | -0.0780− | -0.0754− | -0.0936 |
| private/tg/NCE/original_calibration | nll_bits | J*/400_600/400_600 versus S/400_600/400_600 | +0.0008 | +0.0006 | +0.0017 |
| private/tg/NCE/original_calibration | nll_bits | XM/0_200/0_200 versus S/0_200/0_200 | +0.0013 | +0.0011 | +0.0022 |
| private/tg/NCE/original_calibration | nll_bits | XM/0_200/200_400 versus S/0_200/200_400 | -0.1590− | -0.1604− | -0.1508 |
| private/tg/NCE/original_calibration | nll_bits | XM/0_200/400_600 versus S/0_200/400_600 | -0.0915− | -0.0914− | -0.0923 |
| private/tg/NCE/original_calibration | nll_bits | XM/200_400/0_200 versus S/200_400/0_200 | -0.0375− | -0.0354− | -0.0503 |
| private/tg/NCE/original_calibration | nll_bits | XM/200_400/200_400 versus S/200_400/200_400 | +0.0009 | +0.0010 | +0.0002 |
| private/tg/NCE/original_calibration | nll_bits | XM/200_400/400_600 versus S/200_400/400_600 | -0.0144− | -0.0151− | -0.0100 |
| private/tg/NCE/original_calibration | nll_bits | XM/400_600/0_200 versus S/400_600/0_200 | -0.0101 | -0.0125 | +0.0050 |
| private/tg/NCE/original_calibration | nll_bits | XM/400_600/200_400 versus S/400_600/200_400 | -0.0631− | -0.0624− | -0.0675 |
| private/tg/NCE/original_calibration | nll_bits | XM/400_600/400_600 versus S/400_600/400_600 | +0.0013 | +0.0012 | +0.0019 |
| private/tg/NCE/source_only_destination_calibration | auc | AP/0_200/0_200 versus S/0_200/0_200 | +0.0116 | +0.0088 | +0.0292 |
| private/tg/NCE/source_only_destination_calibration | auc | AP/0_200/200_400 versus S/0_200/200_400 | -0.0034 | +0.0013 | -0.0318 |
| private/tg/NCE/source_only_destination_calibration | auc | AP/0_200/400_600 versus S/0_200/400_600 | +0.0125 | +0.0134 | +0.0067 |
| private/tg/NCE/source_only_destination_calibration | auc | AP/200_400/0_200 versus S/200_400/0_200 | -0.0003 | +0.0018 | -0.0131 |
| private/tg/NCE/source_only_destination_calibration | auc | AP/200_400/200_400 versus S/200_400/200_400 | +0.0113 | +0.0111 | +0.0128 |
| private/tg/NCE/source_only_destination_calibration | auc | AP/200_400/400_600 versus S/200_400/400_600 | +0.0123 | +0.0100 | +0.0262 |
| private/tg/NCE/source_only_destination_calibration | auc | AP/400_600/0_200 versus S/400_600/0_200 | +0.0224+ | +0.0153 | +0.0657 |
| private/tg/NCE/source_only_destination_calibration | auc | AP/400_600/200_400 versus S/400_600/200_400 | +0.0074 | +0.0069 | +0.0104 |
| private/tg/NCE/source_only_destination_calibration | auc | AP/400_600/400_600 versus S/400_600/400_600 | +0.0048 | +0.0033 | +0.0143 |
| private/tg/NCE/source_only_destination_calibration | auc | XP/0_200/0_200 versus S/0_200/0_200 | +0.0006 | +0.0007 | -0.0006 |
| private/tg/NCE/source_only_destination_calibration | auc | XP/0_200/200_400 versus S/0_200/200_400 | +0.0093 | +0.0094 | +0.0088 |
| private/tg/NCE/source_only_destination_calibration | auc | XP/0_200/400_600 versus S/0_200/400_600 | +0.0195 | +0.0200 | +0.0168 |
| private/tg/NCE/source_only_destination_calibration | auc | XP/200_400/0_200 versus S/200_400/0_200 | -0.0175 | -0.0141 | -0.0384 |
| private/tg/NCE/source_only_destination_calibration | auc | XP/200_400/200_400 versus S/200_400/200_400 | +0.0049 | +0.0039 | +0.0108 |
| private/tg/NCE/source_only_destination_calibration | auc | XP/200_400/400_600 versus S/200_400/400_600 | -0.0073 | -0.0116 | +0.0185 |
| private/tg/NCE/source_only_destination_calibration | auc | XP/400_600/0_200 versus S/400_600/0_200 | +0.0093 | +0.0040 | +0.0418 |
| private/tg/NCE/source_only_destination_calibration | auc | XP/400_600/200_400 versus S/400_600/200_400 | +0.0047 | +0.0061 | -0.0039 |
| private/tg/NCE/source_only_destination_calibration | auc | XP/400_600/400_600 versus S/400_600/400_600 | +0.0025 | +0.0021 | +0.0052 |
| private/tg/NCE/source_only_destination_calibration | auc | J*/0_200/0_200 versus S/0_200/0_200 | +0.0072 | +0.0074 | +0.0064 |
| private/tg/NCE/source_only_destination_calibration | auc | J*/0_200/200_400 versus S/0_200/200_400 | +0.0026 | +0.0064 | -0.0204 |
| private/tg/NCE/source_only_destination_calibration | auc | J*/0_200/400_600 versus S/0_200/400_600 | +0.0179 | +0.0172 | +0.0221 |
| private/tg/NCE/source_only_destination_calibration | auc | J*/200_400/0_200 versus S/200_400/0_200 | -0.0179 | -0.0182 | -0.0163 |
| private/tg/NCE/source_only_destination_calibration | auc | J*/200_400/200_400 versus S/200_400/200_400 | +0.0130+ | +0.0143+ | +0.0051 |
| private/tg/NCE/source_only_destination_calibration | auc | J*/200_400/400_600 versus S/200_400/400_600 | -0.0042 | -0.0060 | +0.0067 |
| private/tg/NCE/source_only_destination_calibration | auc | J*/400_600/0_200 versus S/400_600/0_200 | +0.0059 | +0.0040 | +0.0172 |
| private/tg/NCE/source_only_destination_calibration | auc | J*/400_600/200_400 versus S/400_600/200_400 | +0.0075 | +0.0100 | -0.0079 |
| private/tg/NCE/source_only_destination_calibration | auc | J*/400_600/400_600 versus S/400_600/400_600 | +0.0000 | -0.0013 | +0.0081 |
| private/tg/NCE/source_only_destination_calibration | auc | XM/0_200/0_200 versus S/0_200/0_200 | +0.0079 | +0.0070 | +0.0137 |
| private/tg/NCE/source_only_destination_calibration | auc | XM/0_200/200_400 versus S/0_200/200_400 | +0.0092 | +0.0114 | -0.0043 |
| private/tg/NCE/source_only_destination_calibration | auc | XM/0_200/400_600 versus S/0_200/400_600 | +0.0121 | +0.0133 | +0.0045 |
| private/tg/NCE/source_only_destination_calibration | auc | XM/200_400/0_200 versus S/200_400/0_200 | -0.0317− | -0.0287 | -0.0501 |
| private/tg/NCE/source_only_destination_calibration | auc | XM/200_400/200_400 versus S/200_400/200_400 | +0.0054 | +0.0052 | +0.0066 |
| private/tg/NCE/source_only_destination_calibration | auc | XM/200_400/400_600 versus S/200_400/400_600 | +0.0051 | +0.0024 | +0.0217 |
| private/tg/NCE/source_only_destination_calibration | auc | XM/400_600/0_200 versus S/400_600/0_200 | -0.0060 | -0.0083 | +0.0082 |
| private/tg/NCE/source_only_destination_calibration | auc | XM/400_600/200_400 versus S/400_600/200_400 | -0.0072 | -0.0026 | -0.0347 |
| private/tg/NCE/source_only_destination_calibration | auc | XM/400_600/400_600 versus S/400_600/400_600 | +0.0065 | +0.0060 | +0.0094 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | AP/0_200/0_200 versus S/0_200/0_200 | +0.0022+ | +0.0018 | +0.0048 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | AP/0_200/200_400 versus S/0_200/200_400 | +0.0002 | +0.0003 | +0.0000 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | AP/0_200/400_600 versus S/0_200/400_600 | +0.0000 | +0.0000 | -0.0000 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | AP/200_400/0_200 versus S/200_400/0_200 | +0.0003 | +0.0003 | +0.0001 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | AP/200_400/200_400 versus S/200_400/200_400 | +0.0023+ | +0.0024+ | +0.0013 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | AP/200_400/400_600 versus S/200_400/400_600 | +0.0002 | +0.0002 | +0.0006 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | AP/400_600/0_200 versus S/400_600/0_200 | +0.0011 | +0.0006 | +0.0041 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | AP/400_600/200_400 versus S/400_600/200_400 | +0.0002 | +0.0002 | +0.0002 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | AP/400_600/400_600 versus S/400_600/400_600 | +0.0019+ | +0.0017 | +0.0029 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XP/0_200/0_200 versus S/0_200/0_200 | +0.0002 | +0.0002 | +0.0005 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XP/0_200/200_400 versus S/0_200/200_400 | +0.0001 | +0.0001 | +0.0002 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XP/0_200/400_600 versus S/0_200/400_600 | +0.0000 | +0.0000 | -0.0001 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XP/200_400/0_200 versus S/200_400/0_200 | -0.0002 | -0.0001 | -0.0008 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XP/200_400/200_400 versus S/200_400/200_400 | +0.0003 | +0.0001 | +0.0015 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XP/200_400/400_600 versus S/200_400/400_600 | +0.0001 | +0.0000 | +0.0002 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XP/400_600/0_200 versus S/400_600/0_200 | +0.0002 | +0.0000 | +0.0013 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XP/400_600/200_400 versus S/400_600/200_400 | -0.0001 | +0.0000 | -0.0009 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XP/400_600/400_600 versus S/400_600/400_600 | +0.0009 | +0.0008 | +0.0015 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | J*/0_200/0_200 versus S/0_200/0_200 | +0.0014 | +0.0014 | +0.0015 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | J*/0_200/200_400 versus S/0_200/200_400 | -0.0001 | -0.0000 | -0.0005 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | J*/0_200/400_600 versus S/0_200/400_600 | -0.0000 | -0.0000 | -0.0001 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | J*/200_400/0_200 versus S/200_400/0_200 | -0.0001 | -0.0001 | +0.0002 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | J*/200_400/200_400 versus S/200_400/200_400 | +0.0017 | +0.0019 | +0.0005 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | J*/200_400/400_600 versus S/200_400/400_600 | -0.0001 | -0.0001 | +0.0001 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | J*/400_600/0_200 versus S/400_600/0_200 | +0.0001 | +0.0000 | +0.0008 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | J*/400_600/200_400 versus S/400_600/200_400 | +0.0002 | +0.0003 | -0.0005 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | J*/400_600/400_600 versus S/400_600/400_600 | +0.0008 | +0.0006 | +0.0017 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XM/0_200/0_200 versus S/0_200/0_200 | +0.0013 | +0.0011 | +0.0022 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XM/0_200/200_400 versus S/0_200/200_400 | +0.0004 | +0.0004 | +0.0003 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XM/0_200/400_600 versus S/0_200/400_600 | +0.0000 | +0.0001 | -0.0001 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XM/200_400/0_200 versus S/200_400/0_200 | -0.0001 | -0.0001 | -0.0002 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XM/200_400/200_400 versus S/200_400/200_400 | +0.0009 | +0.0010 | +0.0002 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XM/200_400/400_600 versus S/200_400/400_600 | +0.0001 | +0.0001 | +0.0001 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XM/400_600/0_200 versus S/400_600/0_200 | +0.0001 | -0.0001 | +0.0008 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XM/400_600/200_400 versus S/400_600/200_400 | +0.0000 | +0.0002 | -0.0010 |
| private/tg/NCE/source_only_destination_calibration | nll_bits | XM/400_600/400_600 versus S/400_600/400_600 | +0.0013 | +0.0012 | +0.0019 |
| private/windows/CS_SINGLE/ | auc | AP/0_200 versus S/0_200 | +0.0015 | +0.0002 | +0.0097 |
| private/windows/CS_SINGLE/ | auc | AP/200_400 versus S/200_400 | -0.0032 | -0.0014 | -0.0137 |
| private/windows/CS_SINGLE/ | auc | AP/400_600 versus S/400_600 | -0.0013 | -0.0013 | -0.0011 |
| private/windows/CS_SINGLE/ | auc | AP/full versus S/full | +0.0010 | +0.0002 | +0.0060 |
| private/windows/CS_SINGLE/ | auc | XP/0_200 versus S/0_200 | +0.0094 | +0.0077 | +0.0200 |
| private/windows/CS_SINGLE/ | auc | XP/200_400 versus S/200_400 | -0.0051 | -0.0032 | -0.0162 |
| private/windows/CS_SINGLE/ | auc | XP/400_600 versus S/400_600 | -0.0019 | -0.0011 | -0.0070 |
| private/windows/CS_SINGLE/ | auc | XP/full versus S/full | +0.0026 | +0.0028 | +0.0017 |
| private/windows/CS_SINGLE/ | auc | J*/0_200 versus S/0_200 | +0.0059 | +0.0050 | +0.0114 |
| private/windows/CS_SINGLE/ | auc | J*/200_400 versus S/200_400 | -0.0115− | -0.0092 | -0.0256− |
| private/windows/CS_SINGLE/ | auc | J*/400_600 versus S/400_600 | -0.0082 | -0.0069 | -0.0160 |
| private/windows/CS_SINGLE/ | auc | J*/full versus S/full | -0.0029 | -0.0041 | +0.0046 |
| private/windows/CS_SINGLE/ | auc | XM/0_200 versus S/0_200 | +0.0072 | +0.0045 | +0.0241 |
| private/windows/CS_SINGLE/ | auc | XM/200_400 versus S/200_400 | -0.0021 | +0.0007 | -0.0189 |
| private/windows/CS_SINGLE/ | auc | XM/400_600 versus S/400_600 | -0.0026 | -0.0023 | -0.0042 |
| private/windows/CS_SINGLE/ | auc | XM/full versus S/full | +0.0007 | +0.0029 | -0.0123 |
| private/windows/CS_SINGLE/ | history_gain_bits | AP/0_200 versus S/0_200 | -0.0001 | +0.0002 | -0.0020 |
| private/windows/CS_SINGLE/ | history_gain_bits | AP/200_400 versus S/200_400 | -0.0007 | -0.0001 | -0.0043 |
| private/windows/CS_SINGLE/ | history_gain_bits | AP/400_600 versus S/400_600 | -0.0001 | -0.0003 | +0.0012 |
| private/windows/CS_SINGLE/ | history_gain_bits | AP/full versus S/full | +0.0011 | +0.0012 | -0.0001 |
| private/windows/CS_SINGLE/ | history_gain_bits | XP/0_200 versus S/0_200 | +0.0006 | +0.0006 | +0.0004 |
| private/windows/CS_SINGLE/ | history_gain_bits | XP/200_400 versus S/200_400 | -0.0005 | -0.0002 | -0.0019 |
| private/windows/CS_SINGLE/ | history_gain_bits | XP/400_600 versus S/400_600 | +0.0010 | +0.0010 | +0.0005 |
| private/windows/CS_SINGLE/ | history_gain_bits | XP/full versus S/full | +0.0008 | +0.0005 | +0.0023 |
| private/windows/CS_SINGLE/ | history_gain_bits | J*/0_200 versus S/0_200 | -0.0002 | -0.0001 | -0.0006 |
| private/windows/CS_SINGLE/ | history_gain_bits | J*/200_400 versus S/200_400 | -0.0004 | +0.0002 | -0.0037 |
| private/windows/CS_SINGLE/ | history_gain_bits | J*/400_600 versus S/400_600 | -0.0011 | -0.0011 | -0.0013 |
| private/windows/CS_SINGLE/ | history_gain_bits | J*/full versus S/full | -0.0001 | -0.0003 | +0.0010 |
| private/windows/CS_SINGLE/ | history_gain_bits | XM/0_200 versus S/0_200 | -0.0008 | -0.0007 | -0.0010 |
| private/windows/CS_SINGLE/ | history_gain_bits | XM/200_400 versus S/200_400 | -0.0008 | -0.0005 | -0.0029 |
| private/windows/CS_SINGLE/ | history_gain_bits | XM/400_600 versus S/400_600 | +0.0007 | +0.0007 | +0.0006 |
| private/windows/CS_SINGLE/ | history_gain_bits | XM/full versus S/full | -0.0010 | -0.0007 | -0.0027 |
| private/windows/CS_SINGLE/ | nll_bits | AP/0_200 versus S/0_200 | -0.0005 | -0.0004 | -0.0011 |
| private/windows/CS_SINGLE/ | nll_bits | AP/200_400 versus S/200_400 | -0.0017 | -0.0012 | -0.0047 |
| private/windows/CS_SINGLE/ | nll_bits | AP/400_600 versus S/400_600 | -0.0001 | -0.0001 | +0.0000 |
| private/windows/CS_SINGLE/ | nll_bits | AP/full versus S/full | +0.0004 | +0.0003 | +0.0012 |
| private/windows/CS_SINGLE/ | nll_bits | XP/0_200 versus S/0_200 | +0.0008 | +0.0007 | +0.0018 |
| private/windows/CS_SINGLE/ | nll_bits | XP/200_400 versus S/200_400 | -0.0014 | -0.0011 | -0.0036 |
| private/windows/CS_SINGLE/ | nll_bits | XP/400_600 versus S/400_600 | +0.0002 | +0.0004 | -0.0011 |
| private/windows/CS_SINGLE/ | nll_bits | XP/full versus S/full | +0.0005 | +0.0005 | +0.0008 |
| private/windows/CS_SINGLE/ | nll_bits | J*/0_200 versus S/0_200 | +0.0003 | +0.0001 | +0.0012 |
| private/windows/CS_SINGLE/ | nll_bits | J*/200_400 versus S/200_400 | -0.0012 | -0.0007 | -0.0045 |
| private/windows/CS_SINGLE/ | nll_bits | J*/400_600 versus S/400_600 | -0.0012 | -0.0011 | -0.0018 |
| private/windows/CS_SINGLE/ | nll_bits | J*/full versus S/full | -0.0006 | -0.0010 | +0.0013 |
| private/windows/CS_SINGLE/ | nll_bits | XM/0_200 versus S/0_200 | +0.0007 | +0.0005 | +0.0016 |
| private/windows/CS_SINGLE/ | nll_bits | XM/200_400 versus S/200_400 | -0.0013 | -0.0008 | -0.0040 |
| private/windows/CS_SINGLE/ | nll_bits | XM/400_600 versus S/400_600 | -0.0002 | -0.0000 | -0.0015 |
| private/windows/CS_SINGLE/ | nll_bits | XM/full versus S/full | -0.0004 | -0.0000 | -0.0028 |
| private/windows/NCE/ | auc | AP/0_200 versus S/0_200 | +0.0116 | +0.0088 | +0.0292 |
| private/windows/NCE/ | auc | AP/200_400 versus S/200_400 | +0.0113 | +0.0111 | +0.0128 |
| private/windows/NCE/ | auc | AP/400_600 versus S/400_600 | +0.0048 | +0.0033 | +0.0143 |
| private/windows/NCE/ | auc | AP/full versus S/full | +0.0209+ | +0.0178+ | +0.0399 |
| private/windows/NCE/ | auc | XP/0_200 versus S/0_200 | +0.0006 | +0.0007 | -0.0006 |
| private/windows/NCE/ | auc | XP/200_400 versus S/200_400 | +0.0049 | +0.0039 | +0.0108 |
| private/windows/NCE/ | auc | XP/400_600 versus S/400_600 | +0.0025 | +0.0021 | +0.0052 |
| private/windows/NCE/ | auc | XP/full versus S/full | +0.0085 | +0.0088 | +0.0071 |
| private/windows/NCE/ | auc | J*/0_200 versus S/0_200 | +0.0072 | +0.0074 | +0.0064 |
| private/windows/NCE/ | auc | J*/200_400 versus S/200_400 | +0.0130+ | +0.0143+ | +0.0051 |
| private/windows/NCE/ | auc | J*/400_600 versus S/400_600 | +0.0000 | -0.0013 | +0.0081 |
| private/windows/NCE/ | auc | J*/full versus S/full | +0.0166+ | +0.0158+ | +0.0212 |
| private/windows/NCE/ | auc | XM/0_200 versus S/0_200 | +0.0079 | +0.0070 | +0.0137 |
| private/windows/NCE/ | auc | XM/200_400 versus S/200_400 | +0.0054 | +0.0052 | +0.0066 |
| private/windows/NCE/ | auc | XM/400_600 versus S/400_600 | +0.0065 | +0.0060 | +0.0094 |
| private/windows/NCE/ | auc | XM/full versus S/full | +0.0117+ | +0.0101 | +0.0219 |
| private/windows/NCE/ | history_gain_bits | AP/0_200 versus S/0_200 | +0.0033+ | +0.0030+ | +0.0053+ |
| private/windows/NCE/ | history_gain_bits | AP/200_400 versus S/200_400 | +0.0024+ | +0.0024+ | +0.0023 |
| private/windows/NCE/ | history_gain_bits | AP/400_600 versus S/400_600 | +0.0021+ | +0.0020+ | +0.0023 |
| private/windows/NCE/ | history_gain_bits | AP/full versus S/full | +0.0038+ | +0.0036+ | +0.0051 |
| private/windows/NCE/ | history_gain_bits | XP/0_200 versus S/0_200 | +0.0009 | +0.0010 | +0.0002 |
| private/windows/NCE/ | history_gain_bits | XP/200_400 versus S/200_400 | -0.0001 | -0.0006 | +0.0026 |
| private/windows/NCE/ | history_gain_bits | XP/400_600 versus S/400_600 | +0.0003 | +0.0001 | +0.0015 |
| private/windows/NCE/ | history_gain_bits | XP/full versus S/full | +0.0009 | +0.0009 | +0.0011 |
| private/windows/NCE/ | history_gain_bits | J*/0_200 versus S/0_200 | +0.0021 | +0.0020 | +0.0025 |
| private/windows/NCE/ | history_gain_bits | J*/200_400 versus S/200_400 | +0.0020+ | +0.0021+ | +0.0018 |
| private/windows/NCE/ | history_gain_bits | J*/400_600 versus S/400_600 | +0.0012 | +0.0012 | +0.0012 |
| private/windows/NCE/ | history_gain_bits | J*/full versus S/full | +0.0024+ | +0.0025 | +0.0020 |
| private/windows/NCE/ | history_gain_bits | XM/0_200 versus S/0_200 | +0.0019+ | +0.0016 | +0.0034 |
| private/windows/NCE/ | history_gain_bits | XM/200_400 versus S/200_400 | +0.0012 | +0.0012 | +0.0011 |
| private/windows/NCE/ | history_gain_bits | XM/400_600 versus S/400_600 | +0.0018+ | +0.0017 | +0.0024 |
| private/windows/NCE/ | history_gain_bits | XM/full versus S/full | +0.0020 | +0.0019 | +0.0026 |
| private/windows/NCE/ | nll_bits | AP/0_200 versus S/0_200 | +0.0022+ | +0.0018 | +0.0048 |
| private/windows/NCE/ | nll_bits | AP/200_400 versus S/200_400 | +0.0023+ | +0.0024+ | +0.0013 |
| private/windows/NCE/ | nll_bits | AP/400_600 versus S/400_600 | +0.0019+ | +0.0017+ | +0.0029 |
| private/windows/NCE/ | nll_bits | AP/full versus S/full | +0.0040+ | +0.0036+ | +0.0067 |
| private/windows/NCE/ | nll_bits | XP/0_200 versus S/0_200 | +0.0002 | +0.0002 | +0.0005 |
| private/windows/NCE/ | nll_bits | XP/200_400 versus S/200_400 | +0.0003 | +0.0001 | +0.0015 |
| private/windows/NCE/ | nll_bits | XP/400_600 versus S/400_600 | +0.0009 | +0.0008 | +0.0015 |
| private/windows/NCE/ | nll_bits | XP/full versus S/full | +0.0013 | +0.0013 | +0.0010 |
| private/windows/NCE/ | nll_bits | J*/0_200 versus S/0_200 | +0.0014 | +0.0014 | +0.0015 |
| private/windows/NCE/ | nll_bits | J*/200_400 versus S/200_400 | +0.0017+ | +0.0019+ | +0.0005 |
| private/windows/NCE/ | nll_bits | J*/400_600 versus S/400_600 | +0.0008 | +0.0006 | +0.0017 |
| private/windows/NCE/ | nll_bits | J*/full versus S/full | +0.0024 | +0.0022 | +0.0035 |
| private/windows/NCE/ | nll_bits | XM/0_200 versus S/0_200 | +0.0013 | +0.0011 | +0.0022 |
| private/windows/NCE/ | nll_bits | XM/200_400 versus S/200_400 | +0.0009 | +0.0010 | +0.0002 |
| private/windows/NCE/ | nll_bits | XM/400_600 versus S/400_600 | +0.0013 | +0.0012 | +0.0019 |
| private/windows/NCE/ | nll_bits | XM/full versus S/full | +0.0015 | +0.0011 | +0.0037 |

## Development (prior_science): simultaneous intervals over all endpoints × coefficients per model

Models: (a) all children, age in years + HA indicator; (b) HA only, age + device-use duration in years. Associations conditional on fitted models; not maturation or treatment effects. Only coefficient cells whose simultaneous interval excludes 0 are listed; every cell is in the CSV.

| Configuration / seed scope | Model | Endpoint | Coefficient | Estimate [simultaneous 95%] |
|---|---|---|---|---|

0 of 320 coefficient cells exclude 0 under their simultaneous family.

### Prespecified stage means (descriptive; seed-mean configurations)

| Configuration | Stage | n | full AUC | history gain | history − twin | adapt 0.3/20 ΔNLL |
|---|---|---|---|---|---|---|
| AP/CS_SINGLE/3401 | <=2mo | 14 | 0.518 | -0.0040 | 0.0010 | -0.0007 |
| AP/CS_SINGLE/3401 | >2to<13mo | 5 | 0.550 | 0.0011 | 0.0069 | 0.0009 |
| AP/CS_SINGLE/3401 | >=13mo | 36 | 0.534 | 0.0010 | 0.0043 | 0.0011 |
| AP/NCE/3401 | <=2mo | 14 | 0.533 | -0.0010 | 0.0014 | 0.0005 |
| AP/NCE/3401 | >2to<13mo | 5 | 0.578 | 0.0040 | 0.0074 | 0.0008 |
| AP/NCE/3401 | >=13mo | 36 | 0.542 | 0.0027 | 0.0030 | 0.0010 |
| J*/CS_SINGLE/3401 | <=2mo | 14 | 0.510 | -0.0059 | -0.0015 | -0.0008 |
| J*/CS_SINGLE/3401 | >2to<13mo | 5 | 0.533 | -0.0048 | 0.0019 | 0.0018 |
| J*/CS_SINGLE/3401 | >=13mo | 36 | 0.533 | 0.0002 | 0.0022 | 0.0009 |
| J*/NCE/3401 | <=2mo | 14 | 0.532 | -0.0031 | 0.0005 | 0.0028 |
| J*/NCE/3401 | >2to<13mo | 5 | 0.565 | 0.0030 | 0.0069 | 0.0014 |
| J*/NCE/3401 | >=13mo | 36 | 0.542 | 0.0019 | 0.0029 | 0.0006 |
| S/CS_SINGLE/3401 | <=2mo | 14 | 0.524 | -0.0032 | 0.0023 | -0.0002 |
| S/CS_SINGLE/3401 | >2to<13mo | 5 | 0.554 | -0.0020 | 0.0034 | 0.0017 |
| S/CS_SINGLE/3401 | >=13mo | 36 | 0.531 | -0.0008 | 0.0029 | 0.0011 |
| S/NCE/3401 | <=2mo | 14 | 0.518 | -0.0042 | -0.0001 | -0.0002 |
| S/NCE/3401 | >2to<13mo | 5 | 0.553 | 0.0003 | 0.0055 | 0.0002 |
| S/NCE/3401 | >=13mo | 36 | 0.525 | -0.0010 | 0.0014 | 0.0002 |
| XM/CS_SINGLE/3401 | <=2mo | 14 | 0.522 | -0.0052 | -0.0005 | -0.0006 |
| XM/CS_SINGLE/3401 | >2to<13mo | 5 | 0.542 | -0.0027 | 0.0015 | 0.0016 |
| XM/CS_SINGLE/3401 | >=13mo | 36 | 0.538 | -0.0010 | 0.0014 | 0.0002 |
| XM/NCE/3401 | <=2mo | 14 | 0.524 | -0.0026 | -0.0008 | 0.0011 |
| XM/NCE/3401 | >2to<13mo | 5 | 0.557 | -0.0000 | 0.0039 | 0.0014 |
| XM/NCE/3401 | >=13mo | 36 | 0.537 | 0.0013 | 0.0025 | 0.0001 |
| XP/CS_SINGLE/3401 | <=2mo | 14 | 0.531 | -0.0031 | 0.0022 | 0.0002 |
| XP/CS_SINGLE/3401 | >2to<13mo | 5 | 0.549 | -0.0002 | 0.0036 | 0.0003 |
| XP/CS_SINGLE/3401 | >=13mo | 36 | 0.533 | -0.0003 | 0.0026 | 0.0009 |
| XP/NCE/3401 | <=2mo | 14 | 0.520 | -0.0031 | 0.0010 | 0.0003 |
| XP/NCE/3401 | >2to<13mo | 5 | 0.557 | 0.0008 | 0.0057 | 0.0006 |
| XP/NCE/3401 | >=13mo | 36 | 0.537 | -0.0002 | 0.0014 | 0.0004 |

