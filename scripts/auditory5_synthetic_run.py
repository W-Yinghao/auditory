import argparse,json,os,shutil
from auditory5.provenance import ROOT,require_slurm,write_json,digest
from auditory5.synthetic import run_synthetic_suite

def main():
    require_slurm();p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args()
    dest=ROOT/'private/auditory5_v1/validation'/a.run
    summary=run_synthetic_suite(dest,repetitions=100)
    out=ROOT/'results/auditory5_v1'/a.run;out.mkdir(parents=True,exist_ok=False)
    summary['job_id']=os.environ['SLURM_JOB_ID'];summary['implementation_sha256']=digest(ROOT/'auditory5/synthetic.py')
    write_json(out/'summary.json',summary)
    if summary['status']!='PASS':raise RuntimeError('Synthetic world failed; inspect restricted outputs')
if __name__=='__main__':main()
