from auditory_next.public_audit import text_findings,structured_fields,csv_fields,DISALLOWED_FIELDS


def test_known_pseudonyms_are_restricted_even_when_no_name_is_present():
    assert text_findings('estimate for ha_record_0123 is 0.3',{'ha_record_0123'})==['KNOWN_INDIVIDUAL_IDENTIFIER']
    assert text_findings('59 candidates; aggregate effect=-0.02',{'ha_record_0123'})==[]
    assert 'ABSOLUTE_FILESYSTEM_PATH' in text_findings('/projects/data/child/file',set())


def test_nested_individual_prediction_fields_are_detected():
    keys=structured_fields({'aggregate':{'n_candidates':49},'rows':[{'candidate_id':'opaque','p1':.8}]})
    assert DISALLOWED_FIELDS & keys=={'candidate_id','p1'}


def test_empty_withheld_table_has_no_identifiers_but_populated_header_is_checked():
    assert csv_fields('\n') == set()
    assert csv_fields('candidate_id,estimate\nopaque,.1\n') & DISALLOWED_FIELDS == {'candidate_id'}
