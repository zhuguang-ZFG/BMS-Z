#!/usr/bin/env python3
"""卷 II 16K 试排：复用 build_html 的装配、紧排与压印，只换 185×260 mm 页面。

为什么是补丁而不是复制一份构建器：卷 II 的正文装配、目录页码、页眉页脚、
索引页码全都长在 build_html.py 里；复制会立刻分叉。这里只替换 @page 尺寸
与依附于 A4 高度的几个常量，其余流程原样复用。共享装配器（P2 余项）落地后
本文件并入 book/。

用法：python bms-book/build_print_book.py --out-dir book/dist/volume-2
"""
from __future__ import annotations

import argparse
from pathlib import Path

import build_html as bh

A4_PAGE = "@page { size:A4; margin:17mm 16mm; }"
PAGE_16K = "@page { size:185mm 260mm; margin:15mm 14mm; }"

REPLACEMENTS = (
    (A4_PAGE, PAGE_16K),
    ("font-size:10.2pt; line-height:1.62;", "font-size:9.6pt; line-height:1.6;"),
    ("min-height:245mm;", "min-height:230mm;"),
    ("max-width:85mm; max-height:64mm;", "max-width:75mm; max-height:56mm;"),
    ("min-height:243mm;", "min-height:228mm;"),
    ("padding:16mm 12mm;", "padding:14mm 11mm;"),
    ("figure img { max-height:150mm;", "figure img { max-height:125mm;"),
    ('figure img { max-height:125mm; }', 'figure img { max-height:105mm; }'),
    ("min-height:6.2mm;", "min-height:5.6mm;"),
    ("padding-top:9mm;", "padding-top:8mm;"),
)


def patch_css() -> None:
    css = bh.CSS
    for old, new in REPLACEMENTS:
        if old not in css:
            raise SystemExit(f"16K 排版补丁找不到锚点：{old}")
        css = css.replace(old, new)
    if PAGE_16K not in css:
        raise SystemExit("16K 页面尺寸没有写进 CSS")
    bh.CSS = css


def print_pdf(browser: str, html_path: Path, out_pdf: Path) -> None:
    """同 bh._print_pdf，只把单遍打印超时放宽到 300 s（16K 页数更多）。"""
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             "--generate-pdf-document-outline", f"--user-data-dir={profile}",
             f"--print-to-pdf={out_pdf}", html_path.resolve().as_uri()],
            check=True, capture_output=True, timeout=300)


DEFAULT_OUT = Path(__file__).resolve().parent / "dist-16k"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="卷 II 16K 试排")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--browser", help="Chrome/Edge 可执行文件")
    args = parser.parse_args(argv)

    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    bh.DIST = out
    bh._print_pdf = print_pdf
    patch_css()
    bh.main()
    bh.build_pdf(args.browser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
