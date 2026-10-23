"""Paper line, Table 2 row 'VLAAI' (GPU): released subject-independent VLAAI decoder, target fine-tuned per common unit.

Model: paper/vlaai_torch.py (PyTorch port of github.com/exporl/vlaai @ 9af13054, released vlaai.h5 converted and verified
against the original TensorFlow model layer by layer: vlaai_conversion/VERIFY.json).  Released reconstruction interface:
EEG [T, 64] at 64 Hz -> envelope [T]; native 5 s windows and negative-Pearson loss.
Input: the common cohort EEG of each 5 s cs segment (ext_common cache, 64 Hz, the segment itself, no samples beyond it).
  DTU: native 64 BioSemi channels (order asserted), common-average re-referenced (the released preprocessing re-references to
       the common average), then standardised per listener and channel over that listener's cached segments (label-free).
  FAU (31 channels): a time-shared linear adapter Linear(31 -> 64) in front of the released model, initialised with the
       spherical-spline interpolation matrix (Perrin 1989; MNE 1.11 _make_interpolation_matrix, standard_1005 positions,
       least-squares sphere centre removed) from the 31 FAU positions onto the 64 BioSemi positions, then fitted jointly
       with the target fine-tuning on the permitted training listeners only.  Not an identity map, not a native checkpoint.
Target fine-tuning (every unit, seed 3401): all released weights (+ adapter) trained on the unit's train people's cs role=fit
segments with the attended common envelope (ext_common: kcs Local row 5, 64 Hz); Adam lr 1e-4, batch 64, loss = -mean
Pearson r over 5 s windows; at most 50 epochs; training-side validation = mean per-segment r on the train people's cs
role=es segments after every epoch, patience 5, best epoch restored.  No test listener or test content is used.
Scoring: eval mode; segment margin = r(hat, attended) - r(hat, ignored) for the train people's fit + es segments and the test
people's test segments; integration = ext_common.integrate_unit (aln42.external_eval.integrate).
Native context: 5 s of EEG per segment margin (the released model's training window); 20 s per primary decision.
"""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from . import ext_common as XC
from . import ext_fleet as XF
from . import vlaai_torch as VT

SYSTEM = 'vlaai'
NAME, LANE, SBATCH = 'c3_s35pxvla', 's35_paper_ext_vlaai', 'slurm/aln35_paper_ext_vlaai.sbatch'
OUT = XC.OUT / 'vlaai'
STORE = XC.STORE / 'vlaai'
VERIFY = XC.OUT / 'vlaai_conversion' / 'VERIFY.json'
SEED, LR, BATCH, MAX_EPOCHS, PATIENCE, EVAL_BATCH = 3401, 1e-4, 64, 50, 5, 256
SMOKE = {'train': 256, 'val': 64, 'score': 64, 'epochs': 2}
# Numerics: full fp32 for fine-tuning and scoring (cuDNN TF32 off -- PyTorch enables it for convolutions by default -- matmul TF32
# off, deterministic cuDNN, no autotuning), so a segment's margin does not depend on which other segments share its batch.
# Batch-invariance check on the quantity that is integrated: |margin(batch) - margin(alone)| over the first 8 scored segments
# must stay below MARGIN_TOL (Pearson-r units; margins are differences of two r in [-2, 2], typical |margin| ~ 1e-2..1e-1, so the
# tolerance is <= 1 % of a typical margin and ~100x above fp32 round-off); its ratio to the median |margin| is recorded.
MARGIN_TOL, N_INVARIANCE = 1e-4, 8
BIOSEMI64 = ['Fp1', 'AF7', 'AF3', 'F1', 'F3', 'F5', 'F7', 'FT7', 'FC5', 'FC3', 'FC1', 'C1', 'C3', 'C5', 'T7', 'TP7', 'CP5', 'CP3', 'CP1',
             'P1', 'P3', 'P5', 'P7', 'P9', 'PO7', 'PO3', 'O1', 'Iz', 'Oz', 'POz', 'Pz', 'CPz', 'Fpz', 'Fp2', 'AF8', 'AF4', 'AFz', 'Fz', 'F2',
             'F4', 'F6', 'F8', 'FT8', 'FC6', 'FC4', 'FC2', 'FCz', 'Cz', 'C2', 'C4', 'C6', 'T8', 'TP8', 'CP6', 'CP4', 'CP2', 'P2', 'P4', 'P6',
             'P8', 'P10', 'PO8', 'PO4', 'O2']
read, write, sha, digest = XC.read, XC.write, XC.sha, XC.digest


def sources():
    here = Path(__file__).parent
    return {**XC.sources(), **{f'auditory_alignment_v3/paper/{f}': sha(here / f) for f in ('ext_vlaai.py', 'ext_fleet.py', 'vlaai_torch.py')}}


def rows():
    out = []
    for ds in XC.DATASETS:
        for cf in XC.CFS:
            for sf in XC.SFS:
                body = {'system': SYSTEM, 'dataset': ds, 'content_fold': cf, 'person_fold': sf, 'seed': SEED}
                out.append({**body, 'id': 'PXVLA_' + digest(body, 16)})
    return out


def make_plan():
    ver = read(VERIFY); assert ver['pass'] and ver['port_source_sha256'] == sha(Path(VT.__file__)) and ver['h5_sha256'] == sha(VT.H5)
    body = {'version': 'PAPER_EXT_VLAAI_v1', 'rows': rows(), 'sources': sources(),
            'input_index_sha256': {ds: sha(XC.INPUT / ds / 'index.json') for ds in XC.DATASETS},
            'released': {'repo': 'github.com/exporl/vlaai', 'commit': VT.COMMIT, 'h5_sha256': sha(VT.H5), 'verify_sha256': sha(VERIFY),
                         'n_params': 1740289},
            'recipe': {'numerics': 'fp32 (TF32 off, deterministic cuDNN)', 'batch_invariance_margin_tol': MARGIN_TOL, 'seed': SEED, 'optimizer': 'Adam', 'lr': LR, 'batch': BATCH, 'max_epochs': MAX_EPOCHS, 'patience': PATIENCE,
                       'loss': '-mean Pearson r over the 5 s window (released pearson_loss)', 'train': 'train people cs role=fit, attended envelope',
                       'validation': 'train people cs role=es, mean per-segment r (attended), best epoch restored',
                       'dtu_input': 'native 64 BioSemi channels, common average reference, per-listener per-channel z-score',
                       'fau_input': 'Linear(31->64) time-shared adapter, spherical-spline init, trained jointly',
                       'margin': 'r(hat, attended) - r(hat, ignored), 5 s segment', 'integration': 'aln42.external_eval.integrate'},
            'context': {'eeg_per_segment_s': 5.0, 'eeg_per_20s_decision_s': 20.0, 'native_window_s': 5.0},
            'smoke': SMOKE}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
        return old
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700); STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
    write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    return read(plan)


def verify(plan):
    assert plan['sources'] == sources(), 'vlaai source drift'
    for ds in XC.DATASETS:
        assert sha(XC.INPUT / ds / 'index.json') == plan['input_index_sha256'][ds]
    assert sha(VERIFY) == plan['released']['verify_sha256'] and sha(VT.H5) == plan['released']['h5_sha256']


# ------------------------------------------------------------------------------------------------ data
def load_all(cache, car):
    """Segment EEG [n, C, 320] (cache order), attended / ignored envelopes [n, 320]; DTU: CAR + per-listener z-score."""
    a = cache.arr; n = len(a['cs_person']); C = len(cache.index['channels'])
    X = np.zeros((n, C, XC.SEG64), np.float32); att = np.zeros((n, XC.SEG64), np.float32); ign = np.zeros_like(att)
    for pid in sorted(set(a['cs_person'].tolist())):
        rows_ = cache.person_rows(pid); E, at, ig = cache.load(pid, check=True); E = E[a['cs_row'][rows_], :, :XC.SEG64]
        if car:
            E = E - E.mean(1, keepdims=True)
            mu = E.mean((0, 2), keepdims=True); sd = E.std((0, 2), keepdims=True); sd[sd == 0] = 1
            E = (E - mu) / sd
        X[rows_] = E; att[rows_] = at[a['cs_row'][rows_]]; ign[rows_] = ig[a['cs_row'][rows_]]
    return X, att, ign


def sphere_unit(pos):
    A = np.c_[2 * pos, np.ones(len(pos))]; b = (pos ** 2).sum(1)
    c = np.linalg.lstsq(A, b, rcond=None)[0][:3]
    v = pos - c
    return v / np.linalg.norm(v, axis=1, keepdims=True), c


def adapter_init(src_names, dst_names=BIOSEMI64):
    """[len(dst), len(src)] spherical-spline interpolation matrix (MNE), standard_1005 positions, common LS sphere centre."""
    import mne
    from mne.channels.interpolation import _make_interpolation_matrix
    pos = mne.channels.make_standard_montage('standard_1005').get_positions()['ch_pos']
    allp = np.array([pos[c] for c in list(src_names) + list(dst_names)])
    unit, centre = sphere_unit(allp)
    M = _make_interpolation_matrix(unit[:len(src_names)], unit[len(src_names):])
    assert M.shape == (len(dst_names), len(src_names))
    return M.astype(np.float32), {'mne': mne.__version__, 'sphere_centre_m': centre.tolist(), 'row_sum_mean': float(M.sum(1).mean())}


def build_net(ds, channels, dev):
    import torch
    from torch import nn
    vl = VT.pretrained()

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.vlaai = vl; self.adapter = None
            if ds == 'fau':
                self.adapter = nn.Linear(len(channels), 64)
                M, info = adapter_init(channels)
                with torch.no_grad():
                    self.adapter.weight.copy_(torch.from_numpy(M)); self.adapter.bias.zero_()
                self.adapter_info = info

        def forward(self, x):                      # x [B, C, T] -> [B, T]
            x = x.transpose(1, 2)
            if self.adapter is not None:
                x = self.adapter(x)
            return self.vlaai(x)[..., 0]
    if ds == 'dtu':
        assert [c.casefold() for c in channels] == [c.casefold() for c in BIOSEMI64], 'DTU channel order'
    return Net().to(dev)


def pearson(a, b):
    a = a - a.mean(-1, keepdim=True); b = b - b.mean(-1, keepdim=True)
    return (a * b).sum(-1) / ((a * a).sum(-1) * (b * b).sum(-1)).clamp_min(1e-24).sqrt()


def predict(net, X, ids, dev):
    import torch
    out = np.zeros((len(ids), X.shape[-1]), np.float64)
    net.eval()
    with torch.no_grad():
        for s in range(0, len(ids), EVAL_BATCH):
            out[s:s + EVAL_BATCH] = net(torch.from_numpy(X[ids[s:s + EVAL_BATCH]]).to(dev)).double().cpu().numpy()
    return out


def fit(net, X, Y, fit_ids, val_ids, epochs, dev, tag=''):
    """Adam on -mean Pearson r; validation mean per-segment r after every epoch; patience; best state restored."""
    import copy
    import torch
    params = [p for p in net.parameters() if p.requires_grad]
    opt = torch.optim.Adam(params, lr=LR)
    best, best_ep, best_state, hist = -np.inf, -1, None, []
    for ep in range(epochs):
        t0 = time.time(); net.train(); perm = np.random.default_rng([SEED, ep]).permutation(len(fit_ids)); losses = []
        for s in range(0, len(perm), BATCH):
            b = fit_ids[perm[s:s + BATCH]]
            x = torch.from_numpy(X[b]).to(dev); y = torch.from_numpy(Y[b]).to(dev)
            loss = -pearson(net(x), y).mean()
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step(); losses.append(float(loss))
        val = float(XC.rowcorr(predict(net, X, val_ids, dev), Y[val_ids].astype(np.float64)).mean())
        hist.append({'epoch': ep + 1, 'train_loss': float(np.mean(losses)), 'val_mean_r': val, 'seconds': round(time.time() - t0, 2)})
        print(tag, hist[-1], flush=True)
        if val > best:
            best, best_ep, best_state = val, ep + 1, copy.deepcopy(net.state_dict())
        elif ep + 1 - best_ep >= PATIENCE:
            break
    net.load_state_dict(best_state)
    return {'history': hist, 'best_epoch': best_ep, 'best_val_mean_r': best, 'epochs_run': len(hist)}


def fp32_numerics():
    import torch
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False
    return {'cuda_matmul_allow_tf32': torch.backends.cuda.matmul.allow_tf32, 'cudnn_allow_tf32': torch.backends.cudnn.allow_tf32,
            'cudnn_deterministic': torch.backends.cudnn.deterministic, 'cudnn_benchmark': torch.backends.cudnn.benchmark}


def margin_invariance(margin_fn, ids, ref_margin, all_margins):
    """margin_fn(idx) -> margins of segments idx scored as one batch; compares each of the first N_INVARIANCE segments scored alone."""
    k = ids[:N_INVARIANCE]
    alone = np.concatenate([margin_fn(k[j:j + 1]) for j in range(len(k))])
    d = float(np.abs(alone - ref_margin[:len(k)]).max()); med = float(np.median(np.abs(all_margins)))
    return {'batch_invariance_margin_max_abs': d, 'batch_invariance_tolerance': MARGIN_TOL, 'median_abs_margin': med,
            'batch_invariance_relative_to_median_margin': d / med if med > 0 else None, 'batch_invariance_ok': d < MARGIN_TOL}


def run_unit(row, plan, probe=False):
    import torch
    t_all = time.time(); job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda'); torch.cuda.reset_peak_memory_stats()
    numerics = fp32_numerics()
    ds, cf, sf = row['dataset'], row['content_fold'], row['person_fold']
    cache = XC.Cache(ds); channels = cache.index['channels']
    t0 = time.time(); X, att, ign = load_all(cache, car=(ds == 'dtu')); t_load = time.time() - t0
    role = cache.role(cf); tr_ids, te_ids = cache.scored(cf, sf)
    fit_ids, val_ids = tr_ids[role[tr_ids] == 'fit'], tr_ids[role[tr_ids] == 'es']
    full = {'fit': int(len(fit_ids)), 'val': int(len(val_ids)), 'score': int(len(tr_ids) + len(te_ids))}
    score_tr, score_te = tr_ids, te_ids
    if probe:
        rng = np.random.default_rng(SEED)
        fit_ids = np.sort(rng.choice(fit_ids, SMOKE['train'], replace=False)); val_ids = val_ids[:SMOKE['val']]
        score_tr, score_te = tr_ids[:SMOKE['score']], te_ids[:0]
    torch.manual_seed(SEED); np.random.seed(SEED)
    net = build_net(ds, channels, dev)
    init_val = float(XC.rowcorr(predict(net, X, val_ids, dev), att[val_ids].astype(np.float64)).mean())
    t0 = time.time(); tr = fit(net, X, att, fit_ids, val_ids, SMOKE['epochs'] if probe else MAX_EPOCHS, dev, row['id']); t_train = time.time() - t0
    t0 = time.time(); ids = np.concatenate([score_tr, score_te]).astype(int)
    P = predict(net, X, ids, dev); ra = XC.rowcorr(P, att[ids].astype(np.float64)); ri = XC.rowcorr(P, ign[ids].astype(np.float64))
    t_score = time.time() - t0
    n = len(cache.arr['cs_person'])
    margin = np.full(n, np.nan); r_att = np.full(n, np.nan); r_ign = np.full(n, np.nan); scored = np.full(n, '', dtype='<U10')
    margin[ids], r_att[ids], r_ign[ids] = ra - ri, ra, ri
    scored[score_tr] = 'train_side'; scored[score_te] = 'test'
    checks = {'margins_finite': bool(np.isfinite(margin[ids]).all())}
    def margin_fn(idx):
        Q = predict(net, X, idx, dev)
        return XC.rowcorr(Q, att[idx].astype(np.float64)) - XC.rowcorr(Q, ign[idx].astype(np.float64))
    checks.update(margin_invariance(margin_fn, ids, ra - ri, ra - ri))
    k = ids[:N_INVARIANCE]
    checks['prediction_alone_vs_batch_max_abs'] = float(np.abs(np.concatenate([predict(net, X, k[j:j + 1], dev) for j in range(len(k))]) - P[:len(k)]).max())
    checks['prediction_sd'] = float(P.std())
    checks['swap_antisymmetric'] = bool(np.allclose(XC.rowcorr(P, ign[ids]) - XC.rowcorr(P, att[ids]), -(ra - ri)))
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(dest / 'margins.npz', cs_person=cache.arr['cs_person'], cs_code=cache.arr['cs_code'], cs_e0=cache.arr['cs_e0'],
                        cs_role=role, margin=margin, r_att=r_att, r_ign=r_ign, scored=scored)
    if not probe:
        torch.save(net.state_dict(), dest / 'final_model.pt')
    rec = {'status': 'complete' if all(v for kk, v in checks.items() if kk.endswith(('_ok', 'finite', 'antisymmetric'))) else 'check_failed',
           'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'dest': str(dest), 'npz_sha256': sha(dest / 'margins.npz'),
           'final_model_sha256': None if probe else sha(dest / 'final_model.pt'), 'init_val_mean_r': init_val, **tr,
           'adapter': getattr(net, 'adapter_info', None), 'n': {'fit': int(len(fit_ids)), 'val': int(len(val_ids)), 'scored_train_side': int(len(score_tr)),
                                                                 'scored_test': int(len(score_te))}, 'full_counts': full,
           'seconds': {'load': round(t_load, 1), 'train': round(t_train, 1), 'score': round(t_score, 1), 'total': round(time.time() - t_all, 1)},
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': job, 'checks': checks,
           'numerics': numerics}
    if probe:
        per = t_train / max(1, tr['epochs_run']) / max(1, len(fit_ids))
        rec['projected_full_unit_hours_upper'] = (t_load + per * full['fit'] * MAX_EPOCHS + t_score / max(1, len(ids)) * full['score']) / 3600
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], ds, cf, sf, rec['status'], rec['seconds'], flush=True)
    assert rec['status'] == 'complete', checks
    return rec


def smoke():
    job = os.environ['SLURM_JOB_ID']; plan = make_plan(); verify(plan)
    receipt = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
    try:
        for ds in XC.DATASETS:
            row = next(r for r in plan['rows'] if r['dataset'] == ds and r['content_fold'] == 0 and r['person_fold'] == 0)
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', XF.DISPATCH, 'unit', '--id', row['id'], '--probe', '--system', SYSTEM]).returncode
            assert rc == 0, (ds, rc)
            rec = read(OUT / 'probes' / job / 'units' / f'{row["id"]}.json')
            assert rec['status'] == 'complete' and rec['n']['scored_test'] == 0
            receipt['units'].append({k: rec[k] for k in ('row', 'seconds', 'gpu_peak_mb', 'device', 'checks', 'numerics', 'init_val_mean_r', 'history', 'adapter',
                                                         'n', 'full_counts', 'projected_full_unit_hours_upper')})
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', receipt)


def unit_cli(uid, probe):
    plan = read(OUT / 'plan.json'); verify(plan)
    run_unit(next(r for r in plan['rows'] if r['id'] == uid), plan, probe)


def fleet_status():
    return XF.fleet_status(sys.modules[__name__], slots=1, max_units=10)
