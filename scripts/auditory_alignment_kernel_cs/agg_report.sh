#!/bin/bash
cd /home/infres/yinwang/EEG_auditory
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD PYTHONHASHSEED=0 OMP_NUM_THREADS=4 _MNE_FAKE_HOME_DIR=$(mktemp -d) MPLCONFIGDIR=$(mktemp -d)
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
$PY -m auditory_alignment.aggregate && $PY -m auditory_alignment.report
