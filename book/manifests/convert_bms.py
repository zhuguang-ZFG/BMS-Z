#!/usr/bin/env python3
"""把 bms-book/manifest.json 转成 schema 3 卷级 manifest，并在构建前校验。

校验三件事（设计 §6）：
  1. 章节罗盘全覆盖：每个编号章都有「本章要回答 / 读完应交出 / 这一章不证明」；
  2. 来源无孤儿：chapter_sources / book_sources 引用的来源都已登记，登记的也都有人引用；
  3. 索引术语无空项、无重复。
任何一条不过都抛 ManifestError，由调用方以非零码退出。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "bms-book" / "manifest.json"
DEFAULT_OUT = ROOT / "book" / "dist" / "manifests" / "volume-2.json"

CHAPTER_FILE_RE = re.compile(r"^\d{2}-.+\.md$")
FRONT_FILE_RE = re.compile(r"^00-")
APPENDIX_FILE_RE = re.compile(r"^附录")


class ManifestError(RuntimeError):
    """BMS 卷 manifest 不满足 schema 3 卷级契约。"""


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def _chapter_guides(manifest: dict, chapter_files: list[str]) -> dict:
    guides = manifest.get("chapter_guides", {})
    missing = sorted(set(chapter_files) - set(guides))
    extra = sorted(set(guides) - set(chapter_files))
    _require(not missing, f"章节罗盘缺章：{missing}")
    _require(not extra, f"章节罗盘指向不存在的章：{extra}")
    for name in chapter_files:
        guide = guides[name]
        for field in ("question", "deliverable", "boundary"):
            _require(bool(str(guide.get(field, "")).strip()),
                     f"{name} 的章节罗盘缺字段 {field}")
    return guides


def _sources(manifest: dict) -> tuple[dict, list[str], dict]:
    sources = manifest.get("sources", {})
    book_sources = list(manifest.get("book_sources", []))
    chapter_sources = manifest.get("chapter_sources", {})
    referenced: set[str] = set(book_sources)
    for ids in chapter_sources.values():
        referenced.update(ids)
    undefined = sorted(referenced - set(sources))
    orphans = sorted(set(sources) - referenced)
    _require(not undefined, f"引用了未登记来源：{undefined}")
    _require(not orphans, f"登记来源无人引用（孤儿）：{orphans}")
    return sources, book_sources, chapter_sources


def _index_terms(manifest: dict, base: Path) -> list[str]:
    rel = manifest.get("index_terms")
    _require(isinstance(rel, str) and rel.strip(), "index_terms 未指向术语文件")
    terms_path = base / rel
    _require(terms_path.is_file(), f"术语文件不存在：{terms_path}")
    terms = load_json(terms_path)
    _require(isinstance(terms, list), "术语文件必须是 JSON 数组")
    empty = [i for i, term in enumerate(terms)
             if not isinstance(term, str) or not term.strip()]
    _require(not empty, f"索引术语有空项或非字符串：下标 {empty}")
    _require(len(terms) == len(set(terms)), "索引术语有重复项")
    return terms


def convert(source: Path = SOURCE, volume_id: str = "II",
            print_spec: dict | None = None) -> dict:
    manifest = load_json(source)
    _require(isinstance(manifest, dict), "BMS manifest 必须是 JSON 对象")
    parts = manifest.get("parts", [])
    _require(bool(parts), "BMS manifest 没有 parts")

    files = [name for part in parts for name in part.get("files", [])]
    _require(len(files) == len(set(files)), "同一页出现在多个 part 中")

    front = [name for name in files if FRONT_FILE_RE.match(name)]
    appendix = [name for name in files if APPENDIX_FILE_RE.match(name)]
    chapters = [name for name in files
                if CHAPTER_FILE_RE.match(name) and not FRONT_FILE_RE.match(name)]
    rest = [name for name in files
            if name not in set(front) | set(appendix) | set(chapters)]
    _require(not rest, f"无法归类的页：{rest}")

    guides = _chapter_guides(manifest, chapters)
    sources, book_sources, chapter_sources = _sources(manifest)
    terms = _index_terms(manifest, source.parent)

    def goal(part_id: str) -> str | None:
        return manifest.get("part_goals", {}).get(part_id)

    chapter_set = set(chapters)
    body_parts = [part for part in parts
                  if any(name in chapter_set for name in part.get("files", []))]
    _require(bool(body_parts), "没有包含编号章的 part")

    try:
        source_label = str(source.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        source_label = str(source).replace("\\", "/")

    return {
        "schema": 3,
        "id": volume_id,
        "source_manifest": source_label,
        "title": manifest.get("title"),
        "subtitle": manifest.get("subtitle"),
        "author": manifest.get("author"),
        "license": manifest.get("license"),
        "language": manifest.get("language", "zh-CN"),
        "front_matter": [{"file": name, "title": name[3:-3]} for name in front],
        "parts": [
            {"id": part["id"], "title": part.get("title"),
             "goal": goal(part["id"]), "files": list(part["files"])}
            for part in body_parts
        ],
        "appendix": {"title": "附录", "files": appendix} if appendix else None,
        "chapter_guides": guides,
        "sources": sources,
        "book_sources": book_sources,
        "chapter_sources": chapter_sources,
        "index_terms": terms,
        "part_goals": manifest.get("part_goals", {}),
        "demos": manifest.get("demos", []),
        "keywords": manifest.get("keywords", ""),
        "print": print_spec or {"trim_mm": [185, 260], "max_pages_per_volume": 700},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BMS manifest → schema 3 卷级 manifest")
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    try:
        volume = convert(args.source)
    except ManifestError as exc:
        print(f"manifest error: {exc}", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(volume, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"volume {volume['id']}: {len(volume['parts'])} parts, "
          f"{sum(len(p['files']) for p in volume['parts'])} chapters, "
          f"{len(volume['index_terms'])} index terms -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
