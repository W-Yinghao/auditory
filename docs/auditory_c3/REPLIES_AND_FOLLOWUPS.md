# 数据请求的回复记录与后续邮件（2026-10-05 起）

`EMAIL_REQUESTS_v1.md` 的发出版本保持不变。这里记录回复、它们对 C3 的影响，以及待发的后续邮件。邮件由用户发送；凭据与逐人数据只存放在 `private/`。

## D1 — DTU（数据提供方），2026-10-05

- 原始音频已提供（访问凭据见 `private/auditory_c3/dtu_audio/`），已下载并通过校验（`DOWNLOAD_RECEIPT.json`）。
- 使用条件：仅用于研究，存放在访问受控的存储上，不再分发。
- 影响：H7c 和 DTU 的 H2/H3 可以按登记形式计算，正在进行（队列 007）。

## D3 — FAU/TUD（数据提供方），2026-10-05，两封

| 回复内容 | 对 C3 的影响 | 处理（在拿到相关数据之前写定） |
| --- | --- | --- |
| TH 少了一名被试，数据还在，可以提供 | TH 将从 28 人变为 29 人 | 新被试**归入留出的一半**（它从未参与选层），所以留出 TH 变为 15 人。预处理、ICA 规则和所有测量都按冻结规格执行。v2 中 14 人的结果保留，新结果标为 v2.1 并与之并列 |
| `eeg_ica` 那句话是 CI 数据集的遗留，ICA 清洗过的数据没有发布 | 发布的三份数据都没有 ICA。我们阶段 B 自己做 ICA 的做法成立。**这可能解释 G2-T 中 CI 的差距**：H1a 复现用的是未经 ICA 的发布数据（56.2%），论文的 63.1% 也许是在未发布的 ICA 清洗数据上算的 | 在后续邮件中确认，确认之前不改 G2-T 的判定 |
| 用辅助音频重新对齐是最稳妥的做法 | 修正案 001 以重新对齐的试次为主的选择，得到数据提供者确认 | 在 `MEASUREMENT_AMENDMENT_001.md` 中补记 |
| CI 的逐人数据已在 NeuroImage 论文附录 Table 4 中公开（doi 10.1016/j.neuroimage.2026.121771），编号与数据集一致 | H7a（CI 的功能主终点）**从"不可评估"变为可评估** | 按 `H7_FUNCTION_PREREG.md`，先登记再连接数据 |
| HA 的行为数据很可能也能提供 | H7b 待定 | 同一份登记，数据到后执行 |

**Table 4 的获取**：ScienceDirect 拒绝了自动抓取（403）。预印本（bioRxiv 10.64898/2025.12.22.695344，CC-BY）的全文接口目前对本服务器限流，之后再试；也可以由用户下载论文 PDF，放到 `private/auditory_c3/<FAU 行为数据目录>/`。

---

## 后续邮件草稿 — 致 FAU/TUD 数据提供方（待用户发送）

**To:** [联系邮箱，发布版删去]
**Subject:** Re: Request: participant-level behavioural data for the "Attention Decoding at the Cocktail Party" datasets

> Dear [recipient],
>
> Thank you very much for your quick and very helpful replies, and for pointing us to Table 4. We will use it with the dataset IDs as you describe, and we look forward to hearing whether the hearing-aid data can be shared as well.
>
> 1. **Missing typical-hearing participant.** We would be grateful to receive this participant's data, ideally in the same HDF5 format as the published files, including the auxiliary audio channels.
>
> 2. **ICA and the CI results.** Thank you for clarifying the "eeg_ica" note. This may explain the one difference we found in our reproduction. Using your published linear pipeline (aad-neuroimage @ cbf9bd8) on the released, non-ICA data, we obtain 85.5% for TH and 87.9% for HA, close to the 87.8% and 88.5% in the paper, but 56.2% (95% CI 52.3–60.6) for CI, against 63.1% in the paper. Were the CI accuracies in the paper computed on ICA-cleaned EEG, for example with the ICA–audio cross-correlation procedure of Jehn et al. (2025, J Neural Eng)? If so, could you share the settings used (threshold and SNR definition, and the number of removed components per participant), or the cleaned CI data or unmixing matrices, if that is possible?
>
> 3. **Behavioural variables for the hearing-aid group** (if they can be shared): HSM in noise and Freiburg monosyllables, ACALES ratings, the per-trial comprehension-question scores, age and duration of hearing-aid use. If comparable measures exist for the typical-hearing participants, they would be useful too.
>
> The data will stay on our access-controlled server and will not be redistributed; your datasets and papers will be cited.
>
> Best regards,
> [Your name]
