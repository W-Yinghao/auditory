"""Read checkpoint receipts only; never load EEG or a fitted model."""
import json
from .provenance import ROOT, finish, require_slurm


def run(config,registry,site,dest,public,report):
    require_slurm()
    runs=[]
    for name in ('N1_core_001','N3_core_001','N2_core_001','C2R_core_001','E0R_core_001','synthetic_001'):
        folder=ROOT/'private/auditory_next_v2'/name
        counts={}
        for base in ('fits','heads','states'):
            path=folder/base
            if not path.exists():continue
            counts[base]={pattern:sum(1 for _ in path.rglob(pattern)) for pattern in
                ('start.json','initial_receipt.json','numerics_1000.json','numerics_2000.json',
                 '*_1000.json','*_2000.json','completion.json','*.pt','*.pkl')}
        done=folder/'completion.json';failure=folder/'failure.json'
        runs.append(dict(run=name,started=(folder/'start.json').exists(),
            completion_status=json.loads(done.read_text()).get('status') if done.exists() else None,
            failure=failure.exists(),prepared_case_files=sum(1 for _ in (folder/'cases').glob('*/case.json')),
            receipts=counts))
    return finish(dest,public,dict(status='SCHEDULER_PROGRESS_ONLY',runs=runs,new_fits=0))
