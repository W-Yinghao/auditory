from types import SimpleNamespace

import numpy as np
import torch

from auditory_alignment_v3.aln34 import data_inner as D


def fixture():
    people = [{"id": f"p{f}_{g}_{i}", "fold": f, "group": g, "dev": False}
              for f in range(5) for g in ("nh", "hi") for i in range(2)]
    segs = [{"p": p, "role": role, "kind": "ss", "uid": f"{role}{j}@0", "part": f"{role}{j}",
             "e0": k*64, "s0": k*64} for k, (p, role, j) in enumerate(
                 (p, role, j) for p in range(len(people)) for role in ("fit", "es", "test") for j in range(8))]
    return SimpleNamespace(participants=people, segments=segs)


def test_nested_people_groups_and_outer_exclusion():
    m = D.metadata(fixture())
    small = D.selection(m, 0, 0, "people", .25)
    large = D.selection(m, 0, 0, "people", .5)
    assert set(small["train_ids"]) < set(large["train_ids"])
    assert not set(small["train_ids"]) & set(small["outer_ids"])
    assert {p["group"] for p in m["participants"] if p["id"] in small["train_ids"]} == {"nh", "hi"}
    assert len(small["train_ids"]) == 4


def test_content_group_nesting_keeps_es_and_never_test():
    m = D.metadata(fixture())
    a, b = [D.selection(m, 1, 0, "content", f) for f in (.25, .5)]
    assert set(a["content_groups"]) < set(b["content_groups"])
    assert a["es_indices"] == b["es_indices"]
    assert set(a["fit_indices"]) < set(b["fit_indices"])
    assert all(m["segments"][i]["role"] == "fit" for i in a["fit_indices"])
    assert {m["segments"][i]["part"] for i in a["fit_indices"]} == set(a["content_groups"])


def test_inner_view_excludes_both_person_sets_and_test_content():
    c = fixture()
    s = D.selection(D.metadata(c), 0, 0, "inner_person", 1)
    assert not set(s["train_ids"]) & (set(s["inner_ids"]) | set(s["outer_ids"]))
    v = D.evaluation_view(c, s)
    queries = [x for x in v.segments if x["role"] == "test"]
    assert queries
    assert {c.participants[x["p"]]["id"] for x in queries} == set(s["inner_ids"])
    assert all(x["part"].startswith("es") for x in queries)
    assert all(v.segments[i]["role"] != "test" for i, x in enumerate(c.segments) if x["role"] == "test")
    assert all(x["role"] == "es" for x in c.segments if x["part"].startswith("es")), "input not mutated"


def test_batcher_masks_removed_content_and_retains_common_audio_basis():
    from auditory_alignment_v2 import train as T
    from auditory_alignment_v3 import core, local_train
    c = fixture()
    c.fs, c.meta, c.n_ch = 128, {"dataset": "dtu", "seg_len": 64}, 2
    n = len(c.segments)*64+256
    c.eeg = np.zeros((2, n), np.float32)
    c.stim = {"Ac": np.zeros((2, n), np.float32)}
    meta = D.metadata(c)
    split = D.selection(meta, 0, 0, "content", .25)
    row = {"experiment_id": "test", "family_id": "ALN34_SPLIT_LOCAL", "subject_fold": 0, "content_fold": 0,
           "spec": {"split_key": "x"}}
    plan = {"splits": {"x": split}, "metadata_sha256": {"0": D.hashlib.sha256(D.B.dumps(meta).encode()).hexdigest()}}
    spec = {"architecture": "lag_local_tokens", "window": "full", "target": "Ac"}
    old_init, old_stats = T.Batcher.__init__, local_train.target_stats
    with D.instrumentation(row, plan, 2):
        bt = T.Batcher(c, spec, row, torch.device("cpu"))
        assert bt.fit == split["fit_indices"]
        assert len(bt._aln34_target_fit) == 4*len(bt.fit)
        visible = [i for i, x in enumerate(c.segments) if x["p"] in bt.train_p and x["role"] == "fit"]
        assert visible == split["fit_indices"], "discarded fitting EEG must not re-enter through readouts"
        mu, sd = local_train.target_stats(bt, np.random.default_rng(0))
        assert np.isfinite(mu).all() and np.isfinite(sd).all()
        assert bt.fit == split["fit_indices"], "target-statistics hook must restore reduced training set"
    assert T.Batcher.__init__ is old_init and local_train.target_stats is old_stats
