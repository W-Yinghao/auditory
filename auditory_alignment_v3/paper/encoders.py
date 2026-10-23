"""Paper line (manuscript v2, 2026-10-22): REVE and the MindMix aligned EEG branch on the unchanged ALN4.1 pediatric protocol.

Rows "REVE" and "MindMix aligned EEG branch" of Tables 3-5, next to CBraMod (= ALN4.1 arm B0) and the proposed temporal CS
(= ALN4.1 arm TCS). Encoder interfaces: paper/enc_models.py. Everything else is the ALN4.1 code, called unchanged with module
attributes re-pointed inside one unit process (as paper/arms.py does):
  frozen (GPU)   private_bdf: aln41/frozen.run_unit -> private_unit (64 children, all trials, crops onset 50, timebank layout at
                 250 Hz, PCA64 shared by the 3 windows per outer fold on training children's fit trials, seed 3437 + 100 + f, age
                 features = per-child trial mean / sd of each slot's raw token vector). mff_cross_stim: the aln41/cross_stim.run_unit
                 computation (same gated records from the aln41 cross-stim plan, cross_stim.load per-record z-score, 15 PCA fits
                 transfer/refit/within, seeds 3437 + offset + fold) with its CBraMod-only shape assertion generalised to C*E.
                 q0 = uniform (as B0). Frozen encoders are seed-independent (as B0): one unit per encoder x cohort.
  FT (GPU)       aln41/private_ft_resume.run_unit unchanged (resumable): same children, outer folds, fit/ES split, child-balanced draws
                 (data RNG seed + 1000 f + 7, so batches equal B0/TCS/TNCE of the same seed and fold), three slot heads (seeded),
                 gate a = 0, AdamW, batch 64, 100 epochs, cosine, clip 5, selection = minimum equal-child ES NLL over epochs
                 0..100, test children never used. Only the model (enc_models.build_ft), the learning rate and the weight decay
                 differ. Target-validation allowance (manuscript B.4): two candidates per external encoder,
                   common     lr 1e-4, weight decay 1e-4 (the established common-backbone setting),
                   documented the encoder's documented fine-tuning lr and weight decay (CANDIDATES),
                 fitted at seed 3401 for every outer fold; per fold the candidate with the lower selected ES NLL (training children's
                 ES blocks only; exact tie -> common) is the selected fit, and seeds 3407 / 3413 run only that candidate.
  readout (CPU)  aln41/readout.private on the private frozen units (current-event AUC, history-conditional gain, strict twin).
  cross (CPU)    aln41/cross_stim.readout on the MFF frozen units (transferred / refitted / within, per-child AUC).
  age (CPU)      aln41/age.main rule (age_probe.run_probe on the private frozen age features) + raw log-variance reference.
  support (CPU)  aln41/support.run_unit on the selected FT unit of every encoder x seed x fold (delta / cal, U0 / U10x5 / U30).
Plans are frozen (0444) before any unit runs; every unit verifies the bound sources and asset hashes; GPU units need a passing
smoke receipt for the current sources and plan.

CLI (`python -m auditory_alignment_v3.paper.encoders ...`, Slurm only):
  plan (CPU) | smoke (GPU) | worker --lane {Z,R,M} [--max-units N] (GPU) | unit --stage {frozen,ft} --id ID [--probe] (GPU) |
  readout | cross-readout | age | support (CPU) | status
Fleet: fleet_status(lane) for lanes Z (frozen, c3_s35pefrz), R (REVE FT, c3_s35pereve), M (MindMix FT, c3_s35pemmix).
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import fcntl
import gc
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from ..aln41 import cross_stim as XS, frozen as FZ, private_ft as PF, private_ft_resume as PR, readout as RO, source as SRC, time_access as TA
from ..aln42 import external_mindmix as XM

ENCODERS = ('REVE', 'MINDMIX')
SEEDS = (3401, 3407, 3413)
FOLDS = (0, 1, 2, 3, 4)
COHORTS = ('private_bdf', 'mff_cross_stim')
CANDIDATES = {
    'REVE': {'common': {'lr': 1e-4, 'weight_decay': 1e-4},
             'documented': {'lr': 1e-4, 'weight_decay': 1e-2,
                            'source': 'github elouayas/reve_eeg main@06a7059a (2026-03-20; linked from brain-bzh.github.io/reve): '
                                      'src/configs/task/{bciciv2a,speech,tuev}.yaml fine_tuning.optimizer.lr 1e-4; '
                                      'src/configs/optimizer/stable_adamw.yaml weight_decay 0.01 (StableAdamW, betas [0.92, 0.999]); '
                                      'LoRA r16, two-stage LP->FT, plateau scheduler, mixup are not adopted (common full-FT recipe)'}},
    'MINDMIX': {'common': {'lr': 1e-4, 'weight_decay': 1e-4},
                'documented': {'lr': 1e-5, 'weight_decay': 1e-2,
                               'source': 'MindMix@98445f36 README CLI = universal_eeg_finetune.get_args defaults: lr 1e-5, '
                                         'weight_decay 0.01 (AdamW betas 0.9/0.95, batch 32, 50 epochs, warmup 3); only lr and '
                                         'weight decay adopted (common full-FT recipe)'}}}
SELECTION_RULE = ('per encoder x outer fold, seed 3401: choose the candidate with the lower selected_es_nll_bits (minimum equal-child '
                  'ES NLL over epochs 0..100 on the training children\'s ES blocks); exact tie -> common; seeds 3407 / 3413 run only '
                  'the chosen candidate; held-out children never enter training, selection or the candidate choice')
OUT = Path(core.OUT) / 'paper' / 'encoders_v1'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/paper/encoders_v1')
BRANCH = STORE / 'assets' / 'mindmix_eeg_branch.pt'
FZ_BASE, FZ_STORE = OUT / 'frozen_v1', STORE / 'frozen_v1'
FT_BASE, FT_STORE = OUT / 'private_ft_v1', STORE / 'private_ft_v1'
SUP_BASE = OUT / 'support_v1'
READER_EVIDENCE = Path(core.REPO) / 'archive/private/auditory5_v1/inputs/mff_probe_001/reader_evidence.json'
LANES = {'Z': ('c3_s35pefrz', 's35_paper_enc_frozen', 'slurm/aln35_paper_enc_frozen.sbatch'),
         'R': ('c3_s35pereve', 's35_paper_enc_ft_reve', 'slurm/aln35_paper_enc_reve.sbatch'),
         'M': ('c3_s35pemmix', 's35_paper_enc_ft_mindmix', 'slurm/aln35_paper_enc_mmix.sbatch')}
LANE_ENC = {'R': 'REVE', 'M': 'MINDMIX'}
LANE_SLOTS = {'Z': (2, 2), 'R': (3, 1), 'M': (2, 2)}        # (slots, units per job)
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest
DEVIATIONS = [
    'Target-validation allowance = two (lr, weight decay) candidates per external encoder; the documented candidate adopts only '
    'the documented lr and weight decay; optimizer, schedule, batch, epochs, heads and selection are the common ALN4.1 recipe.',
    'The candidate is chosen per outer fold at seed 3401 (training-side ES NLL only) and inherited by seeds 3407 / 3413 '
    '(not re-selected per seed), as the ALN4.1 R2 seeds inherit the R1 learning rate.',
    'REVE documented fine-tuning (LoRA r16 attention adapters, linear probing then unfreezing, StableAdamW, plateau scheduler, '
    'mixup, classifier dropout) is replaced by full fine-tuning of every parameter from the first step (manuscript B.4).',
    'MindMix amplitude: the shared per-record (per-child / per-MFF-record) channel z-score of the loaders, not MindMix\'s per-2-s '
    'window z-score; a z-score over each 400-ms crop would remove crop mean and scale that the other encoders see.',
    'MindMix tokens: official return_patch_tokens output (fc_norm per patch token) of both patches (80 real + 120 zero samples; '
    '200 zero samples) concatenated per channel (E = 400); the pooled embedding and eeg_proj are not used downstream, like the '
    'proposed model\'s projection heads; drop_path 0.1 of the official construction is active in training.',
    'REVE input: 80 real samples right-padded to 200 = exactly one REVE patch (patch 200, overlap 20); amplitude clip(z, -15, 15) '
    '(foundation_adapter contract), not the repository dataset scale factors (raw-unit conversions).',
    'Frozen units are seed-independent (pretrained weights, fixed PCA seeds), as for B0: one frozen unit per encoder x cohort.',
]


def master_sources():
    repo = Path(core.REPO); here = Path(__file__).parent
    files = [here / 'encoders.py', here / 'enc_models.py']
    files += [repo / 'auditory_alignment_v3/aln41' / f for f in ('frozen.py', 'timebank.py', 'time_access.py', 'readout.py', 'private_ft.py',
                                                                 'private_ft_resume.py', 'cross_stim.py', 'support.py', 'age.py',
                                                                 'age_probe.py', 'source.py', 'r2.py')]
    files += [repo / f for f in ('auditory_alignment/data.py', 'auditory_c3/c3dl/hc.py', 'auditory_c3/private_mi2.py',
                                 'auditory_alignment_v2/foundation_adapter.py', 'auditory_alignment_v2/fm_readout.py',
                                 'auditory_alignment_v3/fm_aligned.py', 'auditory_alignment_v3/aln34/private_current_time_v2.py',
                                 'auditory_alignment_v3/aln34/content_time.py', 'auditory_alignment_v3/aln35/history_interface.py',
                                 'auditory_alignment_v3/aln35/support_contract.py', 'auditory_alignment_v3/aln35/support_runtime.py',
                                 'auditory_alignment_v3/aln42/external_mindmix.py')]
    out = {str(p.relative_to(repo)): sha(p) for p in sorted(set(files))}
    out.update({f'mindmix@{XM.MM_COMMIT[:8]}/{f}': sha(XM.MM_REPO / f) for f in
                ('universal_eeg_finetune.py', 'universal_models.py', 'modeling_finetune_2.py', 'utils.py')})
    return out


# ----------------------------------------------------------------------------------------------- plans (CPU)
def frozen_rows():
    rows = []
    for enc in ENCODERS:
        for cohort in COHORTS:
            body = {'arm': enc, 'encoder': enc, 'dataset': cohort, 'content_fold': None, 'seed': None}
            rows.append({**body, 'id': 'PENCZ_' + digest(body, 16)})
    return rows


def ft_rows():
    rows = []
    for enc in ENCODERS:
        for seed in SEEDS:
            for f in FOLDS:
                for cand in ('common', 'documented'):
                    c = CANDIDATES[enc][cand]
                    body = {'arm': enc, 'encoder': enc, 'outer_fold': f, 'seed': seed, 'candidate': cand, 'lr': c['lr'],
                            'weight_decay': c['weight_decay'], 'epochs': PF.EPOCHS, 'batch': PF.BATCH,
                            'stage': 'calibration' if seed == SEEDS[0] else 'inherit'}
                    rows.append({**body, 'id': 'PENCF_' + digest(body, 16)})
    return rows


def freeze(path, body):
    path = Path(path)
    if path.exists():
        old = read(path); drift = [k for k, v in body.items() if old.get(k) != v]
        assert not drift, f'immutable plan drift {path}: {drift}'
        return old
    write(path, {**body, 'created': datetime.now().astimezone().isoformat()}); path.chmod(0o444)
    return read(path)


def make_plans():
    from . import enc_models as EM
    for d in (OUT, FZ_BASE, FT_BASE, SUP_BASE):
        d.mkdir(parents=True, exist_ok=True, mode=0o700)
    for d in (STORE, FZ_STORE, FT_STORE):
        d.mkdir(parents=True, exist_ok=True, mode=0o700)
    mm = EM.mindmix_extract(BRANCH)
    xplan = read(XS.OUT / 'plan.json')
    layouts = {}
    for r in xplan['records']:
        with np.load(XS.STAGE / 'epochs' / f'{r["record_id"]}.npz', allow_pickle=False) as z:
            layouts[r['record_id']] = (str(z['layout_hash']), int(z['n_channels']), float(z['rate_hz']), int(z['pre_samples']))
    assert {v for v in layouts.values()} == {(EM.MFF_LAYOUT_HASH, 128, 250.0, 50)}, set(layouts.values())
    geom = EM.mff_geometry_check(READER_EVIDENCE)
    assert geom['residual_max_m'] < 1e-4 and geom['nearest_bank_label_equals_name'] == 128, geom
    import auditory_alignment_v2.foundation_adapter as FA
    bindings = {'aln41_frozen_plan_sha256': sha(SRC.OUT / 'frozen_v1' / 'plan.json'),
                'aln41_private_ft_plan_sha256': sha(SRC.OUT / 'private_ft_v1' / 'plan.json'),
                'aln41_cross_stim_plan_sha256': sha(XS.OUT / 'plan.json'), 'aln41_cross_stim_decision_sha256': sha(XS.DECISION),
                'aln41_support_plan_sha256': sha(SRC.OUT / 'support_v1' / 'plan.json'),
                'aln41_age_results_sha256': sha(SRC.OUT / 'age_v1' / 'age_results.json')}
    interface = {
        'common': {'windows_ms': [list(w) for w in TA.WINDOWS_MS],
                   'crop': 'aln41/timebank.crop_inputs: native crop at 250 Hz (100 samples), crop-only FFT resampling to 200 Hz '
                           '(80 samples), zero right padding to 200; each crop an independent forward',
                   'private_bdf': 'auditory_alignment.data.load_private (64 children, 20 ch, 250 Hz, per-child z-score), onset 50',
                   'mff_cross_stim': 'aln41/cross_stim.load (gated GX records, per-record channel z-score), onset 50, 128 ch E1..E128'},
        'REVE': {'asset': 'HF brain-bzh/reve-base@dc2a075 + brain-bzh/reve-positions@befa5b5 via foundation_adapter.Backbone',
                 'amplitude': 'clip(z, -15, 15)', 'patch': 'size 200, overlap 20 (unfold step 180)', 'pad_to': 200,
                 'patches_per_crop': 1, 'token': 'final transformer output [C, 512] of the single patch', 'E': 512,
                 'channels_private': EM.channel_names('private_bdf'), 'channels_mff': 'E1..E128 (REVE bank names)',
                 'adapter_channel_aliases': FA.ALIASES},
        'MINDMIX': {'asset': 'MindMix@98445f36 best_model_loss_0.0909.pth, eeg_model.* only (strict) -> official EEGEncoder',
                    'amplitude': 'loader z-score unchanged', 'pad_to': 400, 'patches_per_crop': 2,
                    'token': 'official forward(return_patch_tokens=True) = fc_norm(patch tokens); per channel [patch0 | patch1]',
                    'E': 400, 'spatial_embedding': 'none (pos_embed forced None, no input_chans)',
                    'channels_private_in_standard_1020': True, 'channels_mff': 'E1..E128 (no channel vocabulary used)'}}
    master = {'version': 'PAPER_ENCODERS_v1', 'encoders': list(ENCODERS), 'seeds': list(SEEDS), 'folds': list(FOLDS),
              'candidates': CANDIDATES, 'selection_rule': SELECTION_RULE, 'interface': interface, 'deviations': DEVIATIONS,
              'sources': master_sources(), 'bindings': bindings,
              'assets': {'reve': EM.reve_asset_hashes(),
                         'mindmix': {'checkpoint_sha256': XM.CKPT_SHA, 'commit': XM.MM_COMMIT, 'branch_file': str(BRANCH),
                                     'branch_sha256': sha(BRANCH), 'audit': mm}},
              'mff': {'channels': EM.MFF_CHANNELS, 'layout_hash': EM.MFF_LAYOUT_HASH, 'records': len(layouts),
                      'geometry_vs_reve_bank': geom, 'reader_evidence_sha256': sha(READER_EVIDENCE)},
              'stages': {'frozen': 'frozen_v1/plan.json', 'ft': 'private_ft_v1/plan.json', 'support': 'support_v1/plan.json'},
              'store': str(STORE), 'results_seen': False}
    freeze(OUT / 'plan.json', master)
    msha = sha(OUT / 'plan.json')
    freeze(FZ_BASE / 'plan.json', {'version': 'PAPER_ENCODERS_FROZEN_v1', 'rows': frozen_rows(), 'master_plan_sha256': msha,
                                   'store': str(FZ_STORE), 'q0': 'uniform', 'cross_stim_records': xplan['records'],
                                   'pca': {'dim': FZ.PCA_DIM, 'rows_per_slot': FZ.PCA_ROWS_PER_SLOT, 'seed_private': f'{FZ.PCA_SEED} + 100 + fold',
                                           'seed_mff': {k: FZ.PCA_SEED + v for k, v in XS.PCA_OFFSET.items()}}})
    freeze(FT_BASE / 'plan.json', {'version': 'PAPER_ENCODERS_FT_v1', 'rows': ft_rows(), 'master_plan_sha256': msha, 'store': str(FT_STORE),
                                   'recipe': {'runner': 'aln41/private_ft_resume.run_unit', 'epochs': PF.EPOCHS, 'batch': PF.BATCH,
                                              'optimizer': 'AdamW default betas, no-decay for ndim<=1 / bias / a', 'schedule': 'cosine',
                                              'clip': 5.0, 'gate_init': 'a = 0', 'heads': 'SpatialPatchHead(E, 20, d32, K8, e32) + Linear(32, 2) x 3',
                                              'selection': 'min equal-child ES NLL over epochs 0..100'},
                                   'candidates': CANDIDATES, 'selection_rule': SELECTION_RULE})
    from ..aln41 import support as SU
    freeze(SUP_BASE / 'plan.json', {'version': 'PAPER_ENCODERS_SUPPORT_v1', 'master_plan_sha256': msha, 'runner': 'aln41/support.run_unit',
                                    'steps': SU.STEPS, 'lr': SU.LR, 'l2': SU.L2, 'clip': SU.CLIP, 'methods': list(SU.METHODS),
                                    'supports': ['U0', 'U10x5', 'U30'], 'base_units': 'selected FT unit per encoder x seed x fold',
                                    'support_results_seen': False})
    print('paper encoders plans', msha, sha(FZ_BASE / 'plan.json'), sha(FT_BASE / 'plan.json'), sha(SUP_BASE / 'plan.json'), flush=True)


def verify():
    master = read(OUT / 'plan.json')
    assert master['sources'] == master_sources(), 'paper encoders source drift'
    msha = sha(OUT / 'plan.json')
    for p in (FZ_BASE / 'plan.json', FT_BASE / 'plan.json'):
        assert read(p)['master_plan_sha256'] == msha, p
    assert sha(BRANCH) == master['assets']['mindmix']['branch_sha256'], 'MindMix branch file changed'
    return master


def plans_exist():
    return all(p.exists() for p in (OUT / 'plan.json', FZ_BASE / 'plan.json', FT_BASE / 'plan.json', SUP_BASE / 'plan.json'))


# ----------------------------------------------------------------------------------------------- contexts (unit processes only)
AUDITS = []


def encoder_tokens(encoder, cohort, dev):
    from . import enc_models as EM
    m = EM.make_tokens(encoder, cohort, BRANCH)
    AUDITS.append({'encoder': encoder, 'cohort': cohort, **EM.audit(m, encoder, BRANCH)})
    m = m.to(dev).eval(); m.requires_grad_(False)
    return m


def provenance(encoder):
    master = read(OUT / 'plan.json')
    return {'kind': 'external_foundation', 'encoder': encoder, 'interface': master['interface'][encoder],
            'asset': master['assets']['mindmix' if encoder == 'MINDMIX' else 'reve']}


@contextlib.contextmanager
def frozen_ctx(encoder):
    saved = [(FZ, k, getattr(FZ, k)) for k in ('BASE', 'STORE', 'arm_state', 'backbone')] + [(XS, 'OUT', XS.OUT)]
    try:
        FZ.BASE, FZ.STORE, XS.OUT = FZ_BASE, FZ_STORE, FZ_BASE
        FZ.arm_state = lambda arm: (None, np.full(3, 1 / 3), provenance(encoder))

        def backbone(dataset_key, net, dev):
            assert dataset_key == 'private_bdf' and net is None
            return encoder_tokens(encoder, 'private_bdf', dev)
        FZ.backbone = backbone
        yield
    finally:
        for m, k, v in saved:
            setattr(m, k, v)


@contextlib.contextmanager
def ft_ctx(row):
    import torch
    from . import enc_models as EM
    saved = [(PF, k, getattr(PF, k)) for k in ('BASE', 'STORE', 'LR', 'build', 'source_init', 'param_groups')] + [(SRC, 'SEED', SRC.SEED)]
    enc = row['encoder']
    try:
        PF.BASE, PF.STORE, PF.LR, SRC.SEED = FT_BASE, FT_STORE, row['lr'], row['seed']
        PF.source_init = lambda arm: (None, torch.zeros(3), provenance(enc))

        def build(net, a0, seed, dev):
            assert net is None
            model = EM.build_ft(enc, a0, seed, dev, BRANCH)
            AUDITS.append({'encoder': enc, 'cohort': 'private_bdf', 'seed_heads': seed, **EM.audit(model.bb, enc, BRANCH)})
            return model
        PF.build = build
        PF.param_groups = lambda model: EM.param_groups(model, row['weight_decay'])
        yield
    finally:
        for m, k, v in saved:
            setattr(m, k, v)


# ----------------------------------------------------------------------------------------------- GPU units
def tokens_into(bb, crops_fn, n, fs, width, chunk=256):
    """aln41/frozen.tokens into a preallocated float16 CPU tensor [n, 3, width] (no concatenation copy); finite per chunk."""
    import torch
    from ..aln41 import timebank as TB
    T = torch.empty((n, 3, width), dtype=torch.float16)
    with torch.no_grad():
        for s in range(0, n, chunk):
            crops = crops_fn(s, min(n, s + chunk))
            B = crops[0].shape[0]
            h = bb(TB.crop_inputs(crops, fs))[:, :, 0]
            hh = h.reshape(3, B, -1).transpose(0, 1).half()
            assert bool(torch.isfinite(hh).all()), 'nonfinite float16 tokens'
            T[s:s + B] = hh.cpu()
    return T


def mff_unit(row, plan, probe):
    """aln41/cross_stim.run_unit with the encoder replaced and its 128*200 assertion generalised to 128*E."""
    import torch
    from ..aln41 import timebank as TB
    from . import enc_models as EM
    t0 = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']
    recs = plan['cross_stim_records']
    if probe:
        recs = [r for r in recs if r['lane'] == 'mff_puretone'][:6] + [r for r in recs if r['lane'] == 'mff_bapa'][:6]
    for r in recs:
        assert sha(XS.STAGE / 'epochs' / f'{r["record_id"]}.npz') == r['npz_sha256'], r['record_id']
    X, rows, children = XS.load(recs)
    Xt = torch.as_tensor(X); lay = TB.layout(250)

    def crops_fn(s, t):
        return [Xt[s:t, :, 50 + lo:50 + hi].to(dev) for lo, hi, _ in lay]
    enc = row['encoder']; E = EM.ENC[enc]['E']
    bb = encoder_tokens(enc, 'mff', dev)
    T = tokens_into(bb, crops_fn, len(X), 250, 128 * E)
    del bb; torch.cuda.empty_cache()
    dest = (FZ_STORE / 'probes' / job if probe else FZ_STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    arrays = dict(rows)
    meta = {'row': row, 'arm_provenance': provenance(enc), 'q0': [1 / 3] * 3, 'children': children, 'crop_layout': lay,
            'n_trials': int(len(X)), 'pca': {}, 'probe': probe, 'channels': EM.MFF_CHANNELS, 'token_width': 128 * E}
    for kind, f in XS.FITS:
        train, test = XS.fit_rows(rows, children, kind, f)
        if probe and (len(train) < 50 or not test):
            continue
        p = FZ.pca_fit(T, train, FZ.PCA_SEED + XS.PCA_OFFSET[kind] + f)
        arrays[f'pca_{kind}{f}'] = FZ.pca_apply(T.reshape(len(T) * 3, -1), p).reshape(len(T), 3, -1).astype(np.float16)
        meta['pca'][f'{kind}{f}'] = {k: v for k, v in p.items() if k in ('n_rows', 'dim', 'explained_variance')}
        meta['pca'][f'{kind}{f}'].update(row_ids_sha256=digest(p['row_ids']), train_children=len(set(rows['child'][train].tolist())),
                                         test_children=len(test))
        assert np.isfinite(arrays[f'pca_{kind}{f}']).all()
    np.savez_compressed(dest / 'arrays.npz', **arrays)
    meta['array_sha256'] = sha(dest / 'arrays.npz'); write(dest / 'meta.json', meta)
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(FZ_BASE / 'plan.json'), 'dest': str(dest),
           'meta_sha256': sha(dest / 'meta.json'), 'array_sha256': meta['array_sha256'], 'seconds': time.time() - t0,
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': job}
    write((FZ_BASE / 'probes' / job if probe else FZ_BASE) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], enc, 'mff', 'complete', len(X), 'trials', round(rec['seconds'], 1), flush=True)
    del T, Xt, X; gc.collect()
    return rec


def write_audits(kind, row, probe, base=None):
    """Strict-load audits of the encoders built in this unit (released weights, before any update)."""
    job = os.environ['SLURM_JOB_ID']
    if base is None:
        base = FZ_BASE if kind == 'frozen' else FT_BASE
        base = base / 'probes' / job if probe else base
    write(Path(base) / 'audits' / f'{row["id"]}.{job}.json', {'row': row, 'audits': list(AUDITS), 'job': job})


def run_frozen(uid, probe=False):
    verify(); plan = read(FZ_BASE / 'plan.json'); AUDITS.clear()
    row = next(r for r in plan['rows'] if r['id'] == uid)
    with frozen_ctx(row['encoder']):
        rec = FZ.run_unit(row, plan, probe=probe) if row['dataset'] == 'private_bdf' else mff_unit(row, plan, probe)
    write_audits('frozen', row, probe)
    return rec


def run_ft(uid, probe=False, **kw):
    """One FT row through aln41/private_ft_resume.run_unit; kw (dest, record_dir, overrides) only for the smoke resume check."""
    verify(); plan = read(FT_BASE / 'plan.json'); AUDITS.clear()
    row = next(r for r in plan['rows'] if r['id'] == uid)
    with ft_ctx(row):
        rec = PR.run_unit(row, plan, probe=probe, **kw)
    write_audits('ft', row, probe, base=kw.get('record_dir'))
    return rec


# ----------------------------------------------------------------------------------------------- state / selection
def frozen_state(row):
    if (FZ_BASE / 'units' / f'{row["id"]}.json').exists():
        return 'complete'
    return 'failed' if (FZ_BASE / 'units' / f'{row["id"]}.FAILED.json').exists() else 'ready'


def selection_path(enc, f):
    return FT_BASE / 'selection' / f'{enc}_fold{f}.json'


def calibration_rows(enc, f, rows=None):
    rows = rows if rows is not None else read(FT_BASE / 'plan.json')['rows']
    return {r['candidate']: r for r in rows if r['encoder'] == enc and r['outer_fold'] == f and r['stage'] == 'calibration'}


def selectable(enc, f, rows=None):
    if selection_path(enc, f).exists():
        return False
    return all((FT_BASE / 'units' / f'{r["id"]}.json').exists() for r in calibration_rows(enc, f, rows).values())


def choose(cands):
    """The frozen candidate rule: lower selected ES NLL; exact tie -> common."""
    return min(cands, key=lambda c: (cands[c]['selected_es_nll_bits'], c != 'common'))


def select(enc, f):
    """Training-side candidate choice for one encoder x outer fold (seed 3401); immutable once written."""
    path = selection_path(enc, f)
    lock = FT_BASE / 'selection' / 'select.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        fcntl.flock(h, fcntl.LOCK_EX)
        if path.exists():
            return read(path)
        cands = {}
        for cand, r in calibration_rows(enc, f).items():
            p = FT_BASE / 'units' / f'{r["id"]}.json'; rec = read(p)
            assert rec['status'] == 'complete' and not rec['probe'] and rec['row'] == r
            cands[cand] = {'unit': r['id'], 'record_sha256': sha(p), 'selected_es_nll_bits': rec['selected_es_nll_bits'],
                           'selected_epoch': rec['selected_epoch'], 'lr': r['lr'], 'weight_decay': r['weight_decay']}
        assert all(math.isfinite(c['selected_es_nll_bits']) for c in cands.values())
        choice = choose(cands)
        value = {'version': 'PAPER_ENCODERS_SELECTION_v1', 'encoder': enc, 'outer_fold': f, 'seed': SEEDS[0], 'candidates': cands,
                 'choice': choice, 'rule': SELECTION_RULE, 'ft_plan_sha256': sha(FT_BASE / 'plan.json'),
                 'test_fields_read': False, 'created': datetime.now().astimezone().isoformat()}
        write(path, value); path.chmod(0o444)
        print('selection', enc, 'fold', f, choice, {c: round(v['selected_es_nll_bits'], 5) for c, v in cands.items()}, flush=True)
        return value


def ft_state(row, rows=None):
    if (FT_BASE / 'units' / f'{row["id"]}.json').exists():
        return 'complete'
    if (FT_BASE / 'units' / f'{row["id"]}.FAILED.json').exists():
        return 'failed'
    if row['stage'] == 'calibration':
        return 'ready'
    p = selection_path(row['encoder'], row['outer_fold'])
    if p.exists():
        return 'ready' if read(p)['choice'] == row['candidate'] else 'skipped'
    return 'selectable' if selectable(row['encoder'], row['outer_fold'], rows) else 'waiting_selection'


def ft_summary(enc):
    rows = [r for r in read(FT_BASE / 'plan.json')['rows'] if r['encoder'] == enc]
    states = {r['id']: ft_state(r, rows) for r in rows}
    to_run = sum(states[r['id']] in ('ready', 'failed') for r in rows)
    to_run += sum(states[r['id']] in ('selectable', 'waiting_selection') for r in rows) // 2      # one of two candidates runs
    ready = sum(s == 'ready' for s in states.values()) + sum(s == 'selectable' for s in states.values()) // 2
    return {'rows': rows, 'states': states, 'remaining': to_run, 'ready': ready,
            'failed': [i for i, s in states.items() if s == 'failed'], 'complete': sum(s == 'complete' for s in states.values())}


def receipts():
    out = {'pass': [], 'other': []}
    if not plans_exist():
        return out
    src, psha = master_sources(), sha(OUT / 'plan.json')
    for path in sorted((OUT / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('sources') == src and rec.get('plan_sha256') == psha:
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status(lane='Z'):
    """Read-only lane state for the fleet coordinator (paper/arms.py convention)."""
    name, lane_name, sbatch = LANES[lane]
    slots, per_job = LANE_SLOTS[lane]
    st = {'name': name, 'lane': lane_name, 'state': 'plan_missing', 'ready': 0, 'remaining': 1, 'slots': 1, 'initial': [], 'submit': []}
    if not plans_exist():
        return st
    rec = receipts()
    if not rec['pass']:
        if rec['other']:
            return {**st, 'state': 'engineering_probe_failed'}
        return {**st, 'state': 'ready', 'ready': 1, 'submit': [sbatch, 'smoke']} if lane == 'Z' else {**st, 'state': 'waiting_smoke'}
    if lane == 'Z':
        states = [frozen_state(r) for r in read(FZ_BASE / 'plan.json')['rows']]
        left = [s for s in states if s != 'complete']
        st['remaining'] = len(left)
        if not left:
            return {**st, 'state': 'complete'}
        if 'failed' in left:
            return {**st, 'state': 'failed_unit_review'}
        return {**st, 'state': 'ready', 'ready': len(left), 'slots': slots, 'submit': [sbatch, 'worker', '--lane', 'Z', '--max-units', str(per_job)]}
    s = ft_summary(LANE_ENC[lane])
    st['remaining'] = s['remaining']
    if not s['remaining']:
        return {**st, 'state': 'complete'}
    if s['failed']:
        return {**st, 'state': 'failed_unit_review'}
    return {**st, 'state': 'ready' if s['ready'] else 'waiting_calibration', 'ready': s['ready'], 'slots': slots,
            'submit': [sbatch, 'worker', '--lane', lane, '--max-units', str(per_job)]}


# ----------------------------------------------------------------------------------------------- workers
def sub(*args):
    return subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, *map(str, args)]).returncode


def claim(base, uid, fn):
    path = base / 'units' / f'{uid}.json'
    lock = base / 'claims' / f'{uid}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if path.exists():
            return False
        rc = fn()
        if rc < 0:                          # preempted / signalled: no FAILED marker; FT units resume from resume.pt
            raise SystemExit(rc)
        if rc or not path.exists():
            write(base / 'units' / f'{uid}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
            raise RuntimeError(f'paper encoder unit failed: {uid}')
        return True


def worker(lane, max_units):
    assert receipts()['pass'], 'no passing smoke for the current sources / plan'
    verify(); count = 0
    if lane == 'Z':
        for row in read(FZ_BASE / 'plan.json')['rows']:
            if frozen_state(row) != 'ready':
                continue
            if claim(FZ_BASE, row['id'], lambda: sub('unit', '--stage', 'frozen', '--id', row['id'])):
                count += 1
            if count >= max_units:
                return
        return
    enc = LANE_ENC[lane]
    tried = set()
    while count < max_units:
        rows = [r for r in read(FT_BASE / 'plan.json')['rows'] if r['encoder'] == enc]
        for f in FOLDS:
            if selectable(enc, f, rows):
                select(enc, f)
        order = sorted(rows, key=lambda r: (r['stage'] != 'calibration', r['seed'], r['outer_fold'], r['candidate']))
        nxt = next((r for r in order if r['id'] not in tried and ft_state(r, rows) == 'ready'), None)
        if nxt is None:
            return
        tried.add(nxt['id'])
        if claim(FT_BASE, nxt['id'], lambda: sub('unit', '--stage', 'ft', '--id', nxt['id'])):
            count += 1


# ----------------------------------------------------------------------------------------------- smoke (GPU)
def smoke():
    """Engineering smoke (no outcome threshold): strict loads, finite tokens (20-ch private, 128-ch MFF), save/reload exactness,
    MindMix channel-permutation equivariance, frozen probe units of both cohorts, a 1-epoch x 3-update FT probe per encoder through
    private_ft_resume, a simulated-preemption resume check and per-update / per-ES-pass timing for GPU-hour projections."""
    import torch
    from auditory_alignment import data
    from ..aln41 import timebank as TB
    from . import enc_models as EM
    job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda'); out = OUT / 'probes' / job
    receipt = {'status': 'running', 'job': job, 'sources': master_sources(), 'plan_sha256': sha(OUT / 'plan.json'),
               'device': torch.cuda.get_device_name(0), 'checks': {}, 'units': [], 'timing': {}}
    try:
        verify()
        receipt['checks']['reve_assets'] = EM.reve_asset_hashes() == read(OUT / 'plan.json')['assets']['reve']
        assert receipt['checks']['reve_assets']
        kids = data.load_private()
        xp = torch.as_tensor(np.concatenate([k['x'][:16] for k in kids[:2]]).astype(np.float32))
        Xm, _, _ = XS.load([r for r in read(FZ_BASE / 'plan.json')['cross_stim_records'] if r['lane'] == 'mff_puretone'][:1])
        xm = torch.as_tensor(Xm[:16]); del Xm
        lay = TB.layout(250)
        for enc in ENCODERS:
            for cohort, x in (('private_bdf', xp), ('mff', xm)):
                m = EM.make_tokens(enc, cohort, BRANCH); a = EM.audit(m, enc, BRANCH); m = m.to(dev).eval()
                with torch.no_grad():
                    z = TB.crop_inputs([x[:, :, 50 + lo:50 + hi].to(dev) for lo, hi, _ in lay], 250)
                    assert tuple(z.shape) == (3 * len(x), x.shape[1], 200) and bool((z[..., 80:] == 0).all())
                    h1 = m(z); h2 = m(z)
                c = {'audit': a, 'input_shape': list(z.shape), 'token_shape': list(h1.shape), 'finite': bool(torch.isfinite(h1).all()),
                     'abs_max': float(h1.abs().max()), 'float16_finite': bool(torch.isfinite(h1.half()).all()),
                     'repeat_max_abs_diff': float((h1 - h2).abs().max())}
                assert c['finite'] and c['float16_finite'] and c['token_shape'] == [3 * len(x), x.shape[1], 1, EM.ENC[enc]['E']]
                if enc == 'MINDMIX':
                    perm = torch.randperm(x.shape[1], generator=torch.Generator().manual_seed(3401)).to(dev)
                    with torch.no_grad():
                        hp = m(z[:, perm])
                    c['channel_permutation_equivariance_max_abs_diff'] = float((hp - h1[:, perm]).abs().max())
                    assert c['channel_permutation_equivariance_max_abs_diff'] < 1e-3
                receipt['checks'][f'{enc}/{cohort}'] = c
                del m; torch.cuda.empty_cache()
            # save / reload exactness of the full FT model (encoder + heads + a)
            model = EM.build_ft(enc, torch.zeros(3), 3401, dev, BRANCH); model.eval()
            path = FT_STORE / 'probes' / job / f'save_reload_{enc}.pt'; path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            torch.save(model.state_dict(), path)
            model2 = EM.build_ft(enc, torch.ones(3), 9, dev, BRANCH); res = model2.load_state_dict(torch.load(path, map_location=dev), strict=True)
            model2.eval(); s1, s2 = model.state_dict(), model2.state_dict()
            with torch.no_grad():
                l1, _ = model.log_probs(xp[:32].to(dev)); l2, _ = model2.log_probs(xp[:32].to(dev))
            receipt['checks'][f'{enc}/save_reload'] = {'tensors': len(s1), 'all_equal': all(torch.equal(s1[k], s2[k]) for k in s1),
                                                       'missing': list(res.missing_keys), 'unexpected': list(res.unexpected_keys),
                                                       'logprob_max_abs_diff': float((l1 - l2).abs().max()), 'has_gate_a': 'a' in s1}
            assert receipt['checks'][f'{enc}/save_reload']['all_equal'] and 'a' in s1
            del model, model2; path.unlink(); torch.cuda.empty_cache()
            receipt['timing'][enc] = time_ft(enc, kids, dev)
        frows = read(FZ_BASE / 'plan.json')['rows']
        for row in frows:
            assert sub('unit', '--stage', 'frozen', '--id', row['id'], '--probe') == 0, row['id']
            rec = read(FZ_BASE / 'probes' / job / 'units' / f'{row["id"]}.json')
            with np.load(Path(rec['dest']) / 'arrays.npz') as zz:
                keys = [k for k in zz.files if k.startswith('pca_')]
                fin = all(bool(np.isfinite(zz[k]).all()) for k in keys); shapes = {k: list(zz[k].shape) for k in keys[:2]}
            assert keys and fin
            receipt['units'].append({'stage': 'frozen', 'id': row['id'], 'encoder': row['encoder'], 'dataset': row['dataset'],
                                     'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb'], 'pca_keys': len(keys), 'shapes': shapes})
        ftrows = read(FT_BASE / 'plan.json')['rows']
        for enc in ENCODERS:
            row = next(r for r in ftrows if r['encoder'] == enc and r['seed'] == 3401 and r['outer_fold'] == 0 and r['candidate'] == 'documented')
            assert sub('unit', '--stage', 'ft', '--id', row['id'], '--probe') == 0, row['id']
            rec = read(FT_BASE / 'probes' / job / 'units' / f'{row["id"]}.json')
            assert rec['label_access']['test_children'] in (12, 13) and len(rec['curve']) == 2
            assert all(math.isfinite(c['es_nll_bits']) for c in rec['curve'])
            receipt['units'].append({'stage': 'ft', 'id': row['id'], 'encoder': enc, 'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb'],
                                     'curve': rec['curve'], 'selected_epoch': rec['selected_epoch'], 'lr': row['lr'],
                                     'weight_decay': row['weight_decay']})
            assert sub('resume-check', '--id', row['id']) == 0, 'resume check ' + enc
            receipt['checks'][f'{enc}/resume'] = read(FT_BASE / 'probes' / job / f'resume_{row["id"]}.json')
        receipt['projection'] = projection(receipt)
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(out / 'receipt.json', receipt)


def time_ft(enc, kids, dev, n_updates=20, warm=3):
    """Seconds per training update (batch 64, fold 0 draws) and per ES evaluation pass, for GPU-hour projections."""
    import torch
    from . import enc_models as EM
    f = 0; train = [i for i, k in enumerate(kids) if k['fold'] != f]; test = [i for i, k in enumerate(kids) if k['fold'] == f]
    X = [torch.as_tensor(k['x'], dtype=torch.float32, device=dev) for k in kids]; Y = [np.asarray(k['y'], np.int64) for k in kids]
    fit = {i: np.flatnonzero(~kids[i]['es_mask']) for i in train}; es = sorted(i for i in train if kids[i]['es_mask'].any())
    model = EM.build_ft(enc, torch.zeros(3), 3401, dev, BRANCH)
    opt = torch.optim.AdamW(EM.param_groups(model, 1e-4), lr=1e-4); rng = np.random.default_rng(7)
    params = [p for g in opt.param_groups for p in g['params']]
    model.train(); times = []
    for i in range(warm + n_updates):
        torch.cuda.synchronize(); t = time.time()
        ch = rng.choice(train, size=PF.BATCH, replace=True); tr = np.array([fit[c][rng.integers(len(fit[c]))] for c in ch])
        xb = torch.stack([X[c][t_] for c, t_ in zip(ch, tr)]); yb = torch.as_tensor([Y[c][t_] for c, t_ in zip(ch, tr)], device=dev)
        lp, _ = model.log_probs(xb); loss = -lp[torch.arange(len(yb), device=dev), yb].mean()
        opt.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(params, 5.0); opt.step()
        torch.cuda.synchronize(); times.append(time.time() - t)
        grads = [p.grad is not None for p in model.bb.parameters()]
    torch.cuda.synchronize(); t = time.time(); PF.evaluate(model, X, kids, es, dev); torch.cuda.synchronize(); t_es = time.time() - t
    n_fit = sum(len(v) for v in fit.values()); n_es = int(sum(kids[i]['es_mask'].sum() for i in es)); n_test = int(sum(len(kids[i]['y']) for i in test))
    n_es_pass = int(sum(len(kids[i]['y']) for i in es))          # private_ft.evaluate scores every trial of the ES children
    out = {'seconds_per_update': float(np.mean(times[warm:])), 'seconds_es_pass': t_es, 'n_fit': n_fit, 'n_es': n_es, 'n_test': n_test,
           'n_es_pass_trials': n_es_pass,
           'updates_per_epoch': math.ceil(n_fit / PF.BATCH), 'backbone_params_with_grad': int(sum(grads)), 'backbone_params': len(grads),
           'peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20}
    del model, opt, X; torch.cuda.empty_cache()
    return out


def projection(receipt):
    """Projected A-GPU hours per full FT unit (100 epochs) and for the lanes; frozen from the probe units (scaled by trials)."""
    out = {}
    for enc in ENCODERS:
        t = receipt['timing'][enc]
        per_unit = PF.EPOCHS * (t['updates_per_epoch'] * t['seconds_per_update'] + t['seconds_es_pass']) \
            + 2 * t['seconds_es_pass'] * (t['n_test'] / max(1, t['n_es_pass_trials']))
        out[enc] = {'ft_unit_hours': per_unit / 3600, 'ft_units': 20, 'ft_lane_hours': 20 * per_unit / 3600}
    return out


def resume_check(uid):
    """Simulated preemption on one FT row (2 epochs x 2 updates): stop after epoch 1, restart -> resumes at epoch 2; the curve
    equals an uninterrupted run within 1e-4 bits. Nothing written here is a production unit."""
    job = os.environ['SLURM_JOB_ID']; base = FT_STORE / 'probes' / job / f'resume_{uid}'; rdir = FT_BASE / 'probes' / job / f'resume_{uid}'
    ov = {'epochs': 2, 'per_epoch': 2}
    A = run_ft(uid, dest=base / 'A', record_dir=rdir / 'A', overrides=ov)
    try:
        run_ft(uid, dest=base / 'B', record_dir=rdir / 'B', overrides={**ov, 'stop_after': 1}); raise AssertionError('no simulated stop')
    except PR.Interrupted:
        pass
    B = run_ft(uid, dest=base / 'B', record_dir=rdir / 'B', overrides=ov)
    diff = max(abs(a['es_nll_bits'] - b['es_nll_bits']) for a, b in zip(A['curve'], B['curve']))
    res = {'B_segments': [s['first_epoch'] for s in B['resume']['segments']], 'curve_A_B_max_abs_bits': diff,
           'selected_epoch_A_B': [A['selected_epoch'], B['selected_epoch']], 'resume_file_removed': not (base / 'B' / 'resume.pt').exists()}
    write(FT_BASE / 'probes' / job / f'resume_{uid}.json', res)
    assert res['B_segments'] == [1, 2] and diff <= 1e-4 and res['resume_file_removed'], res
    for d in (base / 'A', base / 'B'):
        for p in d.glob('*.pt'):
            p.unlink()


# ----------------------------------------------------------------------------------------------- CPU stages
def frozen_unit_ready(row):
    return (FZ_BASE / 'units' / f'{row["id"]}.json').exists()


def readout():
    verify()
    for row in read(FZ_BASE / 'plan.json')['rows']:
        if row['dataset'] != 'private_bdf' or not frozen_unit_ready(row):
            continue
        out = OUT / 'readout_v1' / 'units' / f'{row["id"]}.json'
        if out.exists():
            continue
        t0 = time.time()
        with frozen_ctx(row['encoder']):
            res = RO.private(row)
        write(out, {'status': 'complete', 'row': row, 'frozen_unit_sha256': sha(FZ_BASE / 'units' / f'{row["id"]}.json'),
                    'source_sha256': sha(RO.__file__), **res, 'seconds': time.time() - t0, 'job': os.environ['SLURM_JOB_ID']})
        print('readout', row['encoder'], 'private_bdf', flush=True)


def cross_readout():
    verify()
    for row in read(FZ_BASE / 'plan.json')['rows']:
        if row['dataset'] != 'mff_cross_stim' or not frozen_unit_ready(row):
            continue
        out = OUT / 'cross_readout_v1' / 'units' / f'{row["id"]}.json'
        if out.exists():
            continue
        with frozen_ctx(row['encoder']):
            res = XS.readout(row)
        write(out, {**res, 'unit_sha256': sha(FZ_BASE / 'units' / f'{row["id"]}.json'), 'source_sha256': sha(XS.__file__),
                    'job': os.environ['SLURM_JOB_ID']})
        print('cross readout', row['encoder'], flush=True)


def age():
    """aln41/age.main for the two encoders (frozen private age features) plus the raw log-variance reference."""
    from auditory_alignment import data
    from ..aln41 import age as AG, age_probe as AP
    verify()
    kids = data.load_private()
    ids = np.array([k['id'] for k in kids]); folds = np.array([str(k['fold']) for k in kids])
    ages = np.array([np.nan if k.get('age_months') is None else float(k['age_months']) for k in kids])
    results = {'roster': {'n_children': len(kids), 'age_available': int(np.isfinite(ages).sum()),
                          'missing_age_ids': ids[~np.isfinite(ages)].tolist()}, 'encoders': {}}
    for row in read(FZ_BASE / 'plan.json')['rows']:
        if row['dataset'] != 'private_bdf':
            continue
        if not frozen_unit_ready(row):
            results['encoders'][row['encoder']] = {'status': 'NOT_RUN'}; continue
        u = read(FZ_BASE / 'units' / f'{row["id"]}.json'); dest = Path(u['dest']); assert sha(dest / 'arrays.npz') == u['array_sha256']
        meta = read(dest / 'meta.json'); assert meta['children'] == {str(i): k['id'] for i, k in enumerate(kids)}
        with np.load(dest / 'arrays.npz', allow_pickle=False) as z:
            X = z['age_features'].reshape(len(kids), -1)
        results['encoders'][row['encoder']] = {'status': 'COMPLETE_VALID', 'frozen_unit': row['id'], **AP.run_probe(X, ages, ids, folds)}
    results['raw_eeg_logvar'] = {'status': 'COMPLETE_VALID', **AP.run_probe(AG.raw_logvar(kids), ages, ids, folds)}
    write(OUT / 'age_v1' / 'age_results.json', {**results, 'age_source_sha256': sha(AG.__file__), 'age_probe_sha256': sha(AP.__file__),
                                                'master_plan_sha256': sha(OUT / 'plan.json'), 'job': os.environ['SLURM_JOB_ID']})
    print({e: v.get('model_metrics') for e, v in results['encoders'].items()}, flush=True)


def selected_ft_units():
    out = []
    for row in read(FT_BASE / 'plan.json')['rows']:
        p = selection_path(row['encoder'], row['outer_fold'])
        if not p.exists() or read(p)['choice'] != row['candidate']:
            continue
        rec = FT_BASE / 'units' / f'{row["id"]}.json'
        if rec.exists():
            out.append((row, rec, p))
    return out


def support():
    from ..aln35 import support_runtime as SR
    from ..aln41 import support as SU
    verify(); plan_sha = sha(SUP_BASE / 'plan.json')
    kids = SR.load_kids()
    for row, rec, sel in selected_ft_units():
        dest = SUP_BASE / 'units' / f'{row["id"]}.json'
        if dest.exists():
            continue
        write(dest, {**SU.run_unit(row['seed'], row, rec, kids), 'plan_sha256': plan_sha, 'selection_sha256': sha(sel),
                     'encoder': row['encoder'], 'candidate': row['candidate'], 'source_sha256': sha(SU.__file__)})
        print('support', row['encoder'], row['seed'], row['outer_fold'], row['candidate'], flush=True)


def status():
    out = {'plans': plans_exist(), 'smoke_pass': [str(p) for p in receipts()['pass']] if plans_exist() else []}
    if plans_exist():
        out['frozen'] = {f"{r['encoder']}/{r['dataset']}": frozen_state(r) for r in read(FZ_BASE / 'plan.json')['rows']}
        for enc in ENCODERS:
            s = ft_summary(enc)
            out[f'ft/{enc}'] = {'complete': s['complete'], 'remaining': s['remaining'], 'ready': s['ready'], 'failed': s['failed'],
                                'selections': {f: read(selection_path(enc, f))['choice'] for f in FOLDS if selection_path(enc, f).exists()}}
        out['lanes'] = {k: {x: fleet_status(k)[x] for x in ('name', 'state', 'ready', 'remaining')} for k in LANES}
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('plan', 'smoke', 'worker', 'unit', 'resume-check', 'readout', 'cross-readout', 'age', 'support', 'status'))
    ap.add_argument('--lane', choices=tuple(LANES)); ap.add_argument('--stage', choices=('frozen', 'ft'))
    ap.add_argument('--id'); ap.add_argument('--probe', action='store_true'); ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.cmd == 'plan':
        make_plans()
    elif a.cmd == 'smoke':
        smoke()
    elif a.cmd == 'worker':
        worker(a.lane, a.max_units)
    elif a.cmd == 'unit':
        (run_frozen if a.stage == 'frozen' else run_ft)(a.id, probe=a.probe)
    elif a.cmd == 'resume-check':
        resume_check(a.id)
    elif a.cmd == 'readout':
        readout()
    elif a.cmd == 'cross-readout':
        cross_readout()
    elif a.cmd == 'age':
        age()
    elif a.cmd == 'support':
        support()
    else:
        status()


if __name__ == '__main__':
    main()
