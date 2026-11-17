"""Generate chapter 8 and 14 scientific figures from the engineering ledger."""
from pathlib import Path
import importlib.util
import json
import re
from io import StringIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
# Matplotlib marker/clip hashes vary with paints and random salt; preserve published references.
SVG_IDS = {
    "thermal-horizon.svg": (
        "mc35baded29", "m4e8da47af3", "m073c265f6b", "pede1470656", "p660aaa694d",
    ),
    "discharge-energy-budget.svg": (
        "mcc8f9f99f2", "m061151e3fb", "md161078e13", "m249dd75509",
        "m38b471f033", "m1b0fe9b367", "p09ec0b8959", "p1568d156ed",
    ),
}
spec = importlib.util.spec_from_file_location("engineering_ledger", ROOT / "code/engineering_ledger.py")
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)
PALETTE = json.loads((ROOT.parent / "tools/visual_palette.json").read_text(encoding="utf-8"))["light"]
SERIES = PALETTE["technical"]
plt.rcParams.update({
    "font.family": "Microsoft YaHei", "svg.fonttype": "path", "font.size": 11,
    "text.color": PALETTE["ink"], "axes.labelcolor": PALETTE["ink"],
    "xtick.color": PALETTE["muted"], "ytick.color": PALETTE["muted"],
    "axes.edgecolor": PALETTE["line_strong"], "grid.color": PALETTE["line_strong"],
    "legend.facecolor": PALETTE["paper"], "legend.edgecolor": PALETTE["line"],
    # 手绘笔触：与概念图 / 曲线图同一支笔；只扰动笔画外形，数据与印出数字不变。
    "path.sketch": (1, 100, 2),
    "lines.solid_capstyle": "round", "lines.dash_capstyle": "round",
    "lines.solid_joinstyle": "round", "lines.dash_joinstyle": "round",
})


def _ink_scope(fig):
    """手绘只落在脊线、刻度、徽章、柱与中等密度曲线；背景/网格/密集数据保持干净精确。"""
    fig.patch.set_sketch_params(None)
    for ax in fig.axes:
        ax.patch.set_sketch_params(None)
        for gridline in ax.get_xgridlines() + ax.get_ygridlines():
            gridline.set_sketch_params(None)
        for line in ax.get_lines():
            if len(line.get_xdata()) > 800:
                line.set_sketch_params(None)


def save(fig, name, title):
    _ink_scope(fig)
    buffer = StringIO()
    # Date=None 去掉 <dc:date> 时间戳：它是重跑唯一的非确定源，去掉后字节级可复现。
    fig.savefig(buffer, format="svg", metadata={"Title": title, "Description": "全部使用书中明确的合成参数，不是电芯实测数据。", "Date": None})
    svg = "\n".join(line.rstrip() for line in buffer.getvalue().splitlines()) + "\n"
    generated_ids = re.findall(r'\bid="([mp][0-9a-f]{10})"', svg)
    ids = dict(zip(generated_ids, SVG_IDS[name], strict=True))
    svg = re.sub(
        r'(\bid="|(?:xlink:)?href="#|url\(#)([^"\)]+)',
        lambda match: match[1] + ids.get(match[2], match[2]),
        svg,
    )
    (ROOT / "assets" / name).write_text(svg, encoding="utf-8")
    plt.close(fig)
    print(f"generated {name}")


fig, axes = plt.subplots(1, 2, figsize=(10, 4.3), facecolor=PALETTE["surface"])
for ax in axes:
    ax.set_facecolor(PALETTE["paper"])
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
times = np.linspace(0, 600, 301)
for current, color in [(10, SERIES["blue"]), (20, SERIES["red"])]:
    temperature = [ledger.thermal_step(current, 0.049, 1, 120, 25, 25, float(t)) for t in times]
    axes[0].plot(times, temperature, color=color, lw=2, label=f"{current} A：稳态 {25 + current ** 2 * 0.049:.1f} °C")
axes[0].axhline(40, color=SERIES["gold"], linestyle="--", label="限温 40 °C")
axes[0].set(xlabel="时间 / s", ylabel="代表温度 / °C", title="电流翻倍，欧姆生热变四倍")
axes[0].legend(fontsize=9)
windows = np.logspace(1, np.log10(600), 150)
for initial, color in [(25, SERIES["blue"]), (35, SERIES["green"])]:
    currents = [ledger.thermal_current_limit(0.049, 1, 120, 25, initial, 40, float(t)) for t in windows]
    axes[1].plot(windows, currents, color=color, lw=2, label=f"初温 {initial} °C")
axes[1].set(xscale="log", xlabel="预测窗 / s（对数）", ylabel="热电流幅值界 / A", title="长窗口与较高初温收紧许可")
axes[1].legend(fontsize=9)
fig.suptitle("同一热参数，预测窗决定热预算", fontsize=15, fontweight="bold")
fig.text(0.07, 0.025, "合成单节点 · R=49 mΩ，Rth=1 K/W，Cth=120 J/K，环境 25 °C · 恒流、无熵热 · 未叠加其他电流约束", fontsize=9, color=PALETTE["muted"])
fig.tight_layout(rect=(0, 0.07, 1, 0.94))
save(fig, "thermal-horizon.svg", "温升与预测窗的热电流约束")

fig, axes = plt.subplots(1, 2, figsize=(10, 4.3), facecolor=PALETTE["surface"])
for ax in axes:
    ax.set_facecolor(PALETTE["paper"])
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
t = np.logspace(-3, 2.2, 350)
for resistor, color in [(200, SERIES["blue"]), (47000, SERIES["green"])]:
    voltage = 400 * np.exp(-t / (resistor * 0.001))
    axes[0].plot(t, voltage, color=color, lw=2, label=f"{resistor:g} Ω")
    target, energy, peak = ledger.discharge_ledger(0.001, 400, 60, resistor)
    axes[0].scatter([target], [60], color=color)
    # 对数轴上 bar 从 0 起画会把矩形边推到 log(0)→−inf 的画布外巨坐标，sketch 逐像素重采样酿成 MB 级路径；从 ylim 下限起画可见结果不变。
    axes[1].bar(str(resistor), peak, color=color, width=0.55, bottom=1)
    axes[1].text(str(resistor), peak * 1.2, f"{peak:.1f} W\n{target:.3f} s", ha="center", fontsize=10)
axes[0].axhline(60, color=SERIES["gold"], ls="--", label="算例目标 60 V")
axes[0].set(xscale="log", xlabel="时间 / s（对数）", ylabel="母线电压 / V", title="同一电容，放电时间相差 235 倍")
axes[0].legend(fontsize=9)
axes[1].set(yscale="log", xlabel="放电电阻 / Ω", ylabel="初始功率 / W（对数）", title="释放能量相同，峰值功率不同", ylim=(1, 3000))
fig.suptitle("放电器件需要三笔账：时间、峰值功率、累计能量", fontsize=15, fontweight="bold")
fig.text(0.07, 0.025, "隔离后 RC 合成算例 · C=1 mF，400→60 V · 初始 80 J，残余 1.8 J，两条路径均释放 78.2 J · 不是高压操作步骤", fontsize=9, color=PALETTE["muted"])
fig.tight_layout(rect=(0, 0.07, 1, 0.94))
save(fig, "discharge-energy-budget.svg", "RC 放电时间与峰值功率对照")
