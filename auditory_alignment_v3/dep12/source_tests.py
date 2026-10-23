"""DEP12 source-line technical checks on real small batches (package 03 §7). GPU, Slurm only; no outcome threshold.

Checks (each returns a dict; any failed assertion fails the smoke):
  reference      the dep12 objective file is the byte copy of the package reference (which passed 10/10 Torch checks)
  access         stream episodes are within-listener, legal and guarded; dev panel listeners/families disjoint from fit
  objectives     real update-0 episode at the initial state: torch raw / centered CS == numpy reference; centered gradient ==
                 raw gradient - mean permuted gradient (null not detached, and != raw gradient); WRONG control: admissible map,
                 finite and not constructively zero; InfoNCE / sigmoid finite
  params         full: every backbone tensor gets gradient at update 1 (mask token exempt); LoRA: only the 48 Q/V adapters +
                 heads train, two optimizer steps change exactly the Q and V row blocks of in_proj_weight and nothing else
  montage        encoders.represent on the 64 / 31 / 20 / 32-channel montages, unit rows, padding validation
  resume         deterministic 6 updates == 3 updates + save + resume + 3 updates (max |diff| of every model tensor)
"""
from __future__ import annotations

import math
import shutil
from pathlib import Path

import numpy as np

from . import objectives as OBJ, source_common as SC, source_sampler as SS, trainer as TR


def reference():
    return {'dep12_copy_sha256': SC.sha(Path(OBJ.T.__file__)), 'package_sha256': OBJ.REFERENCE_SHA256,
            'equal': SC.sha(Path(OBJ.T.__file__)) == OBJ.REFERENCE_SHA256,
            'package_server_verification': 'private/auditory_alignment_v3/dep12/work/verify_training_objectives.json'}


def access(pool):
    P, rec = SS.load_panels()
    fit_fam = {int(f) for p in pool.split['fit'].values() for f in p}; dev_fam = {int(f) for p in pool.split['dev'].values() for f in p}
    assert not set(pool.people['fit']) & set(pool.people['dev']) and not fit_fam & dev_fam
    assert set(pool.seg['participant'][P['dev_rows']].tolist()) <= set(pool.people['dev'])
    assert set(int(f) for f in pool.seg['family'][P['dev_rows']]) <= dev_fam
    out = {'fit_dev_people_disjoint': True, 'fit_dev_families_disjoint': True}
    for seed in (3401, 3407, 3413):
        out[f'stream_{seed}'] = SS.check_stream(seed, pool, sample=range(0, 10000, 97))
    return out


def objectives(model, data, sig, stream, n):
    import torch
    from . import dependence_measure as DM
    u0 = 0; rr = stream['rows'][u0].astype(np.int64); oo = stream['off'][u0].astype(np.int64)
    x = data.eeg(rr.reshape(-1), oo.reshape(-1)); A, _ = data.audio(rr.reshape(-1), oo.reshape(-1))
    model.eval()
    with torch.no_grad():
        proj, _ = model(x)
    out = {}
    for v in TR.VIEWS:
        su, sy = sig['views'][v]['sigma_u'], sig['views'][v]['sigma_y']
        u = proj[v][:n].detach().double().clone().requires_grad_(True); y = A[v][:n].detach().double()
        P = stream['perm'][u0, 0].astype(np.int64); w = stream['wrong'][u0, 0].astype(np.int64)
        K, L = DM.gaussian_gram(u.detach().cpu().numpy(), su), DM.gaussian_gram(y.cpu().numpy(), sy)
        np_raw = DM.parzen_cs(K, L)['raw_cs_nats']
        np_perm = [DM.parzen_cs(K, L[np.ix_(p, p)])['raw_cs_nats'] for p in P]
        l_raw, s_raw = OBJ.episode_loss('raw_cs', u, y, sigma_u=su, sigma_y=sy)
        g_raw = torch.autograd.grad(l_raw, u)[0]
        l_c, s_c = OBJ.episode_loss('cs_pair', u, y, sigma_u=su, sigma_y=sy, perms=P)
        g_c = torch.autograd.grad(l_c, u)[0]
        g_perm = []
        for p in P:
            pi = torch.as_tensor(p, device=y.device)
            lp, _ = OBJ.episode_loss('raw_cs', u, y.index_select(0, pi), sigma_u=su, sigma_y=sy)
            # D(K, P L P^T) with rows of y permuted: the same Gram as index_select on both axes of L
            g_perm.append(torch.autograd.grad(lp, u)[0])
        # loss_c = -(D - mean D_b) = loss_raw - mean(loss_b)  =>  grad = g_raw - mean(g_b)
        g_expect = g_raw - torch.stack(g_perm).mean(0)
        l_w, s_w = OBJ.episode_loss('cs_pair_wrong', u, y, sigma_u=su, sigma_y=sy, perms=P, wrong=w)
        l_n, _ = OBJ.episode_loss('info_nce', u.float(), y.float()); l_s, s_s = OBJ.episode_loss('sigmoid', u.float(), y.float())
        res = {'raw_torch': s_raw['raw_cs_nats'], 'raw_numpy': np_raw, 'raw_abs_diff': abs(s_raw['raw_cs_nats'] - np_raw),
               'centered_torch': s_c['centered_cs_nats'], 'centered_numpy': np_raw - float(np.mean(np_perm)),
               'centered_abs_diff': abs(s_c['centered_cs_nats'] - (np_raw - float(np.mean(np_perm)))),
               'grad_identity_max_abs_diff': float((g_c - g_expect).abs().max()),
               'grad_centered_vs_raw_max_abs_diff': float((g_c - g_raw).abs().max()),
               'wrong_centered_nats': s_w['centered_cs_nats'], 'wrong_raw_nats': s_w['raw_cs_nats'],
               'info_nce': float(l_n), 'sigmoid': float(l_s), 'sigmoid_bias': s_s['bias'], 'sigma_u': su, 'sigma_y': sy}
        assert res['raw_abs_diff'] < 1e-8 and res['centered_abs_diff'] < 1e-8, res
        assert res['grad_identity_max_abs_diff'] < 1e-10 and res['grad_centered_vs_raw_max_abs_diff'] > 0, res
        assert math.isfinite(res['wrong_centered_nats']) and abs(res['wrong_centered_nats']) > 0
        assert math.isfinite(res['info_nce']) and math.isfinite(res['sigmoid']) and abs(res['sigmoid_bias'] + math.log(n - 1)) < 1e-12
        out[v] = res
    return out


def params(seed, data, stream, sig, n):
    import torch
    out = {}
    for mode in TR.MODES:
        torch.manual_seed(0)
        model, groups, info = TR.build_model(mode, seed, TR.DEVICE); opt, sched = TR.make_optimizer(groups)
        before = {k: v.detach().cpu().clone() for k, v in model.merged_net_state().items()}
        heads0 = {k: v.detach().cpu().clone() for k, v in model.heads.state_dict().items()}
        model.train(); grads_ok = None
        for u in range(2):
            rr = stream['rows'][u].astype(np.int64); oo = stream['off'][u].astype(np.int64)
            x = data.eeg(rr.reshape(-1), oo.reshape(-1)); A, _ = data.audio(rr.reshape(-1), oo.reshape(-1))
            proj, _ = model(x); total = 0.0
            for j in range(2):
                sl = slice(j * n, (j + 1) * n)
                for v in TR.VIEWS:
                    l, _ = OBJ.episode_loss('cs_pair', proj[v][sl], A[v][sl], sigma_u=sig['views'][v]['sigma_u'],
                                            sigma_y=sig['views'][v]['sigma_y'], perms=stream['perm'][u, j].astype(np.int64))
                    total = total + l / 6
            opt.zero_grad(set_to_none=True); total.backward()
            if u == 0:
                trainable = [(nm, p) for nm, p in model.bb.named_parameters() if p.requires_grad]
                nograd = [nm for nm, p in trainable if p.grad is None or not bool(torch.any(p.grad != 0))]
                grads_ok = {'trainable_backbone_tensors': len(trainable), 'without_gradient': nograd}
            torch.nn.utils.clip_grad_norm_(groups['backbone'] + groups['heads'], TR.CLIP); opt.step(); sched.step()
        after = model.merged_net_state()
        changed = sorted(k for k in before if not torch.equal(before[k], after[k].cpu()))
        rec = {'info': {k: info[k] for k in ('n_backbone_trainable', 'n_heads_trainable', 'n_backbone_total', 'recipe')},
               'update1_gradients': grads_ok, 'changed_backbone_tensors_after_2_steps': len(changed),
               'heads_changed': any(not torch.equal(heads0[k], v.cpu()) for k, v in model.heads.state_dict().items()),
               'lr_after_2_steps': opt.param_groups[0]['lr'], 'lr_expected': TR.LR * TR.lr_factor(2)}
        assert rec['heads_changed'] and abs(rec['lr_after_2_steps'] - rec['lr_expected']) < 1e-15
        if mode == 'full':
            assert info['n_backbone_trainable'] == info['n_backbone_total']
            assert grads_ok['without_gradient'] == ['net.patch_embedding.mask_encoding'], grads_ok
            rec['changed_fraction'] = len(changed) / len(before)
        else:
            assert len(info['lora_map']) == 24 and info['n_backbone_trainable'] == 24 * 4 * 8 * 100   # 24 MHA modules x (Q, V) = 48 adapters
            assert all(k.endswith('in_proj_weight') for k in changed) and len(changed) == 24, changed
            assert all(nm.endswith(('.A_q', '.A_v') + TR.INERT_SINGLE_PATCH) for nm in grads_ok['without_gradient']), grads_ok
            inert = [nm for nm in grads_ok['without_gradient'] if nm.endswith('self_attn_t.parametrizations.in_proj_weight.0.B_q')]
            assert len(inert) == 12, inert
            e = 100; rows = {}
            for k in changed:
                d = (after[k].cpu() - before[k]).abs().amax(1)
                rows[k] = [bool(d[:e].any()), bool(d[e:2 * e].any()), bool(d[2 * e:].any())]
                want = [False, False, True] if '.self_attn_t.' in k else [True, False, True]
                assert rows[k] == want, (k, rows[k])
            rec['qkv_rows_changed_pattern'] = ('self_attn_s: Q yes / K no / V yes (12 tensors); self_attn_t: Q no / K no / V yes (12 '
                                               'tensors; single key -> Q adapter structurally inert)')
            rec['inert_lora_tensors'] = len(inert)
            rec['lora_map_first'] = info['lora_map'][0]
        out[mode] = rec
        del model, opt
    return out


def montage():
    import torch
    from . import encoders as ENC
    enc = ENC.load('B0', TR.DEVICE); out = {}
    for key in ('dtu', 'fau', 'private_bdf', 'federici'):
        names = list(ENC.montages()[key]); x = torch.randn(5, len(names), 200, device=TR.DEVICE); pm = torch.zeros(5, 200, dtype=torch.bool)
        if key == 'private_bdf':
            x[..., :40] = 0; pm[:, :40] = True
        U = enc.represent(x, names, pm)
        out[key] = {'D': int(U.shape[1]), 'norm_err': float((U.norm(dim=1) - 1).abs().max()), 'montage': enc.last_call['montage']}
        assert out[key]['norm_err'] < 1e-5 and U.shape[1] == len(names) * 200
    try:
        enc.represent(torch.randn(2, 20, 200), list(ENC.montages()['private_bdf'])[::-1]); ok = False
    except ValueError:
        ok = True
    assert ok, 'a permuted montage must be refused'
    out['permuted_order_refused'] = True
    return out


def resume(tmp_root):
    """Deterministic: A = 0->6; B = 0->3 (stop) then resume 3->6; compare every model tensor and the optimizer moments."""
    import torch
    tmp_root = Path(tmp_root)
    a, b = tmp_root / 'resumeA', tmp_root / 'resumeB'
    for d in (a, b):
        if d.exists():
            shutil.rmtree(d)
    quiet = lambda *x, **k: None
    TR.train('cs_pair', 'lora', 3401, 6, probe_dir=a, deterministic=True, log=quiet)
    TR.train('cs_pair', 'lora', 3401, 6, probe_dir=b, deterministic=True, stop_after=3, log=quiet)
    TR.train('cs_pair', 'lora', 3401, 6, probe_dir=b, deterministic=True, log=quiet)
    out = {}
    for mode_dir in ('cs_pair.lora.s3401',):
        sa = torch.load(a / 'store' / mode_dir / 'resume.pt', map_location='cpu', weights_only=False)
        sb = torch.load(b / 'store' / mode_dir / 'resume.pt', map_location='cpu', weights_only=False)
        assert sa['step'] == sb['step'] == 6
        dm = max(float((sa['model'][k].float() - sb['model'][k].float()).abs().max()) for k in sa['model'])
        do = 0.0
        for k, st in sa['optimizer']['state'].items():
            for f in ('exp_avg', 'exp_avg_sq'):
                do = max(do, float((st[f] - sb['optimizer']['state'][k][f]).abs().max()))
        out[mode_dir] = {'max_abs_diff_model': dm, 'max_abs_diff_adam_moments': do, 'steps': 6, 'split_at': 3,
                         'lr_equal': sa['scheduler']['last_epoch'] == sb['scheduler']['last_epoch']}
    # production units run with the default (non-deterministic, faster) kernels: restore them for the timing runs that follow
    torch.use_deterministic_algorithms(False)
    torch.backends.cudnn.deterministic = False
    out['deterministic_flags_reset_after_test'] = True
    return out
