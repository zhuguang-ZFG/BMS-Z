---
search: false
slug: rint-windows
style: FA-029
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: load-voltage-drop
source_svg: null
---

# 观察题

同一颗电芯，为什么 10 ms 和 10 s 脉冲量出的「内阻」不是同一个数？报出阻值时还必须一起报什么？——因为窗越长，算进的极化越多，而「内阻」从来不是一个脱离测试条件的数。

# 帧大纲

1. 版式立起：一条对数时间轴（10⁻⁴ s → 10⁷ s，十一个十进位），五条带将按各自的时间范围横跨这条轴，先只给轴与刻度。
2. 第一条带——仪器能分辨的最快阶跃：只有导体、接触、电解液的快速压降，工程模型里只是 R₀ 的一部分，不是「内阻」。
3. 加两条带——毫秒至秒看见界面反应与双电层（高频 RC、电荷转移阻力）；秒至数十分钟是固相／电解液扩散（一个或多个 RᵢCᵢ，τ_D∼R_p²/D_s≈2500 s，即 42 min）。
4. 补齐更慢的两层——数十秒至数小时是热积累与散热（热阻–热容网络）；循环至日历时间才看见容量和阻抗慢慢变化（老化参数漂移）。
5. 两道观察窗落下：10 ms 与 10 s 画成嵌套横括，前者只圈进快速压降加一部分双电层，后者里双电层已做完、扩散才刚开始——两窗量出的「内阻」不是同一个数，数值必须连同测试协议保存。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. All linework and labels in Prussian blue C-03 only; zero use of C-15 in this figure. Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

Five frames, one fixed layout: a single logarithmic time axis spanning 10⁻⁴ s to 10⁷ s, with five horizontal bars stacked above it, each bar spanning the decades of its own time range, a left-hand label column naming the observation time and a right-hand column naming its shadow in the engineering model. No people, no cartoon mascot, no brand logos, no photorealistic claim:

Frame 1 — layout only: the logarithmic time axis with decade ticks from 10⁻⁴ to 10⁷ seconds; no bars yet.
Frame 2 — first bar: the fastest step the instrument can resolve, holding only the fast voltage drop of conductors, contacts and electrolyte; in the model it is merely part of R₀.
Frame 3 — two more bars: milliseconds to seconds reveals interface reaction and the double layer (high-frequency RC, charge-transfer resistance); seconds to tens of minutes is solid-phase and electrolyte diffusion (one or more RᵢCᵢ).
Frame 4 — the slower two bars: tens of seconds to hours is heat accumulation and dissipation (thermal resistance–capacitance network); cycle to calendar time is where capacity and impedance drift slowly (aging parameter drift).
Frame 5 — two measurement windows arrive as nested horizontal brackets measured from the axis origin: the 10 ms window encloses only the fast drop plus part of the double layer; inside the 10 s window the double layer is finished and diffusion has only just begun. Closing line: the two windows do not measure the same number.

# Prompt（ZH）

手绘教学信息图，FA-029 Chris Ware 几何叙事风格：扁平几何分格、精确的尺规框线、克制的冷静构图、纸张颗粒。所有线条与标注只用普鲁士蓝 C-03，本图完全不用 C-15。数字一律作为小号手写注记，全部标注「示意」。页脚：原理示意 / 非实拍。

五帧，一套固定版式：一条对数时间轴（10⁻⁴ s 至 10⁷ s），轴上方堆五条横带，每条带按自己的时间范围横跨相应的十进位；左列标「观察时间」，右列标「工程模型里的影子」。不画人物、不画卡通吉祥物、不含品牌标识、不声称实拍：

第 1 帧——只立版式：对数时间轴与 10⁻⁴ 到 10⁷ 秒的十进位刻度，暂不出带。
第 2 帧——第一条带：仪器能分辨的最快阶跃，里面只有导体、接触、电解液的快速压降；在模型里只是 R₀ 的一部分。
第 3 帧——再加两条：毫秒至秒看见界面反应与双电层（高频 RC、电荷转移阻力）；秒至数十分钟是固相／电解液扩散（一个或多个 RᵢCᵢ）。
第 4 帧——补齐更慢的两条：数十秒至数小时是热积累与散热（热阻–热容网络）；循环至日历时间看见容量和阻抗慢慢变化（老化参数漂移）。
第 5 帧——两道观察窗以嵌套横括从轴左端量起：10 ms 窗只圈进快速压降加一部分双电层；10 s 窗里双电层已做完、扩散才刚开始。收束句：两窗量出的「内阻」不是同一个数。

# 取数出处

- 五行「观察时间 / 更容易看见什么 / 工程模型里的影子」逐字取自书稿第 1 章 §1.9 表 1-5。
- 「同一电芯用 10 ms 和 10 s 脉冲得到的『内阻』通常不同，后者算进了更多极化。数值必须连同测试协议保存。」取自同节正文。
- τ_D∼R_p²/D_s≈2500 s（42 min）取自 §1.8 的教学值 R_p=5 µm、D_s=10⁻¹⁴ m²/s；本图只用于标注扩散带的量级，不另造数字。
- 时间轴范围 10⁻⁴–10⁷ s 为容纳表 1-5 五行的教学取整，标注为示意。
