#!/bin/bash
#SBATCH --job-name=auditory_clinical_audit
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=private/clinical-audit-%j.log
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
python3 scripts/audit_clinical.py
