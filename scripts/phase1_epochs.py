"""Fixed, outcome-blind full BDF QC and event-aligned epoch reconstruction."""
import argparse
import csv
import hashlib
import json
import os
import time
import traceback
from collections import Counter
from pathlib import Path
import mne
import numpy as np
import pyedflib
from phase1_prepare import readcsv, table
from phase1_core import epoch_grid, reference, baseline

BASE = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''): h.update(b)
    return h.hexdigest()


def process(row, paths, cfg, out, private):
    start = time.monotonic()
    rid = row['recording_id']; destination = out / rid
    destination.mkdir(exist_ok=False)
    sf = cfg['sample_rate_hz']
    source = paths[row['signal_file_id']]
    source_stat = source.stat()
    signal_hash = hashlib.sha256()
    channels = []; saturation = []; flat = []
    with pyedflib.EdfReader(str(source)) as f:
        assert np.all(f.getSampleFrequencies() == sf)
        labels = f.getSignalLabels()
        assert labels == json.loads(row['channel_labels'])
        assert len(set(labels)) == len(labels)
        n_samples = int(f.getNSamples()[0]); assert n_samples == int(row['n_samples'])
        data = np.empty((len(labels), n_samples), dtype=np.float64)
        rail = np.zeros_like(data, dtype=bool)
        for k, name in enumerate(labels):
            h = f.getSignalHeader(k)
            assert h['dimension'] == 'uV'
            x = f.readSignal(k); data[k] = x
            signal_hash.update(np.asarray(x, dtype='<f8').tobytes())
            step = (h['physical_max']-h['physical_min']) / (h['digital_max']-h['digital_min'])
            rail[k] = (x <= h['physical_min']+step) | (x >= h['physical_max']-step)
            blocksize = int(2*sf)
            blockptp = np.ptp(x[:len(x)//blocksize*blocksize].reshape(-1, blocksize), axis=1)
            fracflat = float(np.mean(blockptp < cfg['flat_epoch_peak_to_peak_uv']))
            channels.append(dict(recording_id=rid, channel=name,
                all_finite=bool(np.isfinite(x).all()), raw_mean_uv=float(np.mean(x)),
                raw_sd_uv=float(np.std(x)), raw_min_uv=float(x.min()), raw_max_uv=float(x.max()),
                median_2s_ptp_uv=float(np.median(blockptp)), fraction_2s_blocks_flat=fracflat,
                saturation_samples=int(rail[k].sum()), saturation_fraction=float(rail[k].mean())))
            if rail[k].any(): saturation.append(name)
            if fracflat >= .2: flat.append(name)
    table(destination / 'channel_qc.csv', channels)
    summary = dict(row, job_id=os.environ['SLURM_JOB_ID'],
                   signal_numeric_sha256=signal_hash.hexdigest(), event_file_sha256=digest(paths[row['event_file_id']]),
                   raw_samples_examined=n_samples*len(labels),
                   channels_with_saturation=json.dumps(saturation), channels_flat_in_at_least_20pct_blocks=json.dumps(flat),
                   source_signal_size=source_stat.st_size,
                   clinical_outcomes_used=False, config_sha256=digest(BASE/'configs/phase1_v1.json'))
    (private/f'{rid}_source_stat.json').write_text(json.dumps(dict(signal_file_id=row['signal_file_id'],
        source_signal_mtime_ns=source_stat.st_mtime_ns,source_signal_size=source_stat.st_size),indent=2))
    if row['source_gate'] != cfg['source_gate'] or not np.isfinite(data).all():
        summary.update(status='source_hold_no_epochs', raw_finite=bool(np.isfinite(data).all()),
                       elapsed_s=time.monotonic()-start)
        (destination/'summary.json').write_text(json.dumps(summary, indent=2)); return summary
    scalp = [labels.index(c) for c in cfg['scalp_channels']]
    ears = [labels.index(c) for c in ('A1', 'A2')]
    roi = [cfg['scalp_channels'].index(c) for c in cfg['roi_channels']]
    with pyedflib.EdfReader(str(paths[row['event_file_id']])) as f:
        onsets, durations, descriptions = f.readAnnotations()
    descriptions = [str(c).strip() for c in descriptions]
    assert Counter(descriptions) == Counter(json.loads(row['annotation_counts']))
    assert np.all(np.diff(onsets) >= 0)
    target_indices = [i for i, code in enumerate(descriptions) if code in cfg['event_codes']]
    target_samples = np.rint(onsets[target_indices]*sf).astype(np.int64)
    assert len(np.unique(target_samples)) == len(target_samples)
    offsets, keep_samples, times = epoch_grid(sf, cfg['epoch_tmin_s'], cfg['epoch_tmax_s'], cfg['decimation'])
    reasons = {}
    eligible = []
    edge = int(cfg['edge_guard_s']*sf)
    for rank, (event_index, sample) in enumerate(zip(target_indices, target_samples)):
        why = []
        if sample+offsets[0] < edge or sample+offsets[-1] >= n_samples-edge:
            why.append('record_edge_guard')
        if rank and target_samples[rank-1] >= sample+offsets[0]: why.append('previous_target_in_epoch')
        if rank+1 < len(target_samples) and target_samples[rank+1] <= sample+offsets[-1]: why.append('next_target_in_epoch')
        reasons[event_index] = why
        if not why: eligible.append((event_index, sample))
    n = len(eligible)
    full_epochs = np.empty((n, len(scalp), len(times)), dtype=np.float32)
    roi_waves = np.empty((n, 3, len(times)), dtype=np.float32)
    qc = []; filter_lengths = []
    masks = np.zeros((n, 3), dtype=bool)
    # Each filter processes the continuous signal before epoching.
    for variant, hp in enumerate(cfg['highpass_hz']):
        filt = mne.filter.create_filter(None, sf, hp, cfg['lowpass_hz'],
            l_trans_bandwidth=hp, h_trans_bandwidth=cfg['lowpass_transition_hz'],
            method='fir', phase='zero', fir_window='hamming', fir_design='firwin', verbose='ERROR')
        filter_lengths.append(len(filt))
        assert (len(filt)-1)/(2*sf) <= cfg['edge_guard_s']
        filtered = mne.filter.filter_data(data, sf, hp, cfg['lowpass_hz'],
            l_trans_bandwidth=hp, h_trans_bandwidth=cfg['lowpass_transition_hz'],
            method='fir', phase='zero', fir_window='hamming', fir_design='firwin',
            pad='reflect_limited', n_jobs=1, verbose='ERROR')
        for j, (event_index, sample) in enumerate(eligible):
            x = filtered[:, sample+offsets]
            avg, ear = reference(x, scalp, ears)
            avg = baseline(avg, offsets/sf, cfg['baseline_s'])
            if variant == 0:
                ptp = np.ptp(avg, axis=1)
                minimum_original_ptp = float(np.min(np.ptp(x[scalp], axis=1)))
                isflat = minimum_original_ptp < cfg['flat_epoch_peak_to_peak_uv']
                issat = bool(rail[np.ix_(scalp, sample+offsets)].any())
                finite = bool(np.isfinite(avg).all())
                masks[j] = [finite and not isflat and not issat and float(ptp.max()) <= threshold
                            for threshold in (cfg['epoch_peak_to_peak_uv'], *cfg['epoch_peak_to_peak_sensitivity_uv'])]
                why = []
                if not finite: why.append('nonfinite')
                if isflat: why.append('flat_scalp_channel')
                if issat: why.append('raw_saturation')
                if ptp.max() > cfg['epoch_peak_to_peak_uv']: why.append('scalp_ptp_above_150uv')
                reasons[event_index] = why
                full_epochs[j] = avg[:, keep_samples]
                roi_waves[j, 0] = avg[roi][:, keep_samples].mean(axis=0)
                roi_waves[j, 2] = baseline(ear, offsets/sf, cfg['baseline_s'])[roi][:, keep_samples].mean(axis=0)
                qc.append(dict(event_index_1based=event_index+1, max_scalp_ptp_uv=float(ptp.max()),
                               min_original_scalp_ptp_uv=minimum_original_ptp, raw_saturation=issat,
                               ear_raw_saturation=bool(rail[np.ix_(ears, sample+offsets)].any()),
                               ear_filtered_max_ptp_uv=float(np.ptp(x[ears],axis=1).max()),
                               accepted_150uv=bool(masks[j,0]), accepted_100uv=bool(masks[j,1]), accepted_200uv=bool(masks[j,2])))
            else:
                roi_waves[j, 1] = avg[roi][:, keep_samples].mean(axis=0)
        del filtered
    ledger = []
    byevent = {r['event_index_1based']-1:r for r in qc}
    saved = {event_index:j for j,(event_index,_) in enumerate(eligible)}
    for i, (onset, code) in enumerate(zip(onsets, descriptions)):
        r = dict(recording_id=rid, source_event_file_id=row['event_file_id'], event_index_1based=i+1,
                 onset_s=float(onset), signal_sample_0based=int(round(onset*sf)), event_code=code,
                 event_acoustics='unknown', time_block_30s=int(onset//cfg['time_block_s']),
                 stored_epoch_0based=saved.get(i, ''),
                 disposition=('non_target_code_unknown' if code not in cfg['event_codes'] else
                              'accepted' if not reasons[i] else 'rejected'),
                 reasons=json.dumps(reasons.get(i, ['not_analyzed_code'])))
        r.update(byevent.get(i, {})); ledger.append(r)
    table(destination/'epoch_ledger.csv', ledger)
    event_index = np.array([i+1 for i,_ in eligible])
    samples = np.array([s for _,s in eligible])
    codes = np.array([int(descriptions[i]) for i,_ in eligible])
    block = np.floor(samples/sf/cfg['time_block_s']).astype(int)
    np.savez_compressed(destination/'epochs.npz', data_uv=full_epochs, roi_uv=roi_waves,
        times_s=times, channels=np.array(cfg['scalp_channels']), roi_channels=np.array(cfg['roi_channels']),
        roi_variant_names=np.array(['hp01_avg','hp05_avg','hp01_ears']),
        accepted=masks, acceptance_thresholds_uv=np.array([150,100,200]),
        event_indices_1based=event_index, samples_0based=samples, codes=codes, blocks=block,
        config_sha256=np.array(summary['config_sha256']))
    assert source.stat().st_mtime_ns == source_stat.st_mtime_ns and source.stat().st_size == source_stat.st_size
    for k, threshold in enumerate((150,100,200)):
        summary[f'accepted_{threshold}uv'] = int(masks[:, k].sum())
        for code in (1, 2): summary[f'accepted_{threshold}uv_code{code}'] = int(np.sum(masks[:, k] & (codes == code)))
    summary.update(status='epochs_created', n_target_events=len(target_indices), stored_epochs=n,
        pre_epoch_rejected=len(target_indices)-n, rejection_reason_counts=dict(Counter(reason for v in reasons.values() for reason in v)),
        filter_lengths_samples=filter_lengths, elapsed_s=time.monotonic()-start,
        epoch_data_sha256=digest(destination/'epochs.npz'), raw_finite=True)
    (destination/'summary.json').write_text(json.dumps(summary, indent=2))
    return summary


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--shard', type=int, default=0)
    parser.add_argument('--shards', type=int, default=1)
    parser.add_argument('--record-ids', nargs='*')
    args = parser.parse_args()
    out = BASE/'results'/args.run; out.mkdir(exist_ok=True)
    private = BASE/'private'/args.run; private.mkdir(mode=0o700, exist_ok=True)
    cfg = json.loads((BASE/'configs/phase1_v1.json').read_text())
    paths = {r['file_id']:Path(r['absolute_path']) for r in readcsv(BASE/'private/inventory_001/file_path_map.csv')}
    rows = sorted(readcsv(BASE/cfg['source_manifest']), key=lambda r:r['recording_id'])
    if args.record_ids: rows = [r for r in rows if r['recording_id'] in args.record_ids]
    else: rows = rows[args.shard::args.shards]
    metadata = dict(job_id=os.environ['SLURM_JOB_ID'], shard=args.shard,
        config=cfg, config_sha256=digest(BASE/'configs/phase1_v1.json'),
        source_manifest_sha256=digest(BASE/cfg['source_manifest']),
        code_sha256={name:digest(BASE/'scripts'/name) for name in ('phase1_epochs.py','phase1_core.py','phase1_prepare.py')},
        mne_version=mne.__version__, numpy_version=np.__version__, expected_records=[r['recording_id'] for r in rows])
    mp = out/f'run_shard_{args.shard:02d}.json'
    if mp.exists(): raise FileExistsError(mp)
    mp.write_text(json.dumps(metadata, indent=2))
    snapshot = out/f'code_shard_{args.shard:02d}'; snapshot.mkdir(exist_ok=False)
    for name in ('phase1_epochs.py','phase1_core.py','phase1_prepare.py'):
        (snapshot/name).write_bytes((BASE/'scripts'/name).read_bytes())
    (snapshot/'phase1_v1.json').write_bytes((BASE/'configs/phase1_v1.json').read_bytes())
    errors = []; successful = []
    for row in rows:
        rid = row['recording_id']
        try:
            result = process(row,paths,cfg,out,private)
            successful.append(rid)
            print(json.dumps({k:result.get(k) for k in ('recording_id','status','accepted_150uv','elapsed_s')}), flush=True)
        except Exception as exc:
            errors.append(dict(recording_id=rid,error=repr(exc),trace=traceback.format_exc()))
            print(json.dumps(dict(recording_id=rid,status='error',error_class=type(exc).__name__)),flush=True)
    (private/f'errors_{args.shard:02d}.json').write_text(json.dumps(errors,indent=2))
    (out/f'completion_{args.shard:02d}.json').write_text(json.dumps(dict(job_id=os.environ['SLURM_JOB_ID'],
        records_attempted=len(rows),records_completed=successful, errors=len(errors)),indent=2))
    if errors: raise RuntimeError(f'{len(errors)} records failed; see private logs')


if __name__ == '__main__': main()
