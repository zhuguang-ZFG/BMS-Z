# BMS 术语表

> 中英对照 + 一句话解释 + 反向索引（点链接跳到讲透它的章节）。
> 按主题分组；查单个术语用 Ctrl+F 更快。

先背六句，再查表。每句都能在下面对上一个词。

> **口诀**　离子走里面，电子走外面。过放当时安静。4.2 V 是进恒压的门票。单颗 MOS 关不死两个方向。ESP32 是电台，不是保险丝。包上这一拍就断。

**练完你会怎样**：你能用这张表把一句口诀对回章节，而不是只记住缩写。4.2 V 仍是三元示例。


## 系统与架构

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| BMS | Battery Management System | 电池管理系统：监测、保护、均衡、估算、通信五件事 | [阶段 1](stages/stage-1-认识BMS.md) |
| AFE | Analog Front End | 模拟前端：专职高精度采样与硬件保护的芯片（如 BQ769x2） | [详解 ②](circuits/02-采样链与AFE芯片.md) |
| BMU | Battery Management Unit | 主控板：对外通信、汇总决策、继电器驱动 | [阶段 6](stages/stage-6-精通与毕业项目.md#611-高压电池系统架构-分析) |
| CMU | Cell Monitoring Unit | 从板：每组 12–18 串的采样与均衡执行 | 同上 |
| BDU | Battery Disconnect Unit | 配电盒：主继电器、预充、熔断器、电流传感器 | 同上 |
| 并簇 / 环流 | Parallel strings / Circulating current | 多包并联时压差驱动的包间电流；合闸前须对齐 | [阶段 6 §6.1.5](stages/stage-6-精通与毕业项目.md) |
| TMS | Thermal Management System | 热管理：风冷、液冷、直冷都只执行。允许充多少仍由 BMS 说了算 | [阶段 6 §6.1.6](stages/stage-6-精通与毕业项目.md) |
| 保护板 | Protection Board | 无 MCU 的纯硬件保护：阈值写死、不认识 SOC | [阶段 1 §1.6](stages/stage-1-认识BMS.md) |
| 菊花链 | Daisy Chain | 多颗 AFE 逐级"接收→再生→转发"的级联方式 | [详解 ② §7](circuits/02-采样链与AFE芯片.md) |
| 同口 / 分口 | Common / Separate Port | 充放电共用一个 MOS 组 / 充放电 MOS 分开 | [详解 ① §2.3](circuits/01-功率回路-MOS保护与预充.md) |
| 接触器 | Contactor | 高压回路上的闸。保护板上的 MOS 关的是板级电流；合这只闸之前要先预充 | [详解 ④ §2](circuits/04-系统安全与量产.md#2-接触器管理高压回路的三只闸-分析) |
| HVIL | High-Voltage Interlock Loop | 高压互锁：低压环先断，人还没碰到端子，接触器就该打开。拔枪、开维修开关都拉这根环 | [详解 ④ §1.1](circuits/04-系统安全与量产.md#11-hvil一根低压线串起所有高压插头-理解) |
| 主动放电 | Active discharge | 下电或碰撞后，把母线电容里的电放掉。预充电阻是在合闸前灌电容，两只电阻各干各的 | [详解 ④ §1.3](circuits/04-系统安全与量产.md#13-主动放电碰撞后的-5-秒钟-理解) |
| 寄存器地图 | Register map | 单体电压、电流、均衡位、故障位各在哪个地址。没有地址，电芯规格书写不进比较器。读包级手册时先翻这一页 | [包级手册缺口](t13-包级手册缺口.md#手册里必须有的三页-理解) |

## 电池与状态量

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| SOC | State of Charge | 荷电状态：还剩多少电（分母是**当前**满充容量） | [阶段 4](stages/stage-4-SOC-SOH算法.md) |
| SOH | State of Health | 健康状态：容量口径与内阻口径两种 | [阶段 4 §4.6](stages/stage-4-SOC-SOH算法.md) |
| SOP | State of Power | 此刻能出多大力：多约束取最小 | [阶段 4 §4.7](stages/stage-4-SOC-SOH算法.md) |
| OCV | Open Circuit Voltage | 开路电压：静置后与 SOC 单调对应 | [阶段 4 §4.3](stages/stage-4-SOC-SOH算法.md) |
| C 倍率 | C-rate | 1C = 一小时放完额定容量的电流 | [阶段 0 §0.1.5](stages/stage-0-前置知识.md) |
| CC-CV | Constant Current – Constant Voltage | 恒流转恒压充电法；满充看 CV 截止电流 | [详解 ③ §1](circuits/03-充电均衡与计量.md) |
| NCM / LFP / LCO / LMO | 三元 / 磷酸铁锂 / 钴酸锂 / 锰酸锂 | 正极化学体系不同，满充电压和平台都不一样。锰酸锂在入门讲义里和前三种一起出现 | [阶段 0 §0.1.1](stages/stage-0-前置知识.md) · [Notes01 §六](ece5710-notes01-中文导读.md#六负极正极电解液隔膜15) |
| 过充 | Overcharge | 单体电压越过这颗电芯答应的上限。三元示例里常听到 4.2 V，钠电和固态要换窗口 | [阶段 0 §0.1.2](stages/stage-0-前置知识.md#012-过充一场逐级升级的事故-理解) |
| 过放 | Over-discharge | 放得太低。大约 2.5–3.0 V 是常见预充门槛。铜溶解一般要到大约 1.5 V 或更低，当时可以很安静 | [阶段 0 §0.1.3](stages/stage-0-前置知识.md#013-过放安静的杀手-理解) |
| 五大保护 | — | 过充、过放、过流、短路、过温。先背断哪一只口，再背阈值。读保护板丝印时会一次碰上 | [阶段 1 §1.4](stages/stage-1-认识BMS.md#14-五大保护名词断口与三要素-记忆) |
| 石墨 | Graphite | 锂电最常见的负极。锂来不及嵌进去，就在表面析出来 | [Notes01 §六](ece5710-notes01-中文导读.md#六负极正极电解液隔膜15) |
| 硬碳 | Hard carbon | 钠离子常用的负极。OCV 不跟石墨那张表。拿锂电保护板套钠电，就是在这里踩坑 | [阶段 0 §0.1.10](stages/stage-0-前置知识.md#0110-钠离子硬碳和另一套电压窗口-理解) |
| 电解液 | Electrolyte | 离子走的那一滩液体。它得挡住电子，否则电芯自己就把电放掉。固态换掉的是这一滩 | [Notes01 §六](ece5710-notes01-中文导读.md#六负极正极电解液隔膜15) · [阶段 0 §0.1.8](stages/stage-0-前置知识.md#018-固态电池固体电解质换掉了什么-理解) |
| 隔膜 | Separator | 离子过得去，电子过不去。毛刺或枝晶把它刺穿之后，BMS 断不开电芯内部那一点 | [Notes01 §六](ece5710-notes01-中文导读.md#六负极正极电解液隔膜15) |
| SEI | Solid Electrolyte Interphase | 负极表面那层膜，化成时长出来。只惩罚 SEI 的优化曲线，不要抄成充电策略 | [Notes01 §八](ece5710-notes01-中文导读.md#八电极怎么做出来1718) · [Notes07 §三](ece5720-notes07-中文导读.md#三sei-全阶模型和它的降阶7275) |
| 化成 | Formation | 出厂头几次充放，把 SEI 养出来。涂布设备不是化成柜。产线追溯会在这一步之后才谈 K 值 | [Notes01 §八](ece5710-notes01-中文导读.md#八电极怎么做出来1718) |
| 自放电 | Self-discharge | 搁着也在掉电。节与节掉得不一样，不齐会越攒越大；大家一样差，木桶不会更歪 | [Notes05 §二](ece5720-notes05-中文导读.md#二什么造成不齐51) |
| 平台区 | Voltage plateau | 电压几乎不动的那一段电量。这时候别拿电压当 SOC，铁锂尤其容易被几十毫伏放大 | [阶段 4 §4.3](stages/stage-4-SOC-SOH算法.md#43-ocv-法好尺子但经常够不着-分析) |
| 电压窗口 | Voltage window | 这颗电芯允许走到的上下限。写保护点时跟窗口走。公开规格书里两家钠电的停充点不是同一个数 | [阶段 0 §0.1.10](stages/stage-0-前置知识.md#0110-钠离子硬碳和另一套电压窗口-理解) |
| 标称电压 | Nominal voltage | 铭牌上的那一伏。读固态样品和钠电规格时会先看到它。它不是过充点 | [包级手册缺口](t13-包级手册缺口.md#固态与结构电池-分析) |
| 内阻 | Internal resistance | 电流一来，端电压先掉的那一截。容量还在的时候，内阻往往先把功率收走。估 SOH 时会把它和容量分开 | [阶段 4 §4.6](stages/stage-4-SOC-SOH算法.md#46-soh-与联合估计让算法把电池看透-分析) |
| K 值 | OCV drop rate | 静置时开路电压掉多快。产线用它看微短路。0.0239 mV/h 只属于那条中试线 | [详解 ④ §4.3](circuits/04-系统安全与量产.md#43-电芯筛选与追溯-应用) |
| 固态电池 | Solid-state battery | 固体电解质代替液态电解液；阈值和 OCV 表要换，短路保护仍要留 | [阶段 0 §0.1.8](stages/stage-0-前置知识.md#018-固态电池固体电解质换掉了什么-理解) |
| 结构电池 | Structural battery | 碳纤维兼做电极和承力件。碳纤维外壳里的普通电芯不是这一类 | [阶段 0 §0.1.9](stages/stage-0-前置知识.md#019-碳纤维结构电池电极在承力外壳是另一件事-理解) |
| 钠离子电池 | Sodium-ion battery | 钠离子走硬碳等负极。电压窗口和 OCV 跟这颗电芯走。公开规格书里超钠和海四达的停充点不是同一个数。包级寄存器手册仍缺 | [阶段 0 §0.1.10](stages/stage-0-前置知识.md#0110-钠离子硬碳和另一套电压窗口-理解) · [§0.1.11](stages/stage-0-前置知识.md#0111-公开规格书里的钠离子保护要求-理解) · [包级手册缺口](t13-包级手册缺口.md) |
| 析锂 / 锂枝晶 | Li Plating / Dendrite | 锂来不及嵌入石墨而析出金属锂，长成针可刺穿隔膜 | [阶段 0 §0.1.2](stages/stage-0-前置知识.md) |
| 热失控 | Thermal Runaway | 放热→升温→更放热的自我加速链式反应 | [阶段 1 §1.5](stages/stage-1-认识BMS.md) |
| dT/dt | 温升速率 | 比绝对温度更早的热失控信号 | [阶段 1 §1.5](stages/stage-1-认识BMS.md) |
| OCV 滞回 | OCV Hysteresis | 充放电方向 OCV 曲线不重合，差几十 mV | [阶段 4 §4.3](stages/stage-4-SOC-SOH算法.md) |
| 极化 | Polarization | 电流让端电压偏离 OCV 的压差分量；静置几分钟到几小时才消散，OCV 查表前必须等它 | [阶段 4 §4.3](stages/stage-4-SOC-SOH算法.md) |
| 木桶效应 | Barrel Effect | 串联可用容量被最弱单体锁死；Ah 不相加 | [阶段 1 §1.2](stages/stage-1-认识BMS.md) |

## 功率器件与保护

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| MOSFET | 金属氧化物半导体场效应管 | 电控闸门：BMS 里最重要的器件 | [详解 ① §1](circuits/01-功率回路-MOS保护与预充.md) |
| 体二极管 | Body Diode | MOS 制造白送的并联单向阀，单颗永远关不死双向 | [详解 ① §1.2](circuits/01-功率回路-MOS保护与预充.md) |
| 背靠背 | Back-to-Back | 两颗 MOS 反向串联实现双向阻断（共漏/共源） | [详解 ① §1.2](circuits/01-功率回路-MOS保护与预充.md) |
| 高边 / 低边驱动 | High-/Low-side | 保护开关串在 B+ 或 B−；高边源极浮动需浮地驱动 | [阶段 3 §3.5](stages/stage-3-AFE-MCU智能BMS.md)、[详解 ① §1.4](circuits/01-功率回路-MOS保护与预充.md) |
| 自举（电容） | Bootstrap | 高边驱动的浮地「充电宝」：借开关节点摆动给上管栅泵电，不能常开 | [详解 ① §1.4](circuits/01-功率回路-MOS保护与预充.md)、[阶段 3 §3.5](stages/stage-3-AFE-MCU智能BMS.md) |
| VDS / RDS(on) / Qg | 耐压 / 导阻 / 栅电荷 | MOS 选型三参数 | [详解 ① §1.3](circuits/01-功率回路-MOS保护与预充.md) |
| EAS | 雪崩能量额定 | 关断感性负载时 MOS 承受高压尖峰的能力 | [详解 ① §1.3](circuits/01-功率回路-MOS保护与预充.md) |
| I²t | 电流平方×时间 | 热损伤的量度；MOS、线束、熔断器配合的标尺 | [阶段 2 §2.3](stages/stage-2-保护板实践.md) |
| 预充 | Pre-charge | 先串电阻给母线电容充电再合主闸，防数千安冲击 | [详解 ① §3](circuits/01-功率回路-MOS保护与预充.md) |
| 预充电阻 | Precharge resistor | 合闸前灌电容的那只电阻。照片上标 PRECHARGE 的是它。主动放电是另一只，装在母线旁边 | [详解 ① §3](circuits/01-功率回路-MOS保护与预充.md#3-预充回路合闸前的先灌满蓄水池-应用) |
| 粘连 | Contactor weld | 断开命令已经发出，触点却焊住，电压不掉下来。接触器管理里要单独测这一下 | [详解 ④ §2.2](circuits/04-系统安全与量产.md#22-粘连检测命令断了电断没断-分析) |
| 浮地 | Floating output | 电源输出不跟大地绑死。多路不隔离的台式电源叠成假电芯，会从电源内部把串短路 | [阶段 2 §2.6](stages/stage-2-保护板实践.md#26-保护板实测方法本阶段核心技能-应用) |
| 母线电容 | DC-link Capacitor | 逆变器入口的蓄水池：吸纹波稳母线；裸合闸等于短路，所以要预充 | [详解 ① §3](circuits/01-功率回路-MOS保护与预充.md) |
| 熔断器 | Fuse | 不可复位的最后手段，与 MOS 保护按 I²t 配合 | [阶段 6 §6.1.4](stages/stage-6-精通与毕业项目.md) |
| IMD | Insulation Monitoring Device | 绝缘检测：主流电桥法交替投切解两个未知量 | [阶段 6 §6.1.3](stages/stage-6-精通与毕业项目.md) |
| TVS / ESD | 瞬态抑制二极管 / 静电 | 采样口与通信口的浪涌防护 | [阶段 3 §3.5](stages/stage-3-AFE-MCU智能BMS.md) |
| EMC | 电磁兼容 | 小信号采样链与功率回路噪声的攻防 | [阶段 6 §6.1.4](stages/stage-6-精通与毕业项目.md) |

## 采样与芯片

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| MUX | 多路选择器 | 一颗 ADC 巡逻测 16 串：串间一致性好的来源 | [详解 ② §2](circuits/02-采样链与AFE芯片.md) |
| INL | 积分非线性 | ADC 刻度自身的弯曲程度 | [阶段 0 §0.2.2](stages/stage-0-前置知识.md) |
| 基准源 | Voltage Reference | 误差预算的第一项；温漂是头号敌人 | [详解 ② §1](circuits/02-采样链与AFE芯片.md) |
| 开线检测 | Open-wire Detection | 采样线断线检测：电流源拉一下看电压动不动 | [详解 ② §4](circuits/02-采样链与AFE芯片.md) |
| 开尔文接法 | Kelvin (4-wire) | 电流走一对端子、采样走另一对，剔除引线压降 | [详解 ② §8](circuits/02-采样链与AFE芯片.md) |
| 共模 | Common Mode | 两根信号线「一起抬」的那部分电压；高压包顶上的采样点共模数百伏，直连烧芯片 | [详解 ②](circuits/02-采样链与AFE芯片.md)、[阶段 3](stages/stage-3-AFE-MCU智能BMS.md) |
| 库仑计 | Coulomb Counter | AFE 内独立高速通道，硬件替你安时积分 | [详解 ② §5](circuits/02-采样链与AFE芯片.md) |
| DW01 | — | 单节保护 IC：三道判断题的保安 | [详解 ① §2](circuits/01-功率回路-MOS保护与预充.md) |
| S-8254A | — | 3–4 串保护 IC，不可级联；部分延时由外置电容（CDT/CCT）设定 | [阶段 2 §2.3](stages/stage-2-保护板实践.md) |
| BQ769x0/x2 | TI | ≤16S AFE 家族，中文资料最全 | [阶段 3 §3.2](stages/stage-3-AFE-MCU智能BMS.md) |
| LTC6811 / ADBMS | ADI | 12 串 AFE，isoSPI 菊花链，车规 | [阶段 3 §3.3](stages/stage-3-AFE-MCU智能BMS.md) |
| isoSPI | Isolated SPI | 变压器耦合的差分 SPI：信号穿墙、电位差留下 | [详解 ② §7](circuits/02-采样链与AFE芯片.md) |
| NTC | 负温度系数热敏电阻 | 越热阻值越小；下臂接法中点电压随温降 | [详解 ② §6](circuits/02-采样链与AFE芯片.md) |
| 检流电阻 | Shunt | 电流走这只毫欧电阻，采样只读它上面的毫伏。引线压降用开尔文接法剔掉。和霍尔二选一 | [详解 ② §8](circuits/02-采样链与AFE芯片.md#8-电流采样安时积分精度的天花板-分析) |
| 霍尔电流传感器 | Hall-effect current sensor | 不切开功率线也能测电流。包级手册要写明电流是这只，还是检流电阻 | [包级手册缺口](t13-包级手册缺口.md#手册里必须有的三页-理解) |
| I2C | Inter-Integrated Circuit | 时钟和数据两根线问 AFE 要寄存器。没 ACK 的时候先看波形。逻辑分析仪就是为这一下买的 | [阶段 3 §3.2](stages/stage-3-AFE-MCU智能BMS.md#32-afe-精读以-bq769x0x2-为线-分析) |
| SPI | Serial Peripheral Interface | 时钟带着片选把寄存器读出来。isoSPI 是把这一套变成能穿高压墙的差分信号 | [阶段 3 §3.3](stages/stage-3-AFE-MCU智能BMS.md#33-高压与菊花链ltc6811-的世界-分析) |
| 爬电距离 | Creepage | 沿板面量的绝缘距离。高压和采样贴太近，表面一脏就会爬过去。画板时量这一下 | [电路板 §6](circuits/05-BMS电路板绘制与设计要点.md#6-esd-与爬电间隙-应用) |
| 被动均衡 | Passive balancing | 高的那一节把多余的电变成热。它能维持平衡；快不了的时候，别指望它延长寿命 | [详解 ③ §2](circuits/03-充电均衡与计量.md#2-被动均衡电路热与调度-分析) |
| 主动均衡 | Active balancing | 把电从高的一节搬到低的一节。和被动不是同一笔效率账，空表没填之前不要排百分数 | [详解 ③ §3](circuits/03-充电均衡与计量.md#3-主动均衡把水桶换成搬运工-评价) |
| REGOUT | — | AFE 内置 LDO 输出，给 MCU 供电 | [详解 ② §5](circuits/02-采样链与AFE芯片.md) |

## 算法

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| 安时积分 | Coulomb Counting | `SOC += I·dt/Q`；零漂会被积进去，误差不收敛 | [阶段 4 §4.2](stages/stage-4-SOC-SOH算法.md)、[代码](../code/soc/) |
| 库仑效率 | Coulombic efficiency | 充进去的和放出来的不是 1:1。安时积分若当成 1，搁久了 SOC 会漂。均衡课里它和自放电一起造成不齐 | [阶段 4 §4.2](stages/stage-4-SOC-SOH算法.md#42-安时积分库仑计主力但它会梦游-分析) · [Notes05 §二](ece5720-notes05-中文导读.md#二什么造成不齐51) |
| DRA | Discrete-Time Realization Algorithm | 从脉冲响应做出离散模型的四步。仓库里 EKF 的 A 矩阵不是这么辨出来的。读状态空间那章会遇上 | [Notes05 §六](ece5710-notes05-中文导读.md#六dra-四步510) |
| 降阶模型 | Reduced-order model | 把电芯方程收成 MCU 算得动的几阶。讲义里的降阶用来估计，不拿来当保护阈值 | [Notes07 §三](ece5720-notes07-中文导读.md#三sei-全阶模型和它的降阶7275) |
| 满充校准 | Full-charge Reset | CV 截止电流 → 必然 100% → 复位 | [阶段 4 §4.2](stages/stage-4-SOC-SOH算法.md) |
| Thevenin 模型 | 一阶 RC 等效电路 | R0 瞬时压降 + R1C1 慢回弹 | [阶段 4 §4.4](stages/stage-4-SOC-SOH算法.md) |
| HPPC | 混合脉冲功率特性测试 | 打电流脉冲辨识 R0/R1/C1 的标准方法 | [阶段 4 §4.4](stages/stage-4-SOC-SOH算法.md) |
| EKF / UKF | 扩展/无迹卡尔曼滤波 | 预测+修正，谁可信多听谁 | [阶段 4 §4.5](stages/stage-4-SOC-SOH算法.md) |
| 双卡尔曼 | Dual EKF | 快滤波器估 SOC、慢滤波器估容量/内阻 | [阶段 4 §4.6](stages/stage-4-SOC-SOH算法.md) |
| 可观测性 | Observability | 参数只有在电流激励下才"看得见" | [阶段 4 §4.6](stages/stage-4-SOC-SOH算法.md) |
| 残差 | Residual / Innovation | 实测−预测；持续偏大=模型错了不是滤波器错了 | [阶段 4 §4.5](stages/stage-4-SOC-SOH算法.md) |
| 集总热模型 | Lumped thermal model | $C_{th}\\,dT/dt = P - (T-T_{amb})/R_{th}$：整颗电芯当一个温度教 | [共学·热五天](共学/06-热五天.md) |
| 热阻 | Thermal resistance R_th | 每瓦生热换多少 K 稳态温升（K/W）；稳态温度只由它决定 | [共学·热五天 D1](共学/06-热五天.md#第-1-天欧姆火稳态温度是解出来的) |
| 热容 | Thermal capacity C_th | 整颗电芯升 1 K 要多少焦耳（J/K）；是热容不是电容 | [共学·热五天 D2](共学/06-热五天.md#第-2-天升温降温走同一个-τ) |
| 温升时间常数 | Thermal time constant τ=R_th·C_th | 一个 τ 走完剩余温升的 63.2%，升温降温共用同一个 | [共学·热五天 D2](共学/06-热五天.md#第-2-天升温降温走同一个-τ) |
| 可逆热 | Reversible / entropy heat | Π·I，Π=T·∂U/∂T；方向随充放翻，欧姆火不翻 | [共学·热五天 D3](共学/06-热五天.md#第-3-天可逆热充电吸热放电补火) |
| 低通 | Low-pass | 一阶热系统对正弦生热：快纹波压扁、慢平均照收、相位迟到 | [共学·热五天 D4](共学/06-热五天.md#第-4-天正弦负载温度是生热的低通) |

## 通信

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| UART | 通用异步收发 | 商用 BMS 调试口最常见接口；注意电平与共地 | [阶段 5 §5.2](stages/stage-5-通信与集成.md) |
| 共地 | Common ground | 两台设备的地接在一起。包的地和笔记本的地可以差一截，调试口直连会把口烧掉 | [阶段 5 §5.2](stages/stage-5-通信与集成.md#52-uart商用-bms-的方言普通话-应用) |
| RS485 | — | 差分半双工总线；两端 120Ω 终端 + 方向切换是坑 | [阶段 5 §5.3](stages/stage-5-通信与集成.md) |
| Modbus RTU | — | 储能界老干部；帧界靠 3.5 字符静默 | [阶段 5 §5.3](stages/stage-5-通信与集成.md) |
| CAN / CAN FD | 控制器局域网 | 车上官话；显性 0 盖隐性 1 的非破坏仲裁 | [阶段 5 §5.4](stages/stage-5-通信与集成.md) |
| 显性位 | Dominant bit | CAN 里的 0。它能把总线上的 1 盖住，仲裁靠这个。抓第一帧波形时会看见 | [阶段 5 §5.4](stages/stage-5-通信与集成.md#54-can车上的官话-理解) |
| DBC | CAN Database | CAN 报文的"寄存器映射表"：factor/offset 换算 | [阶段 5 §5.4](stages/stage-5-通信与集成.md) |
| SMBus / SBS | 智能电池系统 | 笔记本电池的国际标准命令集 | [阶段 5 §5.5](stages/stage-5-通信与集成.md) |
| BLE / GATT / MTU | 低功耗蓝牙 | 手机 App 监控主流；长帧要协商 MTU+分包重组 | [阶段 5 §5.5](stages/stage-5-通信与集成.md) |
| MQTT | 消息队列遥测传输 | 物联网发布/订阅主力；TLS 与遗嘱消息是底线 | [ESP32 专题](esp32-bms专题.md) §4 |
| CRC | 循环冗余校验 | 五自由度：多项式/初值/反射×2/异或；先用已知帧验证程序 | [阶段 5 §5.6](stages/stage-5-通信与集成.md)、[代码](../code/protocol/) |

## 功能安全与标准

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| ISO 26262 / GB/T 34590 | 道路车辆功能安全 | 车规功能安全母标准 | [阶段 6 §6.4](stages/stage-6-精通与毕业项目.md) |
| HARA | 危害分析与风险评估 | 定安全目标与 ASIL 的前置分析 | [bms-resources §6.3](bms-resources.md) |
| ASIL | 汽车安全完整性等级 | A→D 逐级严格；防过充常 C/D（由 HARA 定） | [阶段 6 §6.4](stages/stage-6-精通与毕业项目.md) |
| FMEA | 失效模式与影响分析 | 逐器件问"它坏了会怎样" | [bms-resources §6.3](bms-resources.md) |
| FTTI | 故障容忍时间间隔 | 约束诊断周期：检测+反应必须小于它 | [阶段 6 §6.4](stages/stage-6-精通与毕业项目.md) |
| IMD | 绝缘监测装置 | 高压包对壳绝缘的专职哨兵；电桥/注入/外置三路线 | [阶段 6 §6.1.3](stages/stage-6-精通与毕业项目.md) |
| Y 电容 | — | 母线对壳滤波电容；绝缘测量稳态窗的量化依据 | [阶段 6 §6.1.3](stages/stage-6-精通与毕业项目.md) |
| SPFM / LFM | 单点/潜伏故障度量 | ASIL 达标要算的两个覆盖率指标 | [bms-resources §6.3](bms-resources.md) |
| GB/T 38661 / 39086 | 车用 BMS 技术条件 / 功能安全要求 | 中国国标，38661 全文公开 | [bms-resources §6.3](bms-resources.md) |
| GB/T 27930 | 充电机-BMS 通信协议 | 直流桩握手：辨识→参数→周期需求→超时停充 | [阶段 5 §5.4.1](stages/stage-5-通信与集成.md) |
| GB/T 32960 | 电动汽车远程服务与管理系统 | 车载终端采集不低于 1 次/s，正常存储可以到 30 s。那是记录。包上该断的这一拍不等它 | [阶段 6 §6.2.6](stages/stage-6-精通与毕业项目.md#626-云端诊断停在包外-评价) |
| 硬件比较器 | Hardware comparator | 不经过 MCU 的那一道切断。标定和云端都不能把它旁路。过充读数冲高时，它仍应在 | [阶段 6 §6.4.1](stages/stage-6-精通与毕业项目.md#641-过充案例开线被当成过充-评价) |
| 安全状态 | Safe state | 故障或看门狗把输出赶到断开。断电以后仍然安全，这条设计才算对 | [详解 ④ §3.2](circuits/04-系统安全与量产.md#32-安全状态设计断电即安全-评价) |
| UL 1973 / IEC 62619 / UN 38.3 | 储能 / 工业 / 运输安全标准 | 按目标市场选读 | [bms-resources §6.3](bms-resources.md) |

## 固件与量产

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| 状态机 | State Machine | BMS 固件的灵魂：迁移集中一处 | [阶段 3 §3.4](stages/stage-3-AFE-MCU智能BMS.md)、[代码](../code/firmware/) |
| 去抖 | Debounce | 连续 N 拍超限才动作，躲开正常瞬态 | [阶段 3 §3.4](stages/stage-3-AFE-MCU智能BMS.md) |
| 锁存 | Latch | 严重故障保持断开，需明确条件才解锁 | [阶段 6 §6.2.2](stages/stage-6-精通与毕业项目.md) |
| DTC | 故障诊断码 + 快照 | 触发瞬间冻结现场；售后能力=快照质量 | [阶段 6 §6.2.2](stages/stage-6-精通与毕业项目.md) |
| UDS | 统一诊断服务 | 车规诊断协议，DTC 的对外格式 | [阶段 6 §6.2.2](stages/stage-6-精通与毕业项目.md) |
| 标定 | Calibration | 出厂写入电流零漂/电压增益等修正系数 | [阶段 6 §6.2.3](stages/stage-6-精通与毕业项目.md) |
| 电流零漂 | Current offset | 没有电流时 ADC 仍有一个数。出厂不把它写进参数区，SOC 一出场就偏 | [阶段 6 §6.2.3](stages/stage-6-精通与毕业项目.md#623-参数与标定系统-应用) |
| EOL | 下线测试 | 出厂前的全项检测清单 | [阶段 6 §6.5](stages/stage-6-精通与毕业项目.md) |
| HIL | 硬件在环 | 电芯模拟器 + 故障注入的测试台 | [阶段 6 §6.5](stages/stage-6-精通与毕业项目.md) |
| 电芯模拟器 | Cell Simulator/Emulator | 电阻分压链或多路隔离电源假装电池串 | [阶段 2 §2.6](stages/stage-2-保护板实践.md) |
| Bootloader / OTA / A/B 双区 | — | 永不被覆盖 + 断电可回滚，两条铁律 | [阶段 6 §6.2.4](stages/stage-6-精通与毕业项目.md) |
| 磨损均衡 | Wear Leveling | 参数区写次数均摊，防 Flash 写穿 | [阶段 6 §6.2.3](stages/stage-6-精通与毕业项目.md) |
| IWDG | 独立看门狗 | 自己带时钟：主时钟死了它还能复位 | [阶段 0 §0.3.1](stages/stage-0-前置知识.md) |
| FreeRTOS | — | MCU 上最主流的实时内核：任务/队列/事件组三件套 | [STM32 专题](stm32-bms专题.md)、[ESP32 专题](esp32-bms专题.md) |
| ESP-IDF | ESP32 IoT Development Framework | ESP32 原生开发框架；Arduino core 的底层就是它 | [ESP32 专题](esp32-bms专题.md) §3 |
| ADC 注入组 | Injected Channel Group | 定时器硬件触发的 ADC 通道组：I/V 同步采样的实现手段 | [STM32 专题](stm32-bms专题.md) §4 |
| PyBaMM | Python Battery Mathematical Modelling | 电化学机理建模的事实标准（前沿方向） | [bms-resources §6.5](bms-resources.md) |
| 无线 BMS | wBMS | 电芯数据经无线节点回传，省去菊花链线束 | [bms-resources §6.5](bms-resources.md) |

---

返回 [学习路线总纲](bms-resources.md) ｜ [器材与预算清单](budget.md)
