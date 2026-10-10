#!/usr/bin/env bash
# Template only. Supply partition/account/GPU/time/environment via the server's scheduler wrapper.
# This file is NOT submitted by this package. The Python module below must first be implemented.
set -euo pipefail
: "${AUDITORY_WORKTREE:?Set an approved writable worktree, not the read-only source directory}"
: "${ALN2_PLAN:?Set the absolute path of the resolved experiment plan}"
: "${ALN2_RUN_MODULE:?Set the implemented server module accepting --manifest and --job-index}"
: "${SLURM_ARRAY_TASK_ID:?Use the server array task index}"
cd "${AUDITORY_WORKTREE}"
python -m "${ALN2_RUN_MODULE}" --manifest "${ALN2_PLAN}" --job-index "${SLURM_ARRAY_TASK_ID}"
