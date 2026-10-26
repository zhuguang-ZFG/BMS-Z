"""Recompute the book's scientific SVGs from explicit synthetic models."""
from pathlib import Path
import math
import importlib.util
import sys
from decimal import ROUND_HALF_UP, Decimal
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

# ---------------------------------------------------------------------------
# 图 10-1：OCV 四项叠出一条曲线（数据源：code/soc/cell_model.py 的 ocv() / docv_dsoc()）
_cell_spec = importlib.util.spec_from_file_location("cell_model", ROOT / "code/soc/cell_model.py")
cell_model = importlib.util.module_from_spec(_cell_spec)
_cell_spec.loader.exec_module(cell_model)

soc = np.linspace(0.0, 1.0, 801)
term_base = np.full_like(soc, 3.2)
term_slope = 0.8 * soc
term_low = 0.20 * np.tanh((soc - 0.05) * 30.0)
term_high = 0.05 * np.tanh((soc - 0.90) * 15.0)
total = cell_model.ocv(soc)
assert np.allclose(term_base + term_slope + term_low + term_high, total)
assert round(float(cell_model.ocv(0.5)), 4) == 3.75 and round(float(cell_model.ocv(0.0)), 4) == 2.969
slope_low, slope_mid = float(cell_model.docv_dsoc(0.05)), float(cell_model.docv_dsoc(0.5))
assert round(slope_low, 3) == 6.8 and round(slope_mid, 3) == 0.8
noise_v = 0.005
# 书内（10.2 交互实验读数）用印出来的斜率（6.800 / 0.800）按四舍五入换算：0.625 → 0.63。
# docv_dsoc(0.5) 带 tanh 尾项略大于 0.8，直接除会落在 0.6249…，所以先取印刷精度，再显式 ROUND_HALF_UP。
def _pp(slope: float) -> str:
    printed = Decimal(f"{slope:.3f}")
    return str((Decimal(str(noise_v)) / printed * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


pp_low, pp_mid = _pp(slope_low), _pp(slope_mid)  # "0.07" / "0.63" 个百分点
assert (pp_low, pp_mid) == ("0.07", "0.63")

fig = plt.figure(figsize=(10, 5.8), facecolor="#f8fafc")
steps_ax = fig.add_axes((0.06, 0.865, 0.9, 0.068))
steps_ax.axis("off")
steps = [
    ("① 基准 3.2 V", "#64748b"), ("② + 中段斜率 0.8·soc", "#2563eb"),
    ("③ + 低端 tanh（抬头）", "#be123c"), ("④ + 高端 tanh = OCV", "#0f766e"),
]
for idx, (label, color) in enumerate(steps):
    x0 = 0.01 + idx * 0.25
    steps_ax.add_patch(matplotlib.patches.FancyBboxPatch(
        (x0, 0.18), 0.225, 0.64, boxstyle="round,pad=0.012",
        facecolor=color, edgecolor="none", alpha=0.14,
        transform=steps_ax.transAxes, clip_on=False))
    steps_ax.text(x0 + 0.1125, 0.5, label, ha="center", va="center",
                  fontsize=10.5, color=color, fontweight="bold", transform=steps_ax.transAxes)
    if idx < 3:
        steps_ax.annotate("", xy=(x0 + 0.245, 0.5), xytext=(x0 + 0.228, 0.5),
                          xycoords=steps_ax.transAxes, textcoords=steps_ax.transAxes,
                          arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.2))

# 左：一项一项叠上去
ax = fig.add_axes((0.07, 0.13, 0.52, 0.69))
ax.set_facecolor("#ffffff")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=0.2)
ax.plot(soc, term_base, color="#64748b", linewidth=1.6, linestyle=":")
ax.plot(soc, term_base + term_slope, color="#2563eb", linewidth=1.6, linestyle="--")
ax.plot(soc, term_base + term_slope + term_low, color="#be123c", linewidth=1.6, linestyle="-.")
ax.plot(soc, total, color="#0f766e", linewidth=3.0)
ax.fill_between(soc, term_base + term_slope + term_low, total, color="#0f766e", alpha=0.10)
for mark, x, y, color in [("①", 0.80, 3.155, "#64748b"), ("②", 0.62, 3.62, "#2563eb"),
                          ("③", 0.13, 3.56, "#be123c"), ("④", 0.965, 4.33, "#0f766e")]:
    ax.text(x, y, mark, fontsize=14, color=color, fontweight="bold", ha="center", va="center",
            bbox=dict(boxstyle="circle,pad=0.22", facecolor="#ffffff", edgecolor=color, linewidth=1.3))
ax.plot([0.5], [3.75], marker="o", color="#d97706", markersize=8, zorder=5)
ax.annotate("SOC 0.5：3.2 + 0.4 + 0.2 − 0.05\n= 3.7500 V", xy=(0.5, 3.75), xytext=(0.44, 3.30),
            fontsize=10, color="#0f172a", arrowprops=dict(arrowstyle="->", color="#334155", lw=1.1))
ax.annotate("SOC 0 时实际 2.9690 V\n（不是 3.2）", xy=(0.0, 2.969), xytext=(0.10, 2.90),
            fontsize=9.5, color="#be123c", arrowprops=dict(arrowstyle="->", color="#be123c", lw=1.0))
ax.set(xlim=(0, 1), ylim=(2.85, 4.38), xlabel="SOC", ylabel="电压 / V",
       title="一项一项叠：常数打底，斜率管中段，两个 tanh 管两头")
ax.title.set_fontsize(11)

# 右：斜率就是「电压说话算不算数」
bx = fig.add_axes((0.67, 0.13, 0.30, 0.69))
bx.set_facecolor("#ffffff")
bx.spines[["top", "right"]].set_visible(False)
bx.grid(alpha=0.2)
bx.plot(soc, cell_model.docv_dsoc(soc), color="#7c3aed", linewidth=2.4)
bx.plot([0.05, 0.5], [slope_low, slope_mid], "o", color="#7c3aed", markersize=7)
bx.text(0.09, slope_low - 0.1, f"陡处 {slope_low:.1f} V/SOC\n5 mV → {pp_low} 个百分点",
        fontsize=9.5, color="#5b21b6", va="top")
bx.text(0.36, slope_mid + 1.15, f"中段 {slope_mid:.1f} V/SOC\n5 mV → {pp_mid} 个百分点",
        fontsize=9.5, color="#5b21b6")
bx.set(xlim=(0, 1), ylim=(0, 7.4), xlabel="SOC", ylabel="斜率 dOCV/dSOC / (V/SOC)",
       title="斜率 = EKF 的观测矩阵 C")
bx.title.set_fontsize(11)

fig.suptitle("一条 OCV 曲线的四项：先叠出形状，再读斜率", fontsize=15, fontweight="bold", y=0.985)
fig.text(0.07, 0.025,
         "数据源 code/soc/cell_model.py 的 ocv() 与 docv_dsoc() · 合成电芯 · "
         f"同一 5 mV 电压误差：陡处换 {pp_low}、中段换 {pp_mid} 个百分点 SOC（5 mV ÷ 斜率）",
         fontsize=9, color="#475569")
save_figure(fig, "ocv-four-terms.svg", {
    "Title": "OCV 四项叠加与斜率",
    "Description": "合成电芯 OCV 由基准、中段斜率、低端与高端 tanh 四项叠出；右侧斜率曲线说明同一电压误差在陡处与平台处换算的 SOC 误差不同。",
})
plt.close(fig)
print("generated scientific SVG: ocv-four-terms.svg")

# ---------------------------------------------------------------------------
# 图 16-2：私家车的 81%——两只钟表逐年记账（数字全部取自 16.5 示例账：日历年均 3%、循环 5 年合计约 4%）
years = np.arange(0, 6)
cal_per_year, cyc_total = 3.0, 4.0
cal_loss = cal_per_year * years            # 0, 3, …, 15
cyc_loss = cyc_total * years / 5           # 0, 0.8, …, 4
soh_true = 100 - cal_loss - cyc_loss
soh_cycle_only = 100 - cyc_loss
assert soh_true[-1] == 81.0 and soh_cycle_only[-1] == 96.0

fig = plt.figure(figsize=(10, 5.4), facecolor="#f8fafc")
steps_ax = fig.add_axes((0.06, 0.865, 0.9, 0.068))
steps_ax.axis("off")
steps = [("① 日历钟：按年走 3%/年", "#b45309"), ("② 循环钟：按吞吐走，5 年约 4%", "#2563eb"),
         ("③ 两支相加 = 真实 SOH", "#0f766e")]
for idx, (label, color) in enumerate(steps):
    x0 = 0.01 + idx * 0.333
    steps_ax.add_patch(matplotlib.patches.FancyBboxPatch(
        (x0, 0.18), 0.30, 0.64, boxstyle="round,pad=0.012",
        facecolor=color, edgecolor="none", alpha=0.14,
        transform=steps_ax.transAxes, clip_on=False))
    steps_ax.text(x0 + 0.15, 0.5, label, ha="center", va="center",
                  fontsize=10.5, color=color, fontweight="bold", transform=steps_ax.transAxes)
    if idx < 2:
        steps_ax.annotate("", xy=(x0 + 0.328, 0.5), xytext=(x0 + 0.305, 0.5),
                          xycoords=steps_ax.transAxes, textcoords=steps_ax.transAxes,
                          arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.2))

ax = fig.add_axes((0.08, 0.16, 0.86, 0.66))
ax.set_facecolor("#ffffff")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", alpha=0.2)
width = 0.5
ax.bar(years, soh_true, width, color="#0f766e", alpha=0.85, label="剩余容量（真实 SOH）")
ax.bar(years, cal_loss, width, bottom=soh_true, color="#f59e0b", alpha=0.75, label="日历损耗（放着也老）")
ax.bar(years, cyc_loss, width, bottom=soh_true + cal_loss, color="#2563eb", alpha=0.65, label="循环损耗（用了才老）")
ax.plot(years, soh_cycle_only, color="#be123c", linewidth=2.0, linestyle="--", marker="o",
        label="只记循环钟时报的 SOH")
for y_, s in zip(years[1:], soh_true[1:], strict=True):
    ax.text(y_, s - 2.2, f"{s:.0f}%", ha="center", va="top", fontsize=10.5, color="#ffffff", fontweight="bold")
ax.annotate("只看循环支：报 96%", xy=(5, 96), xytext=(2.6, 102.4), fontsize=10.5, color="#be123c",
            fontweight="bold", arrowprops=dict(arrowstyle="->", color="#be123c", lw=1.1))
ax.annotate("", xy=(5.36, 81), xytext=(5.36, 96), arrowprops=dict(arrowstyle="<->", color="#b45309", lw=1.4))
ax.text(5.43, 88.5, "漏算 15%\n= 3%/年\n× 5 年", fontsize=10, color="#b45309", va="center", fontweight="bold")
for mark, x, y, color in [("①", 5, 88.5, "#b45309"), ("②", 5, 97.6, "#2563eb"), ("③", 5, 72, "#0f766e")]:
    ax.text(x - 0.42, y, mark, fontsize=13, color=color, fontweight="bold", ha="center", va="center",
            bbox=dict(boxstyle="circle,pad=0.2", facecolor="#ffffff", edgecolor=color, linewidth=1.3))
ax.set(xlim=(-0.5, 6.35), ylim=(60, 104.5), xticks=years, xlabel="车龄 / 年", ylabel="容量 / %")
ax.legend(loc="lower left", fontsize=9.5, framealpha=0.92)
fig.suptitle("私家车的 81%：两只钟表一起走", fontsize=15, fontweight="bold", y=0.985)
fig.text(0.08, 0.02,
         "教学示例账（16.5）：5 年、6 万公里 · 日历支年均 3%（25 °C 均值、平均 SOC 0.60 示意）\n"
         "循环支按「3000 循环到 80%」折算约 4%，均摊到每年 · 100 − 15 − 4 = 81",
         fontsize=9, color="#475569", linespacing=1.4)
save_figure(fig, "aging-two-clocks.svg", {
    "Title": "私家车 SOH 两支逐年记账",
    "Description": "按 16.5 教学示例：日历损耗每年 3%、循环损耗 5 年约 4%，逐年叠加后 5 年 SOH 约 81%；只看循环支会报 96%。",
})
plt.close(fig)
print("generated scientific SVG: aging-two-clocks.svg")

# ---------------------------------------------------------------------------
# 图 17-2：两种错留下的两种指纹（数据源：code/soc/compare.py 的 simulate_ekf，seed 42，与共学第 3 天同一工况）
sys.path.insert(0, str(ROOT / "code/soc"))
import compare  # noqa: E402  依赖 code/soc 下的 cell_model / estimators

inject = {
    "ok": compare.simulate_ekf(0.020, 0.015, 3000.0, 9.5),
    "r0": compare.simulate_ekf(0.200, 0.015, 3000.0, 9.5),
    "bias": compare.simulate_ekf(0.020, 0.015, 3000.0, 9.5, v_bias_v=0.050),
}
levels = [-6, -5, -4, -3, -2]
def _binned(case: str) -> tuple[list[float], list[float]]:
    tr = inject[case]
    med, imean = [], []
    for lv in levels:
        m = np.abs(tr["current_a"] - lv) < 0.5
        med.append(float(np.median(tr["innovation_mv"][m])))
        imean.append(float(tr["current_a"][m].mean()))
    return med, imean


r0_bins, r0_imean = _binned("r0")
ok_bins, _ = _binned("ok")
assert [round(v) for v in r0_bins] == [679, 538, 354, 230, 1]
assert max(abs(v) for v in ok_bins) < 2.0
# 残差 ≈ ΔR0 ×（电流相对稳态 −2 A 的偏离量）：不变的那部分被 SOC 吸收，只有偏离量漏进残差。
# 稳态 −2 A 不是异常点，而是这条过原点直线的零点。
r0_pred = [(0.200 - 0.020) * (abs(im) - 2.0) * 1000 for im in r0_imean]
assert [round(v) for v in r0_pred] == [675, 537, 354, 221, 0]
assert max(abs(p - m) for p, m in zip(r0_pred, r0_bins, strict=True)) < 10.0
bias = inject["bias"]
t_h = (np.arange(compare.N_STEPS) + 1) * compare.DT_S / 3600.0
sat = int(np.argmax(bias["soc_est"] >= 1.0))
bias_err_pp = 100 * (bias["soc_est"] - bias["soc_true"])
ok_err_pp = 100 * (inject["ok"]["soc_est"] - inject["ok"]["soc_true"])
assert sat == 14916 and round(float(bias_err_pp[1800:8300].mean()), 1) == 6.0
assert round(float(bias["innovation_mv"][sat:].mean()), 1) == 32.5
def _roll(x, window=300):
    """尾随 300 s 均值：只用过去的数据，末端不会因补零掉下来。"""
    csum = np.concatenate(([0.0], np.cumsum(x)))
    idx = np.arange(1, len(x) + 1)
    start = np.maximum(idx - window, 0)
    return (csum[idx] - csum[start]) / (idx - start)


fig = plt.figure(figsize=(10, 6.2), facecolor="#f8fafc")
steps_ax = fig.add_axes((0.06, 0.875, 0.9, 0.062))
steps_ax.axis("off")
steps = [("① 同一工况、同一种子", "#475569"), ("② 只改一处：R0×10 或 电压 +50 mV", "#be123c"),
         ("③ 按电流分组 / 按时间看残差", "#0f766e")]
for idx, (label, color) in enumerate(steps):
    x0 = 0.01 + idx * 0.333
    steps_ax.add_patch(matplotlib.patches.FancyBboxPatch(
        (x0, 0.18), 0.30, 0.64, boxstyle="round,pad=0.012",
        facecolor=color, edgecolor="none", alpha=0.14,
        transform=steps_ax.transAxes, clip_on=False))
    steps_ax.text(x0 + 0.15, 0.5, label, ha="center", va="center",
                  fontsize=10.5, color=color, fontweight="bold", transform=steps_ax.transAxes)
    if idx < 2:
        steps_ax.annotate("", xy=(x0 + 0.328, 0.5), xytext=(x0 + 0.305, 0.5),
                          xycoords=steps_ax.transAxes, textcoords=steps_ax.transAxes,
                          arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.2))

left = fig.add_axes((0.07, 0.2, 0.36, 0.6))
for ax in [left]:
    ax.set_facecolor("#ffffff")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.2)
pos = np.arange(len(levels))
left.bar(pos - 0.2, ok_bins, 0.4, color="#94a3b8", label="参数都对")
left.bar(pos + 0.2, r0_bins, 0.4, color="#be123c", alpha=0.85, label="EKF 的 R0 写成 10 倍")
for x, v in zip(pos, r0_bins, strict=True):
    left.text(x + 0.2, v + 12, f"{v:.0f}", ha="center", va="bottom", fontsize=10, color="#be123c", fontweight="bold")
left.plot(pos + 0.2, r0_pred, marker="o", markersize=5, color="#0f766e", linewidth=1.4,
          linestyle="--", zorder=5, label="ΔR0 ×（电流偏离 −2 A）")
left.set_xticks(pos, ["−6 A\n偏离 −4", "−5 A\n偏离 −3", "−4 A\n偏离 −2",
                      "−3 A\n偏离 −1", "−2 A 稳态\n偏离 0"])
left.set(ylim=(-40, 780), ylabel="新息中位数 / mV", title="① 参数错：残差 ≈ ΔR0 ×（电流偏离稳态）")
left.legend(loc="upper right", fontsize=8.8, framealpha=0.92)
left.text(0.97, 0.60, "稳态 −2 A 是这条线的零点：\n不变的那部分被 SOC 吃掉", transform=left.transAxes,
          fontsize=9.0, color="#0f766e", fontweight="bold", ha="right", va="top", linespacing=1.4,
          bbox=dict(boxstyle="round,pad=0.3", facecolor="#f8fafc", edgecolor="#99f6e4", lw=0.8))

top = fig.add_axes((0.53, 0.53, 0.43, 0.27))
bottom = fig.add_axes((0.53, 0.2, 0.43, 0.27), sharex=top)
for ax in (top, bottom):
    ax.set_facecolor("#ffffff")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
    ax.axvline(t_h[sat], color="#b45309", linestyle="--", linewidth=1.2)
warm = slice(300, None)  # 首 300 s 含初值 0.7→0.8 的收敛尖峰，尾随均值窗口也未填满
top.plot(t_h[warm], _roll(inject["ok"]["innovation_mv"])[warm], color="#94a3b8", linewidth=1.6, label="参数都对")
top.plot(t_h[warm], _roll(bias["innovation_mv"])[warm], color="#2563eb", linewidth=1.8, label="电压读数 +50 mV")
top.set(ylim=(-6, 46), ylabel="残差 / mV\n(300 s 均值)", title="② 传感器偏：先不吵，钳到 100% 才吵")
top.tick_params(labelbottom=False)
top.legend(loc="upper left", fontsize=9, framealpha=0.92)
top.text(t_h[sat] - 0.08, 30, "SOC 估到 100%\n(真值 95.1%)", ha="right", fontsize=9.5, color="#b45309", fontweight="bold")
bottom.plot(t_h, ok_err_pp, color="#94a3b8", linewidth=1.6)
bottom.plot(t_h, bias_err_pp, color="#2563eb", linewidth=1.8)
bottom.set(ylim=(-2, 10.5), xlim=(0, t_h[-1]), xlabel="时间 / h", ylabel="SOC 误差\n/ 百分点")
bottom.text(0.15, 8.4, "偏置被读成「电量多 6 个百分点」", fontsize=10, color="#2563eb", fontweight="bold")
fig.suptitle("两种错，两种指纹：会变的错露在残差里，不变的错藏进状态里", fontsize=14.5, fontweight="bold", y=0.985)
fig.text(0.07, 0.025,
         "仿真源 code/soc/compare.py 的 simulate_ekf（seed=42）· 真值电芯 10 Ah、R0=20 mΩ · 每组只改一处：EKF 的 R0，或电压读数\n"
         "左：按测量电流 ±0.5 A 分组的新息中位数 · 右：+50 mV 偏置组，残差为尾随 300 s 均值（自 300 s 起），虚线为 SOC 估计首次到 100% 的时刻",
         fontsize=9, color="#475569", linespacing=1.4)
save_figure(fig, "residual-fingerprints.svg", {
    "Title": "参数错与传感器偏置的残差指纹",
    "Description": "R0 写成十倍时新息随放电脉冲电流增大（679/538/354/230 mV），稳态 −2 A 仅 1 mV；电压 +50 mV 偏置被 EKF 读成 SOC 偏高约 6 个百分点，残差直到 SOC 估计钳到 100% 才出现。",
})
plt.close(fig)
print("generated scientific SVG: residual-fingerprints.svg")
