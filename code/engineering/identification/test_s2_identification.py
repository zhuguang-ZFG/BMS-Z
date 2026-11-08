"""S2 pulse/rest identification: analytic anchors, fit contract and negative cases.

The tolerances here are floating-point consistency tolerances for synthetic data,
not hardware accuracy. Every expected value is either a closed-form expression of
the frozen scenario or a value produced by this module's own declared equations.
"""
import functools
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    's2_identification', Path(__file__).resolve().parent / 's2_identification.py'
)
assert _spec is not None and _spec.loader is not None
s2 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = s2  # dataclasses resolve annotations through sys.modules
_spec.loader.exec_module(s2)

CFG = s2.CellConfig()
TAUS = s2.tau_grid()


@functools.lru_cache(maxsize=1)
def report():
    return s2.build_report(CFG)


def test_anchors_of_the_frozen_scenario():
    table = s2.simulate_pulse(CFG)
    assert table['pre_step_v'] - table['first_pulse_v'] == pytest.approx(0.040, abs=1e-15)
    assert table['state_at_release']['vp_v'] == pytest.approx(0.005977877912495758, rel=1e-12)
    assert table['state_at_release']['z'] == pytest.approx(0.5972222222222222, rel=1e-12)
    long_pulse = s2.simulate_pulse(s2.replace(CFG, pulse_s=30.0))
    assert long_pulse['state_at_release']['vp_v'] == pytest.approx(0.01459748642902224, rel=1e-12)
    assert 0.60 - long_pulse['state_at_release']['z'] == pytest.approx(0.008333333333333, rel=1e-12)


def test_no_noise_fit_hits_grid_tau_and_validation_is_analytic():
    table = s2.simulate_pulse(CFG)
    fit = s2.identify(CFG, table, TAUS)
    assert fit['tau_s'] == pytest.approx(45.0, abs=1e-12)
    assert fit['tau_at_grid_boundary'] is False
    assert fit['n_samples'] == 361
    assert abs(fit['r1_rel_error']) <= 1e-6
    assert abs(fit['c1_rel_error']) <= 1e-6
    assert abs(fit['z_error']) <= 1e-9
    validation = s2.validation_rmse(CFG, fit)
    assert validation['rmse_v'] <= 1e-8
    assert validation['max_abs_v'] <= 1e-8


def test_r0_comes_from_both_limits_and_sampling_biases_it():
    table = s2.simulate_pulse(CFG)
    r0 = s2.r0_limits(CFG, table)
    assert r0['r0_from_on_step_ohm'] == pytest.approx(0.020, rel=1e-12)
    assert r0['r0_from_release_ohm'] == pytest.approx(0.020, rel=1e-12)
    assert r0['r0_finite_sample_ohm'] == pytest.approx(0.020221299716146834, rel=1e-12)
    assert r0['r0_finite_sample_rel_error'] == pytest.approx(0.01106498580734172, rel=1e-12)
    terms = r0['finite_sample_terms']
    # The sampled estimate above R0 is the polarization growth plus the OCV move.
    assert terms['polarization_v'] == pytest.approx(
        CFG.r1_ohm * (1 - math.exp(-CFG.dt_s / CFG.tau_s)) * CFG.current_a
    )
    assert terms['soc_drop_v'] == pytest.approx(
        CFG.ocv_slope_v_per_soc * CFG.current_a * CFG.dt_s / (3600 * CFG.q_ah)
    )


def test_ignoring_the_finite_pulse_correction_is_rejected():
    table = s2.simulate_pulse(CFG)
    fit = s2.identify(CFG, table, TAUS)
    naive = s2.naive_r1(CFG, fit)
    assert naive['correction_factor'] == pytest.approx(0.19926259708319194, rel=1e-12)
    assert naive['rel_error'] == pytest.approx(-0.8007374029167945, rel=1e-12)
    # The wrong method is off by more than a factor of four, not a rounding detail.
    assert naive['r1_no_finite_pulse_correction_ohm'] < 0.2 * CFG.r1_ohm
    assert abs(fit['r1_rel_error']) <= 1e-6


def test_last_rest_sample_is_not_the_asymptote():
    table = s2.simulate_pulse(CFG)
    short = s2.last_sample_misuse(CFG, table, 5.0)
    long = s2.last_sample_misuse(CFG, table, CFG.rest_s)
    assert short['bias_v'] == pytest.approx(-0.005349240187217497, rel=1e-12)
    assert short['soc_error_pp'] == pytest.approx(-0.6686550234021871, rel=1e-12)
    assert long['bias_v'] == pytest.approx(-0.0001094886531660677, rel=1e-12)
    assert long['soc_error_pp'] == pytest.approx(-0.013686081645758463, rel=1e-12)
    # Never zero: the tail is small at 180 s only because this scenario's tau is known.
    assert short['bias_v'] < 0 and long['bias_v'] < 0


def test_local_observability_determinant_and_unit_scale():
    fast = s2.observability(CFG, 0.5)
    slow = s2.observability(CFG, 5.0)
    assert fast['det'] == pytest.approx(
        CFG.ocv_slope_v_per_soc * (1 - math.exp(-0.5 / CFG.tau_s)), rel=1e-12
    )
    assert slow['det'] / fast['det'] >= 9.0
    # The determinant is unit-dependent: expressing z in percent multiplies it by 100.
    assert fast['det_percent_scale'] == pytest.approx(100 * fast['det'], rel=1e-12)
    flat = s2.observability(s2.replace(CFG, ocv_slope_v_per_soc=0.08), 0.5)
    assert flat['det'] == pytest.approx(0.0008839688564862147, rel=1e-12)
    zero = s2.observability(s2.replace(CFG, ocv_slope_v_per_soc=0.0), 0.5)
    assert zero['det'] == 0.0


def test_flat_ocv_bias_counterexample_has_identical_voltage_and_10pp_soc_gap():
    counter = s2.bias_counterexample()
    assert counter['max_abs_voltage_diff_v'] <= 1e-12
    assert counter['soc_diff_pp'] == pytest.approx(-10.0, abs=1e-12)
    assert counter['n_samples'] == 382


def test_two_decay_candidates_share_start_and_initial_slope_but_split_late():
    curves = s2.ambiguity_curves()
    assert curves['v1_start'] == pytest.approx(curves['v2_start'], abs=1e-12)
    assert curves['v1_initial_slope'] == pytest.approx(curves['v2_initial_slope'], abs=1e-15)
    assert curves['diff_5s_v'] == pytest.approx(7.671474758375041e-05, rel=1e-12)
    assert curves['diff_120s_v'] == pytest.approx(0.008971740868986, rel=1e-12)
    assert curves['diff_120s_v'] > 100 * curves['diff_5s_v']


def test_bias_inversion_scales_with_ocv_slope():
    steep = s2.bias_inversion(0.8, 0.005)
    flat = s2.bias_inversion(0.08, 0.005)
    assert steep['soc_error_pp'] == pytest.approx(0.625, rel=1e-12)
    assert flat['soc_error_pp'] == pytest.approx(6.25, rel=1e-12)
    assert flat['soc_error_pp'] == pytest.approx(10 * steep['soc_error_pp'], rel=1e-12)


def test_seed7_noise_example_is_reproducible_and_marks_the_grid_edge():
    table = s2.simulate_pulse(CFG)
    first = s2.noisy_rest(CFG, table, 7, CFG.noise_sigma_v)
    second = s2.noisy_rest(CFG, table, 7, CFG.noise_sigma_v)
    assert first == second
    example = report()['noise_example_seed7']
    assert example['long']['tau_s'] == 43.0
    assert example['long']['k_error_v'] == pytest.approx(3.4875740369422203e-05, rel=1e-9)
    assert example['short']['tau_s'] == 120.0
    assert example['short']['tau_at_grid_boundary'] is True
    assert example['short']['k_error_v'] == pytest.approx(0.016614269542460036, rel=1e-9)
    assert example['short']['z_error'] == pytest.approx(0.020767836928075156, rel=1e-9)


def test_noise_sensitivity_keeps_per_seed_rows_and_makes_no_universal_claim():
    sensitivity = report()['noise_sensitivity']
    assert sensitivity['seeds'] == list(range(10))
    assert sensitivity['n_seeds'] == 10
    assert len(sensitivity['per_seed']) == 10
    assert sensitivity['long_better_both_metrics'] == 10
    assert sensitivity['median_abs_k_error_long_v'] < sensitivity['median_abs_k_error_short_v']
    assert sensitivity['universal_ordering_claim'] is False
    for row in sensitivity['per_seed']:
        assert set(row) >= {'seed', 'long', 'short', 'abs_tau_error_long_s', 'abs_tau_error_short_s'}
        assert row['long']['window_s'] == CFG.rest_s
        assert row['short']['window_s'] == 5.0


def test_tau_outside_the_grid_is_reported_at_the_boundary():
    slow = s2.replace(CFG, r1_ohm=0.015, c1_f=200.0 / 0.015)
    assert slow.tau_s == pytest.approx(200.0, rel=1e-12)
    fit = s2.identify(slow, s2.simulate_pulse(slow), TAUS)
    assert fit['tau_s'] == 120.0
    assert fit['tau_at_grid_boundary'] is True
    assert fit['tau_error_s'] == pytest.approx(-80.0, abs=1e-12)


def test_invalid_configs_and_windows_are_rejected():
    with pytest.raises(ValueError):
        s2.CellConfig(q_ah=0.0)
    with pytest.raises(ValueError):
        s2.CellConfig(dt_s=0.0)
    with pytest.raises(ValueError):
        s2.CellConfig(noise_sigma_v=-1e-3)
    with pytest.raises(ValueError):
        s2.CellConfig(z0=0.001, current_a=2.0, pulse_s=10.0)
    with pytest.raises(ValueError):
        s2.CellConfig(pulse_s=10.3)
    with pytest.raises(ValueError):
        s2.tau_grid(10.0, 10.2, 0.5)
    with pytest.raises(ValueError):
        s2.tau_grid(0.0, 10.0, 0.5)
    table = s2.simulate_pulse(CFG)
    with pytest.raises(ValueError):
        s2.identify(CFG, table, TAUS, window_s=0.1)
    with pytest.raises(ValueError):
        s2.noisy_rest(CFG, table, 7, -1e-3)
    with pytest.raises(ValueError):
        s2.replace(CFG, ocv_slope_v_per_soc=0.0).z_from_ocv(3.6)


def test_cli_writes_evidence_refuses_overwrite_and_withholds_student_answers(tmp_path):
    reference_dir = tmp_path / 'reference'
    assert s2.main(['--out', str(reference_dir)]) == 0
    for name in ('config.json', 'observations.csv', 'report.json'):
        assert (reference_dir / name).is_file()
    payload = json.loads((reference_dir / 'report.json').read_text(encoding='utf-8'))
    assert payload['report_version'] == s2.REPORT_VERSION
    assert payload['input_digest'].startswith('sha256:')
    assert payload['generator']['name'] == s2.GENERATOR
    before = (reference_dir / 'report.json').read_bytes()
    assert s2.main(['--out', str(reference_dir)]) == 2
    assert (reference_dir / 'report.json').read_bytes() == before

    second_dir = tmp_path / 'second'
    assert s2.main(['--out', str(second_dir)]) == 0
    assert (second_dir / 'report.json').read_bytes() == before

    student_dir = tmp_path / 'student'
    assert s2.main(['--out', str(student_dir), '--mode', 'student']) == 0
    assert not (student_dir / 'report.json').exists()
    questions = (student_dir / 'questions.md').read_text(encoding='utf-8')
    assert '报告最优' in questions and 'k_error_v' not in questions
    assert (student_dir / 'config.json').read_text(encoding='utf-8') == (
        reference_dir / 'config.json'
    ).read_text(encoding='utf-8')


def test_digest_identity_changes_when_the_scenario_changes():
    base = s2.input_digest(CFG, TAUS, [0, 7])
    assert base == s2.input_digest(CFG, TAUS, [0, 7])
    assert s2.input_digest(s2.replace(CFG, dt_s=0.25), TAUS, [0, 7]) != base
    assert s2.input_digest(CFG, TAUS, [0, 8]) != base
