---
search: false
slug: ocv-rest-timeline
style: FA-002
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: ocv-trust
source_svg: docs/circuits/assets/archive/ocv-rest-timeline.svg
---

# 观察题

撤掉电流的那一刻电压就跳了一格，为什么还得再等十分钟才敢把这个读数当开路电压？

# 帧大纲

1. 带载放电：曲线被按在 3.450 V 这条平线上，电流箭头仍在——读数是带载读数，不是开路电压。
2. 撤流瞬间 t = 0⁺：电流归零，欧姆压降当场消失，曲线竖直跳到 3.490 V，一格 +40 mV，这是「立刻回弹」。
3. 慢慢松弛：指数段 V(t) = 3.620 − 0.130·exp(−t/3)，时间轴走到 3 min，读数 3.572 V（1τ），离极限仍差约 48 mV。
4. 继续等：10 min 到 3.615 V，仍差约 5 mV，曲线贴着渐近线 3.620 V（放电支极限）才肯收平。
5. 对照页：同一 SOC 的充电支画在 3.660 V，与放电支极限相隔 40 mV——滞回仍在，静置不是充电；τ = 3 min 也不等于已经完全平衡。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only.

C-15 is used zero times in this figure: the source states no cutoff or limit violation, so its red charge-branch comparison curve becomes a C-03 dashed line and the red 40 mV hysteresis figure becomes a C-03 double-headed arrow. Vermilion is not spent on a comparison series.

Five frames of the same voltage-versus-rest-time chart, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic or oscilloscope-screenshot claim, schematic only:

Frame 1 — loaded discharge held at 3.450 V, current arrow still present; the axis is labelled 带载 / loaded.
Frame 2 — current removed at t = 0⁺: ohmic drop vanishes, the trace steps vertically to 3.490 V, one +40 mV jump, marked 立刻回弹.
Frame 3 — slow relaxation: the exponential V(t) = 3.620 − 0.130·exp(−t/3) curves upward; at 3 min the reading is 3.572 V (1τ) and is still about 48 mV short of the limit.
Frame 4 — at 10 min the reading is 3.615 V, about 5 mV short, flattening onto the 3.620 V asymptote (discharge-branch limit); the trace visibly stops climbing.
Frame 5 — comparison panel: the charge branch at the same SOC sits at 3.660 V, 40 mV above the discharge limit; hysteresis remains, rest is not charging, and τ = 3 min does not mean equilibrium.

Numbers stay as small hand-lettered annotations, all marked 示意. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。

本图 C-15 零次：源图没有画出截止线或越限，红色只用来区分「充电支」这条对照曲线，因此改为 C-03 虚线；红色的 40 mV 滞回数字改画成一支 C-03 双向箭头。朱砂红不花在对照曲线上。

同一张「电压—静置时间」图五个帧、同一视角，无人、无卡通吉祥物、无品牌 Logo、不写实拍、不模仿示波器截图，纯示意：

1. 带载放电：曲线压在 3.450 V，电流箭头仍在，标注「带载」。
2. 撤流瞬间 t = 0⁺：欧姆压降消失，曲线竖直跳到 3.490 V，一格 +40 mV，标「立刻回弹」。
3. 慢慢松弛：指数段 V(t) = 3.620 − 0.130·exp(−t/3)；3 min 读到 3.572 V（1τ），离极限仍差约 48 mV。
4. 10 min 读到 3.615 V，仍差约 5 mV，曲线贴住 3.620 V 渐近线（放电支极限）不再上抬。
5. 对照：同 SOC 充电支在 3.660 V，比放电支极限高 40 mV——滞回仍在，静置不是充电，τ = 3 min 不等于已经平衡。

数字只用小手写标注，全部标「示意」；静置判据须按电芯、温度与测量精度实测。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] C-15 零次，充电支与 40 mV 滞回已改画为 C-03
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 五帧同一视角；时间轴 0 / 3 / 6 / 10 min 与带载段可分
- [ ] 「τ = 3 min 不代表已平衡」在末帧可见
