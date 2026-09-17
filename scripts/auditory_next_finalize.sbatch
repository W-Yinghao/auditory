#!/bin/bash
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=private/auditory_next_v2/logs/final-%j.log
set -uo pipefail
umask 077
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2
export AUDITORY5_ROOT=/home/infres/yinwang/EEG_auditory
export AUDITORY_NEXT_ROOT="$AUDITORY5_ROOT"
export PYTHONDONTWRITEBYTECODE=1
cd "$AUDITORY_NEXT_ROOT"
if [[ -f "private/auditory_next_v2/logs/final-${SLURM_JOB_ID}.log" && ! -L "private/auditory_next_v2/logs/final-${SLURM_JOB_ID}.log" ]]; then
    chmod 600 "private/auditory_next_v2/logs/final-${SLURM_JOB_ID}.log"
fi
ANEXT_PYTHON=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
ANEXT_FINAL_STATUS=0
# Each stage has its own immutable snapshot/receipt. A failed predecessor does
# not suppress the final report of that failure. No stage fits a readout.
"$ANEXT_PYTHON" -m auditory_next.cli metrics --run metrics_001 || ANEXT_FINAL_STATUS=1
"$ANEXT_PYTHON" -m auditory_next.cli fit-accounting --run fit_accounting_001 || ANEXT_FINAL_STATUS=1
"$ANEXT_PYTHON" -m auditory_next.cli postflight --run postflight_001 --source-run S0_001 || ANEXT_FINAL_STATUS=1
"$ANEXT_PYTHON" -m auditory_next.cli resources --run resources_001 --plan private/auditory_next_v2/plan_004/plan.json || ANEXT_FINAL_STATUS=1
"$ANEXT_PYTHON" -m auditory_next.cli report --run final_001 || ANEXT_FINAL_STATUS=1
"$ANEXT_PYTHON" -m auditory_next.cli audit-public --run public_audit_001 --source-run final_001 || ANEXT_FINAL_STATUS=1
exit "$ANEXT_FINAL_STATUS"
