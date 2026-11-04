---
slug: protection-debounce
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: protection-debounce
source_svg: docs/circuits/assets/protection-debounce.svg
---

# 观察题

电压第一次冲过 4.25 V 时为什么什么都没发生？盯住那条去抖计时条——它清零的那一下，和走满的那一下，差在哪里。

# 帧大纲

1. 版式立起：横轴时间、纵轴电压；两条水平线——上是阈值 4.25 V、下是恢复 4.15 V（均为示例）；波形还躺在恢复线以下，MOS 画成通路。
2. 毛刺：波形短促越过 4.25 V，计时条开始走；毛刺短于去抖窗口 20 ms（示例），回落时计时清零，不动作。
3. 持续超限：波形停在阈值之上不下来，计时条一路走满 20 ms。
4. 走满的一瞬：MOS 断开——全图唯一 C-15 点在这一下，保护动作完成。
5. 回差区间：电压回落到阈值与恢复线之间，开关仍保持断开，回差防反复跳闸；这一段不再点红。
6. 收束：落回 4.15 V 以下才恢复导通；侧栏补一句锁存型（短路 / 过温）需人工或上位机清除；底线一句「去抖躲毛刺，回差防颤振，锁存留证据」。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 appears exactly once, as a single small tick at the instant the debounce timer fills and the switch opens — never as a fill, never as a second series colour. The threshold and release lines are C-03 dashed; they are the limit geometry, not the danger itself.

Six frames of the same voltage-versus-time panel, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim, schematic only:

Frame 1 — the panel is ruled: time along the horizontal, voltage up the vertical; two horizontal dashed lines stand in, threshold 4.25 V above, release 4.15 V below (both illustrative); the waveform rests under the release line and the switch is drawn closed.
Frame 2 — a short spike crosses 4.25 V: the debounce bar starts filling, but the spike is shorter than the 20 ms window, so the bar resets to zero on the fall and nothing acts.
Frame 3 — sustained over-limit: the waveform sits above the threshold and stays there; the debounce bar fills all the way through the 20 ms window.
Frame 4 — the bar fills, and the switch opens; the single C-15 tick marks exactly this instant.
Frame 5 — the voltage falls back into the band between threshold and release line and the switch stays open; hysteresis is what stops it from chattering, and this frame carries no red at all.
Frame 6 — only below 4.15 V does the switch close again; a side note adds that short-circuit and over-temperature faults latch and must be cleared by hand or by the host, and the bottom line reads: debounce hides spikes, hysteresis prevents chatter, latching keeps the evidence — protection is a decision chain, not a single line.

Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红全图只出现一次，点去抖计时走满、开关断开的那一瞬；不铺面、不当第二组颜色。阈值线与恢复线都是 C-03 虚线——它们是限值的几何，不是危险本身。

同一块「电压对时间」画面的六个帧、同一视角，无人、无卡通吉祥物、无品牌 Logo、不写实拍，纯示意：

1. 版式划好：横轴时间、纵轴电压；两条水平虚线——阈值 4.25 V 在上、恢复 4.15 V 在下（均为示例）；波形躺在恢复线以下，开关画成通路。
2. 一记毛刺越过 4.25 V：去抖条开始填，但毛刺短于 20 ms 窗口，回落的瞬间计时清零，什么也没发生。
3. 持续超限：波形停在阈值之上不下来，去抖条一路走满 20 ms。
4. 计时走满：开关断开；唯一 C-15 就点在这一刻。
5. 电压落回阈值与恢复线之间，开关仍保持断开——回差挡住反复跳闸，这一帧一点红都不带。
6. 只有落到 4.15 V 以下才重新闭合；侧栏补注：短路 / 过温这类严重故障用锁存型，需人工或上位机清除；底线写：去抖躲毛刺，回差防颤振，锁存留证据——保护不是一根线，是一套决策。

数字只用小手写标注，全部标「示意」。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 危险仅 C-15，且只有一处（计时走满、开关断开的那一刻）
- [ ] 阈值线与恢复线是 C-03 虚线，不是红色
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一视角，计时条状态与波形严格对应，可暂停阅读
- [ ] 数字只用源图的 4.25 V / 4.15 V / 20 ms，且全部标示意
- [ ] 首末帧单独成图仍可读
