"""NumPy/Torch value, first-derivative and first-order boundary checks.

Exit 0: checks passed. Exit 1: error/check failure. Exit 2: torch unavailable.
No production dataset, backbone asset, GPU or server runner is validated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cs-reference-dir", type=Path,
                        help="directory containing the unchanged cs_qmi_reference.py")
    parser.add_argument("--json", "--out", dest="json", type=Path)
    args = parser.parse_args()
    if args.cs_reference_dir:
        sys.path.insert(0, str(args.cs_reference_dir.resolve()))

    def emit(report):
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))

    try:
        import torch
    except ModuleNotFoundError as exc:
        if exc.name != "torch":
            raise
        emit({"status": "unavailable", "reason": "torch_not_installed", "exit_code": 2,
              "scope": "Torch value/gradient verification NOT executed; not a pass"})
        return 2

    import numpy as np
    from temporal_cs_reference import (adapt_delta_cs, logsumexp, softmax, temporal_cs,
                                       temporal_cs_potentials, uniform_prior_kl)
    from temporal_objectives_torch import (ViewBatch, adapt_delta_fo, episode_loss_fo,
        global_cs_score, masks_from_packed_keys, objective_loss, prior_uniform_kl,
        temporal_cs_score, temporal_nce_loss)

    rng = np.random.default_rng(20261021)
    checks = []

    def close(name, actual, expected, tol=2e-9):
        if isinstance(actual, torch.Tensor):
            actual = actual.detach().cpu().numpy()
        error = float(np.max(np.abs(np.asarray(actual) - np.asarray(expected))))
        assert error <= tol, (name, error, actual, expected)
        checks.append({"check": name, "status": "pass", "max_abs_error": error})

    def tensor(x, grad=False):
        return torch.tensor(x, dtype=torch.float64, requires_grad=grad)

    n, slots, d = 9, 3, 4
    un = rng.normal(size=(n, slots, d)); vn = rng.normal(size=(n, d))
    an = np.array([-.7, .3, .1]); su, sv, sg = 1.4, 1.1, .8
    u, v, a = tensor(un, True), tensor(vn), tensor(an, True)
    view = ViewBatch(u, v, su, sv, sg, "env")
    cs, _ = temporal_cs_score(view, a)
    numpy_cs = temporal_cs(un, vn, softmax(an), su, sv)
    close("TCS_value_matches_NumPy", cs, numpy_cs["score_nats"])
    gu, ga = torch.autograd.grad(cs, (u, a), retain_graph=True)
    close("TCS_gate_gradient_matches_NumPy_analytic", ga, numpy_cs["score_gradient_logits"])
    h, index = 1e-6, (2, 1, 3)
    plus, minus = un.copy(), un.copy(); plus[index] += h; minus[index] -= h
    fd_u = (temporal_cs(plus, vn, softmax(an), su, sv)["score_nats"]
            - temporal_cs(minus, vn, softmax(an), su, sv)["score_nats"]) / (2*h)
    close("TCS_EEG_gradient_matches_NumPy_difference", gu[index], fd_u, 2e-8)

    def numpy_global(uu, aa):
        pooled = np.sum(softmax(aa)[None, :, None] * uu, axis=1)
        pooled = pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)
        return temporal_cs(pooled[:, None], vn, [1.], sg, sv)["score_nats"]

    gcs, _ = global_cs_score(view, a)
    close("adaptive_GCS_value_matches_NumPy", gcs, numpy_global(un, an))
    ggu, gga = torch.autograd.grad(gcs, (u, a), retain_graph=True)
    fd_gate = np.zeros(slots)
    for k in range(slots):
        delta = np.zeros(slots); delta[k] = h
        fd_gate[k] = (numpy_global(un, an+delta) - numpy_global(un, an-delta))/(2*h)
    close("adaptive_GCS_gate_gradient_matches_NumPy_difference", gga, fd_gate, 2e-8)
    close("adaptive_GCS_EEG_gradient_matches_NumPy_difference", ggu[index],
          (numpy_global(plus, an)-numpy_global(minus, an))/(2*h), 2e-8)

    def pack(f, p, s):
        return (f << 40) | (p << 24) | s

    keys = torch.tensor([pack(1,1,0), pack(1,1,0), pack(1,1,64), pack(1,1,300),
                         pack(2,2,0), pack(2,2,300), pack(3,3,0), pack(3,4,300),
                         pack(4,5,0)], dtype=torch.int64)
    pos, excl = masks_from_packed_keys(keys, unknown_clock_families=(3,))
    assert bool(pos[0,1]) and not bool(excl[0,1]) and bool(excl[0,2])
    assert not bool(excl[0,3]) and bool(excl[6,7]) and not bool((pos & excl).any())
    checks.append({"check": "multi_positive_near_time_unknown_clock_masks", "status": "pass"})
    pn, en = pos.numpy(), excl.numpy()

    def numpy_nce(uu, aa):
        uu = uu / np.maximum(np.linalg.norm(uu, axis=-1, keepdims=True), 1e-12)
        vv = vn / np.maximum(np.linalg.norm(vn, axis=-1, keepdims=True), 1e-12)
        slot_losses = []
        for k in range(slots):
            logits = uu[:, k] @ vv.T / .1
            allowed = np.where(en, -np.inf, logits)
            positive = np.where(pn, logits, -np.inf)
            l1 = np.mean(logsumexp(allowed, axis=1)-logsumexp(positive, axis=1))
            l2 = np.mean(logsumexp(allowed, axis=0)-logsumexp(positive, axis=0))
            slot_losses.append(.5*(l1+l2))
        return np.dot(softmax(aa), slot_losses)

    nce, _ = temporal_nce_loss(view, a, positive=pos, exclusion=excl)
    close("TNCE_masked_multi_positive_value_matches_NumPy", nce, numpy_nce(un, an))
    ngu, nga = torch.autograd.grad(nce, (u, a), retain_graph=True)
    fd_gate = np.zeros(slots)
    for k in range(slots):
        delta = np.zeros(slots); delta[k] = h
        fd_gate[k] = (numpy_nce(un, an+delta)-numpy_nce(un, an-delta))/(2*h)
    close("TNCE_gate_gradient_matches_NumPy_difference", nga, fd_gate, 2e-8)
    close("TNCE_EEG_gradient_matches_NumPy_difference", ngu[index],
          (numpy_nce(plus, an)-numpy_nce(minus, an))/(2*h), 2e-8)
    kl = prior_uniform_kl(a)
    close("common_uniform_prior_KL_value", kl, uniform_prior_kl(an)[0])
    close("common_uniform_prior_KL_gradient", torch.autograd.grad(kl, a)[0], uniform_prior_kl(an)[1])

    reference_adapt = adapt_delta_cs([temporal_cs_potentials(un, vn, su, sv)], an,
                                    steps=5, step_size=.1, l2=.1)
    delta_torch, _ = adapt_delta_fo("TCS", [view], a, steps=5, step_size=.1, delta_l2=.1)
    close("TCS_five_inner_updates_match_NumPy", delta_torch, reference_adapt["delta"])

    # New leaves for each objective; S and Q have different EEG/audio arrays.
    for kind in ("TCS", "TNCE", "GCS"):
        us = tensor(rng.normal(size=(n,slots,d)), True)
        uq = tensor(rng.normal(size=(n,slots,d)), True)
        vs, vq = tensor(rng.normal(size=(n,d))), tensor(rng.normal(size=(n,d)))
        aa = tensor(an, True)
        support = [ViewBatch(us, vs, su, sv, sg, "env")]
        query = [ViewBatch(uq, vq, su, sv, sg, "env")]
        episode, report = episode_loss_fo(kind, support, query, aa, support_keys=keys,
                                         query_keys=keys, unknown_clock_families=(3,),
                                         steps=5, step_size=.1, delta_l2=.1, prior_kl_weight=.01)
        gsupport, gquery, gprior = torch.autograd.grad(episode, (us, uq, aa),
                                                     allow_unused=True, retain_graph=True)
        assert gsupport is None, (kind, "support unexpectedly received outer gradient")
        assert gquery is not None and bool(torch.isfinite(gquery).all()) and float(gquery.abs().sum()) > 0
        assert gprior is not None and bool(torch.isfinite(gprior).all())
        assert not report["delta"].requires_grad and report["delta"].grad_fn is None
        assert len(report["adaptation"]["history"]) == 5
        manual, _ = objective_loss(kind, query, aa + report["delta"], keys=keys,
                                   unknown_clock_families=(3,))
        manual = manual + .01 * prior_uniform_kl(aa)
        gm_query, gm_prior = torch.autograd.grad(manual, (uq, aa))
        close(kind+"_FO_query_gradient_equals_explicit_detached_delta", gquery, gm_query)
        close(kind+"_FO_live_prior_gradient_equals_explicit_detached_delta", gprior, gm_prior)
        changed_query = [ViewBatch(uq.detach()*2.3, vq.detach().flip(0), su, sv, sg, "env")]
        _, changed = episode_loss_fo(kind, support, changed_query, aa, support_keys=keys,
                                     query_keys=keys, unknown_clock_families=(3,), steps=5)
        close(kind+"_query_mutation_does_not_change_support_delta", report["delta"], changed["delta"])
        checks.append({"check": kind+"_support_detached_query_live_no_second_order", "status": "pass"})

    # Two views must mean losses, not accidentally sum them or pool their sigmas.
    second = ViewBatch(u, v, 1.9, 1.6, 1.2, "ss")
    for kind in ("TCS", "TNCE", "GCS"):
        joint, _ = objective_loss(kind, [view, second], a, keys=keys, unknown_clock_families=(3,))
        one, _ = objective_loss(kind, [view], a, keys=keys, unknown_clock_families=(3,))
        two, _ = objective_loss(kind, [second], a, keys=keys, unknown_clock_families=(3,))
        close(kind+"_views_are_equally_weighted", joint, .5*(one+two))

    emit({"status": "pass", "torch_version": torch.__version__, "device": "cpu", "seed": 20261021,
          "scope": "reference value/first-derivative/FO-detach checks only; not production data or model validation",
          "n_checks": len(checks), "checks": checks})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
