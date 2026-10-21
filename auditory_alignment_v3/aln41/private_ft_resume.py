"""ALN4.1 private CE full fine-tuning, resumable v1 (engineering fix for runfill preemption, 2026-10-21).

The training, selection and evaluation path is aln41.private_ft.run_unit unchanged: same model build, parameter groups,
AdamW / cosine schedule, data RNG, batch draws, clipping, ES-NLL selection, checkpoints and test record (private_ft.py itself
stays byte-identical). The only addition is a state file STORE/units/<id>/resume.pt, written atomically after epoch 0 and
after every epoch: model, optimizer, scheduler, numpy data-RNG bit-generator state, torch CPU and CUDA RNG states, curve,
selection state and the sha256 of best.pt. A restarted job loads it and continues with the next epoch, so an interrupted
fit follows the same update sequence as an uninterrupted one (up to GPU non-associativity). The state is used only if its
row, plan and module hashes match and best.pt still has the recorded hash; otherwise the fit starts from epoch 0. resume.pt
is removed once the unit record is written. The record gains one field, 'resume' (segments: job, first epoch, seconds).
`overrides` (epochs, updates per epoch, stop after epoch) exist only for the validation smoke in r2_private_resume.py.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
import time

import numpy as np

from . import private_ft as PF, source as SRC

MODULE_SHA = None


def module_sha():
    global MODULE_SHA
    if MODULE_SHA is None:
        MODULE_SHA = PF.sha(Path(__file__))
    return MODULE_SHA


class Interrupted(Exception):
    """Raised by the validation smoke's simulated preemption (stop_after)."""


def save_state(path, state):
    import torch
    tmp = path.with_suffix('.tmp'); torch.save(state, tmp); os.replace(tmp, path)


def run_unit(row, plan, probe=False, dest=None, record_dir=None, overrides=None):
    import torch
    from auditory_alignment import data
    ov = overrides or {}
    started = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']
    kids = data.load_private(); f = row['outer_fold']
    train = [i for i, k in enumerate(kids) if k['fold'] != f]; test = [i for i, k in enumerate(kids) if k['fold'] == f]
    assert len(kids) == 64 and len(test) in (12, 13)
    X = [torch.as_tensor(k['x'], dtype=torch.float32, device=dev) for k in kids]
    Y = [np.asarray(k['y'], np.int64) for k in kids]
    fit = {i: np.flatnonzero(~kids[i]['es_mask']) for i in train}; es = {i: np.flatnonzero(kids[i]['es_mask']) for i in train}
    assert all(len(fit[i]) for i in train) and sum(len(v) for v in es.values())
    net, a0, init = PF.source_init(row['arm'])
    model = PF.build(net, a0, SRC.SEED + 1000 * f, dev)
    opt = torch.optim.AdamW(PF.param_groups(model), lr=PF.LR)
    n_fit = sum(len(v) for v in fit.values()); per_epoch = math.ceil(n_fit / PF.BATCH)
    epochs = 1 if probe else PF.EPOCHS
    if probe:
        per_epoch = 3
    epochs = ov.get('epochs', epochs); per_epoch = ov.get('per_epoch', per_epoch)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs * per_epoch)
    rng = np.random.default_rng(SRC.SEED + 1000 * f + 7)
    if dest is None:
        dest = (PF.STORE / 'probes' / job if probe else PF.STORE / 'units') / row['id']
    dest = Path(dest); dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    es_children = sorted(es)
    key = {'row': row, 'plan_sha256': PF.sha(PF.BASE / 'plan.json'), 'module_sha256': module_sha(), 'epochs': epochs, 'per_epoch': per_epoch}

    def es_nll():
        ev = PF.evaluate(model, X, kids, es_children, dev)
        return float(np.mean([PF.nll_bits(ev[i][0][es[i]], Y[i][es[i]]).mean() for i in es_children]))

    def checkpoint(ep):
        save_state(dest / 'resume.pt', {'key': key, 'epoch': ep, 'model': model.state_dict(), 'opt': opt.state_dict(),
                                         'sched': sched.state_dict(), 'rng': rng.bit_generator.state, 'torch_cpu': torch.get_rng_state(),
                                         'torch_cuda': torch.cuda.get_rng_state(), 'curve': curve, 'best': best,
                                         'best_sha256': PF.sha(dest / 'best.pt'), 'segments': segments})

    params = [p for g in opt.param_groups for p in g['params']]
    state = None
    if (dest / 'resume.pt').exists():
        state = torch.load(dest / 'resume.pt', map_location='cpu', weights_only=False)   # RNG states must stay CPU ByteTensors
        if state['key'] != key or not (dest / 'best.pt').exists() or PF.sha(dest / 'best.pt') != state['best_sha256']:
            state = None
    if state is None:
        segments = [{'job': job, 'first_epoch': 1, 'started': time.time()}]
        curve = [{'epoch': 0, 'es_nll_bits': es_nll()}]
        best = (curve[0]['es_nll_bits'], 0); torch.save(model.state_dict(), dest / 'best.pt')
        start = 1; checkpoint(0)
    else:
        model.load_state_dict(state['model']); opt.load_state_dict(state['opt']); sched.load_state_dict(state['sched'])
        rng.bit_generator.state = state['rng']; torch.set_rng_state(state['torch_cpu']); torch.cuda.set_rng_state(state['torch_cuda'])
        curve, best = state['curve'], tuple(state['best']); start = state['epoch'] + 1
        segments = state['segments'] + [{'job': job, 'first_epoch': start, 'started': time.time()}]
        print(row['id'], 'resumed at epoch', start, 'from', [s['job'] for s in state['segments']], flush=True)
    for ep in range(start, epochs + 1):
        model.train(); losses = []
        for _ in range(per_epoch):
            ch = rng.choice(train, size=PF.BATCH, replace=True)
            tr = np.array([fit[c][rng.integers(len(fit[c]))] for c in ch])
            xb = torch.stack([X[c][t] for c, t in zip(ch, tr)]); yb = torch.as_tensor([Y[c][t] for c, t in zip(ch, tr)], device=dev)
            lp, _ = model.log_probs(xb)
            loss = -lp[torch.arange(len(yb), device=dev), yb].mean()
            opt.zero_grad(set_to_none=True); loss.backward()
            gn = torch.nn.utils.clip_grad_norm_(params, 5.0)
            if not torch.isfinite(loss) or not torch.isfinite(gn):
                raise FloatingPointError('nonfinite private CE loss/gradient')
            opt.step(); sched.step(); losses.append(float(loss))
        cur = es_nll(); curve.append({'epoch': ep, 'es_nll_bits': cur, 'train_ce_nats': float(np.mean(losses)), 'a': model.a.detach().cpu().tolist()})
        if cur < best[0]:
            best = (cur, ep); torch.save(model.state_dict(), dest / 'best.pt')
        checkpoint(ep)
        if ep % 10 == 0:
            print(row['id'], row['arm'], 'fold', f, 'epoch', ep, round(cur, 5), round(time.time() - started, 1), flush=True)
        if ov.get('stop_after') == ep:
            raise Interrupted(ep)
    torch.save(model.state_dict(), dest / 'last.pt')
    results = {}
    for label, path in (('selected', dest / 'best.pt'), ('last', dest / 'last.pt')):
        model.load_state_dict(torch.load(path, map_location=dev))
        ev = PF.evaluate(model, X, kids, test, dev); per = {}
        for i in test:
            lp, lk, lu = ev[i]; y = Y[i]
            per[kids[i]['id']] = {'group': kids[i]['group'], 'mixture': PF.metrics(lp, y), 'uniform_q': PF.metrics(lu, y),
                                  'slots': [PF.metrics(lk[:, k], y) for k in range(3)]}
            if label == 'selected':
                np.savez_compressed(dest / f'test_{kids[i]["id"]}.npz', log_mixture=lp, log_slots=lk, log_uniform=lu, y=y)
        results[label] = per
    segments[-1]['seconds'] = time.time() - segments[-1]['started']
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': PF.sha(PF.BASE / 'plan.json'), 'init': init,
           'initial_a': a0.tolist(), 'final_a': model.a.detach().cpu().tolist(), 'curve': curve, 'selected_epoch': best[1],
           'selected_es_nll_bits': best[0], 'checkpoints': {'selected': str(dest / 'best.pt'), 'selected_sha256': PF.sha(dest / 'best.pt'),
                                                            'last': str(dest / 'last.pt'), 'last_sha256': PF.sha(dest / 'last.pt')},
           'label_access': {'fit_trials': n_fit, 'es_trials': int(sum(len(v) for v in es.values())), 'train_children': len(train),
                            'test_children': len(test), 'test_labels_used_for_training_or_selection': False},
           'updates_per_epoch': per_epoch, 'epochs': epochs, 'test': results, 'device': torch.cuda.get_device_name(0), 'job': job,
           'seconds': time.time() - started, 'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20,
           'resume': {'module_sha256': module_sha(), 'segments': segments}}
    if record_dir is None:
        record_dir = (PF.BASE / 'probes' / job if probe else PF.BASE) / 'units'
    PF.write(Path(record_dir) / f'{row["id"]}.json', rec)
    (dest / 'resume.pt').unlink(missing_ok=True)
    print(row['id'], 'complete', row['arm'], f, 'selected epoch', best[1], round(rec['seconds'], 1), 'segments', len(segments), flush=True)
    return rec
