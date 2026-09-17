"""Zero-refit metrics and influence descriptions from fixed outer predictions."""
import json
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.metrics import roc_auc_score
from .provenance import ROOT, digest, write_json, finish, require_slurm
from .readouts import ce_bits, population_weights


SOURCES = [
    ('G0_within', 'G0_readouts_001', 'within_child_predictions.parquet'),
    ('G0_bridge', 'G0_readouts_001', 'bridge_predictions.parquet'),
    ('N1', 'N1_core_001', 'oof_predictions.parquet'),
    ('N3', 'N3_core_001', 'oof_predictions.parquet'),
    ('N3_selected', 'N3_core_001', 'selected_oof_predictions.parquet'),
    ('N2', 'N2_core_001', 'oof_predictions.parquet'),
]


def candidate_metrics(frame):
    """Equal candidates, with natural or class-balanced risk within candidate."""
    frame = frame.copy()
    if 'split_group_id' not in frame:
        frame['split_group_id'] = frame.candidate_id.astype(str)
    if 'population' not in frame:
        frame['population'] = 'P_bal'
    dimensions = [c for c in ('mode','bank','population','family','view','window','calibration') if c in frame]
    identifier = 'bag_id' if 'bag_id' in frame else 'trial_id'
    if frame.duplicated(dimensions + [identifier]).any():
        raise ValueError('FIXED_OUTER_PREDICTION_DUPLICATE')
    output = []
    for keys, rows in frame.groupby(dimensions + ['split_group_id'], sort=True, dropna=False):
        values = dict(zip(dimensions + ['split_group_id'], keys))
        y = rows.stimulus_local_id.to_numpy(int)
        z = rows.logit.to_numpy(float)
        if set(y) != {0,1} or not np.isfinite(z).all():
            raise ValueError('FIXED_METRICS_CLASS_OR_FINITE_SUPPORT')
        w = population_weights(y, rows.split_group_id.to_numpy(), values['population'])
        p = expit(z)
        output.append(dict(values, ce_bits=ce_bits(z,y,w),
            bacc=float(.5*np.mean(z[y==0]<0) + .5*np.mean(z[y==1]>=0)),
            auroc=float(roc_auc_score(y,z)),
            brier_two_class_sum=float(np.average(2*(p-y)**2,weights=w)),
            n_observations=len(rows), n_records=rows.record_id.nunique() if 'record_id' in rows else None))
    return pd.DataFrame(output), dimensions


def influence_description(difference):
    """Describe every leave-one-candidate-out mean; no outlier exclusions."""
    d = np.asarray(difference, float)
    if d.ndim != 1 or len(d)<2 or not np.isfinite(d).all():
        raise ValueError('INFLUENCE_COMPLETE_CANDIDATES')
    loo = (d.sum()-d)/(len(d)-1)
    return dict(n_candidates=len(d), estimate=float(d.mean()),
        leave_one_out_min=float(loo.min()), leave_one_out_max=float(loo.max()),
        all_leave_one_out_positive=bool(np.all(loo>0)),
        positive_candidates=int((d>0).sum()), negative_candidates=int((d<0).sum()),
        max_absolute_share=float(np.max(abs(d))/sum(abs(d))) if np.any(d) else 0.,
        scope='descriptive fixed predictions; no candidate removed from any reported effect')


def calibration_records(packet, folder, hashes):
    def read(path):
        hashes[str(path)]=digest(path)
        return json.loads(path.read_text())
    if packet=='N3_selected':return []
    path=folder/'calibration.json'
    if path.exists():return read(path)
    if packet=='G0_within':
        path=folder/'within_child_fit_receipts.json'
        # The shared fold-level calibration is applied to multiple child heads.
        return [dict(mode=r['mode'],outer_fold=r['outer_fold'],**r['calibration'])
            for r in read(path) if isinstance(r.get('calibration'),dict)]
    if packet=='G0_bridge':
        records=[]
        for path in sorted(folder.glob('bridge_*_outer*_calibration.json')):
            _,bank,outer,_=path.stem.split('_')
            records.append(dict(mode='L0',bank=bank,outer_fold=int(outer[5:]),**read(path)))
        return records
    return []


def history_stratum_support(frame):
    """Describe the fixed N3 test population, counting each trial exactly once."""
    fields = ['trial_id','split_group_id','stimulus_local_id','previous_run_bin']
    output = []
    for (mode, population), rows in frame.groupby(['mode','population'], sort=True):
        reference = rows[rows.view.eq('H') & rows.calibration.eq('raw')][fields]
        if reference.empty or reference.trial_id.duplicated().any():
            raise ValueError('N3_STRATUM_REFERENCE_SUPPORT')
        reference = reference.sort_values('trial_id').reset_index(drop=True)
        for _, view in rows.groupby(['view','calibration'], sort=True):
            actual = view[fields].sort_values('trial_id').reset_index(drop=True)
            if not actual.equals(reference):
                raise ValueError('N3_STRATUM_ALL_VIEWS_SAME_POOL')
        for runbin, group in reference.groupby('previous_run_bin', sort=True):
            y = group.stimulus_local_id.to_numpy(int)
            if not set(y).issubset({0,1}):
                raise ValueError('N3_STRATUM_BINARY_LABELS')
            two_class = group.groupby('split_group_id').stimulus_local_id.nunique().eq(2)
            output.append(dict(mode=mode, population=population, previous_run_bin=runbin,
                class0_trials=int((y==0).sum()), class1_trials=int((y==1).sum()),
                n_candidates=group.split_group_id.nunique(),
                n_candidates_both_classes=int(two_class.sum()), n_trials=len(group),
                support_scope='fixed selected-family outer predictions; all views and calibrations checked'))
    return output


def summarize_metrics(candidate, dimensions):
    metrics = ['ce_bits','bacc','auroc','brier_two_class_sum']
    output = []
    for key, rows in candidate.groupby(dimensions, dropna=False, sort=True):
        if not isinstance(key, tuple): key = (key,)
        values = dict(zip(dimensions,key))
        if rows.split_group_id.duplicated().any():
            raise ValueError('METRICS_CANDIDATE_DUPLICATE')
        rng = np.random.default_rng(20260917)
        ix = rng.integers(0,len(rows),(2000,len(rows)))
        for metric in metrics:
            x = rows[metric].to_numpy(float)
            boots = x[ix].mean(axis=1)
            output.append(dict(values, metric=metric, estimate=float(x.mean()),
                ci_lower=float(np.quantile(boots,.025)),ci_upper=float(np.quantile(boots,.975)),
                n_candidates=len(rows), n_observations=int(rows.n_observations.sum()),
                aggregation='macro candidate mean', bootstrap_scope='fixed OOF candidate bootstrap; no refit'))
    return output


def run(config, registry, site, dest, public, report):
    require_slurm()
    metrics, robustness, statuses, hashes, temperatures, strata = [], [], [], {}, [], []
    for packet, run_name, filename in SOURCES:
        folder = ROOT/'private/auditory_next_v2'/run_name
        source, complete = folder/filename, folder/'completion.json'
        if not complete.exists() or not source.exists():
            statuses.append(dict(packet=packet,source_run=run_name,status='SOURCE_NOT_COMPLETE_OR_PREDICTIONS_WITHHELD'))
            continue
        hashes[str(source)] = digest(source)
        hashes[str(complete)] = digest(complete)
        frame = pd.read_parquet(source)
        if packet == 'G0_within': frame = frame[frame.child_role.eq('heldout')].copy()
        if packet == 'N3_selected': strata.extend(history_stratum_support(frame))
        candidate, dimensions = candidate_metrics(frame)
        candidate.to_parquet(dest/(packet+'_candidate_metrics.parquet'),index=False)
        metrics.extend(dict(packet=packet,source_run=run_name,**row) for row in summarize_metrics(candidate,dimensions))
        pairs = [('HP','HPB'),('HB','HPB'),('HPP','HPB'),('HPBnoise','HPB')] if packet=='N1' else (
            [('H','HP'),('HB','HBP'),('H','Hnoise')] if packet.startswith('N3') else
            [('HMU','HMUVAR'),('HMUMU','HMUVAR')] if packet=='N2' else [])
        if pairs:
            groups = [d for d in dimensions if d!='view']
            for key, rows in candidate.groupby(groups,dropna=False,sort=True):
                wide = rows.pivot(index='split_group_id', columns='view', values='ce_bits')
                values = dict(zip(groups,key))
                for first, second in pairs:
                    if first not in wide or second not in wide: continue
                    if wide[[first,second]].isna().any().any():
                        raise ValueError('ROBUSTNESS_MUST_KEEP_COMPLETE_SUPPORT')
                    robustness.append(dict(packet=packet,source_run=run_name,first=first,second=second,
                        **values,**influence_description(wide[first]-wide[second])))
        calrecords = calibration_records(packet,folder,hashes)
        if calrecords:
            table = pd.DataFrame(calrecords)
            if len(table):
                keys = [c for c in ('mode','bank','population','window','family') if c in table]
                for key, rows in table.groupby(keys,dropna=False,sort=True):
                    if not isinstance(key,tuple):key=(key,)
                    temperatures.append(dict(packet=packet,**dict(zip(keys,key)),n_temperatures=len(rows),
                        parameter_records_are_independent=False,
                        calibration_record_scope='applied final heads; G0 within repeats shared outer-fold calibration',
                        lower_bound=.25,upper_bound=16.,
                        lower_touch_count=int(np.isclose(rows.temperature,.25,atol=1e-4).sum()),
                        upper_touch_count=int(np.isclose(rows.temperature,16.,atol=1e-4).sum()),
                        minimum_temperature=float(rows.temperature.min()),maximum_temperature=float(rows.temperature.max()),
                        mixture_primary=False))
        statuses.append(dict(packet=packet,source_run=run_name,status='PASS',candidate_metric_rows=len(candidate)))
    if any(digest(path)!=sha for path,sha in hashes.items()):raise ValueError('FIXED_PREDICTIONS_CHANGED')
    write_json(dest/'input_hashes.json',hashes)
    pd.DataFrame(metrics).to_csv(public/'metrics_enriched.csv',index=False)
    pd.DataFrame(robustness).to_csv(public/'candidate_influence_aggregate.csv',index=False)
    pd.DataFrame(temperatures).to_csv(public/'temperature_bounds.csv',index=False)
    pd.DataFrame(strata, columns=['mode','population','previous_run_bin','class0_trials','class1_trials',
        'n_candidates','n_candidates_both_classes','n_trials','support_scope']).to_csv(
        public/'history_stratum_support.csv',index=False)
    (report/'FIXED_PREDICTION_METRICS.md').write_text(
        '# 固定预测补充评价\n\n逐候选计算 CE、平衡准确率、AUROC、两类概率平方误差之和，再对候选等权汇总。'
        '区间为2000次固定预测候选bootstrap，不重拟合模型。全部逐候选删除均值仅作敏感性描述，不删除离群值。'
        '只处理源运行已完成且输出的完整模型族；被数值门限扣留的预测不会从部分checkpoint补取。温度与先验混合诊断分开。\n')
    return finish(dest,public,dict(status='FIXED_PREDICTION_METRICS_COMPLETE',sources=statuses,
        new_head_fits=0,new_encoder_fits=0,new_calibration_fits=0))
