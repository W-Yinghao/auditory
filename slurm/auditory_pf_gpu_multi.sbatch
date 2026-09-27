#!/bin/bash
# Same command as auditory_pf_gpu.sbatch, but PF_NSUB worker processes share the one GPU
# (the EEGNet units are tiny; one process leaves the GPU mostly idle). Units are split by
# auditory_pf.runtime.task_units via PF_SUB / PF_NSUB; every unit is still skip-if-done.
#SBATCH --job-name=pf_gpu_multi
# (runfill was used only for the first PF batch; default QoS from now on, per user 2026-09-27)
#SBATCH --partition=A100,A40,L40S,H100,A30
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=23:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_pf/logs/%x-%A_%a.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
NSUB=${PF_NSUB:-4}
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0} workers=$NSUB"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
pids=()
for s in $(seq 0 $((NSUB - 1))); do
  ( PF_SUB=$s PF_NSUB=$NSUB /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_pf.cli "$@" 2>&1 | sed -u "s/^/[w$s] /" ) &
  pids+=($!)
done
rc=0
for p in "${pids[@]}"; do wait "$p" || rc=1; done
echo "end $(date -Is) rc=$rc"
exit $rc
