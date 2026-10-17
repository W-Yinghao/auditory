"""Outcome-independent scheduling only; never edits a registered scientific row."""
LANE_PRIORITY = {
    'private':5, 'science':5, 'prior_loo':5, 'prior_science':5,
    'attention':10, 'private_factorial':10,
    'inner':15, 'breadth_inner':20, 'adapt':25,
    'private_episode':30, 'cb_auditory':35, 'breadth_adapt':35,
    'budget':40, 'fusion':50, 'breadth_fusion':55,
    'episode':60, 'cs_episode':60, 'breadth_episode':70,
    'curves':120, 'breadth_budget':120, 'breadth_curves':140,
}


def source(row):
    if 'spec' in row:return row
    for key in ('source','outer_source','inner_source','outer','inner','row'):
        value=row.get(key)
        if isinstance(value,dict):return source(value)
    return row


def row_priority(lane,row):
    r=source(row);s=r.get('spec',{})
    # All folds/seeds/initializations remain. Main local/CB pairs come first;
    # REVE seed3401 remains the representative, then its additional seeds.
    tier=0
    if lane in ('budget','curves','breadth_budget','breadth_curves'):
        if s.get('architecture')=='reve':tier=1 if r.get('seed')==3401 else 2
    return (tier,r.get('seed',3401),r.get('subject_fold',0),r.get('content_fold',0))


def rank(lane,turn):
    # Fair tie rotation within each priority; every ready lane remains eligible.
    return (LANE_PRIORITY.get(lane,80),turn)


def nice(lane):
    return LANE_PRIORITY.get(lane,80)


def max_units(lane):
    # Frozen-model evaluations are short; amortize allocation/start-up costs.
    return 8 if lane in ('science','private','prior_science') else 2
