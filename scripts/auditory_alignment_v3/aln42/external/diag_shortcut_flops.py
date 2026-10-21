"""Readiness diagnostics (training-side windows only; released checkpoint, no fine-tuning, eval mode):

(1) Official Stage-3 objective (ClipLoss on model(eeg, audio, mode='clip_train'), in-batch negatives) when the 'target'
    slot holds the attended stream, the ignored stream, or unrelated noise, and when the EEG is replaced by noise.
    A near-zero loss for mismatched inputs means the in-batch objective is satisfied by the target-conditioned CALRA
    fusion itself (both embeddings of the positive pair share CALRA(eeg_i, a_i)), not by EEG-audio correspondence.
(2) FLOPs per sample (torch.utils.flop_counter) for one training step and one blind-scorer call, for the GPU estimate.
"""
import glob, json, os, sys
import numpy as np
import pandas as pd
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm_common as C
import dtu_mm_input as M
from auditory_alignment import data as D

out = sys.argv[1]
part = pd.read_csv(f'{M.S}/participants.tsv', sep='\t'); hs = dict(zip(part.participant_id, part.hearing_status))
subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(D.REPO, 'private', 'auditory_c3', 'public', 'dtu_v2', '*.json')))
folds = D._folds({g: [s for s in subs if hs[s] == g] for g in ('nh', 'hi')})
inv = {(r['file'], r['trial'], r['kind']): r for r in json.load(open(f'{M.ROOT}/derived/c3_features_v1/dtu/inventory.json'))}
cg = json.load(open(os.path.join(D.DTU_KCS, 'content_groups.json')))['content']
W = []
for grp in ('nh', 'hi'):
    sub = next(s for s in subs if folds[s] != 0 and hs[s] == grp)
    trs = [t for t in M.trials_of(sub) if t['two'] and cg[inv[(sub, t['trial'], 'target')]['sha']]['half'] != 0
           and not cg[inv[(sub, t['trial'], 'target')]['sha']]['early_stop']][:2]
    for t in trs:
        W += M.windows_for(sub, t, hi=(grp == 'hi'), max_segments=2)
E = torch.tensor(np.stack([w['eeg'] for w in W])); AT = torch.tensor(np.stack([w['att'] for w in W])); IG = torch.tensor(np.stack([w['ign'] for w in W]))
g = torch.Generator().manual_seed(3401)
NZ = torch.randn(AT.shape, generator=g); NZ = NZ / NZ.abs().amax(1, keepdim=True)
EN = torch.randn(E.shape, generator=g)
model, args, _ = C.build(fix_pos_conv=True, quiet=True)
model.eval()
res = {'n_windows': len(W), 'windows': [(w['sub'], w['trial'], w['win_start_s']) for w in W], 'objective': {}}
with torch.no_grad():
    for name, (e, a) in {'eeg+attended': (E, AT), 'eeg+ignored': (E, IG), 'eeg+noise_audio': (E, NZ), 'noise_eeg+attended': (EN, AT)}.items():
        fe, fa = model(e, a, mode='clip_train')
        sc = model.clip_loss.get_scores(fe, fa)
        res['objective'][name] = {'clip_loss': float(model.clip_loss(fe, fa)),
                                  'in_batch_top1': float((sc.argmax(1) == torch.arange(len(e))).float().mean()),
                                  'diag_minus_offdiag_mean_logit': float(sc.diagonal().mean() - (sc.sum() - sc.diagonal().sum()) / (len(e) * (len(e) - 1)))}
    # same quantity without CALRA conditioning: raw projected embeddings (eeg_proj vs audio_proj), for contrast
    ee = model.eeg_proj(model.eeg_encoder(E)); aa = model.audio_proj(model.audio_encoder(AT).last_hidden_state.mean(1))
    sc = model.clip_loss.get_scores(ee, aa)
    res['objective']['eeg+attended_without_CALRA(projections_only)'] = {'clip_loss': float(model.clip_loss(ee, aa)),
                                                                       'in_batch_top1': float((sc.argmax(1) == torch.arange(len(E))).float().mean())}
print(json.dumps(res['objective'], indent=1), flush=True)

from torch.utils.flop_counter import FlopCounterMode
model.train()
fc = FlopCounterMode(display=False)
with fc:
    fe, fa = model(E[:2], AT[:2], mode='clip_train'); loss = model.clip_loss(fe, fa); loss.backward()
res['flops_train_step_per_sample'] = fc.get_total_flops() / 2
model.eval()
fc = FlopCounterMode(display=False)
with fc, torch.no_grad():
    model.forward_contrastive(E[:2], AT[:2], IG[:2])
res['flops_one_forward_contrastive_per_sample'] = fc.get_total_flops() / 2
res['flops_blind_margin_per_sample'] = 2 * res['flops_one_forward_contrastive_per_sample']
print({k: v for k, v in res.items() if k.startswith('flops')})
json.dump(res, open(out, 'w'), indent=1, default=str)
