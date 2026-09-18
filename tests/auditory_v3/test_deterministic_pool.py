import hashlib

import pytest
import torch
from torch import nn

from auditory5.models.small_cnn import SmallEEGCNN_v1
from auditory_v3.deterministic_pool import DeterministicAdaptiveAvgPool1d, configure_pool


@pytest.mark.parametrize("length", [25, 13])
def test_native_cpu_forward_and_backward_equivalence(length):
    generator = torch.Generator().manual_seed(68001 + length)
    x_native = torch.randn(3, 7, length, generator=generator, dtype=torch.float64, requires_grad=True)
    x_replacement = x_native.detach().clone().requires_grad_(True)
    upstream = torch.randn(3, 7, 4, generator=generator, dtype=torch.float64)
    native = nn.AdaptiveAvgPool1d(4)(x_native)
    replacement = DeterministicAdaptiveAvgPool1d()(x_replacement)
    torch.testing.assert_close(replacement, native, rtol=1e-13, atol=1e-13)
    native.backward(upstream)
    replacement.backward(upstream)
    torch.testing.assert_close(x_replacement.grad, x_native.grad, rtol=1e-13, atol=1e-13)


def _state_hash(model):
    digest = hashlib.sha256()
    for name, value in model.state_dict().items():
        digest.update(name.encode())
        digest.update(value.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


def test_configure_preserves_initial_state_parameters_and_rng():
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(11)
        model = SmallEEGCNN_v1(20, 2)
        state_hash = _state_hash(model)
        keys = tuple(model.state_dict())
        parameter_ids = tuple(id(parameter) for parameter in model.parameters())
        random_state = torch.get_rng_state().clone()
        assert configure_pool(model) is model
        assert configure_pool(model) is model
        assert _state_hash(model) == state_hash
        assert tuple(model.state_dict()) == keys
        assert tuple(id(parameter) for parameter in model.parameters()) == parameter_ids
        torch.testing.assert_close(torch.get_rng_state(), random_state, rtol=0, atol=0)
        assert sum(isinstance(layer, DeterministicAdaptiveAvgPool1d) for layer in model.modules()) == 1
        assert not any(isinstance(layer, nn.AdaptiveAvgPool1d) for layer in model.modules())


def test_configure_rejects_other_networks():
    with pytest.raises(TypeError):
        configure_pool(nn.Sequential(nn.AdaptiveAvgPool1d(4)))
