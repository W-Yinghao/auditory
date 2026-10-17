import os
import pytest
assert os.environ.get('SLURM_JOB_ID')
rc=pytest.main(['-q','-p','no:cacheprovider','tests/auditory_alignment_v3/aln34/test_causal_filter.py'])
if rc: raise SystemExit(rc)
from auditory_alignment_v3.aln34.causal_filter import register
register()
