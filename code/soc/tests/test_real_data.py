"""实测数据的来源、时间基准、标定隔离和独立回放契约。"""
import copy
import hashlib
import json

import numpy as np
import pytest

from estimators import EKFEstimator
from hppc_demo import fit_relaxation
from real_data import DATA, calibrate, cumulative_ah, evaluate, load_data, metrics, run, tw_mean


@pytest.fixture(scope="module")
def experiment():
    groups, provenance = load_data(DATA)
    params, table = calibrate(groups)
    return groups, provenance, params, table


def test_measured_data_provenance_and_split(experiment):
    groups, source, params, _ = experiment
    assert source["license"] == "CC-BY-4.0"
    assert source["archive_md5"] == "aa53dce833e0ce7ee75376846dec4e59"
    assert source["rows"] == dict(ocv=19120, capacity=725, pulse=3003, validation=2613)
    assert set(params["calibration_steps"]).isdisjoint(params["validation_steps"])
    assert groups["validation"]["current_a"].min() < -3.9
    assert groups["validation"]["time_s"][-1] == pytest.approx(2588.92)
    assert 1.9 < params["capacity_ah"] < 2.2
    assert 0.07 < params["r0_ohm"] < 0.10


def test_fit_does_not_read_validation(experiment):
    groups, _, expected, _ = experiment
    altered = copy.deepcopy(groups)
    for key in altered["validation"]:
        altered["validation"][key][:] = np.nan
    actual, _ = calibrate(altered)
    assert actual == expected


def test_irregular_timestamp_integration_and_time_weighted_error():
    group = dict(time_s=np.array([0.0, 1.0, 4.0]), current_a=np.array([-1.0, -3.0, -1.0]))
    assert cumulative_ah(group) == pytest.approx([0, -2 / 3600, -8 / 3600])
    score = metrics(np.array([0.0, 0.0, 1.0]), np.zeros(3), np.array([0.0, 1.0, 10.0]))
    assert score["rmse_pp"] == pytest.approx(np.sqrt(0.45) * 100)


def test_held_out_baseline_and_model_mismatch(experiment):
    groups, _, params, table = experiment
    traces, report = evaluate(groups, params, table)
    assert not report["independent_soc_truth"]
    assert not report["model_fitted_on_validation"]
    assert report["metrics"]["coulomb"]["rmse_pp"] == pytest.approx(10.0)
    assert traces["ekf_calibrated"][0] == 0.9  # 首样本没有凭空积分一秒。
    assert traces["soc_reference"][0] == 1.0
    assert report["voltage_rmse_mv"]["calibrated"] < 50
    assert report["voltage_rmse_mv"]["generic"] > 100
    # 只是本夹具的回归范围，不宣称所有电芯或工况都能达到此精度。
    assert report["metrics"]["ekf_calibrated"]["rmse_pp"] < 8
    assert report["reference_end_soc"] > 0.1  # 负载截止不等于真正的零 SOC。


@pytest.mark.parametrize("options", [dict(initial_soc=-0.1), dict(initial_soc=np.nan),
                                     dict(current_offset_a=np.inf), dict(resistance_scale=0)])
def test_invalid_experiment_settings_rejected(experiment, options):
    groups, _, params, table = experiment
    with pytest.raises(ValueError):
        evaluate(groups, params, table, **options)


@pytest.mark.parametrize("replacement", [None, "nan", "0", "4199"])
def test_data_corruption_is_not_silently_cleaned(tmp_path, replacement):
    source = json.loads((DATA / "metadata.json").read_text(encoding="utf-8"))
    payload = (DATA / "samples.csv").read_bytes()
    if replacement is None:
        payload += b"\n"  # 哈希失配。
    else:
        lines = payload.decode().splitlines()
        row = lines[2].split(",")
        row[6 if replacement == "4199" else 3] = replacement
        lines[2] = ",".join(row)
        payload = ("\n".join(lines) + "\n").encode()
        source["csv_sha256"] = hashlib.sha256(payload).hexdigest()
    (tmp_path / "metadata.json").write_text(json.dumps(source))
    (tmp_path / "samples.csv").write_bytes(payload)
    with pytest.raises(ValueError):
        load_data(tmp_path)


def test_ekf_uses_instantaneous_current_for_voltage_observation():
    est = EKFEstimator(0.5, 2, 0.1, 0.05, 1000,
                       ocv_func=lambda soc: 3 + soc, docv_func=lambda _soc: 1.0)
    # 区间平均电流为 0，末端瞬时电流为 -2A；SOC 没变，端电压降 0.2V。
    assert est.step(0, 3.3, 1, voltage_current_a=-2) == pytest.approx(0.5)

def test_ekf_records_innovation_and_nis_invariant():
    est = EKFEstimator(0.5, 2, 0.02, 0.015, 3000, r_volt=0.02 ** 2)
    est.step(-1.0, 3.9, 1.0)
    # S ≥ R ⇒ NIS 不超过 innovation²/R；记录的是更新前工作点的原话。
    assert est.last_nis <= est.last_innovation_v ** 2 / est.R + 1e-12
    assert np.isfinite(est.last_innovation_v) and 0 < est.last_nis


def test_truth_free_diagnostics_flag_parameter_mismatch(experiment):
    groups, _, params, table = experiment
    _, report = evaluate(groups, params, table)
    diag = report["diagnostics"]
    # 坏参数不用真值也听得见：新息 RMS 劣化超过一倍以上。
    assert diag["ekf_calibrated"]["innovation_rms_mv"] < 8.0
    assert diag["ekf_generic"]["innovation_rms_mv"] > 14.0
    assert diag["ekf_generic"]["innovation_rms_mv"] > 2 * diag["ekf_calibrated"]["innovation_rms_mv"]
    # 新息均值都近零：静态模型误差被吸进 SOC 状态，残差体面 ≠ SOC 对。
    for entry in diag.values():
        assert abs(entry["innovation_mean_mv"]) < 2.0
        assert 0 < entry["nis_mean"] < 1.0  # NIS 分母含 S=CPCᵀ+R；<1 只说明设得松，不冒充完美


def test_tw_mean_weights_irregular_timestamps_like_metrics():
    # 与 metrics 同口径的回归锚：密集采样段不许自动加权。
    # 本例若退回简单均值会得 1/3，时间加权是 0.5。
    values = np.array([0.0, 1.0, 0.0])
    t_inn = np.array([1.0, 2.0, 100.0])
    assert tw_mean(values, t_inn) == pytest.approx(0.5)

def test_relaxation_accepts_long_time_constant_and_rejects_invalid_grid():
    time = np.linspace(0, 1500, 300)
    voltage = 4.1 - 0.08 * np.exp(-time / 300)
    tau, amp, offset = fit_relaxation(time, voltage, tau_grid=[100, 300, 600])
    assert (tau, amp, offset) == pytest.approx((300, -0.08, 4.1))
    with pytest.raises(ValueError):
        fit_relaxation(time, voltage, tau_grid=[0, np.nan])


def test_report_and_plot_export_without_network(tmp_path):
    report = run(DATA, tmp_path, plot=True)
    assert json.loads((tmp_path / "report.json").read_text()) == report
    assert (tmp_path / "trace.csv").read_text().count("\n") == 2614
    assert (tmp_path / "comparison.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
