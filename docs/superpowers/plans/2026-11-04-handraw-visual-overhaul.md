---
search: false
---

# Handraw 视觉整库改造（路径 B）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把第一批 20 条因果图按 FA-002/FA-029 + C-03/C-15 改成「位图帧真源 → 可暂停导出动画」的 handraw 产物，沉淀画风包与可复用扩面 runbook；默认只写提示词，用户明确说「出图」后才渲染。

**Architecture:** 在 `docs/circuits/handraw/` 建立统一真源树（`prompts/` → `storyboard/<slug>/` → `exports/`），用 `manifest.json` 登记每条 slug 的源 SVG、画风、色板、帧清单与验收标志；旧几何 SVG 迁入 `docs/circuits/assets/archive/`（`hppc-pulse` 源在 `bms-book/assets/`，归档到 `bms-book/assets/archive/`）。正文先试点换链 `bms-roadmap` 与 `bms-signal-budget`；动画门禁扩展为 handraw 抽检，不推翻现有 SVG 流水线合同，只过渡。

**Tech Stack:** Markdown 提示词；WebP/APNG 帧与导出；Python 3 + pytest（与现有 `bms-book/tests/` 并列）；Windows PowerShell + git；图像生成仅在用户授权「出图」后调用（handraw-style / 本机会话图像工具）。

## Global Constraints

- 画风：FA-002 机制；FA-029 信息结构
- 色：C-03 主色；C-15 仅危险/切断/越限
- 禁区：无人、无卡通 IP、不写实拍；图注「原理示意 / 非实拍」
- 路径 B：位图帧真源 → 导出可暂停动画；旧 SVG archive
- 默认只写提示词；用户明确说「出图」才调用图像生成
- 不 push；合并前本地门禁绿
- 不推翻 `docs/教材彻底改造SPEC.md` §3 / §9；对齐设计 `docs/superpowers/specs/2026-11-04-handraw-visual-overhaul-design.md`
- 现有 `docs/circuits/动画画风规范.md`（几何 SVG 八百宽/类名配色）在过渡期仍约束**未归档**的旧 SVG；handraw 新产物以本计划画风包 + `docs/visual-style-pack.md` 为准，不再要求 SMIL 类名配色

---

## 第一批 20 slug（钉死）

| # | slug | source_svg | kp_id | style |
|---|------|------------|-------|-------|
| 1 | `bms-roadmap` | `docs/circuits/assets/bms-roadmap.svg` | （门面，无单一 KP） | FA-029 |
| 2 | `bms-signal-budget` | `docs/circuits/assets/bms-signal-budget.svg` | `three-probes` | FA-029 |
| 3 | `internal-resistance` | `docs/circuits/assets/internal-resistance.svg` | `load-voltage-drop` | FA-002 |
| 4 | `polarization-physics` | `docs/circuits/assets/polarization-physics.svg` | `load-voltage-drop` | FA-002 |
| 5 | `thermal-runaway` | `docs/circuits/assets/thermal-runaway.svg` | `overcharge-chain` | FA-002 |
| 6 | `overcharge-protection` | `docs/circuits/assets/overcharge-protection.svg` | `overcharge-chain` | FA-002 |
| 7 | `cell-inconsistency-barrel` | `docs/circuits/assets/cell-inconsistency-barrel.svg` | `weakest-cell` | FA-002 |
| 8 | `weakest-cell-ah` | `docs/circuits/assets/weakest-cell-ah.svg` | `weakest-cell` | FA-002 |
| 9 | `protection-debounce` | `docs/circuits/assets/protection-debounce.svg` | `protection-debounce` | FA-002 |
| 10 | `ov-hysteresis-delay` | `docs/circuits/assets/ov-hysteresis-delay.svg` | `protection-debounce` | FA-002 |
| 11 | `adc-quantization` | `docs/circuits/assets/adc-quantization.svg` | `measurement-budget` | FA-029 |
| 12 | `error-budget-waterfall` | `docs/circuits/assets/error-budget-waterfall.svg` | `measurement-budget` | FA-029 |
| 13 | `coulomb-counting` | `docs/circuits/assets/coulomb-counting.svg` | `soc-drift` | FA-002 |
| 14 | `ocv-rest-timeline` | `docs/circuits/assets/ocv-rest-timeline.svg` | `ocv-trust` | FA-002 |
| 15 | `hppc-pulse` | `bms-book/assets/hppc-pulse.svg` | `hppc-identification` | FA-002 |
| 16 | `sop-derating` | `docs/circuits/assets/sop-derating.svg` | `sop-minimum` | FA-002 |
| 17 | `protocol-resync` | `docs/circuits/assets/protocol-resync.svg` | `protocol-resync` | FA-002 |
| 18 | `precharge-sequence-curve` | `docs/circuits/assets/precharge-sequence-curve.svg` | `precharge-evidence` | FA-002 |
| 19 | `ai-context-vs-truth` | `docs/circuits/assets/ai-context-vs-truth.svg` | `ai-boundary` | FA-029 |
| 20 | `ocv-plateau-distrust` | `docs/circuits/assets/ocv-plateau-distrust.svg` | `ocv-trust` | FA-002 |

**路径核实（Task 0 再跑一遍）：** `#15` 不在 `docs/circuits/assets/`，真源是 `bms-book/assets/hppc-pulse.svg`（已存在）。`#20` 两候选均存在，钉死 `ocv-plateau-distrust`（补强 `ocv-trust`；`coulomb-ekf-loop` 留扩面批次）。

---

## File map（本计划将创建 / 修改）

| 路径 | 职责 |
|------|------|
| `docs/circuits/handraw/manifest.json` | 20 条登记真源 |
| `docs/circuits/handraw/prompts/<slug>.md` | 每条提示词（默认交付） |
| `docs/circuits/handraw/storyboard/<slug>/frame-NN.webp` | 位图帧真源（需「出图」） |
| `docs/circuits/handraw/exports/<slug>.webp` | 可暂停导出动画 |
| `docs/circuits/handraw/exports/<slug>-start.webp` / `-end.webp` | 打印用首末帧 |
| `docs/circuits/handraw/README.md` | 目录约定 |
| `docs/circuits/assets/archive/` | 旧 circuits SVG |
| `bms-book/assets/archive/` | 旧 `hppc-pulse.svg` |
| `docs/visual-style-pack.md` | 全库画风包合同 |
| `docs/circuits/handraw/runbook-stage-0-to-7.md` | 扩面手册 |
| `tools/check_handraw_manifest.py` | manifest 校验 CLI |
| `bms-book/tests/test_handraw_manifest.py` | pytest 合同 |
| `docs/circuits/README.md` | 索引对账（Task 5） |
| `docs/README.md` / `docs/stages/stage-1-认识BMS.md` | 试点换链（Task 4） |

---

### Task 0: 脚手架 + 路径核实 + 画风包草案

**Files:**
- Create: `docs/circuits/handraw/README.md`
- Create: `docs/circuits/handraw/manifest.json`（空壳 entries=[]，Task 1 填满 schema）
- Create: `docs/circuits/handraw/prompts/.gitkeep`
- Create: `docs/circuits/handraw/storyboard/.gitkeep`
- Create: `docs/circuits/handraw/exports/.gitkeep`
- Create: `docs/circuits/assets/archive/.gitkeep`
- Create: `bms-book/assets/archive/.gitkeep`
- Create: `docs/visual-style-pack.md`

**Interfaces:**
- Consumes: 设计 §2 画风表；第一批 20 slug 表
- Produces: 目录约定；`docs/visual-style-pack.md` 草案字段（FA/C/禁区/过渡说明）

- [ ] **Step 1: 核实 20 个 source_svg 均存在**

Run (PowerShell，仓库根 `D:\Users\BMS-Z`):

```powershell
$paths = @(
  'docs/circuits/assets/bms-roadmap.svg',
  'docs/circuits/assets/bms-signal-budget.svg',
  'docs/circuits/assets/internal-resistance.svg',
  'docs/circuits/assets/polarization-physics.svg',
  'docs/circuits/assets/thermal-runaway.svg',
  'docs/circuits/assets/overcharge-protection.svg',
  'docs/circuits/assets/cell-inconsistency-barrel.svg',
  'docs/circuits/assets/weakest-cell-ah.svg',
  'docs/circuits/assets/protection-debounce.svg',
  'docs/circuits/assets/ov-hysteresis-delay.svg',
  'docs/circuits/assets/adc-quantization.svg',
  'docs/circuits/assets/error-budget-waterfall.svg',
  'docs/circuits/assets/coulomb-counting.svg',
  'docs/circuits/assets/ocv-rest-timeline.svg',
  'bms-book/assets/hppc-pulse.svg',
  'docs/circuits/assets/sop-derating.svg',
  'docs/circuits/assets/protocol-resync.svg',
  'docs/circuits/assets/precharge-sequence-curve.svg',
  'docs/circuits/assets/ai-context-vs-truth.svg',
  'docs/circuits/assets/ocv-plateau-distrust.svg'
)
$paths | ForEach-Object { "$_ => $(Test-Path $_)" }
```

Expected: 20 行全部 `True`。若某行 `False`，停工：用同 KP 的 `curriculum/concepts.json` → `animations[]` 备选替换，并同步改本计划表格与后续 prompts 文件名。

- [ ] **Step 2: 创建目录**

```powershell
New-Item -ItemType Directory -Force -Path @(
  'docs/circuits/handraw/prompts',
  'docs/circuits/handraw/storyboard',
  'docs/circuits/handraw/exports',
  'docs/circuits/assets/archive',
  'bms-book/assets/archive'
) | Out-Null
Set-Content -Encoding utf8 docs/circuits/handraw/prompts/.gitkeep ''
Set-Content -Encoding utf8 docs/circuits/handraw/storyboard/.gitkeep ''
Set-Content -Encoding utf8 docs/circuits/handraw/exports/.gitkeep ''
Set-Content -Encoding utf8 docs/circuits/assets/archive/.gitkeep ''
Set-Content -Encoding utf8 bms-book/assets/archive/.gitkeep ''
```

Expected: 五处目录存在且含 `.gitkeep`。

- [ ] **Step 3: 写 `docs/circuits/handraw/README.md`**

```markdown
# handraw 真源树（路径 B）

- `prompts/<slug>.md` — 提示词（默认交付；未授权「出图」时只维护这里）
- `storyboard/<slug>/frame-01.webp` … `frame-08.webp` — 位图帧真源（3–8 帧）
- `exports/<slug>.webp` — 可暂停动画；`<slug>-start.webp` / `<slug>-end.webp` 打印首末帧
- `manifest.json` — 全量登记；校验见 `tools/check_handraw_manifest.py`

画风：FA-002 机制 / FA-029 信息结构。色：C-03 主色，C-15 仅危险。图注：原理示意 / 非实拍。
旧几何 SVG → `docs/circuits/assets/archive/`（`hppc-pulse` → `bms-book/assets/archive/`）。
过渡：未归档旧 SVG 仍守 `docs/circuits/动画画风规范.md`；handraw 产物守 `docs/visual-style-pack.md`。
```

- [ ] **Step 4: 写 `docs/visual-style-pack.md` 草案**

必须含以下章节标题（正文可短，但标题固定）：

1. `# 视觉画风包（BMS-Z）`
2. `## 定稿`（FA-002 / FA-029 / C-03 / C-15）
3. `## 禁区`
4. `## 图注合同`
5. `## 与动画画风规范的过渡`（写明：旧 SVG 保留 SMIL+类名配色；handraw 不要求 `viewBox 800` 类名体系，但导出动画须可暂停、首末帧静态可读）
6. `## 提示词模板`（留占位列表，Task 2/6 填满）
7. `## 抽检表`（勾选：无人/无卡通/色板/图注/可暂停/观察题）

- [ ] **Step 5: 写空壳 `manifest.json`**

```json
{
  "version": 1,
  "style_pack": "FA-002+FA-029 / C-03+C-15",
  "caption_required": "原理示意 / 非实拍",
  "entries": []
}
```

- [ ] **Step 6: Commit**

```powershell
git add docs/circuits/handraw docs/circuits/assets/archive/.gitkeep bms-book/assets/archive/.gitkeep docs/visual-style-pack.md
git commit -m "chore(handraw): scaffold path-B dirs and style-pack draft"
```

---

### Task 1: manifest schema + 校验脚本

**Files:**
- Create: `tools/check_handraw_manifest.py`
- Create: `bms-book/tests/test_handraw_manifest.py`
- Modify: `docs/circuits/handraw/manifest.json`（写入 20 条最小合法条目：帧路径可先空数组，`frames_required` 标记 pending）

**Interfaces:**
- Consumes: Task 0 目录与空壳 manifest
- Produces:
  - `validate_manifest(path: Path) -> list[str]`（返回错误列表；空列表=通过）
  - CLI：`python tools/check_handraw_manifest.py` exit 0/1
  - 每条 entry 必填字段：`slug`, `source_svg`, `kp_id`（可为 `null`）, `style`（`FA-002`|`FA-029`）, `colors`（`{"primary":"C-03","danger":"C-15"}`）, `frames`（list[str]）, `export`（str|null）, `caption_ok`（bool）, `bans_ok`（bool）, `status`（`prompts_only`|`rendered`|`exported`|`linked`|`archived`）

- [ ] **Step 1: 写失败测试（尚无校验函数时先写测试文件引用将实现的 API）**

创建 `bms-book/tests/test_handraw_manifest.py`：

```python
from pathlib import Path
import json
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_handraw_manifest import validate_manifest  # noqa: E402

MANIFEST = ROOT / "docs" / "circuits" / "handraw" / "manifest.json"
REQUIRED = {
    "slug", "source_svg", "kp_id", "style", "colors",
    "frames", "export", "caption_ok", "bans_ok", "status",
}
ALLOWED_STYLE = {"FA-002", "FA-029"}
ALLOWED_STATUS = {"prompts_only", "rendered", "exported", "linked", "archived"}


def test_manifest_exists_and_has_20_entries():
    assert MANIFEST.is_file()
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(data["entries"]) == 20


def test_each_entry_has_required_fields_and_palette():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in data["entries"]:
        missing = REQUIRED - set(entry)
        assert not missing, f"{entry.get('slug')}: missing {missing}"
        assert entry["style"] in ALLOWED_STYLE
        assert entry["colors"]["primary"] == "C-03"
        assert entry["colors"]["danger"] == "C-15"
        assert entry["status"] in ALLOWED_STATUS
        src = ROOT / entry["source_svg"]
        assert src.is_file(), f"missing source {entry['source_svg']}"


def test_validate_manifest_clean_on_current_file():
    errors = validate_manifest(MANIFEST)
    assert errors == []
```

- [ ] **Step 2: 跑测试确认失败模式清晰**

```powershell
python -m pytest bms-book/tests/test_handraw_manifest.py -v
```

Expected: FAIL（`ModuleNotFoundError` 或 entries==0 / validate 未定义）。不得 PASS。

- [ ] **Step 3: 实现 `tools/check_handraw_manifest.py`**

```python
#!/usr/bin/env python3
"""Validate docs/circuits/handraw/manifest.json against path-B contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "docs" / "circuits" / "handraw" / "manifest.json"
REQUIRED = {
    "slug", "source_svg", "kp_id", "style", "colors",
    "frames", "export", "caption_ok", "bans_ok", "status",
}
ALLOWED_STYLE = {"FA-002", "FA-029"}
ALLOWED_STATUS = {"prompts_only", "rendered", "exported", "linked", "archived"}


def validate_manifest(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing manifest: {path}"]
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries")
    if not isinstance(entries, list):
        return ["entries must be a list"]
    if len(entries) != 20:
        errors.append(f"expected 20 entries, got {len(entries)}")
    seen: set[str] = set()
    for i, entry in enumerate(entries):
        prefix = f"entries[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: not an object")
            continue
        missing = REQUIRED - set(entry)
        if missing:
            errors.append(f"{prefix}: missing {sorted(missing)}")
        slug = entry.get("slug")
        if slug in seen:
            errors.append(f"duplicate slug: {slug}")
        seen.add(slug)
        if entry.get("style") not in ALLOWED_STYLE:
            errors.append(f"{slug}: bad style {entry.get('style')}")
        colors = entry.get("colors") or {}
        if colors.get("primary") != "C-03" or colors.get("danger") != "C-15":
            errors.append(f"{slug}: colors must be C-03/C-15")
        if entry.get("status") not in ALLOWED_STATUS:
            errors.append(f"{slug}: bad status {entry.get('status')}")
        src = entry.get("source_svg")
        if src and not (ROOT / src).is_file():
            # 允许 archived 后源文件已搬家：若 status==archived 则检查 archive 旁路
            if entry.get("status") != "archived":
                errors.append(f"{slug}: source_svg missing: {src}")
        if not isinstance(entry.get("frames"), list):
            errors.append(f"{slug}: frames must be list")
        if entry.get("status") in {"rendered", "exported", "linked"}:
            frames = entry.get("frames") or []
            if not (3 <= len(frames) <= 8):
                errors.append(f"{slug}: need 3-8 frames when status>={entry['status']}")
            for rel in frames:
                if not (ROOT / rel).is_file():
                    errors.append(f"{slug}: missing frame {rel}")
        if entry.get("status") in {"exported", "linked"}:
            export = entry.get("export")
            if not export or not (ROOT / export).is_file():
                errors.append(f"{slug}: missing export {export}")
        if entry.get("status") in {"linked", "archived"}:
            if not entry.get("caption_ok") or not entry.get("bans_ok"):
                errors.append(f"{slug}: caption_ok/bans_ok must be true before link/archive")
    return errors


def main(argv: list[str] | None = None) -> int:
    path = Path(argv[1]) if argv and len(argv) > 1 else DEFAULT
    errors = validate_manifest(path)
    if errors:
        print("HANDRAW MANIFEST FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print("HANDRAW MANIFEST OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

- [ ] **Step 4: 填满 20 条 `prompts_only` 条目**

对表格每一行写入 `entries`，示例（其余 19 条同构；`kp_id` 按表，门面用 `null`）：

```json
{
  "slug": "bms-roadmap",
  "source_svg": "docs/circuits/assets/bms-roadmap.svg",
  "kp_id": null,
  "style": "FA-029",
  "colors": {"primary": "C-03", "danger": "C-15"},
  "frames": [],
  "export": null,
  "caption_ok": false,
  "bans_ok": false,
  "status": "prompts_only"
}
```

`hppc-pulse` 的 `source_svg` 必须是 `bms-book/assets/hppc-pulse.svg`。

- [ ] **Step 5: 跑校验与测试**

```powershell
python tools/check_handraw_manifest.py
python -m pytest bms-book/tests/test_handraw_manifest.py -v
```

Expected: CLI 打印 `HANDRAW MANIFEST OK`；pytest 全部 PASS。

- [ ] **Step 6: Commit**

```powershell
git add tools/check_handraw_manifest.py bms-book/tests/test_handraw_manifest.py docs/circuits/handraw/manifest.json
git commit -m "test(handraw): manifest schema validator for first 20"
```

---

### Task 2: 第一批 20 条 prompts（只提示词）

**Files:**
- Create: `docs/circuits/handraw/prompts/<slug>.md` × 20
- Modify: `docs/circuits/handraw/manifest.json`（可保持 `prompts_only`；可选加 `prompt_path`）

**Interfaces:**
- Consumes: 每条旧 SVG 因果（打开源文件读标题/步骤）
- Produces: 统一 frontmatter + 中英提示词；**不生成任何 webp/png**

每份 prompts 文件固定结构：

```markdown
---
slug: bms-roadmap
style: FA-029
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: null
source_svg: docs/circuits/assets/bms-roadmap.svg
---

# 观察题
（一句话：读者应在动画里看见什么）

# 帧大纲
1. …
2. …

# Prompt（EN）
Hand-drawn educational diagram, FA-029 Chris Ware geometric narrative style,
Prussian blue C-03 primary lines, vermilion C-15 only for hazard/cutoff,
no people, no cartoon mascot, no photorealistic claim, schematic only…
（把本条因果步骤写全）

# Prompt（ZH）
手绘教学图，FA-029…（同上约束，中文复述因果）

# 验收自检
- [ ] 无人无卡通
- [ ] 危险仅 C-15
- [ ] 图注将用「原理示意 / 非实拍」
```

- [ ] **Step 1: 从旧 SVG 抽因果（只读）**

```powershell
Select-String -Path docs/circuits/assets/bms-roadmap.svg -Pattern '<text|title|观察' -Encoding UTF8 | Select-Object -First 30
```

对每一 slug 打开对应 `source_svg`，写下 3–8 步因果（写入该 prompt 的「帧大纲」）。机制类用 FA-002；路线图/预算/误差瀑布/AI 边界对照用 FA-029（已钉在表内）。

- [ ] **Step 2: 生成全部 20 个 prompt 文件**

文件名必须与 slug 一致，例如：

- `docs/circuits/handraw/prompts/bms-roadmap.md`
- `docs/circuits/handraw/prompts/hppc-pulse.md`
- `docs/circuits/handraw/prompts/ocv-plateau-distrust.md`
- …（其余 17 个同理）

每文件必须字面包含：`FA-002` 或 `FA-029`、`C-03`、`C-15`、`原理示意 / 非实拍`、`no people`（或中文「无人」）。

- [ ] **Step 3: 批量检查 prompt 覆盖**

```powershell
$slugs = @('bms-roadmap','bms-signal-budget','internal-resistance','polarization-physics','thermal-runaway','overcharge-protection','cell-inconsistency-barrel','weakest-cell-ah','protection-debounce','ov-hysteresis-delay','adc-quantization','error-budget-waterfall','coulomb-counting','ocv-rest-timeline','hppc-pulse','sop-derating','protocol-resync','precharge-sequence-curve','ai-context-vs-truth','ocv-plateau-distrust')
$slugs | ForEach-Object {
  $p = "docs/circuits/handraw/prompts/$_.md"
  "$_ => exists=$(Test-Path $p)"
}
python -c "from pathlib import Path; p=Path('docs/circuits/handraw/prompts'); print(len(list(p.glob('*.md'))))"
```

Expected: 20 行 `exists=True`；计数 `20`。

- [ ] **Step 4: Commit（仅提示词 + 必要 manifest 注释字段）**

```powershell
git add docs/circuits/handraw/prompts docs/circuits/handraw/manifest.json
git commit -m "docs(handraw): prompts for first 20 path-B storyboards"
```

**硬闸门：** 到此若用户未说「出图」，**停止执行 Task 3–4 的渲染步骤**；可继续写 Task 5 的抽检脚本草案与 Task 7 runbook，但不得调用图像生成、不得提交大体积位图。

---

### Task 3: （闸门）授权「出图」后生成帧

**Files:**
- Create: `docs/circuits/handraw/storyboard/<slug>/frame-01.webp` …（每条 3–8 帧）
- Modify: `docs/circuits/handraw/manifest.json`（`frames` 填相对路径；`status`→`rendered`；人工设 `bans_ok`）

**Interfaces:**
- Consumes: `prompts/<slug>.md`
- Produces: 位图帧；仍不自动换正文链

- [ ] **Step 1: 确认授权**

仅当用户原话含 **「出图」**（本会话或后续明确授权）时继续。否则：

```powershell
Write-Output 'BLOCKED: waiting for user to say 出图; prompts-only deliverable is complete through Task 2'
```

Expected（未授权）: 打印 BLOCKED，**本 Task 其余步骤跳过**，不失败装成完成。

- [ ] **Step 2: 按 slug 渲染帧（授权后）**

对每个 slug：

1. 读 `docs/circuits/handraw/prompts/<slug>.md`
2. 调用 handraw / 图像工具，**严格注入** FA 编号与 C-03/C-15、禁区
3. 保存为 `docs/circuits/handraw/storyboard/<slug>/frame-01.webp` …（帧数=prompt 大纲）
4. 人工目检：无人、无卡通、危险是否仅红点缀

PowerShell 存在性检查模板：

```powershell
$slug = 'bms-roadmap'
Get-ChildItem "docs/circuits/handraw/storyboard/$slug" -Filter 'frame-*.webp' | Measure-Object | Select-Object -ExpandProperty Count
```

Expected: 每 slug 计数在 3..8。

- [ ] **Step 3: 更新 manifest**

每条：

```json
"frames": [
  "docs/circuits/handraw/storyboard/bms-roadmap/frame-01.webp",
  "docs/circuits/handraw/storyboard/bms-roadmap/frame-02.webp",
  "docs/circuits/handraw/storyboard/bms-roadmap/frame-03.webp",
  "docs/circuits/handraw/storyboard/bms-roadmap/frame-04.webp",
  "docs/circuits/handraw/storyboard/bms-roadmap/frame-05.webp"
],
"bans_ok": true,
"status": "rendered"
```

- [ ] **Step 4: 校验**

```powershell
python tools/check_handraw_manifest.py
python -m pytest bms-book/tests/test_handraw_manifest.py -v
```

Expected: OK / PASS。

- [ ] **Step 5: Commit**

```powershell
git add docs/circuits/handraw/storyboard docs/circuits/handraw/manifest.json
git commit -m "feat(handraw): render storyboard frames for first 20 (authorized)"
```

---

### Task 4: 导出可暂停动画 + 首末静态；试点换链

**Files:**
- Create: `docs/circuits/handraw/exports/<slug>.webp`
- Create: `docs/circuits/handraw/exports/<slug>-start.webp`
- Create: `docs/circuits/handraw/exports/<slug>-end.webp`
- Create: `tools/export_handraw_animation.py`（帧序列 → animated webp；若环境缺编码器，写明回退：生成 APNG 或 ffmpeg 命令）
- Modify: `docs/README.md`（或根 `README.md` 中 roadmap 引用处）
- Modify: `docs/stages/stage-1-认识BMS.md`（`bms-signal-budget` 图）
- Modify: `docs/circuits/handraw/manifest.json`（试点两条 `status`→`linked`，`caption_ok=true`）

**Interfaces:**
- Consumes: `storyboard/<slug>/frame-*.webp`
- Produces: `export_slug(slug: str) -> Path`；正文 Markdown 图片路径改指向 exports，并保留观察题 + 图注

- [ ] **Step 1: 实现导出脚本最小版**

`tools/export_handraw_animation.py` 必须：

- 读 `manifest.json` 中 `status==rendered` 的条目
- 将 frames 按名排序拼成 animated WebP（优先 `pillow`）；若失败打印明确错误，不静默跳过
- 同时写出首帧/末帧静态副本

核心逻辑（实现时保持函数名）：

```python
def export_slug(root: Path, entry: dict) -> Path:
    """Build exports/<slug>.webp plus -start/-end stills; return animation path."""
    ...
```

- [ ] **Step 2: 先导出全部已 rendered 的 slug**

```powershell
python tools/export_handraw_animation.py
Get-ChildItem docs/circuits/handraw/exports -Filter *.webp | Measure-Object | Select-Object -ExpandProperty Count
```

Expected: 至少 `20 * 3 = 60` 个 webp（动画+start+end），或脚本对未授权/未渲染条目跳过并打印计数。

- [ ] **Step 3: 试点换链 — roadmap**

定位引用：

```powershell
Select-String -Path README.md,docs/README.md,docs/circuits/README.md,docs/维护说明.md -Pattern 'bms-roadmap\.svg' -Encoding UTF8
```

将**读者主路径**一处（优先 `docs/circuits/README.md` 索引行 + 根 README 教程节）改为：

```markdown
![BMS 学习路线总览（原理示意 / 非实拍）](circuits/handraw/exports/bms-roadmap.webp)

**观察题：** 光点停在你正在读的阶段时，说出下一站的入口问题。
```

保留旧 SVG 路径注释或指向 archive 的说明，勿双源并存误导。

- [ ] **Step 4: 试点换链 — signal-budget**

修改 `docs/stages/stage-1-认识BMS.md` 中：

```markdown
![信号链时间账](../circuits/assets/bms-signal-budget.svg)
```

改为：

```markdown
![信号链时间账（原理示意 / 非实拍）](../circuits/handraw/exports/bms-signal-budget.webp)

**观察题：** 哪一段毫秒占比最大？硬件比较器为何不在这 12.2 ms 账里？
```

- [ ] **Step 5: manifest 试点两条标 linked**

`bms-roadmap`、`bms-signal-budget`：`export` 填相对路径，`caption_ok=true`，`bans_ok=true`，`status=linked`。其余保持 `exported` 或 `rendered`（若已导出则 `exported`）。

- [ ] **Step 6: 校验 + Commit**

```powershell
python tools/check_handraw_manifest.py
python -m pytest bms-book/tests/test_handraw_manifest.py -v
git add tools/export_handraw_animation.py docs/circuits/handraw/exports docs/circuits/handraw/manifest.json docs/circuits/README.md docs/stages/stage-1-认识BMS.md README.md docs/README.md
git commit -m "feat(handraw): export animations and relink roadmap + signal-budget"
```

---

### Task 5: 旧 SVG 归档 + 索引对账 + handraw 抽检门禁

**Files:**
- Move: 20 个 `source_svg` → 对应 `archive/`（circuits 或 bms-book）
- Modify: `docs/circuits/README.md` 动画索引表
- Modify: `docs/视觉缺口表.md`（若有 handraw 批次行则更新状态）
- Create: `bms-book/tests/test_handraw_spotcheck.py`
- Modify: `docs/circuits/handraw/manifest.json`（`status`→`archived` 对已换链/已导出条目）

**Interfaces:**
- Consumes: Task 4 exports
- Produces: `test_handraw_spotcheck` 抽检：随机或全量检查 manifest 中 `linked|archived` 条目的图注关键词与帧数

- [ ] **Step 1: 归档脚本（显式 Move，保留文件名）**

```powershell
# 示例：circuits 资产
Move-Item -Path docs/circuits/assets/bms-roadmap.svg -Destination docs/circuits/assets/archive/bms-roadmap.svg
# hppc 特例
Move-Item -Path bms-book/assets/hppc-pulse.svg -Destination bms-book/assets/archive/hppc-pulse.svg
```

对表中 20 条全部执行；然后：

```powershell
$paths | ForEach-Object { "live=$(Test-Path $_) archive_circuits=$(Test-Path ($_ -replace 'assets/','assets/archive/'))" }
Test-Path bms-book/assets/archive/hppc-pulse.svg
```

Expected: 原路径 `False`（或仅留 stub 重定向说明，二选一；本计划选 **纯 Move，不留 stub**）；archive `True`。

归档后更新 manifest `source_svg` 为 archive 新路径，或增加字段 `archived_svg`；校验器对 `status==archived` 允许源在 archive。

- [ ] **Step 2: 更新 `docs/circuits/README.md` 索引**

凡指向已归档文件的表格行，链接改为 `handraw/exports/<slug>.webp`，备注列加「handraw 路径 B」。

- [ ] **Step 3: 写抽检测试**

`bms-book/tests/test_handraw_spotcheck.py`：

```python
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/circuits/handraw/manifest.json"
CAPTION = "原理示意 / 非实拍"


def test_linked_entries_have_caption_in_pilot_markdown():
    text = (ROOT / "docs/stages/stage-1-认识BMS.md").read_text(encoding="utf-8")
    assert "bms-signal-budget.webp" in text
    assert CAPTION in text


def test_archived_sources_not_in_live_assets_for_batch():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in data["entries"]:
        if entry["status"] != "archived":
            continue
        live = ROOT / entry.get("live_svg", "") if entry.get("live_svg") else None
        # 原 live 路径不得仍存在同名未归档文件
        slug = entry["slug"]
        if slug == "hppc-pulse":
            assert not (ROOT / "bms-book/assets/hppc-pulse.svg").exists()
        else:
            assert not (ROOT / f"docs/circuits/assets/{slug}.svg").exists()
```

- [ ] **Step 4: 跑门禁**

```powershell
python tools/check_handraw_manifest.py
python -m pytest bms-book/tests/test_handraw_manifest.py bms-book/tests/test_handraw_spotcheck.py -v
```

Expected: PASS。若旧 SVG 风格测试因文件搬走失败，更新豁免/路径列表（只改 handraw 批次 20，不放松全库）。

- [ ] **Step 5: Commit**

```powershell
git add docs/circuits/assets/archive bms-book/assets/archive docs/circuits/assets docs/circuits/README.md docs/circuits/handraw/manifest.json bms-book/tests/test_handraw_spotcheck.py docs/视觉缺口表.md
git commit -m "chore(handraw): archive first-20 SVGs and add spotcheck gate"
```

---

### Task 6: 20 张过门勾选 + 视觉画风包定稿

**Files:**
- Modify: `docs/visual-style-pack.md`（草案 → 定稿；填提示词模板与反例）
- Create: `docs/circuits/handraw/acceptance-batch1.md`（20 行勾选表）

**Interfaces:**
- Consumes: 设计 §5.1 单张过门五条
- Produces: 批次验收记录；画风包可被扩面引用

- [ ] **Step 1: 写 `acceptance-batch1.md`**

表格列：`slug | 无人无卡通 | 色板 | 首末静态 | 可暂停+观察题 | 图注 | 总评`

20 行全部手动勾选；任一行失败 → 记入 `docs/视觉缺口表.md`，**不得**在总评写「完成」。

- [ ] **Step 2: 定稿 `docs/visual-style-pack.md`**

补齐：

- FA-002 / FA-029 选用规则（机制 vs 信息结构）
- C-03 / C-15 色值说明（可映射到近似 hex，但合同名仍用 C-03/C-15）
- 反例：大面积朱红、卡通电芯脸、写「示波器实拍」
- 与 `动画画风规范.md` 共存规则（过渡段保留）

- [ ] **Step 3: 最终校验**

```powershell
python tools/check_handraw_manifest.py
python -m pytest bms-book/tests/test_handraw_manifest.py bms-book/tests/test_handraw_spotcheck.py -v
Select-String -Path docs/visual-style-pack.md -Pattern 'FA-002|FA-029|C-03|C-15|原理示意' -Encoding UTF8
```

Expected: 门禁绿；画风包命中四关键词。

- [ ] **Step 4: Commit**

```powershell
git add docs/visual-style-pack.md docs/circuits/handraw/acceptance-batch1.md docs/视觉缺口表.md
git commit -m "docs(handraw): accept first 20 and finalize visual style pack"
```

---

### Task 7: 扩面 runbook（阶段 0→7，不执行完全库 167）

**Files:**
- Create: `docs/circuits/handraw/runbook-stage-0-to-7.md`

**Interfaces:**
- Consumes: Task 0–6 约定
- Produces: 可复用批次模板；**本计划不要求**跑完剩余 ~147 张

- [ ] **Step 1: 写 runbook**

必须包含：

1. 如何从 `docs/circuits/assets/*.svg` 列未迁移清单  
2. 按 `stage_no` 0→7 分批（每批建议 ≤20）  
3. 单条流水线：抽因果 → prompt →（授权）出帧 → export → 换链 → archive → manifest  
4. 门禁命令抄录：`python tools/check_handraw_manifest.py` + 相关 pytest  
5. 失败进 `docs/视觉缺口表.md` 的行模板  
6. 明确：**未说「出图」只交 prompts**

- [ ] **Step 2: 生成「尚未 handraw 化」计数快照（只读）**

```powershell
(Get-ChildItem docs/circuits/assets -Filter *.svg).Count
(Get-ChildItem docs/circuits/assets/archive -Filter *.svg -ErrorAction SilentlyContinue).Count
```

把数字写入 runbook「基线快照」节（执行当日）。

- [ ] **Step 3: Commit**

```powershell
git add docs/circuits/handraw/runbook-stage-0-to-7.md
git commit -m "docs(handraw): stage 0-7 rollout runbook (no full 167 execution)"
```

---

## Self-review（对照设计 §1–§3）

| 设计条款 | 覆盖任务 |
|----------|----------|
| §1 路径 B：位图帧真源 → 导出可暂停动画 | Task 0 目录、Task 3 帧、Task 4 导出 |
| §1 旧 SVG archive；正文换链 | Task 4 试点、Task 5 归档 |
| §1 不做：未授权实拍/假 SMIL/推翻 SPEC | Global Constraints + Task 2 闸门 + Task 3 Step 1 |
| §2 画风 FA-002/029；C-03/C-15；禁区；图注 | Global Constraints、prompts 模板、style pack |
| §2 第一批 20 + 流水线 | 文首钉死表；Task 2–6 |
| §2 默认提示词 / 「出图」才渲染 | Task 2 硬闸门；Task 3 授权步 |
| §3 单张过门五条 | Task 6 acceptance 表 |
| §3 画风包沉淀 + 0→7 扩面 + 抽检 + gap | Task 6、Task 7、Task 5 spotcheck |
| 过渡：旧 `动画画风规范.md` | Task 0 README + style pack「过渡」节 |

占位符扫描：无 TBD/TODO/「类似 Task N」。`hppc-pulse` 路径已核实为 `bms-book/assets/hppc-pulse.svg`；`#20` 钉死 `ocv-plateau-distrust`。

---

## Execution handoff

Plan 路径：`docs/superpowers/plans/2026-11-04-handraw-visual-overhaul.md`。

执行前再确认：当前会话若只需计划，则停在本文件；实施时优先 **subagent-driven-development**（每 Task 新代理 + 复审），或 **executing-plans** 同会话分批。未听到「出图」前，实施代理不得进入 Task 3 渲染。

---

## 执行记录（2026-11-04）

| Task | 状态 | 证据 |
|------|------|------|
| Task 0 脚手架 + 画风包草案 | 完成 | `5b5314c`；20/20 `source_svg` 存在；五处目录 + `.gitkeep`；`README.md`；`docs/visual-style-pack.md` |
| Task 1 manifest + 校验 | 完成 | `e9ae2f8`；`tools/check_handraw_manifest.py`；`bms-book/tests/test_handraw_manifest.py`（红→绿）；20 条 `prompts_only` |
| Task 2 20 条 prompts | 完成 | `4307f97`；`prompts/` 共 20 个 `.md`；帧数=大纲步数、必含字面量、色板转换均逐条核对 |
| Task 3 渲染帧 | **完成 6/20（自绘）** | 用户改口「你可以自己绘图」，不再走图像网关。手写 SVG 帧 → Edge 无头栅格化 960×560 → WebP q97：`bms-roadmap`、`bms-signal-budget` 各 6 帧（`storyboard/<slug>/frame-01…06.webp`，同名 `.svg` 为矢量源）。像素核对（终版抖动档，`y∈[296,305]` 带内暗点）：主轴 846–2464、背景颗粒 σ≈2.37、无红色像素。关键坑：`objectBoundingBox` 滤镜在水平线（零高度 bbox）上整条不渲染，改 `filterUnits="userSpaceOnUse"` 后才出轴。抖动档经 A/D 盲评（当前档 2 分 vs `baseFrequency 0.05` + `scale 4.5` 得 4 分）改采后者。`af93e3c` 补回源图标题与 signal-budget 累计行（8 → 11 → 12 → 12.2 ms）；`qnaigc / deepseek-v4-flash-vision-exp` 逐张复核两张 frame-06：标题、累计行、总账行、卡片、脚注均无压字/出界，0.2 ms 细条可见，手绘感 4/5；像素行距：标题墨迹 y 68–85，下一行墨迹最早 y 141（signal）/ 203（roadmap） | 第三张 `internal-resistance`（5 帧，同一视角电芯 + 电压标尺）：第 3 帧读数 2.70 V 与截止线相交处是全图唯一 C-15（实测红像素 bbox x81–98/y388–405，其余四帧 0）；第 5 帧 ΔV–I 图按 185.7 px/V 标定，校验点在 (20 A, 0.40 V)/(20 A, 1.20 V) 且两线过原点；视觉复核确认无压字/压线/出界，纵轴 1.2→1.4 段距为其余一半属线性刻度正确表现 | 第四张 `polarization-physics`（6 帧，电芯剖面 + V–t 面板）：剖面用两个点阵 pattern（稠密 18 px / 稀疏 30 px）表达「内部还密、表面已空」，省掉逐帧手抄上百个圆点；曲线按 1277.8 px/V 标定，3.550/3.440/3.400 V 分别落在 y=218.3/358.9/410，卸流竖直跳变在 t=3 min（x=590）；全图无 C-15（像素实测 0 红，符合 prompt「无危险点」）。**视觉复核结论已修正（2026-11-05）**：当初记的「无压字/压线/出界」是假阴性——那轮扫描把 `rotate(-90)` 的 y 轴标题整个跳过，而本题 6 帧的「端电压（V，示意）」正压在刻度数字左缘（标题 x=440，刻度左界 435.6）。已把标题左移到 x=420、重出 6 帧并重导出；现几何门（含旋转包围盒 + 字号继承）判 0 缺陷。其余观察仍成立：第 2 帧表面点阵明显更稀，第 5 帧回弹曲线与横轴 0/3/6/10 读数正确，第 6 帧并置两读数 | 第五张 `ocv-rest-timeline`（5 帧，带载放电 → 撤流回弹 → 指数松弛 → 趋近渐近线 → 充放电支对照）：全图 C-15 零次，五帧 SVG 只含 `#003153`/`#f6f1e3` 两色（`grep` 逐帧实测，红用于对照曲线的槽位已改 C-03 虚线 + C-03 双向箭头）；五帧均含图注「原理示意 / 非实拍」；无 `image`/`href`/`foreignObject` 引用（无实拍/logo/吉祥物）；文本坐标静态核对无出界。限流旁路：第三方视觉端点 4 次退避重试仍 429，改以「几何碰撞扫描 + 分区放大目视」，**检出 5 类真实缺陷并已修**：①frame-01 时间轴标签压电流标签；②frame-04/05 电压标注被 y 轴竖线穿过末位数字；③frame-05「3.660 V（充电支）」压「3.68」刻度；④两图全部 11 帧的 y 轴标题 `rotate(-90)` 压刻度数字（ocv x146→130、polarization x440→420）；⑤frame-04/05 虚线渐近线穿过刻度「3.62」（起点 x120→196）。修后重出 WebP 并重导出：0 红、ink 在画布内。**该缺陷类已固化为门**：`frame_geometry_problems`（文本盒两两相交 / 轴线穿越 / 出界，含旋转包围盒与 `font-size`/`text-anchor` 继承）接入 `check_handraw_manifest`，配 6 条 pytest（4 红 1 绿 1 全帧扫描）。教训：只查画布边界判不出压字，必须做几何相交；且继承属性要沿 `<g>` 链算——`<text>` 自己不写 `font-size` 时按 12 兜底会把宽度量小 8%，真交叠照样漏 | 第六张 `thermal-runaway`（6 帧，四幕机制条 + T–t 面板同视角）：过充/过热 → 析锂枝晶 → 刺穿隔膜 → 自加速环 → dT/dt 报警 → 两种升温速率对照。唯一 C-15 只在第 5 帧（红像素实测 157，其余五帧 0），即 `dT/dt` 报警线与越线切断点，交点按曲线函数算出 y=405/x=706 精确落在曲线上。数值照源图：25 + 0.05×10 = 25.5 °C、25 + 1×10 = 35 °C，10 s 窗口未改。**本轮又给几何门补了 path 检查**：原门只认 `<line>`，曲线不查；补上后立刻在已提交帧里抓出两处真「压曲线」——`polarization-physics` f05 的「3.440 V」压在松弛曲线上（下移到 y=374）、`ocv-rest-timeline` f01 时间轴标签与电流箭头端点相接（左移到 x=560）。两条 `C` 三次曲线按 8 段采样、线段-矩形相交判定 |
| Task 4 导出 + 试点换链 | **Step 1–2 完成；Step 3–5 推迟** | `exported=6 skipped=14 failed=0`；六条动画（6/6/5/6/5/6 帧）、每帧 1200 ms、loop=0；`export` 字段落盘，manifest 状态 `exported`（第 3–4 条见 PR #103，第 5–6 条见本轮）。换链推迟到归档批次——**且与 SPEC 冲突，需先裁决**：《教材彻底改造SPEC》§3.1「现有 SVG 动画流水线保留并加密度」+ §4 禁止「handraw 静态图冒充可暂停动画」，归档 5 个 SMIL 源等于删掉动图证据层；同时 `bms-book/render.mjs` 只内联 `assets/` 下的 svg/png，书稿 4 章的 `data-motion-src` 会断 |
| Task 5 归档 + 抽检 | **未执行（依赖 Task 4）** | 归档会破坏 167 张 SVG 门禁与正文链接 |
| Task 6 Step 1 批次勾选 | **未执行（无帧）** | 不在无产物时填「完成」 |
| Task 6 Step 2 画风包定稿 | 完成 | `540f0ce`；FA 选用规则 / 色板 / 反例 / 过渡 / 模板 / 抽检表 |
| Task 7 扩面 runbook | 完成 | `540f0ce`；基线 167 张、0 归档；门禁命令与失败行模板 |

偏差记录：

- `bms-book/tests/test_handraw_manifest.py` 去掉了计划示例里的 `import pytest`（未使用，ruff `F401` 会让 CI 红）；断言未改。
- `docs/核心问题地图.md` 是 `curriculum/concepts.json` 的生成物；该文件当时的工作区改动静止在生成物上，导致 `check_docs` 报「与 concepts.json 不一致」。已改源 `curriculum/concepts.json` 的两条 `goal` 并重新生成（`45e62d3`）。
- 渲染介质改为自绘（2026-11-05）：用户「你可以自己绘图」后不再调用图像模型；帧由手写 SVG 生成，Chromium 无头栅格化，Pillow 转 WebP。同一 slug 的 `.svg` 与 `.webp` 同名并存，前者是可编辑源、后者才是 manifest/导出的输入。
- 自绘帧用到的 SVG 滤镜必须写 `filterUnits="userSpaceOnUse"`：水平线/垂直线用默认 `objectBoundingBox` 时 bbox 有一维为 0，整条线被裁掉（实测主轴 0 暗点，改后主轴恢复；终版档 846–2464）。
- `bms-roadmap` 第 6 帧的入口卡写「167 张动画与电路图」。归档 2 张旧 SVG 后该数应为 165；归档批次必须同步改帧内文案与 docs 计数，否则图与清单互相打脸。
- 站点 `site-build` 连红两次，根因是同一个决定没做完——这 25 篇是 agent/维护者工作文档，不是读者页：
  1. 搜索索引 5096.4 KiB 越过 4900 KiB 预算（本 PR 新增文档默认全进索引）。处置按 `docs/W0基线冻结.md` 先例：**不抬预算**，给 25 篇加 `search: false`（spec 首字节 BOM 一并去掉，否则 `---` 不在首行、frontmatter 不生效）。索引降到 4787.3 KiB，但只解决预算。
  2. 预算放行后 `check_pages.py` 判红：25 个孤儿（没有任何正文档链进来）+ `维护说明.html` 的主题「下一篇」被根侧栏兜底组里的 `visual-style-pack.html` 顶掉。`search: false` 管不到入口，补链也不是正解——提示词与计划不该出现在读者导航里。
  2 的处置：按「内部文档不发布」落 `srcExclude`（`superpowers/**`、`circuits/handraw/**`、`visual-style-pack.md`），名单与侧栏共用新文件 `docs/.vitepress/internal-docs.ts`。只改配置不改侧栏会留一批指向未构建页面的死链（实测 6 处）；两边同源后产物 166 页、孤儿 0、死链 0、页脚 70 向一致。`search: false` 继续保留：`check_search.mjs` 会按源码树逐篇要求进索引，靠这个键把不发布的页排除。读者面的画风规范仍是已发布的 `circuits/动画画风规范.md`。
- 视觉复核最终走 `qnaigc` 的 `deepseek/deepseek-v4-flash-vision-exp`（6–10 s；偶尔 `content` 为空，需读 `reasoning_content`）。3003 的 claude 通道连续 503/504，不再作为依赖；列出的 qwen/doubao 视觉模型均已退役（502 `retired`）。

门禁（本地，2026-11-04）：

- `python tools/check_handraw_manifest.py` → `HANDRAW MANIFEST OK`
- `python -m pytest bms-book/tests/test_handraw_manifest.py` → 3 passed
- `python .github/scripts/check_docs.py` → EXIT=0
- `python tools/check_curriculum.py` → PASS（13 题 / 27 动画 / 13 练习）
- `python -m pytest bms-book/tests` → 240 passed（237 基线 + 3 新增）
- `ruff check`（新增文件）→ All checks passed
- `bash scripts/local-gates.sh` → **EXIT=0**（15 步全 PASS，无 SKIP）
  - 本机 `TMP/TEMP` 指向不可写的 `D:\temp\User`，会让脚本里所有 pytest 步 `PermissionError`；把 `TMP/TEMP` 指到 `.tmp-gate-tmp` 后全绿。这是环境问题，不是仓库问题。
- 站点产物链（2026-11-05，按 `.github/workflows/tests.yml` 的 site-build 顺序本机复现）：
  - `npm run docs:build` → bundle 预算通过，普通最大 771.6 KiB、搜索索引 4787.9 KiB
  - `python bms-book/publish_downloads.py --out-dir docs/.vitepress/site-dist/downloads` → `packaged book v0.6.10`
  - `python3 .github/scripts/check_pages.py docs/.vitepress/site-dist` → **EXIT=0**（166 页、14151 条站内链接、正文图片 776 张、页脚 70 向一致）
  - `node .github/scripts/check_search.mjs docs/.vitepress/site-dist` → **EXIT=0**（152 篇全部在索引、分词函数一致）
