#!/bin/bash
# Successor of the fleet coordinator 1051045 (c3_aln35keep3) under runfill: normal QoS was at 29 (> 27 rule), so the
# coordinator's own renewal (normal QoS, needs <= 27) would not fire before its 4-day limit (~2026-10-24 09:42).
# Not c3_-prefixed on purpose: gpu_count / project() count only c3_ runfill jobs as GPU work. Same program, same log.
#SBATCH --job-name=aud_fleetkeep4
#SBATCH --partition=CPU
#SBATCH --qos=runfill
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=4-00:00:00
#SBATCH --output=private/auditory_alignment_v3/aln35/fleet.log
#SBATCH --open-mode=append
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln35/maintain_fleet_v3.py
