# Wave 14 视觉复核包（5 张，待人工审图）

本包 5 张全部 `status: generated`，`review_scores` 为空，未插入正文；没有伪造人工签核。

补的是「每节图数」最薄的四章：ch01（8 节 4 图）、ch06（7 节 3 图）、
ch11（11 节 4 图）、ch12（13 节 5 图）。五张只画「分账」与「分工」，
不重复既有图的结构；每张的数字逐 token 可回到 anchor 正文。

## 怎么看

1. 打开 [`contact-wave14.html`](contact-wave14.html)，逐张看大图。
   也可在 GitHub 直接看 [`WAVE14-GALLERY.md`](WAVE14-GALLERY.md)。
2. 按五项各打 1–5 分：教学必要性、事实精度、构图层级、风格一致性、印刷可读性。
3. 任一维度 <4 记具体返工点；5 分才可写 `accepted`。
4. 回复“第 X 张：5/5/5/5/5”或“全部 5 分通过”即可回填；模型不会代签。

## 优先看

| 图 | 为什么先看 |
|---|---|
| `ch01-thevenin-two-load` | 两负载法反推出 5kΩ 与 4kΩ 两个互相矛盾的内阻——这正是该方法的陷阱 |
| `ch06-741-four-blocks` | ④ 偏置网络**不在信号通路**，所以它下方故意不接箭头；增益按级相乘到 20 万倍 |
| `ch11-phase-margin-table` | 45°/60°/65° 对应 23%/10%/4% 过冲，65° 即 Butterworth |
| `ch12-switched-cap-equivalent` | 1pF 配 100kHz 等效 10MΩ：片上做不出的大电阻用开关电容换 |
| `ch12-input-stage-source-z` | 1MΩ 源阻下 BJT 20mV vs CMOS 1µV，但热噪声 BJT 反赢 1.7 倍 |

## 已做的机器检查

| 检查 | 结果 |
|---|---|
| 手绘构建（5 张） | 全部 `bounds: pass`，最小印刷字号 8.606pt（限 8.5pt） |
| `check_visual_manifest.py` | PASS（0 项） |
| 几何审计（出画布 / 文字互压 / 越界面框 / 文字压曲线） | 5 张 0 缺陷 |
| 数字溯源（图内 token ⊆ anchor 正文） | 5/5 通过 |
| alt 溯源（alt token ⊆ 图面 token） | 5/5 通过 |
| 字形覆盖（4 款思源字体） | 0 缺字 |
| 视觉测试 | 65/65 pass |
| Playwright 读图复核 | 5 张逐张看过 |

## 本轮一并修掉的两处版面缺陷

- **`opamp_four_blocks()` 布局重构**：四块等距 pitch 104，信号箭头只穿前三级；
  ④ 偏置网络明确标「不在信号通路」且下方不接箭头（原先画成串联链，拓扑不诚实）。
- **`thevenin_two_load_test()` 贴边**：绿面板内末行距底边仅 1.6px，
  改 26px 行距后余量 7.6px。此处**几何审计不报**（文字技术上仍被面板包含），
  靠读图发现——说明 audit 干净不等于视觉干净。

提交：`db39ac2`。
