"""Validate and stage operational capacity only; no submission or training."""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from auditory_alignment_v3.aln35 import episode_capacity_v1 as capacity
from auditory_alignment_v3.aln35 import episode_pressure as episode
from private.auditory_alignment_v3.aln35 import maintain_fleet as fleet

assert os.environ.get("SLURM_JOB_ID")
os.umask(0o077)
out = fleet.NEWBASE / "capacity_20261019"
out.mkdir(exist_ok=True)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

paths = [fleet.PLUGIN_PATH, fleet.BASE / "fleet_runtime.json"]
before = {str(path): sha(path) for path in paths}
plugins = json.loads(paths[0].read_text())
runtime = json.loads(paths[1].read_text())
proposed = copy.deepcopy(plugins)
entries = [e for e in proposed["plugins"] if e["module"] == "auditory_alignment_v3.aln35.episode_pressure"]
assert len(entries) == 1 and entries[0]["sha256"] == capacity.SOURCE_SHA256
entries[0].update(module="auditory_alignment_v3.aln35.episode_capacity_v1", sha256=sha(capacity.__file__))
(out / "fleet_plugins.before.json").write_text(json.dumps(plugins, indent=2) + "\n")
(out / "fleet_runtime.before.json").write_text(json.dumps(runtime, indent=2) + "\n")
(out / "fleet_plugins.proposed.json").write_text(json.dumps(proposed, indent=2) + "\n")

# Check the existing worker's interprocess lock primitive on the actual claims
# filesystem, without locking an experiment or altering a completed record.
with tempfile.TemporaryDirectory(prefix="capacity-check-", dir=episode.BASE / "claims") as temporary:
    lock_path = Path(temporary) / "probe.lock"
    code = """import fcntl, sys
with open(sys.argv[1], 'a+') as handle:
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit(23)
"""
    with lock_path.open("a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert subprocess.run([sys.executable, "-B", "-c", code, str(lock_path)]).returncode == 23
    assert subprocess.run([sys.executable, "-B", "-c", code, str(lock_path)]).returncode == 0

episode.verify(json.loads(episode.PLAN.read_text()))
status = capacity.fleet_status()
assert status["name"] == "c3_s35episode" and status["lane"] == "s35_episode" and status["slots"] == 2
assert status["state"] == "ready" and status["ready"] >= 2
assert status["submit"] == ["slurm/aln35_episode_pressure.sbatch", "--smoke-job", "1047304", "--max-units", "1"]
assert status["initial"] == []
checked = fleet.plugin_lanes(out / "fleet_plugins.proposed.json")
assert not any(item["state"] == "technical_error" for item in checked), checked
assert len(checked) == len(plugins["plugins"])
assert [item for item in checked if item["name"] == status["name"]][0]["slots"] == 2

# Existing dynamic runtime controls already support two workers for these lanes.
for name in ("breadth_budget", "breadth_curves"):
    assert runtime["extra_lanes"][name][3] == 1
    runtime["extra_lanes"][name][3] = 2
    fleet.CONFIG[name] = fleet.Previous.CONFIG[name] = tuple(runtime["extra_lanes"][name])
    item = fleet.lane(name, fleet.read(fleet.BASE / "fleet_smoke_jobs.json"))
    assert item["state"] == "ready" and item["ready"] >= 2 and item["failed"] == 0, item
(out / "fleet_runtime.proposed.json").write_text(json.dumps(runtime, indent=2) + "\n")
assert all(sha(path) == value for path, value in before.items()), "Live configuration changed during check"
receipt = {"status": "pass", "job": os.environ["SLURM_JOB_ID"], "before_sha256": before,
           "episode_source_sha256": sha(episode.__file__), "episode_plan_sha256": sha(episode.PLAN),
           "episode_claim_exclusion_and_release": "pass", "plugin_validation": "pass",
           "proposed_sha256": {p.name: sha(p) for p in out.glob("*.proposed.json")},
           "capacity_changes": {"s35_episode": [1, 2], "breadth_budget": [1, 2], "breadth_curves": [1, 2]},
           "matched_kept_single_worker": "shared selection refresh uses common temporary output paths",
           "mutations": "new provider and staged configuration only; no live configuration, experiment or Slurm job changed"}
(out / "check_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2), flush=True)
