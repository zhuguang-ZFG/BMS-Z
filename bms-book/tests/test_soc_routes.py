"""第 12 章 §12.4 的三张表与动手题：逐格钉住 soc_coulomb_ocv.py 的实算值。

正文把表 12-4／12-5 的形容词换成了数字，这里保证那些数字与 demo 不漂移。
初稿在这一节错过一次：原来写「删掉最后 48 h 静置，误差会更靠近真值」，实测
反而更远（46.39% vs 46.15%）——因为那段静置自己末尾就带一次锚点，删掉等于
少了一次校正。所以本文件除了钉数字，也钉住那条被纠正过的机制。
"""
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1] / "code"
TRUE_FINAL = 40.0


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def soc():
    return load("soc_coulomb_ocv")


def test_profile_shape_matches_the_prose(soc):
    """正文写的「238 h、净 −60 Ah、四段 ≥1 h 静置」三件事。"""
    total_h = sum(duration for duration, _ in soc.PROFILE) / 3600
    assert total_h == pytest.approx(238.0)
    net_ah = sum(current * duration / 3600 for duration, current in soc.PROFILE)
    assert net_ah == pytest.approx(-60.0)
    rests = [d / 3600 for d, c in soc.PROFILE if d >= 3600 and abs(c) < 1e-9]
    assert rests == [8.0, 8.0, 168.0, 48.0], "锚点机会的段数/时长变了，表 12-7 要跟着改"


def test_table_12_6_rows(soc):
    """表 12-6 的五行终值与最大误差。"""
    expected = [
        # (use_ocv, bias, q_model, final, max_err)
        (False, 0.0, 100.0, 40.00, 0.00),
        (False, 0.05, 100.0, 51.90, 11.90),
        (True, 0.0, 100.0, 40.00, 0.00),
        (True, 0.05, 100.0, 46.15, 9.06),
        (True, 0.0, 95.0, 39.01, 2.77),
    ]
    for use_ocv, bias, q_model, final, max_err in expected:
        got_final, got_max = soc.simulate(use_ocv, bias, q_model)
        label = f"use_ocv={use_ocv} bias={bias} q={q_model}"
        assert got_final == pytest.approx(final, abs=5e-3), label
        assert got_max == pytest.approx(max_err, abs=5e-3), label

    # 正文的算术主张：纯库仑的偏置误差 = 偏置 × 总时长 ÷ 容量，一位不差。
    total_h = sum(d for d, _ in soc.PROFILE) / 3600
    predicted = 0.05 * total_h / 100.0 * 100
    assert predicted == pytest.approx(11.90, abs=5e-3)
    drifted, _ = soc.simulate(False, 0.05)
    assert drifted - TRUE_FINAL == pytest.approx(predicted, abs=5e-3)


def test_table_12_7_each_anchor_recovers_only_thirty_percent(soc):
    """表 12-7：四次锚点的校正前后偏差。

    锚点按 0.7/0.3 混合，所以每次只收回当时偏差的 30%；7 天静置那次
    校正前已攒到 +9.06 pp，正是全程最大误差出现的时刻。
    """
    soc_true = soc_est = 100.0
    anchors = []
    gap_entering_long_rest = None
    for duration, current in soc.PROFILE:
        steps = int(duration // soc.DT_S)
        is_anchor_rest = duration >= 3600 and abs(current) < 1e-9
        if is_anchor_rest and duration == 7 * 24 * 3600:
            # 正文引用的是「7 天静置自己攒了多少」，所以记进入这段时的偏差，
            # 不能拿上一次锚点后的值去减（那中间还夹着一段 2 h 放电）。
            gap_entering_long_rest = soc_est - soc_true
        for step in range(steps):
            soc_true += current * soc.DT_S / 3600.0 / 100.0 * 100.0
            soc_est += (current + 0.05) * soc.DT_S / 3600.0 / 100.0 * 100.0
            if is_anchor_rest and step == steps - 1:
                before = soc_est - soc_true
                soc_ocv = soc.soc_from_ocv(soc.ocv_from_soc(soc_true))
                soc_est = 0.7 * soc_est + 0.3 * soc_ocv
                anchors.append((before, soc_est - soc_true, soc_ocv, soc_true))

    published = [(0.50, 0.35), (0.80, 0.56), (9.06, 6.34), (8.79, 6.15)]
    assert len(anchors) == 4
    for (before, after, _, _), (exp_before, exp_after) in zip(anchors, published, strict=True):
        assert before == pytest.approx(exp_before, abs=5e-3)
        assert after == pytest.approx(exp_after, abs=5e-3)
        # 每次正好收回 30%：剩下的是 0.7 倍。
        assert after == pytest.approx(before * 0.7, abs=5e-3)

    # demo 的锚点读数由真值反推，本身无误差——正文声明过这条边界。
    for _, _, soc_ocv, truth in anchors:
        assert soc_ocv == pytest.approx(truth, abs=1e-9)

    # 7 天静置自己攒了 0.05 A × 168 h ÷ 100 Ah = 8.4 pp（正文的「+0.66 → +9.06」）。
    assert gap_entering_long_rest == pytest.approx(0.66, abs=5e-3)
    assert anchors[2][0] - gap_entering_long_rest == pytest.approx(8.4, abs=5e-3)
    assert anchors[2][0] == pytest.approx(9.06, abs=5e-3)
    # 这一刻也正是全程最大误差：锚点开口前的最后一秒。
    _, max_err = soc.simulate(True, 0.05)
    assert max_err == pytest.approx(anchors[2][0], abs=5e-3)
    assert soc_est == pytest.approx(46.15, abs=5e-3)


def _patched(module_name: str, replacements: list[tuple[str, str]]):
    """用改过源码的副本加载 demo，用于复算动手题的三个对照。"""
    source = (ROOT / "soc_coulomb_ocv.py").read_text(encoding="utf-8")
    for old, new in replacements:
        assert old in source, f"源码里找不到 {old!r}，动手题的改法要跟着更新"
        source = source.replace(old, new)
    target = ROOT.parent / "tests" / f"_patched_{module_name}.py"
    target.write_text(source, encoding="utf-8")
    try:
        spec = importlib.util.spec_from_file_location(module_name, target)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        target.unlink(missing_ok=True)


def test_lab_exercise_one_quadrupled_bias():
    """动手题 1：偏置 0.2 A 时纯库仑终值 87.6%（正文让读者先手算）。"""
    module = _patched("soc_bias_x4", [("BIAS_A = 0.05", "BIAS_A = 0.2")])
    final, _ = module.simulate(False, module.BIAS_A)
    assert final == pytest.approx(87.60, abs=5e-3)
    assert final == pytest.approx(100 - 60 + 0.2 * 238, abs=5e-3)


def test_lab_exercise_two_full_trust_fixes_the_end_not_the_middle():
    """动手题 2：权重改成 1.0，终值归零，但最大误差只到 8.50 pp。

    这是正文把两个原因分开的那个实验：权重管「最后收不收干净」，
    锚点疏密管「中途能飘多远」。
    """
    module = _patched("soc_full_trust", [
        ("soc_est = 0.7 * soc_est + 0.3 * soc_ocv",
         "soc_est = 0.0 * soc_est + 1.0 * soc_ocv"),
    ])
    final, max_err = module.simulate(True, 0.05)
    assert final == pytest.approx(TRUE_FINAL, abs=5e-3), "完全信 OCV 后终值应归零"
    assert max_err == pytest.approx(8.50, abs=5e-3), "中途那 8.50 pp 不是权重能救的"


def test_lab_exercise_three_anchor_density_is_what_helps():
    """动手题 3：把 7 天静置拆成七段，锚点 4→10 次，最大误差 9.06→5.07 pp。"""
    module = _patched("soc_dense_anchors", [
        ("    (7 * 24 * 3600, 0.0),", "".join("    (24 * 3600, 0.0),\n" for _ in range(7)).rstrip("\n")),
    ])
    anchors = sum(1 for d, c in module.PROFILE if d >= 3600 and abs(c) < 1e-9)
    assert anchors == 10
    assert sum(d for d, _ in module.PROFILE) / 3600 == pytest.approx(238.0), "总时长不该变"
    final, max_err = module.simulate(True, 0.05)
    assert max_err == pytest.approx(5.07, abs=5e-3)
    assert final == pytest.approx(43.55, abs=5e-3)


def test_removing_the_last_rest_does_not_help(soc):
    """钉住初稿那个被实测否掉的说法。

    「删掉最后 48 h 静置，误差会更靠近真值」是错的：那段静置末尾自带一次锚点，
    删掉反而少一次校正（46.39% 比 46.15% 更远）。留这条测试是为了不再写回去。
    """
    module = _patched("soc_no_tail_rest", [("    (2 * 24 * 3600, 0.0),\n]", "]")])
    final, _ = module.simulate(True, 0.05)
    assert final == pytest.approx(46.39, abs=5e-3)
    baseline, _ = soc.simulate(True, 0.05)
    assert abs(final - TRUE_FINAL) > abs(baseline - TRUE_FINAL), \
        "删掉尾段静置会更远离真值，不是更近"
