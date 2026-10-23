"""W7 GPU training arms, version 2 (APPENDUM_04): identical to paper/w7_arms.py (v1, byte-bound by smoke 1058008 and left
unchanged) except (a) PRES uses per-slot L2-normalised P z_theta / P z0 with its bandwidth from the median rule on the
L2-normalised fit-panel features, (b) records / checkpoints under w7_v1/arms_v2 (v1 fixed quantities and the CCS validation
receipt are reused read-only), (c) the v2 smoke re-runs only the PRES / RES_PRES probes (plus the TCS control pair, F4 and a
determinism diagnostic) and takes the RES / CCS probes and the downstream check from the v1 smoke, (d) the replay gate follows
APPENDUM_04 (bitwise differences are inherited when the plain-TCS control also differs).

W7 GPU training arms (frozen design docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md sections 2.3-2.5,
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
V1 = W7 / 'arms'                                       # v1 records: fixed_v1, ccs_validation, smoke 1058008 (read-only here)
V1_SMOKE = '1058008'
OUT = W7 / 'arms_v2'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/paper/w7_v1/arms_v2')
FIXED = V1 / 'fixed_v1'                                # history map, sigma_h, sigma_res, PCA P (v1, reused unchanged)
FIXED_V2 = OUT / 'fixed_v2'                            # PRES bandwidth on L2-normalised P z0 (APPENDUM_04)
DESIGN = Path(core.REPO) / 'docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md'
DESIGN_SHA = 'c4b461b0a6754af0ba04720320b0acc3f8c907a37f90369a4a250a612a92746c'
FAMILIES = Path(core.REPO) / 'results/auditory_alignment_v3/paper/w7/W7_FAMILIES_v1.json'
FAMILIES_SHA = 'a95aa35f0f47733f9b1ad57427bd1cc477056459c6555c94cb980fb730982421'
F4_MAX_MB, F4_MAX_RATIO = 40 * 1024, 3.0
LANES = {'A': ('c3_s35pw7v2A', 's35_paper_w7v2_src_a', 'slurm/aln35_paper_w7v2_src_a.sbatch'),
         'B': ('c3_s35pw7v2B', 's35_paper_w7v2_src_b', 'slurm/aln35_paper_w7v2_src_b.sbatch'),
         'Z': ('c3_s35pw7v2Z', 's35_paper_w7v2_frozen', 'slurm/aln35_paper_w7v2_frozen.sbatch')}
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest
_ORIGINAL = {'Source': SRC.Source, 'view_batches': SRC.view_batches, 'build_model': SRC.build_model}
STATE: dict = {}
FIX: dict = {}


def w7_sources():
    here = Path(__file__).parent
    return {str(p.relative_to(core.REPO)): sha(p) for p in (here / 'w7_arms_v2.py', here / 'w7_objectives.py')}


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
    return pres_dependence_l2(zt, z0, pca, FIX['sigma_pres'])


def pres_dependence_l2(z_theta, z0, pca, sigma):
    """APPENDUM_04: mean over slots of I_CS(L2(P z_theta^k) ; L2(P z0^k)), cs_qmi_reference, one fixed bandwidth."""
    import torch
    import torch.nn.functional as F
    from ..aln41.cs_qmi_reference import cs_qmi
    if z0.requires_grad or z0.grad_fn is not None:
        raise AssertionError('PRES: z0 must not carry a gradient')
    assert z_theta.shape == z0.shape and z_theta.ndim == 3
    vals, stats = [], []
    for k in range(z_theta.shape[1]):
        a = F.normalize(OBJ.pca_project(z_theta[:, k].float(), pca), dim=-1)
        b = F.normalize(OBJ.pca_project(z0[:, k].float(), pca), dim=-1)
        v, st = cs_qmi(a, b, sigma_u=sigma, sigma_v=sigma)
        vals.append(v); stats.append(st['cs_qmi_nats'])
    value = torch.stack(vals).mean()
    if not bool(torch.isfinite(value)):
        raise FloatingPointError('nonfinite PRES dependence')
    return value, {'pres_cs_qmi_nats': float(value.detach()), 'slot_cs_qmi_nats': stats, 'normalised': 'L2 per slot'}


def load_fixed():
    import torch
    f = read(FIXED / 'fixed.json'); f2 = read(FIXED_V2 / 'fixed_pres_l2.json')
    assert sha(FIXED / 'pca_dev.pt') == f['pca_sha256'] == f2['pca_sha256'] and f['hmap']['rows'] == 'source fit panel (role fit) only'
    assert f2['fixed_v1_sha256'] == sha(FIXED / 'fixed.json')
    pca = torch.load(FIXED / 'pca_dev.pt', map_location='cpu')
    return {'hmap': f['hmap'], 'sigma_h': f['sigma_h'], 'sigma_res': f['sigma_res'], 'sigma_pres': f2['sigma_pres_l2'],
            'pca': {k: pca[k].float() for k in ('mu', 'sd', 'components')}, 'sha256': fixed_sha()}


def fixed_sha():
    """v1 fixed quantities + the APPENDUM_04 PRES bandwidth."""
    return digest({'fixed_v1': sha(FIXED / 'fixed.json'), 'fixed_pres_l2': sha(FIXED_V2 / 'fixed_pres_l2.json')})


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
    """v1 fixed quantities (history map, sigma_h, sigma_res, PCA P; written by smoke 1058008) are reused read-only. APPENDUM_04
    adds the PRES bandwidth on the L2-normalised projected B0 tokens of the source fit panel (median rule, pooled over the three
    slots, the TCS sigma_u rule), written once (0444) before any v2 PRES unit, with a descriptive initial-state characterisation."""
    import torch
    import torch.nn.functional as F
    from ..aln41.cs_qmi_reference import cs_qmi
    if (FIXED_V2 / 'fixed_pres_l2.json').exists():
        return read(FIXED_V2 / 'fixed_pres_l2.json')
    check_frozen_design(); assert 'APPENDUM_04.md' in appenda(), 'APPENDUM_04 must be frozen first'
    f1 = read(FIXED / 'fixed.json'); assert sha(FIXED / 'pca_dev.pt') == f1['pca_sha256']
    assert (FIXED / 'fixed.json').stat().st_mode & 0o222 == 0
    dev = torch.device('cuda')
    base0, store0, plan0, _ = seed_source(3401)
    man = SRC.open_manifest(); P = SRC.load_arrays(store0 / 'panels.npz'); assert sha(store0 / 'panels.npz') == f1['panels_sha256']
    src = SRC.Source(man, P['fit_rows'], dev)
    model, _ = SRC.build_model(dev)
    init = SRC.state_digest(model); assert init == f1['stage1_initial_state_sha256']
    _, _, Tf, _ = SRC.panel_features(src, model, P['fit_rows'], P['fit_off'])
    Tf = Tf.reshape(len(Tf), 3, -1)
    pca = torch.load(FIXED / 'pca_dev.pt', map_location='cpu'); proj = {k: pca[k].float() for k in ('mu', 'sd', 'components')}
    Pz = torch.stack([OBJ.pca_project(Tf[:, k].float(), proj) for k in range(3)], 1).double()
    Zn = F.normalize(Pz, dim=-1)
    sigma = OBJ.pooled_slot_sigma(Zn)
    g = torch.Generator().manual_seed(3401); sd = float(Pz.std())
    char = {'identity': [], 'scale_1.2': [], 'noise_0.3sd': [], 'noise_1.0sd': []}
    for b in range(16):
        for k in range(3):
            z = Pz[b * 32:(b + 1) * 32, k]; ref = F.normalize(z, dim=-1)
            for key, other in (('identity', z), ('scale_1.2', 1.2 * z),
                               ('noise_0.3sd', z + .3 * sd * torch.randn(z.shape, generator=g, dtype=torch.float64)),
                               ('noise_1.0sd', z + 1.0 * sd * torch.randn(z.shape, generator=g, dtype=torch.float64))):
                char[key].append(float(cs_qmi(F.normalize(other, dim=-1), ref, sigma_u=sigma, sigma_v=sigma)[0]))
    body = {'version': 'W7_FIXED_PRES_L2_v1', 'appendum': 'APPENDUM_04', 'appenda': appenda(), 'w7_sources': w7_sources(),
            'fixed_v1_sha256': sha(FIXED / 'fixed.json'), 'pca_sha256': f1['pca_sha256'], 'panels_sha256': f1['panels_sha256'],
            'stage1_initial_state_sha256': init, 'sigma_pres_l2': sigma, 'sigma_pres_v1_unnormalised': f1['sigma_pres'],
            'rule': 'lower median of within-slot distinct-anchor distances of L2(P z0), source fit panel (512 anchors), pooled over 3 slots',
            'initial_state_characterisation': {k: {'mean': float(np.mean(v)), 'min': float(np.min(v)), 'max': float(np.max(v))}
                                               for k, v in char.items()},
            'characterisation_note': 'I_CS(L2(P z), L2(P z0)) at the initial state, 16 fit-panel batches of 32 x 3 slots; descriptive only',
            'device': torch.cuda.get_device_name(0), 'job': os.environ.get('SLURM_JOB_ID'), 'created': datetime.now().astimezone().isoformat()}
    write(FIXED_V2 / 'fixed_pres_l2.json', body); (FIXED_V2 / 'fixed_pres_l2.json').chmod(0o444)
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
    assert (FIXED / 'fixed.json').exists() and (FIXED_V2 / 'fixed_pres_l2.json').exists(), 'run prepare first'
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
    for p in sorted((V1 / 'ccs_validation').glob('*/receipt.json')):
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
    raise RuntimeError('v2 reuses the v1 CCS validation receipt (w7_objectives.py unchanged); run paper.w7_arms validate-ccs')
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


def replay_magnitude(a, b):
    """Two runs of the same 3-update probe: bitwise equality and the size of any difference (log and final checkpoint)."""
    import torch
    la, lb = a['log'], b['log']
    dl = max(abs(x['loss'] - y['loss']) for x, y in zip(la, lb)); dg = max(abs(x['grad_norm'] - y['grad_norm']) for x, y in zip(la, lb))
    dd = max(abs(u - v) for x, y in zip(la, lb) for p, q in zip(x['delta'], y['delta']) for u, v in zip(p, q))
    ca = torch.load(a['final_checkpoint'], map_location='cpu', weights_only=False)
    cb = torch.load(b['final_checkpoint'], map_location='cpu', weights_only=False)
    pairs = [(f'{k}.{n}', ca[k][n].double(), cb[k][n].double()) for k in ('backbone', 'heads') for n in ca[k]] + [('a', ca['a'].double(), cb['a'].double())]
    diffs = {n: float((x - y).abs().max()) for n, x, y in pairs if x.numel()}
    rel = {n: diffs[n] / max(float(x.abs().max()), 1e-30) for n, x, _ in pairs if x.numel()}
    worst = sorted(diffs, key=lambda n: -rel[n])[:5]
    return {'log_identical': dl == 0 and dg == 0 and dd == 0, 'checkpoint_tensors_identical': all(v == 0 for v in diffs.values()),
            'max_abs_loss_diff': dl, 'max_abs_grad_norm_diff': dg, 'max_abs_delta_diff': dd,
            'max_abs_param_diff': max(diffs.values()), 'max_rel_param_diff': max(rel.values()),
            'n_tensors_differing': sum(v > 0 for v in diffs.values()), 'n_tensors': len(diffs),
            'worst_tensors_rel': {n: rel[n] for n in worst},
            'selection_probe_mean_diff': abs(a['selection_probe']['mean'] - b['selection_probe']['mean'])}


def downstream_cpu():
    """APPENDUM_04: readout + age of the v1 downstream-check frozen units (the stored seed-3401 TCS checkpoint through the W7
    re-pointed frozen path, arrays bit-identical to the stored ones) recomputed as production runs readouts -- a CPU step -- and
    compared exactly (every JSON value) with the stored ALN4.1 TCS readout units and the stored TCS age result. No writes but
    this receipt."""
    from auditory_alignment import data
    from ..aln41 import age_probe as AP
    job = os.environ['SLURM_JOB_ID'] + '.' + os.environ.get('SLURM_STEP_ID', 'batch'); out = {'job': job, 'cohorts': {}}
    check = read(V1 / 'probes' / V1_SMOKE / 'downstream_check.json'); assert check['arrays_bit_identical']
    saved = (FZ.BASE, FZ.STORE, FZ.ARMS, RO.BASE)
    try:
        FZ.BASE, FZ.STORE, FZ.ARMS = V1 / 'downstream_check' / V1_SMOKE / 'frozen_v1', STORE.parent / 'arms' / 'downstream_check' / V1_SMOKE / 'frozen_v1', ('TCS',)
        RO.BASE = OUT / 'downstream_cpu_unused'
        plan = read(FZ.BASE / 'plan.json')
        for ds, cf in (('private_bdf', None), ('fau', 0)):
            row = next(r for r in plan['rows'] if r['dataset'] == ds and r['content_fold'] == cf)
            res = RO.private(row) if ds == 'private_bdf' else RO.public(row)
            st = read(SRC.OUT / 'readout_v1' / 'units' / f'{row["id"]}.json')
            out['cohorts'][f'{ds}/{cf}'] = {'row': row['id'], 'readout_identical': json_equal(res['people'], st['people']) and json_equal(res['q0'], st['q0'])}
        kids = data.load_private()
        ids = np.array([k['id'] for k in kids]); folds = np.array([str(k['fold']) for k in kids])
        age = np.array([np.nan if k.get('age_months') is None else float(k['age_months']) for k in kids])
        row = next(r for r in plan['rows'] if r['dataset'] == 'private_bdf'); u = read(FZ.BASE / 'units' / f'{row["id"]}.json')
        with np.load(Path(u['dest']) / 'arrays.npz', allow_pickle=False) as z:
            X = z['age_features'].reshape(len(kids), -1)
        res = {'status': 'COMPLETE_VALID', 'frozen_unit': row['id'], **AP.run_probe(X, age, ids, folds)}
        out['age_identical'] = json_equal(res, read(SRC.OUT / 'age_v1' / 'age_results.json')['arms']['TCS'])
    finally:
        FZ.BASE, FZ.STORE, FZ.ARMS, RO.BASE = saved
    out['pass'] = bool(all(c['readout_identical'] for c in out['cohorts'].values()) and out['age_identical'])
    out['threads'] = os.environ.get('OMP_NUM_THREADS'); out['w7_sources'] = w7_sources()
    write(OUT / 'downstream_cpu' / job / 'receipt.json', out)
    print(json.dumps(out), flush=True)
    return out


def latest_downstream_cpu():
    c = [(p, read(p)) for p in sorted((OUT / 'downstream_cpu').glob('*/receipt.json'))]
    c = [x for x in c if x[1].get('w7_sources') == w7_sources()]
    return c[-1] if c else None


def nondeterminism_probe():
    """Where a same-seed replay can differ in the unchanged ALN4.1 path: the plain TCS episode of update 0 (person 0) is
    evaluated twice from the same state and RNG seed (train mode, as in run_unit): forward tokens, the loss and every parameter
    gradient compared bitwise; plus the isolated reference cdist backward. Determinism settings are not changed."""
    import torch
    job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda'); out = {}
    with ctx('TCS_CTRL', 3401):
        sig = read(SRC.sigmas_path())['sigmas']; stream = SRC.load_arrays(SRC.STORE / 'stream.npz'); man = SRC.open_manifest()
        src = SRC.Source(man, stream['rows'][:1].reshape(-1), dev); model, a = SRC.build_model(dev)
        kw = {k: SRC.INNER[k] for k in ('steps', 'step_size', 'delta_l2', 'prior_kl_weight', 'temperature')}
        S, Q = stream['rows'][0, 0]; oS, oQ = stream['off'][0, 0]
        runs = []
        for rep_ in range(2):
            torch.manual_seed(12345); model.zero_grad(set_to_none=True); a.grad = None; model.train()
            AS, _ = src.audio(S, oS); AQ, _ = src.audio(Q, oQ)
            with torch.no_grad():
                US, _ = model(src.crops(S, oS))
            UQ, tok = model(src.crops(Q, oQ))
            sv = SRC.view_batches({v: x.detach() for v, x in US.items()}, AS, sig); qv = SRC.view_batches(UQ, AQ, sig)
            loss, _ = TO.episode_loss_fo('TCS_CTRL', sv, qv, a, **kw)
            loss.backward()
            runs.append({'tok': tok.detach().clone(), 'loss': float(loss.detach()),
                         'grads': {n: p.grad.detach().clone() for n, p in model.named_parameters() if p.grad is not None}})
        r0, r1 = runs
        gd = {n: float((r0['grads'][n] - r1['grads'][n]).abs().max()) for n in r0['grads']}
        diff_names = [n for n, v in gd.items() if v > 0]
        out['forward_tokens_identical'] = bool(torch.equal(r0['tok'], r1['tok']))
        out['loss_identical'] = r0['loss'] == r1['loss']; out['loss_abs_diff'] = abs(r0['loss'] - r1['loss'])
        out['grad_tensors_differing'] = len(diff_names); out['grad_tensors'] = len(gd)
        out['grad_max_abs_diff'] = max(gd.values())
        groups = {}
        for n in diff_names:
            key = '.'.join(n.split('.')[:4]); groups[key] = max(groups.get(key, 0.0), gd[n])
        out['differing_gradient_groups_max_abs'] = dict(sorted(groups.items(), key=lambda kv: -kv[1])[:12])
        x = torch.randn(32, 32, device=dev, dtype=torch.float64, generator=torch.Generator(device=dev).manual_seed(1))
        gs = []
        for _ in range(2):
            y = x.clone().requires_grad_(True)
            d = torch.cdist(y, y, p=2, compute_mode='donot_use_mm_for_euclid_dist')
            (d.square() * torch.linspace(0, 1, 1024, device=dev, dtype=torch.float64).reshape(32, 32)).sum().backward(); gs.append(y.grad.clone())
        out['cdist_backward_identical'] = bool(torch.equal(gs[0], gs[1])); out['cdist_backward_max_abs_diff'] = float((gs[0] - gs[1]).abs().max())
        out['device'] = torch.cuda.get_device_name(0)
        out['deterministic_algorithms_enabled'] = torch.are_deterministic_algorithms_enabled()
        out['cudnn_deterministic'] = torch.backends.cudnn.deterministic; out['cudnn_benchmark'] = torch.backends.cudnn.benchmark
    write(OUT / 'probes' / job / 'nondeterminism_probe.json', out)
    return out


def smoke():
    """APPENDUM_04 smoke: the PRES / RES_PRES probes (twice each) and the plain-TCS control pair under v2, GPU (v), F4 and a
    determinism diagnostic; the RES / CCS probes, the downstream check and the v1 F4 come from the v1 smoke 1058008."""
    import torch
    job = os.environ['SLURM_JOB_ID']
    receipt = {'status': 'running', 'w7_sources': w7_sources(), 'job': job, 'units': {}}
    try:
        check_frozen_design(); receipt['appenda'] = appenda(); assert 'APPENDUM_04.md' in receipt['appenda']
        vp, vr = latest_validation()
        assert vr is not None and vr['status'] == 'pass', 'CCS validation (APPENDUM_03) not passed'
        receipt['ccs_validation'] = {'receipt': str(vp), 'sha256': sha(vp), 'gate': vr['gate']}
        v1p = V1 / 'probes' / V1_SMOKE / 'receipt.json'; v1 = read(v1p)
        tb = v1.get('traceback', '')
        # v1 stopped at its downstream assertion (readout / age on the 12-thread GPU node differ from the stored CPU-step values
        # at <= 1e-13 while the frozen arrays are bit-identical); APPENDUM_04: the readout reproduction is checked as production
        # runs it, as a CPU step (receipt below). Its last two checks (downstream, replay) are re-evaluated here.
        assert v1['status'] == 'failed' and 'did not reproduce the stored readouts' in tb, 'v1 smoke failed elsewhere'
        assert v1['ccs_v_gpu']['pass'] and not v1['F4']['cache_fallback_required'] and v1['downstream_check']['arrays_bit_identical']
        cpu = latest_downstream_cpu()
        assert cpu is not None and cpu[1]['pass'], 'CPU-step downstream reproduction receipt missing or failed'
        receipt['downstream_cpu'] = {'receipt': str(cpu[0]), 'sha256': sha(cpu[0]), **cpu[1]}
        receipt['v1_smoke'] = {'receipt': str(v1p), 'sha256': sha(v1p), 'status': v1['status'], 'failed_assertion': tb.strip().splitlines()[-1] if tb else None,
                               'ccs_v_gpu': v1['ccs_v_gpu'], 'downstream_check_gpu_node': v1['downstream_check'], 'F4_v1_pres_definition': v1['F4'],
                               'bench_v1_pres_definition': v1['bench'], 'replay_all_identical_v1': v1['replay_all_identical'],
                               'tcs_ctrl_vs_aln41_tcs_update1_loss': v1.get('tcs_ctrl_vs_aln41_tcs_update1_loss'), 'fixed_v1': v1['fixed']}
        v1rep = {}
        for arm in ('TCS_CTRL', 'TCS_RES', 'TCS_CCS'):
            recs = []
            for tag in ('a', 'b'):
                row = smoke_row(arm, None, tag)
                base = V1 / arm / 'seed3401' / 'source_v1'
                recs.append((read(base / 'probes' / V1_SMOKE / 'units' / f'{row["id"]}.json'), read(base / 'probes' / V1_SMOKE / 'w7' / f'{row["id"]}.json')))
            u = v1['units'][arm]
            assert u['losses_finite'] and u['views_in_log'] == ['env', 'sc', 'ss']
            v1rep[arm] = {'losses': u['losses'], 'history_calls': u['history_calls'], 'ccs_calls': u['ccs_calls'],
                          'history_min_position_samples': u['history_min_position_samples'], 'replay': replay_magnitude(recs[0][0], recs[1][0])}
        assert v1rep['TCS_RES']['history_calls'] > 0 and v1rep['TCS_CCS']['ccs_calls'] == 6
        receipt['v1_units_reused'] = v1rep
        receipt['ccs_v_gpu'] = OBJ.objective_step_timing(torch.device('cuda'))
        assert receipt['ccs_v_gpu']['pass'], 'CCS gate (v) on this GPU'
        fixed2 = prepare(); receipt['fixed_pres_l2'] = {'sha256': sha(FIXED_V2 / 'fixed_pres_l2.json'), 'sigma_pres_l2': fixed2['sigma_pres_l2'],
                                                         'initial_state_characterisation': fixed2['initial_state_characterisation']}
        plans()
        for arm, beta in (('TCS_CTRL', None), ('TCS_PRES', BETAS[0]), ('TCS_RES_PRES', BETAS[0])):
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
            receipt['units'][arm] = {'ids': [ra['row']['id'], rb['row']['id']], 'seconds': ra['seconds'], 'peak_mb': ra['gpu_peak_mb'], 'losses': losses,
                                     'losses_finite': all(math.isfinite(x) for x in losses), 'views_in_log': views,
                                     'replay': replay_magnitude(ra, rb), 'history_calls': sa['history_calls'], 'pres_calls': sa['pres_calls'],
                                     'ccs_calls': sa['ccs_calls'], 'pres_trace': sa['pres_trace_every_call'],
                                     'selection_probe_mean': ra['selection_probe']['mean'], 'device': ra['device']}
        U = receipt['units']
        assert all(x['losses_finite'] and x['views_in_log'] == ['env', 'sc', 'ss'] for x in U.values())
        assert U['TCS_PRES']['pres_calls'] == 6 and U['TCS_RES_PRES']['pres_calls'] == 6 and U['TCS_CTRL']['pres_calls'] == 0
        assert U['TCS_RES_PRES']['history_calls'] > 0 and U['TCS_PRES']['history_calls'] == 0
        assert len({tuple(x['losses']) for x in U.values()}) == len(U)
        assert sub('nondet') == 0, 'nondeterminism probe'
        receipt['nondeterminism_probe'] = read(OUT / 'probes' / job / 'nondeterminism_probe.json')
        for arm, beta in (('TCS_CTRL', None), ('TCS_PRES', BETAS[-1]), ('TCS_RES_PRES', BETAS[-1])):
            assert sub('bench', '--arm', arm, *(['--beta', beta] if beta is not None else [])) == 0, ('bench', arm)
        B = {a_: read(OUT / 'probes' / job / 'bench' / f'{a_}.json') for a_ in ('TCS_CTRL', 'TCS_PRES', 'TCS_RES_PRES')}
        ctrl = B['TCS_CTRL']['median_update_seconds']
        receipt['bench'] = {a_: {'median_update_seconds': b['median_update_seconds'], 'ratio_to_TCS': b['median_update_seconds'] / ctrl,
                                 'peak_mb': b['peak_mb'], 'first_loss': b['first_loss'], 'device': b['device']} for a_, b in B.items()}
        worst = max(B['TCS_PRES']['median_update_seconds'], B['TCS_RES_PRES']['median_update_seconds']) / ctrl
        peak = max(B['TCS_PRES']['peak_mb'], B['TCS_RES_PRES']['peak_mb'])
        receipt['F4'] = {'pres_time_ratio_max': worst, 'pres_peak_mb_max': peak, 'thresholds': {'ratio': F4_MAX_RATIO, 'peak_mb': F4_MAX_MB},
                         'cache_fallback_required': bool(worst > F4_MAX_RATIO or peak > F4_MAX_MB)}
        assert not receipt['F4']['cache_fallback_required'], 'F4 exceeded: implement the precomputed P z0 cache before production'
        # APPENDUM_04 replay rule: a new arm's bitwise difference is a bug unless the plain-TCS control also differs in the same job
        ctrl_differs = not (U['TCS_CTRL']['replay']['log_identical'] and U['TCS_CTRL']['replay']['checkpoint_tensors_identical'])
        new_differ = {a_: not (U[a_]['replay']['log_identical'] and U[a_]['replay']['checkpoint_tensors_identical']) for a_ in ('TCS_PRES', 'TCS_RES_PRES')}
        v1_ctrl_differs = not (v1rep['TCS_CTRL']['replay']['log_identical'] and v1rep['TCS_CTRL']['replay']['checkpoint_tensors_identical'])
        v1_new_differ = {a_: not (v1rep[a_]['replay']['log_identical'] and v1rep[a_]['replay']['checkpoint_tensors_identical']) for a_ in ('TCS_RES', 'TCS_CCS')}
        receipt['replay_rule'] = {'control_differs_v2_job': ctrl_differs, 'new_arms_differ_v2_job': new_differ,
                                  'control_differs_v1_job': v1_ctrl_differs, 'new_arms_differ_v1_job': v1_new_differ,
                                  'inherited': bool((ctrl_differs or not any(new_differ.values())) and (v1_ctrl_differs or not any(v1_new_differ.values())))}
        assert receipt['replay_rule']['inherited'], 'a new arm differs on replay while the plain-TCS control replays bitwise: bug'
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
                                    'select', 'unit', 'frozen-worker', 'frozen-unit', 'readout', 'status', 'nondet', 'downstream-cpu'))
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
    elif a.cmd == 'nondet':
        nondeterminism_probe()
    elif a.cmd == 'downstream-cpu':
        downstream_cpu()
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
