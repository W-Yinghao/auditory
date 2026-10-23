"""W7 GPU training arms (frozen design docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md sections 2.3-2.5,
3 F1(a)/F2/F4, 7; families results/auditory_alignment_v3/paper/w7/W7_FAMILIES_v1.json; clarifications in
private/auditory_alignment_v3/paper/w7_v1/APPENDUM_NN.md) on the unchanged ALN4.1 machinery, as paper/arms.py does.

Arms (objectives in paper/w7_objectives.py)
- TCS_RES      : env audio vector a -> a - h(H) (H = envelope at -20/-100/-200/-500 ms, ridge h fitted once on source fit rows,
                 alpha on source dev rows); option (a): the audio history may lie outside the EEG access interval, asserted to
                 come from the same presentation stream as the current target.
- TCS_CCS      : env view scored by the kernel conditional CS-QMI I_CS(U;A|H); ss/sc unchanged TCS.
- TCS_PRES     : TCS - beta * mean_slot I_CS(P z_theta ; P z0); beta in {0.1, 0.3, 1.0} by the source-only calibration
                 (1,000 updates at seed 3401, common dev ridge probe, exact tie -> smallest beta).
- TCS_RES_PRES : RES and PRES together (inherits the TCS_PRES beta).
- TCS_CTRL     : plain TCS through the same re-pointed path; smoke/benchmark control only (not an arm, no production).
LR = TCS's R1 selection (inherited, not re-selected). Seeds 3401/3407/3413 reuse that seed's ALN4.1 episode stream, panels
and sigma receipt (byte copies, hash-checked), 10,000 updates, snapshots 0/2500/5000/10000, the final one transferred through
aln41/frozen.py and read out with aln41/readout.py and aln41/age.py, all re-pointed in-process. Nothing in aln41 is edited.

CLI (`python -m auditory_alignment_v3.paper.w7_arms ...`, Slurm only):
  validate-ccs (CPU) | plan | prepare | smoke | smoke-unit --arm A --beta B --tag T | bench --arm A --beta B |
  downstream-check | worker [--max-units N] [--only-calibration] | select | unit --arm A --seed S --id ID [--probe] |
  frozen-worker [--max-units N] | frozen-unit --arm A --seed S --id ID | readout [--arm A] (CPU) | status
"""
from __future__ import annotations

import argparse
import contextlib
import copy
from datetime import datetime
import fcntl
import gc
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from ..aln41 import age as AGE, frozen as FZ, r2 as R2, readout as RO, source as SRC, temporal_objectives_torch as TO
from . import w7_objectives as OBJ

SEEDS = (3401, 3407, 3413)
SPEC = {'TCS_PRES': {'res': False, 'ccs': False, 'pres': True, 'calibrate': True},
        'TCS_RES': {'res': True, 'ccs': False, 'pres': False, 'calibrate': False},
        'TCS_CCS': {'res': False, 'ccs': True, 'pres': False, 'calibrate': False},
        'TCS_RES_PRES': {'res': True, 'ccs': False, 'pres': True, 'calibrate': False}}
CONTROL = {'TCS_CTRL': {'res': False, 'ccs': False, 'pres': False, 'calibrate': False}}
ALL = {**SPEC, **CONTROL}
ARMS = tuple(SPEC)                                   # lane order: the beta calibration rows come first
BETAS = (0.1, 0.3, 1.0)
W7 = Path(core.OUT) / 'paper' / 'w7_v1'                # shared W7 record root (rule/, adapt/ ... belong to the other W7 parts)
OUT = W7 / 'arms'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/paper/w7_v1/arms')
FIXED = OUT / 'fixed_v1'
DESIGN = Path(core.REPO) / 'docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md'
DESIGN_SHA = 'c4b461b0a6754af0ba04720320b0acc3f8c907a37f90369a4a250a612a92746c'
FAMILIES = Path(core.REPO) / 'results/auditory_alignment_v3/paper/w7/W7_FAMILIES_v1.json'
FAMILIES_SHA = 'a95aa35f0f47733f9b1ad57427bd1cc477056459c6555c94cb980fb730982421'
F4_MAX_MB, F4_MAX_RATIO = 40 * 1024, 3.0
LANES = {'A': ('c3_s35pw7srcA', 's35_paper_w7_src_a', 'slurm/aln35_paper_w7_src_a.sbatch'),
         'B': ('c3_s35pw7srcB', 's35_paper_w7_src_b', 'slurm/aln35_paper_w7_src_b.sbatch'),
         'Z': ('c3_s35pw7frz', 's35_paper_w7_frozen', 'slurm/aln35_paper_w7_frozen.sbatch')}
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest
_ORIGINAL = {'Source': SRC.Source, 'view_batches': SRC.view_batches, 'build_model': SRC.build_model}
STATE: dict = {}
FIX: dict = {}


def w7_sources():
    here = Path(__file__).parent
    return {str(p.relative_to(core.REPO)): sha(p) for p in (here / 'w7_arms.py', here / 'w7_objectives.py')}


def appenda():
    """Frozen appenda of the W7 arms (w7_v1/APPENDUM_NN.md, 0444); APPENDUM_RAD_* belong to R / A / D."""
    out = {}
    for p in sorted(W7.glob('APPENDUM_[0-9][0-9].md')):
        assert (p.stat().st_mode & 0o222) == 0, f'appendum not frozen: {p.name}'
        out[p.name] = sha(p)
    return out


def check_frozen_design():
    assert sha(DESIGN) == DESIGN_SHA and sha(FAMILIES) == FAMILIES_SHA, 'W7 frozen design / families changed'


def seed_source(seed):
    base = SRC.OUT / 'source_v1' if seed == 3401 else R2.ROOT / f'seed{seed}' / 'source_v1'
    plan = read(base / 'plan.json')
    return base, Path(plan['store']), plan, read(base / 'selection.json')


def tcs_lr():
    return read(SRC.OUT / 'source_v1' / 'selection.json')['choice']['TCS']['lr']


# ----------------------------------------------------------------------------------------------- re-pointed data / model
def history(src, rows, off):
    """Envelope at t - (1, 6, 13, 32) samples (64 Hz) of each anchor, t = s + off the current-target start, read from the SAME
    presentation stream as the current target (DonorBank._target_index); asserted inside [0, stream length) of that stream
    (F1 option (a): may lie outside the EEG access interval, never in another recording). Returns ([n, 4] float32, min pos)."""
    import torch
    rows = np.asarray(rows, np.int64).reshape(-1)
    pres, start = src.seg['presentation'][rows], src.seg['s'][rows]
    off = np.broadcast_to(np.asarray(off, np.int64).reshape(-1), rows.shape)
    st, _ = src.bank._target_index(pres, start, off)
    pos = (start + off)[:, None] - np.asarray(OBJ.lag_samples(64), np.int64)[None]
    assert np.all(pos >= 0) and np.all(pos < src.bank.stream_len[st][:, None]), 'audio history outside its own presentation stream'
    idx = src.bank.stream_off[st][:, None] + pos
    return src.bank.env[torch.as_tensor(idx, device=src.device)], int(pos.min())


class W7Source(_ORIGINAL['Source']):
    """aln41 Source whose audio() replaces the env head input by the history residual (RES) and/or attaches H (CCS)."""

    def audio(self, rows, off):
        import torch
        heads, raw = super().audio(rows, off)
        spec = STATE['spec']
        if spec['res'] or spec['ccs']:
            H, low = history(self, rows, off)
            STATE['history_calls'] += 1
            STATE['history_min_pos'] = low if STATE['history_min_pos'] is None else min(low, STATE['history_min_pos'])
            if spec['res']:
                resid = OBJ.apply_history_map(raw['env'], H, FIX['hmap'])
                with torch.no_grad():
                    heads['env'] = self.heads['env'](resid)
            if spec['ccs']:
                heads['_h'] = H
        return heads, raw


def view_batches_w7(U, A, sig, wrong=None):
    from dataclasses import replace
    assert wrong is None, 'W7 arms never use a wrong pairing'
    out = list(_ORIGINAL['view_batches'](U, A, sig, None))
    assert [b.name for b in out] == ['env', 'ss', 'sc']
    spec = STATE['spec']
    if spec['res']:
        out[0] = replace(out[0], sigma_v=FIX['sigma_res'])
    if spec['ccs']:
        b = out[0]
        out[0] = OBJ.CondViewBatch(b.u, b.v, b.sigma_u, b.sigma_v, b.sigma_pooled_u, b.name, A['_h'].double(), FIX['sigma_h'])
    return out


def build_model_w7(device):
    """Original seeded build; for PRES a frozen copy of the INITIAL model (unregistered: state_dict, parameter groups and the
    initial-state digest are unchanged) and a forward recorder of the grad-enabled training forwards (the query crops)."""
    import torch
    model, a = _ORIGINAL['build_model'](device)
    if STATE['spec']['pres']:
        model0 = copy.deepcopy(model).requires_grad_(False).eval()
        object.__setattr__(model, '_w7_initial', model0)
        forward = model.forward

        def recorded(crops, views=None):
            proj, tok = forward(crops, views)
            if torch.is_grad_enabled() and model.training:
                STATE['last'] = {'crops': crops, 'proj': proj, 'tok': tok}
            return proj, tok
        model.forward = recorded
        STATE['model0'] = model0
    return model, a


def pres_term(query):
    import torch
    last = STATE.get('last'); STATE['last'] = None
    assert last is not None, 'PRES: no recorded query forward'
    assert all(last['proj'][v.name] is v.u for v in query), 'PRES: the recorded forward is not this query'
    m0 = STATE['model0']
    assert all(p.grad is None and not p.requires_grad for p in m0.parameters()), 'PRES: the initial backbone received a gradient'
    with torch.no_grad():
        z0 = m0.tokens(last['crops']).flatten(2)
    zt = last['tok'].flatten(2)
    assert zt.requires_grad and not z0.requires_grad and z0.grad_fn is None
    pca = FIX.setdefault('pca_device', {k: v.to(zt.device) for k, v in FIX['pca'].items()})
    STATE['pres_calls'] += 1
    return OBJ.pres_dependence(zt, z0, pca, FIX['sigma_pres'])


def load_fixed():
    import torch
    f = read(FIXED / 'fixed.json')
    assert sha(FIXED / 'pca_dev.pt') == f['pca_sha256'] and f['hmap']['rows'] == 'source fit panel (role fit) only'
    pca = torch.load(FIXED / 'pca_dev.pt', map_location='cpu')
    return {'hmap': f['hmap'], 'sigma_h': f['sigma_h'], 'sigma_res': f['sigma_res'], 'sigma_pres': f['sigma_pres'],
            'pca': {k: pca[k].float() for k in ('mu', 'sd', 'components')}, 'sha256': sha(FIXED / 'fixed.json')}


def fixed_sha():
    return sha(FIXED / 'fixed.json')


@contextlib.contextmanager
def ctx(arm, seed, check_job=None):
    """Re-point aln41 source / frozen / readout / age and the objective to one W7 arm x seed (or, with check_job, the stored
    seed-3401 TCS source into a downstream-check directory); restores everything on exit."""
    assert seed in SEEDS and (arm in ALL or (check_job and arm == 'TCS'))
    saved = [(m, k, getattr(m, k)) for m, keys in ((SRC, ('SEED', 'STREAM_SEED', 'BASE', 'STORE', 'view_batches', 'Source', 'build_model')),
                                                     (FZ, ('BASE', 'STORE', 'ARMS')), (RO, ('BASE',)), (AGE, ('BASE', 'ARMS')),
                                                     (TO, ('episode_loss_fo',))) for k in keys]
    saved_state, saved_fix = dict(STATE), dict(FIX)
    try:
        if check_job:
            root, sroot = OUT / 'downstream_check' / str(check_job), STORE / 'downstream_check' / str(check_job)
            FZ.BASE, FZ.STORE, FZ.ARMS = root / 'frozen_v1', sroot / 'frozen_v1', ('TCS',)
            RO.BASE, AGE.BASE, AGE.ARMS = root / 'readout_v1', root / 'age_v1', ('TCS',)
            yield root
            return
        spec = ALL[arm]; root, sroot = OUT / arm / f'seed{seed}', STORE / arm / f'seed{seed}'
        SRC.SEED, SRC.STREAM_SEED = seed, seed + 41000
        SRC.BASE, SRC.STORE = root / 'source_v1', sroot / 'source_v1'
        FZ.BASE, FZ.STORE, FZ.ARMS = root / 'frozen_v1', sroot / 'frozen_v1', (arm,)
        RO.BASE, AGE.BASE, AGE.ARMS = root / 'readout_v1', root / 'age_v1', (arm,)
        STATE.clear(); STATE.update(spec=spec, beta=None, trace=[], pres=pres_term, last=None, model0=None, history_calls=0,
                                    history_min_pos=None, pres_calls=0, ccs_calls=0)
        FIX.clear()
        if spec['res'] or spec['ccs'] or spec['pres']:
            FIX.update(load_fixed())
        if spec['res'] or spec['ccs']:
            SRC.Source, SRC.view_batches = W7Source, view_batches_w7
        if spec['pres']:
            SRC.build_model = build_model_w7
        TO.episode_loss_fo = OBJ.make_episode_loss(arm, spec, STATE)
        yield root
    finally:
        for m, k, v in saved:
            setattr(m, k, v)
        STATE.clear(); STATE.update(saved_state); FIX.clear(); FIX.update(saved_fix)


# ----------------------------------------------------------------------------------------------- prepare (GPU, once)
def prepare():
    """Seed-independent fixed quantities, written once (0444) before any W7 training: the history map and its bandwidths
    (RES/CCS) and the PRES projection and bandwidth (F2). Source data only (the frozen ALN4.1 fit/dev panels, identical for
    the three seeds); the initial Stage1 backbone is the same for every seed."""
    import torch
    if (FIXED / 'fixed.json').exists():
        return read(FIXED / 'fixed.json')
    check_frozen_design(); assert appenda(), 'APPENDUM_01 must be frozen first'
    dev = torch.device('cuda')
    base0, store0, plan0, _ = seed_source(3401)
    panels = {s: sha(seed_source(s)[1] / 'panels.npz') for s in SEEDS}
    assert len(set(panels.values())) == 1 and plan0['panels_sha256'] == panels[3401]
    man = SRC.open_manifest(); P = SRC.load_arrays(store0 / 'panels.npz')
    split_pool, _ = SRC.pool(man)
    from ..prior33 import views as V
    segt = V.manifest_index(man).seg['sparrkulee']
    fit_pool = {r for p in split_pool['fit'].values() for v in p.values() for r in v}
    dev_pool = {r for p in split_pool['dev'].values() for v in p.values() for r in v}
    assert all(segt['role'][r] == 'fit' and int(r) in fit_pool for r in P['fit_rows']), 'fit panel row outside the source fit pool'
    assert all(segt['role'][r] == 'dev' and int(r) in dev_pool for r in P['dev_rows']), 'dev panel row outside the source dev pool'
    src = SRC.Source(man, np.r_[P['fit_rows'], P['dev_rows']], dev)
    with torch.no_grad():
        _, raw_f = src.audio(P['fit_rows'], P['fit_off']); _, raw_d = src.audio(P['dev_rows'], P['dev_off'])
        H_f, low_f = history(src, P['fit_rows'], P['fit_off']); H_d, low_d = history(src, P['dev_rows'], P['dev_off'])
    A_f, A_d = raw_f['env'].double().cpu().numpy(), raw_d['env'].double().cpu().numpy()
    hmap = OBJ.fit_history_map(H_f.double().cpu().numpy(), A_f, H_d.double().cpu().numpy(), A_d)
    hmap.update(rows='source fit panel (role fit) only', alpha_rows='source dev panel (role dev)', lags_samples_64hz=list(OBJ.lag_samples(64)),
                lags_ms=list(OBJ.LAGS_MS), fit_rows_sha256=digest(P['fit_rows'].tolist()), dev_rows_sha256=digest(P['dev_rows'].tolist()))
    h_mult, vpath = chosen_h_multiplier()
    assert h_mult is not None, 'no passing CCS validation (APPENDUM_03)'
    sigma_h_median = OBJ.pooled_slot_sigma(H_f.double().cpu()); sigma_h = h_mult * sigma_h_median
    with torch.no_grad():
        resid = OBJ.apply_history_map(raw_f['env'], H_f, hmap)
        res_head = src.heads['env'](resid).double().cpu()
        env_head = src.heads['env'](raw_f['env']).double().cpu()
    sigma_res, sigma_env = OBJ.pooled_slot_sigma(res_head), OBJ.pooled_slot_sigma(env_head)
    seed_sig = {s: read(seed_source(s)[0] / 'sigmas.json')['sigmas']['env']['sigma_v'] for s in SEEDS}
    assert all(abs(v - sigma_env) <= 1e-6 * sigma_env for v in seed_sig.values()), ('TCS env audio sigma not reproduced', seed_sig, sigma_env)
    # F2: PCA64 of B0 tokens on the source dev panel (frozen.pca_fit convention), PRES bandwidth on the fit panel
    model, _ = SRC.build_model(dev)                          # SRC.SEED = 3401; the backbone part is the Stage1 CBraMod state
    init = SRC.state_digest(model); assert init == read(base0 / 'sigmas.json')['initial_state_sha256']
    _, _, Td, _ = SRC.panel_features(src, model, P['dev_rows'], P['dev_off'])
    _, _, Tf, _ = SRC.panel_features(src, model, P['fit_rows'], P['fit_off'])
    Td, Tf = Td.reshape(len(Td), 3, -1), Tf.reshape(len(Tf), 3, -1)
    pca = FZ.pca_fit(Td, np.arange(len(Td)), FZ.PCA_SEED)
    assert pca['dim'] == 64 and pca['n_rows'] == 3 * len(Td)
    FIXED.mkdir(parents=True, exist_ok=True, mode=0o700)
    for stale in (FIXED / 'pca_dev.pt', FIXED / 'pca_dev.pt.tmp'):   # a partial earlier prepare (no fixed.json) is discarded
        if stale.exists():
            stale.unlink()
    torch.save({k: pca[k] for k in ('mu', 'sd', 'components')}, FIXED / 'pca_dev.pt.tmp')
    os.replace(FIXED / 'pca_dev.pt.tmp', FIXED / 'pca_dev.pt'); (FIXED / 'pca_dev.pt').chmod(0o444)
    proj = {k: pca[k].float() for k in ('mu', 'sd', 'components')}
    Pz_f = torch.stack([OBJ.pca_project(Tf[:, k].float(), proj) for k in range(3)], 1).double()
    sigma_pres = OBJ.pooled_slot_sigma(Pz_f)
    # descriptive characterisation at the initial state (no training): the fixed-bandwidth KDE CS-QMI of (P z, P z0)
    from ..aln41.cs_qmi_reference import cs_qmi
    g = torch.Generator().manual_seed(3401); char = {'identity': [], 'scale_1.2': [], 'noise_0.3sd': []}
    sd_pz = float(Pz_f.std())
    for b in range(16):
        z = Pz_f[b * 32:(b + 1) * 32]
        for k in range(3):
            ref = z[:, k]
            char['identity'].append(float(cs_qmi(ref, ref, sigma_u=sigma_pres, sigma_v=sigma_pres)[0]))
            char['scale_1.2'].append(float(cs_qmi(1.2 * ref, ref, sigma_u=sigma_pres, sigma_v=sigma_pres)[0]))
            noise = .3 * sd_pz * torch.randn(ref.shape, generator=g, dtype=torch.float64)
            char['noise_0.3sd'].append(float(cs_qmi(ref + noise, ref, sigma_u=sigma_pres, sigma_v=sigma_pres)[0]))
    body = {'version': 'W7_FIXED_v1', 'design_sha256': DESIGN_SHA, 'appenda': appenda(), 'w7_sources': w7_sources(),
            'panels_sha256': panels[3401], 'stage1_initial_state_sha256': init,
            'hmap': hmap, 'history_min_position_samples': {'fit': low_f, 'dev': low_d},
            'sigma_h': sigma_h, 'sigma_h_median_rule': sigma_h_median, 'sigma_h_multiplier': h_mult,
            'sigma_h_rule': 'APPENDUM_02/03: 0.5 x lower median of pairwise distances of raw H on the source fit panel (overlap SD)',
            'ccs_validation_receipt': str(vpath), 'ccs_validation_receipt_sha256': sha(vpath),
            'sigma_res': sigma_res, 'sigma_env_tcs': sigma_env, 'sigma_env_seed_receipts': {str(k): v for k, v in seed_sig.items()},
            'sigma_res_rule': 'TCS sigma rule on the RES env feature: lower median distinct-anchor distance of head_env(a - h(H)), fit panel',
            'pca_sha256': sha(FIXED / 'pca_dev.pt'), 'pca': {k: pca[k] for k in ('n_rows', 'dim', 'explained_variance')},
            'pca_rule': 'frozen.pca_fit on B0 tokens [3 slots x 512 dev-panel anchors] (per-feature standardisation, SVD, top 64)',
            'sigma_pres': sigma_pres, 'sigma_pres_rule': 'lower median within-slot distinct-anchor distance of P z0, fit panel, pooled over 3 slots',
            'pres_initial_state_characterisation': {k: {'mean': float(np.mean(v)), 'min': float(np.min(v)), 'max': float(np.max(v))}
                                                    for k, v in char.items()},
            'device': torch.cuda.get_device_name(0), 'job': os.environ.get('SLURM_JOB_ID'),
            'created': datetime.now().astimezone().isoformat()}
    write(FIXED / 'fixed.json', body); (FIXED / 'fixed.json').chmod(0o444)
    del src, model; gc.collect(); torch.cuda.empty_cache()
    return body


# ----------------------------------------------------------------------------------------------- plans (CPU)
def selected_beta(arm):
    if not ALL[arm]['pres']:
        return None
    path = OUT / 'TCS_PRES' / 'seed3401' / 'source_v1' / 'selection.json'
    return read(path)['choice']['TCS_PRES']['beta'] if path.exists() else None


def production_row(arm, seed, lr, beta):
    body = {'stage': 'production', 'arm': arm, 'lr': lr, 'beta': beta, 'updates': SRC.PROD_STEPS, 'seed': seed}
    return {**body, 'id': 'W7P_' + digest(body, 16)}


def calibration_rows(lr):
    rows = []
    for b in BETAS:
        body = {'stage': 'calibration', 'arm': 'TCS_PRES', 'lr': lr, 'beta': b, 'updates': SRC.CAL_STEPS, 'seed': 3401}
        rows.append({**body, 'id': 'W7C_' + digest(body, 16)})
    return rows


def make_plan(arm, seed):
    check_frozen_design()
    base0, store0, plan0, _ = seed_source(seed)
    lr, beta = tcs_lr(), selected_beta(arm)
    spec = ALL[arm]; calib = spec['calibrate'] and seed == 3401
    uses_fixed = spec['res'] or spec['ccs'] or spec['pres']
    with ctx(arm, seed):
        for d in (SRC.BASE, SRC.STORE):
            d.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name, key in (('stream.npz', 'stream_sha256'), ('panels.npz', 'panels_sha256')):
            if not (SRC.STORE / name).exists():
                shutil.copyfile(store0 / name, SRC.STORE / name)
            assert sha(SRC.STORE / name) == plan0[key], name
        if not SRC.sigmas_path().exists():
            shutil.copyfile(base0 / 'sigmas.json', SRC.sigmas_path()); SRC.sigmas_path().chmod(0o444)
        assert sha(SRC.sigmas_path()) == sha(base0 / 'sigmas.json')
        keep = ('package_zip_sha256', 'manifest_sha256', 'rich_sha256', 'stage1', 'stage1_gate_sha256', 'pool', 'eligible_people',
                'excluded_people', 'panel_seed', 'inner', 'optimizer', 'production_updates', 'production_snapshots')
        body = {'version': 'PAPER_W7_SOURCE_v1', 'arm': arm, 'seed': seed, 'spec': spec, 'control_only': arm in CONTROL,
                'rows': calibration_rows(lr) if calib else [], 'sources': SRC.sources(), 'w7_sources': w7_sources(), 'store': str(SRC.STORE),
                **{k: plan0[k] for k in keep}, 'views': ['env', 'ss', 'sc'], 'stream_seed': SRC.STREAM_SEED,
                'stream_sha256': plan0['stream_sha256'], 'panels_sha256': plan0['panels_sha256'],
                'seed_source_plan_sha256': sha(base0 / 'plan.json'), 'sigmas_sha256': sha(SRC.sigmas_path()),
                'design_sha256': DESIGN_SHA, 'families_sha256': FAMILIES_SHA, 'appenda': appenda(),
                'fixed_sha256': fixed_sha() if uses_fixed else None, 'lr': lr,
                'lr_rule': 'TCS R1 selection inherited (not re-selected)',
                'beta_rule': ('source-only calibration at seed 3401: beta in {0.1, 0.3, 1.0}, 1000 updates, common dev ridge probe '
                              '(aln41 select rule), exact tie -> smallest beta; other seeds and TCS_RES_PRES inherit') if spec['pres'] else None}
        plan = SRC.BASE / 'plan.json'
        if plan.exists():
            old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
        else:
            write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
        if arm in SPEC and not (SRC.BASE / 'selection.json').exists() and (not spec['pres'] or beta is not None):
            write_selection(arm, seed, lr, beta, 'inherits_TCS_R1_lr' + ('; inherits_TCS_PRES_beta' if spec['pres'] else ''))
    return True


def write_selection(arm, seed, lr, beta, status, probe=None):
    rows = [production_row(arm, seed, lr, beta)]
    sel = {'version': 'PAPER_W7_SELECTION_v1', 'plan_sha256': sha(SRC.BASE / 'plan.json'),
           'choice': {arm: {'lr': lr, 'beta': beta, 'status': status, **({'probe': probe} if probe else {})}}, 'production_rows': rows,
           'created': datetime.now().astimezone().isoformat()}
    path = SRC.BASE / 'selection.json'
    if path.exists():
        old = read(path); assert old['choice'][arm]['beta'] == beta and old['production_rows'] == rows
        return old
    write(path, sel); path.chmod(0o444)
    return sel


def select_beta():
    """Seed-3401 calibration -> beta (aln41 select rule: lowest dev normalised MSE of the common probe, exact tie -> smallest;
    any nonfinite probe -> smallest, 'uninformative_selection'); then TCS_PRES 3407/3413 and TCS_RES_PRES inherit."""
    with ctx('TCS_PRES', 3401):
        plan = read(SRC.BASE / 'plan.json'); recs = {}
        for r in plan['rows']:
            u = read(SRC.BASE / 'units' / f'{r["id"]}.json'); assert u['status'] == 'complete'
            recs[r['beta']] = u['selection_probe']
        finite = all(math.isfinite(recs[b]['mean']) for b in BETAS)
        best = min(BETAS, key=lambda b: (recs[b]['mean'], b)) if finite else min(BETAS)
        sel = write_selection('TCS_PRES', 3401, plan['lr'], best, 'selected' if finite else 'uninformative_selection',
                              {str(k): v for k, v in recs.items()})
    for seed in SEEDS[1:]:
        make_plan('TCS_PRES', seed)
    for seed in SEEDS:
        make_plan('TCS_RES_PRES', seed)
    return sel


def plans():
    assert (FIXED / 'fixed.json').exists(), 'run prepare first'
    for arm in ARMS:
        for seed in SEEDS:
            make_plan(arm, seed)
    make_plan('TCS_CTRL', 3401)


# ----------------------------------------------------------------------------------------------- state
def source_rows(arm, seed):
    base = OUT / arm / f'seed{seed}' / 'source_v1'
    if not (base / 'plan.json').exists():
        return base, []
    rows = list(read(base / 'plan.json')['rows'])
    if (base / 'selection.json').exists():
        rows += read(base / 'selection.json')['production_rows']
    return base, rows


def production_done(arm, seed):
    base, rows = source_rows(arm, seed)
    prod = [r for r in rows if r['stage'] == 'production']
    return bool(prod) and all((base / 'units' / f'{r["id"]}.json').exists() for r in prod)


def calibration_pending_selection():
    base, rows = source_rows('TCS_PRES', 3401)
    calib = [r for r in rows if r['stage'] == 'calibration']
    return bool(calib) and all((base / 'units' / f'{r["id"]}.json').exists() for r in calib) and not (base / 'selection.json').exists()


def open_source_units(only_calibration=False):
    out = []
    for arm in ARMS:
        for seed in SEEDS:
            base, rows = source_rows(arm, seed)
            for r in rows:
                if only_calibration and r['stage'] != 'calibration':
                    continue
                if not (base / 'units' / f'{r["id"]}.json').exists():
                    out.append((arm, seed, r, (base / 'units' / f'{r["id"]}.FAILED.json').exists()))
    return out


def frozen_rows(arm, seed):
    base = OUT / arm / f'seed{seed}' / 'frozen_v1'
    return base, (read(base / 'plan.json')['rows'] if (base / 'plan.json').exists() else [])


def open_frozen_units():
    out = []
    for arm in ARMS:
        for seed in SEEDS:
            if not production_done(arm, seed):
                continue
            base, rows = frozen_rows(arm, seed)
            if not rows:
                out.append((arm, seed, None, False)); continue
            for r in rows:
                if not (base / 'units' / f'{r["id"]}.json').exists():
                    out.append((arm, seed, r, (base / 'units' / f'{r["id"]}.FAILED.json').exists()))
    return out


def receipts():
    out = {'pass': [], 'other': []}
    for path in sorted((OUT / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('w7_sources') == w7_sources():
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status(lane='A'):
    name, lane_name, sbatch = LANES[lane]
    st = {'name': name, 'lane': lane_name, 'state': 'plan_missing', 'ready': 0, 'remaining': 1, 'slots': 1, 'initial': [], 'submit': []}
    if not (OUT / 'TCS_PRES' / 'seed3401' / 'source_v1' / 'plan.json').exists():
        return st
    rec = receipts()
    if not rec['pass']:
        return {**st, 'state': 'engineering_probe_failed' if rec['other'] else 'waiting_smoke'}
    if lane == 'Z':
        units = open_frozen_units()
        st['remaining'] = len(units) + sum(1 for a in ARMS for s in SEEDS if not production_done(a, s))
        if not st['remaining']:
            return {**st, 'state': 'complete'}
        if any(f for *_, f in units):
            return {**st, 'state': 'failed_unit_review'}
        ready = len(units)
        return {**st, 'state': 'ready' if ready else 'waiting_for_sources', 'ready': ready, 'slots': 2,
                'submit': [sbatch, 'frozen-worker', '--max-units', '3']}
    units = open_source_units()
    pending = sum(1 for a in ARMS for s in SEEDS if not (OUT / a / f'seed{s}' / 'source_v1' / 'selection.json').exists())
    st['remaining'] = len(units) + pending
    if not st['remaining']:
        return {**st, 'state': 'complete'}
    if any(f for *_, f in units):
        return {**st, 'state': 'failed_unit_review'}
    ready = len(units) + (1 if calibration_pending_selection() else 0)
    if lane == 'B':
        ready = max(0, ready - 2)                       # lane B only takes work beyond lane A's two slots
    return {**st, 'state': 'ready' if ready else 'waiting_calibration', 'ready': ready, 'slots': 2,
            'submit': [sbatch, 'worker', '--max-units', '2']}


# ----------------------------------------------------------------------------------------------- GPU steps
def sidecar_path(uid, probe):
    job = os.environ['SLURM_JOB_ID']
    return (SRC.BASE / 'probes' / job if probe else SRC.BASE) / 'w7' / f'{uid}.json'


def run_row(arm, seed, row, plan, probe):
    STATE['beta'] = row.get('beta')
    assert (STATE['beta'] is not None) == bool(ALL[arm]['pres']), 'beta must be set exactly for the PRES arms'
    if ALL[arm]['res']:                                  # the residual map comes from the source fit panel rows only
        P = SRC.load_arrays(SRC.STORE / 'panels.npz')
        assert digest(P['fit_rows'].tolist()) == FIX['hmap']['fit_rows_sha256'] and FIX['hmap']['rows'] == 'source fit panel (role fit) only'
    t0 = time.time()
    rec = SRC.run_unit(row, plan, probe=probe)
    side = {'row': row, 'unit_seconds': time.time() - t0, 'history_calls': STATE['history_calls'],
            'history_min_position_samples': STATE['history_min_pos'], 'pres_calls': STATE['pres_calls'], 'ccs_calls': STATE['ccs_calls'],
            'pres_trace_every_call': STATE['trace'], 'beta': STATE['beta'], 'fixed_sha256': FIX.get('sha256'),
            'unit_record_sha256': sha((SRC.BASE / 'probes' / os.environ['SLURM_JOB_ID'] if probe else SRC.BASE) / 'units' / f'{row["id"]}.json'),
            'resumed_unit': len(STATE['trace']) < 2 * row['updates'] if ALL[arm]['pres'] else None}
    if ALL[arm]['pres']:
        assert STATE['pres_calls'] >= 2 and all(p.grad is None for p in STATE['model0'].parameters())
    if ALL[arm]['res'] or ALL[arm]['ccs']:
        assert STATE['history_calls'] > 0 and STATE['history_min_pos'] >= 0
    assert (STATE['ccs_calls'] > 0) == bool(ALL[arm]['ccs'])
    write(sidecar_path(row['id'], probe), side)
    return rec


def verify_plan(plan, arm):
    SRC.verify(plan)
    assert plan['w7_sources'] == w7_sources(), 'W7 source drift'
    assert plan['design_sha256'] == DESIGN_SHA and plan['appenda'] == appenda()
    if plan['fixed_sha256'] is not None:
        assert plan['fixed_sha256'] == fixed_sha() == FIX['sha256']


def run_one(arm, seed, uid, probe=False):
    with ctx(arm, seed):
        plan = read(SRC.BASE / 'plan.json'); verify_plan(plan, arm)
        _, rows = source_rows(arm, seed)
        return run_row(arm, seed, next(r for r in rows if r['id'] == uid), plan, probe)


def smoke_row(arm, beta, tag):
    body = {'stage': 'smoke', 'arm': arm, 'lr': tcs_lr(), 'beta': beta, 'updates': 3, 'seed': 3401, 'tag': tag}
    return {**body, 'id': 'W7S_' + digest(body, 16)}


def run_smoke_unit(arm, beta, tag):
    with ctx(arm, 3401):
        plan = read(SRC.BASE / 'plan.json'); verify_plan(plan, arm)
        return run_row(arm, 3401, smoke_row(arm, beta, tag), plan, True)


def run_frozen(arm, seed, uid):
    with ctx(arm, seed):
        plan = read(FZ.BASE / 'plan.json'); FZ.verify(plan)
        return FZ.run_unit(next(r for r in plan['rows'] if r['id'] == uid), plan)


def bench(arm, beta, n=12):
    """F4 / timing: the run_unit update body (2 people, support no-grad, query with grad, episode objective, clip 5, AdamW)
    timed per update with CUDA synchronisation; median of updates 3..n; peak memory. No checkpoint, no record but this JSON."""
    import torch
    job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda')
    with ctx(arm, 3401):
        STATE['beta'] = beta
        sig = read(SRC.sigmas_path())['sigmas']; stream = SRC.load_arrays(SRC.STORE / 'stream.npz'); man = SRC.open_manifest()
        src = SRC.Source(man, stream['rows'][:n].reshape(-1), dev); model, a = SRC.build_model(dev); lr = tcs_lr()
        opt = torch.optim.AdamW(SRC.param_groups(model, a, lr), lr=lr); params = [p for g in opt.param_groups for p in g['params']]
        kw = {k: SRC.INNER[k] for k in ('steps', 'step_size', 'delta_l2', 'prior_kl_weight', 'temperature')}
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats(); times, losses = [], []
        for u in range(n):
            torch.cuda.synchronize(); t0 = time.perf_counter()
            model.train(); total = 0.0
            for j in range(2):
                S, Q = stream['rows'][u, j]; oS, oQ = stream['off'][u, j]
                AS, _ = src.audio(S, oS); AQ, _ = src.audio(Q, oQ)
                with torch.no_grad():
                    US, _ = model(src.crops(S, oS))
                UQ, _ = model(src.crops(Q, oQ))
                sv = SRC.view_batches({v: x.detach() for v, x in US.items()}, AS, sig); qv = SRC.view_batches(UQ, AQ, sig)
                loss, _ = TO.episode_loss_fo(arm, sv, qv, a, **kw)
                total = total + loss / 2
            opt.zero_grad(set_to_none=True); total.backward(); torch.nn.utils.clip_grad_norm_(params, 5.0); opt.step()
            torch.cuda.synchronize(); times.append(time.perf_counter() - t0); losses.append(float(total.detach()))
        out = {'arm': arm, 'beta': beta, 'n_updates': n, 'update_seconds': times, 'median_update_seconds': float(np.median(times[2:])),
               'peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'first_loss': losses[0], 'device': torch.cuda.get_device_name(0)}
    write(OUT / 'probes' / job / 'bench' / f'{arm}.json', out)
    return out


def json_equal(a, b):
    return json.loads(json.dumps(a, sort_keys=True)) == json.loads(json.dumps(b, sort_keys=True))


def downstream_check():
    """The stored seed-3401 TCS checkpoint routed through the W7 re-pointed frozen / readout / age path (private children and
    FAU content fold 0) must reproduce the stored ALN4.1 TCS frozen arrays and readouts exactly."""
    job = os.environ['SLURM_JOB_ID']; out = {'job': job, 'cohorts': {}}
    r1_frozen, r1_readout = SRC.OUT / 'frozen_v1', SRC.OUT / 'readout_v1'
    with ctx('TCS', 3401, check_job=job):
        FZ.make_plan(); plan = read(FZ.BASE / 'plan.json'); FZ.verify(plan)
        stored_ids = {r['id'] for r in read(r1_frozen / 'plan.json')['rows']}
        for ds, cf in (('private_bdf', None), ('fau', 0)):
            row = next(r for r in plan['rows'] if r['dataset'] == ds and r['content_fold'] == cf)
            assert row['id'] in stored_ids, 'downstream check row id differs from the stored ALN4.1 row'
            rec = FZ.run_unit(row, plan)
            old = read(r1_frozen / 'units' / f'{row["id"]}.json')
            with np.load(Path(rec['dest']) / 'arrays.npz', allow_pickle=False) as z1, np.load(Path(old['dest']) / 'arrays.npz', allow_pickle=False) as z0:
                keys = sorted(set(z1.files) | set(z0.files))
                diff = {k: (None if k not in z1.files or k not in z0.files else
                            (0.0 if np.array_equal(z1[k], z0[k]) else
                             float(np.max(np.abs(z1[k].astype(np.float64) - z0[k].astype(np.float64)))) if z1[k].dtype.kind == 'f' else 'differs'))
                        for k in keys}
            res = RO.private(row) if ds == 'private_bdf' else RO.public(row)
            stored = read(r1_readout / 'units' / f'{row["id"]}.json')
            out['cohorts'][f'{ds}/{cf}'] = {'row': row['id'], 'device': rec['device'], 'stored_device': old['device'],
                                            'arrays_identical': all(v == 0.0 for v in diff.values()),
                                            'array_max_abs_diff': {k: v for k, v in diff.items() if v != 0.0},
                                            'readout_identical': json_equal(res['people'], stored['people']) and json_equal(res['q0'], stored['q0'])}
        argv = sys.argv
        try:
            sys.argv = ['age']; AGE.main()
        finally:
            sys.argv = argv
        mine = read(AGE.BASE / 'age_results.json')['arms']['TCS']; stored = read(SRC.OUT / 'age_v1' / 'age_results.json')['arms']['TCS']
        out['age_identical'] = json_equal(mine, stored)
    out['pass'] = bool(all(c['readout_identical'] for c in out['cohorts'].values()) and out['age_identical'])
    out['arrays_bit_identical'] = all(c['arrays_identical'] for c in out['cohorts'].values())
    write(OUT / 'probes' / job / 'downstream_check.json', out)
    return out


def sub(*args):
    return subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, *map(str, args)]).returncode


def validation_receipts(h_mult, seed, sided):
    out = []
    for p in sorted((OUT / 'ccs_validation').glob('*/receipt.json')):
        r = read(p)
        if (r.get('w7_objectives_sha256') == sha(Path(OBJ.__file__)) and r.get('h_multiplier') == h_mult and r.get('seed') == seed
                and r.get('sided') == sided):
            out.append((p, r))
    return out


def chosen_h_multiplier():
    """APPENDUM_03: sigma_h multiplier of the single current validation rung if its receipt passed; None while missing."""
    m, seed, sided = OBJ.CCS_VALIDATION
    recs = [r for r in validation_receipts(m, seed, sided) if r[1]['status'] in ('pass', 'failed')]
    if not recs:
        return None, None
    p, r = recs[-1]
    if r['status'] != 'pass':
        raise RuntimeError('the APPENDUM_03 CCS validation failed: a further appendum is required before any CCS Stage2 output')
    return m, p


def latest_validation():
    m, p = chosen_h_multiplier()
    return (p, read(p)) if p is not None else (None, None)


def validate_ccs(h_mult, seed, sided='upper'):
    import torch
    torch.set_num_threads(int(os.environ.get('OMP_NUM_THREADS', '2')))
    check_frozen_design(); assert appenda(), 'APPENDUM_01 must be frozen before validation'
    assert (h_mult, seed, sided) == OBJ.CCS_VALIDATION, 'only the APPENDUM_03 rung may be validated'
    job = os.environ['SLURM_JOB_ID'] + '.' + os.environ.get('SLURM_STEP_ID', 'batch'); t0 = time.time()
    receipt = {'status': 'running', 'w7_objectives_sha256': sha(Path(OBJ.__file__)), 'appenda': appenda(), 'job': job,
               'h_multiplier': h_mult, 'seed': seed, 'sided': sided}
    try:
        res = OBJ.validation_suite(seed=seed, h_multipliers=(h_mult,), sensitivity=(), sided=sided)
        receipt.update(result=res, gate=res['gate'], status='pass' if res['gate']['pass_cpu_part'] else 'failed')
    except BaseException:
        receipt.update(status='error', traceback=traceback.format_exc()); raise
    finally:
        receipt['seconds'] = time.time() - t0
        write(OUT / 'ccs_validation' / job / 'receipt.json', receipt)
    print(json.dumps(receipt['gate'], indent=1))


def compare_replay(a, b):
    """Two runs of the same 3-update probe: logged losses, grad norms, deltas and the final checkpoint tensors."""
    import torch
    same_log = [(x['loss'], x['grad_norm'], x['delta']) for x in a['log']] == [(x['loss'], x['grad_norm'], x['delta']) for x in b['log']]
    ca = torch.load(a['final_checkpoint'], map_location='cpu', weights_only=False)
    cb = torch.load(b['final_checkpoint'], map_location='cpu', weights_only=False)
    tensors = all(torch.equal(ca[k][n], cb[k][n]) for k in ('backbone', 'heads') for n in ca[k]) and torch.equal(ca['a'], cb['a'])
    return {'log_identical': same_log, 'checkpoint_tensors_identical': bool(tensors)}


def smoke():
    """Gate 7.3 for the W7 arms (one 3-update probe per new arm + the TCS control, each run twice)."""
    import torch
    job = os.environ['SLURM_JOB_ID']
    receipt = {'status': 'running', 'w7_sources': w7_sources(), 'job': job, 'units': {}}
    try:
        check_frozen_design(); receipt['appenda'] = appenda()
        for _ in range(120):                             # the CPU validation step may still be finishing (<= 30 min)
            if chosen_h_multiplier()[0] is not None:
                break
            time.sleep(15)
        vp, vr = latest_validation()
        assert vr is not None and vr['status'] == 'pass', 'CCS estimator validation (i)-(iv) has not passed for this objective source'
        receipt['ccs_validation'] = {'receipt': str(vp), 'sha256': sha(vp), 'gate': vr['gate']}
        receipt['ccs_v_gpu'] = OBJ.objective_step_timing(torch.device('cuda'))
        assert receipt['ccs_v_gpu']['pass'], 'CCS gate (v): objective step time > 2 x TCS on the training GPU'
        fixed = prepare()
        receipt['fixed'] = {'sha256': fixed_sha(), 'hmap_alpha': fixed['hmap']['alpha_relative'], 'sigma_h': fixed['sigma_h'],
                            'sigma_res': fixed['sigma_res'], 'sigma_env_tcs': fixed['sigma_env_tcs'], 'sigma_pres': fixed['sigma_pres'],
                            'pca_explained_variance': fixed['pca']['explained_variance'],
                            'pres_initial_state_characterisation': fixed['pres_initial_state_characterisation']}
        plans()
        for arm, beta in (('TCS_CTRL', None), ('TCS_RES', None), ('TCS_CCS', None), ('TCS_PRES', BETAS[0]), ('TCS_RES_PRES', BETAS[0])):
            recs = []
            for tag in ('a', 'b'):
                args = ['smoke-unit', '--arm', arm, '--tag', tag] + (['--beta', beta] if beta is not None else [])
                assert sub(*args) == 0, (arm, tag)
                row = smoke_row(arm, beta, tag)
                with ctx(arm, 3401):
                    recs.append((read(SRC.BASE / 'probes' / job / 'units' / f'{row["id"]}.json'), read(sidecar_path(row['id'], True))))
            (ra, sa), (rb, sb) = recs
            views = sorted({v['view'] for x in ra['log'] for q in x['query'] for v in q['views']})
            losses = [x['loss'] for x in ra['log']]
            u = {'ids': [ra['row']['id'], rb['row']['id']], 'seconds': ra['seconds'], 'peak_mb': ra['gpu_peak_mb'], 'losses': losses,
                 'losses_finite': all(math.isfinite(x) for x in losses), 'views_in_log': views, 'replay': compare_replay(ra, rb),
                 'history_calls': sa['history_calls'], 'history_min_position_samples': sa['history_min_position_samples'],
                 'pres_calls': sa['pres_calls'], 'pres_trace': sa['pres_trace_every_call'], 'ccs_calls': sa['ccs_calls'],
                 'selection_probe_mean': ra['selection_probe']['mean']}
            receipt['units'][arm] = u
        U = receipt['units']
        assert all(x['losses_finite'] and x['views_in_log'] == ['env', 'sc', 'ss'] for x in U.values())
        assert U['TCS_RES']['history_calls'] > 0 and U['TCS_RES']['history_min_position_samples'] >= 0
        assert U['TCS_CCS']['history_calls'] > 0 and U['TCS_PRES']['pres_calls'] == 6 and U['TCS_RES_PRES']['pres_calls'] == 6
        assert U['TCS_PRES']['history_calls'] == 0 and U['TCS_CTRL']['pres_calls'] == 0 and U['TCS_CCS']['ccs_calls'] == 6
        r1 = read(SRC.OUT / 'source_v1' / 'units' / f"{next(r for r in read(SRC.OUT / 'source_v1' / 'selection.json')['production_rows'] if r['arm'] == 'TCS')['id']}.json")
        receipt['tcs_ctrl_vs_aln41_tcs_update1_loss'] = {'ctrl': U['TCS_CTRL']['losses'][0], 'aln41_tcs_production': r1['log'][0]['loss'],
                                                         'identical': U['TCS_CTRL']['losses'][0] == r1['log'][0]['loss'],
                                                         'abs_diff': abs(U['TCS_CTRL']['losses'][0] - r1['log'][0]['loss']),
                                                         'aln41_device': r1['device']}
        assert len({tuple(x['losses']) for x in U.values()}) == len(U), 'two arms produced identical losses'
        receipt['replay_all_identical'] = all(x['replay']['log_identical'] and x['replay']['checkpoint_tensors_identical'] for x in U.values())
        for arm, beta in (('TCS_CTRL', None), ('TCS_PRES', BETAS[-1]), ('TCS_CCS', None), ('TCS_RES_PRES', BETAS[-1])):
            assert sub('bench', '--arm', arm, *(['--beta', beta] if beta is not None else [])) == 0, ('bench', arm)
        B = {a: read(OUT / 'probes' / job / 'bench' / f'{a}.json') for a in ('TCS_CTRL', 'TCS_PRES', 'TCS_CCS', 'TCS_RES_PRES')}
        ctrl = B['TCS_CTRL']['median_update_seconds']
        receipt['bench'] = {a: {'median_update_seconds': b['median_update_seconds'], 'ratio_to_TCS': b['median_update_seconds'] / ctrl,
                                'peak_mb': b['peak_mb'], 'first_loss': b['first_loss'], 'device': b['device']} for a, b in B.items()}
        worst = max(B['TCS_PRES']['median_update_seconds'], B['TCS_RES_PRES']['median_update_seconds']) / ctrl
        peak = max(B['TCS_PRES']['peak_mb'], B['TCS_RES_PRES']['peak_mb'])
        receipt['F4'] = {'pres_time_ratio_max': worst, 'pres_peak_mb_max': peak, 'thresholds': {'ratio': F4_MAX_RATIO, 'peak_mb': F4_MAX_MB},
                         'cache_fallback_required': bool(worst > F4_MAX_RATIO or peak > F4_MAX_MB)}
        assert not receipt['F4']['cache_fallback_required'], 'F4 exceeded: implement the precomputed P z0 cache before production'
        assert sub('downstream-check') == 0, 'downstream check'
        receipt['downstream_check'] = read(OUT / 'probes' / job / 'downstream_check.json')
        assert receipt['downstream_check']['pass'], 'TCS checkpoint through the W7 path did not reproduce the stored readouts'
        assert receipt['replay_all_identical'], 'same-seed replay not bit-identical'
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', receipt)


def claim(base, uid, fn):
    path = base / 'units' / f'{uid}.json'
    lock = base / 'claims' / f'{uid}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if path.exists():
            return False
        rc = fn()
        if rc < 0:                          # preempted / signalled: no FAILED marker, the unit resumes elsewhere
            raise SystemExit(rc)
        if rc or not path.exists():
            write(base / 'units' / f'{uid}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
            raise RuntimeError(f'W7 unit failed: {uid}')
        return True


def maybe_select():
    if calibration_pending_selection():
        lock = OUT / 'TCS_PRES' / 'select.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            fcntl.flock(h, fcntl.LOCK_EX)
            if calibration_pending_selection():
                print('beta selection', json.dumps(select_beta()['choice']), flush=True)


def worker(max_units, only_calibration=False):
    assert receipts()['pass'], 'no passing W7 smoke'
    maybe_select()
    count = 0
    for arm, seed, row, failed in open_source_units(only_calibration):
        if failed:
            continue
        base = OUT / arm / f'seed{seed}' / 'source_v1'
        if claim(base, row['id'], lambda: sub('unit', '--arm', arm, '--seed', seed, '--id', row['id'])):
            count += 1
        if count >= max_units:
            break
    maybe_select()


def frozen_worker(max_units):
    assert receipts()['pass'], 'no passing W7 smoke'
    count = 0
    for arm, seed, row, failed in open_frozen_units():
        if row is None and not failed:
            with ctx(arm, seed):
                FZ.make_plan()
    for arm, seed, row, failed in open_frozen_units():
        if failed or row is None:
            continue
        base = OUT / arm / f'seed{seed}' / 'frozen_v1'
        if claim(base, row['id'], lambda: sub('frozen-unit', '--arm', arm, '--seed', seed, '--id', row['id'])):
            count += 1
        if count >= max_units:
            break


def readout(arms):
    """CPU: aln41 readout (content / time / attention / private current and history) and aln41 age, per arm x seed with all five
    frozen units complete."""
    argv = sys.argv
    try:
        for arm in arms:
            for seed in SEEDS:
                base, rows = frozen_rows(arm, seed)
                if rows and all((base / 'units' / f'{r["id"]}.json').exists() for r in rows):
                    with ctx(arm, seed):
                        sys.argv = ['readout', '--all-ready']; RO.main()
                        if not (AGE.BASE / 'age_results.json').exists():
                            sys.argv = ['age']; AGE.main()
    finally:
        sys.argv = argv


def status():
    out = {}
    for arm in ARMS:
        for seed in SEEDS:
            base, rows = source_rows(arm, seed); fb, frows = frozen_rows(arm, seed)
            out[f'{arm}/{seed}'] = {'source': f"{sum((base / 'units' / (r['id'] + '.json')).exists() for r in rows)}/{len(rows)}",
                                    'frozen': f"{sum((fb / 'units' / (r['id'] + '.json')).exists() for r in frows)}/{len(frows)}"}
    out['lanes'] = {k: fleet_status(k) for k in LANES}
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('validate-ccs', 'plan', 'prepare', 'smoke', 'smoke-unit', 'bench', 'downstream-check', 'worker',
                                    'select', 'unit', 'frozen-worker', 'frozen-unit', 'readout', 'status'))
    ap.add_argument('--arm'); ap.add_argument('--seed', type=int); ap.add_argument('--id'); ap.add_argument('--probe', action='store_true')
    ap.add_argument('--beta', type=float); ap.add_argument('--tag'); ap.add_argument('--max-units', type=int, default=1)
    ap.add_argument('--only-calibration', action='store_true'); ap.add_argument('--h-mult', type=float)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.cmd == 'validate-ccs':
        validate_ccs(*OBJ.CCS_VALIDATION)
    elif a.cmd == 'plan':
        plans(); status()
    elif a.cmd == 'prepare':
        print(json.dumps(prepare(), indent=1)[:4000])
    elif a.cmd == 'smoke':
        smoke()
    elif a.cmd == 'smoke-unit':
        run_smoke_unit(a.arm, a.beta, a.tag)
    elif a.cmd == 'bench':
        bench(a.arm, a.beta)
    elif a.cmd == 'downstream-check':
        downstream_check()
    elif a.cmd == 'worker':
        worker(a.max_units, a.only_calibration)
    elif a.cmd == 'select':
        maybe_select()
    elif a.cmd == 'unit':
        run_one(a.arm, a.seed, a.id, a.probe)
    elif a.cmd == 'frozen-worker':
        frozen_worker(a.max_units)
    elif a.cmd == 'frozen-unit':
        run_frozen(a.arm, a.seed, a.id)
    elif a.cmd == 'readout':
        readout([a.arm] if a.arm else ARMS)
    else:
        status()


if __name__ == '__main__':
    main()
