# C3 外部数据申请邮件（v1，2026-10-04）

三封信互相独立，发出后都不阻塞任何步骤。发信前请把签名里的方括号换成你的姓名、单位和导师。收到回复后，告诉我回复内容和附件位置，我来更新回执与登记表。

| # | 决定点 | 收件人 | 要什么 | 解决什么 | 不发的后果 |
| --- | --- | --- | --- | --- | --- |
| 1 | D1 | DTU（数据集联系人） | 原始刺激音频 | DTU 能提取 Whisper/wav2vec2 特征，做 H2/H3 的第二个成人队列；H7c 也能做（SRT、逐试次理解题） | DTU 只做包络层分析；H7c 不可评估 |
| 2 | D3 | FAU（数据集通讯作者） | 逐人行为数据（HSM、Freiburg、ACALES、逐试次理解题） | H7a/H7b，也就是 R3 的主终点（CI 成人） | H7a/H7b 不可评估 |
| 3 | 可选 | IMT Lucca（数据集通讯作者，cc 合作作者） | 故事音频；确认已发布数据的预处理带宽 | H7d 能按登记形式做；D2 有书面依据 | H7d 只能做包络层分析；D2 只能靠数据频谱判断 |

R3（功能）要成立，至少要有一个队列同时具备音频和行为，所以第 1 封和第 2 封至少要有一封得到回复。

地址来源：DTU 来自 Zenodo 3618205 的数据说明（"send an email to [联系邮箱，发布版删去] with the subject line 'ds-eeg-snhl audio'"）；FAU 的地址来自 bioRxiv 10.64898/2025.12.22.695344 的通讯作者；IMT Lucca 的地址来自 bioRxiv 10.1101/2024.02.22.581545 的通讯作者。抄送人（合作作者）的邮箱我没有查到可靠来源，抄送前请自行确认。

---

## 1. D1 — DTU 原始音频

**To:** [联系邮箱，发布版删去]
**Subject:** ds-eeg-snhl audio

> Dear Dr. [recipient],
>
> I am a researcher at [institution] working on EEG speech tracking in hearing-impaired listeners and hearing-device users. We are using the public dataset "Selective auditory attention in normal-hearing and hearing-impaired listeners" (Fuglsang et al., 2020, J Neurosci; Zenodo 10.5281/zenodo.3618205), and following the instructions in its README I am writing to request access to the raw audio of the speech stimuli used in the selective-attention experiment.
>
> We plan to compute layer-wise representations of the stimuli with frozen pretrained speech models (Whisper, wav2vec2) and ask how much information the EEG carries about acoustic versus higher-level speech features, using information-theoretic measures. The envelopes in the derivatives folder support the acoustic part of this analysis; the higher-level features require the waveforms. If possible, we would appreciate both the CamEQ-equalised and the unequalised versions (matching the "woa" envelopes), or the unequalised audio together with the CamEQ gains.
>
> The audio will be used for research only, stored on our institution's access-controlled server, not redistributed, and the dataset and paper will be cited in any resulting publication. We are happy to sign a data-use agreement if required.
>
> Thank you very much for making this dataset available.
>
> Best regards,
> [Your name]
> [Position, lab, institution]
> [Supervisor / PI, if applicable]

---

## 2. D3 — FAU/TUD 逐人行为数据

**To:** [联系邮箱，发布版删去]
**Subject:** Request: participant-level behavioural data for the "Attention Decoding at the Cocktail Party" datasets (Zenodo 17927767 / 17952844 / 17952231)

> Dear Dr. [recipient],
>
> Thank you for publishing the three "Attention Decoding at the Cocktail Party" datasets (hearing-aid users, cochlear-implant users and typical-hearing participants) together with the stimuli and your analysis code. They are an excellent resource. We are using them to study, with information-theoretic measures, which kinds of stimulus information (acoustic versus higher-level speech features from frozen speech models) are carried by the EEG of hearing-device users. As a first step we will reproduce your attention-decoding results with your published pipeline.
>
> Would it be possible to share the participant-level behavioural and clinical data described in your manuscript (bioRxiv 10.64898/2025.12.22.695344), linked to the subject codes used in the HDF5 files? Specifically:
>
> 1. HSM sentence test in noise (65 dB speech / 60 dB noise) and Freiburg monosyllables in quiet;
> 2. ACALES listening-effort ratings;
> 3. the per-trial answers or scores of the comprehension questions;
> 4. basic covariates if they can be shared: age, and for device users the device side(s) and duration of device use.
>
> We would use these only to test, out of sample, whether EEG-derived measures add to clinical baselines in predicting speech understanding. The data would be stored on an access-controlled server and not redistributed, and your datasets and paper would of course be cited. We are glad to sign a data-use agreement.
>
> While auditing the files we noticed three small points. We mention them in case they are useful to you; none of them needs an answer for the request above.
> - The typical-hearing HDF5 contains 28 subjects, while the manuscript reports 29 after exclusion.
> - The HA hdf5_dataset_info.txt mentions an "eeg_ica" branch, but none of the three files contains one (only "eeg").
> - In a small number of trials, the auxiliary audio channels peak at a 6–23 ms offset from the provided envelopes (median 0 ms over all trials). We plan to realign those trials from the auxiliary channels unless you advise otherwise.
>
> Thank you again for your work and for considering this request.
>
> Best regards,
> [Your name]
> [Position, lab, institution]
> [Supervisor / PI, if applicable]

---

## 3.（可选）Federici 数据集提供方 — 故事音频与预处理带宽

**To:** [联系邮箱，发布版删去]
**Cc:** [合作作者的邮箱，请自行确认]
**Subject:** Request: story audio and preprocessing details for Mendeley dataset nzg5g2gzrd (neural speech tracking in children with CIs)

> Dear Prof. [recipient], dear Dr. [co-recipient],
>
> Thank you for sharing the preprocessed EEG, envelopes and code of "Resilience and vulnerability of neural speech tracking after hearing restoration" (Communications Biology, 2025; Mendeley Data 10.17632/nzg5g2gzrd.2). We are using these data to examine, with information-theoretic measures, how speech information carried by the EEG differs between children with cochlear implants and hearing controls. We will first reproduce your short- and long-timescale results.
>
> We would be grateful for help with two points:
>
> 1. **Story audio.** Would it be possible to obtain the audio files of the Italian stories (as listed under CodeStoryA / NameStoryA in the sample-info sheets)? We would extract layer-wise features with frozen pretrained speech models to go beyond the envelope. The audio would be used for research only, not redistributed, and cited. If the recordings cannot be shared, could you tell us their source (for example a commercial audiobook edition) so that we can try to obtain them ourselves?
> 2. **Preprocessing band of the released data.** The manuscript describes 0.1–40 Hz filtering at 250 Hz, followed by re-filtering at 2–8 Hz and resampling to 100 Hz for the TRF analysis. Could you confirm that the released *_preprocEEG_cut_ica.mat files are the 2–8 Hz, 100 Hz version, and what filter type and order were used? This determines which time lags we can interpret.
>
> One small linkage question: the CI folder contains EEG for 33 participants, while the CI variable sheets (variable_16CD16AD.xlsx, CDAD_variable.xlsx) have 32 rows. Is one participant intentionally without behavioural data?
>
> Thank you very much for making these data available.
>
> Best regards,
> [Your name]
> [Position, lab, institution]
> [Supervisor / PI, if applicable]
