"""Strict, metadata-only AP audio derangements; prior33 sources stay unchanged.

An audio row is moved only with all rows in its canonical anchor class.  Known
family clocks collapse presentation aliases; an unknown clock retains the
presentation in the anchor key.  Every assignment crosses a complete stimulus
family, a conservative exclusion stronger than the inherited overlap mask.
Equal-size class matching preserves the audio multiset and nominal 2B x B masks.
"""
from __future__ import annotations

import copy
import hashlib
from collections import Counter, defaultdict
from types import SimpleNamespace

import numpy as np
import torch

from ..prior33 import contract as C, losses as L, sampler as SM, views as V

RULE = "aln35_apwrong_canonical_family_derangement_v1"
REVISION = "same_stratum_redraw_until_strict_anchor_matching_v1"
WRONG_RNG_TAG = 0x41505752


class NoLegalPermutation(ValueError):
    pass


def canonical_groups(keys, unknown_clock=()):
    """Return stable canonical groups, each with its exact row multiplicity."""
    k = np.asarray(keys, dtype=np.int64).reshape(-1)
    fam, pres, sample = C.unpack_key(k)
    unknown = set(map(int, unknown_clock))
    groups = {}
    for i, (f, p, s) in enumerate(zip(fam, pres, sample)):
        key = (int(f), int(p) if int(f) in unknown else -1, int(s))
        groups.setdefault(key, []).append(i)
    return [(key, np.asarray(rows, dtype=np.int64)) for key, rows in groups.items()]


def feasibility(keys, unknown_clock=()):
    groups = canonical_groups(keys, unknown_clock)
    buckets = defaultdict(list)
    for g, (key, rows) in enumerate(groups):
        buckets[len(rows)].append(g)
    for multiplicity, ids in buckets.items():
        counts = Counter(groups[g][0][0] for g in ids)
        if max(counts.values()) * 2 > len(ids):
            return False, {"multiplicity": multiplicity, "groups": len(ids),
                           "family_group_counts": dict(counts)}
    return True, {"groups": len(groups), "multiplicities": dict(Counter(len(r) for _, r in groups))}


def strict_permutation(keys, unknown_clock, rng):
    """An exact group permutation, never an approximate assignment.

    Within each multiplicity bucket, randomise family order and within-family
    group order, then rotate by the largest family count.  A legal perfect
    matching exists iff no family exceeds half the groups (Hall condition for
    this complete multipartite graph).  Both sides keep the original nominal
    keys: the returned array indexes ONLY the audio values.
    """
    keys = np.asarray(keys, dtype=np.int64).reshape(-1)
    groups = canonical_groups(keys, unknown_clock)
    ok, detail = feasibility(keys, unknown_clock)
    if not ok:
        raise NoLegalPermutation(str(detail))
    buckets = defaultdict(lambda: defaultdict(list))
    for g, (key, rows) in enumerate(groups):
        buckets[len(rows)][key[0]].append(g)
    perm = np.full(len(keys), -1, dtype=np.int64)
    for families in buckets.values():
        order = []
        for f in rng.permutation(sorted(families)):
            order.extend(rng.permutation(families[int(f)]).tolist())
        shift = max(map(len, families.values()))
        for i, g in enumerate(order):
            dest = order[(i + shift) % len(order)]
            perm[groups[g][1]] = groups[dest][1]
    assert_permutation(keys, perm, unknown_clock)
    return perm


def assert_permutation(keys, perm, unknown_clock=()):
    keys, perm = np.asarray(keys, dtype=np.int64), np.asarray(perm, dtype=np.int64)
    if not np.array_equal(np.sort(perm), np.arange(len(keys))):
        raise AssertionError("not a lossless within-batch audio permutation")
    fam, _, _ = C.unpack_key(keys)
    if np.any(fam == fam[perm]):
        raise AssertionError("same stimulus family remains paired")
    source_group = {}
    for i, (_, rows) in enumerate(canonical_groups(keys, unknown_clock)):
        for row in rows:
            source_group[int(row)] = i
    for _, rows in canonical_groups(keys, unknown_clock):
        if len({source_group[int(perm[r])] for r in rows}) != 1:
            raise AssertionError("a canonical positive group was split")


def draw_keys(sampler, draw):
    stratum = sampler._strata[draw.k]
    table = sampler.idx.seg[stratum.cohort]
    rows = np.repeat(draw.rows, C.N_ANCHORS)
    pres = table["presentation"][rows]
    start = table["s"][rows] + C.TICK_OFFS[sampler._ticks(draw)].reshape(-1)
    return C.pack_key(sampler.idx.fam[pres], pres, sampler.idx.fs0(pres, start))


def mask_sha(keys, unknown_clock):
    key = torch.as_tensor(np.asarray(keys, dtype=np.int64))
    pos, excl = L.nce_masks(torch.cat([key, key]), key, unknown_clock=unknown_clock)
    h = hashlib.sha256()
    h.update(pos.numpy().tobytes()); h.update(excl.numpy().tobytes())
    return h.hexdigest()


def metadata_banks(manifest, target):
    """Only manifest/table metadata, never EEG or audio cache arrays."""
    _, _, ds = SM.resolve_donor_set(manifest, target, "core")
    banks = {}
    for s in ds["strata"]:
        c = SM.coh_of(s)
        table, _ = V.cohort_table(manifest, c)
        participants = {str(p["participant"]): p for p in table["participants"]}
        pid = V.participant_ids(table, c)
        banks[c] = SimpleNamespace(manifest=manifest, device=torch.device("cpu"), roles=("fit",),
                                   rich=None, mode="slabs", layout=tuple(manifest["cohorts"][c]["layout"]),
                                   participants=participants, pid=pid,
                                   loaded=lambda pieces: np.ones(len(pieces), dtype=bool))
    return banks


class PairSampler(SM.DonorSampler):
    """Shared AP/APwrong stream. Redraw only where the frozen policy permits it."""
    def __init__(self, manifest, target, seed, device, *, revised, metadata_only=False):
        super().__init__(manifest, target, "core", seed, device,
                         banks=metadata_banks(manifest, target) if metadata_only else None)
        self.revised = bool(revised)
        self.unknown = L.unknown_clock_families(manifest)
        self.wrong_rng = np.random.default_rng(np.random.SeedSequence([seed, WRONG_RNG_TAG]))
        self.rejections = Counter()
        self.last_perm = None
        self.config.update(apwrong_rule=RULE, revised=self.revised,
                           revision_rule=REVISION if revised else None)

    def _advance(self):
        draw = self._draw(self.rng)
        stratum = self._strata[draw.k].name
        for attempt in range(4096):
            keys = draw_keys(self, draw)
            ok, detail = feasibility(keys, self.unknown)
            if ok:
                break
            if not self.revised:
                raise NoLegalPermutation(f"original step {self.step} {stratum}: {detail}")
            self.rejections[stratum] += 1
            draw = self._draw(self.rng, k=draw.k)
        else:
            raise NoLegalPermutation(f"4096 metadata redraws failed for {stratum}; lineage stops")
        self.last_perm = strict_permutation(keys, self.unknown, self.wrong_rng)
        self._hash(draw)
        self.step += 1
        if self.step % SM.HASH_EVERY == 0:
            self.hash_log.append([self.step, self._chain.hex()])
        return draw

    def state(self):
        result = super().state()
        result.update(wrong_rng=copy.deepcopy(self.wrong_rng.bit_generator.state),
                      rejections=dict(self.rejections))
        return result

    def load_state(self, state):
        super().load_state(state)
        self.wrong_rng.bit_generator.state = copy.deepcopy(state["wrong_rng"])
        self.rejections = Counter(state["rejections"])
