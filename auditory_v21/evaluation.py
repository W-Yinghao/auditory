"""Locked independent capability evaluation; no participant outcomes fitted."""
import json
import os
import time
import traceback
import numpy as np
import pandas as pd
from scipy.stats import beta
from .runtime import require_slurm,write_json,digest
from .worlds import generate
from .estimator import fit_pipeline
from .fit_ledger import FitLedger
from .capability import score_world


CORE_SOURCES=('auditory_v21/estimator.py','auditory_v21/fit_ledger.py',
              'auditory_v21/capability.py','auditory_v21/worlds.py','auditory_v21/evaluation.py')


def binomial_interval(successes,total):
    if total<1:return [None,None]
    return [float(beta.ppf(.025,successes,total-successes+1)) if successes else 0.,
            float(beta.ppf(.975,successes+1,total-successes)) if successes<total else 1.]


def judge_world(packet,world,rate,rows,losses,thresholds):
    pairs={(row['first'],row['second']):row for row in rows}
    primary=[('HP','HPB'),('HB','HPB')] if packet=='N1' else [('H','HP')]
    controls=[('HPBnoise','HPB'),('HPP','HPB')] if packet=='N1' else [('Hnoise','HP'),('Hdup','HP')]
    positive=world in ('trial_key','group_key','additive_background','strong_history_increment') or world.endswith('_weak')
    if packet=='N1' and world=='independent_background':primary=[('HP','HPB')]
    necessary=primary+controls
    if any(pair not in pairs for pair in necessary):raise ValueError('REQUIRED_CONTROL_MISSING')
    prior_entropy=-(rate*np.log2(rate)+(1-rate)*np.log2(1-rate))
    baseline_ok=all(losses[first]<=prior_entropy-thresholds['minimum_baseline_gain_over_class_prior_bits'] for first,_ in primary)
    if world=='near_deterministic':
        baseline_ok=losses['H']<=thresholds['near_deterministic_maximum_baseline_risk_bits']
    def recovered(pair,minimum):
        r=pairs[pair]
        return r['estimate']>=minimum and r['ci_lower']>thresholds['positive_ci_lower_strictly_above']
    gains=[pairs[pair]['estimate'] for pair in primary]
    raw_fp=any(pairs[pair]['ci_lower']>0 for pair in primary)
    meaningful_fp=any(pairs[pair]['ci_lower']>0 and pairs[pair]['estimate']>thresholds['meaningful_false_positive_gain_bits'] for pair in primary)
    return dict(kind='WEAK_DESCRIPTIVE' if world.endswith('_weak') else ('POSITIVE' if positive else 'NULL'),
        recovered=bool(baseline_ok and all(recovered(pair,thresholds['minimum_positive_gain_bits']) for pair in primary)
            and all(recovered(pair,thresholds['minimum_control_margin_bits']) for pair in controls)),
        baseline_ok=bool(baseline_ok),unthresholded_false_positive=bool(raw_fp),
        meaningful_false_positive=bool(meaningful_fp),worst_primary_gain=float(min(gains)),
        risk_preserved=bool(baseline_ok and min(gains)>=-thresholds['null_maximum_loss_increase_bits']))


def summarize_cells(execution,worlds,rates,thresholds,replicates):
    output=[]
    for world in worlds:
        for rate in rates:
            planned=[r for r in execution if r['world']==world and r['rate']==rate]
            valid=[r for r in planned if r['status']=='COMPLETE']
            kind='WEAK_DESCRIPTIVE' if world.endswith('_weak') else (
                'POSITIVE' if world in ('trial_key','group_key','additive_background','strong_history_increment') else 'NULL')
            successes=sum(r['judgment']['recovered'] for r in valid)
            fp=sum(r['judgment']['meaningful_false_positive'] for r in valid)
            rawfp=sum(r['judgment']['unthresholded_false_positive'] for r in valid)
            preservation=sum(r['judgment']['risk_preserved'] for r in valid)
            mean_gain=float(np.mean([r['judgment']['worst_primary_gain'] for r in valid])) if valid else None
            complete=len(planned)==replicates and len(valid)==replicates
            if kind=='WEAK_DESCRIPTIVE':status='DESCRIPTIVE_ONLY' if complete else 'DESCRIPTIVE_WITH_FAILURES'
            elif kind=='POSITIVE':status='PASS' if complete and successes>=thresholds['minimum_positive_recoveries_per_20'] else 'FAIL'
            else:status='PASS' if complete and fp<=thresholds['maximum_meaningful_false_positives_per_20'] and preservation>=thresholds['minimum_null_risk_preservations_per_20'] and mean_gain>=-thresholds['null_maximum_mean_loss_increase_bits'] else 'FAIL'
            output.append(dict(world=world,rate=rate,kind=kind,planned=replicates,evaluable=len(valid),
                unevaluable=replicates-len(valid),recoveries=successes,recovery_rate=successes/replicates,
                recovery_95ci=binomial_interval(successes,replicates),meaningful_false_positives=fp,
                false_positive_95ci=binomial_interval(fp,replicates),unthresholded_false_positives=rawfp,
                unthresholded_false_positive_95ci=binomial_interval(rawfp,replicates),
                risk_preservations=preservation,mean_worst_primary_gain=mean_gain,status=status))
    return output


def load_cases(path):
    data=json.loads(path.read_text())
    return data if isinstance(data,list) else data['cases']


def run(root,private,public,report,config):
    require_slurm()
    if config['phase']!='INDEPENDENT_CAPABILITY_EVALUATION':raise ValueError('EVALUATION_LOCK_REQUIRED')
    lane=os.environ.get('AUDITORY_V21_LANE','');plan=config['evaluation'];alg=config['algorithm']
    if lane not in plan['lanes']:raise ValueError('FROZEN_LANE_REQUIRED')
    packet,mode=lane.split('_',1);budget=plan['lanes'][lane]
    if private.name!=budget['run']:raise ValueError('EVALUATION_RUN_NAME_MISMATCH')
    preflight=root/'private/auditory_v21'/config['input_preflight_run']
    preflight_completion=json.loads((preflight/'completion.json').read_text())
    manifest_path=preflight/'cases.json';cases=load_cases(manifest_path)
    profiles=sorted([c for c in cases if c['packet']==packet and c['mode']==mode],key=lambda c:c['outer_fold'])
    start=json.loads((private/'start.json').read_text())
    source_hashes={p:start['source_hashes'][p] for p in CORE_SOURCES}
    receipt=dict(estimator_id=alg['id'],packet=packet,mode=mode,lane=lane,
        artifact_integrity_status='PASS',source_hashes=source_hashes,algorithm=alg,
        evaluation_config_hash=start['config_hash'],input_preflight_run=config['input_preflight_run'],
        input_manifest_hash=digest(manifest_path),preflight_receipt_hash=digest(preflight/'completion.json'),
        dimensions=dict(H=25,**plan['dimensions'][mode]),population='P_nat',clinical_inputs=False,
        new_encoder_fits=0,participant_fits=0,thresholds=config['thresholds'])
    if preflight_completion.get('status')!='PASS' or len(profiles)!=5 or {p['outer_fold'] for p in profiles}!=set(range(5)) or any(p.get('status')!='PASS' for p in profiles):
        receipt.update(capability_status='NOT_EVALUATED_SOURCE_OR_SUPPORT_BLOCKED',support_status='BLOCKED',
            budget_execution_status='NOT_STARTED',worlds_planned=budget['worlds'],worlds_evaluated=0,head_fits=0,real_gate_open=False)
        write_json(public/'capability_receipt.json',receipt)
        (report/'CAPABILITY_REPORT.md').write_text('# Independent capability\n\nSource/support preflight did not pass all five folds; no capability world fitted and no real comparison authorized.\n')
        return receipt
    catalog=[]
    for rate_index,rate in enumerate(plan['rates']):
        for repetition in range(plan['replicates_per_rate']):
            for world in plan[packet+'_worlds']:
                catalog.append(dict(packet=packet,mode=mode,world=world,rate=rate,
                    seed=220000+rate_index*1000+repetition,outer_profile=repetition%5,
                    head_fits=9 if packet=='N1' else 4))
    if len(catalog)!=budget['worlds'] or sum(c['head_fits'] for c in catalog)!=budget['head_fits']:
        raise ValueError('FROZEN_EVALUATION_CATALOG_MISMATCH')
    if {c['seed'] for c in catalog}&set(plan['development_seeds_excluded']):raise ValueError('DEVELOPMENT_SEED_REUSE')
    write_json(private/'fit_catalog.json',catalog)
    ledger=FitLedger(private/'fit_events.jsonl',dict(head=budget['head_fits'],calibration=budget['calibration_fits'],transform=budget['transform_fits']))
    execution=[];effects=[];max_gradient=0.;optimizer_success=0;heads_complete=0
    for number,case in enumerate(catalog):
        path=private/f'world_{number:03d}';path.mkdir(mode=0o700)
        write_json(path/'start.json',case);began=time.time()
        ledger.begin_world(number,dict(head=case['head_fits'],calibration=3 if packet=='N1' else 1,transform=7))
        profile=profiles[case['outer_profile']]
        try:
            data=generate(packet,case['world'],case['seed'],plan['dimensions'][mode]['P'],case['rate'],
                history_dimension=25,background_dimension=plan['dimensions'][mode]['B'],role_sample_sizes=profile['role_sample_sizes'])
            fitted=fit_pipeline(data['h'],data['p'],data['b'],data['noise'],data['y'],data['groups'],data['roles'],
                packet=packet,lam=alg['lambda_l2'],maxiter=alg['maxiter'],fit_observer=ledger)
            ledger.complete_world()
            rows,losses=score_world(data,fitted,plan['bootstrap_replicates'],plan['bootstrap_seed'])
            for row in rows:row.update(mode=mode,outer_profile=case['outer_profile'])
            effects.extend(rows)
            judgment=judge_world(packet,case['world'],case['rate'],rows,losses,config['thresholds'])
            write_json(path/'fit_receipts.json',fitted['head_receipts'])
            np.savez_compressed(path/'predictions.npz',y=data['y'][data['roles']['E']],groups=data['groups'][data['roles']['E']],
                **fitted['baseline'],**{k:v['logit'] for k,v in fitted['enhanced'].items()})
            heads_complete+=len(fitted['head_receipts'])
            optimizer_success+=sum(r['optimizer_success'] for r in fitted['head_receipts'])
            max_gradient=max(max_gradient,max(r['gradient_norm'] for r in fitted['head_receipts']))
            record=dict(**case,status='COMPLETE',judgment=judgment,role_counts=fitted['role_counts'],losses=losses,
                selected={k:v['selected'] for k,v in fitted['enhanced'].items()},prediction_hash=digest(path/'predictions.npz'))
        except Exception as exc:
            (path/'traceback.txt').write_text(traceback.format_exc())
            record=dict(**case,status='FAILED',exception_type=type(exc).__name__)
        record['seconds']=time.time()-began;record['fit_counts']={k:dict(v) for k,v in ledger.world_counts.items()}
        write_json(path/'completion.json',record);execution.append(record)
        write_json(private/'progress.json',dict(worlds_finished=len(execution),worlds_planned=len(catalog),
            worlds_failed=sum(r['status']=='FAILED' for r in execution),fit_counts=ledger.summary()))
        print(json.dumps(dict(index=number,lane=lane,world=case['world'],status=record['status'])),flush=True)
    cells=summarize_cells(execution,plan[packet+'_worlds'],plan['rates'],config['thresholds'],plan['replicates_per_rate'])
    gate=all(c['status']=='PASS' for c in cells if c['kind']!='WEAK_DESCRIPTIVE')
    failures=sum(r['status']=='FAILED' for r in execution)
    receipt.update(capability_status='PASS' if gate else 'FAIL',support_status='SOURCE_PROFILES_PASS',
        finite_prediction_status='PASS' if not failures else 'INCOMPLETE',budget_execution_status='COMPLETE' if not failures else 'WITH_FAILURES',
        optimization_diagnostics=dict(heads_completed=heads_complete,optimizer_success=optimizer_success,max_gradient_norm=max_gradient),
        worlds_planned=len(catalog),worlds_evaluated=len(catalog)-failures,unevaluable=failures,fit_counts=ledger.summary(),
        cells=cells,real_gate_open=bool(gate),control_status='PASS' if gate else 'CAPABILITY_CRITERIA_NOT_ALL_MET')
    pd.DataFrame(effects).to_csv(public/'paired_effects.csv',index=False)
    write_json(public/'world_execution.json',execution);write_json(public/'capability_receipt.json',receipt)
    lines=['# Independent capability evaluation','',f'{lane}: **{receipt["capability_status"]}**. Fixed seeds and thresholds; no participant outcomes fitted.','',
        '| World | Rate | Evaluable | Recoveries | Meaningful FP | Raw FP | Risk preserved | Status |',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    for c in cells:lines.append(f'| {c["world"]} | {c["rate"]} | {c["evaluable"]}/{c["planned"]} | {c["recoveries"]} | {c["meaningful_false_positives"]} | {c["unthresholded_false_positives"]} | {c["risk_preservations"]} | {c["status"]} |')
    lines+=['','FP counts have their zero-information interpretation only on NULL rows; positive and weak rows retain the same diagnostic counters without claiming false positives. Exact binomial intervals and all denominators are in capability_receipt.json. Strong identifiability fixtures do not establish weak real-data power. No failed-world subset can authorize a real route.','']
    (report/'CAPABILITY_REPORT.md').write_text('\n'.join(lines))
    return {k:v for k,v in receipt.items() if k!='cells'}
