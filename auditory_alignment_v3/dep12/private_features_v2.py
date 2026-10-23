"""DEP12 Agent P, private features v2 (DECISIONS P23): private_features (v1, unchanged) with the encoder resolved through
dep12/encoders_v2.py, which serves the v1 names through encoders.load (same objects) and adds the extension-1 mechanism
controls raw_cs@3407/3413 and cs_pair_wrong@3407/3413.

`export` calls the v1 export function itself; only its two encoder lookups (load_encoder, encoder_spec) are bound to v2 for
the duration of the call. Resampling, standardisation, padding, representation, PCA and storage are the v1 code, so U for
any name served by both registries is the same computation. The meta additionally records the encoders_v2 sha256.
"""
from __future__ import annotations

import contextlib
from pathlib import Path

from . import private_features as V1
from .private_features import (Binding, FOLDS, REC, RESULTS, ROOT, STORE, PACKAGE, BINDING, SUPPORT_SEEDS, digest, read,  # noqa: F401
                               sha, write, write_frozen, load_fold, pad_mask, channel_names, container, fold_stats, resample_real)


def load_encoder(name, device):
    from . import encoders_v2 as E
    return E.load(name, device)


def encoder_spec(name):
    from . import encoders_v2 as E
    return E.REGISTRY.get(name) or E.refresh().get(name)


def sources():
    files = [Path(__file__), Path(V1.__file__), ROOT / 'auditory_alignment_v3/dep12/encoders.py',
             ROOT / 'auditory_alignment_v3/dep12/encoders_v2.py']
    return {**V1.sources(), **{str(p.relative_to(ROOT)): sha(p) for p in files}}


@contextlib.contextmanager
def _v2_lookups():
    saved = (V1.load_encoder, V1.encoder_spec)
    V1.load_encoder, V1.encoder_spec = load_encoder, encoder_spec
    try:
        yield
    finally:
        V1.load_encoder, V1.encoder_spec = saved


def export(name, dest, **kw):
    from . import encoders_v2 as E
    with _v2_lookups():
        meta = V1.export(name, dest, **kw)
    meta.update(encoders_v2_py_sha256=sha(E.__file__), export_module='private_features_v2 (v1 export, encoders_v2 lookups)',
                sources_v2=sources())
    write(Path(dest) / 'meta.json', meta)
    return meta
