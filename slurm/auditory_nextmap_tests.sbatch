#!/bin/bash
#SBATCH --job-name=nm_tests
#SBATCH --qos=runfill
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_nextmap/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0} qos=${SLURM_JOB_QOS:-?}"
$PY -m py_compile auditory_nextmap/*.py
$PY -m pytest -q -p no:cacheprovider tests/auditory_nextmap
if [ "${NM_SYNTHETIC_RUN:-}" != "" ]; then
  $PY -m auditory_nextmap.cli synthetic --run "$NM_SYNTHETIC_RUN"
fi
