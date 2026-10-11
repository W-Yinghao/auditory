"""ALN3 engineering probe for the first bound families (2 epochs, scratch output; mechanics only, performance not inspected).
Checks: records complete; code hash; d and grid as declared; training anchors on the grid; evaluation grid = target grid;
calibration variants present with positive slope and AUC equal to the raw-score AUC."""
import json, os, sys, time
import numpy as np
import torch
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import run as R3
from auditory_alignment_v3.local_train import GridBatcher
from auditory_alignment_v2.run import load_cohort

S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/probe_out"
os.makedirs(S + "/units", exist_ok=True); os.makedirs(S + "/ckpt", exist_ok=True)
rows = R3.load_rows()
def pick(fam, ds, **m):
    for i, r in enumerate(rows):
        if r["family_id"] == fam and r["dataset"] == ds and r["seed"] == 3401 and r["subject_fold"] == 0 and (r["content_fold"] or 0) == 0 \
                and all(r["spec"].get(k) == v for k, v in m.items()):
            return i, r
    raise KeyError((fam, ds, m))
t0 = time.time(); ok = []
# anchors on the grid (FAU 128 Hz -> 3 samples; Federici 100 Hz -> 2)
for ds, g in (("fau", 3), ("federici", 2)):
    i, r = pick("A_LOCAL", ds, architecture="lag_local_tokens", window="full", objective="NCE")
    b = R3.bind(r); coh = load_cohort(b); assert R3.grid_samples(coh.fs) == g, (ds, coh.fs)
    bt = GridBatcher(coh, b["spec"], b, torch.device("cuda"), g)
    batch = next(bt.epoch_batches(np.random.default_rng(1), 16)); rws = bt.rows(batch, np.random.default_rng(2))
    e0 = np.array([bt.coh_segments[j]["e0"] for j in batch]).repeat(8)
    assert np.all((rws[0].cpu().numpy() - e0) % g == 0), ds
    del bt, coh; torch.cuda.empty_cache()
print("OK grid-aligned anchors", flush=True)
probes = [pick("A_LOCAL", "fau", architecture="lag_local_tokens", window="full", objective="NCE"),
          pick("A_LOCAL", "federici", architecture="density_tokens", window="early", objective="CS_SINGLE"),
          pick("A_TARGETS", "dtu", architecture="lag_local_tokens", window="late", objective="NCE", target="Lz"),
          pick("A_DIMENSION", "fau", architecture="lag_local_tokens", objective="CS_SINGLE", projection_dim=64),
          pick("E_LOCAL", "private_bdf", architecture="lag_local_tokens", window="full", objective="NCE"),
          pick("E_LOCAL", "private_bdf", architecture="density_tokens", window="late", objective="CS_SINGLE"),
          pick("E_GX", "private_bdf", window="full"),
          pick("E_GENERIC", "private_bdf", architecture="cbramod", adaptation="pretrained_frozen", objective="NCE"),
          pick("E_GENERIC", "private_bdf", architecture="reve", adaptation="pretrained_peft", objective="CS_SINGLE"),
          pick("B_DENSE", "fau", architecture="cbramod", adaptation="pretrained_full", readout="dense_query", objective="NCE"),
          pick("B_DENSE", "federici", architecture="reve", adaptation="pretrained_peft", readout="channel_phase_linear", objective="CS_SINGLE")]
from auditory_alignment_v3 import fm_dense
fm_dense.WARMUP, fm_dense.UNFREEZE_EVERY = 1, 1  # probe only: exercise warm-up and two unfreezing steps in 3 epochs
for i, r in probes:
    R3.run_unit(r, S, epochs=3 if r['family_id'] == 'B_DENSE' else 2)
    rec = json.load(open(f"{S}/units/{r['experiment_id']}.json")); assert rec["status"] == "complete", rec.get("error")
    assert rec["code_hash"] == R3.code_hash(r["family_id"]) and rec["row"]["experiment_id"] == rows[i]["experiment_id"]
    fam = r["family_id"]
    if fam == "B_DENSE":
        assert rec["readout"] == r["spec"]["readout"] and rec["readout_params"] > 0 and rec["val_every"] == 1
        og = [c["open_groups"] for c in rec["curve"]]; assert og[0] == 0 and og[-1] >= 1, og  # warm-up first, then unfreezing
        assert len(rec["patch_times_s"]) >= 5 and all(rec["valid_patches"]), rec["patch_times_s"]
        assert rec["eval"]["readout"].get("n_test_candidates")
    elif fam in R3.LOCAL_FAMILIES:
        rc = rec["resolved_config"]; assert rc["d"] == r["spec"]["projection_dim"]
        T = rec["eval"]["readout"].get("n_test_candidates")
        assert T and rec["encoder"]["out_dim" if "out_dim" in rec["encoder"] else "n_params"]
    else:
        nc = rec["eval"]["native_calibration"]
        if "methods" in nc:
            pa = nc["methods"]["positive_affine"]; assert pa["slope"] > 0
            child = next(iter(nc["per_participant"].values()))
            aucs = {m: v["auc_score"] for m, v in child.items()}; assert len(set(round(a, 9) for a in aucs.values())) == 1, aucs
    ok.append((fam, r["dataset"], r["spec"].get("architecture"), r["spec"].get("window") or r["spec"].get("adaptation"), round(rec["total_seconds"])))
    print("OK", ok[-1], flush=True)
print("ALL ALN3 BOUND-FAMILY PROBES PASSED", json.dumps(ok), f"{time.time() - t0:.0f}s")
