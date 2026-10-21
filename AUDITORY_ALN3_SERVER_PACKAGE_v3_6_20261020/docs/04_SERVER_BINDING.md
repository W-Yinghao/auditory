# 04 — Server 接入、源人群排除与执行身份

## 4.1 本文件的执行地位

本包延续 ALN3.5，制作时核对的公开源码为 W-Yinghao/auditory 的 3da8cf5758214c0cf87a1f1c8d67fb84b574000e。它把接下来三轮收束到声音证据共享、个人读出可用性及时间组织的有限比较。旧结果、旧执行身份与有效不利结果全部保留。

**当前仓库没有可以直接启动本轮全部实验的现成 ALN3.6 CLI。** Server agent 须在独立的 auditory_alignment_v3/aln36/ 接入新协议，登记新的代码、设计、数据选择和来源哈希；复用下文已有组件，不修改正在运行的 ALN3.4/3.5 模块或将旧记录改名冒充新执行。包内参考工具及文档不等于生产实现，更不等于真实 EEG 训练已完成。

本轮工程检查通过后，已授权的完整单元继续执行；不再等待论文措辞、显著性、性能入场线或逐项人工 go。只有实际无法满足身份、内容、数据授权或资源约束的问题才阻塞其受影响单元。这里不授权整批取消旧作业、清空 holds、删除 checkpoint 或启动无关新实验。

## 4.2 R1/R2 的真实训练数与评估数

R1 使用 seed 3401；R2 按本包冻结的相同协议重复 seed 3407，不因 R1 的结果方向更换工具、目标组或指标。R3 不新增模型 family。

| 面板 | 唯一训练来源 | R1 评估 bundle |
|---|---|---:|
| FAU 整个目标听觉组排除 | local、CBpre；目标组 HA/CI/TH；2 个 content folds；默认每组/内容/工具只训练一次 | 2 × 3 × 5 person folds × 2 content folds = 60 |
| FAU 旧 pooled 描述参照 | 复用原 20 个相同工具的外层排人 source，不重新训练 | 20 |
| DTU 新个人支持协议 | 复用原 20 个相同工具的外层排人 source，不重新训练 | 20 |
| 私有 matched AP/APwrong | 复用同一修订 sampler、同目标合同的 2 arms × 5 outer folds；必要时补冻结特征提取 | 10 |
| 私有 S 补充参照 | 仅在已有特征、trial、outer fold、query 和历史接口兼容时复用 | 可选额外 5 |
| 合计 | FAU 默认 12 次新 source fits，其余为复用/提取/读出 | 110；兼容 S 加入时 115 |

FAU 的 5 个 person folds 继续作为原有目标人身份与结果分块。**当整个目标听觉组均已排除，目标组的哪一个 fold 正在评价不应再改变合法源训练人集。** 默认 source 使用所有合法非目标组的人及其 source-fit/source-ES 内容，因此 5 个目标 fold 共享一个 source checkpoint。每 seed 的唯一训练数为 2 工具 × 3 目标组 × 2 内容划分 = 12；R1 与 R2 总共默认 24。

Server 必须分别保存 source_training_signature 与 evaluation_signature：

- 训练签名包括 seed、工具及完整 recipe、目标组、合法源人 ID、fit/ES/cal 声音与样本 ID、输入预处理/统计来源、初始化、目标坐标、预算、checkpoint 规则及代码/设计哈希。没有改变训练输入的目标评估 fold 不进入训练签名。
- 评估签名另包括 source checkpoint 哈希、目标组、目标 person fold、content fold、support/query 绑定及读出条件。
- 按实际训练签名去重。不能为了凑 60 个数字复制同一训练、改 RNG 盐或给同一权重五个独立模型身份；同一 checkpoint 的多fold结果也不能当作额外独立 n。
- 每 seed 固定为 12 次唯一 FAU source 训练、60 个评估格。若实际绑定显示原先认为相同的 source 输入并不相同，先报告具体差别并修正绑定；不能静默增加训练，也不能将 60 个评估格解释成允许 60 次训练的额度。
- 以真实目标人作为推断单位，先汇总同人的两个内容重复，再按既定规则汇总 seed。共享 source 权重、fold、seed 和支持抽样均不增加独立人数。

## 4.3 FAU 整组排除：过滤必须贯穿整个学习链

FAU 人群元数据来自现有 cohort loader 与已冻结身份表。正式评估面板为 HA 29、CI 24、TH 14；额外 TH dev 人只可作为合法源人，不进入正式目标人 n。Server 重新绑定实际 roster/hash，不从本轮成功输出反推预期队列。

对于目标组 g ∈ {ha, ci, th}，先构造完整合法源人集合：

    source_ids = human identities whose group != g and test_only == false
    target_ids = registered evaluation identities whose group == g and dev == false

具体规则：

1. 排除目标组的全部 EEG，包括该组其他 outer folds、任何 dev/selection-half 身份和该组不在正式评估面板中的同源记录。leave-TH 时必须排除 TH dev，不能沿用“dev 一律放入训练”的默认条件。
2. 源模型的梯度、早停/选 checkpoint、音频—EEG目标映射、读出、温度、带宽、标准化、PCA/白化等所有依赖 EEG 或 EEG—声音配对的数据拟合，均不得访问目标组 EEG。
3. 合法源 fit 只取 source_ids 中、role=fit、kind=ss 的段；合法源 ES 只取同一 source_ids 中、role=es、kind=ss 的段。source-test 内容不进入梯度、统计拟合或 checkpoint 选择。
4. 听觉组筛选在产生 batch 索引与拟合任何统计量之前完成。允许底层只读文件中同时存在其他组，但所有数据消费者必须使用冻结的合法索引；不能凭“最后的 loss 只算 source 人”证明整个管线排除成立。
5. source ES 可以来自与source-fit相同的人、独立声音内容。报告为“源人内、内容分离的 checkpoint 开发”，不称 whole-pipeline inner-held-out-person 选择。新任务的目标组与目标人始终排除。
6. fit、ES、cal、target support、target query 各自保存人、组、content/part、stimulus UID、物理样本访问与角色哈希；任何 group、role 缺失或不一致必须显式报错，不默认为可训练。

现成入口及必须覆盖的默认行为：

| 组件 | 可复用内容 | 新接入必须处理 |
|---|---|---|
| auditory_alignment/data.py | FAU cohort、5人fold、2内容fold、段/刺激身份 | 74–89 行的 TH dev；109–115 行的角色与预处理；不能仅筛正式 panel |
| auditory_alignment_v2/train.py | Batcher 与按人平衡、去重刺激的训练 batch | 29–32 行默认人选择及49–53行 fit/es/train_p，必须替换为显式合法源集合 |
| auditory_alignment_v3/aln34/breadth_inner.py | metadata、训练索引、独立计划及训练 hook | 60–86 行的默认 dev 保留；不得直接复用作 leave-TH |
| auditory_alignment_v3/aln34/data_inner.py | 186–204 行 batcher/统计 hook | 非 inner axis 在194行保留 outer_fit；新group协议必须用合法 source-fit，不能继承全pooled统计 |
| auditory_alignment_v3/aln34/content_time.py | 冻结提取、声音属性、history残差、ridge与TG | 必须接入新的source签名/路径；旧混合组checkpoint不能冒充新group-excluded模型 |

新模块可以借鉴现有进程内 instrumentation，但使用独立 family/version 与上下文管理，退出后恢复 hook。禁止修改原全局默认后影响其他正在运行的 family。

### 4.3.1 输入标准化与预处理范围

现有 data.py 的 _stdz（38–41 行）按单个参与者的全部已加载 trial 计算均值/标准差；load_fau 在111行调用它，包含fit/es/test内容。它没有把不同人的EEG合并拟合，但不能称为严格 source-fit 内容统计。

新 FAU 接入须把学习型输入统计绑定到合法源fit，使用同一 source-only 通道统计冻结变换 source ES、目标人的支持和查询；不得利用目标组或 source-test EEG 估计 population 输入统计。读取现有 stageB 的预处理 EEG，在新 loader/缓存层实现此绑定，不覆盖原数据或旧cache，也不能在已经按全trial标准化的值上再套一层 scaler 就声称去掉了旧访问。

目标人的自然支持只供本包指定的个人读出干预。本轮不增加个人输入标准化：H0/E0/HP/EC/ET共用固定source尺度。不能让候选比共同基线多一个未登记的输入变换，也不能使用query统计。

保留历史滤波、ICA及记录级离线处理的真实范围。上述分离是新训练、统计、读出和选择阶段的分离，不声称追溯完成原始EEG因果滤波或在线预处理隔离。本轮不以重做全库原始预处理为前置主任务。DTU旧冻结模型的历史预处理原样保留并单列，不把它重标为新FAU预处理协议。

### 4.3.2 音频、初始化与 donor

- local 从该seed的合法新初始化开始，继承有效 local_aligned1000 结构与完整训练配方；不能从见过目标组的旧FAU local权重 warm-start。
- CBpre 仅使用已使用的原始通用 CBraMod checkpoint，记录实际文件及SHA256，并继承 query-aligned full_onestep_v1 的全量更新实现。
- 新FAU排组模型不得使用旧FAU pooled微调权重、项目内CB auditory-continued donor、AP/XP/J*/XM auditory donor，或任何见过被排除FAU组EEG的蒸馏/音频—EEG映射作为初始化或固定teacher。只过滤下游head不能消除这些来源访问。
- 纯声音、且不依赖FAU EEG的既定特征提取器可以复用；音频目标的均值/尺度/投影及声音history残差，只能依赖本任务合法source-fit声音，按既定源端规则开发，禁止使用query声音拟合统计。query的真实声音只用于规定评价目标/候选评分，不输入EEG decoder或参与适配选择。
- 原始通用CB预训练的听觉类别/受试者覆盖未由本包证明。论文与记录限定为“本研究FAU任务学习、校准和选择排除整个目标听觉组”，不能声称原始基础模型历史上从未接触这类听者。
- 此限制针对新FAU排组链。私有matched AP/APwrong是另一条已授权、目标队列排除的既有来源链，仍按其自身配对合同复用，不被误停。

## 4.4 保留有效工具的训练日程；只实施已决定的新选择规则

本轮不是再次竞争backbone/loss或降低local预算。制作基线的直接有效 parent 配方已核对：

| 工具 | 固定配方 | 代码证据 |
|---|---|---|
| local L1 | local_aligned1000，NCE，32维；200 epochs；AdamW lr=1e-3、weight_decay=1e-4；原cosine日程 | core.py:9,30,53–59；local_support.py:108–129；local_train.py:73–89 |
| CBpre | query-aligned full_onestep_v1；NCE；100 epochs；backbone lr=3e-4、head lr=1e-3；LLRD=1；从第一训练阶段全量更新 | run_aligned32.py:23–32；fm_dense.py:42；fm_aligned32.py；直接parent行 |

公开计划中的FAU直接parent例子：local ALN3X_84b5c4fd866b3b7a；CBpre ALN3X_124a413438c432c7。它们是配方来源，不是新排组模型的warm-start权重。Server绑定实际parent记录的 resolved_config、训练ledger、source/code hash并逐项比较；如实际来源不同，先据事实修正binding，不猜值、不静默换parent。

禁止把local改成100 epochs以节省收束成本；也不继承 doubled-budget 的local400/CB200，更不添加4×预算。每个模型保留实际更新次数、源人数、fit段数与训练曝光，因此不同源组之间不冒称等更新次数或等数据量。

### 4.4.1 唯一 checkpoint 选择对象：source实际true-query NLL

原local与FM训练器仍包含 es_loss − es_mismatch 的选择逻辑；新ALN3.6必须替换该选择分支，不能仅把字段改名。旧训练结果保留原定义。

本轮统一在冻结的source-ES query和候选音频池上，以实际native检索概率的true-query NLL选checkpoint：

    risk_bits = mean_queries[-log2 p(correct_candidate | EEG_query)]

要求：

1. query、合法候选集合、正确列索引、候选顺序及所有物理ID在第一次生产训练前冻结。候选池从合法source-ES内容建立、去重，不能用新batch随机负例改变每次风险的对象。
2. 用与最终评价一致的native评分/概率接口；温度及其他概率参数仅来自source-fit，或事先固定的source内部cal子集。cal不从目标组或query中产生。source-ES只负责checkpoint选择，不另扫gain/true-risk选择器。
3. 按既定评估节奏保存实际风险轨迹和epoch/update。候选包括合法初始状态及已登记训练节点；并列优先更早/更简单状态。所有训练按固定parent日程完成，不凭outer结果延长或提前中止。
4. 选择只使用上述真配对NLL。mismatch、相关系数、AUC、组差、个人适配收益可以报告，但不能进入checkpoint排序。
5. 新source的后续共同/个人读出使用这一固定选中checkpoint；不得为history、时间窗、不同目标组子集或个人查询各选一个更好的encoder。
6. 来源同人的独立ES内容用于此处选择是合法的既定层级；不要因此新造一整套inner-person训练网格。

若原score封装重建了自动pooled读出/温度，须在新封装中显式传入合法source集合。可借鉴 adaptation_policy.py:143–195 的重建和评分接口，但其自动training/ES选取不能直接不加筛选复用。

## 4.5 公共目标个人支持：自然U30来自source-fit内容，Q为全部source-test

FAU新排组source、FAU旧pooled参照和DTU旧排人source都使用新版本的同一目标支持/查询定义。旧ALN3.5支持结果保留，不改名复用。

对于每个目标人和content fold：

1. 目标支持候选只来自该人的role=fit、kind=ss内容；query固定为该人的全部合法role=test、kind=ss段/anchors。role=es不混入个人支持或query。
2. 按实验记录的实际顺序构造自然U30：在该人的source-fit内容全部合法5秒段中，取前ceil(0.30 × 段数)个完整5秒段；段内固定8个anchors。不得把整个声音part强行作为最小支持块而让名义U30变成全部fit数据。保存段数、秒数、anchor数、实际比例及所覆盖真实内容block；不看标签或query再挑段。
3. 同一个人的全局读出、概率/时间调整及低维个人读出，必须使用完全相同的U30输入权限和同一个Q。支持集合只按既定顺序/元数据产生，不按标签平衡、history覆盖、读出损失或query效果挑选。
4. block的稳定键来自真实刺激code/记录/part；支持选取的最小单位是上条完整5秒段，block仅作来源和覆盖记录。不要把数据bank拼接顺序假称临床时间。个体若不足以提供完整合法支持，保留no_legal_support状态，不从test内容借样本。
5. 由真实物理样本索引检查支持与query的EEG访问不重叠；覆盖五个一秒窗的联合[-600,1200)ms访问及segment-start规则。若需边界guard，只按冻结几何排除非法支持边界，不随结果改query。声音content/UID也必须符合既定fit/test分离。
6. 支持选择与干预拟合不读取query的标签、EEG、风险或组差。目标query的当前声音/历史只在规定最终评分中使用；它不是个人参数选择的数据。
7. 所有条件输出相同query_hash及显式support_hash、source_fit_content_hash；没有合法支持时保留该人的H0/E0，HP/EC/ET标为not_estimable_no_legal_support，不将未更新基线冒称个人拟合结果，不删除人或偷偷换支持协议。

旧 support_contract.dtu_split 在同一role内取前30%段、后70%段，见66–85行；support_coverage.py:133–146对outer直接传test role。该规则不能满足本轮跨内容支持定义。新实现保留其物理guard、ID和访问记录思想，**不能直接调用它后把结果标为本轮自然U30**。

旧content_time cache只有source fit/ES与outer test，缺outer人的fit内容特征。新公共提取器须补这部分，并复用已有兼容的目标query特征；使用新的cache identity及访问元数据，不把额外支持行塞回旧cache冒充原输出。

新FAU排组模型的60个目标fold评估可以共用12份权重和对应特征库。FAU pooled/DTU旧模型只按各自原outer fold绑定；它们的20份不同source不能因新模型可去重而随意合并。

## 4.6 私有AP/APwrong来源与history接口

本轮10个核心私有bundle只绑定 ALN3.5 matched AP/APwrong 的同修订sampler、同曝光/目标合同、同seed、同outer fold配对。不能用旧prior_science里的原AP替换matched AP，再与新APwrong构造所谓纯配对消融。

可复用入口：

- auditory_alignment_v3/aln35/ap_wrong.py：matched donor/target来源链；
- auditory_alignment_v3/aln34/prior_science.py 与 private_current_time.py：冻结特征提取、实际trial与时间访问；
- auditory_alignment_v3/aln35/history_interface.py:120–164：B0、等接口校准B1、EEG offset logistic、strict异block twin；
- auditory_alignment_v3/aln35/support_contract.py:30–63：私有物理block支持/query边界；
- auditory_alignment_v3/aln35/science_binding.py：真实query身份、roster及来源哈希。

Server须核对matched来源是否已经有兼容逐trial特征；没有则补冻结前向，不重新训练兼容模型。可选S只在接口、trial与query完全兼容时增加5个评估bundle；缺失只标明该补充参照，不阻塞AP/APwrong主比较，也不为S另开新训练族。

私有数据没有公共连续语音那样的独立声音内容合同。这里明确为“新儿童＋独立物理block/固定query＋history受控”，不称未见声音内容泛化。history表、校准、EEG与twin拟合必须遵守各自source/support权限；strict twin在支持拟合时只能从支持内的同history、异block、非自身trial建立，不能从query借partner。缺合法twin保留为显式缺项，不能用同block或self回退。

## 4.7 旧pooled、DTU、已有科学读出的用途

FAU旧pooled的20份结果是有用的描述性参照。新排组source与旧pooled在人群规模、预处理/选择版本等方面不同；不得把 pooled − excluded 的差值解释成听觉组信息的因果效应或纯粹同组数据价值。本轮主科学比较在固定新source、固定目标query内形成：真实声音与适当历史/错配参照、固定共同读出与个人干预。

DTU旧source与原FAU pooled的query/目标读出可按兼容签名复用，但新自然U30需要新输出身份。新结果来源字段同时保留parent执行、旧预处理、当前支持定义和当前统计版本。

公共 content_time.py 的共同ridge与5×5宽窗TG、SCI_R2的严格raw时间参照、私有SCI_R1的raw/latent lag都已存在。复用这些工具完成本包指定的有限时间问题；不得按outer峰值挑窗口，也不以新包为由重做全部模型×特征×窗口矩阵。宽窗中心和遮罩敏感性不命名为单点神经潜伏期。

## 4.8 实施顺序、工程完成条件与资源

建议在独立ALN3.6模块中依次完成：不可变来源binding → 合法source索引/统计与训练签名 → 新source训练/true-NLL选择 → 一次冻结支持/query特征提取 → 固定读出干预 → 逐人汇总与本包规定的成对推断。实际模块和CLI在实现完成后写入接入回执；本文件不提供虚构可运行命令。

足够的工程检查是：

1. 三种目标组均验证完整源排除，特别覆盖leave-TH的dev身份；fit/ES/query角色及内容集合与manifest一致。
2. 所有normalizer、audio head、概率参数及history/条件残差具有合法拟合ID；目标组没有进入source梯度、统计或checkpoint选择。
3. local/CB两工具各一次代表运行确认实际EEG访问、完整parent日程与trainable参数/梯度更新ledger；CB不得重现旧prefix-only更新。
4. 固定source-ES candidate索引、风险值与独立直接概率计算一致；不得将gain写成NLL。完成不依赖风险方向。
5. 12份默认source与60个评估cell映射可验证；不会重复训练同一签名，不会给一个目标人制造五个独立观测。
6. U30/Q物理访问、声音内容及所有干预的query hash一致；个人拟合不得访问Q。
7. 私有matched AP/APwrong来源与trial/history/twin限制可验证；旧local全零pre不再作为真实刺激前证据。
8. 规范逐人输出能通过现有有限数值、重复行、完整性和角色校验；缺失与nonregular显式输出，不要求统计显著。

检查覆盖上述实际风险后立即执行完整已授权单元，不追加泛化“安全审计”、论文框架批准或科学绩效门槛。失败只冻结受影响签名及真实下游，保留失败回执与其他有效结果；修复产生新版本。

全项目运行GPU总数继续最多10张，包含旧尾巴、新source、冻结提取和工程probe。CPU读出/统计独立调度；不为多个lane分别申请10张。只操作本项目精确归属的jobs，保留旧在跑源码与现有holds。

R1/R2各默认12次新source训练；60/seed是评估格数。旧时长只能作估算依据，不能写成新包完工承诺：现成FAU content/time单元约37–41秒，旧FAU倍预算训练样本CB约1786秒、local约382秒，硬件/缓存/预算不同。首个代表完整新source记录训练、true-NLL评价、特征提取、IO和CPU拟合成本后更新剩余估算；不得为节省时间削弱local parent或偷偷扩展训练预算。

## 4.9 Server必须形成的最小绑定与回执

在现有私有输出根下建立独立aln36目录，具体绝对路径由server绑定，不将公开包里的示意路径当现场路径。至少保存：

- 来源与代码binding：实际Git HEAD、parent records/checkpoints、通用CB初始化、stageB/声音特征/roster与角色manifest哈希。
- source manifest：每组/内容/工具/seed的合法源ID、fit/ES/cal样本、所有统计拟合权限、原parent日程、source_training_signature与去重映射。
- evaluation manifest：110个R1评估bundle（兼容S时115）的预期身份、content folds、source checkpoint、U30/Q/twin binding及actual access；R2单独记录seed重复，不能增加独立n。
- 实现与工程回执：真实CLI、版本、smoke与production区别、训练ledger、风险选择轨迹及实际成本。
- 科学输出：所有有效方向的逐人结果、完整/预期覆盖、失败/缺失/nonregular、直接成对差，以及旧pooled参照的限定解释。

旧records、旧统计主分析和旧研究结论保留。新包中的合成验证只验证接口与计算，不能填入以上生产结果。个体级既有授权字段继续沿用，无需重复询问；原始EEG、身份映射、逐trial原始记录及私有权重不因本包新增公开授权。
