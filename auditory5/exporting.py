"""Signal export coordinator: immutable shards and gated restricted outputs."""
import json,os,traceback
from pathlib import Path
import pandas as pd
from auditory5.provenance import ROOT,digest,object_hash,write_json,require_slurm


def run(config,args):
    require_slurm()
    if not args.run:raise ValueError('--run is required')
    base=ROOT/config['paths']['private_relative']
    gate=ROOT/config['paths']['aggregates_relative']/args.contract_run/'validation.json'
    validation=json.loads(gate.read_text())
    if validation['status']!='PASS':raise RuntimeError('BLOCKED_HARD_GATE: module_contracts')
    spec=json.loads((base/'validation'/args.contract_run/'processing_spec.json').read_text())
    table=pd.read_parquet(base/'data'/args.manifest/'records.parquet')
    locator=pd.read_parquet(base/'data'/args.manifest/'raw_locators.parquet').set_index('record_id').to_dict('index')
    branch='HA_BDF' if args.branch=='HA' else 'MFF'
    if args.branch=='MFF' and args.mff_pairs:
        pairs=pd.read_parquet(base/'data'/args.manifest/'E_existing_pairs.parquet')
        pair_ids=set(pairs.container_a)|set(pairs.container_b)
        selected=table[(table.branch==branch)&table.record_id.isin(pair_ids)].sort_values('record_id')
        if len(selected)!=len(pair_ids):raise ValueError('Missing frozen E0 pair source')
        for row in pairs.to_dict('records'):
            subset=selected[selected.record_id.isin([row['container_a'],row['container_b']])]
            if set(subset.candidate_id)!={row['participant_id']}:raise ValueError('E0 pair identity evidence mismatch')
    else:
        selected=table[(table.branch==branch)&table.analysis_index].sort_values('record_id')
    if args.branch=='MFF':
        probe=json.loads((base/'inputs/mff_probe_001/summary.json').read_text())
        if probe['status']!='PASS':raise ValueError('MFF reader integration hard gate')
        spec={**spec,'mff_view':args.mff_view,'mff_qc_version':'auditory5_mff_qc_v1',
            'mff_qc':{'epoch_over_ptp_fraction_max':.1,'epoch_raw_flat_fraction_max':.1,'record_flat_channel_fraction_max':.1}}
    if args.record_ids:selected=selected[selected.record_id.isin(args.record_ids)]
    if args.limit:selected=selected.head(args.limit)
    selected=selected.iloc[args.shard::args.shards]
    dest=base/'data'/args.run/args.bank;dest.mkdir(parents=True,exist_ok=True)
    shard=dest/f'shard_{args.shard:02d}';shard.mkdir(exist_ok=False)
    write_json(shard/'config.json',{'config':config,'processing':spec,'manifest_hash':digest(base/'data'/args.manifest/'records.parquet'),
        'job_id':os.environ['SLURM_JOB_ID'],'selected_record_ids':selected.record_id.tolist(),
        'code_hashes':{str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'auditory5').rglob('*.py'))}})
    for source in (ROOT/'auditory5').rglob('*.py'):
        target=shard/'source_snapshot'/source.relative_to(ROOT/'auditory5');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
    complete=[];errors=[]
    for row in selected.to_dict('records'):
        try:
            if args.branch=='HA':
                from auditory5.adapters.ha import export_record
                summary=export_record(row,locator[row['record_id']],dest/row['record_id'],args.bank,spec)
            else:
                from auditory5.adapters.mff_export import export_record
                summary=export_record(row,locator[row['record_id']],dest/row['record_id'],args.bank,spec)
            complete.append({'record_id':row['record_id'],'accepted':summary['accepted']})
            print(json.dumps({'completed_records':len(complete),'branch':args.branch,'bank':args.bank}),flush=True)
        except Exception as exc:
            errors.append({'record_id':row['record_id'],'error':repr(exc),'traceback':traceback.format_exc()})
    write_json(shard/'errors.json',errors)
    write_json(shard/'completion.json',{'status':'PASS' if not errors else 'IMPLEMENTATION_FAIL','complete':complete,'errors':len(errors),
        'job_id':os.environ['SLURM_JOB_ID'],'processing_hash':object_hash(spec)})
    if errors:raise RuntimeError('Export failure: see restricted shard errors')
