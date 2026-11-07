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

1. 全程预览：按真实比例绘制8/3/1/0.2 ms四段轮廓；右侧四行账栏同时可读，当前落账0 ms。首帧不是无字空尺。
2. 采样落账：第一段加深，当前8 ms；账栏标明本段与累计。
3. 估算落账：第二段加深，当前11 ms。
4. 判决落账：第三段加深，当前12 ms。硬件比较器始终放独立框，不接在软件判决之后，不入累加。
5. 执行落账：细小的0.2 ms段按比例保留；数值在账栏读，当前12.2 ms。
6. 全账：四段同框、当前12.2 ms；底注全部为教学预算，不是某颗MCU实测；硬件比较器→驱动/切断单独核验。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 stays unused in this figure — the source marks no hazard, so nothing is red; the hardware-comparator branch is told apart by being detached and hairline, not by colour. No people, no cartoon mascot, no brand logos, no photorealistic claim. Schematic only.

Six frames of the same cumulative accounting ruler, same framing, no camera move:

Frame 1 is a readable overview: an unfilled proportional ruler and four ledger rows already identify sampling 8 ms, estimation 3 ms, decision 1 ms and actuation 0.2 ms. Frames 2–5 progressively book those amounts, reaching 8, 11, 12 and 12.2 ms; frame 6 presents the complete account. Keep the narrow actuation segment proportional, but place its label in the ledger rather than squeezing text onto the segment. A detached hardware-comparator-to-cutoff lane never enters the software sum and carries no invented response-time number. Use the established restrained paper grain, title hierarchy and margins.

Every value is hand-lettered and marked 示意 where the source marks it; the hardware-comparator branch never enters the sum. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学信息结构图，FA-029 Chris Ware 几何叙事风格：平面几何面板、精确直尺分栏、克制的冷面构图、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红在本图完全不用——源图没有危险标记，所以画面不出现红色；硬件比较器那条支路靠「脱开 + 极细线」与主尺区分，不靠颜色。无人、无卡通吉祥物、无品牌 Logo、不写实拍，纯示意。

同一条累加账尺，六个帧、同一构图、不移动镜头：

首帧把四笔账读清，后续逐笔落账到8/11/12/12.2 ms；主尺长度按时间比例，右侧账栏分清本段与累计，0.2 ms执行段不放大造假也不挤标签。硬件比较器→驱动/切断画在下方独立框，既不接在软件判决之后，也不计入12.2 ms；不编造硬件响应时间。纸纹、标题、正文和留白沿用前轮精修层级。

每个数字都是小手写，按源图标「示意」；硬件比较器支线始终不入总和。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 全图无危险点：C-15 保留不用，支线靠脱开与细线区分
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 四段时长与三处累计（11 / 12 / 12.2）与源图一致，未增未改
- [ ] 首末帧单独成图仍可读：首帧四笔账预览与末帧全账各自成义
