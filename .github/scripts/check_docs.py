#!/usr/bin/env python3
"""轻量文档一致性：SVG 数量、阶段表张数、关键 code 路径、Markdown 相对链接与锚点存在性。"""
from __future__ import annotations

import json
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
# 下界必须跟着实际发货量走——当前 148 张；
# 停在旧值会让"删掉一半动画"这种回退静默通过。
MIN_SVGS = 148

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


# 全库动画张数是人手写的，一共四处：README 两句、门户 HTML 三句、动画索引的标题
# （中文数字）和正文、路线图 SVG 的 desc 与底栏胶囊。147→148 那轮就漂了：README 和
# 索引跟着改，门户 HTML、路线图动画、社交卡位图还写 147——门户那张图甚至是首页第一屏。
# 所以让脚本去数 assets/，写的数对不上就红。CHANGELOG 不在扫描范围：历史条目不改写，
# 里面「147 张」是当时的真话。
ANIM_CLAIM_FILES = (
    "README.md",
    "BMS学习路径.html",
    "docs/circuits/README.md",
    "docs/circuits/assets/bms-roadmap.svg",
)
ANIM_CLAIM_RES = (
    re.compile(r"动画目录是\s*\**(\d+)\**\s*张"),
    re.compile(r"仓库里一共\s*(\d+)\s*张"),
    re.compile(r"(\d+)\s*张\s*(?:SMIL\s*)?动画"),
    re.compile(r"电路动画(?:与详解)?\s*[×xX](\d+)"),
)
CN_CLAIM_RE = re.compile(r"([零一二三四五六七八九十百]+)张动画与电路图")
CN_DIGIT = {c: i for i, c in enumerate("零一二三四五六七八九")}
CN_UNIT = {"十": 10, "百": 100}


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
        for rx in ANIM_CLAIM_RES:
            for m in rx.finditer(text):
                if int(m.group(1)) != total:
                    problems.append(f"{rel}: 写着「{m.group(0)}」，assets/ 实际 {total} 张")
        for m in CN_CLAIM_RE.finditer(text):
            if cn_to_int(m.group(1)) != total:
                problems.append(f"{rel}: 写着「{m.group(0)}」，assets/ 实际 {total} 张")
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


def check_release_truth(rows: list[dict[str, str]]) -> tuple[list[str], str | None]:
    """用 git 与 gh 的现值对账后三列：标签指向、发布时间、收口提交与核验的 run 号。

    返回 (问题, 跳过原因)。gh 不在或没登录时给跳过原因——本地门的惯例是
    缺可选依赖就 SKIP 并写明怎么补，而不是把别人的机器判成 FAIL。
    """
    problems: list[str] = []
    if not shutil.which("git"):
        return [], "本机没有 git，发布记录的真值没对"
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
        return [f"git for-each-ref 失败：{out.stderr.strip()[:200]}"], None

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

    for row in rows:
        ver, close = row["版本"], row["收口提交"]
        shas = SHA_CELL.findall(close)
        if close == "未记录" or len(shas) != 1 or ver not in tag_commits:
            continue
        problems += check_close_commit(ver, shas[0], tag_commits[ver])

    if not shutil.which("gh"):
        return problems, "本机没有 gh，发布时间与核验两列没对上：装上并登录 gh 再跑一次"
    rel = subprocess.run(
        ["gh", "release", "list", "--limit", "100", "--json", "tagName,publishedAt"],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    if rel.returncode != 0:
        return problems, (
            "gh 取不到 Release（多半是没登录），发布时间与核验两列没对上："
            f"{rel.stderr.strip()[:160]}"
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
    return problems, None


def run_release_checks(truth: bool) -> int:
    rows = release_table_rows()
    problems = check_release_record(rows)
    if problems:
        print("FAIL: 发布记录表和 CHANGELOG 对不上:")
        print("\n".join(problems[:20]))
        return 1
    print(f"ok: 发布记录表 {len(rows)} 行与 CHANGELOG 的版本/落款/日期一致")
    if not truth:
        return 0
    tproblems, skip = check_release_truth(rows)
    if tproblems:
        print("FAIL: 发布记录表与 git 标签 / gh Release 的真值对不上:")
        print("\n".join(tproblems[:20]))
        return 1
    print("ok: 发布记录的标签指向/发布时间/收口提交与 run 号都等于 git 与 gh 的现值")
    if skip:
        print(f"注意：{skip}")
        return 3
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
    print(f"ok: 四处手写的动画张数都等于 assets/ 的 {len(svgs)} 张")

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
