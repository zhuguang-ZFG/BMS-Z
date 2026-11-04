---
slug: precharge-sequence-curve
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: precharge-evidence
source_svg: docs/circuits/assets/precharge-sequence-curve.svg
---

# 观察题

母线电压要爬到哪一格，主闸 K1 才被允许合上？要是它半路停住不爬，谁替你守住这个条件？

# 帧大纲

1. t=0：只合预充闸，母线 0 V，冲击电流 400 V ÷ 170 Ω = 2.35 A（示意），主闸 K1 仍开；曲线从原点起步。
2. 一个 τ（0.17 s）：母线升到 253 V（约 63%），预充电流已落到 0.87 A；主闸仍开，曲线继续往上爬。
3. 约 3τ（0.51 s）：母线 380 V（约 95%），电流 0.12 A；合闸阈值竖线在此刻出现（C-03 虚线，原图的绿线），这一刻才允许合主闸、再打开预充闸。
4. 0.80 s：母线 396 V，电流 0.02 A；电流路径从 170 Ω 换到主闸，曲线拉平、贴近 400 V。
5. 故障分支：电压停在约 40 V 不再上升，K1 保持打开——水平故障线与它的标注是全图唯一 C-15 处。
6. 收束：一条 V = 400(1−e^(−t/0.17)) 曲线、两根时间竖线（0.17 / 0.51），旁注储能 ½CU² = 80 J 几乎全在 170 Ω 上变成热。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour tracing the charge path from precharge contactor through the 170 Ω resistor into the bus capacitor, generous white space, deadpan textbook tone, paper grain. Structure lines and labels in Prussian blue C-03 only. The contactor-close marker is a C-03 dashed vertical rule (the source's green rule is a timing marker, not a hazard). Vermilion C-15 appears exactly once, on the horizontal fault line at about 40 V where the bus stalls and K1 stays open — never as a fill, never as a second curve colour.

Six frames of the same bus, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim and no oscilloscope screenshot; schematic only:

Frame 1 — t=0: only the precharge contactor is closed, bus at 0 V, inrush current 400 V ÷ 170 Ω = 2.35 A (illustrative), main contactor K1 still open; the curve leaves the origin.
Frame 2 — one τ at 0.17 s: bus has risen to 253 V, roughly 63%, precharge current down to 0.87 A; K1 still open and the curve keeps climbing.
Frame 3 — about 3τ at 0.51 s: bus at 380 V, roughly 95%, current 0.12 A; the close-permission vertical rule appears at this instant (C-03 dashed), and only now may K1 close and the precharge contactor open.
Frame 4 — 0.80 s: bus at 396 V, current 0.02 A; the current path switches from the 170 Ω resistor to the main contactor and the curve flattens toward 400 V.
Frame 5 — fault branch: the bus stalls near 40 V and stops rising, K1 stays open; this horizontal fault line and its caption carry the only C-15 mark in the picture.
Frame 6 — closing panel: the single curve V = 400(1−e^(−t/0.17)) with two time rules at 0.17 and 0.51, and a small note that the ½CU² = 80 J stored at 400 V ends up almost entirely as heat in the 170 Ω resistor.

All values are small hand-lettered annotations marked 示意 / illustrative: 400 V, 1 mF, 170 Ω, 80 J. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一条不断的墨线从预充闸穿过 170 Ω 电阻画到母线电容，大片留白，冷面教科书语气，纸纹质感。结构线与标注只用 C-03 普鲁士蓝。合闸时刻画成 C-03 虚线竖标（原图的绿线只是时间标记，不是危险）。C-15 朱砂红全图只出现一次，标在母线卡在约 40 V、K1 保持打开的那条水平故障线上；不铺面，也不当第二组曲线的颜色。

同一套母线、同一视角的六个帧，无人、无卡通吉祥物、无品牌 Logo、不写实拍、不是示波器截图，纯示意：

1. t=0：只合预充闸，母线 0 V，冲击电流 400 V ÷ 170 Ω = 2.35 A（示意），主闸 K1 仍开，曲线从原点起步。
2. 一个 τ（0.17 s）：母线到 253 V（约 63%），预充电流降到 0.87 A，K1 仍开，曲线继续爬。
3. 约 3τ（0.51 s）：母线 380 V（约 95%），电流 0.12 A；合闸许可的虚线竖标在此刻出现，这时才合 K1、再打开预充闸。
4. 0.80 s：母线 396 V，电流 0.02 A；电流路径从 170 Ω 换到主闸，曲线拉平贴近 400 V。
5. 故障分支：电压停在约 40 V 不再上升，K1 保持打开——这条水平线与其标注是全图唯一 C-15。
6. 收束：一条 V = 400(1−e^(−t/0.17)) 曲线、两根时间竖线（0.17 / 0.51），旁注 400 V 充满的储能 ½CU² = 80 J 几乎全在 170 Ω 上变成热。

数字只用小手写标注，全部标「示意」：400 V、1 mF、170 Ω、80 J。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 危险仅 C-15，且只有一处（约 40 V 的故障保持线）
- [ ] 合闸标记已从绿线改为 C-03 虚线，未被当成危险
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一条曲线、同一视角，可暂停阅读
- [ ] 首末帧单独成图仍可读（0 V 起步 / 40 V 卡住都能辨认）
- [ ] 不出现示波器截图或真实录波口吻
