"""Paper line W2 (docs/auditory_alignment_v3/paper/PR_STORY_BLUEPRINT.md §2A): audit of the 10 trained MindMix units.

Post-hoc, outside the frozen ALN4.2 EXTERNAL_COMPARISON_BINDING (aln42.external_eval stays the comparison of record). GPU, one
job per unit, after that unit's aln42.external_mindmix record is complete. Per unit: the released architecture with that unit's
final_model.pt (state dict, sha-checked), eval mode, no grad, on every 2 s test window of the unit's test people (the scored test
cs segments x sub-window starts 0 / 1.5 / 3.0 s, inputs from external_mindmix.Inputs, i.e. the bound preprocessing). Windows
are taken in segment / sub-window order and batched per person in consecutive groups of 32 (the official test loader without
shuffling; one model per subject in the official protocol).
  official_att   universal_trainer._evaluate_contrastive verbatim with target = attended, negative = ignored: pred = pA > pB,
                 where pA / pB are the in-batch softmax diagonals of the official ClipLoss.get_probabilities (label 1 for all).
  official_ign   the same with the slots swapped (target = ignored); a blind scorer would give 1 - official_att.
  official_noise official_att with the EEG replaced by Gaussian noise (per-window per-channel z-scored, seed 3401 + unit index).
  blind_real / blind_noise  the bound order-symmetrised margin m(attended, ignored) (external_mindmix.blind_margin), real / noise EEG.
  embeddings     eeg_emb = eeg_proj(eeg_encoder(eeg)) (the EEG branch before CALRA; real and noise) and audio_proj embeddings of
                 the attended and ignored windows; also for up to 600 train-people fit windows (bandwidth calibration).
CS audit (summarize step, CPU): per test person, excess CS dependence (cs_atlas estimator; within-person segment-roll null over
whole 5 s segments) between eeg_emb and the attended / ignored audio embedding, for real and noise EEG.
Usage: `python -m auditory_alignment_v3.paper.mindmix_audit <--make-plan | --smoke | --worker | --unit ID | --summarize>`.
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
from ..aln42 import external_mindmix as XM

OUT = Path(core.OUT) / 'paper' / 'mindmix_audit_v1'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/paper/mindmix_audit_v1')
RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/paper/mindmix_audit'
NAME, LANE, SBATCH = 'c3_s35mmaudit', 's35_paper_mindmix_audit', 'slurm/aln35_paper_mmaudit.sbatch'
BATCH, N_TRAIN_EMB, SMOKE_WINDOWS = 32, 600, 64
read, write, sha = XM.read, XM.write, XM.sha


def sources():
    repo = Path(core.REPO)
    return {str(p.relative_to(repo)): sha(p) for p in (Path(__file__), repo / 'auditory_alignment_v3/aln42/external_mindmix.py',
                                                        repo / 'auditory_alignment_v3/paper/cs_atlas.py')}


def make_plan():
    xplan = read(XM.OUT / 'plan.json')
    body = {'version': 'PAPER_MINDMIX_AUDIT_v1', 'external_plan_sha256': sha(XM.OUT / 'plan.json'), 'sources': sources(),
            'rows': [{'id': r['id'], 'content_fold': r['content_fold'], 'person_fold': r['person_fold'], 'index': k}
                     for k, r in enumerate(xplan['rows'])],
            'settings': {'batch': BATCH, 'n_train_embeddings': N_TRAIN_EMB, 'noise_seed': 'XM.SEED + row index'}}
    path = OUT / 'plan.json'
    if path.exists():
        old = read(path); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
        write(path, {**body, 'created': datetime.now().astimezone().isoformat()}); path.chmod(0o444)
    print('mindmix audit plan', sha(path), len(body['rows']))


def verify(plan):
    assert plan['sources'] == sources() and plan['external_plan_sha256'] == sha(XM.OUT / 'plan.json'), 'audit source drift'


def external_record(row):
    p = XM.OUT / 'units' / f'{row["id"]}.json'
    if not p.exists():
        return None
    rec = read(p)
    return rec if rec['status'] == 'complete' and not rec['probe'] else None


def unit_windows(row, probe):
    """Rebuild the unit's index, people and inputs exactly as external_mindmix.run_unit does."""
    import h5py
    from auditory_alignment import data as D
    cf, sf = row['content_fold'], row['person_fold']
    ix = XM.cohort_index(cf); ix['trial_n'] = {}
    for sub in sorted({g['sub'] for g in ix['geo']}):
        with h5py.File(os.path.join(D.DTU_PRE, f'{sub}.h5'), 'r') as f:
            for k in {g['trial'] for g in ix['geo'] if g['sub'] == sub}:
                ix['trial_n'][(sub, k)] = int(f[k]['eeg_1_20'].shape[1])
    train_p, test_p = XM.unit_people(ix, sf)
    A = ix['arrays']; person, role = A['cs_person'], A['cs_role']
    test_ids = [i for i in range(len(person)) if person[i] in set(test_p) and role[i] == 'test']
    fit_ids = [i for i in range(len(person)) if person[i] in set(train_p) and role[i] == 'fit']
    rng = np.random.default_rng(XM.SEED + 17)
    train_w = [fit_ids[i] for i in np.sort(rng.choice(len(fit_ids), size=min(N_TRAIN_EMB, len(fit_ids)), replace=False))]
    if probe:
        test_ids = test_ids[:SMOKE_WINDOWS // len(XM.SUB_OFFS_S) + 1]; train_w = train_w[:16]
    inp = XM.Inputs(ix, sorted(set(test_ids) | set(train_w)))
    return ix, person, test_ids, train_w, inp


def run_unit(row, plan, probe=False):
    import torch
    t0 = time.time(); job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda')
    xrec = external_record(row); assert xrec is not None, 'external unit not complete'
    model_path = Path(xrec['dest']) / 'final_model.pt'; assert sha(model_path) == xrec['final_model_sha256']
    ix, person, test_ids, train_w, inp = unit_windows(row, probe)
    model, args, UT = XM.build_model(dev)
    model.load_state_dict(torch.load(model_path, map_location='cpu', weights_only=True)); model.eval()
    n = torch.nn.functional.normalize
    gen = torch.Generator(device='cpu').manual_seed(XM.SEED + row['index'])

    def noise_like(e):
        z = torch.randn(e.shape, generator=gen).to(dev)
        return (z - z.mean(-1, keepdim=True)) / (z.std(-1, keepdim=True) + 1e-8)

    def official(e, tgt, neg):
        fe, ft, fn = model.forward_contrastive(e, tgt, neg)
        pA = model.clip_loss.get_probabilities(fe, ft).diagonal(); pB = model.clip_loss.get_probabilities(fe, fn).diagonal()
        return (pA > pB).float(), pA, pB

    def embeds(e, a, m):
        return (model.eeg_proj(model.eeg_encoder(e)), model.audio_proj(model.audio_encoder(a).last_hidden_state.mean(1)),
                model.audio_proj(model.audio_encoder(m).last_hidden_state.mean(1)))
    out = {k: [] for k in ('seg', 'sub', 'person', 'official_att', 'official_ign', 'official_noise', 'pA_att', 'pB_att',
                           'blind_real', 'blind_noise', 'eeg_emb', 'eeg_emb_noise', 'att_emb', 'ign_emb')}
    with torch.no_grad():
        people = sorted({person[i] for i in test_ids})
        for p in people:
            sw = [(i, o) for i in test_ids if person[i] == p for o in XM.SUB_OFFS_S]
            for k in range(0, len(sw), BATCH):
                xs = [inp.window(*w) for w in sw[k:k + BATCH]]
                e = torch.from_numpy(np.stack([x[0] for x in xs])).to(dev)
                at = torch.from_numpy(np.stack([x[1] for x in xs])).to(dev); ig = torch.from_numpy(np.stack([x[2] for x in xs])).to(dev)
                en = noise_like(e)
                pa, A_, B_ = official(e, at, ig); pi, _, _ = official(e, ig, at); pn, _, _ = official(en, at, ig)
                br = XM.blind_margin(model, e, at, ig); bn = XM.blind_margin(model, en, at, ig)
                ee, ea, ei = embeds(e, at, ig); en_e = model.eeg_proj(model.eeg_encoder(en))
                for key, v in (('official_att', pa), ('official_ign', pi), ('official_noise', pn), ('pA_att', A_), ('pB_att', B_),
                               ('blind_real', br), ('blind_noise', bn), ('eeg_emb', ee), ('eeg_emb_noise', en_e), ('att_emb', ea), ('ign_emb', ei)):
                    out[key].append(v.double().cpu().numpy())
                out['seg'] += [i for i, _ in sw[k:k + BATCH]]; out['sub'] += [o for _, o in sw[k:k + BATCH]]; out['person'] += [p] * len(xs)
        tr = {'eeg_emb': [], 'att_emb': [], 'ign_emb': []}
        for k in range(0, len(train_w), BATCH):
            xs = [inp.window(i, XM.SUB_OFFS_S[0]) for i in train_w[k:k + BATCH]]
            e = torch.from_numpy(np.stack([x[0] for x in xs])).to(dev)
            at = torch.from_numpy(np.stack([x[1] for x in xs])).to(dev); ig = torch.from_numpy(np.stack([x[2] for x in xs])).to(dev)
            for key, v in zip(('eeg_emb', 'att_emb', 'ign_emb'), embeds(e, at, ig)):
                tr[key].append(v.double().cpu().numpy())
    arrays = {k: (np.concatenate(v) if k not in ('seg', 'sub', 'person') else np.asarray(v)) for k, v in out.items()}
    arrays.update({f'train_{k}': np.concatenate(v) for k, v in tr.items()})
    # cross-check against the bound blind scoring of the same unit (oriented sub-window margins)
    with np.load(Path(xrec['dest']) / 'margins.npz') as z:
        msub = z['margin_subwindows']
    ref = np.array([msub[i, XM.SUB_OFFS_S.index(o)] for i, o in zip(arrays['seg'], arrays['sub'])])
    checks = {'blind_vs_bound_max_abs': float(np.nanmax(np.abs(ref - arrays['blind_real']))) if not probe else None}
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(dest / 'audit.npz', **arrays)
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'external_record_sha256': sha(XM.OUT / 'units' / f'{row["id"]}.json'),
           'final_model_sha256': xrec['final_model_sha256'], 'dest': str(dest), 'npz_sha256': sha(dest / 'audit.npz'),
           'n_test_windows': int(len(arrays['seg'])), 'n_test_people': int(len(set(arrays['person'].tolist()))), 'n_train_embeddings': int(len(train_w)),
           'checks': checks, 'seconds': time.time() - t0, 'device': torch.cuda.get_device_name(0), 'job': job,
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20}
    if not probe:
        assert checks['blind_vs_bound_max_abs'] < 1e-2, checks
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], 'audit complete', rec['n_test_windows'], round(rec['seconds'], 1), checks, flush=True)
    return rec


def receipts():
    out = {'pass': [], 'other': []}
    if not (OUT / 'plan.json').exists():
        return out
    ps = sha(OUT / 'plan.json')
    for path in sorted((OUT / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('plan_sha256') == ps:
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 10, 'slots': 1, 'initial': [], 'submit': []}
    if not (OUT / 'plan.json').exists():
        return st
    plan = read(OUT / 'plan.json')
    left = [r for r in plan['rows'] if not (OUT / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(left)
    if not left:
        return {**st, 'state': 'complete'}
    if any((OUT / 'units' / f'{r["id"]}.FAILED.json').exists() for r in left):
        return {**st, 'state': 'failed_unit_review'}
    ready = [r for r in left if external_record(r) is not None]
    if not ready:
        return {**st, 'state': 'waiting_for_external_units'}
    rec = receipts()
    if not rec['pass']:
        return {**st, 'state': 'engineering_probe_failed'} if rec['other'] else {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
    return {**st, 'state': 'ready', 'ready': len(ready), 'submit': [SBATCH, '--worker']}


def worker(plan):
    assert receipts()['pass'], 'no passing smoke'
    for row in plan['rows']:
        path = OUT / 'units' / f'{row["id"]}.json'
        if path.exists() or (OUT / 'units' / f'{row["id"]}.FAILED.json').exists() or external_record(row) is None:
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
                raise RuntimeError('mindmix audit unit failed')


def smoke(plan):
    job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
    try:
        row = next(r for r in plan['rows'] if external_record(r) is not None)
        rec = run_unit(row, plan, probe=True)
        with np.load(Path(rec['dest']) / 'audit.npz') as z:
            assert all(np.isfinite(z[k]).all() for k in ('official_att', 'blind_real', 'eeg_emb', 'att_emb', 'train_eeg_emb'))
        receipt['units'].append({k: rec[k] for k in ('row', 'n_test_windows', 'seconds', 'gpu_peak_mb', 'device')}); receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', receipt)


# ----------------------------------------------------------------------------------------------- summary (CPU)
def summarize():
    from . import cs_atlas as CA
    plan = read(OUT / 'plan.json'); per = {}; cs_rows = []
    rng = np.random.default_rng(CA.RNG_SEED)
    for row in plan['rows']:
        p = OUT / 'units' / f'{row["id"]}.json'
        if not p.exists():
            continue
        rec = read(p); assert sha(Path(rec['dest']) / 'audit.npz') == rec['npz_sha256']
        with np.load(Path(rec['dest']) / 'audit.npz') as z:
            Z = {k: z[k] for k in z.files}
        sig = {'eeg': CA.sigma_rule(Z['train_eeg_emb'], rng), 'att': CA.sigma_rule(Z['train_att_emb'], rng), 'ign': CA.sigma_rule(Z['train_ign_emb'], rng)}
        sig['eeg_noise'] = sig['eeg']
        for pid in sorted(set(Z['person'].tolist())):
            ix = np.flatnonzero(Z['person'] == pid)
            d = per.setdefault(pid, {})
            for key, v in (('official_att', Z['official_att'][ix].mean()), ('official_ign_target_wins', Z['official_ign'][ix].mean()),
                           ('official_noise', Z['official_noise'][ix].mean()),
                           ('blind_real', np.mean((Z['blind_real'][ix] > 0) + 0.5 * (Z['blind_real'][ix] == 0))),
                           ('blind_noise', np.mean((Z['blind_noise'][ix] > 0) + 0.5 * (Z['blind_noise'][ix] == 0)))):
                d.setdefault(key, []).append(float(v))
            reps = {'eeg': Z['eeg_emb'][ix], 'eeg_noise': Z['eeg_emb_noise'][ix]}
            tg = {'att': Z['att_emb'][ix], 'ign': Z['ign_emb'][ix]}
            for rname, t, v in CA.person_cells(reps, tg, Z['seg'][ix], {k: sig[k] for k in reps}, {k: sig[k] for k in tg}):
                cs_rows.append({'unit': row['id'], 'content_fold': row['content_fold'], 'person': pid, 'rep': rname, 'target': t, **v})
                d.setdefault(f'cs_excess/{rname}/{t}', []).append(v['excess']); d.setdefault(f'cs_z/{rname}/{t}', []).append(v['z'])
    people = {pid: {k: float(np.mean(v)) for k, v in d.items()} for pid, d in per.items()}
    keys = sorted({k for d in people.values() for k in d})
    means = {k: {'mean': float(np.mean([d[k] for d in people.values() if k in d])), 'n': sum(k in d for d in people.values())} for k in keys}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / 'MINDMIX_AUDIT.json').write_text(json.dumps({'version': plan['version'], 'plan_sha256': sha(OUT / 'plan.json'),
        'units_included': sorted({r['unit'] for r in cs_rows}), 'person_means': means, 'per_person': people,
        'definitions': __doc__}, indent=1) + '\n')
    print(json.dumps(means, indent=1))


def main():
    ap = argparse.ArgumentParser()
    for flag in ('make_plan', 'smoke', 'worker', 'summarize'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = read(OUT / 'plan.json'); verify(plan)
    if a.summarize:
        os.umask(0o022); summarize(); return
    if a.unit:
        run_unit(next(r for r in plan['rows'] if r['id'] == a.unit), plan); return
    if a.smoke:
        smoke(plan); return
    assert a.worker
    worker(plan)


if __name__ == '__main__':
    main()
