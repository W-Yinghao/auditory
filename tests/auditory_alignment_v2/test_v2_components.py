"""ALN2 technical checks (shape, time support, gradients, fixed heads, selection symmetry). Not scientific gates."""
import unittest

import numpy as np
import torch

from auditory_alignment.losses import cs_qmi, deduplicated_infonce, fmca_logdet_loss
from auditory_alignment_v2.audio_targets import build_head, semi_orthogonal
from auditory_alignment_v2.temporal import build_encoder, token_step, window_ranges, window_samples_v2
from auditory_alignment_v2.train import SelectionScore, selection_loss


class Windows(unittest.TestCase):
    def test_half_open_and_legacy(self):
        self.assertEqual(window_samples_v2("fau", "full", 128), (0, 77))
        self.assertEqual(window_samples_v2("fau", "early", 128), (0, 10))
        self.assertEqual(window_ranges("legacy_pool4", "fau", "full", 128), [(0, 78)])
        self.assertEqual(window_ranges("density_tokens", "private_bdf", "late", 250, pre=50), [(110, 130)])
        self.assertEqual(len(window_ranges("lag_local_tokens", "dtu", "joint", 128)), 2)
        self.assertEqual(token_step(128), 3); self.assertEqual(token_step(100), 2); self.assertEqual(token_step(250), 5)


class Encoders(unittest.TestCase):
    def _crop(self, x, anchors, a, b):
        idx = anchors[:, None] + torch.arange(a, b)[None]
        return x[:, idx].permute(1, 0, 2)  # x [C, T] -> [B, C, L]

    def test_outputs_and_support(self):
        torch.manual_seed(0)
        for arch in ("legacy_pool4", "density_tokens", "lag_local_tokens"):
            for win in ("full", "early", "late", "joint"):
                W = window_ranges(arch, "fau", win, 128)
                enc = build_encoder(arch, 31, 16, W, 128).eval()
                x = torch.randn(31, 600, requires_grad=True); anchors = torch.tensor([50, 200, 400])
                u = enc([self._crop(x, anchors, a, b) for a, b in W])
                self.assertEqual(tuple(u.shape), (3, 16))
                self.assertTrue(torch.allclose(u.norm(dim=1), torch.ones(3), atol=1e-5))
                u.sum().backward()
                inside = torch.zeros(600, dtype=torch.bool)
                for t in anchors.tolist():
                    for a, b in W:
                        inside[t + a:t + b] = True
                self.assertEqual(float(x.grad[:, ~inside].abs().sum()), 0.0, f"{arch} {win} reads outside its window")
                x2 = x.detach().clone(); x2[:, ~inside] = 1e3
                u2 = enc([self._crop(x2, anchors, a, b) for a, b in W])
                self.assertTrue(torch.allclose(u, u2, atol=1e-6))

    def test_token_counts_grow_with_window(self):
        n = {w: build_encoder("density_tokens", 31, 16, window_ranges("density_tokens", "fau", w, 128), 128).n_tokens for w in ("early", "late", "full")}
        self.assertLess(n["early"], n["late"]); self.assertLess(n["late"], n["full"])
        enc = build_encoder("lag_local_tokens", 20, 16, window_ranges("lag_local_tokens", "private_bdf", "full", 250, pre=50), 250)
        tok = enc.forward_tokens([torch.randn(4, 20, 150)])
        self.assertEqual(tok.shape[1], enc.n_tokens)


class Heads(unittest.TestCase):
    def test_fixed_and_frozen(self):
        mu, sd = np.zeros(48), np.ones(48)
        h1 = build_head("fixed_features", 48, 16, "fau", (mu, sd)); h2 = build_head("fixed_features", 48, 16, "fau", (mu, sd))
        self.assertEqual(sum(p.numel() for p in h1.parameters() if p.requires_grad), 0)
        a = torch.randn(5, 48)
        self.assertTrue(torch.equal(h1(a), h2(a)))  # same fixed reference for every unit of a cohort
        P = semi_orthogonal(16, 8, 1)  # Federici envelope: 8 < 16, orthonormal columns
        self.assertTrue(torch.allclose(P.T @ P, torch.eye(8), atol=1e-5))
        fr = build_head("frozen_random", 48, 16, "fau")
        self.assertEqual(sum(p.numel() for p in fr.parameters() if p.requires_grad), 0)
        an = build_head("anchored_head", 48, 16, "fau", (mu, sd)).train()
        an(a); self.assertTrue(torch.isfinite(an.aux_loss()))


class Losses(unittest.TestCase):
    def test_selection_swap_symmetry_and_gradients(self):
        torch.manual_seed(1)
        u = torch.nn.functional.normalize(torch.randn(16, 16, requires_grad=True), dim=1)
        va, vi = torch.nn.functional.normalize(torch.randn(16, 16), dim=1), torch.nn.functional.normalize(torch.randn(16, 16), dim=1)
        seg = torch.arange(16) // 8
        for kind in ("cosine", "bilinear"):
            sc = SelectionScore(16, kind)
            l1, _ = selection_loss(sc, u, va, vi, seg, 2, np.random.default_rng(0))
            l2, _ = selection_loss(sc, u, va, vi, seg, 2, np.random.default_rng(5))
            self.assertAlmostEqual(float(l1), float(l2), places=5)  # order randomisation does not change the loss
            l1.backward(retain_graph=True)
        x = torch.randn(64, 16, requires_grad=True); y = torch.randn(64, 16)
        for loss in (-cs_qmi(x, y, sigma_u=1.0, sigma_v=1.0)[0], fmca_logdet_loss(x, y, ridge_u=1e-3, ridge_v=1e-3),
                     deduplicated_infonce(x, y, torch.arange(64), 0.1)):
            g, = torch.autograd.grad(loss, x)
            self.assertTrue(torch.isfinite(g).all())


if __name__ == "__main__":
    unittest.main()
