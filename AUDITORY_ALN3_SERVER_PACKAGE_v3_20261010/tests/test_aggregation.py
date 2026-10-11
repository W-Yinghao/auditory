import json
import numpy as np
import pandas as pd
import pytest
from aln3_reference.aggregation import validate_rows, identity_condition_values, summarize_conditions, paired_conditions


def rows():
    out=[]
    for sid,cond,kind,val,fold in [('SYNTHETIC_A','HC','human',1.,0),('SYNTHETIC_A','HC-v','human',.3,0),
                                  ('SYNTHETIC_B','HC','human',2.,1),('SYNTHETIC_CI_C','CI','human',.5,2),
                                  ('SYNTHETIC_PHANTOM','Artifact','phantom',100.,-1)]:
        out.append(dict(dataset='federici',config_id='SYNTHETIC_CFG',seed=3401,subject_uid=sid,
                        record_uid=sid+'_'+cond,condition=cond,entity_type=kind,identity_source='synthetic_manifest',
                        subject_fold=fold,content_fold=0,unit_id='SYNTHETIC_UNIT_'+str(fold),metric='gain_bits',value=val))
    return pd.DataFrame(out)


def test_phantom_is_separate():
    out=summarize_conditions(rows(),100)
    hc=next(r for r in out if r['condition']=='HC')
    assert hc['n_identities']==2 and hc['mean']==1.5
    assert next(r for r in out if r['condition']=='Artifact')['panel']=='separate_nonhuman_or_unknown'


def test_same_child_pairing():
    out=paired_conditions(rows(),n_boot=100)[0]
    assert out['n_identities']==1 and out['n_first_only']==1
    np.testing.assert_allclose(out['mean'],.7)


def test_records_equalized_before_subject_mean():
    df=rows().query("condition=='HC' and subject_uid=='SYNTHETIC_A'").copy()
    a=df.iloc[0].to_dict(); b=dict(a); c=dict(a)
    a['value']=0.; b.update(value=2.,unit_id='SYNTHETIC_UNIT_EXTRA',content_fold=1)
    c.update(value=9.,record_uid='SYNTHETIC_A_SECOND_RECORD')
    got=identity_condition_values(pd.DataFrame([a,b,c]))
    assert got.iloc[0].value==5.


def test_duplicate_unit_rows_rejected():
    df=rows()
    with pytest.raises(ValueError): validate_rows(pd.concat([df,df.iloc[:1]],ignore_index=True))


def test_conflicting_human_folds_rejected():
    df=rows(); df.loc[df.condition=='HC-v','subject_fold']=4
    with pytest.raises(ValueError): validate_rows(df)


def test_artifact_human_rejected():
    df=rows(); df.loc[df.condition=='Artifact','entity_type']='human'
    with pytest.raises(ValueError): validate_rows(df)


def test_identity_spaces_not_merged():
    df=rows(); df.loc[df.condition=='CI','subject_uid']='SYNTHETIC_A'
    with pytest.raises(ValueError): validate_rows(df)


def test_negative_metric_kept():
    df=rows(); df.loc[df.condition=='CI','value']=-.2
    assert next(x for x in summarize_conditions(df,100) if x['condition']=='CI')['mean']==-.2


def test_missing_identity_source_rejected():
    df=rows(); df.loc[0,'identity_source']=None
    with pytest.raises(ValueError): validate_rows(df)


def test_outputs_are_json_serializable():
    json.dumps(summarize_conditions(rows(),100)); json.dumps(paired_conditions(rows(),n_boot=100))
