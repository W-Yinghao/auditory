#!/bin/bash
#SBATCH --partition=A100
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:02:00
#SBATCH --output=private/auditory_next_v2/logs/gpu-probe-%j.log
set -euo pipefail
umask 077
# Historical one-off probe; its completed P100 receipt is immutable.
# The active entrypoint must not allocate P100 for future submissions.
if [[ "${SLURM_JOB_PARTITION:-}" == "P100" ]]; then
    echo "P100 is disabled by project GPU policy." >&2
    exit 2
fi
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
cd /home/infres/yinwang/EEG_auditory
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python - <<'PY'
import hashlib,json,os,time
from pathlib import Path
import numpy as np
import torch
assert os.environ.get('SLURM_JOB_ID')
run=Path('private/auditory_next_v2/gpu_compatibility_p100_002')
run.mkdir(mode=0o700,exist_ok=False)
code=Path('scripts/auditory_next_gpu_compatibility.sbatch').read_bytes()
(run/'submitted_script.sbatch').write_bytes(code)
start=dict(run=run.name,job_id=os.environ['SLURM_JOB_ID'],source_hashes={'submitted_script.sbatch':hashlib.sha256(code).hexdigest()},new_readout_fits=0)
(run/'start.json').write_text(json.dumps(start))
begin=time.time()
try:
    assert torch.cuda.is_available()
    # Match the existing readout runtime; no extra deterministic-only mode.
    a=np.arange(6,dtype=float).reshape(2,3)/7
    b=np.arange(12,dtype=float).reshape(3,4)/11
    x=torch.tensor(a,dtype=torch.float64,device='cuda',requires_grad=True)
    w=torch.tensor(b,dtype=torch.float64,device='cuda',requires_grad=True)
    y=x@w
    y.sum().backward()
    errors=[float(np.max(abs(y.detach().cpu().numpy()-a@b))),
        float(np.max(abs(w.grad.cpu().numpy()-a.T@np.ones((2,4))))),
        float(np.max(abs(x.grad.cpu().numpy()-np.ones((2,4))@b.T)))]
    assert max(errors)<1e-10
    result=dict(status='PASS',job_id=start['job_id'],gpu=torch.cuda.get_device_name(),
        compute_capability=torch.cuda.get_device_capability(),torch_version=torch.__version__,
        cuda_version=torch.version.cuda,float64_forward_gradient_errors=errors,
        new_readout_fits=0,new_encoder_fits=0,elapsed_seconds=time.time()-begin,
        scope='device compatibility and arithmetic only; no optimizer step or EEG')
    (run/'completion.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
except BaseException as error:
    (run/'failure.json').write_text(json.dumps(dict(status='FAILED',exception_class=type(error).__name__,detail=str(error))))
    raise
PY
