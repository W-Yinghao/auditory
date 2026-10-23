"""DEP12 shared encoder API, registry version 4 (extension 3, 2026-10-23): encoders_v3 (unchanged) + ssl_continue@{3401,3407,3413}.

ssl_continue (coordinator DECISIONS 2026-10-23 11:55; S23-S25): the cs_pair LoRA recipe with the audio-free CBraMod-style
masked-patch reconstruction objective (trainer_ext3 / source_fleet_ext3). encoders.py, encoders_v2.py and encoders_v3.py are
imported unchanged (sha256-checked); every existing name loads through encoders_v3.load (identical objects), so U is
bit-identical for every name served by v1 / v2 / v3 / v4; meta['api_version'] stays 'dep12_encoders_v1'. The ssl arm's
encoders carry meta['registry_module'] = 'encoders_v4'. Same API: REGISTRY, refresh(), servable(), describe(), load().
"""
from __future__ import annotations

from pathlib import Path

from . import encoders as _v1, encoders_v3 as _v3
from .encoders_v3 import (CBraModEncoder, EncoderNotReady, MindMixEncoder, NotServable, ReveEncoder,  # noqa: F401
                          montages, resolve_montage, tokens_to_U, selected_mode, run_receipt, sha, read,
                          TRANSFER_STEP, E0_STEP, SOURCE_OUT, SOURCE_STORE, E0_SELECTION)

V3_SHA256 = 'cc50ee4f95aaccd6bc88e88ec4156df7c9f0378c29385253f27128ac4bcd489e'
EXT3 = {'ssl_continue': (3401, 3407, 3413)}
ACCESS_SSL = ('source EEG only: SparrKULee fit listeners/anchors; audio-free masked-patch reconstruction (no audio enters '
              'training); no target-cohort data')


def _check():
    _v3._check()
    if sha(_v3.__file__) != V3_SHA256:
        raise RuntimeError('encoders_v3.py changed; encoders_v4 is bound to its pinned sha256')


def ext3_names():
    return [f'{o}@{s}' for o, seeds in EXT3.items() for s in seeds]


def build_registry():
    _check()
    R = _v3.build_registry()
    mode = selected_mode()
    for o, seeds in EXT3.items():
        for s in seeds:
            name = f'{o}@{s}'
            assert name not in R, name
            e = _v1._new_entry(name, o, s, mode, TRANSFER_STEP, 'new_round_production')
            e.update(data_access=ACCESS_SSL, extension='ext3 (DECISIONS 2026-10-23 11:55; follow-up, beyond the package budget)',
                     registry_module='encoders_v4', training_targets='none (masked-patch reconstruction of the EEG input)')
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
    if name not in ext3_names():
        return _v3.load(name, device, verify_sha)
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
    enc.meta.update(run=spec.get('run'), net_digest=st.get('net_digest'), mode=spec['training_mode'], registry_module='encoders_v4',
                    extension=spec.get('extension'), training_targets='none (masked-patch reconstruction of the EEG input)')
    return enc


def describe():
    out = {}
    for k, v in refresh().items():
        out[k] = {f: v.get(f) for f in ('kind', 'arch', 'objective', 'seed', 'training_mode', 'step', 'checkpoint', 'sha256',
                                         'input_support_flag', 'data_access', 'servable', 'not_servable_reason', 'state', 'extension')}
    return out
