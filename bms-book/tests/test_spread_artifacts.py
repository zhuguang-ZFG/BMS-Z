"""传播物（docs/public/spread）的发布合同。

这些文件是站点上的公开链接目标：一页纸要**离线可读**（字体已内置、打开时
不去连 fonts.googleapis.com），32 张章内结论卡与第 7 章三件套要真的在。

判据都落在读者能感知的地方：断网打开、点开链接。构建脚本重排顺序或换模板时，
这些断言先红。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPREAD = ROOT / "docs" / "public" / "spread"
SPREAD_TOOLS = ROOT / "tools" / "spread"

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


def test_build_guard_rejects_online_font_fallback() -> None:
    """render.mjs 的 --embed 会静默回退成在线字体；build.py 必须把这种产物判红。"""
    sys.path.insert(0, str(SPREAD_TOOLS))
    import build as spread_build

    leaked = (
        '<link rel="stylesheet" data-gz-fonts="noto-serif-sc" '
        'href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC&display=swap">'
    )
    with pytest.raises(SystemExit):
        spread_build.assert_offline_fonts(leaked, "07-protection-tick")

    inlined = (
        '<link rel="stylesheet" data-gz-fonts="noto-serif-sc" href="data:text/css,">'
        '<style data-gz-embedded>@font-face{font-family:"Noto Serif SC"}</style>'
    )
    spread_build.assert_offline_fonts(inlined, "07-protection-tick")
    # 字体切换器按钮上的 data-href 是「点了才取」，不属于加载期依赖
    switcher = '<button data-href="https://fonts.googleapis.com/css2?family=Inter"></button>'
    spread_build.assert_offline_fonts(switcher, "07-protection-tick")


def _card_fixture(tmp_path, monkeypatch):
    sys.path.insert(0, str(SPREAD_TOOLS))
    import build_cards

    src = tmp_path / "cards" / "demo"
    src.mkdir(parents=True)
    (src / "posters.html").write_text('<section class="poster xhs">x</section>', encoding="utf-8")
    (src / "card.json").write_text('{"theme": "ink-classic"}', encoding="utf-8")

    skill = tmp_path / "skill"
    (skill / "assets").mkdir(parents=True)
    (skill / "assets" / "template-editorial-card.html").write_text(
        "<html><head></head><body><main><!-- POSTERS_HERE --></main></body></html>",
        encoding="utf-8",
    )
    (skill / "scripts").mkdir()
    (tmp_path / "repo").mkdir()

    monkeypatch.setattr(build_cards, "SRC_ROOT", tmp_path / "cards")
    monkeypatch.setattr(build_cards, "OUT_ROOT", tmp_path / "published")
    monkeypatch.setattr(build_cards, "ROOT", tmp_path / "repo")
    monkeypatch.setattr(build_cards, "SKILL_DIR", skill)
    return build_cards, tmp_path / "published"


def _fake_renderer(validator_error: bool):
    def run(cmd, cwd=None, check=False):
        if "render.mjs" in cmd[1]:
            out = Path(cmd[2]) / "output"
            out.mkdir(parents=True, exist_ok=True)
            (out / "xhs-01.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 32)
            return None
        if validator_error:
            raise subprocess.CalledProcessError(1, cmd)
        return None

    return run


def test_failed_validation_never_overwrites_published_cards(tmp_path, monkeypatch) -> None:
    build_cards, published = _card_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(build_cards.subprocess, "run", _fake_renderer(validator_error=True))

    with pytest.raises(subprocess.CalledProcessError):
        build_cards.build("demo", validate=True)

    assert not published.exists(), "校验失败后仍然覆盖了已发布的 PNG"


def test_passing_validation_publishes_cards(tmp_path, monkeypatch) -> None:
    """对照组：同一条路径在校验通过时必须真的拷出 PNG，否则上面的断言没有意义。"""
    build_cards, published = _card_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(build_cards.subprocess, "run", _fake_renderer(validator_error=False))

    build_cards.build("demo", validate=True)

    assert (published / "demo" / "xhs-01.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
