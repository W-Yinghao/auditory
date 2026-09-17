"""Snapshot first; run workers from that immutable source copy."""
import argparse
import os
import subprocess
import sys
from .runtime import ROOT,create


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['probe','stage0','test','capability','input_preflight','n2_design','n2_inputs','closure','evaluation','real','finalize'])
    p.add_argument('--run',required=True)
    p.add_argument('--config',default='configs/auditory_v21_stage0.json')
    a=p.parse_args();private,public,report=create(a.run,a.config,a.command)
    env=dict(os.environ,AUDITORY5_ROOT=str(ROOT),PYTHONPATH=str(private/'source'),PYTHONDONTWRITEBYTECODE='1')
    completed=subprocess.run([sys.executable,'-m','auditory_v21.worker',a.command,str(private),str(public),str(report)],
                              cwd=private/'source',env=env)
    raise SystemExit(completed.returncode)


if __name__=='__main__':main()
