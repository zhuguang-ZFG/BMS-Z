"""Validate the EPUB package, reading order and every local resource/fragment."""
from __future__ import annotations

import posixpath
import re
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

from lxml import etree as ET

OPF = 'http://www.idpf.org/2007/opf'
XHTML = 'http://www.w3.org/1999/xhtml'
XML_TYPES = {'.xhtml', '.opf', '.ncx', '.svg', '.xml'}
MIMES = {'.xhtml': 'application/xhtml+xml', '.css': 'text/css',
         '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg',
         '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2',
         '.ncx': 'application/x-dtbncx+xml', '.txt': 'text/plain'}


class EpubError(ValueError):
    pass


def resolve_reference(base: str, ref: str) -> tuple[str, str] | None:
    url = urlsplit(ref)
    if url.scheme or url.netloc:
        return None
    path = unquote(url.path)
    if '\\' in path or path.startswith('/'):
        raise EpubError(f'{base}: 非法包内路径 {ref}')
    target = posixpath.normpath(posixpath.join(posixpath.dirname(base), path)) if path else base
    if target == '..' or target.startswith('../'):
        raise EpubError(f'{base}: 引用越出 EPUB {ref}')
    return target, unquote(url.fragment)


def validate_epub(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if not infos or infos[0].filename != 'mimetype' or infos[0].compress_type != zipfile.ZIP_STORED:
            raise EpubError('mimetype 必须是首个条目且 STORED')
        if archive.read('mimetype') != b'application/epub+zip':
            raise EpubError('mimetype 内容错误')
        counts = Counter(info.filename for info in infos)
        if any(n != 1 for n in counts.values()):
            raise EpubError('ZIP 含重复条目')
        names = set(counts)
        if archive.testzip() is not None:
            raise EpubError('ZIP CRC 校验失败')
        trees, ids = {}, {}
        parser = ET.XMLParser(resolve_entities=False, no_network=True)
        for name in names:
            if name.startswith('/') or '\\' in name or '..' in name.split('/'):
                raise EpubError(f'非法包条目: {name}')
            if Path(name).suffix not in XML_TYPES:
                continue
            try:
                tree = ET.fromstring(archive.read(name), parser)
            except ET.XMLSyntaxError as exc:
                raise EpubError(f'{name}: XML 无法解析: {exc}') from exc
            trees[name] = tree
            values = [v for element in tree.iter() for v in [element.get('id')] if v]
            if len(set(values)) != len(values):
                raise EpubError(f'{name}: 重复 id')
            ids[name] = set(values)
        container = trees.get('META-INF/container.xml')
        if container is None:
            raise EpubError('缺 META-INF/container.xml')
        roots = container.findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
        if len(roots) != 1:
            raise EpubError('container 必须指定一个 OPF')
        opf_name = roots[0].get('full-path')
        if opf_name not in trees:
            raise EpubError(f'container 指定的 OPF 不存在: {opf_name}')
        package = trees[opf_name]
        items, declared, nav = {}, set(), []
        for item in package.findall(f'{{{OPF}}}manifest/{{{OPF}}}item'):
            iid, href = item.get('id'), item.get('href')
            if not iid or not href or iid in items:
                raise EpubError('manifest 缺 id/href 或 id 重复')
            target = resolve_reference(opf_name, href)
            if target is None or target[1] or target[0] not in names:
                raise EpubError(f'OPF 引用缺失或非法: {href}')
            name = target[0]
            if name in declared:
                raise EpubError(f'资源被重复声明: {name}')
            declared.add(name)
            expected = MIMES.get(Path(name).suffix)
            if expected and item.get('media-type') != expected:
                raise EpubError(f'{name}: media-type 与文件类型不一致')
            if 'nav' in item.get('properties', '').split():
                nav.append(name)
            items[iid] = name
        if len(nav) != 1:
            raise EpubError('manifest 必须声明一个导航文档')
        if nav[0] not in trees:
            raise EpubError('导航不是有效 XHTML')
        spine = []
        for item in package.findall(f'{{{OPF}}}spine/{{{OPF}}}itemref'):
            iid = item.get('idref')
            if iid not in items or not items[iid].endswith('.xhtml'):
                raise EpubError(f'spine 引用无效: {iid}')
            spine.append(items[iid])
        if not spine or len(set(spine)) != len(spine):
            raise EpubError('spine 为空或含重复章节')
        count = 0

        def check_ref(base: str, ref: str, embedded: bool = False) -> None:
            nonlocal count
            target = resolve_reference(base, ref)
            if target is None:
                if embedded:
                    raise EpubError(f'{base}: 资源必须离线可用: {ref}')
                return
            name, fragment = target
            if name not in names:
                raise EpubError(f'{base}: 内部引用缺失 {ref}')
            if name not in declared:
                raise EpubError(f'{base}: 引用未登记资源 {ref}')
            if fragment and fragment not in ids.get(name, set()):
                raise EpubError(f'{base}: 内部锚点缺失 {ref}')
            count += 1

        for name in declared:
            if name.endswith('.css'):
                css = archive.read(name).decode('utf-8')
                for match in re.finditer(r'url\(\s*[\"\']?([^\)\"\']+)', css):
                    check_ref(name, match.group(1).strip(), True)
            tree = trees.get(name)
            if tree is None:
                continue
            for element in tree.iter():
                if not isinstance(element.tag, str):
                    continue
                tag = ET.QName(element).localname
                if tag == 'script':
                    raise EpubError(f'{name}: EPUB 不得依赖脚本')
                for attr, ref in element.attrib.items():
                    local = ET.QName(attr).localname
                    if local in ('href', 'src'):
                        check_ref(name, ref, tag not in ('a', 'link'))
                if tag == 'img' and not element.get('alt', '').strip():
                    raise EpubError(f'{name}: 图片缺 alt')
        # Each chapter must be reachable from the navigation, not just in the spine.
        targets = {resolve_reference(nav[0], ref)[0]
                   for ref in trees[nav[0]].xpath('//*[local-name()="a"]/@href')
                   if resolve_reference(nav[0], ref) is not None}
        missing = set(spine) - targets - set(nav)
        if missing:
            raise EpubError(f'目录缺少章节: {sorted(missing)}')
        return {'chapters': len(spine) - (1 if nav[0] in spine else 0),
                'resources': len(declared), 'local_references': count}
