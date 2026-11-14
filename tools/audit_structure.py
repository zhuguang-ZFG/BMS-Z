#!/usr/bin/env python3
"""yuyu 六要素结构审计（只读）。

逐章检查两卷书稿是否落实六个教学要素，输出逐章矩阵与每要素缺失统计，
写入 docs/yuyu-overhaul/structure-audit-I.md 与 structure-audit-II.md。
本工具不修改任何章节 .md。

要素判据（适配本仓）：
- e1 开场场景：章标题（卷 I 章文件为 H2、卷 II 章文件为 H1）之后、第一个
  小节标题之前，存在超过 40 字的段落。
- e2 原理+图：章内含 <figure> / <img> / Markdown 图片 / mermaid 代码块 /
  手绘引用任一。
- e3 可跟做实验：章内含“命令或仿真步骤”类代码块（shell/控制台、REPL、
  SPICE 仿真指令、可运行 Python 脚本），且正文含「成功判据/预期/应看到」
  类文字。
- e4 翻车对照：存在标题含 翻车|对照|误区|排障|踩坑|失败|陷阱 的小节，
  且该小节内含真表格（Markdown 管道表格或 <table>）。
- e5 跨卷同构点：正文（非标题行）含明确的另一卷目标（「参见卷」「卷 I」「卷 II」）；仅「同构」二字不算。
- e6 版本/环境核对或参考资料：标题、加粗引导语或清单条目中出现
  版本|环境|核对|参考资料|延伸阅读。

用法：
    python tools/audit_structure.py --volume I
    python tools/audit_structure.py --volume II
    python tools/audit_structure.py --volume both
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "yuyu-overhaul"

VOLUME_SPECS: dict[str, dict[str, Any]] = {
    "I": {
        "label": "卷 I · 模拟电路（analog）",
        "manifest": ROOT / "analog" / "analog-book" / "manifest.json",
        "chapters_dir": ROOT / "analog" / "docs",
        "report": OUT_DIR / "structure-audit-I.md",
    },
    "II": {
        "label": "卷 II · BMS（bms-book）",
        "manifest": ROOT / "bms-book" / "manifest.json",
        "chapters_dir": ROOT / "bms-book" / "book",
        "report": OUT_DIR / "structure-audit-II.md",
    },
}

ELEMENTS = ["e1", "e2", "e3", "e4", "e5", "e6"]
ELEMENT_NAMES = {
    "e1": "开场场景",
    "e2": "原理+图",
    "e3": "可跟做实验",
    "e4": "翻车对照",
    "e5": "跨卷同构点",
    "e6": "版本/环境核对或参考资料",
}

FENCE_RE = re.compile(r"^```([^\n]*)\n(.*?)^```\s*$", re.M | re.S)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
BOLD_LEAD_RE = re.compile(r"^\*\*([^*]+)\*\*")
MD_TABLE_RE = re.compile(
    r"^\|.*\|\s*\r?\n^\|(?:\s*:?-+:?\s*\|)+\s*\r?\n(?:^\|.*\|\s*\r?\n?)+",
    re.M,
)

E2_RE = re.compile(r"<figure\b|<img\b|!\[[^\]]*\]\([^)]*\)|```mermaid|手绘", re.I)
E3_SUCCESS_RE = re.compile(r"成功判据|预期|应看到|应该看到")
E4_TITLE_RE = re.compile(r"翻车|对照|误区|排障|踩坑|失败|陷阱")
E5_RE = re.compile(r"参见卷|卷\s*[IⅠⅡ]")
E6_RE = re.compile(r"版本|环境|核对|参考资料|延伸阅读")

SHELL_INFO = {"bash", "sh", "shell", "console", "powershell", "ps1", "bat", "cmd", "batch", "terminal"}
SPICE_DIRECTIVE_RE = re.compile(r"^\s*\.(tran|meas|dc|ac|op|param|step|lib|include|inc|four|noise|pss)\b", re.M)
CMD_LINE_RE = re.compile(r"^\s*(?:\$\s|C:\\|PS>|>>> )", re.M)
CLI_TOKEN_RE = re.compile(
    r"^\s*(?:python3?|pip3?|npm|npx|node|adb|ffmpeg|make|cmake|git|gcc|clang|cargo|go|dotnet|ngspice|ltspice)\b",
    re.M,
)
PY_SCRIPT_RE = re.compile(r"^\s*(?:import |from \S+ import |def |for |while |print\()", re.M)


def load_chapters(volume: str) -> list[dict[str, Any]]:
    """Read the chapter list from the volume manifest (read-only)."""
    spec = VOLUME_SPECS[volume]
    manifest_path: Path = spec["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chapters: list[dict[str, Any]] = []
    if volume == "I":
        for part in manifest.get("parts", []):
            for unit in part.get("units", []):
                for name in unit.get("chapters", []):
                    chapters.append(
                        {
                            "file": name,
                            "part": str(part.get("id", "")),
                            "unit": str(unit.get("title", "")),
                        }
                    )
    else:
        for part in manifest.get("parts", []):
            for name in part.get("files", []):
                chapters.append(
                    {
                        "file": name,
                        "part": str(part.get("id", "")),
                        "unit": str(part.get("title", "")),
                    }
                )
    for ch in chapters:
        path = spec["chapters_dir"] / ch["file"]
        if not path.is_file():
            raise FileNotFoundError(f"章文件缺失：{path}（清单 {manifest_path}）")
        ch["path"] = path
        ch["text"] = path.read_text(encoding="utf-8")
    return chapters


def chapter_id(volume: str, filename: str) -> str:
    """Short row id: analog uses emblem-style chNN, bms uses file stem number."""
    if volume == "I":
        m = re.search(r"-ch(\d+)\.md$", filename)
        return f"ch{int(m.group(1)):02d}" if m else Path(filename).stem
    m = re.match(r"^(\d+)", filename)
    if m:
        return f"{int(m.group(1)):02d}"
    m = re.match(r"^(附录[A-Z])", filename)
    return m.group(1) if m else Path(filename).stem


def chapter_title(text: str) -> str:
    m = HEADING_RE.search(text)
    if not m:
        return "(未找到标题)"
    title = m.group(2).strip()
    title = re.sub(r"<a\b[^>]*>.*?</a>|<a\b[^>]*/>", "", title)
    title = re.sub(r"\*\*|`", "", title)
    return title.strip()


def prose_lines(text: str) -> list[str]:
    """Lines outside fenced code blocks (fence markers themselves dropped)."""
    lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return lines


def block_char_count(block: str) -> int:
    """Count meaningful characters of one markdown block (paragraph-ish)."""
    cleaned_lines: list[str] = []
    for line in block.splitlines():
        line = re.sub(r"^\s*(?:>\s?|[-*+]\s+|\d+[.)]\s+)", "", line)
        line = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"<[^>]+>", "", line)
        line = line.replace("**", "").replace("`", "")
        if re.fullmatch(r"\s*(?:---+|\$\$|\|)", line or ""):
            continue
        cleaned_lines.append(line)
    joined = "".join(cleaned_lines)
    return len(re.sub(r"\s", "", joined))


def is_experiment_block(info: str, body: str) -> bool:
    """A fenced block that reads as commands or simulation steps."""
    tag = info.strip().strip("`").lower()
    if tag in SHELL_INFO or tag in {"spice", "cir", "netlist"}:
        return True
    if tag in {"python", "py"}:
        # 可运行脚本（含 import/def/循环/打印）才算仿真/实验步骤；单行公式不算。
        return bool(PY_SCRIPT_RE.search(body))
    if CMD_LINE_RE.search(body) or CLI_TOKEN_RE.search(body) or SPICE_DIRECTIVE_RE.search(body):
        return True
    return False


def check_e1(text: str) -> bool:
    """>40-char paragraph between the chapter title heading and first section heading."""
    hs = list(HEADING_RE.finditer(text))
    if not hs:
        return False
    first = hs[0]
    region_end = hs[1].start() if len(hs) > 1 else len(text)
    opening = text[first.end():region_end]
    for block in re.split(r"\n\s*\n", opening):
        if block_char_count(block) > 40:
            return True
    return False


def check_e2(text: str) -> bool:
    return bool(E2_RE.search(text))


def check_e3(text: str) -> bool:
    has_block = any(is_experiment_block(info, body) for info, body in FENCE_RE.findall(text))
    if not has_block:
        return False
    prose = "\n".join(prose_lines(text))
    return bool(E3_SUCCESS_RE.search(prose))


def check_e4(text: str) -> bool:
    hs = list(HEADING_RE.finditer(text))
    for idx, h in enumerate(hs):
        if not E4_TITLE_RE.search(h.group(2)):
            continue
        level = len(h.group(1))
        span_end = len(text)
        for nxt in hs[idx + 1:]:
            if len(nxt.group(1)) <= level:
                span_end = nxt.start()
                break
        section = text[h.end():span_end]
        if MD_TABLE_RE.search(section) or re.search(r"<table\b", section, re.I):
            return True
    return False


def check_e5(text: str) -> bool:
    for line in prose_lines(text):
        if HEADING_RE.match(line):
            continue
        if E5_RE.search(line):
            return True
    return False


def check_e6(text: str) -> bool:
    for line in prose_lines(text):
        m = HEADING_RE.match(line)
        if m and E6_RE.search(m.group(2)):
            return True
        if LIST_ITEM_RE.match(line) and E6_RE.search(line):
            return True
        bold = BOLD_LEAD_RE.match(line.strip())
        if bold and E6_RE.search(bold.group(1)):
            return True
    return False


def audit_chapter(volume: str, ch: dict[str, Any]) -> dict[str, Any]:
    text = ch["text"]
    results = {
        "e1": check_e1(text),
        "e2": check_e2(text),
        "e3": check_e3(text),
        "e4": check_e4(text),
        "e5": check_e5(text),
        "e6": check_e6(text),
    }
    # 附录 A–E 是资料性 backmatter：e2/e3/e4 不适用（N/A），不计入缺失。
    if volume == "II" and ch["file"].startswith("附录"):
        for e in ("e2", "e3", "e4"):
            results[e] = None
    return {
        "id": chapter_id(volume, ch["file"]),
        "file": ch["file"],
        "part": ch["part"],
        "unit": ch["unit"],
        "title": chapter_title(text),
        "results": results,
        "missing": [e for e in ELEMENTS if results[e] is False],
    }


CRITERIA_NOTES = """\
| 要素 | 判据（本仓适配实现） |
|---|---|
| e1 开场场景 | 章标题（卷 I 为 H2、卷 II 为 H1）之后、第一个小节标题之前，存在超过 40 字的段落 |
| e2 原理+图 | 章内含 `<figure>`、`<img>`、Markdown 图片、mermaid 代码块或「手绘」引用任一 |
| e3 可跟做实验 | 章内含命令/仿真步骤类代码块（shell/控制台、REPL、SPICE 指令、可运行 Python 脚本），且正文含「成功判据/预期/应看到」类文字 |
| e4 翻车对照 | 存在标题含 翻车/对照/误区/排障/踩坑/失败/陷阱 的小节，且小节内含真表格 |
| e5 跨卷同构点 | 正文（非标题行）含「参见卷/同构/卷 I/卷 II」类跨卷引用 |
| e6 版本/环境核对或参考资料 | 标题、加粗引导语或清单条目含 版本/环境/核对/参考资料/延伸阅读 |

注：卷 II 附录 A–E 为资料性 backmatter，e2/e3/e4 记「—」（不适用），不计入缺失统计。
"""


def render_report(volume: str, rows: list[dict[str, Any]]) -> str:
    spec = VOLUME_SPECS[volume]
    total = len(rows)
    lines: list[str] = []
    lines.append(f"# yuyu 六要素结构审计 · {spec['label']}")
    lines.append("")
    lines.append(f"- 章节清单：`{spec['manifest'].relative_to(ROOT).as_posix()}`")
    lines.append(f"- 章节源文件目录：`{spec['chapters_dir'].relative_to(ROOT).as_posix()}`")
    lines.append(f"- 章数：{total}")
    lines.append("- 审计方式：`tools/audit_structure.py` 只读扫描，未修改任何章节内容。")
    lines.append("")
    lines.append("## 判据说明")
    lines.append("")
    lines.append(CRITERIA_NOTES.rstrip())
    lines.append("")
    lines.append("## 逐章六要素矩阵")
    lines.append("")
    lines.append("| 章 | 标题 | e1 | e2 | e3 | e4 | e5 | e6 | 缺失数 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for row in rows:
        marks = ["✓" if row["results"][e] else ("—" if row["results"][e] is None else "✗")
                 for e in ELEMENTS]
        title = row["title"].replace("|", "\\|")
        lines.append(
            f"| {row['id']} | {title} | " + " | ".join(marks) + f" | {len(row['missing'])} |"
        )
    lines.append("")
    lines.append("## 每要素缺失统计")
    lines.append("")
    lines.append("| 要素 | 含义 | 缺失章数 | 缺失比例 | 缺失章 |")
    lines.append("|---|---|---|---|---|")
    for e in ELEMENTS:
        missing = [r["id"] for r in rows if r["results"][e] is False]
        pct = f"{len(missing) / total * 100:.0f}%" if total else "-"
        lines.append(
            f"| {e} | {ELEMENT_NAMES[e]} | {len(missing)}/{total} | {pct} | "
            + ("、".join(missing) if missing else "—")
            + " |"
        )
    full = [r["id"] for r in rows if not r["missing"]]
    lines.append("")
    lines.append(f"六要素全部满足的章：{len(full)}/{total}"
                 + (f"（{'、'.join(full)}）" if full else ""))
    lines.append("")
    lines.append("> 说明：本审计为关键词与结构启发式判据，用于定位改造缺口；")
    lines.append("> “✗”表示按上述判据未检索到对应要素，不等于该章必须补充该要素。")
    lines.append("")
    return "\n".join(lines)


def run_volume(volume: str, write_report: bool = True) -> tuple[list[dict[str, Any]], Path | None]:
    rows = [audit_chapter(volume, ch) for ch in load_chapters(volume)]
    report_path: Path | None = None
    if write_report:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = VOLUME_SPECS[volume]["report"]
        report_path.write_text(render_report(volume, rows), encoding="utf-8")
    return rows, report_path


def print_summary(volume: str, rows: list[dict[str, Any]], report_path: Path | None) -> None:
    total = len(rows)
    print(f"[{volume}] {VOLUME_SPECS[volume]['label']}：共 {total} 章")
    for e in ELEMENTS:
        missing = [r["id"] for r in rows if r["results"][e] is False]
        print(f"  {e} {ELEMENT_NAMES[e]}：缺失 {len(missing)}/{total}"
              + (f" -> {' '.join(missing)}" if missing else ""))
    full = [r["id"] for r in rows if not r["missing"]]
    print(f"  六要素全满足：{len(full)}/{total}")
    if report_path is not None:
        print(f"  报告已写入：{report_path.relative_to(ROOT).as_posix()}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="yuyu 六要素结构审计（只读）")
    parser.add_argument(
        "--volume",
        required=True,
        choices=["I", "II", "i", "ii", "1", "2", "both"],
        help="审计卷 I（analog）、卷 II（bms-book）或 both",
    )
    args = parser.parse_args(argv)
    volume = args.volume.strip().upper()
    if volume in {"1", "I"}:
        targets = ["I"]
    elif volume in {"2", "II"}:
        targets = ["II"]
    else:
        targets = ["I", "II"]
    for vol in targets:
        rows, report_path = run_volume(vol)
        print_summary(vol, rows, report_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
