"""README/BOOK internal-link integrity: every `#fragment` link must resolve.

Links come in two forms — HTML (`href="#..."` in nav blocks) and Markdown
(`[text](#frag)` everywhere else). Both must point at an existing
`<a id="...">`, and neither may be empty. Catches empty fragments
(e.g. `[★ 必读精选](#)`) and anchors left behind after section renames.

Both generated Markdown products are checked. `README.md` is the short portal
(anchors from `docs/index.md` only); `BOOK.md` is the full single-file
concatenation, so it is the one that exercises the whole-book anchor union and
catches cross-page anchor drift such as a renamed section id. Checking only the
portal would silently drop that coverage. Pure stdlib, runs in seconds.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("README.md", "BOOK.md")


class ReadmeLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = {}
        for name in TARGETS:
            text = (ROOT / name).read_text(encoding="utf-8")
            cls.docs[name] = (text, set(re.findall(r'<a id="([^"]+)"\s*></a>', text)))

    def test_ids_exist(self):
        for name, (_, ids) in self.docs.items():
            with self.subTest(name):
                self.assertTrue(ids, f"{name}: no <a id> anchors found — regex may be wrong")

    def test_all_fragment_links_resolve(self):
        for name, (text, ids) in self.docs.items():
            with self.subTest(name):
                hrefs = re.findall(r'href="#([^"]*)"', text) + re.findall(r'\]\(#([^)]*)\)', text)
                self.assertTrue(hrefs, f"{name}: no #fragment links found — regex may be wrong")
                empty = sorted({h for h in hrefs if not h})
                self.assertEqual(empty, [],
                                 f"{name}: empty fragment links (`](#)` / `href=\"#\"`) must have a target")
                missing = sorted({h for h in hrefs if h and h not in ids})
                self.assertEqual(missing, [], f"{name}: fragments without a matching <a id>: {missing}")

    def test_book_carries_the_whole_book_anchor_union(self):
        """The full file must anchor far more than the portal, or coverage regressed."""
        portal = self.docs["README.md"][1]
        book = self.docs["BOOK.md"][1]
        self.assertGreater(len(book), 10 * len(portal),
                           "BOOK.md should hold the whole-book anchor set, not just the portal's")


if __name__ == "__main__":
    unittest.main()
