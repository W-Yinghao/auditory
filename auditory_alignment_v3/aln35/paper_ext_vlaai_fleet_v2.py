"""Read-only fleet readiness shim for the paper-line Table 2 VLAAI lane, v2 (replaces aln35/paper_ext_vlaai_fleet.py):
paper/ext_vlaai_v2.py = v1 recipe and code with the corrected status-gating swap check (vlaai_v2/CORRECTION_RECEIPT.json).
Every provider module of the fleet path is byte-checked against its frozen sha256, then reloaded in dependency order;
returns ext_vlaai_v2.fleet_status() (worker: slurm/aln35_paper_ext_vlaai_v2.sbatch; same job name c3_s35pxvla and lane id).
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'ext_common': '33de3374f0d0718f8d1ee6a02e39622d940504b59c319414e036aa95b1e3526b',
          'ext_fleet': '766fc3b02323352265e3a2988621187018f168c9ed355b8c708147316859187a',
          'vlaai_torch': '48181327fcea4ef1c9f3764297a80e702c203917857683ad1ac0b92668baa794',
          'ext_vlaai': '91950309731c83cbc6a1eec541c2109257a9322e2f8b1c50bc2e315900dff270',
          'ext_vlaai_v2': '96cd99fbf7608ca1fda30ef2e2de106aa8f3dde51903b18e7f0481988d31a6ff'}
DEPENDS = {'paper/external_decoders': '1abe17dc2bc312189e5199cf00645bad971e2e70433afbbe37d0230f92fa2f9f'}      # byte-checked only (used by ext_vlaai_v2.score)


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    for name, digest in DEPENDS.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / f'{name}.py') == digest, f'dependency changed: {name}'
    for name in FROZEN:
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.paper.{name}'))
        assert B.sha(module.__file__) == FROZEN[name]
    return module.fleet_status()
