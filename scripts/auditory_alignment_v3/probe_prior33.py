"""ALN3.4 M12 real-data engineering probe (PUBLIC_PRIOR_DESIGN.md section 7.2).

Run through slurm/aln33_prior_gpu_probe.sbatch. Outputs are confined to a dated
directory under probe_out_prior33. Production registry files and unit records are
never modified. Every phase writes a receipt, including failures. Training budgets
are explicitly truncated and cannot become production evidence.
"""
from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import time
import traceback

import numpy as np
import torch

from auditory_alignment_v3 import core
from auditory_alignment_v3.prior33 import build_rich as BR
from auditory_alignment_v3.prior33 import build_sparrkulee as SK
from auditory_alignment_v3.prior33 import contract as C
from auditory_alignment_v3.prior33 import donor_train as DT
from auditory_alignment_v3.prior33 import losses as L
from auditory_alignment_v3.prior33 import model as MD
from auditory_alignment_v3.prior33 import registry_patch as RP
from auditory_alignment_v3.prior33 import run_bridge as RB
from auditory_alignment_v3.prior33 import run_donor as RD
from auditory_alignment_v3.prior33 import run_target as RT
from auditory_alignment_v3.prior33 import run_zeroshot as RZ
from auditory_alignment_v3.prior33 import sampler as SM
from auditory_alignment_v3.prior33 import select as SEL
from auditory_alignment_v3.prior33 import views as V

BASE = Path(core.OUT) / "probe_out_prior33"
PHASES = ("integrity", "tiny", "short")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(DT._py(value), indent=2, sort_keys=True, allow_nan=False) + "\n")
    os.replace(tmp, path)


def plan_and_manifests(manifest_path=None):
    path = Path(core.OUT) / "make_plan_ext_prior33.py"
    spec = importlib.util.spec_from_file_location("m12_prior33_plan", path)
    plan = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plan)
    manifest_path = manifest_path or plan.MANIFEST
    man, _, _ = plan.open_manifest(manifest_path, sha(manifest_path))
    rows = plan.build_primary(plan.manifest_context(man, man.sha256), "M12 engineering probe; NOT registered production")
    # Exactly the proposed registry entries, in this Python process only.
    for group in RP.GROUPS:
        core.FAMILY_CODE[group] = RP.group_files(group)
    core.FAMILY_GROUP.update(RP.FAMILIES)
    return rows, man


def pick_row(rows, family, dataset, objective="NCE", **spec):
    candidates = [r for r in rows if r["family_id"] == family and r["dataset"] == dataset and r["seed"] == 3401
                  and r["spec"]["objective"] == objective and all(r["spec"].get(k) == v for k, v in spec.items())
                  and r.get("subject_fold") in (None, 0) and r.get("content_fold") in (None, 0)]
    if len(candidates) != 1:
        raise ValueError(f"probe selection {family}/{dataset}/{objective}/{spec}: {len(candidates)} rows")
    return candidates[0]


def check_selections(rows):
    selected = []
    for ds, obj in (("fau", "NCE"), ("fau", "CS_SINGLE"), ("dtu", "NCE"), ("private_bdf", "NCE")):
        selected.append(pick_row(rows, SEL.DONOR, ds, obj, block="core"))
    selected.append(pick_row(rows, SEL.RICH_DONOR, "fau", block="rich"))
    for ds in ("fau", "dtu"):
        selected.append(pick_row(rows, SEL.BRIDGE, ds, member="AP", block="core"))
        for mode in (("A", "B", "C") if ds == "fau" else ("C",)):
            selected.append(pick_row(rows, SEL.ZEROSHOT, ds, member="AP", mode=mode))
    for ds in ("fau", "private_bdf"):
        selected.append(pick_row(rows, SEL.TARGET, ds, init="random", block="core"))
        selected.append(pick_row(rows, SEL.TARGET, ds, member="AP", block="core"))
    return selected


def integrity(man, out):
    report = {"cache_shapes": {}, "rich_clock": {}, "coverage": {}, "alignment": []}
    tables = {}
    for cohort, info in man["cohorts"].items():
        table, items = V.cohort_table(man, cohort)
        tables[cohort] = (table, items)
        streams = V.cohort_streams(man, cohort)
        offsets = np.cumsum([0] + [int(s["length"]) for s in streams[:-1]]).tolist()
        assert offsets == [int(s["offset"]) for s in streams], "envelope presentation offsets"
        for mode, filename in info["caches"].items():
            path = Path(man.root) / info["dir"] / filename
            V.verify_file(man, path)
            mm = np.load(path, mmap_mode="r", allow_pickle=False)
            assert mm.dtype == np.float16 and mm.shape == (int(info["n_rows"]), int(info["n_ch"]))
            for piece in items:
                if piece.get("row_offset") is None or not piece.get("masked"):
                    continue
                masked = [info["layout"].index(C.canonical(name)) for name in piece["masked"]]
                a = int(piece["row_offset"])
                assert not np.any(mm[a:a + int(piece["T_eeg"]), masked]), f"nonzero masked channels: {cohort}/{mode}"
            report["cache_shapes"][f"{cohort}/{mode}"] = list(mm.shape)
            del mm
        report["coverage"][cohort] = {"channels": len(info["layout"]),
                                      "all_cached_masked_channels_zero": True,
                                      "masked_cells_by_piece": {p.get("piece_id", str(i)): len(p.get("masked") or [])
                                                                for i, p in enumerate(items)}}
        if cohort in ("sparrkulee", "fau", "dtu"):
            rs = V.cohort_streams(man, cohort, name="rich_streams")
            checked = [r for r in rs if r["available"] and r.get("clock")][:3]
            assert len(checked) == 3, f"three clock-checked {cohort} rich streams"
            report["rich_clock"][cohort] = [{"name": r["name"], "clock": r["clock"]} for r in checked]
            assert all(abs(r["clock"]["tau"]) <= 1 for r in checked), f"rich {cohort} lag"
    table, items = tables["sparrkulee"]
    root = Path(man.root) / man["cohorts"]["sparrkulee"]["dir"]
    c1 = json.loads((root / SK.RUNS_TABLE).read_text())
    audits = {r["run"]: r for r in (json.loads(line) for line in (root / SK.AUDIT).read_text().splitlines())}
    source_rows, cached_rows, _, _ = SK._layout(c1, audits)
    first_sub = sorted({r["sub"] for r in cached_rows})[0]
    rr = sorted((r for r in cached_rows if r["sub"] == first_sub), key=lambda r: (r["ses"], r["run"]))
    marker, rebuilt = SK.process_participant(c1["src"], rr, SK.restricted_set(c1))
    cache = np.load(root / C.CACHE_FILE["A"], mmap_mode="r", allow_pickle=False)
    by_id = {r["run_id"]: r for r in items}
    for r in rr:
        start, length = int(r["row_offset"]), int(r["T_eeg"])
        assert np.array_equal(rebuilt[r["run_id"]], cache[start:start + length]), "C4 source reproduction differs"
        assert marker["runs"][r["run_id"]]["masked"] == by_id[r["run_id"]]["masked"]
    report["source_reproduction"] = {"participant": first_sub, "runs": len(rr), "fp16_exact": True, "mask_exact": True}
    del rebuilt
    aligned = [r for r in items if (r.get("audit") or {}).get("clock") == "aligned" and r.get("row_offset") is not None
               and all(by_id[q].get("row_offset") is not None for q in audits[r["run_id"]]["refs"])][:3]
    assert len(aligned) == 3
    report["alignment_selection"] = "first three C2-aligned runs in table order with all original reference EEG caches available"
    source_envs = {e["stimulus"]: e for e in c1["envelopes"]}
    for target in aligned:
        er = source_envs[target["stimulus"]]
        raw, _ = SK._load_array(os.path.join(c1["src"], er["file"]), SK.restricted_set(c1), er["sha256"])
        env = SK._dec_env(raw.reshape(-1))
        gram = []
        for rid in audits[target["run_id"]]["refs"]:
            ref = by_id[rid]
            assert ref["row_offset"] is not None and ref["sub"] not in V.RESTRICTED
            a, n = int(ref["row_offset"]), int(ref["T_eeg"])
            eeg = SK._dec_eeg(cache[a:a + n].T)
            gram.append(SK._gram(eeg, env, min(len(env), eeg.shape[1] - SK.DEC_LAGS[-1])))
        a, n = int(target["row_offset"]), int(target["T_eeg"])
        audit = SK.audit_run(SK._dec_eeg(cache[a:a + n].T), env, gram, len(env))
        report["alignment"].append({"run": target["run_id"], "cached_eeg_audit": audit})
        assert all(t is not None and abs(t) <= 4 for t in audit["tau"]), "cached EEG clock exceeds four samples"
    report["seen_channels"] = {target: {"seen": len(set(names) & set(C.MONTAGES[target])), "total": len(C.MONTAGES[target])}
                               for target, names in man["seen"].items() if target in C.MONTAGES}
    report["standardiser"] = man["standardiser"]
    report["rich_sigma"] = {k: man["rich"][k] for k in ("sigma_ss", "sigma_sc", "n_windows")}
    return report


def tiny(man, out):
    det = DT.determinism(torch.device("cuda"))
    t0 = time.time()
    smp = SM.DonorSampler(man, "fau", "core", 3401, "cuda")
    load_seconds = time.time() - t0
    batch = smp.next_batch()
    perm, xm_stats = smp.derangement(batch)
    xm = smp.xm_view(batch, perm)
    state = smp.state()
    next_a = smp.next_batch()
    hash_a = smp.stream_hash()
    smp.load_state(state)
    next_b = smp.next_batch()
    assert hash_a == smp.stream_hash() and torch.equal(next_a.x1, next_b.x1) and torch.equal(next_a.keys, next_b.keys)
    del next_a, next_b
    heads = {k: h.to("cuda").eval() for k, h in MD.fixed_heads(man, man.root).items()}
    seen = man["seen"]["fau"]
    with torch.no_grad():
        sound = heads["env"](batch.y)
    result = {"determinism": det, "sampler_resume_exact": True, "bank_load_seconds": load_seconds,
              "banks": smp.describe(), "xm": xm_stats, "objectives": {}}
    # The gathered input has exactly the declared temporal support; perturb the source bank on both sides of its right edge.
    bank = smp.banks[batch.cohort]
    seg = smp.idx.seg[batch.cohort]
    r = int(batch.seg_ids[0]); piece = int(seg["piece"][r]); start = int(seg["s"][r]); off = int(C.TICK_OFFS[batch.ticks[0, 0]])
    enc = MD.build_shared(seen, seen, 3401).to("cuda").eval()
    pos = int(bank.base[piece]) + start + off
    with torch.no_grad():
        u0 = enc(bank.gather([piece], [start], [off]), layout=bank.layout)
        saved = bank.E[pos + C.L_IN].clone(); bank.E[pos + C.L_IN] += 10
        u_out = enc(bank.gather([piece], [start], [off]), layout=bank.layout)
        bank.E[pos + C.L_IN] = saved
        saved = bank.E[pos + C.L_IN // 2].clone(); bank.E[pos + C.L_IN // 2] += 10
        u_in = enc(bank.gather([piece], [start], [off]), layout=bank.layout)
        bank.E[pos + C.L_IN // 2] = saved
    assert torch.equal(u0, u_out) and not torch.equal(u0, u_in)
    try:
        bank.gather([piece], [bank.guards[0] - 1], [0])
    except ValueError:
        guard_refused = True
    else:
        raise AssertionError("window outside guard accepted")
    result["time_access"] = {"samples": C.L_IN, "outside_max_abs": float((u_out-u0).abs().max()),
                             "inside_max_abs": float((u_in-u0).abs().max()), "guard_refused": guard_refused}
    for objective in ("NCE", "CS_SINGLE"):
        encs = {m: MD.build_shared(seen, seen, 3401).to("cuda") for m in SEL.GROUP_MEMBERS[SEL.DONOR]}
        sigma = DT.calibrate_bandwidths(encs["AP"], smp, heads)
        members = {m: DT._Member(m, e, objective, sigma, L.unknown_clock_families(man), heads) for m, e in encs.items()}
        curves = {m: [] for m in members}
        chance = {}
        with torch.no_grad():
            for m, mem in members.items():
                if objective == "NCE":
                    zero = torch.zeros_like(sound)
                    chance[m] = float(mem.terms(zero, zero, batch, sound, xm)[0])
        torch.cuda.synchronize(); begin = time.time()
        for step in range(301):
            if step % 25 == 0:
                with torch.no_grad():
                    for m, mem in members.items():
                        value = mem.loss(batch, sound, None, xm)
                        assert value is not None and math.isfinite(float(value[0])), f"nonfinite {objective}/{m}"
                        curves[m].append({"step": step, "loss": float(value[0])})
            if step < 300:
                for mem in members.values():
                    mem.step(batch, sound, None, xm, DT.LR, "main")
        torch.cuda.synchronize(); elapsed = time.time() - begin
        for m in ("AP", "XP", "J1", "J025"):
            assert curves[m][-1]["loss"] < curves[m][0]["loss"] - 1e-6, f"fixed-batch objective did not improve: {objective}/{m}"
        # Resume the exact optimiser/model state and RNG, then verify the next three GPU updates.
        mem = members["AP"]; snap = mem.snapshot(); cpu_rng = torch.get_rng_state(); gpu_rng = torch.cuda.get_rng_state_all()
        for _ in range(3): mem.step(batch, sound, None, xm, DT.LR, "main")
        expected = DT._state(mem.enc)
        mem.restore(snap); torch.set_rng_state(cpu_rng); torch.cuda.set_rng_state_all(gpu_rng)
        for _ in range(3): mem.step(batch, sound, None, xm, DT.LR, "main")
        assert all(torch.equal(v, expected[k]) for k, v in DT._state(mem.enc).items()), "GPU resume mismatch"
        result["objectives"][objective] = {"curves": curves, "chance_loss": chance, "sigma": sigma, "seconds": elapsed,
                                          "ms_per_member_step": 1000 * elapsed / (300 * len(members)), "resume_exact": True}
        write(Path(out) / "tiny_progress.json", result)
        del members, encs
        gc.collect(); torch.cuda.empty_cache()
    return result


def load_record(out, row):
    path = Path(out) / "units" / (row["experiment_id"] + ".json")
    record = json.loads(path.read_text())
    assert record["status"] == "complete", (row["experiment_id"], record.get("error"), record.get("traceback"))
    return record


def short(rows, man, out):
    output = str(Path(out) / "short")
    def choose(family, dataset, objective="NCE", **spec):
        return pick_row(rows, family, dataset, objective, **spec)
    report = {"units": [], "engineering_extra_groups": "DTU/private NCE one-ep-eq donor groups preserve leave-target-out provenance for their downstream probes"}
    groups = {}
    for dataset, objective, epoch_equiv in (("fau", "NCE", 2), ("fau", "CS_SINGLE", 1), ("dtu", "NCE", 1), ("private_bdf", "NCE", 1)):
        row = choose(SEL.DONOR, dataset, objective, block="core")
        steps = DT.steps_at(epoch_equiv, man["budget"]["anchors_per_ep_eq"])
        RD.run(row, output, epochs=steps, manifest=man, device="cuda")
        rec = load_record(output, row)
        groups[dataset, objective] = (row, rec)
        report["units"].append({"id": row["experiment_id"], "stage": "donor", "dataset": dataset, "objective": objective,
                               "epoch_equivalents": epoch_equiv, "seconds": rec["seconds"], "truncated": rec["truncated"],
                               "compute": rec.get("compute"), "sampler": rec.get("sampler")})
        write(Path(out) / "short_progress.json", report)
    row = choose(SEL.RICH_DONOR, "fau", block="rich")
    grow, grec = groups["fau", "NCE"]
    # A production rich horizon requires a completed >=30-ep-eq core group. This probe adopts the initial 30-ep-eq schedule
    # solely to test its first ep-eq, and binds the actual short core stream/checkpoint. No production horizon is inferred.
    upstream = {"horizon": {"gid": grow["experiment_id"], "H": 30, "ceiling": False, "limit": 60,
                             "hash_log": grec["stream"]["hash_log"], "final": grec["stream"]["final"],
                             "final_step": grec["stream"]["final_step"], "code_hash": grec["code_hash"]},
                "core_ap": SEL.member_ckpt(output, grow["experiment_id"], "AP", "best")}
    rich_log = {}
    DT.train_donor_group(row, man, "cuda", os.path.join(output, "ckpt", row["experiment_id"]), rich_log,
                         max_steps=DT.steps_at(1, man["budget"]["anchors_per_ep_eq"]), upstream=upstream,
                         code_hash=core.code_hash(row["family_id"]))
    report["rich_probe"] = {"row": row, "log": rich_log, "horizon_override": "engineering only: initial schedule 30, truncated at 1 ep-eq"}
    csx = SM.DonorSampler(man, "dtu", "csx", 3401, "cuda")
    csx_batches = csx.calibration_batches()
    assert "fau_cs" in csx_batches and all(b.cohort != "dtu" for b in csx_batches.values())
    report["csx"] = {"strata": sorted(csx_batches), "shapes": {k: list(b.x1.shape) for k, b in csx_batches.items()}}
    del csx, csx_batches
    gc.collect(); torch.cuda.empty_cache()
    for dataset in ("fau", "dtu"):
        brow = choose(SEL.BRIDGE, dataset, member="AP", block="core")
        RB.run(brow, output, device="cuda", manifest_path=man.path, cache_root=man.root, rows=rows)
        load_record(output, brow)
        for mode in (("A", "B", "C") if dataset == "fau" else ("C",)):
            zrow = choose(SEL.ZEROSHOT, dataset, member="AP", mode=mode)
            RZ.run(zrow, output, device="cuda", manifest_path=man.path, cache_root=man.root, rows=rows)
            rec = load_record(output, zrow)
            report["units"].append({"id": zrow["experiment_id"], "stage": "zero_shot", "dataset": dataset, "mode": mode,
                                   "coverage": rec.get("coverage"), "normalisation_access": rec.get("normalisation_access")})
            write(Path(out) / "short_progress.json", report)
    paired_budgets = {}
    for dataset in ("fau", "private_bdf"):
        for member in (SEL.SCRATCH, "AP"):
            matching = [r for r in rows if r["family_id"] == SEL.TARGET and r["dataset"] == dataset and r["seed"] == 3401
                        and r["spec"]["objective"] == "NCE" and r["spec"]["block"] == "core"
                        and r.get("subject_fold") == 0 and r.get("content_fold") in (None, 0)
                        and ((member == SEL.SCRATCH and r["spec"].get("init") == "random") or r["spec"].get("member") == member)]
            assert len(matching) == 1, (dataset, member, len(matching))
            row = matching[0]
            RT.run(row, output, epochs=2, device="cuda", manifest_path=man.path, cache_root=man.root, rows=rows)
            rec = load_record(output, row)
            if dataset == "private_bdf":
                assert rec["windows_samples_from_epoch_start"] == [[32, 70]], "private input window differs from contract"
            budget = {k: rec.get(k) for k in ("epochs_completed", "optimizer_steps", "steps_per_epoch", "n_fit_segments",
                                             "n_es_segments", "n_train_participants", "n_fit_trials", "n_train_children")}
            paired_budgets.setdefault(dataset, {})[member] = budget
            report["units"].append({"id": row["experiment_id"], "stage": "target", "dataset": dataset, "member": member,
                                   "epochs": 2, "resolved_config": rec["resolved_config"], "coverage": rec["coverage"],
                                   "truncated": rec["truncated"], "budget": budget, "train_seconds": rec["train_seconds"],
                                   "seconds_per_epoch": rec["train_seconds"] / rec["epochs_completed"],
                                   "eval_seconds": rec["eval_seconds"], "schedule_check": rec["schedule_check"],
                                   "windows_samples_from_epoch_start": rec.get("windows_samples_from_epoch_start")})
            write(Path(out) / "short_progress.json", report)
        assert paired_budgets[dataset][SEL.SCRATCH] == paired_budgets[dataset]["AP"], "unequal paired target training budgets"
    report["paired_target_budgets"] = paired_budgets
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("all",) + PHASES, default="all")
    parser.add_argument("--out", default=None)
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--check-only", action="store_true", help="CPU Slurm preflight: imports, row selection, hashes; no training")
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("M12 checks and training must run through Slurm")
    rows, man = plan_and_manifests(args.manifest)
    selected = check_selections(rows)
    if args.check_only:
        print(json.dumps({"status": "preflight_pass", "rows": len(rows), "probe_rows": len(selected),
                          "manifest_sha256": man.sha256, "manifest_rich_sha256": getattr(man, "rich_sha256", None)}, indent=2))
        return
    if not os.environ.get("SLURM_JOB_ID") or not torch.cuda.is_available():
        raise RuntimeError("M12 must run in a Slurm GPU allocation")
    out = Path(args.out or BASE / time.strftime("%Y%m%dT%H%M%S")).resolve()
    if BASE.resolve() not in out.parents:
        raise ValueError("M12 output must be a subdirectory of probe_out_prior33")
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.umask(0o077)
    receipt = {"schema": "aln34_m12_probe_v1", "status": "running", "job": os.environ["SLURM_JOB_ID"],
               "device": torch.cuda.get_device_name(), "out": str(out), "script_sha256": sha(__file__),
               "manifest_sha256": man.sha256, "manifest_rich_sha256": man.rich_sha256,
               "code_hashes": {family: core.code_hash(family) for family in RP.FAMILIES}, "phases": {}}
    for phase in (PHASES if args.phase == "all" else (args.phase,)):
        start = time.time(); torch.cuda.reset_peak_memory_stats()
        print(f"M12 START {phase} {time.strftime('%FT%T')}", flush=True)
        try:
            values = short(rows, man, out) if phase == "short" else globals()[phase](man, out)
            torch.cuda.synchronize()
            peak = torch.cuda.max_memory_allocated()
            if peak > 13 * 1024 ** 3:
                raise RuntimeError(f"GPU peak {peak / 1024**3:.2f} GiB exceeds the V100-16GB 13-GiB budget")
            receipt["phases"][phase] = {"status": "pass", "seconds": time.time()-start, "gpu_peak_bytes": peak,
                                        "host_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, "values": values}
        except BaseException as exc:
            receipt["phases"][phase] = {"status": "failed", "seconds": time.time()-start,
                                        "error": repr(exc), "traceback": traceback.format_exc()}
            receipt["status"] = "failed"
            write(out / "receipt.json", receipt)
            raise
        write(out / "receipt.json", receipt)
        print(f"M12 PASS {phase} seconds={time.time()-start:.1f}", flush=True)
        gc.collect(); torch.cuda.empty_cache()
    receipt["status"] = "pass" if set(receipt["phases"]) == set(PHASES) else "partial_pass"
    write(out / "receipt.json", receipt)


if __name__ == "__main__":
    main()
