"""Generator of auditory_alignment_v3/prior33/fit_target.py (E34_PUBLIC_PRIOR, contract aln33_env64_125ms_v1; module M7;
private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.12, §6.1, §6.6 M7; the gen_local_train.py precedent).

fit_target.py holds fit_continuous_p33 and fit_private_p33: textual copies of fit_continuous and fit_private of
auditory_alignment_v3/local_train.py (the A_LOCAL / E_LOCAL recipe; that file is never edited) with the declared substitutions
of SUBSTITUTIONS only. Every substitution asserts that its anchor occurs exactly once in its function at the time it is applied
(SubstitutionError otherwise: the source drifted), every KEPT line must occur exactly once unchanged, and the output must pass
the FORBIDDEN / REQUIRED post-conditions and compile. The output is a pure function of the source text: no clock, path or
environment enters it, so the same source sha256 regenerates byte-identical output (the header names the full source sha256).

Substitutions (§2.12; the label of each starts with the design's item number):
  1  GridBatcher(coh, spec, row, dev, grid) -> views.TickBatcher(coh, spec, row, dev, manifest) (contract ticks, packed keys)
  2  build_encoder(spec["architecture"], coh.n_ch, d, bt.W, coh.fs) -> model.build_target_encoder(row, coh.layout, manifest,
     donor_state): the 64 Hz geometry only; donor tensors loaded strictly (model.load_donor, strict=True) with the target
     montage's donor-unseen rows opened at W = 0 when the row is pretrained, the target seed otherwise
  3  target_stats(bt, ...) -> the manifest standardiser (sigma, mu = 0); build_head(...) -> SharedFixedHead(sigma, P): the
     envelope head of model.fixed_heads (the stored P, checked against the manifest and the contract), built from the
     manifest's standardiser and envelope projection only, so the rich block's projection files (§2.15, non-blocking; the
     target stage never uses them) are not opened and cannot fail an envelope target unit
  4  Objective(obj_job, ...) -> losses.ContractObjective(obj_job, ..., unknown_clock=unknown_clock_families(manifest)) on the
     continuous path only (the contract NCE with the +-2 s family-clock mask; CS_SINGLE delegates unchanged)
  5  two selection rules: <ckpt_prefix>_best.pt when es_loss improves (primary: a risk on held-out early-stopping content) and
     <ckpt_prefix>_gainsel_best.pt when es_loss - es_loss_mismatched improves (the inherited A_LOCAL / E_LOCAL rule, a
     correct-pairing sensitivity); the resume file carries both best tuples ("5 resume save": the best_gainsel payload only);
     the log records both best epochs and scores, and the curve keeps both series (es_loss and selection_score = es_loss -
     es_loss_mismatched) at every validation
  6  private path: build_encoder(spec["architecture"], 20, d, bt.W, 250) -> build_target_encoder(row, PRIVATE_LAYOUT, manifest,
     donor_state) (the 250 Hz geometry cannot be built); PrivateBatcher -> views.PrivateBatcher64 (window [32, 70) of x64); the
     private Objective stays auditory_alignment.train.Objective (KEPT: its label / prototype path is unchanged); selection as 5
     with es_loss - es_loss_permuted as the sensitivity
Engineering substitutions beyond the design's list (label prefix "engineering:"; listed in the generated header, in
fit_target.SUBSTITUTIONS and in every target unit record under fit_target.substitutions; deviations of the M7 summary, for the
execution record). None of them changes the trajectory of an uninterrupted run:
  -  "engineering: signature": fit_continuous_p33(row, coh, dev, ckpt_prefix, log, sel_weight=None, anchor_weight=None, d=32, *,
     manifest, donor_state) (grid is gone with GridBatcher) and fit_private_p33(row, kids, dev, ckpt_prefix, log, d=32, *,
     manifest, donor_state)
  -  "engineering: return (enc, head, bt)": the target stage trains no selection head (TickBatcher.selection is False), so the
     dropped fourth value of fit_continuous was always None
  -  "engineering: resume at every validation": the resume file is written at every validation (every 5 epochs; A_LOCAL: every
     20), the cadence §2.10 uses for donor groups, so a requeued runfill job loses at most 5 epochs. Saving reads no RNG, so an
     uninterrupted run is unchanged. On CPU a resumed run is bit-identical to an uninterrupted one (models, optimiser,
     scheduler, the numpy and torch CPU RNGs, both best tuples and the curve are restored; tested). On CUDA it is not: like
     A_LOCAL, the target stage sets no cudnn.deterministic and the resume file holds no CUDA RNG state, so a resumed GPU run
     continues from the same state but not bit-identically (as A_LOCAL's own resumes)
  -  `describe` resolves to model.describe (temporal.describe plus the contract geometry, coverage and tensor map): an import,
     not a text substitution

Usage (run as a module; select.py would shadow the standard library when a prior33 file is run by path):
  python -m auditory_alignment_v3.prior33.gen_fit_target            write fit_target.py (tmp file + os.replace)
  python -m auditory_alignment_v3.prior33.gen_fit_target --check    exit 1 unless fit_target.py equals the regenerated text
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SOURCE_REL = "auditory_alignment_v3/local_train.py"
OUTPUT_REL = "auditory_alignment_v3/prior33/fit_target.py"
GENERATOR_REL = "auditory_alignment_v3/prior33/gen_fit_target.py"
SOURCE = os.path.join(REPO, SOURCE_REL)
OUTPUT = os.path.join(REPO, OUTPUT_REL)
FUNCTIONS = {"fit_continuous": "fit_continuous_p33", "fit_private": "fit_private_p33"}   # source function -> generated name


class SubstitutionError(AssertionError):
    """A declared anchor does not occur exactly once in its function (the source drifted), or a post-condition failed."""


# ---------------------------------------------------------------------------------------------------------- declared edits
_SAVE_ALL = 'torch.save({k: m.state_dict() for k, m in mods.items()}, ckpt_prefix + "_best.pt")'
_SAVE_PRIV = 'torch.save({"enc": enc.state_dict(), "protos": protos.detach()}, ckpt_prefix + "_best.pt")'
_RESUMED = 'best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]\n'
ENGINEERING = "engineering: "          # label prefix of the substitutions beyond the design's list (module docstring)
_CADENCE = ("            if (ep + 1) % 20 == 0 and ep + 1 < epochs:\n", "            if ep + 1 < epochs:\n")
_RESUME_TAIL = "rng=rng.bit_generator.state, torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)\n"
_RESUME_TAIL_GS = ("rng=rng.bit_generator.state, torch_rng=torch.get_rng_state(), best=list(best), best_gainsel=list(best_gs),\n"
                   "                             step=step, curve=curve, epoch=ep + 1)\n")

# (source function, label, anchor, replacement); applied in this order, each anchor exactly once in its function
SUBSTITUTIONS = (
    ("fit_continuous", ENGINEERING + "signature",
     "def fit_continuous(row, coh, dev, ckpt_prefix, log, sel_weight=None, anchor_weight=None, d=32, grid=1):\n",
     "def fit_continuous_p33(row, coh, dev, ckpt_prefix, log, sel_weight=None, anchor_weight=None, d=32, *, manifest, donor_state):\n"),
    ("fit_continuous", "1 batcher",
     "    bt = GridBatcher(coh, spec, row, dev, grid)\n",
     "    bt = TickBatcher(coh, spec, row, dev, manifest)\n"),
    ("fit_continuous", "2 encoder",
     '    enc = build_encoder(spec["architecture"], coh.n_ch, d, bt.W, coh.fs).to(dev)\n',
     "    enc = build_target_encoder(row, coh.layout, manifest, donor_state).to(dev)\n"),
    ("fit_continuous", "3 standardiser",
     '    stats = target_stats(bt, np.random.default_rng(row["seed"] + 5))\n',
     "    stats = manifest_standardiser(manifest)\n"),
    ("fit_continuous", "3 head",
     '    head = build_head(spec.get("audio_head", "trainable_head"), bt.audio_dim, d, coh.meta["dataset"], stats).to(dev)\n',
     "    head = shared_head(manifest, stats, bt.audio_dim, d).to(dev)\n"),
    ("fit_continuous", "4 objective",
     "        obj = Objective(obj_job, enc(bt.patches(r0[0])), head(bt.audio(r0[1])))\n",
     "        obj = ContractObjective(obj_job, enc(bt.patches(r0[0])), head(bt.audio(r0[1])), unknown_clock=unknown_clock_families(manifest))\n"),
    ("fit_continuous", "5 best state",
     "    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0\n",
     "    best, best_gs, t0, step, curve, ep0 = (math.inf, -1), (math.inf, -1), time.time(), 0, [], 0\n"),
    ("fit_continuous", "5 resume load", _RESUMED,
     _RESUMED.rstrip("\n") + '; best_gs = tuple(r["best_gainsel"])\n'),
    ("fit_continuous", "5 two checkpoints",
     "            if sel_score < best[0]:\n"
     "                best = (sel_score, ep + 1)\n"
     f"                {_SAVE_ALL}\n",
     "            if es_loss < best[0]:\n"
     "                best = (es_loss, ep + 1)\n"
     f"                {_SAVE_ALL}\n"
     "            if sel_score < best_gs[0]:\n"
     "                best_gs = (sel_score, ep + 1)\n"
     f"                {_SAVE_ALL.replace('_best.pt', '_gainsel_best.pt')}\n"),
    ("fit_continuous", ENGINEERING + "resume at every validation (A_LOCAL: every 20 epochs)", *_CADENCE),
    ("fit_continuous", "5 resume save (best_gainsel in the resume file)",
     "                _save_resume(rpath, **{k: m.state_dict() for k, m in mods.items()}, opt=opt.state_dict(), sched=sched.state_dict(),\n"
     f"                             {_RESUME_TAIL}",
     "                _save_resume(rpath, **{k: m.state_dict() for k, m in mods.items()}, opt=opt.state_dict(), sched=sched.state_dict(),\n"
     f"                             {_RESUME_TAIL_GS}"),
    ("fit_continuous", "5 log",
     '    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],\n'
     '                "selection_rule": ("min es 2AFC loss" if not use_align else "min over validations of es_loss(training pairing) - es_loss(within-batch roll)"),\n',
     '    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_es_loss": best[0],\n'
     '                "best_epoch_gainsel": best_gs[1], "best_selection_score_gainsel": best_gs[0],\n'
     '                "selection_rule": "min over validations of es_loss(training pairing) (primary; <ckpt_prefix>_best.pt)",\n'
     '                "selection_rule_gainsel": "min over validations of es_loss(training pairing) - es_loss(within-batch roll) (sensitivity; '
     '<ckpt_prefix>_gainsel_best.pt)",\n'
     '                "selection_curves": {"primary": "curve[].es_loss", "gainsel": "curve[].selection_score"},\n'),
    ("fit_continuous", ENGINEERING + "return (enc, head, bt)",
     "    return enc, head, bt, sel\n",
     "    return enc, head, bt\n"),
    ("fit_private", ENGINEERING + "signature",
     "def fit_private(row, kids, dev, ckpt_prefix, log, d=32):\n",
     "def fit_private_p33(row, kids, dev, ckpt_prefix, log, d=32, *, manifest, donor_state):\n"),
    ("fit_private", "6 batcher",
     "    bt = PrivateBatcher(kids, spec, row, dev)\n",
     "    bt = PrivateBatcher64(kids, spec, row, dev)\n"),
    ("fit_private", "6 encoder",
     '    enc = build_encoder(spec["architecture"], 20, d, bt.W, 250).to(dev)\n',
     "    enc = build_target_encoder(row, PRIVATE_LAYOUT, manifest, donor_state).to(dev)\n"),
    ("fit_private", "5 best state",
     "    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0\n",
     "    best, best_gs, t0, step, curve, ep0 = (math.inf, -1), (math.inf, -1), time.time(), 0, [], 0\n"),
    ("fit_private", "5 resume load", _RESUMED,
     _RESUMED.rstrip("\n") + '; best_gs = tuple(r["best_gainsel"])\n'),
    ("fit_private", "6 two checkpoints",
     "            if sel < best[0]:\n"
     "                best = (sel, ep + 1)\n"
     f"                {_SAVE_PRIV}\n",
     "            if es_loss < best[0]:\n"
     "                best = (es_loss, ep + 1)\n"
     f"                {_SAVE_PRIV}\n"
     "            if sel < best_gs[0]:\n"
     "                best_gs = (sel, ep + 1)\n"
     f"                {_SAVE_PRIV.replace('_best.pt', '_gainsel_best.pt')}\n"),
    ("fit_private", ENGINEERING + "resume at every validation (A_LOCAL: every 20 epochs)", *_CADENCE),
    ("fit_private", "5 resume save (best_gainsel in the resume file)",
     "                _save_resume(rpath, enc=enc.state_dict(), protos=protos.detach(), opt=opt.state_dict(), sched=sched.state_dict(),\n"
     f"                             {_RESUME_TAIL}",
     "                _save_resume(rpath, enc=enc.state_dict(), protos=protos.detach(), opt=opt.state_dict(), sched=sched.state_dict(),\n"
     f"                             {_RESUME_TAIL_GS}"),
    ("fit_private", "5 log",
     '    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],\n'
     '                "selection_rule": "min over validations of es_loss(training labels) - es_loss(labels permuted within batch)",\n',
     '    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_es_loss": best[0],\n'
     '                "best_epoch_gainsel": best_gs[1], "best_selection_score_gainsel": best_gs[0],\n'
     '                "selection_rule": "min over validations of es_loss(training labels) (primary; <ckpt_prefix>_best.pt)",\n'
     '                "selection_rule_gainsel": "min over validations of es_loss(training labels) - es_loss(labels permuted within batch) '
     '(sensitivity; <ckpt_prefix>_gainsel_best.pt)",\n'
     '                "selection_curves": {"primary": "curve[].es_loss", "gainsel": "curve[].selection_score"},\n'),
)
# lines that must stay exactly as they are, exactly once (§2.12 item 6: the private Objective is the unpatched class)
KEPT = (("fit_private", "6 private objective unchanged", "        obj = Objective(obj_job, enc(P), None, labels0=Y)\n"),)
# post-conditions on the generated functions: substrings that must be absent / present, and pattern counts
FORBIDDEN = {"fit_continuous_p33": ("GridBatcher", "build_encoder(", "target_stats(", "build_head(", "PrivateBatcher", '_last.pt"', "% 20 == 0"),
             "fit_private_p33": ("build_encoder(", "PrivateBatcher(", "ContractObjective", "TickBatcher", "250", '_last.pt"', "% 20 == 0")}
REQUIRED = {"fit_continuous_p33": ("TickBatcher(coh, spec, row, dev, manifest)", "build_target_encoder(row, coh.layout, manifest, donor_state)",
                                   "ContractObjective(obj_job,", 'ckpt_prefix + "_best.pt"', 'ckpt_prefix + "_gainsel_best.pt"',
                                   "best_gainsel=list(best_gs)"),
            "fit_private_p33": ("PrivateBatcher64(kids, spec, row, dev)", "build_target_encoder(row, PRIVATE_LAYOUT, manifest, donor_state)",
                                'ckpt_prefix + "_best.pt"', 'ckpt_prefix + "_gainsel_best.pt"', "best_gainsel=list(best_gs)")}
COUNTS = {"fit_continuous_p33": ((r"(?<![A-Za-z_])Objective\(", 0), (r"\bgrid\b", 0), (r"ContractObjective\(", 1)),
          "fit_private_p33": ((r"(?<![A-Za-z_])Objective\(obj_job, enc\(P\), None, labels0=Y\)", 1), (r"(?<![A-Za-z_])Objective\(", 1))}

HEADER_IMPORTS = '''from __future__ import annotations

import math
import os
import time

import numpy as np
import torch
import torch.nn as nn

from auditory_alignment.train import Objective, _eff_rank, _kernel_stats, _save_resume, cs_diag
from auditory_alignment_v2.train import N_SEL, ROWS, SelectionScore, selection_loss

from .contract import N_TGT, PRIVATE_LAYOUT
from .losses import ContractObjective, unknown_clock_families
from .model import build_target_encoder, describe, fixed_heads
from .views import PrivateBatcher64, TickBatcher, manifest_root
'''

HELPERS = '''

def manifest_standardiser(manifest):
    """§2.12 substitution 3 (target_stats -> the manifest standardiser): (mu, sigma) float32 [8] of the frozen manifest, mu stored
    as zeros (mu == 0, §2.3) and sigma fitted once on the SparrKULee donor fit, so no target-side statistic enters the head."""
    st = manifest["standardiser"]
    mu, sd = (np.asarray(st[k], dtype=np.float64).reshape(-1) for k in ("mu", "sigma"))
    if mu.shape != (N_TGT,) or sd.shape != (N_TGT,) or bool((mu != 0).any()) or not (np.isfinite(sd).all() and (sd > 0).all()):
        raise ValueError(f"manifest standardiser: mu [{N_TGT}] stored as zeros and a finite sigma [{N_TGT}] > 0 expected")
    return mu.astype(np.float32), sd.astype(np.float32)


def shared_head(manifest, stats, in_dim, d):
    """§2.12 substitution 3 (build_head -> SharedFixedHead(sigma, P)): the envelope head of model.fixed_heads (the stored P,
    checked against the manifest and the contract; never regenerated), consistent with `stats`, the 8-sample target and d.
    fixed_heads sees the manifest's standardiser and envelope projection only: the rich block's projections (§2.15, a
    non-blocking parallel block) are never opened, since the target stage trains the envelope target alone."""
    envelope_only = {"standardiser": manifest["standardiser"], "projection": manifest["projection"]}
    head = fixed_heads(envelope_only, manifest_root(manifest))["env"]
    if int(in_dim) != N_TGT or int(d) != int(head.P.shape[0]) or \\
            not np.array_equal(head.std.sd.cpu().numpy(), np.asarray(stats[1], dtype=np.float32)) or bool(head.std.mu.abs().max() != 0):
        raise ValueError(f"shared_head: target width {in_dim} / d {d} / sigma do not match SharedFixedHead {tuple(head.P.shape)}")
    return head
'''


# ---------------------------------------------------------------------------------------------------------- generation
def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def function_sources(text, names=tuple(FUNCTIONS)):
    """{name: source} of the module-level functions `names` of `text` (ast line spans, as gen_local_train.py)."""
    tree, lines, out = ast.parse(text), text.split("\n"), {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names:
            if n.name in out:
                raise SubstitutionError(f"function {n.name} is defined twice in the source")
            if n.decorator_list:
                raise SubstitutionError(f"function {n.name} has decorators; the copy would not carry them")
            out[n.name] = "\n".join(lines[n.lineno - 1:n.end_lineno]) + "\n"
    missing = [n for n in names if n not in out]
    if missing:
        raise SubstitutionError(f"source has no module-level function(s) {missing}")
    return out


def _sub(src, label, anchor, repl):
    n = src.count(anchor)
    if n != 1:
        raise SubstitutionError(f"substitution {label!r}: anchor occurs {n} times (exactly 1 required): {anchor[:100]!r}")
    return src.replace(anchor, repl)


def _short(s, n=96):
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n - 3] + "..."


def label_kind(label):
    """"design" (the label starts with a §2.12 item number 1-6) or "engineering" (ENGINEERING prefix); anything else raises."""
    if re.match(r"[1-6] \S", label):
        return "design"
    if label.startswith(ENGINEERING) and len(label) > len(ENGINEERING):
        return "engineering"
    raise SubstitutionError(f"substitution label {label!r} is neither a design §2.12 item ('<1-6> ...') nor {ENGINEERING!r}...")


def apply_substitutions(funcs):
    """Apply SUBSTITUTIONS in order and check KEPT, FORBIDDEN, REQUIRED and COUNTS -> {generated name: source}."""
    out = dict(funcs)
    labels = [f"{fn}: {label}" for fn, label, _, _ in SUBSTITUTIONS]
    if len(set(labels)) != len(labels):
        raise SubstitutionError("two substitutions of one function share a label")
    for fn, label, _, _ in SUBSTITUTIONS:
        label_kind(label)
    for fn, label, a, b in SUBSTITUTIONS:
        out[fn] = _sub(out[fn], f"{fn}: {label}", a, b)
    for fn, label, line in KEPT:
        if out[fn].count(line) != 1:
            raise SubstitutionError(f"kept line {fn}: {label!r} occurs {out[fn].count(line)} times (exactly 1 required)")
    gen = {FUNCTIONS[fn]: src for fn, src in out.items()}
    for name, src in gen.items():
        if not src.startswith(f"def {name}("):
            raise SubstitutionError(f"generated function {name}: the signature substitution did not apply")
        bad = [t for t in FORBIDDEN[name] if t in src]
        if bad:
            raise SubstitutionError(f"generated function {name} still contains {bad}")
        miss = [t for t in REQUIRED[name] if t not in src]
        if miss:
            raise SubstitutionError(f"generated function {name} lacks {miss}")
        for pat, k in COUNTS[name]:
            if len(re.findall(pat, src)) != k:
                raise SubstitutionError(f"generated function {name}: pattern {pat!r} occurs {len(re.findall(pat, src))} times, {k} required")
    return gen


def generate(source_text):
    """The complete text of fit_target.py for the given local_train.py text (a pure function of it)."""
    sha = sha256_text(source_text)
    gen = apply_substitutions(function_sources(source_text))
    rows = "".join(f"  - {fn} / {label}:\n        {_short(a)!r}\n     -> {_short(b)!r}\n" for fn, label, a, b in SUBSTITUTIONS)
    kept = "".join(f"  = {fn} / {label} (asserted unchanged):\n        {_short(line)!r}\n" for fn, label, line in KEPT)
    labels = "".join(f"    {f'{fn}: {label}'!r},\n" for fn, label, _, _ in SUBSTITUTIONS)
    eng = "".join(f"    {f'{fn}: {label}'!r},\n" for fn, label, _, _ in SUBSTITUTIONS if label_kind(label) == "engineering")
    doc = (f'"""GENERATED by {GENERATOR_REL} - do not edit by hand. Regenerate with\n'
           f"python -m auditory_alignment_v3.prior33.gen_fit_target (add --check to verify this file).\n"
           f"E34_PUBLIC_PRIOR target-supervised training (PUBLIC_PRIOR_DESIGN.md §2.12): fit_continuous_p33 / fit_private_p33 are\n"
           f"textual copies of fit_continuous / fit_private of {SOURCE_REL} (sha256 {sha})\n"
           f"with these substitutions only (each asserted to apply exactly once; the generator's docstring explains them). A label\n"
           f"that starts with a number is that item of design §2.12; a label that starts with {ENGINEERING.strip()!r} is a declared\n"
           f"engineering change beyond the design's list (ENGINEERING_SUBSTITUTIONS), which leaves an uninterrupted run unchanged:\n"
           f"{rows}{kept}"
           f"Name resolution: describe = model.describe; Objective = auditory_alignment.train.Objective (the private path only).\n"
           f'"""\n')
    consts = (f"\nSOURCE = {SOURCE_REL!r}\nSOURCE_SHA256 = {sha!r}\nGENERATOR = {GENERATOR_REL!r}\n"
              f"SUBSTITUTIONS = (\n{labels})\nENGINEERING_SUBSTITUTIONS = (\n{eng})\n")
    body = "\n\n".join(gen[FUNCTIONS[fn]] for fn in FUNCTIONS)
    text = doc + HEADER_IMPORTS + consts + HELPERS + "\n\n" + body
    try:
        compile(text, OUTPUT_REL, "exec")
    except SyntaxError as ex:
        raise SubstitutionError(f"the generated module does not compile: {ex}") from None
    return text


def read_source(path=SOURCE):
    with open(path, encoding="utf-8") as f:
        return f.read()


def check(source=SOURCE, output=OUTPUT):
    """(ok, detail): whether `output` equals generate(source) byte for byte."""
    want = generate(read_source(source))
    try:
        with open(output, encoding="utf-8") as f:
            got = f.read()
    except FileNotFoundError:
        return False, f"{output} does not exist"
    if got == want:
        return True, f"{output} is current (source sha256 {sha256_text(read_source(source))})"
    return False, f"{output} differs from the text generated from {source}"


def write(source=SOURCE, output=OUTPUT):
    text = generate(read_source(source))
    tmp = output + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, output)
    return output, sha256_text(text)


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--check", action="store_true", help="verify fit_target.py instead of writing it")
    a.add_argument("--source", default=SOURCE)
    a.add_argument("--output", default=OUTPUT)
    args = a.parse_args(argv)
    if args.check:
        ok, detail = check(args.source, args.output)
        print(detail)
        return 0 if ok else 1
    path, sha = write(args.source, args.output)
    print(f"written {path} (sha256 {sha}); {len(SUBSTITUTIONS)} substitutions, {len(KEPT)} kept line(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
