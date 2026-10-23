"""CPU tests for paper/encoders.py and paper/enc_models.py (no GPU, no production writes; synthetic EEG only).

Run as a Slurm CPU step: python -m pytest -q auditory_alignment_v3/paper/test_encoders.py
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
import torch

from auditory_alignment_v3.aln41 import private_ft as PF, source as SRC, support as SU, timebank as TB
from auditory_alignment_v3.paper import enc_models as EM, encoders as EN


@pytest.fixture(scope='module')
def branch(tmp_path_factory):
    path = tmp_path_factory.mktemp('mm') / 'branch.pt'
    audit = EM.mindmix_extract(path)
    return path, audit


def crops(B, C, seed=0):
    g = torch.Generator().manual_seed(seed)
    x = torch.randn(B, C, 200, generator=g)                       # private epoch [-200, 600) ms at 250 Hz
    return x, TB.crop_inputs([x[..., 50 + a:50 + b] for a, b, _ in TB.layout(250)], 250)


def test_layout_and_padding():
    lay = TB.layout(250)
    assert [(a, b, n) for a, b, n in lay] == [(-50, 50, 80), (0, 100, 80), (50, 150, 80)]
    _, z = crops(4, 20)
    assert tuple(z.shape) == (12, 20, 200) and bool((z[..., 80:] == 0).all()) and bool((z[..., :80] != 0).any())
    # REVE unfold(size 200, step 180): 80 samples cannot form a patch (error); 200 -> exactly one patch; 379 -> still one
    with pytest.raises(RuntimeError):
        torch.zeros(1, 1, 80).unfold(2, 200, 180)
    assert torch.zeros(1, 1, 379).unfold(2, 200, 180).shape[2] == 1
    assert torch.zeros(1, 1, 200).unfold(2, 200, 180).shape[2] == 1
    assert EM.ENC['REVE']['pad_to'] == 200 and EM.ENC['MINDMIX']['pad_to'] == 400


def test_channel_names():
    p = EM.channel_names('private_bdf'); m = EM.channel_names('mff')
    assert len(p) == 20 and 'T7' in p and 'T3' not in p and m == [f'E{i}' for i in range(1, 129)]


def test_reve_strict_and_tokens():
    torch.manual_seed(0)
    for cohort, C in (('private_bdf', 20), ('mff', 128)):
        m = EM.make_tokens('REVE', cohort)
        a = EM.audit(m, 'REVE')
        assert a['strict_equal'] and a['positions_equal_bank'] and a['channels'] == C and a['numel'] == a['model_numel']
        m.eval()
        _, z = crops(2, C)
        with torch.no_grad():
            h = m(z)
        assert tuple(h.shape) == (6, C, 1, 512) and bool(torch.isfinite(h).all())


def test_mindmix_extract_and_tokens(branch):
    path, audit = branch
    assert audit['strict_load'] and audit['pos_embed_is_none'] and audit['n_blocks'] == 12 and audit['embed_dim'] == 200
    assert audit['eeg_encoder_numel'] == audit['model_state_numel'] and audit['eeg_proj_tensors'] == 4
    assert 'audio_model' in audit['excluded_groups'] and 'fusion_module' in audit['excluded_groups']
    for cohort, C in (('private_bdf', 20), ('mff', 128)):
        m = EM.make_tokens('MINDMIX', cohort, path).eval()
        a = EM.audit(m, 'MINDMIX', path); assert a['strict_equal'] and a['numel'] == a['model_numel']
        _, z = crops(2, C, seed=1)
        with torch.no_grad():
            h = m(z)
            perm = torch.randperm(C, generator=torch.Generator().manual_seed(3))
            hp = m(z[:, perm])
        assert tuple(h.shape) == (6, C, 1, 400) and bool(torch.isfinite(h).all())
        assert float((hp - h[:, perm]).abs().max()) < 1e-4                 # no spatial embedding: channel-permutation equivariant
        assert float((h[..., :200] - h[..., 200:]).abs().max()) > 1e-3     # the two patch tokens differ


def test_mindmix_channel_vocabulary():
    from auditory_alignment_v3.aln42 import external_mindmix as XM
    XM.official()
    import utils as MMU                                                     # MindMix utils (repo first on sys.path)
    assert Path(MMU.__file__).parent == XM.MM_REPO
    raw = ['Fp1', 'Fp2', 'Fz', 'F3', 'F4', 'F7', 'F8', 'Cz', 'C3', 'C4', 'T3', 'T4', 'Pz', 'P3', 'P4', 'T5', 'T6', 'Oz', 'O1', 'O2']
    from auditory_alignment_v2.foundation_adapter import CHANNELS
    assert CHANNELS['private_bdf'] == raw and all(c.upper() in MMU.standard_1020 for c in raw)
    calls = [f for f in XM.MM_REPO.glob('*.py') if 'get_input_chans(' in f.read_text().replace('def get_input_chans(', '')]
    assert not calls                                                        # input_chans never computed at the pin
    src = (XM.MM_REPO / 'modeling_finetune_2.py').read_text()
    assert 'self.pos_embed = None' in src


@pytest.mark.parametrize('enc', ['MINDMIX', 'REVE'])
def test_build_ft_backward_and_support_compat(enc, branch):
    path, _ = branch
    model = EM.build_ft(enc, torch.zeros(3), 3401, 'cpu', path)
    x, _ = crops(3, 20, seed=2)
    lp, lk = model.log_probs(x)
    assert tuple(lp.shape) == (3, 2) and tuple(lk.shape) == (3, 3, 2)
    loss = -lp[:, 1].mean(); loss.backward()
    named = dict(model.bb.named_parameters())
    nograd = sorted(n for n, p in named.items() if p.grad is None)
    assert nograd == (['bb.net.cls_query_token'] if enc == 'REVE' else []), nograd
    assert 'a' in model.state_dict() and model.a.grad is not None
    model.eval()
    with torch.no_grad():
        lp, lk = model.log_probs(x)
    ref = SU.mixture_logp(model.a.detach().double().numpy(), lk.double().numpy())
    assert np.abs(ref - lp.double().numpy()).max() < 1e-5
    g = EM.param_groups(model, 0.01)
    assert g[0]['weight_decay'] == 0.01 and g[1]['weight_decay'] == 0.0
    assert sum(p.numel() for gg in g for p in gg['params']) == sum(p.numel() for p in model.parameters())


def test_rows_and_rule():
    fr, ft = EN.frozen_rows(), EN.ft_rows()
    assert len(fr) == 4 and len({r['id'] for r in fr}) == 4
    assert len(ft) == 60 and len({r['id'] for r in ft}) == 60
    assert sum(r['stage'] == 'calibration' for r in ft) == 20 and {r['seed'] for r in ft if r['stage'] == 'calibration'} == {3401}
    assert {(r['encoder'], r['candidate'], r['lr'], r['weight_decay']) for r in ft} == {
        ('REVE', 'common', 1e-4, 1e-4), ('REVE', 'documented', 1e-4, 1e-2), ('MINDMIX', 'common', 1e-4, 1e-4), ('MINDMIX', 'documented', 1e-5, 1e-2)}
    assert EN.choose({'common': {'selected_es_nll_bits': 0.9}, 'documented': {'selected_es_nll_bits': 0.8}}) == 'documented'
    assert EN.choose({'common': {'selected_es_nll_bits': 0.8}, 'documented': {'selected_es_nll_bits': 0.9}}) == 'common'
    assert EN.choose({'documented': {'selected_es_nll_bits': 0.8}, 'common': {'selected_es_nll_bits': 0.8}}) == 'common'


def test_contexts_restore():
    keep = {k: getattr(PF, k) for k in ('BASE', 'STORE', 'LR', 'build', 'source_init', 'param_groups')}; seed = SRC.SEED
    row = next(r for r in EN.ft_rows() if r['encoder'] == 'MINDMIX' and r['candidate'] == 'documented' and r['seed'] == 3407)
    with EN.ft_ctx(row):
        assert PF.LR == 1e-5 and SRC.SEED == 3407 and PF.BASE == EN.FT_BASE
        if (EN.OUT / 'plan.json').exists():                                # provenance reads the frozen master plan
            net, a0, prov = PF.source_init('MINDMIX'); assert net is None and torch.equal(a0, torch.zeros(3))
    assert all(getattr(PF, k) is v for k, v in keep.items()) and SRC.SEED == seed
    from auditory_alignment_v3.aln41 import frozen as FZ, cross_stim as XS
    keepz = {k: getattr(FZ, k) for k in ('BASE', 'STORE', 'arm_state', 'backbone')}; xo = XS.OUT
    with EN.frozen_ctx('REVE'):
        assert FZ.BASE == EN.FZ_BASE and XS.OUT == EN.FZ_BASE
    assert all(getattr(FZ, k) is v for k, v in keepz.items()) and XS.OUT == xo


def test_fleet_status_shape():
    for lane in EN.LANES:
        st = EN.fleet_status(lane)
        assert {'name', 'lane', 'state', 'ready', 'remaining', 'slots', 'initial', 'submit'} <= set(st)
        assert st['name'].startswith('c3_s35pe')
