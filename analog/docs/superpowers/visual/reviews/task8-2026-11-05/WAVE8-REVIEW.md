# Wave 8 视觉复核包（8 张，待人工审图）

本包新增 8 张手绘纸墨图（V4），全部 `status: generated`，未插入正文，未回填评分；没有伪造人工签核。

## 怎么看

1. 打开 [`contact-wave8.html`](contact-wave8.html)，逐张看大图。
   也可在 GitHub 直接看 [`WAVE8-GALLERY.md`](WAVE8-GALLERY.md)。
2. 按五项各打 1–5 分：教学必要性、事实精度、构图层级、风格一致性、印刷可读性。
3. 任一维度 <4 记具体返工点；5 分才可写 `accepted`。
4. 回复“第 X 张：5/5/5/5/5”或“全部 5 分通过”即可回填；模型不会代签。

## 优先看这四张

| 图 | 为什么先看 |
|---|---|
| `ch07-hysteresis-window` | 把时间域抖动换成回环，两个阈值与 305 mV 窗口一眼可读 |
| `ch05-tristate-handover` | 三态总线的“先关后开”时序，最容易在实板上漏掉 |
| `ch09-reference-ladder` | 把“基准选型”从口号变成五级精度阶梯 |
| `ch01-e24-ladder` | 把 3.285k → 3.3k 的落档过程画成流程 |

其余按章看：ch4 栅极窗口与死区账 → ch5 上拉功耗 → ch9 ESR 窗口。

## 清单

| id | 章 | 标题 | 类型 | 布局 | anchor |
|---|---|---|---|---|---|
| `ch01-e24-ladder` | 1 | E24 档位与 3.3k 的来历 | V4 | IG-013 | 1.1 |
| `ch04-gate-window` | 4 | 栅极保护的电压窗 | V4 | IG-013 | 4.4 |
| `ch04-deadtime-ledger` | 4 | 死区损耗的明账 | V4 | IG-013 | 4.4 |
| `ch05-rp-power` | 5 | 上拉电阻自己的功耗 | V4 | IG-013 | 5.2 |
| `ch05-tristate-handover` | 5 | 三态总线的交接时序 | V4 | IG-013 | 5.4 |
| `ch07-hysteresis-window` | 7 | 迟滞窗口与两个阈值 | V4 | IG-013 | 7.3 |
| `ch09-esr-window` | 9 | LDO 的 ESR 稳定窗口 | V4 | IG-013 | 9.3 |
| `ch09-reference-ladder` | 9 | 基准选型的精度阶梯 | V4 | IG-013 | 9.1 |

## 已过的自动闸

- `python scripts/check_visual_manifest.py` → PASS（0 项）
- 每张 `bounds: pass`，最小印刷字号 8.606 pt（≥8.5 pt）
- 逐张量过：文字越出画布 0 处；后绘面板遮住文字 0 处
- 审图页 8 个 `<img>`，缺失 0
- 图内数字均由 manifest 闸对 anchor 原文核查，未编码正文没有的量值

## 合入条件

- 人工评分回填且全部 ≥4；
- 插入对应章节 anchor，正文有引用与读图指引；
- 重建 BOOK.md 与站点后，`test_book_real`、`check_visual_manifest`、`test_papercut_figures` 全过；
- PR 合并后 main CI 全绿。
