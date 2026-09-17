#!/bin/bash
#SBATCH --job-name=ha_cov_schema
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:03:00
#SBATCH --output=private/phase3-ha-schema-%j.log
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
python3 scripts/phase3_ha_covariates_schema.py
