"""D11: independent predictions, fitted time constants and explicit calibration."""
import importlib.util
import math
from pathlib import Path
import sys
from dataclasses import replace

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d11_joint_hppc", HERE / "d11_joint_hppc.py")
assert spec is not None and spec.loader is not None
d11 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d11
spec.loader.exec_module(d11)


def observations(tau=62.0, noise=0.0):
    truth = d11.Truth(r1_ohm=0.023, tau_s=tau)
    calibration = d11.Calibration()
    return tuple(d11.simulate_tail(p, truth, calibration, noise_sigma_v=noise)
                 for p in d11.TRAIN_PULSES)


def test_joint_fit_recovers_truth_and_r1():
    fit = d11.joint_fit(observations())
    assert fit["tau"] == pytest.approx(62.0)
    assert fit["r1_ohm"] == pytest.approx(0.023, rel=1e-8)
    assert fit["c1_f"] == pytest.approx(62 / 0.023)
    assert fit["rms_mv"] < 1e-8
    assert not fit["boundary_hit"]


@pytest.mark.parametrize("current", [2.0, -1.5])
def test_finite_pulse_correction_uses_fitted_tau(current):
    tau, pulse_s, r1 = 30.0, 17.0, 0.023
    amplitude = -current * r1 * (1 - math.exp(-pulse_s / tau))
    assert d11.r1_from_amplitude(amplitude, current, tau_s=tau, pulse_s=pulse_s) == pytest.approx(r1)


def test_wrong_grid_conversion_remains_consistent_with_fit():
    obs = observations()[0]
    fit = d11.fit_kat(obs.tail, [30.0])
    expected = -fit["A"] / (obs.pulse.current_a * (1 - math.exp(-obs.pulse.pulse_s / 30)))
    actual = d11.r1_from_amplitude(fit["A"], obs.pulse.current_a, tau_s=fit["tau"], pulse_s=obs.pulse.pulse_s)
    assert actual == pytest.approx(expected)
    assert actual != pytest.approx(0.023, rel=.01)


def test_validation_voltage_changes_scores_not_fit_or_prediction():
    train = observations(noise=.0001)
    pulse = d11.VALIDATION_PULSES[0]
    cal = d11.Calibration()
    fit = d11.joint_fit(train)
    prediction = d11.predict_tail(fit, pulse, cal)
    observed = d11.simulate_tail(pulse, d11.Truth(r1_ohm=.023, tau_s=62), cal)
    changed = replace(observed, tail=tuple((t, v + .05) for t, v in observed.tail))
    first = d11.score_prediction(prediction, observed)
    second = d11.score_prediction(prediction, changed)
    assert second > first + 40
    assert d11.joint_fit(train) == fit
    assert d11.predict_tail(fit, pulse, cal) == prediction


def test_train_validation_overlap_rejected_before_prediction():
    fit = d11.joint_fit(observations())
    with pytest.raises(ValueError, match="training"):
        d11.predict_tail(fit, d11.TRAIN_PULSES[0], d11.Calibration())


def test_tail_asymptote_uses_post_pulse_soc():
    pulse = d11.TRAIN_PULSES[0]
    cal = d11.Calibration()
    obs = d11.simulate_tail(pulse, d11.Truth(), cal)
    fit = d11.fit_kat(obs.tail, [45.0])
    assert fit["K"] == pytest.approx(3.677777777777778)
    assert fit["K"] != pytest.approx(3.68, abs=1e-4)


def test_boundary_hit_is_reported_not_silent():
    tail = observations()[0].tail
    assert not d11.fit_kat(tail, [62.0])["boundary_hit"]
    assert d11.fit_kat(tail, [62.0, 120.0])["boundary_hit"]
    fit = d11.joint_fit(observations(), grid=[1.0, 30.0])
    assert fit["boundary_hit"] and fit["tau"] == 30.0


def test_k_is_local_asymptote_not_transferable():
    old = d11.build_report()["local_k_counterexample"]
    assert old["transferred_k_rmse_mv"] == pytest.approx(160.0)
    assert old["training_rmse_mv"] < 1e-7
    assert old["identity"] == "noiseless same-protocol local-K transfer"


def test_report_separates_noisy_holdout_and_model_mismatch():
    report = d11.build_report()
    assert report["schema_version"] == 2
    assert "leave_one_out_rmse_mv" not in report
    assert set(report["split"]["training"]).isdisjoint(report["split"]["validation"])
    assert report["noiseless"]["validation_rmse_mv"] < 1e-7
    assert .07 < report["noisy"]["validation_rmse_mv"] < .15
    assert report["mismatch"]["validation_rmse_mv"] > 5 * report["noisy"]["validation_rmse_mv"]
    assert report["mismatch"]["fit"] == report["noisy"]["fit"]
    assert "S2" in report["identity"] and "OS02" in report["identity"]


def test_scipy_optimizes_same_training_objective():
    train = observations(tau=62.3, noise=.0001)
    grid = [61 + k * .01 for k in range(301)]
    baseline = d11.joint_fit(train, grid=grid)
    scipy_fit = d11.scipy_joint_fit(train, tau_bounds=(61., 64.))
    assert scipy_fit["success"]
    assert scipy_fit["sse"] <= baseline["sse"] + 1e-12
    assert scipy_fit["tau"] == pytest.approx(baseline["tau"], abs=.011)
    assert scipy_fit["r1_ohm"] == pytest.approx(baseline["r1_ohm"], rel=.001)


@pytest.mark.parametrize("kwargs", [{"tau_s": 0}, {"tau_s": float('nan')}, {"pulse_s": -1}, {"i_pulse_a": 0}])
def test_amplitude_conversion_rejects_invalid_inputs(kwargs):
    args = dict(a_v=-.01, i_pulse_a=2., tau_s=30., pulse_s=10.)
    args.update(kwargs)
    with pytest.raises(ValueError):
        d11.r1_from_amplitude(**args)


def test_invalid_observations_do_not_produce_parameters():
    with pytest.raises(ValueError):
        d11.joint_fit(())
    obs = observations()[0]
    for bad in [replace(obs, tail=()), replace(obs, tail=((0., 3.6), (0., 3.5))),
                replace(obs, tail=((0., 3.6), (1., float('nan')))),
                replace(obs, pulse=replace(obs.pulse, current_a=0.))]:
        with pytest.raises(ValueError):
            d11.joint_fit((bad,))
    with pytest.raises(ValueError):
        d11.joint_fit((obs, obs))


def test_independent_calibration_controls_prediction():
    fit = d11.joint_fit(observations())
    pulse = d11.VALIDATION_PULSES[0]
    first = d11.predict_tail(fit, pulse, d11.Calibration())
    second = d11.predict_tail(fit, pulse, d11.Calibration(ocv0_v=3.61))
    assert all(v2 - v1 == pytest.approx(.01) for (_, v1), (_, v2) in zip(first.tail, second.tail, strict=True))


def test_score_rejects_wrong_pulse_and_time_grid():
    fit = d11.joint_fit(observations())
    pulse = d11.VALIDATION_PULSES[0]
    prediction = d11.predict_tail(fit, pulse, d11.Calibration())
    obs = d11.simulate_tail(pulse, d11.Truth(), d11.Calibration())
    with pytest.raises(ValueError):
        d11.score_prediction(prediction, replace(obs, tail=obs.tail[1:]))
    with pytest.raises(ValueError):
        d11.score_prediction(prediction, replace(obs, pulse=d11.VALIDATION_PULSES[1]))
