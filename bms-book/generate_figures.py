"""Recompute the book's scientific SVGs from explicit synthetic models."""
from pathlib import Path
import math
import importlib.util
from io import StringIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def save_figure(figure, filename, metadata):
    """Normalize generated path whitespace so checked-in SVGs pass git diff checks."""
    buffer = StringIO()
    figure.savefig(buffer, format="svg", metadata=metadata)
    svg = "\n".join(line.rstrip() for line in buffer.getvalue().splitlines()) + "\n"
    (ROOT / "bms-book/assets" / filename).write_text(svg, encoding="utf-8")


plt.rcParams.update({"font.family": "Microsoft YaHei", "svg.fonttype": "path", "font.size": 11})
t = np.linspace(0, 120, 601)
model_a = 3.75 + 0.012 * np.exp(-t / 30)
model_b = 3.738 + 0.024 * np.exp(-t / 60)
assert math.isclose(3.75 + 0.012, 3.738 + 0.024)
assert math.isclose(0.012 / 30, 0.024 / 60)
fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), gridspec_kw={"width_ratios": [2.1, 1]}, facecolor="#f8fafc")
for ax in axes:
    ax.set_facecolor("#ffffff")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
axes[0].plot(t, model_a * 1000, color="#2563eb", linewidth=2.2, label="A：K=3.750 V，τ=30 s")
axes[0].plot(t, model_b * 1000, color="#0f766e", linewidth=2.2, linestyle="--", label="B：K=3.738 V，τ=60 s")
axes[0].axvspan(0, 5, color="#f59e0b", alpha=0.17, label="短窗 0–5 s")
axes[0].set(xlabel="撤流后的时间 / s", ylabel="端电压 / mV", title="延长窗口，曲率才逐渐分离")
axes[0].legend(loc="upper right", fontsize=9)
short = t <= 5
axes[1].plot(t[short], model_a[short] * 1000, color="#2563eb", linewidth=2.2)
axes[1].plot(t[short], model_b[short] * 1000, color="#0f766e", linewidth=2.2, linestyle="--")
axes[1].set(xlabel="时间 / s", title="短窗放大：两条曲线接近")
axes[1].text(0.04, 0.08, "相同起点：3762 mV\n相同初始斜率：−0.4 mV/s", transform=axes[1].transAxes, fontsize=9)
fig.suptitle("短窗口看得到起点与斜率，难以分别辨识 K、A、τ", fontsize=15, fontweight="bold")
fig.text(0.08, 0.025, "教学合成曲线 · 无噪声 · A 幅值 12 mV，B 幅值 24 mV · 两组参数不是同一电芯的真值声明", fontsize=9, color="#475569")
fig.tight_layout(rect=(0, 0.06, 1, 0.94))
save_figure(fig, "hppc-identifiability.svg", {"Title": "HPPC 短窗口参数可辨识性", "Description": "两组相同起点、相同初始斜率的指数模型在短窗内接近，在长窗内分离。"})
print("generated scientific SVG: hppc-identifiability.svg")
plt.close(fig)

spec = importlib.util.spec_from_file_location("estimator_evidence", ROOT / "bms-book/code/estimator_evidence.py")
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)
shuffled, ordered = evidence.residual_sequences()

fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), facecolor="#f8fafc")
for ax in axes:
    ax.set_facecolor("white")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
axes[0].plot(shuffled, linewidth=0.8, color="#2563eb", label="随机顺序")
axes[0].plot(ordered, linewidth=2.2, color="#be123c", label="按残差大小排序")
axes[0].set(xlabel="样本编号", ylabel="标准化新息", title="值相同，时间顺序不同")
axes[0].legend(fontsize=9)
bins = np.linspace(min(shuffled), max(shuffled), 24)
axes[1].hist(shuffled, bins=bins, histtype="stepfilled", alpha=0.20, color="#2563eb", label="随机顺序")
axes[1].hist(ordered, bins=bins, histtype="step", linewidth=1.8, color="#be123c", label="排序后：完全重合")
axes[1].set(xlabel="标准化新息", ylabel="样本数", title="直方图完全相同")
axes[1].legend(fontsize=9)
fig.suptitle("相同 RMS 与平均 NIS，未必具有相同诊断意义", fontsize=15, fontweight="bold")
fig.text(0.08, 0.025, f"教学合成 · 512 个样本 · RMS = 1，平均 NIS = 1 · 一阶相关：{evidence.lag_one(shuffled):.4f} / {evidence.lag_one(ordered):.4f}", fontsize=10, color="#475569")
fig.tight_layout(rect=(0, 0.07, 1, 0.94))
save_figure(fig, "innovation-evidence.svg", {"Title": "新息时间结构与摘要统计", "Description": "同一组512个标准化合成残差，排序前后直方图、RMS及平均NIS相同，一阶相关不同。"})
plt.close(fig)
print("generated scientific SVG: innovation-evidence.svg")

slopes = np.logspace(-3, 1, 400)
gains = np.array([evidence.scalar_update(float(slope), 0.05 ** 2, 0.005 ** 2) for slope in slopes])
fig, axes = plt.subplots(1, 2, figsize=(10, 4.0), facecolor="#f8fafc")
for ax in axes:
    ax.set_facecolor("white")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2, which="both")
    ax.set_xscale("log")
    ax.set_xlabel("观测斜率 H / (V/SOC)")
axes[0].plot(slopes, gains[:, 0], color="#2563eb", linewidth=2)
axes[0].set(ylabel="增益 K / (SOC/V)", title="有单位的 K：先增后减")
axes[1].plot(slopes, gains[:, 1], color="#0f766e", linewidth=2)
axes[1].set(ylabel="观测校正比例 KH（无量纲）", title="KH：斜率变小，权重下降", ylim=(0, 1.04))
for slope, color in [(0.8, "#2563eb"), (0.075, "#be123c")]:
    gain, weight = evidence.scalar_update(slope, 0.05 ** 2, 0.005 ** 2)
    axes[0].scatter([slope], [gain], color=color, zorder=3)
    axes[1].scatter([slope], [weight], color=color, zorder=3)
fig.suptitle("平台更平时，比较观测权重，不能只比较 K 的大小", fontsize=15, fontweight="bold")
fig.text(0.08, 0.025, "标量局部线性模型 · SOC 先验标准差 5 个百分点 · 电压标准差 5 mV · 不含 RC 状态与交叉协方差", fontsize=9, color="#475569")
fig.tight_layout(rect=(0, 0.07, 1, 0.94))
save_figure(fig, "kalman-observation-weight.svg", {"Title": "卡尔曼增益与观测校正权重", "Description": "固定P和R的标量观测中K非单调，而KH随斜率平方单调增加。"})
plt.close(fig)
print("generated scientific SVG: kalman-observation-weight.svg")


# --- 图 28-1：一条 HPPC 脉冲的六步解剖 -----------------------------------
# 仿真源就是 28 章正文与表 28-1 使用的 bms-book/code/hppc_fit.py：
# 合成电芯 R0=33 mΩ、R1=16 mΩ、C1=2200 F（τ=35.2 s），3 A × 10 s 脉冲，
# 电压噪声 σ=1 mV，seed=7——图上每个数字都能在正文或表 28-1 里复核。
_hppc_spec = importlib.util.spec_from_file_location(
    "hppc_fit", ROOT / "bms-book/code/hppc_fit.py"
)
hppc_fit = importlib.util.module_from_spec(_hppc_spec)
_hppc_spec.loader.exec_module(hppc_fit)

t_hp, v_hp, _i_hp, n_pre, n_pulse = hppc_fit.simulate_pulse()
dt_hp = float(t_hp[1] - t_hp[0])
t_pulse0 = n_pre * dt_hp                 # 60 s
t_pulse1 = (n_pre + n_pulse) * dt_hp     # 70 s
drop_mv = (v_hp - 3.75) * 1000.0         # 相对 OCV 的压降（放电为正）
r0_hp, r1_hp, c1_hp = 0.033, 0.016, 2200.0
tau_hp = r1_hp * c1_hp                   # 35.2 s
jump_mv = 3.0 * r0_hp * 1000.0           # 99.0 mV
full_mv = 3.0 * (r0_hp + r1_hp) * 1000.0  # 147.0 mV
climb_mv = 3.0 * r1_hp * (1.0 - math.exp(-10.0 / tau_hp)) * 1000.0  # 11.9 mV
assert abs(jump_mv - 99.0) < 1e-9 and abs(tau_hp - 35.2) < 1e-9
# 无噪声理想曲线：同一参数的解析解，叠在含噪仿真上对照。
ideal_mv = np.where(
    t_hp < t_pulse0, 0.0,
    np.where(
        t_hp <= t_pulse1,
        jump_mv + 3.0 * r1_hp * (1.0 - np.exp(-(t_hp - t_pulse0) / tau_hp)) * 1000.0,
        climb_mv * np.exp(-(t_hp - t_pulse1) / tau_hp),
    ),
)

fig = plt.figure(figsize=(10, 5.4), facecolor="#f8fafc")
steps_ax = fig.add_axes((0.06, 0.878, 0.9, 0.068))
steps_ax.axis("off")
steps = [
    ("① 预静置", "#64748b"), ("② 脉冲 +3 A·10 s", "#7c3aed"), ("③ 欧姆跳变", "#be123c"),
    ("④ 极化爬升", "#0f766e"), ("⑤ 撤流回弹", "#b45309"), ("⑥ 松弛趋渐近线", "#475569"),
]
for idx, (label, color) in enumerate(steps):
    x0 = 0.01 + idx * 0.166
    steps_ax.add_patch(matplotlib.patches.FancyBboxPatch(
        (x0, 0.18), 0.145, 0.64, boxstyle="round,pad=0.012",
        facecolor=color, edgecolor="none", alpha=0.14,
        transform=steps_ax.transAxes, clip_on=False))
    steps_ax.text(x0 + 0.0725, 0.5, label, ha="center", va="center",
                  fontsize=10.5, color=color, fontweight="bold",
                  transform=steps_ax.transAxes)
    if idx < 5:
        steps_ax.annotate("", xy=(x0 + 0.161, 0.5), xytext=(x0 + 0.148, 0.5),
                          xycoords=steps_ax.transAxes, textcoords=steps_ax.transAxes,
                          arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.2))

ax = fig.add_axes((0.075, 0.135, 0.885, 0.70))
ax.set_facecolor("#ffffff")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=0.2)
ax.axvspan(t_pulse0, t_pulse1, color="#7c3aed", alpha=0.08)
ax.axvspan(t_pulse1, t_pulse1 + 40, color="#e11d48", alpha=0.07)
ax.plot(t_hp, drop_mv, color="#334155", linewidth=1.1, label="仿真测量（σ=1 mV）")
ax.plot(t_hp, ideal_mv, color="#0f766e", linewidth=2.0, linestyle="--", label="无噪声模型（同一参数）")
ax.axhline(jump_mv, color="#be123c", linewidth=1.1, linestyle=":", alpha=0.8)
ax.axhline(full_mv, color="#7c3aed", linewidth=1.1, linestyle=":", alpha=0.8)
ax.text(112, jump_mv + 2.5, "I·R0 = 3 A × 33 mΩ = 99.0 mV", color="#be123c", fontsize=10)
ax.text(2, 152, "I·(R0+R1) = 147 mV（满幅）", color="#7c3aed", fontsize=10)

badges = [
    ("①", 28, 6, "#64748b"), ("②", t_pulse0 - 4, 26, "#7c3aed"),
    ("③", t_pulse0 + 3.5, 62, "#be123c"), ("④", t_pulse0 + 4.0, 118, "#0f766e"),
    ("⑤", t_pulse1 + 3.5, 62, "#b45309"), ("⑥", 152, 8, "#475569"),
]
for mark, x, y, color in badges:
    ax.text(x, y, mark, fontsize=15, color=color, fontweight="bold", ha="center", va="center",
            bbox=dict(boxstyle="circle,pad=0.25", facecolor="#ffffff", edgecolor=color, linewidth=1.4))

ax.annotate("跳变窗均值差 97.8 mV → R0 估值 32.6 mΩ（真值 33.0，差在噪声）",
            xy=(t_pulse0 + 0.4, jump_mv - 3), xytext=(2, 132),
            fontsize=10, color="#0f172a",
            arrowprops=dict(arrowstyle="->", color="#334155", lw=1.2))
ax.annotate(f"极化只充到 24.8%：爬升 {climb_mv:.1f} mV",
            xy=(t_pulse1 - 0.6, jump_mv + climb_mv), xytext=(80, 127),
            fontsize=10, color="#0f766e",
            arrowprops=dict(arrowstyle="->", color="#0f766e", lw=1.2))
ax.annotate("", xy=(t_pulse1, 30), xytext=(t_pulse1 + 40, 30),
            arrowprops=dict(arrowstyle="<->", color="#e11d48", lw=1.4))
ax.text(t_pulse1 + 20, 36, "40 s 窗 = 1.1τ", color="#e11d48", fontsize=10.5,
        fontweight="bold", ha="center")
ax.text(t_pulse1 + 33, 14, "窗内 R1 误差 17.5%；满窗 120 s = 3.4τ 时 0.44%",
        color="#9f1239", fontsize=9.5, ha="center")
ax.axvline(t_pulse1 + tau_hp, color="#475569", linewidth=1.1, linestyle=":", alpha=0.8)
ax.text(t_pulse1 + tau_hp + 1.5, 60, "撤流后 1τ = 35.2 s", color="#475569",
        fontsize=9.5, rotation=90, va="center")

ax.set(xlim=(0, 190), ylim=(-6, 168), xlabel="时间 / s", ylabel="相对 OCV 的压降 / mV")
ax.legend(loc="center right", fontsize=9.5, framealpha=0.9)
fig.suptitle("一条 HPPC 脉冲的六步解剖：仿真曲线按步骤读", fontsize=15, fontweight="bold", y=0.985)
fig.text(0.075, 0.025,
         "仿真源 bms-book/code/hppc_fit.py（seed=7）· 合成电芯 R0=33 mΩ、R1=16 mΩ、C1=2200 F · "
         "3 A × 10 s · 噪声 σ=1 mV",
         fontsize=9, color="#475569")
save_figure(fig, "hppc-pulse.svg", {
    "Title": "HPPC 脉冲六步解剖",
    "Description": "仿真电流脉冲下电压的六阶段响应：预静置、脉冲注入、欧姆跳变、极化爬升、撤流回弹、松弛趋渐近线；含噪测量与无噪声模型对照。",
})
plt.close(fig)
print("generated scientific SVG: hppc-pulse.svg")
