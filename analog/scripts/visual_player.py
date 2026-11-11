"""构建期为已登记的 V2 动画生成可渐进增强的静态播放器外壳。"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

V2_IMAGE = re.compile(r'<img\b[^>]*\bsrc=["\'](assets/svg-v2/[^"\']+)["\'][^>]*>', re.I)


def load_players(root: Path) -> dict:
    import yaml

    path = root / "docs/superpowers/visual/visual-manifest.yml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {a["output"]: a for a in data.get("assets", [])
            if a.get("kind") == "animation" and a.get("output", "").startswith("assets/svg-v2/")
            and a.get("status") in {"generated", "reviewed", "accepted", "published"}}


def player_html(asset: dict, root: Path) -> str:
    source, fallback = asset["output"], asset["reduced_motion"]
    for value in (source, fallback):
        path = (root / value).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError(f"播放器缺项目内资源: {value}")
    tree = ET.fromstring((root / source).read_text(encoding="utf-8"))
    box = tree.get("viewBox", "").split()
    if len(box) != 4:
        raise ValueError(f"播放器缺 viewBox: {source}")
    width, height = box[2:]
    metadata = tree.find("{http://www.w3.org/2000/svg}metadata[@id='visual-timeline']")
    duration = float(str(asset["duration"]).removesuffix("s"))
    beats = asset["beats"]
    if metadata is None or not isinstance(beats, list) or not beats:
        raise ValueError(f"播放器缺时间轴: {source}")
    timeline = json.loads(metadata.text)
    keys = ("name", "start", "end")
    recorded_beats = [{k: b[k] for k in keys} for b in timeline["beats"]]
    manifest_beats = [{k: b[k] for k in keys} for b in beats]
    if timeline["duration"] != duration or recorded_beats != manifest_beats:
        raise ValueError(f"动画 metadata 与 manifest 节拍不一致: {source}")
    config = escape(json.dumps({"duration": duration, "beats": beats}, ensure_ascii=False), quote=True)
    alt = escape(asset["alt"], quote=True)
    return (f'<div class="visual-player" data-visual-player="{escape(asset["id"], quote=True)}" '
            f'data-animation-src="{escape(source, quote=True)}" data-timeline="{config}">'
            f'<div class="visual-player-viewport"><img src="{escape(fallback, quote=True)}" '
            f'alt="{alt}" width="{width}" height="{height}" loading="lazy" decoding="async"></div>'
            '<div class="visual-player-controls"></div>'
            '<p class="visual-player-status" role="status">结论静帧；可按需播放演示。</p>'
            f'<p class="visual-player-links"><a href="{escape(source, quote=True)}">查看原动画</a>'
            ' · <a href="gallery.html">动画中心</a></p></div>')


def wrap_visual_players(text: str, players: dict, root: Path) -> str:
    def replace(match):
        source = match.group(1)
        asset = players.get(source)
        if asset is None:
            if source.endswith(("-static.svg", "-storyboard.svg")):
                return match.group(0)
            raise ValueError(f"V2 正文动画未登记或尚未生成: {source}")
        return player_html(asset, root)
    # 先解开仅含图片的段落，避免在 <p> 中嵌套播放器 <div>。
    text = re.sub(r'<p\b[^>]*>\s*(<img\b[^>]*src=["\']assets/svg-v2/[^>]*>)\s*</p>', r'\1', text)
    return V2_IMAGE.sub(replace, text)
