"""Gate 2: load released EEG + audio + projection + CALRA weights into the official classes; explicit key audit.

Audit A: the official loader as-is (strict=False semantics by name+shape).  Audit B: + the mechanical pos-conv key rename.
For every checkpoint tensor: consumed (bitwise equal after load) / not found / shape mismatch.
For every model tensor: loaded from checkpoint or left at its constructor/HF value, grouped per module.
"""
import collections, json, os, sys
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm_common as C

out = sys.argv[1]
assert C.sha256_file(C.CKPT) == C.CKPT_SHA
ck = C.safe_load(C.CKPT)
sd = ck['model_state_dict']


def module_of(k):
    parts = k.split('.')
    if parts[0] in ('eeg_encoder', 'audio_encoder', 'eeg_model', 'audio_model'):
        return '.'.join(parts[:3]) if parts[1] in ('model', 'encoder', 'feature_extractor', 'feature_projection') else '.'.join(parts[:2])
    return parts[0]


def audit(model):
    msd = model.state_dict()
    rows = []
    consumed_model_keys = {}
    for k, v in sd.items():
        mk = C.official_map(k)
        if mk in msd and msd[mk].shape == v.shape:
            st = 'loaded' if torch.equal(msd[mk], v) else 'matched_but_value_differs'
            consumed_model_keys[mk] = k
        elif k in msd and msd[k].shape == v.shape:
            st = 'loaded' if torch.equal(msd[k], v) else 'matched_but_value_differs'; mk = k; consumed_model_keys[k] = k
        elif mk in msd:
            st = f'shape_mismatch ckpt{tuple(v.shape)} model{tuple(msd[mk].shape)}'
        else:
            st = 'not_in_model'
        rows.append({'ckpt_key': k, 'model_key': mk, 'status': st, 'shape': list(v.shape)})
    # keys consumed by the pos-conv rename (audit B)
    for src, dst in C.POS_RENAME.items():
        if dst in msd and torch.equal(msd[dst], sd[src]):
            consumed_model_keys.setdefault(dst, src)
            for r in rows:
                if r['ckpt_key'] == src and r['status'] != 'loaded':
                    r['status'] = 'loaded_via_mechanical_rename'; r['model_key'] = dst
    missing = [k for k in msd if k not in consumed_model_keys]
    per_mod = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        per_mod[module_of(r['ckpt_key'])][r['status'].split(' ')[0]] += 1
    miss_mod = collections.Counter(module_of(k) for k in missing)
    return {'ckpt_tensors': len(sd), 'model_tensors': len(msd),
            'ckpt_status_counts': dict(collections.Counter(r['status'].split(' ')[0] for r in rows)),
            'per_module_ckpt_status': {m: dict(c) for m, c in sorted(per_mod.items())},
            'unexpected_or_unloaded_ckpt_keys': [r for r in rows if not r['status'].startswith('loaded')],
            'model_keys_not_from_ckpt': {k: list(msd[k].shape) for k in missing},
            'model_keys_not_from_ckpt_per_module': dict(miss_mod),
            'n_params_model': int(sum(p.numel() for p in model.parameters())),
            'n_params_from_ckpt': int(sum(msd[k].numel() for k in consumed_model_keys))}


res = {'checkpoint': C.CKPT, 'sha256': C.CKPT_SHA, 'ckpt_epoch': ck['epoch'], 'ckpt_loss': ck['loss'],
       'ckpt_args_fusion_method': ck['args'].fusion_method, 'ckpt_args_model': ck['args'].model, 'ckpt_args_input_size': ck['args'].input_size,
       'ckpt_args_finetune': ck['args'].finetune}
import transformers, timm
res['env'] = {'torch': torch.__version__, 'transformers': transformers.__version__, 'timm': timm.__version__}
model_a, args, log_a = C.build(fix_pos_conv=False, quiet=True)
res['official_args'] = {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in vars(args).items()}
res['official_loader_log_tail'] = log_a.strip().splitlines()[-3:]
res['official_loader_skipped_lines'] = [l for l in log_a.splitlines() if l.startswith('Skipped')]
res['audit_A_official_loader'] = audit(model_a)
del model_a
model_b, _, _ = C.build(fix_pos_conv=True, quiet=True)
res['audit_B_with_pos_conv_rename'] = audit(model_b)
# effective positional-conv weight equals weight_norm(g, v, dim=2) of the checkpoint tensors
conv = model_b.audio_encoder.encoder.pos_conv_embed.conv
w_eff = conv.weight.detach()
w_exp = torch._weight_norm(sd['audio_model.encoder.pos_conv_embed.conv.weight_v'], sd['audio_model.encoder.pos_conv_embed.conv.weight_g'], 2)
res['pos_conv_effective_weight_max_abs_diff'] = float((w_eff - w_exp).abs().max())
res['logit_scale_init'] = float(model_b.clip_loss.logit_scale.detach())
print(json.dumps({k: v for k, v in res.items() if not k.startswith('audit')}, indent=1, default=str))
for a in ('audit_A_official_loader', 'audit_B_with_pos_conv_rename'):
    r = res[a]
    print(a, json.dumps({k: r[k] for k in ('ckpt_tensors', 'model_tensors', 'ckpt_status_counts', 'model_keys_not_from_ckpt',
                                         'n_params_model', 'n_params_from_ckpt')}, indent=1))
    print(' unloaded ckpt keys:', [(x['ckpt_key'], x['status']) for x in r['unexpected_or_unloaded_ckpt_keys']])
json.dump(res, open(out, 'w'), indent=1, default=str)
