"""77 页装配：前置、篇、章、附录、后置、目录、索引与审计。"""
from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import yaml

from . import (config, content, data, fonts, frontmatter, illustrations,
               intuition, quiz, transforms)
from .manifest import BookError, book_pages, load_manifest, validate_manifest

CSS_FILES = ["typography", "gallery", "learning", "reading", "diag"]
BOOK_SCRIPTS = ["calc", "learning", "learning-catalog", "diag"]
MATHJAX_PATH = config.ROOT / "assets" / "vendor" / "mathjax-svg" / "tex-svg-full.js"
CHAPTER_STEMS = {
    0: "p1-01-ch0", 1: "p1-02-ch1", 2: "p1-03-ch2", 3: "p1-04-ch3",
    4: "p1-05-ch4", 5: "p1-06-ch5", 6: "p1-07-ch6", 7: "p1-08-ch7",
    8: "p1-09-ch8", 9: "p1-10-ch9", 10: "p1-11-ch10", 11: "p2-01-ch11",
    12: "p2-02-ch12", 13: "p2-03-ch13", 14: "p3-01-ch14",
    15: "p3-02-ch15", 16: "p4-01-ch16", 17: "p4-02-ch17",
    18: "p4-03-ch18",
}
FRONT_PAGE_IDS = {
    "half-title": "half-title",
    "title-page": "title-page",
    "copyright": "copyright",
    "toc": "book-toc",
    "list-of-figures": "list-of-figures",
    "list-of-tables": "list-of-tables",
}
BACK_PAGE_IDS = {
    "bibliography": "bibliography",
    "index": "book-index",
    "colophon": "colophon",
}
FRONT_KINDS = {"half_title", "title_page", "copyright", "toc",
               "list_of_figures", "list_of_tables", "front"}
BACK_KINDS = {"bibliography", "index", "colophon", "back"}
GENERATED_APPENDIX_IDS = {
    "appendix-A-index": "appendix-a-table",
    "appendix-F-answers": "appendix-f-answers",
}
EXPECTED_PAGES = 77
WORD_TARGET = 15000
VOLUME_LABELS = {1: "上卷", 2: "下卷"}
VOLUME1_LAST_ID = "page-p1-11-ch10"
VOLUME2_FIRST_ID = "part-iii"
VOLUME_COMMON_BACK_IDS = {"bibliography", "book-index"}
# 两卷各放一份的附录：A 动画索引、B 公式速查、F 习题答案、G 术语表、H 模型边界。
# C/D/E 是整书级资源清单，只随下卷发行，避免上卷无谓增厚。
VOLUME_SHARED_APPENDIX_IDS = {"A", "B", "F", "G", "H"}
# 专题加练 34 题的解析大量引用第 III～V 篇，只收在下卷。
EXTRA_QUIZ_VOLUME = 2
INDEX_TARGET = (300, 400)
REFERENCE_TARGET = 100

EMBEDDED_BLOCK_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.S)
ID_ATTR_RE = re.compile(r'(?<![\w-])(id|name)="([^"]+)"')
H1_RE = re.compile(r"<h1\b[^>]*>.*?</h1>", re.S)
PLACEHOLDER_RE = re.compile(r"TODO|TBD|待补|占位")
DATA_URI_RE = re.compile(
    r"data:[a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=]+")
CHAPTER_NUMBER_RE = re.compile(r"-ch(\d+)$")
SCRIPT_SRC_RE = re.compile(r"<script\b[^>]*\bsrc\s*=", re.I)
A_TAG_RE = re.compile(
    r'<a\b(?P<before>[^>]*?)\s+href="#(?P<target>[^"]+)"(?P<after>[^>]*)>'
    r'(?P<body>.*?)</a>', re.S)


def _page_position(pages: list[dict], page_id: str) -> int:
    for index, page in enumerate(pages):
        if page["id"] == page_id:
            return index
    raise BookError(f"页面序列中缺少 {page_id}")


def _select_volume_pages(pages: list[dict], volume: int) -> list[dict]:
    """按自然篇界拆卷：上卷到第 10 章，下卷从第 III 篇起。

    两卷都带共享附录（A/B/F/G/H）与参考文献、索引，保证各卷自洽：章末
    「答案见附录 F」在本卷内就能翻到。
    """
    if volume not in VOLUME_LABELS:
        raise BookError(f"未知卷号: {volume}")
    front_end = _page_position(pages, "part-i")
    front = pages[:front_end]
    common_back = [page for page in pages
                   if page["id"] in VOLUME_COMMON_BACK_IDS]
    if volume == 2:
        start = _page_position(pages, VOLUME2_FIRST_ID)
        return front + pages[start:]
    end = _page_position(pages, VOLUME1_LAST_ID) + 1
    shared = [page for page in pages
              if page["group"] == "appendix"
              and page.get("appendix") in VOLUME_SHARED_APPENDIX_IDS]
    return front + pages[front_end:end] + shared + common_back


def _anchor_positions(pages: list[dict]) -> dict[str, int]:
    anchors: dict[str, int] = {}
    for index, page in enumerate(pages):
        anchors.setdefault(page["id"], index)
        for match in ID_ATTR_RE.finditer(page["html"]):
            anchors.setdefault(match.group(2), index)
    return anchors


def _filter_index_terms(terms: list[dict], pages: list[dict]) -> list[dict]:
    """分卷索引只收本卷可见锚点；see_also 同步收束到本卷词条。"""
    anchors = set(_anchor_positions(pages))
    filtered: list[dict] = []
    for item in terms:
        kept = [anchor for anchor in [item["primary"], *item["anchors"]]
                if anchor in anchors]
        if not kept:
            continue
        copied = deepcopy(item)
        copied["primary"] = kept[0]
        copied["anchors"] = kept[1:] or [kept[0]]
        filtered.append(copied)
    names = {item["term"] for item in filtered}
    for item in filtered:
        item["see_also"] = [name for name in item["see_also"] if name in names]
    return filtered


def _volume_of_anchor(anchor_positions: dict[str, int], pages: list[dict],
                      anchor: str) -> int:
    index = anchor_positions[anchor]
    last_volume1 = _page_position(pages, VOLUME1_LAST_ID)
    return 1 if index <= last_volume1 else 2


def _externalize_cross_volume_links(pages: list[dict], all_pages: list[dict],
                                    volume: int) -> int:
    """把指向另一卷的 `#anchor` 降为「见上/下卷」提示，避免分卷悬空锚点。

    返回降级次数，供构建统计与页面自洽度对账。
    """
    current = set(_anchor_positions(pages))
    all_positions = _anchor_positions(all_pages)
    degraded = 0
    for page in pages:
        def replace(match: re.Match) -> str:
            nonlocal degraded
            target = match.group("target")
            if target in current:
                return match.group(0)
            if target not in all_positions:
                return match.group(0)
            target_volume = _volume_of_anchor(all_positions, all_pages, target)
            if target_volume == volume:
                return match.group(0)
            label = VOLUME_LABELS[target_volume]
            degraded += 1
            return (f'<span class="book-cross-volume" title="该目标在{label}">'
                    f'{match.group("body")}<small>（见{label}）</small></span>')
        page["html"] = A_TAG_RE.sub(replace, page["html"])
    return degraded


def _referenced_anchors(pages: list[dict]) -> set[str]:
    """本卷内容页实际引用的 `#anchor` 集合（生成页此时还是空壳）。"""
    return {match.group("target") for page in pages
            for match in A_TAG_RE.finditer(page["html"])}


def _volume_chapters(pages: list[dict]) -> set[int]:
    numbers = set()
    for page in pages:
        if page["kind"] != "chapter":
            continue
        match = CHAPTER_NUMBER_RE.search(page["stem"])
        if match:
            numbers.add(int(match.group(1)))
    return numbers


def _retarget_volume_appendices(pages: list[dict], volume: int,
                                animations: list[dict],
                                quiz_data: quiz.QuizData) -> None:
    """附录 A/F 按本卷章节重渲：本卷的章 + 本卷正文引用到的条目都留下。

    这样「看动画」与「答案见附录 F」在本卷内闭合，不再降级成跨卷提示。
    就地替换 `pages` 中的元素为副本，整书页对象保持原样。
    """
    chapters = _volume_chapters(pages)
    referenced = _referenced_anchors(pages)
    for position, page in enumerate(pages):
        if page["id"] == "appendix-a-table":
            kept = [item for item in animations
                    if int(item["chapter"]) in chapters
                    or f'anim-{str(item["anchor"])[4:]}' in referenced]
            body = _animation_table(kept, total=len(animations))
        elif page["id"] == "appendix-f-answers":
            extra = quiz_data.extra if volume == EXTRA_QUIZ_VOLUME else []
            scoped = quiz.QuizData(
                chapters={number: items
                          for number, items in quiz_data.chapters.items()
                          if number in chapters},
                extra=list(extra))
            label = VOLUME_LABELS[EXTRA_QUIZ_VOLUME]
            note = ("章节题按题号对应章末练习；专题题为综合加练。" if extra
                    else f'章节题按题号对应本卷章末练习；'
                         f'{len(quiz_data.extra)} 道专题加练收在{label}。')
            body = quiz.render_answers(
                scoped, CHAPTER_STEMS, page["stem"], note=note)
        else:
            continue
        pages[position] = {**page, "html": body, "headings": _headings(body)}


def _esc(value) -> str:
    return html.escape(str(value), quote=True)


def _clean_title(value) -> str:
    return transforms.strip_emoji(str(value)).strip()


def _strip_page_id(body: str, page_id: str) -> str:
    pattern = re.compile(
        r'(<h1\b[^>]*?)\s+id="%s"' % re.escape(page_id))
    return pattern.sub(r"\1", body, count=1)


def _demote_h1(fragment: str) -> str:
    """附录源页的 h1 降为 h2，保留原 id；附录标题由 opener 承担。"""
    return re.sub(
        r"<h1(?P<attrs>[^>]*)>(?P<body>.*?)</h1>",
        r"<h2\g<attrs>>\g<body></h2>", fragment, count=1, flags=re.S)


def _manifest_digest(manifest: dict) -> str:
    payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolve_final(manifest: dict, final: bool | None) -> bool:
    if final is not None:
        return bool(final)
    release = manifest.get("release") or {}
    return release.get("edition_status") == "final"


# ---------------------------------------------------------------------------
# Resource inlining ported from build_book.py (paths come from config/site_dir)
# ---------------------------------------------------------------------------

def _material_css(site_dir: Path) -> list[Path]:
    styles = site_dir / "assets" / "stylesheets"
    found = []
    for pattern in ("main.*.min.css", "palette.*.min.css"):
        matches = sorted(styles.glob(pattern))
        if not matches:
            raise BookError(f"站点缺少样式 {pattern}")
        found.append(matches[-1])
    return found


def inline_css(site_dir: Path, fonts_dir: Path = config.FONTS_DIR
               ) -> tuple[str, str, str]:
    """返回 (字体 CSS, 屏幕 CSS, 打印 CSS)；字体必须最先进入文档。"""
    font_css = fonts.font_css(fonts_dir)
    chunks = [p.read_text(encoding="utf-8") for p in _material_css(site_dir)]
    for name in CSS_FILES:
        path = site_dir / "stylesheets" / f"{name}.css"
        if not path.is_file():
            raise BookError(f"站点缺少样式 {path.name}")
        chunks.append(path.read_text(encoding="utf-8"))
    chunks.append((config.BOOK_DIR / "styles" / "book.css").read_text(encoding="utf-8"))
    print_css = (config.BOOK_DIR / "styles" / "print.css").read_text(encoding="utf-8")
    return font_css, "\n".join(chunks), print_css


def inline_scripts(site_dir: Path) -> str:
    chunks = []
    for name in BOOK_SCRIPTS:
        path = site_dir / "javascripts" / f"{name}.js"
        if not path.is_file():
            raise BookError(f"站点缺少脚本 {path.name}")
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def inline_static(name: str) -> str:
    path = config.BOOK_DIR / "static" / name
    if not path.is_file():
        raise BookError(f"缺少离线脚本: {path}")
    return path.read_text(encoding="utf-8")


MATHJAX_CONFIG = r"""<script>
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"], ["$", "$"]],
    displayMath: [["\\[", "\\]"], ["$$", "$$"]],
    processEscapes: true,
    processEnvironments: true
  },
  svg: { fontCache: "local" },
  options: { ignoreHtmlClass: ".*|", processHtmlClass: "arithmatex" }
};
</script>"""


def inline_mathjax() -> str:
    if not MATHJAX_PATH.is_file():
        raise BookError(f"缺少 MathJax SVG 包: {MATHJAX_PATH}")
    return (MATHJAX_CONFIG + "<script>"
            + MATHJAX_PATH.read_text(encoding="utf-8") + "</script>")


def _build_site(site_dir: Path) -> None:
    if site_dir.resolve() != config.SITE_DIR.resolve():
        raise BookError("自定义站点目录只能配合 rebuild_site=False 使用")
    result = subprocess.run(
        [sys.executable, "-X", "utf8",
         str(config.ROOT / "scripts" / "build_site.py"), "--build"],
        cwd=config.ROOT)
    if result.returncode != 0:
        raise BookError("站点构建失败，整书无法继续")


# ---------------------------------------------------------------------------
# 页面元数据
# ---------------------------------------------------------------------------

def _page_id(desc: dict) -> str:
    kind, stem = desc["kind"], desc["stem"]
    if desc.get("generated"):
        if stem in FRONT_PAGE_IDS:
            return FRONT_PAGE_IDS[stem]
        if kind in {"part", "appendix_opener"}:
            return stem.lower()
        if stem in BACK_PAGE_IDS:
            return BACK_PAGE_IDS[stem]
        if stem in GENERATED_APPENDIX_IDS:
            return GENERATED_APPENDIX_IDS[stem]
        raise BookError(f"生成页缺少固定 ID: {stem}")
    return f"page-{stem}"


def _model_kind(desc: dict) -> str:
    return "back" if desc["kind"] in BACK_KINDS else desc["kind"]


def _group(desc: dict) -> str:
    kind = desc["kind"]
    if kind in FRONT_KINDS:
        return "front"
    if kind in {"part", "chapter"}:
        return "body"
    if kind in {"appendix_opener", "appendix"}:
        return "appendix"
    return "back"


def _bookmark_level(desc: dict) -> int:
    kind = desc["kind"]
    if kind in FRONT_KINDS or kind in BACK_KINDS or kind == "appendix_opener":
        return 1
    if kind == "part":
        return 1
    return 2


def _header(desc: dict, appendices: dict[str, dict]) -> str:
    kind = desc["kind"]
    if kind in {"chapter", "part"}:
        return desc.get("part_title") or ""
    if kind in {"appendix_opener", "appendix"}:
        appendix = appendices.get(desc.get("appendix_id") or "", {})
        return appendix.get("title") or ""
    return ""


def _headings(fragment: str) -> list[dict]:
    return [{"level": heading.level, "text": heading.text,
             "anchor": heading.anchor, "numbered": heading.numbered}
            for heading in content.collect_headings(fragment)]


def _char_count(fragment: str) -> int:
    return len(re.sub(r"\s+", "", content.plain_text(fragment)))


def _light_body(page: content.ContentPage) -> str:
    fragment = transforms.strip_emoji(page.html)
    fragment = transforms.unwrap_details(fragment)
    fragment = transforms.transform_callouts(fragment)
    return content.wrap_tables(fragment)


def _chapter_body(page: content.ContentPage, desc: dict, quiz_data: quiz.QuizData,
                  final: bool, warnings: list[str]
                  ) -> tuple[str, list[dict], list[dict], list[dict]]:
    stem = desc["stem"]
    match = CHAPTER_NUMBER_RE.search(stem)
    if not match:
        raise BookError(f"章节文件名缺少章号: {stem}")
    chapter = int(match.group(1))
    label = str(chapter)
    fragment = transforms.strip_emoji(page.html)
    fragment = transforms.unwrap_details(fragment)
    fragment = transforms.transform_callouts(fragment)
    fragment, figures, figure_warnings = transforms.number_figures(
        fragment, label, stem, final)
    fragment, tables, table_warnings = transforms.number_tables(
        fragment, label, stem, final)
    fragment, notes = transforms.transform_endnotes(fragment, stem)
    calc_warnings = transforms.check_calculator_fallbacks(fragment, stem, final)
    warnings.extend(figure_warnings + table_warnings + calc_warnings)
    if "book-callout-goal" not in fragment:
        warnings.append(f"{stem}: 章内没有 goal 学习目标提示框")
    fragment = quiz.merge_exercises(fragment, quiz_data.chapters.get(chapter, []), stem)
    lead = intuition.chapter_lead(chapter)
    fragment = intuition.insert_lead(fragment, lead)
    # 章徽接线：站点构建已在章首舞台内联章徽（chapter-hero），书内默认沿用；
    # 站点产物缺章徽时由书内补插，保证章徽始终跟在章标题之后。
    if "chapter-emblem" not in fragment:
        art = illustrations.chapter_art(stem, warnings)
        if art:
            emblem = '<div class="chapter-emblem" aria-hidden="true">' + art + "</div>"
            fragment, placed = re.subn(
                r"</h1>", "</h1>\n" + emblem, fragment, count=1, flags=re.I)
            if placed != 1:
                warnings.append(f"{stem}: 未能插入章徽")
    return fragment, figures, tables, notes


def _appendix_body(page: content.ContentPage, desc: dict, final: bool,
                   warnings: list[str], table_start: int = 0
                   ) -> tuple[str, list[dict], list[dict], list[dict], int]:
    stem = desc["stem"]
    label = desc.get("appendix_id") or ""
    fragment = transforms.strip_emoji(page.html)
    fragment = transforms.unwrap_details(fragment)
    fragment = transforms.transform_callouts(fragment)
    fragment = _demote_h1(fragment)
    fragment, figures, figure_warnings = transforms.number_figures(
        fragment, label, stem, final)
    fragment, tables, table_warnings = transforms.number_tables(
        fragment, label, stem, final, start=table_start)
    fragment, notes = transforms.transform_endnotes(fragment, stem)
    calc_warnings = transforms.check_calculator_fallbacks(fragment, stem, final)
    warnings.extend(figure_warnings + table_warnings + calc_warnings)
    return fragment, figures, tables, notes, table_start + len(tables)


def _animation_table(animations: list[dict], total: int | None = None) -> str:
    rows = []
    for item in sorted(animations,
                       key=lambda value: (int(value["chapter"]), str(value["id"]))):
        suffix = str(item["anchor"])[4:]
        rows.append(
            f'<tr id="anim-{_esc(suffix)}">'
            f'<td>{_esc(item["id"])}</td>'
            f'<td>第 {int(item["chapter"])} 章</td>'
            f'<td>{_esc(item["title"])}</td>'
            f'<td>{_esc(item["one_line"])}</td></tr>')
    if total is None or total == len(animations):
        count = f'共 {len(animations)} 条动画，按章号排列；'
    else:
        count = (f'本卷收录 {len(animations)} 条动画（全书共 {total} 条），'
                 '按章号排列；')
    return (
        '<h1>附录 A 动画总表</h1>'
        f'<p class="animation-count">{count}'
        '打印版不收录动画中间帧。</p>'
        '<div class="table-wrap" id="appendix-a-table-wrap">'
        '<p class="table-caption">表 A-1　动画与图示总表</p>'
        '<table><thead><tr><th>编号</th><th>章节</th><th>标题</th>'
        '<th>一句看点</th></tr></thead><tbody>'
        + "".join(rows) + "</tbody></table></div>")


def _page(desc: dict, body: str, title: str, images: int = 0,
          figures: list[dict] | None = None, tables: list[dict] | None = None,
          endnotes: list[dict] | None = None, chars: int = 0,
          appendices: dict[str, dict] | None = None) -> dict:
    return {
        "index": 0,
        "kind": _model_kind(desc),
        "stem": desc["stem"],
        "id": _page_id(desc),
        "title": _clean_title(title),
        "html": body,
        "source": desc.get("file"),
        "group": _group(desc),
        "appendix": desc.get("appendix_id"),
        "header": _clean_title(_header(desc, appendices or {})),
        "bookmark_level": _bookmark_level(desc),
        "headings": _headings(body),
        "figures": list(figures or []),
        "tables": list(tables or []),
        "endnotes": list(endnotes or []),
        "images": images,
        "chars": chars,
    }


def _build_page(desc: dict, *, manifest: dict, site_dir: Path, stems: set[str],
                quiz_data: quiz.QuizData, animations: list[dict],
                references: list[dict], parts: dict[str, dict],
                appendices: dict[str, dict], final: bool,
                warnings: list[str],
                appendix_tables: dict[str, int] | None = None) -> dict:
    kind = desc["kind"]
    appendix_tables = appendix_tables if appendix_tables is not None else {}
    if kind == "half_title":
        return _page(desc, frontmatter.half_title(manifest), desc["title"],
                     appendices=appendices)
    if kind == "title_page":
        return _page(desc, frontmatter.title_page(manifest), desc["title"],
                     appendices=appendices)
    if kind == "copyright":
        return _page(desc, frontmatter.copyright_page(manifest), desc["title"],
                     appendices=appendices)
    if kind == "front":
        page = content.load_page(site_dir, desc["file"], stems, manifest)
        return _page(desc, _light_body(page), desc["title"],
                     images=page.images, appendices=appendices)
    if kind == "toc":
        return _page(desc, "", "目录", appendices=appendices)
    if kind == "list_of_figures":
        return _page(desc, "", "插图目录", appendices=appendices)
    if kind == "list_of_tables":
        return _page(desc, "", "表格目录", appendices=appendices)
    if kind == "part":
        part = parts.get(desc.get("part_id") or "")
        if part is None:
            raise BookError(f"缺少篇数据: {desc.get('part_id')}")
        art_name = part.get("opener_art")
        if not art_name:
            warnings.append(f"第 {part['id']} 篇缺少 opener_art")
        return _page(
            desc, frontmatter.part_opener(part, illustrations.part_art(art_name)),
            desc["title"], appendices=appendices)
    if kind == "chapter":
        page = content.load_page(site_dir, desc["file"], stems, manifest)
        body, figures, tables, notes = _chapter_body(
            page, desc, quiz_data, final, warnings)
        return _page(desc, body, page.title, images=page.images,
                     figures=figures, tables=tables, endnotes=notes,
                     chars=_char_count(body), appendices=appendices)
    if kind == "appendix_opener":
        appendix = appendices.get(desc.get("appendix_id") or "")
        if appendix is None:
            raise BookError(f"缺少附录数据: {desc.get('appendix_id')}")
        return _page(desc, frontmatter.appendix_opener(appendix), desc["title"],
                     appendices=appendices)
    if kind == "appendix":
        if desc["stem"] == "appendix-A-index":
            return _page(
                desc, _animation_table(animations), "附录 A 动画总表",
                tables=[{"number": "表 A-1",
                         "caption": "表 A-1　动画与图示总表",
                         "anchor": "appendix-a-table-wrap",
                         "stem": desc["stem"]}],
                appendices=appendices)
        if desc["stem"] == "appendix-F-answers":
            appendix = appendices.get("F", {})
            return _page(desc, quiz.render_answers(
                quiz_data, CHAPTER_STEMS, desc["stem"]),
                appendix.get("title") or "习题答案与综合自测",
                appendices=appendices)
        page = content.load_page(site_dir, desc["file"], stems, manifest)
        appendix_id = desc.get("appendix_id") or ""
        body, figures, tables, notes, next_table = _appendix_body(
            page, desc, final, warnings,
            table_start=appendix_tables.get(appendix_id, 0))
        appendix_tables[appendix_id] = next_table
        return _page(desc, body, page.title, images=page.images,
                     figures=figures, tables=tables, endnotes=notes,
                     appendices=appendices)
    if kind == "bibliography":
        return _page(desc, frontmatter.render_bibliography(references),
                     "参考文献", appendices=appendices)
    if kind == "index":
        return _page(desc, "", "索引", appendices=appendices)
    if kind == "back":
        page = content.load_page(site_dir, desc["file"], stems, manifest)
        return _page(desc, _light_body(page), desc["title"],
                     images=page.images, appendices=appendices)
    if kind == "colophon":
        return _page(desc, frontmatter.colophon(
            manifest, {"pages": EXPECTED_PAGES}),
            desc["title"], appendices=appendices)
    raise BookError(f"未知页面类型: {kind}")


def _caption_title(caption: str, number: str) -> str:
    text = caption.strip()
    if text.startswith(number):
        text = text[len(number):]
    text = text.strip("　 ").strip()
    head = text.split("：", 1)[0].strip()
    if 3 <= len(head) <= 24:
        return head
    sentence = re.split(r"[。！？]", text, maxsplit=1)[0].strip()
    if len(sentence) <= 28:
        return sentence
    clauses: list[str] = []
    for clause in sentence.split("，"):
        candidate = "，".join([*clauses, clause])
        if clauses and len(candidate) > 26:
            break
        clauses.append(clause)
    return "，".join(clauses).strip("，。：； ")


def _toc_entries(pages: list[dict]) -> list[dict]:
    entries: list[dict] = []

    def sections(page: dict) -> None:
        for heading in page["headings"]:
            if heading["level"] == 2 and heading["numbered"]:
                entries.append({"level": 3, "title": heading["text"],
                                "anchor": heading["anchor"],
                                "kind": "section", "bookmark": 3})

    for page in pages:
        if page["kind"] == "part":
            entries.append({"level": 1, "title": page["title"],
                            "anchor": page["id"], "kind": "part",
                            "bookmark": 1})
        elif page["kind"] == "chapter":
            entries.append({"level": 2, "title": page["title"],
                            "anchor": page["id"], "kind": "chapter",
                            "bookmark": 2})
            sections(page)
        elif page["kind"] == "appendix_opener":
            entries.append({"level": 1, "title": page["title"],
                            "anchor": page["id"], "kind": "appendix",
                            "bookmark": 1})
        elif page["kind"] == "appendix":
            entries.append({"level": 2, "title": page["title"],
                            "anchor": page["id"], "kind": "appendix",
                            "bookmark": 2})
            sections(page)
    return entries


def _list_entries(pages: list[dict], name: str) -> list[dict]:
    entries = []
    for page in pages:
        for item in page[name]:
            entries.append({
                "number": item["number"],
                "title": _caption_title(item["caption"], item["number"]),
                "caption": item["caption"],
                "anchor": item["anchor"],
                "source": item["stem"],
            })
    return entries


def _project_export(entry: dict) -> dict:
    match = re.search(r"([0-9]+|[A-H])-\d+", entry["number"])
    return {
        "id": entry["anchor"],
        "chapter": match.group(1) if match else "",
        "number": entry["number"],
        "title": entry["title"],
        "anchor": entry["anchor"],
        "source": entry["source"],
    }


def _load_list(path: Path) -> list[dict]:
    if not path.is_file():
        raise BookError(f"缺少数据文件: {path}")
    return data.load_list(path)


def _fill_generated_pages(pages: list[dict], toc: list[dict],
                          lof: list[dict], lot: list[dict]) -> None:
    for page in pages:
        if page["kind"] == "toc":
            page["html"] = transforms.strip_emoji(frontmatter.render_toc(toc))
            page["headings"] = _headings(page["html"])
        elif page["kind"] == "list_of_figures":
            page["html"] = transforms.strip_emoji(
                frontmatter.render_list("插图目录", "list-of-figures", lof, "图"))
            page["headings"] = _headings(page["html"])
        elif page["kind"] == "list_of_tables":
            page["html"] = transforms.strip_emoji(
                frontmatter.render_list("表格目录", "list-of-tables", lot, "表"))
            page["headings"] = _headings(page["html"])


def _fill_index(pages: list[dict], terms: list[dict], final: bool) -> None:
    anchors = set()
    for page in pages:
        anchors.add(page["id"])
        anchors.update(match.group(2)
                       for match in ID_ATTR_RE.finditer(page["html"]))
    # 前置页在正文起始页之前，pdf.py 的 _region_links 会丢弃这类链接，
    # 索引页码停在 000，PDF 构建才报错；在装配阶段提前拦下。
    front = {page["stem"] for page in pages if page["group"] == "front"}
    front_ids = {page["id"] for page in pages if page["group"] == "front"}
    for item in terms:
        for anchor in [item["primary"], *item["anchors"]]:
            if (anchor in front_ids
                    or anchor.split("--", 1)[0] in front):
                raise BookError(
                    f"索引锚点落在前置页，PDF 页码无法回填: "
                    f"{item['term']} -> {anchor}")
    data.validate_index_terms(terms, anchors, final=final)
    rendered = transforms.strip_emoji(
        frontmatter.render_index(data.index_sections(terms)))
    for page in pages:
        if page["id"] == "book-index":
            page["html"] = rendered
            page["headings"] = _headings(rendered)
            return
    raise BookError("页面序列中缺少索引页")


# ---------------------------------------------------------------------------
# 文档外壳与导航
# ---------------------------------------------------------------------------

def _page_link(page: dict, direction: str) -> str:
    if direction == "prev":
        label = "← 上一篇"
    else:
        label = "下一篇 →"
    return (
        f'<a class="book-page-nav-{direction}" href="#{page["id"]}" rel="{direction}">'
        f'<span class="book-page-nav-label">{label}</span>'
        f'<span class="book-page-nav-title">{_esc(page["title"])}</span></a>')


def _page_nav(prev_page: dict | None, next_page: dict | None) -> str:
    nav = ['<nav class="book-page-nav" aria-label="翻页">']
    nav.append(_page_link(prev_page, "prev") if prev_page
               else '<span class="book-page-nav-empty" aria-hidden="true"></span>')
    nav.append('<a class="book-page-nav-toc" href="#book-toc">全书目录</a>')
    nav.append(_page_link(next_page, "next") if next_page
               else '<span class="book-page-nav-empty" aria-hidden="true"></span>')
    nav.append("</nav>")
    return "".join(nav)


def _page_section(page: dict, prev_page: dict | None,
                  next_page: dict | None) -> str:
    body = _strip_page_id(page["html"], page["id"])
    return (
        f'<section class="book-page page-{page["kind"]}" id="{page["id"]}" '
        f'data-page="{_esc(page["stem"])}" data-title="{_esc(page["title"])}" '
        f'data-kind="{page["kind"]}" data-header="{_esc(page["header"])}">\n'
        f'<div class="md-typeset">\n{body}\n</div>\n'
        f'{_page_nav(prev_page, next_page)}\n</section>')


def _document(manifest: dict, pages: list[dict], site_dir: Path,
              fonts_dir: Path) -> str:
    font_css, screen_css, print_css = inline_css(site_dir, fonts_dir)
    scripts = inline_scripts(site_dir)
    search = inline_static("book-search.js")
    ui = inline_static("book-ui.js")
    mathjax = inline_mathjax()
    sections = []
    shared_front = content._shared_front_html()
    if shared_front:
        sections.append(shared_front)
    for index, page in enumerate(pages):
        prev_page = pages[index - 1] if index > 0 else None
        next_page = pages[index + 1] if index + 1 < len(pages) else None
        sections.append(_page_section(page, prev_page, next_page))
    return f"""<!doctype html>
<html lang="{_esc(manifest["language"])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>{_esc(manifest["title"])}</title>
<meta name="book-manifest-sha256" content="{_manifest_digest(manifest)}">
<meta name="book-version" content="{_esc(manifest["version"])}">
<meta name="book-date" content="{_esc(manifest["date"])}">
<meta name="book-author" content="{_esc(manifest["author"])}">
<style>
{font_css}
</style>
<style>
{screen_css}
</style>
<style media="print">
{print_css}
</style>
</head>
<body data-md-color-scheme="default" data-md-color-primary="indigo" data-md-color-accent="indigo">
<a class="book-skip" href="#book-toc">跳到目录</a>
<div class="book-progress" id="book-progress" aria-hidden="true"></div>
<header class="book-header"><span class="book-header-title">{_esc(manifest["title"])}</span>
<div class="book-search" id="book-search" role="search">
<label class="visually-hidden" for="book-search-input">搜索全书</label>
<input id="book-search-input" type="search" placeholder="搜索全书（Ctrl+K）" autocomplete="off" spellcheck="false" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="book-search-results">
<div class="book-search-panel" id="book-search-panel" hidden>
<p class="book-search-status" id="book-search-status" role="status" aria-live="polite"></p>
<ul class="book-search-results" id="book-search-results" role="listbox"></ul>
</div>
</div>
<a class="book-header-toc" href="#book-toc">目录</a></header>
<main class="book">
{''.join(sections)}
</main>
<footer class="book-footer">离线整书 · 由 docs/ 构建 · {_esc(manifest["license"])}</footer>
<button class="book-top" id="book-top" type="button" aria-label="回到顶部" hidden>↑</button>
{mathjax}
<script>{scripts}</script>
<script>{search}</script>
<script>{ui}</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# 审计
# ---------------------------------------------------------------------------

def _markup(document: str) -> str:
    return EMBEDDED_BLOCK_RE.sub("", document)


def _one_h1_problem(page: dict) -> bool:
    count = len(H1_RE.findall(page["html"]))
    if page["source"] and page["group"] == "appendix":
        # 附录源页 h1 已降为 h2，附录级 h1 由 opener 提供。
        return count != 0
    return count != 1


def audit_html(document: str, model: dict, final: bool = False) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    def issue(message: str) -> None:
        (errors if final else warnings).append(message)

    markup = _markup(document)
    ids = [match.group(2) for match in ID_ATTR_RE.finditer(markup)]
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        errors.append("重复 ID: " + ", ".join(duplicates[:10]))
    hrefs = re.findall(r'href="#([^"]+)"', markup)
    missing = sorted({href for href in hrefs if href not in set(ids)})
    if missing:
        errors.append("悬空锚点: " + ", ".join(missing[:10]))
    if SCRIPT_SRC_RE.search(document):
        errors.append("含外部脚本")
    if 'rel="stylesheet"' in markup:
        errors.append("含外部样式")
    if "<iframe" in markup or "<video" in markup:
        errors.append("含 iframe/video")
    remote = re.findall(r'<img[^>]+src="https?://[^"]+"', markup)
    if remote:
        errors.append("含远程图片: " + remote[0][:80])
    if "<details" in markup:
        errors.append("书内仍有 <details>")
    probe = markup.replace("✓", "").replace("✗", "")
    emoji = transforms.EMOJI_RE.search(probe)
    if emoji:
        errors.append("书内仍有 emoji: " + emoji.group(0))
    # 仅剥离内联图片/字体的 base64 data URI 载荷；可见文本照常检查占位标记。
    placeholder = PLACEHOLDER_RE.search(DATA_URI_RE.sub("", markup))
    if placeholder:
        errors.append("书内仍有占位标记: " + placeholder.group(0))

    pages = model.get("pages") or []
    expected_pages = int(model.get("expected_pages") or EXPECTED_PAGES)
    if len(pages) != expected_pages:
        errors.append(f"逻辑页应为 {expected_pages}，实际 {len(pages)}")
    sections = len(re.findall(r'<section class="book-page\b', markup))
    if sections != len(pages):
        errors.append(f"book-page 数量 {sections} 与逻辑页 {len(pages)} 不一致")
    for page in pages:
        if _one_h1_problem(page):
            errors.append(f"{page['id']}: h1 数量不符合单页要求")

    for page in pages:
        if (page["kind"] in {"toc", "list_of_figures", "list_of_tables"}
                or page["id"] == "book-index"):
            # 分卷可能出现某卷无图/无表的空目录页；只有真有条目时才要求占位。
            if 'href="#' not in page["html"]:
                continue
            if "000" not in page["html"]:
                errors.append(f"{page['id']}: 缺少 000 页码占位")
    index_page = next((page for page in pages if page["id"] == "book-index"), None)
    if index_page is None:
        errors.append("缺少索引页")
    else:
        missing_index = sorted({
            href for href in re.findall(r'href="#([^"]+)"', index_page["html"])
            if href not in set(ids)})
        if missing_index:
            errors.append("索引悬空锚点: " + ", ".join(missing_index[:10]))

    stats = model.get("stats") or {}
    chapters = stats.get("chapters") or {}
    for chapter in sorted(chapters, key=lambda value: int(value)):
        chars = int(chapters[chapter].get("chars", 0))
        if chars < WORD_TARGET:
            issue(f"第 {chapter} 章字数不足：{chars} < {WORD_TARGET} 非空白字符")
    if not model.get("volume"):
        index_count = int(stats.get("index_terms", 0))
        if not INDEX_TARGET[0] <= index_count <= INDEX_TARGET[1]:
            issue(f"索引应为 {INDEX_TARGET[0]}–{INDEX_TARGET[1]} 条，当前 {index_count}")
        references = int(stats.get("references", 0))
        if references < REFERENCE_TARGET:
            issue(f"参考文献应 ≥{REFERENCE_TARGET} 条，当前 {references}")
    unsigned = int(stats.get("unsigned_reviews", 0))
    if unsigned:
        issue(f"{unsigned} 章缺少技术/编辑/安全审读签字")
    for message in model.get("build_warnings") or []:
        issue(str(message))

    size = len(document.encode("utf-8"))
    if size > config.MAX_HTML_BYTES:
        errors.append(f"HTML 超过硬上限 {config.MAX_HTML_BYTES} 字节")
    elif size > config.HTML_TARGET_BYTES:
        warnings.append(f"HTML 超过目标体积 {config.HTML_TARGET_BYTES} 字节")

    return {
        "errors": errors,
        "warnings": warnings,
        "pages": len(pages),
        "bytes": size,
        "images": markup.count("<img "),
        "formulas": markup.count('class="arithmatex"'),
    }


# ---------------------------------------------------------------------------
# 构建与检查入口
# ---------------------------------------------------------------------------

def build_html(out_dir: Path, site_dir: Path, data_dir: Path, docs_dir: Path,
               manifest: dict, fonts_dir: Path = config.FONTS_DIR,
               rebuild_site: bool = False, final: bool | None = None,
               volume: int | None = None) -> Path:
    site_dir = Path(site_dir)
    data_dir = Path(data_dir)
    docs_dir = Path(docs_dir)
    out_dir = Path(out_dir)
    final = _resolve_final(manifest, final)
    if rebuild_site:
        _build_site(site_dir)
    validate_manifest(manifest, docs_dir=docs_dir)

    descriptors = book_pages(manifest)
    if len(descriptors) != EXPECTED_PAGES:
        raise BookError(
            f"清单应给出 {EXPECTED_PAGES} 个逻辑页，实际 {len(descriptors)}")
    stems = {desc["stem"] for desc in descriptors if not desc.get("generated")}
    warnings: list[str] = []
    parts = {part["id"]: part for part in manifest.get("parts") or []}
    appendices = {appendix["id"]: appendix
                  for appendix in manifest.get("appendices") or []}

    quiz_file = (appendices["F"].get("files") or ["p9-00-quiz.md"])[0]
    quiz_page = content.load_page(site_dir, quiz_file, stems, manifest)
    quiz_data = quiz.parse_quiz(quiz_page.html)
    unknown = sorted(set(quiz_data.chapters) - set(CHAPTER_STEMS))
    if unknown:
        raise BookError(f"题库出现未知章号: {unknown}")

    animations = _load_list(data_dir / "animations.yml")
    data.validate_animations(animations, static_root=site_dir)
    index_terms = _load_list(data_dir / "index-terms.yml")
    references = _load_list(data_dir / "references.yml")
    sources = _load_list(data_dir / "sources.yml")
    signoffs = _load_list(data_dir / "chapter-signoff.yml")
    data.validate_references(references, final=final)
    data.validate_signoffs(signoffs, final=final)

    pages: list[dict] = []
    used_sources: set[str] = set()
    chapter_stats: dict[str, dict] = {}
    appendix_tables: dict[str, int] = {}
    for desc in descriptors:
        page = _build_page(
            desc, manifest=manifest, site_dir=site_dir, stems=stems,
            quiz_data=quiz_data, animations=animations, references=references,
            parts=parts, appendices=appendices, final=final, warnings=warnings,
            appendix_tables=appendix_tables)
        used_sources |= data.used_source_ids(page["html"])
        if page["kind"] == "chapter":
            match = CHAPTER_NUMBER_RE.search(desc["stem"])
            if match is None:
                raise BookError(f"章节文件名缺章号: {desc['stem']}")
            chapter_stats[str(int(match.group(1)))] = {"chars": page["chars"]}
        pages.append(page)
    for index, page in enumerate(pages):
        page["index"] = index

    all_pages = list(pages)
    total_index_terms = len(index_terms)
    cross_volume_links = 0
    if volume is not None:
        pages = _select_volume_pages(all_pages, volume)
        _retarget_volume_appendices(pages, volume, animations, quiz_data)
        chapter_stats = {}
        for index, page in enumerate(pages):
            page["index"] = index
            if page["kind"] == "chapter":
                match = CHAPTER_NUMBER_RE.search(page["stem"])
                if match:
                    chapter_stats[str(int(match.group(1)))] = {"chars": page["chars"]}
        index_terms = _filter_index_terms(index_terms, pages)
    elif len(pages) != EXPECTED_PAGES:
        raise BookError(f"装配得到 {len(pages)} 页，应为 {EXPECTED_PAGES}")

    toc = _toc_entries(pages)
    lof = _list_entries(pages, "figures")
    lot = _list_entries(pages, "tables")
    _fill_generated_pages(pages, toc, lof, lot)
    _fill_index(pages, index_terms, final)
    if volume is not None:
        cross_volume_links = _externalize_cross_volume_links(
            pages, all_pages, volume)

    data.validate_sources(sources, used_sources, final=final)
    unsigned = sum(
        1 for item in signoffs
        if item.get("open_issues")
        or not all(str(item.get(key, "")).strip() for key in
                   ("technical_reviewer", "editorial_reviewer", "safety_reviewer")))

    document = _document(manifest, pages, site_dir, fonts_dir)
    markup = _markup(document)
    stats = {
        "logical_pages": len(pages),
        "figures": len(lof),
        "tables": len(lot),
        "images": sum(page["images"] for page in pages),
        "formulas": markup.count('class="arithmatex"'),
        "endnotes": sum(len(page["endnotes"]) for page in pages),
        "chapters": chapter_stats,
        "index_terms": len(index_terms),
        "index_terms_total": total_index_terms,
        "references": len(references),
        "unsigned_reviews": unsigned,
        "cross_volume_links": cross_volume_links,
    }
    headings = [
        {"page": page["id"], **heading}
        for page in pages for heading in page["headings"]]
    model = {
        "schema": 1,
        "manifest_schema": manifest.get("schema"),
        "manifest_sha256": _manifest_digest(manifest),
        "edition_status": (manifest.get("release") or {}).get("edition_status"),
        "title": manifest["title"],
        "version": manifest["version"],
        "date": manifest["date"],
        "volume": volume,
        "volume_label": VOLUME_LABELS.get(volume) if volume is not None else None,
        "expected_pages": len(pages),
        "pages": pages,
        "toc": toc,
        "lof": lof,
        "lot": lot,
        "endnotes": stats["endnotes"],
        "figures": stats["figures"],
        "tables": stats["tables"],
        "headings": headings,
        "stats": stats,
        "build_warnings": warnings,
        "audit": {},
    }
    report = audit_html(document, model, final=final)
    if report["errors"]:
        raise BookError("整书审计失败:\n" + "\n".join(report["errors"]))
    stats["images"] = report["images"]
    stats["formulas"] = report["formulas"]
    model["audit"] = report

    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / config.OUTPUT_NAME
    output.write_text(document, encoding="utf-8", newline="\n")
    (out_dir / config.MODEL_NAME).write_text(
        json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, entries in (("figures.yml", lof), ("tables.yml", lot)):
        exported = [_project_export(entry) for entry in entries]
        (out_dir / name).write_text(
            yaml.safe_dump(exported, allow_unicode=True, sort_keys=False),
            encoding="utf-8")
    print(f"html  {output} ({report['bytes']} bytes, {report['pages']} pages, "
          f"{report['images']} images, {report['formulas']} formulas, "
          f"{len(report['warnings'])} warnings)")
    return output


def check_html(out_dir: Path, manifest: dict, final: bool | None = None) -> int:
    out_dir = Path(out_dir)
    html_path = out_dir / config.OUTPUT_NAME
    model_path = out_dir / config.MODEL_NAME
    if not html_path.is_file():
        raise BookError(f"整书产物不存在: {html_path}")
    if not model_path.is_file():
        raise BookError(f"整书模型不存在: {model_path}")
    final = _resolve_final(manifest, final)
    document = html_path.read_text(encoding="utf-8")
    model = json.loads(model_path.read_text(encoding="utf-8"))
    report = audit_html(document, model, final=final)
    for warning in report["warnings"]:
        print(f"warning: {warning}")
    if report["errors"]:
        for error in report["errors"]:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"check {html_path} OK ({report['pages']} pages, "
          f"{report['bytes']} bytes, {len(report['warnings'])} warnings)")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=config.DIST_DIR)
    parser.add_argument("--site-dir", type=Path, default=config.SITE_DIR)
    parser.add_argument("--data-dir", type=Path, default=config.DATA_DIR)
    parser.add_argument("--docs-dir", type=Path, default=config.DOCS)
    parser.add_argument("--manifest", type=Path, default=config.MANIFEST_PATH)
    parser.add_argument("--no-build", action="store_true", help="复用已有站点产物")
    parser.add_argument("--check", action="store_true", help="只审计已有整书")
    parser.add_argument("--final", action="store_true",
                        help="按终稿门槛审计（草稿警告升级为错误）")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        final = True if args.final else None
        if args.check:
            return check_html(args.out_dir, manifest, final=final)
        build_html(args.out_dir, args.site_dir, args.data_dir, args.docs_dir,
                   manifest, rebuild_site=not args.no_build, final=final)
        return 0
    except BookError as exc:
        print(f"book build error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
