"""Frozen exposure preparation, three smoke receipts, and exactly30 encoders."""
import hashlib
import json
from pathlib import Path
import numpy as np
from .runtime import Ledger,digest,safe_run,write_json
from .gates import require_tests,require_capability,PACKET_SOURCES
from .data import load_support,load_epochs
from .representation_data import sample_quartets
from .train import fit_encoder,smoke


def _load(root,run):
    p=root/'private/auditory_v3'/safe_run(run)
    return p,json.loads((p/'completion.json').read_text())


def _same_source(private,other,packet='R3',metadata_only=False):
    here=json.loads((private/'start.json').read_text());before=json.loads((other/'start.json').read_text())
    modules=('representation_data','splits','data') if metadata_only else PACKET_SOURCES[packet]
    keys=['auditory_v3/'+x+'.py' for x in modules]
    if not metadata_only:keys+=['auditory5/models/small_cnn.py']
    if here['config_sha256']!=before['config_sha256'] or any(here['source_hashes'].get(k)!=before['source_hashes'].get(k) for k in keys):raise ValueError('R3_SOURCE_CONFIG_MISMATCH')


def prepare(root,private,public,config,args):
    require_tests(root,private,args['gate_run'],'R3')
    m,s,h,r,support=load_support(root,args['split_run'])
    if support['R3_support']!='SUFFICIENT':raise ValueError('R3_SUPPORT_LIMITED')
    plans=[];minimum=support['positive_pair_minimum_seconds']
    for fold in s['folds']:
        for stage in ('selection','final'):
            groups=fold['R3_fit_groups'] if stage=='selection' else fold['train_groups']
            sample=sample_quartets(m,fit_groups=groups,seed=11,epochs=60,support_s=minimum)
            name=f"fold{fold['outer_fold']}_{stage}";path=private/(name+'.npy')
            np.save(path,sample['batch_indices'])
            for key in ('pairs','quartet_metadata','exposure','retry_ledger','support'):
                sample[key].to_pickle(private/(name+'_'+key+'.pkl'))
            plans.append(dict(outer_fold=fold['outer_fold'],stage=stage,fit_groups=sorted(map(str,groups)),exposure_path=str(path),exposure_file_sha256=digest(path),exposure_hash=hashlib.sha256(sample['batch_indices'].tobytes()).hexdigest(),epochs=60,steps_per_epoch=sample['steps_per_epoch'],original_trial_exposures=int(sample['batch_indices'].size),exact_fallback_quartets=int(sample['retry_ledger'].exact_fallback.sum())))
    aggregate=[{k:v for k,v in row.items() if k not in ('fit_groups','exposure_path')} for row in plans]
    import pandas as pd
    pd.DataFrame(aggregate).to_csv(public/'exposure_counts.csv',index=False)
    result=dict(status='EXPOSURES_FROZEN',packet='R3',split_run=args['split_run'],test_run=args['gate_run'],plans=plans,new_model_fits=0)
    result['public_summary']=dict(status='EXPOSURES_FROZEN',packet='R3',plans=aggregate,new_model_fits=0)
    return result


def join(root,private,public,config,args):
    require_tests(root,private,args['gate_run'],'R3');rows=[]
    for run in args['capability_runs']:
        folder,receipt=_load(root,run);_same_source(private,folder)
        if receipt['packet']!='R3' or receipt['test_run']!=args['gate_run'] or receipt['split_run']!=args['split_run']:raise ValueError('SMOKE_SCOPE_MISMATCH')
        rows.append(receipt)
    if len(rows)!=3 or {x['objective'] for x in rows}!={'SUP','SIM','MATCH'}:raise ValueError('THREE_DISTINCT_OBJECTIVES_REQUIRED')
    if len({x['exposure_hash'] for x in rows})!=1 or len({x['initial_encoder_sha256'] for x in rows})!=1:raise ValueError('SMOKE_EXPOSURE_INITIALIZATION_MISMATCH')
    passed=all(x['status']=='PASS' for x in rows)
    return dict(status='PASS' if passed else 'CAPABILITY_FAIL',packet='R3',test_run=args['gate_run'],split_run=args['split_run'],smoke_runs=args['capability_runs'],smokes=rows,new_encoder_fits=0)


def train(root,private,public,config,args):
    gate=require_capability(root,private,args['gate_run'],'R3',args['split_run'])
    # All selection encoders and probe choices must finish before final training.
    if args['stage']=='final':
        selected,selection=_load(root,args['selection_run']);_same_source(private,selected)
        if selection['status'] not in ('PROBES_SELECTED','COMPLETED_WITH_NUMERICAL_FAILURES') or selection['split_run']!=args['split_run']:raise ValueError('COMPLETE_SELECTION_REQUIRED')
        if selection.get('encoder_tasks_verified')!=15 or not selection.get('shared_exposure_verified') or not selection.get('identical_initialization_verified') or selection.get('stage')!='selection':raise ValueError('FIFTEEN_AUDITED_SELECTION_ENCODERS_REQUIRED')
        if digest(selected/'selection_receipt.json')!=selection.get('selection_receipt_sha256') or digest(selected/'checkpoint_bindings.json')!=selection.get('checkpoint_bindings_sha256'):raise ValueError('COMPLETED_SELECTION_ARTIFACT_CHANGED')
        choices=json.loads((selected/'selection_receipt.json').read_text())
        if len(choices.get('selections',[]))!=60 or not choices.get('selection_complete'):raise ValueError('SIXTY_EXPLICIT_PROBE_CHOICES_REQUIRED')
    m,s,h,r,support=load_support(root,args['split_run'])
    if args['stage']=='final':
        from .evaluate import _validate_selection
        _validate_selection(m,s,choices)
    if support['R3_support']!='SUFFICIENT':raise ValueError('R3_SUPPORT_LIMITED')
    index=args['task_index']
    if index not in range(15) or args['stage'] not in ('selection','final'):raise ValueError('UNKNOWN_REPRESENTATION_TASK')
    objective=('SUP','SIM','MATCH')[index//5];number=index%5
    fold=next(f for f in s['folds'] if int(f['outer_fold'])==number)
    groups=fold['R3_fit_groups'] if args['stage']=='selection' else fold['train_groups']
    plan_dir,plan=_load(root,args['plan_run']);_same_source(private,plan_dir,metadata_only=True)
    if plan['status']!='EXPOSURES_FROZEN' or plan['split_run']!=args['split_run']:raise ValueError('FROZEN_EXPOSURE_SCOPE_MISMATCH')
    exposure=next(e for e in plan['plans'] if e['outer_fold']==number and e['stage']==args['stage'])
    path=Path(exposure['exposure_path'])
    if path.parent.resolve()!=plan_dir.resolve() or digest(path)!=exposure['exposure_file_sha256'] or exposure['fit_groups']!=sorted(map(str,groups)):raise ValueError('EXPOSURE_CHANGED')
    batches=np.load(path,allow_pickle=False)
    if hashlib.sha256(batches.tobytes()).hexdigest()!=exposure['exposure_hash']:raise ValueError('EXPOSURE_PAYLOAD_CHANGED')
    post,pre=load_epochs(m,r)
    receipt=fit_encoder(post,m.stimulus_local_id.to_numpy(),m,groups,batches,config['R3'],private/'training',objective,ledger=Ledger(private,'encoder'))
    result=dict(receipt,packet='R3',outer_fold=number,stage=args['stage'],split_run=args['split_run'],test_run=gate['test_run'],capability_run=args['gate_run'],plan_run=args['plan_run'],checkpoint_sha256=digest(receipt['checkpoint']),exposure_path=str(path),exposure_file_sha256=exposure['exposure_file_sha256'],selection_run=args.get('selection_run'))
    result['public_summary']={k:result[k] for k in ('status','packet','objective','outer_fold','stage','seed','epochs','device','parameter_count_encoder','parameter_count_projector','exposure_hash','initial_encoder_sha256','checkpoint_sha256')}
    result['public_summary'].update(training_seconds=receipt['elapsed_seconds'],fit_group_count=len(groups),original_trial_exposures=int(batches.size),last_epoch_diagnostics=receipt['history'][-1],classifier_accuracy_is_training_only=True,SIM_classifier_untrained=objective=='SIM')
    return result


def run(root,private,public,report,config,args):
    if args['command']=='prepare-exposures':return prepare(root,private,public,config,args)
    if args['command']=='join-r3-capability':return join(root,private,public,config,args)
    if args['command']=='train-representation':return train(root,private,public,config,args)
    require_tests(root,private,args['gate_run'],'R3')
    *_,support=load_support(root,args['split_run'])
    if support['R3_support']!='SUFFICIENT':raise ValueError('R3_SUPPORT_LIMITED')
    recovery=None
    if args.get('recover_zero_update_run'):
        recovery=validate_zero_update_recovery(root,private,args['recover_zero_update_run'],args['objective'])
    result=smoke(args['objective'],private/'training',config['R3'],Ledger(private),Ledger(private,'synthetic_encoder'),zero_update_recovery=recovery)
    result.update(test_run=args['gate_run'],split_run=args['split_run'])
    return result


def validate_zero_update_recovery(root,private,run,objective):
    """Only the known first-backward backend failure may reuse its allocation.

    That native CUDA operation fails unconditionally at the first backward,
    before optimizer.step; identical initialization and exposure hashes are
    checked again in fit_encoder. This does not choose a fresh seed or model.
    """
    import ast,inspect
    from .train import generate_smoke_data
    folder=root/'private/auditory_v3'/safe_run(run)
    failure=json.loads((folder/'failure.json').read_text());old_args=json.loads((folder/'args.json').read_text())
    if old_args['command']!='capability' or old_args['packet']!='R3' or old_args['objective']!=objective:raise ValueError('RECOVERY_OBJECTIVE_MISMATCH')
    if failure.get('type')!='RuntimeError' or 'adaptive_avg_pool2d_backward_cuda does not have a deterministic implementation' not in failure.get('message',''):raise ValueError('NOT_KNOWN_FIRST_BACKWARD_FAILURE')
    if any((folder/'training').glob('checkpoint*')) or (folder/'training/training_progress.json').exists() or (folder/'training/training_receipt.json').exists():raise ValueError('ZERO_UPDATE_STATE_NOT_ESTABLISHED')
    old_source=(folder/'source/auditory_v3/train.py').read_text()
    old_node=next(x for x in ast.parse(old_source).body if isinstance(x,ast.FunctionDef) and x.name=='generate_smoke_data')
    if ast.dump(old_node,include_attributes=False)!=ast.dump(ast.parse(inspect.getsource(generate_smoke_data)).body[0],include_attributes=False):raise ValueError('SYNTHETIC_DATA_GENERATOR_CHANGED')
    for name in ('objectives','representation_data','linear','statistics'):
        if digest(folder/f'source/auditory_v3/{name}.py')!=digest(Path(__file__).with_name(name+'.py')):raise ValueError('RECOVERY_SCIENTIFIC_ALGORITHM_CHANGED')
    old_start=json.loads((folder/'start.json').read_text());new_start=json.loads((private/'start.json').read_text())
    if old_start['config_sha256']!=new_start['config_sha256']:raise ValueError('RECOVERY_CONFIG_CHANGED')
    events=[json.loads(x) for x in (folder/'fit_events.jsonl').read_text().splitlines()]
    if len(events)!=1 or events[0]['kind']!='synthetic_encoder' or not events[0]['is_start']:raise ValueError('RECOVERY_MUST_REFERENCE_SINGLE_INITIAL_ATTEMPT')
    return dict(events[0]['details'],run=run,optimizer_updates_before_failure=0,reason='native deterministic CUDA pooling rejected first backward; same initial encoder and data/exposure continued with equivalent deterministic pooling')
