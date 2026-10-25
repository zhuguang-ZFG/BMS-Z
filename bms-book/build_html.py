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
        '<p class="chapter-compass__eyebrow">CHAPTER COMPASS · 先定问题，再读证据</p>'
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
        '<p class="source-anchors__eyebrow">SOURCE ANCHORS · 本章证据来源'
        f'（访问 {html.escape(ACCESS_DATE)} · <a href="#ch-38-sources">全表见附录 D 来源登记表</a>）</p>'
        f"<ul>{''.join(items)}</ul></aside>"
    )


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


CSS = """
:root {
  --ink:#0f172a; --muted:#475569; --border:#d8dee9; --paper:#ffffff;
  --accent:#0f766e; --soft:#f1f5f9; --surface:#f8fafc;
  --sans:"Noto Sans SC","MiSans","HarmonyOS Sans SC","Microsoft YaHei",system-ui,sans-serif;
  --serif:"Noto Serif SC","Source Han Serif SC",Georgia,serif;
}
* { box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
body { margin:0 auto; max-width:920px; padding:44px 26px 96px;
       font-family:var(--serif); color:var(--ink); line-height:1.82; font-size:16px;
       background:var(--paper); text-rendering:optimizeLegibility;
       text-spacing-trim:trim-start; text-autospace:normal; }
body { overflow-wrap:anywhere; }
h2 { font-size:2rem; margin:2.6rem 0 1rem; padding-bottom:.45rem;
     border-bottom:2px solid var(--accent); color:var(--accent); }
h3 { font-size:1.4rem; margin:2rem 0 .7rem; color:#111827; }
h4 { font-size:1.15rem; margin:1.5rem 0 .5rem; color:#1f2937; }
h1, h2, h3, h4 { break-after:avoid; page-break-after:avoid; }
p, li { text-align:justify; orphans:3; widows:3; }
p { margin:.75rem 0; }
ul, ol { padding-left:1.4rem; }
code { font-family:"JetBrains Mono",Consolas,monospace; font-size:.9em;
       background:#eef2f7; padding:.1em .35em; border-radius:4px; }
pre { background:#0f172a; color:#e2e8f0; padding:1rem 1.1rem; overflow:auto;
      border-radius:10px; border:1px solid #1e293b; line-height:1.55;
      text-spacing-trim:normal; text-autospace:no-autospace; }
pre code { background:none; color:inherit; padding:0; }
.vp-adaptive-theme > button.copy, .vp-adaptive-theme > span.lang { display:none; }
table { border-collapse:collapse; width:100%; margin:1.25rem 0;
        font-size:.92em; border-top:2px solid var(--ink); border-bottom:2px solid var(--ink);
        break-inside:avoid; }
th, td { padding:.55rem .7rem; vertical-align:top; }
thead th { border-bottom:1.5px solid var(--ink); background:transparent;
           text-align:left; font-family:var(--sans); font-weight:700; }
tbody tr + tr td, tbody tr + tr th { border-top:1px solid var(--border); }
blockquote { margin:1rem 0; padding:.6rem 1rem; color:var(--muted);
             border-left:4px solid var(--border); background:#f8fafc; }
a { color:#1d4ed8; text-decoration:none; }
a:hover { text-decoration:underline; }
mark { background:#fef08a; padding:0 .15em; border-radius:3px; }
figure { margin:1.7rem 0; padding:.9rem; border:1px solid var(--border);
         border-radius:14px; background:var(--paper);
         box-shadow:0 1px 3px rgba(15,23,42,.07),0 5px 16px rgba(15,23,42,.05);
         break-inside:avoid; }
figure img { width:100%; height:auto; border-radius:9px; display:block; }
figcaption { margin-top:.6rem; padding-top:.6rem; border-top:1px solid var(--border);
             color:var(--muted); font-size:.88em; text-align:center; }

.chapter { break-before:page; page-break-before:always;
           border-top:7px solid var(--accent); padding-top:1.1rem; position:relative; }
.chapter-ribbon { display:flex; align-items:center; gap:.65rem; margin-bottom:.3rem;
                  color:var(--muted); font:700 .75rem/1 var(--sans);
                  letter-spacing:.12em; text-transform:uppercase; }
.chapter-ribbon::before { content:""; width:2.4rem; height:3px; background:var(--accent);
                          border-radius:99px; }
.chapter > h2:first-of-type { margin-top:.75rem; font-size:2.15rem; line-height:1.35;
                              letter-spacing:-.02em; }
.chapter-meta { display:flex; flex-wrap:wrap; gap:.45rem; margin:.65rem 0 1.5rem;
                color:var(--muted); font:.78rem/1.4 var(--sans); }
.chapter-stat { display:inline-flex; align-items:baseline; gap:.28rem; padding:.28rem .58rem;
                border:1px solid var(--border); border-radius:999px; background:var(--surface); }
.chapter-stat strong { color:var(--accent); font-size:.92rem; }
.chapter-nav { display:flex; justify-content:space-between; gap:1rem; margin:2rem 0;
               padding:1rem 0; border-top:1px solid var(--border); font:.85rem/1.6 var(--sans); }
.chapter-nav a { max-width:45%; }
.chapter-nav a:last-child { text-align:right; }
.chapter[data-part="p1"] { --accent:#0f766e; }
.chapter[data-part="p2"] { --accent:#be123c; }
.chapter[data-part="p3"] { --accent:#1d4ed8; }
.chapter[data-part="p4"] { --accent:#6d28d9; }
.chapter[data-part="p5"] { --accent:#b45309; }
.chapter[data-part="p6"] { --accent:#0891b2; }
.chapter[data-part="p7"] { --accent:#15803d; }
.chapter[data-part="p8"] { --accent:#475569; }

.part-divider { break-before:page; page-break-before:always;
                min-height:70vh; display:flex; flex-direction:column; justify-content:center;
                padding:2.4rem; border-radius:18px; color:#fff; position:relative; overflow:hidden;
                background:linear-gradient(135deg,#0f172a 0%,#1e293b 60%,#334155 100%); }
.part-divider::after { content:""; position:absolute; width:280px; height:280px; right:-90px;
                       bottom:-110px; border:1px solid rgba(255,255,255,.2); border-radius:50%;
                       box-shadow:0 0 0 38px rgba(255,255,255,.045),0 0 0 76px rgba(255,255,255,.025); }
.part-divider .part-no { font:700 .78rem/1 var(--sans); letter-spacing:.22em;
                         color:#bae6fd; margin-bottom:1rem; }
.part-divider h1 { font-size:2.1rem; margin:0 0 .6rem; color:#fff; border:none; }
.part-divider p { color:#cbd5e1; font-size:1rem; margin:.15rem 0; max-width:620px; }
.part-divider .part-meta { margin-top:1.4rem; padding-top:1rem;
                           border-top:1px solid rgba(255,255,255,.2);
                           color:#e2e8f0; font:500 .86rem/1.6 var(--sans); }
.part-divider[data-part="p2"] { background:linear-gradient(135deg,#4c0519,#9f1239 70%,#be123c); }
.part-divider[data-part="p3"] { background:linear-gradient(135deg,#172554,#1e3a8a 70%,#1d4ed8); }
.part-divider[data-part="p4"] { background:linear-gradient(135deg,#2e1065,#5b21b6 70%,#6d28d9); }
.part-divider[data-part="p5"] { background:linear-gradient(135deg,#451a03,#92400e 70%,#b45309); }
.part-divider[data-part="p7"] { background:linear-gradient(135deg,#052e16,#15803d 70%,#16a34a); }
.part-divider[data-part="p8"] { background:linear-gradient(135deg,#1e293b,#475569); }
.part-divider[data-part="p6"] { background:linear-gradient(135deg,#164e63,#0e7490 70%,#0891b2); }
.part-divider[data-part="p1"] { background:linear-gradient(135deg,#042f2e,#0f766e 70%,#0d9488); }

.callout { margin:1.2rem 0; padding:.9rem 1.1rem .75rem; border:1px solid var(--border);
           border-top:3px solid var(--c); border-radius:10px;
           background:var(--bg); break-inside:avoid; }
.callout .callout-title { font-weight:800; color:var(--c); margin-bottom:.3rem;
                          font-family:"Noto Sans SC","Microsoft YaHei",sans-serif;
                          font-size:.8rem; letter-spacing:.08em; }
.callout p:last-child { margin-bottom:0; }
.callout.story { --c:#b45309; --bg:#fffbeb; }
.callout.principle { --c:#1d4ed8; --bg:#eff6ff; }
.callout.trap { --c:#be123c; --bg:#fff1f2; }
.callout.lab { --c:#047857; --bg:#ecfdf5; }

.toc { background:var(--surface); border:1px solid var(--border); border-radius:16px;
       padding:1.3rem 1.5rem; margin:2rem 0; }
.toc > strong { display:block; margin-bottom:.7rem; font:800 1.05rem/1 var(--sans);
                letter-spacing:.08em; color:var(--ink); }
.toc ul { margin:.25rem 0; padding-left:0; list-style:none; columns:2; column-gap:2rem; }
.toc li { margin:.13rem 0; break-inside:avoid; }
.toc { font-size:.92em; }
.toc .toc-part { list-style:none; margin:.55rem 0 .15rem; font-weight:700;
                 color:#0f172a; font-family:var(--sans); column-span:all; }
.toc a { color:#1f2937; }

.cover { min-height:92vh; display:flex; flex-direction:column; justify-content:center;
         padding:3.4rem 2.4rem; margin:-44px -26px 0; color:#e2e8f0; position:relative; overflow:hidden;
         background:radial-gradient(circle at 80% 10%,#1e3a8a 0%,transparent 45%),
                    radial-gradient(circle at 10% 90%,#0f766e 0%,transparent 40%),
                    linear-gradient(160deg,#020617,#0f172a 70%); }
.cover::after { content:""; position:absolute; inset:0; opacity:.15; pointer-events:none;
                background-image:linear-gradient(rgba(148,163,184,.35) 1px,transparent 1px),
                                 linear-gradient(90deg,rgba(148,163,184,.35) 1px,transparent 1px);
                background-size:42px 42px; mask-image:linear-gradient(to left,#000,transparent 72%); }
.cover > * { position:relative; z-index:1; }
.cover .eyebrow { color:#7dd3fc; letter-spacing:.2em; font-size:.85rem; }
.cover h1 { border:none; color:#fff; font-size:3.15rem; line-height:1.16; margin:.7rem 0 1rem;
            letter-spacing:-.035em; }
.cover .sub { color:#cbd5e1; font-size:1.1rem; max-width:640px; }
.cover .chips { margin-top:1.6rem; display:flex; flex-wrap:wrap; gap:.5rem; }
.cover .chip { border:1px solid #334155; background:#0b1220; color:#93c5fd;
               padding:.3rem .7rem; border-radius:999px; font-size:.82rem; }
.cover .meta { margin-top:2rem; color:#94a3b8; font-size:.9rem; }

.reader-map { margin:2rem 0; padding:1.5rem; border:1px solid var(--border);
              border-radius:18px; background:linear-gradient(145deg,var(--surface),var(--paper)); }
.source-anchors { margin:1.8rem 0 0; padding:1rem 1.2rem 1.15rem; border:1px solid var(--border);
  border-left:4px solid var(--accent); border-radius:12px; background:var(--surface);
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
.route-card { display:block; padding:1rem; border:1px solid var(--border); border-radius:12px;
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
mjx-container { display:inline-block; max-width:100%; overflow-x:auto; overflow-y:hidden;
                vertical-align:middle; }
mjx-container[display="true"] { display:block; }
@media (max-width:600px) {
  body { padding:20px 16px 80px; }
  .cover { margin:-20px -16px 0; padding:2rem 1rem; min-height:75vh; }
  .cover h1 { font-size:2rem; }
  .part-divider { min-height:35vh; padding:1.2rem; }
  h2 { font-size:1.6rem; }
  table { display:block; overflow-x:auto; }
  p, li { text-align:left; }
  .toc ul { columns:1; }
  .route-grid { grid-template-columns:1fr; }
  .back-to-toc { right:.65rem; bottom:.65rem; width:2.75rem; height:2.75rem; }
}
@media (prefers-color-scheme:dark) {
  :root { --ink:#e2e8f0; --muted:#a8b4c5; --border:#475569; --paper:#0f172a;
          --surface:#172033; --accent:#5eead4; }
  h3, h4, .toc .toc-part, .toc a { color:var(--ink); }
  a { color:#93c5fd; }
  code, .toc { background:#1e293b; }
  blockquote { background:#172033; }
  .callout { background:#172033; }
  .callout.story { --c:#fbbf24; }
  .callout.principle { --c:#93c5fd; }
  .callout.trap { --c:#fda4af; }
  .callout.lab { --c:#6ee7b7; }
  .chapter[data-part="p1"] { --accent:#5eead4; }
  .chapter[data-part="p2"] { --accent:#fda4af; }
  .chapter[data-part="p3"] { --accent:#93c5fd; }
  .chapter[data-part="p4"] { --accent:#c4b5fd; }
  .chapter[data-part="p5"] { --accent:#fcd34d; }
  .chapter[data-part="p6"] { --accent:#67e8f9; }
  .chapter[data-part="p7"] { --accent:#86efac; }
  .chapter[data-part="p8"] { --accent:#cbd5e1; }
}
@media print {
  :root { --ink:#0f172a; --muted:#475569; --border:#d8dee9; --paper:#ffffff;
          --surface:#f8fafc; --accent:#0f766e; }
  .back-to-toc, .skip-link, .chapter-nav { display:none; }
  figure { box-shadow:none; }
  code, .toc { background:#eef2f7; }
  h3, h4, .toc a, .toc .toc-part { color:#0f172a; }
  blockquote { background:#f8fafc; }
  .callout { background:#f1f5f9; }
  @page { size:A4; margin:17mm 16mm; }
  body { max-width:none; padding:0; font-size:11pt; line-height:1.72; }
  .cover { min-height:245mm; margin:0; padding:2.5rem 1.5rem; page-break-after:always; }
  .part-divider { min-height:243mm; padding:2.4rem; border-radius:0; }
  .reader-map { break-after:page; page-break-after:always; }
  .route-card { box-shadow:none; }
  pre { white-space:pre-wrap; overflow:visible; overflow-wrap:anywhere; }
  thead { display:table-header-group; }
  tr { break-inside:avoid; page-break-inside:avoid; }
  a { color:var(--ink); }
  .chapter[data-part="p1"] { --accent:#0f766e; }
  .chapter[data-part="p2"] { --accent:#be123c; }
  .chapter[data-part="p3"] { --accent:#1d4ed8; }
  .chapter[data-part="p4"] { --accent:#6d28d9; }
  .chapter[data-part="p5"] { --accent:#b45309; }
  .chapter[data-part="p6"] { --accent:#0e7490; }
  .chapter[data-part="p7"] { --accent:#15803d; }
  .chapter[data-part="p8"] { --accent:#475569; }
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
.book-lab { margin:1.8rem 0; padding:1.4rem; border:1px solid var(--border); border-top:4px solid var(--accent);
  border-radius:14px; background:var(--surface); break-inside:avoid; }
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
.chapter-compass { margin:1.15rem 0 1.8rem; padding:1.1rem 1.2rem 1.2rem;
  border:1px solid var(--border); border-top:4px solid var(--accent); border-radius:14px;
  background:var(--surface); break-inside:avoid; }
.chapter-compass__eyebrow { margin:0 0 .85rem; color:var(--accent);
  font:800 .7rem/1.3 var(--sans); letter-spacing:.13em; }
.chapter-compass dl { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin:0; }
.chapter-compass dl > div { min-width:0; padding:0 1rem; border-left:1px solid var(--border); }
.chapter-compass dl > div:first-child { padding-left:0; border-left:0; }
.chapter-compass dl > div:last-child { padding-right:0; }
.chapter-compass dt { margin:0 0 .35rem; color:var(--accent); font:700 .78rem/1.4 var(--sans); }
.chapter-compass dd { margin:0; color:var(--ink); font-size:.88rem; line-height:1.7; text-align:left; }
.book-lab:focus-within { border-color:var(--accent); }
figure figcaption { text-align:left; }
figure .visual-guide, figure .visual-question { margin:.65rem 0; }
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
  border-top:4px solid var(--accent); border-radius:14px; background:var(--surface); break-inside:avoid; }
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

def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    renderer = shutil.which("node")
    if renderer is None:
        raise RuntimeError("HTML 构建需要 Node.js 24+；请先在仓库根运行 npm ci")
    rendered = subprocess.run(
        [renderer, str(ROOT / "render.mjs")], check=True, capture_output=True,
        encoding="utf-8", timeout=120,
    )
    chapters = json.loads(rendered.stdout)
    toc, combined, body_parts = [], [], []
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
            f'<section class="part-divider" data-part="{part_id}">'
            f'<div class="part-no">{html.escape(part_title)} · BMS IN PRACTICE</div>'
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
            stats = [
                (chapter_body.count('<h3'), "小节"),
                (chapter_body.count('<figure'), "图解"),
                (chapter_body.count('class="callout '), "提示卡"),
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
            chapter_body += chapter_source_anchors(name)
            if name == "附录D-参考资料.md":
                chapter_body += source_registry_html()
            chapter_body += f'<nav class="chapter-nav" aria-label="章节翻页">{previous_link}{following_link}</nav>'
            body_parts.append(
                f'<section class="chapter" data-part="{part_id}" aria-labelledby="{chapter["prefix"]}">'
                f'<div class="chapter-ribbon">{html.escape(part_title)} / {html.escape(part_desc)}</div>'
                f'{chapter_body}</section>'
            )
    (DIST / "bms-book.md").write_text("\n\n---\n\n".join(combined), encoding="utf-8")

    visuals = json.loads((ROOT / 'visuals.json').read_text(encoding='utf-8'))
    visual_links = ''.join(
        f'<li><a href="#{chapter_links[next(name for name in chapter_links if name.startswith(v["chapter"] + "-"))]}">'
        f'第 {int(v["chapter"])} 章 · {html.escape(v["caption"].split("：")[0].split("。")[0])}</a></li>'
        for v in visuals
    )

    reader_script = (ROOT / 'reader.js').read_text(encoding='utf-8').replace('export function ', 'function ')
    reader_script += "\ndocument.querySelectorAll('[data-book-motion]').forEach(mountBookMotion);\ndocument.querySelectorAll('[data-book-lab]').forEach(mountBookLab);"
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
  <div class="eyebrow">BMS IN PRACTICE · v{MANIFEST["version"]}</div>
  <h1>BMS 实战<br>从一颗电芯到一套证据链</h1>
  <p class="sub">参考 BMS-Z 开源教程、foxBMS、PyBaMM 与社区实践：把“为什么”讲到能复现，把“谁签字”写进流程。</p>
  <div class="chips">
    <span class="chip">BMS-Z 实验数据</span>
    <span class="chip">{sum(chapter['body'].count('<figure') for chapter in chapters)} 个图解</span>
    <span class="chip">{len(visuals)} 个动画</span>
    <span class="chip">{sum(chapter['body'].count('data-book-lab=') for chapter in chapters)} 个交互实验</span>
    <span class="chip">{len(MANIFEST['demos'])} 份可跑代码</span>
    <span class="chip">无真值诊断</span>
    <span class="chip">证据链</span>
    <span class="chip">UDS 诊断</span>
    <span class="chip">高压安全</span>
  </div>
  <p class="meta">2026-10 · 中文 · CC BY-SA 4.0（正文） / MIT（代码）</p>
</header>
<main>
<section class="reader-map" aria-labelledby="reader-map-title">
  <p class="map-eyebrow">READING PATHS</p>
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
_CHAPTER_OUTLINE_RE = re.compile(r"^(第 \d+ 章|附录 [A-E]|前言)")
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
        stamped = output_pdf.with_suffix(".stamped.pdf")
        document.save(stamped, garbage=3, deflate=True)
    finally:
        document.close()
    stamped.replace(output_pdf)


def build_pdf(browser_override: str | None = None) -> None:
    """Chrome/Edge headless 打印带书签 PDF；再盖页眉页脚、目录页码与元数据。"""
    browser = browser_override or next((p for p in BROWSERS if Path(p).exists()), None)
    if browser is None:
        browser = next((shutil.which(p) for p in ("google-chrome", "chromium", "chromium-browser", "msedge") if shutil.which(p)), None)
    if browser is None:
        raise RuntimeError("PDF 构建需要 Chrome/Edge；可用 --browser 指定可执行文件")
    html_path, out_pdf = DIST / "bms-book.html", DIST / "bms-book.pdf"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             "--generate-pdf-document-outline", f"--user-data-dir={profile}",
             f"--print-to-pdf={out_pdf}", html_path.resolve().as_uri()],
            check=True, capture_output=True, timeout=120)
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
