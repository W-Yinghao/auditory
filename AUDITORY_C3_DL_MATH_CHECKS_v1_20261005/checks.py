"""Analytic/finite-distribution checks for C3-DL v1; no EEG or patient data.

Run: python checks.py --out results.json
Only NumPy and the Python standard library are required.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np


def normalize(a: np.ndarray, axis: int = -1) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    s = a.sum(axis=axis, keepdims=True)
    if np.any(s <= 0):
        raise ValueError('Cannot normalize zero/negative mass.')
    return a / s


def discrete_identity(p: np.ndarray, q0: np.ndarray, q1: np.ndarray) -> dict[str, float]:
    # Axes: condition, EEG representation, target.
    p = np.asarray(p, dtype=float)
    if p.ndim != 3 or np.any(p < 0) or not np.isclose(p.sum(), 1):
        raise ValueError('p must be a normalized nonnegative C x Z x Y distribution.')
    if q0.shape != (p.shape[0], p.shape[2]) or q1.shape != p.shape:
        raise ValueError('Incompatible model shapes.')
    if np.any(q0 <= 0) or np.any(q1 <= 0):
        raise ValueError('Models must have positive probabilities.')
    if not np.allclose(q0.sum(-1), 1) or not np.allclose(q1.sum(-1), 1):
        raise ValueError('Models must be normalized.')
    pcz = p.sum(-1, keepdims=True)
    pcy = p.sum(1)
    pc = pcy.sum(-1, keepdims=True)
    pycz = np.divide(p, pcz, out=np.zeros_like(p), where=pcz > 0)
    pyc = np.divide(pcy, pc, out=np.zeros_like(pcy), where=pc > 0)
    q0b = np.broadcast_to(q0[:, None, :], p.shape)
    pycb = np.broadcast_to(pyc[:, None, :], p.shape)
    mask = p > 0
    gain = float(np.sum(p[mask] * np.log2(q1[mask] / q0b[mask])))
    cmi = float(np.sum(p[mask] * np.log2(pycz[mask] / pycb[mask])))
    d0 = float(np.sum(p[mask] * np.log2(pycb[mask] / q0b[mask])))
    d1 = float(np.sum(p[mask] * np.log2(pycz[mask] / q1[mask])))
    return {'gain_bits': gain, 'cmi_bits': cmi, 'd0_bits': d0, 'd1_bits': d1,
            'identity_abs_error': abs(gain - (cmi + d0 - d1))}


def run() -> dict:
    rng = np.random.default_rng(20261005)
    p = rng.uniform(.05, 1.0, size=(3, 4, 2)); p /= p.sum()
    q0 = normalize(rng.uniform(.05, 1., size=(3, 2)))
    q1 = normalize(rng.uniform(.05, 1., size=(3, 4, 2)))
    identity = discrete_identity(p, q0, q1)
    assert identity['identity_abs_error'] < 1e-12

    # Baseline subtraction has zero gradient when q0 is fixed.
    x = np.array([-.7, .2, 1.1]); y = np.array([0., 1., 1.])
    b = np.array([.2, -.3, .4]); theta = .41; eps = 1e-5
    def ll(th: float) -> float:
        v = b + th*x
        return float(np.mean(y*v - np.logaddexp(0., v)))
    base = float(np.mean(y*b - np.logaddexp(0., b)))
    d_ll = (ll(theta+eps)-ll(theta-eps))/(2*eps)
    d_gain = ((ll(theta+eps)-base)-(ll(theta-eps)-base))/(2*eps)
    grad = {'log_likelihood_gradient': d_ll, 'log_ratio_gradient': d_gain,
            'abs_error': abs(d_ll-d_gain)}
    assert grad['abs_error'] < 1e-9

    # History-only score: P(dev|previous std)=.25; P(dev|previous dev)=0.
    joint_hy = np.array([[.6, .2], [.2, 0.]])
    scores = np.array([.25, 0.])
    pos_h = joint_hy[:, 1]/joint_hy[:, 1].sum()
    neg_h = joint_hy[:, 0]/joint_hy[:, 0].sum()
    auc = sum(pos_h[i]*neg_h[j]*(float(scores[i]>scores[j])+.5*float(scores[i]==scores[j]))
              for i in range(2) for j in range(2))
    entropy_y = -(0.2*np.log2(.2)+.8*np.log2(.8))
    h_y_given_h = .8*(-.25*np.log2(.25)-.75*np.log2(.75))
    history = {'history_only_auc': float(auc), 'p_deviant': .2,
               'h_y_bits': float(entropy_y), 'h_y_given_history_bits': float(h_y_given_h),
               'i_history_y_bits': float(entropy_y-h_y_given_h),
               'increment_beyond_same_history_predictor_bits': 0.0,
               'scope': 'Illustrative Markov protocol; not the real BDF sequence.'}
    assert abs(auc-.625)<1e-12

    # XOR: conditional synergy is detectable though marginal information is zero.
    p_xor = np.zeros((2,2,2))
    for c in range(2):
        for z in range(2): p_xor[c,z,c^z] = .25
    q0_xor = np.full((2,2), .5)
    q1_xor = np.full((2,2,2), 1e-9)
    for c in range(2):
        for z in range(2): q1_xor[c,z,c^z] = 1-1e-9
    xor = discrete_identity(p_xor,q0_xor,q1_xor)
    xor['marginal_i_y_z_bits'] = 0.0
    assert abs(xor['cmi_bits']-1)<1e-12

    # Z=C^2: true conditional information is zero, but a weak q0 gives positive gain.
    p_fail = np.zeros((3,2,2)); prob = [.8, .1, .8]
    for ci, c in enumerate([-1,0,1]):
        z = c*c; p_fail[ci,z,:] = np.array([1-prob[ci], prob[ci]])/3
    pbar = float(np.mean(prob))
    q0_fail = np.tile([1-pbar,pbar],(3,1))
    q1_fail = np.array([[[1-v,v],[1-v,v]] for v in prob])
    misspec = discrete_identity(p_fail,q0_fail,q1_fail)
    assert abs(misspec['cmi_bits'])<1e-12 and misspec['gain_bits']>.1

    # Gaussian fixed covariance score: NLL difference equals weighted squared-error difference.
    yv = rng.normal(size=(50,3)); m0 = rng.normal(size=(50,3)); m1 = .4*yv
    var = np.array([.7,1.2,2.0])
    def gnll(mu): return .5*np.sum(np.log(2*np.pi*var)+(yv-mu)**2/var,axis=-1)
    g_ll = float(np.mean((gnll(m0)-gnll(m1))/np.log(2)))
    g_sq = float(np.mean(.5*np.sum(((yv-m0)**2-(yv-m1)**2)/var,axis=-1))/np.log(2))
    gauss = {'gain_bits_per_vector':g_ll, 'weighted_mse_gain_bits_per_vector':g_sq,
             'abs_error':abs(g_ll-g_sq)}
    assert gauss['abs_error']<1e-12

    # Balanced training probabilities cannot be used as natural-distribution probabilities unchanged.
    py = np.array([.8,.2]); q_nat = py.copy(); q_bal = np.array([.5,.5])
    ce_nat = -float(np.sum(py*np.log2(q_nat)))
    ce_bal = -float(np.sum(py*np.log2(q_bal)))
    balance = {'natural_prior_ce_bits':ce_nat, 'balanced_prior_ce_bits':ce_bal,
               'spurious_gain_if_using_balanced_prediction_bits':ce_nat-ce_bal}
    assert balance['spurious_gain_if_using_balanced_prediction_bits'] < 0
    return {'scope':'Analytic and finite-distribution checks only; no EEG, fitting or clinical validation.',
            'seed':20261005,'check_count':7,'checks':{'risk_identity':identity,
            'fixed_baseline_gradient':grad,'history_only':history,'xor':xor,
            'misspecified_background':misspec,'gaussian_shared_covariance':gauss,
            'balanced_vs_natural_prior':balance},'status':'ALL_ASSERTIONS_PASSED'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--out',type=Path,default=Path('results.json'))
    args=parser.parse_args(); output=run(); args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(output,ensure_ascii=False,indent=2))
