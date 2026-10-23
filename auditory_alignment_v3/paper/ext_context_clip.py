"""Paper line, Table 2 POST-HOC context-matched sensitivity, Transformer-CLIP row 'clip_ctx' (GPU).  Protocol: results/.../
context_matched/PROTOCOL.json (frozen 2026-10-22 18:50; analyses.clip_ctx pre-declared there) + APPENDUM_02_CLIP_CTX.json
(engineering binding, written before any clip_ctx output).

Exactly the declared row: the frozen stage-S encoder of the native CLIP row (paper/ext_clip.py source unit, EEGConformerInterleaved,
checkpoint sha bound in the plan) is unchanged; the stage-T native readout (official RegressionModel + PearsonLoss, Adam 1e-3,
batch 64, <= 250 epochs, patience 10 on train people cs role=es, best state restored; FAU Linear(31->64) adapter, spherical-spline
init, fitted jointly) is re-fitted per unit on 192-sample (3 s) windows that lie inside the proposed system's span [13, 304) at
64 Hz: training windows start at 13 and 112, reconstruction windows at 13 / 62 / 112, native Hann overlap-add (torch.hann_window(192)
as the native row; outer half-windows weight 1; normalised by the summed weights) over [13, 304).  Input: cache EEG span only
(ext_context_vlaai.load_ctx: DTU common-average reference + per-listener per-channel z-score over span samples only; FAU cache EEG
span, as the native row's FAU input); no EEG sample outside the span is read.  Margin r(hat, att) - r(hat, ign) over [13, 304).
Same 20 units (dataset x content fold x person fold) as the native row, new ids, own plan / records / claims; integration and
aggregation as every Table 2 row (ext_context.score_units / table -> TABLE2_CLIP_CTX.json).
Fleet: fleet_status() (shim aln35/paper_ext_ctx_clip_fleet.py), job name c3_s35pxcctx, lane s35_paper_ext_clip_ctx, slots 2.
CLI (Slurm only): python -m auditory_alignment_v3.paper.ext_context_clip plan | appendum | smoke | worker [--max-units N] |
unit --id ID [--probe] | score | status       ('--system clip_ctx' from the fleet submit line is accepted and ignored)
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from . import ext_clip as CL
from . import ext_common as XC
from . import ext_context as CX
from . import ext_context_vlaai as CV
from . import ext_fleet as XF
from . import ext_vlaai as XV

SYSTEM = 'clip_ctx'
NAME, LANE, SBATCH = 'c3_s35pxcctx', 's35_paper_ext_clip_ctx', 'slurm/aln35_paper_ext_ctx_clip.sbatch'
OUT = CX.OUT / 'clip'
STORE = CX.STORE / 'clip'
S0, S1 = CX.SPAN64
W = CX.CLIP_DECLARED['window']
TRAIN_STARTS = tuple(CX.CLIP_DECLARED['train_starts_64hz'])          # 13, 112 (absolute 64 Hz segment samples)
INFER_STARTS = tuple(CX.CLIP_DECLARED['infer_starts_64hz'])          # 13, 62, 112
SLOTS, MAX_UNITS = 2, 10
APPENDUM = CX.RES / 'APPENDUM_02_CLIP_CTX.json'
MODULE_FILES = ('auditory_alignment_v3/paper/ext_context_clip.py', 'auditory_alignment_v3/paper/ext_context.py',
                'auditory_alignment_v3/paper/ext_context_vlaai.py', 'auditory_alignment_v3/paper/ext_clip.py',
                'auditory_alignment_v3/paper/ext_vlaai.py', 'auditory_alignment_v3/paper/ext_fleet.py', 'auditory_alignment_v3/paper/ext_common.py',
                'auditory_alignment_v3/aln42/external_eval.py')
read, write, sha, digest = XC.read, XC.write, XC.sha, XC.digest


def sources():
    return CX.file_shas(MODULE_FILES)


def rows():
    out = []
    for ds in XC.DATASETS:
        for cf in XC.CFS:
            for sf in XC.SFS:
                body = {'system': SYSTEM, 'dataset': ds, 'content_fold': cf, 'person_fold': sf, 'seed': CL.SEED, 'span_64hz': list(CX.SPAN64),
                        'window': W, 'train_starts_64hz': list(TRAIN_STARTS), 'infer_starts_64hz': list(INFER_STARTS)}
                out.append({**body, 'id': 'PXCCTX_' + digest(body, 16)})
    return out


def native_source():
    plan = read(CL.OUT / 'plan.json'); srow = plan['rows'][0]
    rec = read(CL.OUT / 'units' / f'{srow["id"]}.json'); assert rec['status'] == 'complete' and not rec['probe']
    return {'unit': srow['id'], 'checkpoint': str(Path(rec['dest']) / 'model.ckpt'), 'checkpoint_sha256': rec['checkpoint_sha256'],
            'plan_sha256': sha(CL.OUT / 'plan.json')}


def geometry_check():
    """The declared windows lie inside the span and cover it; the OLA weights are positive on every span sample."""
    import torch
    hann = torch.hann_window(W).numpy().astype(np.float64)
    wts = np.stack([hann.copy() for _ in INFER_STARTS]); wts[0, :W // 2] = 1; wts[-1, W // 2:] = 1
    den = np.zeros(S1 - S0)
    for j, st in enumerate(INFER_STARTS):
        den[st - S0:st - S0 + W] += wts[j]
    tr_cover = np.zeros(S1 - S0, bool)
    for st in TRAIN_STARTS:
        tr_cover[st - S0:st - S0 + W] = True
    ok = all(S0 <= st and st + W <= S1 for st in TRAIN_STARTS + INFER_STARTS) and bool((den > 0).all()) and bool(tr_cover.all())
    return {'windows_inside_span': all(S0 <= st and st + W <= S1 for st in TRAIN_STARTS + INFER_STARTS),
            'ola_weights_positive_on_span': bool((den > 0).all()), 'train_windows_cover_span': bool(tr_cover.all()),
            'den_min': float(den.min()), 'den_max': float(den.max()), 'pass': bool(ok)}


def write_appendum():
    """Engineering appendum (protocol directory), written once before any clip_ctx output."""
    if APPENDUM.exists():
        return read(APPENDUM)
    assert not (OUT / 'units').exists() or not any((OUT / 'units').glob('*.json')), 'clip_ctx outputs exist; appendum must precede them'
    body = {'appendum': 'APPENDUM_02_CLIP_CTX', 'post_hoc': True, 'protocol_sha256': CX.protocol_sha(),
            'scope': 'engineering binding of the pre-declared clip_ctx row (PROTOCOL.json analyses.clip_ctx); no change of its definition',
            'module': 'auditory_alignment_v3/paper/ext_context_clip.py (new; the frozen protocol listed no clip_ctx module)',
            'implementation': {
                'encoder': 'frozen stage-S EEGConformerInterleaved of the completed native CLIP row (ext_clip source unit, checkpoint sha below), '
                           'loaded exactly as ext_clip.target_unit (memory bank keys excluded)',
                'readout': 'ext_clip.target_unit recipe unchanged (official RegressionModel, PearsonLoss, Adam 1e-3, batch 64, <= 250 epochs, '
                           'patience 10, best state; FAU adapter Linear(31->64) with ext_vlaai.adapter_init)',
                'input': 'ext_context_vlaai.load_ctx(cache, car=(ds == dtu)) = span [13, 304) only; DTU CAR + per-listener per-channel z-score '
                         'over span samples (protocol: "DTU re-reference / z-score over span samples"); FAU cache EEG span',
                'windows': {'length': W, 'train_starts_64hz': list(TRAIN_STARTS), 'infer_starts_64hz': list(INFER_STARTS),
                            'span_relative_train': [s - S0 for s in TRAIN_STARTS], 'span_relative_infer': [s - S0 for s in INFER_STARTS]},
                'ola': 'torch.hann_window(192) (periodic, as the native row), first window first half = 1, last window second half = 1, '
                       'divided by the summed weights over [13, 304)',
                'margin': 'r(hat, att) - r(hat, ign) over the 291 span samples',
                'integration': 'ext_context.score_units -> ext_common.integrate_unit (5 / 10 / 20 s), ext_context.table -> TABLE2_CLIP_CTX.json'},
            'adaptations_to_current_repo': ['the frozen PROTOCOL.json module_sha256 list predates this module; its sha and every reused '
                                            "module's sha are bound in this appendum and in the clip_ctx plan",
                                            'reuses ext_context_vlaai.load_ctx (span loader) instead of duplicating it'],
            'native_source': native_source(), 'geometry_check': geometry_check(), 'module_sha256': sources(),
            'written': datetime.now().astimezone().isoformat(), 'job': os.environ.get('SLURM_JOB_ID')}
    assert body['geometry_check']['pass'], body['geometry_check']
    os.umask(0o022); APPENDUM.write_text(json.dumps(body, indent=1) + '\n'); APPENDUM.chmod(0o444); os.umask(0o077)
    return read(APPENDUM)


def make_plan():
    app = write_appendum()
    body = {'version': 'PAPER_EXT_CLIP_CTX_v1', 'post_hoc': True, 'protocol_sha256': CX.protocol_sha(), 'appendum_sha256': sha(APPENDUM),
            'rows': rows(), 'sources': sources(), 'native_source': app['native_source'],
            'native_plan_sha256': sha(CL.OUT / 'plan.json'), 'input_index_sha256': {ds: sha(XC.INPUT / ds / 'index.json') for ds in XC.DATASETS},
            'target_recipe': CL.TGT, 'span': {'eeg_64hz_half_open': [S0, S1], 'window': W, 'train_starts_64hz': list(TRAIN_STARTS),
                                               'infer_starts_64hz': list(INFER_STARTS)},
            'smoke': CL.SMOKE, 'fleet': {'name': NAME, 'lane': LANE, 'sbatch': SBATCH, 'slots': SLOTS, 'max_units_per_job': MAX_UNITS}}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
        return old
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700); STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
    write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    return read(plan)


def verify(plan):
    assert plan['sources'] == sources(), 'clip_ctx source drift'
    assert plan['protocol_sha256'] == CX.protocol_sha() and plan['appendum_sha256'] == sha(APPENDUM)
    for ds in XC.DATASETS:
        assert sha(XC.INPUT / ds / 'index.json') == plan['input_index_sha256'][ds]
    assert sha(plan['native_source']['checkpoint']) == plan['native_source']['checkpoint_sha256']


# ------------------------------------------------------------------------------------------------ run (= ext_clip.target_unit on the span)
def run_unit(row, plan, probe=False):
    import torch
    from torch import nn
    t_all = time.time(); job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda'); torch.cuda.reset_peak_memory_stats()
    numerics = XV.fp32_numerics()
    CM, DL, TH, TF = CL.official()
    ds, cf, sf = row['dataset'], row['content_fold'], row['person_fold']
    ckpt = Path(plan['native_source']['checkpoint']); assert sha(ckpt) == plan['native_source']['checkpoint_sha256']
    model = CL.build_source_model(dev, 1)
    sd = torch.load(ckpt, map_location='cpu', weights_only=True)
    sd = {k: v for k, v in sd.items() if not k.startswith('eegMemoryBank.')}
    missing = model.load_state_dict(sd, strict=False)
    assert all(k.startswith('eegMemoryBank.') for k in missing.missing_keys) and not missing.unexpected_keys
    enc = model.eegModel.eval(); enc.requires_grad_(False)
    cache = XC.Cache(ds); channels = cache.index['channels']
    t0 = time.time(); X, att, ign = CV.load_ctx(cache, car=(ds == 'dtu')); t_load = time.time() - t0     # [n, C, 291] span only
    L = S1 - S0; assert X.shape[-1] == L
    role = cache.role(cf); tr_ids, te_ids = cache.scored(cf, sf)
    fit_ids, val_ids = tr_ids[role[tr_ids] == 'fit'], tr_ids[role[tr_ids] == 'es']
    full = {'fit': int(len(fit_ids)), 'val': int(len(val_ids)), 'score': int(len(tr_ids) + len(te_ids))}
    score_tr, score_te = tr_ids, te_ids
    if probe:
        rng = np.random.default_rng(CL.SEED)
        fit_ids = np.sort(rng.choice(fit_ids, CL.SMOKE['train'], replace=False)); val_ids = val_ids[:CL.SMOKE['val']]
        score_tr, score_te = tr_ids[:CL.SMOKE['score']], te_ids[:0]
    torch.manual_seed(CL.SEED); np.random.seed(CL.SEED)
    if ds == 'dtu':
        assert [c.casefold() for c in channels] == [c.casefold() for c in XV.BIOSEMI64]
        adapter, ainfo = None, None
    else:
        adapter = nn.Linear(len(channels), 64).to(dev); M, ainfo = XV.adapter_init(channels)
        with torch.no_grad():
            adapter.weight.copy_(torch.from_numpy(M)); adapter.bias.zero_()
    readout = TH.RegressionModel(CL.SRC['latent_dim'], output_dim=1).to(dev)
    crit = TH.PearsonLoss()
    tr_rel = [s - S0 for s in TRAIN_STARTS]; inf_rel = [s - S0 for s in INFER_STARTS]

    def windows(ids, starts):
        xs = np.stack([X[ids, :, s:s + W] for s in starts], 1).reshape(-1, X.shape[1], W)
        ys = np.stack([att[ids, s:s + W] for s in starts], 1).reshape(-1, W)
        return xs, ys

    def embed(x):
        x = x.transpose(1, 2)
        if adapter is not None:
            x = adapter(x)
        return enc(x).transpose(1, 2)

    def forward(x):
        return readout(embed(x))
    xtr, ytr = windows(fit_ids, tr_rel); xva, yva = windows(val_ids, tr_rel)
    params = list(readout.parameters()) + (list(adapter.parameters()) if adapter is not None else [])
    opt = torch.optim.Adam(params, lr=CL.TGT['lr'])
    cached = None
    if adapter is None:
        with torch.no_grad():
            cached = {k: torch.cat([embed(torch.from_numpy(v[s:s + 256]).to(dev)) for s in range(0, len(v), 256)]) for k, v in (('tr', xtr), ('va', xva))}

    def val_loss():
        readout.eval()
        with torch.no_grad():
            out = readout(cached['va']) if cached is not None else \
                torch.cat([forward(torch.from_numpy(xva[s:s + 256]).to(dev)) for s in range(0, len(xva), 256)])
            return float(crit(out, torch.from_numpy(yva[:, None, :]).to(dev)).mean())
    best, best_ep, best_state, hist = float('inf'), -1, None, []
    epochs = CL.SMOKE['target_epochs'] if probe else CL.TGT['epochs']
    t0 = time.time()
    for ep in range(epochs):
        te = time.time(); readout.train(); perm = np.random.default_rng([CL.SEED, ep]).permutation(len(xtr)); losses = []
        for s in range(0, len(perm), CL.TGT['batch']):
            b = perm[s:s + CL.TGT['batch']]
            y = torch.from_numpy(ytr[b][:, None, :]).to(dev)
            out = readout(cached['tr'][torch.from_numpy(b).to(dev)]) if cached is not None else forward(torch.from_numpy(xtr[b]).to(dev))
            loss = crit(out, y).mean()
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step(); losses.append(float(loss))
        v = val_loss(); hist.append({'epoch': ep + 1, 'train_loss': float(np.mean(losses)), 'val_loss': v, 'seconds': round(time.time() - te, 2)})
        print(row['id'], hist[-1], flush=True)
        if v < best:
            best, best_ep = v, ep + 1
            best_state = {'readout': copy.deepcopy(readout.state_dict()), 'adapter': copy.deepcopy(adapter.state_dict()) if adapter is not None else None}
        elif ep + 1 - best_ep > CL.TGT['patience']:
            break
    readout.load_state_dict(best_state['readout'])
    if adapter is not None:
        adapter.load_state_dict(best_state['adapter'])
    t_train = time.time() - t0
    hann = torch.hann_window(W).numpy().astype(np.float64)
    wts = np.stack([hann.copy() for _ in inf_rel]); wts[0, :W // 2] = 1; wts[-1, W // 2:] = 1
    den = np.zeros(L)
    for j, st in enumerate(inf_rel):
        den[st:st + W] += wts[j]

    def recon(idx):
        out = np.zeros((len(idx), L))
        with torch.no_grad():
            for s in range(0, len(idx), 128):
                b = idx[s:s + 128]; xs, _ = windows(b, inf_rel)
                o = torch.cat([forward(torch.from_numpy(xs[k:k + 384]).to(dev)) for k in range(0, len(xs), 384)])[:, 0].double().cpu().numpy()
                o = o.reshape(len(b), len(inf_rel), W); acc = np.zeros((len(b), L))
                for j, st in enumerate(inf_rel):
                    acc[:, st:st + W] += o[:, j] * wts[j]
                out[s:s + len(b)] = acc / den
        return out

    def margin_fn(idx):
        Q = recon(idx)
        return XC.rowcorr(Q, att[idx].astype(np.float64)) - XC.rowcorr(Q, ign[idx].astype(np.float64))
    t0 = time.time(); ids = np.concatenate([score_tr, score_te]).astype(int); readout.eval()
    P = recon(ids)
    ra = XC.rowcorr(P, att[ids].astype(np.float64)); ri = XC.rowcorr(P, ign[ids].astype(np.float64)); t_score = time.time() - t0
    n = len(cache.arr['cs_person'])
    margin = np.full(n, np.nan); r_att = np.full(n, np.nan); r_ign = np.full(n, np.nan); scored = np.full(n, '', dtype='<U10')
    margin[ids], r_att[ids], r_ign[ids] = ra - ri, ra, ri; scored[score_tr] = 'train_side'; scored[score_te] = 'test'
    checks = {'margins_finite': bool(np.isfinite(margin[ids]).all()), 'ola_weights_positive': bool((den > 0).all()),
              'span_input_ok': bool(X.shape[-1] == L and P.shape[-1] == L)}
    checks.update(XV.margin_invariance(margin_fn, ids, ra - ri, ra - ri))
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(dest / 'margins.npz', cs_person=cache.arr['cs_person'], cs_code=cache.arr['cs_code'], cs_e0=cache.arr['cs_e0'],
                        cs_role=role, margin=margin, r_att=r_att, r_ign=r_ign, scored=scored)
    if not probe:
        torch.save(best_state, dest / 'readout_adapter.pt')
    rec = {'status': 'complete' if all(v for k, v in checks.items() if k.endswith(('_ok', 'finite', 'positive'))) else 'check_failed',
           'version': 'ctx_v1', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'protocol_sha256': CX.protocol_sha(),
           'dest': str(dest), 'npz_sha256': sha(dest / 'margins.npz'), 'source_checkpoint_sha256': sha(ckpt), 'best_epoch': best_ep,
           'best_val_loss': best, 'history': hist, 'adapter': ainfo, 'full_counts': full,
           'n': {'fit_windows': int(len(xtr)), 'val_windows': int(len(xva)), 'scored_train_side': int(len(score_tr)), 'scored_test': int(len(score_te))},
           'span_64hz': [S0, S1], 'seconds': {'load': round(t_load, 1), 'train': round(t_train, 1), 'score': round(t_score, 1),
                                               'total': round(time.time() - t_all, 1)},
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': job, 'checks': checks,
           'numerics': numerics}
    if probe:
        per = t_train / max(1, len(hist)) / max(1, len(xtr))
        rec['projected_full_unit_hours_at_60_epochs'] = (per * full['fit'] * len(TRAIN_STARTS) * 60 + t_score / max(1, len(ids)) * full['score']) / 3600
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], ds, cf, sf, rec['status'], rec['seconds'], flush=True)
    assert rec['status'] == 'complete', checks
    return rec


def _sub(*args):
    return subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, *map(str, args)]).returncode


def smoke():
    """Probe units (training-side segments only, 2 epochs, no test segment scored) for dtu / fau cf0 sf0."""
    job = os.environ['SLURM_JOB_ID']; plan = make_plan(); verify(plan)
    receipt = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'protocol_sha256': CX.protocol_sha(), 'units': []}
    try:
        for ds in XC.DATASETS:
            row = next(r for r in plan['rows'] if r['dataset'] == ds and r['content_fold'] == 0 and r['person_fold'] == 0)
            rc = _sub('unit', '--id', row['id'], '--probe'); assert rc == 0, (ds, rc)
            rec = read(OUT / 'probes' / job / 'units' / f'{row["id"]}.json')
            assert rec['status'] == 'complete' and rec['n']['scored_test'] == 0
            receipt['units'].append({k: rec[k] for k in ('row', 'seconds', 'gpu_peak_mb', 'device', 'checks', 'numerics', 'history', 'adapter',
                                                         'n', 'full_counts', 'projected_full_unit_hours_at_60_epochs', 'span_64hz')})
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', receipt)


# ------------------------------------------------------------------------------------------------ fleet
def fleet_status():
    return XF.fleet_status(sys.modules[__name__], slots=SLOTS, max_units=MAX_UNITS)


def worker(max_units):
    S = sys.modules[__name__]
    assert XF.receipts(S)['pass'], 'no passing smoke'
    plan = read(OUT / 'plan.json'); verify(plan); count = 0
    for row, failed in XF.open_rows(S):
        if failed:
            continue
        if XF.claim(S, row['id'], lambda: _sub('unit', '--id', row['id'])):
            count += 1
        if count >= max_units:
            break


def score():
    plan = read(OUT / 'plan.json'); verify(plan)
    recs = {r['id']: read(OUT / 'units' / f'{r["id"]}.json') for r in plan['rows'] if (OUT / 'units' / f'{r["id"]}.json').exists()}
    assert len(recs) == len(plan['rows']), f'{len(plan["rows"]) - len(recs)} units incomplete; scoring refused'
    by = CX.score_units(plan['rows'], lambda row: recs[row['id']])
    meta = {f"{r['dataset']}_cf{r['content_fold']}_sf{r['person_fold']}": {k: recs[r['id']][k] for k in ('best_epoch', 'best_val_loss', 'job', 'device')}
            for r in plan['rows']}
    return CX.table(SYSTEM, by, MODULE_FILES, extra={'plan_sha256': sha(OUT / 'plan.json'), 'appendum_sha256': sha(APPENDUM), 'units': meta,
                                                      'definition': read(CX.PROTOCOL)['analyses'][SYSTEM]})


def status():
    out = {'plan': (OUT / 'plan.json').exists()}
    if out['plan']:
        rows_ = read(OUT / 'plan.json')['rows']
        out['complete'] = sum((OUT / 'units' / f'{r["id"]}.json').exists() for r in rows_); out['total'] = len(rows_)
        out['failed'] = sum((OUT / 'units' / f'{r["id"]}.FAILED.json').exists() for r in rows_)
        out['smoke_pass'] = [str(p) for p in XF.receipts(sys.modules[__name__])['pass']]
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('plan', 'appendum', 'smoke', 'worker', 'unit', 'score', 'status'))
    ap.add_argument('--system'); ap.add_argument('--id'); ap.add_argument('--probe', action='store_true')
    ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    assert a.system in (None, SYSTEM), a.system
    if a.cmd == 'appendum':
        print(json.dumps(write_appendum()['geometry_check'])); print(sha(APPENDUM))
    elif a.cmd == 'plan':
        make_plan(); print(sha(OUT / 'plan.json'))
    elif a.cmd == 'smoke':
        smoke()
    elif a.cmd == 'worker':
        worker(a.max_units)
    elif a.cmd == 'unit':
        plan = read(OUT / 'plan.json'); verify(plan)
        run_unit(next(r for r in plan['rows'] if r['id'] == a.id), plan, a.probe)
    elif a.cmd == 'score':
        score()
    elif a.cmd == 'status':
        status()


if __name__ == '__main__':
    main()
