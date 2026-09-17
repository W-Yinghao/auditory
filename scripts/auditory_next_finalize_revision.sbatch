#!/bin/bash
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --output=private/auditory_next_v2/logs/revision-%j.log
set -uo pipefail
umask 077
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2
export AUDITORY5_ROOT=/home/infres/yinwang/EEG_auditory
export AUDITORY_NEXT_ROOT="$AUDITORY5_ROOT"
export PYTHONDONTWRITEBYTECODE=1
cd "$AUDITORY_NEXT_ROOT"
chmod 600 "private/auditory_next_v2/logs/revision-${SLURM_JOB_ID}.log"
ANEXT_REV_PYTHON=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
ANEXT_REV_STATUS=0
# Reuse completed metrics/fit ledgers. Only audit and aggregate revision runs.
"$ANEXT_REV_PYTHON" -m auditory_next.cli postflight --run postflight_002 --source-run S0_001 || ANEXT_REV_STATUS=1
"$ANEXT_REV_PYTHON" -m auditory_next.cli resources --run resources_002 --plan private/auditory_next_v2/plan_004/plan.json || ANEXT_REV_STATUS=1
"$ANEXT_REV_PYTHON" -m auditory_next.cli report --run final_002 || ANEXT_REV_STATUS=1
"$ANEXT_REV_PYTHON" -m auditory_next.cli audit-public --run public_audit_002 --source-run final_002 || ANEXT_REV_STATUS=1
exit "$ANEXT_REV_STATUS"
