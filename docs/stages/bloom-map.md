# 能力地图

你已经做过第 0 天的小实验，或者你已经知道自己要干什么。这一页用来对号入座：我现在会到哪一层，下一节点哪里。

这六层有个学名，叫布鲁姆。你不用先记住这个名字。把它想成爬楼：先能叫出名字，再能讲清为什么，然后亲手做一次，再拆开看它为什么漂，然后在两种方案里做选择，最后做出别人能复现的东西。

**口诀**　先叫出名字，再讲清为什么，然后亲手做一次。

**练完你会怎样**：你能指出自己停在哪一层，并点开那一层的第一节，而不是把七个阶段从头刷到尾。

第一次学习时，先走 [24 课连续课程](../course/index.md)，按每三课的作品判断进度；这张能力地图用于查缺与进阶，不要求一次完成所有层级。

已经有具体目标的，直接去 [按目标选路线](按目标选路线.md)，不必先把六层读完。

阶段 0–6 仍是练习场的默认顺序。电路详解和 `code/` 按层挂在下面，不另起一条路线。

⚠️ **锂电池实验有真实火灾风险。** 碰真电池前先备护目镜与防火垫。安全纪律与器材见 [预算清单](../budget.md) 与 [阶段 2](stage-2-保护板实践.md)。本页出现的阈值都是示例，以电芯和芯片 datasheet 为准。

## 本页目录

- [怎么用](bloom-map.md#怎么用)
- [记忆](bloom-map.md#记忆)
- [理解](bloom-map.md#理解)
- [应用](bloom-map.md#应用)
- [分析](bloom-map.md#分析)
- [评价](bloom-map.md#评价)
- [创造](bloom-map.md#创造)
- [练习场、电路与代码](bloom-map.md#练习场电路与代码)
- [小节模板约定](bloom-map.md#小节模板约定)

## 怎么用

1. 选一层，读那一层的一句话目标。
2. 点「第一入口」做完，再做自检。做不出就留在这一层。
3. 六层是累积的。应用层默认你认得前面的词，也讲得清前面的机制。

改标题造成的旧锚点见 [迁移表](bloom-migration.md)。零基础的入口不在这一页，在 README 的第一步。

## 记忆

**能做什么**：说得出电芯电压红线、五大保护的名字和断口、保护板上的器件叫什么。

**入口**

- 第一入口：[阶段 0 §0.1.5 必背参数表](stage-0-前置知识.md#015-必背参数表-记忆)
- [阶段 1 §1.4 五大保护名词与断口](stage-1-认识BMS.md#14-五大保护名词断口与三要素-记忆)
- [阶段 0 §0.3.1 MCU 外设名字](stage-0-前置知识.md#031-bms-用到的-mcu-外设按用途记-记忆)
- [详解④ §0 参数速查](../circuits/04-系统安全与量产.md#0-参数速查-记忆)
- 生词：[术语表](../glossary.md)

**自检**：合上资料，默写三元锂和磷酸铁锂的满充电压，并说出 OVP、UVP、OCP、SCD、OTP 各断充电还是放电。说不出就留在这一层，先别做板。

## 理解

**能做什么**：讲清电池为什么怕过充、过放和低温充电，以及 BMS 的模块、形态、保护为什么要延时。

**入口**

- 第一入口（零基础从这里）：[阶段 0 §0.1.1 一块电池里在发生什么](stage-0-前置知识.md#011-一块电池里在发生什么-理解)
- [阶段 0 §0.1.2 过充链条](stage-0-前置知识.md#012-过充一场逐级升级的事故-理解) · [§0.1.6 CC-CV](stage-0-前置知识.md#016-cc-cv充电的两段论-理解)
- [阶段 0 §0.1.8 固态电池](stage-0-前置知识.md#018-固态电池固体电解质换掉了什么-理解) · [§0.1.9 碳纤维结构电池](stage-0-前置知识.md#019-碳纤维结构电池电极在承力外壳是另一件事-理解) · [§0.1.10 钠离子](stage-0-前置知识.md#0110-钠离子硬碳和另一套电压窗口-理解) · [§0.1.11 钠离子规格书](stage-0-前置知识.md#0111-公开规格书里的钠离子保护要求-理解) · [包级手册缺口](../t13-包级手册缺口.md)（读完液态锂电再看；包级寄存器仍缺）
- [阶段 1 §1.2 木桶效应](stage-1-认识BMS.md#12-木桶效应亲眼看看浪费有多大-理解) · [§1.3 五大模块](stage-1-认识BMS.md#13-bms-的五大功能模块-理解) · [§1.6 三种形态](stage-1-认识BMS.md#16-bms-的三种形态-理解)
- [阶段 1 §1.4b 每条保护背后的事故](stage-1-认识BMS.md#14b-五大保护每一条背后都有一个事故-理解)
- [详解① §1.2 为什么必须两颗背靠背](../circuits/01-功率回路-MOS保护与预充.md#12-为什么必须两颗背靠背-理解)

**自检**：用自己的话说明，为什么四串电池不能只看总电压，以及保护板和智能 BMS 差在哪。讲的时候要出现「最弱的那一节」和「有没有 MCU」。

## 应用

**能做什么**：不靠真电池虐待，也能触发一次保护；或在 PC 上把估算器、帧解析、状态机跑起来。

**入口**

- 第一入口（有万用表、还不敢接电池）：[阶段 2 §2.6 保护板实测](stage-2-保护板实践.md#26-保护板实测方法本阶段核心技能-应用)
- [阶段 2 §2.1 先拆一块板](stage-2-保护板实践.md#21-先拆一块板子看-应用)
- [阶段 3 §3.4 固件架构](stage-3-AFE-MCU智能BMS.md#34-固件架构四层--一台状态机-应用) · [§3.7 先模拟后真电池](stage-3-AFE-MCU智能BMS.md#37-调试流程先模拟后真电池-应用)
- [阶段 5 §5.2 UART](stage-5-通信与集成.md#52-uart商用-bms-的方言普通话-应用)
- 代码入口：[soc 跑起来再分析](../../code/soc/README.md) · [protocol 帧解析](../../code/protocol/README.md) · [firmware 状态机](../../code/firmware/README.md) · [阶段 6 §6.2.5 快照回放](stage-6-精通与毕业项目.md#625-故障注入与快照回放-应用)
- [详解① §3.2 预充计算](../circuits/01-功率回路-MOS保护与预充.md#32-解法与计算-应用)
- [详解⑤ 电路板绘制与设计要点](../circuits/05-BMS电路板绘制与设计要点.md) · [阶段 3 §3.6 五条纪律](stage-3-AFE-MCU智能BMS.md#36-原理图与-pcb五条纪律-应用)

**自检**：不接真电池，说出过充保护怎样用分压链触发一次并记下阈值；或者在 PC 上跑通 `code/soc` 的 `compare.py`，指出三条曲线从哪一拍开始分叉。

## 分析

**能做什么**：把「数不准、电量会漂、帧对不上」拆成可核对的原因，而不是换一块板碰运气。

**入口**

- 第一入口：[阶段 4 §4.2 安时积分为什么会漂](stage-4-SOC-SOH算法.md#42-安时积分库仑计主力但它会梦游-分析)
- [§4.3 OCV](stage-4-SOC-SOH算法.md#43-ocv-法好尺子但经常够不着-分析) → [§4.4 等效电路](stage-4-SOC-SOH算法.md#44-等效电路模型让电压在动态中也能用-分析) → [§4.5 卡尔曼](stage-4-SOC-SOH算法.md#45-卡尔曼滤波两个不完美信息源的联姻-分析)
- [详解② §1 采样链误差预算](../circuits/02-采样链与AFE芯片.md#1-采样链全景与误差预算-分析) · [§4 开线](../circuits/02-采样链与AFE芯片.md#4-开线检测采样线断了会发生什么-分析)
- [阶段 5 §5.6 协议逆向](stage-5-通信与集成.md#56-协议逆向方法论当一回协议侦探-分析) · [§5.4.1 握手](stage-5-通信与集成.md#541-gbt-27930充电机与-bms-怎么握手-分析)
- [阶段 0 §0.2.4 三种电流采样的代价](stage-0-前置知识.md#024-电流采样三条路线-分析)
- 代码走读：[soc 为何分叉](../../code/soc/README.md)

**自检**：解释 1 mA 零漂为什么会让纯安时积分越走越偏，以及采样误差预算里为什么先看基准源而不是先加 ADC 位数。

## 评价

**能做什么**：在两种都说得通的方案里做取舍，并说出安全边界：什么不能交给通信芯片。

**入口**

- 第一入口：[按目标选路线](按目标选路线.md)（六条捷径，每条标了层）
- [阶段 3 §3.5 高边还是低边](stage-3-AFE-MCU智能BMS.md#35-高边与低边保护开关挂在哪一头-评价)
- [阶段 6 §6.4 以过充走一遍功能安全](stage-6-精通与毕业项目.md#64-功能安全落地以过充为例走一遍-评价) · [§6.4.1 开线被当成过充](stage-6-精通与毕业项目.md#641-过充案例开线被当成过充-评价) · [§6.2.6 云端停在包外](stage-6-精通与毕业项目.md#626-云端诊断停在包外-评价) · [§6.5.1 错芯](stage-6-精通与毕业项目.md#651-产线追溯错芯和贴错标-评价) · [详解③ §3.1 均衡路径](../circuits/03-充电均衡与计量.md#31-同一模型下的拓扑对比-评价)
- [阶段 6 §6.1.6 BMS 与热管理的边界](stage-6-精通与毕业项目.md#616-bms-与热管理tms的边界-评价)
- [阶段 6 §6.6b 毕业项目评审量规](stage-6-精通与毕业项目.md#66b-毕业项目评审量规-评价)
- [详解① §1.4 高边还是低边](../circuits/01-功率回路-MOS保护与预充.md#14-高边还是低边开关挂在回路哪一头-评价)
- [详解④ §3 功能安全落地](../circuits/04-系统安全与量产.md#3-功能安全落地iso-26262-从纸面到电路-评价) · [§2.3 不许带大电流分断](../circuits/04-系统安全与量产.md#23-不许带大电流分断-评价)
- [详解③ §3 主动均衡选型](../circuits/03-充电均衡与计量.md#3-主动均衡把水桶换成搬运工-评价)（定量对比仍待补，见任务板 T8）

**自检**：有人要做 4 串、只要保护；另一个人要做 16 串、要 SOC 和 CAN。你给两种不同的形态，并说出 ESP32 为什么不能参与断开决策。

## 创造

**能做什么**：按一份写死的需求，做出别人能复现的 BMS 作品，或给这份教程补上还缺的证据。

**入口**

- 第一入口：[阶段 6 §6.6 毕业项目指南](stage-6-精通与毕业项目.md#66-毕业项目指南-创造)
- 做完用 [§6.6b 评审量规](stage-6-精通与毕业项目.md#66b-毕业项目评审量规-评价) 自评
- [阶段 6 §6.8 毕业验收](stage-6-精通与毕业项目.md#68-毕业验收-评价)
- 还没准备好做整机：从 [共建任务板](../共建任务板.md) 认领一条（实测回传、待补证据、导读）

**自检**：按 §6.6 的需求模板写下你自己的一行：串数、化学体系、保护清单、算法、通信。然后在评审量规里指出你准备打到「达标」还是「良好」，以及还缺哪一条证据。

## 练习场、电路与代码

| 去哪 | 干什么 |
|---|---|
| [阶段 0](stage-0-前置知识.md) → [1](stage-1-认识BMS.md) → [2](stage-2-保护板实践.md) → [3](stage-3-AFE-MCU智能BMS.md) → [4](stage-4-SOC-SOH算法.md) → [5](stage-5-通信与集成.md) → [6](stage-6-精通与毕业项目.md) | 练习场，默认顺序 |
| [电路详解目录](../circuits/README.md) | 六篇深潜，动画旁标了层级 |
| [code/](../../code/README.md) | 三个 PC 可跑入口 |
| [学习路线总纲](../bms-resources.md) | 资料海。零基础不要从这里开始刷链接 |
| [锚点迁移](bloom-migration.md) | 旧笔记对不上新标题时来这里 |

## 小节模板约定

新小节标题末尾加一层：`[记忆]` `[理解]` `[应用]` `[分析]` `[评价]` `[创造]`。

混进了两层就拆开。暂时不能拆，在节首写 **先读/后读**，写明哪几段是哪一层。评价和创造不要写进记忆节。

节末三件套，放在正文后面：

> **原理**　机制，不是只有步骤。
> **证据**　datasheet、标准、论文，或可复现实验 / 仿真的链接。
> **延伸阅读**　可选加深；英文资料标可选。

没有把握的证据就写明 **待补证据**，并在 [共建任务板](../共建任务板.md) 加一条。不要编一个看起来像论文的链接。

标题一改，锚点就变。改完把旧 → 新写进 [迁移表](bloom-migration.md)。

---

[README 第一步](../../README.md#从这里开始零基础) · [迁移表](bloom-migration.md)

## 知识点梯子入口

<!-- kp-bloom:start -->
下面的入口由 `curriculum/concepts.json` 的 `ladder` 生成：每层落到知识点的同名梯子级，不再只是散落的小节目录。`分析 / 评价` 合并到 L4，`创造` 对应 L5。

### 记忆（梯子 L1）

| 阶段 | 知识点 |
|---:|---|
| 0 | [三根探针](../核心问题地图.md#kp-three-probes-l1) · [电压窗口看化学体系](../核心问题地图.md#kp-chemistry-voltage-window-l1) · [倍率换成安培](../核心问题地图.md#kp-c-rate-current-l1) · [电压到顶不等于充满](../核心问题地图.md#kp-charge-termination-l1) · [SOC分母会变](../核心问题地图.md#kp-soc-capacity-denominator-l1) · [深放不靠激活补救](../核心问题地图.md#kp-deep-discharge-triage-l1) · [正极材料决定性格](../核心问题地图.md#kp-cathode-family-traits-l1) · [离子走里电子走外](../核心问题地图.md#kp-ion-electron-paths-l1) · [带载掉压](../核心问题地图.md#kp-load-voltage-drop-l1) · [过充链](../核心问题地图.md#kp-overcharge-chain-l1) |
| 1 | [木桶效应](../核心问题地图.md#kp-weakest-cell-l1) · [串抬压并加容量](../核心问题地图.md#kp-series-parallel-taps-l1) · [五大功能与一拍时间](../核心问题地图.md#kp-bms-five-modules-l1) · [五大保护与断口](../核心问题地图.md#kp-five-protections-table-l1) · [每条保护的事故来源](../核心问题地图.md#kp-protection-accident-origin-l1) · [温升速率先抬头](../核心问题地图.md#kp-dtdt-early-warning-l1) · [三种形态怎么选](../核心问题地图.md#kp-bms-three-forms-l1) · [保护三问写成状态机](../核心问题地图.md#kp-protection-state-machine-l1) · [均衡是细流不是大河](../核心问题地图.md#kp-balance-current-scale-l1) |
| 2 | [保护去抖](../核心问题地图.md#kp-protection-debounce-l1) · [认板上五类器件](../核心问题地图.md#kp-board-parts-id-l1) · [同口分口与端子](../核心问题地图.md#kp-terminal-port-topology-l1) · [DW01三道判断题](../核心问题地图.md#kp-dw01-three-judgements-l1) · [回差与确认时间](../核心问题地图.md#kp-ov-hysteresis-recovery-l1) · [多串为何不能摞](../核心问题地图.md#kp-multicell-floating-channels-l1) · [过流分档与I²t](../核心问题地图.md#kp-oc-tiers-i2t-l1) · [背靠背驱动与发热](../核心问题地图.md#kp-mos-drive-and-heat-l1) · [NTC位置与温度窗](../核心问题地图.md#kp-ntc-placement-temp-window-l1) · [分压链实测与记录](../核心问题地图.md#kp-protection-bench-record-l1) |
| 3 | [测量预算](../核心问题地图.md#kp-measurement-budget-l1) · [感知决策分工](../核心问题地图.md#kp-afe-mcu-split-l1) · [一颗ADC轮流扫](../核心问题地图.md#kp-mux-scan-budget-l1) · [误差要逐截垒](../核心问题地图.md#kp-sampling-error-budget-l1) · [CRC与寄存器快照](../核心问题地图.md#kp-afe-crc-register-read-l1) · [均衡关断后的回弹](../核心问题地图.md#kp-balance-settle-window-l1) · [高压从板与隔离](../核心问题地图.md#kp-hv-daisy-isolation-l1) · [故障锁存与快照](../核心问题地图.md#kp-fault-latch-recovery-l1) · [周期预算与喂狗](../核心问题地图.md#kp-loop-slack-watchdog-l1) · [高边低边怎么选](../核心问题地图.md#kp-highside-lowside-choice-l1) · [分级上电与开线](../核心问题地图.md#kp-bringup-ladder-openwire-l1) · [原理图五条纪律](../核心问题地图.md#kp-pcb-five-disciplines-l1) |
| 4 | [安时积分漂移](../核心问题地图.md#kp-soc-drift-l1) · [OCV 可信度](../核心问题地图.md#kp-ocv-trust-l1) · [HPPC 辨识](../核心问题地图.md#kp-hppc-identification-l1) · [SOP 取最小](../核心问题地图.md#kp-sop-minimum-l1) · [SOC四个捣蛋鬼](../核心问题地图.md#kp-soc-four-troublemakers-l1) · [三个锚点的条件](../核心问题地图.md#kp-soc-anchor-conditions-l1) · [零偏与分流温漂](../核心问题地图.md#kp-shunt-offset-tempco-l1) · [增益把信任分出去](../核心问题地图.md#kp-ekf-gain-trust-l1) · [容量与内阻双指标](../核心问题地图.md#kp-soh-dual-indicators-l1) · [局部窗口与dQdV](../核心问题地图.md#kp-soh-window-and-dqdv-l1) · [低温降额不硬充](../核心问题地图.md#kp-temp-derate-charge-l1) · [落地要点与验收](../核心问题地图.md#kp-soc-engineering-landing-l1) · [仿真当裁判，不当签字](../核心问题地图.md#kp-sim-referee-not-signoff-l1) · [参数要带窗口](../核心问题地图.md#kp-param-window-reporting-l1) |
| 5 | [帧状态机](../核心问题地图.md#kp-protocol-resync-l1) · [通信分三层](../核心问题地图.md#kp-comm-three-layers-l1) · [结构合法不等于可信](../核心问题地图.md#kp-frame-structure-vs-trust-l1) · [RS485与静默划帧](../核心问题地图.md#kp-rs485-modbus-framing-l1) · [仲裁与DBC解码](../核心问题地图.md#kp-can-arbitration-dbc-l1) · [充电握手四段](../核心问题地图.md#kp-gbt-27930-handshake-l1) · [SMBus与BLE边界](../核心问题地图.md#kp-smbus-ble-boundaries-l1) · [单变量定位字段](../核心问题地图.md#kp-field-by-variation-l1) · [写入口上锁](../核心问题地图.md#kp-comm-write-lockdown-l1) |
| 6 | [预充证据](../核心问题地图.md#kp-precharge-evidence-l1) · [三级架构与互锁](../核心问题地图.md#kp-hv-three-tier-hvil-l1) · [母线仍有电四形状](../核心问题地图.md#kp-bus-live-shape-diagnosis-l1) · [绝缘两次投切](../核心问题地图.md#kp-imd-two-equations-l1) · [过充与开线分流](../核心问题地图.md#kp-overcharge-two-root-causes-l1) · [量产状态机三铁律](../核心问题地图.md#kp-production-state-machine-l1) · [DTC五要素与快照](../核心问题地图.md#kp-dtc-snapshot-freeze-l1) · [A/B升级与回滚](../核心问题地图.md#kp-ota-ab-rollback-l1) · [EOL与静态功耗](../核心问题地图.md#kp-eol-static-current-l1) · [追溯链与错芯](../核心问题地图.md#kp-trace-chain-identity-l1) · [毕业项目与量规](../核心问题地图.md#kp-capstone-rubric-evidence-l1) |
| 7 | [AI 边界](../核心问题地图.md#kp-ai-boundary-l1) · [先抓包再问模型](../核心问题地图.md#kp-ai-evidence-first-l1) · [三圈边界](../核心问题地图.md#kp-ai-role-circles-l1) · [解释归模型判定归程序](../核心问题地图.md#kp-ai-signoff-chain-l1) · [五种失败模式与探针](../核心问题地图.md#kp-ai-failure-probes-l1) |

### 理解（梯子 L2）

| 阶段 | 知识点 |
|---:|---|
| 0 | [三根探针](../核心问题地图.md#kp-three-probes-l2) · [电压窗口看化学体系](../核心问题地图.md#kp-chemistry-voltage-window-l2) · [倍率换成安培](../核心问题地图.md#kp-c-rate-current-l2) · [电压到顶不等于充满](../核心问题地图.md#kp-charge-termination-l2) · [SOC分母会变](../核心问题地图.md#kp-soc-capacity-denominator-l2) · [深放不靠激活补救](../核心问题地图.md#kp-deep-discharge-triage-l2) · [正极材料决定性格](../核心问题地图.md#kp-cathode-family-traits-l2) · [离子走里电子走外](../核心问题地图.md#kp-ion-electron-paths-l2) · [带载掉压](../核心问题地图.md#kp-load-voltage-drop-l2) · [过充链](../核心问题地图.md#kp-overcharge-chain-l2) |
| 1 | [木桶效应](../核心问题地图.md#kp-weakest-cell-l2) · [串抬压并加容量](../核心问题地图.md#kp-series-parallel-taps-l2) · [五大功能与一拍时间](../核心问题地图.md#kp-bms-five-modules-l2) · [五大保护与断口](../核心问题地图.md#kp-five-protections-table-l2) · [每条保护的事故来源](../核心问题地图.md#kp-protection-accident-origin-l2) · [温升速率先抬头](../核心问题地图.md#kp-dtdt-early-warning-l2) · [三种形态怎么选](../核心问题地图.md#kp-bms-three-forms-l2) · [保护三问写成状态机](../核心问题地图.md#kp-protection-state-machine-l2) · [均衡是细流不是大河](../核心问题地图.md#kp-balance-current-scale-l2) |
| 2 | [保护去抖](../核心问题地图.md#kp-protection-debounce-l2) · [认板上五类器件](../核心问题地图.md#kp-board-parts-id-l2) · [同口分口与端子](../核心问题地图.md#kp-terminal-port-topology-l2) · [DW01三道判断题](../核心问题地图.md#kp-dw01-three-judgements-l2) · [回差与确认时间](../核心问题地图.md#kp-ov-hysteresis-recovery-l2) · [多串为何不能摞](../核心问题地图.md#kp-multicell-floating-channels-l2) · [过流分档与I²t](../核心问题地图.md#kp-oc-tiers-i2t-l2) · [背靠背驱动与发热](../核心问题地图.md#kp-mos-drive-and-heat-l2) · [NTC位置与温度窗](../核心问题地图.md#kp-ntc-placement-temp-window-l2) · [分压链实测与记录](../核心问题地图.md#kp-protection-bench-record-l2) |
| 3 | [测量预算](../核心问题地图.md#kp-measurement-budget-l2) · [感知决策分工](../核心问题地图.md#kp-afe-mcu-split-l2) · [一颗ADC轮流扫](../核心问题地图.md#kp-mux-scan-budget-l2) · [误差要逐截垒](../核心问题地图.md#kp-sampling-error-budget-l2) · [CRC与寄存器快照](../核心问题地图.md#kp-afe-crc-register-read-l2) · [均衡关断后的回弹](../核心问题地图.md#kp-balance-settle-window-l2) · [高压从板与隔离](../核心问题地图.md#kp-hv-daisy-isolation-l2) · [故障锁存与快照](../核心问题地图.md#kp-fault-latch-recovery-l2) · [周期预算与喂狗](../核心问题地图.md#kp-loop-slack-watchdog-l2) · [高边低边怎么选](../核心问题地图.md#kp-highside-lowside-choice-l2) · [分级上电与开线](../核心问题地图.md#kp-bringup-ladder-openwire-l2) · [原理图五条纪律](../核心问题地图.md#kp-pcb-five-disciplines-l2) |
| 4 | [安时积分漂移](../核心问题地图.md#kp-soc-drift-l2) · [OCV 可信度](../核心问题地图.md#kp-ocv-trust-l2) · [HPPC 辨识](../核心问题地图.md#kp-hppc-identification-l2) · [SOP 取最小](../核心问题地图.md#kp-sop-minimum-l2) · [SOC四个捣蛋鬼](../核心问题地图.md#kp-soc-four-troublemakers-l2) · [三个锚点的条件](../核心问题地图.md#kp-soc-anchor-conditions-l2) · [零偏与分流温漂](../核心问题地图.md#kp-shunt-offset-tempco-l2) · [增益把信任分出去](../核心问题地图.md#kp-ekf-gain-trust-l2) · [容量与内阻双指标](../核心问题地图.md#kp-soh-dual-indicators-l2) · [局部窗口与dQdV](../核心问题地图.md#kp-soh-window-and-dqdv-l2) · [低温降额不硬充](../核心问题地图.md#kp-temp-derate-charge-l2) · [落地要点与验收](../核心问题地图.md#kp-soc-engineering-landing-l2) · [仿真当裁判，不当签字](../核心问题地图.md#kp-sim-referee-not-signoff-l2) · [参数要带窗口](../核心问题地图.md#kp-param-window-reporting-l2) |
| 5 | [帧状态机](../核心问题地图.md#kp-protocol-resync-l2) · [通信分三层](../核心问题地图.md#kp-comm-three-layers-l2) · [结构合法不等于可信](../核心问题地图.md#kp-frame-structure-vs-trust-l2) · [RS485与静默划帧](../核心问题地图.md#kp-rs485-modbus-framing-l2) · [仲裁与DBC解码](../核心问题地图.md#kp-can-arbitration-dbc-l2) · [充电握手四段](../核心问题地图.md#kp-gbt-27930-handshake-l2) · [SMBus与BLE边界](../核心问题地图.md#kp-smbus-ble-boundaries-l2) · [单变量定位字段](../核心问题地图.md#kp-field-by-variation-l2) · [写入口上锁](../核心问题地图.md#kp-comm-write-lockdown-l2) |
| 6 | [预充证据](../核心问题地图.md#kp-precharge-evidence-l2) · [三级架构与互锁](../核心问题地图.md#kp-hv-three-tier-hvil-l2) · [母线仍有电四形状](../核心问题地图.md#kp-bus-live-shape-diagnosis-l2) · [绝缘两次投切](../核心问题地图.md#kp-imd-two-equations-l2) · [过充与开线分流](../核心问题地图.md#kp-overcharge-two-root-causes-l2) · [量产状态机三铁律](../核心问题地图.md#kp-production-state-machine-l2) · [DTC五要素与快照](../核心问题地图.md#kp-dtc-snapshot-freeze-l2) · [A/B升级与回滚](../核心问题地图.md#kp-ota-ab-rollback-l2) · [EOL与静态功耗](../核心问题地图.md#kp-eol-static-current-l2) · [追溯链与错芯](../核心问题地图.md#kp-trace-chain-identity-l2) · [毕业项目与量规](../核心问题地图.md#kp-capstone-rubric-evidence-l2) |
| 7 | [AI 边界](../核心问题地图.md#kp-ai-boundary-l2) · [先抓包再问模型](../核心问题地图.md#kp-ai-evidence-first-l2) · [三圈边界](../核心问题地图.md#kp-ai-role-circles-l2) · [解释归模型判定归程序](../核心问题地图.md#kp-ai-signoff-chain-l2) · [五种失败模式与探针](../核心问题地图.md#kp-ai-failure-probes-l2) |

### 应用（梯子 L3）

| 阶段 | 知识点 |
|---:|---|
| 0 | [三根探针](../核心问题地图.md#kp-three-probes-l3) · [电压窗口看化学体系](../核心问题地图.md#kp-chemistry-voltage-window-l3) · [倍率换成安培](../核心问题地图.md#kp-c-rate-current-l3) · [电压到顶不等于充满](../核心问题地图.md#kp-charge-termination-l3) · [SOC分母会变](../核心问题地图.md#kp-soc-capacity-denominator-l3) · [深放不靠激活补救](../核心问题地图.md#kp-deep-discharge-triage-l3) · [正极材料决定性格](../核心问题地图.md#kp-cathode-family-traits-l3) · [离子走里电子走外](../核心问题地图.md#kp-ion-electron-paths-l3) · [带载掉压](../核心问题地图.md#kp-load-voltage-drop-l3) · [过充链](../核心问题地图.md#kp-overcharge-chain-l3) |
| 1 | [木桶效应](../核心问题地图.md#kp-weakest-cell-l3) · [串抬压并加容量](../核心问题地图.md#kp-series-parallel-taps-l3) · [五大功能与一拍时间](../核心问题地图.md#kp-bms-five-modules-l3) · [五大保护与断口](../核心问题地图.md#kp-five-protections-table-l3) · [每条保护的事故来源](../核心问题地图.md#kp-protection-accident-origin-l3) · [温升速率先抬头](../核心问题地图.md#kp-dtdt-early-warning-l3) · [三种形态怎么选](../核心问题地图.md#kp-bms-three-forms-l3) · [保护三问写成状态机](../核心问题地图.md#kp-protection-state-machine-l3) · [均衡是细流不是大河](../核心问题地图.md#kp-balance-current-scale-l3) |
| 2 | [保护去抖](../核心问题地图.md#kp-protection-debounce-l3) · [认板上五类器件](../核心问题地图.md#kp-board-parts-id-l3) · [同口分口与端子](../核心问题地图.md#kp-terminal-port-topology-l3) · [DW01三道判断题](../核心问题地图.md#kp-dw01-three-judgements-l3) · [回差与确认时间](../核心问题地图.md#kp-ov-hysteresis-recovery-l3) · [多串为何不能摞](../核心问题地图.md#kp-multicell-floating-channels-l3) · [过流分档与I²t](../核心问题地图.md#kp-oc-tiers-i2t-l3) · [背靠背驱动与发热](../核心问题地图.md#kp-mos-drive-and-heat-l3) · [NTC位置与温度窗](../核心问题地图.md#kp-ntc-placement-temp-window-l3) · [分压链实测与记录](../核心问题地图.md#kp-protection-bench-record-l3) |
| 3 | [测量预算](../核心问题地图.md#kp-measurement-budget-l3) · [感知决策分工](../核心问题地图.md#kp-afe-mcu-split-l3) · [一颗ADC轮流扫](../核心问题地图.md#kp-mux-scan-budget-l3) · [误差要逐截垒](../核心问题地图.md#kp-sampling-error-budget-l3) · [CRC与寄存器快照](../核心问题地图.md#kp-afe-crc-register-read-l3) · [均衡关断后的回弹](../核心问题地图.md#kp-balance-settle-window-l3) · [高压从板与隔离](../核心问题地图.md#kp-hv-daisy-isolation-l3) · [故障锁存与快照](../核心问题地图.md#kp-fault-latch-recovery-l3) · [周期预算与喂狗](../核心问题地图.md#kp-loop-slack-watchdog-l3) · [高边低边怎么选](../核心问题地图.md#kp-highside-lowside-choice-l3) · [分级上电与开线](../核心问题地图.md#kp-bringup-ladder-openwire-l3) · [原理图五条纪律](../核心问题地图.md#kp-pcb-five-disciplines-l3) |
| 4 | [安时积分漂移](../核心问题地图.md#kp-soc-drift-l3) · [OCV 可信度](../核心问题地图.md#kp-ocv-trust-l3) · [HPPC 辨识](../核心问题地图.md#kp-hppc-identification-l3) · [SOP 取最小](../核心问题地图.md#kp-sop-minimum-l3) · [SOC四个捣蛋鬼](../核心问题地图.md#kp-soc-four-troublemakers-l3) · [三个锚点的条件](../核心问题地图.md#kp-soc-anchor-conditions-l3) · [零偏与分流温漂](../核心问题地图.md#kp-shunt-offset-tempco-l3) · [增益把信任分出去](../核心问题地图.md#kp-ekf-gain-trust-l3) · [容量与内阻双指标](../核心问题地图.md#kp-soh-dual-indicators-l3) · [局部窗口与dQdV](../核心问题地图.md#kp-soh-window-and-dqdv-l3) · [低温降额不硬充](../核心问题地图.md#kp-temp-derate-charge-l3) · [落地要点与验收](../核心问题地图.md#kp-soc-engineering-landing-l3) · [仿真当裁判，不当签字](../核心问题地图.md#kp-sim-referee-not-signoff-l3) · [参数要带窗口](../核心问题地图.md#kp-param-window-reporting-l3) |
| 5 | [帧状态机](../核心问题地图.md#kp-protocol-resync-l3) · [通信分三层](../核心问题地图.md#kp-comm-three-layers-l3) · [结构合法不等于可信](../核心问题地图.md#kp-frame-structure-vs-trust-l3) · [RS485与静默划帧](../核心问题地图.md#kp-rs485-modbus-framing-l3) · [仲裁与DBC解码](../核心问题地图.md#kp-can-arbitration-dbc-l3) · [充电握手四段](../核心问题地图.md#kp-gbt-27930-handshake-l3) · [SMBus与BLE边界](../核心问题地图.md#kp-smbus-ble-boundaries-l3) · [单变量定位字段](../核心问题地图.md#kp-field-by-variation-l3) · [写入口上锁](../核心问题地图.md#kp-comm-write-lockdown-l3) |
| 6 | [预充证据](../核心问题地图.md#kp-precharge-evidence-l3) · [三级架构与互锁](../核心问题地图.md#kp-hv-three-tier-hvil-l3) · [母线仍有电四形状](../核心问题地图.md#kp-bus-live-shape-diagnosis-l3) · [绝缘两次投切](../核心问题地图.md#kp-imd-two-equations-l3) · [过充与开线分流](../核心问题地图.md#kp-overcharge-two-root-causes-l3) · [量产状态机三铁律](../核心问题地图.md#kp-production-state-machine-l3) · [DTC五要素与快照](../核心问题地图.md#kp-dtc-snapshot-freeze-l3) · [A/B升级与回滚](../核心问题地图.md#kp-ota-ab-rollback-l3) · [EOL与静态功耗](../核心问题地图.md#kp-eol-static-current-l3) · [追溯链与错芯](../核心问题地图.md#kp-trace-chain-identity-l3) · [毕业项目与量规](../核心问题地图.md#kp-capstone-rubric-evidence-l3) |
| 7 | [AI 边界](../核心问题地图.md#kp-ai-boundary-l3) · [先抓包再问模型](../核心问题地图.md#kp-ai-evidence-first-l3) · [三圈边界](../核心问题地图.md#kp-ai-role-circles-l3) · [解释归模型判定归程序](../核心问题地图.md#kp-ai-signoff-chain-l3) · [五种失败模式与探针](../核心问题地图.md#kp-ai-failure-probes-l3) |

### 分析 / 评价（梯子 L4）

| 阶段 | 知识点 |
|---:|---|
| 0 | [三根探针](../核心问题地图.md#kp-three-probes-l4) · [电压窗口看化学体系](../核心问题地图.md#kp-chemistry-voltage-window-l4) · [倍率换成安培](../核心问题地图.md#kp-c-rate-current-l4) · [电压到顶不等于充满](../核心问题地图.md#kp-charge-termination-l4) · [SOC分母会变](../核心问题地图.md#kp-soc-capacity-denominator-l4) · [深放不靠激活补救](../核心问题地图.md#kp-deep-discharge-triage-l4) · [正极材料决定性格](../核心问题地图.md#kp-cathode-family-traits-l4) · [离子走里电子走外](../核心问题地图.md#kp-ion-electron-paths-l4) · [带载掉压](../核心问题地图.md#kp-load-voltage-drop-l4) · [过充链](../核心问题地图.md#kp-overcharge-chain-l4) |
| 1 | [木桶效应](../核心问题地图.md#kp-weakest-cell-l4) · [串抬压并加容量](../核心问题地图.md#kp-series-parallel-taps-l4) · [五大功能与一拍时间](../核心问题地图.md#kp-bms-five-modules-l4) · [五大保护与断口](../核心问题地图.md#kp-five-protections-table-l4) · [每条保护的事故来源](../核心问题地图.md#kp-protection-accident-origin-l4) · [温升速率先抬头](../核心问题地图.md#kp-dtdt-early-warning-l4) · [三种形态怎么选](../核心问题地图.md#kp-bms-three-forms-l4) · [保护三问写成状态机](../核心问题地图.md#kp-protection-state-machine-l4) · [均衡是细流不是大河](../核心问题地图.md#kp-balance-current-scale-l4) |
| 2 | [保护去抖](../核心问题地图.md#kp-protection-debounce-l4) · [认板上五类器件](../核心问题地图.md#kp-board-parts-id-l4) · [同口分口与端子](../核心问题地图.md#kp-terminal-port-topology-l4) · [DW01三道判断题](../核心问题地图.md#kp-dw01-three-judgements-l4) · [回差与确认时间](../核心问题地图.md#kp-ov-hysteresis-recovery-l4) · [多串为何不能摞](../核心问题地图.md#kp-multicell-floating-channels-l4) · [过流分档与I²t](../核心问题地图.md#kp-oc-tiers-i2t-l4) · [背靠背驱动与发热](../核心问题地图.md#kp-mos-drive-and-heat-l4) · [NTC位置与温度窗](../核心问题地图.md#kp-ntc-placement-temp-window-l4) · [分压链实测与记录](../核心问题地图.md#kp-protection-bench-record-l4) |
| 3 | [测量预算](../核心问题地图.md#kp-measurement-budget-l4) · [感知决策分工](../核心问题地图.md#kp-afe-mcu-split-l4) · [一颗ADC轮流扫](../核心问题地图.md#kp-mux-scan-budget-l4) · [误差要逐截垒](../核心问题地图.md#kp-sampling-error-budget-l4) · [CRC与寄存器快照](../核心问题地图.md#kp-afe-crc-register-read-l4) · [均衡关断后的回弹](../核心问题地图.md#kp-balance-settle-window-l4) · [高压从板与隔离](../核心问题地图.md#kp-hv-daisy-isolation-l4) · [故障锁存与快照](../核心问题地图.md#kp-fault-latch-recovery-l4) · [周期预算与喂狗](../核心问题地图.md#kp-loop-slack-watchdog-l4) · [高边低边怎么选](../核心问题地图.md#kp-highside-lowside-choice-l4) · [分级上电与开线](../核心问题地图.md#kp-bringup-ladder-openwire-l4) · [原理图五条纪律](../核心问题地图.md#kp-pcb-five-disciplines-l4) |
| 4 | [安时积分漂移](../核心问题地图.md#kp-soc-drift-l4) · [OCV 可信度](../核心问题地图.md#kp-ocv-trust-l4) · [HPPC 辨识](../核心问题地图.md#kp-hppc-identification-l4) · [SOP 取最小](../核心问题地图.md#kp-sop-minimum-l4) · [SOC四个捣蛋鬼](../核心问题地图.md#kp-soc-four-troublemakers-l4) · [三个锚点的条件](../核心问题地图.md#kp-soc-anchor-conditions-l4) · [零偏与分流温漂](../核心问题地图.md#kp-shunt-offset-tempco-l4) · [增益把信任分出去](../核心问题地图.md#kp-ekf-gain-trust-l4) · [容量与内阻双指标](../核心问题地图.md#kp-soh-dual-indicators-l4) · [局部窗口与dQdV](../核心问题地图.md#kp-soh-window-and-dqdv-l4) · [低温降额不硬充](../核心问题地图.md#kp-temp-derate-charge-l4) · [落地要点与验收](../核心问题地图.md#kp-soc-engineering-landing-l4) · [仿真当裁判，不当签字](../核心问题地图.md#kp-sim-referee-not-signoff-l4) · [参数要带窗口](../核心问题地图.md#kp-param-window-reporting-l4) |
| 5 | [帧状态机](../核心问题地图.md#kp-protocol-resync-l4) · [通信分三层](../核心问题地图.md#kp-comm-three-layers-l4) · [结构合法不等于可信](../核心问题地图.md#kp-frame-structure-vs-trust-l4) · [RS485与静默划帧](../核心问题地图.md#kp-rs485-modbus-framing-l4) · [仲裁与DBC解码](../核心问题地图.md#kp-can-arbitration-dbc-l4) · [充电握手四段](../核心问题地图.md#kp-gbt-27930-handshake-l4) · [SMBus与BLE边界](../核心问题地图.md#kp-smbus-ble-boundaries-l4) · [单变量定位字段](../核心问题地图.md#kp-field-by-variation-l4) · [写入口上锁](../核心问题地图.md#kp-comm-write-lockdown-l4) |
| 6 | [预充证据](../核心问题地图.md#kp-precharge-evidence-l4) · [三级架构与互锁](../核心问题地图.md#kp-hv-three-tier-hvil-l4) · [母线仍有电四形状](../核心问题地图.md#kp-bus-live-shape-diagnosis-l4) · [绝缘两次投切](../核心问题地图.md#kp-imd-two-equations-l4) · [过充与开线分流](../核心问题地图.md#kp-overcharge-two-root-causes-l4) · [量产状态机三铁律](../核心问题地图.md#kp-production-state-machine-l4) · [DTC五要素与快照](../核心问题地图.md#kp-dtc-snapshot-freeze-l4) · [A/B升级与回滚](../核心问题地图.md#kp-ota-ab-rollback-l4) · [EOL与静态功耗](../核心问题地图.md#kp-eol-static-current-l4) · [追溯链与错芯](../核心问题地图.md#kp-trace-chain-identity-l4) · [毕业项目与量规](../核心问题地图.md#kp-capstone-rubric-evidence-l4) |
| 7 | [AI 边界](../核心问题地图.md#kp-ai-boundary-l4) · [先抓包再问模型](../核心问题地图.md#kp-ai-evidence-first-l4) · [三圈边界](../核心问题地图.md#kp-ai-role-circles-l4) · [解释归模型判定归程序](../核心问题地图.md#kp-ai-signoff-chain-l4) · [五种失败模式与探针](../核心问题地图.md#kp-ai-failure-probes-l4) |

### 创造（梯子 L5）

| 阶段 | 知识点 |
|---:|---|
| 0 | [三根探针](../核心问题地图.md#kp-three-probes-l5) · [电压窗口看化学体系](../核心问题地图.md#kp-chemistry-voltage-window-l5) · [倍率换成安培](../核心问题地图.md#kp-c-rate-current-l5) · [电压到顶不等于充满](../核心问题地图.md#kp-charge-termination-l5) · [SOC分母会变](../核心问题地图.md#kp-soc-capacity-denominator-l5) · [深放不靠激活补救](../核心问题地图.md#kp-deep-discharge-triage-l5) · [正极材料决定性格](../核心问题地图.md#kp-cathode-family-traits-l5) · [离子走里电子走外](../核心问题地图.md#kp-ion-electron-paths-l5) · [带载掉压](../核心问题地图.md#kp-load-voltage-drop-l5) · [过充链](../核心问题地图.md#kp-overcharge-chain-l5) |
| 1 | [木桶效应](../核心问题地图.md#kp-weakest-cell-l5) · [串抬压并加容量](../核心问题地图.md#kp-series-parallel-taps-l5) · [五大功能与一拍时间](../核心问题地图.md#kp-bms-five-modules-l5) · [五大保护与断口](../核心问题地图.md#kp-five-protections-table-l5) · [每条保护的事故来源](../核心问题地图.md#kp-protection-accident-origin-l5) · [温升速率先抬头](../核心问题地图.md#kp-dtdt-early-warning-l5) · [三种形态怎么选](../核心问题地图.md#kp-bms-three-forms-l5) · [保护三问写成状态机](../核心问题地图.md#kp-protection-state-machine-l5) · [均衡是细流不是大河](../核心问题地图.md#kp-balance-current-scale-l5) |
| 2 | [保护去抖](../核心问题地图.md#kp-protection-debounce-l5) · [认板上五类器件](../核心问题地图.md#kp-board-parts-id-l5) · [同口分口与端子](../核心问题地图.md#kp-terminal-port-topology-l5) · [DW01三道判断题](../核心问题地图.md#kp-dw01-three-judgements-l5) · [回差与确认时间](../核心问题地图.md#kp-ov-hysteresis-recovery-l5) · [多串为何不能摞](../核心问题地图.md#kp-multicell-floating-channels-l5) · [过流分档与I²t](../核心问题地图.md#kp-oc-tiers-i2t-l5) · [背靠背驱动与发热](../核心问题地图.md#kp-mos-drive-and-heat-l5) · [NTC位置与温度窗](../核心问题地图.md#kp-ntc-placement-temp-window-l5) · [分压链实测与记录](../核心问题地图.md#kp-protection-bench-record-l5) |
| 3 | [测量预算](../核心问题地图.md#kp-measurement-budget-l5) · [感知决策分工](../核心问题地图.md#kp-afe-mcu-split-l5) · [一颗ADC轮流扫](../核心问题地图.md#kp-mux-scan-budget-l5) · [误差要逐截垒](../核心问题地图.md#kp-sampling-error-budget-l5) · [CRC与寄存器快照](../核心问题地图.md#kp-afe-crc-register-read-l5) · [均衡关断后的回弹](../核心问题地图.md#kp-balance-settle-window-l5) · [高压从板与隔离](../核心问题地图.md#kp-hv-daisy-isolation-l5) · [故障锁存与快照](../核心问题地图.md#kp-fault-latch-recovery-l5) · [周期预算与喂狗](../核心问题地图.md#kp-loop-slack-watchdog-l5) · [高边低边怎么选](../核心问题地图.md#kp-highside-lowside-choice-l5) · [分级上电与开线](../核心问题地图.md#kp-bringup-ladder-openwire-l5) · [原理图五条纪律](../核心问题地图.md#kp-pcb-five-disciplines-l5) |
| 4 | [安时积分漂移](../核心问题地图.md#kp-soc-drift-l5) · [OCV 可信度](../核心问题地图.md#kp-ocv-trust-l5) · [HPPC 辨识](../核心问题地图.md#kp-hppc-identification-l5) · [SOP 取最小](../核心问题地图.md#kp-sop-minimum-l5) · [SOC四个捣蛋鬼](../核心问题地图.md#kp-soc-four-troublemakers-l5) · [三个锚点的条件](../核心问题地图.md#kp-soc-anchor-conditions-l5) · [零偏与分流温漂](../核心问题地图.md#kp-shunt-offset-tempco-l5) · [增益把信任分出去](../核心问题地图.md#kp-ekf-gain-trust-l5) · [容量与内阻双指标](../核心问题地图.md#kp-soh-dual-indicators-l5) · [局部窗口与dQdV](../核心问题地图.md#kp-soh-window-and-dqdv-l5) · [低温降额不硬充](../核心问题地图.md#kp-temp-derate-charge-l5) · [落地要点与验收](../核心问题地图.md#kp-soc-engineering-landing-l5) · [仿真当裁判，不当签字](../核心问题地图.md#kp-sim-referee-not-signoff-l5) · [参数要带窗口](../核心问题地图.md#kp-param-window-reporting-l5) |
| 5 | [帧状态机](../核心问题地图.md#kp-protocol-resync-l5) · [通信分三层](../核心问题地图.md#kp-comm-three-layers-l5) · [结构合法不等于可信](../核心问题地图.md#kp-frame-structure-vs-trust-l5) · [RS485与静默划帧](../核心问题地图.md#kp-rs485-modbus-framing-l5) · [仲裁与DBC解码](../核心问题地图.md#kp-can-arbitration-dbc-l5) · [充电握手四段](../核心问题地图.md#kp-gbt-27930-handshake-l5) · [SMBus与BLE边界](../核心问题地图.md#kp-smbus-ble-boundaries-l5) · [单变量定位字段](../核心问题地图.md#kp-field-by-variation-l5) · [写入口上锁](../核心问题地图.md#kp-comm-write-lockdown-l5) |
| 6 | [预充证据](../核心问题地图.md#kp-precharge-evidence-l5) · [三级架构与互锁](../核心问题地图.md#kp-hv-three-tier-hvil-l5) · [母线仍有电四形状](../核心问题地图.md#kp-bus-live-shape-diagnosis-l5) · [绝缘两次投切](../核心问题地图.md#kp-imd-two-equations-l5) · [过充与开线分流](../核心问题地图.md#kp-overcharge-two-root-causes-l5) · [量产状态机三铁律](../核心问题地图.md#kp-production-state-machine-l5) · [DTC五要素与快照](../核心问题地图.md#kp-dtc-snapshot-freeze-l5) · [A/B升级与回滚](../核心问题地图.md#kp-ota-ab-rollback-l5) · [EOL与静态功耗](../核心问题地图.md#kp-eol-static-current-l5) · [追溯链与错芯](../核心问题地图.md#kp-trace-chain-identity-l5) · [毕业项目与量规](../核心问题地图.md#kp-capstone-rubric-evidence-l5) |
| 7 | [AI 边界](../核心问题地图.md#kp-ai-boundary-l5) · [先抓包再问模型](../核心问题地图.md#kp-ai-evidence-first-l5) · [三圈边界](../核心问题地图.md#kp-ai-role-circles-l5) · [解释归模型判定归程序](../核心问题地图.md#kp-ai-signoff-chain-l5) · [五种失败模式与探针](../核心问题地图.md#kp-ai-failure-probes-l5) |
<!-- kp-bloom:end -->
