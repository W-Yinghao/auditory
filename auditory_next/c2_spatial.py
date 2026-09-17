"""Reversible C2-S sensor coordinates, distinct from sources or old CNN latents.

All arrays use [...,channel,time]. The caller supplies the actual channel names;
missing/duplicated/renamed electrodes are errors. No temporal filter, QC,
interpolation, scaling, label selection or fitted transform is performed here.
"""
from dataclasses import dataclass
import numpy as np

LEFT = ("Fp1", "F3", "F7", "C3", "T3", "P3", "T5", "O1")
RIGHT = ("Fp2", "F4", "F8", "C4", "T4", "P4", "T6", "O2")
MIDLINE = ("Fz", "Cz", "Pz", "Oz")
CHANNELS = LEFT + RIGHT + MIDLINE
COMPONENT_ORDER = ("u_L", "u_R", "u_M", "m_LR", "m_M")


def _layout(channel_names):
    names = tuple(channel_names)
    if len(names) != 20 or len(set(names)) != 20 or set(names) != set(CHANNELS):
        raise ValueError("C2_COMPLETE_20_CHANNEL_LAYOUT")
    return names, tuple(tuple(names.index(ch) for ch in group) for group in (LEFT, RIGHT, MIDLINE))


def _array(x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim < 2 or min(x.shape) == 0 or not np.isfinite(x).all():
        raise ValueError("C2_FINITE_CHANNEL_TIME_ARRAY")
    return x


def local_center(x):
    """Only the supplied group is inspected; opposite groups are not arguments."""
    x = _array(x)
    return x - x.mean(axis=-2, keepdims=True)


@dataclass(frozen=True)
class SpatialComponents:
    u_L: np.ndarray
    u_R: np.ndarray
    u_M: np.ndarray
    m_LR: np.ndarray
    m_M: np.ndarray
    channel_names: tuple
    effective_dimensions: tuple = (7, 7, 3, 1, 1)


def decompose20(x, channel_names):
    names, (li, ri, mi) = _layout(channel_names)
    x = _array(x)
    if x.shape[-2] != 20:
        raise ValueError("C2_CHANNEL_AXIS")
    left, right, midline = (np.take(x, indices, axis=-2) for indices in (li, ri, mi))
    ml, mr, mm = (group.mean(axis=-2, keepdims=True) for group in (left, right, midline))
    return SpatialComponents(local_center(left), local_center(right), local_center(midline),
                             ml - mr, mm - (ml + mr) / 2, names)


def _components(parts):
    _layout(parts.channel_names)
    values = [_array(getattr(parts, name)) for name in COMPONENT_ORDER]
    base = values[0].shape[:-2] + values[0].shape[-1:]
    for value, width in zip(values, (8, 8, 4, 1, 1)):
        if value.shape[-2] != width or value.shape[:-2] + value.shape[-1:] != base:
            raise ValueError("C2_COMPONENT_ALIGNMENT")
    for value in values[:3]:
        if not np.allclose(value.sum(axis=-2), 0., atol=1e-10, rtol=0):
            raise ValueError("C2_LOCAL_COMPONENT_NOT_CENTERED")
    return values


def reconstruct20(parts):
    """Reconstruct original-order whole-head average reference, not raw reference."""
    ul, ur, um, lr, mid = _components(parts)
    values = np.concatenate((ul + .5 * lr - .2 * mid, ur - .5 * lr - .2 * mid, um + .8 * mid), axis=-2)
    return np.take(values, [CHANNELS.index(name) for name in parts.channel_names], axis=-2)


def helmert_basis(size):
    """Fixed orthonormal basis for the zero-sum subspace; no data-dependent fit."""
    if not isinstance(size, (int, np.integer)) or size < 2:
        raise ValueError("C2_HELMERT_SIZE")
    basis = np.zeros((size, size - 1))
    for i in range(size - 1):
        basis[:i + 1, i] = 1 / np.sqrt((i + 1) * (i + 2))
        basis[i + 1, i] = -(i + 1) / np.sqrt((i + 1) * (i + 2))
    return basis


def coordinates19(parts):
    ul, ur, um, lr, mid = _components(parts)
    locals_ = [np.einsum("ck,...ct->...kt", helmert_basis(n), value)
               for n, value in zip((8, 8, 4), (ul, ur, um))]
    return np.concatenate((*locals_, lr, mid), axis=-2)


def from_coordinates19(z, channel_names):
    z = _array(z)
    names, _ = _layout(channel_names)
    if z.shape[-2] != 19:
        raise ValueError("C2_19_COORDINATES_REQUIRED")
    values = [np.einsum("ck,...kt->...ct", helmert_basis(n), z[..., start:stop, :])
              for n, start, stop in ((8, 0, 7), (8, 7, 14), (4, 14, 17))]
    return SpatialComponents(*values, z[..., 17:18, :], z[..., 18:19, :], names)


def linear_maps(channel_names):
    """Return (A[19,20], B[20,19]), with B@A equal to global-reference matrix."""
    parts = decompose20(np.eye(20), channel_names)
    forward = coordinates19(parts)
    inverse = reconstruct20(from_coordinates19(np.eye(19), channel_names))
    return forward, inverse


def bin_20ms(x, *, sfreq=250.):
    x = _array(x)
    if float(sfreq) != 250. or x.shape[-1] % 5:
        raise ValueError("C2_FIXED_250HZ_COMPLETE_20MS_BINS")
    return x.reshape(*x.shape[:-1], x.shape[-1] // 5, 5).mean(axis=-1)


def l0_views(parts, *, sfreq=250.):
    """Raw channel-coordinate S0/S1/S2 widths 16/17/22; effective 14/15/19.

    Duplication appends cyclic copies of S0 channels until width 17/22. Its
    channel order is fixed without labels. Channel-major 20 ms flatten follows.
    S2 includes redundant local coordinates; coordinates19 is the independent
    diagnostic basis. Neither change is fed into a previously trained CNN.
    """
    ul, ur, um, lr, mid = _components(parts)
    s0 = np.concatenate((ul, ur), axis=-2)
    views = dict(S0=s0, S1=np.concatenate((s0, lr), axis=-2),
                 S2=np.concatenate((s0, lr, um, mid), axis=-2), FULL20=reconstruct20(parts))
    for name, width in (("S0_DUP_S1", 17), ("S0_DUP_S2", 22)):
        views[name] = np.take(s0, np.arange(width) % 16, axis=-2)
    return {name: bin_20ms(value, sfreq=sfreq).reshape(*value.shape[:-2], -1) for name, value in views.items()}


def inject_spatial_world(kind, *, n_trials=40, n_times=25, seed=20260917):
    """Algebraic injection fixtures, not extra independent power-study worlds.

    Balanced labels with exactly zero local components in crossmean/midline
    examples make information loss demonstrable without classifier tuning.
    Noise is absent by design; reference drift is an additive invariance check.
    """
    if kind not in {"crossmean", "midline", "local_left", "reference_drift", "right_perturbation"}:
        raise ValueError("C2_INJECTION_KIND")
    if n_trials < 2 or n_trials % 2 or n_times < 1:
        raise ValueError("C2_INJECTION_SHAPE")
    rng = np.random.default_rng(seed)
    labels = np.arange(n_trials) % 2
    wave = np.ones((n_trials, 1, n_times)) * (2 * labels[:, None, None] - 1)
    x = np.zeros((n_trials, 20, n_times))
    if kind == "crossmean":
        x[:, :8] = wave; x[:, 8:16] = -wave
    elif kind == "midline":
        x[:, 16:] = wave
    elif kind == "local_left":
        x[:, 0:1] = wave; x[:, 1:2] = -wave
    else:
        x = rng.normal(size=x.shape)
    changed = x.copy()
    if kind == "reference_drift":
        changed += rng.normal(size=(n_trials, 1, n_times))
    elif kind == "right_perturbation":
        changed[:, 8:16] += rng.normal(size=(n_trials, 8, n_times)) + 3
    return dict(data=x, changed=changed, labels=labels, channel_names=CHANNELS, kind=kind)
