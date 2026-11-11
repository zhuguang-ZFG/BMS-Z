"""Regression tests for the 入场诊断 widget (p0-09) on the built site.

Rebuilds in a temp workspace and serves it, mirroring test_reading_journey.py:
the widget must map answer paths to the right route, deep-link to real pages,
and the no-JS fallback table must stay readable.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from site_build_inputs import copy_build_inputs  # noqa: E402


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='analog-diag-')
        cls.addClassCleanup(temporary.cleanup)
        work = Path(temporary.name)
        copy_build_inputs(ROOT, work)
        result = subprocess.run([sys.executable, '-X', 'utf8', 'scripts/build_site.py', '--build'],
                                cwd=work, capture_output=True, text=True, encoding='utf8',
                                errors='replace', timeout=300)
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
        playwright = sync_playwright().start()
        cls.addClassCleanup(playwright.stop)
        cls.browser = playwright.chromium.launch(channel='chrome', headless=True)

    def open_page(self, js=True):
        context = self.browser.new_context(java_script_enabled=js)
        self.addCleanup(context.close)
        page = context.new_page()
        page.on('pageerror', lambda error: self.fail(f'page error: {error}'))
        page.goto(self.base + 'p0-09-diagnostic.html')
        return page

    def answer_all(self, page, picks):
        for index, pick in enumerate(picks):
            expect_card = page.locator('.diag-card')
            self.assertTrue(expect_card.is_enabled(timeout=10000),
                            f'question {index + 1} missing')
            page.locator('.diag-opts .diag-btn').nth(pick).click()
            page.wait_for_timeout(50)

    def result_id(self, page):
        card = page.locator('.diag-result')
        card.wait_for(state='attached', timeout=10000)
        return card.get_attribute('data-diag-result')

    def test_working_engineer_gets_practice_route_with_live_links(self):
        page = self.open_page()
        self.answer_all(page, [3, 2, 2, 2, 3, 2])
        card = page.locator('.diag-result')
        card.wait_for(state='attached', timeout=10000)
        self.assertEqual(card.get_attribute('data-diag-result'), 'practice')
        first = card.locator('ol a').first
        self.assertIn('p3-01-ch14.html#ch14', first.get_attribute('href'))
        first.click()
        page.wait_for_timeout(300)
        # 章标题现在是 h1（标题层级归一），别再用 h2 找。
        self.assertIn('设计方法论', page.locator('h1').first.inner_text())

    def test_zero_basis_time_poor_defaults_to_intuition_route(self):
        page = self.open_page()
        self.answer_all(page, [0] * 6)
        self.assertEqual(self.result_id(page), 'intuition')

    def test_back_button_returns_to_previous_question(self):
        page = self.open_page()
        page.locator('.diag-opts .diag-btn').nth(1).click()
        page.wait_for_timeout(50)
        page.locator('.diag-opts .diag-btn').nth(2).click()
        page.wait_for_timeout(50)
        page.locator('.diag-back').click()
        page.wait_for_timeout(50)
        self.assertEqual(page.locator('.diag-progress').inner_text(), '第 2 / 6 题')

    def test_without_javascript_static_routing_table_remains(self):
        page = self.open_page(js=False)
        rows = page.locator('table tr')
        self.assertGreaterEqual(rows.count(), 5)
        body = page.inner_text('main')
        for route in ('直觉线', '硬件线', '实战线', '深造线'):
            self.assertIn(route, body)

    def test_time_budget_selects_matching_timeline_row(self):
        page = self.open_page()
        self.answer_all(page, [3, 2, 2, 2, 3, 2])  # 每周 6～8 小时 → 一周末档
        href = page.locator('.diag-time a').get_attribute('href')
        self.assertTrue(href.endswith('p0-03-timeline.html#t-week'), href)
        page.goto(self.base + 'p0-09-diagnostic.html')
        self.answer_all(page, [0] * 6)  # 每周不到 1 小时 → 5 分钟档
        href = page.locator('.diag-time a').get_attribute('href')
        self.assertTrue(href.endswith('p0-03-timeline.html#t-min'), href)
        page.goto(self.base + href.split('/')[-1])
        page.wait_for_timeout(300)
        row = page.evaluate("() => document.getElementById('t-min').closest('tr').innerText")
        self.assertIn('5 分钟', row)
        self.assertIn('水路比喻', row)

    CALC_CASES = (
        ('practice', [3, 2, 2, 2, 3, 2], '实战线',
         ('p3-01-ch14.md', 'p4-01-ch16.md')),
        ('deep', [2, 2, 2, 3, 3, 2], '深造线',
         ('p1-05-ch4.md', 'p2-01-ch11.md')),
        ('weekend', [0, 0, 1, 1, 2, 3], '硬件线',
         ('p1-01-ch0.md', 'p1-06-ch5.md')),
        ('intuition', [0] * 6, '直觉线', ('p1-01-ch0.md',)),
    )

    def test_calc_exits_follow_routes_with_and_without_javascript(self):
        """实际答题、重测、无 JS 表格和落地段均遵守章首的公式速查映射。"""
        page = self.open_page()
        static = self.open_page(js=False)
        for route, answers, label, chapters in self.CALC_CASES:
            with self.subTest(route=route):
                expected = []
                for chapter in chapters:
                    source = (ROOT / 'docs' / chapter).read_text(encoding='utf-8')
                    match = re.search(r'^> .*公式速查.*?\((p0-08-cheatsheet\.md#[^)]+)\)',
                                      source, re.M)
                    self.assertIsNotNone(match, chapter)
                    expected.append(match.group(1).replace('.md#', '.html#'))
                self.answer_all(page, answers)
                self.assertEqual(route, self.result_id(page))
                calc = page.locator('.diag-calc a')
                expect(calc).to_have_count(len(expected))
                self.assertEqual(expected, calc.evaluate_all(
                    'links => links.map(a => a.getAttribute("href"))'))
                row = static.locator('.md-content tbody tr').filter(has_text=label)
                expect(row).to_have_count(1)
                fallback = row.locator('td').last.locator('a')
                self.assertEqual(expected, fallback.evaluate_all(
                    'links => links.map(a => a.getAttribute("href"))'))
                for link in calc.all() + fallback.all():
                    expect(link).to_be_visible()
                target = expected[-1].split('#')[1]
                calc.last.click()
                expect(page).to_have_url(self.base + expected[-1])
                heading = page.locator(f'p:has(> #{target}) + h2')
                expect(heading).to_be_visible()
                page.wait_for_function(
                    'id => { const r = document.getElementById(id).getBoundingClientRect(); '
                    'return r.top >= 0 && r.top < innerHeight / 2; }', arg=target)
                page.goto(self.base + 'p0-09-diagnostic.html')
                self.answer_all(page, answers)
                page.get_by_role('button', name='重测一次').click()
                expect(page.locator('.diag-result')).to_have_count(0)
                expect(page.locator('.diag-progress')).to_have_text('第 1 / 6 题')


if __name__ == '__main__':
    unittest.main()
