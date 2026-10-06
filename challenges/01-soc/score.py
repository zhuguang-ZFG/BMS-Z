"""第 1 期仿真擂台：固定种子的合成工况，给纯安时积分打一个 RMSE 基线。

复用 code/soc 的 Thevenin 模型和三种教学估算器，不改那些文件。
数字是仿真结果，不是电芯实测。

读者把自己的类交进来：

    python3 challenges/01-soc/score.py --estimator challenges/01-soc/my_estimator.py:MyEstimator

类不要参数。``step(current_a, v_meas, dt_s)`` 返回这一步结束时的 SOC。
充电电流为正，单位 A、V、s。不要在 step 里读真值。

档位按严格小于来判，阈值就是本脚本里仓库估算器的 RMSE：

- 小于纯安时积分 → 胜过基线
- 再小于仓库 Thevenin+EKF → 胜过仓库 EKF
- 更吵的那一档用同一条电流，只把传感器噪声加大，阈值同样现算
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path

import numpy as np

# code/soc 里的模块互相用「同目录 import」。先放进路径，再按原样导入。
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code" / "soc"))

from cell_model import TheveninCell  # noqa: E402
from estimators import CoulombOnly, CoulombWithResets, EKFEstimator  # noqa: E402

SEED = 20261006
DT_S = 1.0
N_STEPS = 5000
Q_TRUE_AH = 10.0
Q_ASSUMED_AH = 9.5
SOC0_TRUE = 0.80
SOC0_EST = 0.70
I_OFFSET_A = 0.002
I_NOISE_A = 0.02
V_NOISE_V = 0.005
R0, R1, C1 = 0.020, 0.015, 3000.0
BASELINE_NAME = "纯安时积分"
REFERENCE_NAME = "Thevenin+EKF"

# 更吵档：电流工况仍用 SEED，只换噪声种子和标准差。阈值跑完才知道。
NOISY_NOISE_SEED = 20261102
NOISY_I_NOISE_A = 0.08
NOISY_V_NOISE_V = 0.020

TIER_EKF = "胜过仓库 EKF"
TIER_BASELINE = "胜过基线"
TIER_NONE = "未胜过基线"


def command_current(n_steps: int = N_STEPS, dt_s: float = DT_S, seed: int = SEED) -> np.ndarray:
    """合成电流 (A)：静置 → 放电加脉冲 → 长静置 → 恒流充 → 指数收尾。"""
    rng = np.random.default_rng(seed)
    t = np.arange(n_steps) * dt_s
    current = np.zeros(n_steps)
    discharge = (t >= 300.0) & (t < 1800.0)
    current[discharge] = -1.5
    pulse = discharge & (rng.random(n_steps) < 0.04)
    extra = rng.uniform(0.5, 2.0, int(pulse.sum()))
    current[pulse] = -1.5 - extra
    charge = (t >= 2800.0) & (t < 4600.0)
    current[charge] = 2.0
    taper = t >= 4600.0
    current[taper] = 2.0 * np.exp(-(t[taper] - 4600.0) / 200.0)
    return current


def build_estimators() -> dict:
    return {
        BASELINE_NAME: CoulombOnly(SOC0_EST, Q_ASSUMED_AH),
        "积分+校准点": CoulombWithResets(SOC0_EST, Q_ASSUMED_AH),
        REFERENCE_NAME: EKFEstimator(SOC0_EST, Q_ASSUMED_AH, R0, R1, C1),
    }


def simulate(
    seed: int = SEED,
    i_noise_a: float = I_NOISE_A,
    v_noise_v: float = V_NOISE_V,
    noise_seed: int | None = None,
    estimators: dict | None = None,
):
    """返回测量电流、测量电压、真值 SOC，以及各估算器的 SOC。

    noise_seed 缺省时等于 seed，公开题和改动前的随机序列一致。
    """
    if noise_seed is None:
        noise_seed = seed
    rng = np.random.default_rng(noise_seed + 1)
    cell = TheveninCell(Q_TRUE_AH, R0, R1, C1, soc0=SOC0_TRUE)
    i_cmd = command_current(seed=seed)
    if estimators is None:
        estimators = build_estimators()
    i_meas = np.empty(N_STEPS)
    v_meas = np.empty(N_STEPS)
    soc_true = np.empty(N_STEPS)
    soc_est = {name: np.empty(N_STEPS) for name in estimators}
    for k in range(N_STEPS):
        v_true = cell.step(float(i_cmd[k]), DT_S)
        soc_true[k] = cell.soc
        i_meas[k] = i_cmd[k] + I_OFFSET_A + rng.normal(0.0, i_noise_a)
        v_meas[k] = v_true + rng.normal(0.0, v_noise_v)
        for name, est in estimators.items():
            soc_est[name][k] = est.step(float(i_meas[k]), float(v_meas[k]), DT_S)
    return i_meas, v_meas, soc_true, soc_est


def rmse(estimate: np.ndarray, truth: np.ndarray) -> float:
    err = np.asarray(estimate, dtype=float) - np.asarray(truth, dtype=float)
    return float(np.sqrt(np.mean(err ** 2)))


def baseline_table(seed: int = SEED) -> dict[str, float]:
    _i, _v, soc_true, soc_est = simulate(seed)
    return {name: rmse(est, soc_true) for name, est in soc_est.items()}


def noisy_table() -> dict[str, float]:
    """同一条公开电流，电流噪声 0.08 A、电压噪声 0.020 V。"""
    _i, _v, soc_true, soc_est = simulate(
        seed=SEED,
        i_noise_a=NOISY_I_NOISE_A,
        v_noise_v=NOISY_V_NOISE_V,
        noise_seed=NOISY_NOISE_SEED,
    )
    return {name: rmse(est, soc_true) for name, est in soc_est.items()}


def tier_name(value: float, baseline: float, reference: float) -> str:
    """严格小于才算胜过。等于仓库 EKF 只落在「胜过基线」，如果它也小于基线。"""
    if value < reference:
        return TIER_EKF
    if value < baseline:
        return TIER_BASELINE
    return TIER_NONE


def load_estimator_class(spec: str):
    """``文件.py:类名`` 或 ``模块名:类名``。类的构造函数不要参数。

    按最后一个冒号切：Windows 的绝对路径自带盘符冒号（``D:\\tmp\\x.py:Cls``），
    按冒号个数校验会把 Windows 读者全部挡在门外，而 CI 的 Linux 路径测不出来。
    """
    mod_part, sep, class_name = spec.rpartition(":")
    if not sep or not mod_part or not class_name:
        raise ValueError("用法：--estimator 文件.py:类名")
    path = Path(mod_part)
    if path.suffix == ".py":
        if not path.is_file():
            raise FileNotFoundError(path)
        mod_name = "arena_plugin_" + path.stem
        loaded = importlib.util.spec_from_file_location(mod_name, path.resolve())
        if loaded is None or loaded.loader is None:
            raise ImportError(f"无法加载 {path}")
        module = importlib.util.module_from_spec(loaded)
        loaded.loader.exec_module(module)
    else:
        module = importlib.import_module(mod_part)
    cls = getattr(module, class_name)
    return cls


def score_estimator(spec: str) -> dict[str, dict[str, float | str]]:
    """在公开档和更吵档上各新建一个实例，避免状态串到下一档。"""
    cls = load_estimator_class(spec)
    return {
        "public": _score_one(cls, baseline_table(), noisy=False),
        "noisy": _score_one(cls, noisy_table(), noisy=True),
    }


def _score_one(cls, table: dict[str, float], noisy: bool) -> dict[str, float | str]:
    if noisy:
        _i, _v, soc_true, soc_est = simulate(
            seed=SEED,
            i_noise_a=NOISY_I_NOISE_A,
            v_noise_v=NOISY_V_NOISE_V,
            noise_seed=NOISY_NOISE_SEED,
            estimators={"读者": cls()},
        )
    else:
        _i, _v, soc_true, soc_est = simulate(estimators={"读者": cls()})
    value = rmse(soc_est["读者"], soc_true)
    baseline = table[BASELINE_NAME]
    reference = table[REFERENCE_NAME]
    return {
        "rmse": value,
        "baseline": baseline,
        "reference": reference,
        "tier": tier_name(value, baseline, reference),
    }


def _print_table(title: str, table: dict[str, float]) -> None:
    print(title)
    print(f"{'估算器':<16}{'RMSE':>12}")
    print("-" * 28)
    baseline = table[BASELINE_NAME]
    reference = table[REFERENCE_NAME]
    for name, value in table.items():
        if name == BASELINE_NAME:
            mark = "  ← 基线，要胜过它"
        elif name == REFERENCE_NAME:
            mark = "  ← 仓库 EKF，第二档"
        else:
            mark = ""
        print(f"{name:<16}{value:>11.6%}{mark}")
    print(
        f"档位阈值｜胜过基线：RMSE < {baseline:.6%}｜"
        f"胜过仓库 EKF：RMSE < {reference:.6%}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="第 1 期 SOC 仿真擂台")
    parser.add_argument(
        "--estimator",
        help="读者的类，例如 challenges/01-soc/my_estimator.py:MyEstimator",
    )
    args = parser.parse_args()
    public = baseline_table()
    noisy = noisy_table()
    print(
        f"仿真结果｜种子 {SEED}｜{N_STEPS} 步 × {DT_S:.0f}s｜"
        f"容量假定 {Q_ASSUMED_AH}Ah（模型 {Q_TRUE_AH}Ah）｜"
        f"初始 SOC {SOC0_EST}（模型 {SOC0_TRUE}）"
    )
    _print_table("公开档", public)
    print(
        f"更吵档｜同一条电流｜噪声种子 {NOISY_NOISE_SEED}｜"
        f"电流噪声 {NOISY_I_NOISE_A} A｜电压噪声 {NOISY_V_NOISE_V} V"
    )
    _print_table("更吵档", noisy)
    if args.estimator:
        scored = score_estimator(args.estimator)
        print(f"读者｜{args.estimator}")
        for label, row in (("公开档", scored["public"]), ("更吵档", scored["noisy"])):
            print(f"  {label}  RMSE {row['rmse']:.6%}  {row['tier']}")
    print("状态：进行中。榜单只收这份合成工况上的仿真 RMSE，不收电芯实测。")
    print("第 1 期：2026-10-06 开始，大约 4 周，2026-11-02 结束。")


if __name__ == "__main__":
    main()
