# S35_CBAUD_PEOPLE results — auditory-continued vs direct CBraMod start by source-people fraction

Analysis job 1047358; plan `ff1bf5992a62297e…`. DTU, seed 3401. Positive advantage = auditory-continued start has lower true-query NLL (bits/query). Change columns = advantage at the reduced fraction minus advantage at 1.0 (positive = the auditory start helps more when people are fewer). Intervals: identity bootstrap-t, B = 4000, simultaneous within each family.

## native readout (n = 44 people)

| Column | Estimate | Simultaneous 95% |
|---|---:|---|
| advantage_0.25 | +0.0927 | [-0.0135, +0.1988] |
| advantage_0.5 | +0.1561 | [+0.0566, +0.2556] |
| advantage_1.0 | +0.0174 | [-0.0188, +0.0537] |
| change_0.25_vs_1.0 | +0.0752 | [-0.0196, +0.1700] |
| change_0.5_vs_1.0 | +0.1386 | [+0.0498, +0.2275] |

| Fraction | direct risk | auditory risk |
|---|---:|---:|
| 0.25 | 6.8842 | 6.7916 |
| 0.5 | 6.5116 | 6.3555 |
| 1.0 | 5.9878 | 5.9704 |

- hi (n=22): advantage_0.25 +0.1509 [-0.0175, +0.3194]; advantage_0.5 +0.2165 [+0.0453, +0.3876]; advantage_1.0 +0.0570 [+0.0085, +0.1055]; change_0.25_vs_1.0 +0.0939 [-0.0450, +0.2329]; change_0.5_vs_1.0 +0.1595 [+0.0094, +0.3096]
- nh (n=22): advantage_0.25 +0.0344 [-0.1141, +0.1829]; advantage_0.5 +0.0957 [-0.0208, +0.2123]; advantage_1.0 -0.0221 [-0.0750, +0.0308]; change_0.25_vs_1.0 +0.0565 [-0.0968, +0.2098]; change_0.5_vs_1.0 +0.1178 [+0.0002, +0.2354]

## unified readout (n = 44 people)

| Column | Estimate | Simultaneous 95% |
|---|---:|---|
| advantage_0.25 | +0.0587 | [-0.0059, +0.1233] |
| advantage_0.5 | +0.0302 | [-0.0344, +0.0948] |
| advantage_1.0 | +0.0064 | [-0.0267, +0.0395] |
| change_0.25_vs_1.0 | +0.0523 | [-0.0073, +0.1119] |
| change_0.5_vs_1.0 | +0.0238 | [-0.0320, +0.0796] |

| Fraction | direct risk | auditory risk |
|---|---:|---:|
| 0.25 | 7.2217 | 7.1629 |
| 0.5 | 6.9195 | 6.8893 |
| 1.0 | 6.6922 | 6.6858 |

- hi (n=22): advantage_0.25 +0.0789 [-0.0260, +0.1838]; advantage_0.5 +0.0757 [-0.0262, +0.1776]; advantage_1.0 +0.0384 [-0.0116, +0.0885]; change_0.25_vs_1.0 +0.0404 [-0.0450, +0.1258]; change_0.5_vs_1.0 +0.0373 [-0.0580, +0.1325]
- nh (n=22): advantage_0.25 +0.0386 [-0.0520, +0.1292]; advantage_0.5 -0.0153 [-0.1025, +0.0719]; advantage_1.0 -0.0256 [-0.0686, +0.0173]; change_0.25_vs_1.0 +0.0642 [-0.0320, +0.1604]; change_0.5_vs_1.0 +0.0103 [-0.0628, +0.0835]

Note: both arms inherit the ALN3.4 people-row early-stopping rule, which selects the epoch by gain (ES loss minus mismatched loss), not by source-side true risk. The rule is identical for both starts, so the comparison is matched, but absolute risks may differ from a true-risk-selected model (see the 1050758 selection result).

