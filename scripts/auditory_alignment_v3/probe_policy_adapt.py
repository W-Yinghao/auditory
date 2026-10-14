"""Engineering probe for the D_ADAPT policy arms (ADDENDUM_04; scratch dir probe_out, full units):
policy re-resolves identically; the rebuilt chosen B/C model re-evaluates to its recorded evaluation (strict rebuild);
adapter 'none' reproduces the base representation; the unit completes with code_group adapt_policy and its policy record."""
import json, sys, time
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch
from auditory_alignment_v3 import run as R3, core, policy, policy_models, fm_dense, fm_complement
from auditory_alignment_v3.run_adapt_policy import AdaptedFM
S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/probe_out"
rows = R3.all_rows(); core.load_rows = lambda: rows; dev = torch.device("cuda")


def leaves(x, pre=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f"{pre}/{k}")
    elif isinstance(x, (list, tuple)):
        for i, v in enumerate(x):
            yield from leaves(v, f"{pre}[{i}]")
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield pre, float(x)


for arch in ("dense_fm_policy", "complement_policy"):
    r = next(r for r in rows if r["family_id"] == "D_ADAPT" and r["dataset"] == "dtu" and r["seed"] == 3401 and r["subject_fold"] == 0 and r["content_fold"] == 0
             and r["spec"]["architecture"] == arch and r["spec"]["adapter"] == "input_spatial" and r["spec"]["objective"] == "NCE")
    p1, p2 = policy.resolve(r, rows, core.OUT), policy.resolve(r, rows, core.OUT)
    assert p1 is not None and p1 == p2, "policy not deterministic / not resolvable"
    t0 = time.time(); m = policy_models.build_chosen(p1, dev); rc = m["record"]
    evf = fm_dense.evaluate_dense if m["kind"] == "dense" else fm_complement.evaluate_complement
    ev = json.loads(json.dumps(evf(m["bound"], m["base"].model, m["head"], m["bt"], m["coh"], rc["objective_calibration"], m["grid"]), default=float))
    a, b = dict(leaves(ev)), dict(leaves(rc["eval"]))
    common = sorted(set(a) & set(b)); diff = max(abs(a[k] - b[k]) for k in common) if common else None
    print(f"{arch}: chosen {p1['chosen']} ({p1['chosen_row']['spec']}); rebuild re-eval vs record: {len(common)}/{len(b)} leaves, max abs diff {diff} ({time.time() - t0:.0f} s)", flush=True)
    assert len(common) == len(b) and diff is not None and diff < 1e-3, "rebuilt model does not reproduce the chosen unit's evaluation"
    fb = m["base"]; e0 = torch.tensor([s["e0"] for s in m["coh"].segments[:4]], device=dev); t = torch.arange(0, m["bt"].seg_len, m["grid"], device=dev)[None].expand(4, -1)
    with torch.no_grad():
        idd = float((AdaptedFM(fb, "none", m["coh"].n_ch, m["d"]).to(dev)(e0, t) - fb(e0, t)).abs().max())
        ids = float((AdaptedFM(fb, "input_spatial", m["coh"].n_ch, m["d"]).to(dev)(e0, t) - fb(e0, t)).abs().max())
    print(f"  identity: none {idd:.2e}, input_spatial at init {ids:.2e}", flush=True); assert idd == 0.0 and ids < 1e-5
    del m; torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()
    R3.run_unit(r, S)
    rec = json.load(open(f"{S}/units/{r['experiment_id']}.json"))
    assert rec["status"] == "complete" and rec["code_group"] == "adapt_policy" and rec["policy"]["chosen"] == p1["chosen"], rec.get("error")
    pp = rec["eval"]["per_participant"]
    print(f"  unit complete: {len(pp)} test participants, steps {rec['eval']['steps']['chosen']} {rec['eval']['steps']['scores']}, "
          f"{rec['total_seconds']} s, gpu peak {rec['gpu_peak_allocated_mb']} MB, code_hash {rec['code_hash']}", flush=True)
print("ALL D_ADAPT POLICY PROBES PASSED")
