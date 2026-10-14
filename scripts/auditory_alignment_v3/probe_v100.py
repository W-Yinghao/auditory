"""V100 engineering probe before adding V100 to the ALN3 pool partitions (user 2026-10-14). Scratch dir probe_out_v100.
Checks: device / precision regime; a D_ATTENTION dense_fm_policy alignment_plus_selection unit (2 epochs), a D_ADAPT
dense_fm_policy input_spatial unit (full) and the most memory-hungry remaining FM unit type (B_DENSE DTU REVE panel, 1 epoch)
complete on a 16 GB V100, with their GPU memory peaks."""
import json, os, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import torch
from auditory_alignment_v3 import run as R3, core, fm_dense
p = torch.cuda.get_device_properties(0)
print("device", torch.cuda.get_device_name(0), "capability", torch.cuda.get_device_capability(0), f"memory {p.total_memory / 2**30:.1f} GiB",
      "cudnn.allow_tf32", torch.backends.cudnn.allow_tf32, "matmul.allow_tf32", torch.backends.cuda.matmul.allow_tf32, "torch", torch.__version__, flush=True)
assert "V100" in torch.cuda.get_device_name(0)
fm_dense.WARMUP, fm_dense.UNFREEZE_EVERY = 1, 1
S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/probe_out_v100"; os.makedirs(S, exist_ok=True)
rows = R3.all_rows(); core.load_rows = lambda: rows
f = lambda **kw: next(r for r in rows if r["dataset"] == "dtu" and r["subject_fold"] == 0 and r["content_fold"] == 0 and all(
    (r["spec"].get(k) == v if k not in ("family_id", "seed") else r[k] == v) for k, v in kw.items()))
tests = [(f(family_id="D_ATTENTION", architecture="dense_fm_policy", training_task="alignment_plus_selection", integrator="mean_score", objective="NCE", seed=3401), 2),
         (f(family_id="D_ADAPT", architecture="dense_fm_policy", adapter="input_spatial", objective="NCE", seed=3401), None),
         (f(family_id="B_DENSE", architecture="reve", adaptation="pretrained_full", readout="dense_query", objective="NCE", seed=3407), 1)]
for r, ep in tests:
    torch.cuda.reset_peak_memory_stats()
    R3.run_unit(r, S, epochs=ep)
    rec = json.load(open(f"{S}/units/{r['experiment_id']}.json"))
    assert rec["status"] == "complete", rec.get("error")
    print(f"{r['family_id']} {r['spec'].get('architecture')} OK: {rec['total_seconds']} s, gpu peak {rec['gpu_peak_allocated_mb']} MB, device {rec['device']}, "
          f"max reserved {torch.cuda.max_memory_reserved() / 2**20:.0f} MB", flush=True)
print("V100 PROBE PASSED")
