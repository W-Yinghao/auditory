"""Read-only scientific execution binding and compact progress report, Slurm CPU."""
from datetime import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path('/home/infres/yinwang/EEG_auditory')
OUT=ROOT/'private/auditory_alignment_v3'; BASE=OUT/'aln35'
PKG=ROOT/'AUDITORY_ALN3_SERVER_PACKAGE_v3_5_20261018'
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def asset(p):
    p=Path(p); return {'path':str(p.relative_to(ROOT)), 'exists':p.is_file(),
                       'sha256':sha(p) if p.is_file() else None}
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2)+'\n')


def bind_plan(path):
    result=asset(path)
    if not result['exists']: return result
    plan=read(path); rows=plan.get('rows',plan.get('units',[])); units=[]
    for r in rows:
        eid=r.get('experiment_id',r.get('id',r.get('unit_id')))
        if eid is None: continue
        record=path.parent/'units'/f'{eid}.json'
        if path.parent.name=='attention':
            record=OUT/'aln34/attention_transfer_v1/units'/f'{eid}.json'
        if path.name=='fleet_plan.json' and path.parent.name=='bridge':
            record=path.parent/'extract_receipts'/f'{r["key"]}.json'
        failure=record.with_name(f'{eid}.FAILED.json')
        rec=read(record) if record.is_file() else {}
        state='complete' if rec.get('status') in ('complete','PASS') else 'failed' if failure.is_file() else 'not_complete'
        units.append({'id':eid,'state':state,'record':asset(record),
                      'failure':asset(failure) if failure.is_file() else None})
    result.update(units=units,expected_units=len(units),complete_units=sum(u['state']=='complete' for u in units))
    return result


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    names={
      'S35_CB_AUDIO_STATE':['cb_audio_state_v1/plan.json'],
      'S35_AP_WRONG':['apwrong_v1/plan.json'],
      'S35_SUPPORT_COVERAGE':['support_coverage_v1/plan.json'],
      'S35_EPISODE_PRESSURE':['episode_pressure_v1/plan.json','episode_lineage_v2/plan.json'],
      'S35_TRUE_RISK_SELECTION':['matched_updates_v1/plan.json'],
      'S35_MATCHED_UPDATES':['matched_updates_v1/plan.json'],
      'S35_FUSION_ATTRIBUTION':['fusion/plan.json'],
      'S35_BRIDGE_FACTOR':['bridge/plan.json','bridge/fleet_plan.json'],
      'S35_ATTENTION_ORDER':['attention/plan.json']}
    inherited={
      'S35_CLOSE_CB_AUDIO':['cb_auditory_v1'],
      'S35_CLOSE_D_FUSION':['data_inner_v1','adaptation_policy_v1','strong_fusion_v1'],
      'S35_CONTINUE_OTHER_VALID':['private_cb_factorial_v1','private_episode_v2','attention_transfer_v1',
        'prior_private_loo_v1','learning_budget_v2','breadth_budget_v1','breadth_inner_v1',
        'breadth_policy_v1','breadth_fusion_v1','breadth_episode_v1','episode_training_v1','cs_episode_v1']}
    artifacts={
      'S35_INTAKE':['INTAKE.md','live_inventory_1047281.json'],
      'S35_PRE_CORRECTION':['../../../results/auditory_alignment_v3/aln35/science/correction_manifest.json'],
      'S35_PAIRED_SCIENCE':['../../../results/auditory_alignment_v3/aln35/science/INDEX.json'],
      'S35_HISTORY_INTERFACE':['../../../results/auditory_alignment_v3/aln35/history/INDEX.json']}
    entries=[]
    for wp in read(PKG/'plans/workpackages.json')['workpackages']:
        item={'id':wp['id'],'action':wp['action'],'scope':wp['scope'],'priority':wp['priority'],
              'source_package':asset(PKG/wp['document']), 'plans':[], 'artifacts':[]}
        item['plans']=[bind_plan(BASE/p) for p in names.get(wp['id'],[])]
        item['plans'] += [bind_plan(OUT/'aln34'/lane/'plan.json') for lane in inherited.get(wp['id'],[])]
        item['artifacts']=[asset((BASE/p).resolve()) for p in artifacts.get(wp['id'],[])]
        if wp['id']=='S35_EPISODE_PRESSURE':
            item['coverage_rule']='58 original units + 2 scoped lineage successors = 60 comparisons; do not count obsolete dependency-only parents twice'
            item['supersedes_dependency_only']=read(BASE/'episode_lineage_v2/plan.json')['supersedes_dependency_only']
        if wp['id']=='S35_TRUE_RISK_SELECTION':
            item.update(coverage_rule='60 policies from the same120 matched trajectories; no additional training',
                        result=asset(BASE/'true_risk_selection_v1/coverage.json'))
        if wp['id']=='S35_CB_AUDIO_STATE':
            item.update(selector='source donor-dev minimum chooses10000; identical to original10 target cells',
                        diagnostic=asset(BASE/'cb_audio_state_v1/complete.json'),
                        target_reuse=asset(BASE/'cb_audio_state_v1/target_reuse.json'))
        entries.append(item)
    frozen=read(BASE/'live_inventory_1047281.json')
    assert sha(OUT/'governance/held_executions.json')==frozen['held_sha256']
    assert sha(ROOT/'auditory_alignment_v3/core.py')==frozen['core_sha256']
    held=read(OUT/'governance/held_executions.json')['ids']
    jobs=subprocess.check_output(['squeue','-u','yinwang','-h','-o','%i|%j|%q|%T|%M|%R'],text=True)
    plugins=[]
    for entry in read(BASE/'fleet_plugins.json')['plugins']:
        module=importlib.import_module(entry['module'])
        assert sha(module.__file__)==entry['sha256']
        if hasattr(module,'verify'): module.verify(read(module.PLAN))
        else: module.open_plan()
        plugins.append({'registration':entry,'readiness':module.fleet_status()})
    value={'schema':'ALN35_BINDINGS_v1','created':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],
      'baseline_publication':'5ef4a60bf77eeaeab5582c2cb076077c0b15bd11','workpackages':entries,
      'scientific_completion_not_implied_by_plan_or_job_count':True,
      'held_file':asset(OUT/'governance/held_executions.json'),'held_registered_ids':len(held),
      'held_incomplete_ids':[eid for eid in held if not (OUT/'units'/f'{eid}.json').is_file()],
      'plugins':plugins,'project_jobs':[s for s in jobs.splitlines() if '|c3_' in s],
      'services':{'fleet':'1047289','evidence':'1047358','watcher':'1044086','checkpoint_offload':'1044070'},
      'evidence_config':asset(BASE/'evidence_tasks.json'),
      'bridge_dependency_chain':asset(BASE/'bridge/PIPELINE_1047390_1047402_1047403.json'),
      'support_summary':asset(BASE/'support_summary_v1/latest.json'),
      'apwrong_analysis_registration':asset(BASE/'apwrong_v1/analysis_v2/registration.json'),
      'cleanup_receipt':asset(BASE/'storage_cleanup/deleted_aborted_fau_1047298.json')}
    for item in entries:
        if item['artifacts']: assert all(a['exists'] for a in item['artifacts']),item['id']
    target=BASE/('bindings_'+os.environ['SLURM_JOB_ID']+'.json')
    write(target,value); write(BASE/'ALN35_BINDINGS.json',value)
    print('workpackages',len(entries),'held registered',len(held),'held incomplete',len(value['held_incomplete_ids']))
    for item in entries:
        print(item['id'], [(p['path'],p.get('complete_units'),p.get('expected_units')) for p in item['plans']])
    # Compact summaries aid actual interpretation; the complete signed results
    # remain authoritative, with nonregular and incomplete families preserved.
    for label,path in [('attention',ROOT/'results/auditory_alignment_v3/aln35/attention/run_1047312/contrasts.json'),
                       ('fusion',ROOT/'results/auditory_alignment_v3/aln35/fusion/run_1047303/contrasts.json')]:
        obj=read(path); lines=[]
        for family in obj['families']:
            counts={k:[v['common_complete_n'],v['expected_n']] for k,v in family['coverage'].items()}
            lines.append({'family':family['family_id'],'coverage':counts,'status':family['status'],
                          'contrasts':[{k:c.get(k) for k in ('id','estimate','simultaneous_ci','status')} for c in family['contrasts']]})
        write(BASE/(label+'_compact_'+os.environ['SLURM_JOB_ID']+'.json'),lines)
        print(label,'families',len(lines))


if __name__=='__main__': main()
