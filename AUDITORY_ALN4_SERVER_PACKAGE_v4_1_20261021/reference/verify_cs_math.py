#!/usr/bin/env python3
"""Independent checks for cs_qmi_reference.py; no training or dataset access.

The oracle explicitly builds two Gaussian mixtures: p_xy has n components;
p_x*p_y has n^2 components. It integrates each Gaussian pair using its full
covariance matrix. It does NOT use the factored Gram score to obtain expected
values or finite-difference gradients. A 2-D quadrature also checks that oracle.

Requires NumPy. PyTorch is required for full PASS; when unavailable the oracle
checks run, but exit status is 2 (INCOMPLETE), never a false module-validation
success. --json writes an optional machine-readable receipt.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np


def gaussian_overlap(mean_a, covariance_a, mean_b, covariance_b):
    """Integral N(z;ma,Ca)*N(z;mb,Cb) dz = N(ma;mb,Ca+Cb)."""
    delta = np.asarray(mean_a) - np.asarray(mean_b)
    covariance = np.asarray(covariance_a) + np.asarray(covariance_b)
    sign, logdet = np.linalg.slogdet(covariance)
    if sign <= 0:
        raise ValueError("Gaussian covariance must be positive definite")
    return float(np.exp(-0.5 * (len(delta) * np.log(2 * np.pi) + logdet
                               + delta @ np.linalg.solve(covariance, delta))))


def mixture_overlap(left, right):
    # Each component: (mass, mean vector, covariance, optional category).
    total = 0.0
    for wa, ma, ca, ya in left:
        for wb, mb, cb, yb in right:
            if ya == yb:
                total += wa * wb * gaussian_overlap(ma, ca, mb, cb)
    return total


def explicit_mixtures(x, y, sigma_x, sigma_y=None, weights=None, categorical=False):
    x = np.asarray(x, dtype=np.float64)
    w = np.ones(len(x)) / len(x) if weights is None else np.asarray(weights, dtype=np.float64)
    w = w / w.sum()
    if categorical:
        # Integrate over continuous x and sum over counting-measure categories.
        covariance = np.eye(x.shape[1]) * sigma_x**2 / 2
        p = [(w[i], x[i], covariance, int(y[i])) for i in range(len(x))]
        q = [(w[i] * w[j], x[i], covariance, int(y[j]))
             for i in range(len(x)) for j in range(len(x))]
    else:
        y = np.asarray(y, dtype=np.float64)
        covariance = np.diag([sigma_x**2 / 2] * x.shape[1] + [sigma_y**2 / 2] * y.shape[1])
        p = [(w[i], np.concatenate((x[i], y[i])), covariance, None) for i in range(len(x))]
        q = [(w[i] * w[j], np.concatenate((x[i], y[j])), covariance, None)
             for i in range(len(x)) for j in range(len(x))]
    return p, q


def oracle(x, y, sigma_x, sigma_y=None, weights=None, categorical=False):
    p, q = explicit_mixtures(x, y, sigma_x, sigma_y, weights, categorical)
    logs = np.log([mixture_overlap(p, p), mixture_overlap(q, q), mixture_overlap(p, q)])
    return float(logs[0] + logs[1] - 2 * logs[2]), logs


def numpy_gram_formula(x, y, sigma_x, sigma_y, weights):
    """Secondary NumPy algebra check only; this is NOT the independent oracle."""
    w = np.asarray(weights, dtype=np.float64)
    w = w / w.sum()
    k = np.exp(-np.square(x[:, None, :] - x[None, :, :]).sum(-1) / (2 * sigma_x**2))
    l = np.exp(-np.square(y[:, None, :] - y[None, :, :]).sum(-1) / (2 * sigma_y**2))
    a = w @ (k * l) @ w
    b = (w @ k @ w) * (w @ l @ w)
    c = w @ ((k @ w) * (l @ w))
    return float(np.log(a) + np.log(b) - 2 * np.log(c))


def numerical_quadrature(x, y, sx, sy, w):
    """Direct 2-D density integration, independent of Gaussian overlap algebra."""
    hx, hy = sx / np.sqrt(2), sy / np.sqrt(2)
    nodes, weights = np.polynomial.legendre.leggauss(180)

    def grid(values, h):
        lo, hi = float(values.min() - 10 * h), float(values.max() + 10 * h)
        return (nodes + 1) * (hi - lo) / 2 + lo, weights * (hi - lo) / 2

    gx, wx = grid(x, hx)
    gy, wy = grid(y, hy)
    px = np.exp(-0.5 * ((gx[:, None] - x[:, 0]) / hx)**2) / (np.sqrt(2 * np.pi) * hx)
    py = np.exp(-0.5 * ((gy[:, None] - y[:, 0]) / hy)**2) / (np.sqrt(2 * np.pi) * hy)
    p = (px * w) @ py.T
    q = np.outer(px @ w, py @ w)
    integration_weight = np.outer(wx, wy)
    return np.array([(p * p * integration_weight).sum(), (q * q * integration_weight).sum(),
                     (p * q * integration_weight).sum()])


def finite_difference(x, y, sx, sy, w, step):
    gradients = []
    for which, values in enumerate((x, y)):
        gradient = np.zeros_like(values)
        for index in np.ndindex(values.shape):
            plus, minus = values.copy(), values.copy()
            plus[index] += step
            minus[index] -= step
            xp, yp = (plus, y) if which == 0 else (x, plus)
            xm, ym = (minus, y) if which == 0 else (x, minus)
            gradient[index] = (oracle(xp, yp, sx, sy, w)[0]
                               - oracle(xm, ym, sx, sy, w)[0]) / (2 * step)
        gradients.append(gradient)
    return gradients


def run_checks():
    checks = []

    def check(name, actual, expected, atol=2e-10, rtol=2e-9):
        error = float(np.max(np.abs(np.asarray(actual) - np.asarray(expected))))
        np.testing.assert_allclose(actual, expected, atol=atol, rtol=rtol, err_msg=name)
        checks.append(dict(name=name, status="PASS", max_abs_error=error))

    x = np.array([[-0.9, 0.2], [0.1, 1.1], [1.2, -0.3]])
    y = np.array([[-0.7], [0.5], [1.4]])
    w = np.array([0.2, 0.35, 0.45])
    sx, sy = 0.8, 0.6
    expected, expected_logs = oracle(x, y, sx, sy, w)
    check("weighted_Gram_vs_explicit_n_and_n_squared_Gaussian_mixtures",
          numpy_gram_formula(x, y, sx, sy, w), expected)

    x1 = x[:, :1]
    _, logs1 = oracle(x1, y, sx, sy, w)
    check("Gaussian_analytic_integrals_vs_direct_2D_quadrature",
          numerical_quadrature(x1, y, sx, sy, w), np.exp(logs1))

    # A full Cartesian product represents exact independence even at finite n.
    ix = np.repeat(np.array([[-1.0], [0.8]]), 3, axis=0)
    iy = np.tile(np.array([[-1.1], [0.2], [1.4]]), (2, 1))
    check("factorizing_Cartesian_joint_is_zero", oracle(ix, iy, 0.9, 0.7)[0], 0)
    check("collapsed_x_is_zero", oracle(np.zeros_like(x), y, sx, sy, w)[0], 0)
    check("one_category_is_zero", oracle(x, np.zeros(3), sx, weights=w, categorical=True)[0], 0)

    rng = np.random.default_rng(4100)
    nx, ny = rng.normal(size=(6, 1)), rng.normal(size=(6, 1))
    check("narrow_unique_independent_draws_give_log_n", oracle(nx, ny, 1e-4, 1e-4)[0], math.log(6))
    duplicates_y = np.repeat(np.array([[-1.0], [0.0], [2.0]]), 2, axis=0)
    check("narrow_duplicated_audio_gives_log_n_over_two",
          oracle(nx, duplicates_y, 1e-4, 1e-4)[0], math.log(3))

    reflected, _ = oracle(-x, y, sx, sy, w)
    check("CS_unchanged_by_reflecting_one_modality", reflected, expected)
    audio = np.array([[-1.0], [1.0]])
    retrieval_accuracy = np.mean(np.argmax((-audio) @ audio.T, axis=1) == np.arange(2))
    check("reflection_can_reverse_all_pointwise_cosine_matches", retrieval_accuracy, 0)

    gradients = finite_difference(x, y, sx, sy, w, 1e-5)
    finer_gradients = finite_difference(x, y, sx, sy, w, 5e-6)
    check("independent_oracle_finite_difference_step_convergence",
          np.concatenate([g.ravel() for g in gradients]),
          np.concatenate([g.ravel() for g in finer_gradients]), atol=2e-8, rtol=2e-6)

    torch_available = importlib.util.find_spec("torch") is not None
    if torch_available:
        import torch
        from cs_qmi_reference import cs_qmi, calibrate_overlap_sigma

        tx = torch.tensor(x, dtype=torch.float64, requires_grad=True)
        ty = torch.tensor(y, dtype=torch.float64, requires_grad=True)
        tw = torch.tensor(w, dtype=torch.float64)
        score, stats = cs_qmi(tx, ty, sigma_u=sx, sigma_v=sy, weights=tw, normalized_overlap=True)
        check("PyTorch_score_vs_independent_density_integral", float(score.detach()), expected)
        check("PyTorch_each_potential_vs_independent_density_integral",
              [stats["log_joint_square"], stats["log_marginal_product_square"], stats["log_cross_overlap"]],
              expected_logs)
        score.backward()
        check("PyTorch_autograd_x_vs_independent_density_finite_difference", tx.grad.numpy(),
              gradients[0], atol=3e-8, rtol=3e-6)
        check("PyTorch_autograd_y_vs_independent_density_finite_difference", ty.grad.numpy(),
              gradients[1], atol=3e-8, rtol=3e-6)
        unnormalized, _ = cs_qmi(tx, ty, sigma_u=sx, sigma_v=sy, weights=tw)
        check("normalized_and_unnormalized_overlap_same_score", float(unnormalized.detach()), expected)

        labels = np.array([0, 1, 1])
        categorical_score, categorical_stats = cs_qmi(tx, labels=torch.tensor(labels), sigma_u=sx,
                                                      weights=tw, normalized_overlap=True)
        cat_expected, cat_logs = oracle(x, labels, sx, weights=w, categorical=True)
        check("PyTorch_categorical_vs_counting_measure_integral", float(categorical_score.detach()), cat_expected)
        check("PyTorch_categorical_each_potential", [categorical_stats[k] for k in
              ("log_joint_square", "log_marginal_product_square", "log_cross_overlap")], cat_logs)

        # Nonuniform weights with one zero row must equal explicitly omitting it.
        zw = np.array([0.4, 0.0, 0.6])
        zero_score, _ = cs_qmi(tx, ty, sigma_u=sx, sigma_v=sy, weights=torch.tensor(zw))
        check("PyTorch_zero_weight_observation", float(zero_score.detach()), oracle(x, y, sx, sy, zw)[0])
        panel = torch.tensor([[0.0], [1.0], [4.0], [10.0]], dtype=torch.float64)
        sigma, metadata = calibrate_overlap_sigma(panel)
        check("calibration_lower_median_of_training_pairs", sigma, 4.0)
        check("KDE_SD_vs_overlap_sigma", metadata["kde_component_sd"], 4.0 / math.sqrt(2))
        versions = dict(torch=torch.__version__, numpy=np.__version__)
    else:
        checks.append(dict(name="PyTorch_reference_values_and_autograd", status="NOT_RUN",
                           reason="PyTorch unavailable; NumPy/oracle checks do not execute the PyTorch module"))
        versions = dict(torch=None, numpy=np.__version__)
    return dict(status="PASS" if torch_available else "INCOMPLETE_TORCH_UNAVAILABLE",
                python=platform.python_version(), executable=sys.executable,
                versions=versions, checks=checks,
                scope="Mathematical/module verification only; no efficacy or training-run claim")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="optional verification receipt path")
    args = parser.parse_args()
    try:
        result = run_checks()
    except Exception as exc:
        result = dict(status="FAIL", error=f"{type(exc).__name__}: {exc}")
    if args.json:
        args.json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else (2 if result["status"].startswith("INCOMPLETE") else 1)


if __name__ == "__main__":
    raise SystemExit(main())
