"""Create outcome-blind BDF source manifest and timing diagnostics through Slurm."""
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import pyedflib
import mne

BASE = Path(__file__).resolve().parents[1]


def readcsv(p):
    with p.open(newline='') as f:
        return list(csv.DictReader(f))


def table(p, rows):
    with p.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}))
        w.writeheader(); w.writerows(rows)


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077)
    out = BASE / 'results/phase1_sources_001'; out.mkdir(exist_ok=False)
    priv = BASE / 'private/phase1_sources_001'; priv.mkdir(mode=0o700, exist_ok=False)
    paths = {r['file_id']: Path(r['absolute_path']) for r in readcsv(BASE / 'private/inventory_001/file_path_map.csv')}
    pairs = {r['candidate_acquisition_id']: r for r in readcsv(BASE / 'results/signal_001/bdf_pairing.csv')}
    participants = {r['participant_id']: r for r in readcsv(BASE / 'manifests/participant_index.csv')}
    # Read only source row and cohort label, never clinical score values.
    groups = {f'C{int(r["source_row"]):04d}': 'NH' if r['group'] == 'NH' else 'HA'
              for r in readcsv(BASE / 'private/clinical_003/clinical_rows_clean.csv')}
    links = defaultdict(list)
    for r in readcsv(BASE / 'manifests/clinical_link.csv'):
        links[r['candidate_acquisition_id']].append(r)
    events = defaultdict(list)
    for r in readcsv(BASE / 'results/other_eeg_001/event_ledger.csv'):
        if r['source'] == 'BDF_annotations': events[r['file_id']].append(r)
    recs = sorted(readcsv(BASE / 'manifests/recording_index.csv'), key=lambda r: r['recording_id'])
    rows = []; channelrows = []; errors = []; crosschecks = []
    for rec in recs:
        rid = rec['recording_id']; pair = pairs[rid]
        erows = events[pair['event_file_id']]
        cohort = set(groups.get(r['clinical_row_id'], 'unknown') for r in links[rid])
        row = dict(recording_id=rid, participant_id=rec['participant_id'],
                   participant_status='candidate_name_group', signal_file_id=pair['signal_file_id'],
                   event_file_id=pair['event_file_id'],
                   cohort_label=next(iter(cohort)) if len(cohort) == 1 else 'ambiguous',
                   cohort_evidence='candidate_clinical_group',
                   clinical_link_status='candidate_only_no_outcomes_loaded',
                   device_state='unknown', code_acoustics='unknown',
                   event_header_minus_signal_header_s=float(rec['event_header_minus_signal_header_s']),
                   identity_dob_conflict=int(participants[rec['participant_id']]['n_birthdate_strings']) > 1)
        rows.append(row)
        try:
            with pyedflib.EdfReader(str(paths[pair['signal_file_id']])) as reader:
                headers = reader.getSignalHeaders()
                labels = reader.getSignalLabels()
                sf = float(reader.getSampleFrequency(0)); ns = int(reader.getNSamples()[0])
                row.update(sfreq_hz=sf, n_samples=ns, n_channels=len(labels), duration_s=ns/sf,
                           channel_labels=json.dumps(labels), units=json.dumps(sorted({h['dimension'] for h in headers})),
                           all_channels_same_rate=bool(np.all(reader.getSampleFrequencies() == sf)))
                for k, h in enumerate(headers):
                    samples = np.concatenate([reader.readSignal(k, start=int((ns-int(5*sf))*fraction), n=int(5*sf))
                                              for fraction in (.1, .5, .9)])
                    channelrows.append(dict(recording_id=rid, channel=labels[k], unit=h['dimension'],
                                            physical_min=h['physical_min'], physical_max=h['physical_max'],
                                            digital_min=h['digital_min'], digital_max=h['digital_max'],
                                            preview_sd_native=float(np.std(samples)),
                                            preview_ptp_native=float(np.ptp(samples)),
                                            preview_finite=bool(np.isfinite(samples).all())))
                # Independent reader comparison on a deterministic subset, in volts.
                if len(crosschecks) < 3:
                    n = int(sf)
                    py = np.array([reader.readSignal(k, start=0, n=n) for k in range(len(labels))]) * 1e-6
                    raw = mne.io.read_raw_bdf(str(paths[pair['signal_file_id']]), preload=False, verbose='ERROR')
                    xx = raw.get_data(start=0, stop=n)
                    crosschecks.append(dict(recording_id=rid, channel_order_equal=raw.ch_names == labels,
                                            max_abs_difference_V=float(np.max(abs(xx-py))),
                                            sfreq_equal=raw.info['sfreq'] == sf))
            onsets = np.array([float(e['onset_s']) for e in erows])
            codes = np.array([e['event_code_token'] for e in erows])
            stim = onsets[np.isin(codes, ['1', '2'])]
            sample = np.rint(stim*sf).astype(np.int64)
            gaps = np.diff(stim)
            row.update(annotation_counts=json.dumps(dict(Counter(codes))), n_code_1_2=len(stim),
                       n_nonmonotonic_annotations=int(np.sum(np.diff(onsets) < 0)),
                       n_target_sample_collisions=len(sample)-len(set(sample)),
                       max_rounding_error_ms=float(np.max(abs(sample/sf-stim))*1000),
                       first_target_s=float(stim[0]), last_target_s=float(stim[-1]),
                       target_interval_min_s=float(gaps.min()), target_interval_median_s=float(np.median(gaps)),
                       target_interval_max_s=float(gaps.max()),
                       target_interval_below_0_5s=int(np.sum(gaps < .5)),
                       target_interval_above_2s=int(np.sum(gaps > 2)),
                       events_outside_signal=int(np.sum((onsets < 0) | (onsets >= ns/sf))))
            exclusions = []
            if row['event_header_minus_signal_header_s'] != 0: exclusions.append('companion_clock_mismatch')
            if row['n_target_sample_collisions']: exclusions.append('target_sample_collision')
            if row['n_nonmonotonic_annotations']: exclusions.append('event_order_conflict')
            if row['events_outside_signal']: exclusions.append('events_outside_signal')
            if row['units'] != '["uV"]': exclusions.append('unsupported_units')
            if not row['all_channels_same_rate']: exclusions.append('mixed_channel_rates')
            row.update(source_gate='eligible_technical_measurement' if not exclusions else 'hold',
                       source_gate_reasons=json.dumps(exclusions))
        except Exception as exc:
            row.update(source_gate='hold', source_gate_reasons='["reader_error"]')
            errors.append(dict(recording_id=rid, error=repr(exc)))
    table(out / 'source_manifest.csv', rows)
    table(out / 'channel_header_and_preview.csv', channelrows)
    table(out / 'reader_crosschecks.csv', crosschecks)
    (priv / 'errors.json').write_text(json.dumps(errors, indent=2))
    summary = {'job_id': os.environ['SLURM_JOB_ID'], 'records': len(rows),
               'cohort_counts': dict(Counter(r['cohort_label'] for r in rows)),
               'gate_counts': dict(Counter(r['source_gate'] for r in rows)),
               'eligible_cohorts': dict(Counter(r['cohort_label'] for r in rows if r['source_gate'].startswith('eligible'))),
               'sample_collisions': sum(r.get('n_target_sample_collisions', 0) for r in rows),
               'events_outside_signal': sum(r.get('events_outside_signal', 0) for r in rows),
               'annotation_code_counts': dict(sum((Counter(json.loads(r.get('annotation_counts','{}'))) for r in rows), Counter())),
               'reader_crosschecks': crosschecks, 'errors': len(errors), 'clinical_outcomes_used': False}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__': main()
