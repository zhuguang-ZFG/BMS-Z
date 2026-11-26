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
    for token in ("训练 A / B", "独立标定", "冻结", "验证 C / D", "不回流", "R1 / τ"):
        assert token in text


def test_f11_2_loo_bars_with_delta_ocv():
    _root, text = load("d11-hppc", "D11-F2-loo-validation.svg")
    for token in ("训练回代", "独立预测", "失配", "160.0 mV", "残差", "0.1 mV"):
        assert token in text


def test_d11_figures_rebuild_from_report_without_touching_d12(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("d11_figures", HERE / "make_d11d12_figures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    before = {p.name: p.read_bytes() for p in module.OUT12.glob("*.svg")}
    report = module.d11.build_report()
    module.generate_d11(tmp_path, report)
    for name in ("D11-F1-sharing-contract.svg", "D11-F2-loo-validation.svg"):
        assert (tmp_path / name).read_bytes() == (module.OUT11 / name).read_bytes()
    assert before == {p.name: p.read_bytes() for p in module.OUT12.glob("*.svg")}
    report["noisy"]["validation_rmse_mv"] = 1.234
    assert "1.234 mV" in module.f11_2_loo(report)
    main = module.ROOT / "bms-book/assets/hppc-validation-contract.svg"
    assert main.read_text(encoding="utf-8") == module.validation_contract(report=None)


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
