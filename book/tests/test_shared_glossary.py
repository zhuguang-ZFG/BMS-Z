#!/usr/bin/env python3
"""共享术语表渲染契约：真表头与全部数据行都进 HTML。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "book"))

import shared_glossary  # noqa: E402


class SharedGlossaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = shared_glossary.render()
        lines = shared_glossary.SOURCE.read_text(encoding="utf-8").splitlines()
        cls.data_rows = [
            line for line in lines
            if line.startswith("|")
            and not all(set(cell) <= set("-: ") for cell in
                        line.strip().strip("|").split("|"))
        ][1:]

    def test_real_header_is_rendered(self) -> None:
        header = ("<thead><tr><th>术语</th><th>英文</th><th>定义</th>"
                  "<th>所属卷</th><th>相关条目</th></tr></thead>")
        self.assertIn(header, self.html)

    def test_every_data_row_is_in_body(self) -> None:
        self.assertGreaterEqual(len(self.data_rows), 70)
        self.assertEqual(self.html.count("<tr>") - 1, len(self.data_rows))
        self.assertIn("<td>虚短/虚断</td>", self.html)
        self.assertIn(f"共 {len(self.data_rows)} 条", self.html)


if __name__ == "__main__":
    unittest.main()
