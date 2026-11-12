#!/usr/bin/env python3
"""生成共享术语表 book/glossary.md（设计 §10.1）。

主干是卷二附录 C 的缩写表，并入卷一 8.10 的黑话速查表；输出统一五列：
术语、英文、定义、所属卷、相关条目。条目定义保持原样，不在此阶段改写正文。

    python book/build_glossary.py           # 重新生成
    python book/build_glossary.py --check   # 校验已提交文件与源同步
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "book"))

from references import ReferenceIndex  # noqa: E402

BMS_GLOSSARY = ROOT / "bms-book" / "book" / "附录C-术语表.md"
ANALOG_GLOSSARY = ROOT / "analog" / "docs" / "p8-10-s8-10.md"
OUTPUT = ROOT / "book" / "glossary.md"

HEADER = "| 术语 | 英文 | 定义 | 所属卷 | 相关条目 |\n|---|---|---|---|---|\n"


def table_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        rows.append(cells)
    return rows[1:]


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def bms_entries() -> list[dict[str, str]]:
    entries = []
    for abbr, english, chinese, meaning in table_rows(BMS_GLOSSARY):
        abbr, chinese = abbr.strip(), chinese.strip()
        if chinese == abbr or abbr in chinese:
            term = chinese
        elif chinese:
            term = f"{abbr}（{chinese}）"
        else:
            term = abbr
        if not re.search(r"[A-Za-z]", english):
            english = "—"
        entries.append({"term": term, "english": english, "definition": meaning,
                        "volume": "卷二", "source": abbr})
    return entries


def analog_entries(index: ReferenceIndex) -> list[dict[str, str]]:
    entries = []
    source = ANALOG_GLOSSARY
    for jargon, meaning, link in table_rows(ANALOG_GLOSSARY):
        english = latin_name(jargon)
        href = re.search(r"\]\(([^)]+)\)", link)
        related = "—"
        if href:
            target = (source.parent / href.group(1).split("#")[0]).resolve()
            chapter = index.by_source.get(target)
            if chapter:
                related = chapter.label
        entries.append({"term": jargon, "english": english, "definition": meaning,
                        "volume": "卷一", "related": related, "source": jargon})
    return entries


def latin_name(term: str) -> str:
    match = re.search(r"[A-Za-z][A-Za-z0-9_-]*(?:\s+[A-Za-z][A-Za-z0-9_-]*)*$", term)
    if not match:
        return "—"
    name = match.group(0).strip()
    if len(re.sub(r"[^A-Za-z]", "", name)) < 2:
        return "—"
    return name


def aliases(entries: list[dict[str, str]]) -> list[tuple[str, str]]:
    result = []
    for entry in entries:
        term = entry["term"]
        result.append((term, entry["term"]))
        core = re.sub(r"（[^）]*）", "", term).strip()
        result.append((core, entry["term"]))
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)（", term)
        if match:
            result.append((match.group(1), entry["term"]))
    return sorted({alias for alias in result if len(alias[0]) >= 2},
                  key=lambda item: len(item[0]), reverse=True)


def related_entries(entry: dict[str, str], entries: list[dict[str, str]]) -> str:
    found: list[str] = []
    definition = entry["definition"]
    for alias, term in aliases(entries):
        if term == entry["term"] or term in found:
            continue
        pattern = (rf"(?<![A-Za-z]){re.escape(alias)}(?![A-Za-z])"
                   if re.search(r"[A-Za-z]", alias) else re.escape(alias))
        if re.search(pattern, definition):
            found.append(term)
            if len(found) == 3:
                break
    return "、".join(found) if found else entry.get("related", "—")


def build(index: ReferenceIndex | None = None) -> str:
    index = index or ReferenceIndex()
    entries = analog_entries(index) + bms_entries()
    seen: dict[str, dict[str, str]] = {}
    for entry in entries:
        key = re.sub(r"[（(].*?[）)]", "", entry["term"]).strip().lower()
        if key in seen:
            merged = seen[key]
            if entry["definition"] not in merged["definition"]:
                merged["definition"] += "；" + entry["definition"]
            merged["volume"] = "两卷"
        else:
            seen[key] = entry
    ordered = list(seen.values())
    lines = ["# 共享术语表", "",
             "> 卷一与卷二的术语合并表；定义以正文为准，相关条目只做导航。", "",
             HEADER.rstrip("\n")]
    for entry in ordered:
        related = related_entries(entry, ordered)
        lines.append("| {term} | {english} | {definition} | {volume} | {related} |".format(
            term=cell(entry["term"]), english=cell(entry["english"]),
            definition=cell(entry["definition"]), volume=entry["volume"],
            related=cell(related)))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成共享术语表")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    content = build()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != content:
            print(f"{OUTPUT.relative_to(ROOT)} 与源术语表不同步，请重新运行生成器",
                  file=sys.stderr)
            return 1
        print(f"共享术语表已同步（{len(content.splitlines())} 行）")
        return 0
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"已生成 {OUTPUT.relative_to(ROOT)}（{len(content.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
