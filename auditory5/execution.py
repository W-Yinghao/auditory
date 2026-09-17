"""One immutable representation job; no clinical endpoint is loaded."""
import json,os,pickle,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from auditory5.provenance import ROOT,require_slurm,write_json,digest,object_hash
from auditory5.contracts import FitScope
from auditory5.datasets import load_dataset
from auditory5.probes import fit_probe,bin_20ms
from auditory5.metrics import classification_metrics,candidate_log_losses_bits
from auditory5.training import fit_random,fit_supervised,fit_simclr


def run(config,args):
    require_slurm();planpath=Path(args.plan).resolve();plan=json.loads(planpath.read_text());task=plan['tasks'][args.index]
    snapshot=Path(plan['source_snapshot'])
    # Relaunch from the immutable snapshot so subsequent code development cannot
    # alter queued jobs. The dataset root remains explicit and read-only to readers.
    if Path(__file__).resolve()!=snapshot/'auditory5/execution.py':
        env=os.environ.copy();env['AUDITORY5_ROOT']=str(ROOT);env['PYTHONPATH']=str(snapshot)
        os.chdir(snapshot)
        os.execve(sys.executable,[sys.executable,'-m','auditory5.cli','--config',str(ROOT/args.config),
             'run-job','--plan',str(planpath),'--index',str(args.index)],env)
    if object_hash(config)!=plan['config_hash']:raise ValueError('Job configuration differs from frozen plan')
    for path,h in plan['code_hashes'].items():
        if digest(snapshot/path)!=h:raise ValueError('Frozen source snapshot mutation')
    base=ROOT/config['paths']['private_relative'];aggregate=ROOT/config['paths']['aggregates_relative']
    gate=aggregate/plan['contract_run']/'validation.json'
    if digest(gate)!=plan['contract_hash'] or json.loads(gate.read_text())['status']!='PASS':raise ValueError('Module hard gate mismatch')
    # Check current core implementation against the successful test snapshot.
    tested=json.loads(gate.read_text())['code_hashes']
    for rel in ['auditory5/training.py','auditory5/models/small_cnn.py','auditory5/models/simclr.py','auditory5/probes.py']:
        if tested[rel]!=plan['code_hashes'][rel]:raise ValueError('Untested training/probe implementation')
    synthetic=json.loads((aggregate/plan['synthetic_run']/'summary.json').read_text())
    if synthetic['status']!='PASS':raise ValueError('Synthetic computational hard gate failed')
    splitpath=base/'splits'/plan['split_run']/'folds.json'
    if digest(splitpath)!=plan['split_hash']:raise ValueError('Split manifest mutation')
    dest=planpath.parent/'outputs'/task['name'];dest.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();write_json(dest/'task.json',dict(task,job_id=os.environ['SLURM_JOB_ID'],plan_hash=digest(planpath)))
    support=pd.read_parquet(splitpath.parent/'support.parquet')
    support['representation']=support[['general','A','B','D']].any(axis=1) if task['branch']=='all' else support.C
    data=load_dataset(plan['export_run'],support,branch=task['branch'],route='representation',window='post')
    pre=load_dataset(plan['export_run'],support,branch=task['branch'],route='representation',window='pre')
    assert np.array_equal(data.trial_ids,pre.trial_ids)
    fit_eligible=set(support.loc[support.general if task['branch']=='all' else support.C,'split_group_id'])
    fit_groups=sorted(set(task['fit_groups'])&fit_eligible)
    scope=FitScope(tuple(fit_groups),tuple(task['validation_groups']),tuple(task['test_groups']))
    training=data.subset_groups(fit_groups)
    if task['resource']=='gpu' and not torch.cuda.is_available():raise ValueError('GPU allocation required for learned encoders')
    if torch.cuda.is_available():torch.cuda.reset_peak_memory_stats()
    common={'seed':task['seed'],'config':config,'device':'cuda' if torch.cuda.is_available() else 'cpu'}
    mode=task['mode'];encoder=None
    if mode=='R_SUP':encoder=fit_supervised(training.X,training.y,training.groups,scope,record_ids=training.record_ids,onset_seconds=training.onset_seconds,**common)
    elif mode=='R_SIM':encoder=fit_simclr(training.X,training.groups,scope,record_ids=training.record_ids,onset_seconds=training.onset_seconds,**common)
    elif mode=='R_RAND':encoder=fit_random(training.X,training.groups,scope,**common)
    elif mode!='L0':raise ValueError('unknown representation mode')
    if encoder is not None:encoder.save(dest/'encoder.pt')
    features={};metrics={};probe_metadata={}
    trainmask=np.isin(data.groups,fit_groups)
    testmask=np.isin(data.groups,task['test_groups']) & np.isin(data.groups,list(fit_eligible))
    for window,view in [('post',data),('pre',pre)]:
        z=bin_20ms(view.X) if encoder is None else encoder.transform(view.X)
        features[window]=z.astype('float32')
        probe=fit_probe(z[trainmask],data.y[trainmask],data.groups[trainmask],scope,seed=task['seed'],pca_max_dim=32 if mode=='L0' else None)
        with (dest/('probe_'+window+'.pkl')).open('xb') as f:pickle.dump(probe,f)
        p=probe.predict(z[testmask]);rows=data.rows.loc[testmask,['trial_id','record_id','candidate_id','split_group_id','stimulus_local_id']].copy()
        for calibration,prob in p.items():
            rows[calibration+'_probability_class1']=prob[:,1]
            metrics[window+'_'+calibration]=classification_metrics(data.y[testmask],prob,data.groups[testmask],data.trial_ids[testmask])
        rows.to_parquet(dest/('stimulus_oof_'+window+'.parquet'),index=False)
        probe_metadata[window]=dict(selected_C=probe.selected_C,temperature=probe.temperature,fit_scopes=probe.fit_scopes)
    np.savez_compressed(dest/'features.npz',post=features['post'],pre=features['pre'],trial_ids=data.trial_ids,groups=data.groups,y=data.y)
    data.rows.to_parquet(dest/'feature_rows.parquet',index=False)
    write_json(dest/'probe_metadata.json',probe_metadata)
    summary={'status':'PASS','scope':'representation and stimulus diagnostics only','task':task['name'],
        'mode':mode,'branch':task['branch'],'stage':task['stage'],'outer_fold':task['outer_fold'],'inner_fold':task['inner_fold'],
        'train_groups':len(fit_groups),'test_groups':int(len(np.unique(data.groups[testmask]))),'train_trials':len(training.y),
        'test_trials':int(testmask.sum()),'metrics':metrics,'elapsed_seconds':time.monotonic()-started,
        'cuda_peak_allocated_bytes':int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else 0,
        'device':'cuda' if torch.cuda.is_available() else 'cpu','job_id':os.environ['SLURM_JOB_ID'],
        'encoder_fit_scope_hash':scope.hash,'plan_hash':digest(planpath)}
    write_json(dest/'completion.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='metrics'}),flush=True)
