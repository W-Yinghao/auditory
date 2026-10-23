"""DEP12 shared encoder API (package v1.2, 03 §1): one independent EEG representation per encoder for every measurement / use.

    from auditory_alignment_v3.dep12 import encoders as ENC
    enc = ENC.load('B0', 'cuda')                      # or 'cs_pair@3401', 'aln41_TCS@3407', 'MINDMIX_branch', ...
    U = enc.represent(x, channel_names, pad_mask)     # x [N, C, 200] float32, 1 s container at 200 Hz -> U [N, D] (L2 rows)
    enc.meta                                          # layer, token layout, checkpoint sha256, mode, input support, access

Input contract (the caller owns cropping, per 03 §1): x is ONE 1 s container at 200 Hz that already holds the native crop
resampled to 200 Hz (source: 64 Hz q+[-26:38] -> 200 points; private: real 0.8 s -> 160 points + 40 leading zeros) in the
cohort's established z-score units. Every encoder applies its own released amplitude convention exactly once inside
(CBraMod 0.15*z, REVE clip(z, -15, 15), MindMix z unchanged). pad_mask [N, 200] bool (True = padding) is validated (padded
samples must be exactly 0) and recorded; none of these backbones has a sample-level mask, so it does not change the forward.
channel_names must be one of the registered montages in the cohort loader's order (CBraMod has no channel-name embedding;
its positional convolution reads the channel INDEX order, so a wrong order would silently change the representation).

Representation (identical rule for every servable encoder; never conditioned on candidate audio): the frozen backbone's
predetermined layer = final encoder output tokens [N, C, P, E] (CBraMod: transformer layer 12 of 12, proj_out removed, P=1,
E=200; REVE: final transformer output, P=1, E=512; MindMix branch: official fc_norm patch tokens, P=2 (real | right pad),
E=200) -> parameter-free LayerNorm over E per token -> flatten in channel-major (channel, patch, feature) order -> L2
normalise. D = C*P*E depends on the montage. project() exposes the training-only 32-d heads of new-round arms (source
montage only) for diagnostics; it is never the common measurement.

REGISTRY: name -> spec dict (kind, arch, checkpoint, sha256, training_mode, step, input_support, input_support_flag,
data_access, servable, not_servable_reason, state). New-round arms resolve their checkpoint from the DEP12 source run
receipts (trainer.py); before they exist their state is 'planned' and load() raises EncoderNotReady.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .source_common import (REPO, OUT, STORE, SOURCE_OUT, SOURCE_STORE, RESULTS, E0_SELECTION, LN_EPS,  # noqa: F401
                            tokens_to_U, run_name)

TARGET_HZ, CONTAINER = 200, 200
from .source_common import CBRAMOD_SHA256  # noqa: E402
CBRAMOD_HF_REVISION = '500543c7e30bda1b22bfd51a49301b238dee21fd'
CBRAMOD_CODE_HEAD = 'b9e961003214326972c567eff390e75b0287e32a'
MINDMIX_BRANCH = Path('<private checkpoint storage>/auditory_alignment_v3/paper/encoders_v1/assets/mindmix_eeg_branch.pt')
MINDMIX_BRANCH_SHA256 = 'b9fa2cfd6d5bbe011eb5aae5c7021223617be332d8bf9f5b0bed50c95df8646d'
MINDMIX_RELEASE_SHA256 = 'fe2603e3ee2c95fa2e1e012710a2774e70b6dd5582560773aafd20b295f15026'
NEW_OBJECTIVES = ('cs_pair', 'info_nce', 'sigmoid', 'raw_cs', 'cs_pair_wrong')
NEW_SEEDS = {'cs_pair': (3401, 3407, 3413), 'info_nce': (3401, 3407, 3413), 'sigmoid': (3401, 3407, 3413),
             'raw_cs': (3401,), 'cs_pair_wrong': (3401,)}
E0_RUNS = tuple((o, m) for o in ('cs_pair', 'info_nce') for m in ('full', 'lora'))
TRANSFER_STEP, E0_STEP = 10000, 2500

# ALN4.1 production source checkpoints at the fixed transfer update 10000 (selection.json + unit receipts, verified 2026-10-23)
_A41 = '<private checkpoint storage>/auditory_alignment_v3/aln41'
ALN41 = {
    ('TCS', 3401): ('ALN41P_b1cdce0e9d5561f1', f'{_A41}/source_v1/units/ALN41P_b1cdce0e9d5561f1/update10000.pt', 'e1fb6f52b4b640172bb15f107a2eb4a3863b2560b385a5c2c74df6c219b3c075'),
    ('TNCE', 3401): ('ALN41P_994006360035af4a', f'{_A41}/source_v1/units/ALN41P_994006360035af4a/update10000.pt', '0a239c4d4c43484c6923f1a3d8402439b8408a8802e2e7cfc310fe193d90cda8'),
    ('GCS', 3401): ('ALN41P_9eb9c2473b62d72d', f'{_A41}/source_v1/units/ALN41P_9eb9c2473b62d72d/update10000.pt', '92d368a0af8420bf7612bbf707ab60f917754150469d9e15a6d1160d8c0b8e6c'),
    ('TCS_WRONG', 3401): ('ALN41P_774cf1d1feb57784', f'{_A41}/source_v1/units/ALN41P_774cf1d1feb57784/update10000.pt', 'de64a27e1b7fa1ecec95ce8e77bc7b17baacf43b89bdf5a09b9cc7d2239538e0'),
    ('TCS', 3407): ('ALN41P_ea14e9690cd9c8a8', f'{_A41}/r2/seed3407/source_v1/units/ALN41P_ea14e9690cd9c8a8/update10000.pt', '82faa3cb701f6be8e7b9ab2778b40f8808465fd9818fe3c954ba913a0f64a78a'),
    ('TNCE', 3407): ('ALN41P_bd32ffb95947b01c', f'{_A41}/r2/seed3407/source_v1/units/ALN41P_bd32ffb95947b01c/update10000.pt', '377fd4745aea2d63cb4324312cca7efb286e86e391e1733eb77eeeb9f5875e34'),
    ('GCS', 3407): ('ALN41P_d037f9f020c9489c', f'{_A41}/r2/seed3407/source_v1/units/ALN41P_d037f9f020c9489c/update10000.pt', 'ffe94667a9030a067b7b3337a779338adc0ab809950c7a6c567b373a593e0962'),
    ('TCS_WRONG', 3407): ('ALN41P_fa11e96fcb06c47d', f'{_A41}/r2/seed3407/source_v1/units/ALN41P_fa11e96fcb06c47d/update10000.pt', 'f037cf1cf239feae6a715cc01ff2a5d04f1735ccf3c24d4ec94bc22b182c4436'),
    ('TCS', 3413): ('ALN41P_bbb726fb7c57db07', f'{_A41}/r2/seed3413/source_v1/units/ALN41P_bbb726fb7c57db07/update10000.pt', 'c4582c7d97bb95ff62806f9d6d17608a391933cfaf3bf541fbe41669be3e2176'),
    ('TNCE', 3413): ('ALN41P_42b2140f961313e6', f'{_A41}/r2/seed3413/source_v1/units/ALN41P_42b2140f961313e6/update10000.pt', '3f07db3eafe13198cac62869e37c1a59443843a214a0d1d16b6602762b3f8013'),
    ('GCS', 3413): ('ALN41P_1d4df450779d63bb', f'{_A41}/r2/seed3413/source_v1/units/ALN41P_1d4df450779d63bb/update10000.pt', 'a942ec378d4cd747eb9fdd4b09a155161b2a1235bbb10708e02c23b3f4f5d8b7'),
    ('TCS_WRONG', 3413): ('ALN41P_587ad626b6b42479', f'{_A41}/r2/seed3413/source_v1/units/ALN41P_587ad626b6b42479/update10000.pt', '48cb1b0ee1adfe587094b0c375222c5a3745459059aeb0184a1dd12a5f065cff'),
}
ALN41_NAME = {'TCS': 'TCS', 'TNCE': 'TNCE', 'GCS': 'GCS', 'TCS_WRONG': 'WRONG'}
ALN34_PLAN = REPO / 'private' / 'auditory_alignment_v3' / 'aln34' / 'content_time_v1' / 'plan.json'
ALN34_PLAN_SHA256 = None  # recorded at first use (the plan file is 0444); see aln34_entries()
ALN34_LABEL = {('cbramod', 'pretrained_full'): 'aln34_cb_full', ('cbramod', 'random_full'): 'aln34_cb_random',
               ('reve', 'pretrained_full'): 'aln34_reve_full', ('lag_local_tokens', None): 'aln34_local'}

SOURCE_SUPPORT = ('1 s container: SparrKULee 64 Hz native crop q+[-26:38] (64 samples, half-open [-406.25, +593.75) ms) -> '
                  'aln41.timebank.resample (scipy-equivalent FFT) -> 200 samples, no padding')
ACCESS_GENERIC = 'generic_pretraining_only (no auditory pairing, no target-cohort data)'
ACCESS_SOURCE = 'source_paired_audio: SparrKULee fit listeners/contents (env/ss/sc views); no target-cohort data'


class EncoderNotReady(RuntimeError):
    pass


class NotServable(RuntimeError):
    pass


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


# ------------------------------------------------------------------------------------------------ montages
def montages():
    """Registered channel orders (cohort loader order, legacy aliases T3/T4/T5/T6 -> T7/T8/P7/P8 resolved)."""
    from auditory_alignment_v2.foundation_adapter import ALIASES, CHANNELS
    from ..prior33 import contract as PC
    out = {k: tuple(ALIASES.get(c, c) for c in v) for k, v in CHANNELS.items()}
    assert out['dtu'] == tuple(PC.BIOSEMI64), 'DTU loader order must equal the SparrKULee BioSemi-64 order'
    out['sparrkulee'] = tuple(PC.BIOSEMI64)
    out['mff'] = tuple(f'E{i}' for i in range(1, 129))
    return out


def resolve_montage(channel_names):
    from auditory_alignment_v2.foundation_adapter import ALIASES
    names = tuple(ALIASES.get(str(c).strip(), str(c).strip()) for c in channel_names)
    for key, order in montages().items():
        if names == order:
            return ('sparrkulee' if key == 'dtu' else key), names
    raise ValueError(f'channel_names ({len(names)} channels, first {names[:4]}) match no registered montage order '
                     f'{sorted(montages())}; reorder to the cohort loader order')


# ------------------------------------------------------------------------------------------------ registry
_new_run_dir = run_name


def selected_mode():
    if not E0_SELECTION.exists():
        return None
    return read(E0_SELECTION).get('selected_mode')


def run_receipt(objective, mode, seed):
    p = SOURCE_OUT / 'runs' / _new_run_dir(objective, mode, seed) / 'receipt.json'
    return read(p) if p.exists() else None


def _new_entry(name, objective, seed, mode, step, kind):
    e = {'name': name, 'kind': kind, 'arch': 'cbramod', 'objective': objective, 'seed': seed, 'training_mode': mode, 'step': step,
         'input_support': SOURCE_SUPPORT, 'input_support_flag': 'same_as_new_round',
         'data_access': ACCESS_SOURCE, 'servable': True, 'not_servable_reason': None, 'checkpoint': None, 'sha256': None,
         'state': 'planned', 'init': 'B0 (CBraMod pretrained_weights.pth sha256 ' + CBRAMOD_SHA256[:16] + '...)'}
    if mode is None:
        e['state'] = 'planned_mode_unselected'
        return e
    rec = run_receipt(objective, mode, seed)
    ck = (rec or {}).get('checkpoints', {}).get(str(step))
    if ck:
        e.update(checkpoint=ck['serve_path'], sha256=ck['serve_sha256'], state='available', run=_new_run_dir(objective, mode, seed))
    else:
        e['checkpoint'] = str(SOURCE_STORE / 'runs' / _new_run_dir(objective, mode, seed) / f'step{step}.serve.pt')
    return e


def aln34_entries():
    """ALN3.4 content_time frozen-model assets (ALN32 per-cohort fits: local_aligned1000 / true-full CB / REVE)."""
    out = {}
    if not ALN34_PLAN.exists():
        return out
    plan = read(ALN34_PLAN)
    for u in plan['rows']:
        s = u['source']; sp = s['spec']
        arch = sp['architecture']; ad = sp.get('adaptation') if arch != 'lag_local_tokens' else None
        label = ALN34_LABEL[(arch, ad)]
        name = f"{label}@{s['dataset']}.s{s['seed']}.sf{s['subject_fold']}.cf{s['content_fold']}"
        ck = REPO / 'private' / 'auditory_alignment_v3' / 'ckpt' / f"{s['experiment_id']}_best.pt"
        e = {'name': name, 'kind': 'reused_aln34', 'arch': 'cbramod' if arch == 'cbramod' else arch, 'objective': sp.get('objective'),
             'seed': s['seed'], 'training_mode': (sp.get('recipe') or sp.get('variant')), 'step': 'best (ALN32 selection)',
             'checkpoint': str(ck), 'sha256': u['checkpoint_sha256'], 'dataset': s['dataset'],
             'subject_fold': s['subject_fold'], 'content_fold': s['content_fold'], 'experiment_id': s['experiment_id'],
             'aln34_unit': u['id'],
             'data_access': (f"target_cohort_training_people_paired_audio ({s['dataset']} subject_fold {s['subject_fold']}, "
                             f"content_fold {s['content_fold']}; NCE; this fold's held-out people/contents only are unseen)"),
             'state': 'available' if ck.exists() else 'missing_checkpoint'}
        if arch == 'lag_local_tokens':
            e.update(servable=False, input_support_flag='not_applicable',
                     input_support=f"native {s['dataset']} lag-local token model (local_aligned1000), cohort-rate input",
                     not_servable_reason=('local lag-token model with its own native-rate input contract and no transformer '
                                          'token layer; the 1 s 200 Hz container is not its input and cannot be inverted to '
                                          'the native samples for all cohorts (private 250 Hz). Use its archived ALN3.4 '
                                          'content_time feature arrays instead.'))
        else:
            e.update(servable=True, not_servable_reason=None, input_support_flag='same_1s_span_different_resampler_and_data_access',
                     input_support=(f"aligned window [-0.4, +0.6) s at the {s['dataset']} native rate, resampled by "
                                    "foundation_adapter.resample_fft (no scipy Nyquist-bin halving) to 200; served here on the "
                                    "DEP12 container (scipy-equivalent resampling)"))
        out[name] = e
    return out


def build_registry():
    R = {}
    R['B0'] = {'name': 'B0', 'kind': 'stage1_zero_update', 'arch': 'cbramod', 'objective': None, 'seed': None,
               'training_mode': 'none (zero updates)', 'step': 0,
               'checkpoint': None, 'weights': None, 'sha256': CBRAMOD_SHA256, 'hf_revision': CBRAMOD_HF_REVISION,
               'code_head': CBRAMOD_CODE_HEAD, 'input_support': SOURCE_SUPPORT + ' (any registered montage; private: 0.8 s real + 0.2 s front zeros)',
               'input_support_flag': 'same_as_new_round', 'data_access': ACCESS_GENERIC, 'servable': True,
               'not_servable_reason': None, 'state': 'available',
               'note': 'the step-0 backbone of every new DEP12 arm (trainer verifies tensor equality at step 0)'}
    try:
        from auditory_alignment_v2.foundation_adapter import CBRAMOD_W
        R['B0']['weights'] = R['B0']['checkpoint'] = CBRAMOD_W
    except Exception:  # pragma: no cover - adapter import failure is reported by load()
        pass
    mode = selected_mode()
    for obj in ('cs_pair', 'info_nce', 'sigmoid', 'raw_cs', 'cs_pair_wrong'):
        for seed in NEW_SEEDS[obj]:
            R[f'{obj}@{seed}'] = _new_entry(f'{obj}@{seed}', obj, seed, mode, TRANSFER_STEP, 'new_round_production')
    for obj, m in E0_RUNS:
        R[f'E0.{obj}.{m}@3401'] = _new_entry(f'E0.{obj}.{m}@3401', obj, 3401, m, E0_STEP, 'new_round_e0_pilot')
    for (arm, seed), (uid, path, digest) in ALN41.items():
        name = f'aln41_{ALN41_NAME[arm]}@{seed}'
        R[name] = {'name': name, 'kind': 'reused_aln41', 'arch': 'cbramod', 'objective': arm, 'seed': seed,
                   'training_mode': 'full (ALN4.1 recipe: lr 1e-4, clip 5, gate a, first-order support delta)', 'step': 10000,
                   'checkpoint': path, 'sha256': digest, 'aln41_unit': uid,
                   'input_support': ('trained on three 400 ms crops W0/W1/W2 per anchor (64 Hz native -> 80 real + 120 zero samples '
                                     'per 200-sample patch); served here on the DEP12 1 s container (different input support)'),
                   'input_support_flag': 'different_input_support', 'data_access': ACCESS_SOURCE.replace('(env/ss/sc views)', '(env/ss/sc; S32/Q32 episodes)'),
                   'servable': True, 'not_servable_reason': None, 'state': 'available' if Path(path).exists() else 'missing_checkpoint'}
    R.update(aln34_entries())
    R['REVE0'] = {'name': 'REVE0', 'kind': 'generic_reference', 'arch': 'reve', 'objective': None, 'seed': None,
                  'training_mode': 'none (zero updates)', 'step': 0, 'checkpoint': 'brain-bzh/reve-base@dc2a075', 'sha256': None,
                  'input_support': '1 s container, one 200-sample REVE patch (overlap rule yields exactly 1 patch)',
                  'input_support_flag': 'same_container_different_backbone', 'data_access': ACCESS_GENERIC,
                  'servable': True, 'not_servable_reason': None, 'state': 'available'}
    R['MINDMIX_branch'] = {'name': 'MINDMIX_branch', 'kind': 'external_branch', 'arch': 'mindmix_labram_base', 'objective': None,
                           'seed': None, 'training_mode': 'released (no DEP12 update)', 'step': None,
                           'checkpoint': str(MINDMIX_BRANCH), 'sha256': MINDMIX_BRANCH_SHA256,
                           'release_checkpoint_sha256': MINDMIX_RELEASE_SHA256,
                           'input_support': ('1 s container right-padded to the released 400-sample two-patch interface (patch 1 '
                                             'all zero); amplitude = loader z-score unchanged (MindMix per-window z-score not applied)'),
                           'input_support_flag': 'different_interface_padding_and_amplitude',
                           'data_access': ('external MindMix multimodal release (official training data; overlap with DTU/FAU '
                                           'not excluded by us); EEG branch only, no audio/CALRA tensor used'),
                           'servable': True, 'not_servable_reason': None,
                           'state': 'available' if MINDMIX_BRANCH.exists() else 'missing_checkpoint'}
    R['MINDMIX_full_fusion'] = {'name': 'MINDMIX_full_fusion', 'kind': 'external_system', 'arch': 'mindmix_fusion', 'servable': False,
                                'not_servable_reason': ('the full fusion system conditions on candidate audio (CALRA); it is a '
                                                        'system score, not an independent EEG representation (03 §1, §6)'),
                                'checkpoint': None, 'sha256': MINDMIX_RELEASE_SHA256, 'state': 'not_servable',
                                'input_support': None, 'input_support_flag': 'not_applicable', 'data_access': 'external release'}
    R['MINDMIX_stage1_eeg_only'] = {'name': 'MINDMIX_stage1_eeg_only', 'kind': 'external_asset', 'arch': 'labram_large_variant',
                                    'servable': False,
                                    'not_servable_reason': ('ALN4.1 STAGE1_GATE not_passed: architecture/position-table gaps and '
                                                            'unrecoverable channel->position mapping (v2.4_large.pth)'),
                                    'checkpoint': None, 'sha256': '707dfabf98e7c471fe7096722f97ac9aa06c3df1c86383b095cfc71f667455a0',
                                    'state': 'not_servable', 'input_support': None, 'input_support_flag': 'not_applicable',
                                    'data_access': 'external release'}
    return R


REGISTRY = build_registry()


def refresh():
    """Rebuild REGISTRY (new-round checkpoints appear as runs complete; E0 selection fixes the production mode)."""
    global REGISTRY
    REGISTRY = build_registry()
    return REGISTRY


def servable():
    return sorted(k for k, v in REGISTRY.items() if v.get('servable'))


# ------------------------------------------------------------------------------------------------ representation
def _as_input(x, device):
    import numpy as np
    import torch
    if isinstance(x, np.ndarray):
        x = torch.from_numpy(np.ascontiguousarray(x))
    x = x.to(device=device, dtype=torch.float32)
    if x.dim() != 3 or x.shape[-1] != CONTAINER:
        raise ValueError(f'x must be [N, C, {CONTAINER}] (one 1 s container at 200 Hz), got {tuple(x.shape)}')
    if not bool(torch.isfinite(x).all()):
        raise ValueError('x contains NaN/Inf')
    return x


def _check_pad(x, pad_mask):
    import numpy as np
    import torch
    if pad_mask is None:
        return {'padding': 'none_declared'}
    m = torch.as_tensor(np.asarray(pad_mask) if not isinstance(pad_mask, torch.Tensor) else pad_mask, device=x.device).bool()
    if m.dim() == 1:
        m = m[None].expand(x.shape[0], -1)
    if tuple(m.shape) != (x.shape[0], CONTAINER):
        raise ValueError(f'pad_mask must be [N, {CONTAINER}] or [{CONTAINER}], got {tuple(m.shape)}')
    if bool((x.abs().amax(1) * m).any()):
        raise ValueError('padded samples (pad_mask True) must be exactly zero in every channel')
    return {'padding': 'validated_zero', 'pad_samples_per_row': sorted(set(m.sum(1).tolist()))[:8]}


class _Base:
    chunk = 512

    def __init__(self, spec, device):
        import torch
        self.spec, self.device = dict(spec), torch.device(device)
        self.meta = {'name': spec['name'], 'kind': spec['kind'], 'arch': spec['arch'], 'checkpoint': spec.get('checkpoint'),
                     'checkpoint_sha256': spec.get('sha256'), 'mode': spec.get('training_mode'), 'step': spec.get('step'),
                     'objective': spec.get('objective'), 'seed': spec.get('seed'), 'input_support': spec.get('input_support'),
                     'input_support_flag': spec.get('input_support_flag'), 'data_access': spec.get('data_access'),
                     'representation': 'final-layer tokens -> parameter-free LayerNorm(E) per token -> channel-major flatten -> L2',
                     'ln_eps': LN_EPS, 'container': '[N, C, 200] at 200 Hz', 'api_version': 'dep12_encoders_v1'}

    def token_shape(self, n_channels):
        return (n_channels, self.P, self.E)

    def _tokens(self, x, montage):
        raise NotImplementedError

    def represent(self, x, channel_names, pad_mask=None):
        import torch
        montage, names = resolve_montage(channel_names)
        x = _as_input(x, self.device)
        if x.shape[1] != len(names):
            raise ValueError(f'x has {x.shape[1]} channels, channel_names {len(names)}')
        self.last_call = {'montage': montage, 'n_channels': len(names), **_check_pad(x, pad_mask),
                          'token_shape': list(self.token_shape(len(names))), 'D': int(len(names) * self.P * self.E)}
        out = []
        with torch.no_grad():
            for a in range(0, len(x), self.chunk):
                h = self._tokens(x[a:a + self.chunk], montage)
                assert tuple(h.shape[1:]) == self.token_shape(len(names)), (tuple(h.shape), self.token_shape(len(names)))
                out.append(tokens_to_U(h))
        return torch.cat(out) if out else torch.zeros(0, len(names) * self.P * self.E, device=self.device)

    def project(self, x, channel_names, pad_mask=None, view='env'):
        raise NotServable(f"{self.spec['name']}: no DEP12 training projector (diagnostics only exist for new-round arms)")


class CBraModEncoder(_Base):
    """foundation_adapter.Backbone('cbramod', ..., fs_native=200): identity resampling, 0.15*z inside, proj_out = Identity."""
    E, P = 200, 1

    def __init__(self, spec, device, net_state=None, heads=None):
        import torch
        from auditory_alignment_v2.foundation_adapter import Backbone
        super().__init__(spec, device)
        self.bb = Backbone('cbramod', 'dtu', 'pretrained_full', TARGET_HZ, init_state=net_state)
        self.bb.requires_grad_(False)
        self.bb.to(self.device).eval()
        self.heads = None
        if heads is not None:
            from ..fm_aligned import AlignedPatchLinear
            n_ch = heads['env.lin.weight'].shape[1] // self.E if 'env.lin.weight' in heads else None
            self.heads = torch.nn.ModuleDict({v: AlignedPatchLinear(n_ch, self.E, 32) for v in ('env', 'ss', 'sc')})
            self.heads.load_state_dict(heads, strict=True)
            self.heads.requires_grad_(False)
            self.heads.to(self.device).eval()
        self.meta.update(layer='CBraMod encoder.layers[11] output (final of 12; proj_out removed)', token_E=self.E, patches=self.P,
                         amplitude='0.15*z inside the adapter', init_state_loaded=self.bb.init_loaded)

    def _tokens(self, x, montage):
        h = self.bb(x)
        assert h.shape[2] == 1, tuple(h.shape)
        return h

    def project(self, x, channel_names, pad_mask=None, view='env'):
        """Diagnostics only: the trained 32-d training head of `view` (source BioSemi-64 montage only)."""
        import torch
        if self.heads is None:
            return super().project(x, channel_names, pad_mask, view)
        montage, names = resolve_montage(channel_names)
        if montage != 'sparrkulee':
            raise NotServable('training heads are channel-specific flatten heads of the source montage (03 §1)')
        x = _as_input(x, self.device); _check_pad(x, pad_mask)
        with torch.no_grad():
            return torch.cat([self.heads[view](self._tokens(x[a:a + self.chunk], montage)[:, :, 0])
                              for a in range(0, len(x), self.chunk)])


class ReveEncoder(_Base):
    """foundation_adapter.Backbone('reve', ...): clip(z, -15, 15), positions from the official bank by channel name."""
    E, P = 512, 1

    def __init__(self, spec, device, net_state=None):
        import torch
        from auditory_alignment_v2.foundation_adapter import Backbone
        super().__init__(spec, device)
        self.bb = Backbone('reve', 'private_bdf', 'pretrained_full', TARGET_HZ)
        if net_state is not None:
            res = self.bb.net.load_state_dict(net_state, strict=True)
            assert not res.missing_keys and not res.unexpected_keys
        self.bb.requires_grad_(False)
        self.bb.to(self.device).eval()
        self._pos = {}
        self.meta.update(layer='REVE final transformer output (final_layer Identity; cls/attention pooling unused)', token_E=self.E,
                         patches=self.P, amplitude='clip(z, -15, 15) inside the adapter', positions='reve-positions bank by name')

    def _positions(self, montage):
        if montage not in self._pos:
            from ..paper import enc_models as EM
            self._pos[montage] = EM.reve_bank_positions(list(montages()['dtu' if montage == 'sparrkulee' else montage])).to(self.device)
        return self._pos[montage]

    def _tokens(self, x, montage):
        self.bb.pos = self._positions(montage)
        h = self.bb(x)
        assert h.shape[2] == 1, tuple(h.shape)
        return h


class MindMixEncoder(_Base):
    """Official MindMix EEGEncoder (labram_base_patch200_200, pos_embed None) strictly loaded from the extracted branch asset."""
    E, P = 200, 2

    def __init__(self, spec, device):
        import contextlib
        import io
        import torch
        from ..paper import enc_models as EM
        super().__init__(spec, device)
        if sha(MINDMIX_BRANCH) != MINDMIX_BRANCH_SHA256:
            raise RuntimeError('MindMix branch asset hash changed')
        UEF, args = EM.mindmix_official()
        with contextlib.redirect_stdout(io.StringIO()):
            self.enc = UEF.EEGEncoder(args, 'cpu')
        st = torch.load(MINDMIX_BRANCH, map_location='cpu', weights_only=True)
        res = self.enc.load_state_dict(st['eeg_encoder'], strict=True)
        assert not res.missing_keys and not res.unexpected_keys and self.enc.model.pos_embed is None
        self.enc.requires_grad_(False)
        self.enc.to(self.device).eval()
        self.meta.update(layer='official forward(return_patch_tokens=True) = fc_norm of every patch token', token_E=self.E,
                         patches=self.P, amplitude='loader z-score unchanged',
                         interface='container right-padded to 400 = released two-patch input (patch 1 is padding)')

    def _tokens(self, x, montage):
        import torch.nn.functional as F
        N, C, T = x.shape
        z = F.pad(x, (0, 2 * 200 - T)).reshape(N, C, 2, 200)
        tok = self.enc.model(z, return_patch_tokens=True)          # [N, C*2, 200], index c*2 + a
        assert tuple(tok.shape) == (N, C * 2, 200), tuple(tok.shape)
        return tok.reshape(N, C, 2, 200)


# ------------------------------------------------------------------------------------------------ load
def _strip(state, prefix):
    out = {k[len(prefix):]: v for k, v in state.items() if k.startswith(prefix)}
    assert out, f'no tensors with prefix {prefix!r}'
    return out


def load(name, device='cpu', verify_sha=True):
    """Encoder object with .represent(x, channel_names, pad_mask) -> U [N, D] (on `device`), .meta, .project (diagnostics)."""
    import torch
    spec = REGISTRY.get(name) or refresh().get(name)
    if spec is None:
        raise KeyError(f'unknown encoder {name!r}')
    if not spec.get('servable'):
        raise NotServable(f"{name}: {spec.get('not_servable_reason')}")
    if spec.get('state') != 'available':
        spec = refresh().get(name)
        if spec.get('state') != 'available':
            raise EncoderNotReady(f"{name}: state {spec.get('state')}")
    ck = spec.get('checkpoint')
    if verify_sha and spec.get('sha256') and ck and Path(ck).is_file() and sha(ck) != spec['sha256']:
        raise RuntimeError(f'{name}: checkpoint sha256 mismatch ({ck})')
    if name == 'B0':
        return CBraModEncoder(spec, device)
    if spec['kind'] in ('new_round_production', 'new_round_e0_pilot'):
        st = torch.load(ck, map_location='cpu', weights_only=True)
        enc = CBraModEncoder(spec, device, net_state=st['net'], heads=st.get('heads'))
        enc.meta.update(run=spec.get('run'), net_digest=st.get('net_digest'), mode=spec['training_mode'])
        return enc
    if spec['kind'] == 'reused_aln41':
        st = torch.load(ck, map_location='cpu', weights_only=False)
        return CBraModEncoder(spec, device, net_state=_strip(st['backbone'], 'net.'))
    if spec['kind'] == 'reused_aln34':
        st = torch.load(ck, map_location='cpu', weights_only=False)['model']
        if spec['arch'] == 'cbramod':
            return CBraModEncoder(spec, device, net_state=_strip(st, 'bb.net.'))
        return ReveEncoder(spec, device, net_state=_strip(st, 'bb.net.'))
    if name == 'REVE0':
        return ReveEncoder(spec, device)
    if name == 'MINDMIX_branch':
        return MindMixEncoder(spec, device)
    raise NotServable(f'{name}: no loader')


def describe():
    """JSON-serialisable registry summary (for receipts / INTERFACES.md)."""
    out = {}
    for k, v in refresh().items():
        out[k] = {f: v.get(f) for f in ('kind', 'arch', 'objective', 'seed', 'training_mode', 'step', 'checkpoint', 'sha256',
                                         'input_support_flag', 'data_access', 'servable', 'not_servable_reason', 'state')}
    return out


if __name__ == '__main__':
    import sys
    d = describe()
    from collections import Counter
    print(json.dumps(Counter((v['kind'], v['servable'], v['state']) for v in d.values()).most_common(), default=str))
    if len(sys.argv) > 1:
        print(json.dumps(d.get(sys.argv[1]), indent=1))
