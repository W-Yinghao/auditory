#!/bin/bash
#SBATCH --job-name=ha_covariates
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:08:00
#SBATCH --output=private/phase3-ha-covariates-%j.log
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
python3 scripts/phase3_ha_covariates.py
