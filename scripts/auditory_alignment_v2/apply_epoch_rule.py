"""Registered epoch-budget rule (IMPLEMENTATION_RECEIPT §4): per architecture, once >= 10 recipes are chosen, the median
best epoch of the chosen candidates over the 20-epoch development runs decides 50 (median < 15) or 100 epochs.
Values once written are never changed."""
import glob, json, os, statistics
R = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v2/fm_recipe"
f = os.path.join(R, "epochs.json"); cur = json.load(open(f)) if os.path.exists(f) else {}
basis = json.load(open(f.replace(".json", "_basis.json"))) if os.path.exists(f.replace(".json", "_basis.json")) else {}
for arch in ("cbramod", "reve"):
    if arch in cur:
        continue
    best = []
    for p in glob.glob(os.path.join(R, f"{arch}__*.json")):
        d = json.load(open(p)); ch = d.get("chosen")
        if not ch:
            continue
        c = [x for x in d["candidates"] if x.get("lr_backbone") == ch["lr_backbone"] and x.get("lr_head") == ch["lr_head"]][0]
        best.append(c["best_epoch"])
    if len(best) >= 10:
        med = statistics.median(best); cur[arch] = 50 if med < 15 else 100
        basis[arch] = {"n_recipes": len(best), "median_best_epoch_of_20": med, "best_epochs": sorted(best), "rule": "median < 15 -> 50 else 100"}
        print(arch, "->", cur[arch], basis[arch])
if cur:
    json.dump(cur, open(f + ".tmp", "w")); os.replace(f + ".tmp", f)
    json.dump(basis, open(f.replace(".json", "_basis.json"), "w"), indent=1)
