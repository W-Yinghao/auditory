"""Read-only source audit, environment capture and feature/scope alignment."""
import inspect
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import scipy
import torch

from .provenance import ROOT, digest, write_json, finish


def run(config, registry, site, dest, public, report):
    planpath = ROOT / registry['legacy_plan']
    splitpath = ROOT / registry['legacy_splits']
    for path, expected in ((planpath, registry['legacy_plan_sha256']), (splitpath, registry['legacy_split_sha256'])):
        if digest(path) != expected:
            raise ValueError('LEGACY_SOURCE_HASH_MISMATCH')
    plan = json.loads(planpath.read_text())
    folds = json.loads(splitpath.read_text())
    support = pd.read_parquet(splitpath.parent / 'support.parquet')
    publication = Path(site['publication_root'])
    manifest = json.loads((publication / 'release/manifest.json').read_text())
    source_files = set(ROOT / p for p in registry['required_documents'])
    source_files.update((planpath, splitpath, splitpath.parent / 'support.parquet', publication / 'PUBLICATION.md', publication / 'release/manifest.json'))
    source_files.update((ROOT / 'auditory5').rglob('*.py'))
    source_files.update((ROOT / registry['legacy_screen']).rglob('*'))
    deltas = []
    for row in manifest['files']:
        p = ROOT / row['path']
        if row.get('source_sha256') and p.is_file():
            changed = digest(p) != row['source_sha256']
            deltas.append(dict(path=row['path'], changed_from_published_source=changed))
            if changed and row['path'].startswith(('auditory5/', 'configs/auditory5')):
                raise ValueError('LEGACY_IMPLEMENTATION_DELTA')
    pd.DataFrame(deltas).to_csv(public / 'snapshot_delta.csv', index=False)
    audits = []
    for task in plan['tasks']:
        folder = planpath.parent / 'outputs' / task['name']
        completion = json.loads((folder / 'completion.json').read_text())
        if completion['status'] != 'PASS' or completion['plan_hash'] != digest(planpath):
            raise ValueError('LEGACY_TASK_INCOMPLETE')
        row = pd.read_parquet(folder / 'feature_rows.parquet')
        with np.load(folder / 'features.npz', allow_pickle=False) as z:
            if not np.array_equal(row.trial_id.to_numpy(str), z['trial_ids'].astype(str)) or not row.trial_id.is_unique:
                raise ValueError('FEATURE_TRIAL_ALIGNMENT')
            if not np.array_equal(row.split_group_id.to_numpy(str), z['groups'].astype(str)):
                raise ValueError('FEATURE_GROUP_ALIGNMENT')
            if not np.array_equal(row.stimulus_local_id.to_numpy(int), z['y']):
                raise ValueError('FEATURE_LABEL_ALIGNMENT')
            shapes = {w: list(z[w].shape) for w in ('post', 'pre')}
            if any(not np.isfinite(z[w]).all() for w in ('post', 'pre')):
                raise ValueError('NONFINITE_LEGACY_FEATURES')
        fitted = set(task['fit_groups'])
        eligible = set(support.loc[support.general if task['branch'] == 'all' else support.C, 'split_group_id'])
        actual = fitted & eligible
        if task['mode'] != 'L0':
            ckpt = torch.load(folder / 'encoder.pt', map_location='cpu', weights_only=False)
            actual = set(ckpt['scope']['train_groups'])
            if actual != fitted & eligible or set(ckpt['scaler']['fit_groups']) != actual:
                raise ValueError('ENCODER_ACTUAL_FIT_SCOPE_MISMATCH')
            if completion['encoder_fit_scope_hash'] != ckpt['scope_hash']:
                raise ValueError('ENCODER_SCOPE_HASH_MISMATCH')
        validation, test = set(task['validation_groups']), set(task['test_groups'])
        if actual & (validation | test) or validation & test:
            raise ValueError('ENCODER_VALIDATION_TEST_LEAKAGE')
        audits.append(dict(task=task['name'], mode=task['mode'], branch=task['branch'],
            stage=task['stage'], outer_fold=task['outer_fold'], inner_fold=task['inner_fold'],
            fit_groups=sorted(actual), validation_groups=sorted(validation), test_groups=sorted(test),
            feature_shapes=shapes, n_trials=len(row), status='PASS'))
        source_files.update(p for p in folder.iterdir() if p.is_file())
    write_json(dest / 'feature_scope_registry.json', audits)
    pd.DataFrame([{k:v for k,v in a.items() if k not in ('fit_groups','validation_groups','test_groups','feature_shapes')} |
                  {k:len(a[k]) for k in ('fit_groups','validation_groups','test_groups')} for a in audits]).to_csv(public / 'feature_scope_counts.csv', index=False)
    exports = ROOT / 'private/auditory5_v1/data' / plan['export_run']
    source_files.update(p for p in exports.rglob('*') if p.is_file())
    for rel in ('private/auditory5_v1/routes/E0_native_003', 'private/auditory5_v1/data/mff_e0_export_001',
                'results/phase3_metadata_addendum_001'):
        source_files.update(p for p in (ROOT / rel).rglob('*') if p.is_file())
    schema = []
    for bank in ('P1_CAUSAL20','P2_SPATIAL_SPLIT'):
        files = sorted((exports / bank).glob('*/events.parquet'))
        if not files: raise ValueError('MISSING_EXPORT_BANK')
        event = pd.read_parquet(files[0])
        summary = json.loads((files[0].parent / 'summary.json').read_text())
        write_json(dest / (bank + '_example_schema.json'), dict(columns={c:str(t) for c,t in event.dtypes.items()}, summary=summary))
        schema.append(dict(bank=bank, records=len(files), event_columns=list(event.columns)))
    write_json(dest / 'export_schema.json', schema)
    from sklearn.neural_network import _multilayer_perceptron as mlp
    source = inspect.getsource(mlp)
    (dest / 'installed_sklearn_multilayer_perceptron.py.txt').write_text(source)
    env = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
               sklearn=sklearn.__version__, torch=torch.__version__, cuda_build=torch.version.cuda,
               cuda_available_in_this_allocation=torch.cuda.is_available(), torch_build=torch.__config__.show())
    write_json(dest / 'environment.json', env)
    for command, name in ((['sinfo','-h','-o','%P %G %c %m %l'], 'slurm_partitions.txt'),):
        p = subprocess.run(command, capture_output=True, text=True)
        (dest / name).write_text(p.stdout + p.stderr)
    hashes = [{'path':str(p), 'bytes':p.stat().st_size, 'sha256':digest(p)} for p in sorted(source_files) if p.is_file()]
    write_json(dest / 'legacy_input_hashes.json', hashes)
    coverage = []
    for fold in folds['folds']:
        inner = fold['D_inner_fold_by_group']
        coverage.append(dict(outer_fold=fold.get('outer_fold',fold.get('fold')), outer_training_groups=len(fold['train_groups']),
                             inner_validation_groups=len(inner), groups_without_inner_validation=len(set(fold['train_groups'])-set(inner))))
    pd.DataFrame(coverage).to_csv(public / 'inner_coverage.csv', index=False)
    (report / 'SOURCE_AND_SCOPE_AUDIT.md').write_text(
        '# v2 source and scope preflight\n\nLegacy 90-task feature rows, labels, trial IDs and actual checkpoint/scaler fit scopes verified. '
        'The publication policy comes from the separate published checkout; publication source hashes account for editorial prefixes. '
        'Raw EEG was not rehashed in full. The private hash inventory covers all reused export banks, representation task artifacts and E0 inputs.\n\n'
        'D-inner validation covers only a subset of outer-training identity groups. New-route calibration must not silently assign uncovered groups to validation. '
        'No new encoder or readout has been fitted by this stage.\n')
    return finish(dest, public, dict(status='PASS', tasks_verified=len(audits), legacy_files_hashed=len(hashes),
                 legacy_bytes_hashed=sum(r['bytes'] for r in hashes), source_deltas=sum(d['changed_from_published_source'] for d in deltas),
                 new_encoder_fits=0, new_readout_fits=0, sklearn_version=sklearn.__version__, scope='implementation and input audit only'))
