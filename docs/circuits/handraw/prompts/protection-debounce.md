---
search: false
slug: protection-debounce
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: protection-debounce
source_svg: docs/circuits/assets/archive/protection-debounce.svg
---

# 观察题

电压第一次冲过 4.25 V 时为什么什么都没发生？盯住那条去抖计时条——它清零的那一下，和走满的那一下，差在哪里。

# 帧大纲

1. 正常：绘到10 ms，电压在恢复线以下；计时0，开关导通。阈值4.25 V、恢复4.15 V、窗口20 ms均标示意。
2. 毛刺回落：11–16 ms短暂越限，画到16.5 ms时已经回落；**当前计时必须为0**，不能把此前5 ms残留在计时条里，开关不动作。
3. 持续超限：20 ms再次越限，画到34 ms；已累计14/20 ms，仍导通，不能字幕先称走满。
4. 动作边界：画到40 ms，累计20/20 ms且开关断开；全图唯一C-15短线标此时刻。
5. 回差保持：画到46 ms，电压4.20 V在两条线之间；计时0但开关仍断开。
6. 恢复：48 ms电压降到4.12 V，画到50 ms已导通；明确这里只画可恢复型示例，锁存型还须另验清除条件，不按故障名称泛化所有产品策略。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 appears exactly once, as a single small tick at the instant the debounce timer fills and the switch opens — never as a fill, never as a second series colour. The threshold and release lines are C-03 dashed; they are the limit geometry, not the danger itself.

Six frames of the same voltage-versus-time panel, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim, schematic only:

Frame 1 is normal at 10 ms. Frame 2 is observed after the 11–16 ms spike has fallen: the live timer must be zero and the switch closed. Frame 3 is at 34 ms, fourteen milliseconds after renewed over-limit at 20 ms, so the switch is still closed. Frame 4 is exactly at the 40 ms trip boundary: twenty milliseconds confirmed, switch open, one small vermilion tick. Frame 5 is at 46 ms inside the hysteresis band: zero timer does not imply a closed switch. Frame 6 is below the release threshold and recovered. Derive waveform, elapsed timer and switch state from the same event sequence. This is an illustrative recoverable policy, not a universal policy for every short circuit or overtemperature fault.

Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红全图只出现一次，点去抖计时走满、开关断开的那一瞬；不铺面、不当第二组颜色。阈值线与恢复线都是 C-03 虚线——它们是限值的几何，不是危险本身。

同一块「电压对时间」画面的六个帧、同一视角，无人、无卡通吉祥物、无品牌 Logo、不写实拍，纯示意：

六帧的观察时刻依次为10、16.5、34、40、46、50 ms；波形、计时条、开关共用同一事件序列推导。第2帧是毛刺已回落后的**0/20 ms**，第3帧为**14/20 ms尚未动作**，第4帧**20/20 ms断开**，第5帧**0/20 ms仍断开**，第6帧过恢复线后导通。明确标注可恢复型教学示例；锁存策略须另定义，不能凭「短路/过温」名称断言产品都要人工清除。图内仅第4帧的确认动作短线使用朱红。

数字只用小手写标注，全部标「示意」。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 危险仅 C-15，且只有一处（计时走满、开关断开的那一刻）
- [ ] 阈值线与恢复线是 C-03 虚线，不是红色
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一视角，计时条状态与波形严格对应，可暂停阅读
- [ ] 数字只用源图的 4.25 V / 4.15 V / 20 ms，且全部标示意
- [ ] 首末帧单独成图仍可读
