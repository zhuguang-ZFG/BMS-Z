---
search: false
slug: error-budget-waterfall
style: FA-029
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: measurement-budget
source_svg: docs/circuits/handraw/exports/error-budget-waterfall.webp
---

# 观察题

五截误差一截一截垒上去，为什么还没标定，整个 ±5 mV 预算就先被吃穿了？

# 帧大纲

1. 空坐标系：零基线与一对 ±5 mV 预算线先立住，柱子一根都还没有（示意账）。
2. 第一截落柱：基准温漂 +2.0 mV 从零基线垒起，增量只手写在柱顶，柱内不放字。
3. 第二截接力：ADC 失调 +1.5 mV 从前一柱的终点接着往上垒，阶梯累计到 3.5 mV。
4. 后三截补齐：RC 漏电 +0.8、电荷注入 +0.3、布局拾取 +0.9 依次衔接，阶梯走到 5.5 mV。
5. 越界：累计段顶破上预算线，探出 0.5 mV —— 越界那一小截是全图唯一的 C-15。
6. 结论卡收束：未标定累加 5.5 mV、预算 ±5 mV、探出 0.5 mV；「标定之后」把系统性那几项按系数修掉，只余约 1.8 mV，重新落回预算内（回到 C-03）。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat ruled panels, an exact little grid, hand-lettered small-caps labels, deadpan textbook tone, paper grain. All structural linework, grid, bars and labels in Prussian blue C-03 only.

Vermilion C-15 is used exactly once: the short segment where the cumulative staircase pokes above the upper budget line. It is a small hazard tick, never a filled area, never a second series colour.

Six frames of the same chart, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic or oscilloscope-screenshot claim, schematic only:

Frame 1 — empty axes; the zero baseline and a pair of ±5 mV budget rules stand alone.
Frame 2 — first bar: baseline temperature drift +2.0 mV, rising from the zero baseline; the increment sits on the bar top, no text inside the bar.
Frame 3 — second bar: ADC offset +1.5 mV continues from the first bar's top; staircase now at 3.5 mV.
Frame 4 — three more bars: RC leakage +0.8, charge injection +0.3, layout pickup +0.9; the staircase lands on 5.5 mV.
Frame 5 — breach: the cumulative step crosses the upper budget rule and overshoots by 0.5 mV; that overshoot segment is the single C-15 mark.
Frame 6 — conclusion card: uncalibrated total 5.5 mV, budget ±5 mV, overshoot 0.5 mV; then "after calibration" removes the systematic items by coefficient and leaves about 1.8 mV, back inside the budget in C-03.

Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative accumulation, not a calibration record of any real board. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学信息图，FA-029 Chris Ware 几何叙事风格：平直的横格分栏、精确的小网格、手写小字标注、冷面教科书语气、纸纹质感。结构线、网格、柱与标注只用 C-03 普鲁士蓝。

C-15 朱砂红全图只出现一次：累计阶梯顶破上预算线的那一小截。它是危险刻度，不铺面、不当第二组曲线的颜色。

同一张图六个帧、同一视角，无人、无卡通吉祥物、无品牌 Logo、不写实拍、不模仿示波器截图，纯示意：

1. 空坐标系：零基线与一对 ±5 mV 预算线先立住，还没有柱子。
2. 第一截：基准温漂 +2.0 mV 从零基线垒起，增量写在柱顶，柱内不放白字。
3. 第二截：ADC 失调 +1.5 mV 从前一柱终点接上去，阶梯累计 3.5 mV。
4. 后三截：RC 漏电 +0.8、电荷注入 +0.3、布局拾取 +0.9 依次衔接，阶梯走到 5.5 mV。
5. 越界：累计阶梯顶破上预算线，探出 0.5 mV，这一小截是唯一 C-15。
6. 收束：结论卡写「未标定累加 5.5 mV / 预算 ±5 mV / 探出 0.5 mV」；标定把系统性几项按系数修掉，只余约 1.8 mV，落回预算内（回到 C-03）。

数字只作小手写标注，全部标「示意累加」，不是某块真实采样板的校准记录。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 危险仅 C-15，且只有越界那一处
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一视角，柱内无白字，增量只在柱顶
- [ ] 首末帧单独成图仍可读（预算线 + 5.5 mV 与 1.8 mV 两组结论）
