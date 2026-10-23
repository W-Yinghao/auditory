"""Paper W5 / manuscript Table 6 row 'MindMix alignment recipe (common backbone)' (App. B.2): MindMix's Stage-2 CALRA +
contrastive recipe re-implemented on the common CBraMod Stage1 initialisation, the ALN4.1 SparrKULee source partition and its
episode stream. A reimplementation on common inputs, not the authors' released model. Arms: CALRA (the Table 6 row; seeds
3401 / 3407 / 3413) and PROJ_NCE (descriptive ablation, CALRA removed; seed 3401 only).

EEG branch (before fusion; the transfer representation read by aln41.frozen): aln41 TimeBankModel tokens [B, 3, 64, 200]
  (CBraMod pretrained_full, crops W0/W1/W2) -> per slot LayerNorm(200) per channel token, Linear(64*200 -> 256), GELU,
  LayerNorm(256) (the project's channel-aware readout; Linear/GELU/LN as MindMix eeg_proj) -> pooled over slots with
  q = softmax(a), a = 3 learned gate logits, init 0 (= MindMix mean pooling). Checkpoints carry 'backbone' (net.*) and 'a'.
Audio branch (MindMix): facebook/wav2vec2-base @ XM.W2V_REV, trainable, train mode, mask_time_min_masks = 1 (released 2;
  ~0.26 of 39 frames masked vs ~0.19 for MindMix's 99-frame 2 s windows); input = 16 kHz mono SparrKULee stimulus over
  [-0.2, 0.6) s around the anchor (12 800 samples, inside the anchor's own 5 s segment), per-window peak normalisation;
  last_hidden_state.mean(1) -> Linear(768, 256), GELU, LayerNorm(256).
  16 kHz bank (prepare(), CPU, once): rich_streams.json source of every stream, bytes / decoded-audio sha256 and
  n_samples_16k asserted against the record, prior33.build_rich read_npz_gz -> _mono -> to16k (the rich-view chain;
  16 kHz sample 250 t = 64 Hz stream sample t; all 72 streams clock tau 0).
Fusion and loss (official, MindMix@98445f3): universal_models.CALRA(embed_dim=256, use_auditory_type=False), applied row-wise
  (fused_eeg_i, aligned_audio_i) = CALRA(e_i, x_i); universal_models.ClipLoss: rows = EEG, one-directional cross-entropy
  toward the diagonal, logit scale log(1/0.07) fixed (Stage-2 pretraining keeps ClipLoss outside the optimiser).
  PROJ_NCE: ClipLoss(e, x).
Batches: one person's 32 QUERY anchors of the shared stream (support blocks carry no gradient in TCS either); update loss = mean
  over the update's two people. AdamW (wd 1e-4 on matrices; biases, norms and a without decay), cosine, clip 5, 10 000 updates,
  snapshots 0/2500/5000/10000. LR calibration: CALRA, 1e-4 vs 3e-4, 1 000 updates, seed 3401, common dev ridge probe
  (source.ridge_probe on raw tokens; source.select rule); PROJ_NCE inherits it. Seeds use the R1 / R2 streams.
Audit (GPU, eval, no grad): source DEV audit blocks (source.make_stream on the dev pool, seed AUDIT_SEED; person blocks of 32,
  cross-family wrong bijection) and DTU cs test anchors (frozen.py cs geometry, attended / ignored audio from the aln42
  binding). Per block: official ClipLoss and in-batch top-1 for real+correct, real+wrong, noise+correct (noise = Gaussian
  with each anchor-channel's mean / SD over the crop span) and pre-fusion; blind order-symmetrised margin m(correct, wrong)
  and the privileged-slot scorer (both slot orders) for real and noise EEG; embeddings for the CS summary
  (paper.cs_atlas estimator = aln41.cs_qmi_reference.cs_qmi).
Layout: OUT/<arm>/seed<S>/{source_v1, frozen_v1, readout_v1} in the aln41 schemas; frozen_ctx(arm, seed) re-points
  aln41.source / aln41.frozen / aln41.readout (as aln41.r2.seeded) so frozen.py and readout.py run unchanged (CALRA only).
CLI: --make-plan | --prepare | --smoke | --worker | --unit ID | --audit ID | --frozen ARM SEED ID | --readout ARM SEED | --summarize
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import fcntl
import hashlib
import math
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from ..aln41 import frozen as FZ, r2 as R2, readout as RO, source as SRC
from ..aln42 import external_mindmix as XM

OUT = Path(core.OUT) / 'paper' / 'calra_v1'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/paper/calra_v1')
R1_STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln41/source_v1')
ARMS = ('CALRA', 'PROJ_NCE')
ARM_SEEDS = {'CALRA': (3401, 3407, 3413), 'PROJ_NCE': (3401,)}
FROZEN_ARMS = ('CALRA',)
TABLE6_ROW = 'MindMix alignment recipe (common backbone)'
D, TEMP, BLOCK = 256, 0.07, 32
W2V_MIN_MASKS, W2V_MIN_MASKS_RELEASED = 1, 2
AUD_WIN_S, FS_AUD, PER64 = (-0.2, 0.6), 16000, 250
AUD_N = int(round((AUD_WIN_S[1] - AUD_WIN_S[0]) * FS_AUD))          # 12 800
AUDIT_SEED, AUDIT_UPDATES, DTU_EVERY = 3460, 16, 4                    # dev audit stream; DTU: every 4th of frozen's 16 cs anchors
SMOKE_UPDATES = {'CALRA': 50, 'PROJ_NCE': 3}
SMOKE_BLOCKS = 2
NAME, LANE, SBATCH = 'c3_s35calra', 's35_paper_calra', 'slurm/aln35_paper_calra.sbatch'
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest

DEPARTURES = {
    'loss': 'official one-directional ClipLoss (EEG rows), logit scale fixed at log(1/0.07) as in MindMix Stage 2; not symmetrised',
    'eeg_backbone': 'common CBraMod Stage1 (pretrained_full), three 400 ms crops per anchor, instead of the released LaBraM-style encoder',
    'eeg_readout': "channel-aware LN + Linear(64*200 -> 256) + GELU + LN per slot (project default; MindMix: channel mean -> Linear(200, 256))",
    'slot_pooling': 'learned gate logits a (init 0 = mean pooling), as every Table 6 arm; frozen readouts use q0 = softmax(a)',
    'audio_window': '0.8 s ([-0.2, 0.6) s around the anchor, inside its 5 s segment) instead of 2 s; wav2vec2 sees 39 frames',
    'specaugment': f'wav2vec2 mask_time_min_masks {W2V_MIN_MASKS} (released {W2V_MIN_MASKS_RELEASED}): masked fraction ~0.26 at 39 frames '
                   '(released config: ~0.44 at 39 frames, ~0.19 at MindMix 99 frames)',
    'optimizer': 'ALN4.1 source recipe (AdamW wd 1e-4 on matrices, cosine, clip 5, no warmup, 10 000 updates of 2 x 32 query anchors) '
                 'instead of MindMix Stage 2 (AdamW wd 0.05, 10-epoch warmup, cosine, lr 1e-4, batch 32)',
    'batches': 'person-homogeneous query blocks of the shared ALN4.1 episode stream; support blocks unused',
    'lr': 'source-only calibration 1e-4 vs 3e-4 over 1 000 updates with the common dev ridge probe (CALRA); PROJ_NCE inherits'}


def sources():
    repo = Path(core.REPO)
    files = [Path(__file__), repo / 'auditory_alignment_v3/aln41/source.py', repo / 'auditory_alignment_v3/aln41/timebank.py',
             repo / 'auditory_alignment_v3/aln41/frozen.py', repo / 'auditory_alignment_v3/aln42/external_mindmix.py',
             repo / 'auditory_alignment_v3/prior33/build_rich.py', repo / 'auditory_alignment_v2/foundation_adapter.py',
             XM.MM_REPO / 'universal_models.py']
    return {str(p): sha(p) for p in files}


def seed_base(arm, seed):     # aln41-schema root (frozen.py reads SRC.BASE/selection.json and SRC.BASE/units)
    return OUT / arm / f'seed{seed}' / 'source_v1'


def stream_file(seed):
    if seed == 3401:
        return R1_STORE / 'stream.npz', R2.R1_SOURCE / 'plan.json'
    return R2.STORE_ROOT / f'seed{seed}' / 'source_v1' / 'stream.npz', R2.ROOT / f'seed{seed}' / 'source_v1' / 'plan.json'


def all_seeds():
    return sorted({s for v in ARM_SEEDS.values() for s in v})


def peak_rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20


# ------------------------------------------------------------------------------------------------------------- model
def mm_classes():
    """CALRA / ClipLoss from the pinned checkout (XM.official sets the offline HF cache before transformers is imported)."""
    XM.official()
    import universal_models as UM
    assert Path(UM.__file__).resolve() == (XM.MM_REPO / 'universal_models.py').resolve()
    return UM.CALRA, UM.ClipLoss


def build(arm, seed, fs_native=64, dataset_key='dtu', n_ch=64):
    import torch
    import torch.nn as nn
    assert arm in ARMS, arm
    CALRA, ClipLoss = mm_classes()
    from transformers import Wav2Vec2Model
    from ..aln41 import timebank as TB

    class EEGBranch(nn.Module):
        def __init__(self):
            super().__init__()
            self.norm = nn.LayerNorm(200); self.lin = nn.Linear(n_ch * 200, D); self.act = nn.GELU(); self.out = nn.LayerNorm(D)

        def forward(self, tok, a):                                   # tok [B, 3, C, 200] -> [B, D]
            z = self.out(self.act(self.lin(self.norm(tok).flatten(2))))
            return torch.einsum('k,bkd->bd', torch.softmax(a, 0), z)

    class W5(nn.Module):
        def __init__(self):
            super().__init__()
            self.arm = arm
            self.tb = TB.TimeBankModel(dataset_key, n_ch, fs_native, views=())
            self.eeg_proj = EEGBranch()
            self.audio_encoder = Wav2Vec2Model.from_pretrained('facebook/wav2vec2-base', revision=XM.W2V_REV,
                                                               mask_time_min_masks=W2V_MIN_MASKS)
            assert self.audio_encoder.config.mask_time_min_masks == W2V_MIN_MASKS
            self.audio_proj = nn.Sequential(nn.Linear(768, D), nn.GELU(), nn.LayerNorm(D))
            self.fusion = CALRA(embed_dim=D, use_auditory_type=False) if arm == 'CALRA' else None
            self.clip = ClipLoss(initial_temp=TEMP).requires_grad_(False)

        def eeg(self, crops, a):
            return self.eeg_proj(self.tb.tokens(crops), a)

        def audio(self, wav):
            wav = wav / wav.abs().amax(-1, keepdim=True).clamp_min(1e-8)
            return self.audio_proj(self.audio_encoder(wav).last_hidden_state.mean(1))

        def fuse(self, e, x):                                        # official pairing: both sides from CALRA(e_i, x_i)
            return self.fusion(e, x) if self.fusion is not None else (e, x)

        def loss(self, e, x):
            return self.clip(*self.fuse(e, x))

        def s(self, e, t, c):                                        # s(c | t) = exp(ls) cos(CALRA(e,t)[0], CALRA(e,c)[1])
            f, _ = self.fuse(e, t); _, g = self.fuse(e, c)
            return self.clip.logit_scale.exp() * torch.nn.functional.cosine_similarity(f, g, dim=-1)

    torch.manual_seed(seed)
    model = W5()
    a = torch.zeros(3, requires_grad=True)
    return model, a


def param_groups(model, a, lr):
    """source.param_groups (source.py:407) restricted to trainable tensors (ClipLoss.logit_scale stays fixed)."""
    decay, no = [], []
    for n, p in model.named_parameters():
        if p.requires_grad:
            (no if (p.ndim <= 1 or n.endswith('.bias')) else decay).append(p)
    return [{'params': decay, 'lr': lr, 'weight_decay': 1e-4, 'name': 'decay'},
            {'params': no, 'lr': lr, 'weight_decay': 0.0, 'name': 'no_decay'},
            {'params': [a], 'lr': lr, 'weight_decay': 0.0, 'name': 'gate_logits'}]


# ------------------------------------------------------------------------------------------------------------- audio
def rich_records(man):
    from ..prior33 import views as V
    return V.cohort_streams(man, 'sparrkulee', None, 'rich_streams')


def prepare():
    """CPU, once: 16 kHz mono float32 per SparrKULee stream under STORE/audio16k, verified against rich_streams.json."""
    from ..prior33 import build_rich as BR
    t0 = time.time(); man = SRC.open_manifest(); out = STORE / 'audio16k'; out.mkdir(parents=True, exist_ok=True, mode=0o700); rec = {}
    for r in rich_records(man):
        if not r['available']:
            continue
        path = out / f'{int(r["stream"])}.npy'
        if not path.exists():
            raw = Path(r['source']).read_bytes(); assert BR._sha_bytes(raw) == r['source_sha256'], r['key']
            audio, fs = BR.read_npz_gz(raw); del raw
            assert hashlib.sha256(np.ascontiguousarray(audio).tobytes()).hexdigest() == r['audio_sha256'], r['key']
            x = BR.to16k(BR._mono(audio), fs); del audio
            assert x.dtype == np.float32 and len(x) == r['n_samples_16k'] and r['clock']['ok'], r['key']
            tmp = path.with_name(path.name + '.tmp.npy'); np.save(tmp, x); os.replace(tmp, path)
        rec[str(r['stream'])] = {'key': r['key'], 'npy_sha256': sha(path), 'n_samples_16k': r['n_samples_16k'],
                                 'source_sha256': r['source_sha256'], 'audio_sha256': r['audio_sha256']}
        print('audio16k', r['stream'], r['key'], round(time.time() - t0, 1), flush=True)
    write(OUT / 'audio16k_receipt.json', {'streams': rec, 'chain': 'prior33.build_rich read_npz_gz -> _mono -> to16k (float32)',
                                          'store': str(out), 'seconds': time.time() - t0, 'job': os.environ.get('SLURM_JOB_ID'),
                                          'created': datetime.now().astimezone().isoformat()})


class AudioBank:
    """Float32 bank (on `device`) of the 16 kHz streams the rows touch; windows(rows, off) -> [n, 12800]."""

    def __init__(self, src, rows, device):
        import torch
        rc = read(OUT / 'audio16k_receipt.json')['streams']
        need = sorted({int(src.idx.stream[p]) for p in src.seg['presentation'][np.unique(rows)]})
        self.off, chunks, n = {}, [], 0
        for st in need:
            x = np.load(STORE / 'audio16k' / f'{st}.npy', mmap_mode='r'); assert len(x) == rc[str(st)]['n_samples_16k']
            self.off[st] = n; n += len(x); chunks.append(torch.from_numpy(np.asarray(x, np.float32)))
        self.x = torch.cat(chunks).to(device); self.src = src; self.dev = device
        self.ar = torch.arange(AUD_N, device=device) + int(AUD_WIN_S[0] * FS_AUD)

    @property
    def nbytes(self):
        return int(self.x.numel() * 4)

    def windows(self, rows, off):
        import torch
        from ..prior33 import contract as PC
        seg = self.src.seg; st = self.src.idx.stream[seg['presentation'][rows]]
        assert np.all(PER64 * off + int(AUD_WIN_S[0] * FS_AUD) >= 0) and np.all(PER64 * off + self.ar[-1].item() < PER64 * PC.SEG_STEP)
        base = np.array([self.off[int(s)] for s in st]) + PER64 * (seg['s'][rows] + off)
        return self.x[torch.as_tensor(base, device=self.dev)[:, None] + self.ar]


# ------------------------------------------------------------------------------------------------------------- plan
def make_plan():
    for seed in all_seeds():
        sp, pp = stream_file(seed); assert sha(sp) == read(pp)['stream_sha256'], seed
    sel1 = read(R2.R1_SOURCE / 'selection.json')
    cal = []
    for lr in SRC.CAL_LRS:
        body = {'stage': 'calibration', 'arm': 'CALRA', 'lr': lr, 'updates': SRC.CAL_STEPS, 'seed': 3401}
        cal.append({**body, 'id': 'W5C_' + digest(body, 16)})
    body = {'version': 'PAPER_W5_CALRA_v1', 'table6_row': TABLE6_ROW, 'rows': cal, 'sources': sources(), 'arms': list(ARMS),
            'arm_seeds': {k: list(v) for k, v in ARM_SEEDS.items()}, 'frozen_arms': list(FROZEN_ARMS),
            'streams': {str(s): sha(stream_file(s)[0]) for s in all_seeds()}, 'panels_sha256': sha(R1_STORE / 'panels.npz'),
            'r1_selection_sha256': sha(R2.R1_SOURCE / 'selection.json'), 'r1_common_lr': sel1['choice']['TCS']['lr'],
            'settings': {'d': D, 'temperature_fixed': TEMP, 'batch': BLOCK, 'audio_window_s': list(AUD_WIN_S), 'audio_samples': AUD_N,
                         'w2v_revision': XM.W2V_REV, 'w2v_mask_time_min_masks': W2V_MIN_MASKS,
                         'w2v_mask_time_min_masks_released': W2V_MIN_MASKS_RELEASED, 'mindmix_commit': XM.MM_COMMIT,
                         'optimizer': 'source.param_groups AdamW wd 1e-4, cosine, clip 5', 'updates': SRC.PROD_STEPS,
                         'snapshots': list(SRC.PROD_SNAPSHOTS), 'calibration_lrs': list(SRC.CAL_LRS), 'calibration_updates': SRC.CAL_STEPS,
                         'audit_seed': AUDIT_SEED, 'audit_updates': AUDIT_UPDATES, 'dtu_anchor_every': DTU_EVERY},
            'departures_from_mindmix': DEPARTURES}
    path = OUT / 'plan.json'
    if path.exists():
        old = read(path); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        OUT.mkdir(parents=True, exist_ok=True, mode=0o700); write(path, {**body, 'created': datetime.now().astimezone().isoformat()}); path.chmod(0o444)
    print('W5 plan', sha(path), flush=True)


def select():
    """CALRA LR = lower dev ridge-probe mean (exact tie -> 1e-4; source.select rule); PROJ_NCE inherits."""
    plan = read(OUT / 'plan.json'); probe = {r['lr']: read(OUT / 'calibration' / 'units' / f'{r["id"]}.json')['selection_probe'] for r in plan['rows']}
    finite = all(math.isfinite(v['mean']) for v in probe.values())
    lr = min(SRC.CAL_LRS, key=lambda x: (probe[x]['mean'], x)) if finite else 1e-4
    choice = {'CALRA': {'lr': lr, 'probe': {str(k): v for k, v in probe.items()}, 'status': 'selected' if finite else 'uninformative_selection'},
              'PROJ_NCE': {'lr': lr, 'status': 'inherits_CALRA'}}
    for arm in ARMS:
        for seed in ARM_SEEDS[arm]:
            base = seed_base(arm, seed)
            body = {'stage': 'production', 'arm': arm, 'lr': lr, 'updates': SRC.PROD_STEPS, 'seed': seed}
            rows = [{**body, 'id': 'W5P_' + digest(body, 16)}]
            if (base / 'selection.json').exists():
                assert read(base / 'selection.json')['production_rows'] == rows
                continue
            write(base / 'plan.json', {'version': 'PAPER_W5_SEED_STUB_v1', 'arm': arm, 'seed': seed, 'w5_plan_sha256': sha(OUT / 'plan.json')})
            write(base / 'selection.json', {'version': 'PAPER_W5_SELECTION_v1', 'plan_sha256': sha(OUT / 'plan.json'), 'production_rows': rows,
                                            'choice': choice, 'table6_row': TABLE6_ROW if arm == 'CALRA' else None,
                                            'created': datetime.now().astimezone().isoformat()})


def all_rows():
    plan = read(OUT / 'plan.json'); rows = [dict(r, base=str(OUT / 'calibration')) for r in plan['rows']]
    for arm in ARMS:
        for seed in ARM_SEEDS[arm]:
            p = seed_base(arm, seed) / 'selection.json'
            if p.exists():
                rows += [dict(r, base=str(seed_base(arm, seed))) for r in read(p)['production_rows']]
    return rows


# ------------------------------------------------------------------------------------------------------------- one fit
def panel_probe(src, model, P):
    """source.ridge_probe on raw backbone tokens [n, 3*C*200] of the fixed fit/dev panels (= source.panel_features input)."""
    import torch
    def feats(rows, off):
        T, R = [], {v: [] for v in ('env', 'ss', 'sc')}
        for k in range(0, len(rows), 128):
            r, o = rows[k:k + 128], off[k:k + 128]
            T.append(model.tb.tokens(src.crops(r, o)).flatten(1).float().cpu()); _, raw = src.audio(r, o)
            for v in R:
                R[v].append(raw[v].double().cpu())
        return torch.cat(T), {v: torch.cat(x) for v, x in R.items()}
    model.eval()
    with torch.no_grad():
        Tf, Rf = feats(P['fit_rows'], P['fit_off']); Td, Rd = feats(P['dev_rows'], P['dev_off'])
    return SRC.ridge_probe(Tf, Rf, Td, Rd)


def run_unit(row, probe=False):
    import torch
    t0 = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']; base = Path(row['base'])
    stream = SRC.load_arrays(stream_file(row['seed'])[0]); P = SRC.load_arrays(R1_STORE / 'panels.npz'); man = SRC.open_manifest()
    steps = row['updates']
    need = np.r_[stream['rows'][:steps, :, 1].reshape(-1), P['fit_rows'], P['dev_rows']]
    src = SRC.Source(man, need, dev); bank = AudioBank(src, need, dev)
    model, a = build(row['arm'], row['seed']); model.to(dev); a = a.detach().to(dev).requires_grad_(True)
    opt = torch.optim.AdamW(param_groups(model, a, row['lr']), lr=row['lr']); sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)
    params = [p for g in opt.param_groups for p in g['params']]
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    out = OUT / 'probes' / job if probe else base
    snaps = (0, steps) if (probe or row['stage'] == 'calibration') else SRC.PROD_SNAPSHOTS
    log, ckpts, begin, resume, times = [], {}, 0, dest / 'resume.pt', []

    def save(step):
        path = dest / f'update{step}.pt'
        body = {'backbone': model.tb.bb.state_dict(), 'a': a.detach().cpu(), 'heads': {}, 'eeg_proj': model.eeg_proj.state_dict(),
                'step': step, 'row': row, 'plan_sha256': sha(OUT / 'plan.json'), 'probe': probe}
        if step == steps:                                            # full model only at the transfer step (audit input)
            body['model'] = model.state_dict()
        SRC.B_atomic(path, body); ckpts[str(step)] = {'path': str(path), 'sha256': sha(path)}

    if resume.exists():
        st = torch.load(resume, map_location=dev, weights_only=False)
        assert st['row'] == row and st['plan_sha256'] == sha(OUT / 'plan.json')
        model.load_state_dict(st['model']); a.data.copy_(st['a']); opt.load_state_dict(st['opt']); sched.load_state_dict(st['sched'])
        begin, log, ckpts = st['step'], st['log'], st['ckpts']
        torch.set_rng_state(st['torch_rng'].cpu()); torch.cuda.set_rng_state(st['cuda_rng'].cpu())
    else:
        save(0)
    setup = time.time() - t0
    for u in range(begin, steps):
        tu = time.time(); model.train(); total = 0.0; parts = []
        for j in range(2):
            Q, oQ = stream['rows'][u, j, 1], stream['off'][u, j, 1]
            e = model.eeg(src.crops(Q, oQ), a); x = model.audio(bank.windows(Q, oQ))
            loss = model.loss(e, x); total = total + loss / 2; parts.append(float(loss.detach()))
        opt.zero_grad(set_to_none=True); total.backward()
        gn = torch.nn.utils.clip_grad_norm_(params, 5.0)
        if not torch.isfinite(total) or not torch.isfinite(gn):
            raise FloatingPointError(f'nonfinite loss or gradient at update {u}')
        if u == begin == 0:
            miss = [n for n, p in model.tb.bb.named_parameters() if n not in SRC.UNUSED_WITHOUT_MASK and (p.grad is None or not bool(torch.any(p.grad != 0)))]
            assert not miss and a.grad is not None, f'backbone tensors without gradient: {miss[:5]}'
        opt.step(); sched.step(); times.append(time.time() - tu)
        if (u + 1) % 25 == 0 or u < 3 or probe:
            log.append({'update': u + 1, 'loss': float(total.detach()), 'person_loss': parts, 'grad_norm': float(gn),
                        'lr': float(sched.get_last_lr()[0]), 'a': a.detach().cpu().tolist()})
        if (u + 1) in snaps:
            save(u + 1)
        if (u + 1) % 100 == 0 and not probe:
            SRC.B_atomic(resume, {'model': model.state_dict(), 'a': a.detach(), 'opt': opt.state_dict(), 'sched': sched.state_dict(),
                                  'step': u + 1, 'log': log, 'ckpts': ckpts, 'row': row, 'plan_sha256': sha(OUT / 'plan.json'),
                                  'torch_rng': torch.get_rng_state(), 'cuda_rng': torch.cuda.get_rng_state()})
        if (u + 1) % 500 == 0:
            print(row['id'], row['arm'], 'update', u + 1, round(float(total.detach()), 5), round(time.time() - t0, 1), flush=True)
    tp = time.time(); sel_probe = panel_probe(src, model, P); probe_s = time.time() - tp
    tt = np.array(times[5:] if len(times) > 10 else times)
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'updates': steps, 'log': log,
           'checkpoints': ckpts, 'final_checkpoint': ckpts[str(steps)]['path'], 'final_checkpoint_sha256': ckpts[str(steps)]['sha256'],
           'selection_probe': sel_probe, 'final_a': a.detach().cpu().tolist(), 'final_q_prior': torch.softmax(a.detach(), 0).cpu().tolist(),
           'device': torch.cuda.get_device_name(0), 'job': job, 'seconds': time.time() - t0,
           'timing': {'setup_s': setup, 'updates_timed': len(times), 'update_s_median': float(np.median(tt)) if len(tt) else None,
                      'update_s_p90': float(np.quantile(tt, .9)) if len(tt) else None, 'panel_probe_s': probe_s},
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'peak_rss_gb': peak_rss_gb(),
           'bank_nbytes': {'eeg': int(src.nbytes), 'audio': bank.nbytes}}
    write(out / 'units' / f'{row["id"]}.json', rec)
    if resume.exists() and not probe:
        resume.unlink()
    print(row['id'], 'complete', row['arm'], row['lr'], round(rec['seconds'], 1), sel_probe['mean'], flush=True)
    return rec


# ------------------------------------------------------------------------------------------------------------- audit
def noise_like(span, gen):
    """Gaussian [n, C, L] with each anchor-channel's mean and SD over its span."""
    import torch
    z = torch.randn(span.shape, generator=gen).to(span.device)
    return span.mean(-1, keepdim=True) + span.std(-1, keepdim=True) * z


def block_eval(model, a, crops, crops_n, x, xw):
    """One person-homogeneous batch. x / xw: pre-fusion audio embeddings of the correct / wrong (ignored) streams."""
    import torch
    import torch.nn.functional as F
    e = model.eeg(crops, a); en = model.eeg(crops_n, a); ar = torch.arange(len(e), device=e.device); r = {}
    for name, (ee, xx) in {'real_correct': (e, x), 'real_wrong': (e, xw), 'noise_correct': (en, x)}.items():
        S = model.clip.get_scores(*model.fuse(ee, xx))
        r[f'{name}_cliploss'] = F.cross_entropy(S, ar); r[f'{name}_top1'] = (S.argmax(1) == ar).float().mean()
    S = model.clip.get_scores(e, x); r['prefusion_cliploss'] = F.cross_entropy(S, ar); r['prefusion_top1'] = (S.argmax(1) == ar).float().mean()
    for tag, ee in (('real', e), ('noise', en)):
        s11, s21, s22, s12 = model.s(ee, x, x), model.s(ee, x, xw), model.s(ee, xw, xw), model.s(ee, xw, x)
        r[f'blind_{tag}'] = 0.5 * ((s11 - s21) - (s22 - s12))                     # > 0: correct stream preferred
        for slot, (t, c) in (('correct', (x, xw)), ('wrong', (xw, x))):             # official _evaluate_contrastive: pA > pB
            fe, ft = model.fuse(ee, t); _, fc = model.fuse(ee, c)
            pA = model.clip.get_probabilities(fe, ft).diagonal(); pB = model.clip.get_probabilities(fe, fc).diagonal()
            r[f'official_{tag}_target_{slot}'] = (pA > pB).float()
    f, g = model.fuse(e, x); fn, _ = model.fuse(en, x)
    r.update(emb_eeg=e, emb_eeg_noise=en, emb_fused=f, emb_fused_noise=fn, emb_audio=x, emb_audio_wrong=xw, emb_aligned_audio=g)
    return {k: v.double().cpu().numpy() for k, v in r.items()}


def audit_source(model, a, dev, n_updates=AUDIT_UPDATES, max_blocks=None):
    """Dev audit stream (source.make_stream on the dev pool; people with >= 3 families x 22 segments); support AND query blocks."""
    import torch
    t0 = time.time(); man = SRC.open_manifest(); split, _ = SRC.pool(man); people, _ = SRC.eligible_people(split['dev'])
    st = SRC.make_stream(split['dev'], people, n_updates, seed=AUDIT_SEED); SRC.check_stream(man, st)
    src = SRC.Source(man, st['rows'].reshape(-1), dev); bank = AudioBank(src, st['rows'].reshape(-1), dev)
    gen = torch.Generator().manual_seed(AUDIT_SEED); out, times = [], []; load = time.time() - t0
    for u in range(len(st['rows'])):
        for j in range(2):
            for k in range(2):
                if max_blocks is not None and len(out) >= max_blocks:
                    return out, {'load_s': load, 'block_s': times}
                tb = time.time()
                r, o, w = st['rows'][u, j, k], st['off'][u, j, k], st['wrong'][u, j, k]
                c = src.crops(r, o); span = torch.cat([c[0], c[2]], -1)              # source.crops: [0,25) + [25,51) = 51 samples
                n = noise_like(span, gen); cn = [n[..., 0:25], n[..., 12:38], n[..., 25:51]]
                x = model.audio(bank.windows(r, o)); xw = x[torch.as_tensor(w, device=dev)]
                res = block_eval(model, a, c, cn, x, xw)
                _, raw = src.audio(r, o)
                res.update({f'target_{v}': raw[v].double().cpu().numpy().reshape(len(r), -1) for v in raw})
                res.update(person=np.repeat(str(st['people'][st['who'][u, j]]), len(r)), segment=np.asarray(r), block=np.repeat(len(out), len(r)))
                out.append(res); times.append(time.time() - tb)
    return out, {'load_s': load, 'block_s': times}


def audit_dtu(model, a, cf, dev, max_blocks=None):
    """frozen.py cs geometry (16 anchors per 5 s cs segment; every DTU_EVERY-th used), role=test segments of non-dev people;
    batches = one anchor offset x up to 32 consecutive segments of one person; attended / ignored 16 kHz audio from the
    aln42 binding (XM.cohort_index / XM.audio_cache: target wav sample 0 = target onset, masker at maskeronset)."""
    import torch
    from auditory_alignment_v2.run import load_cohort
    from ..aln41 import timebank as TB
    t0 = time.time(); ix = XM.cohort_index(cf)
    b = {'experiment_id': f'W5_cf{cf}', 'family_id': 'ALN41', 'dataset': 'dtu', 'subject_fold': 0, 'content_fold': cf, 'seed': SRC.SEED,
         'spec': ix['spec']}
    coh = load_cohort(b); segs = coh.segments; parts = coh.participants
    cs = [i for i, s in enumerate(segs) if s['kind'] == 'cs' and s.get('s0_ign') is not None and s['role'] in ('fit', 'es', 'test')
          and not parts[s['p']].get('test_only')]
    assert np.array_equal(np.array([segs[i]['e0'] for i in cs]), ix['arrays']['cs_e0'])
    assert coh.fs == XM.FS_COH
    E = torch.as_tensor(coh.eeg, dtype=torch.float32); lay = TB.layout(coh.fs); lo, hi = lay[0][0], lay[2][1]
    offs = np.rint(np.linspace(0.4, 4.15, FZ.CS_ANCHORS) * coh.fs).astype(int)[::DTU_EVERY]
    test = [j for j, i in enumerate(cs) if segs[i]['role'] == 'test' and ix['arrays']['cs_person'][j] not in ix['dev']]
    gen = torch.Generator().manual_seed(AUDIT_SEED + 1 + cf); out, times, wav = [], [], {}
    aud = lambda h_, p_: wav[h_] if h_ in wav else wav.setdefault(h_, XM.audio_cache(h_, p_))
    by_person = {}
    for j in test:
        by_person.setdefault(ix['arrays']['cs_person'][j], []).append(j)
    load = time.time() - t0
    info = {'load_s': load, 'block_s': times, 'n_test_segments': len(test), 'n_people': len(by_person),
            'n_blocks_full': len(offs) * sum(math.ceil(len(js) / BLOCK) for js in by_person.values())}
    for p, js in sorted(by_person.items()):
        for o in offs:
            for k in range(0, len(js), BLOCK):
                if max_blocks is not None and len(out) >= max_blocks:
                    return out, info
                tb = time.time()
                jj = js[k:k + BLOCK]; anc = torch.as_tensor([int(e0) + int(o) for e0 in ix['arrays']['cs_e0'][jj]])
                span = E[:, anc[:, None] + torch.arange(lo, hi)[None]].permute(1, 0, 2).to(dev)
                c = [span[..., s - lo:t - lo] for s, t, _ in lay]; n = noise_like(span, gen); cn = [n[..., s - lo:t - lo] for s, t, _ in lay]
                att, ign = [], []
                for jx in jj:
                    g = ix['geo'][jx]; tau = g['st'] / XM.FS_COH + o / coh.fs + AUD_WIN_S[0]
                    ia, im = int(round(tau * FS_AUD)), int(round((tau - g['moff']) * FS_AUD)); assert ia >= 0 and im >= 0
                    A_, M_ = aud(g['th'], g['tpath'])[ia:ia + AUD_N], aud(g['mh'], g['mpath'])[im:im + AUD_N]
                    assert len(A_) == len(M_) == AUD_N; att.append(A_); ign.append(M_)
                x = model.audio(torch.as_tensor(np.stack(att), device=dev)); xw = model.audio(torch.as_tensor(np.stack(ign), device=dev))
                res = block_eval(model, a, c, cn, x, xw)
                res.update(person=np.repeat(p, len(jj)), segment=np.asarray(jj), offset=np.repeat(int(o), len(jj)),
                           content_fold=np.repeat(cf, len(jj)), block=np.repeat(len(out), len(jj)))
                out.append(res); times.append(time.time() - tb)
    return out, info


def run_audit(row, probe=False):
    import torch
    t0 = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']
    unit = read(Path(row['base']) / 'units' / f'{row["id"]}.json'); ck = unit['final_checkpoint']; assert sha(ck) == unit['final_checkpoint_sha256']
    st = torch.load(ck, map_location='cpu', weights_only=False)
    blocks, timing = {}, {}
    mb = SMOKE_BLOCKS if probe else None
    for name, fs in (('source', 64), ('dtu', XM.FS_COH)):
        model, _ = build(row['arm'], row['seed'], fs_native=fs); model.load_state_dict(st['model']); model.to(dev).eval()
        a = st['a'].to(dev)
        with torch.no_grad():
            if name == 'source':
                blocks[name], timing[name] = audit_source(model, a, dev, 1 if probe else AUDIT_UPDATES, mb)
            else:
                blocks[name], timing[name] = [], {}
                for cf in ((0,) if probe else (0, 1)):
                    bl, tm = audit_dtu(model, a, cf, dev, mb); blocks[name] += bl; timing[name][f'cf{cf}'] = tm
        del model; torch.cuda.empty_cache()
    dest = (STORE / 'probes' / job if probe else STORE / 'audit') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name, bl in blocks.items():          # block scalars -> blk_<metric> [n_blocks]; anchor arrays concatenated
        for i, b in enumerate(bl):           # one block numbering per domain (DTU cf 0 and 1 are concatenated)
            b['block'] = np.repeat(i, len(b['block']))
        arr = {f'blk_{k}': np.array([b[k] for b in bl]) for k in bl[0] if np.ndim(bl[0][k]) == 0}
        arr.update({k: np.concatenate([b[k] for b in bl]) for k in bl[0] if np.ndim(bl[0][k]) > 0})
        arr['blk_n'] = np.array([len(b['block']) for b in bl]); np.savez_compressed(dest / f'{name}.npz', **arr)
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'unit_checkpoint_sha256': unit['final_checkpoint_sha256'],
           'dest': str(dest), 'npz_sha256': {n: sha(dest / f'{n}.npz') for n in blocks}, 'n_blocks': {n: len(b) for n, b in blocks.items()},
           'timing': timing, 'seconds': time.time() - t0, 'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20,
           'peak_rss_gb': peak_rss_gb(), 'device': torch.cuda.get_device_name(0), 'job': job}
    write((OUT / 'probes' / job if probe else OUT) / 'audit' / f'{row["id"]}.json', rec)
    print(row['id'], 'audit complete', rec['n_blocks'], round(rec['seconds'], 1), flush=True)
    return rec


# ------------------------------------------------------------------------------------------------------------- frozen readouts
@contextlib.contextmanager
def frozen_ctx(arm, seed):
    """aln41.r2.seeded pattern: frozen.py / readout.py read SRC.BASE/selection.json + units and write FZ.BASE / RO.BASE."""
    assert arm in FROZEN_ARMS and seed in ARM_SEEDS[arm]
    saved = [(m, k, getattr(m, k)) for m, ks in ((SRC, ('SEED', 'BASE', 'STORE')), (FZ, ('BASE', 'STORE', 'ARMS')), (RO, ('BASE',))) for k in ks]
    try:
        SRC.SEED, SRC.BASE, SRC.STORE = seed, seed_base(arm, seed), STORE / arm / f'seed{seed}' / 'source_v1'
        FZ.BASE, FZ.STORE, FZ.ARMS = OUT / arm / f'seed{seed}' / 'frozen_v1', STORE / arm / f'seed{seed}' / 'frozen_v1', (arm,)
        RO.BASE = OUT / arm / f'seed{seed}' / 'readout_v1'
        yield
    finally:
        for m, k, v in saved:
            setattr(m, k, v)


# ------------------------------------------------------------------------------------------------------------- fleet
def receipts():
    out = {'pass': [], 'other': []}
    if (OUT / 'plan.json').exists():
        ps = sha(OUT / 'plan.json')
        for p in sorted((OUT / 'probes').glob('*/receipt.json')):
            r = read(p)
            if r.get('plan_sha256') == ps:
                out['pass' if r.get('status') == 'pass' else 'other'].append(p)
    return out


def pending():
    """Ordered GPU work: ('unit', row) | ('select', None) | ('audit', row) | ('frozen', (arm, seed, frozen_row)); and a failure flag."""
    rows = all_rows(); items = []
    unit_done = lambda r: (Path(r['base']) / 'units' / f'{r["id"]}.json').exists()
    audit_done = lambda r: (OUT / 'audit' / f'{r["id"]}.json').exists()
    bad = any((Path(r['base']) / 'units' / f'{r["id"]}.FAILED.json').exists() or (OUT / 'audit' / f'{r["id"]}.FAILED.json').exists() for r in rows)
    cal = [r for r in rows if r['stage'] == 'calibration']
    items += [('unit', r) for r in cal if not unit_done(r)]
    if all(unit_done(r) for r in cal) and not all((seed_base(a, s) / 'selection.json').exists() for a in ARMS for s in ARM_SEEDS[a]):
        items.append(('select', None))
    for r in rows:
        if r['stage'] == 'production':
            if not unit_done(r):
                items.append(('unit', r))
            elif not audit_done(r):
                items.append(('audit', r))
    for arm in FROZEN_ARMS:
        for seed in ARM_SEEDS[arm]:
            with frozen_ctx(arm, seed):
                if (FZ.BASE / 'plan.json').exists():
                    left = [fr for fr in read(FZ.BASE / 'plan.json')['rows'] if not (FZ.BASE / 'units' / f'{fr["id"]}.json').exists()]
                    bad |= any((FZ.BASE / 'units' / f'{fr["id"]}.FAILED.json').exists() for fr in left)
                    items += [('frozen', (arm, seed, fr)) for fr in left if FZ.ready(fr)]
    return items, bad


def fleet_status():
    n_prod = sum(len(v) for v in ARM_SEEDS.values()); n_frozen = 5 * sum(len(ARM_SEEDS[a]) for a in FROZEN_ARMS)
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': len(SRC.CAL_LRS) + 2 * n_prod + n_frozen,
          'slots': 1, 'initial': [], 'submit': []}
    if not (OUT / 'plan.json').exists():
        return st
    if not (OUT / 'audio16k_receipt.json').exists():
        return {**st, 'state': 'waiting_audio_cache'}
    items, failed = pending()
    frozen_planned = all((OUT / a / f'seed{s}' / 'frozen_v1' / 'plan.json').exists() for a in FROZEN_ARMS for s in ARM_SEEDS[a])
    st['remaining'] = len(items) if frozen_planned else max(len(items), st['remaining'])
    if failed:
        return {**st, 'state': 'failed_unit_review'}
    if not items and frozen_planned:
        return {**st, 'state': 'complete'}
    rec = receipts()
    if not rec['pass']:
        return {**st, 'state': 'engineering_probe_failed'} if rec['other'] else {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
    return {**st, 'state': 'ready', 'ready': len(items), 'slots': 2, 'submit': [SBATCH, '--worker']}


def worker():
    """Claim and run ONE ready work item (flock; own subprocess; FAILED marker on error)."""
    assert receipts()['pass'], 'no passing smoke'
    items, failed = pending(); assert not failed, 'failed unit under review'
    for kind, obj in items:
        if kind == 'select':
            lock = OUT / 'claims' / 'select.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with lock.open('a+') as h:
                fcntl.flock(h, fcntl.LOCK_EX); select()
                for arm in FROZEN_ARMS:
                    for seed in ARM_SEEDS[arm]:
                        with frozen_ctx(arm, seed):
                            FZ.make_plan()
            return
        rid = obj[2]['id'] if kind == 'frozen' else obj['id']
        lock = OUT / 'claims' / f'{rid}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            args = ['--frozen', obj[0], str(obj[1]), rid] if kind == 'frozen' else [f'--{kind}', rid]
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, *args]).returncode
            if rc < 0:
                raise SystemExit(f'unit ended by signal {-rc}')
            if rc:
                fail = {'unit': lambda: Path(obj['base']) / 'units', 'audit': lambda: OUT / 'audit',
                        'frozen': lambda: OUT / obj[0] / f'seed{obj[1]}' / 'frozen_v1' / 'units'}[kind]()
                write(fail / f'{rid}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc, 'kind': kind})
                raise RuntimeError(f'W5 {kind} {rid} failed')
            return


def smoke():
    """Engineering only (no held-out score): CALRA 50 real updates (timing, peak memory), PROJ_NCE 3; checkpoint reload through
    frozen.backbone; audit on 2 blocks per domain (source dev, DTU cf0); GPU-hour estimate from the measured timings."""
    import torch
    job = os.environ['SLURM_JOB_ID']; rec = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
    try:
        for arm in ARMS:
            row = {'stage': 'calibration', 'arm': arm, 'lr': 1e-4, 'updates': SMOKE_UPDATES[arm], 'seed': 3401, 'id': f'W5_SMOKE_{arm}',
                   'base': str(OUT / 'probes' / job)}
            u = run_unit(row, probe=True); au = run_audit(row, probe=True)
            st = torch.load(u['final_checkpoint'], map_location='cpu', weights_only=False)
            net = {k[len('net.'):]: v for k, v in st['backbone'].items() if k.startswith('net.')}
            bb = FZ.backbone('dtu', net, torch.device('cuda'))              # frozen.py's strict donor load
            assert bb.init_loaded['missing'] == [] and bb.init_loaded['unexpected'] == []
            m2, _ = build(arm, 3401); m2.load_state_dict(st['model'], strict=True)
            assert all(torch.equal(m2.tb.bb.state_dict()[k].cpu(), v.cpu()) for k, v in st['backbone'].items())
            rec['units'].append({'arm': arm, 'updates': u['updates'], 'losses': [x['loss'] for x in u['log']], 'timing': u['timing'],
                                 'seconds': u['seconds'], 'gpu_peak_mb': u['gpu_peak_mb'], 'peak_rss_gb': u['peak_rss_gb'], 'device': u['device'],
                                 'bank_nbytes': u['bank_nbytes'], 'frozen_reload': bb.init_loaded,
                                 'audit': {k: au[k] for k in ('n_blocks', 'timing', 'seconds', 'gpu_peak_mb', 'peak_rss_gb', 'npz_sha256')}})
        c = next(x for x in rec['units'] if x['arm'] == 'CALRA'); t = c['timing']
        fit_h = (t['setup_s'] + SRC.PROD_STEPS * t['update_s_median'] + t['panel_probe_s']) / 3600
        cal_h = 2 * (t['setup_s'] + SRC.CAL_STEPS * t['update_s_median'] + t['panel_probe_s']) / 3600
        sb = c['audit']['timing']['source']; db = c['audit']['timing']['dtu']['cf0']
        audit_h = (sb['load_s'] + 4 * AUDIT_UPDATES * float(np.median(sb['block_s'])) + 2 * db['load_s']    # cf1 assumed like cf0
                   + 2 * db['n_blocks_full'] * float(np.median(db['block_s'])) + 2 * 60) / 3600
        n_cal = sum(len(ARM_SEEDS[a]) for a in ARMS)
        rec['estimate_gpu_h'] = {'device': c['device'], 'per_fit_10k': fit_h, 'calibration_total': cal_h, 'per_audit': audit_h,
                                 'frozen_per_arm_seed_R1_measured': 0.33,
                                 'total': cal_h + n_cal * (fit_h + audit_h) + 0.33 * sum(len(ARM_SEEDS[a]) for a in FROZEN_ARMS)}
        rec['status'] = 'pass'
    except BaseException:
        rec.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', rec)


def summarize():
    """CPU. Per arm x seed x domain, person means of: block ClipLoss / in-batch top-1 (chance 1/n) for real+correct,
    real+wrong, noise+correct, pre-fusion; blind accuracy mean(m > 0) (ties 1/2) for real and noise EEG; privileged-slot
    'target wins' rate with the correct and with the wrong stream in the target slot. CS (paper.cs_atlas = cs_qmi_reference
    formula): per block (distinct segments, roll null over the block), excess dependence of {fused, fused_noise, eeg,
    eeg_noise} on {audio (correct), audio_wrong}; sigma = cs_atlas.sigma_rule per space on the domain's real-EEG rows (noise
    reps reuse the real sigma, as paper.mindmix_audit)."""
    import json
    from . import cs_atlas as CA
    rng = np.random.default_rng(CA.RNG_SEED); res = {}
    for r in all_rows():
        p = OUT / 'audit' / f'{r["id"]}.json'
        if r['stage'] != 'production' or not p.exists():
            continue
        rec = read(p)
        for dom in ('source', 'dtu'):
            assert sha(Path(rec['dest']) / f'{dom}.npz') == rec['npz_sha256'][dom]
            with np.load(Path(rec['dest']) / f'{dom}.npz') as z:
                Z = {k: z[k] for k in z.files}
            cell = res.setdefault(f'{r["arm"]}/seed{r["seed"]}/{dom}', {}); per = {}
            bp = np.array([Z['person'][Z['block'] == b][0] for b in range(len(Z['blk_n']))])
            sig_u = {k: CA.sigma_rule(Z[f'emb_{k}'], rng) for k in ('fused', 'eeg')}; sig_u.update(fused_noise=sig_u['fused'], eeg_noise=sig_u['eeg'])
            sig_s = {'audio': CA.sigma_rule(Z['emb_audio'], rng)}; sig_s['audio_wrong'] = sig_s['audio']
            for b in range(len(Z['blk_n'])):
                d = per.setdefault(bp[b], {}); ix = np.flatnonzero(Z['block'] == b)
                for k in [k for k in Z if k.startswith('blk_') and k.endswith(('_cliploss', '_top1'))]:
                    d.setdefault(k[4:], []).append(float(Z[k][b]))
                d.setdefault('chance_top1', []).append(1.0 / Z['blk_n'][b])
                for tag in ('real', 'noise'):
                    m = Z[f'blind_{tag}'][ix]; d.setdefault(f'blind_acc_{tag}', []).append(float(np.mean((m > 0) + 0.5 * (m == 0))))
                    for slot in ('correct', 'wrong'):
                        d.setdefault(f'official_{tag}_target_{slot}_wins', []).append(float(Z[f'official_{tag}_target_{slot}'][ix].mean()))
                if len(ix) >= 3:
                    reps = {k: Z[f'emb_{k}'][ix] for k in ('fused', 'fused_noise', 'eeg', 'eeg_noise')}
                    tg = {'audio': Z['emb_audio'][ix], 'audio_wrong': Z['emb_audio_wrong'][ix]}
                    for rn, t, v in CA.person_cells(reps, tg, np.arange(len(ix)), sig_u, sig_s):
                        d.setdefault(f'cs_excess/{rn}/{t}', []).append(v['excess'])
            people = {p_: {k: float(np.mean(v)) for k, v in d.items()} for p_, d in per.items()}
            for k in sorted({k for d in people.values() for k in d}):
                cell[k] = {'person_mean': float(np.mean([d[k] for d in people.values() if k in d])), 'n_people': sum(k in d for d in people.values())}
    out = Path(core.REPO) / 'results/auditory_alignment_v3/paper/calra_cbramod'; out.mkdir(parents=True, exist_ok=True)
    (out / 'W5_AUDIT.json').write_text(json.dumps({'plan_sha256': sha(OUT / 'plan.json'), 'cs_atlas_sha256': sha(CA.__file__),
                                                   'cells': res, 'definitions': summarize.__doc__}, indent=1) + '\n')


def main():
    ap = argparse.ArgumentParser()
    for flag in ('make_plan', 'prepare', 'smoke', 'worker', 'summarize'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--audit')
    ap.add_argument('--frozen', nargs=3, metavar=('ARM', 'SEED', 'ID')); ap.add_argument('--readout', nargs=2, metavar=('ARM', 'SEED'))
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    if a.prepare:
        prepare(); return
    plan = read(OUT / 'plan.json'); assert plan['sources'] == sources(), 'frozen source drift'
    if a.unit or a.audit:
        row = next(r for r in all_rows() if r['id'] == (a.unit or a.audit))
        (run_unit if a.unit else run_audit)(row); return
    if a.frozen:
        with frozen_ctx(a.frozen[0], int(a.frozen[1])):
            fplan = read(FZ.BASE / 'plan.json'); FZ.verify(fplan)
            FZ.run_unit(next(r for r in fplan['rows'] if r['id'] == a.frozen[2]), fplan)
        return
    if a.readout:                                    # CPU: aln41.readout over this arm x seed's frozen units, unchanged
        with frozen_ctx(a.readout[0], int(a.readout[1])):
            sys.argv = sys.argv[:1]; RO.main()
        return
    if a.smoke:
        smoke(); return
    if a.summarize:
        os.umask(0o022); summarize(); return
    assert a.worker
    worker()


if __name__ == '__main__':
    main()
