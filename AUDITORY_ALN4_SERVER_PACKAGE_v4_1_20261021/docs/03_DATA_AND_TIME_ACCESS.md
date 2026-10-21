# 3. 数据、物理时间与身份隔离

## 3.1 固定源数据

继承有效 SparrKULee core/rich manifests 和 presentation exclusions [4,5,19]：fit 81,732 segments/64 people/48 content families；dev 6,332/10/9；bridge_cal 6,162/6/6。这些是已读取manifest的基线，server须核对实际纳入与文件hash。fit/dev/cal人和内容隔离；源与DTU/FAU/私有目标的重叠排除维持。cal不做R1 LR选择。

- core manifest SHA256 `3ffa6e6d013283368d1f7eb09bf6c9e7573c0ae4009304cf3bc1d9836c197046`。
- rich manifest SHA256 `c8f11c28b4014aec3f06f52e3c058640409d8fa9d0d8a91c95f2f05505eabcfd`。
- server完整manifest SHA256 `b751976b9238590026f26a6fbe6c84177b69802ef9e55e687425af210b627426`；路径 `private/auditory_alignment_v3/aln34/prior33/manifest.json`。

声音固定env、ss、sc三view等权：env为8样本包络，ss为8帧×4个source-fit谱PCA分量，sc为相邻PCA帧差范数。rich来自Whisper 128-bin logmel再PCA，不叫MFCC。必须 `open_with_rich` 合并core/rich、`DonorBank(...,rich=True)`、`rich_targets()`、现有`fixed_heads()`；原CBaud Stream只有env，不可照搬后静默丢两view。PCA/标准化/32d固定head仅用source-fit；三view每个batch都需完整。

## 3.2 先裁原生样本，再重采样，再padding

两种候选FM的一秒patch不能自动产生细时间轴。三窗各自独立backbone forward，共享参数，没有跨窗上下文。以原生样本时间落入半开区间为定义，端点取ceil；下表不是把400ms拉伸成1秒。

| 视图 | 名义支持ms | source64Hz相对anchor切片 | source200Hz有效点数 | private250Hz epoch切片 | private200Hz有效点数 |
|---|---|---|---:|---|---:|
| W0 | [−200,200) | [−12:13]，25点 | 78 | [0:100]，100点 | 80 |
| W1 | [0,400) | [0:26]，26点 | 81 | [50:150]，100点 | 80 |
| W2 | [200,600) | [13:39]，26点 | 81 | [100:200]，100点 | 80 |

source首/末实际采样时刻分别为W0 −187.5/+187.5ms、W1 0/+390.625ms、W2 +203.125/+593.75ms。每窗先裁实际样本，再用固定resampling实现得到 round(n_native×200/fs_native) 个点，保留其原生时长近似；右侧零pad到200，pad在缩放之后。可用 `scipy.signal.resample` 只对该crop计算，不能整秒FFT重采样后mask并声称只访问crop。实现也可用有确定边界处理的等价crop-only方案，必须冻结并验证。幅值/通道归一化继承资产合同，不能按每窗单独使用目标label选尺度；padding不能参与估计实际信号均值。

旧source接口用q+[-26:38]的64点窗，缺少新W2需要的q+38点。必须从原生DonorBank segment span读取，不能补零冒充数据。span长度357，保留原offset≥26且offset+39≤357，缓存几何上限为offset≤318、229个旧grid ticks（旧末tick319不能用）；生产采样进一步固定为 TICK_OFFS∩[26,281]，共200ticks、实际末tick280，使新W2的offset+39≤320、三crop均落在各自5s segment内。每条实际access记录native segment、anchor、crop start/stop、实际首末样本、resampled_valid_n、pad_n；拒绝越界。

本研究披露已有整记录offline滤波/标准化；以上是**模型直接输入样本支持**，不等于因果隔离或真实生理响应潜伏期。重叠400ms窗支持时间组织比较，不能把相关峰或q峰称行为反应时。旧40ms strict-local与旧全1s位置迁移保留各自方法定义。

## 3.3 人内支持/query采样

每update先抽2人，再各自选择3个可用content families。每个S32、Q32由11/11/10个不同5s segment组成，每segment只取1合法anchor。S/Q使用不同segment与不交叠physical access；相邻segment可能属于同一连续记录，需从native时间戳和full access envelope验证guard，而非仅比较segment ID。抽样失败先重抽满足合同的segment，不能自动减小S/Q、混人或静默复用同片。

已审计源fit 64人每人≥518segments、≥3families，人×family至少23segments。该计数只支持抽样可行性预判，**不替代物理guard核验**；某人若实际不满足，记录原因并修正共同采样池，在所有arms采用同一个版本。被排除人员/内容需报告，不能按分数排除。

S与Q可来自同一family但不允许原始时间范围/guard重叠；这检验同人跨片段支持，不等于新内容任务。source fit/dev的完整人和family外隔离另行承担泛化。batch流预生成/可重放，所有臂共用。每人单算CS/NCE、再等权平均；episode数量、anchor数和独立person数分别计。

## 3.4 目标数据合同

公共DTU/FAU继承现有严格participant/content/fit-ES-test划分与候选声音规则。主共同目标是已具备的envelope与history residual；已有频谱成分在可用队列继续复用，不假装所有队列都有相同rich流。DTU 44人HI/NH各22；FAU 67人HA/CI/TH；HI不自动等于HA。三者不与私有儿童混成一个临床样本。

私有主lane为BDF pure-tone的既定64儿童（55HA/9NH）一人一主记录，20channels×200 samples、250Hz、epoch[−200,600)ms，标准/偏差标签与history/bin/block/fold/age/device-duration可用。outer split seed20261005，5fold人数13/13/13/13/12；fit/ES为外层训练儿童的physical block划分，末约20%blocks作ES。这是train-person内的ES，不冒称inner heldout-person。

源loader依赖 `private/auditory_gx/GX_stage_001/epochs`、`private/auditory_pf/prepare_002/{records,children}.csv` 及GX1 shared predictions文件等；后者即使新模型不使用ev也可能是现有loader入口依赖。不得仅按“旧prediction”删除。NH device duration为NA，不填0。

MFF pure-tone已有41records/37ids（GX旧分析40/36），bapa29/27；9个同日同儿童候选配对中旧报告7个完整。先核绑定，不预先当成9个可比人。unknown语义不等于bapa，ba1/ba4稀少对象不能变成独立大任务。R1只恢复资产/旧结果；R2最多一项冻结跨刺激问题，见第5章。

所有角色列出可见EEG、音频、标签、metadata和选择用途。模型可以在目标训练儿童标签上学习，不可用测试儿童query标签选epoch/window/支持/分支。已存在无标签整记录预处理需明确披露，不能为了简写称完全inductive。

### 公共128Hz输入与唯一重采样责任层

现有 `load_dtu/load_fau` 是128Hz，DTU64通道、FAU31通道。公共三窗原生相对anchor切片依次为[-25:26]、[0:52]、[26:77]，51/52/51点；重采样有效点80/81/80，再pad200。必须用真实sampling rate计算，不能套source64Hz offsets。

本包固定**新time-bank wrapper**拥有crop→`scipy.signal.resample`→pad流程：给现成 `Backbone` 的已采样输入为200Hz/200点，构造`fs_native=200`，其resampler因长度相同直接返回。幅值缩放由backbone/资产adapter单独执行一次，外部wrapper不再乘0.15。MindMix新adapter遵守同一责任划分，并登记自身资产幅值合同。旧 `resample_fft` 对Nyquist的处理不保证逐点等于SciPy；不要一部分arm走旧resampler、一部分走新resampler。CPU缓存可复用三crop，但必须以原生crop为输入、记录正确有效点数且没有后续二次重采样。真实前向probe需断言单patch和20/31/64通道映射。
