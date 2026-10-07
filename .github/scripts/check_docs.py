#!/usr/bin/env python3
"""轻量文档一致性：SVG 数量、阶段表张数、关键 code 路径、Markdown 相对链接与锚点存在性。"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")

# 文档站（VitePress）的依赖与构建产物不是文档：node_modules 里有上千个第三方
# README.md，.vitepress 下的 dist/cache 是生成页面。混进遍历会把好链接误报成死链。
PRUNED_DIRS = {"node_modules", ".vitepress", "__pycache__", ".git"}


def iter_md(base: Path) -> list[Path]:
    """遍历 base 下的 Markdown，跳过依赖与构建产物目录。"""
    return [p for p in base.rglob("*.md") if not PRUNED_DIRS.intersection(p.parts)]

# 行内代码：一段不含反引号的文字，两侧各有一串反引号。反引号本身排他，
# 所以 "`a` 文字 `b`" 只会匹配到两段代码，不会把中间的正文吞掉。
# 嵌套写法（外层两个反引号、内层含一个）不在处理范围：漏剥的后果是把示例
# 当死链报红，响亮；不会静默放过真死链。
INLINE_CODE_RE = re.compile(r"`+[^`]*`+")


def strip_code(text: str) -> str:
    """去掉围栏代码块与行内代码，供链接提取使用。

    正文里写技术写法时难免把 `![](...)` 这样的 Markdown 语法放进反引号，而
    LINK_RE 是对整篇原文跑的——那种示例不是链接。CI 在 Linux 上会把它们当死链
    报红，本机（Windows）却常常看不出来，见下面对结尾点号的处理。
    """
    kept: list[str] = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            kept.append(line)
    return INLINE_CODE_RE.sub("", "".join(kept))

# GitHub 锚点算法（github-slugger）的等价实现：
#   小写 → 去掉标点（保留 字母/组合记号/数字/连接符/连字符/空格）→ 每个空格换一个 "-"。
# 注意是"每个空格换一个"，不是折叠——`AFE + MCU` 去掉 "+" 后剩两个空格，
# 必须得到 `afe--mcu`。折叠成单个 "-" 会把正确链接误报为失效。
# 一-鿿 是 CJK，̀-ͯ 是组合记号（\w 不含后者）。
_KEEP = re.compile(r"[^\w\s\-\u4e00-\u9fff\u0300-\u036f]", re.UNICODE)


def slugify(heading: str) -> str:
    s = unicodedata.normalize("NFC", heading).strip().lower()
    s = _KEEP.sub("", s)
    return s.replace(" ", "-")


def anchors_of(path: Path) -> set[str]:
    """收集一份 Markdown 里的全部锚点，含 GitHub 的重复标题去重后缀（-1/-2…）。"""
    out: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        base = slugify(m.group(2))
        if not base:
            continue
        n = seen.get(base, 0)
        seen[base] = n + 1
        out.add(base if n == 0 else f"{base}-{n}")
    return out


# 动画数量只设下界：新增动画不该让 CI 变红，掉下来才是回退。
# 下界必须跟着实际发货量走——当前 150 张；
# 停在旧值会让"删掉一半动画"这种回退静默通过。
MIN_SVGS = 150

SVG_NS = "{http://www.w3.org/2000/svg}"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
ANIM_TAGS = {"animate", "animateTransform", "animateMotion", "set"}

# 各元素真正拥有的几何属性。动画写了元素没有的属性（最典型：给 <line> animate "y"，
# 而 <line> 的几何是 y1/y2）不会报错，只是**静默不动**——所以必须静态拦住。
GEOM_ATTRS = {
    "rect": {"x", "y", "width", "height", "rx", "ry"},
    "circle": {"cx", "cy", "r"},
    "ellipse": {"cx", "cy", "rx", "ry"},
    "line": {"x1", "y1", "x2", "y2"},
    "polyline": {"points"},
    "polygon": {"points"},
    "path": {"d"},
    "text": {"x", "y", "dx", "dy", "rotate", "textLength"},
    "tspan": {"x", "y", "dx", "dy"},
    "image": {"x", "y", "width", "height"},
    "use": {"x", "y", "width", "height"},
    "foreignObject": {"x", "y", "width", "height"},
    "svg": {"x", "y", "width", "height"},
    "g": set(),  # <g> 完全没有几何属性
}
ALL_GEOM = set().union(*GEOM_ATTRS.values())

# 这些元素不写坐标时，缺省就在 (0,0)。延迟开始的 animateMotion 在 begin 之前
# 不会把它们放到路径上，于是圆点停在画布原点。
_MOTION_POS = {
    "circle": ("cx", "cy"),
    "ellipse": ("cx", "cy"),
    "rect": ("x", "y"),
    "image": ("x", "y"),
    "use": ("x", "y"),
    "text": ("x", "y"),
    "foreignObject": ("x", "y"),
}
_CLOCK_RE = re.compile(r"^([+-]?(?:\d+(?:\.\d+)?|\.\d+))(ms|s)?$")


def _clock_seconds(raw: str | None) -> float | None:
    """时钟值换成秒。事件触发（click、id.end）返回 None，不当成原点停留。"""
    if raw is None:
        return 0.0
    match = _CLOCK_RE.fullmatch(raw.strip())
    if not match:
        return None
    value = float(match.group(1))
    if match.group(2) == "ms":
        return value / 1000.0
    return value


def _opacity_at_start(el: ET.Element) -> float | None:
    """这个元素自己在 t=0 贡献的不透明度。None 表示不强制。"""
    shown: list[float] = []
    forced = False
    for child in list(el):
        tag = child.tag.replace(SVG_NS, "")
        if tag not in {"animate", "set"} or child.get("attributeName") != "opacity":
            continue
        begin = _clock_seconds(child.get("begin"))
        if begin is None or begin > 0:
            continue
        forced = True
        if tag == "set":
            raw = child.get("to")
        elif child.get("values"):
            raw = child.get("values", "").split(";", 1)[0]
        else:
            raw = child.get("from")
        if raw is None:
            continue
        try:
            shown.append(float(raw))
        except ValueError:
            continue
    if forced and shown:
        return max(shown)
    if forced:
        return 0.0
    raw = el.get("opacity")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _hidden_before_motion(el: ET.Element, parent: dict[ET.Element, ET.Element]) -> bool:
    node: ET.Element | None = el
    while node is not None:
        if node.get("visibility") == "hidden" or node.get("display") == "none":
            return True
        opacity = _opacity_at_start(node)
        if opacity is not None and opacity <= 0:
            return True
        node = parent.get(node)
    return False


def check_smil(svgs: list[Path]) -> tuple[int, list[str]]:
    """校验 SMIL 动画的硬性规范。

    SMIL 对 keyTimes 的要求是"不满足即文档有错"，而浏览器处理"有错"的方式是
    **整条动画不执行**：元素停在初始值上，页面不报错、CI 也看不出来，只有人眼
    盯着动画才会发现某一幕从来没出现过。本函数把这些规则变成红灯。
    """
    problems: list[str] = []
    total = 0
    for svg in svgs:
        try:
            root = ET.parse(svg).getroot()
        except ET.ParseError as exc:
            problems.append(f"{svg.name}: XML 解析失败：{exc}")
            continue
        parent = {child: p for p in root.iter() for child in p}
        by_id = {el.get("id"): el for el in root.iter() if el.get("id")}

        for el in root.iter():
            tag = el.tag.replace(SVG_NS, "")
            if tag not in ANIM_TAGS:
                continue
            total += 1
            attr = el.get("attributeName")
            where = f"{svg.name}: <{tag} attributeName={attr}>"

            key_times = el.get("keyTimes")
            if key_times is not None:
                parts = key_times.split(";")
                try:
                    nums = [float(p) for p in parts]
                except ValueError:
                    problems.append(f"{where} keyTimes 不是数字列表：{key_times}")
                    nums = []
                if nums:
                    # 规范：首值必须 0；calcMode 非 discrete 时末值必须 1。
                    if nums[0] != 0.0:
                        problems.append(f"{where} keyTimes 必须以 0 开头：{key_times}")
                    if el.get("calcMode") != "discrete" and nums[-1] != 1.0:
                        problems.append(
                            f"{where} keyTimes 必须以 1 结尾（calcMode 非 discrete）：{key_times}"
                        )
                    if any(b < a for a, b in zip(nums, nums[1:], strict=False)):
                        problems.append(f"{where} keyTimes 必须单调不减：{key_times}")
                    if any(x < 0.0 or x > 1.0 for x in nums):
                        problems.append(f"{where} keyTimes 必须落在 [0,1]：{key_times}")
                for name in ("values", "keyPoints"):
                    lst = el.get(name)
                    if lst is not None and len(lst.split(";")) != len(parts):
                        problems.append(
                            f"{where} {name} 有 {len(lst.split(';'))} 项、"
                            f"keyTimes 有 {len(parts)} 项，必须等长"
                        )

            if attr:
                href = el.get(XLINK_HREF) or el.get("href")
                target = (
                    by_id.get(href[1:])
                    if href and href.startswith("#")
                    else parent.get(el)
                )
                if target is not None:
                    ttag = target.tag.replace(SVG_NS, "")
                    if ttag in GEOM_ATTRS and attr in ALL_GEOM and attr not in GEOM_ATTRS[ttag]:
                        owns = "/".join(sorted(GEOM_ATTRS[ttag])) or "无几何属性"
                        problems.append(
                            f"{where} <{ttag}> 没有 {attr} 属性（它的几何属性是 {owns}）"
                        )

            if tag != "animateMotion":
                continue
            begin_s = _clock_seconds(el.get("begin"))
            if begin_s is None or begin_s <= 0:
                continue
            href = el.get(XLINK_HREF) or el.get("href")
            host = (
                by_id.get(href[1:])
                if href and href.startswith("#")
                else parent.get(el)
            )
            if host is None:
                continue
            htag = host.tag.replace(SVG_NS, "")
            if htag == "g":
                parked = not host.get("transform")
            elif htag in _MOTION_POS:
                parked = not any(host.get(name) for name in _MOTION_POS[htag])
            else:
                parked = False
            if not parked or _hidden_before_motion(host, parent):
                continue
            problems.append(
                f"{svg.name}: <animateMotion begin={el.get('begin')}> 的 <{htag}>"
                " 在开始前没有坐标，会停在原点"
            )
    return total, problems


# 画风检查的豁免清单。还没迁过来的旧图写在这里，第 2、3 批改完一张就删掉对应行。
# 本批改过的图和以后新增的图不进清单，四项都要自己通过。
STYLE_BASELINE = Path(__file__).with_name("svg_style_baseline.txt")
STYLE_KINDS = (
    "undefined-class",
    "inline-paint",
    "small-font",
    "missing-desc",
    "missing-role",
    "desc-eq-title",
    "bad-width",
)
_PAINT_OK = {"none", "transparent", "currentcolor", "inherit"}
_CLASS_RE = re.compile(r"\.(-?[_a-zA-Z]+[\w-]*)")
_FONT_CSS_RE = re.compile(r"font-size\s*:\s*([0-9.]+)\s*px", re.IGNORECASE)
_FONT_ATTR_RE = re.compile(r"""font-size\s*=\s*["']([0-9.]+)["']""", re.IGNORECASE)
_STYLE_ATTR_RE = re.compile(r"""\bstyle\s*=\s*(["'])(.*?)\1""", re.IGNORECASE | re.DOTALL)


def _svg_style_findings(text: str) -> list[tuple[str, str]]:
    """四项便宜检查：未定义的 class、内联 fill/color、字号 <12、缺 desc 或 role。"""
    findings: list[tuple[str, str]] = []
    styles = re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.IGNORECASE | re.DOTALL)
    defined = set(_CLASS_RE.findall("\n".join(styles)))
    missing: list[str] = []
    for raw in re.findall(r'class="([^"]+)"', text):
        for name in raw.split():
            if name not in defined and name not in missing:
                missing.append(name)
    if missing:
        findings.append(("undefined-class", "、".join(missing)))

    paints: list[str] = []
    for _quote, body in _STYLE_ATTR_RE.findall(text):
        for decl in body.split(";"):
            if ":" not in decl:
                continue
            prop, val = (part.strip().lower() for part in decl.split(":", 1))
            if prop in {"fill", "color"} and val not in _PAINT_OK:
                item = f"{prop}:{val}"
                if item not in paints:
                    paints.append(item)
    if paints:
        findings.append(("inline-paint", "、".join(paints[:6])))

    small = {n for n in _FONT_CSS_RE.findall(text) + _FONT_ATTR_RE.findall(text) if float(n) < 12}
    if small:
        shown = "、".join(f"{n}px" for n in sorted(small, key=float))
        findings.append(("small-font", shown))

    desc_m = re.search(r"<desc\b[^>]*>(.*?)</desc>", text, flags=re.IGNORECASE | re.DOTALL)
    desc_text = re.sub(r"<[^>]+>", "", desc_m.group(1)) if desc_m else ""
    desc_text = re.sub(r"\s+", "", desc_text)
    if len(desc_text) < 12:
        findings.append(("missing-desc", "缺有内容的 <desc>（至少一句机制说明）"))
    title_m = re.search(r"<title\b[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    title_text = re.sub(r"\s+", "", title_m.group(1)) if title_m else ""
    if desc_text and title_text and desc_text == title_text:
        # 读屏先念 title 再念 desc，两遍同一个句子等于第二遍是噪声。
        findings.append(("desc-eq-title", "<desc> 不该是 <title> 的复读，写图上在动什么"))
    root = re.search(r"<svg\b[^>]*>", text)
    if root is None or 'role="img"' not in root.group(0):
        findings.append(("missing-role", '根 <svg> 缺 role="img"'))
    vb = re.search(r"""\bviewBox\s*=\s*["']([^"']+)["']""", text)
    if vb:
        parts = vb.group(1).split()
        try:
            width = float(parts[2]) if len(parts) == 4 else None
        except ValueError:
            width = None
        if width is None:
            findings.append(("bad-width", f"viewBox 要四位数字：{vb.group(1)!r}"))
        elif width != 800:
            findings.append(("bad-width", f"viewBox 宽 {parts[2]}，规范是 800"))
    return findings


def load_style_baseline() -> set[tuple[str, str]]:
    allowed: set[tuple[str, str]] = set()
    if not STYLE_BASELINE.exists():
        return allowed
    for raw in STYLE_BASELINE.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, _, kind = line.partition(" ")
        if name and kind:
            allowed.add((name, kind))
    return allowed


def check_svg_style(svgs: list[Path]) -> list[str]:
    """旧图可以留在豁免清单里。清单外的图（含本批改过的、新加的）必须通过。"""
    allowed = load_style_baseline()
    names = {svg.name for svg in svgs}
    problems: list[str] = []
    for name, kind in sorted(allowed):
        if name not in names:
            problems.append(f"豁免清单里的 {name} 已经不在 assets/，删掉这一行")
        elif kind not in STYLE_KINDS:
            problems.append(f"豁免清单的检查项不认识：{name} {kind}")
    for svg in svgs:
        for kind, detail in _svg_style_findings(svg.read_text(encoding="utf-8")):
            if (svg.name, kind) in allowed:
                continue
            problems.append(f"{svg.name}: {kind} {detail}")
    return problems


def check_markdown_hygiene() -> list[str]:
    """拦住两类会让公式在 GitHub 上坏掉的写法。

    - 控制字符：\\times 里的 \\t 曾被存成真正的 TAB，公式变成 ``imes``。
    - \\( \\)：GitHub 不渲染这对定界符，行内公式要用 $...$。
    """
    problems: list[str] = []
    delim = re.compile(r"\\\(|\\\)")
    for md in iter_md(ROOT):
        rel = md.relative_to(ROOT).as_posix()
        text = md.read_text(encoding="utf-8")
        for n, line in enumerate(text.splitlines(), 1):
            bad = [ch for ch in line if ord(ch) < 32 and ch not in "\t"]
            # TAB 也算：它就是 \\times 被吃掉的那一种。
            if "\t" in line or bad:
                shown = "TAB" if "\t" in line else ",".join(f"U+{ord(ch):04X}" for ch in bad)
                problems.append(f"{rel}:{n}: 控制字符 {shown}")
        in_fence = False
        for n, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if delim.search(line):
                problems.append(f"{rel}:{n}: 仍用 \\( \\) 定界，GitHub 不渲染")
    return problems


def check_stage_counts() -> list[str]:
    """README 阶段表的「本章动画」列必须等于对应正文里唯一嵌入的 SVG 张数。

    这组数字已经真实漂移过一次（108→110），而且每加一张动画都要人手同步；
    在这里对上账，漂移自己变红，不再靠人记。
    """
    problems: list[str] = []
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    row_re = re.compile(
        r"^\|\s*\[[^\]]*\]\((docs/stages/[^)]+\.md)\)\s*\|[^|]*\|\s*(\d+)\s*\|",
        re.M,
    )
    rows = row_re.findall(readme)
    if not rows:
        return [f"{readme_path.name}: 阶段表一行都没匹配到，表格式变了吗？"]
    embed_re = re.compile(r"!\[[^\]]*\]\(([^)]+\.svg)\)")
    total = 0
    for rel, claimed in rows:
        doc = ROOT / rel
        if not doc.exists():
            problems.append(f"README 阶段表指向不存在的 {rel}")
            continue
        names = {Path(p).name for p in embed_re.findall(doc.read_text(encoding="utf-8"))}
        if len(names) != int(claimed):
            problems.append(
                f"README 说 {rel} 嵌 {claimed} 张动画，正文实际唯一嵌入 {len(names)} 张"
            )
        total += int(claimed)
    m = re.search(r"七篇合计\s*(\d+)", readme)
    if m and int(m.group(1)) != total:
        problems.append(f"README 说七篇合计 {m.group(1)}，表格各行加起来是 {total}")
    return problems


# 全库动画张数是人手写的，散在七个文件里、25 处：README 四句 + 三处中文数字锚点、门户
# HTML 五句、动画索引正文一句 + 标题与目录三处中文数字、路线图 SVG 的 desc／步骤卡／底栏
# 胶囊三句、文档站首页三句、站点 description 与构建注释两句、Obsidian 说明一句。
# 147→148 那轮漂过：README 和索引跟着改，门户 HTML、路线图动画、社交卡位图还写 147
# ——门户那张是首页第一屏。148→150 这轮又查出**六个旧门看不见的洞**：文档站首页、
# config.mts、obsidian.md 三个文件整段不在 ANIM_CLAIM_FILES 里（首页那三句是读者第一屏），
# 门户「动画目录 148 张」（旧正则只认带「是」的那句）、README 的「— 148 张，按阶段各表
# 一行」和「| SMIL 动画与电路图 | 148 |」两种字序（旧正则要求数字紧跟「张动画」）。
# 现在两条一起上：正则把写数的句子捞出来逐个和 `assets/*.svg` 数出来的张数对账；每个文件
# 另外记着「该被捞到几句」，少一句就红。改写法绕开正则也会被抓，而不是静默放行。
# CHANGELOG 和更新动态的已发布小节不扫：历史条目不改写，里面那个旧数是当时的真话。
ANIM_CLAIM_FILES = (
    "README.md",
    "BMS学习路径.html",
    "docs/circuits/README.md",
    "docs/circuits/assets/bms-roadmap.svg",
    "docs/index.md",
    "docs/.vitepress/config.mts",
    "docs/obsidian.md",
)
ANIM_CLAIM_RES = (
    re.compile(r"动画目录是?\s*\**(\d+)\**\s*张"),
    re.compile(r"仓库里一共\s*(\d+)\s*张"),
    re.compile(r"(\d+)\s*张\s*(?:SMIL\s*)?动画"),
    re.compile(r"电路动画(?:与详解)?\s*[×xX](\d+)"),
    re.compile(r"(\d+)\s*张，按阶段各表一行"),
    re.compile(r"SMIL\s*动画与电路图\s*\|\s*(\d+)"),
)
CN_CLAIM_RE = re.compile(r"([零一二三四五六七八九十百]+)张动画与电路图")
CN_DIGIT = {c: i for i, c in enumerate("零一二三四五六七八九")}
CN_UNIT = {"十": 10, "百": 100}
# 每个文件**应当**被捞到的句数（阿拉伯数字 + 中文数字一起算）。少一句说明有人
# 把写数的句子改了写法或删掉了，门会捞空然后静默放行——这道反向对账堵的就是这个。
ANIM_CLAIM_EXPECT = {
    "README.md": 7,
    "BMS学习路径.html": 5,
    "docs/circuits/README.md": 4,
    "docs/circuits/assets/bms-roadmap.svg": 3,
    "docs/index.md": 3,
    "docs/.vitepress/config.mts": 2,
    "docs/obsidian.md": 1,
}


def cn_to_int(text: str) -> int:
    """读「一百四十八」这种中文数字。只到三位数够用——张数过千之前不用回来改这里。"""
    total = current = 0
    for ch in text:
        if ch in CN_DIGIT:
            current = CN_DIGIT[ch]
        else:
            total += (current or 1) * CN_UNIT[ch]
            current = 0
    return total + current


def check_animation_claims(total: int) -> list[str]:
    """凡是写「全库多少张动画」的地方，都得等于 assets/ 里数出来的张数。"""
    problems = []
    for rel in ANIM_CLAIM_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        hits = []
        for rx in ANIM_CLAIM_RES:
            hits += rx.findall(text)
            for m in rx.finditer(text):
                if int(m.group(1)) != total:
                    problems.append(f"{rel}: 写着「{m.group(0)}」，assets/ 实际 {total} 张")
        for m in CN_CLAIM_RE.finditer(text):
            hits.append(m.group(1))
            if cn_to_int(m.group(1)) != total:
                problems.append(f"{rel}: 写着「{m.group(0)}」，assets/ 实际 {total} 张")
        want = ANIM_CLAIM_EXPECT[rel]
        if len(hits) != want:
            problems.append(
                f"{rel}: 该有 {want} 处写全库动画张数，正则只捞到 {len(hits)} 处"
                f"（写法被改了吗？改了要把正则一起补上，别留空门）"
            )
    return problems


def anchors_of_html(path: Path) -> set[str]:
    """HTML 页的锚点就是 id 属性（门户页没有 GitHub 式标题 slug）。"""
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r'\bid="([^"]+)"', text))


def check_svg_index(svgs: list[Path]) -> list[str]:
    """动画索引（docs/circuits/README.md）必须和 assets/ 的实际清单双向一致。

    索引行是 「[名称](assets/xxx.svg)」。assets 有而索引没有 → 新图忘了收录；
    索引有而 assets 没有 → 图删了没摘行。清单对上了，「147 张」这类手写数字
    就没有漂移的空间。
    """
    readme = ROOT / "docs" / "circuits" / "README.md"
    indexed = {
        Path(m).name
        for m in re.findall(r"\]\(assets/([^)]+\.svg)\)", readme.read_text(encoding="utf-8"))
    }
    actual = {s.name for s in svgs}
    problems = [f"assets 有但动画索引没收录：{n}" for n in sorted(actual - indexed)]
    problems += [f"动画索引有但 assets 没有（死行）：{n}" for n in sorted(indexed - actual)]
    return problems


# ---- 外链排除清单与文档对账 ------------------------------------------------
# 被排除的域名不再受巡检，代价是"CI 说绿"不等于"这些站还活着"，所以每月要
# 人手点开（README 维护节 / 任务板 T2）。这套账已经漂移过一次：sigrok 那轮把
# exclude 加到 17，README、任务板和维护说明还写着 16。数字一错，月查就会按旧
# 清单点数，正好漏掉新加的那条——所以让脚本去数配置文件。
EXCLUDE_DOCS = ("README.md", "docs/维护说明.md", "docs/共建任务板.md")
COUNT_RE = re.compile(r"(\d+)\s*个[^。\n]{0,40}域名")

# lychee 的抓取范围就是仓库里的 *.md 与 *.html，这道账用同一套口径，
# 免得「检查器看见的链接」与「巡检看见的链接」又是两拨。
EXTERNAL_URL_RE = re.compile(r"https?://[^\s)\]>\"'`，。；、）（]+")


def iter_site_files() -> list[Path]:
    """.lychee.toml 的 exclude 可能命中的文件：与 links.yml 里 lychee 的 glob 一致。"""
    files = list(iter_md(ROOT))
    files += [
        p for p in ROOT.rglob("*.html")
        if not PRUNED_DIRS.intersection(p.parts) and "dist" not in p.parts
    ]
    return files


def check_exclude_collateral(raw: list[str], maint: str) -> list[str]:
    """exclude 是对整条 URL 的非锚定正则，不是按主机名匹配。

    所以 `archive\\.org` 那一条除了书单里的 archive.org，还把另一家完全不同的站
    www.batteryarchive.org 一起静默排除掉了——月查清单只写「archive.org」，
    按清单点数的人根本不知道该点它。凡被顺带命中的主机名，要么本来就是那条目
    的子域（www.nxp.com 之于 nxp.com），要么必须在维护说明的月查段里点名。
    """
    urls: set[str] = set()
    for path in iter_site_files():
        try:
            text = strip_code(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        urls.update(EXTERNAL_URL_RE.findall(text))

    problems = []
    seen = set()
    for item in raw:
        rx = re.compile(item)
        domain = item.replace("\\.", ".")
        for url in sorted(urls):
            if not rx.search(url):
                continue
            host = urlparse(url).netloc.lower().split(":")[0]
            if not host or host == domain or host.endswith("." + domain):
                continue
            if (item, host) in seen:
                continue
            seen.add((item, host))
            if f"`{host}`" not in maint:
                problems.append(
                    f"exclude '{item}' 顺带把 {host} 也排除了（例如 {url}），"
                    "但维护说明的月度复查段没写这个主机名"
                )
    return problems


def exclude_entries() -> list[str]:
    """.lychee.toml 里 exclude 的原始正则条目。"""
    cfg = (ROOT / ".lychee.toml").read_text(encoding="utf-8")
    block = re.search(r"^exclude\s*=\s*\[(.*?)\]", cfg, re.M | re.S)
    if not block:
        return []
    return re.findall(r"'([^']+)'", block.group(1))


def check_lychee_exclude() -> list[str]:
    """`.lychee.toml` 的 exclude 必须与文档写的数量、以及维护说明的逐条说明对上。"""
    raw = exclude_entries()
    if not raw:
        return [".lychee.toml: 找不到 exclude 列表，配置格式变了吗？"]
    domains = {d.replace("\\.", ".") for d in raw}
    problems = []
    if len(domains) != len(raw):
        problems.append(".lychee.toml: exclude 里有重复域名")
    for rel in EXCLUDE_DOCS:
        text = strip_code((ROOT / rel).read_text(encoding="utf-8"))
        for n in COUNT_RE.findall(text):
            if int(n) != len(domains):
                problems.append(f"{rel}: 写着 {n} 个域名，exclude 实际有 {len(domains)} 条")
    maint = (ROOT / "docs" / "维护说明.md").read_text(encoding="utf-8")
    for d in sorted(domains):
        if f"`{d}`" not in maint:
            problems.append(f"exclude 有 {d}，维护说明的月度复查段没写它")
    problems += check_exclude_collateral(raw, maint)
    return problems


# ---- 发布记录表对账 ------------------------------------------------------
# docs/维护说明.md 的「发布记录」表手抄着版本、标签指向、发布时间和核验。CI 里
# 拿不到 git 标签（actions/checkout 默认不抓 tag），所以文本侧只对上「能自证」的
# 部分：三个版本集合互相等于、发布日期与 CHANGELOG 落款一致、sha 与 run 号的写法
# 成形状、正文里「vX.Y.Z 打在 `sha`」的口径与表一致。标签指向和 publishedAt 的
# 真值由本地门用 `--release-truth` 现取现比（git for-each-ref + gh release list）。

RELEASE_DOC = "docs/维护说明.md"
RELEASE_COLS = ["版本", "标签指向", "Release 发布时间（UTC）", "收口提交", "核验"]
SHA_CELL = re.compile(r"`([0-9a-f]{7,40})`")
NUM_CELL = re.compile(r"`(\d+)`")
STAMP_CELL = re.compile(r"^(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2}$")
CL_HEADING = re.compile(
    r"^## \[v?(\d+\.\d+\.\d+)\]\s*[—-]\s*(\d{4}-\d{2}-\d{2})", re.M
)
CL_REF = re.compile(r"^\[v?(\d+\.\d+\.\d+)\]:\s*https?://", re.M)
# 「vX.Y.Z …… 打在 `sha`」：中间不跨句号，最多隔 120 个字符（够跨过 markdown 链接）。
TAGGED_SHA = re.compile(r"(\d+\.\d+\.\d+)[^。]{0,120}?打在 `([0-9a-f]{7,40})`")
# 「tests `37582750408`」：核验列点名 workflow 的写法。run 号 8 位以上才认。
RUN_NAMED = re.compile(r"([A-Za-z][A-Za-z0-9_.-]*) `(\d{8,})`")
# 提交标题尾部的 PR 号：`docs: … (#42)`。
PR_NUM = re.compile(r"\(#(\d+)\)\s*$")


def workflow_names() -> set[str]:
    """仓库里每条 workflow 的 name，用来要求核验列点名点齐。"""
    names = set()
    for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        m = re.search(r"^name:\s*(\S+)\s*$", path.read_text(encoding="utf-8"), re.M)
        if m:
            names.add(m.group(1))
        else:
            names.add(path.stem)
    return names


CHECKOUT_USE = re.compile(r"^(\s*)-?\s*uses:\s*actions/checkout@", re.I)
FETCH_DEPTH_LINE = re.compile(r"^\s*fetch-depth:\s*(\S+)")
# 正文里「仓库三个 workflow 里那 7 处 checkout 都没改它」这句（中文数字与阿拉伯数字都认）。
RUNNER_CLAIM = re.compile(
    r"仓库([零一二三四五六七八九十百\d]+)\s*个\s*workflow[^\d]{0,8}?(\d+)\s*处\s*checkout"
)


def workflow_files() -> list[str]:
    return sorted(p.name for p in (ROOT / ".github" / "workflows").glob("*.yml"))


def checkout_steps() -> list[tuple[str, int, str | None]]:
    """扫 workflow 里的 actions/checkout 步骤，带回各自显式写的 fetch-depth。

    `- uses:` 一行式和 `- name:` + `uses:` 两行式都要数到：否则将来有人把步骤拆成两行，
    处数凭空少一处，反倒把正文里正确的数字判成错。
    """
    found: list[tuple[str, int, str | None]] = []
    for name in workflow_files():
        raw = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        lines = raw.splitlines()
        for i, line in enumerate(lines):
            m = CHECKOUT_USE.match(line)
            if not m:
                continue
            indent = len(m.group(1))
            depth = None
            for nxt in lines[i + 1:]:
                if not nxt.strip():
                    continue
                nxt_indent = len(nxt) - len(nxt.lstrip())
                # 同级只放行 with:（两行式的参数块），再往下就是下一个步骤
                if nxt_indent < indent or (nxt_indent == indent and nxt.strip() != "with:"):
                    break
                fm = FETCH_DEPTH_LINE.match(nxt)
                if fm:
                    depth = fm.group(1).strip("\"'")
                    break
            found.append((name, i + 1, depth))
    return found


def check_runner_no_tags() -> list[str]:
    """「runner 数不到标签」是两道真值门不进 CI 的理由，所以这句话本身得能对账。

    两个数从 .github/workflows 现读；更要紧的是：谁给某处 checkout 设了 fetch-depth，
    「数不到标签」就不一定成立，那句理由与「为什么不进 CI」的分工得重判。
    """
    steps = checkout_steps()
    text = (ROOT / RELEASE_DOC).read_text(encoding="utf-8")
    m = RUNNER_CLAIM.search(text)
    if not m:
        return [
            f"{RELEASE_DOC}: 找不到「仓库 N 个 workflow 里那 M 处 checkout 都没改 fetch-depth」"
            "那句——真值门不进 CI 的理由要留在纸面上，不能只剩脚本里的注释"
        ]
    claimed_wf = int(m.group(1)) if m.group(1).isdigit() else cn_to_int(m.group(1))
    claimed_ck = int(m.group(2))
    actual_wf = len(workflow_files())
    problems = []
    if claimed_wf != actual_wf:
        problems.append(
            f"{RELEASE_DOC}: 正文写「{m.group(0)}」，.github/workflows 实际 {actual_wf} 个文件"
        )
    if claimed_ck != len(steps):
        problems.append(
            f"{RELEASE_DOC}: 正文写「{m.group(0)}」，实际 {len(steps)} 处 actions/checkout"
        )
    for name, line, depth in steps:
        if depth is not None and depth != "1":
            problems.append(
                f".github/workflows/{name}:{line} 的 checkout 设了 fetch-depth: {depth}——"
                "「runner 数不到标签」这条理由不再一定成立：先实测 runner 上数得到什么，"
                "再决定发布记录/分类两道真值门要不要搬进 CI，最后改正文那句"
            )
    return problems


# ---- 本地门的步数清单：脚本与三处抄本必须说同一句话 -------------------------------
# 加一道门要动四处：两份门脚本各自吐出的步骤标签、两份脚本头注释里「只在本地跑」的
# 名单、CONTRIBUTING 的箭头串与前 N 步/后 M 步。上一轮加「仓库简介对账」就是人工对齐
# 这三处抄本——少改一处没有任何东西变红，因为清单本身在门外。这道门把三处抄本都对回
# 脚本实际吐出的标签序列：脚本改了、文档没跟上，CI 当场点名。
# 真值取脚本吐的标签而不是注释：一步要是不吐标签，本地跑根本看不见它，注释写得再全也
# 没用。只认带 PASS 的那一行——`python 解释器` 那种只在解释器缺失时冒出来的 FAIL-only
# 伪标签不算一步；一步的 PASS 只该出现一次，重复即红（同一名字出现两遍就没法比顺序）。

GATE_SCRIPTS = (
    # bash 有两种写法：report '带空格的名' PASS 与 report check_docs PASS
    ("scripts/local-gates.sh", re.compile(r"\breport\s+(?:'([^']+)'|([A-Za-z_][\w.]*))\s+PASS\b")),
    # PowerShell 的 PASS 常常在标签后面老远：Add-Result 'ruff' $(if … 'PASS' …)
    ("scripts/local-gates.ps1", re.compile(r"\bAdd-Result\s+'([^']+)'.*PASS")),
)
# 头注释点名本地专属的门一律写成「××对账」；正文里的裸名（「跑到发布记录对账那步」）
# 不算点名，不能被捞进来。
LOCAL_ONLY_RE = re.compile(r"「([^」]*对账)」")
GATE_CHAIN_RE = re.compile(r"本地门全绿再推[：:](.+?)。")
ARROW_SPLIT = re.compile(r"\s*→\s*")
CN_COUNT = r"[零一二三四五六七八九十百\d]"
PRE_STEPS_RE = re.compile(rf"前({CN_COUNT}+)步")
POST_STEPS_RE = re.compile(rf"后({CN_COUNT}+)步")
LOCAL_NOUN_RE = re.compile(rf"这({CN_COUNT}+)样在本地缺了记")
# 「第 N 步「××对账」」这种带名字的序号断言：门加在前面就会把后面的序号整体顶歪，
# 而歪掉没有任何症状。已发布小节不扫——历史条目不改写，同动画张数那道门的口径。
STEP_ORDINAL_RE = re.compile(rf"第({CN_COUNT}+)步「([^」]+)」")


def cn_or_int(text: str) -> int:
    return int(text) if text.isdigit() else cn_to_int(text)


def read_gate_script(rel: str) -> str:
    """两份门脚本都要读：.ps1 是 UTF-8 with BOM（Windows PowerShell 5.1 的要求），
    直接按 utf-8 读会把行首的 \\ufeff 当成内容——头注释第一行就不再是 `#` 开头，
    注释块当场判定为空，「本地专属门名单」这道对账就静默变成「脚本没点名」。"""
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def gate_step_labels(rel: str, rx: re.Pattern) -> list[str]:
    """按出现顺序捞出脚本吐出的步骤标签（只认带 PASS 的那行）。"""
    got: list[str] = []
    for line in read_gate_script(rel).splitlines():
        m = rx.search(line)
        if m:
            got.append(m.group(1) or m.group(2))
    return got


def header_comment(text: str) -> str:
    """脚本开头的注释块——本地专属门的名单只在这里点名，函数体里的不算。"""
    kept: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#!"):
            continue
        if not s.startswith("#"):
            break
        kept.append(s)
    return "\n".join(kept)


def gate_seq_diff(want: list[str], got: list[str]) -> str:
    """两条清单分家了怎么说才好用：先说差在哪个名字，再说差在哪个位置。"""
    missing = [x for x in want if x not in got]
    extra = [x for x in got if x not in want]
    if missing or extra:
        return (
            f"脚本有而这里没有 {'、'.join(missing) or '（无）'}；"
            f"这里有而脚本没有 {'、'.join(extra) or '（无）'}"
        )
    for k, (a, b) in enumerate(zip(want, got, strict=False)):
        if a != b:
            return f"第 {k + 1} 步起顺序分家：脚本 {a}，这里 {b}"
    return f"步数不同：脚本 {len(want)} 步，这里 {len(got)} 步"


def unreleased_bullets() -> str:
    """CHANGELOG 的 [Unreleased] 正文——本批还没定稿的话都在里面，已发布小节不碰。"""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^## \[Unreleased\][^\n]*\n(.*?)(?=^## \[|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def check_local_gate_lists() -> list[str]:
    """脚本实际吐出的步骤标签，对上头注释名单、CONTRIBUTING 的箭头串与两处步数。"""
    problems: list[str] = []
    seqs: dict[str, list[str]] = {}
    heads: dict[str, list[str]] = {}
    for rel, rx in GATE_SCRIPTS:
        if not (ROOT / rel).exists():
            problems.append(f"{rel}: 文件读不到——这道门的真值全来自它")
            continue
        got = gate_step_labels(rel, rx)
        if not got:
            problems.append(
                f"{rel}: 一个步骤标签都没捞到（脚本改了吐标签的写法？"
                "改了要把 GATE_SCRIPTS 的正则一起补上，别留空门）"
            )
        dup = [k for k, v in Counter(got).items() if v > 1]
        if dup:
            problems.append(
                f"{rel}: {'、'.join(dup)} 一步吐出两次 PASS——同一个名字出现两遍就没法比"
                "顺序，把重复那步的 PASS 合并成一次"
            )
        seqs[rel] = got
        h = LOCAL_ONLY_RE.findall(header_comment(read_gate_script(rel)))
        if not h:
            problems.append(
                f"{rel}: 头注释没点名任何一道「只在本地跑」的门——为什么不进 CI 得写在纸面上"
            )
        heads[rel] = h

    rel_sh, rel_ps = GATE_SCRIPTS[0][0], GATE_SCRIPTS[1][0]
    labels = seqs.get(rel_sh) or []
    if seqs.get(rel_sh) and seqs.get(rel_ps):
        if labels != seqs[rel_ps]:
            problems.append(
                f"{rel_sh} 与 {rel_ps} 的步骤清单分家了——两份脚本是同一道门的两个壳，"
                + gate_seq_diff(labels, seqs[rel_ps])
            )
        hs = list(heads.values())
        if hs and hs[0] != hs[1]:
            problems.append(
                f"两份脚本头注释的本地专属门名单不是同一份：{rel_sh} {hs[0]} / {rel_ps} {hs[1]}"
            )
        only = heads.get(rel_sh, [])
        if only:
            if len(set(only)) != len(only):
                problems.append(f"{rel_sh}: 头注释把同一道门点名了两遍，先理清再谈对账")
            tail = labels[-len(only):]
            if len(only) > len(labels) or tail != only:
                problems.append(
                    f"{rel_sh} 头注释点名的「只在本地跑」那几道，和脚本实际吐在末尾的几步对不上："
                    + gate_seq_diff(only, tail)
                    + "——本地专属的门都得排在 CI 对齐的那些之后，不然「后 M 步」这个说法就是错的"
                )

    if not labels:
        return problems

    ct_path = ROOT / "CONTRIBUTING.md"
    if not ct_path.exists():
        problems.append("CONTRIBUTING.md: 读不到——箭头清单与前后步数没有对对象")
        ct_line = ""
    else:
        ct = ct_path.read_text(encoding="utf-8")
        ct_line = next((ln for ln in ct.splitlines() if GATE_CHAIN_RE.search(ln)), "")
        m = GATE_CHAIN_RE.search(ct_line)
        if not m:
            problems.append(
                "CONTRIBUTING.md: 找不到「本地门全绿再推：A → B → …」那句箭头清单——"
                "抄本被整段删掉或改写法，这道门就没有对对象了（真要删先把门一起撤）"
            )
        else:
            chain = [x for x in (s.strip() for s in ARROW_SPLIT.split(m.group(1))) if x]
            if not chain:
                problems.append(
                    "CONTRIBUTING.md: 箭头串一步都没拆开（改成不带 → 的写法了？"
                    "那要把这里的正则一起补上，别留空门）"
                )
            elif chain != labels:
                problems.append(
                    "CONTRIBUTING.md 的箭头清单和脚本吐的标签不是同一份："
                    + gate_seq_diff(labels, chain)
                    + "——名字要逐字照抄脚本（散文式别名如「固件 gcc 编译+运行」不算同一步）"
                )

        total, m_local = len(labels), len(heads.get(rel_sh, []))
        for rx, label, want in (
            (PRE_STEPS_RE, "和 CI 对齐的那几步", total - m_local),
            (POST_STEPS_RE, "只在本地跑的那几步", m_local),
            (LOCAL_NOUN_RE, "只在本地跑的那几样", m_local),
        ):
            mm = rx.search(ct_line)
            if not mm:
                problems.append(
                    f"CONTRIBUTING.md: 箭头串那一行找不到「{label}」的数（{rx.pattern}）——"
                    "这个数是门唯一知道的 CI/本地分界，写在别处门读不到"
                )
                continue
            if cn_or_int(mm.group(1)) != want:
                problems.append(
                    f"CONTRIBUTING.md 写「{mm.group(0)}」，两份脚本现数的是 {want}——"
                    f"全表 {total} 步、头注释点名本地专属 {m_local} 道"
                )

    for rel, text in (
        ("CONTRIBUTING.md", ct_line),
        (RELEASE_DOC, (ROOT / RELEASE_DOC).read_text(encoding="utf-8")),
        ("CHANGELOG.md 的 [Unreleased]", unreleased_bullets()),
    ):
        for mm in STEP_ORDINAL_RE.finditer(text):
            name = mm.group(2)
            if name not in labels:
                problems.append(
                    f"{rel}: 「{mm.group(0)}」点名的这一步在脚本清单里不存在——"
                    + gate_seq_diff(labels, [name])
                )
                continue
            want_n = labels.index(name) + 1
            if cn_or_int(mm.group(1)) != want_n:
                problems.append(
                    f"{rel}: 写「{mm.group(0)}」，脚本把它吐在第 {want_n} 步"
                    f"（全表 {total} 步）——前面插进门的时候，后面每一步的序号都得跟着挪"
                )
    return problems


def release_table_rows() -> list[dict[str, str]]:
    """解析「## 发布记录」里那张表。表头按名字认，不按位置猜。"""
    text = (ROOT / RELEASE_DOC).read_text(encoding="utf-8")
    parts = text.split("## 发布记录", 1)
    if len(parts) < 2:
        return []
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in parts[1].splitlines():
        line = line.strip()
        if not line.startswith("|"):
            if header is not None:
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(c and set(c) <= set("-: ") for c in cells):
            continue
        if len(cells) != len(header):
            raise ValueError(
                f"{RELEASE_DOC}: 发布记录表有一行是 {len(cells)} 格，表头 {len(header)} 格：{line[:80]}"
            )
        rows.append(dict(zip(header, cells, strict=True)))
    return rows


def check_release_record(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return [f"{RELEASE_DOC}: 找不到「## 发布记录」的表，这一节的格式变了吗？"]
    missing_cols = [c for c in RELEASE_COLS if c not in rows[0]]
    if missing_cols:
        return [f"{RELEASE_DOC}: 发布记录表缺列：{'、'.join(missing_cols)}"]

    problems: list[str] = []
    # 「点名齐所有 workflow」只对最新那一版要求：以后新增一条 workflow，不该把
    # 已经发过的版本判成漏记——那一版发的时候根本没有这条 workflow。
    parsed = [m.group(1) for m in
              (re.fullmatch(r"v(\d+\.\d+\.\d+)", r["版本"]) for r in rows) if m]
    newest = max(parsed, key=lambda v: tuple(int(n) for n in v.split("."))) if parsed else ""
    for row in rows:
        ver = row["版本"]
        m = re.fullmatch(r"v(\d+\.\d+\.\d+)", ver)
        if not m:
            problems.append(f"发布记录：版本列「{ver}」该写成 v主.次.补丁")
            continue
        key = m.group(1)

        shas = SHA_CELL.findall(row["标签指向"])
        annotated = "标签对象" in row["标签指向"]
        lightweight = "轻量标签" in row["标签指向"]
        if annotated and lightweight:
            problems.append(f"发布记录 {ver}: 标签指向同时写了「标签对象」和「轻量标签」，自相矛盾")
        if annotated and not lightweight and len(set(shas)) != 2:
            problems.append(f"发布记录 {ver}: 写了「标签对象」却没有两个不同的 sha：{shas}")
        if lightweight and len(shas) != 1:
            problems.append(f"发布记录 {ver}: 轻量标签该只有一个 sha，实际：{shas}")
        if not annotated and not lightweight:
            problems.append(f"发布记录 {ver}: 标签指向没说明是附注标签还是轻量标签")

        stamp = STAMP_CELL.match(row["Release 发布时间（UTC）"])
        if not stamp:
            problems.append(
                f"发布记录 {ver}: 发布时间「{row['Release 发布时间（UTC）']}」"
                "不是「2026-01-01 00:00:00」这个写法（空格分隔、不带 T 和 Z）"
            )

        close = row["收口提交"]
        if close != "未记录" and len(SHA_CELL.findall(close)) != 1:
            problems.append(f"发布记录 {ver}: 收口提交「{close}」既不是未记录、也没有唯一一个 sha")

        verify = row["核验"]
        if verify != "未记录":
            for num in NUM_CELL.findall(verify):
                if len(num) < 8:
                    problems.append(f"发布记录 {ver}: 核验里的 `{num}` 不像 run 号（run 号 8 位以上）")
        if close != "未记录":
            pairs = RUN_NAMED.findall(verify)
            named = {n for n, _ in pairs}
            if ver == f"v{newest}":
                missing = sorted(workflow_names() - named)
                if missing:
                    problems.append(
                        f"发布记录 {ver}: 收口提交有记录，核验却没点名 {'、'.join(missing)} 的 run 号")
            unknown = sorted(named - workflow_names())
            if unknown:
                problems.append(
                    f"发布记录 {ver}: 核验点名的 {'、'.join(unknown)} 不是仓库里的 workflow 名")
            for num, times in Counter(i for _, i in pairs).items():
                if times > 1:
                    problems.append(
                        f"发布记录 {ver}: run 号 `{num}` 被 {times} 个 workflow 共用，抄重了")

    cl = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = dict(CL_HEADING.findall(cl))
    refs = set(CL_REF.findall(cl))
    table_vers = set()
    for row in rows:
        m = re.fullmatch(r"v(\d+\.\d+\.\d+)", row["版本"])
        if m:
            table_vers.add(m.group(1))
    if table_vers != set(headings):
        problems.append(
            f"发布记录表的版本与 CHANGELOG 的版本小节不一致："
            f"表有而 CHANGELOG 无 {sorted(table_vers - set(headings))}，"
            f"CHANGELOG 有而表无 {sorted(set(headings) - table_vers)}"
        )
    if table_vers != refs:
        problems.append(
            f"发布记录表的版本与 CHANGELOG 的 compare 落款不一致："
            f"表有而无落款 {sorted(table_vers - refs)}，"
            f"有落款而表无 {sorted(refs - table_vers)}"
        )

    for row in rows:
        m = re.fullmatch(r"v(\d+\.\d+\.\d+)", row["版本"])
        if not m:
            continue
        key = m.group(1)
        stamp = STAMP_CELL.match(row["Release 发布时间（UTC）"])
        if stamp and key in headings and stamp.group(1) != headings[key]:
            problems.append(
                f"发布记录 {row['版本']}: 表里发布日是 {stamp.group(1)}，CHANGELOG 小节落款是 {headings[key]}"
            )

    for src in ("CHANGELOG.md", "docs/更新动态.md"):
        text = (ROOT / src).read_text(encoding="utf-8")
        for line in text.splitlines():
            for ver, sha in TAGGED_SHA.findall(line):
                row = next((r for r in rows if r["版本"] == f"v{ver}"), None)
                if row is None:
                    problems.append(f"{src}: 写了 v{ver} 打在 `{sha}`，发布记录表却没有这一行")
                elif not sha_covers(sha, SHA_CELL.findall(row["标签指向"])):
                    problems.append(
                        f"{src}: 写了 v{ver} 打在 `{sha}`，发布记录表的标签指向是 {row['标签指向']}"
                    )
    problems += check_column_prose()
    return problems


# 门面三处「最新发布」的说法：README 的折叠块、门户卡片、更新动态的导读句。
LATEST_CLAIM_FILES = ("README.md", "BMS学习路径.html", "docs/更新动态.md")
LATEST_ANCHOR = re.compile(r"最近更新|这批已经发布|最新发布")
TAG_URL = re.compile(r"/releases/tag/v(\d+\.\d+\.\d+)")
TAG_MD = re.compile(
    r"\[\s*`?v?(\d+\.\d+\.\d+)`?\s*\]\(\s*[^)\s]*/releases/tag/v(\d+\.\d+\.\d+)\)"
)
TAG_HTML = re.compile(r"/releases/tag/v(\d+\.\d+\.\d+)\">\s*`?v?(\d+\.\d+\.\d+)")
LINE_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def newest_release() -> tuple[str, str]:
    """发布记录表里版本号最大的那一行，带回 (vX.Y.Z, 发布日)；表是空的就交回上一道门。"""
    rows = release_table_rows()
    parsed = []
    for row in rows:
        m = re.fullmatch(r"v(\d+\.\d+\.\d+)", row["版本"])
        if m:
            parsed.append((tuple(int(n) for n in m.group(1).split(".")), m.group(1), row))
    if not parsed:
        return "", ""
    _, tail, row = max(parsed, key=lambda t: t[0])
    stamp = STAMP_CELL.match(row["Release 发布时间（UTC）"])
    return f"v{tail}", stamp.group(1) if stamp else ""


def check_latest_claims() -> list[str]:
    """门面宣布版本的地方必须指向发布记录表最新那一版。

    口径是「链到 Release 标签的那处」：链接文字与 URL 两个数都要等于最新那一版，日期也得
    等于表里的发布日——正文里 `v1.2.0` 之后多少个提交这类历史账不在锚点句里就不追，
    句子里没版本号也不逼你写一个。门面必须留一条指向 `releases/tag/…` 的链接，否则
    「最新版本」这句话就退成一个没人能对账的说法。
    """
    newest, stamp = newest_release()
    if not newest:
        return []
    problems: list[str] = []
    for rel in LATEST_CLAIM_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        anchors = [ln for ln in text.splitlines() if LATEST_ANCHOR.search(ln)]
        if not anchors:
            problems.append(
                f"{rel}: 「最近更新 / 这批已经发布」那句不见了——门面版本号的账没人对得了"
            )
            continue
        linked = [ln for ln in anchors if TAG_URL.search(ln)]
        if not linked:
            problems.append(
                f"{rel}: 「最近更新」那句没有指向 `releases/tag/…` 的链接，"
                f"最新那一版（{newest}）对不上账"
            )
            continue
        for line in linked:
            cited = {g for pair in TAG_MD.findall(line) for g in pair}
            cited |= {g for pair in TAG_HTML.findall(line) for g in pair}
            cited |= set(TAG_URL.findall(line))
            for got in sorted(cited - {newest[1:]}):
                problems.append(f"{rel}: 门面链到 v{got}，发布记录表最新是 {newest}")
            for day in LINE_DATE.findall(line):
                if stamp and day != stamp:
                    problems.append(
                        f"{rel}: 门面那句的日期写 {day}，表里 {newest} 的发布日是 {stamp}"
                    )
    return problems


def check_release_archive() -> list[str]:
    """Unreleased 与表里最新那一版的小节，条目开头前 32 字不许撞车。

    收口是把条目从 Unreleased **搬**进版本节。哪次复制了一份、原来那条没删，
    `check_release_record` 看不出——它比的是小节集合与落款集合，两处都自洽；
    留着的那一份会把下一版的「共 N 条」变成永远数不清的账：同一句话一会儿算进
    1.4.0、一会儿算进 Unreleased，而节首那句数只数自己那一节的行。
    """
    newest, _ = newest_release()
    if not newest:
        return []
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    sec = section_bullets(text, newest[1:])
    if sec is None:
        # 表里有这一版而 CHANGELOG 没这一节，那是 check_release_record 的账
        return []
    un = section_bullets(text, "Unreleased") or []
    dup = sorted({b[:MIGRATE_PREFIX] for b in un} & {b[:MIGRATE_PREFIX] for b in sec})
    if not dup:
        return []
    return [
        f"发布记录 {newest}: Unreleased 有 {len(dup)} 条与 `## [{newest[1:]}]` 一节的开头"
        f"（前 {MIGRATE_PREFIX} 字）相同，例如「{dup[0]}…」——收口是把条目搬进版本节，"
        "不是两边各留一份"
    ]


DYNAMIC_DOC = "docs/更新动态.md"
GROUP_LINE = re.compile(r"^\*\*v?(\d+\.\d+\.\d+)([^*]*)\*\*$")
GROUP_ITEM = re.compile(r"^- \[")


def dynamic_groups() -> list[tuple[str, str, int]]:
    """更新动态本页目录里每个 `**X.Y.Z（……）**` 分组，带回（分组行, 版本号, 组内小节链接数）。"""
    if not (ROOT / DYNAMIC_DOC).exists():
        return []
    lines = (ROOT / DYNAMIC_DOC).read_text(encoding="utf-8").splitlines()
    out: list[tuple[str, str, int]] = []
    for i, ln in enumerate(lines):
        m = GROUP_LINE.match(ln.strip())
        if not m:
            continue
        items = 0
        for nxt in lines[i + 1:]:
            s = nxt.strip()
            if GROUP_LINE.match(s) or s.startswith("#"):
                break
            if GROUP_ITEM.match(s):
                items += 1
        out.append((ln.strip(), m.group(1), items))
    return out


def dynamic_group(ver: str) -> tuple[str, int]:
    """点名某一版的分组，没有就交回空串——点名缺席那句话由调用方打，不在这层猜。"""
    for line, key, items in dynamic_groups():
        if key == ver:
            return line, items
    return "", 0


def release_stamps() -> dict[str, str]:
    """发布记录表里每一版的发布日；那一格没有可解析的真时间就给空串。"""
    out: dict[str, str] = {}
    for row in release_table_rows():
        m = re.fullmatch(r"v(\d+\.\d+\.\d+)", row["版本"])
        if not m:
            continue
        stamp = STAMP_CELL.match(row["Release 发布时间（UTC）"])
        out[m.group(1)] = stamp.group(1) if stamp else ""
    return out


def check_release_dynamic() -> list[str]:
    """更新动态本页目录的分组要与发布记录表对得上。

    Release 正文末尾把读者指向这一页。最新那一版必须有分组、日期等于表里的发布日、组下
    至少一条小节链接——只进了表和 CHANGELOG、这一页没写，症状是「点进去最新只到上一版」，
    而站点照常构建、门面三处照常绿。已有的每一个分组也都比：版本号必须真在表里（否则就是
    宣布一个没发过的版本）、写了日期就要等于表里那一版的发布日、组下不许是空标签、同一版
    不许有两条分组。历史分组没写日期不追，写法是当年的话不改写（与 `check_latest_claims`
    同一口径）。
    """
    newest, stamp = newest_release()
    if not newest:
        return []
    if not (ROOT / DYNAMIC_DOC).exists():
        return [f"{DYNAMIC_DOC}: 文件读不到——最新那一版的读者视角没处对账"]
    newest_key = newest[1:]
    problems: list[str] = []
    groups = dynamic_groups()
    hit, items = dynamic_group(newest_key)
    if not hit:
        problems.append(
            f"{DYNAMIC_DOC}: 本页目录没有 {newest} 的分组——表里最新那一版在读者视角那页查无此版")
    else:
        dates = LINE_DATE.findall(hit)
        if stamp:
            if not dates:
                problems.append(f"{DYNAMIC_DOC}: {newest} 的分组行没标发布日，表里写的是 {stamp}")
            elif stamp not in dates:
                problems.append(
                    f"{DYNAMIC_DOC}: {newest} 的分组行标了 {'、'.join(dates)}，表里发布日是 {stamp}")
        if not items:
            problems.append(
                f"{DYNAMIC_DOC}: {newest} 的分组行下面一条小节链接都没有——分组成了空标签")

    stamps = release_stamps()
    seen: dict[str, int] = {}
    for line, key, group_items in groups:
        seen[key] = seen.get(key, 0) + 1
        if key == newest_key:
            continue
        if key not in stamps:
            problems.append(
                f"{DYNAMIC_DOC}: 本页目录有 {line} 的分组，发布记录表却没有 v{key} 这一行——"
                "读者视角走在凭据前面，等于宣布一个没发过的版本")
            continue
        dates = LINE_DATE.findall(line)
        if stamps[key] and dates and stamps[key] not in dates:
            problems.append(
                f"{DYNAMIC_DOC}: v{key} 的分组行标了 {'、'.join(dates)}，表里那一版的发布日是 {stamps[key]}")
        if not group_items:
            problems.append(
                f"{DYNAMIC_DOC}: v{key} 的分组行下面一条小节链接都没有——分组成了空标签")
    for key, n in seen.items():
        if n > 1:
            problems.append(f"{DYNAMIC_DOC}: 本页目录有 {n} 条 v{key} 的分组行，同一版不该分家")
    return problems


def sha_covers(needle: str, pool: list[str]) -> bool:
    """表里抄 7 位、正文可能写全 40 位：互为前缀就算指同一个对象。"""
    return any(t == needle or t.startswith(needle) or needle.startswith(t) for t in pool)


def sha_diff(pool: list[str], truth: list[str]) -> list[str]:
    """两个 sha 集合按前缀对齐，返回两边各自的缺口。"""
    out = []
    for s in pool:
        if not any(t.startswith(s) or s.startswith(t) for t in truth):
            out.append(f"表里的 `{s}` 不是任何 git 对象的前缀")
    for t in truth:
        if not any(s and (t.startswith(s) or s.startswith(t)) for s in pool):
            out.append(f"git 里的 `{t[:12]}` 表里没写")
    return out


def check_close_commit(ver: str, close_sha: str, tag_commit: str) -> list[str]:
    """收口提交必须是真提交，而且必须排在标签提交之后——这是「标签链接写早了就是
    死链」那句说明的唯一硬证据。"""
    problems: list[str] = []
    exists = subprocess.run(
        ["git", "-c", "core.quotePath=false", "cat-file", "-e", f"{close_sha}^{{commit}}"],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    if exists.returncode != 0:
        return [f"发布记录 {ver}: 收口提交 `{close_sha}` 在本仓库取不到（分支被重写过？）"]
    if sha_covers(close_sha, [tag_commit]):
        problems.append(
            f"发布记录 {ver}: 收口提交与标签指向是同一个提交 `{close_sha}`，"
            "那它里面的 releases/tag 落款还是死链"
        )
    anc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", tag_commit, close_sha],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    if anc.returncode != 0:
        problems.append(
            f"发布记录 {ver}: 收口提交 `{close_sha}` 不在标签提交 "
            f"`{tag_commit[:7]}` 之后（不是它的后代）"
        )
    return problems


def check_run_records(rows: list[dict[str, str]]) -> list[str]:
    """核验列点名的每个 run 号都得真存在、真绿、真跑在收口提交上。"""
    problems: list[str] = []
    cache: dict[str, dict] = {}
    for row in rows:
        if row["收口提交"] == "未记录":
            continue
        close = SHA_CELL.findall(row["收口提交"])
        for wf, run_id in RUN_NAMED.findall(row["核验"]):
            if run_id not in cache:
                got = subprocess.run(
                    ["gh", "run", "view", run_id, "--json", "name,headSha,conclusion"],
                    capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
                )
                cache[run_id] = (
                    json.loads(got.stdout) if got.returncode == 0
                    else {"_err": got.stderr.strip()[:160]}
                )
            info = cache[run_id]
            ver = row["版本"]
            if "_err" in info:
                problems.append(f"发布记录 {ver}: run `{run_id}` 取不到：{info['_err']}")
                continue
            if info["name"] != wf:
                problems.append(
                    f"发布记录 {ver}: 核验把 `{run_id}` 记在 {wf} 名下，它其实是 {info['name']} 的 run")
            if info["conclusion"] != "success":
                problems.append(
                    f"发布记录 {ver}: run `{run_id}`（{wf}）的结论是 {info['conclusion']}，不是 success")
            if close and not sha_covers(close[0], [info["headSha"]]):
                problems.append(
                    f"发布记录 {ver}: run `{run_id}` 跑在 `{info['headSha'][:7]}`，"
                    f"与收口提交 `{close[0]}` 不是同一个提交")
    return problems


MIGRATE_PREFIX = 32


def section_bullets(text: str | None, name: str) -> list[str] | None:
    """一份 CHANGELOG 文本里 `## [name]` 小节下的条目行；小节不存在返回 None。

    `v1.0.0` 那一节当年就是带着 v 写的，所以两处都认（与 `CL_HEADING` 同一口径）。
    """
    if text is None:
        return None
    m = re.search(rf"^## \[v?{re.escape(name)}\][^\n]*\n", text, re.M)
    if not m:
        return None
    body = text[m.end():].split("\n## [", 1)[0]
    return [ln for ln in body.splitlines() if ln.startswith("- ")]


def _balanced_inner(text: str, start: int) -> str | None:
    """text[start] 是「（」时，取到配平的「）」，返回括号里的内容；不配平返回 None。"""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "（":
            depth += 1
        elif text[i] == "）":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
    return None


def _col_key(name: str) -> str:
    """列名的比对口径：括号里的注（`Release 发布时间（UTC）`）不参与比较。"""
    return re.sub(r"（[^）]*）", "", name).strip()


COLUMN_PROSE = re.compile(r"([一二三四五六七八九十])列表（")
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def check_column_prose() -> list[str]:
    """「四列表（标签指向 / …）」这种话，列数与点名的列都得等于表头。

    发布记录表后来加过一列（核验），那之前写的句数就旧了：CHANGELOG 写「四列表」，
    维护说明写「五列齐不齐」，同一张表两个数，读者只能猜哪边过时。这里把两处都钉回
    `RELEASE_COLS`。只认括号里点名列数 ≥2 属于这张表的句子，别的「××列表（…）」不追。
    """
    problems: list[str] = []
    keys = {_col_key(c) for c in RELEASE_COLS}
    for path in (ROOT / "CHANGELOG.md", ROOT / RELEASE_DOC):
        text = path.read_text(encoding="utf-8")
        for m in COLUMN_PROSE.finditer(text):
            inner = _balanced_inner(text, m.end() - 1)
            if inner is None:
                problems.append(f"{path.name}: 「{m.group(0)}」后面括号没配平")
                continue
            items = [_col_key(x) for x in inner.split("/") if x.strip()]
            if len(set(items) & keys) < 2:
                continue
            n = CN_NUM.get(m.group(1), -1)
            if n != len(RELEASE_COLS) or len(items) != len(RELEASE_COLS):
                problems.append(
                    f"{path.name}: 写了「{m.group(1)}列表」（={n}）而括号里数了 {len(items)} 项，"
                    f"发布记录表实际 {len(RELEASE_COLS)} 列：{inner[:60]}"
                )
            elif set(items) != keys:
                problems.append(
                    f"{path.name}: 「{m.group(1)}列表」的列名与表头对不上："
                    f"缺 {'、'.join(sorted(keys - set(items))) or '—'}、"
                    f"多 {'、'.join(sorted(set(items) - keys)) or '—'}"
                )
    return problems


def check_release_migration(ver: str, close_sha: str) -> tuple[list[str], str]:
    """收口那次把 Unreleased 并进版本节，沿途一条都不能丢。

    `ver` 用发布记录表里的写法（`v1.3.0`），CHANGELOG 的小节名去掉开头的 v。
    窗口从「这一节第一次被造出来」的前一个提交起算，逐份快照读历史里的
    CHANGELOG（`git show <rev>:CHANGELOG.md`）。这些 blob 在 runner 上根本取不到
    （`actions/checkout` 默认 fetch-depth 1），所以这道只在真值侧跑。

    认身份用前 32 字而不是整行：收口时把条目里的数重写成定版值是正常的
    （1.3.0 那条「当时实测 30 个提交」就是这么改的），改开头要拦——开头一变
    意味着这条被合并或被换掉，那正是悄悄丢条目的样子。
    """
    sec = ver[1:] if ver.startswith("v") else ver
    # 窗口起点用「第一个带着这一节的提交」来找。不用 `git log -S`：那要按字面匹配
    # `## [1.3.0]`，而 1.0.0 那一节写成了 `## [v1.0.0]`，换个写法就查无此节。
    hist = (git_text("log", "--format=%h", "--reverse", close_sha, "--", "CHANGELOG.md") or "").split()
    if not hist:
        return [f"发布记录 {ver}: `{close_sha}` 的历史里没有一个提交动过 CHANGELOG"], ""
    first = next((rev for rev in hist
                  if section_bullets(git_text("show", f"{rev}:CHANGELOG.md"), sec) is not None),
                 None)
    if first is None:
        return [f"发布记录 {ver}: `{close_sha}` 的历史里找不到创建 `## [{sec}]` 的提交，"
                "并条对不上账"], ""
    revs = list(dict.fromkeys(
        [f"{first}^", first,
         *(git_text("log", "--format=%h", f"{first}..{close_sha}", "--", "CHANGELOG.md") or "").split()]
    ))
    seen: dict[str, str] = {}
    problems: list[str] = []
    for rev in revs:
        got = section_bullets(git_text("show", f"{rev}:CHANGELOG.md"), "Unreleased") or []
        heads = [b[:MIGRATE_PREFIX] for b in got]
        if len(heads) != len(set(heads)):
            problems.append(f"发布记录 {ver}: `{rev}` 这份快照的 Unreleased 里有两条"
                            f"前 {MIGRATE_PREFIX} 字相同，这道门分不开它们")
        for b in got:
            seen.setdefault(b[:MIGRATE_PREFIX], rev)
    final = section_bullets(git_text("show", f"{close_sha}:CHANGELOG.md"), sec)
    if final is None:
        return [f"发布记录 {ver}: 收口提交 `{close_sha}` 里没有 `## [{sec}]` 这一节"], ""
    if not seen:
        problems.append(f"发布记录 {ver}: 窗口 {first}..{close_sha[:7]} 里 Unreleased "
                        "一条都没有，这道门没比任何东西——空跑不算过")
    heads = {b[:MIGRATE_PREFIX] for b in final}
    problems += [
        f"发布记录 {ver}: `{rev}` 的 Unreleased 有过这条，收口提交的 `## [{sec}]` 节里没有："
        f"{head}…"
        for head, rev in seen.items() if head not in heads
    ]
    orphans = len([b for b in final if b[:MIGRATE_PREFIX] not in seen])
    if problems:
        return problems, ""
    note = (f"{ver} 的并条：窗口 {len(revs)} 份快照、Unreleased 去重 {len(seen)} 条，"
            f"`## [{sec}]` 节 {len(final)} 条")
    if orphans:
        note += f"（其中 {orphans} 条是收口当场新写的）"
    return problems, note


CL_COUNT = re.compile(
    r"共 (\d+) 条，覆盖 `v(\d+\.\d+\.\d+)` 之后的? (\d+) 个提交"
    r"（PR #(\d+)[-–~]#(\d+) 共 (\d+) 个，加 (\d+) 个直接提交）"
)
# release_stats.py 在区间里没有带 PR 号的提交时，给的是另一种说法。两种都要判，
# 否则「这一版全是直接提交」的那句就正好漏在门外。
CL_COUNT_NOPR = re.compile(
    r"共 (\d+) 条，覆盖 `v(\d+\.\d+\.\d+)` 之后的? (\d+) 个提交"
    r"（没有带 PR 号的提交，加 (\d+) 个直接提交）"
)
# 工具会先打印它数的是哪一节。这行是门的取证入口：数错节就没法从句子本身看出来。
RS_SECTION = re.compile(r"^CHANGELOG 小节：## \[v?([^\]]+)\]$")


def git_text(*args: str) -> str | None:
    proc = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )
    return proc.stdout if proc.returncode == 0 else None


def changelog_sections() -> list[tuple[str, str]]:
    """CHANGELOG 里每个版本小节，带回 (版本号, 正文)。Unreleased 不算小节。

    小节名的写法历史上不统一（1.0.0 那节写成了 `## [v1.0.0]`），这里与 `CL_HEADING`
    一样容忍那个可选的 v——否则那一节的「共 N 条」就落在门的正则之外，门照样绿。
    这条口径本身由 `check_changelog_enum()` 对账，收紧它就是给计数门砍覆盖。
    """
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"^## \[v?(\d+\.\d+\.\d+)\][^\n]*\n", text, re.M):
        out.append((m.group(1), text[m.end() :].split("\n## [", 1)[0]))
    return out


def check_changelog_enum() -> list[str]:
    """同一份 CHANGELOG 有三套正则在数小节，它们必须看到同一批小节。

    `CL_HEADING` 守发布记录表与 compare 落款，`changelog_sections()` 守「共 N 条」
    那句的数，`section_bullets()` 守并条的逐条比对。三处各写死一份「小节名长什么样」，
    收紧任何一处都不会报错——只会让对应那道门少看几节，覆盖静默归零。本轮实测过：
    小节写成 `## [v1.3.0]`、`changelog_sections()` 不认那个 v，计数门整节跳过，
    `--release-truth` 照样全绿。所以拿同一份正文跑三遍，集合不等就红。
    """
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    base = {m[0] for m in CL_HEADING.findall(text)}
    if not base:
        return ["CHANGELOG 一个小节都没被 CL_HEADING 认出来，发布记录那几道门全是空跑"]
    problems: list[str] = []
    got = {v for v, _ in changelog_sections()}
    if got != base:
        problems.append(
            "CHANGELOG 小节集合两处数出来不一样："
            f"CL_HEADING 认得而 changelog_sections 漏了 {sorted(base - got)}，"
            f"反过来 {sorted(got - base)}——收紧任一处正则就是给某道门静默砍覆盖"
        )
    lost = [v for v in sorted(base) if section_bullets(text, v) is None]
    if lost:
        problems.append(
            f"CHANGELOG 的 {'、'.join(lost)} 用 section_bullets 取不到正文，并条门对它是空跑"
        )
    return problems


def changelog_count_claims() -> list[tuple[str, int, int]]:
    """每个写了「共 N 条」的版本节，带回 (版本号, 节首写的条数, 本节实际条数)。

    数没写就不判——1.0.0／1.1.0／1.2.0 三节是收口流程定下来之前的账。
    """
    out: list[tuple[str, int, int]] = []
    for ver, body in changelog_sections():
        lead = body.split("\n\n", 1)[0]
        hit = CL_COUNT.search(lead) or CL_COUNT_NOPR.search(lead)
        if hit:
            out.append((ver, int(hit.group(1)),
                        len([ln for ln in body.splitlines() if ln.startswith("- ")])))
    return out


def check_changelog_counts() -> list[str]:
    """节首那句「共 N 条」必须等于这一节实际数出来的条目——这半句不要 git，所以进 CI。

    计数门整段只在本地真值侧跑（提交数那一半要标签），可条目数那一半只读 CHANGELOG：
    有人把 44 抄成 45，CI 一路放行，线上读者第一眼就挂个错数。同一节里「覆盖 M 个提交」
    那一半这里明确不管——它要 git，本地第十一步管。
    """
    return [
        f"CHANGELOG {ver}: 节首写「共 {stated} 条」，这一节实际 {got} 条"
        "（数的是本节 `- ` 开头的行）"
        for ver, stated, got in changelog_count_claims() if stated != got
    ]


def check_release_counts(tag_names: set[str]) -> tuple[list[str], list[str]]:
    """节首那句「共 N 条 / 覆盖 v_prev 之后 M 个提交」必须等于 git 与 CHANGELOG 现数出来的。

    数没写就不判（1.1.0 / 1.2.0 那两节没有这句，是收口流程定下来之前的账）；
    区间两头（上一版与本版）任一标签本地取不到就记进「跳过」而不是判红——
    发版草案先写节首、标签后落地是正常状态，缺的是取证条件，不是错。
    条目数那一半已经由 `check_changelog_counts()` 在 CI 侧跑过，这里只补提交数那一半。
    """
    problems: list[str] = []
    skipped: list[str] = []
    for ver, body in changelog_sections():
        lead = body.split("\n\n", 1)[0]
        with_pr, no_pr = CL_COUNT.search(lead), CL_COUNT_NOPR.search(lead)
        if not with_pr and not no_pr:
            continue
        if with_pr:
            prev = with_pr.group(2)
            total, lo, hi, prs, direct = (int(with_pr.group(i)) for i in range(3, 8))
        else:
            prev, total, direct = no_pr.group(2), int(no_pr.group(3)), int(no_pr.group(4))
        missing = [f"v{t}" for t in (prev, ver) if f"v{t}" not in tag_names]
        if missing:
            skipped.append(
                f"CHANGELOG {ver}: 本地没有 {'、'.join(missing)} 标签，"
                "那句提交数没法数（先 `git fetch --tags`）"
            )
            continue
        rng = f"v{prev}..v{ver}"
        raw = git_text("rev-list", "--count", rng)
        subs = git_text("log", "--format=%s", rng)
        if raw is None or subs is None:
            problems.append(f"CHANGELOG {ver}: git 数不到 {rng}，那句提交数没法验")
            continue
        got_total = int(raw.strip())
        if got_total != total:
            problems.append(
                f"CHANGELOG {ver}: 节首写 {total} 个提交，`git rev-list --count {rng}` 是 {got_total}"
            )
        found = sorted({int(n.group(1)) for s in subs.splitlines() if (n := PR_NUM.search(s))})
        got_pr = len([s for s in subs.splitlines() if PR_NUM.search(s)])
        got_direct = got_total - got_pr
        # 门与工具是两套实现，各数一遍再对：哪天一边改了取数口径（区间写法、PR 号怎么算），
        # 只靠文本侧的比对看不出来——工具打的数与节首不一致同样报。
        tool = release_stats_line(f"v{prev}", f"v{ver}", ver)
        if tool is None:
            skipped.append(
                f"CHANGELOG {ver}: tools/release_stats.py 按设计拒绝了（多半是本地缺标签），"
                "这一格没跟它对上"
            )
        else:
            used, tool_line = tool
            if used == RS_CRASH:
                problems.append(
                    f"CHANGELOG {ver}: tools/release_stats.py 跑崩了（不是缺标签那种拒绝），"
                    f"这一格的数没跟它对过：{tool_line}")
            elif used is None:
                problems.append(
                    f"CHANGELOG {ver}: 工具跑了但没打出「CHANGELOG 小节：## [...]」那行，"
                    f"门的取数格式对不上它的输出：{tool_line}")
            elif used not in (ver, f"v{ver}"):
                problems.append(
                    f"CHANGELOG {ver}: 让工具数 `## [{ver}]`，它实际数的是 `## [{used}]`"
                    f"（找不到小节会退回 Unreleased，条目数就成了另一节的账）：{tool_line}")
            else:
                t_hit = CL_COUNT.search(tool_line) or CL_COUNT_NOPR.search(tool_line)
                if t_hit is None:
                    problems.append(
                        f"CHANGELOG {ver}: 工具打的那句门的正则认不出：{tool_line}")
                elif t_hit.groups() != (with_pr or no_pr).groups():
                    problems.append(
                        f"CHANGELOG {ver}: 工具数到 {t_hit.groups()}，节首写的是 "
                        f"{(with_pr or no_pr).groups()}——两套实现分家了（工具那句：{tool_line}）"
                    )
        if not with_pr:
            if found:
                problems.append(
                    f"CHANGELOG {ver}: 节首写「没有带 PR 号的提交」，"
                    f"实际 {rng} 里有 PR #{found[0]}–#{found[-1]} 共 {len(found)} 个"
                )
            elif direct != got_total:
                problems.append(
                    f"CHANGELOG {ver}: 没有 PR 号提交时「直接提交」该等于总数，"
                    f"节首写 {direct} 个、总数写 {total} 个、git 是 {got_total} 个"
                )
            continue
        if not found:
            if prs or direct != got_total:
                problems.append(
                    f"CHANGELOG {ver}: {rng} 里没有带 PR 号的提交，节首却写了 PR 区间"
                )
            continue
        if [lo, hi, prs, direct] != [found[0], found[-1], len(found), got_direct]:
            problems.append(
                f"CHANGELOG {ver}: 节首写 PR #{lo}–#{hi} 共 {prs} 个、直接提交 {direct} 个，"
                f"实际 PR #{found[0]}–#{found[-1]} 共 {len(found)} 个、直接提交 {got_direct} 个"
            )
    return problems, skipped


def release_stats_path() -> Path:
    return ROOT / "tools" / "release_stats.py"


def load_release_stats():
    """把 tools/release_stats.py 当模块读进来。

    措辞检查用的必须是工具自己的 `sentence()`，不能在这边再抄一遍模板——
    抄一遍就等于把「两处实现」的漂移重新变成「两处各说各话」。
    """
    path = release_stats_path()
    spec = importlib.util.spec_from_file_location("release_stats", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"{path} 没能建成模块")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_release_wording() -> list[str]:
    """工具拼的那句必须被门的正则原样读回同一批数，两种句式还要互不认领。

    门对「节首没写那句」是静默放行：工具一改措辞、或门一收紧正则，两边就悄悄分家
    ——工具打的句子从此没人对账，而门照绿。这一格把话钉死，顺带钉住两条实测口径：
    手写那一版多一个「的」（定版的 1.3.0 就是这么写的）仍要认，两种句式不能互相认。
    """
    try:
        rs = load_release_stats()
    except Exception as exc:  # noqa: BLE001
        return [f"tools/release_stats.py 读不进来，「工具与门说同一句」没法验：{exc}"]
    cases = [
        ("带 PR 区间",
         rs.sentence(44, "v1.2.0", 33, [25, 41, 42], 15), CL_COUNT,
         ("44", "1.2.0", "33", "25", "42", "3", "15")),
        ("全直接提交",
         rs.sentence(8, "v1.0.0", 18, [], 18), CL_COUNT_NOPR,
         ("8", "1.0.0", "18", "18")),
    ]
    problems: list[str] = []
    for label, sent, rx, want in cases:
        got = rx.search(sent)
        if not got:
            problems.append(
                f"工具打的「{label}」那句门的正则认不出：{sent}\n"
                "    工具与门的措辞分家了——门对认不出的那句静默放行，"
                "改哪一侧都要两边一起改"
            )
        elif got.groups() != want:
            problems.append(
                f"工具打的「{label}」那句被门读回别的数：{got.groups()} != {want}（{sent}）"
            )
        other = CL_COUNT_NOPR if rx is CL_COUNT else CL_COUNT
        if other.search(sent):
            problems.append(f"「{label}」那句被另一种句式也认了，两种句式会互相顶包：{sent}")
    # 手写那一版多个「的」，正则用 `之后的?` 兜住；收紧成必须不带「的」就把已发布的小节判红
    variant = cases[0][1].replace("之后 33 个提交", "之后的 33 个提交")
    hit = CL_COUNT.search(variant)
    if not hit or hit.groups() != cases[0][3]:
        problems.append(f"「之后的」这种手写写法不再被认，已发布的小节会被判成没写数：{variant}")
    return problems


# 工具找不到点名的小节会退回 `## [Unreleased]`（发版草案要靠这个行为数还没归档的条目），
# 那半句提交数又来自同一个 git 区间——张冠李戴之后看上去仍是一次正常对账。
RS_CRASH = "工具自己崩了"


def release_stats_line(frm: str, to: str, section: str) -> tuple[str | None, str] | None:
    """跑一次工具，取回 (它实际数的小节名, 它打的那句)，三种结果含义不同。

    - `None`：工具按设计拒绝（本地缺标签时退出码 2 并打印「FAIL: 本地找不到 …」）。
      缺的是取证条件，调用方记跳过。
    - `(RS_CRASH, 现场)`：工具抛了 traceback。那不是条件不够，是门依赖的实现坏了，
      这一格的数根本没对上，记红。
    - `(小节名, 那句)`：跑通。小节名可能正是 `Unreleased`（工具没找到点名的小节），
      也可能因为它的输出格式漂了而取不到——两种都判红，不许冒充跳过。

    取字节自己解，不用 `text=True, encoding="utf-8"`：子进程是 python，它按控制台编码
    打中文，中文 Windows 上是 GBK，父进程按 utf-8 解会当场解不动。这轮在
    `bash scripts/local-gates.sh` 里就这么崩过一次——reader 线程解码失败之后
    `proc.stdout` 成了 None，`.splitlines()` 抛 AttributeError，整道门以 traceback 收场；
    而我先前手动跑都带着 `PYTHONIOENCODING=utf-8`，所以一直没撞上。
    """
    proc = subprocess.run(
        [sys.executable, str(release_stats_path()),
         "--from", frm, "--to", to, "--section", section],
        capture_output=True, cwd=ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip()
        # 工具按设计拒绝（缺标签、整份 CHANGELOG 没小节）记跳过；自己崩了不能算跳过
        if "Traceback (most recent call last)" in err:
            return RS_CRASH, (err.splitlines() or ["没有 stderr"])[-1]
        return None
    lines = [ln for ln in proc.stdout.decode("utf-8", "replace").splitlines() if ln.strip()]
    used = next((m.group(1) for ln in lines if (m := RS_SECTION.match(ln))), None)
    sent = next((ln for ln in lines if CL_COUNT.search(ln) or CL_COUNT_NOPR.search(ln)),
                lines[-1] if lines else "")
    return used, sent


def check_release_truth(rows: list[dict[str, str]]) -> tuple[list[str], str | None, list[str]]:
    """用 git 与 gh 的现值对账后三列：标签指向、发布时间、收口提交与核验的 run 号。

    返回 (问题, 跳过原因, 比对了什么)。gh 不在或没登录时给跳过原因——本地门的惯例是
    缺可选依赖就 SKIP 并写明怎么补，而不是把别人的机器判成 FAIL。
    """
    problems: list[str] = []
    if not shutil.which("git"):
        return [], "本机没有 git，发布记录的真值没对", []
    out = subprocess.run(
        ["git", "-c", "core.quotePath=false", "for-each-ref",
         "--format=%(refname:short)\t%(objecttype)\t%(objectname)\t%(*objectname)",
         "refs/tags"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )
    if out.returncode != 0:
        return [f"git for-each-ref 失败：{out.stderr.strip()[:200]}"], None, []

    # 附注标签：%(objectname) 是标签对象，%(*objectname) 是它 peel 到的提交；
    # 轻量标签只有前者，后者是空串。表里两种写法都有，所以两列都要比。
    tags: dict[str, set[str]] = {}
    kinds: dict[str, str] = {}
    tag_commits: dict[str, str] = {}
    for line in out.stdout.splitlines():
        fields = (line.split("\t") + ["", "", ""])[:4]
        name, otype, obj, peeled_sha = fields
        if not name:
            continue
        kinds[name] = "附注标签" if otype == "tag" else "轻量标签"
        if otype == "tag":
            tags[name] = {obj, peeled_sha} - {""}
            tag_commits[name] = peeled_sha or obj
        else:
            tags[name] = {obj}
            tag_commits[name] = obj

    listed = {r["版本"] for r in rows}
    for row in rows:
        ver = row["版本"]
        if ver not in tags:
            problems.append(f"发布记录有 {ver}，仓库的 git 标签里没有它")
            continue
        claimed = "附注标签" if "标签对象" in row["标签指向"] else "轻量标签"
        if claimed != kinds[ver]:
            problems.append(
                f"发布记录 {ver}: 表里写成{claimed}，git 里它是{kinds[ver]}"
            )
        gaps = sha_diff(SHA_CELL.findall(row["标签指向"]), sorted(tags[ver]))
        if gaps:
            problems.append(
                f"发布记录 {ver}: {'；'.join(gaps)}（表里 "
                f"{sorted(SHA_CELL.findall(row['标签指向']))}，git 里 {sorted(tags[ver])}）"
            )
    for name in sorted(set(tags) - listed):
        problems.append(f"git 有标签 {name}，发布记录表没有这一行")

    cproblems, cskipped = check_release_counts(set(tags))
    problems += cproblems
    tail = ("；" + "；".join(cskipped)) if cskipped else ""
    notes: list[str] = []
    unrecorded: list[str] = []
    for row in rows:
        ver, close = row["版本"], row["收口提交"]
        shas = SHA_CELL.findall(close)
        if close == "未记录":
            unrecorded.append(ver)
            continue
        if len(shas) != 1 or ver not in tag_commits:
            continue
        cp = check_close_commit(ver, shas[0], tag_commits[ver])
        problems += cp
        # 收口提交本身取不到的时候，并条的窗口也是废的，只报那一条错
        if cp:
            continue
        mproblems, mnote = check_release_migration(ver, shas[0])
        problems += mproblems
        if mnote:
            notes.append(mnote)
    if unrecorded:
        notes.append(f"{'、'.join(unrecorded)} 没收口提交，并条不追（那三轮没做收口）")

    if not shutil.which("gh"):
        return problems, "本机没有 gh，发布时间与核验两列没对上：装上并登录 gh 再跑一次" + tail, notes
    rel = subprocess.run(
        ["gh", "release", "list", "--limit", "100", "--json", "tagName,publishedAt"],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    if rel.returncode != 0:
        return problems, (
            "gh 取不到 Release（多半是没登录），发布时间与核验两列没对上："
            f"{rel.stderr.strip()[:160]}" + tail, notes
        )
    published = {r["tagName"]: r["publishedAt"] for r in json.loads(rel.stdout)}
    for row in rows:
        ver = row["版本"]
        cell = row["Release 发布时间（UTC）"]
        if ver not in published:
            problems.append(f"发布记录有 {ver}，GitHub 上没有这个 Release")
            continue
        want = published[ver].replace("T", " ").replace("Z", "")
        if cell != want:
            problems.append(f"发布记录 {ver}: 表里写 {cell}，gh 的 publishedAt 是 {want}")
    problems += check_run_records(rows)
    return problems, (tail[1:] if tail else None), notes


def run_release_checks(truth: bool) -> int:
    rows = release_table_rows()
    problems = check_release_record(rows)
    if problems:
        print("FAIL: 发布记录表和 CHANGELOG 对不上:")
        print("\n".join(problems[:20]))
        return 1
    # 真值侧的「共 N 条」逐节比对用的是 changelog_sections()，它要是比 CL_HEADING 少认
    # 一节，那一节的数就根本没跑过——先挡住，别让下一行的 ok 冒充「都数过了」
    problems = check_changelog_enum()
    if problems:
        print("FAIL: CHANGELOG 的小节名在几套正则里被数成了不同的集合:")
        print("\n".join(problems[:20]))
        return 1
    print(f"ok: 发布记录表 {len(rows)} 行与 CHANGELOG 的版本/落款/日期一致")
    count_problems = check_changelog_counts()
    if count_problems:
        print("FAIL: CHANGELOG 版本节节首写的「共 N 条」与本节条目数对不上:")
        print("\n".join(count_problems[:20]))
        return 1
    if not truth:
        return 0
    tproblems, skip, notes = check_release_truth(rows)
    if tproblems:
        print("FAIL: 发布记录表与 git 标签 / gh Release 的真值对不上:")
        print("\n".join(tproblems[:20]))
        return 1
    for note in notes:
        print(f"ok: {note}")
    if skip:
        print(f"注意：{skip}")
        return 3
    # 跳过的时候不许打这句：那句是「三列都比过」的成品话，缺 gh 时只比了 git 那半
    print("ok: 发布记录的标签指向/发布时间/收口提交与 run 号、"
          "CHANGELOG 节首的条目数与提交数都等于 git 与 gh 的现值")
    return 0


# ---- 讨论区分类与发帖模板 --------------------------------------------------
# 维护说明写着「分类现有 N 个」「模板目录里的 M 个文件已经对上分类」，两个数都是
# 手抄的。更要紧的是那条功能约定：slug = 中文名 = 模板文件名。模板或分类改名之后
# 页面照常存在、GitHub 只是不把发帖表套到分类上——坏了不报警，所以不能靠人记。
# 文本侧进 CI；GitHub 上到底有哪几个分类、slug 是不是等于名字，要 gh 登录，留给本地门。

TPL_DIR = ".github/DISCUSSION_TEMPLATE"
CAT_COUNT = re.compile(r"分类现有 (\d+) 个")
CAT_LIST = re.compile(r"slug 等于中文名：([^。]+)。")
TPL_SENT = re.compile(r"里的 (\d+) 个文件已经对上分类：([^。]+)。")
CATEGORY_QUERY = (
    "query($owner: String!, $repo: String!) {"
    " repository(owner: $owner, name: $repo) {"
    " discussionCategories(first: 50) { nodes { name slug } } } }"
)


def split_names(blob: str) -> list[str]:
    """「打卡、求助问答（问答）、作品展示」→ 每项取全角括号前的名字。"""
    names = []
    for item in blob.split("、"):
        item = item.strip()
        if item:
            names.append(re.split("（", item, maxsplit=1)[0].strip())
    return names


def template_files() -> list[str]:
    d = ROOT / TPL_DIR
    return sorted(p.stem for p in list(d.glob("*.yml")) + list(d.glob("*.yaml")))


def declared_categories() -> tuple[list[str], int | None] | None:
    """从维护说明那句清单里读出分类名与它自称的个数。"""
    text = (ROOT / RELEASE_DOC).read_text(encoding="utf-8")
    lm = CAT_LIST.search(text)
    if not lm:
        return None
    m = CAT_COUNT.search(text)
    return split_names(lm.group(1)), int(m.group(1)) if m else None


def check_discussion_templates() -> list[str]:
    read = declared_categories()
    if read is None:
        return [f"{RELEASE_DOC}: 找不到「slug 等于中文名：…」那份清单，分类归属没人记了"]
    cats, declared_n = read
    problems: list[str] = []
    if declared_n is None:
        problems.append(f"{RELEASE_DOC}: 找不到「分类现有 N 个」这句")
    elif declared_n != len(cats):
        problems.append(
            f"{RELEASE_DOC}: 写「分类现有 {declared_n} 个」，同一句列出来的名字是 {len(cats)} 个：{cats}"
        )

    text = (ROOT / RELEASE_DOC).read_text(encoding="utf-8")
    tm = TPL_SENT.search(text)
    files = template_files()
    if tm is None:
        problems.append(f"{RELEASE_DOC}: 找不到「里的 M 个文件已经对上分类：…」这句")
        return problems
    declared_t, tpl_names = int(tm.group(1)), split_names(tm.group(2))
    if declared_t != len(files):
        problems.append(f"{RELEASE_DOC}: 写模板目录有 {declared_t} 个文件，实际 {len(files)} 个：{files}")
    if sorted(tpl_names) != files:
        problems.append(
            f"{RELEASE_DOC}: 正文点名的模板 {sorted(tpl_names)} 与 {TPL_DIR}/ 里的 {files} 不是一份"
        )
    for name in tpl_names + files:
        if name not in cats:
            problems.append(f"{name}：不在分类清单里——发帖表套不上，改名要一起改")
    return problems


def check_category_truth() -> tuple[list[str], str | None]:
    """GitHub 上的分类与 slug，对上正文那句清单。返回 (问题, 跳过原因)。"""
    read = declared_categories()
    if read is None:
        return [f"{RELEASE_DOC}: 找不到分类清单，真值没法定位"], None
    cats, _declared_n = read
    if not shutil.which("gh"):
        return [], "本机没有 gh，分类真值没对：装上并登录 gh 再跑一次"
    info = subprocess.run(
        ["gh", "repo", "view", "--json", "owner,name"],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    if info.returncode != 0:
        return [], f"gh 取不到当前仓库（多半没登录），分类真值没对：{info.stderr.strip()[:160]}"
    meta = json.loads(info.stdout)
    got = subprocess.run(
        ["gh", "api", "graphql", "-f", f"owner={meta['owner']['login']}",
         "-f", f"repo={meta['name']}", "-f", "query=" + CATEGORY_QUERY],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    if got.returncode != 0:
        return [f"gh 取分类失败：{got.stderr.strip()[:160]}"], None
    payload = json.loads(got.stdout)
    repo = (payload.get("data") or {}).get("repository")
    if repo is None:
        return [f"GraphQL 没返回 {meta['owner']['login']}/{meta['name']}："
                f"{ascii(payload.get('errors'))[:200]}"], None
    nodes = repo["discussionCategories"]["nodes"]
    real = {n["name"] for n in nodes}
    problems: list[str] = []
    for missing in sorted(real - set(cats)):
        problems.append(f"GitHub 上有分类 {missing}，{RELEASE_DOC} 的清单没写它")
    for gone in sorted(set(cats) - real):
        problems.append(f"{RELEASE_DOC} 写有分类 {gone}，GitHub 上已经没有")
    if len(nodes) != len(real):
        problems.append(f"GitHub 返回 {len(nodes)} 个分类、去重只剩 {len(real)} 个：有同名分类")
    for node in nodes:
        if node["slug"] != node["name"]:
            problems.append(
                f"分类 {node['name']} 的 slug 是 {node['slug']}，"
                f"正文那句「slug 等于中文名」已经不成立"
            )
    return problems, None


def run_category_checks(truth: bool) -> int:
    problems = check_discussion_templates()
    if problems:
        print("FAIL: 讨论区分类与发帖模板对不上:")
        print("\n".join(problems[:20]))
        return 1
    cats, declared_n = declared_categories()
    print(f"ok: 讨论区 {declared_n} 个分类与 {len(template_files())} 个发帖模板逐条对得上")
    if not truth:
        return 0
    tproblems, skip = check_category_truth()
    if tproblems:
        print("FAIL: 分类清单与 GitHub 上的真值对不上:")
        print("\n".join(tproblems[:20]))
        return 1
    if skip:
        print(f"注意：{skip}")
        return 3
    # 同发布记录那道门：缺 gh 时这句没资格打，真值一个都没比
    print("ok: 分类清单等于 GitHub 现存分类，且每个 slug 都等于中文名")
    return 0


# ---- 仓库简介（GitHub About）的动画张数 --------------------------------------
# 简介那句「150 张动画电路图」和 README 的「动画目录是 150 张」是同一个数，但它存在
# GitHub 的仓库设置里、不在任何文件中，check_animation_claims() 七份文件都扫不到它；
# 而它是别人在 GitHub 上搜到本仓库时最先看到的一行。这里用 gh 登录取回现值和 assets/
# 比。不进 CI：runner 上的 gh 没凭证（同分类真值那道门）。

ABOUT_CLAIM_RES = (
    re.compile(r"(\d+)\s*张\s*(?:SMIL\s*)?动画(?:电路图)?"),
)
# 简介该有几处写全库动画张数。写法一改、正则捞空，这道门的覆盖就静默归零——和
# ANIM_CLAIM_EXPECT 同一个手法，反过来再对一次句数。
ABOUT_CLAIM_EXPECT = 1


def about_claim_problems(desc: str, total: int) -> list[str]:
    """简介文本里的动画张数逐个和 assets/ 现数的张数对账。"""
    problems: list[str] = []
    hits = 0
    for rx in ABOUT_CLAIM_RES:
        for m in rx.finditer(desc):
            hits += 1
            if int(m.group(1)) != total:
                problems.append(f"仓库简介写着「{m.group(0)}」，assets/ 实际 {total} 张")
    if hits != ABOUT_CLAIM_EXPECT:
        problems.append(
            f"仓库简介该有 {ABOUT_CLAIM_EXPECT} 处写全库动画张数，正则只捞到 {hits} 处"
            "（简介改写法了？改了要把这里的正则一起补上，别留空门）"
            f"；简介现值：{desc[:120] or '（空的）'}"
        )
    return problems


def check_about_truth(total: int) -> tuple[list[str], str | None]:
    """GitHub 上的仓库简介，对上 assets/ 现数的张数。返回 (问题, 跳过原因)。"""
    if not shutil.which("gh"):
        return [], "本机没有 gh，仓库简介的张数没对：装上并登录 gh 再跑一次"
    got = subprocess.run(
        ["gh", "repo", "view", "--json", "description"],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    if got.returncode != 0:
        return [], (
            f"gh 取不到仓库简介（多半没登录），About 的张数没对：{got.stderr.strip()[:160]}"
        )
    desc = (json.loads(got.stdout) or {}).get("description") or ""
    return about_claim_problems(desc, total), None


def run_about_checks() -> int:
    svgs = sorted((ROOT / "docs" / "circuits" / "assets").glob("*.svg"))
    problems, skip = check_about_truth(len(svgs))
    if problems:
        print("FAIL: 仓库简介（GitHub About）的动画张数和 assets/ 对不上:")
        print("\n".join(problems[:20]))
        return 1
    if skip:
        print(f"注意：{skip}")
        return 3
    print(
        f"ok: 仓库简介里那 {ABOUT_CLAIM_EXPECT} 处动画张数"
        f"等于 assets/ 现数的 {len(svgs)} 张"
    )
    return 0


# ---- 口诀速查页 ------------------------------------------------------------
# docs/口诀速查.md 是全库口诀的自动汇总，由 build_koujue_page() 生成。
# 检查器每次都重新生成一遍并与入库版本比对：口诀在正文里增改之后没重新
# 生成，这里直接红灯。tools/gen_koujue_index.py 是它的命令行入口。

KOUJUE_LINE = re.compile(r"^> \*\*口诀\*\*[　 ](.+?)\s*$")

# 阅读顺序分组。没列进来的文件落进「其他」，不阻塞新页面。
KOUJUE_GROUPS = [
    ("阶段教程", [
        "docs/stages/stage-0-前置知识.md",
        "docs/stages/stage-1-认识BMS.md",
        "docs/stages/stage-2-保护板实践.md",
        "docs/stages/stage-3-AFE-MCU智能BMS.md",
        "docs/stages/stage-4-SOC-SOH算法.md",
        "docs/stages/stage-5-通信与集成.md",
        "docs/stages/stage-6-精通与毕业项目.md",
    ]),
    ("电路详解", [
        "docs/circuits/01-功率回路-MOS保护与预充.md",
        "docs/circuits/02-采样链与AFE芯片.md",
        "docs/circuits/03-充电均衡与计量.md",
        "docs/circuits/04-系统安全与量产.md",
        "docs/circuits/05-BMS电路板绘制与设计要点.md",
        "docs/circuits/动画画风规范.md",
    ]),
    ("专题与工具页", [
        "docs/esp32-bms专题.md",
        "docs/stm32-bms专题.md",
        "docs/budget.md",
        "docs/共建任务板.md",
        "docs/t13-包级手册缺口.md",
        "docs/glossary.md",
        "docs/比喻地图.md",
    ]),
    ("中文导读", [
        "docs/ece5710-notes01-中文导读.md",
        "docs/ece5710-notes02-中文导读.md",
        "docs/ece5710-notes03-中文导读.md",
        "docs/ece5710-notes04-中文导读.md",
        "docs/ece5710-notes05-中文导读.md",
        "docs/ece5710-notes06-中文导读.md",
        "docs/ece5710-notes07-中文导读.md",
        "docs/ece5720-notes01-中文导读.md",
        "docs/ece5720-notes02-中文导读.md",
        "docs/ece5720-notes03-中文导读.md",
        "docs/ece5720-notes04-中文导读.md",
        "docs/ece5720-notes05-中文导读.md",
        "docs/ece5720-notes06-中文导读.md",
        "docs/ece5720-notes07-中文导读.md",
        "docs/renesas-bms-tutorial-中文导读.md",
    ]),
]
KOUJUE_PAGE = "docs/口诀速查.md"


def _koujue_rows(text: str) -> list[tuple[str, str, str]]:
    """一个 md 文件里的全部口诀：[(小节标题, 锚点, 口诀文本), ...]。"""
    rows: list[tuple[str, str, str]] = []
    seen: dict[str, int] = {}
    in_fence = False
    head = ""
    anchor = ""
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        hm = HEADING_RE.match(line)
        if hm and not in_fence:
            head = hm.group(2)
            base = slugify(head)
            n = seen.get(base, 0)
            seen[base] = n + 1
            anchor = base if n == 0 else f"{base}-{n}"
            continue
        km = KOUJUE_LINE.match(line)
        if km and head and not in_fence:
            rows.append((head, anchor, km.group(1)))
    return rows


def _koujue_cell(saying: str) -> str:
    return saying.replace("|", "\\|")


def build_koujue_page() -> str:
    out: list[str] = []
    total = 0
    for gtitle, files in KOUJUE_GROUPS:
        grows: list[str] = []
        for rel in files:
            path = ROOT / rel
            if not path.exists():
                continue
            for head, anchor, saying in _koujue_rows(path.read_text(encoding="utf-8")):
                link = f"{Path(rel).as_posix().removeprefix('docs/')}#{anchor}"
                grows.append(f"| {_koujue_cell(saying)} | [{head}]({link}) |")
        if not grows:
            continue
        total += len(grows)
        out.append(f"## {gtitle}")
        out.append("")
        out.append("| 口诀 | 出处 |")
        out.append("|---|---|")
        out.extend(grows)
        out.append("")
    listed = {rel for _, files in KOUJUE_GROUPS for rel in files}
    others: list[str] = []
    for md in sorted(iter_md(ROOT / "docs")):
        rel = md.relative_to(ROOT).as_posix()
        if rel in listed:
            continue
        for head, anchor, saying in _koujue_rows(md.read_text(encoding="utf-8")):
            link = f"{Path(rel).as_posix().removeprefix('docs/')}#{anchor}"
            others.append(f"| {_koujue_cell(saying)} | [{head}]({link}) |")
    if others:
        total += len(others)
        out.append("## 其他")
        out.append("")
        out.append("| 口诀 | 出处 |")
        out.append("|---|---|")
        out.extend(others)
        out.append("")
    header = (
        "# 口诀速查\n"
        "\n"
        f"> 全仓库 **{total}** 句口诀的自动汇总，抓取自各篇正文——**本页由工具生成，手改会被检查打回**。\n"
        "> 口诀在正文里改了或加了新句，跑 `python3 tools/gen_koujue_index.py` 重新生成；\n"
        "> 忘了重新生成，CI 的文档一致性检查会提醒你。\n"
        "> 口诀只当门牌，不当教材：忘了细节，点出处回到那节的图和账。比喻的用法见 [比喻地图](比喻地图.md)。\n"
        "\n"
    )
    return header + "\n".join(out).rstrip() + "\n"


def check_koujue_index() -> list[str]:
    path = ROOT / KOUJUE_PAGE
    if not path.exists():
        return [f"{KOUJUE_PAGE} 不存在：跑 python3 tools/gen_koujue_index.py 生成"]
    expected = build_koujue_page()
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        note = ""
        for n, (a, e) in enumerate(zip(actual.splitlines(), expected.splitlines(), strict=False), 1):
            if a != e:
                note = f"，第一处差异在第 {n} 行：页里是「{a[:40]}」、重算是「{e[:40]}」"
                break
        return [f"{KOUJUE_PAGE} 与正文口诀不同步{note}。跑 python3 tools/gen_koujue_index.py 重新生成"]
    return []


def main() -> int:
    if "--release-truth" in sys.argv:
        return run_release_checks(truth=True)
    if "--categories-truth" in sys.argv:
        return run_category_checks(truth=True)
    if "--about-truth" in sys.argv:
        return run_about_checks()

    assets = ROOT / "docs" / "circuits" / "assets"
    svgs = sorted(assets.glob("*.svg"))
    if len(svgs) < MIN_SVGS:
        print(f"FAIL: expected >= {MIN_SVGS} SVGs in {assets}, found {len(svgs)}")
        return 1

    # 每个动画的硬性约定：中文 <title>（可访问性）、SMIL 动画元素、深色模式覆盖块。
    bad_svgs: list[str] = []
    for svg in svgs:
        text = svg.read_text(encoding="utf-8")
        title_m = re.search(r"<title\b[^>]*>(.*?)</title>", text, flags=re.DOTALL)
        title_text = re.sub(r"\s+", "", title_m.group(1)) if title_m else ""
        root_tag = re.search(r"<svg\b[^>]*>", text)
        lacks = [
            name
            for name, ok in (
                ("有内容的 <title>", len(title_text) >= 4),
                ("SMIL 动画", "<animate" in text),
                ("深色模式块", "prefers-color-scheme: dark" in text),
                ('role="img"', root_tag is not None and 'role="img"' in root_tag.group(0)),
            )
            if not ok
        ]
        if lacks:
            bad_svgs.append(f"{svg.name}: 缺 {'、'.join(lacks)}")
    if bad_svgs:
        print("FAIL: SVG 约定不满足:")
        print("\n".join(bad_svgs))
        return 1
    print(f"ok: {len(svgs)} SVGs（title / animate / 深色模式 齐全）")

    anim_count, smil_problems = check_smil(svgs)
    if smil_problems:
        print("FAIL: SMIL 动画不合规（浏览器会直接不执行这条动画）:")
        print("\n".join(smil_problems[:50]))
        return 1
    print(f"ok: {anim_count} 个动画元素的 keyTimes/values/attributeName 合规")

    style_problems = check_svg_style(svgs)
    if style_problems:
        print("FAIL: SVG 画风检查（未定义 class / 内联填色 / 字号 <12 / 缺 desc 或 role / desc 复读 title / 画布宽）:")
        print("\n".join(style_problems[:50]))
        return 1
    print("ok: SVG 画风检查通过（豁免清单之外的图）")

    stage_problems = check_stage_counts()
    if stage_problems:
        print("FAIL: README 阶段表的动画张数和正文对不上:")
        print("\n".join(stage_problems[:50]))
        return 1
    print("ok: README 阶段表的「本章动画」与各篇正文嵌入数一致")

    claim_problems = check_animation_claims(len(svgs))
    if claim_problems:
        print("FAIL: 手写的「全库多少张动画」和 assets/ 对不上:")
        print("\n".join(claim_problems[:50]))
        return 1
    print(
        f"ok: {len(ANIM_CLAIM_FILES)} 个文件里 "
        f"{sum(ANIM_CLAIM_EXPECT.values())} 处手写的动画张数都等于 assets/ 的 {len(svgs)} 张"
    )

    koujue_problems = check_koujue_index()
    if koujue_problems:
        print("FAIL: 口诀速查页和正文口诀对不上:")
        print("\n".join(koujue_problems[:50]))
        return 1
    print("ok: 口诀速查页与正文口诀同步")

    index_problems = check_svg_index(svgs)
    if index_problems:
        print("FAIL: 动画索引和 assets/ 清单对不上:")
        print("\n".join(index_problems[:50]))
        return 1
    print("ok: 动画索引与 assets/ 双向一致（无孤儿图、无死行）")

    exclude_problems = check_lychee_exclude()
    if exclude_problems:
        print("FAIL: 外链排除清单和文档对不上:")
        print("\n".join(exclude_problems[:20]))
        return 1
    print(f"ok: 排除域名清单与文档数量/逐条说明一致（{len(exclude_entries())} 条）")

    rows = release_table_rows()
    release_problems = check_release_record(rows)
    if release_problems:
        print("FAIL: 发布记录表和 CHANGELOG 对不上:")
        print("\n".join(release_problems[:20]))
        return 1
    print(f"ok: 发布记录表 {len(rows)} 行与 CHANGELOG 的版本/落款/日期一致")

    tag_problems = check_runner_no_tags()
    if tag_problems:
        print("FAIL: 「runner 数不到标签」这句和 .github/workflows 的现值对不上:")
        print("\n".join(tag_problems[:20]))
        return 1
    print(
        f"ok: 真值门不进 CI 的理由对得上现值（{len(workflow_files())} 个 workflow / "
        f"{len(checkout_steps())} 处 checkout，没有一处改 fetch-depth）"
    )

    list_problems = check_local_gate_lists()
    if list_problems:
        print("FAIL: 本地门的步数清单四处抄本和脚本实际吐出的标签对不上:")
        print("\n".join(list_problems[:20]))
        return 1
    print(
        "ok: 本地门的步骤清单四处同一份——脚本吐的标签 = 两份头注释的本地专属名单 "
        "= CONTRIBUTING 的箭头串与前/后步数 = 各处「第 N 步「××对账」」的序号"
    )

    latest_problems = check_latest_claims()
    if latest_problems:
        print("FAIL: 门面写的「最近更新」版本和发布记录表最新那一版对不上:")
        print("\n".join(latest_problems[:20]))
        return 1
    newest, _ = newest_release()
    print(f"ok: 门面的「最近更新」三处都指向 {newest}")

    archive_problems = check_release_archive()
    if archive_problems:
        print("FAIL: 收口漏了「搬」这一步，同一条目在 Unreleased 和版本节各留了一份:")
        print("\n".join(archive_problems[:20]))
        return 1
    dynamic_problems = check_release_dynamic()
    if dynamic_problems:
        print("FAIL: 更新动态本页目录的分组与发布记录表对不上:")
        print("\n".join(dynamic_problems[:20]))
        return 1
    dyn_line, dyn_items = dynamic_group(newest[1:])
    print(f"ok: {newest} 的条目已全部搬进版本节（Unreleased 与它零重复），"
          f"更新动态本页目录 {len(dynamic_groups())} 个分组都真在发布记录表里"
          f"（最新那一版的分组带 {dyn_items} 条小节链接）")

    wording_problems = check_release_wording()
    if wording_problems:
        print("FAIL: tools/release_stats.py 打的那句与 check_docs 的正则不是同一句话:")
        print("\n".join(wording_problems[:20]))
        return 1
    print("ok: 工具与门对「节首那句」说的是同一句——两种句式都原样读回同一批数")

    enum_problems = check_changelog_enum()
    if enum_problems:
        print("FAIL: CHANGELOG 的小节名在几套正则里被数成了不同的集合:")
        print("\n".join(enum_problems[:20]))
        return 1
    print("ok: CHANGELOG 小节集合三套正则（CL_HEADING / changelog_sections / "
          "section_bullets）看到的是同一批节")

    claims = changelog_count_claims()
    count_problems = check_changelog_counts()
    if count_problems:
        print("FAIL: CHANGELOG 版本节节首写的「共 N 条」与本节条目数对不上:")
        print("\n".join(count_problems[:20]))
        return 1
    print("ok: 写了「共 N 条」的版本节（"
          + "、".join(f"{ver} 节 {stated} 条" for ver, stated, _ in claims)
          + "）每节的条数都等于本节实际数出来的；「覆盖 M 个提交」那一半要 git，本地第十一步管")

    tpl_problems = check_discussion_templates()
    if tpl_problems:
        print("FAIL: 讨论区分类与发帖模板对不上:")
        print("\n".join(tpl_problems[:20]))
        return 1
    _cats, cats_n = declared_categories()
    print(f"ok: 讨论区 {cats_n} 个分类与 {len(template_files())} 个发帖模板逐条对得上")

    for rel in ("code/soc", "code/protocol", "code/firmware", "code/README.md"):
        if not (ROOT / rel).exists():
            print(f"FAIL: missing {rel}")
            return 1
    print("ok: code packages present")

    missing: list[str] = []
    bad_anchors: list[str] = []
    checked = 0
    anchor_cache: dict[Path, set[str]] = {}

    for md in iter_md(ROOT):
        text = strip_code(md.read_text(encoding="utf-8"))
        for _label, raw in LINK_RE.findall(text):
            url = raw.strip().split()[0]
            if url.startswith(("http://", "https://", "mailto:")):
                continue
            path_part, _, frag = url.partition("#")
            if not path_part:
                # 纯页内锚点：README 与 bms-resources 等页的目录跳转用这种，
                # 对同一文件的标题 slug 校验
                if frag and md.suffix == ".md":
                    if md not in anchor_cache:
                        anchor_cache[md] = anchors_of(md)
                    if frag not in anchor_cache[md]:
                        bad_anchors.append(f"{md.relative_to(ROOT).as_posix()}: {url}")
                continue
            if path_part.endswith((".", " ")):
                # Windows 会吃掉路径结尾的点和空格：`docs/...` 在本机解析成
                # `docs`、判它存在，Linux 上同一句是死链。这种写法哪边都不该有，
                # 直接判坏，别靠本机绿灯。
                missing.append(f"{md.relative_to(ROOT).as_posix()}: {url}")
                continue
            target = (md.parent / path_part).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                continue
            checked += 1
            if not target.exists():
                missing.append(f"{md.relative_to(ROOT).as_posix()}: {url}")
                continue
            # 锚点校验：链接指向的章节被改名时，"文件存在"检查发现不了。
            # .md 用 GitHub 标题 slug，.html 用 id 属性。
            if frag and target.suffix == ".md":
                if target not in anchor_cache:
                    anchor_cache[target] = anchors_of(target)
                if frag not in anchor_cache[target]:
                    bad_anchors.append(f"{md.relative_to(ROOT).as_posix()}: {url}")
            elif frag and target.suffix == ".html":
                if target not in anchor_cache:
                    anchor_cache[target] = anchors_of_html(target)
                if frag not in anchor_cache[target]:
                    bad_anchors.append(f"{md.relative_to(ROOT).as_posix()}: {url}")

    if missing:
        print("FAIL: broken relative links:")
        print("\n".join(missing[:50]))
        return 1
    print(f"ok: {checked} relative file links exist")

    if bad_anchors:
        print("FAIL: anchors not found in target file:")
        print("\n".join(bad_anchors[:50]))
        return 1
    print(f"ok: anchors in {len(anchor_cache)} files resolve")

    hygiene = check_markdown_hygiene()
    if hygiene:
        print("FAIL: Markdown 公式里有控制字符，或仍用 \\( \\) 定界:")
        print("\n".join(hygiene[:50]))
        return 1
    print("ok: markdown has no control characters or \\( \\) math delimiters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
