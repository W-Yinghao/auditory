#!/bin/bash
#SBATCH --job-name=c3_s35cbstatecpu
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=private/auditory_alignment_v3/aln35/cb-state-cpu-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONPATH=$PWD PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -m pytest -q -p no:cacheprovider tests/auditory_alignment_v3/aln35/test_cb_audio_state.py
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.aln35.cb_audio_state register
