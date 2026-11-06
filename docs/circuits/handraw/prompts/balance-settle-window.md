---
search: false
slug: balance-settle-window
style: FA-029
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: measurement-budget
source_svg: null
---

# 观察题

均衡一关就能采样吗？——不能。关断瞬间读到的还是「带着均衡负载的电压」，偏低量与停止判据同量级；要等几个 τ 才落底，这张图把两笔账画到同一条时间轴上。

# 事实表

出处：书稿 [第 9 章 §9.9](../../../../bms-book/book/09-均衡.md)「关断—采样之间要等多久」。合成电芯取 `bms-book/code/soc/compare.py` 的 R0=20 mΩ、R1=15 mΩ、C1=3000 F，本图只用 R1 与 C1。

| 量 | 值 | 来源 |
|---|---|---|
| 均衡电流 | 180 mA | §9.9 被动均衡实测区间 150–200 mA 取中 |
| 回路电阻 | 100 mΩ | §9.9：电芯内阻 + 线阻 + MOS 导通电阻 |
| 关断瞬间偏低 E0 | 18 mV | 180 mA × 100 mΩ |
| 时间常数 τ | 45 s | R1·C1 = 15 mΩ × 3000 F |
| 1τ = 45 s 残余 | 6.6 mV | 18 × e⁻¹ = 6.622 mV，回弹 63.2% |
| 2τ = 90 s 残余 | 2.4 mV | 18 × e⁻² = 2.436 mV，回弹 86.5% |
| 3τ = 135 s 残余 | 0.9 mV | 18 × e⁻³ = 0.896 mV，回弹 95.0% |
| 落底带 | ≤ 2 mV | 2τ 刚过 2 mV、3τ 已在带内，故结论取 2–3 个 τ |
| 落底耗时 | 90–135 s ≈ 1.5–2.25 分钟 | 2τ–3τ |
| 后果算例 | 真实压差 30 mV 读成 12 mV | 30 − 18 = 12，低于 15 mV 停止线 → 均衡提前停 |

纵轴是「读数偏低量 / mV」，0 在顶、20 mV 在底：曲线从 18 mV 向 0 收敛，与「偏低量逐渐消失」方向一致。横轴刻度 0 / 45 s / 90 s / 135 s 即 0–3τ。

# 帧大纲

1. 一个读数定不了结论：坐标轴立起（横轴为均衡关断后的时间，纵轴标 0、10、20 mV），红点落在 t=0、偏低 18 mV 处，旁注 `180 mA × 100 mΩ = 18 mV`。说明均衡一关就采样，读到的是带着均衡负载的电压。
2. 回弹按 τ 走：画指数收敛曲线，标出 1τ。注明 τ = R1·C1 = 45 s、1τ 只回弹 63.2%、读数仍偏低 6.6 mV——一个 τ 不够。
3. 落底要看带不看点：加 2τ、3τ 刻度与「偏低 ≤ 2 mV」的落底带。注明 2τ = 90 s 剩 2.4 mV、3τ = 135 s 剩 0.9 mV。
4. 时序结论：把 2–3 个 τ = 90–135 s ≈ 1.5–2.25 分钟标成区间，写出「关均衡 → 等 2–3 个 τ → 采样 → 判据 → 再开」，不是「关一下就采」。
5. 后果（唯一红色）：真实压差 30 mV 在关断瞬间读成 12 mV，低于 15 mV 停止线——均衡提前停，18 mV 没磨掉。红色只落在这一个结论上。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. All linework and labels in Prussian blue C-03; vermilion C-15 is reserved for the single opening measurement marker and the final frame's concluding annotation. Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

Five frames, one fixed layout: a single axis of reading-error-versus-time occupying the left two thirds, the vertical axis ticked 0, 10 and 20 millivolts with zero at the top so the curve falls toward zero, the horizontal axis ticked at zero and at one, two and three time constants. A right-hand legend column carries short hand-lettered notes. No people, no cartoon mascot, no brand logos, no photorealistic claim:

Frame 1 — the bare axis with a vermilion dot at time zero and an eighteen millivolt reading error, annotated with the balancing current times the loop resistance, stating that sampling the instant balancing stops reads the voltage under balancing load rather than the open-circuit neighbour.
Frame 2 — the exponential recovery curve is drawn, the first time constant marked, annotated that one time constant recovers only sixty-three percent and the reading is still low by six point six millivolts.
Frame 3 — the second and third time constants are marked together with a settling band at two millivolts, annotated with the residual error at each.
Frame 4 — the interval spanning two to three time constants is bracketed and lettered as roughly one and a half to two and a quarter minutes, with the ordering rule that balancing must be switched off, then waited out, then sampled, then judged.
Frame 5 — a vermilion annotation showing a true cell difference of thirty millivolts being read as twelve at the instant of switch-off, below the fifteen millivolt stop threshold, so balancing stops early and the imbalance is never worked off.
