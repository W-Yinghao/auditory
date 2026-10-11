from pathlib import Path
import importlib.util,json
import pytest,yaml
ROOT=Path(__file__).resolve().parents[1]
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'scripts'/f'{n}.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
Q=load('queue_advice');S=load('register_seed_pairs')
def row(cat='aln3_core',state='pending',**kw):
 return dict(job_id='SYNTHETIC_JOB',category=cat,state=state,interface_valid=True,dependencies_ready=True,essential_control=False,compatible_result_exists=False,**kw)
def test_running_small_continues():assert Q.advise(row('item2_small','running'))['advice']=='continue_valid_running'
def test_legacy_fm_queued_deferred():assert Q.advise(row('item2_fm_legacy'))['advice']=='defer_reversible_backlog'
def test_legacy_running_checkpoint_not_immediate_kill():assert Q.advise(row('item2_fm_legacy','running'))['advice']=='checkpoint_and_defer_if_blocking'
def test_legacy_essential_control_kept():
 r=row('item2_fm_legacy');r['essential_control']=True
 assert Q.advise(r)['advice']=='run_when_resource_available'
def test_item3bc_mapping():assert Q.advise(row('item3bc'))['advice']=='map_into_B_no_duplicate'
def test_completed_not_retrained():assert Q.advise(row(state='completed'))['advice']=='preserve_reuse_if_contract_matches'
def test_wrong_interface_pauses_only_affected():
 r=row();r['interface_valid']=False
 assert Q.advise(r)['advice']=='pause_affected_repair_only'
def test_performance_not_used():
 a=row();b=dict(a);a['auc']=.99;b['auc']=.1
 assert Q.advise(a)==Q.advise(b)
def test_dependencies_only_local():
 r=row();r['dependencies_ready']=False
 assert Q.advise(r)['advice']=='wait_only_own_dependencies'
def test_no_side_effect_claim():assert Q.advise(row())['side_effects'] is False

def test_seed_roles_registered_and_controls_exist():
 plan=[json.loads(x) for x in (ROOT/'plans/units.jsonl').read_text().splitlines()]
 rules=yaml.safe_load((ROOT/'configs/seed_confirmation_pairs.yaml').read_text())
 out=S.register(plan,rules)
 assert out['required_seed_values']==[3401,3407,3413]
 roles={x['role'] for x in out['roles']}
 assert {'random_full_dense','pretrained_full_dense','local_base','random_residual','small_capacity','native_gx'}.issubset(roles)
 assert out['not_a_submission'] is True and out['live_completed_jobs_checked'] is False

def test_seed_registration_deterministic():
 plan=[json.loads(x) for x in (ROOT/'plans/units.jsonl').read_text().splitlines()]
 rules=yaml.safe_load((ROOT/'configs/seed_confirmation_pairs.yaml').read_text())
 assert S.register(plan,rules)==S.register(plan,rules)
