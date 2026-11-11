"""无文字底图 + 确定性技术 SVG；另出不含位图的印刷 SVG 与灰度预览。

python scripts/compose_technical_overlay.py --spec path/to/composition.json --preview
--print-only 仅构建技术校样，不表示底图或人工审图已完成。
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
ALLOWED = {"svg", "g", "defs", "marker", "path", "line", "polyline", "polygon",
           "circle", "ellipse", "rect", "text", "tspan", "title", "desc"}


def project_path(value: str, root: Path = ROOT) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"路径越出项目: {value}")
    return path


def luminance(colour: str) -> float:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", colour):
        raise ValueError(f"技术文字必须使用显式六位色值: {colour}")
    values = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    values = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
    return sum(v * k for v, k in zip(values, (.2126, .7152, .0722)))


def contrast(a: str, b: str) -> float:
    x, y = sorted((luminance(a), luminance(b)))
    return (y + .05) / (x + .05)


def validate_overlay(markup: str, spec: dict) -> ET.Element:
    if "<!" in markup:
        raise ValueError("overlay 不接受 DTD、实体或注释中的隐藏内容")
    tree = ET.fromstring(markup)
    width, height = spec.get("canvas", [1448, 1086])
    if not (width > 0 and height > 0 and math.isclose(width / height, 4 / 3)):
        raise ValueError("画幅必须为 1448×1086 或等比例 4:3")
    if tree.get("viewBox") != f"0 0 {width} {height}":
        raise ValueError("overlay viewBox 与 canvas 不一致")
    print_width = spec.get("print_width_mm", 138)
    if not isinstance(print_width, (int, float)) or not 0 < print_width <= 180:
        raise ValueError("print_width_mm 必须是实际版心宽度")
    texts = []
    for node in tree.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag not in ALLOWED:
            raise ValueError(f"overlay 禁止元素: {tag}")
        for key, value in node.attrib.items():
            if key.lower().startswith("on") or key in {"style", "href"} or key.endswith("}href"):
                raise ValueError(f"overlay 禁止属性: {key}")
            if "url(" in value and not re.fullmatch(r"url\(#[A-Za-z0-9_-]+\)", value):
                raise ValueError("overlay 不得加载外部资源")
        if tag == "text":
            texts.append(node)
            size = float(node.get("font-size", "0"))
            points = size / width * print_width * 72 / 25.4
            if points < 8.5:
                raise ValueError(f"16K 字号 {points:.2f}pt < 8.5pt: {''.join(node.itertext())[:24]}")
            if contrast(node.get("fill", ""), node.get("data-background", spec["paper"])) < 4:
                raise ValueError(f"文字对比度 <4: {''.join(node.itertext())[:24]}")
    if not texts:
        raise ValueError("overlay 缺少技术文字")
    if not spec.get("title") or not spec.get("alt"):
        raise ValueError("composition 须含 title 与 alt")
    return tree


def compose(spec: dict, root: Path = ROOT, print_only: bool = False) -> dict[str, Path]:
    overlay = validate_overlay(project_path(spec["overlay"], root).read_text(encoding="utf-8"), spec)
    width, height = spec.get("canvas", [1448, 1086])
    output = project_path(spec["output"], root)
    if output.suffix != ".svg":
        raise ValueError("output 必须为 .svg")
    # 在写出任何产物之前读取并验证底图。
    image_uri = None
    vector_base = None
    if spec.get("base_svg"):
        if spec.get("base_image"):
            raise ValueError("base_svg 与 base_image 必须二选一")
        raw_base = project_path(spec["base_svg"], root).read_text(encoding="utf-8")
        if "<!" in raw_base:
            raise ValueError("矢量底图不接受 DTD 或实体")
        vector_base = ET.fromstring(raw_base)
        if vector_base.get("viewBox") != f"0 0 {width} {height}":
            raise ValueError("矢量底图 viewBox 与 canvas 不一致")
        for node in vector_base.iter():
            if node.tag.rsplit("}", 1)[-1] not in ALLOWED - {"text", "tspan", "title", "desc"}:
                raise ValueError("矢量底图只能包含无文字的静态图形")
            for key, value in node.attrib.items():
                if key.lower().startswith("on") or key in {"style", "href"} or key.endswith("}href"):
                    raise ValueError("矢量底图不允许外部或可执行内容")
                if "url(" in value and not re.fullmatch(r"url\(#[A-Za-z0-9_-]+\)", value):
                    raise ValueError("矢量底图不允许外部资源")
    elif not print_only:
        base = project_path(spec["base_image"], root)
        with Image.open(base) as image:
            if image.format not in {"PNG", "WEBP", "JPEG"}:
                raise ValueError("底图须为 PNG/WebP/JPEG")
            if not math.isclose(image.width / image.height, width / height, rel_tol=.01):
                raise ValueError("底图不是 4:3，须明确重构图；不静默裁切")
            mime = Image.MIME[image.format]
        image_uri = f"data:{mime};base64," + base64.b64encode(base.read_bytes()).decode("ascii")
    shell = ET.Element(f"{{{NS}}}svg", {
        "viewBox": f"0 0 {width} {height}", "role": "img", "aria-labelledby": "title desc",
        "data-print-width-mm": str(spec.get("print_width_mm", 138)),
        "data-composition": "technical-overlay-v1",
        "data-base-medium": "python-svg" if vector_base is not None else "raster"})
    ET.SubElement(shell, f"{{{NS}}}title", {"id": "title"}).text = spec["title"]
    ET.SubElement(shell, f"{{{NS}}}desc", {"id": "desc"}).text = spec["alt"]
    ET.SubElement(shell, f"{{{NS}}}rect", {"width": str(width), "height": str(height), "fill": spec["paper"]})
    written = {}
    output.parent.mkdir(parents=True, exist_ok=True)
    for name in (["print"] if print_only else ["composite", "print"]):
        tree = copy.deepcopy(shell)
        if vector_base is not None:
            base_group = ET.SubElement(tree, f"{{{NS}}}g", {"id": "paper-illustration"})
            base_group.extend(copy.deepcopy(list(vector_base)))
            if name == "print":
                for parent in list(base_group.iter()):
                    for child in list(parent):
                        if child.get("data-paper-shadow"):
                            parent.remove(child)
        elif name == "composite":
            ET.SubElement(tree, f"{{{NS}}}image", {"width": str(width), "height": str(height),
                          "href": image_uri, "aria-hidden": "true"})
        group = ET.SubElement(tree, f"{{{NS}}}g", {"id": "technical-overlay"})
        group.extend(copy.deepcopy(list(overlay)))
        path = output if name == "composite" else output.with_stem(output.stem + "-print")
        path.write_text(ET.tostring(tree, encoding="unicode") + "\n", encoding="utf-8")
        written[name] = path
    return written


def preview(path: Path, spec: dict) -> dict:
    """真实浏览器测量中文边界与变换后的印刷字号，再导出 WebP/灰度。"""
    from playwright.sync_api import sync_playwright
    width, height = spec.get("canvas", [1448, 1086])
    # scale 只影响位图预览的像素密度；文字边界与字号仍按 CSS px 测量，闸不变。
    scale = int(spec.get("scale", 1))
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        try:
            page = browser.new_page(viewport={"width": width, "height": height},
                                    device_scale_factor=scale)
            markup = path.read_text(encoding="utf-8")
            page.set_content('<style>body{margin:0}svg{display:block;width:100%;height:auto}text{font-family:"Microsoft YaHei",sans-serif}</style>' + markup)
            page.evaluate("document.fonts.ready")
            measurements = page.locator("text").evaluate_all("""els => els.map(el => {
                const r = el.getBoundingClientRect(), m = el.getCTM();
                return {text: el.textContent, x: r.x, y: r.y, right: r.right, bottom: r.bottom,
                    size: parseFloat(getComputedStyle(el).fontSize) * Math.hypot(m.c, m.d)};
            })""")
            errors = []
            for m in measurements:
                if m["x"] < 0 or m["y"] < 0 or m["right"] > width + .5 or m["bottom"] > height + .5:
                    errors.append("文字越界: " + m["text"])
                if m["size"] / width * spec.get("print_width_mm", 138) * 72 / 25.4 < 8.5:
                    errors.append("变换后印刷字号不足: " + m["text"])
            if errors:
                raise ValueError("\n".join(errors))
            png = path.with_suffix(".png")
            page.screenshot(path=str(png))
        finally:
            browser.close()
    with Image.open(png) as opened:
        full = opened.convert("RGB")
        if scale > 1:
            # 2x 预览用有损 q93：线条图在显示尺寸下与无损无差，体积约为 1/3。
            # 印刷与正文始终用 SVG，预览不承担像素级复现，仓库不该为它翻倍。
            full.save(path.with_suffix(".webp"), quality=93, method=6)
            review = full.resize((width, height), Image.LANCZOS)
        else:
            full.save(path.with_suffix(".webp"), lossless=True)
            review = full
        review.save(png)
        review.convert("L").save(path.with_stem(path.stem + "-gray").with_suffix(".png"))
    report = {"texts": len(measurements), "min_print_pt": min(
        m["size"] / width * spec.get("print_width_mm", 138) * 72 / 25.4 for m in measurements),
        "bounds": "pass", "human_review": "pending"}
    path.with_suffix(".audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", type=Path, required=True)
    ap.add_argument("--print-only", action="store_true")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args(argv)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    outputs = compose(spec, print_only=args.print_only)
    for name, path in outputs.items():
        print(f"{name} → {path.relative_to(ROOT)}")
        if args.preview:
            print(json.dumps(preview(path, spec), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
