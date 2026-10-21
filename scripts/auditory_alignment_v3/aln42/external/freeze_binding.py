"""Freeze EXTERNAL_COMPARISON_BINDING.json (template fields) before any external test score, plus a public-safe copy
(private paths withheld, no person lists). Refuses to overwrite an existing frozen binding."""
import hashlib, json, os, re, sys
from datetime import datetime

E = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(E, '../../../..'))
OUT = os.path.join(E, 'EXTERNAL_COMPARISON_BINDING.json')
PUB = os.path.join(REPO, 'docs/auditory_alignment_v3/aln42/EXTERNAL_COMPARISON_BINDING.public.json')
assert not os.path.exists(OUT), 'binding already frozen'
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
units = json.load(open(os.path.join(E, 'PUBLIC_UNITS.json')))
q = json.load(open(os.path.join(E, 'COMMON_Q_MANIFEST.json')))
au = json.load(open(os.path.join(E, 'AUDIO_VERSION_EVIDENCE.json')))['by_cf']
ev = lambda cf, key: round(au[cf]['summary'][key]['median'], 4)
mm = '/projects/EEG-foundation-model/auditory_public/foundation_models/github__CookieMikeLiu__MindMix@98445f3/repo'

B = {
 'template_only': False,
 'frozen': True,
 'frozen_at': datetime.now().astimezone().isoformat(),
 'freeze_before_new_external_test_scores': True,
 'no_external_test_score_existed_at_freeze': True,
 'template_sha256': '9a588b7591ef5c643ce1bae1f5c24440f940227e3eb768199eb6a9ec7fca82f4',
 'contract_sha256': {'docs/06_EXTERNAL_COMPARISON_AND_CLOSURE.md': '4d2f59e4a6be63fc54af059fd1ab7330ff6c877be2ee05b34e9f0c905e63eea1',
                     'plans/round3_closure.json': '8fbb89eb8bc54373ca6bc2abd6c5267d1c8ba62436887524a9d3e86a0ba2ab3b'},
 'original_decision_sha256': '5e78e2aa14dedc772a1fbc427923875e5e108757e56f5b5fe0380b5314989e40',
 'original_decision_date': '2026-10-21T02:21:24.768547+02:00',
 'original_decision_path': 'private/auditory_alignment_v3/aln41/intake/EXTERNAL_SLOT_DECISION.json',
 'route': 'A_MindMix (pre-registered rule: all readiness gates passed in ~50 min of the 4 h bound; coordinator confirmed 2026-10-21)',
 'display_name': 'MindMix released full architecture, common-protocol task adaptation',
 'official_repo_commit': '98445f368efcb161c638172501bd16f92d09a89d',
 'weight_sha256': {'pretrain_fusion_checkpoints/best_model_loss_0.0909.pth': 'fe2603e3ee2c95fa2e1e012710a2774e70b6dd5582560773aafd20b295f15026',
                   'bytes': 1221696491,
                   'local_path': '/projects/EEG-foundation-model/auditory_public/foundation_models/github__CookieMikeLiu__MindMix@98445f3/lfs/best_model_loss_0.0909.pth',
                   'facebook/wav2vec2-base@0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8/pytorch_model.bin (instantiation only; all audio tensors overwritten from the fusion checkpoint)':
                       '3249fe98bfc62fcbc26067f724716a6ec49d12c4728a2af1df659013905dff21'},
 'config_sha256': {**{f: sha(os.path.join(mm, f)) for f in ('universal_eeg_finetune.py', 'universal_models.py', 'universal_trainer.py',
                                                           'modeling_finetune_2.py', 'utils.py', 'README.md')},
                   'wav2vec2-base/config.json': '4937977e24d12d1bba70cdce8709c3c04807a8e4ae8ddac4229c48c436ae99ae',
                   'argv': 'official get_args() with --dataset DTU --strategy multimodal_real --fusion_method calra --pretrained_model <fusion ckpt> '
                           '--batch_size 32 --epochs 50 --lr 1e-05 --weight_decay 0.01 --seed 3401 (all other args = pinned defaults)',
                   'environment': 'eeg2025 env: torch 2.6.0+cu124, transformers 5.2.0, timm 1.0.25; fp32, PyTorch default TF32 settings'},
 'loaded_modules': 'all EEG / wav2vec2 / eeg_proj / audio_proj / CALRA tensors (509 of 511; asserted at every start); classifier.* (unused by the AAD path) '
                   'and clip_loss.logit_scale (not saved; ln(1/0.07)) are not from the checkpoint; wav2vec2 pos-conv weight_g/weight_v loaded by '
                   'a pure key rename to parametrizations.weight.original0/1 (bit-identical)',
 'pretraining_data_overlap_status': 'No declared overlap: DTU44 (zenodo 3618205) participants/recordings are in none of the Stage-1 (BCI-IV-2A, HGD, '
     'OpenBMI, EEGMat, TUEP, TUEV, HMCSleep, CAPSleep, CMBMIT) or Stage-2 (ds004356, zenodo 4518754, zenodo 10260082, Brennan 2018, Broderick 2018, '
     'Le Petit Prince) corpora of paper Table 1 / App. A.1; Danish audiobook content is not among the described Stage-2 stimuli; waveform-level '
     'overlap not verified; wav2vec2-base pretrained on LibriSpeech (English).',
 'dataset_doi': '10.5281/zenodo.3618205',
 'raw_audio_available': True,
 'raw_audio_provenance_and_alignment_private': {
     'provenance': 'DRCMR raw stimulus audio (dtu_snhl/audio_drcmr/DOWNLOAD_RECEIPT.json; research use, access-controlled, no redistribution)',
     'version_decision': 'per stream the inventory waveform used by the core3 pipeline: HI listeners -> stimuli-woa/<..>woa.wav (no CamEQ), '
                         'NH listeners -> stimuli/<..>.wav; the inventory sha256 (mono int16) is asserted when the 16 kHz cache is built',
     'version_evidence': {
         'file': 'AUDIO_VERSION_EVIDENCE.json', 'sha256': sha(os.path.join(E, 'AUDIO_VERSION_EVIDENCE.json')),
         'scope': 'content role fit only (cf0 and cf1 separately), 2 two-talker trials per person (44 people), every 5 s segment; no EEG read',
         'core3_envelope': 'dtu_cf{cf}.h5 Local[5] = 1-8 Hz band-passed 128 Hz Hilbert envelope of the inventory waveform (prep_targets.run_dtu_audio/run_dtu); '
                           'the derivative .mat envelopes are not used by core3',
         'HI_vs_core3_median_r': {'woa(stimuli-woa)': [ev('0', 'hi|target|woa(stimuli-woa)|vs_core3_Local5'), ev('0', 'hi|masker|woa(stimuli-woa)|vs_core3_Local5')],
                                  'CamEQ(plain)': [ev('0', 'hi|target|plain|vs_core3_Local5'), ev('0', 'hi|masker|plain|vs_core3_Local5')],
                                  'note': '[target, masker], cf0; cf1 the same pattern; woa(stimuli-woa) sha == core3 sha in 100% of streams, CamEQ in 0%'},
         'HI_vs_official_derivative_median_r': {'woa vs t.mat': [ev('0', 'hi|target|woa(stimuli-woa)|vs_derivative'), ev('1', 'hi|target|woa(stimuli-woa)|vs_derivative')],
                                                'CamEQ vs t.mat': [ev('0', 'hi|target|plain|vs_derivative'), ev('1', 'hi|target|plain|vs_derivative')],
                                                'woa vs twoa.mat': [ev('0', 'hi|target|woa(stimuli-woa)|vs_derivative_woa'), ev('1', 'hi|target|woa(stimuli-woa)|vs_derivative_woa')],
                                                'CamEQ vs twoa.mat': [ev('0', 'hi|target|plain|vs_derivative_woa'), ev('1', 'hi|target|plain|vs_derivative_woa')],
                                                'note': 'targets [cf0, cf1]; maskers same ordering (woa 0.76-0.82 vs CamEQ 0.28-0.45)'},
         'NH': 'plain sha == core3 sha in 100% of streams (r = 1.0000); only one version exists',
         'woa_copies': "stimuli/<..>woa.wav differs slightly from stimuli-woa/<..>woa.wav (r 0.99996, sha differs); stimuli/<..>woacontrol.wav is sha-identical "
                       "to the stimuli-woa file; the stimuli-woa file (inventory) is used"},
     'format': '44.1 kHz 2-channel (same talker lateralised); mono = L/R mean; resample_poly(160, 441) -> 16 kHz float32',
     'identity': 'target = targetonset stim_file, masker = maskeronset stim_file of the trial (c3_features_v1/dtu/inventory.json)',
     'onset_alignment': 'target wav sample 0 = targetonset; masker wav sample 0 = maskeronset (= inventory offset_s = masker_onset_rel_s); '
                        'verified on 8 streams against the official derivative envelopes (READINESS_REPORT.md section 3)'},
 'channels_reference_units_mapping_sha256': '8f063074ad54d2cd9e60daa936cd8678d57d8bfdde80bfd8b04c99d98e0b7aae',
 'channels_reference_units_mapping_file': 'CHANNEL_CONTRACT.json',
 'preprocessing_and_input_access': {
     'eeg_channels': 'first 64 channels.tsv rows of type eeg (BioSemi scalp, recorded order == MindMix ch_names; asserted); EXG1-8 and Status excluded',
     'reference': 'recorded BioSemi CMS/DRL, no re-referencing (same as the core3 c3_preproc_v1 EEG; paper A.2 applies no re-reference beyond the dataset)',
     'units': 'uV (x1e6) before filtering; immaterial after the per-window z-score',
     'filter': 'scipy.signal.butter(N=4, Wn=[1, 40] Hz, btype=bandpass, fs=512, output=sos) applied zero-phase with scipy.signal.sosfiltfilt '
               '(forward-backward, default odd padding) over the whole continuous selective-attention run (paper A.2 "zero-phase 4th-order Butterworth")',
     'resampling': 'scipy.signal.resample_poly(up=25, down=64) of the filtered continuous run (512 -> 200 Hz); trial time 0 = round(onset_s*512)/512 s',
     'eeg_window': '2 s = 400 samples at 200 Hz -> official rearrange to [64, 2, 200]; per-window per-channel z-score (x - mean) / (std + 1e-8)',
     'audio_window': '2 s = 32000 samples of the 16 kHz stream at the same trial time (masker index = time - masker onset); divided by max(|x|.max(), 1e-8)',
     'access': 'only the 5 s physical cs segment of each window (all three sub-windows lie inside it); the zero-phase filter over the continuous run '
               'is the same access pattern as the core3 preprocessing; training reads train people role=fit segments only'},
 'scorer_formula': 's(x|t) = exp(logit_scale) * cos(fused_eeg(eeg, t), aligned_audio(eeg, x)) from the official MultimodalRealModel.forward_contrastive '
                   '(eval mode, no grad), per-sample row diagonal (no in-batch softmax); m(c1, c2) = 1/2[(s(c1|c1) - s(c2|c1)) - (s(c2|c2) - s(c1|c2))] '
                   'from two official calls (c1 then c2 in the target slot); candidate order c1 < c2 by waveform sha256 (label-free); segment margin = '
                   'mean of the three sub-window margins; orientation to attended-minus-ignored applied only after scoring; ties credit 0.5 in the 20 s '
                   'mean-score readout',
 'scoring_batch_rule': 'fixed batches of 32 windows in cs-list order x sub-window order (deterministic), eval mode, torch.no_grad, cudnn deterministic',
 'candidate_swap_check': 'readiness: max|m(c1,c2)+m(c2,c1)| = 0.0 (synthetic 6, real training-side 16); production: asserted < 1e-3 on the first batch of every unit',
 'batch_invariance_check': 'readiness: <= 2.9e-6 (batch 1 vs full, permuted, with unrelated samples; 0 decision flips); production: first 4 windows alone vs in batch asserted < 1e-2',
 'true_label_hidden_until_evaluation_check': 'the scorer receives (eeg, c1, c2) ordered by waveform sha; attended identity used only to orient the stored margin after scoring',
 'native_subwindow_geometry': 'three 2 s sub-windows starting at +0.0, +1.5 and +3.0 s of each 5 s physical segment (cover [0, 5) s; 0.5 s overlaps); '
                              'segment margin = mean of the three blind sub-window margins; no offset search',
 'common_query_manifest_sha256': sha(os.path.join(E, 'COMMON_Q_MANIFEST.json')),
 'common_query_manifest': {'file': 'COMMON_Q_MANIFEST.json', 'rows': q['n'], 'rows_digest_sha256': q['sha256_of_rows'],
                           'definition': 'per unit: cs segments of the frozen B0 DTU unit arrays (core3 attention list) of test people (readout.public rule) with role test; '
                                         'every test-role cs segment occurs in exactly one unit'},
 'valid_coverage_rule_frozen_before_scores': 'every Q segment is scored (sub-windows inside the segment; segment start >= masker onset + 1.7 s so masker '
                                             'audio exists; window ranges asserted in code); a segment failing an assertion stops the unit (no silent exclusion); '
                                             'if any Q segment ever lacked a margin, all core3 methods would be recomputed on the same reduced Q',
 'content_folds': [0, 1],
 'person_folds': [0, 1, 2, 3, 4],
 'downstream_seed': 3401,
 'actual_public_units': [{k: u[k] for k in ('id', 'content_fold', 'person_fold', 'n_fit_segments', 'n_es_segments', 'n_query_segments',
                                            'train_windows', 'score_windows')} | {'n_train_people': len(u['train_people']), 'n_test_people': len(u['test_people'])}
                         for u in units],
 'actual_public_units_file': {'file': 'PUBLIC_UNITS.json', 'sha256': sha(os.path.join(E, 'PUBLIC_UNITS.json')),
                              'people_rule': 'train = auditory_alignment_v2.train.train_participants (= frozen meta pca[sf].train_people); test = ss-anchor people with fold == sf, not dev'},
 'public_fit_cap': 10,
 'source_pretraining_fits': 0,
 'private_external_ft_fits': 0,
 'training_recipe': {
     'source': 'README fine-tune table / public CLI = pinned code defaults', 'strategy': 'multimodal_real', 'fusion_method': 'calra',
     'init': 'released fusion checkpoint (all EEG/audio/projection/CALRA tensors)', 'batch_size': 32, 'epochs': 50, 'lr': 1e-05, 'weight_decay': 0.01,
     'optimizer': 'official setup_optimizer: AdamW(all params, betas (0.9, 0.95), eps 1e-8), no clipping',
     'scheduler': 'official: LinearLR warmup 3 epochs 1e-6 -> 1e-5, CosineAnnealingLR T_max 47, eta_min 1e-7, stepped once per epoch',
     'loop': 'official MultimodalRealTrainer.train_epoch + update_learning_rate for 50 epochs (trainer.train() not used: it evaluates the non-blind scorer on the evaluated fold and early-stops)',
     'loss': 'official ClipLoss(fused_eeg, aligned_audio), in-batch negatives; negative_audio unused by the loss',
     'training_data': "train people's role=fit cs segments only, 3 sub-windows each, target_audio = attended stream; role=es is never used for training or "
                      'selection (es and fit margins are produced only for the training-side tau of the 20 s mean-score readout); single-talker trials not used',
     'batch_composition': 'person-homogeneous batches of 32 (paper App. A.3; the code trains per subject): per epoch each training person\'s windows are '
                          'permuted with numpy default_rng([3401, epoch]), cut into batches of 32 (last partial batch kept), then the batch order is permuted '
                          'with the same generator',
     'seed': 3401, 'precision': 'fp32', 'resume': 'state saved every 5 epochs; the final model is the epoch-50 state'},
 'checkpoint_selection_rule': 'fixed final epoch 50; no selection on es or test (the code selects on the evaluated fold; the paper rule is unspecified)',
 'readout_solver': 'not applicable (route A); 20 s mean-score integration with tau fitted on training-side (fit + es) windows exactly as readout.attention, double order',
 'author_protocol_differences': [
     'within-subject random-window protocol on DTU18 (paper/code) -> pooled person-held-out DTU44, 2 content x 5 person folds, 20 s decisions',
     'official privileged-slot batch-softmax AAD scorer -> blind order-symmetrised per-sample margin (official scorer picks slot 1 in both orders for noise inputs)',
     'checkpoint: final epoch 50 instead of best-on-evaluated-fold / early stopping',
     'README/CLI recipe (batch 32, wd 0.01, warmup 3); paper A.3 text: batch 64, wd 0.05, warmup 10 (Table A2: wd 0.01, warmup 3); not run',
     'paper eq. (1) spatial embedding absent in pinned code and released weights',
     'wav2vec2 pos-conv tensors loaded by a pure key rename (torch>=2.1 parametrized weight_norm)',
     'clip_loss.logit_scale not in the checkpoint (init ln(1/0.07))',
     'person-homogeneous batches across all training people (one model per unit, not per subject)',
     'HI candidates use no-CamEQ (woa) audio although HI listeners heard CamEQ audio (= the waveform behind the core3 envelopes)',
     'recorded CMS reference; authors\' DTU18 reference undocumented',
     'candidate audio visible at test (candidate-matching setting)',
     'one released checkpoint, downstream seed 3401 (code default 42)'],
 'readiness_disclosures': {
     'objective_shortcut': 'released weights: official ClipLoss 0.0087 (attended), 0.0049 (ignored stream as target), 0.0087 (noise EEG), top-1 1.0; '
                           'without CALRA 3.26 (chance) -- DIAG_SHORTCUT_FLOPS.json',
     'eeg_sensitivity_at_release': 'blind margin real vs noise EEG r = 0.997 -- DIAG_EEG_SENSITIVITY.json'},
 'estimated_gpu_hours': {'basis': 'measured 130.1 GFLOP per training window, 113.9 GFLOP per scored window; windows per unit in actual_public_units',
                         'per_unit': 'cf0 ~1.4-2.2, cf1 ~1.9-2.9 GPU-h on A100/A40 fp32 (L40S faster); + ~0.5 h one-time input cache if not prepared',
                         'total_10_units': '~17-26 GPU-h (to be replaced by the smoke projection)', 'gpu_memory': '<= ~12 GB at batch 32 fp32'},
 'actual_gpu_hours': None,
 'readiness_result': 'PASS (4 pre-registered gates + blind-scorer gate); READINESS_REPORT.md',
 'readiness_evidence': {f: sha(os.path.join(E, f)) for f in ('READINESS_REPORT.md', 'GATE2_KEY_AUDIT.json', 'GATE345_RESULTS.json', 'GATE3_OFFICIAL_LOADER.json',
                                                            'DIAG_SHORTCUT_FLOPS.json', 'DIAG_EEG_SENSITIVITY.json', 'AUDIO_VERSION_EVIDENCE.json',
                                                            'DRYRUN_MODULE_CPU.json', 'COMMON_Q_MANIFEST.json', 'PUBLIC_UNITS.json', 'CHANNEL_CONTRACT.json',
                                                            'FETCH_FUSION_RECEIPT.json', 'FETCH_WAV2VEC2_RECEIPT.json')},
 'production_code': {'module': 'auditory_alignment_v3/aln42/external_mindmix.py', 'sbatch': 'slurm/aln35_aln42_external.sbatch',
                     'note': 'module and plan hashes are recorded in the plan (plan.binding_sha256 = sha256 of this file)'},
 'output_contract': 'per unit margins.npz: cs_person, cs_code, cs_e0, cs_role (== frozen B0 DTU unit arrays of that cf), margin (attended-minus-ignored, '
                    'NaN where not scored), margin_subwindows, margin_unoriented, first_is_attended, scored in {train_side, test, ""}',
}
with open(OUT, 'w') as f:
    json.dump(B, f, indent=1)
os.chmod(OUT, 0o400)


def scrub(v):
    if isinstance(v, dict):
        return {k: scrub(x) for k, x in v.items() if k not in ('local_path', 'original_decision_path')}
    if isinstance(v, list):
        return [scrub(x) for x in v]
    if isinstance(v, str):
        return re.sub(r'(/projects/\S+|/home/\S+)', '<server path withheld>', v)
    return v


P = scrub(B)
P['public_copy_of'] = {'file': 'EXTERNAL_COMPARISON_BINDING.json (server-private)', 'sha256': sha(OUT)}
P['raw_audio_provenance_and_alignment_private'] = {k: v for k, v in P['raw_audio_provenance_and_alignment_private'].items() if k != 'provenance'}
P['raw_audio_provenance_and_alignment_private']['provenance'] = 'raw stimulus audio obtained from the dataset authors on request (not redistributed)'
os.makedirs(os.path.dirname(PUB), exist_ok=True)
with open(PUB, 'w') as f:
    json.dump(P, f, indent=1)
print('frozen', sha(OUT)); print('public', sha(PUB))
assert '/projects/' not in open(PUB).read() and '/home/' not in open(PUB).read()
