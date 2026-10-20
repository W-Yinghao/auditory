#!/bin/bash
#SBATCH --job-name=c3_s35evsetup
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=00:20:00
#SBATCH --output=private/auditory_alignment_v3/aln35/evidence-setup-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -m pytest -q -p no:cacheprovider tests/auditory_alignment_v3/aln35/test_evidence_refresh.py
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln35/setup_evidence.py
