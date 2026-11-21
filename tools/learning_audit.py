#!/usr/bin/env python3
"""Report learning-design pressure across the book, stage docs, and video specs.

This is intentionally a report-only tool. It highlights likely overload and
presentation imbalance without turning editorial judgment into a CI failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "bms-book" / "book"
BOOK_SITE_DIR = ROOT / "docs" / "book"
STAGE_DIR = ROOT / "docs" / "stages"
VIDEO_DIR = ROOT / "tools" / "video" / "specs"
MICRO_VIDEO_DIR = ROOT / "tools" / "video" / "microcourses"
CURRICULUM = ROOT / "curriculum" / "concepts.json"
PROSE_BOILERPLATE = re.compile(
    r"值得注意(?:的是)?|需要注意(?:的是)?|不难发现|显而易见|"
    r"总而言之|综上所述|本章将|接下来我们|让我们"
)
CONTRAST_FRAME = re.compile(r"不是[^。！？\n]{0,80}而是")
ENGINEERING_DIR = ROOT / "bms-book" / "engineering"
# "正文开头现场/故障"门标准（登记在此，供试跑观察）：
# 开头 = H1 后第一段 / 首个 `::: story|principle|trap|lab` 块 / 首个引用块，跳过开头图形；
# 必须出现故障/现象代码（OVP、UVP、OCP、UVT、ERR、HVIL、故障、短路、抖动、越界、失效、
# 异常、烧了、断裂、动作、触发、警告、读数 等）或已发生句式「已经/观察到/读到/发现/
# 报指/报出/记录到…… + 具体症状」。
SITUATION_OPENING = re.compile(
    r"(?:OVP|UVP|OCP|UVT|ERR|HVIL|故障|抖动|越界|失效|异常|烧了|断裂|动作|触发|警告|读数)"
    r"|(?:已经|观察到|读到|发现|报指|报出|记录到)[^。！？\n]{0,40}(?:抖动|触发|异常|越界|失效|故障|读数|烧了|断裂|动作|警告)"
)
STORY_OPEN = re.compile(r"^:{3,}\s*(?:story|principle|trap|lab)\b")
SECTION_OPEN = re.compile(r"^:{3,}\s*$")
# 内联定义模式（陈规/Wave 1 登记样式）：`**词**　定义句……。`
# 正文首用前定义门的门标准：术语为 `**词**` + 不短于 15 字的定义句，再接终止符。
TERM_DEFINITION = re.compile(
    r"\*\*([^*。！？…?!|#>]{1,40}?)\*\*[^\n]{0,2}"
    r"([^\n。！？…]{15,}[。！？…])"
)


def count(pattern: str, text: str, flags: int = 0) -> int:
    return len(re.findall(pattern, text, flags))


def exercise_count(text: str) -> int:
    match = re.search(r"^## 练习\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not match:
        return 0
    return count(r"^\d+\. ", match.group(1), re.M)


def audit_book() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(BOOK_DIR.glob("[0-9][0-9]-*.md")):
        text = path.read_text(encoding="utf-8")
        chapter = path.name[:2]
        flags: list[str] = []
        chars = len(text)
        generated_main = BOOK_SITE_DIR / path.name
        generated_deep = BOOK_SITE_DIR / f"{path.stem}-进阶.md"
        first_read_chars = (
            len(generated_main.read_text(encoding="utf-8"))
            if generated_main.is_file() and generated_deep.is_file()
            else chars
        )
        figures = count(r"<figure\b", text)
        exercises = exercise_count(text)
        has_layered_route = all(
            marker in text for marker in ("第一次主线", "第二遍深挖", "动手验证")
        )
        first_formula = text.find("$$")
        first_numeric_example = min(
            (pos for token in ("**表 ", "算一笔", "教学算例") if (pos := text.find(token)) >= 0),
            default=-1,
        )
        if first_read_chars > 9000:
            flags.append("第一次阅读偏长")
        if chapter != "00" and figures < 2:
            flags.append("图解偏少")
        if chapter != "00" and exercises < 3:
            flags.append("取回练习不足")
        if chapter != "00" and "先自己判断" not in text:
            flags.append("缺少显式先判断")
        if chapter != "00" and chars > 7000 and not has_layered_route:
            flags.append("长章缺少第一次/深挖/动手分层")
        if (
            chapter != "00"
            and first_formula >= 0
            and (first_numeric_example < 0 or first_formula < first_numeric_example)
        ):
            flags.append("首个公式早于贯穿算例")
        rows.append(
            {
                "file": path.relative_to(ROOT).as_posix(),
                "chapter": chapter,
                "chars": chars,
                "first_read_chars": first_read_chars,
                "sections": count(r"^## ", text, re.M),
                "figures": figures,
                "tables": count(r"^\*\*表 ", text, re.M),
                "exercises": exercises,
                "layered_route": has_layered_route,
                "flags": flags,
            }
        )
    return rows


def _reading_role(name: str, stem: str) -> str:
    if "主线" in stem:
        return "主线"
    if "选读" in stem:
        return "选读"
    if name in {
        "stage-0-前置知识.md",
        "stage-2-保护板实践.md",
        "stage-3-AFE-MCU智能BMS.md",
        "stage-4-SOC-SOH算法.md",
        "stage-5-通信与集成.md",
        "stage-6-精通与毕业项目.md",
    }:
        return "完整查阅"
    return "主线"


def audit_stages() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(STAGE_DIR.glob("stage-*.md")):
        text = path.read_text(encoding="utf-8")
        chars = len(text)
        flags: list[str] = []
        reading_role = _reading_role(path.name, path.stem)
        if reading_role == "主线" and chars > 35000:
            flags.append("主线超过 3.5 万字符，必须拆分或声明豁免")
        elif reading_role == "主线" and chars > 15000:
            flags.append("主线超过 SPEC 建议的 1.5 万字符，需任务式复核")
        rows.append(
            {
                "file": path.relative_to(ROOT).as_posix(),
                "reading_role": reading_role,
                "chars": chars,
                "sections": count(r"^## ", text, re.M),
                "animation_refs": count(r"\.svg(?:[)\"'])", text),
                "flags": flags,
            }
        )
    return rows


def body_opening(text: str) -> str:
    """Return the first body text after the H1 title of a page.

    Prefer the first `::: story|principle|trap|lab` block or the first
    blockquote; otherwise take the first paragraph. Leading figures/images
    (Book II chapters start with a <figure>) are skipped first.
    """
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        text = text[m.end():]
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if re.match(r"^#\s", ln)), None)
    if start is None:
        return ""
    i = start + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines):
        if re.match(r"^<figure\b", lines[i]):
            j = i
            while j < len(lines) and not re.match(r"^</figure>\s*$", lines[j]):
                j += 1
            i = j + 1 if j < len(lines) else len(lines)
        elif re.match(r"^<img\b", lines[i]):
            i += 1
        else:
            break
        while i < len(lines) and not lines[i].strip():
            i += 1
    if i >= len(lines):
        return ""
    if STORY_OPEN.match(lines[i]):
        parts = []
        j = i + 1
        while j < len(lines) and not SECTION_OPEN.match(lines[j]):
            s = lines[j].strip()
            if s:
                parts.append(s)
            j += 1
        return " ".join(parts)
    if lines[i].lstrip().startswith(">"):
        parts = []
        j = i
        while j < len(lines) and lines[j].lstrip().startswith(">"):
            parts.append(lines[j].lstrip()[1:].strip())
            j += 1
        return " ".join(p for p in parts if p)
    parts = []
    j = i
    while j < len(lines):
        ln = lines[j]
        if not ln.strip() or ln.startswith("#") or SECTION_OPEN.match(ln):
            break
        parts.append(ln.strip())
        j += 1
    return " ".join(parts)


def _gate_targets() -> list[Path]:
    """Gates 的扫描范围（工程册主线 + stage 主线 + Book II 主线）。"""
    targets: list[Path] = list(sorted(ENGINEERING_DIR.glob("*.md")))
    for path in sorted(STAGE_DIR.glob("stage-*.md")):
        if _reading_role(path.name, path.stem) == "主线":
            targets.append(path)
    targets.extend(sorted(BOOK_DIR.glob("[0-9][0-9]-*.md")))
    return targets


def audit_opening_situations() -> list[dict[str, Any]]:
    """Audit: 正文开头现场/故障 — must carry a fault/situation signal (门标准见 SITUATION_OPENING).

    Scope: Book I mainline (docs/stages/*.md, reading_role 主线), Book II mainline
    (bms-book/book/[0-9][0-9]-*.md), and the engineering manuals (bms-book/engineering/*.md).
    """
    targets = _gate_targets()
    rows: list[dict[str, Any]] = []
    for path in targets:
        text = path.read_text(encoding="utf-8")
        opening = body_opening(text)
        has = SITUATION_OPENING.search(opening) is not None
        kind = "book" if path.parent == BOOK_DIR else (
            "engineering" if path.parent == ENGINEERING_DIR else "stage"
        )
        rows.append({
            "file": path.relative_to(ROOT).as_posix(),
            "kind": kind,
            "has_situation": has,
            "flags": [] if has else ["正文开头缺现场/故障"],
            "opening": (opening or "(无正文开头)[:100]")[:100],
        })
    return rows


def glossary_terms() -> set[str]:
    """新手词门的术语宇宙：glossary（docs/glossary.md、docs/glossary-merged.md）表的
    缩写/中文条目（`| 术语 | 英文 | 说明 |` 或 `| 缩写 | 中文 | 说明 |` 形式，取第一列）。
    """
    terms: set[str] = set()
    for path in sorted(ROOT.joinpath("docs").glob("glossary*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells or not cells[0]:
                continue
            if cells[0] == "术语" or cells[0] == "缩写":
                continue
            if cells[0].startswith("---") or set(cells[0]) <= {"-", " "}:
                continue
            for term in cells[0].split(" / "):
                if term.strip():
                    terms.add(term.strip())
    return terms


def audit_newcomer_term_definition() -> list[dict[str, Any]]:
    """Audit: 新手词首用前定义 — newcomer terms whose first body use has no prior
    definition, or terms covered only by the glossary (no body definition before use).

    Scope: same as audit_opening_situations (engineering manuals, stage mainlines,
    Book II mainlines). Universe: glossary (docs/glossary*.md) terms ∪ terms with an
    inline definition (TERM_DEFINITION pattern). Flag:
    - 正文先用后定：术语在正文出现，而定义位置在其首次出现之后；
    - 只有 glossary：术语有 glossary 定义但正文未先定义。
    报告登记，不阻断 CI（像 SITUATION_OPENING）。
    """
    glossary = glossary_terms()
    rows: list[dict[str, Any]] = []
    for path in _gate_targets():
        text = path.read_text(encoding="utf-8")
        defs: dict[str, int] = {}
        for m in TERM_DEFINITION.finditer(text):
            term = m.group(1).strip()
            if term:
                defs[term] = min(defs.get(term, m.start(1)), m.start(1))
        for term in sorted(glossary | set(defs)):
            use = text.find(term)
            if use < 0:
                continue
            def_pos = defs.get(term)
            if def_pos is not None and use >= def_pos:
                continue
            line = text.count("\n", 0, use) + 1
            if def_pos is not None and use < def_pos:
                form = f"正文先用后定（定义在 L{text.count('\n', 0, def_pos) + 1}）"
            else:
                form = "只有 glossary 定义，正文未先定义"
            rows.append({
                "file": path.relative_to(ROOT).as_posix(),
                "term": term,
                "line": line,
                "form": form,
                "flags": [form],
            })
    rows.sort(key=lambda row: (row["file"], row["line"], row["term"]))
    return rows


def audit_videos() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted([
        *VIDEO_DIR.glob("*.json"),
        *(path for path in MICRO_VIDEO_DIR.glob("*.json")
          if not path.name.endswith(".FACTS.json")),
    ])
    for path in paths:
        spec = json.loads(path.read_text(encoding="utf-8"))
        kind = spec.get("kind", "series")
        segments = spec.get("segments", [])
        beats = [beat for segment in segments for beat in segment.get("beats", [])]
        voiceover = "\n".join(beat.get("vo", "") for beat in beats)
        layouts: dict[str, int] = {}
        for beat in beats:
            layout = beat.get("layout", "unknown")
            layouts[layout] = layouts.get(layout, 0) + 1
        card_ratio = layouts.get("card", 0) / len(beats) if beats else 0.0
        flags: list[str] = []
        if kind == "series" and len(segments) > 12:
            flags.append("段落过多，优先拆微课")
        if kind == "series" and len(beats) > 80:
            flags.append("beat 过多，单集认知负担偏高")
        if len(spec.get("checklist", [])) > 6:
            flags.append("片尾清单过长")
        if card_ratio > 0.55:
            flags.append("纯卡片占比偏高")
        boilerplate = PROSE_BOILERPLATE.findall(voiceover)
        contrast_frames = CONTRAST_FRAME.findall(voiceover)
        if boilerplate:
            flags.append("旁白空泛转场：" + "、".join(sorted(set(boilerplate))))
        if len(contrast_frames) >= 3:
            flags.append(f"旁白‘不是…而是…’框架成簇（{len(contrast_frames)} 处）")
        rows.append(
            {
                "file": path.relative_to(ROOT).as_posix(),
                "episode": spec.get("slug", path.stem),
                "kind": kind,
                "segments": len(segments),
                "beats": len(beats),
                "vo_chars": sum(len(beat.get("vo", "")) for beat in beats),
                "vo_contrast_frames": len(contrast_frames),
                "figure_beats": sum(1 for beat in beats if beat.get("svg")),
                "quizzes": layouts.get("quiz", 0),
                "checklist_items": len(spec.get("checklist", [])),
                "card_ratio": round(card_ratio, 3),
                "layouts": dict(sorted(layouts.items())),
                "flags": flags,
            }
        )
    return rows


def audit_curriculum() -> list[dict[str, Any]]:
    data = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for concept in sorted(data["concepts"], key=lambda row: row["order"]):
        flags: list[str] = []
        if "practice" not in concept:
            flags.append("尚无可运行练习")
        if concept["estimated_minutes"] > 30:
            flags.append("单题时间偏长，考虑拆分")
        rows.append(
            {
                "file": concept["id"],
                "stage": concept["stage_no"],
                "minutes": concept["estimated_minutes"],
                "prerequisites": len(concept["prerequisites"]),
                "animations": len(concept["animations"]),
                "has_practice": "practice" in concept,
                "flags": flags,
            }
        )
    return rows


def prose_paths() -> list[Path]:
    paths = [*BOOK_DIR.glob("*.md"), *ROOT.joinpath("docs").rglob("*.md")]
    return sorted(
        path for path in paths
        if "docs/book" not in path.relative_to(ROOT).as_posix()
        and ".vitepress/dist" not in path.relative_to(ROOT).as_posix()
        and ".vitepress/site-dist" not in path.relative_to(ROOT).as_posix()
    )


def prose_paragraphs(text: str) -> list[str]:
    paragraphs = []
    for raw in re.split(r"\n\s*\n", text):
        paragraph = " ".join(line.strip() for line in raw.splitlines()).strip()
        if len(paragraph) < 60:
            continue
        if paragraph.startswith((
            "#", "|", "```", "<", "![", "[![", ">", "- ", "**视频**",
            "按层走先看 ",
        )):
            continue
        paragraphs.append(re.sub(r"\s+", " ", paragraph))
    return paragraphs


def audit_prose() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    owners: dict[str, set[str]] = {}
    paths = prose_paths()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        generated = "<!-- Generated by prepare-stage" in text
        quotes_style_anti_patterns = path.name in {
            "教材彻底改造SPEC.md",
            "教学设计规范.md",
        }
        boilerplate = [] if quotes_style_anti_patterns else PROSE_BOILERPLATE.findall(text)
        contrasts = [] if quotes_style_anti_patterns else CONTRAST_FRAME.findall(text)
        flags: list[str] = []
        if boilerplate:
            flags.append("空泛转场：" + "、".join(sorted(set(boilerplate))))
        if len(contrasts) >= 4:
            flags.append(f"‘不是…而是…’框架成簇（{len(contrasts)} 处）")
        if flags:
            rows.append({
                "file": path.relative_to(ROOT).as_posix(),
                "boilerplate": len(boilerplate),
                "contrast_frames": len(contrasts),
                "flags": flags,
            })
        if not generated:
            for paragraph in prose_paragraphs(text):
                owners.setdefault(paragraph, set()).add(path.relative_to(ROOT).as_posix())
    repeated = [
        {"text": text, "files": sorted(files)}
        for text, files in owners.items()
        if len(files) > 1
    ]
    return {
        "files_scanned": len(paths),
        "risks": rows,
        "repeated_paragraphs": sorted(repeated, key=lambda row: (-len(row["files"]), row["text"])),
    }


def build_report() -> dict[str, Any]:
    return {
        "generated_from": ".",
        "book": audit_book(),
        "stages": audit_stages(),
        "opening_situations": audit_opening_situations(),
        "newcomer_term_definition": audit_newcomer_term_definition(),
        "videos": audit_videos(),
        "curriculum": audit_curriculum(),
        "prose": audit_prose(),
    }


def print_section(title: str, rows: list[dict[str, Any]], fields: list[str]) -> None:
    print(f"\n{title}")
    for row in rows:
        summary = " · ".join(f"{field}={row[field]}" for field in fields)
        flags = "；".join(row["flags"]) or "无明显结构风险"
        print(f"- {row['file']}: {summary} | {flags}")


def print_text(report: dict[str, Any]) -> None:
    book = report["book"]
    stages = report["stages"]
    videos = report["videos"]
    curriculum = report["curriculum"]
    prose = report["prose"]
    print("BMS-Z 学习设计审计（报告模式，不阻断 CI）")
    print(
        f"总览：书稿 {len(book)} 章 / {sum(row['chars'] for row in book):,} 字符，"
        f"阶段教程 {len(stages)} 篇，视频 {len(videos)} 集，"
        f"核心问题 {len(curriculum)} 个。"
    )
    print_section(
        "书稿", book, ["chars", "first_read_chars", "sections", "figures", "exercises", "layered_route"]
    )
    print_section("阶段教程", stages, ["reading_role", "chars", "sections", "animation_refs"])
    print_section(
        "正文开头现场/故障",
        report["opening_situations"],
        ["kind", "has_situation"],
    )
    print_section(
        "新手词首用前定义",
        report["newcomer_term_definition"],
        ["term", "line", "form"],
    )
    print_section(
        "视频",
        videos,
        [
            "kind", "segments", "beats", "vo_chars", "vo_contrast_frames",
            "figure_beats", "card_ratio",
        ],
    )
    print_section(
        "核心问题课程图",
        curriculum,
        ["stage", "minutes", "prerequisites", "animations", "has_practice"],
    )
    print("\n文风（报告模式）")
    if prose["risks"]:
        for row in prose["risks"]:
            print(
                f"- {row['file']}: boilerplate={row['boilerplate']} · "
                f"contrast_frames={row['contrast_frames']} | {'；'.join(row['flags'])}"
            )
    else:
        print(f"- 扫描 {prose['files_scanned']} 份源稿：未发现空泛转场或成簇对比句。")
    repeated = prose["repeated_paragraphs"]
    if repeated:
        print(f"- 跨文件重复长段落：{len(repeated)} 组（先人工确认是否为必要契约文本）")
    else:
        print("- 跨文件重复长段落：0 组")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)


if __name__ == "__main__":
    main()
