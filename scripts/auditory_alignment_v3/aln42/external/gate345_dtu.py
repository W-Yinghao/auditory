"""Gates 3-5 of the ALN4.2 R3 MindMix readiness check (CPU, training-side data only; no test-person or test-content scoring).

Gate 3  input contract evidence on DTU44: raw wav format, target/masker identity and onset alignment against the official
        derivative envelopes (t vector 're trial onset'), channel order vs the MindMix 64-name list, census of fit-role
        two-talker 5 s segments for the 10 public units (for the cost estimate).
Gate 4  blind candidate scorer: official privileged-slot scorer vs the mechanical order-symmetrised per-sample margin;
        synthetic and real training-side windows; swap equivariance, batch-composition invariance, label never input.
Gate 5  one official contrastive training step (forward + backward + AdamW step) on a tiny real DTU batch.

Probe people/trials: content fold 0, person fold 0; people with fold != 0 (training side), trials whose content role is
'fit' (content half 1, not early-stop).  Paper Appendix A.2 preprocessing is reproduced from raw BDF/wav.
"""
import glob, json, math, os, resource, sys, time
import numpy as np
import pandas as pd
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm_common as C
from auditory_alignment import data as D   # read-only import of the frozen fold helper and paths

OUT = sys.argv[1]
ROOT = '/projects/EEG-foundation-model/auditory_public'
S = f'{ROOT}/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl'
AUD = f'{ROOT}/dtu_snhl/audio_drcmr'
CF, SF = 0, 0
FS_EEG, FS_AUD, WIN_S = 200, 16000, 2.0
SUB_OFFS = (0.5, 2.5)          # two non-overlapping 2 s sub-windows per 5 s physical segment (centred)
res = {'probe': {'content_fold': CF, 'person_fold': SF, 'subwindow_offsets_s': SUB_OFFS}}
t_start = time.time()

# ------------------------------------------------------------------ identities, folds, roles (frozen project helpers)
part = pd.read_csv(f'{S}/participants.tsv', sep='\t')
hs = dict(zip(part.participant_id, part.hearing_status))
subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(D.REPO, 'private', 'auditory_c3', 'public', 'dtu_v2', '*.json')))
folds = D._folds({g: [s for s in subs if hs[s] == g] for g in ('nh', 'hi')})
inv = json.load(open(f'{ROOT}/derived/c3_features_v1/dtu/inventory.json'))
INV = {(r['file'], r['trial'], r['kind']): r for r in inv}
cg = json.load(open(os.path.join(D.DTU_KCS, 'content_groups.json')))['content']


def role(sub, trial, cf):
    r = INV.get((sub, trial, 'target'))
    if r is None or r.get('sha') not in cg:
        return None
    c = cg[r['sha']]
    return 'test' if c['half'] == cf else ('es' if c['early_stop'] else 'fit')


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
                    'mstim': m.iloc[0].stim_file if len(m) else None, 'mstim_woa': m.iloc[0].stim_file_without_cambridge_eq if len(m) else None})
    return out


def seg_starts(tr):
    """5 s cs segment starts (s, re trial onset) exactly as auditory_alignment.data.load_dtu (128 Hz grid)."""
    fs = 128; seg_len = int(D.SEG_S * fs); margin = int(D.MAX_WIN_S * fs) + 1 + D.AUDIO_FRAMES
    n = int(round((round(tr['t1'] * 512) - round(tr['t0'] * 512)) / 512 * fs))
    a0 = max(64, int(np.ceil((tr['mon'] + 1.7) * fs)))
    return [st / fs for st in D._segments_of(a0, n, seg_len, margin)]


TR = {s: trials_of(s) for s in subs}
# census: fit/es two-talker 5 s segments of training people per public unit (cost estimate only; no EEG read)
census = {}
for cf in (0, 1):
    for sf in range(5):
        cnt = {'fit': 0, 'es': 0, 'test_people_test_role': 0}
        for s in subs:
            for tr in TR[s]:
                if not tr['two'] or INV.get((s, tr['trial'], 'masker')) is None:
                    continue
                ro = role(s, tr['trial'], cf)
                if ro is None:
                    continue
                n = len(seg_starts(tr))
                if folds[s] != sf and ro in ('fit', 'es'):
                    cnt[ro] += n
                elif folds[s] == sf and ro == 'test':
                    cnt['test_people_test_role'] += n
        census[f'cf{cf}_sf{sf}'] = cnt
res['census_cs_5s_segments'] = census

# ------------------------------------------------------------------ gate 3: probe trials and alignment evidence
train_people = [s for s in subs if folds[s] != SF]
probe_people = [next(s for s in train_people if hs[s] == 'nh'), next(s for s in train_people if hs[s] == 'hi')]
probe = []
for s in probe_people:
    fit_tr = [tr for tr in TR[s] if tr['two'] and role(s, tr['trial'], CF) == 'fit']
    probe += [(s, tr) for tr in fit_tr[:2]]
res['probe']['people'] = {s: {'group': hs[s], 'person_fold': folds[s]} for s in probe_people}
res['probe']['trials'] = [(s, tr['trial']) for s, tr in probe]
assert all(folds[s] != SF and role(s, tr['trial'], CF) == 'fit' for s, tr in probe)

import soundfile as sf
import scipy.io as sio
from scipy.signal import butter, sosfiltfilt, resample_poly


def wav_path(rel, hi):
    """Project convention (auditory_c3/features_dtu.py): HI -> 'woa' (no CamEQ) file, NH -> plain file."""
    if hi:
        c = glob.glob(os.path.join(AUD, 'stimuli-woa', '*', rel))
    else:
        c = glob.glob(os.path.join(AUD, 'stimuli', '*', rel))
    return c[0] if c else None


def env512(x, sr):
    """Crude broadband envelope (|x|^0.3, anti-aliased resampling to 512 Hz) for onset-alignment checks only."""
    from fractions import Fraction
    fr = Fraction(512, sr).limit_denominator(100000)
    return resample_poly(np.abs(x) ** 0.3, fr.numerator, fr.denominator)


def best_lag(ours_t0, ours, mat):
    """Correlate our envelope (first sample at trial time ours_t0) with the official envelope on its own t grid;
    return lag (ms) maximising r within +-1 s and r at lag 0."""
    d = sio.loadmat(mat, squeeze_me=True, struct_as_record=False)
    st = [v for k, v in d.items() if not k.startswith('__')][0]
    feat, efs, tt = np.asarray(st.feat, float).ravel(), float(st.fs), np.asarray(st.t, float).ravel()
    assert abs(efs - 512) < 1e-6
    grid = ours_t0 + np.arange(len(ours)) / 512.0
    ref = np.interp(grid, tt, feat, left=np.nan, right=np.nan)
    ok = ~np.isnan(ref)
    a, b = ours[ok], ref[ok]
    a = (a - a.mean()) / a.std(); b = (b - b.mean()) / b.std()
    lags = np.arange(-512, 513, 2)
    rs = [np.mean(a[max(0, L):len(a) + min(0, L)] * b[max(0, -L):len(b) - max(0, L)]) for L in lags]
    j = int(np.argmax(rs))
    return {'t_first_official_s': float(tt[0]), 't_last_official_s': float(tt[-1]), 'best_lag_ms': float(lags[j] / 512 * 1000),
            'r_best': float(rs[j]), 'r_lag0': float(rs[len(lags) // 2]), 'n_overlap': int(ok.sum())}


align = []
for s, tr in probe:
    hi = hs[s] == 'hi'
    rec = {'sub': s, 'trial': tr['trial'], 'group': hs[s], 'trial_dur_s': tr['t1'] - tr['t0'], 'masker_onset_rel_s': tr['mon']}
    for kind, rel_plain, rel_woa, t0 in (('target', tr['stim'], tr['stim_woa'], 0.0), ('masker', tr['mstim'], tr['mstim_woa'], tr['mon'])):
        rel = rel_woa if hi else rel_plain
        p = wav_path(rel, hi)
        x, sr = sf.read(p, dtype='float64', always_2d=True)
        info = {'path': os.path.relpath(p, ROOT), 'sr': sr, 'channels': x.shape[1], 'dur_s': len(x) / sr,
                'inventory_path_matches': (INV[(s, tr['trial'], kind)]['path'] == p),
                'stereo_lr_corr': float(np.corrcoef(x[:, 0], x[:, 1])[0, 1]) if x.shape[1] == 2 else None}
        mat = os.path.join(S, 'derivatives', 'stimuli', os.path.splitext(rel)[0] + '.mat')
        info['official_env'] = best_lag(t0, env512(x.mean(1), sr), mat)
        if hi:   # CamEQ (heard) file exists too?
            pc = glob.glob(os.path.join(AUD, 'stimuli', '*', rel_plain))
            info['cameq_file_present'] = bool(pc)
            if pc:
                y, _ = sf.read(pc[0], dtype='float64', always_2d=True)
                n = min(len(y), len(x)); info['cameq_vs_woa_corr_mono'] = float(np.corrcoef(y[:n].mean(1), x[:n].mean(1))[0, 1])
                info['cameq_dur_s'] = len(y) / sr
        rec[kind] = info
    align.append(rec)
res['gate3_alignment'] = align
print(json.dumps(align, indent=1), flush=True)

# channel contract
import universal_eeg_finetune as UEF
ch = pd.read_csv(f'{S}/{probe_people[0]}/eeg/{probe_people[0]}_task-selectiveattention_channels.tsv', sep='\t')
eeg64 = [n for n, t in zip(ch['name'], ch['type']) if str(t).lower() == 'eeg'][:64]
res['gate3_channels'] = {'dtu_first64_eeg': eeg64, 'mindmix_ch_names_equal_casefold_same_order': [c.upper() for c in eeg64] == UEF.ch_names,
                         'units_tsv': sorted(set(ch['units'].astype(str))), 'reference': 'CMS/DRL (recorded)'}

# ------------------------------------------------------------------ MindMix inputs from raw data (paper A.2)
import mne
SOS = butter(4, [1.0, 40.0], btype='bandpass', fs=512, output='sos')


def windows_for(s, tr, max_segments=2):
    bdf = glob.glob(f'{S}/{s}/eeg/{s}_task-selectiveattention_eeg.bdf')[0]
    raw = mne.io.read_raw_bdf(bdf, preload=False, verbose=False)
    assert raw.info['sfreq'] == 512
    c0 = max(0.0, tr['t0'] - 10.0); c1 = min(raw.times[-1], tr['t1'] + 10.0)
    raw.crop(c0, c1).load_data(verbose=False)
    X = raw.get_data(picks=eeg64) * 1e6
    Xf = sosfiltfilt(SOS, X, axis=1)
    X200 = resample_poly(Xf, 25, 64, axis=1)
    hi = hs[s] == 'hi'
    xa, sra = sf.read(wav_path(tr['stim_woa'] if hi else tr['stim'], hi), dtype='float64', always_2d=True)
    xm, _ = sf.read(wav_path(tr['mstim_woa'] if hi else tr['mstim'], hi), dtype='float64', always_2d=True)
    assert sra == 44100
    A16, M16 = resample_poly(xa.mean(1), 160, 441), resample_poly(xm.mean(1), 160, 441)
    out = []
    for st in seg_starts(tr)[:max_segments]:
        for o in SUB_OFFS:
            ts = st + o                                       # trial time (s) of the 2 s window start
            i = int(round((tr['t0'] - c0 + ts) * FS_EEG))
            e = X200[:, i:i + int(WIN_S * FS_EEG)]
            e = (e - e.mean(1, keepdims=True)) / (e.std(1, keepdims=True) + 1e-8)
            ja = int(round(ts * FS_AUD)); jm = int(round((ts - tr['mon']) * FS_AUD)); L = int(WIN_S * FS_AUD)
            assert jm >= 0 and ja + L <= len(A16) and jm + L <= len(M16)
            a = A16[ja:ja + L]; m = M16[jm:jm + L]
            out.append({'eeg': e.astype(np.float32), 'att': (a / np.abs(a).max()).astype(np.float32), 'ign': (m / np.abs(m).max()).astype(np.float32),
                        'sub': s, 'trial': tr['trial'], 'seg_start_s': st, 'win_start_s': ts})
    return out


W = []
for s, tr in probe:
    W += windows_for(s, tr)
res['real_windows'] = [{k: v for k, v in w.items() if k in ('sub', 'trial', 'seg_start_s', 'win_start_s')} for w in W]
E = torch.tensor(np.stack([w['eeg'] for w in W])); AT = torch.tensor(np.stack([w['att'] for w in W])); IG = torch.tensor(np.stack([w['ign'] for w in W]))
res['real_batch_shapes'] = {'eeg': list(E.shape), 'att': list(AT.shape), 'ign': list(IG.shape)}
print('real windows', len(W), E.shape, AT.shape, round(time.time() - t_start, 1), 's', flush=True)

# ------------------------------------------------------------------ gate 4: scorers
model, args, _ = C.build(fix_pos_conv=True, quiet=True)
model.eval()
logit = lambda: model.clip_loss.logit_scale.exp()


def official_pred(eeg, tgt, neg):
    """universal_trainer._evaluate_contrastive verbatim: prediction 1 means 'slot-1 (target) wins'."""
    fe, ft, fn = model.forward_contrastive(eeg, tgt, neg)
    pA = model.clip_loss.get_probabilities(fe, ft).diagonal(); pB = model.clip_loss.get_probabilities(fe, fn).diagonal()
    return (pA > pB).long(), pA, pB


def pair_logits(eeg, c1, c2):
    """One official forward_contrastive call -> per-sample scaled cosines s(c1|c1), s(c2|c1) (row diagonals of get_scores)."""
    fe, f1, f2 = model.forward_contrastive(eeg, c1, c2)
    n = torch.nn.functional.normalize
    return (n(fe, dim=-1) * n(f1, dim=-1)).sum(-1) * logit(), (n(fe, dim=-1) * n(f2, dim=-1)).sum(-1) * logit()


def blind_margin(eeg, c1, c2):
    """Order-symmetrised official logit difference: m = 1/2[(s(c1|c1)-s(c2|c1)) - (s(c2|c2)-s(c1|c2))]; >0 favours c1."""
    s11, s21 = pair_logits(eeg, c1, c2)
    s22, s12 = pair_logits(eeg, c2, c1)
    return 0.5 * ((s11 - s21) - (s22 - s12))


def invariance_suite(eeg, c1, c2, tag, extra=None):
    out = {}
    with torch.no_grad():
        m = blind_margin(eeg, c1, c2); ms = blind_margin(eeg, c2, c1)
        out['swap_max_abs(m(c1,c2)+m(c2,c1))'] = float((m + ms).abs().max())
        out['swap_choice_consistent'] = bool(((m > 0) == (ms < 0)).all() | ((m == 0) & (ms == 0)).all())
        singles = torch.cat([blind_margin(eeg[i:i + 1], c1[i:i + 1], c2[i:i + 1]) for i in range(len(eeg))])
        out['batch1_vs_full_max_abs'] = float((singles - m).abs().max())
        perm = torch.randperm(len(eeg), generator=torch.Generator().manual_seed(3401))
        mp = blind_margin(eeg[perm], c1[perm], c2[perm])
        out['permuted_vs_full_max_abs'] = float((mp - m[perm]).abs().max())
        if extra is not None:
            e2, a2, b2 = extra
            mx = blind_margin(torch.cat([eeg, e2]), torch.cat([c1, a2]), torch.cat([c2, b2]))[:len(eeg)]
            out['with_unrelated_samples_max_abs'] = float((mx - m).abs().max())
        out['decision_flips_under_batching'] = int(((singles > 0) != (m > 0)).sum())
        out['margin_scale_abs_mean'] = float(m.abs().mean())
        # official scorer diagnostics
        p_full, pA, pB = official_pred(eeg, c1, c2)
        p_sw, _, _ = official_pred(eeg, c2, c1)
        p_single = torch.cat([official_pred(eeg[i:i + 1], c1[i:i + 1], c2[i:i + 1])[0] for i in range(len(eeg))])
        out['official_batch1_always_tie_pred0'] = bool((p_single == 0).all())
        out['official_slot1_wins_in_both_orders_fraction'] = float(((p_full == 1) & (p_sw == 1)).float().mean())
        out['official_swap_consistent_fraction'] = float((p_full != p_sw).float().mean())
        p_perm = official_pred(eeg[perm], c1[perm], c2[perm])[1]
        out['official_diag_prob_change_under_permutation_max_abs'] = float((p_perm - pA[perm]).abs().max())
        if extra is not None:
            pAx = official_pred(torch.cat([eeg, e2]), torch.cat([c1, a2]), torch.cat([c2, b2]))[1][:len(eeg)]
            out['official_diag_prob_change_with_unrelated_samples_max_abs'] = float((pAx - pA).abs().max())
    print(tag, json.dumps(out, indent=1), flush=True)
    return out


g = torch.Generator().manual_seed(3401)
B = 6
syn = (torch.randn(B, 64, 400, generator=g), torch.randn(B, 32000, generator=g) * 0.1, torch.randn(B, 32000, generator=g) * 0.1)
syn_extra = (torch.randn(3, 64, 400, generator=g), torch.randn(3, 32000, generator=g) * 0.1, torch.randn(3, 32000, generator=g) * 0.1)
res['gate4_synthetic'] = invariance_suite(*syn, 'synthetic', extra=syn_extra)
res['gate4_real_training_side'] = invariance_suite(E, AT, IG, 'real', extra=syn_extra)
# train-mode stochasticity (dropout / drop_path / wav2vec2 SpecAugment): scoring must be in eval mode
model.train()
with torch.no_grad():
    torch.manual_seed(1); m1 = blind_margin(E[:2], AT[:2], IG[:2]); torch.manual_seed(2); m2 = blind_margin(E[:2], AT[:2], IG[:2])
res['gate4_train_mode_nondeterministic_max_abs'] = float((m1 - m2).abs().max())
model.eval()
res['gate4_scorer'] = {
    'official': 'universal_trainer._evaluate_contrastive: fused_eeg = CALRA(eeg, target_audio); pA = softmax_over_batch(sim(fused_eeg, aligned_target))[i,i]; '
                'pB = softmax_over_batch(sim(fused_eeg, aligned_negative))[i,i]; pred = pA > pB; label := 1 for every sample',
    'blind': 'm(c1,c2) = 1/2[(s(c1|c1) - s(c2|c1)) - (s(c2|c2) - s(c1|c2))], s(x|t) = logit_scale.exp() * cos(fused_eeg(eeg, t), aligned_audio(eeg, x)) '
             'from two official forward_contrastive calls (t=c1 then t=c2), eval mode; choose c1 iff m>0, tie (m==0) credit 0.5'}

# ------------------------------------------------------------------ gate 5: one official training step on real DTU windows
_, UM, UT = C.official_modules()
torch.manual_seed(3401)
trainer = UT.create_trainer(args.strategy, model, torch.device('cpu'), args)
trainer.setup_optimizer()
before = {n: p.detach().clone() for n, p in model.named_parameters()}
model.train()
idx = torch.arange(4)
t0 = time.time()
trainer.optimizer.zero_grad()
loss = trainer._train_contrastive(E[idx], AT[idx], IG[idx])
loss.backward()
t_fb = time.time() - t0
gn = {}
for n, p in model.named_parameters():
    key = n.split('.')[0] if not n.startswith(('eeg_encoder', 'audio_encoder')) else '.'.join(n.split('.')[:2])
    if p.grad is None:
        gn.setdefault(key, {'none': 0, 'sq': 0.0, 'finite': True})['none'] += 1
    else:
        d = gn.setdefault(key, {'none': 0, 'sq': 0.0, 'finite': True}); d['sq'] += float(p.grad.pow(2).sum()); d['finite'] &= bool(torch.isfinite(p.grad).all())
trainer.optimizer.step()
changed = {}
for n, p in model.named_parameters():
    key = n.split('.')[0] if not n.startswith(('eeg_encoder', 'audio_encoder')) else '.'.join(n.split('.')[:2])
    changed.setdefault(key, 0); changed[key] += int(not torch.equal(before[n], p.detach()))
res['gate5'] = {'batch': 4, 'loss': float(loss), 'forward_backward_seconds_cpu2': round(t_fb, 2),
                'grad_norm_per_module': {k: {'norm': math.sqrt(v['sq']), 'params_without_grad': v['none'], 'finite': v['finite']} for k, v in gn.items()},
                'params_changed_after_step_per_module': changed, 'lr_after_setup': trainer.optimizer.param_groups[0]['lr'],
                'max_rss_gb': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6}
print('gate5', json.dumps(res['gate5'], indent=1), flush=True)

# official LR trajectory (setup_optimizer + update_learning_rate(epoch) after each epoch), dummy parameter
dummy = torch.nn.Linear(1, 1)
tr2 = UT.create_trainer(args.strategy, dummy, torch.device('cpu'), args); tr2.setup_optimizer()
lrs = []
for ep in range(args.epochs):
    lrs.append(tr2.optimizer.param_groups[0]['lr']); tr2.optimizer.step(); tr2.update_learning_rate(ep)
res['official_lr_per_epoch'] = lrs
res['seconds_total'] = round(time.time() - t_start, 1)
json.dump(res, open(OUT, 'w'), indent=1, default=str)
print('done', res['seconds_total'])
