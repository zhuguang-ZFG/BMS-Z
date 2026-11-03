---
search: false
---

# KP 缺口审计（W0 模板 + W1 草案）

> 合同：[SPEC v2.5 §9](教材彻底改造SPEC.md) · 建立：2026-11-03 · 真源：`curriculum/concepts.json`
>
> 本文件是 §9.7 的落盘：W0 冻结 13 骨干 KP、建表模板；W1 从阶段主线标题抽草案（`planned`）；W2 起逐条填 ladder 并对齐主线文。

## 1. 表模板字段（W0）

`kp_id | stage_no | title | 现正文锚点 | ladder缺级 | 缺媒体(动画/实物/代码/视频) | 优先级 | status | 备注`

## 2. 骨干 KP（13 条，id 冻结）

13 条 id 由 `tools/check_curriculum.py` 的 `BACKBONE_IDS` 守住：删除或改名会让 CI 的文档一致性门直接变红。

| kp_id | stage | 现场问题 | 主线锚点（先懂） | 书稿锚点 | ladder缺级 | 缺媒体 | 优先级 | status | 备注 |
|---|---:|---|---|---|---|---|---|---|---|
| `three-probes` | 0 | BMS 看不见电池内部，凭什么做判断？ | [`stage-0-主线-电池.md`](stages/stage-0-主线-电池.md#00-先立一个视角bms-先看三根探针-理解) | [01-电池里在发生什么.md](../bms-book/book/01-电池里在发生什么.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04） |
| `load-voltage-drop` | 0 | 满电一拧把掉两格，电量真的瞬间消失了吗？ | [`stage-0-主线-电池.md`](stages/stage-0-主线-电池.md#014-温度电池的脾气-理解) | [01-电池里在发生什么.md](../bms-book/book/01-电池里在发生什么.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04） |
| `overcharge-chain` | 0 | 过充为什么会从一个电压数字升级成热失控？ | [`stage-0-主线-电池.md`](stages/stage-0-主线-电池.md#012-过充一场逐级升级的事故-理解) | [03-电芯化学家族.md](../bms-book/book/03-电芯化学家族.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04） |
| `weakest-cell` | 1 | 为什么电池包不是看平均值，而是最弱单体说了算？ | [`stage-1-认识BMS.md`](stages/stage-1-认识BMS.md#12-木桶效应亲眼看看浪费有多大-理解) | [02-BMS的六件事.md](../bms-book/book/02-BMS的六件事.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04） |
| `protection-debounce` | 2 | 电压已经越限，保护为什么不在第一拍立即切断？ | [`stage-2-主线-单节保护板.md`](stages/stage-2-主线-单节保护板.md#22-dw01三类保护条件-理解) | [07-保护tick48.md](../bms-book/book/07-保护tick48.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04）；图 7-4 → L2.media（2026-11-04） |
| `measurement-budget` | 3 | ADC 位数很高，为什么测量仍可能不准？ | [`stage-3-主线-AFE与采样.md`](stages/stage-3-主线-AFE与采样.md#32-afe-精读以-bq769x0x2-为线-分析) | [05-测量链.md](../bms-book/book/05-测量链.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04） |
| `soc-drift` | 4 | 安时积分为什么越走越偏？ | [`stage-4-主线-SOC估算.md`](stages/stage-4-主线-SOC估算.md#41-soc-估计为什么会错-理解) | [12-SOC三条路.md](../bms-book/book/12-SOC三条路.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04） |
| `ocv-trust` | 4 | 电压什么时候能当 SOC 的尺子，什么时候会骗人？ | [`stage-4-主线-SOC估算.md`](stages/stage-4-主线-SOC估算.md#43-ocv-校正先判断电压能不能信-分析) | [10-模型OCV四项.md](../bms-book/book/10-模型OCV四项.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04） |
| `hppc-identification` | 4 | 一条脉冲怎样拆出 R0、R1 和 C1？ | [`stage-4-主线-模型与校正.md`](stages/stage-4-主线-模型与校正.md#44-等效电路从端电压中分离动态压降-分析) | [13-HPPC参数辨识.md](../bms-book/book/13-HPPC参数辨识.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04） |
| `sop-minimum` | 4 | SOP 为什么永远听最短的那块板？ | [`stage-4-主线-SOH与SOP.md`](stages/stage-4-主线-SOH与SOP.md#47-sop计算此刻允许的功率-分析) | [14-SOP与热.md](../bms-book/book/14-SOP与热.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04） |
| `protocol-resync` | 5 | 通信流里坏了一个字节，后面的好帧为什么还能救回来？ | [`stage-5-主线-串口与Modbus.md`](stages/stage-5-主线-串口与Modbus.md#52-uart帧结构与状态机-应用) | [18-通信帧状态机.md](../bms-book/book/18-通信帧状态机.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04） |
| `precharge-evidence` | 6 | 高压接触器为什么不能直接一把合上？ | [`stage-6-主线-高压与安全.md`](stages/stage-6-主线-高压与安全.md#612-预充回路合闸的艺术-应用) | [32-高压安全与绝缘检测.md](../bms-book/book/32-高压安全与绝缘检测.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04） |
| `ai-boundary` | 7 | AI 能帮 BMS 做什么，哪些决定绝不能交给它？ | [`stage-7-BMS与AI.md`](stages/stage-7-BMS与AI.md#72-三圈边界放手签字别碰) | [24-BMS与AI.md](../bms-book/book/24-BMS与AI.md) | 无（L1–L5 已入库） | 无（media[] 已回链现有资产） | P0 | active | v3 已补 ladder；L3 落主线页；W3 核对：L1–L2 动画覆盖无缺项（2026-11-04）；图 24-4 → L3/L4.media（2026-11-04） |

## 3. W1 草案（68 行，全部 `planned`）

从 18 篇阶段主线页的 H2/H3 标题抽取；已排除「本页目录 / 自测题 / 动手任务 / 验收清单 / 开场 / 口诀」等配套栏目。阶段 2、3 另按 §9.2「可含子 KP」补了 3 条子 KP（锚到父节，见备注）。`s{N}-{NN}` 是草案行号，**不是** `concepts.json` 的 KP id——id 在 W2 定名时按 kebab-case 分配。

| draft_id | 阶段 | 候选标题 | 现正文锚点 | status | 备注 |
|---|---:|---|---|---|---|
| `s0-01` | 0 | 0.1.5 必背参数表 [记忆] | [`stage-0-主线-充电与电量.md`](stages/stage-0-主线-充电与电量.md#015-必背参数表-记忆) | planned | 待 W2 定名并补 ladder |
| `s0-02` | 0 | 0.1.5b C 倍率：同一安培，容量不同就不是一回事 [理解] | [`stage-0-主线-充电与电量.md`](stages/stage-0-主线-充电与电量.md#015b-c-倍率同一安培容量不同就不是一回事-理解) | planned | 待 W2 定名并补 ladder |
| `s0-03` | 0 | 0.1.6 CC-CV：充电的两段论 [理解] | [`stage-0-主线-充电与电量.md`](stages/stage-0-主线-充电与电量.md#016-cc-cv充电的两段论-理解) | planned | 待 W2 定名并补 ladder |
| `s0-04` | 0 | 0.1.7 SOC 与 SOH：油表和油箱 [理解] | [`stage-0-主线-充电与电量.md`](stages/stage-0-主线-充电与电量.md#017-soc-与-soh油表和油箱-理解) | planned | 待 W2 定名并补 ladder |
| `s0-05` | 0 | 0.0 先立一个视角：BMS 先看三根探针 [理解] | [`stage-0-主线-电池.md`](stages/stage-0-主线-电池.md#00-先立一个视角bms-先看三根探针-理解) | planned | 待 W2 定名并补 ladder |
| `s0-06` | 0 | 0.1 锂电池化学基础 [理解] | [`stage-0-主线-电池.md`](stages/stage-0-主线-电池.md#01-锂电池化学基础-理解) | planned | 待 W2 定名并补 ladder |
| `s0-07` | 0 | 0.1.1 一块电池里在发生什么 [理解] | [`stage-0-主线-电池.md`](stages/stage-0-主线-电池.md#011-一块电池里在发生什么-理解) | planned | 待 W2 定名并补 ladder |
| `s0-08` | 0 | 0.1.2 过充：一场逐级升级的事故 [理解] | [`stage-0-主线-电池.md`](stages/stage-0-主线-电池.md#012-过充一场逐级升级的事故-理解) | planned | 待 W2 定名并补 ladder |
| `s0-09` | 0 | 0.1.3 过放：安静的杀手 [理解] | [`stage-0-主线-电池.md`](stages/stage-0-主线-电池.md#013-过放安静的杀手-理解) | planned | 待 W2 定名并补 ladder |
| `s0-10` | 0 | 0.1.4 温度：电池的脾气 [理解] | [`stage-0-主线-电池.md`](stages/stage-0-主线-电池.md#014-温度电池的脾气-理解) | planned | 待 W2 定名并补 ladder |
| `s1-01` | 1 | 1.1 从一节电池到一支"马拉松队伍" [理解] | [`stage-1-认识BMS.md`](stages/stage-1-认识BMS.md#11-从一节电池到一支马拉松队伍-理解) | planned | 待 W2 定名并补 ladder |
| `s1-02` | 1 | 1.2 木桶效应：亲眼看看浪费有多大 [理解] | [`stage-1-认识BMS.md`](stages/stage-1-认识BMS.md#12-木桶效应亲眼看看浪费有多大-理解) | planned | 待 W2 定名并补 ladder |
| `s1-03` | 1 | 1.3 BMS 的五大功能模块 [理解] | [`stage-1-认识BMS.md`](stages/stage-1-认识BMS.md#13-bms-的五大功能模块-理解) | planned | 待 W2 定名并补 ladder |
| `s1-04` | 1 | 1.4 五大保护：名词、断口与三要素 [记忆] | [`stage-1-认识BMS.md`](stages/stage-1-认识BMS.md#14-五大保护名词断口与三要素-记忆) | planned | 待 W2 定名并补 ladder |
| `s1-05` | 1 | 1.4b 五大保护：每一条背后都有一个事故 [理解] | [`stage-1-认识BMS.md`](stages/stage-1-认识BMS.md#14b-五大保护每一条背后都有一个事故-理解) | planned | 待 W2 定名并补 ladder |
| `s1-06` | 1 | 1.5 热失控链：为什么安全是最高优先级 [理解] | [`stage-1-认识BMS.md`](stages/stage-1-认识BMS.md#15-热失控链为什么安全是最高优先级-理解) | planned | 待 W2 定名并补 ladder |
| `s1-07` | 1 | 1.6 BMS 的三种形态 [理解] | [`stage-1-认识BMS.md`](stages/stage-1-认识BMS.md#16-bms-的三种形态-理解) | planned | 待 W2 定名并补 ladder |
| `s1-08` | 1 | 1.7 保护决策逻辑（状态机雏形） [理解] | [`stage-1-认识BMS.md`](stages/stage-1-认识BMS.md#17-保护决策逻辑状态机雏形-理解) | planned | 待 W2 定名并补 ladder |
| `s1-09` | 1 | 1.8 均衡初步 [理解] | [`stage-1-认识BMS.md`](stages/stage-1-认识BMS.md#18-均衡初步-理解) | planned | 待 W2 定名并补 ladder |
| `s2-01` | 2 | 2.1 识别保护板器件与端子 [应用] | [`stage-2-主线-单节保护板.md`](stages/stage-2-主线-单节保护板.md#21-识别保护板器件与端子-应用) | planned | 待 W2 定名并补 ladder |
| `s2-02` | 2 | 2.2 DW01：三类保护条件 [理解] | [`stage-2-主线-单节保护板.md`](stages/stage-2-主线-单节保护板.md#22-dw01三类保护条件-理解) | planned | 待 W2 定名并补 ladder |
| `s2-03` | 2 | 2.3 多节保护：S-8254A 与多通道芯片 [理解] | [`stage-2-主线-多节与接口.md`](stages/stage-2-主线-多节与接口.md#23-多节保护s-8254a-与多通道芯片-理解) | planned | 待 W2 定名并补 ladder |
| `s2-04` | 2 | 2.4 MOS 与驱动细节 [分析] | [`stage-2-主线-多节与接口.md`](stages/stage-2-主线-多节与接口.md#24-mos-与驱动细节-分析) | planned | 待 W2 定名并补 ladder |
| `s2-05` | 2 | 2.5 NTC 与 ID：温度和身份识别 [理解] | [`stage-2-主线-多节与接口.md`](stages/stage-2-主线-多节与接口.md#25-ntc-与-id温度和身份识别-理解) | planned | 待 W2 定名并补 ladder |
| `s2-06` | 2 | 2.6 保护板实测：条件、步骤与记录 [应用] | [`stage-2-主线-实测与验收.md`](stages/stage-2-主线-实测与验收.md#26-保护板实测条件步骤与记录-应用) | planned | 待 W2 定名并补 ladder |
| `s2-07` | 2 | 2.1b 端子、同口与分口 | [`stage-2-主线-单节保护板.md`](stages/stage-2-主线-单节保护板.md#21-识别保护板器件与端子-应用) | planned | 子 KP：锚到 2.1；B±/P±/C-/D- 与同口/分口是接线前必须分清的 |
| `s2-08` | 2 | 2.2b 三类条件与恢复 | [`stage-2-主线-单节保护板.md`](stages/stage-2-主线-单节保护板.md#22-dw01三类保护条件-理解) | planned | 子 KP：锚到 2.2；条件 → 断口 → 恢复 |
| `s3-01` | 3 | 3.1 从固定保护到 AFE + MCU [理解] | [`stage-3-主线-AFE与采样.md`](stages/stage-3-主线-AFE与采样.md#31-从固定保护到-afe--mcu-理解) | planned | 待 W2 定名并补 ladder |
| `s3-02` | 3 | 3.2 AFE 精读：以 BQ769x0/x2 为线 [分析] | [`stage-3-主线-AFE与采样.md`](stages/stage-3-主线-AFE与采样.md#32-afe-精读以-bq769x0x2-为线-分析) | planned | 待 W2 定名并补 ladder |
| `s3-03` | 3 | 3.3 高压采样与隔离菊花链 [分析] | [`stage-3-主线-AFE与采样.md`](stages/stage-3-主线-AFE与采样.md#33-高压采样与隔离菊花链-分析) | planned | 待 W2 定名并补 ladder |
| `s3-04` | 3 | 3.6 原理图与 PCB：五条纪律 [应用] | [`stage-3-主线-PCB调试与验收.md`](stages/stage-3-主线-PCB调试与验收.md#36-原理图与-pcb五条纪律-应用) | planned | 待 W2 定名并补 ladder |
| `s3-05` | 3 | 3.7 调试：先模拟，后接电池 [应用] | [`stage-3-主线-PCB调试与验收.md`](stages/stage-3-主线-PCB调试与验收.md#37-调试先模拟后接电池-应用) | planned | 待 W2 定名并补 ladder |
| `s3-06` | 3 | 3.4 固件分层与状态机 [应用] | [`stage-3-主线-固件与功率开关.md`](stages/stage-3-主线-固件与功率开关.md#34-固件分层与状态机-应用) | planned | 待 W2 定名并补 ladder |
| `s3-07` | 3 | 3.5 高边与低边功率开关 [评价] | [`stage-3-主线-固件与功率开关.md`](stages/stage-3-主线-固件与功率开关.md#35-高边与低边功率开关-评价) | planned | 待 W2 定名并补 ladder |
| `s3-08` | 3 | 3.2b 测量子系统：MUX 扫描与时间账 | [`stage-3-主线-AFE与采样.md`](stages/stage-3-主线-AFE与采样.md#32-afe-精读以-bq769x0x2-为线-分析) | planned | 子 KP：锚到 3.2；扫描时间预算与首尾串差 |
| `s4-01` | 4 | 4.1 SOC 估计为什么会错 [理解] | [`stage-4-主线-SOC估算.md`](stages/stage-4-主线-SOC估算.md#41-soc-估计为什么会错-理解) | planned | 待 W2 定名并补 ladder |
| `s4-02` | 4 | 4.2 安时积分：电流误差也会被累计 [分析] | [`stage-4-主线-SOC估算.md`](stages/stage-4-主线-SOC估算.md#42-安时积分电流误差也会被累计-分析) | planned | 待 W2 定名并补 ladder |
| `s4-03` | 4 | 4.3 OCV 校正：先判断电压能不能信 [分析] | [`stage-4-主线-SOC估算.md`](stages/stage-4-主线-SOC估算.md#43-ocv-校正先判断电压能不能信-分析) | planned | 待 W2 定名并补 ladder |
| `s4-04` | 4 | 4.6 SOH 与联合估计：同时跟踪容量和内阻 [分析] | [`stage-4-主线-SOH与SOP.md`](stages/stage-4-主线-SOH与SOP.md#46-soh-与联合估计同时跟踪容量和内阻-分析) | planned | 待 W2 定名并补 ladder |
| `s4-05` | 4 | 4.7 SOP：计算此刻允许的功率 [分析] | [`stage-4-主线-SOH与SOP.md`](stages/stage-4-主线-SOH与SOP.md#47-sop计算此刻允许的功率-分析) | planned | 待 W2 定名并补 ladder |
| `s4-06` | 4 | 4.8 工程落地要点 [评价] | [`stage-4-主线-SOH与SOP.md`](stages/stage-4-主线-SOH与SOP.md#48-工程落地要点-评价) | planned | 待 W2 定名并补 ladder |
| `s4-07` | 4 | 4.4 等效电路：从端电压中分离动态压降 [分析] | [`stage-4-主线-模型与校正.md`](stages/stage-4-主线-模型与校正.md#44-等效电路从端电压中分离动态压降-分析) | planned | 待 W2 定名并补 ladder |
| `s4-08` | 4 | 4.5 卡尔曼滤波：用电压校正积分 [分析] | [`stage-4-主线-模型与校正.md`](stages/stage-4-主线-模型与校正.md#45-卡尔曼滤波用电压校正积分-分析) | planned | 待 W2 定名并补 ladder |
| `s5-01` | 5 | 5.4 CAN：仲裁、信号与 DBC [理解] | [`stage-5-主线-CAN与外部接口.md`](stages/stage-5-主线-CAN与外部接口.md#54-can仲裁信号与-dbc-理解) | planned | 待 W2 定名并补 ladder |
| `s5-02` | 5 | 5.4.1 GB/T 27930：充电机与 BMS 怎么握手 [分析] | [`stage-5-主线-CAN与外部接口.md`](stages/stage-5-主线-CAN与外部接口.md#541-gbt-27930充电机与-bms-怎么握手-分析) | planned | 待 W2 定名并补 ladder |
| `s5-03` | 5 | 5.5 SMBus 与 BLE：笔记本和移动端接口 [理解] | [`stage-5-主线-CAN与外部接口.md`](stages/stage-5-主线-CAN与外部接口.md#55-smbus-与-ble笔记本和移动端接口-理解) | planned | 待 W2 定名并补 ladder |
| `s5-04` | 5 | 5.1 通信在 BMS 里的三个层级 [理解] | [`stage-5-主线-串口与Modbus.md`](stages/stage-5-主线-串口与Modbus.md#51-通信在-bms-里的三个层级-理解) | planned | 待 W2 定名并补 ladder |
| `s5-05` | 5 | 5.2 UART：帧结构与状态机 [应用] | [`stage-5-主线-串口与Modbus.md`](stages/stage-5-主线-串口与Modbus.md#52-uart帧结构与状态机-应用) | planned | 待 W2 定名并补 ladder |
| `s5-06` | 5 | 5.3 RS485 与 Modbus：物理层和寄存器 [理解] | [`stage-5-主线-串口与Modbus.md`](stages/stage-5-主线-串口与Modbus.md#53-rs485-与-modbus物理层和寄存器-理解) | planned | 待 W2 定名并补 ladder |
| `s5-07` | 5 | 5.6 协议逆向：从抓帧到字段验证 [分析] | [`stage-5-主线-协议逆向与安全.md`](stages/stage-5-主线-协议逆向与安全.md#56-协议逆向从抓帧到字段验证-分析) | planned | 待 W2 定名并补 ladder |
| `s5-08` | 5 | 5.6b 通信安全：把能写的口都上锁 [分析] | [`stage-5-主线-协议逆向与安全.md`](stages/stage-5-主线-协议逆向与安全.md#56b-通信安全把能写的口都上锁-分析) | planned | 待 W2 定名并补 ladder |
| `s6-01` | 6 | 6.2.1 量产状态机 [应用] | [`stage-6-主线-量产与毕业.md`](stages/stage-6-主线-量产与毕业.md#621-量产状态机-应用) | planned | 待 W2 定名并补 ladder |
| `s6-02` | 6 | 6.2.2 故障管理（DTC 体系） [应用] | [`stage-6-主线-量产与毕业.md`](stages/stage-6-主线-量产与毕业.md#622-故障管理dtc-体系-应用) | planned | 待 W2 定名并补 ladder |
| `s6-03` | 6 | 6.2.3 参数与标定系统 [应用] | [`stage-6-主线-量产与毕业.md`](stages/stage-6-主线-量产与毕业.md#623-参数与标定系统-应用) | planned | 待 W2 定名并补 ladder |
| `s6-04` | 6 | 6.2.4 Bootloader 与 OTA [应用] | [`stage-6-主线-量产与毕业.md`](stages/stage-6-主线-量产与毕业.md#624-bootloader-与-ota-应用) | planned | 待 W2 定名并补 ladder |
| `s6-05` | 6 | 6.5 量产与测试 [评价] | [`stage-6-主线-量产与毕业.md`](stages/stage-6-主线-量产与毕业.md#65-量产与测试-评价) | planned | 待 W2 定名并补 ladder |
| `s6-06` | 6 | 6.5.1 产线追溯：错芯和贴错标 [评价] | [`stage-6-主线-量产与毕业.md`](stages/stage-6-主线-量产与毕业.md#651-产线追溯错芯和贴错标-评价) | planned | 待 W2 定名并补 ladder |
| `s6-07` | 6 | 6.6 毕业项目指南 [创造] | [`stage-6-主线-量产与毕业.md`](stages/stage-6-主线-量产与毕业.md#66-毕业项目指南-创造) | planned | 待 W2 定名并补 ladder |
| `s6-08` | 6 | 6.6b 毕业项目评审量规 [评价] | [`stage-6-主线-量产与毕业.md`](stages/stage-6-主线-量产与毕业.md#66b-毕业项目评审量规-评价) | planned | 待 W2 定名并补 ladder |
| `s6-09` | 6 | 6.1.1 高压电池系统架构 [分析] | [`stage-6-主线-高压与安全.md`](stages/stage-6-主线-高压与安全.md#611-高压电池系统架构-分析) | planned | 待 W2 定名并补 ladder |
| `s6-10` | 6 | 6.1.2 预充回路：合闸的艺术 [应用] | [`stage-6-主线-高压与安全.md`](stages/stage-6-主线-高压与安全.md#612-预充回路合闸的艺术-应用) | planned | 待 W2 定名并补 ladder |
| `s6-11` | 6 | 6.1.3 绝缘检测（IMD） [分析] | [`stage-6-主线-高压与安全.md`](stages/stage-6-主线-高压与安全.md#613-绝缘检测imd-分析) | planned | 待 W2 定名并补 ladder |
| `s6-12` | 6 | 6.4 功能安全落地：以过充为例走一遍 [评价] | [`stage-6-主线-高压与安全.md`](stages/stage-6-主线-高压与安全.md#64-功能安全落地以过充为例走一遍-评价) | planned | 待 W2 定名并补 ladder |
| `s6-13` | 6 | 6.4.1 过充案例：开线被当成过充 [评价] | [`stage-6-主线-高压与安全.md`](stages/stage-6-主线-高压与安全.md#641-过充案例开线被当成过充-评价) | planned | 待 W2 定名并补 ladder |
| `s7-01` | 7 | 7.2 三圈边界：放手、签字、别碰 | [`stage-7-BMS与AI.md`](stages/stage-7-BMS与AI.md#72-三圈边界放手签字别碰) | planned | 待 W2 定名并补 ladder |
| `s7-02` | 7 | 7.3 证据与印象：它没读过你的 datasheet | [`stage-7-BMS与AI.md`](stages/stage-7-BMS与AI.md#73-证据与印象它没读过你的-datasheet) | planned | 待 W2 定名并补 ladder |
| `s7-03` | 7 | 7.4 谁签字：解释归模型，判定归程序 | [`stage-7-BMS与AI.md`](stages/stage-7-BMS与AI.md#74-谁签字解释归模型判定归程序) | planned | 待 W2 定名并补 ladder |
| `s7-04` | 7 | 7.5 五种失败模式与五个探针 | [`stage-7-BMS与AI.md`](stages/stage-7-BMS与AI.md#75-五种失败模式与五个探针) | planned | 待 W2 定名并补 ladder |

## 4. 配额对照（§9.2）

| 阶段 | 草案行数 | 下限 | 差 | 处置 |
|---|---:|---:|---:|---|
| 0 | 10 | 8 | +2 | — |
| 1 | 9 | 8 | +1 | — |
| 2 | 8 | 8 | 0 | 含 2 条子 KP（2.1b 端子/同口分口、2.2b 条件与恢复） |
| 3 | 8 | 8 | 0 | 含 1 条子 KP（3.2b MUX 扫描与时间账） |
| 4 | 8 | 8 | 0 | — |
| 5 | 8 | 8 | 0 | — |
| 6 | 13 | 8 | +5 | — |
| 7 | 4 | 4 | 0 | — |
| 合计 | 68 | ≥60 | +8 | 达标 |

## 5. 骨干映射候选（W2 复核）

只列语义直接对上的；其余 6 条（`load-voltage-drop`、`protection-debounce`、`measurement-budget`、`soc-drift`、`hppc-identification`、`protocol-resync`）留到 W2 按主线小节逐条核对，不在本表预先认领。

| 骨干 KP | 草案行 | 依据 |
|---|---|---|
| `three-probes` | s0-05 | 「BMS 先看三根探针」就是三读数证据链 |
| `overcharge-chain` | s0-08 | 0.1.2 过充逐级升级 |
| `weakest-cell` | s1-02 | 1.2 木桶效应 |
| `ocv-trust` | s4-03 | 4.3 OCV 校正先判断电压能不能信 |
| `sop-minimum` | s4-05 | 4.7 SOP 取最短板 |
| `precharge-evidence` | s6-10 | 6.1.2 预充回路 |
| `ai-boundary` | s7-01–s7-04 | 阶段 7 全篇即该 KP 的展开 |

## 6. 校验计划（W1 列入，W2 已落地）

- 现有 `tools/check_curriculum.py` 已校验必填字段、死链、先修无环，并新增 **13 骨干 id 冻结门**（删除/改名即 FAIL）。
- `status` 取值已与 §9.2 对齐（`planned` / `active` / `gap`）：`check_curriculum.py` 的 `STATUSES` 与 `gen_curriculum_pages.py` 的 `STATUS_LABELS` 同步更新，W2 把草案行写进 `concepts.json` 不再被误判。
- **L1–L5 梯子硬门（W2 已落地）**：骨干 KP 必须带 `ladder`（恰好 L1–L5）、`title`（≤20 字）、`bloom_ceiling ≥ L3`、`mastery_evidence`、`next[]`；每级 `goal / entry_path / retrieve_task / pass_check / media[]` 齐全，`entry_path` 的文件与锚点都必须真实存在，`media[]` 必须是仓库内已有文件。
- **主线入口硬门（W2 已落地）**：骨干 KP 的 `stage.path` 与 L3 `entry_path` 都必须落在 18 篇主线页（`MAINLINE_PAGES`），完整讲义只作查阅，防回漂。
- 负向实测：删一级 → `ladder 必须恰好含 L1–L5`；改错锚点 → `入口锚点不存在`；`bloom_ceiling` 降 L2 → `必须 ≥ L3`；`stage.path` 回完整页 → `必须是主线页`；`media[]` 指向不存在文件 → `媒介 不存在`。
- 草案行进入 `concepts.json` 时同步过闸；`planned` 行不设 ladder 可暂缓，但必须在 W2 收口（本轮 13 骨干已全部收口）。
