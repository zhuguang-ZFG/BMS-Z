#!/usr/bin/env python3
"""把旧画风 SVG 迁到动画画风规范。

做的事：Tailwind 色改成 Primer 类（含 prefers-color-scheme）、等宽字体、
字号至少 12、role=img、desc、①②③ 步骤卡、缺的底部读数栏、循环收到 8 或 12 秒。
底栏横轴标题调用 gen_mechanism_svgs.axis_title_xy，不再压在最后一个刻度上。

不改 code/。不新增 SVG。曲线和原有数字留在图里，示意句标明「示意」。

    python3 tools/reskin_legacy_svgs.py
    python3 tools/reskin_legacy_svgs.py c-rate.svg li-ion-working.svg
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_mechanism_svgs import axis_title_xy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "circuits" / "assets"
BASELINE = ROOT / ".github" / "scripts" / "svg_style_baseline.txt"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)

# 第 3 批要重画的「只有框」图。本批不改，豁免清单里只留它们。
LEAVE = {
    "afe-register-read.svg",
    "gbt-27930-handshake.svg",
    "gate-return-loop.svg",
    "hvil-loop.svg",
    "smbus-sbs-roundtrip.svg",
    "short-i2t-window.svg",
    "overdischarge-copper.svg",
}

# 已经是 Primer 色，但没有 ①②③ 步骤卡。
PRIMER = {
    "balance-scheduling.svg",
    "cell-reversal.svg",
    "contactor-weld-check.svg",
    "dtc-snapshot.svg",
    "esp32-sleep-current.svg",
    "hil-testbench.svg",
    "mqtt-pubsub-will.svg",
    "open-wire-detection.svg",
    "polarization-physics.svg",
    "watchdog-safestate.svg",
}

HEADER = 156
ANIM = {"animate", "animatemotion", "animatetransform", "set"}

CURATED: dict[str, list[str]] = {
    "bms-roadmap.svg": [
        "从阶段 0 的电芯走到阶段 6 的产品级系统。",
        "绿点沿时间轴巡游，每个阶段停一下。",
        "节点下是建议用时。业余每天 1–2 小时。",
        "底下三枚仍是 147 张动画、配套和书单。",
    ],
    "li-ion-working.svg": [
        "充电半圈：锂离子经电解液嵌进负极。",
        "电子不穿隔膜，经充电器走外电路。",
        "放电半圈：锂离子回正极，电子经负载做功。",
        "两段各占半个循环。离子和箭头是示意。",
    ],
    "c-rate.svg": [
        "同一块电池，龙头开度就是倍率。",
        "卡通按 10 Ah：0.5C=5 A，1C=10 A，2C=20 A。",
        "C 跟着容量走。10 A 对 20 Ah 只是 0.5C。",
        "底栏直线 I=20 Ah×C。0.5C→10 A，2C→40 A。示意。",
    ],
    "cc-cv.svg": [
        "先恒流：电流不动，电压往上爬。",
        "到 4.2 V 改恒压，电流自己往下落。",
        "电压刚到 4.2 V 还不叫充满。",
        "示意 2 Ah：恒流约 1.6 Ah，恒压再约 0.3 Ah。",
    ],
    "internal-resistance.svg": [
        "带载时端电压腿软，卸掉负载会回弹。",
        "底栏 ΔV=I×R。20 A、20 mΩ 掉 0.40 V。",
        "同一电流，60 mΩ 掉 1.20 V。",
        "黄点沿 20 mΩ 那条走。数字是示意。",
    ],
    "ocv-soc-curve.svg": [
        "开路电压对荷电，铁锂中间有一段平台。",
        "平台上斜率很小，几十毫伏能换很多荷电。",
        "两端变陡，同样的毫伏换到的荷电少。",
        "底栏数字是示意，不是某一颗电芯的实测。",
    ],
    "series-parallel-pack.svg": [
        "串联加的是电压，并联加的是容量。",
        "底栏 V=3.7 V×串数。4 串是 14.8 V。",
        "并联不抬电压，只把安时加起来。",
        "3.7 V 是这张图的示意单体电压。",
    ],
    "cell-inconsistency-barrel.svg": [
        "串联能放出的安时，等于最弱那一节。",
        "别的节还剩电，整包也先被最弱节叫停。",
        "底栏：另外三节 50 Ah 时，可用的是最弱节。",
        "木桶是示意，不是某一包的配组记录。",
    ],
    "hil-testbench.svg": [
        "电芯模拟器假装一串可编程电压。",
        "故障注入矩阵做断线、短接，不在真电池上玩火。",
        "被测 BMS 跑真实固件，上位机逐项核对。",
        "底栏四步累计 4.5 s。不是产线节拍标准。",
    ],
    "mux-time-skew.svg": [
        "16 串轮流采样，每串示意 100 µs，一圈 1.6 ms。",
        "这一圈里电流如果涨了 50 A，首尾不是同一瞬间。",
        "1 mΩ×50 A=50 mV。第 1 串 3.700 V，第 16 串 3.650 V。",
        "把 16 个数当成同时，就会对着这 50 mV 去均衡。示意。",
    ],
    "mqtt-pubsub-will.svg": [
        "网关把遥测发布到 Broker，订阅端按主题收。",
        "连接时先登记遗嘱：主题和离线内容。",
        "异常断连，Broker 才代发。正常断开不发。",
        "蓝点是数据包，红点是遗嘱。示意，不是抓包。",
    ],
}


def q(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def norm(value: str | None) -> str:
    if not value:
        return ""
    h = value.strip().lower()
    if len(h) == 4 and h.startswith("#"):
        h = "#" + "".join(ch * 2 for ch in h[1:])
    return h


def lum(h: str) -> float:
    raw = h.lstrip("#")
    r, g, b = (int(raw[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a: str, b: str) -> float:
    hi, lo = max(lum(a), lum(b)), min(lum(a), lum(b))
    return (hi + 0.05) / (lo + 0.05)


TEXT_FILL = {
    "#1e293b": "txt",
    "#334155": "txt",
    "#0f172a": "txt",
    "#475569": "small",
    "#64748b": "small",
    "#94a3b8": "small",
    "#1e40af": "hi",
    "#1d4ed8": "hi",
    "#1e3a8a": "hi",
    "#2563eb": "hi",
    "#3b82f6": "hi",
    "#60a5fa": "hi",
    "#065f46": "ok",
    "#059669": "ok",
    "#047857": "ok",
    "#166534": "ok",
    "#10b981": "ok",
    "#991b1b": "warn",
    "#dc2626": "warn",
    "#b91c1c": "warn",
    "#ef4444": "warn",
    "#92400e": "gold",
    "#b45309": "gold",
    "#9a6700": "gold",
    "#f59e0b": "gold",
    "#fbbf24": "gold",
    "#d97706": "gold",
    "#fff": "on",
    "#ffffff": "on",
}

SHAPE_FILL = {
    "#f8fafc": "bg",
    "#f1f5f9": "panel",
    "#eff6ff": "fill-boxb",
    "#dbeafe": "fill-boxb",
    "#bfdbfe": "fill-boxb",
    "#93c5fd": "fill-boxb",
    "#ecfdf5": "fill-boxg",
    "#a7f3d0": "fill-boxg",
    "#86efac": "fill-boxg",
    "#6ee7b7": "fill-boxg",
    "#fef2f2": "fill-boxr",
    "#fecaca": "fill-boxr",
    "#fca5a5": "fill-boxr",
    "#fffbeb": "fill-boxy",
    "#fef3c7": "fill-boxy",
    "#2563eb": "fill-b",
    "#1d4ed8": "fill-b",
    "#3b82f6": "fill-b",
    "#1e40af": "fill-b",
    "#1e3a8a": "fill-b",
    "#60a5fa": "fill-b",
    "#059669": "fill-g",
    "#10b981": "fill-g",
    "#065f46": "fill-g",
    "#047857": "fill-g",
    "#dc2626": "fill-r",
    "#ef4444": "fill-r",
    "#991b1b": "fill-r",
    "#b91c1c": "fill-r",
    "#f59e0b": "fill-y",
    "#b45309": "fill-y",
    "#bf8700": "fill-y",
    "#92400e": "fill-y",
    "#fbbf24": "fill-y",
    "#475569": "fill-ink",
    "#334155": "fill-ink",
    "#1e293b": "fill-ink",
    "#64748b": "fill-ink",
    "#0f172a": "fill-ink",
    "#94a3b8": "fill-muted",
    "#cbd5e1": "fill-muted",
    "#e2e8f0": "fill-muted",
}

STROKE = {
    "#e2e8f0": "stroke-panel",
    "#cbd5e1": "stroke-panel",
    "#f1f5f9": "stroke-panel",
    "#64748b": "stroke-axis",
    "#94a3b8": "stroke-axis",
    "#475569": "stroke-axis",
    "#334155": "stroke-axis",
    "#1e293b": "stroke-axis",
    "#2563eb": "stroke-b",
    "#1d4ed8": "stroke-b",
    "#3b82f6": "stroke-b",
    "#60a5fa": "stroke-b",
    "#1e40af": "stroke-b",
    "#bfdbfe": "stroke-b",
    "#93c5fd": "stroke-b",
    "#059669": "stroke-g",
    "#10b981": "stroke-g",
    "#047857": "stroke-g",
    "#a7f3d0": "stroke-g",
    "#065f46": "stroke-g",
    "#dc2626": "stroke-r",
    "#ef4444": "stroke-r",
    "#fecaca": "stroke-r",
    "#991b1b": "stroke-r",
    "#5b21b6": "stroke-b",
    "#7c3aed": "stroke-b",
    "#b45309": "stroke-y",
    "#f59e0b": "stroke-y",
    "#92400e": "stroke-y",
    "#fbbf24": "stroke-y",
    "#fff": "stroke-check",
    "#ffffff": "stroke-check",
}

GRAY_STROKE = {"#e2e8f0", "#cbd5e1", "#f1f5f9"}

# 已经用类名、但色值还是 Tailwind 的图，按浅色段 / 深色段分别换。
LIGHT_HEX = {
    "#0f172a": "#0d1117",
    "#f8fafc": "#ffffff",
    "#1e293b": "#1f2328",
    "#334155": "#1f2328",
    "#475569": "#57606a",
    "#64748b": "#57606a",
    "#94a3b8": "#57606a",
    "#2563eb": "#0969da",
    "#1d4ed8": "#0969da",
    "#1e40af": "#0969da",
    "#3b82f6": "#0969da",
    "#059669": "#1a7f37",
    "#10b981": "#1a7f37",
    "#047857": "#1a7f37",
    "#065f46": "#1a7f37",
    "#dc2626": "#cf222e",
    "#ef4444": "#cf222e",
    "#991b1b": "#cf222e",
    "#b45309": "#9a6700",
    "#92400e": "#9a6700",
    "#f59e0b": "#9a6700",
    "#f1f5f9": "#f4f6f8",
    "#e2e8f0": "#d0d7de",
    "#cbd5e1": "#d0d7de",
    "#eff6ff": "#ddf4ff",
    "#dbeafe": "#ddf4ff",
    "#ecfdf5": "#dafbe1",
    "#fffbeb": "#fff8c5",
    "#fef3c7": "#fff8c5",
    "#fde68a": "#fff8c5",
    "#fff7ed": "#fff8c5",
}
DARK_HEX = {
    "#0f172a": "#0d1117",
    "#1e293b": "#161b22",
    "#334155": "#30363d",
    "#475569": "#8b949e",
    "#64748b": "#8b949e",
    "#94a3b8": "#8b949e",
    "#f1f5f9": "#e6edf3",
    "#e2e8f0": "#e6edf3",
    "#cbd5e1": "#8b949e",
    "#60a5fa": "#4493f8",
    "#93c5fd": "#4493f8",
    "#34d399": "#3fb950",
    "#6ee7b7": "#3fb950",
    "#f87171": "#ff7b72",
    "#fca5a5": "#ff7b72",
    "#fbbf24": "#d29922",
    "#fdba74": "#d29922",
    "#172554": "#12233a",
    "#052e16": "#0f2415",
    "#431407": "#2d2607",
    "#451a03": "#2d2607",
    "#78350f": "#2d2607",
    "#022c22": "#0f2415",
    "#1e3a8a": "#12233a",
}


def remap_hex(text: str, table: dict[str, str]) -> str:
    def sub(match: re.Match[str]) -> str:
        return table.get(norm(match.group(0)), match.group(0))

    return re.sub(r"#[0-9a-fA-F]{3,8}", sub, text)


def remap_style_text(text: str) -> str:
    text = re.sub(
        r"font-family\s*:[^;{]*Segoe[^;{]*;",
        "font-family: ui-monospace, Consolas, monospace;",
        text,
    )
    match = re.search(
        r"@media\s*\(\s*prefers-color-scheme\s*:\s*dark\s*\)\s*\{",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return remap_hex(text, LIGHT_HEX)
    start = match.end()
    depth = 1
    index = start
    while index < len(text) and depth:
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
        index += 1
    light = remap_hex(text[: match.start()], LIGHT_HEX)
    dark_body = remap_hex(text[start : index - 1], DARK_HEX)
    return light + text[match.start() : start] + dark_body + remap_style_text(text[index:])


def is_boilerplate_style(text: str) -> bool:
    return '[fill="#' in text or "rect[fill=" in text


def keep_class_rules(text: str) -> str:
    """属性选择器那块整段删掉时，把 .lt / .dk 这种类规则留下来。"""
    kept: list[str] = []
    for block in re.findall(r"(\.[-a-zA-Z_][\w-]*\s*\{[^}]*\})", text):
        if "[fill=" in block or "rect[fill=" in block:
            continue
        kept.append(block)
    dark = []
    match = re.search(
        r"@media\s*\(\s*prefers-color-scheme\s*:\s*dark\s*\)\s*\{",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        start = match.end()
        depth = 1
        index = start
        while index < len(text) and depth:
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
            index += 1
        body = text[start : index - 1]
        for block in re.findall(r"(\.[-a-zA-Z_][\w-]*\s*\{[^}]*\})", body):
            dark.append(block)
    if not kept and not dark:
        return ""
    parts = kept[:]
    if dark:
        parts.append(
            "@media (prefers-color-scheme: dark) {\n      " + "\n      ".join(dark) + "\n    }"
        )
    return "\n    ".join(parts)


def add_spec_style(root: ET.Element) -> None:
    style = ET.Element(q("style"))
    style.text = STYLE
    styles = [el for el in root if local(el.tag) == "style"]
    if styles:
        root.insert(list(root).index(styles[-1]) + 1, style)
        return
    desc = next((el for el in root if local(el.tag) == "desc"), None)
    title = next((el for el in root if local(el.tag) == "title"), None)
    anchor = desc if desc is not None else title
    if anchor is not None:
        root.insert(list(root).index(anchor) + 1, style)
    else:
        root.insert(0, style)


def retint_styles(root: ET.Element) -> None:
    """删掉属性选择器那块深色覆盖，留下具名类并换成 Primer 色。"""
    for el in list(root):
        if local(el.tag) != "style":
            continue
        body = el.text or ""
        if is_boilerplate_style(body):
            kept = keep_class_rules(body)
            if not kept:
                root.remove(el)
                continue
            el.text = kept
            continue
        el.text = remap_style_text(body)
        bump_font_css(el)
    add_spec_style(root)

STYLE = """
    .bg { fill: #ffffff; }
    .panel { fill: #f4f6f8; stroke: #d0d7de; }
    .fill-boxb { fill: #ddf4ff; }
    .fill-boxg { fill: #dafbe1; }
    .fill-boxr { fill: #ffebe9; }
    .fill-boxy { fill: #fff8c5; }
    .fill-b { fill: #0969da; }
    .fill-g { fill: #1a7f37; }
    .fill-r { fill: #cf222e; }
    .fill-y { fill: #9a6700; }
    .fill-ink { fill: #57606a; }
    .fill-muted { fill: #e2e8f0; }
    .fill-lockb { fill: #0969da; }
    .stroke-panel { stroke: #d0d7de; }
    .stroke-axis { stroke: #57606a; }
    .stroke-b { stroke: #0969da; }
    .stroke-g { stroke: #1a7f37; }
    .stroke-r { stroke: #cf222e; }
    .stroke-y { stroke: #bf8700; }
    .stroke-check { stroke: #ffffff; }
    .axis { stroke: #57606a; stroke-width: 1.5; fill: none; }
    .grid { stroke: #d0d7de; stroke-width: 1; fill: none; }
    .txt { fill: #1f2328; font-size: 13px; }
    .small { fill: #57606a; font-size: 12px; }
    .title { fill: #1f2328; font-size: 16px; font-weight: bold; }
    .hi { fill: #0969da; }
    .warn { fill: #cf222e; }
    .ok { fill: #1a7f37; }
    .gold { fill: #9a6700; }
    .on { fill: #ffffff; font-size: 13px; font-weight: bold; }
    .lineb { stroke: #0969da; stroke-width: 2.5; fill: none; }
    @media (prefers-color-scheme: dark) {
      .bg { fill: #0d1117; }
      .panel { fill: #161b22; stroke: #30363d; }
      .fill-boxb { fill: #12233a; }
      .fill-boxg { fill: #0f2415; }
      .fill-boxr { fill: #3d1214; }
      .fill-boxy { fill: #2d2607; }
      .fill-b { fill: #4493f8; }
      .fill-g { fill: #3fb950; }
      .fill-r { fill: #ff7b72; }
      .fill-y { fill: #d29922; }
      .fill-ink { fill: #8b949e; }
      .fill-muted { fill: #30363d; }
      .fill-lockb { fill: #0969da; }
      .stroke-panel { stroke: #30363d; }
      .stroke-axis { stroke: #8b949e; }
      .stroke-b { stroke: #4493f8; }
      .stroke-g { stroke: #3fb950; }
      .stroke-r { stroke: #ff7b72; }
      .stroke-y { stroke: #d29922; }
      .stroke-check { stroke: #0d1117; }
      .axis { stroke: #8b949e; }
      .grid { stroke: #30363d; }
      .txt { fill: #e6edf3; }
      .small { fill: #8b949e; }
      .title { fill: #e6edf3; }
      .hi { fill: #4493f8; }
      .warn { fill: #ff7b72; }
      .ok { fill: #3fb950; }
      .gold { fill: #d29922; }
      .on { fill: #ffffff; }
      .lineb { stroke: #4493f8; }
    }
"""

STEP_KT = "0;0.2490;0.2500;0.4990;0.5000;0.7490;0.7500;1"
STEP_OP = (
    "1;1;0.28;0.28;0.28;0.28;0.28;0.28",
    "0.28;0.28;1;1;0.28;0.28;0.28;0.28",
    "0.28;0.28;0.28;0.28;1;1;0.28;0.28",
    "0.28;0.28;0.28;0.28;0.28;0.28;1;1",
)


def parse_s(token: str) -> float | None:
    token = token.strip()
    if token.endswith("s"):
        try:
            return float(token[:-1])
        except ValueError:
            return None
    return None


def fmt_s(value: float) -> str:
    if abs(value - round(value)) < 1e-6:
        return f"{int(round(value))}s"
    return f"{value:.4g}s"


def bump_font_attr(el: ET.Element) -> None:
    raw = el.get("font-size")
    if not raw:
        return
    try:
        num = float(raw.lower().replace("px", ""))
    except ValueError:
        return
    if num < 12:
        el.set("font-size", "12")


def bump_font_css(style_el: ET.Element) -> None:
    text = style_el.text or ""

    def repl(match: re.Match[str]) -> str:
        num = float(match.group(1))
        if num < 12:
            return "font-size: 12px"
        return match.group(0)

    style_el.text = re.sub(
        r"font-size\s*:\s*([0-9.]+)\s*px", repl, text, flags=re.IGNORECASE
    )


def animated(el: ET.Element, attr: str) -> bool:
    for child in el:
        if local(child.tag) in ANIM and child.get("attributeName") == attr:
            return True
    return False


def add_class(el: ET.Element, name: str) -> None:
    have = [c for c in (el.get("class") or "").split() if c and c != name]
    have.append(name)
    el.set("class", " ".join(have))


def text_of(el: ET.Element) -> str:
    return "".join(el.itertext()).strip()


def is_page_bg(el: ET.Element) -> bool:
    if local(el.tag) != "rect":
        return False
    try:
        w = float(el.get("width") or 0)
        h = float(el.get("height") or 0)
        y = float(el.get("y") or 0)
    except ValueError:
        return False
    return w >= 600 and h >= 200 and y <= 1


def map_paints(root: ET.Element, unknown: list[str]) -> None:
    for el in root.iter():
        tag = local(el.tag)
        if tag in ANIM or tag in {"style", "title", "desc"}:
            continue
        fill = norm(el.get("fill"))
        stroke = norm(el.get("stroke"))
        if tag == "text" or tag == "tspan":
            if fill in {"", "none", "transparent"}:
                pass
            elif fill in TEXT_FILL:
                add_class(el, TEXT_FILL[fill])
                if not animated(el, "fill"):
                    del el.attrib["fill"]
            elif fill.startswith("#"):
                # 没进色表的字，浅了就改成正文色，避免白底对比不够。
                add_class(el, "txt")
                if not animated(el, "fill"):
                    del el.attrib["fill"]
                if contrast(fill, "#ffffff") < 4.5:
                    unknown.append(f"text {fill}")
        elif fill in {"", "none", "transparent"}:
            pass
        elif fill in {"#fff", "#ffffff"} and is_page_bg(el):
            add_class(el, "bg")
            if not animated(el, "fill"):
                del el.attrib["fill"]
        elif fill in {"#fff", "#ffffff"}:
            add_class(el, "panel")
            if not animated(el, "fill"):
                del el.attrib["fill"]
            if stroke in GRAY_STROKE and not animated(el, "stroke"):
                el.attrib.pop("stroke", None)
                stroke = ""
        elif fill in SHAPE_FILL:
            # SMIL 改 fill 时，样式表里的 fill 会把动画压住。这种留下属性，不挂填色类。
            if not animated(el, "fill"):
                chosen = SHAPE_FILL[fill]
                if chosen == "fill-b" and has_white_text(el):
                    chosen = "fill-lockb"
                add_class(el, chosen)
                del el.attrib["fill"]
        elif fill.startswith("#"):
            unknown.append(f"shape {fill}")
        if stroke in STROKE:
            add_class(el, STROKE[stroke])
            if not animated(el, "stroke"):
                el.attrib.pop("stroke", None)
        elif stroke.startswith("#"):
            unknown.append(f"stroke {stroke}")
        if el.get("font-family") and "Segoe" in el.get("font-family", ""):
            del el.attrib["font-family"]
        bump_font_attr(el)


def has_white_text(el: ET.Element) -> bool:
    for child in el.iter():
        if local(child.tag) == "text" and norm(child.get("fill")) in {"#fff", "#ffffff"}:
            return True
    return False


def normalize_durs(root: ET.Element) -> None:
    anims = [el for el in root.iter() if local(el.tag) in ANIM and el.get("dur")]
    values = [parse_s(el.get("dur") or "") for el in anims]
    known = [v for v in values if v is not None]
    if not known:
        return
    primary = max(known)
    for el, dur in zip(anims, values, strict=True):
        if dur is None:
            continue
        if dur in (8.0, 12.0):
            continue
        if primary >= 8 and dur < 4:
            continue
        target = 12.0 if dur >= 10 else 8.0
        el.set("dur", fmt_s(target))
        begin = el.get("begin")
        if begin and dur:
            parts = []
            for piece in begin.split(";"):
                got = parse_s(piece)
                parts.append(fmt_s(got * target / dur) if got is not None else piece)
            el.set("begin", ";".join(parts))


def relocate_axis_titles(root: ET.Element) -> int:
    """横轴标题不要压在刻度上。

    同一点上的 end/middle 是旧底栏的写法。标题放在轴端、刻度在轴端左边时，
    end 锚点会向左伸进最后一个刻度，也要挪开。
    """
    texts: list[tuple[float, float, ET.Element]] = []
    for el in root.iter():
        if local(el.tag) != "text":
            continue
        try:
            texts.append((float(el.get("x") or 0), float(el.get("y") or 0), el))
        except ValueError:
            continue
    groups: dict[tuple[float, float], list[ET.Element]] = {}
    for x, y, el in texts:
        groups.setdefault((round(x, 1), round(y, 1)), []).append(el)
    moved = 0
    for (x, y), group in groups.items():
        if len(group) < 2:
            continue
        middles = [el for el in group if el.get("text-anchor") == "middle"]
        ends = [el for el in group if el.get("text-anchor") == "end"]
        if not middles or not ends:
            continue
        tick = text_of(middles[0])
        nx, ny = axis_title_xy(x, y, tick)
        for el in ends:
            el.set("x", f"{nx:.1f}")
            el.set("y", f"{ny:.1f}")
            el.set("text-anchor", "start")
            moved += 1
    middles = [
        (x, y, el)
        for x, y, el in texts
        if el.get("text-anchor") == "middle" and len(text_of(el)) <= 6
    ]
    for x, y, el in texts:
        if el.get("text-anchor") != "end":
            continue
        title = text_of(el)
        if len(title) < 2:
            continue
        same = [item for item in middles if abs(item[1] - y) < 1 and item[0] <= x + 1]
        if not same:
            continue
        tick_x, _tick_y, tick_el = max(same, key=lambda item: item[0])
        title_w = sum(12 if ord(ch) > 127 else 7 for ch in title)
        half = 0.55 * 12 * max(len(text_of(tick_el)), 1) / 2
        if x - title_w >= tick_x + half + 8:
            continue
        nx, ny = axis_title_xy(tick_x, y, text_of(tick_el))
        el.set("x", f"{nx:.1f}")
        el.set("y", f"{ny:.1f}")
        el.set("text-anchor", "start")
        moved += 1
    return moved


def text_px(text: str) -> float:
    return sum(16 if ord(ch) > 127 else 9 for ch in text)


def short_title(text: str) -> str:
    text = " ".join(text.split())
    if text_px(text) <= 740:
        return text
    for sep in ("：", ":"):
        if sep in text and text_px(text[: text.index(sep)]) <= 740:
            return text[: text.index(sep)]
    cut = text
    while cut and text_px(cut) > 740:
        cut = cut[:-1]
    return cut


def clip(text: str, limit: int = 42) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in ("。", "；", "，", "、"):
        idx = cut.rfind(sep)
        if idx >= 12:
            return cut[: idx + 1]
    return cut


def pick_steps(name: str, texts: list[str], title: str) -> list[str]:
    if name in CURATED:
        return CURATED[name]
    picked: list[str] = []
    for raw in texts:
        line = " ".join(raw.split())
        if len(line) < 8 or line == title:
            continue
        if line in picked:
            continue
        picked.append(clip(line))
        if len(picked) == 3:
            break
    while len(picked) < 3:
        picked.append("数字是示意，不是某一颗电芯或某一台板的实测。")
    picked.append("循环里亮着的那一步对应当前画面。数字标示意。")
    return picked[:4]


def make(tag: str, **attrs: str) -> ET.Element:
    el = ET.Element(q(tag))
    for key, value in attrs.items():
        el.set(key, value)
    return el


def step_nodes(steps: list[str], width: float, primer: bool) -> list[ET.Element]:
    panel_cls = "panel"
    title_cls = "title"
    out = [
        make(
            "rect",
            **{
                "class": panel_cls,
                "x": "24",
                "y": "-112",
                "width": f"{width - 48:.0f}",
                "height": "100",
                "rx": "6",
            },
        )
    ]
    ys = ("-88", "-66", "-44", "-22")
    marks = "①②③④"
    for i, (line, y) in enumerate(zip(steps, ys, strict=True)):
        node = make("text", **{"class": "txt", "x": "40", "y": y, "opacity": "1" if i == 0 else "0.28"})
        node.text = f"{marks[i]} {line}"
        anim = make(
            "animate",
            attributeName="opacity",
            values=STEP_OP[i],
            keyTimes=STEP_KT,
            dur="12s",
            repeatCount="indefinite",
        )
        node.append(anim)
        out.append(node)
    del title_cls, primer
    return out


def visible_texts(root: ET.Element) -> list[str]:
    out = []
    for el in root.iter():
        if local(el.tag) != "text":
            continue
        got = text_of(el)
        if got and got not in out:
            out.append(got)
    return out


def drop_top_heading(root: ET.Element) -> str:
    """页眉会放标题。原来贴在顶上的大标题拿掉，避免同一句出现两次。"""
    found = ""
    for el in list(root.iter()):
        if local(el.tag) != "text":
            continue
        try:
            y = float(el.get("y") or 99)
            size = float((el.get("font-size") or "0").replace("px", ""))
        except ValueError:
            continue
        bold = el.get("font-weight") == "bold" or "title" in (el.get("class") or "")
        if y < 50 and (size >= 16 or bold) and len(text_of(el)) > 6:
            found = text_of(el)
            # 页眉一行放得下才挪走。放不下就留在原处，避免把句子截断。
            if text_px(found) <= 740:
                parent = parent_of(root, el)
                if parent is not None:
                    parent.remove(el)
            else:
                found = ""
            break
    return found


def parent_of(root: ET.Element, node: ET.Element) -> ET.Element | None:
    for parent in root.iter():
        for child in list(parent):
            if child is node:
                return parent
    return None


def ensure_desc(root: ET.Element, sentence: str) -> None:
    desc = next((el for el in root if local(el.tag) == "desc"), None)
    if desc is None:
        desc = ET.Element(q("desc"))
        desc.text = sentence
        title = next((el for el in root if local(el.tag) == "title"), None)
        if title is not None:
            idx = list(root).index(title)
            root.insert(idx + 1, desc)
        else:
            root.insert(0, desc)
        return
    body = " ".join((desc.text or "").split())
    if "示意" not in body:
        desc.text = body.rstrip("。") + "。示意。"


def replace_styles(root: ET.Element) -> None:
    for child in list(root):
        if local(child.tag) == "style":
            root.remove(child)
    style = ET.Element(q("style"))
    style.text = STYLE
    title = next((el for el in root if local(el.tag) == "title"), None)
    desc = next((el for el in root if local(el.tag) == "desc"), None)
    anchor = desc if desc is not None else title
    if anchor is not None:
        root.insert(list(root).index(anchor) + 1, style)
    else:
        root.insert(0, style)


def insert_chrome(root: ET.Element, nodes: list[ET.Element]) -> None:
    meta = {"title", "desc", "style"}
    head = [el for el in list(root) if local(el.tag) in meta]
    tail = [el for el in list(root) if local(el.tag) not in meta]
    for el in list(root):
        root.remove(el)
    for el in head + nodes + tail:
        root.append(el)


def reading_line(texts: list[str]) -> str:
    numbered = [t for t in texts if any(ch.isdigit() for ch in t) and len(t) > 8]
    src = numbered[-1] if numbered else (texts[-1] if texts else "数字是示意")
    line = clip(src, 54)
    if "示意" not in line:
        line = clip(line.rstrip("。") + "。示意。", 54)
    return line


def shift_group(group: ET.Element, dy: float) -> None:
    for el in group.iter():
        if local(el.tag) == "text" and el.get("y"):
            el.set("y", f"{float(el.get('y')) + dy:.1f}")
        if local(el.tag) == "rect" and el.get("y"):
            el.set("y", f"{float(el.get('y')) + dy:.1f}")


def hook_li_ion(root: ET.Element) -> None:
    for el in root.iter():
        if local(el.tag) != "animate":
            continue
        kt = el.get("keyTimes") or ""
        if kt == "0;0.02;0.48;0.5;1":
            el.set("values", "1;1;0;0")
            el.set("keyTimes", "0;0.49;0.5;1")
        elif kt == "0;0.5;0.52;1":
            el.set("keyTimes", "0;0.49;0.5;1")
    for el in root.iter():
        if local(el.tag) == "text" and text_of(el) == "电解液":
            el.set("x", "270")


def hook_roadmap(root: ET.Element) -> None:
    for el in root.iter():
        if local(el.tag) == "circle" and el.get("r") == "16":
            el.set("class", "fill-lockb stroke-b")
            el.attrib.pop("fill", None)
            el.attrib.pop("stroke", None)
        if local(el.tag) == "text" and text_of(el) in list("0123456"):
            el.set("class", "on")
            el.attrib.pop("fill", None)
        if local(el.tag) == "animatemotion" and el.get("path") and "185" in el.get("path", ""):
            el.set("path", el.get("path", "").replace("185", "156"))


def hook_cc_cv(root: ET.Element) -> None:
    for el in root.iter():
        if local(el.tag) != "g":
            continue
        if any(text_of(child) == "恒压 CV 段" or "恒压 CV 段" in text_of(child) for child in el.iter()):
            shift_group(el, -50)
            return


def hook_cell_reversal(root: ET.Element) -> None:
    for el in root.iter():
        if local(el.tag) == "path" and el.get("d") and "H 440" in el.get("d", ""):
            el.set("d", "M 90 248 H 440")
        if local(el.tag) == "rect" and el.get("class") == "panel" and el.get("height") == "250":
            el.set("height", "286")
        if local(el.tag) == "text" and text_of(el) in {"正常", "最弱·已反极"}:
            el.set("y", "278")
        if local(el.tag) == "text" and "放电电流继续" in text_of(el):
            el.set("y", "308")
        if local(el.tag) == "text" and "木桶效应" in text_of(el):
            el.set("y", "368")


def hook_mqtt(root: ET.Element) -> None:
    for el in root.iter():
        if local(el.tag) != "text":
            continue
        if text_of(el) == "Broker":
            el.set("y", "108")
        if "按主题转发" in text_of(el):
            el.set("y", "136")


def hook_hil(root: ET.Element) -> None:
    for el in root.iter():
        if local(el.tag) != "style":
            continue
        body = el.text or ""
        if ".dpanel" not in body and ".sig" not in body:
            continue
        body = body.replace("fill: #ff7b00;", "fill: #bf8700;")
        if ".dpanel" in body:
            el.text = """
    .dpanel { fill: #f4f6f8; stroke: #d0d7de; }
    .dtitle { fill: #1f2328; font-size: 13px; }
    .dsmall { fill: #57606a; font-size: 12px; }
    .dnote { fill: #1f2328; font-size: 12px; }
    .daxis { stroke: #57606a; stroke-width: 1.5; fill: none; }
    .dblue { stroke: #0969da; stroke-width: 2.5; fill: none; }
    .dred { stroke: #cf222e; stroke-width: 2.5; fill: none; }
    .dgreen { stroke: #1a7f37; stroke-width: 2.2; fill: none; }
    .ddot { fill: #bf8700; }
    @media (prefers-color-scheme: dark) {
      .dpanel { fill: #161b22; stroke: #30363d; }
      .dtitle { fill: #e6edf3; }
      .dsmall { fill: #8b949e; }
      .dnote { fill: #e6edf3; }
      .daxis { stroke: #8b949e; }
      .dblue { stroke: #4493f8; }
      .dred { stroke: #ff7b72; }
      .dgreen { stroke: #3fb950; }
      .ddot { fill: #d29922; }
    }
"""
        else:
            el.text = body
            if ".sig { fill: #d29922; }" not in body:
                el.text = body.replace(
                    ".led { fill: #ff7b72; }",
                    ".led { fill: #ff7b72; }\n      .sig { fill: #d29922; }",
                )
    victim = None
    for el in list(root.iter()):
        if local(el.tag) == "rect" and el.get("y") == "172" and el.get("height") == "14":
            parent = parent_of(root, el)
            if parent is not None:
                parent.remove(el)
        if local(el.tag) == "text" and "CH7" in text_of(el):
            victim = el
        if local(el.tag) == "animatemotion" and el.get("path", "").startswith("M 220 135"):
            el.set("path", "M 220 135 L 258 135")
    if victim is not None and not any(local(c.tag) == "animate" for c in victim):
        victim.append(
            make(
                "animate",
                attributeName="opacity",
                values="1;0.35;1",
                dur="8s",
                repeatCount="indefinite",
            )
        )
def put_tick(root: ET.Element, x: float, y: float, text: str, anchor: str) -> None:
    node = make(
        "text",
        **{"class": "small", "x": f"{x:.1f}", "y": f"{y:.1f}", "text-anchor": anchor},
    )
    node.text = text
    root.append(node)


def hook_discharge(root: ET.Element) -> None:
    """两条 RC 衰减原来没有刻度。时间轴按 τ 反推：左 150 s，右 0.9 s。电压 0 / 200 / 400。"""
    for el in root.iter():
        if local(el.tag) == "text" and text_of(el).startswith("到 60 V"):
            el.set("y", "274")
    # 左：x = 70 + t/150*260，y = 80 + (1 - V/400)*150
    for t in (0, 50, 100, 150):
        x = 70 + t / 150 * 260
        root.append(make("line", **{"class": "grid", "x1": f"{x:.1f}", "y1": "230", "x2": f"{x:.1f}", "y2": "236"}))
        put_tick(root, x, 250, str(t), "middle")
    tx, ty = axis_title_xy(70 + 260, 250, "150")
    put_tick(root, tx, ty, "s", "start")
    for volt in (0, 200, 400):
        y = 80 + (1 - volt / 400) * 150
        root.append(make("line", **{"class": "grid", "x1": "64", "y1": f"{y:.1f}", "x2": "70", "y2": f"{y:.1f}"}))
        put_tick(root, 60, y + 4, str(volt), "end")
    # 右：末端约 0.9 s（400·e^(-t/0.2) 落到曲线终点）
    for t, label in ((0, "0"), (0.3, "0.3"), (0.6, "0.6"), (0.9, "0.9")):
        x = 450 + t / 0.9 * 280
        root.append(make("line", **{"class": "grid", "x1": f"{x:.1f}", "y1": "230", "x2": f"{x:.1f}", "y2": "236"}))
        put_tick(root, x, 250, label, "middle")
    tx, ty = axis_title_xy(450 + 280, 250, "0.9")
    put_tick(root, tx, ty, "s", "start")
    for volt in (0, 200, 400):
        y = 80 + (1 - volt / 400) * 150
        root.append(make("line", **{"class": "grid", "x1": "444", "y1": f"{y:.1f}", "x2": "450", "y2": f"{y:.1f}"}))
        put_tick(root, 440, y + 4, str(volt), "end")


def hook_precharge(root: ET.Element) -> None:
    """已有 0、0.6 s、400 V。补中间刻度。400 V 在约 95% 虚线上方，按同一条直线。"""
    # 0 V 在 y=250，380 V（约 95%）在 y=79。
    y = 250 - (250 - 79) * (200 / 380)
    root.append(make("line", **{"class": "grid", "x1": "74", "y1": f"{y:.1f}", "x2": "80", "y2": f"{y:.1f}"}))
    put_tick(root, 70, y + 4, "200", "end")
    x = 80 + (500 - 80) * 0.5
    root.append(make("line", **{"class": "grid", "x1": f"{x:.1f}", "y1": "250", "x2": f"{x:.1f}", "y2": "256"}))
    put_tick(root, x, 268, "0.3", "middle")


def hook_protection(root: ET.Element) -> None:
    """阈值 4.25 V、恢复 4.15 V 补到纵轴左侧，当作刻度。"""
    put_tick(root, 74, 144, "4.25", "end")
    put_tick(root, 74, 184, "4.15", "end")
    root.append(make("line", **{"class": "grid", "x1": "80", "y1": "140", "x2": "86", "y2": "140"}))
    root.append(make("line", **{"class": "grid", "x1": "80", "y1": "180", "x2": "86", "y2": "180"}))


def hook_mux(root: ET.Element, orig_h: float) -> None:
    """底栏补一条 I = 50 A × (t / 1.6 ms)。末尾 1 mΩ×50 A = 50 mV。"""
    y0 = orig_h + 8
    x0, x1 = 108.0, 460.0
    axis_y = y0 + 132
    top = y0 + 28

    def x_of(t: float) -> float:
        return x0 + (x1 - x0) * (t / 1.6)

    def y_of(amp: float) -> float:
        return axis_y - (axis_y - top) * (amp / 50.0)

    panel = make(
        "rect",
        **{"class": "panel", "x": "24", "y": f"{y0:.0f}", "width": "752", "height": "164", "rx": "6"},
    )
    caption = make("text", **{"class": "txt", "x": "40", "y": f"{y0 + 16:.0f}"})
    caption.text = "底栏：扫描这一圈电流从 0 涨到 50 A。ΔV = I × 1 mΩ。示意。"
    y_label = make("text", **{"class": "small", "x": "120", "y": f"{top + 16:.0f}"})
    y_label.text = "电流 A"
    nodes = [panel, caption, y_label]
    nodes.append(make("line", **{"class": "axis", "x1": f"{x0:.1f}", "y1": f"{top:.1f}", "x2": f"{x0:.1f}", "y2": f"{axis_y:.1f}"}))
    nodes.append(make("line", **{"class": "axis", "x1": f"{x0:.1f}", "y1": f"{axis_y:.1f}", "x2": f"{x1:.1f}", "y2": f"{axis_y:.1f}"}))
    for t, label in ((0, "0"), (0.8, "0.8"), (1.6, "1.6")):
        x = x_of(t)
        nodes.append(make("line", **{"class": "grid", "x1": f"{x:.1f}", "y1": f"{axis_y:.1f}", "x2": f"{x:.1f}", "y2": f"{axis_y + 6:.1f}"}))
        tick = make("text", **{"class": "small", "x": f"{x:.1f}", "y": f"{axis_y + 22:.1f}", "text-anchor": "middle"})
        tick.text = label
        nodes.append(tick)
    for amp in (0, 25, 50):
        y = y_of(amp)
        nodes.append(make("line", **{"class": "grid", "x1": f"{x0 - 6:.1f}", "y1": f"{y:.1f}", "x2": f"{x0:.1f}", "y2": f"{y:.1f}"}))
        tick = make("text", **{"class": "small", "x": f"{x0 - 10:.1f}", "y": f"{y + 4:.1f}", "text-anchor": "end"})
        tick.text = str(amp)
        nodes.append(tick)
    pts = []
    for i in range(17):
        t = 1.6 * i / 16
        pts.append(f"{x_of(t):.1f},{y_of(50 * t / 1.6):.1f}")
    nodes.append(make("polyline", **{"class": "lineb", "points": " ".join(pts)}))
    dot = make("circle", **{"class": "fill-y", "r": "5"})
    xs = ";".join(f"{x_of(1.6 * i / 8):.1f}" for i in range(9))
    ys = ";".join(f"{y_of(50 * i / 8):.1f}" for i in range(9))
    kts = ";".join(f"{i / 8:.4f}" for i in range(9))
    dot.append(make("animate", attributeName="cx", values=xs, keyTimes=kts, dur="8s", repeatCount="indefinite"))
    dot.append(make("animate", attributeName="cy", values=ys, keyTimes=kts, dur="8s", repeatCount="indefinite"))
    nodes.append(dot)
    tx, ty = axis_title_xy(x_of(1.6), axis_y + 22, "1.6")
    xlabel = make("text", **{"class": "small", "x": f"{tx:.1f}", "y": f"{ty:.1f}", "text-anchor": "start"})
    xlabel.text = "时间 ms"
    nodes.append(xlabel)
    note = make("text", **{"class": "small", "x": "480", "y": f"{top + 36:.1f}"})
    note.text = "1.6 ms 末：50 A × 1 mΩ = 50 mV"
    nodes.append(note)
    for node in nodes:
        root.append(node)


HOOKS = {
    "li-ion-working.svg": lambda root, _h: hook_li_ion(root),
    "bms-roadmap.svg": lambda root, _h: hook_roadmap(root),
    "cc-cv.svg": lambda root, _h: hook_cc_cv(root),
    "cell-reversal.svg": lambda root, _h: hook_cell_reversal(root),
    "mqtt-pubsub-will.svg": lambda root, _h: hook_mqtt(root),
    "hil-testbench.svg": lambda root, _h: hook_hil(root),
    "mux-time-skew.svg": lambda root, h: hook_mux(root, h),
    "discharge-energy-time.svg": lambda root, _h: hook_discharge(root),
    "precharge-rc-example.svg": lambda root, _h: hook_precharge(root),
    "protection-debounce.svg": lambda root, _h: hook_protection(root),
}


def view_box(root: ET.Element) -> tuple[float, float, float, float]:
    parts = (root.get("viewBox") or "0 0 800 400").split()
    return tuple(float(p) for p in parts[:4])  # type: ignore[return-value]


def process(path: Path, legacy: bool) -> list[str]:
    unknown: list[str] = []
    raw = path.read_text(encoding="utf-8")
    has_bottom = "底栏" in raw
    root = ET.parse(path).getroot()
    _minx, _miny, width, height = view_box(root)
    texts_before = visible_texts(root)
    title_el = next((el for el in root if local(el.tag) == "title"), None)
    title = " ".join((title_el.text or "").split()) if title_el is not None else path.stem
    if "示意" in title:
        desc = title
    else:
        desc = title.rstrip("。") + "。示意。"
    root.set("role", "img")
    root.set("font-family", "ui-monospace, Consolas, monospace")
    ensure_desc(root, desc)
    if legacy:
        retint_styles(root)
        map_paints(root, unknown)
    else:
        for el in root.iter():
            bump_font_attr(el)
            if local(el.tag) == "style":
                bump_font_css(el)
        if path.name == "mqtt-pubsub-will.svg":
            style = next(el for el in root if local(el.tag) == "style")
            extra = (
                "\n    .panel { fill: #f4f6f8; stroke: #d0d7de; }\n"
                "    @media (prefers-color-scheme: dark) {\n"
                "      .panel { fill: #161b22; stroke: #30363d; }\n"
                "    }\n"
            )
            if ".panel" not in (style.text or ""):
                style.text = (style.text or "") + extra
    normalize_durs(root)
    relocate_axis_titles(root)
    heading = drop_top_heading(root)
    footer_h = 0 if has_bottom or path.name == "mux-time-skew.svg" else 64
    if path.name == "mux-time-skew.svg":
        footer_h = 180
    root.set("viewBox", f"0 {-HEADER:.0f} {width:.0f} {height + HEADER + footer_h:.0f}")
    if (root.get("height") or "").replace(".", "", 1).isdigit():
        root.set("height", f"{float(root.get('height') or 0) + HEADER + footer_h:.0f}")
    if (root.get("width") or "").replace(".", "", 1).isdigit():
        root.set("width", f"{width:.0f}")
    chrome = [
        make(
            "rect",
            **{
                "class": "bg",
                "x": "0",
                "y": f"{-HEADER}",
                "width": f"{width:.0f}",
                "height": f"{height + HEADER + footer_h:.0f}",
            },
        )
    ]
    head = make("text", **{"class": "title", "x": "24", "y": "-128"})
    head.text = short_title(heading or title)
    chrome.append(head)
    if "①" not in raw:
        chrome.extend(step_nodes(pick_steps(path.name, texts_before, title), width, not legacy))
    if footer_h == 64:
        bar_y = height + 8
        chrome.append(
            make(
                "rect",
                **{
                    "class": "panel",
                    "x": "24",
                    "y": f"{bar_y:.0f}",
                    "width": f"{width - 48:.0f}",
                    "height": "44",
                    "rx": "6",
                },
            )
        )
        note = make("text", **{"class": "small", "x": "40", "y": f"{bar_y + 28:.0f}"})
        note.text = reading_line(texts_before)
        chrome.append(note)
    insert_chrome(root, chrome)
    hook = HOOKS.get(path.name)
    if hook:
        hook(root, height)
    relocate_axis_titles(root)
    ensure_text_paint(root)
    nudge_known(root, path.name)
    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=False)
    return unknown


PAINT_CLASS = {"txt", "small", "title", "hi", "warn", "ok", "gold", "on"}


def ensure_text_paint(root: ET.Element) -> None:
    """文字没有自己的填色类时，会继承父级的灰块颜色，浅色底上会看不见。"""
    for el in root.iter():
        if local(el.tag) not in {"text", "tspan"}:
            continue
        if animated(el, "fill"):
            continue
        have = set((el.get("class") or "").split())
        if have & PAINT_CLASS:
            continue
        add_class(el, "small")


def nudge_known(root: ET.Element, name: str) -> None:
    if name == "series-parallel-pack.svg":
        for el in root.iter():
            if local(el.tag) == "text" and "与并联数" in text_of(el):
                el.set("x", "548")
            if local(el.tag) == "text" and "从一颗开始" in text_of(el):
                el.set("y", "272")
    if name == "mux-time-skew.svg":
        for el in root.iter():
            if local(el.tag) != "text":
                continue
            body = text_of(el)
            if body.startswith("底栏：扫描这一圈"):
                el.set("y", "484")
            elif body == "电流 A":
                el.set("x", "120")
                el.set("y", "512")


def update_baseline(migrated: set[str]) -> None:
    lines = BASELINE.read_text(encoding="utf-8").splitlines()
    kept = []
    for line in lines:
        body = line.split("#", 1)[0].strip()
        if not body:
            kept.append(line)
            continue
        name = body.split()[0]
        if name in migrated:
            continue
        kept.append(line)
    note = [
        "# SVG 画风豁免清单",
        "#",
        "# 第 2 批已经换皮的图从本清单删掉，必须自己通过画风检查。",
        "# 剩下的是第 3 批要重画的 G 类偏浅图（只有框和标签，还没补内容）。",
        "# 每行：文件名 检查项",
        "# 检查项：undefined-class | inline-paint | small-font | missing-desc | missing-role",
        "",
    ]
    body = [line for line in kept if line.strip() and not line.startswith("#")]
    BASELINE.write_text("\n".join(note + body) + "\n", encoding="utf-8")


def polish_file(path: Path) -> None:
    root = ET.parse(path).getroot()
    relocate_axis_titles(root)
    ensure_text_paint(root)
    nudge_known(root, path.name)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=False)


def main() -> None:
    if "--polish" in sys.argv:
        names = [a for a in sys.argv[1:] if a != "--polish"]
        paths = [ASSETS / name for name in names] if names else sorted(ASSETS.glob("*.svg"))
        for path in paths:
            if path.name in LEAVE or not path.exists():
                continue
            polish_file(path)
            print(f"polish {path.name}")
        return
    only = set(sys.argv[1:])
    migrated: list[str] = []
    for path in sorted(ASSETS.glob("*.svg")):
        if path.name in LEAVE:
            continue
        if only and path.name not in only:
            continue
        raw = path.read_text(encoding="utf-8")
        legacy = "#0f172a" in raw or "Segoe UI" in raw
        if not legacy and path.name not in PRIMER:
            continue
        if not legacy and "①" in raw and path.name not in only:
            continue
        unknown = process(path, legacy)
        migrated.append(path.name)
        extra = f" unknown={sorted(set(unknown))}" if unknown else ""
        print(f"ok {path.name}{extra}")
    if not only:
        update_baseline(set(migrated))
        print(f"migrated {len(migrated)}")


if __name__ == "__main__":
    main()
