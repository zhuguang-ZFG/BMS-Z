#!/usr/bin/env python3
"""题库拆分：章末题目、附录 F 答案与编号稳定性。"""
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import quiz  # noqa: E402

QUIZ = """
<h1>题库</h1>
<p><a id="p9--quiz-ch0"></a></p><h2>第 0 章</h2><ol>
<li><p><a id="p9--q-ch0-01" data-quiz-question="true"></a>问题一？</p>
<details class="note"><summary>答案</summary><p>答案一。</p></details></li>
<li><p><a id="p9--q-ch0-02" data-quiz-question="true"></a>问题二？</p>
<details class="note"><summary>答案</summary><p>答案二。</p></details></li>
</ol>
<h2>专题加练</h2><ol>
<li><p><a id="p9--q-extra-01" data-quiz-question="true"></a>专题问题？</p>
<details class="note"><summary>答案</summary><p>专题答案。</p></details></li>
</ol>
"""


class ParseTests(unittest.TestCase):
    def test_splits_chapter_and_extra(self):
        data = quiz.parse_quiz(QUIZ)
        self.assertEqual([0], list(data.chapters))
        self.assertEqual(2, len(data.chapters[0]))
        self.assertEqual("q-ch0-01", data.chapters[0][0].id)
        self.assertEqual("问题一？", data.chapters[0][0].question)
        self.assertEqual(1, len(data.extra))
        self.assertEqual("q-extra-01", data.extra[0].id)

    def test_strips_emoji_from_answers(self):
        data = quiz.parse_quiz(QUIZ.replace("答案一。", "✅ 答案一。"))
        self.assertEqual("✓ 答案一。", data.chapters[0][0].answer)


class MergeTests(unittest.TestCase):
    def test_appends_exercise_section_without_answers(self):
        data = quiz.parse_quiz(QUIZ)
        result = quiz.merge_exercises("<h1>第 0 章</h1><p>正文。</p>",
                                      data.chapters[0], "p1-01-ch0")
        self.assertIn('class="chapter-exercises"', result)
        self.assertIn('id="p1-01-ch0--q-q-ch0-01"', result)
        self.assertIn("问题一？", result)
        self.assertNotIn("<details", result)
        self.assertNotIn("答案一", result)

    def test_exercise_section_has_stable_chapter_anchor(self):
        data = quiz.parse_quiz(QUIZ)
        result = quiz.merge_exercises("<h1>第 0 章</h1><p>正文。</p>",
                                      data.chapters[0], "p1-01-ch0")
        self.assertIn('id="chapter-0--exercises"', result)

    def test_answers_only_in_appendix(self):
        data = quiz.parse_quiz(QUIZ)
        page = quiz.render_answers(data, {0: "p1-01-ch0"}, "p9-00-quiz")
        self.assertIn("答案一。", page)
        self.assertIn("专题答案。", page)
        self.assertEqual(2, page.count('class="answer-list"'))
        self.assertNotIn("<details", page)
        self.assertIn('href="#p1-01-ch0--q-q-ch0-01"', page)


if __name__ == "__main__":
    unittest.main()
