#!/usr/bin/env python3
"""Playwright 冒烟：离线整书能断网排版公式、渲染计算器并跳转。"""
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

import build_book  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


def launch_chromium(playwright):
    try:
        return playwright.chromium.launch(headless=True)
    except Exception:
        # 部分机器只装了系统 Chrome，没有 Playwright 自带的 Chromium。
        return playwright.chromium.launch(headless=True, channel="chrome")


# 整书 HTML 约 19 MB，满载回归时 30 s 的默认导航超时会偶发误报。
NAV_TIMEOUT = 90000


@unittest.skipIf(sync_playwright is None, "Playwright 未安装")
class BrowserBook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = BOOK / "dist"
        cls.html = out / build_book.OUTPUT_NAME
        if not cls.html.is_file():
            cls.html = build_book.build_html(out, rebuild_site=False)

    def test_offline_formulas_calculators_and_toc(self):
        with sync_playwright() as p:
            browser = launch_chromium(p)
            page = browser.new_page(reduced_motion="reduce")
            errors = []
            page.on("console", lambda msg: errors.append(msg.text)
                    if msg.type == "error" else None)
            page.goto(self.html.resolve().as_uri(), wait_until="load",
                      timeout=NAV_TIMEOUT)
            page.wait_for_function(
                "window.MathJax && MathJax.startup && MathJax.startup.promise",
                timeout=60000)
            page.wait_for_function(
                "document.querySelectorAll('mjx-container').length > 1000",
                timeout=120000)
            self.assertGreater(
                page.evaluate("document.querySelectorAll('mjx-container').length"), 1000)
            self.assertGreater(
                page.evaluate("document.querySelectorAll('[data-calc-ready]').length"), 0)
            page.keyboard.press("Tab")
            self.assertIn("book-skip",
                          page.evaluate("document.activeElement.className"))
            skip = page.locator(".book-skip").bounding_box()
            self.assertIsNotNone(skip)
            self.assertGreaterEqual(skip["y"], 0, "跳到目录应在聚焦时可见")
            page.keyboard.press("Enter")
            page.wait_for_function("location.hash === '#book-toc'")
            page.click('a[href="#page-p1-01-ch0"]')
            page.wait_for_function(
                "document.getElementById('page-p1-01-ch0').getBoundingClientRect().top < 300")
            page.click('#page-p1-01-ch0 .book-page-nav a[rel="next"]')
            page.wait_for_function("location.hash === '#page-p1-02-ch1'")
            page.wait_for_function(
                "document.getElementById('page-p1-02-ch1').getBoundingClientRect().top < 300")
            page.click('#page-p1-02-ch1 .book-page-nav a[rel="prev"]')
            page.wait_for_function("location.hash === '#page-p1-01-ch0'")
            page.wait_for_function(
                "document.getElementById('page-p1-01-ch0').getBoundingClientRect().top < 300")
            page.keyboard.press("Control+k")
            self.assertEqual("book-search-input",
                             page.evaluate("document.activeElement.id"))
            page.fill("#book-search-input", "米勒")
            page.wait_for_selector("#book-search-results li[role=option]")
            self.assertGreater(
                page.locator("#book-search-results li[role=option]").count(), 0)
            self.assertGreater(
                page.locator("#book-search-results mark").count(), 0,
                "命中的查询词应高亮")
            self.assertIn("结果", page.locator("#book-search-status").inner_text())
            self.assertTrue(page.locator("#book-search-status").is_visible())
            page.keyboard.press("ArrowDown")
            page.wait_for_function(
                "document.getElementById('book-search-input')"
                ".getAttribute('aria-activedescendant')")
            page.keyboard.press("Enter")
            page.wait_for_function(
                "document.getElementById('book-search-panel').hidden")
            self.assertRegex(page.evaluate("location.hash"), r"^#.+")
            self.assertIsNotNone(page.evaluate(
                "document.getElementById(decodeURIComponent(location.hash.slice(1)))"))
            page.wait_for_timeout(150)
            position = page.evaluate(
                """() => {
                    const el = document.getElementById(
                        decodeURIComponent(location.hash.slice(1)));
                    const header = document.querySelector('.book-header');
                    return {
                        top: el.getBoundingClientRect().top,
                        headerBottom: header.getBoundingClientRect().bottom,
                    };
                }""")
            self.assertGreaterEqual(
                position["top"], position["headerBottom"] - 1,
                "桌面端搜索结果也不应被 sticky 页眉遮挡")
            page.keyboard.press("Control+k")
            self.assertEqual("book-search-input",
                             page.evaluate("document.activeElement.id"))
            page.keyboard.press("Escape")
            self.assertNotEqual("book-search-input",
                                page.evaluate("document.activeElement.id"))
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_selector("#book-top:not([hidden])")
            page.wait_for_function(
                "getComputedStyle(document.getElementById('book-progress'))"
                ".transform === 'matrix(1, 0, 0, 1, 0, 0)'")
            page.click("#book-top")
            page.wait_for_function("window.scrollY < 60")
            page.wait_for_function(
                "document.getElementById('book-top').hidden")
            page.wait_for_function(
                "getComputedStyle(document.getElementById('book-progress'))"
                ".transform === 'matrix(0, 0, 0, 1, 0, 0)'")
            self.assertEqual([], errors[:5])
            browser.close()

    def _open_mobile(self, browser):
        page = browser.new_page(
            viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page.goto(
            self.html.resolve().as_uri() + "#page-p1-01-ch0",
            wait_until="load", timeout=NAV_TIMEOUT)
        page.wait_for_function(
            "document.getElementById('page-p1-01-ch0')"
            ".getBoundingClientRect().top < 300")
        return page

    def test_mobile_header_and_search_typography_is_readable(self):
        with sync_playwright() as p:
            browser = launch_chromium(p)
            page = self._open_mobile(browser)
            fonts = page.evaluate(
                """() => {
                    const size = (selector) => parseFloat(
                        getComputedStyle(document.querySelector(selector)).fontSize);
                    return {
                        header: size('.book-header'),
                        toc: size('.book-header-toc'),
                        skip: size('.book-skip'),
                    };
                }""")
            self.assertGreaterEqual(fonts["header"], 13,
                                    "页眉不应继承 Material 的 10px 字号")
            self.assertGreaterEqual(fonts["toc"], 13)
            self.assertGreaterEqual(fonts["skip"], 13)
            page.fill("#book-search-input", "电容")
            page.wait_for_selector("#book-search-results li[role=option]")
            hit_font = page.evaluate(
                "parseFloat(getComputedStyle("
                "document.querySelector('.book-search-hit')).fontSize)")
            self.assertGreaterEqual(hit_font, 13, "搜索命中标题应与页眉同样可读")
            browser.close()

    def test_mobile_toc_layout_and_anchor_offset(self):
        with sync_playwright() as p:
            browser = launch_chromium(p)
            page = self._open_mobile(browser)
            layout = page.evaluate(
                """() => {
                    const header = document.querySelector('.book-header');
                    const tocLink = document.querySelector('#book-toc li a');
                    const footerToc = document.querySelector('.book-page-nav-toc');
                    const list = document.querySelector('#book-toc ul');
                    const heading = document.querySelector('#page-p1-01-ch0 h1');
                    return {
                        columns: getComputedStyle(list).columnCount,
                        tocLinkHeight: tocLink.getBoundingClientRect().height,
                        footerTocHeight: footerToc.getBoundingClientRect().height,
                        headerBottom: header.getBoundingClientRect().bottom,
                        headingTop: heading.getBoundingClientRect().top,
                        scrollWidth: document.documentElement.scrollWidth,
                        viewport: window.innerWidth,
                    };
                }""")
            self.assertEqual("1", layout["columns"], "手机端全书目录应单栏显示")
            self.assertGreaterEqual(layout["tocLinkHeight"], 44,
                                    "目录条目的触达高度应至少 44px")
            self.assertGreaterEqual(layout["footerTocHeight"], 44,
                                    "页尾全书目录按钮的触达高度应至少 44px")
            self.assertGreaterEqual(
                layout["headingTop"], layout["headerBottom"] - 1,
                "锚点标题不应被 sticky 页眉遮挡")
            self.assertLessEqual(layout["scrollWidth"], layout["viewport"],
                                 "手机端不应出现横向滚动")
            browser.close()

    def test_mobile_anchor_targets_clear_sticky_header(self):
        fragments = (
            ("#p1-01-ch0--0", "章标题"),
            ("#p1-05-ch4--43", "节标题"),
            ("#p0-05-picks--pick-rc", "交叉引用"),
        )
        with sync_playwright() as p:
            browser = launch_chromium(p)
            page = browser.new_page(
                viewport={"width": 390, "height": 844}, reduced_motion="reduce")
            for fragment, label in fragments:
                page.goto(
                    self.html.resolve().as_uri() + fragment,
                    wait_until="load", timeout=NAV_TIMEOUT)
                page.wait_for_function(
                    "(() => {"
                    " const el = document.getElementById("
                    "decodeURIComponent(location.hash.slice(1)));"
                    " return el && el.getBoundingClientRect().top < 300;"
                    "})()")
                page.wait_for_timeout(150)
                metrics = page.evaluate(
                    """() => {
                        const el = document.getElementById(
                            decodeURIComponent(location.hash.slice(1)));
                        const header = document.querySelector('.book-header');
                        return {
                            top: el.getBoundingClientRect().top,
                            headerBottom: header.getBoundingClientRect().bottom,
                            margin: getComputedStyle(el).scrollMarginTop,
                        };
                    }""")
                self.assertGreaterEqual(
                    metrics["top"], metrics["headerBottom"] - 1,
                    f"{label}目标 {fragment} 应落在页眉下方，实际 top="
                    f"{metrics['top']:.1f}px、页眉底部={metrics['headerBottom']:.1f}px、"
                    f"scroll-margin-top={metrics['margin']}")
            page.goto(self.html.resolve().as_uri(), wait_until="load",
                      timeout=NAV_TIMEOUT)
            page.fill("#book-search-input", "米勒")
            page.wait_for_selector("#book-search-results li[role=option]")
            page.keyboard.press("ArrowDown")
            page.wait_for_function(
                "document.getElementById('book-search-input')"
                ".getAttribute('aria-activedescendant')")
            page.keyboard.press("Enter")
            page.wait_for_function(
                "document.getElementById('book-search-panel').hidden")
            page.wait_for_timeout(150)
            search = page.evaluate(
                """() => {
                    const el = document.getElementById(
                        decodeURIComponent(location.hash.slice(1)));
                    const header = document.querySelector('.book-header');
                    return {
                        hash: location.hash,
                        top: el.getBoundingClientRect().top,
                        headerBottom: header.getBoundingClientRect().bottom,
                    };
                }""")
            self.assertGreaterEqual(
                search["top"], search["headerBottom"] - 1,
                f"搜索结果 {search['hash']} 应落在页眉下方，实际 top="
                f"{search['top']:.1f}px、页眉底部={search['headerBottom']:.1f}px")
            browser.close()

    def test_chapter_number_watermark_uses_brand_tint(self):
        with sync_playwright() as p:
            browser = launch_chromium(p)
            page = self._open_mobile(browser)
            colors = page.evaluate(
                """() => ({
                    ink: getComputedStyle(document.body).color,
                    watermark: getComputedStyle(
                        document.querySelector('#page-p1-01-ch0 .chapter-hero-num')).color,
                })""")
            self.assertNotEqual(colors["ink"], colors["watermark"],
                                "章号水印应使用品牌淡染，而不是正文黑色")
            browser.close()


if __name__ == "__main__":
    unittest.main()
