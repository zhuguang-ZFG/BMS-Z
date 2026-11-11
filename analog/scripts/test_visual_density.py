#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视觉密度扫描器：口径、锚点形态与边界情形（夹具测试，不扫真实章节）。"""
import tempfile
import unittest
from pathlib import Path

import audit_visual_density as avd

DOC = """# 第 N 章\n\n## {h}\n\n{body}\n"""


def chapter(body: str, name: str = "p1-01-ch0.md") -> Path:
    tmp = Path(tempfile.mkdtemp())
    path = tmp / name
    path.write_text(body, encoding="utf-8")
    return path


def filler(n: int) -> str:
    return "字" * n


class AnchorFormsTests(unittest.TestCase):
    def test_html_and_markdown_images_count(self):
        raw = ('<p><img src="assets/figures/a.svg" alt="a"></p>\n'
               "![说明](assets/photos/b.jpg)\n")
        p = chapter(raw)
        r = avd.audit(p)
        self.assertEqual(2, r["visuals"])
        self.assertEqual(["assets/figures/a.svg", "assets/photos/b.jpg"],
                         r["assets"])

    def test_link_masquerading_as_image_does_not_count(self):
        raw = '<a href="assets/svg/anim.svg">看动画</a>\n' + filler(900)
        r = avd.audit(chapter(raw))
        self.assertEqual(0, r["visuals"])

    def test_code_fence_and_comment_images_do_not_count(self):
        raw = ("```bash\n<img src=\"assets/figures/x.svg\">\n```\n"
               "<!-- <img src=\"assets/figures/y.svg\"> -->\n")
        r = avd.audit(chapter(raw))
        self.assertEqual(0, r["visuals"])

    def test_figure_wrapping_img_counts_once(self):
        raw = ('<figure><img src="assets/figures/a.svg" alt="a">'
               "<figcaption>图注</figcaption></figure>\n")
        r = avd.audit(chapter(raw))
        self.assertEqual(1, r["visuals"])


class CharConventionTests(unittest.TestCase):
    def test_chars_are_raw_non_whitespace(self):
        raw = "abc 汉字\n\n**粗** | 表 |"
        r = avd.audit(chapter(raw))
        # 原文非空白字符：abc汉字**粗**|表|（标记符与表格竖线都计）
        self.assertEqual(avd.nonws(chapter(raw).read_text(encoding="utf-8")),
                         r["chars"])

    def test_gaps_split_by_anchor_and_cover_head_tail(self):
        raw = filler(700) + '\n<img src="assets/figures/m.svg">\n' + filler(500)
        r = avd.audit(chapter(raw))
        self.assertEqual([700, 500], r["gaps"])
        self.assertEqual(700, r["longest_gap"])

    def test_gap_ignores_the_img_tag_itself(self):
        raw = filler(600) + '\n<img src="assets/figures/a-really-long-file-name.svg" alt="long alt text here">\n' + filler(600)
        r = avd.audit(chapter(raw))
        self.assertEqual([600, 600], r["gaps"])

    def test_formula_block_image_does_not_count(self):
        raw = ("$$\n<img src=\"assets/figures/inside-formula.svg\">\n"
               "T_J = T_A + P \\times \\theta\n$$\n" + filler(500))
        r = avd.audit(chapter(raw))
        self.assertEqual(0, r["visuals"], "公式块内的图片标签不算正文视觉锚点")

    def test_formula_characters_still_count_as_reading(self):
        """掩码只为排除锚点；公式字符必须照常计入无图段，否则口径被放松。"""
        formula = "$$T_J = T_A + P \\times (\\theta_{JC} + \\theta_{CS})$$"
        r = avd.audit(chapter(formula + "\n" + filler(300)))
        self.assertGreaterEqual(r["gaps"][0], avd.nonws(formula) + 300 - 1)


class DetailFieldsTests(unittest.TestCase):
    """--gaps / --json 附加字段：断层偏移、分型计数、逐 H2 覆盖。"""

    def test_gap_spans_report_line_section_and_next_asset(self):
        head = "# 第 8 章\n\n## 8.1 有图\n\n"
        gap_head = "\n## 8.3 关键参数\n\n"
        raw = (head + '<img src="assets/figures/first.svg">' + gap_head
               + filler(1600) + '\n<img src="assets/figures/on.svg">\n' + filler(200))
        r = avd.audit(chapter(raw), detailed=True)
        self.assertEqual(1, len(r["gap_spans"]))
        g = r["gap_spans"][0]
        self.assertEqual(avd.nonws(gap_head) + 1600, g["chars"])
        self.assertEqual(5, g["at_line"], "行号是断层起点（上一张图所在行），不是小节标题行")
        self.assertEqual("8.1 有图", g["section"], "断层起点之前最近的标题")
        self.assertEqual("8.3 关键参数", g["section_next"], "断层之内遇到的第一个标题＝下刀处")
        self.assertEqual("assets/figures/on.svg", g["next_asset"])

    def test_gap_spans_tail_segment_has_no_next_asset(self):
        raw = "# 第 8 章\n\n<img src=\"assets/figures/a.svg\">\n" + filler(1700)
        g = avd.audit(chapter(raw), detailed=True)["gap_spans"][-1]
        self.assertIsNone(g["next_asset"])

    def test_cluster_positions_keep_multiline_image_line_numbers(self):
        raw = ('# 标题\n<img\n src="assets/figures/a.svg"\n alt="说明">\n'
               '短文字\n<img src="assets/svg-v2/b.svg">\n')
        row = avd.audit(chapter(raw), detailed=True)["cluster_spans"][0]
        self.assertEqual((2, 6, 3),
                         (row["from_line"], row["to_line"], row["chars"]))

    def test_v2_directories_keep_semantic_kind(self):
        self.assertEqual({"figures": 1, "photos": 0, "svg": 1, "other": 0},
                         avd.by_kind(["assets/figures-v2/a.svg", "assets/svg-v2/b.svg"]))

    def test_by_kind_counts_asset_directories(self):
        raw = ('<img src="assets/figures/a.svg"><img src="assets/photos/b.jpg">'
               '<img src="assets/svg/c.svg"><img src="assets/vendor/d.svg">')
        self.assertEqual({"figures": 1, "photos": 1, "svg": 1, "other": 1},
                         avd.audit(chapter(raw), detailed=True)["by_kind"])

    def test_h2_coverage_lists_zero_visual_sections_too(self):
        raw = ("# 第 8 章\n\n## 8.1 有图\n\n<img src=\"assets/figures/a.svg\">\n"
               "## 8.2 没图\n\n" + filler(900))
        cov = avd.audit(chapter(raw), detailed=True)["h2_coverage"]
        self.assertEqual([("8.1 有图", 1), ("8.2 没图", 0)],
                         [(h["title"], h["visuals"]) for h in cov])

    def test_default_audit_keeps_frozen_baseline_shape(self):
        """detailed=False 必须与冻结基线逐位同形，回归闸才不会被新字段绕过。"""
        raw = "# 第 8 章\n\n## 8.1\n\n" + filler(1600)
        keys = set(avd.audit(chapter(raw)))
        self.assertNotIn("gap_spans", keys)
        self.assertNotIn("by_kind", keys)
        self.assertNotIn("h2_coverage", keys)


if __name__ == "__main__":
    unittest.main()
