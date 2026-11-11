"""书内生成页：半书名、书名、版权、目录、图表目录、索引与后置。"""
from __future__ import annotations

import html
import re

UNIT_CHAPTER_RE = re.compile(r"-ch(\d+)\.md$")


def _e(value) -> str:
    return html.escape(str(value), quote=True)


def _draft_note(manifest: dict) -> str:
    if manifest["release"]["edition_status"] != "draft":
        return ""
    return ('<p class="draft-note">本版为构建草稿，尚未完成技术、编辑与安全审读，'
            '不得作为稳定版发行。</p>')


def half_title(manifest: dict) -> str:
    return (
        '<div class="half-title">'
        f'<h1 class="book-title">{_e(manifest["title"])}</h1>'
        f'<p class="book-subtitle">{_e(manifest["subtitle"])}</p>'
        f'<p class="book-edition">{_e(manifest["edition"])}</p>'
        '</div>')


def title_page(manifest: dict) -> str:
    return (
        '<div class="title-page">'
        f'<p class="title-kicker">模拟电路 · 从直觉到工程</p>'
        f'<h1 id="title-page">{_e(manifest["title"])}</h1>'
        f'<p class="title-subtitle">{_e(manifest["subtitle"])}</p>'
        f'<p class="title-author">{_e(manifest["author"])}</p>'
        f'<p class="title-edition">{_e(manifest["edition"])} · '
        f'{_e(manifest["version"])}</p>'
        f'<p class="title-date">{_e(manifest["date"])}</p>'
        '</div>')


def copyright_page(manifest: dict) -> str:
    return (
        '<div class="copyright-page">'
        '<h1 id="copyright">版权、授权与安全</h1>'
        f'<p>《{_e(manifest["title"])}》<br>'
        f'{_e(manifest["subtitle"])}</p>'
        f'<p>{_e(manifest["edition"])} · 版本 {_e(manifest["version"])} · '
        f'{_e(manifest["date"])}</p>'
        f'<p>作者：{_e(manifest["author"])}</p>'
        f'<p>正文、SVG 动画、网表与实验数据采用 {_e(manifest["license"])} 授权；'
        '转载、改编与再分发请保留署名并以相同方式共享。第三方照片、软件与字体的'
        '完整清单见书末「来源与许可」。</p>'
        '<p>正文字体为 Noto Serif SC 与 Noto Sans SC，代码字体为 JetBrains Mono，'
        '均按 SIL Open Font License 1.1 嵌入。</p>'
        f'<p>在线阅读：{_e(manifest["site_url"])}<br>'
        f'勘误与讨论：{_e(manifest["repository"])}/issues</p>'
        '<p><strong>安全声明</strong>：本书是学习读物，不是器件、电源或高压设备的'
        '操作许可。动手前必须断电、放电、限流并确认绝缘与接地；电解电容、电感与'
        '电池可能储存危险能量。器件参数、热设计与安全间距请以厂商最新数据手册、'
        '当地法规和实际测量为准。作者与贡献者不对因照书操作造成的损失承担责任。</p>'
        '<p><strong>关于数据</strong>：仿真是模型结果，不是实测；实测只覆盖书中'
        '明确标出的三套实验。读者设计必须用数据手册、仿真与实际测量三方复核。</p>'
        '<p>印刷规格：16K（185×260mm），正文 80g 纯质纸，封面 250g 铜版纸覆哑膜，'
        '胶装。本 PDF 为按需印刷母版；书号、出版者与印次均未分配，'
        '不按正式出版物发行。</p>'
        + _draft_note(manifest) +
        '</div>')


def render_toc(entries: list[dict]) -> str:
    rows = ['<div class="book-toc">', '<h1 id="book-toc">目录</h1>',
            '<nav class="book-toc-list" aria-label="目录">']
    for entry in entries:
        level = int(entry["level"])
        kind = entry.get("kind", "")
        rows.append(
            f'<div class="toc-row toc-level-{level} toc-{_e(kind)}">'
            f'<a href="#{_e(entry["anchor"])}">'
            f'<span class="toc-title">{_e(entry["title"])}</span>'
            '<span class="toc-dots" aria-hidden="true"></span>'
            '<span class="toc-page">000</span></a></div>')
    rows.append("</nav></div>")
    return "\n".join(rows)


def render_list(title: str, page_id: str, entries: list[dict], label: str) -> str:
    rows = ['<div class="book-toc">',
            f'<h1 id="{_e(page_id)}">{_e(title)}</h1>',
            '<nav class="book-toc-list" aria-label="' + _e(title) + '">']
    for entry in entries:
        short = entry.get("title")
        text = (f'{entry["number"]}　{short}' if short and entry.get("number")
                else entry.get("caption") or short or "")
        rows.append(
            f'<div class="toc-row toc-level-2"><a href="#{_e(entry["anchor"])}">'
            f'<span class="toc-title">{_e(text)}</span>'
            '<span class="toc-dots" aria-hidden="true"></span>'
            '<span class="toc-page">000</span></a></div>')
    rows.append("</nav></div>")
    if not entries:
        rows.append(f'<p class="draft-note">本版尚未登记{_e(label)}。</p>')
    return "\n".join(rows)


def _unit_meta(chapters: list[str]) -> str:
    numbers = []
    for name in chapters:
        match = UNIT_CHAPTER_RE.search(str(name))
        if match:
            numbers.append(int(match.group(1)))
    if len(numbers) != len(chapters) or not numbers:
        return f"{len(chapters)} 章"
    if sorted(numbers) != list(range(min(numbers), max(numbers) + 1)):
        return f"{len(chapters)} 章"
    if len(numbers) == 1:
        return f"CH {numbers[0]:02d} · 1 章"
    return f"CH {min(numbers):02d}–{max(numbers):02d} · {len(chapters)} 章"


def part_opener(part: dict, art: str = "") -> str:
    part_id = _e(part["id"])
    units = part.get("units") or []
    chapter_count = sum(len(unit.get("chapters") or []) for unit in units)
    cards = "".join(
        f'<div class="unit-card">'
        f'<p class="unit-label">U{index:02d} · {_e(unit["title"])}</p>'
        f'<p class="unit-meta">{_e(_unit_meta(unit.get("chapters") or []))}</p>'
        '</div>'
        for index, unit in enumerate(units, 1))
    return (
        f'<div class="part-opener" data-part="{part_id}">'
        '<div class="part-hero">'
        '<div class="part-hero-top">'
        f'<span>PART {part_id} / 第{part_id}篇</span>'
        f'<span>{chapter_count} 章 · {len(units)} 个单元</span>'
        '</div>'
        f'<h1 id="part-{_e(part["id"].lower())}" class="part-heading">'
        f'<span class="part-kicker">第{part_id}篇</span>'
        f'<span class="part-title">{_e(part["title"])}</span></h1>'
        f'<p class="part-sub">{_e(part.get("subtitle", ""))}</p>'
        f'<div class="part-art" aria-hidden="true">{art}</div>'
        '<div class="part-hero-foot">'
        '<span>读法 · L1 直觉 → L2 推导 → L3 工程</span>'
        f'<span>PART {part_id} · {chapter_count} CHAPTERS</span>'
        '</div>'
        '</div>'
        f'<p class="part-intro">{_e(part.get("intro", ""))}</p>'
        f'<div class="part-units">{cards}</div>'
        '<div class="part-reading">'
        '<p class="reading-label"><span>本篇怎么读</span>'
        '<span class="en">READING LAYERS</span></p>'
        '<div class="reading-grid">'
        '<div class="reading-item"><span class="reading-no">L1</span><div>'
        '<strong>直觉</strong><p>先看图、比喻和现象，建立“为什么”的图像。</p>'
        '</div></div>'
        '<div class="reading-item"><span class="reading-no">L2</span><div>'
        '<strong>推导</strong><p>跟一遍关键公式，确认假设、单位和边界。</p>'
        '</div></div>'
        '<div class="reading-item"><span class="reading-no">L3</span><div>'
        '<strong>工程</strong><p>用仿真、实测和失效案例检验模型。</p>'
        '</div></div>'
        '</div>'
        '</div>'
        '</div>')


def appendix_opener(appendix: dict) -> str:
    return (
        f'<div class="appendix-opener" data-appendix="{_e(appendix["id"])}">'
        f'<h1 id="appendix-{_e(appendix["id"].lower())}">'
        f'附录 {_e(appendix["id"])}　{_e(appendix["title"])}</h1>'
        f'<p class="appendix-intro">{_e(appendix.get("intro", ""))}</p>'
        '</div>')


def render_bibliography(references: list[dict]) -> str:
    rows = ['<h1 id="bibliography">参考文献</h1>']
    if not references:
        rows.append('<p class="draft-note">本版为草稿：参考文献将在各章“延伸阅读”'
                    '统一为五列表后去重生成；稳定版要求不少于 100 条。</p>')
        return "\n".join(rows)
    ordered = sorted(references, key=lambda item: (
        str(item.get("authors", "")).lower(), str(item.get("title", "")).lower()))
    rows.append('<ol class="bibliography-list">')
    for number, item in enumerate(ordered, 1):
        chapters = "、".join(f"第 {ch} 章" for ch in item["chapters"])
        edition = f"，{_e(item['edition'])}" if item.get("edition") else ""
        rows.append(
            f'<li>[{number}] {_e(item["authors"])}：'
            f'《{_e(item["title"])}》{edition}。{_e(item["publisher"])}，'
            f'{_e(item["year"])}。{_e(item["isbn_or_url"])}。{_e(chapters)}。</li>')
    rows.append("</ol>")
    return "\n".join(rows)


def render_index(sections: list[tuple[str, list[dict]]]) -> str:
    rows = ['<h1 id="book-index">索引</h1>', '<div class="index-columns">']
    for letter, terms in sections:
        rows.append(f'<section class="index-letter"><h2>{_e(letter)}</h2><ul>')
        for term in terms:
            anchors = [term["primary"]] + [
                item for item in term["anchors"] if item != term["primary"]]
            pages = " ".join(
                f'<a class="index-page-link" href="#{_e(anchor)}">'
                '<span class="index-page">000</span></a>' for anchor in anchors)
            rows.append(
                f'<li><a class="index-term-link" href="#{_e(term["primary"])}">'
                f'<strong>{_e(term["term"])}</strong></a> '
                f'<span class="index-en">{_e(term["english"])}</span> {pages}</li>')
        rows.append("</ul></section>")
    rows.append("</div>")
    return "\n".join(rows)


def colophon(manifest: dict, stats: dict) -> str:
    pages = _e(stats["pages"])
    if "spine_mm" in stats:
        pagination = f'内文 {pages} 页，书脊厚度约 {_e(stats["spine_mm"])} mm。'
    else:
        # HTML 装配时还不知道物理页数；不得用逻辑页数冒充印前事实。
        pagination = (f'内文 {pages} 个逻辑页；印前页数与书脊厚度'
                      '以最终 PDF 与 PRINT-SPEC.md 为准。')
    return (
        '<div class="colophon">'
        '<h1 id="colophon">版本页</h1>'
        f'<p>《{_e(manifest["title"])}》{_e(manifest["edition"])}，'
        f'版本 {_e(manifest["version"])}，{_e(manifest["date"])}。</p>'
        f'<p>{pagination}'
        '开本 16K（185×260mm），正文 80g 纯质纸，封面 250g 铜版纸覆哑膜，胶装。</p>'
        '<p>内容源：docs/；排版：HTML + CSS + Chromium；PDF 后处理：PyMuPDF；'
        '公式：MathJax SVG；动画：仓库内 SMIL SVG。</p>'
        '<p>字体：Noto Serif SC、Noto Sans SC、JetBrains Mono，'
        'SIL Open Font License 1.1。</p>'
        f'<p>授权：{_e(manifest["license"])}。'
        f'仓库：{_e(manifest["repository"])}。</p>'
        '</div>')
