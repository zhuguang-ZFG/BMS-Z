#!/usr/bin/env python3
"""静态技术插图：离线、配色、标题/描述，以及正文中的 figure + 图注。"""
import re
import unittest
from pathlib import Path

from defusedxml import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "assets" / "figures"
DOCS = ROOT / "docs"

WAVE1_FIGURES = {
    "ch00-controlled-sources.svg",
    "ch02-operating-map.svg",
    "ch02-tvs-clamp.svg",
    "ch11-cascode.svg",
    "ch14-error-budget.svg",
    "ch14-power-tree-timing.svg",
    "ch16-probe-model.svg",
    "ch16-signal-injection.svg",
}
# 旧图用三色骨架；2026-11 起的新图走 handraw 纸墨 token（scripts/handraw.py）。
PALETTE = {"#14213d", "#b45309", "#0f766e"} | {
    value.lower() for value in __import__("handraw").LIGHT.values()}
EXTERNAL_REF = re.compile(r'(?:href|src)\s*=\s*["\']https?://', re.I)
SVG_NS = "{http://www.w3.org/2000/svg}"


def _text_width(text, size):
    """与 scripts/generate_svgs.py 一致的等宽估宽，仅作越界探针。"""
    w = 0.0
    for ch in text:
        o = ord(ch)
        if o >= 0x2E80 or 0x2460 <= o <= 0x24FF or ch in "—–…":
            w += size
        elif ch in "iljI.,:;'|! ":
            w += size * 0.30
        elif ch in "→←↑↓⇒⇔±×÷≈≠≤≥√∑∫∞∝°":
            w += size * 0.95
        elif 0x370 <= o <= 0x3FF:
            w += size * 0.75
        elif ch.isupper() or ch.isdigit():
            w += size * 0.66
        else:
            w += size * 0.58
    return w * 1.045


# 估宽探针误报白名单，键为 (去掉 -print 的文件名, 文本前 14 字)。
# 收录条件：Chromium getBoundingClientRect 实测该文本框未越界，仅线性估宽超限——
# 楷体拉丁字形明显窄于 0.58×size 的等宽估计。2026-11-07 实测 ch11-noise-three-taxes
# 全库唯一命中，浏览器量得 right ≤ 1000。
ESTIMATE_FALSE_POSITIVES = {
    ("ch11-noise-three-taxes", "datasheet 给的是每"),
}


def _extent_violations(path):
    """未旋转载体内的 <text> 不许越过画布 2px 以上。

    旋转坐标系的轴标注（transform=rotate）按旋转前坐标跳过；
    只看元素自身的 transform，不解析父级 <g> 的平移——
    组内文字相对画布整体平移时探针仍可能误报，需要时加白名单。
    """
    text = path.read_text(encoding="utf-8")
    viewbox = re.search(
        r'viewBox="([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"', text)
    if not viewbox:
        return [f"{path.name}: 缺少 viewBox"]
    width = float(viewbox.group(3))
    height = float(viewbox.group(4))
    root = ET.fromstring(text)
    issues = []
    for el in root.iter(f"{SVG_NS}text"):
        if el.get("transform"):
            continue
        try:
            x = float(el.get("x", "0"))
            y = float(el.get("y", "0"))
        except ValueError:
            continue
        size = float(el.get("font-size", "12"))
        content = "".join(el.itertext())
        stem = re.sub(r"-print$", "", path.stem)
        if (stem, content[:14]) in ESTIMATE_FALSE_POSITIVES:
            continue
        anchor = el.get("text-anchor", "start")
        w = _text_width(content, size)
        left = x - (w / 2 if anchor == "middle"
                    else w if anchor == "end" else 0)
        right = left + w
        if left < -2 or right > width + 2 or y < -2 or y > height + 2:
            issues.append(
                f'{path.name}: "{content[:24]}" '
                f"x[{left:.0f},{right:.0f}] y={y:.0f} 越出 {width:.0f}x{height:.0f}")
    return issues


# 两条已授权血统：Task 5 overlay 双层合成；2026-11-05 起 python-handraw-v1 手绘整图
# （标记由 scripts/label_handraw_figures.py 从 composition JSON 补齐，波次重建后需重跑）。
COMPOSITIONS = {"technical-overlay-v1", "python-handraw-v1"}


class FigureTests(unittest.TestCase):
    def test_v2_figures_are_labelled_and_have_vector_print_fallbacks(self):
        for path in sorted((ROOT / "assets/figures-v2").glob("*.svg")):
            with self.subTest(path=path.name):
                raw = path.read_text(encoding="utf-8")
                tree = ET.fromstring(raw)
                self.assertIn(tree.get("data-composition"), COMPOSITIONS)
                self.assertRegex(raw, r"<title[^>]*>.+?</title>")
                self.assertRegex(raw, r"<desc[^>]*>.+?</desc>")
                self.assertEqual([], EXTERNAL_REF.findall(raw))
                if path.stem.endswith("-print"):
                    self.assertEqual([], list(tree.iter(f"{SVG_NS}image")))
                self.assertEqual([], _extent_violations(path))

    def test_wave1_figures_exist(self):
        present = {path.name for path in FIGURES.glob("*.svg")}
        self.assertEqual(set(), WAVE1_FIGURES - present)

    def test_svgs_are_offline_labelled_and_colour_locked(self):
        for path in sorted(FIGURES.glob("*.svg")):
            name = path.name
            text = path.read_text(encoding="utf-8")
            root = ET.fromstring(text)
            self.assertTrue(root.tag.endswith("svg"), name)
            self.assertTrue(root.get("viewBox"), name)
            self.assertNotIn("<script", text.lower(), name)
            self.assertNotIn("<image", text.lower(), name)
            self.assertNotIn("<foreignobject", text.lower(), name)
            self.assertEqual([], EXTERNAL_REF.findall(text), name)
            self.assertRegex(text, r"<title[^>]*>.+?</title>", name)
            self.assertRegex(text, r"<desc[^>]*>.+?</desc>", name)
            self.assertGreaterEqual(text.count("<text"), 6, name)
            self.assertTrue(any(colour in text.lower() for colour in PALETTE),
                            name)

    def test_text_stays_inside_the_canvas(self):
        issues = []
        for path in sorted(FIGURES.glob("*.svg")):
            issues.extend(_extent_violations(path))
        self.assertEqual([], issues)

    def test_each_figure_is_wrapped_in_a_figure_with_caption(self):
        docs = "\n".join(path.read_text(encoding="utf-8")
                         for path in sorted(DOCS.glob("*.md")))
        blocks = re.findall(r"<figure\b.*?</figure>", docs, re.S)
        # V2 migration keeps historical files for old links and comparison.
        # Validate every figure actually referenced by the current manuscript,
        # including V2, rather than requiring retired files back in the prose.
        referenced = set(re.findall(
            r"assets/figures(?:-v2)?/[A-Za-z0-9._-]+\.svg", docs))
        self.assertGreater(len(referenced), 100, "正文静态图扫描异常")
        for source in sorted(referenced):
            matches = [block for block in blocks if f'"{source}"' in block]
            self.assertEqual(1, len(matches), f"{source} 应恰好出现一次且放入 figure")
            self.assertRegex(matches[0], r"<figcaption>\s*\S",
                             f"{source} 缺少非空图注")
            self.assertTrue((ROOT / source).is_file(), f"正文引用了不存在的图: {source}")


if __name__ == "__main__":
    unittest.main()
