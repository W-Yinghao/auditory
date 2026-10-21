import argparse, sys, numpy as np, torch
torch.serialization.add_safe_globals([argparse.Namespace, np.dtype, (np._core.multiarray.scalar, 'numpy.core.multiarray.scalar')] + [getattr(np.dtypes, n) for n in dir(np.dtypes) if n.endswith('DType')])
ck = torch.load(sys.argv[1], map_location='cpu', weights_only=True)
for k, v in sorted(vars(ck['args']).items()):
    print(f'{k} = {v!r}')
