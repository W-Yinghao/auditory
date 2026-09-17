"""Pure numerical operations for fixed Phase 2 analyses (run tests via Slurm)."""
import numpy as np


def agreement_metrics(pairs):
    """Two-way absolute-agreement, single-measure ICC(A,1); final axes n x 2.

    Leading dimensions can contain bootstrap draws. No clipping of negative ICC.
    Constant scores and too few pairs are not evidence of reliability.
    """
    x = np.asarray(pairs, float)
    n, k = x.shape[-2:]
    if k != 2 or n < 2 or not np.isfinite(x).all():
        raise ValueError('need at least two finite paired scores')
    grand = x.mean(axis=(-2, -1), keepdims=True)
    rows = x.mean(axis=-1, keepdims=True)
    cols = x.mean(axis=-2, keepdims=True)
    ms_r = k * np.sum((rows-grand)**2, axis=(-2, -1))/(n-1)
    ms_c = n * np.sum((cols-grand)**2, axis=(-2, -1))/(k-1)
    ms_e = np.sum((x-rows-cols+grand)**2, axis=(-2, -1))/((n-1)*(k-1))
    den = ms_r+(k-1)*ms_e+k/n*(ms_c-ms_e)
    icc = np.divide(ms_r-ms_e, den, out=np.full_like(den, np.nan), where=abs(den)>1e-14)
    a, b = x[..., 0], x[..., 1]
    ac, bc = a-a.mean(axis=-1, keepdims=True), b-b.mean(axis=-1, keepdims=True)
    rden = np.sqrt(np.sum(ac**2, axis=-1)*np.sum(bc**2, axis=-1))
    r = np.divide(np.sum(ac*bc, axis=-1), rden, out=np.full_like(rden, np.nan), where=rden>1e-14)
    # With no between-person variation reliability is undefined, even with an offset.
    icc = np.where(ms_r>1e-14, icc, np.nan)
    d = b-a
    bias = d.mean(axis=-1); sd = d.std(axis=-1, ddof=1)
    return {'icc_a1':icc, 'pearson_r':r, 'bias_b_minus_a_uv':bias,
            'difference_sd_uv':sd, 'loa_low_uv':bias-1.96*sd, 'loa_high_uv':bias+1.96*sd,
            'rmse_uv':np.sqrt(np.mean(d**2, axis=-1))}


def pair_summary(pairs, rng, repetitions=2000):
    pairs = np.asarray(pairs, float)
    stats = {k:float(v) for k,v in agreement_metrics(pairs).items()}
    draws = rng.integers(len(pairs), size=(repetitions, len(pairs)))
    boot = agreement_metrics(pairs[draws])
    for key in ('icc_a1', 'pearson_r', 'bias_b_minus_a_uv'):
        finite = boot[key][np.isfinite(boot[key])]
        stats[key+'_bootstrap_valid'] = len(finite)
        lo,hi = np.quantile(finite, [.025,.975]) if len(finite)>=.95*repetitions else [np.nan,np.nan]
        stats[key+'_ci_low'] = float(lo); stats[key+'_ci_high'] = float(hi)
    return stats


def frontal_variant(data, channels):
    """Saved average20 data -> average18 ROI and reference-invariant frontal proxy."""
    ix = {str(c):i for i,c in enumerate(channels)}
    roi = data[:,[ix['Fz'],ix['Cz']],:].mean(axis=1)
    retained = [i for c,i in ix.items() if c not in ('Fp1','Fp2')]
    avg18 = roi-data[:,retained,:].mean(axis=1)
    proxy = data[:,[ix['Fp1'],ix['Fp2']],:].mean(axis=1)-data[:,[ix['Oz'],ix['O1'],ix['O2']],:].mean(axis=1)
    return avg18, proxy


def balanced_selection(codes, mask, half_b, rng):
    """One seeded subset per condition per half, reused by matched references."""
    chosen = np.zeros(len(codes), bool)
    for code in (1,2):
        a = np.flatnonzero(mask & (codes==code) & ~half_b)
        b = np.flatnonzero(mask & (codes==code) & half_b)
        n = min(len(a),len(b))
        chosen[rng.choice(a,n,replace=False)] = True
        chosen[rng.choice(b,n,replace=False)] = True
    return chosen


def ridge_predict(train_x, train_y, test_x, alpha=1.):
    """Training-only scaling, unpenalized intercept; supports zero-column baseline."""
    train_x=np.asarray(train_x,float); test_x=np.asarray(test_x,float); train_y=np.asarray(train_y,float)
    if train_x.ndim!=2 or test_x.ndim!=2 or train_y.shape!=(len(train_x),) or train_x.shape[1]!=test_x.shape[1]:
        raise ValueError('ridge expects aligned 2D predictors and 1D training outcome')
    if not train_x.shape[1]: return np.full(len(test_x),train_y.mean())
    center=train_x.mean(axis=0); scale=train_x.std(axis=0)
    scale=np.where(scale>1e-12,scale,1.)
    z=(train_x-center)/scale; test=(test_x-center)/scale
    beta=np.linalg.solve(z.T@z+alpha*np.eye(z.shape[1]),z.T@(train_y-train_y.mean()))
    return train_y.mean()+test@beta
