"""Test lesson controls against the real SVGs, with no external requests."""
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
LESSONS = {"rc": "rc-charge.svg", "mosfet": "mosfet-four-beats.svg", "lm358": "lm358-dual.svg"}


class LearningInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        playwright = sync_playwright().start()
        cls.addClassCleanup(playwright.stop)
        cls.browser = playwright.chromium.launch(channel="chrome", headless=True)
        cls.addClassCleanup(cls.browser.close)
        cls.js = (ROOT / "scripts/site_media/learning.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "scripts/site_media/learning.css").read_text(encoding="utf-8")

    def setUp(self):
        self.page = self.browser.new_page()
        self.addCleanup(self.page.close)
        self.errors = []
        self.requests = []
        self.bad_svg = False
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.route("**/*", self.respond)

    def respond(self, route):
        url = route.request.url
        self.requests.append(url)
        if url.endswith(".svg"):
            if self.bad_svg and route.request.resource_type != "image":
                route.fulfill(content_type="text/html", body="Unavailable")
            else:
                route.fulfill(content_type="image/svg+xml", body=(ROOT / "assets/svg" / url.rsplit("/", 1)[1]).read_bytes())
        elif "youtube" in url:
            route.fulfill(content_type="text/html", body="External player placeholder")
        else:
            route.fulfill(content_type="text/html", body=self.html)

    def visit(self, lesson="mosfet", javascript=True):
        svg = LESSONS[lesson]
        self.html = (
            '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<style>body{margin:16px}*{box-sizing:border-box}' + self.css + '</style></head><body>'
            f'<main><p><img src="assets/svg/{svg}" width="800" height="680" data-study="{lesson}" alt="教学动画"></p>'
            '<p><a data-study-video href="https://www.youtube.com/watch?v=Te5YYVZiOKs">MOSFET 教程</a></p></main>'
            + ('<script>var document$={subscribe:function(fn){window.initLesson=fn;fn();}};</script><script>' + self.js + '</script>' if javascript else '')
            + '</body></html>'
        )
        self.page.goto("https://lessons.test/lesson.html")

    def enable(self):
        self.page.get_by_role("button", name="启用动画控制").click()
        expect(self.page.get_by_role("button", name="播放", exact=True)).to_be_visible()

    def state(self):
        return self.page.locator("object").evaluate("el => {const s=el.contentDocument.documentElement; return {time:s.getCurrentTime(),paused:s.animationsPaused()};}")

    def test_all_lessons_pause_at_their_named_stages(self):
        cases = {"rc": ("③ 对照时间常数与曲线", 4), "mosfet": ("③ 米勒平台，漏压下降", 7), "lm358": ("③ 输出摆幅限制", 7)}
        for lesson, (label, seconds) in cases.items():
            with self.subTest(lesson=lesson):
                self.visit(lesson)
                self.enable()
                expect(self.page.get_by_role("button", name="播放", exact=True)).to_be_focused()
                stage = self.page.get_by_role("button", name=label)
                stage.click()
                self.assertTrue(self.state()["paused"])
                self.assertAlmostEqual(seconds, self.state()["time"], places=2)
                expect(stage).to_have_attribute("aria-pressed", "true")
                if lesson == "mosfet":
                    # At 490ns (7/10 of 700ns), VGS is on its plateau and VDS falls.
                    points = self.page.locator("object").evaluate("el => {const s=el.contentDocument.documentElement;return [...s.querySelectorAll('circle.cursor-dot')].map(e=>{const b=e.getBBox(),p=s.createSVGPoint();p.x=b.x+b.width/2;p.y=b.y+b.height/2;const v=p.matrixTransform(s.getCTM().inverse().multiply(e.getCTM()));return {x:v.x,y:v.y};});}")
                    self.assertTrue(any(abs(p["x"] - 559) < 1 and abs(p["y"] - 351.56) < 1 for p in points), points)
        self.assertEqual([], self.errors)

    def test_play_pause_replay_and_keyboard_scrubbing_control_svg_time(self):
        self.visit()
        self.enable()
        self.page.get_by_role("button", name="播放", exact=True).click()
        self.page.wait_for_function("document.querySelector('object').contentDocument.documentElement.getCurrentTime()>0.2")
        self.page.get_by_role("button", name="暂停", exact=True).click()
        before = self.state()["time"]
        self.page.wait_for_timeout(180)
        self.assertAlmostEqual(before, self.state()["time"], places=2)
        self.page.get_by_role("button", name="③ 米勒平台，漏压下降").click()
        slider = self.page.get_by_role("slider")
        slider.focus()
        self.page.keyboard.press("ArrowRight")
        self.assertAlmostEqual(7.01, self.state()["time"], places=2)
        self.assertTrue(self.state()["paused"])
        expect(self.page.get_by_role("button", name="③ 米勒平台，漏压下降")).to_have_attribute("aria-pressed", "false")
        self.page.get_by_role("button", name="从头重播").click()
        self.assertFalse(self.state()["paused"])
        self.assertLess(self.state()["time"], 1)

    def test_bad_svg_keeps_image_link_and_allows_retry(self):
        self.bad_svg = True
        self.visit()
        self.page.get_by_role("button", name="启用动画控制").click()
        expect(self.page.locator("figcaption")).to_contain_text("暂不可用")
        expect(self.page.locator(".study-viewport img")).to_be_visible()
        expect(self.page.get_by_role("link", name="打开原图")).to_have_attribute("href", "https://lessons.test/assets/svg/mosfet-four-beats.svg")
        self.bad_svg = False
        self.enable()
        self.assertEqual([], self.errors)

    def test_video_only_loads_on_click_and_close_removes_player(self):
        self.visit()
        self.assertFalse(any("youtube" in url for url in self.requests))
        self.assertEqual(0, self.page.locator("iframe").count())
        self.page.get_by_role("button", name="在本页观看").click()
        expect(self.page.locator("iframe")).to_have_attribute("src", "https://www.youtube-nocookie.com/embed/Te5YYVZiOKs?playsinline=1&autoplay=0")
        expect(self.page.get_by_role("button", name="关闭播放器")).to_be_focused()
        self.page.get_by_role("button", name="关闭播放器").click()
        self.assertEqual(0, self.page.locator("iframe").count())
        expect(self.page.get_by_role("button", name="在本页观看")).to_be_focused()
        expect(self.page.get_by_role("link", name="MOSFET 教程")).to_be_visible()
        self.assertEqual(0, self.page.locator("p > .study-video").count())

    def test_mobile_zoom_scrolls_inside_viewport_and_restores(self):
        self.page.set_viewport_size({"width": 360, "height": 780})
        self.visit()
        self.enable()
        zoom = self.page.get_by_role("button", name="放大细节")
        zoom.click()
        self.assertTrue(self.page.locator(".study-viewport").evaluate("el=>el.scrollWidth>el.clientWidth"))
        self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), 360)
        zoom = self.page.get_by_role("button", name="适应宽度")
        zoom.click()
        self.assertTrue(self.page.locator(".study-viewport").evaluate("el=>el.scrollWidth<=el.clientWidth+1"))
        for button in self.page.locator(".study-controls button").all():
            self.assertGreaterEqual(button.bounding_box()["height"], 44)

    def test_navigation_initializes_once_and_new_lesson_works(self):
        self.visit()
        self.enable()
        self.page.evaluate("initLesson(); initLesson();")
        self.assertEqual(1, self.page.locator(".study-player").count())
        self.page.evaluate("document.querySelector('main').innerHTML='<p><img src=\"assets/svg/rc-charge.svg\" data-study=\"rc\" alt=\"RC\"></p>';initLesson();document.dispatchEvent(new Event('visibilitychange'));")
        self.enable()
        self.page.get_by_role("button", name="③ 对照时间常数与曲线").click()
        self.assertAlmostEqual(4, self.state()["time"], places=2)
        self.assertEqual([], self.errors)

    def test_without_enhancement_image_and_video_link_remain(self):
        self.visit(javascript=False)
        expect(self.page.locator("img[data-study]")).to_be_visible()
        expect(self.page.get_by_role("link", name="MOSFET 教程")).to_be_visible()
        self.assertEqual(0, self.page.locator("object,iframe").count())


if __name__ == "__main__":
    unittest.main()
