"""Read-only M13 provenance collection. Run on Slurm; does not register rows or create the final execution record."""
from pathlib import Path
from datetime import datetime
import hashlib
import importlib.util
import json
import os
import re

from auditory_alignment_v3 import core
from auditory_alignment_v3.prior33 import analysis as A, registry_patch as RP, views as V


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("provenance checks run through Slurm")
    os.umask(0o077)
    root, out = Path(core.REPO), Path(core.OUT) / "aln34"
    path = Path(core.OUT) / "make_plan_ext_prior33.py"
    spec = importlib.util.spec_from_file_location("prior_plan_freeze_audit", path)
    P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
    man, _, _ = P.open_manifest(P.MANIFEST, sha(P.MANIFEST))
    files = set(P.training_code_files()) | set(A.code_files())
    files.update(str(p.relative_to(root)) for p in (root / "auditory_alignment_v3/prior33").glob("*.py"))
    files.update(str(p.relative_to(root)) for p in (root / "tests/auditory_alignment_v3/prior33").rglob("*.py"))
    files.update(str(p.relative_to(root)) for p in (root / "tests/auditory_alignment_v3/prior33").rglob("*.sh"))
    files.update(str(p.relative_to(root)) for p in (root / "slurm").glob("aln33_prior*.sbatch"))
    files.update({"private/auditory_alignment_v3/make_plan_ext_prior33.py", "private/auditory_alignment_v3/probe_prior33.py",
                  "private/auditory_alignment_v3/keeper_prior.sh", "slurm/aln34_prior_finalize_cache.sbatch",
                  "private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md",
                  "AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/inherited/PUBLIC_PRIOR_EXECUTION_v3_3.md",
                  "AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/inherited/public_prior_v3_3.yaml",
                  "AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/inherited/OBJECTIVES_v3_3.md"})
    digests = {f: sha(root / f) for f in sorted(files)}
    for g in RP.GROUPS:
        core.FAMILY_CODE[g] = RP.group_files(g)
    core.FAMILY_GROUP.update(RP.FAMILIES)
    rich = json.loads(Path(man.rich_path).read_text())
    manifests = {p: sha(p) for p in (P.MANIFEST, man.rich_path, str(Path(man.root) / "manifest.json"),
                                     str(Path(man.root) / "manifest_rich.json"))}
    tests = {}
    for job in (1043869, 1043888, 1043896, 1043898, 1043905, 1043916):
        logs = list((Path(core.OUT) / "logs").glob(f"*-{job}.log"))
        if len(logs) != 1:
            raise ValueError(f"test log missing or ambiguous: {job}")
        text = logs[0].read_text()
        tests[str(job)] = {"file": str(logs[0].relative_to(root)), "sha256": sha(logs[0]),
                           "summary": [s for s in text.splitlines() if re.search(r"\d+ (passed|failed)|end .*rc=", s)][-4:]}
    result = {"generated": datetime.now().astimezone().isoformat(), "job": os.environ["SLURM_JOB_ID"], "code": digests,
              "manifests": manifests, "group_hashes": {f: core.code_hash(f) for f in RP.FAMILIES}, "tests": tests,
              "core": {k: man.get(k) for k in ("budget", "declared_choices", "inputs", "overlap_scan", "identity_overlap",
                                                "coverage", "seen", "standardiser", "checks", "rich_supplement")},
              "rich": {k: rich.get(k) for k in ("rich", "c7", "declared_choices", "checks", "guard")},
              "production_rows": len(P.build_primary(P.manifest_context(man, man.sha256), "M13 audit only, NOT registered")),
              "record_status": "audit only; M12 GPU receipt still required before final M13"}
    dest = out / "prior33_freeze_audit.json"
    dest.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (out / "prior33_freeze_sha256.txt").write_text("".join(f"{h}  {p}\n" for p, h in digests.items()))
    print(f"M13 audit written: {dest}; {len(digests)} source files; {result['production_rows']} planned rows")
    print(json.dumps({"manifests": manifests, "group_hashes": result["group_hashes"]}, indent=2))


if __name__ == "__main__":
    main()
