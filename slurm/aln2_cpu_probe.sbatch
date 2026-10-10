#!/bin/bash
#SBATCH --job-name=c3_aln2probe
# ALN2 CPU probe: runs the python script given as arguments (diagnostics only)
#SBATCH --qos=runfill
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=4:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v2/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD PYTHONHASHSEED=0 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 HF_HUB_OFFLINE=1 _MNE_FAKE_HOME_DIR=$(mktemp -d) MNE_USE_NUMBA=false
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} args=$*"
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python "$@"
echo "end $(date -Is) rc=$?"
