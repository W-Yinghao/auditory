"""Deterministic spatially-spread electrode subsets for the channel-budget curve."""
from __future__ import annotations

import numpy as np


def farthest_point_subset(positions: np.ndarray, budget: int, start: int) -> np.ndarray:
    """Greedy farthest-point sampling: a B-electrode montage that covers the scalp.

    Using a spread subset rather than a random one is what makes the budget curve a
    statement about electrode COUNT instead of a statement about luck in coverage.
    """
    positions = np.asarray(positions, dtype=float)
    n = positions.shape[0]
    if not 1 <= budget <= n:
        raise ValueError(f"D2_BUDGET_OUT_OF_RANGE:{budget}:{n}")
    chosen = [int(start) % n]
    distance = np.linalg.norm(positions - positions[chosen[0]], axis=1)
    while len(chosen) < budget:
        nxt = int(np.argmax(distance))
        chosen.append(nxt)
        distance = np.minimum(distance, np.linalg.norm(positions - positions[nxt], axis=1))
    return np.array(sorted(chosen), dtype=int)


def subset_variants(positions: np.ndarray, budget: int, variants: int,
                    seed: int = 20260919) -> list[np.ndarray]:
    """Several spread subsets of the same size, from different greedy seeds."""
    rng = np.random.default_rng(seed + budget)
    starts = rng.choice(positions.shape[0], size=variants, replace=False)
    return [farthest_point_subset(positions, budget, int(s)) for s in starts]


def coverage(positions: np.ndarray, subset: np.ndarray) -> dict:
    """How well a subset covers the array: the worst distance from any electrode to it."""
    picked = positions[subset]
    distances = np.linalg.norm(positions[:, None, :] - picked[None, :, :], axis=-1).min(axis=1)
    return {"max_distance_m": float(distances.max()), "mean_distance_m": float(distances.mean())}
