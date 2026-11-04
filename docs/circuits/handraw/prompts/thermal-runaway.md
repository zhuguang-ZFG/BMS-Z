---
slug: thermal-runaway
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: overcharge-chain
source_svg: docs/circuits/assets/thermal-runaway.svg
---

# 观察题

等到「温度高」再报警来得及吗？盯住 dT/dt 那条线——它在温度读数还很平常的时候就已经抬起来了。

# 帧大纲

1. 幕一 · 过充 / 过热：电芯轮廓完好，两支外力箭头压进来——电压越线、环境高温；温度曲线在低位平走，坡度接近零。
2. 幕二 · 析锂枝晶：负极表面析出金属锂，长成尖刺（短刺由疏到密沿表面铺开）；温度曲线开始起坡。
3. 幕三 · 刺穿隔膜：一根尖刺穿透隔膜，正负极之间接出一条内部短路通路，温度曲线抬头变陡。
4. 幕四 · 热失控：放热 → 升温 → 更放热 收成一个闭合的自加速环，温度曲线由抬头变成近竖直。
5. 对策：dT/dt 温升速率报警线（全图唯一 C-15，一小段朱砂虚线）横在曲线的上升段上，越线那一点同时是切断位——在起火前切断。
6. 收束：底栏对照面板——同样 10 s，0.05 °C/s 只到 25.5 °C，1 °C/s 到 35 °C；结论落在「看升温有多快，而不是看温度有多高」。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 appears exactly once, as a short dashed alarm segment for the dT/dt threshold, with the point where the curve crosses it doubling as the cutoff mark — never as a fill, never to distinguish two temperature traces (both traces stay C-03, separated by weight and dash instead). No people, no cartoon mascot, no brand logos, no photorealistic claim, no photo of a burning cell. Schematic only.

Six frames of the same four-act mechanism strip plus the same small temperature-versus-time panel, same viewpoint, no camera move:

Frame 1 — act one, overcharge / overheating: an intact cell outline; two external arrows press in (voltage past the line, ambient heat); the temperature trace runs flat and low with almost no slope.
Frame 2 — act two, lithium plating: metallic lithium deposits on the anode surface and grows into spikes, short spikes spreading from sparse to dense along the surface; the trace begins to tilt.
Frame 3 — act three, separator pierced: one spike punches through the separator, an internal short path closes between anode and cathode; the trace lifts and steepens.
Frame 4 — act four, thermal runaway: heat → rising temperature → more heat closes into a self-accelerating loop; the trace turns from a lift into something near vertical.
Frame 5 — countermeasure: a dT/dt alarm line (the single C-15 mark, a short vermilion dashed segment) crosses the rising part of the curve; the crossing point is also the cutoff position — cut before it catches fire.
Frame 6 — closing panel: same 10 s window, 0.05 °C/s reaches only 25.5 °C while 1 °C/s reaches 35 °C; the caption logic is 「升温有多快才是最早的可观信号」, not the absolute temperature.

Numbers stay as small hand-lettered annotations with the source's 示意 marking; the 10 s window and both end values are quoted, never recomputed. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红全图只出现一处：dT/dt 阈值那一小段朱砂虚线，曲线越过它的那一点同时充当切断位；不铺面，也不用来区分两条温度曲线（两条都留 C-03，靠线宽与虚线区分）。无人、无卡通吉祥物、无品牌 Logo、不写实拍、不放燃烧照片，纯示意。

同一段四幕机制条加同一块小温度-时间面板，六个帧、同一视角、不移动镜头：

1. 幕一 过充 / 过热：电芯轮廓完好，两支外力箭头压进来（电压越线、环境高温）；温度曲线低位平走，坡度几乎为零。
2. 幕二 析锂枝晶：负极表面析出金属锂，长成尖刺，短刺沿表面由疏到密铺开；曲线开始起坡。
3. 幕三 刺穿隔膜：一根尖刺穿透隔膜，正负极之间接出内部短路通路；曲线抬头变陡。
4. 幕四 热失控：放热 → 升温 → 更放热 收成闭合的自加速环；曲线从抬头变成近竖直。
5. 对策：一条 dT/dt 温升速率报警线（唯一 C-15，一小段朱砂虚线）横在曲线的上升段上，越线那一点同时是切断位——在起火前切断。
6. 收束：同样 10 s 的对照面板，0.05 °C/s 只到 25.5 °C，1 °C/s 到 35 °C；结论写成「升温有多快才是最早的可观信号」，不是绝对温度。

数字只用小手写标注并按源图标「示意」；10 s 窗口与两个末值照抄，不重新计算。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通、无燃烧照片
- [ ] 危险仅 C-15，且只有一处（dT/dt 报警线及其越线点）
- [ ] 两条温度曲线同为 C-03，靠线宽/虚线区分
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 四幕顺序与 25.5 / 35 / 10 s 数值照源图，未增未改
