"""E34_PUBLIC_PRIOR C5: the public target-cohort caches for FAU, DTU and Federici under contract aln33_env64_125ms_v1 (module M2b).

Design: private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.1 (EEG at 64 Hz, normalisation, masks), §2.2 (segments),
§2.3 (the 2-8 Hz envelope), §2.5 (presentations), §2.13 (access modes A / B / C, the mode-C unit rule and scale), §3.1 / §3.3
(donor roles, cells: the ALN3 participant sets and folds), §3.5 (coverage), §6.2 C5 and §6.6 M2b; contract constants and filters
from auditory_alignment_v3.prior33.contract.

CLI (a CPU Slurm job through slurm/aln33_prior_cpu.sbatch; the lead schedules the full builds; always run with -m):
  python -m auditory_alignment_v3.prior33.build_public --cohort fau      --mode A,B,C --out <cache root>
  python -m auditory_alignment_v3.prior33.build_public --cohort dtu      --mode A,C   --out <cache root>
  python -m auditory_alignment_v3.prior33.build_public --cohort federici --mode A,C   --out <cache root>
  python -m auditory_alignment_v3.prior33.build_public --cohort all      --mode all   --out <cache root>   (the three in sequence)
  --mode takes A, B or C, a comma list, or 'all'. <cache root> is CACHE_ROOT (§6.2, the default); any other --out needs
  --allow-other-out, and a partial build (--participants id,id: a dry run) is refused under CACHE_ROOT. One job per cohort and
  mode set is the intended use; separate --mode jobs for one cohort merge into the same pieces.json (one build per cohort directory
  at a time: flock on <cohort>/.build.lock). Every output goes through a tmp file and os.replace; each (cache, participant) has a
  done marker under <cohort>/_c5_done/, so a resubmitted job continues. Outputs are byte-deterministic (sorted JSON keys, no
  timestamps; progress goes to stdout). Single-threaded; peak RSS about 1 GB (the FAU stereo-file check reads one 48 kHz stimulus
  at a time), so -c 2 --mem=8G is enough.

Inputs (read-only, through the existing loaders' constants and helpers, which are not edited: auditory_alignment.data.fau_panel,
data._folds, data.STAGEB / DTU_PRE / DTU_KCS / FED_PRE / PUB / REPO, prep_targets.FAU_ENV, federici_content.OUT / env_key; the
participant sets, trial filters, identities and folds of data.load_fau / load_dtu / load_federici are reproduced exactly):
  fau       stage-B <grp>/<id>.h5 trial_XX/eeg_1_20_ica (mode A), eeg_1_20_noica (modes B, C), 31 ch at 128 Hz, average reference
            incl. the reconstructed Cz; attribute bads_interpolated (CI) -> masked. All 81 participants (14 always-train TH with
            fold -1 and dev true, then the fau_panel ids), all 20 trials (8 single-, 12 competing-talker). Envelopes:
            stimulus_env_128.h5 <code>/{attended,distractor}_env/raw (nan_to_num as prep_targets.py, NaN count recorded). The
            attended side of a code: its presented stereo file (SIDE_RULE). The Zenodo records describe two loudspeakers 60 deg
            apart, the two streams on the left / right channel of one stimulus file per code, and single-talker trials from
            alternating sides; no trial attribute holds a side (stage B and the published HDF5 carry only 'stimulus').
  dtu       c3_preproc_v1/dtu_snhl/<sub>.h5 trial_NNN/eeg_1_20[:64] (uV, Biosemi CMS) -> CAR over the 64 EEG channels (ours). The
            44 subjects of private/auditory_c3/public/dtu_v2/*.json (other files, e.g. sub-024_run-2.h5, are listed with their
            inventory trials, never opened), single- and two-talker trials with load_dtu's filter (target sha in inventory.json,
            content_groups.json and dtu_cf0/1.h5; two-talker: masker sha too); excluded trials are listed with the reason.
            Envelopes: kcs_targets_v1/audio_local.h5 <sha>/env (128 Hz; HI trials point to the 'woa' originals, as in ALN3).
  federici  c3_preproc_v1/federici_ci_children/{HC,CI,HC-v,Artifact}/<id>.h5 eeg [blocks, 32, 5000] and env [blocks, 5000] at
            100 Hz (authors' 2-8 Hz + ICA, unchanged). HC-v identities stay separate (uid federici:HC-v:N) and share only the fold
            key N with HC N (Option A of §3.3); the phantom ('Artifact', 9 sessions) is test_only, never a donor (slab target_only).
            Items: federici_content.env_key of the z-scored block envelope; content groups from content_groups.json.

Processing (per participant; the pieces are every loaded trial / block, single- and competing-talker):
  EEG       contract.resample64 (h_aa: 128 -> 64 Hz 61 taps, 100 -> 64 Hz 727 taps), no further band filter (the design's
            per-cohort band is the existing preprocessing: FAU 1-20 Hz FIR + ICA, DTU 1-20 Hz FIR, Federici the authors' 2-8 Hz).
  mode A    z-score per participant x channel over all of that participant's pieces at 64 Hz (data._stdz semantics: mean and
            population SD over the guarded spans [g0, T - g1) of contract.GUARDS; masked (piece, channel) cells excluded; SD 0 or
            undefined -> 1), masked channels then 0 -> float16 time-major eeg_f16_tmajor.npy [N, C].
  mode B    FAU only: the same on eeg_1_20_noica -> eeg_noica_z_f16_tmajor.npy.
  mode C    the pre-z 64 Hz signal x factor_to_uV, masked cells 0, no z-score -> eeg_raw_f16_tmajor.npy (FAU: noica; DTU: after
            CAR; Federici: the authors' blocks, mode C_partial). Written only when the cohort's physical unit is established
            (UNIT_RULE below): its partial file is created only once the first participant has established the unit, and an
            unsupported mode's own unfinalised partial file is removed (nothing else is ever removed); pieces.json then records
            mode_c.supported = false.
  envelope  per stream: nan_to_num -> resample64 -> contract.band(env_sos, padlen min(128, T - 1)) over the whole stream ->
            contract.rms_norm -> float32, concatenated in stream order into env_f32.npy [M]; streams.json records origin, the
            original band, the RMS, the NaN count and the filter shas. DTU maskers: the masker's own envelope through that chain,
            then placed on the trial grid at its exact offset (FRAC_RULE: Kaiser-windowed sinc fractional delay), one stream per
            (masker sha, offset), so every ignored stream starts at its piece's sample 0 (ignored_lead 0, as the FAU distractor;
            rounding the offset to 64 Hz samples would shift the ignored stream by up to 7.8 ms, 3.9 ms on average).
  segments  piece.segment_starts = contract.segment_starts(T_env, T_eeg, cohort, onset_s): T_env = the attended stream's length,
            onset_s the distractor (FAU) or masker (DTU) onset of competing-talker pieces (+ 1.7 s rule of §2.2; the fixture's
            semantics). cs pieces also carry segment_starts_guard_only, and every piece segment_starts_target_stage: the starts of
            §2.2 for the target-stage evaluation ("DTU target-stage evaluation, FAU in CSX only"), i.e. the guard-only starts for
            FAU competing-talker pieces and segment_starts otherwise. The ignored stream must cover every start (checked at plan
            time; a violation raises before any EEG is read).
  rows      pieces in role slabs ('fit' = donor-usable pieces, then 'target_only'), table order inside a slab: FAU all pieces fit
            (single-talker codes: core donors; competing-talker codes: CSX only, the pool split is C6's); DTU NH single-talker fit,
            HI single-talker and every two-talker trial target_only; Federici humans fit, the phantom target_only.

Outputs in <root>/<cohort>/ (the schema of tests/auditory_alignment_v3/prior33/fixtures.py and of build_sparrkulee.py runs.json):
  eeg_f16_tmajor.npy, eeg_noica_z_f16_tmajor.npy (FAU), eeg_raw_f16_tmajor.npy, each with <file>.done.json {sha256, unit, ...}
  env_f32.npy, streams.json {schema, cohort, id_space, id_note, streams: [stream, name, key, kind, offset, length, family,
            family_name, family_offset, family_basis, rms, nan_count, origin, original_band, source, fs_source, T_source, roles,
            source_sha256 (sha256 of the float64 C-order bytes of the source envelope array as read, before nan_to_num),
            filter_sha256 {aa_fir_<fs_source>, env_sos} (the contract chain, as fixtures.py), filter_padlen, (DTU maskers)
            placement {masker_sha, offset_s, delay_64, rule, base_length}]}
  pieces.json {schema, contract, cohort, id_space, id_note, builder_sha256, layout_sha256, partial, participants, pieces,
            presentations, families, partner_exclusions, excluded_trials, unread_files, checks, cohort_info, caches, unit,
            unit_evidence, mode_c}
    participants: participant, uid, identity, group, fold, dev, test_only, donor, masked, n_pieces, source_file, (dtu) age,
            (fau) cs_side, aux_pattern, (federici) phantom; after a mode build mu {key: [C]}, sd_prez {key: [C]}, sd_prez_unit,
            sd_prez_uV {key: [C]} (x factor_to_uV; None when the unit is not established), n_stat_samples, median_prez_sd and
            source_sha256 (sha256 of the participant's source file). sd_prez is the pre-z SD in the SOURCE arrays' physical unit
            (sd_prez_unit; FAU volts), as build_sparrkulee.py (design §2.1 "in the cache's physical unit"); the fixture's
            synthetic tables are in uV, where both agree. Consumers needing uV read sd_prez_uV or call mode_c_scales(), which
            prefers sd_prez_uV and checks it against sd_prez x units. Keys: the z-mode of the signal (FAU A = ica, B = noica,
            also the mode-C signal; DTU / Federici A) and '<key>_2_8' (FAU / DTU A_2_8: the same signal through the contract
            2-8 Hz band-pass, contract.band(env_sos) over each piece, the band of the Federici target's mode-C input);
            cohort_info.stats_band gives each key's band.
    pieces: the fixture fields piece_id, participant, uid, group, fold, dev, test_only, trial, kind, stimulus, ignored_stimulus,
            content_group, presentation, family, family_offset, stream, ignored_stream, ignored_lead, attended_side, onset_s,
            role, slab, row_offset, T_eeg, T_env, segment_starts, masked; plus identity, presentation_key, family_name,
            family_basis, condition, T_native, source, segment_starts_target_stage, own_repeat_pieces (the participant's other
            pieces of the same presentation: never a partner or positive of each other) and per-cohort fields (fau: part,
            story, stageb, aux_evidence, aux_attended_on, aux_distractor_on, aux_status; dtu: content_half, content_early_stop,
            masker_offset_s, ignored_placement, attend_male_female, stim_file; federici: content_role, block, item_n_listeners,
            session_condition).
    presentations / families: this cohort's registries (id_space cohort_local_provisional, ID_NOTE): C6 remaps them to the
            manifest's global ids by presentation_key / family_name and fills the C3 offsets before any key is packed.
    checks: own_repeats (every participant x presentation with >= 2 pieces), ignored_stream_coverage and per-cohort diagnostics
            (fau: codes, stereo_file_name_mismatches, aux; dtu: inventory_reconciliation; federici: item conditions).
UNIT_RULE (§2.13 mode C): the median over the human (non-test_only) participants x unmasked channels of the pre-z SD of the mode-C
signal (source unit) decides: [1e-7, 1e-3] -> volts (x 1e6 to uV), [1e-1, 1e3] -> microvolts; a source whose SDs cluster at 1
(>= 90 % within 0.05) is source-normalised and gets no unit; documented metadata, where it exists (FAU: the C3 chanmap log of the
published HDF5 against the BrainVision raw files read by MNE in volts; DTU: the stage-A files' code_sha256 equals
auditory_c3/preproc.py, whose dtu() writes MNE volts x 1e6; Federici: none), must agree with the magnitude rule. Every human
participant's own median must fall in the cohort's band. test_only sessions (the Federici phantom: not human, a near-silent
recording) are left out of the evidence, share the cohort unit (same system and export) and are reported in unit_evidence.test_only.
mode_c_scales() gives C6 the donor-derived mode-C scale s_T of §2.13 from the cohort tables, from the same-band statistic by
default; with_band_sd() derives a 2-8 Hz statistic from a z-cache (SparrKULee, whose C4 table records only 1-20 Hz).

Data-use guards (enforced in code; tests in tests/auditory_alignment_v3/prior33/test_build_public.py): only fau / dtu / federici
are built; every file is opened through check_path(), which raises RestrictedAccess for any path that names a restricted
SparrKULee participant (sub-019/020/021/022/026 under a sparrkulee directory, symlinks resolved); nothing is unpickled (h5py, json,
csv, scipy.io.wavfile, RIFF headers by struct; np.load reads only this contract's .npy caches, with allow_pickle=False, and
with_band_sd() opens a cache path through check_path() too); no dataset code runs.

Interpretations (the design names the step but not the detail; each is a deviation of the M2b summary):
- One module build_public.py with --cohort / --mode (the task), not cache_build.py public of §6.6 (M2a owns cache_build-like
  SparrKULee code in build_sparrkulee.py).
- presentation / family ids are cohort-local and provisional (index in the sorted keys; id_space 'cohort_local_provisional', as
  in build_sparrkulee.py), with presentation_key / family_name strings beside them; C6 owns the global ids, the duplicate-scan
  family merges and the Federici natural / vocoded offsets (family_offset None, family clock 'pending_C3', until C3 measures).
- Presentation keys: FAU single talker 'fau:<code>'; competing talker 'fau:<code>|side=<side>' with the attended side of the
  presented stereo file (§2.5 says "from the trial attributes"; no such attribute exists). SIDE_RULE matches the file by content:
  S220.wav holds code 229's waveforms and S229.wav code 220's (r = 1.0), so the name S<code>.wav alone would leave 220 / 229 without
  a side. The per-trial aux evidence of the C3 receipt (fau_tud_schema_private_001.json) is a diagnostic only (AUX_RULE,
  checks.aux): every listener whose aux readings contradict the code-level sides is either 'swapped' (all determined trials
  mirrored: the session's two recording channels exchanged) or 'single_channel' (one silent aux channel); presentations never
  use it. DTU 'dtu:<sha>|side=<side>' (NH single talker; the side is constant per sha in the data), two-talker
  'dtu:<target>+<masker>@<masker offset s>|side=<side>', HI '...|eq=<sub>/<trial>' (individually equalised: unique).
  Federici 'federici:<item>' (§2.5: the item envelope hash) for humans, 'federici:<item>|phantom' for the phantom (never shared
  with a human). condition is an item property, as scan_audio.py and the fixture: vocoded when every human block of the item is
  an HC-v session, else natural; the session's own label is session_condition.
- FAU competing-talker onset: the first nonzero sample of the published 48 kHz distractor_wav (the HDF5 named by
  stimulus_env_128.h5's 'source' attribute); ignored_lead 0 (the distractor envelope is on the trial grid). DTU: onset_s =
  masker_onset_rel_s (as load_dtu; equal to the inventory offset_s), masker placed by FRAC_RULE at offset_s, ignored_lead 0.
- FAU guards 157 / 157 as designed; stage-B valid_start / valid_stop and the realignment extra guard are recorded per piece.
- sd_prez is in the source arrays' unit (design §2.1 "in the cache's physical unit"; build_sparrkulee.py does the same);
  sd_prez_uV holds the uV values when the unit is established.
- mode_c_scales(band='target'): "pre-z SD of the same-band 64 Hz signal" (§2.13) is read as the band of the target's mode-C input,
  so Federici's 2-8 Hz SDs never enter the FAU / DTU (1-20 Hz) scales and the Federici target takes 2-8 Hz statistics.
- Partial builds (--participants) contain only the selected participants' pieces (folds are still computed over everyone; Federici
  item conditions and the DTU reconciliation over the selected participants).
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import csv
import fcntl
import glob
import hashlib
import json
import os
import re
import sys
import urllib.parse
from fractions import Fraction

import numpy as np

from auditory_alignment_v3.prior33 import contract as C

COHORTS = ("fau", "dtu", "federici")
CACHE_ROOT = "/projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1"
SCHEMA_PIECES, SCHEMA_STREAMS, SCHEMA_DONE = "prior33_public_pieces_v1", "prior33_public_streams_v1", "prior33_public_cache_v1"
ID_SPACE = "cohort_local_provisional"
TABLE, ENV, STREAMS, DONE_DIR, LOCK = "pieces.json", "env_f32.npy", "streams.json", "_c5_done", ".build.lock"
MODES = {"fau": ("A", "B", "C"), "dtu": ("A", "C"), "federici": ("A", "C")}
CACHE_MODE = {"fau": {"A": "A", "B": "B", "C": "C"}, "dtu": {"A": "A", "C": "C"}, "federici": {"A": "A", "C": "C_partial"}}
SIGNAL = {"fau": {"A": "ica", "B": "noica", "C": "noica"}, "dtu": {"A": "car", "C": "car"}, "federici": {"A": "authors", "C": "authors"}}
STAT_KEY = {"fau": {"ica": "A", "noica": "B"}, "dtu": {"car": "A"}, "federici": {"authors": "A"}}
Z_MODES = ("A", "B")
SLABS = ("fit", "target_only")
SPARRKULEE_RESTRICTED = ("019", "020", "021", "022", "026")
FAU_WAV_FS = 48000                          # the published stimulus waveforms (hdf5_dataset_info.txt) and S<code>.wav
SIDE_R, SIDE_R_OTHER, AUX_R = 0.9, 0.5, 0.3
DTU_UV_LINE = "raw.get_data(picks=eeg_names + eog_names) * 1e6"
UNIT_BANDS = (("V", 1e-7, 1e-3, 1e6), ("uV", 1e-1, 1e3, 1.0))
UNIT_FACTOR = {name: f for name, _, _, f in UNIT_BANDS}
NORM_TOL, NORM_FRAC = 0.05, 0.9
UNIT_RULE = ("median over participants x unmasked channels of the pre-z SD (source unit) of the mode-C signal: in [1e-7, 1e-3] -> "
             "volts (x 1e6 to uV), in [1e-1, 1e3] -> microvolts, otherwise none; >= 90 % of the SDs within 0.05 of 1 -> "
             "source-normalised, none; documented metadata, where it exists, must agree; every participant's own median must lie "
             "in the cohort's band; test_only sessions (the Federici phantom: not human) are left out of the evidence and of the "
             "per-participant check, share the cohort unit and are reported separately; no unit -> mode C unsupported (no cache, "
             "no mode-C row)")
SIDE_RULE = (f"Pearson r of each channel of the code's stereo file with the published attended_wav (and distractor_wav): the "
             f"attended side is the channel with r >= {SIDE_R} while the other has r < {SIDE_R_OTHER} (competing talker: the other "
             f"channel must carry the distractor the same way); channel 0 = left, 1 = right (WAV order). The stereo file is "
             f"S<code>.wav or, when that file fails the rule, the single other S<ddd>.wav with the published waveform's frame count "
             f"that passes it (content match; the stimulus folder swaps some names); otherwise None")
AUX_RULE = (f"C3 receipt _alignment_rows, per trial: the aux channel whose r with the attended (distractor) envelope is >= {AUX_R} "
            f"while the other's is < {AUX_R}; status undetermined (no attended channel, or a code without a side), single_channel "
            f"(both streams of a competing-talker trial on one aux channel), else consistent / inconsistent with the majority "
            f"aux -> side mapping (votes of the listeners without a single-channel pattern). Per listener: single_channel (every "
            f"competing-talker trial with both channels identified has both streams on one aux channel), consistent (no "
            f"inconsistent trial), swapped (no consistent trial), unexplained (both). Diagnostic only, never used for presentations")
AUX_NOTE = ("the aux channels are StimTrak recordings of the presented audio taken from an audio splitter (Zenodo records 17927767 / "
            "17952231 / 17952844), so which aux channel records which loudspeaker channel depends on each session's cabling: "
            "'swapped' = the two recording channels exchanged for the session, 'single_channel' = one aux channel silent (both "
            "streams on the other), neither identifies a side. The presented side belongs to the code's stereo file, the same for "
            "every listener, and presentations use it")
STATS_BAND = {"sparrkulee": {"A": (1.0, 20.0)},                       # band of each pre-z statistic (§2.1 per-cohort band table)
              "fau": {"A": (1.0, 20.0), "B": (1.0, 20.0), "A_2_8": (2.0, 8.0)},
              "dtu": {"A": (1.0, 20.0), "A_2_8": (2.0, 8.0)},
              "federici": {"A": (2.0, 8.0)}}
TARGET_BAND = {"fau": (1.0, 20.0), "dtu": (1.0, 20.0), "federici": (2.0, 8.0)}   # band of each target's mode-C input
BAND_STAT = {"fau": ("ica",), "dtu": ("car",), "federici": ()}       # signals whose 2-8 Hz pre-z SD is recorded too ('<key>_2_8')
BAND_SUFFIX, BAND_2_8 = "_2_8", (2.0, 8.0)
FRAC_HALF, FRAC_BETA = 32, 8.0
FRAC_RULE = (f"y[n] = m(n - d) at 64 Hz: m = the masker's own contract envelope (h_aa, 2-8 Hz over the whole masker stream, RMS 1), "
             f"d = masker offset_s x 64 samples, band-limited interpolation by a Kaiser-windowed sinc (half-width {FRAC_HALF} "
             f"samples, beta {FRAC_BETA}, unit DC gain; an integer d is an exact shift); stream length ceil(d) + len(m); "
             f"ignored_lead 0")
ID_NOTE = ("presentation / family / stream ids index this cohort's own registries (id_space cohort_local_provisional); C6 assigns the "
           "global ids by presentation_key / family_name / stream key and supplies the C3 family offsets (family_offset None, clock "
           "pending_C3) before any key is packed from these fields")
FED_COND_RULE = ("item condition: 'vocoded' when every human (non-phantom) block of the item is an HC-v session, else 'natural' "
                 "(as scan_audio.py); the phantom's blocks are their own presentation, condition 'phantom'; session_condition is "
                 "the session's label (HC / CI natural, HC-v vocoded, Artifact phantom)")
REFERENCE = {"fau": "average over 30 EEG + reconstructed Cz (stage B, unchanged)",
             "dtu": "CAR over the 64 EEG channels (applied by C5; the stage-A cache is Biosemi CMS)",
             "federici": "average (32; authors, unchanged)"}
BAND = {"fau": {"A": "1-20 Hz FIR + ICA (stage B eeg_1_20_ica, unchanged)", "B": "1-20 Hz FIR, no ICA (stage B eeg_1_20_noica)",
                "C": "1-20 Hz FIR, no ICA (stage B eeg_1_20_noica)"},
        "dtu": {"A": "1-20 Hz FIR (stage A eeg_1_20)", "C": "1-20 Hz FIR (stage A eeg_1_20)"},
        "federici": {"A": "authors' 2-8 Hz + ICA (unchanged)", "C_partial": "authors' 2-8 Hz + ICA (unchanged)"}}
ORIGIN = {"fau": ("authors' 1 kHz envelope (method undocumented), raw-resampled to 128 Hz by c3_preproc_v1 (stimulus_env_128.h5 "
                  "<code>/<stream>_env/raw), nan_to_num as prep_targets.py", "about 0.3-9 Hz with a steep low-pass (authors)"),
          "dtu": ("ours: abs(Hilbert) of the original unequalised 16 kHz audio, resample_poly to 128 Hz (prep_targets.run_dtu_audio, "
                  "kcs_targets_v1/audio_local.h5 <sha>/env)", "broadband"),
          "federici": ("authors' cache AudioEnvSp (not normalised), 100 Hz (c3_preproc_v1 block env)",
                       "low-pass only (-3 dB about 6.9 Hz), not high-passed; the 2 Hz edge comes from the contract filter")}
PRES_FIELDS = ("stimulus", "family_name", "family_offset", "family_basis", "kind", "condition", "attended_side", "stream",
               "ignored_stream", "ignored_lead", "onset_s")
_STEREO_NAME = re.compile(r"S\d{3}\.wav")


class RestrictedAccess(PermissionError):
    """A path names a restricted SparrKULee participant (design §3.2: their arrays are never opened by any job)."""


_SK_RESTRICTED = re.compile(r"sub-(%s)(?!\d)" % "|".join(SPARRKULEE_RESTRICTED))


F16_CLIP_UV = 65000.0  # raw-uV mode-C clip (float16 max 65504); clipped counts are recorded per participant marker

def check_path(path):
    """Return the path unchanged, or raise RestrictedAccess when it (or its resolved target) lies under a SparrKULee directory and
    names sub-019 / 020 / 021 / 022 / 026. Other cohorts' identically numbered ids (DTU sub-021) are not SparrKULee and pass."""
    raw = os.fspath(path)
    for p in (raw, os.path.realpath(raw)):
        low = p.casefold()
        if "sparrkulee" in low and _SK_RESTRICTED.search(low):
            raise RestrictedAccess(f"refusing to open {raw!r}: restricted SparrKULee participant (PUBLIC_PRIOR_DESIGN.md §3.2)")
    return raw


def _h5(path):
    import h5py
    return h5py.File(check_path(path), "r")


def _read_json(path):
    with open(check_path(path)) as f:
        return json.load(f)


def _read_text(path):
    with open(check_path(path), errors="replace") as f:
        return f.read()


def _read_tsv(path):
    with open(check_path(path), newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _file_sha(path, chunk=1 << 24):
    h = hashlib.sha256()
    with open(check_path(path), "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _code_sha():
    """sha256 of this builder and of the contract it applies (recorded and part of the layout hash)."""
    h = hashlib.sha256()
    for f in (os.path.abspath(__file__), os.path.abspath(C.__file__)):
        with open(f, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return float(o) if np.isfinite(o) else None
    return o


def _dumps(obj):
    return json.dumps(_clean(obj), sort_keys=True, allow_nan=False)


def _sha_obj(obj):
    return hashlib.sha256(_dumps(obj).encode()).hexdigest()


def _write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(_dumps(obj))
    os.replace(tmp, path)


def _save_npy(path, a):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        np.save(f, a, allow_pickle=False)
    os.replace(tmp, path)


def _log(*a):
    print(*a, flush=True)


def _s(v):
    if isinstance(v, np.ndarray) and v.shape == ():
        v = v.item()
    if isinstance(v, (bytes, np.bytes_)):
        return bytes(v).decode()
    return str(v)


def _strs(v):
    if v is None:
        return []
    a = np.atleast_1d(np.asarray(v, dtype=object))
    return [_s(x) for x in a.tolist()] if a.size else []


def _num(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if np.isfinite(v) else None


def n64(n_native, fs):
    """Length of contract.resample64 output for n_native samples at fs (resample_poly: ceil(n up / down))."""
    r = Fraction(C.FS, int(fs))
    return -(-int(n_native) * r.numerator // r.denominator)


def _layout_check(names, cohort, path):
    got = tuple(C.canonical(n) for n in names)
    if got != tuple(C.MONTAGES[cohort]):
        raise ValueError(f"{path}: channel layout {got} differs from contract.MONTAGES[{cohort!r}]")


def _ordered(names, cohort):
    lay = C.MONTAGES[cohort]
    out = sorted({C.canonical(n) for n in names}, key=lay.index)   # a name outside the layout raises (ValueError)
    return out


def _corr(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    a = a - a.mean()
    b = b - b.mean()
    d = float(np.sqrt(np.dot(a, a) * np.dot(b, b)))
    return float(np.dot(a, b) / d) if d > 0 else 0.0


def parse_modes(cohort, spec):
    """'A', 'A,B,C', 'all' or a sequence -> the cohort's requested modes in canonical order; an unsupported mode raises."""
    if cohort not in COHORTS:
        raise ValueError(f"cohort {cohort!r}: build_public builds {COHORTS} only")
    if isinstance(spec, str):
        want = list(MODES[cohort]) if spec.strip().lower() == "all" else [m.strip().upper() for m in spec.split(",") if m.strip()]
    else:
        want = [str(m).upper() for m in spec]
    bad = [m for m in want if m not in MODES[cohort]]
    if bad or not want:
        raise ValueError(f"cohort {cohort}: modes {bad or want} not available (supported: {MODES[cohort]})")
    return tuple(m for m in MODES[cohort] if m in want)


# ---------------------------------------------------------------------------------------------------------- signal helpers
def envelope64(raw, fs):
    """One stream's contract envelope: nan_to_num -> resample64 (h_aa) -> 2-8 Hz band (env_sos, padlen min(128, T - 1)) over the
    whole stream -> RMS normalisation. Returns (float32 [T64], RMS of the band-limited stream, NaN / Inf count of the input)."""
    x = np.asarray(raw, dtype=np.float64).reshape(-1)
    bad = int(np.count_nonzero(~np.isfinite(x)))
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    en, rms = C.rms_norm(C.band(C.resample64(x, fs), C.env_sos()[0]), return_rms=True)
    return en.astype(np.float32), float(rms), bad


def frac_delay(x, d, n_out):
    """y[n] = x(n - d) for n in [0, n_out) (FRAC_RULE): band-limited interpolation of the 64 Hz sequence x at the delay d >= 0
    samples by a Kaiser-windowed sinc (half-width FRAC_HALF, beta FRAC_BETA, normalised to unit DC gain); an integer d is an exact
    shift. y is 0 where n - d lies more than FRAC_HALF samples outside x. float64."""
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    d = float(d)
    if not np.isfinite(d) or d < 0:
        raise ValueError(f"frac_delay: delay {d!r} must be finite and >= 0")
    D = int(np.floor(d))
    phi = d - D
    y = np.zeros(int(n_out), dtype=np.float64)
    if phi == 0.0:                                                   # exact integer shift
        seg = x[:max(0, int(n_out) - D)]
        y[D:D + len(seg)] = seg
        return y
    t = np.arange(-FRAC_HALF, FRAC_HALF + 1, dtype=np.float64) - phi  # g[q] = sinc(q - phi) w(q - phi), q = -H .. H
    w = np.i0(FRAC_BETA * np.sqrt(np.clip(1.0 - (t / (FRAC_HALF + 1)) ** 2, 0.0, None))) / np.i0(FRAC_BETA)
    g = np.sinc(t) * w
    g /= g.sum()
    z = np.convolve(x, g)                                            # z[i] = x(i - H - phi), i = 0 .. len(x) + 2H - 1
    idx = np.arange(int(n_out)) - D + FRAC_HALF                      # y[n] = x(n - D - phi) = z[n - D + H]
    ok = (idx >= 0) & (idx < len(z))
    y[ok] = z[idx[ok]]
    return y


def zstats(arrs, masked_idx, guard):
    """data._stdz statistics of one participant's 64 Hz pieces [C, T]: per channel mean and population SD over the guarded spans
    [g0, T - g1) of every piece; masked channels excluded (mu 0, SD NaN, 0 samples). -> (mu, sd, n_samples)."""
    g0, g1 = guard
    V = np.concatenate([a[:, g0:max(g0, a.shape[1] - g1)] for a in arrs], axis=1)
    if V.shape[1] == 0:
        raise ValueError("zstats: no sample outside the guards")
    mu, sd = V.mean(axis=1), V.std(axis=1)
    n = np.full(mu.shape, V.shape[1], dtype=np.int64)
    idx = list(masked_idx)
    mu[idx], sd[idx], n[idx] = 0.0, np.nan, 0
    return mu, sd, n


def zscore(a, mu, sd, masked_idx):
    s = np.where(np.isfinite(sd) & (sd > 0), sd, 1.0)
    z = (a - mu[:, None]) / s[:, None]
    z[list(masked_idx)] = 0.0
    return z


def unit_from_magnitude(sd_values):
    """UNIT_RULE magnitude part -> (unit name 'V' / 'uV' / None, detail)."""
    v = np.asarray([x for x in sd_values if x is not None], dtype=np.float64)
    v = v[np.isfinite(v) & (v > 0)]
    if not len(v):
        return None, {"median": None, "n": 0, "reason": "no finite positive pre-z SD"}
    med, near1 = float(np.median(v)), float(np.mean(np.abs(v - 1.0) <= NORM_TOL))
    det = {"median": med, "n": int(len(v)), "frac_within_tol_of_1": near1, "tol": NORM_TOL}
    if near1 >= NORM_FRAC:
        return None, {**det, "reason": "source-normalised (the SDs cluster at 1): the physical unit is not recoverable"}
    for name, lo, hi, _ in UNIT_BANDS:
        if lo <= med <= hi:
            return name, {**det, "band": [lo, hi]}
    return None, {**det, "reason": f"median SD {med:.4g} lies outside every band"}


def decide_unit(documented, magnitude):
    """documented (name | None, basis) and magnitude (name | None, detail) -> the unit record of UNIT_RULE."""
    dn, dbasis = documented
    mn, mdet = magnitude
    rec = {"rule": UNIT_RULE, "documented": {"unit": dn, "basis": dbasis}, "magnitude": {"unit": mn, **mdet}}
    if dn is not None and mn != dn:
        return {**rec, "supported": False, "name": None, "source_unit": None, "factor_to_uV": None,
                "reason": f"documented unit {dn} but the magnitude rule gives {mn}"}
    name = dn or mn
    if name is None:
        return {**rec, "supported": False, "name": None, "source_unit": None, "factor_to_uV": None,
                "reason": "no documented unit and the magnitude rule gives none"}
    return {**rec, "supported": True, "name": "uV", "source_unit": name, "factor_to_uV": UNIT_FACTOR[name],
            "basis": "documented metadata, confirmed by the magnitude rule" if dn else "magnitude rule (no documented metadata)"}


def _stats_band(cohort, table):
    """{stats key: (lo, hi) Hz} of a cohort table: its cohort_info.stats_band when recorded, else STATS_BAND[cohort]."""
    sb = (table.get("cohort_info") or {}).get("stats_band") or STATS_BAND.get(cohort, {})
    return {k: (float(b[0]), float(b[1])) for k, b in sb.items()}


def _sd_uV(cohort, p, key, factor):
    """One participant's pre-z SD [C] in uV for stats `key`: sd_prez_uV[key] where the table holds sd_prez_uV (the C4 / C5
    tables), checked against sd_prez[key] x factor (a mismatch raises: the caller's factor is not the table's unit); else
    sd_prez[key] x factor (the fixture's tables, which are in uV)."""
    sd = (p.get("sd_prez") or {}).get(key)
    if sd is None:
        raise ValueError(f"{cohort}:{p['participant']}: no pre-z SD (stats {key!r})")
    conv = [None if v is None or not np.isfinite(v) else float(v) * factor for v in sd]
    if "sd_prez_uV" not in p:
        return conv
    uv = (p.get("sd_prez_uV") or {}).get(key)
    if uv is None:
        raise ValueError(f"{cohort}:{p['participant']}: the table holds no uV pre-z SD for {key!r} (its unit is not established)")
    for a, b in zip(conv, uv):
        b = None if b is None or not np.isfinite(b) else float(b)
        if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-9 * max(abs(a), abs(b), 1e-300)):
            raise ValueError(f"{cohort}:{p['participant']}: sd_prez[{key!r}] x {factor} = {a} differs from sd_prez_uV {b}: pass the "
                             f"table's cohort_info.unit.factor_to_uV (sd_prez is in the source unit)")
    return [None if v is None or not np.isfinite(v) else float(v) for v in uv]


def mode_c_scales(target, tables, units, donors=None, band="target", missing_band="unsupported"):
    """Design §2.13 mode-C scale s_T for one target: per target channel n, the median over the leave-T-out donor-fit participants
    having n (unmasked) of their pre-z SD in uV of the same-band 64 Hz signal; names no donor has: the median over all donor
    channels. tables {cohort: {'layout': [names], 'participants': [...], optional 'cohort_info'}} (participants with donor true and
    role 'fit', the default when absent); units {cohort: factor_to_uV or None}: a donor without an established unit makes the target
    unsupported.
    band 'target' (default): the band of the target's mode-C input (TARGET_BAND: FAU / DTU 1-20 Hz, Federici 2-8 Hz). Each donor
      contributes its statistic recorded in that band (_stats_band: 'A' for 1-20 Hz, 'A_2_8' for 2-8 Hz). A donor whose signal
      cannot hold the band (Federici, the authors' 2-8 Hz, for a 1-20 Hz target) has no same-band signal and is left out
      (donors_without_band); a donor whose signal contains the band but whose table lacks the statistic (SparrKULee for the
      Federici target: C4 records only 1-20 Hz) makes the target unsupported (missing_band 'unsupported', the default; with_band_sd()
      derives the statistic from the cohort's z-cache) or is left out and listed (missing_band 'skip').
    band 'own': every donor's 'A' statistic whatever its band (the rule of the synthetic fixture manifest).
    Values in uV come from _sd_uV (sd_prez_uV when the table holds it, cross-checked against sd_prez x units)."""
    if band not in ("target", "own") or missing_band not in ("unsupported", "skip"):
        raise ValueError(f"mode_c_scales: band {band!r} / missing_band {missing_band!r}")
    donors = tuple(donors) if donors is not None else ("sparrkulee",) + tuple(c for c in COHORTS if c != target)
    tb = TARGET_BAND[target] if band == "target" else None
    out = {"donors": list(donors), "band_rule": band, "target_band": None if tb is None else list(tb)}
    missing = [c for c in donors if units.get(c) is None]
    if missing:
        return {**out, "supported": False, "reason": f"no established unit for donor cache(s) {missing}"}
    keys, derivable, without = {}, [], []
    for c in donors:
        if band == "own":
            keys[c] = "A"
            continue
        sb = _stats_band(c, tables[c])
        hit = sorted((k for k, b in sb.items() if b == tb), key=lambda k: (k != "A", k))
        if hit:
            keys[c] = hit[0]
        elif "A" in sb and sb["A"][0] <= tb[0] and tb[1] <= sb["A"][1]:
            derivable.append(c)
        else:
            without.append(c)
    out.update(stat_keys=keys, donors_missing_band=derivable, donors_without_band=without)
    if derivable and missing_band == "unsupported":
        return {**out, "supported": False, "reason": f"donor table(s) {derivable} lack the pre-z SD in the target band {list(tb)} Hz "
                                                     "although their signal contains it (with_band_sd() derives it)"}
    vals, every, n_p = collections.defaultdict(list), [], {}
    for c, key in keys.items():
        lay, n_p[c] = list(tables[c]["layout"]), 0
        for p in tables[c]["participants"]:
            if not p.get("donor") or p.get("role", "fit") != "fit":
                continue
            n_p[c] += 1
            for n, v in zip(lay, _sd_uV(c, p, key, units[c])):
                if v is not None:
                    vals[n].append(v)
                    every.append(v)
    if not every:
        return {**out, "supported": False, "reason": "no donor pre-z SD"}
    lay_t = list(tables[target]["layout"])
    scale = {n: float(np.median(vals[n] if vals.get(n) else every)) for n in lay_t}
    return {**out, "supported": True, "unit": "uV", "scale": scale, "fallback": [n for n in lay_t if not vals.get(n)],
            "n_participants": n_p,
            "rule": "median over the leave-target-out donor-fit participants having the channel of their pre-z SD (uV) of the "
                    + ("signal in the target's mode-C band" if tb else "donor-training input ('A', any band)")
                    + "; names no donor has: median over all donor channels"}


def with_band_sd(table, cohort_dir, key="A", band=BAND_2_8):
    """A copy of a C4 / C5 cohort table (pieces.json, or build_sparrkulee runs.json) whose participants also hold the pre-z SD of
    the `key` signal band-passed to 2-8 Hz, stats key '<key>_2_8' (with sd_prez_uV when the table's unit is established, and
    cohort_info.stats_band), derived from the cohort's z-cache: x = z x sd_prez[key] + mu[key] per channel (the z-score is affine,
    so this is the source signal up to float16 rounding), contract.band(env_sos) over each cached piece, then the population SD
    over the guarded spans of every cached piece of the participant, masked (piece, channel) cells excluded. For C6: the
    SparrKULee donor of the Federici target's same-band mode-C scale (C4 records only 1-20 Hz). Reads the cache read-only."""
    if tuple(map(float, band)) != BAND_2_8:
        raise ValueError(f"with_band_sd: only the contract 2-8 Hz band (env_sos) is available, not {band}")
    t = json.loads(_dumps(table))
    ci = t["cohort_info"]
    lay, (g0, g1) = [C.canonical(n) for n in ci["layout"]], ci["guards"]
    cache = np.load(check_path(os.path.join(cohort_dir, C.CACHE_FILE[key])), mmap_mode="r", allow_pickle=False)
    items = t["pieces"] if "pieces" in t else t["runs"]
    by = collections.defaultdict(list)
    for q in items:
        if q.get("row_offset") is not None:
            by[q["participant"]].append(q)
    sos, newk = C.env_sos()[0], key + BAND_SUFFIX
    fac = (ci.get("unit") or {}).get("factor_to_uV")
    for p in t["participants"]:
        mu, sd, qs = (p.get("mu") or {}).get(key), (p.get("sd_prez") or {}).get(key), by.get(p["participant"], [])
        if mu is None or sd is None or not qs:
            continue
        mu = np.asarray(mu, dtype=np.float64)
        s = np.asarray([np.nan if v is None else v for v in sd], dtype=np.float64)
        segs = [[] for _ in lay]
        for q in qs:
            z = np.asarray(cache[q["row_offset"]:q["row_offset"] + q["T_eeg"]], dtype=np.float64).T
            y = C.band(z * np.where(np.isfinite(s) & (s > 0), s, 1.0)[:, None] + mu[:, None], sos)
            m = {lay.index(C.canonical(n)) for n in q.get("masked", [])}
            for c in range(len(lay)):
                if c not in m and np.isfinite(s[c]):
                    segs[c].append(y[c, g0:max(g0, y.shape[1] - g1)])
        val = [float(np.concatenate(v).std()) if v and sum(len(a) for a in v) else None for v in segs]
        p["sd_prez"][newk] = val
        if "sd_prez_uV" in p:
            p["sd_prez_uV"][newk] = None if fac is None else [None if v is None else v * fac for v in val]
    ci["stats_band"] = {**{k: list(b) for k, b in _stats_band(t.get("cohort", ""), t).items()}, newk: list(BAND_2_8)}
    return t


def _wav_info(path):
    """(channels, sample rate, bits per sample, frames) of a RIFF / WAVE file from its chunk headers; no sample is read."""
    import struct
    with open(check_path(path), "rb") as f:
        head = f.read(12)
        if len(head) < 12 or head[:4] != b"RIFF" or head[8:12] != b"WAVE":
            raise ValueError(f"{path}: not a RIFF / WAVE file")
        fmt = None
        while True:
            h = f.read(8)
            if len(h) < 8:
                raise ValueError(f"{path}: no data chunk")
            cid, size = h[:4], struct.unpack("<I", h[4:])[0]
            if cid == b"fmt ":
                body = f.read(size)
                if len(body) < 16:
                    raise ValueError(f"{path}: short fmt chunk")
                ch, fs = struct.unpack("<HI", body[2:8])
                fmt = (int(ch), int(fs), int(struct.unpack("<H", body[14:16])[0]))
                f.seek(size & 1, 1)
            elif cid == b"data":
                if fmt is None or not fmt[0] or not fmt[2]:
                    raise ValueError(f"{path}: data chunk before a valid fmt chunk")
                return fmt + (int(size // (fmt[0] * ((fmt[2] + 7) // 8))),)
            else:
                f.seek(size + (size & 1), 1)


def _aux_channel(r):
    """'aux0' / 'aux1': the aux channel whose r is >= AUX_R while the other's is < AUX_R (r = [r_aux0, r_aux1]); else None."""
    if r is None:
        return None
    v = [x if x is not None else 0.0 for x in r]
    k = int(np.argmax(v))
    return f"aux{k}" if v[k] >= AUX_R and v[1 - k] < AUX_R else None


def _stereo_side(path, att, dis):
    ev = {"file": path, "rule": SIDE_RULE}
    if att is None:
        return None, {**ev, "reason": "attended waveform unavailable"}
    if not os.path.exists(path):
        return None, {**ev, "reason": "stereo file absent"}
    import warnings
    from scipy.io import wavfile
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", wavfile.WavFileWarning)          # LIST / non-data chunks are skipped
        fs, w = wavfile.read(check_path(path))
    if w.ndim != 2 or w.shape[1] != 2:
        return None, {**ev, "reason": f"not a 2-channel file (shape {w.shape})"}
    if int(fs) != FAU_WAV_FS:
        return None, {**ev, "reason": f"sampling rate {fs} != {FAU_WAV_FS}"}
    n = min(len(w), len(att))
    ra = [_corr(w[:n, c], att[:n]) for c in (0, 1)]
    rd = [_corr(w[:n, c], dis[:n]) for c in (0, 1)] if dis is not None else [None, None]
    k = int(np.argmax(ra))
    ok = ra[k] >= SIDE_R and ra[1 - k] < SIDE_R_OTHER and (dis is None or (rd[1 - k] >= SIDE_R and rd[k] < SIDE_R_OTHER))
    rec = {**ev, "fs": int(fs), "n": int(n), "len_stereo": int(len(w)), "len_published": int(len(att)), "r_attended": ra,
           "r_distractor": rd}
    if not ok:
        rec["reason"] = ("correlations do not identify one channel"
                         + ("; the stereo file's length differs from the published waveform's, so it does not hold this code's "
                            "waveforms" if len(w) != len(att) else ""))
    return (("left", "right")[k] if ok else None), rec


# ---------------------------------------------------------------------------------------------------------- sources
class FauSource:
    """FAU / TUD through the stage-B cache (auditory_alignment.data.load_fau's participants, folds and trials)."""
    cohort, fs, signals = "fau", 128, ("ica", "noica")
    DSET = {"ica": "eeg_1_20_ica", "noica": "eeg_1_20_noica"}

    def __init__(self):
        from auditory_alignment import data, prep_targets
        self.data, self.env_path = data, prep_targets.FAU_ENV
        self.stageb, self.pub, self.repo = data.STAGEB, data.PUB, data.REPO
        self.receipt = os.path.join(self.repo, "private", "auditory_c3", "receipts", "fau_tud_schema_private_001.json")
        self.chanmap = os.path.join(self.pub, "derived", "c3_preproc_v1", "_logs", "fau_tud_chanmap.json")
        self.notes = {}

    def _aux(self):
        if not os.path.exists(self.receipt):
            self.notes["aux_source"] = f"{self.receipt} absent"
            return {}
        d, out = _read_json(self.receipt), {}
        for grp in ("ha", "ci", "th"):
            for r in (d.get(grp) or {}).get("_alignment_rows", []):
                out[(str(r["subject"]), int(r["trial"]))] = {
                    "r_attended": [_num((r.get(f"aux{i}_attended_env") or {}).get("r")) for i in (0, 1)],
                    "r_distractor": [_num((r.get(f"aux{i}_distractor_env") or {}).get("r")) for i in (0, 1)],
                    "stimulus": str(r.get("stimulus"))}
        self.notes["aux_source"] = self.receipt
        return out

    @staticmethod
    def aux_on(ev):
        """The aux channel carrying the attended stream of one trial (AUX_RULE), or None."""
        return None if ev is None else _aux_channel(ev["r_attended"])

    def participants(self, select=None):
        dev, panel = self.data.fau_panel()
        rows = [(s, "th", -1, True) for s in dev] + [(s, g, f, False) for s, (g, f) in sorted(panel.items())]
        rows = _select(rows, select, "fau")
        aux, out = self._aux(), []
        for s, grp, fold, dv in rows:
            path = os.path.join(self.stageb, grp, f"{s}.h5")
            pieces = []
            with _h5(path) as f:
                _layout_check(_strs(f.attrs["channels"]), "fau", path)
                bads = _ordered(_strs(f.attrs.get("bads_interpolated")), "fau")
                g_attr = int(f.attrs["guard_samples"]) if "guard_samples" in f.attrs else None
                for t in sorted(f.keys()):
                    g = f[t]
                    code = _s(g.attrs["stimulus"])
                    if not re.fullmatch(r"[12][12]\d", code):
                        raise ValueError(f"{path}/{t}: unexpected stimulus code {code!r}")
                    shp = {k: tuple(g[d].shape) for k, d in self.DSET.items()}
                    if len(set(shp.values())) != 1 or shp["ica"][0] != len(C.MONTAGES["fau"]):
                        raise ValueError(f"{path}/{t}: shapes {shp}")
                    vs = int(g.attrs["valid_start"]) if "valid_start" in g.attrs else None
                    ve = int(g.attrs["valid_stop"]) if "valid_stop" in g.attrs else None
                    cs = code[0] == "2"
                    ev = aux.get((s, int(t.split("_")[-1])))
                    pieces.append({"trial": t, "kind": "cs" if cs else "ss", "stimulus": code,
                                   "ignored_stimulus": f"{code}/distractor" if cs else None, "content_group": None,
                                   "stream_key": f"{code}/attended", "ignored_stream_key": f"{code}/distractor" if cs else None,
                                   "ignored_lead": 0, "role": "fit", "T_native": int(shp["ica"][1]),
                                   "family_name": f"fau:{code}", "family_offset": 0, "family_basis": "own", "family_clock": "known",
                                   "condition": "competing" if cs else "single-speaker",
                                   "extra": {"part": code[2], "story": code[1], "aux_evidence": ev, "aux_attended_on": None,
                                             "aux_distractor_on": None, "aux_status": None,
                                             "source": {"file": path, "group": t, "datasets": dict(self.DSET)},
                                             "stageb": {"valid_start": vs, "valid_stop": ve, "guard_samples": g_attr,
                                                        "extra_guard_128": None if vs is None or g_attr is None else vs - g_attr,
                                                        "realigned_copy": bool(g.attrs.get("realigned_copy", False)),
                                                        "aux_lag_ms": _num(g.attrs.get("aux_lag_ms"))}}})
            out.append({"participant": s, "uid": f"fau:{s}", "identity": s, "group": grp, "fold": int(fold), "dev": bool(dv),
                        "test_only": False, "donor": True, "masked": bads, "source_file": path, "_pieces": pieces})
        return out

    def _code_info(self, code, pub):
        cs = code[0] == "2"
        att = dis = None
        why = None
        if pub and os.path.exists(pub):
            with _h5(pub) as f:
                g = f["stimulus_files"][code]
                att = np.asarray(g["attended_wav"][()]).reshape(-1)
                if cs:
                    dis = np.asarray(g["distractor_wav"][()]).reshape(-1)
        else:
            why = f"published HDF5 {pub!r} absent"
        info = {"code": code, "kind": "cs" if cs else "ss", "onset_s": None, "onset_rule": None}
        if cs:
            if dis is None:
                raise RuntimeError(f"FAU {code}: the distractor waveform is needed for the competing-talker onset rule ({why})")
            nz = np.flatnonzero(np.nan_to_num(dis.astype(np.float64)) != 0)
            if not len(nz):
                raise RuntimeError(f"FAU {code}: silent distractor waveform")
            info["onset_s"] = float(nz[0]) / FAU_WAV_FS
            info["onset_rule"] = f"first nonzero sample of {pub}:stimulus_files/{code}/distractor_wav / {FAU_WAV_FS} Hz"
        info["side"], info["side_evidence"] = self._side(code, att, dis)
        if why:
            info["side_evidence"]["published"] = why
        return info

    def _side(self, code, att, dis):
        """SIDE_RULE: the attended side from S<code>.wav, or, when that file fails the rule, from the single other S<ddd>.wav of the
        published waveform's frame count that passes it (headers are read for the frame count; only such candidates are loaded)."""
        folder = os.path.join(self.pub, "fau_tud", "stimuli", "stimuli")
        want = f"S{code}.wav"
        side, ev = _stereo_side(os.path.join(folder, want), att, dis)
        ev = {**ev, "expected_file": want, "matched_file": want if side else None, "file_name_mismatch": False}
        if side is not None or att is None or not os.path.isdir(folder):
            return side, ev
        cands = []
        for fn in sorted(os.listdir(folder)):
            if fn == want or not _STEREO_NAME.fullmatch(fn):
                continue
            try:
                ch, fs, _, frames = _wav_info(os.path.join(folder, fn))
            except ValueError:
                continue
            if ch == 2 and fs == FAU_WAV_FS and frames == len(att):
                s2, e2 = _stereo_side(os.path.join(folder, fn), att, dis)
                cands.append({"file": fn, "side": s2, "r_attended": e2.get("r_attended"), "r_distractor": e2.get("r_distractor")})
        hits = [c for c in cands if c["side"] is not None]
        ev["content_search"] = {"candidates": cands, "rule": "other S<ddd>.wav files of the published frame count, SIDE_RULE"}
        if len(hits) == 1:
            ev = {**ev, "matched_file": hits[0]["file"], "file_name_mismatch": True}
            ev["expected_file_reason"] = ev.pop("reason", None)
            return hits[0]["side"], ev
        if len(hits) > 1:
            ev["reason"] = f"{ev.get('reason')}; several other stereo files match: {[c['file'] for c in hits]}"
        return None, ev

    def stimuli(self, parts):
        codes = sorted({q["stimulus"] for p in parts for q in p["_pieces"]})
        specs, quirk = [], []
        org, band = ORIGIN["fau"]
        with _h5(self.env_path) as f:
            src_rel = _s(f.attrs["source"]) if "source" in f.attrs else None
            for code in codes:
                cs = code[0] == "2"
                for stream in ("attended", "distractor") if cs else ("attended",):
                    ds, att = f"{code}/{stream}_env/raw", stream == "attended"
                    specs.append({"key": f"{code}/{stream}", "name": f"{code}/{stream}", "kind": stream, "raw": f[ds][()], "fs": 128,
                                  "family_name": f"fau:{code}" if att else None, "family_offset": 0 if att else None,
                                  "family_basis": "own" if att else None, "origin": org, "original_band": band,
                                  "source": {"file": self.env_path, "dataset": ds}, "roles": [stream]})
                if not cs and f"{code}/distractor_env/raw" in f and np.isfinite(f[f"{code}/distractor_env/raw"][()]).any():
                    quirk.append(code)
        pub = os.path.join(self.pub, src_rel) if src_rel else None
        info = {code: self._code_info(code, pub) for code in codes}
        self.notes["ss_codes_with_a_finite_distractor_env (ignored: single-talker pieces use the attended stream only)"] = quirk
        return specs, info

    def complete(self, parts, info):
        for p in parts:
            p["cs_side"] = {}
            for q in p["_pieces"]:
                ci = info[q["stimulus"]]
                q["attended_side"] = ci["side"]
                if q["kind"] == "cs":
                    q["onset_s"] = ci["onset_s"]
                    q["presentation_key"] = f"fau:{q['stimulus']}|side={ci['side'] or 'unknown'}"
                    p["cs_side"][q["stimulus"]] = ci["side"]
                else:
                    q["onset_s"] = None
                    q["presentation_key"] = f"fau:{q['stimulus']}"
        self._aux_status(parts)

    def _aux_status(self, parts):
        """AUX_RULE per trial (extra aux_attended_on / aux_distractor_on / aux_status) and per listener (aux_pattern); the majority
        aux -> side mapping is voted by the listeners without a single-channel pattern. Diagnostic only: no key depends on it."""
        raw, single = {}, {}
        for p in parts:
            cs_both = []
            for q in p["_pieces"]:
                ev, x = q["extra"]["aux_evidence"], q["extra"]
                x["aux_attended_on"] = None if ev is None else _aux_channel(ev["r_attended"])
                x["aux_distractor_on"] = None if ev is None or q["kind"] != "cs" else _aux_channel(ev["r_distractor"])
                if x["aux_attended_on"] is None or q["attended_side"] is None:
                    raw[id(q)] = "undetermined"
                elif q["kind"] == "cs" and x["aux_distractor_on"] == x["aux_attended_on"]:
                    raw[id(q)] = "single_channel"
                else:
                    raw[id(q)] = "determined"
                if q["kind"] == "cs" and x["aux_attended_on"] is not None and x["aux_distractor_on"] is not None:
                    cs_both.append(x["aux_attended_on"] == x["aux_distractor_on"])
            single[p["participant"]] = bool(cs_both) and all(cs_both)
        votes = collections.Counter((q["extra"]["aux_attended_on"], q["attended_side"]) for p in parts if not single[p["participant"]]
                                    for q in p["_pieces"] if raw[id(q)] == "determined")
        same = votes[("aux0", "left")] + votes[("aux1", "right")]
        swap = votes[("aux0", "right")] + votes[("aux1", "left")]
        mapping = {"aux0": "left", "aux1": "right"} if same >= swap else {"aux0": "right", "aux1": "left"}
        for p in parts:
            n = collections.Counter()
            for q in p["_pieces"]:
                st = raw[id(q)]
                if single[p["participant"]] and st != "undetermined":
                    st = "single_channel"
                elif st == "determined":
                    st = "consistent" if mapping[q["extra"]["aux_attended_on"]] == q["attended_side"] else "inconsistent"
                q["extra"]["aux_status"] = st
                n[st] += 1
            p["aux_pattern"] = ("single_channel" if single[p["participant"]] else "undetermined" if not n["consistent"] + n["inconsistent"]
                                else "consistent" if not n["inconsistent"] else "swapped" if not n["consistent"] else "unexplained")
        self.aux_mapping = {"majority_mapping": mapping, "votes": {f"{a}->{s}": k for (a, s), k in sorted(votes.items())}}

    def checks(self, parts, pieces, info):
        per = collections.defaultdict(collections.Counter)
        for q in pieces:
            per[q["participant"]][q["aux_status"]] += 1
        pat = collections.defaultdict(list)
        for p in parts:
            pat[p["aux_pattern"]].append(p["participant"])
        extra = [q["stageb"]["extra_guard_128"] for q in pieces if q["stageb"]["extra_guard_128"] is not None]
        return {"codes": info, "codes_without_side": {c: v["side_evidence"].get("reason") for c, v in sorted(info.items())
                                                       if v["side"] is None},
                "stereo_file_name_mismatches": {c: v["side_evidence"]["matched_file"] for c, v in sorted(info.items())
                                                if v["side_evidence"].get("file_name_mismatch")},
                "aux": {"rule": AUX_RULE, "interpretation": AUX_NOTE, **getattr(self, "aux_mapping", {}),
                        "listeners_by_pattern": {k: sorted(v) for k, v in sorted(pat.items())},
                        "trials_by_listener": {p: dict(sorted(c.items())) for p, c in sorted(per.items())
                                               if set(c) - {"consistent"}},
                        "listeners_unexplained": sorted(pat.get("unexplained", [])),
                        "n_trials_by_status": dict(sorted(collections.Counter(q["aux_status"] for q in pieces).items()))},
                "stageb_extra_guard_128": {"max": max(extra) if extra else None, "n_trials_positive": sum(e > 0 for e in extra)},
                **self.notes}

    def unit_documented(self):
        if not os.path.exists(self.chanmap):
            return None, f"{self.chanmap} absent"
        d = _read_json(self.chanmap)
        ratios = {g: _num((d.get(g) or {}).get("scale_ratio_median")) for g in ("ha", "ci", "th")}
        if all(r is not None and 0.1 <= r <= 10 for r in ratios.values()):
            return "V", (f"{self.chanmap}: SD(published 1 kHz HDF5) / SD(BrainVision raw read by MNE, volts) median ratios {ratios} "
                         f"(same unit: volts); stage A / B (FIR, resample_poly, re-reference, interpolation, ICA) are linear")
        return None, f"{self.chanmap}: ratios {ratios} do not identify the unit"

    def read(self, p, sigs):
        out = {s: [] for s in sigs}
        with _h5(p["source_file"]) as f:
            for q in p["_pieces"]:
                for s in sigs:
                    out[s].append(np.asarray(f[q["trial"]][self.DSET[s]][()], dtype=np.float64))
        return out


class DtuSource:
    """DTU through the stage-A cache (auditory_alignment.data.load_dtu's subjects, folds and trial filter), CAR applied here."""
    cohort, fs, signals = "dtu", 128, ("car",)
    SIDE = {"attendleft": "left", "attendright": "right"}

    def __init__(self):
        from auditory_alignment import data
        self.data, self.pub, self.pre, self.kcs, self.repo = data, data.PUB, data.DTU_PRE, data.DTU_KCS, data.REPO
        self.tsv = f"{self.pub}/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv"
        self.inv = f"{self.pub}/derived/c3_features_v1/dtu/inventory.json"
        self.audio = os.path.join(self.kcs, "audio_local.h5")
        self.code_shas, self.excluded, self.unread, self.notes = {}, [], [], {}

    def _tf_keys(self):
        keys = []
        for cf in (0, 1):
            with _h5(os.path.join(self.kcs, f"dtu_cf{cf}.h5")) as f:
                keys.append(set(f.keys()))
        self.notes["dtu_cf0_cf1_same_keys"] = keys[0] == keys[1]
        return keys[0] & keys[1]

    def participants(self, select=None):
        tsv = _read_tsv(self.tsv)
        hs = {r["participant_id"]: r["hearing_status"] for r in tsv}
        age = {r["participant_id"]: _num(r.get("age")) for r in tsv}
        subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(self.repo, "private", "auditory_c3", "public", "dtu_v2",
                                                                                 "*.json")))
        folds = self.data._folds({g: [s for s in subs if hs[s] == g] for g in ("nh", "hi")})
        self.inv_rows = _read_json(self.inv)
        sha = {(r["file"], r["trial"], r["kind"]): (r.get("sha"), r["offset_s"]) for r in self.inv_rows}
        cg = _read_json(os.path.join(self.kcs, "content_groups.json"))["content"]
        tf = self._tf_keys()
        out = []
        self.selected = [s for (s,) in _select([(s,) for s in subs], select, "dtu")]
        for s in self.selected:
            grp, path, pieces = hs[s], os.path.join(self.pre, f"{s}.h5"), []
            with _h5(path) as f:
                _layout_check(_strs(f.attrs["channels"])[:64], "dtu", path)
                self.code_shas[s] = _s(f.attrs["code_sha256"]) if "code_sha256" in f.attrs else None
                for k in sorted(f.keys()):
                    g = f[k]
                    two = _s(g.attrs["talkers"]) == "twotalker"
                    th, _ = sha.get((s, k, "target"), (None, 0))
                    mh, moff = sha.get((s, k, "masker"), (None, 0))
                    why = ("no target sha in inventory.json" if th is None else "target sha not in content_groups.json" if th not in cg
                           else "target sha not in dtu_cf0/1.h5" if th not in tf
                           else "masker sha missing from inventory.json or dtu_cf0/1.h5" if two and (mh is None or mh not in tf)
                           else None)
                    if why:
                        self.excluded.append({"participant": s, "trial": k, "group": grp, "kind": "cs" if two else "ss",
                                              "target_sha": th, "reason": why})
                        continue
                    n = tuple(g["eeg_1_20"].shape)
                    if n[0] < 64:
                        raise ValueError(f"{path}/{k}: {n[0]} rows < 64")
                    side = self.SIDE.get(_s(g.attrs.get("attend_left_right", "")))
                    mon = _num(g.attrs.get("masker_onset_rel_s")) if two else None
                    if two and mon is None:
                        raise ValueError(f"{path}/{k}: two-talker trial without a masker onset")
                    eq, c = grp == "hi", cg[th]
                    moff = float(moff) if two else None
                    base = f"dtu:{th}+{mh}@{moff!r}" if two else f"dtu:{th}"
                    pieces.append({"trial": k, "kind": "cs" if two else "ss", "stimulus": th, "ignored_stimulus": mh if two else None,
                                   "content_group": int(c["group"]), "stream_key": th,
                                   "ignored_stream_key": self.placed_key(mh, moff) if two else None,
                                   "ignored_lead": 0, "onset_s": mon, "attended_side": side,
                                   "presentation_key": f"{base}|side={side}" + (f"|eq={s}/{k}" if eq else ""),
                                   "family_name": f"dtu:{th}", "family_offset": 0, "family_basis": "own", "family_clock": "known",
                                   "condition": ("two-talker" if two else "single-talker") + (" (individually equalised)" if eq else ""),
                                   "role": "fit" if grp == "nh" and not two else "target_only", "T_native": int(n[1]),
                                   "extra": {"content_half": int(c["half"]), "content_early_stop": bool(c["early_stop"]),
                                             "masker_offset_s": moff, "ignored_placement": "fractional_delay" if two else None,
                                             "attend_male_female": _s(g.attrs.get("attend_male_female", "")) or None,
                                             "stim_file": _s(g.attrs.get("stim_file", "")) or None,
                                             "source": {"file": path, "group": k, "dataset": "eeg_1_20", "rows": [0, 64]}}})
            out.append({"participant": s, "uid": f"dtu:{s}", "identity": s, "group": grp, "fold": int(folds[s]), "dev": False,
                        "test_only": False, "donor": grp == "nh", "masked": [], "age": age.get(s), "source_file": path,
                        "_pieces": pieces})
        known = {f"{s}.h5" for s in subs}
        self.unread = []
        for x in sorted(os.listdir(self.pre)) if os.path.isdir(self.pre) else []:
            if x.endswith(".h5") and x not in known:                     # listed from the inventory only, never opened
                trials = self._inventory_trials(x[:-3])
                self.unread.append({"file": os.path.join(self.pre, x), "reason": "not read by auditory_alignment.data.load_dtu "
                                    "(<subject>.h5 only)", "n_inventory_trials": len(trials), "inventory_trials": trials})
        return out

    @staticmethod
    def placed_key(masker, offset_s):
        """Stream key of a masker placed on the trial grid at its offset (FRAC_RULE)."""
        return f"{masker}@{float(offset_s)!r}"

    def _inventory_trials(self, stem):
        """inventory.json trials of one file stem (file name without .h5): kind, hearing, target / masker sha, masker offset."""
        tr = collections.defaultdict(dict)
        for r in self.inv_rows:
            if r["file"] == stem:
                tr[r["trial"]][r["kind"]] = r
        out = []
        for t, v in sorted(tr.items()):
            tg, mk = v.get("target") or {}, v.get("masker") or {}
            out.append({"trial": t, "kind": "cs" if mk else "ss", "hearing": "hi" if (tg or mk).get("hi") else "nh",
                        "target_sha": tg.get("sha"), "masker_sha": mk.get("sha"), "masker_offset_s": _num(mk.get("offset_s"))})
        return out

    def stimuli(self, parts):
        tgt = {q["stimulus"] for p in parts for q in p["_pieces"]}
        placed = sorted({(q["ignored_stimulus"], q["extra"]["masker_offset_s"]) for p in parts for q in p["_pieces"]
                         if q["ignored_stimulus"]})
        msk = {h for h, _ in placed}
        hi = {q["stimulus"] for p in parts if p["group"] == "hi" for q in p["_pieces"]}
        org, band = ORIGIN["dtu"]
        specs = []
        with _h5(self.audio) as f:
            for h in sorted(tgt):
                specs.append({"key": h, "name": h, "kind": "attended", "raw": f[f"{h}/env"][()], "fs": 128,
                              "family_name": f"dtu:{h}", "family_offset": 0, "family_basis": "own",
                              "origin": org + ("; the 'woa' original of an HI listener's individually equalised presentation"
                                               if h in hi else ""),
                              "original_band": band, "source": {"file": self.audio, "dataset": f"{h}/env"},
                              "roles": ["target"] + (["masker"] if h in msk else [])})
            raw_m = {h: f[f"{h}/env"][()] for h in sorted(msk)}
        for h, off in placed:
            specs.append({"key": self.placed_key(h, off), "name": self.placed_key(h, off), "kind": "masker", "raw": raw_m[h], "fs": 128,
                          "family_name": None, "family_offset": None, "family_basis": None,
                          "origin": org + "; placed on the trial grid at the masker offset (FRAC_RULE)", "original_band": band,
                          "source": {"file": self.audio, "dataset": f"{h}/env"}, "roles": ["masker"],
                          "place": {"masker_sha": h, "offset_s": off, "delay_64": off * C.FS}})
        return specs, {}

    def complete(self, parts, info):
        pass

    def checks(self, parts, pieces, info):
        sides = collections.defaultdict(set)
        for q in pieces:
            if q["group"] == "nh" and q["kind"] == "ss":
                sides[q["stimulus"]].add(q["attended_side"])
        return {"nh_single_talker_shas_with_mixed_sides": sorted(h for h, v in sides.items() if len(v) > 1),
                "stage_a_code_sha256": sorted({str(v) for v in self.code_shas.values()}),
                "inventory_reconciliation": self._reconcile(pieces), **self.notes}

    def _reconcile(self, pieces):
        """Design §3.5: the inventory's trials against the cache (loaded / excluded by load_dtu's filter / in a file load_dtu never
        reads / not selected in a partial build), and the NH single-talker shas heard by >= 2 NH listeners (subjects; a file stem
        '<sub>_run-N' belongs to <sub>) in the inventory and in the cache; shas that drop below 2 listeners are listed."""
        inv = collections.defaultdict(dict)
        for r in self.inv_rows:
            inv[(r["file"], r["trial"])][r["kind"]] = r
        loaded = {(q["participant"], q["trial"]) for q in pieces}
        excl = {(e["participant"], e["trial"]): e["reason"] for e in self.excluded}
        unread = {os.path.basename(u["file"])[:-3] for u in self.unread}
        sel = set(getattr(self, "selected", []))
        rows, counts = [], collections.Counter()
        for (f, t), v in sorted(inv.items()):
            tg, mk = v.get("target") or {}, v.get("masker") or {}
            hear, kind = ("hi" if (tg or mk).get("hi") else "nh"), ("cs" if mk else "ss")
            st = ("loaded" if (f, t) in loaded else "excluded" if (f, t) in excl else "unread_file" if f in unread
                  else "not_selected" if f.split("_run")[0] not in sel else "absent")
            counts[f"{hear}/{kind}/{st}"] += 1
            rows.append({"file": f, "trial": t, "subject": f.split("_run")[0], "hearing": hear, "kind": kind,
                         "target_sha": tg.get("sha"), "status": st, "reason": excl.get((f, t))})
        lis = {w: collections.defaultdict(set) for w in ("inventory", "cache")}
        n = {w: collections.Counter() for w in ("inventory", "cache")}
        for r in rows:
            if r["hearing"] == "nh" and r["kind"] == "ss":
                lis["inventory"][r["target_sha"]].add(r["subject"])
                n["inventory"][r["target_sha"]] += 1
                if r["status"] == "loaded":
                    lis["cache"][r["target_sha"]].add(r["subject"])
                    n["cache"][r["target_sha"]] += 1
        ge2 = {w: {h for h, v in lis[w].items() if len(v) >= 2} for w in lis}
        nh_ss = {f"{w}_{k}": v for w in ("inventory", "cache") for k, v in
                 (("trials", sum(n[w].values())), ("shas", len(lis[w])), ("shas_ge2_listeners", len(ge2[w])),
                  ("trials_on_shas_ge2", sum(n[w][h] for h in ge2[w])))}
        return {"trials": dict(sorted(counts.items())), "nh_single_talker": nh_ss,
                "shas_below_2_listeners_in_cache": sorted(ge2["inventory"] - ge2["cache"]),
                "not_loaded": [r for r in rows if r["status"] != "loaded"]}

    def unit_documented(self):
        pre = os.path.join(self.repo, "auditory_c3", "preproc.py")
        if not os.path.exists(pre):
            return None, f"{pre} absent"
        sha, shas = _file_sha(pre), set(self.code_shas.values())
        if shas == {sha} and DTU_UV_LINE in _read_text(pre):
            return "uV", (f"every stage-A file's code_sha256 attribute equals sha256(auditory_c3/preproc.py) = {sha}, whose dtu() "
                          f"writes {DTU_UV_LINE} (MNE read_raw_bdf volts -> uV); stage-A FIR / resample_poly and our CAR are linear")
        return None, f"stage-A code_sha256 {sorted(map(str, shas))} vs preproc.py {sha}: the documented unit does not apply"

    def read(self, p, sigs):
        out = []
        with _h5(p["source_file"]) as f:
            for q in p["_pieces"]:
                x = np.asarray(f[q["trial"]]["eeg_1_20"][()], dtype=np.float64)[:64]
                out.append(x - x.mean(axis=0, keepdims=True))                 # CAR over the 64 EEG channels
        return {"car": out}


class FedSource:
    """Federici through the c3_preproc_v1 reformat (auditory_alignment.data.load_federici's people, identities and folds)."""
    cohort, fs, signals = "federici", 100, ("authors",)
    GROUPS = ("HC", "CI", "HC-v", "Artifact")
    COND = {"HC": "natural", "CI": "natural", "HC-v": "vocoded", "Artifact": "phantom"}

    def __init__(self):
        from auditory_alignment import data, federici_content
        self.data, self.fc, self.pre = data, federici_content, data.FED_PRE
        self.content = os.path.join(federici_content.OUT, "content_groups.json")
        self.env_first, self.notes = {}, {}

    @staticmethod
    def identity(grp, fid):
        return fid if grp in ("HC", "HC-v") else f"{grp}:{fid}"          # HC N and HC-v N share only the fold key N

    def participants(self, select=None):
        people = [(g, p) for g in self.GROUPS for p in sorted(glob.glob(os.path.join(self.pre, g, "*.h5")))]
        ids = [(g, os.path.basename(p)[:-3]) for g, p in people]
        folds = self.data._folds({"hc": sorted({self.identity(g, f) for g, f in ids if g in ("HC", "HC-v")}),
                                  "ci": sorted({self.identity(g, f) for g, f in ids if g == "CI"})})
        items = {it["key"]: it for it in _read_json(self.content)["items"]}
        gsize = collections.Counter(int(it["group"]) for it in items.values())
        out = []
        for pid, grp, path, fid in _select([(f"{g}:{f}", g, p, f) for (g, p), (_, f) in zip(people, ids)], select, "federici"):
            ident = self.identity(grp, fid)
            with _h5(path) as f:
                _layout_check(_strs(f.attrs["channels"]), "federici", path)
                env, shp = np.asarray(f["env"][()], dtype=np.float64), tuple(f["eeg"].shape)
            if env.ndim != 2 or len(shp) != 3 or shp[0] != env.shape[0] or shp[1] != len(C.MONTAGES["federici"]) or shp[2] != env.shape[1]:
                raise ValueError(f"{path}: eeg {shp} / env {env.shape}")
            pieces = []
            for b, e in enumerate(env):
                key = self.fc.env_key(((e - e.mean()) / (e.std() + 1e-12)).astype(np.float32))
                it = items.get(key)
                if it is None:
                    raise ValueError(f"{path} block {b}: envelope item {key} not in {self.content}")
                self.env_first.setdefault(key, (e, f"{path}#env[{b}]"))
                g, multi = int(it["group"]), gsize[int(it["group"])] > 1
                pieces.append({"trial": f"block_{b}", "kind": "ss", "stimulus": key, "ignored_stimulus": None, "content_group": g,
                               "stream_key": key, "ignored_stream_key": None, "ignored_lead": 0, "onset_s": None, "attended_side": None,
                               "presentation_key": None, "family_name": f"federici:g{g}",           # key and condition: complete()
                               "family_offset": None if multi else 0,
                               "family_basis": "content_group: natural / vocoded or overlapping items (C3 measures the offsets)" if multi
                               else "own", "family_clock": "pending_C3" if multi else "known", "condition": None,
                               "role": "target_only" if grp == "Artifact" else "fit", "T_native": int(shp[2]),
                               "extra": {"content_role": it.get("role"), "block": b, "item_n_listeners": it.get("n_listeners"),
                                         "session_condition": self.COND[grp], "source": {"file": path, "dataset": "eeg", "index": b}}})
            out.append({"participant": pid, "uid": f"federici:{pid}", "identity": ident, "group": grp, "fold": int(folds.get(ident, -1)),
                        "dev": False, "test_only": grp == "Artifact", "donor": grp != "Artifact", "phantom": grp == "Artifact",
                        "masked": [], "source_file": path, "_pieces": pieces})
        return out

    def stimuli(self, parts):
        fam = {q["stimulus"]: q for p in parts for q in p["_pieces"]}
        org, band = ORIGIN["federici"]
        specs = [{"key": k, "name": k, "kind": "item", "raw": self.env_first[k][0], "fs": 100, "family_name": fam[k]["family_name"],
                  "family_offset": fam[k]["family_offset"], "family_basis": fam[k]["family_basis"], "origin": org, "original_band": band,
                  "source": {"file": self.env_first[k][1]}, "roles": ["item"]} for k in sorted(fam)]
        return specs, {}

    def complete(self, parts, info):
        """FED_COND_RULE: presentation key 'federici:<item>' (§2.5: the item envelope hash) and the item's condition for human
        blocks; the phantom's blocks 'federici:<item>|phantom', condition 'phantom' (never shared with a human)."""
        groups = collections.defaultdict(set)
        for p in parts:
            if not p["phantom"]:
                for q in p["_pieces"]:
                    groups[q["stimulus"]].add(p["group"])
        cond = {k: "vocoded" if g <= {"HC-v"} else "natural" for k, g in groups.items()}
        for p in parts:
            for q in p["_pieces"]:
                if p["phantom"]:
                    q["condition"], q["presentation_key"] = "phantom", f"federici:{q['stimulus']}|phantom"
                else:
                    q["condition"], q["presentation_key"] = cond[q["stimulus"]], f"federici:{q['stimulus']}"

    def checks(self, parts, pieces, info):
        ses, item_cond = collections.defaultdict(set), {}
        for q in pieces:
            if q["session_condition"] != "phantom":
                ses[q["stimulus"]].add(q["session_condition"])
                item_cond[q["stimulus"]] = q["condition"]
        return {"items_heard_in_natural_and_vocoded_sessions": sorted(k for k, v in ses.items() if {"natural", "vocoded"} <= v),
                "item_condition_rule": FED_COND_RULE,
                "n_items_by_condition": dict(sorted(collections.Counter(item_cond.values()).items())),
                "phantom_sessions": sorted(p["participant"] for p in parts if p["phantom"]),
                "hc_hcv_rule": "HC-v N is a separate identity (uid); it shares only the fold key N with HC N (ALN3 Option A); file "
                               "numbers are not identity evidence; partner_exclusions lists the would-be HC N / HC-v N pairs"}

    def unit_documented(self):
        return None, ("undocumented: the authors' EEGLAB export *_preprocEEG_cut_ica.mat (stage A read this non-z-scored file; a "
                      "*_zsc.mat z-scored copy sits beside it); the magnitude rule decides")

    def read(self, p, sigs):
        with _h5(p["source_file"]) as f:
            E = np.asarray(f["eeg"][()], dtype=np.float64)
        return {"authors": [E[q["extra"]["block"]] for q in p["_pieces"]]}


SOURCES = {"fau": FauSource, "dtu": DtuSource, "federici": FedSource}


def _select(rows, select, cohort):
    """Rows (participant id first) in table order, restricted to `select` (None: all) before any participant file is opened."""
    if select is None:
        return list(rows)
    want = set(select)
    miss = sorted(want - {r[0] for r in rows})
    if miss or not want:
        raise ValueError(f"{cohort}: unknown participants {miss or sorted(want)}")
    return [r for r in rows if r[0] in want]


def _partner_exclusions(cohort, parts):
    if cohort != "federici":
        return []
    have = {p["participant"] for p in parts}
    return [["federici", f"HC:{p['identity']}", p["participant"]] for p in parts
            if p["group"] == "HC-v" and f"HC:{p['identity']}" in have]


# ---------------------------------------------------------------------------------------------------------- layout
def plan(src, participants=None):
    """Mode-independent layout of one cohort: participants, pieces with row offsets and segment starts, streams and the
    concatenated envelope, the cohort-local presentation / family registries, partner exclusions and checks. Reads metadata and
    stimulus envelopes only (no EEG array). Returns a dict; 'layout_sha256' covers everything that the caches depend on."""
    cohort = src.cohort
    parts = src.participants(None if participants is None else [str(x) for x in participants])
    specs, info = src.stimuli(parts)
    src.complete(parts, info)
    lay = C.MONTAGES[cohort]
    # streams and the envelope
    specs = sorted(specs, key=lambda s: s["key"])
    fams = sorted({q["family_name"] for p in parts for q in p["_pieces"]} | {s["family_name"] for s in specs if s["family_name"]})
    fam_id = {f: i for i, f in enumerate(fams)}
    rows, env, sid, off, base = [], [], {}, 0, {}
    shas = C.filter_shas()
    aa = shas.get(f"aa_fir_{src.fs}")
    for i, sp in enumerate(specs):
        raw64 = np.ascontiguousarray(np.asarray(sp["raw"], dtype=np.float64).reshape(-1))
        pl = sp.get("place")
        if pl is None:
            en, rms, bad = envelope64(raw64, sp["fs"])
        else:                       # a masker placed on the trial grid (FRAC_RULE): its own contract envelope, delayed exactly
            if pl["masker_sha"] not in base:
                base[pl["masker_sha"]] = envelope64(raw64, sp["fs"])
            b, rms, bad = base[pl["masker_sha"]]
            en = frac_delay(b, pl["delay_64"], int(np.ceil(pl["delay_64"])) + len(b)).astype(np.float32)
        chain = ([f"aa_fir_{sp['fs']}"] if sp["fs"] != C.FS else []) + ["env_sos"]
        rows.append({"stream": i, "name": sp["name"], "key": sp["key"], "kind": sp["kind"], "offset": off, "length": int(len(en)),
                     "family": fam_id.get(sp["family_name"]), "family_name": sp["family_name"], "family_offset": sp["family_offset"],
                     "family_basis": sp["family_basis"], "rms": rms, "nan_count": bad, "origin": sp["origin"],
                     "original_band": sp["original_band"], "source": sp["source"], "fs_source": int(sp["fs"]),
                     "T_source": int(raw64.size), "roles": sp["roles"], "source_sha256": hashlib.sha256(raw64.tobytes()).hexdigest(),
                     "filter_sha256": {k: shas[k] for k in chain}, "filter_padlen": f"min({C.ENV_PADLEN}, T - 1)"})
        if pl is not None:
            rows[-1]["placement"] = {**pl, "rule": FRAC_RULE, "base_length": int(len(base[pl["masker_sha"]][0]))}
        env.append(en)
        sid[sp["key"]] = i
        off += len(en)
    env = np.concatenate(env) if env else np.zeros(0, np.float32)
    # pieces
    pieces = []
    for p in parts:
        for q in p["_pieces"]:
            T_eeg, s = n64(q["T_native"], src.fs), sid[q["stream_key"]]
            T_env = rows[s]["length"]
            rec = {"piece_id": f"{cohort}:{p['participant']}:{q['trial']}", "participant": p["participant"], "uid": p["uid"],
                   "identity": p["identity"], "group": p["group"], "fold": p["fold"], "dev": p["dev"], "test_only": p["test_only"],
                   "trial": q["trial"], "kind": q["kind"], "stimulus": q["stimulus"], "ignored_stimulus": q["ignored_stimulus"],
                   "content_group": q["content_group"], "presentation": None, "presentation_key": q["presentation_key"],
                   "family": fam_id[q["family_name"]], "family_name": q["family_name"], "family_offset": q["family_offset"],
                   "family_basis": q["family_basis"], "stream": s,
                   "ignored_stream": sid[q["ignored_stream_key"]] if q["ignored_stream_key"] else None, "ignored_lead": q["ignored_lead"],
                   "attended_side": q["attended_side"], "onset_s": q["onset_s"], "condition": q["condition"], "role": q["role"],
                   "slab": q["role"], "row_offset": None, "T_eeg": T_eeg, "T_env": T_env, "T_native": q["T_native"],
                   "segment_starts": C.segment_starts(T_env, T_eeg, cohort, onset=q["onset_s"]).tolist(), "masked": list(p["masked"])}
            if q["kind"] == "cs":
                rec["segment_starts_guard_only"] = C.segment_starts(T_env, T_eeg, cohort).tolist()
            # §2.2: the onset rule serves "DTU target-stage evaluation, FAU in CSX only"; FAU's target stage keeps the guard rule
            rec["segment_starts_target_stage"] = rec["segment_starts_guard_only"] if q["kind"] == "cs" and cohort == "fau" \
                else rec["segment_starts"]
            for k, v in q["extra"].items():
                assert k not in rec, k
                rec[k] = v
            pieces.append(rec)
    # every target window of a competing-talker segment must lie inside the ignored stream's edge guards too
    short = []
    for q in pieces:
        if q["ignored_stream"] is None:
            continue
        L = rows[q["ignored_stream"]]["length"]
        for fld in ("segment_starts", "segment_starts_guard_only"):
            ss = q.get(fld) or []
            if ss and (ss[0] - q["ignored_lead"] < C.ENV_EDGE or ss[-1] + C.SPAN_ENV - q["ignored_lead"] > L - C.ENV_EDGE):
                short.append([q["piece_id"], fld, ss[0], ss[-1], L])
    if short:
        raise ValueError(f"{cohort}: ignored streams that do not cover the segments (piece, starts, first, last, length): {short[:5]}")
    rep = collections.defaultdict(list)
    for q in pieces:
        rep[(q["participant"], q["presentation_key"])].append(q["piece_id"])
    for q in pieces:
        q["own_repeat_pieces"] = [x for x in rep[(q["participant"], q["presentation_key"])] if x != q["piece_id"]]
    own_repeats = [{"participant": a, "presentation_key": k, "pieces": v} for (a, k), v in sorted(rep.items()) if len(v) > 1]
    order = sorted(range(len(pieces)), key=lambda i: (SLABS.index(pieces[i]["slab"]), i))
    off, slabs = 0, {}
    for i in order:
        q = pieces[i]
        q["row_offset"] = off
        a = slabs.setdefault(q["slab"], [off, off])
        off += q["T_eeg"]
        a[1] = off
    N = off
    # cohort-local registries
    keys = sorted({q["presentation_key"] for q in pieces})
    pid = {k: i for i, k in enumerate(keys)}
    by = collections.defaultdict(list)
    for q in pieces:
        q["presentation"] = pid[q["presentation_key"]]
        by[q["presentation_key"]].append(q)
    presentations = []
    for k in keys:
        q0 = by[k][0]
        for q in by[k][1:]:
            diff = [f for f in PRES_FIELDS if q[f] != q0[f]]
            if diff:
                raise ValueError(f"{cohort} presentation {k}: {q['piece_id']} differs from {q0['piece_id']} in {diff}")
        presentations.append({"id": pid[k], "key": k, "cohort": cohort, **{f: q0[f] for f in PRES_FIELDS},
                              "family": fam_id[q0["family_name"]], "offset_known": q0["family_offset"] is not None,
                              "n_listeners": len({q["participant"] for q in by[k]}), "n_pieces": len(by[k])})
    clock = {q["family_name"]: q["family_clock"] for p in parts for q in p["_pieces"]}
    families = [{"id": fam_id[f], "cohort": cohort, "name": f, "clock": clock.get(f, "known"),
                 "basis": next((q["family_basis"] for q in pieces if q["family_name"] == f), "own"),
                 "members": [pr["id"] for pr in presentations if pr["family_name"] == f]} for f in fams]
    table_parts = []
    for p in parts:
        r = {k: v for k, v in p.items() if not k.startswith("_")}
        r["n_pieces"] = len(p["_pieces"])
        table_parts.append(r)
    caches = {m: C.CACHE_FILE[m] for m in CACHE_MODE[cohort].values()}
    cohort_info = {"dir": cohort, "fs_native": src.fs, "n_ch": len(lay), "layout": list(lay), "reference": REFERENCE[cohort],
                   "band": BAND[cohort]["A"], "band_by_mode": BAND[cohort], "guards": list(C.GUARDS[cohort]),
                   "s_first": C.S_FIRST[cohort], "n_rows": N, "caches": caches, "table": TABLE, "items": "pieces", "env": ENV,
                   "streams": STREAMS, "role_slabs": slabs,
                   "masked_cells": int(sum(len(q["masked"]) for q in pieces)),
                   "filters": {"aa_fir": aa, "aa_taps": C.AA_TAPS.get(src.fs), "env_sos": C.env_sos()[1], "all": C.filter_shas()},
                   "resampling": f"contract.resample64: {src.fs} -> {C.FS} Hz, scipy.signal.resample_poly with h_aa",
                   "normalisation": {m: ("z per participant x channel over all of that participant's pieces at 64 Hz (guards "
                                         f"{list(C.GUARDS[cohort])} and masked cells excluded; masked channels 0)") if m in Z_MODES else
                                     "pre-z 64 Hz signal x factor_to_uV (uV); masked channels 0; no target statistics"
                                     for m in caches}, "signals": {CACHE_MODE[cohort][m]: SIGNAL[cohort][m] for m in MODES[cohort]},
                   "stats_band": {k: list(v) for k, v in STATS_BAND[cohort].items()},
                   "stats_band_2_8": "contract.band(x, env_sos) over each 64 Hz piece, then the z-statistics' SD (guards, masks)"}
    streams_doc = {"schema": SCHEMA_STREAMS, "contract": C.CONTRACT, "cohort": cohort, "id_space": ID_SPACE, "id_note": ID_NOTE,
                   "streams": rows}
    checks = src.checks(parts, pieces, info)
    assert not {"own_repeats", "ignored_stream_coverage"} & set(checks)
    checks.update(own_repeats=own_repeats, ignored_stream_coverage="every competing-talker segment's target windows lie within "
                  f"[{C.ENV_EDGE}, length - {C.ENV_EDGE}) of the ignored stream (checked; a violation raises)")
    core = {"schema": SCHEMA_PIECES, "contract": C.CONTRACT, "cohort": cohort, "id_space": ID_SPACE, "id_note": ID_NOTE,
            "builder_sha256": _code_sha(),
            "partial": participants is not None, "participants": table_parts, "pieces": pieces, "presentations": presentations,
            "families": families, "partner_exclusions": _partner_exclusions(cohort, parts),
            "excluded_trials": list(getattr(src, "excluded", [])), "unread_files": list(getattr(src, "unread", [])),
            "checks": checks, "cohort_info": cohort_info,
            "env_sha256": hashlib.sha256(env.tobytes()).hexdigest(), "streams_sha256": _sha_obj(streams_doc)}
    core["layout_sha256"] = _sha_obj(core)
    return {"core": core, "streams": streams_doc, "env": env, "parts": parts, "N": N, "n_ch": len(lay)}


# ---------------------------------------------------------------------------------------------------------- build
@contextlib.contextmanager
def cohort_lock(d):
    """One build per cohort directory: an exclusive non-blocking flock on <cohort>/.build.lock (released when the process ends)."""
    fh = open(os.path.join(d, LOCK), "a+")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        raise RuntimeError(f"another build holds {os.path.join(d, LOCK)}")
    try:
        fh.seek(0)
        fh.truncate()
        fh.write(json.dumps({"pid": os.getpid(), "host": os.uname().nodename, "slurm_job": os.environ.get("SLURM_JOB_ID")}))
        fh.flush()
        yield
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


def _partial(final):
    return final[:-4] + ".partial.npy"


def _marker(d, cm, participant):
    return os.path.join(d, DONE_DIR, cm, urllib.parse.quote(participant, safe="") + ".json")


def _install_layout(d, lay, log):
    """Write env_f32.npy, streams.json and pieces.json (layout only) or verify that the existing ones have the same layout."""
    core, path = lay["core"], os.path.join(d, TABLE)
    if os.path.exists(path):
        old = _read_json(path)
        if old.get("layout_sha256") != core["layout_sha256"]:
            raise RuntimeError(f"{path}: built with another layout (sha {old.get('layout_sha256')} != {core['layout_sha256']}; other "
                               "code, sources or participant set); move the cohort directory away before rebuilding")
        for f, sha in ((ENV, core["env_sha256"]), (STREAMS, core["streams_sha256"])):
            p = os.path.join(d, f)
            got = None if not os.path.exists(p) else (hashlib.sha256(np.load(p, allow_pickle=False).tobytes()).hexdigest() if f == ENV
                                                      else _sha_obj(_read_json(p)))
            if got != sha:
                raise RuntimeError(f"{p}: missing or not the file of layout {core['layout_sha256']}")
        log(f"{core['cohort']}: layout {core['layout_sha256'][:16]} already installed in {d}")
        return old
    _save_npy(os.path.join(d, ENV), lay["env"])
    _write_json(os.path.join(d, STREAMS), lay["streams"])
    table = {**core, "caches": {}, "unit": None, "unit_evidence": None, "mode_c": None}
    for p in table["participants"]:
        p.update({k: {} for k in ("mu", "sd_prez", "sd_prez_uV", "n_stat_samples", "median_prez_sd")}, source_sha256=None,
                 sd_prez_unit=None)
    _write_json(path, table)
    log(f"{core['cohort']}: layout {core['layout_sha256'][:16]} written: {len(core['participants'])} participants, "
        f"{len(core['pieces'])} pieces, {lay['N']} rows x {lay['n_ch']} ch, {len(lay['streams']['streams'])} streams")
    return table


def _open_partial(path, shape):
    if os.path.exists(path):
        mm = np.load(path, mmap_mode="r+", allow_pickle=False)
        if mm.shape != shape or mm.dtype != np.float16:
            raise RuntimeError(f"{path}: {mm.shape} {mm.dtype}, expected {shape} float16; move it away")
        return mm
    return np.lib.format.open_memmap(path, mode="w+", dtype=np.float16, shape=shape)


def _stat_rec(mu, sd, n, masked_idx, sd_band=None):
    """A participant's statistics of one signal: mu, sd (None where masked), n, median_sd over the unmasked channels; with
    sd_band also sd_2_8 / median_sd_2_8 (the same signal through the contract 2-8 Hz band-pass)."""
    m = set(masked_idx)

    def med(s):
        keep = [i for i in range(len(s)) if i not in m and np.isfinite(s[i]) and s[i] > 0]
        return float(np.median(s[keep])) if keep else None
    rec = {"mu": mu.tolist(), "sd": [float(v) if np.isfinite(v) else None for v in sd], "n": n.tolist(), "median_sd": med(sd)}
    if sd_band is not None:
        rec.update(sd_2_8=[float(v) if np.isfinite(v) else None for v in sd_band], median_sd_2_8=med(sd_band))
    return rec


def _drop_partial(st, log):
    """Remove this builder's own unfinalised partial file of a mode that is unsupported (it can never be finalised; §2.13: no
    cache, no mode-C row). Only the state's own <cohort>/<cache>.partial.npy is ever removed."""
    mm = st.pop("mm", None)
    del mm
    p = st["partial"]
    if p == _partial(st["final"]) and p.endswith(".partial.npy") and os.path.isfile(p):
        os.remove(p)
        log(f"mode {st['mode']} ({st['cm']}): removed its unfinalised {p}")


def _unsupported(d, st, reason, log):
    """Record (once, persistently) that a mode-C cache cannot be built: later jobs read _c5_done/<cm>/_unsupported.json. The
    mode's own partial file, if any, is removed."""
    st["unsupported"] = reason
    _write_json(os.path.join(d, DONE_DIR, st["cm"], "_unsupported.json"), {"cache_mode": st["cm"], "reason": reason})
    log(f"mode {st['mode']} ({st['cm']}): unsupported: {reason}")
    _drop_partial(st, log)


def _c_factor(d, st, p, rec, log):
    """Mode-C (factor_to_uV, source unit): the documented unit if any, else the magnitude rule on the first participant built
    (humans are built first; recorded in _c5_done/<cm>/_unit.json, so a resumed job keeps it). None when unsupported (recorded)."""
    path = os.path.join(d, DONE_DIR, st["cm"], "_unit.json")
    if os.path.exists(path):
        u = _read_json(path)
    else:
        dn, dbasis = st["documented"]
        mn, mdet = unit_from_magnitude([rec["median_sd"]])
        name = dn or mn
        if name is None:
            _unsupported(d, st, f"no documented unit and the magnitude rule gives none on the first participant "
                                f"{p['participant']} ({mdet})", log)
            return None
        u = {"source_unit": name, "factor_to_uV": UNIT_FACTOR[name], "documented": dn, "documented_basis": dbasis,
             "first_participant": p["participant"], "first_participant_test_only": bool(p["test_only"]),
             "first_participant_magnitude": {"unit": mn, **mdet}}
        _write_json(path, u)
    return u["factor_to_uV"], u["source_unit"]


def _build_caches(d, src, lay, modes, log):
    cohort, core = src.cohort, lay["core"]
    shape, lsha, bsha = (lay["N"], lay["n_ch"]), core["layout_sha256"], core["builder_sha256"]
    lay_names = C.MONTAGES[cohort]
    states = {}
    for m in modes:
        cm = CACHE_MODE[cohort][m]
        final = os.path.join(d, C.CACHE_FILE[cm])
        st = {"cm": cm, "mode": m, "signal": SIGNAL[cohort][m], "final": final, "partial": _partial(final), "done": final + ".done.json"}
        os.makedirs(os.path.join(d, DONE_DIR, cm), exist_ok=True)
        if os.path.exists(st["done"]):
            dj = _read_json(st["done"])
            if dj.get("layout_sha256") != lsha or dj.get("builder_sha256") != bsha:
                raise RuntimeError(f"{st['done']}: built for another layout or code version; move the cohort directory away")
            st["status"] = "done"
            log(f"{cohort} mode {m} ({cm}): already built")
        elif os.path.exists(final):
            if os.path.exists(st["partial"]):
                raise RuntimeError(f"{final} and {st['partial']} both exist without {os.path.basename(st['done'])}; move them away")
            st["status"] = "recover"           # renamed, then killed before its record was written: re-verified at the end
            if cm not in Z_MODES:
                st["documented"] = src.unit_documented()
            log(f"{cohort} mode {m} ({cm}): {final} has no record yet; it is re-verified")
        else:
            st["status"] = "building"          # the partial file is opened when the first rows are written (mode C: unit known)
            if cm not in Z_MODES:
                st["documented"] = src.unit_documented()
                un = os.path.join(d, DONE_DIR, cm, "_unsupported.json")
                if os.path.exists(un):
                    st["unsupported"] = _read_json(un)["reason"]
                    log(f"{cohort} mode {m} ({cm}): recorded as unsupported earlier: {st['unsupported']}")
                    _drop_partial(st, log)
        states[cm] = st
    building = [s for s in states.values() if s["status"] == "building"]
    by_id = {r["piece_id"]: r for r in core["pieces"]}
    sos = C.env_sos()[0]
    for p in sorted(lay["parts"], key=lambda p: bool(p["test_only"])):      # humans first: a mode-C unit is decided on a human
        midx = [lay_names.index(n) for n in p["masked"]]
        todo = []
        for st in building:
            if st.get("unsupported"):
                continue
            mk = _marker(d, st["cm"], p["participant"])
            if os.path.exists(mk):
                rec = _read_json(mk)
                if rec.get("layout_sha256") != lsha or rec.get("builder_sha256") != bsha:
                    raise RuntimeError(f"{mk}: written for another layout or code version")
                continue
            todo.append(st)
        if not todo:
            continue
        sigs = sorted({st["signal"] for st in todo})
        raw = src.read(p, sigs)
        x64 = {}
        for sg in sigs:
            arrs = []
            for q, a in zip(p["_pieces"], raw[sg]):
                if a.shape != (lay["n_ch"], q["T_native"]):
                    raise ValueError(f"{cohort}:{p['participant']}:{q['trial']}: {sg} shape {a.shape}, "
                                     f"expected {(lay['n_ch'], q['T_native'])}")
                if not np.isfinite(a).all():
                    raise ValueError(f"{cohort}:{p['participant']}:{q['trial']}: {int((~np.isfinite(a)).sum())} non-finite {sg} samples")
                y = C.resample64(a, src.fs)
                if y.shape[1] != n64(q["T_native"], src.fs):
                    raise AssertionError((y.shape, q["T_native"]))
                arrs.append(y)
            x64[sg] = arrs
        del raw
        stats = {}
        for sg in sigs:
            sd_b = zstats([C.band(x, sos) for x in x64[sg]], midx, C.GUARDS[cohort])[1] if sg in BAND_STAT[cohort] else None
            stats[sg] = _stat_rec(*zstats(x64[sg], midx, C.GUARDS[cohort]), midx, sd_band=sd_b)
        src_sha = _file_sha(p["source_file"])
        rows = [(q, by_id[f"{cohort}:{p['participant']}:{q['trial']}"]) for q in p["_pieces"]]
        for st in todo:
            sg, rec = st["signal"], stats[st["signal"]]
            own = None
            if st["cm"] in Z_MODES:
                mu, sd = np.asarray(rec["mu"], float), np.asarray([np.nan if v is None else v for v in rec["sd"]], float)
                blocks, unit = [zscore(x, mu, sd, midx) for x in x64[sg]], "z"
            else:
                fu = _c_factor(d, st, p, rec, log)
                if fu is None:
                    continue
                factor, src_unit = fu
                mn, mdet = unit_from_magnitude([rec["median_sd"]])
                own = {"unit": mn, "median_sd": rec["median_sd"], "in_cohort_band": mn == src_unit}
                if mn != src_unit and not p["test_only"]:          # UNIT_RULE: every human's own median in the cohort's band
                    _unsupported(d, st, f"{p['participant']}: median pre-z SD {rec['median_sd']} gives unit {mn}, the cohort's is "
                                        f"{src_unit} ({mdet})", log)
                    continue
                blocks, unit = [], "uV"
                for x in x64[sg]:
                    y = x * factor
                    y[midx] = 0.0
                    blocks.append(y)
            if "mm" not in st:
                st["mm"] = _open_partial(st["partial"], shape)
            h = hashlib.sha256()
            mx, nclip, pre_max = 0.0, 0, 0.0
            for (q, r), b in zip(rows, blocks):
                if st["cm"] not in Z_MODES:                        # lead 2026-10-17: raw-uV values beyond the float16 range (artefacts,
                    over = np.abs(b) > F16_CLIP_UV                    # > 65 mV, first seen fau:221 trial_17 at 7.7e4 uV) are clipped to
                    if over.any():                                    # +-F16_CLIP_UV and counted per participant; NaN still fails
                        nclip += int(over.sum()); pre_max = max(pre_max, float(np.nanmax(np.abs(b))))
                        b = np.clip(b, -F16_CLIP_UV, F16_CLIP_UV)
                b16 = np.ascontiguousarray(b.T.astype(np.float16))
                if not np.isfinite(b16).all():
                    raise ValueError(f"{r['piece_id']}: non-finite float16 values in mode {st['cm']} (|x| max {np.abs(b).max():.4g})")
                st["mm"][r["row_offset"]:r["row_offset"] + r["T_eeg"]] = b16
                h.update(b16.tobytes())
                mx = max(mx, float(np.abs(b16.astype(np.float32)).max()) if b16.size else 0.0)
            st["mm"].flush()
            mrec = {"participant": p["participant"], "cache_mode": st["cm"], "signal": sg, "unit": unit, "layout_sha256": lsha,
                    "builder_sha256": bsha, "stats": rec, "block_sha256": h.hexdigest(), "max_abs": mx, "source_sha256": src_sha,
                    "rows": [[r["row_offset"], r["T_eeg"]] for _, r in rows]}
            if own is not None:
                mrec.update(test_only=bool(p["test_only"]), own_magnitude=own)
            if st["cm"] not in Z_MODES:
                mrec.update(clip_abs_uV=F16_CLIP_UV, clipped_samples=nclip, max_abs_before_clip=pre_max if nclip else None)
                if nclip:
                    log(f"{cohort}:{p['participant']}: mode {st['cm']}: {nclip} samples beyond +-{F16_CLIP_UV:g} uV clipped (max {pre_max:.4g})")
            _write_json(_marker(d, st["cm"], p["participant"]), mrec)
        log(f"{cohort}:{p['participant']}: {len(p['_pieces'])} pieces -> {', '.join(st['cm'] for st in todo)}")
        del x64
    return states


def _finalise_cache(st, core, unit, log):
    """Full NaN / Inf scan, sha256, rename the partial file to its final name and write <file>.done.json. A 'recover' state (the
    final file exists, its record does not) is scanned and hashed in place."""
    recover = st["status"] == "recover"
    path = st["final"] if recover else st["partial"]
    mm = None if recover else st.pop("mm", None)
    if mm is not None:
        mm.flush()
    else:                                   # recover, or every participant was written by an earlier job
        if not os.path.isfile(path):
            raise RuntimeError(f"{path}: missing although every participant has a marker; move the cohort directory away")
        mm = np.load(path, mmap_mode="r", allow_pickle=False)
    if mm.shape != (core["cohort_info"]["n_rows"], core["cohort_info"]["n_ch"]) or mm.dtype != np.float16:
        raise RuntimeError(f"{path}: {mm.shape} {mm.dtype} is not this layout's cache")
    bad, step = 0, 1 << 18
    for a in range(0, mm.shape[0], step):
        bad += int(np.count_nonzero(~np.isfinite(np.asarray(mm[a:a + step]))))
    del mm
    if bad:
        raise RuntimeError(f"{path}: {bad} non-finite values")
    sha = _file_sha(path)
    if not recover:
        os.replace(st["partial"], st["final"])
    rec = {"schema": SCHEMA_DONE, "cohort": core["cohort"], "cache_mode": st["cm"], "file": os.path.basename(st["final"]),
           "signal": st["signal"], "sha256": sha, "shape": [core["cohort_info"]["n_rows"], core["cohort_info"]["n_ch"]],
           "dtype": "float16", "layout": "time-major [N, C], rows in role slabs", "layout_sha256": core["layout_sha256"],
           "builder_sha256": core["builder_sha256"], "nonfinite": 0,
           "unit": "z (per participant x channel)" if st["cm"] in Z_MODES else "uV",
           "unit_record": None if st["cm"] in Z_MODES else unit, "normalisation": core["cohort_info"]["normalisation"][st["cm"]],
           "band": BAND[core["cohort"]][st["cm"]]}
    _write_json(st["done"], rec)
    log(f"{core['cohort']} {st['cm']}: {st['final']} sha256 {sha[:16]}")
    return rec


def _participant_stats(d, core, cms):
    """{participant: {signal: (marker stats, source sha)}} from every cache mode's markers (identical across modes of a signal)."""
    out = collections.defaultdict(dict)
    for cm in cms:
        for p in core["participants"]:
            mk = _marker(d, cm, p["participant"])
            if not os.path.exists(mk):
                continue
            r = _read_json(mk)
            if r.get("layout_sha256") != core["layout_sha256"]:
                continue
            prev = out[p["participant"]].get(r["signal"])
            if prev is not None and (prev[0] != r["stats"] or prev[1] != r["source_sha256"]):
                raise RuntimeError(f"{p['participant']}: signal {r['signal']} statistics or source sha differ between cache modes")
            out[p["participant"]][r["signal"]] = (r["stats"], r["source_sha256"])
    return out


def build(cohort, modes, out, participants=None, log=_log):
    """Build the requested modes of one cohort under <out>/<cohort>/ (module docstring). Returns a summary dict."""
    modes = parse_modes(cohort, modes)
    src = SOURCES[cohort]()
    lay = plan(src, participants)
    core = lay["core"]
    d = os.path.join(out, cohort)
    os.makedirs(d, exist_ok=True)
    with cohort_lock(d):
        table = _install_layout(d, lay, log)
        states = _build_caches(d, src, lay, modes, log)
        all_cms = list(CACHE_MODE[cohort].values())
        stats = _participant_stats(d, core, all_cms)
        csig = SIGNAL[cohort]["C"]
        sig_for_unit = csig if any(csig in v for v in stats.values()) else next((s for v in stats.values() for s in sorted(v)), None)
        test_only = {p["participant"] for p in core["participants"] if p["test_only"]}
        have = [pid for pid in sorted(stats) if sig_for_unit in stats[pid]]
        ev = [pid for pid in have if pid not in test_only] or have          # humans; test_only only when nothing else is built
        sds = [x for pid in ev for x in stats[pid][sig_for_unit][0]["sd"] if x is not None]
        unit = decide_unit(src.unit_documented(), unit_from_magnitude(sds)) if sig_for_unit else None
        own_med = {pid: stats[pid][sig_for_unit][0]["median_sd"] for pid in have}
        if unit is not None:
            unit["signal"] = sig_for_unit
            unit["evidence"] = "human (non-test_only) participants" if set(ev) - test_only else "test_only participants only"
            other = sorted(pid for pid in ev if own_med[pid] is not None
                           and unit_from_magnitude([own_med[pid]])[0] != unit.get("source_unit"))
            unit["participant_medians"] = {"n": len(ev), "min": min((own_med[p] for p in ev if own_med[p] is not None), default=None),
                                           "max": max((own_med[p] for p in ev if own_med[p] is not None), default=None),
                                           "other_unit": other}
            if unit["supported"] and other:                               # UNIT_RULE: every human's own median in the band
                unit.pop("basis", None)
                unit.update(supported=False, name=None, source_unit=None, factor_to_uV=None,
                            reason=f"participants whose own median pre-z SD gives another unit than the cohort's: {other}")
        for st in states.values():
            if st["status"] not in ("building", "recover"):
                continue
            missing = [p["participant"] for p in core["participants"] if not os.path.exists(_marker(d, st["cm"], p["participant"]))]
            if st["cm"] not in Z_MODES:
                used = os.path.join(d, DONE_DIR, st["cm"], "_unit.json")
                used = _read_json(used) if os.path.exists(used) else None
                if not st.get("unsupported") and not missing and (unit is None or not unit["supported"] or used is None
                                                                  or used["source_unit"] != unit["source_unit"]):
                    _unsupported(d, st, f"cohort unit record disagrees: {unit and (unit.get('reason') or unit.get('source_unit'))} "
                                        f"(cache written as {used and used['source_unit']})", log)
                if st.get("unsupported"):
                    st["status"] = "unsupported"
                    _drop_partial(st, log)
                    log(f"{cohort} mode {st['mode']} ({st['cm']}): not finalised: {st['unsupported']}")
                    continue
            if missing:
                raise RuntimeError(f"{cohort} {st['cm']}: participants without a marker: {missing}")
            st["record"] = _finalise_cache(st, core, unit, log)
            st["status"] = "done"
        # pieces.json: statistics, caches, unit, mode C
        fac = unit["factor_to_uV"] if unit and unit["supported"] else None
        for p in table["participants"]:
            per = stats.get(p["participant"], {})
            p["sd_prez_unit"] = unit.get("source_unit") if unit and unit["supported"] else None
            for sg, (rec, ssha) in per.items():
                k = STAT_KEY[cohort][sg]
                p["mu"][k], p["sd_prez"][k] = rec["mu"], rec["sd"]
                p["n_stat_samples"][k], p["median_prez_sd"][k] = rec["n"], rec["median_sd"]
                p["sd_prez_uV"][k] = None if fac is None else [None if v is None else v * fac for v in rec["sd"]]
                if "sd_2_8" in rec:
                    kb = k + BAND_SUFFIX
                    p["sd_prez"][kb], p["median_prez_sd"][kb], p["n_stat_samples"][kb] = rec["sd_2_8"], rec["median_sd_2_8"], rec["n"]
                    p["sd_prez_uV"][kb] = None if fac is None else [None if v is None else v * fac for v in rec["sd_2_8"]]
                p["source_sha256"] = ssha
        for cm in all_cms:
            done = os.path.join(d, C.CACHE_FILE[cm]) + ".done.json"
            if os.path.exists(done):
                table["caches"][cm] = _read_json(done)
        cmode = CACHE_MODE[cohort]["C"]
        un = os.path.join(d, DONE_DIR, cmode, "_unsupported.json")
        c_reason = _read_json(un)["reason"] if os.path.exists(un) else None
        if c_reason is None and not (unit and unit["supported"]):
            c_reason = unit.get("reason") if unit else "no statistics yet"
        table["unit"] = unit
        table["cohort_info"]["unit"] = {"name": "uV" if fac else None, "source_unit": unit and unit.get("source_unit"),
                                        "factor_to_uV": fac, "basis": unit and (unit.get("basis") or unit.get("reason"))}
        table["unit_evidence"] = {"signal": sig_for_unit, "median_prez_sd": unit["magnitude"].get("median") if unit else None,
                                  "n_values": len(sds), "participants": unit and unit.get("evidence"),
                                  "note": "median over the human participants x unmasked channels, source unit",
                                  "test_only": {pid: {"median_prez_sd": own_med[pid],
                                                      "magnitude_unit": unit_from_magnitude([own_med[pid]])[0],
                                                      "in_cohort_band": unit_from_magnitude([own_med[pid]])[0] == (unit or {}).get("source_unit")}
                                                for pid in have if pid in test_only}}
        table["mode_c"] = {"mode": cmode, "file": C.CACHE_FILE[cmode], "built": cmode in table["caches"],
                           "supported": c_reason is None, "reason": c_reason, "zero_shot_mode": C.ZS_MODE_NAME[cmode]}
        _write_json(os.path.join(d, TABLE), table)
    summary = {"cohort": cohort, "out": d, "modes": list(modes), "layout_sha256": core["layout_sha256"], "partial": core["partial"],
               "n_participants": len(core["participants"]), "n_pieces": len(core["pieces"]), "n_rows": lay["N"],
               "caches": {cm: st["status"] for cm, st in states.items()}, "unit": table["cohort_info"]["unit"], "mode_c": table["mode_c"]}
    log(json.dumps(_clean(summary), sort_keys=True))
    return summary


# ---------------------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m auditory_alignment_v3.prior33.build_public", description=__doc__.split("\n")[0])
    ap.add_argument("--cohort", required=True, choices=COHORTS + ("all",),
                    help="one cohort, or 'all' (fau, dtu, federici in sequence, with --mode all: one CPU job for C5)")
    ap.add_argument("--mode", required=True, help="A, B or C, a comma list (A,B,C) or 'all' (B: FAU only; Federici C = C_partial)")
    ap.add_argument("--out", default=CACHE_ROOT, help="cache root (the §6.2 contract directory); outputs go to <out>/<cohort>/")
    ap.add_argument("--allow-other-out", action="store_true", help="permit an --out other than the §6.2 cache root (dry runs)")
    ap.add_argument("--participants", default=None, help="comma-separated participant ids: a partial dry-run build")
    a = ap.parse_args(argv)
    cohorts = COHORTS if a.cohort == "all" else (a.cohort,)
    if a.cohort == "all" and (a.mode.strip().lower() != "all" or a.participants is not None):
        ap.error("--cohort all needs --mode all and no --participants")
    try:
        modes = {c: parse_modes(c, a.mode) for c in cohorts}
    except ValueError as e:
        ap.error(str(e))
    root = os.path.realpath(CACHE_ROOT)
    out = os.path.realpath(a.out)
    if out != root and not a.allow_other_out:
        ap.error(f"--out {a.out} is not the cache root {CACHE_ROOT}; pass --allow-other-out for a dry run")
    parts = None if a.participants is None else [s for s in a.participants.split(",") if s]
    if parts is not None and out == root:
        ap.error("a partial build (--participants) never goes to the cache root")
    for c in cohorts:
        build(c, modes[c], out, participants=parts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
