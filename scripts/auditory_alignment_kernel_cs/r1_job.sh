#!/bin/bash
# runs R1 task lines [$1, $2) concurrently under MPS on one GPU
cd /home/infres/yinwang/EEG_auditory
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD PYTHONHASHSEED=0 OMP_NUM_THREADS=2 _MNE_FAKE_HOME_DIR=$(mktemp -d)
export CUDA_MPS_PIPE_DIRECTORY=$(mktemp -d) CUDA_MPS_LOG_DIRECTORY=$(mktemp -d); nvidia-cuda-mps-control -d && echo "mps on"
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
while read -r line; do
  $PY -m auditory_alignment.r1_reliability $line 2>&1 | grep -v Warning &
done < <(sed -n "$(( $1 + 1 )),$2p" private/auditory_alignment_kernel_cs/r1_tasks.txt)
wait
echo quit | nvidia-cuda-mps-control
