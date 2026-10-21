"""CPU dry run of auditory_alignment_v3.aln42.external_mindmix (no plan needed, training-side segments only):
cohort index + frozen B0 equality + people rules for (cf0, sf0); input cache for one training person; windows; official
model build on CPU; two official train steps on 8 fit windows; blind margins for 2 fit/es segments; swap check."""
import json, sys, time
import numpy as np
import torch
from auditory_alignment_v3.aln42 import external_mindmix as X

out = sys.argv[1]
t0 = time.time(); res = {}
ix = X.cohort_index(0)
import h5py, os
from auditory_alignment import data as D
ix['trial_n'] = {}
for sub in sorted({g['sub'] for g in ix['geo']}):
    with h5py.File(os.path.join(D.DTU_PRE, f'{sub}.h5'), 'r') as f:
        for k in {g['trial'] for g in ix['geo'] if g['sub'] == sub}:
            ix['trial_n'][(sub, k)] = int(f[k]['eeg_1_20'].shape[1])
train, test = X.unit_people(ix, 0)
res['n_cs'] = len(ix['geo']); res['n_train_people'] = len(train); res['n_test_people'] = len(test)
res['frozen_equal'] = X.check_frozen(ix, 0, {'frozen_b0_dtu': X.frozen_b0()}, 0, train, test)
A = ix['arrays']; person, role = A['cs_person'], A['cs_role']
p0 = next(p for p in train if p in set(person))
fit = [i for i in range(len(person)) if person[i] == p0 and role[i] == 'fit'][:3]
es = [i for i in range(len(person)) if person[i] == p0 and role[i] == 'es'][:1]
res['probe_person'] = p0; res['segments'] = fit + es
res['segment_geo'] = [ix['geo'][i] | {'th': ix['geo'][i]['th'][:10], 'mh': ix['geo'][i]['mh'][:10]} for i in fit + es]
t1 = time.time(); inp = X.Inputs(ix, fit + es); res['cache_seconds'] = round(time.time() - t1, 1)
W = [inp.window(i, o) for i in fit for o in X.SUB_OFFS_S]
res['window_shapes'] = [list(w.shape) for w in W[0]]
res['window_stats'] = {'eeg_mean_abs_max': float(max(np.abs(w[0].mean(1)).max() for w in W)), 'audio_peak': float(max(np.abs(w[1]).max() for w in W))}
dev = torch.device('cpu')
model, args, UT = X.build_model(dev)
trainer = UT.create_trainer(args.strategy, model, dev, args); trainer.setup_optimizer()
E = torch.from_numpy(np.stack([w[0] for w in W[:8]])); At = torch.from_numpy(np.stack([w[1] for w in W[:8]])); Ig = torch.from_numpy(np.stack([w[2] for w in W[:8]]))


class L:
    def __iter__(self):
        yield (E[:4], At[:4], Ig[:4], torch.ones(4)); yield (E[4:], At[4:], Ig[4:], torch.ones(4))

    def __len__(self):
        return 2


t1 = time.time(); tl, _, tclip = trainer.train_epoch(L(), 0); trainer.update_learning_rate(0)
res['train_two_batches'] = {'clip_loss': float(tclip), 'seconds': round(time.time() - t1, 1), 'lr_after': trainer.optimizer.param_groups[0]['lr']}
model.eval()
with torch.no_grad():
    sw = [(i, o) for i in fit[:1] + es for o in X.SUB_OFFS_S]
    xs = [inp.window(*w) for w in sw]
    e = torch.from_numpy(np.stack([x[0] for x in xs])); a = torch.from_numpy(np.stack([x[1] for x in xs])); g = torch.from_numpy(np.stack([x[2] for x in xs]))
    m = X.blind_margin(model, e, a, g); ms = X.blind_margin(model, e, g, a)
res['swap_max_abs'] = float((m + ms).abs().max()); res['margins_finite'] = bool(torch.isfinite(m).all())
res['seconds'] = round(time.time() - t0, 1)
json.dump(res, open(out, 'w'), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
