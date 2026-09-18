"""Fixed representations and repeated identity-heldout archival prediction."""
import argparse
import contextlib
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import traceback

ROOT = Path('/home/infres/yinwang/EEG_auditory')


def dump(path, obj):
    def convert(x):
        if hasattr(x, 'tolist'):
            return x.tolist()
        if hasattr(x, 'item'):
            return x.item()
        raise TypeError(type(x).__name__)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False, default=convert) + '\n')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


class Counter:
    def __init__(self, private, maximum):
        self.n = 0
        self.maximum = maximum
        self.handle = (private / 'fit_events.jsonl').open('x')

    def __call__(self, event):
        if self.n >= self.maximum:
            raise ValueError('FIT_ATTEMPT_LIMIT')
        self.n += 1
        self.handle.write(json.dumps(dict(attempt=self.n, **event)) + '\n')


def bank_features(x, t, codes):
    import numpy as np
    from auditory_fseries.data import _record_statistics
    if not np.isfinite(x).all() or x.shape[1:] != (20, 176):
        raise ValueError('INVALID_EPOCH_DATA')
    result = {'HJORTH': _record_statistics(x, np.arange(len(x)))}
    conditions = []
    for code in [1, 2]:
        if np.sum(codes == code) < 1:
            raise ValueError('EMPTY_CONDITION')
        conditions.append(np.mean(x[codes == code], axis=0))
    def bins(wave, start, count):
        return np.concatenate([wave[:, (t >= start + i * .05 - 1e-10) &
            (t < start + (i + 1) * .05 - 1e-10)].mean(axis=1) for i in range(count)])
    post = [bins(w, 0., 8) for w in conditions]
    result['POST'] = np.concatenate(post)
    result['CONTRAST'] = post[1] - post[0]
    result['PRE'] = np.concatenate([bins(w, -.2, 4) for w in conditions])
    z = np.asarray(x[:, :, t >= 0], float)
    z = z - z.mean(axis=2, keepdims=True)
    covariance = np.einsum('nct,ndt->ncd', z, z) / z.shape[2]
    variance = np.maximum(np.diagonal(covariance, axis1=1, axis2=2), 1e-12)
    correlation = covariance / np.sqrt(variance[:, :, None] * variance[:, None, :])
    a, b = np.triu_indices(20, 1)
    result['SPATIAL'] = np.r_[np.median(correlation[:, a, b], axis=0), np.median(np.log(variance), axis=0)]
    if any(not np.isfinite(v).all() for v in result.values()):
        raise ValueError('NONFINITE_BANK')
    return result


def reliability_summary(rows):
    import numpy as np
    import pandas as pd
    output = []
    for key, pairs in rows.items():
        bank, budget, split = key
        if len(pairs) < 3:
            output.append(dict(bank=bank, budget=budget, split=split, n=len(pairs), status='DESCRIPTIVE_SUPPORT_ONLY'))
            continue
        x, y = np.array([a for a, b in pairs]), np.array([b for a, b in pairs])
        x -= x.mean(axis=0); y -= y.mean(axis=0)
        denom = np.sqrt((x*x).sum(axis=0) * (y*y).sum(axis=0))
        valid = denom > 1e-12
        r = (x*y).sum(axis=0)[valid] / denom[valid]
        sb = 2*r / (1+r)
        output.append(dict(bank=bank, budget=budget, split=split, n=len(pairs), valid_features=len(r),
            median_correlation=float(np.median(r)), q25=float(np.quantile(r,.25)), q75=float(np.quantile(r,.75)),
            fraction_positive=float(np.mean(r>0)), median_spearman_brown_heuristic=float(np.median(sb)), status='ESTIMATED'))
    return pd.DataFrame(output)


def prepare(private, public, config):
    import numpy as np
    import pandas as pd
    from auditory_fseries.data import _read_workbook, _workbook_path, _number, _source_row_from_clinical_id, CANONICAL_CHANNELS
    linked_path = ROOT / 'private/phase2_cohort_001/linked_index.csv'
    clinical_path = ROOT / 'private/clinical_003/clinical_rows_clean.csv'
    manifest_path = ROOT / 'results/phase1_sources_001/source_manifest.csv'
    workbook_path = _workbook_path(ROOT, {}, ROOT / 'private/inventory_001/file_path_map.csv')
    workbook, _ = _read_workbook(workbook_path)
    links = pd.read_csv(linked_path).fillna('')
    clinical = pd.read_csv(clinical_path).set_index('source_row')
    sources = pd.read_csv(manifest_path).set_index('recording_id')
    def yes(s):
        return str(s).lower() == 'true'
    candidates = links[links.apply(lambda r: r.cohort == 'HA' and yes(r.eligible_measurement_identity_index)
        and yes(r.strong_unique_link) and r.clinical_link_evidence == 'name_and_label_date' and int(r.clinical_link_count) == 1, axis=1)]
    rows, all_banks, reliability, epochs_hashes, exclusions = [], [], {}, {}, []
    for item in candidates.to_dict('records'):
        rn = _source_row_from_clinical_id(item['clinical_row_id']); wr = workbook[rn]; old = clinical.loc[rn]
        assert str(old.raw_name).strip() == wr['name']
        for field, key in [('age_months','age_months'), ('duration_months','duration_months'), ('MUSS','MUSS'), ('IT_MAIS_MAIS','IT_MAIS_MAIS')]:
            assert _number(old[field]) == wr[key]
        rid = item['recording_id']; path = ROOT / 'results/phase1_epochs_001' / rid / 'epochs.npz'
        if not path.exists():
            exclusions.append(dict(recording=rid, reason='no_epoch_package')); continue
        with np.load(path, allow_pickle=False) as package:
            assert tuple(package['channels'].astype(str)) == CANONICAL_CHANNELS
            t = package['times_s']; assert np.allclose(t, np.linspace(-.2,.5,176), atol=1e-12, rtol=0)
            mask = package['accepted'][:,0].astype(bool) & np.isin(package['codes'],[1,2])
            indices = np.flatnonzero(mask)
            indices = indices[np.lexsort((package['event_indices_1based'][indices],package['samples_0based'][indices]))]
            x = package['data_uv'][indices].astype(float); codes = package['codes'][indices]
            total_stored = len(mask)
        counts = [int(np.sum(codes==c)) for c in [1,2]]
        if min(counts) < config['minimum_trials_per_event_code']:
            exclusions.append(dict(recording=rid, reason='fewer_than_two_accepted_in_one_literal_code')); continue
        required = [wr['age_months'],wr['duration_months'],wr['IT_MAIS_MAIS'],wr['MUSS'],_number(old.CAP),_number(old.SIR)]
        if any(v is None for v in required) or min(required[:2]) < 0:
            exclusions.append(dict(recording=rid, reason='missing_required_archive_value')); continue
        chosen = np.rint(np.linspace(0,len(x)-1,min(config['max_epochs'],len(x)))).astype(int)
        if any(np.sum(codes[chosen] == c) < 1 for c in [1,2]):
            raise ValueError('UNIFORM_SAMPLE_MISSING_CONDITION')
        features = bank_features(x[chosen], t, codes[chosen]); all_banks.append(features)
        q = [np.log1p(len(x)), 1-len(x)/total_stored, np.log(max(np.median(np.ptp(x,axis=2).max(axis=1)),1e-12)),
             np.log(float(sources.loc[rid,'duration_s'])), *np.log1p(counts)]
        rows.append(dict(group=item['participant_id'], recording=rid, source_row=rn, name=wr['name'], age=required[0],
            duration=required[1], A=required[2], V=required[3], CAP=required[4], SIR=required[5],
            unaided=wr['better_unaided_pta'], aided=wr['better_aided_pta'], n_epochs=len(x), code1=counts[0], code2=counts[1], Q=q))
        epochs_hashes[str(path)] = sha(path)
        for budget in config['reliability_budgets']:
            if len(x) < budget:
                continue
            sub = np.rint(np.linspace(0,len(x)-1,budget)).astype(int)
            for split, halves in [('interleaved',(sub[::2],sub[1::2])), ('temporal',(sub[:len(sub)//2],sub[len(sub)//2:]))]:
                if any(any(np.sum(codes[h]==c)<1 for c in [1,2]) for h in halves):
                    continue
                aa, bb = [bank_features(x[h],t,codes[h]) for h in halves]
                for bank in config['banks']:
                    reliability.setdefault((bank,budget,split),[]).append((aa[bank],bb[bank]))
    frame = pd.DataFrame(rows); frame.to_csv(private / 'cohort.csv',index=False)
    assert frame.group.is_unique and len(frame) >= config['outer_folds'] * 2
    arrays = dict(C=np.c_[frame.age,np.log1p(frame.duration),frame.unaided,frame.aided].astype(float),
        Q=np.asarray(frame.Q.tolist()), groups=frame.group.to_numpy(str), recordings=frame.recording.to_numpy(str))
    arrays.update({target:frame[target].to_numpy(float) for target in ['A','V','CAP','SIR']})
    arrays.update({bank:np.array([b[bank] for b in all_banks]) for bank in config['banks']})
    for task in ['A','V','CAP','SIR']:
        lo,hi=config['target_bounds'][task]; assert np.all((arrays[task]>=lo)&(arrays[task]<=hi))
    np.savez(private / 'data.npz', **arrays)
    pd.DataFrame(exclusions).to_csv(private/'exclusions.csv',index=False)
    reliability_summary(reliability).to_csv(public/'reliability.csv',index=False)
    clinical_rows=[]
    for task in ['A','V','CAP','SIR']:
        y=arrays[task];lo,hi=config['target_bounds'][task]
        clinical_rows.append(dict(target=task,n=len(y),minimum=float(min(y)),median=float(np.median(y)),maximum=float(max(y)),
            unique_values=len(np.unique(y)),ceiling_count=int(np.sum(y==hi)),floor_count=int(np.sum(y==lo))))
    pd.DataFrame(clinical_rows).to_csv(public/'target_distribution.csv',index=False)
    corr=frame[['age','duration','A','V','CAP','SIR']].corr(method='spearman')
    corr.to_csv(public/'clinical_rank_correlations.csv')
    dump(private/'inputs.json',{**{str(p):sha(p) for p in [linked_path,clinical_path,manifest_path,workbook_path]},**epochs_hashes})
    return dict(status='READY',identity_groups=len(frame),metadata_candidates=len(candidates),excluded=len(exclusions),
        dimensions={bank:arrays[bank].shape[1] for bank in config['banks']},data_sha256=sha(private/'data.npz'),
        missing_PTA=[int(frame.unaided.isna().sum()),int(frame.aided.isna().sum())])


def options(config, bank=None, quality=False, shuffled=False, clinical=True):
    families=config['clinical_families'] if clinical else ['none']
    result=[]
    for family in families:
        for ac in config['clinical_alphas'] if clinical else [None]:
            if clinical:
                result.append((family,ac,None,quality,False,None))
            for az in config['eeg_alphas'] if bank is not None else []:
                result.append((family,ac,az,quality,shuffled,bank))
    return result


def evaluate_fold(data, y, C, train, test, inner, config, seed, bounds):
    import numpy as np
    from auditory_fseries.models import fit_predict
    cache={}
    def fit(a,b,candidate):
        key=(tuple(a),tuple(b),candidate)
        if key not in cache:
            *head,bank=candidate
            z=data[bank] if bank else np.zeros((len(y),0))
            cache[key]=fit_predict(C,data['Q'],z,y,a,b,tuple(head),seed,bounds)
        return cache[key]
    pool={'C_LINEAR':[c for c in options(config) if c[0]=='linear'],'C_BEST':options(config),
          'C_Q':options(config,quality=True)}
    for bank in config['banks']:
        pool['C_'+bank]=options(config,bank)
    def unique(seq):
        return list(dict.fromkeys(seq))
    pool['BEST_CZ']=unique(options(config)+[c for bank in config['banks'] for c in options(config,bank)])
    pool['BEST_CQZ']=unique(options(config,quality=True)+[c for bank in config['banks'] for c in options(config,bank,quality=True)])
    pool['BEST_SHUFFLED']=unique(options(config)+[c for bank in config['banks'] for c in options(config,bank,shuffled=True)])
    pool['Z_ONLY']=unique([c for bank in config['banks'] for c in options(config,bank,clinical=False)])
    result={'MEAN':dict(prediction=np.repeat(np.clip(y[train].mean(),*bounds),len(test)),candidate=None,model=None)}
    for name,choices in pool.items():
        losses=[]
        for choice in choices:
            losses.append(sum(np.abs(fit(a,b,choice)[0]-y[b]).sum() for a,b in inner)/len(train))
        selected=choices[int(np.argmin(losses))]
        pred,model=fit(train,test,selected)
        result[name]=dict(prediction=pred,candidate=selected,inner_MAE=min(losses),model=model)
    return result


def repeated_interval(d, reps, seed):
    import numpy as np
    identity=np.asarray(d).mean(axis=0)
    draws=np.random.default_rng(seed).integers(len(identity),size=(reps,len(identity)))
    boot=identity[draws].mean(axis=1)
    loo=(identity.sum()-identity)/(len(identity)-1)
    return dict(gain_MAE=float(identity.mean()),ci_low=float(np.quantile(boot,.025)),ci_high=float(np.quantile(boot,.975)),
        repeat_gains=np.mean(d,axis=1).tolist(),positive_repeats=int(np.sum(np.mean(d,axis=1)>0)),
        leave_one_identity_min=float(min(loo)),leave_one_identity_max=float(max(loo)),n=len(identity))


def experiment(private,public,config,input_run,counter):
    import numpy as np
    import pandas as pd
    from auditory_fseries.models import make_splits,set_recorder
    source=ROOT/'private/auditory_repair'/input_run
    ready=json.loads((source/'completion.json').read_text());assert ready['status']=='READY'
    assert sha(source/'data.npz')==ready['data_sha256']
    with np.load(source/'data.npz',allow_pickle=False) as z:data={k:z[k] for k in z.files}
    set_recorder(counter);n=len(data['groups']);all_metrics=[];effects=[];predictions=[];strata_rows=[];selection=[]
    split_records=[];split_sets=[]
    for repeat in range(config['outer_repeats']):
        cfg={'validation':dict(outer_folds=config['outer_folds'],inner_folds=config['inner_folds'],seed=config['seed']+repeat)}
        splits=make_splits(data['groups'],cfg);split_sets.append(splits)
        for fold,(tr,te,inner) in enumerate(splits):
            split_records.append(dict(repeat=repeat,fold=fold,train=tr,test=te,inner=[dict(train=a,validation=b) for a,b in inner]))
    dump(private/'splits.json',split_records)
    for task in config['tasks']:
        y=data['V' if task=='V_given_A' else task]
        C=np.c_[data['C'],data['A']] if task=='V_given_A' else data['C']
        oof={};folds=np.full((config['outer_repeats'],n),-1)
        for repeat,splits in enumerate(split_sets):
            for fold,(tr,te,inner) in enumerate(splits):
                output=evaluate_fold(data,y,C,tr,te,inner,config,config['seed']+repeat,config['target_bounds'][task])
                folds[repeat,te]=fold
                fitted={}
                for model,value in output.items():
                    oof.setdefault(model,np.full((config['outer_repeats'],n),np.nan))[repeat,te]=value['prediction']
                    fitted[model]={k:v for k,v in value.items() if k!='prediction'}
                    selection.append(dict(task=task,repeat=repeat,fold=fold,model=model,candidate=value['candidate']))
                dump(private/f'{task}_r{repeat}_f{fold}_heads.json',fitted)
            print(json.dumps(dict(task=task,repeat_complete=repeat,fit_attempts=counter.n)),flush=True)
        assert (folds>=0).all() and all(np.isfinite(p).all() for p in oof.values())
        losses={model:np.abs(p-y) for model,p in oof.items()}
        for model,p in oof.items():
            all_metrics.append(dict(task=task,model=model,n=n,repeats=config['outer_repeats'],MAE=float(losses[model].mean()),
                RMSE=float(np.sqrt(np.mean((p-y)**2))),R2=float(1-np.mean(np.sum((p-y)**2,axis=1))/np.sum((y-y.mean())**2))))
            for repeat in range(config['outer_repeats']):
                for i in range(n):
                    predictions.append(dict(task=task,model=model,repeat=repeat,fold=int(folds[repeat,i]),group=data['groups'][i],
                        recording=data['recordings'][i],y=float(y[i]),prediction=float(p[repeat,i])))
        pairs=[('increment_'+bank,'C_BEST','C_'+bank) for bank in config['banks']]
        pairs += [('joint_selector','C_BEST','BEST_CZ'),('quality_adjusted','C_Q','BEST_CQZ'),
            ('content_control','BEST_SHUFFLED','BEST_CZ'),('EEG_alone','MEAN','Z_ONLY'),('clinical_nonlinearity','C_LINEAR','C_BEST')]
        for contrast,baseline,augmented in pairs:
            d=losses[baseline]-losses[augmented]
            effects.append(dict(task=task,contrast=contrast,baseline=baseline,augmented=augmented,
                **repeated_interval(d,config['bootstrap_repetitions'],config['bootstrap_seed'])))
        strata={'age_le_36':data['C'][:,0]<=36,'age_gt_36':data['C'][:,0]>36,
            'duration_le_6':data['C'][:,1]<=np.log1p(6),'duration_gt_6':data['C'][:,1]>np.log1p(6),
            'ceiling':y==config['target_bounds'][task][1],'non_ceiling':y<config['target_bounds'][task][1]}
        for label,mask in strata.items():
            if not mask.any():continue
            for model in ['C_BEST','BEST_CZ','BEST_CQZ','Z_ONLY']:
                strata_rows.append(dict(task=task,stratum=label,model=model,n=int(mask.sum()),MAE=float(losses[model][:,mask].mean()),
                    gain_vs_clinical=float((losses['C_BEST'][:,mask]-losses[model][:,mask]).mean())))
        # Durable per-task completion permits summary recovery without refits.
        np.savez(private/f'{task}_complete_oof.npz',y=y,folds=folds,**oof)
    pd.DataFrame(predictions).to_csv(private/'predictions.csv',index=False)
    pd.DataFrame(all_metrics).to_csv(public/'metrics.csv',index=False)
    pd.DataFrame([{k:v for k,v in row.items() if k!='repeat_gains'} for row in effects]).to_csv(public/'effects.csv',index=False)
    dump(public/'effects_all_repeats.json',effects)
    pd.DataFrame(strata_rows).to_csv(public/'strata_descriptive.csv',index=False)
    dump(public/'selections.json',selection)
    dump(private/'input_binding.json',dict(run=input_run,data_sha256=ready['data_sha256']))
    return dict(status='COMPLETE_ALL_DECLARED_TASKS',identity_groups=n,tasks=config['tasks'],model_combinations=len(all_metrics),
        fit_attempts=counter.n,scientific_early_stopping=False,independent_confirmation=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','experiment','test','legacy_phase3','report'])
    parser.add_argument('--run',required=True);parser.add_argument('--input-run');parser.add_argument('--test-run');args=parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('SLURM_REQUIRED')
    os.umask(0o077)
    for value in [args.run,args.input_run]:
        if value and (not value.replace('_','').isalnum()):raise ValueError('UNSAFE_RUN_NAME')
    private=ROOT/'private/auditory_repair'/args.run;public=ROOT/'results/auditory_repair'/args.run
    private.mkdir(mode=0o700);public.mkdir(mode=0o700)
    config_path=ROOT/'configs/auditory_repair_v2.json';config=json.loads(config_path.read_text())
    paths=[Path(__file__),ROOT/'auditory_fseries/models.py',ROOT/'auditory_fseries/data.py',config_path,
        ROOT/'docs/auditory_repair/PROTOCOL_v2.md',*sorted((ROOT/'tests/auditory_repair').glob('*.py')),
        *[p for p in (ROOT/'auditory_repair').glob('*.py') if p!=Path(__file__)]]
    hashes={}
    for path in paths:
        rel=path.relative_to(ROOT);dest=private/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,dest);hashes[str(rel)]=sha(path)
    start=dict(job_id=os.environ['SLURM_JOB_ID'],start_unix=time.time(),arguments=vars(args),source_hashes=hashes,
        config_sha256=sha(config_path),cpus=os.environ.get('SLURM_CPUS_PER_TASK'))
    dump(private/'start.json',start);counter=None
    try:
        if args.command in ['prepare','experiment']:
            tested=ROOT/'private/auditory_repair'/str(args.test_run)
            assert json.loads((tested/'completion.json').read_text())['status']=='PASS'
            prior=json.loads((tested/'start.json').read_text())
            assert prior['config_sha256']==start['config_sha256']
            for rel in ['auditory_repair/extended.py','auditory_fseries/models.py','auditory_fseries/data.py']:
                assert prior['source_hashes'][rel]==hashes[rel], 'UNTESTED_SOURCE'
        if args.command=='prepare':result=prepare(private,public,config)
        elif args.command=='experiment':
            counter=Counter(private,config['limits']['extended_heads']);result=experiment(private,public,config,args.input_run,counter)
        elif args.command=='legacy_phase3':
            from .legacy_phase3 import run
            counter=Counter(private,config['limits']['phase3_repair_heads']);result=run(private,public,config,counter)
        elif args.command=='test':
            import pytest
            from auditory_fseries.models import set_recorder
            counter=Counter(private,1000);set_recorder(counter)
            with (private/'pytest.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                rc=pytest.main(['-q','-p','no:cacheprovider','--import-mode=importlib','--basetemp='+str(private/'tmp'),
                    'tests/auditory_repair/test_extended.py','tests/auditory_fseries/test_models.py'])
            result=dict(status='PASS' if rc==0 else 'FAIL',fit_attempts=counter.n)
        else:
            from .report import run
            result=run(private,public,config,args.input_run)
        if counter:counter.handle.flush()
        result.update(job_id=start['job_id'],elapsed_seconds=time.time()-start['start_unix'],config_sha256=start['config_sha256'])
        dump(private/'completion.json',result);dump(public/'summary.json',result);print(json.dumps(result),flush=True)
        return 0 if result['status']!='FAIL' else 1
    except Exception:
        if counter:counter.handle.flush()
        dump(private/'failure.json',dict(traceback=traceback.format_exc(),fit_attempts=counter.n if counter else 0))
        dump(public/'failure.json',dict(status='FAILED',details='private',fit_attempts=counter.n if counter else 0))
        print(json.dumps(dict(status='FAILED',job_id=start['job_id'])),flush=True);return 1
    finally:
        if counter:counter.handle.close()


if __name__=='__main__':
    raise SystemExit(main())
