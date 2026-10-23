"""Paper line: mechanistic shortcut audit of the COMPLETE released MindMix system (official code @98445f36, official EEGEncoder,
wav2vec2-base, create_model('multimodal_real', 'calra'), released fusion checkpoint via aln42.external_mindmix.build_model),
before fine-tuning (released weights) and after the official fine-tune (the per-unit final_model.pt of the 10 DTU units of
aln42/external_mindmix.py and the 10 FAU units of paper/mindmix_fau.py). Zero optimiser updates.

Frozen protocol: private/auditory_alignment_v3/paper/mindmix_dropkey_v1/PROTOCOL.md (0444, frozen before any audit output; its
sha256 is bound in plan.json and in every unit record). Post-hoc; outside the frozen ALN4.2 external binding and the Table 2
scoring of record (both unchanged).

Question. W5 (MindMix recipe on CBraMod) met its ClipLoss through a shared dropout key: one CALRA(e_i, a_i) call per row shares
its dropout noise between fused_eeg_i and aligned_audio_i. Does the complete system do the same (H_dk), or is its objective met
by a deterministic shared-input key (H_ak: both outputs of one CALRA call are functions of the same audio a_i), or both?

Stochastic layers of the official model in train mode (the only train/eval difference; no BatchNorm):
  CALRA dropout p = 0.1 at 9 sites per call (universal_models.py:151, 157, 172, 178, 179, 180, 182, 183, 184); sites 151/157/172
  reach BOTH outputs (through H = U_e * U_a, :171-175); EEGEncoder DropPath 0..0.1 per sample (universal_eeg_finetune.py:115,
  modeling_finetune_2.py:183, 199-208, 294); wav2vec2-base dropouts 0.1 (feature projection, attention, hidden) and SpecAugment
  time masks (p 0.05 x 10 frames, >= 2 per row, numpy RNG); layerdrop 0. eeg_proj / audio_proj / ClipLoss carry none.

Per unit (one DTU or FAU fine-tuned unit) and per model (released, then fine-tuned; same blocks): person-homogeneous blocks of
B = 32 windows; 'train' = the first N_TRAIN_BLOCKS full batches of the unit's official epoch-0 loader order (the unit's training
windows), 'test' = the first N_TEST_PER_PERSON full consecutive (segment, sub-window) blocks of each test person. Inputs are the
bound ones (external_mindmix.Inputs / mindmix_fau.Inputs). Per block, P = the half-batch roll (P[i] = (i + B/2) mod B):
  inputs   RA real EEG + attended; NA Gaussian EEG matched per window x channel (mean, SD) + attended; RU real + unattended;
           RO real + attended audio of row P[i] (another window, almost always another segment); ID row 0's EEG and attended
           audio repeated over all B rows.
  A  joint pairing (the training forward model(e, a, mode='clip_train') -> ClipLoss), modes train (model.train()) and eval,
     inputs RA NA RU RO ID; plus pre-fusion ClipLoss(eeg_proj(.), audio_proj(.)) for RA.
  B  scorers per window, train and eval: official = universal_trainer._evaluate_contrastive structure (forward_contrastive, pA >
     pB) with target = attended, target = unattended, and noise EEG (target attended); official_split = the same with the target
     re-fused in a separate CALRA call (fe = CALRA(x, t)[0], ft = CALRA(x, t)[1] from two calls); blind = external_mindmix.
     blind_margin(e, attended, unattended) for real and noise EEG.
  C  coupling, mode train, inputs RA NA ID: splitC = encoders once, f and g from two CALRA calls; splitAll = f and g from two
     complete forward passes (every stochastic draw independent; marginals unchanged).
  D  partition, joint pairing, inputs RA ID: only CALRA stochastic (C), only EEG encoder (E), only wav2vec2 (A); C + splitC;
     P0C = train mode with CALRA dropout p = 0 (option b); P0ALL = train mode with every stochastic layer zeroed (identification
     check against eval, recorded).
  E  manual CALRA masks (Bernoulli 0.9 / 0.9 at all 9 sites, forced irrespective of the module mode; encoders eval or train,
     CALRA eval): mjoint = one call; replay = a second call reusing the recorded masks (asserted identical to mjoint); mindep = a
     second call with fresh masks; mtransplant (RA) = a second call reusing the masks with rows permuted by P, so the mask of row
     i is shared by f_i and g_{P^-1(i)}: retrieval follows the mask or the content.
  F  deterministic transplant, eval, RA: f from CALRA(x, y[P]) (audio transplant) or CALRA(x[P], y) (EEG transplant), g from
     CALRA(x, y): retrieval follows the transplanted audio / EEG or the diagonal.
Block metrics: ClipLoss toward the diagonal (ce), in-batch top-1, mean diagonal-minus-off-diagonal logit (gap), mean row logit
spread, mean off-diagonal cosine of f / g (joint conditions); transplant conditions add ce / top-1 / gap toward the follow target.
Unit records carry engineering checks only; the aggregates are written by --summarize (CPU) after every unit is complete.

CLI: --make-plan (CPU) | --selftest (CPU or GPU; synthetic inputs, no data, no writes) | --smoke | --worker | --unit ID |
--probe-unit ID (GPU) | --summarize (CPU).
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from . import ext_common as XC
from ..aln42 import external_mindmix as XM

OUT = Path(core.OUT) / 'paper' / 'mindmix_dropkey_v1'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/paper/mindmix_dropkey_v1')
RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/paper/mindmix_audit'
RESULT_FILE = RESULTS / 'MINDMIX_DROPKEY_AUDIT.json'
PROTOCOL = OUT / 'PROTOCOL.md'
NAME, LANE, SBATCH = 'c3_s35pmmdk', 's35_paper_mmdropkey', 'slurm/aln35_paper_mmdropkey.sbatch'
BATCH = XM.BATCH                                    # 32
N_TRAIN_BLOCKS, N_TEST_PER_PERSON, SMOKE_BLOCKS = 12, 2, 2
RNG_SEED = XM.SEED + 500
P_DROP, CALRA_SITES = 0.1, 9
TAGS, DOMS = ('released', 'finetuned'), ('train', 'test')
LN_B = math.log(BATCH)
read, write, sha, digest = XM.read, XM.write, XM.sha, XM.digest


# ----------------------------------------------------------------------------------------------------------- plan
def mf():
    from . import mindmix_fau as MF
    return MF


def sources():
    repo = Path(core.REPO)
    files = [Path(__file__), repo / 'auditory_alignment_v3/aln42/external_mindmix.py', repo / 'auditory_alignment_v3/paper/mindmix_fau.py',
             repo / 'auditory_alignment_v3/paper/ext_common.py']
    out = {str(p.relative_to(repo)): sha(p) for p in files}
    out.update({f'mindmix@{XM.MM_COMMIT[:8]}/{f}': sha(XM.MM_REPO / f) for f in XM.MM_FILES})
    return out


def bound_record(ds, uid):
    base = XM.OUT if ds == 'dtu' else mf().OUT
    return base / 'units' / f'{uid}.json'


def plan_rows():
    rows = []
    for ds, plan_path in (('dtu', XM.OUT / 'plan.json'), ('fau', mf().OUT / 'plan.json')):
        for r in read(plan_path)['rows']:
            p = bound_record(ds, r['id']); rec = read(p)
            assert rec['status'] == 'complete' and not rec['probe'] and rec['final_model_sha256'], r['id']
            assert (Path(rec['dest']) / 'final_model.pt').exists(), r['id']
            body = {'dataset': ds, 'unit': r['id'], 'content_fold': r['content_fold'], 'person_fold': r['person_fold']}
            rows.append({**body, 'id': 'MMDK_' + digest(body, 16), 'bound_record_sha256': sha(p), 'final_model_sha256': rec['final_model_sha256'],
                         'bound_dest': rec['dest']})
    for k, r in enumerate(rows):
        r['index'] = k
    return rows


def make_plan():
    assert PROTOCOL.exists() and not (PROTOCOL.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)), 'protocol not frozen (0444)'
    body = {'version': 'PAPER_MINDMIX_DROPKEY_AUDIT_v1', 'protocol_sha256': sha(PROTOCOL), 'sources': sources(), 'rows': plan_rows(),
            'production_plans': {'dtu': sha(XM.OUT / 'plan.json'), 'fau': sha(mf().OUT / 'plan.json')},
            'checkpoint_sha256': XM.CKPT_SHA, 'mindmix_commit': XM.MM_COMMIT, 'wav2vec2_revision': XM.W2V_REV,
            'settings': {'batch': BATCH, 'n_train_blocks': N_TRAIN_BLOCKS, 'n_test_blocks_per_person': N_TEST_PER_PERSON,
                         'smoke_blocks': SMOKE_BLOCKS, 'rng_seed': RNG_SEED, 'calra_dropout': P_DROP, 'calra_sites': CALRA_SITES,
                         'models': list(TAGS), 'domains': list(DOMS), 'roll': 'P[i] = (i + B // 2) mod B'},
            'store': str(STORE)}
    path = OUT / 'plan.json'
    if path.exists():
        old = read(path); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        assert not (OUT / 'units').exists() and not (OUT / 'probes').exists() and not STORE.exists(), 'audit output exists before the plan'
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
        write(path, {**body, 'created': datetime.now().astimezone().isoformat()}); path.chmod(0o444)
    print('mindmix dropkey plan', sha(path), len(body['rows']), 'protocol', body['protocol_sha256'], flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'dropkey audit source drift'
    assert sha(PROTOCOL) == plan['protocol_sha256'], 'protocol drift'
    for r in plan['rows']:
        assert sha(bound_record(r['dataset'], r['unit'])) == r['bound_record_sha256'], f'bound unit record drift {r["unit"]}'


# ----------------------------------------------------------------------------------------------------------- data
def unit_data(row, probe):
    ds, cf, sf = row['dataset'], row['content_fold'], row['person_fold']
    if ds == 'dtu':
        import h5py
        from auditory_alignment import data as D
        ix = XM.cohort_index(cf); ix['trial_n'] = {}
        for sub in sorted({g['sub'] for g in ix['geo']}):
            with h5py.File(os.path.join(D.DTU_PRE, f'{sub}.h5'), 'r') as f:
                for k in {g['trial'] for g in ix['geo'] if g['sub'] == sub}:
                    ix['trial_n'][(sub, k)] = int(f[k]['eeg_1_20'].shape[1])
        train_p, test_p = XM.unit_people(ix, sf)
        person, role = ix['arrays']['cs_person'], ix['arrays']['cs_role']
        fit_ids = [i for i in range(len(person)) if person[i] in set(train_p) and role[i] == 'fit']
        test_ids = [i for i in range(len(person)) if person[i] in set(test_p) and role[i] == 'test']
        make = lambda ids: XM.Inputs(ix, ids)
    else:
        MF = mf(); cache = XC.Cache('fau'); person, role = cache.arr['cs_person'], cache.role(cf)
        tr_ids, te_ids = cache.scored(cf, sf)
        fit_ids = [int(i) for i in tr_ids if role[i] == 'fit']; test_ids = [int(i) for i in te_ids]
        make = lambda ids: MF.Inputs(cache, ids)
    # official epoch-0 loader order of the unit (external_mindmix.run_unit / mindmix_fau.run_unit loader(ep=0))
    windows = [(i, o) for i in fit_ids for o in XM.SUB_OFFS_S]; owner = np.array([person[i] for i, _ in windows])
    rng = np.random.default_rng([XM.SEED, 0]); batches = []
    for p in sorted(set(owner.tolist())):
        idx = np.flatnonzero(owner == p); idx = idx[rng.permutation(len(idx))]
        batches += [idx[k:k + BATCH] for k in range(0, len(idx), BATCH)]
    order = rng.permutation(len(batches))
    train_blocks = [[windows[j] for j in batches[k]] for k in order if len(batches[k]) == BATCH][:N_TRAIN_BLOCKS]
    test_blocks = []
    for p in sorted({person[i] for i in test_ids}):
        sw = [(i, o) for i in test_ids if person[i] == p for o in XM.SUB_OFFS_S]
        test_blocks += [sw[k:k + BATCH] for k in range(0, len(sw) - BATCH + 1, BATCH)][:N_TEST_PER_PERSON]
    full = {'train': len(train_blocks), 'test': len(test_blocks)}
    if probe:                                        # the probe never touches test windows
        train_blocks, test_blocks = train_blocks[:SMOKE_BLOCKS], []
    seg_ids = sorted({i for blk in train_blocks + test_blocks for i, _ in blk})
    return {'person': person, 'blocks': {'train': train_blocks, 'test': test_blocks}, 'inputs': make(seg_ids), 'full_counts': full}


# ----------------------------------------------------------------------------------------------------------- model helpers
@contextlib.contextmanager
def modes(model, eeg, audio, fusion):
    """Set exactly which stochastic sub-modules are in train mode (eeg_encoder / audio_encoder / fusion_module)."""
    model.eval(); model.eeg_encoder.train(eeg); model.audio_encoder.train(audio); model.fusion_module.train(fusion)
    try:
        yield
    finally:
        model.eval()


ALL, EVAL = (True, True, True), (False, False, False)


@contextlib.contextmanager
def zero_stochastic(root, w2v_config=None):
    """Runtime-only: every dropout p -> 0, DropPath drop_prob -> 0, wav2vec2 attention dropout -> 0 and (if given) SpecAugment
    mask_time_prob -> 0 under `root`; restored on exit. Yields the patched-attribute counts."""
    import torch.nn as nn
    saved, counts = [], {'dropout': 0, 'drop_path': 0, 'attention_dropout': 0, 'spec_augment': 0}
    for m in root.modules():
        if isinstance(m, nn.modules.dropout._DropoutNd):
            saved.append((m, 'p', m.p)); m.p = 0.0; counts['dropout'] += 1
        elif type(m).__name__ == 'DropPath' and hasattr(m, 'drop_prob'):
            saved.append((m, 'drop_prob', m.drop_prob)); m.drop_prob = 0.0; counts['drop_path'] += 1
        elif 'Attention' in type(m).__name__ and isinstance(getattr(m, 'dropout', None), float):
            saved.append((m, 'dropout', m.dropout)); m.dropout = 0.0; counts['attention_dropout'] += 1
    if w2v_config is not None:
        saved.append((w2v_config, 'mask_time_prob', w2v_config.mask_time_prob)); w2v_config.mask_time_prob = 0.0; counts['spec_augment'] += 1
    try:
        yield counts
    finally:
        for obj, attr, v in reversed(saved):
            setattr(obj, attr, v)


class MaskBank:
    """Manual CALRA dropout masks: Bernoulli(1 - p) / (1 - p) per element (the nn.Dropout distribution), drawn from a dedicated
    generator; 'record' draws and keeps them in call order, 'fresh' draws without keeping, 'replay' reuses the recorded masks in
    the same order, optionally with the batch rows permuted."""

    def __init__(self, gen, p=P_DROP):
        self.gen, self.p, self.rec, self.mode, self.k, self.perm = gen, p, [], 'fresh', 0, None

    def apply(self, x):
        import torch
        if self.mode in ('record', 'fresh'):
            m = (torch.rand(x.shape, generator=self.gen, device=x.device) >= self.p).to(x.dtype) / (1 - self.p)
            if self.mode == 'record':
                self.rec.append(m)
        else:
            m = self.rec[self.k]
            if self.perm is not None:
                m = m[self.perm]
        self.k += 1
        return x * m

    def call(self, fm, x, y, mode, perm=None):
        self.mode, self.k, self.perm = mode, 0, perm
        if mode == 'record':
            self.rec = []
        out = fm(x, y)
        assert self.k == CALRA_SITES, f'CALRA dropout sites {self.k} != {CALRA_SITES}'
        return out


@contextlib.contextmanager
def calra_masks(fm, bank):
    """Runtime-only monkeypatch: the forward of each of CALRA's 4 nn.Dropout modules (self.dropout, eeg_ffn[2], audio_ffn[2],
    shared_interaction[2]) is replaced by an instance attribute bank.apply (forced masks, mode-independent); removed on exit."""
    import torch.nn as nn
    mods = [m for m in fm.modules() if isinstance(m, nn.modules.dropout._DropoutNd)]
    assert len(mods) == 4 and all(type(m) is nn.Dropout and m.p == P_DROP for m in mods), mods
    for m in mods:
        m.forward = bank.apply
    try:
        yield
    finally:
        for m in mods:
            del m.forward


def enc(model, e, a):
    """MultimodalRealModel.forward up to the fusion call (universal_models.py:394-405, raw-audio branch)."""
    x = model.eeg_proj(model.eeg_encoder(e))
    y = model.audio_proj(model.audio_encoder(a).last_hidden_state.mean(1))
    return x, y


def official_split(model, e, t, n):
    """forward_contrastive (universal_models.py:428-454) with the target re-fused in its own CALRA call."""
    x = model.eeg_proj(model.eeg_encoder(e))
    xt = model.audio_proj(model.audio_encoder(t).last_hidden_state.mean(1)); xn = model.audio_proj(model.audio_encoder(n).last_hidden_state.mean(1))
    fe, _ = model.fusion_module(x, xt); _, ft = model.fusion_module(x, xt); _, fn = model.fusion_module(x, xn)
    cl = model.clip_loss
    return cl.get_probabilities(fe, ft).diagonal(), cl.get_probabilities(fe, fn).diagonal()


def mets(model, f, g, follow=None, cos=False):
    import torch
    import torch.nn.functional as F
    S = model.clip_loss.get_scores(f, g).double(); n = S.shape[0]; ar = torch.arange(n, device=S.device)
    d = S.diagonal(); off = (S.sum(1) - d) / (n - 1); am = S.argmax(1)
    r = {'ce': F.cross_entropy(S, ar), 'top1': (am == ar).double().mean(), 'gap': (d - off).mean(),
         'spread': (S.max(1).values - S.min(1).values).mean()}
    if follow is not None:
        sf = S[ar, follow]; offf = (S.sum(1) - sf) / (n - 1)
        r.update(ce_follow=F.cross_entropy(S, follow), top1_follow=(am == follow).double().mean(), gap_follow=(sf - offf).mean())
    if cos:
        for k, v in (('fcos', f), ('gcos', g)):
            z = F.normalize(v.double(), dim=-1); C = z @ z.T; r[k] = (C.sum() - C.diagonal().sum()) / (n * (n - 1))
    return {k: float(v) for k, v in r.items()}


def seed_of(base, tag):
    return int(hashlib.sha256(f'{base}|{tag}'.encode()).hexdigest()[:15], 16)


def matched_noise(e, gen):
    import torch
    z = torch.randn(e.shape, generator=gen).to(e.device)
    z = (z - z.mean(-1, keepdim=True)) / (z.std(-1, keepdim=True) + 1e-8)
    return z * e.std(-1, keepdim=True) + e.mean(-1, keepdim=True)


def stochastic_inventory(model):
    import torch.nn as nn
    inv = {}
    for part in ('eeg_encoder', 'audio_encoder', 'eeg_proj', 'audio_proj', 'fusion_module', 'classifier', 'clip_loss'):
        mod = getattr(model, part); d = {'dropout_p': {}, 'drop_path_p': [], 'attention_dropout_p': {}, 'batchnorm': 0}
        for m in mod.modules():
            if isinstance(m, nn.modules.dropout._DropoutNd):
                d['dropout_p'][str(m.p)] = d['dropout_p'].get(str(m.p), 0) + 1
            elif type(m).__name__ == 'DropPath':
                d['drop_path_p'].append(round(float(m.drop_prob), 6))
            elif 'Attention' in type(m).__name__ and isinstance(getattr(m, 'dropout', None), float):
                d['attention_dropout_p'][str(m.dropout)] = d['attention_dropout_p'].get(str(m.dropout), 0) + 1
            if isinstance(m, nn.modules.batchnorm._BatchNorm):
                d['batchnorm'] += 1
        inv[part] = d
    c = model.audio_encoder.config
    inv['spec_augment'] = {'apply': bool(c.apply_spec_augment), 'mask_time_prob': c.mask_time_prob, 'mask_time_length': c.mask_time_length,
                           'mask_time_min_masks': c.mask_time_min_masks, 'mask_feature_prob': c.mask_feature_prob, 'layerdrop': c.layerdrop}
    return inv


# ----------------------------------------------------------------------------------------------------------- one block
def audit_block(model, e, a, u, base, first):
    """All conditions on one block. Returns (block metrics {cond: mets}, window scores {name: array}, checks)."""
    import torch
    fm = model.fusion_module; n = len(e); dev = e.device
    P = (torch.arange(n, device=dev) + n // 2) % n; Pinv = torch.argsort(P)
    en = matched_noise(e, torch.Generator().manual_seed(seed_of(base, 'noise')))
    eI, aI = e[:1].expand_as(e).contiguous(), a[:1].expand_as(a).contiguous()
    inp = {'RA': (e, a), 'NA': (en, a), 'RU': (e, u), 'RO': (e, a[P]), 'ID': (eI, aI)}
    m, w, chk, tm = {}, {}, {}, {}

    def seeded(tag):
        s = seed_of(base, tag); torch.manual_seed(s); np.random.seed(s % 2 ** 32)
    t0 = time.time()
    # A: joint (training) pairing, train vs eval
    for mode, flags in (('train', ALL), ('eval', EVAL)):
        with modes(model, *flags):
            for name, (ee, aa) in inp.items():
                seeded(f'A/{mode}/{name}'); f, g = model(ee, aa, mode='clip_train'); m[f'A_{mode}_joint_{name}'] = mets(model, f, g, cos=True)
            seeded(f'A/{mode}/prefusion'); x, y = enc(model, e, a); m[f'A_{mode}_prefusion_RA'] = mets(model, x, y)
    if first:
        with modes(model, *EVAL):
            f1, g1 = model(e, a, mode='clip_train'); f2, g2 = fm(*enc(model, e, a))
        chk['enc_replica_eval_max_abs'] = float(max((f1 - f2).abs().max(), (g1 - g2).abs().max()))
    tm['A'] = time.time() - t0; t0 = time.time()
    # B: scorers per window, train vs eval
    for mode, flags in (('train', ALL), ('eval', EVAL)):
        with modes(model, *flags):
            for name, (ee, t, ng) in {'att': (e, a, u), 'ign': (e, u, a), 'noise': (en, a, u)}.items():
                seeded(f'B/{mode}/official/{name}'); fe, ft, fn = model.forward_contrastive(ee, t, ng)
                pA = model.clip_loss.get_probabilities(fe, ft).diagonal(); pB = model.clip_loss.get_probabilities(fe, fn).diagonal()
                w[f'B_{mode}_official_{name}'] = (pA > pB).double()
                if name == 'att':
                    w[f'B_{mode}_official_att_pA'] = pA.double(); w[f'B_{mode}_official_att_pB'] = pB.double()
                if mode == 'train' or first:
                    seeded(f'B/{mode}/split/{name}'); sA, sB = official_split(model, ee, t, ng)
                    if mode == 'train':
                        w[f'B_train_split_{name}'] = (sA > sB).double()
                    else:
                        chk[f'official_split_vs_official_eval_max_abs_{name}'] = float(max((sA - pA).abs().max(), (sB - pB).abs().max()))
            for name, ee in (('real', e), ('noise', en)):
                seeded(f'B/{mode}/blind/{name}'); w[f'B_{mode}_blind_{name}'] = XM.blind_margin(model, ee, a, u).double()
    tm['B'] = time.time() - t0; t0 = time.time()
    # C: coupling broken, train mode
    with modes(model, *ALL):
        for name in ('RA', 'NA', 'ID'):
            ee, aa = inp[name]
            seeded(f'C/splitC/{name}'); x, y = enc(model, ee, aa); f, _ = fm(x, y); _, g = fm(x, y)
            m[f'C_train_splitC_{name}'] = mets(model, f, g)
            seeded(f'C/splitAll/{name}'); f, _ = model(ee, aa, mode='clip_train'); _, g = model(ee, aa, mode='clip_train')
            m[f'C_train_splitAll_{name}'] = mets(model, f, g)
    tm['C'] = time.time() - t0; t0 = time.time()
    # D: partition of the stochastic sources (joint pairing) and option (b)
    for mname, flags in (('C', (False, False, True)), ('E', (True, False, False)), ('A', (False, True, False))):
        with modes(model, *flags):
            for name in ('RA', 'ID'):
                ee, aa = inp[name]
                seeded(f'D/{mname}/joint/{name}'); f, g = model(ee, aa, mode='clip_train'); m[f'D_{mname}_joint_{name}'] = mets(model, f, g)
                if mname == 'C':
                    seeded(f'D/C/splitC/{name}'); x, y = enc(model, ee, aa); f, _ = fm(x, y); _, g = fm(x, y)
                    m[f'D_C_splitC_{name}'] = mets(model, f, g)
    with modes(model, *ALL), zero_stochastic(fm) as cnt:
        assert cnt['dropout'] == 4, cnt
        for name in ('RA', 'ID'):
            seeded(f'D/P0C/{name}'); f, g = model(*inp[name], mode='clip_train'); m[f'D_P0C_joint_{name}'] = mets(model, f, g)
    with modes(model, *ALL), zero_stochastic(model, model.audio_encoder.config) as cnt:
        chk['p0all_patched'] = cnt
        out = {}
        for name in ('RA', 'ID'):
            seeded(f'D/P0ALL/{name}'); f, g = model(*inp[name], mode='clip_train'); m[f'D_P0ALL_joint_{name}'] = mets(model, f, g); out[name] = (f, g)
    with modes(model, *EVAL):
        f0, g0 = model(e, a, mode='clip_train')
    chk['p0all_vs_eval_max_abs'] = float(max((out['RA'][0] - f0).abs().max(), (out['RA'][1] - g0).abs().max()))
    tm['D'] = time.time() - t0; t0 = time.time()
    # E: manual CALRA masks (replay / independent / transplant), encoders eval or train, CALRA eval with forced masks
    for emode in ('eval', 'train'):
        with modes(model, emode == 'train', emode == 'train', False):
            for name in ('RA', 'ID'):
                seeded(f'E/{emode}/{name}'); x, y = enc(model, *inp[name])
                bank = MaskBank(torch.Generator(device=dev).manual_seed(seed_of(base, f'E/{emode}/{name}/masks')))
                with calra_masks(fm, bank):
                    f1, g1 = bank.call(fm, x, y, 'record')
                    _, g2 = bank.call(fm, x, y, 'replay')
                    _, g3 = bank.call(fm, x, y, 'fresh')
                    g4 = bank.call(fm, x, y, 'replay', perm=P)[1] if name == 'RA' else None
                chk.setdefault('mask_replay_max_abs', 0.0)
                chk['mask_replay_max_abs'] = max(chk['mask_replay_max_abs'], float((g2 - g1).abs().max()))
                m[f'E_{emode}_mjoint_{name}'] = mets(model, f1, g1); m[f'E_{emode}_mindep_{name}'] = mets(model, f1, g3)
                if g4 is not None:
                    m[f'E_{emode}_mtransplant_RA'] = mets(model, f1, g4, follow=Pinv)
    tm['E'] = time.time() - t0; t0 = time.time()
    # F: deterministic transplant (eval)
    with modes(model, *EVAL):
        x, y = enc(model, e, a); _, g = fm(x, y)
        m['F_eval_audiotransplant_RA'] = mets(model, fm(x, y[P])[0], g, follow=P)
        m['F_eval_eegtransplant_RA'] = mets(model, fm(x[P], y)[0], g, follow=P)
    tm['F'] = time.time() - t0
    return m, {k: v.cpu().numpy() for k, v in w.items()}, chk, tm


# ----------------------------------------------------------------------------------------------------------- unit
def run_unit(row, plan, probe=False):
    import torch
    t_all = time.time(); job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda'); torch.cuda.reset_peak_memory_stats()
    assert sha(XM.CKPT) == XM.CKPT_SHA
    t0 = time.time(); D = unit_data(row, probe); t_data = time.time() - t0
    rec_b = read(bound_record(row['dataset'], row['unit']))
    with np.load(Path(rec_b['dest']) / 'margins.npz') as z:
        msub = z['margin_subwindows']
    ft_path = Path(rec_b['dest']) / 'final_model.pt'
    t0 = time.time(); model, args, UT = XM.build_model(dev); t_build = time.time() - t0
    inv = stochastic_inventory(model)
    arrays, checks, timing, scale = {}, {}, {}, {}
    person = D['person']; inp = D['inputs']
    for tag in TAGS:
        if tag == 'finetuned':
            assert sha(ft_path) == row['final_model_sha256'] == rec_b['final_model_sha256'], 'final model sha mismatch'
            model.load_state_dict(torch.load(ft_path, map_location='cpu', weights_only=True), strict=True)
        model.eval(); scale[tag] = float(model.clip_loss.logit_scale.exp())
        for dom in DOMS:
            blocks = D['blocks'][dom]
            if not blocks:
                continue
            M, W, meta = {}, {}, {'block_person': [], 'win_seg': [], 'win_sub': [], 'win_block': [], 'win_person': [], 'ro_same_segment': []}
            tb = []
            for b, blk in enumerate(blocks):
                ts = time.time()
                xs = [inp.window(i, o) for i, o in blk]
                e = torch.from_numpy(np.stack([x[0] for x in xs])).to(dev)
                a = torch.from_numpy(np.stack([x[1] for x in xs])).to(dev); u = torch.from_numpy(np.stack([x[2] for x in xs])).to(dev)
                with torch.no_grad():
                    mm, ww, ck, tsec = audit_block(model, e, a, u, f'{RNG_SEED}|{row["index"]}|{tag}|{dom}|{b}', first=(b == 0))
                for k, v in mm.items():
                    for mk, mv in v.items():
                        M.setdefault(f'm__{k}__{mk}', []).append(mv)
                for k, v in ww.items():
                    W.setdefault(f'w__{k}', []).append(v)
                for k, v in ck.items():
                    if k == 'p0all_patched':
                        checks.setdefault('p0all_patched', v)
                    else:
                        key = f'{tag}/{k}'; checks[key] = max(checks.get(key, 0.0), v)
                segs = [i for i, _ in blk]; pp = {person[i] for i in segs}; assert len(pp) == 1, 'block not person-homogeneous'
                meta['block_person'].append(next(iter(pp))); meta['win_seg'] += segs; meta['win_sub'] += [o for _, o in blk]
                meta['win_block'] += [b] * len(blk); meta['win_person'] += [person[i] for i in segs]
                meta['ro_same_segment'].append(float(np.mean([segs[i] == segs[(i + len(segs) // 2) % len(segs)] for i in range(len(segs))])))
                if tag == 'finetuned':           # bound eval-mode blind margins of the fine-tuned unit (attended-minus-ignored)
                    ref = np.array([msub[i, XM.SUB_OFFS_S.index(o)] for i, o in blk])
                    key = f'finetuned/blind_vs_bound_max_abs_{dom}'
                    checks[key] = max(checks.get(key, 0.0), float(np.max(np.abs(ref - ww['B_eval_blind_real']))))
                tb.append(time.time() - ts)
                if b == 0:
                    timing[f'{tag}/{dom}/sections_block0'] = {k: round(v, 2) for k, v in tsec.items()}
            pre = f'{tag}__{dom}__'
            arrays.update({pre + k: np.asarray(v, dtype=np.float64) for k, v in M.items()})
            arrays.update({pre + k: np.concatenate(v) for k, v in W.items()})
            arrays.update({pre + k: np.asarray(v) for k, v in meta.items()})
            timing[f'{tag}/{dom}/block_seconds'] = {'n': len(tb), 'mean': float(np.mean(tb)), 'max': float(np.max(tb))}
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(dest / 'audit.npz', **arrays)
    n_blocks = {f'{t}/{d}': len(D['blocks'][d]) for t in TAGS for d in DOMS}
    per_block = np.mean([v['mean'] for k, v in timing.items() if k.endswith('block_seconds')])
    projected = (t_data + t_build + per_block * len(TAGS) * sum(D['full_counts'].values())) / 3600
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'protocol_sha256': sha(PROTOCOL),
           'bound_record_sha256': sha(bound_record(row['dataset'], row['unit'])), 'final_model_sha256': row['final_model_sha256'],
           'dest': str(dest), 'npz_sha256': sha(dest / 'audit.npz'), 'n_blocks': n_blocks, 'full_block_counts': D['full_counts'],
           'logit_scale_exp': scale, 'stochastic_inventory': inv, 'checks': checks,
           'runtime_patches': ['calra_masks: instance-level forward of CALRA nn.Dropout x4 (self.dropout, eeg_ffn[2], audio_ffn[2], '
                               'shared_interaction[2]) -> MaskBank.apply inside section E only; removed on exit',
                               'zero_stochastic: Dropout.p / DropPath.drop_prob / Wav2Vec2Attention.dropout / config.mask_time_prob set to 0 '
                               'inside section D P0C (CALRA only) and P0ALL (whole model) only; restored on exit',
                               'external_mindmix.official(): UM.load_trusted_checkpoint = safe_load (weights_only; inherited, unchanged)'],
           'timing': timing, 'seconds': {'data': round(t_data, 1), 'build': round(t_build, 1), 'total': round(time.time() - t_all, 1)},
           'projected_full_unit_hours': projected, 'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20,
           'device': torch.cuda.get_device_name(0), 'job': job}
    for tag in TAGS:
        assert checks.get(f'{tag}/enc_replica_eval_max_abs', 1.0) < 1e-4 and checks.get(f'{tag}/mask_replay_max_abs', 1.0) < 1e-5, checks
    assert all(v < 1e-4 for k, v in checks.items() if 'official_split_vs_official_eval' in k), checks
    if 'finetuned/blind_vs_bound_max_abs_train' in checks:
        assert all(v < 1e-2 for k, v in checks.items() if 'blind_vs_bound' in k), checks
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], row['dataset'], row['unit'], 'dropkey audit complete', rec['seconds'], flush=True)
    return rec


# ----------------------------------------------------------------------------------------------------------- selftest (synthetic)
def selftest():
    """Synthetic inputs only (no dataset is read, nothing is written): exercises every section on the released model and prints
    the engineering checks (no metric values)."""
    import torch
    dev = torch.device('cuda' if torch.cuda.is_available() else 'cpu'); t0 = time.time()
    model, _, _ = XM.build_model(dev); g = torch.Generator().manual_seed(0); n = 4
    e = torch.randn(n, 64, 400, generator=g).to(dev); a = torch.randn(n, 32000, generator=g).to(dev); u = torch.randn(n, 32000, generator=g).to(dev)
    a, u = a / a.abs().amax(1, keepdim=True), u / u.abs().amax(1, keepdim=True)
    with torch.no_grad():
        m, w, chk, tm = audit_block(model, e, a, u, 'selftest', first=True)
        m2, _, _, _ = audit_block(model, e, a, u, 'selftest', first=False)
    assert m2.keys() == m.keys() and max(abs(m[c][k] - m2[c][k]) for c in m for k in m[c]) < 1e-9, 'audit_block not reproducible under the same seed base'
    assert all(np.isfinite(v).all() for v in w.values()) and all(math.isfinite(x) for d in m.values() for x in d.values())
    print(json.dumps({'device': str(dev), 'conditions': len(m), 'window_scores': sorted(w), 'checks': chk, 'section_seconds': tm,
                      'inventory': stochastic_inventory(model), 'seconds': round(time.time() - t0, 1)}, indent=1, default=str))


# ----------------------------------------------------------------------------------------------------------- fleet
def receipts():
    out = {'pass': [], 'other': []}
    if (OUT / 'plan.json').exists():
        ps = sha(OUT / 'plan.json')
        for p in sorted((OUT / 'probes').glob('*/receipt.json')):
            r = read(p)
            if r.get('plan_sha256') == ps:
                out['pass' if r.get('status') == 'pass' else 'other'].append(p)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 20, 'slots': 1, 'initial': [], 'submit': []}
    if not (OUT / 'plan.json').exists():
        return st
    plan = read(OUT / 'plan.json'); left = [r for r in plan['rows'] if not (OUT / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(left)
    if not left:
        return {**st, 'state': 'complete'}
    if any((OUT / 'units' / f'{r["id"]}.FAILED.json').exists() for r in left):
        return {**st, 'state': 'failed_unit_review'}
    rec = receipts()
    if not rec['pass']:
        return {**st, 'state': 'engineering_probe_failed'} if rec['other'] else {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
    return {**st, 'state': 'ready', 'ready': len(left), 'slots': 2, 'submit': [SBATCH, '--worker']}


def worker(plan):
    """One unit per job; claimed by flock; a negative return code (signal / preemption) is not a failure."""
    assert receipts()['pass'], 'no passing smoke'
    for row in plan['rows']:
        path = OUT / 'units' / f'{row["id"]}.json'
        if path.exists() or (OUT / 'units' / f'{row["id"]}.FAILED.json').exists():
            continue
        lock = OUT / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', row['id']]).returncode
            if rc < 0:
                raise SystemExit(f'unit ended by signal {-rc}')
            if rc or not path.exists():
                write(OUT / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('mindmix dropkey audit unit failed')
            return


SMOKE_KEYS = ('A_train_joint_RA', 'A_eval_joint_RA', 'A_train_joint_ID', 'C_train_splitAll_RA', 'C_train_splitC_RA', 'D_C_joint_ID',
              'E_eval_mtransplant_RA', 'F_eval_audiotransplant_RA')


def smoke(plan):
    """One DTU and one FAU probe unit (released + fine-tuned, SMOKE_BLOCKS train-side blocks each, no test windows)."""
    job = os.environ['SLURM_JOB_ID']; rec = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'protocol_sha256': sha(PROTOCOL), 'units': []}
    try:
        for ds in ('dtu', 'fau'):
            row = next(r for r in plan['rows'] if r['dataset'] == ds)
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--probe-unit', row['id']]).returncode
            assert rc == 0, rc
            u = read(OUT / 'probes' / job / 'units' / f'{row["id"]}.json'); assert u['status'] == 'complete' and u['n_blocks']['finetuned/test'] == 0
            with np.load(Path(u['dest']) / 'audit.npz') as z:
                assert all(np.isfinite(z[k]).all() for k in z.files if z[k].dtype.kind == 'f')
                nums = {f'{t}/{c}': {mk: round(float(np.mean(z[f'{t}__train__m__{c}__{mk}'])), 6) for mk in ('ce', 'top1', 'top1_follow')
                                     if f'{t}__train__m__{c}__{mk}' in z.files} for t in TAGS for c in SMOKE_KEYS}
                for t in TAGS:
                    for mode in ('eval', 'train'):
                        wa = z[f'{t}__train__w__B_{mode}_official_att'].mean(); wi = z[f'{t}__train__w__B_{mode}_official_ign'].mean()
                        nums[f'{t}/B_{mode}_official_slot_privilege'] = round(float(wa + wi - 1), 6)
            rec['units'].append({**{k: u[k] for k in ('row', 'n_blocks', 'full_block_counts', 'checks', 'timing', 'seconds', 'projected_full_unit_hours',
                                                       'gpu_peak_mb', 'device', 'logit_scale_exp')},
                                 'smoke_numbers_not_results': nums})
        rec['status'] = 'pass'
    except BaseException:
        rec.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', rec)


# ----------------------------------------------------------------------------------------------------------- summary (CPU)
def _pmean(v, who):
    who = np.asarray(who)
    return float(np.mean([np.mean(v[who == p]) for p in sorted(set(who.tolist()))]))


def _ratio(num, den):
    return float(num / den) if abs(den) > 1e-9 else None


def unit_quantities(Z, pre):
    q = {}
    bp = Z[pre + 'block_person']; wp = Z[pre + 'win_person']
    for k in Z.files:
        if k.startswith(pre + 'm__'):
            q[k[len(pre) + 3:]] = _pmean(Z[k], bp)
        elif k.startswith(pre + 'w__') and not k.endswith(('_pA', '_pB')):
            x = Z[k]; acc = ((x > 0) + 0.5 * (x == 0)) if '_blind_' in k else x
            q['acc__' + k[len(pre) + 3:]] = _pmean(acc, wp)
    jt = q['A_train_joint_RA__ce']; d = {'ro_same_segment': float(np.mean(Z[pre + 'ro_same_segment']))}
    for name in ('RA', 'NA', 'ID'):
        base = q[f'A_train_joint_{name}__ce']
        d[f'r_splitAll_{name}'] = _ratio(q[f'C_train_splitAll_{name}__ce'] - base, LN_B - base)
        d[f'r_splitC_{name}'] = _ratio(q[f'C_train_splitC_{name}__ce'] - base, LN_B - base)
    d['r_splitC_calra_only_RA'] = _ratio(q['D_C_splitC_RA__ce'] - q['D_C_joint_RA__ce'], LN_B - q['D_C_joint_RA__ce'])
    for name in ('RA', 'NA', 'RU', 'RO', 'ID'):
        d[f'eval_norm_{name}'] = q[f'A_eval_joint_{name}__ce'] / LN_B; d[f'train_norm_{name}'] = q[f'A_train_joint_{name}__ce'] / LN_B
    d['train_joint_RA_ce'] = jt
    d['audio_follow'] = q['F_eval_audiotransplant_RA__top1_follow']; d['eeg_follow'] = q['F_eval_eegtransplant_RA__top1_follow']
    d['audio_transplant_diag'] = q['F_eval_audiotransplant_RA__top1']; d['eeg_transplant_diag'] = q['F_eval_eegtransplant_RA__top1']
    for em in ('eval', 'train'):
        d[f'mask_follow_enc{em}'] = q[f'E_{em}_mtransplant_RA__top1_follow']; d[f'mask_diag_enc{em}'] = q[f'E_{em}_mtransplant_RA__top1']
    for sc in ('eval_official', 'train_official', 'train_split'):
        d[f'privilege_{sc}'] = q[f'acc__B_{sc}_att'] + q[f'acc__B_{sc}_ign'] - 1
    q.update({'derived__' + k: v for k, v in d.items()})
    return q


def _rule(x, hi, lo, labels):
    if x is None:
        return 'undefined'
    return labels[0] if x >= hi else labels[1] if x <= lo else labels[2]


def summarize():
    """CPU, after every unit is complete. Per dataset x model x domain: across the 10 units (each unit = person mean of its block
    means; windows: person mean of the per-window wins / blind accuracy), mean, SD, median, min, max of every quantity, and the
    pre-registered reading rules applied to the unit medians (PROTOCOL.md section 6)."""
    plan = read(OUT / 'plan.json'); verify(plan)
    missing = [r['id'] for r in plan['rows'] if not (OUT / 'units' / f'{r["id"]}.json').exists()]
    assert not missing, f'{len(missing)} units incomplete'
    cells, n_blocks = {}, {}
    for row in plan['rows']:
        rec = read(OUT / 'units' / f'{row["id"]}.json')
        assert rec['plan_sha256'] == sha(OUT / 'plan.json') and rec['protocol_sha256'] == plan['protocol_sha256'] and not rec['probe']
        f = Path(rec['dest']) / 'audit.npz'; assert sha(f) == rec['npz_sha256']
        with np.load(f) as z:
            Z = {k: z[k] for k in z.files}
        for t in TAGS:
            for d in DOMS:
                pre = f'{t}__{d}__'
                if pre + 'block_person' not in Z:
                    continue
                cells.setdefault(f'{row["dataset"]}/{t}/{d}', []).append(unit_quantities(Z, pre))
                n_blocks.setdefault(f'{row["dataset"]}/{t}/{d}', []).append(int(len(Z[pre + 'block_person'])))
    out, rules = {}, {}
    for key, units in cells.items():
        qs = sorted({k for u in units for k in u})
        agg = {}
        for k in qs:
            v = np.array([u[k] for u in units if u.get(k) is not None], dtype=float)
            agg[k] = {'n_units': int(len(v)), 'mean': float(v.mean()), 'sd': float(v.std(ddof=1)) if len(v) > 1 else None,
                      'median': float(np.median(v)), 'min': float(v.min()), 'max': float(v.max())} if len(v) else {'n_units': 0}
        out[key] = {'n_units': len(units), 'n_blocks_total': int(sum(n_blocks[key])), 'quantities': agg}
        med = lambda k: agg.get('derived__' + k, {}).get('median')
        rules[key] = {
            'R1_shared_noise_necessary': _rule(med('r_splitAll_RA'), 0.9, 0.1, ('supports_H_dk', 'contradicts_H_dk', 'partial')),
            'R1b_calra_noise_necessary': _rule(med('r_splitC_RA'), 0.9, 0.1, ('supports_H_dk_calra', 'contradicts_H_dk_calra', 'partial')),
            'R2_deterministic_key': _rule(None if med('eval_norm_RA') is None else 1 - med('eval_norm_RA'), 0.9, 0.1,
                                          ('deterministic_key_present', 'no_deterministic_key', 'partial')),
            'R3_key_identity': ('audio_key' if (med('audio_follow') or 0) >= 0.9 else 'eeg_key' if (med('eeg_follow') or 0) >= 0.9
                                else 'neither_dominant'),
            'R4_mask_vs_content_enc_eval': ('mask_dominates' if (med('mask_follow_enceval') or 0) >= 0.9 else
                                            'content_dominates' if (med('mask_diag_enceval') or 0) >= 0.9 else 'mixed'),
            'R4_mask_vs_content_enc_train': ('mask_dominates' if (med('mask_follow_enctrain') or 0) >= 0.9 else
                                             'content_dominates' if (med('mask_diag_enctrain') or 0) >= 0.9 else 'mixed'),
            'R5_noise_sufficient_identical_rows': _rule(None if med('train_norm_ID') is None else 1 - med('train_norm_ID'), 0.9, 0.1,
                                                        ('noise_sufficient', 'noise_insufficient', 'partial')),
            'R6_slot_privilege_medians': {k: med('privilege_' + k) for k in ('eval_official', 'train_official', 'train_split')},
            'medians': {k: med(k) for k in ('r_splitAll_RA', 'r_splitC_RA', 'r_splitC_calra_only_RA', 'eval_norm_RA', 'train_norm_ID',
                                            'audio_follow', 'eeg_follow', 'mask_follow_enceval', 'mask_diag_enceval',
                                            'mask_follow_enctrain', 'mask_diag_enctrain')}}
    RESULTS.mkdir(parents=True, exist_ok=True)
    body = {'version': plan['version'], 'plan_sha256': sha(OUT / 'plan.json'), 'protocol_sha256': plan['protocol_sha256'],
            'ln_B': LN_B, 'batch': BATCH, 'units_included': len(plan['rows']), 'cells': out, 'reading_rules': rules,
            'definitions': __doc__ + summarize.__doc__,
            'created': datetime.now().astimezone().isoformat()}
    RESULT_FILE.write_text(json.dumps(body, indent=1) + '\n')
    print(json.dumps(rules, indent=1))


def main():
    ap = argparse.ArgumentParser()
    for flag in ('make_plan', 'selftest', 'smoke', 'worker', 'summarize'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--probe-unit')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.selftest:
        selftest(); return
    if a.make_plan:
        make_plan(); return
    plan = read(OUT / 'plan.json'); verify(plan)
    if a.summarize:
        os.umask(0o022); summarize(); return
    if a.unit or a.probe_unit:
        run_unit(next(r for r in plan['rows'] if r['id'] in (a.unit, a.probe_unit)), plan, probe=bool(a.probe_unit)); return
    if a.smoke:
        smoke(plan); return
    assert a.worker
    worker(plan)


if __name__ == '__main__':
    main()
