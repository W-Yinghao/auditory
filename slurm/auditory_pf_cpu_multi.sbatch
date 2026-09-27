#!/bin/bash
# CPU version of auditory_pf_gpu_multi.sbatch: PF_NSUB single-threaded workers split the units (skip-if-done).
#SBATCH --job-name=pf_cpu_multi
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=23:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_pf/logs/%x-%A_%a.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
NSUB=${PF_NSUB:-16}
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0} workers=$NSUB"
pids=()
for s in $(seq 0 $((NSUB - 1))); do
  ( PF_SUB=$s PF_NSUB=$NSUB /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_pf.cli "$@" 2>&1 | sed -u "s/^/[w$s] /" ) &
  pids+=($!)
done
rc=0
for p in "${pids[@]}"; do wait "$p" || rc=1; done
echo "end $(date -Is) rc=$rc"
exit $rc
