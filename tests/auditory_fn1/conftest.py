"""Make the fn1 suite importable without shadowing the source package.

A `tests/auditory_fn1/__init__.py` would turn this directory into a package named
`auditory_fn1`, which under pytest's default import mode collides with the real source
package of the same name. That exact collision is recorded elsewhere in this repository
as a job that failed during collection with zero fits. There is deliberately no
`__init__.py` here; this conftest only guarantees the repository root is importable, so
the suite runs under either import mode and from any working directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
