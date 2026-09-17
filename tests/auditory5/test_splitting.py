import numpy as np
import pandas as pd
from auditory5.splitting import balanced_component_folds

def test_components_never_split_even_with_multiple_records():
    data=pd.DataFrame([dict(split_group_id='g'+str(i//2),general=True,A=i%2==0,B=True,C=True,D=i%3==0) for i in range(60)])
    a=balanced_component_folds(data,5);b=balanced_component_folds(data,5)
    assert a==b and len(a)==30 and set(a.values())==set(range(5))
    joined=data.split_group_id.map(a)
    assert joined.groupby(data.split_group_id).nunique().eq(1).all()
