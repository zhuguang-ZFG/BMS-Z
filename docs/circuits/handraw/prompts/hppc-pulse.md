---
search: false
slug: hppc-pulse
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: hppc-identification
source_svg: bms-book/assets/hppc-pulse.svg
---

# 观察题

同一条 3 A 脉冲只持续 10 秒，为什么只读前 40 秒算出的 R1 会错 17.5%？

# 帧大纲

1. ① 预静置：电流为 0，压降曲线贴着 0 mV 基线不动，时间轴从 0 s 起，没有任何读数在动。
2. ② 脉冲注入 +3 A·10 s：电流台阶抬起，曲线当场掉 I·R0 = 3 A × 33 mΩ = 99.0 mV，竖向一格到位。
3. ③ 欧姆跳变放大：跳变窗内均值差 97.8 mV，反推 R0 估值 32.6 mΩ（真值 33.0 mΩ，差在噪声 σ = 1 mV），跳变窗用 C-03 细线小括号框住。
4. ④ 极化爬升：10 s 内只爬到 I·(R0+R1) = 147 mV 满幅的 24.8%，再多掉 11.9 mV，曲线缓慢上拱而不是继续直掉。
5. ⑤ 撤流回弹：电流归零，欧姆项 99.0 mV 退出，曲线向上一跳，只剩极化那点残余慢慢退。
6. ⑥ 松弛趋渐近线：撤流后 1τ = 35.2 s；40 s 窗（1.1τ）算 R1 误差 17.5%，拉满 120 s（3.4τ）才压到 0.44%——窗口长度决定辨识可信度。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only.

C-15 is used zero times in this figure: the source marks no hazard or cutoff, so its red measured trace becomes a C-03 solid line with hand jitter and its second model curve becomes a C-03 fine dashed line. Vermilion does not serve as a series colour.

Six frames of the same pulsed-current voltage trace, same viewpoint, timing axis 0–175 s and drop axis 0–160 mV, no people, no cartoon mascot, no brand logos, no photorealistic or oscilloscope-screenshot claim, schematic only:

Frame 1 — ① pre-rest: current is zero, the trace lies flat on the 0 mV baseline.
Frame 2 — ② pulse +3 A for 10 s: the current steps up and the trace drops instantly by I·R0 = 3 A × 33 mΩ = 99.0 mV.
Frame 3 — ③ ohmic jump, magnified: the jump window's mean difference of 97.8 mV gives an R0 estimate of 32.6 mΩ against a true 33.0 mΩ, the gap explained by σ = 1 mV noise.
Frame 4 — ④ polarization climb: within 10 s the polarization charges only to 24.8% of the full I·(R0+R1) = 147 mV, a further 11.9 mV; the curve arcs upward instead of falling straight.
Frame 5 — ⑤ current removed: the ohmic 99.0 mV leaves at once, the trace jumps back up leaving only the residual polarization to decay.
Frame 6 — ⑥ relaxation toward the asymptote: after removal 1τ = 35.2 s; a 40 s window (1.1τ) leaves 17.5% R1 error, while the full 120 s window (3.4τ) brings it to 0.44% — window length sets how much the identification can be trusted.

Numbers stay as small hand-lettered annotations, all marked 示意 / simulated with seed and noise stated, not a shipped-cell measurement. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。

本图 C-15 零次：源图没有危险或截止标记，红色那条含噪测量曲线改成 C-03 实线加手绘抖动，另一条无噪声模型曲线改成 C-03 细虚线。朱砂红不当系列颜色。

同一条脉冲电压响应六个帧、同一视角，时间轴 0–175 s、压降轴 0–160 mV，无人、无卡通吉祥物、无品牌 Logo、不写实拍、不模仿示波器截图，纯示意：

1. ① 预静置：电流为零，曲线贴在 0 mV 基线上不动。
2. ② 脉冲 +3 A·10 s：电流台阶抬起，曲线立刻掉 I·R0 = 3 A × 33 mΩ = 99.0 mV。
3. ③ 欧姆跳变放大：跳变窗均值差 97.8 mV，反推 R0 估值 32.6 mΩ，真值 33.0 mΩ，差在 σ = 1 mV 噪声。
4. ④ 极化爬升：10 s 内只爬到 I·(R0+R1) = 147 mV 满幅的 24.8%，再掉 11.9 mV，曲线开始上拱。
5. ⑤ 撤流回弹：电流归零，欧姆项 99.0 mV 退出，曲线向上一跳，只剩极化残余在退。
6. ⑥ 松弛趋渐近线：撤流后 1τ = 35.2 s；40 s 窗（1.1τ）R1 误差 17.5%，满窗 120 s（3.4τ）才到 0.44%——窗口长度决定辨识可信度。

数字只用小手写标注，全部标「示意」（仿真 seed=7、合成电芯 R0 = 33 mΩ / R1 = 16 mΩ / C1 = 2200 F、噪声 σ = 1 mV），不是实车电芯实测。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] C-15 零次，含噪测量曲线已改画为 C-03 实线 + 抖动
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一视角，①–⑥ 编号与源图一致
- [ ] 99.0 / 147 / 11.9 / 97.8 mV 与 32.6 / 33.0 mΩ 全部来自源图，未新增数字
