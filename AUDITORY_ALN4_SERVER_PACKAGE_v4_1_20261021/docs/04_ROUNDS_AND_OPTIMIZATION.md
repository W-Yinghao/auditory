# 4. 有限优化与三轮收束

## 4.1 R1：方法及科学接口一起跑通

Stage1通过第7章资产核验后，在所有arm/seed间冻结身份。R1 seed3401。每个view/sourcehead初值、群体a=0、batch流与crop处理成对一致。全backbone从第一步更新；不得再用历史prefix-update配置冒称full。

六个短校准：TCS/TNCE/GCS × LR{1e-4,3e-4}，各1000updates。source-fit/dev各固定512合法anchor面板，seed3420；尽量均衡人和内容，确切ID和hash冻结。共同probe取原始backbone三窗tokens按固定slot/channel顺序串联；用fit面板逐维标准化，ridge λ=1e-3 trace(XXᵀ)/n、train截距，预测三view标准化原始声学特征；dev normalized MSE三view等权选LR，精确相同取1e-4。不用各loss自己的native score，不用儿童/DTU/FAU测试。

若两个LR候选都仅因有限值完全退化使probe不可辨，固定LR1e-4并标`uninformative_selection`；NaN/错位/漏梯度是工程故障，不能用这个fallback遮掩。TCS_WRONG继承TCS LR和带宽，不自行调参。

四个生产训练从相同Stage1/head随机初值重新开始，各10000updates；AdamW、weight decay1e-4、cosine LR、clip global norm5。主transfer固定final10000步，保存0/2500/5000/10000及resume；源dev/native loss、共同probe、核谱、表示rank和梯度是诊断，不按臂挑不同最佳epoch。总优化量是6000短校准+40000生产updates；三crop和inner/outer计算成本完整计入，不能与旧一秒单forward用相同“step数”冒充相同算力。

每person64anchor、每update2人、3crop→384 crop forwards的逻辑规模，支持特征可缓存于同update的inner步骤，但outer query必须保持有效梯度。显存不足按确定顺序microbatch backbone并重组完整每人Gram；不能缩小CS的n或把microbatch CS平均当同一估计。记录dropout/RNG与forward顺序，断点恢复需等价。

| R1项目 | 固定范围 | 计数/约束 |
|---|---|---|
| source短校准 | 3objective×2LR | 6fits |
| source生产 | TCS/TNCE/GCS/TCS_WRONG | 4fits |
| 冻结表征/内容/时间 | 5arms×DTU/FAU/private，各自既有fold | CPU heads与exports逐单位展开；不是15次encoder训练 |
| private CE full FT | B0/TCS/TNCE×5fold | 15fits |
| frozen age | core3 + raw EEG ridge + train-mean | 若5outer/4inner/5alpha，4ridge模型共420次小CPU拟合，另5trainmean；不含新backbone训练 |
| attention | core3×DTU/FAU | 20s主，5/10s由同margin描述性导出 |
| 旧跨刺激/age intake | D2/GX/NEXTMAP与私有roster | 读原资产，无新encoder训练 |

## 4.2 私有充分微调的共同配方

core3全部使用三窗共享backbone、每slot相同结构但独立参数的channel-aware signed spatial readout(k8/e32,d32)+2class linear CE classifier；同fold/seed的随机head初值一致。概率p=Σ softmax(a)_k p_k，loss为真实标签−log p_y；用logsumexp计算混合，不把logits平均冒称概率混合。全θ与a从首步可训练，测试人δ=0。对比的是有无源训练的初始化影响；新target训练可覆盖源prior，需导出前后a、θ变化和slot结果。

AdamW，backbone/readout/a LR均1e-4，wd1e-4（logits/bias/norm参数wd0，所有arms同一参数组规则），batch64，100epochs，cosine，clip5。每epoch updates=ceil(N_fit_trials/64)，先均匀抽训练儿童，再在该儿童内按自然trial分布抽样；不把类别强行均衡为50:50。所有arms跑完共同预算，选每儿童等权ES true-label NLL最低的epoch（含epoch0，tie早者）；最后状态也保留，test完全不参与。ES/fit标签访问分别计数。

输出每儿童AUC、NLL、Brier、BA(阈值.5)、原始类别比例、三slot概率和q0混合概率。主科学分析仍包含frozen比较与history/twin，不用全FT AUC替代所有端点。GCS/wrong在R1只做冻结科学对比，不补成25个private FT；后续若需要其FT说明机制，使用唯一消融预算槽并预先登记。

## 4.3 R2：复现、有限适配与一个跨刺激问题

seed3407/3413重复四条原始source生产（8fits），不重选LR，不根据R1测试结果删弱臂；重复核心3×5fold私有FT（30fits），冻结主科学端点也重复。R1提供优化诊断，若确有实现故障，修复受影响版本而非把出错结果并入主seed平均；如果只是预算未收敛，报告而不自动扩展至无限训练。

个人支持问题只用core3：既定U0/U10/U30合同、相同query，对照低维时间δ与概率校准。U10的n10=min(floor(0.1×全部available trials数), guarded early-support-pool大小)，不是支持池的10%；U30是最早ceil(0.3×物理block数)经过边界删除和guard后的全部pool，**不是10/30trials或秒**。U10固定原取样seed351410…351414，不用标签覆盖挑选support；五次支持抽样先在同人内平均，不增加人口n。沿用support_contract的pool/query、边界trial排除、完整EEG访问guard；允许的query一次固定。δ以每个arm/fold选定的private CE checkpoint为底座，从其a_target出发、每个新儿童δ=0重置；θ与三slot heads冻结，用支持标签CE更新δ。对照是同checkpoint混合概率的二参数正斜率affine-logit校准 pcal=sigmoid(exp(s)×logit(p)+b)，s=b=0起步、同支持上更新，penalty=(0.1/2)(s²+b²)，五步梯度下降lr0.1；仅logit计算将p固定截于[1e-6,1−1e-6]，对所有臂相同并登记。支持不足/单类不丢该人，按事先无更新fallback并记录。δ固定五步/lr0.1/L2系数0.1，不称待调的起点；校准与δ均只用support。主适配端点为共同query NLL，Brier与AUC作补充；affine校准通常不改变排序，不能仅凭AUC差异宣称优于校准。所有参数在R2 query评价前冻结。

跨刺激问题只占一席：优先选经身份/标签审核后可共享“当前声音身份或deviance关系”的两个刺激lane，在源lane训练冻结表示的读出并测试另一lane，再做同一表示的目标训练侧重拟合，区分关系可用与读出可复用。若标签语义不可共享，就改为两个lane各自训练读出并比较同儿童的时间/历史条件表型，这叫跨刺激表征评估，不能冒称zero-shot分类。两种问题只能在**查看新结果之前**由资产语义决定一个，并留选择记录；不取结果较好的路线。样本过少时报告配对描述，不新增未批准队列。

## 4.4 R3：外部比较和结束

固定一个外部方法席位：优先完整MindMix在其可忠实支持的共同公共听觉任务上比较；若资产/输入/依赖不能恢复，则以Transformer-CLIP替代这个席位。R1 intake先绑定可行路线与失败条件，不到R3看本方法成绩再选对手。同backbone TNCE不是完整MindMix，提取MindMix EEG-only encoder只是初始化/probe，二者必须标清。

整个R2/R3合计只有**一个可选方法消融槽**，上限3个source fits+15个private FT；例如无episode支持适配，或补GCS target FT，按最终想支持的单一主张选择，不能两个都做。该槽不是默认开满。外部方法若需独立source训练最多3seed、目标FT最多5fold×3seed；在输入不支持儿童时只做忠实公共比较，未用预算不转给其它模型。无新增架构×loss×window sweep，无R4。

最终报告依据内容特异性、时间读出、群体/个人变化和实际用途决定贡献的强度。统计不显著不触发反复训练；有效负结果保留。若方法组件不必要，删去对应必要性主张，保留成立的研究发现。
