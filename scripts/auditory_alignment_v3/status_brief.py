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
HOLD = f"{O}/families_on_hold.json"  # families make_queue.py leaves out (2026-10-14: ETA counts only rows that can run)
held = set(json.load(open(HOLD))) if os.path.exists(HOLD) else set()
HELD_EX = f"{O}/governance/held_executions.json"  # ALN3.2 (2026-10-14 16:49): execution-specific hold, ids make_queue.py skips
held_ids = set(json.load(open(HELD_EX))["ids"]) if os.path.exists(HELD_EX) else set()
nheld = collections.Counter()
now = time.time()
fam = collections.defaultdict(lambda: [0, 0]); recent = 0; tech_failed = 0
bc = collections.defaultdict(lambda: [0, 0])
for r in rows:
    p = f"{O}/units/{r['experiment_id']}.json"
    done = os.path.exists(p)
    fam[r["family_id"]][1] += 1
    if not done and (r["family_id"] in held or r["experiment_id"] in held_ids):
        nheld[r["family_id"]] += 1
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
runnable = sum(t - d - nheld[f] for f, (d, t) in fam.items())
print(f"{time.strftime('%H:%M')} active {tot_d}/{tot} ({100 * tot_d / tot:.1f}%), last hour +{recent}"
      + f", runnable (not held) left {runnable}" + (f", naive ETA {runnable / recent:.0f} h" if recent and runnable else ""))
print("  left:", ", ".join(f"{f} {d}/{t}" + (" HELD" if f in held else f" ({nheld[f]} held)" if nheld[f] else "") for f, (d, t) in sorted(left.items())))
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
df = subprocess.run(["df", "-B1", "--output=avail,used,size", "/projects/EEG-foundation-model"], capture_output=True, text=True).stdout.split()
av, us, sz = (int(x) for x in df[-3:])
log_p = f"{O}/logs/projects_free_gib.tsv"  # trend of the shared volume (other users write to it too)
prev = [l.split() for l in open(log_p)] if os.path.exists(log_p) else []
open(log_p, "a").write(f"{int(now)}\t{av / 2**30:.1f}\n")
rate = ""
if prev:
    t0, a0 = float(prev[max(0, len(prev) - 6)][0]), float(prev[max(0, len(prev) - 6)][1])
    if now - t0 > 1200:
        r = (a0 - av / 2**30) / ((now - t0) / 3600)
        rate = f", trend {r:+.1f} GiB/h consumed" + (f" -> full in ~{(av / 2**30) / r:.0f} h" if r > 0 else "")
print(f"  home ALN3 ckpt real files {int(du[0]) / 2 ** 20:.1f} GiB | /projects avail {av / 2**30:.0f} GiB ({100 * us / sz:.1f}% used{rate})" if du else "  storage: n/a")
