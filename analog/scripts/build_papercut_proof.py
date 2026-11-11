"""三张插图的 16K 彩色/灰度校样；PDF 保留矢量文字，不把截图当印刷稿。"""
from __future__ import annotations

import html
from pathlib import Path
import re

import yaml
from playwright.sync_api import sync_playwright

from compose_technical_overlay import ROOT

FOLDER = ROOT / 'docs/superpowers/visual/reviews/python-papercut-2026-11-05'


def gray_svg(markup):
    def convert(match):
        value = match.group(0)
        r, g, b = (int(value[i:i + 2], 16) for i in (1, 3, 5))
        gray = round(.299 * r + .587 * g + .114 * b)
        return '#' + f'{gray:02x}' * 3
    return re.sub(r'#[a-fA-F0-9]{6}\b', convert, markup)


def build():
    assets = yaml.safe_load((FOLDER / 'pilot-manifest.yml').read_text(encoding='utf-8'))['assets']
    pages = []
    for asset in assets:
        colored = (ROOT / asset['print_fallback']).read_text(encoding='utf-8')
        gray = gray_svg(colored)
        pages.append('<section class="sheet"><h2>' + html.escape(asset['purpose']) +
                     '</h2><div class="label">彩色 · 矢量印刷版</div><div class="image">' + colored +
                     '</div><div class="label">灰度 · 矢量印刷版</div><div class="image">' + gray +
                     '</div><footer>图宽 138mm · 16K 校样 · 第 17 章 ' + html.escape(str(asset['anchor'])) +
                     ' 节 · 用户三章整体验收待完成</footer></section>')
    css = ('@page{size:185mm 260mm;margin:15mm 18mm}*{box-sizing:border-box}'
           'body{margin:0;font-family:"Microsoft YaHei",sans-serif;color:#2a2927;background:#fff}'
           '.sheet{height:229mm;break-after:page}.sheet:last-child{break-after:auto}'
           'h2{font-size:11pt;line-height:5mm;margin:0 0 2mm}.label{font-size:9pt;line-height:4mm}'
           '.image{width:138mm;height:103.5mm;margin:0 auto}svg{display:block;width:138mm;height:103.5mm}'
           'footer{font-size:8pt;line-height:4mm;margin-top:2mm}'
           '@media screen{body{max-width:185mm;margin:12px auto}.sheet{padding:15mm 18mm;height:auto;border:1px solid #ccc}}')
    output = FOLDER / 'print-proof.html'
    output.write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Python 插图 16K 校样</title><style>' +
                      css + '</style>' + ''.join(pages) + '</html>', encoding='utf-8')
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome', headless=True)
        try:
            page = browser.new_page()
            page.goto(output.as_uri())
            page.evaluate('document.fonts.ready')
            page.emulate_media(media='print')
            page.pdf(path=str(FOLDER / 'print-proof.pdf'), prefer_css_page_size=True, print_background=True)
        finally:
            browser.close()
    from pypdf import PdfReader
    pdf = PdfReader(FOLDER / 'print-proof.pdf')
    if len(pdf.pages) != len(assets):
        raise ValueError(f'校样意外分页：{len(pdf.pages)}，应为 {len(assets)}')
    print(f'{len(pdf.pages)} 页矢量校样 → {FOLDER.relative_to(ROOT)}/print-proof.pdf')


if __name__ == '__main__':
    build()
