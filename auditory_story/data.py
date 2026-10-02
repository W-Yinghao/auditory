"""Read-only adapters for STORY v1 (nothing here writes).

Main cohort, primary visits and PF2 outer folds come from AgeSource (PF2 prepare_002 through the NEXTMAP adapter);
whole-trial embeddings from the H-series cache (each PF2 unit's frozen M_o, bf16 as stim_002); trial history and
physical positions from the GX stage files joined to the ST1 event tables by trial_id; interval geometry from D1.
"""
from __future__ import annotations

from functools import cached_property

import numpy as np
import pandas as pd

from auditory_nextmap.adapters import AgeSource, d1_meta, load_stage, st_events, st_records
from auditory_nextmap.runtime import load_config as nm_load_config

from .runtime import ROOT, ProvenanceError, cfg, stable_int

CLASSES = (0, 1)                       # 0 = standard ('1'), 1 = deviant ('2') as staged by GX


class StorySource:
    def __init__(self, config: dict):
        self.config = config
        self.nm = nm_load_config(cfg(config, "sources.nextmap_config"))
        if cfg(self.nm, "sources.pf_prepare_run") != cfg(config, "sources.pf_prepare_run") or \
                cfg(self.nm, "sources.pf_stim_run") != cfg(config, "sources.pf_stim_run"):
            raise ProvenanceError("NEXTMAP_PF_RUNS_DIFFER_FROM_STORY_CONFIG")
        self.age = AgeSource(self.nm)
        self.co = self.age.co
        self.children = [int(c) for c in self.age.main_children]
        self.seeds = [int(s) for s in cfg(config, "splits.outer_seeds")]
        if not set(self.seeds) <= set(self.co.seeds):
            raise ProvenanceError("STORY_SEEDS_NOT_IN_PF2")
        self.n_folds = int(cfg(config, "splits.outer_folds"))
        self.rec = self.co.rec.set_index("rec")
        self.prim = {c: self.age.primary(c) for c in self.children}
        self.all_idx = self.co.trial_idx_of_records([self.prim[c] for c in self.children])

    # ------------------------------------------------------------------ cohort and folds
    def units(self) -> list[tuple[int, int]]:
        return [(s, k) for s in self.seeds for k in range(self.n_folds)]

    def split(self, seed: int, fold: int) -> tuple[list[int], list[int]]:
        outer = self.co.outer(seed)
        train = [c for c in self.children if outer[c] != fold]
        test = [c for c in self.children if outer[c] == fold]
        return train, test

    def main_table(self) -> pd.DataFrame:
        rows = []
        for c in self.children:
            r = self.prim[c]
            R = self.rec.loc[r]
            sir, muss = float(R.sir), float(R.muss)
            ok = sir in (1.0, 2.0, 3.0, 4.0, 5.0) and np.isfinite(muss)
            rows.append({"child": c, "identity_group": str(R.identity_group), "primary_rec": int(r),
                         "record_id": str(R.record_id), "sir_ordinal": sir, "muss_original": muss,
                         "age_months": float(R.age_months), "device_months": float(R.duration_months),
                         "n_std": int(R.n_std), "n_dev": int(R.n_dev), "n_acc": int(R.n_acc),
                         "record_seconds": float(R.d1_seconds), "accept_fraction": float(R.accept_fraction),
                         "record_scale": float(R.record_scale), "qc_over_mean": float(R.qc_over_mean),
                         "target_status": "complete" if ok else "incomplete"})
        return pd.DataFrame(rows)

    def clinical_cross_check(self, table: pd.DataFrame) -> dict:
        """Independent re-read of the clinical main table: one row per primary record and identical SIR/MUSS/age/duration."""
        coh = pd.read_csv(ROOT / cfg(self.config, "sources.clinical_cohort"), usecols=["recording", "age", "duration", "V", "SIR"])
        coh = coh.rename(columns={"recording": "record_id", "age": "age_months", "duration": "device_months",
                                  "V": "muss_original", "SIR": "sir_ordinal"})
        sub = coh[coh.record_id.isin(set(table.record_id))]
        counts = sub.record_id.value_counts()
        merged = table.merge(sub, on="record_id", suffixes=("", "_src"))
        mismatch = {}
        for col in ("sir_ordinal", "muss_original", "age_months", "device_months"):
            a, b = merged[col].astype(float).to_numpy(), merged[f"{col}_src"].astype(float).to_numpy()
            mismatch[col] = int((~np.isclose(a, b, rtol=0, atol=1e-9)).sum())
        return {"rows_found": int(len(sub)), "records_without_row": int(len(set(table.record_id) - set(sub.record_id))),
                "records_with_multiple_rows": int((counts > 1).sum()), "value_mismatches": mismatch}

    # ------------------------------------------------------------------ trial table (cache order = all_idx)
    @cached_property
    def trial_table(self) -> pd.DataFrame:
        co = self.co
        st = st_records(self.nm).set_index("record_id")
        centre = float(cfg(self.config, "inputs.epoch_centre_offset_s"))
        block_s = float(cfg(self.config, "inputs.physical_block_seconds"))
        guard = float(cfg(self.config, "inputs.block_guard_seconds"))
        parts = []
        for c in self.children:
            r = self.prim[c]
            rid = str(self.rec.loc[r, "record_id"])
            idx = self.all_idx[co.t_record[self.all_idx] == r]
            pos, y, onset = co.t_pos[idx], co.t_y[idx], co.t_onset[idx]
            stage = load_stage(self.nm, rid)
            acc = np.flatnonzero(stage["accepted"].astype(bool))
            ep = acc[pos]
            if not np.array_equal(stage["y"][ep], y) or not np.allclose(stage["onset_seconds"][ep], onset, rtol=0, atol=1e-9):
                raise ProvenanceError(f"STAGE_TRIAL_MISMATCH:child{c}")
            tid = stage["trial_id"][ep].astype(str)
            ev = st_events(self.nm, rid)
            targets = ev[ev.event_kind == "target"]
            first, last = float(targets.onset_seconds.min()), float(targets.onset_seconds.max())
            evi = ev.set_index("trial_id")
            if not evi.index.is_unique or not set(tid) <= set(evi.index):
                raise ProvenanceError(f"EVENT_JOIN:child{c}")
            e = evi.loc[tid]
            if not np.allclose(e.onset_seconds.to_numpy(float), onset, rtol=0, atol=1e-9):
                raise ProvenanceError(f"EVENT_ONSET_MISMATCH:child{c}")
            meta = d1_meta(self.nm, str(st.loc[rid, "_d1_container_id"]))
            rate = float(meta["rate_hz"])
            ivs = {int(x["interval_index"]): x for x in meta["intervals"]}
            iv_start = np.array([int(ivs[int(i)]["start"]) for i in e.exported_interval_index])
            iv_stop = np.array([int(ivs[int(i)]["stop"]) for i in e.exported_interval_index])
            rel = (e.exported_index.to_numpy(np.int64) - iv_start) / rate + centre
            length = (iv_stop - iv_start) / rate
            block = np.floor(rel / block_s).astype(np.int64)
            inblock = rel - block * block_s
            guard_ok = (rel >= 0) & (inblock >= guard) & (inblock <= block_s - guard) & (rel <= length - guard)
            run = e.previous_run_length.to_numpy(float)
            gap = e.previous_gap_s.to_numpy(float)
            parts.append(pd.DataFrame({
                "trial": idx, "child": c, "rec": r, "cls": y.astype(np.int64), "onset_s": onset,
                "h_run": np.log1p(run), "h_gap": np.log1p(gap),
                "h_pos": (onset - first) / max(last - first, 1e-9),
                "interval": e.exported_interval_index.to_numpy(np.int64), "block": block,
                "group": (block % 2).astype(np.int64), "guard_ok": guard_ok}))
        tt = pd.concat(parts, ignore_index=True)
        order = np.argsort(tt.trial.to_numpy(), kind="stable")
        tt = tt.iloc[order].reset_index(drop=True)
        if not np.array_equal(tt.trial.to_numpy(), self.all_idx):
            raise ProvenanceError("TRIAL_TABLE_ORDER_DIFFERS_FROM_CACHE_INDEX")
        return tt

    def support_counts(self) -> pd.DataFrame:
        """Guard-respecting trials per child x block group x class (episode / E3 eligibility; no outcome)."""
        tt = self.trial_table
        g = tt[tt.guard_ok].groupby(["child", "group", "cls"]).size().unstack(["group", "cls"], fill_value=0)
        out = pd.DataFrame({"child": self.children})
        for grp in (0, 1):
            for k in CLASSES:
                col = g[(grp, k)] if (grp, k) in g.columns else pd.Series(dtype=int)
                out[f"g{grp}c{k}"] = out.child.map(col).fillna(0).astype(int)
        need = int(cfg(self.config, "inputs.support_per_class"))
        out["episode_eligible"] = (out[["g0c0", "g0c1", "g1c0", "g1c1"]] >= need).all(1)
        return out

    # ------------------------------------------------------------------ embeddings and fixed views
    def embedding_path(self, seed: int, fold: int):
        return ROOT / cfg(self.config, "sources.whole_trial_embeddings") / f"ha_s{seed}_k{fold}.npz"

    def embeddings(self, seed: int, fold: int) -> np.ndarray:
        with np.load(self.embedding_path(seed, fold), allow_pickle=False) as z:
            emb, idx = z["emb_all"], z["all_idx"]
        if not np.array_equal(idx, self.all_idx):
            raise ProvenanceError(f"CACHE_TRIAL_INDEX:{seed}_{fold}")
        if emb.shape != (len(self.all_idx), int(cfg(self.config, "inputs.embedding_dim"))) or not np.isfinite(emb).all():
            raise ProvenanceError(f"CACHE_SHAPE_OR_NONFINITE:{seed}_{fold}")
        return emb

    def cache_consistency(self, seed: int, fold: int, emb: np.ndarray) -> float:
        """Max |mean of cached draw0 embeddings - stim_002 agg_base draw0| over the 55 records x 2 classes."""
        agg = self.age.exports(seed, fold)["agg_base"]
        worst = 0.0
        for c in self.children:
            r = self.prim[c]
            for k in CLASSES:
                gi = self.co.budget_idx(r, 0, k)
                loc = np.searchsorted(self.all_idx, gi)
                if not np.array_equal(self.all_idx[loc], gi):
                    raise ProvenanceError("DRAW0_OUTSIDE_CACHE")
                worst = max(worst, float(np.abs(emb[loc].astype(np.float64).mean(0) - agg[r, 0, k]).max()))
        return worst

    def encoder_scope(self, seed: int, fold: int) -> dict:
        ex = self.age.exports(seed, fold)
        outer = self.co.outer(seed)
        lane_test = {c for c, f in outer.items() if f == fold}
        train = {int(c) for c in ex["train_children"]}
        test = {int(c) for c in ex["test_children"]}
        return {"export_test_equals_fold": test == lane_test, "train_disjoint_test": not (train & lane_test),
                "train_children": sorted(train), "lane_test_children": sorted(lane_test)}

    @cached_property
    def _specplus(self) -> np.ndarray:
        with np.load(ROOT / cfg(self.config, "sources.spectral_plus"), allow_pickle=False) as z:
            sp = z["specplus"]
        if sp.shape[0] != len(self.co.rec):
            raise ProvenanceError("SPECPLUS_RECORD_COUNT")
        return sp

    def spectral_view(self, children) -> np.ndarray:
        """Fixed D2 + spectral-plus combination ('spec_d2_plus' of H8c): PF features_001 cont [20 x 9] and H4 specplus [20 x 8]."""
        S = self.age.spectral(children)
        P = np.stack([self._specplus[self.prim[c]].ravel() for c in children]).astype(np.float64)
        return np.concatenate([S, P], 1)

    def technical(self, children) -> np.ndarray:
        """record scale, accept fraction, bad-segment (QC-over) mean, log1p accepted trials, log1p D1 seconds."""
        return self.age.technical(children)


def label_sets(train_children: list[int], seed: int, outer_seed: int, fold: int, budgets: list, repeats: dict) -> dict:
    """Nested label budgets: per repeat one target-blind permutation of the outer-training children; 12 is the prefix
    of 24; 'all' is one set. Returns {budget: [sorted child lists per repeat]}."""
    base = sorted(int(c) for c in train_children)
    n_rep = max(int(repeats[str(b)]) for b in budgets if str(b) != "all")
    perms = [np.random.default_rng(stable_int(seed, outer_seed, fold, r) % (2 ** 63)).permutation(base).tolist()
             for r in range(n_rep)]
    out = {}
    for b in budgets:
        if str(b) == "all":
            out["all"] = [base]
        else:
            m = int(b)
            if m > len(base):
                raise ProvenanceError(f"BUDGET_EXCEEDS_TRAIN:{m}>{len(base)}")
            out[str(b)] = [sorted(perms[r][:m]) for r in range(int(repeats[str(b)]))]
    return out


def inner_folds(children: list[int], n_folds: int, *key) -> dict[int, int]:
    """Target-blind balanced inner folds: seeded permutation dealt round-robin."""
    base = sorted(int(c) for c in children)
    perm = np.random.default_rng(stable_int(*key) % (2 ** 63)).permutation(base)
    return {int(c): i % n_folds for i, c in enumerate(perm)}
