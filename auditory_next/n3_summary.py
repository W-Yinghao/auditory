"""Training-OOF-only readout family selection and fixed history strata."""
import numpy as np
import pandas as pd
from scipy.special import expit
from .provenance import write_json


def choose_family(calibrations,mode,population,outer,view):
    rows=[c for c in calibrations if (c['mode'],c['population'],c['outer_fold'],c['view'])==(mode,population,outer,view)]
    valid=[c for c in rows if 'inner_ce_bits_raw' in c]
    expected={'logistic','mlp32'} if mode=='R_SIM' else {'logistic'}
    if {c['family'] for c in valid}!=expected:return None
    return min(valid,key=lambda c:(c['inner_ce_bits_raw'],c['family']!='logistic'))['family']


def summarize_selected(predictions,calibrations,public,dest):
    from .context_execution import candidate_losses,paired_effect
    selections=[];selected=[];strata=[];confidence=[]
    for mode in ('R_SIM','L0'):
        for population in ('P_nat','P_bal'):
            if any(choose_family(calibrations,mode,population,o,v) is None for o in range(5) for v in ('H','HP','HB','HBP','Hnoise')):
                selections.append(dict(mode=mode,population=population,status='INCOMPLETE_SELECTION_MATRIX'));continue
            for outer in range(5):
                for view in ('H','HP','HB','HBP','Hnoise'):
                    family=choose_family(calibrations,mode,population,outer,view)
                    selections.append(dict(mode=mode,population=population,outer_fold=outer,view=view,family=family,
                        selector='inner OOF raw CE; ties logistic; never outer test loss'))
                    if family is None:continue
                    q=predictions[(predictions['mode']==mode)&(predictions.population==population)&(predictions.outer_fold==outer)&
                                  (predictions['view']==view)&(predictions.family==family)].copy()
                    q['family']='training_OOF_selected';selected.append(q)
    write_json(public/'training_family_selection.json',selections)
    if not selected:return
    pred=pd.concat(selected,ignore_index=True);pred.to_parquet(dest/'selected_oof_predictions.parquet',index=False)
    effects=[]
    for (mode,population,kind),rows in pred.groupby(['mode','population','calibration']):
        losses=pd.concat([candidate_losses(x,population).assign(view=v) for v,x in rows.groupby('view')],ignore_index=True)
        for first,second in (('H','HP'),('HB','HBP'),('H','Hnoise')):
            effect=paired_effect(losses[losses['view'].isin([first,second])],first,second)
            if effect:effects.append(dict(mode=mode,population=population,calibration=kind,**effect))
        for runbin,sub in rows.groupby('previous_run_bin'):
            # Some fine strata have structural class zeros. Natural-risk
            # strata remain descriptive; no fabricated balanced-class risk.
            if population!='P_nat':continue
            for view,x in sub.groupby('view'):
                z=x.logit.to_numpy();y=x.stimulus_local_id.to_numpy()
                own=x.assign(loss=(np.logaddexp(0,z)-y*z)/np.log(2)).groupby('split_group_id').loss.mean()
                strata.append(dict(mode=mode,population=population,calibration=kind,previous_run_bin=runbin,
                    view=view,ce_bits=float(own.mean()),candidates=len(own),trials=len(x),scope='fixed run-bin descriptive conditional population'))
        h=rows[rows['view']=='H'];p=expit(h.logit.to_numpy())
        if len(h):
            own=h.assign(high=(np.maximum(p,1-p)>=.95)).groupby('split_group_id').high.mean()
            confidence.append(dict(mode=mode,population=population,calibration=kind,fraction_confidence_ge_095=float(own.mean()),
                scope='descriptive confidence only; no test-trial exclusion'))
    pd.DataFrame(effects).to_csv(public/'selected_family_effects.csv',index=False)
    pd.DataFrame(strata).to_csv(public/'history_run_strata.csv',index=False)
    pd.DataFrame(confidence).to_csv(public/'history_confidence.csv',index=False)
