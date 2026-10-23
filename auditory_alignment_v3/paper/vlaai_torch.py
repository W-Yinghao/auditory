"""VLAAI (Accou et al. 2023, Sci Rep; github.com/exporl/vlaai @ 9af13054) as a PyTorch module with the released weights.

Architecture = the pinned model.py / the released vlaai.h5 model_config (read, not executed): input [B, T, 64]
  x = 0; 4 x { x = extractor(eeg + x); x = Dense_i(128 -> 64)(x); x = output_context(x) }; out = Dense(64 -> 1)(x)
  extractor (shared over blocks): 5 x [Conv1D(k=8, valid) -> LayerNorm(eps 1e-3, channel axis) -> LeakyReLU(0.3) ->
           ZeroPadding1D((0, 7))], filters 256, 256, 256, 128, 128
  output_context (shared): ZeroPadding1D((31, 0)) -> Conv1D(64, k=32) -> LayerNorm(eps 1e-3) -> LeakyReLU(0.3)
Weights: converted from pretrained_models/vlaai.h5 (h5py; Conv1D kernel [k, in, out] -> [out, in, k]; Dense [in, out] -> [out, in]).
Numerical equivalence with the original TensorFlow model on a fixed input, layer by layer: vlaai_tf_reference.py (EEG env,
TF 2.4.1) writes the reference; `verify` compares and writes private/auditory_alignment_v3/paper/external_decoders/
vlaai_conversion/VERIFY.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path('/projects/EEG-foundation-model/auditory_public/foundation_models/github__exporl__vlaai@9af1305/repo')
COMMIT = '9af13054bf73188e9c248f249f44ecc0cd02f6c5'
H5 = REPO / 'pretrained_models' / 'vlaai.h5'
FILTERS, KERNEL, CTX_KERNEL, NB_BLOCKS = (256, 256, 256, 128, 128), 8, 32, 4
EPS, SLOPE = 1e-3, 0.3


def build(input_channels=64):
    import torch
    from torch import nn
    import torch.nn.functional as F

    class Extractor(nn.Module):
        def __init__(self):
            super().__init__()
            ins = (input_channels,) + FILTERS[:-1]
            self.convs = nn.ModuleList([nn.Conv1d(i, o, KERNEL) for i, o in zip(ins, FILTERS)])
            self.norms = nn.ModuleList([nn.LayerNorm(o, eps=EPS) for o in FILTERS])

        def forward(self, x, taps=None):                       # x [B, T, C]
            for conv, norm in zip(self.convs, self.norms):
                x = conv(x.transpose(1, 2)).transpose(1, 2)
                x = F.leaky_relu(norm(x), SLOPE)
                x = F.pad(x, (0, 0, 0, KERNEL - 1))
                if taps is not None:
                    taps.append(x)
            return x

    class OutputContext(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = nn.Conv1d(64, 64, CTX_KERNEL); self.norm = nn.LayerNorm(64, eps=EPS)

        def forward(self, x):
            x = F.pad(x, (0, 0, CTX_KERNEL - 1, 0))
            x = self.conv(x.transpose(1, 2)).transpose(1, 2)
            return F.leaky_relu(self.norm(x), SLOPE)

    class VLAAI(nn.Module):
        def __init__(self):
            super().__init__()
            self.extractor = Extractor(); self.output_context = OutputContext()
            self.dense = nn.ModuleList([nn.Linear(FILTERS[-1], 64) for _ in range(NB_BLOCKS)])
            self.final = nn.Linear(64, 1)

        def forward(self, eeg, taps=None):                      # eeg [B, T, 64] -> [B, T, 1]
            x = torch.zeros_like(eeg)
            for i in range(NB_BLOCKS):
                x = self.extractor(eeg + x, None)
                if taps is not None:
                    taps.append(('extractor', i, x))
                x = self.dense[i](x)
                if taps is not None:
                    taps.append(('dense', i, x))
                x = self.output_context(x)
                if taps is not None:
                    taps.append(('output_context', i, x))
            return self.final(x)
    return VLAAI()


def h5_weights(path=H5):
    import h5py
    out = {}
    with h5py.File(path, 'r') as f:
        def visit(name, obj):
            if isinstance(obj, h5py.Dataset):
                out[name] = np.array(obj[()])
        f['model_weights'].visititems(visit)
    return out


def converted_state(path=H5):
    import torch
    W = h5_weights(path); sd = {}
    t = lambda a: torch.from_numpy(np.ascontiguousarray(a))
    for i in range(5):
        sd[f'extractor.convs.{i}.weight'] = t(W[f'functional_9/conv1d_{10 + i}/kernel:0'].transpose(2, 1, 0))
        sd[f'extractor.convs.{i}.bias'] = t(W[f'functional_9/conv1d_{10 + i}/bias:0'])
        sd[f'extractor.norms.{i}.weight'] = t(W[f'functional_9/layer_normalization_{10 + i}/gamma:0'])
        sd[f'extractor.norms.{i}.bias'] = t(W[f'functional_9/layer_normalization_{10 + i}/beta:0'])
    sd['output_context.conv.weight'] = t(W['functional_7/conv1d_9/kernel:0'].transpose(2, 1, 0))
    sd['output_context.conv.bias'] = t(W['functional_7/conv1d_9/bias:0'])
    sd['output_context.norm.weight'] = t(W['functional_7/layer_normalization_9/gamma:0'])
    sd['output_context.norm.bias'] = t(W['functional_7/layer_normalization_9/beta:0'])
    names = ['dense', 'dense_1', 'dense_2', 'dense_3']
    for i, n in enumerate(names):
        sd[f'dense.{i}.weight'] = t(W[f'{n}/{n}/kernel:0'].T); sd[f'dense.{i}.bias'] = t(W[f'{n}/{n}/bias:0'])
    sd['final.weight'] = t(W['dense_4/dense_4/kernel:0'].T); sd['final.bias'] = t(W['dense_4/dense_4/bias:0'])
    used = {k for k in W if k.split('/')[0] in ('functional_9', 'functional_7', *names, 'dense_4')}
    assert used == set(W), sorted(set(W) - used)
    return sd


def pretrained():
    model = build(64)
    missing = model.load_state_dict(converted_state(), strict=True)
    return model


def verify(reference_npz, out_json):
    """Compare the port with the TF reference (same fixed input): final output and every block's tap."""
    import torch
    from .. import core
    from ..aln41 import source as SRC
    ref = dict(np.load(reference_npz))
    model = pretrained().double().eval()
    x = torch.from_numpy(ref['input'].astype(np.float64))
    taps = []
    with torch.no_grad():
        y = model(x, taps).numpy()
    res = {'final': float(np.abs(y - ref['output']).max()), 'final_ref_absmax': float(np.abs(ref['output']).max())}
    for kind, i, v in taps:
        key = f'{kind}_{i}'
        if key in ref:
            res[key] = float(np.abs(v.numpy() - ref[key]).max())
    # float32 path as used in training
    m32 = pretrained().float().eval()
    with torch.no_grad():
        y32 = m32(torch.from_numpy(ref['input'].astype(np.float32))).numpy()
    res['final_float32'] = float(np.abs(y32 - ref['output']).max())
    rec = {'max_abs_diff': res, 'pass': bool(max(v for k, v in res.items() if k != 'final_ref_absmax') < 1e-3 * max(1.0, res['final_ref_absmax'])),
           'n_taps_compared': sum(1 for k in res if k.startswith(('extractor', 'dense', 'output_context'))),
           'h5_sha256': SRC.sha(H5), 'commit': COMMIT, 'reference_sha256': SRC.sha(Path(reference_npz)),
           'reference_meta': json.loads(str(ref['meta'])) if 'meta' in ref else None, 'port_source_sha256': SRC.sha(Path(__file__))}
    Path(out_json).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    SRC.write(Path(out_json), rec)
    return rec
