"""DEP12 source fleet, extension 2: cs_pair_noise at seeds 3401 / 3407 / 3413 (coordinator DECISIONS 2026-10-23 10:55; S20-S22).

Units run trainer_ext2 (cs_pair with i.i.d. unit-Gaussian 32-d targets per view, anchor and update; everything else as the
production cs_pair LoRA runs), 0 -> 10,000 updates each (+30,000), checkpoints 0/500/2500/5000/10000 with resume state.
A V100 smoke (own receipts under source/smoke_ext2/) is required for the current sources: no-audio check of the targets,
noise determinism / independence from the torch RNG, objective parity on noise targets, frozen noise sigma for seed 3401,
deterministic resume equality, timing and the production memory peak. Claims / FAILED markers / preemption as
source_fleet_v2 (signal exit = interrupted, not failed).
CLI (Slurm only): plan | smoke | worker [--max-units N] | status
"""
from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

import numpy as np

from . import source_common as SC, source_fleet_v2 as F2

OUT = SC.SOURCE_OUT
PLAN = OUT / 'plan_ext2.json'
SMOKE = OUT / 'smoke_ext2'
NAME, LANE, SBATCH, SLOTS = 'c3_s35dSx2', 's35_dep12_src_ext2', 'slurm/aln35_dep12_src_ext2.sbatch', 2
SEEDS = (3401, 3407, 3413)
OBJECTIVE = 'cs_pair_noise'
read, write, sha = SC.read, SC.write, SC.sha


def provider_sources():
    here = Path(__file__).parent
    return {f: sha(here / f) for f in ('source_fleet_ext2.py', 'trainer_ext2.py', 'objectives.py', 'training_objectives_torch.py',
                                         'dependence_measure.py', 'source_sampler.py', 'source_common.py', 'devprobe.py')}


def units():
    sel = F2.selection(); assert sel is not None, 'E0 selection missing'
    m = sel['selected_mode']
    return [{'id': F2.unit_id(OBJECTIVE, m, s, F2.TOTAL), 'lane': 'X2', 'objective': OBJECTIVE, 'mode': m, 'seed': s,
             'start': 0, 'end': F2.TOTAL, 'resumes': None, 'role': 'noise_target_control_ext2'} for s in SEEDS]


def make_plan():
    from . import source_sampler as SS, trainer_ext2 as TR
    us = units()
    body = {'version': 'DEP12_SOURCE_PLAN_EXT2_v1', 'units': us, 'budget_updates': len(us) * F2.TOTAL,
            'decision': 'DECISIONS.md 2026-10-23 10:55 (coordinator follow-up ext2) + S20-S22 (engineering)',
            'base_plan_sha256': sha(F2.PLAN), 'e0_selection_sha256': sha(SC.E0_SELECTION), 'selected_mode': us[0]['mode'],
            'streams': {str(s): read(SS.stream_receipt(s))['sha256'] for s in SEEDS},
            'real_sigma_receipts': {str(s): sha(TR.sigma_path(s)) for s in SEEDS},
            'panels_sha256': read(SS.PANELS_RECEIPT)['sha256'], 'coverage_sha256': sha(SS.COVERAGE),
            'noise': {'dim': TR.NOISE_DIM, 'distribution': 'z/||z||, z ~ N(0, I_32), per view x listener episode x anchor x update',
                      'rng': 'numpy PCG64(SeedSequence([seed, %d, u]))' % TR.NOISE_TAG, 'calibration_u': TR.NOISE_CAL_U},
            'training_sources': TR.source_files(), 'lane_module_sha256': sha(__file__),
            'checkpoints': [0, 500, 2500, 5000, 10000], 'transfer_checkpoint': F2.TOTAL}
    assert body['budget_updates'] == 30000
    if PLAN.exists():
        old = read(PLAN)
        drift = [k for k in body if k != 'lane_module_sha256' and old.get(k) != body[k]]
        assert not drift, f'ext2 plan drift {drift}'
        return old
    write(PLAN, {**body, 'created_utc': SC.now()}, freeze=True)
    return read(PLAN)


def plan_ok():
    from . import trainer_ext2 as TR
    return PLAN.exists() and read(PLAN)['training_sources'] == TR.source_files()


def smoke_pass():
    cur = provider_sources()
    for p in sorted(SMOKE.glob('*/receipt.json'), key=lambda p: p.stat().st_mtime, reverse=True):
        r = read(p)
        if r.get('status') == 'pass' and r.get('provider_sources') == cur:
            return p, r
    return None, None


# ----------------------------------------------------------------------------------------------- smoke (GPU)
def noise_audio_check(TR, data, stream, n, updates=20):
    """Targets vs the real env view for the same stream anchors: dimension-pair correlations, in-sample linear R^2 (chance
    = 32/N), within-episode cosine-Gram correlation; determinism and torch-RNG independence."""
    import torch
    Z, Y, gram_r = [], [], []
    for u in range(updates):
        rr = stream['rows'][u].astype(np.int64); oo = stream['off'][u].astype(np.int64)
        A, _ = data.audio(rr.reshape(-1), oo.reshape(-1))
        N = TR.noise_targets(3401, u, rr.shape[0], n, 'cpu')
        Z.append(N['env'].double().numpy())
        Y.append(A['env'].double().cpu().numpy())
        for j in range(rr.shape[0]):
            a = N['env'][j * n:(j + 1) * n].double().numpy(); b = A['env'][j * n:(j + 1) * n].double().cpu().numpy()
            iu = np.triu_indices(n, 1)
            gram_r.append(float(np.corrcoef((a @ a.T)[iu], (b @ b.T)[iu])[0, 1]))
    Z = np.concatenate(Z); Y = np.concatenate(Y); N_ = len(Z)
    Zc, Yc = Z - Z.mean(0), Y - Y.mean(0)
    C = (Zc.T @ Yc) / np.sqrt((Zc ** 2).sum(0)[:, None] * (Yc ** 2).sum(0)[None, :])
    X = np.c_[np.ones(N_), Z]; W, *_ = np.linalg.lstsq(X, Y, rcond=None); R2 = 1 - ((Y - X @ W) ** 2).sum() / (Yc ** 2).sum()
    st0 = torch.get_rng_state().clone()
    a1 = TR.noise_rows(3401, 7, (3, 2, n)); a2 = TR.noise_rows(3401, 7, (3, 2, n))
    out = {'anchors': N_, 'max_abs_dim_corr': float(np.abs(C).max()), 'mean_abs_dim_corr': float(np.abs(C).mean()),
           'null_scale_1_over_sqrt_n': 1 / math.sqrt(N_), 'linear_R2_env_from_noise_in_sample': float(R2),
           'linear_R2_chance_32_over_n': 32 / N_, 'gram_corr_mean': float(np.mean(gram_r)), 'gram_corr_sd': float(np.std(gram_r)),
           'gram_corr_episodes': len(gram_r), 'gram_null_scale_1_over_sqrt_pairs': 1 / math.sqrt(n * (n - 1) / 2),
           'deterministic': bool(np.array_equal(a1, a2)),
           'differs_across_updates': not np.allclose(TR.noise_rows(3401, 7, (1,)), TR.noise_rows(3401, 8, (1,))),
           'differs_across_seeds': not np.allclose(TR.noise_rows(3401, 7, (1,)), TR.noise_rows(3407, 7, (1,))),
           'torch_rng_untouched': bool(torch.equal(st0, torch.get_rng_state())),
           'unit_norm_max_err': float(np.abs(np.linalg.norm(a1, axis=-1) - 1).max())}
    assert out['deterministic'] and out['differs_across_updates'] and out['differs_across_seeds'] and out['torch_rng_untouched']
    assert out['max_abs_dim_corr'] < 6 * out['null_scale_1_over_sqrt_n'] and abs(out['gram_corr_mean']) < 0.02, out
    return out


def noise_objective_parity(TR, sig_n, stream, n):
    """centred CS on noise targets: torch value == NumPy reference; null term carries gradient."""
    import torch
    from . import dependence_measure as DM, objectives as OBJ
    z = TR.noise_rows(3401, 0, (3, 2, n)); P = stream['perm'][0, 0].astype(np.int64); out = {}
    rng = np.random.default_rng(0)
    for k, v in enumerate(TR.VIEWS):
        u = torch.nn.functional.normalize(torch.as_tensor(rng.standard_normal((n, 32))), dim=1).requires_grad_(True)
        y = torch.as_tensor(z[k, 0])
        su, sy = sig_n['views'][v]['sigma_u'], sig_n['views'][v]['sigma_y']
        loss, st = OBJ.episode_loss('cs_pair', u, y, sigma_u=su, sigma_y=sy, perms=P)
        K, L = DM.gaussian_gram(u.detach().numpy(), su), DM.gaussian_gram(y.numpy(), sy)
        ref = DM.parzen_cs(K, L)['raw_cs_nats'] - float(np.mean([DM.parzen_cs(K, L[np.ix_(p, p)])['raw_cs_nats'] for p in P]))
        g = torch.autograd.grad(loss, u)[0]
        out[v] = {'centered_torch': st['centered_cs_nats'], 'centered_numpy': ref, 'abs_diff': abs(st['centered_cs_nats'] - ref),
                  'grad_norm': float(g.norm()), 'sigma_y_noise': sy}
        assert out[v]['abs_diff'] < 1e-8 and out[v]['grad_norm'] > 0
    return out


def smoke():
    import torch
    from . import source_sampler as SS, trainer_ext2 as TR
    job = os.environ['SLURM_JOB_ID']; d = SMOKE / job; d.mkdir(parents=True, exist_ok=True, mode=0o700)
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    rec = {'status': 'running', 'job': job, 'provider_sources': provider_sources(), 'device': torch.cuda.get_device_name(0),
           'started_utc': SC.now(), 'checks': {}, 'timing': {}}
    probe = SC.SOURCE_STORE / 'smoke_ext2' / job
    try:
        make_plan()
        pool = SS.Pool(); n = SS.anchors_per_person(); stream = SS.load_stream(3401); P, _ = SS.load_panels()
        data = SS.SourceData(pool, np.r_[stream['rows'][:20].reshape(-1), P['fit_rows'], P['dev_rows']], torch.device('cuda'))
        rec['checks']['noise_carries_no_audio'] = noise_audio_check(TR, data, stream, n); write(d / 'receipt.json', rec)
        model, groups, info = TR.build_model('lora', 3401, 'cuda'); panels = TR.Panels(pool, data)
        sig, _ = TR.calibrate_sigmas(3401, model, panels)
        sig_n = TR.calibrate_noise_sigmas(3401, panels, sig)
        rec['sigmas_noise_s3401'] = {v: {k: sig_n['views'][v][k] for k in ('sigma_u', 'sigma_y')} for v in TR.VIEWS}
        rec['checks']['noise_objective_parity'] = noise_objective_parity(TR, sig_n, stream, n)
        del model, data; torch.cuda.empty_cache(); write(d / 'receipt.json', rec)
        a, b = probe / 'resumeA', probe / 'resumeB'; q = lambda *x, **k: None
        TR.train(OBJECTIVE, 'lora', 3401, 6, probe_dir=a, deterministic=True, log=q)
        TR.train(OBJECTIVE, 'lora', 3401, 6, probe_dir=b, deterministic=True, stop_after=3, log=q)
        TR.train(OBJECTIVE, 'lora', 3401, 6, probe_dir=b, deterministic=True, log=q)
        name = SC.run_name(OBJECTIVE, 'lora', 3401)
        sa = torch.load(a / 'store' / name / 'resume.pt', map_location='cpu', weights_only=False)
        sb = torch.load(b / 'store' / name / 'resume.pt', map_location='cpu', weights_only=False)
        dm = max(float((sa['model'][k].float() - sb['model'][k].float()).abs().max()) for k in sa['model'])
        do = max(float((st[f] - sb['optimizer']['state'][k][f]).abs().max()) for k, st in sa['optimizer']['state'].items()
                 for f in ('exp_avg', 'exp_avg_sq'))
        rec['checks']['resume'] = {'max_abs_diff_model': dm, 'max_abs_diff_adam_moments': do, 'exact': dm == 0.0 and do == 0.0,
                                   'steps': 6, 'split_at': 3}
        assert sa['step'] == sb['step'] == 6 and dm < 1e-5, rec['checks']['resume']
        torch.use_deterministic_algorithms(False); torch.backends.cudnn.deterministic = False
        ra = read(a / 'out' / name / 'receipt.json')
        rec['checks']['trainer_receipt'] = {k: ra.get(k) for k in ('training_targets', 'sigmas', 'sigmas_real_audio_for_diagnostics',
                                                                    'update1_inert_gradient', 'update1_gradient_check', 'b0_equal_at_step0')}
        assert ra['training_targets'].startswith('iid_unit_gaussian_noise_32d')
        write(d / 'receipt.json', rec)
        t = time.time(); r = TR.train(OBJECTIVE, 'lora', 3401, 60, probe_dir=probe / 'timing', log=q); un = r['units'][-1]
        rec['timing'][f'{OBJECTIVE}.lora'] = {'updates': 60, 'seconds_per_update': un['seconds_per_update'], 'gpu_peak_mb': un['gpu_peak_mb'],
                                              'gpu_peak_reserved_mb': un['gpu_peak_reserved_mb'], 'gpu_total_mb': un['gpu_total_mb'],
                                              'wall_seconds_incl_setup': time.time() - t}
        write(d / 'receipt.json', rec)
        r = TR.train(OBJECTIVE, 'lora', 3401, 3, probe_dir=probe / 'peak', log=q, bank_end=F2.TOTAL); un = r['units'][-1]
        rec['production_peak'] = {'lora': {'gpu_peak_mb': un['gpu_peak_mb'], 'gpu_peak_reserved_mb': un['gpu_peak_reserved_mb'],
                                           'gpu_total_mb': un['gpu_total_mb'], 'bank_nbytes': un['bank_nbytes'],
                                           'bank_rows_updates': un['bank_rows_updates']}}
        rec['status'] = 'pass'
    except BaseException:
        rec.update(status='failed', traceback=traceback.format_exc())
        raise
    finally:
        rec['finished_utc'] = SC.now()
        write(d / 'receipt.json', rec)


# ----------------------------------------------------------------------------------------------- lane
def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': len(SEEDS), 'slots': SLOTS,
          'initial': [], 'submit': []}
    if not PLAN.exists():
        return st
    if not plan_ok():
        return {**st, 'state': 'source_drift_review'}
    p, _ = smoke_pass()
    if p is None:
        cur = [(read(q), time.time() - q.stat().st_mtime) for q in SMOKE.glob('*/receipt.json')]
        cur = [(r, age) for r, age in cur if r.get('provider_sources') == provider_sources()]
        if any(r.get('status') == 'failed' for r, _ in cur):
            return {**st, 'state': 'engineering_probe_failed'}
        if not any(r.get('status') == 'running' and age < 3 * 3600 for r, age in cur):
            return {**st, 'state': 'ready', 'ready': 1, 'slots': 1, 'submit': [SBATCH, 'smoke']}
        return {**st, 'state': 'waiting_smoke'}
    us = units()
    remaining = [u for u in us if not F2.done(u)]
    st['remaining'] = len(remaining)
    if not remaining:
        return {**st, 'state': 'complete'}
    if any(F2.failed(u) for u in remaining):
        return {**st, 'state': 'failed_unit_review'}
    return {**st, 'state': 'ready', 'ready': len(remaining), 'submit': [SBATCH, 'worker', '--max-units', '1']}


def claim_and_run(u):
    F2.CLAIMS.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (F2.CLAIMS / f"{SC.run_name(u['objective'], u['mode'], u['seed'])}.lock").open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 'busy'
        if F2.done(u) or F2.failed(u):
            return 'skip'
        cmd = [sys.executable, '-B', '-u', '-m', 'auditory_alignment_v3.dep12.trainer_ext2', 'run', '--objective', u['objective'],
               '--mode', u['mode'], '--seed', str(u['seed']), '--end', str(u['end'])]
        rc = subprocess.run(cmd).returncode
        if rc == 0 and F2.done(u):
            return 'complete'
        if rc < 0 or F2._stop['signal'] is not None:
            return 'interrupted'
        write(F2.run_out(u) / f"FAILED_to{u['end']}.json", {'job': os.environ.get('SLURM_JOB_ID'), 'returncode': rc, 'unit': u,
                                                             'utc': SC.now(), 'note': 'non-zero exit; review before release'})
        return 'failed'


def worker(max_units):
    signal.signal(signal.SIGTERM, F2._on_term)
    p, _ = smoke_pass(); assert p is not None, 'no passing ext2 smoke receipt for the current sources'
    assert plan_ok(), 'ext2 plan missing or training sources drifted'
    count = 0
    for u in units():
        if F2.done(u) or F2.failed(u):
            continue
        res = claim_and_run(u)
        print(u['id'], res, flush=True)
        if res == 'failed':
            raise RuntimeError(f"unit {u['id']} failed")
        if res == 'interrupted':
            return
        if res == 'complete':
            count += 1
        if count >= max_units:
            break


def status():
    out = {'plan': PLAN.exists(), 'plan_ok': plan_ok() if PLAN.exists() else None, 'smoke': str(smoke_pass()[0]), 'lane': fleet_status(),
           'units': {u['id']: ('complete' if F2.done(u) else 'FAILED' if F2.failed(u) else 'planned') for u in units()}}
    print(json.dumps(out, indent=1, default=str))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['plan', 'smoke', 'worker', 'status'])
    ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'Slurm only'
    os.umask(0o077)
    if a.cmd == 'plan':
        print(json.dumps({k: v for k, v in make_plan().items() if k != 'training_sources'}, default=str))
    elif a.cmd == 'smoke':
        smoke()
    elif a.cmd == 'worker':
        worker(a.max_units)
    else:
        status()


if __name__ == '__main__':
    main()
