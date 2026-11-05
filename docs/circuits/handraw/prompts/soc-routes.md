---
search: false
slug: soc-routes
style: FA-029
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: soc-drift
source_svg: null
---

# 观察题

锚点权重从 0.3 提到 1.0，终值误差归零了——为什么中途最大误差几乎没动？

# 帧大纲

1. 版式立起：底部一条 0 pp 基线，上方三组空位；淡框 = 终值误差，实框 = 全程最大误差。
2. 基准组：权重 0.3、锚点 4 次。终值 +6.15 pp（淡框），最大 9.06 pp（实框）——攒在无锚点的 168 h。
3. 权重 1.0 组：终值 0.00 pp，最大仍 8.50 pp。权重决定终值，管不了无锚点期的累积。
4. 拆 7 天静置组：锚点 4→10 次，最大 9.06→5.07 pp，终值 +3.55 pp。
5. 收束：权重决定终值能否校准干净；锚点间隔决定中途最大误差。偏置在静置时也按时间攒。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. All linework and labels in Prussian blue C-03 only; zero use of C-15 in this figure. Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

Five frames of one grouped-bar layout, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim:

Frame 1 — the layout is ruled: a 0 pp baseline near the bottom, three empty group slots above, and a legend strip reading faint box = end-of-run error, solid box = worst error along the way.
Frame 2 — group one (baseline): weight 0.3, 4 anchors. Faint box 6.15 pp, solid box 9.06 pp, group note reads the 9.06 pp piled up in the 168 h with no anchor.
Frame 3 — group two: weight 1.0, trust OCV fully. Faint box collapses to 0.00 pp, solid box stays 8.50 pp; the note reads weight fixes the endpoint, not the drift between anchors.
Frame 4 — group three: split the 7-day rest into daily anchors, 4 to 10 anchors. Solid box falls 9.06 to 5.07 pp, faint box 3.55 pp.
Frame 5 — closing strip: weight decides whether the endpoint can be calibrated clean; anchor spacing decides the worst error along the way; bias keeps piling even at rest.

# Prompt（ZH）

手绘教学信息结构图，FA-029 Chris Ware 几何叙事风格：平直几何分栏、精确直线框架、克制冷面构图、纸纹质感。结构线与标注只用 C-03 普鲁士蓝，本图零红。数字只用小手写标注，全部标「示意」。图注：原理示意 / 非实拍。

同一套分组条形版式的五个帧、同一视角，无人、无卡通吉祥物、无品牌 Logo、纯示意：

1. 版式划好：底部一条 0 pp 基线，上方三组空位；图例一行：淡框 = 终值误差，实框 = 全程最大误差。
2. 第一组（基准）：权重 0.3、锚点 4 次。淡框 6.15 pp、实框 9.06 pp，组注：9.06 pp 攒在无锚点的 168 h。
3. 第二组：权重 1.0、完全信 OCV。淡框塌到 0.00 pp，实框仍有 8.50 pp；组注：权重治终值，治不了锚点之间的累积。
4. 第三组：把 7 天静置拆成每日一锚，锚点 4→10 次。实框 9.06→5.07 pp，淡框 3.55 pp。
5. 收束条：权重决定终值能否校准干净；锚点间隔决定中途最大误差；偏置在静置时也按时间攒。

# 验收自检

- [ ] 无人、无卡通、无实拍口吻
- [ ] 全图零红（C-15 不出现）
- [ ] 三组条形不越 960 画布、不与组注/结论行重叠
- [ ] 数字与表 12-5/12-6 及「动手」实验块一致：6.15 / 9.06 / 0.00 / 8.50 / 3.55 / 5.07 pp
