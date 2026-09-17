#!/bin/bash
#SBATCH --job-name=auditory_inventory
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=private/slurm-%j.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=/home/infres/yinwang/anaconda3/envs/EEG/bin/python
"$PY" server_restart_en_v1/scripts/first_pass_inventory.py --root AUDIT=/projects/EEG-foundation-model/auditory --out results/inventory_001 --private-out private/inventory_001
"$PY" scripts/discovery.py
"$PY" -m unittest discover -s server_restart_en_v1/tests -v > private/inventory_tests.log 2>&1
