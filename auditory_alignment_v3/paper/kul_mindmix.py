"""Paper line W6: MindMix (official code, released fusion checkpoint) reproduced on KU Leuven AAD v2.0, with the shortcut audit.

Frozen binding: private/auditory_alignment_v3/paper/kul_v1/KUL_MINDMIX_BINDING.json, written by --make-binding before any
input is read and before any score exists; its sha256 is bound in the plan and asserted at every start.
Revision 01 (KUL_MINDMIX_REVISION_01.json, frozen before any unit trained): approved W6 budget ~20 GPU-h -> P1 at all 5 folds,
P2 at folds 0-1 only (all 16 non-repetition trials; fold 1 = experiment-2 trials, same audio pairs as experiment 1 with the
attention swapped). Active plan = plan_v2.json (112 units); the 160-unit v1 plan is kept as plan_v1_superseded.json.

Data: Zenodo 4004271 (KUL AAD v2.0; md5 of every file asserted against the saved Zenodo record), S1..S16.mat, all 20 trials
per subject including the experiment-3 repetitions (experiment / part / repetition / condition recorded per window).
Per trial: attended wav = stimuli[0] (left ear) if attended_ear == 'L' else stimuli[1] (right ear), unattended = the other,
exactly the presented files named in the trial (HRTF trials -> *_hrtf.wav, dry trials -> *_dry.wav), read from stimuli.zip
in memory (never extracted), int16 / 32768, mono, resample_poly 44.1 -> 16 kHz, wav sample 0 = trial start, per-window peak
normalisation. EEG = RawData.EegData, 64 channels as provided (already 128 Hz, 0.5 Hz high-pass, MWF), resample_poly
128 -> 200 Hz per trial, per-window per-channel z-score. Windows: non-overlapping 2 s from trial start, n = floor(min(EEG,
attended wav, unattended wav) / 2 s), trailing partial window dropped; canonical order = TrialID ascending, then time.

Protocols (one official fine-tune per subject x fold; 16 subjects):
  P1 'paper split'       per subject sklearn KFold(5, shuffle=True, random_state=42) over the subject's canonical windows
                         (universal_eeg_finetune.py:492-498, :536); all 5 folds.
  P2 'trial-held-out'    per subject 5 folds of 4 whole trials (fold f tests trials at TrialID-rank 4f..4f+3); no window of
                         a test trial is trained on; folds 0-1 run (revision 01). Audio overlap remains (see revision 01):
                         fold 0 tests experiment-1 trials whose audio pairs occur in training (experiment 2) with the other
                         talker attended and whose first 2 min are replayed with the same attention (repetitions); fold 1
                         tests experiment-2 trials whose audio pairs occur in training only with the other talker attended.
Recipe: official EEGEncoder + Wav2Vec2Model + create_model('multimodal_real', 'calra') + load_pretrained_weights(released
fusion checkpoint) + the mechanical wav2vec2 pos-conv key rename (external_mindmix.build_model, KUL CLI); official
MultimodalRealTrainer.setup_optimizer / train_epoch / update_learning_rate, 50 epochs, batch 32, lr 1e-5, wd 0.01, seed 3401,
per-epoch order numpy default_rng([3401, epoch]), last partial batch kept; checkpoint = final epoch (no selection on the test
fold, unlike universal_trainer.py:414-418). Resume state every STATE_EVERY epochs.
Scorers on every test window of the fitted model (eval, no grad, consecutive batches of 32 in canonical order):
  official_att    universal_trainer._evaluate_contrastive verbatim (target = attended, negative = unattended): pred = pA > pB,
                  pA / pB = in-batch softmax diagonals of ClipLoss.get_probabilities, every label 1 (universal_trainer.py:355-378).
  official_ign    the same with the slots swapped (target = unattended); a scorer blind to the slot gives 1 - official_att.
  official_noise  official_att with the EEG replaced by Gaussian noise matched to each window's per-channel mean / std.
  blind_real / blind_noise   external_mindmix.blind_margin (order-symmetrised pair margin; candidates in label-free ear order
                  left, right), oriented to attended-minus-unattended only after scoring; correct = margin > 0 (ties 1/2).
  clip_real / clip_noise     the official ClipLoss(fused_eeg, aligned_target) per scored batch (real vs noise EEG).
  embeddings      eeg_proj(eeg_encoder(.)) for real and noise EEG, audio_proj(wav2vec2 mean) of attended / unattended (float16).
Unit records carry no accuracy; per-subject results are written to results/auditory_alignment_v3/paper/kul_mindmix/ by
--summarize only after every plan unit is complete.

CLI: --make-binding | --prepare | --make-revision | --make-plan (CPU, srun on the evidence allocation) | --smoke | --worker --lane A|B
[--max-units N] | --unit ID | --probe-unit ID (GPU) | --summarize (CPU).
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import fcntl
import gc
import hashlib
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
from ..aln42 import external_mindmix as XM

OUT = Path(core.OUT) / 'paper' / 'kul_v1'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/paper/kul_v1')
RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/paper/kul_mindmix'
BINDING = OUT / 'KUL_MINDMIX_BINDING.json'
INVENTORY = OUT / 'inventory.json'
PLAN = OUT / 'plan_v2.json'                                  # active plan (revision 01)
PLAN_V1 = OUT / 'plan_v1_superseded.json'                    # the 160-unit v1 plan, kept unchanged (renamed only)
PLAN_V1_SHA = '99775e50e7b55b509b584aed23fb53b730776863c88a5c9a8eb7b94377cd2aa7'
REVISION = OUT / 'KUL_MINDMIX_REVISION_01.json'
PROTOCOL_FOLDS = {'P1': (0, 1, 2, 3, 4), 'P2': (0, 1)}
KUL_DIR = Path(XM.PUB) / 'kul_aad' / 'zenodo_4004271'
KUL_RECORD = Path(XM.PUB) / 'kul_aad' / 'zenodo_record_4004271.json'
SUBJECTS = tuple(f'S{i}' for i in range(1, 17))
FS_KUL, FS_EEG, FS_WAV, FS_AUD, WIN_S = 128, 200, 44100, 16000, 2.0
EEG_RS, AUD_RS = (25, 16), (160, 441)                       # resample_poly up/down: 128 -> 200 Hz, 44.1 -> 16 kHz
LE, LA = int(WIN_S * FS_EEG), int(WIN_S * FS_AUD)
P1_KFOLD = {'n_splits': 5, 'shuffle': True, 'random_state': 42}
N_FOLDS, P2_TRIALS_PER_FOLD = 5, 4
SEED, EPOCHS, BATCH, LR, WD = XM.SEED, XM.EPOCHS, XM.BATCH, XM.LR, XM.WD
STATE_EVERY = 10
SMOKE = {'epochs': 2, 'score_windows': 64}
NOISE_SEED = SEED + 100000                                   # + plan row index
LANES = {'A': ('c3_s35pkA', 's35_paper_kul_a', 'slurm/aln35_paper_kul_a.sbatch', 'P1'),
         'B': ('c3_s35pkB', 's35_paper_kul_b', 'slurm/aln35_paper_kul_b.sbatch', 'P2')}
KUL_ARGV = ['universal_eeg_finetune.py', '--dataset', 'KUL', '--data_path', '<KUL_trail>', '--strategy', 'multimodal_real',
            '--fusion_method', 'calra', '--pretrained_model', str(XM.CKPT), '--batch_size', str(BATCH), '--epochs', str(EPOCHS),
            '--lr', str(LR), '--weight_decay', str(WD), '--seed', str(SEED)]
read, write, sha, digest = XM.read, XM.write, XM.sha, XM.digest


# ----------------------------------------------------------------------------------------------------------- binding / plan
def binding_body():
    rec = read(KUL_RECORD)
    return {
        'version': 'PAPER_KUL_MINDMIX_BINDING_v1',
        'instruction': 'W6 KUL download + attack (researcher-approved); coordinator specification of 2026-10-22',
        'data': {'zenodo_record': 4004271, 'zenodo_version': rec['metadata']['version'], 'doi': rec['doi'],
                 'license': rec['metadata']['license'], 'dir': str(KUL_DIR), 'record_json': str(KUL_RECORD),
                 'record_json_sha256': sha(KUL_RECORD),
                 'md5': {f['key']: f['checksum'].split(':', 1)[1] for f in rec['files'] if f['key'].endswith(('.mat', '.zip'))},
                 'subjects': list(SUBJECTS),
                 'note': 'v2.0 as available to MindMix; the 2026-07-17 v2.1 (record 21415059) corrects a 70 ms EEG-stimulus '
                         'misalignment and is not used here'},
        'trials': 'all 20 trials per subject incl. experiment-3 repetitions; TrialID, experiment, part, repetition, condition, '
                  'attended_ear, attended_track and stimuli recorded per trial and per window',
        'audio': {'files': "per trial the presented wavs named in the trial's stimuli field: stimuli[0] = left ear, stimuli[1] = "
                           "right ear; attended = stimuli[0] if attended_ear == 'L' else stimuli[1]; unattended = the other "
                           "(asserted: attended name contains track<attended_track>, both names contain the trial condition)",
                  'read': 'stimuli.zip member bytes in memory, never extracted; scipy.io.wavfile; int16 / 32768; mono asserted',
                  'resample': 'scipy.signal.resample_poly(x, 160, 441): 44.1 -> 16 kHz', 'alignment': 'wav sample 0 = trial start',
                  'normalisation': 'per window x / max(|x|.max(), 1e-8)'},
        'eeg': {'source': 'trials[i].RawData.EegData (samples x 64), RawData.Channels == 1..64 and FileHeader.SampleRate == 128 '
                          'asserted; channels as provided (already 0.5 Hz high-pass + MWF); BioSemi-64 order = the official '
                          'ch_names list, which the official encoder does not consume',
                'resample': 'scipy.signal.resample_poly(X, 25, 16, axis=time) per trial: 128 -> 200 Hz, float32 after resampling',
                'normalisation': 'per window per channel (x - mean) / (std + 1e-8)  [as the DTU binding]'},
        'windows': {'length_s': WIN_S, 'eeg_samples': LE, 'audio_samples': LA, 'hop_s': WIN_S,
                    'rule': 'window k covers [2k, 2k + 2) s from trial start; n = floor(min(EEG, attended wav, unattended wav) '
                            'duration / 2 s); trailing partial window dropped',
                    'canonical_order': 'TrialID ascending, then window index'},
        'protocols': {'P1': {'name': 'paper split', 'split': f'per subject sklearn KFold({P1_KFOLD}) over the canonical windows '
                                                             '(official universal_eeg_finetune.py:492-498)', 'folds': N_FOLDS},
                      'P2': {'name': 'trial-held-out', 'split': 'per subject 5 folds; fold f tests the 4 trials at TrialID-rank '
                                                                '4f..4f+3 (fixed order by trial index); no window of a test '
                                                                'trial in training', 'folds': N_FOLDS}},
        'model': {'code': f'MindMix commit {XM.MM_COMMIT}, unmodified, imported from the pinned checkout',
                  'construction': 'aln42.external_mindmix build route (official EEGEncoder, Wav2Vec2Model facebook/wav2vec2-base '
                                  f'@ {XM.W2V_REV}, create_model multimodal_real / calra, official load_pretrained_weights, '
                                  'wav2vec2 pos-conv weight_g / weight_v rename) with the KUL README CLI',
                  'checkpoint': str(XM.CKPT), 'checkpoint_sha256': XM.CKPT_SHA, 'cli': KUL_ARGV},
        'recipe': {'epochs': EPOCHS, 'batch_size': BATCH, 'lr': LR, 'weight_decay': WD, 'seed': SEED,
                   'trainer': 'official MultimodalRealTrainer.setup_optimizer / train_epoch / update_learning_rate',
                   'order': 'per epoch numpy default_rng([3401, epoch]) permutation of the unit train windows; consecutive '
                            'batches of 32, last partial batch kept; target = attended, negative = unattended',
                   'checkpoint': 'final epoch 50; no early stopping and no selection on any fold',
                   'units': 'one fine-tune per protocol x subject x fold from the released checkpoint'},
        'scorers': {'official_att': 'universal_trainer._evaluate_contrastive verbatim: pA / pB in-batch softmax diagonals, '
                                    'pred = pA > pB, every label 1; consecutive batches of 32 test windows in canonical order',
                    'official_ign': 'the same with target = unattended, negative = attended',
                    'official_noise': 'official_att with Gaussian-noise EEG matched to each window per-channel mean / std '
                                      f'(torch CPU generator seed {NOISE_SEED} + plan row index)',
                    'blind_real': 'external_mindmix.blind_margin, candidates in ear order (left, right), oriented attended-minus-'
                                  'unattended after scoring; correct = margin > 0, ties count 1/2',
                    'blind_noise': 'blind_real with the noise EEG of official_noise',
                    'clip_loss': 'official ClipLoss(fused_eeg, aligned_target) per scored batch, real and noise EEG'},
        'reporting': 'per subject accuracy of each scorer per protocol (pooled over the 5 folds; each window is tested once) '
                     'and mean fold accuracy, ClipLoss real vs noise; written to results/auditory_alignment_v3/paper/kul_mindmix/ '
                     'only after every plan unit is complete; unit records carry no accuracy',
    }


def make_binding():
    body = binding_body()
    if BINDING.exists():
        old = read(BINDING)
        assert all(old[k] == v for k, v in body.items()) and old['frozen'] is True, 'binding drift'
    else:
        write(BINDING, {**body, 'frozen': True, 'created': datetime.now().astimezone().isoformat()}); BINDING.chmod(0o444)
    print('KUL binding', sha(BINDING), flush=True)


def md5_of(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def prepare():
    """CPU: md5 check, 16 kHz audio cache from stimuli.zip (in memory), 200 Hz EEG cache per subject, trial inventory."""
    import zipfile
    import scipy.io as sio
    import scipy.io.wavfile as W
    from scipy.signal import resample_poly
    b = read(BINDING); assert b['frozen'] is True
    md5 = {}
    for k, want in sorted(b['data']['md5'].items()):
        got = md5_of(KUL_DIR / k); assert got == want, (k, got, want); md5[k] = got
    adir, edir = STORE / 'input_v1' / 'audio', STORE / 'input_v1' / 'eeg'
    adir.mkdir(parents=True, exist_ok=True, mode=0o700); edir.mkdir(parents=True, exist_ok=True, mode=0o700)
    audio = {}
    with zipfile.ZipFile(KUL_DIR / 'stimuli.zip') as z:
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            if not info.filename.endswith('.wav'):
                continue
            name = info.filename.split('/')[-1]; raw = z.read(info.filename)
            fs, x = W.read(io.BytesIO(raw)); assert fs == FS_WAV and x.dtype == np.int16 and x.ndim == 1, (name, fs, x.dtype, x.shape)
            y = resample_poly(x.astype(np.float64) / 32768.0, *AUD_RS).astype(np.float32)
            path = adir / (name[:-4] + '.npy'); tmp = path.with_name(path.name + '.tmp.npy')
            np.save(tmp, y); os.replace(tmp, path)
            audio[name] = {'member_md5': hashlib.md5(raw).hexdigest(), 'n44': int(len(x)), 'n16': int(len(y)), 'cache': str(path),
                           'cache_sha256': sha(path)}
            print('audio', name, len(x), len(y), flush=True)
    trials = []
    for s in SUBJECTS:
        m = sio.loadmat(KUL_DIR / f'{s}.mat', squeeze_me=True, struct_as_record=False)
        tr = sorted(list(m['trials']), key=lambda t: int(t.TrialID)); assert len(tr) == 20, (s, len(tr))
        arrs = {}
        for pos, t in enumerate(tr):
            assert int(t.FileHeader.SampleRate) == FS_KUL and list(np.atleast_1d(t.RawData.Channels).astype(int)) == list(range(1, 65))
            X = np.asarray(t.RawData.EegData, dtype=np.float64); assert X.ndim == 2 and X.shape[1] == 64, X.shape
            assert str(t.subject) == s and np.isfinite(X).all()
            left, right = [str(v) for v in t.stimuli]; ear, cond = str(t.attended_ear), str(t.condition)
            att, ign = (left, right) if ear == 'L' else (right, left); assert ear in ('L', 'R')
            assert f'track{int(t.attended_track)}' in att and cond in att and cond in ign and att != ign, (s, t.TrialID, att, ign)
            Y = resample_poly(X.T, *EEG_RS, axis=1).astype(np.float32)
            arrs[f'eeg__{int(t.TrialID)}'] = Y
            n = int(min(Y.shape[1] // LE, audio[att]['n16'] // LA, audio[ign]['n16'] // LA))
            trials.append({'subject': s, 'trial_id': int(t.TrialID), 'rank': pos, 'experiment': int(t.experiment), 'part': int(t.part),
                           'repetition': int(t.repetition), 'condition': cond, 'attended_ear': ear, 'attended_track': int(t.attended_track),
                           'stimuli': [left, right], 'attended_wav': att, 'unattended_wav': ign, 'n128': int(X.shape[0]),
                           'n200': int(Y.shape[1]), 'n_windows': n,
                           'limit': 'eeg' if Y.shape[1] // LE <= min(audio[att]['n16'], audio[ign]['n16']) // LA else 'audio'})
        path = edir / f'{s}.npz'; tmp = path.with_name(path.name + '.tmp.npz')
        np.savez(tmp, **arrs); os.replace(tmp, path)
        print('eeg', s, sum(t['n_windows'] for t in trials if t['subject'] == s), 'windows', flush=True)
        del m, arrs; gc.collect()
    eeg_sha = {s: sha(edir / f'{s}.npz') for s in SUBJECTS}
    write(INVENTORY, {'binding_sha256': sha(BINDING), 'md5_verified': md5, 'audio': audio, 'eeg_cache_sha256': eeg_sha,
                      'trials': trials, 'created': datetime.now().astimezone().isoformat()})
    print('inventory', sha(INVENTORY), len(trials), 'trials', sum(t['n_windows'] for t in trials), 'windows', flush=True)


def subject_trials(inv, s):
    return sorted((t for t in inv['trials'] if t['subject'] == s), key=lambda t: t['trial_id'])


def canonical_windows(trials):
    return [(t['trial_id'], k) for t in trials for k in range(t['n_windows'])]


def split(trials, protocol, fold):
    """(train, test) index arrays into canonical_windows(trials)."""
    w = canonical_windows(trials); n = len(w)
    if protocol == 'P1':
        from sklearn.model_selection import KFold
        tr, te = list(KFold(**P1_KFOLD).split(np.arange(n)))[fold]
        return np.sort(tr), np.sort(te)
    assert protocol == 'P2'
    test_ids = {t['trial_id'] for t in trials if P2_TRIALS_PER_FOLD * fold <= t['rank'] < P2_TRIALS_PER_FOLD * (fold + 1)}
    te = np.array([i for i, (tid, _) in enumerate(w) if tid in test_ids]); tr = np.array([i for i, (tid, _) in enumerate(w) if tid not in test_ids])
    return tr, te


def sources():
    repo = Path(core.REPO)
    out = {str(p.relative_to(repo)): sha(p) for p in (Path(__file__), repo / 'auditory_alignment_v3/aln42/external_mindmix.py')}
    out.update({f'mindmix@{XM.MM_COMMIT[:8]}/{f}': sha(XM.MM_REPO / f) for f in XM.MM_FILES})
    return out


P2_CAVEATS = ('P2 removes trial fingerprints (no window of a test trial is trained on) but not audio overlap (window-level '
              'counts in p2_audio_overlap; replay identity in repetition_audio_identity). Fold 0 tests the experiment-1 '
              'trials: every test window has its exact audio pair in the experiment-2 training trials with the other talker '
              'attended, and the experiment-3 repetitions in training replay the first 2 min (62 windows per trial) of the '
              'same story parts with the same attended track and ear. Fold 1 tests the experiment-2 trials: every test window '
              'has its audio pair in training (experiment 1, and the repetitions for the first 2 min) with the other talker '
              'attended and none with the same attention, so a model keyed to audio content rather than to attention is pushed '
              'below chance there (strongest shortcut check). Folds 2-4 (repetition trials, not run) would have same-attention '
              'replays in training.')


def p2_overlap(inv):
    """Test windows of the run P2 folds whose audio (exact wav incl. condition / same story part ignoring condition) occurs at
    the same story offset in the unit's training windows with the same or the swapped attended talker (rep_ = story replay)."""
    def key(name, cond):
        n = name[:-4]; n = n[4:] if n.startswith('rep_') else n
        part, track, c = n.split('_'); return (part, track, c) if cond else (part, track)
    out = {}
    for f in PROTOCOL_FOLDS['P2']:
        tot = {'test_trials': 0, 'test_windows': 0}
        for s in SUBJECTS:
            trials = subject_trials(inv, s); w = canonical_windows(trials); tr, te = split(trials, 'P2', f)
            by = {t['trial_id']: t for t in trials}

            def wk(i, cond):
                tid, k = w[i]; t = by[tid]
                return key(t['attended_wav'], cond), key(t['unattended_wav'], cond), k
            tot['test_trials'] += len({w[i][0] for i in te}); tot['test_windows'] += len(te)
            for cond, tag in ((True, 'same_wavs'), (False, 'same_story_parts')):
                train = {wk(i, cond) for i in tr}
                for i in te:
                    a, u, k = wk(i, cond)
                    tot[f'{tag}_same_attention'] = tot.get(f'{tag}_same_attention', 0) + int((a, u, k) in train)
                    tot[f'{tag}_swapped_attention'] = tot.get(f'{tag}_swapped_attention', 0) + int((u, a, k) in train)
        out[str(f)] = tot
    return out


def rep_identity(inv):
    """max |rep_partX_trackY_C - partX_trackY_C[:len(rep)]| on the 16 kHz caches (is the repetition a byte replay?)."""
    out = {}
    for name, rec in sorted(inv['audio'].items()):
        if name.startswith('rep_'):
            r = np.load(rec['cache']); p = np.load(inv['audio'][name[4:]]['cache'])[:len(r)]
            out[name] = {'n16': int(len(r)), 'max_abs_diff_vs_story_start': float(np.abs(r - p).max()),
                         'corr': float(np.corrcoef(r, p)[0, 1])}
    return out


def make_revision():
    """Revision 01 (frozen): P2 folds 0-1 only; written only while no unit has trained."""
    assert sha(PLAN_V1) == PLAN_V1_SHA and not (OUT / 'plan.json').exists(), 'v1 plan must be kept as plan_v1_superseded.json'
    assert not list((OUT / 'units').glob('*.json')) and not list((STORE / 'units').glob('*')), 'a unit already exists'
    inv = read(INVENTORY)
    v1_receipts = sorted(str(p) for p in (OUT / 'probes').glob('*/receipt.json') if read(p).get('plan_sha256') == PLAN_V1_SHA)
    body = {'version': 'PAPER_KUL_MINDMIX_REVISION_01',
            'decision': 'coordinator 2026-10-22 within the researcher-approved W6 budget: run P1 at all 5 folds and P2 at '
                        'folds 0-1 only (32 P2 units); recorded revision, nothing has trained',
            'reasons': ['approved W6 budget ~20 GPU-h (smoke 1056212 projected 31.8 A100 GPU-h for the 160-unit v1 plan)',
                        'P2 folds 0-1 cover all 16 non-repetition trials (experiments 1 and 2; 1564 of 2308 windows per subject)',
                        'fold 1 = experiment-2 trials with swapped attention relative to the experiment-1 trials in training: '
                        'the strongest shortcut check'],
            'change': {'protocol_folds': {k: list(v) for k, v in PROTOCOL_FOLDS.items()}, 'units': 16 * sum(len(v) for v in PROTOCOL_FOLDS.values())},
            'unchanged': 'binding KUL_MINDMIX_BINDING.json (sha256 below) in force for everything else; unit ids, window '
                         'geometry, splits, recipe and scorers identical to v1',
            'binding_sha256': sha(BINDING), 'inventory_sha256': sha(INVENTORY),
            'superseded_plan': {'path': str(PLAN_V1), 'sha256': PLAN_V1_SHA, 'units': 160},
            'superseded_smoke_receipts': v1_receipts,
            'smoke_gate': 'the v1 smoke receipt binds the v1 plan sha256 and does not gate plan_v2; a new smoke against plan_v2 is required',
            'p2_caveats': P2_CAVEATS, 'p2_audio_overlap': p2_overlap(inv), 'repetition_audio_identity': rep_identity(inv)}
    if REVISION.exists():
        old = read(REVISION); assert all(old[k] == v for k, v in body.items()) and old['frozen'] is True, 'revision drift'
    else:
        write(REVISION, {**body, 'frozen': True, 'created': datetime.now().astimezone().isoformat()}); REVISION.chmod(0o444)
    print('KUL revision 01', sha(REVISION), json.dumps(body['p2_audio_overlap']), flush=True)


def make_plan():
    import sklearn
    b = read(BINDING); assert b['frozen'] is True
    rv = read(REVISION); assert rv['frozen'] is True and rv['binding_sha256'] == sha(BINDING)
    inv = read(INVENTORY); assert inv['binding_sha256'] == sha(BINDING) and rv['inventory_sha256'] == sha(INVENTORY)
    rows = []
    for protocol in ('P1', 'P2'):
        for fold in PROTOCOL_FOLDS[protocol]:                # fold-major: a fold is complete for every subject before the next
            for s in SUBJECTS:
                tr, te = split(subject_trials(inv, s), protocol, fold)
                body = {'method': 'MindMix_official_released_checkpoint_KUL', 'protocol': protocol, 'subject': s, 'fold': fold, 'seed': SEED}
                rows.append({**body, 'id': 'KULMM_' + digest(body, 16), 'index': len(rows), 'n_train': int(len(tr)), 'n_test': int(len(te))})
    v1 = {r['id']: r for r in read(PLAN_V1)['rows']}
    assert all(v1[r['id']] == r for r in rows), 'revision rows must equal their v1 rows'
    body = {'version': 'PAPER_KUL_MINDMIX_v2', 'rows': rows, 'sources': sources(), 'binding_sha256': sha(BINDING),
            'revision_sha256': sha(REVISION), 'superseded_plan_sha256': PLAN_V1_SHA, 'protocol_folds': {k: list(v) for k, v in PROTOCOL_FOLDS.items()},
            'inventory_sha256': sha(INVENTORY), 'checkpoint_sha256': XM.CKPT_SHA, 'mindmix_commit': XM.MM_COMMIT,
            'wav2vec2_revision': XM.W2V_REV, 'sklearn_version': sklearn.__version__, 'store': str(STORE),
            'recipe': {'epochs': EPOCHS, 'batch_size': BATCH, 'lr': LR, 'weight_decay': WD, 'seed': SEED, 'state_every': STATE_EVERY},
            'smoke': SMOKE, 'lanes': {k: list(v) for k, v in LANES.items()}, 'notes': {'p2_caveats': P2_CAVEATS,
            'p2_audio_overlap': rv['p2_audio_overlap']}}
    if PLAN.exists():
        old = read(PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        write(PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); PLAN.chmod(0o444)
    print('KUL MindMix plan', len(rows), sha(PLAN), flush=True)
    for p in ('P1', 'P2'):
        r = [x for x in rows if x['protocol'] == p]
        print(p, len(r), 'units; train windows', sum(x['n_train'] for x in r), 'test windows', sum(x['n_test'] for x in r), flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'source drift'
    assert sha(BINDING) == plan['binding_sha256'] and read(BINDING)['frozen'] is True, 'binding drift'
    assert sha(REVISION) == plan['revision_sha256'] and read(REVISION)['frozen'] is True, 'revision drift'
    assert sha(INVENTORY) == plan['inventory_sha256'], 'inventory drift'


# ----------------------------------------------------------------------------------------------------------- inputs / model
class SubjectInputs:
    def __init__(self, inv, s):
        self.trials = subject_trials(inv, s); self.windows = canonical_windows(self.trials)
        self.by_id = {t['trial_id']: t for t in self.trials}
        path = STORE / 'input_v1' / 'eeg' / f'{s}.npz'; assert sha(path) == inv['eeg_cache_sha256'][s], 'eeg cache drift'
        with np.load(path) as z:
            self.E = {int(k[5:]): z[k] for k in z.files}
        self.A = {}
        for t in self.trials:
            for name in (t['attended_wav'], t['unattended_wav']):
                if name not in self.A:
                    rec = inv['audio'][name]; assert sha(rec['cache']) == rec['cache_sha256'], 'audio cache drift'
                    self.A[name] = np.load(rec['cache'])

    def arrays(self, idx):
        E = np.empty((len(idx), 64, LE), np.float32); A = np.empty((len(idx), LA), np.float32); M = np.empty((len(idx), LA), np.float32)
        meta = {k: [] for k in ('trial_id', 'window', 'experiment', 'repetition', 'condition', 'att_left')}
        for j, i in enumerate(idx):
            tid, k = self.windows[i]; t = self.by_id[tid]
            x = self.E[tid][:, k * LE:(k + 1) * LE]; assert x.shape[1] == LE
            E[j] = (x - x.mean(1, keepdims=True)) / (x.std(1, keepdims=True) + 1e-8)
            for out, name in ((A, t['attended_wav']), (M, t['unattended_wav'])):
                a = self.A[name][k * LA:(k + 1) * LA]; assert len(a) == LA
                out[j] = a / max(float(np.abs(a).max()), 1e-8)
            for key, v in (('trial_id', tid), ('window', k), ('experiment', t['experiment']), ('repetition', t['repetition']),
                           ('condition', t['condition']), ('att_left', t['attended_ear'] == 'L')):
                meta[key].append(v)
        return E, A, M, {k: np.asarray(v) for k, v in meta.items()}


def build_model(dev):
    """external_mindmix.build_model with the KUL README CLI (dataset / data_path do not enter model construction)."""
    import torch
    UEF, UM, UT = XM.official()
    from transformers import Wav2Vec2Model
    old = sys.argv; sys.argv = list(KUL_ARGV)
    try:
        args = UEF.get_args()
    finally:
        sys.argv = old
    UEF.set_random_seed(args.seed)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        eeg = UEF.EEGEncoder(args, dev)
        audio = Wav2Vec2Model.from_pretrained('facebook/wav2vec2-base', revision=XM.W2V_REV).to(dev)
        model = UM.create_model(args.strategy, eeg, audio, args.fusion_method, num_classes=2, use_auditory_type=args.use_auditory_type)
        model.to(dev)
        model.load_pretrained_weights(args.pretrained_model)
    skipped = [l for l in buf.getvalue().splitlines() if l.startswith('Skipped')]
    assert sorted(skipped) == sorted(['Skipped: audio_model.encoder.pos_conv_embed.conv.weight_g (shape mismatch or not found)',
                                      'Skipped: audio_model.encoder.pos_conv_embed.conv.weight_v (shape mismatch or not found)',
                                      'Skipped: classifier.weight (shape mismatch or not found)',
                                      'Skipped: classifier.bias (shape mismatch or not found)']), skipped
    sd = XM.safe_load(args.pretrained_model)['model_state_dict']; msd = model.state_dict()
    for src_k, dst_k in XM.POS_RENAME.items():
        assert msd[dst_k].shape == sd[src_k].shape
        msd[dst_k] = sd[src_k]
    model.load_state_dict(msd)
    loaded = sum(int(torch.equal(model.state_dict()[k if not k.startswith(('eeg_model.', 'audio_model.')) else
                                                 k.replace('eeg_model.', 'eeg_encoder.').replace('audio_model.', 'audio_encoder.')].cpu(), v))
                 for k, v in sd.items() if k not in XM.POS_RENAME and not k.startswith('classifier.'))
    assert loaded == len(sd) - 4, loaded
    del sd, msd; gc.collect()
    return model, args, UT


def state_digest(model):
    h = hashlib.sha256()
    for k, v in sorted(model.state_dict().items()):
        h.update(k.encode()); h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


# ----------------------------------------------------------------------------------------------------------- unit
def run_unit(row, plan, probe=False):
    import torch
    t_all = time.time(); job = os.environ['SLURM_JOB_ID']
    dev = torch.device('cuda'); torch.cuda.reset_peak_memory_stats()
    assert sha(XM.CKPT) == XM.CKPT_SHA
    inv = read(INVENTORY); t0 = time.time()
    si = SubjectInputs(inv, row['subject'])
    tr, te = split(si.trials, row['protocol'], row['fold'])
    assert len(tr) == row['n_train'] and len(te) == row['n_test'] and not set(tr.tolist()) & set(te.tolist())
    if row['protocol'] == 'P2':
        assert not {si.windows[i][0] for i in tr} & {si.windows[i][0] for i in te}
    score_idx = tr[:SMOKE['score_windows']] if probe else te          # the probe never scores test windows
    Etr, Atr, Mtr, _ = si.arrays(tr)
    Etr, Atr, Mtr = (torch.from_numpy(x).to(dev) for x in (Etr, Atr, Mtr))
    t_prep = time.time() - t0
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    t0 = time.time(); model, args, UT = build_model(dev); t_build = time.time() - t0
    trainer = UT.create_trainer(args.strategy, model, dev, args); trainer.setup_optimizer()
    n_tr = len(tr); n_batches = int(np.ceil(n_tr / BATCH))

    class _L:  # iterable with len() for the official train_epoch
        def __init__(self, ep):
            self.ep = ep

        def __iter__(self):
            perm = np.random.default_rng([SEED, self.ep]).permutation(n_tr)
            for k in range(0, n_tr, BATCH):
                b = torch.from_numpy(perm[k:k + BATCH]).to(dev)
                yield Etr[b], Atr[b], Mtr[b], torch.ones(len(b), device=dev)

        def __len__(self):
            return n_batches
    epochs = SMOKE['epochs'] if probe else EPOCHS
    state_path = dest / 'train_state.pt'; history, start = [], 0
    if state_path.exists() and not probe:
        st = torch.load(state_path, map_location='cpu', weights_only=False)
        assert st['plan_sha256'] == sha(PLAN) and st['row_id'] == row['id']
        model.load_state_dict(st['model']); trainer.optimizer.load_state_dict(st['optimizer'])
        trainer.warmup_scheduler.load_state_dict(st['warmup']); trainer.scheduler.load_state_dict(st['scheduler'])
        torch.set_rng_state(st['rng_cpu']); torch.cuda.set_rng_state(st['rng_cuda']); history, start = st['history'], st['epoch'] + 1
    t0 = time.time()
    for ep in range(start, epochs):
        te_ = time.time(); lr = trainer.optimizer.param_groups[0]['lr']
        _, _, tclip = trainer.train_epoch(_L(ep), ep); trainer.update_learning_rate(ep)
        history.append({'epoch': ep + 1, 'lr': lr, 'clip_loss': float(tclip), 'seconds': round(time.time() - te_, 2)})
        print(row['id'], 'epoch', ep + 1, history[-1], flush=True)
        if not probe and (ep + 1) % STATE_EVERY == 0 and ep + 1 < epochs:
            torch.save({'plan_sha256': sha(PLAN), 'row_id': row['id'], 'epoch': ep, 'model': model.state_dict(),
                        'optimizer': trainer.optimizer.state_dict(), 'warmup': trainer.warmup_scheduler.state_dict(),
                        'scheduler': trainer.scheduler.state_dict(), 'rng_cpu': torch.get_rng_state(), 'rng_cuda': torch.cuda.get_rng_state(),
                        'history': history}, state_path.with_suffix('.tmp'))
            os.replace(state_path.with_suffix('.tmp'), state_path)
    t_train = time.time() - t0
    del Etr, Atr, Mtr; torch.cuda.empty_cache()
    final_digest = state_digest(model)
    # ---------------- scoring (eval, no grad, consecutive batches of BATCH in canonical order)
    model.eval(); t0 = time.time()
    E, A, M, meta = si.arrays(score_idx)
    gen = torch.Generator(device='cpu').manual_seed(NOISE_SEED + row['index'])
    nrm = torch.nn.functional.normalize

    def official(e, tgt, neg):
        fe, ft, fn = model.forward_contrastive(e, tgt, neg)
        pA = model.clip_loss.get_probabilities(fe, ft).diagonal(); pB = model.clip_loss.get_probabilities(fe, fn).diagonal()
        return (pA > pB), pA, pB, model.clip_loss(fe, ft)

    def audio_emb(a):
        return model.audio_proj(model.audio_encoder(a).last_hidden_state.mean(1))
    keys = ('official_att', 'pA_att', 'pB_att', 'official_ign', 'official_noise', 'blind_real', 'blind_noise',
            'eeg_emb', 'eeg_emb_noise', 'att_emb', 'ign_emb')
    out = {k: [] for k in keys}; clip_real, clip_noise, batch_n = [], [], []
    checks = {}
    with torch.no_grad():
        for k in range(0, len(score_idx), BATCH):
            e = torch.from_numpy(E[k:k + BATCH]).to(dev); at = torch.from_numpy(A[k:k + BATCH]).to(dev); ig = torch.from_numpy(M[k:k + BATCH]).to(dev)
            z = torch.randn(e.shape, generator=gen).to(dev)
            z = (z - z.mean(-1, keepdim=True)) / (z.std(-1, keepdim=True) + 1e-8)
            en = z * e.std(-1, keepdim=True) + e.mean(-1, keepdim=True)
            left = torch.from_numpy(meta['att_left'][k:k + BATCH]).to(dev)[:, None]
            c1 = torch.where(left, at, ig); c2 = torch.where(left, ig, at)            # label-free ear order: left, right
            sign = torch.where(left[:, 0], 1.0, -1.0).double()
            pa, A_, B_, la = official(e, at, ig); pi, _, _, _ = official(e, ig, at); pn, _, _, ln = official(en, at, ig)
            br = XM.blind_margin(model, e, c1, c2); bn = XM.blind_margin(model, en, c1, c2)
            if k == 0:
                checks['swap_max_abs'] = float((br + XM.blind_margin(model, e, c2, c1)).abs().max())
                m4 = min(4, len(e))
                checks['batch_invariance_max_abs'] = float((torch.cat([XM.blind_margin(model, e[j:j + 1], c1[j:j + 1], c2[j:j + 1]) for j in range(m4)])
                                                            - br[:m4]).abs().max())
            for key, v in (('official_att', pa), ('pA_att', A_), ('pB_att', B_), ('official_ign', pi), ('official_noise', pn),
                           ('blind_real', br.double() * sign), ('blind_noise', bn.double() * sign)):
                out[key].append(v.double().cpu().numpy())
            for key, v in (('eeg_emb', model.eeg_proj(model.eeg_encoder(e))), ('eeg_emb_noise', model.eeg_proj(model.eeg_encoder(en))),
                           ('att_emb', audio_emb(at)), ('ign_emb', audio_emb(ig))):
                out[key].append(v.float().cpu().numpy().astype(np.float16))
            clip_real.append(float(la)); clip_noise.append(float(ln)); batch_n.append(len(e))
    t_score = time.time() - t0
    arrays = {k: np.concatenate(v) for k, v in out.items()}
    arrays.update({f'meta_{k}': v for k, v in meta.items()})
    arrays.update({'window_index': np.asarray(score_idx), 'clip_real': np.array(clip_real), 'clip_noise': np.array(clip_noise),
                   'batch_n': np.array(batch_n)})
    checks['scores_finite'] = bool(all(np.isfinite(arrays[k]).all() for k in ('pA_att', 'pB_att', 'blind_real', 'blind_noise', 'clip_real', 'clip_noise')))
    checks['swap_ok'] = checks['swap_max_abs'] < 1e-3; checks['batch_invariance_ok'] = checks['batch_invariance_max_abs'] < 1e-2
    checks['split_disjoint_ok'] = True
    np.savez_compressed(dest / 'scores.npz', **arrays)
    sec = {'prepare': round(t_prep, 1), 'build': round(t_build, 1), 'train': round(t_train, 1), 'score': round(t_score, 1),
           'total': round(time.time() - t_all, 1)}
    steady = [h['seconds'] for h in history[1:]] or [h['seconds'] for h in history]
    rec = {'status': 'complete' if all(v for k, v in checks.items() if k.endswith(('_ok', 'finite'))) else 'check_failed',
           'row': row, 'probe': probe, 'plan_sha256': sha(PLAN), 'binding_sha256': sha(BINDING), 'dest': str(dest),
           'npz_sha256': sha(dest / 'scores.npz'), 'final_state_digest': final_digest, 'epochs_run': len(history), 'history': history,
           'final_train_clip_loss': history[-1]['clip_loss'] if history else None, 'n_train_windows': int(n_tr),
           'n_scored_windows': int(len(score_idx)), 'scored': 'train_side_probe' if probe else 'test', 'seconds': sec,
           'epoch_seconds_steady': float(np.median(steady)) if steady else None,
           'score_seconds_per_window': t_score / max(1, len(score_idx)), 'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20,
           'device': torch.cuda.get_device_name(0), 'job': job, 'checks': checks}
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    if not probe and state_path.exists():
        state_path.unlink()
    print(row['id'], row['protocol'], row['subject'], 'fold', row['fold'], rec['status'], sec, flush=True)
    assert rec['status'] == 'complete', checks
    return rec


# ----------------------------------------------------------------------------------------------------------- smoke / fleet
def smoke(plan):
    job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': sha(PLAN), 'units': []}
    try:
        row = plan['rows'][0]
        assert subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--probe-unit', row['id']]).returncode == 0
        rec = read(OUT / 'probes' / job / 'units' / f'{row["id"]}.json')
        assert rec['status'] == 'complete' and rec['scored'] == 'train_side_probe'
        per_win_epoch = rec['epoch_seconds_steady'] / rec['n_train_windows']
        overhead = rec['seconds']['build'] + rec['seconds']['prepare']

        def hours(r):
            return (per_win_epoch * r['n_train'] * EPOCHS + rec['score_seconds_per_window'] * r['n_test'] + overhead) / 3600
        proj = {p: sum(hours(r) for r in plan['rows'] if r['protocol'] == p) for p in ('P1', 'P2')}
        proj_fold = {p: {f: sum(hours(r) for r in plan['rows'] if r['protocol'] == p and r['fold'] == f) for f in PROTOCOL_FOLDS[p]}
                     for p in ('P1', 'P2')}
        receipt['units'].append({'id': row['id'], 'seconds': rec['seconds'], 'epoch_seconds_steady': rec['epoch_seconds_steady'],
                                 'n_train_windows': rec['n_train_windows'], 'train_s_per_window_epoch': per_win_epoch,
                                 'score_s_per_window': rec['score_seconds_per_window'], 'peak_mb': rec['gpu_peak_mb'],
                                 'device': rec['device'], 'checks': rec['checks'],
                                 'projected_unit_hours_this_row': hours(row)})
        receipt.update(projected_gpu_hours=proj, projected_gpu_hours_by_fold=proj_fold, projected_total_gpu_hours=sum(proj.values()),
                       status='pass')
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'units'}, indent=1), flush=True)


def receipts():
    out = {'pass': [], 'other': []}
    if not (PLAN).exists():
        return out
    ps = sha(PLAN)
    for path in sorted((OUT / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('plan_sha256') == ps:
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status(lane='A'):
    name, lane_name, sbatch, protocol = LANES[lane]
    st = {'name': name, 'lane': lane_name, 'state': 'plan_missing', 'ready': 0, 'remaining': len(SUBJECTS) * len(PROTOCOL_FOLDS[protocol]), 'slots': 1, 'initial': [], 'submit': []}
    if not (PLAN).exists():
        return st
    plan = read(PLAN)
    left = [r for r in plan['rows'] if r['protocol'] == protocol and not (OUT / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(left)
    if not left:
        return {**st, 'state': 'complete'}
    if any((OUT / 'units' / f'{r["id"]}.FAILED.json').exists() for r in left):
        return {**st, 'state': 'failed_unit_review'}
    rec = receipts()
    if not rec['pass']:
        if rec['other']:
            return {**st, 'state': 'engineering_probe_failed'}
        return {**st, 'state': 'ready', 'ready': 1, 'submit': [sbatch, '--smoke']} if lane == 'A' else {**st, 'state': 'waiting_smoke'}
    return {**st, 'state': 'ready', 'ready': len(left), 'slots': 2, 'submit': [sbatch, '--worker', '--lane', lane, '--max-units', '4']}


def worker(plan, lane, max_units):
    assert receipts()['pass'], 'no passing smoke'
    protocol = LANES[lane][3]; done = 0
    for row in plan['rows']:
        if row['protocol'] != protocol:
            continue
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
                raise RuntimeError('KUL MindMix unit failed')
        done += 1
        if done >= max_units:
            break


# ----------------------------------------------------------------------------------------------------------- summary (CPU)
def summarize():
    plan = read(PLAN); verify(plan)
    missing = [r['id'] for r in plan['rows'] if not (OUT / 'units' / f'{r["id"]}.json').exists()]
    assert not missing, f'{len(missing)} units incomplete; results are written only after every plan unit is complete'
    acc_keys = ('official_att', 'official_ign', 'official_noise', 'blind_real', 'blind_noise')
    per = {p: {s: {'n_windows': 0, **{k: [] for k in acc_keys}, 'fold_acc': {k: [] for k in acc_keys}, 'clip_real': [], 'clip_noise': [],
                   'by_experiment': {}} for s in SUBJECTS} for p in ('P1', 'P2')}
    for row in plan['rows']:
        rec = read(OUT / 'units' / f'{row["id"]}.json'); assert rec['status'] == 'complete' and not rec['probe']
        assert rec['plan_sha256'] == sha(PLAN) and sha(Path(rec['dest']) / 'scores.npz') == rec['npz_sha256']
        with np.load(Path(rec['dest']) / 'scores.npz') as z:
            Z = {k: z[k] for k in z.files}
        corr = {k: Z[k].astype(float) for k in ('official_att', 'official_ign', 'official_noise')}
        corr['blind_real'] = (Z['blind_real'] > 0) + 0.5 * (Z['blind_real'] == 0)
        corr['blind_noise'] = (Z['blind_noise'] > 0) + 0.5 * (Z['blind_noise'] == 0)
        d = per[row['protocol']][row['subject']]; d['n_windows'] += len(Z['window_index'])
        for k in acc_keys:
            d[k].append(corr[k]); d['fold_acc'][k].append(float(corr[k].mean()))
        w = Z['batch_n'].astype(float)
        d['clip_real'].append((Z['clip_real'] * w).sum() / w.sum()); d['clip_noise'].append((Z['clip_noise'] * w).sum() / w.sum())
        for ex in sorted(set(Z['meta_experiment'].tolist())):
            m = Z['meta_experiment'] == ex
            e = d['by_experiment'].setdefault(str(ex), {k: [] for k in acc_keys})
            for k in acc_keys:
                e[k].append(corr[k][m])
    table = {}
    for p, subs in per.items():
        rows = {}
        for s, d in subs.items():
            rows[s] = {'n_windows': d['n_windows'], **{f'acc_{k}': float(np.concatenate(d[k]).mean()) for k in acc_keys},
                       **{f'fold_mean_acc_{k}': float(np.mean(d['fold_acc'][k])) for k in acc_keys},
                       'clip_loss_real': float(np.mean(d['clip_real'])), 'clip_loss_noise': float(np.mean(d['clip_noise'])),
                       'by_experiment': {ex: {f'acc_{k}': float(np.concatenate(v[k]).mean()) for k in acc_keys} for ex, v in d['by_experiment'].items()}}
        keys = [k for k in next(iter(rows.values())) if k not in ('by_experiment',)]
        group = {k: {'mean': float(np.mean([r[k] for r in rows.values()])), 'sd': float(np.std([r[k] for r in rows.values()])),
                     'min': float(np.min([r[k] for r in rows.values()])), 'n_subjects': len(rows)} for k in keys}
        table[p] = {'per_subject': rows, 'group': group}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / 'KUL_MINDMIX.json').write_text(json.dumps({'version': plan['version'], 'plan_sha256': sha(PLAN),
        'binding_sha256': plan['binding_sha256'], 'n_units': len(plan['rows']), 'results': table, 'definitions': __doc__}, indent=1) + '\n')
    lines = ['protocol\tsubject\tn_windows\t' + '\t'.join(f'acc_{k}' for k in acc_keys) + '\tclip_loss_real\tclip_loss_noise']
    for p in table:
        for s, r in table[p]['per_subject'].items():
            lines.append('\t'.join([p, s, str(r['n_windows'])] + [f'{r[f"acc_{k}"]:.4f}' for k in acc_keys]
                                   + [f'{r["clip_loss_real"]:.4f}', f'{r["clip_loss_noise"]:.4f}']))
    (RESULTS / 'kul_mindmix_per_subject.tsv').write_text('\n'.join(lines) + '\n')
    print(json.dumps({p: table[p]['group'] for p in table}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    for flag in ('make_binding', 'prepare', 'make_revision', 'make_plan', 'smoke', 'worker', 'summarize'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--probe-unit'); ap.add_argument('--lane', choices=sorted(LANES), default='A')
    ap.add_argument('--max-units', type=int, default=4)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_binding:
        make_binding(); return
    if a.prepare:
        prepare(); return
    if a.make_revision:
        make_revision(); return
    if a.make_plan:
        make_plan(); return
    plan = read(PLAN); verify(plan)
    if a.summarize:
        os.umask(0o022); summarize(); return
    if a.unit or a.probe_unit:
        run_unit(next(r for r in plan['rows'] if r['id'] in (a.unit, a.probe_unit)), plan, probe=bool(a.probe_unit)); return
    if a.smoke:
        smoke(plan); return
    assert a.worker
    worker(plan, a.lane, a.max_units)


if __name__ == '__main__':
    main()
