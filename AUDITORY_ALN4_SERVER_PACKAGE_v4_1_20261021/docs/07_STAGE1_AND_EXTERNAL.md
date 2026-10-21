# 7. Stage1 初始化资产：MindMix 优先核验，可信起点必须落地

本轮最多用一个 Stage1 初始化。先对 MindMix 释放的 EEG-only 资产做有界核验；在 ALN4 生产计划冻结前通过就采用，未通过即使用项目已有可严格加载的 CBraMod。核验不使用任何儿童目标表现。本包不要求重新训练数千小时 Stage1。

## 7.1 已核实与仍未核实

MindMix 仓库此前资产审计使用的代码 pin：`98445f368efcb161c638172501bd16f92d09a89d`。官方 README 把 `checkpoints/v2.4_large.pth` 列为 EEG-only 预训练资产，把 `pretrain_fusion_checkpoints/best_model_loss_0.0909.pth` 列为 Stage2 fusion 资产。现成 `load_pretrained_eeg.py` 从后者提取 `eeg_model.model.*`，不能拿它的输出冒充 Stage1。

已对 EEG-only 文件做 HTTP Range 和静态 pickle opcode 元数据审计，没有执行 unpickle、torch.load 或完整模型推理。文件不是不可用的小指针：响应给出总长166,531,622 bytes；LFS对象/响应 ETag 对应 SHA256 `707dfabf98e7c471fe7096722f97ac9aa06c3df1c86383b095cfc71f667455a0`。本地只读取190,971字节头部，**未独立计算完整文件 SHA**。

元数据中 `student.*` 是24个 transformer blocks、hidden=200；`cls_token=[1,1,200]`、`pos_embed=[1,109,200]`、`time_embed=[1,128,200]`、`qkv=[600,200]`。args含 `labram_large_patch200_1600_8k_vocab`、input1600、patch200；epoch=29。当前公开 factory 的 base 是12×200、large 是24×400，不能根据文件名选择 large 并忽略不匹配。位置/时间嵌入的当前实现也要逐项核对。

资产加入时的 commit 描述与后来 README 定位有差异；二者不能证明权重等于某个原始 LaBraM release，也不构成对作者的指控。现有公开材料尚不足以在本机确认“准确恢复了论文 Stage1”。即使 exact-load 成功，也应先标注为“MindMix-released EEG-only asset，恢复的24×200配置”；只有来源、架构、训练配置都吻合才能标论文 Stage1 reproduced。

## 7.2 Server 的有界核验

intake阶段给一次集中恢复尝试，不超过一个工作时段（建议4小时工程时间）；这不是效果搜索预算。应完成：下载完整资产并计算 SHA；识别真实 state_dict；记录每个 tensor 的名字、shape、用途；使用作者可追溯的结构恢复完整 EEG backbone；仅允许明确剥离 token-prediction/classification heads。记录 trainable backbone loaded numel / expected numel=1，且没有静默丢弃不匹配 backbone tensor。`strict=False` 单独不构成证据。

明确列出位置嵌入选择/重排、通道表、采样率、振幅归一化、本包三个实际crop、resampled有效点数、padding及完整儿童epoch的处理。只允许对现有 EEG 支持作重采样、合法位置映射或显式 padding；不能读取目标窗外数据来凑输入。完成独立 EEG 前向、所有 backbone 层梯度、保存→strict reload 输出一致性和20/31/64通道输入探针。只有 shape 不够，必须有运行验证。

若仍存在未解释架构缺口、部分随机 backbone 或输入不支持，记录 `asset_gate=not_passed`，采用已验证 CBraMod `pretrained_full`。这是一项事先固定的就绪决策，不能按分数把某个模型换上来。CB 资产应从项目 `FETCH_RECEIPT.json` 继承完整来源和权重 SHA；已知代码 pin `b9e96100`，HF `weighting666/CBraMod@500543c`，实际完整hash由server复核。

Stage1身份一经在 `BINDING.json` 冻结，五臂完全相同；R2复现也不换起点。后续另一 backbone 只能作为单独、明确命名的可移植性实验，不能与主结果混算。REVE仍保留竞争配置，但不是R1新增分支。


## 7.3 新版时间与外部比较补充

资产实际运行核验必须覆盖20/31/64通道、每窗78/81/80有效点+右pad200的接口；不能只用原1秒/800ms整段通过后声称新三窗已验证。记录patch定位与通道映射，所有backbone tensor完整恢复、从首步有效梯度、保存→strict reload同输入一致。

R1 intake优先核验完整MindMix外部比较的Stage2/downstream资产与可忠实公共任务；若工程就绪失败，固定Transformer-CLIP替代该外部席位。不得按本方法成绩选择对手。外部预训练数据重叠、audio可见性、license和输入合同必须真实记录。未在本机完成完整权重下载/torch加载；LFS SHA是来源声明，不冒充本机完整文件校验。

论文：https://proceedings.iclr.cc/paper_files/paper/2026/file/b0ae046e198a5e43141519868a959c74-Paper-Conference.pdf

官方代码：https://github.com/CookieMikeLiu/MindMix/tree/98445f368efcb161c638172501bd16f92d09a89d

Transformer-CLIP官方代码：https://github.com/exporl/transformer-clip-eeg

CSAligner（用于界定已有CS跨模态方法）：https://proceedings.iclr.cc/paper_files/paper/2026/file/42bc612558891859b1b8717051f2c7b0-Paper-Conference.pdf

经典CS依赖学习来源：https://people.csail.mit.edu/fisher/publications/papers/principe00vlsi.pdf
