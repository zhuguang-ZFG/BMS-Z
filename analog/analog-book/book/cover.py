"""印刷封面：书脊公式、三栏版式、裁切线、二维码与 150dpi 预览。"""
from __future__ import annotations

import hashlib
import html
from pathlib import Path

from . import config, fonts
from .manifest import BookError
from .pdf import print_pdf

READING_LAYERS = (
    ("直觉层", "先看见电流怎么走"),
    ("推导层", "把模型算到能下手"),
    ("工程层", "仿真、实测与排故闭环"),
)
METHOD_LABEL = "读 → 算 → 仿 → 测 → 排"
FRONT_SPEC = "19 章 · 5 篇 · 三层读法 · 16K 全彩"


def spine_mm(pages: int, manifest: dict) -> float:
    if pages <= 0:
        raise ValueError("页数必须为正")
    cover = manifest["cover"]
    value = pages / 2 * cover["paper_caliper_mm"] + cover["spine_allowance_mm"]
    return round(value, 2)


def cover_size_mm(pages: int, manifest: dict) -> tuple[float, float]:
    if pages <= 0:
        raise ValueError("页数必须为正")
    trim = manifest["trim"]
    bleed = manifest["cover"]["bleed_mm"]
    width = 2 * trim["width_mm"] + spine_mm(pages, manifest) + 2 * bleed
    height = trim["height_mm"] + 2 * bleed
    return round(width, 2), round(height, 2)


def qr_svg(data: str) -> str:
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError as exc:
        raise BookError("封面二维码需要 qrcode：pip install qrcode") from exc
    image = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage,
                        box_size=10, border=2)
    text = image.to_string().decode("utf-8")
    svg = text[text.index("<svg"):]
    # qrcode 对每个码都输出 id="qr-path"；封面上有两个码，重复 ID 无效。
    unique_id = "qr-path-" + hashlib.sha256(
        data.encode("utf-8")).hexdigest()[:10]
    svg = svg.replace('id="qr-path"', f'id="{unique_id}"')
    return svg.replace("url(#qr-path)", f"url(#{unique_id})")


def _e(value) -> str:
    return html.escape(str(value), quote=True)


def _crop_marks(width: float, height: float, bleed: float) -> str:
    left, right = bleed, width - bleed
    top, bottom = bleed, height - bleed
    short = max(1.0, bleed - 0.8)
    lines = [
        (left, 0, left, short), (left, height - short, left, height),
        (right, 0, right, short), (right, height - short, right, height),
        (0, top, short, top), (width - short, top, width, top),
        (0, bottom, short, bottom), (width - short, bottom, width, bottom),
    ]

    def stroke(kind: str) -> str:
        return "".join(
            f'<line class="{kind}" x1="{x1:.2f}" y1="{y1:.2f}" '
            f'x2="{x2:.2f}" y2="{y2:.2f}"/>'
            for x1, y1, x2, y2 in lines)

    # 先画米白垫底，黑芯压在中间：深色背封上仍可见，米色前封上只剩黑芯。
    return stroke("crop-mark-halo") + stroke("crop-mark")


def _cover_css(width: float, height: float, spine: float,
               manifest: dict) -> str:
    trim = manifest["trim"]
    bleed = manifest["cover"]["bleed_mm"]
    template = (config.COVER_DIR / "cover.css").read_text(encoding="utf-8")
    return (template.replace("__WIDTH__", f"{width:.2f}")
            .replace("__HEIGHT__", f"{height:.2f}")
            .replace("__TRIM_W__", f"{trim['width_mm']:.2f}")
            .replace("__TRIM_H__", f"{trim['height_mm']:.2f}")
            .replace("__BLEED__", f"{bleed:.2f}")
            .replace("__SPINE__", f"{spine:.2f}"))


def _cover_art() -> str:
    path = config.STATIC_DIR / "cover-art.svg"
    if not path.is_file():
        raise BookError(f"缺少封面插图: {path}")
    return path.read_text(encoding="utf-8")


def _structure_html(structure) -> str:
    """全书结构是可选数据；没有时整块省略。"""
    if not structure:
        return ""
    rows = "".join(
        '<div class="structure-row">'
        f'<span class="structure-no">{index:02d}</span>'
        '<span class="structure-body">'
        f'<span class="structure-title">{_e(item.get("title", ""))}</span>'
        f'<span class="structure-scope">{_e(item.get("scope", ""))}</span>'
        "</span></div>"
        for index, item in enumerate(structure, 1))
    return f"""
<section class="back-structure">
<p class="back-heading">五篇</p>
<div class="structure-list">{rows}</div>
</section>"""


def _highlights_html(highlights) -> str:
    """没有 structure 时，用要点索引占住同一版块，避免中缝出现大块空白。"""
    if not highlights:
        return ""
    rows = "".join(f"<li>{_e(item)}</li>" for item in highlights)
    return f"""
<section class="back-highlights">
<p class="back-heading">本书要点</p>
<ul class="highlight-list">{rows}</ul>
</section>"""


def _reading_html() -> str:
    rows = "".join(
        '<div class="layer-row">'
        f'<span class="layer-name">{_e(name)}</span>'
        f'<span class="layer-desc">{_e(desc)}</span>'
        "</div>" for name, desc in READING_LAYERS)
    return f"""
<section class="back-layers">
<p class="back-heading">三层读法</p>
<div class="layer-list">{rows}</div>
</section>"""


def _features_html(highlights) -> str:
    if not highlights:
        return ""
    return ('<p class="back-features">'
            + " · ".join(_e(item) for item in highlights) + "</p>")


def cover_html(manifest: dict, pages: int, fonts_css: str = "") -> str:
    width, height = cover_size_mm(pages, manifest)
    spine = spine_mm(pages, manifest)
    back = manifest["cover"]["back_cover"]
    structure_data = back.get("structure")
    structure = _structure_html(structure_data)
    highlights = back.get("highlights", [])
    features = _features_html(highlights) if structure_data else ""
    highlight_index = "" if structure_data else _highlights_html(highlights)
    spine_class = "cover-spine is-thin" if spine < 6 else "cover-spine"
    spine_text = "" if spine < 6 else (
        '<div class="spine-text">'
        f'<span class="spine-title">{_e(manifest["title"])}</span>'
        f'<span class="spine-author">{_e(manifest["author"])}</span>'
        '</div>')
    site_qr = qr_svg(manifest["site_url"])
    repo_qr = qr_svg(manifest["repository"])
    crop_marks = ""
    if manifest["cover"].get("crop_marks", True):
        crop_marks = (
            f'<svg class="cover-marks" viewBox="0 0 {width:.2f} {height:.2f}" '
            'xmlns="http://www.w3.org/2000/svg">\n'
            f'{_crop_marks(width, height, manifest["cover"]["bleed_mm"])}\n'
            '</svg>')
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{_e(manifest["title"])} · 封面</title>
<style>{fonts_css}
{_cover_css(width, height, spine, manifest)}</style></head>
<body><div class="cover">
{crop_marks}
<section class="cover-panel cover-back">
<header class="back-head">
<p class="back-kicker">关于本书</p>
<p class="back-blurb">{_e(back["blurb"])}</p>
<p class="back-audience"><strong>适合读者</strong>{_e(back["audience"])}</p>
{features}
</header>
{_reading_html()}
{structure}{highlight_index}
<p class="back-method"><span class="method-label">{_e(METHOD_LABEL)}</span>
<span class="method-note">每章沿这条路线走完一轮。</span></p>
<footer class="back-foot">
<div class="back-qr">
<div class="qr" data-qr="site">{site_qr}<span>在线站</span></div>
<div class="qr" data-qr="repo">{repo_qr}<span>仓库</span></div>
</div>
<div class="isbn-area"><span>ISBN / 条码预留区（留空）</span></div>
<div class="back-legal">
<p>{_e(manifest["license"])} · {_e(manifest["edition"])} · {_e(manifest["version"])}</p>
<p class="back-errata">勘误与讨论：{_e(manifest["repository"])}/issues</p>
<p class="back-spec">185 × 260 mm · 全彩 · 胶装</p>
</div>
</footer>
</section>
<section class="cover-panel {spine_class}">{spine_text}</section>
<section class="cover-panel cover-front">
<header class="front-head">
<span class="front-wordmark">ANALOG CIRCUIT ROADMAP</span>
<span class="front-edition">{_e(manifest["edition"])}</span>
</header>
<div class="front-art">{_cover_art()}</div>
<div class="front-title-block">
<h1 class="front-title">{_e(manifest["title"])}</h1>
<p class="front-subtitle">{_e(manifest["subtitle"])}</p>
</div>
<footer class="front-foot">
<span class="front-author">{_e(manifest["author"])}</span>
<p class="front-spec">{_e(FRONT_SPEC)}</p>
</footer>
</section>
</div></body></html>
"""


def inspect_cover(pdf_path: Path, pages: int, manifest: dict) -> dict:
    try:
        import fitz
    except ImportError as exc:
        raise BookError("封面检查需要 PyMuPDF") from exc
    expected_width, expected_height = cover_size_mm(pages, manifest)
    document = fitz.open(pdf_path)
    try:
        problems = []
        if document.page_count != 1:
            problems.append(f"封面应为 1 页，实际 {document.page_count} 页")
        page = document[0]
        width = page.rect.width / (72 / 25.4)
        height = page.rect.height / (72 / 25.4)
        if abs(width - expected_width) > 0.5 or abs(height - expected_height) > 0.5:
            problems.append(
                f"封面尺寸 {width:.2f}×{height:.2f}mm，"
                f"应为 {expected_width}×{expected_height}mm")
        return {"pages": document.page_count,
                "size_mm": [round(width, 2), round(height, 2)],
                "spine_mm": spine_mm(pages, manifest),
                "problems": problems}
    finally:
        document.close()


def build_cover(out_dir: Path, pages: int, manifest: dict,
                browser_override: str | None = None):
    if pages <= 0:
        raise ValueError("页数必须为正")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "cover.html"
    pdf_path = out_dir / config.COVER_PDF_NAME
    preview_path = out_dir / config.COVER_PREVIEW_NAME
    html_path.write_text(
        cover_html(manifest, pages, fonts.font_css()), encoding="utf-8",
        newline="\n")
    print_pdf(html_path, pdf_path, browser_override)
    report = inspect_cover(pdf_path, pages, manifest)
    if report["problems"]:
        raise BookError("封面审计失败:\n" + "\n".join(report["problems"]))
    try:
        import fitz
    except ImportError as exc:
        raise BookError("封面预览需要 PyMuPDF") from exc
    document = fitz.open(pdf_path)
    try:
        pixmap = document[0].get_pixmap(dpi=150)
        pixmap.save(preview_path)
    finally:
        document.close()
    print(f"cover {pdf_path} ({pages} pages -> spine {report['spine_mm']} mm)")
    return html_path, pdf_path, preview_path
