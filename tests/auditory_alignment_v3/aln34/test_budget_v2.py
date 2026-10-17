import ast
from pathlib import Path

from auditory_alignment_v3 import local_train
from auditory_alignment_v3.aln34 import budget_local_v2, learning_budget_v2 as B


def test_local_training_equations_unchanged_except_observation():
    original = ast.parse(Path(local_train.__file__).read_text())
    fixed = ast.parse(Path(budget_local_v2.__file__).read_text())
    a = next(n for n in original.body if isinstance(n, ast.FunctionDef) and n.name == 'fit_continuous')
    b = next(n for n in fixed.body if isinstance(n, ast.FunctionDef) and n.name == 'fit_continuous')
    loop = next(n for n in b.body if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == 'ep')
    hook = loop.body.pop()
    assert isinstance(hook, ast.If) and ast.unparse(hook.test) == 'SNAPSHOT is not None'
    assert ast.unparse(hook.body[0]) == 'SNAPSHOT(ep + 1, step, enc, head)'
    assert ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)


def test_v2_identity_and_trajectory_horizon():
    assert B.snapshot_epochs(200, 400) == [50, 100, 200, 400]
    assert B.snapshot_epochs(200, 2) == [2]
    assert B.BASE.name == 'learning_budget_v2'
    assert set(B.FAMILIES) == {'ALN34_BUDGET2_FM', 'ALN34_BUDGET2_LOCAL'}
