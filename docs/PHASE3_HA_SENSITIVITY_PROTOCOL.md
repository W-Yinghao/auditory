> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# HA penalty sensitivity protocol

This is a single robustness check specified after observing Phase 3 HA v1 results. It does not expand the scientific targets or create a new model search. It uses the exact 50-record PTA-complete index set and the same outer/inner folds and seed as `phase3_science_v1`.

The target is MUSS only. The clinical-only age plus log-duration baseline uses the frozen alpha grid; age plus log-duration plus PTA reproduces the v1 clinical baseline. For the poststimulus 160-feature and prestimulus 80-feature models, clinical and EEG blocks have separate penalty grids. Standardization and pair selection occur within training folds. The infinity EEG option omits the EEG block and is a null-EEG check. Predictions are clipped to 0–100 in inner and outer scoring. Fixed outer predictions are compared with 2,000 candidate-level loss bootstrap draws; the interval excludes full-workflow refitting uncertainty.

The result is a penalty sensitivity check. It cannot establish independent validation, clinical utility, causality, or cortical specificity.
