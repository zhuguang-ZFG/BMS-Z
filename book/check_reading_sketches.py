"""Verify that the finished PDF and EPUB retain every hand-drawn reading figure."""

import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

import fitz

ROOT = Path(__file__).resolve().parents[1]
X = '{http://www.w3.org/1999/xhtml}'
S = '{http://www.w3.org/2000/svg}'


def compact(value):
    return re.sub(r'\s+', '', value)


def check_pdf(path, entries):
    rows = []
    with fitz.open(path) as doc:
        texts = [compact(page.get_text()) for page in doc]
        for entry in entries:
            matches = [i for i, text in enumerate(texts) if compact(entry['title']) in text]
            if len(matches) != 1:
                raise ValueError(f"{entry['drawing']}: expected one searchable PDF title, found {len(matches)}")
            index = matches[0]
            svg = ET.parse(ROOT / entry['asset']).getroot()
            labels = [''.join(node.itertext()) for node in svg.iter(S + 'text')]
            for label in labels + [entry['caption'], entry['question']]:
                if compact(label) not in texts[index]:
                    raise ValueError(f"{entry['drawing']}: PDF page {index + 1} is missing exact text: {label}")
            rows.append({'drawing':entry['drawing'], 'page':index + 1,
                         'labels_checked':len(labels), 'caption_and_question_on_same_page':True})
    return rows


def check_epub(path, entries):
    rows = []
    with zipfile.ZipFile(path) as archive:
        docs = {name:ET.fromstring(archive.read(name)) for name in archive.namelist()
                if name.endswith('.xhtml') and not name.endswith('/nav.xhtml')}
        for entry in entries:
            matches = [(name, figure, img) for name, doc in docs.items()
                       for figure in doc.iter(X + 'figure') for img in figure.iter(X + 'img')
                       if img.get('alt') == entry['alt']]
            if len(matches) != 1:
                raise ValueError(f"{entry['drawing']}: expected one EPUB figure, found {len(matches)}")
            name, figure, img = matches[0]
            asset = posixpath.normpath(posixpath.join(posixpath.dirname(name), img.get('src')))
            raw = archive.read(asset)
            # Volume II serializes SVG as XML while stripping theme media rules.
            # Namespace prefixes and attribute order may change; content may not.
            source = (ROOT / entry['asset']).read_bytes()
            if ET.canonicalize(raw, rewrite_prefixes=True) != ET.canonicalize(source, rewrite_prefixes=True):
                raise ValueError(f"{entry['drawing']}: EPUB drawing differs from the source SVG")
            text = compact(''.join(figure.itertext()))
            if any(compact(value) not in text for value in [entry['caption'], entry['question']]):
                raise ValueError(f"{entry['drawing']}: EPUB caption or question is missing")
            rows.append({'drawing':entry['drawing'], 'document':name, 'asset':asset})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path, default=ROOT/'book/dist/combined/from-analog-to-bms.pdf')
    parser.add_argument('--epub', type=Path, default=ROOT/'book/dist/combined/from-analog-to-bms.epub')
    parser.add_argument('--output', type=Path, default=ROOT/'book/dist/reading-sketch-checks.json')
    args = parser.parse_args()
    entries = json.loads((ROOT/'book/reading-sketches.json').read_text(encoding='utf-8'))['entries']
    result = {'pdf':check_pdf(args.pdf, entries), 'epub':check_epub(args.epub, entries)}
    for name in ['pdf', 'epub']:
        with getattr(args, name).open('rb') as stream:
            result[name + '_sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'PASS: {len(entries)} drawings in PDF/EPUB; exact labels, numbers, captions and questions')


if __name__ == '__main__':
    main()
