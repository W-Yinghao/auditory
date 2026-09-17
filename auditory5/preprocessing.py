"""Fixed causal preprocessing with explicit original-sample coordinates.

Each actual stored continuous interval (and each independent validation
interval) needs its own reset. The only temporal filter is forward SOS HP4
0.5 Hz followed by LP8 30 Hz at the original sampling rate. No baseline,
trialwise normalization, interpolation, or phase compensation is performed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, sosfilt


HA_CHANNELS = (
    "Fp1", "Fp2", "Fz", "F3", "F4", "F7", "F8", "Cz", "C3", "C4",
    "T3", "T4", "Pz", "P3", "P4", "T5", "T6", "Oz", "O1", "O2",
)
LEFT_CHANNELS = ("Fp1", "F3", "F7", "C3", "T3", "P3", "T5", "O1")
RIGHT_CHANNELS = ("Fp2", "F4", "F8", "C4", "T4", "P4", "T6", "O2")


def _integer_sample(value: int, name: str) -> int:
    converted = int(value)
    if isinstance(value, (bool, np.bool_)) or value != converted or converted < 0:
        raise ValueError(f"{name} must be a nonnegative integer sample index")
    return converted


def fixed_sos(original_fs: float) -> np.ndarray:
    """Return HP4 then LP8 Butterworth SOS, frequencies specified in Hz."""
    fs = float(original_fs)
    if not math.isfinite(fs) or fs <= 60:
        raise ValueError("original_fs must exceed 60 Hz for the fixed 30 Hz low-pass")
    return np.concatenate((
        butter(4, 0.5, btype="highpass", fs=fs, output="sos"),
        butter(8, 30.0, btype="lowpass", fs=fs, output="sos"),
    ))


@dataclass(frozen=True)
class ImpulseSupport:
    """Empirical absolute-tail support; IIR support remains mathematically infinite."""

    original_fs: float
    tolerance: float
    support_samples: int
    support_seconds: float
    guard_samples: int
    guard_seconds: float
    impulse_length_samples: int
    impulse_length_seconds: float
    absolute_sum: float
    absolute_tail_fraction: float
    terminal_half_fraction: float
    numerical_tail_check: str = "terminal_half_below_tolerance_times_1e-3"


def effective_impulse_support(
    original_fs: float,
    *,
    tolerance: float = 1e-6,
    minimum_guard_seconds: float = 20.0,
    initial_duration_seconds: float = 60.0,
    maximum_duration_seconds: float = 960.0,
) -> ImpulseSupport:
    """Measure the first lag k with sum(abs(h[k:]))/sum(abs(h)) < tolerance.

    The measured horizon doubles until its terminal half contributes less
    than tolerance*1e-3. This numerical convergence check is recorded; it is
    not a proof of finite IIR support. Failure to converge is a hard error.
    Startup guard is independently max(20 s by default, measured support).
    Values are samples at ORIGINAL Hz; reported seconds divide by that Hz.
    """
    fs = float(original_fs)
    sos = fixed_sos(fs)
    if not math.isfinite(tolerance) or not 0 < tolerance < 1:
        raise ValueError("tolerance must be strictly between zero and one")
    for value in (minimum_guard_seconds, initial_duration_seconds, maximum_duration_seconds):
        if not math.isfinite(value) or value <= 0:
            raise ValueError("support durations must be finite positive seconds")
    if initial_duration_seconds > maximum_duration_seconds:
        raise ValueError("initial impulse horizon exceeds its maximum")
    length = max(2, math.ceil(initial_duration_seconds * fs))
    maximum = max(2, math.ceil(maximum_duration_seconds * fs))
    while True:
        impulse = np.zeros(length, dtype=np.float64)
        impulse[0] = 1.0
        response = np.abs(sosfilt(sos, impulse))
        total = float(response.sum())
        if not math.isfinite(total) or total <= 0:
            raise ValueError("invalid impulse response")
        terminal = float(response[length // 2:].sum() / total)
        if terminal < tolerance * 1e-3:
            break
        if length >= maximum:
            raise ValueError("impulse horizon did not establish numerical tail convergence")
        length = min(2 * length, maximum)
    tails = np.concatenate((np.cumsum(response[::-1])[::-1], [0.0])) / total
    support = int(np.flatnonzero(tails < tolerance)[0])
    guard = max(math.ceil(minimum_guard_seconds * fs), support)
    return ImpulseSupport(
        original_fs=fs,
        tolerance=tolerance,
        support_samples=support,
        support_seconds=support / fs,
        guard_samples=guard,
        guard_seconds=guard / fs,
        impulse_length_samples=length,
        impulse_length_seconds=length / fs,
        absolute_sum=total,
        absolute_tail_fraction=float(tails[support]),
        terminal_half_fraction=terminal,
    )


@dataclass(frozen=True)
class ProcessedChunk:
    """Arrays retain all samples; startup eligibility is an explicit mask."""

    data: dict[str, np.ndarray]
    source_samples: np.ndarray
    guard_valid: np.ndarray
    original_fs: float
    processed_fs: float
    decimation_factor: int
    grid_origin_sample: int
    segment_start_sample: int
    bank: str


@dataclass(frozen=True)
class Epoch:
    data: dict[str, np.ndarray]
    source_samples: np.ndarray
    times_s: np.ndarray
    eligible: bool
    reject_reasons: tuple[str, ...]


class CausalPreprocessor:
    """Stateful raw-channel reference/filter/decimator for one continuous interval.

    ``process`` requires consecutive original sample positions. A true gap or
    an independent train/test interval must call ``reset_segment``. The
    decimation grid stays anchored at ``grid_origin_sample`` even after reset;
    neither chunk boundaries nor event onsets can change its phase.

    P1 defaults to the fixed 20 HA channels. For a verified native MFF layout,
    callers may supply its explicit ``p1_channels``; no mapping is inferred.
    P2 selects disjoint raw left/right channels, references and filters each
    separately. Midline/ear channels cannot affect either spatial branch.
    """

    def __init__(
        self,
        original_fs: float,
        channel_names: tuple[str, ...] | list[str],
        *,
        bank: str = "P1_CAUSAL20",
        p1_channels: tuple[str, ...] | list[str] = HA_CHANNELS,
        left_channels: tuple[str, ...] | list[str] = LEFT_CHANNELS,
        right_channels: tuple[str, ...] | list[str] = RIGHT_CHANNELS,
        segment_start_sample: int = 0,
        grid_origin_sample: int = 0,
        support: ImpulseSupport | None = None,
    ):
        self.original_fs = float(original_fs)
        self.sos = fixed_sos(self.original_fs)
        self.channel_names = tuple(channel_names)
        if len(set(self.channel_names)) != len(self.channel_names):
            raise ValueError("raw channel names must be unique")
        if bank == "P1_CAUSAL20":
            groups = {"all": tuple(p1_channels)}
        elif bank == "P2_SPATIAL_SPLIT":
            groups = {"left": tuple(left_channels), "right": tuple(right_channels)}
            if set(groups["left"]) & set(groups["right"]):
                raise ValueError("spatial branches must use disjoint raw channels")
        else:
            raise ValueError("only fixed P1_CAUSAL20 and P2_SPATIAL_SPLIT are implemented")
        for names in groups.values():
            if len(names) < 2 or len(set(names)) != len(names):
                raise ValueError("reference groups require at least two unique raw channels")
            if not set(names).issubset(self.channel_names):
                raise ValueError("required raw channels are missing; no interpolation is permitted")
        self.bank = bank
        self.branch_channels = groups
        self.indices = {key: [self.channel_names.index(name) for name in names]
                        for key, names in groups.items()}
        ratio = self.original_fs / 250.0
        integer_ratio = round(ratio)
        self.decimation_factor = (integer_ratio if integer_ratio >= 1
                                  and math.isclose(ratio, integer_ratio, rel_tol=0, abs_tol=1e-12)
                                  else 1)
        self.processed_fs = self.original_fs / self.decimation_factor
        self.grid_origin_sample = _integer_sample(grid_origin_sample, "grid_origin_sample")
        self.support = support if support is not None else effective_impulse_support(self.original_fs)
        if self.support.original_fs != self.original_fs:
            raise ValueError("impulse support must use the same original sampling rate")
        if self.support.tolerance != 1e-6 or self.support.guard_seconds < 20.0:
            raise ValueError("P1/P2 require tail tolerance 1e-6 and at least 20 s startup guard")
        self.reset_segment(segment_start_sample)

    def reset_segment(self, segment_start_sample: int) -> None:
        """Reset all IIR states without changing the original decimation grid."""
        self.segment_start_sample = _integer_sample(segment_start_sample, "segment_start_sample")
        self.next_sample = self.segment_start_sample
        self._states = {key: np.zeros((len(self.sos), len(indices), 2), dtype=np.float64)
                        for key, indices in self.indices.items()}

    def process(self, raw: np.ndarray, *, start_sample: int) -> ProcessedChunk:
        """Process [raw_channels, samples]; reject unannounced gaps and NaNs."""
        start = _integer_sample(start_sample, "start_sample")
        if start != self.next_sample:
            raise ValueError("noncontiguous raw samples require an explicit segment reset")
        x = np.asarray(raw, dtype=np.float64)
        if x.ndim != 2 or x.shape[0] != len(self.channel_names):
            raise ValueError("raw must be [all named raw channels, original-rate samples]")
        if not np.isfinite(x).all():
            raise ValueError("nonfinite raw samples require explicit source/QC handling")
        samples = np.arange(start, start + x.shape[1], dtype=np.int64)
        take = (samples - self.grid_origin_sample) % self.decimation_factor == 0
        output = {}
        for key, indices in self.indices.items():
            selected = x[indices]
            referenced = selected - selected.mean(axis=0, keepdims=True)
            if x.shape[1]:
                filtered, state = sosfilt(self.sos, referenced, axis=-1, zi=self._states[key])
                self._states[key] = state
                output[key] = filtered[:, take]
            else:
                output[key] = referenced
        self.next_sample = start + x.shape[1]
        selected_samples = samples[take]
        return ProcessedChunk(
            data=output,
            source_samples=selected_samples,
            guard_valid=selected_samples - self.segment_start_sample >= self.support.guard_samples,
            original_fs=self.original_fs,
            processed_fs=self.processed_fs,
            decimation_factor=self.decimation_factor,
            grid_origin_sample=self.grid_origin_sample,
            segment_start_sample=self.segment_start_sample,
            bank=self.bank,
        )


def concatenate_chunks(chunks: list[ProcessedChunk]) -> ProcessedChunk:
    """Join output chunks for bounded records/tests, never silently bridge a gap."""
    if not chunks:
        raise ValueError("at least one chunk is required")
    first = chunks[0]
    fields = ("original_fs", "processed_fs", "decimation_factor", "grid_origin_sample",
              "segment_start_sample", "bank")
    for chunk in chunks:
        if any(getattr(chunk, field) != getattr(first, field) for field in fields):
            raise ValueError("incompatible processed chunks")
        if tuple(chunk.data) != tuple(first.data):
            raise ValueError("incompatible output branches")
    samples = np.concatenate([chunk.source_samples for chunk in chunks])
    if len(samples) > 1 and not np.all(np.diff(samples) == first.decimation_factor):
        raise ValueError("output chunks must be contiguous on the original sample grid")
    return ProcessedChunk(
        data={key: np.concatenate([chunk.data[key] for chunk in chunks], axis=-1)
              for key in first.data},
        source_samples=samples,
        guard_valid=np.concatenate([chunk.guard_valid for chunk in chunks]),
        **{field: getattr(first, field) for field in fields},
    )


def extract_epoch(
    processed: ProcessedChunk,
    onset_sample: int,
    *,
    tmin: float = -0.2,
    tmax: float = 0.5,
) -> Epoch:
    """Take [tmin,tmax) on the existing grid; do not round or shift the event.

    Event zero need not occur on a decimated grid. Exact relative output
    times are returned. Rejected/incomplete waveforms remain available.
    This function is intended for a bounded buffer, not whole long records.
    """
    onset = _integer_sample(onset_sample, "onset_sample")
    if not math.isfinite(tmin) or not math.isfinite(tmax) or tmax <= tmin:
        raise ValueError("epoch limits must be finite increasing seconds")

    def ceil_offset(seconds):
        value = seconds * processed.original_fs
        nearest = round(value)
        return nearest if abs(value - nearest) < 1e-9 else math.ceil(value)

    low = onset + ceil_offset(tmin)
    high = onset + ceil_offset(tmax)
    first_grid = low + (processed.grid_origin_sample - low) % processed.decimation_factor
    expected = max(0, (high - 1 - first_grid) // processed.decimation_factor + 1)
    take = (processed.source_samples >= low) & (processed.source_samples < high)
    selected = processed.source_samples[take]
    reasons = []
    if expected == 0 or len(selected) != expected:
        reasons.append("incomplete_epoch")
    if not processed.guard_valid[take].all():
        reasons.append("startup_guard")
    return Epoch(
        data={key: value[:, take] for key, value in processed.data.items()},
        source_samples=selected,
        times_s=(selected - onset) / processed.original_fs,
        eligible=not reasons,
        reject_reasons=tuple(reasons),
    )
