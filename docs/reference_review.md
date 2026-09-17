> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# Reference review

This review is based only on the extracted text in `private/supporting_001/` and the file-to-title map in `private/reference_names.json`. The papers are treated as methodological or provenance clues. Their stimulus, timing, device, and participant parameters must not be transferred to this dataset without direct evidence from the acquisition files.

### `file_925cacb320a9ceee4a454edc60444bb2` — *Speech-induced suppression during natural dialogues*

This study concerns natural, unscripted dialogue rather than pediatric auditory evoked potentials. It used paired adult participants, dual 128-channel BioSemi recordings at 1024 Hz, synchronized microphone audio, manual inter-pausal-unit alignment, and continuous speech envelope or mel-spectrogram models. The analysis used listening/speaking intervals of at least 600 ms and later downsampled EEG and audio to 128 Hz. It is useful for continuous-stimulus alignment, lagged encoding, and speech segmentation. It is very unlikely to be the original source of the project’s pediatric CI files: the population, hardware family, task, and acquisition design do not match.

### `file_9fae6ab5a49581d205d2b10eb8b7168d` — *EEG-based diagnostics of the auditory system using cochlear implant electrodes as sensors*

This paper reports three adult CI users with an experimental percutaneous implant. It records two EEG channels plus a trigger channel at approximately 133 kHz, sends a trigger pulse on every stimulation pulse, and uses the trigger both for trial cutting and amplifier blanking. The methods document electrode montage, stimulation electrode pairs, pulse timing, C/T levels, blanking, and artifact interpolation in detail. It is not a plausible source for the project’s scalp EEG recordings, but it is a strong comparator for checking CI device state, trigger presence, stimulation timing, and artifact-related history.

### `file_c665dddfb3a019c408c877cc98b2c9d2` — *Objective electroencephalography-based assessment for auditory rehabilitation of pediatric cochlear implant users*

This is the closest methodological and provenance candidate. It reports 91 children (66 CI and 25 NH) with a 128-channel EGI/Net Amps setup at 1 kHz, an oddball design spanning pure tones, syllables, and Chinese tones, and approximately 600 ms analysis windows with 100 ms pre-stimulus and 500 ms post-stimulus periods. The reported sound levels differ between NH and CI groups, and the paper describes CI artifact removal, average reference, interpolation, ICA/PCA, and sLORETA. The shared pediatric CI context and matching EGI-style acquisition make it a possible original source, but the extracted text does not establish that any particular file belongs to this study.

### `file_03c524b4f51e445efb443d68e14c6456` — *Neural envelope tracking as a measure of speech understanding in cochlear implant users*

This paper uses eight experienced adult CI users, direct research-processor stimulation, 64-channel BioSemi EEG at 16,384 Hz, dropped stimulation pulses, and a 4 ms artifact-free gap repeated at 40 Hz. Speech understanding is varied by shifting current units between threshold and comfortable levels, and neural envelope tracking is compared with behavioral sentence scores. It is useful for interpreting CI artifact controls, current-level metadata, and the distinction between intelligibility and loudness. It is not a likely source of the pediatric 128-channel files; its direct stimulation and high-rate BioSemi design are different.

### `file_23f4c9bca34318d77ad8142736813627` — *不同听觉任务下人工耳蜗植入儿童听觉皮层诱发电位特征研究*

This Chinese pediatric CI paper is another high-proximity provenance candidate. It reports 54 children tested in pure-tone, syllable, and tone tasks with a 128-electrode EGI cap, loudspeaker presentation, approximately 65 dB SPL stimulation, and repeated standard/deviant trials. The reported CAEP/MMN processing includes 100 ms pre-label and 500 ms post-label segmentation, baseline correction, artifact rejection, interpolation, re-referencing, and averaging. The population, task vocabulary, device family, and timing conventions overlap the project metadata. That overlap is suggestive only; no file-level identity or event-code equivalence is demonstrated here.

### `file_a66da29bf53ad8afdabb0f49a21b48b2` — *Functional connectivity changes in infants with varying degrees of unilateral hearing loss*

This is a resting-state fNIRS study of 48 infants aged roughly 3–10 months, with unilateral hearing-loss groups and NH controls. Data were acquired at 10 Hz with a 40-optode/64-channel arrangement while infants slept; there is no EEG oddball task, event-code scheme, or stimulus-locked segmentation. It may provide clinical context for pediatric hearing-loss grouping and participant counts, and the institutional setting is compatible with the broader pediatric program. It is not a plausible source of the project’s EEG/MFF or BDF recordings.

### `file_dc7a74c3f5ff51e0b8e346c4917bcdd0` — *Effects of Sensorineural Hearing Loss on Cortical Synchronization to Competing Speech during Selective Attention*

This paper enrolled 45 older adult HI/NH listeners, with one EEG acquisition failure leaving 44 analyzed, not children or CI rehabilitation. It uses 64-channel BioSemi EEG at 512 Hz, insert earphones, 1–9 Hz speech-attention analysis, tone EFR/ERP paradigms, and carefully described sound-level and trial structures. Its value is as a comparator for speech-envelope analyses, loudness matching, attention conditions, and the need to distinguish EFR/ERP epochs from continuous attention trials. It is not a likely source of the project’s pediatric recordings.

### `file_287607181adeb8884ffa54bea4a0b5fb` — *2562.full.pdf*

The extracted text is byte-identical to `file_dc7a74c3f5ff51e0b8e346c4917bcdd0`, including the same title and methods. It therefore represents a duplicate reference entry rather than an independent study. Apply the same provenance conclusion and methodological use as the preceding entry; do not count it as a second participant cohort or independent source.

### `file_417d21e2d32089b155557ce337c73fc7` — *Frequency Selectivity of Persistent Cortical Oscillatory Responses to Auditory Rhythmic Stimulation*

This study combines sEEG in 16 epilepsy patients and MEG in 15 adults. It presents a 6.24 s bass-riff stimulus containing 62/83 Hz tones in a 2.56 Hz sequence, at a comfortable level near 70 dB, with 1000 Hz sEEG and 678 Hz MEG acquisition. Stimulus-locked epochs run from −1 to 9 s and the analysis explicitly separates stimulus and post-offset activity. It is useful for epoch-boundary, offset, and oscillatory-response concepts, but neither population nor hardware indicates that it is the project’s original source.

### `file_525e4399ac4372fff38628e031c341d3` — *The Multivariate Temporal Response Function (mTRF) Toolbox*

This is a methods/toolbox paper, not a source cohort. It explains forward and backward regularized linear temporal-response models, lag matrices, stimulus/EEG resampling, cross-validation, and speech-envelope or spectrogram examples. It is relevant if the project later analyzes continuous auditory features, especially because it stresses matching stimulus and neural sampling rates and preventing leakage across train/test segments. It supplies no evidence about the project’s children, devices, event codes, sound levels, or acquisition sessions.

## Provenance conclusion

The two pediatric CI papers (`file_c665...` and `file_23f4...`) are the only strong candidates for an original-source relationship because their population, EGI hardware family, auditory oddball tasks, sound-level reporting, and segmentation conventions overlap the project metadata. The other papers are methodological comparators or clearly different cohorts. No reference reviewed here independently proves the identity of a raw file, the meaning of a project event code, the acquisition version, or the child/session mapping.
