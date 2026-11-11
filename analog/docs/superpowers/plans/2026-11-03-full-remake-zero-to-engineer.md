# 整包重做：零基础到工程师 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **执行状态（2026-11-04，机器可验快照）**：Task 0–12、11b、11c、14、15 已完成并逐项提交；`make remake-ship` 六项残余扫描全绿（契约 19/19、套话零命中、引用库闸、SVG 153≥150、双源探测、五线数值抽检），print-volumes 双卷已重建。Task 13 已完成旁白默认音色/音高契约、20 集数值对齐审计（3 处修正）以及 EP01–20 横竖版全量重渲；72 项视频测试全绿，40 个发布成片均已生成。当前唯一实施缺口是静止闸：`check_still` **32/40 PASS、8 FAIL**，失败为 EP01 竖版，以及 EP01/02/05/06/14/19/20 横版，详见 Task 13R。故整包状态仍是 **实施中 / 不可发布**；不得把“文件已生成”写成“视频线已完成”。push、Pages 部署、社媒实际发布与 ship-gate 人工签字继续冻结。

> **后续视觉计划**：用户于 2026-11-04 复审后否决当前书籍视觉质量。本计划不再代表全部剩余工作；插图密度、图替繁文和 153 张旧动画的彻底改造，转入 `docs/superpowers/plans/2026-11-04-visual-first-book-overhaul.md`。新 spec 未 Accepted 前不提交推送。

**Goal:** 按已通过的整包重做 spec，把「通往模拟电路之路」推倒重写成 docs 单源教材，再同源派生站点、离线书、视频与社媒，清单勾完即可出片出书上架。

**Architecture:** 唯一内容源仍是 `docs/*.md`（保留 ch0–18 文件名与 `#chN` 锚点）。先锁教学地图、章节契约与 FA-029 视觉 DNA，再打穿样板章（ch1 + ch16），按 A→B→C→D 段波次重写全书；脚本侧只改 `handraw.py` / `generate_svgs.py` / 视频旁白默认音色等派生管线，禁止手改 `assets/svg/` 产物。每阶段以可运行的 unittest / make 目标为出口闸。

**Tech Stack:** Python 3、Markdown + MkDocs Material、`scripts/handraw.py`（FA-029）、`scripts/generate_svgs.py`、`scripts/build_readme.py` / `build_site.py`、`analog-book/` 离线与印刷管线、Remotion + `video/director.py` / `narrate.py` / `master.py`（edge-tts）、unittest、Playwright（浏览器回归）、ruff（可选）。

**Spec（权威）:** `docs/superpowers/specs/2026-11-03-full-remake-zero-to-engineer-design.md`（用户已批准，含 **附录 A** 动画加量 + 资料加厚；实施前将状态改为 Accepted）

## Global Constraints

- 打法 A：先按章节契约重写 `docs/*.md`（唯一内容源），再派生站点 / 离线书 / 视频 / 社媒；未完成①不得宣称②–⑤「终态上架」。
- `docs/` 是唯一数据源；禁止直接改 `README.md`；改完必须重跑 `python scripts/build_readme.py`（CI 比对漂移即红灯）。
- `assets/svg/` 必须 == `scripts/generate_svgs.py` 输出；改图先改脚本再重生，禁止只改 SVG 不回灌。
- 不新开第二套章节编号；不落地、不复活 2026-10-26「书稿优先独立中文树」双源。
- 对外稳定锚点 `#chN` / `#partN` 规则仍遵守 `CONTRIBUTING.md`；允许章内小节重排，不允许平行章号。
- 手绘 = FA-029 Geometric Diagrammatic Narrative（精密几何图示叙事），不是卡通；不用 `feTurbulence` 抖线滤镜。
- 视觉 token 锁死：纸 C-30 `#fdf8ea`；墨 C-31 `#16202b`；标记 C-29 `#a4630f`；规范见 `analog-book/HANDRAW-STYLE.md` + `scripts/handraw.py`。
- 文风通篇按 `D:\Users\monidianlu\humanizer-zh.md` 重写；非白名单「不是…而是」清零；禁止编造亲身经历。
- 无出处 → 不写死数字；教学示意须标明「示意」；区分典型值与保证值。
- 继承 v3.90 / SPEC-V4：图前提问、图后含数字读图指引、打印版保留动画叙事关键帧；不回退其验收。
- 五线平权：同一章共享标题语义、口诀卡、主图隐喻、关键数值、验收清单；只改编幅与密度。
- 视频 TTS 默认（可被用户改口覆盖）：`edge-tts` `zh-CN-XiaoxiaoNeural`，语速 −5%，音高 −4Hz。
- 本地小步提交，不推送远程；构建产物只写 `build/`、`analog-book/dist/` 等约定目录。
- 缺验收项、无出处死数字、画风漂移、残留 AI 套话 → 硬挡，不得宣称整包完成。
- 手绘原理动画**大幅扩量**：在现有约 118 张 `assets/svg/` 之上，经 `scripts/generate_svgs.py` + `scripts/handraw.py` 新增 FA-029 气质动画（目标见 Task 11b；宁可精准多图，禁止卡通化/涂鸦风）。
- 官方与开源引用扩容：每章关键数字/选型优先锚定 ADI/TI 等 datasheet 与应用笔记；另建策展 `references.yml`（GitHub OSS + 厂商文档），章内引用可回溯；杨建国式教学法仅作可选阅读标注，不替代官方参数源。
- Approach A 与既有单源/锚点/五线平权约束全部保留，不因扩动画或扩引用而改打法。

## File Structure（本轮计划锁死的责任边界）

| 路径 | 责任 |
|---|---|
| `docs/superpowers/curriculum/2026-11-03-zero-to-engineer-map.md` | 四段主线 ↔ ch0–18 地图 + 过关像什么 |
| `docs/superpowers/templates/chapter-contract.md` | 章节六槽 + 四件套模板 |
| `docs/superpowers/templates/humanizer-whitelist.md` | 允许保留的工程对比白名单 |
| `docs/superpowers/checklists/ship-gate.md` | §10 五线清单可勾选副本 |
| `scripts/check_chapter_contract.py` | 结构槽 / 口诀 / 数值例 / 验收清单静态扫描 |
| `scripts/check_ai_slop.py` | 非白名单套话扫描（「不是…而是」等） |
| `scripts/test_chapter_contract.py` | 合同测试 |
| `scripts/test_ai_slop.py` | 套话闸测试 |
| `docs/p1-02-ch1.md` … `docs/p4-03-ch18.md` | 正文唯一源（波次重写） |
| `docs/p8-11-s8-11.md` | 十九章口诀总表同源登记 |
| `analog-book/HANDRAW-STYLE.md` / `scripts/handraw.py` | FA-029 DNA（只确认/小补，不换肤） |
| `scripts/generate_svgs.py` | 动画气质迁移入口 |
| `video/narrate.py` | TTS 默认改 XiaoxiaoNeural −5%/−4Hz |
| `video/shots/*.json` + `video/episodes/` | 分镜与旁白随章重写 |
| `docs/superpowers/templates/social-slice.md` | 三平台切片模板 |
| `analog-book/data/references.yml` | 既有参考文献库：**扩编**厂商笔记 + OSS + 可选教法（勿破坏既有 id 规则） |
| `analog-book/data/sources.yml` | 事实源/出处索引（当前近空）：扩编为可追溯源 |
| `docs/superpowers/references/oss-animation-candidates.md` | 动画相关 OSS 候选评估（许可 + 是否贴合 FA-029） |
| `docs/superpowers/templates/chapter-citations.md` | 每章官方引用勾选清单模板 |
| `scripts/check_references.py` / `test_references.py` | 引用库 schema 与章内回溯闸 |
| `scripts/generate_svgs.py` 新增主题函数 | 动画扩量唯一入口（禁止手改产物） |
| `docs/p5-00-part5.md` 等动画中心页 | 画廊索引随新 SVG 回填；文案「118」改为动态计数 |

## Scope And Non-goals

**Scope:** 工具链引用与闸脚本；教学地图；章节契约；样板 ch1+ch16；全书 ch0–18 按段重写；口诀总表与题库同步；站点/书重建；SVG 气质批迁移；**手绘动画大幅扩量（>现网约 118）**；**references.yml 策展与每章官方引用清单**；视频与社媒模板及首波可出片资产；总闸自动化。

**Non-goals:** 不推远程；不另起章号；不引入双源书稿树；不把原理图卡通化；不把自测分宣传成独立设计认证；不锁印刷供应商与首刷册数；不在本计划正文里写完整章节内容。

---

## 执行台账（2026-11-04）

本表是当前状态权威；下方各 Task 的 `- [ ]` 保留为可复用执行步骤，不再以逐框回填代表历史完成度。状态变化必须同时写清证据与未过闸原因。

| 范围 | 状态 | 可验事实 | 下一动作 |
|---|---|---|---|
| Task 0–10 | 完成 | Accepted spec、19 章契约重写、humanizer 与 docs 派生均已提交 | 无 |
| Task 11 / 11b | 完成 | SVG 生成器单源；动画 118→153，数量闸 ≥150 | 无 |
| Task 11c | 完成 | references/sources、章引用模板与校验闸已提交 | 无 |
| Task 12 | 完成 | 离线书与印刷双卷重建，双源探测通过 | 无 |
| Task 13 | **进行中** | 20 集横竖版均已生成；72 项视频测试 PASS；`check_still` 32/40 PASS | 执行 Task 13R，修复 8 个失败成片并全量复验 |
| Task 14–15 | 完成 | 三平台模板、`remake-ship` 与发布冻结规则已提交 | 待视频线过闸后人工签字 |
| 对外发布 | 冻结 | 尚有 8 个视频静止闸失败 | 不 push、不部署、不宣称整包完成 |

---

### Task 0: 工具链引用、spec 状态与闸脚本骨架

**Files:**
- Modify: `docs/superpowers/specs/2026-11-03-full-remake-zero-to-engineer-design.md`（状态 → Accepted）
- Create: `docs/superpowers/checklists/ship-gate.md`
- Create: `docs/superpowers/agent-refs/README.md`
- Create: `scripts/check_ai_slop.py`
- Create: `scripts/check_chapter_contract.py`
- Create: `scripts/test_ai_slop.py`
- Create: `scripts/test_chapter_contract.py`
- Modify: `Makefile`（增加 `remake-check` 目标）

**Interfaces:**
- Consumes: 已批准 spec；`D:\Users\monidianlu\humanizer-zh.md`；https://github.com/yang0/handraw-style ；`analog-book/HANDRAW-STYLE.md`
- Produces: `check_ai_slop.scan_text(text, whitelist) -> list[tuple[int,str]]`；`check_chapter_contract.scan_chapter(path) -> dict`（keys: slots/motto/hero_fig/numeric_example/acceptance）；`make remake-check`

- [ ] **Step 1: 把 spec 状态改为 Accepted**

将文件头状态行改为：

```markdown
- **状态**：Accepted（用户 2026-11-03 确认；实施以本文件 + `docs/superpowers/plans/2026-11-03-full-remake-zero-to-engineer.md` 为准）
```

文末改为「已 Accepted；实施计划见同日 plans 文件。」

- [ ] **Step 2: 写 agent 引用清单**

创建 `docs/superpowers/agent-refs/README.md`，表列：humanizer-zh 本机路径、yang0/handraw-style URL、HANDRAW-STYLE.md、handraw.py、humanizer-whitelist.md。不把大 skill 原文复制进仓。

- [ ] **Step 3: 写失败测试 `scripts/test_ai_slop.py`**

```python
#!/usr/bin/env python3
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_ai_slop  # noqa: E402


class AiSlopTests(unittest.TestCase):
    def test_flags_fake_contrast(self):
        hits = check_ai_slop.scan_text("这不是电阻，而是电感。", whitelist=[])
        self.assertTrue(hits)

    def test_allows_whitelisted_engineering_contrast(self):
        wl = ["开环 ≠ 闭环"]
        hits = check_ai_slop.scan_text("记住：开环 ≠ 闭环。", whitelist=wl)
        self.assertEqual(hits, [])

    def test_flags_empty_outro(self):
        hits = check_ai_slop.scan_text("总而言之，值得注意的是我们在本章中我们将继续前进。", whitelist=[])
        self.assertTrue(hits)
```

- [ ] **Step 4: 运行确认红**

Run: `python -B -m unittest discover -s scripts -p test_ai_slop.py -v`  
Expected: FAIL / ImportError（模块尚不存在）

- [ ] **Step 5: 实现 `scripts/check_ai_slop.py`**

```python
#!/usr/bin/env python3
from __future__ import annotations
import argparse
import re
from pathlib import Path

FAKE_CONTRAST = re.compile(r"不是[^。；\n]{0,40}而是|与其说[^。；\n]{0,40}不如说")
EMPTY_PHRASES = ("值得注意的是", "在本章中我们将", "综上所述", "总而言之，")


def scan_text(text: str, whitelist: list[str]) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        if any(w and w in line for w in whitelist):
            continue
        if FAKE_CONTRAST.search(line):
            hits.append((i, line.strip()))
        for p in EMPTY_PHRASES:
            if p in line:
                hits.append((i, line.strip()))
    return hits


def load_whitelist(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [ln[2:].strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.startswith("- ")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--whitelist", type=Path,
                    default=Path("docs/superpowers/templates/humanizer-whitelist.md"))
    args = ap.parse_args()
    wl = load_whitelist(args.whitelist)
    code = 0
    for p in args.paths:
        for ln, s in scan_text(p.read_text(encoding="utf-8"), wl):
            print(f"{p}:{ln}: {s}")
            code = 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: 实现 `scripts/check_chapter_contract.py` + `test_chapter_contract.py`**

`scan_chapter(path) -> dict` 布尔字段：

- `slots`: 文中出现六类标记（`<!-- slot:hook -->` … `<!-- slot:selfcheck -->`）或中文槽位标题（钩子/现象、直觉、定量、失效|边界、动手|验证、自检）
- `motto`: 存在 `> **口诀**` 或 `> **一点就懂**`
- `hero_fig`: 引用 `assets/figures/` 或 `assets/svg/` 且存在图问（`> **图问**` 或紧邻问句）
- `numeric_example`: 存在 `**算一笔**` 或含单位的算式段
- `acceptance`: 存在 `### 验收清单` 且其下至少两个 `- [ ]`

测试：临时合格 fixture 全 True；空文件全 False。

- [ ] **Step 7: 复制 ship-gate**

将 spec §10.1–10.6 原文 checkbox 抄入 `docs/superpowers/checklists/ship-gate.md`，文首声明「任一线未完不得宣称整包完成」。

- [ ] **Step 8: Makefile 增加目标**

```makefile
remake-check:
	$(PY) -B -m unittest discover -s scripts -p 'test_ai_slop.py' -v
	$(PY) -B -m unittest discover -s scripts -p 'test_chapter_contract.py' -v
```

- [ ] **Step 9: 跑绿本任务测试**

Run: `python -B -m unittest discover -s scripts -p 'test_ai_slop.py' -v`  
Expected: PASS  
Run: `python -B -m unittest discover -s scripts -p 'test_chapter_contract.py' -v`  
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add docs/superpowers/specs/2026-11-03-full-remake-zero-to-engineer-design.md \
  docs/superpowers/checklists/ship-gate.md docs/superpowers/agent-refs/README.md \
  scripts/check_ai_slop.py scripts/check_chapter_contract.py \
  scripts/test_ai_slop.py scripts/test_chapter_contract.py Makefile
git commit -m "chore: 整包重做闸脚本与 Accepted spec 状态"
```

---

### Task 1: 教学主线地图（四段 ↔ ch0–18）

**Files:**
- Create: `docs/superpowers/curriculum/2026-11-03-zero-to-engineer-map.md`
- Create: `docs/superpowers/templates/acceptance-chapter.md`
- Create: `docs/superpowers/templates/acceptance-design-note.md`
- Modify: `scripts/test_chapter_contract.py`

**Interfaces:**
- Consumes: spec §5.2；现有 19 章 `docs/p*-ch*.md`
- Produces: 完整枚举的章列表；章末验收模板；设计说明五块模板（指标/选型/极限/测试/失败预案）

- [ ] **Step 1: 写地图文件（必须枚举全部 19 个文件名，禁止省略号）**

`docs/superpowers/curriculum/2026-11-03-zero-to-engineer-map.md`：

```markdown
# 零基础 → 工程师 · 教学地图（2026-11-03）

## 认知节奏（每章强制）
现象 → 直觉 → 定量 → 边界/失效 → 动手验证 → 章末自检

## 四段映射

### A 地基
- `p1-01-ch0.md` 电路直觉
- `p1-02-ch1.md` 无源
- `p1-03-ch2.md` 二极管
过关：能画回路、估数量级、解释二极管压降与限流

### B 有源与接口
- `p1-04-ch3.md` BJT
- `p1-05-ch4.md` MOSFET
- `p1-06-ch5.md` 推挽/开漏
- `p1-07-ch6.md` 运放
- `p1-08-ch7.md` 比较器
- `p1-09-ch8.md` 模拟开关
过关：读懂开关/放大角色，算简单偏置，分清推挽与开漏

### C 电路族与系统
- `p1-10-ch9.md` 基准与稳压（文件在器件篇，教学段归 C）
- `p1-11-ch10.md` 555
- `p2-01-ch11.md` 放大拓扑
- `p2-02-ch12.md` 运放应用族
- `p2-03-ch13.md` 电源与信号
- `p3-01-ch14.md` 设计方法
- `p3-02-ch15.md` PCB/地
过关：能选拓扑、算关键 RC、标出地回流与去耦；ch14 能写设计说明草稿

### D 排故与独立设计
- `p4-01-ch16.md` 排故五步
- `p4-02-ch17.md` 故障速查
- `p4-03-ch18.md` 大师智慧 + 贯穿设计作业
过关：五步收敛故障；交出设计说明五块齐全

## 导航篇（改链不改章号）
`p0-06-roadmap.md` `p0-09-diagnostic.md` `p0-08-cheatsheet.md` `p0-10-model-limits.md` `p8-11-s8-11.md` `p9-00-quiz.md`
```

- [ ] **Step 2: 写 `acceptance-chapter.md` 与 `acceptance-design-note.md`**

章末三条（观察/计算/测量，至少勾两条可过关）。设计说明五块原样拷贝 spec §4.2 表。

- [ ] **Step 3: 测试断言地图含 19 文件名**

```python
def test_curriculum_map_lists_all_19_chapter_files(self):
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/superpowers/curriculum/2026-11-03-zero-to-engineer-map.md").read_text(encoding="utf-8")
    for name in [
        "p1-01-ch0.md", "p1-02-ch1.md", "p1-03-ch2.md", "p1-04-ch3.md", "p1-05-ch4.md",
        "p1-06-ch5.md", "p1-07-ch6.md", "p1-08-ch7.md", "p1-09-ch8.md", "p1-10-ch9.md",
        "p1-11-ch10.md", "p2-01-ch11.md", "p2-02-ch12.md", "p2-03-ch13.md", "p3-01-ch14.md",
        "p3-02-ch15.md", "p4-01-ch16.md", "p4-02-ch17.md", "p4-03-ch18.md",
    ]:
        self.assertIn(name, text)
```

- [ ] **Step 4: 运行**

Run: `python -B -m unittest discover -s scripts -p 'test_chapter_contract.py' -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/curriculum/2026-11-03-zero-to-engineer-map.md \
  docs/superpowers/templates/acceptance-chapter.md \
  docs/superpowers/templates/acceptance-design-note.md \
  scripts/test_chapter_contract.py
git commit -m "docs: 零基础到工程师教学地图与验收模板"
```

---

### Task 2: 章节契约模板 + humanizer 白名单

**Files:**
- Create: `docs/superpowers/templates/chapter-contract.md`
- Create: `docs/superpowers/templates/humanizer-whitelist.md`
- Modify: `scripts/check_chapter_contract.py`（识别 `<!-- slot:* -->`）

**Interfaces:**
- Consumes: spec §6 §7；`D:\Users\monidianlu\humanizer-zh.md`
- Produces: 可复制骨架；白名单条目供 `load_whitelist`

- [ ] **Step 1: 写入 `chapter-contract.md` 固定骨架**

顺序与标记必须如下（N 为章号占位）：

1. `<a id="chN"></a>` + `## 第 N 章 …` + 场景/难度/白话/先修/学完你应能
2. `<!-- slot:hook -->` + 钩子现象节
3. `<!-- slot:intuition -->` + 直觉节
4. `<!-- slot:quant -->` + 定量节 + `> **口诀**：`
5. `<!-- slot:limits -->` + 失效边界节
6. `<!-- slot:lab -->` + 动手验证 + `<figure>` hero（`assets/figures/chNN-hero.svg`）+ `> **图问**：` + `**算一笔**：`
7. `<!-- slot:selfcheck -->` + 自检 + `### 验收清单`（三个 `- [ ]`）
8. 可选 `<!-- slot:advanced -->` 进阶框
9. `### 参考与出处`（或 `<!-- slot:citations -->`）：至少 1 条可核对的厂商文档/应用笔记或已登记 OSS；示意数字标明「示意」

- [ ] **Step 2: 写 `humanizer-whitelist.md`**

默认条目（整行放行子串）：

- 开环 ≠ 闭环
- 典型值 / 保证值
- 典型值与保证值
- 推挽 / 开漏
- 推挽与开漏
- 示意 / 实测
- 示意与实测
- 理想模型 / 实物
- 静态 / 动态

规则：新增真工程对比必须先改白名单再写正文。

- [ ] **Step 3: 扫描模板自身**

Run: `python scripts/check_ai_slop.py docs/superpowers/templates/chapter-contract.md`  
Expected: exit 0

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/templates/chapter-contract.md \
  docs/superpowers/templates/humanizer-whitelist.md \
  scripts/check_chapter_contract.py
git commit -m "docs: 章节契约模板与 humanizer 白名单"
```

---

### Task 3: 视觉 DNA 锁定

**Files:**
- Create: `docs/superpowers/visual/2026-11-03-dna-lock.md`
- Create: `docs/superpowers/visual/anim-migration-notes.md`
- Default: **不改** `scripts/handraw.py` / `HANDRAW-STYLE.md`（仅核对）

**Interfaces:**
- Consumes: `handraw.LIGHT["paper"|"ink"|"amber"]`
- Produces: yang0 封面 prompt 配方；SVG 迁移改/不改清单

- [ ] **Step 1: 核对 token**

```bash
python -c "import sys; sys.path.insert(0,'scripts'); import handraw; assert handraw.LIGHT['paper']=='#fdf8ea'; assert handraw.LIGHT['ink']=='#16202b'; assert handraw.LIGHT['amber']=='#a4630f'; print('OK')"
```

Expected: `OK`

- [ ] **Step 2: 写 DNA lock**

写明 FA-029、三色、禁卡通/禁换肤/禁科技渐变；封面配方字段：

```text
style: FA-029 Geometric Diagrammatic Narrative
paper: ivory C-30 #fdf8ea; ink Payne gray C-31 #16202b; marker sienna C-29 #a4630f
subject: [章节物理故事一句话]
constraints: legible Simplified Chinese labels; no cute cartoon parts; no rainbow gradients; precise schematic geometry; subtle paper grain; single focal question
aspect: [16:9 | 9:16 | 1:1]
```

- [ ] **Step 3: 写 `anim-migration-notes.md`**

改：经 `handraw.apply`/`retint`/`bow_lines`/`title_decor` 的外壳；与新口诀冲突的 caption 字符串（只改 `generate_svgs.py`）。  
不改：教学数值、封装与电流路径语义；禁止手改 SVG 产物；禁止把 reduced-motion 写回 SVG media query。  
回归：`test_svg_assets.py` + `make test-static` 相关项。

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/visual/2026-11-03-dna-lock.md \
  docs/superpowers/visual/anim-migration-notes.md
git commit -m "docs: 锁定 FA-029 视觉 DNA 与动画迁移备忘"
```

---

### Task 4: 样板重写 — ch1 无源（地基）

**Files:**
- Modify: `docs/p1-02-ch1.md`
- Create: `assets/figures/ch01-hero-parasitics.svg`（或经生成脚本产出的等价路径；静态 hero 放 figures）
- Modify: `docs/p8-11-s8-11.md`（登记 ch1 口诀）
- Test: `scripts/check_chapter_contract.py`；`scripts/check_ai_slop.py`；既有 `test_docs_links.py`

**Interfaces:**
- Consumes: Task 2 契约模板；Task 3 DNA；既有 ch1 事实/公式/动画链接（`assets/svg/resistor-model.svg`、`rc-charge.svg` 等可保留引用）
- Produces: 通过 §10.1 的 ch1；口诀总表 ch1 行更新

- [ ] **Step 1: 备份对照**

```bash
git show HEAD:docs/p1-02-ch1.md > /tmp/ch1-before.md
```

保留事实骨架：寄生夺权点公式、ESR/ESL、戴维南带载、RC lab 链接、已校验数值。

- [ ] **Step 2: 按契约重排并重写口吻（结构必须出现）**

在 `docs/p1-02-ch1.md` 写入/保留：

```markdown
<a id="ch1"></a>
## 第 1 章 无源元件的真实面目
…元数据块…

<!-- slot:hook -->
### 1.x 钩子现象
<!-- slot:intuition -->
### 1.x 直觉
<!-- slot:quant -->
### 1.x 定量推导
> **口诀**：……（一点就懂，一句）
<!-- slot:limits -->
### 1.x 失效边界
<!-- slot:lab -->
### 1.x 动手验证
<figure>…hero…</figure>
> **图问**：……？
**算一笔**：……（条件写全；无出处标「示意」）
<!-- slot:selfcheck -->
### 1.x 自检
### 验收清单
- [ ] 观察：……
- [ ] 计算：……
- [ ] 测量：……
```

humanizer 步骤（强制）：

1. 通读 `D:\Users\monidianlu\humanizer-zh.md`
2. 删除空收尾、万能总结、「在本章中我们将」
3. 非白名单「不是…而是」改为直陈或「A 做 X；B 做 Y」
4. 禁止编造亲身经历

- [ ] **Step 3: hero 图**

FA-029 纸墨；中文标注；一图一问（寄生夺权或 RC τ）。可用手写 SVG + `handraw.apply`，或按 DNA lock 生成后放入 `assets/figures/ch01-hero-parasitics.svg`。图前 `图问`，图后 figcaption 含数字。

- [ ] **Step 4: 闸**

```bash
python scripts/check_chapter_contract.py docs/p1-02-ch1.md
python scripts/check_ai_slop.py docs/p1-02-ch1.md
python -B -m unittest discover -s scripts -p 'test_docs_links.py' -v
```

Expected: contract 字段全 True；slop exit 0；links PASS

- [ ] **Step 5: 口诀总表**

更新 `docs/p8-11-s8-11.md` 中第 1 章行与章内口诀字面一致。

- [ ] **Step 6: Commit**

```bash
git add docs/p1-02-ch1.md docs/p8-11-s8-11.md assets/figures/ch01-hero-parasitics.svg
git commit -m "content: 样板重写 ch1 无源（契约+humanizer+hero）"
```

---

### Task 5: 样板重写 — ch16 排故五步（精通端）

**Files:**
- Modify: `docs/p4-01-ch16.md`
- Create: `assets/figures/ch16-hero-five-steps.svg`
- Modify: `docs/p8-11-s8-11.md`
- Modify: （若乱码残留）修复章内历史编码损坏行
- Test: 同 Task 4 闸 + 设计说明作业段必须出现

**Interfaces:**
- Consumes: 契约模板；`acceptance-design-note.md`；既有五步法事实与 `assets/svg/debug-flow.svg`
- Produces: 通过 §10.1 且指向 §4.2 的 ch16

- [ ] **Step 1: 对照备份**

```bash
git show HEAD:docs/p4-01-ch16.md > /tmp/ch16-before.md
```

- [ ] **Step 2: 按契约重写结构**

六槽齐全；口诀一句；hero 图讲「证据先于动作」；数值例可用「n 节点最多 ceil(log2 n) 次」并给 n=6→3 的算一笔；验收清单含设计判断题。

章末必须嵌入设计说明作业五块（可引用模板），明确：题库分数不能替代本作业。

- [ ] **Step 3: humanizer + 乱码清理**

按 humanizer-zh 重写；删除非白名单假对比；修复任何 `` 类乱码为正确中文。

- [ ] **Step 4: 闸**

```bash
python scripts/check_chapter_contract.py docs/p4-01-ch16.md
python scripts/check_ai_slop.py docs/p4-01-ch16.md
python -B -m unittest discover -s scripts -p 'test_docs_links.py' -v
```

Expected: 全绿；contract 全 True

- [ ] **Step 5: 口诀总表登记 ch16**

- [ ] **Step 6: Commit**

```bash
git add docs/p4-01-ch16.md docs/p8-11-s8-11.md assets/figures/ch16-hero-five-steps.svg
git commit -m "content: 样板重写 ch16 排故（契约+设计作业+humanizer）"
```

---

### Task 6: 样板派生 — 站点 / README 重建与视觉回归

**Files:**
- Regenerate: `README.md`（via script）
- Build: `build/docs/` `build/site/`（不强制提交产物）
- Modify: 仅当样板暴露脚本 bug 时改 `scripts/build_site.py` / `build_readme.py`

**Interfaces:**
- Consumes: 已重写的 ch1/ch16
- Produces: 本地可打开的站点页；docs↔README 对账绿

- [ ] **Step 1: 重生 README 并对账**

```bash
python scripts/build_readme.py
python -B -m unittest discover -s scripts -p 'test_docs_sync.py' -v
python scripts/build_readme.py --check
```

Expected: PASS / check 无漂移

- [ ] **Step 2: 构建站点**

```bash
python scripts/build_site.py --build
```

Expected: 成功；抽查 `build/site/` 下 ch1、ch16 页含主图与验收清单标题

- [ ] **Step 3: 静态回归子集**

```bash
python -B -m unittest discover -s scripts -p 'test_docs_links.py' -v
python -B -m unittest discover -s scripts -p 'test_site_build.py' -v
python -B -m unittest discover -s scripts -p 'test_a11y.py' -v
```

Expected: PASS（若环境缺依赖，记录并至少保证 docs_links + docs_sync 绿）

- [ ] **Step 4: Commit**

```bash
git add README.md scripts/build_site.py scripts/build_readme.py
git commit -m "build: 样板章后重建 README/站点派生"
```

（无脚本改动则只提交 README）

---

### Task 7: 波次重写 — A 地基剩余章（ch0、ch2）

**Files:**
- Modify: `docs/p1-01-ch0.md`、`docs/p1-03-ch2.md`
- Create: `assets/figures/ch00-hero-*.svg`、`assets/figures/ch02-hero-*.svg`（每章 ≥1）
- Modify: `docs/p8-11-s8-11.md`

**Interfaces:**
- Consumes: 与 Task 4 相同契约/白名单/DNA
- Produces: A 段三章全部 §10.1 可勾

每章重复同一工序（禁止「类似 Task 4」省略——下列清单对 ch0、ch2 **各做一遍**）：

- [ ] **Step 1: 插入 slot 注释与六槽标题，保留已校验公式与 lab/动画链接**
- [ ] **Step 2: humanizer 通篇改写；跑 `check_ai_slop.py` 至 exit 0**
- [ ] **Step 3: 补 FA-029 hero + 图问 + 含数字 figcaption + 至少一则算一笔**
- [ ] **Step 4: 写验收清单（观察/计算/测量）**
- [ ] **Step 5: `check_chapter_contract.py` 全 True；`test_docs_links.py` PASS**
- [ ] **Step 6: 更新口诀总表对应行**
- [ ] **Step 7: 逐章 Commit**

```bash
git add docs/p1-01-ch0.md assets/figures/ch00-hero-*.svg docs/p8-11-s8-11.md
git commit -m "content: 重写 ch0 电路直觉（契约+humanizer）"
git add docs/p1-03-ch2.md assets/figures/ch02-hero-*.svg docs/p8-11-s8-11.md
git commit -m "content: 重写 ch2 二极管（契约+humanizer）"
```

- [ ] **Step 8: A 段总闸**

```bash
python scripts/check_chapter_contract.py docs/p1-01-ch0.md docs/p1-02-ch1.md docs/p1-03-ch2.md
python scripts/check_ai_slop.py docs/p1-01-ch0.md docs/p1-02-ch1.md docs/p1-03-ch2.md
```

Expected: 全绿

---

### Task 8: 波次重写 — B 有源与接口（ch3–ch8）

**Files:**
- Modify: `docs/p1-04-ch3.md` … `docs/p1-09-ch8.md`（6 个文件）
- Create: `assets/figures/ch03-hero-*.svg` … `assets/figures/ch08-hero-*.svg`
- Modify: `docs/p8-11-s8-11.md`
- Modify: `docs/p0-08-cheatsheet.md` / `docs/p0-10-model-limits.md`（仅当章内链接锚点或条目名变更时）

**Interfaces:**
- Consumes: 契约、白名单、DNA、既有 SVG 动画引用
- Produces: B 段六章 §10.1 全勾

对 **ch3、ch4、ch5、ch6、ch7、ch8 每一章**执行：

- [ ] **Step A: 六槽 + 口诀 + hero + 算一笔 + 验收清单**
- [ ] **Step B: humanizer；`python scripts/check_ai_slop.py docs/p1-0X-chN.md` exit 0**
- [ ] **Step C: `python scripts/check_chapter_contract.py docs/p1-0X-chN.md` 全 True**
- [ ] **Step D: 口诀写入 `p8-11-s8-11.md` 对应行**
- [ ] **Step E: Commit** `content: 重写 chN …（契约+humanizer）`

章特定保留事实（不得无出处改数）：

| 章 | 必须保住的骨架 |
|---|---|
| ch3 | BJT 区制、偏置算例、热失控边界 |
| ch4 | MOSFET 四拍/米勒相关已校验叙述与动画链 |
| ch5 | 推挽 vs 开漏（可走白名单对比） |
| ch6 | 虚短虚断条件句；开环≠闭环（白名单） |
| ch7 | 迟滞公式与符号同向（CONTRIBUTING 铁律 11） |
| ch8 | 电荷注入/导通电阻数量级与动画链 |

- [ ] **Step F: B 段总闸**

```bash
python scripts/check_chapter_contract.py docs/p1-04-ch3.md docs/p1-05-ch4.md docs/p1-06-ch5.md docs/p1-07-ch6.md docs/p1-08-ch7.md docs/p1-09-ch8.md
python scripts/check_ai_slop.py docs/p1-04-ch3.md docs/p1-05-ch4.md docs/p1-06-ch5.md docs/p1-07-ch6.md docs/p1-08-ch7.md docs/p1-09-ch8.md
python -B -m unittest discover -s scripts -p 'test_docs_links.py' -v
```

Expected: 全绿

---

### Task 9: 波次重写 — C 电路族与系统（ch9–ch15）

**Files:**
- Modify: `docs/p1-10-ch9.md` `docs/p1-11-ch10.md` `docs/p2-01-ch11.md` `docs/p2-02-ch12.md` `docs/p2-03-ch13.md` `docs/p3-01-ch14.md` `docs/p3-02-ch15.md`
- Create: 各章 `assets/figures/chNN-hero-*.svg`
- Modify: `docs/p8-11-s8-11.md`
- Modify: `docs/p9-00-quiz.md`（题干/答案若引用旧口吻或旧结论则同步；分数≠认证立场保留）

**Interfaces:**
- Consumes: 契约；ch14 必须嵌入完整设计说明作业五块
- Produces: C 段七章 §10.1 全勾；ch14 指向 §4.2

对 **ch9–ch15 每一章**执行与 Task 8 相同的 Step A–E（六槽、humanizer、contract、口诀、commit）。

额外硬条件：

- [ ] **ch14**: 章末含 `acceptance-design-note.md` 五块表；至少一则带指标的迷你设计练习
- [ ] **ch15**: 地回流/星形地与去耦的主图隐喻与验收可勾
- [ ] **ch11/ch12**: 拓扑选型决策句保留可操作区分；动画回填链接不丢

- [ ] **Step F: C 段总闸**

```bash
python scripts/check_chapter_contract.py \
  docs/p1-10-ch9.md docs/p1-11-ch10.md docs/p2-01-ch11.md docs/p2-02-ch12.md \
  docs/p2-03-ch13.md docs/p3-01-ch14.md docs/p3-02-ch15.md
python scripts/check_ai_slop.py \
  docs/p1-10-ch9.md docs/p1-11-ch10.md docs/p2-01-ch11.md docs/p2-02-ch12.md \
  docs/p2-03-ch13.md docs/p3-01-ch14.md docs/p3-02-ch15.md
python scripts/build_readme.py --check
```

Expected: 全绿

---

### Task 10: 波次重写 — D 排故/精通（ch17–ch18）+ 设计说明量规

**Files:**
- Modify: `docs/p4-02-ch17.md` `docs/p4-03-ch18.md`（ch16 已在 Task 5）
- Create: hero figures for ch17/ch18
- Create: `docs/superpowers/rubrics/design-note-rubric.md`
- Modify: `docs/p8-11-s8-11.md` `docs/p0-06-roadmap.md` `docs/p0-09-diagnostic.md`（导航文案对齐四段主线）
- Modify: `docs/p9-00-quiz.md`（如需）

**Interfaces:**
- Consumes: §4.2；ch16 样板
- Produces: D 段收官；可打分的设计说明量规（过关/不过关，不是证书）

- [ ] **Step 1: 重写 ch17、ch18（同契约工序 A–E）**
- [ ] **Step 2: 写 `design-note-rubric.md`**

```markdown
# 设计说明量规（非认证）

| 块 | 过关 | 不过关 |
|---|---|---|
| 指标 | 五类指标写全且可测 | 缺项或不可测 |
| 选型 | 有型号或选型窗+否决理由 | 只有「选用合适器件」 |
| 极限 | ≥3 corner + 预期行为 | 只写「注意温度」 |
| 测试 | 顺序+仪器+判据 | 无判据 |
| 失败预案 | 优先怀疑点+下一刀测量 | 「再检查一遍」 |
```

正文与 CONTRIBUTING 一致：自测分不能替代本量规。

- [ ] **Step 3: 导航篇改链**

`p0-06-roadmap.md` / `p0-09-diagnostic.md` 文案按 A/B/C/D 四段重写，**不改章号**。

- [ ] **Step 4: D + 全书内容闸**

```bash
python scripts/check_chapter_contract.py docs/p4-01-ch16.md docs/p4-02-ch17.md docs/p4-03-ch18.md
python scripts/check_ai_slop.py docs/p*-ch*.md
python -B -m unittest discover -s scripts -p 'test_docs_sync.py' -v
python -B -m unittest discover -s scripts -p 'test_docs_links.py' -v
```

Expected: contract 三章绿；slop 对所有章节 md exit 0（白名单外零命中）；sync/links PASS

- [ ] **Step 5: Commit**

```bash
git add docs/p4-02-ch17.md docs/p4-03-ch18.md docs/superpowers/rubrics/design-note-rubric.md \
  docs/p0-06-roadmap.md docs/p0-09-diagnostic.md docs/p8-11-s8-11.md docs/p9-00-quiz.md \
  assets/figures/ch17-hero-*.svg assets/figures/ch18-hero-*.svg
git commit -m "content: D 段收官与设计说明量规；导航对齐四段主线"
```

---

### Task 11: SVG / handraw 气质批迁移（只改脚本）

**Files:**
- Modify: `scripts/handraw.py`（仅当迁移需要增强 paper grain / title_decor 参数；不改 token 色值）
- Modify: `scripts/generate_svgs.py`（caption/外壳调用与重写后口诀对齐）
- Regenerate: `assets/svg/*.svg`（生成器输出）
- Test: `scripts/test_svg_assets.py` `test_svg_contrast.py` `test_a11y.py`

**Interfaces:**
- Consumes: `anim-migration-notes.md`；`handraw.apply(text, width, title)`
- Produces: 与生成器逐字节一致的 SVG 集；数值语义不变

- [ ] **Step 1: 确认生成入口仍统一 `handraw.apply`**

在 `generate_svgs.py` 的 `save()` 路径确认调用 `handraw.apply`；若有旁路拼色，改为走 token。

- [ ] **Step 2: 对齐口诀/节拍字幕**

检索重写后口诀，更新对应 `caption()` 字符串；禁止改电路参数常量 unless docs 同步改且有出处。

- [ ] **Step 3: 重生**

```bash
python scripts/generate_svgs.py
python -B -m unittest discover -s scripts -p 'test_svg_assets.py' -v
```

Expected: PASS（集合与内容一致）

- [ ] **Step 4: 对比度与 a11y**

```bash
python -B -m unittest discover -s scripts -p 'test_a11y.py' -v
```

有浏览器时再跑 `test_svg_contrast.py`。

- [ ] **Step 5: Commit**

```bash
git add scripts/handraw.py scripts/generate_svgs.py assets/svg
git commit -m "feat: SVG 纸墨气质迁移（生成器回灌，语义不变）"
```

> 本任务只做**既有**约 118 张的气质迁移。新增动画数量见 **Task 11b**（不合并，避免迁移与扩量验收缠死）。

---

### Task 11b: 手绘动画大幅扩量（FA-029，经生成器）

**Files:**
- Modify: `scripts/generate_svgs.py`（新增主题函数；仍统一 `handraw.apply`）
- Modify: `scripts/handraw.py`（仅当新主题需要共享图元助手；**不改** C-29/30/31 token）
- Create: `docs/superpowers/visual/animation-expansion-backlog.md`（选题 ↔ 章 ↔ 教学节拍）
- Create: `docs/superpowers/references/oss-animation-candidates.md`（候选评估表）
- Modify: `docs/p5-00-part5.md`（去掉写死「118」；索引纳入新 demo 锚点）
- Modify: 相关章 `docs/p*-ch*.md`（动画回填链接）
- Regenerate: `assets/svg/*.svg`
- Test: `scripts/test_svg_assets.py`；扩展 `scripts/test_svg_assets.py` 或新增 `scripts/test_svg_count_floor.py`

**Interfaces:**
- Consumes: Task 11 气质迁移结果；附录 A §1；OSS 候选评估结论
- Produces: SVG 总数 **显著高于** 现网约 118（本任务出口闸：**≥150** 张且每张有章回填；冲刺目标 **160+** 若选题与 CI 时长允许）；画廊与 `test_svg_assets` 绿

- [ ] **Step 1: 写扩量 backlog（先选题后写码）**

`animation-expansion-backlog.md` 每行：`id | 章 | 一句话物理故事 | 节拍数 | 关键数值来源（docs 段落或示意） | 优先级`。  
优先补：低密度章（历史 ch7/8/13/17/18）、样板章加深、每章至少一个「失效边界」动态图。  
禁选题：无数值故事的装饰循环、卡通拟人元件。

- [ ] **Step 2: 评估 OSS 候选（许可 + 是否贴合 FA-029）**

写入 `oss-animation-candidates.md` 表（列：repo / license / 用途建议 / FA-029 贴合 / 决策）：

| repo | 用途建议 | 决策默认 |
|---|---|---|
| https://github.com/yang0/handraw-style | 封面/社媒提示词与风格编号 | **采用**（视觉 DNA 已锁） |
| https://github.com/ningzimu/handdrawn-tech-illustrations | 章内静态分析图构图与中文标注密度 | **灵感参考**（不替代 handraw.py） |
| https://github.com/overegneered/manim-eng | 工程向 Manim 动画思路 | **可选灵感**；不强制引入 Manim 重写管线 |
| https://github.com/Mr-FuzzyPenguin/manim-circuit | 电路 Manim 组件 | **可选灵感**；许可不合或风格冲突则只记笔记 |
| https://github.com/milkway/rpic-lang | SVG + GSAP 电路动画 | **可选对照**（交互思路）；主站仍 SMIL/`generate_svgs.py` |
| https://github.com/wijnen/edraw | 电子图绘制 | **可选对照**；不替换生成器 |

规则：任一候选 **先记 license**；不得把外部代码未经许可拷进仓；默认 **不** 把 `generate_svgs.py` 改写成 Manim/GSAP 主链——它们是启发源，最多做可选并行实验目录（如 `experiments/`，不进主 CI）。

- [ ] **Step 3: 写失败测试（数量下限）**

```python
# scripts/test_svg_count_floor.py
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class SvgCountFloor(unittest.TestCase):
    def test_at_least_150_svgs(self):
        n = len(list((ROOT / "assets" / "svg").glob("*.svg")))
        # 扩量完成后抬到 >=150；迁移中期可临时 118，但本任务结束必须过线
        self.assertGreaterEqual(n, 150, f"only {n} svgs; expansion gate is >=150")
```

Run: `python -B -m unittest discover -s scripts -p test_svg_count_floor.py -v`  
Expected: 扩量前 FAIL；扩量后 PASS

- [ ] **Step 4: 在 `generate_svgs.py` 按 backlog 实现新主题**

每个新函数：`svg_open` → 图元 → `caption` 节拍 → `save` → 经 `handraw.apply`。  
数值与封装路径必须可回对 docs 或标明「示意」。  
批量实现可按波次（每波 8–12 张）提交，但本任务总闸仍看 ≥150。

- [ ] **Step 5: 重生 + 一致性**

```bash
python scripts/generate_svgs.py
python -B -m unittest discover -s scripts -p 'test_svg_assets.py' -v
python -B -m unittest discover -s scripts -p 'test_svg_count_floor.py' -v
python -B -m unittest discover -s scripts -p 'test_a11y.py' -v
```

Expected: PASS

- [ ] **Step 6: 画廊与章内回填**

更新 `docs/p5-00-part5.md`：标题/摘要改为「全部 N 张」（N=实际计数或「由生成器产出」表述），索引表加入新 demo 锚点。  
对应章增加动画链接；跑 `test_docs_links.py`。

- [ ] **Step 7: Commit（可多波）**

```bash
git add scripts/generate_svgs.py scripts/handraw.py scripts/test_svg_count_floor.py \
  assets/svg docs/p5-00-part5.md docs/p*-ch*.md \
  docs/superpowers/visual/animation-expansion-backlog.md \
  docs/superpowers/references/oss-animation-candidates.md
git commit -m "feat: 扩容 FA-029 手绘原理动画（生成器≥150）"
```

---

### Task 11c: 策展引用库扩编 + 每章官方引用清单

**Files:**
- Modify: `analog-book/data/references.yml`（扩编；保留既有 `ref-NNN` id，只追加）
- Modify: `analog-book/data/sources.yml`（从 `[]` 扩成可追溯源列表）
- Create: `docs/superpowers/templates/chapter-citations.md`
- Create: `scripts/check_references.py`
- Create: `scripts/test_references.py`
- Modify: 各章 `### 参考与出处`（随内容波次填；本任务交付模板+闸+首批官方/OSS 条目）
- Optional mirror note: `docs/superpowers/references/README.md`（指向 data yml，避免双源正文）

**Interfaces:**
- Consumes: 附录 A §2；既有 references.yml schema（`id/authors/title/edition/publisher/year/isbn_or_url/chapters`）
- Produces: `check_references.validate(path) -> list[str]` 错误列表；每章引用勾选模板；OSS+厂商候选入库

- [ ] **Step 1: 写 `chapter-citations.md` 模板**

```markdown
### 参考与出处（发布前勾选）
- [ ] 关键数字可回溯到 datasheet / 应用笔记 / 已验证算例（写明型号与章节或 URL）
- [ ] 示意数量已标「示意」，未写成保证值
- [ ] 本章至少 1 条 `analog-book/data/references.yml` 的 `ref-***` 已列入 `chapters`
- [ ] 若引用 GitHub OSS：已登记 license + 用途（灵感/工具），未复制无许可代码
- [ ] 未把可选教法读物（如杨建国风格笔记、ADI《新概念模拟电路》PDF）当成参数权威源
```

- [ ] **Step 2: 失败测试 `test_references.py`**

断言：`references.yml` 可解析为 list[dict]；每条含 `id`,`title`,`isbn_or_url`,`chapters`；`id` 唯一；`sources.yml` 为 list（允许先空，本任务结束后 `len>=20`）。  
断言：下列 URL/书名字符串至少作为条目字段出现（可在 title 或 isbn_or_url）：

- `https://github.com/yang0/handraw-style`
- `https://github.com/ningzimu/handdrawn-tech-illustrations`
- `https://github.com/overegneered/manim-eng`
- `https://github.com/Mr-FuzzyPenguin/manim-circuit`
- `https://github.com/milkway/rpic-lang`
- `https://github.com/wijnen/edraw`
- Analog Devices 与 Texas Instruments 官方域名各至少 3 条（datasheet 或 app note）
- 《新概念模拟电路》或等价 ADI 教法 PDF：**可选深读**，条目 `notes`/`edition` 字段标明 `optional-deep-read`，不得标成参数权威

- [ ] **Step 3: 实现 `check_references.py`**

校验 schema、唯一 id、chapters 元素为 0–18 int；CLI 扫描 `docs/p*-ch*.md` 是否至少有 `### 参考与出处` 或 `<!-- slot:citations -->`（全书波次完成后强制；样板阶段可 `--only docs/p1-02-ch1.md,docs/p4-01-ch16.md`）。

- [ ] **Step 4: 扩编 yml（追加，不重编号旧 id）**

OSS 六条：`chapters: []` 或挂到视觉/工具章；`isbn_or_url` 用 repo URL；`authors` 填 org/owner；在 title 后缀注明用途：`（视觉灵感 / 可选管线对照，非主生成器）`。  
厂商：每章至少规划 1 条 ADI 或 TI 链接（可与现有 ref-004 等去重）；`sources.yml` 写入「文档类型、URL、对应章、取数字段」。  
ADI《新概念模拟电路》：单条 optional-deep-read。

- [ ] **Step 5: 跑绿**

```bash
python -B -m unittest discover -s scripts -p 'test_references.py' -v
python scripts/check_references.py analog-book/data/references.yml analog-book/data/sources.yml
```

Expected: PASS / exit 0

- [ ] **Step 6: Commit**

```bash
git add analog-book/data/references.yml analog-book/data/sources.yml \
  docs/superpowers/templates/chapter-citations.md \
  docs/superpowers/references/README.md \
  scripts/check_references.py scripts/test_references.py
git commit -m "docs: 扩编 references/sources 与每章引用清单闸"
```

---

### Task 12: 离线书 / 印刷重建闸

**Files:**
- Regenerate via: `analog-book/build_book.py`、`analog-book/build_print_book.py`
- Modify: 仅当注入链发现平行正文时改 book 构建脚本（禁止在 `analog-book/` 维护第二份章节正文）
- Test: `analog-book/tests/test_build.py`；`make book-check`；`scripts/test_publish_a4_book.py`

**Interfaces:**
- Consumes: 重写后 docs；HANDRAW-STYLE；v3.90 打印动画信息规则
- Produces: A4 HTML/PDF 与（如启用）16K 分卷可打开；§10.3 可勾

- [ ] **Step 1: 确认无双源正文**

```bash
# 不应存在独立中文章稿树；正文段落须从 docs 注入
python analog-book/build_book.py --check --no-build
```

Expected: 通过或仅暴露需修的注入问题（修脚本不写平行 md 正文）

- [ ] **Step 2: 构建离线书**

```bash
make book
make book-pdf
```

Expected: `analog-book/dist/` 下 HTML/PDF 可打开；目录章号对齐 ch0–18

- [ ] **Step 3: 印刷相关**

```bash
make print-book
# 若页数策略需要分卷：
make print-volumes
```

抽查：灰度下标注可读；动画关键帧/说明仍在（不回退 v3.90）。

- [ ] **Step 4: 静态测试**

```bash
python -B -m unittest discover -s analog-book/tests -p 'test_build.py' -v
python -B -m unittest discover -s scripts -p 'test_publish_a4_book.py' -v
```

Expected: PASS

- [ ] **Step 5: Commit**（仅脚本/配置；不强制提交巨型 PDF）

```bash
git add analog-book/*.py analog-book/book analog-book/styles analog-book/tests
git commit -m "build: 整包重做后离线/印刷书重建闸"
```

---

### Task 13: 视频线 — 旁白默认音色 + 分镜/时间轴/烧录字幕/封面波次

**Files:**
- Modify: `video/narrate.py`（默认 VOICE/RATE/音高对齐 spec §10.4）
- Modify: `video/shots/ep01-*.json` … `ep20-*.json`（口诀/数值/旁白与重写 docs 对齐）
- Modify: `video/episodes/` 脚本若存在
- Modify: `video/README.md`（默认音色、时间轴字幕契约与发布闸同步）
- Modify: `docs/p7-01-s7-1.md`（成片链接回填位）
- Test: `video/test_storyboard.py` `video/test_subtitles.py` `video/test_narration_timing.py`

**Interfaces:**
- Consumes: 重写后口诀与关键数值；FA-029 画面资产
- Produces: TTS 默认 `zh-CN-XiaoxiaoNeural`、语速 −5%、音高 −4Hz；字幕由 `timeline.json` 同源烧录；缺分镜/时间轴/烧录字幕/封面不出片

- [ ] **Step 1: 改 `narrate.py` 默认参数**

将现行默认（仓库现为 `zh-CN-YunxiNeural` / `+12%`）改为：

```python
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-5%"
# 若 edge-tts 支持 pitch 参数则：
PITCH = "-4Hz"
```

`synth()` / `Communicate(...)` 传入 pitch（若当前 API 无 pitch，封装文档写明用 ffmpeg `asetrate/atempo` 等价实现，并在本任务 Step 中给出具体函数补丁，禁止含糊「稍后处理」）。

示例补丁方向：

```python
async def _comm(text, voice, rate, pitch):
    import edge_tts
    kwargs = {"rate": rate}
    if pitch:
        kwargs["pitch"] = pitch
    await edge_tts.Communicate(text, voice, **kwargs).save(...)
```

- [ ] **Step 2: 单集对齐样板（先 ep 对应 ch1 或排故相关集）**

更新该集 `video/shots/*.json` 的 `voice` 文本：可压缩句式，**不改结论/数字**；主图隐喻与口诀一致。

```bash
python video/storyboard_lint.py --shots video/shots/<ep>.json
python -B -m unittest discover -s video -p 'test_storyboard.py' -v
```

- [ ] **Step 3: 出草片/字幕/封面闸**

```bash
python video/director.py --shots video/shots/<ep>.json --size vertical
python video/narrate.py --shots video/shots/<ep>.json --size vertical
python video/master.py --shots video/shots/<ep>.json --size vertical
python video/check_still.py video/samples/<name>-final.mp4
python video/director.py --shots video/shots/<ep>.json --size horizontal
python video/narrate.py --shots video/shots/<ep>.json --size horizontal
python video/master.py --shots video/shots/<ep>.json --size horizontal
python video/check_still.py video/samples/<name>-final-h.mp4
```

缺时间轴、烧录字幕、封面或章节标记 → 标记该集未出片。若平台另需 SRT，只能由同一 `timeline.json` 导出，禁止维护第二份字幕正文。

- [ ] **Step 4: 其余 EP 波次**

按章重写完成度分波更新 20 集；每波跑 storyboard/subtitle 测试。  
BGM/响度规则沿用 `video/README.md`，不在本任务改版权策略。

- [ ] **Step 5: Commit**

```bash
git add video/narrate.py video/shots video/episodes docs/p7-01-s7-1.md video/test_*.py
git commit -m "feat: 视频旁白默认 XiaoxiaoNeural 且分镜对齐重写文档"
```

---

### Task 13R: EP01–20 发布成片收口（当前唯一实施缺口）

**当前基线（2026-11-04 实测）**

- 20 份 `video/shots/*.json` 均存在，20 份封面、20 份 timeline、20 个竖版 `-final.mp4`、20 个横版 `-final-h.mp4` 均已生成。
- 使用项目实际运行时 Python 3.13 执行 `python -B -m unittest discover -s video -p 'test_*.py' -v`：**72 tests PASS**。
- 对 40 个发布成片逐个执行 `video/check_still.py`：**32 PASS / 8 FAIL**。

| 集 | 版式 | 失败时间 | 对应镜头 | 修复关注点 |
|---|---|---:|---|---|
| EP01 Miller | 竖 + 横 | 22.0–37.2s | shot 4 `svg:miller-plateau` | 源 SVG/相机层在整段几乎静止；两版都必须补可见运动 |
| EP02 虚短虚断 | 横 | 43.1–46.5s、53.4–56.6s | shot 5 `card:feedback boundary` | 横版卡片进入/停留/退出的运动幅度不足 |
| EP05 探头 | 横 | 22.3–27.1s | shot 4 `num:9%→1%` | 数字卡计数结束后长时间静止 |
| EP06 热失控 | 横 | 22.1–25.4s | shot 4 `card:R_E` | 横版卡片停留段运动不足 |
| EP14 LDO | 横 | 20.4–23.7s | shot 4 `card:dropout` | 横版卡片停留段运动不足 |
| EP19 排故 | 横 | 21.1–25.6s、27.6–31.9s | shot 4 `num:40→15min` | 数字变化前后均有静止窗口 |
| EP20 噪声 | 横 | 27.9–37.7s | shot 4 `num:0→4.1mV` + shot 5 `quiz` 起段 | 数字卡结束与问答卡起段连续静止 |

- [ ] **R1: 先证明问题类型，不改闸值**

对每个失败窗口抽取起/中/末三帧，确认是组件自身冻结、横版相机运动幅度不足，还是 `check_still` 裁切误判。只有能用帧证据证明误判，才允许修检测器；禁止把全局 `0.20%` 阈值下调到刚好放行。

- [ ] **R2: 按组件类型修一次，避免逐集打补丁**

优先检查 Remotion 的 `card`、`num`、`svg` 三类共享运动：停留段应保留缓慢推镜、视差或有教学含义的局部变化。修共享组件后只对上表镜头做窄测；若共享修复会改变其余 32 个已通过成片，必须重跑 40 个静止闸。

- [ ] **R3: 只重渲受影响版式**

EP01 重渲横竖两版；EP02/05/06/14/19/20 只重渲横版。保留既有旁白缓存与已通过版式，禁止因修横版覆盖竖版 timeline 或成片。

- [ ] **R4: 全量机器复验**

```bash
python -B -m unittest discover -s video -p 'test_*.py' -v
# 对 samples/ 下 20 个 -final.mp4 与 20 个 -final-h.mp4 全量循环：
python video/check_still.py video/samples/<name>-final.mp4
python video/check_still.py video/samples/<name>-final-h.mp4
```

出口：72 项测试 PASS，40/40 静止闸 PASS；媒体均含视频+音频流，竖版 1080×1920、横版 1920×1080，时长与各自 timeline 总时长一致。

- [ ] **R5: 人工审片抽检**

逐个查看上表失败窗口，确认运动不是为了过检测而空转；字幕不越界、不遮关键数值，语音与字幕同步，横竖裁切均保住主图信息。人工抽检未签字前，机器全绿也不等于可发布。

- [ ] **R6: 文档与提交收口**

同步 `video/README.md` 的默认音色（XiaoxiaoNeural / −5% / −4Hz）、时间轴烧录字幕契约与 40/40 结果；更新本计划和 ship-gate。只提交跟踪约定内的 `-final*.mp4`、`-timeline.json`、封面与必要源码，不提交 `draft/vo/wav` 中间稿或 `.tmp-render-all.sh`。

```bash
git add video/README.md video/samples/*-final.mp4 video/samples/*-final-h.mp4 \
  video/samples/*-timeline.json video/narrate.py video/master.py video/remotion/src \
  docs/superpowers/plans/2026-11-03-full-remake-zero-to-engineer.md \
  docs/superpowers/specs/2026-11-03-full-remake-zero-to-engineer-design.md \
  docs/superpowers/checklists/ship-gate.md
git commit -m "feat: EP01-20 横竖成片全量重制并通过静止闸"
```

---

### Task 14: 社媒切片模板（公众号 / B 站 / 小红书）

**Files:**
- Create: `docs/superpowers/templates/social-slice.md`
- Create: `docs/superpowers/checklists/social-ship.md`（§10.5 可勾选副本）
- Create: 样例切片各 1 条（可放 `docs/superpowers/examples/social/`，文案结论必须引自已重写章）
- Modify: 封面/主视觉生成记录可引用 yang0 prompt（DNA lock）

**Interfaces:**
- Consumes: 章口诀卡、验收清单、yang0/handraw-style 配方
- Produces: 三平台同构模板；禁止新结论/新数字

- [ ] **Step 1: 写 `social-slice.md`**

字段固定：`章号 | 口诀 | 钩子句 | 关键数值（回溯 docs 路径+锚点） | 验收一句 | CTA（回书/回站） | 尺寸（B站封面 16:9 / 公众号头图 / 小红书 3:4）`。

- [ ] **Step 2: 写 §10.5 checklist 副本到 `social-ship.md`**
- [ ] **Step 3: 用 ch1、ch16 各产一条样例文案（结论与清单一致）**
- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/templates/social-slice.md \
  docs/superpowers/checklists/social-ship.md \
  docs/superpowers/examples/social
git commit -m "docs: 三平台社媒切片模板与上架清单"
```

---

### Task 15: 总闸自动化与发布冻结

**Files:**
- Modify: `docs/superpowers/checklists/ship-gate.md`（勾选状态区；仍人工最终签字）
- Modify: `Makefile`（`remake-ship` 聚合）
- Modify: `scripts/check_ai_slop.py`（支持 `docs/p*-ch*.md` glob）
- Create: `scripts/check_ship_residual.py`（聚合：contract 抽样、slop、references、svg count、双源目录探测）
- Test: `scripts/test_ship_residual.py`

**Interfaces:**
- Consumes: §10.1–10.6；附录 A
- Produces: 一键残余扫描；发布冻结说明（不推送，只本地/CI 门禁）

- [ ] **Step 1: 双源探测**

`check_ship_residual.py` 失败条件示例：存在 `book-manuscript/` 或 spec 点名废止的平行中文树目录；`assets/svg` 与生成器不一致；svg 数 <150；任一样板/抽样章缺 citations 槽。

- [ ] **Step 2: Makefile**

```makefile
remake-ship: remake-check
	$(PY) scripts/check_ai_slop.py docs/p1-01-ch0.md docs/p1-02-ch1.md docs/p1-03-ch2.md \
	  docs/p1-04-ch3.md docs/p1-05-ch4.md docs/p1-06-ch5.md docs/p1-07-ch6.md docs/p1-08-ch7.md \
	  docs/p1-09-ch8.md docs/p1-10-ch9.md docs/p1-11-ch10.md docs/p2-01-ch11.md docs/p2-02-ch12.md \
	  docs/p2-03-ch13.md docs/p3-01-ch14.md docs/p3-02-ch15.md docs/p4-01-ch16.md docs/p4-02-ch17.md \
	  docs/p4-03-ch18.md
	$(PY) scripts/check_references.py analog-book/data/references.yml analog-book/data/sources.yml
	$(PY) -B -m unittest discover -s scripts -p 'test_svg_count_floor.py' -v
	$(PY) scripts/check_ship_residual.py
	$(PY) scripts/build_readme.py --check
```

- [ ] **Step 3: 抽检 3 章四线数值一致（人工+脚本辅助）**

固定抽检：`ch1`、`ch14` 或 `ch12`、`ch16`。对照站页、书页、对应 EP 分镜、社媒样例的口诀与关键数字。

- [ ] **Step 4: 冻结规则写入 ship-gate 文首**

「`make remake-ship` 未绿不得宣称整包完成；通过后仍不自动 push；发布走既有 pages 门禁。」

- [ ] **Step 5: 跑总闸**

```bash
make remake-ship
```

Expected: 全绿（内容波次全部完成之后；中期允许阶段性失败但不得改闸阈值糊弄）

- [ ] **Step 6: Commit**

```bash
git add Makefile scripts/check_ship_residual.py scripts/test_ship_residual.py \
  scripts/check_ai_slop.py docs/superpowers/checklists/ship-gate.md
git commit -m "chore: 整包重做总闸 remake-ship 与发布冻结规则"
```

---

## Self-Review（对照已批准 spec + 附录 A）

| Spec 块 | 计划落点 |
|---|---|
| §1–3 目标/非目标/单源/废止双源 | Global Constraints；Task 12 双源探测；Task 15 |
| §4 精通=设计说明五块 | Task 1 模板；Task 5/9/10 量规 |
| §5 四段×ch0–18 | Task 1 地图；Tasks 7–10 波次 |
| §6 章节契约四件套 | Task 2 模板；Tasks 4–10；`check_chapter_contract` |
| §7 humanizer / 白名单 | Task 2；`check_ai_slop`；各章重写步骤 |
| §8 FA-029 DNA / yang0 分层 | Task 3；Task 14 封面 |
| §9 Approach A 顺序 | 任务序 内容→站→书→动画/视频→社媒；Constraints 保留 A |
| §10.1–10.6 五线清单 | ship-gate；Tasks 6/12/13/14/15 |
| §11–12 旧 spec / 技能 | agent-refs；不删旧 spec |
| §13 P0–P5 | Tasks 0–15 映射 |
| **附录 A.1 动画加量** | **Task 11 + 11b**（≥150，生成器扩） |
| **附录 A.2 资料加厚** | **Task 11c**（references.yml/sources.yml + 章引用清单） |
| **附录 A.3 独立可验收且不削弱 A** | 11b/11c 独立出口闸；Constraints 明示不改打法 A |

**Placeholder scan:** 无 TBD/TODO；OSS 候选均给默认决策（采用/灵感/可选对照）。  
**残余风险（非计划缺口）：** Manim/GSAP 仅灵感，主链仍 SMIL 生成器——若未来要并行实验，另开计划，不阻塞本整包。  
**音高 −4Hz：** Task 13 要求在 edge-tts 或 ffmpeg 等价路径落地，不得留下「以后再说」。

---

*计划写毕。执行时推荐 superpowers:subagent-driven-development（每任务新子代理+复审），或 executing-plans 本会话推进。*
