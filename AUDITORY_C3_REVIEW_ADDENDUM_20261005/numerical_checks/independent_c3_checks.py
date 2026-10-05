"""Independent, synthetic checks of the uploaded C3 reference implementation.
No EEG, downloads, server access, or changes to the original package.
These are counterexamples to general implications, not estimates for real participants.
"""
from pathlib import Path
import json, sys, hashlib
import numpy as np
from scipy.stats import entropy
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from gcmi_core import gcmi_cc, gcmi_ccc, cmi_model_gdd, gcmi_model_cd, copnorm, collapse_rare
rng=np.random.default_rng(20261005)
n=60000
R={}
# Independent noises make conditional independence exact, but rank-Gaussian partial association nonzero.
z=rng.standard_normal(n)
x=z*z+0.4*rng.standard_normal(n)
y=z*z+0.4*rng.standard_normal(n)
R['nonlinear_common_cause']={'true_I_XY_given_Z_bits':0.,'gcmi_ccc_bits':float(gcmi_ccc(x,y,z)),
 'gcmi_XY_bits':float(gcmi_cc(x,y)), 'assumption':'X=Z^2+independent noise; Y=Z^2+independent noise'}
# Gaussian target mixture within Z: raw model comparison can exceed discrete entropy.
z=rng.integers(0,2,n); h=rng.integers(0,2,n)
x=6*(2*h-1)+rng.standard_normal(n)
raw=float(cmi_model_gdd(x,h,z))
perm=[]
for b in range(30):
 xp=x.copy()
 for k in (0,1):
  ix=np.flatnonzero(z==k); xp[ix]=x[rng.permutation(ix)]
 perm.append(cmi_model_gdd(xp,h,z))
within=sum(np.mean(z==k)*gcmi_model_cd(x[z==k],h[z==k]) for k in (0,1))
R['mixed_cmi_entropy_bound']={'conditional_discrete_entropy_upper_bound_bits':1.,'raw_cmi_model_gdd_bits':raw,
 'stratified_surrogate_mean_bits':float(np.mean(perm)),'surrogate_subtracted_bits':float(raw-np.mean(perm)),
 'within_stratum_copnorm_model_bits':float(within),
 'note':'The last value is an alternative estimate, not a validated patch or the true MI.'}
# Silent semantic merging and skipping are readily visible.
labs=np.r_[np.zeros(181,dtype=int),np.ones(19,dtype=int)]
v=10*labs+rng.normal(0,.05,len(labs))
R['rare_class']={'counts':[181,19],'classes_after_collapse':np.unique(collapse_rare(labs)).tolist(),
 'returned_MI_bits':float(gcmi_model_cd(v,labs)),
 'target_entropy_bits':float(entropy([181/200,19/200],base=2)),
 'note':'A strongly separated rare category is silently removed; this is not evidence of independence.'}
# All strata smaller than 40 are silently omitted.
nsmall=60; zz=np.tile([0,1],30); hh=np.tile([0,0,1,1],15)
xs=8*hh+rng.normal(0,.1,nsmall)
R['small_condition_strata']={'stratum_counts':[30,30],'returned_CMI_bits':float(cmi_model_gdd(xs,hh,zz))}
# A constant source becomes a trend under ordered ranks.
nt=4000; const=np.zeros(nt); clock=np.linspace(0,1,nt); drift=clock+.25*rng.standard_normal(nt)
cn=copnorm(const).ravel()
R['ties']={'true_MI_of_constant_bits':0.,'copnorm_constant_std':float(cn.std()),
 'gcmi_constant_with_time_trend_bits':float(gcmi_cc(const,drift)),
 'note':'Order tie-breaking injects a sample-index signal.'}
# Chronological age adjustment vs a noisy EEG-age proxy; all Gaussian.
age=rng.standard_normal(n); dur=age+rng.standard_normal(n)
evidence=age+rng.standard_normal(n); eegage=age+rng.standard_normal(n)
R['noisy_age_conditioning']={'true_I_E_D_given_age_bits':0.,
 'estimated_given_age_bits':float(gcmi_ccc(evidence,dur,age)),
 'estimated_given_noisy_eeg_age_bits':float(gcmi_ccc(evidence,dur,eegage)),
 'analytic_noisy_proxy_bits':float(-.5*np.log2(1-(1/3)**2))}
# Controlled Markov sequence with no consecutive deviants and stationary P(dev)=.2.
nm=80000; cur=np.zeros(nm,dtype=int)
for j in range(1,nm): cur[j]=int(cur[j-1]==0 and rng.random()<.25)
hist=cur[:-1]; current=cur[1:]
score=hist+.35*rng.standard_normal(nm-1)
# A scalar copnorm within each history stratum is sufficient here, as current-only Gaussian CMI also ~0.
conditional=sum(np.mean(hist==k)*gcmi_model_cd(score[hist==k],current[hist==k]) for k in (0,1))
R['current_via_history_only']={'model':'score = previous class + independent noise',
 'I_score_current_bits':float(gcmi_model_cd(score,current)),
 'I_score_current_given_history_bits':float(conditional),
 'true_conditional_information_bits':0.,'deviant_fraction':float(current.mean())}
# Same information per observation does not imply per-second rate under duplicates.
R['sampling_rate_duplicate']={'example':'T=A+noise with noise variance 1; one independent draw each second repeated m times',
 'true_information_per_original_second_bits':.5,'naive_I_times_fs_at_1Hz_bits_per_s':.5,
 'naive_I_times_fs_at_128Hz_bits_per_s':64.,
 'note':'Duplicating the same observation creates no new joint information.'}
# Unequal block null corrections break chain identities if nulls differ.
R['null_chain_consistency']={'symbolic':'[I_AB-b_AB]-[I_A-b_A] = I_B_given_A-(b_AB-b_A); equals separate corrected CMI only if b_CMI=b_AB-b_A',
 'consequence':'Use a common surrogate law for a decomposition; keep null-excess statistics distinct from PID atoms.'}
R['source_sha256']=hashlib.sha256((ROOT/'gcmi_core.py').read_bytes()).hexdigest()
out=ROOT/'independent_results.json'; out.write_text(json.dumps(R,indent=2,ensure_ascii=False))
print(json.dumps(R,indent=2,ensure_ascii=False))
