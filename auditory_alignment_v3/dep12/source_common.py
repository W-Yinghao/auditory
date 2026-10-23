"""DEP12 source-side shared constants and the single representation rule (imported by encoders, trainer, devprobe).

Kept separate from encoders.py so that registry additions there cannot change the code the training fleet byte-checks.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / 'private' / 'auditory_alignment_v3' / 'dep12'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/dep12')
SOURCE_OUT = OUT / 'source'
SOURCE_STORE = STORE / 'source'
RESULTS = REPO / 'results' / 'auditory_alignment_v3' / 'dep12'
E0_SELECTION = RESULTS / 'E0_SELECTION.json'
CBRAMOD_SHA256 = '0792cb808c14e6b7a2bb2ce1dff379bc47bc54c49a779825bdfeb33bf8157178'
LN_EPS = 1e-5


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dumps(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False, default=str)


def write(path, value, freeze=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists() and freeze:
        raise FileExistsError(f'{path} is frozen')
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=1, sort_keys=True, allow_nan=False, default=str) + '\n')
    os.replace(tmp, path)
    if freeze:
        path.chmod(0o444)
    return path


def now():
    return datetime.now(timezone.utc).isoformat()


def run_name(objective, mode, seed):
    return f'{objective}.{mode}.s{seed}'


def tokens_to_U(h):
    """h [N, C, P, E] final-layer tokens -> U [N, C*P*E]: parameter-free LayerNorm per token, channel-major flatten, L2."""
    import torch.nn.functional as F
    assert h.dim() == 4, tuple(h.shape)
    z = F.layer_norm(h.float(), (h.shape[-1],), eps=LN_EPS)
    return F.normalize(z.reshape(len(z), -1), dim=1)


def net_digest(state):
    """sha256 over sorted keys, dtypes, shapes and float32 bytes of a plain CBraMod state dict."""
    import torch
    h = hashlib.sha256()
    for k in sorted(state):
        v = state[k].detach().to('cpu')
        h.update(k.encode()); h.update(str(tuple(v.shape)).encode())
        h.update((v.float() if v.is_floating_point() else v).contiguous().numpy().tobytes())
    return h.hexdigest()


def b0_net_state():
    """The Stage1 CBraMod tensors as the backbone holds them (proj_out replaced by Identity, so its two tensors are dropped)."""
    import torch
    from auditory_alignment_v2.foundation_adapter import CBRAMOD_W
    assert sha(CBRAMOD_W) == CBRAMOD_SHA256, 'Stage1 CBraMod weights changed'
    sd = torch.load(CBRAMOD_W, map_location='cpu', weights_only=True)
    return {k: v for k, v in sd.items() if not k.startswith('proj_out.')}
