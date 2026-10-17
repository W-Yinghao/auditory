from auditory_alignment_v3.aln34.fusion_function_aggregate import selected_values,FIELDS


def test_inner_selected_step_and_matched_fm_risk_direction():
    def result(x):return {'per_person':{'native':{'p':{'true_nll_bits':x}}}}
    d={k:.1 for k in FIELDS[:6]};d['native']={k:.2 for k in FIELDS[6:9]}
    r={'decisions':{'native':{'pairs':{'cb_pre':{'residual':'residual/20'}}}},
       'stages':{'outer':{'diagnostics':{'cb_pre':{'residual/20':{'p':d}}},
       'comparisons':{'cb_pre':{'local_direct':result(2.),'residual/20':result(1.5),'residual_mismatched_fm/20':result(1.7),
                              'residual/100':result(.2)}}}}}
    values,key=selected_values(r,'cb_pre','native')
    assert key=='residual/20' and values['p']['risk_benefit_vs_local']==.5
    assert abs(values['p']['matched_benefit_vs_wrong_fm']-.2)<1e-12
