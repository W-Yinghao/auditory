"""Snapshot and re-exec; no analysis runs on a login node."""
import argparse
import os
import subprocess
import sys
from .runtime import ROOT,create

def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['inspect','freeze-support','test','test-scoring','repair-selection','make-plan','prepare-exposures','develop-n2r','join-r3-capability','capability','run-pca','run-bags','train-representation','select-probes','evaluate-representations','finalize'])
    p.add_argument('--config',default='configs/auditory_v3_plan.yaml')
    p.add_argument('--run',required=True)
    p.add_argument('--registry-run')
    p.add_argument('--split-run')
    p.add_argument('--gate-run')
    p.add_argument('--packet',choices=['P0','N2R','R3'])
    p.add_argument('--stage',choices=['selection','final'])
    p.add_argument('--task-index',type=int)
    p.add_argument('--objective',choices=['SUP','SIM','MATCH'])
    p.add_argument('--plan-run')
    p.add_argument('--development-run')
    p.add_argument('--selection-run')
    p.add_argument('--representation-run')
    p.add_argument('--recover-zero-update-run')
    p.add_argument('--capability-runs',nargs=3)
    p.add_argument('--p0-run')
    p.add_argument('--n2r-run')
    p.add_argument('--r3-run')
    p.add_argument('--scoring-test-run')
    p.add_argument('--stable-scoring',action='store_true')
    a=p.parse_args()
    if a.command=='train-representation':
        if a.task_index is None:a.task_index=int(os.environ['SLURM_ARRAY_TASK_ID'])
        a.run=a.run+f'_task{a.task_index:03d}'
    private,public,report=create(a)
    env=dict(os.environ,AUDITORY_ROOT=str(ROOT),AUDITORY5_ROOT=str(ROOT),PYTHONPATH=str(private/'source'),PYTHONDONTWRITEBYTECODE='1')
    result=subprocess.run([sys.executable,'-m','auditory_v3.worker',str(private),str(public),str(report)],cwd=private/'source',env=env)
    raise SystemExit(result.returncode)

if __name__=='__main__':main()
