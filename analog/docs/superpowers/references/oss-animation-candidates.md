# OSS 动画候选评估（Task 11b · 2026-11-03）

> 规则：任一候选**先记 license**；不得把外部代码未经许可拷进仓；默认**不**把 `generate_svgs.py` 改写成 Manim/GSAP 主链——它们是启发源，最多做可选并行实验目录（如 `experiments/`，不进主 CI）。

| repo | license | 用途建议 | FA-029 贴合 | 决策 |
|---|---|---|---|---|
| [yang0/handraw-style](https://github.com/yang0/handraw-style) | 见仓库 LICENSE | 封面 / 社媒提示词与风格编号（FA-029 来源） | **完全贴合**（视觉 DNA 已锁） | **采用**（仅用提示词配方，不引代码） |
| [ningzimu/handdrawn-tech-illustrations](https://github.com/ningzimu/handdrawn-tech-illustrations) | 先核 LICENSE | 章内静态分析图构图与中文标注密度 | 贴合（构图参考） | **灵感参考**（不替代 handraw.py） |
| [overegneered/manim-eng](https://github.com/overegneered/manim-eng) | 先核 LICENSE | 工程向 Manim 动画思路（公式逐步推导） | 中（版式思想可借） | **可选灵感**；不引入 Manim 重写管线 |
| [Mr-FuzzyPenguin/manim-circuit](https://github.com/Mr-FuzzyPenguin/manim-circuit) | 先核 LICENSE | 电路 Manim 组件 | 中 | **可选灵感**；许可不合或风格冲突则只记笔记 |
| [milkway/rpic-lang](https://github.com/milkway/rpic-lang) | 先核 LICENSE | SVG + GSAP 电路动画（交互思路） | 低（GSAP 依赖与主站 SMIL 冲突） | **可选对照**；主站仍 SMIL/`generate_svgs.py` |
| [wijnen/edraw](https://github.com/wijnen/edraw) | 先核 LICENSE | 电子图绘制 | 低-中 | **可选对照**；不替换生成器 |

## 结论

1. **主生成链不变**：`scripts/generate_svgs.py` → `handraw.apply` → `assets/svg/`（SMIL，明暗双模，印刷管线兼容）。本轮扩量的 35 张动画全部走该链。
2. Manim/GSAP 仅作思路启发（推导阶梯、节拍揭示、Indicate 高亮已在 `derive_ladder` / `stage_cards` 中落地）。
3. 若未来开并行实验目录 `experiments/`，须先核各仓库 license 并单独立项，不进主 CI。
