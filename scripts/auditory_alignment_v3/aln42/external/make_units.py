"""Write the 10 public-unit bindings (content fold x person fold: train people, test people, fit/es/test 5 s cs segment
counts from GATE345 census) and the channel contract file, using the frozen project fold helper (seed 20261005)."""
import glob, json, os, sys
import pandas as pd
from auditory_alignment import data as D
E = os.path.dirname(os.path.abspath(__file__))
S = '/projects/EEG-foundation-model/auditory_public/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl'
part = pd.read_csv(f'{S}/participants.tsv', sep='\t'); hs = dict(zip(part.participant_id, part.hearing_status))
subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(D.REPO, 'private', 'auditory_c3', 'public', 'dtu_v2', '*.json')))
folds = D._folds({g: [s for s in subs if hs[s] == g] for g in ('nh', 'hi')})
census = json.load(open(f'{E}/GATE345_RESULTS.json'))['census_cs_5s_segments']
units = []
for cf in (0, 1):
    for sf in range(5):
        c = census[f'cf{cf}_sf{sf}']
        units.append({'unit': f'dtu_cf{cf}_sf{sf}', 'content_fold': cf, 'person_fold': sf, 'seed': 3401,
                      'train_people': [s for s in subs if folds[s] != sf], 'test_people': [s for s in subs if folds[s] == sf],
                      'roles': 'content role per target waveform: test if content half == cf; es if early_stop; else fit (load_dtu)',
                      'cs_5s_segments': {'fit_train_people': c['fit'], 'es_train_people': c['es'], 'test_test_people': c['test_people_test_role']},
                      'mindmix_2s_windows': {'fit': 2 * c['fit'], 'es': 2 * c['es'], 'test': 2 * c['test_people_test_role']}})
json.dump(units, open(f'{E}/PUBLIC_UNITS.draft.json', 'w'), indent=1)
g = json.load(open(f'{E}/GATE345_RESULTS.json'))['gate3_channels']
ch = {'dtu_channels_in_input_order': g['dtu_first64_eeg'], 'mindmix_ch_names_equal_casefold_same_order': g['mindmix_ch_names_equal_casefold_same_order'],
      'excluded': ['EXG1-EXG8', 'Status'], 'reference': 'recorded BioSemi CMS/DRL, not re-referenced (as project c3 preprocessing)',
      'units': 'uV before per-window per-channel z-score (z-score makes the unit immaterial)', 'fs_in': 512, 'fs_model': 200,
      'band': '1-40 Hz, scipy butter(N=4, bandpass) + sosfiltfilt (zero-phase), continuous run', 'window': '2 s = 400 samples -> [64, 2, 200]',
      'spatial_embedding': 'none at pinned commit (pos_embed forced None; no input_chans passed); encoder is channel-permutation invariant'}
json.dump(ch, open(f'{E}/CHANNEL_CONTRACT.json', 'w'), indent=1)
print(len(units), [len(u['test_people']) for u in units[:5]])
