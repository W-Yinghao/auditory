"""Structural validation only; real server/data receipts must exist separately."""
from pathlib import Path
import argparse,json,re,sys

def validate(binding,scope='all'):
    errors=[]
    if binding.get('schema')!='auditory_aln41_binding_v1':errors.append('wrong schema')
    if binding.get('status')!='READY':errors.append('status must be READY after actual verification')
    def walk(obj,prefix=''):
        if isinstance(obj,dict):
            for k,v in obj.items():walk(v,prefix+'.'+k if prefix else k)
        elif obj is None:errors.append(f'{prefix}: unbound')
        elif prefix.endswith('sha256') and not (isinstance(obj,str) and re.fullmatch('[0-9a-f]{64}',obj)):
            errors.append(f'{prefix}: expected actual sha256')
    walk(binding)
    checks={
      'code':['production_tree_clean'],
      'stage1':['strict_load_ok','channels20_31_64_forward_ok','all_backbone_layers_gradient_ok','save_reload_equal_ok','three_crop_input_ok'],
      'data':['source_people_and_content_split_disjoint','source_target_overlap_excluded','episode_physical_guard_verified','age_one_row_one_child_same_encoder','rich_all_three_views_present'],
      'method':['source_native_crop_before_resample','support_query_disjoint_and_inner_support_only','gcs_same_support_adaptation','shared_slot_sigma_per_view','wrong_all_views_same_bijection','freeze_source_selection_before_targets'],
      'targets':['private_train_es_test_roles_verified','age_nested_child_cv_verified'],
      'execution':['slurm_cpu_and_gpu_rule_confirmed','existing_holds_preserved','running_source_immutable','no_automatic_deletion_or_publication'],
      'external':['readiness_decision_before_new_target_results'],
    }
    for section,keys in checks.items():
        for key in keys:
            if binding.get(section,{}).get(key) is not True:errors.append(f'{section}.{key}: must be explicitly verified true')
    s=binding.get('stage1',{})
    if not isinstance(s.get('expected_numel'),int) or s.get('expected_numel',0)<=0 or s.get('loaded_backbone_numel')!=s.get('expected_numel'):
        errors.append('stage1 backbone loaded/expected numel must match positive count')
    if binding.get('execution',{}).get('project_gpu_running_plus_pending_cap')!=10:errors.append('project aggregate GPU cap must remain 10')
    folds=binding.get('data',{}).get('private_outer_fold_sizes')
    if folds!=[13,13,13,13,12]:errors.append('private roster/folds changed: need explicit versioned amendment, not silent rebinding')
    if scope=='source':
        source_data_keys=('core_manifest_sha256','rich_manifest_sha256','source_people_and_content_split_disjoint',
                          'source_target_overlap_excluded','episode_physical_guard_verified','rich_all_three_views_present')
        errors=[e for e in errors if not (
            e.startswith(('targets.','legacy_intake.','external.','private roster/')) or
            (e.startswith('data.') and not any(e.startswith('data.'+k+':') for k in source_data_keys)))]
    elif scope!='all':raise ValueError('scope must be all or source')
    return {'status':'PASS' if not errors else 'NOT_READY','scope':scope,'errors':errors,
            'does_not_verify_actual_files_or_data_leakage':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('binding',type=Path);p.add_argument('--scope',choices=['all','source'],default='all');p.add_argument('--out',type=Path);a=p.parse_args()
    r=validate(json.loads(a.binding.read_text()),scope=a.scope);s=json.dumps(r,ensure_ascii=False,indent=2)
    if a.out:a.out.write_text(s+'\n')
    print(s);sys.exit(0 if r['status']=='PASS' else 2)
