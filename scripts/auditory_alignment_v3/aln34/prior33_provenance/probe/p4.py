import sys, json, os, glob, collections
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import core
from auditory_alignment_v3.registry import FAMILY_CODE, FAMILY_GROUP
U = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/units"
now = {f: core.code_hash(f) for f in FAMILY_GROUP}
# latest record hash per family (by mtime) vs current
latest = {}
for p in sorted(glob.glob(U + "/ALN3*.json"), key=os.path.getmtime)[-3000:]:
    if p.endswith(".FAILED.json"): continue
    try: d = json.load(open(p))
    except Exception: continue
    f = d.get("row", {}).get("family_id"); latest[f] = (d.get("code_hash"), d.get("code_group"))
for f, (h, g) in sorted(latest.items(), key=lambda x: str(x[0])):
    print(f, "group", g, "last-record hash", h, "current", now.get(f), "MATCH" if h == now.get(f) else "differs")
files = sorted({x for g in FAMILY_CODE.values() for x in g} | set(core.V2_DEPS))
print("files hashed by every group:", [f"{d}/{f}" for d, f in core.V2_DEPS] + ["auditory_alignment_v3/core.py", "auditory_alignment_v3/local_train.py"])
