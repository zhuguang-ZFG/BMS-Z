#!/usr/bin/env python3
"""合集 EPUB 目录结构回归：EPUB 3.3 §7.3 的 nav 内容模型。"""
from __future__ import annotations

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "book"))

import build_combined  # noqa: E402

XHTML = "{http://www.w3.org/1999/xhtml}"
OPS = "{http://www.idpf.org/2007/ops}"


def nav_ols(xhtml: str) -> tuple[ET.Element, list[ET.Element]]:
    root = ET.fromstring(xhtml)
    nav = next(node for node in root.iter(XHTML + "nav")
               if node.get(OPS + "type") == "toc")
    top = [node for node in nav if node.tag == XHTML + "ol"]
    return nav, top


class CombinedNavTest(unittest.TestCase):
    def test_nav_has_one_top_level_ol_with_two_nested_volumes(self):
        nav = build_combined.compose_nav_xhtml(
            '<ol><li><a href="p1.xhtml">甲</a></li></ol>',
            '<ol><li><a href="p2.xhtml">乙</a></li></ol>',
        )
        self.assertEqual(build_combined.nav_structure_problems(nav), [])
        nav_node, top = nav_ols(nav)
        self.assertEqual(len(top), 1)
        self.assertEqual(len([n for n in nav_node if n.tag == XHTML + "h1"]), 1)
        items = [n for n in top[0] if n.tag == XHTML + "li"]
        self.assertEqual(len(items), 2)
        self.assertTrue(all(any(n.tag == XHTML + "ol" for n in item) for item in items))
        self.assertIn(build_combined.VOL1_TITLE, nav)
        self.assertIn(build_combined.VOL2_TITLE, nav)

    def test_legacy_h2_ol_pair_is_rejected(self):
        legacy = f'''<html xmlns="http://www.w3.org/1999/xhtml"
 xmlns:epub="http://www.idpf.org/2007/ops"><body>
<nav epub:type="toc"><h1>{build_combined.TITLE}</h1>
<h2>{build_combined.VOL1_TITLE}</h2><ol><li><a href="v1/a.xhtml">甲</a></li></ol>
<h2>{build_combined.VOL2_TITLE}</h2><ol><li><a href="v2/a.xhtml">乙</a></li></ol>
</nav></body></html>'''
        problems = build_combined.nav_structure_problems(legacy)
        self.assertTrue(any("顶层 ol" in problem for problem in problems), problems)
        self.assertTrue(any("标题" in problem for problem in problems), problems)


if __name__ == "__main__":
    unittest.main()
