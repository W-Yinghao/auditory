"""ALN3.6 R1 private frozen window features for the matched AP / APwrong targets (GPU forward only).

Bundles: the 10 ALN3.5 matched target units (apwrong_v1; seed 3401, NCE, AP and APwrong arms x 5 outer child folds,
same revised sampler, initialisation and exposure stream). Each target's selected checkpoint (record
`checkpoints.best`, hash-checked) is loaded strictly into the 64 Hz shared encoder; the private view is rebuilt and
its pool/view hashes must equal the training record. Windows: encoder-input masks of prior_science (0-200, 200-400,
400-600 ms nominal; 64 Hz samples 0-12, 13-25, 26-37 after onset, i.e. 0-187.5, 203.1-390.6, 406.3-578.1 ms) plus the
unmasked input; masks act before encoding. Optional reference S uses the existing prior_science_v1 caches (no GPU).
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import gc
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from ..aln34 import prior_science as PS
from . import common as C

BASE = C.OUT / 'private_features_v1'
PLAN = BASE / 'plan.json'
STORE = C.STORE / 'private_features_v1'
APW = Path(core.OUT) / 'aln35/apwrong_v1'
APW_STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln35_apwrong_v1/production/targets')
WINDOWS = PS.WINDOWS
NAME, LANE, SBATCH = 'c3_s35a36priv', 's35_aln36_private', 'slurm/aln35_aln36_private.sbatch'


def sources():
    files = [Path(__file__), Path(C.__file__), Path(PS.__file__), C.REPO / 'auditory_alignment_v3/prior33/views.py',
             C.REPO / 'auditory_alignment_v3/prior33/model.py', C.REPO / 'auditory_alignment_v3/prior33/contract.py',
             C.REPO / 'auditory_alignment_v3/prior33/target_train.py', C.REPO / 'auditory_alignment_v3/aln35/support_runtime.py',
             C.REPO / 'auditory_alignment/data.py']
    return {str(p.relative_to(C.REPO)): C.sha(p) for p in sorted(set(files))}


def make_plan():
    apw = C.read(APW / 'plan.json')
    rows = []
    for u in apw['units']:
        if u['stage'] != 'target' or u['dataset'] != 'private_bdf':
            continue
        rec_path = APW / 'units' / f'{u["unit_id"]}.json'; rec = C.read(rec_path)
        assert rec['status'] == 'complete' and rec['seed'] == C.SEED and rec['arm'] in ('AP', 'APwrong')
        ck = APW_STORE / rec['checkpoints']['best']['file']
        assert C.sha(ck) == rec['checkpoints']['best']['sha256']
        body = {'kind': 'matched_target', 'arm': rec['arm'], 'person_fold': rec['subject_fold'], 'seed': rec['seed'],
                'source_id': u['unit_id'], 'source_record_sha256': C.sha(rec_path), 'checkpoint': str(ck),
                'checkpoint_sha256': rec['checkpoints']['best']['sha256'], 'checkpoint_rule': rec['selection']['primary']['rule'],
                'donor_unit': rec['donor_unit'], 'view_sha256': rec['view']['view_sha256'], 'pool_sha256': rec['view']['pool_sha256']}
        rows.append({**body, 'id': 'ALN36P_' + C.digest(body)})
    assert len(rows) == 10 and {(r['arm'], r['person_fold']) for r in rows} == {(a, f) for a in ('AP', 'APwrong') for f in C.PERSON_FOLDS}
    ps = C.read(PS.PLAN)
    optional = []
    for u in ps['rows']:
        r = u['source']
        if r['dataset'] != 'private_bdf' or u['config'] != ['S', 'NCE']:
            continue
        meta = PS.STORE / 'cache' / u['id'] / 'meta.json'
        if not meta.exists():
            continue
        m = C.read(meta)
        body = {'kind': 'existing_S_cache', 'arm': 'S', 'person_fold': r['subject_fold'], 'seed': r['seed'], 'source_id': r['experiment_id'],
                'prior_science_unit': u['id'], 'cache_meta_sha256': C.sha(meta), 'array_sha256': m['array_sha256']}
        optional.append({**body, 'id': 'ALN36P_' + C.digest(body)})
    rows.sort(key=lambda r: (r['person_fold'], r['arm'])); optional.sort(key=lambda r: r['person_fold'])
    body = {'version': 'ALN36_PRIVATE_FEATURES_v1', 'rows': rows, 'optional_S': optional, 'sources': sources(),
            'store': str(STORE), 'windows_ms': {k: v for k, v in WINDOWS.items()}, 'apwrong_plan_sha256': C.sha(APW / 'plan.json')}
    if PLAN.exists():
        old = C.read(PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
        C.write(PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); PLAN.chmod(0o444)
    print('ALN36 private feature plan', len(rows), 'core,', len(optional), 'optional S', C.sha(PLAN), flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'frozen source drift'


def load_children():
    """support_runtime.load_kids (physical onsets, history, blocks) + the 64 Hz view used in training."""
    from ..aln35 import support_runtime as SR
    from ..prior33 import views as V
    return V.load_private64(SR.load_kids())


def extract(row, kids=None, probe=False):
    import torch
    from ..prior33 import contract as PC, model as M, target_train as TT, views as V
    t0 = time.time(); dev = torch.device('cuda')
    rec = C.read(APW / 'units' / f'{row["source_id"]}.json'); assert C.sha(APW / 'units' / f'{row["source_id"]}.json') == row['source_record_sha256']
    assert C.sha(row['checkpoint']) == row['checkpoint_sha256']
    kids = load_children() if kids is None else kids
    sf = rec['subject_fold']; view = TT._private_view(kids, sf)
    assert view['pool_sha256'] == row['pool_sha256'], 'private children/folds/ES blocks differ from training'
    # ap_wrong_queries precedent: bind the view to the frozen manifest filter bytes; record whether this host's
    # redesigned filter coefficients are byte-identical (a host numerical difference, not a different contract).
    filters = V.open_for_row(rec['source_template'])['filters']; local = PC.filter_shas()
    frozen_view = TT._sha_json({'pool': view['pool_sha256'], 'lp20_sos': filters['lp20_sos'],
                                'aa_fir_250': filters['aa_fir_250'], 'contract': PC.CONTRACT})
    assert frozen_view == row['view_sha256'], 'private view contract differs from training'
    view.update(frozen_filter_view_sha256=frozen_view,
                host_filters_equal_frozen={k: local.get(k) == filters.get(k) for k in ('lp20_sos', 'aa_fir_250')})
    b = TT.bind(rec['adapter_row'])
    bt = V.PrivateBatcher64(kids, b['spec'], b, dev)
    enc = M.build_shared(PC.PRIVATE_LAYOUT, PC.PRIVATE_LAYOUT, rec['seed']).to(dev)
    sd = torch.load(row['checkpoint'], map_location=dev, weights_only=False)
    enc.load_state_dict(sd['enc'], strict=True); enc.requires_grad_(False).eval()
    arrays = {}
    children = kids if not probe else kids[:3]
    with torch.no_grad():
        for window, bounds in WINDOWS.items():
            for i, k in enumerate(children):
                out = []
                for start in range(0, len(k['y']), 256):
                    idx = torch.arange(start, min(start + 256, len(k['y'])), device=dev)
                    out.append(enc(PS.mask64(bt.patches(i, idx), bt, bounds)).float().cpu().numpy())
                arrays[f'{window}_{i}'] = np.concatenate(out)
    dest = (STORE / 'probes' / os.environ['SLURM_JOB_ID'] if probe else STORE / 'banks') / row['id']
    dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(dest / 'arrays.npz', **arrays)
    meta = {'row': row, 'plan_sha256': C.sha(PLAN), 'source_sha256': C.sha(__file__), 'probe': probe,
            'children': {str(i): k['id'] for i, k in enumerate(children)}, 'windows_ms': WINDOWS,
            'onset_sample': PC.ONSET64, 'input_samples': list(PC.PRIVATE_WIN),
            'sample_times_ms': [(i - PC.ONSET64) / PC.FS * 1000 for i in range(*PC.PRIVATE_WIN)],
            'view': view, 'array_sha256': C.sha(dest / 'arrays.npz'), 'seconds': round(time.time() - t0, 1),
            'gpu_peak_mb': round(torch.cuda.max_memory_allocated() / 2 ** 20), 'device': torch.cuda.get_device_name(0),
            'job': os.environ['SLURM_JOB_ID']}
    C.write(dest / 'meta.json', meta)
    if not probe:
        C.write(BASE / 'units' / f'{row["id"]}.json', {'status': 'complete', 'bank': str(dest), 'meta_sha256': C.sha(dest / 'meta.json'),
                                                      'array_sha256': meta['array_sha256'], 'row': row})
    print(row['id'], row['arm'], 'sf', row['person_fold'], meta['seconds'], 's', flush=True)
    del enc, bt; gc.collect(); torch.cuda.empty_cache()
    return meta


def receipts():
    out = {'pass': [], 'other': []}
    if not PLAN.exists():
        return out
    for path in sorted((BASE / 'probes').glob('*/receipt.json')):
        rec = C.read(path)
        if rec.get('plan_sha256') == C.sha(PLAN):
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    status = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 10, 'slots': 1, 'initial': [], 'submit': []}
    if not PLAN.exists():
        return status
    plan = C.read(PLAN)
    remaining = [r for r in plan['rows'] if not (BASE / 'units' / f'{r["id"]}.json').exists()]
    status['remaining'] = len(remaining)
    if not remaining:
        status['state'] = 'complete'; return status
    rec = receipts()
    if not rec['pass']:
        if rec['other']:
            status['state'] = 'engineering_probe_failed'; return status
        status.update(state='ready', ready=1, submit=[SBATCH, '--smoke']); return status
    available = [r for r in remaining if not (BASE / 'units' / f'{r["id"]}.FAILED.json').exists()]
    status.update(state='ready' if available else 'failed_unit_review', ready=min(1, len(available)),
                  submit=[SBATCH, '--smoke-job', rec['pass'][-1].parent.name])
    return status


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--make-plan', action='store_true'); ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--smoke-job')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = C.read(PLAN); verify(plan)
    kids = load_children()
    if a.smoke:
        job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': C.sha(PLAN), 'units': []}
        try:
            for row in plan['rows'][:2]:
                meta = extract(row, kids, probe=True)
                with np.load(STORE / 'probes' / job / row['id'] / 'arrays.npz') as z:
                    assert all(np.isfinite(z[k]).all() and z[k].shape[1] == 32 for k in z.files)
                    for i in range(3):
                        assert not np.allclose(z[f'0_200_{i}'], z[f'400_600_{i}']), 'window masks must change the encoding'
                receipt['units'].append({'id': row['id'], 'seconds': meta['seconds'], 'peak_mb': meta['gpu_peak_mb']})
            receipt['status'] = 'pass'
        except BaseException:
            receipt.update(status='failed', traceback=traceback.format_exc()); raise
        finally:
            C.write(BASE / 'probes' / job / 'receipt.json', receipt)
        return
    rec = C.read(BASE / 'probes' / str(a.smoke_job) / 'receipt.json'); assert rec['status'] == 'pass' and rec['plan_sha256'] == C.sha(PLAN)
    lock = (BASE / 'claims' / 'all.lock'); lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for row in plan['rows']:
            path = BASE / 'units' / f'{row["id"]}.json'
            if path.exists():
                continue
            try:
                extract(row, kids)
            except BaseException:
                C.write(BASE / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'traceback': traceback.format_exc()})
                raise


if __name__ == '__main__':
    main()
