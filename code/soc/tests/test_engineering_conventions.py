"""新读者放电正与旧充电正接口在同一物理轨迹上的等价性。"""
import math

import numpy as np
import pytest

from cell_model import TheveninCell, ocv
from estimators import CoulombOnly, EKFEstimator
from real_data import cumulative_ah


@pytest.mark.parametrize("discharge_current", [2.0, -2.0])
def test_charge_and_discharge_match_independent_analytic_solution(discharge_current):
    q, r0, r1, c1, soc0, duration = 2.0, 0.020, 0.015, 3000.0, 0.6, 10.0
    legacy = TheveninCell(q, r0, r1, c1, soc0)
    tau = r1 * c1
    expected_soc = soc0 - discharge_current * duration / (3600 * q)
    expected_vp = r1 * discharge_current * -math.expm1(-duration / tau)
    before_state = legacy.soc, legacy.u_rc
    # 同一状态两侧的跳变只来自欧姆项，读电压不推进状态。
    jump_v = legacy.terminal_voltage(-discharge_current) - legacy.terminal_voltage(0)
    assert jump_v == pytest.approx(-r0 * discharge_current, abs=1e-14)
    assert (legacy.soc, legacy.u_rc) == before_state

    returned_voltage = legacy.step(-discharge_current, duration)
    assert legacy.soc == pytest.approx(expected_soc, abs=1e-14)
    assert -legacy.u_rc == pytest.approx(expected_vp, abs=1e-14)
    assert abs(expected_vp * 1000) == pytest.approx(5.977877912495758)
    assert abs((expected_soc - soc0) * 100) == pytest.approx(0.2777777777777778)
    # step 返回区间末端状态下的电压，不能当作起点电压。
    assert returned_voltage == pytest.approx(float(ocv(expected_soc)) - r0 * discharge_current - expected_vp)


def test_current_reversal_keeps_signed_polarization_memory_and_voltage_components():
    legacy = TheveninCell(2.0, 0.020, 0.015, 3000.0, 0.6)
    expected_soc, expected_vp = 0.6, 0.010
    legacy.u_rc = -expected_vp
    # 首段反向充电仍留正压降；abs(u_rc) 会在后续极化翻转时出错。
    for discharge_current, dt in [(-2.0, 0.5), (0.0, 3.0), (2.0, 10.0), (-2.0, 90.0)]:
        a = math.exp(-dt / 45.0)
        expected_soc -= discharge_current * dt / (3600 * 2.0)
        expected_vp = a * expected_vp + 0.015 * (1 - a) * discharge_current
        voltage = legacy.step(-discharge_current, dt)
        assert (legacy.soc, -legacy.u_rc) == pytest.approx((expected_soc, expected_vp), abs=1e-14)
        new_components = (float(ocv(expected_soc)), -0.020 * discharge_current, -expected_vp)
        old_components = (float(ocv(legacy.soc)), 0.020 * -discharge_current, legacy.u_rc)
        assert old_components == pytest.approx(new_components, abs=1e-14)
        assert voltage == pytest.approx(sum(new_components), abs=1e-14)
    assert expected_vp < 0  # 极化能反号，不能取绝对值映射。


@pytest.mark.parametrize("discharge_current", [2.0, -2.0])
def test_integrator_and_ekf_use_same_legacy_input_mapping(discharge_current):
    dt, q, soc0, vp0 = 10.0, 2.0, 0.6, 0.005
    a = math.exp(-dt / 45.0)
    expected_soc = soc0 - discharge_current * dt / (3600 * q)
    expected_vp = a * vp0 + 0.015 * (1 - a) * discharge_current
    voltage = float(ocv(expected_soc)) - 0.020 * discharge_current - expected_vp
    coulomb = CoulombOnly(soc0, q)
    ekf = EKFEstimator(soc0, q, 0.020, 0.015, 3000.0)
    ekf.x[1] = -vp0
    assert coulomb.step(-discharge_current, voltage, dt) == pytest.approx(expected_soc)
    assert ekf.step(-discharge_current, voltage, dt) == pytest.approx(expected_soc)
    assert -ekf.x[1] == pytest.approx(expected_vp)
    assert ekf.last_innovation_v == pytest.approx(0.0, abs=1e-14)


def test_rw3_style_irregular_integral_adapts_sign_once_and_keeps_pp_scale():
    time = np.array([0.0, 1.0, 4.0, 8.0])
    discharge_current = np.array([1.0, 3.0, -1.0, -2.0])
    legacy_charge_ah = cumulative_ah(dict(time_s=time, current_a=-discharge_current))
    # 独立手算每段放电电量：2、3、-6 A·s，总计 -1 A·s。
    expected_discharge_ah = np.array([0.0, 2.0, 5.0, -1.0]) / 3600
    assert legacy_charge_ah == pytest.approx(-expected_discharge_ah)
    new_soc = 0.6 - expected_discharge_ah / 2.0
    old_soc = 0.6 + legacy_charge_ah / 2.0
    assert old_soc == pytest.approx(new_soc)
    assert (old_soc[1] - old_soc[0]) * 100 == pytest.approx(-2 / 7200 * 100)
