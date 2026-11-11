"""把视觉声明回对到来源小节；示意值必须逐项注明且出现在图内。"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


def source_excerpt(root: Path, reference: str) -> str:
    filename, _, anchor = reference.partition("#")
    path = (root / filename).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"source_facts 必须在项目内: {filename}")
    if not path.is_file():
        raise ValueError(f"source_facts 文件不存在 {filename}")
    text = path.read_text(encoding="utf-8")
    if not anchor:
        return text
    headings = list(re.finditer(r"^(#{1,6})\s+(.+)$", text, re.M))
    for index, heading in enumerate(headings):
        title = heading.group(2).strip()
        if title == anchor or title.startswith(anchor + " "):
            end = next((h.start() for h in headings[index + 1:]
                        if len(h.group(1)) <= len(heading.group(1))), len(text))
            return text[heading.start():end]
    explicit = re.search(r'<a\b[^>]*\bid=["\']' + re.escape(anchor) + r'["\'][^>]*>', text)
    if explicit:
        # 显式锚点紧邻标题，复用标题的小节边界。
        heading = next((h for h in headings if h.start() >= explicit.end()), None)
        if heading:
            return source_excerpt(root, filename + "#" + heading.group(2).strip())
    raise ValueError(f"source_facts 锚点找不到 {anchor!r}")


def number_gaps(tag: str, numbers: list, source: str, visible: str = "") -> list[str]:
    bad = []
    for number in numbers:
        if isinstance(number, dict):
            value = str(number.get("value", ""))
            if (not value or number.get("label") != "示意"
                    or not str(number.get("reason", "")).strip()):
                bad.append(f"{tag}: 示意数值须含 value、label=示意 与 reason")
            elif "示意" not in visible:
                bad.append(f"{tag}: 示意数值 {value!r} 未在图内标注「示意」")
        else:
            value = str(number)
            if re.search(r"\d", value) and value not in source:
                bad.append(f"{tag}: 数值 {value!r} 在来源正文里找不到")
    return bad


def visible_number_gaps(tag: str, visible: str, source: str, declared: list) -> list[str]:
    """额外扫描 SVG 的可见文字，防止 prompt 遗漏数字后绕过事实检查。"""
    token = re.compile(r"(?<![\d.])\d+(?:\.\d+)?")
    values = set(token.findall(visible))
    facts = set(token.findall(source))
    illustrative = {v for entry in declared if isinstance(entry, dict)
                    and entry.get("label") == "示意" and entry.get("reason")
                    for v in token.findall(str(entry.get("value", "")))}
    if "示意" not in visible:
        illustrative = set()
    return [f"{tag}: 图内数值 {value!r} 缺来源或逐项示意声明"
            for value in sorted(values - facts - illustrative)]


def visible_text(path: Path) -> str:
    if not path.is_file() or path.suffix != ".svg":
        return ""
    try:
        tree = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError:
        return ""
    return " ".join("".join(node.itertext()) for node in tree.iter()
                    if node.tag.rsplit("}", 1)[-1] == "text")
