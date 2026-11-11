#!/usr/bin/env python3
"""「为什么」机制卡：两端接线（站点卡片 + 印刷卡片）与配色。"""
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
ROOT = BOOK.parent
sys.path.insert(0, str(BOOK))
sys.path.insert(0, str(ROOT / "scripts"))

from book import transforms  # noqa: E402


class WhyCardWiringTests(unittest.TestCase):
    def test_why_kind_is_wired_into_site_and_book(self):
        from build_site import CALLOUT_KINDS
        self.assertEqual("why", CALLOUT_KINDS["为什么"])
        self.assertEqual("为什么", transforms.CALLOUT_LABELS["why"])

    def test_why_becomes_a_card_not_a_plain_quote(self):
        """没接线时它会安静退化成 blockquote——印出来就看不出是机制卡了。"""
        fragment = ('<div class="callout callout-why">'
                    "<p><strong>为什么</strong>：电荷被搬走了。</p></div>")
        result = transforms.transform_callouts(transforms.strip_emoji(fragment))
        self.assertIn('<aside class="book-callout book-callout-why"', result)
        self.assertIn('data-label="为什么"', result)
        self.assertNotIn("book-quote", result)

    def test_why_has_styles_for_site_a4_and_print(self):
        site = (ROOT / "scripts" / "site_media" / "typography.css").read_text(
            encoding="utf-8")
        self.assertIn(".callout-why", site)
        self.assertIn('[data-md-color-scheme="slate"] .md-typeset .callout-why',
                      site)
        a4 = (BOOK / "styles" / "book.css").read_text(encoding="utf-8")
        self.assertIn(".book-callout-why", a4)
        print_css = (BOOK / "styles" / "print.css").read_text(encoding="utf-8")
        self.assertIn(".book .book-callout-why", print_css)


if __name__ == "__main__":
    unittest.main()
