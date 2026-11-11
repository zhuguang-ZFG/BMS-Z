# Wave 11 视觉复核包（3 张，待人工审图）

本包新增 3 张手绘纸墨图（V4），全部 `status: generated`，未插入正文，未回填评分；没有伪造人工签核。

覆盖 ch11（米勒带宽）与 ch13（恒流源合规电压、分流电阻预算）。三张都避开已有动画/手绘图的角度：不重复画结构，只画“账”。

## 怎么看

1. 打开 [`contact-wave11.html`](contact-wave11.html)，逐张看大图。
   也可在 GitHub 直接看 [`WAVE11-GALLERY.md`](WAVE11-GALLERY.md)。
2. 按五项各打 1–5 分：教学必要性、事实精度、构图层级、风格一致性、印刷可读性。
3. 任一维度 <4 记具体返工点；5 分才可写 `accepted`。
4. 回复“第 X 张：5/5/5/5/5”或“全部 5 分通过”即可回填；模型不会代签。

## 优先看

| 图 | 为什么先看 |
|---|---|
| `ch11-miller-bandwidth` | 10pF 被增益撬成 1.01nF，15.8kHz 是“以为能到 MHz”的现场 |
| `ch13-compliance-ceiling` | 2.0k / 4.2k / 11.2k 三块天花板，把“恒流源也会退出恒流”算死 |
| `ch13-current-sense-budget` | 5A 的 0.25W 与堵转 20A 的 4W 并排，精度 1% 的 CMRR 门槛跟着出来 |

## 清单

| id | 章 | 标题 | 类型 | 布局 | anchor |
|---|---|---|---|---|---|
| `ch11-miller-bandwidth` | 11 | 米勒电容把带宽压到 15.8kHz | V4 | IG-013 | 11.5 |
| `ch13-compliance-ceiling` | 13 | 恒流源的合规电压天花板 | V4 | IG-013 | 13.5.1 |
| `ch13-current-sense-budget` | 13 | 10mΩ 分流电阻的两笔账 | V4 | IG-013 | 13.8 |

## 已过的自动闸

- `python scripts/check_visual_manifest.py` → PASS（0 项）
- 每张 `bounds: pass`，最小印刷字号 8.606 pt（≥8.5 pt）
- 逐张量过：文字越出画布 0 处；文字越出面板 0 处；后绘面板遮字 0 处；文字互压 0 处；文字压线 0 处
- 审图页 3 个 `<img>`，缺失 0
- 图内数字均由 manifest 闸对 anchor 原文核查

## 合入条件

- 人工评分回填且全部 ≥4；
- 插入对应章节 anchor，正文有引用与读图指引；
- 重建 BOOK.md 与站点后，`test_book_real`、`check_visual_manifest`、`test_papercut_figures` 全过；
- PR 合并后 main CI 全绿。
