"""以合集身份整理 EPUB 卷首、目录、引用和元数据。"""

from __future__ import annotations

import copy
import posixpath
import re
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

from lxml import etree as ET

from combined_front import (
    TITLE,
    VOL1_TITLE,
    VOL2_TITLE,
    GUIDE,
    colophon_sections,
    cover_png,
    prose_xhtml,
    xhtml,
)

X = "{http://www.w3.org/1999/xhtml}"
OPF = "{http://www.idpf.org/2007/opf}"
D = "{http://purl.org/dc/elements/1.1/}"
OPS = "http://www.idpf.org/2007/ops"
N = "{http://www.daisy.org/z3986/2005/ncx/}"
IDENTIFIER = "urn:uuid:" + str(
    uuid.uuid5(uuid.NAMESPACE_URL, "BMS-Z/from-analog-to-bms/combined")
)
SHARED = dict(
    zip(
        ("00-title", "01-reading-guide", "02-toc", "03-colophon"),
        ("cover.xhtml", "guide.xhtml", "nav.xhtml", "colophon.xhtml"),
        strict=True,
    )
)


def xml(data):
    return ET.fromstring(data, ET.XMLParser(resolve_entities=False, no_network=True))


def serialize(root):
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def normalize_content(files):
    """Migrate legacy XHTML markup while retaining its alignment and text."""
    changes = {"namespaces": 0, "align_attributes": 0}
    legacy = b"http://www.idpf.org/2007/epub"
    for path, data in list(files.items()):
        if not path.endswith(".xhtml"):
            continue
        if legacy in data:
            data = data.replace(legacy, OPS.encode())
            changes["namespaces"] += 1
        root = xml(data)
        for node in root.iter():
            if not isinstance(node.tag, str) or not node.tag.startswith(X):
                continue
            align = node.attrib.pop("align", None)
            if align is None:
                continue
            changes["align_attributes"] += 1
            align = align.lower()
            if align not in {"left", "right", "center", "justify"}:
                raise ValueError(f"Unsupported legacy alignment: {path}: {align}")
            tag = node.tag[len(X) :]
            if tag in {"img", "table"} and align == "center":
                style = "display:block;margin-left:auto;margin-right:auto"
            elif tag in {"img", "table"} and align in {"left", "right"}:
                style = f"float:{align}"
            else:
                style = f"text-align:{align}"
            # Explicit author CSS retains precedence over presentational attributes.
            node.set("style", style + ";" + node.get("style", ""))
        files[path] = serialize(root)
    return changes


def content_properties(data):
    """Manifest declarations describe the actual embedded vocabularies."""
    root = xml(data)
    props = set()
    for namespace, prop in [
        ("http://www.w3.org/2000/svg", "svg"),
        ("http://www.w3.org/1998/Math/MathML", "mathml"),
    ]:
        if any(
            isinstance(e.tag, str) and e.tag.startswith("{" + namespace + "}")
            for e in root.iter()
        ):
            props.add(prop)
    return props


def add_reader_styles(files):
    files["reader.css"] = (
        Path(__file__).with_name("assets") / "epub-reader.css"
    ).read_bytes()
    for path, data in list(files.items()):
        if path.endswith(".xhtml"):
            root = xml(data)
            ET.SubElement(
                root.find(X + "head"),
                X + "link",
                rel="stylesheet",
                type="text/css",
                href=relative(path, "reader.css"),
            )
            files[path] = serialize(root)


def relative(base, target):
    path, sep, anchor = target.partition("#")
    return posixpath.relpath(path, posixpath.dirname(base) or ".") + (
        sep + anchor if sep else ""
    )


def resolve(base, href):
    u = urlsplit(href)
    if u.scheme or u.netloc:
        return None
    path = (
        posixpath.normpath(posixpath.join(posixpath.dirname(base), unquote(u.path)))
        if u.path
        else base
    )
    return path + ("#" + unquote(u.fragment) if u.fragment else "")


def chapter_targets(files):
    """由现成文档的真实标题/ID建立源文名映射，不猜测 ch-N 偏移。"""
    targets = {}
    for path in files:
        if path.startswith("v1/text/") and path.endswith(".xhtml"):
            stem = re.sub(r"^\d+-", "", Path(path).stem)
            targets[stem + ".md"] = path
    root = xml(files["v2/book.xhtml"])
    chapters = {}
    for node in root.iter(X + "h2"):
        match = re.match(r"第\s*(\d+)\s*章", "".join(node.itertext()))
        if match and node.get("id"):
            chapters[int(match[1])] = "v2/book.xhtml#" + node.get("id")
    source_dir = Path(__file__).resolve().parents[1] / "bms-book/book"
    for source in source_dir.glob("*.md"):
        match = re.match(r"(\d+)-", source.name)
        if match and int(match[1]) in chapters:
            targets[source.name] = chapters[int(match[1])]
    return targets


def rewrite_links(files, redirects, targets):
    converted = []
    for path, data in list(files.items()):
        if not path.endswith((".xhtml", ".ncx")):
            continue
        root, changed = xml(data), False
        for node in root.iter():
            for attr in ("href", "src"):
                value = node.get(attr)
                if not value:
                    continue
                target = resolve(path, value)
                dest = redirects.get(target)
                if not dest and target:
                    dest = redirects.get(target.split("#")[0])
                parsed = urlsplit(value)
                decoded = unquote(parsed.path)
                cross = "/bms-book/book/" in decoded or "/analog/docs/" in decoded
                if cross and attr == "href":
                    name = posixpath.basename(decoded)
                    dest = targets.get(name)
                    if dest is None:
                        raise ValueError(f"跨卷引用无合集目标: {path}: {value}")
                    if parsed.fragment:
                        fragment = unquote(parsed.fragment)
                        dest_path = dest.split("#")[0]
                        ids = {e.get("id") for e in xml(files[dest_path]).iter()}
                        candidates = [fragment, Path(name).stem + "--" + fragment]
                        found = next(
                            (candidate for candidate in candidates if candidate in ids),
                            None,
                        )
                        if not found:
                            raise ValueError(f"跨卷锚点未解析: {path}: {value}")
                        dest = dest_path + "#" + found
                    converted.append(
                        {"source": path, "original": value, "target": dest}
                    )
                if dest:
                    node.set(attr, relative(path, dest))
                    changed = True
        if changed:
            files[path] = serialize(root)
    return converted


def nav_list(data, prefix, removed):
    root = xml(data)
    nav = next(root.iter(X + "nav"))
    block = copy.deepcopy(nav.find(X + "ol"))
    for a in list(block.iter(X + "a")):
        target = resolve(prefix + "nav.xhtml", a.get("href"))
        if target and target.split("#")[0] in removed:
            parent = a.getparent()
            parent.getparent().remove(parent)
        elif target:
            a.set("href", target)
    # 清除仅包含共享卷首的空目录分组。
    for li in reversed(list(block.iter(X + "li"))):
        if not list(li.iter(X + "a")) and li.getparent() is not None:
            li.getparent().remove(li)
    return block


def link_print_references(files):
    """把纸书式的卷次/章节文字引用还原为 EPUB 内链，保留全部原文字。"""
    destinations = {}
    for path, data in files.items():
        if not path.endswith(".xhtml") or not path.startswith(("v1/text/", "v2/book.")):
            continue
        for node in xml(data).iter():
            # Volume I's chapter is the document h1; quiz subsections reuse
            # chapter numbers in h2 and must never replace the body destination.
            heading = X + ("h1" if path.startswith("v1/") else "h2")
            if node.tag != heading:
                continue
            match = re.match(r"第\s*(\d+)\s*章", "".join(node.itertext()))
            if match:
                key = ("一" if path.startswith("v1/") else "二", match[1])
                if key in destinations:
                    raise ValueError(f"Ambiguous chapter destination: {key}: {path}")
                destinations[key] = path + (
                    "#" + node.get("id") if node.get("id") else ""
                )
    pattern = re.compile(r"卷([一二])\s*·\s*第\s*(\d+)\s*章(?:《[^》]+》)?")
    count = 0
    for path, data in list(files.items()):
        if not path.endswith(".xhtml"):
            continue
        root = xml(data)
        changed = False
        for node in list(root.iter()):
            if not isinstance(node.tag, str):
                continue
            for attr in ("text", "tail"):
                value = getattr(node, attr)
                if not value:
                    continue
                parent = node if attr == "text" else node.getparent()
                if parent is None:
                    continue
                if any(
                    e.tag
                    in {X + t for t in ("a", "code", "pre", "style", "script", "title")}
                    for e in [parent, *parent.iterancestors()]
                ):
                    continue
                matches = list(pattern.finditer(value))
                if not matches:
                    continue
                index = 0 if attr == "text" else parent.index(node) + 1
                setattr(node, attr, value[: matches[0].start()])
                for i, match in enumerate(matches):
                    target = destinations.get((match[1], match[2]))
                    if target is None:
                        raise ValueError(f"文字跨卷引用无目标: {match[0]}")
                    a = ET.Element(X + "a", href=relative(path, target))
                    a.text = match[0]
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(value)
                    a.tail = value[match.end() : end]
                    parent.insert(index, a)
                    index += 1
                    count += 1
                changed = True
        if changed:
            files[path] = serialize(root)
    return count


def make_nav(ol1, ol2):
    root = xml(xhtml(TITLE, ""))
    body = root.find(X + "body")
    # 卷首入口放在 toc 之外；toc 中仍以两卷为两个顶层组。
    p = ET.SubElement(body, X + "p")
    for target, label in [
        ("cover.xhtml", "合集封面"),
        ("guide.xhtml", "两卷怎么读"),
        ("lab.xhtml", "三次观察，一张手记"),
        ("colophon.xhtml", "版本、许可与勘误"),
    ]:
        a = ET.SubElement(p, X + "a", href=target)
        a.text, a.tail = label, "　"
    nav = ET.SubElement(body, X + "nav", {f"{{{OPS}}}type": "toc", "id": "toc"})
    ET.SubElement(nav, X + "h1").text = "两卷总目录"
    top = ET.SubElement(nav, X + "ol")
    for title, ol in [(VOL1_TITLE, ol1), (VOL2_TITLE, ol2)]:
        li = ET.SubElement(top, X + "li")
        ET.SubElement(li, X + "span").text = title
        li.append(ol)
    return serialize(root)


def validate_chapter_references(documents):
    """An existing anchor is insufficient: numbered references must land on a chapter."""
    checked = 0
    for path, root in documents.items():
        for a in root.iter(X + "a"):
            match = re.match(r"卷([一二])\s*·\s*第\s*(\d+)\s*章", "".join(a.itertext()))
            if not match:
                continue
            destination = resolve(path, a.get("href", ""))
            if not destination:
                raise ValueError(f"Chapter reference is not internal: {path}")
            target_path, _, fragment = destination.partition("#")
            target = documents[target_path]
            volume = "v1/" if match[1] == "一" else "v2/"
            heading = X + ("h1" if match[1] == "一" else "h2")
            nodes = [
                e
                for e in target.iter(heading)
                if not fragment or e.get("id") == fragment
            ]
            valid = any(
                re.match(rf"第\s*{int(match[2])}\s*章(?:\s|$)", "".join(e.itertext()))
                for e in nodes
            )
            if volume not in target_path or not valid:
                raise ValueError(
                    f"Chapter reference targets a non-chapter: {path}: {a.text} -> {destination}"
                )
            checked += 1
    return checked


def make_ncx(nav_data):
    root = ET.Element(N + "ncx", nsmap={None: N[1:-1]}, version="2005-1")
    head = ET.SubElement(root, N + "head")
    ET.SubElement(head, N + "meta", name="dtb:uid", content=IDENTIFIER)
    ET.SubElement(ET.SubElement(root, N + "docTitle"), N + "text").text = TITLE
    navmap = ET.SubElement(root, N + "navMap")
    orders = {}
    for index, (target, label) in enumerate(
        [
            ("cover.xhtml", "合集封面"),
            ("guide.xhtml", "两卷怎么读"),
            ("lab.xhtml", "三次观察，一张手记"),
            ("colophon.xhtml", "版本、许可与勘误"),
            ("nav.xhtml", "两卷总目录"),
        ]
        + [
            (a.get("href"), "".join(a.itertext()).replace("\u200b", "").strip())
            for a in xml(nav_data).find(X + "body").find(X + "nav").iter(X + "a")
        ],
        1,
    ):
        order = orders.setdefault(target, len(orders) + 1)
        point = ET.SubElement(
            navmap, N + "navPoint", id=f"np-{index}", playOrder=str(order)
        )
        ET.SubElement(ET.SubElement(point, N + "navLabel"), N + "text").text = label
        ET.SubElement(point, N + "content", src=target)
    return serialize(root)


def build(vol1: Path, vol2: Path, output: Path) -> dict:
    from reading_lab import lab_xhtml

    files, packages = {}, []
    for source, prefix, rootdir, opfname in [
        (vol1, "v1/", "OEBPS/", "content.opf"),
        (vol2, "v2/", "EPUB/", "package.opf"),
    ]:
        with zipfile.ZipFile(source) as archive:
            package = xml(archive.read(rootdir + opfname))
            packages.append((prefix, package))
            for name in archive.namelist():
                if (
                    name.startswith(rootdir)
                    and name != rootdir + opfname
                    and not name.endswith("/")
                ):
                    files[prefix + name[len(rootdir) :]] = archive.read(name)
    targets = chapter_targets(files)
    removed, redirects = (
        set(),
        {"v1/nav.xhtml": "nav.xhtml", "v2/nav.xhtml": "nav.xhtml"},
    )
    for path in list(files):
        for stem, destination in SHARED.items():
            if re.search(r"/\d+-shared-" + re.escape(stem) + r"\.xhtml$", path):
                removed.add(path)
                redirects[path] = destination
    v2 = xml(files["v2/book.xhtml"])
    for section in list(v2.iter(X + "section")):
        sid = section.get("id", "")
        if sid.startswith("shared-") and sid[7:] in SHARED:
            for node in section.iter():
                if node.get("id"):
                    redirects["v2/book.xhtml#" + node.get("id")] = SHARED[sid[7:]]
            section.getparent().remove(section)
    # 原独立卷封面改为简洁的分卷扉页，保留正文的版本与版权页。
    for node in list(v2.iter(X + "header")):
        if "cover" in node.get("class", "").split():
            node.clear()
            ET.SubElement(node, X + "p").text = "从模拟电路到 BMS · 卷 II"
            ET.SubElement(node, X + "h1").text = "BMS 实战"
            ET.SubElement(node, X + "p").text = "从一颗电芯到一套证据链"
    files["v2/book.xhtml"] = serialize(v2)
    nav1 = nav_list(files["v1/nav.xhtml"], "v1/", removed)
    nav2 = nav_list(files["v2/nav.xhtml"], "v2/", removed)
    for path in removed:
        del files[path]
    converted = rewrite_links(files, redirects, targets)
    restored = link_print_references(files)
    files.update(
        {
            "cover.png": cover_png(),
            "cover.xhtml": xhtml(
                "合集封面",
                '<img src="cover.png" alt="从模拟电路到 BMS：两卷合集封面"/>',
            ),
            "guide.xhtml": prose_xhtml("两卷怎么读", GUIDE),
            "lab.xhtml": lab_xhtml(),
            "colophon.xhtml": prose_xhtml("版本、许可与勘误", colophon_sections()),
            "nav.xhtml": make_nav(nav1, nav2),
        }
    )
    files["toc.ncx"] = make_ncx(files["nav.xhtml"])
    normalized = normalize_content(files)
    add_reader_styles(files)
    package = ET.Element(
        OPF + "package",
        nsmap={None: OPF[1:-1], "dc": D[1:-1]},
        attrib={"version": "3.0", "unique-identifier": "pub-id"},
    )
    meta = ET.SubElement(package, OPF + "metadata")
    ET.SubElement(meta, D + "identifier", id="pub-id").text = IDENTIFIER
    ET.SubElement(meta, D + "title").text = TITLE
    ET.SubElement(meta, D + "language").text = "zh-CN"
    ET.SubElement(meta, D + "creator").text = "zhuguang-ZFG 与贡献者"
    ET.SubElement(meta, OPF + "meta", property="dcterms:modified").text = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = ET.SubElement(package, OPF + "manifest")
    spine = ET.SubElement(package, OPF + "spine", toc="combined-ncx")
    for name, mime, prop in [
        ("cover.xhtml", "application/xhtml+xml", ""),
        ("guide.xhtml", "application/xhtml+xml", ""),
        ("lab.xhtml", "application/xhtml+xml", ""),
        ("colophon.xhtml", "application/xhtml+xml", ""),
        ("nav.xhtml", "application/xhtml+xml", "nav"),
        ("cover.png", "image/png", "cover-image"),
        ("toc.ncx", "application/x-dtbncx+xml", ""),
        ("reader.css", "text/css", ""),
    ]:
        iid = (
            "combined-ncx"
            if name == "toc.ncx"
            else "combined-" + name.replace(".", "-")
        )
        attrs = {"id": iid, "href": name, "media-type": mime}
        if prop:
            attrs["properties"] = prop
        ET.SubElement(manifest, OPF + "item", **attrs)
        if name.endswith(".xhtml"):
            ET.SubElement(spine, OPF + "itemref", idref=iid)
    for prefix, source in packages:
        old_items = {}
        for node in source.find(OPF + "manifest"):
            path = prefix + node.get("href")
            old_items[node.get("id")] = path
            if path in removed:
                continue
            item = copy.deepcopy(node)
            item.set("id", prefix[:2] + "_" + node.get("id"))
            item.set("href", path)
            props = set(item.get("properties", "").split()) - {"nav", "cover-image"}
            if path.endswith(".xhtml"):
                props = (props - {"svg", "mathml"}) | content_properties(files[path])
            item.attrib.pop("properties", None)
            if props:
                item.set("properties", " ".join(sorted(props)))
            for attr in ("fallback", "media-overlay"):
                if item.get(attr):
                    item.set(attr, prefix[:2] + "_" + item.get(attr))
            manifest.append(item)
        for node in source.find(OPF + "spine"):
            path = old_items[node.get("idref")]
            if path in removed or path in ("v1/nav.xhtml", "v2/nav.xhtml"):
                continue
            item = copy.deepcopy(node)
            item.set("idref", prefix[:2] + "_" + node.get("idref"))
            spine.append(item)
    files["content.opf"] = serialize(package)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as archive:
        archive.writestr(
            "mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED
        )
        archive.writestr(
            "META-INF/container.xml",
            b'<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
        )
        for path, data in sorted(files.items()):
            archive.writestr("OEBPS/" + path, data)
    return {
        "cross_volume_links": converted,
        "content_normalization": normalized,
        "restored_print_references": restored,
        "removed_shared_documents": sorted(removed),
        "removed_shared_sections": 4,
        "spine_items": len(spine),
        "bytes": output.stat().st_size,
    }


def validate(path: Path) -> dict:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analog/scripts"))
    from epub_validation import validate_epub

    result = validate_epub(path)
    with zipfile.ZipFile(path) as archive:
        result["chapter_references"] = validate_chapter_references(
            {
                name: xml(archive.read(name))
                for name in archive.namelist()
                if name.endswith(".xhtml")
            }
        )
        package = xml(archive.read("OEBPS/content.opf"))
        ncx = xml(archive.read("OEBPS/toc.ncx"))
        identifier = package.find(OPF + "metadata").find(D + "identifier").text
        uid = ncx.find(N + "head").find(N + "meta").get("content")
        if identifier != uid:
            raise ValueError("OPF/NCX 标识不一致")
        orders = {}
        for p in ncx.iter(N + "navPoint"):
            src, order = p.find(N + "content").get("src"), p.get("playOrder")
            if order in orders and orders[order] != src:
                raise ValueError("NCX 顺序冲突")
            orders[order] = src
        covers = [
            i
            for i in package.find(OPF + "manifest")
            if "cover-image" in i.get("properties", "").split()
        ]
        if len(covers) != 1 or covers[0].get("href") != "cover.png":
            raise ValueError("合集封面未正确登记")
        if any(
            "shared-front-page" in e.get("class", "").split()
            for e in xml(archive.read("OEBPS/v2/book.xhtml")).iter()
        ):
            raise ValueError("卷二仍有重复共享卷首")
        for name in archive.namelist():
            if not name.endswith(".xhtml"):
                continue
            for a in xml(archive.read(name)).iter(X + "a"):
                u = urlsplit(a.get("href", ""))
                if u.scheme and (
                    "/bms-book/book/" in unquote(u.path)
                    or "/analog/docs/" in unquote(u.path)
                ):
                    raise ValueError(f"未内联的跨卷引用: {name}")
    return result
