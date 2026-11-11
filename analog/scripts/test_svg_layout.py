# -*- coding: utf-8 -*-
"""SVG 版面几何回归：102 张动画不得出现「内容出界 / 字幕压字 / 注释框溢出 / 文字被裁 / 文字被盖」。

用 Playwright + 系统 Chrome 打开每张 SVG，跑 getBBox() 做只读几何断言（不写任何文件）。
v3.24 一次性修掉的 30+ 处版面硬伤、v3.26 的「轴标题被后画面板整块盖住」，由本测试长期兜底。

判定口径（为消除假阳性而设）：
- 全幅背景板（宽或高 ≥ 画布）与 `url(#…)` 底纹（渐变/点阵/暗角）一律不计；
- 字幕组（带 `animateTransform` 的 `<g>`）天然同 y 叠放、beat 标签按 opacity 时分复用，
  因此「静态文字互相压字」只统计**自身及祖先都没有 opacity 动画**的文字；
- `getBBox()` 不含祖先 transform，本库 SVG 均为平铺结构、不用嵌套 transform 定位。

Requires Playwright and installed Google Chrome (channel="chrome").
"""
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "svg"

# 一次性把所有检查跑在同一个页面里，避免 102 次重复求值。
PROBE = r"""
() => {
  const svg = document.documentElement;
  const W = +svg.getAttribute('width'), H = +svg.getAttribute('height');
  const all = Array.from(svg.querySelectorAll('rect,circle,line,path,polygon,polyline,text,ellipse'))
                   .filter(e => !e.closest('defs'));
  all.forEach((e, i) => { e.__i = i; });

  const isPlate = e => {
    if (e.classList && (e.classList.contains('page-bg') || e.classList.contains('page-vig')
                        || e.classList.contains('page-hdr'))) return true;
    if ((e.getAttribute('fill') || '').indexOf('url(#') >= 0) return true;   // 渐变/点阵/暗角
    const b = e.getBBox();
    return b.width >= W - 1 && b.height >= H - 1;
  };
  const hasOpacityAnim = e => {
    let n = e;
    while (n && n.tagName !== 'svg') {
      if (Array.from(n.children).some(c => c.tagName === 'animate'
          && c.getAttribute('attributeName') === 'opacity')) return true;
      n = n.parentElement;
    }
    return false;
  };
  const capGroups = Array.from(svg.querySelectorAll('g'))
                         .filter(g => g.querySelector(':scope > animateTransform'));
  const inCap = new Set();
  capGroups.forEach(g => { inCap.add(g); g.querySelectorAll('*').forEach(k => inCap.add(k)); });
  const capTexts = [];
  capGroups.forEach(g => {
    const t = Array.from(g.children).find(c => c.tagName === 'text');
    if (t) capTexts.push(t);
  });

  const texts = all.filter(e => e.tagName === 'text');
  const capSet = new Set(capTexts);
  const hasAnimChild = e => Array.from(e.children)
      .some(c => ['animate', 'animatemotion', 'animatetransform'].includes(c.tagName.toLowerCase()));
  const out = { W, H, below: [], capVsText: [], capVsShape: [], noteOver: [], clipped: [], staticHit: [], covered: [] };

  // ① 内容超出画布底部
  for (const e of all) {
    if (isPlate(e)) continue;
    const b = e.getBBox();
    if (b.y + b.height > H + 1)
      out.below.push({ tag: e.tagName, txt: (e.textContent || '').slice(0, 24), bot: +(b.y + b.height).toFixed(1) });
  }

  // ② 字幕压住其它文字
  for (const c of capTexts) {
    const cb = c.getBBox();
    for (const t of texts) {
      if (t === c || capSet.has(t)) continue;
      const b = t.getBBox();
      const ix = Math.min(b.x + b.width, cb.x + cb.width) - Math.max(b.x, cb.x);
      const iy = Math.min(b.y + b.height, cb.y + cb.height) - Math.max(b.y, cb.y);
      if (ix > 1.5 && iy > 1.5)
        out.capVsText.push({ cap: (c.textContent || '').slice(0, 18), other: (t.textContent || '').slice(0, 18) });
    }
  }

  // ③ 字幕压住「其后绘制」的形状（注释框等）
  for (const c of capTexts) {
    const cb = c.getBBox();
    const g = c.parentElement;
    const giMax = Math.max(-1, ...Array.from(g.querySelectorAll('*'))
                                      .map(k => (k.__i === undefined ? -1 : k.__i)));
    for (const e of all) {
      if (inCap.has(e) || e.tagName === 'text') continue;
      if (e.__i <= giMax) continue;
      if (isPlate(e)) continue;
      const b = e.getBBox();
      if (b.width * b.height > 0.35 * W * H) continue;      // 大面板允许被压
      const ix = Math.min(b.x + b.width, cb.x + cb.width) - Math.max(b.x, cb.x);
      const iy = Math.min(b.y + b.height, cb.y + cb.height) - Math.max(b.y, cb.y);
      if (ix > 1.5 && iy > 1.5)
        out.capVsShape.push({ cap: (c.textContent || '').slice(0, 18), tag: e.tagName });
    }
  }

  // ④ note_box 文案溢出自己的框（支持折行后的多行文案）
  for (const g of svg.querySelectorAll('g')) {
    const rects = Array.from(g.children).filter(c => c.tagName === 'rect');
    const ts = Array.from(g.children).filter(c => c.tagName === 'text');
    if (!rects.length || !ts.length) continue;
    rects.sort((a, b) => b.getBBox().width - a.getBBox().width);
    const rb = rects[0].getBBox();
    let x0 = Infinity, x1 = -Infinity;
    for (const t of ts) {
      const b = t.getBBox();
      x0 = Math.min(x0, b.x); x1 = Math.max(x1, b.x + b.width);
    }
    const over = Math.max(rb.x - x0, x1 - (rb.x + rb.width));
    if (over > 6)
      out.noteOver.push({ txt: (ts[0].textContent || '').slice(0, 24), over: +over.toFixed(1) });
  }

  // ⑤ 文字被画布四边裁切
  for (const t of texts) {
    const b = t.getBBox();
    const sides = [];
    if (b.x < -1) sides.push('left');
    if (b.x + b.width > W + 1) sides.push('right');
    if (b.y < -1) sides.push('top');
    if (b.y + b.height > H + 1) sides.push('bottom');
    if (sides.length)
      out.clipped.push({ txt: (t.textContent || '').slice(0, 24), side: sides.join(',') });
  }

  // ⑥ 静态文字互相压字（≥5.5px 才算真压；小重叠属于字面升降部留白）
  const statics = texts.filter(t => !capSet.has(t) && !hasOpacityAnim(t));
  for (let i = 0; i < statics.length; i++) {
    for (let j = i + 1; j < statics.length; j++) {
      const a = statics[i].getBBox(), b = statics[j].getBBox();
      const ix = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x);
      const iy = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y);
      if (ix > 3 && iy > 5.5)
        out.staticHit.push({ a: (statics[i].textContent || '').slice(0, 18),
                             b: (statics[j].textContent || '').slice(0, 18),
                             ix: +ix.toFixed(1), iy: +iy.toFixed(1) });
    }
  }
  // ⑦ 静态文字被「其后绘制」的不透明形状完整盖住 —— 真正看不见（mosfet-curves 的
  //    轴标题 V_DS → 曾被后画的说明面板整块盖住；本项专门兜底这类「画了等于没画」）
  for (const t of texts) {
    if (capSet.has(t) || hasOpacityAnim(t) || hasAnimChild(t)) continue;
    const tb = t.getBBox();
    if (!tb.width) continue;
    const cx = tb.x + tb.width / 2, cy = tb.y + tb.height / 2;
    for (const e of all) {
      if (e.__i <= t.__i) continue;                                  // 只看后绘制的
      if (!['rect', 'path', 'polygon', 'circle', 'ellipse'].includes(e.tagName.toLowerCase())) continue;
      if (isPlate(e) || hasAnimChild(e)) continue;
      const cs = getComputedStyle(e);
      if (!cs.fill || cs.fill === 'none') continue;                   // 描边曲线（波形/引线）不遮字
      if ((cs.fill || '').indexOf('url(') >= 0) continue;            // 渐变/底纹不算实心遮盖
      const m = (cs.fill || '').match(/rgba?\([^)]*?,\s*([\d.]+)\)/);
      if (m && +m[1] < 0.9) continue;                                // 半透明不算
      if (parseFloat(cs.opacity || '1') < 0.9) continue;
      const b = e.getBBox();
      if (b.width * b.height <= 200) continue;                       // 小色块允许压（药丸/色条）
      if (cx >= b.x && cx <= b.x + b.width && cy >= b.y && cy <= b.y + b.height) {
        out.covered.push({ txt: (t.textContent || '').slice(0, 24), tag: e.tagName,
                           cov: `${b.width | 0}x${b.height | 0}` });
        break;
      }
    }
  }
  return out;
}
"""


def _fmt(rows, n=3):
    return "; ".join(str(r) for r in rows[:n]) + (" …" if len(rows) > n else "")


class TestSvgLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._pw = sync_playwright().start()
        cls.browser = cls._pw.chromium.launch(channel="chrome", headless=True)
        cls.page = cls.browser.new_page(viewport={"width": 1200, "height": 900})
        cls.files = sorted(ASSETS.glob("*.svg"))
        cls.report = {}
        for f in cls.files:
            cls.page.goto(f.as_uri())
            cls.page.locator("svg").wait_for()
            cls.report[f.stem] = cls.page.evaluate(PROBE)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls._pw.stop()

    def test_assets_present(self):
        self.assertGreaterEqual(len(self.files), 100, "SVG 数量异常")

    def test_no_content_below_canvas(self):
        bad = {n: r["below"] for n, r in self.report.items() if r["below"]}
        self.assertEqual(bad, {}, f"内容溢出画布底部：{_fmt(list(bad.items()))}")

    def test_captions_do_not_overlap_text(self):
        bad = {n: r["capVsText"] for n, r in self.report.items() if r["capVsText"]}
        self.assertEqual(bad, {}, f"字幕压住正文：{_fmt(list(bad.items()))}")

    def test_captions_do_not_cover_later_shapes(self):
        bad = {n: r["capVsShape"] for n, r in self.report.items() if r["capVsShape"]}
        self.assertEqual(bad, {}, f"字幕压住其后绘制的形状：{_fmt(list(bad.items()))}")

    def test_note_box_text_fits_box(self):
        bad = {n: r["noteOver"] for n, r in self.report.items() if r["noteOver"]}
        self.assertEqual(bad, {}, f"注释框文案溢出框宽：{_fmt(list(bad.items()))}")

    def test_text_not_clipped_by_canvas(self):
        bad = {n: r["clipped"] for n, r in self.report.items() if r["clipped"]}
        self.assertEqual(bad, {}, f"文字被画布边缘裁切：{_fmt(list(bad.items()))}")

    def test_static_text_do_not_collide(self):
        bad = {n: r["staticHit"] for n, r in self.report.items() if r["staticHit"]}
        self.assertEqual(bad, {}, f"静态文字互相压字：{_fmt(list(bad.items()))}")

    def test_text_not_covered_by_later_shape(self):
        bad = {n: r["covered"] for n, r in self.report.items() if r["covered"]}
        self.assertEqual(bad, {}, f"文字被其后绘制的形状盖住（看不见）：{_fmt(list(bad.items()))}")


if __name__ == "__main__":
    unittest.main()
