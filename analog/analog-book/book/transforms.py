"""书内语义转换：去 emoji、展开折叠块、提示框、图表编号、尾注与计算器兜底。"""
from __future__ import annotations

import html
import re

from .content import plain_text, wrap_tables
from .manifest import BookError

EMOJI_MAP = (("✅", "✓"), ("❌", "✗"), ("⚠️", "注意"), ("⚠", "注意"),
             ("\u2318", "Cmd"))
# 源文里的 ✓/✗ 是有意义的判定符（EMOJI_RE 的区间也覆盖它们），保留原样。
KEEP_SYMBOLS = ("✓", "✗")
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2300-\u23FF\u2600-\u27BF\u2B00-\u2BFF"
    "\uFE0F\u200D]+")
CALLOUT_LABELS = {
    "goal": "学习目标", "prereq": "先修", "calc": "公式速查",
    "limit": "模型边界", "gem": "精髓", "warn": "注意",
    "fix": "修复方法", "idea": "设计直觉", "video": "配套视频",
    "demo": "动画演示", "photo": "实测记录", "attach": "附件",
    "pin": "记忆锚点", "link": "延伸阅读", "scene": "场景",
    "level": "难度", "lead": "白话导读",
    "why": "为什么",
}
CALLOUT_RE = re.compile(
    r'<div class="callout callout-([a-z]+)">(.*?)</div>', re.S)
LEADING_TITLE_RE = re.compile(
    r"<p>\s*<strong>([^<]{1,20})</strong>\s*[：:]\s*", re.S)
FIGURE_RE = re.compile(r"<figure(?P<attrs>[^>]*)>(?P<body>.*?)</figure>", re.S)
FIGCAPTION_RE = re.compile(r"<figcaption[^>]*>(?P<cap>.*?)</figcaption>", re.S)
TABLE_CAPTION_RE = re.compile(
    r"<p[^>]*>\s*<strong>\s*(表\s*[0-9A-H]+-\d+[^<]*)</strong>\s*</p>\s*"
    r"<div class=\"table-wrap\">(?P<table><table.*?</table>)</div>", re.S)
TABLE_NUMBER_PREFIX_RE = re.compile(r"^表\s*[0-9A-H]+-\d+")
NUMBERED_TABLE_RE = re.compile(
    r'<div class="table-wrap" id="[^"]+">\s*<p class="table-caption">.*?</p>\s*'
    r'<table(?:\s[^>]*)?>.*?</table>\s*</div>', re.S)
LINK_RE = re.compile(
    r'<a\s+(?P<pre>[^>]*?)href="(?P<href>[^"]+)"(?P<post>[^>]*)>(?P<text>.*?)</a>',
    re.S)
CALC_RE = re.compile(r'<div class="calc" data-calc="([^"]+)"></div>')
CHAPTER_RE = re.compile(r"-ch(\d+)$")
FALLBACK_RE = re.compile(r'class="calc-print"|例\s*\d+-\d+|算一笔|再算一笔')
DETAILS_RE = re.compile(
    r"<details(?:\s[^>]*)?>\s*<summary>(?P<title>.*?)</summary>"
    r"(?P<body>.*?)</details>", re.S)


def strip_emoji(fragment: str) -> str:
    placeholders = {}
    for index, symbol in enumerate(KEEP_SYMBOLS):
        token = f"\ue100{index}\ue101"
        if symbol in fragment:
            placeholders[token] = symbol
            fragment = fragment.replace(symbol, token)
    for index, (emoji, replacement) in enumerate(EMOJI_MAP):
        token = f"\ue000{index}\ue001"
        if emoji in fragment:
            placeholders[token] = replacement
            fragment = fragment.replace(emoji, token)
    fragment = EMOJI_RE.sub("", fragment)
    for token, replacement in placeholders.items():
        fragment = fragment.replace(token, replacement)
    return fragment


def unwrap_details(fragment: str) -> str:
    def repl(match: re.Match) -> str:
        title = match.group("title").strip()
        body = match.group("body").strip()
        return ('<div class="book-reveal">'
                f'<p class="book-reveal-title">{title}</p>{body}</div>')

    return DETAILS_RE.sub(repl, fragment)


def transform_callouts(fragment: str) -> str:
    def repl(match: re.Match) -> str:
        slug, body = match.group(1), match.group(2)
        label = CALLOUT_LABELS.get(slug)
        if label is None:
            return f'<blockquote class="book-quote">{body}</blockquote>'
        body = LEADING_TITLE_RE.sub("<p>", body, count=1)
        if label == "注意":
            # ⚠️ 已被 strip_emoji 翻成“注意”，卡片标签又写一遍会重复。
            body = re.sub(r"^(\s*)<p>\s*注意\s*", r"\1<p>", body, count=1)
        return (f'<aside class="book-callout book-callout-{slug}" '
                f'data-label="{label}" role="note">'
                f'<p class="callout-label">{label}</p>{body}</aside>')

    return CALLOUT_RE.sub(repl, fragment)


def chapter_label(stem: str, appendix_id: str | None = None) -> str | None:
    if appendix_id:
        return appendix_id
    match = CHAPTER_RE.search(stem)
    return str(int(match.group(1))) if match else None


def number_figures(fragment: str, label: str, stem: str,
                   final: bool = False) -> tuple[str, list[dict], list[str]]:
    counter = 0
    entries, warnings = [], []

    def repl(match: re.Match) -> str:
        nonlocal counter
        body = match.group("body")
        caption_match = FIGCAPTION_RE.search(body)
        if caption_match is None:
            warnings.append(f"{stem}: 图片缺少 <figcaption> 图注，未编号")
            return match.group(0)
        caption = plain_text(caption_match.group("cap"))
        if not caption:
            warnings.append(f"{stem}: 图注为空")
            return match.group(0)
        counter += 1
        number = f"图 {label}-{counter}"
        if not caption.startswith(number):
            caption = f"{number}　{caption}"
            body = (body[:caption_match.start("cap")]
                    + f"{number}　" + caption_match.group("cap")
                    + body[caption_match.end("cap"):])
        anchor = re.search(r'(?<![\w-])id="([^"]+)"', match.group("attrs"))
        anchor_id = anchor.group(1) if anchor else f"{stem}--fig-{counter}"
        attrs = match.group("attrs")
        if anchor is None:
            attrs += f' id="{anchor_id}"'
        entries.append({"number": number, "caption": caption,
                        "anchor": anchor_id, "stem": stem})
        return f'<figure{attrs}>{body}</figure>'

    result = FIGURE_RE.sub(repl, fragment)
    if final and warnings:
        raise BookError("图注校验失败:\n" + "\n".join(warnings))
    return result, entries, warnings


def number_tables(fragment: str, label: str, stem: str,
                  final: bool = False, start: int = 0
                  ) -> tuple[str, list[dict], list[str]]:
    """给表格加「表 X-Y」编号表注。

    ``start`` 是编号起点：附录族按「整族连续」编号（表 C-1…C-14），由
    assemble 逐页累加；章内仍从 1 起。正文表注里的号必须与这里算出的号
    一致，否则会被补成「表 C-4　表 C-1　…」这样的双号。
    """
    stash = []

    def stash_repl(match: re.Match) -> str:
        stash.append(match.group(0))
        return f"\ue200{len(stash) - 1}\ue201"

    fragment = NUMBERED_TABLE_RE.sub(stash_repl, fragment)
    fragment = wrap_tables(fragment)
    counter = start
    entries, warnings = [], []

    def repl(match: re.Match) -> str:
        nonlocal counter
        counter += 1
        raw = plain_text(match.group(1))
        number = f"表 {label}-{counter}"
        stale = TABLE_NUMBER_PREFIX_RE.match(raw)
        if raw.startswith(number):
            caption = raw
        elif stale:
            warnings.append(
                f"{stem}: 表注编号「{stale.group(0)}」与计算号「{number}」不符"
                "（表号按全文顺序计算，前面插表后需顺移后续表号）")
            caption = f"{number}　{raw[stale.end():].lstrip(' 　')}"
        else:
            caption = f"{number}　{raw}"
        anchor = f"{stem}--table-{counter}"
        entries.append({"number": number, "caption": caption,
                        "anchor": anchor, "stem": stem})
        return (f'<div class="table-wrap" id="{anchor}">'
                f'<p class="table-caption">{html.escape(caption)}</p>'
                f'{match.group("table")}</div>')

    result = TABLE_CAPTION_RE.sub(repl, fragment)
    remaining = len(re.findall(r'<div class="table-wrap">', result))
    if remaining:
        warnings.append(f"{stem}: {remaining} 个表格缺少“表 X-Y”表注，未编号")
    for index, block in enumerate(stash):
        result = result.replace(f"\ue200{index}\ue201", block)
    if final and warnings:
        raise BookError("表注校验失败:\n" + "\n".join(warnings))
    return result, entries, warnings


def transform_endnotes(fragment: str, stem: str) -> tuple[str, list[dict]]:
    notes, seen, refs = [], {}, {}

    def repl(match: re.Match) -> str:
        href = match.group("href")
        if href.startswith("#"):
            return match.group(0)
        number = seen.get(href)
        if number is None:
            number = len(notes) + 1
            seen[href] = number
            notes.append({"number": number, "id": f"{stem}--note-{number}",
                          "href": href, "text": plain_text(match.group("text"))})
        refs[number] = refs.get(number, 0) + 1
        suffix = "" if refs[number] == 1 else f"-{refs[number]}"
        anchor = f"{stem}--note-{number}"
        return (f'{match.group("text")}<sup class="endnote-ref">'
                f'<a href="#{anchor}" id="{stem}--note-ref-{number}{suffix}">'
                f'{number}</a></sup>')

    result = LINK_RE.sub(repl, fragment)
    if not notes:
        return result, []
    items = "".join(
        f'<li id="{note["id"]}"><span class="endnote-text">'
        f'{html.escape(note["text"])}</span> '
        f'<span class="endnote-url">{html.escape(note["href"])}</span></li>'
        for note in notes)
    section = (
        f'<section class="chapter-endnotes" id="{stem}--notes">'
        f'<h2 class="endnotes-title">注释与链接</h2>'
        f'<ol class="endnote-list">{items}</ol></section>')
    return result + section, notes


def check_calculator_fallbacks(fragment: str, stem: str,
                               final: bool = False) -> list[str]:
    warnings = []
    for match in CALC_RE.finditer(fragment):
        window = fragment[max(0, match.start() - 1600):match.end() + 1600]
        if not FALLBACK_RE.search(window):
            warnings.append(f"{stem}: 计算器 {match.group(1)} 附近没有印刷替代"
                            "（例 N-x / 算一笔 / .calc-print）")
    if final and warnings:
        raise BookError("计算器兜底校验失败:\n" + "\n".join(warnings))
    return warnings
