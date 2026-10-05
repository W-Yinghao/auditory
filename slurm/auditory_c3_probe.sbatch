#!/bin/bash
#SBATCH --job-name=c3_probe
# C3 v1 (AUDITORY_C3_SERVER_PACKAGE_v1_20261003) P0/P1 environment probe: compute-node internet, eeg2025 packages,
# HF model cache, MATLAB module; then the package's own pytest + synthetic S1-S8 on a copy (synthetic data only).
#SBATCH --qos=runfill
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=private/auditory_c3/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
echo "start $(date -Is) node=${SLURMD_NODENAME:-?}"
echo "== internet"
for u in https://zenodo.org/api/records/17927767 https://data.mendeley.com/public-api/datasets/nzg5g2gzrd https://huggingface.co/api/models/openai/whisper-large-v3; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$u"); echo "$code $u"; done
echo "== packages"
$PY - <<'EOF'
import importlib, sys
print(sys.version)
for m in ["numpy","scipy","sklearn","pandas","h5py","mne","torch","torchaudio","transformers","soundfile","librosa","pytest","statsmodels","whisperx","dit","gcmi","frites","mtrf","jsonschema","yaml"]:
    try:
        mod = importlib.import_module(m); print(f"OK  {m} {getattr(mod,'__version__','?')}")
    except Exception as e:
        print(f"MISSING {m}: {type(e).__name__}")
EOF
echo "== HF cache"
ls -d ${HF_HOME:-$HOME/.cache/huggingface}/hub/models--* 2>/dev/null | grep -i -E "whisper|wav2vec|xls|hubert|gpt2|german" || echo "no matching cached models"
echo "== matlab"
(module avail matlab 2>&1 | grep -i matlab) || which matlab || echo "no matlab"
echo "== package pytest (copy)"
cd private/auditory_c3/p1_synthetic_001
$PY -m pytest -q -p no:cacheprovider tests; echo "pytest_exit=$?"
echo "== synthetic checks (copy)"
$PY reference/synthetic_checks.py > synthetic_stdout.json; echo "synthetic_exit=$?"
sha256sum reference/checks_c3.json
echo "end $(date -Is)"
