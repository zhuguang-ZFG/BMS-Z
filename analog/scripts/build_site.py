#!/usr/bin/env python3
"""由 docs/ 生成 MkDocs 站点源 build/docs（含动画画廊与配套 JS/CSS）。

    python scripts/build_site.py            # 生成站点源 + build/mkdocs.yml
    python scripts/build_site.py --build    # 生成后直接调用 mkdocs build

内容页原样拷贝，另生成：
  * gallery.md —— 118 张动画卡片墙（按章筛选 + 关键字搜索，waytoagi 式卡片导航）
  * stylesheets/gallery.css、javascripts/gallery.js、javascripts/mathjax.js
  * build/mkdocs.yml —— 按篇分组的导航与 Material 主题配置
"""
from __future__ import annotations

import argparse
from html import escape
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from visual_player import load_players, wrap_visual_players

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BUILD = ROOT / "build"
OUT = BUILD / "docs"
SVG_SRC = ROOT / "assets" / "svg"

DEMO_HEAD = re.compile(r'^## (5\.\d+)\s+(.+?)\s*<a id="(demo\d+)"')
DEMO_IMG = re.compile(r'<img src="assets/(svg(?:-v2)?/[\w\-]+\.svg)"[^>]*alt="([^"]*)"')
# docs 迁移后锚点链接写作 p5-00-part5.md#demoN，拼回 README 时才是 #demoN——两种都要认
DEMO_LINK = re.compile(r"\[(5\.\d+)\]\((?:[\w\-]+\.md)?#(demo\d+)\)")
CHAPTER_ROW = re.compile(r"^\|\s*§(\d+)\s+(第\s*\d+\s*章[^|]*?)\s*\|")
SVG_SIZE = re.compile(r'<svg[^>]*\bwidth="(\d+)"\s+height="(\d+)"')


def svg_size(name):
    """读出 SVG 的画布尺寸，给 <img> 写 width/height 预留空间（消除画廊的布局抖动）。"""
    if not name:
        return 800, 460
    # name 既可能是纯文件名（wrap_picture 链，目录固定 assets/svg/），
    # 也可能是 parse_demos 捕获的带目录相对路径（svg/ 或 svg-v2/ 开头）。
    path = (ROOT / "assets" / name) if "/" in name else (SVG_SRC / name)
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:600]
    except OSError:
        return 800, 460
    m = SVG_SIZE.search(head)
    if m:
        return int(m.group(1)), int(m.group(2))
    # V2 SVG 只有 viewBox 没有 width/height 属性（handraw/papercut 渲染器输出）。
    vb = re.search(r'viewBox="[\d.\-]+\s+[\d.\-]+\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)"', head)
    return (int(float(vb.group(1))), int(float(vb.group(2)))) if vb else (800, 460)


IMG_TAG = re.compile(r'<img\s+src="assets/svg/([\w\-]+\.svg)"([^>]*)>')
IMG_ATTRS = 'loading="lazy" decoding="async"'

# 静止版的规则：与「动画版」同源，只是把"会飞"的东西（电流粒子 / 波形游标 /
# 扫压圆点 / 脉冲辉光圈）**无条件**关掉。节拍字幕与器件状态变化保留 —— 字幕是
# 多路复用（同一行轮流显示），一起显示反而互相压字、更读不了。
#
# 为什么不用 `@media (prefers-reduced-motion: reduce)` 写在 SVG 里？
# 因为 SVG 作为 <img> 载入时，Chrome 把 `prefers-reduced-motion` **恒判为 reduce**：
# 页面自己明明是无偏好，图片文档里却是 reduce（有头/无头、data:/http、独立启动的
# Chrome 155 均实测一致）。于是 SVG 内的 media query 要么恒不生效、要么恒生效；
# 一旦恒生效，全站 108 张动画对**所有人**都是静止的 —— v3.45 正是踩了这个坑。
# 正确做法是让**页面**选源：`<source media>` 在页面上下文里求值，因此是准的。
REDUCE_CSS = (
    "\n:has(> animateMotion):not(:has(text)),"
    "\n:has(> animateTransform):not(:has(text)),"
    '\n:has(> animate:not([attributeName="opacity"])):not(:has(text)){display:none}\n'
)


def reduce_variant(name):
    """动画文件名 → 对应的静止版文件名。"""
    return name[:-4] + ".reduce.svg"


def wrap_picture(name, img):
    """把动画 <img> 包进 <picture>，由 <source media> 在页面上下文里挑「静止版」。

    只在站点产物上做；`docs/` 与 README 保持原样（那里的 <img> 走默认的动画版）。
    """
    return ('<picture>'
            f'<source srcset="assets/svg/{reduce_variant(name)}" '
            'media="(prefers-reduced-motion: reduce)">'
            f'{img}</picture>')


def optimize_imgs(text):
    """给站点产物里的动画 <img> 补 loading="lazy" + decoding="async" + 按画布比例写 height，
    并包进 <picture>（由 <source media> 挑「减弱动效」下的静止版）。

    - 「动画演示中心」一页就嵌了全部 108 张 SVG（约 1.7MB），全部 eager 加载太浪费；
    - 108 张图高度从 430 到 762 不等，只写 width 会让浏览器在下载完成前无从预留高度，
      滚动时整页剧烈抖动（CLS）——补 height 后浏览器可提前按比例占位。
    只在站点产物上做，`docs/` 保持单一数据源干净；README 由 GitHub 自行懒加载。
    """
    def repl(m):
        name, rest = m.group(1), m.group(2)
        if "loading=" in rest:
            return m.group(0)
        w, h = svg_size(name)
        wm = re.search(r'\bwidth="(\d+)"', rest)
        if wm and "height=" not in rest:
            rest += f' height="{round(int(wm.group(1)) * h / w)}"'
        return wrap_picture(name, f'<img src="assets/svg/{name}"{rest} {IMG_ATTRS}>')
    return IMG_TAG.sub(repl, text)


def write_reduce_variants(dst=None):
    """为每张动画生成一份「静止版」`<stem>.reduce.svg`（只进站点产物，不进仓库）。

    做法是给动画版**追加**一段无条件生效的 REDUCE_CSS；选择器按结构匹配，所以新增
    动画无需登记。放进独立 <style> 追加在 </svg> 前，避免与原有样式块纠缠。

    `dst` 默认为站点产物的 `assets/svg/`；测试会传一个临时目录进来复用同一段逻辑。
    """
    dst = Path(dst) if dst is not None else (OUT / "assets" / "svg")
    if not dst.is_dir():
        return 0
    written = 0
    for svg in sorted(dst.glob("*.svg")):
        if svg.name.endswith(".reduce.svg"):
            continue
        text = svg.read_text(encoding="utf-8")
        i = text.rfind("</svg>")
        if i < 0:
            continue
        out = text[:i] + f"<style>{REDUCE_CSS}</style>\n" + text[i:]
        (dst / reduce_variant(svg.name)).write_text(out, encoding="utf-8", newline="\n")
        written += 1
    return written


# 标志性提示块：正文里以「**标签**：」开头的引用块，在**站点产物**里会被包成
# 彩色卡片。这套粗体标签就是本教程的固定语汇（精髓 / 公式速查 / 通关打卡 /
# 先修…），全站各出现几十次，是最该被一眼认出来的东西。
# v3.72 起从「emoji + 标签」改为纯文本标签：emoji 是 AI 味的视觉签名，印刷端
# 本来就被 strip_emoji 剥掉，站点与印刷由此对齐；卡片颜色仍由 callout-* 类承担。
CALLOUT_KINDS = {
    "场景": "scene",       # 章首生活化开场（场景卡 同族，见 test_book_scene 唯一性契约）
    "场景卡": "scene",
    "难度": "level",       # 章首分级（L0–L3）+ 精读时长
    "白话": "lead",        # 一句话导读写给第一次接触的人
    "先修": "prereq",
    "学完你应能": "goal",
    "通关打卡": "goal",
    "用法": "goal",
    "做完 19 组": "goal",
    "公式速查": "calc",
    "模型边界": "limit",   # 理想模型什么时候失效（v3.56 起 19 章章首一行）
    "精髓": "gem",         # 本节最该记住的一句
    "为什么": "why",       # 机制卡：现象 → 原因 → 判据
    "配套视频": "video",
    "60 秒动画版": "demo",
    "配套动画": "demo",
    "实物照片": "photo",
    "实测记录": "photo",
    "怎么看这张实物图": "photo",
    "附件": "attach",
    "资料": "attach",
    "datasheet 直达": "attach",
    "和第 6 章的分工": "attach",
    "一句话收束": "attach",
    "新增小节的配套料": "pin",
    "记忆锚点": "pin",
    "补充想法": "idea",
    "设计直觉": "idea",
    "核心理解": "idea",
    "一句话": "idea",
    "延伸阅读": "link",
    "相关链接": "link",
    "军规": "fix",         # 动手 / 排故的判据清单
    "修复方法": "fix",
    "注意": "warn",        # 坑
}

_CALLOUT_LABEL_RE = re.compile(r"^\*\*([^*]{1,24})\*\*\s*[：:]")


def _callout_kind(body):
    """引用块首行开头是不是「**已知标签**：」？是就返回对应的 slug。

    标签不在 CALLOUT_KINDS 里的（如「**打印复习稿**：」）原样当普通引用块，
    与 emoji 时代「未登记 emoji 不成卡」的行为一致。
    """
    match = _CALLOUT_LABEL_RE.match(body)
    if match is None:
        return None
    return CALLOUT_KINDS.get(match.group(1).strip())


def wrap_callouts(text):
    """把「**标签**：」开头的引用块包成 `<div class="callout callout-…">`（站点产物专用）。

    为什么不在 `docs/` 里直接写 div：`.md` 在 GitHub 上要能直接读，
    `<div markdown="1">` 会把原文切碎、也会让 `docs/` 的 diff 变吵。
    放生成阶段还有个好处：将来换视觉风格只改 CSS，不用动 58 个正文文件。

    `md_in_html` 的 `markdown="1"` 保证块内的粗体 / 链接 / 公式照常渲染。
    代码围栏内的 `>` 不动；不以已登记标签开头的引用块原样保留（它们仍会被
    theme.css 当作普通引用块统一排版）。

    **一个引用块里可以并排放着好几个提示**——章首固定是
    `> **学完你应能**：…` 紧跟一行 `> **公式速查**：…`（19 章全都如此）。所以按
    「这一行自身是不是以已登记标签开头」把块再切成子块，各自成卡；
    否则 19 张公式速查卡会被吞进目标卡里，白丢一类视觉信号（实测：切之前 calc 卡 0 张）。
    """
    lines = text.split("\n")
    out = []
    i, n = 0, len(lines)
    fence = None
    while i < n:
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = None if fence else stripped[:3]
            out.append(line)
            i += 1
            continue
        if fence or not line.startswith(">"):
            out.append(line)
            i += 1
            continue
        # 一整段引用块 = 连续的 '>' 行（单独一个 '>' 是块内空行）
        j = i
        while j < n and lines[j].startswith(">"):
            j += 1
        # 按「该行自身以标志性 emoji 开头」切子块（首行永远算新子块的开头）
        segs = []
        cur = []
        for b in lines[i:j]:
            if cur and _callout_kind(b[1:].lstrip()) is not None:
                segs.append(cur)
                cur = []
            cur.append(b)
        if cur:
            segs.append(cur)
        for seg in segs:
            head = next((b[1:].lstrip() for b in seg if b[1:].strip()), "")
            kind = _callout_kind(head)
            if kind is None:
                out.extend(seg)
                continue
            inner = [(b[1:][1:] if b[1:].startswith(" ") else b[1:]) for b in seg]
            while inner and not inner[-1].strip():
                inner.pop()
            out.append(f'<div class="callout callout-{kind}" markdown="1">')
            out.append("")
            out.extend(inner)
            out.append("")
            out.append("</div>")
        i = j
    return "\n".join(out)


# ---------------------------------------------------------------- 章首舞台
# 首页在 v3.50 就有了「舞台 + 点阵 + 辉光」的 hero，而 19 个正文章的开屏仍是
# 「光秃秃的 h1 + 三张灰底卡」，和首页相比落差最大的一处版面。v3.56 把每章
# 开头的 h1、引导句（普通引用块）与紧随其后的提示卡包进一层
# `<div class="chapter-hero" data-chapter="N">`，由 typography.css 画成与
# 首页同语言的章级舞台：品牌渐变底 + 蓝图点阵 + 右下角一枚巨大章号水印
# （水印是独立元素并 aria-hidden，读屏不会把「3」当正文念两遍）。
#
# 为什么在生成阶段包：docs/ 的 Markdown 还要直接喂 GitHub 渲染 README，
# 不能为了在线站外观塞 div（与 wrap_callouts 同一条理由）。
#
# 只包「章页」（pN-MM-chNN.md）且只在 h1 之后**连续**吞：普通引用块 + 提示卡
# div 块。一旦遇到第一个正文标题/图片/段落就停手——正文中间的提示卡一概不动。
#
# v3.57 把同一套包装推广到 9 个篇级落地页（pN-00-*.md → .part-hero，
# 水印是篇号）：首页 → 篇 → 章 三级开屏从此说同一种视觉语言。
_HERO_CALLOUT_OPEN = re.compile(r'^<div class="callout callout-[a-z]+" markdown="1">$')

# 19 章各有一枚手绘单线章徽（analog-book/static/illustrations/chNN.svg，与
# 篇首蚀刻版画同一套笔触）。构建期把它内联进章首舞台，站点 / A4 / 16K 共用
# 同一份 HTML；内联前逐项校验，避免矢量文件变成脚本或远程请求的入口。
EMBLEM_DIR = ROOT / "analog-book" / "static" / "illustrations"
EMBLEM_BANNED = ("<script", "<style", "<image", "<foreignobject", "<iframe",
                 "<object", "<embed", "xlink:", "data:", "@import", "url(",
                 "<!entity", "<!doctype")
EMBLEM_ATTR = re.compile(r"\s(?:id|href|on[a-z]+)\s*=", re.I)
EMBLEM_URL = re.compile(r"https?://[^\"'\s>]+")


def _emblem_problem(svg):
    """返回章徽的毛病；干净则返回空串。"""
    lowered = svg.lower()
    if not svg.startswith("<svg ") or "</svg>" not in svg:
        return "不是完整的 SVG"
    if 'viewBox="0 0 64 64"' not in svg:
        return "画布不是 64×64"
    if 'stroke="currentColor"' not in svg:
        return "笔画没有跟随 currentColor"
    if len(svg.encode("utf-8")) >= 6000:
        return "体积超过 6000 字节"
    for token in EMBLEM_BANNED:
        if token in lowered:
            return f"含不允许的内容（{token}）"
    if EMBLEM_ATTR.search(svg):
        return "含 id / href / 事件属性"
    if set(EMBLEM_URL.findall(svg)) - {"http://www.w3.org/2000/svg"}:
        return "含外部 URL"
    if re.search(r"[\u4e00-\u9fff]", svg):
        return "含中文（章徽只用笔画）"
    return ""


def chapter_emblem(number, art_dir=None):
    """读出第 N 章的单线章徽，并补上装饰性属性（aria-hidden 在构建期写入）。"""
    try:
        chapter = int(str(number).strip())
    except ValueError:
        raise ValueError(f"章号不是整数：{number!r}") from None
    if not 0 <= chapter <= 18:
        raise ValueError(f"章号不在 0~18：{chapter}")
    path = Path(art_dir or EMBLEM_DIR) / f"ch{chapter:02d}.svg"
    try:
        svg = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"章徽缺失：{path}") from exc
    problem = _emblem_problem(svg)
    if problem:
        raise ValueError(f"章徽 {path.name}：{problem}")
    # 用块级 div 包住：Markdown 会把裸 <svg> 当成行内元素塞进 <p>，
    # 空段落会在标题与场景卡之间撑出一条缝。
    return ('<div class="chapter-emblem" aria-hidden="true">'
            + svg + "</div>")


def _wrap_stage(text, page_name, page_re, kind, attr):
    m = page_re.fullmatch(page_name)
    if not m:
        return text
    number = m.group(1)
    lines = text.split("\n")
    start = next((k for k, ln in enumerate(lines) if ln.startswith("# ")), None)
    if start is None:
        return text
    j = start + 1
    consumed = False
    while j < len(lines):
        line = lines[j]
        if not line.strip():
            j += 1
            continue
        if line.startswith(">"):
            consumed = True
            j += 1
            continue
        if _HERO_CALLOUT_OPEN.match(line):
            consumed = True
            depth = 1
            j += 1
            while j < len(lines) and depth:
                if lines[j].startswith("<div "):
                    depth += 1
                elif lines[j].startswith("</div>"):
                    depth -= 1
                j += 1
            continue
        break
    if not consumed:
        return text          # h1 后面没有引导句 / 提示卡，没有舞台可包
    hero = [
        '<div class="%s" data-%s="%s" markdown="1">' % (kind, attr, number),
        "",
        lines[start],
    ]
    if kind == "chapter-hero":
        hero += ["", chapter_emblem(number)]
    hero += lines[start + 1:j]
    hero += [
        "",
        '<p class="%s-num" aria-hidden="true">%s</p>' % (kind, number),
        "</div>",
    ]
    return "\n".join(lines[:start] + hero + lines[j:])


def wrap_chapter_hero(text, page_name):
    """章页章首包成「章首舞台」（站点产物专用，见上方块注释）。"""
    return _wrap_stage(text, page_name, re.compile(r"p\d+-\d+-ch(\d+)\.md"),
                       "chapter-hero", "chapter")


def wrap_part_hero(text, page_name):
    """篇级落地页（pN-00-*.md，共 9 个）章首包成「篇首舞台」（站点产物专用）。

    与章首舞台同一套吞块规则与视觉语言，水印是篇号（1~9）。9 个篇首页都有
    引言引用块，所以「h1 后面必须有引导内容」的规则与章页共用；
    新篇页没写引言会被 test_site_build 的 9/9 舞台断言红出来提醒补上。
    """
    return _wrap_stage(text, page_name, re.compile(r"p(\d+)-00-[a-z0-9\-]+\.md"),
                       "part-hero", "part")


# 正文里每张动画下方都跟着一行 `[动画演示 N](p5-00-part5.md#demoNN)`，
# 此前渲染成普通段落，混在图与正文之间毫无存在感。v3.57 把这种**独立成行、
# 且只链到动画中心**的行（全站 107 处）包成 .demo-link 药丸（站点产物专用）。
# 一行双链的 combo 行（`…](#demo107) · [5.108](#demo108)`）同样整行入药丸；
# 只认「整行恰好由动画演示链接组成」：Falstad 交互链接、句中出现的链接一概不动。
# v3.72 起行首的 🔗 前缀随全书去表情标签取消，药丸样式本身足以标识。
_DEMO_LINK = re.compile(
    r"^(\[动画演示[^\]]*\]\(p5-00-part5\.md#demo\d+\)"
    r"(?: · \[[^\]]*\]\(p5-00-part5\.md#demo\d+\))*"
    r")$")


def wrap_demo_links(text):
    out = []
    for line in text.split("\n"):
        # rstrip 掉行尾空白（含 Windows 检出带来的 \r）：本地工作区可能是
        # CRLF，$ 锚点对 \r 不买账就会漏包，本地与 CI 的产物会差两行
        m = _DEMO_LINK.match(line.rstrip())
        if m:
            out += ['<div class="demo-link" markdown="1">', "", m.group(1), "", "</div>"]
        else:
            out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------- 标题层级归一
# 48 个页面（含全部 19 个正文章 + 6.x/7.x/8.x 分节页 + 前言/目录/更新日志）
# 用 `## 第 N 章 …` 当章标题，正文里一个 `# ` 都没有。后果是 Material 的
# `partials/content.html` 见 `page.content` 里没有 `<h1`，就先补一个来自 nav 的
# `<h1>`，正文再渲染一个**同名**的 `<h2>` —— 页面上标题出现两遍（实测 48/62 页）。
# 把正文标题整体上提一级后：① 同名重复消失（正文里有了 <h1>，主题就不再补）；
# ② 文档大纲变成规范的 h1→h2→h3（原来是 h2→h3→h4，凭空跳了一级，
# 屏幕阅读器与搜索引擎都读不到「这一页的主题」）。
_FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
_ATX = re.compile(r"^( {0,3})(#{1,6})(?=\s|$)(.*)$")
_FENCE_OPEN = re.compile(r"^[ \t]*(```|~~~)")
_ATX_H1 = re.compile(r"^ {0,3}#(?=\s|$)")


def shift_headings(text):
    """正文里没有 h1 时，把整页标题层级归一（站点产物专用）。

    规则两条：
      ① **第一个标题升为 `#`** —— 它就是这一页的主题；
      ② 其余标题各升一级，但**不高于 `##`**。

    第 ② 条不是凑数：「🙏 致谢」页有 `## 致谢` 与 `## 共建者墙` 两个同级标题，
    如果无脑全升一级，那一页会出**两个 h1**（实测踩过）。把第二个压在 `##` 上，
    「致谢 = 页标题、共建者墙 = 其中的一节」这层意思才落对。

    **只动真正的 ATX 标题行**：front-matter、代码围栏内、4 空格缩进的代码块、
    `>` 引用块、表格行一律不碰（正则锚在行首且只允许 ≤3 个前导空格）。
    整页**一个 `# ` 标题都没有**时才生效，有 h1 的 10 个篇首页原样返回 ——
    这样既不会和 `docs/` 里已有的 `#` 风格打架，也不会出现「一半归一一半没归」。
    """
    m = _FRONT_MATTER.match(text)
    fm, body = (m.group(0), text[m.end():]) if m else ("", text)
    lines = body.split("\n")

    def scan(lines):
        """产出 (行, 是否在围栏内) —— 两次扫描的围栏判定必须一致。

        围栏按「同一种围栏字符」配对：``` 里的 ~~~ 只是普通文本，反之亦然。
        """
        fence = None
        for ln in lines:
            f = _FENCE_OPEN.match(ln)
            if f:
                ch = f.group(1)[0]
                if fence is None:
                    fence = ch
                elif fence == ch:
                    fence = None
                yield ln, True
                continue
            yield ln, bool(fence)

    if any(_ATX_H1.match(ln) for ln, in_fence in scan(lines) if not in_fence):
        return text

    out = []
    seen_first = False
    for ln, in_fence in scan(lines):
        m2 = _ATX.match(ln) if not in_fence else None
        if not m2:
            out.append(ln)
            continue
        if not seen_first:
            seen_first = True
            level = 1
        else:
            level = max(len(m2.group(2)) - 1, 2)
        out.append(m2.group(1) + "#" * level + m2.group(3))
    return fm + "\n".join(out)


FM_DESC_MAX = 150
DESC_MIN = 30          # 摘要的最短可采纳长度（更短的几乎都是图注 / 链接行 / 残句）
_MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MD_CODE = re.compile(r"`([^`]*)`")
_MD_NOISE = re.compile(r"[*`$\\]")
# 只剥"认识"的标签：`I_C < 5mA, V > 2V` 这类含尖括号的正文不能被误删
_HTML_TAG = re.compile(
    r"</?(?:a|b|i|em|strong|code|kbd|sub|sup|br|p|span|div|img|figure|figcaption|"
    r"center|details|summary|blockquote|table|thead|tbody|tr|td|th|ul|ol|li|hr)\b[^>]*/?>",
    re.I)
_MATH = re.compile(r"\$([^$]+)\$")
_ENTITY = {"&lt;": "<", "&gt;": ">", "&amp;": "&", "&quot;": '"',
           "&#39;": "'", "&nbsp;": " "}
_ENTITY_RE = re.compile("|".join(map(re.escape, _ENTITY)))
_LATEX = re.compile(r"\\([a-zA-Z]+)")
_LATEX_MAP = {
    "approx": "≈", "times": "×", "cdot": "·", "ge": "≥", "le": "≤", "ne": "≠",
    "to": "→", "rightarrow": "→", "Rightarrow": "⇒", "pm": "±", "mu": "µ",
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "Delta": "Δ",
    "eta": "η", "theta": "θ", "lambda": "λ", "nu": "ν", "pi": "π", "rho": "ρ",
    "sigma": "σ", "Sigma": "Σ", "tau": "τ", "phi": "φ", "omega": "ω",
    "Omega": "Ω", "infty": "∞", "propto": "∝",
}
# 这些 LaTeX 结构压成纯文本必然走样（\frac{a}{b} -> fracab、\text{ms} -> textms），
# 含它们的段落宁可不做摘要——否则搜索结果里会出现 `τ=RC=1textms,quad tr≈2.2τ`
_HARD_TEX = re.compile(
    r"\\(?:frac|dfrac|tfrac|sqrt|text|mathrm|mathbf|begin|end|sum|int|lim|left|"
    r"right|overline|vec|hat|dot|partial|nabla)\b")
_FENCE = re.compile(r"^\s*(?:```|~~~)")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
_SEP_ROW = re.compile(r"^\|[\s\-:|]+\|$")
# 图片版权声明行（"以上图片：Wikimedia Commons，公有领域/CC 授权"）不是页面摘要
_CREDIT = re.compile(r"Wikimedia Commons|公有领域|CC[ -]?BY|版权|授权声明")
_LAST_UPDATE = re.compile(r"[，,；;、\s]*最后更新[：:][^\s。；;]*\s*$")
# ASCII 双引号 -> 中文弯引号：正文里写 "反型层"，直接塞进 <meta content="..."> 会把属性截断
_QUOTE_PAIR = re.compile(r'"([^"]*)"')
# 表格行 / 原始 HTML / admonition / 脚注 / 列表项 / 分隔线 —— 都不是正文段落
_SKIP = re.compile(r"^(?:\||<|!|\^\[|\[\^|[-*+]\s|\d+[.)]\s|[-*_]{3,}\s*$)")


def _demath(m):
    r"""把行内公式压成可读纯文本：$V_{BE}\approx0.7V$ -> VBE≈0.7V。"""
    s = _LATEX.sub(lambda g: _LATEX_MAP.get(g.group(1), g.group(1)), m.group(1))
    return s.replace("{", "").replace("}", "").replace("_", "").replace("^", "")


def _plain(s):
    """把一行 Markdown 压成纯文本：去链接语法 / 行内代码 / 公式 / 标记 / HTML 标签。"""
    s = _MD_LINK.sub(r"\1", s)
    s = _MD_CODE.sub(r"\1", s)     # 先取出代码内容，否则 build_readme.py 会被压成 buildreadme.py
    s = _ENTITY_RE.sub(lambda m: _ENTITY[m.group(0)], s)
    s = _HTML_TAG.sub("", s)
    s = _MATH.sub(_demath, s)
    s = _MD_NOISE.sub("", s)
    return re.sub(r"\s+", " ", s).strip()


def _cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


_CJK = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]")


def _join_lines(lines):
    """按 CJK 排版规则拼行：中文之间的软换行不补空格，英文之间才补。

    否则「…系统学习指南」+「仿《通往 AGI 之路》…」会拼成「指南 仿《…》」。
    """
    parts = [ln.strip() for ln in lines if ln.strip()]
    if not parts:
        return ""
    out = parts[0]
    for nxt in parts[1:]:
        sep = "" if (_CJK.search(out[-1]) and _CJK.search(nxt[0])) else " "
        out += sep + nxt
    return out


def _fit(s):
    """截到 FM_DESC_MAX 以内，尽量落在句号 / 分号处，不要在句子中间硬切。"""
    s = _LAST_UPDATE.sub("", s).strip()      # 末尾的「最后更新：2026-10」是噪声
    s = _QUOTE_PAIR.sub("\u201c\\1\u201d", s).replace('"', "\u201d")
    if len(s) <= FM_DESC_MAX:
        return s.rstrip("，,、；;：: ")
    cut = s[:FM_DESC_MAX]
    for sep in "。！？；":
        k = cut.rfind(sep)
        if k >= DESC_MIN:
            return cut[:k + 1]
    return cut.rstrip("，,、；;：: ")


def page_description(text):
    """为每页摘一句 meta description（写进站点产物的 front-matter）。

    SEO：原先 59 个页面共用同一句 site_description，搜索结果与社交卡片里全站摘要
    一模一样；MkDocs Material 优先用 front-matter 的 `description`，所以这里为每页
    生成一句独立的。

    做法：按文档顺序扫描，取**第一个够长的正文块**（普通段落，或开篇的引用块——
    篇首页 / 章首页的开场白正好写成 `>` 引用）。沿途跳过标题、表格、列表、原始
    HTML，**以及代码围栏内的全部内容**——曾经把 `p1-04-ch3.md` 里 ASCII 画的 BJT
    结构图当成了摘要（`│ N ├───┬───┤ N+ │`）；含 `\\frac` 之类压不成文字的公式的
    段落也跳过，否则摘要里会出现 `dfracR0VDD-VIN-VTH`。
    整页都是标题 + 表格/清单时（速查表、目录页），退回「标题（表格列名）」。
    """
    # 相邻的引用行合成一段（`> a` / `> b` 是同一段开场白），并去掉行首的 `>`
    lines: list[str] = []
    for raw in text.split("\n"):
        if raw.strip().startswith(">") and lines and lines[-1].strip().startswith(">"):
            lines[-1] = _join_lines([lines[-1], re.sub(r"^>+\s*", "", raw.strip())])
        else:
            lines.append(raw)

    title = ""
    cols: list[str] = []
    bullet = ""
    cands: list[tuple[int, str]] = []      # (在文中的行号, 候选摘要)
    buf: list[str] = []
    buf_at = 0
    in_fence = False

    def close_buf():
        if buf:
            raw = _join_lines(buf)
            body = _plain(raw)
            # 图片版权声明（"以上图片：Wikimedia Commons…"）不是页面摘要
            if (len(body) >= DESC_MIN and not _HARD_TEX.search(raw)
                    and not _CREDIT.search(body)):
                cands.append((buf_at, body))
            buf.clear()

    for i, raw in enumerate(lines):
        if _FENCE.match(raw):            # ``` / ~~~ 围栏：连同围栏内的内容整块丢弃
            in_fence = not in_fence
            close_buf()
            continue
        if in_fence:
            continue
        s = raw.strip()
        if not s:
            close_buf()
            continue
        m = _HEADING.match(s)
        if m:
            close_buf()
            if not title:
                title = _plain(m.group(1))
            continue
        if s.startswith(">"):
            close_buf()
            body = _plain(s.lstrip("> ").strip())
            # 「**先修**」这类提示块不是正文摘要
            if (len(body) >= DESC_MIN and "**先修**" not in s
                    and not _HARD_TEX.search(s)
                    and not _CREDIT.search(body)):
                cands.append((i, body))
            continue
        if s.startswith("|"):
            close_buf()
            if not cols:                 # 表头行 = 下一行是 |---|---| 分隔行
                nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if _SEP_ROW.match(nxt):
                    cols = [c for c in map(_plain, _cells(s)) if c]
            continue
        if len(_MD_LINK.findall(s)) >= 3:     # 一串链接 = 导航行，不是正文
            close_buf()
            continue
        if _SKIP.match(s):
            close_buf()
            if not bullet:
                m2 = re.match(r"^(?:[-*+]|\d+[.)])\s+(.*)$", s)
                if m2:
                    body = _plain(m2.group(1))
                    if 6 <= len(body) <= 40:
                        bullet = body
            continue
        if not buf:
            buf_at = i
        buf.append(s)
    close_buf()

    if cands:
        return _fit(min(cands, key=lambda c: c[0])[1])
    if title:
        tail = " · ".join(cols) if cols else bullet
        return _fit(title + ("（%s）" % tail if tail else ""))
    return ""


def with_description(text):
    """Explicit titles keep pre-heading anchors from confusing MkDocs' title lookup."""
    desc = page_description(text)
    if not desc:
        return text
    title = content_title(text)
    return (f"---\ndescription: {json.dumps(desc, ensure_ascii=False)}\n"
            f"title: {json.dumps(title, ensure_ascii=False)}\n---\n\n" + text)


def content_title(text):
    for line in text.splitlines():
        match = _HEADING.match(line)
        if match:
            return _plain(match.group(1))
    return ''


CHAPTER_LABEL = {
    "0": "§0 电路直觉", "1": "§1 无源元件", "2": "§2 二极管", "3": "§3 BJT",
    "4": "§4 MOSFET", "5": "§5 推挽/开漏", "6": "§6 运放", "7": "§7 比较器",
    "8": "§8 模拟开关", "9": "§9 基准稳压", "10": "§10 555",
    "11": "§11 放大拓扑", "12": "§12 运放族", "13": "§13 电源振荡",
    "14": "§14 设计方法", "15": "§15 PCB", "16": "§16 排故", "17": "§17 速查",
    "18": "§18 大师智慧",
}
APPENDIX = {"p9-12-changelog.md", "p9-13-thanks.md", "p9-14-credits.md",
            "p9-15-glossary.md"}

GALLERY_CSS = """
/* 动画 <img> 被包进 <picture>（为了让 <source media> 能在页面上下文里挑「静止版」）。
   display:contents 让 <picture> 对布局完全透明，img 的排版与包之前一模一样。 */
picture{display:contents}
.gal-bar{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;margin:.6rem 0 1.2rem}
.gal-bar input[type=search]{flex:1 1 220px;min-width:180px;padding:.45rem .7rem;border-radius:.5rem;
  border:1px solid var(--md-default-fg-color--lightest);background:var(--md-code-bg-color);
  color:var(--md-default-fg-color)}
.gal-chip{padding:.3rem .7rem;border-radius:999px;border:1px solid var(--md-default-fg-color--lightest);
  background:transparent;color:var(--md-default-fg-color);cursor:pointer;font-size:.75rem}
.gal-chip[aria-pressed=true]{background:var(--md-primary-fg-color);color:var(--md-primary-bg-color);
  border-color:var(--md-primary-fg-color)}
/* 暗色下 --md-primary-fg-color 是浅青 #7fb7cf，白字只有 2.2:1 —— 压上深墨字 */
[data-md-color-scheme="slate"] :is(.gal-chip[aria-pressed=true],.gal-random:hover,.gal-play:hover){color:#1d1a14}
.gal-bar input[type=search]::placeholder{color:#655f52}
[data-md-color-scheme="slate"] .gal-bar input[type=search]::placeholder{color:#9aa0a6}
.gal-icon{width:.85em;height:.85em;vertical-align:-.1em}
.gal-random{padding:.3rem .7rem;border-radius:999px;cursor:pointer;font-size:.75rem;font-weight:600;
  border:1px dashed var(--md-primary-fg-color);background:transparent;color:var(--md-primary-fg-color)}
.gal-random:hover{background:var(--md-primary-fg-color);color:var(--md-primary-bg-color)}
.gal-hint{margin:-.6rem 0 1rem;font-size:.72rem;opacity:.72}
.gal-hint kbd{border:1px solid var(--md-default-fg-color--lightest);border-radius:.25rem;
  padding:0 .3rem;font-size:.7rem}
.gal-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:1rem}
.gal-card{border:1px solid var(--md-default-fg-color--lightest);border-radius:.6rem;overflow:hidden;
  background:var(--md-code-bg-color);transition:transform .15s ease,box-shadow .15s ease;
  display:flex;flex-direction:column}
.gal-card:hover{transform:translateY(-2px);box-shadow:0 4px 14px rgba(0,0,0,.18)}
.gal-card>a{display:block;text-decoration:none;color:inherit;flex:1 1 auto}
.gal-card img{display:block;width:100%;height:auto;background:#fff}
.gal-meta{padding:.5rem .7rem .7rem}
.gal-title{font-weight:600;font-size:.85rem;line-height:1.35;margin-bottom:.25rem}
.gal-tag{font-size:.7rem;opacity:.75}
.gal-empty{opacity:.7;font-size:.9rem}
.gal-actions{padding:0 .7rem .7rem}
.gal-play{width:100%;padding:.35rem .6rem;border-radius:.4rem;cursor:pointer;font-size:.75rem;font-weight:600;
  border:1px solid var(--md-primary-fg-color);background:transparent;color:var(--md-primary-fg-color)}
.gal-play:hover{background:var(--md-primary-fg-color);color:var(--md-primary-bg-color)}
.gal-modal{position:fixed;inset:0;z-index:9999;display:none;align-items:center;justify-content:center;
  background:rgba(0,0,0,.8);padding:2vh 2vw}
.gal-modal.is-open{display:flex}
.gal-modal-box{max-width:min(1100px,94vw);max-height:94vh;overflow:auto;padding:.8rem;border-radius:.6rem;
  background:var(--md-default-bg-color)}
.gal-modal-bar{display:flex;gap:.6rem;align-items:center;justify-content:space-between;flex-wrap:wrap;
  margin-bottom:.5rem}
.gal-modal-title{font-weight:700;font-size:.9rem}
.gal-modal-tools{display:flex;gap:.4rem;align-items:center;flex-wrap:wrap}
.gal-pos{font-size:.72rem;opacity:.75;min-width:4.2rem;text-align:center}
.gal-nav,.gal-modal-close{padding:.25rem .6rem;border-radius:.4rem;cursor:pointer;font-size:.78rem;
  border:1px solid var(--md-default-fg-color--lightest);background:transparent;color:inherit}
.gal-nav:hover{border-color:var(--md-primary-fg-color);color:var(--md-primary-fg-color)}
.gal-modal-box img{display:block;width:100%;height:auto;background:#fff;border-radius:.35rem}
.gal-modal-foot{margin-top:.5rem;font-size:.78rem}
.gal-modal-foot a{font-weight:600}
/* 尊重系统的「减弱动效」偏好：卡片悬停不再位移，只换阴影。
   动画 SVG 自身的动效不在这里管 —— 那由 <picture><source media> 挑静止版，
   见本文件顶部的 REDUCE_CSS / wrap_picture()。 */
@media (prefers-reduced-motion: reduce){
.gal-card{transition:none}
.gal-card:hover{transform:none}
}
"""

GALLERY_JS = """
(function () {
  function init() {
    var cards = Array.prototype.slice.call(document.querySelectorAll('.gal-card'));
    if (!cards.length) { return; }
    var search = document.getElementById('gal-search');
    var chips = Array.prototype.slice.call(document.querySelectorAll('.gal-chip'));
    var empty = document.getElementById('gal-empty');
    var counter = document.getElementById('gal-count');
    var randomBtn = document.getElementById('gal-random');
    var state = { ch: 'all', q: '' };
    var visible = cards.slice();

    /* ---------- 筛选状态可分享：?ch=12&q=米勒 ---------- */
    function readUrl() {
      var p;
      try { p = new URLSearchParams(window.location.search); } catch (e) { return; }
      var chapter = p.get('ch');
      if (chips.some(function (c) { return c.dataset.ch === chapter; })) { state.ch = chapter; }
      if (p.get('q')) { state.q = p.get('q').trim().toLowerCase(); }
    }
    function writeUrl() {
      if (!window.history || !window.history.replaceState) { return; }
      var p = new URLSearchParams(window.location.search);
      p.delete('ch'); p.delete('q');
      if (state.ch && state.ch !== 'all') { p.set('ch', state.ch); }
      if (state.q) { p.set('q', state.q); }
      var qs = p.toString();
      window.history.replaceState(window.history.state, '',
        window.location.pathname + (qs ? '?' + qs : '') + window.location.hash);
    }

    function paintChips() {
      chips.forEach(function (c) {
        c.setAttribute('aria-pressed', String(c.dataset.ch === state.ch));
      });
    }
    function apply() {
      visible = [];
      cards.forEach(function (c) {
        var okCh = (state.ch === 'all') || (c.dataset.ch === state.ch);
        var hay = ((c.dataset.title || '') + ' ' + (c.dataset.file || '')).toLowerCase();
        var okQ = !state.q || hay.indexOf(state.q) >= 0;
        var ok = okCh && okQ;
        c.style.display = ok ? '' : 'none';
        if (ok) { visible.push(c); }
      });
      if (empty) { empty.style.display = visible.length ? 'none' : ''; }
      if (counter) { counter.textContent = visible.length + ' / ' + cards.length; }
      if (randomBtn) { randomBtn.disabled = !visible.length; }
      paintChips();
    }

    readUrl();
    if (search) { search.value = state.q; }
    apply();

    if (search) {
      search.addEventListener('input', function () {
        state.q = search.value.trim().toLowerCase();
        apply(); writeUrl();
      });
    }
    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        state.ch = chip.dataset.ch;
        apply(); writeUrl();
      });
    });

    /* ---------- lightbox：放大播放 + 上一张/下一张 ---------- */
    var modal = document.getElementById('gal-modal');
    if (!modal) { return; }
    var mImg = document.getElementById('gal-modal-img');
    var mTitle = document.getElementById('gal-modal-title');
    var mLink = document.getElementById('gal-modal-link');
    var mClose = document.getElementById('gal-modal-close');
    var mPrev = document.getElementById('gal-modal-prev');
    var mNext = document.getElementById('gal-modal-next');
    var mPos = document.getElementById('gal-modal-pos');
    var current = -1;
    var returnFocus = null;
    var previousOverflow = '';

    /* 弹窗里是 <img>，没法用 <picture>，所以在这里手动挑源。
       SVG 作为 <img> 载入时 Chrome 恒把 prefers-reduced-motion 判为 reduce，
       偏好只能由页面来判 —— 与卡片上的 <source media> 同一个道理。 */
    function pickSvg(src) {
      var q = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
      /* 用切片而不是正则：GALLERY_JS 是普通字符串，正则里的转义点号会触发 Python 告警 */
      return (q && q.matches) ? src.slice(0, -4) + '.reduce.svg' : src;
    }

    function show(card) {
      var btn = card.querySelector('.gal-play');
      if (!btn) { return; }
      mImg.setAttribute('src', pickSvg(btn.dataset.svg));
      mImg.setAttribute('alt', btn.dataset.title);
      mTitle.textContent = btn.dataset.title;
      if (mLink) { mLink.setAttribute('href', btn.dataset.href); }
      /* current 是"当前可见列表"里的下标；被筛掉的卡片开出来时没有位置信息 */
      current = visible.indexOf(card);
      var many = current >= 0 && visible.length > 1;
      if (mPos) { mPos.textContent = current >= 0 ? (current + 1) + ' / ' + visible.length : ''; }
      if (mPrev) { mPrev.style.visibility = many ? '' : 'hidden'; }
      if (mNext) { mNext.style.visibility = many ? '' : 'hidden'; }
    }
    function isOpen() { return modal.classList.contains('is-open'); }
    function openModal(card) {
      if (!isOpen()) {
        returnFocus = document.activeElement;
        previousOverflow = document.body.style.overflow;
      }
      show(card);
      modal.classList.add('is-open');
      document.body.style.overflow = 'hidden';
      if (mClose) { mClose.focus(); }
    }
    function closeModal() {
      if (!isOpen()) { return; }
      modal.classList.remove('is-open');
      mImg.removeAttribute('src');
      document.body.style.overflow = previousOverflow;
      current = -1;
      if (returnFocus && returnFocus.isConnected) { returnFocus.focus(); }
    }
    function step(delta) {
      if (!isOpen() || !visible.length) { return; }
      var base = current < 0 ? (delta > 0 ? -1 : 0) : current;
      show(visible[(base + delta + visible.length) % visible.length]);
    }

    document.addEventListener('click', function (e) {
      var t = e.target;
      var closest = (t && t.closest) ? function (sel) { return t.closest(sel); } : function () { return null; };
      var play = closest('.gal-play');
      if (play) { e.preventDefault(); openModal(play.closest('.gal-card')); return; }
      if (closest('#gal-modal-prev')) { step(-1); return; }
      if (closest('#gal-modal-next')) { step(1); return; }
      if (t === modal || closest('#gal-modal-close')) { closeModal(); }
    });

    document.addEventListener('keydown', function (e) {
      if (e.defaultPrevented || e.isComposing || e.ctrlKey || e.altKey || e.metaKey) { return; }
      if (e.key === 'Escape') { closeModal(); return; }
      if (!isOpen()) {
        var target = e.target;
        var editing = target && (target.isContentEditable ||
          (target.closest && target.closest('input, textarea, select, [role="textbox"]')));
        if (e.key === '/' && search && !editing) {
          e.preventDefault(); search.focus();
        }
        return;
      }
      if (e.key === 'Tab') {
        var focusable = Array.prototype.slice.call(modal.querySelectorAll('button, a[href]'))
          .filter(function (el) {
            return !el.disabled && el.getClientRects().length &&
              window.getComputedStyle(el).visibility !== 'hidden';
          });
        var first = focusable[0], last = focusable[focusable.length - 1];
        if (focusable.indexOf(document.activeElement) < 0 ||
            (e.shiftKey && document.activeElement === first) ||
            (!e.shiftKey && document.activeElement === last)) {
          e.preventDefault();
          (e.shiftKey ? last : first).focus();
        }
      }
      if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
    });

    if (randomBtn) {
      randomBtn.addEventListener('click', function () {
        if (!visible.length) { return; }
        var pick = visible[Math.floor(Math.random() * visible.length)];
        if (pick.scrollIntoView) { pick.scrollIntoView({ block: 'center' }); }
        openModal(pick);
      });
    }
  }

  if (document.readyState !== 'loading') { init(); }
  else { document.addEventListener('DOMContentLoaded', init); }
})();
"""

# ---------------------------------------------------------------------------
# Material 主题补丁：让「篇首页」真的当上节首页（navigation.indexes）
# ---------------------------------------------------------------------------
# Material 的 navigation.indexes 只认 MkDocs 的 `Page.is_index`，而那个属性的
# 定义就是 `self.file.name == 'index'`（README.md 会被归一成 index）。本站的篇首页
# 叫 `p1-00-part1.md`，主干是 `p1-00-part1` —— 于是这个特性**完全没生效**：
#   ① 节标题退化成纯折叠标签（点它只能展开，进不了篇首页）；
#   ② 篇首页又以普通子项出现在列表首位，标题与节标题**一字不差**。
# 结果：侧栏里每个篇标题都重复一行，9 篇共 9 处。而 build_nav() 里那句
# 「配合 navigation.indexes，点击节名即进入该页」的意图其实一直没兑现。
#
# 修法：不重命名文件（那会动 URL、锚点与 README），而是对上游模板打一个最小补丁 ——
# 把「**首个标题与节标题相同的叶子页**」也算作该节的 index。判据挑「标题相同」是因为
# 重复的根源正是这两处标题相同；`not item.children` 保证它必须是页面而不是子节。
# 这样节标题变成链接（点进篇首页）、右侧只留一个展开箭头，篇首页不再重复出现在子列表。
#
# **刻意不复制整份模板**：每次构建都从已安装的 Material 取原文再打补丁，
# 所以升级 Material 不会留下过期的副本；上游一旦改了这段锚点，
# nav_item_override() 会直接抛错（而不是静默产出一个不对的侧栏），
# `test_site_build.py` 也会变红。
NAV_ITEM_ANCHOR = '''    {% set _ = namespace(index = none) %}
    {% if "navigation.indexes" in features %}
      {% for item in nav_item.children %}
        {% if item.is_index and _.index is none %}
          {% set _.index = item %}
        {% endif %}
      {% endfor %}
    {% endif %}
    {% set index = _.index %}'''

NAV_ITEM_PATCHED = '''    {% set _ = namespace(index = none) %}
    {% if "navigation.indexes" in features %}
      {% for item in nav_item.children %}
        {% if _.index is none and (item.is_index or (not item.children and item.title == nav_item.title)) %}
          {% set _.index = item %}
        {% endif %}
      {% endfor %}
    {% endif %}
    {% set index = _.index %}'''


def nav_item_override(source=None):
    """取上游 nav-item.html，打上「篇首页即节首页」的补丁后返回。

    锚点必须**恰好出现一次**：找不到（Material 改了结构）就抛错，
    宁可构建失败也不要静默生成一个篇标题重复的侧栏。

    `source` 只给测试用（喂一份没有锚点的文本，验证它确实会响亮地失败）——
    因此 `import material` 只在真的要去读上游模板时才做。
    """
    if source:
        src = Path(source)
    else:
        import material
        src = (Path(material.__file__).parent / "templates" / "partials" / "nav-item.html")
    text = src.read_text(encoding="utf-8")
    if text.count(NAV_ITEM_ANCHOR) != 1:
        raise SystemExit(
            "Material 的 partials/nav-item.html 结构变了："
            "navigation.indexes 那段锚点找不到或出现多次。\n"
            "请重新核对 build_site.NAV_ITEM_ANCHOR / NAV_ITEM_PATCHED 这对补丁"
            "（补丁的作用见上方注释），改完再构建。")
    return text.replace(NAV_ITEM_ANCHOR, NAV_ITEM_PATCHED)


OVERRIDES_MAIN_HTML = """{% extends "base.html" %}

{% block extrahead %}
  {{ super() }}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{{ config.site_name }}">
  <meta property="og:title" content="{{ page.title | default(config.site_name, true) | e }}">
  <meta property="og:description" content="{{ ((page.meta or {}).get('description') or config.site_description) | e }}">
  {% if page.canonical_url %}<meta property="og:url" content="{{ page.canonical_url }}">{% endif %}
  <meta property="og:image" content="__OG_IMAGE__">
  <meta property="og:image:width" content="__OG_WIDTH__">
  <meta property="og:image:height" content="__OG_HEIGHT__">
  <meta property="og:image:alt" content="{{ config.site_name }} —— {{ config.site_description }}">
  <meta property="og:locale" content="zh_CN">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{{ page.title | default(config.site_name, true) | e }}">
  <meta name="twitter:description" content="{{ ((page.meta or {}).get('description') or config.site_description) | e }}">
  <meta name="twitter:image" content="__OG_IMAGE__">
  <meta name="twitter:image:alt" content="{{ config.site_name }} —— {{ config.site_description }}">
  <meta name="theme-color" content="#3f51b5">
  <meta name="author" content="zhuguang-ZFG">

  {# 结构化数据：站点一个 WebSite 节点 + 每页一个 WebPage/TechArticle 节点。
     用 Jinja 的 tojson 而不是手拼字符串 —— 它会把 < > & 转成 \\uXXXX，
     正文里出现的尖括号（公式、标签）不会把 <script> 提前截断。
     不写 SearchAction：本站搜索是主题的模态框，没有 ?q= 形式的 URL，
     声明了就是骗爬虫。 #}
  <script type="application/ld+json">{{ {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        "@id": config.site_url ~ "#website",
        "url": config.site_url,
        "name": config.site_name,
        "description": config.site_description,
        "inLanguage": "zh-CN",
        "license": "https://creativecommons.org/licenses/by-sa/4.0/"
      },
      {
        "@type": "WebPage" if page.is_homepage else "TechArticle",
        "@id": (page.canonical_url or config.site_url) ~ "#page",
        "headline": page.title | default(config.site_name, true),
        "description": (page.meta or {}).get('description') or config.site_description,
        "url": page.canonical_url or config.site_url,
        "inLanguage": "zh-CN",
        "isPartOf": {"@id": config.site_url ~ "#website"},
        "author": {"@type": "Person", "name": "zhuguang-ZFG"},
        "publisher": {"@type": "Organization", "name": config.site_name,
                      "url": config.site_url},
        "license": "https://creativecommons.org/licenses/by-sa/4.0/",
        "image": "__OG_IMAGE__"
      }
    ]
  } | tojson }}</script>
{% endblock %}
"""

# 自托管分享卡：scripts/build_og_image.py 渲染的 1200×630 卡片，产物提交进仓库
# （assets/og-cover.png），随站点一起发布。原来外链 Wikimedia 的电路板照片：
# 跨域抓取常超时、且与本站内容无关，分享出去看不出是「模拟电路教程」。
OG_IMAGE = "https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/assets/og-cover.png"
OG_WIDTH, OG_HEIGHT = 1200, 630

ROBOTS_TXT = """User-agent: *
Allow: /

Sitemap: https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/sitemap.xml
"""

FEEDBACK_FOOTER = """
---

> **参与共建**：发现错别字、公式错误或失效链接？[提一个纠错 Issue](https://github.com/zhuguang-ZFG/analog-circuit-roadmap/issues/new?template=content-fix.yml) ·
> 想补充新主题、新动画或新资源？[提个建议](https://github.com/zhuguang-ZFG/analog-circuit-roadmap/issues/new?template=new-topic.yml) ·
> 想直接动手改：[共建指南](CONTRIBUTING.md) · [共建者墙](CONTRIBUTORS.md)
"""


MATHJAX_JS = r"""
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"], ["$", "$"]],
    displayMath: [["\\[", "\\]"], ["$$", "$$"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: { ignoreHtmlClass: ".*|", processHtmlClass: "arithmatex" },
  startup: {
    pageReady: function () {
      var rendered = document.querySelector('.md-content__inner');
      return MathJax.startup.defaultPageReady().then(function () {
        var queue = Promise.resolve();
        var revision = 0;
        function typesetPage() {
          var content = document.querySelector('.md-content__inner');
          var ticket = ++revision;
          queue = queue.then(function () {
            if (!content || !content.isConnected || ticket !== revision || content === rendered) return;
            MathJax.typesetClear();
            MathJax.texReset();
            // Instant navigation replaces <head>; cached CHTML styles are detached.
            MathJax.startup.output.clearCache();
            return MathJax.typesetPromise([content]).then(function () { rendered = content; });
          }).catch(function () {
            if (!content || !content.isConnected || content.querySelector('.math-status')) return;
            var note = document.createElement('p');
            note.className = 'math-status';
            note.setAttribute('role', 'status');
            note.textContent = '部分公式未能排版，可刷新重试。';
            content.prepend(note);
          });
        }
        if (typeof document$ !== 'undefined') document$.subscribe(typesetPage);
      });
    }
  }
};
"""

MKDOCS_YML = """site_name: 通往模拟电路之路
site_description: 从欧姆定律到芯片内部结构 —— 原理推导 + 器件剖析 + 故障分析 + 153 张 SVG 动画
site_url: https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/
repo_url: https://github.com/zhuguang-ZFG/analog-circuit-roadmap
# 顶栏右上角那个仓库链接显示的就是这个串，而 Material 给它的宽度是**固定**的
# （`.md-header__source` 在桌面上限死 11.5rem，跟视口宽度无关），所以写全路径
# `zhuguang-ZFG/analog-circuit-roadmap` 会被 CSS 截成 `zhuguang-ZFG/analog-ci…`
# —— 顶栏上挂着一个省略号，是每页都看得见的一处毛刺。GitHub 图标已经说明了
# 平台，文字只留平台名即可（这也是 MkDocs 在 host 为 github.com 时的默认值）。
repo_name: GitHub
edit_uri: edit/main/docs/
copyright: CC BY-SA 4.0

docs_dir: docs
site_dir: site
# 页面保持平铺（不带目录 URL），使正文里相对路径的 SVG 引用在各页都能解析
use_directory_urls: false

theme:
  name: material
  language: zh
  font: false
  custom_dir: overrides
  # 品牌标识：不用 Material 自带的「一本白书」（跟模拟电路毫无关系）。
  # 这里的值对应 custom_dir 下的 `.icons/analog-circuit.svg` —— 由 main()
  # 从 scripts/site_media/logo.svg 拷进去。写成 icon.logo 而不是 theme.logo，
  # 是为了让 SVG **内联**进 HTML：logo 就能用 currentColor 跟着顶栏文字色走，
  # 浅色/深色主题与悬停态都不用再管。
  icon:
    logo: analog-circuit
  # favicon 也是自绘的（scripts/build_favicon.py 渲染、产物提交进仓库）。
  # 路径相对 docs_dir；assets/ 由 main() 整棵拷进站点源，所以这里指得到。
  favicon: assets/images/favicon.png
  features:
    - navigation.instant
    # 刻意**不开** navigation.tracking。它会把「读到哪一段」实时写进 URL
    # （滚动 250ms 后 replaceState 成当前目录项的 #锚点），而 navigation.instant
    # 换页时会把**上一个页面** URL 上的哈希搬到新页面来 —— 于是从滚动过的首页
    # 点进第 0 章，落地地址可能是 p1-01-ch0.html#_2，而 `_2` 是首页的自动标题 id，
    # 在章节页根本不存在：复制这个地址出去，读者落在页首、还带个莫名碎片。
    # 正常节奏下本地复现不了那个搬运窗口，CPU 节流 8× 就够了：滚动过的首页地址
    # 6/6 挂着 #_2（关掉 tracking 后 6/6 干净），换页落地 3 次里 2 次地址被改写。
    # 护栏是 test_reading_journey 的
    # test_scrolling_and_page_switch_keep_the_link_target_in_the_url。
    # 「记录阅读位置」这件事本站已经用自己的 progress.js 做得更准
    # （remember() + 首页「继续上次阅读」），不需要 URL 再承担一遍。
    - navigation.sections
    - navigation.top
    - navigation.indexes
    - content.action.edit
    - content.code.copy
    - search.highlight
    - search.suggest
    - search.share
    - toc.follow
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/weather-night
        name: 切换到深色
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/weather-sunny
        name: 切换到浅色

# 中文搜索必须显式声明 search 插件：
#   1. 分词靠 jieba，它在构建期把正文里的汉字串切成词、词间插 U+200B，
#      再交给前端按 separator 切开建索引。jieba 没装时 Material 会静默跳过
#      整条链路（页面照常生成、搜索框照常出现），任何中文关键词都返回 0 条。
#      requirements.txt 声明 jieba，test_reading_journey.py 验证实际检索结果。
#   2. lang 必须显式写 zh。主题语言虽是 zh，但 zh 语言包只定义了 separator、
#      没有 search.config.lang 键，不写就会退回 en，拿不到 lunr 的中文
#      trimmer / 停用词表。
#   3. jieba_dict_user 是「本书术语表」，把相位裕度 / 共模抑制比 / 去耦电容
#      这类被默认词典切碎的领域词钉成整词，否则整词检索必然落空。
plugins:
  - search:
      lang: zh
      jieba_dict_user: scripts/jieba_user_dict.txt

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/zhuguang-ZFG/analog-circuit-roadmap
      name: GitHub 仓库
    - icon: fontawesome/solid/pen-to-square
      link: https://github.com/zhuguang-ZFG/analog-circuit-roadmap/issues/new/choose
      name: 提 Issue（纠错 / 建议）

extra_css:
  - stylesheets/typography.css
  - stylesheets/gallery.css
  - stylesheets/learning.css
  - stylesheets/visual-player.css
  - stylesheets/reading.css
  - stylesheets/diag.css
  - stylesheets/handraw.css

extra_javascript:
  - javascripts/mathjax.js
  - assets/vendor/mathjax/tex-chtml-full.js
  - javascripts/gallery.js
  - javascripts/learning.js
  - javascripts/visual-player.js
  - javascripts/reading.js
  - javascripts/learning-catalog.js
  - javascripts/progress.js
  - javascripts/diag.js
  - javascripts/calc.js

markdown_extensions:
  - abbr
  - admonition
  - attr_list
  - def_list
  - footnotes
  - md_in_html
  - tables
  - toc:
      permalink: true
  - pymdownx.details
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.tabbed:
      alternate_style: true
  # ASCII → 排版符号：(c) → ©、+/- → ±、--> → →、3rd → 3<sup>rd</sup>、1/2 → ½。
  # ⚠️ 它也会把「第 3/4 章」这种**章号区间**误当成 ¾ —— 见 scripts/test_smartsymbols.py
  # 的护栏（docs/ 里出现裸分数即红灯，逼作者改写成「第 3、4 章」）。
  - pymdownx.smartsymbols

nav:
__NAV__
"""

def parse_demos():
    lines = (DOCS / "p5-00-part5.md").read_text(encoding="utf-8").split("\n")

    chapter_of = {}
    for ln in lines:
        m = CHAPTER_ROW.match(ln)
        if not m:
            continue
        for _num, demo in DEMO_LINK.findall(ln):
            chapter_of[demo] = m.group(1)

    items = []
    cur = None
    for ln in lines:
        m = DEMO_HEAD.match(ln)
        if m:
            if cur and cur.get("svg"):
                items.append(cur)
            cur = {"num": m.group(1), "title": m.group(2).strip(),
                   "anchor": m.group(3), "svg": "", "alt": "", "ch": ""}
            continue
        if cur and not cur.get("svg"):
            im = DEMO_IMG.search(ln)
            if im:
                cur["svg"] = im.group(1)
                cur["alt"] = im.group(2)
    if cur and cur.get("svg"):
        items.append(cur)
    for it in items:
        it["ch"] = chapter_of.get(it["anchor"], "")
        it["w"], it["h"] = svg_size(it.get("svg", ""))
    return items, chapter_of


def render_gallery(items):
    chips = ['<button class="gal-chip" data-ch="all" aria-pressed="true">全部 %d</button>'
             % len(items)]
    seen = []
    for it in items:
        if it["ch"] and it["ch"] not in seen:
            seen.append(it["ch"])
    for ch in sorted(seen, key=lambda x: int(x)):
        n = sum(1 for i in items if i["ch"] == ch)
        chips.append('<button class="gal-chip" data-ch="%s" aria-pressed="false">%s · %d</button>'
                     % (ch, CHAPTER_LABEL.get(ch, "§" + ch), n))

    cards = []
    for it in items:
        title = it["title"].replace('"', "&quot;")
        href = "p5-00-part5.html#%s" % it["anchor"]
        full = "assets/" + it["svg"]
        # legacy（svg/ 开头）有 .reduce.svg 静止版，包 <picture> 降级；
        # svg-v2 尚无 reduce 变体，与全书 wrap_picture 的既有 v2 行为一致：直出 <img>。
        if it["svg"].startswith("svg/"):
            media = ('<picture><source srcset="assets/%s" '
                     'media="(prefers-reduced-motion: reduce)">'
                     '<img src="%s" alt="%s" width="%d" height="%d" '
                     'loading="lazy" decoding="async"></picture>'
                     % (reduce_variant(it["svg"]), full, it["alt"], it["w"], it["h"]))
        else:
            media = ('<img src="%s" alt="%s" width="%d" height="%d" '
                     'loading="lazy" decoding="async">'
                     % (full, it["alt"], it["w"], it["h"]))
        cards.append(
            '<div class="gal-card" data-ch="%s" data-title="%s" data-file="%s">\n'
            '  <a href="%s" title="%s">\n'
            '    %s\n'
            '    <div class="gal-meta">\n'
            '      <div class="gal-title">%s %s</div>\n'
            '      <div class="gal-tag">%s</div>\n'
            '    </div>\n'
            '  </a>\n'
            '  <div class="gal-actions">\n'
            '    <button class="gal-play" type="button" data-svg="%s" '
            'data-title="%s %s" data-href="%s"><svg class="gal-icon" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.1 5.3 L18.6 12 L8.4 18.7 Z"/></svg> 放大播放</button>\n'
            '  </div>\n'
            '</div>'
            % (it["ch"], title.lower(), it["svg"], href, title, media,
               it["num"], it["title"],
               CHAPTER_LABEL.get(it["ch"], "动画"),
               full, it["num"], title, href)
        )

    return "\n".join([
        "# 动画画廊",
        "",
        "> 全部 %d 张 SMIL 动画，可按章筛选、按标题搜索；"
        "点「放大播放」在弹窗里全尺寸观看（动画会自动播放），"
        "点卡片标题区直达该动画在 [动画演示中心](p5-00-part5.md)里的讲解与看点。" % len(items),
        "",
        '<div class="gal-bar">',
        '  <input id="gal-search" type="search" aria-label="搜索动画" placeholder="搜索：米勒 / LDO / 迟滞 / mosfet …">',
        "  " + "\n  ".join(chips),
        '  <button class="gal-random" id="gal-random" type="button">随机一张</button>',
        '  <span class="gal-tag" id="gal-count" role="status" aria-live="polite"></span>',
        "</div>",
        "",
        '<p class="gal-hint">键盘：<kbd>/</kbd> 聚焦搜索 · 弹窗里 <kbd>←</kbd> <kbd>→</kbd> 翻页 · '
        '<kbd>Esc</kbd> 关闭。筛选状态会写进地址栏（如 '
        '<code>gallery.html?ch=12&q=米勒</code>），可以直接分享。</p>',
        "",
        '<div class="gal-grid">',
        "\n".join(cards),
        "</div>",
        "",
        '<p class="gal-empty" id="gal-empty" style="display:none">'
        "没有匹配的动画，换个关键词试试。</p>",
        "",
        '<div class="gal-modal" id="gal-modal" role="dialog" aria-modal="true" aria-label="动画放大播放">',
        '  <div class="gal-modal-box">',
        '    <div class="gal-modal-bar">',
        '      <span class="gal-modal-title" id="gal-modal-title"></span>',
        '      <span class="gal-modal-tools">',
        '        <span class="gal-pos" id="gal-modal-pos"></span>',
        '        <button class="gal-nav" id="gal-modal-prev" type="button"><svg class="gal-icon" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14.6 5.6 L8.3 12 L14.4 18.5"/></svg> 上一张</button>',
        '        <button class="gal-nav" id="gal-modal-next" type="button">下一张 <svg class="gal-icon" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9.4 5.6 L15.7 12 L9.6 18.5"/></svg></button>',
        '        <button class="gal-modal-close" id="gal-modal-close" type="button"><svg class="gal-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" aria-hidden="true"><path d="M6.4 6.4 L17.6 17.6 M17.4 6.2 L6.2 17.4"/></svg> 关闭（Esc）</button>',
        "      </span>",
        "    </div>",
        '    <img id="gal-modal-img" alt="">',
        '    <div class="gal-modal-foot">'
        '<a id="gal-modal-link" href="#">查看这张动画的讲解与看点</a></div>',
        "  </div>",
        "</div>",
        "",
    ]) + "\n"


def page_title(path):
    return content_title(path.read_text(encoding="utf-8")) or path.stem


def build_nav(pages):
    groups = []
    for name in pages:
        if name == "index.md":
            continue
        m = re.match(r"^p(\d+)-", name)
        key = 90 if name in APPENDIX else (int(m.group(1)) if m else 99)
        if not groups or groups[-1][0] != key:
            groups.append([key])
        groups[-1].append(name)

    lines = ["  - 首页: index.md"]
    for key, *names in groups:
        # pN-00-* 是「篇首页」：整篇的入口页，其后页面作为它的子项
        has_head = bool(re.match(r"^p\d+-00-", names[0]))
        if key == 90:
            title = "附录"
        elif key == 0:
            title = "开始之前"
        else:
            title = page_title(OUT / names[0])
        lines.append("  - %s:" % title)
        # 篇首页作为本节的首项（配合 navigation.indexes，点击节名即进入该页）
        if has_head:
            lines.append("    - %s" % names[0])
            children = names[1:]
        else:
            children = names
        for n in children:
            lines.append("    - %s: %s" % (page_title(OUT / n), n))
    lines.append("  - 动画画廊: gallery.md")
    lines.append("  - 社区:")
    lines.append("    - 参与共建: CONTRIBUTING.md")
    lines.append("    - 共建者墙: CONTRIBUTORS.md")
    return "\n".join(lines)


def patch_search_worker(site_dir: Path) -> bool:
    """修复 Material 搜索 worker 对中文整词查询的切分缺陷（v3.90 起既有）。

    worker 的 fe() 在倒排索引里做贪心最长匹配，但内层扫描 `o<t.length`
    永远排除「从当前位置开始的整词」——查询「去耦电容」只能切成
    「去耦* 电」（尾字单切），单字「电」命中 900+ 页，正典整词反而匹配不上。
    把扫描上界放宽到 `o<=t.length` 后，fe 能产出整词词元，查询词元与索引
    词表对齐，排名回到内容相关。Material 升级若模式缺失则跳过并告警。
    """
    patched = False
    old = "for(let o=s+1;o<t.length;o++)t.slice(s,o)in e&&(n[s]=o-s);"
    for p in sorted(site_dir.glob("assets/javascripts/workers/search.*.min.js")):
        text = p.read_text(encoding="utf-8")
        if old not in text:
            continue
        p.write_text(text.replace(old, old.replace("o<t.length", "o<=t.length"), 1),
                     encoding="utf-8", newline="\n")
        patched = True
    return patched


def write_mkdocs_config():
    skip = {"gallery.md", "CONTRIBUTING.md", "CONTRIBUTORS.md"}
    pages = [p.name for p in sorted(OUT.glob("*.md")) if p.name not in skip]
    yml = MKDOCS_YML.replace("__NAV__", build_nav(pages))
    (BUILD / "mkdocs.yml").write_text(yml, encoding="utf-8", newline="\n")


def chapter_routes():
    """Derive the reading sequence from source pages, never from menu position."""
    chapters = []
    for path in DOCS.glob("*.md"):
        match = re.fullmatch(r"p\d+-\d+-ch(\d+)\.md", path.name)
        if match:
            number = int(match.group(1))
            chapters.append((number, path.name, page_title(path)))
    return sorted(chapters)


def reading_navigation(page_name, chapters):
    """Close the chapter -> exercise -> next chapter loop in the online edition."""
    for position, (number, name, _title) in enumerate(chapters):
        if name != page_name:
            continue
        previous = ('index.html', '回到学习起点')
        following = ('p8-03-s8-3.html', '接下来：动手验证')
        if position:
            n, file, label = chapters[position - 1]
            previous = (file.replace('.md', '.html') + f'#ch{n}', '上一章：' + label)
        if position + 1 < len(chapters):
            n, file, label = chapters[position + 1]
            following = (file.replace('.md', '.html') + f'#ch{n}', '下一章：' + label)
        return (
            '\n<div class="reading-checkpoint">\n'
            f'<p><strong>学完第 {number} 章，检验一下理解</strong>'
            f'<span>核心课程 {position + 1} / {len(chapters)}</span></p>\n'
            '<p>先独立作答，再展开解析；做错的地方回到本章复习。</p>\n'
            '<nav class="reading-nav" aria-label="章节学习导航">\n'
            f'<a href="{escape(previous[0], quote=True)}">{escape(previous[1])}</a>\n'
            f'<a class="reading-quiz" href="p9-00-quiz.html#quiz-ch{number}">做第 {number} 章自测 →</a>\n'
            f'<a href="{escape(following[0], quote=True)}">{escape(following[1])}</a>\n'
            '</nav>\n</div>\n'
        )
    return ''


def legacy_anchor_links(page_name, redirects):
    """Keep old shared URLs usable, including a visible fallback without JS."""
    links = []
    for source, target in redirects.items():
        filename, anchor = source.split('#', 1)
        if filename != Path(page_name).with_suffix('.html').name:
            continue
        links.append(
            f'<div class="legacy-anchor" id="{escape(anchor, quote=True)}">'
            f'<a href="{escape(target, quote=True)}">此内容已移到对应页面，继续阅读 →</a></div>'
        )
    return '\n'.join(links)


def learning_catalog(chapters):
    questions = []
    pattern = re.compile(r'^\d+\. <a id="(q-[\w-]+)" data-quiz-question="true"></a>(.+)$', re.M)
    for match in pattern.finditer((DOCS / 'p9-00-quiz.md').read_text(encoding='utf-8')):
        questions.append({'id': match[1], 'title': _plain(match[2])[:100],
                          'href': 'p9-00-quiz.html#' + match[1]})
    return {'chapters': [{'id': f'ch{number}', 'title': title,
                          'href': name.replace('.md', '.html')}
                         for number, name, title in chapters], 'questions': questions}


def render_quiz_answers(text):
    """Keep GFM details in the source; use native details blocks for MkDocs.

    Python-Markdown's HTML preprocessor does not handle HTML indented inside
    list items. Without this conversion it emits details inside a paragraph.
    """
    pattern = r'^    <details markdown="1">\n    <summary>答案</summary>\n\n(.*?)\n\n    </details>'
    def replace(match):
        body = '\n'.join('    ' + line if line else '' for line in match[1].splitlines())
        return '    ??? note "答案"\n\n' + body + '\n'
    return re.sub(pattern, replace, text, flags=re.M | re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="生成后直接运行 mkdocs build")
    args = ap.parse_args()

    if not DOCS.is_dir():
        print("docs/ 不存在", file=sys.stderr)
        return 1
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    chapters = chapter_routes()
    media = ROOT / "scripts" / "site_media"
    redirects = json.loads((media / "legacy-anchors.json").read_text(encoding="utf-8"))
    players = load_players(ROOT)
    for page in sorted(DOCS.glob("*.md")):
        text = page.read_text(encoding="utf-8")
        if page.name == 'p9-00-quiz.md':
            text = render_quiz_answers(text)
        # MkDocs does not rewrite raw HTML links, with or without fragments.
        text = re.sub(r'href="([\w\-]+)\.md(?=[#\"])', r'href="\1.html', text)
        # 动画 <img> 补懒加载 + 预留高度（只在站点产物里加）
        text = optimize_imgs(text)
        text = wrap_visual_players(text, players, ROOT)
        # SEO：每页一句独立的 meta description（front-matter，只加在站点产物里）
        text = with_description(text)
        # 标题层级归一：正文没有 h1 的页面整体上提一级，消掉「同名 h1+h2」重复
        text = shift_headings(text)
        # 标志性引用块 → 彩色提示卡（放在 with_description 之后：摘要仍按原文摘）
        text = wrap_callouts(text)
        # 章页章首包成「章首舞台」（h1 + 引导句 + 开场提示卡；放在 wrap_callouts
        # 之后：舞台吞的就是它产出的提示卡 div）
        text = wrap_chapter_hero(text, page.name)
        # 篇级落地页包成「篇首舞台」——与章首舞台同语言（v3.57）
        text = wrap_part_hero(text, page.name)
        # 「🔗 动画演示」独立行 → 图下药丸（v3.57）
        text = wrap_demo_links(text)
        # 每页页脚加「参与共建」闭环（只在站点产物里加，docs/ 保持单一数据源干净）
        text = (text.rstrip("\n") + "\n" + reading_navigation(page.name, chapters)
                + legacy_anchor_links(page.name, redirects) + "\n" + FEEDBACK_FOOTER)
        (OUT / page.name).write_text(text, encoding="utf-8", newline="\n")
    for extra in ("CONTRIBUTING.md", "CONTRIBUTORS.md"):
        src = ROOT / extra
        if src.exists():
            text = with_description(optimize_imgs(src.read_text(encoding="utf-8")))
            text = text.rstrip("\n") + "\n" + FEEDBACK_FOOTER
            (OUT / extra).write_text(text, encoding="utf-8", newline="\n")

    # Photos and future local media must be published alongside the SVGs.
    # Attribution lives in the chapter captions; asset README files are for contributors.
    assets = ROOT / "assets"
    if assets.is_dir():
        shutil.copytree(assets, OUT / "assets", ignore=shutil.ignore_patterns("*.md"))
    if (ROOT / "LICENSE").exists():
        shutil.copyfile(ROOT / "LICENSE", OUT / "LICENSE")

    # 「减弱动效」的静止版：跟着动画一起发布（只进站点产物，仓库里不留第二份）。
    # 必须在上面的 copytree 之后 —— 它写的就是 OUT/assets/svg/ 下的副本。
    write_reduce_variants()

    (OUT / "stylesheets").mkdir(exist_ok=True)
    # 标题字体：整站只有这一处依赖中文 webfont（KaiTi 只存在于中文字体齐全的桌面）。
    (OUT / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    for name in ("NotoSerifSC-Regular.woff2", "NotoSerifSC-Bold.woff2"):
        shutil.copyfile(ROOT / "analog-book" / "fonts" / name,
                        OUT / "assets" / "fonts" / name)
    (OUT / "javascripts").mkdir(exist_ok=True)
    (OUT / "stylesheets" / "gallery.css").write_text(GALLERY_CSS, encoding="utf-8")
    (OUT / "javascripts" / "gallery.js").write_text(GALLERY_JS, encoding="utf-8")
    (OUT / "javascripts" / "mathjax.js").write_text(MATHJAX_JS, encoding="utf-8")
    shutil.copyfile(media / "typography.css", OUT / "stylesheets" / "typography.css")
    shutil.copyfile(media / "learning.js", OUT / "javascripts" / "learning.js")
    shutil.copyfile(media / "learning.css", OUT / "stylesheets" / "learning.css")
    shutil.copyfile(media / "visual-player.js", OUT / "javascripts" / "visual-player.js")
    shutil.copyfile(media / "visual-player.css", OUT / "stylesheets" / "visual-player.css")
    shutil.copyfile(media / "reading.js", OUT / "javascripts" / "reading.js")
    shutil.copyfile(media / "reading.css", OUT / "stylesheets" / "reading.css")
    shutil.copyfile(media / "progress.js", OUT / "javascripts" / "progress.js")
    shutil.copyfile(media / "diag.js", OUT / "javascripts/diag.js")
    shutil.copyfile(media / "calc.js", OUT / "javascripts/calc.js")
    shutil.copyfile(media / "diag.css", OUT / "stylesheets/diag.css")
    shutil.copyfile(media / "handraw.css", OUT / "stylesheets/handraw.css")
    catalog = json.dumps(learning_catalog(chapters), ensure_ascii=False).replace('<', '\\u003c')
    (OUT / 'javascripts/learning-catalog.js').write_text(
        'window.ANALOG_LEARNING_CATALOG = ' + catalog + ';\n', encoding='utf-8', newline='\n')

    # SEO：robots.txt（sitemap.xml 由 MkDocs 依据 site_url 自动生成）
    (OUT / "robots.txt").write_text(ROBOTS_TXT, encoding="utf-8", newline="\n")

    # SEO：社交卡片 meta（og / twitter）通过主题覆写注入 <head>
    ov = BUILD / "overrides"
    ov.mkdir(parents=True, exist_ok=True)
    (ov / "main.html").write_text(
        OVERRIDES_MAIN_HTML.replace("__OG_IMAGE__", OG_IMAGE)
        .replace("__OG_WIDTH__", str(OG_WIDTH))
        .replace("__OG_HEIGHT__", str(OG_HEIGHT)),
        encoding="utf-8", newline="\n")

    # 主题补丁：让「篇首页」成为节标题本身的链接（否则篇标题在侧栏里重复一行）
    partials = ov / "partials"
    partials.mkdir(parents=True, exist_ok=True)
    (partials / "nav-item.html").write_text(
        nav_item_override(), encoding="utf-8", newline="\n")

    # 品牌标识：Material 的 `theme.icon.logo` 会在 custom_dir 的 `.icons/` 下找
    # `<名字>.svg`。放在这里而不是写进仓库的 overrides/ —— 本项目的 overrides
    # 一律由构建生成（见上方注释），仓库里不留第二份主题目录。
    #
    # 顺手剥掉 XML 注释：logo.svg 里那段「为什么是圈 + 正弦、fill 为什么必须写在
    # 子元素上」是给改图的人看的，但它会被**内联**进 61 页的 HTML，等于把设计说明
    # 当成正文发出去。注释留在源文件里，产物只带图形。
    icons = ov / ".icons"
    icons.mkdir(parents=True, exist_ok=True)
    mark = (media / "logo.svg").read_text(encoding="utf-8")
    mark = re.sub(r"<!--.*?-->", "", mark, flags=re.S)      # 去掉设计说明
    mark = re.sub(r"\n[ \t]*\n+", "\n", mark)               # 顺手清掉留下的空行
    (icons / "analog-circuit.svg").write_text(mark, encoding="utf-8", newline="\n")

    items, _ = parse_demos()
    gallery = with_description(render_gallery(items).rstrip("\n"))
    (OUT / "gallery.md").write_text(gallery + "\n" + FEEDBACK_FOOTER,
                                    encoding="utf-8", newline="\n")
    write_mkdocs_config()
    print("站点源已生成：%s（%d 页 + %d 张动画卡片）"
          % (OUT, len(list(OUT.glob("*.md"))), len(items)))

    if args.build:
        cmd = [sys.executable, "-X", "utf8", "-m", "mkdocs", "build", "--config-file",
               str(BUILD / "mkdocs.yml")]
        print("mkdocs build ->", " ".join(cmd))
        rc = subprocess.call(cmd, cwd=str(ROOT))
        if rc == 0:
            site_out = BUILD / "site"
            if not patch_search_worker(site_out):
                print("警告：search worker 切分补丁未命中（Material 版本变化？），"
                      "中文整词搜索维持既有行为", file=sys.stderr)
        return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
