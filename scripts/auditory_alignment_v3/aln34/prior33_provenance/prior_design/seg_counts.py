"""Read-only: SparrKULee segment counts under the PUBLIC_PRIOR_DESIGN segment rule (runtable.json from the scout; no data read)."""
import collections, json, sys
RT = json.load(open(sys.argv[1])); runs = RT["runs"]
RES = set("019 020 021 022 026".split()); BAD = {("051", "audiobook_12_2"), ("011", "audiobook_6_1")}
ROLE = {"shortstories01": "fit", "varyingStories05": "dev", "varyingStories06": "dev", "varyingStories07": "bridge_cal"}
FAM = {s: "audiobook_1" for s in ("audiobook_1", "audiobook_1_1", "audiobook_1_2", "audiobook_1_1_shifted", "audiobook_1_2_shifted", "audiobook_1_artefact")}
role_of = lambda ses: ROLE.get(ses, "fit")
i_of = lambda k: (64 * k + 25) // 50
G0, GE_ENV, GE_EEG, SEG_T, SEG_S = 128, 41, 128, 250, 320
EEG_SPAN, ENV_SPAN = i_of(249) + 38, i_of(249) + 8   # 357, 327 samples from the segment start
assert (EEG_SPAN, ENV_SPAN) == (357, 327) and all(i_of(k + 25) == i_of(k) + 32 for k in range(0, 5000))
def seg_starts(T_env, T_eeg):
    out, s = [], G0  # 128 = 4 x 32: tick 100
    while s + ENV_SPAN <= T_env - GE_ENV and s + EEG_SPAN <= T_eeg - GE_EEG:
        out.append(s); s += SEG_S
    return out
for pol in ("P2", "P1"):
    keep = [r for r in runs if r["stim"] != "audiobook_1_artefact" and (r["sub"], r["stim"]) not in BAD and (pol == "P1" or r["sub"] not in RES)]
    keep = [r for r in keep if not (FAM.get(r["stim"]) == "audiobook_1" and role_of(r["ses"]) != "fit")]
    by_p = collections.defaultdict(list)
    for r in keep:
        by_p[(role_of(r["ses"]), r["stim"])].append(r)
    tot = collections.Counter(); subs = collections.defaultdict(set)
    for (role, p), rs in by_p.items():
        segsets = {r["sub"]: set(seg_starts(r["env_len"], r["shape"][1])) for r in rs}
        allseg = collections.Counter(s for v in segsets.values() for s in v)
        elig = {s for s, c in allseg.items() if c >= 2}
        n_list = sum(len(v & elig) for v in segsets.values())
        tot[(role, "listener_segments")] += n_list; tot[(role, "content_segments")] += len(elig)
        tot[(role, "pair_segments")] += sum(c * (c - 1) // 2 for s, c in allseg.items() if c >= 2)
        if elig:
            subs[role] |= {u for u, v in segsets.items() if v & elig}; tot[(role, "presentations")] += 1
    for role in ("fit", "dev", "bridge_cal"):
        ls = tot[(role, "listener_segments")]
        print(pol, role, "participants", len(subs[role]), "presentations", tot[(role, "presentations")], "listener_segments", ls,
              f"({ls*5/3600:.1f} h)", "content_segments", tot[(role, "content_segments")], f"({tot[(role,'content_segments')]*5/3600:.2f} h)",
              "anchor_ticks", tot[(role, "content_segments")] * 250)
    nf = tot[("fit", "listener_segments")]
    print(pol, "S0 steps (30 x 8 x N_seg / 256) =", -(-30 * 8 * nf // 256), "; per epoch-equivalent", 8 * nf, "anchors =", -(-8 * nf // 256), "steps")
# participant-balanced share of audiobook_1 in the P2 fit pool
keep = [r for r in runs if r["stim"] != "audiobook_1_artefact" and (r["sub"], r["stim"]) not in BAD and r["sub"] not in RES and role_of(r["ses"]) == "fit"]
by_p = collections.defaultdict(list)
for r in keep:
    by_p[r["stim"]].append(r)
per_sub = collections.defaultdict(collections.Counter)
for p, rs in by_p.items():
    segsets = {r["sub"]: set(seg_starts(r["env_len"], r["shape"][1])) for r in rs}
    cnt = collections.Counter(s for v in segsets.values() for s in v)
    for u, v in segsets.items():
        per_sub[u][FAM.get(p, p)] += sum(1 for s in v if cnt[s] >= 2)
tot = {u: sum(c.values()) for u, c in per_sub.items()}
tot = {u: t for u, t in tot.items() if t > 0}
share = sum(per_sub[u]["audiobook_1"] / t for u, t in tot.items()) / len(tot)
v = sorted(tot.values())
print(f"P2 fit: participants with eligible segments {len(tot)}; segments per participant min {v[0]} median {v[len(v)//2]} max {v[-1]}; "
      f"participant-balanced audiobook_1 share {share:.3f}; listener-window share {sum(c['audiobook_1'] for c in per_sub.values())/sum(tot.values()):.3f}")
