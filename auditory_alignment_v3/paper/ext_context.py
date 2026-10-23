"""Paper line, Table 2 POST-HOC context-matched sensitivity (researcher request 2026-10-22 ~18:40, after the Table 2 numbers had
been seen): do the external decoders (mTRF, VLAAI; Transformer-CLIP pre-declared) keep their advantage over the proposed
temporal-CS system when they may use only the EEG span the proposed system uses?  Nothing here replaces a primary Table 2 cell.

Proposed-system span (aln41/frozen.py, cs endpoint): anchors a = rint(linspace(0.4, 4.15, 16) * 128) = 51, 83, ..., 531 (128 Hz,
segment-relative), three crops per anchor (aln41/timebank.layout(128)) = [a-25, a+26), [a, a+52), [a+26, a+77); their union is
the contiguous half-open range [26, 608) at 128 Hz = [0.203125, 4.75) s of each 5 s segment.  The external decoders' 64 Hz
EEG is the pairwise mean of the same cohort EEG (ext_common: 64 Hz sample j = mean of 128 Hz samples 2j, 2j + 1), so the span
is exactly [13, 304) at 64 Hz (291 samples, 4.547 s).  Cohort-level preprocessing (offline filtering, the loaders' per-person
standardisation) is shared by every system, the proposed one included, and is not a decoder input; it is unchanged.

Per decoder (definitions also in PROTOCOL.json; all other recipe elements identical to the Table 2 row):
  mtrf_ctx  (ext_context_mtrf.py, CPU): backward model, lags 0..32 samples (0..500 ms) at 64 Hz.  An envelope sample t is used
            (as a training row, for alpha selection and for the margin) only if all of EEG t..t+32 lies in [13, 304):
            t in [13, 271] (259 samples, 4.047 s).  EEG outside the span is set to NaN before the design matrix is built, and all
            sufficient statistics / predictions are asserted finite.
  vlaai_ctx (ext_context_vlaai.py, GPU): the released VLAAI (fully convolutional, any length) receives only EEG [13, 304) as its
            window (DTU: common-average reference and per-listener per-channel z-score computed over span samples only); the
            target / loss / validation r / margin envelope is the same span [13, 304) (VLAAI's native convention: EEG window and
            envelope window coincide).  Re-fitted per unit with the Table 2 recipe (not re-scored from the native models).
  clip_ctx  (pre-declared here before the native CLIP row exists; to be implemented as a new module once that row is complete):
            frozen stage-S encoder unchanged; stage-T readout re-fitted on 3 s (192-sample) windows that lie inside [13, 304):
            training starts 13 and 112, reconstruction starts 13 / 62 / 112 with the native Hann overlap-add (outer half-windows
            weight 1) over [13, 304); DTU re-reference / z-score over span samples; margin over [13, 304).
Unchanged: partition (ext_common: 2 content folds x 5 person folds), train / test people, roles, hyper-parameter grids and
selection rules, margin r(hat, attended) - r(hat, ignored), integration aln42.external_eval.integrate (5 / 10 / 20 s, tau by
double-order log loss on training-side windows), aggregation (content folds averaged per person, both required).
CLI (Slurm only): python -m auditory_alignment_v3.paper.ext_context selftest | protocol | span
"""
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import sys

import numpy as np

from .. import core
from . import ext_common as XC

RES = XC.RESULTS / 'context_matched'
OUT = XC.OUT / 'context_matched'
STORE = XC.STORE / 'context_matched'
PROTOCOL = RES / 'PROTOCOL.json'
SPAN128 = (26, 608)                      # half-open, segment-relative, 128 Hz (asserted against aln41 frozen in span_check)
SPAN64 = (SPAN128[0] // 2, SPAN128[1] // 2)
SPAN_S = (SPAN128[0] / XC.FS_IN, SPAN128[1] / XC.FS_IN)
CLIP_DECLARED = {'window': 192, 'train_starts_64hz': [13, 112], 'infer_starts_64hz': [13, 62, 112],
                 'ola': 'native Hann overlap-add, outer half-windows weight 1, normalised by summed weights, over [13, 304)'}
REQUESTED = '2026-10-22 ~18:40 by the researcher, after the Table 2 numbers had been seen'
SEEN = {'proposed_temporal_CS_20s_acc': {'dtu': 0.612, 'fau': 0.515}, 'mtrf_20s_acc': {'dtu': 0.818, 'fau': 0.636},
        'vlaai_20s_acc': {'dtu': 0.830, 'fau': 0.679}}
MAIN = {'mtrf_ctx': XC.RESULTS / 'mtrf' / 'TABLE2_MTRF.json', 'vlaai_ctx': XC.RESULTS / 'vlaai_v2' / 'TABLE2_VLAAI_V2.json',
        'clip_ctx': XC.RESULTS / 'clip' / 'TABLE2_CLIP.json'}
HERE = Path(__file__).parent
NEW_FILES = ('auditory_alignment_v3/paper/ext_context.py', 'auditory_alignment_v3/paper/ext_context_mtrf.py',
             'auditory_alignment_v3/paper/ext_context_vlaai.py', 'auditory_alignment_v3/aln35/paper_ext_ctx_vlaai_fleet.py',
             'slurm/aln35_paper_ext_ctx_vlaai.sbatch')
REUSED_FILES = ('auditory_alignment_v3/paper/ext_common.py', 'auditory_alignment_v3/paper/ext_mtrf.py', 'auditory_alignment_v3/paper/ext_vlaai.py',
                'auditory_alignment_v3/paper/ext_vlaai_v2.py', 'auditory_alignment_v3/paper/vlaai_torch.py', 'auditory_alignment_v3/paper/ext_fleet.py',
                'auditory_alignment_v3/aln42/external_eval.py', 'auditory_alignment_v3/aln41/frozen.py', 'auditory_alignment_v3/aln41/timebank.py',
                'auditory_alignment_v3/aln41/time_access.py', 'auditory_alignment_v3/aln34/content_time.py', 'auditory_alignment_v3/aln34/attention_order.py',
                'auditory_alignment_v3/run_attention.py')
read, write, sha, digest = XC.read, XC.write, XC.sha, XC.digest


def file_shas(names):
    return {n: sha(Path(core.REPO) / n) for n in names}


# ------------------------------------------------------------------------------------------------ span
def span_check():
    """Derive the proposed system's cs EEG span from aln41 (frozen.py constants + timebank.layout(128)) and assert it against the
    stored frozen B0 arrays / meta of both datasets and content folds (cs_offsets, crop_layout)."""
    from ..aln41 import frozen as FZ, timebank as TB
    offs = np.rint(np.linspace(0.4, 4.15, FZ.CS_ANCHORS) * XC.FS_IN).astype(int)      # == aln41/frozen.py cs_offs
    lay = [tuple(int(v) for v in l) for l in TB.layout(XC.FS_IN)]
    cover = sorted((int(a) + lo, int(a) + hi) for a in offs for lo, hi, _ in lay)
    contiguous = all(b[0] <= a[1] for a, b in zip(cover, cover[1:]))
    lo, hi = min(c[0] for c in cover), max(c[1] for c in cover)
    stored = {}
    for ds in XC.DATASETS:
        for cf in XC.CFS:
            A, meta = XC.frozen_arrays(ds, cf, keys=('cs_offsets',))
            stored[f'{ds}_cf{cf}'] = {'cs_offsets_equal': bool(np.array_equal(A['cs_offsets'], offs)),
                                      'crop_layout_equal': [tuple(l) for l in meta['crop_layout']] == lay, 'seg_len': meta['cs']['seg_len']}
    ok = contiguous and (lo, hi) == SPAN128 and SPAN128[0] % 2 == 0 and SPAN128[1] % 2 == 0 and \
        all(v['cs_offsets_equal'] and v['crop_layout_equal'] and v['seg_len'] == XC.SEG128 for v in stored.values())
    rec = {'anchors_128hz': offs.tolist(), 'crop_layout_128hz': [list(l) for l in lay], 'union_contiguous': contiguous,
           'span_128hz_half_open': [lo, hi], 'span_s': [lo / XC.FS_IN, hi / XC.FS_IN], 'span_64hz_half_open': list(SPAN64),
           'span_64hz_samples': SPAN64[1] - SPAN64[0], 'stored_frozen_b0': stored, 'pass': bool(ok)}
    assert ok, rec
    return rec


# ------------------------------------------------------------------------------------------------ protocol
def protocol_body():
    from . import ext_mtrf as MT
    from . import ext_vlaai as V1, ext_vlaai_v2 as V2
    nlag = MT.NLAG
    t_lo, t_hi = SPAN64[0], SPAN64[1] - nlag            # inclusive t range for mTRF
    plans = {'mtrf': XC.OUT / 'mtrf' / 'plan.json', 'vlaai_v1': V1.OUT / 'plan.json', 'vlaai_v2': V2.OUT / 'plan.json'}
    return {
        'post_hoc': True, 'requested': REQUESTED,
        'question': 'does the 20 s accuracy gap between the proposed temporal-CS system and mTRF / VLAAI come from the EEG context '
                    'each system sees?  Restrict mTRF and VLAAI to the proposed system EEG span in training and scoring.',
        'seen_before_request': SEEN,
        'span': {'source': 'aln41/frozen.py cs anchors rint(linspace(0.4, 4.15, 16) * 128) and aln41/timebank.layout(128) crops',
                 'span_128hz_half_open_segment_relative': list(SPAN128), 'span_s': list(SPAN_S),
                 'span_64hz_half_open': list(SPAN64), 'span_64hz_samples': SPAN64[1] - SPAN64[0],
                 'eeg_seconds_per_segment': (SPAN128[1] - SPAN128[0]) / XC.FS_IN,
                 'eeg_seconds_used_per_20s_decision': 4 * (SPAN128[1] - SPAN128[0]) / XC.FS_IN,
                 'eeg_extent_seconds_per_20s_decision': 15 + SPAN_S[1] - SPAN_S[0],
                 'native_eeg_seconds_per_segment': {'mtrf': 5.5, 'vlaai': 5.0},
                 'mapping': 'ext_common 64 Hz sample j = mean of 128 Hz samples 2j, 2j+1 -> [26, 608) at 128 Hz == [13, 304) at 64 Hz',
                 'not_restricted': 'cohort-level offline preprocessing and per-person standardisation (shared by every system incl. the proposed one)'},
        'analyses': {
            'mtrf_ctx': {'output': 'TABLE2_MTRF_CTX.json', 'module': 'auditory_alignment_v3/paper/ext_context_mtrf.py',
                         'reference_row': 'mtrf (ext_mtrf, plan sha below)',
                         'eeg_used_64hz': list(SPAN64), 'lags_samples': [0, nlag - 1],
                         'reconstructed_envelope_samples_64hz_inclusive': [t_lo, t_hi], 'n_envelope_samples': t_hi - t_lo + 1,
                         'rule': 'envelope sample t used iff EEG t..t+32 all inside [13, 304); EEG outside the span set to NaN before the design '
                                 'matrix, finiteness asserted',
                         'train': 'train people cs role=fit, attended envelope at t in [13, 271]',
                         'alpha': 'same grid logspace(-3, 4, 8); mean per-segment Pearson r over t in [13, 271] on train people cs role=es',
                         'refit': 'fit + es with the selected alpha', 'margin': 'r(hat, att) - r(hat, ign) over t in [13, 271]'},
            'vlaai_ctx': {'output': 'TABLE2_VLAAI_CTX.json', 'module': 'auditory_alignment_v3/paper/ext_context_vlaai.py',
                          'reference_row': 'vlaai_v2 (ext_vlaai_v2, plan sha below)',
                          'eeg_used_64hz': list(SPAN64), 'input_window_samples': SPAN64[1] - SPAN64[0],
                          'envelope_window_64hz': list(SPAN64),
                          'rule': 'model input = EEG[:, 13:304] only (fully convolutional, zero padding at the window edges as natively); '
                                  'target / loss / validation r / margin over the same window (native VLAAI convention)',
                          'dtu_input': 'common average reference, then per-listener per-channel z-score over span samples only',
                          'fau_input': 'cache EEG span, Linear(31->64) adapter (spherical-spline init) trained jointly, as Table 2',
                          'recipe': 'identical to Table 2 (seed 3401, Adam 1e-4, batch 64, <= 50 epochs, patience 5, best epoch by mean '
                                    'per-segment r on train people cs role=es, fp32 numerics); re-fitted per unit, not re-scored',
                          'margin': 'r(hat, att) - r(hat, ign) over [13, 304)', 'checks': 'finiteness, batch invariance, v2 swap check'},
            'clip_ctx': {'status': 'pre-declared, not implemented; added as a new module after the native CLIP row is complete',
                         'output': 'TABLE2_CLIP_CTX.json', 'eeg_used_64hz': list(SPAN64), **CLIP_DECLARED,
                         'rule': 'frozen stage-S encoder unchanged; stage-T readout (+ FAU adapter) re-fitted with the Table 2 recipe on windows '
                                 'inside the span; DTU re-reference / z-score over span samples; margin over [13, 304)'},
            'not_run': {'extend_proposed_to_full_5s': 'assessed only (needs new frozen GPU features); see report'},
            'excluded': {'mindmix': 'at chance in Table 2; left out by the researcher'}},
        'unchanged': {'partition': 'ext_common / ALN4.1 public units (2 content folds x 5 person folds), same train / test people and roles',
                      'integration': 'aln42.external_eval.integrate via ext_common.integrate_unit (5 / 10 / 20 s; 20 s primary)',
                      'aggregation': 'ext_common.summarize: per person content folds averaged (both required); groups dtu nh/hi, fau th/ha/ci, all'},
        'module_sha256_at_freeze': {**file_shas(NEW_FILES), **file_shas(REUSED_FILES)},
        'plans_sha256': {k: sha(p) for k, p in plans.items()},
        'input_index_sha256': {ds: sha(XC.INPUT / ds / 'index.json') for ds in XC.DATASETS},
        'main_rows_sha256': {k: (sha(p) if p.exists() else None) for k, p in MAIN.items()},
        'span_check': span_check()}


def freeze_protocol():
    body = protocol_body()
    if PROTOCOL.exists():
        old = read(PROTOCOL)
        drift = [k for k, v in body.items() if k not in ('module_sha256_at_freeze', 'main_rows_sha256') and old.get(k) != v]
        assert not drift, f'protocol drift: {drift}'
        return old
    os.umask(0o022); RES.mkdir(parents=True, exist_ok=True)
    PROTOCOL.write_text(json.dumps({**body, 'frozen_at': datetime.now().astimezone().isoformat(),
                                    'frozen_by_job': os.environ.get('SLURM_JOB_ID')}, indent=1) + '\n')
    PROTOCOL.chmod(0o444); os.umask(0o077)
    return read(PROTOCOL)


def protocol_sha():
    assert PROTOCOL.exists() and (PROTOCOL.stat().st_mode & 0o222) == 0, 'PROTOCOL.json missing or writable'
    return sha(PROTOCOL)


# ------------------------------------------------------------------------------------------------ result table
def table(system, by, module_files, extra=None):
    """by[ds] = (ext_common.summarize output, taus).  Writes RES/TABLE2_<SYSTEM>.json in the sensitivity/TABLE2_* layout
    (datasets -> <cohort> -> per_person_by_window_s[sec] -> {person: {accuracy, nll_bits, ...}}) plus the main-row reference."""
    main = read(MAIN[system]) if MAIN[system].exists() else None
    out = {'system': system, 'post_hoc': True, 'protocol_sha256': protocol_sha(), 'module_sha256': file_shas(module_files),
           'span_s': list(SPAN_S), 'span_64hz_half_open': list(SPAN64), **(extra or {}), 'datasets': {}}
    if main is not None:
        out['main_row'] = {'file': str(MAIN[system].relative_to(core.REPO)), 'sha256': sha(MAIN[system])}
    for ds, (summ, taus) in by.items():
        d = {'summary_by_window_s': {sec: v['groups'] for sec, v in summ.items()},
             'per_person_by_window_s': {sec: v['people'] for sec, v in summ.items()}, 'tau': taus}
        if main is not None:
            ref = main['datasets'][ds]; cmp_ = {}
            for sec, v in summ.items():
                mp = ref['per_person_by_window_s'][sec]; assert sorted(mp) == sorted(v['people']), f'people differ from main row {ds} {sec}'
                cmp_[sec] = {}
                for grp, g in v['groups'].items():
                    ps = [p for p, x in v['people'].items() if grp == 'all' or x['group'] == grp]
                    da = np.array([v['people'][p]['accuracy'] - mp[p]['accuracy'] for p in ps])
                    dn = np.array([v['people'][p]['nll_bits'] - mp[p]['nll_bits'] for p in ps])
                    cmp_[sec][grp] = {'n_people': len(ps), 'main_accuracy_mean': ref['summary_by_window_s'][sec][grp]['accuracy_mean'],
                                      'main_nll_bits_mean': ref['summary_by_window_s'][sec][grp]['nll_bits_mean'],
                                      'ctx_minus_main_accuracy_mean': float(da.mean()), 'ctx_minus_main_nll_bits_mean': float(dn.mean()),
                                      'n_people_accuracy_lower': int((da < 0).sum()), 'n_people_accuracy_higher': int((da > 0).sum())}
            d['versus_main_row_by_window_s'] = cmp_
        out['datasets'][ds] = d
    os.umask(0o022); RES.mkdir(parents=True, exist_ok=True)
    path = RES / f'TABLE2_{system.upper()}.json'; path.write_text(json.dumps(out, indent=1, default=float) + '\n'); os.umask(0o077)
    cells = {ds: {g: (round(v['accuracy_mean'], 4), round(v['nll_bits_mean'], 4), v['n_people'])
                  for g, v in out['datasets'][ds]['summary_by_window_s']['20'].items()} for ds in out['datasets']}
    print(system, json.dumps(cells), flush=True)
    return out


def score_units(rows, record_of, by_ds=XC.DATASETS):
    """rows: plan rows (dataset, content_fold, person_fold); record_of(row) -> unit record with dest / npz_sha256.  Integrates the
    saved margins of every unit with ext_common.integrate_unit and summarises per dataset; refuses on any missing unit."""
    by = {}
    for ds in by_ds:
        cache = XC.Cache(ds); per_unit, taus = {}, {}
        for row in rows:
            if row['dataset'] != ds:
                continue
            rec = record_of(row); assert rec['status'] == 'complete' and not rec.get('probe'), row['id']
            path = Path(rec['dest']) / 'margins.npz'; assert sha(path) == rec['npz_sha256'], path
            with np.load(path, allow_pickle=False) as z:
                Z = {k: z[k] for k in z.files}
            for k in ('cs_person', 'cs_code', 'cs_e0'):
                assert np.array_equal(Z[k], cache.arr[k]), k
            assert np.array_equal(Z['cs_role'], cache.role(row['content_fold']))
            res = XC.integrate_unit(cache, row['content_fold'], row['person_fold'], Z['margin'].astype(np.float64))
            per_unit[(row['content_fold'], row['person_fold'])] = res
            taus[f"cf{row['content_fold']}_sf{row['person_fold']}"] = {sec: v['tau'] for sec, v in res.items()}
        assert len(per_unit) == len(XC.CFS) * len(XC.SFS), (ds, len(per_unit))
        by[ds] = (XC.summarize(per_unit, cache.index['groups'], ds), taus)
    return by


# ------------------------------------------------------------------------------------------------ engineering self-test (synthetic)
def selftest():
    """Synthetic engineering checks only (no cohort data, no scores): mTRF span design, NaN guard, VLAAI forward on the span."""
    from . import ext_mtrf as MT, ext_context_mtrf as CM
    rng = np.random.default_rng(0)
    E = rng.standard_normal((3, 5, XC.BLOCK64)).astype(np.float32)
    full = MT.design(E).reshape(3, XC.SEG64, -1)
    ctx = CM.design_ctx(E).reshape(3, CM.NT, -1)
    eq = bool(np.array_equal(full[:, CM.T0:CM.T0 + CM.NT], ctx))
    Em = CM.mask_outside(E)
    nan_ok = bool(np.isfinite(CM.design_ctx(Em)).all()) and not np.isfinite(MT.design(Em)).all()
    one_more = Em.copy(); one_more[:, :, SPAN64[1] - 1] = np.nan          # last span sample must be used
    uses_last = not np.isfinite(CM.design_ctx(one_more)).all()
    one_first = Em.copy(); one_first[:, :, SPAN64[0]] = np.nan             # first span sample must be used
    uses_first = not np.isfinite(CM.design_ctx(one_first)).all()
    out = {'mtrf_design_ctx_equals_full_rows': eq, 'mtrf_nan_guard': nan_ok, 'mtrf_uses_first_span_sample': uses_first,
           'mtrf_uses_last_span_sample': uses_last, 'mtrf_t_range_inclusive': [CM.T0, CM.T0 + CM.NT - 1], 'mtrf_nt': CM.NT}
    import torch
    from . import ext_vlaai as V1
    net = V1.build_net('dtu', V1.BIOSEMI64, torch.device('cpu')).eval()
    x = torch.from_numpy(rng.standard_normal((2, 64, SPAN64[1] - SPAN64[0])).astype(np.float32))
    with torch.no_grad():
        y = net(x)
    out['vlaai_span_forward_shape'] = list(y.shape); out['vlaai_span_forward_finite'] = bool(torch.isfinite(y).all())
    out['pass'] = bool(eq and nan_ok and uses_last and uses_first and list(y.shape) == [2, SPAN64[1] - SPAN64[0]] and out['vlaai_span_forward_finite'])
    print(json.dumps(out, indent=1), flush=True)
    assert out['pass'], out
    return out


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    cmd = sys.argv[1]
    if cmd == 'selftest':
        selftest()
    elif cmd == 'span':
        print(json.dumps(span_check(), indent=1))
    elif cmd == 'protocol':
        selftest(); p = freeze_protocol(); print(json.dumps({k: p[k] for k in ('post_hoc', 'span', 'frozen_at')}, indent=1)); print(sha(PROTOCOL))


if __name__ == '__main__':
    main()
