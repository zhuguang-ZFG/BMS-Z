# 电路与芯片详解（含动画）

> 电路级、芯片级的深度解析，配 SMIL 动画（GitHub 网页端打开自动播放，深浅色随站点主题切换；本地请用浏览器打开 SVG，此时配色跟随系统主题）。
> 详解①③以水路比喻一以贯之：电压=水压、电流=水流、电阻=细管子、电容=蓄水池、MOS=闸门、二极管=单向阀；详解②采样链以芯片手册语言为主。
> 动画同时嵌入在 [阶段教程](../stages/) 的对应章节中。

## 三篇详解

| 篇目 | 内容 | 配套阶段 |
|---|---|---|
| [① 功率回路：MOS、保护与预充](01-功率回路-MOS保护与预充.md) | MOS 结构与背靠背、高边/低边驱动、DW01、预充回路计算 | 阶段 2 / 3 / 6 |
| [② 采样链与 AFE 芯片](02-采样链与AFE芯片.md) | 采样链误差预算、MUX 扫描、开线检测、NTC、BQ769x2 内部、隔离与 isoSPI | 阶段 3 |
| [③ 充电、均衡与计量](03-充电均衡与计量.md) | CC-CV 物理、被动均衡三笔账、主动均衡拓扑、库仑计与校准 | 阶段 2 / 4 |

## 四十张动画与电路图

**学习路线**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [BMS 学习路线总览](assets/bms-roadmap.svg) | 光点逐站巡游七个阶段，终点星闪烁 | 根 README 阶段教程节 |

**电池与系统原理**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [锂离子与电子分头行动](assets/li-ion-working.svg) | 充放电时 Li⁺ 走电解液、e⁻ 走外电路 | 阶段 0 |
| [木桶效应](assets/cell-inconsistency-barrel.svg) | 最弱单体锁死整包容量；端电压先撑不住 | 阶段 1 |
| [热失控链](assets/thermal-runaway.svg) | 过充→枝晶→刺穿→起火的四幕剧与 dT/dt 早警 | 阶段 1 / 6 |
| [内阻压降与回弹](assets/internal-resistance.svg) | 带载「腿软」I·R、卸载回弹；老化腿更软 | 阶段 0 |
| [温度的两副面孔](assets/temperature-two-faces.svg) | 低温充电析锂 vs 高温老化加速 | 阶段 0 |
| [C 倍率](assets/c-rate.svg) | 0.5C/1C/2C 三种龙头开度对比 | 阶段 0 |
| [串并联成组](assets/series-parallel-pack.svg) | 4S2P：串联抬压、并联扩容；采样按并联块 | 阶段 1 |

**功率回路（详解 ①）**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [背靠背 MOS](assets/mosfet-backtoback.svg) | 为什么一颗 MOS 关不断，两颗才行 | ①（阶段 2 链到详解） |
| [过充保护（DW01）](assets/overcharge-protection.svg) | 电压越线 → OC 拉低 → MOS 断开 → 恢复 | ① / 阶段 2 |
| [短路时间尺度](assets/short-circuit-timeline.svg) | μs 级关断：为什么软件保护来不及 | 阶段 2 |
| [预充回路](assets/precharge.svg) | 上电时序：预充→爬压→合主闸 | ① / 阶段 6 |
| [保护去抖与回差](assets/protection-debounce.svg) | 毛刺清零不动作；持续超限才断；回差防颤 | 阶段 1 |
| [MOS 导通发热](assets/mos-rdson-heating.svg) | I²R 平方发热 + 正温系数正反馈 | 阶段 2 |
| [高边驱动与自举](assets/highside-gate-drive.svg) | 栅压顶到母线之上；自举不能常开 | 阶段 3 |
| [DW01 保护板电路图](assets/dw01-protection-schematic.svg) | 单节保护典型应用：三道判断怎么接两颗 MOS（充放电流向动画） | ① / 阶段 2 |

**采样链（详解 ②）**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [MUX 扫描采样](assets/mux-scan.svg) | 一颗 ADC 巡逻测 16 串 | ② / 阶段 3 |
| [NTC 测温](assets/ntc-temperature.svg) | 分压电路：温度升 → 阻值降 → 中点电压降 | ② |
| [共模与隔离](assets/isolation-common-mode.svg) | 300V 电位差：直连冒烟 vs 隔离跳过 | ② |
| [isoSPI 菊花链](assets/isospi-daisy.svg) | 数据接力穿隔离墙 | ② / 阶段 6 |
| [四线开尔文](assets/shunt-kelvin.svg) | 采样取本体内侧，剔除走线压降 | 阶段 2 |
| [ADC 量化与误差](assets/adc-quantization.svg) | 分辨率 ≠ 精度；基准一偏全偏 | 阶段 0 |
| [AFE 寄存器读取](assets/afe-register-read.svg) | I2C 时序 + CRC 校验重读 + 快照 | 阶段 3 |

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
| [卡尔曼增益](assets/kalman-gain.svg) | 信任分配；LFP 平台区少信电压 | 阶段 4 |
| [SOP 多约束降额](assets/sop-derating.svg) | 最短板 + 时间窗分级 + 平滑输出 | 阶段 4 |

**通信与固件（阶段 3 / 5）**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [状态机巡游](assets/state-machine.svg) | 令牌走遍 BMS 状态图 | 阶段 3 / 6 |
| [Modbus 帧与差分波形](assets/rs485-modbus-frame.svg) | 8 字节各司其职 + A/B 反相 | 阶段 5 |
| [CAN 仲裁](assets/can-arbitration.svg) | 显性 0 盖过隐性 1，ID 小者胜 | 阶段 5 |
| [GB/T 27930 握手](assets/gbt-27930-handshake.svg) | 五阶段时序剧：BMS 要电、充电机跟随 | 阶段 5 |

**高压系统（阶段 6）**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [高压互锁 HVIL](assets/hvil-loop.svg) | 低压环看住高压口；信号先于高压断 | 阶段 6 |
| [绝缘检测电桥](assets/imd-bridge.svg) | 两次投切换来两个方程，解出 R_iso± | 阶段 6 |
| [并簇环流](assets/parallel-cluster-circulating.svg) | 压差落在毫欧上 → 数百安对冲 | 阶段 6 |


**MCU 与通信（STM32 / ESP32 专题）**

| 动画 | 演示 | 出现位置 |
|---|---|---|
| [STM32 ADC 注入组同步采样](assets/stm32-adc-injected.svg) | 定时器触发 I/V 背靠背转换 + DMA，对比软件轮询时差 | [STM32 专题](../stm32-bms专题.md) §4 |
| [ESP32 睡眠-唤醒电流剖面](assets/esp32-sleep-current.svg) | 10µA 平台 + 150mA 尖峰，占空比算平均电流 | [ESP32 专题](../esp32-bms专题.md) §5 |

返回 [学习路线总纲](../bms-resources.md)
