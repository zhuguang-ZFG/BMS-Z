"""prose 预筛：两卷正文的客观文字问题扫描（诊断工具，非门禁）。

规则：
- 重复词：的的/了了/是是/在在/与与/和和/或或（排除合理叠用如"想想"）
- 高频错别字对（的/地/得、做/作、帐/账、象/像、其它/其他 在术语表外的用法）
- 半角标点混入中文（, ; ! ? ( ) 在 CJK 之间）
- 一逗到底：单句 >60 字无句号
- 英文残留：连续 ASCII 字母序列夹在中文段落里（排除代码块/行内码/术语白名单）
- 口语残留黑名单：说白了、咱们、啥的、玩意儿、搞懂、搞明白（书风允许的除外，列出人工判）

跳过：代码块、行内代码、HTML 标签内、链接 URL、图片行、公式块。

用法：python tools/prose_prescreen.py [--md PATH ...]（默认两卷全部 md）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V1 = ROOT / "analog/docs"
V2 = ROOT / "bms-book/book"

CJK = r"[一-鿿]"

DUP_WORDS = ["的的", "了了", "是是", "在在", "与与", "和和", "或或", "很很", "最最", "都都", "对对"]

HALF_PUNCT = re.compile(CJK + r"[,;!?()]|[,;!?()]" + CJK)

COLLOQUIAL = ["说白了", "咱们", "啥的", "玩意儿", "搞懂", "搞明白", "整明白", "唠", "啥是"]

# 合理英文残留白名单（常见术语/单位/协议）
EN_WHITELIST = re.compile(
    r"^(BMS|AFE|MCU|SOC|SOH|SOP|DOD|OCV|CV|CC|CAN|I2C|SPI|UART|PWM|MOS|NTC|EMC|ESD|ISO|IEC|GB|UL|AEC|"
    r"e\.g\.|i\.e\.|vs\.|etc\.|Fig\.|Eq\.|Ch\.|Appendix|LiFePO4|NMC|LFP|NCA|LCO|LMO|"
    r"SPICE|ngspice|LTspice|Python|JavaScript|HTML|CSS|EPUB|PDF|SVG|API|CLI|GUI|"
    r"GitHub|VitePress|Playwright|Markdown|YAML|JSON|XML|MQTT|OTA|JTAG|SWD|"
    r"SOC|SOCv|AFE|ADC|DAC|GPIO|CRC|ECC|RAM|ROM|Flash|EEPROM|"
    r"[0-9]+[munkMG]?[AVsHzWbKΩ]|V|A|Ω|℃|mV|mA|mΩ|kΩ|MΩ|μF|nF|pF|mH|μH|kHz|MHz|GHz)$"
)
EN_SEQ = re.compile(r"[A-Za-z][A-Za-z0-9+./-]{1,}")


def strip_nonprose(text: str) -> list[tuple[int, str]]:
    """返回 (行号, 纯散文行)：去掉代码块/行内码/HTML 标签/公式。"""
    out = []
    in_code = False
    in_math = False
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if s.startswith("$$"):
            in_math = not in_math
            continue
        if in_math or "$$" in s:
            continue
        # 去行内码与标签
        s = re.sub(r"`[^`]*`", "", s)
        s = re.sub(r"<[^>]+>", "", s)
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
        if s:
            out.append((i, s))
    return out


def scan_file(path: Path) -> list[str]:
    issues = []
    text = path.read_text(encoding="utf-8")
    lines = strip_nonprose(text)
    for ln, s in lines:
        for w in DUP_WORDS:
            if w in s:
                issues.append(f"{path.name}:{ln} 重复词「{w}」: {s[:60]}")
        m = HALF_PUNCT.search(s)
        if m:
            issues.append(f"{path.name}:{ln} 半角标点「{m.group(0)}」: {s[:60]}")
        for w in COLLOQUIAL:
            if w in s:
                issues.append(f"{path.name}:{ln} 口语「{w}」: {s[:60]}")
        # 一逗到底：>60 字无句号
        if "，" in s and "。" not in s and len(s) > 60:
            issues.append(f"{path.name}:{ln} 长句 {len(s)} 字无句号: {s[:50]}…")
        # 英文残留
        for em in EN_SEQ.finditer(s):
            w = em.group(0)
            if EN_WHITELIST.match(w):
                continue
            # 中文紧邻的英文序列才算残留
            start, end = em.span()
            if start > 0 and re.match(CJK, s[start - 1]) or end < len(s) and re.match(CJK, s[end]):
                issues.append(f"{path.name}:{ln} 英文残留「{w}」: {s[:60]}")
    return issues


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    targets = [Path(a) for a in args] if args else sorted(V1.glob("*.md")) + sorted(V2.glob("*.md"))
    total = 0
    per_file: dict[str, int] = {}
    for p in targets:
        if not p.is_file():
            continue
        issues = scan_file(p)
        per_file[p.name] = len(issues)
        total += len(issues)
        for it in issues:
            print(it)
    print(f"\n== 合计 {total} 处 ==")
    for name, n in sorted(per_file.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  {name}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
