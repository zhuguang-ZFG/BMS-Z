"""首屏（顶栏 + 首页 hero）的视觉护栏 —— 这些只能在浏览器里验。

Run: python -B -m unittest discover -s scripts -p test_first_screen.py -v

为什么不能靠静态检查：
  1. **hero 皮肤有没有真的贴上**。`reading.css` 里 hero 的底色是
     `background-color` + `background-image` 分开写的 —— 一旦有人改回
     `background:` **简写**，background-image（品牌渐变 + 蓝图点阵）会被整个重置成
     none，而页面**照样能构建、照样不报错**，只是首屏变回一块灰底。
     实测踩过：typography.css 里写的同一批规则被 reading.css 的简写覆盖掉了。
  2. **chip 文字在暗色主题下读不读得出**。chip 文字色是 `color-mix` 掺出来的，
     而 `--md-primary-fg-color` 在暗色主题下**不变**（仍是 #4051b5），直接拿它当
     文字色压在本站深靛底色上只有 2.56:1。色值算得对不对，只有量像素才知道。
  3. **四个 chip 会不会掉行**。Material 有一条 `[dir=ltr] .md-typeset ul li
     {margin-left:1.25em}`，特异性 (0,2,2) 比 `.md-typeset .learning-stats > li`
     的 (0,2,1) 高 —— 每个 chip 会凭空多 17.5px 左外边距（四个共 70px），
     刚好把第四枚挤到第二行。这类「差 1px」的排版事故静态查不出来。
  4. **顶栏那两处**（品牌标识是描边还是实心盘、仓库链接有没有被截断）同样是
     纯 CSS 计算结果：Material 的 `.md-header__button.md-logo :is(img,svg)
     {fill:currentcolor}` 会压掉根 <svg> 上的 fill 属性，而 `.md-header__source`
     在桌面上宽度写死 11.5rem、跟视口无关。两条都是「构建不报错、只有人看得见」。
  5. **hero 底部那条走线的正弦**（v3.50）与**首页顶部的去盒化**（§5.5 的 `:has()`）
     也一样：mask 的 data URI 转义坏一个字符，波形就整条消失；`:has()` 那几条失效，
     h1 与引子重新长出盒子，hero 被推下折叠线。两种都不会让构建报错。

对比度口径：截图取元素区域，**众数色当底色、离底色最远的像素当字芯**，
按 WCAG 算比值，正文级要求 ≥4.5（比 SVG 那套 ≥3.0 严，因为 chip 是正文字号）。
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from collections import Counter
import io
import subprocess
import sys
import tempfile
import threading
import unittest

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from site_build_inputs import copy_build_inputs  # noqa: E402

# 正文字号的门槛（WCAG AA）。SVG 那套用 3.0 是因为图里的标注算"大号图形文字"。
MIN_RATIO = 4.5

# 顶栏 logo 框里「接近白色」的像素占比上限。实测：描边 0.198、实心盘 0.535。
LOGO_MAX_INK = 0.35


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def _luminance(rgb):
    def channel(value):
        v = value / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2])


def contrast(a, b):
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def measured_contrast(page, selector):
    """截取元素区域，众数色=底、离底最远的像素=字芯，返回 (底, 字, 比值)。"""
    box = page.eval_on_selector(selector, "e => e.getBoundingClientRect().toJSON()")
    shot = page.screenshot(clip={"x": box["x"], "y": box["y"],
                                 "width": box["width"], "height": box["height"]})
    pixels = list(Image.open(io.BytesIO(shot)).convert("RGB").get_flattened_data())
    background = Counter(pixels).most_common(1)[0][0]
    glyph = max(pixels, key=lambda c: sum((c[i] - background[i]) ** 2 for i in range(3)))
    return background, glyph, contrast(background, glyph)


def ink_fraction(page, selector, distance=48):
    """元素区域里「与底色不同」的像素占比 —— 分辨「描边图形」与「实心色块」。

    早期版本数的是「接近白色」的像素，前提是顶栏为深色底、标识画白线；
    换纸色顶栏后纸底本身就接近白色，量到 0.69 全是背景。改成先取众数色当
    底色，再数偏离它的像素：描边圈约 0.20，实心盘约 0.53，门槛 0.35 仍居中。
    """
    box = page.eval_on_selector(selector, "e => e.getBoundingClientRect().toJSON()")
    shot = page.screenshot(clip={"x": box["x"], "y": box["y"],
                                 "width": box["width"], "height": box["height"]})
    pixels = list(Image.open(io.BytesIO(shot)).convert("RGB").get_flattened_data())
    background = Counter(pixels).most_common(1)[0][0]
    ink = sum(1 for pixel in pixels
              if sum((pixel[i] - background[i]) ** 2 for i in range(3))
              > distance ** 2)
    return ink / max(1, len(pixels))


class FirstScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix="analog-hero-")
        cls.addClassCleanup(temporary.cleanup)
        work = Path(temporary.name)
        copy_build_inputs(ROOT, work)
        result = subprocess.run([sys.executable, "-X", "utf8", "scripts/build_site.py", "--build"],
                                cwd=work, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=300)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        server = ThreadingHTTPServer(("127.0.0.1", 0),
                                     partial(QuietHandler, directory=str(work / "build")))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        cls.addClassCleanup(lambda: (server.shutdown(), server.server_close(), thread.join(5)))
        cls.base = f"http://127.0.0.1:{server.server_port}/site/"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(channel="chrome")
        cls.addClassCleanup(cls.playwright.stop)
        cls.addClassCleanup(cls.browser.close)

    def homepage(self, scheme="light", width=1280, height=900, reduced_motion="no-preference"):
        context = self.browser.new_context(viewport={"width": width, "height": height},
                                           color_scheme=scheme,
                                           reduced_motion=reduced_motion)
        self.addCleanup(context.close)
        page = context.new_page()
        page.goto(self.base + "index.html", wait_until="load")
        page.wait_for_timeout(700)   # 等字体与渐变铺好
        return page

    # ---------- ① 皮肤真的贴上了 ----------
    def test_hero_skin_is_not_reset_by_a_background_shorthand(self):
        """品牌渐变 + 蓝图点阵必须真的画出来（`background:` 简写会把它重置成 none）。"""
        for scheme in ("light", "dark"):
            with self.subTest(scheme=scheme):
                page = self.homepage(scheme)
                skin = page.evaluate("""() => {
                  const hero = document.querySelector('.learning-hero');
                  const cs = getComputedStyle(hero);
                  const before = getComputedStyle(hero, '::before');
                  return {image: cs.backgroundImage, shadow: cs.boxShadow,
                          isolation: cs.isolation, glow: before.backgroundImage,
                          glowZ: before.zIndex, dots: cs.backgroundSize};
                }""")
                self.assertNotEqual("none", skin["image"],
                                    "hero 的 background-image 被重置了（多半是改回了 background 简写）")
                self.assertIn("radial-gradient", skin["image"], "蓝图点阵丢了")
                self.assertIn("linear-gradient", skin["image"], "品牌渐变丢了")
                self.assertNotEqual("none", skin["shadow"], "hero 的投影丢了")
                self.assertIn("radial-gradient", skin["glow"], "右上角辉光（::before）丢了")
                # 辉光必须压在文字之下，否则会盖住标题
                self.assertEqual("-1", skin["glowZ"], "辉光的 z-index 变了，可能盖住文字")
                self.assertEqual("isolate", skin["isolation"],
                                 "少了 isolation:isolate，z-index:-1 会跑到页面底板后面")

    # ---------- ①-b 底部走线的正弦 ----------
    def test_hero_signal_trace_is_masked_and_only_loops_when_allowed(self):
        """hero 底部那条正弦必须**画得出来**，并且只在无偏好下走线。

        形状画在 `mask-image` 的一张 data-URI SVG 上、颜色画在 `background` 上 ——
        这样它才能跟着主题的品牌色走。两处都会静默翻车：
          * data URI 里少转义一个字符 → mask 解析失败，`mask-image` 变 none，
            整条波形**直接消失**，页面照常构建；
          * 周期与位移量对不上（SVG 的 width ≠ @keyframes 的 translateX）→
            每循环一次波形**跳一下**，一眼就能看出不是连续的。
        所以三样一起钉：mask 命中、动画在跑、周期与位移相等。
        另外 reduce 下动画必须停（本站对「减弱动效」的承诺是「静止但内容完整」，
        波形是装饰，停了不该连带把形状也撤掉）。
        """
        page = self.homepage("light")
        trace = page.evaluate("""() => {
          const after = getComputedStyle(document.querySelector('.learning-hero'), '::after');
          const tile = /width='(\\d+)'/.exec(after.maskImage || after.webkitMaskImage || '');
          const key = [...document.styleSheets].flatMap(s => {
            try { return [...s.cssRules]; } catch { return []; }
          }).filter(r => r.type === CSSRule.KEYFRAMES_RULE && r.name === 'hero-signal');
          const to = key.length ? [...key[0].cssRules].find(r => r.keyText === '100%') : null;
          const shift = to ? /translate3d\\(-?(\\d+)px/.exec(to.style.transform) : null;
          return {mask: after.maskImage || after.webkitMaskImage, size: after.maskSize,
                  anim: after.animationName, tile: tile && tile[1],
                  shift: shift && shift[1],
                  running: document.getAnimations().some(a =>
                    a.animationName === 'hero-signal' && a.playState === 'running')};
        }""")
        self.assertIn("data:image/svg", trace["mask"], "波形的 mask 没了（多半是 data URI 转义坏了）")
        self.assertTrue(trace["tile"], "读不出 mask 图块的周期")
        self.assertEqual(trace["tile"] + "px", trace["shift"] + "px",
                         "走线位移量和图块周期对不上，每循环会跳一下")
        self.assertEqual("hero-signal", trace["anim"])
        self.assertTrue(trace["running"], "无偏好下波形没有在走")

        page = self.homepage("light", reduced_motion="reduce")
        still = page.evaluate("""() => {
          const after = getComputedStyle(document.querySelector('.learning-hero'), '::after');
          return {anim: after.animationName,
                  mask: after.maskImage || after.webkitMaskImage};
        }""")
        self.assertEqual("none", still["anim"], "减弱动效下波形仍在走线")
        self.assertIn("data:image/svg", still["mask"],
                      "减弱动效应该是静止、不是把波形撤掉")

    # ---------- ①-c 首页顶部三段收成一层 ----------
    def test_homepage_top_three_blocks_compose_as_one(self):
        """首页开头必须是「标题 → 副标题 → hero」，前两段不带自己的盒子。

        h1 的通栏下划线、引子 blockquote 的灰底 + 左色条，都是 typography.css
        §5.5 用 `:has(.learning-hero)` 压掉的。这类规则失效是**无声**的：选择器
        写错、或者有人把 §5 的通用规则挪到 §5.5 之后，页面照样构建，只是首屏
        又变回三块各自带底子的东西，hero 被挤到折叠线以下。
        """
        page = self.homepage("light")
        top = page.evaluate("""() => {
          const h1 = document.querySelector('.md-typeset > h1');
          const quote = document.querySelector('.md-typeset > h1 + blockquote');
          const hero = document.querySelector('.learning-hero');
          const q = getComputedStyle(quote);
          // 引子的灰底是 `background: color-mix(… 4%, transparent)` —— 一个背景
          // **颜色**，不是背景图。只看 backgroundImage 会永远读到 none，
          // 于是这条护栏对它其实是瞎的（变异验证 M5 就是这么暴露的）。
          // rgba() 缺第 4 位要按**不透明**算，否则 rgb(…) 这种实心底又漏过去了。
          const chan = q.backgroundColor.match(/[\\d.]+/g) ?? [];
          const alpha = chan.length ? Number(chan[3] ?? 1) : 0;
          return {h1Border: getComputedStyle(h1).borderBottomWidth,
                  quoteBoxed: q.backgroundImage !== 'none' || alpha > 0,
                  quoteBorder: q.borderLeftWidth,
                  heroTop: Math.round(hero.getBoundingClientRect().top),
                  fold: window.innerHeight};
        }""")
        self.assertEqual("0px", top["h1Border"], "首页 h1 又长出通栏下划线了")
        self.assertFalse(top["quoteBoxed"], "首页引子又变回一块灰底")
        self.assertEqual("0px", top["quoteBorder"], "首页引子又长出左色条")
        self.assertLess(top["heroTop"], top["fold"] // 2,
                        f"hero 起点掉到 {top['heroTop']}px，首屏一半被顶部吃掉了")

    # ---------- ② 文字读得出来 ----------
    def test_hero_text_meets_body_contrast_in_both_themes(self):
        """chip 文字与 eyebrow 在明暗两套主题下都必须 ≥4.5。

        暗色主题是重灾区：`--md-primary-fg-color` 在 slate 下**不变**，
        直接拿它当文字色只有 2.56:1。修法是改用随主题变化的
        `--md-typeset-a-color`，再掺正文色兜底。

        chip 的数字**单独量一枚目标**：这个办法取的是「离底色最远的像素」当字芯，
        所以只要同一元素里有较亮的一段，量到的永远是它 —— 给 `<strong>` 掺更多品牌色
        （饱和度高、亮度低）时，数字成了整枚 chip 最读不清的一段，而测试一路绿灯。
        """
        targets = [("chip 文字", ".learning-stats > li"),
                   ("chip 数字", ".learning-stats > li > strong"),
                   ("eyebrow", ".learning-eyebrow")]
        for scheme in ("light", "dark"):
            page = self.homepage(scheme)
            for name, selector in targets:
                with self.subTest(scheme=scheme, target=name):
                    background, glyph, ratio = measured_contrast(page, selector)
                    self.assertGreaterEqual(
                        ratio, MIN_RATIO,
                        f"{scheme} 主题下 {name} 对比度只有 {ratio:.2f}（底={background} 字={glyph}），"
                        f"低于正文级 {MIN_RATIO}")

    # ---------- ③ chip 不掉行、不溢出 ----------
    def test_chips_share_one_row_and_never_overflow(self):
        """桌面宽度下四个 chip 同处一行；手机上换行但不产生横向滚动。

        桌面必须**同一行**是刻意的：Material 的 `[dir=ltr] .md-typeset ul li
        {margin-left:1.25em}` 会给每个 chip 加 17.5px 左外边距，把第四枚挤下去 ——
        选择器写成 `ul.learning-stats:not([hidden])`（特异性 0,3,1）才压得住它。
        """
        for width in (1280, 1024):
            with self.subTest(width=width):
                page = self.homepage(width=width)
                rows = page.evaluate("""() => {
                  const ul = document.querySelector('.learning-stats');
                  const tops = [...ul.children].map(e => Math.round(e.getBoundingClientRect().top));
                  return {rows: new Set(tops).size, count: ul.children.length,
                          marginLeft: getComputedStyle(ul.children[0]).marginLeft,
                          box: +ul.getBoundingClientRect().width.toFixed(1),
                          widths: [...ul.children].map(e => +e.getBoundingClientRect().width.toFixed(1))};
                }""")
                self.assertEqual(4, rows["count"], "规模清单应恰好四项")
                self.assertEqual("0px", rows["marginLeft"],
                                 "chip 被 Material 的 li 左外边距推开了（选择器特异性不够）")
                self.assertEqual(1, rows["rows"],
                                 f"{width}px 下 chip 掉到了多行：容器 {rows['box']}px，"
                                 f"四枚 {rows['widths']}")

        page = self.homepage(width=390)
        overflow = page.evaluate(
            "() => document.documentElement.scrollWidth > window.innerWidth + 1")
        self.assertFalse(overflow, "手机宽度下 chip 撑出了横向滚动")
    def test_learning_depth_steps_form_a_visual_and_conceptual_ladder(self):
        """首页知识阶梯在桌面横排、手机纵排，并保留四层学习语义。"""
        for width, columns in ((1280, 4), (390, 1)):
            with self.subTest(width=width):
                page = self.homepage(width=width)
                snapshot = page.evaluate("""() => {
                  const root = document.querySelector('.learning-depth');
                  const steps = [...root.querySelectorAll('.learning-depth-step')];
                  const cs = getComputedStyle(root);
                  return {
                    count: steps.length,
                    titles: steps.map(e => {
                      // Material 给每个标题塞了 .headerlink（¶）；opacity 隐藏不是
                      // 不可见，textContent/innerText 都读得到。按意图剥掉锚再比，
                      // 不去钉「¶ 长什么样」。
                      const h = e.querySelector('h3');
                      if (!h) return undefined;
                      const clone = h.cloneNode(true);
                      clone.querySelectorAll('.headerlink').forEach(n => n.remove());
                      return clone.textContent.trim();
                    }),
                    columns: cs.gridTemplateColumns.split(' ').filter(Boolean).length,
                    overflow: document.documentElement.scrollWidth > innerWidth + 1,
                    links: root.querySelectorAll('a').length
                  };
                }""")
                self.assertEqual(4, snapshot["count"], "知识阶梯应有四层")
                self.assertEqual(["01 现象", "02 模型", "03 数量级", "04 边界"],
                                 snapshot["titles"])
                self.assertEqual(columns, snapshot["columns"],
                                 f"{width}px 下知识阶梯列数不符合响应式设计")
                self.assertGreaterEqual(snapshot["links"], 4, "每层应有可继续阅读的出口")
                self.assertFalse(snapshot["overflow"], f"{width}px 下知识阶梯产生横向滚动")

    def test_learning_depth_body_text_matches_the_other_cards(self):
        """阶梯正文必须与路线卡/样板课卡同一号排印（字号+行高）。

        四层阶梯是首页卡组家族的一员，正文文字却继承了正文默认字号
        （16px/25.6px），比兄弟卡的 15.2px/27.36px 更大、行距更紧 ——
        同一屏里三种卡片三种排版。样式失效是无声的：改一个选择器就能把阶梯
        排印整块丢掉，构建照常。
        """
        page = self.homepage(width=1280)
        for name, selector in (("阶梯正文", ".learning-depth-step > p:nth-of-type(1)"),
                               ("路线卡正文", ".learning-path > p:nth-of-type(1)"),
                               ("样板课卡正文", ".learning-lesson > p:nth-of-type(2)")):
            with self.subTest(card=name):
                style = page.eval_on_selector(selector, "e => { const c = getComputedStyle(e); return [c.fontSize, c.lineHeight]; }")
                self.assertEqual(["15.2px", "27.36px"], style,
                                 f"{name} 排印与兄弟卡不一致，卡片家族出现了第二套字号")

    def test_learning_depth_step_headings_meet_body_contrast_in_both_themes(self):
        """四层标题在明暗两套主题下都必须 ≥4.5（正文级门槛）。

        四层各配一色（靛/青/琥珀/紫），标题直接吃 `--pc` 当文字色 ——
        这是本站唯一一处「品牌色当标题文字」的用法，明色下琥珀 #b45309
        余量最小（实测 4.77），最经不起渲染器差异（v3.50.1 的 chip 就是
        同一份 CSS 在 CI 的 Linux 渲染器上掉到 3.98）。
        """
        for scheme in ("light", "dark"):
            page = self.homepage(scheme=scheme)
            for index in (1, 2, 3, 4):
                with self.subTest(scheme=scheme, step=index):
                    selector = f".learning-depth > .learning-depth-step:nth-child({index}) > h3"
                    page.eval_on_selector(selector, "e => e.scrollIntoView({block:'center'})")
                    background, glyph, ratio = measured_contrast(page, selector)
                    self.assertGreaterEqual(
                        ratio, MIN_RATIO,
                        f"{scheme} 主题第 {index} 层标题对比度只有 {ratio:.2f}"
                        f"（底={background} 字={glyph}），低于正文级 {MIN_RATIO}")


    # ---------- ④ 顶栏品牌（每页都有，属于首屏的一部分） ----------
    def test_header_logo_is_an_outline_not_a_filled_disc(self):
        """顶栏标识必须是「圈 + 正弦」的**描边**，不能糊成一个实心圆盘。

        为什么专门钉这个：Material 有
        `.md-header__button.md-logo :is(img,svg){fill:currentcolor}` —— CSS 声明
        压得过根 <svg> 上的 `fill="none"`（呈现属性优先级最低）。所以只要有人把
        `fill="none"` 从**子元素**挪到根元素上（看起来更「整洁」），圆就变成实心盘。
        构建不报错、静态检查也看不出来，只有人眼发现「logo 变成一个白点」。

        实测 24×24 的 logo 框：描边时白像素占比 0.198，实心盘 0.535 ——
        门槛取 0.35，两边都留足余量。
        """
        for scheme in ("light", "dark"):
            with self.subTest(scheme=scheme):
                page = self.homepage(scheme)
                size = page.eval_on_selector(
                    ".md-header__button.md-logo svg",
                    "e => { const r = e.getBoundingClientRect();"
                    "       return {w: r.width, h: r.height}; }")
                self.assertGreater(size["w"], 8, "顶栏标识没渲染出来")
                ink = ink_fraction(page, ".md-header__button.md-logo svg")
                self.assertLess(
                    ink, LOGO_MAX_INK,
                    f"{scheme} 主题下顶栏标识有 {ink:.3f} 的像素偏离底色（上限 {LOGO_MAX_INK}）——"
                    "多半是 fill=\"none\" 被挪到根 <svg> 上、又被 Material 的 "
                    "fill:currentcolor 覆盖了，圈糊成了实心盘")

    def test_header_repo_link_is_not_truncated(self):
        """顶栏右上角的仓库链接不能被截断。

        Material 给 `.md-header__source` 的宽度在桌面上是**写死的 11.5rem**，
        跟视口宽度无关 —— 所以写全路径 `zhuguang-ZFG/analog-circuit-roadmap`
        会被 CSS 截成 `zhuguang-ZFG/analog-ci…`：每页顶栏都挂着一个省略号。
        这里直接比 scrollWidth 与 clientWidth（截断时前者更大）。
        """
        for width in (1440, 1280, 1024):
            with self.subTest(width=width):
                page = self.homepage(width=width)
                box = page.evaluate("""() => {
                  const e = document.querySelector('.md-source__repository');
                  return {scroll: e.scrollWidth, client: e.clientWidth,
                          text: e.textContent.trim()};
                }""")
                self.assertTrue(box["text"], "顶栏仓库链接是空的")
                self.assertLessEqual(
                    box["scroll"], box["client"] + 1,
                    f"{width}px 下仓库链接「{box['text']}」被截断了"
                    f"（内容 {box['scroll']}px > 容器 {box['client']}px）")

    def test_header_title_actually_paints_glyphs(self):
        """顶栏站点标题必须真的画出来，而不只是「算出来的颜色合规」。

        CI（Ubuntu，无 KaiTi）实测过一整块纯底色：`--hand-font` 整栈都是中文
        桌面字体，掉到通用 serif 后 CJK 字形一个都没画，几何框仍在、对比度脚本
        量到的「字」等于底色（1.00:1）。这里按像素占比钉住「有字」：
        实测手写体约 4.6%，低于 0.5% 说明没画，高于 60% 说明糊成了色块。
        """
        for scheme in ("light", "dark"):
            with self.subTest(scheme=scheme):
                page = self.homepage(scheme)
                ink = ink_fraction(page, ".md-header__title")
                self.assertGreater(
                    ink, 0.005,
                    f"{scheme} 主题下顶栏标题只有 {ink:.4f} 的像素偏离底色——"
                    "文字没画出来（多半是字体栈里没有可用的中文字体）")
                self.assertLess(
                    ink, 0.6,
                    f"{scheme} 主题下顶栏标题有 {ink:.3f} 的像素偏离底色——像是糊成了色块")

    def test_header_text_meets_body_contrast_in_both_themes(self):
        """顶栏的站点标题与仓库链接在明暗两套主题下都要 ≥4.5。

        顶栏底色是固定的品牌色（`--md-primary-fg-color` 在 slate 下也不变），
        文字是白色 —— 理论上够用，但这条线此前**没有任何测试覆盖**
        （SVG 那套管的是图里的文字，hero 那套管的是首页正文）。
        """
        targets = [("站点标题", ".md-header__title"),
                   ("仓库链接", ".md-source__repository")]
        for scheme in ("light", "dark"):
            page = self.homepage(scheme)
            for name, selector in targets:
                with self.subTest(scheme=scheme, target=name):
                    background, glyph, ratio = measured_contrast(page, selector)
                    self.assertGreaterEqual(
                        ratio, MIN_RATIO,
                        f"{scheme} 主题下顶栏{name}对比度只有 {ratio:.2f}"
                        f"（底={background} 字={glyph}），低于正文级 {MIN_RATIO}")


if __name__ == "__main__":
    unittest.main()
