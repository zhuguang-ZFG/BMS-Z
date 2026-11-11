#!/usr/bin/env python3
"""真实仓库整书：77 页、无站点残留、锚点全通、习题拆分与 16K 打印契约。"""
import html
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import assemble, config  # noqa: E402
from book.manifest import direct_files, excluded_files, load_manifest  # noqa: E402

SITE_READY = (config.SITE_DIR / "p1-01-ch0.html").is_file()
SHELL_MARKERS = (
    "md-content__button", "headerlink", "data-study-video",
    "<iframe", "<video", '<pre class="mermaid">', "mermaid.min.js",
    "TODO", "TBD", "待补", "占位",
)
# 印刷品不得残留 emoji。站点新契约已不带 emoji，此表仍是回归护栏；
# 以转义写出，避免测试源码本身出现 emoji 字面量。
EMOJI = ("\U0001F4DA\U0001F9ED\U0001F523\U0001F4A1\u26A0\uFE0F"
         "\U0001F3AF\U0001F527\U0001F4D0\U0001F9EA\U0001F4DD")
# MathJax 的内联源码里可能出现 TODO/emoji；内联 base64 也可能恰含 TBD。
# 占位检查只针对可见正文，先剥离脚本/样式与 base64 data URI 载荷。
SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1>", re.S | re.I)
DATA_URI_RE = re.compile(
    r"data:[a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=]+")


def _part_intro(document: str, page_id: str) -> str | None:
    """只在指定篇首页内找导语，避免匹配到后续篇的段落。"""
    start = document.find(f'id="{page_id}"')
    if start < 0:
        return None
    following = document.find('id="part-', start + 1)
    section = document[start:following if following >= 0 else len(document)]
    match = re.search(r'<p class="part-intro">(.*?)</p>', section, re.S)
    return match.group(1) if match else None


@unittest.skipUnless(SITE_READY, "先运行 python scripts/build_site.py --build")
class RealBookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.out = Path(cls.tmp.name)
        cls.manifest = load_manifest()
        cls.html_path = assemble.build_html(
            cls.out, config.SITE_DIR, config.DATA_DIR, config.DOCS,
            cls.manifest, rebuild_site=False, final=False)
        cls.document = cls.html_path.read_text(encoding="utf-8")
        cls.visible = DATA_URI_RE.sub(
            "", SCRIPT_STYLE_RE.sub("", cls.document))
        cls.model = json.loads(
            (cls.out / config.MODEL_NAME).read_text(encoding="utf-8"))

    def test_inventory_and_manifest_coverage(self):
        self.assertEqual(77, len(self.model["pages"]))
        self.assertEqual(77, len({page["id"] for page in self.model["pages"]}))
        self.assertEqual(54, len(direct_files(self.manifest)))
        self.assertEqual(10, len(excluded_files(self.manifest)))
        ids = {page["id"] for page in self.model["pages"]}
        for page_id in ("page-p0-11-conventions", "page-p0-12-symbols",
                        "page-p9-15-glossary", "appendix-a-table",
                        "book-index", "colophon"):
            self.assertIn(page_id, ids)
        for page_id in ("part-i", "part-ii", "part-iii", "part-iv", "part-v"):
            intro = _part_intro(self.visible, page_id)
            self.assertIsNotNone(intro, f"{page_id} 缺少篇导语")
            self.assertTrue(intro.strip(), f"{page_id} 篇导语为空")

    def test_part_intro_lookup_does_not_cross_sections(self):
        document = ('<section id="part-i"><h1>一</h1></section>'
                    '<section id="part-ii">'
                    '<p class="part-intro">第二篇的导语</p></section>')
        self.assertIsNone(_part_intro(document, "part-i"))

    def test_site_shell_and_draft_markers_are_gone(self):
        for marker in SHELL_MARKERS:
            self.assertNotIn(marker, self.visible)
        for emoji in EMOJI:
            self.assertNotIn(emoji, self.visible)
        self.assertNotIn("<details", self.visible)
        self.assertNotIn("<summary", self.visible)
        self.assertGreaterEqual(self.visible.count('class="book-reveal"'), 4,
                                "章内折叠块应展开为可见块")
        self.assertNotRegex(self.visible, r'(?:src|srcset|poster)="https?://')
        self.assertNotRegex(self.document, r"url\(https?://")

    def test_ids_unique_and_internal_links_resolve(self):
        # 排除 data-id 等复合属性，只统计真正的 id 属性。
        ids = re.findall(r'(?<![\w-])id="([^"]+)"', self.visible)
        self.assertEqual(len(ids), len(set(ids)), "整书不应有重复 id")
        known = set(ids)
        hrefs = {unquote(html.unescape(value))
                 for value in re.findall(r'\bhref="#([^"]+)"', self.visible)}
        missing = sorted(hrefs - known)
        self.assertEqual([], missing[:20], f"{len(missing)} 个锚点无法到达")
        self.assertEqual([], self.model["audit"]["errors"])

    def test_every_chapter_opener_carries_its_emblem(self):
        """19 章章首各有一枚手绘单线章徽，内联 SVG、装饰性、无远程引用。"""
        self.assertEqual(19, self.document.count('class="chapter-emblem"'))
        # MkDocs 的 md_in_html 会把 div 的属性排序，因此不锁 class/aria-hidden 的先后。
        self.assertEqual(19, len(re.findall(
            r'<div (?=[^>]*class="chapter-emblem")(?=[^>]*aria-hidden="true")'
            r'[^>]*><svg [^>]*viewBox="0 0 64 64"[^>]*stroke="currentColor"',
            self.document)))
        self.assertNotRegex(self.document, r'<div [^>]*class="chapter-emblem"[^>]*\bid=')

    def test_chapter_exercises_and_appendix_answers(self):
        self.assertEqual(19, self.document.count('class="chapter-exercises"'))
        self.assertEqual(20, self.document.count('class="answer-list"'))
        merged = len(re.findall(
            r'<li><a id="[^"]+--q-q-ch\d+-\d+"></a>', self.visible))
        self.assertEqual(90, merged, "90 道章节题应全部并入章末")
        self.assertEqual(merged, self.document.count('class="answer-ref"'),
                         "章末每题都要在附录 F 有一条答案回链")
        self.assertEqual(34, self.document.count('class="answer-question"'))
        self.assertIn('id="appendix-f-answers"', self.document)
        self.assertIn('href="#p1-01-ch0--q-q-ch0-01"', self.document)

    def test_wave1_chapter_visible_char_floors(self):
        # 2026-11 可读性改写签核后重定 ch0/ch11 的基线：源头契约
        # （test_wave1_chapters 的 15000/18000 字）仍生效，这里只防印刷稿
        # 相对源稿二次缩水，不再卡改写前含重复铺垫的旧长度。
        floors = {"0": 13200, "2": 15000, "11": 16500, "14": 17000,
                  "16": 13000}
        chapters = self.model["stats"]["chapters"]
        for chapter, floor in floors.items():
            self.assertIn(chapter, chapters)
            self.assertGreaterEqual(
                chapters[chapter]["chars"], floor,
                f"第 {chapter} 章可见正文 {chapters[chapter]['chars']} < {floor}")

    def test_stats_cross_real_content_thresholds(self):
        stats = self.model["stats"]
        self.assertEqual(77, stats["logical_pages"])
        self.assertGreater(stats["images"], 120,
                           "真实构建 137 张；阈值防批量丢图，不锁死数量")
        self.assertGreater(stats["formulas"], 800,
                           "Phase 0 草稿阈值；最终 >2000 在 Phase 5 启用")
        self.assertGreaterEqual(stats["figures"], 1)
        self.assertGreaterEqual(stats["tables"], 1)
        self.assertGreater(len(self.model["toc"]), 100)
        self.assertGreaterEqual(len(self.model["lof"]), 1)
        self.assertGreater(stats["tables"], 0)
        self.assertIsInstance(self.model["lot"], list)

    def test_colophon_does_not_claim_unverified_physical_pagination(self):
        page = next(item for item in self.model["pages"]
                    if item["id"] == "colophon")
        self.assertIn("77 个逻辑页", page["html"])
        self.assertIn("PRINT-SPEC.md", page["html"])
        self.assertNotIn("书脊厚度约", page["html"])

    def test_print_contract_is_inline(self):
        self.assertIn('<style media="print">', self.document)
        match = re.search(
            r'<style media="print">(.*?)</style>', self.document, re.S)
        self.assertIsNotNone(match, "16K 打印样式必须内联")
        print_css = match.group(1)
        self.assertIn("size: 185mm 260mm", print_css)
        self.assertIn("@page :left", print_css)
        # book.css 仍保留 A4 @page 给 1.0 管线；16K 的打印块必须覆盖它。
        self.assertNotIn("size: A4", print_css)
        self.assertIn("data:font/woff2;base64,", self.document)


if __name__ == "__main__":
    unittest.main()
