# Wave 12 视觉复核包（6 张，待人工审图）

本包新增 6 张手绘纸墨图（V4），全部 `status: generated`，未插入正文，未回填评分；没有伪造人工签核。

补的是全书图最少的五章：ch01（原 1 张）、ch04（原 2 张）、ch06（原 1 张）、ch07（原 1 张）。六张都只画“账”与时序，不重复既有图的结构。

## 怎么看

1. 打开 [`contact-wave12.html`](contact-wave12.html)，逐张看大图。
   也可在 GitHub 直接看 [`WAVE12-GALLERY.md`](WAVE12-GALLERY.md)。
2. 按五项各打 1–5 分：教学必要性、事实精度、构图层级、风格一致性、印刷可读性。
3. 任一维度 <4 记具体返工点；5 分才可写 `accepted`。
4. 回复“第 X 张：5/5/5/5/5”或“全部 5 分通过”即可回填；模型不会代签。

## 优先看

| 图 | 为什么先看 |
|---|---|
| `ch01-electrolytic-life` | 2000 小时怎么变成 3.7 年：降温 4 档翻 4 倍，纹波发热再吃回去 |
| `ch01-derating-product` | 降容是乘法不是加法：三项八折相乘只剩一半 |
| `ch04-dvdt-false-turnon` | 50pF × 20V/ns = 1A 落在 10Ω 上，栅极被自己灌开 |
| `ch06-slew-vs-gbw` | 压摆段 2µs 把 1.1µs 的建立时间拖成 2.6µs，GBW 看着宽也没用 |
| `ch07-pullup-three-accounts` | 一只上拉电阻同时挂速度、低电平、噪声三本账 |
| `ch07-threshold-budget` | ±50mV 的电阻容差是 ±5mV 失调的十倍——先压最大项 |

## 清单

| id | 章 | 标题 | 类型 | 布局 | anchor |
|---|---|---|---|---|---|
| `ch01-electrolytic-life` | 1 | 10°C 翻倍法则下的电解电容寿命账 | V4 | IG-013 | 1.7 |
| `ch01-derating-product` | 1 | 降容是乘法：三项八折只剩一半 | V4 | IG-013 | 1.7 |
| `ch04-dvdt-false-turnon` | 4 | dv/dt 误导通的定量图像 | V4 | IG-013 | 4.3 |
| `ch06-slew-vs-gbw` | 6 | 压摆率与全功率带宽的两套物理 | V4 | IG-013 | 6.7 |
| `ch07-pullup-three-accounts` | 7 | 上拉电阻同时挂在三本账上 | V4 | IG-013 | 7.2 |
| `ch07-threshold-budget` | 7 | 阈值精度的误差预算排序 | V4 | IG-013 | 7.2 |

## 已过的自动闸

- `python scripts/check_visual_manifest.py` → PASS（0 项）
- 65 项视觉测试通过：`test_visual_manifest` 31 + `test_visual_builder_review` 7 + `test_papercut_figures` 4 + `test_visual_fidelity` 5 + `test_visual_density` 16 + `test_visual_contact_sheet` 2
- 每张 `bounds: pass`，最小印刷字号 8.606 pt（≥8.5 pt）
- 逐张 DOM 量测：文字越出画布 0、文字越出面板 0、填充条压字 0、文字互压 0
- 图内数字与 alt 文案均逐 token 对 anchor 原文核查；alt 不含图面上没有的数字
- 审图页 6 个 `<img>`，缺失 0

## 合入条件

五项全部 ≥4 才回填 `review_scores` 与 `accepted`；通过后再按 anchor 插入正文。
