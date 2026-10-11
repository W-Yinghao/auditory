"""One-screen ALN3 fleet status for the monitoring loop (read-only; file names, record status fields and logs only).
Active rows = plan + plan_ext minus deferred_redundant (unless PANEL_V30_RESUME). Prints per-family done/total for families with
work left, the last-hour completion rate and a naive ETA, the B/C breadth milestone (seed 3401) that gates the D policy arms,
failure markers, worker / refresher liveness, checkpoint offload state and storage."""
import collections
import glob
import json
import os
import subprocess
import sys
import time

sys.dont_write_bytecode = True
os.chdir("/home/infres/yinwang/EEG_auditory")
sys.path.insert(0, os.getcwd())
from auditory_alignment_v3 import run as r3  # noqa: E402

O = "private/auditory_alignment_v3"
DEF = f"{O}/governance/deferred_redundant_v30_panel.json"
deferred = set(json.load(open(DEF))["ids"]) if os.path.exists(DEF) and not os.path.exists(f"{O}/PANEL_V30_RESUME") else set()
rows = [r for r in r3.all_rows() if r["experiment_id"] not in deferred]
now = time.time()
fam = collections.defaultdict(lambda: [0, 0]); recent = 0; tech_failed = 0
bc = collections.defaultdict(lambda: [0, 0])
for r in rows:
    p = f"{O}/units/{r['experiment_id']}.json"
    done = os.path.exists(p)
    fam[r["family_id"]][1] += 1
    if done:
        fam[r["family_id"]][0] += 1
        if now - os.path.getmtime(p) < 3600:
            recent += 1
    if os.path.exists(f"{O}/units/{r['experiment_id']}.FAILED.json"):
        tech_failed += 1
    if r["family_id"] in ("B_DENSE", "C_COMPLEMENT") and r["seed"] == 3401:
        bc[r["family_id"]][1] += 1; bc[r["family_id"]][0] += done
tot_d = sum(v[0] for v in fam.values()); tot = sum(v[1] for v in fam.values())
left = {f: v for f, v in fam.items() if v[0] < v[1]}
unbound = {"F_SCIENCE"} | {f for f in left if f.startswith("D_") and fam[f][0] == 0}
print(f"{time.strftime('%H:%M')} active {tot_d}/{tot} ({100 * tot_d / tot:.1f}%), last hour +{recent}"
      + (f", naive ETA {(tot - tot_d) / recent:.0f} h" if recent else ""))
print("  left:", ", ".join(f"{f} {d}/{t}" for f, (d, t) in sorted(left.items())))
print("  B/C breadth s3401:", ", ".join(f"{f} {d}/{t}" for f, (d, t) in sorted(bc.items())),
      "-> D policy arms can be bound" if bc and all(d == t for d, t in bc.values()) else "")
F = glob.glob(f"{O}/pool/*/*.failed")
nf = [f for f in F if "DESCOPED" not in open(f, errors="ignore").read()]
print(f"  failed markers (non-DESCOPED) {len(nf)}; technical_failed records {tech_failed}")
sq = subprocess.run(["squeue", "-u", os.environ.get("USER", "yinwang"), "-h", "-o", "%j|%T|%q"], capture_output=True, text=True).stdout.split()
c = collections.Counter(tuple(x.split("|")[:2]) for x in sq)
print("  jobs:", ", ".join(f"{j}:{s} {n}" for (j, s), n in sorted(c.items()) if j.startswith(("c3_", "sci_r1"))) or "none",
      "| other-project normal-QOS jobs", sum(1 for x in sq if x.split("|")[2] == "normal" and not x.split("|")[0].startswith(("c3_", "sci_r1"))))
age = now - os.path.getmtime(f"{O}/logs/refresh.log")
print(f"  refresh.log age {age / 60:.0f} min")
log = [l.strip() for l in open(f"{O}/logs/ckpt_offload.log") if " pass" in l or "ERROR" in l]
print("  offload:", log[-1][:160] if log else "no pass yet", "| ERROR lines", sum("ERROR" in l for l in log))
du = subprocess.run(["du", "-sk", f"{O}/ckpt"], capture_output=True, text=True).stdout.split()
df = subprocess.run(["df", "-h", "--output=avail,pcent", "/projects/EEG-foundation-model"], capture_output=True, text=True).stdout.split()
print(f"  home ALN3 ckpt real files {int(du[0]) / 2 ** 20:.1f} GiB | /projects avail {df[-2]} ({df[-1]} used)" if du and df else "  storage: n/a")
