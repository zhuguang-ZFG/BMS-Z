---
search: false
slug: balance-ledger
style: FA-029
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: balancing
source_svg: null
---

# 观察题

被动均衡「把多的变成热」，到底要多久？——三笔账互相咬住：电流小、功率小，时间就必然很长。再加一笔热账：单路功率不大，16 路全部导通的热量要一起算，NTC 可能受到局部加热。

# 事实表

出处：书稿 [第 9 章 §9.2](../../../../bms-book/book/09-均衡.md)「被动均衡：把多的变成热」。100 Ω 放电电阻、单体 4 V 的教学算例，与 §9.2 正文和练习 1 同一组数。

| 量 | 值 | 来源 |
|---|---|---|
| 放电电阻 | 100 Ω | §9.2 教学算例 |
| 单体电压 | 4 V | §9.2 教学算例 |
| 均衡电流 I | 40 mA | U/R = 4 V / 100 Ω |
| 单路功率 P | 0.16 W | U²/R = 4² / 100，全部变成热 |
| 补回 ΔQ = 1 Ah 的时间 t | 25 h | ΔQ/I = 1 Ah / 0.04 A |
| 单路平均耗散 | 0.08 W | 导通耗散 0.16 W × 50% 占空比；不是器件额定能力 |
| 16 路同开总热 | 2.56 W | 16 × 0.16 W（教学合成值） |

**功率口径**：0.16 W 是导通时的耗散功率；0.08 W 是单路在 50% 占空比下的平均耗散，不是器件额定功率或允许脉冲能力。相同条件下平均电流为 20 mA，泄放 1 Ah 约需 50 h；25 h 是连续导通算例。16 路全部导通的 2.56 W 属于另一假设工况，实际并发通道数须查策略与硬件。

局部温升取决于安装与散热条件，不能从瓦数直接断言升温十几度。贴近电阻的 NTC 可能被局部加热，须核查它测到的是哪个位置。

# 帧大纲

1. 版式：最高那节挂一只 100 Ω 放电电阻，右边立三行空账（电流 / 功率 / 时间），先只画回路与两个标签。
2. 第一笔账——电流：`I ≈ U/R = 4 V / 100 Ω = 40 mA`，电流标在回路上。
3. 第二笔账——功率：`P ≈ U²/R = 0.16 W`，注明这部分全部变成热。
4. 第三笔账——时间：`t ≈ ΔQ/I = 1 Ah / 0.04 A = 25 h`。一句结论：25 小时才补回 1 Ah，被动均衡只能微调，不能修复。
5. 热账：左下标 16 路同开 2.56 W；右栏写明导通 0.16 W 在 50% 占空比下平均耗散 0.08 W、约需 50 h，再写 NTC 可能被局部加热、温升须核查散热条件。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. All linework and labels in Prussian blue C-03; vermilion C-15 stays unused in this figure, which carries no single alarming conclusion. Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

Five frames, one fixed layout: at the left a single cell drawn as a tall rectangle with a bleed resistor wired across it as a small rectangle, at the right a ledger of three stacked rows labelled current, power and time that fill in one per frame. The lower band is reserved for the thermal account. No people, no cartoon mascot, no brand logos, no photorealistic claim:

Frame 1 — the bare circuit and the empty three-row ledger, annotated that the highest cell carries a one hundred ohm bleed resistor.
Frame 2 — the current row fills in: four volts across one hundred ohms gives forty milliamps, with the current lettered onto the loop.
Frame 3 — the power row fills in: four volts squared over one hundred ohms gives zero point one six watts, annotated that all of it becomes heat.
Frame 4 — the time row fills in: one amp hour at forty milliamps takes twenty five hours, with a concluding line that passive balancing can only trim an imbalance, never repair one.
Frame 5 — the thermal account appears in the lower band: sixteen channels switched on together total two point five six watts at the left, while the right column states that a single channel dissipates zero point one six watts while on and averages zero point zero eight watts at fifty percent duty, taking about fifty hours to bleed one amp hour; local thermistor heating and temperature rise depend on mounting and cooling.
