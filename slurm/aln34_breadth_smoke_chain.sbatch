#!/bin/bash
# One queued allocation covers the added cohort contracts. Each lane writes its
# own matching receipt; a failure stops the chain and preserves previous receipts.
#SBATCH --job-name=c3_breadthsmoke
#SBATCH --qos=runfill
#SBATCH --partition=A30,A40,L40S
#SBATCH --exclude=node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --nice=85
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 OPENBLAS_NUM_THREADS=12
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
probe_root="private/auditory_alignment_v3/aln34/breadth_inner_v1/probes/$SLURM_JOB_ID"
"$PY" -B -u -m auditory_alignment_v3.aln34.breadth_inner --smoke
"$PY" -B -u -m auditory_alignment_v3.aln34.breadth_policy --probe-root "$probe_root"
"$PY" -B -u -m auditory_alignment_v3.aln34.breadth_fusion --probe-root "$probe_root"
"$PY" -B -u -m auditory_alignment_v3.aln34.breadth_episode --probe-root "$probe_root"
"$PY" -B -u -m auditory_alignment_v3.aln34.breadth_budget --smoke
