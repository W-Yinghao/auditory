"""Hard information-boundary checks used by adapters, training and tests."""
from dataclasses import dataclass
import numpy as np
from auditory5.provenance import object_hash


@dataclass(frozen=True)
class FitScope:
    train_groups: tuple
    validation_groups: tuple = ()
    test_groups: tuple = ()

    def __post_init__(self):
        tr, va, te = map(set, (self.train_groups,self.validation_groups,self.test_groups))
        if not tr or tr & va or tr & te or va & te:
            raise ValueError('INVALID_FIT_SCOPE: nonempty train and disjoint identity groups required')

    @property
    def hash(self):
        return object_hash({k:sorted(getattr(self,k)) for k in ('train_groups','validation_groups','test_groups')})

    def assert_fit_groups(self, groups):
        if not set(groups) <= set(self.train_groups):
            raise ValueError('LEAKAGE: transform fit sees held-out identities')


def require_shared_coordinates(hashes):
    if len(set(hashes)) != 1:
        raise ValueError('CROSS_ENCODER_COORDINATES: cannot concatenate fold embeddings')


def validate_history_context(columns):
    permitted={'log_previous_gap_s','record_position_fraction','log_previous_gap_s_squared','record_position_fraction_squared'}
    if set(columns) != permitted:
        raise ValueError('HISTORY_CONTEXT_SCHEMA: target/identity or unspecified input field')


class EEGTrainingView:
    """Clinical or provenance fields in the source table cannot leave this view."""
    def __init__(self, X, rows):
        self.X=X;self.rows=rows
        if len(X)!=len(rows):raise ValueError('trial alignment mismatch')

    def __len__(self):return len(self.rows)

    def __getitem__(self,index):
        row=self.rows[index]
        return {'X':self.X[index],'stimulus_local_id':row['stimulus_local_id'],
                'split_group_id':row['split_group_id'],'trial_id':row['trial_id']}


def check_direct_sample_overlap(train, test):
    """Intervals are (record, segment, start, stop), with stop exclusive."""
    for a in train:
        for b in test:
            if a[:2]==b[:2] and max(a[2],b[2])<min(a[3],b[3]):
                raise ValueError('RAW_SAMPLE_OVERLAP')


def canonical_records(rows):
    selected={}
    for row in rows:
        canonical=row['canonical_record_id']
        if row['record_id']!=canonical:continue
        if canonical in selected:raise ValueError('duplicate canonical record')
        selected[canonical]=row
    return list(selected.values())


class CandidateScaler:
    """Training candidates have equal weight in channel center/scale moments."""
    def fit(self, arrays, groups, scope):
        scope.assert_fit_groups(groups)
        moments=[]
        for group in sorted(set(groups)):
            parts=[np.asarray(x,dtype=np.float64) for x,g in zip(arrays,groups) if g==group]
            x=np.concatenate(parts,axis=0)
            if x.ndim!=3 or not len(x) or not np.isfinite(x).all():raise ValueError('invalid training EEG')
            moments.append((x.mean(axis=(0,2)),(x*x).mean(axis=(0,2))))
        self.center=np.mean([m[0] for m in moments],axis=0)
        variance=np.mean([m[1] for m in moments],axis=0)-self.center**2
        self.scale=np.sqrt(np.maximum(variance,1e-12))
        self.scope_hash=scope.hash
        self.fit_groups=tuple(sorted(set(groups)))
        return self

    def transform(self,x):
        a=np.asarray(x)
        if not np.isfinite(a).all():raise ValueError('nonfinite inference EEG')
        return ((a-self.center[None,:,None])/self.scale[None,:,None]).astype(np.float32)
