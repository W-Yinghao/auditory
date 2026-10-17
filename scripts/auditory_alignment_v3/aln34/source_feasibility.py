"""Read-only source/header inventory for the remaining ALN3.4 sensitivities."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import h5py
import mne

ROOT = Path('/home/infres/yinwang/EEG_auditory')
PUB = Path('/projects/EEG-foundation-model/auditory_public')
OUT = ROOT / 'private/auditory_alignment_v3/aln34/source_feasibility_20261017.json'

def stat(p):
    return {'file': str(p), 'exists': p.is_file(),
            'bytes': p.stat().st_size if p.is_file() else None}

def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077)
    from auditory_c3.preproc import H5
    result = {'time': datetime.now().astimezone().isoformat(),
              'job': os.environ['SLURM_JOB_ID'], 'inspection': 'headers and metadata only; no outcome selection',
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'fau': {}}
    for group, rel in H5.items():
        p = PUB / rel
        item = stat(p)
        if p.is_file():
            with h5py.File(p, 'r') as f:
                subjects = sorted(f['eeg'])
                trials = [f['eeg'][s][t] for s in subjects for t in f['eeg'][s] if t.isdigit()]
                item.update(subjects=len(subjects), trials=len(trials),
                            row_counts=sorted({t.shape[0] for t in trials}),
                            fs_from_existing_preprocessor=1000,
                            waves={code: {k: list(f['stimulus_files'][code][k].shape)
                                          for k in ('attended_wav', 'distractor_wav') if k in f['stimulus_files'][code]}
                                   for code in sorted(f['stimulus_files'])})
                item['limit'] = 'Published HDF5 before our FIR; provider/hardware filtering is not certified absent. Spatial and alignment provenance must be preserved.'
        result['fau'][group] = item
    dtu = PUB / 'dtu_snhl/ds-eeg-snhl/ds-eeg-snhl'
    rows = []
    for p in sorted(dtu.glob('sub-*/eeg/*task-selectiveattention*_eeg.bdf')):
        raw = mne.io.read_raw_bdf(p, preload=False, verbose=False)
        rows.append({**stat(p), 'fs': float(raw.info['sfreq']), 'n_times': int(raw.n_times),
                     'channels': len(raw.ch_names),
                     'events_exists': p.with_name(p.name.replace('_eeg.bdf', '_events.tsv')).is_file()})
        raw.close()
    # The provider's waveform delivery is a sibling audio_drcmr tree, not the
    # BIDS EEG root. Use the already-used feature inventory, not guessed paths.
    invpath = PUB / 'derived/c3_features_v1/dtu/inventory.json'
    inventory = json.loads(invpath.read_text())
    waves = sorted({Path(r['path']) for r in inventory if r.get('path')})
    result['dtu'] = {'recordings': rows, 'waveforms': [stat(p) for p in waves],
                     'wave_inventory_sha256': hashlib.sha256(invpath.read_bytes()).hexdigest(),
                     'wave_inventory_rows': len(inventory), 'wave_missing_paths': sum(not p.is_file() for p in waves),
                     'limit': 'Native BDF supports a new causal pipeline; old zero-phase and resample_poly caches cannot be made causal by refiltering.'}
    fed = PUB / 'federici_ci_children'
    result['federici'] = {'waveforms': [stat(p) for p in sorted(fed.rglob('*.wav'))],
                          'raw_recording_extensions': {ext: len(list(fed.rglob('*' + ext))) for ext in ('.bdf', '.edf', '.vhdr', '.fif')},
                          'limit': 'Current released EEG cache is 2-8Hz. Other files are not treated as raw EEG without a separate schema/provenance check.'}
    result['source_hashes'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [ROOT/'auditory_c3/preproc.py', ROOT/'auditory_c3/stageb.py', ROOT/'auditory_alignment/data.py']}
    tmp = OUT.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(result, indent=2) + '\n'); os.replace(tmp, OUT)
    print(json.dumps({'fau': {g: {'subjects': v.get('subjects'), 'trials': v.get('trials'), 'wave_codes': len(v.get('waves', {}))}
                             for g,v in result['fau'].items()},
                      'dtu_recordings': len(rows), 'dtu_waves': len(waves),
                      'federici_waves': len(result['federici']['waveforms']), 'output': str(OUT)}), flush=True)

if __name__ == '__main__': main()
