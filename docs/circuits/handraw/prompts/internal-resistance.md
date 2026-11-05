---
search: false
slug: internal-resistance
style: FA-002
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: load-voltage-drop
source_svg: docs/circuits/assets/internal-resistance.svg
---

# 观察题

端电压掉下去的那一截，究竟是谁吃掉的？合闸再撤载，看同一颗电芯的读数怎么回弹。

# 帧大纲

1. 静置：端电压 = 开路电压，指针停在 3.9 V（示意），电路里没有电流。
2. 合闸带载 20 A（示例）：电流穿过「变细的水管段」——内阻，端电压立刻掉 I×R = 0.40 V。
3. 同一 20 A 换成老化内阻 60 mΩ：压降变成 1.20 V，读数跌到 2.7 V，碰到截止线（全图唯一 C-15 处）。
4. 撤载：电流归零，端电压回弹到 3.9 V，带载时的「虚低」被揭穿。
5. 收束：ΔV = I×R 的两条过原点直线（20 mΩ 与 60 mΩ），一个点沿 20 mΩ 那条滑动。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 appears exactly once, as a small danger tick where the terminal voltage crosses the cutoff line — never as a fill, never as a second series colour.

Five frames of the same battery cell, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim, schematic only:

Frame 1 — cell at rest: open-circuit voltage 3.9 V, ammeter at zero, terminal voltage equals EMF.
Frame 2 — switch closed at 20 A (illustrative value): current threads through a narrowed pipe section representing internal resistance; terminal voltage sags by I×R = 0.40 V.
Frame 3 — same 20 A on an aged cell, internal resistance 60 mΩ: sag becomes 1.20 V, reading falls to 2.7 V and touches the cutoff line (single C-15 mark).
Frame 4 — switch opened: current returns to zero, terminal voltage rebounds to 3.9 V; the loaded reading is exposed as falsely low.
Frame 5 — closing panel: two straight lines through the origin for ΔV = I×R at 20 mΩ and 60 mΩ, one dot sliding along the 20 mΩ line.

Numbers stay as small hand-lettered annotations; all values marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红全图只出现一次，标在端电压碰到截止线的那一点；不铺面、不当第二组曲线的颜色。

同一颗电芯五个帧、同一视角，无人、无卡通吉祥物、无品牌 Logo、不写实拍，纯示意：

1. 静置：开路电压 3.9 V，电流为零，端电压 = 电动势。
2. 合闸带载 20 A（示例）：电流穿过象征内阻的「变细的水管段」，端电压按 I×R 掉 0.40 V。
3. 同一 20 A 落在老化电芯（内阻 60 mΩ）：压降 1.20 V，读数跌到 2.7 V 并触碰截止线（唯一 C-15 标记）。
4. 撤载：电流归零，端电压回弹到 3.9 V，带载读数「虚低」被揭穿。
5. 收束：ΔV = I×R 的两条过原点直线（20 mΩ / 60 mΩ），一个点沿 20 mΩ 那条滑动。

数字只用小手写标注，全部标「示意」。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 危险仅 C-15，且只有一处
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 五帧同一视角，可暂停阅读
- [ ] 首末帧单独成图仍可读
