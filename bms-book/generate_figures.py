"""Recompute the book's scientific SVGs from explicit synthetic models."""
from pathlib import Path
import math
import importlib.util

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
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
fig.savefig(ROOT / "bms-book/assets/hppc-identifiability.svg", metadata={"Title": "HPPC 短窗口参数可辨识性", "Description": "两组相同起点、相同初始斜率的指数模型在短窗内接近，在长窗内分离。"})
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
fig.savefig(ROOT / "bms-book/assets/innovation-evidence.svg", metadata={"Title": "新息时间结构与摘要统计", "Description": "同一组512个标准化合成残差，排序前后直方图、RMS及平均NIS相同，一阶相关不同。"})
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
fig.savefig(ROOT / "bms-book/assets/kalman-observation-weight.svg", metadata={"Title": "卡尔曼增益与观测校正权重", "Description": "固定P和R的标量观测中K非单调，而KH随斜率平方单调增加。"})
plt.close(fig)
print("generated scientific SVG: kalman-observation-weight.svg")
