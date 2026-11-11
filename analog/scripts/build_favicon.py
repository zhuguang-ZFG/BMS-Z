#!/usr/bin/env python
"""生成站点 favicon（assets/images/favicon.png）。

用法：
    python scripts/build_favicon.py
    python scripts/build_favicon.py --out X.png --size 128

为什么自渲染而不是沿用主题默认：Material 自带的是**一本白书压深灰圆**，
和「模拟电路」毫无关系，浏览器标签页上只看到一团深色。这里用站点自己的
标识（`scripts/site_media/logo.svg` 的「节点圈 + 正弦」）压在同一套品牌
渐变上，标签页、顶栏、og 分享卡三处才是同一套视觉。

产物是**提交进仓库的静态文件**，CI 不重新生成（同 assets/og-cover.png 的
做法）——不同机器的 Chromium / 抗锯齿会让像素有差异，逐字节比对必然红。

渲染走 Playwright 的 Chromium：直接用现成的 SVG，比手搓 PIL 路径省事。
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "scripts" / "site_media" / "logo.svg"
DEFAULT_OUT = ROOT / "assets" / "images" / "favicon.png"

# 64px 足够：浏览器标签用 16px、书签栏 32px，桌面快捷方式也不会超过 64。
DEFAULT_SIZE = 64

# 图标里的描边要比顶栏 logo 粗得多，而且标识要占得更满 —— 浏览器标签只有
# 16px，细线和小图形在那尺寸上直接糊成一片。这两个值是按 16/24/32/64px
# 四档实拍挑的（0.64 时 16px 下圈变细、正弦完全看不见）。
FAVICON_STROKE = 2.9
FAVICON_RATIO = 0.78

CARD = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  html,body{{width:{size}px;height:{size}px;overflow:hidden;background:transparent}}
  .badge{{
    width:100%;height:100%;display:grid;place-items:center;
    border-radius:{radius}px;
    background:linear-gradient(135deg,#4f46e5 0%,#4051b5 58%,#3730a3 100%);
    color:#fff;
  }}
  svg{{display:block;width:{mark}px;height:{mark}px}}
</style></head><body>
  <div class="badge">{markup}</div>
</body></html>
"""


def _markup():
    """读 logo.svg，把描边调粗到 favicon 该有的粗细。

    只改 stroke-width：形状与顶栏完全一致，缩小后仍认得出是同一个标。
    """
    text = LOGO.read_text(encoding="utf-8")
    return text.replace('stroke-width="1.9"', 'stroke-width="%s"' % FAVICON_STROKE)


def render(out: Path, size: int = DEFAULT_SIZE):
    from playwright.sync_api import sync_playwright

    html = CARD.format(size=size, radius=round(size * 0.23),
                       mark=round(size * FAVICON_RATIO), markup=_markup())
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        # channel="chrome"：与 build_og_image.py 同理，内置 headless shell 未必装好。
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": size, "height": size},
                                device_scale_factor=1)
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(120)
        page.screenshot(path=str(out), omit_background=True)
        browser.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--size", type=int, default=DEFAULT_SIZE)
    args = ap.parse_args()
    path = render(Path(args.out), args.size)
    print(f"已生成 {path}（{args.size}×{args.size}，{path.stat().st_size / 1024:.1f} KB）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
