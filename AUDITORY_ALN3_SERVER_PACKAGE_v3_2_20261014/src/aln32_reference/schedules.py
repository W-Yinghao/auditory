"""Explicit epoch coverage, not a claim that production gradients were measured.

Epoch indices passed to functions are zero-based. Reports show one-based epochs.
The legacy arithmetic follows audited fm_dense/fm_aligned at 9b9e03e.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Coverage:
    name: str
    first_open_epoch: int | None
    open_epochs: int


def _check(n_blocks: int, epochs: int, warmup: int, interval: int) -> None:
    if n_blocks < 1 or epochs < 1 or warmup < 0 or interval < 1:
        raise ValueError('Invalid architecture or schedule dimensions')


def legacy_open_groups(epoch: int, n_blocks: int, warmup: int = 5,
                       interval: int = 5) -> int:
    _check(n_blocks, epoch + 1, warmup, interval)
    if epoch < warmup:
        return 0
    return min(n_blocks + 1, 1 + (epoch - warmup) // interval)


def legacy_coverage(n_blocks: int, epochs: int, warmup: int = 5,
                    interval: int = 5) -> dict:
    """All groups allowed (random_full/pretrained_full); masks for PEFT differ."""
    _check(n_blocks, epochs, warmup, interval)
    names = [f'block_{i}' for i in range(n_blocks - 1, -1, -1)] + ['non_block']
    rows = []
    for gi, name in enumerate(names):
        active = [ep + 1 for ep in range(epochs)
                  if gi < legacy_open_groups(ep, n_blocks, warmup, interval)]
        rows.append(asdict(Coverage(name, active[0] if active else None, len(active))))
    return {'n_blocks': n_blocks, 'epochs': epochs,
            'final_open_blocks': min(n_blocks, legacy_open_groups(epochs-1, n_blocks, warmup, interval)),
            'non_block_open': rows[-1]['open_epochs'] > 0,
            'groups': rows,
            'coverage_kind': 'arithmetic_allowed_epochs_not_measured_optimizer_updates'}


def full_update_flags(epoch: int, allowed: list[bool], recipe: str,
                      warmup_epochs: int = 5) -> list[bool]:
    """Return only allowed backbone-group flags; head must remain trainable.

    Do not reconstruct allowed masks from the current requires_grad state after
    freezing; store each original permitted mask once at initialization.
    """
    if epoch < 0 or warmup_epochs < 0:
        raise ValueError('Epoch/warmup must be nonnegative')
    if recipe not in ('full_onestep_v1', 'warmup_then_all_v1'):
        raise ValueError(f'Unknown recipe: {recipe}')
    open_all = recipe == 'full_onestep_v1' or epoch >= warmup_epochs
    return [bool(a and open_all) for a in allowed]


def update_coverage_from_steps(names: list[str], step_counts: list[int]) -> dict:
    """Summarize caller-measured optimizer updates, not inferred requires_grad."""
    if len(names) != len(step_counts) or len(set(names)) != len(names):
        raise ValueError('Unique names and matching step counts required')
    if any(not isinstance(x, int) or x < 0 for x in step_counts):
        raise ValueError('Counts must be nonnegative integers')
    return {'steps': dict(zip(names, step_counts)),
            'never_updated': [n for n, s in zip(names, step_counts) if s == 0]}
