"""Read-only, source-metadata audit before freezing any APwrong training plan."""
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

from auditory_alignment_v3.prior33 import views as V, sampler as S, losses as L
from auditory_alignment_v3.aln35.ap_wrong_sampler import metadata_banks, draw_keys, feasibility

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "private/auditory_alignment_v3/aln35/apwrong_v1"

def sha(path):
    return hashlib.file_digest(open(path, "rb"), "sha256").hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(line) for line in (ROOT / "private/auditory_alignment_v3/plan_ext.jsonl").read_text().splitlines()]
    source = [r for r in rows if r["family_id"] == "ALN32_PUBLIC_AUDIO_PRIOR_DONOR"
              and r["seed"] == 3401 and r["spec"]["objective"] == "NCE" and r["spec"]["block"] == "core"
              and r["dataset"] in ("dtu", "fau", "private_bdf")]
    result = {"utc": datetime.now(timezone.utc).isoformat(), "job": os.environ.get("SLURM_JOB_ID"), "lineages": []}
    assert len(source) == 3
    for row in source:
        target = row["dataset"]
        man = V.open_for_row(row)
        record_path = ROOT / "private/auditory_alignment_v3/units" / (row["experiment_id"] + ".json")
        rec = json.loads(record_path.read_text())
        assert rec["status"] == "complete"
        mem = rec["members"]["AP"]
        smp = S.DonorSampler(man, target, "core", 3401, "cpu", banks=metadata_banks(man, target))
        unknown = L.unknown_clock_families(man)
        first_invalid = None
        counts = Counter()
        # A single impossible actual batch is sufficient to disprove reuse of
        # this historical stream under the strict pure-audio intervention.
        for step in range(int(row["spec"]["budget"]["steps0"])):
            draw = smp._advance()
            keys = draw_keys(smp, draw)
            ok, detail = feasibility(keys, unknown)
            counts[smp._strata[draw.k].name] += 1
            if not ok:
                first_invalid = {"step_zero_based": step, "stratum": smp._strata[draw.k].name,
                                 "detail": detail, "keys": keys.tolist(), "rows": draw.rows.tolist(),
                                 "stream_sha256": smp.stream_hash()}
                break
        checkpoints = {}
        for kind in ("best", "h30_best", "gainsel_best"):
            p = ROOT / "private/auditory_alignment_v3/ckpt" / f'{row["experiment_id"]}_mAP_{kind}.pt'
            checkpoints[kind] = {"path": str(p), "exists": p.exists(), "sha256": sha(p) if p.exists() else None}
        item = {"target": target, "source_row": row, "source_record_sha256": sha(record_path),
                "source_code_hash": rec.get("code_hash"), "source_record": str(record_path),
                "manifest_sha256": man.sha256, "donor_set": man["donor_sets"][target]["core"],
                "original_horizon": rec["horizon_ep_eq"], "original_schedule": rec.get("schedule"),
                "original_side_branch": rec.get("side_branch"), "original_trigger_log": rec.get("trigger_log"),
                "original_AP_best": mem.get("best"), "original_AP_h30": mem.get("h30"),
                "original_AP_curve": mem.get("curve"), "original_AP_steps": mem.get("steps"),
                "original_stream": rec.get("stream"), "checkpoints": checkpoints,
                "checked_original_steps": sum(counts.values()), "checked_strata": dict(counts),
                "first_invalid": first_invalid,
                "strict_stream_reuse_possible": first_invalid is None,
                "no_outer_wrong_results_exist_or_read": True}
        result["lineages"].append(item)
        (OUT / "source_audit.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"target": target, "H": rec["horizon_ep_eq"], "checked_steps": sum(counts.values()),
                          "first_invalid_step": None if first_invalid is None else first_invalid["step_zero_based"]}), flush=True)

if __name__ == "__main__":
    main()
