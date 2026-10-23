"""DEP12 shared encoder API, registry version 2 (extension 1, 2026-10-23): encoders.py (v1) plus four registry names.

Adds raw_cs@3407, raw_cs@3413, cs_pair_wrong@3407, cs_pair_wrong@3413 (the extension-1 mechanism controls, coordinator
decision DECISIONS.md 2026-10-23 07:30; trained by source_fleet_ext1 with the unchanged trainer_v2). Everything else is
imported from encoders.py, which is NOT edited (Agents M and P pin its sha256): the representation code, the encoder
classes, the montage guard and the loaders of all v1 names are the same objects, so U is identical for every name served
by both modules. meta['api_version'] stays 'dep12_encoders_v1' (the representation API did not change); extension
encoders additionally carry meta['registry_module'] = 'encoders_v2'.

Same API: REGISTRY, refresh(), servable(), describe(), load(name, device) -> .represent(x, channel_names, pad_mask) / .meta
/ .project (diagnostics only).
"""
from __future__ import annotations

from pathlib import Path

from . import encoders as _v1
from .encoders import (CBraModEncoder, EncoderNotReady, MindMixEncoder, NotServable, ReveEncoder,  # noqa: F401
                       montages, resolve_montage, tokens_to_U, selected_mode, run_receipt, sha, read,
                       TRANSFER_STEP, E0_STEP, SOURCE_OUT, SOURCE_STORE, E0_SELECTION)

V1_SHA256 = '0201f97504d15b92abb161900deb826ec10667baac69afa6e0fbb72459cf26f1'
EXTENSION = {'raw_cs': (3407, 3413), 'cs_pair_wrong': (3407, 3413)}
NEW_SEEDS = {k: tuple(sorted(set(v) | set(EXTENSION.get(k, ())))) for k, v in _v1.NEW_SEEDS.items()}


def _check_v1():
    if sha(_v1.__file__) != V1_SHA256:
        raise RuntimeError('encoders.py (v1) changed; encoders_v2 is bound to its pinned sha256')


def extension_names():
    return [f'{o}@{s}' for o, seeds in EXTENSION.items() for s in seeds]


def build_registry():
    _check_v1()
    R = _v1.build_registry()
    mode = selected_mode()
    for o, seeds in EXTENSION.items():
        for s in seeds:
            name = f'{o}@{s}'
            assert name not in R, name
            e = _v1._new_entry(name, o, s, mode, TRANSFER_STEP, 'new_round_production')
            e.update(extension='ext1 (DECISIONS 2026-10-23 07:30; beyond the package budget)', registry_module='encoders_v2')
            R[name] = e
    return R


REGISTRY = build_registry()


def refresh():
    global REGISTRY
    REGISTRY = build_registry()
    return REGISTRY


def servable():
    return sorted(k for k, v in REGISTRY.items() if v.get('servable'))


def load(name, device='cpu', verify_sha=True):
    """v1 names: encoders.load (identical object path). Extension names: the v1 new-round production loader branch."""
    import torch
    _check_v1()
    if name not in extension_names():
        return _v1.load(name, device, verify_sha)
    spec = REGISTRY.get(name)
    if spec is None or spec.get('state') != 'available':
        spec = refresh().get(name)
    if spec.get('state') != 'available':
        raise EncoderNotReady(f"{name}: state {spec.get('state')}")
    ck = spec['checkpoint']
    if verify_sha and spec.get('sha256') and Path(ck).is_file() and sha(ck) != spec['sha256']:
        raise RuntimeError(f'{name}: checkpoint sha256 mismatch ({ck})')
    st = torch.load(ck, map_location='cpu', weights_only=True)
    enc = CBraModEncoder(spec, device, net_state=st['net'], heads=st.get('heads'))
    enc.meta.update(run=spec.get('run'), net_digest=st.get('net_digest'), mode=spec['training_mode'], registry_module='encoders_v2',
                    extension=spec.get('extension'))
    return enc


def describe():
    out = {}
    for k, v in refresh().items():
        out[k] = {f: v.get(f) for f in ('kind', 'arch', 'objective', 'seed', 'training_mode', 'step', 'checkpoint', 'sha256',
                                         'input_support_flag', 'data_access', 'servable', 'not_servable_reason', 'state', 'extension')}
    return out
