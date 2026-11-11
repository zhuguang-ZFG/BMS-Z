"""「减弱动效」在真实 Chromium 里的行为护栏。

Run: python -B -m unittest discover -s scripts -p test_reduced_motion.py -v

为什么需要它：108 张 SVG 全是自动播放的 SMIL 动画，前庭敏感的用户打开站点
没有任何开关能停下来。正确做法**不是**在 SVG 里写 media query ——
SVG 作为 `<img>` 载入时（本站就是这么嵌的）Chrome 把 `prefers-reduced-motion`
**恒判为 reduce**，于是 SVG 内部的 media query 要么恒不生效、要么恒生效；
一旦恒生效，全站动画对**所有人**都是静止的（v3.45 正是这么翻车的）。
所以改成由**页面**选源：`build_site.py` 生成 `<stem>.reduce.svg` 静止版，
再用 `<picture><source media="(prefers-reduced-motion: reduce)">` 挑。

这里用真实 Chromium 断言四件事：
  1. `<picture>` 在 reduce 下**确实选中**静止版、无偏好下选中动画版（选源是机制本身）；
  2. 静止版里**没有任何可见的运动载体**（108 张逐张查）；
  3. 静止版里**节拍字幕组一个都没被误伤**（仍可见）；
  4. 动画版里同一个探针必须真能看见上千个运动载体 —— 防假绿：
     否则"没漏"可能只是因为选择器根本没命中。
另外验证站点自身的悬停位移在 reduce 下也停掉。

注意：探针必须把 SVG 当**顶层文档**打开才量得到 computed style；而"选源"那一步
必须在**页面**里做。两者各司其职，缺一不可 —— 只测前者正是 v3.45 漏掉的那一半。
"""
from pathlib import Path
import re
import shutil
import tempfile
import unittest

from playwright.sync_api import sync_playwright

from build_site import (GALLERY_CSS, GALLERY_JS, parse_demos, render_gallery,
                        wrap_picture, write_reduce_variants)

ROOT = Path(__file__).resolve().parents[1]
SVGS = sorted((ROOT / "assets" / "svg").glob("*.svg"))

# 会「飞」的动画：位移/形变类。opacity 淡入淡出不算运动，节拍字幕靠它分时显示。
PROBE = """() => {
  const motion = 'animateMotion, animateTransform, animate:not([attributeName="opacity"])';
  let carriers = 0, visibleMotion = 0, captions = 0, captionsVisible = 0;
  const samples = [];
  for (const el of document.querySelectorAll('*')) {
    if (!Array.from(el.children).some(k => k.matches(motion))) { continue; }
    carriers += 1;
    const hidden = getComputedStyle(el).display === 'none';
    const hasText = el.querySelector('text') !== null;
    if (hasText) {
      captions += 1;
      if (!hidden) { captionsVisible += 1; }
    } else if (!hidden) {
      visibleMotion += 1;
      if (samples.length < 3) { samples.push(el.tagName + '.' + (el.getAttribute('class') || '-')); }
    }
  }
  return { carriers, visibleMotion, captions, captionsVisible, samples };
}"""

# 把 108 张图各自的 <picture> 摆在一个页面里，好让浏览器自己挑源
HARNESS = """<!doctype html><meta charset="utf-8"><body>
%s
<script>
window.selected = () => Array.prototype.map.call(
  document.querySelectorAll('picture img'),
  function (i) { return i.currentSrc.split('/').pop(); });
</script>
"""


class ReducedMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 把真实 SVG 复制到临时目录，再用 build_site 的同一段逻辑生成静止版 ——
        # 测的就是线上那对文件，不是另造的样本。
        temporary = tempfile.TemporaryDirectory(prefix="analog-reduce-")
        cls.addClassCleanup(temporary.cleanup)
        cls.svg_dir = Path(temporary.name) / "svg"
        cls.svg_dir.mkdir(parents=True)
        for svg in SVGS:
            shutil.copyfile(svg, cls.svg_dir / svg.name)
        cls.written = write_reduce_variants(cls.svg_dir)

        # 用 build_site 的**真实**包装函数拼 <picture>，而不是手写一份 —— 否则
        # srcset 写错源这类 bug 就绕过了这组测试（变异验证时踩过）。
        blocks = "\n".join(
            wrap_picture(svg.name, '<img src="%s" alt="">' % svg.name)
            for svg in SVGS)
        harness = cls.svg_dir / "_harness.html"
        harness.write_text(HARNESS % blocks, encoding="utf-8")
        cls.harness = harness.as_uri()

        playwright = sync_playwright().start()
        cls.addClassCleanup(playwright.stop)
        cls.browser = playwright.chromium.launch(channel="chrome", headless=True)
        cls.addClassCleanup(cls.browser.close)
        page = cls.browser.new_page(viewport={"width": 900, "height": 700})
        cls.addClassCleanup(page.close)
        cls.page = page

        # ① 选源：在**页面**上下文里看 <picture> 挑了哪一份
        cls.selected = {}
        for mode in ("no-preference", "reduce"):
            page.emulate_media(reduced_motion=mode)
            page.goto(cls.harness)
            cls.selected[mode] = page.evaluate("() => window.selected()")

        # ② 逐张量运动载体：这里必须把 SVG 当顶层文档打开才读得到 computed style
        cls.report = {}
        for mode, names in (("animated", [s.name for s in SVGS]),
                            ("reduce", [s.stem + ".reduce.svg" for s in SVGS])):
            page.emulate_media(reduced_motion="no-preference")
            rows = {}
            for name in names:
                page.goto((cls.svg_dir / name).as_uri())
                rows[name] = page.evaluate(PROBE)
            cls.report[mode] = rows

    def totals(self, mode):
        rows = self.report[mode].values()
        return (sum(r["carriers"] for r in rows),
                sum(r["visibleMotion"] for r in rows),
                sum(r["captions"] for r in rows),
                sum(r["captionsVisible"] for r in rows))

    # ---------- 选源：机制本身 ----------
    def test_picture_picks_the_still_version_when_reduced_motion_is_on(self):
        """reduce 下每个 <picture> 都必须挑中静止版。

        这是整条链路的命门：包了 <picture> 但 srcset 写错（或没生成静止版），
        浏览器会回落到动画版 —— 页面照常渲染、测试若只查"文件在不在"也照常绿。
        """
        names = self.selected["reduce"]
        self.assertEqual(len(SVGS), len(names), "探针没看到全部 <picture>")
        wrong = [n for n in names if not n.endswith(".reduce.svg")]
        self.assertEqual([], wrong, "这些图在减弱动效下没走静止版：" + repr(wrong[:8]))

    def test_picture_picks_the_animated_version_without_the_preference(self):
        """防假绿：无偏好下必须挑**动画版**，否则整站会一直是静止的。"""
        names = self.selected["no-preference"]
        self.assertEqual(len(SVGS), len(names), "探针没看到全部 <picture>")
        wrong = [n for n in names if n.endswith(".reduce.svg")]
        self.assertEqual([], wrong, "这些图在无偏好下也走了静止版：" + repr(wrong[:8]))

    # ---------- 静止版 / 动画版的内容 ----------
    def test_the_still_version_has_no_visible_motion_at_all(self):
        _, visible, _, _ = self.totals("reduce")
        leaked = {name: r["samples"] for name, r in self.report["reduce"].items()
                  if r["visibleMotion"]}
        self.assertEqual(0, visible,
                         f"静止版里仍有 {visible} 个运动元素可见：" + repr(list(leaked.items())[:5]))

    def test_the_still_version_keeps_beat_captions_readable(self):
        _, _, captions, captions_visible = self.totals("reduce")
        self.assertGreaterEqual(captions, 350, f"静止版里只找到 {captions} 个字幕组")
        self.assertEqual(captions, captions_visible,
                         "静止版把节拍字幕也藏掉了——字幕是多路复用的，藏了就整段读不到")

    def test_the_animated_version_really_moves(self):
        """防假绿：动画版必须能看见大量运动载体，否则上面的"没漏"是空转。"""
        carriers, visible, captions, captions_visible = self.totals("animated")
        self.assertGreaterEqual(carriers, 1000, f"只找到 {carriers} 个运动载体，探针失效")
        self.assertGreaterEqual(captions, 350, f"只找到 {captions} 个字幕组")
        self.assertEqual(captions, captions_visible, "动画版里字幕组不该被隐藏")
        self.assertEqual(carriers - captions, visible,
                         "动画版里不该有被隐藏的运动载体："
                         f"{carriers} 个载体 - {captions} 个字幕组 != {visible} 个可见")

    # ---------- 站点自身的动效 ----------
    def test_gallery_cards_do_not_slide_under_reduced_motion(self):
        html = ('<!doctype html><html><head><meta charset="utf-8"><style>'
                + GALLERY_CSS + '</style></head><body>'
                + render_gallery(parse_demos()[0])
                + '<script>' + GALLERY_JS + '</script></body></html>')
        page = self.browser.new_page()
        self.addCleanup(page.close)
        page.route("**/*", lambda route: route.fulfill(
            content_type="text/html" if route.request.resource_type == "document"
            else "image/svg+xml", body=html if route.request.resource_type == "document"
            else '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="580"/>'))
        for mode, expect in (("no-preference", "matrix"), ("reduce", "none")):
            page.emulate_media(reduced_motion=mode)
            page.goto("https://gallery.test/gallery.html")
            card = page.locator(".gal-card").first
            card.hover()
            transform = card.evaluate("el => getComputedStyle(el).transform")
            if expect == "none":
                self.assertEqual("none", transform,
                                 "减弱动效下卡片悬停仍会位移：" + transform)
            else:
                self.assertTrue(re.search(r"matrix|translate", transform),
                                "默认偏好下卡片悬停位移消失了，测试失去意义：" + transform)


if __name__ == "__main__":
    unittest.main()
