"""Read-only adapters onto earlier rounds (nothing here writes).

PF2 cohort and single-encoder exports (A package), PF spectral features, PF round-1 cohort and H14 errors (C0),
GX staged epochs, D1 BDF arrays and ST1 event tables (A1).
"""
from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path

import numpy as np
import pandas as pd

from auditory_pf.cohort import Cohort
from auditory_pf.runtime import load_config as pf_load_config

from .runtime import ROOT, ProvenanceError, cfg

AGG_SHAPE_TAIL = (10, 2, 192)       # [records, draws, classes, embedding]; class 0 = standard ('1'), 1 = deviant ('2')


def pf_config(config: dict, *, round1: bool = False) -> dict:
    return pf_load_config(cfg(config, "sources.pf_config_round1" if round1 else "sources.pf_config"))


def units(config: dict) -> list[tuple[int, int]]:
    return [(int(s), int(k)) for s in cfg(config, "age.outer_seeds") for k in range(int(cfg(config, "age.outer_folds")))]


class AgeSource:
    """PF2 cohort + stim_002 single-encoder exports + D2 spectra + technical summaries, keyed by PF2 child index."""

    def __init__(self, config: dict):
        self.config = config
        self.pfc = pf_config(config)
        self.co = Cohort(self.pfc, cfg(config, "sources.pf_prepare_run"))
        if [int(s) for s in self.co.seeds] != [int(s) for s in cfg(config, "age.outer_seeds")]:
            raise ProvenanceError("PF2_SEEDS_DIFFER_FROM_CONFIG")
        self.stim_dir = ROOT / "private/auditory_pf" / cfg(config, "sources.pf_stim_run")
        self.ch = self.co.ch.set_index("child")
        self.rec = self.co.rec.set_index("rec")
        self._exports: dict = {}

    # ------------------------------------------------------------------ cohort
    @cached_property
    def main_children(self) -> list[int]:
        """Primary group (labelled HA) with fixed-budget draws and a finite age on the primary record."""
        ch = self.co.ch
        out = []
        for c in sorted(ch[ch.group == cfg(self.config, "age.primary_group")].child.astype(int)):
            r = self.primary(c)
            if r in self.co.draw_row and np.isfinite(self.rec.loc[r, "age_months"]):
                out.append(c)
        return out

    def primary(self, child: int) -> int:
        return int(self.ch.loc[int(child), "primary_rec"])

    def age(self, child: int) -> float:
        return float(self.rec.loc[self.primary(child), "age_months"])

    def outer(self, seed: int) -> dict[int, int]:
        return self.co.outer(seed)

    # ------------------------------------------------------------------ exports (single encoder M_o per unit)
    def exports(self, seed: int, fold: int) -> dict:
        key = (int(seed), int(fold))
        if key not in self._exports:
            path = self.stim_dir / f"unit_s{seed}_k{fold}" / "exports.npz"
            with np.load(path, allow_pickle=False) as z:
                out = {n: z[n] for n in ("agg_base", "test_children", "train_children", "agg_source")}
            if tuple(out["agg_base"].shape[1:]) != AGG_SHAPE_TAIL or out["agg_base"].shape[0] != len(self.co.rec):
                raise ProvenanceError(f"AGG_SHAPE:{key}:{out['agg_base'].shape}")
            if str(out["agg_source"]) != "single_encoder_M_o":
                raise ProvenanceError(f"AGG_SOURCE:{key}:{out['agg_source']}")
            self._exports[key] = out
        return self._exports[key]

    def class_means(self, seed: int, fold: int, children, budget: str) -> tuple[np.ndarray, np.ndarray]:
        """(mu0, mu1) [n, 192] from ONE unit's M_o for every child (T1: never mix units)."""
        agg = self.exports(seed, fold)["agg_base"]
        rows = [self.primary(c) for c in children]
        a = agg[rows]                                              # [n, D, 2, 192]
        if budget == "single_draw80":
            a = a[:, int(cfg(self.config, "age.primary_draw"))]
        elif budget == "draw_ensemble10":
            a = a.mean(1)
        else:
            raise ValueError(budget)
        if not np.isfinite(a).all():
            raise ProvenanceError(f"NONFINITE_AGG:{seed}_{fold}:{budget}")
        return a[:, 0].astype(np.float64), a[:, 1].astype(np.float64)

    # ------------------------------------------------------------------ fixed inputs
    @cached_property
    def spectra(self) -> np.ndarray:
        with np.load(ROOT / cfg(self.config, "sources.pf_feature_file"), allow_pickle=False) as z:
            cont = z["cont"]
        if cont.shape[0] != len(self.co.rec):
            raise ProvenanceError("SPECTRA_RECORD_COUNT")
        return cont

    def spectral(self, children) -> np.ndarray:
        return np.stack([self.spectra[self.primary(c)].ravel() for c in children]).astype(np.float64)

    def technical(self, children, *, with_scale: bool = True) -> np.ndarray:
        rows = [self.rec.loc[self.primary(c)] for c in children]
        cols = [[float(r.record_scale) for r in rows]] if with_scale else []
        cols += [[float(r.accept_fraction) for r in rows], [float(r.qc_over_mean) for r in rows],
                 [float(np.log1p(r.n_acc)) for r in rows], [float(np.log1p(r.d1_seconds)) for r in rows]]
        return np.array(cols, dtype=np.float64).T

    def draw_unique_counts(self, children) -> dict:
        """Unique trial counts behind the 10-draw average vs the single draw (T5 reporting)."""
        out = {}
        for c in children:
            row = self.co.draw_row[self.primary(c)]
            out[int(c)] = {"std_draw0": int(np.unique(self.co.draw_std[row, 0]).size),
                           "dev_draw0": int(np.unique(self.co.draw_dev[row, 0]).size),
                           "std_union10": int(np.unique(self.co.draw_std[row]).size),
                           "dev_union10": int(np.unique(self.co.draw_dev[row]).size)}
        return out


def round1_cohort(config: dict) -> tuple[dict, Cohort]:
    pfc = pf_config(config, round1=True)
    co = Cohort(pfc, cfg(config, "sources.pf_prepare_round1"))
    if [int(s) for s in co.seeds] != [int(s) for s in cfg(config, "headroom.round1_seeds")]:
        raise ProvenanceError("ROUND1_SEEDS_DIFFER_FROM_CONFIG")
    return pfc, co


def h14_errors(config: dict) -> dict:
    data = json.loads((ROOT / cfg(config, "sources.pf_h14_private")).read_text())
    return {k: {int(c): float(v) for c, v in d.items()} for k, d in data["si"]["h14_err"].items()}


# ---------------------------------------------------------------------- staged epochs, D1 arrays, ST1 events

def stage_path(config: dict, record_id: str) -> Path:
    return ROOT / "private/auditory_gx" / cfg(config, "sources.stage_run") / "epochs" / f"{record_id}.npz"


def load_stage(config: dict, record_id: str) -> dict:
    with np.load(stage_path(config, record_id), allow_pickle=False) as s:
        return {k: s[k] for k in s.files}


def st_records(config: dict) -> pd.DataFrame:
    return pd.read_csv(ROOT / "private/auditory_st" / cfg(config, "sources.st_scope_run") / "records.csv")


def st_events(config: dict, record_id: str) -> pd.DataFrame:
    return pd.read_parquet(ROOT / "private/auditory_st" / cfg(config, "sources.st_scope_run") / "events" / f"{record_id}.parquet")


def d1_meta(config: dict, container_id: str) -> dict:
    return json.loads((ROOT / "private/auditory_d1" / cfg(config, "sources.d1_bdf_run") / "arrays" / f"{container_id}.json").read_text())


def d1_array(config: dict, container_id: str) -> np.ndarray:
    return np.load(ROOT / "private/auditory_d1" / cfg(config, "sources.d1_bdf_run") / "arrays" / f"{container_id}.npy", mmap_mode="r")
