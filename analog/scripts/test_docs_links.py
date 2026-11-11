#!/usr/bin/env python3
"""docs/ 内部链接完整性：跨页锚点必须真实存在（站点与 README 双形态都要能跳转）。"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

MD_LINK = re.compile(r"\]\(([\w\-]+\.md)#([^)/]+)\)")
HTML_HREF = re.compile(r'href="([\w\-]+\.md)#([^"]+)"')
ANCHOR_DEF = re.compile(r'<a\s+id="([^"]+)"')
IMG_REF = re.compile(r'<img src="assets/(svg|icons)/([\w\-]+\.(?:svg|png|jpe?g))"')


class DocsLinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.anchors = {}
        cls.pages = sorted(DOCS.glob("*.md"))
        for p in cls.pages:
            text = p.read_text(encoding="utf-8")
            cls.anchors[p.name] = set(ANCHOR_DEF.findall(text))

    def test_cross_page_anchors_exist(self):
        broken = []
        for p in self.pages:
            text = p.read_text(encoding="utf-8")
            for target, anchor in MD_LINK.findall(text) + HTML_HREF.findall(text):
                if target not in self.anchors:
                    broken.append("%s -> 缺少页面 %s" % (p.name, target))
                elif anchor not in self.anchors[target]:
                    broken.append("%s -> %s 缺少锚点 #%s" % (p.name, target, anchor))
        self.assertEqual([], broken, "\n".join(broken[:10]))

    def test_svg_references_exist(self):
        have = {sub: {f.name for f in (ROOT / "assets" / sub).glob("*.svg")}
                for sub in ("svg", "icons")}
        missing = set()
        for p in self.pages:
            for sub, name in IMG_REF.findall(p.read_text(encoding="utf-8")):
                if name not in have[sub]:
                    missing.add("%s:assets/%s/%s" % (p.name, sub, name))
        self.assertEqual(set(), missing, "引用了不存在的 SVG/图标：%s" % sorted(missing)[:5])

    def test_every_animation_center_demo_is_linked_from_a_chapter(self):
        """动画中心的 demo 若无任何章节回链，读者只能靠翻到第五篇撞见它。

        回归来源：587336a 把 ch16 §16.2 的「img+看点+回链」块换成内嵌
        <figure> 时没把回链搬过去，5.99 四暗器成了全书唯一零回链动画。
        """
        part5 = (DOCS / "p5-00-part5.md").read_text(encoding="utf-8")
        defined = set(re.findall(r'<a id="demo(\d+)"></a>', part5))
        linked = set()
        for p in self.pages:
            if p.name == "p5-00-part5.md":
                continue
            linked |= set(re.findall(r'p5-00-part5\.md#demo(\d+)',
                                     p.read_text(encoding="utf-8")))
        self.assertEqual(set(), defined - linked,
                         "这些动画没有任何章节回链：%s"
                         % sorted(defined - linked, key=int))

    def test_every_page_has_heading(self):
        for p in self.pages:
            text = p.read_text(encoding="utf-8")
            self.assertTrue(re.search(r"^#{1,2} ", text, re.M),
                            "%s 缺少标题（站点导航会退化成文件名）" % p.name)

    def test_chapter_and_part_anchors_belong_to_their_content(self):
        """A link existing on the previous page is still a broken learning route."""
        for page in self.pages:
            match = re.search(r'-(ch\d+|part\d+)\.md$', page.name)
            if match:
                with self.subTest(page=page.name):
                    self.assertIn(match[1], self.anchors[page.name])
                    prefix = page.read_text(encoding='utf-8').splitlines()[:4]
                    self.assertIn(f'<a id="{match[1]}"></a>', prefix)
            self.assertIsNone(re.search(r'<a id="[^"]+"></a>\s*\Z',
                                       page.read_text(encoding='utf-8')),
                              f'{page.name}: anchor stranded at the end of a page')

    def test_source_anchors_are_unique_in_the_single_file_edition(self):
        seen = set()
        for page in self.pages:
            for anchor in ANCHOR_DEF.findall(page.read_text(encoding='utf-8')):
                self.assertNotIn(anchor, seen, f'Duplicate anchor #{anchor}')
                seen.add(anchor)

    def test_numbered_section_links_point_to_the_same_chapter(self):
        pattern = re.compile(r'\[([^\]]+)\]\((p\d+-\d+-ch(\d+)\.md)#[^)]+\)')
        for page in self.pages:
            if page.name == 'p9-12-changelog.md':
                continue
            for match in pattern.finditer(page.read_text(encoding='utf-8')):
                number = re.match(r'^§?(\d+)\.\d+(?:\D|$)', match[1])
                if number:
                    self.assertEqual(int(number[1]), int(match[3]), f'{page.name}: {match[1]} -> {match[2]}')

    def test_every_chapter_has_a_quiz_and_a_return_link(self):
        quiz = (DOCS / 'p9-00-quiz.md').read_text(encoding='utf-8')
        for page in self.pages:
            match = re.search(r'-ch(\d+)\.md$', page.name)
            if match:
                number = match[1]
                with self.subTest(chapter=number):
                    section = re.search(rf'<a id="quiz-ch{number}"></a>\n(.*?)(?=\n## |\Z)',
                                        quiz, re.S)
                    self.assertIsNotNone(section, f'Missing quiz for chapter {number}')
                    self.assertIn(f'({page.name}#ch{number})', section.group(1))

    def test_quiz_numbered_references_land_at_the_named_section(self):
        quiz = (DOCS / 'p9-00-quiz.md').read_text(encoding='utf-8')
        checked = 0
        for label, filename, anchor in re.findall(r'\[([^\]]+)\]\((p\d+-\d+-ch\d+\.md)#([^)]+)\)', quiz):
            number = re.match(r'^§?(\d+(?:\.\d+)+)', label)
            if not number:
                continue
            checked += 1
            target = (DOCS / filename).read_text(encoding='utf-8').split(f'<a id="{anchor}"></a>', 1)[1]
            heading = re.match(r'\s*#{2,4} (\d+(?:\.\d+)+)(?=\s)', target)
            self.assertIsNotNone(heading, f'{label}: #{anchor} must immediately precede its section')
            self.assertEqual(number[1], heading[1], f'{label} -> {filename}#{anchor}')
        self.assertGreater(checked, 80)

    def test_quiz_return_rows_link_to_cheatsheet_section(self):
        quiz = (DOCS / 'p9-00-quiz.md').read_text(encoding='utf-8')
        sheet = (DOCS / 'p0-08-cheatsheet.md').read_text(encoding='utf-8')
        for page in self.pages:
            match = re.search(r'-ch(\d+)\.md$', page.name)
            if match:
                with self.subTest(chapter=match[1]):
                    section = re.search(rf'<a id="quiz-ch{match[1]}"></a>\n(.*?)(?=\n## |\Z)', quiz, re.S)
                    self.assertIsNotNone(section)
                    ref = re.search(r'\[[^\]]*\]\(p0-08-cheatsheet\.md#([a-z]+)\)', section.group(1))
                    self.assertIsNotNone(ref, 'each quiz chapter must link to the formula cheatsheet')
                    self.assertIn(f'<a id="{ref[1]}"></a>', sheet)

    def test_cheatsheet_sections_link_back_to_quizzes(self):
        sheet = (DOCS / 'p0-08-cheatsheet.md').read_text(encoding='utf-8')
        quiz = (DOCS / 'p9-00-quiz.md').read_text(encoding='utf-8')
        blocks = re.findall(r'<a id="([a-z]+)"></a>\n### [^\n]+\n(.*?)(?=\n<a id="|\n本页与|\Z)', sheet, re.S)
        self.assertEqual(len(blocks), 16)
        for sid, body in blocks:
            with self.subTest(section=sid):
                rows = re.findall(r'\[第 (\d+) 章\]\(p9-00-quiz\.md#quiz-ch(\d+)\)', body)
                self.assertTrue(rows, f'{sid} must link to chapter quizzes')
                for shown, anchor in rows:
                    self.assertEqual(shown, anchor)
                    self.assertIn(f'<a id="quiz-ch{shown}"></a>', quiz)

    def test_every_chapter_links_its_cheatsheet_section(self):
        sheet = (DOCS / 'p0-08-cheatsheet.md').read_text(encoding='utf-8')
        for page in self.pages:
            match = re.search(r'-ch(\d+)\.md$', page.name)
            if match:
                with self.subTest(chapter=match[1]):
                    text = page.read_text(encoding='utf-8')
                    ref = re.search(r'\[速查表·[^\]]*\]\(p0-08-cheatsheet\.md#([a-z]+)\)', text)
                    self.assertIsNotNone(ref, 'chapter must link its cheatsheet section')
                    self.assertIn(f'<a id="{ref[1]}"></a>', sheet)

    LIMITS_ROW = re.compile(
        r'> \*\*模型边界\*\*：\[边界速查·[^\]]*\]\(p0-10-model-limits\.md#(limits-[a-z]+)\)')

    def test_every_chapter_links_the_model_limits_card(self):
        """19 章章首各带一行「模型边界」卡，指向的卡锚点必须真的在模型边界页。"""
        limits = (DOCS / 'p0-10-model-limits.md').read_text(encoding='utf-8')
        cards = set(re.findall(r'<a id="(limits-[a-z]+)"></a>', limits))
        chapters = 0
        for page in self.pages:
            match = re.search(r'-ch(\d+)\.md$', page.name)
            if not match:
                continue
            chapters += 1
            with self.subTest(chapter=match[1]):
                text = page.read_text(encoding='utf-8')
                refs = self.LIMITS_ROW.findall(text)
                self.assertEqual(1, len(refs), '章首必须恰好一行「模型边界」卡')
                self.assertIn(refs[0], cards, f'模型边界页缺卡：{refs[0]}')
        self.assertEqual(19, chapters, '章节文件数异常——模型边界行覆盖检查失真了')

    def test_model_limits_cards_cite_every_chapter(self):
        """模型边界页必须把 19 章都引一遍：漏一章，那一章的失效点就没有落点。"""
        limits = (DOCS / 'p0-10-model-limits.md').read_text(encoding='utf-8')
        cited = set(re.findall(r'\(p\d+-\d+-ch(\d+)\.md', limits))
        expected = {str(n) for n in range(19)}
        self.assertEqual(expected, cited,
                         f'缺章：{sorted(expected - cited)} / 多章：{sorted(cited - expected)}')

    def test_model_limits_is_wired_into_the_lookup_family(self):
        """五件套互链：目录页速查族、速查表头尾、首页工具行与阶梯出口。"""
        limits = (DOCS / 'p0-10-model-limits.md').read_text(encoding='utf-8')
        self.assertIn('<a id="limits"></a>', limits, '模型边界页缺页首锚点')
        for name, needle in (
            ('目录页', '**速查五件套**'),
            ('速查表头', '查失效去[模型边界速查]'),
            ('速查表尾', '构成五件套速查族'),
        ):
            text = (DOCS / {'目录页': 'p0-07-toc.md',
                            '速查表头': 'p0-08-cheatsheet.md',
                            '速查表尾': 'p0-08-cheatsheet.md'}[name]).read_text(encoding='utf-8')
            self.assertIn(needle, text, f'{name}没有把模型边界速查编进速查族')
        index = (DOCS / 'index.md').read_text(encoding='utf-8')
        self.assertIn('(p0-10-model-limits.md#limits)', index,
                      '首页没有通往模型边界速查的出口（工具行 / 阶梯「边界」层）')
        # 旧称「四件套」不得残留在任何一页
        stale = [p.name for p in self.pages if '速查四件套' in p.read_text(encoding='utf-8')]
        self.assertEqual([], stale, f'「四件套」旧称未更新：{stale}')

    def test_cheatsheet_calc_links_land_on_real_widgets(self):
        """速查表的「就地算」链接必须落在真的长着计算器的章节小节。"""
        sheet = (DOCS / 'p0-08-cheatsheet.md').read_text(encoding='utf-8')
        links = re.findall(r'\[就地算\]\(([\w\-]+\.md)#([\w\-]+)\)', sheet)
        self.assertGreaterEqual(len(links), 6, '速查表的就地算出口少于 6 个——互链网缩水了')
        pages = {p.name: p.read_text(encoding='utf-8') for p in self.pages}
        for target, anchor in links:
            with self.subTest(target=target):
                self.assertIn(target, pages, f'就地算目标页不存在：{target}')
                self.assertIn(f'<a id="{anchor}"></a>', pages[target],
                              f'就地算锚点不存在：{target}#{anchor}')
                self.assertIn('class="calc" data-calc=', pages[target],
                              f'{target} 里没有计算器——链接成了空头支票')

    def test_model_limits_card_inventory(self):
        """模型边界页的卡与目录必须对账：每张卡都该在目录里有一格。"""
        limits = (DOCS / 'p0-10-model-limits.md').read_text(encoding='utf-8')
        cards = re.findall(r'<a id="(limits-[a-z]+)"></a>', limits)
        self.assertEqual(18, len(cards), f'边界卡应是 18 张（页首 limits 除外），实为 {len(cards)}')
        toc_targets = re.findall(r'\]\(#(limits-[a-z]+)\)', limits)
        missing = sorted(set(cards) - set(toc_targets))
        self.assertEqual([], missing, f'目录漏了这些卡：{missing}')

    SECTION_LABEL = re.compile(r'\[§(\d+(?:\.\d+)+)\]\(([\w\-]+\.md)?#([\w\-]+)\)')

    def test_section_labels_match_the_landing_section(self):
        """[§N.M](page#anchor) 的标签小节号必须与落点小节的真号一致。

        锚点存在性由 test_cross_page_anchors_exist 管，章号匹配由
        test_numbered_section_links_point_to_the_same_chapter 管——但
        「标签写着 §6.5、锚点却落在 6.3」这一类**权威性硬伤**此前没人管：
        读者按标签跳过去看到的是另一节，查证时先怀疑的是自己。审计时
        全书 217 个小节号链接零错标，这条护栏负责让它在 218 也继续成立。
        """
        headings = {}
        for p in self.pages:
            current = None
            page_map = {}
            for line in p.read_text(encoding='utf-8').split('\n'):
                m = re.match(r'<a id="([^"]+)"></a>', line)
                if m:
                    current = m.group(1)
                    continue
                h = re.match(r'#{2,4} (.+)', line)
                if h and current:
                    page_map[current] = h.group(1)
                    current = None
            headings[p.name] = page_map
        checked, mismatches = 0, []
        for p in self.pages:
            for label, target, anchor in self.SECTION_LABEL.findall(
                    p.read_text(encoding='utf-8')):
                fname = target or p.name
                head = headings.get(fname, {}).get(anchor)
                if head is None:
                    continue          # 无显式锚点的小节（如 §3.5）落章首，另有人管
                checked += 1
                if not head.startswith(label):
                    mismatches.append(f'{p.name}: [§{label}] → {fname}#{anchor} 实为「{head[:30]}」')
        self.assertGreater(checked, 180, f'只对账了 {checked} 个链接——扫描器瞎了')
        self.assertEqual([], mismatches, '小节号标签与落点不符：\n' + '\n'.join(mismatches[:10]))

    PICK_ITEMS = re.compile(r'<a id="(pick-[a-z]+)"></a>.*?\[速查表·[^\]]*\]\(p0-08-cheatsheet\.md#([a-z]+)\)')

    def test_picks_items_link_to_cheatsheet_section(self):
        """必读精选每条必须带行级锚点 + 速查表直达链接，且目标段存在。"""
        picks = (DOCS / 'p0-05-picks.md').read_text(encoding='utf-8')
        sheet = (DOCS / 'p0-08-cheatsheet.md').read_text(encoding='utf-8')
        items = self.PICK_ITEMS.findall(picks)
        self.assertEqual(6, len(items), '精选共 6 条，每条都要有 <a id="pick-*"> 行级锚点和速查表链接')
        for anchor, sec in items:
            with self.subTest(pick=anchor):
                self.assertIn(f'<a id="{sec}"></a>', sheet, f'速查表缺段：{sec}')

    def test_cheatsheet_sections_link_back_to_picks_symmetrically(self):
        """速查表段的 ★ 回链与精选条的速查表正链必须互指 —— 只改一侧（映射漂移）即红。"""
        sheet = (DOCS / 'p0-08-cheatsheet.md').read_text(encoding='utf-8')
        picks = (DOCS / 'p0-05-picks.md').read_text(encoding='utf-8')
        forward = dict()
        for anchor, sec in self.PICK_ITEMS.findall(picks):
            forward[sec] = anchor
        self.assertEqual(6, len(forward), '正链的 段→条 映射塌缩——两条精选指向了同一段')
        actual = dict()
        for sid, body in re.findall(r'<a id="([a-z]+)"></a>\n### [^\n]+\n(.*?)(?=\n<a id="|\n本页与|\Z)', sheet, re.S):
            m = re.search(r'★ \[[^\]]*\]\(p0-05-picks\.md#(pick-[a-z]+)\)', body)
            if m:
                self.assertIn(f'<a id="{m.group(1)}"></a>', picks, f'{sid} 的回链锚点在精选页不存在')
                actual[sid] = m.group(1)
        self.assertEqual(forward, actual, '精选 ↔ 速查表映射不对称（一侧改了另一侧没跟）')

    def test_learning_path_cards_link_to_cheatsheet_sections(self):
        """首页三条路线卡各带「顺手算」速查表出口，指向的段必须存在。"""
        index = (DOCS / 'index.md').read_text(encoding='utf-8')
        sheet = (DOCS / 'p0-08-cheatsheet.md').read_text(encoding='utf-8')
        cards = re.findall(r'<div class="learning-path"[^\n]*\n\n(.*?)\n</div>', index, re.S)
        self.assertEqual(3, len(cards), '首页路线卡不是 3 张——解析瞎了')
        for i, body in enumerate(cards, 1):
            with self.subTest(card=i):
                secs = re.findall(r'\(p0-08-cheatsheet\.md#([a-z]+)\)', body)
                self.assertTrue(secs, f'路线卡 {i} 缺速查表出口')
                for sec in secs:
                    self.assertIn(f'<a id="{sec}"></a>', sheet, f'路线卡 {i} 指向缺段 {sec}')

    def test_changelog_quick_view_jumps_resolve(self):
        """更新日志「系列速览」必须真能跳：每个 (#锚点) 都落在本页的 <a id> 上。"""
        page = (DOCS / 'p9-12-changelog.md').read_text(encoding='utf-8')
        jumps = re.findall(r'\]\(#([^)]+)\)', page)
        self.assertGreaterEqual(len(jumps), 8, '速览至少覆盖 8 个系列组——速览表塌了就是护栏瞎了')
        ids = set(ANCHOR_DEF.findall(page))
        missing = sorted({j for j in jumps if j not in ids})
        self.assertEqual([], missing, f'速览跳转缺少锚点：{missing}')

    def test_changelog_series_groups_hold_every_version(self):
        """每个版本行必须恰好落在一个系列组里；速览与组标题的条数必须等于实际行数。

        发版仪式新增版本行时，速览条数、组标题条数、组范围都要跟着动——
        这一条把「忘了同步」直接变红，而不是让速览悄悄说谎。
        """
        page = (DOCS / 'p9-12-changelog.md').read_text(encoding='utf-8')
        version_row = re.compile(r'^\| \**v\d', re.M)
        parts = re.split(r'^<a id="(log-[\w\-]+)"></a>$', page, flags=re.M)
        groups = list(zip(parts[1::2], parts[2::2]))
        self.assertGreaterEqual(len(groups), 8, '系列组塌回单表——分组本身被删了')
        self.assertEqual([], version_row.findall(parts[0]), '第一组之前不允许出现版本行')
        counts, covered = {}, []
        for anchor, body in groups:
            rows = version_row.findall(body)
            self.assertTrue(rows, f'组 {anchor} 里没有版本行')
            title = re.search(r'(?m)^### .+（(\d+) 条）', body)
            self.assertIsNotNone(title, f'组 {anchor} 缺带条数的标题（右侧目录会瞎）')
            self.assertEqual(int(title.group(1)), len(rows), f'组 {anchor} 标题条数与实际行数不符')
            versions = re.findall(r'^\| \**(v\d+(?:\.\d+)+)', body, re.M)
            bounds = sorted(versions, key=lambda version: tuple(map(int, version[1:].split('.'))))
            expected_range = (bounds[0], bounds[-1])
            title_range = re.search(r'^### (v[\d.]+) → (v[\d.]+)', body, re.M)
            self.assertIsNotNone(title_range, f'组 {anchor} 缺版本范围')
            self.assertEqual(expected_range, title_range.groups(), f'组 {anchor} 标题范围不符')
            quick_range = re.search(
                rf'\[(v[\d.]+) → (v[\d.]+)\]\(#{re.escape(anchor)}\)', parts[0])
            self.assertIsNotNone(quick_range, f'组 {anchor} 缺速览范围')
            self.assertEqual(expected_range, quick_range.groups(), f'组 {anchor} 速览范围不符')
            counts[anchor] = len(rows)
            covered += rows
        self.assertEqual(covered, version_row.findall(page), '各组行数拼起来必须等于全表、不多不少')
        versions = re.findall(r'^\| \**(v\d+(?:\.\d+)+)', page, re.M)
        self.assertEqual(len(versions), len(set(versions)), '同一版本不能出现在多个系列组中')
        declared = dict((m[0], int(m[1])) for m in
                        re.findall(r'\]\(#(log-[\w\-]+)\) \| [^|]+\| (\d+) \|', page))
        self.assertEqual(declared, counts, '速览的条数与组内实际行数不一致（发版忘同步速览）')

    REMOTE_IMG = re.compile(r'<img[^>]+src="(https?://[^"]+)"')
    ALLOWED_REMOTE_IMG = re.compile(
        r"https://img\.youtube\.com/vi/[\w-]+/[a-z]+\.jpg")
    LOCAL_PHOTO_IMG = re.compile(r'<img[^>]+src="(assets/photos/[^"]+)"')

    def test_only_youtube_thumbnails_may_stay_remote(self):
        bad = []
        for page in self.pages:
            for url in self.REMOTE_IMG.findall(page.read_text(encoding="utf-8")):
                if not self.ALLOWED_REMOTE_IMG.fullmatch(url):
                    bad.append(f"{page.name}: {url}")
        self.assertEqual([], bad,
                         "远程图片必须本地化到 assets/photos/：\n" + "\n".join(bad[:10]))

    def test_local_photo_references_exist(self):
        missing = []
        for page in self.pages:
            for rel in self.LOCAL_PHOTO_IMG.findall(page.read_text(encoding="utf-8")):
                if not (ROOT / rel).is_file():
                    missing.append(f"{page.name}: {rel}")
        self.assertEqual([], missing,
                         "引用了不存在的照片：\n" + "\n".join(missing[:10]))

    def test_credits_page_lists_every_web_photo(self):
        credits = (DOCS / "p9-14-credits.md").read_text(encoding="utf-8")
        photos = sorted(p.name for p in (ROOT / "assets/photos/web").glob("*"))
        missing = [name for name in photos if name not in credits]
        self.assertEqual([], missing, f"来源页漏登记：{missing[:10]}")


if __name__ == "__main__":
    unittest.main()
