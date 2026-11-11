# Wave 18 视觉复核包（3 张，待人工审图）

本包 3 张全部 `status: generated`，`review_scores` 为空，未插入正文；没有伪造人工签核。

**这轮不是按数字密度选，是按「0 图井真的干了」选。** 全库 `###` 节里，既没有 manifest 图、
数字又 ≥110 的只剩 5 个：`§10.3`、`§10.1`、`§11.6`、`§2.11`、`§3.9`。
其中 `§11.6` 的噪声四税已被 Wave 15 的 `ch11-noise-three-taxes` 覆盖，`§2.11` 的 ESD 数值账
已被 Wave 13 的 `ch02-esd-chain` 覆盖，两张都因「同一教学点不重复加图」剔除。
剩下三节各做一张。

| 图 | anchor | 节内数字 | 现有资产 | 选它的理由 |
|---|---|---|---|---|
| `ch10-555-fault-tree` | §10.3 | 249 | `assets/svg/ne555-params.svg`（老动画） | 全库最密的未覆盖小节；五条故障各自对应一条回路，本来就是决策树 |
| `ch10-555-threshold-clamp` | §10.1 | 197 | `assets/svg/ne555-astable.svg`（老动画） | 门限夹持只有 ASCII 块图在讲，两张门限的上下限位没有静态图 |
| `ch03-ce-swing-budget` | §3.9 | 127 | `assets/svg/ce-dynamic.svg`（老动画） | 6 V / 4 V 两份余量与 8.0 Vpp 是本节最硬的一笔算，动画扫一眼看不出来 |

**为什么只做 3 张**：再往下 `§10.5`、`§18.4` 已有 2 张 manifest 图，`§6.2` 有两张（照片 + 动画），
按「已有图覆盖同一教学点不再加」的口径都不选。宁少不重复。

## 怎么看

1. 打开 [`contact-wave18.html`](contact-wave18.html)，逐张看大图。
   也可在 GitHub 直接看 [`WAVE18-GALLERY.md`](WAVE18-GALLERY.md)。
2. 按五项各打 1–5 分：教学必要性、事实精度、构图层级、风格一致性、印刷可读性。
3. 任一维度 <4 记具体返工点；5 分才可写 `accepted`。
4. 回复「第 X 张：5/5/5/5/5」或「全部 5 分通过」即可回填；模型不会代签。

## 优先看

1. **`ch10-555-fault-tree`**：五行「现象 → 判据」是本包的主图。若觉得判据列写得太长、
   在 138 mm 版面上会挤，这是首要返工点——可以砍到每行一句。
2. **`ch03-ce-swing-budget`**：左右两个余量数与 8.0 Vpp 的推导关系是否一眼看出。
3. **`ch10-555-threshold-clamp`**：此图刻意不画电路，只画两条门限的动作与占空比的来历；
   若认为缺电路图，需要和 `ne555-astable.svg` 的分工重新划。

## 已过的闸

- `check_visual_manifest.py` → **PASS（0 项）**；manifest 401 → 404 项，accepted 仍 46 张。
- 版面三级：`audit_visual_geometry.py`（全库 361 张，仅既存 `svg/opamp-slew` 出画布，范围外）→
  `.tmp/measure_svg.py`（5/5 → 3/3 clean：出画布 0、后盖前 0、互压 0）→
  `.tmp/probe_lines_edges.py`（`<line>` 穿字 0；面板内贴边只剩 1 处 6.4 px，属全库版面风格）。
- 16K/138mm：3 张 `min_print_pt = 8.605984251968504`，`bounds: pass`，print 变体齐全。
- 字形：`font_gate` 6 个变体（3 图 × 正文/print）全覆盖。
- 数字溯源：图内数字 ⊆ anchor 正文 **3/3**；alt 数字 ⊆ 图内数字 **3/3**。
- 视觉测试 6 文件 **65 项全通过**。

## 本轮修掉的二处

1. `ch10-555-threshold-clamp` 两块面板底下各留了一条没有内容的横线 → 删掉（右下角空白装饰线）。
2. 同一张图的「要更小的占空比，得给放电另开一条路」超出 anchor 原文（正文只给
   `占空比 = (R1+R2)/(R1+2R2) > 50%` 这条公式）→ 改成「R1 只出现在充电支路，所以这个比值压不到 50%」。

## 未做

- 未插图、未标 `accepted`、未写 `review_record`。
- 未改正文。除本包与 manifest/场景/SVG/webp/prompt/contact 外无其他改动。
