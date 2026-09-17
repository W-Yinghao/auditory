"""Independent configuration/duplicate and epoch smoke checks, under Slurm."""
import json,os
from pathlib import Path
import mne
import numpy as np
from phase1_prepare import readcsv
from phase3_ci_measurements import bins, decoding
BASE=Path(__file__).resolve().parents[1]
def main():
    assert os.getenv('SLURM_JOB_ID');os.umask(0o077)
    cfg=json.loads((BASE/'configs/phase3_science_v1.json').read_text())['ci']
    manifest=readcsv(BASE/'results/phase3_ci_sources_001/source_manifest.csv')
    paths={r['container_id']:r['path'] for r in readcsv(BASE/'private/phase3_ci_sources_001/source_paths_and_tokens.csv')}
    checks=[]
    for row in manifest:
        if row['source_status']!='exact_binary_duplicate':continue
        a=mne.io.read_raw_egi(paths[row['container_id']],preload=False,verbose='ERROR')
        b=mne.io.read_raw_egi(paths[row['canonical_container_id']],preload=False,verbose='ERROR')
        assert a.ch_names==b.ch_names and a.info['sfreq']==b.info['sfreq']
        assert np.array_equal(a._cals,b._cals)
        assert np.allclose([c['loc'] for c in a.info['chs']],[c['loc'] for c in b.info['chs']],equal_nan=True)
        for key in ['first_samps','last_samps']:assert np.array_equal(a._raw_extras[0][key],b._raw_extras[0][key])
        assert np.array_equal(a.annotations.description,b.annotations.description)
        assert np.array_equal(a.annotations.onset,b.annotations.onset)
        checks.append(row['container_id']);a.close();b.close()
    for sf in [250,500,1000]:
        kernel=mne.filter.create_filter(None,sf,cfg['highpass_hz'],cfg['lowpass_hz'],l_trans_bandwidth=cfg['highpass_hz'],h_trans_bandwidth=7.5,verbose='ERROR')
        assert (len(kernel)-1)/2/sf<cfg['edge_guard_s']
    for p in (BASE/'results/phase3_ci_smoke_001').glob('M*/epochs_roi.npz'):
        with np.load(p,allow_pickle=False) as d:
            x=d['roi_uv'];t=d['times_s'];accepted=d['accepted']
            assert np.isfinite(x).all() and x.shape[1:]==(2,176)
            assert np.count_nonzero(np.isclose(t,0))==1 and np.all(~accepted[:,1]|accepted[:,0])
            for start,end in cfg['decoding_windows_s'].values():assert bins(x,t,start,end).shape==(len(x),10)
    # A deterministic synthetic strong response checks class orientation and blocked support.
    rng=np.random.default_rng(731);t=np.arange(-50,126)/250;codes=np.array(['stad','devt']*150)
    x=rng.normal(0,.1,(len(codes),2,len(t)));x[codes=='devt',:,:]+=((t>=.05)&(t<.25))*5
    ds,folds,preds=decoding(x,codes,np.arange(len(codes))*600,t,1000,cfg,'synthetic','primary')
    assert next(r for r in ds if r['window']=='poststim')['mean_fold_auc']>.99
    assert all(r['valid_folds']==5 for r in ds)
    out=BASE/'results/phase3_ci_verification_001';out.mkdir(exist_ok=False)
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],status='passed',duplicate_metadata_pairs=len(checks),duplicate_equality='EEG calibrations, channel geometry, interval boundaries and event codes/onsets all equal',filter_half_support_inside_guard=True,smoke_layouts_checked=4,synthetic_blocked_decoder_orientation=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
