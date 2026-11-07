#!/usr/bin/env python3
"""Render the editable course sketches to high-resolution static WebP files.

python tools/render_course_sketches.py --browser-channel msedge
python tools/render_course_sketches.py --browser-channel chrome
python tools/render_course_sketches.py --check

Inputs are fixed to docs/course/assets/sketches/*.svg. Rendering uses the
existing Playwright and Pillow dependencies; it never installs a browser or
substitutes another typeface. --check needs only the Python standard library.
The local manifest describes static course images, not the animation inventory.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SKETCH_DIR = ROOT / 'docs/course/assets/sketches'
SCRIPT = Path(__file__).resolve()
SCHEMA = 'bms-course-static-sketch-webp-v1'
SETTINGS = {
    'viewport_width': 1440, 'viewport_height': 1080,
    'device_scale_factor': 2, 'image_width': 2880, 'image_height': 2160,
    'format': 'WEBP', 'quality': 97, 'method': 6,
}
CSS_FONT = 'CourseKaiTi'
KAI_FAMILIES = {'kaiti', '楷体', '楷體'}
SVG_NS = '{http://www.w3.org/2000/svg}'
TEXT_PROBE = '电芯电流电量采样有效0123456789 A V Ah Δ Ω −'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def is_kaiti(family):
    return family.strip().casefold().replace(' ', '') in KAI_FAMILIES


def svg_dimensions(data):
    root = ET.fromstring(data)
    if root.tag != f'{SVG_NS}svg':
        raise ValueError('source must be an SVG document')
    viewbox = [float(n) for n in root.attrib.get('viewBox', '').split()]
    if viewbox != [0, 0, 1440, 1080]:
        raise ValueError(f'expected viewBox="0 0 1440 1080", got {viewbox}')
    for attr, expected in (('width', 1440), ('height', 1080)):
        declared = root.attrib.get(attr, '')
        if not re.fullmatch(rf'{expected}(?:\.0+)?(?:px)?', declared):
            raise ValueError(f'expected {attr}={expected}, got {declared!r}')
    return {'width': 1440, 'height': 1080, 'viewBox': [0, 0, 1440, 1080]}


def webp_dimensions(data):
    """Read the canvas size without Pillow, including all three WebP encodings."""
    if (len(data) < 20 or data[:4] != b'RIFF' or data[8:12] != b'WEBP'
            or struct.unpack_from('<I', data, 4)[0] + 8 != len(data)):
        raise ValueError('invalid or truncated WebP RIFF container')
    position = 12
    while position + 8 <= len(data):
        kind = data[position:position + 4]
        size = struct.unpack_from('<I', data, position + 4)[0]
        start, end = position + 8, position + 8 + size
        if end > len(data):
            raise ValueError('truncated WebP chunk')
        payload = data[start:end]
        if kind == b'VP8X' and len(payload) >= 10:
            return (int.from_bytes(payload[4:7], 'little') + 1,
                    int.from_bytes(payload[7:10], 'little') + 1)
        if kind == b'VP8L' and len(payload) >= 5 and payload[0] == 0x2F:
            packed = int.from_bytes(payload[1:5], 'little')
            return (packed & 0x3FFF) + 1, ((packed >> 14) & 0x3FFF) + 1
        if kind == b'VP8 ' and len(payload) >= 10 and payload[3:6] == b'\x9d\x01\x2a':
            return (struct.unpack_from('<H', payload, 6)[0] & 0x3FFF,
                    struct.unpack_from('<H', payload, 8)[0] & 0x3FFF)
        position = end + (size & 1)
    raise ValueError('WebP canvas chunk not found')


def find_kaiti(explicit=None):
    """Resolve and identify an actual KaiTi font file, rejecting fontconfig fallback."""
    from PIL import ImageFont

    candidates = []
    if explicit is not None:
        candidates.append(explicit.resolve())
    elif sys.platform == 'win32':
        candidates.append(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/simkai.ttf')
    else:
        # KaiTi can be installed by the user on macOS/Linux. fc-match alone is
        # insufficient: it happily returns a different font when KaiTi is absent.
        if shutil.which('fc-match'):
            result = subprocess.run(
                ['fc-match', '-f', '%{file}\n%{family}\n', 'KaiTi'],
                capture_output=True, text=True, encoding='utf-8', check=False, timeout=10,
            )
            fields = result.stdout.splitlines()
            if result.returncode == 0 and len(fields) >= 2 and any(is_kaiti(name) for name in fields[1].split(',')):
                candidates.append(Path(fields[0]))
        candidates += [Path('/Library/Fonts/simkai.ttf'),
                       Path.home() / 'Library/Fonts/simkai.ttf',
                       Path.home() / '.local/share/fonts/simkai.ttf']
    for path in dict.fromkeys(candidates):
        if not path.is_file():
            continue
        try:
            face = ImageFont.truetype(str(path), size=48)
            family, style = face.getname()
        except (OSError, ValueError):
            continue
        if not is_kaiti(family):
            continue
        data = path.read_bytes()
        return data, {'family': family, 'style': style, 'file_name': path.name,
                      'file_sha256': sha256(data), 'browser_family': CSS_FONT}
    raise RuntimeError('KaiTi 字体未确认，停止导出；不会回退到宋体、无衬线或 STKaiti。'
                       'Windows 需要可读取的 Fonts/simkai.ttf；其他平台可用 --font-file 指定真正的 KaiTi 文件。')


def check_manifest(directory=SKETCH_DIR):
    """Verify local sources, renderer identity, output sizes and image identities."""
    problems = []
    sources = sorted(directory.glob('*.svg'))
    if not sources:
        problems.append('no SVG inputs found')
    path = directory / 'manifest.json'
    if not path.is_file():
        return [*problems, 'manifest.json missing; render after the SVG sources are frozen']
    try:
        manifest = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return [*problems, f'invalid manifest: {exc}']
    if manifest.get('schema') != SCHEMA:
        problems.append('manifest schema mismatch')
    renderer = manifest.get('renderer', {})
    if renderer.get('source') != 'tools/render_course_sketches.py' or renderer.get('sha256') != sha256(SCRIPT.read_bytes()):
        problems.append('renderer SHA-256 changed; render again')
    if renderer.get('settings') != SETTINGS:
        problems.append('renderer settings mismatch')
    if renderer.get('browser_channel') not in {'chrome', 'msedge'} or not renderer.get('browser_version'):
        problems.append('missing actual browser channel/version')
    font = manifest.get('font', {})
    if (not is_kaiti(font.get('family', '')) or font.get('browser_family') != CSS_FONT
            or not re.fullmatch('[0-9a-f]{64}', font.get('file_sha256', ''))):
        problems.append('missing verified KaiTi font identity')
    entries = manifest.get('images', [])
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        return [*problems, 'manifest images must be a list of image records']
    listed = [entry.get('source') for entry in entries]
    if len(listed) != len(set(listed)) or set(listed) != {path.name for path in sources}:
        problems.append('SVG input list differs from manifest (missing, added or duplicate source)')
    expected_images = {path.with_suffix('.webp').name for path in sources}
    actual_images = {path.name for path in directory.glob('*.webp')}
    for missing in sorted(expected_images - actual_images):
        problems.append(f'{missing}: output missing')
    for extra in sorted(actual_images - expected_images):
        problems.append(f'{extra}: unmanifested/orphan output')
    for entry in entries:
        name = entry.get('source')
        if not isinstance(name, str) or Path(name).name != name or Path(name).suffix != '.svg':
            problems.append(f'invalid source name: {name!r}')
            continue
        source, image = directory / name, directory / Path(name).with_suffix('.webp')
        if entry.get('image') != image.name:
            problems.append(f'{name}: unexpected output name')
        if not source.is_file():
            problems.append(f'{name}: source missing')
            continue
        data = source.read_bytes()
        if sha256(data) != entry.get('source_sha256'):
            problems.append(f'{name}: SVG SHA-256 changed; render again')
        try:
            if svg_dimensions(data) != entry.get('source_dimensions'):
                problems.append(f'{name}: SVG dimensions mismatch')
        except (ValueError, ET.ParseError) as exc:
            problems.append(f'{name}: {exc}')
        if entry.get('image_dimensions') != {'width': 2880, 'height': 2160}:
            problems.append(f'{name}: manifest output dimensions mismatch')
        bounds = entry.get('text_bounds_check', {})
        if (bounds.get('passed') is not True or not isinstance(bounds.get('text_nodes'), int)
                or bounds['text_nodes'] <= 0):
            problems.append(f'{name}: no successful text-bounds check recorded')
        if not image.is_file():
            continue
        image_data = image.read_bytes()
        if sha256(image_data) != entry.get('image_sha256'):
            problems.append(f'{image.name}: WebP SHA-256 changed')
        try:
            if webp_dimensions(image_data) != (2880, 2160):
                problems.append(f'{image.name}: actual size must be 2880×2160')
        except ValueError as exc:
            problems.append(f'{image.name}: {exc}')
    return problems


FONT_AND_BOUNDS = r'''async ({fontUrl, cssFamily, probe}) => {
  const face = new FontFace(cssFamily, `url("${fontUrl}")`, {style: 'normal', weight: '400'});
  await face.load();
  document.fonts.add(face);
  const sheet = document.createElement('style');
  sheet.textContent = `svg text, svg tspan { font-family: "${cssFamily}" !important; }`;
  document.head.append(sheet);
  const matches = await document.fonts.load(`48px "${cssFamily}"`, probe);
  await document.fonts.ready;
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  if (face.status !== 'loaded' || !matches.includes(face) || !document.fonts.check(`48px "${cssFamily}"`, probe)) {
    throw new Error('KaiTi FontFace was not successfully loaded; refusing fallback');
  }
  const svg = document.querySelector('body > svg');
  if (!svg) throw new Error('missing root SVG');
  const frame = svg.getBoundingClientRect();
  if (Math.abs(frame.width - 1440) > .01 || Math.abs(frame.height - 1080) > .01) {
    throw new Error(`unexpected SVG viewport: ${frame.width} × ${frame.height}`);
  }
  const nodes = [...svg.querySelectorAll('text, tspan')].filter(el => {
    const style = getComputedStyle(el);
    return el.textContent.trim() && style.display !== 'none' && style.visibility !== 'hidden';
  });
  if (!nodes.length) throw new Error('no visible editable SVG text to inspect');
  const measured = nodes.map(el => {
    const rect = el.getBoundingClientRect();
    const font = getComputedStyle(el).fontFamily;
    if (!font.includes(cssFamily)) throw new Error(`unexpected text font: ${font}`);
    return {text: el.textContent.trim(), left: rect.left - frame.left, top: rect.top - frame.top,
            right: rect.right - frame.left, bottom: rect.bottom - frame.top};
  });
  const overflow = measured.filter(r => r.left < -.25 || r.top < -.25 || r.right > 1440.25 || r.bottom > 1080.25);
  return {textNodes: nodes.length, overflow, bounds: {
    left: Math.min(...measured.map(r => r.left)), top: Math.min(...measured.map(r => r.top)),
    right: Math.max(...measured.map(r => r.right)), bottom: Math.max(...measured.map(r => r.bottom))
  }};
}'''


def render(browser_channel, font_file=None):
    from importlib.metadata import version

    from PIL import Image, __version__ as pillow_version, features
    from playwright.sync_api import sync_playwright

    sources = sorted(SKETCH_DIR.glob('*.svg'))
    if not sources:
        raise RuntimeError(f'no SVG sources found in {SKETCH_DIR}')
    # Read all sources once; verify their identities again before replacing any
    # output so a concurrent SVG edit cannot be silently exported as a mixed set.
    originals = {source.name: source.read_bytes() for source in sources}
    dimensions = {name: svg_dimensions(data) for name, data in originals.items()}
    font_data, font = find_kaiti(font_file)
    font_url = 'data:font/ttf;base64,' + base64.b64encode(font_data).decode('ascii')
    records = []
    # Keep staging on the target volume: Windows cannot atomically replace a
    # file across a C: temporary directory and a D: workspace.
    with tempfile.TemporaryDirectory(prefix='.tmp-sketch-render-', dir=SKETCH_DIR) as work:
        stage = Path(work)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel=browser_channel, headless=True)
            try:
                browser_version = browser.version
                context = browser.new_context(
                    viewport={'width': 1440, 'height': 1080}, device_scale_factor=2,
                    color_scheme='light', reduced_motion='reduce', locale='zh-CN', timezone_id='UTC',
                )
                try:
                    page = context.new_page()
                    page.set_default_timeout(30000)
                    for source in sources:
                        raw = originals[source.name]
                        svg = re.sub(r'^\s*<\?xml[^>]*\?>', '', raw.decode('utf-8-sig'))
                        page.set_content('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
                                         '<style>html,body{margin:0;padding:0;width:1440px;height:1080px;overflow:hidden}'
                                         'body>svg{display:block;width:1440px;height:1080px}</style></head><body>'
                                         + svg + '</body></html>', wait_until='load')
                        diagnostic = page.evaluate(FONT_AND_BOUNDS, {'fontUrl': font_url, 'cssFamily': CSS_FONT, 'probe': TEXT_PROBE})
                        if diagnostic['overflow']:
                            for item in diagnostic['overflow'][:12]:
                                print(f'OVERFLOW {source.name}: {json.dumps(item, ensure_ascii=False)}', file=sys.stderr)
                            raise RuntimeError(f'{source.name}: {len(diagnostic["overflow"])} text bounds exceed the canvas; no outputs replaced')
                        png = page.screenshot(type='png', full_page=False, animations='disabled')
                        output = stage / source.with_suffix('.webp').name
                        with Image.open(BytesIO(png)) as image:
                            if image.size != (2880, 2160):
                                raise RuntimeError(f'{source.name}: screenshot has unexpected size {image.size}')
                            image.convert('RGB').save(output, format='WEBP', quality=97, method=6)
                        encoded = output.read_bytes()
                        if webp_dimensions(encoded) != (2880, 2160):
                            raise RuntimeError(f'{output.name}: unexpected encoded dimensions')
                        records.append({
                            'source': source.name, 'source_sha256': sha256(raw),
                            'source_dimensions': dimensions[source.name], 'image': output.name,
                            'image_sha256': sha256(encoded), 'image_dimensions': {'width': 2880, 'height': 2160},
                            'text_bounds_check': {'passed': True, 'text_nodes': diagnostic['textNodes'],
                                                  'bounds_css_px': {key: round(value, 3) for key, value in diagnostic['bounds'].items()}},
                        })
                        print(f'RENDERED {source.name} → {output.name}: 2880×2160, {diagnostic["textNodes"]} text nodes within bounds')
                finally:
                    context.close()
            finally:
                browser.close()
        if {p.name for p in SKETCH_DIR.glob('*.svg')} != set(originals) or any(
                source.read_bytes() != originals[source.name] for source in sources):
            raise RuntimeError('SVG sources changed during rendering; no outputs replaced, freeze sources and rerun')
        manifest = {
            'schema': SCHEMA,
            'renderer': {'source': 'tools/render_course_sketches.py', 'sha256': sha256(SCRIPT.read_bytes()),
                         'settings': SETTINGS, 'browser_channel': browser_channel, 'browser_version': browser_version,
                         'playwright_version': version('playwright'), 'pillow_version': pillow_version,
                         'webp_version': features.version('webp')},
            'font': font, 'images': records,
        }
        manifest_path = stage / 'manifest.json'
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        for record in records:
            # Moving out of a private TemporaryDirectory carries its restrictive
            # Windows ACL. Copy into the public asset directory so other local
            # build identities can read the output, with its inherited ACL.
            shutil.copyfile(stage / record['image'], SKETCH_DIR / record['image'])
        # Publish the manifest last so it never claims an unfinished batch is valid.
        shutil.copyfile(manifest_path, SKETCH_DIR / 'manifest.json')
    return check_manifest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='check source/renderer/image hashes and dimensions using only the standard library')
    parser.add_argument('--browser-channel', choices=('chrome', 'msedge'), default='msedge' if sys.platform == 'win32' else 'chrome')
    parser.add_argument('--font-file', type=Path, help='explicit KaiTi font file; identity is verified, never used as a fallback')
    args = parser.parse_args()
    try:
        problems = check_manifest() if args.check else render(args.browser_channel, args.font_file)
    except Exception as exc:
        print(f'FAIL: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1
    if problems:
        for problem in problems:
            print(f'FAIL: {problem}', file=sys.stderr)
        return 1
    print(f'PASS: {len(list(SKETCH_DIR.glob("*.svg")))} static sketches; SVG/renderer/WebP SHA-256, 2880×2160 and font/bounds metadata')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
