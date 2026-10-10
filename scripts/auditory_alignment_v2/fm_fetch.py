"""Fetch pinned foundation-model assets (Slurm; network). Records revisions and SHA256; prints no credentials."""
import hashlib, json, os, subprocess
from huggingface_hub import HfApi, snapshot_download
ROOT = "/projects/EEG-foundation-model/auditory_public/foundation_models"
os.makedirs(ROOT, exist_ok=True)
api = HfApi(); out = {}
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
for repo, rev in (("brain-bzh/reve-base", "dc2a075c287bb2f6c04ee5875bd79535a0f7dba6"), ("weighting666/CBraMod", "500543c7e30bda1b22bfd51a49301b238dee21fd")):
    d = os.path.join(ROOT, repo.replace("/", "__") + "@" + rev[:7])
    snapshot_download(repo, revision=rev, local_dir=d)
    out[repo] = {"revision": rev, "dir": d, "files": {f: sha(os.path.join(d, f)) for f in sorted(os.listdir(d)) if os.path.isfile(os.path.join(d, f))}}
# REVE electrode position bank (separate repo, if present)
for cand in ("brain-bzh/reve-positions",):
    try:
        info = api.model_info(cand)
        d = os.path.join(ROOT, cand.replace("/", "__") + "@" + info.sha[:7])
        snapshot_download(cand, revision=info.sha, local_dir=d)
        out[cand] = {"revision": info.sha, "dir": d, "files": {f: sha(os.path.join(d, f)) for f in sorted(os.listdir(d)) if os.path.isfile(os.path.join(d, f))}}
    except Exception as ex:
        out[cand] = {"error": type(ex).__name__ + ": " + str(ex)[:200]}
# official CBraMod code
g = os.path.join(ROOT, "github__wjq-learning__CBraMod")
if not os.path.isdir(g):
    subprocess.run(["git", "clone", "-q", "https://github.com/wjq-learning/CBraMod", g], check=True)
out["github:wjq-learning/CBraMod"] = {"dir": g, "head": subprocess.run(["git", "-C", g, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
                                       "files": sorted(os.listdir(os.path.join(g, "models"))) if os.path.isdir(os.path.join(g, "models")) else os.listdir(g)}
json.dump(out, open(os.path.join(ROOT, "FETCH_RECEIPT.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
