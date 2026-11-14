"""合并卷一/卷二两册成品为《从模拟电路到 BMS》合集（EPUB + A4 PDF）。

EPUB：整树平移——两卷资源子树原样搬进 OEBPS/v1/ 与 OEBPS/v2/，
子树内部相对引用不变（已验证零绝对路径引用）；只合成新 container、
OPF（manifest/spine 合并）、EPUB3 导航与 NCX（两卷目录并列）。

PDF：按页序拼接两卷 A4 PDF，书签以「卷一」「卷二」为顶层层级，
页码沿用各卷印刷页（不重编），元数据与目录改成丛书身份。

用法：python book/build_combined.py [--check]
"""

from __future__ import annotations

import argparse
import re
import sys
import uuid
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

MIMETYPE = "application/epub+zip"
NS_OPF = "http://www.idpf.org/2007/opf"
NS_DC = "http://purl.org/dc/elements/1.1/"


def read_member(z: zipfile.ZipFile, name: str) -> bytes:
    return z.read(name)


def tree_entries(z: zipfile.ZipFile, root_prefix: str, skip: set[str]) -> dict[str, bytes]:
    """取 root_prefix 下全部条目（去前缀），跳过 skip 集合（原始完整名）。"""
    out = {}
    for name in z.namelist():
        if name in skip:
            continue
        if name.startswith(root_prefix):
            out[name[len(root_prefix):]] = z.read(name)
    return out


def find_nav_item(opf_text: str) -> str | None:
    """从 opf 文本找 properties="nav" 的 item href（兼容 ns0: 前缀）。"""
    for m in re.finditer(r"<(?:\w+:)?item\b[^>]*>", opf_text):
        tag = m.group(0)
        if 'properties="nav"' in tag:
            h = re.search(r'href="([^"]+)"', tag)
            if h:
                return h.group(1)
    return None


def extract_nav_ol(nav_bytes: bytes) -> str:
    """从 EPUB3 nav 文档提取目录 <ol> 块（兼容 ns 前缀序列化产物）。"""
    text = nav_bytes.decode("utf-8")
    m = re.search(r"<(?:\w+:)?ol[^>]*>.*</(?:\w+:)?ol>", text, re.S)
    if not m:
        raise SystemExit("nav 文档里找不到 <ol>")
    block = m.group(0)
    # 去前缀化：合集导航模板只声明默认命名空间，嵌入块须去掉 html:/ns1: 前缀
    block = re.sub(r"<(/?)html:", r"<\1", block)
    block = re.sub(r"\bns1:type=", 'epub:type=', block)
    return block


def shift_hrefs(block: str, prefix: str) -> str:
    """给块内相对 href 加前缀（外链/锚点不动）。"""
    def sub(m: re.Match) -> str:
        href = m.group(1)
        if href.startswith(("http://", "https://", "#", "mailto:")):
            return m.group(0)
        return f'href="{prefix}{href}"'
    return re.sub(r'href="([^"]+)"', sub, block)


def merge_opf(v1_opf: str, v2_opf: str, new_id: str) -> tuple[str, str, str]:
    """返回 (新 opf 文本, 卷一 spine itemref 块, 卷二 spine itemref 块)。"""
    def items(opf: str) -> list[str]:
        return [m.group(0) for m in re.finditer(r"<(?:\w+:)?item\b[^>]*>", opf)]

    def shift_items(opf: str, id_p: str, href_p: str) -> list[str]:
        out = []
        for tag in items(opf):
            if 'properties="nav"' in tag:
                # 原 nav 仍被 spine 引用，须保留条目；仅去除 nav 属性，
                # 合集导航由 combined-nav 承担
                tag = re.sub(r'\s*properties="nav"', '', tag)
            tag = re.sub(r"<(/?)(?:\w+:)?item\b", r"<\1item", tag)
            tag = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{id_p}{m.group(1)}"', tag)
            tag = re.sub(r'\bhref="([^"]+)"', lambda m: f'href="{href_p}{m.group(1)}"', tag)
            out.append(tag)
        return out

    v1_manifest = shift_items(v1_opf, "v1_", "v1/")
    v2_manifest = shift_items(v2_opf, "v2_", "v2/")
    manifest_xml = "\n    ".join(v1_manifest + v2_manifest)
    manifest_xml += (
        '\n    <item id="combined-nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
        '\n    <item id="combined-ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
    )

    def spine_refs(opf: str, id_p: str) -> list[str]:
        m = re.search(r"<(?:\w+:)?spine\b[^>]*>(.*?)</(?:\w+:)?spine>", opf, re.S)
        if not m:
            raise SystemExit("opf 里找不到 spine")
        refs = []
        for r in re.finditer(r"<(?:\w+:)?itemref\b[^>]*>", m.group(1)):
            ref = re.sub(r"<(/?)(?:\w+:)?itemref\b", r"<\1itemref", r.group(0))
            refs.append(re.sub(r'\bidref="([^"]+)"', lambda mm: f'idref="{id_p}{mm.group(1)}"', ref))
        return refs

    v1_refs = spine_refs(v1_opf, "v1_")
    v2_refs = spine_refs(v2_opf, "v2_")

    opf_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="{NS_OPF}" unique-identifier="pub-id" version="3.0" xml:lang="zh-CN">
  <metadata xmlns:dc="{NS_DC}">
    <dc:identifier id="pub-id">urn:uuid:{new_id}</dc:identifier>
    <dc:title>{TITLE}</dc:title>
    <dc:language>zh-CN</dc:language>
    <dc:creator>zhuguang-ZFG</dc:creator>
    <meta property="dcterms:modified">2026-11-13T00:00:00Z</meta>
  </metadata>
  <manifest>
    {manifest_xml}
  </manifest>
  <spine toc="combined-ncx">
    {' '.join(v1_refs)}
    {' '.join(v2_refs)}
  </spine>
</package>
'''
    return opf_xml, " ".join(v1_refs), " ".join(v2_refs)


def merge_ncx(v1_ncx: bytes, v2_nav_ol: str) -> str:
    text = v1_ncx.decode("utf-8")
    m = re.search(r"<navMap>(.*?)</navMap>", text, re.S)
    if not m:
        raise SystemExit("卷一 ncx 里找不到 navMap")
    v1_map = m.group(1)
    # 卷一 navPoint id 加前缀防冲突，src 加 v1/ 前缀
    v1_map = re.sub(r'\bid="([^"]+)"', lambda mm: f'id="v1-{mm.group(1)}"', v1_map)
    v1_map = re.sub(r'\bsrc="([^"]+)"', lambda mm: f'src="v1/{mm.group(1)}"', v1_map)

    # 卷二：从 nav 的 ol 提取条目生成 navPoint
    points = []
    for idx, am in enumerate(re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', v2_nav_ol, re.S), 1):
        href, label = am.group(1), re.sub(r"<[^>]+>", "", am.group(2)).strip()
        label = (label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        points.append(f'<navPoint id="v2-np-{idx}" playOrder="{idx + 100000}"><navLabel><text>{label}</text></navLabel><content src="v2/{href}"/></navPoint>')
    v2_map = "\n    ".join(points)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh-CN">
  <head><meta name="dtb:uid" content="combined"/></head>
  <docTitle><text>{TITLE}</text></docTitle>
  <navMap>
    <navPoint id="vol1" playOrder="1"><navLabel><text>{VOL1_TITLE}</text></navLabel><content src="v1/nav.xhtml"/>
      {v1_map}
    </navPoint>
    <navPoint id="vol2" playOrder="2"><navLabel><text>{VOL2_TITLE}</text></navLabel><content src="v2/nav.xhtml"/>
      {v2_map}
    </navPoint>
  </navMap>
</ncx>
'''


def build() -> Path:
    if not VOL1.is_file() or not VOL2.is_file():
        raise SystemExit("缺分卷 EPUB 产物，先 build.py epub --volume I/II")
    z1 = zipfile.ZipFile(VOL1)
    z2 = zipfile.ZipFile(VOL2)

    v1_opf = read_member(z1, "OEBPS/content.opf").decode("utf-8")
    v2_opf_name = "EPUB/package.opf"
    v2_opf = read_member(z2, v2_opf_name).decode("utf-8")
    v2_nav_href = find_nav_item(v2_opf)
    if not v2_nav_href:
        raise SystemExit("卷二 OPF 找不到 nav item")
    v2_nav_path = "EPUB/" + v2_nav_href

    new_id = str(uuid.uuid4())

    # 原 nav/ncx 仍被各卷 spine 与 navMap 引用，保留落盘；合集用自己的三件套
    skip1 = {"mimetype", "META-INF/container.xml", "OEBPS/content.opf"}
    skip2 = {"mimetype", "META-INF/container.xml", v2_opf_name}
    tree1 = tree_entries(z1, "OEBPS/", skip1)
    tree2 = tree_entries(z2, "EPUB/", skip2)

    opf_xml, _, _ = merge_opf(v1_opf, v2_opf, new_id)

    v1_nav_ol = shift_hrefs(extract_nav_ol(read_member(z1, "OEBPS/nav.xhtml")), "v1/")
    v2_nav_ol_raw = extract_nav_ol(read_member(z2, v2_nav_path))
    v2_nav_ol = shift_hrefs(v2_nav_ol_raw, "v2/")
    ncx_xml = merge_ncx(read_member(z1, "OEBPS/toc.ncx"), v2_nav_ol_raw)

    nav_xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">
<head><title>{TITLE}</title></head>
<body>
<nav epub:type="toc" id="toc">
<h1>{TITLE}</h1>
<h2>{VOL1_TITLE}</h2>
{v1_nav_ol}
<h2>{VOL2_TITLE}</h2>
{v2_nav_ol}
</nav>
</body>
</html>
'''

    container_xml = '''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>
'''

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), MIMETYPE, compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container_xml)
        z.writestr("OEBPS/content.opf", opf_xml)
        z.writestr("OEBPS/nav.xhtml", nav_xhtml)
        z.writestr("OEBPS/toc.ncx", ncx_xml)
        for rel, data in tree1.items():
            z.writestr("OEBPS/v1/" + rel, data)
        for rel, data in tree2.items():
            z.writestr("OEBPS/v2/" + rel, data)
    z1.close()
    z2.close()
    print(f"combined epub -> {OUT} ({OUT.stat().st_size} bytes)")
    return OUT


def check(path: Path) -> int:
    """结构校验：zip 序、XML 合法性、spine↔manifest、manifest href 落盘。"""
    import xml.etree.ElementTree as ET

    z = zipfile.ZipFile(path)
    names = set(z.namelist())
    assert z.namelist()[0] == "mimetype", "mimetype 必须是首个条目"
    assert z.read("mimetype") == MIMETYPE.encode()
    opf = z.read("OEBPS/content.opf").decode("utf-8")
    ET.fromstring(opf)
    ET.fromstring(z.read("OEBPS/nav.xhtml"))
    ET.fromstring(z.read("OEBPS/toc.ncx"))
    ids = set(re.findall(r'<(?:\w+:)?item\b[^>]*\bid="([^"]+)"', opf))
    hrefs = dict(re.findall(r'<(?:\w+:)?item\b[^>]*\bid="([^"]+)"[^>]*\bhref="([^"]+)"', opf))
    spine_ids = re.findall(r'<(?:\w+:)?itemref\b[^>]*\bidref="([^"]+)"', opf)
    missing_ref = [s for s in spine_ids if s not in ids]
    missing_file = [h for h in hrefs.values() if ("OEBPS/" + h) not in names]
    ncx = z.read("OEBPS/toc.ncx").decode("utf-8")
    ncx_src = re.findall(r'<content\b[^>]*\bsrc="([^"]+)"', ncx)
    ncx_missing = [s for s in ncx_src if ("OEBPS/" + s.split("#")[0]) not in names]
    z.close()
    problems = []
    if missing_ref:
        problems.append(f"spine 悬空 idref: {missing_ref[:5]}")
    if missing_file:
        problems.append(f"manifest 缺文件: {missing_file[:5]}")
    if ncx_missing:
        problems.append(f"ncx 悬空 src: {ncx_missing[:5]}")
    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    print(f"PASS: 合集 EPUB 结构校验（{len(spine_ids)} spine 项、{len(hrefs)} manifest 项、{len(ncx_src)} ncx 点全落盘）")
    return 0


SHARED_HEAD = "从模拟电路到BMS"
SHARED_TAIL = "版本、许可与勘误"


def _flat_text(doc, index: int) -> str:
    return re.sub(r"\s+", "", doc[index].get_text())


def _shared_block(doc) -> tuple[int, int]:
    """卷二开头与卷一重复的共享卷首页段（含扉页到版权页），找不到返回空段。"""
    start = None
    for i in range(1, min(doc.page_count, 12)):
        if _flat_text(doc, i).startswith(SHARED_HEAD):
            start = i
            break
    if start is None:
        return (0, -1)
    for j in range(start + 1, min(start + 10, doc.page_count)):
        if _flat_text(doc, j).startswith(SHARED_TAIL):
            return (start, j)
    return (0, -1)


def _collect_links(doc) -> list[tuple[int, dict]]:
    return [(i, link) for i in range(doc.page_count) for link in doc[i].get_links()]


def build_pdf() -> Path:
    """拼接两卷 A4 PDF：共享卷首只留卷一那份，重建页内链接与两卷书签。"""
    import fitz

    if not VOL1_PDF.is_file() or not VOL2_PDF.is_file():
        raise SystemExit("缺分卷 A4 PDF 产物，先 build.py pdf --format a4 --volume I/II")

    with fitz.open(VOL1_PDF) as d1:
        n1 = d1.page_count
        toc1 = d1.get_toc(simple=True)
        links1 = _collect_links(d1)
        out = fitz.open()
        out.insert_pdf(d1, links=0)  # 链接全部自建，避免外链被复制两遍
    with fitz.open(VOL2_PDF) as d2:
        n2 = d2.page_count
        toc2 = d2.get_toc(simple=True)
        links2 = _collect_links(d2)
        skips = _shared_block(d2)
        skipped = set(range(skips[0], skips[1] + 1)) if skips[1] >= skips[0] else set()
        if skipped:
            out.insert_pdf(d2, from_page=0, to_page=skips[0] - 1, links=0)
            out.insert_pdf(d2, from_page=skips[1] + 1, to_page=n2 - 1, links=0)
        else:
            out.insert_pdf(d2, links=0)

    def v2_page(src: int) -> int:
        return n1 + src - sum(1 for s in skipped if s < src)

    outline: list[list] = [[1, VOL1_TITLE, 1]]
    outline += [[min(level + 1, 6), title, page] for level, title, page in toc1]
    outline.append([1, VOL2_TITLE, n1 + 1])
    for level, title, page in toc2:
        if page - 1 in skipped:
            continue
        outline.append([min(level + 1, 6), title, v2_page(page - 1) + 1])

    def copy_link(links: list[tuple[int, dict]], place, resolve) -> int:
        copied = 0
        for src, link in links:
            rect = link.get("from")
            if rect is None or place(src) is None:
                continue
            page = out[place(src)]
            if link.get("kind") == fitz.LINK_URI and link.get("uri"):
                page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": link["uri"]})
                copied += 1
                continue
            target = link.get("page")
            if target is None or target < 0:
                continue
            dest = resolve(target)
            if dest is None:
                continue
            page.insert_link({"kind": fitz.LINK_GOTO, "from": rect, "page": dest,
                              "to": link.get("to") or fitz.Point(0, 0)})
            copied += 1
        return copied

    copied = copy_link(links1, lambda src: src, lambda target: target if target < n1 else None)
    copied += copy_link(links2, lambda src: None if src in skipped else v2_page(src),
                        lambda target: None if target in skipped else v2_page(target))

    out.set_toc(outline)
    out.set_metadata({
        "title": TITLE,
        "author": "zhuguang-ZFG 与贡献者",
        "subject": f"{VOL1_TITLE} + {VOL2_TITLE}；A4 合集，页码沿用各卷印刷页",
        "keywords": "模拟电路, BMS, 电池管理系统, 两卷合集",
        "creator": "book/build_combined.py",
    })
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # 149 MB 的合集不做全量重压缩：卷内流已是各自构建器的成品，
    # deflate/clean 会把保存拖成数十分钟且没有体积收益。
    out.save(OUT_PDF, garbage=0, deflate=False)
    pages = out.page_count
    out.close()

    print(f"combined pdf -> {OUT_PDF} ({OUT_PDF.stat().st_size} bytes, {pages} pages, "
          f"去重 {len(skipped)} 页共享卷首, 重建 {copied} 条链接)")
    return OUT_PDF


def check_pdf(path: Path) -> int:
    """页数=两卷之和减去重复卷首；书签就位；每一条应保留的页内链接逐条对拍源页。"""
    import fitz

    problems: list[str] = []
    with fitz.open(VOL1_PDF) as d1, fitz.open(VOL2_PDF) as d2:
        n1, n2 = d1.page_count, d2.page_count
        skips = _shared_block(d2)
        skipped = set(range(skips[0], skips[1] + 1)) if skips[1] >= skips[0] else set()
        expected = n1 + n2 - len(skipped)

        def v2_map(src: int) -> int:
            return n1 + src - sum(1 for s in skipped if s < src)

        # (合集页, 类型, 目标页/URI, 源矩形, 源目标页文本指纹) —— 重建时应原样出现的链接。
        expected_links: list[tuple[int, int, object, tuple[float, ...], str]] = []
        text_cache: dict[tuple[str, int], str] = {}

        def src_text(tag: str, doc, index: int) -> str:
            key = (tag, index)
            if key not in text_cache:
                text_cache[key] = _flat_text(doc, index)[:40]
            return text_cache[key]

        def collect(doc, count: int, tag: str, place) -> None:
            for src in range(count):
                out_page = place(src)
                if out_page is None:
                    continue
                for link in doc[src].get_links():
                    box = link.get("from")
                    if box is None:
                        continue
                    rect = (box.x0, box.y0, box.x1, box.y1)
                    if link.get("kind") == fitz.LINK_URI and link.get("uri"):
                        expected_links.append((out_page, fitz.LINK_URI, link["uri"], rect, ""))
                        continue
                    target = link.get("page")
                    if target is None or not 0 <= target < count:
                        continue
                    dest = place(target)
                    if dest is None:
                        continue
                    expected_links.append((out_page, fitz.LINK_GOTO, dest, rect,
                                           src_text(tag, doc, target)))

        collect(d1, n1, "v1", lambda i: i)
        collect(d2, n2, "v2", lambda i: None if i in skipped else v2_map(i))

        with fitz.open(path) as doc:
            toc = doc.get_toc(simple=True)
            if doc.page_count != expected:
                problems.append(f"页数 {doc.page_count} != {expected}")
            level1 = [entry for entry in toc if entry[0] == 1]
            if not level1 or level1[0][1:] != [VOL1_TITLE, 1]:
                problems.append(f"首个顶层书签异常：{level1[:1]}")
            if [VOL2_TITLE, n1 + 1] not in [entry[1:] for entry in level1]:
                problems.append(f"卷二顶层书签缺失或页码错：{level1[-1:]}")
            if doc.metadata.get("title") != TITLE:
                problems.append(f"元数据 title={doc.metadata.get('title')!r}")
            if skipped and any(_flat_text(doc, i).startswith(SHARED_TAIL)
                               for i in range(50, min(doc.page_count, n1 + 30))):
                problems.append("卷二仍带共享卷首副本")

            links_by_page: dict[int, list[dict]] = {}
            total = 0
            for page_index in range(doc.page_count):
                for link in doc[page_index].get_links():
                    if link.get("from") is None:
                        continue
                    links_by_page.setdefault(page_index, []).append(link)
                    total += 1
            if total != len(expected_links):
                problems.append(f"页内链接 {total} 条，应保留 {len(expected_links)} 条")

            def same_rect(link: dict, rect: tuple[float, ...]) -> bool:
                box = link.get("from")
                return box is not None and all(
                    abs(a - b) <= 1.0
                    for a, b in zip((box.x0, box.y0, box.x1, box.y1), rect, strict=True))

            verified = 0
            for out_page, kind, payload, rect, want in expected_links:
                bucket = links_by_page.get(out_page, [])
                match = None
                for candidate in bucket:
                    if candidate.get("kind") != kind or not same_rect(candidate, rect):
                        continue
                    if kind == fitz.LINK_URI and candidate.get("uri") == payload:
                        match = candidate
                        break
                    if kind == fitz.LINK_GOTO and candidate.get("page") == payload:
                        match = candidate
                        break
                if match is None:
                    if len(problems) < 8:
                        problems.append(f"缺链接：第 {out_page + 1} 页 → {payload}")
                    continue
                bucket.remove(match)
                if kind == fitz.LINK_GOTO and want and want not in _flat_text(doc, payload):
                    if len(problems) < 8:
                        problems.append(
                            f"链接目标错位：第 {out_page + 1} 页 → 第 {payload + 1} 页 期望 {want!r}")
                    continue
                verified += 1
            if verified != len(expected_links):
                problems.append(f"逐条核实 {verified}/{len(expected_links)} 条链接")

    if problems:
        for problem in problems:
            print("FAIL:", problem)
        return 1
    print(f"PASS: 合集 PDF 结构校验（{n1}+{n2}-{len(skipped)}={expected} 页、"
          f"{len(toc)} 条书签、{verified} 条链接逐条对拍源目标页）")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验已有产物")
    args = ap.parse_args(argv)
    if args.check:
        return check(OUT) | check_pdf(OUT_PDF)
    build()
    build_pdf()
    return check(OUT) | check_pdf(OUT_PDF)


if __name__ == "__main__":
    sys.exit(main())
