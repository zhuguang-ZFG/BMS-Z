#!/usr/bin/env python3
"""共享术语表与术语登记表的 lint（设计 §10.1）。

只拦截新增歧义：禁用变体按文件记录当前基线，出现次数超过基线才报错；
不要求把既有正文全量改写成首选词。术语表本身另查重复、悬空互引与卷次字段。

    python book/glossary_lint.py --write-baseline   # 首次/确认后重设基线
    python book/glossary_lint.py                    # 校验，失败返回 1
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "book"))

from build_glossary import OUTPUT, table_rows  # noqa: E402
from references import ReferenceIndex  # noqa: E402

TERMINOLOGY = ROOT / "book" / "terminology.json"
SOURCES = [ROOT / "analog" / "docs", ROOT / "bms-book" / "book"]


def source_files() -> list[Path]:
    files = []
    for directory in SOURCES:
        files.extend(sorted(directory.glob("*.md")))
    return files


def counts(files: list[Path], phrases: list[str]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for path in files:
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            number = text.count(phrase)
            if number:
                result.setdefault(str(path.relative_to(ROOT)), {})[phrase] = number
    return result


def load_term_config() -> dict:
    return json.loads(TERMINOLOGY.read_text(encoding="utf-8"))


def all_forbidden(config: dict) -> list[str]:
    return [phrase for item in config["terms"] for phrase in item["forbidden"]]


def write_baseline() -> None:
    config = load_term_config()
    files = source_files() + [OUTPUT]
    config["baseline"] = counts(files, all_forbidden(config))
    TERMINOLOGY.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(f"已重设术语基线：{len(config['baseline'])} 个文件")


def lint() -> list[str]:
    problems: list[str] = []
    config = load_term_config()
    rows = table_rows(OUTPUT)
    if not rows:
        return ["术语表为空"]

    index = ReferenceIndex()
    labels = {chapter.label for chapter in index.chapters.values()}
    terms: dict[str, str] = {}
    english: dict[str, str] = {}
    names: set[str] = set()
    for number, row in enumerate(rows, 2):
        if len(row) != 5:
            problems.append(f"术语表第 {number} 行列数不是 5：{row}")
            continue
        term, eng, _, volume, _ = row
        key = re.sub(r"[（(].*?[）)]", "", term).strip().lower()
        if key in terms:
            problems.append(f"术语重复：{term}（第 {number} 行）")
        terms[key] = term
        names.add(term.lower())
        names.add(key)
        for inner in re.findall(r"[（(](.*?)[）)]", term):
            names.add(inner.strip().lower())
        if eng not in ("—", ""):
            if eng.lower() in english:
                problems.append(f"英文名重复：{eng}（{term} / {english[eng.lower()]}）")
            english[eng.lower()] = term
        if volume not in ("卷一", "卷二", "两卷"):
            problems.append(f"所属卷无效：{term} -> {volume}")

    candidates = [(name, name) for name in names | {label.lower() for label in labels}]
    candidates.sort(key=lambda item: len(item[0]), reverse=True)

    def resolve(related: str) -> str | None:
        rest = related.strip()
        while rest and rest != "—":
            rest = rest.lstrip("、,， ")
            if not rest:
                return None
            lowered = rest.lower()
            for name, _ in candidates:
                if lowered.startswith(name):
                    rest = rest[len(name):]
                    break
            else:
                return re.split(r"[、,，]", rest, maxsplit=1)[0]
        return None

    for row in rows[1:]:
        if len(row) != 5:
            continue
        term, _, _, _, related = row
        if related in ("—", ""):
            continue
        dangling = resolve(related)
        if dangling:
            problems.append(f"相关条目悬空：{term} -> {dangling}")

    forbidden = all_forbidden(config)
    current = counts(source_files() + [OUTPUT], forbidden)
    # 基线键在不同平台可能带反斜杠（Windows 写入）——比较时统一成正斜杠，
    # 否则 Linux CI 上 baseline.get 全部落空，既有变体全被误报为「新增」。
    baseline = {str(k).replace("\\", "/"): v for k, v in config.get("baseline", {}).items()}
    for file, phrases in current.items():
        for phrase, number in phrases.items():
            allowed = baseline.get(str(file).replace("\\", "/"), {}).get(phrase, 0)
            if number > allowed:
                problems.append(f"禁用变体新增：{file} 中「{phrase}」{allowed} -> {number}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="术语表与术语登记 lint")
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args(argv)
    if args.write_baseline:
        write_baseline()
        return 0
    problems = lint()
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"术语 lint：{len(problems)} 个问题", file=sys.stderr if problems else sys.stdout)
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
