import json, os, glob, time
R=[json.loads(l) for l in open("../../AUDITORY_ALIGNMENT_NEXT_SERVER_PACKAGE_v2_20261006/plans/planned_comparisons.jsonl")]
SC=json.load(open("seed_scope.json")); PN=SC["panel"]
inpan=lambda r: r["seed"] in PN["seeds"] and r["family_id"] in PN["families"] and r["spec"].get("objective")==PN["objective"] and r["spec"].get("adaptation") in PN["adaptations"]
scope=[r for r in R if r["seed"] in SC["seeds"] or r["family_id"] in SC["exempt_families"] or inpan(r)]
while True:
    left=[r["experiment_id"] for r in scope if not os.path.exists(f"units/{r['experiment_id']}.json")]
    real=[p for p in glob.glob("pool/*/*.failed") if "DESCOPED" not in open(p).read()]
    if real: print("FAILED", real); break
    if not left: print("ALL IN-SCOPE UNITS COMPLETE", len(scope), time.strftime("%H:%M")); break
    time.sleep(120)
