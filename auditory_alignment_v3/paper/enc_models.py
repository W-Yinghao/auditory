"""Paper line (manuscript v2 Tables 3-5, Appendix B.3-B.4): external EEG encoders behind the ALN4.1 time-bank token interface.

Both encoders receive exactly the ALN4.1 crops: aln41/timebank.crop_inputs (native crop [-200,200), [0,400), [200,600) ms ->
crop-only FFT resampling to 200 Hz = 80 real samples -> zero right padding to 200). Each crop is one independent forward.
The wrappers below only add what each released interface needs and return channel tokens [N, C, 1, E] (one "patch" row per
channel), so aln41/frozen.tokens, frozen.pca_fit and the SpatialPatchHead target heads apply unchanged.

REVE (HF brain-bzh/reve-base @ dc2a075, positions brain-bzh/reve-positions @ befa5b5), through
auditory_alignment_v2/foundation_adapter.Backbone('reve', ...) (amplitude clip(z, -15, 15) of the loader z-score, 200 Hz):
  patch_size 200, patch_overlap 20 -> eeg.unfold(size=200, step=180); an input shorter than 200 samples has no patch, so the
  80 real samples are right-padded to 200 (the timebank padding itself) = exactly one patch; tokens = final transformer
  outputs [N, C, 1, 512] (final_layer is Identity; the unused cls_query_token / attention_pooling are not part of the
  interface). Channel positions: private 20 channels = foundation_adapter names (T3/T4/T5/T6 -> T7/T8/P7/P8; the bank stores
  identical coordinates under both names); MFF = names E1..E128 of the bank (GSN HydroCel-129 template; the recorded MFF
  layout f2432571... is an exact similarity transform of these bank coordinates, verified in the plan step).
  Strict load: the adapter's from_pretrained state is compared tensor-by-tensor with model.safetensors (same key set, every
  tensor equal, numel equal).
MindMix aligned EEG branch (github CookieMikeLiu/MindMix @ 98445f36, released multimodal checkpoint best_model_loss_0.0909.pth,
sha256 fe2603e3...): the official EEGEncoder (labram_base_patch200_200 NeuralTransformer: TemporalConv patch embedding, 12
blocks x 200, 10 heads, time_embed [1,16,200], fc_norm), built by the official get_models with the README CLI arguments
(aln42/external_mindmix.README_ARGV; finetune '' so no other file is read) and strictly loaded with the checkpoint tensors
'eeg_model.*' (prefix removed). eeg_proj (the 200 -> 256 alignment projection before CALRA) is extracted and audited but is a
training head, like the proposed model's auditory projections, and is not part of the token interface. No Wav2Vec2 / audio /
CALRA tensor is loaded or used.
  Input: the 200-sample timebank crop (80 real) is right-padded to 400 = the released two-patch interface
  ('B N (A T) -> B N A T', A=2, T=200); amplitude = the loader z-score unchanged (MindMix's own preprocessing is a per-window
  z-score; a z-score over a 400-ms crop would remove the crop mean/scale that the other encoders see, so the shared per-record
  z-score is kept and the difference is recorded). Tokens = official forward(..., return_patch_tokens=True) = fc_norm of
  every patch token [N, C*2, 200] (index c*2 + a), arranged per channel as [patch0 | patch1] -> [N, C, 1, 400].
  Channels: pos_embed is forced to None in NeuralTransformer.__init__ and EEGEncoder.forward passes no input_chans
  (utils.get_input_chans is never called), so no spatial embedding exists: tokens are channel-permutation equivariant and any
  channel count works (20 private names are all in the official standard_1020 list; MFF E1..E128 use the same rule).
  The TemporalConv GroupNorm normalises over all tokens of an input, padding patch included (inherent to the padded
  interface). drop_path 0.1 (official default) is active only in train mode.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

ENC = {'REVE': {'E': 512, 'pad_to': 200, 'patches_per_crop': 1},
       'MINDMIX': {'E': 400, 'pad_to': 400, 'patches_per_crop': 2}}
ENCODERS = tuple(ENC)
MFF_CHANNELS = [f'E{i}' for i in range(1, 129)]
MFF_LAYOUT_HASH = 'f2432571f166a2fbb38282d732841dd396fc5583c91caa3eb205127bcdd04c1f'
COHORTS = ('private_bdf', 'mff')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def channel_names(cohort):
    from auditory_alignment_v2.foundation_adapter import ALIASES, CHANNELS
    if cohort == 'private_bdf':
        return [ALIASES.get(c, c) for c in CHANNELS['private_bdf']]
    assert cohort == 'mff', cohort
    return list(MFF_CHANNELS)


# ------------------------------------------------------------------------------------------------ assets
def reve_asset_hashes():
    from auditory_alignment_v2.foundation_adapter import FM_ROOT, REVE_DIR, REVE_POS
    receipt = json.loads((Path(FM_ROOT) / 'FETCH_RECEIPT.json').read_text())
    out = {}
    for key, d in (('brain-bzh/reve-base', REVE_DIR), ('brain-bzh/reve-positions', REVE_POS)):
        rec = receipt[key]
        for f, h in rec['files'].items():
            got = sha(Path(d) / f); assert got == h, (key, f)
        out[key] = {'revision': rec['revision'], 'files': rec['files']}
    return out


def reve_bank_positions(names):
    """[C, 3] positions of exactly these names from the REVE bank (the bank itself silently drops unknown names)."""
    import torch
    from transformers import AutoModel
    from auditory_alignment_v2.foundation_adapter import REVE_POS
    bank = AutoModel.from_pretrained(REVE_POS, trust_remote_code=True)
    missing = [n for n in names if n not in bank.mapping]
    assert not missing, missing
    with torch.no_grad():
        pos = bank(names)
    assert tuple(pos.shape) == (len(names), 3)
    return pos.float()


def mff_geometry_check(reader_evidence):
    """Recorded MFF layout (archived auditory5 reader evidence, head frame) vs REVE bank E1..E128: similarity Procrustes."""
    d = json.loads(Path(reader_evidence).read_text())
    g = next(r['metadata'] for r in d if r['metadata']['layout_hash'] == MFF_LAYOUT_HASH)
    names = [x['channel_name'] for x in g['geometry']]
    assert names == MFF_CHANNELS
    X = np.array([x['xyz_m'] for x in g['geometry']], dtype=np.float64)
    from auditory_alignment_v2.foundation_adapter import REVE_POS
    bank = json.loads((Path(REVE_POS) / 'positions.json').read_text()); Y = np.array([bank[n] for n in names], dtype=np.float64)
    mx, my = X.mean(0), Y.mean(0); Xc, Yc = X - mx, Y - my
    U, S, Vt = np.linalg.svd(Xc.T @ Yc); R = U @ Vt; s = S.sum() / (Xc ** 2).sum()
    res = np.linalg.norm(s * Xc @ R + my - Y, axis=1)
    allE = [f'E{i}' for i in range(1, 130)]; A = np.array([bank[n] for n in allE])
    nearest = [allE[int(np.argmin(np.linalg.norm(A - p, axis=1)))] for p in s * Xc @ R + my]
    return {'layout_hash': MFF_LAYOUT_HASH, 'excluded_reference': g['excluded_reference_channel_names'], 'scale': float(s),
            'rotation_det': float(np.linalg.det(R)), 'residual_max_m': float(res.max()), 'residual_median_m': float(np.median(res)),
            'nearest_bank_label_equals_name': int(sum(a == b for a, b in zip(nearest, names))),
            'raw_distance_median_m': float(np.median(np.linalg.norm(X - Y, axis=1)))}


def mindmix_official():
    from ..aln42 import external_mindmix as XM
    UEF, UM, UT = XM.official()
    import sys
    old = sys.argv; sys.argv = list(XM.README_ARGV)
    try:
        args = UEF.get_args()
    finally:
        sys.argv = old
    assert args.finetune == '' and args.model == 'labram_base_patch200_200' and args.input_size == 400
    return UEF, args


def mindmix_extract(dest):
    """CPU: EEG tensors of the released fusion checkpoint -> dest (torch file, 0400). Returns the audit."""
    import contextlib
    import io
    import torch
    from ..aln42 import external_mindmix as XM
    assert sha(XM.CKPT) == XM.CKPT_SHA
    ck = XM.safe_load(XM.CKPT)
    sd = ck['model_state_dict']
    eeg = {k[len('eeg_model.'):]: v.clone() for k, v in sd.items() if k.startswith('eeg_model.')}
    proj = {k[len('eeg_proj.'):]: v.clone() for k, v in sd.items() if k.startswith('eeg_proj.')}
    groups = {}
    for k in sd:
        groups[k.split('.')[0]] = groups.get(k.split('.')[0], 0) + 1
    UEF, args = mindmix_official()
    with contextlib.redirect_stdout(io.StringIO()):
        enc = UEF.EEGEncoder(args, 'cpu')
    res = enc.load_state_dict(eeg, strict=True)
    assert not res.missing_keys and not res.unexpected_keys
    msd = enc.state_dict()
    assert set(msd) == set(eeg) and all(torch.equal(msd[k], eeg[k]) for k in eeg)
    audit = {'checkpoint': str(XM.CKPT), 'checkpoint_sha256': XM.CKPT_SHA, 'checkpoint_epoch': ck.get('epoch'),
             'checkpoint_tensor_groups': groups, 'eeg_encoder_tensors': len(eeg), 'eeg_encoder_numel': int(sum(v.numel() for v in eeg.values())),
             'eeg_proj_tensors': len(proj), 'eeg_proj_numel': int(sum(v.numel() for v in proj.values())),
             'model_state_tensors': len(msd), 'model_state_numel': int(sum(v.numel() for v in msd.values())),
             'strict_load': True, 'pos_embed_is_none': enc.model.pos_embed is None,
             'time_embed_shape': list(enc.model.time_embed.shape), 'n_blocks': len(enc.model.blocks), 'embed_dim': enc.model.embed_dim,
             'excluded_groups': sorted(g for g in groups if g not in ('eeg_model', 'eeg_proj'))}
    assert audit['eeg_encoder_numel'] == audit['model_state_numel'] and audit['pos_embed_is_none']
    dest = Path(dest); dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if dest.exists():
        old = torch.load(dest, map_location='cpu', weights_only=True)
        assert set(old['eeg_encoder']) == set(eeg) and all(torch.equal(old['eeg_encoder'][k], eeg[k]) for k in eeg)
    else:
        tmp = dest.with_suffix('.tmp')
        torch.save({'eeg_encoder': eeg, 'eeg_proj': proj, 'source_checkpoint_sha256': XM.CKPT_SHA}, tmp)
        tmp.rename(dest); dest.chmod(0o400)
    del ck, sd
    return audit


# ------------------------------------------------------------------------------------------------ token wrappers
class ReveTokens(nn.Module):
    """[N, C, 200] (timebank crop, 200 Hz, 80 real + 120 zero) -> REVE tokens [N, C, 1, 512]."""

    def __init__(self, cohort):
        super().__init__()
        from auditory_alignment_v2.foundation_adapter import Backbone
        self.cohort, self.names = cohort, channel_names(cohort)
        self.bb = Backbone('reve', 'private_bdf', 'pretrained_full', 200)
        if cohort == 'mff':
            self.bb.pos = reve_bank_positions(self.names)      # registered buffer replaced; adapter file unchanged
            self.bb.channel_names = list(self.names)
        assert tuple(self.bb.pos.shape) == (len(self.names), 3), self.bb.pos.shape
        self.E = 512

    def audit(self):
        """Strict comparison with the released safetensors (call before any update)."""
        import torch
        from safetensors.torch import load_file
        from auditory_alignment_v2.foundation_adapter import REVE_DIR
        ref = load_file(str(Path(REVE_DIR) / 'model.safetensors'))
        got = self.bb.net.state_dict()
        assert set(ref) == set(got), (sorted(set(ref) ^ set(got))[:5])
        bad = [k for k in ref if not torch.equal(ref[k], got[k].cpu())]
        assert not bad, bad[:5]
        pos_ref = reve_bank_positions(self.names)
        return {'tensors': len(ref), 'numel': int(sum(v.numel() for v in ref.values())),
                'model_numel': int(sum(p.numel() for p in self.bb.net.parameters())), 'strict_equal': True,
                'positions_equal_bank': bool(torch.equal(pos_ref, self.bb.pos.cpu())), 'channels': len(self.names)}

    def forward(self, z):
        assert z.dim() == 3 and z.shape[1] == len(self.names) and z.shape[-1] == ENC['REVE']['pad_to'], tuple(z.shape)
        h = self.bb(z)
        assert h.shape[2] == 1 and h.shape[3] == self.E, tuple(h.shape)
        return h


class MindMixTokens(nn.Module):
    """[N, C, 200] (timebank crop) -> right pad to 400 -> official EEGEncoder patch tokens -> [N, C, 1, 400]."""

    def __init__(self, cohort, branch_path):
        super().__init__()
        import contextlib
        import io
        import torch
        self.cohort, self.names = cohort, channel_names(cohort)
        UEF, args = mindmix_official()
        with contextlib.redirect_stdout(io.StringIO()):
            self.enc = UEF.EEGEncoder(args, 'cpu')
        st = torch.load(branch_path, map_location='cpu', weights_only=True)
        res = self.enc.load_state_dict(st['eeg_encoder'], strict=True)
        assert not res.missing_keys and not res.unexpected_keys
        assert self.enc.model.pos_embed is None
        self.E = 400

    def audit(self, branch_path):
        import torch
        st = torch.load(branch_path, map_location='cpu', weights_only=True)['eeg_encoder']
        got = self.enc.state_dict()
        assert set(st) == set(got)
        bad = [k for k in st if not torch.equal(st[k], got[k].cpu())]
        assert not bad, bad[:5]
        return {'tensors': len(st), 'numel': int(sum(v.numel() for v in st.values())),
                'model_numel': int(sum(p.numel() for p in self.enc.parameters())), 'strict_equal': True,
                'pos_embed_is_none': self.enc.model.pos_embed is None, 'channels': len(self.names)}

    def forward(self, z):
        import torch.nn.functional as F
        from einops import rearrange
        N, C, T = z.shape
        assert C == len(self.names) and T == 200, tuple(z.shape)
        x = rearrange(F.pad(z, (0, ENC['MINDMIX']['pad_to'] - T)), 'B N (A T) -> B N A T', A=2, T=200)
        tok = self.enc.model(x, return_patch_tokens=True)                        # [N, C*2, 200], index c*2 + a
        assert tuple(tok.shape) == (N, C * 2, 200), tuple(tok.shape)
        return tok.reshape(N, C, 2 * 200).unsqueeze(2)


def make_tokens(encoder, cohort, branch_path=None):
    if encoder == 'REVE':
        return ReveTokens(cohort)
    assert encoder == 'MINDMIX' and branch_path is not None
    return MindMixTokens(cohort, branch_path)


def audit(model, encoder, branch_path=None):
    return model.audit() if encoder == 'REVE' else model.audit(branch_path)


# ------------------------------------------------------------------------------------------------ private CE model (FT)
def build_ft(encoder, a0, seed, dev, branch_path=None):
    """aln41/private_ft.build with the backbone replaced: same three slot heads (SpatialPatchHead(E, 20, d 32, K 8, e 32) +
    Linear(32, 2), seeded by `seed` inside fork_rng), same gate a, same crops (onset 50, timebank layout at 250 Hz)."""
    import torch
    import torch.nn as nn
    from auditory_alignment_v2.fm_readout import SpatialPatchHead
    from ..aln41 import private_ft as PF, timebank as TB
    E = ENC[encoder]['E']

    class Model(nn.Module):
        def __init__(self):
            super().__init__()
            self.bb = make_tokens(encoder, 'private_bdf', branch_path)
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(seed)
                self.slots = nn.ModuleList([SpatialPatchHead(E, 20, d=32, K=8, e=32) for _ in range(3)])
                self.cls = nn.ModuleList([nn.Linear(32, 2) for _ in range(3)])
            self.a = nn.Parameter(a0.clone().float())

        def slot_logits(self, x):
            B = x.shape[0]
            lay = TB.layout(250)
            crops = [x[..., PF.ONSET + a:PF.ONSET + b] for a, b, _ in lay]
            h = self.bb(TB.crop_inputs(crops, 250))                       # [3B, C, 1, E]
            h = h.reshape(3, B, *h.shape[1:])
            return torch.stack([self.cls[k](self.slots[k](h[k])[:, 0]) for k in range(3)], 1)   # [B, 3, 2]

        def log_probs(self, x, uniform=False):
            lk = torch.log_softmax(self.slot_logits(x), -1)
            lq = torch.log_softmax(torch.zeros_like(self.a) if uniform else self.a, 0)
            return torch.logsumexp(lq[None, :, None] + lk, 1), lk
    model = Model()
    for p in model.bb.parameters():
        p.requires_grad_(True)
    return model.to(dev)


def param_groups(model, weight_decay):
    """aln41/private_ft.param_groups with the candidate's weight decay (same no-decay rule)."""
    decay, no = [], []
    for n, p in model.named_parameters():
        (no if (p.ndim <= 1 or n.endswith('.bias') or n == 'a') else decay).append(p)
    return [{'params': decay, 'weight_decay': weight_decay}, {'params': no, 'weight_decay': 0.0}]
