"""Register independently validated new CPU analyses with the running service."""
import argparse
import hashlib
import importlib
import os
from pathlib import Path
from private.auditory_alignment_v3.aln35 import evidence_refresh as E

assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
ap=argparse.ArgumentParser();ap.add_argument('names',nargs='+',choices=['apwrong_v2','support_summary']);args=ap.parse_args()
config=E.read(E.CONFIG); added=[]
for name in args.names:
    if name=='apwrong_v2':
        module='auditory_alignment_v3.aln35.ap_wrong_analysis_v2'
        m=importlib.import_module(module);m.verify()
        task={'args':['-m',module,'run'],
              'sources':['private/auditory_alignment_v3/aln35/apwrong_v1/units/ALN35APT_*.json']}
    else:
        module='auditory_alignment_v3.aln35.support_experiment_summary'
        task={'args':['-m',module],
              'sources':[f'private/auditory_alignment_v3/aln35/{lane}/units/ALN*.json'
                         for lane in ('support_coverage_v1','episode_pressure_v1','episode_lineage_v2',
                                      'matched_updates_v1','true_risk_selection_v1')]}
    task.update(interval_seconds=1800,module_sha256=hashlib.sha256((E.ROOT/(module.replace('.','/')+'.py')).read_bytes()).hexdigest())
    E.validate_task(task)
    assert name not in config['tasks'] or config['tasks'][name]==task
    config['tasks'][name]=task; added.append(name)
# Four-state diagnostics and all ten aliases are complete. They do not depend
# on other CB target jobs; no repeated CPU report is needed for that finite panel.
cb=E.BASE/'cb_audio_state_v1'
if (cb/'complete.json').is_file() and not E.read(cb/'target_reuse.json')['pending_original_lane']:
    config['tasks'].pop('cbstate',None)
E.write(E.CONFIG,config)
E.write(E.BASE/('analysis_enrollment_'+os.environ['SLURM_JOB_ID']+'.json'),
        {'status':'pass','job':os.environ['SLURM_JOB_ID'],'added':added,'config':config,
         'finite_cb_state_complete':(cb/'complete.json').is_file()})
print('PASS analysis refresh enrollment',added,flush=True)
