#!/bin/bash
#SBATCH --job-name=fseries-ha-qual
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=private/auditory_fseries/ha_qualification_002-%j.log
set -euo pipefail
umask 077
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
export NUMEXPR_NUM_THREADS=2
cd /home/infres/yinwang/EEG_auditory
if [[ -f "private/auditory_fseries/ha_qualification_002-${SLURM_JOB_ID}.log" ]]; then
    chmod 600 "private/auditory_fseries/ha_qualification_002-${SLURM_JOB_ID}.log"
fi
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python scripts/fseries_ha_qualification.py
