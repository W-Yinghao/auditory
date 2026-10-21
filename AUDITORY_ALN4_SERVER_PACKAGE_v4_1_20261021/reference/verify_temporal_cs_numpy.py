"""Deterministic mathematical checks; no EEG files, torch, training or GPUs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from temporal_cs_reference import (adapt_delta_cs, gaussian_log_gram, softmax,
    temporal_cs, temporal_cs_expanded, temporal_cs_from_potentials,
    temporal_cs_potentials, uniform_prior_kl, weighted_cs_from_log_grams)


def verify():
    rng = np.random.default_rng(20261021)
    checks = []

    def close(name, actual, expected, tol=2e-10):
        error = float(np.max(np.abs(np.asarray(actual) - np.asarray(expected))))
        assert error <= tol, (name, error, actual, expected)
        checks.append({"check": name, "status": "pass", "max_abs_error": error})

    u = rng.normal(size=(17, 3, 5)); v = rng.normal(size=(17, 4))
    q = np.array([0.13, 0.61, 0.26]); su, sv = 1.7, 1.3
    r = temporal_cs(u, v, q, su, sv)
    close("expanded_counting_measure_KDE_equals_q_squared_formula",
          r["score_nats"], temporal_cs_expanded(u, v, q, su, sv))
    close("expanded_KDE_with_zero_slot_probability",
          temporal_cs(u, v, [0., .4, .6], su, sv)["score_nats"],
          temporal_cs_expanded(u, v, [0., .4, .6], su, sv))
    ordinary = weighted_cs_from_log_grams(gaussian_log_gram(u[:, 0], su),
                                         gaussian_log_gram(v, sv), np.ones(17) / 17)
    close("single_slot_reduces_to_ordinary_CS",
          temporal_cs(u[:, :1], v, [1.], su, sv)["score_nats"], ordinary)
    close("identical_slots_reduce_to_ordinary_CS_for_nonuniform_q",
          temporal_cs(np.repeat(u[:, :1], 3, axis=1), v, q, su, sv)["score_nats"], ordinary)
    const_u = np.repeat(rng.normal(size=(1, 3, 5)), 17, axis=0)
    close("constant_EEG_within_each_slot_is_independent_of_audio",
          temporal_cs(const_u, v, q, su, sv)["score_nats"], 0.)
    const_v = np.repeat(v[:1], 17, axis=0)
    close("constant_audio_is_independent_of_time_tagged_EEG",
          temporal_cs(u, const_v, q, su, sv)["score_nats"], 0.)
    perm = rng.permutation(17)
    close("simultaneous_anchor_permutation_invariance", r["score_nats"],
          temporal_cs(u[perm], v[perm], q, su, sv)["score_nats"])
    slot_perm = np.array([2, 0, 1])
    close("slot_relabeling_with_q_relabeling", r["score_nats"],
          temporal_cs(u[:, slot_perm], v, q[slot_perm], su, sv)["score_nats"])
    close("audio_marginal_stays_uniform_under_nonuniform_q",
          np.sum(q[:, None] * np.ones((3, 17)) / 17, axis=0), np.ones(17) / 17)

    a = np.log(q); h = 1e-6
    numerical = np.zeros(3)
    for k in range(3):
        d = np.zeros(3); d[k] = h
        plus = temporal_cs_from_potentials(r, softmax(a + d))["score_nats"]
        minus = temporal_cs_from_potentials(r, softmax(a - d))["score_nats"]
        numerical[k] = (plus - minus) / (2 * h)
    close("analytic_gate_logit_gradient_matches_finite_difference",
          r["score_gradient_logits"], numerical, tol=3e-9)
    close("gate_gradient_null_direction", r["score_gradient_logits"].sum(), 0.)
    kl, kl_grad = uniform_prior_kl(a)
    numerical_kl = np.zeros(3)
    for k in range(3):
        d = np.zeros(3); d[k] = h
        numerical_kl[k] = (uniform_prior_kl(a + d)[0] - uniform_prior_kl(a - d)[0]) / (2 * h)
    close("uniform_prior_KL_gradient", kl_grad, numerical_kl, tol=3e-9)

    # Independent source support and query. Only support is passed to adapt.
    support = temporal_cs_potentials(u[:9], v[:9], su, sv)
    adapted = adapt_delta_cs([support], np.zeros(3), steps=5, step_size=.1, l2=.1)
    query1 = temporal_cs(u[9:], v[9:], adapted["q"], su, sv)
    query2 = temporal_cs(u[9:], rng.normal(size=v[9:].shape), adapted["q"], su, sv)
    adapted_again = adapt_delta_cs([support], np.zeros(3), steps=5, step_size=.1, l2=.1)
    close("query_changes_cannot_change_support_only_delta", adapted["delta"], adapted_again["delta"])
    close("delta_has_zero_mean", adapted["delta"].mean(), 0.)
    assert np.isfinite(query1["score_nats"]) and np.isfinite(query2["score_nats"])

    try:
        temporal_cs(u, v, q, np.array([1., 2., 3.]), sv)
    except ValueError:
        checks.append({"check": "slot_specific_sigma_rejected", "status": "pass"})
    else:
        raise AssertionError("slot-specific sigma silently accepted")

    # Deterministic true vs independently permuted audio example, not a universal
    # claim that a finite-sample score detects all true dependencies.
    n = 256
    a_signal = rng.normal(size=(n, 2))
    signal_u = np.stack([a_signal + .08*rng.normal(size=(n, 2)),
                         rng.normal(size=(n, 2)), rng.normal(size=(n, 2))], axis=1)
    true = temporal_cs(signal_u, a_signal, [.6, .2, .2], 1., 1.)["score_nats"]
    wrong = temporal_cs(signal_u, a_signal[rng.permutation(n)], [.6, .2, .2], 1., 1.)["score_nats"]
    assert true > wrong + .02, (true, wrong)
    checks.append({"check": "constructed_dependency_exceeds_wrong_pairing", "status": "pass",
                   "true_score_nats": true, "wrong_score_nats": wrong})
    return {"status": "pass", "scope": "NumPy mathematical reference only; not production/GPU/gradient-through-EEG validation",
            "seed": 20261021, "n_checks": len(checks), "checks": checks,
            "warning": "CS scores are not Shannon mutual information or neural latency; q_squared pooling is density-scale sensitive."}


def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", "--out", dest="json", type=Path); args = p.parse_args()
    report = verify()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
