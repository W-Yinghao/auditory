"""Technical probe (Slurm GPU): foundation backbones load, channel positions resolve, shapes, gradients, time and memory
per adaptation recipe on real segments. Not a scientific test."""
import json, os, sys, time
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch
from auditory_alignment_v2.foundation_adapter import Backbone, PatchHead, CHANNELS
from auditory_alignment import data

dev = torch.device("cuda")
res = {"gpu": torch.cuda.get_device_name(0)}
coh = data.load_fau(0, kinds=("ss",))
segs = [s for s in coh.segments if s["role"] == "fit"][:32]
E = coh.eeg; L = coh.meta["seg_len"]
x_fau = torch.tensor(np.stack([E[:, s["e0"]:s["e0"] + L] for s in segs]), device=dev).float()  # [32, 31, 640]
res["fau_segment_shape"] = list(x_fau.shape)
for arch in ("cbramod", "reve"):
    for ds, n_ch, fs, T in (("dtu", 64, 128, 640), ("federici", 32, 100, 500), ("private_bdf", 20, 250, 200)):
        try:
            bb = Backbone(arch, ds, "pretrained_frozen", fs).to(dev)
            with torch.no_grad():
                tok = bb(torch.randn(4, n_ch, T, device=dev))
            res[f"{arch}|{ds}|shape"] = list(tok.shape)
        except Exception as ex:
            res[f"{arch}|{ds}|error"] = f"{type(ex).__name__}: {str(ex)[:300]}"
    for a in ("random_full", "pretrained_frozen", "pretrained_peft", "pretrained_partial", "pretrained_full"):
        torch.cuda.reset_peak_memory_stats()
        try:
            bb = Backbone(arch, "fau", a, 128).to(dev); hd = PatchHead(bb.E, 16).to(dev)
            params = [p for p in list(bb.parameters()) + list(hd.parameters()) if p.requires_grad]
            opt = torch.optim.AdamW(params, lr=1e-4)
            bb.train(); hd.train()
            for it in range(6):
                if it == 1:
                    torch.cuda.synchronize(); t0 = time.time()
                u = hd(bb(x_fau))  # [32, P, 16]
                loss = -(u[:, :, 0].mean())
                opt.zero_grad(); loss.backward(); opt.step()
            torch.cuda.synchronize()
            g = [p.grad for p in params if p.grad is not None]
            res[f"{arch}|{a}"] = {"out": list(u.shape), "sec_per_step_32seg": round((time.time() - t0) / 5, 4), "peak_mb": round(torch.cuda.max_memory_allocated() / 2**20),
                                  "grads_finite": bool(all(torch.isfinite(x).all() for x in g)), "patch_starts_s": bb.patch_starts(1000), "contract": bb.contract()}
        except Exception as ex:
            res[f"{arch}|{a}"] = {"error": f"{type(ex).__name__}: {str(ex)[:400]}"}
        finally:
            torch.cuda.empty_cache()
print(json.dumps(res, indent=1, default=str))
