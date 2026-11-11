"""Exercise the generated gallery in Chrome, without external network requests.

Run: python -B -m unittest discover -s scripts -p test_gallery_interactions.py -v
"""
import unittest

from playwright.sync_api import sync_playwright

from build_site import GALLERY_CSS, GALLERY_JS, parse_demos, render_gallery


class GalleryInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        playwright = sync_playwright().start()
        cls.addClassCleanup(playwright.stop)
        cls.browser = playwright.chromium.launch(channel="chrome", headless=True)
        cls.addClassCleanup(cls.browser.close)
        cls.html = (
            '<!doctype html><html><head><meta charset="utf-8"><style>'
            + GALLERY_CSS + '</style></head><body style="overflow: auto">'
            + '<input id="other-search"><textarea id="notes"></textarea>'
            + '<div id="editor" contenteditable="true">notes</div>'
            + render_gallery(parse_demos()[0])
            + '<script>' + GALLERY_JS + '</script></body></html>'
        )

    def setUp(self):
        self.page = self.browser.new_page()
        self.addCleanup(self.page.close)
        self.page.route("**/*", self.respond)

    def respond(self, route):
        if route.request.resource_type == "document":
            route.fulfill(content_type="text/html", body=self.html)
        else:
            route.fulfill(content_type="image/svg+xml", body=(
                '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="580"/>'
            ))

    def visit(self, query=""):
        self.page.goto("https://gallery.test/gallery.html" + query)

    def focused(self):
        return self.page.evaluate("document.activeElement.id")

    def test_modal_traps_focus_and_restores_opener_and_scroll(self):
        self.visit()
        opener = self.page.locator(".gal-play").first
        opener.click()
        self.assertEqual("gal-modal-close", self.focused())
        self.assertEqual("hidden", self.page.evaluate("document.body.style.overflow"))
        self.page.locator("#gal-modal-link").focus()
        self.page.keyboard.press("Tab")
        self.assertEqual("gal-modal-prev", self.focused())
        self.page.keyboard.press("Shift+Tab")
        self.assertEqual("gal-modal-link", self.focused())
        self.page.keyboard.press("Escape")
        self.assertTrue(opener.evaluate("el => el === document.activeElement"))
        self.assertEqual("auto", self.page.evaluate("document.body.style.overflow"))
        self.assertIsNone(self.page.locator("#gal-modal-img").get_attribute("src"))

    def test_single_result_skips_hidden_navigation_and_random_restores_focus(self):
        self.visit()
        filename = self.page.locator(".gal-card").first.get_attribute("data-file")
        self.page.locator("#gal-search").fill(filename)
        self.assertEqual(1, self.page.locator(".gal-card:visible").count())
        self.page.locator("#gal-random").click()
        self.page.locator("#gal-modal-link").focus()
        self.page.keyboard.press("Tab")
        self.assertEqual("gal-modal-close", self.focused())
        self.page.keyboard.press("Shift+Tab")
        self.assertEqual("gal-modal-link", self.focused())
        self.page.keyboard.press("Escape")
        self.assertEqual("gal-random", self.focused())

    def test_shortcut_preserves_editable_fields(self):
        self.visit()
        for field in ("other-search", "notes", "editor", "gal-search"):
            with self.subTest(field=field):
                self.page.locator("#" + field).focus()
                self.page.keyboard.press("/")
                self.assertEqual(field, self.focused())
        self.page.locator("#gal-search").fill("")
        self.page.locator(".gal-play").first.focus()
        self.page.keyboard.press("/")
        self.assertEqual("gal-search", self.focused())

    def test_filters_preserve_url_context_and_normalize_shared_query(self):
        self.visit("?ch=invalid&q=%20LDO%20&source=bookmark#gallery")
        self.assertEqual("ldo", self.page.locator("#gal-search").input_value())
        self.assertEqual("true", self.page.locator('.gal-chip[data-ch="all"]').get_attribute("aria-pressed"))
        self.assertGreater(self.page.locator(".gal-card:visible").count(), 0)
        self.page.evaluate("history.replaceState({saved: 42}, '', location.href)")
        self.page.locator("#gal-search").fill("")
        self.assertEqual("https://gallery.test/gallery.html?source=bookmark#gallery", self.page.url)
        self.assertEqual({"saved": 42}, self.page.evaluate("history.state"))
        self.page.locator('.gal-chip[data-ch="12"]').click()
        self.page.locator("#gal-search").fill("米勒")
        self.page.reload()
        self.assertEqual("米勒", self.page.locator("#gal-search").input_value())
        self.assertEqual("true", self.page.locator('.gal-chip[data-ch="12"]').get_attribute("aria-pressed"))
        self.assertIn("source=bookmark", self.page.url)
        self.assertTrue(self.page.url.endswith("#gallery"))

    def test_empty_results_disable_random_and_navigation_wraps(self):
        self.visit()
        self.page.locator("#gal-search").fill("no-such-animation-xyz")
        self.assertTrue(self.page.locator("#gal-empty").is_visible())
        self.assertTrue(self.page.locator("#gal-random").is_disabled())
        self.page.locator("#gal-search").fill("")
        self.assertTrue(self.page.locator("#gal-random").is_enabled())
        count = self.page.locator(".gal-card").count()
        self.page.locator(".gal-play").first.click()
        self.page.keyboard.press("ArrowLeft")
        self.assertEqual(f"{count} / {count}", self.page.locator("#gal-modal-pos").inner_text())
        self.page.keyboard.press("ArrowRight")
        self.assertEqual(f"1 / {count}", self.page.locator("#gal-modal-pos").inner_text())


if __name__ == "__main__":
    unittest.main()
