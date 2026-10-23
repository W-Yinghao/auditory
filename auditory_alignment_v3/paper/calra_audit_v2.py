"""Paper W5 audit v2: dependency-scoped correction of the calra_cbramod audit (training rows, checkpoints, frozen units and
readouts unchanged; the v1 audit and W5_AUDIT.json are kept as they are).

Why v2. The v1 audit (calra_cbramod.run_audit) scores in eval mode only. Read-only diagnosis of the CALRA seed-3401 final
checkpoint on its own last training blocks (R1 stream, updates 9998-9999, query blocks): eval mode gives ClipLoss ln 32 with
every embedding constant across rows (cosine 1.000000), while train mode reproduces the logged training loss (0.0011, top-1
1.0); train mode gives the same 0.0011 with noise EEG, wrong audio and with all 32 rows fed identical inputs; switching ONLY
the CALRA block to train mode gives 0.0009 and everything except CALRA gives ln 32. The objective is met by CALRA's internal
dropout noise, which a single CALRA(e_i, x_i) call shares between fused_eeg_i and aligned_audio_i (the official pairing), not
by any EEG or audio content. PROJ_NCE (no shared path) stays at ln 32 in both modes. v1 therefore measured the eval-mode
representation correctly, but could not show the training-time mechanism.

v2 per production unit, on the v1 blocks (calra_cbramod.audit_source / audit_dtu, same seeds and geometry, unchanged code with
block_eval replaced by block_eval_v2), in two modes:
  eval   all modules eval (reproduces v1; max |v2 - v1| recorded per unit),
  train  all modules train exactly as in training (CALRA / wav2vec2 / CBraMod dropout, SpecAugment), torch and numpy RNG
         seeded per domain.
Per block: ClipLoss and in-batch top-1 from ONE CALRA call per row (the training pairing) for real+correct, real+wrong,
noise+correct and identical inputs (row 0's EEG crops and audio embedding repeated over the 32 rows), and pre-fusion;
official forward_contrastive call structure for each target slot ((f, g_t) = CALRA(e, t); g_c = CALRA(e, c)[1]) giving the
privileged-slot scorer (pA > pB, both slot orders) and the blind order-symmetrised margin
m = 1/2[(s(c|c) - s(w|c)) - (s(w|w) - s(c|w))], s(x|t) = exp(ls) cos(f_t, g_x), for real and noise EEG.
Train mode also stores f / g (float32) of the one-call pairs for real+correct, noise+correct and identical inputs; the
summary computes per-block CS excess dependence of f on g (paper.cs_atlas = aln41.cs_qmi_reference formula, roll null).
CLI: --make-plan | --smoke | --worker | --unit ID | --summarize ; CPU preview: preview_source(max_blocks) (no writes).
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from . import calra_cbramod as W

OUT = W.OUT / 'audit_v2'
STORE = W.STORE / 'audit_v2'
RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/paper/calra_cbramod'
MODES = ('eval', 'train')
RNG_SEED = W.AUDIT_SEED + 100
NAME, LANE, SBATCH = 'c3_s35calra', 's35_paper_calra_audit2', 'slurm/aln35_paper_calra_audit2.sbatch'
read, write, sha = W.read, W.write, W.sha


def sources():
    repo = Path(core.REPO)
    return {str(p): sha(p) for p in (Path(__file__), repo / 'auditory_alignment_v3/paper/calra_cbramod.py')}


def production_rows():
    return [r for r in W.all_rows() if r['stage'] == 'production']


def make_plan():
    rows = []
    for r in production_rows():
        u = Path(r['base']) / 'units' / f'{r["id"]}.json'; v1 = W.OUT / 'audit' / f'{r["id"]}.json'
        assert read(u)['status'] == 'complete' and v1.exists(), r['id']
        rows.append({'id': r['id'], 'arm': r['arm'], 'seed': r['seed'], 'base': r['base'], 'unit_sha256': sha(u), 'v1_audit_sha256': sha(v1)})
    assert len(rows) == sum(len(v) for v in W.ARM_SEEDS.values())
    body = {'version': 'PAPER_W5_AUDIT_v2', 'w5_plan_sha256': sha(W.OUT / 'plan.json'), 'rows': rows, 'sources': sources(),
            'settings': {'modes': list(MODES), 'rng_seed': RNG_SEED, 'blocks': 'v1 audit blocks (source dev AUDIT_SEED stream; DTU cs test)',
                         'identical_inputs': "row 0's EEG crops and pre-fusion audio embedding repeated over the block",
                         'objective_pairing': 'one CALRA(e_i, x_i) call per row for both sides (training pairing)',
                         'official_scorer': 'forward_contrastive call structure: (f, g_t) = CALRA(e, t); g_c = CALRA(e, c)[1]'},
            'correction': 'v1 audit scored eval mode only; v2 adds training-mode scoring; v1 records and W5_AUDIT.json unchanged',
            'v1_summary_sha256': sha(RESULTS / 'W5_AUDIT.json') if (RESULTS / 'W5_AUDIT.json').exists() else None}
    path = OUT / 'plan.json'
    if path.exists():
        old = read(path); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        OUT.mkdir(parents=True, exist_ok=True, mode=0o700); write(path, {**body, 'created': datetime.now().astimezone().isoformat()}); path.chmod(0o444)
    print('W5 audit v2 plan', sha(path), flush=True)


# ------------------------------------------------------------------------------------------------------------- scoring
def block_eval_v2(model, a, crops, crops_n, x, xw):
    """Drop-in for calra_cbramod.block_eval (same call signature; mode is set by the caller)."""
    import torch
    import torch.nn.functional as F
    e = model.eeg(crops, a); en = model.eeg(crops_n, a)
    es = model.eeg([c[:1].expand_as(c).contiguous() for c in crops], a); xs = x[:1].expand_as(x).contiguous()
    ar = torch.arange(len(e), device=e.device); r = {}
    for name, (ee, xx) in {'real_correct': (e, x), 'real_wrong': (e, xw), 'noise_correct': (en, x), 'identical_inputs': (es, xs)}.items():
        f, g = model.fuse(ee, xx); S = model.clip.get_scores(f, g)            # one call per row for both sides
        r[f'{name}_cliploss'] = F.cross_entropy(S, ar); r[f'{name}_top1'] = (S.argmax(1) == ar).float().mean()
        if name != 'real_wrong':
            r[f'emb_f_{name}'] = f; r[f'emb_g_{name}'] = g
    S = model.clip.get_scores(e, x); r['prefusion_cliploss'] = F.cross_entropy(S, ar); r['prefusion_top1'] = (S.argmax(1) == ar).float().mean()
    scale = model.clip.logit_scale.exp()
    for tag, ee in (('real', e), ('noise', en)):
        s = {}
        for t_name, t, c_name, c in (('correct', x, 'wrong', xw), ('wrong', xw, 'correct', x)):
            f, gt = model.fuse(ee, t); _, gc = model.fuse(ee, c)                # official forward_contrastive structure
            s[(t_name, t_name)] = scale * F.cosine_similarity(f, gt, dim=-1); s[(c_name, t_name)] = scale * F.cosine_similarity(f, gc, dim=-1)
            pA = model.clip.get_probabilities(f, gt).diagonal(); pB = model.clip.get_probabilities(f, gc).diagonal()
            r[f'official_{tag}_target_{t_name}'] = (pA > pB).float()
        r[f'blind_{tag}'] = 0.5 * ((s[('correct', 'correct')] - s[('wrong', 'correct')]) - (s[('wrong', 'wrong')] - s[('correct', 'wrong')]))
    return {k: (v.float() if k.startswith('emb_') else v.double()).cpu().numpy() for k, v in r.items()}


def score(row, dev, domains=('source', 'dtu'), max_blocks=None, cfs=(0, 1)):
    """{mode: {domain: (blocks, timing)}} for one production unit (calra_cbramod audit loops, block_eval -> block_eval_v2)."""
    import torch
    unit = read(Path(row['base']) / 'units' / f'{row["id"]}.json'); ck = unit['final_checkpoint']; assert sha(ck) == unit['final_checkpoint_sha256']
    st = torch.load(ck, map_location='cpu', weights_only=False)
    W.block_eval = block_eval_v2
    out = {m: {} for m in MODES}
    for name, fs in (('source', 64), ('dtu', W.XM.FS_COH)):
        if name not in domains:
            continue
        model, _ = W.build(row['arm'], row['seed'], fs_native=fs); model.load_state_dict(st['model'], strict=True); model.to(dev)
        a = st['a'].to(dev)
        for mode in MODES:
            model.train(mode == 'train'); torch.manual_seed(RNG_SEED); np.random.seed(RNG_SEED)
            with torch.no_grad():
                if name == 'source':
                    out[mode][name] = W.audit_source(model, a, dev, W.AUDIT_UPDATES, max_blocks)
                else:
                    bl, tm = [], {}
                    for cf in cfs:
                        b, t = W.audit_dtu(model, a, cf, dev, max_blocks); bl += b; tm[f'cf{cf}'] = t
                    out[mode][name] = (bl, tm)
        del model
        if dev.type == 'cuda':
            torch.cuda.empty_cache()
    return out


def assemble(bl, keep_emb):
    for i, b in enumerate(bl):
        b['block'] = np.repeat(i, len(b['block']))
    keys = [k for k in bl[0] if keep_emb or not k.startswith('emb_')]
    arr = {f'blk_{k}': np.array([b[k] for b in bl]) for k in keys if np.ndim(bl[0][k]) == 0}
    arr.update({k: np.concatenate([b[k] for b in bl]) for k in keys if np.ndim(bl[0][k]) > 0})
    arr['blk_n'] = np.array([len(b['block']) for b in bl])
    return arr


CONTINUOUS = ('blk_real_correct_cliploss', 'blk_real_wrong_cliploss', 'blk_noise_correct_cliploss', 'blk_prefusion_cliploss',
              'blind_real', 'blind_noise')
DISCRETE = ('blk_real_correct_top1', 'blk_noise_correct_top1', 'official_real_target_correct', 'official_real_target_wrong')


def v1_check(arr, v1_npz):
    """Eval-mode v2 vs v1 on the same blocks: max |diff| of the continuous metrics (asserted < 1e-3) and the agreement of the
    discrete ones (argmax / pA > pB of near-constant logits are decided by float noise, so they are reported, not asserted)."""
    with np.load(v1_npz) as z:
        n, m = len(arr['blk_n']), len(arr['blind_real'])
        cont = {k: float(np.max(np.abs(arr[k] - z[k][:(n if k.startswith('blk_') else m)]))) for k in CONTINUOUS}
        disc = {k: float(np.mean(arr[k] == z[k][:(n if k.startswith('blk_') else m)])) for k in DISCRETE}
    return {'max_abs': cont, 'agreement': disc}


def run_unit(row, probe=False):
    import torch
    t0 = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']
    res = score(row, dev, max_blocks=W.SMOKE_BLOCKS if probe else None, cfs=(0,) if probe else (0, 1))
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    v1_dest = Path(read(W.OUT / 'audit' / f'{row["id"]}.json')['dest']); npz, checks, timing = {}, {}, {}
    for mode, doms in res.items():
        for dom, (bl, tm) in doms.items():
            arr = assemble(bl, keep_emb=(mode == 'train')); p = dest / f'{mode}_{dom}.npz'; np.savez_compressed(p, **arr)
            npz[f'{mode}_{dom}'] = sha(p); timing[f'{mode}_{dom}'] = tm
            if mode == 'eval':
                checks[dom] = v1_check(arr, v1_dest / f'{dom}.npz')
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'dest': str(dest), 'npz_sha256': npz,
           'v1_reproduction_max_abs': checks, 'timing': timing, 'seconds': time.time() - t0,
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'peak_rss_gb': W.peak_rss_gb(), 'device': torch.cuda.get_device_name(0), 'job': job}
    assert all(v < 1e-3 for c in checks.values() for v in c['max_abs'].values()), checks
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], row['arm'], 'audit v2 complete', round(rec['seconds'], 1), checks, flush=True)
    return rec


def preview_source(max_blocks=8, rows=None):
    """CPU, no writes: block means of the source dev audit in both modes for each production unit."""
    import torch
    out = {}
    for row in rows or production_rows():
        res = score(row, torch.device('cpu'), domains=('source',), max_blocks=max_blocks)
        out[f'{row["arm"]}/seed{row["seed"]}'] = {mode: block_means(assemble(res[mode]['source'][0], keep_emb=False)) for mode in MODES}
    return out


def block_means(arr):
    m = {k[4:]: float(arr[k].mean()) for k in arr if k.startswith('blk_') and k != 'blk_n'}
    for tag in ('real', 'noise'):
        b = arr[f'blind_{tag}']; m[f'blind_acc_{tag}'] = float(np.mean((b > 0) + 0.5 * (b == 0)))
        for slot in ('correct', 'wrong'):
            m[f'official_{tag}_target_{slot}_wins'] = float(arr[f'official_{tag}_target_{slot}'].mean())
    m['chance_top1'] = float(np.mean(1.0 / arr['blk_n'])); m['n_blocks'] = int(len(arr['blk_n']))
    return m


# ------------------------------------------------------------------------------------------------------------- fleet
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
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 4, 'slots': 1, 'initial': [], 'submit': []}
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
                raise RuntimeError('W5 audit v2 unit failed')
            return


def smoke(plan):
    job = os.environ['SLURM_JOB_ID']; rec = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
    try:
        for arm in W.ARMS:
            row = next(r for r in plan['rows'] if r['arm'] == arm and r['seed'] == 3401)
            u = run_unit(row, probe=True)
            rec['units'].append({k: u[k] for k in ('row', 'v1_reproduction_max_abs', 'timing', 'seconds', 'gpu_peak_mb', 'peak_rss_gb', 'device')})
        rec['status'] = 'pass'
    except BaseException:
        rec.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', rec)


def summarize():
    """CPU. Per arm x seed x domain x mode: person means of the block metrics (block_means definitions); train mode adds
    per-block CS excess dependence of f on g for real+correct, noise+correct and identical inputs (cs_atlas.person_cells,
    seg = block rows, sigma = cs_atlas.sigma_rule on the domain's real+correct f / g, reused for the other conditions)."""
    from . import cs_atlas as CA
    plan = read(OUT / 'plan.json'); rng = np.random.default_rng(CA.RNG_SEED); res = {}
    for row in plan['rows']:
        p = OUT / 'units' / f'{row["id"]}.json'
        if not p.exists():
            continue
        rec = read(p)
        for key, h in rec['npz_sha256'].items():
            mode, dom = key.split('_', 1); f = Path(rec['dest']) / f'{key}.npz'; assert sha(f) == h
            with np.load(f) as z:
                Z = {k: z[k] for k in z.files}
            nb = len(Z['blk_n']); bp = np.array([Z['person'][Z['block'] == b][0] for b in range(nb)]); per = {}
            if mode == 'train':
                su = CA.sigma_rule(Z['emb_f_real_correct'], rng); sg = CA.sigma_rule(Z['emb_g_real_correct'], rng)
            for b in range(nb):
                ix = np.flatnonzero(Z['block'] == b); sub = {k: (v[b:b + 1] if k.startswith('blk_') else v[ix]) for k, v in Z.items()}
                d = per.setdefault(bp[b], {})
                for k, v in block_means(sub).items():
                    if k != 'n_blocks':
                        d.setdefault(k, []).append(v)
                if mode == 'train' and len(ix) >= 3:
                    for cond in ('real_correct', 'noise_correct', 'identical_inputs'):
                        for _, _, v in CA.person_cells({cond: Z[f'emb_f_{cond}'][ix]}, {cond: Z[f'emb_g_{cond}'][ix]}, np.arange(len(ix)),
                                                       {cond: su}, {cond: sg}):
                            d.setdefault(f'cs_excess_f_on_g/{cond}', []).append(v['excess'])
            people = {q: {k: float(np.mean(v)) for k, v in d.items()} for q, d in per.items()}
            res[f'{row["arm"]}/seed{row["seed"]}/{dom}/{mode}'] = {k: {'person_mean': float(np.mean([d[k] for d in people.values() if k in d])),
                                                                     'n_people': sum(k in d for d in people.values())}
                                                                 for k in sorted({k for d in people.values() for k in d})}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / 'W5_AUDIT_v2.json').write_text(json.dumps({'version': plan['version'], 'plan_sha256': sha(OUT / 'plan.json'),
                                                          'cs_atlas_sha256': sha(CA.__file__), 'cells': res, 'definitions': __doc__ + summarize.__doc__},
                                                         indent=1) + '\n')


def main():
    ap = argparse.ArgumentParser()
    for flag in ('make_plan', 'smoke', 'worker', 'summarize'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = read(OUT / 'plan.json'); assert plan['sources'] == sources(), 'frozen source drift'
    if a.unit:
        run_unit(next(r for r in plan['rows'] if r['id'] == a.unit)); return
    if a.smoke:
        smoke(plan); return
    if a.summarize:
        os.umask(0o022); summarize(); return
    assert a.worker
    worker(plan)


if __name__ == '__main__':
    main()
