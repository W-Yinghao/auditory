"""Stage1 gate step 1: inspect the MindMix EEG-only checkpoint with weights_only loading (no arbitrary unpickling)."""
import argparse, collections, json, sys, torch
path = sys.argv[1]
import numpy as np
safe = [argparse.Namespace, np.dtype, (np._core.multiarray.scalar, 'numpy.core.multiarray.scalar')] + [getattr(np.dtypes, n) for n in dir(np.dtypes) if n.endswith('DType')]
torch.serialization.add_safe_globals(safe)
try:
    ck = torch.load(path, map_location='cpu', weights_only=True)
    mode = 'weights_only'
except Exception as exc:
    print('weights_only failed:', repr(exc)[:400]); raise
print('top keys', list(ck.keys()) if isinstance(ck, dict) else type(ck))
for k, v in ck.items():
    if not isinstance(v, dict):
        print(k, type(v).__name__, (str(v)[:1500] if not torch.is_tensor(v) else tuple(v.shape)))
sd = ck.get('model', ck)
groups = collections.Counter(k.split('.')[0] for k in sd)
print('prefix counts', dict(groups))
for k, v in sd.items():
    if '.blocks.' in k and not ('.blocks.0.' in k or '.blocks.23.' in k):
        continue
    print(k, tuple(v.shape))
print('n_tensors', len(sd), 'numel', sum(v.numel() for v in sd.values()))
