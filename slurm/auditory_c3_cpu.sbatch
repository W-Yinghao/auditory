#!/bin/bash
#SBATCH --job-name=c3_cpu
# C3 v1 (AUDITORY_C3_SERVER_PACKAGE_v1_20261003) generic CPU entry: python -m auditory_c3.<module> <args>
#SBATCH --qos=runfill
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_c3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
# per-job local MNE home: concurrent jobs locking ~/.mne/mne-python.json on NFS fail with "Stale file handle"
export _MNE_FAKE_HOME_DIR=$(mktemp -d) MNE_USE_NUMBA=false
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0} args=$*"
MOD="$1"; shift
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m "auditory_c3.$MOD" "$@"
