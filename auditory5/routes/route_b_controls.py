"""B window, measured-quality and fixed-head temporal-misalignment diagnostics."""
import json, math, pickle
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from auditory5.provenance import ROOT, require_slurm, write_json, digest, object_hash
from auditory5.contracts import FitScope
from auditory5.datasets import load_dataset
from auditory5.training import FittedEncoder
from auditory5.probes import (CandidateTabularScaler, C_GRID, bin_20ms, candidate_class_weights,
    fit_temperature, weighted_log_loss_nats, _fit_head, _head_logits)
from auditory5.routes.route_b import (ContextFeatures, HistoryReadout, _fit_transform, _features,
    fit_history_readouts, history_eligible, select_common_support, candidate_support_mask, _summaries)
from auditory5.routes.route_b_learned import _load_fold, ROW_COLUMNS
from auditory5.metrics import candidate_log_losses_bits
from auditory5.statistics import paired_cluster_bootstrap


def quality_values(rows):
    values=rows[['all_ptp_uv','pre_ptp_uv']].to_numpy(float)
    if not np.isfinite(values).all() or np.any(values<0):raise ValueError('B_QUALITY_SCHEMA')
    return np.log1p(values)


class QualityContext(ContextFeatures):
    def fit(self, rows, scope):
        super().fit(rows,scope)
        self.quality_scaler_=CandidateTabularScaler().fit(quality_values(rows),rows.split_group_id,scope)
        return self

    def transform(self, rows, *, strong=True):
        return np.c_[super().transform(rows,strong=strong),self.quality_scaler_.transform(quality_values(rows))]


def fit_quality_readouts(rows, eeg_by_model, scope, seed):
    """Same B nested head algorithm, with quality kept outside EEG PCA."""
    scope.assert_fit_groups(rows.split_group_id)
    groups=rows.split_group_id.to_numpy(str);y=rows.history_target.to_numpy(int)
    candidate_class_weights(y,groups)
    oof={name:{C:np.full((len(rows),2),np.nan) for C in C_GRID} for name in eeg_by_model}
    folds=[]
    for number,(tr,va) in enumerate(GroupKFold(3).split(np.zeros(len(rows)),y,groups)):
        inner=FitScope(tuple(np.unique(groups[tr])),tuple(np.unique(groups[va])),tuple(scope.test_groups))
        a,b,gate=select_common_support(rows.iloc[tr],rows.iloc[va],inner);tr,va=tr[a],va[b]
        if not len(tr) or not len(va):raise ValueError('B_INNER_SUPPORT: empty quality inner fold')
        context=QualityContext().fit(rows.iloc[tr],inner)
        for name,eeg in eeg_by_model.items():
            strong=name!='B0_context_linear'
            x,scaler,pca=_fit_transform(rows.iloc[tr],None if eeg is None else eeg[tr],context,strong,inner)
            valid=context.transform(rows.iloc[va],strong=strong)
            if eeg is not None:valid=np.c_[valid,pca.transform(scaler.transform(eeg[va]))]
            for C in C_GRID:oof[name][C][va]=_head_logits(_fit_head(x,y[tr],groups[tr],C,seed),valid)
        folds.append({'fold':number,'fit_groups':list(inner.train_groups),'validation_groups':list(inner.validation_groups),'scope_hash':inner.hash,'gate':gate.to_dict()})
    available=np.isfinite(oof[next(iter(oof))][C_GRID[0]]).all(axis=1)
    if not available.any():raise ValueError('B_INNER_SUPPORT: no quality inner OOF')
    weights=candidate_class_weights(y[available],groups[available]);context=QualityContext().fit(rows,scope);result={}
    for name,eeg in eeg_by_model.items():
        if any(not np.array_equal(np.isfinite(value).all(axis=1),available) for value in oof[name].values()):raise ValueError('B_UNPAIRED_INNER')
        losses={C:weighted_log_loss_nats(oof[name][C][available],y[available],weights) for C in C_GRID}
        C=min(C_GRID,key=lambda c:(losses[c],c));temperature=fit_temperature(oof[name][C][available],y[available],groups[available],scope)
        strong=name!='B0_context_linear';x,scaler,pca=_fit_transform(rows,eeg,context,strong,scope)
        head=_fit_head(x,y,groups,C,seed)
        evidence={'fit_groups':list(np.unique(groups)),'scope_hash':scope.hash,'inner_folds':folds,
                  'quality_dimension':2,'quality_outside_eeg_pca':True,'inner_encoder_refitted':False,
                  'calibration':temperature,'C_inner_ce_bits':{str(c):v/math.log(2) for c,v in losses.items()}}
        result[name]=HistoryReadout(context,strong,scaler,pca,head,temperature['temperature'],C,evidence)
    return result


def reaction_windows(epochs, rows):
    x=np.asarray(epochs);starts=rows.post_start_index.to_numpy(int)
    if x.ndim!=3 or x.shape[-1]!=175 or len(x)!=len(rows):raise ValueError('B_DIAGNOSTIC_EPOCH_SCHEMA')
    post=np.stack([v[:,s:s+100] for v,s in zip(x,starts)])
    if post.shape[-1]!=100:raise ValueError('B_DIAGNOSTIC_WINDOW')
    return {'early':post[:,:,:50].copy(),'late':post[:,:,50:].copy()}


def stable_shift_segments(rows):
    """Fixed local stability check; never join records or true segments."""
    r=rows.reset_index(drop=True).copy();r['_third']=np.minimum((r.segment_position_fraction*3).astype(int),2)
    segments=[]
    for _,part in r.groupby(['record_id','segment_id','_third'],sort=True):
        ids=part.sort_values('onset_sample').index.to_numpy();gap=part.previous_gap_s.to_numpy(float)
        if len(ids)<100 or any(np.sum(part.history_target==h)<20 for h in (0,1)):continue
        median=float(np.median(gap))
        if not np.isfinite(gap).all() or median<=0 or np.ptp(np.quantile(gap,[.25,.75]))>.1*median or gap.max()>1.5*median:continue
        segments.append(ids)
    mask=np.zeros(len(r),bool)
    for ids in segments:mask[ids]=True
    mask=candidate_support_mask(r,mask)
    # The candidate gate removes whole groups, thus never shortens a segment.
    return [ids for ids in segments if mask[ids].all()],mask


def shift_permutation(n,segments,seed):
    rng=np.random.default_rng(seed);order=np.arange(n)
    for ids in segments:
        if len(ids)<100:raise ValueError('B_SHIFT_SHORT_SEGMENT')
        shift=int(rng.integers(20,len(ids)-19));order[ids]=np.roll(ids,shift)
    return order


def _predictions(models,features,rows,fold,analysis):
    output=[]
    for name,model in models.items():
        for calibration,p in model.predict(rows,None if features[name] is None else features[name]).items():
            part=rows[['trial_id','record_id','candidate_id','split_group_id','history_target']].copy()
            part['model']=name;part['probability_mode']=calibration;part['analysis_set']=analysis;part['outer_fold']=fold
            part['p0']=p[:,0];part['p1']=p[:,1];output.append(part)
    return pd.concat(output,ignore_index=True)


def _core_features(pre,post):
    return dict(B0_context_linear=None,B0_context_spline=None,B1_pre=pre,B2_post=post,B3_pre_post=np.c_[pre,post])


def _readout_path(core,mode,fold):
    return core/f'fold_{fold}_all_readouts.pkl' if mode=='L0' else core/mode/f'outer{fold}_all_readouts.pkl'


def _core_predictions(core,mode):
    path=core/'oof_history_predictions.parquet' if mode=='L0' else core/mode/'oof_history_predictions.parquet'
    frame=pd.read_parquet(path);return frame[frame.analysis_set.eq('all')]


def run(config,split_run,representation_plan,modes,core_runs,output_dir):
    require_slurm();dest=Path(output_dir)
    if not dest.resolve().is_relative_to(ROOT/'private'):raise ValueError('B_CONTROL_PRIVATE_ONLY')
    dest.mkdir(parents=True,exist_ok=False);base=ROOT/config['paths']['private_relative']
    planpath=Path(representation_plan);plan=json.loads(planpath.read_text());splitpath=base/'splits'/split_run/'folds.json'
    split=json.loads(splitpath.read_text());support=pd.read_parquet(splitpath.parent/'support.parquet')
    if digest(splitpath)!=plan['split_hash'] or object_hash(config)!=plan['config_hash']:raise ValueError('B_CONTROL_PLAN_CHANGED')
    hashes={str(planpath):digest(planpath),str(splitpath):digest(splitpath)}
    for row in support[support.B].to_dict('records'):
        path=base/'data'/split['export_run']/'P1_CAUSAL20'/row['record_id']/'summary.json'
        if digest(path)!=split['input_hashes']['P1_CAUSAL20/'+row['record_id']]:raise ValueError('B_CONTROL_EXPORT_CHANGED')
        meta=json.loads(path.read_text())
        for name,h in meta['output_sha256'].items():
            if digest(path.parent/name)!=h:raise ValueError('B_CONTROL_EXPORT_ARRAY_CHANGED')
        hashes[str(path)]=digest(path)
    data=load_dataset(split['export_run'],support,window='epoch',route='B')
    windows=reaction_windows(data.X,data.rows);raw_pre,raw_post=_features(data)
    original=[]
    for row in support[support[['general','A','B','D']].any(axis=1)].to_dict('records'):
        p=base/'data'/split['export_run']/'P1_CAUSAL20'/row['record_id']/'events.parquet'
        events=pd.read_parquet(p,columns=list(ROW_COLUMNS));original.append(events[events.accepted.eq(True)])
    original=pd.concat(original,ignore_index=True);selected=np.flatnonzero(history_eligible(data.rows))
    rows=data.rows.iloc[selected].reset_index(drop=True).copy()
    rows['pre_ptp_uv']=np.ptp(data.X[selected,:,:50],axis=-1).max(axis=-1)
    raw_lookup={v:i for i,v in enumerate(data.trial_ids)};summaries={}
    for mode in modes:
        if mode not in ['L0','R_SUP','R_SIM','R_RAND']:raise ValueError('B_CONTROL_MODE')
        core=Path(core_runs[mode]);core=core if core.is_absolute() else base/'routes'/core
        if not (core/'completion.json').exists():raise ValueError('B_CORE_NOT_COMPLETE')
        baseline=_core_predictions(core,mode);folder=dest/mode;folder.mkdir();predictions=[];shift_losses=[];flows=[];context_rows=[]
        for fold in split['folds']:
            number=fold['outer_fold'];scope=FitScope(tuple(fold['train_groups']),test_groups=tuple(fold['test_groups']))
            if mode=='L0':
                pre,post=raw_pre[selected],raw_post[selected];early=bin_20ms(windows['early'][selected]);late=bin_20ms(windows['late'][selected])
            else:
                payload,ledger,_,checked=_load_fold(plan,planpath,fold,mode,support,original);hashes.update(checked)
                lookup={v:i for i,v in enumerate(ledger.trial_id)};ix=np.array([lookup[v] for v in rows.trial_id])
                pre,post=payload['pre'][ix],payload['post'][ix]
                encoder=FittedEncoder.load(planpath.parent/'outputs'/f'outer{number}_all_{mode}'/'encoder.pt',device='cpu')
                early=encoder.transform(windows['early'][selected]);late=encoder.transform(windows['late'][selected]);del encoder,payload,ledger
            train=np.flatnonzero(rows.split_group_id.isin(scope.train_groups));test=np.flatnonzero(rows.split_group_id.isin(scope.test_groups))
            a,b,gate=select_common_support(rows.iloc[train],rows.iloc[test],scope);train,test=train[a],test[b]
            tr,te=rows.iloc[train].reset_index(drop=True),rows.iloc[test].reset_index(drop=True)
            expected=baseline[baseline.outer_fold.eq(number)].trial_id.unique()
            if set(te.trial_id)!=set(expected):raise ValueError('B_CONTROL_CHANGED_CORE_TEST_COHORT')
            flow={'outer_fold':number,'eligible_test_rows_before_support':int(rows.split_group_id.isin(scope.test_groups).sum()),
                  'retained_test_rows':len(te),'test_groups':int(te.split_group_id.nunique()),'train_groups':int(tr.split_group_id.nunique()),'diagnostics':{}}
            for h,part in te.groupby('history_target'):
                for group,r in part.groupby('split_group_id'):
                    context_rows.append({'outer_fold':number,'split_group_id':group,'H':int(h),'n':len(r),
                        'gap_mean':float(r.previous_gap_s.mean()),'position_mean':float(r.segment_position_fraction.mean())})
            for diagnostic,window in [('early',early),('late',late),('quality',post)]:
                features=_core_features(pre,window);trainfeatures={k:None if v is None else v[train] for k,v in features.items()}
                try:
                    models=fit_quality_readouts(tr,trainfeatures,scope,split['seed']) if diagnostic=='quality' else fit_history_readouts(tr,trainfeatures,scope,seed=split['seed'])
                except ValueError as exc:
                    if not str(exc).startswith('B_INNER_SUPPORT'):raise
                    flow['diagnostics'][diagnostic]='SUPPORT_INSUFFICIENT';continue
                out=_predictions(models,{k:None if v is None else v[test] for k,v in features.items()},te,number,diagnostic)
                predictions.append(out);flow['diagnostics'][diagnostic]='PASS'
                with (folder/f'outer{number}_{diagnostic}_readouts.pkl').open('xb') as stream:pickle.dump(models,stream)
            path=_readout_path(core,mode,number);hashes[str(path)]=digest(path)
            with path.open('rb') as stream:primary=pickle.load(stream)
            segments,keep=stable_shift_segments(te);flow['circular_shift_groups']=int(te.loc[keep,'split_group_id'].nunique());flow['stable_shift_segments']=len(segments)
            if keep.any():
                core_features=_core_features(pre[test],post[test]);observed=_predictions(primary,core_features,te,number,'circular_observed')
                predictions.append(observed[observed.trial_id.isin(te.loc[keep,'trial_id'])])
                for repeat in range(20):
                    order=shift_permutation(len(te),segments,split['seed']+repeat+1000*number)
                    shifted=primary['B2_post'].predict(te,post[test][order])
                    for cal,prob in shifted.items():
                        losses=candidate_log_losses_bits(te.loc[keep,'history_target'].to_numpy(int),prob[keep],te.loc[keep,'split_group_id'].to_numpy(str),te.loc[keep,'trial_id'].to_numpy(str))
                        shift_losses.extend({'split_group_id':g,'probability_mode':cal,'repeat':repeat,'ce_bits':v,'outer_fold':number} for g,v in losses.items())
            flow['diagnostics']['circular_shift']='PASS' if keep.any() else 'SUPPORT_INSUFFICIENT';flows.append(flow)
            print(json.dumps({'B_control_mode':mode,'outer_fold':number,'test_groups':flow['test_groups']}),flush=True)
        frame=pd.concat(predictions,ignore_index=True) if predictions else pd.DataFrame();frame.to_parquet(folder/'oof_diagnostics.parquet',index=False)
        losses,comparisons=_summaries(frame,split['seed']);losses.to_parquet(folder/'candidate_losses.parquet',index=False)
        shifted=pd.DataFrame(shift_losses);shifted.to_parquet(folder/'shift_losses.parquet',index=False);shift_summary=[]
        if len(shifted):
            avg=shifted.groupby(['split_group_id','probability_mode']).ce_bits.mean()
            for cal in ['raw','calibrated']:
                own=losses[losses.analysis_set.eq('circular_observed') & losses.model.eq('B2_post') & losses.probability_mode.eq(cal)].set_index('split_group_id').ce_bits
                other=avg.xs(cal,level='probability_mode').reindex(own.index)
                if other.isna().any():raise ValueError('B_SHIFT_UNPAIRED')
                ci=paired_cluster_bootstrap(other,own,own.index,n_boot=2000,seed=split['seed'])
                shift_summary.append({'probability_mode':cal,'contrast':'mean_shifted_post_CE_minus_original_post_CE','not_a_permutation_p_value':True,**ci})
        ctx=pd.DataFrame(context_rows);ctx.to_parquet(folder/'context_by_candidate.parquet',index=False)
        balance=[]
        for h,part in ctx.groupby('H'):
            balance.append({'H':int(h),'candidate_groups':len(part),'gap_mean_candidate_equal':float(part.gap_mean.mean()),'gap_sd_across_candidate_means':float(part.gap_mean.std()),
                'position_mean_candidate_equal':float(part.position_mean.mean()),'position_sd_across_candidate_means':float(part.position_mean.std())})
        write_json(folder/'flows.json',flows)
        summaries[mode]={'comparisons':comparisons,'circular_shift':shift_summary,'context_balance':balance,
            'completed_fold_diagnostics':{d:sum(f['diagnostics'].get(d)=='PASS' for f in flows) for d in ['early','late','quality','circular_shift']},
            'retained_common_support_fraction':sum(f['retained_test_rows'] for f in flows)/sum(f['eligible_test_rows_before_support'] for f in flows)}
    for path,h in hashes.items():
        if digest(path)!=h:raise ValueError('B_CONTROL_INPUT_CHANGED')
    write_json(dest/'input_hashes.json',hashes)
    summary={'stage':'B_prespecified_diagnostics','status':'DIAGNOSTICS_RECORDED','modes':summaries,
        'scope':'fixed outer encoder, inner readout-only CV, paired OOF diagnostics; no new primary screen',
        'clinical_claim':None,'circular_shift_interpretation':'descriptive feature-alignment sensitivity, not CMI significance'}
    write_json(dest/'aggregate.json',summary);return summary
