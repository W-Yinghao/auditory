"""Metadata-only reconstruction of the frozen prior33 evaluator query identities.

No EEG is loaded or fitted. Public views use the unmodified target_view metadata
builder, temporarily omitting only its EEG-array materialisation. Private trials
use the exact accepted/history-known mask in hc.load_children. Sensitive raw
event indices are saved only in the project-private /projects ledger.
"""
from __future__ import annotations

import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..prior33 import views as V, sampler as SM, target_train as T
from . import ap_wrong as W
from .ap_wrong_sampler import PairSampler


def private_metadata():
    from auditory_c3 import private_mi as PM, private_mi2 as PM2
    from auditory_c3.c3dl import hc
    rec, bank = PM.lane_bank("bdf_puretone", accepted_only=True)
    records_path = Path(PM.P) / "auditory_pf/prepare_002/records.csv"
    children_path = Path(PM.P) / "auditory_pf/prepare_002/children.csv"
    records, children = pd.read_csv(records_path), pd.read_csv(children_path)
    assert list(rec.record_id) == list(records.record_id)
    history = PM2.hist_codes(bank["pc"], bank["prl"])
    kids, sources = [], {str(records_path): W.sha(records_path), str(children_path): W.sha(children_path)}
    for _, child in children.iterrows():
        group = "HA" if child.group == "labelled" and bool(child.eligible) else (
            "NH" if child.group == "nh" and bool(child.nh_eligible) else None)
        if group is None:
            continue
        rid = records.record_id[int(child.primary_rec)]
        path = Path(PM.P) / "auditory_gx/GX_stage_001/epochs" / f"{rid}.npz"
        source_sha = W.sha(path)
        sources[str(path)] = source_sha
        mask = bank["rec"] == int(child.primary_rec)
        with np.load(path, allow_pickle=False) as source:
            accepted = source["accepted"].astype(bool)
            original_indices = np.flatnonzero(accepted)
            block = source["block_id"][accepted]
            labels = source["y"][accepted]
        if len(original_indices) != int(mask.sum()) or not np.array_equal(labels, bank["y"][mask]):
            raise ValueError("private accepted index order differs from the original loader")
        known = history["since_last_deviant"][mask] >= 0
        indices, labels, block = original_indices[known], labels[known], block[known]
        blocks = np.unique(block)
        es_blocks = set(blocks[int(np.floor(.8 * len(blocks))):].tolist()) if len(blocks) >= 3 else set()
        kids.append({"id": f"child{int(child.child)}", "group": group, "y": labels,
                     "block": block, "es_mask": np.isin(block, list(es_blocks)),
                     "query_ids": ["private-trial:" + W.digest({"source_sha256": source_sha, "epoch_index": int(i)})
                                   for i in indices],
                     "source_npz": str(path), "source_npz_sha256": source_sha,
                     "original_epoch_indices": indices.tolist()})
    folds = hc.folds(kids)
    for child in kids:
        child["fold"] = folds[child["id"]]
    return kids, sources


def donor_people(manifest, dataset):
    sampler = PairSampler(manifest, dataset, 3401, "cpu", revised=True, metadata_only=True)
    fit = {f"{stratum.cohort}:{pid}" for stratum in sampler._strata for pid in stratum.participants}
    selection = SM.selection_sets(manifest)
    fit.update("sparrkulee:" + str(pid) for pid in selection["fit"].participant)
    dev = {"sparrkulee:" + str(pid) for pid in selection["dev"]["queries"].participant}
    return sorted(fit), sorted(dev)


def public_views(manifest, dataset):
    """Build exactly the actual public segment/candidate metadata, without EEG."""
    views = {}
    original = V._load_eeg_cm
    V._load_eeg_cm = lambda *args, **kwargs: None
    try:
        for cf in (0, 1):
            cohort = V.target_view(dataset, cf, manifest, T.INPUT_MODE)
            _, candidates = V.pool_of(cohort, "test", "ss")
            candidate_ids = ["audio:" + W.digest({key: row[key] for key in ("uid", "s0", "presentation", "family", "fs0")})
                             for row in candidates]
            queries = {}
            for p, person in enumerate(cohort.participants):
                selected = [row for row in cohort.segments if row["p"] == p and row["role"] == "test" and row["kind"] == "ss"]
                order = np.argsort([row["e0"] for row in selected])
                selected = [selected[int(i)] for i in order]
                ids = ["eeg-query:" + W.digest({"dataset": dataset, "person": person["id"],
                                              **{key: row[key] for key in ("e0", "s0", "uid", "piece", "s", "presentation")}})
                       for row in selected]
                if len(ids) != len(set(ids)):
                    raise ValueError("duplicate physical public query identifiers")
                queries[str(person["id"])] = {"group": str(person["group"]), "fold": person.get("fold"),
                                              "test_only": bool(person.get("test_only")), "query_ids": ids}
            views[cf] = {"view": {key: cohort.meta.get(key) for key in (
                "view_sha256", "pool_sha256", "content_sha256", "manifest_sha256", "mode", "cache", "contract",
                "n_segments", "n_participants", "n_segments_meeting_shared_audio")},
                         "candidate_ids": candidate_ids, "candidate_order_sha256": W.digest(candidate_ids), "people": queries}
            del cohort
            gc.collect()
    finally:
        V._load_eeg_cm = original
    return views


def make_ledger(plan):
    templates = [unit for unit in plan["units"] if unit["stage"] == "target" and unit["arm"] == "AP"]
    manifest = V.open_for_row(templates[0]["source_template"])
    kids, private_sources = private_metadata()
    by_id = {child["id"]: child for child in kids}
    ledger = {"version": "ALN35_APWRONG_QUERIES_v2", "manifest_sha256": manifest.sha256, "cells": {},
              "source_files": private_sources, "expected": {}, "required_folds": {},
              "provenance_level": "deterministic reconstruction from exact frozen evaluator source and bound input metadata",
              "historical_limit": "legacy S records lack runtime query IDs; their stored view/cell/code provenance is checked against this reconstruction, not relabeled as runtime capture"}
    for dataset in ("dtu", "fau", "private_bdf"):
        fit_donor, dev_donor = donor_people(manifest, dataset)
        pv = public_views(manifest, dataset) if dataset != "private_bdf" else None
        expected, required = {}, {}
        for unit in [item for item in templates if item["dataset"] == dataset]:
            row = unit["adapter_row"]
            sf, cf = row["subject_fold"], row["content_fold"]
            cell = V.manifest_cell(manifest, dataset, sf, cf)
            target_ids = sorted(set(map(str, cell["test"])) | set(map(str, cell.get("test_only", []))))
            fold_name = "evaluation" if dataset == "private_bdf" else f"content_{cf}"
            target_train = sorted(f"{dataset}:{pid}" for pid in cell["train"])
            if dataset == "private_bdf":
                T._private_cell(kids, cell, sf)
                view = T._private_view(kids, sf)
                # Query indexing is independent of the host's numerical filter
                # redesign. Bind the recorded input view to the frozen filter
                # bytes in the manifest, not coefficients recomputed on this CPU.
                filters = manifest["filters"]
                local_view_sha = view["view_sha256"]
                view["view_sha256"] = T._sha_json({"pool": view["pool_sha256"],
                    "lp20_sos": filters["lp20_sos"], "aa_fir_250": filters["aa_fir_250"],
                    "contract": T.C.CONTRACT})
                if sf == 0:
                    print(json.dumps({"private_view_binding": "frozen manifest filters", "cpu_redesign_view_sha256": local_view_sha,
                                      "frozen_filter_view_sha256": view["view_sha256"]}), flush=True)
                candidates = ["class:0", "class:1"]
            else:
                view, candidates = pv[cf]["view"], pv[cf]["candidate_ids"]
            people = {}
            for pid in target_ids:
                person = by_id[pid] if dataset == "private_bdf" else pv[cf]["people"][pid]
                if person["fold"] != sf and not person.get("test_only"):
                    raise ValueError("manifest target roster conflicts with evaluator outer assignment")
                identity, group = f"{dataset}:{pid}", person["group"]
                if identity in expected and expected[identity] != group:
                    raise ValueError("identity group changes across required content folds")
                expected[identity] = group
                required.setdefault(identity, []).append(fold_name)
                qids = person["query_ids"]
                people[pid] = {"identity": identity, "group": group, "query_ids": qids,
                               "query_order_sha256": W.digest(qids),
                               "query_set_id": W.digest({"query_ids": qids, "candidate_ids": candidates,
                                                         "target_contract": row["spec"]["target_contract"]})}
            ledger["cells"][f"{dataset}|{sf}|{cf}"] = {"dataset": dataset, "subject_fold": sf, "content_fold": cf,
                "fold_name": fold_name, "view": view, "manifest_cell": cell, "people": people,
                "candidate_ids": candidates, "candidate_order_sha256": W.digest(candidates),
                "target_fit": target_train, "target_selection": target_train,
                "donor_fit": fit_donor, "donor_selection": dev_donor}
        ledger["expected"][dataset] = expected
        ledger["required_folds"][dataset] = {pid: sorted(set(folds)) for pid, folds in required.items()}
        expected_count = {"dtu": 44, "fau": 67, "private_bdf": 64}[dataset]
        if len(expected) != expected_count:
            raise ValueError(f"frozen roster changed: {dataset} {len(expected)} vs {expected_count}")
        print(json.dumps({"query_ledger_dataset": dataset, "expected_people": len(expected)}), flush=True)
    return ledger


def check_record(record, cell, dataset):
    """Bind a result to explicit ordered query/candidate IDs, never counts alone."""
    if record["view"] != cell["view"]:
        differences = {key: [record["view"].get(key), cell["view"].get(key)]
                       for key in set(record["view"]) | set(cell["view"])
                       if record["view"].get(key) != cell["view"].get(key)}
        raise ValueError(f"{dataset} sf{cell['subject_fold']} cf{cell['content_fold']}: result view hashes do not bind reconstructed IDs: {differences}")
    recorded = record["cell"]
    manifest = cell["manifest_cell"]
    for key in ("dataset", "subject_fold", "content_fold", "split_hash"):
        if recorded.get(key) != manifest.get(key):
            raise ValueError(f"result cell differs from frozen roster: {key}")
    pp = record["eval"]["per_participant"]
    queried = {pid: person for pid, person in cell["people"].items() if person["query_ids"]}
    if set(pp) != set(queried):
        raise ValueError("result identities differ from reconstructed actual evaluator queries")
    for pid, person in queried.items():
        result = pp[pid]
        if result["group"] != person["group"]:
            raise ValueError("group differs from metadata roster")
        n = result.get("n") if dataset == "private_bdf" else result["unified/regular"]["n_queries"]
        if n != len(person["query_ids"]):
            raise ValueError("result count does not match explicit query IDs")
        if dataset != "private_bdf" and result["unified/regular"]["n_candidates"] != len(cell["candidate_ids"]):
            raise ValueError("result candidate count does not match explicit ordered candidate IDs")
    return queried
