"""Sequential immutable tasks inside a bounded Slurm allocation."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from auditory5.provenance import ROOT,require_slurm,digest,write_json

def main():
    require_slurm();p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--resource',choices=['cpu','gpu'],required=True)
    p.add_argument('--worker',type=int,required=True);p.add_argument('--workers',type=int,default=2);a=p.parse_args()
    path=Path(a.plan);plan=json.loads(path.read_text());expected=digest(path)
    tasks=[t for t in plan['tasks'] if t['resource']==a.resource][a.worker::a.workers]
    dest=path.parent/'worker_receipts';dest.mkdir(exist_ok=True)
    record={'job_id':os.environ['SLURM_JOB_ID'],'resource':a.resource,'worker':a.worker,'plan_hash':expected,'tasks':[]}
    for t in tasks:
        complete=path.parent/'outputs'/t['name']/'completion.json'
        if complete.exists():
            old=json.loads(complete.read_text())
            if old['status']!='PASS' or old['plan_hash']!=expected:raise ValueError('Cannot resume incompatible output')
            record['tasks'].append({'index':t['index'],'status':'EXISTING_VERIFIED_PASS'});continue
        print(json.dumps({'starting_index':t['index'],'task':t['name'],'resource':a.resource}),flush=True)
        command=[sys.executable,'-m','auditory5.cli','run-job','--plan',str(path),'--index',str(t['index'])]
        result=subprocess.run(command,cwd=ROOT)
        record['tasks'].append({'index':t['index'],'returncode':result.returncode,'status':'PASS' if result.returncode==0 else 'FAIL'})
        if result.returncode:
            write_json(dest/(a.resource+'_'+str(a.worker)+'_'+os.environ['SLURM_JOB_ID']+'.json'),record)
            raise RuntimeError('Worker stopped at failed task; later tasks remain NOT_RUN')
    record['status']='PASS';write_json(dest/(a.resource+'_'+str(a.worker)+'_'+os.environ['SLURM_JOB_ID']+'.json'),record)
if __name__=='__main__':main()
