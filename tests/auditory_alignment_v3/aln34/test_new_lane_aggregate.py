import pytest

from auditory_alignment_v3.aln34.new_lane_aggregate import Panel


def row(seed=3401, cf=0, sf=0, ds='dtu'):
    return {'dataset': ds, 'seed': seed, 'subject_fold': sf, 'content_fold': cf}


def test_incomplete_content_or_seed_never_enters_full_mean():
    p = Panel(); pop = {'a': {'group': 'G'}, 'b': {'group': 'G'}}
    for seed in (3401, 3407):
        for cf in (0, 1):
            observed = {'a': seed - 3400 + cf, 'b': 9.}
            if seed == 3407 and cf == 1:
                observed.pop('b')
            p.add('scope', 'x', 'native', row(seed, cf), pop, observed)
    key = ('dtu', 'scope', 'native', 'x')
    assert p.complete(key, {3401}) == {'a': 1.5, 'b': 9.}
    assert p.complete(key, {3401, 3407}) == {'a': 4.5}


def test_federici_sessions_cluster_and_phantom_excluded():
    p = Panel({'a1': ('a', 'HC', 'human'), 'a2': ('a', 'HC', 'human'), 'v': ('v', 'HC-v', 'human'), 'ph': ('ph', 'Artifact', 'phantom')})
    pop = {k: {} for k in p.manifest}
    p.add('s', 'x', 'native', row(ds='federici'), pop, {'a1': 1, 'a2': 3, 'v': 10, 'ph': 999})
    assert p.complete(('federici', 's', 'native', 'x'), {3401}) == {'a': 2., 'v': 10.}
    assert p.excluded_entities == {('federici', 'ph')}


def test_missing_session_is_not_an_identity_complete_observation():
    p = Panel({'a1': ('a', 'HC', 'human'), 'a2': ('a', 'HC', 'human')})
    p.add('s', 'x', 'native', row(ds='federici'), {'a1': {}, 'a2': {}}, {'a1': 4})
    assert p.complete(('federici', 's', 'native', 'x'), {3401}) == {}


def test_duplicate_and_nonfinite_fail_closed():
    p = Panel(); pop = {'a': {'group': 'G'}}
    p.add('s', 'x', 'native', row(), pop, {'a': 3})
    p.add('s', 'x', 'native', row(), pop, {'a': 3})
    with pytest.raises(ValueError, match='conflicting'):
        p.add('s', 'x', 'native', row(), pop, {'a': 2})
    with pytest.raises(ValueError, match='nonfinite'):
        p.add('s', 'x', 'native', row(), pop, {'a': float('nan')})


def test_family_uses_common_identities_and_nll_sign():
    p = Panel(); pop = {str(i): {'group': 'G'} for i in range(4)}
    for name, vals in [('ref', {str(i): i + 3 for i in range(4)}), ('good', {str(i): i + 1 for i in range(3)})]:
        p.add('s', name, 'native', row(), pop, vals)
    p.compare('dtu', 's', 'native', 'ref', 'good')
    out = p.summarise(40)[0]
    assert out['common_identity_n'] == 3
    assert out['expected_identity_n'] == 4
    assert out['groups']['all']['est'] == [2.]


def test_representative_single_seed_does_not_enter_multiseed_family():
    p = Panel(); pop = {'a': {'group': 'G'}}
    for seed in (3401, 3407):
        p.add('s', 'ref', 'native', row(seed), pop, {'a': 3})
        p.add('s', 'paired', 'native', row(seed), pop, {'a': 2})
    p.add('s', 'representative', 'native', row(), pop, {'a': 1})
    p.compare('dtu', 's', 'native', 'ref', 'paired')
    p.compare('dtu', 's', 'native', 'ref', 'representative')
    out = next(x for x in p.summarise(40) if x['seed_scope'] == 'complete_seed_mean')
    assert out['labels'] == ['paired versus ref']


def test_group_interaction_is_difference_of_paired_changes():
    p=Panel();pop={str(i):{'group':'A' if i<4 else 'B'} for i in range(8)}
    ref={str(i):100.+i for i in range(8)}
    cand={str(i):ref[str(i)]-(3. if i<4 else 1.) for i in range(8)}
    p.add('policy/model','ref','native',row(),pop,ref)
    p.add('policy/model','cand','native',row(),pop,cand)
    p.compare('dtu','policy/model','native','ref','cand')
    out=p.summarise(80)[0]['group_by_intervention']
    assert out['comparisons']['A minus B']['est']==[2.]
    assert out['comparisons']['A minus B']['n_a']==4
    assert out['joint_simultaneous_family']['n_members']==1
