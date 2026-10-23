"""DEP12 source fleet, extension 3: ssl_continue at seeds 3401 / 3407 / 3413 (coordinator DECISIONS 2026-10-23 11:55; S23-S25).

Units run trainer_ext3 (audio-free CBraMod-style masked-patch reconstruction with the Stage1 proj_out head; everything else as
the production cs_pair LoRA runs), 0 -> 10,000 updates each (+30,000), checkpoints 0/500/2500/5000/10000 with resume state.
A V100 smoke (receipts under source/smoke_ext3/) is required for the current sources: reconstruction-head identity with the
Stage1 proj_out, mask determinism / torch-RNG independence, the fixed-mask evaluation MSE decreasing over 500 real-schedule
updates, deterministic resume equality, timing and the production memory peak. Claims / FAILED markers / preemption as
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
PLAN = OUT / 'plan_ext3.json'
AMEND = OUT / 'plan_ext3_amend1.json'     # S26: training sources after the external-mask fix (plan_ext3.json stays frozen)
SMOKE = OUT / 'smoke_ext3'
NAME, LANE, SBATCH, SLOTS = 'c3_s35dSx3', 's35_dep12_src_ext3', 'slurm/aln35_dep12_src_ext3.sbatch', 2
SEEDS = (3401, 3407, 3413)
OBJECTIVE = 'ssl_continue'
read, write, sha = SC.read, SC.write, SC.sha


def provider_sources():
    here = Path(__file__).parent
    return {f: sha(here / f) for f in ('source_fleet_ext3.py', 'trainer_ext3.py', 'objectives.py', 'training_objectives_torch.py',
                                         'dependence_measure.py', 'source_sampler.py', 'source_common.py', 'devprobe.py')}


def units():
    sel = F2.selection(); assert sel is not None, 'E0 selection missing'
    m = sel['selected_mode']
    return [{'id': F2.unit_id(OBJECTIVE, m, s, F2.TOTAL), 'lane': 'X2', 'objective': OBJECTIVE, 'mode': m, 'seed': s,
             'start': 0, 'end': F2.TOTAL, 'resumes': None, 'role': 'ssl_domain_adaptation_control_ext3'} for s in SEEDS]


def make_plan():
    from . import source_sampler as SS, trainer_ext3 as TR
    us = units()
    body = {'version': 'DEP12_SOURCE_PLAN_EXT3_v1', 'units': us, 'budget_updates': len(us) * F2.TOTAL,
            'decision': 'DECISIONS.md 2026-10-23 11:55 (coordinator follow-up ext3) + S23-S25 (engineering)',
            'base_plan_sha256': sha(F2.PLAN), 'e0_selection_sha256': sha(SC.E0_SELECTION), 'selected_mode': us[0]['mode'],
            'streams': {str(s): read(SS.stream_receipt(s))['sha256'] for s in SEEDS},
            'real_sigma_receipts': {str(s): sha(TR.sigma_path(s)) for s in SEEDS},
            'panels_sha256': read(SS.PANELS_RECEIPT)['sha256'], 'coverage_sha256': sha(SS.COVERAGE),
            'ssl': {'mask': 'Bernoulli(%.1f) per channel patch (CBraMod generate_mask)' % TR.SSL_MASK_RATIO,
                    'rng': 'numpy PCG64(SeedSequence([seed, %d, u]))' % TR.SSL_TAG, 'eval_u': TR.SSL_EVAL_U,
                    'head': 'Stage1 proj_out.0 (Linear 200->200), strict, trainable', 'loss': 'MSE(mean) on masked tokens of 0.15*z, per episode, listeners averaged',
                    'source': 'github__wjq-learning__CBraMod pretrain_trainer.py / pretrain_main.py / utils/util.py'},
            'training_sources': TR.source_files(), 'lane_module_sha256': sha(__file__),
            'checkpoints': [0, 500, 2500, 5000, 10000], 'transfer_checkpoint': F2.TOTAL}
    assert body['budget_updates'] == 30000
    if PLAN.exists():
        old = read(PLAN)
        drift = [k for k in body if k not in ('lane_module_sha256', 'training_sources') and old.get(k) != body[k]]
        assert not drift, f'ext3 plan drift {drift}'
        if bound_sources() != body['training_sources']:
            make_amendment(old, body['training_sources'])
        return old
    write(PLAN, {**body, 'created_utc': SC.now()}, freeze=True)
    return read(PLAN)


def bound_sources():
    return read(AMEND)['training_sources'] if AMEND.exists() else read(PLAN)['training_sources']


def make_amendment(old, current):
    """Frozen once: the S26 fix (external masking) changed trainer_ext3 before any ext3 training update existed."""
    assert not AMEND.exists(), 'a further source change needs a new amendment version'
    runs = [u['id'] for u in units() if (F2.run_out(u) / 'receipt.json').exists()]
    assert not runs, f'ext3 runs already exist: {runs}'
    write(AMEND, {'version': 'DEP12_SOURCE_PLAN_EXT3_AMEND1', 'base_plan_sha256': sha(PLAN), 'reason': 'DECISIONS S26 (CUDA index_put defect in '
                  'CBraMod mask branch; identical masking applied outside the net); failed smoke 1059742 had no training update',
                  'previous_training_sources': old['training_sources'], 'training_sources': current, 'created_utc': SC.now()}, freeze=True)


def plan_ok():
    from . import trainer_ext3 as TR
    return PLAN.exists() and bound_sources() == TR.source_files()


def smoke_pass():
    cur = provider_sources()
    for p in sorted(SMOKE.glob('*/receipt.json'), key=lambda p: p.stat().st_mtime, reverse=True):
        r = read(p)
        if r.get('status') == 'pass' and r.get('provider_sources') == cur:
            return p, r
    return None, None


# ----------------------------------------------------------------------------------------------- smoke (GPU)
def smoke():
    import torch
    from . import trainer_ext3 as TR
    job = os.environ['SLURM_JOB_ID']; d = SMOKE / job; d.mkdir(parents=True, exist_ok=True, mode=0o700)
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    rec = {'status': 'running', 'job': job, 'provider_sources': provider_sources(), 'device': torch.cuda.get_device_name(0),
           'started_utc': SC.now(), 'checks': {}, 'timing': {}}
    probe = SC.SOURCE_STORE / 'smoke_ext3' / job; q = lambda *x, **k: None
    name = SC.run_name(OBJECTIVE, 'lora', 3401)
    try:
        make_plan()
        from auditory_alignment_v2.foundation_adapter import CBRAMOD_W
        sd = torch.load(CBRAMOD_W, map_location='cpu', weights_only=True)
        m0, _, _ = TR.build_model('lora', 3401, 'cpu'); h = TR.attach_recon_head(m0, 'cpu')
        st0 = torch.get_rng_state().clone()
        k1 = TR.ssl_mask(3401, 5, 128, 64, 'cpu'); k2 = TR.ssl_mask(3401, 5, 128, 64, 'cpu')
        c = {'head_equals_stage1_proj_out': bool(torch.equal(h.weight, sd['proj_out.0.weight']) and torch.equal(h.bias, sd['proj_out.0.bias'])),
             'mask_deterministic': bool(torch.equal(k1, k2)), 'mask_fraction': float(k1.float().mean()),
             'mask_differs_across_updates': not torch.equal(k1, TR.ssl_mask(3401, 6, 128, 64, 'cpu')),
             'mask_differs_across_seeds': not torch.equal(k1, TR.ssl_mask(3407, 5, 128, 64, 'cpu')),
             'torch_rng_untouched': bool(torch.equal(st0, torch.get_rng_state()))}
        with torch.no_grad():   # S26: external masking == CBraMod's internal mask branch (CPU, eval mode)
            m0.eval(); xx = 0.15 * torch.randn(8, 64, 1, 200); mk = TR.ssl_mask(3401, 9, 8, 64, 'cpu')
            ya = m0.bb.net(xx, mask=mk); yb = m0.bb.net(TR.apply_mask(m0, xx, mk))
        c['external_mask_equals_cbramod_branch_max_abs_diff_cpu'] = float((ya - yb).abs().max())
        rec['checks']['recon_head_and_mask'] = c
        assert all(c[k] for k in ('head_equals_stage1_proj_out', 'mask_deterministic', 'mask_differs_across_updates',
                                  'mask_differs_across_seeds', 'torch_rng_untouched')), c
        assert c['external_mask_equals_cbramod_branch_max_abs_diff_cpu'] == 0.0, c
        del m0, sd; write(d / 'receipt.json', rec)
        t = time.time(); r = TR.train(OBJECTIVE, 'lora', 3401, 500, probe_dir=probe / 'decrease', log=q); un = r['units'][-1]
        diags = read(probe / 'decrease' / 'out' / name / 'diagnostics.json')['diags']
        st = torch.load(probe / 'decrease' / 'store' / name / 'step500.state.pt', map_location='cpu', weights_only=False)
        tl = [x['loss'] for x in st['logs']]
        e0, e1 = diags[0]['ssl'], diags[-1]['ssl']
        rec['checks']['loss_decrease'] = {'eval_fixed_mask_mse_step0': e0['ssl_eval_mse'], 'eval_fixed_mask_mse_step500': e1['ssl_eval_mse'],
                                          'eval_masked_input_power': e0['ssl_eval_input_power_masked'], 'eval_rows': e0['ssl_eval_rows'],
                                          'diag_steps': [x['step'] for x in diags],
                                          'train_loss_mean_first50': float(np.mean(tl[:50])), 'train_loss_mean_last50': float(np.mean(tl[-50:])),
                                          'updates': 500, 'schedule': 'real (warmup 500: lr reaches 3e-4 at update 500)',
                                          'decreased': e1['ssl_eval_mse'] < e0['ssl_eval_mse']}
        rec['checks']['trainer_receipt'] = {k: r.get(k) for k in ('training_objective', 'update1_inert_gradient', 'update1_gradient_check',
                                                                   'b0_equal_at_step0')}
        rec['timing'][f'{OBJECTIVE}.lora'] = {'updates': 500, 'seconds_per_update': un['seconds_per_update'], 'gpu_peak_mb': un['gpu_peak_mb'],
                                              'gpu_peak_reserved_mb': un['gpu_peak_reserved_mb'], 'gpu_total_mb': un['gpu_total_mb'],
                                              'wall_seconds_incl_setup': time.time() - t, 'note': 'loop time includes the step-500 snapshot'}
        write(d / 'receipt.json', rec)
        assert rec['checks']['loss_decrease']['decreased'], rec['checks']['loss_decrease']
        assert r['training_objective'].startswith('ssl_masked_patch_reconstruction')
        a, b = probe / 'resumeA', probe / 'resumeB'
        TR.train(OBJECTIVE, 'lora', 3401, 6, probe_dir=a, deterministic=True, log=q)
        TR.train(OBJECTIVE, 'lora', 3401, 6, probe_dir=b, deterministic=True, stop_after=3, log=q)
        TR.train(OBJECTIVE, 'lora', 3401, 6, probe_dir=b, deterministic=True, log=q)
        sa = torch.load(a / 'store' / name / 'resume.pt', map_location='cpu', weights_only=False)
        sb = torch.load(b / 'store' / name / 'resume.pt', map_location='cpu', weights_only=False)
        dm = max(float((sa['model'][k].float() - sb['model'][k].float()).abs().max()) for k in sa['model'])
        do = max(float((v[f] - sb['optimizer']['state'][k][f]).abs().max()) for k, v in sa['optimizer']['state'].items()
                 for f in ('exp_avg', 'exp_avg_sq'))
        rec['checks']['resume'] = {'max_abs_diff_model': dm, 'max_abs_diff_adam_moments': do, 'exact': dm == 0.0 and do == 0.0,
                                   'steps': 6, 'split_at': 3, 'recon_in_state': any(k.startswith('recon.') for k in sa['model'])}
        assert sa['step'] == sb['step'] == 6 and dm < 1e-5 and rec['checks']['resume']['recon_in_state'], rec['checks']['resume']
        torch.use_deterministic_algorithms(False); torch.backends.cudnn.deterministic = False
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
        cmd = [sys.executable, '-B', '-u', '-m', 'auditory_alignment_v3.dep12.trainer_ext3', 'run', '--objective', u['objective'],
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
    p, _ = smoke_pass(); assert p is not None, 'no passing ext3 smoke receipt for the current sources'
    assert plan_ok(), 'ext3 plan missing or training sources drifted'
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
