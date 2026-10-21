# ALN4.1 intake — 2026-10-21 (Claude Code)

Researcher instruction: "这个包也启动，这个包里的有优先级" (`AUDITORY_ALN4_SERVER_PACKAGE_v4_1_20261021.zip`, received while
ALN3.6 R1 was being launched). Interpretation recorded in AGENTS.md: ALN4.1 runs alongside ALN3.6 and takes priority where they
compete (engineering effort first; fleet plugin placed before ALN3.6 so its lanes take released slots first). Neither package
cancels the other's registered work.

## Package and repository

- Zip SHA256 `eb9b343beb81994bf564a81b65577f0160547005a162db7894766e36e7971b2c`; extracted beside earlier packages.
- `verify_package.py` PASS (56 files), `verify_handoff.py` PASS (9 checks), NumPy temporal-CS PASS, time-access PASS,
  age-probe PASS, classical CS PASS, `materialize_plan.py` 72 logical units (`aln41_logical_units.json`).
- `verify_temporal_torch.py` crashed in its own harness (`close()` converted an `expected` tensor that still required grad to
  NumPy). A server copy with only that detach added (`verify_temporal_torch_server.py`) passes 28/28 checks with torch
  2.6.0+cu124 (`VERIFY_TEMPORAL_TORCH.server.json`). The package file is unchanged.
- GitHub main rechecked 2026-10-21T00:16:53Z: `3da8cf5758214c0cf87a1f1c8d67fb84b574000e` (equals the package baseline).
  The server root workspace is not a git checkout; production code hashes are bound per plan (`sources`).
- No ALN4.0 package or units ever reached this server (no `AUDITORY_ALN4*v4_0*`, no `aln4/` code, no ALN4 records):
  nothing to register as a legacy design.

## Live state (2026-10-21 ~02:17 CEST)

Fleet coordinator 1051045 and evidence service 1047358 running; 10 runfill GPUs held by the four registered tails
(DTU budget 6, breadth budget 1, breadth curves 2) plus one ALN3.6 local unit. ALN3.6 lanes registered 2026-10-21 01:3x
(researcher-approved); ALN4.1 lanes registered after this intake, ahead of ALN3.6 in plugin order.

## Stage1 gate (bounded MindMix restoration, ~35 min of the 4 h bound)

`STAGE1_GATE.json`: the MindMix EEG-only asset was downloaded at the pinned commit (full-file SHA256 equals the LFS oid
`707dfabf…5a0`) and loaded with `weights_only=True`. It is a LaBraM-style student with 200×24 dims, 20 heads, out_chans 8,
pos_embed [1,109,200] and time_embed [1,128,200]. Neither the public factory (`labram_large_*` = 400×24 dims, 16 heads,
out 16; pos_embed forced None; time_embed 16, on main and fix branch) nor the only channel table (136 entries) explains it.
The pretraining channel→position mapping is unrecoverable. **asset_gate = not_passed → Stage1 = verified CBraMod
pretrained_full** (`pretrained_weights.pth` SHA256 `0792cb80…7178`, HF 500543c, code b9e96100). No target outcome was
consulted.

## Source data

- prior33 manifests: server full `b751976b…` and rich `c8f11c28…` match the package; public core `3ffa6e6d…` matches.
- Pool after the downstream-overlap exclusion (presentations 4, 5, 19): fit 81,732 segments / 64 people / 48 families;
  dev 6,332 / 10 / 9 (`pools.dev.sparrkulee`). Both match the package. Rich streams are complete for all 72 streams.
- First plan attempt (unused) defined dev as every dev-role segment (6,556 / 10 / 10). It was set aside before any
  unit ran, under `source_v1/superseded_unused/`.
- Second plan (smoke 1053067 only) failed its gradient check on `net.patch_embedding.mask_encoding`. That is CBraMod's
  masked-pretraining token, `requires_grad=False` upstream, read only when a mask is passed. It is now exempted by exact name
  (`UNUSED_WITHOUT_MASK`). The plan was regenerated with a byte-identical stream (`b51945d5…`); the old plan is set aside.
  The private-FT and frozen plans recorded the earlier source-plan hash as provenance; their rows reference source
  units by id, so they are unaffected.

## Private roster and target splits

64 children (HA 55, NH 9), outer folds 13/13/13/13/12 (seed 20261005), ES = last ~20% physical blocks of training children.
Public DTU/FAU keep the existing pooled participant/content folds.

## Legacy D2 / GX / NEXTMAP intake (read-only, from server originals)

The three git-tree entries the package could not fetch are present byte-identical under `archive/` (same blob OIDs).
- D2 (MFF continuous EEG, 62 children; guess-mean MAE 19.07 months): 128-electrode ridge 12.50 (single-seed linear,
  `archive/results/auditory_d2/D2_ridge_001_curve.json`); 4-seed repeats are linear 12.97 ± 0.57 and RBF 12.50 ± 0.27
  (`D2_ROUND4_CORRECTION.md`). The handoff phrase "17.68 → 12.50" mixes linear and RBF; like-for-like is linear
  17.68 → 12.97 or RBF 18.04 → 12.50. BDF: linear 26.91 ± 1.12 vs 32.20. Per-child predictions are in
  `archive/private/auditory_d2/D2_*_predictions.json` (test folds only). D1 continuous arrays were deleted 2026-10-11, so D2
  features cannot be rebuilt without re-export.
- GX: R1 MFF SSL ridge 19.8 vs 19.7 baseline; HA SSL 27.7 vs 33.6. R2 embedding-age result voided by its own erratum
  (corrected HA 23.7); the erratum is not on GitHub. Per-child predictions are in `private/auditory_gx/GX3_age_*`.
- NEXTMAP: HA/BDF 55 children common view 23.2; G1 direct single-trial age 32.2. H8 D2+spectral 10.46 (MFF), H8b 24.03 (BDF).
  The `gpu_age.train_age` train-mode bug (`archive/auditory_nextmap/gpu_age.py:90/130/151`) affects G1 age_trial/age_subavg
  and H3 ft_from_stim only; it is documented in `archive/docs/auditory_story/PROTOCOL.md:164-173` but not in the G1/H
  reports, and no corrected rerun exists. D2 ridge/RBF is unaffected.
- MFF counts: GX staged 41 records / 37 ids pure-tone, 29/27 bapa; evaluated 40/36. The same-day pairs are 9
  candidates; earlier reports say 7 complete, while GX4's own CSV has 8 complete in both directions and 1 one-directional
  (discrepancy recorded, not resolved by selection).
- Missing or limited: no per-child predictions for H1/H2/H4–H6/H8/H10/H11 (summaries only); archived GX code does not run
  in place.

## Deviations and notes

- Engineering checks (`checks/`, receipts) have no outcome thresholds.
- Storage: no deletion; A3b/A3c/A3d/D_FM remain registered, not judged deletable.
