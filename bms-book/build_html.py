#!/usr/bin/env python3
"""Build the single-file HTML/PDF edition of the BMS book.

Usage: python build_html.py [--pdf]      # --pdf 额外打印带书签、带页码的 PDF
"""

from pathlib import Path
import html
import json
import re
import shutil
import subprocess
import tempfile
import argparse


from index_terms import first_body_page, index_label, index_term_rect, load_terms, term_pages


ROOT = Path(__file__).resolve().parent
BOOK = ROOT / "book"
DIST = ROOT / "dist"

MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
PARTS = [(p["id"], p["title"], p["description"], p["files"]) for p in MANIFEST["parts"]]

GUIDE_FIELDS = (
    ("本章要回答", "question"),
    ("读完应交出", "deliverable"),
    ("这一章不证明", "boundary"),
)
NUMBERED_FILES = {
    name
    for _, _, _, files in PARTS
    for name in files
    if name[:2].isdigit() and not name.startswith("00-")
}
if set(MANIFEST["chapter_guides"]) != NUMBERED_FILES:
    missing = sorted(NUMBERED_FILES - set(MANIFEST["chapter_guides"]))
    extra = sorted(set(MANIFEST["chapter_guides"]) - NUMBERED_FILES)
    raise RuntimeError(f"章节罗盘清单不完整：missing={missing}, extra={extra}")

SOURCES: dict[str, dict[str, str]] = MANIFEST.get("sources", {})
BOOK_SOURCES: list[str] = MANIFEST.get("book_sources", [])
CHAPTER_SOURCES: dict[str, list[str]] = MANIFEST.get("chapter_sources", {})
ACCESS_DATE = sorted({e["accessed"] for e in SOURCES.values() if "accessed" in e})[-1] if SOURCES else ""

INDEX_TERMS_PATH = ROOT / MANIFEST.get("index_terms", "index_terms.json")


def _load_index_terms(path: Path = INDEX_TERMS_PATH) -> list[str]:
    """加载去重后的术语索引清单；空项或重复项直接挡在构建前。"""
    return load_terms(path)


INDEX_TERMS = _load_index_terms()


def _validate_source_anchors() -> None:
    """来源锚点契约：编号章必登记、ID 可解析、登记项无孤儿。"""
    all_files = {name for _, _, _, files in PARTS for name in files}
    unknown_files = sorted(set(CHAPTER_SOURCES) - all_files)
    if unknown_files:
        raise RuntimeError(f"来源锚点：chapter_sources 含未知章节 {unknown_files}")
    for name in sorted(NUMBERED_FILES):
        if not CHAPTER_SOURCES.get(name):
            raise RuntimeError(f"来源锚点：{name} 未登记任何来源")
    used = {sid for ids in CHAPTER_SOURCES.values() for sid in ids} | set(BOOK_SOURCES)
    unknown = sorted(used - set(SOURCES))
    if unknown:
        raise RuntimeError(f"来源锚点：引用了未登记的来源 {unknown}")
    orphans = sorted(set(SOURCES) - used)
    if orphans:
        raise RuntimeError(f"来源锚点：登记表未被任何章或全书引用 {orphans}")


_validate_source_anchors()


def chapter_compass(name: str) -> str:
    guide = MANIFEST["chapter_guides"].get(name)
    if guide is None:
        return ""
    rows = "".join(
        f'<div><dt>{html.escape(label)}</dt><dd>{html.escape(guide[key])}</dd></div>'
        for label, key in GUIDE_FIELDS
    )
    return (
        '<aside class="chapter-compass" aria-label="本章罗盘">'
        '<p class="chapter-compass__eyebrow">本章导读 · 先定问题，再读证据</p>'
        f'<dl>{rows}</dl></aside>'
    )


def _source_link(entry: dict[str, str]) -> str:
    title = html.escape(entry["title"])
    if entry.get("url"):
        return f'<a href="{html.escape(entry["url"])}">{title}</a>'
    return f"<span>{title}</span>"


def chapter_source_anchors(name: str) -> str:
    """章末来源锚点卡：与 manifest sources 登记表一一对应。"""
    ids = CHAPTER_SOURCES.get(name)
    if not ids:
        return ""
    items = []
    for sid in ids:
        entry = SOURCES[sid]
        chips = [f'<span class="src-chip">{html.escape(entry["authority"])}</span>']
        if entry.get("snapshot"):
            chips.append(f'<span class="src-chip src-chip--snap">快照 {html.escape(entry["snapshot"])}</span>')
        if entry.get("license"):
            chips.append(f'<span class="src-chip">{html.escape(entry["license"])}</span>')
        items.append(f"<li>{_source_link(entry)}{''.join(chips)}</li>")
    return (
        '<aside class="source-anchors" aria-label="本章来源锚点">'
        '<p class="source-anchors__eyebrow">本章证据来源'
        f'（访问 {html.escape(ACCESS_DATE)} · <a href="#ch-38-sources">全表见附录 D 来源登记表</a>）</p>'
        f"<ul>{''.join(items)}</ul></aside>"
    )


# 章末「参考资料」h3 + 紧随其后的列表：打上类名，供打印版压缩成章末小字参考区。
_REFS_RE = re.compile(r'<h3([^>]*)>(参考资料 <a class="header-anchor".*?</h3>)\s*<ul>', re.S)


def _tag_chapter_refs(body: str) -> str:
    """给章末参考资料小节加 class（标题 chapter-refs__title、列表 chapter-refs）。"""
    return _REFS_RE.sub(r'<h3 class="chapter-refs__title"\1>\2<ul class="chapter-refs">', body, count=1)


def source_registry_html() -> str:
    """附录 D 末尾的来源登记表：按类别分组，标注快照、许可与被引章。"""
    cite_map: dict[str, list[str]] = {sid: [] for sid in SOURCES}
    for name, ids in CHAPTER_SOURCES.items():
        for sid in ids:
            cite_map[sid].append(name[:2])
    groups: dict[str, list[tuple[str, dict[str, str]]]] = {}
    for sid, entry in SOURCES.items():
        groups.setdefault(entry["authority"], []).append((sid, entry))
    sections = []
    for authority in sorted(groups):
        rows = []
        for sid, entry in sorted(groups[authority], key=lambda item: item[1]["title"]):
            meta = []
            if entry.get("snapshot"):
                meta.append(f"快照 {html.escape(entry['snapshot'])}")
            if entry.get("license"):
                meta.append(html.escape(entry["license"]))
            if entry.get("scope"):
                meta.append(html.escape(entry["scope"]))
            cited = cite_map.get(sid) or []
            if cited:
                meta.append(f"第 {'、'.join(n.lstrip('0') for n in cited)} 章引用")
            elif sid in BOOK_SOURCES:
                meta.append("全书 / 附录 D 引用")
            body = _source_link(entry)
            if meta:
                body += f'<p class="src-meta">{" · ".join(meta)}</p>'
            rows.append(f"<li>{body}</li>")
        sections.append(
            f'<section class="src-group"><h3>{html.escape(authority)}</h3>'
            f"<ul>{''.join(rows)}</ul></section>"
        )
    return (
        '<section class="source-registry" id="ch-38-sources" aria-label="来源登记表">'
        "<h2>来源登记表</h2>"
        f"<p>本表由 <code>manifest.json</code> 的 <code>sources</code> 登记生成，与各章末「来源锚点」一一对应"
        f"（访问日期 {html.escape(ACCESS_DATE)}）。带快照的来源按书中冻结版本引用；"
        "标准以现行有效版本原文为准，书中阈值凡属教学引用均已注明。</p>"
        f"{''.join(sections)}</section>"
    )


def _front_matter_html() -> str:
    """卷首三页：扉页、版权与使用、本书约定。

    标题刻意不用 <h1>/<h2>：Chrome 会把这些标题写进 PDF 大纲，而一级书签被
    当作「分部页」参与页眉跳过与目录定位——卷首三页混进去会让目录探测失效。
    这里用带 id 的段落承担版式，目录链接照旧可达。
    """
    title = html.escape(MANIFEST["title"])
    subtitle = html.escape(MANIFEST["subtitle"])
    author = html.escape(MANIFEST["author"])
    license_text = html.escape(MANIFEST["license"])
    version = html.escape(MANIFEST["version"])
    return f"""
<section class="front-matter title-page" id="title-page" aria-label="扉页">
  <p class="front-matter__eyebrow">BMS 实战</p>
  <p class="front-matter__title" id="title-page-heading">{title}</p>
  <p class="front-matter__subtitle">{subtitle}</p>
  <div class="front-matter__rule"></div>
  <p class="front-matter__author">{author}</p>
  <p class="front-matter__edition">v{version} · 2026-10 · 中文版</p>
  <p class="front-matter__note">配套开源项目：<a href="https://github.com/zhuguang-ZFG/BMS-Z">BMS-Z</a></p>
</section>
<section class="front-matter colophon" id="colophon" aria-label="版权与使用">
  <p class="front-matter__eyebrow">版权与使用</p>
  <p class="front-matter__title" id="colophon-heading">版权、引用与勘误</p>
  <dl class="book-facts">
    <dt>版本</dt><dd>v{version}（2026-10）</dd>
    <dt>作者</dt><dd>{author}</dd>
    <dt>许可</dt><dd>{license_text}</dd>
    <dt>引用</dt><dd>规范引用字段见仓库 <code>bms-book/CITATION.cff</code>；引用章节数字时同时写版本号与访问日期。</dd>
    <dt>勘误</dt><dd><a href="https://github.com/zhuguang-ZFG/BMS-Z/issues">GitHub Issues</a>；请附章节、小节、版本与复算过程。</dd>
    <dt>在线版</dt><dd><a href="https://zhuguang-zfg.github.io/BMS-Z/">zhuguang-zfg.github.io/BMS-Z</a></dd>
    <dt>构建</dt><dd><code>build_html.py</code> + Chromium + PyMuPDF；下载 PDF 受页眉、页脚、目录页码、元数据与索引契约共同校验。</dd>
  </dl>
  <p class="front-matter__note"><strong>数字口径：</strong>实测 / 合成 / 参考 / 独立真值 四类不能混称；教学阈值不能替代电芯 datasheet、法规原文与项目签字。</p>
</section>
<section class="front-matter conventions" id="conventions" aria-label="本书约定">
  <p class="front-matter__eyebrow">本书约定</p>
  <p class="front-matter__title" id="conventions-heading">读数字以前，先看它的身份</p>
  <div class="convention-grid">
    <section><h2>单位与符号</h2><p>电压用 V / mV，电流用 A / mA，电量用 Ah / mAh，时间用 s / h；电流正负必须跟随该章声明，跨数据集时先对账再积分。</p></section>
    <section><h2>阈值与参数</h2><p>凡写“教学合成值”“示例线”的数字，只用于复算方法；产品阈值必须回到具体电芯、温度、老化与法规条款。</p></section>
    <section><h2>编号与引用</h2><p>章节用 X.Y；图与表用 X-Y；正文提到实验输出时给脚本、工况、种子或数据卡，不用“据说”“典型值”替代来源。</p></section>
    <section><h2>证据块</h2><p>“现场”给问题，“一句话”收边界，“坑”写反例，“动手”交复现；赶时间先读“一句话”，想复现照“动手”跑；来源锚点锁定版本，不能把链接可达当成结论成立。</p></section>
  </div>
</section>
"""


def _index_html(terms: list[str]) -> str:
    """生成卷末索引骨架；页码由 PyMuPDF 在最终 PDF 上二次盖章。"""
    items = "".join(
        '<li><span class="book-index__term" '
        f'data-index-term="{html.escape(term, quote=True)}">{html.escape(term)}</span>'
        '<span class="book-index__refs" aria-hidden="true"></span></li>'
        for term in terms
    )
    return (
        '<section class="chapter book-index" data-part="p8" aria-labelledby="book-index">'
        '<div class="chapter-ribbon">卷末 / 术语索引</div>'
        '<h2 id="book-index">索引</h2>'
        '<p class="book-index__intro">页码按最终 PDF 文字层生成；每词最多列六页，更多命中以省略号标记。'
        '术语表本身不计入索引。</p>'
        f'<ol class="book-index__list">{items}</ol></section>'
    )


CSS = """
:root {
  /* 色板的单一来源：屏幕阅读的温润纸色。深色模式与打印各自只改这一组变量，
     元素规则一律吃变量——上一轮的教训是温纸皮肤把色值硬编码在规则里，
     深色模式下正文已转深底、封面与分部页却仍是奶白（实测 15.4:1 直射眼睛），
     打印页又出现「暖色分部页 + 冷色章内强调」两套色混排。 */
  --ink:#28241f; --muted:#71695f; --border:#ddd5c8; --border-strong:#c9bca8;
  --paper:#fffefa; --surface:#faf7f1; --soft:#f1ece2; --page:#efebe3;
  --accent:#3f6f67; --link:#1c5a7a;
  /* 卷首与分部页自带纸色：比正文纸略深一档，翻到这两处知道「换场了」。 */
  --feature-paper:#f6f1e8; --feature-ink:#27231e; --feature-muted:#665e54;
  --feature-border:#d8cfc0;
  --book-reader-scale:1;
  --sans:"Noto Sans SC","Noto Sans CJK SC","MiSans","HarmonyOS Sans SC","Microsoft YaHei",system-ui,sans-serif;
  --serif:"Noto Serif SC","Noto Serif CJK SC","Source Han Serif SC",Georgia,serif;
}
* { box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
body { margin:0 auto; max-width:880px; padding:44px 26px 112px;
       font-family:var(--serif); color:var(--ink); line-height:1.9;
       font-size:calc(17px * var(--book-reader-scale));
       background:var(--paper); text-rendering:optimizeLegibility;
       text-spacing-trim:trim-start; text-autospace:normal; }
body { overflow-wrap:anywhere; }
h2 { font-size:2rem; margin:2.6rem 0 1rem; padding-bottom:.45rem;
     border-bottom:2px solid var(--accent); color:var(--accent); }
h3 { font-size:1.4rem; margin:2rem 0 .7rem; color:var(--ink); }
h4 { font-size:1.15rem; margin:1.5rem 0 .5rem; color:var(--ink); }
/* 小节题层级：h3 上方一条通栏发丝线把章切成段落群，h4 只靠字号与字重收一级。
   不用彩色竖条——一章里十几处竖条会让版面碎成色块。 */
.chapter h3 { margin-top:2.8rem; padding:1.05rem 0 0; color:var(--ink);
  border-top:1px solid var(--border); font-size:1.34rem; font-weight:700; }
.chapter h4 { color:var(--ink); font-size:1.08rem; }
h1, h2, h3, h4 { break-after:avoid; page-break-after:avoid; }
p, li { text-align:justify; orphans:3; widows:3; }
p { margin:.75rem 0; }
/* 书刊体：章内正文首行缩进两字符、段距收紧——「新段落」由缩进表达，不再靠空行。
   章节开头与题注、元信息之后的首段不缩进；提示卡、读图卡、索引、卷首这些
   非正文流里的段落保持顶格。 */
.chapter p { text-indent:2em; margin:.5rem 0; }
.chapter > :is(p,ul,ol,blockquote,h3,h4) { max-width:44rem; margin-left:auto; margin-right:auto; }
.chapter :is(h2,h3,h4) + p, .chapter .chapter-meta + p,
.chapter .table-caption + p { text-indent:0; }
.chapter :is(.callout,.reader-map,.source-anchors) p, .chapter li p,
.chapter .table-caption, .chapter.book-index p,
.front-matter p, .part-divider p { text-indent:0; }
/* 列表符号着分部主题色：与 STM32 参考书一致的小节制。 */
.chapter li::marker { color:var(--accent); font-weight:700; }
ul, ol { padding-left:1.4rem; }
code { font-family:"JetBrains Mono",Consolas,monospace; font-size:.9em;
       background:var(--soft); padding:.1em .35em; border-radius:4px; }
pre { background:#2b2823; color:#f0ece2; padding:1rem 1.1rem; overflow:auto;
      border-radius:10px; border:1px solid #403a32; line-height:1.55;
      text-spacing-trim:normal; text-autospace:no-autospace; }
/* 代码块与图解卡同一色彩语言：顶条着分部主题色。 */
pre { border-top:3px solid var(--accent); }
pre code { background:none; color:inherit; padding:0; }
.vp-adaptive-theme > button.copy, .vp-adaptive-theme > span.lang { display:none; }
table { border-collapse:collapse; width:100%; margin:1.25rem 0;
        font-size:.92em; border-top:2px solid var(--ink); border-bottom:2px solid var(--ink);
        break-inside:avoid; }
th, td { padding:.55rem .7rem; vertical-align:top; }
thead th { border-bottom:1.5px solid var(--ink); background:var(--surface);
           text-align:left; font-family:var(--sans); font-weight:700; }
tbody tr + tr td, tbody tr + tr th { border-top:1px solid var(--border); }
blockquote { margin:1rem 0; padding:.6rem 1rem; color:var(--muted);
             border-left:4px solid var(--border); background:var(--surface); }
a { color:var(--link); text-decoration:none; }
a:hover { text-decoration:underline; }
mark { background:#f6e6a8; padding:0 .15em; border-radius:3px; }
/* 图解卡：一圈发丝线 + 顶边略深一档，不用阴影也不用签条——图自己就是重点。 */
figure { margin:2.2rem 0; padding:1rem; position:relative;
         border:1px solid var(--border); border-top:1px solid var(--border-strong);
         border-radius:8px; background:var(--paper); break-inside:avoid; }
figure img { width:100%; height:auto; border-radius:9px; display:block; }
figcaption { margin-top:.8rem; padding:.75rem .15rem .05rem; border-top:1px solid var(--border);
             color:var(--muted); font-size:.86em; line-height:1.72; text-align:center; }

/* 章首：留白开场而非色块开场——顶部给足空气，层级靠字面与发丝线建立。 */
.chapter { break-before:page; page-break-before:always; position:relative;
           padding:4.4rem 1.2rem 0; }
/* 章首幽灵章号：大号浅色水印压在题区右上方，经典大典的章首记号；
   章号来自 section 的 data-chapter-no（编号章两位数字，附录用字母）。 */
.chapter[data-chapter-no]::before { content:attr(data-chapter-no); position:absolute;
  top:2.65rem; right:1rem; z-index:0; pointer-events:none;
  font:800 5.2rem/1 var(--sans); letter-spacing:-.05em;
  color:var(--accent); opacity:.055; }
.chapter > * { position:relative; z-index:1; }
.chapter-ribbon { display:flex; align-items:center; gap:.65rem; margin-bottom:.8rem;
                  color:var(--muted); font:700 .7rem/1 var(--sans);
                  letter-spacing:.16em; text-transform:uppercase; }
.chapter-ribbon::before { content:""; width:1.75rem; height:1px; background:var(--accent);
                          border-radius:99px; }
/* 章题压一条分部主题色的细下划线：全书章首的签名，比色块安静、在纸上也立得住。 */
.chapter > h2:first-of-type { margin:.2rem 0 1rem; padding:0 5.5rem .9rem 0;
  color:var(--ink); border-bottom:1px solid color-mix(in srgb,var(--accent) 48%,var(--border));
  font-size:2.45rem; font-weight:650; line-height:1.28; letter-spacing:.005em; }
.chapter :is(h2,h3,h4):focus { outline:none; }
/* 章节构成用「·」分隔的一行小字，不是一排药丸：它是元信息，不该抢正文的注意力。 */
.chapter-meta { display:flex; flex-wrap:wrap; gap:0; margin:.4rem 0 1.7rem;
                color:var(--muted); font:.78rem/1.4 var(--sans); }
.chapter-stat { display:inline-flex; align-items:baseline; gap:.28rem;
                padding:.08rem .65rem .08rem 0; }
.chapter-stat + .chapter-stat::before { content:"·"; margin-right:.65rem; color:var(--border-strong); }
.chapter-stat strong { color:var(--ink); font-size:.78rem; font-weight:650; }
.chapter-nav { display:flex; justify-content:space-between; gap:1rem; margin:2rem 0;
               padding:1rem 0; border-top:1px solid var(--border); font:.85rem/1.6 var(--sans); }
.chapter-nav a { max-width:45%; }
.chapter-nav a:last-child { text-align:right; }
/* 九个分部的主题色：章与分部页同吃一份，翻到哪个分部、章题下划线与分部页宽边同色。
   饱和度压到纸色能托住的档位——高饱和的霓虹蓝紫压在暖纸上会发灰发脏。
   p0（导读）单独给一档暖灰：它不是编号分部，沿用 :root 的话会和第一部分同色，
   翻书时「导读」与「第一部分」看起来是同一段。 */
:is(.chapter,.part-divider)[data-part="p0"] { --accent:#6b5f50; }
:is(.chapter,.part-divider)[data-part="p1"] { --accent:#3f6f67; }
:is(.chapter,.part-divider)[data-part="p2"] { --accent:#8a4653; }
:is(.chapter,.part-divider)[data-part="p3"] { --accent:#4e638a; }
:is(.chapter,.part-divider)[data-part="p4"] { --accent:#695581; }
:is(.chapter,.part-divider)[data-part="p5"] { --accent:#8a6532; }
:is(.chapter,.part-divider)[data-part="p6"] { --accent:#3f7180; }
:is(.chapter,.part-divider)[data-part="p7"] { --accent:#486f50; }
:is(.chapter,.part-divider)[data-part="p8"] { --accent:#62666b; }

/* 分部页：纸色底 + 左侧一道分部主题色宽边。原先是整页深色渐变，屏幕上八次跳黑、
   打印时八页满版油墨，而它承载的信息只有三行字。 */
.part-divider { break-before:page; page-break-before:always;
                min-height:70vh; display:flex; flex-direction:column; justify-content:center;
                padding:2.4rem; position:relative; overflow:hidden;
                color:var(--feature-ink); border:1px solid var(--feature-border);
                border-left:8px solid var(--accent); border-radius:3px;
                background:var(--feature-paper); }
.part-divider::after { content:""; position:absolute; width:280px; height:280px; right:-90px;
                       bottom:-110px; border:1px solid rgba(58,48,37,.09); border-radius:50%;
                       box-shadow:0 0 0 38px rgba(58,48,37,.025),0 0 0 76px rgba(58,48,37,.015); }
/* 分部幽灵号：右上角巨型主题色水印，与章首幽灵章号同一签名体系。 */
.part-divider::before { content:attr(data-part-no); position:absolute; top:.9rem; right:1.4rem;
  font:800 8.6rem/1 var(--sans); letter-spacing:-.05em; color:var(--accent); opacity:.08; }
.part-divider > * { position:relative; z-index:1; }
.part-divider .part-no { font:700 .78rem/1 var(--sans); letter-spacing:.22em;
                         color:var(--accent); margin-bottom:1rem; }
.part-divider h1 { font-size:2.1rem; margin:0 0 .6rem; color:var(--feature-ink);
                   border:none; font-weight:650; }
.part-divider p { color:var(--feature-muted); font-size:1rem; margin:.15rem 0; max-width:620px; }
.part-divider .part-meta { margin-top:1.4rem; padding-top:1rem;
                           border-top:1px solid var(--feature-border);
                           color:var(--feature-muted); font:500 .86rem/1.6 var(--sans); }

/* 提示卡：只留左侧一条类型色竖线 + 一层极淡的类型色底，不描边不加阴影。
   一章里四五张卡，描边会把正文切成一格一格。 */
.callout { margin:1.6rem 0; padding:1rem 1.15rem .9rem; border:0;
           border-left:3px solid var(--c); border-radius:2px;
           background:color-mix(in srgb,var(--bg) 56%,var(--paper)); break-inside:avoid; }
.callout .callout-title { font-weight:800; color:var(--c); margin-bottom:.3rem;
                          font-family:"Noto Sans SC","Microsoft YaHei",sans-serif;
                          font-size:.72rem; letter-spacing:.12em; }
/* 类型记号收成一个小圆点：◆■▲● 四个异形符号在中文字面里忽大忽小，对不齐基线。 */
.callout-title::before { content:""; display:inline-block; width:.35rem; height:.35rem;
  margin-right:.55rem; border-radius:50%; background:currentColor; vertical-align:.08em; }
.callout p:last-child { margin-bottom:0; }
.callout.story { --c:#9a631f; --bg:#faf2df; }
.callout.principle { --c:#315f77; --bg:#edf4f5; }
.callout.trap { --c:#9b4350; --bg:#faedef; }
.callout.lab { --c:#2d6a59; --bg:#edf5f1; }
.reading-bet { margin:1.25rem 0 1.45rem; padding:.9rem 1.05rem 1rem;
  border:1px solid var(--bet-line); border-left:3px solid var(--bet-c); border-radius:5px;
  background:var(--bet-bg); font-family:var(--sans); break-inside:avoid;
  --bet-c:#6d5b83; --bet-line:#d8d0c5; --bet-bg:#f7f4f8; }
.reading-bet__eyebrow { margin:0 0 .42rem; color:var(--bet-c); font-size:.76rem;
  font-weight:850; letter-spacing:.08em; }
.reading-bet > p:not(.reading-bet__eyebrow) { margin:.2rem 0 .6rem; font-weight:700; }
.reading-bet ol { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.5rem;
  margin:.55rem 0 0; padding:0; list-style:none; counter-reset:bet; }
.reading-bet li { counter-increment:bet; padding:.48rem .62rem; border:1px solid var(--bet-line);
  border-radius:6px; background:color-mix(in srgb,var(--paper) 72%,transparent);
  font-size:.88rem; line-height:1.5; }
.reading-bet li::before { content:counter(bet, upper-alpha) ". "; color:var(--bet-c); font-weight:850; }

.toc { background:var(--surface); border:1px solid var(--border); border-radius:8px;
       padding:1.3rem 1.5rem; margin:2rem 0; }
.toc > strong { display:block; margin-bottom:.7rem; font:800 1.05rem/1 var(--sans);
                letter-spacing:.08em; color:var(--ink); }
.toc ul { margin:.25rem 0; padding-left:0; list-style:none; columns:2; column-gap:2rem; }
.toc li { margin:.13rem 0; break-inside:avoid; padding:.16rem .4rem; border-radius:6px; }
.toc li:hover { background:var(--soft); }
.toc li:hover a { color:var(--accent); text-decoration:none; }
.toc { font-size:.92em; }
.toc .toc-part { list-style:none; margin:.55rem 0 .15rem; font-weight:700;
                 color:var(--ink); font-family:var(--sans); column-span:all; }
.toc a { color:var(--ink); }

.cover { min-height:92vh; display:flex; flex-direction:column; justify-content:center;
         padding:3.4rem 2.4rem; margin:-44px -26px 0; position:relative; overflow:hidden;
         color:var(--feature-ink); background:var(--feature-paper);
         border-left:10px solid var(--accent); }
/* 封面压一个超大浅色「BMS」：书脊式的字母水印，不用图片也能有一张封面的分量。 */
.cover::before { content:"BMS"; position:absolute; right:1.3rem; bottom:.2rem;
  font:800 9rem/1 var(--sans); letter-spacing:-.08em; color:var(--accent); opacity:.055; }
.cover > * { position:relative; z-index:1; }
.cover-eyebrow { margin:0; color:var(--feature-muted); font:600 .72rem/1 var(--sans); letter-spacing:.28em; }
.cover-rule { width:5.5rem; height:1px; background:var(--border-strong); margin:1.6rem 0; }
.cover h1 { max-width:12ch; border:none; color:var(--feature-ink);
            font-family:Georgia,"Noto Serif SC","Songti SC","SimSun",serif;
            font-size:3.2rem; font-weight:650; line-height:1.24; margin:0 0 1.4rem; letter-spacing:.02em; }
.cover .sub { color:var(--feature-muted); font-size:1.05rem; max-width:34rem; line-height:1.9; }
.cover .meta { margin-top:2.2rem; color:var(--feature-muted); font-size:.88rem; }

.front-matter { break-before:page; page-break-before:always; min-height:78vh;
                display:flex; flex-direction:column; justify-content:center; padding:2.2rem; }
.front-matter h1, .front-matter__title { margin:.45rem 0 .8rem; font-size:2.35rem; line-height:1.3;
                                        color:var(--ink); font-weight:800; }
.front-matter h2 { margin:.4rem 0; padding:0; border:0; color:var(--ink); font-size:1.05rem; }
.front-matter__eyebrow { margin:0; color:var(--accent); font:800 .74rem/1 var(--sans);
                         letter-spacing:.18em; }
.front-matter__subtitle { max-width:660px; color:var(--muted); font-size:1.08rem; }
.front-matter__rule { width:5rem; height:4px; margin:1.4rem 0; border-radius:99px; background:var(--accent); }
/* 扉页用居中版式：经典书名页的对称构图；版权页与约定页保持左对齐阅读流。 */
.front-matter.title-page { text-align:center; align-items:center; }
.front-matter.title-page .front-matter__rule { margin-left:auto; margin-right:auto; }
.front-matter.title-page .front-matter__subtitle { margin-left:auto; margin-right:auto; }
.front-matter__author { margin:.2rem 0; font:800 1rem/1.4 var(--sans); }
.front-matter__edition, .front-matter__note { color:var(--muted); font-size:.9rem; }
.book-facts { display:grid; grid-template-columns:6rem 1fr; gap:.42rem 1rem; margin:1rem 0; }
.book-facts dt { font:800 .82rem/1.6 var(--sans); color:var(--accent); }
.book-facts dd { margin:0; font-size:.9rem; }
.convention-grid { display:grid; grid-template-columns:1fr 1fr; gap:.8rem; margin-top:1rem; }
.convention-grid section { padding:1rem; border:1px solid var(--border); border-radius:12px;
                           background:var(--surface); break-inside:avoid; }
.convention-grid p { margin:.35rem 0 0; font-size:.9rem; color:var(--muted); }
.table-caption { margin:1.35rem 0 -.85rem; color:var(--muted);
                 font:.82rem/1.5 var(--sans); break-after:avoid; page-break-after:avoid; }
.table-caption strong { color:var(--ink); }
.table-caption + table { margin-top:1rem; }
.book-index__intro { color:var(--muted); font-size:.9rem; }
.book-index__list { margin:1.2rem 0; padding:0; list-style:none; }
.book-index__list li { display:flex; align-items:baseline; gap:.55rem; min-height:1.65rem;
                       break-inside:avoid; font-size:.92rem; }
.book-index__term { flex:none; font-family:var(--sans); font-weight:650; }
.book-index__refs { flex:1; min-width:5rem; border-bottom:1px dotted var(--border); }

.reader-map { margin:2rem 0; padding:1.5rem; border:1px solid var(--border);
              border-radius:8px; background:var(--surface); }
.source-anchors { margin:1.8rem 0 0; padding:1rem 1.2rem 1.15rem; border:1px solid var(--border);
  border-left:2px solid var(--accent); border-radius:5px; background:var(--surface);
  break-inside:avoid; font:.86rem/1.7 var(--sans); }
.source-anchors__eyebrow { margin:0 0 .55rem; color:var(--accent);
  font:800 .7rem/1.3 var(--sans); letter-spacing:.12em; }
.source-anchors ul { margin:0; padding:0; list-style:none; }
.source-anchors li { margin:.32rem 0; text-align:left; }
.source-anchors li > a, .source-anchors li > span { margin-right:.5rem; }
.src-chip { display:inline-block; margin:.12rem .18rem 0 0; padding:.04rem .48rem;
  border:1px solid var(--border); border-radius:999px; color:var(--muted); font-size:.74rem; }
.src-chip--snap { color:var(--accent); border-color:var(--accent); }
.source-registry { margin:2.4rem 0 0; }
.source-registry > p { color:var(--muted); font-size:.92rem; }
.src-group h3 { margin:1.5rem 0 .45rem; color:var(--ink); }
.src-group ul { margin:0; padding-left:1.25rem; }
.src-group li { margin:.3rem 0; font-size:.93em; text-align:left; }
.src-meta { margin:.08rem 0 0; color:var(--muted); font-size:.84em; }
.reader-map .map-eyebrow { margin:0 0 .45rem; color:var(--accent);
                           font:800 .75rem/1 var(--sans); letter-spacing:.16em; }
.reader-map h2 { margin:.25rem 0 .55rem; padding:0; border:0; color:var(--ink); font-size:1.75rem; }
.reader-map > p { color:var(--muted); margin:0 0 1rem; }
.route-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.75rem; }
.route-card { display:block; padding:1rem; border:1px solid var(--border); border-radius:6px;
              color:var(--ink); background:var(--paper); text-decoration:none; }
.route-card:hover { border-color:var(--accent); text-decoration:none; transform:translateY(-1px); }
.route-card strong { display:block; margin-bottom:.25rem; font:750 .95rem/1.4 var(--sans); color:var(--ink); }
.route-card span { display:block; color:var(--muted); font-size:.84rem; line-height:1.55; }
.route-card:focus-visible, a:focus-visible { outline:3px solid var(--accent); outline-offset:4px; }
.skip-link { position:absolute; top:0; left:1rem; transform:translateY(-140%); z-index:10;
             background:var(--paper); padding:.5rem 1rem; }
.skip-link:focus { transform:translateY(0); }

.back-to-toc { position:fixed; right:1rem; bottom:1rem; display:grid; place-items:center;
  width:3rem; height:3rem; padding:0; background:var(--paper); border:1px solid var(--border);
  border-radius:999px; box-shadow:0 8px 24px rgba(15,23,42,.16);
  font:700 .75rem/1 var(--sans); opacity:.94; }
.back-to-toc:hover { border-color:var(--accent); text-decoration:none; }
.reader-progress { position:fixed; top:0; left:0; right:0; z-index:30; height:2px;
  background:transparent; pointer-events:none; }
.reader-progress span { display:block; width:100%; height:100%; background:var(--accent);
  transform:scaleX(0); transform-origin:left center; transition:transform .12s linear; }
.reader-tools { position:fixed; left:1rem; bottom:1rem; z-index:25; display:flex;
  align-items:center; gap:.25rem; padding:.28rem; color:var(--muted); background:color-mix(in srgb,var(--paper) 92%,transparent);
  border:1px solid var(--border); border-radius:999px; box-shadow:0 6px 20px rgba(15,23,42,.12);
  backdrop-filter:blur(10px); font:650 .72rem/1 var(--sans); opacity:.72;
  transition:opacity .18s ease, box-shadow .18s ease; }
.reader-tools:hover, .reader-tools:focus-within { opacity:1; box-shadow:0 8px 24px rgba(15,23,42,.16); }
.reader-tools button { min-width:2.25rem; height:2.25rem; padding:0 .65rem; color:inherit;
  background:transparent; border:0; border-radius:999px; cursor:pointer; font:inherit; }
.reader-tools button:hover, .reader-tools button[aria-pressed="true"] { color:var(--accent); background:var(--soft); }
.reader-tools button:focus-visible { outline:2px solid var(--accent); outline-offset:1px; }
.reader-tools button:disabled { opacity:.35; cursor:default; }
.reader-tools__divider { width:1px; height:1.15rem; background:var(--border); }
.reader-tools output { min-width:4.8rem; text-align:center; font-variant-numeric:tabular-nums; }
/* 静读：把装饰收到最低——只剩纸、字和一条发丝线。行宽再收两字，专治「读到一半
   被侧栏、水印、色块拽走注意力」。开关与字号存在浏览器本地，不进正文。 */
html.book-calm body { line-height:2; }
html.book-calm .chapter[data-chapter-no]::before { display:none; }
html.book-calm .chapter-meta { opacity:.48; }
html.book-calm .chapter-ribbon { opacity:.58; }
html.book-calm .chapter > :is(p,ul,ol,blockquote,h3,h4) { max-width:40rem; }
html.book-calm :is(.callout,.reading-bet,.chapter-compass,.source-anchors,.book-lab) {
  box-shadow:none; background:var(--paper); }

/* 屏幕上给正文垫一张纸：页底色比纸略深，纸面靠一层极淡的投影浮起来。 */
html { background:var(--page); }
body { box-shadow:0 0 0 1px rgba(91,77,58,.06),0 24px 70px rgba(64,52,37,.08); }
mjx-container { display:inline-block; max-width:100%; overflow-x:auto; overflow-y:hidden;
                vertical-align:middle; }
mjx-container[display="true"] { display:block; }
@media (max-width:600px) {
  body { padding:20px 16px 80px; }
  .cover { margin:-20px -16px 0; padding:2rem 1rem; min-height:75vh; }
  .cover h1 { font-size:2rem; }
  .part-divider { min-height:35vh; padding:1.2rem; }
  h2 { font-size:1.6rem; }
  .chapter { padding-left:.5rem; }
  .chapter > h2:first-of-type { font-size:1.85rem; }
  html.book-calm .chapter > h2:first-of-type { font-size:1.75rem; }
  .chapter[data-chapter-no]::before { display:none; }
  table { display:block; overflow-x:auto; }
  p, li { text-align:left; }
  .toc ul { columns:1; }
  .route-grid { grid-template-columns:1fr; }
  .reading-bet ol { grid-template-columns:1fr; }
  .back-to-toc { right:.65rem; bottom:.65rem; width:2.75rem; height:2.75rem; }
  .reader-tools { left:.65rem; bottom:.65rem; max-width:calc(100vw - 4.4rem); }
  .reader-tools output { display:none; }
}
@media (prefers-reduced-motion:reduce) {
  .reader-progress span, .reader-tools { transition:none; }
}
/* 深色模式：只改这一组变量就够——元素规则一律吃变量。卷首与分部页也必须在这里
   换掉自己那组 --feature-*，否则封面和八张分部页会留着奶白纸色，在深底正文里
   一页一页直射眼睛（实测对比度 15.4:1）。 */
@media (prefers-color-scheme:dark) {
  :root { --ink:#e8e3da; --muted:#aea69a; --border:#39404a; --border-strong:#4a525e;
          --paper:#121722; --surface:#181e29; --soft:#232a37; --page:#0b0f17;
          --accent:#79a79f; --link:#93c5fd;
          --feature-paper:#171d28; --feature-ink:#ece7de; --feature-muted:#b3aba0;
          --feature-border:#39404a; }
  body { box-shadow:none; }
  pre { background:#0d1117; border-color:#262c36; }
  .part-divider::after { border-color:rgba(255,255,255,.07);
    box-shadow:0 0 0 38px rgba(255,255,255,.022),0 0 0 76px rgba(255,255,255,.012); }
  .callout.story { --c:#d2a44f; --bg:#2a2317; }
  .callout.principle { --c:#7fa8bd; --bg:#17222a; }
  .callout.trap { --c:#d08c95; --bg:#2a1a1d; }
  .callout.lab { --c:#73b39c; --bg:#15241f; }
  .reading-bet { --bet-c:#a492c0; --bet-line:#3c3650; --bet-bg:#1d1a28; }
  :is(.chapter,.part-divider)[data-part="p0"] { --accent:#a79c8c; }
  :is(.chapter,.part-divider)[data-part="p1"] { --accent:#79a79f; }
  :is(.chapter,.part-divider)[data-part="p2"] { --accent:#c08e97; }
  :is(.chapter,.part-divider)[data-part="p3"] { --accent:#93a3c4; }
  :is(.chapter,.part-divider)[data-part="p4"] { --accent:#a898bd; }
  :is(.chapter,.part-divider)[data-part="p5"] { --accent:#c4a471; }
  :is(.chapter,.part-divider)[data-part="p6"] { --accent:#80aab8; }
  :is(.chapter,.part-divider)[data-part="p7"] { --accent:#8bb294; }
  :is(.chapter,.part-divider)[data-part="p8"] { --accent:#a3a8ae; }
}
/* 打印：纸由印厂提供，所以底色一律退成白（纸色底满版铺油墨既贵又脏），
   但墨色与分部色沿用屏幕那一套暖色——这样同一本书的屏与纸是一个长相。
   上一轮这里把 :root 重置成冷色板，却没动分部页的暖色规则，于是印出来
   「暖色分部页 + 冷色章内强调」两套色同页混排。 */
@media print {
  :root { --paper:#ffffff; --surface:#faf8f4; --soft:#f1ece4; --page:#ffffff;
          --feature-paper:#ffffff; }
  .back-to-toc, .skip-link, .chapter-nav, .reader-tools, .reader-progress { display:none; }
  body { box-shadow:none; }
  .cover, .part-divider { border:0; border-left:6px solid var(--accent); }
  .cover::before, .part-divider::after { display:none; }
  pre { background:#f4f1ea; color:#2b2823; border-color:var(--border-strong); }
  @page { size:A4; margin:17mm 16mm; }
  body { max-width:none; padding:0; font-size:10.2pt; line-height:1.62; letter-spacing:.015em; }
  .cover { min-height:245mm; margin:0; padding:2.5rem 1.5rem; page-break-after:always; }
  .part-divider { min-height:243mm; padding:2.4rem; border-radius:0; }
  .front-matter { min-height:243mm; padding:16mm 12mm; }
  .book-index__list li { min-height:6.2mm; }
  .chapter { padding-top:9mm; }
  .table-caption { font-size:9pt; }
  /* 读者地图另起一页、整体不拆：眉题不再孤悬上一页页底；图解入口紧跟其后。
     目录自起一页：路线卡也是章节链接，与目录同页会被当成缺页码的目录行（check_pdf 目录契约）。 */
  .reader-map { break-before:page; page-break-before:always; break-inside:avoid; }
  #contents { break-before:page; page-break-before:always; }
  .route-card { box-shadow:none; }
  pre { white-space:pre-wrap; overflow:visible; overflow-wrap:anywhere; }
  thead { display:table-header-group; }
  tr { break-inside:avoid; page-break-inside:avoid; }
  /* 长表允许跨页（表头重复、行不拆）：整表不拆会把术语表这类长表整张推到下一页，留下大片空白。 */
  table { break-inside:auto; }
  /* 高图限高：整图不拆时，过高的图被推走会在上一页留半页白；限高后更多图能留在原页。 */
  figure img { max-height:150mm; width:auto; max-width:100%; margin:0 auto; }
  /* 章末来源锚点：紧凑双栏、允许跨页，眉题跟随首条；不再整框被推到新页独占一页。 */
  .source-anchors { break-inside:auto; margin-top:1rem; padding:.7rem 1rem .75rem; font-size:.8rem; line-height:1.55; }
  .source-anchors__eyebrow { break-after:avoid; page-break-after:avoid; }
  .source-anchors ul { columns:2; column-gap:1.4rem; }
  .source-anchors li { break-inside:avoid; margin:.18rem 0; }
  /* 登记表条目与其元信息行同页：不让「第 15 章引用」一行孤落新页。 */
  .src-group li { break-inside:avoid; page-break-inside:avoid; }
  .src-group h3 { break-after:avoid; page-break-after:avoid; }
  /* 章末参考资料：小字双栏，标题随首条；与来源锚点合成一块紧凑的章末参考区，少翻一页。 */
  .chapter-refs__title { margin:1.2rem 0 .35rem; font-size:1rem; break-after:avoid; page-break-after:avoid; }
  .chapter-refs { columns:2; column-gap:1.4rem; margin:0; padding-left:1.1rem; font-size:.8rem; line-height:1.5; }
  .chapter-refs li { break-inside:avoid; margin:.12rem 0; text-align:left; overflow-wrap:anywhere; }
  /* 查阅型附录（地图 / 清单 / 参考资料）排紧一号：它们是查表不是通读，紧排后不再各拖一两行孤页。 */
  .chapter:is([data-chapter-no="A"],[data-chapter-no="B"],[data-chapter-no="D"]) { font-size:9.4pt; line-height:1.5; }
  .chapter:is([data-chapter-no="A"],[data-chapter-no="B"],[data-chapter-no="D"]) :is(h3,h4) { margin-top:1rem; }
  .src-group ul { columns:2; column-gap:1.4rem; }
  /* 二遍排版（copyfit）：首遍测出「末页只剩几行」的章，下一遍只给这些章收一点行距与段距，
     把溢出的几行拉回上一页；章节总是另起一页，所以只影响本章，不会把孤行推到别章。
     1 级收行距段距；1 级仍拖尾的章再上 2 级（字号微收、图限高更低）。 */
  .chapter[data-fit] { line-height:1.5; }
  .chapter[data-fit] p { margin:.4em 0; }
  .chapter[data-fit] :is(ul, ol, blockquote) { margin-top:.45em; margin-bottom:.45em; }
  .chapter[data-fit] h2 { margin:1.6rem 0 .7rem; }
  .chapter[data-fit] h3 { margin:1.2rem 0 .45rem; }
  .chapter[data-fit] :is(figure, .callout, .reading-bet, .book-lab, table) { margin-top:.9rem; margin-bottom:.9rem; }
  .chapter[data-fit="2"] { font-size:9.8pt; line-height:1.46; }
  .chapter[data-fit="2"] figure img { max-height:125mm; }
  /* 查阅型附录本身已是 9.4pt：二级紧排不能反把它放大到 9.8pt（同权重后者胜），这里压得更紧。 */
  .chapter:is([data-chapter-no="A"],[data-chapter-no="B"],[data-chapter-no="D"])[data-fit="2"] { font-size:9.2pt; line-height:1.44; }
  a { color:var(--ink); }
}
"""

VISUAL_CSS = """
.book-motion button { display:block; margin:.8rem 0; padding:.55rem .9rem;
  background:var(--paper); color:var(--accent); border:1px solid var(--accent);
  border-radius:8px; cursor:pointer; font:600 .85rem var(--sans); }
.book-motion button[hidden] { display:none; }
.visual-guide, .visual-question { font-size:.88rem; text-align:left; line-height:1.7; }
.visual-guide { color:var(--ink); }
.visual-question { color:var(--muted); padding-top:.5rem; border-top:1px solid var(--border); }
.book-lab { margin:1.8rem 0; padding:1.4rem; border:1px solid var(--border);
  border-top:1px solid var(--border-strong); border-radius:8px;
  background:var(--surface); break-inside:avoid; }
.book-lab h4 { margin:0 0 .4rem; color:var(--accent); }
.lab-controls { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.8rem; }
.lab-controls label { display:block; font:.88rem/1.6 var(--sans); }
.lab-controls input { display:block; width:100%; accent-color:var(--accent); margin:.4rem 0; }
.book-lab svg { width:100%; height:auto; display:block; color:var(--ink); }
.lab-readouts { display:flex; flex-wrap:wrap; gap:.6rem 1.4rem; font:.88rem/1.7 var(--sans); margin:.7rem 0; }
.lab-readouts > span { padding:.35rem .65rem; background:var(--paper); border:1px solid var(--border); border-radius:7px; }
.book-lab [data-lab-reset] { margin:.5rem 0; padding:.4rem .7rem; border:1px solid var(--border); border-radius:7px;
  color:var(--accent); background:var(--paper); cursor:pointer; font:.82rem var(--sans); }
.book-lab [data-lab-reset][hidden] { display:none; }
.chapter-compass { margin:1.1rem 0 2.2rem; padding:1.25rem 1.35rem 1.35rem;
  border:1px solid var(--border); border-top:1px solid var(--border-strong); border-radius:8px;
  background:var(--surface); break-inside:avoid; }
.chapter-compass__eyebrow { margin:0 0 1rem; color:var(--muted);
  font:800 .7rem/1.3 var(--sans); letter-spacing:.15em; }
.chapter-compass dl { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin:0; }
.chapter-compass dl > div { min-width:0; padding:0 1rem; border-left:1px solid var(--border); }
.chapter-compass dl > div:first-child { padding-left:0; border-left:0; }
.chapter-compass dl > div:last-child { padding-right:0; }
.chapter-compass dt { margin:0 0 .35rem; color:var(--accent); font:700 .78rem/1.4 var(--sans); }
.chapter-compass dd { margin:0; color:var(--ink); font-size:.88rem; line-height:1.7; text-align:left; }
.book-lab:focus-within { border-color:var(--accent); }
figure figcaption { text-align:left; }
.lab-readouts output { font-weight:700; color:var(--accent); }
.timing-budget { margin:1rem 0 .35rem; }
.timing-track { position:relative; display:flex; height:1.2rem; overflow:visible;
  border:1px solid var(--border); border-radius:999px; background:var(--paper); }
.timing-phase { display:block; height:100%; background:var(--accent); }
.timing-phase:first-child { border-radius:999px 0 0 999px; }
.timing-phase.timing-wait { opacity:.32; }
.timing-phase.timing-confirm { opacity:.52; }
.timing-phase.timing-decision { opacity:.72; }
.timing-phase.timing-actuator { opacity:.95; }
.timing-ftti { position:absolute; top:-.35rem; bottom:-.35rem; width:0;
  border-left:2px dashed var(--ink); transform:translateX(-1px); }
.timing-legend { display:flex; flex-wrap:wrap; gap:.35rem 1rem; margin-top:.65rem;
  color:var(--muted); font:.76rem/1.5 var(--sans); }
.timing-legend span::before { content:""; display:inline-block; width:.7rem; height:.7rem;
  margin-right:.35rem; border-radius:3px; background:var(--accent); }
.timing-legend .timing-wait::before { opacity:.32; }
.timing-legend .timing-confirm::before { opacity:.52; }
.timing-legend .timing-decision::before { opacity:.72; }
.timing-legend .timing-actuator::before { opacity:.95; }
.timing-legend .timing-limit::before { width:0; border-radius:0; border-left:2px dashed var(--ink);
  background:transparent; }
.timing-status[data-state="within"] { color:#047857; }
.timing-status[data-state="over"] { color:#be123c; }
.book-lab .lab-note { font-size:.83rem; color:var(--muted); }
.frame-trace { margin:1.5rem 0; overflow:hidden; border:1px solid var(--border);
  border-top:1px solid var(--border-strong); border-radius:8px;
  background:var(--surface); break-inside:avoid; }
.frame-trace__head { padding:1.05rem 1.2rem .9rem; }
.frame-trace__eyebrow { margin:0 0 .3rem; color:var(--accent);
  font:800 .72rem/1 var(--sans); letter-spacing:.14em; }
.frame-trace__title { margin:.2rem 0 .45rem; color:var(--ink); font:700 1.15rem/1.4 var(--sans); }
.frame-trace__head > p:last-child { margin:0; color:var(--muted); text-align:left; }
.frame-trace__steps { margin:0; padding:0; list-style:none; }
.frame-trace__steps > li { display:grid; grid-template-columns:2.25rem minmax(0,1fr); gap:.85rem;
  padding:.9rem 1.2rem; border-top:1px solid var(--border); }
.frame-trace__index { display:grid; place-items:center; align-self:start; width:2.05rem; height:2.05rem;
  border:1px solid var(--accent); border-radius:50%; color:var(--accent); font:800 .72rem/1 var(--sans); }
.frame-trace__steps strong { display:block; font-family:var(--sans); }
.frame-trace__steps li > div > code { display:inline-block; margin:.38rem 0; }
.frame-trace__steps p { margin:.25rem 0; text-align:left; }
.frame-trace__steps small { display:block; margin-top:.35rem; color:var(--muted); font:.76rem/1.55 var(--sans); }
.frame-trace__steps small code { background:transparent; padding:0; }
.visual-index summary { font:700 1rem var(--sans); cursor:pointer; }
@media (max-width:600px) {
  .lab-controls { grid-template-columns:1fr; }
  .chapter-meta { gap:.35rem; }
  .chapter-stat { padding:.25rem .48rem; }
  .chapter-compass { padding:1rem; }
  .chapter-compass dl { grid-template-columns:1fr; }
  .chapter-compass dl > div { padding:.75rem 0; border-top:1px solid var(--border); border-left:0; }
  .chapter-compass dl > div:first-child { padding-top:0; border-top:0; }
  .chapter-compass dl > div:last-child { padding-bottom:0; }
  .frame-trace__head { padding:.9rem; }
  .frame-trace__steps > li { grid-template-columns:1.85rem minmax(0,1fr); gap:.65rem; padding:.8rem .9rem; }
  .frame-trace__index { width:1.7rem; height:1.7rem; }
}
@media (prefers-color-scheme:dark) {
  .timing-status[data-state="within"] { color:#6ee7b7; }
  .timing-status[data-state="over"] { color:#fda4af; }
}
@media print { .book-motion button, .book-lab [data-lab-reset] { display:none !important; } .lab-controls input { display:none; }
  .book-lab, .chapter-compass { padding:1rem; } .chapter-compass dd { font-size:9.5pt; } }
"""

def main(fit: dict[str, int] | None = None) -> None:
    """生成单文件 HTML；fit 为章号（data-chapter-no）→紧排级别，由 PDF 逐级排版回填。"""
    fit = fit or {}
    DIST.mkdir(parents=True, exist_ok=True)
    renderer = shutil.which("node")
    if renderer is None:
        raise RuntimeError("HTML 构建需要 Node.js 24+；请先在仓库根运行 npm ci")
    rendered = subprocess.run(
        [renderer, str(ROOT / "render.mjs")], check=True, capture_output=True,
        encoding="utf-8", timeout=120,
    )
    chapters = json.loads(rendered.stdout)
    toc = [
        '<li class="toc-part">卷首 · 版本、版权与阅读约定</li>',
        '<li><a href="#title-page">扉页</a></li>',
        '<li><a href="#colophon">版权、引用与勘误</a></li>',
        '<li><a href="#conventions">本书约定</a></li>',
    ]
    combined, body_parts = [], []
    index = 0
    chapter_links = {name: chapter["prefix"] for name, chapter in zip(
        (name for _, _, _, files in PARTS for name in files), chapters, strict=True
    )}
    routes = [
        ("建立系统观", "02-BMS的六件事.md", "从测量、判决到执行反馈，先画出一条闭环。", "第 1–8 章 → 第 25–26 章"),
        ("做一套可信的算法", "05-测量链.md", "先算测量误差，再辨识参数，用独立工况检查估计。", "第 5 章 → 第 10–17 章 → 第 27–28 章"),
        ("把数据接到现场", "18-通信帧状态机.md", "从帧边界走到身份、新鲜度、故障降级与回放。", "第 18–21 章 → 第 29 章 → 第 31 章"),
        ("读懂热与高压", "14-SOP与热.md", "把功率、温升与高压动作都写成可核对的账。", "第 14 章 → 第 30 章 → 第 32 章"),
    ]
    route_cards = ''.join(
        f'<a class="route-card" href="#{chapter_links[name]}"><strong>{html.escape(title)}</strong>'
        f'<span>{html.escape(description)}</span><span>{html.escape(sequence)}</span></a>'
        for title, name, description, sequence in routes
    )
    for part_id, part_title, part_desc, files in PARTS:
        label = f"{part_title} · {part_desc}"
        toc.append(f'<li class="toc-part">{html.escape(label)}</li>')
        body_parts.append(
            f'<section class="part-divider" data-part="{part_id}"'
            f' data-part-no="{int(part_id[1:]):02d}">'
            f'<div class="part-no">{html.escape(part_title)}</div>'
            f'<h1>{html.escape(part_desc)}</h1>'
            f'<p>{html.escape(MANIFEST["part_goals"][part_id])}</p>'
            f'<div class="part-meta">{len(files)} 篇 · 原理 / 实验 / 练习 / 证据</div></section>'
        )
        for name in files:
            chapter = chapters[index]
            combined.append((BOOK / name).read_text(encoding="utf-8"))
            index += 1
            toc.append(f'<li><a href="#{chapter["prefix"]}">{html.escape(chapter["title"])}</a></li>')
            chapter_body = chapter["body"]
            chapter_body = re.sub(
                r'<p><strong>(表 [A-E0-9]+-\d+)</strong>(.*?)</p>',
                r'<p class="table-caption"><strong>\1</strong>\2</p>',
                chapter_body,
                flags=re.DOTALL,
            )
            stats = [
                (chapter_body.count('<h3'), "小节"),
                (chapter_body.count('<figure'), "图解"),
                (chapter_body.count('class="callout '), "提示卡"),
                (chapter_body.count('class="reading-bet"'), "开读挑战"),
                (chapter_body.count('data-book-lab='), "交互"),
            ]
            stat_html = ''.join(
                f'<span class="chapter-stat"><strong>{count}</strong>{html.escape(label)}</span>'
                for count, label in stats if count
            )
            heading_end = chapter_body.index('</h2>') + len('</h2>')
            chapter_body = (
                chapter_body[:heading_end]
                + f'<div class="chapter-meta" aria-label="章节构成">{stat_html}</div>'
                + chapter_compass(name)
                + chapter_body[heading_end:]
            )
            previous = chapters[index - 2] if index > 1 else None
            following = chapters[index] if index < len(chapters) else None
            previous_link = (
                f'<a href="#{previous["prefix"]}">上一章 · {html.escape(previous["title"])}</a>'
                if previous else '<a href="#contents">全书目录</a>'
            )
            following_link = (
                f'<a href="#{following["prefix"]}">下一章 · {html.escape(following["title"])}</a>'
                if following else '<a href="#contents">全书目录</a>'
            )
            chapter_body = _tag_chapter_refs(chapter_body)
            chapter_body += chapter_source_anchors(name)
            if name == "附录D-参考资料.md":
                chapter_body += source_registry_html()
            chapter_body += f'<nav class="chapter-nav" aria-label="章节翻页">{previous_link}{following_link}</nav>'
            match_num = re.search(r"第 (\d+) 章", chapter["title"])
            match_app = re.search(r"附录 ([A-E])", chapter["title"])
            chapter_no = (
                f"{int(match_num.group(1)):02d}" if match_num
                else (match_app.group(1) if match_app else "")
            )
            no_attr = f' data-chapter-no="{chapter_no}"' if chapter_no else ""
            if chapter_no in fit:
                no_attr += f' data-fit="{fit[chapter_no]}"'
            body_parts.append(
                f'<section class="chapter" data-part="{part_id}"{no_attr}'
                f' aria-labelledby="{chapter["prefix"]}">'
                f'<div class="chapter-ribbon">{html.escape(part_title)} / {html.escape(part_desc)}</div>'
                f'{chapter_body}</section>'
            )
    toc.append('<li class="toc-part">卷末 · 关键词页码</li>')
    toc.append('<li><a href="#book-index">索引</a></li>')
    body_parts.append(_index_html(INDEX_TERMS))
    (DIST / "bms-book.md").write_text("\n\n---\n\n".join(combined), encoding="utf-8")

    visuals = json.loads((ROOT / 'visuals.json').read_text(encoding='utf-8'))
    visual_links = ''.join(
        f'<li><a href="#{chapter_links[next(name for name in chapter_links if name.startswith(v["chapter"] + "-"))]}">'
        f'第 {int(v["chapter"])} 章 · {html.escape(v["caption"].split("：")[0].split("。")[0])}</a></li>'
        for v in visuals
    )

    reader_script = (ROOT / 'reader.js').read_text(encoding='utf-8').replace('export function ', 'function ')
    reader_script += (
        "\ndocument.querySelectorAll('[data-book-motion]').forEach(mountBookMotion);"
        "\ndocument.querySelectorAll('[data-book-lab]').forEach(mountBookLab);"
        "\nmountCalmReader(document);"
    )
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BMS 实战：从一颗电芯到一套证据链</title>
<style>{CSS}{VISUAL_CSS}</style>
</head>
<body>
<a class="skip-link" href="#contents">跳到目录</a>
<header class="cover">
  <p class="cover-eyebrow">BMS-Z 开源社区 · 教学用书</p>
  <div class="cover-rule" aria-hidden="true"></div>
  <h1>BMS 实战<br>从一颗电芯到一套证据链</h1>
  <p class="sub">参考 BMS-Z 开源教程、foxBMS、PyBaMM 与社区实践：把“为什么”讲到能复现，把“谁签字”写进流程。</p>
  <div class="cover-rule" aria-hidden="true"></div>
  <p class="meta">v{MANIFEST["version"]} · 2026-10 · 中文 · CC BY-SA 4.0（正文） / MIT（代码）</p>
</header>
<main>
{_front_matter_html()}
<section class="reader-map" aria-labelledby="reader-map-title">
  <p class="map-eyebrow">阅读路线</p>
  <h2 id="reader-map-title">带着一个问题开始读</h2>
  <p>选一条路线，留下框图、误差预算或回放记录。每读完一章，都能说明结论来自哪条证据。</p>
  <div class="route-grid">{route_cards}</div>
</section>
<details class="toc visual-index"><summary>从图解开始 · {len(visuals)} 个动画入口</summary><ul>{visual_links}</ul></details>
<nav class="toc" id="contents" aria-label="全书目录"><strong>目录</strong><ul>{''.join(toc)}</ul></nav>
{''.join(body_parts)}
</main>
<a class="back-to-toc" href="#contents" aria-label="返回全书目录">目录</a>
<script>{reader_script}</script>
</body>
</html>
"""
    out = DIST / "bms-book.html"
    out.write_text(doc, encoding="utf-8")
    print(f"built {out} ({out.stat().st_size} bytes, {index} chapters)")

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


# 章/附录/前言在大纲中的标题形态（get_toc 的 1 基页码）。
_CHAPTER_OUTLINE_RE = re.compile(r"^(第 \d+ 章|附录 [A-E]|前言|索引)")
# Chrome 生成大纲时可能在中文标题里插入零宽字符（CI 的 Linux 侧实测尾随 U+200B）：
# 放进页眉既画不出来也提不出来，先剥掉，页眉与契约比较才用同一个字符串。
_INVISIBLE_RE = re.compile(r"[\u00ad\u200b-\u200f\u2028\u2029\u202a-\u202e\ufeff]")
_GRAY = (0.38, 0.42, 0.45)
_RULE = (0.72, 0.74, 0.76)
_FOOTER_SIZE = 8.0
_HEADER_SIZE = 7.5


def _clean_outline_title(title: str) -> str:
    """剥掉大纲标题里的零宽字符，返回可打印、可提取的纯标题。"""
    return _INVISIBLE_RE.sub("", title).strip()


def _pdf_sections(document) -> list[tuple[int, str]]:
    """各章起始页（0 基）与标题，供奇偶页眉使用。"""
    sections: list[tuple[int, str]] = []
    for level, title, page in document.get_toc():
        clean = _clean_outline_title(title)
        if level == 2 and _CHAPTER_OUTLINE_RE.match(clean):
            sections.append((page - 1, clean))
    return sections


def _toc_page_indices(document, first_section: int) -> list[int]:
    """目录页（0 基）：首个前向内链 ≥10 的页，及其后连续仍有前向内链的页。

    续页判据是「仍有前向内链」而不是「≥2 条」：目录最后一条（CI 的 Linux 侧排版把
    附录那一条单独挤出一页）只剩 1 条前向内链时，那一页照样要盖章——旧判据在这里
    断链，条目没有页码，契约门当场报红。上界钉在第一章开始之前：目录只可能位于
    正文之前，正文页里的单条跨页引用不会被误盖章。
    """
    pages: list[int] = []
    started = False
    for index in range(1, min(first_section, document.page_count)):
        forward = [
            link
            for link in document[index].get_links()
            if isinstance(link.get("page"), int) and link["page"] > index
        ]
        if not started:
            if len(forward) >= 10:
                started = True
                pages.append(index)
        elif forward:
            pages.append(index)
        else:
            break
    return pages


def _stamp_toc_page_refs(document, fitz, first_section: int) -> None:
    """在目录条目右侧盖目标页码（0 基，与页脚计数一致）。"""
    for index in _toc_page_indices(document, first_section):
        page = document[index]
        links = [
            link
            for link in page.get_links()
            if isinstance(link.get("page"), int) and link["page"] >= 1
        ]
        if not links:
            continue
        midpoint = page.rect.width / 2
        page_right = page.rect.width - 42
        left_column_right = midpoint - 18
        for link in links:
            rect = fitz.Rect(link["from"])
            label = str(link["page"])
            width = fitz.get_text_length(label, fontname="helv", fontsize=_FOOTER_SIZE)
            column_right = left_column_right if rect.x0 < midpoint else page_right
            page.insert_text(
                fitz.Point(column_right - width, rect.y1 - 2),
                label,
                fontname="helv",
                fontsize=_FOOTER_SIZE,
                color=_GRAY,
            )


def _outline_range(document, title_prefix: str) -> tuple[int, int] | None:
    """返回某个二级书签覆盖的 [start, end) 物理页范围（0 基）。"""
    sections = [
        (page - 1, _clean_outline_title(title))
        for level, title, page in document.get_toc()
        if level == 2 and page >= 1
    ]
    for pos, (start, title) in enumerate(sections):
        if title.startswith(title_prefix):
            end = sections[pos + 1][0] if pos + 1 < len(sections) else document.page_count
            return start, end
    return None


def _stamp_index_refs(document, fitz, terms: list[str]) -> dict[str, list[int]]:
    """在卷末索引右侧盖正文页码；术语表与索引自身不参与命中。"""
    index_range = _outline_range(document, "索引")
    if index_range is None:
        return {}
    index_start, _index_end = index_range
    glossary = _outline_range(document, "附录 C")
    refs_by_term = term_pages(
        document, terms, index_start, glossary or (index_start, index_start),
        floor=first_body_page(document),
    )
    for term, pages in refs_by_term.items():
        target = index_term_rect(document, index_start, term)
        if target is None or not pages:
            continue
        page_index, rect = target
        label = index_label(pages)
        page = document[page_index]
        width = fitz.get_text_length(label, fontname="helv", fontsize=_FOOTER_SIZE)
        page.insert_text(
            fitz.Point(page.rect.width - 42 - width, rect.y1 - 2),
            label,
            fontname="helv",
            fontsize=_FOOTER_SIZE,
            color=_GRAY,
        )
    return refs_by_term


def _stamp_pdf(output_pdf: Path, metadata: dict[str, str]) -> None:
    """除封面外逐页盖页脚页码，奇偶页眉（书名/章名）加细线，并写元数据。"""
    import fitz

    document = fitz.open(output_pdf)
    try:
        document.set_metadata({**document.metadata, **metadata})
        sections = _pdf_sections(document)
        section_starts = {start for start, _title in sections}
        dividers = {page - 1 for level, _title, page in document.get_toc() if level == 1 and page > 1}
        header_skip = section_starts | dividers
        total = max(0, document.page_count - 1)
        short_title = MANIFEST["title"].split("：", 1)[0]
        current_title: str | None = None
        next_section = 0

        for index in range(1, document.page_count):
            while next_section < len(sections) and sections[next_section][0] <= index:
                current_title = sections[next_section][1]
                next_section += 1

            page = document[index]
            label = f"{index} / {total}"
            width = fitz.get_text_length(label, fontname="helv", fontsize=_FOOTER_SIZE)
            page.insert_text(
                fitz.Point((page.rect.width - width) / 2, page.rect.height - 10),
                label,
                fontname="helv",
                fontsize=_FOOTER_SIZE,
                color=_GRAY,
            )

            if current_title is None or index in header_skip:
                continue
            if index % 2 == 0:  # 1 基偶数页（左页）：书名靠左
                header = short_title
                x = 42.0
            else:  # 1 基奇数页（右页）：章名靠右
                header = current_title
                x = page.rect.width - 42 - fitz.get_text_length(
                    header, fontname="china-s", fontsize=_HEADER_SIZE
                )
            page.insert_text(
                fitz.Point(x, 20), header, fontname="china-s", fontsize=_HEADER_SIZE, color=_GRAY
            )
            page.draw_line(
                fitz.Point(42, 27),
                fitz.Point(page.rect.width - 42, 27),
                color=_RULE,
                width=0.35,
            )

        _stamp_toc_page_refs(
            document, fitz, min(section_starts) if section_starts else document.page_count
        )
        _stamp_index_refs(document, fitz, INDEX_TERMS)
        stamped = output_pdf.with_suffix(".stamped.pdf")
        document.save(stamped, garbage=3, deflate=True)
    finally:
        document.close()
    stamped.replace(output_pdf)


# 末页内容低于正文区这一比例的章，视为「只拖了几行」的孤尾页，下一遍紧排；最多升到 _FIT_LEVELS 级。
_TAIL_FILL = 0.35
_FIT_LEVELS = 2


def _page_fill(page) -> float:
    """正文区（页高 6%–93%，避开页眉页脚带）内最低内容的位置占比。"""
    top, bottom = page.rect.height * 0.06, page.rect.height * 0.93
    ys = [b[3] for b in page.get_text("blocks") if b[1] > top and b[3] < bottom]
    ys += [d["rect"].y1 for d in page.get_drawings() if d["rect"].y0 > top and d["rect"].y1 < bottom]
    return (max(ys) - top) / (bottom - top) if ys else 0.0


def _short_tail_chapters(pdf_path: Path) -> frozenset[str]:
    """PDF 中末页孤尾的章号（与 data-chapter-no 同格式：两位数字或附录字母）。

    章的结束页取「下一章或下一篇扉页的起始页 − 1」：篇扉页（1 级书签）截断篇末章，
    章内二级书签（如附录 D 的来源登记表）不截断，登记表的尾页仍算附录 D 的末页。
    """
    import fitz

    with fitz.open(pdf_path) as document:
        sections = _pdf_sections(document)
        starts = sorted({start for start, _ in sections}
                        | {page - 1 for level, _, page in document.get_toc() if level == 1})
        tails: set[str] = set()
        for start, title in sections:
            match = re.match(r"第 (\d+) 章|附录 ([A-E])", title)
            end = next((s for s in starts if s > start), document.page_count)
            if match is None or end - start < 2:
                continue
            if _page_fill(document[end - 1]) < _TAIL_FILL:
                tails.add(f"{int(match.group(1)):02d}" if match.group(1) else match.group(2))
    return frozenset(tails)


def _print_pdf(browser: str, html_path: Path, out_pdf: Path) -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             "--generate-pdf-document-outline", f"--user-data-dir={profile}",
             f"--print-to-pdf={out_pdf}", html_path.resolve().as_uri()],
            check=True, capture_output=True, timeout=120)


def build_pdf(browser_override: str | None = None) -> None:
    """Chrome/Edge headless 打印带书签 PDF；二遍紧排孤尾章，再盖页眉页脚、目录页码与元数据。"""
    browser = browser_override or next((p for p in BROWSERS if Path(p).exists()), None)
    if browser is None:
        browser = next((shutil.which(p) for p in ("google-chrome", "chromium", "chromium-browser", "msedge") if shutil.which(p)), None)
    if browser is None:
        raise RuntimeError("PDF 构建需要 Chrome/Edge；可用 --browser 指定可执行文件")
    html_path, out_pdf = DIST / "bms-book.html", DIST / "bms-book.pdf"
    _print_pdf(browser, html_path, out_pdf)
    # 逐级紧排：每遍只把仍拖尾的章升一级，最多 _FIT_LEVELS 级；无孤尾即停。
    fit: dict[str, int] = {}
    for _ in range(_FIT_LEVELS):
        try:
            tails = _short_tail_chapters(out_pdf)
        except ImportError:
            break
        bump = sorted(no for no in tails if fit.get(no, 0) < _FIT_LEVELS)
        if not bump:
            break
        for no in bump:
            fit[no] = fit.get(no, 0) + 1
        print(f"fit   紧排 {len(bump)} 章：{' '.join(f'{no}→{fit[no]}' for no in bump)}")
        main(fit)
        _print_pdf(browser, html_path, out_pdf)
    try:
        _stamp_pdf(out_pdf, {
            "title": MANIFEST["title"],
            "author": MANIFEST.get("author", ""),
            "subject": MANIFEST.get("subtitle", ""),
            "keywords": MANIFEST.get("keywords", ""),
            "creator": "bms-book/build_html.py",
            "producer": "Chromium headless + PyMuPDF",
        })
    except ImportError:
        print(f"pdf   {out_pdf} ({out_pdf.stat().st_size} bytes, outline; 未装 pymupdf，跳过页眉页脚与元数据)")
        return
    print(f"pdf   {out_pdf} ({out_pdf.stat().st_size} bytes, outline + 页眉页脚 + 目录页码 + 元数据)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", action="store_true", help="额外生成 PDF")
    parser.add_argument("--out-dir", type=Path, default=DIST, help="构建输出目录")
    parser.add_argument("--browser", help="Chrome/Edge 可执行文件")
    options = parser.parse_args()
    DIST = options.out_dir.resolve()
    main()
    if options.pdf:
        build_pdf(options.browser)
