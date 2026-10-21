"""Label-free readiness diagnostic: does the blind order-symmetrised margin of the RELEASED checkpoint depend on the EEG?
Same 16 training-side windows as diag_shortcut_flops.py; margins m(eeg, att, ign) with real EEG, with noise EEG, and with
EEG from a different window (rolled by 1).  No accuracy is computed (no attended/ignored label is used beyond slot order)."""
import glob, json, os, sys
import numpy as np, pandas as pd, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm_common as C
import dtu_mm_input as M
from auditory_alignment import data as D
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
E = torch.tensor(np.stack([w['eeg'] for w in W])); A = torch.tensor(np.stack([w['att'] for w in W])); B = torch.tensor(np.stack([w['ign'] for w in W]))
EN = torch.randn(E.shape, generator=torch.Generator().manual_seed(3401))
model, args, _ = C.build(fix_pos_conv=True, quiet=True); model.eval()
n = torch.nn.functional.normalize
def pl(e, c1, c2):
    fe, f1, f2 = model.forward_contrastive(e, c1, c2); s = model.clip_loss.logit_scale.exp()
    return (n(fe, dim=-1) * n(f1, dim=-1)).sum(-1) * s, (n(fe, dim=-1) * n(f2, dim=-1)).sum(-1) * s
def m(e, c1, c2):
    s11, s21 = pl(e, c1, c2); s22, s12 = pl(e, c2, c1); return 0.5 * ((s11 - s21) - (s22 - s12))
with torch.no_grad():
    mr, mn, mx = m(E, A, B), m(EN, A, B), m(torch.roll(E, 1, 0), A, B)
c = lambda a, b: float(np.corrcoef(a.numpy(), b.numpy())[0, 1])
res = {'n': len(W), 'mean_abs_margin_real': float(mr.abs().mean()), 'mean_abs_diff_real_vs_noiseEEG': float((mr - mn).abs().mean()),
       'corr_real_vs_noiseEEG': c(mr, mn), 'mean_abs_diff_real_vs_otherwindowEEG': float((mr - mx).abs().mean()), 'corr_real_vs_otherwindowEEG': c(mr, mx),
       'sign_agreement_real_vs_noiseEEG': float(((mr > 0) == (mn > 0)).float().mean())}
print(json.dumps(res, indent=1)); json.dump(res, open(sys.argv[1], 'w'), indent=1)
