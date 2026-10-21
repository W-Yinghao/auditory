"""Gate 2 step 1: inspect the released fusion checkpoint without arbitrary unpickling.

1) list every GLOBAL referenced by the pickle (zip member data.pkl) via pickletools (no execution);
2) torch.load(weights_only=True) with an allowlist limited to what step 1 shows is needed (argparse.Namespace, numpy scalars);
3) print top-level structure, prefix counts, shapes and parameter totals; write a JSON summary.
"""
import argparse, collections, io, json, pickletools, sys, zipfile
import numpy as np
import torch

path, out = sys.argv[1], sys.argv[2]
zf = zipfile.ZipFile(path)
pk = [n for n in zf.namelist() if n.endswith('data.pkl')]
assert len(pk) == 1, pk
raw = zf.read(pk[0])
globs = set()
ops = list(pickletools.genops(io.BytesIO(raw)))
strs = []
for op, arg, pos in ops:
    if op.name in ('GLOBAL',):
        globs.add(arg.replace(' ', '.'))
    if op.name in ('SHORT_BINUNICODE', 'BINUNICODE', 'UNICODE'):
        strs.append(arg)
    if op.name == 'STACK_GLOBAL':
        globs.add('STACK_GLOBAL:' + '.'.join(strs[-2:]))
print('pickle globals:', sorted(globs))

safe = [argparse.Namespace, np.dtype, (np._core.multiarray.scalar, 'numpy.core.multiarray.scalar')] + \
       [getattr(np.dtypes, n) for n in dir(np.dtypes) if n.endswith('DType')]
torch.serialization.add_safe_globals(safe)
ck = torch.load(path, map_location='cpu', weights_only=True)
print('top keys', list(ck.keys()) if isinstance(ck, dict) else type(ck))
summary = {'pickle_globals': sorted(globs), 'top_keys': list(ck.keys()) if isinstance(ck, dict) else str(type(ck)), 'meta': {}}
for k, v in ck.items():
    if isinstance(v, dict):
        print(k, 'dict', len(v))
        summary['meta'][k] = f'dict[{len(v)}]'
    elif torch.is_tensor(v):
        summary['meta'][k] = list(v.shape)
    else:
        s = repr(v)
        print(k, type(v).__name__, s[:3000])
        summary['meta'][k] = s[:6000]
sd = ck['model_state_dict'] if 'model_state_dict' in ck else ck.get('model', ck)
pref = collections.Counter()
numel = collections.Counter()
for k, v in sd.items():
    p = '.'.join(k.split('.')[:2]) if k.startswith(('eeg_model', 'audio_model')) else k.split('.')[0]
    pref[p] += 1; numel[p] += v.numel()
print('prefixes', dict(pref)); print('numel', dict(numel))
summary['prefix_counts'] = dict(pref); summary['prefix_numel'] = dict(numel)
summary['n_tensors'] = len(sd); summary['numel'] = int(sum(v.numel() for v in sd.values()))
summary['dtypes'] = dict(collections.Counter(str(v.dtype) for v in sd.values()))
summary['keys'] = {k: list(v.shape) for k, v in sd.items()}
for k, v in sd.items():
    if 'audio_model' in k and 'layers.' in k and 'layers.0.' not in k:
        continue
    if 'eeg_model' in k and 'blocks.' in k and 'blocks.0.' not in k:
        continue
    print(k, tuple(v.shape), v.dtype)
if 'optimizer_state_dict' in ck:
    o = ck['optimizer_state_dict']
    summary['optimizer_param_groups'] = [{kk: vv for kk, vv in g.items() if kk != 'params'} | {'n_params': len(g['params'])} for g in o['param_groups']]
    print('optimizer groups', summary['optimizer_param_groups'])
json.dump(summary, open(out, 'w'), indent=1, default=str)
