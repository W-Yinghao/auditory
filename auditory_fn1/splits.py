"""Identity-level five-outer / three-inner splitting (plan section 9).

Balancing uses identity and eligibility metadata only. Target values and any previous
out-of-fold score are deliberately not visible here: the split is made once, with the
frozen seed, and is not re-drawn until a support rule passes.
"""
from __future__ import annotations

import hashlib
import json
from typing import Sequence

import numpy as np


class SupportError(RuntimeError):
    """Raised when the frozen design cannot be satisfied by the available identities."""


def _ordering(identities: Sequence[str], seed: int) -> list[str]:
    """Deterministic identity order that does not depend on input row order.

    Keyed by sha256(seed|identity) rather than PYTHONHASHSEED-dependent set order,
    so two processes produce the same folds.
    """
    return sorted(identities, key=lambda g: hashlib.sha256(f"{seed}|{g}".encode()).hexdigest())


def make_splits(identities: Sequence[str], *, outer_folds: int, inner_folds: int, seed: int,
                minimums: dict) -> dict:
    groups = [str(g) for g in identities]
    if len(set(groups)) != len(groups):
        raise SupportError("DUPLICATE_IDENTITY_IN_SPLIT_INPUT")
    total = len(groups)
    if total < int(minimums["min_total_groups"]):
        raise SupportError(f"DESIGN_SUPPORT_INSUFFICIENT:total={total}<{minimums['min_total_groups']}")
    ordered = _ordering(groups, seed)
    # Round-robin over the deterministic order keeps outer folds within one of each
    # other in size without consulting any outcome.
    outer: list[list[str]] = [[] for _ in range(outer_folds)]
    for index, group in enumerate(ordered):
        outer[index % outer_folds].append(group)
    folds = []
    for number, test in enumerate(outer):
        train = [g for g in ordered if g not in set(test)]
        if len(test) < int(minimums["min_outer_test_groups"]):
            raise SupportError(f"DESIGN_SUPPORT_INSUFFICIENT:outer_test[{number}]={len(test)}")
        if len(train) < int(minimums["min_outer_train_groups"]):
            raise SupportError(f"DESIGN_SUPPORT_INSUFFICIENT:outer_train[{number}]={len(train)}")
        inner: list[list[str]] = [[] for _ in range(inner_folds)]
        for index, group in enumerate(train):
            inner[index % inner_folds].append(group)
        inner_spec = []
        for inner_number, validation in enumerate(inner):
            inner_train = [g for g in train if g not in set(validation)]
            if len(inner_train) < int(minimums["min_inner_train_groups"]):
                raise SupportError(f"DESIGN_SUPPORT_INSUFFICIENT:inner_train[{number}/{inner_number}]={len(inner_train)}")
            inner_spec.append({"inner_fold": inner_number, "train": inner_train, "validation": validation})
        folds.append({"outer_fold": number, "train": train, "test": sorted(test), "inner": inner_spec})
    spec = {"seed": int(seed), "identities": ordered, "n_identities": total,
            "outer_folds": int(outer_folds), "inner_folds": int(inner_folds), "folds": folds}
    validate_splits(spec)
    return spec


def validate_splits(spec: dict) -> None:
    """Independent re-check of the invariants, run on every produced or loaded split."""
    universe = set(spec["identities"])
    if len(universe) != spec["n_identities"]:
        raise SupportError("SPLIT_IDENTITY_COUNT_MISMATCH")
    seen_test: set[str] = set()
    for fold in spec["folds"]:
        train, test = set(fold["train"]), set(fold["test"])
        if train & test:
            raise SupportError(f"OUTER_FOLD_LEAKAGE:{fold['outer_fold']}")
        if train | test != universe:
            raise SupportError(f"OUTER_FOLD_NOT_PARTITION:{fold['outer_fold']}")
        if seen_test & test:
            raise SupportError(f"IDENTITY_TESTED_TWICE:{fold['outer_fold']}")
        seen_test |= test
        inner_union: set[str] = set()
        for inner in fold["inner"]:
            itrain, ival = set(inner["train"]), set(inner["validation"])
            if itrain & ival:
                raise SupportError(f"INNER_FOLD_LEAKAGE:{fold['outer_fold']}/{inner['inner_fold']}")
            if itrain | ival != train:
                raise SupportError(f"INNER_FOLD_NOT_PARTITION_OF_TRAIN:{fold['outer_fold']}/{inner['inner_fold']}")
            if ival & test:
                raise SupportError(f"INNER_VALIDATION_TOUCHES_OUTER_TEST:{fold['outer_fold']}/{inner['inner_fold']}")
            if inner_union & ival:
                raise SupportError(f"INNER_VALIDATION_OVERLAP:{fold['outer_fold']}/{inner['inner_fold']}")
            inner_union |= ival
        if inner_union != train:
            raise SupportError(f"INNER_VALIDATION_DOES_NOT_COVER_TRAIN:{fold['outer_fold']}")
    if seen_test != universe:
        raise SupportError("OUTER_TEST_DOES_NOT_COVER_UNIVERSE")


def fingerprint(spec: dict) -> str:
    payload = json.dumps({"seed": spec["seed"], "folds": [[f["outer_fold"], f["test"]] for f in spec["folds"]]},
                         sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()
