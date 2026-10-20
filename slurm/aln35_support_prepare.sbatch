#!/bin/bash
#SBATCH --job-name=c3_s35supprep
#SBATCH --qos=normal
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -m pytest -q -p no:cacheprovider tests/auditory_alignment_v3/aln35/test_support_contract.py
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.aln35.support_coverage --make-plan
