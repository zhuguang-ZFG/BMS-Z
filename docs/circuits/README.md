# 电路与芯片详解（含动画）

> 电路级、芯片级的深度解析，配 SMIL 动画（GitHub 网页端打开自动播放；本地请用浏览器打开 SVG）。
> 讲解统一使用水路比喻：电压=水压、电流=水流、MOS=闸门、二极管=单向阀。

## 三篇详解

| 篇目 | 内容 | 配套阶段 |
|---|---|---|
| [① 功率回路：MOS、保护与预充](01-功率回路-MOS保护与预充.md) | MOS 结构与背靠背、DW01 芯片级解析、预充回路计算 | 阶段 2 / 6 |
| [② 采样链与 AFE 芯片](02-采样链与AFE芯片.md) | 采样链误差预算、MUX 扫描、开线检测、BQ769x2 内部、isoSPI 菊花链 | 阶段 3 |
| [③ 充电、均衡与计量](03-充电均衡与计量.md) | CC-CV 物理、被动均衡三笔账、主动均衡拓扑、库仑计与校准 | 阶段 2 / 4 |

## 八个动画

| 动画 | 演示内容 | 所属篇目 |
|---|---|---|
| [背靠背 MOS](assets/mosfet-backtoback.svg) | 为什么一颗 MOS 关不断，两颗才行 | ① |
| [过充保护（DW01）](assets/overcharge-protection.svg) | 电压越线 → OC 拉低 → MOS 断开 → 恢复 | ① |
| [预充回路](assets/precharge.svg) | 上电时序：预充→爬压→合主闸 | ① |
| [MUX 扫描采样](assets/mux-scan.svg) | 一颗 ADC 巡逻测 16 串 | ② |
| [isoSPI 菊花链](assets/isospi-daisy.svg) | 数据接力穿隔离墙 | ② |
| [CC-CV 充电](assets/cc-cv.svg) | 恒流→恒压→截止全过程 | ③ |
| [被动均衡](assets/passive-balancing.svg) | 高水位电池开阀放热 | ③ |
| [库仑计漂移](assets/coulomb-counting.svg) | 零漂累积与满充校准 | ③ |

返回 [学习路线总纲](../bms-resources.md)
