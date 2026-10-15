"""ALN3.2 (package docs/03 §3; CORRECTION_01): post-hoc update coverage of the legacy progressive-prefix recipe.
Part A, every complete seed-3401 B_DENSE and B_ALIGNED record: open groups per epoch (recorded `open_groups`) intersected with
what the adaptation allows -> trainable backbone blocks reached, whether the non-block (input / embedding) group was ever
open, nominal lr of the deepest opened group.
Part B, registered subset (FAU and DTU, subject fold 0, content fold 0, NCE; B_DENSE both readouts, B_ALIGNED; all
adaptations): relative weight change per backbone group, best checkpoint vs theta_0 rebuilt with the training construction
order (seed -> Backbone). CPU. Writes results/auditory_alignment_v3/effective_update/ + docs/.../EFFECTIVE_UPDATE_REPORT.md."""
import json, math, os, sys, time
from collections import defaultdict
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch
from auditory_alignment_v3 import core, fm_dense, run as R3
from auditory_alignment_v2.foundation_adapter import Backbone

U = os.path.join(core.OUT, "units"); CK = os.path.join(core.OUT, "ckpt")
RES = os.path.join(core.REPO, "results", "auditory_alignment_v3", "effective_update"); os.makedirs(RES, exist_ok=True)
NB = {"cbramod": 12, "reve": 22}; PARTIAL_K = {"cbramod": 3, "reve": 6}
rows = R3.all_rows()


def trainable_blocks(arch, ad, n_open):
    """blocks (top-first) that train when n_open groups are open; the non-block group is group index NB (opened last)."""
    nb = NB[arch]
    if ad in ("pretrained_frozen",):
        return 0, False
    if ad == "pretrained_peft":  # LoRA on every block's attention, opened at once after warm-up; base weights frozen
        return (nb if n_open > 0 else 0), False
    k = PARTIAL_K[arch] if ad == "pretrained_partial" else nb
    return min(n_open, k), (ad in ("random_full", "pretrained_full") and n_open > nb)


A = defaultdict(list)
for r in rows:
    if r["family_id"] not in ("B_DENSE", "B_ALIGNED") or r["seed"] != 3401:
        continue
    p = os.path.join(U, f"{r['experiment_id']}.json")
    if not os.path.exists(p):
        continue
    rec = json.load(open(p))
    if rec.get("status") != "complete":
        continue
    s = r["spec"]; arch, ad = s["architecture"], s["adaptation"]
    opens = [c.get("open_groups", 0) for c in rec.get("curve", [])]
    blocks_last, nonblock = trainable_blocks(arch, ad, opens[-1] if opens else 0)
    best = rec.get("best_epoch") or len(opens)
    blocks_best, _ = trainable_blocks(arch, ad, opens[best - 1] if opens else 0)
    lr_b = fm_dense.LR[ad][0]; nb = NB[arch]  # nominal initial lr of the deepest opened group: lr_b * LLRD^depth (top block depth 0, non-block depth nb)
    deep = (nb if nonblock else blocks_last - 1) if ad != "pretrained_peft" else nb - 1
    nominal = lr_b * fm_dense.LLRD ** deep if (lr_b > 0 and blocks_last > 0) else None
    A[(r["family_id"], s.get("readout"), arch, ad)].append({"blocks_last": blocks_last, "nonblock_ever": nonblock, "blocks_at_best": blocks_best,
                                                           "epochs": len(opens), "lr_min_group": nominal})
partA = {}
for k, v in sorted(A.items(), key=lambda kv: str(kv[0])):
    partA["|".join(map(str, k))] = {"n_units": len(v), "blocks_total": NB[k[2]], "trainable_blocks_last_epoch": sorted({x["blocks_last"] for x in v}),
                                    "trainable_blocks_at_best_median": float(np.median([x["blocks_at_best"] for x in v])),
                                    "nonblock_ever_open_fraction": float(np.mean([x["nonblock_ever"] for x in v])),
                                    "nominal_lr_deepest_opened_group": min((x["lr_min_group"] for x in v if x["lr_min_group"] is not None), default=None)}

B = {}
for r in rows:
    s = r["spec"]
    if r["family_id"] not in ("B_DENSE", "B_ALIGNED") or r["seed"] != 3401 or r["dataset"] not in ("fau", "dtu") or r["subject_fold"] != 0 or r["content_fold"] != 0 or s["objective"] != "NCE":
        continue
    ck = os.path.join(CK, f"{r['experiment_id']}_best.pt")
    if not os.path.exists(ck) or not os.path.exists(os.path.join(U, f"{r['experiment_id']}.json")):
        continue
    t0 = time.time(); arch, ad = s["architecture"], s["adaptation"]
    torch.manual_seed(r["seed"]); bb = Backbone(arch, r["dataset"], ad, 128)
    sd = torch.load(ck, map_location="cpu")["model"]
    name = {id(p): n for n, p in bb.named_parameters()}
    groups = []
    for kind, i, ps in fm_dense.block_groups(bb):
        num = den = 0.0
        for p in ps:
            n = name[id(p)]; q = sd["bb." + n].float()
            num += float(((q - p.detach()) ** 2).sum()); den += float((p.detach() ** 2).sum())
        groups.append({"group": f"{kind}{i}", "rel_change": math.sqrt(num) / (math.sqrt(den) + 1e-12)})
    blk = [g for g in groups if g["group"].startswith("block")]; other = [g for g in groups if g["group"].startswith("other")]
    B[r["experiment_id"]] = {"family": r["family_id"], "dataset": r["dataset"], "arch": arch, "adaptation": ad, "readout": s.get("readout"),
                             "blocks_changed_gt_1e-6": sum(g["rel_change"] > 1e-6 for g in blk), "blocks_total": len(blk),
                             "max_block_rel_change": max(g["rel_change"] for g in blk), "nonblock_rel_change": other[0]["rel_change"] if other else None,
                             "per_group": groups, "seconds": round(time.time() - t0, 1)}
    print(r["family_id"], r["dataset"], arch, ad, s.get("readout"), "blocks changed", B[r["experiment_id"]]["blocks_changed_gt_1e-6"], "/", len(blk),
          "nonblock", B[r["experiment_id"]]["nonblock_rel_change"], flush=True)
json.dump({"partA": partA, "partB": B}, open(os.path.join(RES, "effective_update.json"), "w"), indent=1)
L = ["# Effective update coverage of the legacy progressive-prefix recipe (B_DENSE, B_ALIGNED; seed 3401)", "",
     f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')} by `private/auditory_alignment_v3/effective_update_legacy.py` (Slurm {os.environ.get('SLURM_JOB_ID', 'local')}); "
     "see CORRECTION_01_FULL_UPDATE_LABEL.md. Part A uses each record's `open_groups` per epoch intersected with the adaptation's allowed parameters; "
     "Part B measures the best checkpoint against θ_0 rebuilt with the training construction order. B_ALIGNED rows cover the units complete at generation time.", "",
     "## Part A — trainable backbone blocks (all complete units)", "",
     "| family · readout · backbone · adaptation | units | blocks | trainable blocks, last epoch | median at best epoch | non-block ever open | nominal initial lr of the deepest opened group (lr × 0.75^depth) |", "|---|---|---|---|---|---|---|"]
for k, v in partA.items():
    L.append(f"| {k.replace('|', ' · ')} | {v['n_units']} | {v['blocks_total']} | {v['trainable_blocks_last_epoch']} | {v['trainable_blocks_at_best_median']:.0f} | "
             f"{v['nonblock_ever_open_fraction']:.2f} | {v['nominal_lr_deepest_opened_group']:.2e} |" if v['nominal_lr_deepest_opened_group'] else
             f"| {k.replace('|', ' · ')} | {v['n_units']} | {v['blocks_total']} | {v['trainable_blocks_last_epoch']} | {v['trainable_blocks_at_best_median']:.0f} | {v['nonblock_ever_open_fraction']:.2f} | – |")
L += ["", "## Part B — measured weight change (FAU and DTU, subject fold 0, content fold 0, NCE)", "",
      "| family | dataset | backbone | adaptation | readout | blocks with rel. change > 1e-6 | max block rel. change | non-block rel. change |", "|---|---|---|---|---|---|---|---|"]
for e, v in sorted(B.items(), key=lambda kv: (kv[1]["family"], kv[1]["dataset"], kv[1]["arch"], kv[1]["adaptation"], str(kv[1]["readout"]))):
    nbv = "–" if v["nonblock_rel_change"] is None else f"{v['nonblock_rel_change']:.2e}"
    L.append(f"| {v['family']} | {v['dataset']} | {v['arch']} | {v['adaptation']} | {v['readout']} | {v['blocks_changed_gt_1e-6']} / {v['blocks_total']} | {v['max_block_rel_change']:.2e} | {nbv} |")
L.append("")
open(os.path.join(core.REPO, "docs", "auditory_alignment_v3", "EFFECTIVE_UPDATE_REPORT.md"), "w").write("\n".join(L))
print("done", len(partA), "cells,", len(B), "checkpoints")
