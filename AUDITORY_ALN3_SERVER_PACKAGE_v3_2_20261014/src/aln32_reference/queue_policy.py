"""Read-only version-scoped queue advice. No metric-based stopping, no Slurm API."""
from __future__ import annotations


def advise(row: dict) -> dict:
    rid=row.get('experiment_id','UNBOUND')
    status=row.get('status','unknown')
    family=row.get('family_id',row.get('family',''))
    spec=row.get('spec',{})
    if status=='complete':
        action,reason='retain','Completed result; new package does not invalidate it.'
    elif status=='running':
        action,reason='allow_registered_completion','Do not mutate live recipe; inspect actual dependencies separately.'
    elif family=='B_ALIGNED':
        action,reason='continue_existing','Preserve ADDENDUM_06 registration; no duplicate generation.'
    elif row.get('depends_on_old_dense_interface') is True or row.get('legacy_hold_version') is True:
        action,reason='hold_version','Only the declared old execution or descendants remain on hold.'
    elif spec.get('architecture') in ('lag_local_tokens','density_tokens','gx') and row.get('depends_on_old_dense_interface') is False:
        action,reason='continue_if_bound','Independent local path is not blocked by its family name.'
    elif family in ('A_LOCAL','E_GX','F_SCIENCE') and row.get('dependencies_resolved') is True:
        action,reason='continue_if_bound','Known independent work with resolved dependencies.'
    else:
        action,reason='needs_binding','No guessing of dependency/recipe from broad family or performance.'
    return {'experiment_id':rid,'recommendation':action,'reason':reason,'remote_action_performed':False}
