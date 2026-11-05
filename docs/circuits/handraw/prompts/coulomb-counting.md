---
search: false
slug: coulomb-counting
style: FA-002
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: soc-drift
source_svg: docs/circuits/handraw/exports/coulomb-counting.webp
---

# 观察题

电流明明是 0 A，屏幕上的电量为什么一格一格往上爬？

# 帧大纲

1. 立场景：同一块 100 Ah 电池半满，液面停在 50%；真实电流始终 0 A（忽略自放电与静态耗电，教学假设）。
2. 误读：电流计把 0 A 读成 +0.1 A，指针偏到零刻度外一点点——这枚误读的指针用 C-03 空心圈标出，不借红色。
3. 开始积分：12 小时里积分器多记 1.2 Ah，屏幕估算从 50% 抬到 51.2%；估算线在此改用 C-03 虚线（源图的红色第二组曲线转成蓝虚线），真实电量那条线原地不动。
4. 继续积分：到 24 小时多记 2.4 Ah，估算 52.4%，两线之间裂开 2.4 个百分点，液面高度全程没变。
5. 收束：两条线并排收尾，右卡固定预告「24 h 后 52.4%」（不随动画时刻变），一句话钉住——增加的是记录，不是电。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only.

C-15 is used zero times in this figure: the source states no drift limit and marks no hazard boundary, so its red estimate curve is redrawn as a C-03 dashed line and its red misread callout as a small C-03 open ring. Vermilion stays unused rather than becoming a second series colour.

Five frames of the same cell, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim, schematic only:

Frame 1 — a 100 Ah pack, half full: a liquid-level sketch holds at 50%, real current is 0 A (teaching assumption: self-discharge and quiescent draw ignored).
Frame 2 — the ammeter misreads 0 A as +0.1 A; its needle sits just past the zero mark, circled once in C-03.
Frame 3 — integration starts: over 12 h the counter books an extra 1.2 Ah, the on-screen estimate climbs from 50% to 51.2% while the true level line does not move; the estimate is drawn as a C-03 dashed stroke.
Frame 4 — at 24 h the error reaches 2.4 Ah and the estimate reads 52.4%; the gap between the two lines opens to 2.4 percentage points, the liquid level is unchanged.
Frame 5 — closing panel: the two lines run out side by side, a fixed preview card on the right reads "24 h → 52.4%", and the verdict line states that what grew is the record, not the charge.

Numbers stay as small hand-lettered annotations, all marked 示意. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。

本图 C-15 零次：源图没有给漂移定任何限值、也没有画出危险边界，所以它的红色估算线改成 C-03 虚线，红色误读圈改成一枚 C-03 空心圈；朱砂红不用，更不当第二组曲线的颜色。

同一块电池五个帧、同一视角，无人、无卡通吉祥物、无品牌 Logo、不写实拍，纯示意：

1. 建立场景：100 Ah 电池半满，液面停在 50%；真实电流始终 0 A（忽略自放电与静态耗电的教学假设）。
2. 电流计把 0 A 误读成 +0.1 A，指针偏出零刻度一点，用一枚 C-03 空心圈标住这次误读。
3. 积分开始：12 小时多记 1.2 Ah，屏幕估算从 50% 升到 51.2%；估算线画成 C-03 虚线，真实电量那条线不动。
4. 24 小时多记 2.4 Ah，估算读到 52.4%，两线之间裂开 2.4 个百分点，液面仍是 50%。
5. 收束：两线并排，右侧固定预告卡写「24 h 后 52.4%」，结论一句：增加的是记录，不是电。

数字只用小手写标注，全部标「示意」。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] C-15 零次，并已说明源图红线属第二组曲线改画为 C-03 虚线
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 五帧同一视角；液面在 3、4 帧保持 50% 不变
- [ ] 右卡是固定预告（52.4%），不随动画时刻改写
