#!/bin/bash
#SBATCH --job-name=auditory_clinical_002
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=private/clinical-002-%j.log
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
python3 scripts/audit_clinical_002.py
