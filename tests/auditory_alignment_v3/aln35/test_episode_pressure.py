import numpy as np
import torch
from auditory_alignment_v3.aln35 import episode_pressure as E


def candidate(ids, value, repeats=None):
    rows={}
    for identity in ids:
        supports={}
        for rule in [*(f'U10_{s}' for s in E.K.SAMPLING_SEEDS),'U30']:
            supports[rule]={'candidates':{str(step):{'metrics':{mode:{'nll_bits':value+step/100}
                        for mode in ('native','linear','unified')}} for step in E.TARGET_STEPS}}
        if repeats:
            for seed,delta in zip(E.K.SAMPLING_SEEDS,repeats):
                for step in E.TARGET_STEPS:
                    for mode in ('native','linear','unified'):
                        supports[f'U10_{seed}']['candidates'][str(step)]['metrics'][mode]['nll_bits']+=delta
        rows[identity]={'status':'complete','supports':supports,'group':'g'}
    return {'per_participant':rows}


def test_within_person_draw_mean_not_new_n():
    rec=candidate(['a','b'],1.,[0,1,2,3,4])
    vals=E.identity_risks(rec,'U10',0,'native')
    assert vals=={'a':3.,'b':3.}


def test_policy_independent_of_outer_risks_and_tie_source_zero():
    inner={name:candidate(['a','b'],1.) for name in ('source','ordinary','episode')}
    outer={name:candidate(['x','y'],1. if name=='source' else .01) for name in inner}
    result=E.choose(inner,outer,'dtu')
    for mode in result.values():
        for support in mode.values():
            for selection in support.values():
                assert selection['chosen']=='source/0' and selection['zero_step_selected']
                assert selection['outer_per_identity_nll']=={'x':1.,'y':1.}


def test_policy_compares_common_inner_people_without_outer_selection():
    inner={'source':candidate(['a','b'],1.),'ordinary':candidate(['b','c'],.9),'episode':candidate(['a','b'],.8)}
    outer={name:candidate(['x'],10.) for name in inner}
    result=E.choose(inner,outer,'private_bdf')['native']['U10']
    assert result['ordinary']['inner_complete_ids']==['b']
    assert result['ordinary']['chosen']=='ordinary/0'
    assert result['episode']['chosen']=='episode/0'
    assert result['episode']['source_fallback_selected'] is False


def test_actual_zero_direction_undefined():
    assert E.tensor_cosine([torch.zeros(2)],[torch.ones(2)]) is None
    assert E.tensor_cosine([torch.tensor([1.,0.])],[torch.tensor([0.,1.])])==0.


def test_adapter_freeze_preserves_source_gradient():
    model=torch.nn.Linear(3,2,bias=False)
    adapted=E.D.Adapter(model,'output_low_rank',3,dim=2)
    E.freeze_adapter(adapted);model.requires_grad_(True)
    result=adapted(torch.ones(4,3)).sum()
    grads=torch.autograd.grad(result,list(model.parameters()))
    assert all(torch.isfinite(g).all() for g in grads)
    assert not adapted.A.requires_grad and not adapted.B.requires_grad


def test_pressure_and_target_steps_are_bounded():
    assert E.PRESSURES==(20,100) and E.ENCODER_UPDATES==100 and E.TARGET_STEPS==(0,5,20)
    split={'pool':np.arange(30),'n10':10}
    out=E.episode_supports(split,'a')
    assert len(out)==6 and len(out['U30'])==30
    assert all(len(v)==10 for k,v in out.items() if k!='U30')
