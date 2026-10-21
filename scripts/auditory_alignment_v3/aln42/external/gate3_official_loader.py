"""Gate 3 (pre-registered wording): the official DTU loader runs on our DTU export.

Exports 8 training-side windows (one NH training person of person fold 0, one fit-role two-talker trial of content
fold 0) in the official KUL/DTU pickle format (<subject>.pkl DataFrame: eeg, target_audio, negative_audio,
attended_label) into a private 0700 temp dir, then runs the unmodified official path:
DatasetLoader.load_dataset('DTU', dir) -> UniversalDataset(df, 'DTU', 'multimodal_real') -> DataLoader(batch 4,
same stacking collate as cross_validate_subject) -> MultimodalRealTrainer.setup_optimizer + train_epoch (1 epoch)
+ update_learning_rate.  The export is deleted afterwards (its SHA256 is recorded).
"""
import glob, hashlib, json, os, shutil, sys, time
import numpy as np
import pandas as pd
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm_common as C
import dtu_mm_input as M
from auditory_alignment import data as D

out_json = sys.argv[1]
tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'loader_probe_tmp')
os.makedirs(tmp, mode=0o700, exist_ok=True)
part = pd.read_csv(f'{M.S}/participants.tsv', sep='\t'); hs = dict(zip(part.participant_id, part.hearing_status))
subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(D.REPO, 'private', 'auditory_c3', 'public', 'dtu_v2', '*.json')))
folds = D._folds({g: [s for s in subs if hs[s] == g] for g in ('nh', 'hi')})
inv = {(r['file'], r['trial'], r['kind']): r for r in json.load(open(f'{M.ROOT}/derived/c3_features_v1/dtu/inventory.json'))}
cg = json.load(open(os.path.join(D.DTU_KCS, 'content_groups.json')))['content']
sub = next(s for s in subs if folds[s] != 0 and hs[s] == 'nh')
tr = next(t for t in M.trials_of(sub) if t['two'] and cg[inv[(sub, t['trial'], 'target')]['sha']]['half'] != 0
          and not cg[inv[(sub, t['trial'], 'target')]['sha']]['early_stop'])
W = M.windows_for(sub, tr, hi=False, max_segments=4)
df = pd.DataFrame([{'eeg': w['eeg'], 'target_audio': w['att'], 'negative_audio': w['ign'],
                    'attended_label': 0 if w['attend_lr'] == 'attendleft' else 1} for w in W])
pkl = os.path.join(tmp, f'{sub}.pkl'); df.to_pickle(pkl)
res = {'sub': sub, 'group': hs[sub], 'person_fold': folds[sub], 'trial': tr['trial'], 'n_windows': len(W),
       'export_sha256': C.sha256_file(pkl), 'export_columns': list(df.columns)}

UEF, UM, UT = C.official_modules()
data = UEF.DatasetLoader.load_dataset('DTU', tmp)
res['official_loader_subjects'] = {k: list(v.shape) for k, v in data.items()}
ds = UEF.UniversalDataset(data[sub], 'DTU', 'multimodal_real')
item = ds[0]
res['official_item_shapes'] = [list(t.shape) for t in item]


def collate_fn(batch):   # cross_validate_subject.collate_fn (KUL/DTU branch) on CPU
    e, t, n, l = zip(*batch)
    return torch.stack(e), torch.stack(t), torch.stack(n), torch.stack(l)


dl = torch.utils.data.DataLoader(ds, batch_size=4, shuffle=True, num_workers=0, collate_fn=collate_fn,
                                 generator=torch.Generator().manual_seed(3401))
model, args, _ = C.build(fix_pos_conv=True, quiet=True)
torch.manual_seed(3401)
trainer = UT.create_trainer(args.strategy, model, torch.device('cpu'), args)
trainer.setup_optimizer()
t0 = time.time()
tl, tc, tclip = trainer.train_epoch(dl, 0)
trainer.update_learning_rate(0)
res['official_train_epoch'] = {'batches': len(dl), 'mean_total_loss': tl, 'mean_clip_loss': tclip, 'seconds_cpu2': round(time.time() - t0, 1),
                               'lr_after_epoch0': trainer.optimizer.param_groups[0]['lr'], 'finite': bool(np.isfinite(tl))}
shutil.rmtree(tmp)
res['export_deleted'] = not os.path.exists(tmp)
json.dump(res, open(out_json, 'w'), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
