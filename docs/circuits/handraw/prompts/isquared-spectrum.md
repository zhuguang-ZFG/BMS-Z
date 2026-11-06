---
search: false
slug: isquared-spectrum
style: FA-029
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: sop-minimum
source_svg: null
---

# 观察题

同样是周期电流，为什么有的波形让温度出现 2ω 纹波，有的只收敛到恒温升？——温度跟的是生热，生热跟的是 I²，而平方是非线性的。

# 帧大纲

1. 版式立起：左边时域画电流 I(t)（零线 + 时间轴），右边画 I² 的频率成分（基线 + DC/ω/2ω/3ω 刻度），先只放一条正弦，谱线不出。
2. 正弦 I=A sinωt：I² = A²/2 − A²cos2ωt/2，右边两根——直流 A²/2 与 2ω A²/2。「翻倍」的直觉只来自这一行。
3. 对称双极方波 I=±A：I² 恒为 A²，右边只剩一根直流，纹波整项消失；忽略切换与熵热时只向恒温升收敛。
4. 0/A 开关：I² 就是原周期的开关功率，原频率 ω 还在（50% 占空时为奇次，DC/ω/3ω…），不是翻倍；高次谐波经热低通后才被削平。
5. 带偏置的正弦 I=I0+A sinωt：直流、ω 和 2ω 三根同时存在，偏置导致的 ω 分量不能漏算。表 14-1 四行此时全部列齐。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. All linework and labels in Prussian blue C-03 only; zero use of C-15 in this figure. Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

Five frames, one fixed two-panel layout (left: current waveform in time; right: frequency content of I²), plus a four-row comparison table that fills in row by row. No people, no cartoon mascot, no brand logos, no photorealistic claim:

Frame 1 — layout only: left panel has a zero line and a time axis; right panel has a baseline with DC / ω / 2ω / 3ω ticks; a single sine wave is drawn on the left, no spectral stems yet.
Frame 2 — I=A sinωt: I² = A²/2 − A²cos2ωt/2; two stems on the right, DC at A²/2 and 2ω at A²/2. Table row 1 appears.
Frame 3 — symmetric bipolar square wave I=±A: I² is a constant A²; only one DC stem remains, the ripple term vanishes entirely. Table row 2 appears.
Frame 4 — switching between 0 and A: I² is the switching power at the original period; the original frequency is still there (odd harmonics at 50% duty: DC / ω / 3ω…), not doubled; higher harmonics are flattened only by the thermal low-pass. Table row 3 appears.
Frame 5 — I=I0+A sinωt: DC, ω and 2ω stems all present at once; the ω component caused by the bias must not be dropped. Table row 4 and the closing line appear.

# Prompt（ZH）

手绘教学信息结构图，FA-029 Chris Ware 几何叙事风格：平直几何分栏、精确直线框架、克制冷面构图、纸纹质感。结构线与标注只用 C-03 普鲁士蓝，本图零红。数字只用小手写标注，全部标「示意」。图注：原理示意 / 非实拍。

固定双面板版式（左：电流时域波形；右：I² 的频率成分）的五个帧，下方四行对照逐帧填入。无人、无卡通吉祥物、无品牌 Logo、纯示意：

1. 只立版式：左面板零线 + 时间轴，右面板基线 + DC / ω / 2ω / 3ω 刻度；左边先画一条正弦，右边不出谱线。
2. I=A sinωt：I² = A²/2 − A²cos2ωt/2；右边两根——直流 A²/2 与 2ω A²/2。表格第一行出现。
3. 对称双极方波 I=±A：I² 恒为 A²，右边只剩一根直流，纹波整项消失。表格第二行出现。
4. I 在 0 与 A 间切换：I² 是原周期的开关功率；原频率还在（50% 占空为奇次：DC / ω / 3ω…），不是翻倍；高次谐波经热低通后才被削平。表格第三行出现。
5. I=I0+A sinωt：直流、ω 和 2ω 三根同时存在，偏置导致的 ω 分量不能漏算。表格第四行与结论句出现。

# 验收自检

- [ ] 无人、无卡通、无实拍口吻
- [ ] 全图零红（C-15 不出现）
- [ ] 四行表格文字与表 14-1 逐字一致（含「忽略切换与熵热时，只向恒温升收敛」「原频率及高次谐波经热低通」）
- [ ] 50% 占空的 0/A 方波不画 2ω（I²=A²·s(t) 只有直流 + 奇次谐波）
- [ ] 带偏置的正弦全程为正（I0 > A），虚线标出 I0
- [ ] 谱线 stem 高度一律 <60 px（几何门把 ≥60 px 的竖线当规则线，不得压字）
