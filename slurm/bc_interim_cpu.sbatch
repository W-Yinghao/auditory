#!/bin/bash
#SBATCH --job-name=bc_interim
# ALN3 ADDENDUM_05 interim B/C aggregation (docs/auditory_alignment_v3/ADDENDUM_05_BC_INTERIM_AGGREGATION.md): CPU only.
# Usage: sbatch [--job-name=...] slurm/bc_interim_cpu.sbatch <python -m module and args...>
#   tests : sbatch -J bc_interim_test slurm/bc_interim_cpu.sbatch pytest -q tests/auditory_alignment_v3/test_bc_interim.py
#   run   : sbatch slurm/bc_interim_cpu.sbatch -m auditory_alignment_v3.bc_interim
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=2-00:00:00
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/bc_interim/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK OPENBLAS_NUM_THREADS=$SLURM_CPUS_PER_TASK MKL_CBWR=AUTO
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} job=${SLURM_JOB_ID:-?} args: $*"
if [ "$1" = pytest ]; then shift; $PY -B -m pytest -p no:cacheprovider "$@"; else $PY -B "$@"; fi
rc=$?; echo "end $(date -Is) rc=$rc"; exit $rc  # capture before $(date) runs (audit 2026-10-11)
