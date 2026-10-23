"""DEP12 source trainer ext3 = trainer_v2 + the audio-free ssl_continue arm (coordinator DECISIONS 2026-10-23 11:55; S23-S25).

ssl_continue: same model / LoRA mode / stream anchors and 1 s windows / two 64-anchor listener episodes / optimiser /
schedule / checkpoints / dev probe / diagnostics as cs_pair; objective = CBraMod pre-training masked-patch reconstruction:
Bernoulli(0.5) channel-patch mask (PCG64(SeedSequence([seed, SSL_TAG, u]))), masked tokens -> the model's mask_encoding,
reconstruction by the Stage1 pre-trained proj_out head (Linear 200->200, strictly loaded, trainable), MSE on masked tokens
of the scaled input (0.15*z), per listener episode, two listeners averaged. No audio is used. All other objectives behave
exactly as trainer_v2.

trainer_v2 header follows.

v2 (2026-10-23, after the V100 smoke 1058746 failed on an exact-zero assertion; v1 never trained): identical model, data,
objectives, optimiser and schedule. Changes: TF32 disabled for matmul and cuDNN (cross-GPU consistency with the V100-frozen
seed sigma; V100 has no TF32), per-unit CUDA peak-memory reset, the seed-sigma recheck tolerance is 1e-4 relative with the
observed difference recorded, the structurally inert single-key temporal-attention Q (and K) path is checked by a
relative gradient bound (INERT_REL_TOL) instead of exact zero and its magnitudes are recorded, and bank_end lets the smoke
measure the production memory peak.


Model: the Stage1 CBraMod (foundation_adapter.Backbone('cbramod', 'dtu', 'pretrained_full', fs_native=200): strict load of
pretrained_weights.pth sha256 0792cb80..., proj_out removed, 0.15*z inside) + one training head per view
(LayerNorm(E) per channel token -> ordered flatten C*E -> Linear(12800 -> 32) -> L2; fm_aligned.AlignedPatchLinear). Heads
are built in a forked RNG seeded by the training seed, so they are identical across objectives and modes of one seed.
  full : every backbone tensor trainable from update 1 (full_onestep_v1; no progressive unfreezing, no LLRD).
  lora : backbone frozen; rank-8, alpha-16, dropout-0 adapters on the Q and V row blocks of in_proj_weight of both
         criss-cross attentions (self_attn_s, self_attn_t) of all 12 layers (48 adapters, registered mapping); heads trainable.
Input: SourceData.eeg = exact CBAUD q+[-26:38] native crop -> scipy-equivalent resampling to 200 points.
Objective per update: two listener episodes (stream, shared by every arm of the seed) x three views (env/ss/sc, weight 1/3);
listeners averaged (1/2); objectives.episode_loss (package reference byte copy). CS sigmas: grouped within-listener lower
median on the source-fit panel at the seed's initial state (eval mode), per view, written once (0444) and reused by every
CS arm of the seed.
Optimiser: AdamW lr 3e-4 for backbone/LoRA and heads, weight decay 1e-4 on every trainable tensor, linear warmup over the
first 500 updates then cosine to 0 at update 10,000 (fixed for every unit, also E0's 2,500-update pilots), global clip 1.
Checkpoints 0/500/2500/5000/10000: serve file (plain merged CBraMod state + heads) and state file (model, optimiser,
scheduler, torch/CUDA RNG, step, logs); rolling resume.pt every 100 updates (preemption). E0 diagnostics every 500 updates
and the dev probe (devprobe.py) at every checkpoint.
CLI (Slurm only): python -m auditory_alignment_v3.dep12.trainer run --objective O --mode M --seed S --end E [--probe-dir D]
"""
from __future__ import annotations

import argparse
import contextlib
import gc
import math
import os
from pathlib import Path
import time
import traceback

import numpy as np

from . import objectives as OBJ, source_common as SC, source_sampler as SS

LR, WD, WARMUP, TOTAL, CLIP = 3e-4, 1e-4, 500, 10000, 1.0
CHECKPOINTS = (0, 500, 2500, 5000, 10000)
DIAG_EVERY, RESUME_EVERY, LOG_EVERY = 500, 100, 25
LORA_RANK, LORA_ALPHA, LORA_DROPOUT = 8, 16, 0.0
HEAD_SEED, LORA_SEED, TRAIN_SEED = 77, 78, 79       # offsets added to the training seed
VIEWS = SS.VIEWS
MODES = ('full', 'lora')
UNUSED_WITHOUT_MASK = ('patch_embedding.mask_encoding',)
# One 1 s patch per channel: the temporal attention has a single key (softmax == 1), so its Q/K projections cannot affect the
# output; the LoRA Q adapter of every self_attn_t receives exactly zero gradient (full mode: zero Q/K rows of its in_proj).
INERT_SINGLE_PATCH = ('self_attn_t.parametrizations.in_proj_weight.0.A_q', 'self_attn_t.parametrizations.in_proj_weight.0.B_q')
# GPU attention kernels leave float32 rounding residue in the (mathematically zero) single-key softmax gradient. A live path
# has a gradient ratio of order 1e-2..1 (self_attn_s Q vs V is recorded as the live reference); 1e-3 separates the two.
INERT_REL_TOL = 1e-3
SIGMA_RECHECK_REL_TOL = 1e-4
SSL_OBJECTIVE, SSL_TAG, SSL_EVAL_U, SSL_MASK_RATIO, SSL_EVAL_N = 'ssl_continue', 20261155, 1000000, 0.5, 256
RUNS_OUT = SC.SOURCE_OUT / 'runs'
DEVICE = os.environ.get('DEP12_DEVICE', 'cuda')          # cpu only for engineering dry runs
RUNS_STORE = SC.SOURCE_STORE / 'runs'
read, write, sha = SC.read, SC.write, SC.sha


def sigma_path(seed):
    return SC.SOURCE_OUT / f'sigmas_s{seed}.json'


def ssl_mask(seed, u, n_rows, n_ch, device):
    """long [n_rows, n_ch, 1]: Bernoulli(SSL_MASK_RATIO) per channel patch (CBraMod generate_mask), seeded per update."""
    import torch
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(seed), SSL_TAG, int(u)])))
    m = (rng.random((n_rows, n_ch, 1)) < SSL_MASK_RATIO).astype(np.int64)
    return torch.as_tensor(m, device=device)


def attach_recon_head(model, device):
    """model.recon = Stage1 proj_out (Linear 200->200), strictly loaded from pretrained_weights.pth, trainable."""
    import torch
    from auditory_alignment_v2.foundation_adapter import CBRAMOD_W
    assert sha(CBRAMOD_W) == SC.CBRAMOD_SHA256
    sd = torch.load(CBRAMOD_W, map_location='cpu', weights_only=True)
    head = torch.nn.Linear(200, 200)
    res = head.load_state_dict({'weight': sd['proj_out.0.weight'], 'bias': sd['proj_out.0.bias']}, strict=True)
    assert not res.missing_keys and not res.unexpected_keys
    model.recon = head.to(device)
    return model.recon


def apply_mask(model, inp, mask):
    """CBraMod PatchEmbedding mask branch done outside the net (identical maths; avoids a CUDA index_put defect, S26):
    masked channel patches -> the frozen mask_encoding vector; the net is then called with mask=None."""
    import torch
    enc = model.bb.net.patch_embedding.mask_encoding.view(1, 1, 1, -1).to(inp.dtype)
    return torch.where((mask == 1)[..., None], enc, inp)


def ssl_loss(model, x, mask, n):
    """Per-episode masked MSE (two listeners averaged) and stats; inputs scaled exactly as Backbone.forward feeds the net."""
    B, C, T = x.shape
    inp = (0.15 * x).reshape(B, C, 1, 200)
    feats = model.bb.net(apply_mask(model, inp, mask))            # proj_out is Identity inside the adapter
    y = model.recon(feats)
    total, stats = 0.0, []
    J = B // n
    for j in range(J):
        sl = slice(j * n, (j + 1) * n); m = mask[sl] == 1
        lj = ((y[sl][m] - inp[sl][m]) ** 2).mean()
        total = total + lj / J
        stats.append({'ssl_mse': float(lj.detach()), 'masked_fraction': float(m.float().mean())})
    return total, stats


def ssl_eval(model, data, panels, seed):
    """Fixed-mask reconstruction MSE (eval mode, no grad) on the first SSL_EVAL_N fit-panel anchors."""
    import torch
    was = model.training; model.eval()
    R, O = panels.P['fit_rows'][:SSL_EVAL_N], panels.P['fit_off'][:SSL_EVAL_N]
    with torch.no_grad():
        x = data.eeg(R, O); mask = ssl_mask(seed, SSL_EVAL_U, len(R), x.shape[1], x.device)
        inp = (0.15 * x).reshape(len(R), x.shape[1], 1, 200)
        y = model.recon(model.bb.net(apply_mask(model, inp, mask))); m = mask == 1
        out = {'ssl_eval_mse': float(((y[m] - inp[m]) ** 2).mean()), 'ssl_eval_input_power_masked': float((inp[m] ** 2).mean()),
               'ssl_eval_rows': int(len(R)), 'ssl_eval_masked_fraction': float(m.float().mean())}
    model.train(was)
    return out


def lr_factor(u):
    """Multiplier for the optimizer step taken at 0-based update u (fixed 10,000-update schedule)."""
    if u < WARMUP:
        return (u + 1) / WARMUP
    return 0.5 * (1.0 + math.cos(math.pi * (u - WARMUP) / (TOTAL - WARMUP)))


# ----------------------------------------------------------------------------------------------- model
def _torch():
    import torch
    import torch.nn as nn
    return torch, nn


class QVLoRA:
    pass


def make_lora_class():
    torch, nn = _torch()

    class _QVLoRA(nn.Module):
        """Parametrisation of a packed in_proj_weight [3e, e]: W + (alpha/r) [B_q A_q ; 0 ; B_v A_v]; B = 0 at start."""

        def __init__(self, e, r=LORA_RANK, alpha=LORA_ALPHA):
            super().__init__()
            self.e, self.scale = e, alpha / r
            self.A_q = nn.Parameter(torch.randn(r, e) / math.sqrt(e)); self.B_q = nn.Parameter(torch.zeros(e, r))
            self.A_v = nn.Parameter(torch.randn(r, e) / math.sqrt(e)); self.B_v = nn.Parameter(torch.zeros(e, r))

        def forward(self, W):
            assert W.shape == (3 * self.e, self.e), tuple(W.shape)
            dq = self.scale * (self.B_q @ self.A_q); dv = self.scale * (self.B_v @ self.A_v)
            return W + torch.cat([dq, torch.zeros_like(dq), dv], 0)
    return _QVLoRA


def build_model(mode, seed, device):
    """(model, info). Identical backbone (B0) and seed-identical heads for every objective and mode."""
    torch, nn = _torch()
    import torch.nn.utils.parametrize as P
    from auditory_alignment_v2.foundation_adapter import Backbone
    from ..fm_aligned import AlignedPatchLinear
    assert mode in MODES

    class SourceModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.bb = Backbone('cbramod', 'dtu', 'pretrained_full', 200)
            self.plain_keys = list(self.bb.net.state_dict().keys())
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(seed + HEAD_SEED)
                self.heads = nn.ModuleDict({v: AlignedPatchLinear(64, 200, 32) for v in VIEWS})
            self.lora_map = []
            if mode == 'lora':
                self.bb.net.requires_grad_(False)
                Lo = make_lora_class()
                with torch.random.fork_rng(devices=[]):
                    torch.manual_seed(seed + LORA_SEED)
                    for i, layer in enumerate(self.bb.net.encoder.layers):
                        for att in ('self_attn_s', 'self_attn_t'):
                            mha = getattr(layer, att); W = mha.in_proj_weight; e = mha.embed_dim
                            assert mha._qkv_same_embed_dim and W.shape == (3 * e, e)
                            P.register_parametrization(mha, 'in_proj_weight', Lo(e))
                            mha.parametrizations.in_proj_weight.original.requires_grad_(False)
                            self.lora_map.append({'layer': i, 'module': f'encoder.layers.{i}.{att}', 'tensor': 'in_proj_weight',
                                                  'shape': [3 * e, e], 'q_rows': [0, e], 'v_rows': [2 * e, 3 * e],
                                                  'k_rows_untouched': [e, 2 * e], 'rank': LORA_RANK, 'alpha': LORA_ALPHA,
                                                  'dropout': LORA_DROPOUT})
            else:
                self.bb.net.requires_grad_(True)

        def tokens(self, x):
            h = self.bb(x)
            assert h.shape[1:3] == (64, 1), tuple(h.shape)
            return h

        def forward(self, x):
            h = self.tokens(x)
            return {v: self.heads[v](h[:, :, 0]) for v in VIEWS}, h

        def merged_net_state(self):
            """Plain CBraMod state (B0 key set); LoRA deltas merged exactly into in_proj_weight."""
            out = {}
            for k in self.plain_keys:
                mod, _, attr = k.rpartition('.')
                out[k] = getattr(self.bb.net.get_submodule(mod), attr).detach().clone()
            return out

    model = SourceModel().to(device)
    groups = {'backbone': [p for n, p in model.bb.named_parameters() if p.requires_grad],
              'heads': [p for p in model.heads.parameters()]}
    info = {'mode': mode, 'seed': seed, 'n_backbone_trainable': int(sum(p.numel() for p in groups['backbone'])),
            'n_heads_trainable': int(sum(p.numel() for p in groups['heads'])),
            'n_backbone_total': int(sum(p.numel() for p in model.bb.net.parameters())),
            'backbone_trainable_tensors': [n for n, p in model.bb.named_parameters() if p.requires_grad],
            'lora_map': model.lora_map, 'recipe': 'full_onestep_v1' if mode == 'full' else 'lora_qv_r8_a16_d0'}
    return model, groups, info


def make_optimizer(groups):
    torch, _ = _torch()
    opt = torch.optim.AdamW([{'params': groups['backbone'], 'name': 'backbone'}, {'params': groups['heads'], 'name': 'heads'}],
                            lr=LR, weight_decay=WD, betas=(0.9, 0.999), eps=1e-8)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lr_factor)
    return opt, sched


# ----------------------------------------------------------------------------------------------- panels, sigmas, diagnostics
class Panels:
    def __init__(self, pool, data):
        P, rec = SS.load_panels()
        self.P, self.rec, self.pool, self.data = P, rec, pool, data
        self.n = int(rec['meta']['fit']['per_person'])
        self.fit_people = rec['meta']['fit']['people']; self.dev_people = rec['meta']['dev']['people']
        self.dev_per = int(rec['meta']['dev']['per_person'])

    def rows(self):
        return np.r_[self.P['fit_rows'], self.P['dev_rows']]

    def features(self, model, chunk=256):
        """eval/no_grad: projected U per view, audio heads per view, raw env [*, 8], common representation (CPU float32)."""
        torch, _ = _torch()
        out = {}
        model.eval()
        with torch.no_grad():
            for split in ('fit', 'dev'):
                R, O = self.P[f'{split}_rows'], self.P[f'{split}_off']
                proj = {v: [] for v in VIEWS}; aud = {v: [] for v in VIEWS}; env = []; rep = []
                for a in range(0, len(R), chunk):
                    x = self.data.eeg(R[a:a + chunk], O[a:a + chunk])
                    pj, h = model(x); A, raw = self.data.audio(R[a:a + chunk], O[a:a + chunk])
                    for v in VIEWS:
                        proj[v].append(pj[v].double().cpu()); aud[v].append(A[v].double().cpu())
                    env.append(raw['env'].double().cpu()); rep.append(SC.tokens_to_U(h).cpu())
                out[split] = {'proj': {v: torch.cat(proj[v]) for v in VIEWS}, 'aud': {v: torch.cat(aud[v]) for v in VIEWS},
                              'env': torch.cat(env), 'rep': torch.cat(rep), 'who': self.P[f'{split}_who']}
        return out


def calibrate_sigmas(seed, model, panels):
    """Once per seed at the initial state (identical for both modes: LoRA B = 0); frozen 0444; reused by every CS arm."""
    torch, _ = _torch()
    from . import dependence_measure as DM
    path = sigma_path(seed)
    feats = panels.features(model)
    fit = feats['fit']; who = fit['who']; n = panels.n
    body = {'version': 'DEP12_SOURCE_SIGMA_v1', 'seed': seed, 'panel_sha256': panels.rec['sha256'],
            'panel': f'source-fit panel, {n} legal anchors x {len(panels.fit_people)} fit listeners', 'views': {},
            'rule': 'calibrate_grouped_overlap_sigma (package reference): within-listener off-diagonal distances, pooled lower median',
            'state': 'initial (Stage1 CBraMod + seed heads; eval mode)'}
    for v in VIEWS:
        for side, X in (('u', fit['proj'][v]), ('y', fit['aud'][v])):
            rows = {str(panels.fit_people[i]): X[torch.as_tensor(who == i)].numpy() for i in sorted(set(who.tolist()))}
            assert all(len(r) == n for r in rows.values())
            c = DM.calibrate_grouped_overlap_sigma(rows, calibration_scope='source_train', panel_id=f"dep12_fit_panel_{panels.rec['sha256'][:16]}")
            s = float(c['overlap_sigma'])
            if not (math.isfinite(s) and s > 0):
                raise FloatingPointError(f'sigma_{side} for {v} is {s}: technical error, no epsilon substitution')
            body['views'].setdefault(v, {})[f'sigma_{side}'] = s
            body['views'][v][f'calibration_{side}'] = {k: c[k] for k in c if k not in ('person_ids',)}
    import fcntl
    lock = SC.SOURCE_OUT / 'claims' / f'sigma_s{seed}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        fcntl.flock(h, fcntl.LOCK_EX)              # concurrent first units of one seed: one writer, the others verify
        if path.exists():
            old = read(path)
            for v in VIEWS:
                for k in ('sigma_u', 'sigma_y'):
                    rel = abs(old['views'][v][k] - body['views'][v][k]) / max(1.0, abs(body['views'][v][k]))
                    old.setdefault('recheck_max_rel_diff', 0.0); old['recheck_max_rel_diff'] = max(old['recheck_max_rel_diff'], rel)
                    assert rel <= SIGMA_RECHECK_REL_TOL, (v, k, rel)
            return old, feats
        write(path, {**body, 'created_utc': SC.now(), 'job': os.environ.get('SLURM_JOB_ID')}, freeze=True)
    return read(path), feats


def effective_rank(X):
    torch, _ = _torch()
    X = X.double().to('cuda' if torch.cuda.is_available() else 'cpu'); X = X - X.mean(0)
    s = torch.linalg.svdvals(X) ** 2
    tot = float(s.sum())
    if tot <= 0:
        return {'total_variance': 0.0, 'effective_rank': 0.0}
    p = s / s.sum(); p = p[p > 0]
    return {'total_variance': tot / max(len(X) - 1, 1), 'effective_rank': float(torch.exp(-(p * p.log()).sum())),
            'top1_fraction': float(s[0] / s.sum())}


def diagnostics(feats, sig, panels, model, ref):
    """E0 diagnostics (02 §4) on fixed panels; projector and backbone recorded separately."""
    torch, _ = _torch()
    from . import dependence_measure as DM
    out = {'views': {}}
    for split, nulls, per in (('fit', panels.P['fit_diag_null'], panels.n), ('dev', panels.P['dev_diag_null'], min(panels.n, panels.dev_per))):
        F = feats[split]; who = F['who']; people = sorted(set(who.tolist()))
        for v in VIEWS:
            su, sy = sig['views'][v]['sigma_u'], sig['views'][v]['sigma_y']
            acc = {'raw': [], 'null': [], 'excess': [], 'k_identity': 0, 'k_constant': 0, 'k_offdiag_mean': [],
                   'top1_correct': [], 'top1_mismatched': [], 'mean_rank_correct': []}
            for e, i in enumerate(people):
                m = torch.as_tensor(who == i)
                U = F['proj'][v][m][:per].numpy(); Y = F['aud'][v][m][:per].numpy()
                K, L = DM.gaussian_gram(U, su), DM.gaussian_gram(Y, sy)
                raw = DM.parzen_cs(K, L)['raw_cs_nats']
                nl = [DM.parzen_cs(K, L[np.ix_(p, p)])['raw_cs_nats'] for p in nulls[e].astype(np.int64)]
                kd = DM.kernel_diagnostics(K)
                S = U @ Y.T; rank = (S > S[np.arange(per), np.arange(per)][:, None]).sum(1)
                pi = nulls[e][0].astype(np.int64)
                acc['raw'].append(raw); acc['null'].append(float(np.mean(nl))); acc['excess'].append(raw - float(np.mean(nl)))
                acc['k_identity'] += int(kd['identity_like']); acc['k_constant'] += int(kd['constant_like'])
                acc['k_offdiag_mean'].append(kd['offdiag_mean'])
                acc['top1_correct'].append(float(np.mean(S.argmax(1) == np.arange(per))))
                acc['top1_mismatched'].append(float(np.mean(S.argmax(1) == pi)))
                acc['mean_rank_correct'].append(float(rank.mean()))
            rk = effective_rank(F['proj'][v])
            cos = F['proj'][v] @ F['proj'][v].T; off = ~torch.eye(len(cos), dtype=torch.bool)
            out['views'].setdefault(v, {})[split] = {
                'raw_cs_mean': float(np.mean(acc['raw'])), 'null_mean': float(np.mean(acc['null'])),
                'excess_mean': float(np.mean(acc['excess'])), 'excess_per_listener': [float(x) for x in acc['excess']],
                'k_identity_like_episodes': acc['k_identity'], 'k_constant_like_episodes': acc['k_constant'],
                'k_offdiag_mean': float(np.mean(acc['k_offdiag_mean'])),
                'top1_correct': float(np.mean(acc['top1_correct'])), 'top1_mismatched': float(np.mean(acc['top1_mismatched'])),
                'chance_top1': 1.0 / per, 'mean_rank_correct': float(np.mean(acc['mean_rank_correct'])),
                'proj_total_variance': rk['total_variance'], 'proj_effective_rank': rk['effective_rank'],
                'proj_mean_offdiag_cosine': float(cos[off].mean()), 'episodes': len(people), 'n_per_episode': per}
    rep = feats['fit']['rep']
    rk = effective_rank(rep[:2048])
    out['backbone_rep'] = {'fit_total_variance': rk['total_variance'], 'fit_effective_rank_2048': rk['effective_rank'],
                           'fit_top1_variance_fraction': rk.get('top1_fraction'),
                           'mean_cosine_to_step0_rep': float((rep[:512] * ref['rep0']).sum(1).mean()) if ref.get('rep0') is not None else None}
    merged = model.merged_net_state()
    num = den = 0.0
    for k, v0 in ref['b0'].items():
        d = merged[k].float().cpu() - v0.float(); num += float((d * d).sum()); den += float((v0.float() ** 2).sum())
    out['param_change'] = {'backbone_rel_l2_vs_B0': math.sqrt(num) / math.sqrt(den)}
    num = den = 0.0
    for k, v in model.heads.state_dict().items():
        d = v.float().cpu() - ref['heads0'][k].float(); num += float((d * d).sum()); den += float((ref['heads0'][k].float() ** 2).sum())
    out['param_change']['heads_rel_l2_vs_init'] = math.sqrt(num) / math.sqrt(den)
    return out


# ----------------------------------------------------------------------------------------------- the run
def run_dirs(objective, mode, seed, probe_dir=None):
    name = SC.run_name(objective, mode, seed)
    if probe_dir:
        return name, Path(probe_dir) / 'out' / name, Path(probe_dir) / 'store' / name
    return name, RUNS_OUT / name, RUNS_STORE / name


def source_files():
    here = Path(__file__).parent
    files = [here / f for f in ('trainer_ext3.py', 'objectives.py', 'training_objectives_torch.py', 'dependence_measure.py',
                                 'source_sampler.py', 'source_common.py', 'devprobe.py')]
    files += [SC.REPO / 'auditory_alignment_v2/foundation_adapter.py', SC.REPO / 'auditory_alignment_v3/fm_aligned.py',
              SC.REPO / 'auditory_alignment_v3/aln41/timebank.py', SC.REPO / 'auditory_alignment_v3/aln41/source.py',
              SC.REPO / 'auditory_alignment_v3/prior33/views.py', SC.REPO / 'auditory_alignment_v3/prior33/model.py',
              SC.REPO / 'auditory_alignment_v3/prior33/contract.py']
    return {str(p.relative_to(SC.REPO)): sha(p) for p in files}


def atomic_save(obj, path):
    torch, _ = _torch()
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + '.tmp'); torch.save(obj, tmp); os.replace(tmp, path)
    return sha(path)


def inert_gradient_report(model, mode):
    """Update-1 gradient norms of the single-key temporal-attention Q (and K) path vs live references (float64 sums)."""
    torch, _ = _torch()
    sq = lambda t: float((t.detach().double() ** 2).sum()) if t is not None else 0.0
    out = {}
    if mode == 'lora':
        g = {'t_q': 0.0, 't_v': 0.0, 's_q': 0.0, 's_v': 0.0}
        for n_, p in model.bb.named_parameters():
            if n_.endswith(('.B_q', '.B_v')):
                key = ('t_' if '.self_attn_t.' in n_ else 's_') + n_[-1]
                g[key] += sq(p.grad)
        out = {k: math.sqrt(v) for k, v in g.items()}
        out['inert_ratio'] = out['t_q'] / max(math.sqrt(g['s_q'] + g['s_v'] + g['t_v']), 1e-300)
        out['live_reference_ratio_s_q_over_s_v'] = out['s_q'] / max(out['s_v'], 1e-300)
    else:
        g = {'t_qk': 0.0, 't_v': 0.0, 's_q': 0.0, 's_v': 0.0}
        for layer in model.bb.net.encoder.layers:
            for att, pre in ((layer.self_attn_t, 't_'), (layer.self_attn_s, 's_')):
                e = att.embed_dim; W = att.in_proj_weight.grad; b = att.in_proj_bias.grad
                if pre == 't_':
                    g['t_qk'] += sq(W[:2 * e]) + sq(b[:2 * e]); g['t_v'] += sq(W[2 * e:]) + sq(b[2 * e:])
                else:
                    g['s_q'] += sq(W[:e]) + sq(b[:e]); g['s_v'] += sq(W[2 * e:]) + sq(b[2 * e:])
        out = {k: math.sqrt(v) for k, v in g.items()}
        out['inert_ratio'] = out['t_qk'] / max(out['t_v'], 1e-300)
        out['live_reference_ratio_s_q_over_s_v'] = out['s_q'] / max(out['s_v'], 1e-300)
    out['tolerance'] = INERT_REL_TOL
    return out


def train(objective, mode, seed, end, probe_dir=None, deterministic=False, stop_after=None, log=print, bank_end=None):
    """Advance run (objective, mode, seed) from its latest saved state to update `end` (<= 10,000)."""
    torch, _ = _torch()
    assert objective in OBJ.OBJECTIVES + (SSL_OBJECTIVE,) and mode in MODES and (end in CHECKPOINTS[1:] or probe_dir) and 0 < end <= TOTAL
    ssl = objective == SSL_OBJECTIVE
    started = time.time(); dev = torch.device(DEVICE); cuda = dev.type == 'cuda'
    if cuda:
        torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
        torch.cuda.reset_peak_memory_stats()
    if deterministic:
        os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
        torch.use_deterministic_algorithms(True, warn_only=True)
        torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False
    name, out_dir, store = run_dirs(objective, mode, seed, probe_dir)
    out_dir.mkdir(parents=True, exist_ok=True, mode=0o700); store.mkdir(parents=True, exist_ok=True, mode=0o700)
    srcs = source_files()
    stream = SS.load_stream(seed); srec = read(SS.stream_receipt(seed))
    n = SS.anchors_per_person(); assert stream['rows'].shape[2] == n
    pool = SS.Pool()
    panels_np, prec = SS.load_panels()
    receipt_path = out_dir / 'receipt.json'
    receipt = read(receipt_path) if receipt_path.exists() else {
        'version': 'DEP12_SOURCE_RUN_v1', 'run': name, 'objective': objective, 'mode': mode, 'seed': seed, 'checkpoints': {},
        'units': [], 'stream_sha256': srec['sha256'], 'panels_sha256': prec['sha256'], 'coverage_sha256': sha(SS.COVERAGE),
        'sources': srcs, 'probe_dir': str(probe_dir) if probe_dir else None,
        'optimizer': {'kind': 'AdamW', 'lr_backbone': LR, 'lr_heads': LR, 'weight_decay': WD, 'weight_decay_scope': 'every trainable tensor',
                      'betas': [0.9, 0.999], 'eps': 1e-8, 'schedule': f'linear warmup {WARMUP} then cosine to 0 at {TOTAL}',
                      'grad_clip_global': CLIP}, 'anchors_per_person': n}
    assert receipt['stream_sha256'] == srec['sha256'] and receipt['panels_sha256'] == prec['sha256']
    if receipt['sources'] != srcs:
        raise RuntimeError('frozen source drift for this run: ' + str({k for k in srcs if receipt['sources'].get(k) != srcs[k]}))
    # resume point
    begin, state = 0, None
    cks = sorted((int(p.name[4:-9]), p) for p in store.glob('step*.state.pt'))
    if cks:
        state = torch.load(cks[-1][1], map_location='cpu', weights_only=False); assert int(state['step']) == cks[-1][0]
    if (store / 'resume.pt').exists():
        rs = torch.load(store / 'resume.pt', map_location='cpu', weights_only=False)
        if state is None or int(rs['step']) > int(state['step']):
            state = rs
        del rs
    if state is not None:
        begin = int(state['step'])
    if begin >= end:
        log(name, 'already at', begin, '>= end', end); return receipt
    rows_needed = np.r_[stream['rows'][begin:max(end, bank_end or 0)].reshape(-1), panels_np['fit_rows'], panels_np['dev_rows']]
    data = SS.SourceData(pool, rows_needed, dev)
    panels = Panels(pool, data)
    model, groups, info = build_model(mode, seed, dev)
    if ssl:
        rh = attach_recon_head(model, dev); groups['recon'] = list(rh.parameters())
        info['recon_head'] = 'Stage1 proj_out.0 (Linear 200->200), strict, trainable'
        groups['heads'] = groups['heads'] + groups['recon']
    opt, sched = make_optimizer(groups)
    b0 = SC.b0_net_state()
    ref = {'b0': b0}
    if state is None:
        merged = model.merged_net_state()
        assert set(merged) == set(b0) and all(torch.equal(merged[k].cpu(), b0[k]) for k in b0), 'step-0 backbone != B0'
        receipt['b0_equal_at_step0'] = True; receipt['b0_net_digest'] = SC.net_digest(b0)
        receipt['model_info'] = info
        sig, feats0 = calibrate_sigmas(seed, model, panels)
        heads0 = {k: v.detach().cpu().clone() for k, v in model.heads.state_dict().items()}
        receipt['initial_heads_digest'] = SC.net_digest(heads0)
        rep0 = feats0['fit']['rep'][:512].clone()
        torch.manual_seed(seed + TRAIN_SEED)
        if cuda:
            torch.cuda.manual_seed_all(seed + TRAIN_SEED)
        logs, diags, gacc = [], [], {'backbone': [], 'heads': []}
    else:
        model.load_state_dict(state['model'], strict=True); opt.load_state_dict(state['optimizer']); sched.load_state_dict(state['scheduler'])
        torch.set_rng_state(state['torch_rng'])
        if cuda:
            torch.cuda.set_rng_state(state['cuda_rng'])
        sig = read(sigma_path(seed)); assert sig['seed'] == seed
        heads0, rep0 = state['heads0'], state['rep0']
        logs, diags, gacc = state['logs'], state['diags'], state['gacc']
        assert state['run'] == name and state['stream_sha256'] == srec['sha256']
        feats0 = None
    ref.update(heads0=heads0, rep0=rep0)
    receipt['sigmas'] = {v: {k: sig['views'][v][k] for k in ('sigma_u', 'sigma_y')} for v in VIEWS}
    receipt['sigma_receipt_sha256'] = sha(sigma_path(seed))
    receipt['training_objective'] = ('ssl_masked_patch_reconstruction (mask %.1f, Stage1 proj_out head, MSE on masked tokens; no audio)' % SSL_MASK_RATIO) if ssl else objective
    receipt['sigma_recheck_max_rel_diff'] = sig.get('recheck_max_rel_diff')
    receipt['tf32'] = {'matmul': bool(torch.backends.cuda.matmul.allow_tf32), 'cudnn': bool(torch.backends.cudnn.allow_tf32)} if cuda else None
    params = groups['backbone'] + groups['heads']
    rows_t, off_t, perm_t, wrong_t = stream['rows'], stream['off'], stream['perm'], stream['wrong']

    def snapshot(step, feats=None):
        model.eval()
        feats = feats if feats is not None else panels.features(model)
        d = diagnostics(feats, sig, panels, model, ref)
        if ssl:
            d['ssl'] = ssl_eval(model, data, panels, seed)
        d['step'] = step; d['grad_norm_mean_since_last'] = {g: (float(np.mean(v)) if v else None) for g, v in gacc.items()}
        for g in gacc:
            gacc[g] = []
        diags.append(d)
        dp = None
        if step in CHECKPOINTS:
            from . import devprobe as DP
            dp = DP.score(feats['fit']['rep'].to(dev), feats['fit']['env'], feats['dev']['rep'].to(dev), feats['dev']['env'],
                          feats['dev']['who'], panels.dev_people)
            dp['step'] = step
            write(out_dir / f'devprobe_step{step}.json', dp)
            serve = {'net': {k: v.cpu() for k, v in model.merged_net_state().items()},
                     **({'recon_head': {k: v.detach().cpu() for k, v in model.recon.state_dict().items()}} if ssl else {}),
                     'heads': {k: v.detach().cpu() for k, v in model.heads.state_dict().items()}, 'step': step, 'run': name}
            serve['net_digest'] = SC.net_digest(serve['net'])
            sp = store / f'step{step}.serve.pt'; ssha = atomic_save(serve, sp)
            st = full_state(step); tp = store / f'step{step}.state.pt'; tsha = atomic_save(st, tp)
            receipt['checkpoints'][str(step)] = {'serve_path': str(sp), 'serve_sha256': ssha, 'state_path': str(tp), 'state_sha256': tsha,
                                                 'net_digest': serve['net_digest'], 'devprobe_dev_mean_r': dp['dev_listener_mean_r'],
                                                 'job': os.environ.get('SLURM_JOB_ID'), 'saved_utc': SC.now()}
        receipt['last_diag'] = d
        write(out_dir / 'diagnostics.json', {'run': name, 'diags': diags})
        write(receipt_path, receipt)
        model.train()
        return d, dp

    def full_state(step):
        return {'model': model.state_dict(), 'optimizer': opt.state_dict(), 'scheduler': sched.state_dict(), 'step': step,
                'torch_rng': torch.get_rng_state(), 'cuda_rng': torch.cuda.get_rng_state() if cuda else None, 'logs': logs, 'diags': diags,
                'gacc': gacc, 'heads0': heads0, 'rep0': rep0, 'run': name, 'stream_sha256': srec['sha256'],
                'sources': srcs, 'objective': objective, 'mode': mode, 'seed': seed}

    unit = {'begin': begin, 'end': end, 'job': os.environ.get('SLURM_JOB_ID'), 'started_utc': SC.now(),
            'device': torch.cuda.get_device_name(0) if cuda else 'cpu'}
    if begin == 0:
        snapshot(0, feats0)
    del feats0
    model.train(); t_loop = time.time(); first_check = begin == 0
    for u in range(begin, end):
        rr = rows_t[u].astype(np.int64); oo = off_t[u].astype(np.int64)
        x = data.eeg(rr.reshape(-1), oo.reshape(-1))
        if ssl:
            total, stats = ssl_loss(model, x, ssl_mask(seed, u, x.shape[0], x.shape[1], dev), n)
        else:
            A, _ = data.audio(rr.reshape(-1), oo.reshape(-1))
            proj, _ = model(x)
            total = 0.0; stats = []
        for j in (range(0) if ssl else range(rr.shape[0])):
            sl = slice(j * n, (j + 1) * n); lj = 0.0; sj = {}
            for v in VIEWS:
                kw = {}
                if objective in OBJ.USES_SIGMA:
                    kw = dict(sigma_u=sig['views'][v]['sigma_u'], sigma_y=sig['views'][v]['sigma_y'], perms=perm_t[u, j].astype(np.int64),
                              wrong=wrong_t[u, j].astype(np.int64))
                loss, st = OBJ.episode_loss(objective, proj[v][sl], A[v][sl].detach(), **kw)
                lj = lj + loss / len(VIEWS); sj[v] = OBJ.compact(st)
            total = total + lj / rr.shape[0]; stats.append(sj)
        opt.zero_grad(set_to_none=True)
        total.backward()
        gn = {g: float(torch.linalg.vector_norm(torch.stack([p.grad.detach().norm() for p in groups[g] if p.grad is not None]))) if any(p.grad is not None for p in groups[g]) else 0.0
              for g in ('backbone', 'heads')}
        gt = torch.nn.utils.clip_grad_norm_(params, CLIP)
        if not torch.isfinite(total) or not torch.isfinite(gt):
            raise FloatingPointError(f'nonfinite objective or gradient at update {u}')
        if first_check:
            names = [n_ for n_, p in model.bb.named_parameters() if p.requires_grad]
            missing = [n_ for n_, p in model.bb.named_parameters() if p.requires_grad and not n_.endswith(UNUSED_WITHOUT_MASK)
                       and (p.grad is None or not bool(torch.any(p.grad != 0)))]
            if mode == 'lora':   # B = 0 at start: dL/dA = 0 exactly at update 1; B must receive gradient (except inert t-attn Q)
                missing = [m for m in missing if not (m.endswith('.A_q') or m.endswith('.A_v') or m.endswith(INERT_SINGLE_PATCH))]
            assert not missing, f'trainable backbone tensors without gradient: {missing[:5]}'
            if ssl:   # audio projection heads are unused (no gradient); the reconstruction head must train
                assert all(p.grad is None for p in model.heads.parameters())
                assert all(p.grad is not None and bool(torch.any(p.grad != 0)) for p in groups['recon'])
            else:
                assert all(p.grad is not None and bool(torch.any(p.grad != 0)) for p in groups['heads'])
            ig = inert_gradient_report(model, mode)
            receipt['update1_inert_gradient'] = ig
            assert ig['inert_ratio'] < INERT_REL_TOL, f'single-key temporal attention is not inert: {ig}'
            receipt['update1_gradient_check'] = {'trainable_backbone_tensors': len(names), 'without_gradient_exempt': list(UNUSED_WITHOUT_MASK) if mode == 'full' else ['A_q/A_v at update 1 (B=0)', 'self_attn_t Q adapters (single key: structurally inert)']}
            first_check = False
        opt.step(); sched.step()
        gacc['backbone'].append(gn['backbone']); gacc['heads'].append(gn['heads'])
        step = u + 1
        if step % LOG_EVERY == 0 or u < 3 or probe_dir:
            logs.append({'update': step, 'loss': float(total.detach()), 'grad_norm_backbone': gn['backbone'], 'grad_norm_heads': gn['heads'],
                         'grad_norm_total_preclip': float(gt), 'lr': float(opt.param_groups[0]['lr']),
                         'people': [str(stream['people'][i]) for i in stream['who'][u]], 'stats': stats})
        if step % DIAG_EVERY == 0 or step in CHECKPOINTS:
            snapshot(step)
        if step % RESUME_EVERY == 0 and step not in CHECKPOINTS and not probe_dir:
            atomic_save(full_state(step), store / 'resume.pt')
        if step % 500 == 0:
            log(name, 'update', step, round(float(total.detach()), 5), 's/update', round((time.time() - t_loop) / (step - begin), 4), flush=True)
        if stop_after is not None and step >= stop_after:
            break
    seconds = time.time() - t_loop
    if step < end or (probe_dir and step not in CHECKPOINTS):
        atomic_save(full_state(step), store / 'resume.pt')
    unit.update(finished_step=step, loop_seconds=seconds, seconds_per_update=seconds / max(step - begin, 1),
                total_seconds=time.time() - started, gpu_peak_mb=torch.cuda.max_memory_allocated() / 2 ** 20 if cuda else None,
                gpu_peak_reserved_mb=torch.cuda.max_memory_reserved() / 2 ** 20 if cuda else None,
                gpu_total_mb=torch.cuda.get_device_properties(0).total_memory / 2 ** 20 if cuda else None, bank_rows_updates=[begin, max(end, bank_end or 0)],
                bank_nbytes=data.bank.nbytes, finished_utc=SC.now())
    receipt['units'].append(unit)
    if step >= end and step in CHECKPOINTS and (store / 'resume.pt').exists() and not probe_dir:
        (store / 'resume.pt').unlink()
    receipt['status'] = 'complete' if step >= TOTAL else f'at_step_{step}'
    write(receipt_path, receipt)
    del data, model, opt
    gc.collect()
    if cuda:
        torch.cuda.empty_cache()
    return receipt


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')  # trainer_ext3
    r.add_argument('--objective', required=True); r.add_argument('--mode', required=True); r.add_argument('--seed', type=int, required=True)
    r.add_argument('--end', type=int, required=True); r.add_argument('--probe-dir')
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'Slurm only'
    os.umask(0o077)
    if a.cmd == 'run':
        train(a.objective, a.mode, a.seed, a.end, probe_dir=a.probe_dir)


if __name__ == '__main__':
    main()
