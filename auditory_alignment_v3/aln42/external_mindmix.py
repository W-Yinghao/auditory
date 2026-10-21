"""ALN4.2 R3 external method, route A: MindMix released full architecture, common-protocol task adaptation.

Frozen binding: private/auditory_alignment_v3/aln42/external/EXTERNAL_COMPARISON_BINDING.json (sha256 recorded in the plan and
asserted at every start). Readiness evidence: private/auditory_alignment_v3/aln42/external/READINESS_REPORT.md.

Units = the 10 public DTU units of the core3 attention endpoint: content fold cf in {0, 1} x pooled person fold sf in 0..4.
Segments: auditory_alignment_v2.run.load_cohort(b) with b as aln41/frozen.py public_unit (dataset 'dtu', that cf); the cs list
is exactly frozen.py's ([i for i, s in enumerate(segs) if s['kind'] == 'cs' and s.get('s0_ign') is not None and s['role'] in
('fit', 'es', 'test') and not parts[s['p']].get('test_only')]) and its person/code/e0/role arrays are asserted equal to the
frozen B0 DTU unit of that cf. Train people = auditory_alignment_v2.train.train_participants(coh, spec, sf) (= frozen meta
pca[sf].train_people, asserted); test people = readout.public(): ss-anchor people with fold == sf and not dev.

Per unit (official code at MindMix commit 98445f36, unmodified, imported from the pinned checkout):
  model  = official EEGEncoder + Wav2Vec2Model('facebook/wav2vec2-base' @ pinned revision) + create_model('multimodal_real',
           'calra') + official load_pretrained_weights(released fusion checkpoint) + the mechanical wav2vec2 pos-conv key rename
           (weight_g/weight_v -> parametrizations.weight.original0/1; bit-identical tensors).
  train  = official MultimodalRealTrainer.setup_optimizer / train_epoch / update_learning_rate for 50 epochs (README CLI:
           batch 32, lr 1e-5, wd 0.01), seed 3401, on the train people's role=fit cs segments only (target_audio = attended
           stream); person-homogeneous batches of 32 (paper App. A.3), order from numpy default_rng([3401, epoch]);
           checkpoint = final epoch 50 (role=es is never used for selection). Resume state every 5 epochs.
  score  = blind order-symmetrised margin (eval mode, no grad), batches of 32 windows in fixed segment/sub-window order:
           s(x|t) = exp(logit_scale) cos(fused_eeg(eeg, t), aligned_audio(eeg, x)) from official forward_contrastive;
           m(c1, c2) = 1/2[(s(c1|c1) - s(c2|c1)) - (s(c2|c2) - s(c1|c2))], candidates ordered by waveform sha256 (label-free);
           segment margin = mean over the three 2 s sub-windows starting at +0, +1.5, +3.0 s of the 5 s segment; the
           attended-minus-ignored orientation is applied only after scoring. Scored: train people's fit and es cs segments
           and test people's test cs segments; every other cs segment is NaN.
Input (binding): BDF 64 scalp channels (recorded CMS reference), scipy butter(N=4, 1-40 Hz band-pass) + sosfiltfilt over
the continuous run, resample_poly 512 -> 200 Hz, per-window per-channel z-score; audio = inventory waveform (HI 'woa',
NH plain; the waveform of the core3 envelope), mono, resample_poly 44.1 -> 16 kHz, per-window peak normalisation;
target wav sample 0 = target onset, masker wav sample 0 = masker onset.

CLI: --make-plan | --smoke | --worker | --unit ID | --probe-unit ID | --prepare (CPU input cache only).
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import fcntl
import gc
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from ..aln41 import source as SRC

OUT = Path(core.OUT) / 'aln42' / 'external_v1'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln42/external_v1')
BINDING = Path(core.OUT) / 'aln42' / 'external' / 'EXTERNAL_COMPARISON_BINDING.json'
MM_REPO = Path('/projects/EEG-foundation-model/auditory_public/foundation_models/github__CookieMikeLiu__MindMix@98445f3/repo')
MM_COMMIT = '98445f368efcb161c638172501bd16f92d09a89d'
CKPT = MM_REPO.parent / 'lfs' / 'best_model_loss_0.0909.pth'
CKPT_SHA = 'fe2603e3ee2c95fa2e1e012710a2774e70b6dd5582560773aafd20b295f15026'
HF_CACHE = '/projects/EEG-foundation-model/auditory_public/derived/hf_cache/hub'
W2V_REV = '0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8'
PUB = '/projects/EEG-foundation-model/auditory_public'
BIDS = f'{PUB}/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl'
INVENTORY = f'{PUB}/derived/c3_features_v1/dtu/inventory.json'
NAME, LANE, SBATCH = 'c3_s35a42ext', 's35_aln42_external', 'slurm/aln35_aln42_external.sbatch'
SEED, EPOCHS, BATCH, LR, WD = 3401, 50, 32, 1e-5, 0.01
SUB_OFFS_S = (0.0, 1.5, 3.0)
WIN_S, FS_EEG, FS_AUD, FS_BDF, FS_COH = 2.0, 200, 16000, 512, 128
SCORE_BATCH = 32
STATE_EVERY = 5
SMOKE = {'train_windows': 64, 'epochs': 1, 'score_segments': 32}
README_ARGV = ['universal_eeg_finetune.py', '--dataset', 'DTU', '--data_path', '<DTU_trail>', '--strategy', 'multimodal_real',
               '--fusion_method', 'calra', '--pretrained_model', str(CKPT), '--batch_size', str(BATCH), '--epochs', str(EPOCHS),
               '--lr', str(LR), '--weight_decay', str(WD), '--seed', str(SEED)]
POS_RENAME = {'audio_model.encoder.pos_conv_embed.conv.weight_g': 'audio_encoder.encoder.pos_conv_embed.conv.parametrizations.weight.original0',
              'audio_model.encoder.pos_conv_embed.conv.weight_v': 'audio_encoder.encoder.pos_conv_embed.conv.parametrizations.weight.original1'}
MM_FILES = ('universal_eeg_finetune.py', 'universal_models.py', 'universal_trainer.py', 'modeling_finetune_2.py', 'utils.py')
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest


# ----------------------------------------------------------------------------------------------------------- plan
def sources():
    here = Path(__file__).parent; repo = Path(core.REPO)
    files = [here / 'external_mindmix.py', repo / 'auditory_alignment_v3/aln41/frozen.py', repo / 'auditory_alignment_v3/aln41/readout.py',
             repo / 'auditory_alignment/data.py', repo / 'auditory_alignment_v2/run.py', repo / 'auditory_alignment_v2/train.py',
             repo / 'auditory_c3/features_dtu.py']
    out = {str(p.relative_to(repo)): sha(p) for p in sorted(set(files))}
    out.update({f'mindmix@{MM_COMMIT[:8]}/{f}': sha(MM_REPO / f) for f in MM_FILES})
    return out


def frozen_b0():
    from ..aln41 import frozen as FZ
    plan = read(FZ.BASE / 'plan.json'); out = {}
    for cf in (0, 1):
        row = next(r for r in plan['rows'] if r['arm'] == 'B0' and r['dataset'] == 'dtu' and r['content_fold'] == cf)
        rec = read(FZ.BASE / 'units' / f'{row["id"]}.json'); assert rec['status'] == 'complete'
        out[str(cf)] = {'unit': row['id'], 'dest': rec['dest'], 'array_sha256': rec['array_sha256'], 'meta_sha256': rec['meta_sha256']}
    return out


def make_plan():
    binding = read(BINDING)
    assert binding.get('frozen') is True and binding['route'].startswith('A_MindMix'), 'binding not frozen'
    rows = []
    for cf in (0, 1):
        for sf in range(5):
            body = {'method': 'MindMix_released_full_architecture_common_protocol', 'dataset': 'dtu', 'content_fold': cf,
                    'person_fold': sf, 'seed': SEED}
            rows.append({**body, 'id': 'ALN42X_' + digest(body, 16)})
    body = {'version': 'ALN42_EXTERNAL_MINDMIX_v1', 'rows': rows, 'sources': sources(), 'binding_sha256': sha(BINDING),
            'frozen_b0_dtu': frozen_b0(), 'checkpoint_sha256': CKPT_SHA, 'mindmix_commit': MM_COMMIT, 'wav2vec2_revision': W2V_REV,
            'store': str(STORE), 'geometry': {'sub_window_starts_s': list(SUB_OFFS_S), 'window_s': WIN_S, 'segment_s': 5.0},
            'recipe': {'epochs': EPOCHS, 'batch_size': BATCH, 'lr': LR, 'weight_decay': WD, 'seed': SEED, 'checkpoint': 'final_epoch_50',
                       'train_rows': 'train people, role fit, cs', 'batches': 'person-homogeneous', 'score_batch': SCORE_BATCH},
            'smoke': SMOKE}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
        write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    print('ALN42 external MindMix plan', len(rows), sha(plan), flush=True)
    for r in rows:
        print(r['id'], 'cf', r['content_fold'], 'sf', r['person_fold'])


def verify(plan):
    assert plan['sources'] == sources(), 'external source drift'
    assert sha(BINDING) == plan['binding_sha256'], 'binding drift'
    assert plan['frozen_b0_dtu'] == frozen_b0(), 'frozen B0 drift'


# ----------------------------------------------------------------------------------------------------------- data
def cohort_index(cf):
    """Core3 cs list of content fold cf with each segment's trial geometry (subject, trial, start, streams, onsets)."""
    import h5py
    from auditory_alignment import data as D
    from auditory_alignment_v2.run import load_cohort
    b = {'experiment_id': f'ALN42X_cf{cf}', 'family_id': 'ALN41', 'dataset': 'dtu', 'subject_fold': 0, 'content_fold': cf, 'seed': SEED,
         'spec': {'architecture': 'cbramod', 'window': 'full', 'objective': 'NCE', 'target': 'local', 'audio_head': 'fixed_features',
                  'training_task': 'paired_alignment', 'epochs': 1, 'adaptation': 'pretrained_full'}}
    coh = load_cohort(b); segs = coh.segments; parts = coh.participants
    cs = [i for i, s in enumerate(segs) if s['kind'] == 'cs' and s.get('s0_ign') is not None and s['role'] in ('fit', 'es', 'test')
          and not parts[s['p']].get('test_only')]
    items = [i for i, s in enumerate(segs) if s['kind'] == 'ss' and s['role'] in ('fit', 'es', 'test') and not parts[s['p']].get('test_only')]
    ss_people = sorted({parts[segs[i]['p']]['id'] for i in items})
    A = {'cs_person': np.array([parts[segs[i]['p']]['id'] for i in cs]), 'cs_code': np.array([str(segs[i]['code']) for i in cs]),
         'cs_e0': np.array([segs[i]['e0'] for i in cs]), 'cs_role': np.array([segs[i]['role'] for i in cs])}
    # replicate load_dtu's EEG-bank layout to recover (trial, start) of every segment
    inv = json.load(open(INVENTORY)); invd = {(r['file'], r['trial'], r['kind']): r for r in inv}
    cg = json.load(open(os.path.join(D.DTU_KCS, 'content_groups.json')))['content']
    with h5py.File(os.path.join(D.DTU_KCS, f'dtu_cf{cf}.h5'), 'r') as tf:
        tkeys = set(tf.keys())
    trials, base = [], 0
    for pi, p in enumerate(parts):
        with h5py.File(os.path.join(D.DTU_PRE, f'{p["id"]}.h5'), 'r') as f:
            fsrc = str(f.attrs['source'])
            for k in sorted(f.keys()):
                g = f[k]; two = str(g.attrs['talkers']) == 'twotalker'
                t = invd.get((p['id'], k, 'target')); m = invd.get((p['id'], k, 'masker'))
                th = t['sha'] if t else None; mh = m['sha'] if m else None
                if th is None or th not in cg or th not in tkeys or (two and (mh is None or mh not in tkeys)):
                    continue
                n = int(g['eeg_1_20'].shape[1])
                trials.append({'pi': pi, 'sub': p['id'], 'trial': k, 'two': two, 'th': th, 'mh': mh, 'moff': float(m['offset_s']) if two else None,
                               'onset_s': float(g.attrs['onset_s']), 'mon_attr': float(g.attrs['masker_onset_rel_s']) if two else None,
                               'base': base, 'n': n, 'source': fsrc, 'group': cg[th]['group'],
                               'tpath': t['path'], 'mpath': m['path'] if two else None})
                base += n
    starts = np.array([t['base'] for t in trials])
    geo = []
    for j, i in enumerate(cs):
        s = segs[i]; ti = int(np.searchsorted(starts, s['e0'], side='right') - 1); t = trials[ti]; st = int(s['e0'] - t['base'])
        assert t['pi'] == s['p'] and t['two'] and 0 <= st < t['n'], (i, t['sub'])
        assert s['uid'] == f"g{t['group']}@{st}" and s['code'] == t['th'][:10], (s['uid'], s['code'], t['trial'])
        assert abs(t['moff'] - t['mon_attr']) < 1e-6
        geo.append({'sub': t['sub'], 'trial': t['trial'], 'st': st, 'th': t['th'], 'mh': t['mh'], 'moff': t['moff'], 'onset_s': t['onset_s'],
                    'source': t['source'], 'tpath': t['tpath'], 'mpath': t['mpath']})
    folds = {p['id']: p['fold'] for p in parts}; dev = {p['id'] for p in parts if p.get('dev')}
    spec = b['spec']; seg_len = coh.meta['seg_len']
    del coh; gc.collect()
    return {'arrays': A, 'geo': geo, 'folds': folds, 'dev': dev, 'ss_people': ss_people, 'spec': spec, 'parts': parts, 'seg_len': seg_len}


def unit_people(ix, sf):
    from auditory_alignment_v2.train import train_participants

    class _C:  # train_participants only reads .participants
        participants = ix['parts']
    train = sorted(ix['parts'][i]['id'] for i in train_participants(_C, ix['spec'], sf))
    test = sorted(p for p in ix['ss_people'] if ix['folds'].get(p) == sf and p not in ix['dev'])
    return train, test


def check_frozen(ix, cf, plan, sf=None, train=None, test=None):
    rec = plan['frozen_b0_dtu'][str(cf)]
    with np.load(Path(rec['dest']) / 'arrays.npz', allow_pickle=False) as z:
        for k in ('cs_person', 'cs_code', 'cs_e0', 'cs_role'):
            assert np.array_equal(ix['arrays'][k], z[k]), f'frozen {k} mismatch'
        people = set(z['person'].tolist()) if sf is not None else None
    if sf is not None:
        meta = read(Path(rec['dest']) / 'meta.json')
        assert train == meta['pca'][str(sf)]['train_people'], 'train people mismatch'
        assert test == sorted(p for p in people if meta['folds'].get(p) == sf and p not in set(meta['dev_people'])), 'test people mismatch'
    return True


def _lock(path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    h = path.open('a+'); fcntl.flock(h, fcntl.LOCK_EX); return h


def eeg_cache(sub, trials):
    """{trial: (j0, eeg200 [64, L] float32)} for the person's cs trials; built once from the continuous BDF run."""
    path = STORE / 'input_v1' / 'eeg' / f'{sub}.npz'
    h = _lock(STORE / 'input_v1' / 'locks' / f'eeg_{sub}.lock')
    try:
        if not path.exists():
            import mne
            import pandas as pd
            from scipy.signal import butter, sosfiltfilt, resample_poly
            src = {t['source'] for t in trials}; assert len(src) == 1
            bdf = os.path.join(PUB, src.pop())
            ch = pd.read_csv(bdf.replace('_eeg.bdf', '_channels.tsv'), sep='\t')
            names = [n for n, t in zip(ch['name'], ch['type']) if str(t).lower() == 'eeg'][:64]
            assert [n.upper() for n in names] == MM_CH_NAMES, 'channel order'
            raw = mne.io.read_raw_bdf(bdf, preload=False, verbose=False); assert raw.info['sfreq'] == FS_BDF
            X = raw.get_data(picks=names) * 1e6
            sos = butter(4, [1.0, 40.0], btype='bandpass', fs=FS_BDF, output='sos')
            X = sosfiltfilt(sos, X, axis=1)
            X = resample_poly(X, 25, 64, axis=1).astype(np.float32)
            arrs = {}
            for t in {(t['trial'], t['onset_s']) for t in trials}:
                k, onset = t; a = int(round(onset * FS_BDF)); j0 = int(round(a / FS_BDF * FS_EEG))
                n = next(x['n'] for x in trials if x['trial'] == k); L = int(np.ceil(n / FS_COH * FS_EEG)) + 2
                assert j0 + L <= X.shape[1]
                arrs[f'eeg__{k}'] = X[:, j0:j0 + L]; arrs[f'j0__{k}'] = np.array(j0)
            tmp = path.with_name(path.name + '.tmp.npz'); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            np.savez(tmp, **arrs); os.replace(tmp, path)
            del X; gc.collect()
    finally:
        h.close()
    with np.load(path) as z:
        out = {k[5:]: (int(z['j0__' + k[5:]]), z[k]) for k in z.files if k.startswith('eeg__')}
    assert {t['trial'] for t in trials} <= set(out), f'eeg cache of {sub} lacks trials'
    return out


def audio_cache(h_, path_):
    """16 kHz mono float32 of one waveform (project _mono16k; sha256 of the mono int16 asserted == inventory sha)."""
    path = STORE / 'input_v1' / 'audio' / f'{h_}.npy'
    lk = _lock(STORE / 'input_v1' / 'locks' / f'aud_{h_}.lock')
    try:
        if not path.exists():
            from auditory_c3.features_dtu import _mono16k
            x, h2 = _mono16k(path_); assert h2 == h_, 'audio sha mismatch'
            tmp = path.with_name(path.name + '.tmp.npy'); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            np.save(tmp, x.astype(np.float32)); os.replace(tmp, path)
    finally:
        lk.close()
    return np.load(path)


class Inputs:
    """Window extraction for scored / trained segments (binding geometry)."""

    def __init__(self, ix, seg_ids):
        self.geo = ix['geo']; self.E, self.A = {}, {}
        need = sorted({self.geo[i]['sub'] for i in seg_ids})
        for sub in need:
            tr = [g for g in self.geo if g['sub'] == sub]
            n_of = {}
            for i, g in enumerate(self.geo):
                if g['sub'] == sub:
                    n_of[g['trial']] = None
            trials = [{'trial': k, 'onset_s': next(g['onset_s'] for g in tr if g['trial'] == k), 'source': tr[0]['source'],
                       'n': ix['trial_n'][(sub, k)]} for k in n_of]
            self.E[sub] = eeg_cache(sub, trials)
        for i in seg_ids:
            g = self.geo[i]
            for h_, p_ in ((g['th'], g['tpath']), (g['mh'], g['mpath'])):
                if h_ not in self.A:
                    self.A[h_] = audio_cache(h_, p_)

    def window(self, i, o):
        g = self.geo[i]; tau = g['st'] / FS_COH + o
        j0, e = self.E[g['sub']][g['trial']]
        j = int(round((round(g['onset_s'] * FS_BDF) / FS_BDF + tau) * FS_EEG)) - j0; L = int(WIN_S * FS_EEG)
        x = e[:, j:j + L].astype(np.float32); assert j >= 0 and x.shape[1] == L
        x = (x - x.mean(1, keepdims=True)) / (x.std(1, keepdims=True) + 1e-8)
        La = int(WIN_S * FS_AUD)
        ia = int(round(tau * FS_AUD)); im = int(round((tau - g['moff']) * FS_AUD))
        a = self.A[g['th']][ia:ia + La]; m = self.A[g['mh']][im:im + La]
        assert im >= 0 and len(a) == La and len(m) == La, ('audio range', i, o)
        a = a / max(float(np.abs(a).max()), 1e-8); m = m / max(float(np.abs(m).max()), 1e-8)
        return x, a.astype(np.float32), m.astype(np.float32)


# ----------------------------------------------------------------------------------------------------------- model
MM_CH_NAMES = [
    "FP1", "AF7", "AF3", "F1", "F3", "F5", "F7", "FT7", "FC5", "FC3", "FC1", "C1", "C3", "C5", "T7", "TP7", "CP5", "CP3", "CP1", "P1",
    "P3", "P5", "P7", "P9", "PO7", "PO3", "O1", "IZ", "OZ", "POZ", "PZ", "CPZ", "FPZ", "FP2", "AF8", "AF4", "AFZ", "FZ", "F2", "F4", "F6",
    "F8", "FT8", "FC6", "FC4", "FC2", "FCZ", "CZ", "C2", "C4", "C6", "T8", "TP8", "CP6", "CP4", "CP2", "P2", "P4", "P6", "P8", "P10",
    "PO8", "PO4", "O2"]


def safe_load(path, map_location='cpu'):
    import argparse as _ap
    import torch
    torch.serialization.add_safe_globals([_ap.Namespace])
    return torch.load(path, map_location=map_location, weights_only=True)


def official():
    os.environ.setdefault('HF_HUB_CACHE', HF_CACHE); os.environ.setdefault('HF_HUB_OFFLINE', '1')
    if str(MM_REPO) not in sys.path:
        sys.path.insert(0, str(MM_REPO))
    import universal_eeg_finetune as UEF
    import universal_models as UM
    import universal_trainer as UT
    UM.load_trusted_checkpoint = safe_load  # weights_only unpickling; keys/values unchanged
    assert UEF.ch_names == MM_CH_NAMES
    return UEF, UM, UT


def build_model(dev):
    import torch
    UEF, UM, UT = official()                      # sets the HF cache env before transformers is imported
    from transformers import Wav2Vec2Model
    old = sys.argv; sys.argv = list(README_ARGV)
    try:
        args = UEF.get_args()
    finally:
        sys.argv = old
    UEF.set_random_seed(args.seed)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        eeg = UEF.EEGEncoder(args, dev)
        audio = Wav2Vec2Model.from_pretrained('facebook/wav2vec2-base', revision=W2V_REV).to(dev)
        model = UM.create_model(args.strategy, eeg, audio, args.fusion_method, num_classes=2, use_auditory_type=args.use_auditory_type)
        model.to(dev)
        model.load_pretrained_weights(args.pretrained_model)
    skipped = [l for l in buf.getvalue().splitlines() if l.startswith('Skipped')]
    assert sorted(skipped) == sorted(['Skipped: audio_model.encoder.pos_conv_embed.conv.weight_g (shape mismatch or not found)',
                                      'Skipped: audio_model.encoder.pos_conv_embed.conv.weight_v (shape mismatch or not found)',
                                      'Skipped: classifier.weight (shape mismatch or not found)',
                                      'Skipped: classifier.bias (shape mismatch or not found)']), skipped
    sd = safe_load(args.pretrained_model)['model_state_dict']; msd = model.state_dict()
    for src_k, dst_k in POS_RENAME.items():
        assert msd[dst_k].shape == sd[src_k].shape
        msd[dst_k] = sd[src_k]
    model.load_state_dict(msd)
    loaded = sum(int(torch.equal(model.state_dict()[k if not k.startswith(('eeg_model.', 'audio_model.')) else
                                                 k.replace('eeg_model.', 'eeg_encoder.').replace('audio_model.', 'audio_encoder.')].cpu(), v))
                 for k, v in sd.items() if k not in POS_RENAME and not k.startswith('classifier.'))
    assert loaded == len(sd) - 4, loaded
    del sd, msd; gc.collect()
    return model, args, UT


def blind_margin(model, eeg, c1, c2):
    import torch
    n = torch.nn.functional.normalize; s = model.clip_loss.logit_scale.exp()

    def pair(a, b):
        fe, fa, fb = model.forward_contrastive(eeg, a, b)
        return (n(fe, dim=-1) * n(fa, dim=-1)).sum(-1) * s, (n(fe, dim=-1) * n(fb, dim=-1)).sum(-1) * s
    s11, s21 = pair(c1, c2); s22, s12 = pair(c2, c1)
    return 0.5 * ((s11 - s21) - (s22 - s12))


# ----------------------------------------------------------------------------------------------------------- unit
def run_unit(row, plan, probe=False):
    import torch
    t_all = time.time(); job = os.environ['SLURM_JOB_ID']
    dev = torch.device('cuda'); torch.cuda.reset_peak_memory_stats()
    cf, sf = row['content_fold'], row['person_fold']
    assert sha(CKPT) == CKPT_SHA
    ix = cohort_index(cf)
    ix['trial_n'] = {}
    import h5py
    from auditory_alignment import data as D
    for sub in sorted({g['sub'] for g in ix['geo']}):
        with h5py.File(os.path.join(D.DTU_PRE, f'{sub}.h5'), 'r') as f:
            for k in {g['trial'] for g in ix['geo'] if g['sub'] == sub}:
                ix['trial_n'][(sub, k)] = int(f[k]['eeg_1_20'].shape[1])
    train_p, test_p = unit_people(ix, sf)
    checks = {'frozen_arrays_and_people_equal': check_frozen(ix, cf, plan, sf, train_p, test_p)}
    A = ix['arrays']; person, role = A['cs_person'], A['cs_role']
    fit_ids = [i for i in range(len(person)) if person[i] in set(train_p) and role[i] == 'fit']
    side_ids = [i for i in range(len(person)) if person[i] in set(train_p) and role[i] in ('fit', 'es')]
    test_ids = [i for i in range(len(person)) if person[i] in set(test_p) and role[i] == 'test']
    windows = [(i, o) for i in fit_ids for o in SUB_OFFS_S]
    score_ids = side_ids + test_ids
    full_counts = {'train_windows': len(windows), 'score_windows': len(score_ids) * len(SUB_OFFS_S)}
    if probe:
        windows = windows[:SMOKE['train_windows']]; score_ids = side_ids[:SMOKE['score_segments']]
    t0 = time.time()
    inp = Inputs(ix, sorted(set([w[0] for w in windows]) | set(score_ids)))
    t_prep = time.time() - t0
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    model, args, UT = build_model(dev)
    trainer = UT.create_trainer(args.strategy, model, dev, args); trainer.setup_optimizer()
    owner = np.array([person[i] for i, _ in windows])

    def loader(ep):
        rng = np.random.default_rng([SEED, ep]); batches = []
        for p in sorted(set(owner.tolist())):
            idx = np.flatnonzero(owner == p); idx = idx[rng.permutation(len(idx))]
            batches += [idx[k:k + BATCH] for k in range(0, len(idx), BATCH)]
        for b in [batches[k] for k in rng.permutation(len(batches))]:
            xs = [inp.window(*windows[j]) for j in b]
            yield (torch.from_numpy(np.stack([x[0] for x in xs])).to(dev), torch.from_numpy(np.stack([x[1] for x in xs])).to(dev),
                   torch.from_numpy(np.stack([x[2] for x in xs])).to(dev), torch.ones(len(b), device=dev))

    class _L:  # iterable with len() for the official train_epoch
        def __init__(self, ep):
            self.ep = ep; self.n = sum(int(np.ceil((owner == p).sum() / BATCH)) for p in set(owner.tolist()))

        def __iter__(self):
            return loader(self.ep)

        def __len__(self):
            return self.n
    epochs = SMOKE['epochs'] if probe else EPOCHS
    state_path = dest / 'train_state.pt'; history, start = [], 0
    if state_path.exists() and not probe:
        st = torch.load(state_path, map_location='cpu', weights_only=False)
        assert st['plan_sha256'] == sha(OUT / 'plan.json') and st['row_id'] == row['id']
        model.load_state_dict(st['model']); trainer.optimizer.load_state_dict(st['optimizer'])
        trainer.warmup_scheduler.load_state_dict(st['warmup']); trainer.scheduler.load_state_dict(st['scheduler'])
        torch.set_rng_state(st['rng_cpu']); torch.cuda.set_rng_state(st['rng_cuda']); history, start = st['history'], st['epoch'] + 1
    t0 = time.time()
    for ep in range(start, epochs):
        te = time.time(); lr = trainer.optimizer.param_groups[0]['lr']
        tl, _, tclip = trainer.train_epoch(_L(ep), ep); trainer.update_learning_rate(ep)
        history.append({'epoch': ep + 1, 'lr': lr, 'clip_loss': float(tclip), 'seconds': round(time.time() - te, 1)})
        print(row['id'], 'epoch', ep + 1, history[-1], flush=True)
        if not probe and ((ep + 1) % STATE_EVERY == 0 and ep + 1 < epochs):
            torch.save({'plan_sha256': sha(OUT / 'plan.json'), 'row_id': row['id'], 'epoch': ep, 'model': model.state_dict(),
                        'optimizer': trainer.optimizer.state_dict(), 'warmup': trainer.warmup_scheduler.state_dict(),
                        'scheduler': trainer.scheduler.state_dict(), 'rng_cpu': torch.get_rng_state(), 'rng_cuda': torch.cuda.get_rng_state(),
                        'history': history}, state_path.with_suffix('.tmp'))
            os.replace(state_path.with_suffix('.tmp'), state_path)
    t_train = time.time() - t0
    if not probe:
        torch.save(model.state_dict(), dest / 'final_model.pt')
        if state_path.exists():
            state_path.unlink()
    # ---------------- blind scoring (eval mode, fixed order, batches of SCORE_BATCH windows)
    model.eval(); t0 = time.time()
    sw = [(i, o) for i in score_ids for o in SUB_OFFS_S]
    raw = np.full(len(sw), np.nan)
    first = {i: min(inp.geo[i]['th'], inp.geo[i]['mh']) for i in score_ids}
    with torch.no_grad():
        for k in range(0, len(sw), SCORE_BATCH):
            xs = [inp.window(*w) for w in sw[k:k + SCORE_BATCH]]
            e = torch.from_numpy(np.stack([x[0] for x in xs])).to(dev)
            at = torch.from_numpy(np.stack([x[1] for x in xs])).to(dev); ig = torch.from_numpy(np.stack([x[2] for x in xs])).to(dev)
            fa = np.array([first[i] == inp.geo[i]['th'] for i, _ in sw[k:k + SCORE_BATCH]])
            fa_t = torch.from_numpy(fa).to(dev)[:, None]
            c1 = torch.where(fa_t, at, ig); c2 = torch.where(fa_t, ig, at)       # label-free order: smaller waveform sha first
            m = blind_margin(model, e, c1, c2)
            if k == 0:
                checks['swap_max_abs'] = float((m + blind_margin(model, e, c2, c1)).abs().max())
                checks['batch_invariance_max_abs'] = float((torch.cat([blind_margin(model, e[j:j + 1], c1[j:j + 1], c2[j:j + 1]) for j in range(min(4, len(e)))])
                                                            - m[:min(4, len(e))]).abs().max())
            raw[k:k + len(xs)] = m.double().cpu().numpy()
    t_score = time.time() - t0
    raw = raw.reshape(len(score_ids), len(SUB_OFFS_S))
    first_is_att = np.array([first[i] == inp.geo[i]['th'] for i in score_ids])
    sub_oriented = np.where(first_is_att[:, None], raw, -raw)            # orientation applied after scoring (evaluation)
    n = len(person)
    margin = np.full(n, np.nan); msub = np.full((n, len(SUB_OFFS_S)), np.nan); mraw = np.full(n, np.nan)
    fia = np.zeros(n, bool); scored = np.full(n, '', dtype='<U10')
    margin[score_ids] = sub_oriented.mean(1); msub[score_ids] = sub_oriented; mraw[score_ids] = raw.mean(1); fia[score_ids] = first_is_att
    scored[side_ids if not probe else score_ids] = 'train_side'
    if not probe:
        scored[test_ids] = 'test'
    checks['margins_finite'] = bool(np.isfinite(margin[score_ids]).all())
    checks['swap_ok'] = checks['swap_max_abs'] < 1e-3; checks['batch_invariance_ok'] = checks['batch_invariance_max_abs'] < 1e-2
    np.savez_compressed(dest / 'margins.npz', cs_person=person, cs_code=A['cs_code'], cs_e0=A['cs_e0'], cs_role=role, margin=margin,
                        margin_subwindows=msub, margin_unoriented=mraw, first_is_attended=fia, scored=scored,
                        sub_window_starts_s=np.array(SUB_OFFS_S))
    rec = {'status': 'complete' if all(v for k, v in checks.items() if k.endswith(('_ok', '_equal', 'finite'))) else 'check_failed',
           'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'binding_sha256': sha(BINDING), 'dest': str(dest),
           'npz_sha256': sha(dest / 'margins.npz'), 'final_model_sha256': None if probe else sha(dest / 'final_model.pt'),
           'epochs_run': len(history), 'history': history, 'final_clip_loss': history[-1]['clip_loss'] if history else None,
           'n_train_people': len(train_p), 'n_test_people': len(test_p), 'n_train_windows': len(windows),
           'n_scored_segments': {'train_side': int((scored == 'train_side').sum()), 'test': int((scored == 'test').sum())},
           'seconds': {'prepare': round(t_prep, 1), 'train': round(t_train, 1), 'score': round(t_score, 1), 'total': round(time.time() - t_all, 1)},
           'train_seconds_per_window_epoch': t_train / max(1, len(history)) / max(1, len(windows)),
           'score_seconds_per_window': t_score / max(1, len(sw)), 'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20,
           'full_unit_counts': full_counts,
           'projected_full_unit_hours': (t_train / max(1, len(history)) / max(1, len(windows)) * full_counts['train_windows'] * EPOCHS
                                         + t_score / max(1, len(sw)) * full_counts['score_windows']) / 3600,
           'device': torch.cuda.get_device_name(0), 'job': job, 'checks': checks}
    out = OUT / 'probes' / job if probe else OUT
    write(out / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], 'cf', cf, 'sf', sf, rec['status'], rec['seconds'], flush=True)
    assert rec['status'] == 'complete', checks
    return rec


def prepare(plan):
    """CPU-only: build the EEG and audio input caches for every person / waveform of both content folds."""
    for cf in (0, 1):
        ix = cohort_index(cf)
        import h5py
        from auditory_alignment import data as D
        ix['trial_n'] = {}
        for sub in sorted({g['sub'] for g in ix['geo']}):
            with h5py.File(os.path.join(D.DTU_PRE, f'{sub}.h5'), 'r') as f:
                for k in {g['trial'] for g in ix['geo'] if g['sub'] == sub}:
                    ix['trial_n'][(sub, k)] = int(f[k]['eeg_1_20'].shape[1])
        check_frozen(ix, cf, plan)
        Inputs(ix, list(range(len(ix['geo']))))
        print('prepared cf', cf, flush=True)


# ----------------------------------------------------------------------------------------------------------- fleet
def receipts():
    out = {'pass': [], 'other': []}
    if not (OUT / 'plan.json').exists():
        return out
    ps = sha(OUT / 'plan.json')
    for path in sorted((OUT / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('plan_sha256') == ps:
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 10, 'slots': 1, 'initial': [], 'submit': []}
    if not (OUT / 'plan.json').exists():
        return st
    plan = read(OUT / 'plan.json')
    left = [r for r in plan['rows'] if not (OUT / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(left)
    if not left:
        return {**st, 'state': 'complete'}
    if any((OUT / 'units' / f'{r["id"]}.FAILED.json').exists() for r in left):
        return {**st, 'state': 'failed_unit_review'}
    rec = receipts()
    if not rec['pass']:
        return {**st, 'state': 'engineering_probe_failed'} if rec['other'] else {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
    return {**st, 'state': 'ready', 'ready': len(left), 'slots': 2, 'submit': [SBATCH, '--worker']}


def main():
    ap = argparse.ArgumentParser()
    for flag in ('make_plan', 'smoke', 'worker', 'prepare'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--probe-unit')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = read(OUT / 'plan.json'); verify(plan)
    if a.prepare:
        prepare(plan); return
    if a.unit or a.probe_unit:
        run_unit(next(r for r in plan['rows'] if r['id'] in (a.unit, a.probe_unit)), plan, probe=bool(a.probe_unit)); return
    if a.smoke:
        job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
        try:
            row = plan['rows'][0]
            assert subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--probe-unit', row['id']]).returncode == 0
            rec = read(OUT / 'probes' / job / 'units' / f'{row["id"]}.json')
            assert rec['status'] == 'complete' and rec['n_scored_segments']['test'] == 0
            receipt['units'].append({'id': row['id'], 'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb'], 'device': rec['device'],
                                     'projected_full_unit_hours': rec['projected_full_unit_hours'], 'full_unit_counts': rec['full_unit_counts'],
                                     'train_s_per_window_epoch': rec['train_seconds_per_window_epoch'],
                                     'score_s_per_window': rec['score_seconds_per_window'], 'checks': rec['checks']})
            receipt['status'] = 'pass'
        except BaseException:
            receipt.update(status='failed', traceback=traceback.format_exc()); raise
        finally:
            write(OUT / 'probes' / job / 'receipt.json', receipt)
        return
    assert a.worker and receipts()['pass'], 'no passing smoke'
    for row in plan['rows']:
        path = OUT / 'units' / f'{row["id"]}.json'
        if path.exists() or (OUT / 'units' / f'{row["id"]}.FAILED.json').exists():
            continue
        lock = OUT / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', row['id']]).returncode
            if rc < 0:
                raise SystemExit(f'unit interrupted by signal {-rc}; resume state kept')
            if rc or not path.exists():
                write(OUT / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('aln42 external unit failed')
        break


if __name__ == '__main__':
    main()
