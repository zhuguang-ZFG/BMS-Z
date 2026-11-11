#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""backlog 点位布局校验器的夹具测试：不碰真实章节，只验「计划能不能落成合法布局」。

backlog 是人手写的行号清单，会写错三种东西：插到被替代文字之前、行号落在段落中间、
在太短的段里塞两张图。校验器的价值就是把这三种错误变成退出码，而不是靠读 YAML 放心。
"""
import tempfile
import unittest
from pathlib import Path

import audit_visual_density as avd
import check_backlog_layout as cbl

FIG_LEN = cbl.CAPTION_CHARS


def write_raw(text: str, name: str = "p1-01-ch0.md") -> Path:
    tmp = Path(tempfile.mkdtemp())
    path = tmp / name
    path.write_text(text, encoding="utf-8")
    return path


def write_doc(blocks: list[str], name: str = "p1-01-ch0.md") -> Path:
    """blocks 的每一项是一个段落（内部可多行），段间自动空行，首行是章标题。"""
    return write_raw("# 第 0 章\n\n" + "\n\n".join(blocks) + "\n", name)


def write_backlog(points: list[dict], source: Path, chapter: int = 0) -> Path:
    import yaml
    tmp = Path(tempfile.mkdtemp())
    path = tmp / f"ch{chapter:02d}.yml"
    path.write_text(yaml.safe_dump(
        {"chapter": chapter, "source": source.as_posix(),
         "budget": avd.BUDGETS[chapter], "points": points},
        allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def filler(n: int) -> str:
    return "字" * n


def anchor(src: str = "assets/figures/existing.svg") -> str:
    return f'<img src="{src}" width="720" alt="既有锚点">'


def visible(lines: list[str]) -> list[str]:
    return [l for l in lines if l.strip()]


class ParagraphBlockTests(unittest.TestCase):
    def test_blocks_are_nonblank_runs(self):
        p = write_doc(["第一段", "第二段的\n两行", "<figure>\n<img>\n</figure>"])
        self.assertEqual([(1, 1), (3, 3), (5, 6), (8, 10)],
                         cbl.paragraphs(p.read_text("utf-8")))

    def test_single_line_blocks(self):
        text = write_doc(["甲", "乙"]).read_text("utf-8")
        self.assertEqual([(1, 1), (3, 3), (5, 5)], cbl.paragraphs(text))


class ApplyPlanTests(unittest.TestCase):
    def test_insert_lands_after_the_deleted_text(self):
        p = write_doc([filler(200), filler(900), filler(200)])
        out = cbl.apply_plan(p.read_text("utf-8"),
                             [{"id": "x", "insert_after_line": 5,
                               "delete_lines": [[5, 5]]}])
        seq = visible(out.split("\n"))
        self.assertEqual(4, len(seq), "章题／原段／占位图／尾段")
        self.assertIn("<img", seq[2], "占位图顶在被替代段的位置上")
        self.assertNotIn(filler(900), out, "被替代的原文必须真的删掉")

    def test_caption_chars_count_into_the_run_after_the_anchor(self):
        """图注不像 alt 那样被掩掉：它落在锚点之后的那一段里。"""
        p = write_doc([anchor(), filler(300), filler(1200), filler(300)])
        out = cbl.apply_plan(p.read_text("utf-8"),
                             [{"id": "x", "insert_after_line": 7,
                               "delete_lines": [[7, 7]]}])
        seg = avd.gaps(cbl.simulated_text(out))
        self.assertGreaterEqual(seg[-1], 300 + FIG_LEN, seg)

    def test_inserting_before_the_replaced_text_is_worse(self):
        """把同一张图挪到被替代文字之前，右段反而更长——这就是 backlog 的硬口径。"""
        p = write_doc([anchor(), filler(200), filler(1300), filler(300)])
        text = p.read_text("utf-8")
        after = max(avd.gaps(cbl.simulated_text(cbl.apply_plan(
            text, [{"id": "x", "insert_after_line": 7, "delete_lines": [[7, 7]]}]))))
        before = max(avd.gaps(cbl.simulated_text(cbl.apply_plan(
            text, [{"id": "x", "insert_after_line": 5}]))))
        self.assertLess(after, before, (after, before))

    def test_points_apply_from_a_single_pass(self):
        """一次成型，点位之间不互相顶行号。"""
        p = write_doc([anchor(), filler(200), filler(200), filler(200), filler(200)])
        out = cbl.apply_plan(p.read_text("utf-8"),
                             [{"id": "a", "insert_after_line": 5},
                              {"id": "b", "insert_after_line": 9}])
        self.assertEqual(3, out.count("<img"), "两点都落位")


class LegalityTests(unittest.TestCase):
    BLOCKS = [(1, 1), (3, 3), (5, 8), (10, 12)]

    def test_insert_inside_its_own_deletion_is_illegal(self):
        problems = cbl.check_point({"id": "x", "insert_after_line": 6,
                                   "delete_lines": [[5, 8]]}, self.BLOCKS, 99)
        self.assertTrue(problems, problems)

    def test_insert_midway_through_a_paragraph_is_illegal(self):
        self.assertTrue(cbl.check_point({"id": "x", "insert_after_line": 6},
                                        self.BLOCKS, 99))

    def test_insert_at_paragraph_end_is_legal(self):
        self.assertEqual([], cbl.check_point(
            {"id": "x", "insert_after_line": 8, "delete_lines": [[5, 8]]},
            self.BLOCKS, 99))

    def test_insert_after_a_blank_line_is_legal(self):
        """点位也可以落在两段落之间的空行上（等价于段末之后）。"""
        self.assertEqual([], cbl.check_point({"id": "x", "insert_after_line": 4},
                                             self.BLOCKS, 99))

    def test_deleting_half_a_paragraph_is_illegal(self):
        self.assertTrue(cbl.check_point({"id": "x", "insert_after_line": 8,
                                         "delete_lines": [[6, 8]]},
                                        self.BLOCKS, 99))

    def test_deleting_an_existing_anchor_is_illegal(self):
        """既有锚点所在行不是新图的下刀处。"""
        problems = cbl.check_point({"id": "x", "insert_after_line": 12,
                                    "delete_lines": [[10, 12]]},
                                   [(10, 12)], 99,
                                   [(11, 12, "assets/figures/keep.svg")])
        self.assertTrue(any("既有锚点" in s for s in problems), problems)

    def test_out_of_range_line_is_illegal(self):
        self.assertTrue(cbl.check_point({"id": "x", "insert_after_line": 400},
                                        self.BLOCKS, 9))

    def test_duplicate_insert_lines_are_flagged(self):
        self.assertTrue(cbl.duplicate_inserts(
            [{"id": "a", "insert_after_line": 8},
             {"id": "b", "insert_after_line": 8}]))


class BaselineRunTests(unittest.TestCase):
    def test_runs_cover_head_anchor_gaps_and_tail(self):
        raw = f"# 第 0 章\n\n{filler(200)}\n\n{anchor()}\n\n{filler(2000)}\n\n尾"
        p = write_raw(raw)
        text, anchors, _ = avd.load(p)
        runs = cbl.baseline_runs(text, anchors)
        self.assertEqual(2, len(runs))
        self.assertEqual("assets/figures/existing.svg", runs[0]["next_asset"])
        self.assertIsNone(runs[-1]["next_asset"])
        self.assertEqual(2001, runs[1]["chars"], "含段末的「尾」")
        self.assertLess(runs[1]["start_line"], runs[1]["end_line"])

    def test_line_numbers_are_true_source_lines(self):
        """跨行 figure 不再把之后的断层行号往上顶（旧口径会少两行）。"""
        raw = ("# 第 0 章\n\n" + filler(100) + "\n\n"
               "<figure>\n<img src=\"assets/figures/multi.svg\" alt=\"m\">\n"
               "<figcaption>图注</figcaption>\n</figure>\n\n"
               + filler(200) + "\n\n<img src=\"assets/figures/two.svg\">\n")
        p = write_raw(raw)
        spans = cbl.anchor_spans(raw)
        self.assertEqual([(6, 6, "assets/figures/multi.svg"),
                          (12, 12, "assets/figures/two.svg")], spans)
        text, anchors, _ = avd.load(p)
        runs = cbl.baseline_runs(text, anchors)
        self.assertEqual(12, runs[-1]["start_line"],
                         "第二段起于第二张图的真实行号（旧口径报 10，少两行）")

    def test_run_of_a_line_is_found(self):
        raw = f"# 第 0 章\n\n{anchor()}\n\n{filler(2000)}\n\n{filler(50)}"
        p = write_raw(raw)
        text, anchors, _ = avd.load(p)
        self.assertEqual(1, cbl.run_at(cbl.baseline_runs(text, anchors), 7)["index"])


class VerifyTests(unittest.TestCase):
    def test_layout_that_still_breaks_hard_gap_is_reported(self):
        p = write_doc([anchor(), filler(4000), filler(300)])
        b = write_backlog([{"id": "x", "action": "new", "insert_after_line": 5}], p)
        v = cbl.verify(b)
        self.assertTrue(any("最长无图段" in f for f in v["failures"]), v["failures"])

    def test_layout_that_clears_the_gaps_passes(self):
        p = write_doc([anchor(), filler(1300), filler(1300), filler(300)])
        b = write_backlog([{"id": "x", "action": "new", "insert_after_line": 7,
                            "delete_lines": [[7, 7]]}], p)
        v = cbl.verify(b)
        self.assertEqual([], [f for f in v["failures"] if "最长无图段" in f],
                         v["failures"])

    def test_cluster_from_two_close_points_is_located_by_line(self):
        p = write_doc([anchor(), filler(500), filler(200), filler(500)])
        b = write_backlog([{"id": "x", "action": "new", "insert_after_line": 5},
                           {"id": "y", "action": "new", "insert_after_line": 7}], p)
        hits = cbl.verify(b)["spacing_conflicts"]
        self.assertTrue(hits, "两张图隔着 200 字，必须报出来")
        self.assertEqual((5, 7), (hits[0]["line_a"], hits[0]["line_b"]),
                         "行号折回正文原始行，不是模拟行")

    def test_action_keep_points_are_not_planned_as_inserts(self):
        p = write_doc([anchor(), filler(300), filler(200), filler(300)])
        b = write_backlog([{"id": "k", "action": "keep", "at_line": 3},
                           {"id": "x", "action": "new", "insert_after_line": 7}], p)
        self.assertEqual(1, cbl.verify(b)["planned"], "keep 点不新增锚点")

    def test_illegal_point_blocks_the_gate(self):
        p = write_doc([anchor(), filler(300), filler(200) + "\n" + filler(200)])
        b = write_backlog([{"id": "x", "action": "new", "insert_after_line": 7}], p)
        v = cbl.verify(b)
        self.assertTrue(v["problems"], v["problems"])
        self.assertEqual([], v["planned_ids"], "非法点位不进入套用")

    def test_stale_target_run_is_flagged(self):
        p = write_doc([anchor(), filler(800), filler(200)])
        b = write_backlog([{"id": "x", "action": "new", "insert_after_line": 5,
                            "target_run": 9999}], p)
        v = cbl.verify(b)
        self.assertTrue(any("target_run" in s for s in v["problems"]), v["problems"])


class DeferredStatusTests(unittest.TestCase):
    """落不下的点位登记成 deferred 就不参与套用，但必须写清为什么落不下。"""

    def test_deferred_point_is_not_simulated(self):
        p = write_doc([anchor(), filler(4000), filler(300)])
        b = write_backlog([{"id": "x", "action": "new", "insert_after_line": 5,
                            "status": "deferred", "defer_reason": "表格墙"}], p)
        v = cbl.verify(b)
        self.assertEqual(0, v["planned"])
        self.assertEqual(["x"], v["deferred"])
        self.assertEqual(1, v["audit"]["visuals"], "deferred 点位不该长出占位锚点")
        self.assertEqual([], v["problems"])

    def test_deferred_without_a_reason_is_a_problem(self):
        p = write_doc([anchor(), filler(800), filler(300)])
        b = write_backlog([{"id": "x", "action": "new", "insert_after_line": 5,
                            "status": "deferred"}], p)
        v = cbl.verify(b)
        self.assertTrue(any("blocked_by" in s for s in v["problems"]), v["problems"])

    def test_blocked_by_alone_is_an_acceptable_reason(self):
        p = write_doc([anchor(), filler(800), filler(300)])
        b = write_backlog([{"id": "x", "action": "new", "insert_after_line": 5,
                            "status": "deferred", "blocked_by": "table-runs"}], p)
        self.assertEqual([], cbl.verify(b)["problems"])

    def test_is_executable_covers_status_default(self):
        self.assertTrue(cbl.is_executable({"action": "new"}))
        self.assertFalse(cbl.is_executable({"action": "new", "status": "deferred"}))
        self.assertFalse(cbl.is_executable({"action": "keep", "status": "planned"}))


class SharedDeletionTests(unittest.TestCase):
    def test_two_points_cannot_replace_the_same_lines(self):
        p = write_doc([anchor(), filler(600), filler(600), filler(300)])
        b = write_backlog([{"id": "x", "action": "new", "insert_after_line": 5,
                            "delete_lines": [[5, 5]]},
                           {"id": "y", "action": "new", "insert_after_line": 7,
                            "delete_lines": [[5, 7]]}], p)
        v = cbl.verify(b)
        self.assertTrue(any("替代文字" in s for s in v["problems"]), v["problems"])

    def test_disjoint_deletions_are_fine(self):
        p = write_doc([anchor(), filler(600), filler(600), filler(300)])
        self.assertEqual([], cbl.duplicate_deletes(
            [{"id": "x", "delete_lines": [[3, 5]]}, {"id": "y", "delete_lines": [[7, 7]]}]))


if __name__ == "__main__":
    unittest.main()
