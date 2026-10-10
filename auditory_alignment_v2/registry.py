"""Which plan families / architectures the runner can execute now (integration status only; not part of any unit's code
hash, so integrating a new family never changes the provenance of completed units)."""
SMALL_FAMILIES = {"A_TIME", "A_TARGET_TIME", "A_ANCHOR", "S_CONTROLS", "D_TASK_LOCAL"}
SMALL_ARCH = {"legacy_pool4", "density_tokens", "lag_local_tokens"}


def integrated(row):
    fam, spec = row["family_id"], row["spec"]
    if fam in SMALL_FAMILIES:
        return True
    if fam in ("C_COVERAGE", "C_ATTENTION", "C_SELECTION") and spec.get("architecture") in SMALL_ARCH:
        return True
    return False
