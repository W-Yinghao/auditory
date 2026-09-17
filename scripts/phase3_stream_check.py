"""Verify bounded-memory FIR implementation against four completed smoke layouts."""
import json,os
from pathlib import Path
import numpy as np
from phase1_prepare import readcsv
from phase3_ci_epochs import process,BASE
def main():
    assert os.getenv('SLURM_JOB_ID');os.umask(0o077);os.environ['AUDIT_STREAM_THRESHOLD_SAMPLES']='0'
    out=BASE/'results/phase3_ci_stream_check_001';out.mkdir(exist_ok=False)
    private=BASE/'private/phase3_ci_stream_check_001';private.mkdir(mode=0o700,exist_ok=False)
    old=BASE/'results/phase3_ci_smoke_001';ids={p.parent.name for p in old.glob('M*/summary.json')}
    rows=[r for r in readcsv(BASE/'results/phase3_ci_sources_001/source_manifest.csv') if r['container_id'] in ids]
    paths={r['container_id']:r['path'] for r in readcsv(BASE/'private/phase3_ci_sources_001/source_paths_and_tokens.csv')}
    cfg=json.loads((BASE/'configs/phase3_science_v1.json').read_text())['ci'];checks=[]
    for r in rows:
        s=process(r,paths[r['container_id']],cfg,out,private);mid=r['container_id']
        with np.load(old/mid/'epochs_roi.npz') as a,np.load(out/mid/'epochs_roi.npz') as b:
            assert np.array_equal(a['accepted'],b['accepted']) and np.array_equal(a['samples_0based'],b['samples_0based'])
            err=float(np.max(np.abs(a['roi_uv']-b['roi_uv'])))
            assert np.allclose(a['roi_uv'],b['roi_uv'],atol=2e-5,rtol=1e-6)
        checks.append(dict(container_id=mid,max_epoch_difference_uv=err,accepted_identical=True))
    result=dict(job_id=os.environ['SLURM_JOB_ID'],status='passed',checks=checks)
    (out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
