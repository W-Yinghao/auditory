"""DEP12 shared encoder API, registry version 3 (extension 2, 2026-10-23): encoders_v2 (unchanged) + cs_pair_noise@{3401,3407,3413}.

cs_pair_noise (coordinator DECISIONS 2026-10-23 10:55; S20-S22): the cs_pair LoRA recipe trained against i.i.d. unit-Gaussian
32-d targets instead of the audio views (trainer_ext2 / source_fleet_ext2). encoders.py and encoders_v2.py are imported
unchanged (sha256-checked), every existing name loads through encoders_v2.load (identical objects), so U is bit-identical for
every name served by v1 / v2 / v3; meta['api_version'] stays 'dep12_encoders_v1'. The noise arm's encoders carry
meta['registry_module'] = 'encoders_v3'. Same API: REGISTRY, refresh(), servable(), describe(), load().
"""
from __future__ import annotations

from pathlib import Path

from . import encoders as _v1, encoders_v2 as _v2
from .encoders_v2 import (CBraModEncoder, EncoderNotReady, MindMixEncoder, NotServable, ReveEncoder,  # noqa: F401
                          montages, resolve_montage, tokens_to_U, selected_mode, run_receipt, sha, read,
                          TRANSFER_STEP, E0_STEP, SOURCE_OUT, SOURCE_STORE, E0_SELECTION)

V2_SHA256 = '6e4d3b5928826f0f27da2a9b026469c9f03a0ce0000fcab8edeaaeb9a55183c7'
EXT2 = {'cs_pair_noise': (3401, 3407, 3413)}
ACCESS_NOISE = ('source EEG only: SparrKULee fit listeners/anchors; training targets are i.i.d. unit-Gaussian 32-d vectors '
                '(no audio enters training); no target-cohort data')


def _check():
    _v2._check_v1()
    if sha(_v2.__file__) != V2_SHA256:
        raise RuntimeError('encoders_v2.py changed; encoders_v3 is bound to its pinned sha256')


def ext2_names():
    return [f'{o}@{s}' for o, seeds in EXT2.items() for s in seeds]


def build_registry():
    _check()
    R = _v2.build_registry()
    mode = selected_mode()
    for o, seeds in EXT2.items():
        for s in seeds:
            name = f'{o}@{s}'
            assert name not in R, name
            e = _v1._new_entry(name, o, s, mode, TRANSFER_STEP, 'new_round_production')
            e.update(data_access=ACCESS_NOISE, extension='ext2 (DECISIONS 2026-10-23 10:55; follow-up, beyond the package budget)',
                     registry_module='encoders_v3', training_targets='iid_unit_gaussian_noise_32d')
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
    import torch
    _check()
    if name not in ext2_names():
        return _v2.load(name, device, verify_sha)
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
    enc.meta.update(run=spec.get('run'), net_digest=st.get('net_digest'), mode=spec['training_mode'], registry_module='encoders_v3',
                    extension=spec.get('extension'), training_targets='iid_unit_gaussian_noise_32d')
    return enc


def describe():
    out = {}
    for k, v in refresh().items():
        out[k] = {f: v.get(f) for f in ('kind', 'arch', 'objective', 'seed', 'training_mode', 'step', 'checkpoint', 'sha256',
                                         'input_support_flag', 'data_access', 'servable', 'not_servable_reason', 'state', 'extension')}
    return out
