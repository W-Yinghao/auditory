#!/bin/bash
#SBATCH --job-name=aln3
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=24:00:00
# TEMPLATE ONLY. Do not submit before binding account/partition/runtime/runner.
set -euo pipefail
: "${ALN3_REPO:?Set the server research-workspace path}"
: "${ALN3_PACKAGE:?Set the extracted package path}"
: "${ALN3_RUNNER:?Set an existing, integrated Python runner path}"
: "${ALN3_EXPERIMENT_ID:?Set a bound plan experiment ID}"
[[ -f "$ALN3_RUNNER" ]] || { echo "Integrated runner does not exist" >&2; exit 2; }
cd "$ALN3_REPO"
# This CLI is the interface to implement, not a claim the existing repo already has it.
python "$ALN3_RUNNER" --plan "$ALN3_PACKAGE/plans/units.jsonl" --experiment-id "$ALN3_EXPERIMENT_ID"
