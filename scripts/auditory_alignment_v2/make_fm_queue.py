"""queue_lrsel.txt (all recipe keys) and queue_fm.txt (runnable foundation rows: D_GX, and B_FM / D_FM_GENERIC rows whose
learning-rate recipe is resolved). Rebuilt atomically; workers re-read the file every pass."""
import json, os, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v2.run_fm import RECIPE, recipe_key
from auditory_alignment_v2.run import PLAN
O = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v2"
R = [json.loads(l) for l in open(PLAN)]
SC = json.load(open("/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v2/seed_scope.json"))
PN = SC.get("panel", {})
in_panel = lambda r: bool(PN) and r["seed"] in PN["seeds"] and r["family_id"] in PN["families"] and r["spec"].get("objective") == PN["objective"] \
    and r["spec"].get("adaptation") in PN["adaptations"]  # registered multi-seed panel (repair/PANEL_REGISTRATION.json)
in_scope = lambda r: r["seed"] in SC["seeds"] or r["family_id"] in SC["exempt_families"] or in_panel(r)  # user 2026-10-07: one seed + panel
fm = [(i, r) for i, r in enumerate(R) if r["family_id"] in ("B_FM", "D_FM_GENERIC")]
keys = sorted({recipe_key(r) for _, r in fm}, key=lambda k: (k.split("|")[0] != "cbramod", k.split("|")[2] != "private_bdf", k))
if not os.path.exists(f"{O}/queue_lrsel.txt"):
    open(f"{O}/queue_lrsel.txt", "w").write("".join(f"{k.replace('|', '__')}|0\n" for k in keys))
cfm = [(i, r) for i, r in enumerate(R) if r["family_id"] in ("C_ATTENTION", "C_SELECTION", "C_COVERAGE") and r["spec"]["architecture"] == "cbramod"]
ready = [(i, r) for i, r in enumerate(R) if r["family_id"] == "D_GX"]
EP = json.load(open(os.path.join(RECIPE, "epochs.json"))) if os.path.exists(os.path.join(RECIPE, "epochs.json")) else {}
EPOCHS_OK = lambda arch: arch in EP  # foundation units need the resolved epoch budget of their architecture
ready += [(i, r) for i, r in fm + cfm if EPOCHS_OK(r["spec"]["architecture"]) and os.path.exists(os.path.join(RECIPE, recipe_key(r).replace("|", "__") + ".json"))]
ready.sort(key=lambda t: (t[1]["family_id"] != "D_GX", t[1]["seed"], t[1]["subject_fold"], t[1]["content_fold"], t[1]["spec"]["architecture"]))
# ---- dependency-bearing lines (technical dependencies only)
from auditory_alignment_v2.donor import donor_id, sources_for
from auditory_alignment_v2.run_stage import teacher_of, depth_of
from auditory_alignment_v2.run_adapt import base_row, resolve_unit
rec = lambda a, d, ds, o: os.path.exists(os.path.join(RECIPE, f"{a}__pretrained_{d}__{ds}__{o}.json"))
donors = set()
for a in ("cbramod", "reve"):
    for s in SC["seeds"]:
        for d in ("partial", "full"):
            for t in ("fau", "dtu"):
                src = sources_for("B_AUDITORY_CONTINUE", t)
                if rec(a, d, src[0], "NCE"):
                    donors.add(donor_id(a, d, src, s))
        src = sources_for("D_FM_PUBLIC", "private_bdf")
        if rec(a, "full", src[0], "NCE"):
            donors.add(donor_id(a, "full", src, s))
dlines = [d for d in sorted(donors) if not os.path.exists(f"{O}/donors/{d}.pt")]
dep = []
for i, r in enumerate(R):
    f = r["family_id"]; sp = r["spec"]
    if f in ("B_AUDITORY_CONTINUE", "D_FM_PUBLIC"):
        dpth = "full" if f == "D_FM_PUBLIC" else depth_of(sp["adaptation"])
        did = donor_id(sp["architecture"], dpth, sources_for(f, r["dataset"]), r["seed"])
        if EPOCHS_OK(sp["architecture"]) and os.path.exists(f"{O}/donors/{did}.pt") and rec(sp["architecture"], depth_of(sp["adaptation"]), r["dataset"], sp["objective"]):
            dep.append((i, r))
    elif f == "D_LOCAL_DISTILL":
        _, t = teacher_of(r, R)
        if t and os.path.exists(f"{O}/units/{t}.json"):
            dep.append((i, r))
    elif f == "C_ADAPT":
        b = base_row(r, R)
        if b and resolve_unit(b["experiment_id"], O)[0] is not None:
            dep.append((i, r))
ready = [(i, r) for i, r in ready if in_scope(r)]; dep = [(i, r) for i, r in dep if in_scope(r)]
# order: the one-seed matrix and its dependent families first, the registered multi-seed panel afterwards
lines = [t for t in ready + dep if not in_panel(t[1])] + [t for t in ready + dep if in_panel(t[1])]
# per-unit GPU weights for the pool's admission. User 2026-10-07: units that train a foundation model get a whole card
# (weight 1000 > any card budget: starts only on an idle card, nothing else is admitted while it runs). Light units that
# only adapt on a frozen base (C_ADAPT) or train a small student (D_LOCAL_DISTILL) share a card (GB estimates).
EXCLUSIVE = 1000
def weight(r=None, donor=None):
    if donor:
        return EXCLUSIVE
    f, sp = r["family_id"], r["spec"]
    if f == "D_LOCAL_DISTILL":
        return 6 if "reve" in sp.get("teacher", "") else 3
    if f == "C_ADAPT":
        return 4 if sp.get("architecture") == "cbramod" else 2
    if sp.get("architecture") in ("cbramod", "reve"):
        return EXCLUSIVE
    return 2
wt = [f"{d} {weight(donor=d)}" for d in dlines] + [f"{r['experiment_id']} {weight(r)}" for i, r in lines]
open(f"{O}/queue_fm_weights.txt.tmp", "w").write("\n".join(wt) + "\n"); os.replace(f"{O}/queue_fm_weights.txt.tmp", f"{O}/queue_fm_weights.txt")
tmp = f"{O}/queue_fm.txt.tmp"
open(tmp, "w").write("".join(f"{d}|-1\n" for d in dlines) + "".join(f"{r['experiment_id']}|{i}\n" for i, r in lines)); os.replace(tmp, f"{O}/queue_fm.txt")
print("donor lines", len(dlines), "dependency rows", len(dep))
print(len(keys), "recipe keys;", len(ready), "runnable foundation rows")
