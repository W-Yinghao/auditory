"""Physical keep-mask interval arithmetic and a pure-ID support allocation reference."""

import math
import random

from .contrasts import ReferenceError, _finite, _string


def _interval(value, name):
    if not isinstance(value, list) or len(value) != 2 or any(type(x) is not int for x in value):
        raise ReferenceError(f"{name} must be [start_sample, stop_sample] with integer endpoints")
    if value[1] <= value[0]:
        raise ReferenceError(f"{name} must be a nonempty half-open interval [start,stop)")
    return value


def audit_mask_coverage(spec):
    """Count retained/zeroed positions when keeping a window; do not inspect EEG.

    A disjoint keep window forces every input position to zero. If positions are
    retained, their actual values are unknown and an all-zero array remains possible.
    """
    if not isinstance(spec, dict) or set(spec) != {"sample_rate_hz", "mask_samples", "contexts"}:
        raise ReferenceError("mask spec requires sample_rate_hz, mask_samples, contexts")
    rate = _finite(spec["sample_rate_hz"], "sample_rate_hz")
    if rate <= 0:
        raise ReferenceError("sample_rate_hz must be positive")
    mask = _interval(spec["mask_samples"], "mask_samples")
    if not isinstance(spec["contexts"], list) or not spec["contexts"]:
        raise ReferenceError("contexts must be a nonempty list")
    rows, names = [], set()
    for context in spec["contexts"]:
        if not isinstance(context, dict) or not {"id", "input_samples"} <= context.keys() or context.keys() - {"id", "input_samples", "expected_overlap_samples"}:
            raise ReferenceError("context requires id,input_samples and optional expected_overlap_samples")
        name = _string(context["id"], "context.id")
        if name in names:
            raise ReferenceError("duplicate context id")
        names.add(name)
        bounds = _interval(context["input_samples"], "context.input_samples")
        start, stop = max(mask[0], bounds[0]), min(mask[1], bounds[1])
        overlap = max(0, stop - start)
        expected = context.get("expected_overlap_samples")
        if expected is not None and (type(expected) is not int or expected < 0):
            raise ReferenceError("expected_overlap_samples must be a nonnegative integer")
        input_count = bounds[1] - bounds[0]
        rows.append({"id": name, "input_samples": bounds, "input_samples_count": input_count,
                     "mask_samples": mask,
                     "overlap_samples": overlap, "overlap_seconds": overlap / rate,
                     "overlap_interval": [start, stop] if overlap else None,
                     "retained_samples": overlap, "retained_seconds": overlap / rate,
                     "zeroed_samples": input_count - overlap,
                     "has_requested_data": overlap > 0,
                     "all_zero_input_after_keep_mask": True if overlap == 0 else None,
                     "requested_mask_fraction_present": overlap / (mask[1] - mask[0]),
                     "expected_overlap_samples": expected,
                     "matches_expected": overlap == expected if expected is not None else None})
    return {"reference_only": True, "interval_convention": "half-open integer samples [start,stop), relative to the same query anchor",
            "mask_operation": "keep samples inside the requested window; set all other input positions to zero",
            "input_values_inspected": False,
            "all_zero_field_semantics": "true means zero is forced at every input position; null means some positions are retained and their actual values were not inspected",
            "sample_rate_hz": rate, "contexts": rows,
            "all_declared_counts_match": all(r["matches_expected"] is not False for r in rows),
            "limitation": "Counts depend on supplied physical input intervals and keep-mask semantics. Retained/zeroed positions do not establish whether actual EEG values changed. This does not verify loading, resampling, normalization, masks in memory, encoder receptive fields, or EEG effects."}


def allocate_support_ids(spec):
    """Draw a nested 10%-count subset inside the same first-30% ID region.

    IDs and chronological order only: not a check of EEG context halos or filtering.
    The query is fixed after the first floor(0.30*N) ordered IDs in both arms.
    """
    if not isinstance(spec, dict) or set(spec) != {"segments", "seed"}:
        raise ReferenceError("support spec requires segments and seed")
    if type(spec["seed"]) is not int or spec["seed"] < 0:
        raise ReferenceError("support seed must be a nonnegative integer")
    segments = spec["segments"]
    if not isinstance(segments, list) or not segments:
        raise ReferenceError("segments must be a nonempty list")
    ids, orders = set(), set()
    for segment in segments:
        if not isinstance(segment, dict) or set(segment) != {"id", "order"}:
            raise ReferenceError("each segment requires id and chronological integer order")
        _string(segment["id"], "segment.id")
        if type(segment["order"]) is not int or segment["order"] < 0:
            raise ReferenceError("segment.order must be a nonnegative integer")
        if segment["id"] in ids or segment["order"] in orders:
            raise ReferenceError("segment IDs and chronological orders must each be unique")
        ids.add(segment["id"]); orders.add(segment["order"])
    ordered = [s["id"] for s in sorted(segments, key=lambda x: x["order"])]
    n = len(ordered)
    # Integer arithmetic fixes rounding and does not fabricate a support ID for tiny n.
    small_n, region_n = n // 10, 3 * n // 10
    if small_n < 1 or region_n <= small_n or region_n >= n:
        raise ReferenceError("insufficient segment IDs for distinct 10%/30% support counts and a query")
    region = ordered[:region_n]
    chosen = set(random.Random(spec["seed"]).sample(region, small_n))
    small = [identity for identity in region if identity in chosen]
    query = ordered[region_n:]
    return {"reference_only": True, "seed": spec["seed"], "n_total": n,
            "rounding": "floor(0.10*N), floor(0.30*N); the query is the remaining tail",
            "support_region_ids": region, "support_10_ids": small, "support_30_ids": region[:],
            "query_ids": query, "n_support_10": len(small), "n_support_30": len(region),
            "n_query": len(query), "support_10_nested_in_30": set(small) <= set(region),
            "query_same_for_both_counts": True, "support_query_id_intersection": [],
            "physical_context_leakage_checked": False,
            "limitation": "This isolates ID count within a shared chronological source region only. Duration balance, minimum separation, filtering and encoder context halos require the actual loader and segment manifest."}
