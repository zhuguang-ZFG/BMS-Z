---
search: false
slug: bms-signal-budget
style: FA-029
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: three-probes
source_svg: docs/circuits/assets/archive/bms-signal-budget.svg
---

# 观察题

一拍数据从电芯走到开关要 12.2 ms，盯着累加尺一段一段被填：最肥的那一段落在哪一站，最细的那一段又是什么。

# 帧大纲

1. 空尺：一条从 0 起步的累加尺画出来，四个站刻度（采样完 / 估算完 / 判决完 / 执行完）先立成空位，尺上还没有任何长度。
2. 采样落账：8 ms 那一节落到尺头，明显最肥；旁注「电压电流还在滤波器里」，游标停在 8。
3. 估算叠加：+3 ms 接在采样后面，右侧出现「累计 11 ms」；旁注「SOC 算完才知道该不该限功率」。
4. 判决叠加：+1 ms，累计刻度走到 12；尺外分出一条脱开的细支线——比较器那条硬件路不在这 1 ms 里，它不参与累加。
5. 执行叠加：+0.2 ms，累计 12.2；MOS 那一节细成一根发丝，和采样那节并置时几乎看不见。
6. 总账：8 + 3 + 1 + 0.2 四段同框、四段各自标名，尺下注「8 ms、3 ms、1 ms、0.2 ms 是教学预算，不是某一颗 MCU 的手册」，硬件比较器支线仍悬在尺外。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 stays unused in this figure — the source marks no hazard, so nothing is red; the hardware-comparator branch is told apart by being detached and hairline, not by colour. No people, no cartoon mascot, no brand logos, no photorealistic claim. Schematic only.

Six frames of the same cumulative accounting ruler, same framing, no camera move:

Frame 1 — empty ruler: one ruled bar starting at 0, four station ticks (采样完 / 估算完 / 判决完 / 执行完) standing as empty slots, no length drawn yet, a small cursor at the left end.
Frame 2 — sampling drops in: the 8 ms block lands at the head of the ruler and is plainly the fattest; a note reads 电压电流还在滤波器里; the cursor sits at 8.
Frame 3 — estimation stacks: +3 ms attaches behind sampling, the cumulative label 累计 11 ms appears at the right edge; a note reads SOC 算完才知道该不该限功率.
Frame 4 — decision stacks: +1 ms pushes the cumulative mark to 12; outside the ruler a detached hairline branch forks away — 比较器那条硬件路不在这 1 ms 里 — explicitly not part of the accumulation.
Frame 5 — actuation stacks: +0.2 ms brings the total to 12.2; the MOS segment is a hairline sliver, almost invisible beside the sampling block.
Frame 6 — the whole account: 8 / 3 / 1 / 0.2 as four labelled segments in one bar, cumulative marks at 8, 11, 12, 12.2, ruler ticks labelled 0, 8 and 12 as the source prints them, and a footnote strip beneath: 8 ms、3 ms、1 ms、0.2 ms 是教学预算，不是某一颗 MCU 的手册.

Every value is hand-lettered and marked 示意 where the source marks it; the hardware-comparator branch never enters the sum. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学信息结构图，FA-029 Chris Ware 几何叙事风格：平面几何面板、精确直尺分栏、克制的冷面构图、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红在本图完全不用——源图没有危险标记，所以画面不出现红色；硬件比较器那条支路靠「脱开 + 极细线」与主尺区分，不靠颜色。无人、无卡通吉祥物、无品牌 Logo、不写实拍，纯示意。

同一条累加账尺，六个帧、同一构图、不移动镜头：

1. 空尺：一条从 0 起步的直尺式累加条，四个站刻度（采样完 / 估算完 / 判决完 / 执行完）先立成空位，尺上还没画出任何长度，左端一个小游标。
2. 采样落账：8 ms 那块落到尺头，显然最肥；旁注「电压电流还在滤波器里」，游标停在 8。
3. 估算叠加：+3 ms 接在采样后面，右端浮出「累计 11 ms」；旁注「SOC 算完才知道该不该限功率」。
4. 判决叠加：+1 ms 把累计刻度推到 12；尺外分出一条脱开的极细支线——比较器那条硬件路不在这 1 ms 里，明确不计入累加。
5. 执行叠加：+0.2 ms 把总数带到 12.2；MOS 那一节只是一根发丝，摆在采样那块旁边几乎看不见。
6. 总账：8 / 3 / 1 / 0.2 四段各自标名、同框并列，累计刻度落 8、11、12、12.2，尺上刻度按源图写 0、8、12；尺下一条脚注：「8 ms、3 ms、1 ms、0.2 ms 是教学预算，不是某一颗 MCU 的手册」。

每个数字都是小手写，按源图标「示意」；硬件比较器支线始终不入总和。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 全图无危险点：C-15 保留不用，支线靠脱开与细线区分
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 四段时长与三处累计（11 / 12 / 12.2）与源图一致，未增未改
- [ ] 首末帧单独成图仍可读：空尺与总账各自成义
