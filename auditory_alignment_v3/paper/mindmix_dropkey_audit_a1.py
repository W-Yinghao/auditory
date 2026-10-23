"""Appendum 01 to the complete-MindMix shortcut audit (paper/mindmix_dropkey_audit.py = v1; frozen PROTOCOL.md be2d1e9c..., plan
23769dbc...; v1 is imported, never edited). Frozen appendum: private/auditory_alignment_v3/paper/mindmix_dropkey_v1/APPENDUM_01.md
and plan_v2_appendum.json (0444, frozen before any appendum unit ran; both sha256s bound in every appendum unit record).

Question. In the v1 smoke, two independent complete train-mode forward passes broke the positive-pair match while two independent
CALRA calls on shared encoder outputs did not. Which encoder's train-mode randomness carries that coupling: the EEG encoder's
DropPath, wav2vec2's randomness (dropout / attention dropout / feature-projection dropout and SpecAugment time masks), or both?

Same units (the 20 v1 rows: 10 DTU + 10 FAU fine-tuned units), same models (released, then the unit's final_model.pt), same blocks
(v1.unit_data) and the same matched-noise EEG as v1 (identical seed base). Per block and input (RA real EEG + attended audio, NA
v1's matched Gaussian EEG + attended, ID row 0 repeated), encoders in train mode, CALRA eval with v1's forced manual masks:
  x1, x2  two EEG-encoder passes with independent DropPath (x = eeg_proj(eeg_encoder(e)));
  y1, y2  two wav2vec2 passes with independent dropout AND SpecAugment (y = audio_proj(mean wav2vec2 last_hidden_state));
  y_spec  a wav2vec2 pass replaying y1's torch RNG state (same dropout masks) with a fresh numpy state (new SpecAugment masks);
  y_drop  a wav2vec2 pass replaying y1's numpy RNG state (same SpecAugment masks) with a fresh torch seed (new dropout masks);
  M1, M2  two independent sets of CALRA masks (9 sites each).
  f = CALRA(x1, y1; M1)[0] in every cell; g = CALRA(xg, yg; Mg)[1] with xg in {x1 (E s), x2 (E i)}, yg in {y1 (A s), y2 (A i)},
  Mg in {M1 (C s), M2 (C i)}: the full 2 x 2 x 2 factorial E?A?C? (EsAsCs = the training pairing, all shared; EiAiCi = nothing
  shared), plus EsAspecCs (only SpecAugment independent) and EsAdropCs (only wav2vec2 dropout independent).
Metrics per cell: v1.mets (ClipLoss toward the diagonal, top-1, gap, spread); diagnostics: mean relative perturbation
||x2-x1||/||x1||, ||y2-y1||/||y1||, ||y_spec-y1||/||y1||, ||y_drop-y1||/||y1||.
Engineering checks (asserted): RNG-state replay reproduces x1 and y1 exactly; EsAsCs g == the recording call's g; 9 mask sites per
call; fine-tuned eval blind margin == the bound margins.npz (block 0 per domain, < 1e-2).
--summarize (CPU, after all appendum AND all v1 units): runs v1's summarize (MINDMIX_DROPKEY_AUDIT.json) and writes
MINDMIX_DROPKEY_AUDIT_COMBINED.json: v1 cells and reading rules (R1 and R1b shown) side by side with the appendum's.

CLI: --make-plan (CPU) | --selftest (GPU, synthetic inputs, no data, no writes) | --smoke | --worker | --unit ID | --probe-unit ID
| --summarize (CPU).
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import traceback

import numpy as np

from . import mindmix_dropkey_audit as V

XM = V.XM
OUT = V.OUT / 'appendum_01'
STORE = V.STORE / 'appendum_01'
APPENDUM = V.OUT / 'APPENDUM_01.md'
PLAN = V.OUT / 'plan_v2_appendum.json'
RESULT_FILE = V.RESULTS / 'MINDMIX_DROPKEY_AUDIT_COMBINED.json'
NAME, LANE, SBATCH = 'c3_s35pmmda1', 's35_paper_mmdropkey_a1', 'slurm/aln35_paper_mmdropkey_a1.sbatch'
INPUTS = ('RA', 'NA', 'ID')
CELLS = tuple(f'E{e}A{a}C{c}' for e in 'si' for a in 'si' for c in 'si')
SUBCELLS = ('EsAspecCs', 'EsAdropCs')
REF = 'EsAsCs'
read, write, sha, digest = V.read, V.write, V.sha, V.digest


# ----------------------------------------------------------------------------------------------------------- plan
def sources():
    repo = Path(V.core.REPO)
    return {**V.sources(), str(Path(__file__).relative_to(repo)): sha(Path(__file__))}


def make_plan():
    for p in (APPENDUM,):
        assert p.exists() and not (p.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)), f'{p.name} not frozen (0444)'
    v1 = read(V.OUT / 'plan.json')
    rows = []
    for r in v1['rows']:
        body = {'appendum': 1, 'v1_id': r['id'], 'dataset': r['dataset'], 'unit': r['unit'], 'content_fold': r['content_fold'],
                'person_fold': r['person_fold']}
        rows.append({**body, 'id': 'MMDKA1_' + digest(body, 16), 'v1_index': r['index'], 'bound_record_sha256': r['bound_record_sha256'],
                     'final_model_sha256': r['final_model_sha256']})
    body = {'version': 'PAPER_MINDMIX_DROPKEY_AUDIT_APPENDUM_01', 'appendum_sha256': sha(APPENDUM), 'v1_plan_sha256': sha(V.OUT / 'plan.json'),
            'v1_protocol_sha256': v1['protocol_sha256'], 'sources': sources(), 'rows': rows,
            'settings': {'inputs': list(INPUTS), 'cells': list(CELLS), 'subcells': list(SUBCELLS), 'reference': REF,
                         'blocks': 'v1.unit_data (same blocks as v1)', 'seed_base': 'v1 per-block base (identical NA noise); appendum tags A1/...',
                         'smoke': 'one unit (first DTU row), released + fine-tuned, v1.SMOKE_BLOCKS train-side blocks'},
            'store': str(STORE)}
    if PLAN.exists():
        old = read(PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable appendum plan drift'
    else:
        assert not OUT.exists() and not STORE.exists(), 'appendum output exists before the appendum plan'
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
        write(PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); PLAN.chmod(0o444)
    print('appendum plan', sha(PLAN), len(rows), 'appendum', body['appendum_sha256'], flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'appendum source drift'
    assert sha(APPENDUM) == plan['appendum_sha256'] and sha(V.OUT / 'plan.json') == plan['v1_plan_sha256'], 'appendum / v1 plan drift'
    for r in plan['rows']:
        assert sha(V.bound_record(r['dataset'], r['unit'])) == r['bound_record_sha256'], f'bound unit record drift {r["unit"]}'


# ----------------------------------------------------------------------------------------------------------- one block
def _states():
    import torch
    return (torch.get_rng_state(), torch.cuda.get_rng_state() if torch.cuda.is_available() else None), np.random.get_state()


def _set_torch(st):
    import torch
    torch.set_rng_state(st[0])
    if st[1] is not None:
        torch.cuda.set_rng_state(st[1])


def _rel(a, b):
    return float(((a - b).norm(dim=-1) / b.norm(dim=-1).clamp_min(1e-12)).mean())


def block_cells(model, e, a, base, first):
    import torch
    fm = model.fusion_module; dev = e.device
    en = V.matched_noise(e, torch.Generator().manual_seed(V.seed_of(base, 'noise')))        # == v1's NA input of this block
    inp = {'RA': (e, a), 'NA': (en, a), 'ID': (e[:1].expand_as(e).contiguous(), a[:1].expand_as(a).contiguous())}
    X = lambda ee: model.eeg_proj(model.eeg_encoder(ee))
    Y = lambda aa: model.audio_proj(model.audio_encoder(aa).last_hidden_state.mean(1))
    m, chk = {}, {}

    def seeded(tag):
        s = V.seed_of(base, tag); torch.manual_seed(s); np.random.seed(s % 2 ** 32)
    with V.modes(model, True, True, False):                       # encoders train mode; CALRA eval with forced masks
        for name, (ee, aa) in inp.items():
            seeded(f'A1/{name}/eeg'); st_t, _ = _states()
            x1 = X(ee); x2 = X(ee)
            if first:
                _set_torch(st_t); chk[f'eeg_replay_max_abs_{name}'] = float((X(ee) - x1).abs().max())
            seeded(f'A1/{name}/audio'); st_t, st_n = _states()
            y1 = Y(aa); y2 = Y(aa)
            _set_torch(st_t); np.random.seed(V.seed_of(base, f'A1/{name}/spec_np') % 2 ** 32); y_spec = Y(aa)
            np.random.set_state(st_n); torch.manual_seed(V.seed_of(base, f'A1/{name}/drop_torch')); y_drop = Y(aa)
            if first:
                _set_torch(st_t); np.random.set_state(st_n); chk[f'audio_replay_max_abs_{name}'] = float((Y(aa) - y1).abs().max())
            m[f'diag_{name}'] = {'x_rel': _rel(x2, x1), 'y_rel': _rel(y2, y1), 'yspec_rel': _rel(y_spec, y1), 'ydrop_rel': _rel(y_drop, y1)}
            assert min(m[f'diag_{name}'].values()) > 0, ('a renewed stochastic component left the embedding unchanged', m[f'diag_{name}'])
            bank = V.MaskBank(torch.Generator(device=dev).manual_seed(V.seed_of(base, f'A1/{name}/masks')))
            with V.calra_masks(fm, bank):
                f, g_ref = bank.call(fm, x1, y1, 'record'); M1 = bank.rec
                bank.call(fm, x1, y1, 'record'); M2 = bank.rec
                for cell in CELLS:
                    xg = x1 if cell[1] == 's' else x2; yg = y1 if cell[3] == 's' else y2; bank.rec = M1 if cell[5] == 's' else M2
                    _, g = bank.call(fm, xg, yg, 'replay'); m[f'{cell}_{name}'] = V.mets(model, f, g)
                    if cell == REF:
                        chk['ref_replay_max_abs'] = max(chk.get('ref_replay_max_abs', 0.0), float((g - g_ref).abs().max()))
                for cell, yg in (('EsAspecCs', y_spec), ('EsAdropCs', y_drop)):
                    bank.rec = M1; _, g = bank.call(fm, x1, yg, 'replay'); m[f'{cell}_{name}'] = V.mets(model, f, g)
    return m, chk


# ----------------------------------------------------------------------------------------------------------- unit
def run_unit(row, plan, probe=False):
    import torch
    t_all = time.time(); job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda'); torch.cuda.reset_peak_memory_stats()
    assert sha(XM.CKPT) == XM.CKPT_SHA
    t0 = time.time(); D = V.unit_data(row, probe); t_data = time.time() - t0
    rec_b = read(V.bound_record(row['dataset'], row['unit']))
    with np.load(Path(rec_b['dest']) / 'margins.npz') as z:
        msub = z['margin_subwindows']
    ft_path = Path(rec_b['dest']) / 'final_model.pt'
    t0 = time.time(); model, _, _ = XM.build_model(dev); t_build = time.time() - t0
    arrays, checks, timing = {}, {}, {}
    person, inp = D['person'], D['inputs']
    for tag in V.TAGS:
        if tag == 'finetuned':
            assert sha(ft_path) == row['final_model_sha256'] == rec_b['final_model_sha256'], 'final model sha mismatch'
            model.load_state_dict(torch.load(ft_path, map_location='cpu', weights_only=True), strict=True)
        model.eval()
        for dom in V.DOMS:
            blocks = D['blocks'][dom]
            if not blocks:
                continue
            M, bp, tb = {}, [], []
            for b, blk in enumerate(blocks):
                ts = time.time()
                xs = [inp.window(i, o) for i, o in blk]
                e = torch.from_numpy(np.stack([x[0] for x in xs])).to(dev)
                a = torch.from_numpy(np.stack([x[1] for x in xs])).to(dev); u = torch.from_numpy(np.stack([x[2] for x in xs])).to(dev)
                with torch.no_grad():
                    mm, ck = block_cells(model, e, a, f'{V.RNG_SEED}|{row["v1_index"]}|{tag}|{dom}|{b}', first=(b == 0))
                    if tag == 'finetuned' and b == 0:                  # pipeline check against the bound eval-mode margins
                        with V.modes(model, *V.EVAL):
                            br = XM.blind_margin(model, e, a, u).double().cpu().numpy()
                        ref = np.array([msub[i, XM.SUB_OFFS_S.index(o)] for i, o in blk])
                        checks[f'finetuned/blind_vs_bound_max_abs_{dom}'] = float(np.max(np.abs(ref - br)))
                for k, v in mm.items():
                    for mk, mv in v.items():
                        M.setdefault(f'm__{k}__{mk}', []).append(mv)
                for k, v in ck.items():
                    key = f'{tag}/{k}'; checks[key] = max(checks.get(key, 0.0), v)
                pp = {person[i] for i, _ in blk}; assert len(pp) == 1, 'block not person-homogeneous'
                bp.append(next(iter(pp))); tb.append(time.time() - ts)
            pre = f'{tag}__{dom}__'
            arrays.update({pre + k: np.asarray(v, dtype=np.float64) for k, v in M.items()}); arrays[pre + 'block_person'] = np.asarray(bp)
            timing[f'{tag}/{dom}/block_seconds'] = {'n': len(tb), 'mean': float(np.mean(tb)), 'max': float(np.max(tb))}
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(dest / 'audit.npz', **arrays)
    per_block = np.mean([v['mean'] for v in timing.values()])
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(PLAN), 'appendum_sha256': sha(APPENDUM),
           'v1_plan_sha256': sha(V.OUT / 'plan.json'), 'v1_protocol_sha256': sha(V.PROTOCOL),
           'bound_record_sha256': sha(V.bound_record(row['dataset'], row['unit'])), 'final_model_sha256': row['final_model_sha256'],
           'dest': str(dest), 'npz_sha256': sha(dest / 'audit.npz'), 'n_blocks': {f'{t}/{d}': len(D['blocks'][d]) for t in V.TAGS for d in V.DOMS},
           'full_block_counts': D['full_counts'], 'checks': checks,
           'runtime_patches': ['v1.calra_masks: instance-level forward of CALRA nn.Dropout x4 -> v1.MaskBank.apply (forced masks); removed on exit',
                               'RNG-state replay (torch CPU/CUDA, numpy global) to share or renew one stochastic component between passes',
                               'external_mindmix.official(): UM.load_trusted_checkpoint = safe_load (inherited, unchanged)'],
           'timing': timing, 'seconds': {'data': round(t_data, 1), 'build': round(t_build, 1), 'total': round(time.time() - t_all, 1)},
           'projected_full_unit_hours': (t_data + t_build + per_block * len(V.TAGS) * sum(D['full_counts'].values())) / 3600,
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': job}
    assert all(v < 1e-5 for k, v in checks.items() if 'replay' in k), checks
    assert all(v < 1e-2 for k, v in checks.items() if 'blind_vs_bound' in k), checks
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], row['dataset'], row['unit'], 'appendum audit complete', rec['seconds'], flush=True)
    return rec


def selftest():
    """Synthetic inputs only (no dataset is read, nothing is written): every cell on the released model; prints checks only."""
    import torch
    dev = torch.device('cuda'); t0 = time.time()
    model, _, _ = XM.build_model(dev); gq = torch.Generator().manual_seed(0); n = 4
    e = torch.randn(n, 64, 400, generator=gq).to(dev); a = torch.randn(n, 32000, generator=gq).to(dev); a = a / a.abs().amax(1, keepdim=True)
    with torch.no_grad():
        m, chk = block_cells(model, e, a, 'selftest', first=True); m2, _ = block_cells(model, e, a, 'selftest', first=False)
    assert m2.keys() == m.keys() and max(abs(m[c][k] - m2[c][k]) for c in m for k in m[c]) < 1e-9, 'not reproducible'
    assert all(v < 1e-5 for k, v in chk.items() if 'replay' in k), chk
    print(json.dumps({'cells': len(m), 'checks': chk, 'synthetic_perturbation_diagnostics': {k: v for k, v in m.items() if k.startswith('diag_')},
                      'seconds': round(time.time() - t0, 1)}, indent=1))


# ----------------------------------------------------------------------------------------------------------- fleet
def receipts():
    out = {'pass': [], 'other': []}
    if PLAN.exists():
        ps = sha(PLAN)
        for p in sorted((OUT / 'probes').glob('*/receipt.json')):
            r = read(p)
            if r.get('plan_sha256') == ps:
                out['pass' if r.get('status') == 'pass' else 'other'].append(p)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 20, 'slots': 1, 'initial': [], 'submit': []}
    if not PLAN.exists():
        return st
    plan = read(PLAN); left = [r for r in plan['rows'] if not (OUT / 'units' / f'{r["id"]}.json').exists()]
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
                raise RuntimeError('mindmix dropkey appendum unit failed')
            return


def smoke(plan):
    """One unit (the first DTU row): released + fine-tuned, v1.SMOKE_BLOCKS train-side blocks, no test windows."""
    job = os.environ['SLURM_JOB_ID']; rec = {'status': 'running', 'plan_sha256': sha(PLAN), 'appendum_sha256': sha(APPENDUM), 'units': []}
    try:
        row = next(r for r in plan['rows'] if r['dataset'] == 'dtu')
        rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--probe-unit', row['id']]).returncode
        assert rc == 0, rc
        u = read(OUT / 'probes' / job / 'units' / f'{row["id"]}.json'); assert u['status'] == 'complete' and u['n_blocks']['finetuned/test'] == 0
        with np.load(Path(u['dest']) / 'audit.npz') as z:
            assert all(np.isfinite(z[k]).all() for k in z.files if z[k].dtype.kind == 'f')
            nums = {f'{t}/{c}_{i}': {mk: round(float(np.mean(z[f'{t}__train__m__{c}_{i}__{mk}'])), 6) for mk in ('ce', 'top1')}
                    for t in V.TAGS for c in CELLS + SUBCELLS for i in ('RA', 'ID')}
            nums.update({f'{t}/diag_RA': {mk: round(float(np.mean(z[f'{t}__train__m__diag_RA__{mk}'])), 6)
                                          for mk in ('x_rel', 'y_rel', 'yspec_rel', 'ydrop_rel')} for t in V.TAGS})
        rec['units'].append({**{k: u[k] for k in ('row', 'n_blocks', 'full_block_counts', 'checks', 'timing', 'seconds',
                                                   'projected_full_unit_hours', 'gpu_peak_mb', 'device')}, 'smoke_numbers_not_results': nums})
        rec['status'] = 'pass'
    except BaseException:
        rec.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', rec)


# ----------------------------------------------------------------------------------------------------------- summary (CPU)
def unit_quantities(Z, pre):
    """Person mean of the block means per cell x input x metric; r = (ce_cell - ce_EsAsCs) / (ln B - ce_EsAsCs) of the same input
    (the fraction of the gap to chance opened by making the cell's components independent); norm = ce / ln B."""
    bp = Z[pre + 'block_person']; q = {}
    for k in Z.files:
        if k.startswith(pre + 'm__'):
            q[k[len(pre) + 3:]] = V._pmean(Z[k], bp)
    for name in INPUTS:
        base = q[f'{REF}_{name}__ce']
        for cell in CELLS + SUBCELLS:
            q[f'derived__r_{cell}_{name}'] = V._ratio(q[f'{cell}_{name}__ce'] - base, V.LN_B - base)
            q[f'derived__norm_{cell}_{name}'] = q[f'{cell}_{name}__ce'] / V.LN_B
    return q


def _lab(x, hi=0.9, lo=0.1):
    return None if x is None else 'ge_0.9' if x >= hi else 'le_0.1' if x <= lo else 'between'


def a1_rules(med):
    rE, rA, rEA, rC = (med(f'r_{c}_RA') for c in ('EiAsCs', 'EsAiCs', 'EiAiCs', 'EsAsCi'))
    if None in (rE, rA, rEA):
        key = 'undefined'
    elif rA >= 0.9 and rE <= 0.1:
        key = 'audio_branch_key'
    elif rE >= 0.9 and rA <= 0.1:
        key = 'eeg_branch_key'
    elif rA >= 0.9 and rE >= 0.9:
        key = 'both_branches_necessary'
    elif rEA <= 0.1:
        key = 'no_encoder_key'
    elif rA <= 0.1 and rE <= 0.1 and rEA >= 0.9:
        key = 'redundant_either_branch_suffices'
    else:
        key = 'partial'
    suff = {src: _lab(None if med(f'norm_{c}_ID') is None else 1 - med(f'norm_{c}_ID'))
            for src, c in (('only_audio_shared', 'EiAsCi'), ('only_eeg_shared', 'EsAiCi'), ('only_calra_shared', 'EiAiCs'),
                           ('all_shared', 'EsAsCs'))}
    return {'A1_R1_which_branch_coupling_is_necessary': key,
            'A1_R2_calra_coupling_necessary': {'ge_0.9': 'necessary', 'le_0.1': 'not_necessary', 'between': 'partial', None: 'undefined'}[_lab(rC)],
            'A1_R3_audio_components': {'specaugment_only_independent': _lab(med('r_EsAspecCs_RA')), 'dropout_only_independent': _lab(med('r_EsAdropCs_RA'))},
            'A1_R4_sufficiency_identical_rows_(1-norm)': suff,
            'A1_R5_noise_eeg_same_as_real': {c: [med(f'r_{c}_RA'), med(f'r_{c}_NA')] for c in ('EiAsCs', 'EsAiCs', 'EiAiCs')},
            'medians': {f'{k}_{i}': med(f'{k}_{i}') for k in [f'r_{c}' for c in CELLS + SUBCELLS] + [f'norm_{c}' for c in CELLS + SUBCELLS]
                        for i in INPUTS}}


def summarize():
    """CPU, after every appendum unit and every v1 unit is complete. Runs v1.summarize() (unchanged v1 aggregates and rules), then
    aggregates the appendum (per dataset x model x domain: across the 10 units, mean / SD / median / min / max of every quantity,
    unit = person mean of block means) and writes both side by side with v1 R1 and R1b shown next to the appendum rules."""
    plan = read(PLAN); verify(plan)
    missing = [r['id'] for r in plan['rows'] if not (OUT / 'units' / f'{r["id"]}.json').exists()]
    assert not missing, f'{len(missing)} appendum units incomplete'
    V.verify(read(V.OUT / 'plan.json')); V.summarize()
    v1 = json.loads(V.RESULT_FILE.read_text())
    cells = {}
    for row in plan['rows']:
        rec = read(OUT / 'units' / f'{row["id"]}.json')
        assert rec['plan_sha256'] == sha(PLAN) and rec['appendum_sha256'] == plan['appendum_sha256'] and not rec['probe']
        f = Path(rec['dest']) / 'audit.npz'; assert sha(f) == rec['npz_sha256']
        with np.load(f) as z:
            Z = {k: z[k] for k in z.files}
        for t in V.TAGS:
            for d in V.DOMS:
                pre = f'{t}__{d}__'
                if pre + 'block_person' in Z:
                    cells.setdefault(f'{row["dataset"]}/{t}/{d}', []).append(unit_quantities(Z, pre))
    out, side = {}, {}
    for key, units in cells.items():
        agg = {}
        for k in sorted({k for u in units for k in u}):
            v = np.array([u[k] for u in units if u.get(k) is not None], dtype=float)
            agg[k] = {'n_units': int(len(v)), 'mean': float(v.mean()), 'sd': float(v.std(ddof=1)) if len(v) > 1 else None,
                      'median': float(np.median(v)), 'min': float(v.min()), 'max': float(v.max())} if len(v) else {'n_units': 0}
        med = lambda k: agg.get('derived__' + k, {}).get('median')
        out[key] = {'n_units': len(units), 'quantities': agg, 'rules': a1_rules(med)}
        vr = v1['reading_rules'].get(key, {})
        side[key] = {'v1_R1_shared_noise_necessary': vr.get('R1_shared_noise_necessary'),
                     'v1_R1b_calra_noise_necessary': vr.get('R1b_calra_noise_necessary'),
                     'v1_R2_deterministic_key': vr.get('R2_deterministic_key'), 'v1_R3_key_identity': vr.get('R3_key_identity'),
                     'v1_medians': vr.get('medians'),
                     'a1_which_branch': out[key]['rules']['A1_R1_which_branch_coupling_is_necessary'],
                     'a1_calra': out[key]['rules']['A1_R2_calra_coupling_necessary'],
                     'a1_medians_RA': {c: med(f'r_{c}_RA') for c in ('EiAsCs', 'EsAiCs', 'EiAiCs', 'EsAsCi', 'EiAiCi', 'EsAspecCs', 'EsAdropCs')}}
    body = {'version': 'PAPER_MINDMIX_DROPKEY_AUDIT_COMBINED_v1_A1', 'v1_plan_sha256': plan['v1_plan_sha256'],
            'v1_protocol_sha256': plan['v1_protocol_sha256'], 'appendum_plan_sha256': sha(PLAN), 'appendum_sha256': plan['appendum_sha256'],
            'v1_result_file_sha256': sha(V.RESULT_FILE), 'ln_B': V.LN_B, 'side_by_side': side,
            'v1': {'cells': v1['cells'], 'reading_rules': v1['reading_rules']}, 'appendum': out,
            'definitions': {'v1': v1['definitions'], 'appendum': __doc__ + summarize.__doc__ + unit_quantities.__doc__},
            'created': datetime.now().astimezone().isoformat()}
    RESULT_FILE.write_text(json.dumps(body, indent=1) + '\n')
    print(json.dumps(side, indent=1))


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
    plan = read(PLAN); verify(plan)
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
