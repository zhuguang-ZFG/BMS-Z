---
search: false
slug: cell-inconsistency-barrel
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: weakest-cell
source_svg: docs/circuits/assets/archive/cell-inconsistency-barrel.svg
---

# 观察题

四节串在一条回路上，为什么每次先停下的都是同一节？盯住 3 号那块桶板的水位线，看整包还剩多少安时却再也放不出来。

# 帧大纲

1. 四块桶板并排立起：1 号 / 2 号 / 4 号各 50 Ah，3 号只有 35 Ah；每节各画一条满充线，3 号那条明显更低，标「满充线（容量小）」。旁注：木桶是示意，不是某一包的配组记录。
2. 充电开始：串联电流相同，四节以同样速度「进水」，水位一起上涨；3 号先顶到自己的满充线，另外三节头顶还空着一截。
3. 停充：3 号先满 → BMS 必须停充，其他三节只能充到七成；那三截空着的头顶被标成「用不上」。
4. 放电：水位一起下降，3 号容量小、内阻大，端电压先跌破截止线——2.55 V，另外三节约 3.1 V——整组停放。全图唯一一处 C-15 就点在这下「跌破」上。
5. 底栏算账：可用 Ah 的柱停在 35，旁边一根柱标着另外三节的 50；图上的 35 Ah 把整包锁在 35，不是 50。
6. 恶性循环收束：最弱那节每次都工作在最极限的区间，老化更快，差距越拉越大；四块板重新量一遍，最短板又短了一点。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour, generous white space, deadpan textbook tone, paper grain. Primary linework and labels in Prussian blue C-03 only. Vermilion C-15 appears exactly once, as a single small tick at the instant the weakest cell's terminal voltage breaks the discharge cutoff — never as a fill, never as a second series colour. The four full-charge head lines are C-03 dashed, not red: they are geometry, not danger.

Six frames of the same four-stave barrel, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim, schematic only:

Frame 1 — four staves stand side by side: cells 1, 2 and 4 hold 50 Ah, cell 3 only 35 Ah; each has its own full-charge line and cell 3's sits visibly lower, labelled full-charge line, small capacity. Margin note: the barrel is a schematic, not one pack's matching record.
Frame 2 — charging begins: identical series current enters all four at the same rate, the four levels rise together; cell 3 touches its own full-charge line first while the other three still have empty headroom.
Frame 3 — charging must stop because cell 3 is full; the other three can only reach seventy percent, and their empty headroom is labelled unused.
Frame 4 — discharge: the levels fall together, but cell 3's smaller capacity and higher internal resistance drive its terminal voltage through the cutoff first — 2.55 V against about 3.1 V on the other three — and the whole string stops. The single C-15 tick sits on this crossing.
Frame 5 — closing ledger: an available-Ah bar stops at 35 while a neighbouring bar stands for the other three at 50; the note says the 35 Ah figure locks the pack at 35, not 50.
Frame 6 — feedback loop: the weakest cell always works in the most extreme interval, ages faster, and the gap widens again; the staves are re-measured and the shortest one is shorter still.

Numbers stay as small hand-lettered annotations; all values marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一笔不断的墨线、大片留白、冷面教科书语气、纸纹质感。结构线与标注只用 C-03 普鲁士蓝。C-15 朱砂红全图只出现一次，点在最弱那节端电压跌破放电截止线的那一瞬；不铺面、不当第二组颜色。四条满充线一律画成 C-03 虚线——它们是几何，不是危险。

同一个木桶、同一视角的六个帧，无人、无卡通吉祥物、无品牌 Logo、不写实拍，纯示意：

1. 四块桶板并排：1 号 / 2 号 / 4 号各 50 Ah，3 号 35 Ah；每节一条满充线，3 号那条更低，标「满充线（容量小）」。
2. 充电开始：串联电流相同，四节同样速度「进水」，水位齐涨；3 号先顶到自己的满充线，另外三节头顶还空着。
3. 3 号先满 → BMS 必须停充，其他三节只能充到七成；空着的头顶标「用不上」。
4. 放电：水位一起下降，3 号容量小、内阻大，端电压先跌破截止线（2.55 V，其余约 3.1 V）→ 整组停放。唯一 C-15 点在这一下。
5. 底栏算账：可用 Ah 柱停在 35，旁边一根 50 的柱是另外三节；35 Ah 把整包锁在 35，不是 50。
6. 恶性循环：最弱那节总在最极限的区间工作，老化更快，差距越拉越大；重新量板，最短板又短了一点。

数字只用小手写标注，全部标「示意」。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 危险仅 C-15，且只有一处（3 号跌破截止线那一点）
- [ ] 四条满充线是 C-03 虚线，不是红色
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一视角，可暂停阅读
- [ ] 数字只用源图的 50 / 35 Ah、2.55 V、约 3.1 V、七成，且全部标示意
- [ ] 首末帧单独成图仍可读
