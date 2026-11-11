"""真实 SVG 的播放/倍速/键盘/结论停留/无 JS/减弱动效回归，全部请求在本地拦截。"""
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright

from visual_player import load_players, player_html, wrap_visual_players

ROOT = Path(__file__).resolve().parents[1]


class VisualPlayerBuildTests(unittest.TestCase):
    def test_marked_v2_images_get_static_fallback_and_manifest_alt(self):
        players = load_players(ROOT)
        asset = next(iter(players.values()))
        markup = wrap_visual_players('<img src="' + asset["output"] + '" data-visual-player>', players, ROOT)
        self.assertIn('src="' + asset["reduced_motion"] + '"', markup)
        self.assertIn('data-animation-src="' + asset["output"] + '"', markup)
        self.assertIn('动画中心', markup)

    def test_unregistered_v2_animation_rejected(self):
        with self.assertRaises(ValueError):
            wrap_visual_players('<img src="assets/svg-v2/unregistered.svg">', {}, ROOT)

    def test_manifest_timeline_drift_rejected(self):
        asset = dict(next(iter(load_players(ROOT).values())))
        asset["duration"] = "999s"
        with self.assertRaises(ValueError):
            player_html(asset, ROOT)


class VisualPlayerBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.addClassCleanup(cls.pw.stop)
        cls.browser = cls.pw.chromium.launch(channel="chrome", headless=True)
        cls.addClassCleanup(cls.browser.close)
        cls.asset = load_players(ROOT)["assets/svg-v2/ch17-esr-sweep.svg"]
        cls.markup = player_html(cls.asset, ROOT)
        cls.js = (ROOT / "scripts/site_media/visual-player.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "scripts/site_media/visual-player.css").read_text(encoding="utf-8")

    def setUp(self):
        self.page = self.browser.new_page()
        self.addCleanup(self.page.close)
        self.bad_svg = False
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.route("**/*", self.route)

    def route(self, route):
        if route.request.url.endswith(".svg"):
            if self.bad_svg and route.request.resource_type != "image":
                route.fulfill(content_type="text/html", body="Unavailable")
            else:
                path = ROOT / "assets/svg-v2" / route.request.url.rsplit("/", 1)[1]
                route.fulfill(content_type="image/svg+xml", body=path.read_bytes())
        else:
            route.fulfill(content_type="text/html", body=self.html)

    def visit(self, *, javascript=True, reduced=False):
        self.page.emulate_media(reduced_motion="reduce" if reduced else "no-preference")
        script = '<script>var document$={subscribe:function(fn){window.initV2=fn;fn();}}</script><script>' + self.js + '</script>' if javascript else ''
        self.html = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><style>body{margin:16px}*{box-sizing:border-box}' + self.css + '</style><main>' + self.markup + '</main>' + script
        self.page.goto("https://visual.test/lesson.html")

    def start(self):
        self.page.get_by_role("button", name="播放动画", exact=True).click()
        expect(self.page.get_by_role("slider", name="动画进度")).to_be_visible()

    def time(self):
        return self.page.locator("object").evaluate("el => el.contentDocument.documentElement.getCurrentTime()")

    def scrub(self, seconds):
        self.page.get_by_role("slider").evaluate("(el,t)=>{el.value=String(t);el.dispatchEvent(new Event('input',{bubbles:true}));}", seconds)

    def test_no_js_and_initial_state_are_static_and_readable(self):
        for javascript in (False, True):
            self.visit(javascript=javascript)
            expect(self.page.locator(".visual-player img")).to_have_attribute("src", self.asset["reduced_motion"])
            self.assertEqual(0, self.page.locator("object").count())
            expect(self.page.get_by_role("link", name="动画中心")).to_be_visible()

    def test_play_pause_keyboard_seek_and_replay(self):
        self.visit()
        self.start()
        expect(self.page.get_by_role("button", name="暂停", exact=True)).to_be_focused()
        self.page.wait_for_function("Number(document.querySelector('input[type=range]').value) > .2")
        self.page.get_by_role("button", name="暂停", exact=True).click()
        before = self.time()
        self.page.wait_for_timeout(120)
        self.assertAlmostEqual(before, self.time(), places=2)
        self.page.get_by_role("button", name="3. 内部生热").click()
        self.assertAlmostEqual(3.6, self.time(), places=2)
        expect(self.page.locator('.visual-player-time')).to_have_text('3.6 / 8 秒')
        slider = self.page.get_by_role("slider")
        slider.focus()
        self.page.keyboard.press("ArrowRight")
        self.assertAlmostEqual(3.61, self.time(), places=2)
        self.page.get_by_role("button", name="重播", exact=True).click()
        self.assertLess(self.time(), 1)
        self.assertEqual([], self.errors)

    def test_speed_changes_elapsed_svg_time(self):
        self.visit(); self.start()
        elapsed = []
        for speed in ("0.5", "1.5"):
            self.scrub(1)
            self.page.get_by_role("combobox", name="播放速度").select_option(speed)
            self.page.get_by_role("button", name="播放", exact=True).click()
            self.page.wait_for_timeout(600)
            self.page.get_by_role("button", name="暂停", exact=True).click()
            elapsed.append(self.time() - 1)
        self.assertGreater(elapsed[1], elapsed[0] * 2)

    def test_ends_once_on_conclusion_and_reduced_motion_never_autoplays(self):
        self.visit(); self.start(); self.scrub(7.9)
        self.page.get_by_role("button", name="播放", exact=True).click()
        expect(self.page.get_by_role("status")).to_have_text("已到结论：闭环")
        self.page.wait_for_timeout(160)
        self.assertAlmostEqual(8, self.time(), places=2)
        self.page.emulate_media(reduced_motion="reduce")
        expect(self.page.locator("object")).to_have_count(0)
        expect(self.page.locator(".visual-player img")).to_be_visible()
        self.start()
        expect(self.page.get_by_role("button", name="播放", exact=True)).to_be_visible()
        self.assertAlmostEqual(8, self.time(), places=2)

    def test_failed_load_restores_static_and_can_retry(self):
        self.visit(); self.bad_svg = True
        self.page.get_by_role("button", name="播放动画", exact=True).click()
        expect(self.page.get_by_role("status")).to_contain_text("加载失败")
        expect(self.page.locator(".visual-player img")).to_be_visible()
        self.bad_svg = False; self.start()

    def test_mobile_no_overflow_and_reinitialization_is_idempotent(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.visit(); self.start()
        self.page.evaluate("initV2(); initV2();")
        self.assertEqual(1, self.page.get_by_role("slider").count())
        self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), 390)
        self.page.evaluate("document.querySelector('main').innerHTML=''; initV2();")
        self.assertEqual([], self.errors)


if __name__ == "__main__":
    unittest.main()
