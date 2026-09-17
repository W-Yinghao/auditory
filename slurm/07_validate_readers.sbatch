#!/bin/bash
#SBATCH --job-name=auditory_reader_checks
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=3G
#SBATCH --time=00:05:00
#SBATCH --output=private/slurm-%j.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=scripts
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m unittest discover -s tests -v
cd server_restart_en_v1
sha256sum -c MANIFEST.sha256
