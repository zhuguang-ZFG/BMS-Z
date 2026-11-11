#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""章节分布闸：预算、1500 硬上限、1200 警告、堆图与 H2 零视觉（夹具测试）。"""
import json
import tempfile
import unittest
from pathlib import Path

import audit_visual_density as avd


def chapter(body: str, name: str = "p1-01-ch0.md") -> Path:
    tmp = Path(tempfile.mkdtemp())
    path = tmp / name
    path.write_text(body, encoding="utf-8")
    return path


IMG = '<img src="assets/figures/f{}.svg">'


def spaced(n: int, between: int) -> str:
    """n 张图，图间 between 字。"""
    return "\n".join("字" * between + "\n" + IMG.format(i) for i in range(n))


class GateTests(unittest.TestCase):
    def test_budget_failure_lists_chapter(self):
        p = chapter(spaced(2, 900))
        rows = [avd.audit(p)]
        bad = avd.failures(rows)
        self.assertTrue(any("预算" in line for line in bad))

    def test_hard_gap_failure(self):
        p = chapter("字" * 1600 + "\n" + IMG.format(0))
        r = avd.audit(p)
        self.assertEqual(1600, r["longest_gap"])
        self.assertEqual(1, r["hard_gaps"])
        self.assertTrue(any("1500" in line for line in avd.failures([r])))

    def test_warn_gap_is_not_failure(self):
        p = chapter("字" * 1300 + "\n" + IMG.format(0))
        r = avd.audit(p)
        self.assertEqual(1, r["warn_gaps"])
        self.assertEqual(0, r["hard_gaps"])

    def test_cluster_detected_when_gap_short_without_heading(self):
        body = IMG.format(0) + "\n" + "字" * 120 + "\n" + IMG.format(1)
        r = avd.audit(chapter(body))
        self.assertEqual(1, r["clusters"])

    def test_cluster_excused_by_heading(self):
        body = (IMG.format(0) + "\n" + "字" * 120 + "\n### 下一小节\n"
                + IMG.format(1))
        r = avd.audit(chapter(body))
        self.assertEqual(0, r["clusters"])

    def test_h2_over_800_without_visual_fails(self):
        body = "## 长小节\n\n" + "字" * 900 + "\n"
        r = avd.audit(chapter(body))
        self.assertEqual(1, len(r["h2_no_visual"]))

    def test_h2_over_800_with_visual_passes(self):
        body = "## 长小节\n\n" + "字" * 900 + "\n" + IMG.format(0) + "\n"
        r = avd.audit(chapter(body))
        self.assertEqual(0, len(r["h2_no_visual"]))


class RealTreeTests(unittest.TestCase):
    """真实文档树：口径回归钉在冻结 head，活树只断言不倒退。

    baseline-2026-11-04.json 冻结在 meta.head；本改造计划要持续往正文加图
    （出口 ≥390 锚点），对活树做精确相等断言会让每一波图都读作回归。
    所以：口径对不对，在冻结 head 上逐位复现基线来验；活树只要求
    章节数不减、每章锚点不少于基线、总数不低于 200。
    """
    BASELINE = (Path(__file__).resolve().parents[1]
                / "docs/superpowers/visual/baseline-2026-11-04.json")

    @classmethod
    def frozen(cls) -> list[tuple[dict, dict]]:
        import subprocess
        base = json.loads(cls.BASELINE.read_text(encoding="utf-8"))
        head = base["meta"]["head"]
        fixtures = cls.BASELINE.parent / "frozen-8961d38"
        rows = []
        for row in base["chapters"]:
            fixture = fixtures / Path(row["file"]).name
            if fixture.is_file():
                # 合并仓没有原仓历史（squash 导入），冻结 head 的章节原文
                # 按 head 名固化在 fixtures 里，逐字节复现基线。
                text = fixture.read_text(encoding="utf-8")
            else:
                text = subprocess.run(
                    ["git", "show", f"{head}:{row['file']}"], cwd=avd.ROOT,
                    capture_output=True, check=True).stdout.decode("utf-8")
            tmp = Path(tempfile.mkdtemp()) / Path(row["file"]).name
            tmp.write_text(text, encoding="utf-8")
            live = avd.audit(tmp)
            live.pop("file")
            expect = dict(row)
            expect.pop("file")
            rows.append((expect, live))
        return rows

    def test_convention_reproduces_frozen_baseline(self):
        """口径回归：审计器在冻结 head 上逐位复现 baseline JSON。

        换任何统计口径（字符、锚点、间距）都必须先让这条绿——
        基线数字才可复现，波次对比才有意义。
        """
        for expect, live in self.frozen():
            self.assertEqual(expect, live)

    def test_live_tree_never_loses_anchors(self):
        base = {r["chapter"]: r["visuals"]
                for r in json.loads(
                    self.BASELINE.read_text(encoding="utf-8"))["chapters"]}
        rows = [avd.audit(p) for p in avd.chapters()]
        self.assertEqual(19, len(rows))
        for r in rows:
            self.assertGreaterEqual(
                r["visuals"], base[r["chapter"]],
                f"ch{r['chapter']} 锚点少于冻结基线")
        self.assertGreaterEqual(sum(r["visuals"] for r in rows), 200)

    def test_every_chapter_has_a_budget(self):
        for n in range(19):
            self.assertIn(n, avd.BUDGETS)

    def test_referenced_assets_exist(self):
        missing = []
        for p in avd.DOCS.glob(avd.CHAPTER_GLOB):
            if not avd.CHAPTER_NAME.search(p.name):
                continue
            for src in avd.audit(p)["assets"]:
                if not (avd.ROOT / src).exists():
                    missing.append(f"{p.name}: {src}")
        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
