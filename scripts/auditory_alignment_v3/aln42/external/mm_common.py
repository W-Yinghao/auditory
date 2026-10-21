"""Shared helpers for the ALN4.2 R3 MindMix readiness check (no project code edited; official repo used unmodified).

build(fix_pos_conv): official args (README DTU CLI) -> official EEGEncoder + Wav2Vec2Model.from_pretrained('facebook/wav2vec2-base')
-> official universal_models.create_model('multimodal_real', calra) -> official load_pretrained_weights(fusion ckpt).
The only runtime substitution is the unpickler: universal_models.load_trusted_checkpoint is replaced by a
weights_only=True loader (the pickle references only argparse.Namespace / OrderedDict / FloatStorage / _rebuild_tensor_v2,
see inspect_fusion.log), which changes no key or value.
fix_pos_conv=True additionally copies the two wav2vec2 positional-conv weight-norm tensors that the official name-based
loader cannot match under torch>=2.1 parametrized weight_norm (weight_g -> parametrizations.weight.original0,
weight_v -> parametrizations.weight.original1): a pure key rename of identical tensors.
"""
import argparse, hashlib, io, os, sys, contextlib
import numpy as np
import torch

REPO = '/projects/EEG-foundation-model/auditory_public/foundation_models/github__CookieMikeLiu__MindMix@98445f3/repo'
CKPT = '/projects/EEG-foundation-model/auditory_public/foundation_models/github__CookieMikeLiu__MindMix@98445f3/lfs/best_model_loss_0.0909.pth'
CKPT_SHA = 'fe2603e3ee2c95fa2e1e012710a2774e70b6dd5582560773aafd20b295f15026'
README_ARGV = ['universal_eeg_finetune.py', '--dataset', 'DTU', '--data_path', '<DTU_trail>', '--strategy', 'multimodal_real',
               '--fusion_method', 'calra', '--pretrained_model', CKPT, '--batch_size', '32', '--epochs', '50']
POS_RENAME = {'audio_model.encoder.pos_conv_embed.conv.weight_g': 'audio_encoder.encoder.pos_conv_embed.conv.parametrizations.weight.original0',
              'audio_model.encoder.pos_conv_embed.conv.weight_v': 'audio_encoder.encoder.pos_conv_embed.conv.parametrizations.weight.original1'}

if REPO not in sys.path:
    sys.path.insert(0, REPO)


def safe_load(path, map_location='cpu'):
    torch.serialization.add_safe_globals([argparse.Namespace])
    return torch.load(path, map_location=map_location, weights_only=True)


def official_modules():
    import universal_eeg_finetune as UEF
    import universal_models as UM
    import universal_trainer as UT
    UM.load_trusted_checkpoint = safe_load
    return UEF, UM, UT


def official_args():
    UEF, _, _ = official_modules()
    old = sys.argv
    sys.argv = list(README_ARGV)
    try:
        args = UEF.get_args()
    finally:
        sys.argv = old
    return args


def official_map(k):
    """Exact replica of MultimodalRealModel.load_pretrained_weights key mapping (universal_models.py:471-488)."""
    if k.startswith('eeg_model.'):
        return k.replace('eeg_model.', 'eeg_encoder.')
    if k.startswith('audio_model.'):
        return k.replace('audio_model.', 'audio_encoder.')
    return k


def build(fix_pos_conv=True, quiet=True, seed=3401):
    from transformers import Wav2Vec2Model
    UEF, UM, UT = official_modules()
    torch.manual_seed(seed)
    args = official_args()
    dev = torch.device('cpu')
    buf = io.StringIO()
    with (contextlib.redirect_stdout(buf) if quiet else contextlib.nullcontext()):
        eeg = UEF.EEGEncoder(args, dev)
        audio = Wav2Vec2Model.from_pretrained('facebook/wav2vec2-base')
        model = UM.create_model(args.strategy, eeg, audio, args.fusion_method, num_classes=2, use_auditory_type=args.use_auditory_type)
        model.load_pretrained_weights(args.pretrained_model)
    log = buf.getvalue()
    if fix_pos_conv:
        sd = safe_load(args.pretrained_model)['model_state_dict']
        msd = model.state_dict()
        upd = {}
        for src, dst in POS_RENAME.items():
            assert dst in msd and msd[dst].shape == sd[src].shape, (dst, src)
            upd[dst] = sd[src]
        msd.update(upd)
        model.load_state_dict(msd)
    return model, args, log


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()
