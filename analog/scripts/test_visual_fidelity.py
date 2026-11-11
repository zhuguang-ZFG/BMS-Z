"""来源须落到声明小节，示意值不能冒充正文事实。"""
import tempfile
import unittest
from pathlib import Path

from visual_fidelity import number_gaps, source_excerpt, visible_text, visible_number_gaps


class FidelityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "chapter.md").write_text(
            '## 17.1 供电\n41%\n### 细节\n23%\n## 17.2 放大\n99%\n', encoding="utf-8")

    def test_other_section_cannot_supply_number(self):
        source = source_excerpt(self.root, "chapter.md#17.1")
        self.assertIn("23%", source)
        self.assertNotIn("99%", source)
        self.assertTrue(number_gaps("demo", ["99%"], source))

    def test_missing_heading_and_outside_root_rejected(self):
        for ref in ("chapter.md#99", "../other.md"):
            with self.assertRaises(ValueError):
                source_excerpt(self.root, ref)

    def test_illustration_needs_reason_and_visible_label(self):
        item = {"value": "99%", "label": "示意", "reason": "只展示比例变化，不是实测"}
        self.assertEqual([], number_gaps("demo", [item], "", "示意"))
        self.assertTrue(number_gaps("demo", [item], "", ""))
        del item["reason"]
        self.assertTrue(number_gaps("demo", [item], "", "示意"))

    def test_hidden_description_does_not_count_as_visible_label(self):
        path = self.root / "fig.svg"
        path.write_text('<svg><desc>示意</desc><text>读数</text></svg>', encoding="utf-8")
        self.assertEqual("读数", visible_text(path))

    def test_visible_number_cannot_hide_by_omitting_prompt_declaration(self):
        self.assertTrue(visible_number_gaps("demo", "扫描 0.1Ω", "100Hz", []))
        declaration = [{"value": "0.1Ω", "label": "示意", "reason": "演示端点"}]
        self.assertEqual([], visible_number_gaps("demo", "扫描 0.1Ω（示意）", "100Hz", declaration))


if __name__ == "__main__":
    unittest.main()
