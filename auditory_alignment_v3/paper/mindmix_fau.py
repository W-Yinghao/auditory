"""Paper line, Table 2 row 'MindMix, complete system' on FAU (TH / HA / CI; 31 channels).  DTU = aln42/external_mindmix.py
(10 units complete; same released checkpoint, same official code, recipe and blind scoring -- imported, not re-derived).

Units = FAU content fold cf in {0, 1} x pooled person fold sf in 0..4 (ext_common partition; cs list, train / test people and
scored segments = ext_common.Cache('fau'), asserted against the frozen B0 FAU units when the cache was built).
Model / training / scoring = aln42.external_mindmix: build_model (official EEGEncoder + wav2vec2-base + create_model
('multimodal_real', 'calra') + released fusion checkpoint, asserted key-by-key), official MultimodalRealTrainer 50 epochs
(batch 32, lr 1e-5, wd 0.01, seed 3401) on the train people's role=fit cs segments, person-homogeneous batches, final epoch,
resume state every 5 epochs; blind order-symmetrised margin (candidates ordered by waveform sha256, label-free), segment
margin = mean over the three 2 s sub-windows at +0 / +1.5 / +3.0 s of the 5 s segment.
Channel handling: the encoder at commit 98445f36 has no spatial embedding (pos_embed forced None, no input_chans; the time
embedding indexes the two 1 s patches) and mean-pools all channel x patch tokens, so it accepts 31 channels and is
channel-permutation invariant -- checked numerically in the smoke (31-channel forward and a channel permutation).
FAU EEG (deviation from the DTU raw-BDF 1-40 Hz route, disclosed): the CI stimulation-artifact-cleaned stream is only
available as c3_preproc stage B (average reference over 30 EEG + reconstructed Cz, ICA artifact rejection, 1-20 Hz FIR,
128 Hz); MindMix therefore receives stage-B eeg_1_20_ica resampled 128 -> 200 Hz (resample_poly 25/16 per trial), per-window
per-channel z-score -- the same EEG stream as every other system on FAU; raw FAU EEG would expose CI artifacts.
FAU audio: the published stimulus waveforms (zenodo hdf5 stimulus_files/<code>/{attended,distractor}_wav, 48 kHz int32,
byte-identical across the three group files -- asserted), mono, resample_poly 48 -> 16 kHz, per-window peak normalisation;
waveform sample 0 = trial EEG sample 0 = envelope sample 0 (the cohort convention; checked in `prepare`: Hilbert envelope of
each waveform vs the published 1 kHz envelope, lag of the correlation peak must be 0 ms, AUDIO_ALIGNMENT.json).

CLI via paper/external_decoders.py: plan | smoke | worker | unit --system mmfau; `prepare` (CPU) builds the input caches and the
alignment receipt: python -m auditory_alignment_v3.paper.mindmix_fau prepare
"""
from __future__ import annotations

from datetime import datetime
import fcntl
import gc
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from . import ext_common as XC
from . import ext_fleet as XF
from ..aln42 import external_mindmix as XM

SYSTEM = 'mmfau'
NAME, LANE, SBATCH = 'c3_s35pxmmf', 's35_paper_ext_mmfau', 'slurm/aln35_paper_ext_mmfau.sbatch'
OUT = XC.OUT / 'mindmix_fau'
STORE = XC.STORE / 'mindmix_fau'
FAU_H5 = {'ha': '/projects/EEG-foundation-model/auditory_public/fau_tud/zenodo_17927767_ha/hi_dataset_1kHz.hdf5',
          'th': '/projects/EEG-foundation-model/auditory_public/fau_tud/zenodo_17952231_th/nh_dataset_1kHz.hdf5',
          'ci': '/projects/EEG-foundation-model/auditory_public/fau_tud/zenodo_17952844_ci/ci_dataset_1kHz.hdf5'}
ALIGN = OUT / 'AUDIO_ALIGNMENT.json'
FS_COH = 128
SEED, EPOCHS, BATCH = XM.SEED, XM.EPOCHS, XM.BATCH
SUB_OFFS_S, WIN_S, FS_EEG, FS_AUD = XM.SUB_OFFS_S, XM.WIN_S, XM.FS_EEG, XM.FS_AUD
SCORE_BATCH, STATE_EVERY, SMOKE = XM.SCORE_BATCH, XM.STATE_EVERY, XM.SMOKE
read, write, sha, digest = XC.read, XC.write, XC.sha, XC.digest


def sources():
    here = Path(__file__).parent
    out = {**XC.sources(), **{f'auditory_alignment_v3/paper/{f}': sha(here / f) for f in ('mindmix_fau.py', 'ext_fleet.py')},
           'auditory_alignment_v3/aln42/external_mindmix.py': sha(Path(XM.__file__))}
    out.update({f'mindmix@{XM.MM_COMMIT[:8]}/{f}': sha(XM.MM_REPO / f) for f in XM.MM_FILES})
    return out


def rows():
    out = []
    for cf in XC.CFS:
        for sf in XC.SFS:
            body = {'method': 'MindMix_released_full_architecture_common_protocol', 'dataset': 'fau', 'content_fold': cf, 'person_fold': sf, 'seed': SEED}
            out.append({**body, 'id': 'PXMMF_' + digest(body, 16)})
    return out


def make_plan():
    al = read(ALIGN); assert al['pass']
    body = {'version': 'PAPER_EXT_MINDMIX_FAU_v1', 'rows': rows(), 'sources': sources(), 'input_index_sha256': sha(XC.INPUT / 'fau' / 'index.json'),
            'dtu_route': {'module': 'auditory_alignment_v3/aln42/external_mindmix.py', 'plan_sha256': sha(XM.OUT / 'plan.json'),
                          'binding_sha256': sha(XM.BINDING)},
            'checkpoint_sha256': XM.CKPT_SHA, 'mindmix_commit': XM.MM_COMMIT, 'wav2vec2_revision': XM.W2V_REV, 'audio_alignment_sha256': sha(ALIGN),
            'store': str(STORE), 'geometry': {'sub_window_starts_s': list(SUB_OFFS_S), 'window_s': WIN_S, 'segment_s': 5.0},
            'recipe': {'epochs': EPOCHS, 'batch_size': BATCH, 'lr': XM.LR, 'weight_decay': XM.WD, 'seed': SEED, 'checkpoint': 'final_epoch_50',
                       'train_rows': 'train people, role fit, cs', 'batches': 'person-homogeneous', 'score_batch': SCORE_BATCH,
                       'eeg': 'stage-B eeg_1_20_ica (31 ch) 128 -> 200 Hz, per-window per-channel z-score',
                       'audio': 'published 48 kHz waveforms -> 16 kHz, per-window peak normalisation'},
            'context': {'eeg_per_segment_s': 5.0, 'eeg_per_subwindow_s': 2.0, 'eeg_per_20s_decision_s': 20.0, 'native_window_s': 2.0},
            'smoke': SMOKE}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
        return old
    STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
    write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    return read(plan)


def verify(plan):
    assert plan['sources'] == sources(), 'mmfau source drift'
    assert sha(XC.INPUT / 'fau' / 'index.json') == plan['input_index_sha256'] and sha(ALIGN) == plan['audio_alignment_sha256']


# ------------------------------------------------------------------------------------------------ inputs
def _lock(path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    h = path.open('a+'); fcntl.flock(h, fcntl.LOCK_EX); return h


def eeg_cache(pid, group, trials):
    """{trial: eeg200 [31, L] float32} of the person's cs trials (stage-B eeg_1_20_ica, resample_poly 25/16 per trial)."""
    path = STORE / 'input_v1' / 'eeg' / f'{pid}.npz'
    h = _lock(STORE / 'input_v1' / 'locks' / f'eeg_{pid}.lock')
    try:
        if not path.exists():
            import h5py
            from scipy.signal import resample_poly
            from auditory_alignment import data as D
            arrs = {}
            with h5py.File(os.path.join(D.STAGEB, group, f'{pid}.h5'), 'r') as f:
                for t in sorted(set(trials)):
                    x = f[t]['eeg_1_20_ica'][()].astype(np.float64)
                    arrs['eeg__' + t] = resample_poly(x, 25, 16, axis=1).astype(np.float32)
            tmp = path.with_name(path.name + '.tmp.npz'); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            np.savez(tmp, **arrs); os.replace(tmp, path)
    finally:
        h.close()
    with np.load(path) as z:
        out = {k[5:]: z[k] for k in z.files}
    assert set(trials) <= set(out), pid
    return out


def wav48(code, stream, group='th'):
    import h5py
    with h5py.File(FAU_H5[group], 'r') as f:
        return f[f'stimulus_files/{code}/{stream}_wav'][()]


def audio_cache(code, stream):
    path = STORE / 'input_v1' / 'audio' / f'{code}_{stream}.npy'
    lk = _lock(STORE / 'input_v1' / 'locks' / f'aud_{code}_{stream}.lock')
    try:
        if not path.exists():
            from scipy.signal import resample_poly
            x = wav48(code, stream).astype(np.float64)
            y = resample_poly(x, 1, 3).astype(np.float32)
            tmp = path.with_name(path.name + '.tmp.npy'); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            np.save(tmp, y); os.replace(tmp, path)
    finally:
        lk.close()
    return np.load(path)


class Inputs:
    def __init__(self, cache, seg_ids):
        a = cache.arr; self.a = a; self.E, self.A, self.sha = {}, {}, {}
        groups = cache.index['groups']
        for pid in sorted({a['cs_person'][i] for i in seg_ids}):
            trials = sorted({a['cs_trial'][i] for i in seg_ids if a['cs_person'][i] == pid})
            self.E[pid] = eeg_cache(pid, groups[pid], trials)
        al = read(ALIGN)
        for code in sorted({a['cs_code'][i] for i in seg_ids}):
            for stream in ('attended', 'distractor'):
                self.A[(code, stream)] = audio_cache(code, stream)
                self.sha[(code, stream)] = al['waveform_sha256'][f'{code}/{stream}']

    def window(self, i, o):
        a = self.a; tau = int(a['cs_st'][i]) / FS_COH + o
        e = self.E[a['cs_person'][i]][a['cs_trial'][i]]; j = int(round(tau * FS_EEG)); L = int(WIN_S * FS_EEG)
        x = e[:, j:j + L].astype(np.float32); assert j >= 0 and x.shape[1] == L, ('eeg range', i, o)
        x = (x - x.mean(1, keepdims=True)) / (x.std(1, keepdims=True) + 1e-8)
        La = int(WIN_S * FS_AUD); ia = int(round(tau * FS_AUD)); code = a['cs_code'][i]
        t = self.A[(code, 'attended')][ia:ia + La]; m = self.A[(code, 'distractor')][ia:ia + La]
        assert len(t) == La and len(m) == La, ('audio range', i, o)
        t = t / max(float(np.abs(t).max()), 1e-8); m = m / max(float(np.abs(m).max()), 1e-8)
        return x, t.astype(np.float32), m.astype(np.float32)

    def first_is_attended(self, i):
        code = self.a['cs_code'][i]
        return self.sha[(code, 'attended')] < self.sha[(code, 'distractor')]


def prepare():
    """CPU: waveform identity across group files, audio alignment receipt, audio + EEG caches."""
    import h5py
    from scipy.signal import hilbert, resample_poly
    cache = XC.Cache('fau'); a = cache.arr
    codes = sorted(set(a['cs_code'].tolist()))
    rec = {'waveform_sha256': {}, 'identical_across_group_files': True, 'lag_ms': {}, 'peak_r': {}}
    for code in codes:
        for stream in ('attended', 'distractor'):
            hs = []
            for g in ('th', 'ha', 'ci'):
                hs.append(hashlib.sha256(np.ascontiguousarray(wav48(code, stream, g)).tobytes()).hexdigest())
            rec['identical_across_group_files'] &= len(set(hs)) == 1
            rec['waveform_sha256'][f'{code}/{stream}'] = hs[0]
            x = wav48(code, stream).astype(np.float64)
            from scipy.fft import next_fast_len
            env = resample_poly(np.abs(hilbert(x, N=next_fast_len(len(x)))[:len(x)]), 1, 48)   # 48 kHz -> 1 kHz (zero-padded FFT)
            with h5py.File(FAU_H5['th'], 'r') as f:
                pub = f[f'stimulus_files/{code}/{stream}_env'][()].astype(np.float64)
            n = min(len(env), len(pub)); e1 = env[:n] - env[:n].mean(); p1 = pub[:n] - pub[:n].mean()
            lags = range(-50, 51)
            r = [float(np.dot(e1[max(0, L):n + min(0, L)], p1[max(0, -L):n - max(0, L)]) /
                       np.sqrt(np.dot(e1, e1) * np.dot(p1, p1))) for L in lags]
            k = int(np.argmax(r)); rec['lag_ms'][f'{code}/{stream}'] = list(lags)[k]; rec['peak_r'][f'{code}/{stream}'] = r[k]
            audio_cache(code, stream)
            print(code, stream, 'lag', list(lags)[k], 'r', round(r[k], 3), flush=True)
    rec['pass'] = bool(rec['identical_across_group_files'] and all(v == 0 for v in rec['lag_ms'].values()))
    rec['rule'] = 'Hilbert |x| of the 48 kHz waveform -> resample_poly 1/48 -> 1 kHz vs published *_env (1 kHz); argmax Pearson r over lags -50..50 ms must be 0'
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700); write(ALIGN, rec)
    groups = cache.index['groups']
    for pid in sorted(set(a['cs_person'].tolist())):
        sel = cache.person_rows(pid); eeg_cache(pid, groups[pid], sorted(set(a['cs_trial'][sel].tolist())))
    print('prepared; alignment pass', rec['pass'], flush=True)


# ------------------------------------------------------------------------------------------------ unit
def run_unit(row, plan, probe=False):
    import torch
    t_all = time.time(); job = os.environ['SLURM_JOB_ID']
    dev = torch.device('cuda'); torch.cuda.reset_peak_memory_stats()
    cf, sf = row['content_fold'], row['person_fold']
    assert sha(XM.CKPT) == XM.CKPT_SHA
    cache = XC.Cache('fau'); a = cache.arr; person, role = a['cs_person'], cache.role(cf)
    tr_ids, te_ids = cache.scored(cf, sf)
    fit_ids = [int(i) for i in tr_ids if role[i] == 'fit']; side_ids = [int(i) for i in tr_ids]; test_ids = [int(i) for i in te_ids]
    windows = [(i, o) for i in fit_ids for o in SUB_OFFS_S]
    score_ids = side_ids + test_ids
    full_counts = {'train_windows': len(windows), 'score_windows': len(score_ids) * len(SUB_OFFS_S)}
    if probe:
        windows = windows[:SMOKE['train_windows']]; score_ids = side_ids[:SMOKE['score_segments']]
    t0 = time.time(); inp = Inputs(cache, sorted(set([w[0] for w in windows]) | set(score_ids))); t_prep = time.time() - t0
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    model, args, UT = XM.build_model(dev)
    trainer = UT.create_trainer(args.strategy, model, dev, args); trainer.setup_optimizer()
    owner = np.array([person[i] for i, _ in windows])
    checks = {}
    if probe:                                # channel-count / permutation check of the released EEG branch on real FAU windows
        model.eval()
        with torch.no_grad():
            x = torch.from_numpy(np.stack([inp.window(*w)[0] for w in windows[:4]])).to(dev)
            perm = torch.from_numpy(np.random.default_rng(SEED).permutation(x.shape[1])).to(dev)
            e1 = model.eeg_encoder(x); e2 = model.eeg_encoder(x[:, perm])
        checks['eeg_channels'] = int(x.shape[1]); checks['channel_permutation_max_abs'] = float((e1 - e2).abs().max())
        checks['channel_permutation_ok'] = checks['channel_permutation_max_abs'] < 1e-3
        model.train()

    def loader(ep):
        rng = np.random.default_rng([SEED, ep]); batches = []
        for p in sorted(set(owner.tolist())):
            idx = np.flatnonzero(owner == p); idx = idx[rng.permutation(len(idx))]
            batches += [idx[k:k + BATCH] for k in range(0, len(idx), BATCH)]
        for b in [batches[k] for k in rng.permutation(len(batches))]:
            xs = [inp.window(*windows[j]) for j in b]
            yield (torch.from_numpy(np.stack([x[0] for x in xs])).to(dev), torch.from_numpy(np.stack([x[1] for x in xs])).to(dev),
                   torch.from_numpy(np.stack([x[2] for x in xs])).to(dev), torch.ones(len(b), device=dev))

    class _L:
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
    model.eval(); t0 = time.time()
    sw = [(i, o) for i in score_ids for o in SUB_OFFS_S]
    raw = np.full(len(sw), np.nan)
    with torch.no_grad():
        for k in range(0, len(sw), SCORE_BATCH):
            xs = [inp.window(*w) for w in sw[k:k + SCORE_BATCH]]
            e = torch.from_numpy(np.stack([x[0] for x in xs])).to(dev)
            at = torch.from_numpy(np.stack([x[1] for x in xs])).to(dev); ig = torch.from_numpy(np.stack([x[2] for x in xs])).to(dev)
            fa = torch.from_numpy(np.array([inp.first_is_attended(i) for i, _ in sw[k:k + SCORE_BATCH]])).to(dev)[:, None]
            c1 = torch.where(fa, at, ig); c2 = torch.where(fa, ig, at)          # label-free order: smaller waveform sha first
            m = XM.blind_margin(model, e, c1, c2)
            if k == 0:
                checks['swap_max_abs'] = float((m + XM.blind_margin(model, e, c2, c1)).abs().max())
                checks['batch_invariance_max_abs'] = float((torch.cat([XM.blind_margin(model, e[j:j + 1], c1[j:j + 1], c2[j:j + 1])
                                                                       for j in range(min(4, len(e)))]) - m[:min(4, len(e))]).abs().max())
            raw[k:k + len(xs)] = m.double().cpu().numpy()
    t_score = time.time() - t0
    raw = raw.reshape(len(score_ids), len(SUB_OFFS_S))
    first_is_att = np.array([inp.first_is_attended(i) for i in score_ids])
    sub_oriented = np.where(first_is_att[:, None], raw, -raw)
    n = len(person)
    margin = np.full(n, np.nan); msub = np.full((n, len(SUB_OFFS_S)), np.nan); mraw = np.full(n, np.nan)
    fia = np.zeros(n, bool); scored = np.full(n, '', dtype='<U10')
    margin[score_ids] = sub_oriented.mean(1); msub[score_ids] = sub_oriented; mraw[score_ids] = raw.mean(1); fia[score_ids] = first_is_att
    scored[side_ids if not probe else score_ids] = 'train_side'
    if not probe:
        scored[test_ids] = 'test'
    checks['margins_finite'] = bool(np.isfinite(margin[score_ids]).all())
    checks['swap_ok'] = checks['swap_max_abs'] < 1e-3; checks['batch_invariance_ok'] = checks['batch_invariance_max_abs'] < 1e-2
    np.savez_compressed(dest / 'margins.npz', cs_person=person, cs_code=a['cs_code'], cs_e0=a['cs_e0'], cs_role=role, margin=margin,
                        margin_subwindows=msub, margin_unoriented=mraw, first_is_attended=fia, scored=scored, sub_window_starts_s=np.array(SUB_OFFS_S))
    per_we = t_train / max(1, len(history)) / max(1, len(windows))
    rec = {'status': 'complete' if all(v for k, v in checks.items() if k.endswith(('_ok', 'finite'))) else 'check_failed',
           'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'dest': str(dest), 'npz_sha256': sha(dest / 'margins.npz'),
           'final_model_sha256': None if probe else sha(dest / 'final_model.pt'), 'epochs_run': len(history), 'history': history,
           'final_clip_loss': history[-1]['clip_loss'] if history else None, 'n_train_windows': len(windows),
           'n_scored_segments': {'train_side': int((scored == 'train_side').sum()), 'test': int((scored == 'test').sum())},
           'seconds': {'prepare': round(t_prep, 1), 'train': round(t_train, 1), 'score': round(t_score, 1), 'total': round(time.time() - t_all, 1)},
           'train_seconds_per_window_epoch': per_we, 'score_seconds_per_window': t_score / max(1, len(sw)),
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'full_unit_counts': full_counts,
           'projected_full_unit_hours': (per_we * full_counts['train_windows'] * EPOCHS + t_score / max(1, len(sw)) * full_counts['score_windows']) / 3600,
           'device': torch.cuda.get_device_name(0), 'job': job, 'checks': checks}
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], 'cf', cf, 'sf', sf, rec['status'], rec['seconds'], flush=True)
    assert rec['status'] == 'complete', checks
    return rec


def smoke():
    job = os.environ['SLURM_JOB_ID']; plan = make_plan(); verify(plan)
    receipt = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
    try:
        row = plan['rows'][0]
        rc = subprocess.run([sys.executable, '-B', '-u', '-m', XF.DISPATCH, 'unit', '--id', row['id'], '--probe', '--system', SYSTEM]).returncode
        assert rc == 0, rc
        rec = read(OUT / 'probes' / job / 'units' / f'{row["id"]}.json')
        assert rec['status'] == 'complete' and rec['n_scored_segments']['test'] == 0 and rec['checks']['eeg_channels'] == 31
        receipt['units'].append({k: rec[k] for k in ('row', 'seconds', 'gpu_peak_mb', 'device', 'projected_full_unit_hours', 'full_unit_counts',
                                                     'train_seconds_per_window_epoch', 'score_seconds_per_window', 'checks', 'history')})
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', receipt)


def unit_cli(uid, probe):
    plan = read(OUT / 'plan.json'); verify(plan)
    run_unit(next(r for r in plan['rows'] if r['id'] == uid), plan, probe)


def fleet_status():
    return XF.fleet_status(sys.modules[__name__], slots=2, max_units=1)


if __name__ == '__main__':
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if sys.argv[1:] == ['prepare']:
        prepare()
