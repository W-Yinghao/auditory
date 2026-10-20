"""Real-source bindings for the bounded ALN3.5 paired analyses.

No encoder fitting or inference. Query identities come from physical cached
segment/anchor indices, or retained original private epoch indices. These full
provenance rows are private execution artifacts, not a raw-event release.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import numpy as np

from auditory_alignment_v3 import core, bc_interim

ROOT = Path(core.REPO)
BASE = Path(core.OUT)
PACKAGE = ROOT / 'AUDITORY_ALN3_SERVER_PACKAGE_v3_5_20261018'
PRIVATE = BASE / 'aln35/science'
RESULTS = ROOT / 'results/auditory_alignment_v3/aln35/science'
BASELINE = '5ef4a60bf77eeaeab5582c2cb076077c0b15bd11'


@lru_cache(maxsize=None)
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('x') as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=2)
        f.write('\n')


def native_arm(row):
    s = row['spec']
    if s.get('objective') != 'NCE': return None
    if row['family_id'] == 'ALN32_LOCAL_SUPPORT' and s.get('variant') == 'local_aligned1000':
        return 'LOCAL'
    if (row['family_id'] == 'ALN32_TRUE_FULL' and s.get('architecture') == 'cbramod'
            and s.get('recipe') == 'full_onestep_v1' and float(s.get('lr_backbone', -1)) == 3e-4):
        return {'pretrained_full': 'CB_PRE', 'random_full': 'CB_RANDOM'}.get(s.get('adaptation'))
    return None


def public_queries(arrays, pid, dataset, content_fold, fs, anchors=True):
    """Stable physical cache coordinates, independent of arm/unit identifiers."""
    index = np.flatnonzero((arrays['role'] == 'test') & (arrays['person'] == pid))
    segments = arrays['segment'][index]
    offsets = arrays['anchor_offsets']
    nt = len(offsets)
    assert len(index) and len(index) % nt == 0
    selected = np.unique(segments)
    output = []
    for segment in selected:
        positions = index[segments == segment]
        assert len(positions) == nt
        start = int(arrays['source_segment_e0'][segment])
        prefix = f'{dataset}/cf{content_fold}/{pid}/fs{fs}/e0={start}'
        output.extend([prefix + f'/anchor={int(a)}' for a in offsets] if anchors else [prefix + '/segment5s'])
    assert len(output) == len(set(output))
    return output


class Binding:
    def __init__(self):
        from auditory_alignment_v3.prior33 import run_target as RT, views as V
        from auditory_alignment import data
        self.rows = core.load_rows() + [json.loads(x) for x in (BASE / 'plan_ext.jsonl').read_text().splitlines()]
        self.row_by_id = {r['experiment_id']: r for r in self.rows}
        prior = next(r for r in self.rows if r['family_id'] == 'ALN32_PUBLIC_AUDIO_PRIOR_TARGET')
        self.manifest = RT.open_manifest(prior)
        self.manifest_sha = self.manifest.sha256
        self.entities = bc_interim.load_manifest()
        self.parts = {}
        self.expected = {}
        self.sessions = defaultdict(list)
        self.sources = {}
        self.missing = []
        for ds in ('dtu', 'fau', 'federici'):
            table, _ = V.cohort_table(self.manifest, ds)
            self.parts[ds] = {str(p['participant']): p for p in table['participants']}
            self.expected[ds] = {}
            for pid, p in self.parts[ds].items():
                ident, group, human = self.identity(ds, pid)
                if human and not p.get('dev') and not p.get('test_only'):
                    self.expected[ds][ident] = group
                    self.sessions[(ds, ident)].append(pid)
        # This is the original production loader, not an inferred cohort from
        # whichever result files happen to have arrived.
        self.kids = data.load_private()
        self.kid_by_id = {k['id']: k for k in self.kids}
        self.parts['private_bdf'] = self.kid_by_id
        self.expected['private_bdf'] = {k['id']: k['group'] for k in self.kids}
        self.private_query = {}
        self.private_trial_bindings = {}
        self._bind_private_trials()
        self.native_cache = {}
        self.prior_cache = {}
        self.plan_hashes = {}
        self._donor = {}

    def identity(self, ds, pid):
        if ds == 'federici':
            ident, group, kind = self.entities[pid]
            return ident, group, kind == 'human'
        p = self.parts[ds][pid]
        return pid, p['group'], not p.get('test_only', False)

    def _bind_private_trials(self):
        from auditory_c3.private_mi import P
        from auditory_c3.private_mi2 import hist_codes
        for kid in self.kids:
            path = Path(P) / 'auditory_gx/GX_stage_001/epochs' / (kid['rid'] + '.npz')
            with np.load(path, allow_pickle=False) as z:
                accepted = np.flatnonzero(z['accepted'].astype(bool))
                hist = hist_codes(z['previous_code'][accepted], z['previous_run_length'][accepted])['since_last_deviant']
                original = accepted[hist >= 0]
                assert np.array_equal(z['y'][original], kid['y'])
                assert np.array_equal(z['block_id'][original], kid['block'])
                assert np.array_equal(hist[hist >= 0], kid['bin'])
            queries = [f"private_bdf/{kid['id']}/original_epoch={int(i)}" for i in original]
            assert len(queries) == len(kid['y']) and len(queries) == len(set(queries))
            self.private_query[kid['id']] = queries
            self.private_trial_bindings[kid['id']] = {
                'raw_source_sha256': sha(path), 'original_epoch_indices_sha256': digest(original.tolist()),
                'retained_trial_count': len(queries), 'query_ids_sha256': digest(queries),
                'loader': 'hc.load_children: accepted then nonnegative since_last_deviant history code',
                'loader_sha256': sha(ROOT / 'auditory_c3/c3dl/hc.py'),
                'history_code_sha256': sha(ROOT / 'auditory_c3/private_mi2.py'),
            }

    def source(self, row, expected_sha=None):
        path = BASE / 'units' / (row['experiment_id'] + '.json')
        if not path.exists(): raise FileNotFoundError(path)
        h = sha(path)
        if expected_sha is not None: assert h == expected_sha, ('source record drift', path)
        rec = read(path)
        assert rec['status'] == 'complete' and rec['row'] == row and not rec.get('truncated')
        self.sources[str(path.relative_to(ROOT))] = h
        return rec, path, h

    def _donor_ids(self, row):
        from auditory_alignment_v3.prior33 import sampler as S, views as V, target_train as TT
        if TT.arm_of(row)[0] == 'S': return [], []
        key = row['dataset'], row['spec']['block']
        if key not in self._donor:
            ds = self.manifest['donor_sets'][key[0]][S.BLOCKS[key[1]]]
            S.check_leave_target_out(key[0], S.BLOCKS[key[1]], ds)
            idx = V.manifest_index(self.manifest)
            fit = set()
            for s in ds['strata']:
                cohort = S.coh_of(s)
                pool = self.manifest['pools']['core'][cohort]
                excluded = set(S._excluded(ds, s))
                seg = idx.seg[cohort]
                eligible = [int(i) for i in pool if int(seg['presentation'][int(i)]) not in excluded]
                fit.update(f"donor/{cohort}/{seg['participant'][i]}" for i in eligible)
            sets = S.selection_sets(self.manifest)
            dev = {f"donor/sparrkulee/{idx.seg['sparrkulee']['participant'][int(i)]}"
                   for i in sets['dev']['queries'].rows}
            # Donor-side ridge selection also fits on its registered fit subset.
            fit.update(f"donor/sparrkulee/{idx.seg['sparrkulee']['participant'][int(i)]}"
                       for i in sets['fit'].rows)
            self._donor[key] = sorted(fit), sorted(dev)
        return self._donor[key]

    def populations(self, row, prior=False):
        ds, sf = row['dataset'], row['subject_fold']
        fit = set()
        for pid, p in self.parts[ds].items():
            ident, _, human = self.identity(ds, pid)
            if human and not p.get('test_only', False) and (p.get('dev', False) or p['fold'] != sf): fit.add(ident)
        select = set(fit)
        if prior:
            extra_fit, extra_select = self._donor_ids(row)
            fit.update(extra_fit); select.update(extra_select)
        return sorted(fit), sorted(select)

    def load_lane(self, name):
        from auditory_alignment_v3.aln34 import content_time as T, prior_science as Q, private_current_time_v2 as P
        mod = {'content_time_v1': T, 'prior_science_v1': Q, 'private_current_time_v2': P}[name]
        plan = read(mod.PLAN)
        mod.verify(plan)
        self.plan_hashes[name] = sha(mod.PLAN)
        return plan

    def lane_record(self, lane, unit):
        path = BASE / 'aln34' / lane / 'units' / (unit['id'] + '.json')
        if not path.exists():
            self.missing.append({'source': lane, 'unit': unit['id'], 'reason': 'record_missing'})
            return None
        rec = read(path)
        assert rec['status'] == 'complete' and not rec.get('probe')
        assert rec['plan_sha256'] == self.plan_hashes[lane]
        assert rec['unit']['source'] == unit['source']
        if lane == 'prior_science_v1':
            bp = BASE / 'aln34' / lane / 'bindings' / (unit['id'] + '.json')
            assert sha(bp) == rec['binding_sha256'] and read(bp) == rec['unit']
            self.sources[str(bp.relative_to(ROOT))] = sha(bp)
        else: assert rec['unit'] == unit
        self.source(unit['source'], rec['unit']['record_sha256'])
        self.sources[str(path.relative_to(ROOT))] = sha(path)
        return rec, path

    def cache(self, lane, plan, rec):
        uid = rec['unit'].get('previous_id', rec['unit']['id'])
        store = Path(plan.get('store', '<private checkpoint storage>/auditory_alignment_v3/aln34_private_current_time_v1'))
        path = store / 'cache' / uid
        meta = read(path / 'meta.json')
        source_meta = rec.get('metadata', rec.get('cache_metadata'))
        assert meta == source_meta
        assert sha(path / 'arrays.npz') == meta['array_sha256']
        self.sources[str(path / 'meta.json')] = sha(path / 'meta.json')
        self.sources[str(path / 'arrays.npz')] = meta['array_sha256']
        return path, meta

    def observation(self, row, path, ident, group, arm, window, metric, unit, value,
                    queries, *, prior=False, source_lane='', extra=None):
        assert value is not None and math.isfinite(float(value)) and queries
        fit, select = self.populations(row, prior)
        assert ident not in fit and ident not in select, ('held-out identity in source side', ident)
        cf = int(row.get('content_fold') or 0)
        ds = row['dataset']
        return {'dataset': ds, 'identity': ident, 'group': group,
                'fold': 'evaluation' if ds == 'private_bdf' else f'content_{cf}',
                'seed': int(row['seed']), 'arm': arm, 'window': window, 'metric': metric,
                'unit': unit, 'value': float(value), 'query_set_id': digest(queries), 'analysis_role': 'outer_test',
                'provenance': {'query_ids': queries, 'support_ids': [], 'population_fit_identities': fit,
                               'selection_identities': select, 'outer_fold': f"subject_{row['subject_fold']}",
                               'source_record': str(path.relative_to(ROOT)), 'source_sha256': sha(path),
                               'source_fold_ids': [f'content_{cf}' if ds != 'private_bdf' else 'evaluation'],
                               'source_seed_ids': [int(row['seed'])]},
                'metadata': {'source_commit': BASELINE, 'source_unit_id': path.stem,
                             'source_plan_sha256': self.plan_hashes.get(source_lane, sha(BASE / 'plan_ext.jsonl')),
                             'subject_fold': row['subject_fold'], 'content_fold': cf,
                             'representation_contract_id': 'aln33_env64_125ms_v1' if prior else 'native_aligned1000',
                             'readout_contract_id': source_lane, 'target_training_selection_level': 'same-source-person early-stopping content/blocks',
                             'query_definition': 'original retained epoch indices' if ds == 'private_bdf' else 'physical cached EEG bank segment start and fixed sound-anchor offsets',
                             'external_original_FM_pretraining_identity_audit': 'not available in these source records; not asserted',
                             **(extra or {})}}


def expected_for(family, roster):
    groups = {t['group'] for c in family['contrasts'] for t in c['terms']}
    return {g: sorted(i for i, level in roster.items() if level in family.get('group_sets', {}).get(g, [g]))
            for g in sorted(groups)}
