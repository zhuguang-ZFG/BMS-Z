# -*- coding: utf-8 -*-
"""SVG 明暗两套主题的可读性回归：102 张动画在 light / dark 下都不得出现低对比度文字。

v3.25 修掉的暗色盲区（由本测试长期兜底）：
- 面板色 remap 只写了 `rect[fill="#f8fafc"]`，导致运放三角 / 反相泡等**非 rect 器件体**
  在暗色下仍是浅色，压在上面的红/绿 `+`/`−` 直接看不见；
- `#f1f5f9 / #e0f2fe / #fff7ed / #d1fae5 / #fee2e2 / #34d399` 等浅底色根本没有 remap；
- `fill="#fff"` 的器件体不会 remap（短写不匹配 `[fill="#ffffff"]`），暗色下仍为纯白。

v3.26 补上的浅色盲区：`#94a3b8`(2.6:1) / `#0ea5e9`(2.7:1) / `#f59e0b`(2.2:1) 这三个
「弱化色」当**文字**用太淡（当线/粒子用没问题）——已用 `@media (prefers-color-scheme: light)`
只压暗文字、不动同色的线。

判定口径：对每个可见 `<text>`，用「文档序中最后一个 bbox 命中其中心、且有效不透明度 ≥0.5 的
形状」作为真实底色（半透明药丸底衬/淡色蒙版按页面底色算），再算 WCAG 对比度，要求 ≥ 3.0。

Requires Playwright and installed Google Chrome (channel="chrome").
"""
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "svg"
MODES = ("light", "dark")
MIN_RATIO = 3.0

PROBE = r"""
() => {
  const lin = c => { c/=255; return c<=0.04045 ? c/12.92 : Math.pow((c+0.055)/1.055, 2.4); };
  const lum = (r,g,b) => 0.2126*lin(r)+0.7152*lin(g)+0.0722*lin(b);
  const contrast = (a,b) => { const l1=lum(a[0],a[1],a[2]), l2=lum(b[0],b[1],b[2]);
    const hi=Math.max(l1,l2), lo=Math.min(l1,l2); return (hi+0.05)/(lo+0.05); };
  const parse = s => { if(!s) return null; if(s==='none'||s==='transparent') return null;
    const m=s.match(/(\d+(?:\.\d+)?)/g); return m? m.slice(0,3).map(Number):null; };

  const svg = document.documentElement;
  const TAG = ['rect','path','polygon','circle','ellipse'];
  const nodes = [...svg.querySelectorAll('*')].filter(e => !e.closest('defs'));
  const info = nodes.map((e,i) => {
    const tag = e.tagName.toLowerCase();
    let bb=null; try { bb = e.getBBox(); } catch(_) {}
    const cs = getComputedStyle(e);
    const fo = parseFloat(cs.fillOpacity || '1');
    return { e, i, tag, bb,
             moving: !!e.querySelector('animateMotion, animateTransform'),
             fill: parse(cs.fill),
             opacity: parseFloat(cs.opacity||'1') * (isNaN(fo)?1:fo),
             fillRaw: cs.fill };
  });

  // 页面底板色：解析 .page-bg 实际指向的那条渐变（明/暗各不相同）
  let PAGE = [248,250,252];
  try {
    const bg = svg.querySelector('.page-bg');
    const f = bg ? getComputedStyle(bg).fill : '';
    const m = f.match(/url\(["']?#([^"')]+)/);
    if (m) {
      const st = svg.querySelector('#' + m[1] + ' stop');
      if (st) PAGE = parse(getComputedStyle(st).stopColor) || PAGE;
    }
  } catch(_) {}

  const bad = []; let scanned = 0;
  info.forEach(t => {
    if (t.tag !== 'text' || !t.bb || t.bb.width === 0) return;
    if (t.moving || t.opacity < 0.35) return;
    const fg = t.fill; if (!fg) return;
    scanned++;
    const cx = t.bb.x + t.bb.width/2, cy = t.bb.y + t.bb.height/2;
    let bg = PAGE;
    for (let j = t.i - 1; j >= 0; j--) {
      const s = info[j];
      if (!TAG.includes(s.tag)) continue;
      if (s.moving || !s.bb || !s.fill || s.opacity < 0.5) continue;
      const b = s.bb;
      if (cx >= b.x && cx <= b.x + b.width && cy >= b.y && cy <= b.y + b.height) { bg = s.fill; break; }
    }
    const ratio = contrast(fg, bg);
    if (ratio < 3.0) bad.push({ txt:(t.e.textContent||'').slice(0,26),
                                fg:t.fillRaw, bg:`rgb(${bg.join(',')})`, ratio:+ratio.toFixed(2) });
  });
  return { scanned, bad };
}
"""


class TestSvgContrast(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = {}          # mode -> {stem: [violations]}
        cls.scanned = {}         # mode -> int
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome", headless=True)
            for mode in MODES:
                pg = b.new_page(viewport={"width": 1000, "height": 900}, color_scheme=mode)
                rep, total = {}, 0
                for f in sorted(ASSETS.glob("*.svg")):
                    pg.goto(f.as_uri())
                    pg.wait_for_timeout(8)
                    r = pg.evaluate(PROBE)
                    if r["bad"]:
                        rep[f.stem] = r["bad"]
                    total += r["scanned"]
                pg.close()
                cls.report[mode] = rep
                cls.scanned[mode] = total
            b.close()

    def test_probe_actually_scanned_text(self):
        """守卫：探针必须真的量到大量文字，否则本测试是「假绿」。"""
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertGreaterEqual(len(self.report[mode]), 0)
                self.assertGreaterEqual(
                    self.scanned[mode], 1500,
                    f"{mode} 模式只量到 {self.scanned[mode]} 个文字，探针可能已失效")

    def test_no_low_contrast_text(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                bad = self.report[mode]
                msg = "\n".join(
                    f"  {k}: " + "; ".join(
                        f"{x['txt']!r} fg={x['fg']} on bg={x['bg']} ratio={x['ratio']}"
                        for x in v[:4])
                    for k, v in bad.items())
                self.assertEqual(
                    {}, bad,
                    f"{mode} 模式下有 {len(bad)} 张图存在对比度 < {MIN_RATIO} 的文字：\n{msg}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
