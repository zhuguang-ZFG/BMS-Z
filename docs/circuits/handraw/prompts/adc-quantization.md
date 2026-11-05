---
search: false
slug: adc-quantization
style: FA-029
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: measurement-budget
source_svg: docs/circuits/assets/archive/adc-quantization.svg
---

# 观察题

台阶越细，读数就越准吗？盯住整把尺子的零点——它一偏，是只有一格偏，还是每一格都在同一方向偏。

# 帧大纲

1. 版式立起：左边一块坐标板，纵轴四道刻度 3.48 / 3.60 / 3.72 / 3.84 V，横轴是时间；右边自上而下留四格空清单，两栏用细直线划开。
2. 真实电压：一条连续细线从左下向右上爬，一路穿过四道刻度，线旁标「真实电压（连续）」。
3. 量化：同一条上升被压成台阶——读数只能落在格上（台阶已放大示意，实际 1 LSB ≈ 1.2 mV），一个点沿台阶逐级跳，每一级的高度标 1 LSB。
4. 整尺上移：整套台阶整体上移（示意 +24 mV），连续线与台阶之间的缝被拉开——参考源一偏，所有读数同方向偏；全图唯一 C-15 就落在这道上移的刻度上。
5. 四格清单逐格点亮，每格牵一根短线到台阶上的对应特征：分辨率 = 刻度多细（12 bit → 4096 格，示例）；偏移误差 = 整体平移（零点不准，处处同偏）；增益误差 = 比例不对（读数随幅度按比例偏）；温漂 = 随温度变（参考源自己也随温度晃）。
6. 收束：底部一行小字 12 bit、5 V 参考，1 LSB = 5/4096 ≈ 1.22 mV；整尺上移 24 mV 是基准偏移，平均消不掉——所以「刻度细 ≠ 尺子准」。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 appears exactly once, as a single short tick on the +24 mV shift of the whole ruler — the one error that averaging cannot remove — never as a fill, never as a second series colour. The source drew the shifted staircase in red only to separate it from the original; here it becomes a C-03 dashed offset, and the text says so.

Six frames of one two-column layout, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic or oscilloscope-screenshot claim, schematic only:

Frame 1 — the layout is ruled: a left coordinate panel with four horizontal tick levels 3.48, 3.60, 3.72 and 3.84 V and time along the bottom, and a right column holding four empty index cards, the two columns divided by a thin straight line.
Frame 2 — the true voltage enters as one thin continuous curve climbing from lower left to upper right and crossing all four levels; the label reads true voltage, continuous.
Frame 3 — the same rise is forced onto a staircase: a reading may only land on a step, so the curve is replaced by flat treads and risers (steps deliberately exaggerated, real 1 LSB is about 1.2 mV), one dot hops tread by tread, and each riser is marked 1 LSB.
Frame 4 — the whole staircase shifts upward as one piece (illustrative +24 mV): every tread moves the same way and the gap between the continuous curve and the stair opens up; the label reads that a shifted reference pushes every reading the same direction. The single C-15 tick sits on this shift.
Frame 5 — the four index cards light up in order, each tied by one short ruled line to the matching feature on the staircase: resolution is how fine the graduations are (12 bit gives 4096 steps, example); offset error is a whole-ruler translation (a wrong zero offsets everything); gain error is a wrong proportion (the reading deviates with amplitude); drift follows temperature (the reference itself wanders).
Frame 6 — the closing strip: 12 bit, 5 V reference, 1 LSB = 5/4096 ≈ 1.22 mV; the whole ruler moving up 24 mV is a reference offset, and averaging cannot cancel it — which is why fine graduations still do not make a ruler accurate.

Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学信息结构图，FA-029 Chris Ware 几何叙事风格：平直的几何分栏、精确的直线框架、克制的冷面构图、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红全图只出现一次，是一段短刻度，标在整把尺子上移 +24 mV 的那一处——平均消不掉的那一种误差；不铺面、不当第二组曲线的颜色。源图把上移后的台阶画成红色只为与原始台阶区分，这里改成 C-03 虚线上移，并在文字里注明。

同一套两栏版式的六个帧、同一视角，无人、无卡通吉祥物、无品牌 Logo、不写实拍也不写示波器截图，纯示意：

1. 版式划好：左边一块坐标板，四道水平刻度 3.48 / 3.60 / 3.72 / 3.84 V，底部横轴是时间；右边一列四张空索引卡，两栏之间一道细直线分开。
2. 真实电压进场：一条细的连续曲线从左下爬到右上，穿过四道刻度，标「真实电压（连续）」。
3. 同一条上升被压成台阶：读数只能落在台阶上，曲线换成一段段踏面与踢面（台阶刻意放大，实际 1 LSB 约 1.2 mV），一个点逐级跳，每一级竖踢面标 1 LSB。
4. 整套台阶整体上移（示意 +24 mV）：每一级都朝同一方向挪，连续线与台阶之间的缝被拉开；标注「参考源一偏，所有读数同方向偏」。唯一 C-15 就标在这次上移上。
5. 四张索引卡按序点亮，每张一根短线牵到台阶上对应的特征：分辨率 = 刻度多细（12 bit → 4096 格，示例）；偏移误差 = 整体平移（零点不准，处处同偏）；增益误差 = 比例不对（读数随幅度按比例偏）；温漂 = 随温度变（参考源自己也随温度晃）。
6. 底部收束条：12 bit、5 V 参考，1 LSB = 5/4096 ≈ 1.22 mV；整尺上移 24 mV 是基准偏移，平均消不掉——所以「刻度细 ≠ 尺子准」。

数字只用小手写标注，全部标「示意」。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通、无示波器实拍口吻
- [ ] 危险仅 C-15，且只有一处（整尺上移 +24 mV 的那段短刻度）
- [ ] 上移后的台阶是 C-03 虚线，不是红色，且文字已说明这处改色
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 左证右释的两栏层级稳定，四张卡与台阶的连线一一对应，可暂停阅读
- [ ] 数字只用源图的 3.48 / 3.60 / 3.72 / 3.84 V、12 bit / 4096 格、5 V、1 LSB ≈ 1.22 mV、+24 mV，且全部标示意
- [ ] 首末帧单独成图仍可读
