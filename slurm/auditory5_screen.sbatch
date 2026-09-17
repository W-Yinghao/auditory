#!/usr/bin/env bash
#SBATCH --job-name=auditory5_screen
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=private/auditory5_v1/logs/%x-%j.log
set -euo pipefail
umask 077
export AUDITORY5_ROOT="${AUDITORY5_ROOT:-/home/infres/yinwang/EEG_auditory}"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
screen_run="$1"
contract_run="$2"
source_registry="$3"
[[ "$screen_run" =~ ^[A-Za-z0-9_]+$ && "$contract_run" =~ ^[A-Za-z0-9_]+$ ]]
screen_python="${AUDITORY5_PYTHON:-/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python}"
screen_snapshot="$AUDITORY5_ROOT/private/auditory5_v1/validation/$contract_run/source_snapshot"
export PYTHONPATH="$screen_snapshot"
cd "$screen_snapshot"
# Execute the tested snapshot, including plotting; queued work never imports
# a subsequently edited working-tree module. Registry is a per-run text copy.
"$screen_python" - "$contract_run" <<'PY'
import json, sys
from pathlib import Path
from auditory5.provenance import ROOT, digest, require_slurm
require_slurm()
gate = json.loads((ROOT / 'results/auditory5_v1' / sys.argv[1] / 'validation.json').read_text())
assert gate['status'] == 'PASS', 'SCREENING_CONTRACT_GATE_FAILED'
for module in ('auditory5/screening.py', 'auditory5/provenance.py', 'auditory5/plot_screens.py'):
    assert digest(Path(module)) == gate['code_hashes'][module], 'SCREENING_SNAPSHOT_HASH_MISMATCH'
PY
"$screen_python" -m auditory5.screening --run "$screen_run" --sources "$source_registry"
"$screen_python" -m auditory5.plot_screens --screen-run "$screen_run"
