#!/usr/bin/env python3
"""Assemble the engineering deep-dive product (P2.6) from the registries only.

The builder never reads docs/.vitepress/site-dist or any built artifact: unit
manuscripts, claims, figures and experiments come from the four registries in
bms-book/, Markdown rendering is delegated to bms-book/engineering/render.mjs
(the site's own createMarkdownRenderer, math included). Reading levels (P2.3)
become data-level attributes; the level toggle is a render-time filter, so
closing a shallow level never deletes technical text.

Output: <out>/index.html, <out>/<unit>.html, copied figure assets and a
deterministic build-report.json (content hashes, no timestamps).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINEERING = ROOT / 'bms-book/engineering'
MANIFEST = ROOT / 'bms-book/engineering-manifest.json'
CLAIMS = ROOT / 'bms-book/engineering-claims.json'
FIGURES = ROOT / 'bms-book/engineering-figures.json'
EXPERIMENTS = ROOT / 'bms-book/engineering-experiments.json'
RENDERER = ENGINEERING / 'render.mjs'
LEVELS = ['intro', 'core', 'derivation', 'lab', 'research']

PAGE_CSS = """
:root { --ink: #22303c; --paper: #f7f3ea; --accent: #1f4e79; --line: #d8d2c4; }
* { box-sizing: border-box; }
body { margin: 0 auto; max-width: 880px; padding: 24px 20px 64px; color: var(--ink);
  background: var(--paper); font: 16px/1.75 -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; }
h1 { font-size: 1.6rem; border-bottom: 2px solid var(--accent); padding-bottom: .3em; }
h2 { margin-top: 2.2em; font-size: 1.25rem; }
h3 { font-size: 1.05rem; }
code, pre { background: #efe9db; border-radius: 4px; }
code { padding: .1em .35em; }
pre { padding: .8em 1em; overflow-x: auto; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: .95rem; }
th, td { border: 1px solid var(--line); padding: .35em .6em; text-align: left; }
img { max-width: 100%; height: auto; }
figure { margin: 1.2em 0; }
figcaption { font-size: .85rem; color: #5a6a76; margin-top: .4em; }
a { color: var(--accent); }
.callout, .chapter-route { border: 1px solid var(--line); border-left: 4px solid var(--accent);
  background: #fbf8f1; padding: .6em 1em; margin: 1em 0; border-radius: 4px; }
.callout-title, .chapter-route__eyebrow { font-weight: 600; margin-bottom: .3em; }
.chapter-route ol { margin: .3em 0 0; padding-left: 1.3em; }
.level-bar { position: sticky; top: 0; background: var(--paper); border-bottom: 1px solid var(--line);
  padding: .5em 0; margin-bottom: 1em; display: flex; gap: .5em; align-items: center; flex-wrap: wrap; z-index: 5; }
.level-bar button { border: 1px solid var(--line); background: #fff; border-radius: 4px;
  padding: .25em .8em; cursor: pointer; font-size: .9rem; }
.level-bar button[aria-pressed="true"] { background: var(--accent); color: #fff; border-color: var(--accent); }
.level-note { font-size: .8rem; color: #5a6a76; }
nav.toc { margin: 1em 0 2em; padding: 1em; border: 1px solid var(--line); border-radius: 6px; background: #fbf8f1; }
.unit-card { border: 1px solid var(--line); border-radius: 6px; padding: 1em 1.2em; margin: 1em 0; background: #fff; }
.unit-card h2 { margin: 0 0 .3em; border: none; }
.badge { display: inline-block; border: 1px solid var(--line); border-radius: 999px;
  padding: .05em .6em; font-size: .78rem; margin-right: .35em; color: #445; }
footer { margin-top: 3em; font-size: .8rem; color: #5a6a76; border-top: 1px solid var(--line); padding-top: 1em; }
"""

LEVEL_JS = """
(function () {
  var RANK = { intro: 0, core: 1, derivation: 2, lab: 3, research: 4 };
  var main = document.querySelector('main');
  if (!main) return;
  var items = [];
  var current = 'intro';
  for (var node of main.childNodes) {
    var tag = node.nodeType === 1 ? node.tagName : '';
    if (tag === 'H2') { current = node.getAttribute('data-level') || 'core'; }
    items.push([node, current]);
  }
  var bar = document.querySelector('.level-bar');
  function apply(level) {
    var max = RANK[level];
    for (var pair of Array.from(items)) {
      var el = pair[0];
      if (el.nodeType !== 1) continue;
      var rank = RANK[pair[1]];
      if (rank === undefined) continue;
      if (rank > max && tag !== 'H1') el.hidden = true; else el.hidden = false;
    }
    for (var btn of bar.querySelectorAll('button')) {
      btn.setAttribute('aria-pressed', String(btn.dataset.level === level));
    }
    try { localStorage.setItem('engineering-level', level); } catch (e) {}
  }
  bar.addEventListener('click', function (event) {
    var level = event.target && event.target.dataset && event.target.dataset.level;
    if (level) apply(level);
  });
  var saved = null;
  try { saved = localStorage.getItem('engineering-level'); } catch (e) {}
  apply(saved || 'lab');
})();
"""


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f'工程装配：{path.name} 读不到或解析不了：{exc}') from exc


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def section_levels(unit: dict, claims: list[dict], experiments: list[dict]) -> dict:
    """Map heading anchor -> reading level for one unit."""
    derivation = {c['anchor'] for c in claims if c.get('unit') == unit['id']}
    lab: set[str] = set()
    for exp in experiments:
        if exp.get('unit') != unit['id']:
            continue
        for key in ('student_tasks_anchor', 'rejects_anchor', 'frozen_anchor'):
            lab.add(exp[key])
    return {anchor: 'derivation' for anchor in derivation} | {anchor: 'lab' for anchor in lab}


def anchor_token(text: str) -> str:
    parts = text.split()
    return parts[0] if parts else text


def tag_levels(html: str, levels: dict[str, str]) -> str:
    """Add data-level to every h2 whose heading token/full text is registered."""
    def repl(match: re.Match) -> str:
        attrs, text = match.group(1), match.group(2)
        plain = re.sub(r'<[^>]+>', '', text).strip()
        level = levels.get(anchor_token(plain)) or levels.get(plain)
        if level and 'data-level' not in attrs:
            return f'<h2{attrs} data-level="{level}">{text}</h2>'
        return match.group(0)
    return re.sub(r'<h2([^>]*)>([\s\S]*?)</h2>', repl, html)


def page_html(title: str, body: str, level_bar: bool) -> str:
    bar = ''
    if level_bar:
        buttons = ''.join(
            f'<button type="button" data-level="{level}">{label}</button>'
            for level, label in [('intro', '导读'), ('core', '核心'), ('derivation', '推导'),
                                 ('lab', '动手'), ('research', '研究')])
        bar = (f'<div class="level-bar" role="group" aria-label="阅读层级">{buttons}'
               '<span class="level-note">层级只过滤显示，正文始终完整（含折叠答案与来源）</span></div>')
    script = f'<script>{LEVEL_JS}</script>' if level_bar else ''
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · BMS 工程深研</title>
<style>{PAGE_CSS}</style>
</head>
<body>
{bar}
<main>
{body}
</main>
{script}
</body>
</html>
'''


def verify_spine(index_html: str, out: Path) -> None:
    """坏 spine 负例：目录页 href 必须逐一到得了真实页面，断导航不许出厂。"""
    for href in re.findall(r'href="([^"#]+)\.html', index_html):
        target = out / f'{href}.html'
        if not target.is_file():
            raise SystemExit(f'工程装配：坏 spine——目录页指向 {href}.html，但文件不存在')


def verify_publication(out: Path) -> None:
    """P2.7 出版门（HTML 侧）：断链、外链资源、数学、折叠答案、来源摘要。

    外链 URL 只允许出现在 <a href>（内容链接可离线点开）；字体、脚本、图片、
    样式必须本地自带，断网阅读不破版。build-report.json 的来源指纹必须与
    当前正文源一致——登记漂移不许混进出版产物。
    """
    problems: list[str] = []
    pages = sorted(out.glob('*.html'))
    if len(pages) < 2:
        raise SystemExit(f'工程装配：出版门——产物页数不足：{out}')
    for page in pages:
        text = page.read_text(encoding='utf-8')
        for attr, url in re.findall(r'(href|src)="([^"]+)"', text):
            if url.startswith(('http://', 'https://')):
                if attr == 'src' or (attr == 'href' and re.search(r'<link[^>]+href="' + re.escape(url), text)):
                    problems.append(f'{page.name}: 外链资源 {url} 必须本地自带（断网不破版）')
                continue
            if url.startswith(('#', 'mailto:', 'data:')):
                continue
            bare = url.split('#')[0]
            target = (page.parent / bare).resolve()
            if bare.endswith('/'):
                if not target.is_dir():
                    problems.append(f'{page.name}: 断链目录 {url}')
            elif not target.is_file():
                problems.append(f'{page.name}: 断链 {url}')
        if re.search(r'<script[^>]+src="https?://|<link[^>]+href="https?://', text):
            problems.append(f'{page.name}: 脚本/样式不得走 CDN')
    units_html = {p.stem.upper(): p for p in pages if p.stem.upper().startswith('S')}
    s2 = units_html.get('S2')
    if s2 and 'mjx' not in s2.read_text(encoding='utf-8'):
        problems.append('S2: 数学式未离线渲染（缺 MathJax SVG）')
    for stem, page in units_html.items():
        text = page.read_text(encoding='utf-8')
        if '答案' not in text:
            problems.append(f'{stem}: 缺折叠/Inline 答案区')
        source = ENGINEERING / f'{stem}-精度够了保护为什么反而慢了.md'
        if not source.is_file():
            source = next((m for m in ENGINEERING.glob(f'{stem}-*.md') if '先修' not in m.name), None)
        if source and '<details' in source.read_text(encoding='utf-8') and '<details' not in text:
            problems.append(f'{stem}: 源稿有折叠答案，产物未保留 <details>')
    report_path = out / 'build-report.json'
    if not report_path.is_file():
        problems.append('缺 build-report.json（来源摘要）')
    else:
        report = json.loads(report_path.read_text(encoding='utf-8'))
        for uid, info in report.get('units', {}).items():
            source = ROOT / info['source']
            if source.is_file() and sha256_file(source) != info['source_sha256']:
                problems.append(f'{uid}: 出版产物的来源指纹与当前正文源不一致，须重建')
    if problems:
        raise SystemExit('工程装配：出版门不过——\n- ' + '\n- '.join(problems))


def find_browser() -> str:
    candidates = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        shutil.which('google-chrome'), shutil.which('chromium'), shutil.which('msedge'),
    ]
    browser = next((p for p in candidates if p and Path(p).exists()), None)
    if not browser:
        raise SystemExit('工程装配：PDF 需要 Chrome/Edge（--pdf 可跳过）')
    return browser


def print_pdfs(out: Path) -> list[str]:
    """把产物页打印成 PDF（无头 Chromium，展开折叠答案后打印）。"""
    import tempfile
    browser = find_browser()
    pdf_dir = out / 'pdf'
    pdf_dir.mkdir(parents=True, exist_ok=True)
    printed = []
    for page in sorted(out.glob('*.html')):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
            print_source = Path(profile) / f'{page.stem}-print.html'
            print_source.write_text(
                re.sub(r'<details\b(?![^>]*\bopen)([^>]*)>', r'<details open\1>',
                       page.read_text(encoding='utf-8')),
                encoding='utf-8')
            target = pdf_dir / f'{page.stem}.pdf'
            subprocess.run(
                [browser, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                 '--generate-pdf-document-outline', f'--user-data-dir={profile}',
                 f'--print-to-pdf={target.resolve()}', print_source.resolve().as_uri()],
                capture_output=True, check=True, timeout=180)
        try:
            import fitz
        except ImportError:
            printed.append(target.name)
            continue
        with fitz.open(target) as document:
            document.set_metadata({'title': f'{page.stem} · BMS 工程深研（样章）',
                                   'creator': 'tools/build_engineering.py --pdf'})
            document.saveIncr()
            parts: list[str] = []
            for pdf_page in document:
                parts.append(str(pdf_page.get_text()))
            text = ''.join(parts)
            if page.stem.upper().startswith('S') and page.stem.upper() not in text:
                raise SystemExit(f'工程装配：PDF {target.name} 缺单元编号文本，打印失败')
        printed.append(target.name)
    return printed


def build(out: Path) -> dict:
    manifest = read_json(MANIFEST)
    claims = read_json(CLAIMS)['claims']
    figures = read_json(FIGURES)['figures']
    experiments = read_json(EXPERIMENTS)['experiments']
    units = [u for u in manifest['units'] if u.get('kind') == 'sample' and u.get('status') == 'locally_verified']
    if not units:
        raise SystemExit('工程装配：登记里没有可装配的样章单元')

    for unit in units:
        source = ROOT / unit['source']
        if not source.is_file():
            raise SystemExit(f"工程装配：{unit['id']} 正文源缺失 {unit['source']}（先回写登记表）")

    node = shutil.which('node')
    if node is None:
        raise SystemExit('工程装配需要 Node.js（渲染走 VitePress 解析器）')
    rendered = subprocess.run(
        [node, str(RENDERER)], check=True, capture_output=True, encoding='utf-8', timeout=180,
    )
    try:
        fragments = {u['id']: u for u in json.loads(rendered.stdout)['units']}
    except (KeyError, json.JSONDecodeError) as exc:
        detail = rendered.stderr.strip() or rendered.stdout[:400]
        raise SystemExit(f'工程装配：渲染器输出解析失败：{exc}；渲染器说：{detail}') from exc

    out.mkdir(parents=True, exist_ok=True)
    report: dict = {'units': {}, 'figures_copied': []}

    # 样章页面
    for unit in units:
        fragment = fragments[unit['id']]
        levels = section_levels(unit, claims, experiments)
        body = tag_levels(fragment['html'], levels)
        title = f"{unit['id']}　{unit['title']}"
        page = page_html(title, body, level_bar=True)
        (out / f"{unit['id'].lower()}.html").write_text(page, encoding='utf-8')
        src = ROOT / unit['source']
        report['units'][unit['id']] = {
            'title': unit['title'], 'levels': unit.get('levels', []),
            'source': unit['source'], 'source_sha256': sha256_file(src),
            'page_bytes': len(page.encode('utf-8')),
        }

    # 图资产：只复制登记过的文件（移除目标会在登记表与校验器处报错）
    for figure in figures:
        if figure['unit'] not in {u['id'] for u in units}:
            continue
        src = ROOT / figure['file']
        if not src.is_file():
            raise SystemExit(f"工程装配：{figure['id']} 的文件缺失 {figure['file']}")
        dest = out / 'assets' / src.parent.name / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        report['figures_copied'].append(str(dest.relative_to(out)).replace('\\', '/'))

    # 工程约定页（符号/时钟/数据口径合同，随册交付）
    conventions = fragments.get('conventions')
    conventions_card = ''
    if conventions:
        page = page_html(conventions['title'], conventions['html'], level_bar=False)
        (out / 'conventions.html').write_text(page, encoding='utf-8')
        conventions_card = (
            f'<p>符号、时钟与数据口径的合同见'
            f'<a href="conventions.html">{conventions["title"]}</a>。'
            '正文、图、实验与断言的数字身份以它为准。</p>')

    # 目录页：单元卡 + 先修 + 层级 + 实验
    cards = []
    by_id = {u['id']: u for u in manifest['units']}
    for unit in units:
        prereqs = '、'.join(by_id[p]['title'] + f'（{p}）' for p in unit.get('prerequisites', []) if p in by_id)
        exps = [e for e in experiments if e.get('unit') == unit['id']]
        badges = ''.join(f'<span class="badge">{level}</span>' for level in unit.get('levels', []))
        cards.append(
            f'<section class="unit-card"><h2><a href="{unit["id"].lower()}.html">'
            f'{unit["id"]}　{unit["title"]}</a></h2>'
            f'<p>{badges}</p>'
            f'<p>先修：{prereqs or "无"}</p>'
            + ''.join(f'<p>实验 {e["id"]}（{e["family"]}）：{e["acceptance"]}</p>' for e in exps)
            + '</section>')
    index_body = (
        '<h1>BMS 工程深研册（P1 样章）</h1>'
        '<p>三份深研样章的离线装配产物。正文、图、实验与断言来自同一份登记表，'
        '数字身份见 build-report.json；样章不是全书，工程整册装配在 P3 之后。</p>'
        + conventions_card + ''.join(cards)
    )
    (out / 'index.html').write_text(page_html('BMS 工程深研册', index_body, level_bar=False), encoding='utf-8')
    verify_spine(index_body, out)

    report_path = out / 'build-report.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    verify_publication(out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=str(ENGINEERING / 'dist'), help='输出目录')
    parser.add_argument('--pdf', action='store_true', help='额外打印 PDF（无头 Chrome/Edge）')
    parser.add_argument('--check', metavar='DIST', help='只对已构建产物跑出版门')
    args = parser.parse_args()
    if args.check:
        verify_publication(Path(args.check))
        print(f'engineering publication gate ok: {args.check}')
        return 0
    out = Path(args.out)
    report = build(out)
    total = sum(u['page_bytes'] for u in report['units'].values())
    printed = print_pdfs(out) if args.pdf else []
    print(f"engineering build ok: {len(report['units'])} units, {total} bytes pages, "
          f"{len(report['figures_copied'])} figures"
          + (f", {len(printed)} PDFs" if printed else '') + f" -> {args.out}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
