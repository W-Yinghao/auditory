import sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import core
from auditory_alignment_v3.registry import POLICY_GROUP
for fam, g in POLICY_GROUP.items():
    core.FAMILY_GROUP = {**core.FAMILY_GROUP, fam: g}
    print(fam, g, core.code_hash(fam))
