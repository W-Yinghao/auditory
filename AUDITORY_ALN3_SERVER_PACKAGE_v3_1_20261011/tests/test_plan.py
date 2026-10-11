from pathlib import Path
import importlib.util
import yaml
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('plan',ROOT/'scripts/expand_plan.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def config(): return yaml.safe_load((ROOT/'configs/experiment_families.yaml').read_text())


def test_plan_deterministic():
    a=mod.expand(config()); b=mod.expand(config()); assert a==b


def test_no_duplicate_ids():
    rows=mod.expand(config()); assert len(rows)==len({r['experiment_id'] for r in rows})


def test_panel_not_selected_from_performance():
    rows=mod.expand(config())
    assert any(r['seed_scope']=='panel' and r['spec'].get('adaptation')=='random_full' for r in rows)
    assert all(r['status']=='planned_needs_binding' for r in rows)


def test_selection_only_named_ce():
    rows=mod.expand(config())
    assert all(r['spec']['objective']=='SELECTION_CE' for r in rows if r['spec'].get('training_task')=='selection_only')


def test_federici_identity_dependency():
    assert all('verified_identity_manifest' in r['logical_dependencies'] for r in mod.expand(config()) if r['dataset']=='federici')


def test_analysis_not_fake_training():
    rows=mod.expand(config()); agg=[r for r in rows if r['job_kind']=='reaggregate']
    assert len(agg)==1 and agg[0]['subject_fold'] is None
