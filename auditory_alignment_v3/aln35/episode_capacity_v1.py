"""Operational two-worker allowance; frozen episode execution is unchanged."""
import hashlib
from pathlib import Path

from . import episode_pressure as source

SOURCE_SHA256 = "8b677aae8601b0e40a8237bb0e7aef57293a73db1055e11c45394d37909ca40a"


def fleet_status():
    if hashlib.sha256(Path(source.__file__).read_bytes()).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("Frozen episode readiness/execution source changed")
    status = dict(source.fleet_status())
    status["slots"] = 2
    return status
