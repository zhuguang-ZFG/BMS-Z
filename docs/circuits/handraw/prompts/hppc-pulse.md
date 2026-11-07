---
search: false
slug: hppc-pulse
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: hppc-identification
source_svg: docs/circuits/assets/archive/hppc-pulse.svg
---

# 观察题

同一条 3 A 脉冲只持续 10 秒，为什么只读前 40 秒算出的 R1 会错 17.5%？

# 帧大纲

1. 预静置：直接读取 `bms-book/code/hppc_fit.py::simulate_pulse()` 默认 seed=7 数据，时间 0–59.9 s；电流为 0，无噪模型保持 0 mV，含噪轨迹仅有 1 mV 电压噪声，不提前画 60 s 的注入。
2. 脉冲注入：60 s 起 +3 A、持续 10 s；欧姆项立即出现，理论偏移 99.0 mV。
3. 欧姆读数：使用同一份数据的前 1 s / 后 0.3 s 均值；电压均值差约 98.6 mV，按含噪电流差算 R0=32.85 mΩ，真值 33.00 mΩ。章首 97.8 mV / 32.6 mΩ 是另一组对照，不能贴到这条曲线上。
4. 极化建立：截至撤流前；10 s 只建立极化支路满幅 I·R1=48 mV 的约 24.7%，残余约 11.9 mV；不能写成总偏移 147 mV 的 24.7%。
5. 撤流回弹：70 s 撤流，欧姆项退出，极化残余连续释放。
6. 全窗：0–190 s 横轴、60–70 s 脉冲；从撤流点分别标 40 s 与 120 s 观察窗，侧栏显示同数据拟合 R1 误差 17.5% / 0.44%。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only.

C-15 is used zero times in this figure: the source marks no hazard or cutoff, so its red measured trace becomes a C-03 solid line with hand jitter and its second model curve becomes a C-03 fine dashed line. Vermilion does not serve as a series colour.

Six frames share an aligned voltage-offset/current time axis and a separate reading column. Use the actual seeded synthetic samples from `bms-book/code/hppc_fit.py`, not invented measurement jitter. Voltage offset is positive downward; do not call it a measured discharge-voltage drop. Pre-rest ends strictly before injection at 60 s, the pulse lasts to 70 s, and relaxation continues to 190 s. Keep noisy samples as a fine solid blue line and the noiseless model as a dashed blue line. The reading column uses the same run: R0=32.85 mΩ, a 24.7% polarization fraction of I·R1=48 mV, and R1 fitting errors of 17.5% / 0.44% for 40 s / 120 s windows. Separate these script values from the chapter's introductory 97.8 mV / 32.6 mΩ example. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。

本图 C-15 零次：源图没有危险或截止标记，红色那条含噪测量曲线改成 C-03 实线加手绘抖动，另一条无噪声模型曲线改成 C-03 细虚线。朱砂红不当系列颜色。

六帧共享对齐的电压偏移/电流时间轴，右侧独立读数栏，不把大段标注压在曲线上。曲线直接来自同一份 seed=7 合成数据；电压偏移正向朝下，不冒充放电端电压实测。60 s 注入、70 s 撤流、190 s 结束；首帧严格停在注入前。含噪数据细实线，无噪模型真虚线，仍全图零红。读数使用本次脚本复算结果：R0=32.85 mΩ、极化支路完成约 24.7%、观察窗 R1 误差 17.5% / 0.44%。数字注明合成示例、噪声 1 mV / 5 mA，图注「原理示意 / 非实拍」。

# 验收自检

- [ ] 无人、无卡通
- [ ] C-15 零次，含噪测量曲线已改画为 C-03 实线 + 抖动
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一视角，预静置不提前画脉冲；读数放侧栏，电流与电压共用时间轴
- [ ] 本次数据与章首对照分清；极化 24.7% 的分母为 I·R1=48 mV，不是 147 mV
