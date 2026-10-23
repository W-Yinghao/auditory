"""DEP12 Agent P GPU lane, VERSION 4 (DECISIONS P25): v3 plus the ext3 follow-up arm ssl_continue@{3401,3407,3413} served
by dep12/encoders_v4.py (imports encoders_v3 unchanged); exports through private_features_v4; receipt smoke_v4; mechanism
stage = private_mechanism_v3 (EXT1, EXT2, EXT3 blocks and the manipulation check), marker REC/mechanism_v3.

--- v3 description ---
DEP12 Agent P GPU lane, VERSION 3 (DECISIONS P24): v2 plus the ext2 follow-up arm cs_pair_noise@{3401,3407,3413} served
by dep12/encoders_v3.py (imports encoders_v2 / encoders unchanged); exports through private_features_v3; CPU equivalence
receipt smoke_v3; mechanism stage = private_mechanism_v2 (P23 report plus block EXT2), marker REC/mechanism_v2.

--- v2 description ---
DEP12 Agent P GPU lane, VERSION 2 (DECISIONS P23): private_fleet (v1, untouched) plus the extension-1 mechanism controls
raw_cs@3407/3413 and cs_pair_wrong@3407/3413, served by dep12/encoders_v2.py (which imports encoders.py unchanged). Same
specs / units / CPU-stage directories and unit-id rule as v1; exports go through private_features_v2 (the v1 export with the
encoder resolved by encoders_v2). The v1 GPU smoke passed; v2 adds a CPU equivalence receipt (smoke_v2) instead of a new GPU
smoke. Added CPU stage: private_mechanism (mechanism-control report, BDF + MFF) whenever its inputs change.

--- v1 description (unchanged below) ---
DEP12 Agent P GPU lane: private feature export units (one per encoder), fleet-ready (paper/encoders.py convention).

Unit = one encoder x all 5 outer folds (private_features.export). Specs are frozen one file per unit (0444) under
REC/features_v1/specs before the unit runs; the unit id hashes the encoder name, the frozen binding sha256 and the export
version. Readiness = dep12.encoders REGISTRY state 'available' after refresh(). Order: B0, REVE0, MINDMIX_branch, the twelve
ALN4.1 arms (seed 3401 first), then the eleven new-round production arms as they become available.

Smoke (GPU, engineering only, no outcome threshold): resampler checks; probe export (6 children, fold 0) for one encoder of
each family (aln41_TCS@3401, REVE0, MINDMIX_branch): strict loads, finite U, pad check, timing and peak memory; then the
complete B0 unit through the ordinary claim / run_unit path (full-scale memory and per-fold time on all 64 children).
A failed unit writes units/<id>.FAILED.json; a preempted / signalled subprocess (negative return code) does not.

Post-processing (CPU work inside the lane's jobs, never blocking GPU units): after its units, every worker runs `post`:
private_use for each complete unit without U0/δ outputs, selection for each (candidate set, seed) whose four candidates have
U0 outputs, then private_analysis whenever its inputs changed. Each stage is a subprocess; a failure writes
post_failed/<stage>.json and does not mark the GPU unit failed.

Commands (Slurm only): --register | --smoke | --worker [--max-units N] | --unit ID | --post | --status
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

from . import private_features as PF
from . import private_features_v4 as PF2

BASE = PF.REC / 'features_v1'
STORE = PF.STORE / 'features_v1'
EXPORT_VERSION = 'DEP12_PRIVATE_EXPORT_v1'
NAME, LANE, SBATCH = 'c3_s35dPfeat', 's35_dep12_private_features', 'slurm/aln35_dep12_priv_feat_v4.sbatch'
SLOTS, PER_JOB = 2, 4
REUSED = (['B0', 'REVE0', 'MINDMIX_branch']
          + [f'aln41_{a}@{s}' for s in (3401, 3407, 3413) for a in ('TCS', 'TNCE', 'GCS', 'WRONG')])
NEW = ([f'{o}@{s}' for s in (3401, 3407, 3413) for o in ('cs_pair', 'info_nce', 'sigmoid')]
       + ['raw_cs@3401', 'cs_pair_wrong@3401'])
EXT1 = ['raw_cs@3407', 'raw_cs@3413', 'cs_pair_wrong@3407', 'cs_pair_wrong@3413']     # encoders_v2 extension 1
NEW = NEW + EXT1
EXT2 = ['cs_pair_noise@3401', 'cs_pair_noise@3407', 'cs_pair_noise@3413']     # encoders_v3 follow-up ext2
NEW = NEW + EXT2
EXT3 = ['ssl_continue@3401', 'ssl_continue@3407', 'ssl_continue@3413']     # encoders_v4 follow-up ext3
NEW = NEW + EXT3
MECH = ['cs_pair', 'raw_cs', 'cs_pair_wrong', 'cs_pair_noise', 'ssl_continue', 'info_nce', 'sigmoid']
SMOKE_ENCODERS = ('aln41_TCS@3401', 'REVE0', 'MINDMIX_branch')
read, write, sha, digest = PF.read, PF.write, PF.sha, PF.digest


def sources():
    files = [Path(__file__), Path(PF.__file__), Path(PF2.__file__), PF.ROOT / 'auditory_alignment_v3/dep12/encoders.py',
             PF.ROOT / 'auditory_alignment_v3/dep12/encoders_v2.py', PF.ROOT / 'auditory_alignment_v3/dep12/encoders_v3.py',
             PF.ROOT / 'auditory_alignment_v3/dep12/encoders_v4.py']
    return {str(p.relative_to(PF.ROOT)): sha(p) for p in files}


def mechanism_inputs():
    """Digest of every U0/δ output the mechanism report reads (BDF use_v1 and MFF use)."""
    files = []
    for o in MECH:
        for s_ in (3401, 3407, 3413):
            n = f'{o}@{s_}'.replace('@', '_at_')
            files += [PF.REC / 'use_v1' / n / 'complete.json', PF.REC / 'mff_v1' / 'use' / f'{n}.json']
    files += [PF.REC / 'use_v1' / 'B0' / 'complete.json', PF.REC / 'mff_v1' / 'use' / 'B0.json']
    have = [p for p in files if p.exists()]
    return digest([[str(p.relative_to(PF.REC)), sha(p)] for p in have]) if have else None


def mechanism_pending(failed):
    cur = mechanism_inputs()
    last = PF.REC / 'mechanism_v3' / 'inputs.json'
    if cur is None or 'mechanism.json' in failed:
        return None
    return cur if (not last.exists() or read(last).get('digest') != cur) else None


POST_SEEDS = (3401, 3407, 3413)


def post_candidates(seed, cset):
    if cset == 'primary':
        return ['B0', f'cs_pair@{seed}', f'info_nce@{seed}', f'sigmoid@{seed}']
    return ['B0', f'aln41_TCS@{seed}', f'aln41_TNCE@{seed}', f'aln41_GCS@{seed}']


def use_done(name):
    return (PF.REC / 'use_v1' / name.replace('@', '_at_') / 'complete.json').exists()


def sel_done(cset, seed):
    return (PF.REC / 'selection_v1' / f'{cset}_s{seed}' / 'complete.json').exists()


def post_failed():
    return sorted(p.name for p in (BASE / 'post_failed').glob('*.json')) if (BASE / 'post_failed').exists() else []


def analysis_inputs():
    files = sorted((PF.REC / 'use_v1').glob('*/complete.json')) + sorted((PF.REC / 'selection_v1').glob('*/complete.json'))
    return digest([[str(p.relative_to(PF.REC)), sha(p)] for p in files]) if files else None


def post_pending():
    done = {s['encoder'] for s in specs() if unit_state(s) == 'complete'}
    failed = set(post_failed())
    todo = [('use', n) for n in [s['encoder'] for s in specs()] if n in done and not use_done(n) and f'use_{n}.json' not in failed]
    for cset in ('primary', 'aln41'):
        for seed in POST_SEEDS:
            if all(use_done(n) for n in post_candidates(seed, cset)) and not sel_done(cset, seed) \
                    and f'selection_{cset}_{seed}.json' not in failed:
                todo.append(('selection', cset, seed))
    last = BASE / 'analysis_inputs.json'
    cur = analysis_inputs()
    if cur and (not last.exists() or read(last).get('digest') != cur) and 'analysis.json' not in failed:
        todo.append(('analysis',))
    if mechanism_pending(failed):
        todo.append(('mechanism',))
    return todo


def post():
    """Run every pending CPU stage once (subprocesses; failures recorded, not raised)."""
    for _ in range(3):
        todo = post_pending()
        if not todo:
            return
        for item in todo:
            if item[0] == 'use':
                cmd, tag = ['auditory_alignment_v3.dep12.private_use', '--encoders', item[1]], f'use_{item[1]}'
            elif item[0] == 'selection':
                cmd, tag = ['auditory_alignment_v3.dep12.selection', '--set', item[1], '--seeds', str(item[2])], f'selection_{item[1]}_{item[2]}'
            elif item[0] == 'mechanism':
                if any(t[0] == 'use' for t in post_pending()):
                    continue
                cmd, tag = ['auditory_alignment_v3.dep12.private_mechanism_v3'], 'mechanism'
            else:
                if any(t[0] not in ('analysis', 'mechanism') for t in post_pending()):
                    continue
                cur = analysis_inputs()
                cmd, tag = ['auditory_alignment_v3.dep12.private_analysis'], 'analysis'
            t0 = time.time()
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', *cmd]).returncode
            if rc < 0:
                raise SystemExit(rc)
            if rc:
                write(BASE / 'post_failed' / f'{tag}.json', {'job': os.environ.get('SLURM_JOB_ID'), 'returncode': rc, 'cmd': cmd,
                                                             'time': datetime.now().astimezone().isoformat()})
            elif item[0] == 'analysis':
                write(BASE / 'analysis_inputs.json', {'digest': cur, 'job': os.environ.get('SLURM_JOB_ID'), 'seconds': time.time() - t0})
            print('post', tag, 'rc', rc, round(time.time() - t0, 1), flush=True)


def unit_id(name, binding_sha):
    return 'DEP12P_' + digest({'encoder': name, 'binding_sha256': binding_sha, 'version': EXPORT_VERSION}, 16)


def specs():
    out = []
    for p in sorted((BASE / 'specs').glob('*.json')):
        out.append(read(p))
    return sorted(out, key=lambda s: s['order'])


def register(names):
    """Freeze one spec per encoder (append-only; existing specs are never rewritten)."""
    bind_sha = PF.sha(PF.BINDING)
    existing = {s['encoder'] for s in specs()}
    order0 = len(existing)
    for j, name in enumerate(n for n in names if n not in existing):
        uid = unit_id(name, bind_sha)
        body = {'id': uid, 'encoder': name, 'binding_sha256': bind_sha, 'version': EXPORT_VERSION, 'order': order0 + j,
                'family': 'new_round' if name in NEW else 'reused', 'created': datetime.now().astimezone().isoformat(),
                'sources_at_registration': sources(), 'store': str(STORE / 'units' / uid), 'results_seen': False}
        PF.write_frozen(BASE / 'specs' / f'{uid}.json', body)
        print('registered', name, uid, flush=True)


def encoder_state(name):
    from . import encoders_v4 as E
    spec = E.REGISTRY.get(name) or E.refresh().get(name)
    if spec is None:
        return 'unknown'
    if not spec.get('servable'):
        return 'not_servable'
    return spec.get('state')


def unit_state(spec, refreshed=None):
    rec = BASE / 'units' / f'{spec["id"]}.json'
    if rec.exists():
        return 'complete'
    if (BASE / 'units' / f'{spec["id"]}.FAILED.json').exists():
        return 'failed'
    st = (refreshed or {}).get(spec['encoder'])
    if st is None:
        st = encoder_state(spec['encoder'])
    return 'ready' if st == 'available' else 'waiting_encoder:' + str(st)


def smoke_receipts():
    """v2: a passing v1 GPU smoke (any v1 sources, same binding) AND a passing v2 CPU equivalence receipt for these sources."""
    out = {'pass': [], 'other': []}
    v1 = [p for p in sorted((BASE / 'smoke').glob('*/receipt.json'))
          if read(p).get('status') == 'pass' and read(p).get('binding_sha256') == PF.sha(PF.BINDING)]
    for p in sorted((BASE / 'smoke_v4').glob('*/receipt.json')):
        r = read(p)
        if r.get('sources') == sources() and r.get('binding_sha256') == PF.sha(PF.BINDING):
            out['pass' if (r.get('status') == 'pass' and v1) else 'other'].append(p)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 0, 'slots': 1, 'initial': [], 'submit': []}
    if not PF.BINDING.exists() or not (BASE / 'specs').exists():
        return st
    sp = specs()
    if not sp:
        return st
    from . import encoders_v4 as E
    E.refresh()
    refreshed = {s['encoder']: encoder_state(s['encoder']) for s in sp}
    states = [unit_state(s, refreshed) for s in sp]
    left = [x for x in states if x != 'complete']
    st['remaining'] = len(left)
    if not left:
        if post_failed():
            return {**st, 'state': 'failed_unit_review'}
        if post_pending():
            if not smoke_receipts()['pass']:
                return {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
            return {**st, 'state': 'ready', 'ready': 1, 'remaining': 1, 'slots': 1, 'submit': [SBATCH, '--post']}
        return {**st, 'state': 'complete'}
    if 'failed' in left:
        return {**st, 'state': 'failed_unit_review'}
    rec = smoke_receipts()
    if not rec['pass']:
        if rec['other']:
            return {**st, 'state': 'engineering_probe_failed'}
        return {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
    ready = sum(x == 'ready' for x in left)
    if ready:
        return {**st, 'state': 'ready', 'ready': ready, 'slots': min(SLOTS, ready),
                'submit': [SBATCH, '--worker', '--max-units', str(PER_JOB)]}
    if post_failed():
        return {**st, 'state': 'failed_unit_review'}
    if post_pending():
        return {**st, 'state': 'ready', 'ready': 1, 'slots': 1, 'submit': [SBATCH, '--post']}
    return {**st, 'state': 'waiting_for_encoders'}


# ----------------------------------------------------------------------------------------------- execution
def sub(*args):
    return subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, *map(str, args)]).returncode


def run_unit(uid):
    spec = read(BASE / 'specs' / f'{uid}.json')
    assert spec['binding_sha256'] == PF.sha(PF.BINDING), 'binding drift'
    dest = Path(spec['store'])
    t0 = time.time()
    meta = PF2.export(spec['encoder'], dest)
    arrays = {str(f): meta['folds'][str(f)]['array_sha256'] for f in PF.FOLDS}
    write(BASE / 'units' / f'{uid}.json', {'status': 'complete', 'spec': spec, 'spec_sha256': sha(BASE / 'specs' / f'{uid}.json'),
                                            'meta_sha256': sha(dest / 'meta.json'), 'arrays_sha256': arrays,
                                            'encoder_checkpoint_sha256': meta['encoder_meta'].get('checkpoint_sha256'),
                                            'encoder_meta': meta['encoder_meta'], 'U_dim': meta['folds']['0']['U_dim'],
                                            'gpu_peak_mb': meta['gpu_peak_mb'], 'seconds': time.time() - t0, 'device': meta['device'],
                                            'job': os.environ.get('SLURM_JOB_ID'), 'sources': sources(), 'fleet_version': 'v4',
                                            'encoders_v2_py_sha256': meta.get('encoders_v2_py_sha256'), 'encoders_v3_py_sha256': meta.get('encoders_v3_py_sha256'), 'encoders_v4_py_sha256': meta.get('encoders_v4_py_sha256'),
                                            'time': datetime.now().astimezone().isoformat()})
    print('unit complete', spec['encoder'], uid, round(time.time() - t0, 1), flush=True)


def claim(uid, fn):
    path = BASE / 'units' / f'{uid}.json'
    lock = BASE / 'claims' / f'{uid}.lock'
    lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if path.exists() or (BASE / 'units' / f'{uid}.FAILED.json').exists():
            return False
        rc = fn()
        if rc < 0:                      # preempted / signalled: no FAILED marker; the unit restarts from scratch later
            raise SystemExit(rc)
        if rc or not path.exists():
            write(BASE / 'units' / f'{uid}.FAILED.json', {'job': os.environ.get('SLURM_JOB_ID'), 'returncode': rc,
                                                          'time': datetime.now().astimezone().isoformat()})
            raise RuntimeError(f'DEP12 private feature unit failed: {uid}')
        return True


def worker(max_units):
    assert smoke_receipts()['pass'], 'no passing smoke for the current sources / binding'
    from . import encoders_v4 as E
    E.refresh()
    count = 0
    for spec in specs():
        if count >= max_units:
            break
        if unit_state(spec) != 'ready':
            continue
        if claim(spec['id'], lambda: sub('--unit', spec['id'])):
            count += 1
    post()


def smoke():
    """v4 equivalence receipt (CPU or GPU; no outcome threshold): encoders_v4 lists the ext1-ext3 names; for every
    registered v1 name its registry spec equals encoders.py's (state excluded); B0 loaded through encoders_v4 and encoders gives
    identical U on real fold-0 containers, and reproduces the stored production B0 fold-0 kernel rows (max |diff| <= 1e-5)."""
    import numpy as np
    import torch
    from . import encoders as E1, encoders_v4 as E2
    job = os.environ['SLURM_JOB_ID']
    receipt = {'status': 'running', 'sources': sources(), 'binding_sha256': PF.sha(PF.BINDING), 'job': job}
    try:
        R1, R2 = E1.refresh(), E2.refresh()
        assert set(EXT1 + EXT2 + EXT3) <= set(R2) and not set(EXT1 + EXT2 + EXT3) & set(R1)
        skip = ('state', 'checkpoint', 'sha256', 'run')
        diffs = [n for n in REUSED + NEW if n in R1 and {k: v for k, v in R1[n].items() if k not in skip} != {k: v for k, v in R2[n].items() if k not in skip}]
        assert not diffs, diffs
        receipt['registry'] = {'v1_names_equal': True, 'extension': {n: R2[n].get('state') for n in EXT1 + EXT2 + EXT3}}
        b0 = next(s_ for s_ in specs() if s_['encoder'] == 'B0')
        z = PF.load_fold(b0['store'], 0)
        bind = PF.Binding(); kids = PF.load_children(); off, _ = bind.offsets()
        cids = bind.ids[:3]
        dev = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        enc1, enc2 = E1.load('B0', dev), E2.load('B0', dev)
        mu, sd = torch.as_tensor(z['std_mu']).to(dev), torch.as_tensor(z['std_sd']).to(dev)
        kpos = {int(g): i for i, g in enumerate(z['kernel_index'])}
        worst, n = 0.0, 0
        for c in cids:
            k = next(k_ for k_ in kids if k_['id'] == c)
            rows = bind.arr(c, 'panel_rows')[:64]
            xr = PF.resample_real(torch.as_tensor(k['x'][rows]).to(dev)).float()
            xb = PF.container(xr, mu, sd)
            u1 = enc1.represent(xb, PF.channel_names(), torch.as_tensor(PF.pad_mask()).to(dev)).cpu()
            u2 = enc2.represent(xb, PF.channel_names(), torch.as_tensor(PF.pad_mask()).to(dev)).cpu()
            assert torch.equal(u1, u2), 'encoders_v4 and encoders differ for B0'
            ref = z['U_kernel'][[kpos[off[c] + int(r)] for r in rows]]
            worst = max(worst, float(np.max(np.abs(u2.numpy() - ref)))); n += len(rows)
        assert worst <= 1e-5, worst
        receipt['B0'] = {'rows_checked': n, 'v1_v2_identical': True, 'max_abs_diff_vs_stored_production': worst, 'device': str(dev)}
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc())
        raise
    finally:
        write(BASE / 'smoke_v4' / job / 'receipt.json', receipt)


def status():
    sp = specs()
    print(json.dumps({'fleet': fleet_status(), 'units': [(s['encoder'], unit_state(s)) for s in sp]}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--register', action='store_true')
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--worker', action='store_true')
    ap.add_argument('--max-units', type=int, default=PER_JOB)
    ap.add_argument('--unit')
    ap.add_argument('--status', action='store_true')
    ap.add_argument('--post', action='store_true')
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'compute through Slurm'
    os.umask(0o077)
    if a.register:
        register(REUSED + NEW)
    elif a.smoke:
        smoke()
    elif a.unit:
        run_unit(a.unit)
    elif a.worker:
        worker(a.max_units)
    elif a.post:
        assert smoke_receipts()['pass'], 'no passing smoke for the current sources / binding'
        post()
    elif a.status:
        status()


if __name__ == '__main__':
    main()
