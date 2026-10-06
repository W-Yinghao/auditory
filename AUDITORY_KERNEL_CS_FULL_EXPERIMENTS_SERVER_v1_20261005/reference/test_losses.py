"""Small deterministic numerical checks; not tests of real EEG performance."""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
import torch
from losses import cs_qmi, cs_qmi_from_log_grams, gaussian_log_gram, fmca_logdet_loss, multiscale_cs_loss, symmetric_infonce


def main() -> None:
    torch.set_num_threads(1)
    torch.manual_seed(42)
    u = torch.randn(24, 3, dtype=torch.float64)
    v = u[:, :2] + 0.5 * torch.randn(24, 2, dtype=torch.float64)
    results = []
    def add(name, **numbers):
        results.append({"name": name, "passed": True, **numbers})

    value, _ = cs_qmi(u, v, sigma_u=1.1, sigma_v=0.8)
    k, l = gaussian_log_gram(u, 1.1).exp(), gaussian_log_gram(v, 0.8).exp()
    direct = (k*l).mean().log() + (k.mean()*l.mean()).log() - 2*(k.mean(1)*l.mean(1)).mean().log()
    assert torch.allclose(value, direct, atol=1e-12)
    add("logspace_equals_information_potentials", value=float(value), error=float(abs(value-direct)))

    w = torch.arange(1, 25, dtype=torch.float64); w /= w.sum()
    weighted, _ = cs_qmi(u, v, sigma_u=1.1, sigma_v=0.8, weights=w)
    a = ((w[:, None]*w[None, :])*k*l).sum()
    b = (w@k@w)*(w@l@w); c = (w*(k@w)*(l@w)).sum()
    assert torch.allclose(weighted, a.log()+b.log()-2*c.log(), atol=1e-12)
    add("weighted_empirical_measure", value=float(weighted))

    perm = torch.randperm(len(u))
    vp, _ = cs_qmi(u[perm], v[perm], sigma_u=1.1, sigma_v=0.8)
    vs, _ = cs_qmi(v, u, sigma_u=0.8, sigma_v=1.1)
    assert torch.allclose(value, vp, atol=1e-12) and torch.allclose(value, vs, atol=1e-12)
    q, _ = torch.linalg.qr(torch.randn(3,3,dtype=torch.float64))
    vr, _ = cs_qmi(u@q, -v, sigma_u=1.1, sigma_v=0.8)
    assert torch.allclose(value, vr, atol=1e-12)
    add("pair_permutation_symmetry_and_orthogonal_invariance", value=float(vr))

    n = 32
    log_eye = torch.full((n,n), -torch.inf, dtype=torch.float64)
    log_eye.fill_diagonal_(0)
    eye_val, _ = cs_qmi_from_log_grams(log_eye, log_eye)
    zero_val, _ = cs_qmi_from_log_grams(torch.zeros_like(log_eye), torch.zeros_like(log_eye))
    assert abs(float(eye_val)-math.log(n))<1e-12 and abs(float(zero_val))<1e-12
    add("identity_and_collapse_limits", identity=float(eye_val), collapse=float(zero_val))

    ms, _ = multiscale_cs_loss(u,v,sigma_u=1.1,sigma_v=0.8)
    expected = -torch.stack([cs_qmi(u,v,sigma_u=1.1*s,sigma_v=.8*s)[0] for s in (.5,1,2)]).mean()
    assert torch.allclose(ms,expected,atol=1e-12)
    add("multiscale_is_mean_objective", loss=float(ms))

    # Direct numerical integration of 2-D joint KDE versus product of its marginals.
    a_np=np.array([-1.3,-.7,.1,.5,1.4]); b_np=np.array([-.8,-.5,.3,.9,1.0])
    h=.65; grid=np.linspace(-7,7,701); dx=grid[1]-grid[0]
    ga=np.exp(-.5*((grid[:,None]-a_np)/h)**2)/(math.sqrt(2*math.pi)*h)
    gb=np.exp(-.5*((grid[:,None]-b_np)/h)**2)/(math.sqrt(2*math.pi)*h)
    joint=ga@gb.T/len(a_np); product=ga.mean(1)[:,None]*gb.mean(1)[None,:]
    integ=math.log(np.sum(joint**2)*dx**2)+math.log(np.sum(product**2)*dx**2)-2*math.log(np.sum(joint*product)*dx**2)
    kernel,_=cs_qmi(torch.tensor(a_np[:,None]),torch.tensor(b_np[:,None]),sigma_u=math.sqrt(2)*h,sigma_v=math.sqrt(2)*h)
    assert abs(float(kernel)-integ)<1e-9
    add("continuous_KDE_integral", kernel=float(kernel), quadrature=integ)

    # Mixed KDE: Gaussian smoothing in x, counting measure in category y.
    labels_np=np.array([0,0,0,1,1]); pj=np.column_stack([ga[:,labels_np==c].sum(1)/5 for c in (0,1)])
    pm=ga.mean(1)[:,None]*np.array([.6,.4])[None,:]
    integ_d=math.log(np.sum(pj**2)*dx)+math.log(np.sum(pm**2)*dx)-2*math.log(np.sum(pj*pm)*dx)
    kernel_d,_=cs_qmi(torch.tensor(a_np[:,None]),labels=torch.tensor(labels_np),sigma_u=math.sqrt(2)*h)
    assert abs(float(kernel_d)-integ_d)<1e-9
    all_same,_=cs_qmi(u,labels=torch.zeros(len(u)),sigma_u=1.1)
    assert abs(float(all_same))<1e-12
    add("categorical_KDE_and_single_class", kernel=float(kernel_d), quadrature=integ_d, single_class=float(all_same))

    fm=fmca_logdet_loss(u,v,ridge_u=.02,ridge_v=.03)
    uc,vc=u-u.mean(0),v-v.mean(0); ru=uc.T@uc/len(u)+.02*torch.eye(3,dtype=torch.float64); rv=vc.T@vc/len(v)+.03*torch.eye(2,dtype=torch.float64); p=uc.T@vc/len(u)
    schur=torch.linalg.slogdet(rv-p.T@torch.linalg.solve(ru,p))[1]-torch.linalg.slogdet(rv)[1]
    assert torch.allclose(fm,schur,atol=1e-12,rtol=0)
    add("FMCA_matches_Schur_form", value=float(fm), error=float(abs(fm-schur)))

    ug=torch.randn(7,2,dtype=torch.float64,requires_grad=True); vg=torch.randn(7,2,dtype=torch.float64,requires_grad=True)
    assert torch.autograd.gradcheck(lambda x,y:cs_qmi(x,y,sigma_u=1.2,sigma_v=.9)[0],(ug,vg),atol=1e-5)
    assert torch.autograd.gradcheck(lambda x,y:fmca_logdet_loss(x,y,ridge_u=.04,ridge_v=.05),(ug,vg),atol=1e-5)
    loss=symmetric_infonce(ug,vg); loss.backward()
    assert torch.isfinite(ug.grad).all() and torch.isfinite(vg.grad).all()
    add("CS_FMCA_autograd_and_NCE_gradients", nce=float(loss.detach()))

    report={"scope":"synthetic numeric kernels and gradients only; no EEG training", "tests_passed":len(results), "torch_version":torch.__version__, "results":results}
    out=Path(__file__).resolve().parent/"NUMERICAL_TEST_RESULTS.json"
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))

if __name__=="__main__": main()
