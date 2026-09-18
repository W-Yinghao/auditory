"""Corrected-cohort nested retraining. Every command requires a Slurm job."""
import argparse
import json
import os
import pickle
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml

from auditory5.provenance import ROOT, digest, object_hash, require_slurm, write_json

CONFIG = ROOT / 'configs/auditory_retrain_v1.json'


def settings():
    return json.loads(CONFIG.read_text())


def gpu_guard(spec):
    if not torch.cuda.is_available():
        raise RuntimeError('A supported GPU allocation is required')
    name = torch.cuda.get_device_name(0)
    if 'P100' in name or not any(token in name for token in spec['allowed_GPU_names']):
        raise RuntimeError('Unsupported GPU: ' + name)
    return name


def probe(args):
    from auditory5.models import SmallEEGCNN_v1
    spec = settings()
    name = gpu_guard(spec)
    model = SmallEEGCNN_v1(20, n_classes=2).cuda()
    x = torch.randn(16, 20, 100, device='cuda')
    z, logits = model(x, return_logits=True)
    loss = torch.nn.functional.cross_entropy(logits, torch.arange(16, device='cuda') % 2)
    loss.backward()
    torch.cuda.synchronize()
    assert torch.isfinite(z).all() and torch.isfinite(loss)
    report = dict(status='PASS', job_id=os.environ['SLURM_JOB_ID'], gpu=name,
                  torch_version=str(torch.__version__), cuda_version=torch.version.cuda)
    write_json(ROOT / spec['aggregates_relative'] / args.run / 'validation.json', report)
    print(json.dumps(report), flush=True)


def complete(row):
    fields = ['clinical_age_months', 'duration_months', 'better_unaided_pta', 'MUSS']
    numbers = [pd.to_numeric(row[k], errors='coerce') for k in fields]
    return bool(row.pta_status == 'linked_complete_unaided' and np.isfinite(numbers).all()
                and numbers[0] >= 0 and numbers[1] >= 0 and 0 <= numbers[3] <= 100
                and str(row.strong_unique_link).lower() == 'true'
                and str(row.eligible_measurement_identity_index).lower() == 'true')


def prepare(args):
    from auditory5.splitting import balanced_component_folds, record_support
    spec = settings()
    base = ROOT / spec['private_relative']
    dest = base / 'jobs' / spec['plan_run']
    dest.mkdir(parents=True, exist_ok=False)
    config = yaml.safe_load((ROOT / spec['base_config']).read_text())
    for key in ['private_relative', 'aggregates_relative', 'reports_relative']:
        config['paths'][key] = spec[key]
    config['corrected_retraining'] = spec
    config['resources']['gpu_partition'] = 'H100,A100,L40S'
    old_manifest = ROOT / spec['old_manifest']
    old_split = ROOT / spec['old_splits']
    old = json.loads((old_split / 'folds.json').read_text())
    corrected = pd.read_csv(ROOT / spec['corrected_covariates']).set_index('recording_id')
    assert corrected.index.is_unique and len(corrected) == 57
    clinical = pd.read_parquet(old_manifest / 'clinical_index.parquet').set_index('record_id')
    assert set(clinical.index) == set(corrected.index)
    for rid, row in corrected.iterrows():
        # PTA and completeness alone change; the registered endpoint and covariates do not.
        for old_key, new_key in [('age_months', 'clinical_age_months'), ('MUSS_source_percentage', 'MUSS')]:
            assert np.isclose(clinical.loc[rid, old_key], row[new_key], equal_nan=True)
        duration = np.log1p(row.duration_months) if pd.notna(row.duration_months) and row.duration_months >= 0 else np.nan
        assert np.isclose(clinical.loc[rid, 'log1p_device_duration_months'], duration, equal_nan=True)
        assert clinical.loc[rid, 'candidate_id'] == row.participant_id
        clinical.loc[rid, 'better_ear_4freq_source_units'] = row.better_unaided_pta
        clinical.loc[rid, 'clinical_complete'] = complete(row)
    manifest = base / 'data' / spec['manifest_run']
    manifest.mkdir(parents=True, exist_ok=False)
    for name in ['records.parquet', 'identity_graph.json']:
        shutil.copyfile(old_manifest / name, manifest / name)
    clinical.reset_index().to_parquet(manifest / 'clinical_index.parquet', index=False)
    exports = ROOT / 'private/auditory5_v1/data' / old['export_run']
    (base / 'data' / old['export_run']).symlink_to(exports, target_is_directory=True)
    old_support = pd.read_parquet(old_split / 'support.parquet')
    support_rows, source_hashes, summary_hashes = [], {}, {}
    for row in old_support.to_dict('records'):
        rid = row['record_id']
        events = {}
        for bank in ['P1_CAUSAL20', 'P2_SPATIAL_SPLIT']:
            folder = exports / bank / rid
            summary_path = folder / 'summary.json'
            summary = json.loads(summary_path.read_text())
            summary_hash = digest(summary_path)
            assert summary_hash == old['input_hashes'][bank + '/' + rid]
            source_hashes[str(summary_path)] = summary_hash
            summary_hashes[bank + '/' + rid] = summary_hash
            for name, expected in summary['output_sha256'].items():
                path = folder / name
                actual = digest(path)
                if actual != expected:
                    raise ValueError('EEG export checksum mismatch')
                source_hashes[str(path)] = actual
            events[bank] = pd.read_parquet(folder / 'events.parquet')
            assert events[bank].trial_id.is_unique
            assert events[bank].split_group_id.eq(row['split_group_id']).all()
        cc = rid in clinical.index and bool(clinical.loc[rid, 'clinical_complete'])
        rebuilt = {k: row[k] for k in ['record_id', 'candidate_id', 'split_group_id']}
        rebuilt.update(record_support(events['P1_CAUSAL20'], events['P2_SPATIAL_SPLIT'], cc))
        support_rows.append(rebuilt)
    support = pd.DataFrame(support_rows)
    expected = pd.read_parquet(ROOT / spec['corrected_support'])
    pd.testing.assert_frame_equal(support.sort_values('record_id').reset_index(drop=True),
                                  expected.sort_values('record_id').reset_index(drop=True), check_dtype=False)
    d_ids = set(support.loc[support.D, 'split_group_id'])
    assert len(d_ids) == spec['expected_D_groups']
    c = clinical[clinical.split_group_id.isin(d_ids)]
    assert len(c) == len(d_ids) and c.split_group_id.is_unique and c.clinical_complete.all()
    assert np.isfinite(c[['age_months', 'log1p_device_duration_months', 'better_ear_4freq_source_units', 'MUSS_source_percentage']]).all().all()
    eligible = support[support[['general', 'A', 'B', 'C', 'D']].any(axis=1)]
    outer = balanced_component_folds(eligible, spec['outer_folds'], spec['split_seed'])
    assert len(outer) == spec['expected_outer_groups']
    audit = json.loads((ROOT / spec['corrected_support']).with_name('folds_corrected.json').read_text())
    assert outer == audit['corrected_assignment']
    changed = sum(outer[g] != old['outer_fold_by_group'][g] for g in outer)
    assert changed == spec['expected_changed_outer_assignments']
    folds, tasks = [], []
    fit_eligible = set(support.loc[support.general, 'split_group_id'])
    for of in range(spec['outer_folds']):
        test = sorted(g for g, f in outer.items() if f == of)
        train = sorted(set(outer) - set(test))
        inner = balanced_component_folds(eligible[eligible.D & eligible.split_group_id.isin(train)], 3, spec['split_seed'] + of + 1)
        folds.append(dict(outer_fold=of, train_groups=train, test_groups=test, D_inner_fold_by_group=inner,
                          D_encoder_policy='exclude outer-test and clinical-inner-validation groups'))
        for inner_fold in [None, 0, 1, 2]:
            valid = [] if inner_fold is None else sorted(g for g, f in inner.items() if f == inner_fold)
            fit = sorted(set(train) - set(valid))
            effective = sorted(set(fit) & fit_eligible)
            assert not (set(effective) & (set(test) | set(valid))) and effective
            modes = spec['modes'] if inner_fold is None else ['R_SUP', 'R_SIM']
            for mode in modes:
                name = f'outer{of}_all_{mode}' if inner_fold is None else f'D_outer{of}_inner{inner_fold}_{mode}'
                tasks.append(dict(name=name, stage='outer' if inner_fold is None else 'D_inner',
                                  outer_fold=of, inner_fold=inner_fold, branch='all', mode=mode, seed=spec['seed'],
                                  fit_groups=fit, effective_fit_groups=effective, validation_groups=valid,
                                  test_groups=test, resource='cpu' if mode == 'L0' else 'gpu', index=len(tasks)))
    assert len(tasks) == 45 and sum(t['resource'] == 'gpu' for t in tasks) == 40
    splitdir = base / 'splits' / spec['split_run']
    splitdir.mkdir(parents=True, exist_ok=False)
    support.to_parquet(splitdir / 'support.parquet', index=False)
    write_json(splitdir / 'folds.json', dict(outer_fold_by_group=outer, folds=folds, fold_count=5,
               export_run=old['export_run'], manifest=spec['manifest_run'], input_hashes=summary_hashes,
               seed=spec['split_seed'], outcome_blind=True))
    snapshot = dest / 'source'
    for package in ['auditory5', 'auditory_retrain']:
        shutil.copytree(ROOT / package, snapshot / package, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(ROOT / 'tests/auditory5', snapshot / 'tests/auditory5', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copyfile(CONFIG, snapshot / 'config.json')
    shutil.copyfile(ROOT / 'docs/auditory_retrain/PROTOCOL_v1.md', snapshot / 'PROTOCOL_v1.md')
    tests = ['contracts', 'splitting', 'training', 'probes', 'route_d', 'route_d_controls']
    env = dict(os.environ, PYTHONPATH=str(snapshot))
    with (dest / 'tests.log').open('x') as log:
        result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'] +
                                [f'tests/auditory5/test_{name}.py' for name in tests],
                                cwd=snapshot, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Contract tests failed; see private tests.log')
    hashes = {str(p.relative_to(snapshot)): digest(p) for p in sorted(snapshot.rglob('*.py'))}
    inputs = {str(p): digest(p) for p in [CONFIG, ROOT / spec['base_config'],
              ROOT / 'docs/auditory_retrain/PROTOCOL_v1.md', ROOT / spec['corrected_covariates'],
              ROOT / spec['corrected_support'], manifest / 'clinical_index.parquet', manifest / 'records.parquet',
              manifest / 'identity_graph.json', splitdir / 'support.parquet', splitdir / 'folds.json']}
    write_json(dest / 'verified_EEG_inputs.json', source_hashes)
    # Worker verifies size/mtime plus per-task event/array checksums before loading.
    stamps = {path: [Path(path).stat().st_size, Path(path).stat().st_mtime_ns] for path in source_hashes}
    plan = dict(version=spec['version'], tasks=tasks, config=config, config_hash=object_hash(config),
                split_run=spec['split_run'], split_hash=digest(splitdir / 'folds.json'), export_run=old['export_run'],
                source_snapshot=str(snapshot), code_hashes=hashes, input_hashes=inputs, EEG_file_stamps=stamps,
                EEG_hash_manifest_hash=digest(dest / 'verified_EEG_inputs.json'), learned_encoder_jobs=40, CPU_jobs=5,
                tests_status='PASS', tests_log_hash=digest(dest / 'tests.log'), preparation_job=os.environ['SLURM_JOB_ID'])
    write_json(dest / 'plan.json', plan)
    report = dict(status='PASS', D_groups=len(d_ids), outer_groups=len(outer), changed_outer_assignments=changed,
                  learned_encoder_jobs=40, fixed_representation_jobs=5, tests_status='PASS',
                  verified_EEG_files=len(source_hashes), plan_hash=digest(dest / 'plan.json'),
                  scientific_early_stopping=False, job_id=os.environ['SLURM_JOB_ID'])
    write_json(ROOT / spec['aggregates_relative'] / 'preparation_001' / 'validation.json', report)
    print(json.dumps(report), flush=True)


def frozen_plan(args):
    planpath = Path(args.plan).resolve()
    plan = json.loads(planpath.read_text())
    snapshot = Path(plan['source_snapshot'])
    if Path(__file__).resolve() != snapshot / 'auditory_retrain/run.py':
        env = dict(os.environ, AUDITORY5_ROOT=str(ROOT), PYTHONPATH=str(snapshot))
        os.chdir(snapshot)
        os.execve(sys.executable, [sys.executable, '-m', 'auditory_retrain.run'] + sys.argv[1:], env)
    assert object_hash(plan['config']) == plan['config_hash'] and plan['tests_status'] == 'PASS'
    for rel, expected in plan['code_hashes'].items():
        assert digest(snapshot / rel) == expected, 'Frozen code mutation'
    for path, expected in plan['input_hashes'].items():
        assert digest(path) == expected, 'Input metadata mutation'
    assert digest(planpath.parent / 'verified_EEG_inputs.json') == plan['EEG_hash_manifest_hash']
    for path, stamp in plan['EEG_file_stamps'].items():
        s = Path(path).stat()
        assert [s.st_size, s.st_mtime_ns] == stamp, 'EEG file changed since full checksum validation'
    return planpath, plan


def task_run(planpath, plan, task):
    from auditory5.contracts import FitScope
    from auditory5.datasets import load_dataset
    from auditory5.probes import fit_probe, bin_20ms
    from auditory5.metrics import classification_metrics
    from auditory5.training import fit_supervised, fit_simclr, FittedEncoder
    config = plan['config']
    spec = config['corrected_retraining']
    base = ROOT / config['paths']['private_relative']
    dest = planpath.parent / 'outputs' / task['name']
    if (dest / 'completion.json').exists():
        c = json.loads((dest / 'completion.json').read_text())
        assert c['status'] == 'PASS' and c['plan_hash'] == digest(planpath)
        for name, expected in c['output_hashes'].items():
            assert digest(dest / name) == expected
        return c
    gpu = gpu_guard(spec) if task['resource'] == 'gpu' else None
    dest.mkdir(parents=True, exist_ok=True)
    stored = dict(task, job_id=os.environ['SLURM_JOB_ID'], plan_hash=digest(planpath))
    if (dest / 'task.json').exists():
        previous = json.loads((dest / 'task.json').read_text())
        assert all(previous[k] == v for k, v in task.items()) and previous['plan_hash'] == digest(planpath)
    else:
        write_json(dest / 'task.json', stored)
    started = time.monotonic()
    support = pd.read_parquet(base / 'splits' / plan['split_run'] / 'support.parquet')
    support['representation'] = support[['general', 'A', 'B', 'D']].any(axis=1)
    data = load_dataset(plan['export_run'], support, route='representation', window='post')
    pre = load_dataset(plan['export_run'], support, route='representation', window='pre')
    assert np.array_equal(data.trial_ids, pre.trial_ids) and np.array_equal(data.y, pre.y)
    fit_eligible = set(support.loc[support.general, 'split_group_id'])
    fit_groups = sorted(set(task['fit_groups']) & fit_eligible)
    assert fit_groups == task['effective_fit_groups']
    scope = FitScope(tuple(fit_groups), tuple(task['validation_groups']), tuple(task['test_groups']))
    training = data.subset_groups(fit_groups)
    assert set(training.groups) == set(fit_groups)
    mode = task['mode']
    encoder = None
    if gpu:
        torch.cuda.reset_peak_memory_stats()
        common = dict(seed=task['seed'], config=config, device='cuda',
                      record_ids=training.record_ids, onset_seconds=training.onset_seconds)
        if (dest / 'encoder.pt').exists():
            encoder = FittedEncoder.load(dest / 'encoder.pt', device='cuda')
            assert encoder.scope == scope and encoder.metadata['config_hash'] == plan['config_hash'] and encoder.mode == mode
        else:
            print(json.dumps(dict(task=task['name'], stage='training', gpu=gpu, job_id=os.environ['SLURM_JOB_ID'])), flush=True)
            if mode == 'R_SUP':
                encoder = fit_supervised(training.X, training.y, training.groups, scope, **spec['supervised'], **common)
            elif mode == 'R_SIM':
                encoder = fit_simclr(training.X, training.groups, scope, **spec['simclr'], **common)
            else:
                raise ValueError('Invalid learned mode')
            encoder.save(dest / 'encoder.pt')
            write_json(dest / 'training_receipt.json', dict(status='PASS', gpu_name=gpu, job_id=os.environ['SLURM_JOB_ID'],
                       elapsed_seconds=time.monotonic()-started, encoder_sha256=digest(dest / 'encoder.pt'),
                       scope_hash=scope.hash, plan_hash=digest(planpath)))
    features, metrics, probe_metadata = {}, {}, {}
    trainmask = np.isin(data.groups, fit_groups)
    testmask = np.isin(data.groups, task['test_groups']) & np.isin(data.groups, list(fit_eligible))
    if (dest / 'features.npz').exists():
        with np.load(dest / 'features.npz', allow_pickle=False) as saved:
            assert np.array_equal(saved['trial_ids'], data.trial_ids)
            features = {w: saved[w] for w in ['post', 'pre']}
    for window, view in [('post', data), ('pre', pre)]:
        z = features.get(window)
        if z is None:
            z = bin_20ms(view.X) if encoder is None else encoder.transform(view.X)
            features[window] = z.astype('float32')
        path = dest / ('probe_' + window + '.pkl')
        if path.exists():
            with path.open('rb') as f:
                probe = pickle.load(f)
            assert probe.fit_scopes['scope_hash'] == scope.hash
        else:
            probe = fit_probe(z[trainmask], data.y[trainmask], data.groups[trainmask], scope,
                              seed=task['seed'], pca_max_dim=32 if mode == 'L0' else None)
            with path.open('xb') as f:
                pickle.dump(probe, f)
        probabilities = probe.predict(z[testmask])
        rows = data.rows.loc[testmask, ['trial_id', 'record_id', 'candidate_id', 'split_group_id', 'stimulus_local_id']].copy()
        for calibration, prob in probabilities.items():
            rows[calibration + '_probability_class1'] = prob[:, 1]
            metrics[window + '_' + calibration] = classification_metrics(data.y[testmask], prob, data.groups[testmask], data.trial_ids[testmask])
        target = dest / ('stimulus_oof_' + window + '.parquet')
        if not target.exists():
            rows.to_parquet(target, index=False)
        probe_metadata[window] = dict(selected_C=probe.selected_C, temperature=probe.temperature, fit_scopes=probe.fit_scopes)
    if not (dest / 'features.npz').exists():
        np.savez_compressed(dest / 'features.npz', **features, trial_ids=data.trial_ids, groups=data.groups, y=data.y)
    if not (dest / 'feature_rows.parquet').exists():
        data.rows.to_parquet(dest / 'feature_rows.parquet', index=False)
    if not (dest / 'probe_metadata.json').exists():
        write_json(dest / 'probe_metadata.json', probe_metadata)
    summary = dict(status='PASS', task=task['name'], mode=mode, branch='all', stage=task['stage'],
                   outer_fold=task['outer_fold'], inner_fold=task['inner_fold'], train_groups=len(fit_groups),
                   test_groups=int(len(np.unique(data.groups[testmask]))), train_trials=len(training.y), test_trials=int(testmask.sum()),
                   metrics=metrics, elapsed_seconds=time.monotonic()-started, device='cuda' if gpu else 'cpu', gpu_name=gpu,
                   cuda_peak_allocated_bytes=int(torch.cuda.max_memory_allocated()) if gpu else 0,
                   job_id=os.environ['SLURM_JOB_ID'], encoder_fit_scope_hash=scope.hash, plan_hash=digest(planpath),
                   output_hashes={p.name: digest(p) for p in dest.iterdir() if p.is_file()})
    write_json(dest / 'completion.json', summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ['metrics', 'output_hashes']}), flush=True)
    return summary


def worker(args):
    planpath, plan = frozen_plan(args)
    tasks = [t for t in plan['tasks'] if t['resource'] == args.resource]
    if args.resource == 'gpu':
        tasks = [t for i, t in enumerate(tasks) if (i // 2) % 2 == args.lane]
    for task in tasks:
        # Separate process releases all CPU/GPU arrays between training scopes.
        subprocess.run([sys.executable, '-m', 'auditory_retrain.run', 'task', '--plan', str(planpath),
                        '--index', str(task['index'])], check=True)
    write_json(planpath.parent / f'worker_{args.resource}_{args.lane}_{os.environ["SLURM_JOB_ID"]}.json',
               dict(status='PASS', tasks=[t['name'] for t in tasks], job_id=os.environ['SLURM_JOB_ID']))


def readout(args):
    from auditory5.routes import route_d, route_d_controls
    planpath, plan = frozen_plan(args)
    config = plan['config']
    base = ROOT / config['paths']['private_relative']
    modes = config['corrected_retraining']['modes']
    for task in plan['tasks']:
        c = json.loads((planpath.parent / 'outputs' / task['name'] / 'completion.json').read_text())
        assert c['status'] == 'PASS' and c['plan_hash'] == digest(planpath)
    calls = [0]
    original = route_d.grouped_ridge_predict
    def counted(*a, **kw):
        calls[0] += 1
        return original(*a, **kw)
    route_d.grouped_ridge_predict = counted
    route_d_controls.grouped_ridge_predict = counted
    if args.command == 'core':
        destination = base / 'core_001'
        summary = route_d.run(config, plan['split_run'], planpath, modes, destination)
    else:
        destination = base / 'controls_001'
        summary = route_d_controls.run(config, plan['split_run'], planpath, modes,
                                       {m: base / 'core_001' for m in modes}, destination)
    write_json(destination / 'execution_receipt.json', dict(job_id=os.environ['SLURM_JOB_ID'],
               head_calls=calls[0], plan_hash=digest(planpath), scientific_early_stopping=False))
    print(json.dumps(dict(stage=args.command, status=summary['status'], head_calls=calls[0])), flush=True)
    if args.command == 'controls' and summary['status'] != 'COMPLETED_DIAGNOSTICS':
        raise RuntimeError('Some controls failed; inspect saved private errors before proceeding')


def main():
    require_slurm()
    torch.set_num_threads(int(os.environ.get('SLURM_CPUS_PER_TASK', '4')))
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['probe', 'prepare', 'worker', 'task', 'core', 'controls'])
    parser.add_argument('--run', default='gpu_probe_001')
    parser.add_argument('--plan', default=str(ROOT / 'private/auditory_retrain_v1/jobs/plan_001/plan.json'))
    parser.add_argument('--resource', choices=['cpu', 'gpu'], default='gpu')
    parser.add_argument('--lane', type=int, choices=[0, 1], default=0)
    parser.add_argument('--index', type=int)
    args = parser.parse_args()
    if args.command == 'probe':
        probe(args)
    elif args.command == 'prepare':
        prepare(args)
    elif args.command == 'worker':
        worker(args)
    elif args.command == 'task':
        path, plan = frozen_plan(args)
        task_run(path, plan, plan['tasks'][args.index])
    else:
        readout(args)


if __name__ == '__main__':
    main()
