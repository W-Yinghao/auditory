"""M2e tests: the C6 manifest builder (auditory_alignment_v3/prior33/manifest.py; PUBLIC_PRIOR_DESIGN.md §2.3, §2.5, §3, §6.2 C6,
§6.6 M2e). Synthetic data only: the shared fixture (fixtures.make_synthetic_manifest, scale 4) is converted into the outputs of the
real builders in their own schemas (C1 runs_table.json, C2 align_audit.jsonl + meta, C4 runs.json / streams.json, C5 pieces.json /
streams.json with cache done records, C3 scan_audio.json + latest pointer, later C7 rich_build.json / rich_streams.json):
cohort-local provisional ids, presentation keys, provisional families (C4's declared offsets, C5's pending_C3 clocks, DTU's
duplicate as its own family), and ALN3 A_LOCAL / E_LOCAL records and a plan for the cell check. The fixture's manifest is the
reference.

Covered: the id mapping (presentation_key -> one global id space, C3's families / offsets / clocks over the provisional ones,
cohort-local table ids untouched); the 30 cells (public from the tables against the ALN3 records, private from the E_LOCAL
records) and their split hashes; leave-target-out donor pools and donor sets equal to the fixture's (strata, n_segments, weights,
overlap exclusions; DTU HI, the phantom, restricted participants never in a pool); the declared exclusions present (restricted,
C2 misaligned, structural, a declared run, README, the DTU loader filter) with C2 'unverifiable' runs kept; the sha256 of every
described file; core first (no C7 file anywhere) and the rich supplement after synthetic C7 outputs; the public / full copies
(private children only in the full copy); views.open_manifest, DonorBank, target_view, DonorSampler, selection_sets and
bridge_rows on the output; the guards (restricted rows, inconsistent inputs, a stale C3 pointer, output locations, results
already present), a dry run and the CLI. Review round 2: the full copy's location (the consumers' PRIVATE_MANIFEST) and
open_for_row (falls through the public copy, merges the rich supplement a row quotes, refuses a RICH_DONOR row without one); C3
entries no cached presentation plays (mapped by code, unplayed listed, unknown refused) and C3's caveats (not scanned,
identity overlap unverifiable); ignored streams without a C3 row; the DTU trials of an unread file declared with the file's
reason; unverifiable_kept over donor roles only; a declaration's cited file sha256 and C2 numbers checked; the per-participant
2-8 Hz derivation equal to one with_band_sd call; the rich supplement's production guard; declared_choices. CPU only; about
1-2 minutes."""
import collections
import copy
import hashlib
import json
import os
import shutil
import sys

import numpy as np
import pytest

from auditory_alignment_v3.prior33 import contract as C
from auditory_alignment_v3.prior33 import manifest as M

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixtures as FX  # noqa: E402

SCALE = 4
SK_NOISE = {"podcast_2": ("in_noise", -4.0)}                       # one SparrKULee presentation with another acoustic condition
UNVERIFIABLE_KEPT = (("003", "podcast_2"), ("004", "audiobook_2_1"))  # fit runs that C2 classes unverifiable: they stay (F11)
DECLARED_TEST = ({"cohort": "sparrkulee", "sub": "052", "stimulus": "podcast_16", "rule": "declared_structural_exclusion",
                  "reason": "synthetic declared structural exclusion (test)"},)
DTU_FILTERED = {"participant": "sub-025", "trial": "trial_099", "group": "nh", "kind": "ss", "target_sha": "t99",
                "reason": "target sha not in content_groups.json"}
DTU_FILTERED_ROW = {"file": "sub-025", "trial": "trial_099", "subject": "sub-025", "hearing": "nh", "kind": "ss", "target_sha": "t99",
                    "status": "excluded", "reason": "target sha not in content_groups.json"}   # C5 lists a filtered trial here too
DTU_ABSENT = {"file": "sub-024_run-2", "trial": "trial_001", "subject": "sub-024", "hearing": "nh", "kind": "ss", "target_sha": "t08",
              "status": "unread_file", "reason": None}                                           # C5: the reason is the file's
DTU_UNREAD = {"file": "/synthetic/sub-024_run-2.h5", "reason": "not read by auditory_alignment.data.load_dtu (<subject>.h5 only)",
              "n_inventory_trials": 1}
RICH_FILES = ("rich_f32.npy", "rich_streams.json")


# ---------------------------------------------------------------------------------------------------------- helpers
def _load(path):
    with open(path) as f:
        return json.load(f)


def _dump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, sort_keys=True)


def _fsha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _link(src, dst):
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _quiet(*a, **k):
    pass


# ---------------------------------------------------------------------------------------------------------- the builder tree
def _sk_key(stim):
    nc, snr = SK_NOISE.get(stim, ("in_noise", 100.0))
    return f"sparrkulee:{stim}|{nc}|snr={snr:g}|noise=noise_{stim}.npz.gz", nc, snr


def _fau_key(p):
    return f"fau:{p['stimulus']}" if p["kind"] == "ss" else f"fau:{p['stimulus']}|side={p['attended_side']}"


def _registry(cohort, entries, fam_of):
    """Cohort-local registries as C4 / C5 write them: presentation ids = rank of the key, family ids = rank of the name."""
    keys = sorted(entries)
    lid = {k: i for i, k in enumerate(keys)}
    names = sorted({fam_of[k][0] for k in keys})
    fid = {n: i for i, n in enumerate(names)}
    reg = []
    for k in keys:
        e = entries[k]
        n, off, basis, clock = fam_of[k]
        reg.append({**e, "id": lid[k], "key": k, "cohort": cohort, "family": fid[n], "family_name": n, "family_offset": off,
                    "family_basis": basis, "offset_known": off is not None})
    fams = [{"id": fid[n], "cohort": cohort, "name": n, "clock": next(fam_of[k][3] for k in keys if fam_of[k][0] == n),
             "basis": next(fam_of[k][2] for k in keys if fam_of[k][0] == n), "members": [lid[k] for k in keys if fam_of[k][0] == n]}
            for n in names]
    return reg, fams, lid, fid


def build_tree(fx, root):
    """The C1 / C2 / C3 / C4 / C5 outputs of the fixture build under `root` (module docstring) -> info for the tests."""
    src, M0 = fx["root"], fx["manifest"]
    P = {p["id"]: p for p in M0["presentations"]}
    F = {f["id"]: f for f in M0["families"]}
    os.makedirs(root)
    info = {"key_of": {}, "phantom_keys": {}, "c3_name": {}}
    # ------------------------------------------------------------------ SparrKULee (C1, C2, C4)
    d0, d = os.path.join(src, "sparrkulee"), os.path.join(root, "sparrkulee")
    os.makedirs(d)
    for f in ("eeg_f16_tmajor.npy", "env_f32.npy"):
        _link(os.path.join(d0, f), os.path.join(d, f))
    t, st = _load(os.path.join(d0, "runs.json")), _load(os.path.join(d0, "streams.json"))
    decl = {p["stimulus"] for p in P.values() if p["cohort"] == "sparrkulee" and F[p["family"]]["name"] == "audiobook_1"}
    entries, fam_of = {}, {}
    for p in (q for q in P.values() if q["cohort"] == "sparrkulee"):
        k, nc, snr = _sk_key(p["stimulus"])
        info["key_of"][p["id"]] = k
        entries[k] = {"stimulus": p["stimulus"], "kind": "ss", "condition": "listeningActive", "noise_condition": nc, "snr": snr,
                      "noise_file": f"noise_{p['stimulus']}.npz.gz", "attended_side": None, "stream": p["stream"],
                      "ignored_stream": None, "ignored_lead": 0, "onset_s": None}
        if p["stimulus"] in decl:     # C4 declares the halves / copies; the artefact's offset is measured by C3 only
            fam_of[k] = ("sparrkulee:audiobook_1", None if p["stimulus"] == "audiobook_1_artefact" else p["family_offset"], "declared", "known")
        else:
            fam_of[k] = (f"sparrkulee:{p['stimulus']}", 0, "own", "known")
    reg, fams, lid, fid = _registry("sparrkulee", entries, fam_of)
    sub_runs = collections.Counter()
    runs, c1 = [], []
    for r in t["runs"]:
        r = copy.deepcopy(r)
        sub_runs[r["sub"]] += 1
        r.update(ses="shortstories01", run=f"{sub_runs[r['sub']]:02d}", task="listeningActive")
        rule = r["flags"][0] if r["flags"] else None
        restricted = r["role"] == "restricted"
        if restricted:
            r.update(presentation=None, presentation_key=None, family=None, family_name=None, family_offset=None)
        else:
            k = info["key_of"][r["presentation"]]
            n, off = fam_of[k][:2]
            r.update(presentation=lid[k], presentation_key=k, family=fid[n], family_name=n, family_offset=off,
                     noise_condition=entries[k]["noise_condition"], snr=entries[k]["snr"], noise_file=entries[k]["noise_file"])
        cls = r["audit"]["clock"]
        if (r["sub"], r["stimulus"]) in UNVERIFIABLE_KEPT:
            cls = "unverifiable"
        r["audit"] = {"clock": cls, "reason": None, "refs": [], "tau_hat": r["audit"].get("tau_hat"), "z": r["audit"].get("z")}
        r["structural"] = {"anomalous": rule == "structural_anomaly_unverified_clock", "delta": 64 if rule == "structural_anomaly_unverified_clock" else 0}
        r["role_c1"] = "fit" if r["role"] == "excluded_rule" else r["role"]
        runs.append(r)
        c1.append({"run_id": r["run_id"], "sub": r["sub"], "ses": r["ses"], "run": r["run"], "stimulus": r["stimulus"],
                   "role": r["role_c1"], "restricted": restricted, "flags": [], "structural": r["structural"],
                   "presentation_key": r["presentation_key"], "family_name": r.get("family_name")})
    rt = {"schema": "prior33_sparrkulee_runs_table_v1", "cohort": "sparrkulee", "contract": C.CONTRACT, "builder_sha256": "synthetic",
          "runs": c1, "readme_flagged": [list(x) for x in M.README_FLAGGED], "readme_flagged_absent": True,
          "restricted": list(M.RESTRICTED)}
    _dump(rt, os.path.join(d, "runs_table.json"))
    rt_sha = _fsha(os.path.join(d, "runs_table.json"))
    lines = []
    for r in runs:
        cls = "not_audited" if r["role"] == "restricted" else r["audit"]["clock"]
        lines.append(json.dumps({"run": r["run_id"], "sub": r["sub"], "ses": r["ses"], "stimulus": r["stimulus"], "class": cls,
                                 "tau": r["audit"].get("tau_hat"), "z": r["audit"].get("z"), "refs": [], "n_refs": 0, "reason": None,
                                 "runs_table_sha256": rt_sha, "builder_sha256": "synthetic"}, sort_keys=True))
    with open(os.path.join(d, "align_audit.jsonl"), "w") as f:
        f.write("\n".join(lines) + "\n")
    a_sha = _fsha(os.path.join(d, "align_audit.jsonl"))
    mis = [json.loads(x) for x in lines if json.loads(x)["class"] == "misaligned"]
    _dump({"schema": "prior33_sparrkulee_align_audit_v1", "contract": C.CONTRACT, "align_audit_sha256": a_sha, "runs_table_sha256": rt_sha,
           "classes": dict(collections.Counter(json.loads(x)["class"] for x in lines)),
           "misaligned": [{"run": m["run"], "tau": m["tau"], "z": m["z"]} for m in mis]}, os.path.join(d, "align_audit_meta.json"))
    parts = []
    for p in t["participants"]:
        p = copy.deepcopy(p)
        p.update(identity=p["participant"], dev=False, test_only=False, fold=-1, masked=[], sd_prez_uV=copy.deepcopy(p["sd_prez"]))
        parts.append(p)
    ci = {k: v for k, v in M0["cohorts"]["sparrkulee"].items() if k not in RICH_FILES and k not in ("rich", "rich_streams")}
    ci["unit"] = {"name": "uV", "source_unit": "uV", "factor_to_uV": 1.0, "basis": "synthetic"}
    srows = []
    for r in st["streams"]:
        r = copy.deepcopy(r)
        k = next((info["key_of"][q["id"]] for q in P.values() if q["cohort"] == "sparrkulee" and q["stream"] == r["stream"]), None)
        n = fam_of[k][0] if k else None
        r.update(family=None if n is None else fid[n], family_name=n, family_offset=None if k is None else fam_of[k][1])
        srows.append(r)
    _dump({"schema": "prior33_sparrkulee_streams_v1", "cohort": "sparrkulee", "id_space": M.ID_SPACE, "streams": srows},
          os.path.join(d, "streams.json"))
    _dump({"schema": "prior33_sparrkulee_runs_v1", "cohort": "sparrkulee", "contract": C.CONTRACT, "id_space": M.ID_SPACE,
           "participants": parts, "runs": runs, "presentations": reg, "families": fams, "cohort_info": ci, "unit": ci["unit"],
           "inputs": {"align_audit_sha256": a_sha, "runs_table_sha256": rt_sha}, "builder_sha256": "synthetic"},
          os.path.join(d, "runs.json"))
    # ------------------------------------------------------------------ FAU / DTU / Federici (C5)
    for c in M.PUBLIC:
        d0, d = os.path.join(src, c), os.path.join(root, c)
        os.makedirs(d)
        t, st = _load(os.path.join(d0, "pieces.json")), _load(os.path.join(d0, "streams.json"))
        info_c = M0["cohorts"][c]
        for m, f in info_c["caches"].items():
            _link(os.path.join(d0, f), os.path.join(d, f))
        _link(os.path.join(d0, "env_f32.npy"), os.path.join(d, "env_f32.npy"))
        entries, fam_of, key_of_piece = {}, {}, []
        for it in t["pieces"]:
            p = P[it["presentation"]]
            if c == "fau":
                k = _fau_key(p)
                prov = (f"fau:{it['stimulus']}", 0, "own", "known")
            elif c == "dtu":
                h = it["stimulus"]
                if p["kind"] == "cs":
                    k = f"dtu:{p['stimulus']}|side=None"
                elif it["group"] == "hi":
                    k = f"dtu:{h}|side=None|eq={it['participant']}/{it['trial']}"
                else:
                    k = f"dtu:{h}|side=None"
                prov = (f"dtu:{h}", 0, "own", "known")
            else:
                item = it["stimulus"]
                k = f"federici:{item}" + ("|phantom" if it["test_only"] else "")
                g = FX.FED_CG[item]
                multi = sum(v == g for v in FX.FED_CG.values()) > 1
                prov = (f"federici:g{g}", None if multi else 0, "content_group" if multi else "own", "pending_C3" if multi else "known")
                if it["test_only"]:
                    info["phantom_keys"][k] = p["id"]
            if not it["test_only"]:
                info["key_of"].setdefault(p["id"], k)
            key_of_piece.append(k)
            cond = "phantom" if (c == "federici" and it["test_only"]) else p["condition"]
            entries[k] = {"stimulus": p["stimulus"], "kind": p["kind"], "condition": cond, "attended_side": p["attended_side"],
                          "stream": p["stream"], "ignored_stream": p["ignored_stream"], "ignored_lead": p["ignored_lead"],
                          "onset_s": p["onset_s"]}
            fam_of[k] = prov
        reg, fams, lid, fid = _registry(c, entries, fam_of)
        pieces = []
        for it, k in zip(t["pieces"], key_of_piece):
            it = copy.deepcopy(it)
            n, off = fam_of[k][:2]
            it.update(presentation=lid[k], presentation_key=k, family=fid[n], family_name=n, family_offset=off, identity=it.get("identity"),
                      condition=entries[k]["condition"])
            if it["kind"] == "cs":
                it["segment_starts_guard_only"] = C.segment_starts(it["T_env"], it["T_eeg"], c).tolist()
            it["segment_starts_target_stage"] = it["segment_starts_guard_only"] if (it["kind"] == "cs" and c == "fau") else it["segment_starts"]
            if c == "dtu":
                half, es = FX.DTU_SPLIT[FX.DTU_GROUP[it["stimulus"]]]
                it.update(content_half=half, content_early_stop=es)
            if c == "federici":
                it["content_role"] = FX.FED_ROLE[FX.FED_CG[it["stimulus"]]]
            pieces.append(it)
        parts = []
        for p in t["participants"]:
            p = copy.deepcopy(p)
            if c in ("fau", "dtu"):
                p["sd_prez"]["A_2_8"] = [None if v is None else 0.37 * v for v in p["sd_prez"]["A"]]
            p.update(sd_prez_uV=copy.deepcopy(p["sd_prez"]), sd_prez_unit="uV")
            if c == "federici":
                p["phantom"] = bool(p["test_only"])
            parts.append(p)
        ci = {k: v for k, v in info_c.items() if k not in ("rich", "rich_streams")}
        ci["caches"] = dict(info_c["caches"])
        ci["unit"] = {"name": "uV", "source_unit": "uV", "factor_to_uV": 1.0, "basis": "synthetic"}
        ci["stats_band"] = {"fau": {"A": [1.0, 20.0], "B": [1.0, 20.0], "A_2_8": [2.0, 8.0]}, "dtu": {"A": [1.0, 20.0], "A_2_8": [2.0, 8.0]},
                            "federici": {"A": [2.0, 8.0]}}[c]
        caches = {}
        for m, f in info_c["caches"].items():
            mm = np.load(os.path.join(d, f), mmap_mode="r", allow_pickle=False)
            rec = {"schema": "prior33_public_cache_v1", "cohort": c, "cache_mode": m, "file": f, "sha256": _fsha(os.path.join(d, f)),
                   "shape": list(mm.shape), "dtype": "float16", "unit": "uV" if m.startswith("C") else "z (per participant x channel)"}
            del mm
            _dump(rec, os.path.join(d, f) + ".done.json")
            caches[m] = rec
        cm = M.MODE_C[c]
        checks = {"own_repeats": []}
        excluded = []
        if c == "dtu":
            checks["inventory_reconciliation"] = {"trials": {"nh/ss/loaded": 20}, "nh_single_talker": {"cache_shas_ge2_listeners": 6},
                                                  "shas_below_2_listeners_in_cache": [],
                                                  "not_loaded": [dict(DTU_ABSENT), dict(DTU_FILTERED_ROW)]}
            excluded = [dict(DTU_FILTERED)]
        srows = []
        for r in st["streams"]:
            r = copy.deepcopy(r)
            k = next((kk for kk, e in entries.items() if e["stream"] == r["stream"]), None)
            n = fam_of[k][0] if k else None
            r.update(key=r["name"], family=None if n is None else fid[n], family_name=n, family_offset=None if k is None else fam_of[k][1])
            srows.append(r)
        _dump({"schema": "prior33_public_streams_v1", "cohort": c, "contract": C.CONTRACT, "id_space": M.ID_SPACE, "streams": srows},
              os.path.join(d, "streams.json"))
        _dump({"schema": "prior33_public_pieces_v1", "cohort": c, "contract": C.CONTRACT, "id_space": M.ID_SPACE, "partial": False,
               "builder_sha256": "synthetic", "layout_sha256": "synthetic", "participants": parts, "pieces": pieces,
               "presentations": reg, "families": fams,
               "partner_exclusions": [list(x) for x in M0["partner_exclusions"] if x[0] == c], "excluded_trials": excluded,
               "unread_files": [dict(DTU_UNREAD)] if c == "dtu" else [],
               "checks": checks, "cohort_info": ci, "caches": caches,
               "unit": {"supported": True, "name": "uV", "source_unit": "uV", "factor_to_uV": 1.0, "basis": "synthetic"},
               "mode_c": {"mode": cm, "file": C.CACHE_FILE[cm], "built": True, "supported": True, "reason": None}},
              os.path.join(d, "pieces.json"))
    # ------------------------------------------------------------------ C3
    info["scan"] = write_scan(fx, root, info)
    return info


def _c3_name(cohort, fam):
    n = fam["name"]
    if cohort == "federici":
        item = n if not n.startswith("g") else {"g0": "N1", "g1": "N2"}[n]
        return f"federici:g{FX.FED_CG[item]}"
    return f"{cohort}:{n}"


def write_scan(fx, root, info, ok=True):
    """A C3 scan_audio.json in scan_audio.py's schema from the fixture's ground truth, plus its latest pointer."""
    M0 = fx["manifest"]
    P = {p["id"]: p for p in M0["presentations"]}
    streams, families, shared = {}, {}, {}
    for c in M.COHORTS:
        rows = _load(os.path.join(root, c, "streams.json"))["streams"]
        fam_rows, member_of = [], {}
        for f in (f for f in M0["families"] if f["cohort"] == c):
            name = _c3_name(c, f)
            info["c3_name"][f["id"]] = name
            mem = {}
            for pid in f["members"]:
                p = P[pid]
                sid = rows[p["stream"]]["name"]
                mem.setdefault(sid, {"stream": sid, "offset": p["family_offset"] if p["offset_known"] else None,
                                     "offset_known": bool(p["offset_known"]), "length": rows[p["stream"]]["length"]})
            prov = sorted({f"{c}:{FX.DTU_DUP[0]}", f"{c}:{FX.DTU_DUP[1]}"}) if (c == "dtu" and f["name"] == FX.DTU_DUP[0]) else [name]
            fam_rows.append({"name": name, "root": sorted(mem)[0], "basis": f["basis"], "clock": f["clock"],
                             "members": sorted(mem.values(), key=lambda m: m["stream"]), "provisional_names": prov})
            for sid, m in mem.items():
                member_of[sid] = (name, m["offset"], m["offset_known"])
        keyed = {"attended", "item"}
        streams[c] = [{"stream": r["name"], "kind": r["kind"], "keyed": r["kind"] in keyed, "n": r["length"],
                       "family": member_of.get(r["name"], (None,))[0], "family_offset": member_of.get(r["name"], (None, None))[1],
                       "offset_known": member_of.get(r["name"], (None, None, None))[2], "source_sha256": r.get("source_sha256")}
                      for r in rows]
        families[c] = fam_rows
        shared[c] = []
        for s in M0["shared_audio"]:
            if s["cohort"] == c:
                sid = rows[P[s["presentation"]]["stream"]]["name"]
                shared[c].append({"stream": sid, "span": list(s["span"]), "partners": []})
    (ca, sa), (cb, sb) = fx["truth"]["overlap"]
    o = M0["overlap"][0]
    sid = lambda c, s: (f"{s}/attended" if c == "fau" else s)     # noqa: E731
    overlaps = [{"a": {"cohort": o["a"]["cohort"], "stream": sid(o["a"]["cohort"], o["a"]["stimulus"]), "stimulus": o["a"]["stimulus"],
                       "kind": "attended", "keyed": True, "span": o["a"]["span"]},
                 "b": {"cohort": o["b"]["cohort"], "stream": sid(o["b"]["cohort"], o["b"]["stimulus"]), "stimulus": o["b"]["stimulus"],
                       "kind": "attended", "keyed": True, "span": o["b"]["span"]},
                 "b_in_a": -o["lag"], "lag": o["lag"], "r_pooled": o["r"], "r_detect_max": o["r"], "coverage": 1.0, "refined": True}]
    excl = {t: {dn: [] for dn in M.DONORS[t]} for t in M.TARGETS}
    excl[cb][ca] = [sid(ca, sa)]
    excl[ca][cb] = [sid(cb, sb)]
    doc = {"schema": "prior33_scan_audio_v1", "contract": C.CONTRACT, "created_utc": "2026-10-17T00:00:00Z", "ok": ok, "complete": True,
           "cohorts_scanned": list(M.COHORTS), "builder": {"sha256": "synthetic"}, "signature": "synthetic", "checks": [],
           "streams": streams, "families": families, "shared_audio": shared,
           "cross_cohort": {"overlaps": overlaps, "donor_exclusions": excl, "flagged_streams": {}}}
    p = os.path.join(root, "scan_audio.json")
    if os.path.exists(p):
        os.chmod(p, 0o644)
    _dump(doc, p)
    _dump({"schema": "prior33_scan_audio_latest_v1", "status": "ok", "file": "scan_audio.json", "sha256": _fsha(p)},
          os.path.join(root, "scan_audio.latest.json"))
    return doc


def write_aln3(fx, d, kids, extra=None):
    """A synthetic ALN3 plan (units.jsonl) and completed A_LOCAL / E_LOCAL records equal to the fixture's cells (+ noise rows)."""
    os.makedirs(os.path.join(d, "units"))
    rows = []
    for cell in fx["manifest"]["cells"]:
        ds, sf, cf = cell["dataset"], cell["subject_fold"], cell["content_fold"]
        for rep in range(2):
            eid = f"ALN3_{ds[:3]}{sf}{cf}{rep:02d}"
            fam = "E_LOCAL" if ds == "private_bdf" else "A_LOCAL"
            rows.append({"experiment_id": eid, "family_id": fam, "dataset": ds, "subject_fold": sf, "content_fold": cf, "seed": 3401})
            test = list(cell["test"]) + list(cell.get("test_only", []))
            grp = {k["id"]: k["group"] for k in kids}
            rec = {"experiment_id": eid, "status": "complete", "eval": {"per_participant": {p: {"group": grp.get(p, "x")} for p in test}}}
            rec["n_train_children" if ds == "private_bdf" else "n_train_participants"] = len(cell["train"])
            _dump(rec, os.path.join(d, "units", f"{eid}.json"))
    rows.append({"experiment_id": "ALN3_running", "family_id": "A_LOCAL", "dataset": "fau", "subject_fold": 0, "content_fold": 0, "seed": 3401})
    _dump({"experiment_id": "ALN3_running", "status": "running"}, os.path.join(d, "units", "ALN3_running.json"))
    rows.append({"experiment_id": "ALN3_otherseed", "family_id": "A_LOCAL", "dataset": "fau", "subject_fold": 0, "content_fold": 0,
                 "seed": 3407})
    _dump({"experiment_id": "ALN3_otherseed", "status": "complete", "eval": {"per_participant": {"nobody": {}}}, "n_train_participants": 1},
          os.path.join(d, "units", "ALN3_otherseed.json"))
    for r in extra or ():
        rows.append(r)
    with open(os.path.join(d, "units.jsonl"), "w") as f:
        f.write("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n")
    with open(os.path.join(d, "plan_ext.jsonl"), "w") as f:
        f.write(json.dumps({"experiment_id": "ALN3X_0000000000000001", "family_id": "B_SOMETHING", "spec": {}}) + "\n")
    return os.path.join(d, "units.jsonl"), os.path.join(d, "units"), os.path.join(d, "plan_ext.jsonl")


def write_rich(fx, root):
    """Synthetic C7 outputs (build_rich.py schema v2) from the fixture's rich arrays and rich block."""
    src, M0 = fx["root"], fx["manifest"]
    for f in ("rich_pca4_f64.npy", C.RICH_P_FILE["ss"], C.RICH_P_FILE["sc"]):
        _link(os.path.join(src, f), os.path.join(root, f))
    rb_c = {}
    for c in M.COHORTS:
        d0, d = os.path.join(src, c), os.path.join(root, c)
        _link(os.path.join(d0, "rich_f32.npy"), os.path.join(d, "rich_f32.npy"))
        rows = _load(os.path.join(d0, "rich_streams.json"))["streams"]
        st = _load(os.path.join(d, "streams.json"))["streams"]
        for r, s in zip(rows, st):
            r["length"] = s["length"]
        table = "runs.json" if c == "sparrkulee" else "pieces.json"
        doc = {"schema": "prior33_rich_streams_v2", "contract": C.CONTRACT, "cohort": c, "pca4_sha256": M0["rich"]["pca4"]["sha256"],
               "partial": False, "reasons": {k: {"waveform_read": k not in FX.NO_SOURCE} for k in FX.NO_SOURCE + ("waveform_unavailable", "clock_lag")},
               "no_source_reasons": list(FX.NO_SOURCE), "read_masked_reasons": ["waveform_unavailable", "clock_lag"], "streams": rows,
               "inputs": {"streams_sha256": _fsha(os.path.join(d, "streams.json")), "env_sha256": _fsha(os.path.join(d, "env_f32.npy")),
                          "table": table, "table_sha256": _fsha(os.path.join(d, table)), "table_partial": False}}
        _dump(doc, os.path.join(d, "rich_streams.json"))
        rb_c[c] = {"stale": False, "partial": False, "pca4_sha256": M0["rich"]["pca4"]["sha256"], "rich_sha256": _fsha(os.path.join(d, "rich_f32.npy")),
                   "rich_streams_sha256": _fsha(os.path.join(d, "rich_streams.json"))}
    _dump({"schema": "prior33_rich_build_v2", "contract": C.CONTRACT, "partial": False, "builder_sha256": "synthetic",
           "fit_mask": {"applied": True, "sha256": _fsha(os.path.join(root, "scan_audio.json"))}, "manifest_rich": M0["rich"],
           "cohorts": rb_c, "targets": {"ss": "whisper_logmel_pca4_sk_v1", "sc": "flux_pca4_v1"}}, os.path.join(root, "rich_build.json"))


# ---------------------------------------------------------------------------------------------------------- module fixtures
@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    return FX.make_synthetic_manifest(tmp_path_factory.mktemp("m2e_fixture"), scale=SCALE)


@pytest.fixture(scope="module")
def kids():
    return FX.synthetic_kids()


@pytest.fixture(scope="module")
def tree(fx, tmp_path_factory, kids):
    base = tmp_path_factory.mktemp("m2e_tree")
    root = os.path.join(base, "root")
    info = build_tree(fx, root)
    info["root"] = root
    info["aln3"] = write_aln3(fx, os.path.join(base, "aln3"), kids)
    info["private"] = os.path.join(base, "private_copy")
    return info


@pytest.fixture(scope="module")
def built(tree):
    plan, units, plan_ext = tree["aln3"]
    res = M.build_core(tree["root"], out_private=tree["private"], aln3_plan=plan, units_dir=units, plan_ext=plan_ext, declared=DECLARED_TEST,
                       log=_quiet)
    with open(res["manifest"], "rb") as f:
        pub_raw = f.read()
    with open(res["full"], "rb") as f:
        full_raw = f.read()
    return {**res, "pub": json.loads(pub_raw), "full_doc": json.loads(full_raw), "pub_raw": pub_raw, "full_raw": full_raw}


def _fixture_pid(tree, man, p):
    """The fixture presentation id of a manifest presentation (phantom presentations: the fixture's shared item presentation)."""
    inv = {k: pid for pid, k in tree["key_of"].items()}
    return inv[p["key"]] if p["key"] in inv else tree["phantom_keys"][p["key"]]


# ---------------------------------------------------------------------------------------------------------- id mapping
def test_global_ids_map_the_cohort_local_tables_by_key(fx, tree, built):
    man, M0 = built["full_doc"], fx["manifest"]
    F0 = {f["id"]: f for f in M0["families"]}
    P0 = {p["id"]: p for p in M0["presentations"]}
    pres = man["presentations"]
    assert [p["id"] for p in pres] == list(range(len(pres))) and [f["id"] for f in man["families"]] == list(range(len(man["families"])))
    # one id space: cohorts in order, keys sorted within a cohort
    assert [p["cohort"] for p in pres] == sorted((p["cohort"] for p in pres), key=M.COHORTS.index)
    for c in M.COHORTS:
        ks = [p["key"] for p in pres if p["cohort"] == c]
        assert ks == sorted(ks) and len(set(ks)) == len(ks)
    # every fixture presentation is one manifest presentation, plus one per phantom item (C5 keys the phantom separately)
    assert len(pres) == len(P0) + len(tree["phantom_keys"])
    fam_name = {f["id"]: f["name"] for f in man["families"]}
    for p in pres:
        q = P0[_fixture_pid(tree, man, p)]
        assert (p["cohort"], p["stream"], p["kind"], p["attended_side"], p["ignored_stream"], p["ignored_lead"]) == \
               (q["cohort"], q["stream"], q["kind"], q["attended_side"], q["ignored_stream"], q["ignored_lead"])
        assert fam_name[p["family"]] == tree["c3_name"][q["family"]]          # C3's family, not the provisional one
        assert man["families"][p["family"]]["clock"] == F0[q["family"]]["clock"]
        if F0[q["family"]]["clock"] == "known":
            assert p["family_offset"] == q["family_offset"] and p["offset_known"]
    # C3's measured offsets replace C4's declared None and C5's pending clocks; the DTU duplicate joins its original's family
    by_key = {p["key"]: p for p in pres}
    art = by_key[_sk_key("audiobook_1_artefact")[0]]
    assert art["family_offset"] == fx["truth"]["family_offset"]["sparrkulee:audiobook_1_artefact"] and art["offset_known"]
    assert by_key["federici:V1"]["family_offset"] == FX.FED_LAG and by_key["federici:V1"]["family"] == by_key["federici:N1"]["family"]
    t07, t01 = by_key["dtu:t07|side=None"], by_key["dtu:t01|side=None"]
    assert t07["family"] == t01["family"] and t07["family_offset"] - t01["family_offset"] == FX.DTU_DUP[2]
    assert set(man["families"][t07["family"]]["provisional_names"]) == {"dtu:t01", "dtu:t07"}
    unknown = {f["id"] for f in man["families"] if f["clock"] == "unknown"}
    assert unknown == {by_key["federici:N2"]["family"]}
    # the tables keep their own (cohort-local) ids: the views map them by key; here the global ids really differ
    fau = _load(os.path.join(tree["root"], "fau", "pieces.json"))
    assert fau["id_space"] == M.ID_SPACE and any(it["presentation"] != by_key[it["presentation_key"]]["id"] for it in fau["pieces"])
    # the segment table uses global ids consistent with every piece's key
    for c in M.COHORTS:
        items = _load(os.path.join(tree["root"], c, man["cohorts"][c]["table"]))[man["cohorts"][c]["items"]]
        S = man["segments"][c]
        for i, p in zip(S["piece"], S["presentation"]):
            assert by_key[items[i]["presentation_key"]]["id"] == p


# ---------------------------------------------------------------------------------------------------------- segments, pools, donor sets
def _expected_segments(fx, tree, man):
    """The fixture's segment rows with the test's declared run relabelled and n_partners recomputed independently."""
    M0 = fx["manifest"]
    out = {}
    twins = {(c, a): b for c, a, b in M0["partner_exclusions"]}
    twins.update({(c, b): a for c, a, b in M0["partner_exclusions"]})
    for c in M.COHORTS:
        S = M0["segments"][c]
        items = _load(os.path.join(fx["root"], c, M0["cohorts"][c]["table"]))[M0["cohorts"][c]["items"]]
        roles = list(S["role"])
        for r, i in enumerate(S["piece"]):
            it = items[i]
            for dcl in DECLARED_TEST:
                if dcl["cohort"] == c and str(it.get("sub", it.get("participant"))) == dcl["sub"] and it["stimulus"] == dcl["stimulus"]:
                    roles[r] = M.DECLARED_ROLE
        grp = collections.defaultdict(set)
        for r in range(len(S["s"])):
            grp[(S["presentation"][r], S["s"][r], roles[r])].add(S["participant"][r])
        rows = []
        for r in range(len(S["s"])):
            g = grp[(S["presentation"][r], S["s"][r], roles[r])]
            n_p = len(g - {S["participant"][r]} - ({twins[(c, S["participant"][r])]} if (c, S["participant"][r]) in twins else set())) \
                if roles[r] in M.DONOR_ROLES else 0
            rows.append((S["piece"][r], S["participant"][r], S["s"][r], roles[r], S["kind"][r], n_p))
        out[c] = rows
    return out


def test_segments_and_pools_match_the_fixture(fx, tree, built):
    man = built["full_doc"]
    exp = _expected_segments(fx, tree, man)
    for c in M.COHORTS:
        S = man["segments"][c]
        got = list(zip(S["piece"], S["participant"], S["s"], S["role"], S["kind"], S["n_partners"]))
        assert got == exp[c], c
        assert len({len(v) for v in S.values()}) == 1
    # pools: fit / ss (core), FAU fit / cs (csx), dev and bridge_cal, all with >= 1 partner; the declared dev run's segments left
    for c, rows in man["pools"]["core"].items():
        S = man["segments"][c]
        assert rows == [r for r in range(len(S["s"])) if S["role"][r] == "fit" and S["kind"][r] == "ss" and S["n_partners"][r] >= 1]
    S = man["segments"]["sparrkulee"]
    dev_parts = {(S["participant"][r], man["presentations"][S["presentation"][r]]["stimulus"]) for r in man["pools"]["dev"]["sparrkulee"]}
    assert ("052", "podcast_16") not in dev_parts and ("051", "podcast_16") not in dev_parts     # its only partner left with it
    assert {s for _, s in dev_parts} == {"audiobook_11_1"}
    assert set(man["pools"]["core"]["sparrkulee"]) == set(fx["manifest"]["pools"]["core"]["sparrkulee"])
    # never a DTU HI listener, the phantom or a restricted participant in any pool
    for key, d in man["pools"].items():
        for s, rows in d.items():
            Sc = man["segments"][M.coh_of(s)]
            ps = {Sc["participant"][r] for r in rows}
            assert not ps & set(FX.DTU_HI) and not ps & set(fx["truth"]["phantom"]) and not ps & set(M.RESTRICTED)
    # the C2 'unverifiable' fit runs stay in the core pool (F11)
    items = _load(os.path.join(tree["root"], "sparrkulee", "runs.json"))["runs"]
    core_pieces = {S["piece"][r] for r in man["pools"]["core"]["sparrkulee"]}
    for sub, stim in UNVERIFIABLE_KEPT:
        i = next(i for i, r in enumerate(items) if r["sub"] == sub and r["stimulus"] == stim)
        assert items[i]["audit"]["clock"] == "unverifiable" and i in core_pieces
    assert man["exclusion_summary"]["unverifiable_kept"] == len(UNVERIFIABLE_KEPT)
    # shared audio: the jingle spans of C3 mask every role, as the fixture
    assert {(d["sid"], tuple(d["span"])) for d in man["shared_audio"]} == \
           {(s, (0, FX.JINGLE + FX.MARGIN)) for s in FX.SK_JINGLE}
    assert man["hc_hcv_excluded_pairs"] == fx["manifest"]["hc_hcv_excluded_pairs"]
    assert man["partner_exclusions"] == fx["manifest"]["partner_exclusions"]


def test_leave_target_out_donor_sets_match_the_fixture(fx, tree, built):
    man, M0 = built["full_doc"], fx["manifest"]
    assert set(man["donor_sets"]) == set(M0["donor_sets"])
    for target, blocks in M0["donor_sets"].items():
        assert set(man["donor_sets"][target]) == set(blocks)
        for b, ds in blocks.items():
            got = man["donor_sets"][target][b]
            assert got["strata"] == ds["strata"] and got["n_segments"] == ds["n_segments"]
            assert np.allclose(got["weights"], ds["weights"], rtol=0, atol=1e-15)
            assert target not in got["strata"] and "private_bdf" not in got["strata"]
            assert ("fau_cs" in got["strata"]) == (b == "csx") and not (target == "fau" and b == "csx")
            for s, ps in got["excluded_presentations"].items():
                assert sorted(_fixture_pid(tree, man, man["presentations"][p]) for p in ps) == sorted(ds["excluded_presentations"][s])
    # the overlap: FAU 122 leaves DTU's donor set, DTU t05 leaves FAU's, nothing else
    ex = man["donor_sets"]
    assert {man["presentations"][p]["stimulus"] for p in ex["dtu"]["core"]["excluded_presentations"]["fau"]} == {"122"}
    assert {man["presentations"][p]["stimulus"].split("@")[0] for p in ex["fau"]["core"]["excluded_presentations"]["dtu"]} == {"t05"}
    assert not any(ex["private_bdf"]["core"]["excluded_presentations"].values())
    assert man["overlap"][0]["lag"] == M0["overlap"][0]["lag"]
    # budget, standardiser, seen sets and coverage equal the fixture's
    assert man["budget"]["N_SK"] == M0["budget"]["N_SK"] and man["budget"]["S0"] == M0["budget"]["S0"]
    np.testing.assert_allclose(man["standardiser"]["sigma"], M0["standardiser"]["sigma"], rtol=1e-12)
    np.testing.assert_allclose(man["standardiser"]["mu_estimate"], M0["standardiser"]["mu_estimate"], rtol=1e-9, atol=1e-15)
    assert man["standardiser"]["mu"] == [0.0] * C.N_TGT and man["standardiser"]["n_windows"] == M0["standardiser"]["n_windows"]
    assert man["seen"] == M0["seen"] and man["coverage"] == M0["coverage"]
    assert man["projection"]["sha256"].startswith(C.P_SHA16) and man["projection"]["sha256"] == M0["projection"]["sha256"]
    assert man["target_contract"] == M0["target_contract"]


def test_fixed_sets_avoid_excluded_presentations_and_cover_the_cal_split(built):
    man = built["full_doc"]
    S = man["segments"]["sparrkulee"]
    anywhere = M.excluded_anywhere(man["donor_sets"])
    for name, rows, pool in (("fit", man["selection"]["fit_segments"], man["pools"]["core"]["sparrkulee"]),
                             ("dev", man["selection"]["dev_queries"], man["pools"]["dev"]["sparrkulee"]),
                             ("cal", man["bridge"]["cal_queries"], man["pools"]["bridge_cal"]["sparrkulee"])):
        assert rows and set(rows) <= set(pool) and not {S["presentation"][r] for r in rows} & set(anywhere), name
    assert len(man["selection"]["fit_segments"]) == min(M.N_FIT, len(man["pools"]["core"]["sparrkulee"]))
    qp = {S["participant"][r] for r in man["bridge"]["cal_queries"]}
    sp = man["bridge"]["cal_split"]
    assert set(sp[0]) | set(sp[1]) == qp and not set(sp[0]) & set(sp[1])
    for target, rows in man["bridge"]["fit_rows"].items():
        ds = man["donor_sets"][target]["core"]
        assert len(rows) == M.N_BRIDGE and {s for s, _ in rows} <= set(ds["strata"])
        for s, r in rows:
            assert r in man["pools"]["core"][s] and man["segments"][s]["presentation"][r] not in ds["excluded_presentations"][s]
    # participant balance: rows of every listener of the role, at most one apart when the pool allows it
    bal = M._balanced(list(range(40)), {i: f"p{i % 4}" if i < 36 else "p4" for i in range(40)}, 15, np.random.default_rng(0))
    cnt = collections.Counter(f"p{i % 4}" if i < 36 else "p4" for i in bal)
    assert len(bal) == 15 == len(set(bal)) and max(cnt.values()) - min(cnt.values()) <= 1 and set(cnt) == {"p0", "p1", "p2", "p3", "p4"}


# ---------------------------------------------------------------------------------------------------------- cells
def test_cells_bound_to_the_aln3_cells_with_split_hashes(fx, tree, built, kids):
    man, M0 = built["full_doc"], fx["manifest"]
    assert [(c["dataset"], c["subject_fold"], c["content_fold"]) for c in man["cells"]] == \
           [(c["dataset"], c["subject_fold"], c["content_fold"]) for c in M0["cells"]]
    for got, ref in zip(man["cells"], M0["cells"]):
        for k in ("train", "test", "always_train", "test_only"):
            assert sorted(got[k]) == sorted(ref[k]), (got["dataset"], got["subject_fold"], k)
        assert got["split_hash"] == M.split_hash(got)
        assert got["n_train"] == len(got["train"]) and got["n_test"] == len(got["test"])
        if got["dataset"] == "fau":
            assert got["content"] == {k: {r: sorted(v) for r, v in d.items()} for k, d in ref["content"].items()}
        elif got["dataset"] != "private_bdf":
            assert got["content"] == {r: sorted(v) for r, v in ref["content"].items()}
            assert {k: v for k, v in got["content_groups"].items()} == {k: v for k, v in ref["content_groups"].items()}
    # a different binding changes the hash; the hash covers ids, content, rules and seeds only
    c0 = copy.deepcopy(man["cells"][0])
    h = M.split_hash(c0)
    c0["n_train"] = -1
    assert M.split_hash(c0) == h
    c0["test"] = c0["test"][1:]
    assert M.split_hash(c0) != h
    # every public cell agreed with both synthetic ALN3 records of its cell (the running and other-seed records are ignored)
    rows = man["cell_binding"]["public"]
    assert len(rows) == 25 and all(r["n_records"] == 2 == r["n_agree"] for r in rows)
    # private cells from the E_LOCAL records: the kids' folds
    priv = [c for c in man["cells"] if c["dataset"] == "private_bdf"]
    for c in priv:
        assert set(c["test"]) == {k["id"] for k in kids if k["fold"] == c["subject_fold"]}
        assert sum(c["n_test_by_group"].values()) == c["n_test"]


def test_disagreeing_aln3_record_is_refused(fx, tree, tmp_path, kids):
    plan, units, plan_ext = tree["aln3"]
    units2 = tmp_path / "units"
    shutil.copytree(units, units2)
    rec = _load(units2 / "ALN3_fau0000.json")
    rec["n_train_participants"] += 1
    _dump(rec, units2 / "ALN3_fau0000.json")
    with pytest.raises(M.ManifestError, match="A_LOCAL record"):
        M.build_core(tree["root"], out=None, out_private=str(tmp_path / "p"), aln3_plan=plan, units_dir=str(units2), plan_ext=plan_ext,
                     declared=DECLARED_TEST, log=_quiet)


def test_public_copy_has_no_child_ids_and_names_the_full_copy(built, kids, tree):
    pub, full = built["pub"], built["full_doc"]
    assert pub["copy"] == "public_redacted" and full["copy"] == "private_full"
    assert pub["full_manifest_sha256"] == hashlib.sha256(built["full_raw"]).hexdigest() == built["full_sha256"]
    text = built["pub_raw"].decode()
    for k in kids:
        assert f'"{k["id"]}"' not in text
    assert all("train" not in c and "test" not in c and c["split_hash"] for c in pub["cells"] if c["dataset"] == "private_bdf")
    assert M.dumps({**M.redact(full), "full_manifest_sha256": built["full_sha256"]}) == built["pub_raw"]
    assert oct(os.stat(built["manifest"]).st_mode & 0o777) == "0o444" and oct(os.stat(built["full"]).st_mode & 0o777) == "0o444"
    assert oct(os.stat(os.path.dirname(built["full"])).st_mode & 0o777) == "0o700"


# ---------------------------------------------------------------------------------------------------------- declared exclusions, reconciliations
def test_declared_exclusions_are_listed_with_reasons(fx, tree, built):
    man = built["full_doc"]
    ex = man["exclusions"]
    rules = collections.defaultdict(list)
    for e in ex:
        assert e["declared"] is True and e["rule"] in man["exclusion_rules"]
        rules[e["rule"]].append(e)
    assert {e["sub"] for e in rules["restricted_participant"]} == {"019"}
    mis = rules["clock_misaligned"]
    assert [(e["sub"], e["stimulus"]) for e in mis] == [("005", "audiobook_2_1")] and mis[0]["detail"]["tau"] == [-566, -566]
    assert [(e["sub"], e["stimulus"]) for e in rules["structural_anomaly_unverified_clock"]] == [("005", "podcast_2")]
    d = rules["declared_structural_exclusion"]
    assert [(e["sub"], e["stimulus"]) for e in d] == [("052", "podcast_16")] and d[0]["detail"]["reason"] == DECLARED_TEST[0]["reason"]
    assert sorted((e["sub"], e["run_id"]) for e in rules["readme_flagged"]) == \
           sorted((s, f"sub-{s}_ses-{ses}_run-{r}") for s, ses, r in M.README_FLAGGED)
    # every DTU inventory trial the ALN3 loader does not load: the filtered one (its own reason) and the one in a file load_dtu
    # never opens (the file's reason: C5 gives the trial none)
    lf = {e["stimulus"]: e["detail"] for e in rules["aln3_loader_filter"]}
    assert set(lf) == {"t99", "t08"}
    assert lf["t99"]["status"] == "excluded" and lf["t99"]["reason"] == DTU_FILTERED["reason"]
    assert lf["t08"]["status"] == "unread_file" and lf["t08"]["reason"] == DTU_UNREAD["reason"]
    # the real declared list names sub-051 audiobook_12_2, its basis, the C2 numbers it quotes and its conflicts with §1 and §3.2
    d0 = M.DECLARED_EXCLUSIONS[0]
    assert d0["sub"] == "051" and d0["stimulus"] == "audiobook_12_2" and d0["rule"] == "declared_structural_exclusion"
    for s in ("decoder_lag.json", "-566", "unverifiable", "-1668", "-2220", "3.40", "3.19", "§1", "F11", "-568", "-565"):
        assert s in d0["reason"], s
    assert "consistent -566" not in d0["reason"]                     # C2 does not measure a consistent shift
    assert d0["expect_c2"]["class"] == "unverifiable" and d0["expect_c2"]["tau"] == [-1668, -2220]
    assert any("§1" in x for x in d0["conflicts"]) and any("§3.2" in x for x in d0["conflicts"])
    b = d0["basis"][0]
    prov = os.path.join(M.REPO, b["file"])
    assert b["file"].endswith("aln34_sparrk/decoder_lag.json") and b["entry"] == "051:audiobook_12_2"
    if os.path.exists(prov):                                           # the 0700 provenance copy (design §1, Appendix A)
        assert _fsha(prov) == b["sha256"]
        assert _load(prov)[b["entry"]]["tau_samples"] == b["values"]["tau_samples"] == -566
    # reconciliations
    rc = man["dtu_reconciliation"]
    want_absent = [dict(DTU_ABSENT, reason=DTU_UNREAD["reason"]), dict(DTU_FILTERED_ROW)]
    assert sorted(rc["absent_trials"], key=lambda r: r["file"]) == sorted(want_absent, key=lambda r: r["file"])
    assert rc["excluded_trials"] == [DTU_FILTERED] and len(rc["not_loaded"]) == 2
    assert {u["what"] for u in man["unused"] if u["cohort"] == "dtu"} >= {"NH single-talker inventory trials not in the C5 cache (excluded)",
                                                                           "NH single-talker inventory trials not in the C5 cache (unread_file)"}
    assert {u["what"] for u in man["unused"]} >= {"sub-019_podcast_1", "competing-talker pieces", "HI single-talker trials",
                                                   "two-talker trials", "phantom sessions"}
    assert any(u["reason"].startswith(M.DECLARED_ROLE) for u in man["unused"])
    assert man["declared_before_results"]["checked"] is True and man["declared_before_results"]["n_e34_records"] == 0


def test_mode_c_scales_equal_build_public(fx, tree, built):
    from auditory_alignment_v3.prior33 import build_public as BP
    man = built["full_doc"]
    root = tree["root"]
    tabs = {}
    for c in M.COHORTS:
        t = _load(os.path.join(root, c, "runs.json" if c == "sparrkulee" else "pieces.json"))
        tabs[c] = {"layout": t["cohort_info"]["layout"], "participants": t["participants"], "cohort_info": t["cohort_info"]}
        if c == "sparrkulee":
            sk = t
    units = {c: 1.0 for c in M.COHORTS}
    for target in M.PUBLIC:
        tb = dict(tabs)
        if target == "federici":
            d = BP.with_band_sd(sk, os.path.join(root, "sparrkulee"))
            tb["sparrkulee"] = {"layout": d["cohort_info"]["layout"], "participants": d["participants"], "cohort_info": d["cohort_info"]}
        want = BP.mode_c_scales(target, tb, units, donors=M.DONORS[target], band="target")
        got = man["mode_c"][target]
        assert got["supported"] and want["supported"] and got["mode"] == M.MODE_C[target]
        assert got["scale"] == want["scale"] and got["cache"] == C.CACHE_FILE[M.MODE_C[target]]
    assert man["mode_c"]["federici"]["sparrkulee_2_8_derived"] is True and man["mode_c"]["sparrkulee"]["supported"] is False
    assert man["cohorts"]["fau"]["caches"] == {"A": C.CACHE_FILE["A"], "B": C.CACHE_FILE["B"], "C": C.CACHE_FILE["C"]}


# ---------------------------------------------------------------------------------------------------------- file hashes, core first
def test_every_described_file_is_hashed(tree, built):
    man = built["full_doc"]
    files = man["files"]
    for rel, v in files.items():
        p = os.path.join(tree["root"], rel)
        assert os.path.isfile(p), rel
        assert _fsha(p) == v["sha256"] and os.path.getsize(p) == v["bytes"], rel
    for c, info in man["cohorts"].items():
        for f in [info["table"], info["streams"], info["env"], *info["caches"].values()]:
            assert f"{c}/{f}" in files
        for f in info["caches"].values():
            if c != "sparrkulee":
                assert f"{c}/{f}.done.json" in files
    for f in ("sparrkulee/runs_table.json", "sparrkulee/align_audit.jsonl", "sparrkulee/align_audit_meta.json", "scan_audio.json",
              "scan_audio.latest.json", C.P_FILE):
        assert f in files
    assert not any(os.path.basename(f) in RICH_FILES or "rich" in f for f in files)          # core first: no C7 file
    assert built["full_doc"]["builder_sha256"] == _fsha(M.__file__)


def test_core_first_and_the_rich_supplement(fx, tree, built, tmp_path_factory):
    # core first: no C7 output anywhere in the tree, the core manifest exists, the rich part waits for C7
    for c in M.COHORTS:
        assert not any(os.path.exists(os.path.join(tree["root"], c, f)) for f in RICH_FILES)
    assert "rich" not in built["full_doc"] and built["full_doc"]["rich_supplement"]["file"] == M.MANIFEST_RICH
    with pytest.raises(M.ManifestError, match="rich_build.json"):
        M.build_rich(tree["root"], out_private=tree["private"], plan_ext=tree["aln3"][2], units_dir=tree["aln3"][1], log=_quiet)
    # after C7 (synthetic outputs on a copy of the tree): the supplement links both copies and rich_build.json
    base = tmp_path_factory.mktemp("m2e_rich")
    root = os.path.join(base, "root")
    shutil.copytree(tree["root"], root, copy_function=_link)
    priv = os.path.join(base, "private")
    shutil.copytree(tree["private"], priv)
    write_rich(fx, root)
    plan, units, plan_ext = tree["aln3"]
    res = M.build_rich(root, out_private=priv, plan_ext=plan_ext, units_dir=units, log=_quiet)
    doc = _load(res["manifest_rich"])
    assert res["guard"]["checked"] is True and res["guard"]["n_rich_rows"] == 0 and doc["declared_before_results"] == res["guard"]
    ch = {c["choice"]: c for c in doc["declared_choices"]}
    assert ch["rich_pca4_basis_as_built"]["effect"]["basis_includes_left_out_presentations"] == \
        built["full_doc"]["standardiser"]["left_out_presentations"]
    assert "manifest_rich_sha256" in doc["usage"]
    assert doc["core_manifest_sha256"] == built["full_sha256"] and doc["core_manifest_public_sha256"] == built["manifest_sha256"]
    assert doc["rich_build_sha256"] == _fsha(os.path.join(root, "rich_build.json"))
    ref = fx["manifest"]["rich"]
    np.testing.assert_allclose(doc["rich"]["sigma_ss"], ref["sigma_ss"], rtol=1e-12)
    np.testing.assert_allclose(doc["rich"]["sigma_sc"], ref["sigma_sc"], rtol=1e-12)
    assert doc["rich"]["n_windows"] == ref["n_windows"] and doc["rich"]["P_ss"] == ref["P_ss"] and doc["rich"]["pca4"] == ref["pca4"]
    for c in M.COHORTS:
        for f in RICH_FILES:
            assert doc["files"][f"{c}/{f}"]["sha256"] == _fsha(os.path.join(root, c, f))
    with open(os.path.join(priv, M.MANIFEST_RICH), "rb") as f_, open(res["manifest_rich"], "rb") as g:
        assert f_.read() == g.read()
    assert doc["unused"] and {u["cohort"] for u in doc["unused"]} >= {"federici", "sparrkulee"}
    # merged into an opened core manifest (either copy), checked against the link
    from auditory_alignment_v3.prior33 import views as V
    core = V.open_manifest(os.path.join(priv, M.MANIFEST), built["full_sha256"], root=root)
    mr = M.open_with_rich(core, res["sha256"])
    assert mr.sha256 == core.sha256 and mr["rich"]["sigma_sc"] == doc["rich"]["sigma_sc"] and mr["cohorts"]["dtu"]["rich"] == "rich_f32.npy"
    bank = V.DonorBank(mr, "sparrkulee", ("fit",), "cpu", rich=True)
    assert bank.rich is not None
    pub = V.open_manifest(os.path.join(root, M.MANIFEST), built["manifest_sha256"], root=root)
    assert M.open_with_rich(pub, res["sha256"][:16])["rich"] == mr["rich"]
    with pytest.raises(ValueError):
        M.open_with_rich(core, "0" * 16)
    # the consumer path: open_for_row opens the row's core manifest (the public copy first: its sha256 differs, so it falls through
    # to the full copy) and merges the supplement the row quotes; a RICH_DONOR row must quote one
    paths, rpaths = [os.path.join(root, M.MANIFEST), os.path.join(priv, M.MANIFEST)], [os.path.join(root, M.MANIFEST_RICH)]
    row = {"experiment_id": "ALN3X_00000000000000r1", "family_id": M.RICH_DONOR_FAMILY,
           "spec": {"block": "rich", "manifest_sha256": built["full_sha256"], "manifest_rich_sha256": res["sha256"]}}
    m = M.open_for_row(row, paths=paths, rich_paths=rpaths, cache_root=root)
    assert m.sha256 == built["full_sha256"] and m.rich_sha256 == res["sha256"] and m["rich"] == doc["rich"]
    assert m.root == os.path.abspath(root) and m["cohorts"]["sparrkulee"]["rich"] == "rich_f32.npy"
    assert V.DonorBank(m, "fau", ("fit",), "cpu", rich=True).rich is not None
    with pytest.raises(ValueError, match="manifest_rich_sha256"):
        M.open_for_row({**row, "spec": {"manifest_sha256": built["full_sha256"]}}, paths=paths)
    core_row = {"experiment_id": "ALN3X_00000000000000d1", "family_id": "ALN32_PUBLIC_AUDIO_PRIOR_DONOR",
                "spec": {"block": "core", "manifest_sha256": built["full_sha256"][:16]}}
    m2 = M.open_for_row(core_row, paths=paths, cache_root=root)
    assert "rich" not in m2 and m2.sha256 == built["full_sha256"]
    with pytest.raises(ValueError, match="no manifest with the row's sha256"):
        M.open_for_row({**core_row, "spec": {"manifest_sha256": "0" * 64}}, paths=paths)
    with pytest.raises(FileNotFoundError):
        M.open_for_row(core_row, paths=[os.path.join(root, "absent.json")])
    with pytest.raises(ValueError, match="no rich supplement"):
        M.open_for_row({**row, "spec": {**row["spec"], "manifest_rich_sha256": "0" * 64}}, paths=paths, rich_paths=rpaths, cache_root=root)
    # a C7 build from another scan than the core froze is refused
    rb = _load(os.path.join(root, "rich_build.json"))
    rb["fit_mask"]["sha256"] = "0" * 64
    os.chmod(os.path.join(root, "rich_build.json"), 0o644)
    _dump(rb, os.path.join(root, "rich_build.json"))
    with pytest.raises(M.ManifestError, match="fit_mask|C3"):
        M.build_rich(root, out_private=priv, plan_ext=plan_ext, units_dir=units, log=_quiet)


# ---------------------------------------------------------------------------------------------------------- the views read it
def test_views_and_sampler_read_the_manifest_unchanged(fx, tree, built):
    torch = pytest.importorskip("torch")
    from auditory_alignment_v3.prior33 import sampler as SM
    from auditory_alignment_v3.prior33 import views as V
    root = tree["root"]
    man = V.open_manifest(built["full"], built["full_sha256"])                  # the full copy: cache_root recorded, no root= needed
    assert man.root == os.path.abspath(root)
    pub = V.open_manifest(built["manifest"], built["manifest_sha256"][:16])
    assert pub.root == man.root
    with pytest.raises(ValueError):
        V.open_manifest(built["manifest"], built["full_sha256"])                  # the copies differ: rows quote the full copy's sha256
    banks = {c: V.DonorBank(man, c, ("fit", "dev", "bridge_cal") if c == "sparrkulee" else ("fit",), "cpu") for c in V.DONOR_COHORTS}
    assert all(b.presentation_check == "checked" and b.n_pieces_checked > 0 for b in banks.values())
    for c, b in banks.items():
        S = man["segments"][c]
        rows = man["pools"]["core"][c][:3]
        x = b.gather(np.asarray(S["piece"])[rows], np.asarray(S["s"])[rows], 0)
        assert x.shape == (3, len(C.MONTAGES[c]), C.L_IN) and torch.isfinite(x.float()).all()
    for c in M.PUBLIC:
        for mode in [m for m, cs in C.ZS_COHORTS.items() if c in cs]:
            for cf in sorted({cell["content_fold"] for cell in man["cells"] if cell["dataset"] == c}):
                v = V.target_view(c, cf, man, mode)
                assert v.meta["n_segments"] > 0 and v.meta["manifest_sha256"] == built["full_sha256"]
    combos = [(t, b) for t in M.TARGETS for b in ("core", "csx") if not (t == "fau" and b == "csx")]
    for target, block in combos:
        smp = SM.DonorSampler(man, target, block, 3401, "cpu", banks=banks)
        bt = smp.next_batch()
        assert bt.x1.shape[0] == 256 and bt.stratum in man["donor_sets"][target][SM.BLOCKS[block]]["strata"]
    sets = SM.selection_sets(man)
    assert len(sets["dev"]["queries"].rows) == len(man["selection"]["dev_queries"])
    for target in M.TARGETS:
        br = SM.bridge_rows(man, target)
        assert br["n_fit_rows"] == M.N_BRIDGE
    cell = V.manifest_cell(man, "fau", 0, 0)
    coh = V.target_view("fau", 0, man, "A")
    bt = V.TickBatcher(coh, {"architecture": "lag_local_tokens", "window": "full", "training_task": "paired_alignment"},
                       {"dataset": "fau", "subject_fold": 0, "content_fold": 0}, "cpu", man)
    assert bt.cell_split_hash == cell["split_hash"] and {coh.participants[i]["id"] for i in bt.train_p} == set(cell["train"])


# ---------------------------------------------------------------------------------------------------------- guards
def _variant(tree, tmp_path, edit):
    """A copy of the builder tree with one table edited by `edit(root)`."""
    root = os.path.join(tmp_path, "root")
    shutil.copytree(tree["root"], root, copy_function=_link)
    for d, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".json") or f.endswith(".jsonl"):
                p = os.path.join(d, f)
                data = open(p, "rb").read()
                os.unlink(p)
                with open(p, "wb") as g:
                    g.write(data)
    edit(root)
    return root


def _build(tree, root, tmp_path, **kw):
    plan, units, plan_ext = tree["aln3"]
    return M.build_core(root, out_private=os.path.join(tmp_path, "priv"), aln3_plan=plan, units_dir=units, plan_ext=plan_ext,
                        declared=kw.pop("declared", DECLARED_TEST), log=_quiet, **kw)


def test_restricted_rows_and_paths_are_refused(tree, tmp_path):
    def edit(root):
        p = os.path.join(root, "sparrkulee", "runs.json")
        t = _load(p)
        r = next(r for r in t["runs"] if r["role"] == "restricted")
        r["segment_starts"] = [128]
        _dump(t, p)
    root = _variant(tree, tmp_path, edit)
    with pytest.raises(M.RestrictedAccess):
        _build(tree, root, tmp_path)
    with pytest.raises(M.RestrictedAccess):
        M.check_path("/x/sparrkulee/derivatives/preprocessed_eeg/sub-019/ses-a/sub-019_x.npy")
    assert M.check_path("/x/dtu/sub-021.h5") == "/x/dtu/sub-021.h5"


def test_inconsistent_inputs_are_refused(tree, tmp_path):
    def c2_mismatch(root):                     # C4 says aligned where C2 said misaligned
        p = os.path.join(root, "sparrkulee", "runs.json")
        t = _load(p)
        next(r for r in t["runs"] if "clock_misaligned" in r["flags"])["audit"]["clock"] = "aligned"
        _dump(t, p)
    with pytest.raises(M.ManifestError, match="C2 class"):
        _build(tree, _variant(tree, tmp_path / "a", c2_mismatch), tmp_path / "a")

    def stale_pointer(root):                   # the C3 pointer names another file version
        p = os.path.join(root, "scan_audio.latest.json")
        d = _load(p)
        d["sha256"] = "0" * 64
        _dump(d, p)
    with pytest.raises(M.ManifestError, match="pointer"):
        _build(tree, _variant(tree, tmp_path / "b", stale_pointer), tmp_path / "b")

    def cache_changed(root):                   # a cache that differs from its C5 done record
        p = os.path.join(root, "dtu", C.CACHE_FILE["A"])
        a = np.load(p, allow_pickle=False)
        os.unlink(p)
        a[0, 0] += 1
        np.save(p, a, allow_pickle=False)
    with pytest.raises(M.ManifestError, match="done record"):
        _build(tree, _variant(tree, tmp_path / "c", cache_changed), tmp_path / "c")

    def wrong_family(root):                    # a provisional family name that maps to no C3 family of its stream
        p = os.path.join(root, "fau", "pieces.json")
        t = _load(p)
        t["presentations"][0]["family_name"] = "fau:999"
        _dump(t, p)
    with pytest.raises(M.ManifestError, match="provisional"):
        _build(tree, _variant(tree, tmp_path / "d", wrong_family), tmp_path / "d")
    with pytest.raises(M.ManifestError, match="declared exclusion"):
        _build(tree, tree["root"], tmp_path / "e", declared=M.DECLARED_EXCLUSIONS)      # sub-051 audiobook_12_2 is not in the fixture


def test_results_already_present_refuse_production(tree, tmp_path):
    plan_ext = tmp_path / "plan_ext.jsonl"
    units = tmp_path / "units"
    units.mkdir()
    plan_ext.write_text(json.dumps({"experiment_id": "ALN3X_00000000000000aa", "family_id": "ALN32_PUBLIC_AUDIO_PRIOR_DONOR",
                                    "spec": {"manifest_sha256": "ab" * 32}}) + "\n")
    ctx = M._Ctx(tree["root"], "local", _quiet)
    rec, shas = M.guard_results(ctx, str(plan_ext), str(units))
    assert rec["n_e34_rows"] == 1 and rec["n_e34_records"] == 0 and shas == {"ab" * 32}
    (units / "ALN3X_00000000000000aa.json").write_text("{}")
    with pytest.raises(M.Refused, match="E34 unit records"):
        M.guard_results(M._Ctx(tree["root"], "production", _quiet), str(plan_ext), str(units))


def test_output_locations(tree, tmp_path):
    with pytest.raises(M.Refused):
        M.resolve_mode(tree["root"], out=os.path.join(tree["root"], "x"), dry_run=True)         # a dry run never writes under --root
    with pytest.raises(M.Refused):
        M.resolve_mode(tree["root"], out=os.path.join(M.REPO, "private", "x"), dry_run=True)
    with pytest.raises(M.Refused):
        M.resolve_mode(tree["root"], out_private=os.path.join(M.REPO, "private", "x"))        # a synthetic build never writes there
    with pytest.raises(M.Refused):
        M.resolve_mode(tree["root"], out=str(tmp_path))                                       # --out is for dry runs only
    assert M.resolve_mode(tree["root"], out=str(tmp_path / "dry"), dry_run=True)[0] == "dry_run"
    if os.path.isdir(M.CACHE_ROOT):
        with pytest.raises(M.Refused):
            M.resolve_mode(M.CACHE_ROOT, out_private=str(tmp_path / "p"))                        # production: 0700 area only


def test_dry_run_writes_only_to_scratch_and_tolerates_missing_inputs(tree, tmp_path):
    root = os.path.join(tmp_path, "root")
    shutil.copytree(tree["root"], root, copy_function=_link, ignore=shutil.ignore_patterns("federici", "scan_audio*", "manifest*.json"))
    before = sorted(os.listdir(root))
    out = tmp_path / "dry"
    res = M.build_core(root, out=str(out), dry_run=True, aln3_plan=None, units_dir=None, plan_ext=None, declared=DECLARED_TEST, log=_quiet)
    assert sorted(os.listdir(root)) == before and not os.path.exists(os.path.join(root, M.MANIFEST))
    doc = _load(res["manifest"])
    assert res["manifest"] == str(out / M.MANIFEST) and doc["dry_run"]["private_ids_written"] is False
    miss = " ".join(doc["dry_run"]["missing"])
    assert "federici" in miss and "scan_audio" in miss and "private_bdf" in miss
    assert "federici" not in doc["cohorts"] and all(c["dataset"] != "private_bdf" for c in doc["cells"])
    assert os.path.exists(out / "private" / M.MANIFEST)


def test_cli(tree, tmp_path, capsys):
    assert M.main(["--part", "core", "--root", tree["root"], "--dry-run", "--out", os.path.join(tree["root"], "inside")]) == 3
    with pytest.raises(SystemExit):
        M.main(["--part", "nope", "--root", tree["root"]])
    assert M.main(["--part", "rich", "--root", tree["root"], "--out-private", tree["private"]]) == 1     # waits for C7
    capsys.readouterr()


def test_sparrkulee_content_excluded_for_one_target_leaves_the_shared_sets(fx, tree, tmp_path):
    """The real C3 scan flags SparrKULee fit (audiobook_4) and dev (audiobook_12_x) content against single targets: such a
    presentation leaves only that target's donor set, but it leaves the shared dev pool, every fixed set and the standardiser
    windows for all (sampler.selection_sets fails closed on them), and the overlap with a dev presentation is reported."""
    def edit(root):
        p = os.path.join(root, "scan_audio.json")
        d = _load(p)
        d["cross_cohort"]["donor_exclusions"]["federici"]["sparrkulee"] = ["podcast_2"]          # fit content
        d["cross_cohort"]["donor_exclusions"]["fau"]["sparrkulee"] = ["podcast_16"]              # dev content
        _dump(d, p)
        _dump({"schema": "prior33_scan_audio_latest_v1", "status": "ok", "file": "scan_audio.json", "sha256": _fsha(p)},
              os.path.join(root, "scan_audio.latest.json"))
    root = _variant(tree, tmp_path, edit)
    res = _build(tree, root, tmp_path, declared=())
    man = _load(res["full"])
    key = {p["key"]: p["id"] for p in man["presentations"]}
    p2, p16 = key[_sk_key("podcast_2")[0]], key[_sk_key("podcast_16")[0]]
    ds = man["donor_sets"]
    assert ds["federici"]["core"]["excluded_presentations"]["sparrkulee"] == [p2]
    assert ds["fau"]["core"]["excluded_presentations"]["sparrkulee"] == [p16] and not ds["dtu"]["core"]["excluded_presentations"]["sparrkulee"]
    S = man["segments"]["sparrkulee"]
    n_p2 = sum(S["presentation"][r] == p2 for r in man["pools"]["core"]["sparrkulee"])
    i = ds["federici"]["core"]["strata"].index("sparrkulee")
    assert ds["federici"]["core"]["n_segments"][i] == len(man["pools"]["core"]["sparrkulee"]) - n_p2 > 0
    assert ds["dtu"]["core"]["n_segments"][0] == len(man["pools"]["core"]["sparrkulee"]) == man["budget"]["N_SK"]
    for rows in (man["pools"]["dev"]["sparrkulee"], man["pools"]["bridge_cal"]["sparrkulee"], man["selection"]["fit_segments"],
                 man["selection"]["dev_queries"], man["bridge"]["cal_queries"]):
        assert not {S["presentation"][r] for r in rows} & {p2, p16}
    assert man["standardiser"]["left_out_presentations"] == [_sk_key("podcast_2")[0]]
    flag = next(c for c in man["checks"] if c["check"].startswith("no SparrKULee dev / bridge_cal presentation"))
    assert flag["ok"] is False and flag["detail"]["presentations"] == [_sk_key("podcast_16")[0]]
    pytest.importorskip("torch")
    from auditory_alignment_v3.prior33 import sampler as SM
    from auditory_alignment_v3.prior33 import views as V
    m = V.open_manifest(res["full"], res["full_sha256"])
    assert SM.selection_sets(m)["excluded_presentations_checked"] == 2


# ---------------------------------------------------------------------------------------------------------- review round 2 (M2e)
def _edit_scan(root, fn):
    """Edit the C3 scan of a variant tree with fn(doc) and re-point scan_audio.latest.json at it."""
    p = os.path.join(root, "scan_audio.json")
    d = _load(p)
    fn(d)
    _dump(d, p)
    _dump({"schema": "prior33_scan_audio_latest_v1", "status": "ok", "file": "scan_audio.json", "sha256": _fsha(p)},
          os.path.join(root, "scan_audio.latest.json"))


def test_private_out_is_where_the_consumers_read(tree):
    """The full copy goes where design §6.2 and every consumer read it (run_donor / run_target / bridge PRIVATE_MANIFEST,
    make_plan_ext_prior33 MANIFEST, whose sha256 every row quotes); production defaults to it."""
    from auditory_alignment_v3.prior33 import select as SEL
    assert M.PRIVATE_OUT == os.path.join(M.REPO, "private", "auditory_alignment_v3", "aln34", "prior33")
    assert 'OUT = os.path.join(REPO, "private", "auditory_alignment_v3")' in open(os.path.join(M.REPO, "auditory_alignment_v3", "core.py")).read()
    pat = 'os.path.join(core.OUT, "aln34", "prior33", "manifest.json")'
    seen = 0
    for rel in ("auditory_alignment_v3/prior33/run_donor.py", "auditory_alignment_v3/prior33/run_target.py",
                "auditory_alignment_v3/prior33/bridge.py", "private/auditory_alignment_v3/make_plan_ext_prior33.py"):
        p = os.path.join(M.REPO, rel)
        if os.path.exists(p):
            seen += 1
            assert pat in open(p).read(), rel
    assert seen >= 1
    assert M.RICH_DONOR_FAMILY == SEL.RICH_DONOR
    if os.path.isdir(M.CACHE_ROOT):
        assert M.resolve_mode(M.CACHE_ROOT)[2] == M.PRIVATE_OUT                 # nothing is written by resolve_mode


def test_unplayed_c3_exclusion_entries_are_mapped_by_code_or_reported(fx, tree, tmp_path, monkeypatch):
    """C3 lists a stream that no cached presentation plays (the real scan's FAU '123/distractor': a single-talker code whose stereo
    file carries a non-silent other channel): it is mapped to the presentations of its code and reported; a listed stream that no
    code maps is listed as unplayed; an entry naming no C3 stream refuses; C3's not_scanned / assumptions caveats are recorded."""
    n111 = next(r["length"] for r in _load(os.path.join(tree["root"], "fau", "streams.json"))["streams"] if r["name"] == "111/attended")

    def edit(d):
        d["streams"]["fau"].append({"stream": "111/distractor", "kind": "distractor", "keyed": False, "code": "111", "n": n111,
                                    "family": None, "family_offset": None, "offset_known": None, "source_sha256": "synthetic"})
        d["streams"]["dtu"].append({"stream": "t99", "kind": "attended", "keyed": True, "n": 640, "family": None,
                                    "family_offset": None, "offset_known": None, "source_sha256": "synthetic"})
        d["cross_cohort"]["donor_exclusions"]["dtu"]["fau"].append("111/distractor")
        d["cross_cohort"]["donor_exclusions"]["fau"]["dtu"].append("t99")
        d["cross_cohort"]["not_scanned"] = {"private_bdf": "not scanned: the private task stimuli are outside C3 (synthetic)"}
        d["assumptions"] = [{"item": "private_bdf donor overlap with the target's test stimuli", "status": "unverified", "detail": "x"},
                            {"item": "identity overlap across cohorts", "status": "unverifiable", "detail": "different sites (synthetic)"}]
    root = _variant(tree, tmp_path / "a", lambda r: _edit_scan(r, edit))
    res = _build(tree, root, tmp_path / "a")
    man = _load(res["full"])
    key = {p["key"]: p["id"] for p in man["presentations"]}
    for b in ("core", "rich", "csx"):
        ex = man["donor_sets"]["dtu"][b]["excluded_presentations"]["fau"]
        assert key["fau:111"] in ex and key["fau:122"] in ex                       # mapped by code, and the C3 overlap item
    assert key["fau:111"] not in man["donor_sets"]["federici"]["core"]["excluded_presentations"]["fau"]
    i = man["donor_sets"]["dtu"]["core"]["strata"].index("fau")
    S = man["segments"]["fau"]
    n111_rows = sum(S["presentation"][r] == key["fau:111"] for r in man["pools"]["core"]["fau"])
    assert n111_rows > 0
    assert man["donor_sets"]["dtu"]["core"]["n_segments"][i] == \
        sum(S["presentation"][r] not in {key["fau:111"], key["fau:122"]} for r in man["pools"]["core"]["fau"])
    os_ = man["overlap_scan"]
    ent = {e["stream"]: e for e in os_["targets"]["dtu"]["fau"]["entries"]}
    assert ent["111/distractor"]["mapped_by"] == "stimulus_code" and ent["111/distractor"]["presentations"] == ["fau:111"]
    assert {e["stream"]: e["mapped_by"] for e in os_["targets"]["fau"]["dtu"]["entries"]}["t99"] == "unplayed"
    chk = {c["check"]: c for c in man["checks"]}
    mapped = next(c for n, c in chk.items() if n.startswith("C3 donor_exclusions entries that no cached presentation plays"))
    assert mapped["ok"] is False and mapped["detail"][0]["presentations"] == ["fau:111"]
    unplayed = next(c for n, c in chk.items() if n.startswith("C3 donor_exclusions entries that no cached piece plays"))
    assert unplayed["ok"] is False and ["fau", "dtu", "t99", "attended"] in unplayed["detail"]
    choice = next(c for c in man["declared_choices"] if c["choice"] == "c3_unplayed_by_code")
    assert choice["enabled"] is True and choice["effect"] == [{"target": "dtu", "donor": "fau", "stream": "111/distractor", "code": "111",
                                                               "presentations": ["fau:111"], "core_pool_rows_removed": n111_rows,
                                                               "core_pool_rows": len(man["pools"]["core"]["fau"])}]
    # C3's caveats: private_bdf never scanned (its empty lists mean 'not scanned'), identity overlap unverifiable
    for c, v in os_["targets"]["private_bdf"].items():
        assert v["status"] == "not_scanned" and v["n_listed"] == 0 and "not scanned" in v["not_scanned"]
    assert os_["targets"]["dtu"]["fau"]["status"] == "scanned"
    assert man["inputs"]["c3"]["not_scanned"] == {"private_bdf": "not scanned: the private task stimuli are outside C3 (synthetic)"}
    assert len(man["inputs"]["c3"]["assumptions"]) == 2
    assert man["identity_overlap"]["status"] == "unverifiable" and man["identity_overlap"]["source"].startswith("C3")
    priv = chk["overlap of the private_bdf target's test stimuli with the donors is verified"]
    assert priv["ok"] is False and priv["detail"]["status"].startswith("unverified")
    # C3's literal rule instead (the lead's alternative): the code's presentations stay
    monkeypatch.setattr(M, "MAP_UNPLAYED_BY_CODE", False)
    man2 = _load(_build(tree, root, tmp_path / "b")["full"])
    assert key["fau:111"] not in man2["donor_sets"]["dtu"]["core"]["excluded_presentations"]["fau"]
    assert {e["stream"]: e["mapped_by"] for e in man2["overlap_scan"]["targets"]["dtu"]["fau"]["entries"]}["111/distractor"] == "unplayed"
    monkeypatch.undo()
    # an entry that names no C3 stream (a spelling mismatch) refuses the build
    root3 = _variant(tree, tmp_path / "c", lambda r: _edit_scan(
        r, lambda d: d["cross_cohort"]["donor_exclusions"]["dtu"]["fau"].append("999/distractor")))
    with pytest.raises(M.ManifestError, match="names a stream of C3"):
        _build(tree, root3, tmp_path / "c")


def test_c3_caveats_default_and_identity_overlap(built):
    """Without C3 caveats every list is 'scanned'; identity overlap is still recorded as unverifiable (design §3.4.5)."""
    man = built["full_doc"]
    assert all(v["status"] == "scanned" for t in man["overlap_scan"]["targets"].values() for v in t.values())
    assert set(man["overlap_scan"]["targets"]) == set(M.TARGETS)
    assert man["identity_overlap"]["status"] == "unverifiable" and "3.4.5" in man["identity_overlap"]["source"]
    assert man["overlap_scan"]["map_unplayed_by_code"] is True and man["inputs"]["c3"]["not_scanned"] == {}
    ch = {c["choice"]: c for c in man["declared_choices"]}
    assert set(ch) == {"shared_dev_bridge_cal", "shared_standardiser", "c3_unplayed_by_code", "declared_exclusions"}
    assert ch["shared_dev_bridge_cal"]["effect"]["kept"]["dev"]["rows"] == len(man["pools"]["dev"]["sparrkulee"])
    assert ch["shared_standardiser"]["effect"]["left_out_presentations"] == man["standardiser"]["left_out_presentations"]
    assert ch["c3_unplayed_by_code"]["effect"] == []
    d = ch["declared_exclusions"]["effect"]
    assert len(d) == 1 and d[0]["run_id"] == "sub-052_podcast_16" and d[0]["n_segments"] > 0


def test_ignored_stream_without_a_c3_row_is_refused(tree, tmp_path):
    """An ignored stream a presentation plays must have a C3 row with C5's source sha and length, as attended streams must."""
    def drop(d):
        d["streams"]["fau"] = [r for r in d["streams"]["fau"] if r["stream"] != "215/distractor"]
    with pytest.raises(M.ManifestError, match="ignored stream a presentation plays"):
        _build(tree, _variant(tree, tmp_path / "a", lambda r: _edit_scan(r, drop)), tmp_path / "a")

    def resha(d):
        next(r for r in d["streams"]["fau"] if r["stream"] == "215/distractor")["source_sha256"] = "0" * 64
    with pytest.raises(M.ManifestError, match="masker / distractor source_sha256"):
        _build(tree, _variant(tree, tmp_path / "b", lambda r: _edit_scan(r, resha)), tmp_path / "b")


def test_dtu_unread_file_trials_are_declared_with_their_reason(tree, tmp_path):
    """The real C5 DTU table: excluded_trials empty, the trials of sub-024_run-2 under unread_files and inventory_reconciliation
    .not_loaded with status unread_file and reason None. Each is a declared aln3_loader_filter exclusion carrying the file's reason,
    with unused-table rows; an absence without a recorded reason, or a file count that does not add up, refuses the build."""
    trials = (("ss", "t08"), ("ss", "t02"), ("ss", "t03"), ("cs", "t04"))
    unread = [{"file": "sub-024_run-2", "trial": f"trial_00{k}", "subject": "sub-024", "hearing": "nh", "kind": kind, "target_sha": h,
               "status": "unread_file", "reason": None} for k, (kind, h) in enumerate(trials, 1)]

    def edit(root, extra=(), n=4):
        p = os.path.join(root, "dtu", "pieces.json")
        t = _load(p)
        t["excluded_trials"] = []
        t["checks"]["inventory_reconciliation"]["not_loaded"] = [dict(r) for r in unread] + list(extra)
        t["unread_files"] = [dict(DTU_UNREAD, n_inventory_trials=n)]
        _dump(t, p)
    root = _variant(tree, tmp_path / "a", edit)
    man = _load(_build(tree, root, tmp_path / "a")["full"])
    lf = [e for e in man["exclusions"] if e["rule"] == "aln3_loader_filter"]
    assert sorted(e["run_id"] for e in lf) == sorted(f"sub-024_run-2:{r['trial']}" for r in unread)
    assert all(e["declared"] and e["detail"]["status"] == "unread_file" and e["detail"]["reason"] == DTU_UNREAD["reason"] for e in lf)
    assert man["exclusion_summary"]["n_by_rule"]["aln3_loader_filter"] == 4
    rc = man["dtu_reconciliation"]
    assert [r["trial"] for r in rc["absent_trials"]] == ["trial_001", "trial_002", "trial_003"]
    assert all(r["reason"] == DTU_UNREAD["reason"] for r in rc["absent_trials"]) and len(rc["not_loaded"]) == 4
    assert rc["not_loaded_by_status"] == {"nh/cs/unread_file": 1, "nh/ss/unread_file": 3} and rc["excluded_trials"] == []
    un = {u["what"]: u for u in man["unused"] if u["cohort"] == "dtu"}
    assert un["NH single-talker inventory trials not in the C5 cache (unread_file)"]["n"] == 3
    assert un["NH two-talker inventory trials not in the C5 cache (unread_file)"]["n"] == 1
    assert DTU_UNREAD["reason"] in un["NH two-talker inventory trials not in the C5 cache (unread_file)"]["reason"]
    absent = {"file": "sub-021", "trial": "trial_077", "subject": "sub-021", "hearing": "nh", "kind": "ss", "target_sha": "t01",
              "status": "absent", "reason": None}
    with pytest.raises(M.ManifestError, match="DTU: every inventory trial"):
        _build(tree, _variant(tree, tmp_path / "b", lambda r: edit(r, extra=[absent])), tmp_path / "b")
    with pytest.raises(M.ManifestError, match="DTU: every inventory trial"):
        _build(tree, _variant(tree, tmp_path / "c", lambda r: edit(r, n=5)), tmp_path / "c")


def test_unverifiable_kept_does_not_count_declared_or_non_donor_runs(tree, tmp_path):
    """unverifiable_kept counts the C2-unverifiable runs that stay in a donor role; a declared-excluded run and a
    holdout_seen_content run that C2 also classes unverifiable are listed by role, not counted as kept."""
    targets = {("052", "podcast_16"), ("051", "audiobook_1_1")}           # the declared dev run, a holdout_seen_content run

    def edit(root):
        d = os.path.join(root, "sparrkulee")
        lines = [json.loads(x) for x in open(os.path.join(d, "align_audit.jsonl")) if x.strip()]
        for r in lines:
            if (r["sub"], r["stimulus"]) in targets:
                r["class"] = "unverifiable"
        with open(os.path.join(d, "align_audit.jsonl"), "w") as f:
            f.write("\n".join(json.dumps(r, sort_keys=True) for r in lines) + "\n")
        a_sha = _fsha(os.path.join(d, "align_audit.jsonl"))
        meta = _load(os.path.join(d, "align_audit_meta.json"))
        meta.update(align_audit_sha256=a_sha, classes=dict(collections.Counter(r["class"] for r in lines)))
        _dump(meta, os.path.join(d, "align_audit_meta.json"))
        t = _load(os.path.join(d, "runs.json"))
        for r in t["runs"]:
            if (r["sub"], r["stimulus"]) in targets:
                r["audit"]["clock"] = "unverifiable"
        t["inputs"]["align_audit_sha256"] = a_sha
        _dump(t, os.path.join(d, "runs.json"))
    root = _variant(tree, tmp_path, edit)
    man = _load(_build(tree, root, tmp_path)["full"])
    es = man["exclusion_summary"]
    runs = _load(os.path.join(root, "sparrkulee", "runs.json"))["runs"]
    roles = collections.Counter(r["role"] for r in runs if r["audit"]["clock"] == "unverifiable")
    assert roles["holdout_seen_content"] == 1 and roles["dev"] == 1 and roles["fit"] == len(UNVERIFIABLE_KEPT)
    assert es["unverifiable_by_role"] == dict(sorted(roles.items()))
    assert es["unverifiable_kept"] == len(UNVERIFIABLE_KEPT)                     # not 2 + the declared run + the holdout run
    assert es["unverifiable_declared_excluded"] == ["sub-052_podcast_16"]
    assert es["c2_classes"]["unverifiable"] == sum(roles.values())


def test_declared_exclusion_basis_and_c2_numbers_are_checked(tree, tmp_path):
    """A declaration's cited file must have the cited sha256, and the C2 numbers its reason quotes must be C2's (else refused)."""
    lines = [json.loads(x) for x in open(os.path.join(tree["root"], "sparrkulee", "align_audit.jsonl")) if x.strip()]
    a = next(r for r in lines if r["sub"] == "052" and r["stimulus"] == "podcast_16")
    scout = tmp_path / "scout.json"
    scout.write_text(json.dumps({"052:podcast_16": {"tau_samples": 0}}))
    good = dict(DECLARED_TEST[0], basis=[{"file": str(scout), "sha256": _fsha(scout), "entry": "052:podcast_16"}],
                expect_c2={"class": a["class"], "tau": a["tau"], "z_2dp": a["z"]}, conflicts=["synthetic conflict"])
    root = _variant(tree, tmp_path / "v", lambda r: None)                    # never rewrite the shared tree's manifest
    man = _load(_build(tree, root, tmp_path / "a", declared=(good,))["full"])
    e = next(x for x in man["exclusions"] if x["rule"] == "declared_structural_exclusion")
    assert e["detail"]["basis"] == good["basis"] and e["detail"]["conflicts"] == ["synthetic conflict"]
    assert any(c["check"].endswith("C2 gives the class and lags its reason quotes") and c["ok"] for c in man["checks"])
    with pytest.raises(M.ManifestError, match="C2 gives the class"):
        _build(tree, root, tmp_path / "b", declared=(dict(good, expect_c2={"class": "misaligned", "tau": [-6, -6], "z_2dp": [9, 9]}),))
    with pytest.raises(M.ManifestError, match="cited sha256"):
        _build(tree, root, tmp_path / "c", declared=(dict(good, basis=[dict(good["basis"][0], sha256="0" * 64)]),))
    res = _build(tree, root, tmp_path / "d", declared=(dict(good, basis=[dict(good["basis"][0], file=str(tmp_path / "gone.json"))]),))
    assert any("gone.json" in n for n in res["notes"])                         # a synthetic build only notes a missing basis file
    # the real declaration's C2 numbers round-trip through the same normalisation
    d0 = M.DECLARED_EXCLUSIONS[0]
    fake = {"class": "unverifiable", "tau": [-1668, -2220], "z": [3.4019701906009323, 3.1872026679635708],
            "diagnostic": {"full": {"tau": -566, "z": 4.041188}, "halves": [{"tau": -568, "z": 3.290058}, {"tau": -565, "z": 3.116329}]}}
    exp = M._expected_c2(d0["expect_c2"])
    assert {k: v for k, v in M.c2_numbers(fake).items() if k in exp} == exp


def test_band_sd_by_participant_equals_one_with_band_sd_call(tree):
    """The per-participant derivation (bounded memory) gives the one-call build_public.with_band_sd values for every participant
    mode_c_scales reads, and the same stats_band."""
    from auditory_alignment_v3.prior33 import build_public as BP
    d = os.path.join(tree["root"], "sparrkulee")
    t = _load(os.path.join(d, "runs.json"))
    one = BP.with_band_sd(t, d)
    per = M.band_sd_by_participant(t, d, log=_quiet)
    assert per["cohort_info"]["stats_band"] == one["cohort_info"]["stats_band"]
    n = 0
    for a, b in zip(one["participants"], per["participants"]):
        assert a["participant"] == b["participant"]
        if M._mode_c_donor(a):
            n += 1
            assert b["sd_prez"]["A_2_8"] == a["sd_prez"]["A_2_8"] and b["sd_prez_uV"]["A_2_8"] == a["sd_prez_uV"]["A_2_8"]
        else:
            assert "A_2_8" not in b["sd_prez"]
    assert n == per["n_derived"] > 0


def test_rich_guard_refuses_a_changed_supplement_in_production(tree, tmp_path):
    """--part rich: registered rows quoting another manifest_rich_sha256, or a rich-block record with a supplement that would change,
    refuse a production build (a local build only notes them)."""
    plan_ext, units = tmp_path / "plan_ext.jsonl", tmp_path / "units"
    units.mkdir()
    row = {"experiment_id": "ALN3X_00000000000000r1", "family_id": M.RICH_DONOR_FAMILY,
           "spec": {"block": "rich", "manifest_sha256": "ab" * 32, "manifest_rich_sha256": "cd" * 32}}
    plan_ext.write_text(json.dumps(row) + "\n" + json.dumps({"experiment_id": "ALN3X_0000000000000001", "family_id": "B_X"}) + "\n")
    ctx = M._Ctx(tree["root"], "production", _quiet)
    with pytest.raises(M.Refused, match="manifest_rich_sha256"):
        M.guard_rich(ctx, "ef" * 32, None, str(plan_ext), str(units))
    rec = M.guard_rich(ctx, "cd" * 32, None, str(plan_ext), str(units))
    assert rec["n_rich_rows"] == 1 and rec["n_rich_records"] == 0 and rec["registered_manifest_rich_sha256"] == ["cd" * 32]
    (units / "ALN3X_00000000000000r1.json").write_text("{}")
    with pytest.raises(M.Refused, match="rich-block unit records"):
        M.guard_rich(ctx, "cd" * 32, "00" * 32, str(plan_ext), str(units))
    assert M.guard_rich(ctx, "cd" * 32, "cd" * 32, str(plan_ext), str(units))["n_rich_records"] == 1
    loc = M._Ctx(tree["root"], "local", _quiet)
    M.guard_rich(loc, "ef" * 32, "00" * 32, str(plan_ext), str(units))
    assert any("manifest_rich_sha256" in n for n in loc.notes) and any("would change" in n for n in loc.notes)
