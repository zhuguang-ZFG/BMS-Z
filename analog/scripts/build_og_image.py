#!/usr/bin/env python
"""生成自托管的社交分享卡（og:image / twitter:image）。

用法：
    python scripts/build_og_image.py            # 写到 assets/og-cover.png
    python scripts/build_og_image.py --out X.png

为什么自托管而不是外链：原先 og:image 指向 Wikimedia 的一张电路板照片，
① 抓取方要跨域取第三方资源，国内访问时常超时；② 那张图与本站内容无关，
分享出去看不出是「模拟电路教程」。这里用同一套站点配色渲染一张 1200×630
的卡片（og 的标准 1.91:1），产物提交进仓库、随站点一起发布。

产物是**提交进仓库的静态文件**，CI 不重新生成（不同机器字体不同，逐像素比对
必然红）。脚本依赖 Playwright 的 Chromium 来渲染——比 PIL 手排中文省事得多，
渐变 / 字重 / emoji 都能直接用。
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "assets" / "og-cover.png"

WIDTH, HEIGHT = 1200, 630

CARD = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><style>
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:1200px;height:630px;overflow:hidden}
  body{
    font-family:"Microsoft YaHei","PingFang SC","Hiragino Sans GB","Noto Sans CJK SC",
                "Source Han Sans SC",system-ui,sans-serif;
    background:linear-gradient(128deg,#141033 0%,#241c5c 38%,#3730a3 72%,#4f46e5 100%);
    color:#eef2ff;position:relative;
  }
  /* 点阵：让纯色渐变不至于太空 */
  .dots{position:absolute;inset:0;
    background-image:radial-gradient(rgba(199,210,254,.16) 1.4px,transparent 1.4px);
    background-size:26px 26px;}
  /* 右上角辉光 */
  .glow{position:absolute;width:760px;height:760px;right:-260px;top:-330px;border-radius:50%;
    background:radial-gradient(circle,rgba(129,140,248,.55),rgba(129,140,248,0) 66%);}
  .motif{position:absolute;right:22px;top:92px;opacity:.42}
  .wrap{position:relative;height:100%;padding:58px 66px;display:flex;flex-direction:column}
  .badge{display:inline-flex;align-items:center;gap:10px;align-self:flex-start;
    padding:9px 18px;border:1.5px solid rgba(199,210,254,.42);border-radius:999px;
    font-size:21px;letter-spacing:.04em;color:#c7d2fe}
  h1{margin-top:30px;font-size:78px;font-weight:800;letter-spacing:.01em;line-height:1.12}
  h1 .accent{color:#a5b4fc}
  .sub{margin-top:20px;font-size:27px;line-height:1.6;color:#c7d2fe;max-width:690px;
    text-wrap:balance}
  .chips{margin-top:auto;display:flex;gap:14px;flex-wrap:wrap}
  .chip{padding:12px 22px;border-radius:12px;background:rgba(199,210,254,.13);
    border:1px solid rgba(199,210,254,.24);font-size:23px;color:#e0e7ff}
  .chip b{color:#fff;font-weight:800}
</style></head><body>
  <div class="dots"></div><div class="glow"></div>
  <svg class="motif" width="440" height="240" viewBox="0 0 470 250" fill="none"
       stroke="#c7d2fe" stroke-width="3.2" stroke-linecap="round">
    <!-- RC 充电曲线 -->
    <path d="M10 200 C 70 200, 90 78, 150 62 C 215 46, 300 60, 460 58" opacity=".85"/>
    <!-- 正弦 -->
    <path d="M10 232 q 34 -34 68 0 t 68 0 t 68 0 t 68 0 t 68 0 t 68 0" opacity=".45"/>
    <!-- 坐标轴 -->
    <path d="M10 205 H 465" opacity=".35"/>
    <path d="M12 20 V 205" opacity=".35"/>
    <!-- 三极管符号 -->
    <circle cx="300" cy="150" r="30" opacity=".7"/>
    <path d="M282 132 V 168 M282 150 H 320 M320 130 V 170" opacity=".7"/>
  </svg>
  <div class="wrap">
    <span class="badge"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M4.5 19.5 C 8 15.5, 7.5 11, 11.5 9.5 C 15 7.5, 15.5 5.5, 19.5 4.5"/><circle cx="4.5" cy="19.5" r="1.6" fill="currentColor" stroke="none"/><circle cx="19.5" cy="4.5" r="1.6" fill="currentColor" stroke="none"/></svg>开放知识库 · CC BY-SA 4.0</span>
    <h1>通往<span class="accent">模拟电路</span>之路</h1>
    <p class="sub">从欧姆定律到芯片内部结构<br>原理推导 · 器件剖析 · 故障分析 · 动画演示</p>
    <div class="chips">
      <span class="chip"><b>19</b> 章核心内容</span>
      <span class="chip"><b>153</b> 张原理动画</span>
      <span class="chip"><b>90+34</b> 道自测题</span>
      <span class="chip">可交互教学样板</span>
    </div>
  </div>
</body></html>
"""


def render(out: Path):
    from playwright.sync_api import sync_playwright

    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        # channel="chrome" 而不是内置 chromium：本机只装了系统 Chrome，
        # 且内置 headless shell 的中文字体覆盖不如系统 Chrome 稳。
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT},
                                device_scale_factor=1)
        page.set_content(CARD, wait_until="load")
        page.wait_for_timeout(250)          # 等字体落地，避免拍到回退字形
        page.screenshot(path=str(out))
        browser.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    path = render(Path(args.out))
    size = path.stat().st_size
    print(f"已生成 {path}（{WIDTH}×{HEIGHT}，{size / 1024:.1f} KB）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
