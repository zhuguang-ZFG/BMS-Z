"""Catch readable-looking PDF figures whose copied numbers are corrupted."""

from pathlib import Path
import base64
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_reading_sketches as checks  # noqa: E402
from generate_reading_sketches import ROOT  # noqa: E402


class ReadingSketchOutputTests(unittest.TestCase):
    def test_all_reading_sketches_keep_exact_text_in_current_chromium_pdf(self):
        from playwright.sync_api import sync_playwright

        entries = json.loads((ROOT / 'book/reading-sketches.json').read_text(
            encoding='utf-8'))['entries']
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            figures = []
            for entry in entries:
                source = (ROOT / entry['asset']).read_bytes()
                encoded = base64.b64encode(source).decode('ascii')
                figures.append(
                    f'<figure><img src="data:image/svg+xml;base64,{encoded}">'
                    f'<p>{entry["question"]}</p><figcaption>{entry["caption"]}</figcaption></figure>')
            html = root / 'sketches.html'
            html.write_text(
                '<style>@page{size:A4;margin:15mm}figure{margin:0;break-after:page}'
                'img{width:100%}</style>' + ''.join(figures), encoding='utf-8')
            output = root / 'sketches.pdf'
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.goto(html.as_uri(), wait_until='load')
                page.evaluate('async () => { await document.fonts.ready; '
                              'await Promise.all(Array.from(document.images, i => i.decode())); }')
                page.pdf(path=str(output), print_background=True, prefer_css_page_size=True)
                browser.close()
            self.assertEqual(len(checks.check_pdf(output, entries)), len(entries))

    def test_epub_xml_serialization_keeps_art_and_embedded_font_content(self):
        entry = {'drawing':'sample', 'alt':'sample diagram', 'asset':'sample.svg',
                 'caption':'Caption', 'question':'Question'}
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><style>font-data</style><text>3.16 V</text></svg>'
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'sample.svg').write_text(svg, encoding='utf-8')
            for label in ['3.16 V', 'M.KP V']:
                with self.subTest(label=label):
                    with zipfile.ZipFile(root/'test.epub', 'w') as archive:
                        archive.writestr('chapter.xhtml',
                            '<html xmlns="http://www.w3.org/1999/xhtml"><body><figure>'
                            '<img src="asset.svg" alt="sample diagram"/>'
                            '<p>Question</p><figcaption>Caption</figcaption></figure></body></html>')
                        archive.writestr('asset.svg', ET.tostring(ET.fromstring(svg.replace('3.16 V', label))))
                    with patch.object(checks, 'ROOT', root):
                        if label == '3.16 V':
                            self.assertEqual(len(checks.check_epub(root/'test.epub', [entry])), 1)
                        else:
                            with self.assertRaisesRegex(ValueError, 'differs'):
                                checks.check_epub(root/'test.epub', [entry])

    def test_exact_numbers_and_same_page_caption_are_required(self):
        entry = {'drawing':'sample', 'title':'Reading', 'asset':'sample.svg',
                 'caption':'Caption', 'question':'Question'}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'sample.svg').write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"><text>3.16 V</text></svg>', encoding='utf-8')
            for value, caption_on_next, expected_error in [
                ('3.16 V', False, None),
                ('M.KP V', False, '3.16 V'),
                ('3.16 V', True, 'Caption'),
            ]:
                with self.subTest(value=value, caption_on_next=caption_on_next):
                    output = root/'proof.pdf'
                    with fitz.open() as pdf:
                        page = pdf.new_page()
                        page.insert_text((30,30), 'Reading\n'+value+'\nQuestion')
                        if caption_on_next:
                            page = pdf.new_page()
                        page.insert_text((30,90), 'Caption')
                        pdf.save(output)
                    with patch.object(checks, 'ROOT', root):
                        if expected_error:
                            with self.assertRaisesRegex(ValueError, expected_error):
                                checks.check_pdf(output, [entry])
                        else:
                            self.assertEqual(checks.check_pdf(output, [entry])[0]['page'], 1)


if __name__ == '__main__':
    unittest.main()
