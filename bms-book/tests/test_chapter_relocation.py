"""Artifact-level regression for local chapter links in a movable single-file book."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('href'):
            self.hrefs.append(attrs['href'])


def test_local_chapter_link_resolves_inside_single_file(tmp_path):
    import os
    import subprocess
    import sys

    output = tmp_path / 'book'
    subprocess.run(
        [sys.executable, str(ROOT / 'build_html.py'), '--out-dir', str(output)],
        check=True, capture_output=True, encoding='utf-8',
        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, timeout=120,
    )
    links = Links()
    links.feed((output / 'bms-book.html').read_text(encoding='utf-8'))
    filenames = {p.stem for p in (ROOT / 'book').glob('*.md')}
    local = [href for href in links.hrefs if not urlsplit(href).scheme
             and Path(unquote(urlsplit(href).path)).stem in filenames
             and urlsplit(href).path]
    assert not local, f'missing chapter files in movable edition: {local}'
    assert '#ch-09' in links.hrefs  # 第8章，前面还有00前言
    assert {unquote(href[1:]) for href in links.hrefs if href.startswith('#')} <= links.ids
