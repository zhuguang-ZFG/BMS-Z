"""书内数据台账：动画、索引、来源、审读签字与参考文献。"""
from __future__ import annotations

import re
from pathlib import Path

import yaml
from pypinyin import Style, lazy_pinyin

from . import config
from .manifest import BookError

ANIMATION_FIELDS = {"id", "file", "title", "chapter", "anchor", "one_line", "static_svg"}
INDEX_FIELDS = {"term", "english", "primary", "anchors", "see_also"}
SOURCE_FIELDS = {"id", "chapter", "claim", "source_type", "citation",
                 "url_or_doi", "verified_on", "verifier"}
REFERENCE_FIELDS = {"id", "authors", "title", "edition", "publisher",
                    "year", "isbn_or_url", "chapters"}
REFERENCE_OPTIONAL_FIELDS = {"notes"}  # notes：OSS 用途/许可立场与 optional-deep-read 标注（Task 11c）
SIGNOFF_FIELDS = {"chapter", "draft_version", "technical_reviewer",
                  "editorial_reviewer", "safety_reviewer", "date", "open_issues"}
SOURCE_TYPES = {"教材", "数据手册", "应用笔记", "论文", "仓库实测", "仿真"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_list(path: Path) -> list[dict]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise BookError(f"{path.name}: YAML 解析失败: {exc}") from exc
    if not isinstance(value, list):
        raise BookError(f"{path.name}: 顶层必须是列表")
    if not all(isinstance(item, dict) for item in value):
        raise BookError(f"{path.name}: 列表项必须是映射")
    return value


def _fields(item: dict, expected: set[str], where: str,
            optional: frozenset[str] = frozenset()) -> None:
    missing = sorted(expected - item.keys())
    unknown = sorted(item.keys() - expected - optional)
    if missing:
        raise BookError(f"{where}: 缺字段 {missing}")
    if unknown:
        raise BookError(f"{where}: 未知字段 {unknown}")


def _nonempty(item: dict, names: tuple[str, ...], where: str) -> None:
    for name in names:
        value = item[name]
        if not isinstance(value, str) or not value.strip():
            raise BookError(f"{where}: {name} 不能为空")


# 动画总数：改这个常量即可，scripts/build_book_data.py 的上限断言、docs 徽章与
# 统计口径同步改；test_real_generator_matches_committed_yaml 会对账真实清单。
EXPECTED_ANIMATIONS = 153

def validate_animations(items: list[dict], static_root: Path = config.ROOT) -> None:
    if len(items) != EXPECTED_ANIMATIONS:
        raise BookError(f"animations.yml 应恰好 {EXPECTED_ANIMATIONS} 条，实际 {len(items)}")
    ids, anchors = set(), set()
    for index, item in enumerate(items, 1):
        where = f"animations.yml 第 {index} 条"
        _fields(item, ANIMATION_FIELDS, where)
        _nonempty(item, ("id", "file", "title", "anchor", "one_line", "static_svg"), where)
        if item["id"] in ids:
            raise BookError(f"{where}: id 重复 {item['id']}")
        if item["anchor"] in anchors:
            raise BookError(f"{where}: anchor 重复 {item['anchor']}")
        ids.add(item["id"])
        anchors.add(item["anchor"])
        if item["file"] != "p5-00-part5.md":
            raise BookError(f"{where}: file 必须是 p5-00-part5.md")
        if not isinstance(item["chapter"], int) or not 0 <= item["chapter"] <= 18:
            raise BookError(f"{where}: chapter 必须是 0–18")
        if not re.fullmatch(r"demo\d+", item["anchor"]):
            raise BookError(f"{where}: anchor 必须形如 demo12")
        # 与 build_site/build_book_data 同口径：legacy 在 assets/svg/，
        # 批次换图后的 V2 在 assets/svg-v2/；仍限动画目录、仍验文件存在。
        if not re.fullmatch(r"assets/svg(?:-v2)?/[\w\-]+\.svg", item["static_svg"]):
            raise BookError(f"{where}: static_svg 必须位于 assets/svg/ 或 assets/svg-v2/")
        if not (static_root / item["static_svg"]).is_file():
            raise BookError(f"{where}: 静态图不存在 {item['static_svg']}")
    covered = {item["chapter"] for item in items}
    if covered != set(range(19)):
        raise BookError(f"动画未覆盖全部 19 章；缺少 {sorted(set(range(19)) - covered)}")


def validate_index_terms(items: list[dict], anchors: set[str],
                         final: bool = False) -> None:
    if final and not 300 <= len(items) <= 400:
        raise BookError(f"索引应为 300–400 条，实际 {len(items)}")
    names = set()
    for index, item in enumerate(items, 1):
        where = f"index-terms.yml 第 {index} 条"
        _fields(item, INDEX_FIELDS, where)
        _nonempty(item, ("term", "english", "primary"), where)
        if item["term"] in names:
            raise BookError(f"{where}: 术语重复 {item['term']}")
        names.add(item["term"])
        if not isinstance(item["anchors"], list) or not item["anchors"]:
            raise BookError(f"{where}: anchors 必须是非空列表")
        if not isinstance(item["see_also"], list):
            raise BookError(f"{where}: see_also 必须是列表")
        for anchor in [item["primary"], *item["anchors"]]:
            if anchor not in anchors:
                raise BookError(f"{where}: 索引锚点不存在 {anchor}")
    for item in items:
        for other in item["see_also"]:
            if other not in names:
                raise BookError(f"{item['term']}: see_also 指向未知术语 {other}")


def pinyin_key(term: str) -> str:
    return "".join(lazy_pinyin(term, style=Style.NORMAL)).lower()


def index_sections(terms: list[dict]) -> list[tuple[str, list[dict]]]:
    ordered = sorted(terms, key=lambda item: (pinyin_key(item["term"]), item["term"]))
    groups: dict[str, list[dict]] = {}
    for item in ordered:
        key = pinyin_key(item["term"])
        letter = key[0].upper() if key and key[0].isalpha() else "#"
        groups.setdefault(letter, []).append(item)
    return sorted(groups.items())


def validate_sources(items: list[dict], used_ids: set[str] | None = None,
                     final: bool = False) -> None:
    ids = set()
    for index, item in enumerate(items, 1):
        where = f"sources.yml 第 {index} 条"
        _fields(item, SOURCE_FIELDS, where)
        _nonempty(item, ("id", "claim", "citation", "url_or_doi", "verifier"), where)
        if item["id"] in ids:
            raise BookError(f"{where}: id 重复 {item['id']}")
        ids.add(item["id"])
        if not isinstance(item["chapter"], int) or not 0 <= item["chapter"] <= 18:
            raise BookError(f"{where}: chapter 必须是 0–18")
        if item["source_type"] not in SOURCE_TYPES:
            raise BookError(f"{where}: source_type 不在枚举内")
        if not DATE_RE.match(str(item["verified_on"])):
            raise BookError(f"{where}: verified_on 必须是 YYYY-MM-DD")
    if used_ids is None:
        if final:
            raise BookError("final 阶段必须提供正文片段以校验来源闭合")
        return
    missing = sorted(used_ids - ids)
    unused = sorted(ids - used_ids)
    if missing and final:
        raise BookError(f"正文引用的来源不存在: {missing}")
    if unused and final:
        raise BookError(f"sources.yml 有未使用条目: {unused}")


def used_source_ids(fragment: str) -> set[str]:
    return set(re.findall(r'data-source="([^"]+)"', fragment))


def validate_signoffs(items: list[dict], final: bool = False) -> None:
    if len(items) != 19:
        raise BookError(f"chapter-signoff.yml 应有 19 条，实际 {len(items)}")
    chapters = [item.get("chapter") for item in items]
    if chapters != list(range(19)):
        raise BookError("chapter-signoff.yml 必须按 0–18 每章一条")
    for item in items:
        where = f"chapter-signoff.yml 第 {item['chapter']} 章"
        _fields(item, SIGNOFF_FIELDS, where)
        if not DATE_RE.match(str(item["date"])):
            raise BookError(f"{where}: date 必须是 YYYY-MM-DD")
        if not isinstance(item["open_issues"], list):
            raise BookError(f"{where}: open_issues 必须是列表")
        if final:
            for name in ("technical_reviewer", "editorial_reviewer", "safety_reviewer"):
                if not str(item[name]).strip():
                    raise BookError(f"{where}: final 阶段 {name} 不能为空")
            if item["open_issues"]:
                raise BookError(f"{where}: final 阶段 open_issues 必须为空")


def validate_references(items: list[dict], final: bool = False) -> None:
    if final and len(items) < 100:
        raise BookError(f"参考文献去重后应 ≥100 条，实际 {len(items)}")
    ids = set()
    for index, item in enumerate(items, 1):
        where = f"references.yml 第 {index} 条"
        _fields(item, REFERENCE_FIELDS, where, optional=REFERENCE_OPTIONAL_FIELDS)
        _nonempty(item, ("id", "authors", "title", "publisher", "isbn_or_url"), where)
        if item["id"] in ids:
            raise BookError(f"{where}: id 重复 {item['id']}")
        ids.add(item["id"])
        if not isinstance(item["year"], int):
            raise BookError(f"{where}: year 必须是整数")
        if not isinstance(item["chapters"], list) or (
                not item["chapters"] and "notes" not in item):
            # notes 在场 = OSS/工具类条目（Task 11c），允许 chapters 空列表；
            # 章节正文引用仍必须挂到具体章。
            raise BookError(f"{where}: chapters 必须是非空列表")
        if any(not isinstance(ch, int) or not 0 <= ch <= 18 for ch in item["chapters"]):
            raise BookError(f"{where}: chapters 必须是 0–18 的整数")
