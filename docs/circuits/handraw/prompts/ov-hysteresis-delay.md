---
slug: ov-hysteresis-delay
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: protection-debounce
source_svg: docs/circuits/assets/ov-hysteresis-delay.svg
---

# 观察题

同一条 4.28 V 的线，为什么第一次被越过时什么都没断？看那根 1.0 s 的确认尺，在 1.5–1.8 s 和 3.0 s 之后各自走了多远。

# 帧大纲

1. 起手：电压从 4.12 V 附近缓缓爬升（横轴 0–8 s，纵轴 4.12–4.34 V）；断开线 4.28 V 与恢复线 4.18 V 横贯全幅，旁边立一根 1.0 s 的确认尺。
2. 毛刺 0.3 s：1.5–1.8 s 冲到 4.34 V，越过 4.28 V 但远不足 1.0 s；确认计时清零，MOS 不动。
3. 真的越过：3.0 s 起波形停在 4.32 V，比较器翻转，确认计时从零起走。
4. 确认满 1.0 s：4.0 s 断开充电 MOS——全图唯一 C-15 落在这条越限跨线并断开的一刻。
5. 回差：波形往下走，但仍在 4.18 V 之上，开关保持断开——回差让它先别急着合。
6. 收束：6.2 s 电压落到 4.12 V、低于恢复线，才允许重新合上；末行写「阈值、回差、确认时间，三件事叠在同一条电压上」。旁注：4.28 V / 4.18 V / 1.0 s 都是示意，不是某一颗保护 IC 的规格，铁锂阈值完全不同。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 appears exactly once, as a single small tick where the real over-limit crossing is confirmed and the charge switch opens — never as a fill, never as a second series colour. The trip and release lines are C-03 dashed; they are the limit geometry, not the danger itself.

Six frames of one voltage-versus-time panel, horizontal 0 to 8 s, vertical 4.12 to 4.34 V, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim, schematic only:

Frame 1 — a slow ramp starts near 4.12 V; the trip line at 4.28 V and the release line at 4.18 V run across the full width, with a separate 1.0 s confirmation ruler standing beside the trace.
Frame 2 — a spike at 1.5 to 1.8 s jumps to 4.34 V: it clears 4.28 V but lasts only 0.3 s, far short of the 1.0 s confirmation, so the timer resets and the switch does not move.
Frame 3 — the real crossing: from 3.0 s the trace settles at 4.32 V, the comparator flips, and the confirmation timer starts from zero.
Frame 4 — at 4.0 s the confirmation reaches 1.0 s and the charge switch opens; the single C-15 tick marks this crossing-and-opening instant.
Frame 5 — the trace falls back but stays above 4.18 V, so the switch remains open; hysteresis is what keeps it from re-closing early, and this frame carries no red.
Frame 6 — at 6.2 s the voltage reaches 4.12 V, below the release line, and only then may the switch close again; the closing line reads that threshold, hysteresis and confirmation time are three things stacked on the same voltage trace. Margin note: 4.28 V, 4.18 V and 1.0 s are illustrative, not the datasheet of any protection IC, and a lithium-iron-phosphate pack has entirely different thresholds.

Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红全图只出现一次，点在真的越限被确认、充电开关断开的那一刻；不铺面、不当第二组颜色。断开线与恢复线都是 C-03 虚线——它们是限值的几何，不是危险本身。

同一块「电压对时间」画面的六个帧，横轴 0–8 s、纵轴 4.12–4.34 V，同一视角，无人、无卡通吉祥物、无品牌 Logo、不写实拍，纯示意：

1. 电压从 4.12 V 附近慢慢爬升；断开线 4.28 V、恢复线 4.18 V 横贯全幅，旁边另立一根 1.0 s 的确认尺。
2. 1.5–1.8 s 一记毛刺冲到 4.34 V：越过 4.28 V，但只撑 0.3 s，远不够 1.0 s，确认计时清零，开关不动。
3. 真的越过：3.0 s 起波形停在 4.32 V，比较器翻转，确认计时从零起走。
4. 4.0 s 确认满 1.0 s，充电开关断开；唯一 C-15 点在这道跨线并断开的一刻。
5. 波形回落，但仍在 4.18 V 之上，开关保持断开——回差让它先别急着合，这一帧一点红都不带。
6. 6.2 s 电压落到 4.12 V，低于恢复线，才允许重新合上；末行：阈值、回差、确认时间，三件事叠在同一条电压上。旁注：4.28 V / 4.18 V / 1.0 s 都是示意，不是某一颗保护 IC 的规格，铁锂阈值完全不同。

数字只用小手写标注，全部标「示意」。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 危险仅 C-15，且只有一处（确认满 1.0 s、开关断开那一刻）
- [ ] 断开线与恢复线是 C-03 虚线，不是红色
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一视角，毛刺 0.3 s 与确认 1.0 s 的时长对比一眼可辨，可暂停阅读
- [ ] 数字只用源图的 4.28 / 4.18 / 4.34 / 4.32 / 4.12 V、0.3 / 1.0 s、1.5–1.8 s、3.0 / 4.0 / 6.2 / 8 s，且全部标示意
- [ ] 首末帧单独成图仍可读
