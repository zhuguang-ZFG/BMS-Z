#!/usr/bin/env python3
"""Build a complete, offline EPUB3 from the same HTML edition used for PDF.

python bms-book/build_epub.py [--html freshly-built.html] [--out-dir dist]
Without --html, regenerate the HTML from current manuscripts before packaging.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
from html.parser import HTMLParser
from io import BytesIO
import shutil
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
XHTML = "http://www.w3.org/1999/xhtml"
SVG = "http://www.w3.org/2000/svg"
MATH = "http://www.w3.org/1998/Math/MathML"
XLINK = "http://www.w3.org/1999/xlink"
OPF = "http://www.idpf.org/2007/opf"
DC = "http://purl.org/dc/elements/1.1/"
EPUB = "http://www.idpf.org/2007/ops"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SKIP = {"script", "style", "button", "input", "mjx-assistive-mml"}
SVG_CASE = {"viewbox": "viewBox", "preserveaspectratio": "preserveAspectRatio", "textlength": "textLength", "lengthadjust": "lengthAdjust", "gradientunits": "gradientUnits", "gradienttransform": "gradientTransform", "markerwidth": "markerWidth", "markerheight": "markerHeight", "refx": "refX", "refy": "refY", "patternunits": "patternUnits", "clippathunits": "clipPathUnits"}
CSS = """body{font-family:serif;line-height:1.65;margin:1em;color:#182626;word-wrap:break-word;overflow-wrap:anywhere}h1,h2,h3{line-height:1.3;break-after:avoid}h2{break-before:page}p{orphans:2;widows:2}img{max-width:100%;height:auto}figure{margin:1em 0}figcaption{font-size:.85em}table{border-collapse:collapse;width:100%;font-size:.9em}th,td{border-bottom:1px solid #899;padding:.4em;text-align:left}pre{white-space:pre-wrap;overflow-wrap:anywhere}code{font-family:monospace;font-size:.9em}blockquote,aside{border-left:2px solid #688;padding-left:.8em}a{color:#17626b}.epub-equation{max-width:100%;vertical-align:middle}.epub-lab-note{font-size:.85em;font-style:italic}nav ol{padding-left:1.5em}"""


def q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def append_text(element: ET.Element, text: str) -> None:
    if len(element):
        child = element[-1]
        child.tail = (child.tail or "") + text
    else:
        element.text = (element.text or "") + text


class BookParser(HTMLParser):
    """Parse emitted HTML, keeping content but removing executable controls."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = ET.Element(q(XHTML, "div"))
        self.stack = [("root", self.root)]
        self.in_body = False
        self.skipping = 0

    def handle_starttag(self, tag, attributes):
        if tag == "body":
            self.in_body = True
            return
        if not self.in_body:
            return
        if self.skipping:
            if tag not in VOID:
                self.skipping += 1
            return
        if tag in SKIP:
            if tag not in VOID:
                self.skipping = 1
            return
        parent = self.stack[-1][1]
        ns = SVG if tag == "svg" or parent.tag.startswith("{" + SVG + "}") else MATH if tag == "math" or parent.tag.startswith("{" + MATH + "}") else XHTML
        mapped = "span" if tag == "mjx-container" else "div" if tag in {"details", "summary"} else tag
        attrs = {}
        lab = False
        for key, value in attributes:
            if key == "data-book-lab":
                lab = True
            if key.startswith("v-") or (tag == "mjx-container" and key in {"jax", "display", "tabindex"}):
                continue
            if key == "style":
                value = re.sub(r"(?:^|;)\s*direction\s*:[^;]*(?:;|$)", ";", value or "")
            if ns == XHTML and tag == "img" and key in {"width", "height"} and value:
                value = str(round(float(value)))
            if key.startswith(("on", "data-")) or key in {"hidden", "disabled", "loading", "xmlns", "xmlns:xlink", "v-book-motion", "v-book-lab", "aria-live", "aria-pressed"}:
                continue
            key = q(XLINK, key[6:]) if key.startswith("xlink:") else q("http://www.w3.org/XML/1998/namespace", "lang") if key == "xml:lang" else SVG_CASE.get(key, key) if ns == SVG else key
            attrs[key] = value if value is not None else key
        element = ET.SubElement(parent, q(ns, mapped), attrs)
        if lab:
            ET.SubElement(element, q(XHTML, "p"), {"class": "epub-lab-note"}).text = "静态电子书保留本节公式、示意图与默认输出；参数交互请在在线版或配套 PC 代码中复算。本页不执行控制脚本。"
        if tag not in VOID:
            self.stack.append((tag, element))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "body":
            self.in_body = False
            return
        if not self.in_body or tag in VOID:
            return
        if self.skipping:
            self.skipping -= 1
            return
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if self.in_body and not self.skipping:
            append_text(self.stack[-1][1], data)


def xml_bytes(element: ET.Element) -> bytes:
    return ET.tostring(element, encoding="utf-8", xml_declaration=True)


def light_svg(payload: bytes) -> bytes:
    """EPUB diagrams use the light palette, without browser-only theme media blocks."""
    document = ET.fromstring(payload)
    for element in document.iter(q(SVG, "style")):
        css = element.text or ""
        while match := re.search(r"@media\b[^{}]*\{", css):
            depth, end = 1, match.end()
            while end < len(css) and depth:
                depth += (css[end] == "{") - (css[end] == "}")
                end += 1
            css = css[:match.start()] + css[end:]
        element.text = css
    return xml_bytes(document)


def serialize_svg(element: ET.Element) -> bytes:
    # Local equation references stay local to the extracted SVG file.
    element.attrib.setdefault("version", "1.1")
    return xml_bytes(element)


def package_html(source: str, output: Path, metadata: dict) -> None:
    parser = BookParser()
    parser.feed(source)
    assets: dict[str, tuple[bytes, str]] = {}

    def asset(payload: bytes, extension: str, mime: str) -> str:
        name = f"assets/{hashlib.sha256(payload).hexdigest()[:24]}.{extension}"
        assets[name] = (payload, mime)
        return name

    def normalize(parent):
        for child in list(parent):
            if child.tag == q(XHTML, "figure"):
                # EPUB's figure content model allows its caption only first or last.
                for caption in list(child):
                    if caption.tag == q(XHTML, "figcaption"):
                        child.remove(caption)
                        child.append(caption)
            if child.tag == q(SVG, "svg"):
                # Preserve CSS em sizing for inline MathJax equations.
                width = child.attrib.get("width", "")
                # MathJax expresses size in ex/em so equations follow the text size.
                # Without it, SVG's default intrinsic viewport can stretch a tiny symbol.
                style = child.attrib.get("style", "")
                if re.fullmatch(r"[\d.]+(?:ex|em|px)", width):
                    style += f";width:{width};height:auto;"
                attrs = {"src": asset(serialize_svg(child), "svg", "image/svg+xml"),
                         "alt": child.attrib.get("aria-label", "公式或机制示意图"),
                         "class": "epub-equation", "style": style}
                image = ET.Element(q(XHTML, "img"), attrs)
                image.tail = child.tail
                parent[list(parent).index(child)] = image
                continue
            if child.tag == q(XHTML, "img"):
                src = child.attrib.get("src", "")
                match = re.fullmatch(r"data:(image/[\w.+-]+);base64,([\s\S]+)", src)
                if not match:
                    raise ValueError(f"EPUB offline image is not embedded: {src}")
                mime, encoded = match.groups()
                payload = base64.b64decode(encoded, validate=True)
                if mime == "image/webp":
                    from PIL import Image
                    with Image.open(BytesIO(payload)) as image:
                        image.seek(0)
                        stream = BytesIO()
                        image.convert("RGB").save(stream, format="PNG")
                        payload = stream.getvalue()
                    mime = "image/png"
                if mime == "image/svg+xml":
                    payload = light_svg(payload)
                extension = {"image/svg+xml": "svg", "image/png": "png", "image/jpeg": "jpg"}.get(mime)
                if extension is None:
                    raise ValueError(f"EPUB image media type is unsupported: {mime}")
                child.set("src", asset(payload, extension, mime))
            normalize(child)
    normalize(parser.root)
    html = ET.Element(q(XHTML, "html"), {"lang": "zh-CN", q("http://www.w3.org/XML/1998/namespace", "lang"): "zh-CN"})
    head = ET.SubElement(html, q(XHTML, "head"))
    ET.SubElement(head, q(XHTML, "title")).text = metadata["title"]
    ET.SubElement(head, q(XHTML, "link"), {"rel": "stylesheet", "type": "text/css", "href": "book.css"})
    body = ET.SubElement(html, q(XHTML, "body"))
    body.text = parser.root.text
    body.extend(list(parser.root))
    headings = [el for el in body.iter() if local(el.tag) in {"h1", "h2"} and el.get("id")]
    if not headings:
        raise ValueError("EPUB has no navigable chapter headings")
    nav = ET.Element(q(XHTML, "html"), {"lang": "zh-CN"})
    nav_head = ET.SubElement(nav, q(XHTML, "head"))
    ET.SubElement(nav_head, q(XHTML, "title")).text = "目录"
    nav_body = ET.SubElement(nav, q(XHTML, "body"))
    toc = ET.SubElement(nav_body, q(XHTML, "nav"), {q(EPUB, "type"): "toc", "id": "toc"})
    ET.SubElement(toc, q(XHTML, "h1")).text = "目录"
    items = ET.SubElement(toc, q(XHTML, "ol"))
    for heading in headings:
        li = ET.SubElement(items, q(XHTML, "li"))
        ET.SubElement(li, q(XHTML, "a"), {"href": f"book.xhtml#{heading.get('id')}"}).text = "".join(heading.itertext()).strip()
    container = ET.Element("container", {"xmlns": "urn:oasis:names:tc:opendocument:xmlns:container", "version": "1.0"})
    rootfiles = ET.SubElement(container, "rootfiles")
    ET.SubElement(rootfiles, "rootfile", {"full-path": "EPUB/package.opf", "media-type": "application/oebps-package+xml"})
    package = ET.Element(q(OPF, "package"), {"version": "3.0", "unique-identifier": "book-id"})
    meta = ET.SubElement(package, q(OPF, "metadata"))
    ET.SubElement(meta, q(DC, "identifier"), {"id": "book-id"}).text = f"urn:bms-z:book:{metadata['version']}"
    ET.SubElement(meta, q(DC, "title")).text = metadata["title"]
    ET.SubElement(meta, q(DC, "creator")).text = metadata.get("author", "BMS-Z contributors")
    ET.SubElement(meta, q(DC, "language")).text = "zh-CN"
    ET.SubElement(meta, q(DC, "rights")).text = metadata.get("license", "CC BY-SA 4.0；第三方图片按原授权")
    ET.SubElement(meta, q(OPF, "meta"), {"property": "dcterms:modified"}).text = "2026-11-07T00:00:00Z"
    manifest = ET.SubElement(package, q(OPF, "manifest"))
    ET.SubElement(manifest, q(OPF, "item"), {"id": "book", "href": "book.xhtml", "media-type": "application/xhtml+xml"})
    ET.SubElement(manifest, q(OPF, "item"), {"id": "nav", "href": "nav.xhtml", "media-type": "application/xhtml+xml", "properties": "nav"})
    ET.SubElement(manifest, q(OPF, "item"), {"id": "css", "href": "book.css", "media-type": "text/css"})
    for index, (name, (_, mime)) in enumerate(sorted(assets.items())):
        ET.SubElement(manifest, q(OPF, "item"), {"id": f"asset-{index}", "href": name, "media-type": mime})
    spine = ET.SubElement(package, q(OPF, "spine"))
    ET.SubElement(spine, q(OPF, "itemref"), {"idref": "book"})
    files = {"META-INF/container.xml": xml_bytes(container), "EPUB/package.opf": xml_bytes(package), "EPUB/book.xhtml": xml_bytes(html), "EPUB/nav.xhtml": xml_bytes(nav), "EPUB/book.css": CSS.encode()}
    files.update({f"EPUB/{name}": data for name, (data, _) in assets.items()})
    problems = validate_files(files)
    if problems:
        raise ValueError("EPUB contract: " + "; ".join(problems[:12]))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".epub.tmp")
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for name, data in [("mimetype", b"application/epub+zip"), *sorted(files.items())]:
                info = zipfile.ZipInfo(name, date_time=(2026, 11, 7, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED
                archive.writestr(info, data)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def validate_files(files: dict[str, bytes]) -> list[str]:
    problems = []
    documents = {}
    ids = {}
    for name, data in files.items():
        if name.endswith((".xhtml", ".svg", ".opf", ".xml")):
            try:
                documents[name] = ET.fromstring(data)
            except ET.ParseError as exc:
                problems.append(f"invalid XML {name}: {exc}")
                continue
            all_ids = [el.get("id") for el in documents[name].iter() if el.get("id")]
            ids[name] = set(all_ids)
            if len(all_ids) != len(ids[name]):
                problems.append(f"duplicate id in {name}")
    for name, doc in documents.items():
        for el in doc.iter():
            for attr in ("href", "src", q(XLINK, "href")):
                target = el.get(attr)
                if not target:
                    continue
                parsed = urlsplit(target)
                if parsed.scheme:
                    if local(el.tag) not in {"a"}:
                        problems.append(f"network or data resource {name}: {target[:100]}")
                    continue
                parts = list(PurePosixPath(name).parent.parts)
                for part in PurePosixPath(unquote(parsed.path)).parts:
                    if part == "..":
                        if parts:
                            parts.pop()
                        else:
                            problems.append(f"escaping target {name}: {target}")
                    elif part != ".":
                        parts.append(part)
                destination = "/".join(parts) if parsed.path else name
                if destination not in files:
                    problems.append(f"missing file {name}: {target}")
                elif parsed.fragment and unquote(parsed.fragment) not in ids.get(destination, set()):
                    problems.append(f"missing fragment {name}: {target}")

    return problems


def validate_epub(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        if archive.infolist()[0].filename != "mimetype" or archive.read("mimetype") != b"application/epub+zip" or archive.infolist()[0].compress_type != zipfile.ZIP_STORED:
            return ["invalid EPUB mimetype entry"]
        return validate_files({name: archive.read(name) for name in archive.namelist() if name != "mimetype"})


def rendered_source(path: Path) -> str:
    """Freeze real default lab diagrams, not empty pre-enhancement SVG tracks."""
    source = path.read_text(encoding="utf-8")
    if 'data-book-lab=' not in source:
        return source
    from build_html import BROWSERS
    browser = next((candidate for candidate in BROWSERS if Path(candidate).is_file()), None)
    browser = browser or next((shutil.which(name) for name in ("google-chrome", "chromium", "msedge") if shutil.which(name)), None)
    if browser is None:
        raise ValueError("EPUB static laboratory diagrams require Chrome/Edge")
    with tempfile.TemporaryDirectory(prefix="bms-epub-browser-", ignore_cleanup_errors=True) as profile:
        result = subprocess.run(
            [browser, "--headless=new", "--disable-gpu", f"--user-data-dir={profile}",
             "--virtual-time-budget=1000", "--dump-dom", path.resolve().as_uri()],
            capture_output=True, encoding="utf-8", errors="replace", check=True, timeout=120,
        )
    if not result.stdout.startswith("<!DOCTYPE html>") and "<html" not in result.stdout[:200]:
        raise ValueError("Browser did not return the rendered standalone book")
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, help="use an explicitly freshly-built HTML edition")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--check", type=Path, help="validate an existing EPUB without rebuilding")
    args = parser.parse_args()
    if args.check:
        problems = validate_epub(args.check)
        if problems:
            parser.error("; ".join(problems[:12]))
        print(f"PASS: EPUB XML / assets / links ({args.check})")
        return 0
    if args.html:
        source = rendered_source(args.html)
    else:
        with tempfile.TemporaryDirectory(prefix="bms-epub-", ignore_cleanup_errors=True) as work:
            subprocess.run([sys.executable, str(ROOT / "build_html.py"), "--out-dir", work], check=True)
            source = rendered_source(Path(work) / "bms-book.html")
    metadata = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    output = args.out_dir / "bms-book.epub"
    package_html(source, output, metadata)
    print(f"built {output} ({output.stat().st_size} bytes; EPUB3, offline static diagrams)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
