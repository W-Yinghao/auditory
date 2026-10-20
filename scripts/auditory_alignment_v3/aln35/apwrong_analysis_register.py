"""Slurm CPU-only APwrong analysis contract tests and prospective freeze."""
import json
import os
import subprocess
import sys
from auditory_alignment_v3.aln35 import ap_wrong as W, ap_wrong_analysis as A

assert os.environ.get("SLURM_JOB_ID")
subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                "tests/auditory_alignment_v3/aln35/test_ap_wrong_analysis.py"], check=True)
A.register()
A.run()
W.write(W.OUT / "analysis_cpu_receipt.json", {"status": "PASS", "job": os.environ["SLURM_JOB_ID"],
        "analysis_sha256": W.sha(A.SEAL), "training_plan_sha256": W.sha(W.PLAN),
        "training_fleet_status": W.fleet_status()})
print(json.dumps(W.fleet_status()), flush=True)
