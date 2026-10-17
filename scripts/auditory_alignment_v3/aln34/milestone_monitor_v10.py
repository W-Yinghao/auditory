"""Slurm CPU evidence maintenance; fitting jobs remain under the GPU coordinators."""
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from auditory_alignment_v3 import core
from auditory_alignment_v3.aln34 import learning_budget as B

OUT = Path(core.OUT); BASE = OUT/'aln34'; ROOT = Path(core.REPO)
LANES = ('learning_budget_v2', 'data_inner_v1', 'adaptation_policy_v1', 'strong_fusion_v1', 'episode_training_v1', 'content_time_v1', 'private_current_time_v1')
SCIENCE_LANES = LANES[5:]
BREADTH_LANES = ('breadth_budget_v1','breadth_inner_v1','breadth_policy_v1','breadth_fusion_v1','breadth_episode_v1')
LANES += BREADTH_LANES
LANES += ('private_episode_v2',)
LANES += ('cb_auditory_v1',)
LANES += ('attention_transfer_v1',)
LANES += ('private_cb_factorial_v1',)
LANES += ('prior_private_loo_v1',)
LANES += ('prior_science_v1',)
LANES += ('cs_episode_v1',)


def read(p): return json.loads(p.read_text())
def log(*parts): print(datetime.now().astimezone().isoformat(), *parts, flush=True)
def run(args):
    log('RUN', args)
    subprocess.run([sys.executable, '-B', *args], check=True)


def verify_add11():
    for line in (OUT/'aln32/code_sha256_at_freeze_add11.txt').read_text().splitlines():
        if not line or line.startswith('#'): continue
        digest, name = line.split(None, 1); path = ROOT/name
        raw = path.read_bytes()
        if name.endswith('plan_ext.jsonl'):
            raw = b''.join(raw.splitlines(keepends=True)[:3325])
        assert hashlib.sha256(raw).hexdigest() == digest, 'ADDENDUM_11 freeze drift: '+name


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077); os.chdir(ROOT)
    with (BASE/'.milestone_monitor.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        analysed = {}; last = {}; statefile = BASE/'milestone_state.json'
        if statefile.exists():
            state = read(statefile); analysed = state.get('analysed_counts', {}); last = state.get('last_success', {})
        tick = 0
        while not (BASE/'STOP_milestone_monitor_v10').exists():
            tick += 1; counts = {}; errors = []
            for lane in LANES:
                plan = read(BASE/lane/'plan.json'); total = len(plan['rows']); completed = 0
                for row in plan['rows']:
                    eid = row.get('experiment_id', row.get('id')); p = BASE/lane/'units'/f'{eid}.json'
                    completed += p.exists() and read(p).get('status') == 'complete'
                counts[lane] = [int(completed), total]
            rows = core.load_rows()+[json.loads(x) for x in (OUT/'plan_ext.jsonl').read_text().splitlines()]
            tf = [r for r in rows if r['family_id'] == 'ALN32_TRUE_FULL']
            done = sum((OUT/'units'/f'{r["experiment_id"]}.json').exists() for r in tf)
            counts['true_full'] = [done, len(tf)]
            prior=[r for r in rows if r['spec'].get('execution_contract')=='aln33_env64_125ms_v1']
            counts['public_prior']=[sum((OUT/'units'/f'{r["experiment_id"]}.json').exists() and
                read(OUT/'units'/f'{r["experiment_id"]}.json').get('status')=='complete' for r in prior),len(prior)]
            from auditory_alignment_v3.aln34 import private_calibration_device as D
            lp = D.L.load_plan(); nloo = sum(bool(D.successes(u['row']['experiment_id'])) for u in lp['units'])
            counts['private_loo'] = [nloo, len(lp['units'])]
            now = time.time()
            tasks = []
            signatures = {'efficacy':{k:counts[k] for k in LANES[:5]}, 'science':{k:counts[k] for k in SCIENCE_LANES},
                          'breadth':{k:counts[k] for k in BREADTH_LANES},'tf':counts['true_full'],
                          'private_episode':counts['private_episode_v2'],
                          'cb_auditory':counts['cb_auditory_v1'],
                          'attention':counts['attention_transfer_v1'],'public_prior':counts['public_prior'],
                          'private_factorial':counts['private_cb_factorial_v1'],'prior_science':counts['prior_science_v1'],'prior_loo':counts['prior_private_loo_v1'],'cs_episode':counts['cs_episode_v1'],
                          'fusion_function':{k:counts[k] for k in ('strong_fusion_v1','breadth_fusion_v1')}}
            changed = signatures['efficacy'] != analysed.get('efficacy')
            if changed and (now-last.get('efficacy', 0)>1800 or all(counts[k][0] == counts[k][1] for k in LANES[:5])):
                tasks.append(('efficacy', ['-m','auditory_alignment_v3.aln34.new_lane_aggregate']))
            if signatures['science'] != analysed.get('science') and (now-last.get('science', 0)>1800 or all(counts[k][0] == counts[k][1] for k in SCIENCE_LANES)):
                tasks.append(('science', ['-m','auditory_alignment_v3.aln34.science_aggregate']))
            if signatures['breadth'] != analysed.get('breadth') and (now-last.get('breadth', 0)>1800 or all(counts[k][0] == counts[k][1] for k in BREADTH_LANES)):
                tasks.append(('breadth', ['-m','auditory_alignment_v3.aln34.breadth_aggregate']))
            if signatures['tf'] != analysed.get('tf') and now-last.get('tf', 0)>3600:
                tasks.append(('tf',['-m','auditory_alignment_v3.aln34.tf_l1_pairs']))
            for task,lanes,module in (('private_episode',('private_episode_v2',),'private_episode_v2_aggregate'),
                                      ('private_factorial',('private_cb_factorial_v1',),'private_cb_factorial_aggregate'),
                                      ('cs_episode',('cs_episode_v1',),'cs_episode_aggregate'),
                                      ('prior_science',('prior_science_v1',),'prior_science_aggregate'),
                                      ('attention',('attention_transfer_v1',),'attention_transfer_aggregate'),
                                      ('cb_auditory',('cb_auditory_v1',),'cb_auditory_aggregate'),
                                      ('fusion_function',('strong_fusion_v1','breadth_fusion_v1'),'fusion_function_aggregate')):
                if signatures[task] != analysed.get(task) and (now-last.get(task,0)>1800 or all(counts[k][0]==counts[k][1] for k in lanes)):
                    tasks.append((task,['-m','auditory_alignment_v3.aln34.'+module]))
            if signatures['prior_loo'] != analysed.get('prior_loo') and (now-last.get('prior_loo',0)>1800 or counts['prior_private_loo_v1'][0]==counts['prior_private_loo_v1'][1]):
                tasks.append(('prior_loo',['-m','auditory_alignment_v3.aln34.prior_private_loo','--aggregate']))
            if signatures['public_prior'] != analysed.get('public_prior') and (now-last.get('public_prior',0)>1800 or counts['public_prior'][0]==counts['public_prior'][1]):
                tasks.append(('public_prior',['-m','auditory_alignment_v3.prior33.analysis']))
            if nloo == len(lp['units']) and not (ROOT/'results/auditory_alignment_v3/aln34/private_calibration/leave_self_out.json').exists():
                tasks.append(('loo',['-m','auditory_alignment_v3.aln34.private_calibration_aggregate']))
            if tick == 1 or tick % 10 == 0:
                tasks.append(('prior_progress',[str(BASE/'prior_progress.py')]))
                tasks.append(('continuation',[str(BASE/'continue_prior.py'),'--apply']))
            if now-last.get('prior_curves',0)>3600:
                tasks.append(('prior_curves',[str(BASE/'prior_trajectory.py')]))
            for name, args in tasks:
                try:
                    run(args); last[name] = time.time()
                    if name in signatures: analysed[name] = signatures[name]
                except Exception as e:
                    log('ERROR', name, repr(e)); errors.append({'task': name, 'error': repr(e)})
            final_receipt = BASE/'add11_final_receipt.json'
            if len(tf) == 800 and done == 800 and not final_receipt.exists():
                try:
                    assert all(read(OUT/'units'/f'{r["experiment_id"]}.json').get('status') == 'complete' for r in tf)
                    verify_add11()
                    run(['-m','pytest','-p','no:cacheprovider','-q','tests/auditory_alignment_v3/test_aln32_panel_interim.py'])
                    run(['-m','auditory_alignment_v3.aln32_panel_interim'])
                    B.write(final_receipt, {'job':os.environ['SLURM_JOB_ID'], 'time':datetime.now().astimezone().isoformat(),
                        'status':'complete','TF_units':800,'original_plan_prefix_lines':3325,
                        'aggregate_sha256':B.sha(ROOT/'results/auditory_alignment_v3/aln32_panel/aln32_panel.json')})
                except Exception as e:
                    errors.append({'task':'ADDENDUM_11','error':repr(e)}); log('ERROR ADDENDUM_11', repr(e))
            state = {'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],
                     'counts':counts,'analysed_counts':analysed,'last_success':last,'errors':errors,'source_sha256':B.sha(__file__)}
            B.write(statefile,state); log('HEARTBEAT',counts,errors)
            time.sleep(60)


if __name__ == '__main__': main()
