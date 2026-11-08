"""实测数据的来源、时间基准、标定隔离和独立回放契约。"""
import copy
import csv
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


def test_calibration_rejects_validation_rows_relabelled_as_calibration(experiment):
    groups, _, _, _ = experiment
    altered = copy.deepcopy(groups)
    altered["ocv"] = altered["validation"]
    with pytest.raises(ValueError, match="验证数据混入"):
        calibrate(altered)


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


def test_report_names_reference_and_keeps_row_provenance(experiment):
    groups, _, params, table = experiment
    traces, report = evaluate(groups, params, table)
    assert report["current_convention"] == "charge_positive_discharge_negative"
    assert report["reference_assumptions"]["initial_soc"] == 1.0
    assert report["evaluation_scope"]["held_out"] == "source_steps_same_cell_RW3"
    assert not report["evaluation_scope"]["cross_cell_validated"]
    assert not report["evaluation_scope"]["cross_temperature_validated"]
    assert report["metric_basis"]["voltage_soc_input"] == "computed_reference_not_estimated_soc"
    assert report["diagnostics_window_s"] == pytest.approx(groups["validation"]["time_s"][[1, -1]])
    for key in ("source_step", "source_sample"):
        assert np.array_equal(traces[key], groups["validation"][key])
    assert "ground_truth_soc" not in traces
    # 电压以 V 输入后直接换算 mV，不借用 SOC 百分点指标。
    voltage_error = traces["voltage_calibrated"] - traces["voltage_v"]
    time = traces["time_s"]
    expected_mv = np.sqrt(sum(
        (voltage_error[k - 1] ** 2 + voltage_error[k] ** 2) * 0.5 * (time[k] - time[k - 1])
        for k in range(1, len(time))
    ) / (time[-1] - time[0])) * 1000
    assert report["voltage_rmse_mv"]["calibrated"] == pytest.approx(expected_mv)


def test_estimator_offset_does_not_change_reference_or_open_loop_model(experiment):
    groups, _, params, table = experiment
    baseline, _ = evaluate(groups, params, table)
    altered, _ = evaluate(groups, params, table, current_offset_a=0.02, resistance_scale=2)
    assert np.array_equal(altered["soc_reference"], baseline["soc_reference"])
    assert np.array_equal(altered["voltage_calibrated"], baseline["voltage_calibrated"])
    expected_change = 0.02 * baseline["time_s"] / (3600 * params["capacity_ah"])
    assert altered["coulomb"] - baseline["coulomb"] == pytest.approx(expected_change, abs=1e-12)


def test_reference_is_not_an_input_to_estimators_or_innovation_diagnostics(experiment, monkeypatch):
    groups, _, params, table = experiment
    baseline, baseline_report = evaluate(groups, params, table)
    # 只改变离线参考的构造；估算器仍接收相同原始电流/电压和冻结参数。
    def altered_reference_integral(group):
        integral = cumulative_ah(group)
        return integral + np.linspace(0.0, 0.05, len(integral))

    monkeypatch.setattr("real_data.cumulative_ah", altered_reference_integral)
    altered, altered_report = evaluate(groups, params, table)
    assert not np.array_equal(altered["soc_reference"], baseline["soc_reference"])
    assert not np.array_equal(altered["voltage_calibrated"], baseline["voltage_calibrated"])
    for name in ("coulomb", "ekf_generic", "ekf_calibrated"):
        assert np.array_equal(altered[name], baseline[name])
    assert altered_report["diagnostics"] == baseline_report["diagnostics"]


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


@pytest.mark.parametrize("column,replacement", [("source_sample", "0"), ("source_sample", "1.5"),
                                               ("source_step", "0.5")])
def test_rehashed_data_still_requires_exact_source_row_identity(tmp_path, column, replacement):
    source = json.loads((DATA / "metadata.json").read_text(encoding="utf-8"))
    lines = (DATA / "samples.csv").read_text(encoding="utf-8").splitlines()
    row = lines[2].split(",")
    row[lines[0].split(",").index(column)] = replacement
    lines[2] = ",".join(row)
    payload = ("\n".join(lines) + "\n").encode()
    source["csv_sha256"] = hashlib.sha256(payload).hexdigest()
    (tmp_path / "metadata.json").write_text(json.dumps(source))
    (tmp_path / "samples.csv").write_bytes(payload)
    with pytest.raises(ValueError, match="原始"):
        load_data(tmp_path)


def test_metadata_cannot_silently_redefine_training_split(tmp_path):
    source = json.loads((DATA / "metadata.json").read_text(encoding="utf-8"))
    source["selection"]["ocv"] = [32]
    (tmp_path / "metadata.json").write_text(json.dumps(source))
    (tmp_path / "samples.csv").write_bytes((DATA / "samples.csv").read_bytes())
    with pytest.raises(ValueError, match="划分"):
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
        assert 0 < entry["nis_mean"] < 1.0  # 本数据回归范围，不能单独归因于 R 或证明 SOC 正确。


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
    assert report["provenance"]["archive_and_member_hashes"] == "copied_from_metadata_not_recomputed"
    with (tmp_path / "trace.csv").open(encoding="utf-8", newline="") as stream:
        first = next(csv.DictReader(stream))
    assert (first["source_step"], first["source_sample"]) == ("32", "0")
