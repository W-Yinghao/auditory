"""Read-only: numbers for a session-block donor split (fit / dev / bridge_cal) by participant AND physical content."""
import collections, itertools, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
RT = json.load(open(os.path.join(HERE, "runtable.json"))); runs = RT["runs"]
RES = set("019 020 021 022 026".split()); BAD = {("051", "audiobook_12_2"), ("011", "audiobook_6_1")}
ROLE_OF_SES = {"shortstories01": "fit", "varyingStories01": "fit", "varyingStories02": "fit", "varyingStories03": "fit", "varyingStories04": "fit",
               "varyingStories08": "fit", "varyingStories09": "fit", "varyingStories10": "fit",
               "varyingStories05": "dev", "varyingStories06": "dev", "varyingStories07": "bridge_cal"}
FAMILY = {s: "audiobook_1" for s in ("audiobook_1", "audiobook_1_1", "audiobook_1_2", "audiobook_1_1_shifted", "audiobook_1_2_shifted", "audiobook_1_artefact")}
def fam(s): return FAMILY.get(s, s)
def ticks(Te): return (50 * (Te - 8) + 24) // 64 + 1
content_role = {}
for r in runs:  # content family -> set of roles of the sessions in which it was heard
    content_role.setdefault(fam(r["stim"]), set()).add(ROLE_OF_SES[r["ses"]])
SHARED_TO = {"audiobook_1": "fit"}  # a content heard in several roles is kept only in this role
for pol, excl in (("P1", lambda r: False), ("P2", lambda r: r["sub"] in RES)):
    keep = [r for r in runs if r["stim"] != "audiobook_1_artefact" and (r["sub"], r["stim"]) not in BAD and not excl(r)]
    out = collections.defaultdict(lambda: {"subs": set(), "runs": 0, "eeg_h": 0.0, "pres": collections.defaultdict(set)})
    dropped = collections.Counter()
    for r in keep:
        role = ROLE_OF_SES[r["ses"]]; f = fam(r["stim"])
        roles = content_role[f]
        if len(roles) > 1 and SHARED_TO.get(f) != role:
            dropped[(role, f)] += 1; continue
        assert len(roles) == 1 or SHARED_TO.get(f) == role
        o = out[role]; o["subs"].add(r["sub"]); o["runs"] += 1; o["eeg_h"] += r["shape"][1] / 64 / 3600; o["pres"][r["stim"]].add(r["sub"])
    print(pol, "dropped runs (role, content):", dict(dropped))
    for role in ("fit", "dev", "bridge_cal"):
        o = out[role]; P = o["pres"]
        elig = {s: v for s, v in P.items() if len(v) >= 2}
        Te = {r["stim"]: r["env_len"] for r in runs}
        anchors = sum(ticks(Te[s]) for s in elig); lw = sum(ticks(Te[s]) * len(v) for s, v in elig.items())
        pairs = sum(ticks(Te[s]) * len(v) * (len(v) - 1) // 2 for s, v in elig.items())
        fams = sorted({fam(s) for s in P})
        print(f"  {role:10s} participants {len(o['subs']):2d} runs {o['runs']:3d} EEG {o['eeg_h']:6.1f} h | presentations {len(P)} (>=2 listeners {len(elig)}) | "
              f"anchors {anchors/50/3600:5.2f} h content ({anchors:,}) | listener-windows {lw/50/3600:6.1f} h | pairs {pairs/1e6:7.2f} M | single-listener: {sorted(s for s in P if len(P[s]) < 2)}")
        if role != "fit": print("     contents:", fams)
