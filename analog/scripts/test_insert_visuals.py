#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""插图落位器契约测试：落点必须同时过密度闸的堆图与断层两关。

闸的口径来自 audit_visual_density（锚点标签本身不计字数，alt 再长也不算阅读），
所以这里全部用真闸函数验收，而不是复刻一套算法。
"""
import unittest

import audit_visual_density as avd
import insert_visuals as iv

OLD = "assets/svg/old.svg"
NEW = "assets/figures-v2/new-one.svg"
TAIL = "assets/svg/tail.svg"


def figure(src: str, alt: int = 0, cap: int = 0) -> str:
    return (f'<figure>\n<img src="{src}" width="720" alt="{"字" * alt}">\n'
            f'<figcaption>{"题" * cap}</figcaption>\n</figure>\n')


def asset(purpose: str, src: str = NEW) -> dict:
    return {"id": src, "output": src, "alt": "新图", "purpose": purpose,
            "anchor": "1.1", "chapter": 1}


def place(text: str, item: dict):
    pos = iv.best_insertion(text, item)
    if pos is None:
        return None
    return text[:pos] + "\n" + iv.figure_block(item) + text[pos:]


def violations(cand: str, src: str = NEW) -> list[str]:
    """这张图落进去之后，密度闸会挑出什么。"""
    anchors = avd.anchor_matches(cand)
    index = [i for i, (_s, _e, path) in enumerate(anchors) if path == src]
    if len(index) != 1:
        return [f"图 {src} 出现 {len(index)} 次"]
    i = index[0]
    start, end = anchors[i][0], anchors[i][1]
    bad = []
    if i:
        before = cand[anchors[i - 1][1]:start]
        if avd.nonws(before) < avd.MIN_SPACING and not avd.H3.search(before):
            bad.append(f"堆图（前向 {avd.nonws(before)} 字）")
    if i + 1 < len(anchors):
        after = cand[end:anchors[i + 1][0]]
        if avd.nonws(after) < avd.MIN_SPACING and not avd.H3.search(after):
            bad.append(f"堆图（后向 {avd.nonws(after)} 字）")
    for gap in avd.gaps(avd.mask(cand)):
        if gap > avd.HARD_MAX_GAP:
            bad.append(f"断层（{gap} 字 > {avd.HARD_MAX_GAP}）")
    return bad


class PlacementTests(unittest.TestCase):
    def test_alt_text_does_not_count_as_reading_distance(self):
        """长 alt 撑开的是标签，不是读者要看的路——不能拿它当图间距。"""
        text = ("### 1.1 引子\n\n" + figure(OLD, alt=700, cap=100) + "\n"
                + "字" * 250 + "\n\n" + "文" * 900 + "\n\n" + "号" * 900 + "\n")
        cand = place(text, asset("字"))
        self.assertIsNotNone(cand, "后面还有够远的段落，不该整章放弃")
        self.assertEqual([], violations(cand))

    def test_refuses_to_open_a_hard_gap(self):
        """段末插入等于把说明文字记到右段账上，右段可能被顶过 1500。"""
        text = ("### 1.1 引子\n\n" + figure(OLD, cap=50) + "\n\n"
                + "字" * 700 + "\n\n" + "字" * 600 + "\n\n" + figure(TAIL, cap=50) + "\n")
        cand = place(text, asset("字" * 950))
        self.assertIsNotNone(cand)
        self.assertEqual([], violations(cand))
        # 落在前一段段落末尾会把 950 字说明全压进右段，必须选后一段。
        first_para_end = text.index("字" * 700) + 701
        early = text[:first_para_end] + "\n" + iv.figure_block(asset("字" * 950)) + text[first_para_end:]
        self.assertTrue(violations(early), "夹具本身要能复现断层，否则这条测试是空的")

    def test_second_figure_keeps_distance_from_the_first(self):
        """同一轮连插两张：后一张要把前一张当成已在场的图。"""
        text = ("### 1.1 引子\n\n" + "字" * 600 + "\n\n" + "文" * 200 + "\n\n"
                + "号" * 1200 + "\n")
        first = place(text, asset("字"))
        self.assertIsNotNone(first)
        second = place(first, asset("文", "assets/figures-v2/new-two.svg"))
        self.assertIsNotNone(second, "还有合法段落，不该直接放弃")
        self.assertEqual([], violations(second, "assets/figures-v2/new-two.svg"))
        self.assertEqual([], violations(second))

    def test_legal_placement_still_found(self):
        """反向对照：宽松排布不该被新规则误伤成无处可插。"""
        text = ("### 1.1 引子\n\n" + "字" * 600 + "\n\n" + "文" * 600 + "\n\n"
                + "号" * 600 + "\n")
        cand = place(text, asset("号"))
        self.assertIsNotNone(cand)
        self.assertEqual([], violations(cand))

    def test_cuts_an_oversized_gap_instead_of_giving_up(self):
        """一整节 5000 字没图：一张图补不平，但必须切短，而且切得最匀。"""
        text = ("### 1.1 引子\n\n" + figure(OLD, cap=50) + "\n\n"
                + "字" * 1000 + "\n\n" + "文" * 1000 + "\n\n" + "号" * 1000 + "\n\n"
                + "码" * 1000 + "\n\n" + "图" * 1000 + "\n\n"
                + figure(TAIL, cap=50) + "\n")
        cand = place(text, asset("表"))
        self.assertIsNotNone(cand, "切短也是进步，不能因为一张图补不完就整节放弃")
        self.assertEqual([], [v for v in violations(cand) if v.startswith("堆图")])
        # 五段各 1000 字：随便插都能变短，切在 2|3 处才算真的会挑落点。
        before = max(avd.gaps(avd.mask(text)))
        self.assertLess(max(avd.gaps(avd.mask(cand))), before * 0.65,
                        "同一档里要挑把长段切得最匀的落点")

    def test_returns_none_when_every_spot_is_illegal(self):
        """整节只剩一个短段落，硬插必然堆图——宁可报告不可落点。"""
        text = "### 1.1 引子\n\n" + figure(OLD, cap=100) + "\n\n" + "字" * 200 + "\n"
        self.assertIsNone(iv.best_insertion(text, asset("字")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
