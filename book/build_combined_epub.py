"""合并卷一/卷二两册 EPUB 为《从模拟电路到 BMS》合集。

机制：整树平移——两卷资源子树原样搬进 OEBPS/v1/ 与 OEBPS/v2/，
子树内部相对引用不变（已验证零绝对路径引用）；只合成新 container、
OPF（manifest/spine 合并）、EPUB3 导航与 NCX（两卷目录并列）。

用法：python book/build_combined_epub.py [--check]
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
OUT_DIR = ROOT / "book/dist/combined"
OUT = OUT_DIR / "from-analog-to-bms.epub"

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验已有产物")
    args = ap.parse_args()
    if args.check:
        return check(OUT)
    build()
    return check(OUT)


if __name__ == "__main__":
    sys.exit(main())
