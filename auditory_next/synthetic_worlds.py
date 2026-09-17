"""Deterministic synthetic worlds for the auditory_next v2 contracts.

Generators only create arrays. They do not fit classifiers or run Monte Carlo
loops; callers choose train/test groups and repetitions explicitly.
"""

from __future__ import annotations

import numpy as np


def _rng(seed):
    if not isinstance(seed, (int, np.integer)):
        raise ValueError("seed must be an integer")
    return np.random.default_rng(int(seed))


def _split(n, rng):
    if n < 4:
        raise ValueError('at least four independent synthetic candidates required')
    groups = np.arange(n)
    rng.shuffle(groups)
    cut = max(2, int(.6 * n))
    return groups[:cut], groups[cut:]


def _group_size(n, size, *, minimum=8):
    if not isinstance(size, (int, np.integer)) or isinstance(size, (bool, np.bool_)) or size < minimum or n % size:
        raise ValueError("invalid synthetic observations per candidate")
    if n // size < 4:
        raise ValueError("at least four independent synthetic candidates required")
    return int(size)


def _common(n, rng, make, observations_per_group=8):
    if n < 32 or n % 8:
        raise ValueError("n must be a multiple of 8 and at least 32")
    size = _group_size(n, observations_per_group)
    group = np.arange(n) // size
    train_g, test_g = _split(len(np.unique(group)), rng)
    # group labels are deliberately synthetic and not clinical identifiers.
    tr, te = np.isin(group, train_g), np.isin(group, test_g)
    data = make(n, rng)
    data["candidate_id"] = np.array([f"synthetic_{i}" for i in group])
    data["group_id"] = group
    data["train_mask"], data["test_mask"] = tr, te
    data["train"] = {k: v[tr] for k, v in data.items() if isinstance(v, np.ndarray) and len(v) == n}
    data["test"] = {k: v[te] for k, v in data.items() if isinstance(v, np.ndarray) and len(v) == n}
    return data


def n1_prior_only(n=240, seed=20260917, *, observations_per_group=8):
    def make(n, r):
        h = np.arange(n) % 2; y=h.copy()
        for start in range(0,n,8):
            if r.random()<.32:
                pair=start+np.array([0,1]);y[pair]=1-y[pair]
        b = h.astype(float)[:, None] + r.normal(0, .2, (n, 1)); p = r.normal(size=(n, 2))
        return {"y": y, "H": h[:, None].astype(float), "P": p, "B": b, "world": "PRIOR_ONLY"}
    return _common(n, _rng(seed), make, observations_per_group)


def n1_background_key(n=240, seed=20260917, *, observations_per_group=8):
    def make(n, r):
        y = np.arange(n) % 2; b = r.choice([-1., 1.], size=(n, 1))
        p = (2 * y[:, None] - 1) * b + r.normal(0, .15, (n, 1))
        return {"y": y, "H": r.normal(size=(n, 2)), "P": p, "B": b, "world": "BACKGROUND_KEY"}
    return _common(n, _rng(seed), make, observations_per_group)


def n1_additive_noise(n=240, seed=20260917, *, observations_per_group=8):
    def make(n, r):
        y = np.arange(n) % 2; latent = r.normal(size=(n, 1))
        b = latent + r.normal(0, .35, (n, 1)); p = (2 * y[:, None] - 1) + latent + r.normal(0, .5, (n, 1))
        return {"y": y, "H": r.normal(size=(n, 2)), "P": p, "B": b, "world": "ADDITIVE_NOISE"}
    return _common(n, _rng(seed), make, observations_per_group)


def n1_independent_background(n=240, seed=20260917, *, observations_per_group=8):
    def make(n, r):
        y = np.arange(n) % 2; return {"y": y, "H": r.normal(size=(n, 2)), "P": (2*y[:, None]-1)+r.normal(size=(n, 1)), "B": r.normal(size=(n, 1)), "world": "INDEPENDENT_BACKGROUND"}
    return _common(n, _rng(seed), make, observations_per_group)


def _bags(n, k, seed, world, bags_per_group=8):
    if n < 32 or n % 8 or k < 2:
        raise ValueError("n must be a multiple of 8 and at least 32; k at least 2")
    size = _group_size(n, bags_per_group, minimum=2)
    r = _rng(seed); bags = n; group = np.arange(bags) // size; y = np.arange(bags) % 2
    trials = r.normal(size=(bags, k, 2))
    if world == "MEAN_SUFFICIENT":
        trials += (2*y[:, None, None] - 1) * .8
    elif world == "COVARIANCE_SIGNAL":
        trials = r.normal(size=(bags, k, 2)) * np.where(y[:, None, None] == 0, .35, 1.4)
        trials -= trials.mean(axis=1, keepdims=True)
    elif world == "TIME_DRIFT":
        # Outcome-blind generator definition: global time changes the class
        # mixture, while every candidate supports P_bal. Labels are shuffled
        # independently of EEG within each candidate; clipping is not post-hoc
        # rejection or regeneration of an unfavorable random draw.
        time = np.linspace(0, 1, bags)
        y = np.zeros(bags, int)
        for first in range(0, bags, size):
            probability = .2 + .6 * time[first:first + size].mean()
            count = int(np.clip(np.rint(probability * size), 1, size - 1))
            y[first + r.permutation(size)[:count]] = 1
        trials = r.normal(size=(bags, k, 2)) + time[:, None, None] * .1
    else:
        raise ValueError("unknown N2 world")
    h = np.c_[np.full(bags, k), np.linspace(0, 1, bags), np.full(bags,2)]
    tr_g, te_g = _split(len(np.unique(group)), r)
    return {"world": world, "bags": trials, "y": y, "H_BAG": h,
            "candidate_id": np.array([f"synthetic_{i}" for i in group]),
            "group_id": group, "train_mask": np.isin(group, tr_g), "test_mask": np.isin(group, te_g),
            "k": int(k)}


def n2_mean_sufficient(n=40, k=8, seed=20260917, *, bags_per_group=8): return _bags(n, k, seed, "MEAN_SUFFICIENT", bags_per_group)
def n2_covariance_signal(n=40, k=8, seed=20260917, *, bags_per_group=8): return _bags(n, k, seed, "COVARIANCE_SIGNAL", bags_per_group)
def n2_time_drift(n=40, k=8, seed=20260917, *, bags_per_group=8): return _bags(n, k, seed, "TIME_DRIFT", bags_per_group)


def _n3(n, seed, world, observations_per_group=8):
    if n < 32 or n % 8: raise ValueError('n must be a multiple of 8 and at least 32')
    size = _group_size(n, observations_per_group)
    r = _rng(seed); h=np.tile([0,1],n//2);y=h.copy()
    if world == "HISTORY_ONLY": p = h[:, None] + r.normal(0, .2, (n, 1))
    elif world == "EEG_INCREMENT": y = np.arange(n) % 2; p = y[:, None] + r.normal(0, .15, (n, 1)); h = r.integers(0, 2, n)
    elif world == "NEAR_DETERMINISTIC_HISTORY":
        y=h.copy()
        for start in range(0,n,80):y[start:start+2]=1-y[start:start+2]
        p = r.normal(size=(n, 1))
    else: raise ValueError("unknown N3 world")
    group = np.arange(n) // size; b = r.normal(size=(n, 1)); tr_g, te_g = _split(len(np.unique(group)), r)
    return {"world": world, "y": y, "H": h[:, None].astype(float), "P": p, "B": b,
            "candidate_id": np.array([f"synthetic_{i}" for i in group]), "group_id": group,
            "train_mask": np.isin(group, tr_g), "test_mask": np.isin(group, te_g)}


def n3_history_only(n=240, seed=20260917, *, observations_per_group=8): return _n3(n, seed, "HISTORY_ONLY", observations_per_group)
def n3_eeg_increment(n=240, seed=20260917, *, observations_per_group=8): return _n3(n, seed, "EEG_INCREMENT", observations_per_group)
def n3_near_deterministic_history(n=240, seed=20260917, *, observations_per_group=8): return _n3(n, seed, "NEAR_DETERMINISTIC_HISTORY", observations_per_group)


N1_WORLDS = {"PRIOR_ONLY": n1_prior_only, "BACKGROUND_KEY": n1_background_key, "ADDITIVE_NOISE": n1_additive_noise, "INDEPENDENT_BACKGROUND": n1_independent_background}
N2_WORLDS = {"MEAN_SUFFICIENT": n2_mean_sufficient, "COVARIANCE_SIGNAL": n2_covariance_signal, "TIME_DRIFT": n2_time_drift}
N3_WORLDS = {"HISTORY_ONLY": n3_history_only, "EEG_INCREMENT": n3_eeg_increment, "NEAR_DETERMINISTIC_HISTORY": n3_near_deterministic_history}
