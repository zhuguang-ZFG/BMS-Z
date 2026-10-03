# 电路与芯片详解（含动画）

> 电路级、芯片级的深度解析，配 SMIL 动画（GitHub 网页端打开自动播放；本地请用浏览器打开 SVG）。
> 讲解统一使用水路比喻：电压=水压、电流=水流、MOS=闸门、二极管=单向阀。
> 动画同时嵌入在 [阶段教程](../stages/) 的对应章节中。

## 三篇详解

| 篇目 | 内容 | 配套阶段 |
|---|---|---|
| [① 功率回路：MOS、保护与预充](01-功率回路-MOS保护与预充.md) | MOS 结构与背靠背、DW01 芯片级解析、预充回路计算 | 阶段 2 / 6 |
| [② 采样链与 AFE 芯片](02-采样链与AFE芯片.md) | 采样链误差预算、MUX 扫描、开线检测、NTC、BQ769x2 内部、隔离与 isoSPI | 阶段 3 |
| [③ 充电、均衡与计量](03-充电均衡与计量.md) | CC-CV 物理、被动均衡三笔账、主动均衡拓扑、库仑计与校准 | 阶段 2 / 4 |

## 二十个动画

**电池与系统原理**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [锂离子与电子分头行动](assets/li-ion-working.svg) | 充放电时 Li⁺ 走电解液、e⁻ 走外电路 | 阶段 0 |
| [木桶效应](assets/cell-inconsistency-barrel.svg) | 最弱单体锁死整包容量；端电压先撑不住 | 阶段 1 |
| [热失控链](assets/thermal-runaway.svg) | 过充→枝晶→刺穿→起火的四幕剧与 dT/dt 早警 | 阶段 1 / 6 |

**功率回路（详解 ①）**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [背靠背 MOS](assets/mosfet-backtoback.svg) | 为什么一颗 MOS 关不断，两颗才行 | ①（阶段 2 链到详解） |
| [过充保护（DW01）](assets/overcharge-protection.svg) | 电压越线 → OC 拉低 → MOS 断开 → 恢复 | ① / 阶段 2 |
| [短路时间尺度](assets/short-circuit-timeline.svg) | μs 级关断：为什么软件保护来不及 | 阶段 2 |
| [预充回路](assets/precharge.svg) | 上电时序：预充→爬压→合主闸 | ① / 阶段 6 |

**采样链（详解 ②）**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [MUX 扫描采样](assets/mux-scan.svg) | 一颗 ADC 巡逻测 16 串 | ② / 阶段 3 |
| [NTC 测温](assets/ntc-temperature.svg) | 分压电路：温度升 → 阻值降 → 中点电压降 | ② |
| [共模与隔离](assets/isolation-common-mode.svg) | 300V 电位差：直连冒烟 vs 隔离跳过 | ② |
| [isoSPI 菊花链](assets/isospi-daisy.svg) | 数据接力穿隔离墙 | ② / 阶段 6 |

**充电、均衡与计量（详解 ③）**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [CC-CV 充电](assets/cc-cv.svg) | 恒流→恒压→截止全过程 | ③ |
| [被动均衡](assets/passive-balancing.svg) | 高水位电池开阀放热 | ③ |
| [主动均衡](assets/active-balancing.svg) | 电感两拍搬运能量 | ③ |
| [库仑计漂移](assets/coulomb-counting.svg) | 零漂累积与满充校准 | ③ / 阶段 4 |

**算法（阶段 4）**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [OCV-SOC 曲线](assets/ocv-soc-curve.svg) | NCM 斜率 vs LFP 平台区 30mV | 阶段 4 |
| [EKF 融合](assets/ekf-estimation.svg) | 积分预测 + 电压修正，贴住真值 | 阶段 4 |

**通信与固件（阶段 3 / 5）**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [状态机巡游](assets/state-machine.svg) | 令牌走遍 BMS 状态图 | 阶段 3 / 6 |
| [Modbus 帧与差分波形](assets/rs485-modbus-frame.svg) | 8 字节各司其职 + A/B 反相 | 阶段 5 |
| [CAN 仲裁](assets/can-arbitration.svg) | 显性 0 盖过隐性 1，ID 小者胜 | 阶段 5 |

返回 [学习路线总纲](../bms-resources.md)
