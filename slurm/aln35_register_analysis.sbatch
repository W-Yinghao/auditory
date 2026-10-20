#!/bin/bash
#SBATCH --job-name=c3_s35analyses
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=12G
#SBATCH --time=00:30:00
#SBATCH --output=private/auditory_alignment_v3/aln35/analysis-enroll-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln35/register_analysis_refresh.py "$@"
