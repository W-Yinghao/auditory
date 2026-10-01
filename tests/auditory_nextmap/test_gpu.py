"""G1 / G2 building blocks: sub-average groups, evaluation chunks, joint identity folds, per-lane splits (CPU tensors)."""
import numpy as np
import pytest
import torch

from auditory_nextmap import gpu_age as ga
from auditory_nextmap import gpu_share as gs


class _Co:
    def __init__(self):
        self.t_record = np.array([0, 0, 0, 0, 1, 1, 1, 0, 1, 1])
        self.t_y = np.array([0, 1, 0, 1, 0, 0, 1, 0, 1, 0])


def test_subaverage_partners_stay_in_record_and_class():
    co = _Co()
    g = ga.Groups(co, "cpu")
    gen = torch.Generator().manual_seed(0)
    sel = torch.arange(10)
    for _ in range(20):
        p = g.partners(sel, 2, gen).numpy()
        for i in range(10):
            assert all(co.t_record[j] == co.t_record[i] and co.t_y[j] == co.t_y[i] for j in p[i])
    # a group of three trials sampled with m = 3 returns three distinct members
    p3 = g.partners(torch.tensor([0]), 3, gen).numpy()[0]
    assert sorted(p3) == [0, 2, 7]


def test_evaluation_chunks_are_disjoint_and_exact():
    idx = np.arange(80) * 3
    ch = ga.chunks(idx, 20)
    assert len(ch) == 4 and all(len(c) == 20 for c in ch)
    assert len(np.unique(np.concatenate(ch))) == 80
    assert len(ga.chunks(np.arange(45), 20)) == 2          # trailing remainder dropped, never padded


def test_joint_folds_keep_identity_groups_on_one_side():
    groups = [f"g{i}" for i in range(23)]
    f = gs.make_folds(groups, 701, 5, 0.15)
    assert sorted(f["outer"]) == sorted(groups) and set(f["outer"].values()) == set(range(5))
    for k in range(5):
        assert not (set(f["val"][k]) & {g for g, v in f["outer"].items() if v == k})
    assert f == gs.make_folds(groups, 701, 5, 0.15)        # deterministic


def test_split_indices_by_group_across_lanes():
    class Lane:
        def __init__(self, ids, child):
            self.child_ids, self.child = ids, np.array(child)
    lanes = {"a": Lane(["g1", "g2", "g3"], [0, 0, 1, 2, 2]), "b": Lane(["g2", "g4"], [0, 1, 1])}
    folds = {"outer": {"g1": 0, "g2": 1, "g3": 0, "g4": 0}, "val": {1: ["g3"]}}
    sp = gs.split_indices(lanes, folds, 1)
    assert sp["a"]["test"].tolist() == [2] and sp["b"]["test"].tolist() == [0]        # g2 is test in BOTH lanes
    assert sp["a"]["val"].tolist() == [3, 4] and sp["a"]["train"].tolist() == [0, 1]
    assert sp["b"]["train"].tolist() == [1, 2]
