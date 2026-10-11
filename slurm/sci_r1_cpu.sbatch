#!/bin/bash
#SBATCH --job-name=sci_r1
# docs/13 science round 1 (docs/auditory_alignment_v3/SCI_R1_PREREG.md): CPU-only analysis of completed ALN2/ALN3 checkpoints.
# Usage: sbatch [--job-name=...] slurm/sci_r1_cpu.sbatch <python -m module and args...>
#   tests : sbatch -J sci_r1_test slurm/sci_r1_cpu.sbatch pytest -q tests/auditory_alignment_v3/test_sci_r1_core.py
#   probe : sbatch -J sci_r1_probe slurm/sci_r1_cpu.sbatch -m auditory_alignment_v3.sci_r1.probe --dataset federici --eids ...
#   job   : sbatch -J sci_r1_<job> slurm/sci_r1_cpu.sbatch -m auditory_alignment_v3.sci_r1.continuous --job <job>
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=2-00:00:00
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/sci_r1/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK OPENBLAS_NUM_THREADS=$SLURM_CPUS_PER_TASK MKL_CBWR=AUTO
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} job=${SLURM_JOB_ID:-?} args: $*"
if [ "$1" = pytest ]; then shift; $PY -B -m pytest -p no:cacheprovider "$@"; else $PY -B "$@"; fi
rc=$?; echo "end $(date -Is) rc=$rc"; exit $rc  # capture before $(date) runs (audit 2026-10-11)
