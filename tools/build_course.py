#!/usr/bin/env python3
"""Build the sequential course HTML and EPUB; --pdf also prints a local PDF.

All three editions read docs/course/manifest.json and the same lesson manuscripts.
"""
from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / 'docs/course'
DEFAULT_OUT = ROOT / 'bms-book/dist'


def load_epub_module():
    spec = importlib.util.spec_from_file_location('course_epub', ROOT / 'bms-book/build_epub.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CourseHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.targets, self.images, self.answers = [], [], [], 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'a' and attrs.get('href'):
            self.targets.append(attrs['href'])
        if tag == 'img':
            self.images.append(attrs.get('src', ''))
        if tag == 'details' and 'course-check' in attrs.get('class', '').split():
            self.answers += 1


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []

    def handle_data(self, data):
        self.text.append(data)


def normalized_text(value):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', value))


def missing_pdf_answers(source, pdf_text):
    missing = []
    actual = normalized_text(pdf_text)
    for number, content in enumerate(re.findall(r'<details\b[^>]*class="course-check"[^>]*>([\s\S]*?)</details>', source), 1):
        parser = TextOnly()
        parser.feed(content)
        if normalized_text(''.join(parser.text)) not in actual:
            missing.append(number)
    return missing


def validate_html(source, manifest):
    parsed = CourseHTML()
    parsed.feed(source)
    problems = []
    if len(parsed.ids) != len(set(parsed.ids)):
        problems.append('duplicate HTML IDs')
    for row in manifest['lessons']:
        if f'lesson-{row["id"]}' not in parsed.ids:
            problems.append(f'missing lesson {row["id"]}')
    for target in parsed.targets:
        if target.startswith('#'):
            if target[1:] not in parsed.ids:
                problems.append(f'unknown offline anchor {target}')
        elif not re.match(r'^(?:https?:|mailto:)', target):
            problems.append(f'nonportable link {target}')
    if any(not src.startswith('data:image/') for src in parsed.images):
        problems.append('image not embedded')
    if parsed.answers < len(manifest['lessons']):
        problems.append(f'only {parsed.answers} answer sections')
    if problems:
        raise ValueError('; '.join(problems))
    return {'lessons': len(manifest['lessons']), 'answers': parsed.answers,
            'images': len(parsed.images), 'links': len(parsed.targets), 'ids': len(parsed.ids)}


def render_html():
    manifest = json.loads((COURSE / 'manifest.json').read_text(encoding='utf-8'))
    rendered = subprocess.run(['node', str(ROOT / 'tools/render_course.mjs')], cwd=ROOT,
                              capture_output=True, encoding='utf-8')
    if rendered.returncode:
        raise RuntimeError(f'Course renderer failed:\n{rendered.stderr}')
    sections = json.loads(rendered.stdout)
    by_file = {section['file']: section for section in sections}
    esc = html.escape
    parts = [f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(manifest['title'])}</title><style>{(COURSE / 'course.css').read_text(encoding='utf-8')}</style>
</head><body><header class="cover"><p class="eyebrow">BMS-Z · 连续学习版</p>
<h1 id="course-cover">从读懂电池<br>到交付验证</h1><p class="cover-deck">24 课 · 8 个模块 · 一个贯穿项目</p>
<p>先算清，再测量；先有证据，再下结论。</p>
<p class="cover-note">版本 {esc(manifest['version'])} · {esc(manifest['modified'][:10])}<br>{esc(manifest['author'])}</p>
<p class="cover-note">教学数据与 PC 模型不等于真实硬件验证。<br>真人试读 W5 仍待验收。</p></header>''']
    parts.append('<nav class="course-toc" aria-label="目录"><h2 id="course-toc">课程目录</h2><ol>')
    parts.append('<li><a href="#course-guide">怎么使用这门课程</a></li><li><a href="#course-project">贯穿项目使用说明</a></li>')
    for module in manifest['modules']:
        parts.append(f'<li><a href="#module-{esc(module["id"])}">{esc(module["title"])}</a><ol>')
        for lesson in manifest['lessons']:
            if lesson['module'] == module['id']:
                parts.append(f'<li><a href="#lesson-{lesson["id"]}">{lesson["id"]} · {esc(lesson["title"])}</a></li>')
        parts.append('</ol></li>')
    parts.append('</ol></nav><main>')
    for filename in ('index.md', 'project.md'):
        parts.append(f'<section class="frontmatter">{by_file[filename]["body"]}</section>')
    for module in manifest['modules']:
        parts.append(f'<section class="module"><p class="eyebrow">模块作品</p><h1 id="module-{module["id"]}">{esc(module["title"])}</h1><p class="module-artifact">完成后留下：{esc(module["artifact"])}</p></section>')
        for lesson in manifest['lessons']:
            if lesson['module'] == module['id']:
                parts.append(f'<article class="lesson" data-course-lesson="{lesson["id"]}">{by_file[lesson["file"]]["body"]}</article>')
    parts.append('</main></body></html>')
    source = '\n'.join(parts)
    return source, manifest, validate_html(source, manifest)


def find_browser(override=None):
    candidates = [override] if override else [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        shutil.which('google-chrome'), shutil.which('chromium'), shutil.which('msedge'),
    ]
    browser = next((p for p in candidates if p and Path(p).exists()), None)
    if not browser:
        raise RuntimeError('PDF requires Chrome/Edge; supply --browser executable')
    return browser


def print_pdf(html_path, output, manifest, browser):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        print_source = Path(profile) / 'course-print.html'
        print_source.write_text(re.sub(r'<details\b(?![^>]*\bopen)([^>]*)>', r'<details open\1>',
                                       html_path.read_text(encoding='utf-8')), encoding='utf-8')
        subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                        '--generate-pdf-document-outline', f'--user-data-dir={profile}',
                        f'--print-to-pdf={output.resolve()}', print_source.resolve().as_uri()],
                       capture_output=True, check=True, timeout=180)
    import fitz
    temporary = output.with_suffix('.stamped.pdf')
    with fitz.open(output) as document:
        document.set_metadata({'title': manifest['title'], 'author': manifest['author'],
                               'subject': '24 课连续学习版；虚拟项目不构成硬件验收',
                               'creator': 'tools/build_course.py'})
        for number, page in enumerate(document):
            if number:
                label = f'{number} / {document.page_count - 1}'
                width = fitz.get_text_length(label, fontsize=8)
                page.insert_text(((page.rect.width - width) / 2, page.rect.height - 20), label,
                                 fontsize=8, color=(.38, .43, .40))
        text = ''.join(page.get_text() for page in document)
        missing = [row['id'] for row in manifest['lessons'] if f'{row["id"]} ·' not in text]
        answer_gaps = missing_pdf_answers(html_path.read_text(encoding='utf-8'), text)
        if missing or answer_gaps or not document.get_toc():
            raise ValueError(f'PDF lesson/answer/outline contract: lessons={missing}, answers={answer_gaps}, outline={len(document.get_toc())}')
        result = {'pages': document.page_count, 'outline_entries': len(document.get_toc()),
                  'lesson_headings': len(manifest['lessons']), 'answers': len(manifest['lessons'])}
        document.save(temporary, garbage=3, deflate=True)
    temporary.replace(output)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--pdf', action='store_true')
    parser.add_argument('--browser')
    args = parser.parse_args(argv)
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source, manifest, report = render_html()
    html_path = out / 'bms-course.html'
    html_path.write_text(source, encoding='utf-8')
    epub = load_epub_module()
    metadata = {**manifest, 'identifier': f'urn:bms-z:course:{manifest["version"]}'}
    epub_path = out / 'bms-course.epub'
    epub.package_html(source, epub_path, metadata, stylesheet=(COURSE / 'course.css').read_text(encoding='utf-8'))
    problems = epub.validate_epub(epub_path)
    if problems:
        raise ValueError('; '.join(problems))
    report['epub'] = 'PASS: XML, links, assets and archive'
    if args.pdf:
        report['pdf'] = print_pdf(html_path, out / 'bms-course.pdf', manifest, find_browser(args.browser))
    report['sources_sha256'] = {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [COURSE / 'manifest.json', COURSE / 'index.md', COURSE / 'project.md',
                                          COURSE / 'course.css', Path(__file__), ROOT / 'tools/render_course.mjs',
                                          ROOT / 'bms-book/build_epub.py',
                                          *(COURSE / row['file'] for row in manifest['lessons'])]}
    artifacts = [html_path, epub_path] + ([out / 'bms-course.pdf'] if args.pdf else [])
    report['artifacts'] = {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                           for p in artifacts}
    (out / 'course-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'sources_sha256'}, ensure_ascii=False, indent=2))
    print(f'built {html_path}\nbuilt {epub_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
