"""CPU checks for the 2026-10-20 bounded lanes (cbaud_people, episode_pressure_s3407)."""
from auditory_alignment_v3 import core
from auditory_alignment_v3.aln35 import cbaud_people as CP, episode_pressure_s3407 as ER, episode_pressure as E


def test_cbaud_family_registered_and_hash_stable():
    CP.register()
    assert core.FAMILY_GROUP[CP.FAMILY] == CP.GROUP
    assert core.code_hash(CP.FAMILY) == core.code_hash(CP.FAMILY)
    assert CP.SELF in core.FAMILY_CODE[CP.GROUP]


def test_cbaud_donor_is_complete_production_state():
    cp = CP.read(CP.CA.PLAN)
    donor, rec, _ = CP.donor_record(cp)
    assert donor['arm'] == 'generic_paired' and donor['seed'] == 3401
    assert CP.B.sha(rec['final_checkpoint']) == rec['final_checkpoint_sha256']


def test_cbaud_provenance_runs_last_and_keeps_inherited(monkeypatch, tmp_path):
    seen = {}
    fake = tmp_path / 'plan.json'
    fake.write_text('{}')
    monkeypatch.setattr(CP, 'PLAN', fake)
    monkeypatch.setattr(core, 'write_record', lambda path, rec, start: seen.update(rec))
    row = {'spec': {'epochs': 100, 'direct_reference_id': 'REF'}}
    plan = {'donor': {'id': 'D', 'checkpoint_sha256': 'S'}}
    with CP.provenance(row, plan, True, 2):
        inner_old = core.write_record

        def inherited(path, rec, start):  # stands in for data_inner / cb_auditory wrappers
            rec.update(plan_sha256='CB_PLAN', execution={'plan_sha256': 'DI_PLAN'})
            inner_old(path, rec, start)
        core.write_record = inherited
        core.write_record('x', {'status': 'complete'}, 0)
    assert seen['inherited_instrumentation'] == {'cb_auditory_plan_sha256': 'CB_PLAN',
                                                 'data_inner_execution': {'plan_sha256': 'DI_PLAN'}}
    assert seen['probe'] is True and seen['truncated'] is True and seen['start']['donor_id'] == 'D'
    assert seen['execution']['design'] == 'S35_CBAUD_PEOPLE_v1' and seen['plan_sha256'] == CP.B.sha(fake)


def test_episode_replication_sources_and_originals():
    sources = ER.selected_sources()
    assert len(sources) == 10
    assert all(s['inner']['seed'] == 3407 and s['outer']['row']['seed'] == 3407 for s in sources)
    assert all(s['architecture'] == 'lag_local_tokens' for s in sources)
    assert len(ER.original_units()) == 10


def test_episode_replication_context_restores_paths():
    before = (E.BASE, E.PLAN, E.STORE)
    with ER.execution_context():
        assert (E.BASE, E.PLAN, E.STORE) == (ER.BASE, ER.PLAN, ER.STORE)
    assert (E.BASE, E.PLAN, E.STORE) == before


def test_status_before_plan_is_not_ready():
    for m in (CP, ER):
        if not m.PLAN.exists():
            assert m.fleet_status()['state'] == 'plan_missing'
        assert m.fleet_status()['name'].startswith('c3_s35') and m.fleet_status()['lane'].startswith('s35_')
