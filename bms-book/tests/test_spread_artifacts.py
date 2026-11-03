"""传播物（docs/public/spread）的发布合同。

这些文件是站点上的公开链接目标：一页纸要**离线可读**（字体已内置、打开时
不去连 fonts.googleapis.com），32 张章内结论卡与第 7 章三件套要真的在。

判据都落在读者能感知的地方：断网打开、点开链接。构建脚本重排顺序或换模板时，
这些断言先红。
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPREAD = ROOT / "docs" / "public" / "spread"

LOAD_TIME_REMOTE = re.compile(
    r'<(?:link\b[^>]*\brel="stylesheet"[^>]*\bhref|script\b[^>]*\bsrc|img\b[^>]*\bsrc|iframe\b[^>]*\bsrc)'
    r'="(https?://[^"]+)"'
)
PRECONNECT_RE = re.compile(r'<link\b[^>]*\brel="preconnect"[^>]*\bhref="https?://fonts\.')


def test_one_pager_reads_offline() -> None:
    html = (SPREAD / "07-protection-tick.html").read_text(encoding="utf-8")

    assert "data-gz-embedded" in html, "字体没有内置：断网打开会退回系统字体"
    assert not PRECONNECT_RE.search(html), "还留着 fonts.g* 的 preconnect，打开时仍会外连"
    remote = LOAD_TIME_REMOTE.findall(html)
    assert remote == [], f"页面加载期仍会请求远端资源：{remote}"


def test_one_pager_ships_all_three_formats() -> None:
    for name in ("07-protection-tick.html", "07-protection-tick.pdf", "07-protection-tick.png"):
        path = SPREAD / name
        assert path.is_file(), f"缺产物：{name}"
        assert path.stat().st_size > 100_000, f"{name} 只有 {path.stat().st_size} 字节，像是空壳"


def test_chapter_cards_cover_all_thirty_two_chapters() -> None:
    cards = sorted((SPREAD / "cards" / "chapters").glob("xhs-*.png"))
    assert [p.name for p in cards] == [f"xhs-{n:02d}.png" for n in range(1, 33)]
    for card in cards:
        assert card.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", f"{card.name} 不是 PNG"


def test_chapter_seven_kit_is_published() -> None:
    cards = sorted((SPREAD / "cards" / "07-protection-tick").glob("xhs-*.png"))
    assert len(cards) == 5, f"第 7 章卡组应为 5 张，实际 {len(cards)}"
    deck = SPREAD / "deck" / "07-protection-tick.html"
    assert deck.is_file()
    assert "SPEAKER_NOTES" in deck.read_text(encoding="utf-8")
