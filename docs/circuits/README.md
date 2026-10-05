# 电路与芯片详解（含动画）

> 电路级、芯片级的深度解析，配 SMIL 动画（GitHub 网页端打开自动播放，深浅色随站点主题切换；本地请用浏览器打开 SVG，此时配色跟随系统主题）。
> 详解①③以水路比喻一以贯之：电压=水压、电流=水流、电阻=细管子、电容=蓄水池、MOS=闸门、二极管=单向阀；详解②采样链以芯片手册语言为主。
> 按层进入：[能力地图](../stages/bloom-map.md)。五篇正文的小节标题，以及下面每张动画，都标了布鲁姆层。
> 动画同时嵌入在 [阶段教程](../stages/) 的对应章节中。
> 已经看过原理、只想找公式与调试入口 → [参数速查卡](../参数速查卡.md)。

## 本页目录

按层走先看 [能力地图](../stages/bloom-map.md)。标题末尾的 `[记忆]` … `[创造]` 是布鲁姆层级。

- [电路与芯片详解（含动画）](README.md#电路与芯片详解含动画)
- [五篇详解](README.md#五篇详解)
- [电路动态分析](README.md#电路动态分析)
- [七句口诀](README.md#七句口诀)
- [走线会把过程做坏](README.md#走线会把过程做坏)
- [短自测](README.md#短自测)
- [九十四张动画与电路图](README.md#九十四张动画与电路图)
- [实物图](README.md#实物图)

## 五篇详解

| 篇目 | 内容 | 主层级 | 配套阶段 |
|---|---|---|---|
| [① 功率回路：MOS、保护与预充](01-功率回路-MOS保护与预充.md) | MOS 结构与背靠背、高边/低边驱动、DW01、预充回路计算 | 理解 / 应用 / 评价 | 阶段 2 / 3 / 6 |
| [② 采样链与 AFE 芯片](02-采样链与AFE芯片.md) | 采样链误差预算、MUX 扫描、开线检测、NTC、BQ769x2 内部、隔离与 isoSPI | 分析为主 | 阶段 3 |
| [③ 充电、均衡与计量](03-充电均衡与计量.md) | CC-CV 物理、被动均衡三笔账、主动均衡拓扑、库仑计与校准 | 理解 / 分析 / 评价 | 阶段 2 / 4 |
| [④ 系统安全与量产](04-系统安全与量产.md) | HVIL/IMD/主动放电三件套、接触器粘连检测、E-Gas 三层监控、看门狗安全态、EOL 产线测试与追溯 | 记忆到评价 | 阶段 5 / 6 |
| [⑤ 电路板绘制与设计要点](05-BMS电路板绘制与设计要点.md) | 分区、采样与开尔文、功率与栅极回流、均衡电阻的热、地与隔离净空、投板检查表 | 应用 | 阶段 3 §3.6 |

## 电路动态分析

仓库里原先没有单独的「动态分析」模块。下面七个回路已经按时间在动，正文用同一句式：初始态、扰动、中间态、稳态或保护态。点亮格子不等于看完过程。数量级和示意波形写在各节「算一笔」里，四拍不在那里重复。波形上的数字是示例，不是示波器截图。

| 过程 | 动画 | 看什么在变 |
|---|---|---|
| 预充爬压再合闸 | [预充](assets/precharge.svg) · [和主动放电对照](assets/precharge-vs-discharge.svg) | 母线水位从空爬到接近包压，主闸才合。[详解① §3.2](01-功率回路-MOS保护与预充.md#32-解法与计算-应用) |
| 短路 μs 关断 | [短路时间尺度](assets/short-circuit-timeline.svg) | 电流先冲上去，硬件比较器在软件醒来前关断。[阶段 2 §2.3](../stages/stage-2-保护板实践.md#23-多节保护s-8254a-与多通道芯片-理解) |
| 主动放电泄压 | [主动放电](assets/active-discharge.svg) | 触点分开之后，小电阻把母线电容上的电压拉下来。[详解④ §1.3](04-系统安全与量产.md#13-主动放电碰撞后的-5-秒钟-理解) |
| HVIL 先断信号 | [互锁环](assets/hvil-loop.svg) · [断环顺序](assets/hvil-break-order.svg) | 环先断，接触器再开，母线最后才掉。[阶段 6 §6.1.1](../stages/stage-6-精通与毕业项目.md#611-高压电池系统架构-分析) |
| 均衡能量流动 | [被动](assets/passive-balancing.svg) · [主动](assets/active-balancing.svg) · [去向对照](assets/balance-energy-fate.svg) | 被动水位进电阻变热；主动先吸进电感再倒给低节。[详解③ §2](03-充电均衡与计量.md#2-被动均衡电路热与调度-分析) |
| MUX 扫描时序 | [MUX 扫描](assets/mux-scan.svg) | 同一颗 ADC 逐串接通，读数一块一块换，不是同一瞬间。[详解② §2](02-采样链与AFE芯片.md#2-mux-巡逻式测量一颗-adc-测-16-串-理解) |
| 粘连检测 | [粘连检测](assets/contactor-weld-check.svg) | 命令断开后，正常侧电压掉到 0；粘连侧停在包压附近。[详解④ §2.2](04-系统安全与量产.md#22-粘连检测命令断了电断没断-分析) |

七句可以先背。走线把过程做坏的对照在下一节，板级句子在 [详解⑤](05-BMS电路板绘制与设计要点.md#7-五张对照-理解)。

### 七句口诀

- **预充**　先小电流灌满母线电容，再合主闸。看 [预充](assets/precharge.svg)。
- **短路**　短路按微秒关。软件那一拍来不及。看 [短路时间尺度](assets/short-circuit-timeline.svg)。
- **主动放电**　先确认接触器已经断开，再用小电阻把母线拉下来。看 [主动放电](assets/active-discharge.svg)。
- **HVIL**　环先断，闸再开。人碰到端子之前，高压先离开。看 [断环顺序](assets/hvil-break-order.svg)。
- **均衡**　高的那节把水放进电阻，变成热。主动则是高节吸进电感，再倒给低节。看 [去向对照](assets/balance-energy-fate.svg)。
- **MUX**　一颗 ADC 轮流看每一串。这一拍的电压不是同一瞬间。看 [MUX 扫描](assets/mux-scan.svg)。
- **粘连**　命令已经断开，负载侧电压还不掉，就是粘连。看 [粘连检测](assets/contactor-weld-check.svg)。

### 走线会把过程做坏

动画里的四拍，假定铜已经按回路走对了。下面四张对照说明走线一错，时间过程先失败。隔离槽上的铜桥、分区和投板检查表在 [详解⑤](05-BMS电路板绘制与设计要点.md)。

| 走线 | 动画 | 时间过程怎样失败 |
|---|---|---|
| 栅极回路绕远 | [栅极回流](assets/gate-return-loop.svg) | 关断变慢，短路的微秒窗口先被环路电感吃掉 |
| 采样贴着功率铜 | [采样贴着功率](assets/sense-beside-power.svg) | 读数跟着电流跳，去抖会把噪声当成越线 |
| 电压从螺丝端子取 | [开尔文与两线](assets/kelvin-vs-twowire.svg) | 安时积分按偏大的电流累加 |
| 均衡电阻贴着基准 | [热烤基准](assets/ref-heat-couple.svg) | 误差跟着温度走，常温标定留不住 |

### 短自测

1. 预充电压爬不到接近包压。主闸还合吗？
2. 短路只交给软件的毫秒轮询。示例取 500 A，10 μs 切断和 1 ms 切断，I²t 差几倍？
3. HVIL 的去抖拉到 500 ms。人先碰到的是什么？
4. 粘连检测在线圈断电后 100 ms 就采样。示例 τ = 1 s、包压 400 V，正常断开的负载侧大约还剩多少伏？

<details>
<summary><b>参考答案（先自己想完再展开）</b></summary>

1. 不合。爬不上来就停在故障。空着的母线电容上直接合主闸，触点会打火粘连。
2. 大约 100 倍。10 μs 时 I²t = 500² × 10 μs = 2.5 A²s；1 ms 时是 250 A²s。硬件比较器要在软件醒来前关断。2 μs、10 μs 仍是示意，以保护 IC 手册为准。
3. 还带包压的端子。针脚长短差是第一道：信号针短、先断。去抖是第二道，要远短于拔插头。示例里大约 15 ms 下令开闸、30 ms 母线开始掉；500 ms 时人可以先碰到端子。
4. 大约 360 V（400 × e^{−0.1}）。正常侧这时还很高，会把已经断开误判成粘连。要等衰减窗口，或同时看电池侧和负载侧。真实窗口用本包的 Y 电容和泄放电阻重算。

</details>

**练完你会怎样**：预充爬不上来你不合主闸。短路你交给硬件的微秒。HVIL 去抖拉太长，你知道人会先碰到端子。数字都是示例。


## 九十四张动画与电路图

**学习路线**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [BMS 学习路线总览](assets/bms-roadmap.svg) | 光点逐站巡游七个阶段，终点星闪烁 | 理解 | 根 README 阶段教程节 |

**电池与系统原理**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [锂离子与电子分头行动](assets/li-ion-working.svg) | 充放电时 Li⁺ 走电解液、e⁻ 走外电路 | 理解 | 阶段 0 |
| [液态、固态与结构电池对照](assets/solid-vs-structural-cell.svg) | 离子走液体还是固体；碳纤维是电极还是外壳。示意图，不是实拍 | 理解 | 阶段 0 §0.1.8 |
| [包级采样与保护](assets/pack-manual-sampling.svg) | 钠离子包和固态/结构电池包的采样；寄存器与阈值格留空。示意图·待公开手册 | 理解 | [包级手册缺口](../t13-包级手册缺口.md) |
| [钠离子与锂离子电压窗口](assets/na-ion-vs-li-ion.svg) | 锂电 4.2 V 示例和一篇钠电软包实验的 3.80 / 4.00 V。示意图，不是实拍 | 理解 | 阶段 0 §0.1.10 |
| [过放铜溶解](assets/overdischarge-copper.svg) | 过放时铜离子离开集流体，再充电长成针 | 理解 | 阶段 0 §0.1.3 |
| [木桶效应](assets/cell-inconsistency-barrel.svg) | 最弱单体锁死整包容量；端电压先撑不住 | 理解 | 阶段 1 |
| [热失控链](assets/thermal-runaway.svg) | 过充→枝晶→刺穿→起火的四幕剧与 dT/dt 早警 | 理解 | 阶段 1 / 6 |
| [内阻压降与回弹](assets/internal-resistance.svg) | 带载「腿软」I·R、卸载回弹；老化腿更软 | 理解 | 阶段 0 |
| [温度的两副面孔](assets/temperature-two-faces.svg) | 低温充电析锂 vs 高温老化加速 | 理解 | 阶段 0 |
| [C 倍率](assets/c-rate.svg) | 0.5C/1C/2C 三种龙头开度对比 | 理解 | 阶段 0 |
| [串并联成组](assets/series-parallel-pack.svg) | 4S2P：串联抬压、并联扩容；采样按并联块 | 理解 | 阶段 1 |
| [并联块只有一个电压](assets/parallel-tap-boundary.svg) | 对：一路抽头。错：把并联的两颗当成两路。示意图 | 理解 | 阶段 1 |

**功率回路（详解 ①）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [背靠背 MOS](assets/mosfet-backtoback.svg) | 为什么一颗 MOS 关不断，两颗才行 | 理解 | ①（阶段 2 链到详解） |
| [过充保护（DW01）](assets/overcharge-protection.svg) | 电压越线 → OC 拉低 → MOS 断开 → 恢复 | 理解 | ① / 阶段 2 |
| [短路时间尺度](assets/short-circuit-timeline.svg) | μs 级关断：为什么软件保护来不及 | 理解 | 阶段 2 |
| [预充回路](assets/precharge.svg) | 上电时序：预充→爬压→合主闸 | 应用 | ① / 阶段 6 |
| [预充与主动放电时序](assets/precharge-vs-discharge.svg) | 预充在合主闸前；主动放电在触点分开后。示意图 | 理解 | ④ / 阶段 6 |
| [保护去抖与回差](assets/protection-debounce.svg) | 毛刺清零不动作；持续超限才断；回差防颤 | 理解 | 阶段 1 |
| [MOS 导通发热](assets/mos-rdson-heating.svg) | I²R 平方发热 + 正温系数正反馈 | 分析 | 阶段 2 |
| [高边驱动与自举](assets/highside-gate-drive.svg) | 栅压顶到母线之上；自举不能常开 | 评价 | 阶段 3 |
| [DW01 保护板电路图](assets/dw01-protection-schematic.svg) | 单节保护典型应用：三道判断怎么接两颗 MOS（充放电流向动画） | 理解 | ① / 阶段 2 |
| [DW01 丝印位置示意图](assets/dw01-silkscreen-callout.svg) | 六脚保护 IC 与八脚双 MOS 先对印字。示意图，不是实拍 | 应用 | 阶段 2 §2.2 |
| [分压链实测台示意图](assets/divider-testbench.svg) | 一台电源、电阻分压、保护板、万用表。不要用真电池做过充 | 应用 | 阶段 2 §2.6 |
| [同框分压实测台接线](assets/divider-bench-same-frame.svg) | 电源、分压链、保护板、万用表画在同一框。示意图·待实拍 | 应用 | 阶段 2 §2.6 |

**采样链（详解 ②）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [MUX 扫描采样](assets/mux-scan.svg) | 一颗 ADC 巡逻测 16 串 | 理解 | ② / 阶段 3 |
| [NTC 测温](assets/ntc-temperature.svg) | 分压电路：温度升 → 阻值降 → 中点电压降 | 理解 | ② |
| [共模与隔离](assets/isolation-common-mode.svg) | 300V 电位差：直连冒烟 vs 隔离跳过 | 理解 | ② |
| [isoSPI 菊花链](assets/isospi-daisy.svg) | 数据接力穿隔离墙 | 理解 | ② / 阶段 6 |
| [BQ769 评估板与 isoSPI 线束](assets/bq769-evb-isospi.svg) | 评估板采样座和变压器隔离的菊花链。示意图·待实拍 | 分析 | ② §5 |
| [四线开尔文](assets/shunt-kelvin.svg) | 采样取本体内侧，剔除走线压降 | 分析 | 阶段 2 |
| [ADC 量化与误差](assets/adc-quantization.svg) | 分辨率 ≠ 精度；基准一偏全偏 | 理解 | 阶段 0 |
| [AFE 寄存器读取](assets/afe-register-read.svg) | I2C 时序 + CRC 校验重读 + 快照 | 应用 | 阶段 3 |
| [采样链误差预算瀑布](assets/error-budget-waterfall.svg) | 五级误差累加超预算；标定压回 1.8mV | 分析 | ② §1 |

**充电、均衡与计量（详解 ③）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [CC-CV 充电](assets/cc-cv.svg) | 恒流→恒压→截止全过程 | 理解 | ③ |
| [被动均衡](assets/passive-balancing.svg) | 高水位电池开阀放热 | 理解 | ③ |
| [能量去向对照](assets/balance-energy-fate.svg) | 被动进电阻变热；主动交给低节。示意图，不写效率 | 理解 | ③ |
| [主动均衡](assets/active-balancing.svg) | 电感两拍搬运能量 | 评价 | ③ |
| [均衡拓扑对照](assets/balance-topology-compare.svg) | 同一模型里被动、节到节、节到包、包到节。示意图，不是效率实测 | 评价 | ③ §3.1 |
| [同一工作点效率空表](assets/balance-efficiency-blank.svg) | 4 串电感与 4 串开关电容，η 留空。示意图·待实测 | 评价 | ③ §3.1 |
| [库仑计漂移](assets/coulomb-counting.svg) | 零漂累积与满充校准 | 分析 | ③ / 阶段 4 |

**算法（阶段 4）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [OCV-SOC 曲线](assets/ocv-soc-curve.svg) | NCM 斜率 vs LFP 平台区 30mV | 分析 | 阶段 4 |
| [平台区为何不信电压](assets/ocv-plateau-distrust.svg) | 同一小段毫伏可以对应差很远的荷电。示意图 | 分析 | 阶段 4 |
| [EKF 融合](assets/ekf-estimation.svg) | 积分预测 + 电压修正，贴住真值 | 分析 | 阶段 4 |
| [卡尔曼增益](assets/kalman-gain.svg) | 信任分配；LFP 平台区少信电压 | 分析 | 阶段 4 |
| [SOP 多约束降额](assets/sop-derating.svg) | 最短板 + 时间窗分级 + 平滑输出 | 分析 | 阶段 4 |
| [SOH 老化双指标](assets/soh-aging.svg) | 容量滑向 80% EOL；内阻上翘先咬 SOP | 分析 | 阶段 4 §4.6 |
| [OCV 滞回](assets/ocv-hysteresis.svg) | 同一 SOC 充电高放电低；单表落中间两头错 | 分析 | 阶段 4 §4.3 |
| [极化的物理图景](assets/polarization-physics.svg) | 表面锂离子被抽空 → 静置扩散回匀 → 电压回弹 | 理解 | 阶段 4 §4.3 |
| [一阶 vs 二阶 RC](assets/second-order-rc.svg) | 真实曲线前段快陷，一阶拟合不了；快慢两支路各管一段 | 分析 | 阶段 4 §4.4 |

**通信与固件（阶段 3 / 5）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [状态机巡游](assets/state-machine.svg) | 令牌走遍 BMS 状态图 | 应用 | 阶段 3 / 6 |
| [Modbus 帧与差分波形](assets/rs485-modbus-frame.svg) | 8 字节各司其职 + A/B 反相 | 应用 | 阶段 5 |
| [CAN 仲裁](assets/can-arbitration.svg) | 显性 0 盖过隐性 1，ID 小者胜 | 理解 | 阶段 5 |
| [GB/T 27930 握手](assets/gbt-27930-handshake.svg) | 五阶段时序剧：BMS 要电、充电机跟随 | 分析 | 阶段 5 |
| [UART 字节状态机](assets/uart-byte-machine.svg) | 找帧头、收长度、对 CRC；坏帧计数后重新同步 | 应用 | 阶段 5 §5.2 |
| [Modbus RTU 静默划帧](assets/modbus-rtu-silence.svg) | 帧间 3.5 字符结束一帧；帧内超过 1.5 字符则丢帧 | 理解 | 阶段 5 §5.3 |
| [BLE MTU 与重组](assets/ble-mtu-reassembly.svg) | 默认 MTU 23 把长帧切碎；谈大之后仍要按长度拼回去 | 理解 | 阶段 5 §5.5 |
| [SMBus 命令往返](assets/smbus-sbs-roundtrip.svg) | 先写 Voltage() 命令字，再读回两个字节 | 理解 | 阶段 5 §5.5 |

**高压系统（阶段 6）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [高压互锁 HVIL](assets/hvil-loop.svg) | 低压环看住高压口；信号先于高压断 | 理解 | 阶段 6 |
| [HVIL 断环顺序](assets/hvil-break-order.svg) | 环断开，接触器打开，母线再掉下来。错序对照。示意图 | 理解 | 阶段 6 |
| [主动放电](assets/active-discharge.svg) | 被动泄放很慢；确认断开后再用小电阻在数秒内拉低母线 | 理解 | 详解④ §1.3 |
| [主动放电电阻在接触器旁](assets/active-discharge-beside-contactor.svg) | 左半是已有的预充实拍位置，右半是待实拍的放电电阻 | 理解 | 详解④ §1.3 |
| [绝缘检测电桥](assets/imd-bridge.svg) | 两次投切换来两个方程，解出 R_iso± | 分析 | 阶段 6 |
| [并簇环流](assets/parallel-cluster-circulating.svg) | 压差落在毫欧上 → 数百安对冲 | 分析 | 阶段 6 |
| [DTC 故障快照](assets/dtc-snapshot.svg) | 越线一瞬冻结 U/I/T/SOC/时间戳 | 应用 | 阶段 6 §6.2.2 |
| [快照回放](assets/dtc-snapshot-replay.svg) | 过充帧先冻结，随后的短路不覆盖。示意图，不是实验台照片 | 应用 | 阶段 6 §6.2.5 |
| [电池 HIL 实验台场景](assets/hil-bench-scene.svg) | 可编程电源、故障注入、被测 BMS、上位机。示意图·待实拍 | 应用 | 阶段 6 §6.2.5 |
| [云端与包端切断](assets/cloud-vs-pack-protection.svg) | 包上先断，报文可以晚到 30 s 量级。示意图，不是平台截图 | 评价 | 阶段 6 §6.2.6 |
| [电池云仪表盘](assets/cloud-bms-dashboard.svg) | 各串电压、包内 DTC、留在包上的切断。示意图·待实拍 | 评价 | 阶段 6 §6.2.6 |
| [被动均衡分时调度](assets/balance-scheduling.svg) | 入口条件门控 → 泄放/关断/复测轮询 → 压差收敛 | 应用 | 阶段 6 §6.3 |
| [HIL 测试台](assets/hil-testbench.svg) | 电芯模拟器 + 故障注入矩阵 + 上位机自动判定 | 评价 | 阶段 6 §6.5 |
| [过充安全路径](assets/asil-overcharge-path.svg) | 先查开线，硬件比较器不经过 MCU。示意图 | 评价 | 阶段 6 §6.4.1 |
| [认证现场三件事](assets/cert-floor-scene.svg) | 失效注入、硬件比较器、见证记录。示意图·待实拍 | 评价 | 阶段 6 §6.4.1 |
| [电芯追溯链](assets/cell-trace-chain.svg) | 二维码到包序列号；错芯不能靠均衡抹平。示意图 | 评价 | 阶段 6 §6.5.1 |
| [热管理三路线](assets/thermal-paths.svg) | 风冷/液冷/直冷散热路径对比，BMS 测温降额职责不变 | 评价 | 阶段 6 §6.1.6 |
| [接触器粘连检测](assets/contactor-weld-check.svg) | 命令断开后读负载侧电压：掉不下去 = 熔焊粘连 | 分析 | 详解④ §2.2 |
| [看门狗与安全态](assets/watchdog-safestate.svg) | 喂狗停止→复位；硬件钳位让失控=断高压 | 评价 | 详解④ §3.2 |
| [采样线断线检测](assets/open-wire-detection.svg) | 悬空引脚被检测电流推向异常电平，先信线再信数 | 分析 | 详解④ §3.4 |
| [最弱单体反极](assets/cell-reversal.svg) | 放电末端弱节被同伴电流反向充电，永久损伤 | 理解 | 阶段 1 §1.2 |

**MCU 与通信（STM32 / ESP32 专题）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [STM32 ADC 注入组同步采样](assets/stm32-adc-injected.svg) | 定时器触发 I/V 背靠背转换 + DMA，对比软件轮询时差 | 应用 | [STM32 专题](../stm32-bms专题.md) §4 |
| [ESP32 睡眠-唤醒电流剖面](assets/esp32-sleep-current.svg) | 10µA 平台 + 150mA 尖峰，占空比算平均电流 | 分析 | [ESP32 专题](../esp32-bms专题.md) §5 |
| [MQTT 发布订阅与遗嘱](assets/mqtt-pubsub-will.svg) | broker 转发；断连代发「离线」遗嘱 | 应用 | [ESP32 专题](../esp32-bms专题.md) §4 |

**示意波形（示例值，不是示波器截图）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [预充 RC 示例](assets/precharge-rc-example.svg) | 400 V、1 mF、170 Ω，约 0.51 s 到 95%，储能 80 J | 应用 | 详解① §3.2 |
| [短路 I²t 时窗](assets/short-i2t-window.svg) | 500 A：10 μs 约 2.5 A²s，1 ms 约 250 A²s | 理解 | 阶段 2 §2.3 |
| [主动放电能量与时间](assets/discharge-energy-time.svg) | 80 J；47 kΩ 约 89 s，200 Ω 约 0.38 s 到 60 V | 理解 | 详解④ §1.3 |
| [HVIL 毫秒时序](assets/hvil-ms-timing.svg) | 环先断，约 15 ms 开闸，约 30 ms 母线开始掉 | 理解 | 阶段 6 §6.1.1 |
| [均衡功耗与一拍能量](assets/balance-heat-example.svg) | 被动约 0.18 W；主动一拍约 20 μJ。不写效率百分数 | 分析 | 详解③ §2 |
| [MUX 扫描时差](assets/mux-time-skew.svg) | 一圈 1.6 ms 的示例里，首尾可以差 50 mV | 理解 | 详解② §2 |
| [粘连检测衰减窗口](assets/weld-decay-window.svg) | τ = 1 s 时，100 ms 仍约 360 V，5 s 约 3 V | 分析 | 详解④ §2.2 |

**电路板对照（示意图）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [采样线靠近功率回路](assets/sense-beside-power.svg) | 贴着粗铜走，读数在示例的 3.65 V 与 3.78 V 之间跳 | 应用 | 详解⑤ §2 |
| [开尔文与两线](assets/kelvin-vs-twowire.svg) | 引线 0.4 mΩ 算进去，100 A 读成 180 A | 分析 | 详解② §8 / ⑤ §2 |
| [栅极回流环](assets/gate-return-loop.svg) | 回流绕远，关断变慢 | 应用 | 详解⑤ §3 |
| [隔离槽上的铜桥](assets/isolation-copper-bridge.svg) | 铜把电池侧和通信侧接上 | 应用 | 详解⑤ §5 |
| [热耦合到基准](assets/ref-heat-couple.svg) | 均衡电阻贴着基准，整串读数一起偏 | 应用 | 详解⑤ §4 |

## 实物图

成品保护板、电芯、万用表、NTC、检流电阻、平衡插头、直流电源、密封接触器、线绕电阻、笔记本气量计、保护 IC 特写、带 DW01A/8205A 的单节充电保护板、和主接触器同框的预充电阻、博物馆里的 Faradion 钠离子电池、锂离子电极涂布设备、LibreSolar BMS C1、DIY BQ76940、OVMS 仪表盘、INL / ORNL / DOE 电池试验室、两张电芯仿真器表征台，以及 EcoMat 的 TL431 均衡电路图，在 [assets/photos/](assets/photos/)，来源与授权写在 [PHOTOS.md](assets/photos/PHOTOS.md)。同框分压实测台、TI 官方 BQ769 评估板、isoSPI 线束、主动放电电阻，以及「被测 BMS 在环」的完整 HIL 和功能安全见证现场，仍没有可转载实拍，正文里用标明「示意图·待实拍」的动画。包级采样那张标「待公开手册」。还缺的实拍记在 [共建任务板](../共建任务板.md) T11。涂布设备不是化成或分选工位。LibreSolar 和 DIY 板不是 TI 官方 EVM。试验室照片不是见证现场。仿真器表征台里没有被测 BMS。

返回 [学习路线总纲](../bms-resources.md)
