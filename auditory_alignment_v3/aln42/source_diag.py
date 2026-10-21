"""ALN4.2 bounded source-learning diagnosis (package AUDITORY_ALN4_SERVER_PACKAGE_v4_2_20261021 docs/03).

Post-R1 mechanism diagnosis; it does not change any production training, selection or statistics. The ALN4.1 seed-3401
production checkpoints at updates 0 / 2500 / 5000 / 10000 of TCS, TNCE, GCS and TCS_WRONG are evaluated on one fixed panel:
- fit: the first 32 episodes of the production stream (same rows, offsets, wrong bijections and packed keys);
- dev: 32 episodes drawn from the source-dev pool with the production sampler (aln41.source.make_stream, seed 348201) over the
  dev people that meet the production eligibility (>= 3 families with >= 22 segments).
Zero optimizer updates: no optimizer is constructed and the model state digest is asserted unchanged after every snapshot.
The only fitted quantities are the production per-episode support delta (5 steps, discarded) and the original 512 / 512 ridge
probe refitted per snapshot on the fixed fit panel (lambda rule unchanged, dev evaluated only).

Per arm, snapshot, panel, episode, person, view, slot and split (S / Q) it exports, all through the production objective
functions (aln41.temporal_objectives_torch, unchanged):
 A. pairing: cosine/temperature logits of the projected EEG and fixed audio heads with the production packed-key masks;
    positive vs legal-negative means, top-1 retrieval, the masked symmetric NCE and its exact uniform-score baseline;
    TCS slot potentials (log A/B/C) and the GCS pooled score as common read-only CS probes; the native objective of the arm
    (TCS_WRONG: native wrong pairing, plus a separately labelled correct-pairing probe);
 B. representation: centred variance, effective rank exp(H(normalised squared singular values)), mean off-diagonal cosine and
    norms of raw backbone tokens and of each projected view, relative change from update 0 on identical inputs; ridge probe
    fit and dev NMSE, prediction means, rank and condition number;
 C. gate / support: query objective under q_uniform, q_prior = softmax(a) and q_support = softmax(a + delta); the five support
    steps with and without the delta penalty; on the first 2 fit and 2 dev episodes, d/da of the mean query objective at
    a + stopgrad(delta) against d/da of 0.01 KL(softmax(a) || U), with projection and backbone gradient norms of the data term;
 D. reproduction: train-mode reference of the logged first update on a clone (snapshot 0, fit episode 0 = log 'update 1').
Person ids are replaced by an opaque hash in exported rows; physical panel ids stay in the private store.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from ..aln41 import source as SRC

OUT = Path(core.OUT) / 'aln42' / 'source_diag_v1'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln42/source_diag_v1')
ARMS = ('TCS', 'TNCE', 'GCS', 'TCS_WRONG')
SNAPSHOTS = (0, 2500, 5000, 10000)
N_EPISODES, DEV_SEED, GRAD_EPISODES = 32, 348201, 2
NAME, LANE, SBATCH = 'c3_s35a42diag', 's35_aln42_source_diag', 'slurm/aln35_aln42_diag.sbatch'
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest


def sources():
    here = Path(__file__).parent; a41 = here.parent / 'aln41'
    files = [here / 'source_diag.py', a41 / 'source.py', a41 / 'timebank.py', a41 / 'temporal_objectives_torch.py',
             a41 / 'cs_qmi_reference.py']
    return {str(p.relative_to(core.REPO)): sha(p) for p in sorted(set(files))}


def opaque(person):
    return hashlib.sha256(('ALN42_DIAG|' + str(person)).encode()).hexdigest()[:12]


# ----------------------------------------------------------------------------------------------- plan (CPU, once)
def make_plan():
    r1 = read(SRC.BASE / 'plan.json'); SRC.verify(r1); sel = read(SRC.BASE / 'selection.json')
    man = SRC.open_manifest(); split_pool, pool_info = SRC.pool(man)
    dev_people, dev_excluded = SRC.eligible_people(split_pool['dev'])
    dev = SRC.make_stream(split_pool['dev'], dev_people, N_EPISODES, seed=DEV_SEED)
    SRC.check_stream(man, dev)
    fit = {k: v[:N_EPISODES] for k, v in SRC.load_arrays(SRC.STORE / 'stream.npz').items() if k != 'people'}
    fit['people'] = SRC.load_arrays(SRC.STORE / 'stream.npz')['people']
    STORE.mkdir(parents=True, exist_ok=True, mode=0o700); OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(STORE / 'panels.npz', **{f'fit_{k}': v for k, v in fit.items()}, **{f'dev_{k}': v for k, v in dev.items()})
    rows, ckpts = [], {}
    for arm in ARMS:
        prow = next(r for r in sel['production_rows'] if r['arm'] == arm)
        rec = read(SRC.BASE / 'units' / f'{prow["id"]}.json'); assert rec['status'] == 'complete'
        ck = {str(s): rec['checkpoints'][str(s)] for s in SNAPSHOTS}
        for s, c in ck.items():
            assert sha(c['path']) == c['sha256'], (arm, s)
        ckpts[arm] = {'production_unit': prow['id'], 'record_sha256': sha(SRC.BASE / 'units' / f'{prow["id"]}.json'), 'checkpoints': ck}
        body = {'arm': arm, 'seed': SRC.SEED, 'snapshots': list(SNAPSHOTS)}
        rows.append({**body, 'id': 'ALN42D_' + digest(body, 16)})
    body = {'version': 'ALN42_SOURCE_DIAG_v1', 'rows': rows, 'sources': sources(), 'store': str(STORE),
            'r1_source_plan_sha256': sha(SRC.BASE / 'plan.json'), 'r1_stream_sha256': r1['stream_sha256'],
            'r1_sigmas_sha256': sha(SRC.sigmas_path()), 'checkpoints': ckpts, 'panels_sha256': sha(STORE / 'panels.npz'),
            'fit_panel': f'production stream episodes 0..{N_EPISODES - 1}', 'dev_panel': {'seed': DEV_SEED, 'episodes': N_EPISODES,
            'eligible_dev_people': len(dev_people), 'excluded_dev_people': len(dev_excluded),
            'pool': {k: pool_info[k] for k in ('dev_people', 'dev_families', 'dev_segments')}},
            'ridge': 'aln41.source ridge rule (lambda = 1e-3 trace(K)/n), refit per snapshot on the 512 fit panel; dev evaluated only',
            'optimizer_updates': 0, 'design': 'post_R1_diagnostic (package ALN4.2 docs/03)'}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    print('ALN42 source diag plan', len(rows), 'arms; dev eligible', len(dev_people), sha(plan), flush=True)


# ----------------------------------------------------------------------------------------------- statistics helpers
def rep_stats(x):
    """x [n, d] (float64 torch): centred variance, effective rank, mean off-diagonal cosine, norms."""
    import torch
    x = x.double(); n = len(x)
    c = x - x.mean(0, keepdim=True)
    s = torch.linalg.svdvals(c)
    p = s ** 2 / (s ** 2).sum() if float((s ** 2).sum()) > 0 else None
    eff = float(torch.exp(-(p[p > 0] * torch.log(p[p > 0])).sum())) if p is not None else None
    nrm = torch.linalg.vector_norm(x, dim=1); u = x / nrm.clamp_min(1e-12)[:, None]
    cos = u @ u.T; off = cos[~torch.eye(n, dtype=torch.bool, device=x.device)]
    return {'centred_variance': float((c ** 2).sum() / n), 'effective_rank': eff, 'degenerate': p is None or float(s[0]) < 1e-10,
            'mean_offdiag_cosine': float(off.mean()), 'norm_mean': float(nrm.mean()), 'norm_min': float(nrm.min()), 'norm_max': float(nrm.max())}


def pairing(u_slot, v, positive, exclusion, tau):
    """Cosine/tau logits of one slot against the fixed audio vectors with the production masks."""
    import torch
    import torch.nn.functional as F
    from ..aln41 import temporal_objectives_torch as TO
    logits = F.normalize(u_slot.double(), dim=-1) @ F.normalize(v.double(), dim=-1).T / tau
    legal = ~positive & ~exclusion; allowed = ~exclusion
    top = logits.masked_fill(exclusion, -torch.inf).argmax(1)
    n_allowed_r, n_pos_r = allowed.sum(1).double(), positive.sum(1).double()
    n_allowed_c, n_pos_c = allowed.sum(0).double(), positive.sum(0).double()
    uniform = .5 * (torch.log(n_allowed_r / n_pos_r).mean() + torch.log(n_allowed_c / n_pos_c).mean())
    nce = TO.masked_symmetric_nce(logits, positive, exclusion)
    return logits, {'pos_mean': float(logits[positive].mean()), 'legal_neg_mean': float(logits[legal].mean()) if legal.any() else None,
                    'margin': float(logits[positive].mean() - logits[legal].mean()) if legal.any() else None,
                    'top1_retrieval': float(positive[torch.arange(len(top), device=positive.device), top].double().mean()),
                    'nce_nats': float(nce), 'uniform_nce_nats': float(uniform), 'nce_minus_uniform': float(nce - uniform),
                    'n_positive': int(positive.sum()), 'n_excluded': int(exclusion.sum()), 'N': int(len(logits))}


def ridge_full(Tf, Rf, Td, Rd):
    """The production ridge probe (aln41.source.ridge_probe) with fit NMSE, prediction means, rank and conditioning added."""
    import torch
    X = Tf.double(); mu = X.mean(0); sd = X.std(0) + 1e-8; X = (X - mu) / sd; Xd = (Td.double() - mu) / sd
    K = X @ X.T; n = len(X); lam = 1e-3 * float(torch.trace(K)) / n
    M = K + lam * torch.eye(n, dtype=K.dtype)
    alpha = torch.linalg.solve(M, torch.eye(n, dtype=K.dtype))
    ev = torch.linalg.eigvalsh(K).clamp_min(0)
    p = ev / ev.sum(); eff = float(torch.exp(-(p[p > 0] * torch.log(p[p > 0])).sum()))
    out = {'lambda': lam, 'kernel_effective_rank': eff, 'condition_number': float((ev.max() + lam) / (ev.min() + lam)), 'views': {}}
    for v in Rf:
        Y = Rf[v].double(); ym = Y.mean(0); ys = Y.std(0) + 1e-8; Yz = (Y - ym) / ys; Ydz = (Rd[v].double() - ym) / ys
        W = X.T @ (alpha @ Yz); P = Xd @ W; Pf = X @ W
        out['views'][v] = {'fit_nmse': float(((Pf - Yz) ** 2).mean() / (Yz ** 2).mean()), 'dev_nmse': float(((P - Ydz) ** 2).mean() / (Ydz ** 2).mean()),
                           'fit_pred_mean_abs': float(Pf.mean(0).abs().mean()), 'dev_pred_mean_abs': float(P.mean(0).abs().mean()),
                           'dev_target_mean_abs': float(Ydz.mean(0).abs().mean())}
    out['dev_nmse_mean'] = float(np.mean([out['views'][v]['dev_nmse'] for v in Rf]))
    out['fit_nmse_mean'] = float(np.mean([out['views'][v]['fit_nmse'] for v in Rf]))
    return out


# ----------------------------------------------------------------------------------------------- one arm (GPU)
def load_snapshot(model, ck):
    import torch
    st = torch.load(ck['path'], map_location='cpu', weights_only=False)
    model.bb.load_state_dict(st['backbone'], strict=True); model.heads.load_state_dict(st['heads'], strict=True)
    return st['a'].to(next(model.parameters()).device).double(), st


def run_unit(row, plan, probe=False):
    import torch
    from ..aln41 import temporal_objectives_torch as TO
    t0 = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']; arm = row['arm']
    kind = 'TCS' if arm == 'TCS_WRONG' else arm
    sig = read(SRC.sigmas_path())['sigmas']; P = SRC.load_arrays(STORE / 'panels.npz'); PR = SRC.load_arrays(SRC.STORE / 'panels.npz')
    assert sha(STORE / 'panels.npz') == plan['panels_sha256']
    man = SRC.open_manifest()
    n_ep = 2 if probe else N_EPISODES
    panels = {name: {k: P[f'{name}_{k}'][:n_ep] for k in ('rows', 'off', 'wrong', 'who')} | {'people': P[f'{name}_people']} for name in ('fit', 'dev')}
    seg_rows = np.r_[panels['fit']['rows'].reshape(-1), panels['dev']['rows'].reshape(-1), PR['fit_rows'], PR['dev_rows']]
    src = SRC.Source(man, seg_rows, dev)
    model, _ = SRC.build_model(dev); model.eval()
    inner = dict(steps=SRC.INNER['steps'], step_size=SRC.INNER['step_size'], delta_l2=SRC.INNER['delta_l2'], temperature=SRC.INNER['temperature'])
    tau = SRC.INNER['temperature']
    snaps = (0, 10000) if probe else SNAPSHOTS
    base_tokens, base_proj = {}, {}
    out_rows, ridge, grads, repro, checks = [], {}, [], {}, {}
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    bundles = {}
    for snap in snaps:
        ck = plan['checkpoints'][arm]['checkpoints'][str(snap)]; assert sha(ck['path']) == ck['sha256']
        a, st = load_snapshot(model, ck)
        before = SRC.state_digest(model)
        for name, pan in panels.items():
            for e in range(n_ep):
                for j in range(2):
                    person = str(pan['people'][pan['who'][e, j]])
                    S, Q = pan['rows'][e, j]; oS, oQ = pan['off'][e, j]
                    AS, _ = src.audio(S, oS); AQ, _ = src.audio(Q, oQ)
                    with torch.no_grad():
                        US, tokS = model(src.crops(S, oS)); UQ, tokQ = model(src.crops(Q, oQ))
                    kS, kQ = src.keys(S, oS), src.keys(Q, oQ)
                    posS, excS = TO.masks_from_packed_keys(kS, unknown_clock_families=src.unknown)
                    posQ, excQ = TO.masks_from_packed_keys(kQ, unknown_clock_families=src.unknown)
                    wS = torch.as_tensor(pan['wrong'][e, j, 0], device=dev); wQ = torch.as_tensor(pan['wrong'][e, j, 1], device=dev)
                    rec = {'arm': arm, 'snapshot': snap, 'panel': name, 'episode': e, 'person': opaque(person), 'slot_pairing': {}, 'repr': {}}
                    # C. gate / support under the native pairing (TCS_WRONG: the registered wrong audio), and the correct-pair probe
                    pairings = [('native', wS if arm == 'TCS_WRONG' else None, wQ if arm == 'TCS_WRONG' else None)]
                    if arm == 'TCS_WRONG':
                        pairings.append(('correct_pair_probe', None, None))
                    rec['objective'] = {}
                    for label, ws, wq in pairings:
                        sv = SRC.view_batches(US, AS, sig, ws); qv = SRC.view_batches(UQ, AQ, sig, wq)
                        kw = dict(support_keys=kS, unknown_clock_families=src.unknown) if kind == 'TNCE' else {}
                        delta, adapt = TO.adapt_delta_fo(kind, sv, a, **kw, **inner)
                        lam = SRC.INNER['delta_l2']
                        support_steps = [{'with_penalty': h['support_inner_loss_nats'],
                                          'without_penalty': h['support_inner_loss_nats'] - .5 * lam * h['delta_l2'] ** 2, 'q': h['q']}
                                         for h in adapt['history']]
                        gates = {}
                        for gname, logits in (('uniform', torch.zeros_like(a)), ('prior', a), ('support', a + delta)):
                            qk = dict(keys=kQ, unknown_clock_families=src.unknown) if kind == 'TNCE' else {}
                            loss, rep = TO.objective_loss(kind, qv, logits, temperature=tau, **qk)
                            gates[gname] = {'query_objective_nats': float(loss),
                                            'views': [{k: w[k] for k in w if k in ('view', 'score_nats', 'loss_nats', 'q', 'slot_scores_nats',
                                                                                   'slot_loss_nats', 'log_A_slot', 'log_B_slot', 'log_C_slot',
                                                                                   'pooled_norm_min')} for w in rep['views']]}
                        rec['objective'][label] = {'delta': delta.tolist(), 'q_prior': torch.softmax(a, 0).tolist(),
                                                   'q_support': torch.softmax(a + delta, 0).tolist(), 'support_steps': support_steps,
                                                   'query': gates, 'direction': 'NCE: lower is better; CS: objective = -score, lower is better'}
                    # A. pairing diagnostics with the correct audio (common read-only probe for every arm)
                    for split, U, A_, pos, exc in (('S', US, AS, posS, excS), ('Q', UQ, AQ, posQ, excQ)):
                        for v in ('env', 'ss', 'sc'):
                            for k in range(3):
                                lg, m = pairing(U[v][:, k], A_[v], pos, exc, tau)
                                rec['slot_pairing'][f'{split}/{v}/{k}'] = m
                                if name == 'fit' and e == 0 and j == 0 and split == 'Q':
                                    bundles.setdefault(snap, {}).setdefault(v, []).append(lg.cpu().numpy())
                            pot = TO.tcs_slot_log_potentials(SRC.view_batches(U, A_, sig)[('env', 'ss', 'sc').index(v)])
                            rec['slot_pairing'][f'{split}/{v}/tcs_potentials'] = {'log_A': pot[0].tolist(), 'log_B': pot[1].tolist(), 'log_C': pot[2].tolist(),
                                                                                  'slot_scores_nats': (pot[0] + pot[1] - 2 * pot[2]).tolist()}
                        if name == 'fit' and e == 0 and j == 0 and split == 'Q':
                            bundles[snap]['positive'] = pos.cpu().numpy(); bundles[snap]['exclusion'] = exc.cpu().numpy()
                            bundles[snap]['q_prior'] = torch.softmax(a, 0).cpu().numpy()
                            bundles[snap]['q_support'] = np.asarray(rec['objective']['native']['q_support'])
                    # B. representation statistics (raw tokens and each projected view) and change from update 0
                    for split, U, tok in (('S', US, tokS), ('Q', UQ, tokQ)):
                        key = (name, e, j, split)
                        for k in range(3):
                            t = tok[:, k].flatten(1)
                            rec['repr'][f'{split}/tokens/{k}'] = rep_stats(t)
                            for v in ('env', 'ss', 'sc'):
                                rec['repr'][f'{split}/{v}/{k}'] = rep_stats(U[v][:, k])
                        if snap == snaps[0]:
                            base_tokens[key] = tok.half().cpu(); base_proj[key] = {v: U[v].cpu() for v in U}
                        else:
                            b = base_tokens[key].float().to(dev)
                            rec['repr'][f'{split}/tokens/rel_change_from_update0'] = float(torch.linalg.vector_norm(tok.float() - b) / torch.linalg.vector_norm(b))
                            for v in ('env', 'ss', 'sc'):
                                pb = base_proj[key][v].to(dev)
                                rec['repr'][f'{split}/{v}/rel_change_from_update0'] = float(torch.linalg.vector_norm(U[v] - pb) / torch.linalg.vector_norm(pb))
                    if snap == snaps[0] and name == 'fit' and e == 0 and j == 0:
                        rec['audio_repr'] = {f'{split}/{v}': rep_stats(A_[v]) for split, A_ in (('S', AS), ('Q', AQ)) for v in ('env', 'ss', 'sc')}
                    out_rows.append(rec)
        # C. gradient audit (first 2 fit and 2 dev episodes; production first-order outer objective, no step)
        for name, pan in panels.items():
            for e in range(min(GRAD_EPISODES, n_ep)):
                a_p = a.clone().requires_grad_(True); data = 0.0
                for j in range(2):
                    S, Q = pan['rows'][e, j]; oS, oQ = pan['off'][e, j]
                    AS, _ = src.audio(S, oS); AQ, _ = src.audio(Q, oQ)
                    with torch.no_grad():
                        US, _ = model(src.crops(S, oS))
                    UQ, _ = model(src.crops(Q, oQ))
                    ws = torch.as_tensor(pan['wrong'][e, j, 0], device=dev) if arm == 'TCS_WRONG' else None
                    wq = torch.as_tensor(pan['wrong'][e, j, 1], device=dev) if arm == 'TCS_WRONG' else None
                    sv = SRC.view_batches(US, AS, sig, ws); qv = SRC.view_batches(UQ, AQ, sig, wq)
                    kw = dict(support_keys=src.keys(S, oS), unknown_clock_families=src.unknown) if kind == 'TNCE' else {}
                    delta, _ = TO.adapt_delta_fo(kind, sv, a_p.detach(), **kw, **inner)
                    qk = dict(keys=src.keys(Q, oQ), unknown_clock_families=src.unknown) if kind == 'TNCE' else {}
                    loss, _ = TO.objective_loss(kind, qv, a_p + delta.detach(), temperature=tau, **qk)
                    data = data + loss / 2
                kl = SRC.INNER['prior_kl_weight'] * TO.prior_uniform_kl(a_p)
                proj = [p for p in model.heads.parameters()]; bb = [p for p in model.bb.parameters()]
                g = torch.autograd.grad(data, [a_p] + proj + bb, allow_unused=True)
                g_kl = torch.autograd.grad(kl, a_p)[0]
                ga = g[0]
                gn = lambda gs: float(torch.sqrt(sum((x.double() ** 2).sum() for x in gs if x is not None)))
                cos = float(torch.dot(ga, g_kl) / (ga.norm() * g_kl.norm())) if float(ga.norm()) > 0 and float(g_kl.norm()) > 0 else None
                grads.append({'snapshot': snap, 'panel': name, 'episode': e, 'grad_a_data': ga.tolist(), 'grad_a_kl': g_kl.tolist(),
                              'norm_a_data': float(ga.norm()), 'norm_a_kl': float(g_kl.norm()), 'cosine_data_kl': cos,
                              'norm_projection_data': gn(g[1:1 + len(proj)]), 'norm_backbone_data': gn(g[1 + len(proj):]),
                              'reduction': 'mean over the 2 people of the query objective (production outer loss) + 0.01 KL'})
                model.zero_grad(set_to_none=True)
        # B. ridge probe refitted on this snapshot
        with torch.no_grad():
            Uf, Af, Tf, Rf = SRC.panel_features(src, model, PR['fit_rows'], PR['fit_off'])
            Ud, Ad, Td, Rd = SRC.panel_features(src, model, PR['dev_rows'], PR['dev_off'])
        ridge[str(snap)] = ridge_full(Tf, Rf, Td, Rd)
        ridge[str(snap)]['token_repr_fit'] = rep_stats(Tf.double())
        # D. reproduction: logged train-mode losses of the first updates (snapshot 0, fit episodes 0 and 1) on a clone
        if snap == 0:
            clone = copy.deepcopy(model).train(); a_c = a.clone()
            rec_log = read(SRC.BASE / 'units' / f'{plan["checkpoints"][arm]["production_unit"]}.json')['log']
            for e in range(1):   # log 'update 1' = episode 0 at the update-0 state; later log entries used updated states
                tot = 0.0
                for j in range(2):
                    pan = panels['fit']; S, Q = pan['rows'][e, j]; oS, oQ = pan['off'][e, j]
                    AS, _ = src.audio(S, oS); AQ, _ = src.audio(Q, oQ)
                    with torch.no_grad():
                        US, _ = clone(src.crops(S, oS)); UQ, _ = clone(src.crops(Q, oQ))
                    ws = torch.as_tensor(pan['wrong'][e, j, 0], device=dev) if arm == 'TCS_WRONG' else None
                    wq = torch.as_tensor(pan['wrong'][e, j, 1], device=dev) if arm == 'TCS_WRONG' else None
                    sv = SRC.view_batches(US, AS, sig, ws); qv = SRC.view_batches(UQ, AQ, sig, wq)
                    kw = dict(support_keys=src.keys(S, oS), query_keys=src.keys(Q, oQ), unknown_clock_families=src.unknown) if kind == 'TNCE' else {}
                    loss, _ = TO.episode_loss_fo(kind, sv, qv, a_c, prior_kl_weight=SRC.INNER['prior_kl_weight'], **kw, **inner)
                    tot += float(loss) / 2
                logged = next((x['loss'] for x in rec_log if x['update'] == e + 1), None)
                repro[f'fit_episode_{e}'] = {'train_mode_clone_loss': tot, 'logged_loss': logged,
                                             'abs_diff': abs(tot - logged) if logged is not None else None,
                                             'note': 'train-mode dropout RNG differs from the production run; eval-mode values are the primary diagnosis'}
            del clone
        assert SRC.state_digest(model) == before, 'model state changed during a diagnostic snapshot'
        checks[str(snap)] = {'state_digest_unchanged': True, 'checkpoint_sha256': ck['sha256'], 'a': a.tolist()}
        print(arm, 'snapshot', snap, 'done', round(time.time() - t0, 1), flush=True)
    rows_path = dest / 'rows.jsonl.gz'
    with gzip.open(rows_path, 'wt') as f:
        for r in out_rows:
            f.write(json.dumps(r) + '\n')
    for snap, b in bundles.items():
        np.savez_compressed(dest / f'helper_bundle_s{snap}.npz', logits=np.stack([np.stack(b[v]) for v in ('env', 'ss', 'sc')]),
                            positive=b['positive'], exclusion=b['exclusion'], q_prior=b['q_prior'], q_support=b['q_support'])
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'rows_path': str(rows_path),
           'rows_sha256': sha(rows_path), 'n_rows': len(out_rows), 'ridge': ridge, 'gradient_audit': grads, 'reproduction': repro,
           'zero_update_checks': checks, 'optimizer_constructed': False, 'kind': kind, 'seconds': time.time() - t0,
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': job,
           'code_checks': static_checks()}
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], arm, 'complete', round(rec['seconds'], 1), flush=True)
    return rec


def static_checks():
    """D. the production update path, read from aln41/source.py (byte-checked in the plan)."""
    text = (Path(SRC.__file__)).read_text()
    need = {'support_detached': 'US, _ = model(src.crops(S, oS))' in text and 'with torch.no_grad():\n                US' in text,
            'query_with_grad': '            UQ, _ = model(src.crops(Q, oQ))' in text,
            'a_in_optimizer': "{'params': [a], 'lr': lr, 'weight_decay': 0.0, 'name': 'gate_logits'}" in text,
            'delta_reset_each_episode': 'delta = torch.zeros_like(a_detached)' in (Path(SRC.__file__).with_name('temporal_objectives_torch.py')).read_text(),
            'sigmas_from_frozen_receipt': "sig = read(sigmas_path())['sigmas']" in text}
    return need


# ----------------------------------------------------------------------------------------------- workers / fleet
def receipts():
    out = {'pass': [], 'other': []}
    if not (OUT / 'plan.json').exists():
        return out
    for path in sorted((OUT / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('plan_sha256') == sha(OUT / 'plan.json'):
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': len(ARMS), 'slots': 1, 'initial': [], 'submit': []}
    if not (OUT / 'plan.json').exists():
        return st
    plan = read(OUT / 'plan.json')
    left = [r for r in plan['rows'] if not (OUT / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(left)
    if not left:
        return {**st, 'state': 'complete'}
    if any((OUT / 'units' / f'{r["id"]}.FAILED.json').exists() for r in left):
        return {**st, 'state': 'failed_unit_review'}
    rec = receipts()
    if not rec['pass']:
        return {**st, 'state': 'engineering_probe_failed'} if rec['other'] else {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
    return {**st, 'state': 'ready', 'ready': len(left), 'slots': 2, 'submit': [SBATCH, '--worker']}


def main():
    ap = argparse.ArgumentParser()
    for flag in ('make_plan', 'smoke', 'worker'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--probe-unit')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = read(OUT / 'plan.json'); assert plan['sources'] == sources(), 'frozen source drift'
    SRC.verify(read(SRC.BASE / 'plan.json'))
    if a.unit or a.probe_unit:
        run_unit(next(r for r in plan['rows'] if r['id'] in (a.unit, a.probe_unit)), plan, probe=bool(a.probe_unit)); return
    if a.smoke:
        job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
        try:
            for row in plan['rows'][:2]:
                assert subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--probe-unit', row['id']]).returncode == 0, row['arm']
                rec = read(OUT / 'probes' / job / 'units' / f'{row["id"]}.json')
                assert all(c['state_digest_unchanged'] for c in rec['zero_update_checks'].values()) and all(rec['code_checks'].values())
                receipt['units'].append({'arm': row['arm'], 'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb'], 'n_rows': rec['n_rows']})
            receipt['status'] = 'pass'
        except BaseException:
            receipt.update(status='failed', traceback=traceback.format_exc()); raise
        finally:
            write(OUT / 'probes' / job / 'receipt.json', receipt)
        return
    assert a.worker and receipts()['pass'], 'no passing smoke'
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
            if rc or not path.exists():
                write(OUT / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('aln42 source diag unit failed')
        break


if __name__ == '__main__':
    main()
