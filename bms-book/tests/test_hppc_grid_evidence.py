"""Independent numerical oracles for the chapter 28 lookup-table experiment."""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]


def evidence(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "bms-book/code"))
    import hppc_grid_evidence
    return hppc_grid_evidence


def test_nonuniform_rectangular_table_preserves_axis_order(monkeypatch):
    module = evidence(monkeypatch)
    soc, temp = [.2, .5, .8], [5., 25.]
    values = np.array([[2, 4], [7, 11], [13, 17]], dtype=float)
    # Independent four-corner weights: z fraction 1/3, T fraction 1/4.
    expected = (2 * 2/3 * 3/4 + 7 * 1/3 * 3/4
                + 4 * 2/3 * 1/4 + 11 * 1/3 * 1/4)
    got = module.interpolate_table(soc, temp, values, [[.3, 10.]])
    assert got.shape == (1,)
    assert got[0] == pytest.approx(expected)
    with pytest.raises(ValueError):
        module.interpolate_table(soc, temp, values.T, [[.3, 10.]])


@pytest.mark.parametrize("coefficients", [(3, 0, 0, 0), (3, .8, .01, 0), (3, .8, .01, .02)])
def test_bilinear_functions_and_boundary_nodes_are_exact(monkeypatch, coefficients):
    module = evidence(monkeypatch)
    a, b, c, d = coefficients
    def f(z, t):
        return a + b*z + c*t + d*z*t
    soc, temp = [.2, .3, .8], [5., 10., 25., 40.]
    points = [[s, t] for s in soc for t in temp] + [[.23, 7.], [.6, 33.]]
    values = [[f(s, t) for t in temp] for s in soc]
    result = module.interpolate_table(soc, temp, values, points)
    assert np.allclose(result, [f(s, t) for s, t in points], atol=1e-13, rtol=0)


@pytest.mark.parametrize("soc,temp,values,queries", [
    ([.4], [15, 35], [[3, 4]], [[.4, 25]]),
    ([.4, .6], [25], [[3], [4]], [[.5, 25]]),
    ([.4, .4], [15, 35], [[3, 4], [4, 5]], [[.4, 25]]),
    ([.6, .4], [15, 35], [[3, 4], [4, 5]], [[.5, 25]]),
    ([.4, .6], [35, 15], [[3, 4], [4, 5]], [[.5, 25]]),
    ([-.1, .6], [15, 35], [[3, 4], [4, 5]], [[.5, 25]]),
    ([.4, 1.1], [15, 35], [[3, 4], [4, 5]], [[.5, 25]]),
    ([.4, np.nan], [15, 35], [[3, 4], [4, 5]], [[.5, 25]]),
    ([.4, .6], [15, np.inf], [[3, 4], [4, 5]], [[.5, 25]]),
    ([.4, .6], [15, 35], [[3, np.nan], [4, 5]], [[.5, 25]]),
    ([.4, .6], [15, 35], [[3, 4]], [[.5, 25]]),
    ([.4, .6], [15, 35], [[3, 4], [4, 5]], [.5, 25]),
    ([.4, .6], [15, 35], [[3, 4], [4, 5]], []),
    ([.4, .6], [15, 35], [[3, 4], [4, 5]], [[.5, 25, 1]]),
    ([.4, .6], [15, 35], [[3, 4], [4, 5]], [[np.inf, 25]]),
])
def test_invalid_table_or_queries_are_rejected(monkeypatch, soc, temp, values, queries):
    with pytest.raises(ValueError):
        evidence(monkeypatch).interpolate_table(soc, temp, values, queries)


@pytest.mark.parametrize("point", [[.39, 25], [.61, 25], [.5, 14], [.5, 36], [1.05, 25]])
def test_outside_calibrated_domain_is_not_clamped(monkeypatch, point):
    with pytest.raises(ValueError):
        evidence(monkeypatch).interpolate_table([.4, .6], [15, 35], [[3, 4], [4, 5]], [point])
    assert point in [[.39, 25], [.61, 25], [.5, 14], [.5, 36], [1.05, 25]]


def test_constant_node_bias_survives_refinement(monkeypatch):
    module = evidence(monkeypatch)
    for size in [3, 5, 9]:
        soc, temp = np.linspace(.4, .6, size), np.linspace(15, 35, size)
        values = soc[:, None] + .01*temp[None, :]
        queries = [[.43, 21.], [.57, 31.]]
        before = module.interpolate_table(soc, temp, values, queries)
        after = module.interpolate_table(soc, temp, values + .002, queries)
        assert after - before == pytest.approx([.002, .002])


def test_quadratic_error_matches_independent_analytic_bound(monkeypatch):
    module = evidence(monkeypatch)
    def f(z, t):
        return 3.2 + .8*z + .2*z*z + 1e-4*(t-25)**2 + 1e-3*z*(t-25)
    for hz, ht in [(.1, 10), (.05, 10), (.1, 5), (.05, 5)]:
        soc, temp = np.linspace(.4, .6, round(.2/hz)+1), np.linspace(15, 35, round(20/ht)+1)
        y = [[f(s, t) for t in temp] for s in soc]
        points = [[s, t] for s in (soc[1:]+soc[:-1])/2 for t in (temp[1:]+temp[:-1])/2]
        error = module.interpolate_table(soc, temp, y, points) - [f(s, t) for s, t in points]
        exact = .2*hz**2/4 + 1e-4*ht**2/4
        assert error == pytest.approx([exact]*len(points))
        assert module.bilinear_bound(hz, ht, .4, .0002) == pytest.approx(exact)
    assert module.bilinear_bound(.1, 10, 0, 0) == 0


@pytest.mark.parametrize("args", [(0, 10, .4, .0002), (-.1, 10, .4, .0002),
    (.1, 0, .4, .0002), (.1, 10, -.4, .0002), (.1, 10, .4, -1),
    (np.nan, 10, .4, .0002), (.1, np.inf, .4, .0002)])
def test_bound_requires_finite_nonnegative_derivative_bounds(monkeypatch, args):
    with pytest.raises(ValueError):
        evidence(monkeypatch).bilinear_bound(*args)


def test_hidden_curvature_is_monotone_and_invisible_at_nodes(monkeypatch):
    report = evidence(monkeypatch).build_report()
    case = report["hidden_curvature"]
    assert abs(np.diff(case["node_values_v"], n=2)[0]) < 1e-14
    assert case["validation_residual_mv"] == pytest.approx([20, 20])
    assert case["derivative_lower_bound_v_per_soc"] > 0
    assert set(case["validation_soc"]).isdisjoint(case["node_soc"])
    z = np.array(case["curve_soc"])
    expected = 3.2 + .8*z + .02*np.sin(np.pi*(z-.4)/.1)**2
    assert case["curve_true_v"] == pytest.approx(expected)
    assert np.diff(case["curve_true_v"]).min() > 0


def test_report_distinguishes_coordinate_error_from_interpolation(monkeypatch):
    report = evidence(monkeypatch).build_report()
    assert report["schema"] == 1 and report["synthetic"] is True
    case = report["coordinate_vs_grid"]
    assert case["steep_line_interpolation_error_mv"] < 1e-10
    assert case["coordinate_error_mv"] == pytest.approx(340.)
    assert case["nonlinear_finite_delta_mv"] == pytest.approx(221.029650732)
    assert [x["error_mv"] for x in report["axis_refinement"]] == pytest.approx([3, 2.625, 1.125, .75])
    assert report["node_error"]["total_error_mv"] == pytest.approx(5)
    assert all(x["rejected"] for x in report["domain_policy"]["checks"])


def test_cli_writes_the_same_finite_report_to_stdout_and_file(tmp_path):
    result = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "bms-book/code/hppc_grid_evidence.py"),
                             "--out", str(tmp_path)], check=True, capture_output=True, text=True, encoding="utf-8")
    report = json.loads(result.stdout)
    assert report == json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    json.dumps(report, allow_nan=False)
