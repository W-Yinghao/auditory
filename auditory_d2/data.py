"""Window sampling over the D1 continuous exports. Memory-mapped; no epochs, no events."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

WINDOW_SECONDS = 8.0
QC_BLOCK_SECONDS = 4.0
MAX_BAD_CHANNEL_FRACTION = 0.10


class RecordStore:
    """One D1-exported recording, with per-window usability from the stored QC blocks."""

    def __init__(self, root: Path, run: str, container_id: str, *,
                 window_seconds: float = WINDOW_SECONDS,
                 max_bad_fraction: float = MAX_BAD_CHANNEL_FRACTION,
                 preload: bool = False):
        directory = root / "private/auditory_d1" / run / "arrays"
        self.container_id = container_id
        self.meta = json.loads((directory / f"{container_id}.json").read_text())
        self.path = directory / f"{container_id}.npy"
        self.rate = float(self.meta["rate_hz"])
        self.n_channels = int(self.meta["n_channels"])
        self.window = int(round(window_seconds * self.rate))
        self._data = None
        self._preload = preload
        qc_path = directory / f"{container_id}_qc.npz"
        with np.load(qc_path, allow_pickle=False) as store:
            over = store["channels_over_threshold"].astype(np.float64)
        blocks_per_window = int(round(window_seconds / QC_BLOCK_SECONDS))
        bad = over / max(self.n_channels, 1)
        usable_block = bad <= max_bad_fraction
        n = usable_block.size - blocks_per_window + 1
        if n <= 0:
            self.starts = np.empty(0, dtype=np.int64)
        else:
            windows_ok = np.ones(n, dtype=bool)
            for offset in range(blocks_per_window):
                windows_ok &= usable_block[offset:offset + n]
            # A window must also lie inside one stored interval.
            block = int(round(QC_BLOCK_SECONDS * self.rate))
            starts = np.nonzero(windows_ok)[0].astype(np.int64) * block
            self.starts = np.array([s for s in starts if self._inside_interval(s)], dtype=np.int64)
        self.usable_fraction = float(self.starts.size * blocks_per_window
                                     / max(usable_block.size, 1))

    def _inside_interval(self, start: int) -> bool:
        stop = start + self.window
        return any(row["start"] <= start and stop <= row["stop"] for row in self.meta["intervals"])

    @property
    def data(self) -> np.ndarray:
        if self._data is None:
            # Training draws each window thousands of times; reading it from the memory
            # map every step makes the disk, not the GPU, the bottleneck.
            self._data = (np.load(self.path).astype(np.float32) if self._preload
                          else np.load(self.path, mmap_mode="r"))
        return self._data

    def nbytes(self) -> int:
        return int(self.n_channels) * int(self.meta["n_samples"]) * 4

    def read(self, start: int) -> np.ndarray:
        block = self.data[:, start:start + self.window]
        return block if block.dtype == np.float32 else np.asarray(block, dtype=np.float32)


def record_scale(store: RecordStore, *, probe_windows: int = 24, seed: int = 20260919) -> float:
    """One robust gain per recording: the median absolute deviation over sampled windows.

    Dividing by a single scalar removes recording gain without flattening the relative
    amplitude structure across channels, which per-channel scaling would destroy.
    """
    if store.starts.size == 0:
        return 1.0
    rng = np.random.default_rng(seed)
    picks = rng.choice(store.starts, size=min(probe_windows, store.starts.size), replace=False)
    values = np.concatenate([np.abs(store.read(int(s))).ravel() for s in picks])
    scale = float(np.median(values))
    return scale if scale > 1e-6 else 1.0


class WindowSampler:
    """Draws windows from a set of records with a fixed channel subset."""

    def __init__(self, stores: list[RecordStore], channels: np.ndarray, scales: np.ndarray,
                 *, normalisation: str = "record_robust"):
        if normalisation not in ("none", "record_robust"):
            raise ValueError(f"D2_UNKNOWN_NORMALISATION:{normalisation}")
        self.stores = stores
        self.channels = np.asarray(channels, dtype=int)
        self.scales = np.asarray(scales, dtype=np.float32)
        self.normalisation = normalisation
        self.index = np.array([(i, int(s)) for i, store in enumerate(stores)
                               for s in store.starts], dtype=np.int64)

    def __len__(self) -> int:
        return int(self.index.shape[0])

    def batch(self, rows: np.ndarray) -> np.ndarray:
        out = np.empty((len(rows), self.channels.size,
                        self.stores[0].window), dtype=np.float32)
        for position, row in enumerate(rows):
            record, start = self.index[row]
            window = self.stores[record].read(int(start))[self.channels]
            if self.normalisation == "record_robust":
                window = window / self.scales[record]
            out[position] = window
        return out

    def channel_view(self, channels: np.ndarray) -> "WindowSampler":
        """Same records and windows, a different electrode subset."""
        view = WindowSampler.__new__(WindowSampler)
        view.stores = self.stores
        view.channels = np.asarray(channels, dtype=int)
        view.scales = self.scales
        view.normalisation = self.normalisation
        view.index = self.index
        return view

    def record_of(self, rows: np.ndarray) -> np.ndarray:
        return self.index[rows, 0]


def evaluation_rows(sampler: WindowSampler, record: int, *, stride: int = 1) -> np.ndarray:
    rows = np.nonzero(sampler.index[:, 0] == record)[0]
    return rows[::stride]


class GpuWindowBank:
    """Whole labelled corpus resident on the accelerator.

    Assembling batches in numpy would move about 130 MB per step; at the step counts this
    study needs that makes host memory, not the GPU, the bottleneck. The corpus here is
    a few gigabytes, so it is concatenated once into one device tensor and every batch
    becomes a device-side gather.
    """

    def __init__(self, stores: list, scales: np.ndarray, device, *,
                 normalisation: str = "record_robust", store_dtype: str = "float32"):
        import torch

        if normalisation not in ("none", "record_robust"):
            raise ValueError(f"D2_UNKNOWN_NORMALISATION:{normalisation}")
        cast = {"float32": torch.float32, "float16": torch.float16}[store_dtype]
        self.normalisation = normalisation
        self.window = stores[0].window
        self.rate = stores[0].rate
        self.device = device
        offsets, pieces, index = [], [], []
        total = 0
        for record, store in enumerate(stores):
            array = np.asarray(store.data, dtype=np.float32)
            if normalisation == "record_robust":
                array = array / np.float32(scales[record])
            pieces.append(torch.from_numpy(np.ascontiguousarray(array)).to(cast))
            offsets.append(total)
            for start in store.starts:
                index.append((record, total + int(start)))
            total += array.shape[1]
        self.bank = torch.cat(pieces, dim=1).to(device)
        self.index = torch.tensor(index, dtype=torch.long, device=device)
        self.record = self.index[:, 0]
        self.start = self.index[:, 1]
        self.n_channels = int(self.bank.shape[0])
        self.offsets = offsets

    def __len__(self) -> int:
        return int(self.index.shape[0])

    def batch(self, rows, channels):
        import torch

        starts = self.start[rows]
        span = torch.arange(self.window, device=self.device)
        positions = starts[:, None] + span[None, :]
        gathered = self.bank[channels][:, positions]
        return gathered.permute(1, 0, 2).contiguous().float()

    def rows_for(self, records) -> "torch.Tensor":
        import torch

        wanted = torch.as_tensor(records, dtype=torch.long, device=self.device)
        return torch.nonzero(torch.isin(self.record, wanted), as_tuple=False).squeeze(1)
