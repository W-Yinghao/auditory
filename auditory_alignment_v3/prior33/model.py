"""E34_PUBLIC_PRIOR model (private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.3, §2.4, §2.12, §2.15; §6.6 M4): the
name-indexed signed spatial map, the shared 64 Hz lag_local_tokens encoder, the fixed audio head in the shared coordinates, the rich
EEG heads, seeded construction and strict donor loading.

SharedEncoder(layout): NameIndexedSpatial (W [70, 16] over contract.VOCAB, b [16], bool buffer seen [70]) followed by
auditory_alignment_v2.temporal.TokenEncoder('lag_local_tokens', n_ch=16, d=32, windows=[(0, 38)], fs=64) (imported, not edited)
with branches[0].local[0] = Identity: token step 1 sample, local window 3 samples, 36 lag tokens, proj = LayerNorm(1152) ->
Linear(1152, 32), L2-normalised; 44,176 parameters (proj.1 36,896). The spatial step is per time sample, so the composition equals
the per-cohort TokenEncoder whose local[0] is the Conv1d(C, 16, 1) holding W[idx].T and b. forward(x) -> [B, 32],
forward_tokens(x) -> [B, 36, 32], trunk(x) -> [B, 1152] (pre-projection features, fed to RichHeads), project(z) -> [B, 32].
  s(x)[b, f, t] = sum_c x[b, c, t] W[idx_c, f] seen[idx_c] + b_f. Channels whose name is unseen are never read (their input is
  replaced by 0 before the map) and their W rows are 0, so they contribute exactly zero and receive zero gradient, even for
  non-finite input values. W rows of untrained names start at 0 and stay 0 under AdamW (zero gradient, zero decay of 0).

Interpretations where the design gives only a name (each is also listed as a deviation in the M4 summary):
- SharedEncoder(layout, train_names=None): layout = the input row order (aliases canonicalised via contract.canonical; duplicates
  raise); train_names = the names that get weights (default: the layout). The input of forward / forward_tokens / trunk is a tensor
  [B, C, 38] or the batchers' one-window patch list [x]. Optional keywords: layout= (a per-call row order, e.g. the cohort of a
  single-stratum donor batch; the default is the constructor's layout) and mask= ([C] or [B, C] bool, True = keep; a per-sample
  channel mask, applied exactly like an unseen channel). set_layout(layout) changes the default row order (load_donor sets the
  target layout).
- build_shared(layout, train_names, seed, rich=False): construction under torch.random.fork_rng with torch.manual_seed(seed), so the
  build is a function of its arguments and the caller's RNG stream is untouched; W rows of train_names (VOCAB order) and b ~
  U(+-1/sqrt(n_c)), n_c = len(train_names) (= the per-cohort Conv1d default bound); the temporal part keeps the PyTorch defaults of
  TokenEncoder. rich=True attaches RichHeads as `enc.rich` (state-dict keys rich.proj_ss.*, rich.proj_sc.*) after the encoder is
  built from the same RNG stream, so the APR trunk and proj start exactly as AP's.
- SharedFixedHead(sigma, P) is a FixedFeatureHead (keys std.mu = 0, std.sd = sigma, P; forward inherited) for any input width:
  the envelope head (sigma [8], P [32, 8]) and the rich audio heads (sigma_ss [32], P_ss [32, 32]; sigma_sc [8], P_sc [32, 8]).
  load_projection / fixed_heads(manifest, root) load the stored P files (allow_pickle=False) and check their float32 sha256 against
  the manifest (schema of tests/auditory_alignment_v3/prior33/fixtures.py); P is never regenerated. fixed_heads also checks each
  manifest entry against the contract, so P's provenance does not rest on the manifest builder alone: the envelope P must be
  contract.P_FILE with seed PROJ_SEED and a sha256 starting with P_SHA16 (the design count 706c4ff4441f4940); P_ss / P_sc must be
  RICH_P_FILE with seed RICH_SEEDS (contract.py pins no sha for them, so their file sha is checked against the manifest only).
- load_donor(enc, state, layout, open_new=True, strict=True) -> tensor map (also stored as enc.tensor_map). Keys: loaded (enc
  tensors set from the donor), new (enc tensors the donor does not provide; torch's load_state_dict calls these missing_keys),
  missing (donor SharedEncoder tensors that enc does not have; torch's unexpected_keys), mismatched (shape or dtype differs),
  dropped (the donor's rich.* heads), opened_rows (target-layout names the donor never saw, opened at W = 0 when open_new),
  closed_unseen (the same names when not open_new: zero contribution, zero-shot), parameter counts and fractions (opened W rows
  count as new parameters: FAU 1 - 32 / 44,176 = 99.93 % loaded), and terms (these definitions, so a record reads unambiguously
  against torch's names). The design names are kept (§2.4: "new and missing must both be empty"). strict raises on any new,
  missing or mismatched tensor and on a nonzero W row of a donor-unseen name; strict=False loads the matching tensors only.
  `state` may be the encoder state dict or a checkpoint dict holding it under "enc".
- build_target_encoder(row, layout, manifest, donor_state) returns the CPU module (drop-in for build_encoder(...); the caller moves
  it) with enc.tensor_map. Pretrained iff row.spec.init == "donor" (absent: iff donor_state is given; a contradiction raises). The
  from-scratch arm trains the target layout (train_names = layout) from spec.target_seed (absent: row.seed). Asserted: 36 tokens,
  proj in-features 1152, d 32; any of spec architecture / channel_map / fs / projection_dim / input_samples / window that is present
  must equal the contract; the manifest contract and constants when present; the layout equals manifest.montages[dataset] when
  present; the donor's seen set equals manifest.seen[dataset] (the union of the leave-target-out donor montages).
- describe(enc): temporal.describe plus the geometry, coverage and the tensor map.
"""
from __future__ import annotations

import hashlib
import math
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from auditory_alignment_v2.audio_targets import FixedFeatureHead, Standardiser
from auditory_alignment_v2.temporal import TOKEN_DIM, TokenEncoder
from auditory_alignment_v2.temporal import describe as _describe_tokens

from .contract import (CONTRACT, FS, L_IN, P_FILE, P_SHA16, P_SHAPE, PROJ_SEED, RICH_P_FILE, RICH_P_SHAPE, RICH_SEEDS, VOCAB,
                       VOCAB_INDEX, canonical)

ARCH, CHANNEL_MAP = "lag_local_tokens", "name_indexed_signed_v1"
D_SP, D_OUT, N_TOKENS = 16, 32, 36
TRUNK_DIM = N_TOKENS * TOKEN_DIM            # 1152
N_PARAMS = 44_176
RICH_PREFIX = "rich."
TENSOR_MAP_TERMS = {"new": "enc tensors absent from the donor state, initialised here (torch: missing_keys)",
                    "missing": "donor SharedEncoder tensors absent from enc (torch: unexpected_keys)"}
GEOMETRY = {"architecture": ARCH, "channel_map": CHANNEL_MAP, "fs": FS, "projection_dim": D_OUT, "input_samples": [0, L_IN],
            "window": "full"}


def names_of(layout):
    """Contract names of a layout in row order (aliases and case normalised); duplicates raise."""
    out = tuple(canonical(n) for n in layout)
    if len(set(out)) != len(out):
        raise ValueError(f"layout repeats an electrode after canonicalisation: {out}")
    return out


class NameIndexedSpatial(nn.Module):
    """s(x)[b, f, t] = sum_c x[b, c, t] W[idx_c, f] seen[idx_c] + b_f over the 70-name contract vocabulary."""

    def __init__(self, layout, train_names=None, n_out=D_SP):
        super().__init__()
        self.layout = names_of(layout)
        train = set(self.layout if train_names is None else names_of(train_names))
        rows = [VOCAB_INDEX[n] for n in VOCAB if n in train]
        if not rows:
            raise ValueError("NameIndexedSpatial: no trained electrode")
        self.W = nn.Parameter(torch.zeros(len(VOCAB), n_out))
        self.b = nn.Parameter(torch.zeros(n_out))
        self.register_buffer("seen", torch.zeros(len(VOCAB), dtype=torch.bool))
        self.register_buffer("idx", torch.tensor([VOCAB_INDEX[n] for n in self.layout]), persistent=False)
        bound, r = 1.0 / math.sqrt(len(rows)), torch.tensor(rows)
        with torch.no_grad():
            self.W[r] = torch.empty(len(rows), n_out).uniform_(-bound, bound)
            self.b.uniform_(-bound, bound)
            self.seen[r] = True
        self._idx = {}

    def set_layout(self, layout):
        self.layout = names_of(layout)
        self.idx = torch.tensor([VOCAB_INDEX[n] for n in self.layout], device=self.W.device)

    def seen_names(self):
        return [VOCAB[i] for i in torch.nonzero(self.seen).flatten().tolist()]

    def _index(self, layout, device):
        k = (tuple(layout), str(device))
        if k not in self._idx:
            self._idx[k] = torch.tensor([VOCAB_INDEX[n] for n in names_of(layout)], device=device)
        return self._idx[k]

    def forward(self, x, layout=None, mask=None):
        idx = self.idx if layout is None else self._index(layout, x.device)
        if x.ndim != 3 or x.shape[1] != len(idx):
            raise ValueError(f"NameIndexedSpatial: input [B, {len(idx)}, T] expected, got {tuple(x.shape)}")
        keep = self.seen[idx][None]
        if mask is not None:
            m = torch.as_tensor(mask, device=x.device).bool()
            keep = keep & (m[None] if m.ndim == 1 else m)
        x = x.to(self.W.dtype).masked_fill(~keep[..., None], 0.0)          # unseen / masked channels are never read
        w = self.W[idx] * self.seen[idx, None].to(self.W.dtype)
        return F.conv1d(x, w.T[..., None], self.b)


class SharedEncoder(TokenEncoder):
    """NameIndexedSpatial -> lag_local_tokens at 64 Hz (36 tokens of 32) -> LayerNorm(1152) -> Linear(1152, 32), L2-normalised."""

    def __init__(self, layout, train_names=None):
        super().__init__(ARCH, D_SP, D_OUT, [(0, L_IN)], FS)
        self.branches[0].local[0] = nn.Identity()
        self.spatial = NameIndexedSpatial(layout, train_names)
        if self.n_tokens != N_TOKENS or self.proj[1].in_features != TRUNK_DIM or self.proj[1].out_features != D_OUT:
            raise AssertionError(f"SharedEncoder geometry: {self.n_tokens} tokens, proj {self.proj[1]}")

    @property
    def layout(self):
        return self.spatial.layout

    def set_layout(self, layout):
        self.spatial.set_layout(layout)

    def seen_names(self):
        return self.spatial.seen_names()

    def forward_tokens(self, x, layout=None, mask=None):
        if isinstance(x, (list, tuple)):
            if len(x) != 1:
                raise ValueError(f"SharedEncoder: one window [(0, {L_IN})] expected, got {len(x)}")
            x = x[0]
        if x.shape[-1] != L_IN:
            raise ValueError(f"SharedEncoder: {L_IN}-sample windows expected, got {tuple(x.shape)}")
        return self.branches[0](self.spatial(x, layout, mask))

    def trunk(self, x, layout=None, mask=None):
        return self.forward_tokens(x, layout, mask).flatten(1)

    def project(self, z):
        return F.normalize(self.proj(z), dim=1)

    def forward(self, x, layout=None, mask=None):
        return self.project(self.trunk(x, layout, mask))


class RichHeads(nn.Module):
    """APR EEG-side heads rich.proj_ss and rich.proj_sc: LayerNorm(1152) -> Linear(1152, 32), L2-normalised, fed by trunk()."""

    def __init__(self):
        super().__init__()
        self.proj_ss = nn.Sequential(nn.LayerNorm(TRUNK_DIM), nn.Linear(TRUNK_DIM, D_OUT))
        self.proj_sc = nn.Sequential(nn.LayerNorm(TRUNK_DIM), nn.Linear(TRUNK_DIM, D_OUT))

    def forward(self, z):
        return {"ss": F.normalize(self.proj_ss(z), dim=1), "sc": F.normalize(self.proj_sc(z), dim=1)}


class SharedFixedHead(FixedFeatureHead):
    """v = normalize((y / sigma) P^T) with mu == 0; no trainable parameter; FixedFeatureHead keys std.mu (zeros), std.sd, P."""

    def __init__(self, sigma, P):
        nn.Module.__init__(self)
        sd = torch.as_tensor(sigma, dtype=torch.float32).detach().cpu().reshape(-1).clone()
        P = torch.as_tensor(P, dtype=torch.float32).detach().cpu().clone()
        if P.shape != (D_OUT, sd.numel()) or not (torch.isfinite(sd).all() and (sd > 0).all()):
            raise ValueError(f"SharedFixedHead: P [{D_OUT}, {sd.numel()}] and finite sigma > 0 expected, got P {tuple(P.shape)}")
        self.std = Standardiser(torch.zeros_like(sd), sd)
        self.register_buffer("P", P)


def load_projection(path, sha256=None, shape=None):
    """A stored float32 projection (np.load, allow_pickle=False); sha256 (full or >= 16-hex prefix) of its float32 bytes checked."""
    P = np.load(path, allow_pickle=False)
    if P.dtype != np.float32 or (shape is not None and P.shape != tuple(shape)):
        raise ValueError(f"load_projection: float32 {shape} expected, got {P.dtype} {P.shape} ({path})")
    if sha256 is not None:
        h = hashlib.sha256(np.ascontiguousarray(P).tobytes()).hexdigest()
        if len(sha256) < 16 or not h.startswith(sha256):
            raise ValueError(f"load_projection: sha256 {h[:16]} does not match the manifest {sha256[:16]} ({path})")
    return P


def _stored_projection(entry, root, name, seed, shape, sha16=None):
    """A manifest projection entry checked against the contract (file name, seed, sha256 prefix), then loaded and sha-checked."""
    sha, f, s = str(entry.get("sha256") or ""), entry.get("file"), entry.get("seed")
    if os.path.basename(str(f)) != name or s != seed or (sha16 is not None and not sha.startswith(sha16)):
        raise ValueError(f"fixed_heads: manifest projection {f!r} (seed {s!r}, sha256 {sha[:16]!r}) is not the contract's {name} "
                         f"(seed {seed}" + (f", sha256 {sha16}...)" if sha16 else ")"))
    return load_projection(os.path.join(root, entry["file"]), sha, shape)


def fixed_heads(manifest, root):
    """{"env": SharedFixedHead(sigma, P)} plus {"ss", "sc"} when the manifest has the rich block; files relative to `root`; every
    stored projection must be the contract's (file name, seed and, for P, the sha256 prefix P_SHA16)."""
    st, pj = manifest["standardiser"], manifest["projection"]
    if any(float(m) != 0.0 for m in st["mu"]):
        raise ValueError("fixed_heads: the standardiser mu must be stored as zeros (mu == 0)")
    heads = {"env": SharedFixedHead(st["sigma"], _stored_projection(pj, root, P_FILE, PROJ_SEED, P_SHAPE, P_SHA16))}
    rich = manifest.get("rich")
    for k in ("ss", "sc") if rich else ():
        P = _stored_projection(rich[f"P_{k}"], root, RICH_P_FILE[k], RICH_SEEDS[k], RICH_P_SHAPE[k])
        heads[k] = SharedFixedHead(rich[f"sigma_{k}"], P)
    return heads


def build_shared(layout, train_names, seed, rich=False):
    """SharedEncoder(layout, train_names) built from torch seed `seed` in a forked CPU RNG (+ RichHeads as enc.rich)."""
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(seed))
        enc = SharedEncoder(layout, train_names)
        if rich:
            enc.rich = RichHeads()
    return enc


def _enc_state(state):
    if isinstance(state, dict) and isinstance(state.get("enc"), dict) and "spatial.W" not in state:
        state = state["enc"]
    return dict(state)


def load_donor(enc, state, layout, open_new=True, strict=True):
    """Load a donor SharedEncoder state into `enc` (the rich.* heads dropped and listed), set the target layout, and open the
    layout's donor-unseen names at W = 0 (open_new) or keep them closed (zero contribution). Returns the tensor map."""
    state = _enc_state(state)
    own = enc.state_dict()
    dropped = sorted(k for k in state if k.startswith(RICH_PREFIX))
    donor = {k: v for k, v in state.items() if not k.startswith(RICH_PREFIX)}
    new, missing = sorted(set(own) - set(donor)), sorted(set(donor) - set(own))
    mismatched = sorted(k for k in set(own) & set(donor) if tuple(own[k].shape) != tuple(donor[k].shape) or own[k].dtype != donor[k].dtype)
    if strict and (new or missing or mismatched):
        bad = ", ".join(f"{n}={v}" for n, v in (("new", new), ("missing", missing), ("mismatched", mismatched)) if v)
        terms = "; ".join(f"{n}: {d}" for n, d in TENSOR_MAP_TERMS.items())
        raise ValueError(f"load_donor: strict load refused: {bad} ({terms})")
    load = {k: donor[k] for k in own if k in donor and k not in mismatched}
    if strict:
        W, seen = load["spatial.W"], load["spatial.seen"].bool()
        bad = [VOCAB[i] for i in torch.nonzero(~seen).flatten().tolist() if bool((W[i] != 0).any())]
        if bad:
            raise ValueError(f"load_donor: donor W rows of unseen names are not zero: {bad}")
    enc.load_state_dict(load, strict=strict)
    names = names_of(layout)
    enc.set_layout(names)
    sp = enc.spatial
    unseen = [n for n in names if not bool(sp.seen[VOCAB_INDEX[n]])]
    if open_new and unseen:
        r = torch.tensor([VOCAB_INDEX[n] for n in unseen], device=sp.W.device)
        with torch.no_grad():
            sp.W[r] = 0.0
            sp.seen[r] = True
    npar = {k: p.numel() for k, p in enc.named_parameters()}
    total, n_open = sum(npar.values()), (len(unseen) * sp.W.shape[1] if open_new else 0)
    n_loaded = sum(npar.get(k, 0) for k in load) - n_open
    tmap = {"loaded": sorted(load), "new": new, "missing": missing, "mismatched": mismatched, "dropped": dropped,
            "opened_rows": unseen if open_new else [], "closed_unseen": [] if open_new else unseen, "layout": list(names),
            "coverage": {"n_seen": len(names) - len(unseen), "n_total": len(names), "unseen": unseen},
            "seen_after": sp.seen_names(), "n_params": total, "n_params_loaded": n_loaded, "n_params_opened": n_open,
            "loaded_param_fraction": n_loaded / total, "opened_param_fraction": n_open / total,
            "n_dropped_params": int(sum(state[k].numel() for k in dropped)), "strict": bool(strict), "terms": dict(TENSOR_MAP_TERMS)}
    enc.tensor_map = tmap
    return tmap


def _check_geometry(row, layout, manifest):
    spec = row.get("spec") or {}
    for k, v in GEOMETRY.items():
        if k in spec:
            got = list(spec[k]) if isinstance(spec[k], (list, tuple)) else spec[k]
            if got != v:
                raise ValueError(f"build_target_encoder: spec {k} = {spec[k]!r}; the contract geometry is {v!r}")
    if manifest.get("contract", CONTRACT) != CONTRACT:
        raise ValueError(f"build_target_encoder: manifest contract {manifest.get('contract')!r} is not {CONTRACT}")
    cst = manifest.get("constants") or {}
    if cst.get("fs", FS) != FS or cst.get("l_in", L_IN) != L_IN:
        raise ValueError(f"build_target_encoder: manifest constants {cst} do not match fs {FS}, l_in {L_IN}")
    mont = (manifest.get("montages") or {}).get(row["dataset"])
    if mont is not None and names_of(mont) != names_of(layout):
        raise ValueError(f"build_target_encoder: layout differs from the manifest montage of {row['dataset']}")


def build_target_encoder(row, layout, manifest, donor_state):
    """The 64 Hz contract encoder on the target layout: from scratch (target seed) or strictly loaded from the donor member."""
    spec = row.get("spec") or {}
    init = spec.get("init") or ("random" if donor_state is None else "donor")
    if init not in ("random", "donor") or (init == "donor") != (donor_state is not None):
        raise ValueError(f"build_target_encoder: init {init!r} with donor_state {'given' if donor_state is not None else 'None'}")
    _check_geometry(row, layout, manifest)
    names = names_of(layout)
    seed = spec.get("target_seed")
    seed = row["seed"] if seed is None else seed
    enc = build_shared(names, names, seed)
    if init == "donor":
        state = _enc_state(donor_state)
        if "spatial.seen" not in state:
            raise ValueError("build_target_encoder: the donor state is not a SharedEncoder state (no spatial.seen)")
        got = sorted(VOCAB[i] for i in torch.nonzero(torch.as_tensor(state["spatial.seen"]).bool()).flatten().tolist())
        exp = sorted(names_of(manifest["seen"][row["dataset"]]))
        if got != exp:
            raise ValueError(f"build_target_encoder: donor seen set {got} differs from the manifest donor union for {row['dataset']}")
        load_donor(enc, state, names, open_new=True, strict=True)
    else:
        enc.tensor_map = {"init": "random", "seed": int(seed), "layout": list(names), "trained_names": list(names),
                          "n_params": int(sum(p.numel() for p in enc.parameters()))}
    if enc.n_tokens != N_TOKENS or enc.proj[1].in_features != TRUNK_DIM or enc.proj[1].out_features != D_OUT:
        raise AssertionError("build_target_encoder: geometry")
    return enc


def describe(enc):
    out = _describe_tokens(enc)
    if isinstance(enc, SharedEncoder):
        seen = set(enc.seen_names())
        out.update({"contract": CONTRACT, "architecture": ARCH, "channel_map": CHANNEL_MAP, "fs": FS, "input_samples": [0, L_IN],
                    "trunk_dim": TRUNK_DIM, "d": D_OUT, "layout": list(enc.layout), "n_seen": len(seen),
                    "layout_seen": sum(n in seen for n in enc.layout), "layout_total": len(enc.layout),
                    "rich_heads": isinstance(getattr(enc, "rich", None), RichHeads)})
        if getattr(enc, "tensor_map", None) is not None:
            out["tensor_map"] = enc.tensor_map
    return out
