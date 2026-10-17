from auditory_alignment_v3.aln34 import attention_transfer_aggregate as A


def test_source_choice_uses_inner_attention_and_ties_are_fixed():
    records={arm:{'inner_risks':{'5|native':{'mean':.8}},'chosen_integrators':{'5|native':'mean'},
                  'outer':{'arbitrary_test_score':100-i}} for i,arm in enumerate(A.ARMS)}
    assert A.select_model(records,'5|native')[0]=='local'
    records['reve/pretrained_full']['inner_risks']['5|native']['mean']=.7
    assert A.select_model(records,'5|native')[0]=='reve/pretrained_full'
    for r in records.values():r['outer']={'arbitrary_test_score':-999}
    assert A.select_model(records,'5|native')[0]=='reve/pretrained_full'


def test_accuracy_direction_is_candidate_better_and_counts_not_observations():
    assert A.observations({'p':{'accuracy':.7,'n_windows':99}},'accuracy')=={'p':-.7}
    assert A.observations({'p':{'nll_bits':.9,'n_windows':99}},'nll_bits')=={'p':.9}
