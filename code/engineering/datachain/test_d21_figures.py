"""Structural and content checks for D21 figures."""

import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "d21-datachain"


def load(name: str) -> tuple[ET.Element, str]:
    path = ASSETS / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d21_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


def test_f21_1_svg_is_wellformed_with_identity():
    root, _text = load("D21-F1-record-chain.svg")
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None


def test_f21_1_record_chain_stages_and_lineage_tokens():
    _root, text = load("D21-F1-record-chain.svg")
    # 三站链与冻结数字
    for token in ("① 原始身份", "② 单位防火墙 + 质量隔离", "③ 20 ms 对齐网格"):
        assert token in text
    assert "11 条原始记录" in text
    assert "51200 mV → 51.2 V" in text
    assert "120 dA → 12.0 A" in text
    assert "quarantine" in text and "estimator seq 3" in text
    assert "age=20" in text and "age=180" in text
    # 谱系与回放判定
    assert "source_sha256" in text
    assert "config_sha256" in text
    assert "exit 2" in text
