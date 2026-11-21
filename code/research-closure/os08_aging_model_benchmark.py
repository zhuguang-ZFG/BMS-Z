'''OS08 BLAST-Lite S8 capacity-aging model benchmark: textbook fade model (no BLAST-Lite dependency).

Contract (research doc OS08 / E08 + snapshot OS08 B01-B06 + R03):
This benchmark validates ALGORITHM SEMANTICS only, NOT calibration. Every parameter is
explicitly TEACHING-SYNTHETIC, not a real-cell measured fit. Two additive, separable losses:
    q_cal = k_cal * exp(-Ea/R * (1/T - 1/T_ref)) * exp(b*(SOC - SOC_ref)) * sqrt(t)
    q_cyc = k_cyc * integral(|I|/Q) dt       (equivalent full cycles, EFC)
    SOH   = 1 - q_cal - q_cyc
Calendar: Arrhenius temperature acceleration + SOC stress + sqrt(t) diffusion scaling.
Cycle: linear in throughput. Valid domain declared ONLY inside training window
(25-35 C, 0.20-0.80 SOC); outside (60 C, 1.00 SOC) flagged extrapolation=True with NO
accuracy assertion. R03 empirical closure stays pending: synthetic data cannot close it.
'''
import json
import platform
from pathlib import Path

import numpy as np

EVIDENCE = Path(__file__).parent / 'evidence' / 'os08-aging-model-benchmark.json'

SEED = 20261108
R_GAS = 8.314          # J/(mol K)
T_REF_K = 298.15       # 25 C
SOC_REF = 0.50

# TEACHING-SYNTHETIC parameters: chosen by hand for the demo, NOT fitted to any real cell.
K_CAL = 2.0e-4         # calendar coefficient per sqrt(hour) at reference
EA_J_PER_MOL = 35000.0 # Arrhenius activation energy (J/mol)
B_SOC = 1.2            # SOC stress exponent
K_CYC = 5.0e-5         # cycle coefficient per unit throughput (EFC)

VALID_T_C = (25.0, 35.0)
VALID_SOC = (0.20, 0.80)


def arrhenius_factor(t_kelvin):
    return np.exp(-EA_J_PER_MOL / R_GAS * (1.0 / t_kelvin - 1.0 / T_REF_K))


def soc_stress(soc):
    return np.exp(B_SOC * (soc - SOC_REF))


def calendar_loss(t_kelvin, soc, t_hours, k_cal=K_CAL, ea=EA_J_PER_MOL, b_soc=B_SOC):
    arr = np.exp(-ea / R_GAS * (1.0 / t_kelvin - 1.0 / T_REF_K))
    stress = np.exp(b_soc * (soc - SOC_REF))
    return k_cal * arr * stress * np.sqrt(t_hours)


def cycle_loss(throughput_efc, k_cyc=K_CYC):
    return k_cyc * throughput_efc


def in_valid_domain(t_celsius, soc):
    return VALID_T_C[0] <= t_celsius <= VALID_T_C[1] and VALID_SOC[0] <= soc <= VALID_SOC[1]


def bilinear(grid, xs, ys, x, y):
    '''Bilinear interpolation of grid[i,j] over ascending xs,ys (no scipy).'''
    ix = int(np.searchsorted(xs, x) - 1)
    iy = int(np.searchsorted(ys, y) - 1)
    ix = min(max(ix, 0), len(xs) - 2)
    iy = min(max(iy, 0), len(ys) - 2)
    tx = (x - xs[ix]) / (xs[ix + 1] - xs[ix])
    ty = (y - ys[iy]) / (ys[iy + 1] - ys[iy])
    g00, g01 = grid[ix, iy], grid[ix, iy + 1]
    g10, g11 = grid[ix + 1, iy], grid[ix + 1, iy + 1]
    return (g00 * (1.0 - tx) + g10 * tx) * (1.0 - ty) + (g01 * (1.0 - tx) + g11 * tx) * ty


def monotonicity_checks():
    cal_t = calendar_loss(np.array([283.15, 293.15, 298.15, 308.15, 318.15]), 0.60, 1000.0)
    cal_s = calendar_loss(298.15, np.array([0.20, 0.35, 0.50, 0.65, 0.80]), 1000.0)
    cal_h = calendar_loss(298.15, 0.60, np.array([1.0, 100.0, 10000.0, 1000000.0]))
    return {
        'calendar_vs_T_values': [float(x) for x in cal_t],
        'calendar_vs_SOC_values': [float(x) for x in cal_s],
        'calendar_vs_time_values': [float(x) for x in cal_h],
        'mono_T': bool(np.all(np.diff(cal_t) > 0)),
        'mono_SOC': bool(np.all(np.diff(cal_s) > 0)),
        'mono_t': bool(np.all(np.diff(cal_h) > 0)),
    }


def cycle_linearity_check():
    tp = np.array([0.0, 1.0, 2.5, 5.0, 10.0])
    q = cycle_loss(tp)
    ratios = q[1:] / tp[1:]
    return {
        'throughput': [float(x) for x in tp],
        'cycle_loss': [float(x) for x in q],
        'slope_per_efc': [float(x) for x in ratios],
        'linear_and_zero_intercept': bool(float(q[0]) == 0.0 and np.allclose(ratios, ratios[0], rtol=1e-12)),
    }


def fit_from_synthetic(rng):
    '''Recover each component parameter from synthetic truth with fixed-seed noise.'''
    n = 240
    t_c = rng.uniform(VALID_T_C[0], VALID_T_C[1], n)
    t_k = t_c + 273.15
    soc = rng.uniform(VALID_SOC[0], VALID_SOC[1], n)
    t_h = rng.uniform(50.0, 5000.0, n)
    q_cal_true = calendar_loss(t_k, soc, t_h)
    y = np.log(q_cal_true / np.sqrt(t_h))
    y_obs = y + rng.normal(0.0, 0.002, n)
    design = np.column_stack((np.ones(n), soc - SOC_REF, -(1.0 / t_k - 1.0 / T_REF_K)))
    coef, _, _, _ = np.linalg.lstsq(design, y_obs, rcond=None)
    ln_kcal, b_hat, ea_over_r = (float(c) for c in coef)
    k_cal_hat = float(np.exp(ln_kcal))
    ea_hat = ea_over_r * R_GAS
    q_cal_obs = np.exp(y_obs) * np.sqrt(t_h)
    q_cal_fit = calendar_loss(t_k, soc, t_h, k_cal_hat, ea_hat, b_hat)
    cal_resid = float(np.linalg.norm(q_cal_fit - q_cal_obs) / np.linalg.norm(q_cal_obs))

    m = 160
    throughput = rng.uniform(0.0, 40.0, m)
    t_h2 = rng.uniform(50.0, 5000.0, m)
    t_k2 = np.full(m, T_REF_K)
    soc2 = np.full(m, SOC_REF)
    q_cal2 = calendar_loss(t_k2, soc2, t_h2, k_cal_hat, ea_hat, b_hat)
    q_total_true = q_cal2 + cycle_loss(throughput)
    q_total_obs = q_total_true * (1.0 + rng.normal(0.0, 0.002, m))
    y_cyc = q_total_obs - q_cal2
    k_cyc_hat = float(np.dot(throughput, y_cyc) / np.dot(throughput, throughput))
    q_total_fit = q_cal2 + cycle_loss(throughput, k_cyc_hat)
    cyc_resid = float(np.linalg.norm(q_total_fit - q_total_obs) / np.linalg.norm(q_total_obs))

    params = {
        'k_cal': k_cal_hat,
        'ea_j_per_mol': ea_hat,
        'b_soc': b_hat,
        'k_cyc': k_cyc_hat,
    }
    rel_err = {
        'k_cal': abs(k_cal_hat - K_CAL) / K_CAL,
        'ea_j_per_mol': abs(ea_hat - EA_J_PER_MOL) / EA_J_PER_MOL,
        'b_soc': abs(b_hat - B_SOC) / B_SOC,
        'k_cyc': abs(k_cyc_hat - K_CYC) / K_CYC,
    }
    return {'params': params, 'rel_err': rel_err, 'cal_resid': cal_resid, 'cyc_resid': cyc_resid}


def domain_checks():
    tg = np.linspace(VALID_T_C[0], VALID_T_C[1], 41)
    sg = np.linspace(VALID_SOC[0], VALID_SOC[1], 41)
    t_grid_k = tg + 273.15
    tt, ss = np.meshgrid(t_grid_k, sg, indexing='ij')
    grid = arrhenius_factor(tt) * soc_stress(ss)

    t_in, s_in = 30.4, 0.55
    g_interp = float(bilinear(grid, tg, sg, t_in, s_in))
    g_true = float(arrhenius_factor(t_in + 273.15) * soc_stress(s_in))
    interp_rel_err = abs(g_interp - g_true) / g_true

    t_out, s_out = 60.0, 1.00
    out_in_domain = in_valid_domain(t_out, s_out)
    return {
        'training_window_t_c': list(VALID_T_C),
        'training_window_soc': list(VALID_SOC),
        'interior_point': {'t_c': t_in, 'soc': s_in},
        'interior_in_domain': bool(in_valid_domain(t_in, s_in)),
        'interpolated_rate_factor': g_interp,
        'analytic_rate_factor': g_true,
        'interp_rel_err': float(interp_rel_err),
        'exterior_point': {'t_c': t_out, 'soc': s_out},
        'exterior_in_domain': bool(out_in_domain),
        'extrapolation_flag': bool(not out_in_domain),
    }


def control_assumption_check():
    q_one = float(cycle_loss(10.0))
    q_split = float(4.0 * cycle_loss(2.5))
    cal_short = float(calendar_loss(T_REF_K, SOC_REF, 1000.0))
    cal_long = float(calendar_loss(T_REF_K, SOC_REF, 4000.0))
    return {
        'fixed_energy_throughput_cycle_equal': bool(np.isclose(q_one, q_split, rtol=1e-12)),
        'cycle_loss_one_block': q_one,
        'cycle_loss_four_blocks': q_split,
        'calendar_short_time': cal_short,
        'calendar_long_time': cal_long,
        'calendar_grows_with_wall_time': bool(cal_long > cal_short),
        'note': 'Fixed-energy control fixes cycle loss (throughput only); fixed-SOC-window control changes wall time so calendar loss differs. Cycle loss never depends on time-splitting.',
    }


def main():
    mono = monotonicity_checks()
    lin = cycle_linearity_check()
    fit = fit_from_synthetic(np.random.default_rng(SEED))
    fit_repeat = fit_from_synthetic(np.random.default_rng(SEED))
    reproducible = bool(fit == fit_repeat)
    dom = domain_checks()
    ctrl = control_assumption_check()

    residual_max = max(fit['cal_resid'], fit['cyc_resid'])
    param_err_max = max(fit['rel_err'].values())
    checks = {
        'calendar_monotonic_T': {'pass': mono['mono_T'], 'value': mono['calendar_vs_T_values'], 'note': 'Calendar loss strictly increases with temperature (Arrhenius) at fixed SOC,t.'},
        'calendar_monotonic_SOC': {'pass': mono['mono_SOC'], 'value': mono['calendar_vs_SOC_values'], 'note': 'Calendar loss strictly increases with SOC stress at fixed T,t.'},
        'calendar_monotonic_time': {'pass': mono['mono_t'], 'value': mono['calendar_vs_time_values'], 'note': 'Calendar loss strictly increases with elapsed time (sqrt(t)).'},
        'cycle_linear_throughput': {'pass': lin['linear_and_zero_intercept'], 'value': lin['slope_per_efc'], 'note': 'Cycle loss proportional to |I|/Q throughput, zero intercept.'},
        'separable_parameter_recovery': {'pass': bool(param_err_max < 0.01), 'value': {'max_rel_param_err': param_err_max, 'per_param': fit['rel_err']}, 'note': 'Calendar and cycle params each recovered from synthetic truth within 1%.'},
        'separable_regression_residual': {'pass': bool(residual_max < 0.01), 'value': {'calendar_rel_resid': fit['cal_resid'], 'cycle_rel_resid': fit['cyc_resid']}, 'note': 'Reconstructed two-component SOH matches noisy synthetic observations with <1% residual.'},
        'domain_interpolation_small': {'pass': bool(dom['interior_in_domain'] and dom['interp_rel_err'] < 0.01), 'value': {'interp_rel_err': dom['interp_rel_err'], 'interior_point': dom['interior_point']}, 'note': 'Inside training window bilinear interpolation matches analytic rate factor within 1%.'},
        'extrapolation_flagged_no_accuracy': {'pass': bool(dom['extrapolation_flag'] and not dom['exterior_in_domain']), 'value': {'exterior_point': dom['exterior_point'], 'extrapolation': dom['extrapolation_flag'], 'accuracy_asserted': False}, 'note': 'Outside (60C,1.00 SOC) flagged extrapolation=True; NO accuracy claim is made.'},
        'fixed_seed_reproducible': {'pass': reproducible, 'value': {'seed': SEED, 'identical_two_runs': reproducible}, 'note': 'default_rng(SEED) gives bit-identical recovered params across runs.'},
        'control_assumption_semantics': {'pass': bool(ctrl['fixed_energy_throughput_cycle_equal'] and ctrl['calendar_grows_with_wall_time']), 'value': ctrl, 'note': 'Fixed-energy throughput vs fixed-SOC-window assumptions distinguished; cycle loss is time-split-invariant.'},
    }

    result = {
        'source_id': 'OS08',
        'benchmark': 'S8 capacity-aging model: Arrhenius+SOC+sqrt(t) calendar and throughput cycle, separable regression, conditional valid domain (no BLAST-Lite dependency)',
        'python': platform.python_version(),
        'seed': SEED,
        'parameter_provenance': 'TEACHING-SYNTHETIC: hand-chosen demo constants, NOT fitted to any real cell. Synthetic data validates algorithm semantics, not calibration.',
        'model': {
            'calendar': 'q_cal = k_cal*exp(-Ea/R*(1/T-1/Tref))*exp(b*(SOC-SOCref))*sqrt(t_hours)',
            'cycle': 'q_cyc = k_cyc*integral(|I|/Q)dt (EFC)',
            'soh': 'SOH = 1 - q_cal - q_cyc',
            'synthetic_true_params': {'k_cal': K_CAL, 'ea_j_per_mol': EA_J_PER_MOL, 'b_soc': B_SOC, 'k_cyc': K_CYC},
            'units': {'T': 'K (Tref=298.15K=25C)', 't': 'hours', 'throughput': 'EFC', 'loss': 'capacity fraction'},
        },
        'recovered_params': fit['params'],
        'checks': checks,
        'extrapolation_limit': {
            'exterior_point': dom['exterior_point'],
            'extrapolation': dom['extrapolation_flag'],
            'accuracy_asserted': False,
            'registered_as': 'extrapolation-limit evidence: domain boundary only, no precision claim',
        },
        'r03_empirical_status': {'status': 'pending', 'note': 'No external aging data; synthetic benchmark cannot close R03 empirical validation. Expected-life is qualitative only.'},
        'all_pass': bool(all(c['pass'] for c in checks.values())),
    }

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'all_pass': result['all_pass'], 'checks': {k: v['pass'] for k, v in checks.items()}, 'recovered_params': fit['params']}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
