"""Byte-derived local fit with an end-of-epoch observation hook only.

Source: local_train.fit_continuous, unchanged update/selection/resume equations.
The AST equivalence test removes the hook and compares to the live source.
"""
from ..local_train import *  # existing trainer globals
from ..local_train import _eff_rank, _kernel_stats, _save_resume

SNAPSHOT = None

def fit_continuous(row, coh, dev, ckpt_prefix, log, sel_weight=None, anchor_weight=None, d=32, grid=1):
    spec = row["spec"]
    obj_name = spec["objective"]
    n_seg = max(2, ROWS.get(obj_name, 256) // 8)
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bt = GridBatcher(coh, spec, row, dev, grid)
    enc = build_encoder(spec["architecture"], coh.n_ch, d, bt.W, coh.fs).to(dev)
    stats = target_stats(bt, np.random.default_rng(row["seed"] + 5))
    head = build_head(spec.get("audio_head", "trainable_head"), bt.audio_dim, d, coh.meta["dataset"], stats).to(dev)
    task = spec.get("training_task", "paired_alignment")
    use_align = task != "selection_only"
    sel = SelectionScore(d, "bilinear" if obj_name == "CS_SINGLE" else "cosine").to(dev) if bt.selection else None
    params = [p for m in (enc, head, sel) if m is not None for p in m.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=1e-3, weight_decay=1e-4)
    epochs = int(spec.get("epochs", 200))
    steps_per_epoch = max(1, len(bt.fit) // n_seg)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    calib = next(bt.epoch_batches(np.random.default_rng(row["seed"] + 99), n_seg))
    obj_job = {"objective": "NCE" if obj_name == "SELECTION_CE" else obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}
    with torch.no_grad():
        r0 = bt.rows(calib, np.random.default_rng(row["seed"] + 98))
        obj = Objective(obj_job, enc(bt.patches(r0[0])), head(bt.audio(r0[1])))
    es_rng = np.random.default_rng(12345)
    es_sel = []
    while len(es_sel) < N_SEL:
        got = [b for b, _ in zip(bt.epoch_batches(es_rng, n_seg, bt.es), range(N_SEL - len(es_sel)))]
        if not got:
            break
        es_sel += got
    es_sets = [(bt.rows(b, np.random.default_rng(k)), bt.rows(b, np.random.default_rng(k), roll=True), len(b)) for k, b in enumerate(es_sel)]
    sw = 1.0 if sel_weight is None else sel_weight
    aw = 0.0 if anchor_weight is None else anchor_weight

    def batch_loss(rws, n_b, rng_l, train_mode):
        u, v = enc(bt.patches(rws[0])), head(bt.audio(rws[1]))
        loss, parts = 0.0, {}
        if use_align:
            la, _ = obj(u, v, keys=rws[2]); loss = loss + la; parts["align"] = float(la)
        if bt.selection:
            vi = head(bt.audio(rws[3]))
            ls, acc = selection_loss(sel, u, v, vi, rws[4], n_b, rng_l)
            loss = loss + (sw if use_align else 1.0) * ls; parts["selection"] = float(ls); parts["sel_acc"] = acc
        if aw and train_mode:
            ax = head.aux_loss()
            if ax is not None:
                loss = loss + aw * ax; parts["anchor"] = float(ax)
        return loss, parts, u, v

    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0
    rpath = ckpt_prefix + "_resume.pt"
    mods = {"enc": enc, "head": head, **({"sel": sel} if sel is not None else {})}
    if os.path.exists(rpath):
        r = torch.load(rpath, map_location=dev, weights_only=False)
        for k, m in mods.items():
            m.load_state_dict(r[k])
        opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
        rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu()); best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]
        log["resumed_from_epoch"] = ep0
    for ep in range(ep0, epochs):
        for m in mods.values():
            m.train()
        tl, gns, nonfin = [], [], 0
        for batch in bt.epoch_batches(rng, n_seg):
            rws = bt.rows(batch, rng)
            loss, parts, _, _ = batch_loss(rws, len(batch), rng, True)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        if ep % 5 == 4 or ep == epochs - 1:
            for m in mods.values():
                m.eval()
            with torch.no_grad():
                el, elr, accs, dm, dx = [], [], [], [], []
                for (rws, rr, n_b) in es_sets:
                    l_, parts, u, v = batch_loss(rws, n_b, np.random.default_rng(0), False)
                    lr_, _, _, vr = batch_loss(rr, n_b, np.random.default_rng(0), False)
                    el.append(float(l_)); elr.append(float(lr_))
                    if "sel_acc" in parts:
                        accs.append(parts["sel_acc"])
                    if obj.sigma_v is not None:
                        dm.append(cs_diag(u, v, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v)); dx.append(cs_diag(u, vr, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v))
                es_loss, es_mm = float(np.mean(el)), float(np.mean(elr))
                # selection-only: the legal mismatch does not define the task; select on the 2AFC loss itself
                sel_score = es_loss if not use_align else es_loss - es_mm
                avg = lambda L, k: float(np.mean([x[k] for x in L])) if L else None
                rec = {"epoch": ep + 1, "step": step, "train_loss": float(np.mean(tl)) if tl else None, "es_loss": es_loss, "es_loss_mismatched": es_mm,
                       "selection_score": sel_score, "es_sel_acc": float(np.mean(accs)) if accs else None,
                       "grad_norm": float(np.mean(gns)) if gns else None, "nonfinite_steps": nonfin, "seconds": round(time.time() - t0, 1),
                       "es_cs_true_nats": avg(dm, "cs_qmi_nats"), "es_cs_mismatched_nats": avg(dx, "cs_qmi_nats"),
                       "u_eff_rank": _eff_rank(u), "kernel_u": _kernel_stats(u, obj.sigma_u), "lr": float(sched.get_last_lr()[0])}
            curve.append(rec)
            if sel_score < best[0]:
                best = (sel_score, ep + 1)
                torch.save({k: m.state_dict() for k, m in mods.items()}, ckpt_prefix + "_best.pt")
            if (ep + 1) % 20 == 0 and ep + 1 < epochs:
                _save_resume(rpath, **{k: m.state_dict() for k, m in mods.items()}, opt=opt.state_dict(), sched=sched.state_dict(),
                             rng=rng.bit_generator.state, torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)
        if SNAPSHOT is not None:
            SNAPSHOT(ep + 1, step, enc, head)
    if os.path.exists(rpath):
        os.remove(rpath)
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],
                "selection_rule": ("min es 2AFC loss" if not use_align else "min over validations of es_loss(training pairing) - es_loss(within-batch roll)"),
                "epochs_completed": epochs, "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_segments": len(bt.fit),
                "n_es_segments": len(bt.es), "n_train_participants": len(bt.train_p), "train_seconds": round(time.time() - t0, 1),
                "encoder": describe(enc), "windows_samples": [list(w) for w in bt.W], "window_rule": "legacy_plus1" if spec["architecture"] == "legacy_pool4" else "half_open",
                "audio_head": spec.get("audio_head"), "selection_weight": sw if bt.selection else None, "anchor_weight": aw or None})
    sd = torch.load(ckpt_prefix + "_best.pt", map_location=dev)
    for k, m in mods.items():
        m.load_state_dict(sd[k]); m.eval()
    return enc, head, bt, sel

