# 电路与芯片详解（含动画）

> 电路级、芯片级的深度解析，配 SMIL 动画（GitHub 网页端打开自动播放，深浅色随站点主题切换；本地请用浏览器打开 SVG，此时配色跟随系统主题）。
> 详解①③以水路比喻一以贯之：电压=水压、电流=水流、电阻=细管子、电容=蓄水池、MOS=闸门、二极管=单向阀；详解②采样链以芯片手册语言为主。
> 按层进入：[能力地图](../stages/bloom-map.md)。四篇正文的小节标题，以及下面每张动画，都标了布鲁姆层。
> 动画同时嵌入在 [阶段教程](../stages/) 的对应章节中。
> 已经看过原理、只想找公式与调试入口 → [参数速查卡](../参数速查卡.md)。

## 本页目录

按层走先看 [能力地图](../stages/bloom-map.md)。标题末尾的 `[记忆]` … `[创造]` 是布鲁姆层级。

- [电路与芯片详解（含动画）](README.md#电路与芯片详解含动画)
- [四篇详解](README.md#四篇详解)
- [五十七张动画与电路图](README.md#五十七张动画与电路图)
- [实物图](README.md#实物图)

## 四篇详解

| 篇目 | 内容 | 主层级 | 配套阶段 |
|---|---|---|---|
| [① 功率回路：MOS、保护与预充](01-功率回路-MOS保护与预充.md) | MOS 结构与背靠背、高边/低边驱动、DW01、预充回路计算 | 理解 / 应用 / 评价 | 阶段 2 / 3 / 6 |
| [② 采样链与 AFE 芯片](02-采样链与AFE芯片.md) | 采样链误差预算、MUX 扫描、开线检测、NTC、BQ769x2 内部、隔离与 isoSPI | 分析为主 | 阶段 3 |
| [③ 充电、均衡与计量](03-充电均衡与计量.md) | CC-CV 物理、被动均衡三笔账、主动均衡拓扑、库仑计与校准 | 理解 / 分析 / 评价 | 阶段 2 / 4 |
| [④ 系统安全与量产](04-系统安全与量产.md) | HVIL/IMD/主动放电三件套、接触器粘连检测、E-Gas 三层监控、看门狗安全态、EOL 产线测试与追溯 | 记忆到评价 | 阶段 5 / 6 |

## 五十七张动画与电路图

**学习路线**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [BMS 学习路线总览](assets/bms-roadmap.svg) | 光点逐站巡游七个阶段，终点星闪烁 | 理解 | 根 README 阶段教程节 |

**电池与系统原理**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [锂离子与电子分头行动](assets/li-ion-working.svg) | 充放电时 Li⁺ 走电解液、e⁻ 走外电路 | 理解 | 阶段 0 |
| [过放铜溶解](assets/overdischarge-copper.svg) | 过放时铜离子离开集流体，再充电长成针 | 理解 | 阶段 0 §0.1.3 |
| [木桶效应](assets/cell-inconsistency-barrel.svg) | 最弱单体锁死整包容量；端电压先撑不住 | 理解 | 阶段 1 |
| [热失控链](assets/thermal-runaway.svg) | 过充→枝晶→刺穿→起火的四幕剧与 dT/dt 早警 | 理解 | 阶段 1 / 6 |
| [内阻压降与回弹](assets/internal-resistance.svg) | 带载「腿软」I·R、卸载回弹；老化腿更软 | 理解 | 阶段 0 |
| [温度的两副面孔](assets/temperature-two-faces.svg) | 低温充电析锂 vs 高温老化加速 | 理解 | 阶段 0 |
| [C 倍率](assets/c-rate.svg) | 0.5C/1C/2C 三种龙头开度对比 | 理解 | 阶段 0 |
| [串并联成组](assets/series-parallel-pack.svg) | 4S2P：串联抬压、并联扩容；采样按并联块 | 理解 | 阶段 1 |

**功率回路（详解 ①）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [背靠背 MOS](assets/mosfet-backtoback.svg) | 为什么一颗 MOS 关不断，两颗才行 | 理解 | ①（阶段 2 链到详解） |
| [过充保护（DW01）](assets/overcharge-protection.svg) | 电压越线 → OC 拉低 → MOS 断开 → 恢复 | 理解 | ① / 阶段 2 |
| [短路时间尺度](assets/short-circuit-timeline.svg) | μs 级关断：为什么软件保护来不及 | 理解 | 阶段 2 |
| [预充回路](assets/precharge.svg) | 上电时序：预充→爬压→合主闸 | 应用 | ① / 阶段 6 |
| [保护去抖与回差](assets/protection-debounce.svg) | 毛刺清零不动作；持续超限才断；回差防颤 | 理解 | 阶段 1 |
| [MOS 导通发热](assets/mos-rdson-heating.svg) | I²R 平方发热 + 正温系数正反馈 | 分析 | 阶段 2 |
| [高边驱动与自举](assets/highside-gate-drive.svg) | 栅压顶到母线之上；自举不能常开 | 评价 | 阶段 3 |
| [DW01 保护板电路图](assets/dw01-protection-schematic.svg) | 单节保护典型应用：三道判断怎么接两颗 MOS（充放电流向动画） | 理解 | ① / 阶段 2 |
| [DW01 丝印位置示意图](assets/dw01-silkscreen-callout.svg) | 六脚保护 IC 与八脚双 MOS 先对印字。示意图，不是实拍 | 应用 | 阶段 2 §2.2 |
| [分压链实测台示意图](assets/divider-testbench.svg) | 一台电源、电阻分压、保护板、万用表。不要用真电池做过充 | 应用 | 阶段 2 §2.6 |

**采样链（详解 ②）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [MUX 扫描采样](assets/mux-scan.svg) | 一颗 ADC 巡逻测 16 串 | 理解 | ② / 阶段 3 |
| [NTC 测温](assets/ntc-temperature.svg) | 分压电路：温度升 → 阻值降 → 中点电压降 | 理解 | ② |
| [共模与隔离](assets/isolation-common-mode.svg) | 300V 电位差：直连冒烟 vs 隔离跳过 | 理解 | ② |
| [isoSPI 菊花链](assets/isospi-daisy.svg) | 数据接力穿隔离墙 | 理解 | ② / 阶段 6 |
| [四线开尔文](assets/shunt-kelvin.svg) | 采样取本体内侧，剔除走线压降 | 分析 | 阶段 2 |
| [ADC 量化与误差](assets/adc-quantization.svg) | 分辨率 ≠ 精度；基准一偏全偏 | 理解 | 阶段 0 |
| [AFE 寄存器读取](assets/afe-register-read.svg) | I2C 时序 + CRC 校验重读 + 快照 | 应用 | 阶段 3 |
| [采样链误差预算瀑布](assets/error-budget-waterfall.svg) | 五级误差累加超预算；标定压回 1.8mV | 分析 | ② §1 |

**充电、均衡与计量（详解 ③）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [CC-CV 充电](assets/cc-cv.svg) | 恒流→恒压→截止全过程 | 理解 | ③ |
| [被动均衡](assets/passive-balancing.svg) | 高水位电池开阀放热 | 理解 | ③ |
| [主动均衡](assets/active-balancing.svg) | 电感两拍搬运能量 | 评价 | ③ |
| [库仑计漂移](assets/coulomb-counting.svg) | 零漂累积与满充校准 | 分析 | ③ / 阶段 4 |

**算法（阶段 4）**

| 动画 | 演示 | 层级 | 出现位置 |
|---|---|---|---|
| [OCV-SOC 曲线](assets/ocv-soc-curve.svg) | NCM 斜率 vs LFP 平台区 30mV | 分析 | 阶段 4 |
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
| [主动放电](assets/active-discharge.svg) | 被动泄放很慢；确认断开后再用小电阻在数秒内拉低母线 | 理解 | 详解④ §1.3 |
| [绝缘检测电桥](assets/imd-bridge.svg) | 两次投切换来两个方程，解出 R_iso± | 分析 | 阶段 6 |
| [并簇环流](assets/parallel-cluster-circulating.svg) | 压差落在毫欧上 → 数百安对冲 | 分析 | 阶段 6 |
| [DTC 故障快照](assets/dtc-snapshot.svg) | 越线一瞬冻结 U/I/T/SOC/时间戳 | 应用 | 阶段 6 §6.2.2 |
| [被动均衡分时调度](assets/balance-scheduling.svg) | 入口条件门控 → 泄放/关断/复测轮询 → 压差收敛 | 应用 | 阶段 6 §6.3 |
| [HIL 测试台](assets/hil-testbench.svg) | 电芯模拟器 + 故障注入矩阵 + 上位机自动判定 | 评价 | 阶段 6 §6.5 |
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

## 实物图

成品保护板、电芯、万用表、NTC、检流电阻、平衡插头、直流电源、密封接触器、线绕电阻、笔记本气量计、保护 IC 特写、带 DW01A/8205A 的单节充电保护板，以及和主接触器同框的预充电阻，在 [assets/photos/](assets/photos/)，来源与授权写在 [PHOTOS.md](assets/photos/PHOTOS.md)。DW01 引脚位置和分压实测台仍有标明「示意图」的动画。还缺的实拍（同框实测台、BQ769 评估板、isoSPI 线束、主动放电电阻）记在 [共建任务板](../共建任务板.md) T11。

返回 [学习路线总纲](../bms-resources.md)
