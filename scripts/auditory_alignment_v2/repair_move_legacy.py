"""Move every artefact produced through the channel-mean foundation-model interface into legacy_chmean_v1/ (move only; no
deletion, no edit). Dependency-based: units of B_FM, D_FM_GENERIC, B_AUDITORY_CONTINUE, D_FM_PUBLIC, D_LOCAL_DISTILL, the
cbramod arms of C_ATTENTION / C_COVERAGE / C_SELECTION / C_ADAPT; donors and donor markers; learning-rate recipes and the
learning-rate queue state; canonical-reuse pointers to affected units; their logs, pool markers and checkpoints.
Writes legacy_chmean_v1/MANIFEST.json (sha256 of every moved unit record). Usage: move_legacy.py [--execute]"""
import glob, hashlib, json, os, shutil, sys, time
raise SystemExit("one-time migration, executed 2026-10-07 22:39; re-running would select REPAIRED units by family. Disabled.")
O = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v2"
L = O + "/legacy_chmean_v1"
CK_REAL = os.path.realpath(O + "/ckpt"); CK_LEG = os.path.join(os.path.dirname(CK_REAL), "legacy_chmean_v1", "ckpt")
EXE = "--execute" in sys.argv
R = {}
for l in open("/home/infres/yinwang/EEG_auditory/AUDITORY_ALIGNMENT_NEXT_SERVER_PACKAGE_v2_20261006/plans/planned_comparisons.jsonl"):
    r = json.loads(l); R[r["experiment_id"]] = r
def affected(e):
    if e.startswith("donor__"): return True
    r = R.get(e)
    if r is None: return False
    f, a = r["family_id"], r["spec"].get("architecture")
    return f in ("B_FM", "D_FM_GENERIC", "B_AUDITORY_CONTINUE", "D_FM_PUBLIC", "D_LOCAL_DISTILL") or \
           (f in ("C_ATTENTION", "C_COVERAGE", "C_SELECTION", "C_ADAPT") and a == "cbramod")
moves = []  # (src, dst, kind)
def add(src, dst, kind):
    moves.append((src, dst, kind))
for p in glob.glob(O + "/units/*.json"):
    b = os.path.basename(p); e = b.replace(".FAILED.json", "").replace(".json", "")
    if affected(e): add(p, f"{L}/units/{b}", "unit_record")
aff = {os.path.basename(s).replace(".FAILED.json", "").replace(".json", "") for s, _, k in moves}
for p in glob.glob(O + "/canon/*"):
    if open(p).read().strip() in aff: add(p, f"{L}/canon/{os.path.basename(p)}", "canon_pointer")
for p in glob.glob(O + "/logs/units/*.log"):
    e = os.path.basename(p)[:-4]
    if affected(e): add(p, f"{L}/logs_units/{os.path.basename(p)}", "unit_log")
for q in ("queue_fm",):
    for p in glob.glob(f"{O}/pool/{q}/*"):
        b = os.path.basename(p)
        if b.startswith(".") or os.path.isdir(p) and not b.endswith(".claim"): continue
        e = b.rsplit(".", 1)[0]
        if affected(e) and not (b.endswith(".failed") and "DESCOPED" in open(p).read()): add(p, f"{L}/pool_{q}/{b}", "pool_marker")
for p in glob.glob(O + "/pool/queue_lrsel/*") + [O + "/queue_lrsel.txt"]:
    if os.path.exists(p): add(p, f"{L}/pool_queue_lrsel/{os.path.basename(p)}", "lrsel_state")
for p in glob.glob(O + "/fm_recipe/*"): add(p, f"{L}/fm_recipe/{os.path.basename(p)}", "recipe")
for p in glob.glob(O + "/donors/*"): add(p, f"{L}/donors/{os.path.basename(p)}", "donor")
for p in glob.glob(CK_REAL + "/*"):
    b = os.path.basename(p)
    if os.path.isdir(p): continue
    import re
    mm = re.match(r"^(ALN2_[A-Z_]+?_(?:fau|dtu|federici|private_bdf)_[0-9a-f]{16}|donor__\S+?__s\d+)", b)  # fixed 2026-10-09 (was split("_c"))
    e = mm.group(1) if mm else b
    if affected(e): add(p, f"{CK_LEG}/{b}", "checkpoint")
from collections import Counter
print("planned moves:", dict(Counter(k for _, _, k in moves)), "| affected unit ids:", len(aff))
if EXE:
    man = {"created": time.strftime("%Y-%m-%d %H:%M:%S"), "identifier": "legacy_chmean_v1",
           "reason": "foundation-model alignment head averaged backbone tokens over channels before projection (implementation receipt §11, §12)",
           "status_of_results": "documented channel-mean variant; excluded from primary foundation-model conclusions; not evidence against foundation models or the data's auditory content",
           "checkpoint_dir": CK_LEG, "unit_records": {}}
    for s, d, k in moves:
        if k == "unit_record":
            man["unit_records"][os.path.basename(s)] = hashlib.sha256(open(s, "rb").read()).hexdigest()
    for s, d, k in moves:
        os.makedirs(os.path.dirname(d), exist_ok=True); shutil.move(s, d)
    man["counts"] = dict(Counter(k for _, _, k in moves))
    json.dump(man, open(L + "/MANIFEST.json", "w"), indent=1)
    print("moved; manifest written")
