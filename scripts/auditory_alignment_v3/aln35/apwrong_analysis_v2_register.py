"""Prospective analysis correction, source metadata audit, tests, then freeze."""
import json
import os
import subprocess
import sys
from auditory_alignment_v3.aln35 import ap_wrong as W, ap_wrong_analysis_v2 as A

assert os.environ.get("SLURM_JOB_ID")
subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "tests/auditory_alignment_v3/aln35/test_ap_wrong_analysis_v2.py"], check=True)
A.register()
A.run()
W.write(A.BASE / "cpu_receipt.json", {"status": "PASS", "job": os.environ["SLURM_JOB_ID"],
        "analysis_v2_sha256": W.sha(A.SEAL), "training_plan_sha256": W.sha(W.PLAN), "training_unchanged": True})
print(json.dumps({"status": "PASS", "analysis_v2_sha256": W.sha(A.SEAL)}), flush=True)
