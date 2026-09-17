"""Outcome-blind donor selection for N1 context mismatch diagnostics."""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd


BASE = {"trial_id", "candidate_id", "record_id", "segment_id", "onset_sample", "split_group_id",
        "previous_code", "previous_run_bin", "previous_gap_s", "layout_id",
        "raw_dependency_start", "raw_dependency_end"}


def _tie(seed, query, donor):
    return hashlib.sha256(f"{seed}|{query}|{donor}".encode()).hexdigest()


def _check(frame: pd.DataFrame, name: str):
    if not isinstance(frame, pd.DataFrame) or not BASE.issubset(frame.columns):
        raise ValueError(f"N1_DONOR_SCHEMA:{name}")
    if frame[list(BASE - {"previous_gap_s"})].isna().any().any():
        raise ValueError(f"N1_DONOR_NULL:{name}")
    if frame.trial_id.duplicated().any():
        raise ValueError("N1_DONOR_DUPLICATE_TRIAL")
    for col in ("raw_dependency_start", "raw_dependency_end"):
        values = pd.to_numeric(frame[col], errors="coerce").to_numpy(float)
        if not np.isfinite(values).all():
            raise ValueError("N1_DONOR_DEPENDENCY_INTERVAL")
    if (frame.raw_dependency_end.to_numpy(float) <= frame.raw_dependency_start.to_numpy(float)).any():
        raise ValueError("N1_DONOR_DEPENDENCY_INTERVAL")


def _same_history(query, pool):
    columns = ("previous_code", "previous_run_bin", "layout_id")
    mask = np.ones(len(pool), dtype=bool)
    for col in columns:
        if pd.isna(query[col]):
            mask &= pool[col].isna().to_numpy()
        else:
            mask &= pool[col].astype(object).to_numpy() == query[col]
    qgap = query["previous_gap_s"]
    if pd.isna(qgap):
        mask &= pool["previous_gap_s"].isna().to_numpy()
    else:
        mask &= pd.to_numeric(pool["previous_gap_s"], errors="coerce").notna().to_numpy()
    return mask


def select_donors(queries: pd.DataFrame, pool: pd.DataFrame, *, role: str,
                  seed: int = 20260917,
                  min_dependency_separation_seconds: float = 0.0):
    """Select deterministic pre donors and preserve all legal alternatives.

    ``role='same_child_remote'`` permits an earlier legal row from the same
    record (or a remote row) for the same candidate. ``role='training_remote'`` requires a pool row with
    ``is_training=True`` and a different candidate. Matching uses only past-H,
    layout, and gap fields. Current stimulus labels, predictions, clinical
    values, and identity strings never enter the matching key.
    """
    _check(queries, "queries")
    _check(pool, "pool")
    if role not in {"same_child_remote", "training_remote"}:
        raise ValueError("N1_DONOR_ROLE")
    if min_dependency_separation_seconds < 0 or not np.isfinite(float(min_dependency_separation_seconds)):
        raise ValueError("N1_DONOR_GAP")
    outputs, alternatives = [], []
    for _, query in queries.iterrows():
        mask = _same_history(query, pool)
        mask &= pool.trial_id.astype(str).to_numpy() != str(query.trial_id)
        if role == "same_child_remote":
            mask &= pool.candidate_id.astype(str).to_numpy() == str(query.candidate_id)
        else:
            if "is_training" not in pool:
                raise ValueError("N1_DONOR_TRAINING_FLAG")
            mask &= pool.is_training.fillna(False).to_numpy(bool)
            mask &= pool.candidate_id.astype(str).to_numpy() != str(query.candidate_id)
            mask &= pool.split_group_id.astype(str).to_numpy() != str(query.split_group_id)
        # A same-record pre donor must precede the query.  Remote records have
        # no shared clock and are therefore not ordered by their numeric time.
        same_physical = ((pool.record_id.astype(str).to_numpy() == str(query.record_id)) &
                         (pool.segment_id.astype(str).to_numpy() == str(query.segment_id)))
        mask &= (~same_physical | (pool.onset_sample.to_numpy(float) < float(query.onset_sample)))
        # Remove raw dependency overlap before any gap-distance ranking so a
        # nearer but illegal donor cannot suppress a legal alternative.
        qstart, qend = float(query.raw_dependency_start), float(query.raw_dependency_end)
        candidate = pool.loc[mask].copy()
        candidate = candidate.loc[~((candidate.raw_dependency_start.to_numpy(float) < qend) &
                                    (candidate.raw_dependency_end.to_numpy(float) > qstart) &
                                    (candidate.record_id.astype(str).to_numpy() == str(query.record_id)) &
                                    (candidate.segment_id.astype(str).to_numpy() == str(query.segment_id)))]
        had_overlap_legal = not candidate.empty
        if min_dependency_separation_seconds:
            same_candidate_physical = ((candidate.record_id.astype(str).to_numpy() == str(query.record_id)) &
                                       (candidate.segment_id.astype(str).to_numpy() == str(query.segment_id)))
            before = np.maximum(qstart - candidate.raw_dependency_end.to_numpy(float), 0.0)
            after = np.maximum(candidate.raw_dependency_start.to_numpy(float) - qend, 0.0)
            separation = np.maximum(before, after)
            candidate = candidate.loc[(~same_candidate_physical) |
                                      (separation >= min_dependency_separation_seconds)]
        if candidate.empty:
            outputs.append(dict(query_trial_id=str(query.trial_id), donor_trial_id=None,
                                donor_status=("DEPENDENCY_OVERLAP" if not had_overlap_legal else "NO_LEGAL_DONOR"),
                                n_candidates=0,
                                donor_options=[]))
            continue
        qgap = pd.to_numeric(pd.Series([query.previous_gap_s]), errors="coerce").iloc[0]
        if np.isfinite(qgap):
            distances = (pd.to_numeric(candidate.previous_gap_s, errors="coerce") - qgap).abs()
        else:
            distances = pd.Series(0.0, index=candidate.index)
        candidate = candidate.assign(_gap_distance=distances)
        candidate = candidate.assign(_same_record=candidate.record_id.astype(str).eq(str(query.record_id)) &
                                     candidate.segment_id.astype(str).eq(str(query.segment_id)),
                                     _tie=[_tie(seed, query.trial_id, value)
                                           for value in candidate.trial_id.astype(str)])
        candidate["_earlier_order"] = np.where(
            candidate._same_record.to_numpy(bool), -candidate.onset_sample.to_numpy(float), 0.0)
        candidate = candidate.sort_values(["_same_record", "_earlier_order", "_gap_distance", "_tie"],
                                          ascending=[False, True, True, True], kind="stable")
        if candidate.empty:
            outputs.append(dict(query_trial_id=str(query.trial_id), donor_trial_id=None,
                                donor_status="DEPENDENCY_OVERLAP", n_candidates=0,
                                donor_options=[]))
            continue
        order = list(candidate.index)
        chosen = candidate.loc[order[0]]
        options = [str(candidate.at[i, "trial_id"]) for i in order]
        status = "UNIQUE" if len(options) == 1 else "AMBIGUOUS_ALTERNATIVES"
        outputs.append(dict(query_trial_id=str(query.trial_id), donor_trial_id=str(chosen.trial_id),
                            donor_status=status, n_candidates=len(options), donor_options=options,
                            donor_record_id=str(chosen.record_id), donor_candidate_id=str(chosen.candidate_id)))
        alternatives.extend(dict(query_trial_id=str(query.trial_id), donor_trial_id=str(candidate.at[i, "trial_id"]),
                                 rank=int(rank), donor_status=status)
                            for rank, i in enumerate(order, 1))
    return pd.DataFrame(outputs), pd.DataFrame(alternatives)


build_donor_map = select_donors
choose_donors = select_donors
