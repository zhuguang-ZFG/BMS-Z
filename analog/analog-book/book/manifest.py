"""schema-2 manifest：加载、覆盖校验与 77 个逻辑页描述。"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from .config import DOCS, MANIFEST_PATH

SCHEMA_VERSION = 2
PART_IDS = ["I", "II", "III", "IV", "V"]
APPENDIX_IDS = list("ABCDEFGH")
APPENDIX_FILE_COUNTS = {"A": 0, "B": 1, "C": 5, "D": 11, "E": 6, "F": 1, "G": 2, "H": 1}
NEW_PAGES = {"p0-11-conventions.md", "p0-12-symbols.md", "p9-15-glossary.md"}
EXCLUDED_ALLOWED = {
    "index.md", "p0-07-toc.md",
    "p1-00-part1.md", "p2-00-part2.md", "p3-00-part3.md", "p4-00-part4.md",
    "p5-00-part5.md", "p6-00-part6.md", "p7-00-part7.md", "p8-00-part8.md",
}
CHAPTER_RE = re.compile(r"^p\d+-\d+-ch(\d+)\.md$")
FRONT_KINDS = {"half_title", "title_page", "copyright", "toc",
               "list_of_figures", "list_of_tables"}
BACK_KINDS = {"bibliography", "index", "colophon"}

TOTAL_CHAPTERS = 19
EXISTING_DIRECT_COUNT = 51
EXCLUDED_COUNT = 10
EDITION_STATUSES = {"draft", "final"}
SECTIONS = ("front_matter", "parts", "appendices", "back_matter")

METADATA_KEYS = ("title", "subtitle", "edition", "version", "source_version",
                 "date", "language", "author", "site_url", "repository", "license")

FRONT_GENERATED = {
    "half_title": ("half-title", "半书名页"),
    "title_page": ("title-page", "书名页"),
    "copyright": ("copyright", "版权页"),
    "toc": ("toc", "目录"),
    "list_of_figures": ("list-of-figures", "插图目录"),
    "list_of_tables": ("list-of-tables", "表格目录"),
}
BACK_GENERATED = {
    "bibliography": ("bibliography", "参考文献"),
    "index": ("index", "索引"),
    "colophon": ("colophon", "版本页"),
}


class BookError(Exception):
    """manifest 或页面结构不满足 schema-2 约定。"""


def load_manifest(path: str | Path = MANIFEST_PATH) -> dict:
    """读取 manifest JSON；解析失败时抛出 :class:`BookError`。"""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BookError(f"manifest JSON 解析失败：{path}") from exc


def manifest_sha256(path: str | Path = MANIFEST_PATH) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def direct_files(manifest: dict) -> list[str]:
    """直接进入书内的源文件（前置、章节、附录、后置），不含生成页。"""
    files = [entry["file"] for entry in manifest.get("front_matter") or []
             if "file" in entry]
    for part in manifest.get("parts") or []:
        for unit in part.get("units") or []:
            files.extend(unit.get("chapters") or [])
    for appendix in manifest.get("appendices") or []:
        files.extend(appendix.get("files") or [])
    files.extend(entry["file"] for entry in manifest.get("back_matter") or []
                 if "file" in entry)
    return files


def excluded_files(manifest: dict) -> list[str]:
    """明确排除、由书内生成页替代的 docs 页面。"""
    return [entry["file"] for entry in manifest.get("excluded_pages") or []
            if entry.get("file")]


def validate_manifest(manifest: dict, docs_dir: str | Path = DOCS) -> None:
    """校验 schema-2 manifest；不满足时抛出 :class:`BookError`。"""
    _validate_section_types(manifest)
    _validate_section_entries(manifest)
    _validate_header(manifest)
    _validate_unique_direct(direct_files(manifest))
    _validate_front_matter(manifest)
    _validate_parts(manifest)
    _validate_appendices(manifest)
    _validate_back_matter(manifest)
    _validate_excluded(manifest)
    _validate_coverage(manifest, Path(docs_dir))
    _validate_cover(manifest)
    _validate_release(manifest)


def book_pages(manifest: dict) -> list[dict]:
    """按前置、正文、附录、后置的固定顺序给出全部逻辑页。"""
    pages: list[dict] = []
    _front_pages(manifest, pages)
    _body_pages(manifest, pages)
    _appendix_pages(manifest, pages)
    _back_pages(manifest, pages)
    return pages


def _page(kind: str, stem: str, title: str, *, file: str | None = None,
          part_id: str | None = None, part_title: str | None = None,
          unit_title: str | None = None, appendix_id: str | None = None,
          transform: str | None = None, generated: bool = False) -> dict:
    return {
        "kind": kind,
        "stem": stem,
        "title": title,
        "file": file,
        "part_id": part_id,
        "part_title": part_title,
        "unit_title": unit_title,
        "appendix_id": appendix_id,
        "transform": transform,
        "generated": generated,
    }


def _front_pages(manifest: dict, pages: list[dict]) -> None:
    for entry in manifest.get("front_matter", []):
        kind = entry.get("kind")
        if kind:
            stem, title = FRONT_GENERATED[kind]
            pages.append(_page(kind, stem, title, generated=True))
        else:
            name = entry["file"]
            pages.append(_page("front", Path(name).stem, entry["title"], file=name))


def _body_pages(manifest: dict, pages: list[dict]) -> None:
    for part in manifest.get("parts", []):
        part_id = part["id"]
        part_title = part["title"]
        pages.append(_page(
            "part", f"part-{part_id}", f"第 {part_id} 篇 {part_title}",
            part_id=part_id, part_title=part_title, generated=True))
        for unit in part.get("units", []):
            unit_title = unit.get("title", "")
            for name in unit.get("chapters", []):
                stem = Path(name).stem
                pages.append(_page(
                    "chapter", stem, stem, file=name, part_id=part_id,
                    part_title=part_title, unit_title=unit_title))


def _appendix_pages(manifest: dict, pages: list[dict]) -> None:
    for appendix in manifest.get("appendices", []):
        appendix_id = appendix["id"]
        title = appendix["title"]
        transform = appendix.get("transform")
        pages.append(_page(
            "appendix_opener", f"appendix-{appendix_id}",
            f"附录 {appendix_id} {title}", appendix_id=appendix_id,
            transform=transform, generated=True))
        if transform == "animation_index":
            pages.append(_page(
                "appendix", f"appendix-{appendix_id}-index", title,
                appendix_id=appendix_id, transform=transform, generated=True))
        if transform == "answers":
            # 题库原文由答案页替代，本身不进入 77 页。
            pages.append(_page(
                "appendix", f"appendix-{appendix_id}-answers", title,
                appendix_id=appendix_id, transform=transform, generated=True))
            continue
        for name in appendix.get("files", []):
            stem = Path(name).stem
            pages.append(_page(
                "appendix", stem, stem, file=name, appendix_id=appendix_id,
                transform=transform))


def _back_pages(manifest: dict, pages: list[dict]) -> None:
    for entry in manifest.get("back_matter", []):
        kind = entry.get("kind")
        if kind:
            stem, title = BACK_GENERATED[kind]
            pages.append(_page(kind, stem, title, generated=True))
        else:
            name = entry["file"]
            pages.append(_page("back", Path(name).stem, entry["title"], file=name))


def _validate_section_types(manifest: dict) -> None:
    """四个清单段必须是列表；null 先归一为空列表，再由各规则报错。"""
    for key in SECTIONS:
        value = manifest.get(key)
        if value is not None and not isinstance(value, list):
            raise BookError(f"{key} 必须是列表")


def _validate_section_entries(manifest: dict) -> None:
    """清单段内每条记录必须是对象，避免后续 .get 抛 AttributeError。"""
    for key in SECTIONS:
        for entry in manifest.get(key) or []:
            if not isinstance(entry, dict):
                raise BookError(f"{key} 的条目必须是对象")


def _validate_header(manifest: dict) -> None:
    schema = manifest.get("schema")
    if schema != SCHEMA_VERSION:
        raise BookError(f"manifest.schema 必须为 {SCHEMA_VERSION}，当前为 {schema!r}")
    for key in METADATA_KEYS:
        value = manifest.get(key)
        if not isinstance(value, str) or not value.strip():
            raise BookError(f"manifest.{key} 不能为空")
    trim = manifest.get("trim") or {}
    width = trim.get("width_mm")
    height = trim.get("height_mm")
    if width != 185 or height != 260:
        raise BookError(f"trim 必须是 185×260 mm，当前为 {width}×{height}")


def _validate_unique_direct(files: list[str]) -> None:
    duplicates = sorted(name for name, count in Counter(files).items() if count > 1)
    if duplicates:
        raise BookError(f"直接页文件重复：{', '.join(duplicates)}")


def _validate_front_matter(manifest: dict) -> None:
    entries = manifest.get("front_matter") or []
    if not isinstance(entries, list):
        raise BookError("front_matter 必须是列表")
    for entry in entries:
        if "kind" in entry and not isinstance(entry["kind"], str):
            raise BookError(
                f"front_matter 的 kind 必须是字符串，当前为 {entry['kind']!r}")
    kinds = [entry["kind"] for entry in entries if "kind" in entry]
    unknown = sorted(set(kinds) - FRONT_KINDS)
    if unknown:
        raise BookError(f"front_matter 含未知生成页：{', '.join(unknown)}")
    repeated = sorted(kind for kind, count in Counter(kinds).items() if count > 1)
    if repeated:
        raise BookError(f"front_matter 生成页重复：{', '.join(repeated)}")
    missing = sorted(FRONT_KINDS - set(kinds))
    if missing:
        raise BookError(f"front_matter 缺少生成页：{', '.join(missing)}")
    for entry in entries:
        if "kind" in entry:
            if "file" in entry:
                raise BookError("front_matter 条目不能同时给出 kind 与 file")
            continue
        name = entry.get("file")
        if not isinstance(name, str) or not name.endswith(".md"):
            raise BookError("front_matter 的文件页必须给出 .md 文件")
        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            raise BookError(f"front_matter {name} 缺少 title")


def _validate_parts(manifest: dict) -> None:
    parts = manifest.get("parts") or []
    ids = [part.get("id") for part in parts]
    if ids != PART_IDS:
        raise BookError(f"parts ID 必须依次为 {PART_IDS}，当前为 {ids}")
    numbers: list[int] = []
    for part in parts:
        units = part.get("units") or []
        if not units:
            raise BookError(f"第 {part.get('id')} 篇必须至少有一个单元")
        for unit in units:
            title = unit.get("title")
            if not isinstance(title, str) or not title.strip():
                raise BookError(f"第 {part.get('id')} 篇存在没有标题的单元")
            chapters = unit.get("chapters") or []
            if not chapters:
                raise BookError(f"第 {part.get('id')} 篇的单元 {title!r} 没有章节")
            for name in chapters:
                match = CHAPTER_RE.match(str(name))
                if not match:
                    raise BookError(f"章节文件名不符合 pN-N-chN.md：{name}")
                numbers.append(int(match.group(1)))
    if len(numbers) != TOTAL_CHAPTERS:
        raise BookError(f"正文章节必须为 {TOTAL_CHAPTERS} 个，当前为 {len(numbers)}")
    expected = list(range(TOTAL_CHAPTERS))
    if numbers != expected:
        raise BookError(
            f"章节编号必须依次为 0..{TOTAL_CHAPTERS - 1}，当前为 {numbers}")


def _validate_appendices(manifest: dict) -> None:
    appendices = manifest.get("appendices") or []
    ids = [appendix.get("id") for appendix in appendices]
    if ids != APPENDIX_IDS:
        raise BookError(
            f"附录 ID 必须依次为 {''.join(APPENDIX_IDS)}，当前为 {ids}")
    by_id: dict[str, dict] = {}
    for appendix in appendices:
        appendix_id = appendix.get("id")
        by_id[appendix_id] = appendix
        title = appendix.get("title")
        if not isinstance(title, str) or not title.strip():
            raise BookError(f"附录 {appendix_id} 缺少标题")
        files = appendix.get("files", [])
        if not isinstance(files, list):
            raise BookError(f"附录 {appendix_id} 的 files 必须是列表")
    if by_id["A"].get("transform") != "animation_index" or not by_id["A"].get("data"):
        raise BookError("附录 A 必须使用 animation_index 变换并给出 data")
    if by_id["F"].get("transform") != "answers":
        raise BookError("附录 F 必须使用 answers 变换")
    for appendix_id in APPENDIX_IDS:
        expected = APPENDIX_FILE_COUNTS[appendix_id]
        actual = len(by_id[appendix_id].get("files") or [])
        if actual != expected:
            raise BookError(
                f"附录 {appendix_id} 的文件数应为 {expected}，当前为 {actual}")


def _validate_back_matter(manifest: dict) -> None:
    entries = manifest.get("back_matter") or []
    for entry in entries:
        if "kind" in entry and not isinstance(entry["kind"], str):
            raise BookError(
                f"back_matter 的 kind 必须是字符串，当前为 {entry['kind']!r}")
    kinds = [entry["kind"] for entry in entries if "kind" in entry]
    unknown = sorted(set(kinds) - BACK_KINDS)
    if unknown:
        raise BookError(f"back_matter 含未知生成页：{', '.join(unknown)}")
    for kind in ("bibliography", "index", "colophon"):
        if kinds.count(kind) != 1:
            raise BookError(f"back_matter 必须恰好包含一个 {kind} 生成页")
    for entry in entries:
        if "kind" in entry:
            continue
        name = entry.get("file")
        if not isinstance(name, str) or not name.endswith(".md"):
            raise BookError("back_matter 的文件页必须给出 .md 文件")
        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            raise BookError(f"back_matter {name} 缺少 title")


def _validate_excluded(manifest: dict) -> None:
    entries = manifest.get("excluded_pages") or []
    files = [entry.get("file") for entry in entries]
    if set(files) != EXCLUDED_ALLOWED or len(files) != len(EXCLUDED_ALLOWED):
        listed = sorted(name for name in files if name)
        raise BookError(
            f"排除页清单必须恰好为 {sorted(EXCLUDED_ALLOWED)}，当前为 {listed}")
    for entry in entries:
        name = entry.get("file")
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise BookError(f"排除页 {name} 缺少 reason")


def _validate_coverage(manifest: dict, docs_dir: Path) -> None:
    if not docs_dir.is_dir():
        raise BookError(f"docs 目录不存在：{docs_dir}")
    docs = {path.name for path in docs_dir.glob("*.md")}
    direct = direct_files(manifest)
    excluded = excluded_files(manifest)
    named = set(direct) | set(excluded)
    uncovered = sorted(docs - named)
    if uncovered:
        raise BookError(f"docs 页面未被清单覆盖或未排除：{', '.join(uncovered)}")
    unknown = sorted(named - docs)
    if unknown:
        raise BookError(f"清单中的页面在 docs 中不存在：{', '.join(unknown)}")
    missing_new = sorted(NEW_PAGES - set(direct))
    if missing_new:
        raise BookError(f"新增页面必须直入：{', '.join(missing_new)}")
    existing = [name for name in direct if name not in NEW_PAGES]
    if len(existing) != EXISTING_DIRECT_COUNT:
        raise BookError(
            f"既有文档必须直入 {EXISTING_DIRECT_COUNT} 个，当前为 {len(existing)}")
    if len(excluded) != EXCLUDED_COUNT:
        raise BookError(f"排除页必须为 {EXCLUDED_COUNT} 个，当前为 {len(excluded)}")


def _validate_cover(manifest: dict) -> None:
    cover = manifest.get("cover") or {}
    if "spine_mm" in cover:
        raise BookError("cover.spine_mm 必须由页数与纸厚计算，不能手写")
    for key in ("bleed_mm", "paper_caliper_mm", "spine_allowance_mm"):
        value = cover.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise BookError(f"cover.{key} 必须为正数")


def _validate_release(manifest: dict) -> None:
    release = manifest.get("release") or {}
    status = release.get("edition_status")
    if status not in EDITION_STATUSES:
        raise BookError(
            f"release.edition_status 必须为 draft 或 final，当前为 {status!r}")
