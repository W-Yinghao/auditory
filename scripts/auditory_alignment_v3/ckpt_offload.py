"""ALN3 checkpoint offload to /projects (user approval 2026-10-11: "可以把checkpoints迁移到/projects"; ALN2 precedent 2026-10-07).

Live-safe, per file, while the fleet runs:
  - only *_best.pt files of COMPLETED units move: units/<eid>.json exists (written as the runner's very last statement,
    after its final torch.load of best.pt), no claim of <eid> in any pool queue, no <eid>*_resume.pt* present, file older
    than MIN_AGE; files of running units are never touched;
  - checkpoints that any PENDING unit depends on (claimed or queued without a record: C/D_ADAPT base, E_COMPLEMENT base,
    lag-local donor, E_DISTILL teacher candidates, attention twin) stay on home until those dependents are done;
    a pending row of a family/arm the dependency model does not know → the pass is skipped (fail closed);
  - per file: stream-copy to <DEST>/.<name>.part.<tag> computing sha256 → fsync → drop page cache → re-read and verify
    sha256 (+ size) → keep source mtime → rename to <DEST>/<name> → re-check source unchanged and claims/deps again →
    manifest 'linking' line → atomically replace the source path with an absolute symlink to the copy → manifest 'done'.
    torch.load / os.path.exists follow symlinks, so readers are unaffected.
Restore (filesystem is the source of truth; atomic per link):
  for l in $(find private/auditory_alignment_v3/ckpt -maxdepth 1 -type l -lname '/projects/EEG-foundation-model/*'); do
    t=$(readlink "$l"); tmp="$(dirname "$l")/.$(basename "$l").restore.$$"; cp --preserve=timestamps "$t" "$tmp" && mv -T "$tmp" "$l"; done
If a completed unit is ever re-run: remove its symlink first ([ -L ckpt/<eid>_best.pt ] && rm ckpt/<eid>_best.pt), otherwise
the write would go through to /projects. Move/repair tooling must resolve links (os.path.realpath) or use the manifest.
Usage: python ckpt_offload.py [--dry-run] [--once] [--max-files N] [--families A,B] [--interval S] | --verify
Stops on <OUT>/STOP_ckpt_offload, SIGTERM (between files), or when the fleet is idle (no claims, no c3_aln3 jobs, queues
not refreshed for > 1 h). Reviews 2026-10-11 (symlink compatibility; races/failures): both SAFE_WITH_FIXES, fixes applied."""
from __future__ import annotations

import argparse
import errno
import fcntl
import glob
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid

REPO = "/home/infres/yinwang/EEG_auditory"
sys.path.insert(0, REPO)
OUT = f"{REPO}/private/auditory_alignment_v3"
SRC = f"{OUT}/ckpt"
DEST = "<private checkpoint storage>/auditory_alignment_v3/ckpt"
MAN = f"{OUT}/ckpt_offload_manifest.tsv"
LOG = f"{OUT}/logs/ckpt_offload.log"
STOP = f"{OUT}/STOP_ckpt_offload"
LOCK = f"{OUT}/.ckpt_offload.lock"
EID = re.compile(r"^(ALN3X?_[0-9a-f]{16})(?:_[A-Za-z0-9]+)*_best\.pt$")
MIN_AGE = 900            # s since last modification
MIN_FREE_DEST = 200e9    # bytes that must stay free on /projects
FATAL_ERRNO = {errno.ENOSPC, errno.EDQUOT, errno.EIO, errno.ESTALE, errno.EROFS}
TAG = f"{socket.gethostname()}.{os.getpid()}.{uuid.uuid4().hex[:8]}"
# families whose units read no other unit's checkpoint (plain training / probes); D_* only for the lag-local arms
NO_DEPS = {"A_LOCAL", "A_TARGETS", "A_DIMENSION", "A_LOCAL_FACTORS", "B_DENSE", "B_CTRL_ONESTEP", "B_LR_PANEL", "B_LAYER_PROBE",
           "E_LOCAL", "E_GX", "E_GENERIC", "D_COVERAGE", "D_ATTENTION", "B_ALIGNED", "ALN32_LOCAL_SUPPORT", "ALN32_POSTONLY_FM", "ALN32_TRUE_FULL"}  # B_ALIGNED: ADDENDUM_06, no checkpoint dependencies
HANDLED = {"C_COMPLEMENT", "C_CAPACITY_CONTROL", "D_ADAPT", "E_COMPLEMENT", "E_PUBLIC_TRANSFER", "E_DISTILL", "D_ATTENTION", "ALN32_RESIDUAL", "ALN32_SIMPLE_COMPLEMENT"}
_term = False
_POLICY = {}  # D_ADAPT policy cell -> chosen unit (the B/C seed-3401 candidates are complete and immutable)


def _on_term(signum, frame):  # noqa: ARG001
    global _term
    _term = True


def log(msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}"
    with open(LOG, "a") as f:
        f.write(line + "\n")


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        try:
            os.posix_fadvise(f.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
        except (AttributeError, OSError):
            pass
        for chunk in iter(lambda: f.read(16 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def claims():
    return {os.path.basename(d)[:-len(".claim")] for d in glob.glob(f"{OUT}/pool/*/*.claim")}


def queued():
    out = set()
    for q in glob.glob(f"{OUT}/queue_v3_*.txt"):
        if q.endswith("_weights.txt"):
            continue
        out |= {l.split("|", 1)[0] for l in open(q) if l.strip()}
    return out


def all_rows():
    from auditory_alignment_v3 import core
    ext = f"{OUT}/plan_ext.jsonl"
    return core.load_rows() + ([json.loads(l) for l in open(ext)] if os.path.exists(ext) else [])


def has_resume(eid):
    return bool(glob.glob(f"{SRC}/{eid}*_resume.pt*"))


def deps_of(pending, rows):
    """Checkpoint owners read at start by the pending units. Returns (set, uncertain_reason or '')."""
    from auditory_alignment_v3 import run_attention, run_complement, run_distill, run_e_complement, run_transfer
    by = {r["experiment_id"]: r for r in rows}
    out, why = set(), ""
    for e in pending:
        r = by.get(e)
        if r is None:
            why = why or f"pending id {e} not in plan rows"; continue
        f, s = r["family_id"], r["spec"]
        lag = s.get("architecture") == "lag_local_tokens"
        if f.startswith(("D_ADAPT", "D_ATTENTION", "D_COVERAGE")) and not lag:
            # ADDENDUM_04 (2026-10-13) policy arms: D_ADAPT reads the chosen B/C unit (frozen base); the D_COVERAGE complement arm
            # reads the same-population D_COVERAGE lag unit; the D_ATTENTION complement mean_score arm reads the lag-arm unit of the
            # same training task; dense_fm_policy attention rows and learned_temporal derived records read no checkpoint
            from auditory_alignment_v3 import run_attention_policy, run_coverage_policy
            if f == "D_ADAPT":
                k = (r["dataset"], r["subject_fold"], r["content_fold"], r["seed"], s["objective"], s["architecture"])
                if _POLICY.get(k) is None:  # unresolvable cells are re-checked on every pass
                    from auditory_alignment_v3 import policy
                    p = policy.resolve(r, rows, OUT); _POLICY[k] = p["chosen"] if p else None
                if _POLICY[k] is None:
                    why = why or f"D_ADAPT policy arm {e}: training-only policy not resolvable"; continue
                out.add(_POLICY[k]); continue
            if f == "D_COVERAGE":
                lb = run_coverage_policy.lag_base_row(r, rows)
                if lb is None:
                    why = why or f"D_COVERAGE policy arm {e}: no lag base row"; continue
                out.add(lb["experiment_id"]); continue
            if s.get("integrator") == "mean_score" and s["architecture"] == "complement_policy":
                lt = run_attention_policy.lag_twin_row(r, rows)
                if lt is None:
                    why = why or f"D_ATTENTION policy arm {e}: no lag twin row"; continue
                out.add(lt["experiment_id"])
            continue
        if f not in HANDLED and f not in NO_DEPS:
            why = why or f"unmodelled family {f} ({e})"; continue
        try:
            got = []
            if f in ("C_COMPLEMENT", "C_CAPACITY_CONTROL"):
                got = [run_complement.base_row(r, rows)]
            elif f == "D_ADAPT":
                got = [run_complement.base_row({**r, "spec": {**s, "local_architecture": "lag_local_tokens", "window": "full"}}, rows)]
            elif f == "E_COMPLEMENT":
                got = [run_e_complement.base_row(r, rows)]
            elif f == "ALN32_RESIDUAL":
                from auditory_alignment_v3 import residual32
                got = [residual32.base_row(r, rows)]
            elif f == "ALN32_SIMPLE_COMPLEMENT":
                from auditory_alignment_v3 import complement32
                got = [complement32.base_row(r, rows)]
            elif f == "E_PUBLIC_TRANSFER" and s.get("source_architecture") == "lag_local_tokens":
                got = [run_transfer.local_donor_row(r, rows)]
            elif f == "E_DISTILL":
                out |= set(run_distill.candidates(r, rows) or [])
            elif f == "D_ATTENTION" and s.get("integrator") != "mean_score":
                got = [run_attention.twin_row(r, rows)]
            out |= {g["experiment_id"] for g in got if g}
        except Exception as ex:  # noqa: BLE001
            why = why or f"dependency lookup failed for {e} ({f}): {ex!r}"
    return out, why


def dest_reachable(timeout=60):
    res = {}

    def probe():
        try:
            res["ok"] = os.statvfs(os.path.dirname(DEST)).f_bavail >= 0
        except Exception as ex:  # noqa: BLE001
            res["err"] = repr(ex)
    t = threading.Thread(target=probe, daemon=True); t.start(); t.join(timeout)
    return bool(res.get("ok")), res.get("err", "timeout" if t.is_alive() else "")


def ensure_dest():
    for d in (os.path.dirname(DEST), DEST):
        os.makedirs(d, exist_ok=True)
        os.chmod(d, 0o700)


def manifest(state, eid, name, size, sha, src, dst):
    with open(MAN, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{eid}\t{name}\t{size}\t{sha}\t{src}\t{dst}\t{state}\n")
        f.flush(); os.fsync(f.fileno())


def move_one(name, rows):
    """Returns bytes moved, 0 if skipped. Raises OSError for fatal filesystem errors."""
    src, dst = f"{SRC}/{name}", f"{DEST}/{name}"
    eid = EID.match(name).group(1)
    st0 = os.stat(src)
    h_src = None
    if os.path.isfile(dst) and not os.path.islink(dst) and os.path.getsize(dst) == st0.st_size:
        h_src, h_dst = sha_file(src), sha_file(dst)  # reuse a verified copy from an earlier pass
        if h_src != h_dst:
            h_src = None
    if h_src is None:
        tmp = f"{DEST}/.{name}.part.{TAG}"
        try:
            h = hashlib.sha256()
            with open(src, "rb") as fi, open(tmp, "wb") as fo:
                for chunk in iter(lambda: fi.read(16 << 20), b""):
                    h.update(chunk); fo.write(chunk)
                fo.flush(); os.fsync(fo.fileno())
            h_src = h.hexdigest()
            if os.path.getsize(tmp) != st0.st_size or sha_file(tmp) != h_src:
                log(f"ERROR copy verification failed {name}; source kept"); return 0
            os.chmod(tmp, 0o600)
            os.utime(tmp, ns=(st0.st_atime_ns, st0.st_mtime_ns))
            os.replace(tmp, dst)
        finally:
            if os.path.lexists(tmp):
                os.remove(tmp)
    st1 = os.stat(src)
    if os.path.islink(src) or (st1.st_size, st1.st_mtime_ns) != (st0.st_size, st0.st_mtime_ns):
        log(f"SKIP source changed during copy {name}; verified copy left at {dst}"); return 0
    if eid in claims() or has_resume(eid) or not os.path.exists(f"{OUT}/units/{eid}.json"):
        log(f"SKIP {name}: unit pending/resuming; verified copy kept for a later pass"); return 0
    deps, why = deps_of(claims(), rows)  # last-moment re-check against currently claimed units
    if why or eid in deps:
        log(f"SKIP {name}: last-moment dependency check ({why or 'protected'})"); return 0
    lnk = f"{SRC}/.{name}.lnk.{TAG}"
    manifest("linking", eid, name, st0.st_size, h_src, src, dst)
    try:
        if os.path.lexists(lnk):
            os.remove(lnk)
        os.symlink(dst, lnk)
        os.replace(lnk, src)  # atomic: the regular file is replaced by a symlink to the verified copy
    finally:
        if os.path.lexists(lnk):
            os.remove(lnk)
    if not (os.path.islink(src) and os.path.realpath(src) == os.path.realpath(dst) and os.path.getsize(src) == st0.st_size):
        log(f"ERROR post-link check failed {name} (see manifest 'linking' line)"); return 0
    manifest("done", eid, name, st0.st_size, h_src, src, dst)
    return st0.st_size


def one_pass(dry=False, max_files=None, families=None):
    rows = all_rows()
    fam = {r["experiment_id"]: r["family_id"] for r in rows}
    done_ids = {os.path.basename(p)[:-5] for p in glob.glob(f"{OUT}/units/ALN3*.json") if not p.endswith(".FAILED.json")}
    cl = claims()
    pending = cl | {e for e in queued() if e not in done_ids}
    deps, why = deps_of(pending, rows)
    if why:
        log(f"pass skipped (fail closed): {why}")
        return 0, 0
    cands, skipped = [], {"running": 0, "incomplete": 0, "resume": 0, "young": 0, "dependency": 0, "family_filter": 0}
    now = time.time()
    for name in sorted(os.listdir(SRC)):
        m = EID.match(name); p = f"{SRC}/{name}"
        if not m or os.path.islink(p) or not os.path.isfile(p):
            continue
        eid = m.group(1)
        if eid in cl:
            skipped["running"] += 1; continue
        if eid not in done_ids:
            skipped["incomplete"] += 1; continue
        if has_resume(eid):
            skipped["resume"] += 1; continue
        st = os.stat(p)
        if now - st.st_mtime < MIN_AGE:
            skipped["young"] += 1; continue
        if families and fam.get(eid) not in families:
            skipped["family_filter"] += 1; continue
        if eid in deps:
            skipped["dependency"] += 1; continue
        cands.append((name, st.st_size))
    tot = sum(s for _, s in cands)
    if cands or dry:
        log(f"pass: {len(cands)} candidates ({tot / 2**30:.2f} GiB); skipped {skipped}; pending {len(pending)}; protected deps {len(deps)}")
    if dry:
        return len(cands), 0
    if not cands:
        return 0, 0
    ok, err = dest_reachable()
    if not ok:
        log(f"ERROR /projects not reachable ({err}); pass skipped"); return len(cands), 0
    ensure_dest()
    moved = nbytes = 0
    for name, size in (cands[:max_files] if max_files else cands):
        if _term or os.path.exists(STOP):
            log("stop requested; pass interrupted between files"); break
        if shutil.disk_usage(os.path.dirname(DEST)).free < MIN_FREE_DEST:
            log("ERROR /projects free space below the safety margin; pass stopped"); break
        try:
            got = move_one(name, rows)
        except OSError as ex:
            if ex.errno in FATAL_ERRNO:
                log(f"ERROR fatal filesystem error on {name}: {ex!r}; pass aborted"); break
            log(f"ERROR {name}: {ex!r}"); got = 0
        except Exception as ex:  # noqa: BLE001
            log(f"ERROR {name}: {ex!r}"); got = 0
        if got:
            moved += 1; nbytes += got
    log(f"pass done: moved {moved} files, {nbytes / 2**30:.2f} GiB")
    return len(cands), moved


def verify_manifest():
    done = {}
    for line in open(MAN):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 7 and (len(parts) == 7 or parts[7] == "done"):
            done[parts[2]] = parts
    bad = 0
    for name, (t, eid, _, size, sha, src, dst, *_) in sorted(done.items()):
        ok = os.path.islink(src) and os.path.realpath(src) == os.path.realpath(dst) and os.path.getsize(dst) == int(size) and sha_file(dst) == sha
        if not ok:
            bad += 1; log(f"VERIFY MISMATCH {name}")
    links = [l for l in glob.glob(f"{SRC}/*") if os.path.islink(l) and os.readlink(l).startswith("/projects/EEG-foundation-model/")]
    unlisted = [l for l in links if os.path.basename(l) not in done]
    log(f"verify: {len(done)} manifest files, {bad} mismatches, {len(links)} links on disk, {len(unlisted)} links not in the manifest (host {socket.gethostname()})")
    return bad + len(unlisted)


def fleet_idle():
    try:
        q = subprocess.run(["squeue", "-u", os.environ.get("USER", "yinwang"), "-h", "-o", "%j"], capture_output=True, text=True, timeout=60)
        if q.returncode != 0:
            return False
        jobs = q.stdout.split()
    except Exception:  # noqa: BLE001
        return False
    qs = [p for p in glob.glob(f"{OUT}/queue_v3_*.txt") if not p.endswith("_weights.txt")]
    stale = qs and all(time.time() - os.path.getmtime(p) > 3600 for p in qs)
    return not any(j.startswith("c3_aln3") for j in jobs) and not claims() and stale


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--dry-run", action="store_true"); a.add_argument("--once", action="store_true")
    a.add_argument("--max-files", type=int); a.add_argument("--families"); a.add_argument("--interval", type=int, default=600)
    a.add_argument("--verify", action="store_true")
    args = a.parse_args()
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if args.verify:
        sys.exit(1 if verify_manifest() else 0)
    lockf = open(LOCK, "w")
    try:
        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another ckpt_offload instance holds the lock; exiting"); sys.exit(0)
    signal.signal(signal.SIGTERM, _on_term)
    fams = set(args.families.split(",")) if args.families else None
    log(f"start dry={args.dry_run} once={args.once} max_files={args.max_files} families={fams} tag={TAG}")
    idle = 0
    while not _term:
        if os.path.exists(STOP):
            log("STOP file present; exiting"); break
        n_cand, _ = one_pass(args.dry_run, args.max_files, fams)
        if args.once or args.dry_run:
            break
        idle = idle + 1 if (n_cand == 0 and fleet_idle()) else 0
        if idle >= 3:
            log("fleet idle (no claims, no c3_aln3 jobs, queues not refreshed for 1 h) and nothing left; exiting"); break
        for _ in range(args.interval):
            if _term or os.path.exists(STOP):
                break
            time.sleep(1)
    log("exit")


if __name__ == "__main__":
    main()
