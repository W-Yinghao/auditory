"""Training-only preprocessing and bounded nested archival-score comparisons."""
import itertools
import json
from pathlib import Path
import numpy as np
from sklearn.model_selection import KFold

RECORDER = None


def set_recorder(callback):
    global RECORDER
    RECORDER = callback


def standardize(train, test):
    mean = train.mean(axis=0)
    scale = train.std(axis=0)
    scale = np.where(scale > 1e-12, scale, 1.)
    return (train - mean) / scale, (test - mean) / scale, dict(mean=mean.tolist(), scale=scale.tolist())


def clinical_block(train, test, quadratic=False):
    train, test = np.asarray(train, float), np.asarray(test, float)
    if train.ndim != 2 or test.shape[1] != train.shape[1]:
        raise ValueError('INVALID_CLINICAL_SHAPE')
    if np.isinf(train).any() or np.isinf(test).any():
        raise ValueError('INFINITE_CLINICAL_VALUE')
    med = np.array([np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else 0. for v in train.T])
    missing_a, missing_b = np.isnan(train), np.isnan(test)
    a, b, first = standardize(np.where(missing_a, med, train), np.where(missing_b, med, test))
    if quadratic:
        pairs = list(itertools.combinations_with_replacement(range(a.shape[1]), 2))
        a = np.column_stack([a] + [a[:, i] * a[:, j] for i, j in pairs])
        b = np.column_stack([b] + [b[:, i] * b[:, j] for i, j in pairs])
    a, b, second = standardize(np.column_stack([a, missing_a]), np.column_stack([b, missing_b]))
    return a, b, dict(imputation=med.tolist(), raw_scaling=first, expanded_scaling=second, quadratic=quadratic)


def fit_predict(C, Q, Z, y, train, test, candidate, seed, bounds):
    """candidate=(clinical_family, clinical_alpha, eeg_alpha, use_quality, shuffle)."""
    if RECORDER:
        RECORDER(dict(candidate=list(candidate), training_rows=len(train), test_rows=len(test)))
    family, alpha_c, alpha_z, use_q, shuffle = candidate
    a_parts, b_parts, penalties, transforms = [], [], [], {}
    if family != 'none':
        a, b, state = clinical_block(C[train], C[test], family == 'quadratic')
        a_parts.append(a); b_parts.append(b); penalties.extend([alpha_c] * a.shape[1])
        transforms['clinical'] = state
    if use_q:
        a, b, state = clinical_block(Q[train], Q[test])
        a_parts.append(a); b_parts.append(b); penalties.extend([alpha_c] * a.shape[1])
        transforms['quality'] = state
    if alpha_z is not None:
        if not np.isfinite(Z[train]).all() or not np.isfinite(Z[test]).all():
            raise ValueError('NONFINITE_EEG_FEATURE')
        a, b, state = standardize(Z[train], Z[test])
        if shuffle:
            local_seed = (int(seed) + sum((int(i) + 1) * 2654435761 for i in train)) % (2**32 - 1)
            permutation = np.random.default_rng(local_seed).permutation(len(train))
            a = a[permutation]
            state['training_permutation_indices'] = permutation.tolist()
        a_parts.append(a); b_parts.append(b); penalties.extend([alpha_z] * a.shape[1])
        transforms['EEG'] = state
    if not a_parts:
        raise ValueError('EMPTY_MODEL')
    x, xx = np.column_stack(a_parts), np.column_stack(b_parts)
    ytrain = np.asarray(y[train], float)
    if not np.isfinite(ytrain).all() or not np.isfinite(x).all() or not np.isfinite(xx).all():
        raise ValueError('NONFINITE_FIT_INPUT')
    alpha = np.asarray(penalties, float)
    scaled = x / np.sqrt(alpha)
    intercept = float(ytrain.mean())
    coef = (scaled.T @ np.linalg.solve(scaled @ scaled.T + np.eye(len(train)), ytrain - intercept)) / np.sqrt(alpha)
    prediction = np.clip(xx @ coef + intercept, *bounds)
    if not np.isfinite(prediction).all() or not np.isfinite(coef).all():
        raise ValueError('NONFINITE_RIDGE_SOLUTION')
    return prediction, dict(candidate=list(candidate), transforms=transforms, coef=coef.tolist(), intercept=intercept)


def candidates(name, config):
    c = config['validation']
    use_q = name in ['C_Q', 'C_Q_Z']
    families = ['linear'] if name == 'C_LINEAR' else c['clinical_families']
    if name == 'Z_ONLY':
        return [('none', None, a, False, False) for a in c['eeg_alphas']]
    result = [(family, alpha, None, use_q, False) for family in families for alpha in c['clinical_alphas']]
    if name in ['C_Z', 'C_Q_Z', 'C_SHUFFLED_Z']:
        result += [(family, alpha, z_alpha, use_q, name == 'C_SHUFFLED_Z')
                   for family in families for alpha in c['clinical_alphas'] for z_alpha in c['eeg_alphas']]
    return result


def make_splits(groups, config):
    groups = np.asarray(groups).astype(str)
    if len(set(groups)) != len(groups):
        raise ValueError('ONE_RECORD_PER_IDENTITY_REQUIRED')
    order = np.argsort(groups, kind='stable')
    cfg = config['validation']
    result = []
    for fold, (a, b) in enumerate(KFold(cfg['outer_folds'], shuffle=True, random_state=cfg['seed']).split(order)):
        train, test = order[a], order[b]
        inner = [(train[x], train[y]) for x, y in KFold(cfg['inner_folds'], shuffle=True, random_state=cfg['seed'] + fold + 1).split(train)]
        if any(set(x) & set(y) or (set(x) | set(y)) & set(test) for x, y in inner):
            raise ValueError('IDENTITY_LEAKAGE')
        result.append((train, test, inner))
    return result


def evaluate_fold(C, Q, Z, y, train, test, inner, config):
    cache = {}
    def fit(a, b, candidate):
        key = (tuple(map(int, a)), tuple(map(int, b)), candidate)
        if key not in cache:
            cache[key] = fit_predict(C, Q, Z, y, a, b, candidate, config['validation']['seed'], config['validation']['target_prediction_bounds'])
        return cache[key]
    outputs = {}
    for name in config['models']:
        if name == 'MEAN':
            prediction = np.full(len(test), np.clip(y[train].mean(), *config['validation']['target_prediction_bounds']))
            outputs[name] = dict(prediction=prediction, selected=None, selection_loss=None, fitted_model=None)
            continue
        scores = []
        possible = candidates(name, config)
        for candidate in possible:
            loss, n = 0., 0
            for a, b in inner:
                p, _ = fit(a, b, candidate)
                loss += np.abs(p - y[b]).sum(); n += len(b)
            if n != len(train):
                raise ValueError('INCOMPLETE_INNER_DENOMINATOR')
            scores.append(float(loss / n))
        chosen = int(np.argmin(scores))
        prediction, model = fit(train, test, possible[chosen])
        outputs[name] = dict(prediction=prediction, selected=possible[chosen], selection_loss=scores[chosen], fitted_model=model,
                             candidate_risks=[dict(candidate=list(c), MAE=s) for c, s in zip(possible, scores)])
    return outputs


def paired_interval(loss_difference, folds, repetitions, seed):
    difference = np.asarray(loss_difference, float)
    difference = np.where(np.abs(difference) < 1e-10, 0., difference)
    if not np.isfinite(difference).all():
        raise ValueError('NONFINITE_PAIRED_RISK')
    rng = np.random.default_rng(seed)
    partitions = [np.flatnonzero(folds == f) for f in np.unique(folds)]
    boot = np.zeros(repetitions)
    for indices in partitions:
        draws = rng.choice(indices, size=(repetitions, len(indices)), replace=True)
        boot += difference[draws].sum(axis=1) / len(difference)
    low, high = np.quantile(boot, [.025, .975])
    return dict(gain_MAE=float(difference.mean()), ci_low=float(low), ci_high=float(high), n_identity_groups=len(difference),
                positive_fold_count=sum(difference[indices].mean() > 0 for indices in partitions), n_folds=len(partitions))


def run_models(data, config, private, public):
    import pandas as pd
    C, Q, Z, A, V, groups = (data[k] for k in ['C', 'Q', 'Z', 'A', 'V', 'groups'])
    n = len(groups)
    if n < config['population']['minimum_identity_groups']:
        return dict(status='SUPPORT_INSUFFICIENT', identity_groups=n, new_model_fits=0)
    if any(not np.isfinite(y).all() or len(np.unique(y)) < config['validation']['minimum_unique_target_values'] for y in [A, V]):
        raise ValueError('TARGET_VARIATION_UNSUPPORTED')
    splits = make_splits(groups, config)
    assignments = []
    for fold, (train, test, inner) in enumerate(splits):
        assignments.append(dict(fold=fold, train=train.tolist(), test=test.tolist(),
            train_groups=groups[train].tolist(), test_groups=groups[test].tolist(),
            inner=[dict(train=a.tolist(), validation=b.tolist()) for a, b in inner]))
    (private / 'splits.json').write_text(json.dumps(assignments, indent=2))
    metrics, comparisons, selections, predictions, fold_metrics = [], [], [], [], []
    statuses = {}
    for task in config['tasks']:
        y = A if task == 'A_given_C' else V
        clinical = np.column_stack([C, A]) if task == 'V_given_C_and_A' else C
        oof = {name: np.full(n, np.nan) for name in config['models']}
        fold_index = np.full(n, -1)
        for fold, (train, test, inner) in enumerate(splits):
            outputs = evaluate_fold(clinical, Q, Z, y, train, test, inner, config)
            fold_index[test] = fold
            for name, output in outputs.items():
                oof[name][test] = output['prediction']
                selections.append(dict(task=task, outer_fold=fold, model=name, selected=output['selected'], inner_MAE=output['selection_loss']))
                serial = {k: v for k, v in output.items() if k != 'prediction'}
                (private / f'{task}_fold{fold}_{name}_fit.json').write_text(json.dumps(serial, indent=2, allow_nan=False))
        if any(not np.isfinite(v).all() for v in oof.values()) or (fold_index < 0).any():
            raise ValueError('INCOMPLETE_OUTER_PREDICTIONS')
        for name, p in oof.items():
            err = p - y
            metrics.append(dict(task=task, model=name, n_identity_groups=n, MAE=float(np.abs(err).mean()),
                RMSE=float(np.sqrt(np.mean(err**2))), R2=float(1 - np.sum(err**2) / np.sum((y-y.mean())**2)),
                prediction_min=float(p.min()), prediction_max=float(p.max())))
            for f in np.unique(fold_index):
                local = err[fold_index == f]
                fold_metrics.append(dict(task=task, model=name, outer_fold=int(f), n_identity_groups=len(local),
                    MAE=float(np.abs(local).mean()), RMSE=float(np.sqrt(np.mean(local**2)))))
            for i in range(n):
                predictions.append(dict(task=task, model=name, group=groups[i], recording=data['recordings'][i],
                    outer_fold=int(fold_index[i]), y=float(y[i]), prediction=float(p[i])))
        contrasts = [('primary', 'C_BEST', 'C_Z'), ('quality_adjusted', 'C_Q', 'C_Q_Z'),
                     ('content_control', 'C_SHUFFLED_Z', 'C_Z'), ('clinical_nonlinearity', 'C_LINEAR', 'C_BEST'),
                     ('EEG_alone_vs_mean', 'MEAN', 'Z_ONLY'), ('quality_vs_clinical', 'C_BEST', 'C_Q')]
        local = {}
        for label, baseline, augmented in contrasts:
            d = np.abs(y-oof[baseline]) - np.abs(y-oof[augmented])
            estimate = paired_interval(d, fold_index, config['validation']['bootstrap_repetitions'], config['validation']['bootstrap_seed'])
            row = dict(task=task, contrast=label, baseline=baseline, augmented=augmented, **estimate)
            comparisons.append(row); local[label] = row
        promising = local['primary']['ci_low'] > 0 and local['quality_adjusted']['ci_low'] > 0 and local['content_control']['gain_MAE'] > 0
        statuses[task] = 'EXPLORATORY_CONTROLLED_GAIN_SCREEN' if promising else 'NO_CONTROLLED_ARCHIVAL_GAIN_ESTABLISHED'
    pd.DataFrame(predictions).to_csv(private / 'predictions.csv', index=False)
    pd.DataFrame(metrics).to_csv(public / 'metrics.csv', index=False)
    pd.DataFrame(comparisons).to_csv(public / 'paired_effects.csv', index=False)
    pd.DataFrame(fold_metrics).to_csv(public / 'fold_metrics.csv', index=False)
    (public / 'selections.json').write_text(json.dumps(selections, indent=2, allow_nan=False))
    return dict(status='ARCHIVAL_SCREEN_COMPLETE', identity_groups=n, tasks=statuses, metrics=metrics,
        comparisons=comparisons, exploratory=True, strict_clinical_qualification_unchanged=True,
        clinical_contemporaneity='unknown', target_A='mixed_literal_IT_MAIS_MAIS_header', automatic_push=False)
