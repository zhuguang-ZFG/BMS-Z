"""篇首插图加载：安全地内联 static/illustrations/*.svg。"""
from __future__ import annotations

import re
from pathlib import Path

from . import config
from .manifest import BookError

ART_DIR = config.STATIC_DIR / "illustrations"
SAFE_NAME_RE = re.compile(r"^part-(?:i|ii|iii|iv|v)\.svg$")
CHAPTER_STEM_RE = re.compile(r"-ch(\d+)$")
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


def _inline_svg(path: Path, label: str) -> str:
    """读出并校验一幅 SVG；任何安全契约被破坏即抛 BookError。"""
    svg = path.read_text(encoding="utf-8").strip()
    if not svg.startswith("<svg"):
        raise BookError(f"{label}不是 SVG: {path}")
    lowered = svg.lower()
    for token in ACTIVE_TOKENS:
        if token in lowered:
            raise BookError(f"{label}含不允许的内容 {token!r}: {path}")
    if HREF_ATTR_RE.search(lowered):
        raise BookError(f"{label}含 href 属性: {path}")
    if EVENT_ATTR_RE.search(lowered):
        raise BookError(f"{label}含事件属性: {path}")
    urls = {url.lower() for url in URL_RE.findall(svg)}
    if urls - URL_ALLOWED:
        raise BookError(f"{label}含外部 URL: {path}")
    for reference in CSS_URL_RE.findall(svg):
        if not reference.strip().startswith("#"):
            raise BookError(f"{label}含外部 url(): {path}")
    if CJK_RE.search(svg):
        raise BookError(f"{label}只许拉丁文字: {path}")
    return svg


def part_art(name: str | None) -> str:
    """读取并校验一幅篇首 SVG；名称为空时返回空字符串。"""
    if not name:
        return ""
    if not isinstance(name, str) or not SAFE_NAME_RE.fullmatch(name):
        raise BookError(f"篇首插图文件名不合法: {name!r}")
    path = ART_DIR / name
    if not path.is_file():
        raise BookError(f"缺少篇首插图: {path}")
    return _inline_svg(path, "篇首插图")


def chapter_art(chapter_filename_stem: str, warnings: list[str] | None = None) -> str:
    """按章源文件名读取并校验章徽；缺文件记警告返回空串，不阻断构建。

    章号取自文件名的 -chN 后缀，映射到 static/illustrations/chNN.svg
    （两位零填充：p1-01-ch0 → ch00.svg）。安全校验契约与篇首插图一致。
    """
    match = CHAPTER_STEM_RE.search(str(chapter_filename_stem or ""))
    if not match:
        return ""
    path = ART_DIR / f"ch{int(match.group(1)):02d}.svg"
    if not path.is_file():
        if warnings is not None:
            warnings.append(f"缺少章徽: {path}")
        return ""
    return _inline_svg(path, "章徽")
