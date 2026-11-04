---
slug: polarization-physics
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: load-voltage-drop
source_svg: docs/circuits/assets/polarization-physics.svg
---

# 观察题

卸流那一刻电压先跳回 40 mV，剩下的 0.110 V 为什么要几分钟才还回来——盯住表面那层点阵，看它是怎么被抽空、又怎么被扩散抹平的。

# 帧大纲

1. 静置平衡：表面层与内部的点阵疏密一致，端电压停在 3.550 V（示意），曲线上只有一个孤零零的起点，没有梯度。
2. 开始放电：电流抽走表面锂离子，表面层点阵变稀、内部仍旧密实（内部还密，表面已空），浓度梯度出现，端电压从 3.550 V 往下滑。
3. 带载维持：读数钉在 3.400 V，开路仍在 3.550 V；电流不停，表面就一直空着，梯度既不扩大也不再收敛。
4. 第 3 分钟卸流（竖虚线）：电流归零，端电压在曲线上竖直跳一下，按 R0 从 3.400 V 抬到 3.440 V；表面还没回匀，梯度仍在。
5. 扩散回匀：扩散把表面与内部的点阵拉平，曲线离开 3.440 V，沿 3.550 − 0.110·e^(−(t−3)/2) 弯向 3.550 V，横轴 0 / 3 / 6 / 10 min。
6. 收束：两个读数时刻并置——急着在 3.440 V 读，把还没散的极化当成开路电压；等回弹到 3.550 V 再读，才是 OCV。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 stays unused in this figure — the source marks no hazard, so nothing is red. The source's purple voltage trace is recoloured: it becomes a C-03 dashed line, told apart from the open-circuit reference by dash pattern and weight, not by hue. No people, no cartoon mascot, no brand logos, no photorealistic or oscilloscope-screenshot claim. Schematic only.

Six frames of the same cell cross-section plus the same small voltage-versus-time panel, same viewpoint, no camera move:

Frame 1 — at rest: surface layer and interior carry the same evenly spaced ion dots; terminal voltage 3.550 V; the curve holds a single starting point, no gradient.
Frame 2 — discharge begins: current draws lithium ions off the surface, the surface dot field thins while the interior stays dense (内部还密，表面已空); a concentration gradient appears and the terminal voltage starts to sag from 3.550 V.
Frame 3 — under load: the reading is pinned at 3.400 V while open circuit remains 3.550 V; the surface stays emptied for as long as current flows, the gradient neither grows nor closes.
Frame 4 — current removed at minute 3 (vertical dashed marker): the trace jumps straight up by 40 mV as R0 returns, from 3.400 V to 3.440 V; the surface is still depleted, the gradient still there.
Frame 5 — diffusion evens out: diffusion flattens the surface/interior dot field, the trace leaves 3.440 V and bends toward 3.550 V along 3.550 − 0.110·e^(−(t−3)/2), time axis 0 / 3 / 6 / 10 min.
Frame 6 — closing panel: two reading moments side by side — reading at 3.440 V mistakes undissipated polarization for open-circuit voltage; only after the rebound reaches 3.550 V is OCV readable.

Axis ticks keep the source's 3.40 / 3.46 / 3.52 / 3.58 V and 0 / 3 / 6 / 10 min. All values hand-lettered and marked 示意. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红在本图完全不用——源图没有危险标记，画面不出现红色。源图的紫线在这里改色：端电压曲线画成 C-03 虚线，与开路参考线靠虚线节奏与线宽区分，不靠色相。无人、无卡通吉祥物、无品牌 Logo、不写实拍、不冒充示波器截图，纯示意。

同一颗电芯的剖面加同一块小电压-时间面板，六个帧、同一视角、不移动镜头：

1. 静置：表面层与内部的离子点阵疏密一致；端电压 3.550 V；曲线只有一个起点，没有梯度。
2. 开始放电：电流把表面锂离子抽走，表面点阵变稀、内部仍密（内部还密，表面已空）；浓度梯度出现，端电压从 3.550 V 往下滑。
3. 带载：读数钉在 3.400 V，开路仍是 3.550 V；电流不停，表面就一直空着，梯度既不扩大也不收敛。
4. 第 3 分钟卸流（竖虚线）：曲线竖直跳 40 mV，按 R0 从 3.400 V 抬到 3.440 V；表面仍未回匀，梯度还在。
5. 扩散回匀：扩散把表面与内部的点阵抹平，曲线离开 3.440 V，沿 3.550 − 0.110·e^(−(t−3)/2) 弯向 3.550 V，横轴 0 / 3 / 6 / 10 min。
6. 收束：两个读数时刻并置——3.440 V 就读，是把没散掉的极化当开路电压；等回弹到 3.550 V 再读，才是 OCV。

坐标刻度沿用源图的 3.40 / 3.46 / 3.52 / 3.58 V 与 0 / 3 / 6 / 10 min。所有数字手写并标「示意」。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 全图无危险点：C-15 保留不用
- [ ] 端电压曲线已由紫改 C-03 虚线，未引入第三色
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 三个电压值（3.400 / 3.440 / 3.550 V）与 40 mV、0.110 V 逐字照源图，未改算
