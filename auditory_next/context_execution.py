"""N1/N3 fixed-readout matrices with explicitly partial, encoder-isolated OOF.

No clinical outcome enters this runner. Existing D-inner validation groups
provide calibration predictions only where they are explicitly unseen by the
encoder. Uncovered outer-training groups are never silently relabeled OOF.
"""
import json
import pickle
import numpy as np
import pandas as pd
import torch
from scipy.special import expit

from .provenance import ROOT,digest,object_hash,write_json,finish,require_slurm
from .features import LegacyFeatureRegistry,audit_inner_scope
from .readouts import population_weights,calibrate,ce_bits
from .fitting import fit_cases,predict_logits,array_hash
from .context_inputs import history_matrix,independent_noise,context_views,fit_context_inputs,donor_indices
from .n1_controls import AUX_VIEWS,prepare_matched,fixed_head_inputs


def _calibrated_logit(z,cal,kind):
    if kind=='raw':return z
    z=z/cal['temperature']
    if kind=='temperature':return z
    eta=cal['eta'];prior=cal['training_prior']
    if eta==0:return z
    l0=-np.logaddexp(0.,z);l1=-np.logaddexp(0.,-z)
    if eta==1:return np.full(len(z),np.log(prior/(1-prior)))
    return np.logaddexp(l1+np.log1p(-eta),np.log(eta*prior))-np.logaddexp(l0+np.log1p(-eta),np.log(eta*(1-prior)))


def candidate_losses(predictions,population):
    result=[]
    for group,rows in predictions.groupby('split_group_id',sort=True):
        y=rows.stimulus_local_id.to_numpy(int);z=rows.logit.to_numpy(float)
        w=population_weights(y,np.full(len(y),group),population)
        p=expit(z);hard=z>=0
        result.append(dict(split_group_id=group,ce_bits=ce_bits(z,y,w),
                           brier=float(np.average(2*(p-y)**2,weights=w)),
                           bacc=float(np.mean([hard[y==label].mean() if label else (~hard[y==label]).mean() for label in (0,1)])),
                           n_trials=len(rows)))
    return pd.DataFrame(result)


def paired_effect(loss_table,first,second,*,n_boot=2000):
    table=loss_table.pivot(index='split_group_id',columns='view',values='ce_bits')
    if first not in table or second not in table or table[[first,second]].isna().any().any():return None
    difference=(table[first]-table[second]).to_numpy(float)
    rng=np.random.default_rng(20260917);ix=rng.integers(0,len(difference),size=(n_boot,len(difference)))
    boots=difference[ix].mean(axis=1)
    return dict(first=first,second=second,estimate=float(difference.mean()),ci_lower=float(np.quantile(boots,.025)),
                ci_upper=float(np.quantile(boots,.975)),n_candidates=len(difference),n_bootstrap=n_boot,
                units='bits_per_trial',ci_scope='fixed_oof_no_refit; shared candidate draws')


def run(config,registry,site,dest,public,report,packet,task_plan,*,modes=('R_SIM','L0'),smoke=False):
    require_slurm()
    if packet not in ('N1','N3'):raise ValueError('CONTEXT_PACKET')
    support=ROOT/'private/auditory_next_v2'/task_plan['support_run']
    if json.loads((support/'completion.json').read_text())['status']!='PASS':raise ValueError('CONTEXT_SUPPORT_GATE')
    metadata=pd.read_parquet(support/'full_event_history.parquet')
    metadata=metadata[metadata.accepted & metadata.history_chain_complete & metadata.stimulus_local_id.isin([0,1])].copy()
    metadata['history_cell']=metadata.previous_code.astype(str)+'|'+metadata.previous_run_bin.astype(str)
    n1groups=set(json.loads((support/'N1_groups.json').read_text()))
    n3=json.loads((support/'N3_outer_support.json').read_text())
    planpath=ROOT/registry['legacy_plan'];legacy=json.loads(planpath.read_text())
    folds=json.loads((ROOT/registry['legacy_splits']).read_text())['folds']
    gate=ROOT/'private/auditory_next_v2'/task_plan['preflight_run']
    features=LegacyFeatureRegistry.from_files(planpath,gate/'feature_scope_registry.json')
    hashes={r['path']:r['sha256'] for r in json.loads((gate/'legacy_input_hashes.json').read_text())}
    cases=[];evaluate={};transforms={};scopes=[];donor_records=[];matched_definitions=[]
    device='cuda' if torch.cuda.is_available() else 'cpu'
    if not smoke and device!='cuda':raise ValueError('CONTEXT_NEURAL_MATRIX_REQUIRES_GPU_ALLOCATION')
    views=config[packet]['models']
    # Counts and all masks are determined without opening any fitted prediction.
    for mode in modes:
        families=('logistic','mlp32') if mode=='R_SIM' else ('logistic',)
        for fold in folds:
            number=fold['outer_fold']
            own=metadata[metadata.split_group_id.isin(n1groups)] if packet=='N1' else metadata[
                metadata.history_cell.isin(n3[number]['omega_H']) & metadata.split_group_id.isin(n3[number]['train_groups']+n3[number]['test_groups'])]
            for inner in (0,1,2,None):
                task=features.resolve_task(stage='outer' if mode=='L0' or inner is None else 'D_inner',mode=mode,branch='all',outer_fold=number,
                                           inner_fold=None if mode=='L0' else inner)
                folder=planpath.parent/'outputs'/task['name']
                for filename in ('features.npz','feature_rows.parquet'):
                    if digest(folder/filename)!=hashes[str(folder/filename)]:raise ValueError('CONTEXT_FEATURE_MUTATION')
                data=features.load_features(task,planpath.parent/'outputs')
                rowframe=pd.DataFrame(data['rows']);lookup=pd.Series(np.arange(len(rowframe)),index=rowframe.trial_id.astype(str))
                if not set(own.trial_id)<=set(lookup.index):raise ValueError('CONTEXT_FROZEN_SUPPORT_MISSING_FEATURES')
                rows=own.sort_values('trial_id').reset_index(drop=True)
                ix=lookup.loc[rows.trial_id].to_numpy(int)
                p,b=data['zpost'][ix].astype(float),data['zpre'][ix].astype(float)
                h,hcolumns=history_matrix(rows)
                eligible=set(rows.split_group_id)
                val=set() if inner is None else {g for g,i in fold['D_inner_fold_by_group'].items() if i==inner}&eligible
                train=(set(fold['train_groups'])&eligible)-val
                test=set(fold['test_groups'])&eligible
                if inner is not None and mode!='L0':audit_inner_scope(features.scope_for(task),val,data['actual_fit_groups'],fold['train_groups'])
                if set(data['actual_fit_groups'])&test:raise ValueError('CONTEXT_OUTER_ENCODER_LEAKAGE')
                if inner is not None and not val:continue
                fitmask=rows.split_group_id.isin(train).to_numpy(); evalmask=rows.split_group_id.isin(test if inner is None else val).to_numpy()
                if not fitmask.any() or not evalmask.any():raise ValueError('CONTEXT_EMPTY_FROZEN_FOLD')
                yy=rows.stimulus_local_id.to_numpy(int);gg=rows.split_group_id.to_numpy(str)
                scope=dict(fit_groups=sorted(train),validation_groups=sorted(val),test_groups=sorted(test))
                scopes.append(dict(mode=mode,outer_fold=number,inner_fold=inner,inner_validation_groups=len(val),
                                    outer_training_groups=len(set(fold['train_groups'])&eligible),scope=scope,feature_scope_id=data['feature_scope_id']))
                for population in ('P_nat','P_bal'):
                    weights=population_weights(yy[fitmask],gg[fitmask],population)
                    transform=fit_context_inputs(h[fitmask],p[fitmask],b[fitmask],weights,mode=mode)
                    hp=transform['H'].transform(h);pp=transform['P'].transform(p);bp=transform['B'].transform(b)
                    base=bp if packet=='N1' else pp
                    center=np.average(base[fitmask],axis=0,weights=weights);scale=np.sqrt(np.average((base[fitmask]-center)**2,axis=0,weights=weights))
                    noise=independent_noise(rows.trial_id,base.shape[1],namespace=packet+'_noise')*scale+center
                    composed=context_views(hp,pp,bp,noise,packet)
                    transform_key=f'{mode}_f{number}_i{inner}_{population}'
                    transforms[transform_key]=dict(transforms=transform,H_columns=hcolumns,feature_scope_id=data['feature_scope_id'],scope=scope)
                    for family in families:
                        for view in views:
                            identifier=f'{transform_key}_{family}_{view}'
                            cases.append(dict(id=identifier,family=family,x=composed[view][fitmask],y=yy[fitmask],weights=weights,scope=scope,
                                              feature_scope_id=data['feature_scope_id'],width=32))
                            evalcolumns=['trial_id','record_id','split_group_id','stimulus_local_id','previous_run_bin']
                            evaluate[identifier]=dict(x=composed[view][evalmask],rows=rows.loc[evalmask,evalcolumns].reset_index(drop=True),
                                mode=mode,outer_fold=number,inner_fold=inner,population=population,family=family,view=view,transform_key=transform_key)
                    if packet=='N1' and mode=='R_SIM' and population=='P_nat':
                        ac,ae,definition=prepare_matched(h,p,b,rows,fitmask,evalmask,scope,data['feature_scope_id'],transform_key)
                        cases.extend(ac)
                        for identifier,e in ae.items():
                            evaluate[identifier]={**e,'mode':mode,'outer_fold':number,'inner_fold':inner,'population':population,
                                                  'family':'mlp32','transform_key':transform_key}
                        matched_definitions.append(dict(mode=mode,outer_fold=number,inner_fold=inner,**definition))
                    # Donor maps are frozen from metadata here, before any head
                    # fitting. Fixed-head donor interventions use the complete
                    # common supported test subset and retain its coverage.
                    if packet=='N1' and population=='P_nat' and mode=='R_SIM' and inner is None:
                        query=rows.loc[evalmask].reset_index(drop=True);pool=rows.loc[fitmask].reset_index(drop=True)
                        same,ns=donor_indices(query,query,role='same_child')
                        cross,nc=donor_indices(query,pool,role='training_child')
                        common=(same>=0)&(cross>=0)
                        ct=query.loc[common].groupby(['split_group_id','stimulus_local_id']).size().unstack(fill_value=0)
                        good=set(ct.index[(ct.get(0,0)>=20)&(ct.get(1,0)>=20)])
                        common &= query.split_group_id.isin(good).to_numpy()
                        donor_records.append(dict(outer_fold=number,query_rows=query,same=same,cross=cross,common=common,fit_rows=pool,
                                                  bp_query=bp[evalmask],bp_fit=bp[fitmask],hp=hp[evalmask],pp=pp[evalmask],counts_same=ns,counts_cross=nc))
                if smoke:break
            if smoke:break
        if smoke:break
    # Persist input manifests before training; total fits must fit the frozen
    # reservation. Donor-matched training has a separate follow-up reservation.
    catalog=pd.read_csv(task_plan['task_csv'])
    allowance=catalog[(catalog.packet==packet)&catalog['mode'].isin(modes)&catalog.fit_stage.isin(['inner','final'])]
    if not smoke and len(cases)!=len(allowance):raise ValueError('CONTEXT_TASK_PLAN_CASE_COUNT')
    write_json(dest/'case_manifest.json',[{k:c[k] for k in ('id','family','scope','feature_scope_id')}|dict(shape=list(c['x'].shape)) for c in cases])
    write_json(dest/'inner_scope_coverage.json',scopes)
    with (dest/'transforms.pkl').open('xb') as f:pickle.dump(transforms,f)
    with (dest/'donor_maps.pkl').open('xb') as f:pickle.dump(donor_records,f)
    with (dest/'matched_donor_definitions.pkl').open('xb') as f:pickle.dump(matched_definitions,f)
    if smoke:
        # The smoke is an input/scope/transform integration gate, not a model
        # search. It deliberately performs no fit or test-effect evaluation.
        return finish(dest,public,dict(status='PASS',scope='metadata-selected first fold/inner/population input integration',
                      generated_cases=len(cases),head_fits=0,encoder_fits=0,all_inputs_finite=all(np.isfinite(c['x']).all() for c in cases)))
    models,receipts=fit_cases(cases,dest/'fits',device=device,expected_fits=len(cases))
    receipt_by_id={r['fit_id']:r for r in receipts};outputs=[];calibrations=[];losses=[];effects=[];numerical=[]
    for mode in modes:
        for population in ('P_nat','P_bal'):
            for family in (('logistic','mlp32') if mode=='R_SIM' else ('logistic',)):
                ids=[i for i,e in evaluate.items() if (e['mode'],e['population'],e['family'])==(mode,population,family)]
                complete=all(receipt_by_id[i]['numerical_status']=='OPTIMIZATION_STABLE' for i in ids)
                numerical.append(dict(mode=mode,population=population,family=family,complete=complete,fit_count=len(ids)))
                if not complete:continue
                family_views=list(views)+(list(AUX_VIEWS) if packet=='N1' and (mode,population,family)==('R_SIM','P_nat','mlp32') else [])
                family_rows=[]
                for outer in range(5):
                    for view in family_views:
                        matching=[i for i in ids if evaluate[i]['outer_fold']==outer and evaluate[i]['view']==view]
                        inner_ids=[i for i in matching if evaluate[i]['inner_fold'] is not None]
                        final_ids=[i for i in matching if evaluate[i]['inner_fold'] is None]
                        if len(final_ids)!=1:raise ValueError('CONTEXT_FINAL_MODEL_UNIQUE')
                        fid=final_ids[0];e=evaluate[fid]
                        if inner_ids:
                            inrows=pd.concat([evaluate[i]['rows'] for i in inner_ids],ignore_index=True)
                            if not inrows.trial_id.is_unique:raise ValueError('CONTEXT_INNER_OOF_DUPLICATE')
                            z=np.concatenate([predict_logits(models[i],evaluate[i]['x']) for i in inner_ids])
                            w=population_weights(inrows.stimulus_local_id.to_numpy(),inrows.split_group_id.to_numpy(),population)
                            c=next(c for c in cases if c['id']==fid)
                            prior=float(np.average(c['y'],weights=c['weights']))
                            cal=calibrate(z,inrows.stimulus_local_id.to_numpy(),w,training_prior=prior)
                            cal['status']='PARTIAL_COVERAGE_ENCODER_ISOLATED_INNER_OOF'
                            cal['inner_ce_bits_raw']=ce_bits(z,inrows.stimulus_local_id.to_numpy(),w)
                            cal['inner_ce_bits_temperature']=ce_bits(z/cal['temperature'],inrows.stimulus_local_id.to_numpy(),w)
                            cal['n_calibration_groups']=int(inrows.split_group_id.nunique())
                        else:
                            c=next(c for c in cases if c['id']==fid)
                            cal=dict(temperature=1.,eta=0.,training_prior=float(np.average(c['y'],weights=c['weights'])),status='UNCALIBRATED_FIXED')
                        calibrations.append(dict(mode=mode,population=population,family=family,view=view,outer_fold=outer,**cal))
                        z=predict_logits(models[fid],e['x'])
                        for kind in ('raw','temperature','mixture_diagnostic'):
                            part=e['rows'].copy();part['logit']=_calibrated_logit(z,cal,kind)
                            part=part.assign(mode=mode,population=population,family=family,view=view,outer_fold=outer,calibration=kind)
                            family_rows.append(part)
                pred=pd.concat(family_rows,ignore_index=True);outputs.append(pred)
                for kind in ('raw','temperature','mixture_diagnostic'):
                    parts=[]
                    for view in family_views:
                        part=candidate_losses(pred[(pred.calibration==kind)&(pred['view']==view)],population).assign(view=view)
                        parts.append(part)
                    loss=pd.concat(parts,ignore_index=True);losses.append(loss.assign(mode=mode,population=population,family=family,calibration=kind))
                    contrasts=[('HP','HPB'),('HB','HPB'),('H','HP'),('H','HB'),('HPP','HPB'),('HPBnoise','HPB')] if packet=='N1' else [('H','HP'),('HB','HBP'),('H','Hnoise')]
                    for first,second in contrasts:
                        effect=paired_effect(loss[loss['view'].isin([first,second])],first,second)
                        if effect:effects.append(dict(packet=packet,mode=mode,population=population,family=family,calibration=kind,**effect))
    controls=[]
    if packet=='N1' and all(receipt_by_id[i]['numerical_status']=='OPTIMIZATION_STABLE' for i,e in evaluate.items()
                           if (e['mode'],e['population'],e['family'])==('R_SIM','P_nat','mlp32')):
        parts=[]
        for record in donor_records:
            outer=record['outer_fold'];fid=f'R_SIM_f{outer}_iNone_P_nat_mlp32_HPB'
            cal=next(c for c in calibrations if (c['mode'],c['population'],c['family'],c['view'],c['outer_fold'])==('R_SIM','P_nat','mlp32','HPB',outer))
            inputs=fixed_head_inputs(record)
            rows=record['query_rows'].loc[record['common'],['trial_id','split_group_id','stimulus_local_id']].reset_index(drop=True)
            for view,x in inputs.items():
                parts.append(rows.assign(logit=predict_logits(models[fid],x)/cal['temperature'],view=view,outer_fold=outer))
        donor_predictions=pd.concat(parts,ignore_index=True)
        donor_predictions.to_parquet(dest/'fixed_head_donor_predictions.parquet',index=False)
        # All fixed-head contrasts share exactly the same candidate/trial subset.
        donor_losses=pd.concat([candidate_losses(r,'P_nat').assign(view=v) for v,r in donor_predictions.groupby('view')],ignore_index=True)
        for view in ('same_child_B','training_child_B'):
            effect=paired_effect(donor_losses[donor_losses['view'].isin([view,'actual_B'])],view,'actual_B')
            if effect:controls.append(dict(control='fixed_head_donor',**effect))
        primary=pd.concat(outputs,ignore_index=True)
        matching=primary[(primary['mode']=='R_SIM')&(primary.population=='P_nat')&(primary.family=='mlp32')&
                         (primary.calibration=='temperature')&primary['view'].isin(AUX_VIEWS)]
        common_trials=set.intersection(*(set(matching.loc[matching['view']==v,'trial_id']) for v in AUX_VIEWS))
        matching=matching[matching.trial_id.isin(common_trials)]
        auxloss=pd.concat([candidate_losses(r,'P_nat').assign(view=v) for v,r in matching.groupby('view')],ignore_index=True)
        effect=paired_effect(auxloss,AUX_VIEWS[1],AUX_VIEWS[0])
        if effect:controls.append(dict(control='matched_training_donor_vs_same_support_reference',**effect))
        write_json(public/'donor_coverage.json',dict(common_fixed_head_trials=int(donor_predictions.trial_id.nunique()),
            common_fixed_head_candidates=int(donor_predictions.split_group_id.nunique()),matched_training_test_trials=len(common_trials),
            interpretation='conditional donor assignment diagnostic; no current-label donor matching'))
    pd.DataFrame(controls).to_csv(public/'donor_controls.csv',index=False)
    if packet=='N3' and outputs:
        from .n3_summary import summarize_selected
        summarize_selected(pd.concat(outputs,ignore_index=True),calibrations,public,dest)
    if outputs:pd.concat(outputs,ignore_index=True).to_parquet(dest/'oof_predictions.parquet',index=False)
    if losses:pd.concat(losses,ignore_index=True).to_parquet(dest/'candidate_losses.parquet',index=False)
    write_json(dest/'calibration.json',calibrations)
    pd.DataFrame(effects).to_csv(public/'paired_effects.csv',index=False)
    pd.DataFrame(numerical).to_csv(public/'numerical_status.csv',index=False)
    write_json(public/'calibration_coverage.json',[{k:v for k,v in c.items() if k not in ('training_prior',)} for c in calibrations])
    (report/(packet+'_CONTEXT_REPORT.md')).write_text('# '+packet+' fixed-readout matrix\n\n'
        'Outer identity folds and task supports are frozen. Training-only transforms and fixed head parameters are fitted separately in each existing encoder coordinate system. '
        'Calibration uses only the declared, encoder-unseen D-inner validation subset; remaining outer-training candidates are included only in fitting, never in calibration evaluation. '
        'This is explicitly partial calibration coverage, not a complete-cohort nested validation. Clinical outcomes are not inputs.\n\n'
        'The complete matrix is retained for each reported head family. A family with any unresolved fit is not summarized over successes. '
        'N1 includes frozen-head donor substitutions and matched-donor training with a same-support reference. N3 family selection uses only training-inner OOF loss. '
        'Synthetic recovery audits remain required before a scientific interpretation.\n')
    return finish(dest,public,dict(status='CORE_MATRIX_RECORDED',packet=packet,head_fits=len(cases),neural_head_fits=sum(c['family']!='logistic' for c in cases),
                  formal_encoder_fits=0,numerical_families=numerical,scientific_status='NOT_EVALUABLE',
                  pending_controls=['synthetic recovery audit']))
