"""Gate 1: fetch the MindMix fusion checkpoint via the Git LFS batch API (HTTPS), verify full-file SHA256 == LFS oid.

Writes only <lfs_dir>/best_model_loss_0.0909.pth (+ a .part during download) and a JSON receipt.
The repo working tree (pointer file) is not modified.
"""
import hashlib, json, os, sys, time, urllib.request

REPO = "https://github.com/CookieMikeLiu/MindMix.git"
OID = "fe2603e3ee2c95fa2e1e012710a2774e70b6dd5582560773aafd20b295f15026"
SIZE = 1221696491
COMMIT = "98445f368efcb161c638172501bd16f92d09a89d"
REPO_PATH = "pretrain_fusion_checkpoints/best_model_loss_0.0909.pth"

lfs_dir, receipt_path = sys.argv[1], sys.argv[2]
dst = os.path.join(lfs_dir, "best_model_loss_0.0909.pth")
part = dst + ".part"

# confirm the pointer in the pinned checkout
pointer = open(os.path.join(os.path.dirname(lfs_dir), "repo", REPO_PATH)).read()
assert f"oid sha256:{OID}" in pointer and f"size {SIZE}" in pointer, pointer

req = urllib.request.Request(
    REPO + "/info/lfs/objects/batch",
    data=json.dumps({"operation": "download", "transfers": ["basic"],
                     "ref": {"name": "refs/heads/main"},
                     "objects": [{"oid": OID, "size": SIZE}]}).encode(),
    headers={"Accept": "application/vnd.git-lfs+json", "Content-Type": "application/vnd.git-lfs+json"})
batch = json.load(urllib.request.urlopen(req, timeout=60))
obj = batch["objects"][0]
assert obj["oid"] == OID and "actions" in obj, obj
href = obj["actions"]["download"]["href"]
hdrs = obj["actions"]["download"].get("header", {})
print("batch ok; download host", href.split("/")[2], flush=True)

t0 = time.time()
h = hashlib.sha256()
n = 0
with urllib.request.urlopen(urllib.request.Request(href, headers=hdrs), timeout=120) as r, open(part, "wb") as f:
    while True:
        b = r.read(1 << 22)
        if not b:
            break
        f.write(b); h.update(b); n += len(b)
        if n % (1 << 28) < (1 << 22):
            print(f"{n/1e9:.2f} GB {time.time()-t0:.0f}s", flush=True)
dig = h.hexdigest()
print("bytes", n, "sha256", dig, flush=True)
assert n == SIZE, (n, SIZE)
assert dig == OID, dig
os.replace(part, dst)
# independent re-hash of the final file
h2 = hashlib.sha256()
with open(dst, "rb") as f:
    for b in iter(lambda: f.read(1 << 22), b""):
        h2.update(b)
rec = {"repo": REPO, "commit": COMMIT, "repo_path": REPO_PATH, "lfs_oid": OID, "lfs_size": SIZE,
       "local_path": dst, "bytes": os.path.getsize(dst), "sha256_stream": dig, "sha256_reread": h2.hexdigest(),
       "matches_lfs_oid": h2.hexdigest() == OID and os.path.getsize(dst) == SIZE,
       "download_host": href.split("/")[2], "seconds": round(time.time() - t0, 1),
       "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
json.dump(rec, open(receipt_path, "w"), indent=1)
print(json.dumps(rec, indent=1))
