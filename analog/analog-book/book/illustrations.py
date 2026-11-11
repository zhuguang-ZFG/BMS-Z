"""篇首插图加载：安全地内联 static/illustrations/*.svg。"""
from __future__ import annotations

import re

from . import config
from .manifest import BookError

ART_DIR = config.STATIC_DIR / "illustrations"
SAFE_NAME_RE = re.compile(r"^part-(?:i|ii|iii|iv|v)\.svg$")
ACTIVE_TOKENS = (
    "<script", "<style", "<image", "<foreignobject", "<iframe",
    "<object", "<embed", "xlink:", "data:", "@import",
)
EVENT_ATTR_RE = re.compile(r"on[a-z]+\s*=")
HREF_ATTR_RE = re.compile(r"href\s*=")
URL_RE = re.compile(r"https?://[^\"'\s>]+", re.I)
URL_ALLOWED = {"http://www.w3.org/2000/svg"}
CSS_URL_RE = re.compile(r"url\(([^)]*)\)", re.I)
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def part_art(name: str | None) -> str:
    """读取并校验一幅篇首 SVG；名称为空时返回空字符串。"""
    if not name:
        return ""
    if not isinstance(name, str) or not SAFE_NAME_RE.fullmatch(name):
        raise BookError(f"篇首插图文件名不合法: {name!r}")
    path = ART_DIR / name
    if not path.is_file():
        raise BookError(f"缺少篇首插图: {path}")
    svg = path.read_text(encoding="utf-8").strip()
    if not svg.startswith("<svg"):
        raise BookError(f"篇首插图不是 SVG: {path}")
    lowered = svg.lower()
    for token in ACTIVE_TOKENS:
        if token in lowered:
            raise BookError(f"篇首插图含不允许的内容 {token!r}: {path}")
    if HREF_ATTR_RE.search(lowered):
        raise BookError(f"篇首插图含 href 属性: {path}")
    if EVENT_ATTR_RE.search(lowered):
        raise BookError(f"篇首插图含事件属性: {path}")
    urls = {url.lower() for url in URL_RE.findall(svg)}
    if urls - URL_ALLOWED:
        raise BookError(f"篇首插图含外部 URL: {path}")
    for reference in CSS_URL_RE.findall(svg):
        if not reference.strip().startswith("#"):
            raise BookError(f"篇首插图含外部 url(): {path}")
    if CJK_RE.search(svg):
        raise BookError(f"篇首插图只许拉丁文字: {path}")
    return svg
