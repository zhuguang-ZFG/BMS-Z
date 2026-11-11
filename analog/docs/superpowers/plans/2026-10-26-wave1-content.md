# Wave 1 内容扩写与视觉升级实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把第 0、2、11、14、16 章扩写到印刷书正文规格，补齐 7 张静态技术插图、5 套可运行 SPICE 仿真与 32 道章节练习，并完成 16K 整书重建与视觉审计。

**Architecture:** 所有正文仍以 `docs/*.md` 为唯一真源。每章先建立自动化合同（节结构、字数、图表、仿真、练习），再写正文、插图、deck 与题目；最后统一升级打印视觉、重做字体子集、重建 16K 内文/封面并跑全量回归。

**Tech Stack:** Python 3、Markdown/Material、SVG、ngspice、Chromium/Playwright、PyMuPDF（仅本地审计）、unittest、ruff。

**Spec:** `docs/superpowers/specs/2026-10-25-print-book-design.md`（§6.1–§6.6）

## Global Constraints

- 不推送。任何推送前必须按仓库约定执行安全审查门；发现问题先修复，不得跳过。
- `docs/` 是唯一内容真源；不得直接改构建产物伪装内容。
- 构建产物只写 `build/`、`analog-book/dist/`、`analog-book/dist/print/` 或临时目录；不提交 PDF、PNG 审计图、字体源文件。
- 不修改 `book.yml`；`manifest-a4.json` 保持冻结；`release.edition_status` 保持 `draft`。
- 不伪造实测数据、客户案例、文献、ISBN、厂商曲线。实测只限 RC、LM358、MOSFET；其余明确标为“仿真 / 教学推导 / 常见现象”。
- 正文不得出现 `TODO`、`TBD`、`待补`、`占位`、假页码、假书脊或“已审读”。
- 每章至少 3 个完整算例、1 套自包含 SPICE deck、4 个编号图表；Wave 1 五章各补到 9–10 道题。
- 图用 `<figure><img><figcaption>`；表前一行写 `**表 N-M　标题**`；图注写“看什么、得出什么”。
- 新静态图只放 `assets/figures/`，不得外链、不得含脚本；SPICE deck 不得 `.include` / `.lib` 外部模型。
- 每章完成后更新 `test_book_real.py` 的题目总数与 `docs/p9-00-quiz.md` 的计数说明；最终总数 90。
- 本地提交只做小步提交，不推送。

## Scope And Non-goals

**Scope:** 五章正文、7 张静态图、5 套 SPICE、32 道练习、打印 CSS 视觉基座、字体子集、16K 重建与验收。

**Non-goals:** 不扩写第 1、3–10、12、13、15、17、18 章；不改 A4 管线；不做 ISBN/条码；不引入新依赖；不重做 108 张动画。

## File Structure

**修改：**
- `docs/p1-01-ch0.md` — 0.7–0.10、算例、图表、速查卡、延伸阅读
- `docs/p1-03-ch2.md` — 2.9–2.13、算例、图表、修复乱码
- `docs/p2-01-ch11.md` — 11.8–11.11、算例、图表
- `docs/p3-01-ch14.md` — 14.9–14.12、算例、图表、移动章末总结
- `docs/p4-01-ch16.md` — 16.6–16.9、算例、图表、案例免责声明
- `docs/p9-00-quiz.md` — 每章追加题目与答案，最终 90 题
- `docs/p0-07-toc.md` — 题目计数
- `analog-book/styles/print.css` — 章首舞台、图框、正文节奏
- `scripts/site_media/typography.css` — 站点图注样式
- `analog-book/book/fonts.py` — 扫描 `assets/figures`
- `analog-book/tests/test_book_real.py` — 90 题、字数下限
- `analog-book/tests/test_spice.py` — 6 套 deck、逐套运行
- `analog-book/tests/test_book_fonts.py` — 如需补充新字形说明
- `analog-book/tests/test_wave1_chapters.py` — 新增，逐章合同

**新增：**
- `assets/figures/ch00-controlled-sources.svg`
- `assets/figures/ch02-operating-map.svg`
- `assets/figures/ch02-tvs-clamp.svg`
- `assets/figures/ch11-cascode.svg`
- `assets/figures/ch14-error-budget.svg`
- `assets/figures/ch14-power-tree-timing.svg`
- `assets/figures/ch16-signal-injection.svg`
- `assets/spice/ch00/divider.cir` + `assert.json`
- `assets/spice/ch02/rectifier.cir` + `assert.json`
- `assets/spice/ch11/diffpair.cir` + `assert.json`
- `assets/spice/ch14/pt100.cir` + `assert.json`
- `assets/spice/ch16/probe.cir` + `assert.json`
- `scripts/test_figures.py`

---

### Task 1: 视觉基座与合同骨架

**Files:**
- Modify: `analog-book/styles/print.css`
- Modify: `scripts/site_media/typography.css`
- Create: `analog-book/tests/test_wave1_chapters.py`

**Interfaces:**
- Produces: `CHAPTER_CONTRACTS` 字典（后续每章任务追加一项）、`print.css` 的 `.chapter-hero` / `figure` 选择器、站点 `figcaption` 样式。

- [ ] **Step 1: 写视觉合同测试（预期失败）**

在 `analog-book/tests/test_wave1_chapters.py` 写：

```python
#!/usr/bin/env python3
"""Wave 1 逐章合同：字数、节结构、图表、算例、仿真与练习。"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
ROOT = BOOK.parent
sys.path.insert(0, str(BOOK))

from book import config  # noqa: E402
from book.manifest import BookError  # noqa: E402


class VisualContractTests(unittest.TestCase):
    def test_print_css_has_chapter_stage_and_figure_frames(self):
        css = (BOOK / "styles" / "print.css").read_text(encoding="utf-8")
        for selector in (
            ".book .chapter-hero",
            ".book .chapter-hero-num",
            ".book .md-typeset figure",
            ".book .md-typeset figcaption",
        ):
            self.assertIn(selector, css)
        self.assertIn("break-inside: avoid", css)
```

- [ ] **Step 2: 运行并确认红**

Run: `python -B -m unittest analog-book.tests.test_wave1_chapters.VisualContractTests -v`
Expected: FAIL，至少 `.book .chapter-hero` 不存在。

- [ ] **Step 3: 写打印视觉基座**

在 `print.css` 的“正文页”前加入章首舞台；在“插图”段替换/补充图框。目标不是再画一套样张，而是让真实章页也有舞台、密集正文和统一图框：

```css
/* ---------- 章首舞台（真实章页） ---------- */
.book .chapter-hero {
  position: relative; isolation: isolate; overflow: hidden;
  margin: 0 0 7mm; padding: 5.5mm 6.5mm 5mm;
  border: 0.2mm solid var(--rule);
  border-top: 1.2mm solid var(--navy);
  background:
    radial-gradient(120% 90% at 100% 0%, rgba(180, 83, 9, .10), transparent 55%),
    linear-gradient(135deg, #fbf7f1 0%, #fffdf8 55%, #f3f8f7 100%);
  break-inside: avoid;
}
.book .chapter-hero::before {
  content: ""; position: absolute; inset: 0; z-index: -1;
  background-image: radial-gradient(rgba(20, 33, 61, .14) .22mm, transparent .24mm);
  background-size: 4mm 4mm;
  -webkit-mask-image: linear-gradient(135deg, #000, transparent 68%);
  mask-image: linear-gradient(135deg, #000, transparent 68%);
}
.book .chapter-hero::after {
  content: ""; position: absolute; right: 0; top: 0;
  width: 26mm; height: 0.8mm; background: var(--amber);
}
.book .chapter-hero > h1 { font-size: 23pt; line-height: 30pt; margin-bottom: 3mm; }
.book .chapter-hero > blockquote { background: transparent; border-left: 0; padding-left: 0; }
.book .chapter-hero .chapter-intuition {
  margin: 0 0 4mm; padding: 2.5mm 0 2.8mm; border-top: 0.4mm solid var(--navy);
}
.book .chapter-hero .chapter-hero-num {
  position: absolute; right: 4mm; bottom: -9mm; z-index: -1;
  margin: 0; font: 800 58pt/1 "Book Mono", monospace;
  color: transparent; -webkit-text-stroke: 0.28mm rgba(180, 83, 9, .38);
  letter-spacing: -.04em;
}
```

图框：

```css
.book .md-typeset figure {
  position: relative; break-inside: avoid;
  margin: 3.6mm 0 4.8mm; padding: 3mm 3mm 2.4mm;
  border: 0.2mm solid var(--rule); border-top: 0.6mm solid var(--navy);
  background: #fff;
}
.book .md-typeset figure > img,
.book .md-typeset figure > p { display: block; margin: 0 auto; }
.book .md-typeset figcaption {
  margin-top: 2.2mm; padding-top: 2mm;
  border-top: 0.2mm solid var(--rule);
  font: 400 8.8pt/12.6pt "Book Sans", sans-serif;
  color: var(--muted); text-align: left;
}
.book .md-typeset figure:has(figcaption)::after {
  content: "FIG"; position: absolute; right: 2.4mm; top: 1.4mm;
  font: 700 6.2pt/1 "Book Mono", monospace; letter-spacing: .18em;
  color: var(--rule);
}
```

站点图注（屏幕侧）：

```css
.md-typeset figure {
  margin: 1.4rem 0 1.8rem;
}
.md-typeset figure > img { display: block; margin: 0 auto; }
.md-typeset figcaption {
  margin-top: .55rem; font-size: .72rem; line-height: 1.6;
  color: var(--md-default-fg-color--light); text-align: left;
}
```

- [ ] **Step 4: 跑测试并构建样张**

Run:
```bash
python -B -m unittest analog-book.tests.test_wave1_chapters.VisualContractTests -v
python analog-book/build_print_book.py --sample
```
Expected: 测试通过；样张生成成功。用 PyMuPDF 将样张首章页渲染到 `build/visual-audit/sample-chapter.png`，人工检查：章首无大块空白、图框不压正文、图注不孤行。

- [ ] **Step 5: 提交**

```bash
git add analog-book/styles/print.css scripts/site_media/typography.css analog-book/tests/test_wave1_chapters.py
git commit -m "feat(book): add wave-one chapter stage and figure framing"
```

---

### Task 2: 第 0 章扩写（15k）

**Files:**
- Modify: `docs/p1-01-ch0.md`
- Modify: `docs/p9-00-quiz.md`
- Modify: `docs/p0-07-toc.md`
- Modify: `analog-book/tests/test_book_real.py`
- Modify: `analog-book/tests/test_spice.py`
- Modify: `analog-book/tests/test_wave1_chapters.py`
- Create: `assets/figures/ch00-controlled-sources.svg`
- Create: `assets/spice/ch00/divider.cir`
- Create: `assets/spice/ch00/assert.json`

**Interfaces:**
- Produces: `divider.cir` 的节点 `in/out`、数据 `divider.dat`、指标 `vout_open/vout_load/i_load`；后续章节复用“KCL/分压/带载”语言。

- [ ] **Step 1: 追加第 0 章合同测试（预期失败）**

在 `test_wave1_chapters.py` 增加：

```python
CHAPTER_CONTRACTS = {
    0: {
        "stem": "p1-01-ch0",
        "floor": 15000,
        "sections": ("0.7", "0.8", "0.9", "0.10"),
        "examples": 3,
        "figures": 5,
        "tables": 2,
        "quiz": 10,
        "figure": "ch00-controlled-sources.svg",
        "deck": "ch00/divider.cir",
    },
}


class ChapterContractTests(unittest.TestCase):
    def test_contracts(self):
        quiz = (config.DOCS / "p9-00-quiz.md").read_text(encoding="utf-8")
        for chapter, spec in CHAPTER_CONTRACTS.items():
            path = config.DOCS / f"{spec['stem']}.md"
            text = path.read_text(encoding="utf-8")
            chars = len(re.sub(r"\s+", "", text))
            self.assertGreaterEqual(chars, spec["floor"], path.name)
            for section in spec["sections"]:
                self.assertRegex(text, rf"^### {re.escape(section)}\s", path.name)
            for index in range(1, spec["examples"] + 1):
                self.assertIn(f"例 {chapter}-{index}", text, path.name)
            self.assertGreaterEqual(text.count("<figure"), spec["figures"], path.name)
            captions = re.findall(rf"<strong>表 {chapter}-\d+", text)
            self.assertGreaterEqual(len(captions), spec["tables"], path.name)
            self.assertIn(spec["figure"], text, path.name)
            deck = ROOT / "assets" / "spice" / spec["deck"]
            spec_json = json.loads(
                (deck.parent / "assert.json").read_text(encoding="utf-8"))
            self.assertEqual({"deck", "analysis", "data", "min_rows", "metrics"},
                             set(spec_json), deck.parent.name)
            found = len(re.findall(rf'id="q-ch{chapter}-\d+"', quiz))
            self.assertEqual(spec["quiz"], found, f"第 {chapter} 章题数")
            for marker in ("TODO", "TBD", "待补", "占位"):
                self.assertNotIn(marker, text, f"{path.name} 残留 {marker}")
```

- [ ] **Step 2: 运行并确认红**

Run: `python -B -m unittest analog-book.tests.test_wave1_chapters.ChapterContractTests -v`
Expected: FAIL（第 0 章字数、0.7、算例、deck 均缺）。

- [ ] **Step 3: 写 0.7 量纲、数量级与工程记号（约 3,000 字）**

保留 0.1–0.6，在 0.6 后新增。必须包含：

- 用“5 V 不是绝对高度，而是两点水位差”把电压参考讲透；接 0.4 的地。
- SI 七个基本量与导出单位；只列本书常用单位，不抄全表。
- 工程记号的读写规则：`4.7 kΩ`、`100 nF`、`2.2 µF`，数字与单位之间空格，微用 `µ`。
- 量纲检查三例：`V=IR`、`P=VI`、`τ=RC`；明确“单位不对，公式一定错；单位对，公式不一定对”。
- 数量级直觉：1 mA、10 kΩ、100 nF 组成的电路，时间常数在 1 ms 量级；不要一上来算到小数点后六位。
- **表 0-1　常用 SI 词头**：p/n/µ/m/k/M/G，配一个“读错一次差一千倍”的例子。
- 小白视角：把“工程记号”写成“给数字换一件合身的衣服”，避免术语堆叠。

**例 0-1　分压器带载误差**（放在 0.3 末尾，保持与既有 10 V/10 kΩ 例子同一组数）：

- 给定：12 V、R1=10 kΩ、R2=10 kΩ、RL=10 kΩ。
- 求：空载输出、带载输出、相对误差、输出电阻。
- 解：空载 6 V；带载 R2∥RL=5 kΩ → 4 V；误差 −33.3%；输出电阻 R1∥R2=5 kΩ。
- 校验：负载电流 0.4 mA，5 kΩ 上压降 2 V → 4 V。
- 坑点：把“分压比”当“带载能力”；带载误差与 RL/Rout 直接相关。

- [ ] **Step 4: 写 0.8 受控源与放大器雏形（约 2,500 字）**

必须包含：

- 独立源 vs 受控源：受控源的输出由**别的节点电压/支路电流**决定，不是自己独立。
- 四类受控源：VCVS、VCCS、CCVS、CCCS；各给一个“像什么”的比喻（压控水阀、跨导、电流互感器、电流镜雏形）。
- 跨导 `gm = ΔIout/ΔVin` 的单位 A/V = S；用 2 mS、1 V 控制量、3 kΩ 负载算输出 6 V。
- 放大器三参数模型：输入电阻、输出电阻、受控源增益；说明“放大不是凭空造能量，是用控制量搬运电源能量”。
- 理想运放只是“增益极大、输入电阻极大、输出电阻极小”的受控源极限；不要提前讲虚短虚断的成立条件。
- **图 0-3　四类受控源**：用 `assets/figures/ch00-controlled-sources.svg`，四象限画菱形符号、控制量与输出量、一个生活比喻；图注写“看菱形箭头的方向：箭头指向决定电压/电流，控制量在另一支路”。

**例 0-2　受控源等效跨导**：

- 给定：VCVS 控制系数 40、输入 50 mV、输出串 200 Ω，接 1 kΩ 负载。
- 求：输出电流、等效跨导、负载电压。
- 解：理想输出 2 V；总串阻 1.2 kΩ → 1.667 mA；等效跨导 1.667 mA / 50 mV = 33.3 mS；负载电压 1.667 V。
- 校验：负载分压 1.667 V；受控源输出 2 V 减 200 Ω 上的 0.333 V。
- 坑点：把“开路电压增益”直接当“带载增益”。

- [ ] **Step 5: 写 0.9 功率、能量与符号约定（约 2,500 字）**

必须包含：

- `P=VI`、`P=I²R`、`P=V²/R` 的适用条件；为什么电阻三种写法等价，而电源不能乱套。
- 关联参考方向：电流从电压正端流入，吸收功率；从正端流出，发出功率。用“记账”比喻，不写成符号学论文。
- 能量 `W=Pt`、电池容量 Ah/Wh、效率；9 V/500 mAh 电池供 10 mA，理想 50 h，按 80% 可用算 40 h。
- 电阻额定功率与降额：1/4 W 电阻按 50% 降额只有 125 mW；12 V 加在 1 kΩ 上是 144 mW，必须换 1/2 W。
- 自热与温升：功率不是“抽象数字”，最终会变成温度；接第 14 章热阻链。
- **例 0-3　电阻功耗与额定功率**：给定 12 V、1 kΩ、1/4 W、环境 40°C；求电流、功耗、降额判断；解 12 mA、144 mW；1/4 W 的 50% 只有 125 mW，不合格；选 1/2 W 且留 28% 余量；坑点是“常温摸着不烫”不等于额定够。
- 加一张“功率记账表”小表（不编号，作为算例的一部分），列“谁吸收/谁发出/多少”。

- [ ] **Step 6: 写 0.10 十个开局误区（约 2,000 字）**

用 **表 0-2　十个开局误区**，每行“误区 / 为什么错 / 正确动作”：

1. 电压是绝对量 → 电压是两点差 → 先问参考点。
2. 电流会被电阻“用完” → 串联电流处处相等 → 用 KCL 追回路。
3. 分压公式永远成立 → 只在空载/后级高阻时成立 → 先算输出电阻。
4. 地是下水道 → 地是参考点兼回流路径 → 看回流阻抗。
5. 电池是理想恒压源 → 有内阻、会随负载塌 → 查 V-I 斜率。
6. 大电阻一定省电 → 功耗还取决于电压/电流 → 用 P=V²/R 或 I²R。
7. 电容能瞬间提供任意电流 → 有 ESR/ESL，电压不能突变 → 看去耦环路。
8. 放大器增益越大越好 → 带宽/噪声/稳定性会买单 → 先定信号链预算。
9. 仿真过了就能工作 → 模型缺寄生与公差 → 仿真只证拓扑与数量级。
10. 公式记住就会设计 → 不知道假设就会用错 → 每条公式旁写适用条件。

表后逐条用 2–4 句展开，至少给 3 个“真实电路里会怎样”的小场景。

- [ ] **Step 7: 章末速查卡、小结与延伸阅读**

在通关打卡前加入：

- **本章速查卡**（5 条）：电压是差、电流成环、功率有代价、分压先看输出电阻、受控源看控制量。
- **小结与下一章**：用 3 句话把“水路八词 → 三个习惯 → 量纲/受控源/功率”串起来；下一章预告“理想元件开始长寄生”。
- **延伸阅读** 6 条，只列真实资料：Horowitz & Hill《The Art of Electronics》第 1 章；MIT 6.002 电路与电子学公开课；Falstad 电路仿真器；NIST SI Brochure；All About Circuits 直流章节；本书第 1 章。每条写“读什么 + 为什么现在读”，不写假页码。

- [ ] **Step 8: 把所有图片改成 figure，给所有表加表注**

第 0 章现有 4 张图全部改成：

```html
<figure>
<img src="assets/svg/water-analogy.svg" width="720" alt="水路与电路八词对照">
<figcaption>水路八词对照：电压是水位差、电流必须成环，电容与电感分别对应水位与水流惯性。</figcaption>
</figure>
```

图注要求：

- 水路图：八词一一对应，先看环再记词。
- 电压降图：同一股电流在串联电阻上按阻值分压，总和等于电源电压。
- 分压带载图：空载 6 V，接 10 kΩ 负载跌到 4 V，误差 33%。
- 恒压/恒流图：看 V-I 曲线是竖线还是水平线，判断内阻。
- 新受控源图：四类受控源由“控制量”而非自己决定输出。

现有 2 张表加表注：`**表 0-1　常用 SI 词头**`、`**表 0-2　十个开局误区**`；水路八词表和源性格表若保留，也补表注并按出现顺序重编号。不要手写错误表号；`number_tables()` 会按顺序重排。

- [ ] **Step 9: 画受控源静态图**

创建 `assets/figures/ch00-controlled-sources.svg`：

- `viewBox="0 0 960 520"`，白底，藏青 `#14213d` 线框、琥珀 `#b45309` 强调、青 `#0f766e` 控制量。
- 四象限：左上 VCVS（电压控电压）、右上 VCCS（电压控电流）、左下 CCVS（电流控电压）、右下 CCCS（电流控电流）。
- 每格画一个菱形受控源符号、控制支路、输出端和一句中文比喻；文字 ≥ 9 个 `<text>`。
- 顶部标题“四类受控源：输出听谁的？”；底部一行“先找控制量，再谈增益”。
- 必须含 `<title>` 与 `<desc>`；不得含 `<script>`、`<image>`、`http`、外部字体。

- [ ] **Step 10: 加 SPICE deck 与断言**

`assets/spice/ch00/divider.cir`：

```spice
* 第 0 章 分压器带载：10V，R1=R2=10k，1ms 后加 0.5mA 负载
.param VIN=10 R1=10k R2=10k
V1 in 0 DC {VIN}
R1 in out {R1}
R2 out 0 {R2}
I1 out 0 PULSE(0 0.5m 1m 1u 1u 10m 20m)
.tran 5u 4m 0 5u
.control
run
set wr_singlescale
set wr_vecnames
wrdata divider.dat v(out) i(I1)
meas tran vout_open FIND v(out) AT=0.5m
meas tran vout_load FIND v(out) AT=3m
meas tran i_load FIND i(I1) AT=3m
print vout_open vout_load i_load
.endc
.end
```

`assert.json`：

```json
{
  "deck": "divider.cir",
  "analysis": "tran",
  "data": "divider.dat",
  "min_rows": 200,
  "metrics": {
    "vout_open": {"expected": 5.0, "tolerance": 0.02},
    "vout_load": {"expected": 2.5, "tolerance": 0.02},
    "i_load": {"expected": 0.0005, "tolerance": 0.00001}
  }
}
```

说明：`i_load` 的符号可能为负，`parse_measurements` 取绝对值前先确认；若实际为负，把断言改为 `"expected": -0.0005`，不要改 deck 去伪造正号。

- [ ] **Step 11: 追加 7 道题并更新计数**

在 `docs/p9-00-quiz.md` 第 0 章题目末尾追加 `q-ch0-04` 至 `q-ch0-10`，每题带 `<details>` 答案：

| ID | 考点 | 答案要点 |
|---|---|---|
| q-ch0-04 | 量纲/时间常数 | 10 kΩ × 100 µF = 1 s；单位是秒 |
| q-ch0-05 | 功率与降额 | 12 V/1 kΩ → 144 mW；1/4 W 降额 50% 仅 125 mW，不合格；选 1/2 W |
| q-ch0-06 | 受控源 | 2 mS × 1 V = 2 mA；3 kΩ 上 6 V |
| q-ch0-07 | 地/回流 | 0.1 Ω × 1 A = 0.1 V 地弹；参考点不是理想零阻抗 |
| q-ch0-08 | 源内阻 | 1 kΩ 负载、50 Ω 内阻 → 5 × 1k/1.05k ≈ 4.76 V |
| q-ch0-09 | 能量/电池 | 500 mAh/10 mA=50 h；80% 可用约 40 h |
| q-ch0-10 | 开局误区 | 任选一个误区，指出错误假设与正确检查动作 |

更新 `test_book_real.py` 的 `self.assertEqual(58, merged, ...)` → `65`；更新 `docs/p9-00-quiz.md` 开头计数与 `docs/p0-07-toc.md` 的“58 题”为 65。

- [ ] **Step 12: 跑第 0 章门禁并提交**

Run:
```bash
python -B -m unittest analog-book.tests.test_wave1_chapters.ChapterContractTests -v
python scripts/build_site.py --build
python -B -m unittest analog-book.tests.test_book_real.RealBookTests.test_chapter_exercises_and_appendix_answers -v
```
Expected: 第 0 章合同通过；65 题合并；如本地无 ngspice，SPICE 运行测试跳过，必须在 ledger 记录“CI-only”。

```bash
git add docs/p1-01-ch0.md docs/p9-00-quiz.md docs/p0-07-toc.md \
  assets/figures/ch00-controlled-sources.svg assets/spice/ch00 \
  analog-book/tests/test_wave1_chapters.py analog-book/tests/test_book_real.py
git commit -m "feat(book): expand chapter 0 with units sources and power"
```

---

### Task 3: 第 2 章扩写（16k）

**Files:**
- Modify: `docs/p1-03-ch2.md`
- Modify: `docs/p9-00-quiz.md`
- Modify: `docs/p0-07-toc.md`
- Modify: `analog-book/tests/test_book_real.py`
- Modify: `analog-book/tests/test_wave1_chapters.py`
- Create: `assets/figures/ch02-operating-map.svg`
- Create: `assets/figures/ch02-tvs-clamp.svg`
- Create: `assets/spice/ch02/rectifier.cir`
- Create: `assets/spice/ch02/assert.json`

**Interfaces:**
- Produces: `rectifier.cir` 输出 `v(out)`、桥臂电流 `i(D1)`；后续第 13 章引用“整流纹波/浪涌”但不重复推导。

- [ ] **Step 1: 追加合同（预期失败）**

在 `CHAPTER_CONTRACTS` 加：

```python
    2: {
        "stem": "p1-03-ch2",
        "floor": 16000,
        "sections": ("2.9", "2.10", "2.11", "2.12", "2.13"),
        "examples": 3,
        "figures": 7,
        "tables": 5,
        "quiz": 9,
        "figure": "ch02-operating-map.svg",
        "deck": "ch02/rectifier.cir",
    },
```

Run: `python -B -m unittest analog-book.tests.test_wave1_chapters.ChapterContractTests -v`
Expected: FAIL（第 2 章字数/新节/deck 缺）。

- [ ] **Step 2: 修复现有乱码与重复链接**

- 第 53 行附近“温度就跟着跑。：①”改成“温度就跟着跑。两个速算：①……”。
- 第 191 行“救过多少驱动管。；接口保护”改成“救过多少驱动管；接口保护”。
- 删除重复的 `动画演示 5.2` 行，保留首次出现。
- 把“tiny 的 PN 结”改成“极小的 PN 结”，全章清除中英混排造成的断句。

- [ ] **Step 3: 写 2.9 温度、击穿与安全工作区（约 2,000 字）**

必须包含：

- 肖克利方程温度项：`Is(T)` 随温度指数上升，`Vf` 约 −2 mV/°C；不要只写“温度升高压降降低”，要讲“同样电流下”。
- 正温度系数 vs 负温度系数：硅 PN 结在恒流下 `Vf` 负漂；在恒压下电流暴增；并联均流为什么困难。
- 击穿分类：齐纳击穿（低反压、隧道）、雪崩击穿（高反压、碰撞电离）；两者都是可逆的，但**必须限流**。
- 安全工作区（SOA）：电压、电流、功率、温度四条边界；雪崩能量 `Eas` 只在规定条件下可重复。
- **图 2-1　二极管工作地图**：横轴反向电压、纵轴电流（对数），标正向、反向截止、击穿、SOA 边界；图注“先看工作在哪个象限，再谈参数”。
- **常见现象**：稳压管直接并在 12 V 电源上不串限流电阻 → 烧毁；只能写“常见现象/教材推导”，不写“某客户”。

- [ ] **Step 4: 写 2.10 整流与纹波设计（约 2,200 字）**

- 半波/全波/桥式三种整流的导通路径、二极管数量、压降、纹波频率。
- 纹波公式 `ΔV ≈ I_load / (f_ripple C)`；全波 `f_ripple=2f`。
- 电容选择四步：定负载电流 → 定允许纹波 → 算 C → 按耐压/ESR/浪涌复核。
- 峰值电流与导通角：`I_peak ≈ I_load × (T/Δt_on)`；说明为什么平均电流 1 A 的管子可能不够。
- 桥堆损耗 `P=2Vf×I_avg`；肖特基桥降低损耗但漏电更大。
- **例 2-1　整流纹波**：12 Vrms/50 Hz → 峰值约 17 V；桥式两只二极管压降约 1.4 V，空载约 15.6 V；1 A、4700 µF → 纹波 2.13 V；若目标 1 V 需 10,000 µF；校验电容耐压 ≥25 V、浪涌电流与保险丝。
- **表 2-3　整流方案对比**：半波/全波/桥式/同步整流，列二极管数、压降、纹波频率、适用场景。

- [ ] **Step 5: 写 2.11 TVS/ESD 与接口保护选型（约 2,000 字）**

- ESD 波形：IEC 61000-4-2、接触/空气放电、上升沿 <1 ns；HBM 与 IEC 不是一回事。
- TVS 六参数：`V_RWM`、`V_BR`、`V_C`、`I_PP`、`P_PP`、`C_j`；逐项解释“正常工作不导通、浪涌时钳位、不能影响信号”。
- 单向 vs 双向；信号正负摆幅决定选型。
- 限流电阻、钳位二极管、TVS 的分工；TVS 贴着接口放，地回路短。
- **例 2-2　TVS 钳位与限流电阻**：5 V 信号、绝对最大 6.5 V、IEC 8 kV/330 Ω；选 `V_RWM=5 V`、`V_C=9.2 V` TVS，前串 100 Ω；计算残压灌入 GPIO 的电流与 TVS 承受功率；结论“TVS 先泄放、电阻再限流，不能只靠一颗”。
- **图 2-2　TVS 钳位链**：接口 → TVS → 限流电阻 → 钳位二极管 → 芯片；标注浪涌路径、正常信号路径、地被弹路径。图注“先看浪涌走哪条路，再看正常信号被谁影响”。
- **表 2-4　TVS 选型检查表**：参数 / 要求 / 常见错误。

- [ ] **Step 6: 写 2.12 桥堆、保险丝与浪涌（约 1,500 字）**

- 桥堆封装、散热、浪涌电流 `I²t`；保险丝慢断/快断、额定电流降额。
- NTC 浪涌抑制、继电器/ MOSFET 旁路；上电“啪”一声的来源。
- 桥堆选型：`V_RRM ≥ 2×峰值`、`I_F(AV)` 按温升降额、`I_FSM` 扛浪涌。
- **例 2-3　二极管功耗与结温**：1 A 整流、`Vf=0.9 V`、两管导通 → 1.8 W；`RθJA=40 °C/W`、`Ta=50 °C` → `Tj=122 °C`，已接近 125 °C 上限；降额到 0.6 A 或换低 `Vf` 肖特基；校验“平均电流”与“峰值电流”不是一回事。

- [ ] **Step 7: 写 2.13 二极管故障案例（约 1,200 字）**

用“常见现象”而非虚构客户，每条给“现象 → 可能原因 → 一分钟验证”：

1. 桥式整流输出只有半波 → 一只桥臂开路 → 二极管档逐只测。
2. 纹波突然变大 → 滤波电容干涸/ESR 升高 → 看纹波形状、测电容温度。
3. 肖特基高温漏电 → 反向漏流随温度指数上升 → 热风枪局部加热看漏电。
4. 续流管失效打穿驱动管 → 关断尖峰 → 示波器抓漏极/集电极。
5. TVS 正常工作时微导通 → `V_RWM` 选低 → 测漏电与信号摆幅。

最后总结“二极管三件事：方向、压降、散热”。

- [ ] **Step 8: 图、表、速查卡与延伸阅读**

- 现有 7 张图全部改 `<figure>` + 图注；新图 2 张；图注数量 ≥7。
- 表：2-1 二极管家族、2-2 故障速查、2-3 整流方案、2-4 TVS 选型、2-5 桥堆/保险丝参数；按出现顺序编号，表前一行写表注。
- 章末加“本章速查卡”：方向、0.7 V 假设、纹波、TVS 三参数、结温。
- 延伸阅读 7 条：Sedra/Smith 微电子学二极管章；TI《TVS Diode Selection Guide》；IEC 61000-4-2 标准说明；ON Semi 整流器应用笔记；Art of Electronics 二极管节；本书第 9 章（基准）；第 13 章（电源）。不能给假文档编号。

- [ ] **Step 9: 新静态图**

`ch02-operating-map.svg`：四象限工作地图，标正向导通、反向截止、击穿、SOA；用藏青/琥珀/青，含 `<title>` `<desc>`。

`ch02-tvs-clamp.svg`：接口保护链，画 TVS 对地、限流电阻、钳位二极管、被保护芯片，用红/青两条路径区分浪涌与正常信号；底部写“TVS 先泄放，电阻再限流”。

- [ ] **Step 10: 整流 deck**

`assets/spice/ch02/rectifier.cir`：

```spice
* 第 2 章 桥式整流 + 电容滤波：10Vpk/50Hz，1000uF，200Ω
.param VP=10 F=50 C=1000u RS=1 RL=200
V1 a0 0 SIN(0 {VP} {F})
RS a0 a {RS}
D1 a out DMOD
D2 b out DMOD
D3 0 a DMOD
D4 0 b DMOD
V1b b 0 SIN(0 {VP} {F})
C1 out 0 {C}
RL out 0 {RL}
.model DMOD D(Is=1e-12 N=1 Rs=0.05 Cjo=10p)
.tran 20u 250m 0 20u
.control
run
set wr_singlescale
set wr_vecnames
wrdata rectifier.dat v(out) i(D1)
meas tran vavg AVG v(out) FROM=200m TO=250m
meas tran vmax MAX v(out) FROM=200m TO=250m
meas tran vmin MIN v(out) FROM=200m TO=250m
meas tran vripple PARAM='vmax-vmin'
meas tran ipeak MAX i(D1) FROM=200m TO=250m
print vavg vmax vmin vripple ipeak
.endc
.end
```

注意：`V1b` 与 `V1` 不能共用同一个 `0` 参考还把 `b` 短路；正确拓扑是 `V1 a0 0 SIN(...)`、`RS a0 a`、`V1b b 0 SIN(...)` 两只反相源？这会改变电路。实施时用**单只交流源跨接 a–b**，避免双源相位错误：

```spice
V1 a b SIN(0 {VP} {F})
RS a a1 {RS}
D1 a1 out DMOD
D2 b out DMOD
D3 0 a1 DMOD
D4 0 b DMOD
```

把 `a1` 作为桥的一个交流端，`b` 作为另一端；`RS` 放在源与桥之间。先在纸上画一遍节点，再写入 deck。

`assert.json`：

```json
{
  "deck": "rectifier.cir",
  "analysis": "tran",
  "data": "rectifier.dat",
  "min_rows": 2000,
  "metrics": {
    "vavg": {"expected": 8.6, "tolerance": 0.5},
    "vripple": {"expected": 0.43, "tolerance": 0.2},
    "ipeak": {"expected": 0.8, "tolerance": 0.5}
  }
}
```

容差是“教材数量级断言”，不是实测精度；CI 跑 ngspice 后若偏差超出，先检查拓扑/稳态窗口，不得为了通过把容差放大到失去意义。

- [ ] **Step 11: 追加 5 道题并更新计数**

`q-ch2-05` 至 `q-ch2-09`：

| ID | 考点 | 答案要点 |
|---|---|---|
| q-ch2-05 | 温度 | −2 mV/°C × 60°C = −120 mV |
| q-ch2-06 | 击穿 | 齐纳/雪崩都可逆但必须限流；5.1 V 钳位选合适 TVS/稳压管 |
| q-ch2-07 | 纹波电容 | 1 A、100 Hz、1 V → C=1/(100×1)=10,000 µF |
| q-ch2-08 | TVS 选型 | `V_RWM≥5.5 V`、`V_C<` 被保护脚绝对最大值、`P_PP` 足够 |
| q-ch2-09 | 结温 | 1 A×0.9 V=0.9 W；单管？两管？按实际导通管数算；40°C/W×0.9 W+40°C=76°C（单管） |

更新总题数 65→70；同步 quiz 开头与 TOC。

- [ ] **Step 12: 门禁与提交**

Run:
```bash
python -B -m unittest analog-book.tests.test_wave1_chapters.ChapterContractTests -v
python scripts/build_site.py --build
python -B -m unittest analog-book.tests.test_book_real.RealBookTests.test_chapter_exercises_and_appendix_answers -v
```
Expected: 第 2 章合同通过；70 题；无 `<details>` 残留。

```bash
git add docs/p1-03-ch2.md docs/p9-00-quiz.md docs/p0-07-toc.md \
  assets/figures/ch02-operating-map.svg assets/figures/ch02-tvs-clamp.svg \
  assets/spice/ch02 analog-book/tests/test_wave1_chapters.py \
  analog-book/tests/test_book_real.py
git commit -m "feat(book): expand chapter 2 with thermal protection and rectifier design"
```

---

### Task 4: 第 11 章扩写（18k）

**Files:**
- Modify: `docs/p2-01-ch11.md`
- Modify: `docs/p9-00-quiz.md`
- Modify: `docs/p0-07-toc.md`
- Modify: `analog-book/tests/test_book_real.py`
- Modify: `analog-book/tests/test_wave1_chapters.py`
- Create: `assets/figures/ch11-cascode.svg`
- Create: `assets/spice/ch11/diffpair.cir`
- Create: `assets/spice/ch11/assert.json`

**Interfaces:**
- Produces: `diffpair.cir` 的 `v(c1)`/`v(c2)`、直流扫描 `VCM`；后续第 12 章只引用 CMRR 结论。

- [ ] **Step 1: 追加合同（预期失败）**

```python
    11: {
        "stem": "p2-01-ch11",
        "floor": 18000,
        "sections": ("11.8", "11.9", "11.10", "11.11"),
        "examples": 3,
        "figures": 7,
        "tables": 5,
        "quiz": 10,
        "figure": "ch11-cascode.svg",
        "deck": "ch11/diffpair.cir",
    },
```

Run 并确认红。

- [ ] **Step 2: 写 11.8 有源负载与共源共栅（约 2,000 字）**

- 电阻负载的局限：要增益就得大 `Rc`，但大 `Rc` 吃掉电压余量。
- 电流源负载：直流电阻小、交流输出电阻大；增益 `Av = gm(ro_n || ro_p)`。
- cascode：共源共栅把输出电阻抬到 `gm ro²` 量级，代价是少一个 `Vds` 余量；画“两层管子叠罗汉”的直觉。
- 折叠 cascode 一句话预告，不展开偏置细节。
- **图 11-4　cascode 为什么增益高**：左边电阻负载，右边电流源/cascode 负载；标 `ro`、输出电压摆幅、增益箭头；图注“看输出电阻，不看管子数量”。
- **表 11-3　四种负载对比**：电阻、电流源、cascode、折叠 cascode；增益、余量、噪声、适用场景。
- **例 11-1　共射增益**：`gm=40 mS`、`Rc=2.2 kΩ`、`ro=50 kΩ`；`Av=-gm(Rc||ro)≈-84`；接 10 kΩ 负载后 `Av≈-68`；说明“负载会吃掉增益”。

- [ ] **Step 3: 写 11.9 CMRR/PSRR（约 1,800 字）**

- 共模增益来源：尾电流源有限输出电阻、负载失配、管子失配。
- `CMRR = |Avd/Acm|`，用 dB；单端输出与差分输出的定义不同，必须写清。
- PSRR：电源纹波到输出的传递；低频 PSRR 好不代表高频好。
- **例 11-3　差分对 CMRR**：`Avd=200`、`Acm=0.01` → CMRR=20,000=86 dB；若尾电阻从 1 MΩ 降到 100 kΩ，CMRR 掉 20 dB；说明“尾巴越大，共模越难动”。
- 表 11-4：CMRR/PSRR 的测量条件与常见误读。
- 交叉引用第 6 章运放参数，不重复 741 内部结构。

- [ ] **Step 4: 写 11.10 噪声模型与计算（约 2,000 字）**

- 热噪声 `4kTR`、散粒噪声 `2qI`、闪烁噪声 `1/f`；用“三种税”比喻。
- 输入参考噪声：把输出噪声除以增益；源电阻热噪声是下限。
- 噪声带宽：`en_rms = en × sqrt(ENBW)`；一阶系统 `ENBW=π/2 f3dB`。
- **例**：10 kΩ 电阻、300 K、1 MHz 带宽 → `12.9 µVrms`；若信号 1 mVrms，SNR≈37.8 dB；说明“先压带宽，再降源阻”。
- 不重复 11.6 已讲的噪声预算步骤；只补模型、单位和计算。
- 表 11-5：噪声源/公式/数量级/降噪手段。

- [ ] **Step 5: 写 11.11 两级放大器设计实例（约 2,000 字）**

给一个可手算的两级 NPN 放大器：

- 指标：`Av≥60 dB`、`BW≥100 kHz`、`Rin≥10 kΩ`、`Rout≤100 Ω`、单电源 12 V。
- 第一级共射：`Ic=1 mA`、`gm=38.5 mS`、`Rc=4.7 kΩ` → `Av1≈-150`（加 `ro` 后约 −130）。
- 第二级射随：`Av2≈0.95`、`Rout≈30 Ω`；总增益约 42 dB，不够 → 第一级加 cascode 或提高 `Rc`，重新分配。
- 用**表 11-6　两级预算**列指标、分配、余量、失败模式。
- 说明“增益不够不是把第二级也做成共射就完事：输出阻抗、带宽、偏置会一起反噬”。
- **例 11-2　Miller 电容与带宽**：`Cgd=5 pF`、`Av=50` → `Cin≈255 pF`；源阻 10 kΩ → 极点约 62 kHz；要 100 kHz 必须降增益/加 cascode/降源阻。

- [ ] **Step 6: 图表、速查卡、延伸阅读**

- 现有图片全部改 figure，删除重复的 `diff-pair.svg` 第二次出现或改成不同图注；图注 ≥7。
- 表 11-1 拓扑对比、11-2 差分对参数、11-3 负载对比、11-4 CMRR/PSRR、11-5 噪声、11-6 两级预算；按出现顺序编号。
- 章末速查卡：三种组态、差分对尾巴、cascode 换余量、Miller 乘法、噪声顺序。
- 延伸阅读 7 条：Gray & Meyer《Analysis and Design of Analog Integrated Circuits》差分对/电流镜章；Razavi《Design of Analog CMOS Integrated Circuits》；Sedra/Smith 放大拓扑章；TI《Op Amps for Everyone》噪声章；Art of Electronics 第 2 章；本书第 6、12 章。只写真实书名/章节主题，不写假页码。

- [ ] **Step 7: cascode 静态图**

`ch11-cascode.svg`：左右对比“电阻负载共射”和“cascode 电流源负载”；用箭头标 `ro` 提升、电压余量损失；底部公式 `Av ≈ gm·(ro_n||ro_p)` 与 `Rout ≈ gm·ro²`；含 `<title>` `<desc>`，无外部资源。

- [ ] **Step 8: 差分对 deck**

`assets/spice/ch11/diffpair.cir`：

```spice
* 第 11 章 差分对：1mA 尾电流，Rc=10k，Vid=2mV，Vcm 0→1V
.param VCC=12 VEE=-12 RC=10k ITAIL=1m
VCC vcc 0 {VCC}
VEE vee 0 {VEE}
VCM cm 0 DC 0
VD1 b1 cm DC 1m
VD2 b2 cm DC -1m
Q1 c1 b1 e QN
Q2 c2 b2 e QN
RC1 vcc c1 {RC}
RC2 vcc c2 {RC}
IEE e vee {ITAIL}
REE e vee 1Meg
.model QN NPN(Is=1e-16 BF=200 VAF=100)
.dc VCM 0 1 0.01
.control
run
set wr_singlescale
set wr_vecnames
wrdata diffpair.dat v(c1) v(c2)
meas dc vc1_0 FIND v(c1) AT=0
meas dc vc2_0 FIND v(c2) AT=0
meas dc vc1_cm FIND v(c1) AT=1
meas dc vc2_cm FIND v(c2) AT=1
print vc1_0 vc2_0 vc1_cm vc2_cm
.endc
.end
```

`assert.json`：

```json
{
  "deck": "diffpair.cir",
  "analysis": "dc",
  "data": "diffpair.dat",
  "min_rows": 50,
  "metrics": {
    "vc1_0": {"expected": 6.81, "tolerance": 0.08},
    "vc2_0": {"expected": 7.19, "tolerance": 0.08},
    "vc1_cm": {"expected": 6.805, "tolerance": 0.08},
    "vc2_cm": {"expected": 7.185, "tolerance": 0.08}
  }
}
```

先在纸上确认 NPN 电流方向与 `IEE e vee` 的符号；若 ngspice 报错，改 `IEE vee e` 并重新推导，不得凭感觉翻转。

- [ ] **Step 9: 追加 7 道题并更新计数**

`q-ch11-04` 至 `q-ch11-10`：

| ID | 考点 | 答案要点 |
|---|---|---|
| q-ch11-04 | 有源负载 | 直流压降小、交流 `ro` 大 → 单级高增益 |
| q-ch11-05 | cascode | 输出电阻约 `gm ro²`，代价是电压余量 |
| q-ch11-06 | CMRR | 200/0.01=20,000=86 dB |
| q-ch11-07 | PSRR | 60 dB=1000×，100 mV 纹波折到输入 0.1 mV |
| q-ch11-08 | 热噪声 | `sqrt(4kTRB)`，10 kΩ/1 MHz≈12.7 µVrms |
| q-ch11-09 | 两级预算 | 60 dB=1000×；第一级 40×、第二级 25× |
| q-ch11-10 | Miller | `(1+50)×5 pF=255 pF` |

更新总数 70→77；同步 quiz/TOC。

- [ ] **Step 10: 门禁与提交**

Run 合同、站点、题数检查；提交：

```bash
git add docs/p2-01-ch11.md docs/p9-00-quiz.md docs/p0-07-toc.md \
  assets/figures/ch11-cascode.svg assets/spice/ch11 \
  analog-book/tests/test_wave1_chapters.py analog-book/tests/test_book_real.py
git commit -m "feat(book): expand chapter 11 with cascode cmrr and noise"
```

---

### Task 5: 第 14 章扩写（18k）

**Files:**
- Modify: `docs/p3-01-ch14.md`
- Modify: `docs/p9-00-quiz.md`
- Modify: `docs/p0-07-toc.md`
- Modify: `analog-book/tests/test_book_real.py`
- Modify: `analog-book/tests/test_wave1_chapters.py`
- Create: `assets/figures/ch14-error-budget.svg`
- Create: `assets/figures/ch14-power-tree-timing.svg`
- Create: `assets/spice/ch14/pt100.cir`
- Create: `assets/spice/ch14/assert.json`

**Interfaces:**
- Produces: `pt100.cir` 的 `vout` 温度三点；后续第 16 章排故引用“从后往前设计、从前往后调试”。

- [ ] **Step 1: 追加合同（预期失败）**

```python
    14: {
        "stem": "p3-01-ch14",
        "floor": 18000,
        "sections": ("14.9", "14.10", "14.11", "14.12"),
        "examples": 3,
        "figures": 7,
        "tables": 6,
        "quiz": 10,
        "figure": "ch14-error-budget.svg",
        "deck": "ch14/pt100.cir",
    },
```

- [ ] **Step 2: 移动章末总结**

把 14.8 末尾的“通关打卡 / 配套视频 / 60 秒动画版”整体移到新的 14.12 之后；14.8 末尾只留“本章未完，下一节把预算、最坏情况、测试计划补全”的过渡句。删除“设计五部曲”与六步流程的计数不一致（正文写六步，打卡写五部曲），统一为“六步”。

- [ ] **Step 3: 写 14.9 指标分解与误差预算（约 1,800 字）**

- 从客户指标到可分配预算：总误差 = 传感 + 激励 + 放大 + 滤波 + ADC + 基准。
- 误差预算表的三列：误差源、典型值、对输出贡献；每一项都折算到同一单位（输入折合或输出折合）。
- **例 14-1　PT100 误差预算**：0.1°C 目标；PT100 公差、1 mA 激励误差、仪放增益误差、ADC 量化、基准温漂；给出一组假设并算出 RSS 与 WC；结论“最紧的是激励与基准，不是 ADC”。
- **图 14-8　误差瀑布**：从总预算逐项扣减，最后剩多少余量；图注“先看哪一项吃掉了最多预算”。
- **表 14-3　PT100 误差预算**：按上例列全。

- [ ] **Step 4: 写 14.10 最坏情况、容差与 Monte Carlo（约 1,800 字）**

- WC：所有项同向取极限；RSS：独立随机，平方和开根；相关项不能 RSS。
- 电阻容差、基准初始精度、温漂、负载调整率的折算。
- Monte Carlo 不是“更高级的仿真”，而是“把公差分布跑很多次”；样本数、随机种子、收敛判断。
- 用 3σ 折良率；说明“规格 = 3σ”与“规格 = WC”是两种设计哲学。
- **例 14-3　最坏情况**：三个 ±1% 项；WC=3%，RSS=1.73%；若规格 ±2%，WC 不合格、RSS 的 3σ=5.2%？不，RSS 1.73% 是 1σ 吗？这里必须统一：把每项 ±1% 当 1σ 还是极限。正确写法：每项极限 ±1%，按均匀分布折 1σ=0.577%；RSS 1σ=1.0%，3σ=3.0%。WC=3%。用这组数算，避免把极限当 σ。计划实施时以这个定义为准。
- **表 14-4　WC 与 RSS 对比**：定义、假设、结果、适用场景。
- 交叉引用 14.8 的 Buck 例子，但不重复整张表。

- [ ] **Step 5: 写 14.11 测试计划与验证（约 1,400 字）**

- 测试计划四层：电源/静态工作点、功能、精度、环境/EMC。
- 每个测试写：目的、条件、仪器、判据、失败动作。
- 首件、抽检、量产；测试点覆盖率；测试本身的不确定度。
- **表 14-5　PT100 样机测试计划**：至少 8 行（上电电流、3.3V/5V 轨、恒流值、零点、满量程、温漂、噪声、ESD/浪涌）。
- 说明“测试计划不是验证清单的堆砌，而是回答‘哪条指标最可能先坏’”。

- [ ] **Step 6: 写 14.12 完整 PT100 案例：BOM、PCB、测试（约 2,000 字）**

把 14.4 的信号链推进到可打样：

- BOM 表：PT100、基准/恒流源、仪放、运放、ADC、LDO、保护器件、连接器；列关键参数与降额。
- PCB 要点：模拟地/数字地单点连接、恒流回路面积最小、仪放输入对称、基准远离热源、测试点。
- 测试计划与失败模式：激励开路、PT100 短路、仪放饱和、ADC 基准漂移。
- **例 14-2　热设计**（把 14.5 的 LDO 例正式编号）：7 W、`θJC=2`、`θCS=1`、`Ta=40`、`Tj≤125` → `θSA≤9.1 °C/W`；校验散热器选型。
- **表 14-6　PT100 BOM 与关键降额**：至少 10 行。
- 结尾回扣“设计是从后往前推、调试是从前往后查”。

- [ ] **Step 7: 图表与延伸阅读**

- 现有 4 张图全部改 figure；删除 14.7 重复的 `power-tree.svg`，换成 `ch14-power-tree-timing.svg`（四时间尺度：ms/kHz/MHz/ns）。
- 表 14-1 预算、14-2 降额、14-3 PT100 预算、14-4 WC/RSS、14-5 测试计划、14-6 BOM；按出现顺序编号。
- 章末速查卡：六步、预算、WC/RSS、热阻链、测试点。
- 延伸阅读 7 条：Art of Electronics 第 7 章（设计实践）；TI《Analog Engineer's Pocket Reference》；TI《Op Amps for Everyone》噪声/稳定性章；IPC-2221 设计标准说明；本书第 15、16 章；LTspice 官方教程。只写真实资料，不写假页码。

- [ ] **Step 8: 静态图**

`ch14-error-budget.svg`：横向瀑布图，从 0.1°C 总预算开始，逐项扣 PT100、激励、仪放、ADC、基准，剩余绿色余量；含公式 `RSS=√Σeᵢ²`。

`ch14-power-tree-timing.svg`：四层时间尺度（大电解 ms、Buck 几十 kHz、LDO MHz、100nF ns），用四条不同频率的波形叠在电源树上；图注“每一级只负责一个时间尺度”。

- [ ] **Step 9: PT100 deck**

`assets/spice/ch14/pt100.cir`：

```spice
* 第 14 章 PT100 理想信号链：1mA 激励，增益 40，偏置 4V
.param IT=1m GAIN=40 VOFF=4
VTEMP temp 0 DC 0
IEX 0 n1 {IT}
BPT n1 0 I = V(n1)/(100*(1+0.00385*V(temp)))
EAMP amp 0 n1 0 {GAIN}
VOFF out amp DC {VOFF}
.dc VTEMP 0 100 50
.control
run
set wr_singlescale
set wr_vecnames
wrdata pt100.dat v(out) v(n1)
meas dc vout0 FIND v(out) AT=0
meas dc vout50 FIND v(out) AT=50
meas dc vout100 FIND v(out) AT=100
print vout0 vout50 vout100
.endc
.end
```

`assert.json`：

```json
{
  "deck": "pt100.cir",
  "analysis": "dc",
  "data": "pt100.dat",
  "min_rows": 3,
  "metrics": {
    "vout0": {"expected": 8.0, "tolerance": 0.15},
    "vout50": {"expected": 8.77, "tolerance": 0.15},
    "vout100": {"expected": 9.54, "tolerance": 0.15}
  }
}
```

如果 ngspice 的 `B` 源语法或 `.dc` 扫描不支持，改用三套独立电阻 + 三个 `E` 源，保持同样的断言；不要删掉温度点。

- [ ] **Step 10: 追加 7 道题并更新计数**

`q-ch14-04` 至 `q-ch14-10`：

| ID | 考点 | 答案要点 |
|---|---|---|
| q-ch14-04 | WC/RSS | 三项 ±1%：WC 3%；按均匀分布 1σ=0.577%，RSS 3σ=3% |
| q-ch14-05 | 热阻 | `Tj=50+2×20=90°C` |
| q-ch14-06 | 相关项 | 相关误差不能平方和开根，要先合并再 RSS |
| q-ch14-07 | 测试计划 | 空载/满载/纹波/温漂四类，含判据与失败动作 |
| q-ch14-08 | PT100 增益 | 38.5 mV → 1.54 V，增益 40 |
| q-ch14-09 | 公差 | 0.1% 电阻把增益误差从 1% 压到 0.1%，但成本/可得性要权衡 |
| q-ch14-10 | DFT | 测试点寄生电容会破坏高速节点，改用测试过孔/BIST |

更新总数 77→84；同步 quiz/TOC。

- [ ] **Step 11: 门禁与提交**

Run 合同、站点、题数检查；提交：

```bash
git add docs/p3-01-ch14.md docs/p9-00-quiz.md docs/p0-07-toc.md \
  assets/figures/ch14-error-budget.svg assets/figures/ch14-power-tree-timing.svg \
  assets/spice/ch14 analog-book/tests/test_wave1_chapters.py \
  analog-book/tests/test_book_real.py
git commit -m "feat(book): expand chapter 14 with budgets test plan and pt100 case"
```

---

### Task 6: 第 16 章扩写（16k）

**Files:**
- Modify: `docs/p4-01-ch16.md`
- Modify: `docs/p9-00-quiz.md`
- Modify: `docs/p0-07-toc.md`
- Modify: `analog-book/tests/test_book_real.py`
- Modify: `analog-book/tests/test_wave1_chapters.py`
- Create: `assets/figures/ch16-signal-injection.svg`
- Create: `assets/spice/ch16/probe.cir`
- Create: `assets/spice/ch16/assert.json`

**Interfaces:**
- Produces: `probe.cir` 的 `v(out1)`/`v(out2)`、上升时间；后续第 17 章引用“先静后动”。

- [ ] **Step 1: 追加合同（预期失败）**

```python
    16: {
        "stem": "p4-01-ch16",
        "floor": 16000,
        "sections": ("16.6", "16.7", "16.8", "16.9"),
        "examples": 3,
        "figures": 6,
        "tables": 6,
        "quiz": 9,
        "figure": "ch16-signal-injection.svg",
        "deck": "ch16/probe.cir",
    },
```

- [ ] **Step 2: 给 16.5 案例加免责声明**

在 16.5 开头加：

> 以下三个案例是**教学复盘场景**：现象与数字用于演示五步法，不对应真实客户，也不是仓库实测；真实排故必须用自己的测量记录替换示例数据。

这不削弱方法，反而符合证据等级。保留三个案例的结构，但把所有“某传感器板”改成“教学板 A/B/C”或明确“假设场景”。

- [ ] **Step 3: 写 16.6 探头负载与接地（约 2,000 字）**

- 探头模型：`1 MΩ ∥ 100 pF`（×1）、`10 MΩ ∥ 10~15 pF`（×10）；输入电容与源阻形成低通。
- 探头不是“旁观者”，是并联负载；高阻节点、晶振、基准、反馈节点最容易被改变。
- 地线夹的长回路：电感拾取开关磁场，形成假纹波；弹簧地针、差分探头、同轴适配器。
- **例 16-1　探头负载误差**：`Rs=100 kΩ`、×1 探头 1 MΩ∥100 pF、×10 10 MΩ∥10 pF；算直流分压 0.909/0.990 V 与 10–90% 上升时间约 20 µs/2.2 µs；结论“×10 不是礼貌，是必要”。
- **表 16-2　探头/节点匹配**：低速高阻、电源纹波、高速时钟、差分/高共模，分别选什么探头与地。

- [ ] **Step 4: 写 16.7 信号注入与二分（约 1,800 字）**

- 信号注入：在链路中点注入已知信号，观察前后级响应；注意注入源阻抗与直流偏置。
- 二分不是“随便切一半”：按信号流、按电源域、按连接器；每次测量要能排除一半。
- **例 16-2　二分定位**：16 个节点的链路，每次在中点测，4 次定位到 1 个节点；画决策表；强调“先电源后信号”。
- **图 16-3　信号注入决策树**：从“有无输出”分叉到注入点/测量点，标 4 次二分。
- **表 16-3　二分定位记录**：轮次、测量点、结果、排除范围。

- [ ] **Step 5: 写 16.8 三个案例的复盘表（约 1,600 字）**

- 用统一表头：现象、复现条件、隔离范围、根因、修复、回归、防呆。
- 把 16.5 三个教学案例填成三行；每行后加一句“如果重来，第一步做什么”。
- 强调“根因”与“触发条件”分开：根因是设计/工艺缺陷，触发条件是温度/振动/时序。
- **表 16-4　三案例复盘**。

- [ ] **Step 6: 写 16.9 可复印排故记录表（约 1,200 字）**

- 一页纸记录表字段：板号、现象、复现率、环境、电源/信号测量、假设、单变量实验、根因、修复、回归、防呆。
- 解释每个字段为什么存在；哪些字段可以空，哪些不能空。
- **表 16-5　排故记录表**（6 列以内；宽表拆两张）。
- 结尾“记录不是给领导看的，是给三个月后的自己看的”。

- [ ] **Step 7: 图表、速查卡、延伸阅读**

- 现有 5 张图全部改 figure；新图 `ch16-signal-injection.svg`；图注 ≥6。
- 表 16-1 测量检查表、16-2 探头匹配、16-3 二分记录、16-4 案例复盘、16-5 记录表、16-6 常见假象；按顺序编号。
- 章末速查卡：五步、单变量、探头负载、二分、记录。
- 延伸阅读 6 条：Jim Williams《Analog Circuit Design》相关章节；Art of Electronics 第 12 章（测量）；Tektronix 探头应用笔记；Fluke 万用表安全指南；本书第 14、17 章。只写真实资料。

- [ ] **Step 8: 信号注入静态图**

`ch16-signal-injection.svg`：一条传感器→放大→滤波→ADC 链路，标四个注入/测量点；用琥珀箭头标“注入”，青色箭头标“测量”，底部“每测一次，砍掉一半”。含 `<title>` `<desc>`，无外部资源。

- [ ] **Step 9: 探头 deck**

`assets/spice/ch16/probe.cir`：

```spice
* 第 16 章 探头负载：源阻 100k，×1=1M||100p，×10=10M||10p
.param VS=1 RS=100k
V1 in1 0 PULSE(0 {VS} 0 1n 1n 10m 20m)
RS1 in1 out1 {RS}
RP1 out1 0 1Meg
CP1 out1 0 100p
V2 in2 0 PULSE(0 {VS} 0 1n 1n 10m 20m)
RS2 in2 out2 {RS}
RP2 out2 0 10Meg
CP2 out2 0 10p
.tran 0.1u 100u 0 0.1u
.control
run
set wr_singlescale
set wr_vecnames
wrdata probe.dat v(out1) v(out2)
meas tran vfinal1 FIND v(out1) AT=90u
meas tran vfinal2 FIND v(out2) AT=90u
meas tran trise1 TRIG v(out1) VAL=0.09 RISE=1 TARG v(out1) VAL=0.82 RISE=1
meas tran trise2 TRIG v(out2) VAL=0.099 RISE=1 TARG v(out2) VAL=0.891 RISE=1
print vfinal1 vfinal2 trise1 trise2
.endc
.end
```

`assert.json`：

```json
{
  "deck": "probe.cir",
  "analysis": "tran",
  "data": "probe.dat",
  "min_rows": 200,
  "metrics": {
    "vfinal1": {"expected": 0.909, "tolerance": 0.01},
    "vfinal2": {"expected": 0.990, "tolerance": 0.005},
    "trise1": {"expected": 0.000020, "tolerance": 0.000005},
    "trise2": {"expected": 0.0000022, "tolerance": 0.0000006}
  }
}
```

- [ ] **Step 10: 追加 6 道题并更新计数**

`q-ch16-04` 至 `q-ch16-09`：

| ID | 考点 | 答案要点 |
|---|---|---|
| q-ch16-04 | ×10 探头 | 10 MΩ 分压误差约 1%，输入电容 10 pF 把带宽拉高 |
| q-ch16-05 | 二分 | 16 节点 → 4 次（2⁴=16） |
| q-ch16-06 | 信号注入 | 注入点要考虑源阻抗/偏置，不能把电路拖死 |
| q-ch16-07 | 地环路 | 长地夹拾取磁场 → 弹簧地针/差分探头 |
| q-ch16-08 | 记录 | 现象、复现条件、测量、假设、单变量、根因、回归、防呆 |
| q-ch16-09 | 复盘 | 根因 ≠ 触发条件；修复要能防再发 |

更新总数 84→90；同步 quiz/TOC，并把 quiz 开头阈值表改为 70~90 / 47~69 / 0~46。

- [ ] **Step 11: 门禁与提交**

Run 合同、站点、题数检查；提交：

```bash
git add docs/p4-01-ch16.md docs/p9-00-quiz.md docs/p0-07-toc.md \
  assets/figures/ch16-signal-injection.svg assets/spice/ch16 \
  analog-book/tests/test_wave1_chapters.py analog-book/tests/test_book_real.py
git commit -m "feat(book): expand chapter 16 with probe loading and injection"
```

---

### Task 7: 全量测试、字体、SPICE 与文档同步

**Files:**
- Modify: `analog-book/tests/test_spice.py`
- Modify: `analog-book/tests/test_book_real.py`
- Modify: `analog-book/book/fonts.py`
- Create: `scripts/test_figures.py`
- Regenerate: `analog-book/fonts/*.woff2`（按脚本输出）
- Regenerate: `README.md`（如脚本产生变化）

- [ ] **Step 1: 写静态图验收**

创建 `scripts/test_figures.py`：

```python
#!/usr/bin/env python3
"""静态技术插图：有效性、离线、配色、标题/描述与正文引用。"""
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "assets" / "figures"
DOCS = ROOT / "docs"
EXPECTED = {
    "ch00-controlled-sources.svg",
    "ch02-operating-map.svg",
    "ch02-tvs-clamp.svg",
    "ch11-cascode.svg",
    "ch14-error-budget.svg",
    "ch14-power-tree-timing.svg",
    "ch16-signal-injection.svg",
}
PALETTE = {"#14213d", "#b45309", "#0f766e"}


class FigureTests(unittest.TestCase):
    def test_expected_figures_exist(self):
        present = {path.name for path in FIGURES.glob("*.svg")}
        self.assertEqual(EXPECTED, present)

    def test_svgs_are_offline_labelled_and_colour_locked(self):
        for name in sorted(EXPECTED):
            path = FIGURES / name
            text = path.read_text(encoding="utf-8")
            root = ET.fromstring(text)
            self.assertTrue(root.tag.endswith("svg"), name)
            self.assertTrue(root.get("viewBox"), name)
            self.assertNotIn("<script", text.lower(), name)
            self.assertNotIn("<image", text.lower(), name)
            self.assertNotIn("http", text.lower(), name)
            self.assertRegex(text, r"<title>.+</title>", name)
            self.assertRegex(text, r"<desc>.+</desc>", name)
            self.assertGreaterEqual(text.count("<text"), 6, name)
            self.assertTrue(any(colour in text.lower() for colour in PALETTE), name)

    def test_each_figure_is_wrapped_in_a_figure_with_caption(self):
        docs = "\n".join(p.read_text(encoding="utf-8") for p in DOCS.glob("*.md"))
        for name in sorted(EXPECTED):
            pattern = rf'<figure[^>]*>.*?assets/figures/{re.escape(name)}.*?</figure>'
            self.assertRegex(docs, pattern, name)
```

Run: `python -B -m unittest scripts.test_figures -v`
Expected: PASS（若字体新字形未覆盖，先继续，Step 4 处理）。

- [ ] **Step 2: 更新 SPICE 测试为 6 套并逐套运行**

把 `test_discovers_the_rc_case` 改成：

```python
EXPECTED_CASES = {
    "ch00/divider.cir", "ch01/rc.cir", "ch02/rectifier.cir",
    "ch11/diffpair.cir", "ch14/pt100.cir", "ch16/probe.cir",
}

def test_discovers_all_six_wave1_cases(self):
    cases = run_spice.discover_cases()
    paths = {case.deck.relative_to(ROOT / "assets" / "spice").as_posix()
             for case in cases}
    self.assertEqual(EXPECTED_CASES, paths)
    for case in cases:
        self.assertIn(case.deck.name, case.spec["deck"])
```

`SimulationTests` 改为在 `setUpClass` 循环全部 case，`results` 字典按相对路径保存；`test_metrics_match`、`test_data_is_written_and_monotonic` 逐套断言。保留 `test_plot_is_generated_from_simulation_data` 只针对 `ch01/rc.cir`，避免为每套 deck 重复制图。

- [ ] **Step 3: 把字数下限写进真实构建测试**

在 `test_book_real.py` 加：

```python
def test_wave1_chapter_word_floors(self):
    floors = {"0": 15000, "2": 16000, "11": 18000,
              "14": 18000, "16": 16000}
    chapters = self.model["stats"]["chapters"]
    for chapter, floor in floors.items():
        self.assertGreaterEqual(
            chapters[chapter]["chars"], floor,
            f"第 {chapter} 章实际 {chapters[chapter]['chars']}，低于 {floor}")
```

同时把题目断言从 58 改为 90（若前面已逐章改到 90，这里只做最终确认）。

- [ ] **Step 4: 字体扫描扩展到静态图并重建子集**

在 `fonts.required_text()` 中把：

```python
for path in sorted((config.ROOT / "assets" / "svg").rglob("*.svg")):
```

后面补：

```python
figures = config.ROOT / "assets" / "figures"
if figures.is_dir():
    for path in sorted(figures.rglob("*.svg")):
        chunks.append(html.unescape(re.sub(r"<[^>]+>", " ", path.read_text(
            encoding="utf-8", errors="replace"))))
```

Run:
```bash
python scripts/subset_fonts.py --build
python -B -m unittest analog-book.tests.test_book_fonts -v
```
Expected: 新图与正文的汉字全部覆盖；若缺字，回到对应内容补字后重跑，不得手改 WOFF2。

- [ ] **Step 5: 更新文档计数与 README**

- 确认 `docs/p9-00-quiz.md` 为 90 题、阈值表为 70~90 / 47~69 / 0~46。
- 确认 `docs/p0-07-toc.md` 为“19 章 90 题 + 34 道专题加练”。
- 运行 `python scripts/build_readme.py`；若 README 变化，一并提交。

- [ ] **Step 6: 跑全量测试**

Run:
```bash
python -B -m unittest discover -s analog-book/tests -v
python -B -m unittest discover -s scripts -v
ruff check analog-book scripts
```
Expected: 所有非 SPICE 运行测试通过；`test_spice.SimulationTests` 在无 ngspice 的机器上 skip，必须记录为 **CI-only**，不得写成“已通过 ngspice 验证”。

- [ ] **Step 7: 提交**

```bash
git add analog-book/tests/test_spice.py analog-book/tests/test_book_real.py \
  analog-book/book/fonts.py analog-book/fonts scripts/test_figures.py \
  docs/p9-00-quiz.md docs/p0-07-toc.md README.md
git commit -m "test(book): gate wave one content assets and fonts"
```

---

### Task 8: 16K 重建、视觉审计与最终验收

**Files:**
- Modify: 无（只生成 `build/` 下产物与报告；必要时修 CSS/内容后回到对应任务）

- [ ] **Step 1: 构建站点与完整 16K**

```bash
python scripts/build_site.py --build
python analog-book/build_print_book.py --sample
python analog-book/build_print_book.py --pdf --cover
python analog-book/build_print_book.py --no-build --report
```

Expected:
- 内文 PDF 页数为 4 的倍数；
- 目录/索引无 `000`；
- 封面书脊 = `pages / 2 × 0.10 + 1.0` mm；
- 内文 MediaBox 在 185×260 mm ±0.5 mm；
- 报告显示 `draft`，没有新增 error。

- [ ] **Step 2: 视觉审计**

用 PyMuPDF 渲染以下页面到 `build/visual-audit/`：

- 第 0 章章首页与含图页；
- 第 2 章 TVS/整流图页；
- 第 11 章 cascode 图页；
- 第 14 章预算图页；
- 第 16 章注入图页；
- 目录、插图目录、索引各一页。

检查清单：
- 章首舞台没有把首段挤到下一页，或留下 >35 mm 空白；
- 图框不跨页、图注不孤行；
- 表头跨页重复，宽表不溢出；
- 图注编号连续、与插图目录一致；
- 黑底/深色图不糊，白底图不脏；
- 没有 emoji、`<details>`、站点按钮或视频播放器残留。

- [ ] **Step 3: 全量回归（最终）**

```bash
python -B -m unittest discover -s analog-book/tests -v
python -B -m unittest discover -s scripts -v
ruff check analog-book scripts
```

Expected: 全绿（SPICE 运行测试在无 ngspice 时 skip，记录 CI-only）。

- [ ] **Step 4: 更新 ledger 并提交**

在 `.superpowers/sdd/2026-10-25-print-book-phase0/progress.md` 追加 Wave 1 完成记录、实际页数、书脊、字体重建时间、SPICE CI-only 状态。

```bash
git status --short
git add docs/p1-01-ch0.md docs/p1-03-ch2.md docs/p2-01-ch11.md \
  docs/p3-01-ch14.md docs/p4-01-ch16.md docs/p9-00-quiz.md docs/p0-07-toc.md \
  assets/figures assets/spice analog-book/styles/print.css \
  scripts/site_media/typography.css analog-book/book/fonts.py \
  analog-book/fonts analog-book/tests scripts/test_figures.py README.md \
  .superpowers/sdd/2026-10-25-print-book-phase0/progress.md
git commit -m "feat(book): finish wave one content and rebuild 16k edition"
```

**不推送。** 如未来获得推送指令，先按仓库约定跑安全审查门；发现问题先修复。

---

## Self-Review

- **Spec coverage:** §6.3 的 15k/16k/18k 字数、3 算例、1 仿真、8–12 题、6–8 阅读、4 图表；§6.5 五章逐节蓝图；§6.6 的语言、图表、公式、证据等级均落到任务。
- **No placeholders:** 每个新节都给了主题、公式、算例数字、图表内容与验收方式；未写“待补/自行发挥”。
- **Type consistency:** `vout_open/vout_load/i_load`、`vc1_0/vc2_0/vc1_cm/vc2_cm`、`vfinal1/vfinal2/trise1/trise2` 在 deck、assert 与正文例子中同名。
- **Known risk:** 本地无 ngspice，五套新 deck 只能做语法/拓扑审查，最终由 CI 安装 ngspice 验证；不得宣称已实测。整流 deck 的 `ipeak` 与 PT100 的 `B` 源语法风险最高，若 CI 失败，先修拓扑/模型，再看是否调整容差。
