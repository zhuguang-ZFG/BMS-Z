#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提示词记录契约：每条新资产有记录、双语 prompt、数值回对正文。

新资产 = manifest 中 status 不是 legacy-unreviewed 的条目。真实 manifest 与
夹具两种来源都跑同一套判定。
"""
import tempfile
import unittest
from pathlib import Path

import check_visual_manifest as chk

ABS_PATH = ("C:\\Users\\", "/home/", "/Users/", "D:\\Users\\")


def sandbox(numbers: str = "['41%']", zh: str = "中文", en: str = "English") -> Path:
    root = Path(tempfile.mkdtemp())
    (root / "docs").mkdir()
    (root / "docs" / "p4-02-ch17.md").write_text(
        "## 17.0\n\n故障占比 41%，验证成本 23%。\n", encoding="utf-8")
    (root / "assets" / "figures").mkdir(parents=True)
    (root / "assets" / "figures" / "ch17-demo.svg").write_text(
        "<svg/>", encoding="utf-8")
    (root / "prompts").mkdir()
    (root / "prompts" / "ch17-demo.md").write_text(
        f"---\nid: ch17-demo\ngenerator: deterministic-svg-v1\n"
        f"reference_policy: none\nnumbers: {numbers}\n"
        f"zh_prompt: {zh}\nen_prompt: {en}\n---\n", encoding="utf-8")
    return root


def entry() -> dict:
    return {
        "id": "ch17-demo", "chapter": 17, "kind": "figure", "type": "V3",
        "anchor": "17.0", "purpose": "定量图", "style_id": "FA-029",
        "layout_id": "IG-012", "color_ids": ["C-30"],
        "source_facts": ["docs/p4-02-ch17.md#17.0"],
        "prompt_file": "prompts/ch17-demo.md",
        "output": "assets/figures/ch17-demo.svg",
        "print_fallback": "assets/figures/ch17-demo.svg",
        "status": "generated",
        "status_history": ["planned", "generated"],
        "alt": "故障占比与验证成本",
    }


class PromptRecordTests(unittest.TestCase):
    def run_check(self, root: Path) -> list[str]:
        old = chk.ROOT
        chk.ROOT = root
        try:
            return chk.check({"meta": {"statuses": chk.STATUSES},
                              "assets": [entry()]})
        finally:
            chk.ROOT = old

    def test_valid_record_passes(self):
        self.assertEqual([], self.run_check(sandbox()))

    def test_number_absent_from_source_fails(self):
        bad = self.run_check(sandbox(numbers="['99%']"))
        self.assertTrue(any("99%" in x for x in bad))

    def test_missing_prompt_file_fails(self):
        root = sandbox()
        (root / "prompts" / "ch17-demo.md").unlink()
        self.assertTrue(any("prompt 记录不存在" in x for x in self.run_check(root)))

    def test_prompt_without_chinese_or_english_fails(self):
        root = sandbox(zh="''")
        self.assertTrue(any("中/英" in x for x in self.run_check(root)))

    def test_id_mismatch_fails(self):
        root = sandbox()
        (root / "prompts" / "ch17-demo.md").write_text(
            "---\nid: other\nnumbers: []\nzh_prompt: 中\nen_prompt: E\n---\n",
            encoding="utf-8")
        self.assertTrue(any("id 不匹配" in x for x in self.run_check(root)))

    def test_no_absolute_paths_in_project_prompts(self):
        """项目 prompt 与 lock 不许出现本机绝对路径（上游相对路径除外）。"""
        visual = chk.ROOT / "docs" / "superpowers" / "visual"
        problems = []
        for path in list(visual.rglob("*.md")) + list(visual.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            for needle in ABS_PATH:
                if needle in text:
                    problems.append(f"{path.name}: {needle}")
        self.assertEqual([], problems)


class RealManifestTests(unittest.TestCase):
    def test_manifest_check_passes(self):
        self.assertEqual([], chk.check(chk.load()))

    def test_every_non_legacy_asset_has_prompt(self):
        for a in chk.load().get("assets") or []:
            if a.get("status") == "legacy-unreviewed":
                continue
            self.assertTrue(a.get("prompt_file"), a["id"])
            self.assertTrue((chk.ROOT / a["prompt_file"]).exists(), a["id"])


if __name__ == "__main__":
    unittest.main()
