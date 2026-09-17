#!/usr/bin/env bash
#SBATCH --job-name=auditory5_aggregate
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=private/auditory5_v1/logs/%x-%j.log
set -euo pipefail
umask 077
export AUDITORY5_ROOT="${AUDITORY5_ROOT:-/home/infres/yinwang/EEG_auditory}"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
aggregate_run="$1"
contract_run="$2"
[[ "$aggregate_run" =~ ^[A-Za-z0-9_]+$ && "$contract_run" =~ ^[A-Za-z0-9_]+$ ]]
aggregate_python="${AUDITORY5_PYTHON:-/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python}"
aggregate_snapshot="$AUDITORY5_ROOT/private/auditory5_v1/validation/$contract_run/source_snapshot"
export PYTHONPATH="$aggregate_snapshot"
cd "$aggregate_snapshot"
"$aggregate_python" - "$contract_run" <<'PY'
import json, sys
from pathlib import Path
from auditory5.provenance import ROOT, digest, require_slurm
require_slurm()
gate = json.loads((ROOT / 'results/auditory5_v1' / sys.argv[1] / 'validation.json').read_text())
assert gate['status'] == 'PASS', 'AGGREGATE_CONTRACT_GATE_FAILED'
for module in ('auditory5/reporting.py', 'auditory5/provenance.py', 'auditory5/metrics.py', 'auditory5/statistics.py'):
    assert digest(Path(module)) == gate['code_hashes'][module], 'AGGREGATE_SNAPSHOT_HASH_MISMATCH'
PY
"$aggregate_python" -m auditory5.cli --config "$AUDITORY5_ROOT/configs/auditory5_v1.yaml" \
    aggregate --run "$aggregate_run" --split-run splits_001
