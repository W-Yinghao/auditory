"""CPU check of real GPU probe stream/ledger and explicit target query binding."""
import json
import os
from pathlib import Path
import numpy as np
from auditory_alignment_v3.aln35 import ap_wrong as W, ap_wrong_analysis_v2 as A, ap_wrong_queries as Q
from auditory_alignment_v3.aln35.ap_wrong_sampler import PairSampler, assert_permutation, mask_sha
from auditory_alignment_v3.prior33 import views as V

assert os.environ.get("SLURM_JOB_ID")
plan, registration, ledger = A.verify()
checks = []
for dataset in ("dtu", "fau", "private_bdf"):
    engineering = json.loads((W.OUT / "engineering" / f"{dataset}.json").read_text())
    base = W.OUT / "probes" / f'{dataset}_{engineering["job"]}'
    donor = json.loads((base / f'{engineering["donor_pair"]}.json').read_text())
    target = json.loads((base / f'{engineering["target"]}.json').read_text())
    unit = next(unit for unit in plan["units"] if unit["unit_id"] == engineering["donor_pair"])
    manifest = V.open_for_row(unit["source_row"])
    sampler = PairSampler(manifest, dataset, 3401, "cpu", revised=True, metadata_only=True)
    for _ in range(engineering["donor_steps_per_arm"]):
        sampler.next_draw()
    assert sampler.stream_hash() == donor["stream_sha256"]
    n = 0
    for chunk in donor["correspondence_ledger"]["files"]:
        path = Path(donor["correspondence_ledger"]["directory"]) / chunk["name"]
        assert W.sha(path) == chunk["sha256"]
        with np.load(path, allow_pickle=False) as data:
            for keys, actual, permutation, mask in zip(data["nominal_keys"], data["actual_audio_keys"],
                                                      data["audio_row_permutation"], data["nominal_positive_exclusion_mask_sha256"]):
                assert_permutation(keys, permutation, sampler.unknown)
                assert np.array_equal(actual, keys[permutation])
                assert mask_sha(keys, sampler.unknown) == mask
                n += 1
    assert n == engineering["donor_steps_per_arm"]
    cell = ledger["cells"][f'{dataset}|{target["subject_fold"]}|{target["content_fold"]}']
    people = Q.check_record(target, cell, dataset)
    checks.append({"dataset": dataset, "probe_job": engineering["job"], "stream_sha256": sampler.stream_hash(),
                   "strict_ledger_batches": n, "target_query_identities": len(people),
                   "candidate_order_sha256": cell["candidate_order_sha256"], "status": "PASS"})
W.write(A.BASE / "real_gpu_probe_validation.json", {"status": "PASS", "job": os.environ["SLURM_JOB_ID"],
        "analysis_v2_sha256": W.sha(A.SEAL), "checks": checks})
print(json.dumps({"status": "PASS", "job": os.environ["SLURM_JOB_ID"], "lineages": len(checks)}), flush=True)
