#!/bin/bash
cd /home/infres/yinwang/EEG_auditory
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 _MNE_FAKE_HOME_DIR=$(mktemp -d)
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_alignment_v2.run_fm --lr-select "cbramod|pretrained_peft|federici|NCE" --epochs 1 --out private/auditory_alignment_v2/smoke_fm 2>&1 | grep -v Warn | tail -2
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_alignment_v2.run_fm --lr-select "reve|pretrained_frozen|private_bdf|CS_SINGLE" --epochs 1 --out private/auditory_alignment_v2/smoke_fm 2>&1 | grep -v Warn | tail -2
for i in 4803 7848 7683 7728; do /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_alignment_v2.run_fm --job-index $i --out private/auditory_alignment_v2/smoke_fm 2>&1 | grep -v Warn | tail -2; done
