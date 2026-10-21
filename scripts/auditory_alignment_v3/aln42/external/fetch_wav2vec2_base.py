"""Fetch facebook/wav2vec2-base (needed by the official code: Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base"))
into the project's public HF cache at the current main revision, and record revision + per-file SHA256."""
import hashlib, json, os, sys, time
from huggingface_hub import HfApi, snapshot_download

cache, receipt = sys.argv[1], sys.argv[2]
api = HfApi()
info = api.model_info("facebook/wav2vec2-base", files_metadata=True)
rev = info.sha
files = [s.rfilename for s in info.siblings]
print('revision', rev, 'files', files, flush=True)
allow = [f for f in files if f in ('config.json', 'preprocessor_config.json', 'pytorch_model.bin', 'model.safetensors')]
d = snapshot_download("facebook/wav2vec2-base", revision=rev, cache_dir=cache, allow_patterns=allow)
out = {'repo': 'facebook/wav2vec2-base', 'revision': rev, 'cache_dir': cache, 'snapshot': d, 'files': {},
       'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'remote_files': files}
for f in allow:
    p = os.path.join(d, f)
    h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    out['files'][f] = {'sha256': h, 'bytes': os.path.getsize(p)}
json.dump(out, open(receipt, 'w'), indent=1)
print(json.dumps(out, indent=1))
