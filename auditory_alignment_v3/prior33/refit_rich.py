"""Pre-registration FIXC refit: rich PCA and sigma use the core manifest's eligible windows.

The original build_rich.py and its pass-1 marker hashes remain unchanged. Its feature
extraction work is reused; only PCA and pass 2 are recomputed. Previous outputs are
preserved as hard links before atomic replacement. Production refuses after any rich
row is registered. This implements the lead decision recorded before donor results.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from . import build_rich as BR
from . import contract as C

RULE = "core_fit_unique_windows_exclude_any_donor_set_presentation_v1"


def core_fit_windows(full):
    """Unique stimulus windows, excluding each presentation barred by any target's donor set."""
    from .manifest import excluded_anywhere
    excluded = excluded_anywhere(full["donor_sets"], "sparrkulee")
    seg = full["segments"]["sparrkulee"]
    pairs = sorted({(int(full["presentations"][seg["presentation"][r]]["stream"]), int(seg["s"][r]))
                    for r in full["pools"]["core"]["sparrkulee"] if int(seg["presentation"][r]) not in excluded})
    return BR.segment_windows(pairs), {"rule": RULE, "excluded_presentations": sorted(excluded), "n_segments": len(pairs)}


def available_windows(full, recs):
    windows, stats = core_fit_windows(full)
    kept = {}
    total = sum(len(w) for w in windows.values())
    for stream, starts in windows.items():
        rec = recs[stream]
        if rec["reason"] is not None:
            continue
        end = BR.valid_end(rec["n_64"], rec["length"])
        starts = starts[(starts >= 0) & (starts + C.N_TGT <= end)]
        if len(starts):
            kept[stream] = starts
    stats.update(n_windows_before_availability=int(total), n_windows_kept=sum(len(w) for w in kept.values()),
                 fit_streams=[recs[s]["name"] for s in sorted(kept)])
    return kept, stats


def fit_pca(out, full, full_sha, recs, code_sha, scan_sha, log):
    kept, stats = available_windows(full, recs)
    wsha = BR._sha_bytes(b"".join(np.int64(st).tobytes() + np.ascontiguousarray(w, dtype=np.int64).tobytes()
                                for st, w in sorted(kept.items())))
    key = BR._sha_bytes(BR._dumps({"refit_code_sha256": code_sha, "core_manifest_sha256": full_sha,
                                  "windows_sha256": wsha, "scan_sha256": scan_sha,
                                  "fit": [[st, recs[st]["marker_key"], recs[st]["work_sha256"]] for st in sorted(kept)]}).encode())
    path, marker = os.path.join(out, BR.PCA_FILE), os.path.join(out, "_c7_pca_fixc.json")
    if os.path.exists(path) and os.path.exists(marker):
        old, basis = BR._read_json(marker), BR._load_npy(path)
        if old.get("marker_key") == key and BR._sha_bytes(np.ascontiguousarray(basis).tobytes()) == old["sha256"]:
            return {**old, "V": basis, "mu": np.asarray(old["mean"]), "reused": True}, kept
    basis, mu, fit = BR.pca_fit((BR._load_work(out, recs[st]), w) for st, w in sorted(kept.items()))
    BR._save_npy(path, basis)
    rec = {"schema": BR.SCHEMA_PCA, "marker_key": key, "file": BR.PCA_FILE,
           "sha256": BR._sha_bytes(np.ascontiguousarray(basis).tobytes()), "shape": [BR.N_MEL, BR.PCA_K],
           "mean": mu.tolist(), "windows_sha256": wsha, "scan_sha256": scan_sha, "core_manifest_sha256": full_sha,
           "refit_code_sha256": code_sha, **stats, **fit}
    BR._write_json(marker, rec)
    log(f"FIXC PCA refit: {stats['n_windows_kept']} windows, {len(kept)} streams, sha256 {rec['sha256']}")
    return {**rec, "V": basis, "mu": mu, "reused": False}, kept


def preserve_previous(out):
    """Never overwrite a pre-refit output without retaining its previous bytes."""
    backup = Path(out) / "rich_before_fixc_20261017"
    backup.mkdir(exist_ok=True)
    paths = [BR.PCA_FILE, BR.PCA_MARK, BR.META]
    paths += [os.path.join(c, name) for c in BR.COHORTS for name in (BR.RICH, BR.RICH_STREAMS)]
    for rel in paths:
        source, dest = Path(out) / rel, backup / rel
        if source.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.link(source, dest)
    return str(backup)


def build(out, full_path, log=print):
    from . import manifest as MF
    out = os.path.realpath(out)
    if out != os.path.realpath(BR.CACHE_ROOT):
        raise ValueError("FIXC refit accepts only the registered production cache root")
    ctx_m = MF._Ctx(out, "production", log)
    guard, quoted, have = MF.rich_results(ctx_m)
    if guard["n_rich_rows"] or quoted or have:
        raise MF.Refused("rich rows are already registered; cache refitting requires a new execution version")
    full, full_sha, _ = MF._read_core(out, os.path.dirname(full_path), ctx_m)
    sources = BR.Sources()
    BR._register_sk_root(sources.sparrkulee)
    tabs = {c: BR._Tables(out, c) for c in BR.COHORTS}
    old_code_sha = BR._code_sha()
    code_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    state = {"computed": 0, "stop_after": None}
    ctx = BR._Ctx(sources, None)
    with BR._build_lock(out), contextlib.closing(ctx):
        backup = preserve_previous(out)
        recs = {c: BR._pass1(out, c, tabs[c], ctx, None, old_code_sha, log, state) for c in BR.COHORTS}
        _, mask = BR._scan_state("auto", out, True)
        if mask["sha256"] != full["inputs"]["c3"]["sha256"]:
            raise ValueError("C3 scan changed since the core manifest was frozen")
        pca, windows = fit_pca(out, full, full_sha, recs["sparrkulee"], code_sha, mask["sha256"], log)
        extra = {"code_sha": code_sha, "partial": False, "extractor": ctx.extractor_info()}
        rich, rows = {}, {}
        for cohort in BR.COHORTS:
            rich[cohort], rows[cohort] = BR._pass2(out, cohort, tabs[cohort], recs[cohort], pca, log, extra)
        std = BR.rich_standardiser(rich["sparrkulee"], tabs["sparrkulee"].streams, rows["sparrkulee"], windows)
        mask = {**mask, "rule": RULE, "core_manifest_sha256": full_sha, "n_windows_kept": pca["n_windows_kept"],
                "excluded_presentations": pca["excluded_presentations"]}
        checks = {c: BR._extractor_check(ctx, c, tabs[c], recs[c]) for c in ("fau", "dtu")}
        meta = BR._meta(out, tabs, pca, BR.rich_projections(out), std, extra, checks, sources, None, mask)
        meta["refit"] = {"rule": RULE, "core_manifest_sha256": full_sha, "code_sha256": code_sha,
                         "pass1_builder_sha256": old_code_sha, "pass1_recomputed_streams": state["computed"],
                         "previous_outputs": os.path.relpath(backup, out), "declared_before_results": guard}
        meta["notes"] = ["Rich PCA and sigma use unique core donor-fit windows, excluding every presentation barred by any target's donor set.",
                         "Pass-1 feature extraction is unchanged; its original builder hash is retained in refit.pass1_builder_sha256.",
                         "Erratum to the original builder's docstring: the fixture has four no-source reasons, including not_nh_original; "
                         "only not_selected_dry_run is additional. The CPU Slurm example already names build_rich and --out.",
                         "Unavailable rich streams remain masked; no target-cohort EEG enters this audio-only PCA fit."]
        BR._write_json(os.path.join(out, BR.META), meta)
    log(f"FIXC rich complete: PCA {pca['sha256']}, sigma windows {std['n_windows']}, pass-1 recomputed {state['computed']}")
    return meta


def main():
    from .manifest import PRIVATE_OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=BR.CACHE_ROOT)
    parser.add_argument("--manifest", default=os.path.join(PRIVATE_OUT, "manifest.json"))
    args = parser.parse_args()
    build(args.out, args.manifest)


if __name__ == "__main__":
    main()
