---
slug: sop-derating
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: sop-minimum
source_svg: docs/circuits/assets/sop-derating.svg
---

# 观察题

四块板各说各的上限，为什么最后能出多大力，只由最矮的那一块说了算？

# 帧大纲

1. ① 温度板：k_T 在 −20 °C 到 60 °C 之间分段线性，温度游标滑到 −10 °C，板高落到 0.33——温度成了最短板。
2. ② 另外三块板并排立起：荷电 1.00、电压墙 0.49（平台 OCV 换算）、熔断 1.00。
3. ③ 取最小：四块板的顶边对齐到一条地板线，最矮那块 0.33 拍板，其余三块的高处留白。
4. ④ 脉冲时长：k·min(2, √(30/t)) 把 0.33 抬成 30 s → 0.333、10 s → 0.577、2 s → 0.667，柱高随申请时长增长。
5. ⑤ 阶跃：温度 25 °C 一步掉到 −10 °C，直接取最小那条线竖直坠下去（源图红线的第二组曲线，改画为 C-03 虚线）。
6. ⑥ 再限斜率：每步 0.012 的回退限制，功率线只能斜着爬下去，追不上那条竖直跳变——限斜率之后的实线才是许用的 SOP。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only.

C-15 is used zero times in this figure: the source draws no forbidden zone or limit breach, so its red "take the minimum" curve becomes a C-03 dotted line and its gold slope-limited curve becomes a heavier C-03 stroke. Vermilion does not serve as a series colour.

Six frames of the same derating chart, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic or oscilloscope-screenshot claim, schematic only:

Frame 1 — ① temperature coefficient: a piecewise-linear k_T across −20 °C to 60 °C; the temperature cursor slides to −10 °C and the plate drops to 0.33, the shortest board.
Frame 2 — ② the other three plates stand up side by side: state of charge 1.00, voltage wall 0.49 (platform OCV), fuse 1.00.
Frame 3 — ③ take the minimum: the four plate tops align to one floor line, the shortest 0.33 decides; the taller three keep empty headroom.
Frame 4 — ④ pulse duration: k·min(2, √(30/t)) lifts 0.33 to 0.333 at 30 s, 0.577 at 10 s, 0.667 at 2 s; bar height grows with the shorter request.
Frame 5 — ⑤ step: temperature falls from 25 °C to −10 °C in one move and the direct-minimum line plunges vertically (drawn as a C-03 dotted second curve, not red).
Frame 6 — ⑥ slew limit: the 0.012-per-step retreat lets the power line only creep down at an angle, trailing the vertical drop; the resulting solid line is the permitted SOP.

Numbers stay as small hand-lettered annotations, all marked 示意; product thresholds come from datasheets and measurements. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。

本图 C-15 零次：源图没有禁区，也没有画出越限，红色那条「直接取最小」曲线只是第二组曲线，改画为 C-03 虚线；金色「限斜率之后」改成 C-03 加粗实线。朱砂红不当系列颜色。

同一张降额图六个帧、同一视角，无人、无卡通吉祥物、无品牌 Logo、不写实拍、不模仿示波器截图，纯示意：

1. ① 温度系数：k_T 在 −20 °C 到 60 °C 分段线性；温度游标滑到 −10 °C，板高落到 0.33，成为最短板。
2. ② 另外三块：荷电 1.00、电压墙 0.49（平台 OCV 换算）、熔断 1.00 并排立起。
3. ③ 取最小：四块板顶边对齐到一条地板线，最矮的 0.33 拍板，高出的三块留白。
4. ④ 脉冲时长：k·min(2, √(30/t))，30 s → 0.333、10 s → 0.577、2 s → 0.667，柱高随申请时长变。
5. ⑤ 阶跃：温度 25 °C 一步掉到 −10 °C，直接取最小那条线竖直坠落（画成 C-03 虚线）。
6. ⑥ 再限斜率：每步 0.012 的回退限制让功率线只能斜着往下爬，追不上竖直跳变；限斜率后的实线才是许用 SOP。

数字只用小手写标注，全部标「示意」（3.00 V、15 mΩ、40 A 与温度拐点均为教学数），产品阈值以规格书和实测为准。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] C-15 零次，红线与金线均已改画为 C-03（虚线 / 加粗）
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一视角，①–④ 与源图编号一致
- [ ] 0.33 / 1.00 / 0.49 / 1.00 与 0.333 / 0.577 / 0.667 全部来自源图，未新增数字
