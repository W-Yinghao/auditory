"""Versioned repair of the linear-only summary; never refit existing C models."""
import argparse,json,shutil
import pandas as pd
from auditory5.provenance import ROOT,require_slurm,digest,write_json
from auditory5.routes.route_c import summarize_losses,screen


def main():
    require_slurm();p=argparse.ArgumentParser();p.add_argument('--source-run',required=True);p.add_argument('--run',required=True);p.add_argument('--contracts',required=True);a=p.parse_args()
    base=ROOT/'private/auditory5_v1';public=ROOT/'results/auditory5_v1';source=base/'routes'/a.source_run
    gate=json.loads((public/a.contracts/'validation.json').read_text())
    if gate['status']!='PASS' or digest(ROOT/'auditory5/routes/route_c.py')!=gate['code_hashes']['auditory5/routes/route_c.py']:raise ValueError('Untested C summary repair')
    contract=json.loads((source/'run_contract.json').read_text());failure=json.loads((source/'failure.json').read_text())
    if not contract['linear_only_partial'] or failure['detail']!='C_CAPACITY_SUPPORT: incomplete expanded single heads':raise ValueError('Repair is restricted to the observed linear-only aggregation error')
    planpath=base/'jobs/plan_001/plan.json';plan=json.loads(planpath.read_text());split=json.loads((base/'splits'/plan['split_run']/'folds.json').read_text())
    if digest(planpath)!=contract['plan_hash']:raise ValueError('Source plan changed')
    hashes=json.loads((source/'input_hashes.json').read_text())
    for path,h in hashes.items():
        if digest(path)!=h:raise ValueError('Frozen C inputs changed')
    for mode in contract['modes']:
        coverage=[v for v in failure['coverage'] if v['representation']==mode]
        if {v['outer_fold'] for v in coverage}!=set(range(len(split['folds']))) or any(v['status']!='COMPLETE_FOLD' for v in coverage):raise ValueError('Incomplete C fitting cannot be repaired by aggregation')
        for fold in split['folds']:
            if not (source/f'outer{fold["outer_fold"]}_{mode}_heads.pkl').is_file():raise ValueError('Missing fitted C heads')
    losses=pd.read_parquet(source/'candidate_losses.parquet')
    if set(losses.family)!={'linear'}:raise ValueError('Unexpected family in linear-only repair')
    expected=set(pd.read_parquet(base/'splits'/plan['split_run']/'support.parquet').query('C').split_group_id)
    for _,group in losses[losses.intervention.eq('none')].groupby(['representation','probability_mode','model']):
        if set(group.split_group_id)!=expected or not group.split_group_id.is_unique:raise ValueError('C complete candidate cohort required')
    gains,interventions=summarize_losses(losses,split['seed'],families=('linear',))
    dest=base/'routes'/a.run;out=public/a.run;dest.mkdir(parents=True,exist_ok=False);out.mkdir(parents=True,exist_ok=False)
    for filename in ['candidate_losses.parquet','fit_scopes.json','run_contract.json','input_hashes.json']:shutil.copyfile(source/filename,dest/filename)
    for filename in ['classification_metrics.csv','coverage.csv','input_isolation_tests.json','synthetic_controls.json']:shutil.copyfile(public/a.source_run/filename,out/filename)
    pd.DataFrame(gains).to_csv(out/'single_joint_gains.csv',index=False)
    pd.DataFrame([r for r in gains if 'margin' in r['statistic']]).to_csv(out/'capacity_controls.csv',index=False)
    pd.DataFrame(interventions).to_csv(out/'fixed_head_interventions.csv',index=False)
    summary=screen(gains,['all nonlinear heads and expanded capacity controls; linear-only computational fallback'])
    summary.update(stage='C_PAIRED_READOUT',evaluated_modes=contract['modes'],completed_model_folds=len(failure['coverage']),
        source_fit_run=a.source_run,repair='aggregate explicit linear family; no refitting or changed predictions',
        uncertainty='2000 fixed OOF cluster draws, not full-workflow refitting')
    write_json(out/'summary.json',summary)
    write_json(dest/'completion.json',{'status':summary['status'],'source_fit_run':a.source_run,
        'source_loss_sha256':digest(source/'candidate_losses.parquet'),'source_contract_sha256':digest(source/'run_contract.json'),
        'aggregation_code_sha256':digest(ROOT/'auditory5/routes/route_c.py')})
    print(json.dumps({'run':a.run,'status':summary['status'],'refitted_models':0}),flush=True)

if __name__=='__main__':main()
