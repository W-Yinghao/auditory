"""DTU44 -> MindMix input adapter (readiness version; same code path as gate345_dtu.py).

Paper Appendix A.2 contract: raw BDF 64 scalp channels (BioSemi order == MindMix ch_names), recorded CMS reference,
zero-phase 4th-order Butterworth band-pass 1-40 Hz (scipy butter(N=4) + sosfiltfilt), resample 512 -> 200 Hz
(resample_poly 25/64), 2 s windows (400 samples), per-window per-channel z-score.  Audio: 44.1 kHz stereo wav ->
mono (L/R mean) -> 16 kHz (resample_poly 160/441) -> 2 s window (32000) -> divide by peak |x|.
Time base (verified against the official derivative envelopes): target wav sample 0 = targetonset event;
masker wav sample 0 = maskeronset event.  HI listeners: 'woa' (no CamEQ) files; NH: plain files (project convention,
auditory_c3/features_dtu.py).  Windows: two 2 s sub-windows at +0.5 s and +2.5 s inside each project 5 s cs segment
(auditory_alignment.data.load_dtu geometry).  Readiness only: the BDF is cropped to the trial +-10 s before filtering;
the production adapter should filter the continuous run as the project preprocessing does.
"""
import glob, os
import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt, resample_poly
from auditory_alignment import data as D

ROOT = '/projects/EEG-foundation-model/auditory_public'
S = f'{ROOT}/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl'
AUD = f'{ROOT}/dtu_snhl/audio_drcmr'
FS_EEG, FS_AUD, WIN_S = 200, 16000, 2.0
SUB_OFFS = (0.5, 2.5)
SOS = butter(4, [1.0, 40.0], btype='bandpass', fs=512, output='sos')


def trials_of(sub):
    ev = pd.read_csv(glob.glob(f'{S}/{sub}/eeg/{sub}_task-selectiveattention_events.tsv')[0], sep='\t')
    on = ev[ev.trigger_type == 'targetonset'].reset_index(drop=True)
    ends = ev[ev.trigger_type.isin(['trialend', 'error_terminated'])]
    mk = ev[ev.trigger_type == 'maskeronset']
    out = []
    for i, r in on.iterrows():
        t0 = float(r.onset); later = ends[ends.onset > t0]
        if later.empty:
            continue
        t1 = float(later.iloc[0].onset); m = mk[(mk.onset > t0) & (mk.onset < t1)]
        out.append({'trial': f'trial_{i + 1:03d}', 't0': t0, 't1': t1, 'two': r.single_talker_two_talker == 'twotalker',
                    'mon': float(m.iloc[0].onset - t0) if len(m) else None, 'stim': r.stim_file, 'stim_woa': r.stim_file_without_cambridge_eq,
                    'mstim': m.iloc[0].stim_file if len(m) else None, 'mstim_woa': m.iloc[0].stim_file_without_cambridge_eq if len(m) else None,
                    'attend_lr': r.attend_left_right})
    return out


def seg_starts(tr):
    fs = 128; seg_len = int(D.SEG_S * fs); margin = int(D.MAX_WIN_S * fs) + 1 + D.AUDIO_FRAMES
    n = int(round((round(tr['t1'] * 512) - round(tr['t0'] * 512)) / 512 * fs))
    a0 = max(64, int(np.ceil((tr['mon'] + 1.7) * fs)))
    return [st / fs for st in D._segments_of(a0, n, seg_len, margin)]


def wav_path(rel, hi):
    c = glob.glob(os.path.join(AUD, 'stimuli-woa' if hi else 'stimuli', '*', rel))
    return c[0] if c else None


def eeg64(sub):
    ch = pd.read_csv(f'{S}/{sub}/eeg/{sub}_task-selectiveattention_channels.tsv', sep='\t')
    return [n for n, t in zip(ch['name'], ch['type']) if str(t).lower() == 'eeg'][:64]


def windows_for(sub, tr, hi, max_segments=2):
    import mne, soundfile as sf
    bdf = glob.glob(f'{S}/{sub}/eeg/{sub}_task-selectiveattention_eeg.bdf')[0]
    raw = mne.io.read_raw_bdf(bdf, preload=False, verbose=False)
    assert raw.info['sfreq'] == 512
    c0 = max(0.0, tr['t0'] - 10.0); c1 = min(raw.times[-1], tr['t1'] + 10.0)
    raw.crop(c0, c1).load_data(verbose=False)
    X200 = resample_poly(sosfiltfilt(SOS, raw.get_data(picks=eeg64(sub)) * 1e6, axis=1), 25, 64, axis=1)
    xa, sra = sf.read(wav_path(tr['stim_woa'] if hi else tr['stim'], hi), dtype='float64', always_2d=True)
    xm, _ = sf.read(wav_path(tr['mstim_woa'] if hi else tr['mstim'], hi), dtype='float64', always_2d=True)
    assert sra == 44100
    A16, M16 = resample_poly(xa.mean(1), 160, 441), resample_poly(xm.mean(1), 160, 441)
    out = []
    for st in seg_starts(tr)[:max_segments]:
        for o in SUB_OFFS:
            ts = st + o
            i = int(round((tr['t0'] - c0 + ts) * FS_EEG))
            e = X200[:, i:i + int(WIN_S * FS_EEG)]
            e = (e - e.mean(1, keepdims=True)) / (e.std(1, keepdims=True) + 1e-8)
            ja = int(round(ts * FS_AUD)); jm = int(round((ts - tr['mon']) * FS_AUD)); L = int(WIN_S * FS_AUD)
            assert jm >= 0 and ja + L <= len(A16) and jm + L <= len(M16)
            a = A16[ja:ja + L]; m = M16[jm:jm + L]
            out.append({'eeg': e.astype(np.float32), 'att': (a / np.abs(a).max()).astype(np.float32),
                        'ign': (m / np.abs(m).max()).astype(np.float32), 'sub': sub, 'trial': tr['trial'], 'seg_start_s': st, 'win_start_s': ts,
                        'attend_lr': tr['attend_lr']})
    return out
