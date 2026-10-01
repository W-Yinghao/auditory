"""T7 (semantic evidence) and T8 (identity counting) for the B0 recovery code."""
import numpy as np
import pandas as pd

from auditory_nextmap import recovery as rc


def test_t7_rules_and_names_give_stimuli_but_roles_and_soa_do_not():
    settings = ['1: Rules for category "Standard"', 'Milliseconds Before: 100', 'Event 1:', 'Code is "stm+" and',
                'Cell is "renshengba.wav"', '2: Rules for category "Deviant"', 'Code is "stm+" and', 'Cell is "renshengba4.wav"']
    rules = rc.segmentation_rules(settings)
    assert [r["category"] for r in rules] == ["Standard", "Deviant"]
    assert rules[1]["cells"] == ["renshengba4.wav"] and rules[1]["codes"] == ["stm+"]
    assert rc.pair_family(["renshengba.wav", "renshengba4.wav"]) == "ba1ba4"
    assert rc.pair_family(["renshengba.wav", "renshengpa.wav"]) == "bapa"
    assert rc.pair_family(["1000Hz.wav", "1500Hz.wav"]) == "puretone"
    assert rc.name_semantics("sound2k")["physical_frequency_hz"] == 2000.0
    assert rc.name_semantics("renshengba4.wav")["lexical_tone_label"] == "T4"
    # role words alone carry no stimulus identity, frequency or tone
    for literal in ("Standard", "hdev", "Deviant"):
        sem = rc.name_semantics(literal)
        assert sem["physical_frequency_hz"] is None and sem["lexical_tone_label"] is None and sem["task_family"] == "other"
    assert {k for k, _ in rc.vocab_hits("hdev ldev Standard")} == {"role_code"}


def test_t7_conflicts_are_kept_not_voted_away():
    C = pd.DataFrame([
        {"record_id": "a", "claim_field": "task_family", "claim_value": "puretone", "evidence_grade": "DIRECT", "conflict_status": "none"},
        {"record_id": "a", "claim_field": "task_family", "claim_value": "bapa", "evidence_grade": "LINKED", "conflict_status": "none"},
        {"record_id": "b", "claim_field": "task_family", "claim_value": "bapa", "evidence_grade": "DIRECT", "conflict_status": "none"},
        {"record_id": "b", "claim_field": "task_family", "claim_value": "bapa", "evidence_grade": "SCOPED", "conflict_status": "none"},
        {"record_id": "c", "claim_field": "task_family", "claim_value": "puretone", "evidence_grade": "DIRECT", "conflict_status": "none"},
        {"record_id": "c", "claim_field": "task_family", "claim_value": "bapa", "evidence_grade": "SCOPED", "conflict_status": "none"},
    ])
    out = rc.mark_conflicts(C)
    assert set(out[out.record_id == "a"].conflict_status) == {"CONFLICT"}
    assert set(out[out.record_id == "b"].conflict_status) == {"none"}
    assert set(out[out.record_id == "c"].conflict_status) == {"CONFLICT"}


def test_t8_identities_are_counted_by_anchor_not_container():
    M = pd.DataFrame([
        {"container_id": "m1", "data_level": "continuous_or_discontinuous", "subject_fields_empty": False,
         "name_link_status": "name_link", "anchors": "ci:P1", "links_existing_canonical_identity": False, "age_months": 40.0},
        {"container_id": "m2", "data_level": "continuous_or_discontinuous", "subject_fields_empty": False,
         "name_link_status": "name_link", "anchors": "ci:P1", "links_existing_canonical_identity": False, "age_months": np.nan},
        {"container_id": "m3", "data_level": "evoked", "subject_fields_empty": True,
         "name_link_status": "no_name_link", "anchors": "", "links_existing_canonical_identity": False, "age_months": np.nan},
        {"container_id": "m4", "data_level": "continuous_or_discontinuous", "subject_fields_empty": False,
         "name_link_status": "name_link", "anchors": "ci:P9", "links_existing_canonical_identity": True, "age_months": 70.0},
    ])
    out = rc.identity_counts(M, {"m1": "A", "m2": "A", "m3": "B", "m4": "C"}, pretrained={"m2"})
    assert out["net_new_identity_candidates"] == 1                 # two unknown components -> one child
    assert out["net_new_identity_candidates_with_age"] == 1
    assert out["unresolved_identity_containers"] == 1              # empty subject fields never make a new child
    assert out["containers_of_known_identities_extra_visits"] == 1
    assert out["distinct_acquisition_ids"] == 3
    assert out["exposure"]["net_new_identities_with_pretraining_exposure"] == 1


def test_rtf_plain_decodes_gbk_and_drops_control_words():
    raw = r"{\rtf1\ansi {\fonttbl\f0 x;}\f0\fs24 \'d2\'f4\'bd\'da ba pa 1000Hz\par}"
    text = rc.rtf_plain(raw)
    assert "音节" in text and "1000Hz" in text and "rtf1" not in text
    hits = {k for k, _ in rc.vocab_hits(text)}
    assert {"zh", "syllable", "hz"} <= hits


def test_path_tokens_include_pinyin_of_han_runs():
    lk = rc._linkage_helpers()
    toks = rc.path_tokens(lk, "/data/纯音张三测试/rec_01.mff")
    assert "zhangsan" in toks and "rec" in toks


def test_role_names_are_normalised_before_reversal_checks():
    assert {rc.normalise_role(x) for x in ("stad", "Standard", "std")} == {"standard"}
    assert {rc.normalise_role(x) for x in ("devat", "Deviant", "devt")} == {"deviant"}
    assert rc.normalise_role("MMN") == "other"


def test_log_semantics_families_and_counts():
    sem = rc.log_semantics([["wav", "renshengba.wav", 851], ["wav", "renshengba4.wav", 149], ["rensheng", "renshengba4", 149]])
    assert sem["families"] == ["ba1ba4"] and sem["wav_counts"][0] == ("renshengba.wav", 851)
    assert rc.log_semantics([["hz", "1500hz", 10], ["rensheng", "renshengpa", 3]])["families"] == ["bapa", "puretone"]
    assert rc.counts_match(850, 851) and not rc.counts_match(850, 600) and not rc.counts_match(0, 0)


def test_stm_cell_classes_decode_hashed_keys():
    class L:
        label_map = {"Lk": "cel#"}
        idx = pd.DataFrame({"numeric_event_key_counts": ['{"stm+|Lk": {"1": 850, "2": 150, "3": 20}, "CELL|Lx": {"1": 1}}']},
                           index=["m1"])
    assert rc.stm_cell_classes(L, "m1") == [("1", 850), ("2", 150), ("3", 20)]
