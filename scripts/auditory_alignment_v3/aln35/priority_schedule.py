"""ALN3.5 operational priorities: dependencies and fixed comparisons, no score gates."""
from private.auditory_alignment_v3.aln34 import priority_schedule as OLD
LANE_PRIORITY = dict(OLD.LANE_PRIORITY)
LANE_PRIORITY.update(inner=5,breadth_inner=10,cb_auditory=10,fusion=10,adapt=15,
                     attention=25,private_episode=25,private_factorial=25,
                     episode=40,cs_episode=40,breadth_adapt=45,breadth_fusion=45,
                     budget=60,breadth_episode=70,curves=100,breadth_budget=110,
                     breadth_curves=120)
LANE_PRIORITY.update(s35_apwrong=5,s35_support=10,s35_episode=15,
                     s35_selection=10,s35_matched_updates=20,s35_cb_state=10,
                     s35_fusion_cache=5,s35_bridge_cache=5,s35_attention_cache=5)
source=OLD.source
row_priority=OLD.row_priority
max_units=OLD.max_units
def rank(lane,turn):return (LANE_PRIORITY.get(lane,30),turn)
def nice(lane):return LANE_PRIORITY.get(lane,30)
