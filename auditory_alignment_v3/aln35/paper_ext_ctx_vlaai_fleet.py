"""Read-only fleet readiness shim for the paper-line Table 2 POST-HOC context-matched VLAAI lane (s35_paper_ext_vlaai_ctx, job name
c3_s35pxvctx): paper/ext_context_vlaai.py = the Table 2 VLAAI recipe re-fitted on the proposed system's EEG span [0.203, 4.75) s
(protocol results/auditory_alignment_v3/paper/external_decoders/context_matched/PROTOCOL.json, post_hoc: true).
Every provider module of the fleet path is byte-checked against its frozen sha256, then reloaded in dependency order;
returns ext_context_vlaai.fleet_status() (worker: slurm/aln35_paper_ext_ctx_vlaai.sbatch; slots 2, <= 10 units per job).
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'ext_common': '33de3374f0d0718f8d1ee6a02e39622d940504b59c319414e036aa95b1e3526b',
          'ext_fleet': '766fc3b02323352265e3a2988621187018f168c9ed355b8c708147316859187a',
          'vlaai_torch': '48181327fcea4ef1c9f3764297a80e702c203917857683ad1ac0b92668baa794',
          'ext_vlaai': '91950309731c83cbc6a1eec541c2109257a9322e2f8b1c50bc2e315900dff270',
          'ext_vlaai_v2': '96cd99fbf7608ca1fda30ef2e2de106aa8f3dde51903b18e7f0481988d31a6ff',
          'ext_context': '24c1390fa73a3736755b1a09a9a2adcd7c0cd48faffe8b405b6a60342b129f7a',
          'ext_context_vlaai': '1da423de47c00a0fabbc766a1712d99364a83453af2cf2e07b2134a7282b1f9e'}
DEPENDS = {'aln42/external_eval': '2922109a21f23a36b298ac27aaabcc1d7edc26df590cc05c6b543e935ceb6fb4'}      # byte-checked only (used by the CPU score step)


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    for name, digest in DEPENDS.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / f'{name}.py') == digest, f'dependency changed: {name}'
    for name in FROZEN:
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.paper.{name}'))
        assert B.sha(module.__file__) == FROZEN[name]
    return module.fleet_status()
