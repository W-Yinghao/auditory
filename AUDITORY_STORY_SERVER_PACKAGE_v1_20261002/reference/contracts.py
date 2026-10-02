"""Minimal provenance contracts; these do not certify an entire server pipeline."""
from __future__ import annotations
from contextlib import contextmanager
from collections.abc import Iterable, Mapping
import numpy as np


def check_scopes(*, outer_train: Iterable[str], outer_test: Iterable[str],
                 encoder_train: Iterable[str], transform_fit: Iterable[str],
                 profile_fit: Iterable[str], label_train: Iterable[str],
                 label_budget: int | None=None) -> None:
    tr,te=set(outer_train),set(outer_test)
    if not tr or not te or tr & te:
        raise ValueError("Empty or overlapping outer identity scopes.")
    enc=set(encoder_train)
    if enc & te:
        raise ValueError("The upstream encoder saw outer test identities.")
    for name,ids in [('transform',transform_fit),('profile',profile_fit),('clinical',label_train)]:
        ids=set(ids)
        if not ids <= tr or ids & te:
            raise ValueError(f"Invalid {name} fitting identities.")
    if label_budget is not None and len(set(label_train)) != label_budget:
        raise ValueError("The declared label budget does not match actual identities.")


def redact_targets(targets: Mapping[str,np.ndarray], visible_mask: np.ndarray) -> dict[str,np.ndarray]:
    visible_mask=np.asarray(visible_mask)
    if visible_mask.ndim != 1 or visible_mask.dtype != bool:
        raise ValueError("visible_mask must be a boolean vector.")
    out={}
    for key,value in targets.items():
        arr=np.asarray(value,dtype=float)
        if arr.shape != visible_mask.shape:
            raise ValueError(f"Target {key} has an incompatible shape.")
        out[key]=np.where(visible_mask,arr,np.nan)
    return out


@contextmanager
def temporary_eval(model):
    """Restore exact submodule train/eval states, including on exceptions."""
    states={m:m.training for m in model.modules()}
    model.eval()
    try:
        yield model
    finally:
        for m,state in states.items():
            m.training=state
