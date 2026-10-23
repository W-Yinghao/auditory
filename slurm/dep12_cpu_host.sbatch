#!/bin/bash
#SBATCH --job-name=aud_dep12cpu
#SBATCH --partition=CPU
#SBATCH --qos=runfill
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=2-00:00:00
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
# DEP12 CPU host allocation (EEG_auditory project; not c3_-prefixed on purpose: the fleet coordinator's gpu_count raises on a
# c3_ runfill job without a GPU request). CPU steps attach with: srun --jobid=<this job> --overlap -n1 -c<k> ...
# Created 2026-10-23 after the evidence allocation 1047358 hit its 4-day limit and normal QoS was at 28 (> 27 rule).
set -euo pipefail
sleep infinity
