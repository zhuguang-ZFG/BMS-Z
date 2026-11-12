#!/usr/bin/env python3
"""跨卷引用解析与审计（设计 §9）。

引用源保持普通相对链接，指向对方卷的书稿文件（GitHub/Obsidian 可直接打开）：

    卷 II → 卷 I：`../../analog/docs/p1-10-ch9.md#ch9`
    卷 I → 卷 II：`../../bms-book/book/06-AFE.md`

本模块把这类链接解析到唯一章（或附录），供三种介质改写：
站点版换成可点击路由，印刷版与单文件 HTML 降级为「卷二·第 N 章《标题》」。
审计对悬空目标、悬空锚点和手写「见卷 X」的链接文本报错。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALOG_ROOT = ROOT / "analog" / "docs"
BMS_ROOT = ROOT / "bms-book" / "book"
ANALOG_MANIFEST = ROOT / "analog" / "analog-book" / "manifest.json"
BMS_MANIFEST = ROOT / "bms-book" / "manifest.json"

KEEP = re.compile(r"[^\w\s-]", re.UNICODE)
LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)")
ANCHOR = re.compile(r'<a\s+id="([^"]+)"')
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def github_slugify(heading: str) -> str:
    """与 docs/.vitepress/config.mts 的 githubSlugify 及 check_docs.py 同步。"""
    text = unicodedata.normalize("NFC", heading).strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return text.replace(" ", "-")


@dataclass(frozen=True)
class Chapter:
    volume: str
    number: str
    title: str
    source: Path

    @property
    def short_title(self) -> str:
        text = re.sub(r"^第\s*\d+\s*章\s*", "", self.title).strip()
        return re.sub(r"^附录\s*[A-Z]\s*", "", text).strip()

    @property
    def volume_name(self) -> str:
        return "卷一" if self.volume == "I" else "卷二"

    @property
    def label(self) -> str:
        if self.number.startswith("附录"):
            return f"{self.volume_name}·{self.number}《{self.short_title}》"
        return f"{self.volume_name}·第 {self.number} 章《{self.short_title}》"

    @property
    def site_path(self) -> str:
        stem = self.source.stem
        if self.volume == "I":
            return f"/volume-1/{stem}.html"
        return f"/book/{stem}.html"


def _first_heading(path: Path, levels: str = "#") -> str:
    pattern = re.compile(rf"^{levels}\s+(.+?)\s*$", re.MULTILINE)
    match = pattern.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"章节缺少标题：{path}")
    return re.sub(r"<[^>]+>", "", match.group(1)).strip()


def _anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {match.group(1) for match in ANCHOR.finditer(text)} | {
        github_slugify(match.group(2)) for match in HEADING.finditer(text)
    }


def load_chapters() -> dict[Path, Chapter]:
    analog = json.loads(ANALOG_MANIFEST.read_text(encoding="utf-8"))
    bms = json.loads(BMS_MANIFEST.read_text(encoding="utf-8"))
    chapters: dict[Path, Chapter] = {}

    files: list[str] = []
    for part in analog.get("parts", []):
        for unit in part.get("units", []):
            files.extend(unit.get("chapters", []))
    for name in files:
        path = (ANALOG_ROOT / name).resolve()
        number = re.search(r"ch(\d+)\.md$", name)
        title = _first_heading(path, "##")
        chapters[path] = Chapter("I", number.group(1), title, path)
    for appendix in analog.get("appendices", []):
        for name in appendix.get("files", []):
            path = (ANALOG_ROOT / name).resolve()
            chapters[path] = Chapter("I", f"附录 {appendix['id']}", appendix["title"], path)

    files = [name for part in bms.get("parts", []) for name in part.get("files", [])
             if not name.startswith("00-")]
    appendix_files = sorted(path.name for path in BMS_ROOT.glob("附录*.md"))
    for name in files:
        path = (BMS_ROOT / name).resolve()
        number = re.match(r"(\d{2})-", name)
        if not number:
            continue
        title = _first_heading(path, "#")
        chapters[path] = Chapter("II", str(int(number.group(1))), title, path)
    for index, name in enumerate(appendix_files, 1):
        path = (BMS_ROOT / name).resolve()
        chapters[path] = Chapter("II", f"附录 {chr(64 + index)}", _first_heading(path, "#"), path)

    return chapters


class ReferenceIndex:
    def __init__(self, chapters: dict[Path, Chapter] | None = None) -> None:
        self.chapters = chapters or load_chapters()
        self.by_source = {path: chapter for path, chapter in self.chapters.items()}
        self._anchors: dict[Path, set[str]] = {}

    def resolve(self, source: Path, href: str) -> tuple[Chapter, str] | None:
        """解析跨卷链接；卷内链接与非书稿链接返回 None。"""
        if href.startswith(("http:", "https:", "mailto:", "/", "#")):
            return None
        path_part, _, anchor = href.partition("#")
        if not path_part.endswith(".md"):
            return None
        target = (source.parent / path_part).resolve()
        chapter = self.by_source.get(target)
        if chapter is None:
            return None
        volume_root = ANALOG_ROOT if source.is_relative_to(ANALOG_ROOT) else BMS_ROOT
        target_root = ANALOG_ROOT if target.is_relative_to(ANALOG_ROOT) else BMS_ROOT
        if source.is_relative_to(volume_root) and volume_root != target_root:
            return chapter, anchor
        return None

    def anchors(self, path: Path) -> set[str]:
        if path not in self._anchors:
            self._anchors[path] = _anchors(path)
        return self._anchors[path]

    def audit(self) -> list[str]:
        problems: list[str] = []
        for root in (ANALOG_ROOT, BMS_ROOT):
            for source in sorted(root.glob("*.md")):
                text = source.read_text(encoding="utf-8")
                for match in LINK.finditer(text):
                    link_text, href = match.group(1), match.group(2)
                    resolved = self.resolve(source, href)
                    if resolved is None:
                        continue
                    chapter, anchor = resolved
                    if anchor and anchor not in self.anchors(chapter.source):
                        problems.append(
                            f"{source.relative_to(ROOT)}: 锚点不存在于 {chapter.label}：#{anchor}")
                    if re.search(r"卷\s*[一二]", link_text):
                        problems.append(
                            f"{source.relative_to(ROOT)}: 链接文本手写了卷次（应交给装配层）：{link_text}")
        return problems


def format_reference(index: ReferenceIndex, source: Path, href: str) -> str | None:
    resolved = index.resolve(source, href)
    if resolved is None:
        return None
    chapter, _ = resolved
    return chapter.label


def site_href(index: ReferenceIndex, source: Path, href: str, base: str = "") -> str | None:
    resolved = index.resolve(source, href)
    if resolved is None:
        return None
    chapter, anchor = resolved
    suffix = f"#{anchor}" if anchor else ""
    return f"{base}{chapter.site_path}{suffix}"


def describe(index: ReferenceIndex) -> dict:
    volumes: dict[str, list[dict]] = {"I": [], "II": []}
    for chapter in index.chapters.values():
        volumes[chapter.volume].append({
            "number": chapter.number,
            "title": chapter.title,
            "source": str(chapter.source.relative_to(ROOT)),
            "site_path": chapter.site_path,
        })
    for items in volumes.values():
        items.sort(key=lambda item: (not item["number"].isdigit(), item["number"]))
    return {"volumes": volumes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="跨卷引用解析与审计")
    parser.add_argument("--check", action="store_true", help="只审计，有问题返回 1")
    parser.add_argument("--json", action="store_true", help="输出章节索引 JSON")
    args = parser.parse_args(argv)

    index = ReferenceIndex()
    if args.json:
        print(json.dumps(describe(index), ensure_ascii=False, indent=2))
    problems = index.audit()
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"跨卷引用审计：{len(index.chapters)} 章/附录，{len(problems)} 个问题",
          file=sys.stderr if args.json else sys.stdout)
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
