"""
synthetic_checks.py — the five checks of 03_MEASUREMENT_SPEC §7.7 / 08_SYNTHETIC_CHECKS.md.

Run:  python reference/synthetic_checks.py   (from the package root)
Writes: reference/checks_c3.json. No real EEG is read.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from gcmi_core import (  # noqa: E402
    circular_shift_surrogates, cmi_model_gdd, gcmi_cc, gcmi_ccc, gcmi_model_cd,
    pid_mmi, tmif,
)

rng = np.random.default_rng(20261003)
R = {}


def _r(x):
    return float(np.round(x, 5))


# S1. Analytic Gaussian: I = -0.5 log2(1 - rho^2)
rho = 0.6
n = 20000
a = rng.standard_normal(n)
b = rho * a + np.sqrt(1 - rho**2) * rng.standard_normal(n)
R["S1_analytic_gaussian"] = {"rho": rho, "I_analytic": _r(-0.5 * np.log2(1 - rho**2)),
                             "I_gcmi": _r(gcmi_cc(a, b))}

# S2. CMI removes a common cause: x <- z -> y, I(x;y|z) ~ 0 while I(x;y) > 0
z = rng.standard_normal(n)
x = z + 0.7 * rng.standard_normal(n)
y = z + 0.7 * rng.standard_normal(n)
R["S2_cmi_common_cause"] = {"I_xy": _r(gcmi_cc(x, y)), "I_xy_given_z": _r(gcmi_ccc(x, y, z))}

# S3. Pure redundancy: T = A, B = A + small noise -> R ~ I(T;A), unique ~ 0, S ~ 0
t = a + 0.05 * rng.standard_normal(n)  # near-deterministic; exact copy would make the copula covariance singular
b2 = a + 0.3 * rng.standard_normal(n)
ita, itb, itab = gcmi_cc(t, a), gcmi_cc(t, b2), gcmi_cc(t, np.column_stack([a, b2]))
R["S3_pure_redundancy_mmi"] = {k: _r(v) for k, v in pid_mmi(ita, itb, itab).items()}
R["S3_pure_redundancy_mmi"]["note"] = "T~A, B = A + noise: under MMI, R = I(T;B) (bounded by the weaker source) and the excess goes to U_A; S ~ 0. This is the MMI structural property, not a bug."

# S4a. Additive synergy visible to GCMI: T = A + B + noise, A, B independent
e = 0.3 * rng.standard_normal(n)
t2 = a + rng.standard_normal(n) + e
bb = (t2 - a - e)  # B exactly
ita, itb, itab = gcmi_cc(t2, a), gcmi_cc(t2, bb), gcmi_cc(t2, np.column_stack([a, bb]))
R["S4a_additive_synergy_mmi"] = {k: _r(v) for k, v in pid_mmi(ita, itb, itab).items()}
# S4b. XOR-type synergy INVISIBLE to GCMI: T = A*B  (documented limitation)
t3 = a * rng.standard_normal(n)
bb3 = t3 / np.where(np.abs(a) < 1e-6, 1e-6, a)
R["S4b_xor_type_invisible"] = {"I_TA": _r(gcmi_cc(t3, a)), "I_TB": _r(gcmi_cc(t3, bb3)),
                               "I_TAB": _r(gcmi_cc(t3, np.column_stack([a, bb3]))),
                               "note": "Gaussian copula cannot see multiplicative/XOR synergy; declare as limitation."}

# S5. Bias vs dimension and sample size for INDEPENDENT variables; raw vs bias-corrected vs surrogate-corrected
bias = []
for d in (1, 3, 5, 8):
    for nn in (200, 500, 1000, 3000):
        xx = rng.standard_normal((nn, d))
        yy = rng.standard_normal((nn, 1))
        raw = gcmi_cc(xx, yy, biascorrect=False)
        bc = gcmi_cc(xx, yy, biascorrect=True)
        _, sc, _ = circular_shift_surrogates(lambda p, q: gcmi_cc(p, q, biascorrect=True), xx, yy, n_sur=50, rng=1)
        bias.append({"d": d, "n": nn, "raw": _r(raw), "biascorrected": _r(bc), "surrogate_corrected": _r(sc)})
R["S5_bias_curve_independent"] = bias

# S6. Early-lag aliasing: AR(1) stimulus, response only at lag L; TMIF shows MI at an earlier lag,
#     CMI given the true lag removes it.
phi, lag_e, lag_l, nts = 0.98, 20, 40, 60000
s = np.empty(nts)
s[0] = rng.standard_normal()
for i in range(1, nts):
    s[i] = phi * s[i - 1] + np.sqrt(1 - phi**2) * rng.standard_normal()
resp = np.roll(s, lag_l) + 0.5 * rng.standard_normal(nts)
seg = slice(lag_l, None)
s_e, s_l, r_ = np.roll(s, lag_e)[seg], np.roll(s, lag_l)[seg], resp[seg]
R["S6_early_lag_aliasing"] = {"I_resp_earlylag": _r(gcmi_cc(r_, s_e)),
                              "I_resp_truelag": _r(gcmi_cc(r_, s_l)),
                              "I_resp_earlylag_given_truelag": _r(gcmi_ccc(r_, s_e, s_l)),
                              "tmif_peak_lag_samples": int(np.array(list(range(0, 61, 5)))[np.argmax(tmif(s, resp, list(range(0, 61, 5))))])}

# S7. Oddball history: logit depends only on current class -> I(T;Hist|Cur) ~ 0 after permutation correction;
#     inject run-length dependence -> I(T;Hist|Cur) > 0.
ntr = 4000
cur = (rng.random(ntr) < 0.2).astype(int)  # 20% deviants
prev = np.roll(cur, 1)
prev[0] = 0
run = np.zeros(ntr, int)
for i in range(1, ntr):
    run[i] = run[i - 1] + 1 if cur[i] == cur[i - 1] else 0
run = np.minimum(run, 8)
logit_cur_only = 1.0 * cur + rng.standard_normal(ntr)
logit_with_hist = 1.0 * cur - 0.25 * run + rng.standard_normal(ntr)


def cmi_stat(lg, hist_and_cur):
    h, c = hist_and_cur[:, 0], hist_and_cur[:, 1]
    return cmi_model_gdd(lg, h, c)


hc = np.column_stack([run, cur])


def stratified_null(lg, cur_lab, hist_cur, n_sur=100, seed=2):
    """Null for I(T;Hist|Cur): permute T within each current-class stratum.
    Keeps I(T;Cur) and the history sequence statistics intact; breaks any T-history link."""
    g = np.random.default_rng(seed)
    vals = np.empty(n_sur)
    for i in range(n_sur):
        lg_p = lg.copy()
        for c in np.unique(cur_lab):
            idx = np.flatnonzero(cur_lab == c)
            lg_p[idx] = lg[g.permutation(idx)]
        vals[i] = cmi_stat(lg_p, hist_cur)
    return vals


obs0 = cmi_stat(logit_cur_only, hc)
sur0 = stratified_null(logit_cur_only, cur, hc)
obs1 = cmi_stat(logit_with_hist, hc)
sur1 = stratified_null(logit_with_hist, cur, hc)
R["S7_oddball_history"] = {"I_T_Cur_curonly": _r(gcmi_model_cd(logit_cur_only, cur)),
                           "curonly_raw": _r(obs0), "curonly_surrogate_mean": _r(sur0.mean()),
                           "curonly_corrected": _r(obs0 - sur0.mean()),
                           "withhist_raw": _r(obs1), "withhist_surrogate_mean": _r(sur1.mean()),
                           "withhist_corrected": _r(obs1 - sur1.mean()),
                           "note": "corrected value for cur-only generator should be ~0; with-hist generator clearly > 0."}

# S8. Common artifact changes MI difference although neural weights are fixed (V4 A2 in MI units)
out = []
for k in (0.0, 1.0, 4.0):
    A = rng.standard_normal(n)
    B = rng.standard_normal(n)
    T = 2 * A + B + k * (A + B) + 0.5 * rng.standard_normal(n)
    out.append({"k": k, "I_TA": _r(gcmi_cc(T, A)), "I_TB": _r(gcmi_cc(T, B)), "diff": _r(gcmi_cc(T, A) - gcmi_cc(T, B))})
R["S8_common_artifact"] = out

out_path = os.path.join(os.path.dirname(__file__), "checks_c3.json")
with open(out_path, "w") as f:
    json.dump(R, f, indent=1)
print(json.dumps(R, indent=1))
print("written:", out_path)
