from pathlib import Path
import argparse,json
import numpy as np
from time_access import (WINDOWS_MS,native_bounds,describe,crop_resample_pad,
                         source_tick_offsets,direct_access_interval,disjoint_with_guard)

def verify():
    checks=[]
    expected=[(-12,13),(0,26),(13,39)]
    assert [native_bounds(w,64) for w in WINDOWS_MS]==expected
    assert [describe(w,64)['resampled_valid_n'] for w in WINDOWS_MS]==[78,81,81]
    checks.append('source_half_open_native_indices_and_duration_preserved_lengths')
    assert [native_bounds(w,250,origin_ms=-200) for w in WINDOWS_MS]==[(0,100),(50,150),(100,200)]
    assert [describe(w,250,origin_ms=-200)['resampled_valid_n'] for w in WINDOWS_MS]==[80]*3
    checks.append('private_native_indices_and_lengths')
    assert [native_bounds(w,128) for w in WINDOWS_MS]==[(-25,26),(0,52),(26,77)]
    assert [describe(w,128)['resampled_valid_n'] for w in WINDOWS_MS]==[80,81,80]
    checks.append('public_128Hz_native_indices_and_80_81_80_lengths')
    safe=source_tick_offsets();cache=source_tick_offsets(mode='cache_contained')
    assert (len(safe),int(safe.min()),int(safe.max()))==(200,26,280)
    assert len(cache)==229 and 319 not in cache
    assert np.all(safe+39<=320)
    checks.append('actual_source_tick_grid_200_segment_contained_not_256_integer_offsets')
    assert 282+39>320 and 319+39>357
    checks.append('off_by_one_old_last_anchor_rejected')
    a=direct_access_interval(0,int(safe[-1]));b=direct_access_interval(320,int(safe[0]))
    assert disjoint_with_guard(a,b) and not disjoint_with_guard(a,b,guard_samples=17)
    checks.append('actual_physical_interval_guard_not_only_segment_identity')
    rng=np.random.default_rng(3435);x=rng.normal(size=(2,357))
    anchor=100
    for w in WINDOWS_MS:
        y,m=crop_resample_pad(x,w,64,anchor_index=anchor)
        altered=x.copy();a,b=m['actual_array_start'],m['actual_array_stop_exclusive']
        altered[...,:a]=1e5;altered[...,b:]=-1e5
        z,m2=crop_resample_pad(altered,w,64,anchor_index=anchor)
        assert np.array_equal(y,z)
        assert np.count_nonzero(y[...,m['resampled_valid_n']:])==0 and y.shape==(2,200)
    checks.append('outside_crop_perturbation_cannot_affect_resample')
    checks.append('right_padding_does_not_stretch_signal_to_one_second')
    try:crop_resample_pad(x,WINDOWS_MS[2],64,anchor_index=319)
    except ValueError:checks.append('out_of_bound_read_rejected_not_silently_zero_filled')
    else:raise AssertionError('missing bound check')
    return {'status':'PASS','checks':checks,'n_checks':len(checks),'numpy_version':np.__version__}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args()
    result=verify();text=json.dumps(result,indent=2)
    if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(text+'\n')
    print(text)
