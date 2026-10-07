#!/usr/bin/env python3
"""Pages 侧门禁：构建产物里每条站内链接都必须命中真实页面，带锚点的必须命中真实 id；
反向也要成立——每一页都得被别处链到，否则等于写了正文却没发布（站点上没有入口）。

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

# <a> 之外的引用（script src、img src、link href）由 Vite 构建保证存在——
# 文件名是构建期算出来的哈希，手写不进去。手能写错、且 CI 之外没人再查的，只有 <a>。
ID_RE = re.compile(r'\bid="([^"]+)"')
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


class AnchorCollector(HTMLParser):
    """抓全部 <a href>。HTMLParser 自己处理单双引号与转义，不用正则啃 HTML。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value is not None:
                    self.hrefs.append(value)


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

    # 反向对账：没有任何页面链到它，这一页在站点上就等于没发布——搜索引擎进不来，
    # 读者从侧栏也点不到。404.html 是 GitHub Pages 按路径直接取的，本来就没有入口。
    for page in sorted(pages):
        if page.name != "404.html" and not inbound.get(page):
            failures.append(f"孤儿  {page.relative_to(dist).as_posix()}  ->  没有任何页面链到它")

    print(f"ok: {len(pages)} 个页面，站内链接 {n_links} 条（其中带锚点 {n_frag} 条）")
    if failures:
        print(f"FAIL: {len(failures)} 处站内链接对不上：", file=sys.stderr)
        for line in failures:
            print("  " + line, file=sys.stderr)
        return 1
    print("ok: 全部命中真实页面与锚点 id，且每页都有入口")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
