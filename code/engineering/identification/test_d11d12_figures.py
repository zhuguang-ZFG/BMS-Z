"""Structural checks for D11 and D12 figures."""
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def load(sub: str, name: str) -> tuple[ET.Element, str]:
    path = HERE.parents[2] / "bms-book" / "engineering" / "assets" / sub / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d11d12_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


@pytest.mark.parametrize("sub,name", [
    ("d11-hppc", "D11-F1-sharing-contract.svg"),
    ("d11-hppc", "D11-F2-loo-validation.svg"),
    ("d12-soc", "D12-F1-three-errors.svg"),
    ("d12-soc", "D12-F2-calibration.svg"),
])
def test_svg_is_wellformed_with_identity(sub, name):
    root, text = load(sub, name)
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None
    assert 'class="bg"' in text and 'class="title"' in text


def test_f11_1_shows_shared_tau_and_free_k():
    _root, text = load("d11-hppc", "D11-F1-sharing-contract.svg")
    assert "τ = 45 s（共享）" in text
    assert "K/A 逐脉冲自由" in text
    assert "留出 160 mV" in text
    assert "写不出理由默认逐工况自由" in text


def test_f11_2_loo_bars_with_delta_ocv():
    _root, text = load("d11-hppc", "D11-F2-loo-validation.svg")
    assert "160.0 mV = ΔOCV" in text
    assert "0.0 mV" in text
    assert "留出残差才是可迁移性的证据" in text


def test_f12_1_three_error_curves():
    _root, text = load("d12-soc", "D12-F1-three-errors.svg")
    for token in ("偏置 50 mA：25 pp / 10 h", "初值错 10 pp", "容量错 5%"):
        assert token in text
    assert "三种伤要不同的医生" in text


def test_f12_2_three_calibration_conditions():
    _root, text = load("d12-soc", "D12-F2-calibration.svg")
    for cond in ("静置够久", "斜率够陡", "迟滞同支"):
        assert cond in text
    assert "0.62 pp" in text and "6.25 pp" in text and "1.25 pp" in text
    assert "同页附三个条件的满足证据" in text
