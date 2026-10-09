#!/usr/bin/env python3
"""Pages 侧门禁：构建产物里每条站内链接都必须命中真实页面，带锚点的必须命中真实 id；
反向也要成立——每一页都得被别处链到，否则等于写了正文却没发布（站点上没有入口）。
正文里的图片一起对账：src 必须命中真实文件，除每页首图外必须懒加载，站内图必须带宽高。

为什么 VitePress 自带死链检查不够：docs/ 里有近百处链接跨出站点根（指向 README、
code/、.github 模板），这些在源码里是合法的——GitHub 网页端和 Obsidian 都能点开，
所以 config.mts 开着 ignoreDeadLinks，改由渲染期插件改写成 GitHub blob URL。
改写是否完整、站内 3600+ 条链接是否条条可达，源码侧（check_docs.py）看不见，
只有对 dist 对账才知道。锚点同理：check_docs.py 按 GitHub slug 规则验证源码，
这里按 dist 里的真实 id 验证产物，两边一起把 config.mts 的 slugify 钉死。

用法：python3 .github/scripts/check_pages.py [dist目录] [--base /BMS-Z/]
"""
from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[2]

# <a> 与 <img> 之外的引用（script src、link href）由 Vite 构建保证存在——文件名是
# 构建期算出来的哈希，手写不进去。<img> 要查是因为仓库根拷进来的 HTML：它的 src 是
# 人手写的相对路径，Vite 根本接管不到它（换掉 Jekyll 之后 /BMS-Z/docs/… 404 就是这么
# 漏出去的）。另外图片的懒加载与宽高占位是渲染期插件加的，插件一坏产物就静默退化，
# 只有对账才知道。
ID_RE = re.compile(r'\bid="([^"]+)"')
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
# 图片的 width/height 属性：viewBox 允许小数，所以整数小数都算合法。
NUMERIC_RE = re.compile(r"\d+(?:\.\d+)?")


class AnchorCollector(HTMLParser):
    """抓全部 <a href>，以及正文区（div.vp-doc）之后的 <img> 属性。

    HTMLParser 自己处理单双引号与转义，不用正则啃 HTML。
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.images: list[tuple[bool, dict[str, str | None]]] = []
        self._in_doc = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        given = dict(attrs)
        if tag == "a":
            if given.get("href") is not None:
                self.hrefs.append(given["href"])
            return
        if "vp-doc" in (given.get("class") or ""):
            self._in_doc = True
        if tag == "img":
            self.images.append(
                (self._in_doc, {k: given.get(k) for k in ("src", "loading", "width", "height")})
            )


FOOT_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
THEME_FOOT_RE = re.compile(r'<a[^>]*class="[^"]*\b(prev|next)\b[^"]*"[^>]*href="([^"]+)"')

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist", nargs="?", default=str(ROOT / "docs" / ".vitepress" / "dist"))
    parser.add_argument("--base", default="/BMS-Z/")
    args = parser.parse_args()

    dist = Path(args.dist)
    base = args.base
    if not dist.is_dir():
        print(f"FAIL: dist 目录不存在：{dist}", file=sys.stderr)
        return 1

    # 每个页面的 id 集合只算一次；锚点命中判定要用目标页的集合。
    pages: dict[Path, list[str]] = {}
    for html in sorted(dist.rglob("*.html")):
        pages[html] = ID_RE.findall(html.read_text(encoding="utf-8"))

    failures: list[str] = []
    n_links = 0
    n_frag = 0
    n_img = 0
    # 反向计票：每页被多少别的页面链到。自己链自己不算——那是页内跳转。
    inbound: dict[Path, int] = {}
    for html in sorted(pages):
        rel_html = html.relative_to(dist).as_posix()
        page_url = base + rel_html
        collector = AnchorCollector()
        collector.feed(html.read_text(encoding="utf-8"))
        for href in collector.hrefs:
            href = href.strip()
            # 外链（https:/mailto: 等）与协议相对链接（//）不在站内对账范围。
            if not href or SCHEME_RE.match(href) or href.startswith("//"):
                continue
            n_links += 1
            parts = urlsplit(urljoin("https://site" + page_url, href))
            path = unquote(parts.path)
            if not path.startswith(base):
                failures.append(f"越界  {rel_html}  ->  {href}")
                continue
            # href 正好等于 base（导航 logo 指首页）时切出来是空串，按首页算。
            rel = path[len(base):].lstrip("/")
            if not rel or rel.endswith("/"):
                rel += "index.html"
            target = dist / rel
            if not target.is_file():
                failures.append(f"死链  {rel_html}  ->  {href}")
                continue
            if target != html:
                inbound[target] = inbound.get(target, 0) + 1
            if parts.fragment:
                n_frag += 1
                frag = unquote(parts.fragment)
                if frag not in pages.get(target, []):
                    failures.append(f"锚点  {rel_html}  ->  {href}")

        # 图片：正文区（div.vp-doc）里的图由渲染期插件加 loading/width/height，插件一坏
        # 产物就静默退化；拷进来的根 HTML 没有 vp-doc，那种页面整页都按正文算。
        images = [a for in_doc, a in collector.images if in_doc] or [a for _, a in collector.images]
        for index, attrs in enumerate(images):
            src = (attrs.get("src") or "").strip()
            if not src:
                failures.append(f"图片  {rel_html}  ->  src 是空的")
                continue
            n_img += 1
            if index and attrs.get("loading") != "lazy":
                failures.append(f"懒加载  {rel_html}  ->  {src}")
            # 一律要求真实像素宽高：懒加载把下载推迟到靠近视口时，没有宽高就会在图片
            # 落地那一刻把下面的正文顶开，动画正看着会跳一下。站内图从源文件读真实尺寸，
            # 外链只认 lazy-images 插件里实测过的固定尺寸（视频封面）；白名单外的新外链
            # 来源会在这里判红，逼着先把尺寸量出来再登记，不靠约定俗成。
            if not NUMERIC_RE.fullmatch(attrs.get("width") or "") or not NUMERIC_RE.fullmatch(attrs.get("height") or ""):
                failures.append(f"宽高  {rel_html}  ->  {src}")
            if SCHEME_RE.match(src) or src.startswith("//"):
                continue  # 外链图不归本仓库管，不做死链对账，只查宽高与懒加载
            parts = urlsplit(urljoin("https://site" + page_url, src))
            path = unquote(parts.path)
            if not path.startswith(base):
                failures.append(f"越界图片  {rel_html}  ->  {src}")
                continue
            target = dist / path[len(base):].lstrip("/")
            if not target.is_file():
                failures.append(f"死图  {rel_html}  ->  {src}")
                continue

    # 反向对账：没有任何页面链到它，这一页在站点上就等于没发布——搜索引擎进不来，
    # 读者从侧栏也点不到。404.html 是 GitHub Pages 按路径直接取的，本来就没有入口。
    for page in sorted(pages):
        if page.name != "404.html" and not inbound.get(page):
            failures.append(f"孤儿  {page.relative_to(dist).as_posix()}  ->  没有任何页面链到它")

    # 页脚双轨对账：手写页脚是 GitHub/Obsidian 的正规链（精选链，人工校准过），主题页脚是站点上
    # 按 frontmatter/sidebar 渲染的那一对。同页并存时必须同靶：手写指向 docs 内的页面，主题那一向
    # 就必须是同一个 href；手写写「无（……）」或指向仓库根 README（站点改写成 GitHub 链接），主题
    # 那一向就必须缺席。没有手写页脚的页面靠主题自动导航，那里它是唯一来源，不归这道门管。
    n_footer = 0
    for html in sorted(pages):
        rel_html = html.relative_to(dist).as_posix()
        md = (ROOT / "docs" / rel_html).with_suffix(".md")
        if not md.is_file():
            continue
        manual: dict[str, str | None] = {}
        for line in md.read_text(encoding="utf-8").splitlines():
            for label in ("上一篇", "下一篇"):
                if f"**{label}**" in line and label not in manual:
                    seg = line.split(f"**{label}**", 1)[1].split("｜")[0]
                    match = FOOT_LINK_RE.search(seg)
                    manual[label] = match.group(1) if match else None
        if not manual:
            continue
        theme = dict(THEME_FOOT_RE.findall(html.read_text(encoding="utf-8")))
        for label, tgt in manual.items():
            cls = "prev" if label == "上一篇" else "next"
            got = unquote((theme.get(cls) or "").split("#")[0])
            want = ""
            if tgt is not None:
                abs_p = (md.parent / tgt.split("#")[0]).resolve()
                try:
                    rel_target = abs_p.with_suffix(".html").relative_to((ROOT / "docs").resolve())
                    want = base + rel_target.as_posix()  # 与 got 同样按解码路径比；dist 有的 href 编码有的原样，编码比会假红
                except ValueError:
                    want = ""  # 仓库根 README 这类站外目标：主题那一向应当缺席
            if got != want:
                failures.append(f"页脚  {rel_html}  {label}: 手写要对 {want or '(无主题页脚)'}，主题实际 {got or '缺席'}")
            else:
                n_footer += 1

    print(
        f"ok: {len(pages)} 个页面，站内链接 {n_links} 条（其中带锚点 {n_frag} 条），正文图片 {n_img} 张，页脚 {n_footer} 向手写与主题一致"
    )
    if failures:
        print(f"FAIL: {len(failures)} 处产物对不上：", file=sys.stderr)
        for line in failures:
            print("  " + line, file=sys.stderr)
        return 1
    print("ok: 全部命中真实页面与锚点 id，每页都有入口，图片都能下载且预留了位置")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
