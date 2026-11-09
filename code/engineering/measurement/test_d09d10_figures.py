"""Structural checks for D09 and D10 figures."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def load(sub: str, name: str) -> tuple[ET.Element, str]:
    path = HERE.parents[2] / "bms-book" / "engineering" / "assets" / sub / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d09d10_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


@pytest.mark.parametrize(
    "sub,name",
    [
        ("d09-safety", "D09-F1-common-supply.svg"),
        ("d09-safety", "D09-F2-matrix-fmea.svg"),
        ("d10-balance", "D10-F1-bleed-window.svg"),
        ("d10-balance", "D10-F2-three-diffs.svg"),
    ],
)
def test_svg_is_wellformed_with_identity(sub, name):
    root, text = load(sub, name)
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None
    assert 'class="bg"' in text and 'class="title"' in text


def test_f9_1_common_supply_kills_backup():
    _root, text = load("d09-safety", "D09-F1-common-supply.svg")
    assert "共用 DC/DC 供电轨" in text
    assert "备份概率 0" in text
    assert "供电 / 基准源 / 传感链 / 时钟" in text


def test_f9_2_matrix_and_fmea_gap_row():
    _root, text = load("d09-safety", "D09-F2-matrix-fmea.svg")
    assert "完整独立保护" in text and "共因双杀" in text
    assert "共因缺口明示" in text, "FMEA 摘要必须含缺口行"
    assert "覆盖低" in text and "覆盖高" in text and "不隔离" in text and "隔离" in text


def test_f10_1_bleed_three_accounts_and_duty():
    _root, text = load("d10-balance", "D10-F1-bleed-window.svg")
    assert "35 mA" in text and "0.122 W" in text and "85.7 min" in text
    assert "50%" in text and "样本无效" in text


def test_f10_2_three_differences_rows():
    _root, text = load("d10-balance", "D10-F2-three-diffs.svg")
    for token in ("电压差", "SOC 差", "容量差"):
        assert token in text
    assert "25 pp" in text and "2.5 pp" in text
    assert "永远在" in text
    assert "先按容量归档弱节" in text
