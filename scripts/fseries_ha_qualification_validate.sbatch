#!/bin/bash
#SBATCH --job-name=fseries-ha-val
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:02:00
#SBATCH --output=private/auditory_fseries/ha_qualification_validate-%j.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("results/auditory_fseries/ha_qualification_002")
s = json.loads((p / "qualification_summary.json").read_text())
assert s["clinical_group_counts"] == {"NH": 11, "HA": 84}
assert s["decision"] == {"F1": "SUPPORT_INSUFFICIENT", "F2": "SUPPORT_INSUFFICIENT", "F3": "SUPPORT_INSUFFICIENT", "F4": "SUPPORT_INSUFFICIENT"}
assert not any("evidence" in x.name for x in p.iterdir())
print("validation_ok")
PY
