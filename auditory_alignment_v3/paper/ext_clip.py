"""Paper line, Table 2 row 'Transformer-CLIP' (Bollens, Accou, Van hamme, Francart, Sci Rep 15:28744, 2025) -- GPU.

Released weights: the official repository (github.com/exporl/transformer-clip-eeg @ 8be963ab) points to one Google Drive file
and a KU Leuven page; both return HTTP 404 (checked 2026-10-22, EXT_DECODERS_DOWNLOAD_RECEIPT.json).  ROUTE (needs the
coordinator's approval file OUT/ROUTE_APPROVED.json before production; the smoke does not need it): reproduce the published
final configuration with the official code on the public SparrKULee release already on the server (71 of the 91 official
training subjects are public; the paper used 180 subjects incl. non-public ones), then apply the native envelope readout.

Stage S (one GPU unit, resumable per story / per epoch):
  speech features = official preprocess_audio/create_wav2vec.get_hidden_output re-implemented line by line (its module runs
    at import): jonatasgrosman/wav2vec2-large-xlsr-53-dutch @ 46f22138, layer 19, 8 s chunks with 2 s context, no input
    normalisation, 50 -> 64 Hz scipy.signal.resample; stimuli = SparrKULee stimuli/eeg/<story>.npz.gz (48 kHz -> 16 kHz).
  EEG = SparrKULee derivatives/preprocessed_eeg (official preprocessing, 64 Hz), standardised per recording and channel
    (the official evaluation path standardises EEG before the encoder; the training loader takes the stored arrays as given).
  model / data / split = the official modules imported from the pinned checkout (read first): train_clip_final.load_eeg_encoder
    ('EEGConformerInterleaved', depth 10, 1 conv layer, latent 8, window 192), load_speech_encoder('convLSTM'),
    clip_model.CLIPSimNoLatentProj (temperature 0.075, lambda_clip 1, lambda_sim 0) + memoryBank(momentum 0.9),
    dataset_loader.EEGDatasetSimdata (3 s windows, batch 128 within one story chunk, subject shuffle 1.0; braindecode is
    stubbed because its import fails in this env and augmentation is off), helper get_train_val_test_files_final(run 4,
    'wav2vec_19', fold_split.json).  Training loop = train_clip_final.py's: AdamW(lr 1e-3, betas 0.9/0.999, wd 0.01),
    StepLR(10, 0.1), <= 500 epochs, early stopping on validation CE with patience 15, best state restored.  Seed 3401.
Stage T (20 units = ext_common partition): native envelope readout = official RegressionModel (Conv1d(8 -> 1, k 32 = 500 ms,
  'same') + LeakyReLU) on the frozen stage-S EEG encoder's [192, 8] embeddings of 3 s windows, official PearsonLoss, Adam
  1e-3, batch 64, <= 250 epochs, patience 10 on training-side validation (train people cs role=es), best state restored;
  train windows = the train people's cs role=fit segments at +0 s and +2 s (3 s each, inside the 5 s segment);
  reconstruction of a segment = windows at +0 / +1 / +2 s, Hann overlap-add as the official evaluation (outer half-windows
  weight 1), normalised by the summed weights.  DTU: native 64 channels, common average reference, per-listener z-score.
  FAU: Linear(31 -> 64) time-shared adapter (spherical-spline init, ext_vlaai.adapter_init) fitted jointly with the readout
  through the frozen encoder on the training listeners only.  Margin / integration as every other system.
Native context: 3 s encoder windows; 5 s of EEG per segment margin; 20 s per primary decision.
"""
from __future__ import annotations

import copy
from datetime import datetime
import gzip
import io
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import types

import numpy as np

from . import ext_common as XC
from . import ext_fleet as XF
from . import ext_vlaai as XV

SYSTEM = 'clip'
NAME, LANE, SBATCH = 'c3_s35pxclp', 's35_paper_ext_clip', 'slurm/aln35_paper_ext_clip.sbatch'
OUT = XC.OUT / 'clip'
STORE = XC.STORE / 'clip'
FM = Path('/projects/EEG-foundation-model/auditory_public/foundation_models')
REPO = FM / 'github__exporl__transformer-clip-eeg@8be963a' / 'repo'
COMMIT = '8be963abe5be5c0568e54df3bceb2600861f895b'
W2V = FM / 'hf__jonatasgrosman__wav2vec2-large-xlsr-53-dutch@46f2213'
W2V_REV = '46f221381d200f7bef268309b3f02023ccf11fcc'
SPARR = Path('/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0')
SDIR = STORE / 'source_v1'
DATA = SDIR / 'data'
APPROVAL = OUT / 'ROUTE_APPROVED.json'
REPO_FILES = ('clip_model.py', 'dataset_loader.py', 'train_clip_final.py', 'train_clip_helper_functions.py', 'vlaai.py', 'fold_split.json',
              'preprocess_audio/create_wav2vec.py')
SEED = 3401
SRC = {'run': 4, 'stimulus_features': 'wav2vec_19', 'model_arch': 'clip_sim_no_latent_proj', 'eeg_encoder': 'EEGConformerInterleaved',
       'speech_encoder': 'convLSTM', 'attention_depth': 10, 'number_conv_layers': 1, 'latent_dim': 8, 'lstm_units': 128,
       'temperature': 0.075, 'lambda_clip_loss': 1.0, 'lambda_sim_loss': 0.0, 'momentum_membank': 0.9, 'learning_rate': 1e-3,
       'beta1': 0.9, 'beta2': 0.999, 'weight_decay': 0.01, 'optimizer': 'adamw', 'lr_scheduler': 'step', 'step_size_scheduler': 10,
       'epochs': 500, 'patience': 15, 'batch_size': 128, 'shuffle': True, 'shuffle_percentage': 1.0, 'window_s': 3, 'fs': 64,
       'number_of_training_subjects': 1000, 'warmup_epochs': 0}
W2V_LAYER, W2V_OVERLAP, W2V_SEG = 19, 2, 8
TGT = {'numerics': 'fp32 (TF32 off, deterministic cuDNN)', 'batch_invariance_margin_tol': XV.MARGIN_TOL, 'lr': 1e-3, 'batch': 64, 'epochs': 250, 'patience': 10, 'train_starts_s': [0, 2], 'infer_starts_s': [0, 1, 2], 'window': 192}
SMOKE = {'stories': 3, 'source_epochs': 1, 'max_batches': 40, 'train': 256, 'val': 64, 'score': 64, 'target_epochs': 2, 'w2v_seconds': 30}
read, write, sha, digest = XC.read, XC.write, XC.sha, XC.digest


def sources():
    here = Path(__file__).parent
    out = {**XC.sources(), **{f'auditory_alignment_v3/paper/{f}': sha(here / f) for f in ('ext_clip.py', 'ext_fleet.py', 'ext_vlaai.py')}}
    out.update({f'transformer-clip-eeg@{COMMIT[:8]}/{f}': sha(REPO / f) for f in REPO_FILES})
    out.update({f'wav2vec2-dutch@{W2V_REV[:8]}/{f}': sha(W2V / f) for f in ('config.json', 'pytorch_model.bin')})
    return out


def rows():
    out = [{'stage': 'source', 'system': SYSTEM, 'seed': SEED, 'id': 'PXCLP_S_' + digest({'stage': 'source', 'seed': SEED, **SRC}, 16)}]
    for ds in XC.DATASETS:
        for cf in XC.CFS:
            for sf in XC.SFS:
                body = {'stage': 'target', 'system': SYSTEM, 'dataset': ds, 'content_fold': cf, 'person_fold': sf, 'seed': SEED}
                out.append({**body, 'id': 'PXCLP_T_' + digest(body, 16)})
    return out


def make_plan():
    body = {'version': 'PAPER_EXT_CLIP_v1', 'rows': rows(), 'sources': sources(),
            'input_index_sha256': {ds: sha(XC.INPUT / ds / 'index.json') for ds in XC.DATASETS},
            'route': 'released weights unavailable (README links 404 on 2026-10-22) -> official-code reproduction on public SparrKULee',
            'source_recipe': SRC, 'target_recipe': TGT, 'w2v': {'layer': W2V_LAYER, 'overlap_s': W2V_OVERLAP, 'segment_s': W2V_SEG, 'revision': W2V_REV},
            'sparrkulee': str(SPARR), 'repo_commit': COMMIT,
            'context': {'eeg_per_window_s': 3.0, 'eeg_per_segment_s': 5.0, 'eeg_per_20s_decision_s': 20.0, 'native_window_s': 3.0},
            'smoke': SMOKE}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
        return old
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700); STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
    write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    return read(plan)


def verify(plan):
    assert plan['sources'] == sources(), 'clip source drift'
    for ds in XC.DATASETS:
        assert sha(XC.INPUT / ds / 'index.json') == plan['input_index_sha256'][ds]


# ------------------------------------------------------------------------------------------------ official code
def official():
    """Import the pinned official modules (read before use). braindecode's import fails in this env (moabb API) and the
    augmentation classes are only referenced when augmentation is enabled (it is off), so a stub module stands in."""
    if 'braindecode.augmentation' not in sys.modules or not getattr(sys.modules['braindecode.augmentation'], '_paper_stub', False):
        bd = types.ModuleType('braindecode'); aug = types.ModuleType('braindecode.augmentation'); aug._paper_stub = True

        class _Unavailable:
            def __init__(self, *a, **k):
                raise RuntimeError('braindecode augmentation is disabled in this reproduction')
        for n in ('SignFlip', 'FTSurrogate', 'FrequencyShift', 'BandstopFilter', 'GaussianNoise', 'SmoothTimeMask', 'ChannelsDropout', 'ChannelsShuffle'):
            setattr(aug, n, _Unavailable)
        bd.augmentation = aug; sys.modules['braindecode'] = bd; sys.modules['braindecode.augmentation'] = aug
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    import clip_model as CM
    import dataset_loader as DL
    import train_clip_helper_functions as TH
    import train_clip_final as TF
    return CM, DL, TH, TF


def build_source_model(dev, bank_size):
    CM, DL, TH, TF = official()
    wl = SRC['window_s'] * SRC['fs']
    TF.latent_dim = SRC['latent_dim']               # load_speech_encoder('convLSTM') reads the script-level global
    eeg = TF.load_eeg_encoder(SRC['eeg_encoder'], SRC['lstm_units'], 'valid', 128, SRC['number_conv_layers'], wl, SRC['latent_dim'],
                              SRC['attention_depth'])
    speech = TF.load_speech_encoder(SRC['speech_encoder'], SRC['lstm_units'], 'valid', 128, SRC['number_conv_layers'], wl, 3, 1024)
    bank = CM.memoryBank(bank_size=bank_size, dim=speech.get_output_dim(wl), momentum=SRC['momentum_membank'], device=dev)
    model = CM.CLIPSimNoLatentProj(eeg, speech, bank, temperature=SRC['temperature'], window_length=wl,
                                   lambda_clip=SRC['lambda_clip_loss'], lambda_average=SRC['lambda_sim_loss'])
    return model.to(dev)


# ------------------------------------------------------------------------------------------------ stage S data
def split_files():
    CM, DL, TH, TF = official()
    return TH.get_train_val_test_files_final(str(DATA), SRC['run'], SRC['stimulus_features'], str(REPO / 'fold_split.json'),
                                             SRC['number_of_training_subjects'])


def needed_stories():
    import json
    d = json.loads((REPO / 'fold_split.json').read_text())
    val = set(d[str(SRC['run'])]); train = {s for k in range(9) if str(k) != str(SRC['run']) for s in d[str(k)]}
    subs = set(d['train_subs'])
    eeg = [p for p in sorted((SPARR / 'derivatives' / 'preprocessed_eeg').glob('sub-*/*/*_eeg.npy'))
           if p.name.split('_')[0] in subs and p.name.split('-audio-')[-1].split('_eeg')[0] in (train | val)]
    stories = sorted({p.name.split('-audio-')[-1].split('_eeg')[0] for p in eeg})
    return eeg, stories, sorted(train), sorted(val)


def prepare_eeg():
    """Per-recording per-channel standardised float32 copies in the official layout (CPU-able; idempotent)."""
    eeg, *_ = needed_stories(); n = 0
    for p in eeg:
        dst = DATA / 'derivatives' / 'preprocessed_eeg' / p.relative_to(SPARR / 'derivatives' / 'preprocessed_eeg')
        if dst.exists():
            continue
        x = np.load(p).astype(np.float64)
        mu, sd = x.mean(1, keepdims=True), x.std(1, keepdims=True); sd[sd == 0] = 1
        dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        tmp = dst.with_name(dst.name + '.tmp.npy'); np.save(tmp, ((x - mu) / sd).astype(np.float32)); os.replace(tmp, dst); n += 1
    return {'n_recordings': len(eeg), 'written': n}


def load_audio48(story):
    with gzip.open(SPARR / 'stimuli' / 'eeg' / f'{story}.npz.gz', 'rb') as f:
        z = np.load(io.BytesIO(f.read()), allow_pickle=False)
        return z['audio'], int(z['fs'])


def w2v_model(dev):
    from transformers import Wav2Vec2ForCTC
    m = Wav2Vec2ForCTC.from_pretrained(str(W2V)).to(dev).eval()
    return m


def hidden_19(model, speech, dev, sr=16000, overlap=W2V_OVERLAP, segment_length=W2V_SEG, layer=W2V_LAYER):
    """create_wav2vec.get_hidden_output, one layer, same chunking / cropping (input already at 16 kHz, float32)."""
    import torch
    speech_array = np.expand_dims(speech.astype(np.float32), 0)
    segment_length = segment_length * sr; wav_length = np.size(speech_array)
    speech_array2 = np.concatenate([np.zeros((1, int(overlap / 2) * sr), dtype=np.float32), speech_array], axis=1)
    end_of_file = False; outs = []
    for i in range(int(wav_length / segment_length) + 1):
        start = 0 + i * segment_length; end = start + segment_length + overlap * sr
        if end < np.size(speech_array2):
            spch_seg = speech_array2[:, start:end]
        else:
            spch_seg = speech_array2[:, start:]; end_of_file = True
        inp = torch.tensor(spch_seg).to(dev)
        with torch.no_grad():
            h = model.base_model(inp, attention_mask=torch.ones_like(inp), output_hidden_states=True)['hidden_states'][layer]
        out = np.squeeze(h.float().cpu().numpy())
        out = out[int(overlap / 2) * 50:] if end_of_file else out[int(overlap / 2) * 50: -int(overlap / 2) * 50 + 1, :]
        outs.append(out)
    return np.vstack(outs)


def w2v_features(story, model, dev, seconds=None):
    import scipy.signal as sps
    from scipy.signal import resample_poly
    dst = DATA / 'derivatives' / 'preprocessed_stimuli' / f'{story}_-_wav2vec_{W2V_LAYER}.npy'
    if dst.exists() and seconds is None:
        return dst
    a, fs = load_audio48(story)
    if seconds is not None:
        a = a[:int(seconds * fs)]
    x = resample_poly(a, 16000, fs).astype(np.float32)
    v = hidden_19(model, x, dev)
    v = sps.resample(v, round(np.size(v, axis=0) * float(SRC['fs']) / 50)).astype(np.float32)
    if seconds is not None:
        return v
    dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = dst.with_name(dst.name + '.tmp.npy'); np.save(tmp, v); os.replace(tmp, dst)
    return dst


# ------------------------------------------------------------------------------------------------ stage S train
def source_unit(row, plan, probe=False):
    import torch
    t_all = time.time(); job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda'); torch.cuda.reset_peak_memory_stats()
    dest = (SDIR / 'probes' / job) if probe else SDIR; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    eeg_files, stories, train_st, val_st = needed_stories()
    t0 = time.time(); prep = prepare_eeg(); t_eeg = time.time() - t0
    t0 = time.time(); w2v = w2v_model(dev)
    smoke_feat = None
    if probe:
        smoke_feat = w2v_features(stories[0], w2v, dev, seconds=SMOKE['w2v_seconds'])
        use = [s for s in train_st if s in stories][:2] + [s for s in val_st if s in stories][:1]
    else:
        use = stories
    for s in use:
        w2v_features(s, w2v, dev)
    del w2v; torch.cuda.empty_cache(); t_w2v = time.time() - t0
    CM, DL, TH, TF = official()
    tr_f, va_f, te_f, te_h, tr_a, va_a, te_a, te_ha = split_files()
    full_n_files = {'train': len(tr_f), 'val': len(va_f), 'train_subjects': len({os.path.basename(f).split('_')[0] for f in tr_f})}
    if probe:
        keep = lambda fs, st: [f for f in fs if os.path.basename(f).split('-audio-')[-1].split('_eeg')[0] in st][:SMOKE['stories'] * 2]
        tr_f = keep(tr_f, set(use[:2])); va_f = keep(va_f, set(use[2:]))
        tr_a = [a for a in tr_a if os.path.basename(a).split('_-_')[0] in set(use[:2])]; va_a = [a for a in va_a if os.path.basename(a).split('_-_')[0] in set(use[2:])]
    wl = SRC['window_s'] * SRC['fs']; bs = SRC['batch_size']
    np.random.seed(SEED); torch.manual_seed(SEED); torch.backends.cudnn.benchmark = True
    t0 = time.time()
    train_data = DL.EEGDatasetSimdata(tr_f, tr_a, wl, wl, batch_size=bs, shuffle=SRC['shuffle'], addEEG=False,
                                      shuffle_percentage=SRC['shuffle_percentage'], data_augmentation=[], data_augmentation_probability=0.5)
    val_data = DL.EEGDatasetSimdata(va_f, va_a, wl, wl, batch_size=bs, shuffle_percentage=SRC['shuffle_percentage'])
    t_load = time.time() - t0
    from torch.utils.data import DataLoader
    params = {'batch_size': None, 'batch_sampler': None, 'shuffle': False, 'pin_memory': True}
    train_loader, val_loader = DataLoader(train_data, **params), DataLoader(val_data, **params)
    model = build_source_model(dev, train_data.get_number_of_stimuli_segments())
    opt = torch.optim.AdamW(model.parameters(), betas=(SRC['beta1'], SRC['beta2']), amsgrad=False, weight_decay=SRC['weight_decay'], lr=SRC['learning_rate'])
    sched = torch.optim.lr_scheduler.StepLR(opt, step_size=SRC['step_size_scheduler'], gamma=0.1)
    state_path = dest / 'train_state.pt'; best_loss, best_epoch, best_state, hist, start = float('inf'), 0, None, [], 0
    if state_path.exists() and not probe:
        st = torch.load(state_path, map_location='cpu', weights_only=False)
        assert st['plan_sha256'] == sha(OUT / 'plan.json')
        model.load_state_dict(st['model']); opt.load_state_dict(st['opt']); sched.load_state_dict(st['sched'])
        best_loss, best_epoch, best_state, hist, start = st['best_loss'], st['best_epoch'], st['best_state'], st['hist'], st['epoch'] + 1
        np.random.set_state(st['np_rng']); torch.set_rng_state(st['torch_rng']); torch.cuda.set_rng_state(st['cuda_rng'])
        train_data.batches_keys = st['batches_keys']
    epochs = SMOKE['source_epochs'] if probe else SRC['epochs']
    stopped = None
    for epoch in range(start, epochs):
        if epoch > best_epoch + SRC['patience'] and epoch > SRC['warmup_epochs']:
            model.load_state_dict(best_state); stopped = epoch; break
        te = time.time(); model.train(); losses = []
        for b, data in enumerate(train_loader):
            eeg = data[0].to(dev, dtype=torch.float); speech = data[1][0].to(dev, dtype=torch.float); ids = data[2].to(dev, dtype=torch.int64)
            loss_ce, loss_avg, loss_total = model(eeg, speech, ids)
            opt.zero_grad(); loss_total.backward(); opt.step(); losses.append(float(loss_ce))
            if probe and b + 1 >= SMOKE['max_batches']:
                break
        sched.step(); t_tr = time.time() - te
        model.eval(); vl = []
        with torch.no_grad():
            for b, data in enumerate(val_loader):
                eeg = data[0].to(dev, dtype=torch.float); speech = data[1][0].to(dev, dtype=torch.float); ids = data[2].to(dev, dtype=torch.int64)
                vl.append(model(eeg, speech, ids)[0])
                if probe and b + 1 >= SMOKE['max_batches']:
                    break
        mean_ce = torch.mean(torch.hstack(vl)).item()
        hist.append({'epoch': epoch, 'train_ce': float(np.mean(losses)), 'val_ce': mean_ce, 'n_batches': len(losses), 'train_seconds': round(t_tr, 1),
                     'seconds': round(time.time() - te, 1), 'lr': opt.param_groups[0]['lr']})
        print('clip source', hist[-1], flush=True)
        if mean_ce < best_loss:
            best_loss, best_epoch, best_state = mean_ce, epoch, copy.deepcopy(model.state_dict())
        if not probe:
            torch.save({'plan_sha256': sha(OUT / 'plan.json'), 'epoch': epoch, 'model': model.state_dict(), 'opt': opt.state_dict(),
                        'sched': sched.state_dict(), 'best_loss': best_loss, 'best_epoch': best_epoch, 'best_state': best_state, 'hist': hist,
                        'np_rng': np.random.get_state(), 'torch_rng': torch.get_rng_state(), 'cuda_rng': torch.cuda.get_rng_state(),
                        'batches_keys': list(train_data.batches_keys)}, state_path.with_suffix('.tmp'))
            os.replace(state_path.with_suffix('.tmp'), state_path)
    if stopped is None and best_state is not None:
        model.load_state_dict(best_state)
    torch.save(model.state_dict(), dest / 'model.ckpt')
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'dest': str(dest),
           'checkpoint_sha256': sha(dest / 'model.ckpt'), 'best_epoch': best_epoch, 'best_val_ce': best_loss, 'stopped_at_epoch': stopped,
           'history': hist, 'n_files': {'train': len(tr_f), 'val': len(va_f)}, 'full_n_files': full_n_files, 'n_stories': len(use),
           'train_subjects': sorted({os.path.basename(f).split('_')[0] for f in tr_f}), 'eeg_prep': prep,
           'n_params': {'model': sum(p.numel() for p in model.parameters()), 'eeg': sum(p.numel() for p in model.eegModel.parameters())},
           'seconds': {'eeg_prep': round(t_eeg, 1), 'w2v': round(t_w2v, 1), 'load': round(t_load, 1), 'total': round(time.time() - t_all, 1)},
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': job}
    if probe:
        rec['smoke_w2v_shape'] = list(smoke_feat.shape); rec['smoke_w2v_rate_ok'] = abs(smoke_feat.shape[0] - SMOKE['w2v_seconds'] * 64) <= 2
        per_batch = hist[-1]['train_seconds'] / max(1, hist[-1]['n_batches'])
        rec['per_batch_seconds'] = per_batch
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    if state_path.exists() and not probe:
        state_path.unlink()
    print(row['id'], 'source complete', rec['seconds'], flush=True)
    return rec


# ------------------------------------------------------------------------------------------------ stage T
def source_ckpt(plan, probe_job=None):
    srow = plan['rows'][0]
    if probe_job is not None:
        rec = read(OUT / 'probes' / probe_job / 'units' / f'{srow["id"]}.json')
    else:
        rec = read(OUT / 'units' / f'{srow["id"]}.json'); assert rec['status'] == 'complete' and not rec['probe']
    path = Path(rec['dest']) / 'model.ckpt'; assert sha(path) == rec['checkpoint_sha256']
    return path, rec


def target_unit(row, plan, probe=False):
    import torch
    from torch import nn
    t_all = time.time(); job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda'); torch.cuda.reset_peak_memory_stats()
    numerics = XV.fp32_numerics()             # stage T: full fp32, deterministic cuDNN (stage S keeps the official settings)
    CM, DL, TH, TF = official()
    ds, cf, sf = row['dataset'], row['content_fold'], row['person_fold']
    ckpt, srec = source_ckpt(plan, job if probe else None)
    model = build_source_model(dev, 1)
    sd = torch.load(ckpt, map_location='cpu', weights_only=True)
    sd = {k: v for k, v in sd.items() if not k.startswith('eegMemoryBank.')}
    missing = model.load_state_dict(sd, strict=False)
    assert all(k.startswith('eegMemoryBank.') for k in missing.missing_keys) and not missing.unexpected_keys
    enc = model.eegModel.eval(); enc.requires_grad_(False)
    cache = XC.Cache(ds); channels = cache.index['channels']
    X, att, ign = XV.load_all(cache, car=(ds == 'dtu'))
    role = cache.role(cf); tr_ids, te_ids = cache.scored(cf, sf)
    fit_ids, val_ids = tr_ids[role[tr_ids] == 'fit'], tr_ids[role[tr_ids] == 'es']
    full = {'fit': int(len(fit_ids)), 'val': int(len(val_ids)), 'score': int(len(tr_ids) + len(te_ids))}
    score_tr, score_te = tr_ids, te_ids
    if probe:
        rng = np.random.default_rng(SEED)
        fit_ids = np.sort(rng.choice(fit_ids, SMOKE['train'], replace=False)); val_ids = val_ids[:SMOKE['val']]
        score_tr, score_te = tr_ids[:SMOKE['score']], te_ids[:0]
    torch.manual_seed(SEED); np.random.seed(SEED)
    W = TGT['window']
    if ds == 'dtu':
        assert [c.casefold() for c in channels] == [c.casefold() for c in XV.BIOSEMI64]
        adapter = None
    else:
        adapter = nn.Linear(len(channels), 64).to(dev); M, ainfo = XV.adapter_init(channels)
        with torch.no_grad():
            adapter.weight.copy_(torch.from_numpy(M)); adapter.bias.zero_()
    readout = TH.RegressionModel(SRC['latent_dim'], output_dim=1).to(dev)
    crit = TH.PearsonLoss()

    def windows(ids, starts):
        """[n * len(starts), C, 192] EEG windows and [., 192] attended targets (segment order, then start)."""
        xs = np.stack([X[ids, :, s * 64:s * 64 + W] for s in starts], 1).reshape(-1, X.shape[1], W)
        ys = np.stack([att[ids, s * 64:s * 64 + W] for s in starts], 1).reshape(-1, W)
        return xs, ys

    def embed(x):                       # x [B, C, 192] tensor -> [B, 8, 192]
        x = x.transpose(1, 2)
        if adapter is not None:
            x = adapter(x)
        e = enc(x)                       # [B, 192, 8]
        return e.transpose(1, 2)

    def forward(x):
        return readout(embed(x))         # [B, 1, 192]
    xtr, ytr = windows(fit_ids, TGT['train_starts_s']); xva, yva = windows(val_ids, TGT['train_starts_s'])
    params = list(readout.parameters()) + (list(adapter.parameters()) if adapter is not None else [])
    opt = torch.optim.Adam(params, lr=TGT['lr'])
    cached = None
    if adapter is None:                  # frozen encoder, no adapter: embeddings once (as the official regression code)
        with torch.no_grad():
            cached = {k: torch.cat([embed(torch.from_numpy(v[s:s + 256]).to(dev)) for s in range(0, len(v), 256)]) for k, v in (('tr', xtr), ('va', xva))}

    def val_loss():
        readout.eval()
        with torch.no_grad():
            if cached is not None:
                out = readout(cached['va'])
            else:
                out = torch.cat([forward(torch.from_numpy(xva[s:s + 256]).to(dev)) for s in range(0, len(xva), 256)])
            return float(crit(out, torch.from_numpy(yva[:, None, :]).to(dev)).mean())
    best, best_ep, best_state, hist = float('inf'), -1, None, []
    epochs = SMOKE['target_epochs'] if probe else TGT['epochs']
    t0 = time.time()
    for ep in range(epochs):
        te = time.time(); readout.train(); perm = np.random.default_rng([SEED, ep]).permutation(len(xtr)); losses = []
        for s in range(0, len(perm), TGT['batch']):
            b = perm[s:s + TGT['batch']]
            y = torch.from_numpy(ytr[b][:, None, :]).to(dev)
            out = readout(cached['tr'][torch.from_numpy(b).to(dev)]) if cached is not None else forward(torch.from_numpy(xtr[b]).to(dev))
            loss = crit(out, y).mean()
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step(); losses.append(float(loss))
        v = val_loss(); hist.append({'epoch': ep + 1, 'train_loss': float(np.mean(losses)), 'val_loss': v, 'seconds': round(time.time() - te, 2)})
        print(row['id'], hist[-1], flush=True)
        if v < best:
            best, best_ep = v, ep + 1
            best_state = {'readout': copy.deepcopy(readout.state_dict()), 'adapter': copy.deepcopy(adapter.state_dict()) if adapter is not None else None}
        elif ep + 1 - best_ep > TGT['patience']:
            break
    readout.load_state_dict(best_state['readout'])
    if adapter is not None:
        adapter.load_state_dict(best_state['adapter'])
    t_train = time.time() - t0
    # reconstruction: windows at +0 / +1 / +2 s, official Hann overlap-add (outer half-windows weight 1), normalised
    starts = TGT['infer_starts_s']; hann = torch.hann_window(W).numpy().astype(np.float64)
    wts = np.stack([hann.copy() for _ in starts]); wts[0, :W // 2] = 1; wts[-1, W // 2:] = 1
    den = np.zeros(XC.SEG64)
    for j, st in enumerate(starts):
        den[st * 64:st * 64 + W] += wts[j]

    def recon(idx):
        out = np.zeros((len(idx), XC.SEG64))
        with torch.no_grad():
            for s in range(0, len(idx), 128):
                b = idx[s:s + 128]; xs, _ = windows(b, starts)
                o = torch.cat([forward(torch.from_numpy(xs[k:k + 384]).to(dev)) for k in range(0, len(xs), 384)])[:, 0].double().cpu().numpy()
                o = o.reshape(len(b), len(starts), W); acc = np.zeros((len(b), XC.SEG64))
                for j, st in enumerate(starts):
                    acc[:, st * 64:st * 64 + W] += o[:, j] * wts[j]
                out[s:s + len(b)] = acc / den
        return out

    def margin_fn(idx):
        Q = recon(idx)
        return XC.rowcorr(Q, att[idx].astype(np.float64)) - XC.rowcorr(Q, ign[idx].astype(np.float64))
    t0 = time.time(); ids = np.concatenate([score_tr, score_te]).astype(int); readout.eval()
    P = recon(ids)
    ra = XC.rowcorr(P, att[ids].astype(np.float64)); ri = XC.rowcorr(P, ign[ids].astype(np.float64)); t_score = time.time() - t0
    n = len(cache.arr['cs_person'])
    margin = np.full(n, np.nan); r_att = np.full(n, np.nan); r_ign = np.full(n, np.nan); scored = np.full(n, '', dtype='<U10')
    margin[ids], r_att[ids], r_ign[ids] = ra - ri, ra, ri; scored[score_tr] = 'train_side'; scored[score_te] = 'test'
    checks = {'margins_finite': bool(np.isfinite(margin[ids]).all()), 'ola_weights_positive': bool((den > 0).all())}
    checks.update(XV.margin_invariance(margin_fn, ids, ra - ri, ra - ri))
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(dest / 'margins.npz', cs_person=cache.arr['cs_person'], cs_code=cache.arr['cs_code'], cs_e0=cache.arr['cs_e0'],
                        cs_role=role, margin=margin, r_att=r_att, r_ign=r_ign, scored=scored)
    if not probe:
        torch.save(best_state, dest / 'readout_adapter.pt')
    rec = {'status': 'complete' if all(v for k, v in checks.items() if k.endswith(('_ok', 'finite', 'positive'))) else 'check_failed',
           'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'dest': str(dest), 'npz_sha256': sha(dest / 'margins.npz'),
           'source_checkpoint_sha256': sha(ckpt), 'best_epoch': best_ep, 'best_val_loss': best, 'history': hist,
           'adapter': ainfo if adapter is not None else None, 'full_counts': full,
           'n': {'fit_windows': int(len(xtr)), 'val_windows': int(len(xva)), 'scored_train_side': int(len(score_tr)), 'scored_test': int(len(score_te))},
           'seconds': {'train': round(t_train, 1), 'score': round(t_score, 1), 'total': round(time.time() - t_all, 1)},
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': job, 'checks': checks,
           'numerics': numerics}
    if probe:
        per = t_train / max(1, len(hist)) / max(1, len(xtr))
        rec['projected_full_unit_hours_at_60_epochs'] = (per * full['fit'] * len(TGT['train_starts_s']) * 60 + t_score / max(1, len(ids)) * full['score']) / 3600
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], ds, cf, sf, rec['status'], rec['seconds'], flush=True)
    assert rec['status'] == 'complete', checks
    return rec


def run_unit(row, plan, probe=False):
    return source_unit(row, plan, probe) if row['stage'] == 'source' else target_unit(row, plan, probe)


def smoke():
    job = os.environ['SLURM_JOB_ID']; plan = make_plan(); verify(plan)
    receipt = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
    try:
        picks = [plan['rows'][0]] + [next(r for r in plan['rows'] if r.get('dataset') == ds and r['content_fold'] == 0 and r['person_fold'] == 0)
                                      for ds in XC.DATASETS]
        for row in picks:
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', XF.DISPATCH, 'unit', '--id', row['id'], '--probe', '--system', SYSTEM]).returncode
            assert rc == 0, (row['id'], rc)
            rec = read(OUT / 'probes' / job / 'units' / f'{row["id"]}.json')
            assert rec['status'] == 'complete' and (row['stage'] == 'source' or rec['n']['scored_test'] == 0)
            keep = ('row', 'seconds', 'gpu_peak_mb', 'device', 'history', 'n_files', 'full_n_files', 'n_params', 'per_batch_seconds', 'smoke_w2v_shape',
                    'smoke_w2v_rate_ok', 'checks', 'numerics', 'adapter', 'n', 'full_counts', 'projected_full_unit_hours_at_60_epochs', 'train_subjects')
            receipt['units'].append({k: rec[k] for k in keep if k in rec})
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', receipt)


def unit_cli(uid, probe):
    plan = read(OUT / 'plan.json'); verify(plan)
    run_unit(next(r for r in plan['rows'] if r['id'] == uid), plan, probe)


def ready_fn(row):
    if row['stage'] == 'source':
        return APPROVAL.exists()
    plan = read(OUT / 'plan.json')
    return APPROVAL.exists() and (OUT / 'units' / f'{plan["rows"][0]["id"]}.json').exists()


def fleet_status():
    st = XF.fleet_status(sys.modules[__name__], ready_fn=ready_fn, slots=1, max_units=10)
    if st['state'] == 'waiting_for_dependencies' and not APPROVAL.exists():
        st['state'] = 'awaiting_route_approval'
    st['remaining'] = st['remaining'] if (OUT / 'plan.json').exists() else 21
    return st
