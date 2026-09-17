#!/bin/bash
#SBATCH --job-name=auditory_p3_ci_clinical
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:08:00
#SBATCH --output=private/slurm-%j.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
if [[ "${PHASE3_SCHEMA_ONLY:-0}" == "1" ]]; then
  /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python scripts/phase3_ci_clinical.py --schema-only
else
  /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python scripts/phase3_ci_clinical.py --private-run "${PHASE3_RUN:-phase3_ci_clinical_004}"
fi
