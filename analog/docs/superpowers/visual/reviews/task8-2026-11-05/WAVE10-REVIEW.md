# Wave 10 视觉复核包（9 张，待人工审图）

本包新增 9 张手绘纸墨图（V4），全部 `status: generated`，未插入正文，未回填评分；没有伪造人工签核。

覆盖 ch2（4 张）与 ch3（5 张）。ch2 此前只有 legacy SVG/照片；ch3 已有偏置、达林顿、热失控，这轮补的是开关驱动、组态折算、C/E 反接与厄利效应。

## 怎么看

1. 打开 [`contact-wave10.html`](contact-wave10.html)，逐张看大图。
   也可在 GitHub 直接看 [`WAVE10-GALLERY.md`](WAVE10-GALLERY.md)。
2. 按五项各打 1–5 分：教学必要性、事实精度、构图层级、风格一致性、印刷可读性。
3. 任一维度 <4 记具体返工点；5 分才可写 `accepted`。
4. 回复“第 X 张：5/5/5/5/5”或“全部 5 分通过”即可回填；模型不会代签。

## 优先看这四张

| 图 | 为什么先看 |
|---|---|
| `ch03-switch-budget` | 360Ω 与 10kΩ 两笔账并排，把“标称 β 不是饱和保证”算到毫安 |
| `ch02-zener-budget` | 228Ω → 220Ω、36.8mA、188mW 一条链，稳压管炸机的典型现场 |
| `ch02-junction-margin` | 122°C 对 125°C，只剩 3°C；余量不是形容词 |
| `ch03-low-high-side` | 同一只 NPN，参考点一换，3.3V GPIO 就从够得着变成够不着 |

其余：ch2 IEC 8kV 的 24A 分账 → ch2 并联热抢流 → ch3 C/E 反接 → ch3 组态折算律 → ch3 厄利效应。

## 清单

| id | 章 | 标题 | 类型 | 布局 | anchor |
|---|---|---|---|---|---|
| `ch02-esd-chain` | 2 | IEC 8kV 的 24A 分账 | V4 | IG-013 | 2.11.3 |
| `ch02-zener-budget` | 2 | 稳压管的限流电阻与最坏功耗 | V4 | IG-013 | 2.9 |
| `ch02-junction-margin` | 2 | 结温余量只剩 3°C | V4 | IG-013 | 2.9 |
| `ch02-parallel-hog` | 2 | 并联二极管的热抢流 | V4 | IG-013 | 2.9 |
| `ch03-switch-budget` | 3 | 继电器基极电阻的两笔账 | V4 | IG-013 | 3.5 |
| `ch03-low-high-side` | 3 | 低边与高边开关的参考点 | V4 | IG-013 | 3.5 |
| `ch03-reverse-beta` | 3 | C/E 反接为什么 β 只剩个位数 | V4 | IG-013 | 3.2 |
| `ch03-config-impedance` | 3 | 三种组态共用一条阻抗折算律 | V4 | IG-013 | 3.3 |
| `ch03-early-effect` | 3 | 厄利效应与输出阻抗 | V4 | IG-013 | 3.1 |

## 已过的自动闸

- `python scripts/check_visual_manifest.py` → PASS（0 项）
- 每张 `bounds: pass`，最小印刷字号 8.606 pt（≥8.5 pt）
- 逐张量过：文字越出画布 0 处；文字越出所在面板 0 处；后绘面板遮字 0 处；文字互压 0 处；文字压线 0 处
- 审图页 9 个 `<img>`，缺失 0
- 图内数字均由 manifest 闸对 anchor 原文核查

## 合入条件

- 人工评分回填且全部 ≥4；
- 插入对应章节 anchor，正文有引用与读图指引；
- 重建 BOOK.md 与站点后，`test_book_real`、`check_visual_manifest`、`test_papercut_figures` 全过；
- PR 合并后 main CI 全绿。
