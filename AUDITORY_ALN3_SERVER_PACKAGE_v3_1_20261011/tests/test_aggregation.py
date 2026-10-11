from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest
from aln3_reference.aggregation import (validate_rows,identity_condition_values,summarize_conditions,
 independent_group_contrasts,phantom_sessions,paired_conditions)
ROOT=Path(__file__).resolve().parents[1]
def rows():return pd.read_csv(ROOT/'examples/SYNTHETIC_federici_long.csv')
def test_phantom_separate():
 d=summarize_conditions(rows(),100);hc=next(r for r in d if r['condition']=='HC')
 assert hc['n_identities']==2 and hc['mean']==1.5
 art=next(r for r in d if r['condition']=='Artifact')
 assert art['n_identities']==1 and art['ci_low'] is None

def test_independent_group_contrast():
 out=independent_group_contrasts(rows(),n_boot=100)
 hc=next(r for r in out if r['contrast']=='HC - HC-v')
 assert hc['design']=='independent_groups' and hc['n_first']==2 and hc['n_second']==2
 np.testing.assert_allclose(hc['mean'],1.)

def test_nine_sessions_one_phantom():
 out=phantom_sessions(rows())[0]
 assert out['n_sessions']==9 and out['n_identities']==1 and out['ci_low'] is None
 assert out['session_min']==100 and out['session_max']==108

def test_obsolete_alias_rejected():
 d=rows();d.loc[d.subject_uid=='SYNTHETIC_HCv_1001','subject_uid']='SYNTHETIC_HC_1001'
 with pytest.raises(ValueError,match='not be paired'):validate_rows(d)

def test_nine_phantom_ids_rejected():
 d=rows();mask=d.condition=='Artifact';d.loc[mask,'subject_uid']=d.loc[mask,'record_uid']
 with pytest.raises(ValueError,match='one phantom'):validate_rows(d)

def test_old_pair_function_rejected():
 with pytest.raises(ValueError,match='withdrawn'):paired_conditions(rows())

def test_equalize_records():
 d=rows().query("subject_uid=='SYNTHETIC_HC_1001'").copy();a=d.iloc[0].to_dict();b=dict(a);c=dict(a)
 a['value']=0.;b.update(value=2.,unit_id='SYNTHETIC_EXTRA',content_fold=1);c.update(value=9.,record_uid='SYNTHETIC_SECOND')
 assert identity_condition_values(pd.DataFrame([a,b,c])).iloc[0].value==5.

def test_duplicates_rejected():
 d=rows()
 with pytest.raises(ValueError):validate_rows(pd.concat([d,d.iloc[:1]],ignore_index=True))

def test_conflicting_folds_rejected():
 d=rows();x=d.iloc[0].copy();x['record_uid']='SYNTHETIC_SECOND';x['subject_fold']=4;x['unit_id']='SYNTHETIC_OTHER'
 with pytest.raises(ValueError):validate_rows(pd.concat([d,pd.DataFrame([x])],ignore_index=True))

def test_artifact_human_rejected():
 d=rows();d.loc[d.condition=='Artifact','entity_type']='human'
 with pytest.raises(ValueError):validate_rows(d)

def test_negative_kept():
 d=rows();d.loc[d.condition=='CI','value']=-.2
 assert next(r for r in summarize_conditions(d,100) if r['condition']=='CI')['mean']==-.2

def test_missing_identity_source_rejected():
 d=rows();d.loc[0,'identity_source']=None
 with pytest.raises(ValueError):validate_rows(d)

def test_json_finite():
 json.dumps(summarize_conditions(rows(),100),allow_nan=False)
 json.dumps(independent_group_contrasts(rows(),n_boot=100),allow_nan=False)
 json.dumps(phantom_sessions(rows()),allow_nan=False)
