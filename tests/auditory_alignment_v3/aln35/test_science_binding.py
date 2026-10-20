"""Meaningful boundary checks for actual-source query bindings and contrast signs."""
from types import SimpleNamespace
import numpy as np
import pytest
from auditory_alignment_v3.aln35 import science_binding as B, science_export as E


def test_queries_use_actual_coordinates_not_list_position_or_arm():
    arrays = {'role': np.array(['fit', 'fit', 'test', 'test', 'test', 'test']),
              'person': np.array(['source', 'source', 'person', 'person', 'person', 'person']),
              'segment': np.array([0, 0, 1, 1, 2, 2]), 'source_segment_e0': np.array([7, 900, 1800]),
              'anchor_offsets': np.array([100, 200])}
    assert B.public_queries(arrays, 'person', 'dtu', 1, 128) == [
        f'dtu/cf1/person/fs128/e0={x}/anchor={y}' for x in (900, 1800) for y in (100, 200)]
    assert len(B.public_queries(arrays, 'person', 'dtu', 1, 128, anchors=False)) == 2
    arrays['source_segment_e0'][1] += 1
    assert '/e0=901/' in B.public_queries(arrays, 'person', 'dtu', 1, 128)[0]


def test_incomplete_segment_metadata_is_rejected():
    arrays = {'role': np.array(['test']), 'person': np.array(['p']), 'segment': np.array([0]),
              'source_segment_e0': np.array([900]), 'anchor_offsets': np.array([100, 200])}
    with pytest.raises(AssertionError): B.public_queries(arrays, 'p', 'dtu', 0, 128)


def test_expected_roster_is_group_manifest_not_observed_results():
    family = {'group_sets': {'all': ['HA', 'NH']}, 'contrasts': [{'terms': [{'group': 'all'}]}]}
    assert B.expected_for(family, {'HA_missing': 'HA', 'NH_seen': 'NH', 'phantom': 'Artifact'}) == {'all': ['HA_missing', 'NH_seen']}


def test_all_prescribed_families_and_main_endpoint_signs():
    roster = {'fau': {'a': 'ha', 'b': 'ci', 'c': 'th'}, 'dtu': {'d': 'hi', 'e': 'nh'},
              'federici': {'f': 'CI', 'g': 'HC', 'h': 'HC-v'}, 'private_bdf': {'i': 'HA', 'j': 'NH'}}
    families = E.bind_families(SimpleNamespace(expected=roster))
    assert len(families) == 13 and sum(len(s['contrasts']) for _, s in families) == 40
    specs = {s['family_id']: s for _, s in families}
    terms = specs['S35_MAIN_FAU_APS_GROUP']['contrasts'][0]['terms']
    got = {(t['group'], t['arm']): t['weight'] for t in terms}
    assert got == {('ha', 'S'): 1, ('ha', 'AP'): -1, ('ci', 'S'): -1, ('ci', 'AP'): 1}
    got = {(t['group'], t['arm']): t['weight'] for t in specs['S35_MAIN_PRIVATE_APS_GROUP']['contrasts'][0]['terms']}
    assert got == {('HA', 'AP'): 1, ('HA', 'S'): -1, ('NH', 'AP'): -1, ('NH', 'S'): 1}
    assert all(s['bootstrap']['B'] == 4000 and s['require_full_provenance'] for _, s in families)
