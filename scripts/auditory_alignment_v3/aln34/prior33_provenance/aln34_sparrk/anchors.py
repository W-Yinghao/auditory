"""Cross-person anchor index counts for aln33_env64_125ms_v1 on SparrKULee (read-only; uses runtable.json from runtable.py).
tick k: requested t_k = 0.020 k s, sample i_k = round(1.28 k) = (64 k + 25) // 50 (no ties at 64 Hz / 20 ms); target [i_k, i_k + 8),
EEG input [i_k, i_k + 38). Eligible tick of a run: i_k + 8 <= T_env and i_k + 38 <= T_eeg. Positive key = (sparrkulee, content_id,
presentation_id, condition, attended_stream='single', tick); presentation_id = stimulus file (each file has one presentation in the
observed events). Policies: P0 = all 666 runs; P1 = P0 minus artefact run, minus 2 unverified-alignment runs; P2 = P1 minus the 5
access-restricted participants (no events.tsv)."""
import collections, itertools, json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
RT = json.load(open(os.path.join(HERE, "runtable.json"))); runs = RT["runs"]
RES = set("019 020 021 022 026".split()); BADALIGN = {("051", "audiobook_12_2"), ("011", "audiobook_6_1")}
def ticks(T_env, T_eeg):
    kmax_env = (50 * (T_env - 8) + 24) // 64  # largest k with (64k+25)//50 <= T_env-8  -> verify below
    ks = np.arange(0, kmax_env + 3); i = (64 * ks + 25) // 50
    ok = (i + 8 <= T_env) & (i + 38 <= T_eeg)
    assert np.array_equal(i, np.round(ks * 0.020 * 64).astype(int))
    return int(ok.sum()), i[ok]
pol = {"P0_all": lambda r: True,
       "P1_minus_artefact_and_unaligned": lambda r: r["stim"] != "audiobook_1_artefact" and (r["sub"], r["stim"]) not in BADALIGN,
       "P2_P1_minus_restricted": lambda r: r["stim"] != "audiobook_1_artefact" and (r["sub"], r["stim"]) not in BADALIGN and r["sub"] not in RES}
res = {}
for pname, f in pol.items():
    R = [r for r in runs if f(r)]
    by = collections.defaultdict(list)
    for r in R: by[r["stim"]].append(r)
    per = {}
    for s, rr in by.items():
        Te = rr[0]["env_len"]; K = min(ticks(Te, r["shape"][1])[0] for r in rr)
        n = len({r["sub"] for r in rr})
        per[s] = {"listeners": n, "ticks": K, "env_s": Te / 64, "anchors_eligible": K if n >= 2 else 0, "listener_windows": K * n,
                  "pairs_unordered": K * n * (n - 1) // 2, "eeg_h": sum(r["shape"][1] for r in rr) / 64 / 3600}
    tot = {k: sum(v[k] for v in per.values()) for k in ("ticks", "anchors_eligible", "listener_windows", "pairs_unordered")}
    elig_lw = sum(v["listener_windows"] for v in per.values() if v["listeners"] >= 2)
    unused = {s: v for s, v in per.items() if v["listeners"] < 2}
    subs = sorted({r["sub"] for r in R}); S = {p: {r["stim"] for r in R if r["sub"] == p} for p in subs}
    pairshared = {}
    for p, q in itertools.combinations(subs, 2):
        sh = S[p] & S[q]
        if sh: pairshared[(p, q)] = sum(per[s]["ticks"] for s in sh)
    v = np.array(list(pairshared.values())) / 50 / 60  # minutes of shared content (20 ms ticks)
    persub = {p: sum(per[s]["ticks"] for s in S[p] if per[s]["listeners"] >= 2) / 50 / 3600 for p in subs}
    res[pname] = {"runs": len(R), "participants": len(subs), "stimuli": len(per), "stimuli_ge2": sum(v_["listeners"] >= 2 for v_ in per.values()),
                  "eeg_hours": sum(r["shape"][1] for r in R) / 64 / 3600, "totals": tot, "eligible_listener_windows": elig_lw,
                  "eligible_listener_hours_at_tick_rate": elig_lw / 50 / 3600, "eligible_anchor_hours": tot["anchors_eligible"] / 50 / 3600,
                  "unused_single_listener": {s: {"listeners": v_["listeners"], "env_s": round(v_["env_s"], 1)} for s, v_ in unused.items()},
                  "participant_pairs_total": len(subs) * (len(subs) - 1) // 2, "participant_pairs_sharing": len(pairshared),
                  "pair_shared_minutes_quantiles": dict(zip(("min", "q25", "median", "q75", "max"), np.round(np.quantile(v, [0, .25, .5, .75, 1]), 1).tolist())),
                  "pairs_sharing_only_audiobook_1": sum(1 for (p, q) in pairshared if S[p] & S[q] == {"audiobook_1"}),
                  "eligible_hours_per_participant_quantiles": dict(zip(("min", "median", "max"), np.round(np.quantile(list(persub.values()), [0, .5, 1]), 2).tolist())),
                  "per_stimulus": per}
    print(pname, json.dumps({k: v_ for k, v_ in res[pname].items() if k != "per_stimulus"}, default=float)[:1500])
json.dump(res, open(os.path.join(HERE, "anchors.json"), "w"), indent=1, default=float)
# tick-grid facts
ks = np.arange(0, 50); i = (64 * ks + 25) // 50
print("first ticks i_k:", i[:16].tolist(), "steps:", collections.Counter(np.diff((64 * np.arange(0, 5000) + 25) // 50).tolist()))
err = ((64 * np.arange(0, 100000) + 25) // 50) / 64 - 0.020 * np.arange(0, 100000)
print("actual - requested time (ms): min %.4f max %.4f mean %.5f, distinct %d" % (err.min() * 1e3, err.max() * 1e3, err.mean() * 1e3, len(np.unique(np.round(err * 1e6)))))
