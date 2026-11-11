# Task 8 试片复核（ch8 / ch0 / ch17）

三章试片按 `docs/superpowers/plans/2026-11-04-visual-first-book-overhaul.md` 第 272 行的字符预算执行：
每章以自身基线降 10%。ch8、ch0、ch17 正文与图已落盘；人工评分仍待用户审图。

## ch8 模拟开关与多路复用

基线 38,745 字，目标 ≤34,870（下降 10%）；复核时正文 **34,309 字**，净减 4,436 字（11.4%）。

- `python scripts/audit_visual_density.py --gate --chapter 8` → **PASS（0 项）**
- 实测：`字符=34309 视觉=32/32 最长无图段=1470 警告=8 堆图=0 H2无图=0`
- 分型：`figures 26 / photos 1 / svg 5`
- 8 段 >1200 字预警全部 <1500，未触硬闸；章尾 1244 字，仍留参考与出处

本轮新增 20 张纸层静态图，并把 4 个旧模板动画替换为 V2：

| 动画 | 类型 | anchor | 节拍 |
|---|---|---|---|
| `ch08-transfer-gate-v2` | A1 机理 | 8.1 | 低电平 N 管 → 中段 P 管接管 → 20/26.7/20Ω 包络 |
| `ch08-mux-address-glitch-v2` | A4 失效边界 | 8.2 | 011→100 途经 111 → INH 罩住跳变 → 采样窗错开 |
| `ch08-charge-injection-v2` | A4 失效边界 | 8.6 | Qch=0.2pC 分两路 → 10mV → 20 LSB |
| `ch08-sample-hold-v2` | A1 机理 | 8.4 | 采样 → 保持 → droop → 再采样 |

20 张静态图全部经 `build_papercut_pilot.py --render` 验证 `bounds: pass`，
最小印刷字号 8.6449pt；48 项纸层/清单/保真/动画测试通过。

原 128→139 的 311 字堆图（mux 动画紧挨结构图）由一段 INH 地址时序补齐到 400 字以上，
`堆图 0`；`ch08.yml` 的 measured 与 `plan_verified` 已按实跑结果更新。

`contact-ch8.html` 收录 24 个 manifest 资产（20 张静态图 + 4 个 V2 动画）；
正文另有 5 个旧 SVG/图锚点与 1 张面包板照片。**ch8 人工评分同样为空**，
视觉模型通道 503，未把任何图标记为 `accepted`。

## ch0 电路直觉学前班

基线 19,284 字，目标 ≤17,355（下降 10%）；复核时正文 **17,353 字**，净减 1,931 字（10.0%）。

- `python scripts/audit_visual_density.py --gate --chapter 0` → **PASS（0 项）**
- 实测：`字符=17353 视觉=18/18 最长无图段=1177 警告=0 堆图=0 H2无图=0`
- 分型：`figures 12 / photos 1 / svg 5`
- 19 段无图区间全部 <1200；章尾（表 0-6 ＋ 参考与出处 ＋ 打卡）1177，未再靠插图凑数

本轮新增 10 张纸层静态图与 4 个 V2 动画（视觉总数仍 18）：2 个既有 V2 动画保留，另把 `divider-loading.svg`、`source-types.svg` 两张旧静态图升级为 V2 动画。

| 图 | texts | 最小印刷字号 | bounds |
|---|---:|---:|---|
| ground-is-copper | 23 | 8.6449pt | pass |
| engineering-notation-ladder | 24 | 8.6449pt | pass |
| dimension-check-both-ways | 31 | 8.6449pt | pass |
| conversion-four-steps | 15 | 8.6449pt | pass |
| gain-is-three-factors | 17 | 8.6449pt | pass |
| example-0-2-worked | 23 | 8.6449pt | pass |
| three-power-formulas | 23 | 8.6449pt | pass |
| derating-125mw | 23 | 8.6449pt | pass |
| ten-myth-signatures | 25 | 8.6449pt | pass |
| next-chapter-parasites | 23 | 8.6449pt | pass |

原 0.1 的色环电阻照片移到章尾「通关打卡」之后，作为实物回调；0.1 开头 166 字的堆图消除。
`contact-ch0.html` 收录 14 个 manifest 资产（10 张静态图 + 4 个 V2 动画），正文另有 3 个旧 SVG/图锚点与 1 张实物照片。4 个动画的 prompt 均已改为「Task 8 正文试片锚点，正式印刷前待风格复评」，不再声明「不进入正文」。
图内数字逐项来自 anchor 原文；转换示例用 `0.0005 A→0.5 mA`，不再引入正文没有的 4700 Ω。

`check_visual_manifest.py` → PASS（0 项）；纸层/清单/保真/动画测试 48 项通过。
**ch0 人工评分同样为空**：视觉模型通道仍为 503，未把任何图标记为 `accepted`。

## ch17 六类故障排查

本章按同一计划行执行：以 24,741 为基线，目标 ≤22,267（下降 10%）。复核时正文为 22,266 字，
净减 2,475 字（10.0%）。

## 复核范围

`contact-ch17.html` 收录 manifest 中 20 个 ch17 图资产（18 张静态图 + 2 个已登记动画条目），
另有 4 个 V2 动画与 1 张实物照片直接嵌在正文，审计合计 24 个视觉锚点。

本轮新增 7 张纸层静态图：

- `ch17-power-fault-layers`（17.1，两栏：电源自身 / 系统交界）
- `ch17-noise-floor-before-verdict`（17.2，仪器底噪与电路漂移）
- `ch17-probe-changes-the-circuit`（17.4，四象限“测量依赖型正常”）
- `ch17-thermal-cycling-vs-dissipation`（17.5，热循环与耗散对照）
- `ch17-intermittent-fault-forcing`（17.6，五步逼迫流程）
- `ch17-first-power-on-static-check`（17.7，五步静态检查）
- `ch17-triage-tree-three-tradeoffs`（17.8，三个设计取舍）

## 正文与闸具

- `python scripts/audit_visual_density.py --gate --chapter 17` → **PASS（0 项）**
- 实测：`字符=22266 视觉=24/18 最长无图段=1452 警告=3 堆图=0 H2无图=0`
- 分型：`figures 18 / photos 1 / svg 5`
- 三个 >1200 字预警段：1452（17.2→I²C）、1318（17.3→振荡顺序）、1211（17.5→热链）
- 表 17-2 / 17-3 / 17-4 / 17-6 / 17-8 均采用“续表 + 图”拆开，未删表行、公式或失效边界

## 机器验证与人工评分

7 张新图均通过 `build_papercut_pilot.py` 的几何与字号检查：

| 图 | texts | 最小印刷字号 | bounds |
|---|---:|---:|---|
| power-fault-layers | 31 | 8.6449pt | pass |
| noise-floor-before-verdict | 31 | 8.6449pt | pass |
| probe-changes-the-circuit | 17 | 8.6449pt | pass |
| thermal-cycling-vs-dissipation | 31 | 8.6449pt | pass |
| intermittent-fault-forcing | 18 | 8.6449pt | pass |
| first-power-on-static-check | 18 | 8.6449pt | pass |
| triage-tree-three-tradeoffs | 12 | 8.6449pt | pass |

`check_visual_manifest.py` → PASS（0 项）；纸层/清单/保真/动画测试 48 项通过。

**人工视觉评分仍为空。** 视觉模型审图通道返回
`503 No available channel for model dots-3-note-prev ... model_not_found`，
本轮无法取得 35 分量规分数，也未把任何新图标成 `accepted`。
上表只是机器可验证的字号与边界结果，不等于用户已确认风格或印刷验收。

## 用户签核（2026-11-05 晚）

用户在确认 43 张 contact sheet（ch0 10 / ch8 20 / ch17 13）后，
选择「全部 5 分通过」。已把 43 张 figure 的 5 项评分全部回填 5，
`status_history` 迁移至 `accepted`，`review_record.reviewer = zhuguang-ZFG`，
`asset_sha256` 与磁盘 SVG（LF 归一）一致：
`check_visual_manifest.py` → PASS；`test_papercut_figures` 4 项含哈希校验全过。
机器字号/边界预检不替代此项确认，评分来源是用户人工签核。

## 可复现

```bash
for n in 8 0 17; do python scripts/audit_visual_density.py --gate --chapter $n; done
python scripts/check_visual_manifest.py
python scripts/check_visual_manifest.py --write-animation-index
python scripts/build_visual_contact_sheet.py --wave ch08 \
  --out docs/superpowers/visual/reviews/task8-2026-11-05/contact-ch8.html --page-size 24
python scripts/build_visual_contact_sheet.py --wave ch00 \
  --out docs/superpowers/visual/reviews/task8-2026-11-05/contact-ch0.html --page-size 24
python scripts/build_visual_contact_sheet.py --wave ch17 \
  --out docs/superpowers/visual/reviews/task8-2026-11-05/contact-ch17.html --page-size 24
python -m pytest scripts/test_papercut_figures.py scripts/test_visual_manifest.py \
  scripts/test_visual_fidelity.py scripts/test_animation_v2.py -q
```
