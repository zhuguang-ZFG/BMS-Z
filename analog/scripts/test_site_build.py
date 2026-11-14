"""在临时目录里跑一遍 build_site.py，检查生成的站点源是否自洽。

Run: python -B -m unittest discover -s scripts -p test_site_build.py -v

为什么要这组测试：`build_site.py` 里有一批"静默失效"的正则（DEMO_LINK、DEMO_IMG、
CHAPTER_ROW）。docs/ 迁移成多页后，`DEMO_LINK` 只认 `](#demoN)`、认不出
`(p5-00-part5.md#demoN)`，结果画廊的章节筛选 chips 全部消失——页面照样生成、
构建照样成功，只有人肉点开才发现。这里把这类漂移变成红灯。

只用标准库；mkdocs.yml 的重复键检查需要 PyYAML（随 mkdocs-material 一起装）。
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_build_inputs import copy_build_inputs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PART5 = "p5-00-part5.md"

# 侧栏「节首页补丁」的单元测试要读已安装的 Material 模板，所以直接 import
# build_site（本文件所在的 site-build 作业本来就装了 mkdocs-material）。
sys.path.insert(0, str(ROOT / "scripts"))
from build_site import (CALLOUT_KINDS, NAV_ITEM_ANCHOR,  # noqa: E402
                        NAV_ITEM_PATCHED, nav_item_override)

DEMO_HEAD = re.compile(r'^## (5\.\d+)\s+(.+?)\s*<a id="(demo\d+)"')
ANCHOR = re.compile(r'<a\s+id="(demo\d+)"')
CHAPTER_ROW = re.compile(r"^\|\s*§(\d+)\s+(第\s*\d+\s*章[^|]*?)\s*\|")
DEMO_LINK = re.compile(r"\[(5\.\d+)\]\((?:[\w\-]+\.md)?#(demo\d+)\)")

CARD = re.compile(
    r'<div class="gal-card" data-ch="([^"]*)" data-title="([^"]*)" data-file="([^"]*)">\s*'
    r'<a href="([^"]+)"[^>]*>\s*'
    # 动画 <img> 现在包在 <picture> 里（<source media> 负责挑「减弱动效」的静止版）；
    # 用非捕获组，保持下面的分组下标不变。
    r'(?:<picture><source srcset="[^"]+"\s+media="[^"]*">)?'
    r'<img src="([^"]+)"[^>]*>\s*'
    r'(?:</picture>\s*)?'
    r'<div class="gal-meta">\s*<div class="gal-title">([^<]*)</div>\s*'
    r'<div class="gal-tag">([^<]*)</div>\s*</div>\s*</a>\s*'
    r'<div class="gal-actions">\s*<button class="gal-play"[^>]*data-svg="([^"]+)"\s*'
    r'data-title="([^"]*)" data-href="([^"]*)"[^>]*>')
CHIP = re.compile(r'<button class="gal-chip" data-ch="([^"]*)" aria-pressed="[^"]*">([^<]*)</button>')

# 篇级落地页 → 子页文件名前缀：落地页必须把本篇每个子页都链接一遍
PART_LANDING_PREFIX = {
    "p1-00-part1.md": "p1-", "p2-00-part2.md": "p2-", "p3-00-part3.md": "p3-",
    "p4-00-part4.md": "p4-", "p6-00-part6.md": "p6-", "p7-00-part7.md": "p7-",
    "p8-00-part8.md": "p8-",
}


class SiteBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix="analog-site-parity-")
        cls.addClassCleanup(temporary.cleanup)
        work = Path(temporary.name)
        cls.work = work
        # 输入清单集中在 site_build_inputs（章徽、标题 webfont 都在里面）：
        # 这里再抄一份的话，构建读新路径时这个用例会以 FileNotFoundError 红灯。
        copy_build_inputs(ROOT, work)

        result = subprocess.run(
            [sys.executable, "-B", str(work / "scripts" / "build_site.py"), "--build"],
            cwd=str(work), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=600,
        )
        if result.returncode:
            raise RuntimeError("build_site.py failed:\n" + result.stdout + result.stderr)
        cls.stdout = result.stdout
        cls.stderr = result.stderr
        cls.out = work / "build" / "docs"
        cls.build = work / "build"
        cls.site = work / "build" / "site"
        if not cls.out.is_dir():
            raise AssertionError("build_site.py 没有产出 build/docs")
        if not cls.site.is_dir():
            raise AssertionError("build_site.py --build 没有产出 build/site")

        cls.gallery = (cls.out / "gallery.md").read_text(encoding="utf-8")
        cls.part5 = (work / "docs" / PART5).read_text(encoding="utf-8")
        cls._part5_built = (cls.out / PART5).read_text(encoding="utf-8")
        cls.cards = CARD.findall(cls.gallery)
        cls.chips = CHIP.findall(cls.gallery)
        cls._rendered = {}

    def rendered(self, name):
        """按需读取渲染后的 HTML（62 页全读一遍也就几 MB，读一次就缓存）。"""
        if name not in self._rendered:
            self._rendered[name] = (self.site / name).read_text(encoding="utf-8")
        return self._rendered[name]

    def body_html(self, name):
        """只取 <article class="md-content__inner"> 里的正文，避开导航/目录里的同名文字。"""
        text = self.rendered(name)
        i = text.find('<article class="md-content__inner')
        j = text.find("</article>", i)
        return text[i:j] if i >= 0 and j > i else text

    # ---------- Markdown 泄漏护栏 ----------
    def test_built_pages_carry_no_unrendered_markdown(self):
        """v3.83–v3.85 潜伏回归：公式里的 $X<Y$ 让 Python-Markdown 的 HTML stash
        把 `<V` 当成未闭合标签起点，与后一个 HTML 块（figure）组合后解析器永久
        落入 raw 态——ch4 从 §4.3 起整页裸 markdown 被三个版本带病发出。逐页断言
        正文不再出现行首裸标题、成对 ** 标记、裸表格行与未渲染的 `.md` 链接
        （后两类都是 HTML 块内写 markdown 的同一症状）。"""
        strip = re.compile(r"<(pre|code|script|style|svg)\b.*?</\1>", re.S)
        heading = re.compile(r"^#{1,6}\s\S", re.M)
        bold = re.compile(r"\*\*[^*\n]{2,80}\*\*")
        pipe_row = re.compile(r"^\|[^\n]+\|\s*$", re.M)
        # ch17 的图注踩过同一坑：markdown 链接写在原生 HTML 块里，Python-Markdown
        # 整段 stash，`[12.1](p2-02-ch12.md#ch12)` 原样出现在成品页上。
        md_link = re.compile(r"\[[^\]\n]{1,40}\]\([^)\s]*\.md(?:#[\w\-]+)?\)")
        offenders = []
        for page in sorted(self.site.glob("*.html")):
            text = strip.sub("", page.read_text(encoding="utf-8"))
            hits = (heading.findall(text) + bold.findall(text)
                    + pipe_row.findall(text) + md_link.findall(text))
            if hits:
                offenders.append("%s: %r" % (page.name, hits[:3]))
        self.assertEqual([], offenders)

    # ---------- 画廊卡片 ----------
    def test_card_inventory_matches_animation_headings(self):
        """卡片数必须等于第 5 篇里带 demo 锚点的动画条目数。"""
        expected = [m.group(3) for m in map(DEMO_HEAD.match, self.part5.split("\n")) if m]
        self.assertEqual(len(expected), len(self.cards),
                         "画廊卡片数与 p5-00-part5.md 的动画条目数不一致")
        got = [c[3].rsplit("#", 1)[-1] for c in self.cards]
        self.assertEqual(sorted(expected, key=self._n), sorted(got, key=self._n),
                         "卡片锚点集合与动画条目锚点集合不一致")

    def test_every_card_has_a_chapter(self):
        """每张卡片都要能归到某一章——这条专门守住 DEMO_LINK 正则漂移。"""
        blank = [c[1] for c in self.cards if not c[0].strip()]
        self.assertEqual([], blank, "有卡片没有 data-ch（章节筛选会漏掉它们）")
        bad = [c[0] for c in self.cards if not c[0].isdigit()]
        self.assertEqual([], bad, "data-ch 必须是章号")

    def test_card_chapters_match_the_index_table(self):
        """卡片归属的章集合 == 第 5 篇速查索引表里列出的章集合。"""
        indexed = set()
        for ln in self.part5.split("\n"):
            m = CHAPTER_ROW.match(ln)
            if m and DEMO_LINK.search(ln):
                indexed.add(m.group(1))
        got = {c[0] for c in self.cards}
        self.assertEqual(indexed, got,
                         "索引表章集合 %s != 卡片章集合 %s" % (sorted(indexed), sorted(got)))

    def test_every_card_svg_exists(self):
        for ch, _t, f, _h, img, *_ in self.cards:
            with self.subTest(card=f):
                self.assertTrue(f, "data-file 为空")
                self.assertEqual("assets/%s" % f, img, "data-file 与 img src 不一致")
                self.assertTrue((self.out / "assets" / f).is_file(),
                                "卡片引用的 SVG 不存在：%s" % f)

    def test_every_card_anchor_exists(self):
        anchors = set(ANCHOR.findall(self.part5))
        for ch, _t, f, href, *_ in self.cards:
            with self.subTest(card=f):
                self.assertTrue(href.startswith("p5-00-part5.html#"),
                                "卡片链接必须指向第 5 篇的锚点：%s" % href)
                self.assertIn(href.rsplit("#", 1)[-1], anchors,
                              "卡片锚点不存在：%s" % href)

    def test_every_card_has_a_play_button(self):
        """卡片数 == 放大播放按钮数（lightbox 与卡片一一对应）。"""
        plays = re.findall(r'<button class="gal-play"[^>]*data-svg="([^"]+)"', self.gallery)
        self.assertEqual(len(self.cards), len(plays))
        for ch, _t, f, href, _img, *_rest in self.cards:
            with self.subTest(card=f):
                self.assertEqual("assets/%s" % f, plays[[c[2] for c in self.cards].index(f)])

    def test_lightbox_is_wired(self):
        for needle in ('id="gal-modal"', 'id="gal-modal-img"', 'id="gal-modal-title"',
                       'id="gal-modal-link"', 'id="gal-modal-close"'):
            self.assertIn(needle, self.gallery, "画廊缺少 lightbox 结构：%s" % needle)
        js = (self.out / "javascripts" / "gallery.js").read_text(encoding="utf-8")
        for needle in ("gal-play", "gal-modal", "Escape"):
            self.assertIn(needle, js, "gallery.js 缺少 lightbox 逻辑：%s" % needle)

    def test_lightbox_prev_next_and_keyboard(self):
        for needle in ('id="gal-modal-prev"', 'id="gal-modal-next"', 'id="gal-modal-pos"'):
            self.assertIn(needle, self.gallery, "lightbox 缺少翻页结构：%s" % needle)
        js = (self.out / "javascripts" / "gallery.js").read_text(encoding="utf-8")
        for needle in ("ArrowLeft", "ArrowRight", "gal-modal-prev", "gal-modal-next"):
            self.assertIn(needle, js, "gallery.js 缺少翻页/键盘逻辑：%s" % needle)

    def test_filter_state_is_shareable(self):
        """筛选状态要能写进地址栏（?ch=&q=），否则分享出去的链接会丢掉筛选。"""
        js = (self.out / "javascripts" / "gallery.js").read_text(encoding="utf-8")
        self.assertIn("URLSearchParams", js)
        self.assertIn("replaceState", js)
        self.assertIn("?ch=", self.gallery)
        for needle in ('id="gal-random"', "gal-random"):
            self.assertIn(needle, self.gallery if needle.startswith("id=") else js)

    def test_card_images_reserve_space(self):
        """<img> 必须带真实 width/height（否则 102 张图会让画廊疯狂抖动）。"""
        pat = re.compile(r'<img src="(assets/svg(?:-v2)?/[\w\-]+\.svg)"[^>]*?width="(\d+)" height="(\d+)"')
        found = pat.findall(self.gallery)
        self.assertEqual(len(self.cards), len(found),
                         "有卡片图片没写 width/height")
        for src, w, h in found:
            with self.subTest(svg=src):
                head = (self.out / src).read_text(encoding="utf-8", errors="replace")[:600]
                m = re.search(r'<svg[^>]*\bwidth="(\d+)"\s+height="(\d+)"', head)
                if m:
                    fw, fh = m.group(1), m.group(2)
                else:
                    # V2 SVG 只有 viewBox（与 build_site.svg_size 的回退口径一致）。
                    vb = re.search(
                        r'viewBox="[\d.\-]+\s+[\d.\-]+\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)"', head)
                    if vb is None:
                        self.fail("SVG 里读不到画布尺寸")
                    fw = str(int(float(vb.group(1))))
                    fh = str(int(float(vb.group(2))))
                self.assertEqual((w, h), (fw, fh),
                                 "卡片上的 width/height 与 SVG 画布不一致")

    def test_animation_images_are_lazy_and_reserve_space(self):
        """第五篇一页嵌 102 张 SVG（约 1.9MB）：必须懒加载，且按画布比例写 height 防抖动。"""
        pat = re.compile(r'<img src="assets/svg/([\w\-]+\.svg)"[^>]*?>')
        tags = pat.findall(self._part5_built)
        self.assertGreaterEqual(len(tags), 100, "第五篇的动画 <img> 数量异常")
        for m in pat.finditer(self._part5_built):
            tag, name = m.group(0), m.group(1)
            with self.subTest(svg=name):
                self.assertIn('loading="lazy"', tag, "动画图片缺 loading=lazy")
                self.assertIn('decoding="async"', tag, "动画图片缺 decoding=async")
                hm = re.search(r'\bheight="(\d+)"', tag)
                wm = re.search(r'\bwidth="(\d+)"', tag)
                if hm is None or wm is None:
                    self.fail("动画图片缺 width/height（会整页抖动）")
                head = (self.out / "assets" / "svg" / name).read_text(encoding="utf-8",
                                                                     errors="replace")[:600]
                sm = re.search(r'<svg[^>]*\bwidth="(\d+)"\s+height="(\d+)"', head)
                if sm is None:
                    self.fail("SVG 里读不到画布尺寸")
                ratio = int(sm.group(2)) / int(sm.group(1))
                expect = round(int(wm.group(1)) * ratio)
                self.assertLessEqual(abs(int(hm.group(1)) - expect), 1,
                                     f"height 与画布比例不符（{hm.group(1)} vs {expect}）")

    # ---------- 减弱动效（<picture> 选源） ----------
    def test_every_animation_image_is_wrapped_in_a_reduce_picture(self):
        """每个动画 <img> 都要包进 <picture>，且 <source> 指向静止版。

        为什么必须由页面选源：SVG 作为 `<img>` 载入时 Chrome 把
        `prefers-reduced-motion` **恒判为 reduce**，所以 SVG 内部的 media query
        是恒真/恒假的（v3.45 因此把全站动画冻住过）。`<source media>` 在页面
        上下文里求值，才是准的。漏包一个，那张图在「减弱动效」下就照常乱飞。
        """
        for page in (PART5, "gallery.md"):
            text = (self.out / page).read_text(encoding="utf-8")
            imgs = re.findall(r'<img src="assets/svg/[\w\-]+\.svg"[^>]*>', text)
            wrapped = re.findall(
                r'<picture><source srcset="assets/svg/[\w\-]+\.reduce\.svg" '
                r'media="\(prefers-reduced-motion: reduce\)">'
                r'<img src="assets/svg/[\w\-]+\.svg"[^>]*></picture>', text)
            with self.subTest(page=page):
                self.assertGreaterEqual(len(imgs), 100, f"{page} 的动画图太少，覆盖面不对")
                self.assertEqual(len(imgs), len(wrapped),
                                 f"{page} 有 {len(imgs) - len(wrapped)} 张动画图没包 <picture>")

    def test_reduce_variants_exist_and_actually_freeze_the_particles(self):
        """每个静止版都要真的存在，且带上无条件生效的三条运动选择器。

        静止版由 build_site.py 从动画版追加 REDUCE_CSS 生成；这里同时守住
        「文件确实生成了」和「规则确实是那三条」——少了任何一条，
        对应类别的粒子（animateMotion / animateTransform / 非透明度 animate）就漏网。
        """
        svg_dir = self.out / "assets" / "svg"
        animated = sorted(p for p in svg_dir.glob("*.svg")
                          if not p.name.endswith(".reduce.svg"))
        self.assertGreaterEqual(len(animated), 108, "动画 SVG 数量不对")
        for svg in animated:
            variant = svg_dir / (svg.stem + ".reduce.svg")
            with self.subTest(svg=svg.name):
                self.assertTrue(variant.exists(), f"{svg.name} 没有对应的静止版")
                text = variant.read_text(encoding="utf-8")
                for sel in (":has(> animateMotion):not(:has(text))",
                            ":has(> animateTransform):not(:has(text))",
                            ':has(> animate:not([attributeName="opacity"])):not(:has(text))'):
                    self.assertIn(sel, text, f"{variant.name} 缺选择器 {sel}")
                # 静止版里不能再出现 media query——那正是 v3.45 的坑
                self.assertNotIn("prefers-reduced-motion", text,
                                 f"{variant.name} 的规则被包进了 media query")

    def test_every_page_has_a_unique_description(self):
        """59 个页面原先共用同一句 site_description：每页必须有自己的、干净的摘要。

        摘要由正文自动摘取，很容易静默劣化——曾把 `p1-04-ch3.md` 里 ASCII 画的 BJT
        结构图（`│ N ├───┬───┤ N+ │`）和 `\\dfrac{R_0}{V_{DD}-V_{IN}-V_{TH}}` 这类
        压不成文字的公式当成摘要。这里把「每页有、各不相同、无 Markdown/公式残渣」
        钉成红灯。
        """
        pat = re.compile(r'^---\ndescription: ([^\n]*)\ntitle: ([^\n]*)\n---\n')
        descs = {}
        for page in sorted(self.out.glob("*.md")):
            with self.subTest(page=page.name):
                m = pat.match(page.read_text(encoding="utf-8"))
                if m is None:
                    self.fail(f"{page.name} 没有 description（会退回全站同一句）")
                descs[page.name] = json.loads(m.group(1))
                title = json.loads(m.group(2))
                self.assertTrue(title)
                self.assertNotEqual(page.stem, title)

        values = list(descs.values())
        dup = {v: [k for k, x in descs.items() if x == v] for v in values if values.count(v) > 1}
        self.assertEqual({}, dup, "有页面共用同一句 description：%s" % dup)

        for name, desc in descs.items():
            with self.subTest(page=name):
                self.assertGreaterEqual(len(desc), 8, "摘要太短：%r" % desc)
                self.assertLessEqual(len(desc), 150, "摘要超长：%r" % desc)
                # `"` 会把 <meta content="..."> 属性截断（p1-05-ch4 就因此整条 meta 消失），
                # 所以摘要里必须已经换成中文弯引号
                for bad in ("`", "*", "$", "\\", "|", "│", "├", "&lt;", "frac", "quad", '"'):
                    self.assertNotIn(bad, desc, "摘要里混进了 Markdown/公式/ASCII 图残渣：%r" % desc)

    # ---------- 筛选 chips ----------
    def test_chips_cover_all_and_every_chapter(self):
        self.assertEqual("all", self.chips[0][0], "第一个 chip 必须是「全部」")
        self.assertEqual(1, len([c for c in self.chips if c[0] == "all"]))
        chip_ch = [c[0] for c in self.chips[1:]]
        self.assertEqual(sorted(chip_ch, key=int), sorted({c[0] for c in self.cards}, key=int),
                         "每个出现过的章都要有一个 chip")
        self.assertEqual(len(chip_ch), len(set(chip_ch)), "chip 重复")

    def test_chip_counts_sum_to_card_total(self):
        def count(label):
            match = re.search(r"(\d+)\s*$", label)
            if match is None:
                self.fail(f"chip 缺数量: {label}")
            return int(match.group(1))
        total = sum(count(label) for ch, label in self.chips if ch != "all")
        self.assertEqual(len(self.cards), total, "各章 chip 上的数字之和 != 卡片总数")
        all_label = [label for chip, label in self.chips if chip == "all"][0]
        self.assertEqual(len(self.cards), count(all_label))

    # ---------- 导航与配置 ----------
    def test_nav_covers_every_content_page(self):
        nav = (self.build / "mkdocs.yml").read_text(encoding="utf-8")
        pages = [p.name for p in sorted(self.out.glob("*.md"))
                 if p.name not in {"gallery.md", "CONTRIBUTING.md", "CONTRIBUTORS.md"}]
        missing = [p for p in pages if p not in nav]
        self.assertEqual([], missing, "这些页面没进侧栏导航：%s" % missing)
        for extra in ("gallery.md", "CONTRIBUTING.md", "CONTRIBUTORS.md"):
            self.assertIn(extra, nav, "%s 没进导航" % extra)

    def test_sidebar_part_titles_are_links_not_duplicated_rows(self):
        """侧栏里每个篇标题只占一行，而且它本身就是进入篇首页的链接。

        背景：Material 的 `navigation.indexes` 只认 MkDocs 的 `Page.is_index`，
        而那个属性的定义就是 `self.file.name == 'index'`。本站的篇首页叫
        `p1-00-part1.md` —— 命不中，于是节标题退化成纯折叠标签（点它只能展开），
        篇首页又以普通子项出现在列表首位，两处标题**一字不差**，于是每个篇标题
        在侧栏里重复两行（实测 9 处）。`build_site.nav_item_override()` 给上游
        模板打了补丁，这里锁住渲染结果：补丁一旦失效就会退回重复。
        """
        html = self.rendered("index.html")
        heads = sorted(p.stem for p in (self.work / "docs").glob("p?-00-*.md"))
        self.assertGreaterEqual(len(heads), 8, "篇首页数量异常，测试前提不成立")

        # 补丁生效时，节标题被包进 md-nav__container（指向篇首页的 <a> + 展开箭头）；
        # 未生效时它是裸 <label>，容器一个都不会出现。
        self.assertEqual(len(heads), html.count("md-nav__container"),
                         "侧栏篇标题没有变成指向篇首页的链接（navigation.indexes 未生效）")

        nav = html[html.index("md-nav--primary"):html.index("md-sidebar--secondary")]
        for stem in heads:
            self.assertEqual(1, len(re.findall(r'href="%s\.html"' % stem, nav)),
                             "%s 在侧栏里出现了多次（篇标题与篇首页链接重复）" % stem)

    # ---------- 品牌标识（顶栏 logo / favicon / 仓库链接文案） ----------
    def test_header_logo_is_ours_not_the_theme_default(self):
        """顶栏标识必须是我们自己的「节点圈 + 正弦」，不能退回 Material 默认的书本图标。

        为什么值得钉：Material 默认那个 `material/library` 图标跟模拟电路毫无关系，
        而它「静默生效」—— `theme.icon.logo` 一旦丢了或名字写错，主题会**悄悄**
        回退到默认图标，构建照样成功、其他测试照样绿。

        `fill="none"` 那一条是硬性的：Material 有
        `.md-header__button.md-logo :is(img,svg){fill:currentcolor}`，CSS 声明压得过
        根 <svg> 上的同名呈现属性。写在根上 = 圈变成实心盘（渲染结果由
        test_first_screen.py 按像素占比验）。
        """
        nav = (self.build / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn("logo: analog-circuit", nav, "主题配置里没有指向自绘标识")

        icon = self.build / "overrides" / ".icons" / "analog-circuit.svg"
        self.assertTrue(icon.is_file(), "品牌标识没有被写进 custom_dir 的 .icons/")
        mark = icon.read_text(encoding="utf-8")
        self.assertEqual(2, mark.count('fill="none"'),
                         'fill="none" 必须分别写在 circle 与 path 两个子元素上')
        self.assertNotIn("<!--", mark,
                         "生成的主题图标里还留着注释（设计说明会被内联进 61 页 HTML）")

        html = self.rendered("index.html")
        start = html.index("md-header__button md-logo")
        header_logo = html[start:html.index("</a>", start)]
        self.assertIn("M6.3 12c1.5-3.5", header_logo, "顶栏没有内联我们的标识")
        self.assertNotIn("M12 8a3 3 0 0 0 3-3", header_logo,
                         "顶栏退回 Material 默认的书本图标了")
        self.assertNotIn("品牌标识", header_logo, "logo.svg 的设计说明被内联进页面了")

    def test_favicon_is_ours_not_the_theme_default(self):
        """favicon 必须是自绘的那张（品牌渐变 + 标识），不能是 Material 默认的深色书本。

        Material 自带 `assets/images/favicon.png`，而 MkDocs 收集静态文件时是
        「docs_dir 先、主题目录后」，同名文件里 docs_dir 赢。所以只要仓库里的
        `assets/images/favicon.png` 还在、`assets/` 还被整棵拷进站点源，产物就
        应当与它**逐字节相同**；哪天有人挪了路径或改了名字，产物会静默换回
        主题默认图 —— 同样不影响构建、不影响其他测试。
        """
        ours = (ROOT / "assets" / "images" / "favicon.png").read_bytes()
        built = (self.site / "assets" / "images" / "favicon.png").read_bytes()
        self.assertEqual(ours, built, "产物里的 favicon 不是仓库里那份（被主题默认图盖掉了）")

        nav = (self.build / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn("favicon: assets/images/favicon.png", nav)
        self.assertIn('rel="icon" href="assets/images/favicon.png"',
                      self.rendered("index.html"))

    def test_header_repo_name_has_no_path(self):
        """顶栏仓库链接的文案里不能带 `/`。

        Material 给 `.md-header__source` 的宽度在桌面上写死 11.5rem（跟视口无关），
        所以 `zhuguang-ZFG/analog-circuit-roadmap` 会被 CSS 截成
        `zhuguang-ZFG/analog-ci…` —— 每页顶栏都挂一个省略号。
        （真实渲染由 test_first_screen.py 比 scrollWidth/clientWidth 验。）
        """
        nav = (self.build / "mkdocs.yml").read_text(encoding="utf-8")
        line = next(ln for ln in nav.splitlines() if ln.startswith("repo_name:"))
        self.assertNotIn("/", line, f"仓库链接文案带了路径，会被顶栏截断：{line!r}")

    def test_no_placeholders_left(self):
        nav = (self.build / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertNotIn("__NAV__", nav)
        main = (self.build / "overrides" / "main.html").read_text(encoding="utf-8")
        self.assertNotIn("__OG_IMAGE__", main)
        self.assertIn("og:image", main)

    def test_mkdocs_yml_has_no_duplicate_keys(self):
        """重复键（例如被复制粘贴两遍的 use_directory_urls）必须报错，而不是静默取最后一个。"""
        try:
            import yaml
        except ImportError:  # pragma: no cover - 站点构建 job 会装 PyYAML
            self.skipTest("PyYAML 未安装")

        class DupCheck(yaml.SafeLoader):
            pass

        def construct_mapping(loader, node, deep=False):
            mapping = {}
            for key_node, value_node in node.value:
                key = loader.construct_object(key_node, deep=deep)
                if key in mapping:
                    raise AssertionError("mkdocs.yml 第 %d 行有重复键：%r"
                                         % (key_node.start_mark.line + 1, key))
                mapping[key] = loader.construct_object(value_node, deep=deep)
            return mapping

        DupCheck.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
        DupCheck.add_multi_constructor("tag:yaml.org,2002:python/name:", lambda loader, suffix, node: None)
        text = (self.build / "mkdocs.yml").read_text(encoding="utf-8")
        cfg = yaml.load(text, Loader=DupCheck)
        self.assertEqual("https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/", cfg["site_url"])
        self.assertIn("edit_uri", cfg)
        self.assertEqual("overrides", cfg["theme"]["custom_dir"])
        self.assertIn("content.action.edit", cfg["theme"]["features"])

    def test_seo_files(self):
        robots = (self.out / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Sitemap: https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/sitemap.xml",
                      robots)

    def test_lesson_assets_and_three_entry_points_are_published(self):
        config = (self.build / "mkdocs.yml").read_text(encoding="utf-8")
        for kind, name in (("stylesheets", "learning.css"), ("javascripts", "learning.js")):
            self.assertIn(f"{kind}/{name}", config)
            self.assertEqual((self.work / "scripts/site_media" / name).read_bytes(),
                             (self.out / kind / name).read_bytes())
        for page, lesson, photo in (("p1-02-ch1.md", "rc", "capacitors.jpg"),
                                    ("p1-05-ch4.md", "mosfet", "mosfets.jpg"),
                                    ("p1-07-ch6.md", "lm358", "lm358n.jpg")):
            text = (self.out / page).read_text(encoding="utf-8")
            self.assertIn(f'data-study="{lesson}"', text)
            self.assertIn("data-study-video", text)
            self.assertNotIn("<iframe", text)
            self.assertIn(f"assets/photos/{photo}", text)
            self.assertTrue((self.out / "assets/photos" / photo).is_file())

    def test_reading_navigation_connects_all_chapters_to_their_quizzes(self):
        quiz = (self.out / 'p9-00-quiz.md').read_text(encoding='utf-8')
        chapters = []
        for path in self.out.glob('*-ch[0-9]*.md'):
            match = re.search(r'-ch(\d+)\.md$', path.name)
            if match is None:
                self.fail(f'章节文件名不合法: {path.name}')
            chapters.append((int(match.group(1)), path))
        chapters.sort()
        self.assertEqual(list(range(19)), [n for n, _ in chapters])
        for position, (number, page) in enumerate(chapters):
            content = page.read_text(encoding='utf-8')
            self.assertIn(f'href="p9-00-quiz.html#quiz-ch{number}"', content)
            self.assertIn(f'<a id="quiz-ch{number}"></a>', quiz)
            if position + 1 < len(chapters):
                next_number, next_page = chapters[position + 1]
                self.assertIn(f'href="{next_page.stem}.html#ch{next_number}"', content)
            if position:
                previous_number, previous_page = chapters[position - 1]
                self.assertIn(f'href="{previous_page.stem}.html#ch{previous_number}"', content)
        self.assertIn('href="index.html"', chapters[0][1].read_text(encoding='utf-8'))
        self.assertIn('href="p8-03-s8-3.html"', chapters[-1][1].read_text(encoding='utf-8'))

    def test_legacy_links_resolve_to_canonical_source_anchors(self):
        redirects = json.loads((self.work / 'scripts/site_media/legacy-anchors.json').read_text(encoding='utf-8'))
        self.assertEqual(35, len(redirects))
        for source, target in redirects.items():
            old_page, old_anchor = source.split('#')
            new_page, new_anchor = target.split('#')
            old = (self.out / old_page.replace('.html', '.md')).read_text(encoding='utf-8')
            canonical = (self.work / 'docs' / new_page.replace('.html', '.md')).read_text(encoding='utf-8')
            self.assertIn(f'class="legacy-anchor" id="{old_anchor}"', old)
            self.assertIn(f'href="{target}"', old)
            self.assertIn(f'<a id="{new_anchor}"></a>', canonical)
            self.assertNotIn(target, redirects, 'Redirect chains must not be introduced')

    def test_homepage_local_html_links_and_reading_assets_are_published(self):
        home = (self.out / 'index.md').read_text(encoding='utf-8')
        self.assertNotRegex(home, r'href="[^"]*\.md(?:#|\")')
        for filename in re.findall(r'href="([\w-]+)\.html', home):
            self.assertTrue((self.out / f'{filename}.md').exists())
        self.assertTrue((self.out / 'LICENSE').is_file())
        for directory, filename in (('stylesheets', 'reading.css'), ('javascripts', 'reading.js')):
            self.assertEqual((self.work / 'scripts/site_media' / filename).read_bytes(),
                             (self.out / directory / filename).read_bytes())

    def test_learning_catalog_covers_all_chapters_and_question_anchors(self):
        data = (self.out / 'javascripts/learning-catalog.js').read_text(encoding='utf-8')
        catalog = json.loads(data.split(' = ', 1)[1].rstrip(';\n'))
        self.assertEqual(19, len(catalog['chapters']))
        self.assertEqual(124, len(catalog['questions']))
        quiz = (self.out / 'p9-00-quiz.md').read_text(encoding='utf-8')
        ids = [question['id'] for question in catalog['questions']]
        self.assertEqual(len(ids), len(set(ids)))
        for question in catalog['questions']:
            self.assertIn(f'id="{question["id"]}"', quiz)
            self.assertEqual('p9-00-quiz.html#' + question['id'], question['href'])
        self.assertEqual((self.work / 'scripts/site_media/progress.js').read_bytes(),
                         (self.out / 'javascripts/progress.js').read_bytes())

    def test_homepage_hero_counts_match_the_real_inventory(self):
        """首页规模清单的数字必须由真实清单推导：加动画/题目/样板忘改首页即红灯。

        清单在 docs/index.md 里是一段 `<ul class="learning-stats">`，四项各占一个
        `<li>`（站点产物里再被 reading.css 渲染成药丸 chip）。最后一项
        「N 道章节题 + M 道专题题」含两个数，单独取。
        """
        home = (self.out / 'index.md').read_text(encoding='utf-8')
        block = re.search(r'<ul class="learning-stats">(.*?)</ul>', home, re.S)
        if block is None:
            self.fail('首页 hero 规模清单缺失或格式改变')
        items = re.findall(r'<li>\s*(.*?)\s*</li>', block.group(1), re.S)
        self.assertEqual(4, len(items), '首页 hero 规模清单应恰好四项，实际 %d 项' % len(items))

        def number(pattern, text):
            # chip 里的数字包在 <strong> 里（reading.css 把它做成「读数」字重），
            # 先剥标签再匹配 —— 本测试钉的是「数字必须来自真实清单」，不是标签形状。
            m = re.search(pattern, re.sub(r"</?\w+>", "", text))
            if m is None:
                self.fail(f'首页 hero 规模清单格式改变：{pattern!r} 不匹配 {text!r}')
            return int(m.group(1))

        claimed_chapters = number(r'^(\d+) 章核心内容$', items[0])
        animations = number(r'^(\d+) 张原理动画$', items[1])
        lessons = number(r'^(\d+) 个可控教学样板$', items[2])
        chapter_q = number(r'^(\d+) 道章节题', items[3])
        extra_q = number(r'\+ (\d+) 道专题题$', items[3])
        data = (self.out / 'javascripts/learning-catalog.js').read_text(encoding='utf-8')
        catalog = json.loads(data.split(' = ', 1)[1].rstrip(';\n'))
        studies = []
        for page in self.out.glob('*.md'):
            studies += re.findall(r'<a id="(\w+)-study"></a>', page.read_text(encoding='utf-8'))
        self.assertEqual(len(catalog['chapters']), claimed_chapters, 'hero 章数与学习目录不符')
        self.assertEqual(len(list((self.work / 'assets/svg').glob('*.svg'))), animations,
                         'hero 动画张数与 assets/svg 实际文件数不符')
        self.assertEqual(len(set(studies)), lessons, 'hero 样板数与 *-study 互动课锚点不符')
        self.assertEqual(sum(1 for q in catalog['questions'] if re.fullmatch(r'q-ch\d+-\d+', q['id'])),
                         chapter_q, 'hero 章节题数与 q-ch* 题目不符')
        self.assertEqual(sum(1 for q in catalog['questions'] if re.fullmatch(r'q-extra-\d+', q['id'])),
                         extra_q, 'hero 专题题数与 q-extra-* 题目不符')


    # ---------- 篇级落地页与章级验收 ----------
    def test_part_landing_pages_link_all_children(self):
        """篇级落地页不能退化成一句标题：必须给出「怎么读」并链接本篇全部子页。"""
        for landing, prefix in sorted(PART_LANDING_PREFIX.items()):
            with self.subTest(page=landing):
                text = (self.work / "docs" / landing).read_text(encoding="utf-8")
                self.assertIn("怎么读", text)
                children = [p.name for p in sorted((self.work / "docs").glob(prefix + "*.md"))
                            if p.name != landing]
                self.assertTrue(children, f"{landing} 没有找到任何子页")
                for child in children:
                    self.assertIn(f"({child}", text, f"{landing} 缺少子页链接 {child}")

    def test_every_chapter_declares_verifiable_outcomes(self):
        """章首「学完你应能」落实共建铁律 9：新增章节忘写验收标准即红灯。"""
        chapters = sorted(p.name for p in (self.work / "docs").glob("p[1-4]-*-ch*.md"))
        self.assertGreaterEqual(len(chapters), 19)
        for page in chapters:
            with self.subTest(page=page):
                self.assertIn("学完你应能", (self.work / "docs" / page).read_text(encoding="utf-8"))

    def test_cheatsheet_cites_every_chapter(self):
        """公式速查表是全站的「算」入口：19 章每章至少贡献一条，新增章节漏入表即红灯。"""
        text = (self.work / "docs" / "p0-08-cheatsheet.md").read_text(encoding="utf-8")
        chapters = sorted(p.name for p in (self.work / "docs").glob("p[1-4]-*-ch*.md"))
        self.assertGreaterEqual(len(chapters), 19)
        for page in chapters:
            with self.subTest(page=page):
                self.assertIn(f"]({page}#", text, f"速查表没有引用 {page}")

    # ---------- 共建页脚 ----------
    def test_feedback_footer_on_every_page(self):
        for page in sorted(self.out.glob("*.md")):
            with self.subTest(page=page.name):
                text = page.read_text(encoding="utf-8")
                self.assertIn("issues/new?template=content-fix.yml", text)
                self.assertIn("issues/new?template=new-topic.yml", text)

    def test_docs_stay_clean(self):
        """页脚 / lightbox / 懒加载属性 / description / 提示卡只进站点产物，docs/ 里不能出现。

        懒加载要按 `<img …loading="lazy">` 匹配——更新日志里会**用文字**提到这个属性，
        只查字面量会把正常的文档表述误判成注入。
        """
        for page in sorted((self.work / "docs").glob("*.md")):
            with self.subTest(page=page.name):
                text = page.read_text(encoding="utf-8")
                self.assertNotIn("issues/new?template=content-fix.yml", text)
                self.assertNotIn("gal-card", text)
                self.assertNotIn('<div class="callout callout-', text,
                                 "docs/ 里要能直接读，提示卡是站点产物才有的")
                self.assertIsNone(re.search(r'<img[^>]*\bloading="lazy"', text),
                                  "docs/ 里的 <img> 不该带懒加载属性")
                self.assertFalse(text.startswith("---\n"), "docs/ 里不该有 front-matter")

    # ---------- 标题层级 ----------
    HEADING = re.compile(r"<h([1-6])(?:\s[^>]*)?>(.*?)</h\1>", re.S)
    CALL_TAG = re.compile(r"<[^>]+>")
    # 与 build_site.CALLOUT_KINDS 同源：新增一类卡片时，这条对账不可能漏。
    SIGNATURE = re.compile("^> *\\*\\*(?:%s)\\*\\*[：:]"
                           % "|".join(sorted(re.escape(e) for e in CALLOUT_KINDS)))

    def headings(self, name):
        return [(int(m.group(1)), self.CALL_TAG.sub("", m.group(2)).replace("&para;", "").strip())
                for m in self.HEADING.finditer(self.body_html(name))]

    def test_every_page_renders_exactly_one_h1(self):
        """正文里必须恰好一个 h1。

        48 个页面原本用 `##` 当章标题，正文里没有 h1，Material 就补一个来自 nav 的
        `<h1>`，正文再渲染一个**同名**的 `<h2>` —— 标题在页面上出现两遍，
        而且文档大纲里根本没有「这一页的主题」。修法是 build_site.shift_headings()。
        """
        for page in sorted(self.site.glob("*.html")):
            with self.subTest(page=page.name):
                h1 = [t for lv, t in self.headings(page.name) if lv == 1]
                self.assertEqual(1, len(h1), f"h1 个数应为 1，实际 {len(h1)}：{h1}")

    def test_no_page_repeats_its_title_as_h1_plus_h2(self):
        for page in sorted(self.site.glob("*.html")):
            with self.subTest(page=page.name):
                hs = self.headings(page.name)
                dup = [a[1] for a, b in zip(hs, hs[1:])
                       if a[0] == 1 and b[0] == 2 and a[1] and a[1] == b[1]]
                self.assertEqual([], dup, f"标题重复（主题 h1 与正文首个 h2 同名）：{dup}")

    def test_no_page_skips_a_heading_level(self):
        """h1 → h3 这种跳级会让屏幕阅读器读不出层级（WCAG 1.3.1）。

        实测踩过一次：入场诊断组件用 h3 当「第 N 题」的题面，而它长在页面最顶部，
        于是每页第一条标题就是 h1 → h3。
        """
        for page in sorted(self.site.glob("*.html")):
            with self.subTest(page=page.name):
                levels = [lv for lv, _t in self.headings(page.name)]
                for a, b in zip(levels, levels[1:]):
                    self.assertLessEqual(b, a + 1,
                                         f"标题层级从 h{a} 跳到 h{b}：{self.headings(page.name)}")

    # ---------- 章首舞台 ----------
    def test_every_chapter_opens_with_a_hero_stage(self):
        """19 个章页产物各有一只章首舞台：章号、h1、开场提示卡与水印一个不少。"""
        chapters = [p.name for p in self.out.glob("*.md")
                    if re.fullmatch(r"p\d+-\d+-ch\d+\.md", p.name)]
        self.assertGreaterEqual(len(chapters), 19, "章页数量异常")
        for name in sorted(chapters):
            with self.subTest(page=name):
                html = self.body_html(name.replace(".md", ".html"))
                m = re.search(r'<div class="chapter-hero" data-chapter="(\d+)">', html)
                if m is None:
                    self.fail("章页没有章首舞台")
                hero = html[m.start():html.find("</div>", html.find(
                    'class="chapter-hero-num"', m.start()))]
                self.assertIn("<h1", hero, "舞台里没有章标题")
                self.assertEqual(1, hero.count('class="chapter-emblem"'),
                                 "舞台里应当恰好有一枚章徽")
                self.assertIn('viewBox="0 0 64 64"', hero, "章徽画布不对")
                self.assertLess(hero.index("<h1"), hero.index('class="chapter-emblem"'),
                                "章徽要跟在章标题之后")
                self.assertGreaterEqual(hero.count('<div class="callout callout-'), 2,
                                        "舞台至少要有两张开场提示卡")
                num = None
                for pm in re.finditer(r"<p ([^>]*)>(\d+)</p>", hero):
                    attrs = pm.group(1)
                    if "chapter-hero-num" in attrs and 'aria-hidden="true"' in attrs:
                        num = pm
                        break
                if num is None:
                    self.fail("舞台缺章号水印（或水印不是 aria-hidden）")
                self.assertEqual(m.group(1), num.group(2), "章号水印与 data-chapter 不一致")

    def test_non_chapter_pages_have_no_hero_stage(self):
        """舞台是章页专属：首页/速查表/动画中心/篇首页不得被误包。

        注意匹配的是**开标签** `<div class="chapter-hero"`：更新日志正文里
        提到过这个词（转义文本也含 `chapter-hero` 子串），只查子串会假红。
        篇首页有它们自己的 `.part-hero`（下一条测试），不算误包。
        """
        for name in ("index.html", "p0-08-cheatsheet.html", "p5-00-part5.html",
                     "p1-00-part1.html", "p9-12-changelog.html",
                     "p0-11-conventions.html", "p0-12-symbols.html",
                     "p9-15-glossary.html"):
            with self.subTest(page=name):
                self.assertNotIn('<div class="chapter-hero"', self.body_html(name),
                                 f"{name} 被误包了章首舞台")

    def test_every_part_opens_with_a_stage(self):
        """9 个篇级落地页各有一只篇首舞台：篇号、h1 与水印一个不少。"""
        parts = sorted(p.name for p in self.out.glob("*.md")
                       if re.fullmatch(r"p\d+-00-[a-z0-9\-]+\.md", p.name))
        self.assertEqual(9, len(parts), f"篇首页数量异常：{parts}")
        for name in parts:
            with self.subTest(page=name):
                html = self.body_html(name.replace(".md", ".html"))
                m = re.search(r'<div class="part-hero" data-part="(\d+)">', html)
                if m is None:
                    self.fail("篇首页没有篇首舞台")
                num = None
                for pm in re.finditer(r"<p ([^>]*)>(\d+)</p>", html):
                    attrs = pm.group(1)
                    if "part-hero-num" in attrs and 'aria-hidden="true"' in attrs:
                        num = pm
                        break
                if num is None:
                    self.fail("舞台缺篇号水印（或水印不是 aria-hidden）")
                self.assertEqual(m.group(1), num.group(2), "篇号水印与 data-part 不一致")

    def test_demo_links_all_become_pills(self):
        """docs/ 里整行动画演示链接必须逐行成为产物药丸，一行不多一行不少。"""
        pattern = re.compile(
            r"^\[动画演示[^\]]*\]\(p5-00-part5\.md#demo\d+\)"
            r"(?: · \[[^\]]*\]\(p5-00-part5\.md#demo\d+\))*$")
        expected = 0
        for page in sorted((self.work / "docs").glob("*.md")):
            in_fence = False
            for line in page.read_text(encoding="utf-8").split("\n"):
                s = line.strip()
                if s.startswith("```") or s.startswith("~~~"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                if pattern.match(s.rstrip()):
                    expected += 1
        # V2 内嵌播放器替代了部分独立链接行；链接数不是动画数量门禁。
        # 保留非空覆盖，并把每一行与产物逐项对账。
        self.assertGreater(expected, 0, "docs/ 未扫描到任何独立动画链接")
        got = sum(p.read_text(encoding="utf-8").count('<div class="demo-link" markdown="1">')
                  for p in self.out.glob("*.md"))
        self.assertEqual(expected, got, "药丸数与 docs/ 的动画链接行数不一致（漏包或多包）")

    def test_hero_stage_css_is_published(self):
        """章首/篇首舞台与动画药丸的样式、打印降级必须跟着产物走。"""
        css = (self.site / "stylesheets" / "typography.css").read_text(encoding="utf-8")
        self.assertIn(".chapter-hero", css)
        self.assertIn(".part-hero", css)
        self.assertIn(".chapter-hero-num", css)
        self.assertIn(".chapter-emblem", css)
        self.assertIn(".demo-link", css)
        self.assertIn("@media print", css)

    # ---------- 就地算计算器 ----------
    CALC_SPOTS = {
        "p1-01-ch0.md": ["divider"],
        "p1-02-ch1.md": ["electrolyte"],
        "p1-06-ch5.md": ["swcap"],
        "p1-07-ch6.md": ["opamp"],
        "p1-08-ch7.md": ["hysteresis"],
        "p1-09-ch8.md": ["samplehold"],
        "p2-02-ch12.md": ["loop"],
        "p2-03-ch13.md": ["buck"],
        "p2-01-ch11.md": ["miller", "noise"],
        "p4-01-ch16.md": ["probe"],
    }

    def test_inline_calcs_are_placed_next_to_their_worked_examples(self):
        """每个计算器容器都要长在它对应算例的章节里，型号一个不重不漏。"""
        for name, calcs in self.CALC_SPOTS.items():
            with self.subTest(page=name):
                text = (self.out / name).read_text(encoding="utf-8")
                hits = re.findall(r'<div class="calc" data-calc="([a-z]+)"></div>', text)
                self.assertEqual(calcs, hits, f"{name} 的计算器容器缺失或型号不对")
        self.assertEqual(11, sum(map(len, self.CALC_SPOTS.values())), "型号表变了就同步这条对账")

    def test_inline_calc_scripts_are_published_and_wired(self):
        """calc.js 要随产物发布、被 mkdocs 引用，且每个型号都有渲染逻辑。"""
        js = (self.site / "javascripts" / "calc.js").read_text(encoding="utf-8")
        for calc in [c for calcs in self.CALC_SPOTS.values() for c in calcs]:
            with self.subTest(calc=calc):
                self.assertIn(f"{calc}: {{", js, f"calc.js 缺型号 {calc}")
        yml = (self.build / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn("javascripts/calc.js", yml, "mkdocs 没有加载 calc.js")
        css = (self.site / "stylesheets" / "typography.css").read_text(encoding="utf-8")
        self.assertIn(".calc-box", css, "计算器样式没随产物发布")

    # ---------- 标志性提示卡 ----------
    def test_signature_blockquotes_become_cards(self):
        """真实正文卡片保持完整；全部标签用夹具覆盖，避免强迫正文凑齐卡片类型。"""
        counts = {}
        for page in sorted(self.out.glob("*.md")):
            text = page.read_text(encoding="utf-8")
            for kind in re.findall(r'<div class="callout callout-([a-z]+)" markdown="1">', text):
                counts[kind] = counts.get(kind, 0) + 1
        self.assertGreaterEqual(sum(counts.values()), 160,
                                f"提示卡总数偏少，可能有一类没被包上：{counts}")
        self.assertLessEqual(set(counts), set(CALLOUT_KINDS.values()))
        # 附件类在 V2 改写后可没有实例；仍逐标签验证转换能力，正文逐行
        # 对账由 test_card_count_equals_the_number_of_signature_prompts_in_docs 守住。
        from build_site import wrap_callouts
        for label, kind in CALLOUT_KINDS.items():
            with self.subTest(label=label):
                rendered = wrap_callouts(f'> **{label}**：验证内容。\n')
                self.assertIn(f'<div class="callout callout-{kind}" markdown="1">',
                              rendered)
                self.assertIn('验证内容。', rendered)

    def test_no_signature_blockquote_is_left_unwrapped(self):
        """包完不该还剩 `> **精髓**：` 这种——漏一张就是「同一类提示两种长相」。"""
        leftovers = []
        for page in sorted(self.out.glob("*.md")):
            text = page.read_text(encoding="utf-8")
            for num, line in enumerate(text.split("\n"), 1):
                if self.SIGNATURE.match(line):
                    leftovers.append(f"{page.name}:{num} {line[:40]}")
        self.assertEqual([], leftovers, "还有没被包成卡片的标志性引用块：\n  "
                         + "\n  ".join(leftovers))

    def test_card_count_equals_the_number_of_signature_prompts_in_docs(self):
        """独立数一遍 docs/ 里的提示行，和产物里的卡片数对上——防「切多 / 切少」。

        切分规则是「每一行**自己**以标志性 emoji 开头就另起一张卡」，所以
        「签名行数」与「卡片数」必须一一对应。这条不复用 build_site 的函数，
        是照着规则独立数一遍——两边一起漂移才可能同时错。
        """
        expected = 0
        for page in sorted((self.work / "docs").glob("*.md")):
            in_fence = False
            for line in page.read_text(encoding="utf-8").split("\n"):
                s = line.strip()
                if s.startswith("```") or s.startswith("~~~"):
                    in_fence = not in_fence
                    continue
                if in_fence or not line.startswith(">"):
                    continue
                if self.SIGNATURE.match(line):
                    expected += 1
        got = sum(len(re.findall(r'<div class="callout callout-[a-z]+" markdown="1">',
                                 p.read_text(encoding="utf-8")))
                  for p in self.out.glob("*.md"))
        self.assertGreater(expected, 160, f"docs/ 里只数到 {expected} 个提示行，扫描器可能坏了")
        self.assertEqual(expected, got, "卡片数与 docs/ 里的提示行数不一致（切多或切少）")

    def test_no_card_is_empty(self):
        """空卡片 = 切割切错了（把提示行切走、只剩空行）。"""
        for page in sorted(self.out.glob("*.md")):
            text = page.read_text(encoding="utf-8")
            for m in re.finditer(r'<div class="callout callout-([a-z]+)" markdown="1">\n(.*?)\n</div>',
                                 text, re.S):
                with self.subTest(page=page.name, kind=m.group(1)):
                    self.assertTrue(m.group(2).strip(), "空的提示卡")

    # ---------- 社交卡片与结构化数据 ----------
    @staticmethod
    def _png_size(path):
        raw = path.read_bytes()[:33]
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            raise AssertionError(f"{path} 不是 PNG")
        return (int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big"))

    def test_social_card_is_self_hosted_and_the_right_size(self):
        """og:image 必须指向本站的产物，且真是一张 1200×630 的 PNG。

        原来外链 Wikimedia 的电路板照片：抓取方要跨域取第三方资源（国内常超时），
        而且那张图与本站内容无关。自托管后还要防「只改了 URL、忘了提交图片」——
        所以这里既查 meta 也查文件本体。
        """
        from build_site import OG_HEIGHT, OG_IMAGE, OG_WIDTH
        self.assertTrue(OG_IMAGE.startswith("https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/"),
                        f"og:image 必须自托管：{OG_IMAGE}")
        self.assertNotIn("wikimedia", OG_IMAGE)
        page = self.rendered("p1-02-ch1.html")
        for tag, attr in (("og:image", "property"), ("twitter:image", "name")):
            with self.subTest(tag=tag):
                m = re.search(rf'<meta {attr}="{tag}" content="([^"]+)"', page)
                if m is None:
                    self.fail(f"缺少 {tag}")
                self.assertEqual(OG_IMAGE, m.group(1), f"{tag} 必须指向自托管产物")
        local = self.site / OG_IMAGE.split("/analog-circuit-roadmap/", 1)[1]
        self.assertTrue(local.is_file(), f"站点产物里没有 {local}")
        self.assertEqual((OG_WIDTH, OG_HEIGHT), self._png_size(local))
        self.assertEqual((1200, 630), self._png_size(local),
                         "og:image 应当是 1200×630（社交卡片的 1.91:1）")
        for tag in ("og:image:width", "og:image:height", "twitter:image:alt"):
            self.assertIn(tag, page)

    def test_every_page_ships_parseable_json_ld(self):
        """结构化数据必须能被 json.loads 直接吃下（转义错一个字符就整块失效）。"""
        for page in sorted(self.site.glob("*.html")):
            with self.subTest(page=page.name):
                blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                                    self.rendered(page.name), re.S)
                self.assertEqual(1, len(blocks), "每页应当恰好一块 JSON-LD")
                data = json.loads(blocks[0])
                graph = data.get("@graph", [])
                self.assertEqual("https://schema.org", data.get("@context"))
                self.assertEqual(2, len(graph), f"应当有 WebSite + 页面节点：{graph}")
                self.assertEqual("WebSite", graph[0]["@type"])
                self.assertIn(graph[1]["@type"], ("WebPage", "TechArticle"))
                self.assertTrue(graph[1]["headline"].strip(), "headline 不能为空")
                self.assertTrue(graph[1]["description"].strip(), "description 不能为空")
                self.assertEqual("zh-CN", graph[1]["inLanguage"])

    def test_homepage_is_a_webpage_and_the_rest_are_articles(self):
        def structured_data(name):
            match = re.search(r'<script type="application/ld\+json">(.*?)</script>',
                              self.rendered(name), re.S)
            if match is None:
                self.fail(f'{name} 缺 JSON-LD')
            return json.loads(match.group(1))
        home = structured_data("index.html")
        self.assertEqual("WebPage", home["@graph"][1]["@type"])
        ch1 = structured_data("p1-02-ch1.html")
        self.assertEqual("TechArticle", ch1["@graph"][1]["@type"])

    def test_json_ld_escapes_html_specials(self):
        """把模板里的 JSON-LD 表达式抠出来，喂一份恶意摘要，直接看它转义没有。

        真站点目前**没有任何一页**的标题/摘要含 `<` `>` `&`（实测 62 页 0 命中），
        所以「扫产物里有没有裸尖括号」这条断言永远为真——是个假绿。
        摘要器会把 `&lt;` 还原成 `<`，所以这个风险是真的、只是暂时没被触发。
        这里单独渲染那段表达式，才真的能红。
        """
        import jinja2
        from build_site import OVERRIDES_MAIN_HTML

        m = re.search(r'<script type="application/ld\+json">\{\{(.*?)\}\}</script>',
                      OVERRIDES_MAIN_HTML, re.S)
        if m is None:
            self.fail("模板里找不到 JSON-LD 的 {{ … }} 表达式")
        expr = m.group(1)
        self.assertIn("tojson", expr, "JSON-LD 必须走 tojson（它把 < > & 转成 \\uXXXX）")

        class _Config:
            site_url = "https://example.test/x/"
            site_name = "站点"
            site_description = "描述"

        class _Page:
            is_homepage = False
            canonical_url = "https://example.test/x/a.html"
            title = "标题"
            meta = {"description": "危险 </script><script>alert(1)</script> & <b>粗</b>"}

        out = jinja2.Environment(autoescape=True).from_string(
            "{{" + expr + "}}").render(config=_Config(), page=_Page())
        for ch in "<>&":
            with self.subTest(char=ch):
                self.assertNotIn(ch, out, f"JSON-LD 里出现了裸 {ch!r}，会截断 <script>")
        data = json.loads(out)
        self.assertEqual("TechArticle", data["@graph"][1]["@type"])
        self.assertIn("</script>", data["@graph"][1]["description"],
                      "转义应当是「JSON 层面可还原」的，而不是把内容删掉")

    # ---------- 排版层 ----------
    def test_typography_layer_is_published_and_linked(self):
        from build_site import MKDOCS_YML
        self.assertRegex(MKDOCS_YML,
                         re.compile(r"^[ \t]*-[ \t]*stylesheets/typography\.css[ \t]*$", re.M),
                         "typography.css 必须在 extra_css 里被真正引用（注释不算）")
        css = self.site / "stylesheets" / "typography.css"
        self.assertTrue(css.is_file(), "typography.css 没有发布到站点")
        text = css.read_text(encoding="utf-8")
        for kind in ("callout-gem", "callout-warn", "callout-calc"):
            self.assertIn(kind, text)
        self.assertIn("stylesheets/typography.css", self.rendered("p1-02-ch1.html"))

    def test_every_callout_kind_has_light_and_dark_colours(self):
        """13 类提示卡**每一类**都要有浅色与深色两套 `--co`。

        只查「文件里出现过 `data-md-color-scheme="slate"`」是假绿：漏掉某一类，
        那一类在深色主题下就是深色文字落在深色卡片上——等于没写，而且没人看得出来
        （变异验证时踩过这个坑）。
        """
        from build_site import CALLOUT_KINDS
        kinds = sorted(set(CALLOUT_KINDS.values()))
        raw = (self.site / "stylesheets" / "typography.css").read_text(encoding="utf-8")
        # 先剥掉 /* … */ —— 否则「被注释掉的那条规则」仍然能被正则匹配到，
        # 漏配一整类颜色却照样绿灯（变异验证时踩过这个坑）。
        text = re.sub(r"/\*.*?\*/", " ", raw, flags=re.S)
        dark_rules = re.findall(r'\[data-md-color-scheme="slate"\][^{]*\{[^}]*\}', text)
        dark = "\n".join(dark_rules)
        # 浅色那边必须先把深色规则**整条摘掉**：`[data-md-color-scheme="slate"] … .callout-warn { --co }`
        # 里同样含 `.callout-warn { --co`，不摘掉的话浅色漏配也照样绿灯
        # （变异验证时踩过这个坑）。
        light = text
        for rule in dark_rules:
            light = light.replace(rule, " ")
        self.assertGreaterEqual(len(kinds), 13, f"词表缩水了：{kinds}")
        for slug in kinds:
            with self.subTest(kind=slug):
                self.assertRegex(light, rf"\.callout-{slug}\s*\{{[^}}]*--co",
                                 f"{slug} 没有浅色配色")
                self.assertRegex(dark, rf"\.callout-{slug}\b[^{{]*\{{[^}}]*--co",
                                 f"{slug} 没有深色配色")

    def test_build_log_reports_no_missing_anchors(self):
        """mkdocs 的站内锚点校验必须一条不报，同时更新日志的 8 个锚点仍在产物里。

        正文里写字面的 script / title 这类「原始文本」标签——哪怕裹在反引号里——
        会让 mkdocs 的 HTML 预处理器进入 raw-text 模式，把其后每个 id 属性都吞掉，
        于是**真实存在**的 a 锚点被逐条报成死链（v3.55.1 之前实测 7 条）。这条噪声
        真正的代价是把真死链埋在已知误报里：站内锚点只有这一路在全量校验。
        「删锚点」或「忽略校验」也能消音，但那样速览跳转就塌了，所以同时钉产物。
        """
        noise = [line for line in f"{self.stdout}\n{self.stderr}".splitlines()
                 if "no such anchor" in line]
        self.assertEqual([], noise, "mkdocs 报出锚点缺失：正文里的字面标签会吞掉后续 id")
        page = self.rendered("p9-12-changelog.html")
        self.assertEqual(8, len(re.findall(r'<a id="log-v[\w-]+"></a>', page)),
                         "更新日志的系列锚点必须留在产物里——别拿删锚点当消音")

    def test_changelog_version_rows_render_as_table_cells(self):
        """更新日志每个加粗版本行都要渲染成真 `<td>` 首列，不是字面管道符段落。

        v3.59 起「| **v3.NN** |」行曾插在系列锚点与组标题之间——那里没有表头
        与分隔行，mkdocs 把它渲染成带字面「|」的段落，v3.59–v3.63 五个版本
        在线上挂了五轮才被读者视角发现；数源行数的护栏（docs_links 的系列
        对账）全程绿着。这条在**渲染层**对账：源里每个加粗版本行，产物里
        必须有同数的 `<td><strong>v3.NN</strong></td>` 首列 cell——再往锚点
        后裸插版本行，这里当场红。
        """
        src = (self.work / "docs" / "p9-12-changelog.md").read_text(encoding="utf-8")
        rows = re.findall(r"^\| \*\*(v3\.\d+(?:\.\d+)?(?:（当前）)?)\*\* \|", src, re.M)
        page = self.rendered("p9-12-changelog.html")
        cells = re.findall(
            r"<td[^>]*>\s*<strong>(v3\.\d+(?:\.\d+)?(?:（当前）)?)</strong>\s*</td>", page)
        self.assertEqual(len(rows), len(cells),
                         f"源里 {len(rows)} 行加粗版本行、产物里只有 {len(cells)} 个"
                         "首列 cell——有版本行没进表格，被渲染成了带字面「|」的段落")
        self.assertEqual(sorted(rows), sorted(cells),
                         "版本行与产物首列 cell 对不上——一边多、一边少或版本号写错")

    # ---------- 辅助 ----------
    @staticmethod
    def _n(demo_anchor):
        return int(re.sub(r"\D", "", demo_anchor))


class NavIndexPatchTests(unittest.TestCase):
    """Material 的 navigation.indexes 对「篇首页」不生效，得给上游模板打补丁。

    `navigation.indexes` 只认 MkDocs 的 `Page.is_index`，而那个属性的定义就是
    `self.file.name == 'index'`（README.md 会被归一成 index）。本站的篇首页叫
    `p1-00-part1.md` —— 命不中，于是节标题退化成纯折叠标签（点它只能展开）、
    篇首页又以普通子项出现在列表首位，两处标题**一字不差**，侧栏里每个篇标题
    都重复一行（实测 9 处）。补丁把「首个标题与节标题相同的叶子页」也算作该节的
    index，于是标题变成链接、篇首页不再重复出现。

    这组测试**不构建站点**（快），只钉住补丁本身；渲染结果由
    `SiteBuildTests.test_sidebar_part_titles_are_links_not_duplicated_rows` 验。
    """

    @staticmethod
    def _upstream():
        import material
        return (Path(material.__file__).parent / "templates" / "partials"
                / "nav-item.html").read_text(encoding="utf-8")

    def test_the_anchor_appears_exactly_once_upstream(self):
        self.assertEqual(
            1, self._upstream().count(NAV_ITEM_ANCHOR),
            "Material 的 partials/nav-item.html 结构变了：锚点找不到或出现多次，"
            "请重新核对 build_site.NAV_ITEM_ANCHOR / NAV_ITEM_PATCHED 这对补丁")

    def test_the_patch_teaches_it_about_part_index_pages(self):
        """判据是「标题相同」——因为重复的根源正是这两处标题相同。"""
        self.assertIn("item.title == nav_item.title", NAV_ITEM_PATCHED)
        self.assertNotIn("item.title == nav_item.title", NAV_ITEM_ANCHOR)

    def test_the_patch_only_accepts_a_leaf_page(self):
        """必须限定 `not item.children`，否则会把子节也当成 index。"""
        self.assertIn("not item.children and item.title == nav_item.title",
                      NAV_ITEM_PATCHED)

    def test_the_override_differs_from_upstream_only_at_the_anchor(self):
        self.assertEqual(self._upstream().replace(NAV_ITEM_ANCHOR, NAV_ITEM_PATCHED),
                         nav_item_override())

    def test_a_missing_anchor_fails_loudly_instead_of_patching_blindly(self):
        with tempfile.TemporaryDirectory(prefix="nav-item-") as tmp:
            broken = Path(tmp) / "nav-item.html"
            broken.write_text("{% macro render(nav_item, path, level, parent) %}{% endmacro %}",
                              encoding="utf-8")
            with self.assertRaises(SystemExit) as caught:
                nav_item_override(broken)
            self.assertIn("nav-item.html", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
