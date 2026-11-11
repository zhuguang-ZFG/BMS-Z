"""Exercise the built site, including search workers and instant navigation.

Uses a temporary build served under /site/ to catch project-site path mistakes.
All external requests are blocked; no deployed site or external player is needed.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
import threading
import unittest

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from site_build_inputs import copy_build_inputs  # noqa: E402


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args):
        pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # Navigating away cancels in-flight images and search requests.


class ReadingJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='analog-reading-')
        cls.addClassCleanup(temporary.cleanup)
        work = Path(temporary.name)
        copy_build_inputs(ROOT, work)
        result = subprocess.run([sys.executable, '-X', 'utf8', 'scripts/build_site.py', '--build'],
                                cwd=work, capture_output=True, text=True, encoding='utf-8',
                                errors='replace', timeout=180)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        server = ThreadingHTTPServer(('127.0.0.1', 0),
                                     partial(QuietHandler, directory=str(work / 'build')))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def stop_server():
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        cls.addClassCleanup(stop_server)
        cls.base = f'http://127.0.0.1:{server.server_port}/site/'
        # Material only uses instant navigation for URLs in the sitemap.
        # Production-domain entries silently turned these tests into full loads.
        sitemap = work / 'build/site/sitemap.xml'
        sitemap.write_text(sitemap.read_text(encoding='utf-8').replace(
            'https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/', cls.base), encoding='utf-8')
        playwright = sync_playwright().start()
        cls.addClassCleanup(playwright.stop)
        cls.browser = playwright.chromium.launch(channel='chrome', headless=True)
        cls.addClassCleanup(cls.browser.close)

    def setUp(self):
        self.errors = []
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 900})
        self.addCleanup(self.context.close)
        self.context.route('**/*', lambda route: route.continue_()
                           if route.request.url.startswith(self.base) else route.abort())
        self.page = self.context.new_page()
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.assertEqual([], self.errors)

    def test_homepage_start_takes_the_reader_to_chapter_zero(self):
        self.page.goto(self.base)
        expect(self.page.locator('.learning-path')).to_have_count(3)
        expect(self.page.locator('.learning-lesson')).to_have_count(3)
        start = self.page.get_by_role('link', name='从第 0 章开始 →', exact=True)
        expect(start).to_be_in_viewport()
        start.click()
        expect(self.page).to_have_url(self.base + 'p1-01-ch0.html#ch0')
        # 章标题在站点产物里是 h1（build_site.shift_headings 把 48 个页面的
        # `##` 章标题归一成 `#`），所以锚点后面跟的是 h1 而不是 h2。
        # v3.56 起章页开头被 wrap_chapter_hero 包进 .chapter-hero 舞台，
        # h1 是锚点段兄弟 div 的直接子元素。
        expect(self.page.locator('p:has(> #ch0) + .chapter-hero > h1')).to_contain_text('第 0 章')

    def test_scrolling_and_page_switch_keep_the_link_target_in_the_url(self):
        # 地址只该跟着「去了哪」变，不该跟着「滚到哪一段」变。
        # Material 的 navigation.tracking 会在滚动约 250ms 后把当前目录项
        # replaceState 进 URL，而 navigation.instant 换页时又会把**上一页** URL
        # 上的哈希搬进新页 —— 两个叠起来，从滚动过的首页点进第 0 章会落地成
        # p1-01-ch0.html#_2 或干脆丢掉片段：`_2` 是首页自动生成的标题 id，
        # 章节页根本没有它，复制出去只会让读者回到页首。
        # test_dashboard_keeps_expanded_sections… 在 CI 上的间歇性红就是这个；
        # 重新打开 navigation.tracking，这里第一段断言就会稳定红。
        self.page.goto(self.base)
        self.page.locator('.learning-chapters summary').click()
        chapter_link = self.page.locator('.learning-chapters a').first
        expect(chapter_link).to_be_visible()
        self.page.wait_for_timeout(1500)  # 越过 tracking 的 250ms 节流窗
        expect(self.page).to_have_url(self.base)
        chapter_link.click()
        self.page.wait_for_timeout(1500)
        expect(self.page).to_have_url(self.base + 'p1-01-ch0.html#ch0')

    def test_chapter_quiz_review_and_next_chapter_form_a_round_trip(self):
        self.page.goto(self.base + 'p1-07-ch6.html#ch6')
        self.page.evaluate('window.readingJourneyMarker = true')
        self.page.get_by_role('link', name='做第 6 章自测 →', exact=True).click()
        expect(self.page).to_have_url(self.base + 'p9-00-quiz.html#quiz-ch6')
        expect(self.page.locator('p:has(> #quiz-ch6) + h2')).to_contain_text('第 6 章')
        self.page.get_by_role('link', name='← 返回第 6 章复习', exact=True).click()
        expect(self.page).to_have_url(self.base + 'p1-07-ch6.html#ch6')
        expect(self.page.locator('.reading-nav')).to_have_count(1)
        self.page.locator('.reading-nav a').last.click()
        expect(self.page).to_have_url(self.base + 'p1-08-ch7.html#ch7')
        self.assertTrue(self.page.evaluate('window.readingJourneyMarker === true'), 'Must use instant navigation')

    def assert_math_rendered(self):
        # 即时导航**先改地址、再换正文**：6× CPU 节流下点同一个速查出口，6 次里 4 次看到
        # URL 已经是 p0-08-cheatsheet.html#outstage，正文标题却还是「入场诊断」、
        # .arithmatex 计数 0。原来这里只等到「地址变了 + startup.promise 在」就断言，
        # 把「正文还没换过来」读成「公式没排版」——CI 上这条间歇性红就是这么来的
        # （改动前的同一提交原样重跑 CI 也复现，见 v3.55.2）。同步点挪到被测对象本身：
        # 先等公式真的排进当前正文，断言一条不减；真没排版时仍由下面的断言报出可读的错。
        try:
            self.page.wait_for_function(
                '() => document.querySelector(".arithmatex mjx-container")', timeout=15000)
        except PlaywrightTimeoutError:
            pass
        self.page.wait_for_function('window.MathJax && MathJax.startup && MathJax.startup.promise')
        self.page.evaluate('MathJax.startup.promise')
        self.assertGreater(self.page.locator('.arithmatex').count(), 0)
        expect(self.page.locator('.arithmatex:not(:has(mjx-container))')).to_have_count(0)
        expect(self.page.locator('mjx-merror, .math-status')).to_have_count(0)

    def test_actual_mathjax_renders_after_instant_navigation_and_back(self):
        self.page.goto(self.base + 'p1-01-ch0.html#ch0')
        self.assert_math_rendered()
        self.page.evaluate('window.mathJourneyMarker = true')
        self.page.locator('.reading-nav a').last.click()
        expect(self.page).to_have_url(self.base + 'p1-02-ch1.html#ch1')
        self.assertTrue(self.page.evaluate('window.mathJourneyMarker === true'))
        self.assert_math_rendered()
        self.page.go_back()
        expect(self.page).to_have_url(self.base + 'p1-01-ch0.html#ch0')
        self.assert_math_rendered()
        self.page.reload()
        self.assert_math_rendered()

    def test_mathjax_starting_after_navigation_typesets_the_current_page(self):
        held = []
        self.page.route('**/tex-chtml-full.js', lambda route: held.append(route))
        self.page.goto(self.base + 'p1-01-ch0.html#ch0', wait_until='commit')
        expect(self.page.locator('.reading-nav')).to_be_visible()
        self.page.evaluate('window.mathJourneyMarker = true')
        self.page.locator('.reading-nav a').last.click(no_wait_after=True)
        expect(self.page).to_have_url(self.base + 'p1-02-ch1.html#ch1')
        self.assertTrue(self.page.evaluate('window.mathJourneyMarker === true'))
        self.assertEqual(1, len(held))
        held[0].continue_()
        self.assert_math_rendered()

    def test_mobile_formula_exit_keeps_glyphs_and_anchor_after_back(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.page.goto(self.base + 'p0-08-cheatsheet.html')
        self.assert_math_rendered()
        self.page.evaluate('document.fonts.ready')
        glyphs = "nodes => nodes.map(node => [node.className, getComputedStyle(node, '::before').content])"
        expected_glyphs = self.page.locator('mjx-c').evaluate_all(glyphs)
        self.page.goto(self.base + 'p0-09-diagnostic.html')
        self.page.evaluate('MathJax.startup.promise')
        self.page.evaluate('window.mathJourneyMarker = true')
        for _ in range(3):
            row = self.page.locator('.md-content tbody tr').filter(has_text='硬件线')
            row.get_by_role('link', name='输出级', exact=True).click()
            expect(self.page).to_have_url(self.base + 'p0-08-cheatsheet.html#outstage')
            self.assertTrue(self.page.evaluate('window.mathJourneyMarker === true'))
            self.assert_math_rendered()
            self.page.evaluate('document.fonts.ready')
            actual_glyphs = self.page.locator('mjx-c').evaluate_all(glyphs)
            self.assertTrue(expected_glyphs == actual_glyphs,
                            'SPA 换页后的公式字形必须与完整加载一致')
            self.page.wait_for_function(
                "() => { const top = document.getElementById('outstage').getBoundingClientRect().top; "
                "return top >= 0 && top < innerHeight / 2; }")
            self.page.go_back()
            expect(self.page.locator('.diag-progress')).to_have_text('第 1 / 6 题')

    def test_page_titles_and_social_metadata_survive_pre_heading_anchors(self):
        for filename, title in (
            ('p1-00-part1.html', '第一篇：器件深度原理解析'),
            ('p9-00-quiz.html', '第九篇：自测与练习'),
            ('p1-08-ch7.html', '第 7 章 比较器：专为"判决"而生'),
        ):
            with self.subTest(page=filename):
                self.page.goto(self.base + filename)
                self.assertIn(title, self.page.title())
                expect(self.page.locator('meta[property="og:title"]')).to_have_attribute('content', title)
                expect(self.page.locator('meta[name="twitter:title"]')).to_have_attribute('content', title)

    def test_old_bookmarks_redirect_without_losing_queries_or_trapping_back(self):
        for source, target in (
            ('p1-01-ch0.html#ch1', 'p1-02-ch1.html#ch1'),
            ('p4-03-ch18.html#part5', 'p5-00-part5.html#part5'),
            ('p8-08-s8-8.html#sec89', 'p8-09-s8-9.html#sec89'),
            ('index.html#preface', 'p0-01-preface.html#preface'),
        ):
            with self.subTest(source=source):
                self.page.goto(self.base)
                self.page.goto(self.base + source.replace('#', '?from=bookmark#'))
                expect(self.page).to_have_url(self.base + target.replace('#', '?from=bookmark#'))
                self.page.go_back()
                expect(self.page).to_have_url(self.base)

    def test_reading_and_legacy_fallback_work_without_javascript(self):
        context = self.browser.new_context(java_script_enabled=False)
        self.addCleanup(context.close)
        context.route('**/*', lambda route: route.continue_()
                      if route.request.url.startswith(self.base) else route.abort())
        page = context.new_page()
        page.goto(self.base)
        page.get_by_role('link', name='从第 0 章开始 →', exact=True).click()
        expect(page).to_have_url(self.base + 'p1-01-ch0.html#ch0')
        page.get_by_role('link', name='做第 0 章自测 →', exact=True).click()
        expect(page).to_have_url(self.base + 'p9-00-quiz.html#quiz-ch0')
        page.goto(self.base + 'p1-01-ch0.html#ch1')
        fallback = page.locator('.legacy-anchor:target a')
        expect(fallback).to_be_visible()
        fallback.click()
        expect(page).to_have_url(self.base + 'p1-02-ch1.html#ch1')

    def test_home_and_chapter_navigation_fit_mobile_in_both_themes(self):
        for theme in ('light', 'dark'):
            context = self.browser.new_context(color_scheme=theme, reduced_motion='reduce')
            self.addCleanup(context.close)
            context.route('**/*', lambda route: route.continue_()
                          if route.request.url.startswith(self.base) else route.abort())
            page = context.new_page()
            page.on('pageerror', lambda error: self.errors.append(str(error)))
            for width in (360, 390, 1280):
                page.set_viewport_size({'width': width, 'height': 900})
                for path in ('', 'p1-02-ch1.html#ch1'):
                    with self.subTest(theme=theme, width=width, path=path):
                        page.goto(self.base + path)
                        expect(page.locator('body')).to_have_attribute('data-md-color-scheme',
                                                                      'slate' if theme == 'dark' else 'default')
                        self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                        links = page.locator('.reading-nav a' if path else '.learning-actions a')
                        for link in links.all():
                            box = link.bounding_box()
                            assert box is not None, '阅读导航链接没有可见边界'
                            self.assertGreaterEqual(box['height'], 44)
                        links.first.focus()
                        expect(links.first).to_be_focused()
                        if not path:
                            page.locator('.learning-chapters summary').click()
                            expect(page.locator('.learning-chapters a')).to_have_count(19)
                            self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                            for chapter in page.locator('.learning-chapters a').all():
                                box = chapter.bounding_box()
                                assert box is not None, '章节链接没有可见边界'
                                self.assertGreaterEqual(box['height'], 44)

    def test_real_search_returns_relevant_chinese_and_model_number_results(self):
        self.page.goto(self.base)
        search = self.page.locator('input[data-md-component="search-query"]')
        search.click()
        for query, expected_page in (
            # 2026-11：search worker 切分补丁（build_site.patch_search_worker）让整词
            # 「去耦电容」成为真实词元后，榜首是动画画廊页——它聚合了 EP08 去耦 demo
            # 卡与章节映射行，是站内「去耦电容」最密的自然落点；正典正文仍看 ch1。
            ('去耦电容', 'p5-00-part5.html'),
            # v3.81：ch12 新增相位裕度波特图与 §12.9 实测段后，该主题的正典章节
            # 从 ch11（11.5/11.11 两处提及）移到 ch12（五个密集小节），搜索榜首随之迁移。
            ('相位裕度', 'p2-02-ch12.html'),
            ('LM358', 'p1-07-ch6.html'),
        ):
            with self.subTest(query=query):
                # Playwright inserts non-Latin text without keyup. Material's
                # query observer listens to keyup (not input), so finish the
                # input with a real, non-editing key rather than depending on
                # the worker-ready event happening after text insertion.
                search.fill(query)
                search.press('End')
                expect(search).to_have_value(query)
                result = self.page.locator('.md-search-result__link[href*="' + expected_page + '"]')
                expect(result.first).to_be_visible(timeout=15000)
        search.fill('zzzxqv987654')
        search.press('End')
        expect(self.page.locator('.md-search-result__meta')).to_contain_text('没有找到')

    def test_chapter_completion_and_resume_survive_reload_and_can_be_undone(self):
        self.page.goto(self.base + 'p1-02-ch1.html#rc-study')
        complete = self.page.locator('.chapter-done-button')
        expect(complete).to_have_attribute('aria-pressed', 'false')
        complete.click()
        expect(complete).to_have_attribute('aria-pressed', 'true')
        self.page.reload()
        expect(self.page.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'true')
        self.page.goto(self.base)
        expect(self.page.locator('.learning-dashboard')).to_contain_text('已完成 1 / 19 章')
        self.page.locator('.learning-chapters summary').click()
        expect(self.page.locator('.learning-chapter-status[data-chapter="ch1"]')).to_have_text('已完成')
        expect(self.page.locator('.learning-chapter-status[data-done="false"]')).to_have_count(18)
        resume = self.page.locator('.learning-resume')
        expect(resume).to_contain_text('第 1 章')
        resume.click()
        self.assertIn('p1-02-ch1.html', self.page.url)
        expect(self.page.locator('.chapter-done-button')).to_have_count(1)
        self.page.locator('.chapter-done-button').click()
        expect(self.page.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'false')

    def test_question_bookmarks_are_independent_stable_and_survive_navigation(self):
        self.page.goto(self.base + 'p9-00-quiz.html#q-ch0-01')
        expect(self.page.locator('.question-bookmark')).to_have_count(124)
        first = self.page.locator('.question-bookmark[data-question="q-ch0-01"]')
        extra = self.page.locator('.question-bookmark[data-question="q-extra-26"]')
        first.click()
        extra.click()
        self.page.reload()
        expect(first).to_have_attribute('aria-pressed', 'true')
        expect(extra).to_have_attribute('aria-pressed', 'true')
        self.page.goto(self.base)
        self.page.locator('.learning-bookmarks summary').click()
        expect(self.page.locator('.learning-bookmarks a')).to_have_count(2)
        self.page.locator('.learning-dashboard a[href$="#q-ch0-01"]').click()
        expect(self.page).to_have_url(self.base + 'p9-00-quiz.html#q-ch0-01')
        self.page.locator('.question-bookmark[data-question="q-ch0-01"]').click()
        expect(self.page.locator('.question-bookmark[data-question="q-extra-26"]')).to_have_attribute('aria-pressed', 'true')

    def test_corrupt_or_unavailable_storage_does_not_break_reading(self):
        self.page.add_init_script("localStorage.setItem('analog-learning:v1:/site/', '{broken');")
        self.page.goto(self.base + 'p1-01-ch0.html#ch0')
        expect(self.page.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'false')
        self.page.locator('.chapter-done-button').click()
        expect(self.page.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'true')
        context = self.browser.new_context()
        self.addCleanup(context.close)
        context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(self.base) else route.abort())
        context.add_init_script("""for (const method of ['getItem', 'setItem']) {
          const original = Storage.prototype[method];
          Storage.prototype[method] = function(key, ...args) {
            if (key.startsWith('analog-learning:')) throw new DOMException('Blocked', 'SecurityError');
            return original.call(this, key, ...args);
          };
        }""")
        page = context.new_page()
        page.on('pageerror', lambda error: self.errors.append(str(error)))
        page.goto(self.base + 'p1-01-ch0.html#ch0')
        page.locator('.chapter-done-button').click()
        expect(page.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'true')
        expect(page.locator('.learning-storage-note')).to_contain_text('仅临时保留')

    def test_tabs_save_independent_actions_before_storage_events_arrive(self):
        self.page.goto(self.base + 'p1-01-ch0.html#ch0')
        with self.page.expect_popup() as opened:
            self.page.evaluate("url => { window.studyTab = window.open(url); }",
                               self.base + 'p9-00-quiz.html#q-ch0-01')
        other = opened.value
        other.on('pageerror', lambda error: self.errors.append(str(error)))
        expect(other.locator('.question-bookmark')).to_have_count(124)
        # Both clicks happen in one task, before either page can process the
        # asynchronous storage event from the other page's write.
        self.page.evaluate("""() => {
          studyTab.document.querySelector('[data-question="q-ch0-01"]').click();
          document.querySelector('.chapter-done-button').click();
        }""")
        expect(self.page.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'true')
        expect(other.locator('[data-question="q-ch0-01"]')).to_have_attribute('aria-pressed', 'true')
        # Removing independent records must not resurrect the other tab's
        # removal while its storage event is still queued.
        self.page.evaluate("""() => {
          studyTab.document.querySelector('[data-question="q-ch0-01"]').click();
          document.querySelector('.chapter-done-button').click();
        }""")
        expect(self.page.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'false')
        expect(other.locator('[data-question="q-ch0-01"]')).to_have_attribute('aria-pressed', 'false')
        self.page.reload()
        other.reload()
        expect(self.page.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'false')
        expect(other.locator('[data-question="q-ch0-01"]')).to_have_attribute('aria-pressed', 'false')

    def test_two_tabs_marking_the_same_chapter_do_not_undo_each_other(self):
        self.page.goto(self.base + 'p1-01-ch0.html#ch0')
        with self.page.expect_popup() as opened:
            self.page.evaluate("url => { window.studyTab = window.open(url); }", self.page.url)
        other = opened.value
        other.on('pageerror', lambda error: self.errors.append(str(error)))
        expect(other.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'false')
        self.page.evaluate("""() => {
          studyTab.document.querySelector('.chapter-done-button').click();
          document.querySelector('.chapter-done-button').click();
        }""")
        for page in (self.page, other):
            expect(page.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'true')
            page.reload()
            expect(page.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'true')

    def test_dashboard_keeps_expanded_sections_and_keyboard_focus_on_tab_updates(self):
        self.page.goto(self.base)
        expect(self.page.locator('.learning-resume')).to_be_hidden()
        other = self.context.new_page()
        other.on('pageerror', lambda error: self.errors.append(str(error)))
        other.goto(self.base + 'p1-01-ch0.html#ch0')
        expect(other.locator('.chapter-done-button')).to_be_visible()
        chapter_summary = self.page.locator('.learning-chapters summary')
        chapter_summary.click()
        self.page.locator('.learning-bookmarks summary').click()
        chapter_link = self.page.locator('.learning-chapters a').first
        chapter_link.focus()
        other.locator('.chapter-done-button').click()
        expect(self.page.locator('.learning-chapter-status[data-chapter="ch0"]')).to_have_text('已完成')
        expect(chapter_link).to_be_focused()
        for selector in ('.learning-chapters', '.learning-bookmarks'):
            expect(self.page.locator(selector)).to_have_attribute('open', '')
        chapter_link.click()
        expect(self.page).to_have_url(self.base + 'p1-01-ch0.html#ch0')
        self.page.locator('.chapter-done-button').click()
        self.page.goto(self.base)
        expect(self.page.locator('.learning-chapter-status[data-chapter="ch0"]')).to_have_text('未完成')

    def test_write_only_storage_failure_keeps_multiple_temporary_bookmarks(self):
        self.page.add_init_script("""window.failLearningWrites = true;
          const original = Storage.prototype.setItem;
          Storage.prototype.setItem = function(key, value) {
            if (window.failLearningWrites && key.startsWith('analog-learning:'))
              throw new DOMException('Full', 'QuotaExceededError');
            return original.call(this, key, value);
          };""")
        self.page.goto(self.base + 'p9-00-quiz.html#q-ch0-01')
        first = self.page.locator('[data-question="q-ch0-01"]')
        extra = self.page.locator('[data-question="q-extra-26"]')
        first.click()
        expect(first).to_have_attribute('aria-pressed', 'true')
        extra.click()
        expect(extra).to_have_attribute('aria-pressed', 'true')
        expect(first).to_have_attribute('aria-pressed', 'true')
        first.click()
        expect(first).to_have_attribute('aria-pressed', 'false')
        expect(extra).to_have_attribute('aria-pressed', 'true')
        expect(self.page.locator('.quiz-storage-note')).to_contain_text('仅临时保留')
        self.page.evaluate('window.failLearningWrites = false')
        first.click()
        expect(self.page.locator('.quiz-storage-note')).not_to_contain_text('仅临时保留')
        self.page.reload()
        expect(first).to_have_attribute('aria-pressed', 'true')
        expect(extra).to_have_attribute('aria-pressed', 'true')

    def test_legacy_records_survive_upgrade_and_removals_survive_reload(self):
        self.page.goto(self.base)
        self.page.evaluate("""() => localStorage.setItem('analog-learning:v1:/site/', JSON.stringify({
          version: 1, completed: ['ch0', 'ch0', 'unknown'], bookmarks: ['q-ch0-01'],
          last: {chapter: 'ch0', anchor: 'ch0'}
        }))""")
        self.page.reload()
        expect(self.page.locator('.learning-count')).to_have_text('已完成 1 / 19 章')
        expect(self.page.locator('.learning-bookmarks summary')).to_have_text('错题收藏（1）')
        self.page.locator('.learning-resume').click()
        self.page.locator('.chapter-done-button').click()
        self.page.reload()
        expect(self.page.locator('.chapter-done-button')).to_have_attribute('aria-pressed', 'false')
        self.page.goto(self.base + 'p9-00-quiz.html#q-ch0-01')
        mark = self.page.locator('[data-question="q-ch0-01"]')
        expect(mark).to_have_attribute('aria-pressed', 'true')
        mark.click()
        self.page.reload()
        expect(mark).to_have_attribute('aria-pressed', 'false')
        self.page.goto(self.base)
        expect(self.page.locator('.learning-count')).to_have_text('已完成 0 / 19 章')
        expect(self.page.locator('.learning-bookmarks summary')).to_have_text('错题收藏（0）')


    def test_downloadable_labs_are_served_under_the_project_subpath(self):
        self.page.goto(self.base + 'p8-03-s8-3.html#lab-rc')
        for lab in ('rc', 'mosfet', 'lm358'):
            link = self.page.locator(f'.md-content a[href$="assets/labs/{lab}-lab.zip"]')
            expect(link).to_have_count(1)
            response = self.context.request.get(link.evaluate('el => el.href'))
            self.assertEqual(200, response.status)
            self.assertTrue(response.body().startswith(b'PK'))

    def test_export_and_import_merge_progress_without_overwriting_existing_records(self):
        self.page.goto(self.base + 'p1-01-ch0.html#ch0')
        self.page.locator('.chapter-done-button').click()
        self.page.goto(self.base + 'p9-00-quiz.html#q-ch0-01')
        self.page.locator('[data-question="q-ch0-01"]').click()
        self.page.goto(self.base)
        with self.page.expect_download() as download:
            self.page.get_by_role('button', name='导出学习记录', exact=True).click()
        payload = json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
        self.assertEqual('analog-circuit-learning', payload['format'])
        self.assertEqual(['ch0'], payload['completed'])
        self.assertEqual(['q-ch0-01'], payload['bookmarks'])
        self.page.evaluate('localStorage.clear()')
        self.page.goto(self.base + 'p1-02-ch1.html#ch1')
        self.page.locator('.chapter-done-button').click()
        self.page.goto(self.base)
        resume = self.page.locator('.learning-resume').get_attribute('href')
        assert resume is not None, '继续阅读链接缺少 href'
        payload['completed'] += ['unknown', 'ch0']
        payload['title'] = '<img src=x onerror=alert(1)>'
        payload['url'] = 'https://example.invalid/'
        for _ in range(2):
            self.page.get_by_label('选择学习记录文件').set_input_files({
                'name': 'learning.json', 'mimeType': 'application/json',
                'buffer': json.dumps(payload).encode()})
            expect(self.page.locator('.learning-backup-message')).to_contain_text('记录已合并')
        expect(self.page.locator('.learning-count')).to_have_text('已完成 2 / 19 章')
        expect(self.page.locator('.learning-bookmarks summary')).to_have_text('错题收藏（1）')
        expect(self.page.locator('.learning-resume')).to_have_attribute('href', resume)
        expect(self.page.locator('.learning-dashboard img')).to_have_count(0)
        self.page.reload()
        expect(self.page.locator('.learning-count')).to_have_text('已完成 2 / 19 章')
        expect(self.page.locator('.learning-bookmarks summary')).to_have_text('错题收藏（1）')

    def test_invalid_or_oversized_import_does_not_change_learning_records(self):
        self.page.goto(self.base + 'p1-01-ch0.html#ch0')
        self.page.locator('.chapter-done-button').click()
        self.page.goto(self.base)
        for body in (b'{broken', json.dumps({'format': 'analog-circuit-learning', 'version': 2,
                     'completed': [], 'bookmarks': [], 'last': None}).encode(),
                     json.dumps({'format': 'analog-circuit-learning', 'version': 1,
                     'completed': ['ch1'], 'bookmarks': [None], 'last': None}).encode()):
            self.page.get_by_label('选择学习记录文件').set_input_files({
                'name': 'invalid.json', 'mimeType': 'application/json', 'buffer': body})
            expect(self.page.locator('.learning-backup-message')).to_contain_text('无法导入')
            expect(self.page.locator('.learning-count')).to_have_text('已完成 1 / 19 章')
        self.page.get_by_label('选择学习记录文件').set_input_files({
            'name': 'large.json', 'mimeType': 'application/json', 'buffer': b' ' * (256 * 1024 + 1)})
        expect(self.page.locator('.learning-backup-message')).to_contain_text('文件过大')
        self.page.reload()
        expect(self.page.locator('.learning-count')).to_have_text('已完成 1 / 19 章')

    def test_unsaved_records_can_be_exported_after_instant_navigation(self):
        self.context.add_init_script("""const original = Storage.prototype.setItem;
          Storage.prototype.setItem = function(key, value) {
            if (key.startsWith('analog-learning:')) throw new DOMException('Full', 'QuotaExceededError');
            return original.call(this, key, value);
          };""")
        self.page.goto(self.base + 'p1-01-ch0.html#ch0')
        self.page.locator('.chapter-done-button').click()
        self.page.locator('.reading-nav a').first.click()
        expect(self.page.locator('.learning-count')).to_have_text('已完成 1 / 19 章')
        with self.page.expect_download() as download:
            self.page.get_by_role('button', name='导出学习记录', exact=True).click()
        payload = json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
        self.assertEqual(['ch0'], payload['completed'])

    def test_quiz_review_targets_the_section_and_source_lists_render_as_lists(self):
        self.page.goto(self.base + 'p9-00-quiz.html#q-ch12-03')
        self.assert_math_rendered()
        # md_in_html consumes this attribute. If it survives, the block was
        # not parsed and the browser may be silently repairing invalid HTML.
        expect(self.page.locator('.md-content details[markdown]')).to_have_count(0)
        answer = self.page.locator('li:has(a#q-ch12-03) details')
        answer.locator('summary').click()
        answer.get_by_role('link', name='12.9', exact=True).click()
        expect(self.page).to_have_url(self.base + 'p2-02-ch12.html#sec129')
        # §12.9 是 `###`，归一后升一级变 h2（见 test_page_structure.py）。
        expect(self.page.locator('p:has(> #sec129) + h2')).to_contain_text('12.9 容性负载')
        self.page.goto(self.base + 'p1-01-ch0.html#ch0')
        item = self.page.locator('.md-content li').filter(has_text='实验室电源')
        expect(item).to_have_count(1)
        expect(item.locator('xpath=..').locator(':scope > li')).to_have_count(3)

    def test_changelog_prints_one_page_per_series_group(self):
        """打印介质下，更新日志的 8 个系列组标题必须各自另起一页。

        分页范围靠该页独有的 #log-v345 用 :has() 圈定 —— 光断言 changelog 页
        是红的半边：规则若写成全局 h2，首页/章节页会被拆得满地碎片而这里全绿。
        所以第二条断言盯着运放章节页（13 个小节 h2、与任何分组都无关）：它们在打印下必须还是 auto。
        """
        self.page.goto(self.base + 'p9-12-changelog.html')
        expect(self.page.locator('.md-content h2')).to_have_count(8)
        self.page.emulate_media(media='print')
        breaks = self.page.eval_on_selector_all(
            '.md-content h2', 'els => els.map(e => getComputedStyle(e).breakBefore)')
        self.assertEqual(['page'] * 8, breaks, '更新日志打印分页没生效')
        self.page.goto(self.base + 'p2-02-ch12.html')
        self.page.emulate_media(media='print')
        other = self.page.eval_on_selector_all(
            '.md-content h2', 'els => [...new Set(els.map(e => getComputedStyle(e).breakBefore))]')
        self.assertEqual(['auto'], other, '打印分页范围泄漏：章节页的 h2 也被拆页了')

    def test_picks_print_without_a_trailing_blank_page(self):
        self.page.goto(self.base + 'p0-05-picks.html')
        expect(self.page.locator('.md-content ol > li')).to_have_count(6)
        self.page.evaluate('() => document.fonts.ready')
        pdf = self.page.pdf(format='A4', margin={'top': '12mm', 'bottom': '12mm'})
        # Chromium serializes each page as a /Type /Page object; exclude /Pages.
        self.assertEqual(1, len(re.findall(rb'/Type\s*/Page\b', pdf)),
                         '六条精选之后不应多打一张空白页')

    def test_print_paging_covers_cheatsheet_sections_and_quiz_chapters(self):
        """速查表的 16 个场景、题库的 19 章及专题组分别另起一页。

        长组允许自然续页；诊断页不在分页范围内，h2 必须仍为 auto。
        """
        self.page.goto(self.base + 'p0-08-cheatsheet.html')
        expect(self.page.locator('.md-content h2')).to_have_count(16)
        self.page.emulate_media(media='print')
        breaks = self.page.eval_on_selector_all(
            '.md-content h2', 'els => els.map(e => getComputedStyle(e).breakBefore)')
        self.assertEqual(['page'] * 16, breaks, '速查表打印分页没生效')
        self.page.goto(self.base + 'p9-00-quiz.html')
        expect(self.page.locator('.md-content h2')).to_have_count(20)
        self.page.emulate_media(media='print')
        breaks = self.page.eval_on_selector_all(
            '.md-content h2', 'els => els.map(e => getComputedStyle(e).breakBefore)')
        self.assertEqual(['page'] * 20, breaks, '题库打印分页没生效')
        self.page.goto(self.base + 'p0-09-diagnostic.html')
        self.page.emulate_media(media='print')
        breaks = self.page.eval_on_selector_all(
            '.md-content h2', 'els => [...new Set(els.map(e => getComputedStyle(e).breakBefore))]')
        self.assertEqual(['auto'], breaks, '打印分页蔓延到了没有分组结构的页面')

    def test_route_cards_on_the_homepage_offer_a_cheatsheet_exit(self):
        """三条路线卡的「顺手算」链接必须真的落到速查表的段上（SPA 换页 + 锚点落地）。"""
        self.page.goto(self.base)
        card = self.page.locator('.learning-path').first
        card.get_by_role('link', name='无源与频域').click()
        expect(self.page).to_have_url(self.base + 'p0-08-cheatsheet.html#passive')
        expect(self.page.locator('p:has(> #passive) + h2')).to_contain_text('无源元件')


if __name__ == '__main__':
    unittest.main()
