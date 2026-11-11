"""「就地算」互动计算器的浏览器回归（v3.58）。

每个型号的默认值 = 正文算例的原数，这条铁律在这里变成红灯：加载章节页、
不碰输入，输出必须与正文「算一笔」里的数一致；再拨一次参数验证教学点
（负载越轻塌得越少、×10 档救回带宽）。计算器是教学承诺的一部分——
书上算例和屏上计算器对不上，比没有计算器更糟。
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from site_build_inputs import copy_build_inputs  # noqa: E402


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def read_outputs(page):
    """把当前计算器的结果读成 {label: float}。"""
    return page.evaluate("""() => {
      const out = {};
      document.querySelectorAll('.calc .calc-out').forEach(chip => {
        const value = parseFloat(chip.querySelector('b').textContent);
        const label = chip.querySelector('.calc-out-label').textContent.trim();
        out[label] = value;
      });
      return out;
    }""")


class CalcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='analog-calc-')
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

    @classmethod
    def tearDownClass(cls):
        cls.browser.close

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

    def open(self, path, calc):
        self.page.goto(self.base + path)
        box = self.page.locator(f'.calc[data-calc="{calc}"] .calc-box')
        box.wait_for(state='visible')
        return box

    def test_divider_defaults_match_the_book_example(self):
        """§0.3：10V ÷ 10k/10k 接 10k 负载 → 空载 5V、带载 3.33V、塌 33%。"""
        self.open('p1-01-ch0.html', 'divider')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['空载输出'], 5.0, delta=0.01)
        self.assertAlmostEqual(out['带载输出'], 3.33, delta=0.01)
        self.assertAlmostEqual(out['塌陷'], 33.3, delta=0.2)

    def test_divider_lighter_load_collapses_less(self):
        """教学点：负载阻抗 ≫ R2 时几乎不塌——RL 提到 1MΩ，塌陷 ≤1%。"""
        box = self.open('p1-01-ch0.html', 'divider')
        box.locator('input').nth(3).fill('1000')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['带载输出'], 4.98, delta=0.02)
        self.assertLessEqual(out['塌陷'], 1.0)

    def test_electrolyte_life_matches_the_book_example(self):
        """§1.7：105℃/2000h 的电解在 65℃ → 32000h ≈ 3.7 年。"""
        self.open('p1-02-ch1.html', 'electrolyte')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['预期寿命'], 32000, delta=1)
        self.assertAlmostEqual(out['约合'], 3.7, delta=0.05)

    def test_hysteresis_window_matches_the_book_example(self):
        """§7.3：R2/R1=100、摆幅 10V → 窗口 100mV。"""
        self.open('p1-08-ch7.html', 'hysteresis')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['窗口 ΔV'], 0.100, delta=0.001)
        self.assertAlmostEqual(out['上门槛 VTH+'], 2.515, delta=0.01)
        self.assertAlmostEqual(out['下门槛 VTH−'], 2.415, delta=0.01)

    def test_probe_modes_match_the_book_example(self):
        """§16.3：100kΩ 源阻 ×1 → 误差 9%、截止 16kHz；×10 → 1%、159kHz。"""
        self.open('p4-01-ch16.html', 'probe')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['分压系数'], 0.909, delta=0.001)
        self.assertAlmostEqual(out['幅度误差'], 9.1, delta=0.1)
        self.assertAlmostEqual(out['带宽截止'], 15.9, delta=0.2)
        self.page.locator('.calc[data-calc="probe"] select').select_option('x10')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['幅度误差'], 1.0, delta=0.1)
        self.assertAlmostEqual(out['带宽截止'], 159.2, delta=0.5)

    def test_opamp_dual_criteria_match_the_book_example(self):
        """§6.3：LM358（GBW 0.7MHz / SR 0.5V/µs）增益 100 @ 10kHz、10Vpp
        → 闭环带宽 7kHz（正文原数）、GBW 需 ≥10MHz、满功率带宽 ≈16kHz。"""
        self.open('p1-07-ch6.html', 'opamp')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['闭环带宽'], 7.0, delta=0.1)
        self.assertAlmostEqual(out['GBW 需 ≥'], 10.0, delta=0.1)
        self.assertAlmostEqual(out['满功率带宽'], 15.9, delta=0.2)

    def test_buck_matches_the_book_example(self):
        """§13.2：12V→5V、150kHz、22µH、100µF → D 0.417、ΔIL 0.884A、ΔV 7.4mV。"""
        self.open('p2-03-ch13.html', 'buck')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['占空比 D'], 0.417, delta=0.001)
        self.assertAlmostEqual(out['电感纹波 ΔIL'], 0.884, delta=0.001)
        self.assertAlmostEqual(out['输出纹波 ΔV'], 7.4, delta=0.1)

    def test_noise_matches_the_book_example(self):
        """§11.6：1kΩ、1MHz 带宽、室温 → 密度 ≈4.1nV/√Hz、总噪声 ≈4.1µV。"""
        self.open('p2-01-ch11.html', 'noise')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['噪声密度'], 4.1, delta=0.1)
        self.assertAlmostEqual(out['总噪声'], 4.07, delta=0.05)

    def test_miller_matches_the_book_example(self):
        """§11.11 例 11-3：C_bc=5pF、|A|=50、Rs=10kΩ → C_in=255pF、f_p≈62kHz；
        教学点：砍增益到 30 → f_p≈103kHz ≥ 100kHz 目标（正文原数）。"""
        self.open('p2-01-ch11.html', 'miller')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['等效电容 C_in'], 255, delta=1)
        self.assertAlmostEqual(out['输入极点 f_p'], 62.4, delta=0.5)
        self.assertLessEqual(out['达成比 f_p/100k'], 1.0)
        self.page.locator('.calc[data-calc="miller"] input').nth(0).fill('30')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['输入极点 f_p'], 102.7, delta=1.0)
        self.assertGreaterEqual(out['达成比 f_p/100k'], 1.0)

    def test_swcap_matches_the_book_example(self):
        """§5.1：20pF、5V、10MHz → 单线 5mW、充放能耗 0.5nJ（正文原数）；
        教学点：64 根一起翻 → 320mW；同一根线降到 3.3V → 2.2mW，功耗按 V² 缩。"""
        self.open('p1-06-ch5.html', 'swcap')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['单线功耗'], 5.0, delta=0.01)
        self.assertAlmostEqual(out['每次充放能耗'], 0.5, delta=0.01)
        self.page.locator('.calc[data-calc="swcap"] input').nth(3).fill('64')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['总线功耗'], 320.0, delta=0.5)
        self.page.locator('.calc[data-calc="swcap"] .calc-presets button',
                          has_text='3.3V').click()
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['单线功耗'], 2.18, delta=0.01)

    def test_samplehold_matches_the_book_example(self):
        """§8.6 拍③：0.2pC 打进 10pF → 台阶 10mV = 20 LSB（2.048V/12 位，1 LSB=500µV）；
        教学点：电容加到 100pF → 1mV = 2 LSB（正文原数），8.3τ 同步放大 10 倍。"""
        self.open('p1-09-ch8.html', 'samplehold')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['1 LSB'], 500.0, delta=0.5)
        self.assertAlmostEqual(out['注入台阶 ΔV'], 10.0, delta=0.01)
        self.assertAlmostEqual(out['折合误差'], 20.0, delta=0.1)
        self.assertAlmostEqual(out['采集 8.3τ'], 3.7, delta=0.2)
        self.page.locator('.calc[data-calc="samplehold"] .calc-presets button',
                          has_text='100pF').click()
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['注入台阶 ΔV'], 1.0, delta=0.01)
        self.assertAlmostEqual(out['折合误差'], 2.0, delta=0.1)

    def test_loop_margin_matches_the_book_example(self):
        """§12.7：60dB、−120°、β=0.1 → 环路增益 100、裕度 60° 判「稳」（正文原数）；
        教学点：相移拖到 −170° → 裕度只剩 10°，判定翻成「危险」。"""
        self.open('p2-02-ch12.html', 'loop')
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['环路增益 A·β'], 100.0, delta=0.1)
        self.assertAlmostEqual(out['环路增益 dB'], 40.0, delta=0.1)
        self.assertAlmostEqual(out['相位裕度'], 60.0, delta=0.1)
        verdict = self.page.locator(
            '.calc[data-calc="loop"] .calc-out', has_text='判定').locator('b').text_content()
        self.assertEqual('稳', verdict)
        self.page.locator('.calc[data-calc="loop"] .calc-presets button',
                          has_text='−170').click()
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['相位裕度'], 10.0, delta=0.1)
        verdict = self.page.locator(
            '.calc[data-calc="loop"] .calc-out', has_text='判定').locator('b').text_content()
        self.assertEqual('危险', verdict)

    def test_divider_presets_hit_the_book_numbers(self):
        """预设一键切换：空载 → 5.00V 不塌；RL=1kΩ → 带载 0.83V（§0.3 口径）。"""
        box = self.open('p1-01-ch0.html', 'divider')
        box.locator('.calc-presets button', has_text='空载').click()
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['带载输出'], 5.0, delta=0.01)
        box.locator('.calc-presets button', has_text='RL = 1 kΩ').click()
        out = read_outputs(self.page)
        self.assertAlmostEqual(out['带载输出'], 0.83, delta=0.01)

    def test_charted_calcs_render_a_curve(self):
        """miller/buck 的曲线配置必须画出 inline SVG（读数之外给趋势）。"""
        for path, calc in (('p2-01-ch11.html', 'miller'), ('p2-03-ch13.html', 'buck'),
                           ('p1-09-ch8.html', 'samplehold')):
            with self.subTest(calc=calc):
                box = self.open(path, calc)
                chart = box.locator('.calc-chart svg')
                self.assertEqual(chart.count(), 1)
                self.assertEqual(chart.locator('polyline').count(), 1)

    def test_buck_chart_keeps_the_work_point_off_the_floor(self):
        """ΔV(C) 是 1/C 双曲线：横轴若从 1µF 起，曲线峰值会把 ymax 撑大百倍，
        工作点红点贴底（高度比 ≈1%），读者只看到一条贴着轴的线。

        回归来源：v3.74 把域收到 [C/2, 4C]，红点落到 43% 高度。断言用中间带
        （25%–85%）而不是精确像素——域以后再调，只要工作点还在图上就放行。
        """
        box = self.open('p2-03-ch13.html', 'buck')
        chart = box.locator('.calc-chart svg')
        spot = chart.locator('circle[fill="#dc2626"]')
        self.assertEqual(spot.count(), 1)
        spot_y = float(spot.get_attribute('cy'))
        # drawChart：T=22，绘图区高 ih = 150-22-28 = 100
        ratio = (122 - spot_y) / 100
        self.assertGreater(ratio, 0.25, f'工作点贴底：高度比 {ratio:.2f}')
        self.assertLess(ratio, 0.85, f'工作点越顶：高度比 {ratio:.2f}')

    def test_every_registered_calc_ships_and_renders(self):
        """calc.js 注册的每个型号都必须有容器、能渲染出输入与结果。"""
        self.open('p1-01-ch0.html', 'divider')
        registered = self.page.evaluate("""() => {
          return fetch('javascripts/calc.js').then(r => r.text()).then(t =>
            [...t.matchAll(/^\\s{4}(\\w+): \\{$/gm)].map(m => m[1]));
        }""")
        self.assertEqual(
            ['divider', 'electrolyte', 'hysteresis', 'probe', 'opamp', 'buck', 'noise', 'miller',
             'swcap', 'samplehold', 'loop'],
            registered)
        for path, calc in (('p1-01-ch0.html', 'divider'), ('p1-02-ch1.html', 'electrolyte'),
                           ('p1-06-ch5.html', 'swcap'), ('p1-07-ch6.html', 'opamp'),
                           ('p1-08-ch7.html', 'hysteresis'), ('p1-09-ch8.html', 'samplehold'),
                           ('p2-01-ch11.html', 'noise'), ('p2-02-ch12.html', 'loop'),
                           ('p2-03-ch13.html', 'buck'), ('p2-01-ch11.html', 'miller'),
                           ('p4-01-ch16.html', 'probe')):
            with self.subTest(calc=calc):
                box = self.open(path, calc)
                self.assertGreaterEqual(box.locator('.calc-inputs input, .calc-inputs select').count(), 2)
                self.assertGreaterEqual(box.locator('.calc-out').count(), 2)


if __name__ == '__main__':
    unittest.main()
