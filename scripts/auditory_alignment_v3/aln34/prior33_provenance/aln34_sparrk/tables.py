"""Read-only: compact per-presentation anchor table (P1 and P2), pair statistics inside the proposed fit split, epoch-equivalent sizes."""
import collections, itertools, json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RT = json.load(open(os.path.join(HERE, "runtable.json"))); runs = RT["runs"]
RES = set("019 020 021 022 026".split()); BAD = {("051", "audiobook_12_2"), ("011", "audiobook_6_1")}
ROLE = {"varyingStories05": "dev", "varyingStories06": "dev", "varyingStories07": "bridge_cal"}
FAM = {s: "audiobook_1" for s in ("audiobook_1", "audiobook_1_1", "audiobook_1_2", "audiobook_1_1_shifted", "audiobook_1_2_shifted", "audiobook_1_artefact")}
OFFSET = {"audiobook_1_1": 1711, "audiobook_1_1_shifted": 1711, "audiobook_1_2": 30986, "audiobook_1_2_shifted": 30986, "audiobook_1_artefact": 0, "audiobook_1": 0}
VARIANT = {"audiobook_1_1_shifted": "voice_shifted", "audiobook_1_2_shifted": "voice_shifted", "audiobook_1_artefact": "insertphone_artefact"}
def ticks(Te): return (50 * (Te - 8) + 24) // 64 + 1
Te = {r["stim"]: r["env_len"] for r in runs}
pres = {}
for r in runs:
    e = r["events"][0] if r["events"] else None
    p = pres.setdefault(r["stim"], {"P1": set(), "P2": set(), "ses": set(), "fields": collections.Counter()})
    p["ses"].add(r["ses"]); p["fields"][(e["condition"], e["snr"], "noise" if e["noise_file"] != "n/a" else "-", e["video_file"]) if e else "NO_EVENTS"] += 1
    if r["stim"] != "audiobook_1_artefact" and (r["sub"], r["stim"]) not in BAD:
        p["P1"].add(r["sub"])
        if r["sub"] not in RES: p["P2"].add(r["sub"])
lines = []
for s in sorted(pres, key=lambda s: (min(pres[s]["ses"]), s)):
    p = pres[s]; K = ticks(Te[s]); n1, n2 = len(p["P1"]), len(p["P2"])
    f = [k for k in p["fields"] if k != "NO_EVENTS"]
    cond = f"{f[0][0]}@{f[0][1]}" if len(f) == 1 else str(f)
    lines.append(f"| {s} | {FAM.get(s, s)} (+{OFFSET.get(s, 0)}) | {VARIANT.get(s, 'normal')} | {cond} | {','.join(sorted(x.replace('varyingStories','vS').replace('shortstories01','ss01') for x in p['ses']))} | {Te[s]/64:.1f} | {K} | {n1}/{n2} | {K*n1*(n1-1)//2/1e6:.3f} | {K*n2*(n2-1)//2/1e6:.3f} |")
open(os.path.join(HERE, "presentation_table.md"), "w").write("\n".join(lines))
print(len(lines), "rows written")
# fit-split pair stats (P1 and P2)
for pol in ("P1", "P2"):
    fit_runs = [r for r in runs if r["stim"] != "audiobook_1_artefact" and (r["sub"], r["stim"]) not in BAD and (pol == "P1" or r["sub"] not in RES) and ROLE.get(r["ses"], "fit") == "fit"]
    S = collections.defaultdict(set)
    for r in fit_runs: S[r["sub"]].add(r["stim"])
    L = collections.Counter(r["stim"] for r in fit_runs)
    sh = []
    for a, b in itertools.combinations(sorted(S), 2):
        c = [s for s in S[a] & S[b] if L[s] >= 2]
        sh.append(sum(ticks(Te[s]) for s in c) / 50 / 60)
    sh = np.array(sh)
    seg_l = sum((r["env_len"] - 8) // 320 for r in fit_runs if L[r["stim"]] >= 2)
    seg_c = sum((Te[s] - 8) // 320 for s in L if L[s] >= 2)
    print(f"{pol} fit: participants {len(S)}, pairs {len(sh)}, sharing>=1 {int((sh > 0).sum())}, shared minutes q: min {sh.min():.1f} q25 {np.quantile(sh, .25):.1f} med {np.median(sh):.1f} q75 {np.quantile(sh, .75):.1f} max {sh.max():.1f}; "
          f"listener 5-s segments (eligible) {seg_l:,}; content 5-s segments {seg_c:,}; listener-windows at 20 ms {sum(ticks(r['env_len']) for r in fit_runs if L[r['stim']] >= 2):,}")
