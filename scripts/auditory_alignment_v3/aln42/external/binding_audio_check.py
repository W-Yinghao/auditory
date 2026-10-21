"""Binding evidence: which raw-audio version underlies the stimulus envelope the core3 pipeline actually uses?

Core3 (auditory_alignment.data.load_dtu -> frozen.py 'Local' row 5) uses dtu_cf{cf}.h5 [sha]/Local[5] = 1-8 Hz FIR
band-pass of the 128 Hz Hilbert envelope of the 16 kHz mono waveform (prep_targets.run_dtu_audio / run_dtu).
For FIT-role two-talker segments only (content role 'fit' of the given content fold; no EEG is read), we recompute the
same envelope from every available raw version of the target and masker streams (HI: CamEQ 'stimuli' file, 'woa' file
in stimuli/ and in stimuli-woa/, 'woacontrol'; NH: plain file) and correlate it per 5 s segment with
  (A) the core3 envelope Local[5] at the segment's samples, and
  (B) the official derivative envelopes (derivatives/stimuli/<rel>.mat and <rel>woa.mat; t re trial onset),
      interpolated to the 128 Hz trial grid and band-passed identically.
Output: per hearing group x stream x version, median / 5th percentile r and the waveform sha256 of each version.
"""
import glob, json, os, sys, hashlib, collections
import numpy as np
import pandas as pd
import scipy.io as sio
from scipy.signal import hilbert, resample_poly
from auditory_alignment import data as D
from auditory_alignment import prep_targets as PT
from auditory_c3.features_dtu import _mono16k

out = sys.argv[1]
S = '/projects/EEG-foundation-model/auditory_public/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl'
AUD = '/projects/EEG-foundation-model/auditory_public/dtu_snhl/audio_drcmr'
F = '/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/dtu'
TRIALS_PER_PERSON = 2
part = pd.read_csv(f'{S}/participants.tsv', sep='\t'); hs = dict(zip(part.participant_id, part.hearing_status))
inv = {(r['file'], r['trial'], r['kind']): r for r in json.load(open(f'{F}/inventory.json'))}
cg = json.load(open(f'{F}/kcs_targets_v1/content_groups.json'))['content']
subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(D.REPO, 'private', 'auditory_c3', 'public', 'dtu_v2', '*.json')))
import h5py


def env128(x16):
    return resample_poly(np.abs(hilbert(x16.astype(np.float64))), 1, 125)


def bp(x):
    return PT._bp(x)[0]


def official(rel, n):
    d = sio.loadmat(os.path.join(S, 'derivatives', 'stimuli', rel), squeeze_me=True, struct_as_record=False)
    st = [v for k, v in d.items() if not k.startswith('__')][0]
    feat, tt = np.asarray(st.feat, float).ravel(), np.asarray(st.t, float).ravel()
    return np.interp(np.arange(n) / 128.0, tt, feat, left=np.nan, right=np.nan)


def corr(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok] - a[ok].mean(), b[ok] - b[ok].mean()
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12)) if ok.sum() > 100 else np.nan


res = {'rule': 'content role fit only; no EEG read', 'by_cf': {}}
shas = {}
for cf in (0, 1):
    tf = h5py.File(f'{F}/kcs_targets_v1/dtu_cf{cf}.h5', 'r')
    R = collections.defaultdict(list)
    n_tr = collections.Counter()
    for sub in subs:
        hi = hs[sub] == 'hi'
        with h5py.File(os.path.join(D.DTU_PRE, f'{sub}.h5'), 'r') as f:
            keys = sorted(f.keys())
            picked = 0
            for k in keys:
                g = f[k]
                if str(g.attrs['talkers']) != 'twotalker':
                    continue
                th = inv.get((sub, k, 'target'), {}).get('sha'); mh = inv.get((sub, k, 'masker'), {}).get('sha')
                if th not in cg or th not in tf or mh not in tf:
                    continue
                c = cg[th]
                if c['half'] == cf or c['early_stop']:      # keep content role 'fit' only
                    continue
                n = g['eeg_1_20'].shape[1]; mon = float(g.attrs['masker_onset_rel_s']); lead = int(round(inv[(sub, k, 'masker')]['offset_s'] * 128))
                fs_ = 128; seg_len = 640; margin = int(D.MAX_WIN_S * fs_) + 1 + D.AUDIO_FRAMES
                a0 = max(64, int(np.ceil((mon + 1.7) * fs_)))
                starts = D._segments_of(a0, n, seg_len, margin)
                if not starts:
                    continue
                rel_t = str(g.attrs['stim_file'])
                for kind, rel in (('target', rel_t), ('masker', rel_t.replace('/target/t', '/masker/m'))):
                    sha_core = th if kind == 'target' else mh
                    core = tf[f'{sha_core}/Local'][()][5].astype(np.float64)
                    off = 0 if kind == 'target' else lead
                    base = rel[:-4]
                    vers = {'plain': glob.glob(os.path.join(AUD, 'stimuli', '*', rel))}
                    if hi:
                        vers.update({'woa(stimuli)': glob.glob(os.path.join(AUD, 'stimuli', '*', base + 'woa.wav')),
                                     'woa(stimuli-woa)': glob.glob(os.path.join(AUD, 'stimuli-woa', '*', base + 'woa.wav')),
                                     'woacontrol': glob.glob(os.path.join(AUD, 'stimuli', '*', base + 'woacontrol.wav'))})
                    envs = {}
                    for v, p in vers.items():
                        if not p:
                            continue
                        x, h = _mono16k(p[0]); shas[(sub, k, kind, v)] = h
                        e = bp(env128(x)); envs[v] = e
                        R[(hs[sub], kind, v, 'is_core3_sha')].append(float(h == sha_core))
                    offs = {'derivative': official(base + '.mat', n + 2000)}
                    if os.path.exists(os.path.join(S, 'derivatives', 'stimuli', base + 'woa.mat')):
                        offs['derivative_woa'] = official(base + 'woa.mat', n + 2000)
                    offs = {k2: bp(np.nan_to_num(v2, nan=np.nanmean(v2))) * np.where(np.isfinite(v2), 1, np.nan) for k2, v2 in offs.items()}
                    for st in starts:
                        for v, e in envs.items():
                            i = st - off
                            seg = e[i:i + seg_len]
                            R[(hs[sub], kind, v, 'vs_core3_Local5')].append(corr(seg, core[i:i + seg_len]))
                            for k2, o in offs.items():
                                R[(hs[sub], kind, v, f'vs_{k2}')].append(corr(seg, o[st:st + seg_len]))
                picked += 1; n_tr[hs[sub]] += 1
                if picked >= TRIALS_PER_PERSON:
                    break
    summ = {}
    for (grp, kind, v, what), vals in sorted(R.items()):
        a = np.asarray(vals, float); a = a[np.isfinite(a)]
        summ[f'{grp}|{kind}|{v}|{what}'] = {'n': int(len(a)), 'median': float(np.median(a)) if len(a) else None,
                                            'p05': float(np.percentile(a, 5)) if len(a) else None}
    res['by_cf'][str(cf)] = {'n_trials': dict(n_tr), 'summary': summ}
    print(cf, json.dumps(summ, indent=0), flush=True)
# identical-waveform check between the two 'woa' copies
same = [shas[(s, k, kd, 'woa(stimuli)')] == shas[(s, k, kd, 'woa(stimuli-woa)')] for (s, k, kd, v) in shas if v == 'woa(stimuli)' and (s, k, kd, 'woa(stimuli-woa)') in shas]
res['woa_copies_identical_fraction'] = float(np.mean(same)) if same else None
json.dump(res, open(out, 'w'), indent=1)
print('woa copies identical', res['woa_copies_identical_fraction'])
