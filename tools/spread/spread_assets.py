"""传播层的图片引用处理：源稿写真路径、产物写站点路径、SVG 补宽高。

源稿（`tools/spread/decks/<slug>/slides.html`、`cards/<slug>/posters.html`）里的
`<img src>` 指向仓库内的真实文件，这样 linter 与 lychee 都能直接核；构建期再按
文件名映射改写成 `assets/<dest>`，产物只需要同名素材躺在旁边。
"""

from __future__ import annotations

import re
from pathlib import Path

IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
SRC_RE = re.compile(r'\ssrc="([^"]+)"', re.I)
VIEWBOX_RE = re.compile(r'viewBox="\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)\s*"', re.I)


def rewrite_img_srcs(html: str, assets: dict[str, str]) -> str:
    """把素材引用改写成产物里的 `assets/<dest>`（按文件名匹配）。"""
    by_name = {Path(rel).name: dest for dest, rel in assets.items()}

    def sub(match: re.Match[str]) -> str:
        tag = match.group(0)
        src = SRC_RE.search(tag)
        if not src:
            return tag
        name = src.group(1).rsplit("/", 1)[-1]
        dest = by_name.get(name)
        if dest is None:
            return tag
        return tag.replace(f'src="{src.group(1)}"', f'src="assets/{dest}"', 1)

    return IMG_RE.sub(sub, html)


def ensure_img_dims(html: str, base: Path) -> str:
    """给产物里的 `<img>` 补像素宽高。

    站点检查（`.github/scripts/check_pages.py`）要求站内图带宽高数字，否则懒加载
    落地时会把下面的正文顶开；SVG 的真实尺寸从自身 viewBox 读。
    """

    def sub(match: re.Match[str]) -> str:
        tag = match.group(0)
        src = SRC_RE.search(tag)
        if not src or "width=" in tag or "height=" in tag:
            return tag
        target = (base / src.group(1).lstrip("/")).resolve()
        if not target.is_file() or target.suffix.lower() != ".svg":
            return tag
        vb = VIEWBOX_RE.search(target.read_text(encoding="utf-8", errors="ignore")[:2000])
        if not vb:
            return tag
        w, h = str(int(float(vb.group(3)))), str(int(float(vb.group(4))))
        closed = tag.endswith("/>")
        body = tag[:-2] if closed else tag[:-1]
        return body.rstrip() + f' width="{w}" height="{h}"' + ("/>" if closed else ">")

    return IMG_RE.sub(sub, html)
