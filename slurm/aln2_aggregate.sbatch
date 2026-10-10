#!/bin/bash
#SBATCH --job-name=c3_aln2agg
# ALN2 aggregation (neutral tables over completed units): python -m auditory_alignment_v2.aggregate
#SBATCH --qos=runfill
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v2/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD PYTHONHASHSEED=0 OMP_NUM_THREADS=4 _MNE_FAKE_HOME_DIR=$(mktemp -d) MPLCONFIGDIR=$(mktemp -d)
echo "start $(date -Is) node=${SLURMD_NODENAME:-?}"
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_alignment_v2.aggregate
echo "end $(date -Is) rc=$?"
