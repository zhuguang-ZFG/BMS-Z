# Wave 9 视觉复核包（7 张，待人工审图）

本包新增 7 张手绘纸墨图（V4），全部 `status: generated`，未插入正文，未回填评分；没有伪造人工签核。

## 怎么看

1. 打开 [`contact-wave9.html`](contact-wave9.html)，逐张看大图。
   也可在 GitHub 直接看 [`WAVE9-GALLERY.md`](WAVE9-GALLERY.md)。
2. 按五项各打 1–5 分：教学必要性、事实精度、构图层级、风格一致性、印刷可读性。
3. 任一维度 <4 记具体返工点；5 分才可写 `accepted`。
4. 回复“第 X 张：5/5/5/5/5”或“全部 5 分通过”即可回填；模型不会代签。

## 优先看这四张

| 图 | 为什么先看 |
|---|---|
| `ch12-tia-three-way` | 把 TIA 的增益、带宽、稳定画成三角，12.10 的核心张力一眼可读 |
| `ch12-input-types` | 用 1MΩ 源把 BJT 20mV 与 CMOS 1µV 摆在一起，选型判据极硬 |
| `ch10-recovery-gap` | “第二拍变短”是单稳态最容易被忽略的失效 |
| `ch06-bias-balance` | 把 Ib×Rs 的账与 R3=R1∥R2 的边界画在同一页 |

其余：ch10 单稳态误差预算 → ch11 电流镜三笔误差 → ch12 开关电容。

## 清单

| id | 章 | 标题 | 类型 | 布局 | anchor |
|---|---|---|---|---|---|
| `ch06-bias-balance` | 6 | 输入偏置电流与平衡电阻 | V4 | IG-013 | 6.3 |
| `ch10-monostable-budget` | 10 | 单稳态 1.1RC 的误差预算 | V4 | IG-013 | 10.5 |
| `ch10-recovery-gap` | 10 | 单稳态恢复时间与连发触发 | V4 | IG-013 | 10.5 |
| `ch11-mirror-three-errors` | 11 | 电流镜的三笔误差 | V4 | IG-013 | 11.3 |
| `ch12-tia-three-way` | 12 | TIA 的增益带宽稳定三角 | V4 | IG-013 | 12.10 |
| `ch12-switch-cap` | 12 | 开关电容的等效电阻 | V4 | IG-013 | 12.12 |
| `ch12-input-types` | 12 | 按源阻抗选输入级 | V4 | IG-013 | 12.13 |

## 已过的自动闸

- `python scripts/check_visual_manifest.py` → PASS（0 项）
- 每张 `bounds: pass`，最小印刷字号 8.606 pt（≥8.5 pt）
- 逐张量过：文字越出画布 0 处；后绘面板遮住文字 0 处
- 审图页 7 个 `<img>`，缺失 0
- 图内数字均由 manifest 闸对 anchor 原文核查

## 合入条件

- 人工评分回填且全部 ≥4；
- 插入对应章节 anchor，正文有引用与读图指引；
- 重建 BOOK.md 与站点后，`test_book_real`、`check_visual_manifest`、`test_papercut_figures` 全过；
- PR 合并后 main CI 全绿。
