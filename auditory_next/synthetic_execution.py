"""Frozen synthetic mechanism audit: 600 route worlds, plus 60 G0 fixtures.

N1/N3: 60 candidates x600 independent trials; N2: 60x80 bags x8 trials.
Fixed generator parameters are mechanism checks, not fitted empirical power
models. All neural cases share one 1000/2000 training-only extension decision.
Raw scores only: no inner calibration/head fits beyond the fixed task catalog.
Missing numerical outcomes remain unknown in every planned-world denominator.
"""
import json
from pathlib import Path
import pickle
import traceback

import numpy as np
import pandas as pd
from scipy.stats import beta
import torch

from auditory5.contracts import FitScope
from auditory5.probes import CandidateTabularScaler
from . import synthetic_worlds as worlds
from .a2_residual_audit import make_residual_world, audit_residual_world
from .fitting import WeightedTransform, fit_cases, predict_logits, array_hash
from .n2_features import fit_weighted_pca8, transform_pca8, fit_rff16, transform_rff16
from .readouts import population_weights, ce_bits
from .provenance import ROOT, digest, object_hash, write_json, require_slurm, finish

TRIALS_PER_CANDIDATE = 600
BAGS_PER_CANDIDATE = 80
WORLD_CANDIDATES = 60
SPECS = {
    "N1": (("logistic", "H"), ("mlp32", "HP"), ("mlp32", "HPB"), ("mlp32", "HPBnoise")),
    "N2": tuple(("logistic", view) for view in ("H", "HMU", "HMUVAR", "HMUMU", "HVAR", "HRFF")),
    "N3": tuple((family, view) for family in ("logistic", "mlp32") for view in ("H", "HP", "Hnoise")),
    "G0": (("logistic", "feature_injection"),),
    "A2": (("ridge", "background_audit"),),
}
MECHANISMS = {"N1": tuple(worlds.N1_WORLDS), "N2": tuple(worlds.N2_WORLDS), "N3": tuple(worlds.N3_WORLDS),
              "A2": ("null", "predictable_nuisance", "individual_stimulus"), "G0": ("feature_injection",)}


def planned_worlds():
    result = []
    for packet in ("A2", "N1", "N2", "N3", "G0"):
        for mechanism in MECHANISMS[packet]:
            count = 100 if packet == "A2" else 60 if packet == "G0" else 30
            for repeat in range(count):
                key = f"{packet}_{mechanism}_{repeat:03d}"
                seed = int(object_hash(dict(base_seed=20260917, packet=packet, mechanism=mechanism, repeat=repeat))[:8], 16)
                bootstrap_seed = int(object_hash(dict(base_seed=20260917, world=key, stream="candidate_bootstrap"))[:8], 16)
                result.append(dict(packet=packet, mechanism=mechanism, world_index=repeat, id=key, seed=seed,
                    bootstrap_seed=bootstrap_seed, specs=SPECS[packet], route_world=packet != "G0"))
    return result


def _validate_world(world, *, candidates=60):
    y, g = np.asarray(world["y"]), np.asarray(world["candidate_id"], str)
    tr, te = np.asarray(world["train_mask"]), np.asarray(world["test_mask"])
    if (y.ndim != 1 or not np.isin(y, [0, 1]).all() or g.shape != y.shape or tr.shape != y.shape or
            te.shape != y.shape or tr.dtype != bool or te.dtype != bool or np.any(tr & te) or not (tr | te).all()):
        raise ValueError("SYNTHETIC_OBSERVATION_PARTITION")
    if len(set(g)) != candidates or set(g[tr]) & set(g[te]) or not tr.any() or not te.any():
        raise ValueError("SYNTHETIC_CANDIDATE_PARTITION")
    if any(set(y[g == group]) != {0, 1} for group in np.unique(g)):
        raise ValueError("SYNTHETIC_CANDIDATE_MISSING_CLASS")
    return y, g, tr, te


def make_world(spec, *, trials_per_candidate=600, bags_per_candidate=80):
    packet, mechanism, seed = spec["packet"], spec["mechanism"], spec["seed"]
    if packet == "A2":
        design = spec.get("a2_design")
        if design is None:
            # Small pure fixture default. The execution entry point requires
            # the real frozen support counts before constructing any world.
            return make_residual_world(mechanism, n_train=40, n_test=20, seed=seed)
        return make_residual_world(mechanism, n_train=design["train"], n_test=design["test"], seed=seed,
            noise_scale_train=np.full((design["train"], 2), design["half_contrast_noise_sd"]),
            noise_scale_test=np.full((design["test"], 2), design["half_contrast_noise_sd"]))
    if packet == "N1":
        value = worlds.N1_WORLDS[mechanism](60 * trials_per_candidate, seed, observations_per_group=trials_per_candidate)
    elif packet == "N3":
        value = worlds.N3_WORLDS[mechanism](60 * trials_per_candidate, seed, observations_per_group=trials_per_candidate)
    elif packet == "N2":
        value = worlds.N2_WORLDS[mechanism](60 * bags_per_candidate, 8, seed, bags_per_group=bags_per_candidate)
    elif packet == "G0":
        # Separate, deliberately small dimensionality fixtures, not part of the
        # 600 route worlds or a claim of real-cohort power at eight trials/child.
        rng = np.random.default_rng(seed)
        dimension = 64 if spec["world_index"] % 2 == 0 else 400
        y, group = np.tile([0, 1], 240), np.repeat(np.arange(60), 8)
        x = rng.normal(size=(480, dimension))
        injected = spec["world_index"] >= 30
        if injected:
            x[:, 0] += 2 * y - 1
        order = rng.permutation(60)
        value = dict(y=y, X=x, candidate_id=np.array([f"synthetic_{i}" for i in group]),
            group_id=group, train_mask=np.isin(group, order[:36]), test_mask=np.isin(group, order[36:]),
            injected=injected, input_dimension=dimension)
    else:
        raise ValueError("SYNTHETIC_PACKET")
    value["candidate_id"] = np.array([spec["id"] + "_" + name for name in value["candidate_id"]])
    _validate_world(value)
    return value


def build_views(world, packet, seed):
    """Train-only scale/PCA/RFF and independent noise; no readout fitting."""
    y, groups, train, test = _validate_world(world)
    scope = FitScope(tuple(np.unique(groups[train])), test_groups=tuple(np.unique(groups[test])))
    artifacts = {}
    if packet in ("N1", "N3"):
        h, p, b = [np.asarray(world[name], float) for name in ("H", "P", "B")]
        reference = b if packet == "N1" else p
        scale = CandidateTabularScaler().fit(reference[train], groups[train], scope)
        noise = np.random.default_rng(seed ^ 0xA31F).normal(size=reference.shape) * scale.scale_ + scale.mean_
        artifacts["noise_training_scale"] = scale
        views = dict(H=h, HP=np.c_[h, p], HPB=np.c_[h, p, b], HPBnoise=np.c_[h, p, noise]) if packet == "N1" else dict(H=h, HP=np.c_[h, p], Hnoise=np.c_[h, noise])
    elif packet == "N2":
        bags = np.asarray(world["bags"], float)
        k, dimension = bags.shape[1:]
        if k != 8 or dimension != 2 or not np.isfinite(bags).all():
            raise ValueError("SYNTHETIC_N2_FIXED_BAGS")
        trial_train = bags[train].reshape(-1, dimension)
        pca = fit_weighted_pca8(trial_train, np.repeat(groups[train], k))
        z = transform_pca8(bags.reshape(-1, dimension), pca).reshape(len(bags), k, -1)
        rff = fit_rff16(z[train].reshape(-1, z.shape[-1]), seed=11)
        mu, variance = z.mean(axis=1), np.log(z.var(axis=1, ddof=1) + 1e-6)
        rff_mean = transform_rff16(z.reshape(-1, z.shape[-1]), rff).reshape(len(z), k, 16).mean(axis=1)
        h = np.asarray(world["H_BAG"], float)
        views = dict(H=h, HMU=np.c_[h, mu], HMUVAR=np.c_[h, mu, variance], HMUMU=np.c_[h, mu, mu], HVAR=np.c_[h, variance], HRFF=np.c_[h, rff_mean])
        artifacts.update(pca=pca, rff=rff)
    elif packet == "G0":
        views = dict(feature_injection=world["X"])
    else:
        raise ValueError("SYNTHETIC_VIEW_PACKET")
    if set(views) != {view for _, view in SPECS[packet]} or any(len(x) != len(y) or not np.isfinite(x).all() for x in views.values()):
        raise ValueError("SYNTHETIC_COMPLETE_VIEW_MATRIX")
    return views, artifacts


def paired_loss_contrasts(losses, pairs, *, seed, threshold):
    """2000 shared candidate draws, after candidate losses have been formed."""
    if not losses.index.is_unique or len(losses) < 2 or not np.isfinite(losses.to_numpy(float)).all():
        raise ValueError("SYNTHETIC_COMPLETE_CANDIDATE_LOSSES")
    table = losses.sort_index()
    values = table.to_numpy(float)
    draws = np.random.default_rng(seed).integers(0, len(values), (2000, len(values)))
    means = values.mean(axis=0)
    boot = values[draws].mean(axis=1)
    result = {}
    for name, (baseline, augmented) in pairs.items():
        a, b = table.columns.get_loc(baseline), table.columns.get_loc(augmented)
        estimate, samples = means[a] - means[b], boot[:, a] - boot[:, b]
        lo, hi = np.quantile(samples, [.025, .975])
        result[name] = dict(estimate=float(estimate), ci_lower=float(lo), ci_upper=float(hi),
            threshold=threshold, n_candidates=len(values), n_bootstrap=2000,
            screen=bool(estimate >= threshold and lo > 0), bootstrap_scope="fixed_fitted_predictions_no_refit")
    return result


def identity_bootstrap(matrix, ids, *, seed, n_boot=2000):
    """Vectorized matching bootstrap excludes duplicate copies of one identity."""
    m, ids = np.asarray(matrix, float), np.asarray(ids, str)
    if m.shape != (len(ids), len(ids)) or len(ids) < 2 or len(set(ids)) != len(ids) or not np.isfinite(m).all():
        raise ValueError("SYNTHETIC_MATCHING_MATRIX")
    n = len(ids)
    index = np.random.default_rng(seed).integers(0, n, (n_boot, n))
    counts = np.zeros((n_boot, n), int)
    np.add.at(counts, (np.arange(n_boot)[:, None], index), 1)
    diagonal = np.diag(m)
    numerator = np.einsum("bi,ij,bj->b", counts, m, counts) - (counts ** 2) @ diagonal
    denominator = n * n - (counts ** 2).sum(axis=1)
    samples = counts @ diagonal / n - np.divide(numerator, denominator, out=np.full(n_boot, np.nan), where=denominator > 0)
    mask = ~np.eye(n, dtype=bool)
    finite = samples[np.isfinite(samples)]
    return dict(estimate=float(diagonal.mean() - m[mask].mean()),
        ci_lower=float(np.quantile(finite, .025)) if len(finite) else None,
        ci_upper=float(np.quantile(finite, .975)) if len(finite) else None,
        invalid_replicates=int(n_boot - len(finite)), n_candidates=n, n_bootstrap=n_boot,
        bootstrap_scope="fixed_predictions_identity_draws; duplicate identities excluded from mismatched pairs")


def rate_summary(outcomes, expected):
    """Unknown outcomes stay in the fixed denominator, with identification bounds."""
    if expected < 1 or len(outcomes) != expected or len({row["world_id"] for row in outcomes}) != expected:
        raise ValueError("SYNTHETIC_PLANNED_WORLD_DENOMINATOR")
    evaluated = [r for r in outcomes if r["status"] == "EVALUATED"]
    if any(type(row["screen"]) is not bool for row in evaluated):
        raise ValueError("SYNTHETIC_EVALUATED_SCREEN_REQUIRED")
    positive = sum(r["screen"] is True for r in evaluated)
    unknown = expected - len(evaluated)
    lower = 0. if positive == 0 else float(beta.ppf(.025, positive, expected - positive + 1))
    maximum = positive + unknown
    upper = 1. if maximum == expected else float(beta.ppf(.975, maximum + 1, expected - maximum))
    return dict(n_planned=expected, n_evaluable=len(evaluated), n_positive=positive, n_unknown=unknown,
        n_numerical_failure=sum(r["status"] == "NUMERICAL_FAILURE" for r in outcomes),
        observed_positive_fraction_of_planned=positive / expected,
        positive_rate_among_evaluable=positive / len(evaluated) if evaluated else None,
        identified_rate_lower=positive / expected, identified_rate_upper=maximum / expected,
        monte_carlo_ci_lower=lower, monte_carlo_ci_upper=upper,
        monte_carlo_ci_definition="Clopper-Pearson envelope over every possible outcome of unknown worlds",
        unknowns_are_not_negative=True)


def _source_plan(task_plan, hashes):
    path = Path(task_plan["task_csv"])
    if not path.resolve().is_relative_to(ROOT / "private/auditory_next_v2"):
        raise ValueError("SYNTHETIC_PRIVATE_TASK_PLAN")
    for source in (path, path.parent / "plan.json", path.parent / "completion.json"):
        hashes[str(source)] = digest(source)
    if (hashes[str(path)] != task_plan["task_csv_hash"] or
            object_hash(json.loads((path.parent / "plan.json").read_text())) != object_hash(task_plan) or
            json.loads((path.parent / "completion.json").read_text())["status"] != "PASS"):
        raise ValueError("SYNTHETIC_TASK_PLAN_HASH")
    # "null" is an actual frozen mechanism label, not a missing CSV value.
    catalog = pd.read_csv(path, keep_default_na=False, na_values={"world_index": [""]})
    own = catalog[catalog["mode"].eq("synthetic") & catalog.fit_stage.eq("synthetic")]
    if len(own) != 1920 or not own.fit_index.is_unique or int(own.neural.sum()) != 630:
        raise ValueError("SYNTHETIC_FROZEN_1920_FITS_630_NEURAL")
    for spec in planned_worlds():
        part = own[own.packet.eq(spec["packet"]) & own.world_index.eq(spec["world_index"])]
        if spec["packet"] != "G0":
            part = part[part.mechanism.eq(spec["mechanism"])]
        if len(part) != len(spec["specs"]) or set(zip(part.family, part.view)) != set(spec["specs"]):
            raise ValueError("SYNTHETIC_COMPLETE_WORLD_TASK_MATRIX")
        population = "equal_candidate" if spec["packet"] == "A2" else "P_bal" if spec["packet"] in ("N2", "G0") else "P_nat"
        if not part.population.eq(population).all() or not part.fit_stage.eq("synthetic").all():
            raise ValueError("SYNTHETIC_TASK_POPULATION")
    contract = ROOT / "private/auditory_next_v2" / task_plan["contract_run"] / "completion.json"
    hashes[str(contract)] = digest(contract)
    if json.loads(contract.read_text())["status"] != "PASS":
        raise ValueError("SYNTHETIC_CONTRACT_GATE")
    return own


def _save_pickle(path, value):
    with Path(path).open("xb") as stream:
        pickle.dump(value, stream, protocol=pickle.HIGHEST_PROTOCOL)


def prepare_cases(specifications, destination):
    """Persist evaluation separately; returned fitting cases contain train only."""
    destination.mkdir(mode=0o700)
    cases, manifest = [], []
    for spec in specifications:
        folder = destination / spec["id"]
        folder.mkdir(mode=0o700)
        world = make_world(spec)
        if spec["packet"] == "A2":
            _save_pickle(folder / "world.pkl", world)
            manifest.append(dict(spec, population="equal_candidate", fit_ids=[], folder=str(folder)))
            continue
        y, groups, train, test = _validate_world(world)
        views, feature_artifacts = build_views(world, spec["packet"], spec["seed"])
        population = "P_bal" if spec["packet"] in ("N2", "G0") else "P_nat"
        weight = population_weights(y[train], groups[train], population)
        scope = dict(fit_groups=sorted(set(groups[train])), validation_groups=[], test_groups=sorted(set(groups[test])))
        train_y = y[train].astype(int)
        np.savez(folder / "evaluation_labels.npz", y=y[test], groups=groups[test])
        fit_ids = []
        transforms = {}
        for view, raw in views.items():
            transform = WeightedTransform().fit(raw[train], weight)
            transforms[view] = transform
            transformed = transform.transform(raw)
            np.save(folder / f"{view}_test.npy", transformed[test], allow_pickle=False)
            # A single shared training array per view, even when both readout
            # families use it; no repeated real EEG or all-world test bank RAM.
            training = np.ascontiguousarray(transformed[train])
            np.save(folder / f"{view}_train.npy", training, allow_pickle=False)
            for family, current_view in spec["specs"]:
                if current_view != view:
                    continue
                identifier = spec["id"] + "__" + family + "__" + view
                cases.append(dict(id=identifier, family=family, x=training, y=train_y, weights=weight,
                    scope=scope, feature_scope_id=object_hash(dict(world=spec["id"], scope=scope, view=view)),
                    C=1., width=32))
                fit_ids.append(identifier)
        np.savez(folder / "training_labels_weights.npz", y=train_y, groups=groups[train], weights=weight)
        _save_pickle(folder / "feature_transforms.pkl", dict(transforms=transforms, **feature_artifacts))
        info = dict(spec, population=population, fit_ids=fit_ids, folder=str(folder),
            candidates=60, train_candidates=len(set(groups[train])), test_candidates=len(set(groups[test])),
            training_observations=int(train.sum()), testing_observations=int(test.sum()),
            observation_unit="bag" if spec["packet"] == "N2" else "trial",
            input_dimension=world.get("input_dimension"), injected=world.get("injected"))
        manifest.append(info)
    if len(cases) != 1620 or sum(c["family"] == "mlp32" for c in cases) != 630:
        raise ValueError("SYNTHETIC_FIT_INPUT_COUNT")
    write_json(destination / "world_manifest.json", manifest)
    return cases, manifest


def _candidate_losses(scores, y, groups, population):
    return {group: ce_bits(scores[groups == group], y[groups == group],
        population_weights(y[groups == group], groups[groups == group], population)) for group in np.unique(groups)}


def _comparisons(packet, family):
    if packet == "N1":
        return {"main": ("mlp32__HP", "mlp32__HPB"), "noise_margin": ("mlp32__HPBnoise", "mlp32__HPB")}, .005
    if packet == "N2":
        return {"main": ("logistic__HMU", "logistic__HMUVAR"), "duplicate_margin": ("logistic__HMUMU", "logistic__HMUVAR"),
                "RFF_margin": ("logistic__HMU", "logistic__HRFF")}, .01
    if packet == "N3":
        return {"main": (family + "__H", family + "__HP"), "noise_margin": (family + "__Hnoise", family + "__HP")}, .005
    return {"main": ("prior", "logistic__feature_injection")}, .01


def _mechanism_expectation(world):
    packet = world["packet"]
    mechanism = ("injected" if world["injected"] else "null") if packet == "G0" else world["mechanism"]
    expected = (mechanism in ("BACKGROUND_KEY", "ADDITIVE_NOISE") if packet == "N1" else
                mechanism == "COVARIANCE_SIGNAL" if packet == "N2" else
                mechanism == "EEG_INCREMENT" if packet == "N3" else bool(world["injected"]))
    return mechanism, bool(expected)


def score_worlds(manifest, models, receipts, destination):
    receipt = {r["fit_id"]: r for r in receipts}
    output, losses = [], []
    for world in manifest:
        if world["packet"] == "A2":
            continue
        mechanism, expected = _mechanism_expectation(world)
        complete = all(identifier in models and receipt.get(identifier, {}).get("numerical_status") == "OPTIMIZATION_STABLE"
                       for identifier in world["fit_ids"])
        families = ("logistic", "mlp32") if world["packet"] == "N3" else ("mlp32",) if world["packet"] == "N1" else ("logistic",)
        if not complete:
            for family in families:
                output.append(dict(world_id=world["id"], packet=world["packet"], mechanism=mechanism,
                    world_index=world["world_index"], family=family, status="NUMERICAL_FAILURE", screen=None,
                    expected_positive=expected,
                    reason="at least one prescribed head in the complete world matrix is unresolved"))
            continue
        folder = Path(world["folder"])
        with np.load(folder / "evaluation_labels.npz", allow_pickle=False) as data:
            y, groups = data["y"], data["groups"].astype(str)
        columns = {}
        for family, view in world["specs"]:
            identifier = world["id"] + "__" + family + "__" + view
            x = np.load(folder / f"{view}_test.npy", mmap_mode="r")
            score = np.asarray(predict_logits(models[identifier], x))
            np.save(folder / f"{family}_{view}_raw_test_logits.npy", score, allow_pickle=False)
            column = family + "__" + view
            columns[column] = _candidate_losses(score, y, groups, world["population"])
            for group, value in columns[column].items():
                losses.append(dict(world_id=world["id"], candidate=group, family=family, view=view, ce_bits=value))
        table = pd.DataFrame(columns)
        if world["packet"] == "G0":
            table["prior"] = 1.
        table.to_parquet(folder / "candidate_losses.parquet")
        for family in families:
            pairs, threshold = _comparisons(world["packet"], family)
            contrast = paired_loss_contrasts(table, pairs, seed=world["bootstrap_seed"], threshold=threshold)
            control = "duplicate_margin" if world["packet"] == "N2" else "noise_margin"
            screen = contrast["main"]["screen"] and (control not in contrast or contrast[control]["ci_lower"] > 0)
            output.append(dict(world_id=world["id"], packet=world["packet"], mechanism=mechanism,
                world_index=world["world_index"], family=family, status="EVALUATED", screen=bool(screen),
                expected_positive=bool(expected), contrasts=contrast, candidate_mean_CE=table.mean().to_dict(),
                probability="raw_uncalibrated", input_dimension=world["input_dimension"],
                claim_scope="budgeted mechanism contrast; not the complete real-route control matrix"))
    pd.DataFrame(losses).to_parquet(destination / "all_candidate_losses.parquet", index=False)
    write_json(destination / "world_results.json", output)
    return output


def _matrix(a, b, metric):
    dot = a @ b.T
    if metric == "inner_product":
        return dot
    norm = np.linalg.norm(a, axis=1)[:, None] * np.linalg.norm(b, axis=1)[None, :]
    return None if np.any(norm == 0) else dot / norm


def run_a2(manifest, destination):
    rows, outcomes = [], []
    count = 0
    for world in manifest:
        if world["packet"] != "A2":
            continue
        folder = Path(world["folder"])
        with (folder / "world.pkl").open("rb") as stream:
            values = pickle.load(stream)
        receipt = dict(fit_id=world["id"] + "__ridge__background_audit", family="ridge", alpha=10.,
            task_fit_index=world["task_fit_indices"][0],
            training_background_hash=array_hash(values["train"]["background"]),
            training_delta_hash=array_hash(values["train"]["delta"]),
            train_candidates=len(values["train"]["candidate_ids"]), test_candidates=len(values["test"]["candidate_ids"]),
            support_design=world["a2_design"], fit_scope="train candidate half means only",
            shared_draw_conditions=["zero", "fixed", "fitted"])
        write_json(folder / "ridge_start.json", receipt)
        audit = audit_residual_world(values)  # Exactly one train-only ridge fit.
        count += 1
        write_json(folder / "ridge_completion.json", dict(receipt, status="PASS",
            max_pair_error=max(a["max_pair_error"] for a in audit["conditions"].values()),
            max_matching_gain_error=max(a["matching_gain_error"] for a in audit["conditions"].values())))
        _save_pickle(folder / "residual_audit.pkl", audit)
        test = values["test"]
        predictions = dict(zero=np.zeros_like(test["delta"]), fixed=test["background"] @ (2 * values["true_weight"]),
                           fitted=audit["fitted_predictor"].predict(test["background"]))
        for condition, prediction in predictions.items():
            statistics = {}
            for diagnostic in ("max_pair_error", "matching_gain_error"):
                rows.append(dict(world_id=world["id"], mechanism=world["mechanism"], condition=condition,
                    component=diagnostic, metric="identity_error", estimate=audit["conditions"][condition][diagnostic],
                    status="IDENTITY_AUDITED"))
            for name, array in (("delta", test["delta"]), ("prediction", prediction), ("residual", test["delta"] - prediction)):
                for metric in ("cosine", "inner_product"):
                    matrix = _matrix(array[:, 0], array[:, 1], metric)
                    result = dict(status="UNDEFINED_ZERO_NORM", estimate=None, ci_lower=None, ci_upper=None) if matrix is None else dict(
                        status="EVALUATED", **identity_bootstrap(matrix, test["candidate_ids"], seed=world["bootstrap_seed"]))
                    rows.append(dict(world_id=world["id"], mechanism=world["mechanism"], condition=condition,
                        component=name, metric=metric, **result))
                    statistics[name, metric] = result
            for term, value in audit["conditions"][condition].items():
                if term in ("delta_delta", "minus_delta_prediction", "minus_prediction_delta", "prediction_prediction", "residual"):
                    rows.append(dict(world_id=world["id"], mechanism=world["mechanism"], condition=condition,
                        component=term, metric="decomposition_inner_product", estimate=value["gain"],
                        matched=value["matched"], mismatched=value["mismatched"], status="IDENTITY_AUDITED"))
            for component in ("delta", "residual"):
                result = statistics[component, "cosine"]
                evaluable = result["status"] == "EVALUATED" and result["ci_lower"] is not None
                outcomes.append(dict(world_id=world["id"], packet="A2", mechanism=world["mechanism"],
                    family=condition + "__" + component, status="EVALUATED" if evaluable else "UNDEFINED",
                    screen=bool(result["estimate"] >= .05 and result["ci_lower"] > 0) if evaluable else None,
                    expected_positive=world["mechanism"] == "individual_stimulus",
                    interpretation="shared-W residual repeatability is not recovered stimulus information",
                    shared_draw_conditions=True))
    if count != 300:
        raise ValueError("SYNTHETIC_A2_EXACT_300_RIDGE_FITS")
    pd.DataFrame(rows).to_parquet(destination / "A2_all_world_statistics.parquet", index=False)
    write_json(destination / "A2_world_results.json", outcomes)
    return outcomes


def aggregate_rates(outcomes):
    """Separate conditions/families; no pooling of repeated shared-world draws."""
    groups = {}
    for row in outcomes:
        key = row["packet"], row["mechanism"], row["family"]
        groups.setdefault(key, []).append(row)
    result = []
    for (packet, mechanism, family), rows in sorted(groups.items()):
        expected = 100 if packet == "A2" else 30
        positive = {r["expected_positive"] for r in rows}
        if len(positive) != 1:
            raise ValueError("SYNTHETIC_FROZEN_MECHANISM_EXPECTATION")
        main = [r["contrasts"]["main"]["estimate"] for r in rows if r["status"] == "EVALUATED" and "contrasts" in r]
        result.append(dict(packet=packet, mechanism=mechanism, family=family,
            rate_role="recovery" if positive.pop() else "false_positive_tendency",
            rate_question="stimulus-specific interpretation of matching" if packet == "A2" else "prespecified incremental contrast",
            main_estimate_mean_among_evaluable=float(np.mean(main)) if main else None,
            main_estimate_n_evaluable=len(main),
            units="cosine" if packet == "A2" else "bits/bag" if packet == "N2" else "bits/trial",
            shared_draw_conditions=packet in ("A2", "N3"), **rate_summary(rows, expected)))
    return result


def _bind_tasks(specifications, catalog):
    """One-to-one binding to the frozen allowance; no implicit extra head fits."""
    bindings = {}
    used = []
    for spec in specifications:
        part = catalog[catalog.packet.eq(spec["packet"]) & catalog.world_index.eq(spec["world_index"])]
        if spec["packet"] != "G0":
            part = part[part.mechanism.eq(spec["mechanism"])]
        spec["task_fit_indices"] = []
        for family, view in spec["specs"]:
            own = part[part.family.eq(family) & part.view.eq(view)]
            if len(own) != 1:
                raise ValueError("SYNTHETIC_TASK_BINDING")
            index = int(own.iloc[0].fit_index)
            bindings[spec["id"] + "__" + family + "__" + view] = index
            spec["task_fit_indices"].append(index)
            used.append(index)
    if len(used) != 1920 or len(set(used)) != 1920 or set(used) != set(catalog.fit_index):
        raise ValueError("SYNTHETIC_ALLOWANCE_BIJECTION")
    return bindings


def _verify_sources(hashes):
    if any(digest(Path(path)) != before for path, before in hashes.items()):
        raise ValueError("SYNTHETIC_FROZEN_SOURCE_CHANGED")


def a2_support_design(overlap, draw, folds):
    """Metadata-only support size and unit-noise contrast variance, no EEG."""
    omega, groups = tuple(overlap["omega"]), set(overlap["groups"])
    if (len(omega) != 2 or overlap["trials_per_cell"] != 6 or overlap["repetitions"] != 20 or
            overlap["status"] != "SUFFICIENT_FOR_SCREEN" or len(groups) < 25 or
            tuple(draw["omega"]) != omega or draw["definition_hash"] != overlap["definition_hash"] or
            set(draw["groups"]) != groups or len(draw["groups"]) != len(groups) or
            overlap["cell_weights"] != [.5, .5] or draw["cell_weights"] != [.5, .5] or draw["seed"] != 20260917):
        raise ValueError("SYNTHETIC_A2_FROZEN_TWO_CELL_QUOTA")
    regions = [r for r in overlap["candidates"] if tuple(r["omega"]) == omega]
    if len(regions) != 1 or set(regions[0]["groups"]) != groups or not regions[0]["sufficient"]:
        raise ValueError("SYNTHETIC_A2_CHOSEN_SUPPORT")
    expected_counts = {int(f): (int(tr), int(te)) for f, tr, te in regions[0]["fold_counts"]}
    result, seen = [], []
    for fold in sorted(folds["folds"], key=lambda f: f["outer_fold"]):
        tr, te = groups & set(fold["train_groups"]), groups & set(fold["test_groups"])
        number = int(fold["outer_fold"])
        if (tr & te or tr | te != groups or len(tr) < 12 or len(te) < 2 or
                expected_counts.get(number) != (len(tr), len(te))):
            raise ValueError("SYNTHETIC_A2_FOLD_SUPPORT")
        seen.extend(te)
        # Delta=sum q*(class1 mean-class0 mean), each class mean uses six
        # independent unit-variance trial errors in each selected cell.
        result.append(dict(outer_fold=number, train=len(tr), test=len(te),
            half_contrast_noise_sd=float(np.sqrt(2 * sum(q*q for q in draw["cell_weights"]) / 6)),
            trials_per_cell_half_class=6, selected_cells=2, trial_noise_variance=1.,
            repeat_noise_reduction=False))
    if len(result) != 5 or len({r["outer_fold"] for r in result}) != 5 or set(seen) != groups or len(seen) != len(groups):
        raise ValueError("SYNTHETIC_A2_FIVE_FOLD_PARTITION")
    return result


def _a2_design_source(registry, task_plan, hashes):
    base = ROOT / "private/auditory_next_v2" / task_plan["support_run"]
    if not base.resolve().is_relative_to(ROOT / "private/auditory_next_v2"):
        raise ValueError("SYNTHETIC_A2_PRIVATE_SUPPORT")
    paths = [base / name for name in ("A2_overlap.json", "A2_draw_definition.json", "completion.json", "support_definition.json")]
    split_path = ROOT / registry["legacy_splits"]
    if not split_path.resolve().is_relative_to(ROOT / "private"):
        raise ValueError("SYNTHETIC_PRIVATE_LEGACY_SPLIT")
    paths.append(split_path)
    for path in paths:
        hashes[str(path)] = digest(path)
    overlap, draw, complete, definition, folds = [json.loads(path.read_text()) for path in paths]
    if (complete["status"] != "PASS" or definition["frozen_before_features"] is not True or
            hashes[str(split_path)] != definition["fold_hash"] or hashes[str(split_path)] != registry["legacy_split_sha256"]):
        raise ValueError("SYNTHETIC_A2_SUPPORT_PROVENANCE")
    return a2_support_design(overlap, draw, folds)


def _a2_aggregate(destination, public):
    table = pd.read_parquet(destination / "A2_all_world_statistics.parquet")
    aggregates = []
    for key, rows in table.groupby(["mechanism", "condition", "component", "metric"], sort=True):
        value = rows.estimate.to_numpy(float)
        finite = value[np.isfinite(value)]
        if len(rows) != 100:
            raise ValueError("SYNTHETIC_A2_STATISTIC_WORLD_COUNT")
        aggregates.append(dict(zip(("mechanism", "condition", "component", "metric"), key),
            n_planned=100, n_defined=len(finite), n_undefined=100-len(finite),
            estimate_mean=float(finite.mean()) if len(finite) else None,
            estimate_max=float(finite.max()) if len(finite) else None,
            scope="shared draw conditions; undefined zero norms are not zero effects"))
    pd.DataFrame(aggregates).to_csv(public / "A2_residual_audit_aggregate.csv", index=False)


def _smoke(specifications):
    selected, seen, result = [], set(), []
    for spec in specifications:
        key = spec["packet"], spec["mechanism"]
        if (spec["packet"] != "G0" and key not in seen) or (spec["packet"] == "G0" and spec["world_index"] in (0, 1, 30, 31)):
            selected.append(spec)
            seen.add(key)
    for spec in selected:
        world = make_world(spec)
        if spec["packet"] == "A2":
            result.append(dict(packet="A2", mechanism=spec["mechanism"],
                train_candidates=len(world["train"]["candidate_ids"]), test_candidates=len(world["test"]["candidate_ids"]),
                half_means_per_candidate=2, background_dimension=8, delta_dimension=8))
        else:
            y, g, train, test = _validate_world(world)
            counts = pd.crosstab(g, y)
            result.append(dict(packet=spec["packet"], mechanism=spec["mechanism"], candidates=len(set(g)),
                train_candidates=len(set(g[train])), test_candidates=len(set(g[test])),
                observations=len(y), minimum_candidate_class_count=int(counts.min().min()),
                unit="bag" if spec["packet"] == "N2" else "trial", input_dimension=world.get("input_dimension")))
    return result


def run(config, registry, site, dest, public, report, task_plan, smoke=False):
    """Fixed-budget synthetic packet. CLI owns Slurm allocation and hard timeout.

    No real feature/clinical loader is called. The two-hour allocation is not a
    license to lower the frozen sample counts. A killed job has no completion;
    its planned-world manifest and fit states remain available to a budget audit.
    """
    require_slurm()
    dest, public, report = map(Path, (dest, public, report))
    for path, base in ((dest, "private"), (public, "results"), (report, "reports")):
        if not path.resolve().is_relative_to(ROOT / base / "auditory_next_v2"):
            raise ValueError("SYNTHETIC_OUTPUT_ROOT")
    if (dest / "synthetic_definition.json").exists() or (dest / "completion.json").exists():
        raise FileExistsError("SYNTHETIC_RUN_IMMUTABLE")
    r = config["readouts"]
    if (not isinstance(smoke, bool) or r["new_fixed_logistic_C"] != 1. or r["new_fixed_mlp_lambda"] != .001 or
            r["seed"] != 11 or r["precision"] != "float64" or r["steps_initial"] != 1000 or
            r["steps_extension_once"] != 1000 or r["schedule_horizon_steps"] != 2000 or
            r["learning_rate"] != .001 or r["new_mlp_weight_decay"] != 0. or r["repair_hidden_primary"] != 32 or
            config["validation"]["fixed_oof_cluster_bootstrap"] != 2000 or
            config["A2"]["effect_floor"] != .05 or config["N1"]["background_gain_floor_bits"] != .005 or
            config["N2"]["main_gain_floor_bits_per_bag"] != .01 or config["N3"]["main_gain_floor_bits"] != .005 or
            config["N2"]["main_k"] != 8 or config["N2"]["variance_epsilon"] != 1e-6 or
            config["N2"]["rff_dimension"] != 16 or config["N2"]["trial_pca_dimension"] != 8):
        raise ValueError("SYNTHETIC_FROZEN_ESTIMATOR_CONFIG")
    hashes = {}
    catalog = _source_plan(task_plan, hashes)
    if task_plan["resources"]["reservations"]["synthetic_gpu_hours"] != 2 or task_plan["synthetic_worlds"] != 600:
        raise ValueError("SYNTHETIC_FROZEN_RESOURCE_CATALOG")
    specifications = planned_worlds()
    a2_design = _a2_design_source(registry, task_plan, hashes)
    for spec in specifications:
        if spec["packet"] == "A2":
            spec["a2_design"] = a2_design[spec["world_index"] % 5]
    bindings = _bind_tasks(specifications, catalog)
    write_json(dest / "fit_task_binding.json", bindings)
    write_json(dest / "planned_worlds.json", specifications)
    definition = dict(route_worlds=600, independent_worlds_by_packet=dict(A2=300, N1=120, N2=90, N3=90),
        G0_separate_fixtures=60, A2_ridge_fits=300, classifier_fits=1620, neural_fits=630,
        total_fits=1920, calibration_fits=0, new_encoder_fits=0, neural_lambda=.001, logistic_C=1.,
        A2_ridge_alpha=10., A2_candidate_and_noise_design=a2_design,
        A2_fold_rule="world_index % 5; same qualified frozen Omega counts in all shared W conditions",
        A2_missingness_scope="post-eligibility equal quotas; excluded candidates are not imputed",
        N_candidates=dict(total=60, train=36, test=24), N1_N3_trials_per_candidate=600,
        N2_bags_per_candidate=80, N2_trials_per_bag=8,
        G0_fixture_trials_per_candidate=8, G0_dimensions=[64, 400], G0_injection_coordinate=0,
        G0_injection_class_mean_difference=2., G0_null_worlds=30, G0_injected_worlds=30,
        G0_scope="small independent feature-dimension fixtures; not real split/cohort power",
        raw_scores_only=True, calibration_status="BUDGET_LIMITED_NO_INNER_OOF",
        head_seed=11, world_seed_rule="SHA256 of base_seed=20260917/packet/mechanism/repetition, first32bits",
        bootstrap_seed_rule="separate SHA256 stream candidate_bootstrap/world_id/base_seed; shared within each world",
        paired_candidate_bootstrap=2000, bootstrap_scope="fixed fitted predictions, no refit",
        population=dict(N1="P_nat", N2="P_bal", N3="P_nat", G0="P_bal", A2="equal_candidate"),
        family_barrier="all630NN initial1000; if any unstable all to2000; no test predictions before terminal budget",
        hard_budget_gpu_hours=2, timeout_status="BUDGET_LIMITED; no reduced-sample retry",
        claims="mechanism diagnostics; not empirical power fitted to real EEG or clinical validation",
        A2_conditions_share_draw=True, N3_families_share_draw=True,
        incomplete_required_heads="whole world unresolved; retained in planned denominator",
        source_task_plan_hash=object_hash(task_plan), source_config_hash=object_hash(config),
        source_registry_hash=object_hash(registry), source_site_hash=object_hash(site), clinical_inputs=False)
    write_json(dest / "synthetic_definition.json", definition)
    write_json(public / "synthetic_definition.json", definition)
    write_json(dest / "input_hashes.json", hashes)
    if smoke:
        details = _smoke(specifications)  # Generators/metadata only; no scaler or readout fits.
        _verify_sources(hashes)
        return finish(dest, public, dict(stage="SYNTHETIC", status="PASS", scope="generator/input smoke only",
            actual_head_fits=0, actual_ridge_fits=0, neural_head_fits=0, scientific_status="NOT_EVALUATED", inputs=details))
    cases, manifest = prepare_cases(specifications, dest / "worlds")
    prepared_hashes = {str(path): digest(path) for world in manifest for path in Path(world["folder"]).iterdir() if path.is_file()}
    write_json(dest / "prepared_input_hashes.json", prepared_hashes)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    write_json(dest / "execution_policy.json", dict(device=device, complete_family_required=True,
        neural_fits=630, terminal_steps_allowed=[1000, 2000], test_effects_select_budget=False,
        declared_total_fits=1920, timeout_requires_external_scheduler_budget_status=True))
    try:
        a2_outcomes = run_a2(manifest, dest)
        models, receipts = fit_cases(cases, dest / "heads", device=device, expected_fits=1620, legacy=False)
        if len(receipts) != 1620 or len({r["fit_id"] for r in receipts}) != 1620:
            raise ValueError("SYNTHETIC_COMPLETE_FIT_RECEIPTS")
        # Test arrays cannot enter fit_cases. It returns only after the entire
        # neural family has made its terminal, training-only budget decision.
        outcomes = score_worlds(manifest, models, receipts, dest)
        rates = aggregate_rates(a2_outcomes + outcomes)
        if len(rates) != 33:  # A2 18 + N1 4 + N2 3 + N3 6 + G0 2.
            raise ValueError("SYNTHETIC_ALL_MECHANISM_CONDITIONS_REQUIRED")
        _verify_sources(hashes)
        _verify_sources(prepared_hashes)
    except Exception as exc:
        # Keep detailed errors private. No failed world is assigned a negative
        # score, and an incomplete run never receives complete aggregate rates.
        write_json(dest / "synthetic_failure.json", dict(error_type=type(exc).__name__, error=str(exc),
            traceback=traceback.format_exc(), scientific_status="NOT_EVALUABLE"))
        raise
    pd.DataFrame(rates).to_csv(public / "synthetic_rates.csv", index=False)
    _a2_aggregate(dest, public)
    write_json(dest / "fit_receipts.json", receipts)
    failures = sum(r["numerical_status"] != "OPTIMIZATION_STABLE" for r in receipts)
    failed_worlds = len({r["world_id"] for r in outcomes if r["status"] != "EVALUATED"})
    (report / "SYNTHETIC_REPORT.md").write_text(
        "# 冻结预算的合成机制审计\n\n600个独立路线世界：A2三种机制各100，N1四种各30，N2/N3各三种机制各30。"
        "另有60个G0维度/注入夹具。A2的零、固定非零和训练拟合W共享同一次世界抽样；N3两种读出也共享世界，不能将这些条件累计成独立儿童或世界。\n\n"
        "N1/N3各60候选×600试次，N2各60候选×80袋×8试次；固定36训练/24测试候选。A2按world_index%5采用冻结Omega合格外折训练/测试人数。"
        "A2每半Delta的噪声SD由单位试次方差、共同两格q和每格每类6次配额固定为sqrt(1/6)，不将20次重抽样当独立新增试次再次缩小噪声。"
        "只模拟资格后的共同配额，不填补被排除候选；三种W条件共享同样的人数和噪声。生成参数没有根据真实EEG拟合，因此结果检验机制和数值行为，不是当前队列的经验功效估计。"
        "G0每候选8试次、64/400维各半、零/注入各30例，仅作独立维度夹具，不冒充真实划分注入。\n\n"
        "所有特征变换仅在训练候选拟合，P_nat每候选等权，P_bal每候选及其两类等权。N2 PCA和RFF仅使用训练袋内试次；TIME_DRIFT每候选两类均有支持，全局时间进入H_BAG。"
        "Logistic固定C=1，MLP32固定lambda=.001，共1620分类头（630神经头）及300个A2 ridge；没有新encoder、内折调参或温度拟合。"
        "630神经头完成初始1000步后，任一个训练数值不稳定则全部续至2000步，随后才预测测试集。测试分数全部是raw；raw校准误差会影响log-loss增益。\n\n"
        "增益按候选先汇总，再以2000次共享候选抽样形成区间，条件是固定预测，不是完整流程重拟合。N1/N3量级为.005 bits/trial，N2为.01 bits/bag；"
        "同时要求预定噪声/重复维度对照的区间下界大于0。G0用.01 bits/trial的先验减模型CE。"
        "每个世界的全部规定模型必须成功才评价该世界；所有数值失败仍进入固定30次分母，未知结果给出比例识别界与Clopper-Pearson包络，不填零。"
        "A2同时输出Delta/P/R的cosine和内积，逐项核验四项内积恒等式；零范数cosine保留未定义。"
        "A2的假阳性倾向是将重复性解释为刺激特异信息的风险，不将真实nuisance重复性叫作统计学零效应。\n\n"
        "本预算合成目录没有覆盖真实路线的全部HB/HPP、供体或历史条件对照，不能凭此宣布真实路线科学完成。"
        "2小时硬预算到期保留BUDGET_LIMITED与模型状态，不缩小试次数重来；数值未完成不能用作充分否定真实效应。\n", encoding="utf-8")
    return finish(dest, public, dict(stage="SYNTHETIC", status="NUMERICAL_INCOMPLETE" if failures else "MECHANISM_AUDIT_COMPLETE",
        scientific_status="MECHANISM_DIAGNOSTICS_ONLY", independent_route_worlds=600, G0_separate_fixtures=60,
        actual_head_fits=1620, actual_ridge_fits=300, total_fits=1920, neural_head_fits=630,
        calibration_fits=0, new_encoder_fits=0, failed_head_fits=failures, unresolved_classifier_worlds=failed_worlds,
        all_required_worlds_evaluable=failed_worlds == 0, raw_uncalibrated=True,
        family_extension_used=any(r["family_extension_used"] for r in receipts),
        planned_denominators_preserved=True, rates=rates, clinical_inputs=False,
        pending=["empirical real-cohort power is not estimated", "budgeted synthetic models do not cover every real-route control"]))
