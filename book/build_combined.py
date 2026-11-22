"""合并卷一/卷二两册成品为《从模拟电路到 BMS》合集（EPUB + A4 PDF）。

EPUB：共享卷首去重、总目录与跨卷链接内联、合集封面及压缩打包。

PDF：重排合集卷首与分卷封面，目录按实际书签生成，保留正文与原卷页码。

用法：python book/build_combined.py [--check]
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOL1 = ROOT / "book/dist/volume-1/book.epub"
VOL2 = ROOT / "book/dist/volume-2/book.epub"
VOL1_PDF = ROOT / "book/dist/volume-1/book-a4.pdf"
VOL2_PDF = ROOT / "book/dist/volume-2/book-a4.pdf"
OUT_DIR = ROOT / "book/dist/combined"
OUT = OUT_DIR / "from-analog-to-bms.epub"
OUT_PDF = OUT_DIR / "from-analog-to-bms.pdf"

TITLE = "从模拟电路到 BMS（两卷合集）"
VOL1_TITLE = "卷一　通往模拟电路之路"
VOL2_TITLE = "卷二　BMS 实战：从一颗电芯到一套证据链"

def compose_nav_xhtml(v1_nav_ol: str, v2_nav_ol: str) -> str:
    """合成 EPUB3 目录：nav 内 0/1 个标题后只接一个顶层 ol，两卷作嵌套 ol。

    EPUB 3.3 §7.3 的 nav 内容模型是「可选标题 + 恰好一个 ol」，
    不能把两卷目录平铺成 h2/ol/h2/ol 的兄弟序列。
    """
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">
<head><title>{TITLE}</title></head>
<body>
<nav epub:type="toc" id="toc">
<h1>{TITLE}</h1>
<ol>
<li><span>{VOL1_TITLE}</span>
{v1_nav_ol}
</li>
<li><span>{VOL2_TITLE}</span>
{v2_nav_ol}
</li>
</ol>
</nav>
</body>
</html>
'''


def nav_structure_problems(nav_xhtml: str | bytes) -> list[str]:
    """按 EPUB 3.3 nav 内容模型校验：一个 toc nav、至多一个标题、一个顶层 ol。"""
    import xml.etree.ElementTree as ET

    xhtml = "{http://www.w3.org/1999/xhtml}"
    ops = "{http://www.idpf.org/2007/ops}"
    try:
        root = ET.fromstring(nav_xhtml)
    except ET.ParseError as exc:
        return [f"nav 不是合法 XML：{exc}"]
    navs = [node for node in root.iter(xhtml + "nav") if node.get(ops + "type") == "toc"]
    if len(navs) != 1:
        return [f"toc nav 数量为 {len(navs)}，应为 1"]
    children = list(navs[0])
    headings = [node for node in children if node.tag in {
        xhtml + f"h{level}" for level in range(1, 7)}]
    ols = [node for node in children if node.tag == xhtml + "ol"]
    problems: list[str] = []
    if len(headings) > 1:
        problems.append(f"nav 标题 {len(headings)} 个，应至多 1 个")
    if len(ols) != 1:
        problems.append(f"nav 顶层 ol {len(ols)} 个，应恰好 1 个")
        return problems
    if headings and children.index(headings[0]) > children.index(ols[0]):
        problems.append("nav 标题须在目录 ol 之前")
    extra = [node for node in children if node not in headings and node not in ols]
    if extra:
        problems.append(f"nav 含目录外直接子元素 {len(extra)} 个")
    top_items = [node for node in ols[0] if node.tag == xhtml + "li"]
    if len(top_items) != 2:
        problems.append(f"顶层目录卷数 {len(top_items)}，应为 2")
    for index, item in enumerate(top_items, 1):
        if not any(node.tag == xhtml + "ol" for node in item):
            problems.append(f"第 {index} 卷缺少嵌套目录 ol")
    return problems


def build() -> Path:
    from combined_epub import build as build_epub
    details = build_epub(VOL1, VOL2, OUT)
    print(f"combined epub -> {OUT} ({details['bytes']} bytes)")
    return OUT


def build_pdf() -> Path:
    from combined_pdf import build as assemble_pdf
    details = assemble_pdf(VOL1_PDF, VOL2_PDF, OUT_PDF)
    print(f"combined pdf -> {OUT_PDF} ({details['pages']} pages)")
    return OUT_PDF


def check(path: Path) -> int:
    from combined_epub import validate
    from epub_standard import check as check_standard
    try:
        details = validate(path)
        standard = check_standard(path)
        if standard is not None:
            details['epubcheck'] = standard
        with zipfile.ZipFile(path) as archive:
            problems = nav_structure_problems(archive.read('OEBPS/nav.xhtml'))
        if problems:
            raise ValueError('; '.join(problems))
    except (ValueError, AssertionError, OSError, KeyError) as exc:
        print(f"FAIL: EPUB {exc}")
        return 1
    print(f"PASS: 合集 EPUB {details}")
    return 0


def check_pdf(path: Path) -> int:
    from combined_pdf import validate
    try:
        details = validate(path, VOL1_PDF, VOL2_PDF)
    except (ValueError, AssertionError, OSError, KeyError) as exc:
        print(f"FAIL: PDF {exc}")
        return 1
    print(f"PASS: 合集 PDF {details}")
    return 0


def fingerprint(path: Path) -> dict:
    import hashlib
    with path.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': digest}


def main(argv: list[str] | None = None) -> int:
    import json
    import subprocess
    from datetime import UTC, datetime
    from combined_epub import build as assemble_epub, validate as validate_epub
    from combined_pdf import build as assemble_pdf, validate as validate_pdf
    from epub_standard import check as check_standard
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='只校验已有产物')
    args = ap.parse_args(argv)
    if args.check:
        return check(OUT) | check_pdf(OUT_PDF)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pending_epub = OUT_DIR / '.building.epub'
    pending_pdf = OUT_DIR / '.building.pdf'
    inputs = [fingerprint(p) for p in (VOL1, VOL2, VOL1_PDF, VOL2_PDF)]
    print('构建合集 EPUB：整理卷首与跨卷引用', flush=True)
    epub_build = assemble_epub(VOL1, VOL2, pending_epub)
    epub_check = validate_epub(pending_epub)
    epub_standard = check_standard(pending_epub)
    if epub_standard is not None:
        epub_check['epubcheck'] = epub_standard
    with zipfile.ZipFile(pending_epub) as archive:
        problems = nav_structure_problems(archive.read('OEBPS/nav.xhtml'))
    if problems:
        raise ValueError('; '.join(problems))
    print(f'PASS: EPUB {epub_check}', flush=True)
    print('构建合集 PDF：重建总目录、链接与卷号页码', flush=True)
    pdf_build = assemble_pdf(VOL1_PDF, VOL2_PDF, pending_pdf)
    pdf_check = validate_pdf(pending_pdf, VOL1_PDF, VOL2_PDF)
    print(f'PASS: PDF {pdf_check}', flush=True)
    if inputs != [fingerprint(p) for p in (VOL1, VOL2, VOL1_PDF, VOL2_PDF)]:
        raise ValueError('构建期间分卷输入发生变化；未替换正式合集')
    pending_epub.replace(OUT)
    pending_pdf.replace(OUT_PDF)
    commit = subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    status = subprocess.run(['git','status','--porcelain'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    report = {'schema':1,'scope':'combined','generated_at':datetime.now(UTC).isoformat(),
              'git_commit':commit,'working_tree_changes':status,'inputs':inputs,
              'outputs':[fingerprint(OUT),fingerprint(OUT_PDF)],
              'builder_sources':[fingerprint(ROOT/'book'/name) for name in
                  ('build_combined.py','combined_epub.py','combined_pdf.py','combined_front.py',
                   'epub_standard.py','reading_lab.py','assets/epub-reader.css')],
              'build':{'epub':epub_build,'pdf':pdf_build},
              'checks':{'epub':epub_check,'pdf':pdf_check}}
    (OUT_DIR/'combined-build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # 保留旧分卷审计的原始时间，不把旧检查冒充本轮全量检查。
    report_path = ROOT/'book/dist/build-report.json'
    previous = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
    previous['combined'] = report
    report_path.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'合集与构建记录已更新 -> {OUT_DIR}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
