---
slug: overcharge-protection
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: overcharge-chain
source_svg: docs/circuits/assets/overcharge-protection.svg
---

# 观察题

电压已经越过 4.30 V 的那一瞬间，充电 MOS 为什么没有立刻断开——盯着比较器后面那段内部延时，看「确认」比「检测」慢了多少。

# 帧大纲

1. 充电进行中：充电器 → 充电 MOS → 电芯 的通路闭合，OC = 高（允许充电），读数 3.60 V，电压曲线还在 4.20–4.40 V 的图表窗口之外。
2. 逼近阈值：电压以每秒 +50 mV 爬升（示意），曲线从 4.20 V 出发走到 4.25 V；比较器看着，但还不翻。
3. 2.0 s 越线：曲线穿过 4.30 V 过充阈值（唯一一处 C-15 短线），比较器翻转；可它先落进内部延时窗口——确认还没走完，MOS 纹丝不动。
4. 延时确认 → 硬关断：DW01 拉低 OC 脚，OC = 低，充电 MOS 断开，通路上出现断口、电流归零，电压停在 4.35 V 的越线峰值。
5. 回落恢复：电压被带回 3.90 V，OC 回高，MOS 重新闭合，自动重新允许充电——关断不是一次性熔断。
6. 收束：三要素面板——阈值（4.30 V）＋ 延时（内部产生，防误触发）＋ 恢复条件（电压回落）；横轴 0 / 2.0 / 4 s 与纵轴 4.20 / 4.30 / 4.40 V 同框。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 appears exactly once, as a short dashed line for the overcharge threshold with its small tick at the 4.35 V overshoot — never as a fill, never as a second series colour (the safe band is a C-03 hairline, not green). No people, no cartoon mascot, no brand logos, no photorealistic claim. Schematic only.

Six frames of the same charger–MOS–cell circuit plus the same small voltage-versus-time panel, same viewpoint, no camera move:

Frame 1 — charging: charger → charge MOS → cell path closed, comparator output OC = 高 (允许充电), cell reading 3.60 V, and the trace still outside the 4.20–4.40 V plot window.
Frame 2 — approaching threshold: voltage climbs at +50 mV per second (illustrative), the trace moves from 4.20 V to 4.25 V; the comparator is watching but has not flipped.
Frame 3 — crossing at 2.0 s: the trace passes the 4.30 V overcharge threshold (the single C-15 dashed mark); the comparator flips, but it now enters an internal delay window — confirmation is still pending and the MOS has not moved.
Frame 4 — delay confirmed, hard cutoff: DW01 pulls OC low, OC = 低 (关断), the charge MOS opens, the path shows a gap with current at zero, and the reading settles at 4.35 V, the overshoot peak.
Frame 5 — recovery: voltage falls back to 3.90 V, OC returns high, the MOS closes again and charging is permitted once more — the cutoff is not a one-shot fuse.
Frame 6 — closing panel: three protection elements laid out as columns — 阈值 (4.30 V) + 延时 (internally generated, prevents false trips) + 恢复条件 (voltage falls back); axes 0 / 2.0 / 4 s and 4.20 / 4.30 / 4.40 V framed together.

Every voltage stays as small hand-lettered annotation marked 示意; the +50 mV/s rate is illustrative and the 2.0 s crossing is quoted, not derived. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红全图只出现一处：过充阈值那一小段朱砂虚线，附 4.35 V 越线处的一个小记号；不铺面，也不当第二组曲线的颜色（安全区间用 C-03 极细线，不用绿色）。无人、无卡通吉祥物、无品牌 Logo、不写实拍，纯示意。

同一套 充电器–MOS–电芯 电路加同一块小电压-时间面板，六个帧、同一视角、不移动镜头：

1. 充电中：充电器 → 充电 MOS → 电芯 通路闭合，比较器输出 OC = 高（允许充电），电芯读数 3.60 V，曲线还在 4.20–4.40 V 的窗口外。
2. 逼近阈值：电压以每秒 +50 mV 爬升（示意），曲线从 4.20 V 走到 4.25 V；比较器在看，还没翻。
3. 2.0 s 越线：曲线穿过 4.30 V 过充阈值（唯一一处 C-15 虚线），比较器翻转，但随即进入内部延时窗口——确认未完成，MOS 没动。
4. 延时确认 → 硬关断：DW01 拉低 OC 脚，OC = 低（关断），充电 MOS 断开，通路上留出断口、电流归零，读数停在 4.35 V 的越线峰值。
5. 回落恢复：电压回落到 3.90 V，OC 回高，MOS 重新闭合，重新允许充电——关断不是一次性熔断。
6. 收束：三要素分三栏排开——阈值（4.30 V）＋ 延时（内部产生，防误触发）＋ 恢复条件（电压回落）；横轴 0 / 2.0 / 4 s 与纵轴 4.20 / 4.30 / 4.40 V 同框。

电压值一律小手写并标「示意」；+50 mV/s 是示意速率，2.0 s 越线点照抄源图，不反推。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 危险仅 C-15，且只有一处（4.30 V 阈值线及其越线记号）
- [ ] 安全区间不用第三色（不引入绿色/红色二元语义）
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 阈值 4.30 V、越线峰值 4.35 V、恢复 3.90 V、2.0 s 与源图逐字一致
