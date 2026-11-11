#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""manifest 不变量：ID、状态机、评分下限、定量图四规、磁盘覆盖（夹具测试）。"""
import copy
import tempfile
import unittest
from pathlib import Path

import check_visual_manifest as chk

VALID = {
    "id": "ch17-demo",
    "chapter": 17,
    "kind": "figure",
    "type": "V3",
    "anchor": "17.0",
    "purpose": "定量图",
    "style_id": "FF-015",
    "layout_id": "IG-012",
    "color_ids": ["C-30"],
    "source_facts": ["docs/p4-02-ch17.md#17.0"],
    "prompt_file": "prompts/ch17-demo.md",
    "output": "assets/figures/ch17-demo.svg",
    "print_fallback": "assets/figures/ch17-demo.svg",
    "status": "generated",
    "status_history": ["planned", "generated"],
    "alt": "故障占比与验证成本的对比",
    "review_scores": {},
    "quant_rules": {
        "layer_encodes_value": False,
        "value_channel": "overlay-axis",
        "leader_route": "margin",
        "accent_on": "paper",
        "series_distinguisher": ["lineweight", "dash"],
    },
}


def sandbox() -> tuple[Path, dict]:
    root = Path(tempfile.mkdtemp())
    (root / "docs").mkdir()
    (root / "docs" / "p4-02-ch17.md").write_text(
        "## 17.0\n\n故障占比 41% 与 23%。\n\n"
        '<img src="assets/figures/ch17-demo.svg">\n', encoding="utf-8")
    for sub in ("assets/svg", "assets/figures", "assets/photos",
                "prompts", "docs/superpowers/visual"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    (root / "docs/superpowers/visual/visual-manifest.yml").write_text(
        "", encoding="utf-8")
    (root / "docs/superpowers/visual/handraw-style-lock.md").write_text(
        "-", encoding="utf-8")
    (root / "assets/figures/ch17-demo.svg").write_text("<svg/>", encoding="utf-8")
    (root / "prompts/ch17-demo.md").write_text(
        "---\nid: ch17-demo\ngenerator: deterministic-svg-v1\n"
        "numbers: ['41%']\nzh_prompt: 中文\nen_prompt: English\n---\n",
        encoding="utf-8")
    data = {"meta": {"statuses": chk.STATUSES},
            "assets": [copy.deepcopy(VALID)]}
    return root, data


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.root, self.data = sandbox()
        self._root = chk.ROOT
        chk.ROOT = self.root

    def tearDown(self):
        chk.ROOT = self._root

    def fails(self) -> list[str]:
        return chk.check(self.data)

    def animation(self, status="accepted"):
        a = self.data["assets"][0]
        a.update(kind="animation", type="A2", status=status,
                 status_history=chk.STATUSES[1:chk.STATUSES.index(status) + 1],
                 beats=[{"name": "开场", "start": 0, "end": 1},
                        {"name": "结论", "start": 1, "end": 3}],
                 duration="3s", parameters=[],
                 conclusion_frame={"beat": "结论", "output": a["output"]},
                 reduced_motion=a["output"], storyboard=a["output"])
        return a

    def test_valid_entry_passes(self):
        self.assertEqual([], self.fails())

    def test_duplicate_ids_fail(self):
        self.data["assets"].append(copy.deepcopy(VALID))
        self.assertTrue(any("ID 重复" in x for x in self.fails()))

    def test_bad_status_fails(self):
        self.data["assets"][0]["status"] = "done"
        self.assertTrue(any("非法状态" in x for x in self.fails()))

    def test_reviewed_requires_scores(self):
        self.data["assets"][0]["status"] = "reviewed"
        bad = self.fails()
        self.assertTrue(any("评分" in x for x in bad))

    def test_reviewed_with_scores_passes(self):
        a = self.data["assets"][0]
        a["status"] = "accepted"
        a["status_history"] = ["planned", "generated", "reviewed", "accepted"]
        a["review_scores"] = {dim: 4 for dim in chk.SCORE_DIMS}
        self.assertEqual([], self.fails())

    def test_animation_requires_motion_dimensions(self):
        a = self.data["assets"][0]
        a["kind"], a["type"] = "animation", "A2"
        a["status"] = "reviewed"
        a["review_scores"] = {dim: 5 for dim in chk.SCORE_DIMS}
        self.assertTrue(any("运动叙事" in x for x in self.fails()))

    def test_quant_rules_required_for_v3(self):
        del self.data["assets"][0]["quant_rules"]
        self.assertTrue(any("quant_rules" in x for x in self.fails()))

    def test_quant_rule1_layer_height_must_not_encode_values(self):
        self.data["assets"][0]["quant_rules"]["layer_encodes_value"] = True
        self.assertTrue(any("规则①层高" in x for x in self.fails()))

    def test_quant_rule1_values_go_via_overlay(self):
        self.data["assets"][0]["quant_rules"]["value_channel"] = "paper-layer"
        self.assertTrue(any("overlay-axis" in x for x in self.fails()))

    def test_quant_rule2_leaders_must_not_cross_subject(self):
        self.data["assets"][0]["quant_rules"]["leader_route"] = "across-subject"
        self.assertTrue(any("规则②" in x for x in self.fails()))

    def test_quant_rule3_accent_only_on_paper(self):
        self.data["assets"][0]["quant_rules"]["accent_on"] = "shade"
        self.assertTrue(any("规则③" in x for x in self.fails()))

    def test_quant_rule4_colour_alone_is_not_a_channel(self):
        self.data["assets"][0]["quant_rules"]["series_distinguisher"] = ["color"]
        self.assertTrue(any("规则④" in x for x in self.fails()))

    def test_v2_figure_skips_quant_rules(self):
        self.data["assets"][0]["type"] = "V2"
        del self.data["assets"][0]["quant_rules"]
        self.assertEqual([], self.fails())

    def test_legacy_v3_skips_quant_rules(self):
        a = self.data["assets"][0]
        a["status"] = "legacy-unreviewed"
        del a["quant_rules"]
        self.assertEqual([], self.fails())

    def test_flat_lineart_style_skips_quant_rules(self):
        """四条规矩守的是纸雕层高，FA-029 平面线稿不受约束。"""
        a = self.data["assets"][0]
        a["style_id"] = "FA-029"
        del a["quant_rules"]
        self.assertEqual([], self.fails())

    def test_animation_total_floor_is_30(self):
        a = self.data["assets"][0]
        a["kind"], a["type"], a["status"] = "animation", "A2", "reviewed"
        a["review_scores"] = {d: 4 for d in chk.SCORE_DIMS + chk.ANIM_DIMS}
        self.assertTrue(any("合计 28/35" in x for x in self.fails()))

    def test_animation_full_marks_passes(self):
        a = self.animation()
        a["review_scores"] = {d: 5 for d in chk.SCORE_DIMS + chk.ANIM_DIMS}
        self.assertEqual([], self.fails())

    def test_history_rejects_skipped_review(self):
        a = self.data["assets"][0]
        a.update(status="accepted", status_history=["planned", "generated", "accepted"],
                 review_scores={d: 5 for d in chk.SCORE_DIMS})
        self.assertTrue(any("逐级" in e for e in self.fails()))

    def test_previous_snapshot_catches_forged_complete_history(self):
        previous = copy.deepcopy(self.data)
        a = self.data["assets"][0]
        a.update(status="accepted", status_history=chk.STATUSES[1:5],
                 review_scores={d: 5 for d in chk.SCORE_DIMS})
        self.assertTrue(any("越级" in e for e in chk.check(self.data, previous)))

    def test_transition_is_adjacent_and_does_not_mutate_input(self):
        with self.assertRaises(ValueError):
            chk.transition(VALID, "accepted")
        reviewed = chk.transition(VALID, "reviewed")
        self.assertEqual("generated", VALID["status"])
        self.assertEqual(["planned", "generated", "reviewed"], reviewed["status_history"])

    def test_missing_alt_fails(self):
        del self.data["assets"][0]["alt"]
        self.assertTrue(any("缺 alt" in e for e in self.fails()))

    def test_animation_missing_parameters_or_final_frame_fails(self):
        a = self.animation()
        del a["parameters"]
        a["conclusion_frame"]["beat"] = "开场"
        bad = self.fails()
        self.assertTrue(any("parameters" in e for e in bad))
        self.assertTrue(any("末拍" in e for e in bad))

    def test_missing_print_fallback_fails(self):
        self.data["assets"][0]["print_fallback"] = "missing.svg"
        self.assertTrue(any("print_fallback 不存在" in e for e in self.fails()))

    def test_invalid_score_does_not_crash_or_pass(self):
        a = self.animation()
        for value in ("5", 6, float("nan"), True):
            a["review_scores"] = {d: value for d in chk.SCORE_DIMS + chk.ANIM_DIMS}
            self.assertTrue(any("评分" in e for e in self.fails()))

    def test_orphan_v2_fallback_is_not_silently_ignored(self):
        folder = self.root / "assets/svg-v2"
        folder.mkdir()
        (folder / "orphan-static.svg").write_text("<svg/>", encoding="utf-8")
        self.assertTrue(any("未登记" in e for e in self.fails()))

    def test_v2_print_fallback_cannot_embed_a_bitmap(self):
        folder = self.root / "assets/figures-v2"
        folder.mkdir()
        (folder / "demo.svg").write_text("<svg/>", encoding="utf-8")
        (folder / "demo-print.svg").write_text('<svg><image href="data:image/png;base64,AA=="/></svg>', encoding="utf-8")
        self.data["assets"][0].update(output="assets/figures-v2/demo.svg",
                                       print_fallback="assets/figures-v2/demo-print.svg")
        self.assertTrue(any("不得包含位图" in e for e in self.fails()))

    def test_missing_output_file_fails(self):
        (self.root / "assets/figures/ch17-demo.svg").unlink()
        self.assertTrue(any("output 不存在" in x for x in self.fails()))

    def test_unregistered_disk_asset_fails(self):
        (self.root / "assets/figures/orphan.svg").write_text(
            "<svg/>", encoding="utf-8")
        self.assertTrue(any("未登记" in x for x in self.fails()))

    def test_legacy_entry_skips_deep_fields(self):
        self.data["assets"] = [{
            "id": "legacy-x", "chapter": 0, "kind": "figure", "type": "V2",
            "output": "assets/figures/ch17-demo.svg",
            "status": "legacy-unreviewed"}]
        self.assertEqual([], self.fails())

    def test_bootstrap_is_idempotent(self):
        self.data["assets"] = []
        added = chk.bootstrap(self.data)
        self.assertEqual(1, added)
        self.assertEqual(0, chk.bootstrap(self.data))
        self.assertEqual("legacy-unreviewed", self.data["assets"][0]["status"])

    def test_bootstrap_infers_chapter_from_docs(self):
        self.data["assets"] = []
        chk.bootstrap(self.data)
        self.assertEqual(17, self.data["assets"][0]["chapter"])


if __name__ == "__main__":
    unittest.main()
