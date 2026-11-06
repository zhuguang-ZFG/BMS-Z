---
search: false
slug: bus-live-shapes
style: FA-029
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: precharge-evidence
source_svg: null
---

# 观察题

下电后量到母线仍有电，这一个读数能定下原因吗？——不能。表 8-2 的四种候选原因，在电压-时间曲线上各画出一种形状；分不开形状，就只能输出「隔离状态未确认」。

# 帧大纲

1. 只有一个读数：坐标轴立起（横轴为断开命令发出后的时间，纵轴标 400 V 与 60 V 两个刻度），红点落在 t=0、400 V 处，写明「下电后量到：母线仍有电」。一个读数定不了原因——四条形状都能从这里起笔。
2. 正常衰减做基准：按本章 §8.3 的 τ = 10 µF × 100 kΩ = 1.0 s 画指数线，粗实线。注明 0.1 s 时还有 361.9 V、5 s 才掉到 2.7 V——采样太早会把正常断开误判成粘连。
3. 贴近包压是另一族：点划线几乎贴在 400 V 一线，5 s 时仍在包压附近。形状分得开，原因仍要证据分：辅助触点、支路命令与电流、外部能源状态（表 8-2 该行逐字）。
4. 两种容易混的形状同时出现：长虚线是「慢于预期」，仍属指数族；短虚线是「读数一直不动」，是一条水平线。前者要实测 RC，后者要第二测点——证据不一样。
5. 第四种形状与结论：红实线在投入放电后斜率几乎不变，竖红虚线标出投入放电时刻。四种形状都对不上时，红色只落在一句结论——输出「隔离状态未确认」，不为了让状态机继续运行而选一个最方便的解释。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. All linework and labels in Prussian blue C-03; vermilion C-15 is reserved for the single observation marker and the final frame's concluding curve and line. Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

Five frames, one fixed layout: a single voltage-versus-time axis occupying the left two thirds, ticked at 400 V and 60 V on the vertical and at 0, 1 s and 5 s on the horizontal, with a right-hand legend column of short stroke swatches and hand-lettered cause text. Each cause is drawn in a distinct stroke so the legend maps unambiguously onto the curves: thick solid for the normal reference, dash-dot, long dash, short dash, and one vermilion solid. No people, no cartoon mascot, no brand logos, no photorealistic claim:

Frame 1 — the bare axis with a single vermilion dot at time zero and full pack voltage, annotated that the bus still reads live after shutdown and that one reading cannot choose among four shapes.
Frame 2 — the normal exponential decay is drawn as the thick solid reference curve, annotated with the measured time constant and the two sampled voltages that show how early sampling misreads a healthy opening.
Frame 3 — a dash-dot curve stays pinned near pack voltage across the whole window, with the distinguishing evidence for that row lettered below the axis.
Frame 4 — two confusable shapes appear together: a long-dash exponential that decays more slowly than expected, and a short-dash perfectly horizontal line representing a frozen reading that is not a bus state at all.
Frame 5 — a vermilion curve whose slope barely changes, a vermilion dashed vertical rule marking the moment active discharge is commanded, and a single concluding line stating that when no shape matches, the output is an unconfirmed isolation state.
