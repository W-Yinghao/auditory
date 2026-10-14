"""BC_PROBE_PLAN_20261014 P0 (CPU): levels of the existing seed-3401 B_LAYER_PROBE units (frozen backbone, training-side ridge)
and pointwise contrasts against the same-fold local model (NCE, CS_SINGLE) and the frozen B phase-linear readout (NCE), with the
ADDENDUM_05 functions. Writes private/auditory_alignment_v3/probe_bc/probe_layers.json."""
import json, os, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import bc_interim as BI, core, run as R3


def cfg(r):
    s, f, ds = r["spec"], r["family_id"], r["dataset"]
    if r["seed"] != BI.SEED or ds not in BI.DS:
        return None
    if f == "B_LAYER_PROBE":
        return ("P", ds, "RIDGE", s["architecture"], s["layer"])
    if f == "A_LOCAL" and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full" and s.get("projection_dim", 32) == 32:
        return ("L", ds, s["objective"])
    if f == "B_DENSE" and s["adaptation"] == "pretrained_frozen" and s["readout"] == "channel_phase_linear" and s["objective"] == "NCE":
        return ("B", ds, "NCE", s["architecture"], "pretrained_frozen", "channel_phase_linear")
    return None


BI.cfg_of = cfg
rows = R3.all_rows()
data = BI.load_continuous(rows, BI.unit_loader(), BI.load_manifest())
notes = list(data["notes"]); vals = data["vals"]
out = {"status": {f"{k[0]}|{k[1]}": v for k, v in data["status"].items()}, "levels": BI.levels(vals, sorted(vals, key=BI.ckey), list(BI.DIRECTION), "p0", notes), "contrasts": {}}
for ds in BI.DS:
    for a in BI.ARCH:
        for layer in ("patch_embedding", "middle", "last"):
            P = ("P", ds, "RIDGE", a, layer)
            for refname, ref in (("local_NCE", ("L", ds, "NCE")), ("local_CS", ("L", ds, "CS_SINGLE")), ("B1_frozen_NCE", ("B", ds, "NCE", a, "pretrained_frozen", "channel_phase_linear"))):
                why = BI.pair_ok(data, ref, P)
                if why:
                    notes.append(f"{ds}/{a}/{layer} vs {refname}: {why}"); continue
                lab = f"P0|{ds}|{a}|{layer}|{refname}"
                out["contrasts"][lab] = {m: BI.run_family(lab, [(layer, ref, P, refname)], vals, m, notes, False)["members"].get(layer) for m in (BI.PRIMARY, "unified/gain_bits", "unified/regular/top1")}
out["notes"] = notes
BI.write_json(os.path.join(core.OUT, "probe_bc", "probe_layers.json"), out, private=True)
for k, r in out["levels"].items():
    R = r.get(BI.PRIMARY, {}); gn = r.get("unified/gain_bits", {})
    print(f"{k:60s} n={r['n']:3d} R={R.get('est', float('nan')):.3f} [{R.get('ci_low', float('nan')):.3f},{R.get('ci_high', float('nan')):.3f}] gain={gn.get('est', float('nan')):.3f}")
for k, c in out["contrasts"].items():
    m = c[BI.PRIMARY]
    if m:
        print(f"{k:55s} dR={m['est']:+.3f} [{m['ci_low']:+.3f},{m['ci_high']:+.3f}]  dgain={c['unified/gain_bits']['est']:+.3f}")
print("pairing notes:", len([n for n in notes if 'vs' in n]))
