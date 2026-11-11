"""无障碍静态护栏：SVG 的可读名称与描述、图片 alt、减弱动效的落点。
Run: python -B -m unittest discover -s scripts -p test_a11y.py -v

为什么需要这组测试：全站 313 张 `<img>` 里有 108 张是自动播放的 SMIL 动画，
而 SVG 自身此前只有 `<title>`、没有 `<desc>`，也没有 `role`/`aria-*`——
读屏用户拿到的是一个"没有名字的图形"。更糟的是 3 张实物图连 `alt` 都没有，
读屏会直接念出文件 URL。

这里把四件事钉成红灯（都不需要浏览器，纯静态检查）：
  1. 每张 SVG 有 role="img" + aria-labelledby + 非空 <title> + 非空 <desc>；
  2. <desc> 里带上这张图自己的节拍字幕（不许串到别的图），
     且描述文案与图内字幕逐字一致；
  3. **SVG 里不得出现 `prefers-reduced-motion` 的 media query** ——
     这条是踩过坑的红线，理由见该测试的 docstring（真行为由
     test_reduced_motion.py 在 Chromium 里验证）；
  4. docs/ 里每个 <img> 都有非空 alt（代码围栏与行内代码里的 `<img>`
     是文档在讲语法，不是真标签，必须先剥掉再查）。
"""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from xml.sax.saxutils import unescape

ROOT = Path(__file__).resolve().parents[1]
SVGS = sorted((ROOT / "assets" / "svg").glob("*.svg"))
DOCS = sorted((ROOT / "docs").glob("*.md"))

TITLE = re.compile(r'<title id="ttl">(.*?)</title>', re.S)
DESC = re.compile(r"<desc>(.*?)</desc>", re.S)
IMG = re.compile(r"<img\b[^>]*>", re.I)
ALT = re.compile(r'\balt="([^"]*)"', re.I)


def strip_code(text):
    """剥掉围栏代码块与行内代码——里面的 <img> 是文档在讲语法。"""
    text = re.sub(r"^[ \t]*(```|~~~).*?^[ \t]*\1[ \t]*$", "", text, flags=re.S | re.M)
    return re.sub(r"`[^`\n]*`", "", text)


class SvgAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {p.name: p.read_text(encoding="utf-8") for p in SVGS}

    def test_inventory_is_complete(self):
        """防假绿：探针必须真的看到 108 张图。"""
        self.assertGreaterEqual(len(self.sources), 108,
                                "assets/svg 少于 108 张，下面的断言会变成空转")

    def test_every_svg_has_role_name_and_description(self):
        missing = []
        for name, text in self.sources.items():
            title = TITLE.search(text)
            desc = DESC.search(text)
            if 'role="img"' not in text:
                missing.append((name, "role=img"))
            if 'aria-labelledby="ttl"' not in text:
                missing.append((name, "aria-labelledby"))
            if not title or len(title.group(1).strip()) < 6:
                missing.append((name, "title"))
            if not desc or len(desc.group(1).strip()) < 6:
                missing.append((name, "desc"))
        self.assertEqual([], missing, "这些图缺可读名称/描述：" + repr(missing[:10]))

    def test_description_carries_this_diagrams_own_beat_narration(self):
        """<desc> 的节拍必须与图内字幕**逐字相同**。

        只查"desc 里的文案在本文件出现过"是不够的——desc 本身就在文件里，
        断言会永远成立（变异验证时踩过这个坑）。这里改成双向对照：
        从图里抽出节拍字幕组（同时带 animateTransform 子节点与 text 的 <g>，
        正是 caption() 的结构），再要求 desc 的节拍串与它完全相等。
        """
        ns = "{http://www.w3.org/2000/svg}"
        with_beats = 0
        for name, text in self.sources.items():
            root = ET.fromstring(text)
            beats = [t.text.strip()
                     for g in root.iter(ns + "g")
                     if any(c.tag == ns + "animateTransform" for c in g)
                     for t in g.iter(ns + "text")
                     if (t.text or "").strip()]
            if not beats:
                continue
            with_beats += 1
            desc = unescape(DESC.search(text).group(1))
            self.assertIn("节拍：", desc, f"{name} 有 {len(beats)} 条节拍字幕，<desc> 却没写")
            self.assertEqual("；".join(beats), desc.split("节拍：", 1)[1],
                             f"{name} 的 <desc> 与图内字幕对不上（串图或漏抄）")
        self.assertGreaterEqual(with_beats, 90,
                                "带节拍描述的图太少，说明字幕登记（_BEATS）没生效")

    def test_no_svg_uses_an_in_svg_reduced_motion_media_query(self):
        """SVG 里**不得**出现 `prefers-reduced-motion` 的 media query。

        这是一条踩过坑的红线。SVG 作为 `<img>` 载入时（本站 108 张动画就是这么嵌的），
        Chrome 把 `prefers-reduced-motion` **恒判为 reduce** —— 页面自己明明是无偏好，
        图片文档里却是 reduce（有头/无头、data: / http、独立启动的 Chrome 155 均实测一致）。
        于是写在 SVG 里的 media query 只有两种结局：要么恒不生效，要么恒生效；
        一旦恒生效，全站动画对**所有人**都是静止的 —— v3.45 正是这么翻车的，
        而且因为测试当时是"把 SVG 当顶层文档打开"（那种上下文里偏好是正常的），
        全套测试都绿灯放行。

        正确做法是让**页面**选源：`build_site.py` 生成 `<stem>.reduce.svg` 静止版，
        再用 `<picture><source media="(prefers-reduced-motion: reduce)">` 挑；
        `<source media>` 在页面上下文里求值，所以是准的。护栏见
        test_site_build.py 的 picture 包装断言与 test_reduced_motion.py 的渲染断言。
        """
        offenders = [name for name, text in self.sources.items()
                     if "prefers-reduced-motion" in text]
        self.assertEqual(
            [], offenders,
            "这些 SVG 里又出现了 SVG 内部的减弱动效 media query（在 <img> 下恒真/恒假，"
            "会把动画对所有人冻住）：" + repr(offenders[:10]))

    def test_every_docs_image_has_a_non_empty_alt(self):
        offenders = []
        total = 0
        for path in DOCS:
            for tag in IMG.findall(strip_code(path.read_text(encoding="utf-8"))):
                total += 1
                alt = ALT.search(tag)
                if not alt or not alt.group(1).strip():
                    offenders.append((path.name, tag[:80]))
        # docs/ 现有 251 张真 <img>；下限取 240，一旦 strip_code 把真标签也剥掉、
        # 或某页整批图丢失，这里会先红。
        self.assertGreaterEqual(total, 240, f"只扫到 {total} 张图，覆盖面不对")
        self.assertEqual([], offenders, "这些图没有 alt：" + repr(offenders[:6]))

    def test_docs_sources_carry_no_emoji(self):
        """docs/ 源文件不得再出现表情符号（v3.82 全退场的永久防线）。

        双色 emoji 块（U+1F000–1FAFF）与曾被当标签用的彩色 dingbat 在站点上
        渲染成彩色图标、与纸墨手绘视觉契约冲突；印刷端的 strip_emoji 则把它们
        静默剥掉（丢标记不丢话）。v3.82 的处置：行内标记换 assets/icons/ 的
        手绘 doodle，历史引文换「算盘」「钻石」这类文字称谓。

        刻意保留：→↑↓↔ 等信号流箭头（EMOJI_RE 本就不含 U+2190–21FF，印刷端
        原样输出）、✓/✗/★ 单色排版符号。docs/superpowers/ 是开发计划，
        不进站点与印刷书，本就不在 DOCS 的 glob 范围。
        """
        emoji = re.compile("[\U0001F000-\U0001FAFF⭐⚡⚠✅❌☰❖⚙✎️‍]")
        offenders = []
        for path in DOCS:
            for lineno, line in enumerate(
                    strip_code(path.read_text(encoding="utf-8")).splitlines(), 1):
                hit = emoji.search(line)
                if hit:
                    offenders.append("%s:%d %s" % (path.name, lineno, hit.group(0)))
        self.assertEqual([], offenders,
                         "docs/ 又混进了表情符号（行内标记请用 assets/icons/ 的"
                         "手绘 doodle，历史引文请用文字称谓）：" + repr(offenders[:8]))


if __name__ == "__main__":
    unittest.main()
