---
search: false
slug: ocv-plateau-distrust
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: ocv-trust
source_svg: docs/circuits/handraw/exports/ocv-plateau-distrust.webp
---

# 观察题

同是几毫伏的读数误差，为什么在曲线两端只值零点几个百分点，到了平台正中却能盖住六七个点？看那支 5 mV 的铅笔在曲线上落下多宽一道影子。

# 帧大纲

1. 两端还陡：游标停在 s=0.08，V=3.173，斜率 22.35 mV/1%；同样 5 mV 只换 0.2 个百分点，影子窄得几乎看不见。
2. 进入平台：曲线爬进 0.30 到 0.70 这一段，电压从 3.280 V 到 3.310 V，整段只动 30.0 mV——曲线被压成一条近水平的长坡。
3. 正中间：游标推到 s=0.50，V=3.295，斜率 0.75 mV/1%；一支 5 mV 的铅笔在曲线上横着一划，落下 6.7 个百分点宽的影子（全图唯一 C-15 标记）。
4. 局部放大：0.30–0.70 这一段被抽出来放大成右侧小图，纵轴只剩 3.28 / 3.295 / 3.31 三格，30.0 mV 摊在 40 个百分点上，一眼看出坡度有多薄。
5. 另一端：游标滑到 s=0.92，V=3.383，斜率回升到 14.20 mV/1%，5 mV 又只值 0.4 个百分点，影子重新收窄。
6. 收束：同一小段毫伏，在陡处与平台处映射出两个很不同的荷电宽度；旁注「电压只能定两端，平台这段信积分」。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour drawn as the cell's open-circuit-voltage curve, a small cursor riding it, generous white space, deadpan textbook tone, paper grain. Structure lines and labels in Prussian blue C-03 only. The plateau segment is emphasised with a heavier C-03 stroke, not red. Vermilion C-15 appears exactly once, as the short error bracket at SOC 0.50 whose 5 mV width casts a 6.7-percentage-point shadow — never as a fill, never as a second curve colour.

Six frames of the same OCV(SOC) curve with its zoom inset, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim, no oscilloscope screenshot; schematic only:

Frame 1 — the steep end: cursor at s=0.08, V=3.173, slope 22.35 mV per 1%; the same 5 mV now buys only 0.2 percentage points, and the shadow is a hairline.
Frame 2 — entering the plateau: the curve runs into the 0.30 to 0.70 stretch, voltage goes from 3.280 V to 3.310 V, only 30.0 mV across the whole span, and the contour flattens into a long shallow shelf.
Frame 3 — dead centre: cursor at s=0.50, V=3.295, slope 0.75 mV per 1%; a 5 mV pencil laid across the curve drops a shadow 6.7 percentage points wide — the only C-15 mark in the picture.
Frame 4 — zoom inset: the 0.30 to 0.70 stretch is lifted out into a panel at right, its vertical axis reduced to three gridlines 3.28 / 3.295 / 3.31, showing 30.0 mV spread over 40 percentage points.
Frame 5 — the other end: cursor slides to s=0.92, V=3.383, slope back up to 14.20 mV per 1%, so 5 mV is worth 0.4 percentage points again and the shadow narrows.
Frame 6 — closing panel: the same millivolt sliver maps to two very different charge widths depending on where it lands; a hand-lettered note reads 电压只能定两端，平台这段信积分.

All numbers are small hand-lettered annotations marked 示意 / illustrative; this is not any single cell's datasheet. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一条不断的墨线就是开路电压曲线，一个小游标骑在上面，大片留白，冷面教科书语气，纸纹质感。结构线与标注只用 C-03 普鲁士蓝。平台段用更粗的 C-03 加深，不上红。C-15 朱砂红全图只出现一次，即 SOC 0.50 处那支 5 mV 的误差横标——它落下的影子有 6.7 个百分点宽；不铺面，也不当第二组曲线的颜色。

同一条 OCV(SOC) 曲线带右侧放大窗、同一视角的六个帧，无人、无卡通吉祥物、无品牌 Logo、不写实拍、不是示波器截图，纯示意：

1. 两端还陡：游标在 s=0.08，V=3.173，斜率 22.35 mV/1%；同样 5 mV 只换 0.2 个百分点，影子细成一根发丝。
2. 进入平台：曲线走进 0.30 到 0.70 这一段，电压从 3.280 V 到 3.310 V，整段只动 30.0 mV，墨线被压成一道近水平的长坡。
3. 正中间：游标推到 s=0.50，V=3.295，斜率 0.75 mV/1%；5 mV 的铅笔在曲线上横着一划，落下 6.7 个百分点宽的影子——全图唯一 C-15。
4. 局部放大：0.30–0.70 这段抽到右侧放大窗，纵轴只剩 3.28 / 3.295 / 3.31 三格，30.0 mV 摊在 40 个百分点上。
5. 另一端：游标滑到 s=0.92，V=3.383，斜率回升到 14.20 mV/1%，5 mV 又只值 0.4 个百分点，影子重新收窄。
6. 收束：同一条毫伏细条落在不同位置，映射出很不一样的荷电宽度；手写旁注「电压只能定两端，平台这段信积分」。

数字只用小手写标注，全部标「示意」；不冒充任何一颗电芯的规格。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 危险仅 C-15，且只有一处（s=0.50 的 5 mV 横标）
- [ ] 平台段用加粗 C-03 强调，没有被画成红色曲线
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一条曲线、同一视角，可暂停阅读
- [ ] 首末帧单独成图仍可读（陡段窄影子 / 平台宽影子都能辨认）
- [ ] 纵轴与放大窗的刻度值都来自源图，没有新造数字
