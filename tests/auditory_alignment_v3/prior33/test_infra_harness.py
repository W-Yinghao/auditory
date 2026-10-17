"""M10 infrastructure (PUBLIC_PRIOR_DESIGN.md §6.5, §7.1 item 15): runs infra/run_harness.sh, which drives the real
slurm/aln33_prior_pool.sbatch and private/auditory_alignment_v3/keeper_prior.sh with fake squeue / sbatch / nvidia-smi and a fake
unit runner in a temporary directory, and applies the make_queue / ckpt_offload / watch_anyhost patches to temporary copies of
the live files and tests them there. CPU only, about 3-5 minutes (its waits are event-based, so a loaded node makes it slower,
not flaky); never touches the live pool, queue, units or ckpt files. The harness runs once per module (fixture `harness`).

Before and after deployment (§6.5 live-edit steps 3, 5 and 6) the harness runs every check: a deployed live file (its sha256 is
the patch's patched-sha256) is tested as it is, and the unpatched file that the comparisons, the line count and the recipes use
is its reverse patch, pinned by the header's live-sha256. Only a live file that carries the patch marker but has changed since
deployment (neither sha256) is beyond the patch checks: the harness reports that file's checks as 'n/a' and runs everything
else, so test_pool_keeper_and_patches still passes while test_patch_checks_apply skips and names the file. The marker the
harness reads (P33MARK) is one of the strings below that only the prior33 patches add, checked against the patch files and the
unpatched live files. ALN33_HARNESS_LIVE=<dir> makes both the harness and deployed() read the three live files from <dir>."""
import hashlib
import os
import re
import shutil
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.join(HERE, "infra", "run_harness.sh")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
LIVE = os.environ.get("ALN33_HARNESS_LIVE") or os.path.join(REPO, "private", "auditory_alignment_v3")
PATCHES = os.path.join(REPO, "private", "auditory_alignment_v3", "aln34", "prior33_patches")
MARKERS = {  # live file -> strings that only its patch (prior33_patches/<stem>.prior33.patch) adds
    "make_queue.py": ("E34_PUBLIC_PRIOR", 'QUEUES["prior"]'),
    "ckpt_offload.py": ("E34_PUBLIC_PRIOR", "P33_FAMILIES"),
    "watch_anyhost.sh": ("E34_PUBLIC_PRIOR", "queue_v3_prior"),
}
HARNESS_MARK = "E34_PUBLIC_PRIOR"   # run_harness.sh: P33MARK, its test for 'changed after deployment'


def deployed():
    """[(live file, marker)] for every prior33 patch marker that a live file already carries."""
    found = []
    for name, marks in MARKERS.items():
        try:
            with open(os.path.join(LIVE, name), encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        found += [(name, m) for m in marks if m in text]
    return found


def _sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_markers_are_added_by_the_patches_only():
    """Every marker is on an added line of its file's patch and on no context or removed line, and deployed() reports nothing for
    a live file that is still the unpatched one (its sha256 is the patch's live-sha256): only a deployed patch can make deployed()
    or the harness's P33MARK test report it. The harness reads the first marker of every file."""
    with open(HARNESS, encoding="utf-8") as f:
        assert f"\nP33MARK={HARNESS_MARK} " in f.read(), "run_harness.sh no longer defines P33MARK as " + HARNESS_MARK
    found = deployed()
    for name, marks in MARKERS.items():
        assert marks[0] == HARNESS_MARK, name
        path = os.path.join(PATCHES, os.path.splitext(name)[0] + ".prior33.patch")
        if not os.path.exists(path):
            pytest.skip(f"no patch file {os.path.relpath(path, REPO)}")
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
        body = [ln for ln in lines if not ln.startswith("#")]   # the header is '#' comment lines
        added = "\n".join(ln[1:] for ln in body if ln.startswith("+") and not ln.startswith("+++"))
        kept = "\n".join(ln[1:] for ln in body if ln[:1] in (" ", "-") and not ln.startswith("---"))
        for m in marks:
            assert m in added and m not in kept, (name, m)
        live_sha = [re.match(r"# live-sha256: *([0-9a-f]{64})", ln) for ln in lines]
        live_sha = [m.group(1) for m in live_sha if m]
        assert len(live_sha) == 1, (name, "live-sha256 header")
        live = os.path.join(LIVE, name)
        if os.path.exists(live) and _sha256(live) == live_sha[0]:   # still unpatched: no marker may be found in it
            assert not [m for n, m in found if n == name], (name, [m for n, m in found if n == name])


@pytest.fixture(scope="module")
def harness(tmp_path_factory):
    if shutil.which("bash") is None or shutil.which("patch") is None:
        pytest.skip("needs bash and patch")
    env = {**os.environ, "TMPDIR": str(tmp_path_factory.mktemp("aln33_infra")), "ALN33_HARNESS_KEEP": "1"}  # pytest rotates it
    return subprocess.run(["bash", HARNESS], capture_output=True, text=True, env=env, timeout=2400)


def _tail(r):
    return (r.stdout[-6000:] + "\n" + r.stderr[-3000:]).strip()


def test_pool_keeper_and_patches(harness):
    """Every harness check passes: pool, keeper, lock, refresher, sbatch files, and every patch check that applies."""
    lines = harness.stdout.splitlines()
    assert harness.returncode == 0, _tail(harness)
    assert lines and re.search(r"\b0 failed\b", lines[-1]), _tail(harness)


def test_patch_checks_apply(harness):
    """The three prior33 patches were checked, not deployed or deployed (harness patch states). A live file that has changed
    since its deployment cannot be checked against its patch any more: the harness reports it 'n/a', and this test skips."""
    lines = harness.stdout.splitlines()
    na = [ln[len("  n/a  "):] for ln in lines if ln.startswith("  n/a  ")]
    if na:
        pytest.skip("the prior33 patch checks do not apply to every live file (" + "; ".join(na) + "). The pool, keeper, lock and "
                    "refresher checks ran (test_pool_keeper_and_patches). A file named here no longer matches its patch: pin "
                    "the harness to the new file (a regenerated patch) or drop that patch from it.")
    for name in ("watch_anyhost", "make_queue", "ckpt_offload"):
        state = [ln for ln in lines if ln.startswith(f"  ok   {name} patch applies to a copy of the live file")
                 or ln.startswith(f"  ok   {name} patch is deployed: ")]
        assert len(state) == 1, (name, _tail(harness))
