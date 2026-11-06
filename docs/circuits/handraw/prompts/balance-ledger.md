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

被动均衡「把多的变成热」，到底要多久？——三笔账互相咬住：电流小、功率小，时间就必然很长。再加一笔热账：单路功率不大，16 路同开却足以把贴着的 NTC 自己加热。

# 事实表

出处：书稿 [第 9 章 §9.2](../../../../bms-book/book/09-均衡.md)「被动均衡：把多的变成热」。100 Ω 放电电阻、单体 4 V 的教学算例，与 §9.2 正文和练习 1 同一组数。

| 量 | 值 | 来源 |
|---|---|---|
| 放电电阻 | 100 Ω | §9.2 教学算例 |
| 单体电压 | 4 V | §9.2 教学算例 |
| 均衡电流 I | 40 mA | U/R = 4 V / 100 Ω |
| 单路功率 P | 0.16 W | U²/R = 4² / 100，全部变成热 |
| 补回 ΔQ = 1 Ah 的时间 t | 25 h | ΔQ/I = 1 Ah / 0.04 A |
| 单路持续热设计 | 0.08 W | 0.16 W 是额定脉冲能力，按 50% 占空比降额（教学合成值） |
| 16 路同开总热 | 2.56 W | 16 × 0.16 W（教学合成值） |

**降额口径**：0.08 W 是**单路** 0.16 W 按 50% 占空比降额后的持续值，不是 2.56 W 的降额结果（2.56 W 的一半是 1.28 W，图上与正文都不出现这个数）。两笔账的分母不同——降额按单路算，总热账按 16 路算。图 9-2 的图说与 `docs/circuits/README.md` 索引行都按这个顺序写：先单路降额，再 16 路合计。

2.56 W 足以让铜箔局部升温十几度，贴着电阻的 NTC 被「加热」，温度读数失真——这是本图最后一笔账要指出的后果，也是 §9.9「关断—采样时序」的前因。

# 帧大纲

1. 版式：最高那节挂一只 100 Ω 放电电阻，右边立三行空账（电流 / 功率 / 时间），先只画回路与两个标签。
2. 第一笔账——电流：`I ≈ U/R = 4 V / 100 Ω = 40 mA`，电流标在回路上。
3. 第二笔账——功率：`P ≈ U²/R = 0.16 W`，注明这部分全部变成热。
4. 第三笔账——时间：`t ≈ ΔQ/I = 1 Ah / 0.04 A = 25 h`。一句结论：25 小时才补回 1 Ah，被动均衡只能微调，不能修复。
5. 热账：左下标 16 路同开 2.56 W；右栏写明单路 0.16 W 按 50% 占空比降额到 0.08 W（分母不同，勿把降额套到 2.56 W 上），再写贴着的 NTC 被加热、温度读数失真。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. All linework and labels in Prussian blue C-03; vermilion C-15 stays unused in this figure, which carries no single alarming conclusion. Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

Five frames, one fixed layout: at the left a single cell drawn as a tall rectangle with a bleed resistor wired across it as a small rectangle, at the right a ledger of three stacked rows labelled current, power and time that fill in one per frame. The lower band is reserved for the thermal account. No people, no cartoon mascot, no brand logos, no photorealistic claim:

Frame 1 — the bare circuit and the empty three-row ledger, annotated that the highest cell carries a one hundred ohm bleed resistor.
Frame 2 — the current row fills in: four volts across one hundred ohms gives forty milliamps, with the current lettered onto the loop.
Frame 3 — the power row fills in: four volts squared over one hundred ohms gives zero point one six watts, annotated that all of it becomes heat.
Frame 4 — the time row fills in: one amp hour at forty milliamps takes twenty five hours, with a concluding line that passive balancing can only trim an imbalance, never repair one.
Frame 5 — the thermal account appears in the lower band: sixteen channels switched on together total two point five six watts at the left, while the right column states that a single channel derates from zero point one six watts to zero point zero eight watts at fifty percent duty, and that the thermistor taped beside the resistor is heated by it so the temperature reading is distorted.
