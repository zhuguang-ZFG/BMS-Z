---
search: false
slug: weakest-cell-ah
style: FA-002
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: weakest-cell
source_svg: docs/circuits/assets/archive/weakest-cell-ah.svg
---

# 观察题

平均值一直写着 2.00 Ah，可用值却一路往下走——多报出来的那一截，究竟是从哪一节身上扣走的？

# 帧大纲

1. 极差是 0：四节等高，最弱的也是 2.00 Ah；「平均值」与「串联可用」两条线此刻完全重合，平均没有撒谎。
2. 极差 0.20 Ah：最弱掉到 1.90 Ah，平均值仍写 2.00——报 2.00 就多报了 0.10；两条线第一次裂开一道口子。
3. 斜率成形：极差每大 0.10 Ah，可用就少 0.05 Ah；可用线是一条斜率 −1/2 的直线，不弯。
4. 极差 0.40 Ah：点走到线末，可用 1.80 Ah；平均值那条平线始终停在 2.00，缺口张到最宽——全图唯一 C-15 的短刻度就落在这道缺口上。
5. 收束加脚注：串联只认最小值，不认平均；2.00 Ah 与「左右对称的极差」是教学假设，真实电池不对称时仍然只用最小值，不用这个 1/2。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 appears exactly once, as a short tick measuring the widest gap between the average value and the usable value — never as a fill, never as a second series colour. The source drew the usable curve in red merely to separate it from the average curve; here that second curve is a C-03 dashed line instead, and the text says so.

Five frames, same chart, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim, schematic only:

Frame 1 — spread is zero: four cells stand at equal height, the weakest is also 2.00 Ah; the average line and the usable line coincide exactly, so quoting the average lies about nothing.
Frame 2 — spread 0.20 Ah: the weakest falls to 1.90 Ah while the average is still written 2.00, an overstatement of 0.10; the two lines separate for the first time and a thin wedge opens between them.
Frame 3 — the slope takes shape: every extra 0.10 Ah of spread costs 0.05 Ah of usable capacity; the usable line is straight at a slope of −1/2, it does not bend.
Frame 4 — spread 0.40 Ah: a dot walks to the end of the line at 1.80 Ah usable, while the flat average line still reads 2.00; the wedge is widest here and the single C-15 tick measures it.
Frame 5 — closing note: a series string obeys the minimum, never the average; 2.00 Ah plus a symmetric spread are teaching assumptions, and a real asymmetric pack still uses only the minimum, not the halved rule.

Axes: horizontal spread s = max minus min in Ah, marked 0, 0.20, 0.40; vertical usable Ah, marked 1.80 and 2.00. All numbers stay as small hand-lettered annotations marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红全图只出现一次，是一段短刻度，量在「平均值」与「可用值」张得最宽的那道缺口上；不铺面、不当第二组曲线的颜色。源图把可用曲线画成红色只为与平均线区分，这里改成 C-03 虚线，并在文字里注明。

同一张图、同一视角的五个帧，无人、无卡通吉祥物、无品牌 Logo、不写实拍，纯示意：

1. 极差是 0：四节等高，最弱的也是 2.00 Ah；平均值线与可用线完全重合，平均没有撒谎。
2. 极差 0.20 Ah：最弱掉到 1.90 Ah，平均值仍写 2.00，多报 0.10；两条线第一次裂开一道细缝。
3. 斜率成形：极差每大 0.10 Ah，可用少 0.05 Ah；可用线斜率 −1/2，是一条不弯的直线。
4. 极差 0.40 Ah：点走到线末，可用 1.80 Ah；平均线仍平在 2.00，缺口最宽，唯一 C-15 短刻度就量在这里。
5. 收束加脚注：串联只认最小值，不认平均；2.00 Ah 与「左右对称的极差」是教学假设，真实电池不对称时仍只用最小值，不用这个 1/2。

坐标：横轴是极差 s = 最大减最小（Ah），标 0 / 0.20 / 0.40；纵轴是串联可用 Ah，标 1.80 与 2.00。数字只用小手写标注，全部标「示意」。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 危险仅 C-15，且只有一处（平均值与可用值最宽的那道缺口）
- [ ] 第二组曲线是 C-03 虚线，不是红色，且文字已说明这处改色
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 五帧同一视角，点沿可用线单向移动，可暂停阅读
- [ ] 数字只用源图的 2.00 / 1.90 / 1.80 / 0.20 / 0.40 / 0.10 / 0.05 与 −1/2，且全部标示意
- [ ] 首末帧单独成图仍可读
