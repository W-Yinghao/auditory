"""Environment probe (Slurm): foundation-model access and package versions. Prints no credentials."""
import hashlib, json, os
out = {}
try:
    import braindecode, torch
    out["eeg2025_braindecode"] = braindecode.__version__; out["torch"] = torch.__version__; out["cuda"] = torch.cuda.is_available()
    import braindecode.models as bm
    out["braindecode_has_CBraMod"] = hasattr(bm, "CBraMod"); out["braindecode_has_REVE"] = hasattr(bm, "REVE")
except Exception as ex:
    out["braindecode_error"] = repr(ex)
try:
    import peft; out["peft"] = peft.__version__
except Exception as ex:
    out["peft"] = repr(ex)
from huggingface_hub import HfApi
api = HfApi()
for repo in ("brain-bzh/reve-base", "weighting666/CBraMod", "braindecode/cbramod-pretrained"):
    try:
        info = api.model_info(repo, files_metadata=True)
        out[repo] = {"sha": info.sha, "gated": getattr(info, "gated", None), "license": (info.card_data or {}).get("license") if info.card_data else None,
                     "files": {s.rfilename: {"size": s.size, "lfs_sha256": (s.lfs or {}).get("sha256") if isinstance(s.lfs, dict) else getattr(s.lfs, "sha256", None)} for s in info.siblings}}
    except Exception as ex:
        out[repo] = {"error": type(ex).__name__ + ": " + str(ex)[:200]}
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
loc = {"colleague_reve_base_official": "<other user's cache>/reve_base_official/weights.safetensors",
       "shared_cache_cbramod": "<other user's cache>/hub/models--weighting666--CBraMod/snapshots",
       "own_cache_braindecode_cbramod": os.path.expanduser("~/.cache/huggingface/hub/models--braindecode--cbramod-pretrained/snapshots")}
for k, p in loc.items():
    try:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    q = os.path.join(root, f); out[f"{k}:{os.path.relpath(q, p)}"] = {"sha256": sha(q), "size": os.path.getsize(q)}
        else:
            out[k] = {"sha256": sha(p), "size": os.path.getsize(p)}
    except Exception as ex:
        out[k] = repr(ex)
print(json.dumps(out, indent=1))
