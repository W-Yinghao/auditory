# 2. 时间标记的传统 CS 与支持适配

## 2.1 输入表示

对声音锚点 i，从实际 EEG 构造 W0=[−200,200)、W1=[0,400)、W2=[200,600) ms 三个窗口。分别调用同一 EEG backbone，保留通道身份，不允许跨窗 attention 后再把 token 命名成局部时间。物理访问见第3章。每个声音视图 v∈{env,ss,sc} 使用一个跨窗口共享的32维 EEG线性投影和现有固定32维声音head，两个模态各自 L2 normalize。

令 U_i,k 为某个视图的EEG投影，A_i为同一锚点音频表示，q=softmax(a+δ) 是一个人episode内所有锚点共用的三维权重。a 是学习的群体prior logits；δ是仅由该人支持集更新、每个episode重置的个人偏移。q不是神经潜伏期分布，也不是每个trial按声音自适应的注意力。

## 2.2 分布与精确定义

以离散时间标签 T 的 counting measure 和连续高斯 KDE 定义 p(U,T,A)，时间分量k质量q_k/n。比较联合密度与其边缘乘积的传统 Cauchy–Schwarz divergence。每个视图、每个人分别计算，不把人混合后让身份相关性冒充共同声音关系。

设 K^k_ij=exp(−||U_i,k−U_j,k||²/(2σ_u²))，L_ij=exp(−||A_i−A_j||²/(2σ_a²))，则

\[
A_k=n^{-2}\sum_{ij}K^k_{ij}L_{ij},\quad
B_k=(n^{-2}\sum_{ij}K^k_{ij})(n^{-2}\sum_{ij}L_{ij}),\quad
C_k=n^{-3}\sum_i(\sum_jK^k_{ij})(\sum_jL_{ij}).
\]
\[
D_{TCS}=\log\sum_k q_k^2 A_k+\log\sum_kq_k^2B_k-2\log\sum_kq_k^2C_k.
\]

这是 p(U,T,A) 与 p(U,T)p(A) 的经典CS，不是新divergence、不等于Shannon互信息的bits估计、不是条件MI的chain rule，也不是 Σq_k D_k。每个视图内所有窗口必须共享 EEG σ_u、维度和尺度，否则窗口间被省略的Gaussian归一化常数不能抵消。σ是**overlap kernel**标准差，等于KDE component标准差的√2倍。

完整保留对角项；不用Gram中心化、不删nearby pair、不加入InfoNCE mask、不按得分截断到0。float64 log-domain求和；有限值退化如实记录，数值溢出修复。每人 query 只有32个anchor，不能将三窗展开的96行称为96个独立样本。

初始 source-fit 面板下校准带宽并冻结：每个view将三窗EEG合并，仅取**同一window内不同anchor**的全部非对角距离汇总，取lower median作为一个共同σ_u；audio同理得到σ_a。不是每窗各取σ。若距离全部为0或σ不正，按数值/表示就绪故障查因；不得用target结果调bandwidth。乘子固定1。GCS在均匀q下先池化再归一，单独校准其一个EEGσ；audioσ复用。诊断需记录距分布、kernel均值/有效秩以及GCS池化前norm，避免相消被隐瞒。

## 2.3 支持适配与一阶训练

每个update抽2个人；每人32 support和32 query。先从support求δ，再从query更新backbone、投影和群体a。初始a=0；δ每次从0开始，只更新三个logits并减去其均值。

inner目标：三视图均值 L_support + (0.1/2)||δ||²；5步梯度下降、步长0.1。inner只读support；其特征和a均detach。outer使用 live backbone/a、q=softmax(a+stopgrad(δ_final))，两人query loss等权平均，另加0.01 KL(softmax(a)||Uniform(3))。这是明确的一阶surrogate，不声称 exact bilevel differentiation。原生实现不需要对torch.cdist求二阶梯度。

| Arm | query/support目标 | 时间信息与适配 |
|---|---|---|
| B0 | 无Stage2 | 同Stage1，q0均匀 |
| TCS | −D_TCS，三view等权 | 带时间标签的分布，支持更新δ |
| TNCE | Σq_k L_NCE,k，三view等权 | 同三窗/同S/Q/同一阶δ步骤；不是pooled NCE |
| GCS | −D_CS(L2(Σq_k U_k), A) | 同三窗/同S/Q/同δ步骤，只在依赖估计前做pooling |
| TCS_WRONG | 与TCS完全相同 | 同EEG、预算/超参数，跨family错配整套audio row |

TNCE温度0.1，采用仓库已经修正的symmetric masked multi-positive NCE。正例包含对应锚点；同内容的合法多正例按既定规则登记，same-family ±2s的其他近邻不作负例。每个方向分子/分母和无合法负例情况必须可审计。不能把这些masks传入CS。TCS、TNCE和GCS都有支持适配，比较不能被“只有新方法得到支持”混淆。

wrong在每人support/query各自构造跨family双射置换，三个audio view使用同一行置换；保持音频边缘和各view之间关系，破坏与EEG的对应。11/11/10的family计数允许无同family匹配；每episode重新确定，保存seed及mapping hash，不能同一固定映射跨epoch形成新可学的词典。

## 2.4 真正的贡献候选

CSAligner等已有工作已研究CS跨模态对齐，不能以“首次CS对齐”作为创新。候选方法贡献是：以听觉时间访问为显式变量构造依赖；在人内计算、在人间学习；训练时用支持/query分离压力，使一个低维个人组织变量可被使用；在EEG-only目标上区分共享内容、读出变换和支持校准。

这一设计不保证可识别的生理分解，也不自动解决年龄/听力confounding。q和q²归一化权重、log A/B/C及per-slot score都导出，但q峰值不能当响应时间；时间表型来自held-out读出曲线、重拟合恢复与稳定性。冻结读出同时报告使用q0与同头均匀权重重置，识别源prior究竟是否参与了收益。

## 2.5 转移内容

源→目标传EEG backbone θ和群体a。源64通道audio投影不直接套在20通道儿童上；保存用于源诊断，目标建立共同新head。query的真实audio从不进入EEG encoder。公共attention评分可以访问两个候选audio，但应明确这是候选可见的应用场景。

R1目标测试人δ=0。儿童全FT允许用外层训练儿童更新θ和群体a，所有臂相同；它不是测试儿童适配。R2儿童支持δ使用已获支持标签的CE，和源侧有paired audio的CS适配是不同的监督入口，不能称无标签TTA。年龄冻结probe只读backbone的有序三窗特征，使用δ=0且不用q缩放；不把会被后续标准化抵消的q乘法写成方法作用。
