"""One-device numerical probe, invoked only in a GPU Slurm allocation."""
import os
import torch
from auditory5.models.small_cnn import SmallEEGCNN_v1
from auditory5.models.simclr import ProjectionHead, nt_xent_loss
from auditory5.provenance import ROOT, require_slurm, write_json


def main():
    require_slurm()
    assert torch.cuda.is_available(), 'CUDA allocation is required'
    torch.manual_seed(11)
    device=torch.device('cuda:0')
    model=SmallEEGCNN_v1(20,2).to(device)
    projector=ProjectionHead().to(device)
    x=torch.randn(8,20,100,device=device)
    z,logits=model(x,return_logits=True)
    loss=nt_xent_loss(projector(z),projector(model(x+0.02*torch.randn_like(x))))
    loss.backward()
    assert torch.isfinite(loss) and all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
    info={'job_id':os.environ['SLURM_JOB_ID'],'status':'PASS','device':torch.cuda.get_device_name(0),
          'torch':torch.__version__,'cuda_build':torch.version.cuda,
          'cnn_parameters':sum(p.numel() for p in model.parameters()),'latent_shape':list(z.shape),
          'nt_xent_loss_synthetic':float(loss.detach()),'max_memory_allocated_bytes':torch.cuda.max_memory_allocated()}
    write_json(ROOT/'private/auditory5_v1/inputs/gpu_probe_001.json',info)
    print({k:v for k,v in info.items() if k!='device'})


if __name__=='__main__':main()
